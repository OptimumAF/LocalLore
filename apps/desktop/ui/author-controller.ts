// Native AuthorPort is supplied by Root's shared broker adapter. No IPC registration.
import {
    authorAvailable,
    authorError,
    authorRaw,
    authorRequest,
    checkedAuthorCompletion,
    checkedAuthorContext,
    checkedAuthorDraft,
    checkedAuthorPreview,
    checkedAuthorStatus,
    type AuthorContext,
    type AuthorDraft,
    type AuthorInput,
    type AuthorOutcome,
    type AuthorPreview,
    type AuthorStatus,
} from "./author-model";
export {
    checkedAuthorInput,
    checkedAuthorPreview,
    checkedAuthorOutcome,
    checkedAuthorStatus,
} from "./author-model";
export interface AuthorPort {
    prepareStart(raw: string): Promise<unknown>;
    commitStart(raw: string): Promise<unknown>;
    lookupStart(raw: string): Promise<unknown>;
    status(id: number): Promise<unknown>;
    cancel(id: number): Promise<unknown>;
    discardPreview(session: string, token: string): Promise<boolean>;
}
interface Effects {
    refreshLibrary(): Promise<unknown>;
    openChild(scope: { story: string; branch: string }): Promise<unknown>;
}
interface Work {
    serial: number;
    key: string;
    context: AuthorContext;
    kind: "prepare" | "commit" | "lookup";
    input: AuthorInput;
    session: string;
    id: number | null;
    finalized: boolean;
    cancelRequested: boolean;
}
interface AuthorState {
    status:
        | "idle"
        | "preparing"
        | "preview"
        | "committing"
        | "lookup"
        | "uncertain"
        | "complete"
        | "not_found"
        | "error";
    busy: boolean;
    uncertain: boolean;
    available: boolean;
    authorConsent: boolean;
    previewRead: boolean;
    draft: AuthorDraft;
    input: AuthorInput | null;
    preview: AuthorPreview | null;
    outcome: AuthorOutcome | null;
    operation: AuthorStatus | null;
    error: string | null;
    notice: string;
}
const emptyDraft = (): AuthorDraft =>
    Object.freeze({
        fork_revision: 0,
        child_branch: "",
        fact: "",
        expected_proposition: "",
        replacement: "",
        reason: "",
    });
export class AuthorController {
    private state: Readonly<AuthorState> = Object.freeze({
        status: "idle" as
            | "idle"
            | "preparing"
            | "preview"
            | "committing"
            | "lookup"
            | "uncertain"
            | "complete"
            | "not_found"
            | "error",
        busy: false,
        uncertain: false,
        available: false,
        authorConsent: false,
        previewRead: false,
        draft: emptyDraft(),
        input: null as AuthorInput | null,
        preview: null as AuthorPreview | null,
        outcome: null as AuthorOutcome | null,
        operation: null as AuthorStatus | null,
        error: null as string | null,
        notice: "",
    });
    private context: AuthorContext | null = null;
    private key = "none";
    private serial = 0;
    private active: Work | null = null;
    private resultKey = "";
    private disposed = false;
    private listeners = new Set<() => void>();
    constructor(
        private port: AuthorPort,
        private effects: Effects,
        private pause: () => Promise<void> = () =>
            new Promise((resolve) => setTimeout(resolve, 25)),
    ) {}
    get = () => this.state;
    subscribe = (listener: () => void) => {
        this.listeners.add(listener);
        return () => {
            this.listeners.delete(listener);
        };
    };
    private patch(value: Partial<AuthorState>) {
        if (this.disposed) return;
        this.state = Object.freeze({ ...this.state, ...value });
        for (const f of this.listeners) f();
    }
    private fail(error: unknown) {
        this.patch({
            error: authorError(error),
            status: this.state.uncertain ? "uncertain" : "error",
        });
    }
    matchesContext(context: AuthorContext | null) {
        try {
            return (
                !this.disposed &&
                this.key ===
                    (context
                        ? JSON.stringify(checkedAuthorContext(context))
                        : "none")
            );
        } catch {
            return false;
        }
    }
    private current(work: Work) {
        return (
            !this.disposed &&
            work.serial === this.serial &&
            work.key === this.key
        );
    }
    private discard(preview: AuthorPreview | null) {
        if (preview)
            void this.port
                .discardPreview(preview.session, preview.preview_token)
                .catch(() => {});
    }
    private invalidate() {
        this.discard(this.state.preview);
        this.patch({ authorConsent: false, previewRead: false, preview: null });
    }
    contextChanged(value: AuthorContext | null) {
        if (this.disposed) return;
        let context: AuthorContext | null = null;
        try {
            context = value === null ? null : checkedAuthorContext(value);
        } catch {
            /* Invalid context cannot grant author access. */
        }
        const key = context ? JSON.stringify(context) : "none";
        if (key === this.key) return;
        const oldRoot = this.context?.rootIncarnation;
        const sameRoot = !!context && oldRoot === context.rootIncarnation;
        const pending = this.state.busy || this.state.uncertain;
        const previousPreview = this.state.preview;
        const previousWork = this.state.busy ? this.active : null;
        this.serial++;
        // Install the identity before synchronous presentation subscribers run.
        // A nested selection change must never be overwritten by this callback.
        this.context = context;
        this.key = key;
        this.resultKey = "";
        if (!sameRoot) this.active = null;
        this.discard(previousPreview);
        this.patch({
            authorConsent: false,
            previewRead: false,
            preview: null,
            available: authorAvailable(context),
            busy: false,
            operation: null,
            outcome: null,
            error: null,
            input: sameRoot ? this.state.input : null,
            uncertain: sameRoot && pending,
            status: sameRoot && pending ? "uncertain" : "idle",
            notice:
                sameRoot && pending
                    ? "The earlier operation must be inspected; no correction will be retried automatically."
                    : "",
            ...(!sameRoot ? { draft: emptyDraft() } : {}),
        });
        if (previousWork?.id !== null && previousWork?.id !== undefined)
            void this.port.cancel(previousWork.id).catch(() => {});
    }
    setDraft(value: AuthorDraft) {
        if (this.disposed) return;
        if (this.state.busy || this.state.uncertain) {
            this.fail(Error("Busy"));
            return;
        }
        try {
            const draft = checkedAuthorDraft(value);
            if (JSON.stringify(draft) === JSON.stringify(this.state.draft))
                return;
            this.serial++;
            this.invalidate();
            this.patch({
                draft,
                input: null,
                outcome: null,
                error: null,
                status: "idle",
                notice: "",
            });
        } catch (error) {
            this.serial++;
            this.invalidate();
            this.patch({ input: null, outcome: null });
            this.fail(error);
        }
    }
    setAuthorConsent(value: boolean) {
        if (this.disposed || this.state.busy || this.state.uncertain) return;
        if (!value) this.invalidate();
        else this.patch({ authorConsent: true, error: null });
    }
    setPreviewRead(value: boolean) {
        if (
            !this.disposed &&
            !this.state.busy &&
            this.state.preview &&
            this.state.authorConsent
        )
            this.patch({ previewRead: value, error: null });
    }
    private startWork(kind: Work["kind"], input: AuthorInput): Work {
        const context = this.context!;
        const work: Work = {
            serial: ++this.serial,
            key: this.key,
            context,
            kind,
            input,
            session: context.session,
            id: null,
            finalized: false,
            cancelRequested: false,
        };
        this.active = work;
        this.patch({
            busy: true,
            uncertain: false,
            input,
            outcome: null,
            error: null,
            operation: null,
            status:
                kind === "prepare"
                    ? "preparing"
                    : kind === "commit"
                      ? "committing"
                      : "lookup",
            notice: "",
        });
        return work;
    }
    async prepare() {
        if (
            !authorAvailable(this.context) ||
            this.state.busy ||
            this.state.uncertain
        ) {
            this.fail(Error("Unavailable"));
            return;
        }
        if (!this.state.authorConsent) {
            this.fail(Error("AuthorConsentRequired"));
            return;
        }
        try {
            const selectedKey = this.key,
                generation = this.serial;
            const input = authorRequest(this.context!, this.state.draft);
            this.discard(this.state.preview);
            this.patch({ preview: null, previewRead: false });
            if (
                this.key !== selectedKey ||
                this.serial !== generation ||
                !this.state.authorConsent ||
                !authorAvailable(this.context)
            )
                return;
            const raw = authorRaw({
                version: 1,
                session: this.context!.session,
                input,
                author_consent: true,
            });
            const work = this.startWork("prepare", input);
            await this.run(work, () => this.port.prepareStart(raw));
        } catch (error) {
            this.fail(error);
        }
    }
    async confirm(confirmed: boolean) {
        if (
            !authorAvailable(this.context) ||
            this.state.busy ||
            this.state.uncertain
        ) {
            this.fail(Error("Unavailable"));
            return;
        }
        const preview = this.state.preview,
            input = this.state.input;
        if (
            !confirmed ||
            !this.state.authorConsent ||
            !this.state.previewRead ||
            !preview ||
            !input
        ) {
            this.fail(Error("ReadPreviewRequired"));
            return;
        }
        try {
            const selectedKey = this.key,
                generation = this.serial;
            const raw = authorRaw({
                version: 1,
                session: this.context!.session,
                input,
                preview_token: preview.preview_token,
                preview_sha256: preview.preview_sha256,
                confirmed: true,
            });
            // A verified native attempt consumes this token even if the worker is Busy.
            this.patch({
                preview: null,
                previewRead: false,
                authorConsent: false,
            });
            if (
                this.key !== selectedKey ||
                this.serial !== generation ||
                !authorAvailable(this.context)
            )
                return;
            const work = this.startWork("commit", input);
            await this.run(work, () => this.port.commitStart(raw));
        } catch (error) {
            this.fail(error);
        }
    }
    private async run(work: Work, start: () => Promise<unknown>) {
        // startWork notifies synchronously; navigation may retire it before IPC.
        if (!this.current(work)) return;
        try {
            const value = await start();
            await this.follow(work, value);
        } catch (error) {
            if (!this.current(work) || work.finalized) return;
            const code = authorError(error);
            const uncertain =
                code === "Transport" ||
                code === "Wire" ||
                code === "UnknownArchiveOperation";
            this.patch({
                busy: false,
                uncertain,
                status: uncertain ? "uncertain" : "error",
                error: code,
                preview: null,
                previewRead: false,
                authorConsent: false,
                notice:
                    work.kind === "commit"
                        ? uncertain
                            ? "Outcome unknown. Check the saved child only; do not apply again."
                            : "A new private preview is required before another apply attempt."
                        : "",
            });
        }
    }
    private async follow(work: Work, value: unknown) {
        for (let polls = 0; polls < 2400; polls++) {
            if (work.finalized) return;
            const status = checkedAuthorStatus(value);
            if (work.id !== null && work.id !== status.operation_id)
                throw Error("Wire");
            work.id = status.operation_id;
            if (!this.current(work)) {
                if (work.kind === "prepare" && status.phase === "completed")
                    this.discard(
                        await checkedAuthorPreview(
                            status.result,
                            work.input,
                            work.session,
                        ),
                    );
                else if (status.running)
                    void this.port.cancel(status.operation_id).catch(() => {});
                return;
            }
            const phase =
                work.kind === "prepare"
                    ? "author_preparing"
                    : work.kind === "commit"
                      ? "author_applying"
                      : "author_lookup";
            if (
                status.running &&
                status.phase !== "starting" &&
                status.phase !== phase
            )
                throw Error("Wire");
            this.patch({ operation: status });
            if (!status.running) {
                await this.finish(work, status);
                return;
            }
            if (work.cancelRequested) {
                value = await this.port.cancel(status.operation_id);
                work.cancelRequested = false;
                continue;
            }
            await this.pause();
            if (!this.current(work)) return;
            value = await this.port.status(status.operation_id);
        }
        throw Error("Transport");
    }
    private async finish(work: Work, status: AuthorStatus) {
        if (work.finalized) return;
        if (!this.current(work)) {
            if (work.kind === "prepare" && status.phase === "completed")
                this.discard(
                    await checkedAuthorPreview(
                        status.result,
                        work.input,
                        work.session,
                    ),
                );
            return;
        }
        if (status.error) {
            work.finalized = true;
            this.patch({
                busy: false,
                uncertain: false,
                status: "error",
                error: status.error,
                preview: null,
                previewRead: false,
                authorConsent: false,
                notice:
                    work.kind === "commit"
                        ? "No automatic retry. Inspect if uncertain; otherwise prepare a new preview."
                        : "",
            });
            return;
        }
        if (work.kind === "prepare") {
            const preview = await checkedAuthorPreview(
                status.result,
                work.input,
                work.session,
            );
            if (!this.current(work)) {
                this.discard(preview);
                return;
            }
            work.finalized = true;
            if (work.cancelRequested) {
                this.discard(preview);
                this.patch({
                    busy: false,
                    uncertain: false,
                    status: "idle",
                    preview: null,
                    previewRead: false,
                    authorConsent: false,
                    error: null,
                    notice: "Cancelled preview discarded. No correction was applied.",
                });
                return;
            }
            this.patch({
                busy: false,
                uncertain: false,
                status: "preview",
                preview,
                previewRead: false,
                error: null,
            });
            return;
        }
        const outcome = checkedAuthorCompletion(
            status.result,
            work.kind,
            work.input,
            work.session,
        );
        if (!this.current(work)) return;
        work.finalized = true;
        this.resultKey = this.key;
        this.patch({
            busy: false,
            uncertain: false,
            status: outcome ? "complete" : "not_found",
            outcome,
            error: null,
            preview: null,
            previewRead: false,
            authorConsent: false,
            notice: outcome
                ? "Saved child confirmed. No character observation was created by this author action."
                : "No matching child found. Nothing was created by this inspection; a new explicit preview is required to apply.",
        });
        // Library refresh is presentation only; failure cannot demote an actual saved result.
        if (outcome && this.current(work))
            try {
                await this.effects.refreshLibrary();
            } catch {
                if (this.current(work))
                    this.patch({
                        notice: "Saved child confirmed; refresh the story library explicitly.",
                    });
            }
    }
    async inspectOperation() {
        const old = this.active;
        if (
            this.disposed ||
            !old ||
            old.id === null ||
            !this.context ||
            old.context.rootIncarnation !== this.context.rootIncarnation
        )
            return;
        // A stale private preview cannot acquire a new context through a status read.
        if (old.kind === "prepare" && old.key !== this.key) return;
        const work: Work = {
            ...old,
            serial: ++this.serial,
            key: this.key,
            context: this.context,
            finalized: false,
        };
        this.active = work;
        this.patch({ busy: true, error: null });
        await this.run(work, () => this.port.status(work.id!));
    }
    async lookup() {
        if (
            !authorAvailable(this.context) ||
            this.state.busy ||
            !this.state.input
        ) {
            this.fail(Error("Unavailable"));
            return;
        }
        const input = this.state.input;
        try {
            const selectedKey = this.key,
                generation = this.serial;
            // A readonly lookup replaces the preview presentation; release its
            // unused native capability before that ownership disappears.
            if (this.state.preview) this.invalidate();
            if (
                this.key !== selectedKey ||
                this.serial !== generation ||
                !authorAvailable(this.context)
            )
                return;
            const raw = authorRaw({ version: 1, input, author_consent: true });
            const work = this.startWork("lookup", input);
            await this.run(work, () => this.port.lookupStart(raw));
        } catch (error) {
            this.fail(error);
        }
    }
    async cancel() {
        if (this.disposed) return;
        if (this.state.preview) {
            this.invalidate();
            this.patch({
                status: "idle",
                notice: "Unused preview discarded. No correction was applied.",
            });
            return;
        }
        const work = this.active;
        if (!work || !this.state.busy) return;
        work.cancelRequested = true;
        if (work.id === null) {
            this.patch({
                uncertain: true,
                notice: "Start acknowledgment is unavailable. No cancellation or rollback can be confirmed; inspect the outcome.",
            });
            return;
        }
        try {
            const value = await this.port.cancel(work.id);
            if (!this.current(work)) return;
            const status = checkedAuthorStatus(value);
            if (status.operation_id !== work.id) throw Error("Wire");
            if (!status.running) await this.finish(work, status);
            else
                this.patch({
                    notice: "Cancellation requested. A committed result remains saved.",
                });
        } catch (error) {
            if (this.current(work))
                this.patch({
                    error: authorError(error),
                    uncertain: true,
                    notice: "Cancellation is unconfirmed. Inspect the saved outcome.",
                });
        }
    }
    async openConfirmed() {
        const outcome = this.state.outcome;
        if (
            !outcome ||
            this.resultKey !== this.key ||
            !authorAvailable(this.context) ||
            this.state.busy
        )
            return;
        try {
            await this.effects.openChild({ ...outcome.scope });
        } catch (error) {
            this.fail(error);
        }
    }
    dispose() {
        if (this.disposed) return;
        this.discard(this.state.preview);
        if (
            this.active?.id !== null &&
            this.active?.id !== undefined &&
            this.state.busy
        )
            void this.port.cancel(this.active.id).catch(() => {});
        this.serial++;
        this.patch({
            input: null,
            preview: null,
            outcome: null,
            operation: null,
            authorConsent: false,
            previewRead: false,
            draft: emptyDraft(),
            busy: false,
            available: false,
            uncertain: false,
        });
        this.disposed = true;
        this.context = null;
        this.active = null;
        this.listeners.clear();
    }
}
