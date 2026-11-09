import {
    archiveErrors,
    archiveBinding,
    decodeArchiveCompletion,
    decodePreview,
    decodeStatus,
} from "./archive-model";
import type {
    ArchiveCommand,
    ArchiveResult,
    ArchiveStatus,
    PreviewToken,
} from "./archive-model";
import type { Scope } from "./model";
type Invoke = (
    name: string,
    args?: Record<string, unknown>,
) => Promise<unknown>;
type ExportBasis = { session: string; scope: Scope; expectedRevision: number };
export class ArchiveController {
    private state = {
        shown: false,
        busy: false,
        consent: false,
        preview: null as PreviewToken | null,
        status: null as ArchiveStatus | null,
        result: null as ArchiveResult | null,
        error: null as string | null,
        notice: "",
    };
    private listeners = new Set<() => void>();
    private epoch = 0;
    private context = "";
    private allowed = false;
    constructor(
        private invoke: Invoke,
        private refreshLibrary: () => Promise<unknown>,
    ) {}
    get = () => this.state;
    subscribe = (f: () => void) => {
        this.listeners.add(f);
        return () => {
            this.listeners.delete(f);
        };
    };
    matchesContext(context: string) {
        return this.context === context;
    }
    private patch(v: Partial<typeof this.state>) {
        this.state = { ...this.state, ...v };
        for (const f of this.listeners) f();
    }
    private discard(token: string) {
        void this.invoke("archive_discard", { token }).catch(() => {});
    }
    private invalidate() {
        const preview = this.state.preview,
            operation = this.state.status;
        this.epoch++;
        this.patch({
            shown: false,
            busy: false,
            preview: null,
            status: null,
            result: null,
            consent: false,
            error: null,
            notice: "",
        });
        if (preview) this.discard(preview.token);
        if (operation?.running)
            void this.invoke("archive_cancel", {
                operationId: operation.operation_id,
            }).catch(() => {});
    }
    contextChanged(context: string, allowed: boolean) {
        if (this.context === context && this.allowed === allowed) return;
        this.context = context;
        this.allowed = allowed;
        this.invalidate();
    }
    dispose() {
        this.allowed = false;
        this.invalidate();
    }
    show() {
        if (this.allowed) this.patch({ shown: true });
    }
    hide() {
        this.invalidate();
    }
    consent(value: boolean) {
        this.patch({ consent: value });
    }
    private errorCode(e: unknown) {
        const n = e instanceof Error ? e.message : String(e);
        return archiveErrors.has(n) ? n : "Wire";
    }
    private async action(command: ArchiveCommand, basis?: ExportBasis) {
        if (!this.allowed || this.state.busy) return;
        const isPreview = command.endsWith("preview"),
            preview = this.state.preview;
        if (!isPreview && (!preview || !this.state.consent)) return;
        const epoch = ++this.epoch;
        this.patch({
            busy: true,
            ...(isPreview ? { preview: null, consent: false } : {}),
            error: null,
            status: null,
            result: null,
            notice: isPreview
                ? "Reading one private archive snapshot..."
                : "Explicit private transfer in progress. Native dialog cancellation uses its Cancel button.",
        });
        const completion = (status: ArchiveStatus) =>
            decodeArchiveCompletion(
                status,
                command,
                !isPreview && preview ? archiveBinding(preview) : undefined,
                basis
                    ? {
                          story: basis.scope.story,
                          branch: basis.scope.branch,
                          head: basis.expectedRevision,
                      }
                    : undefined,
            );
        const discardRetiredPreview = (status: ArchiveStatus) => {
            if (!status.result?.token) return;
            const { token } = completion(status);
            if (token && token !== this.state.preview?.token)
                this.discard(token);
        };
        try {
            if (isPreview && preview) this.discard(preview.token);
            if (epoch !== this.epoch) return;
            let status = decodeStatus(
                await this.invoke(
                    command,
                    isPreview
                        ? (basis ?? {})
                        : { token: preview!.token, consent: true },
                ),
            );
            const operation = status.operation_id;
            if (epoch !== this.epoch) {
                if (status.running) {
                    if (this.state.status?.operation_id !== operation)
                        void this.invoke("archive_cancel", {
                            operationId: operation,
                        }).catch(() => {});
                } else discardRetiredPreview(status);
                return;
            }
            for (;;) {
                if (status.operation_id !== operation) throw Error("Wire");
                if (epoch !== this.epoch) {
                    discardRetiredPreview(status);
                    return;
                }
                if (!status.running) break;
                this.patch({ status });
                await new Promise((r) => setTimeout(r, 25));
                if (epoch !== this.epoch) return;
                status = decodeStatus(
                    await this.invoke("archive_status", {
                        operationId: operation,
                    }),
                );
            }
            if (status.error) {
                this.patch({ status });
                throw Error(status.error);
            }
            const result = completion(status);
            if (result.token) {
                const p = decodePreview(result);
                this.patch({
                    status,
                    preview: p,
                    consent: false,
                    result: null,
                    error: null,
                    notice: "Review this exact captured snapshot before confirming. Preview expires ten minutes after creation.",
                });
            } else {
                this.patch({
                    status,
                    preview: null,
                    consent: false,
                    result,
                    error:
                        result.status === "failed"
                            ? (result.error ?? "Wire")
                            : null,
                    notice:
                        result.status === "imported"
                            ? "Imported as a saved story. Open it explicitly; old pending operations and model selections were not resumed."
                            : result.status === "exported"
                              ? "Private playable archive published. This file preserves the captured history; later play does not update it."
                              : result.status === "cancelled"
                                ? "Native file selection cancelled. No transfer occurred."
                                : "Transfer failed. Check cleanup status; no automatic retry.",
                });
                if (result.status === "imported" && epoch === this.epoch)
                    await this.refreshLibrary();
            }
        } catch (e) {
            if (epoch === this.epoch)
                this.patch({
                    ...(isPreview ? {} : { preview: null, consent: false }),
                    error: this.errorCode(e),
                    notice: "No automatic retry. If acknowledgement was lost, check saved stories before trying this identity again.",
                });
        } finally {
            if (epoch === this.epoch) this.patch({ busy: false });
        }
    }
    previewExport(session: string, scope: Scope, expectedRevision: number) {
        return this.action("archive_export_preview", {
            session,
            scope: { ...scope },
            expectedRevision,
        });
    }
    previewImport() {
        return this.action("archive_import_preview");
    }
    confirm() {
        return this.action(
            this.state.preview?.kind === "export"
                ? "archive_export"
                : "archive_import",
        );
    }
    async cancel() {
        const s = this.state.status;
        if (!s?.running) return;
        const epoch = this.epoch;
        const ownsRunningStatus = () =>
            epoch === this.epoch &&
            this.state.status?.running &&
            this.state.status.operation_id === s.operation_id;
        try {
            const reply = decodeStatus(
                await this.invoke("archive_cancel", {
                    operationId: s.operation_id,
                }),
            );
            if (reply.operation_id !== s.operation_id) throw Error("Wire");
            if (reply.running && ownsRunningStatus())
                this.patch({
                    error: null,
                    notice: "Cancellation requested. A transaction that already committed wins; check the final result. Native picker dialogs must be cancelled in the dialog.",
                });
        } catch (e) {
            if (ownsRunningStatus())
                this.patch({
                    error: this.errorCode(e),
                    notice: "Cancellation could not be confirmed. Check the final transfer status before trying again.",
                });
        }
    }
}
