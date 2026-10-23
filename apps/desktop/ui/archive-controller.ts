import { archiveErrors, decodePreview, decodeStatus } from "./archive-model";
import type {
    ArchiveResult,
    ArchiveStatus,
    PreviewToken,
} from "./archive-model";
import type { Scope } from "./model";
type Invoke = (
    name: string,
    args?: Record<string, unknown>,
) => Promise<unknown>;
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
    private invalidate() {
        const preview = this.state.preview,
            operation = this.state.status;
        this.epoch++;
        this.patch({
            busy: false,
            preview: null,
            status: null,
            result: null,
            consent: false,
            error: null,
            notice: "",
        });
        if (preview)
            void this.invoke("archive_discard", { token: preview.token }).catch(
                () => {},
            );
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
        this.patch({ shown: false });
    }
    dispose() {
        this.allowed = false;
        this.invalidate();
        this.patch({ shown: false });
    }
    show() {
        if (this.allowed) this.patch({ shown: true });
    }
    hide() {
        this.invalidate();
        this.patch({ shown: false });
    }
    consent(value: boolean) {
        this.patch({ consent: value });
    }
    private failure(e: unknown) {
        const n = e instanceof Error ? e.message : String(e);
        this.patch({
            error: archiveErrors.has(n) ? n : "Wire",
            busy: false,
            notice: "No automatic retry. If acknowledgement was lost, check saved stories before trying this identity again.",
        });
    }
    async action(
        command:
            | "archive_export_preview"
            | "archive_import_preview"
            | "archive_export"
            | "archive_import",
        args: Record<string, unknown> = {},
    ) {
        if (!this.allowed || this.state.busy) return;
        const isPreview = command.endsWith("preview"),
            preview = this.state.preview;
        if (!isPreview && (!preview || !this.state.consent)) return;
        if (isPreview) this.invalidate();
        const epoch = ++this.epoch;
        this.patch({
            busy: true,
            error: null,
            status: null,
            result: null,
            notice: isPreview
                ? "Reading one private archive snapshot..."
                : "Explicit private transfer in progress. Native dialog cancellation uses its Cancel button.",
        });
        try {
            let status = decodeStatus(
                await this.invoke(
                    command,
                    isPreview ? args : { token: preview!.token, consent: true },
                ),
            );
            const operation = status.operation_id;
            if (epoch !== this.epoch) {
                if (status.result?.token)
                    void this.invoke("archive_discard", {
                        token: status.result.token,
                    }).catch(() => {});
                if (status.running)
                    void this.invoke("archive_cancel", {
                        operationId: operation,
                    }).catch(() => {});
                return;
            }
            for (;;) {
                if (epoch !== this.epoch) return;
                if (status.operation_id !== operation) throw Error("Wire");
                this.patch({ status });
                if (!status.running) break;
                await new Promise((r) => setTimeout(r, 25));
                if (epoch !== this.epoch) return;
                status = decodeStatus(
                    await this.invoke("archive_status", {
                        operationId: operation,
                    }),
                );
                if (epoch !== this.epoch && status.result?.token)
                    void this.invoke("archive_discard", {
                        token: status.result.token,
                    }).catch(() => {});
            }
            if (status.error) throw Error(status.error);
            const result = status.result;
            if (!result) throw Error("Wire");
            if (
                !isPreview &&
                result.status === "imported" &&
                (preview!.kind !== "import" ||
                    result.root?.story !== preview!.preview.story_id ||
                    result.root.branch !== preview!.preview.root_branch)
            )
                throw Error("Wire");
            if (
                !isPreview &&
                result.status === "exported" &&
                (preview!.kind !== "export" ||
                    result.payload_sha256 !== preview!.preview.payload_sha256)
            )
                throw Error("Wire");
            if (result.token) {
                const p = decodePreview(result);
                if (
                    p.kind !==
                    (command === "archive_export_preview" ? "export" : "import")
                )
                    throw Error("Wire");
                this.patch({
                    preview: p,
                    consent: false,
                    result: null,
                    notice: "Review this exact captured snapshot before confirming. Preview expires after ten idle minutes.",
                });
            } else {
                this.patch({
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
                              ? "Private playable archive published. The original story and archive are unchanged by later play."
                              : result.status === "cancelled"
                                ? "Native file selection cancelled. No transfer occurred."
                                : "Transfer failed. Check cleanup status; no automatic retry.",
                });
                if (result.status === "imported" && epoch === this.epoch)
                    await this.refreshLibrary();
            }
        } catch (e) {
            if (epoch === this.epoch) {
                if (!isPreview) this.patch({ preview: null, consent: false });
                this.failure(e);
            }
        } finally {
            if (epoch === this.epoch) this.patch({ busy: false });
        }
    }
    previewExport(session: string, scope: Scope, expectedRevision: number) {
        return this.action("archive_export_preview", {
            session,
            scope,
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
        try {
            await this.invoke("archive_cancel", {
                operationId: s.operation_id,
            });
            if (epoch === this.epoch)
                this.patch({
                    notice: "Cancellation requested. A transaction that already committed wins; check the final result. Native picker dialogs must be cancelled in the dialog.",
                });
        } catch (e) {
            if (epoch === this.epoch) this.failure(e);
        }
    }
}
