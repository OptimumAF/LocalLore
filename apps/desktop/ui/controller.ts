import {
    category,
    difference,
    ErrorBuffer,
    PAGE_SIZE,
    playView,
    request,
    sameScope,
    structural,
} from "./model";
import type {
    Action,
    Command,
    FakeMode,
    Gateway,
    Json,
    Pending,
    PlayView,
    Request,
    Session,
    Scope,
    Workspace,
    State,
    TurnStatus,
    ExportMode,
    ExportPreview,
    NativeAction,
} from "./model";
interface Operation {
    session: Session;
    epoch: number;
    request: Request;
    mode: FakeMode;
    submitted: boolean;
    cancelled: boolean;
    promise: Promise<void>;
}
export class Controller {
    private state: State = {
        exports: {
            shown: false,
            imported: false,
            mode: "diagnostics",
            busy: false,
            preview: null,
            savedLocation: null,
            selectedFile: "manifest.json",
            opened: null,
            storage: null,
            error: null,
            notice: "",
        },
        workspace: null,
        ephemeral: false,
        starting: false,
        sessions: [],
        selectedId: null,
        view: "play",
        observer: "player",
        play: null,
        inspection: null,
        inspectionRevision: null,
        inspectionObserver: null,
        pending: null,
        turnStatus: null,
        visibleError: null,
        draft: "",
        action: "give",
        fakeMode: "accepted",
        inspectorOpen: true,
        receiptTurn: null,
        page: 0,
        sidebarSize: 1,
        inspectorSize: 1,
        textScale: 100,
        diff: [],
        diffRevision: null,
        notice: "",
        disposed: false,
    };
    private listeners = new Set<() => void>();
    private drafts = new Map<string, string>();
    private epoch = 0;
    private inspectionEpoch = 0;
    private readSequence = 0;
    private nextTurn = 0;
    private operation: Operation | null = null;
    private unresolved: Operation | null = null;
    private outstanding = new Set<Promise<void>>();
    private exportEpoch = 0;
    constructor(
        readonly gateway: Gateway,
        readonly errors = new ErrorBuffer(),
        private prefix = `desktop-${crypto.randomUUID()}`,
    ) {}
    get = () => this.state;
    subscribe = (listener: () => void) => {
        this.listeners.add(listener);
        return () => {
            this.listeners.delete(listener);
        };
    };
    private patch(value: Partial<State>) {
        if (this.state.disposed) return;
        this.state = { ...this.state, ...value };
        this.listeners.forEach((listener) => listener());
    }
    selected() {
        return (
            this.state.sessions.find((s) => s.id === this.state.selectedId) ??
            null
        );
    }
    private current(operation: Pick<Operation, "session" | "epoch">) {
        return (
            !this.state.disposed &&
            operation.epoch === this.epoch &&
            operation.session.id === this.state.selectedId
        );
    }
    private fail(error: unknown) {
        const value = category(error);
        this.errors.add("frontend", value);
        this.patch({ visibleError: value });
    }
    private exportPatch(value: Partial<State["exports"]>) {
        this.patch({ exports: { ...this.state.exports, ...value } });
    }
    private native(command: NativeAction, args: Record<string, unknown> = {}) {
        if (!this.gateway.native)
            return Promise.reject(new Error("Unsupported"));
        return this.gateway.native(command, args);
    }
    showExports(shown = true) {
        this.exportPatch({ shown });
    }
    private clearExportPreview() {
        const token = this.state.exports.preview?.token;
        this.exportEpoch++;
        this.exportPatch({
            preview: null,
            imported: false,
            busy: false,
            opened: null,
            savedLocation: null,
            error: null,
            notice: "",
        });
        if (token)
            void this.native("inspection_cancel", { token }).catch(() => {});
    }
    setExportMode(mode: ExportMode) {
        if (
            !["diagnostics", "player", "full", "database"].includes(mode) ||
            this.state.exports.busy
        )
            return;
        this.clearExportPreview();
        this.exportPatch({ mode });
    }
    async previewExport() {
        const session = this.selected(),
            play = this.state.play;
        if (!session || !play || this.state.exports.busy) return;
        await this.cancelExport();
        const seq = ++this.exportEpoch,
            epoch = this.epoch,
            mode = this.state.exports.mode;
        this.exportPatch({
            busy: true,
            error: null,
            notice: "Capturing one authoritative head...",
        });
        try {
            const value = (await this.native(
                mode === "database"
                    ? "inspection_database_preview"
                    : "inspection_preview",
                {
                    session: session.id,
                    scope: session.scope,
                    expectedRevision: play.revision,
                    mode,
                },
            )) as ExportPreview;
            if (
                !value ||
                typeof value.token !== "string" ||
                value.token.length > 64 ||
                !value.manifest?.scope ||
                !sameScope(value.manifest.scope, session.scope) ||
                (mode !== "database" &&
                    value.manifest.revision !== play.revision) ||
                value.manifest.mode !== mode ||
                !Array.isArray(value.files) ||
                value.files.length > 9 ||
                value.files.some(
                    (f) =>
                        !f ||
                        typeof f.path !== "string" ||
                        !Number.isSafeInteger(f.bytes),
                )
            )
                throw new Error("Wire");
            if (
                seq !== this.exportEpoch ||
                epoch !== this.epoch ||
                session.id !== this.state.selectedId
            ) {
                await this.native("inspection_cancel", { token: value.token });
                return;
            }
            this.exportPatch({
                preview: value,
                imported: false,
                selectedFile: "manifest.json",
                savedLocation: null,
                opened: null,
                notice: "Preview captured. Saving writes these exact bytes, even if play advances.",
            });
        } catch (error) {
            if (seq === this.exportEpoch)
                this.exportPatch({
                    error: category(error),
                    notice: "No snapshot was saved.",
                });
        } finally {
            if (seq === this.exportEpoch) this.exportPatch({ busy: false });
        }
    }
    async saveExport() {
        const preview = this.state.exports.preview;
        if (!preview || this.state.exports.busy) return;
        const seq = this.exportEpoch;
        this.exportPatch({
            busy: true,
            error: null,
            notice: "Choose a destination in the native folder picker.",
        });
        try {
            const result = (await this.native("inspection_save", {
                token: preview.token,
            })) as { status: string; location?: string };
            if (seq !== this.exportEpoch) return;
            if (result.status === "cancelled")
                this.exportPatch({
                    notice: "Folder selection cancelled. Canon and preview are unchanged.",
                });
            else if (
                result.status === "saved" &&
                typeof result.location === "string"
            )
                this.exportPatch({
                    savedLocation: result.location,
                    notice: "Inspection snapshot saved. It is a derived, read-only view; editing it cannot change canon.",
                });
            else throw new Error("Wire");
        } catch (error) {
            if (seq === this.exportEpoch)
                this.exportPatch({
                    error: category(error),
                    notice: "The snapshot was not published. Canon is unchanged.",
                });
        } finally {
            if (seq === this.exportEpoch) this.exportPatch({ busy: false });
        }
    }
    async cancelExport() {
        const preview = this.state.exports.preview;
        if (preview) {
            try {
                const result = (await this.native("inspection_cancel", {
                    token: preview.token,
                })) as { status: string };
                if (result.status === "saved" && this.state.exports.busy) {
                    this.exportPatch({
                        notice: "Save completed before cancellation.",
                    });
                    return;
                }
            } catch {
                /* Expiry/window destruction already revokes the native preview. */
            }
        }
        this.exportEpoch++;
        this.exportPatch({
            preview: null,
            imported: false,
            busy: false,
            opened: null,
            savedLocation: null,
            error: null,
            notice: "",
        });
    }
    selectExportFile(selectedFile: string) {
        if (
            this.state.exports.preview?.files.some(
                (f) => f.path === selectedFile,
            )
        )
            this.exportPatch({ selectedFile, opened: null });
    }
    async openExport() {
        const e = this.state.exports;
        if (!e.preview || !e.savedLocation || e.busy) return;
        const seq = this.exportEpoch;
        this.exportPatch({ busy: true, error: null });
        try {
            const value = (await this.native("inspection_open", {
                token: e.preview.token,
                file: e.selectedFile,
            })) as {
                read_only: boolean;
                text: string;
                truncated: boolean;
                bytes: number;
                path: string;
            };
            if (
                !value ||
                value.read_only !== true ||
                typeof value.text !== "string" ||
                value.text.length > 65536 ||
                value.path !== e.selectedFile
            )
                throw new Error("Wire");
            if (seq === this.exportEpoch)
                this.exportPatch({
                    opened: value,
                    notice: "Verified saved files opened read-only in this app.",
                });
        } catch (error) {
            if (seq === this.exportEpoch)
                this.exportPatch({ error: category(error), opened: null });
        } finally {
            if (seq === this.exportEpoch) this.exportPatch({ busy: false });
        }
    }
    async loadExport() {
        if (this.state.exports.busy) return;
        await this.cancelExport();
        const seq = ++this.exportEpoch;
        this.exportPatch({ shown: true, busy: true, error: null });
        try {
            const result = (await this.native("inspection_load")) as {
                status: string;
                preview?: ExportPreview & { location: string };
            };
            if (seq !== this.exportEpoch) return;
            if (result.status === "cancelled") {
                this.exportPatch({ notice: "Folder selection cancelled." });
                return;
            }
            const preview = result.preview;
            if (
                !preview ||
                result.status !== "opened" ||
                typeof preview.token !== "string" ||
                !preview.manifest ||
                !Array.isArray(preview.files) ||
                preview.files.length > 9
            )
                throw new Error("Wire");
            this.exportPatch({
                preview,
                imported: true,
                mode: preview.manifest.mode,
                savedLocation: preview.location,
                selectedFile: "manifest.json",
                opened: null,
                notice: "Local inspection validated. Checksums establish file consistency, not authorship. These files are never imported into canon.",
            });
        } catch (error) {
            if (seq === this.exportEpoch)
                this.exportPatch({ error: category(error) });
        } finally {
            if (seq === this.exportEpoch) this.exportPatch({ busy: false });
        }
    }
    async revealStorage() {
        try {
            const value = (await this.native("inspection_storage")) as {
                location: string;
                schema_version: number;
                read_only: boolean;
            };
            if (
                !value ||
                value.read_only !== true ||
                typeof value.location !== "string"
            )
                throw new Error("Wire");
            this.exportPatch({ shown: true, storage: value, error: null });
        } catch (error) {
            this.exportPatch({ error: category(error) });
        }
    }
    async library() {
        const value = (await this.gateway.call({
            op: "workspace",
        })) as
            | Workspace
            | {
                  persistent: false;
                  location: null;
                  schema_version: null;
                  stories: [];
              };
        if (value && value.persistent === false) {
            if (
                value.location !== null ||
                value.schema_version !== null ||
                !Array.isArray(value.stories) ||
                value.stories.length !== 0
            )
                throw new Error("Wire");
            this.patch({ workspace: null, ephemeral: true });
            return value;
        }
        if (
            !value ||
            value.persistent !== true ||
            typeof value.location !== "string" ||
            value.schema_version !== 1 ||
            !Array.isArray(value.stories) ||
            value.stories.length > 256 ||
            value.stories.some(
                (s) =>
                    !s.scope ||
                    typeof s.title !== "string" ||
                    !Number.isSafeInteger(s.revision),
            )
        )
            throw new Error("Wire");
        this.patch({ workspace: value, ephemeral: false });
        return value;
    }
    async start() {
        this.patch({ starting: true, visibleError: null });
        try {
            const workspace = await this.library();
            // Shared library ordering is deterministic story-ID ordering.
            if (workspace?.stories.length)
                await this.resume(workspace.stories[0].scope);
            else await this.create();
        } catch (error) {
            this.fail(error);
        } finally {
            this.patch({ starting: false });
        }
    }
    async resume(scope: Scope) {
        const existing = this.state.sessions.find((s) =>
            sameScope(s.scope, scope),
        );
        if (existing) {
            await this.switchSession(existing.id);
            return;
        }
        if (this.state.sessions.length >= 4) {
            this.fail("SessionLimit");
            return;
        }
        if (this.state.selectedId)
            this.drafts.set(this.state.selectedId, this.state.draft);
        await this.invalidate();
        const epoch = this.epoch;
        try {
            const reply = (await this.gateway.call({
                op: "resume",
                scope,
            })) as {
                session: string;
                scope: Scope;
                revision: number;
                drafts?: number;
            };
            if (this.state.disposed || epoch !== this.epoch) {
                await this.gateway.call({
                    op: "close",
                    session: reply.session,
                    scope: reply.scope,
                });
                return;
            }
            if (
                !sameScope(reply.scope, scope) ||
                typeof reply.session !== "string" ||
                !Number.isSafeInteger(reply.revision)
            )
                throw new Error("Wire");
            const saved = this.state.workspace?.stories.find((s) =>
                sameScope(s.scope, scope),
            );
            const session = {
                id: reply.session,
                scope,
                revision: reply.revision,
                name: saved?.title ?? "Lantern Quay",
            };
            this.patch({
                sessions: [...this.state.sessions, session],
                selectedId: session.id,
                draft: "",
                play: null,
                pending: null,
                turnStatus: null,
                receiptTurn: null,
                diff: [],
                diffRevision: null,
                visibleError: null,
                page: 0,
                notice:
                    (reply.drafts ?? saved?.drafts ?? 0) > 0
                        ? "Saved uncommitted requests exist. They are not automatically committed or cancelled."
                        : "Resumed validated saved history.",
            });
            await this.refresh();
        } catch (error) {
            if (epoch === this.epoch) this.fail(error);
        }
    }
    async create() {
        if (this.state.selectedId)
            this.drafts.set(this.state.selectedId, this.state.draft);
        await this.invalidate();
        const epoch = this.epoch;
        try {
            const reply = (await this.gateway.call({
                op: "create",
                seed: "lantern-quay-v1",
            })) as {
                session: string;
                scope: Session["scope"];
                revision: number;
            };
            if (this.state.disposed || epoch !== this.epoch) {
                await this.gateway.call({
                    op: "close",
                    session: reply.session,
                    scope: reply.scope,
                });
                return;
            }
            const session = {
                id: reply.session,
                scope: reply.scope,
                revision: reply.revision,
                name: `Lantern Quay ${reply.session.split("-").at(-1)}`,
            };
            this.patch({
                sessions: [...this.state.sessions, session],
                selectedId: session.id,
                draft: "",
                play: null,
                pending: null,
                turnStatus: null,
                receiptTurn: null,
                diff: [],
                diffRevision: null,
                visibleError: null,
                notice: this.state.workspace
                    ? "New saved story. Earlier stories are retained."
                    : "New in-memory test session.",
                page: 0,
            });
            await this.refresh();
            if (this.state.workspace) await this.library();
        } catch (error) {
            if (epoch === this.epoch) this.fail(error);
        }
    }
    // Used by another application-owned view/test client; still opens the same Rust owner.
    async attach(session: Session) {
        await this.invalidate();
        this.patch({ sessions: [session], selectedId: session.id });
        await this.refresh();
    }
    async switchSession(id: string) {
        const session = this.state.sessions.find((s) => s.id === id);
        if (!session || id === this.state.selectedId) return;
        if (this.state.selectedId)
            this.drafts.set(this.state.selectedId, this.state.draft);
        await this.invalidate();
        this.patch({
            selectedId: id,
            draft: this.drafts.get(id) ?? "",
            play: null,
            pending: null,
            turnStatus: null,
            receiptTurn: null,
            diff: [],
            diffRevision: null,
            visibleError: null,
            page: 0,
        });
        await this.refresh();
    }
    async closeSession() {
        const session = this.selected();
        if (!session) return;
        await this.invalidate();
        try {
            await this.gateway.call({
                op: "close",
                session: session.id,
                scope: session.scope,
            });
        } catch (error) {
            this.fail(error);
            return;
        }
        this.drafts.delete(session.id);
        const sessions = this.state.sessions.filter((s) => s.id !== session.id);
        this.patch({
            sessions,
            selectedId: sessions[0]?.id ?? null,
            play: null,
            pending: null,
            turnStatus: null,
            draft: sessions[0] ? (this.drafts.get(sessions[0].id) ?? "") : "",
            receiptTurn: null,
            diff: [],
            diffRevision: null,
            visibleError: null,
            page: 0,
        });
        if (sessions.length) await this.refresh();
    }
    async reset() {
        const draft = this.state.draft;
        await this.closeSession();
        await this.create();
        this.setDraft(draft);
    }
    private async invalidate() {
        await this.cancelExport();
        const old = this.operation ?? this.unresolved;
        if (old) {
            old.cancelled = true;
            try {
                await this.control(old, "cancel");
            } catch {
                /* Close/switch fences every late completion as well. */
            }
        }
        this.epoch++;
        this.inspectionEpoch++;
        this.operation = null;
        this.unresolved = null;
        this.patch({
            pending: null,
            inspection: null,
            inspectionRevision: null,
            inspectionObserver: null,
        });
    }
    async refresh() {
        const session = this.selected();
        if (!session) return;
        const epoch = this.epoch;
        const sequence = ++this.readSequence;
        for (let attempt = 0; attempt < 3; attempt++) {
            try {
                const open = (await this.gateway.call({
                    op: "open",
                    session: session.id,
                    scope: session.scope,
                })) as { revision: number };
                const view = playView(
                    await this.gateway.call({
                        op: "play_snapshot",
                        session: session.id,
                        scope: session.scope,
                        expected_revision: open.revision,
                    }),
                    session.scope,
                    open.revision,
                );
                if (
                    !this.current({ session, epoch }) ||
                    sequence !== this.readSequence ||
                    (this.state.play &&
                        this.state.play.revision > view.revision)
                )
                    return;
                this.patch({
                    play: view,
                    sessions: this.state.sessions.map((s) =>
                        s.id === session.id
                            ? { ...s, revision: view.revision }
                            : s,
                    ),
                    page: Math.min(
                        this.state.page,
                        Math.max(
                            0,
                            Math.ceil(view.receipts.length / PAGE_SIZE) - 1,
                        ),
                    ),
                });
                await this.inspect();
                return;
            } catch (error) {
                if (
                    !this.current({ session, epoch }) ||
                    sequence !== this.readSequence
                )
                    return;
                if (category(error) !== "Stale" || attempt === 2) {
                    this.fail(error);
                    return;
                }
            }
        }
    }
    async inspect() {
        const session = this.selected(),
            play = this.state.play;
        const epoch = ++this.inspectionEpoch,
            observer =
                this.state.view === "play" ? "player" : this.state.observer;
        this.patch({
            inspection: null,
            inspectionRevision: null,
            inspectionObserver: null,
        });
        if (!session || !play || this.state.view !== "lab") return;
        try {
            const value = (await this.gateway.call({
                op: "inspect",
                session: session.id,
                scope: session.scope,
                observer,
                expected_revision: play.revision,
            })) as Json;
            if (
                epoch !== this.inspectionEpoch ||
                this.state.selectedId !== session.id ||
                this.state.play?.revision !== play.revision ||
                this.state.view !== "lab" ||
                observer !== this.state.observer
            )
                return;
            this.patch({
                inspection: value,
                inspectionRevision: play.revision,
                inspectionObserver: observer,
            });
        } catch (error) {
            if (epoch === this.inspectionEpoch) this.fail(error);
        }
    }
    setView(view: State["view"]) {
        if (view === "play" && this.state.exports.mode === "full") {
            this.clearExportPreview();
            this.exportPatch({ mode: "diagnostics" });
        }
        this.patch({
            view,
            observer: view === "play" ? "player" : "omniscient",
            visibleError: null,
        });
        void this.inspect();
    }
    setObserver(observer: string) {
        if (this.state.view !== "lab") return;
        this.patch({ observer });
        void this.inspect();
    }
    setDraft(draft: string) {
        this.patch({ draft: draft.slice(0, 2048) });
    }
    setAction(action: Action) {
        this.patch({ action });
    }
    setFakeMode(fakeMode: FakeMode) {
        this.patch({ fakeMode });
    }
    setInspector(inspectorOpen: boolean) {
        this.patch({ inspectorOpen });
    }
    layout(sidebarSize: number, inspectorSize: number, textScale: number) {
        this.patch({
            sidebarSize: Math.max(0, Math.min(2, sidebarSize)),
            inspectorSize: Math.max(0, Math.min(2, inspectorSize)),
            textScale: [100, 125, 150, 200].includes(textScale)
                ? textScale
                : 100,
        });
    }
    page(page: number) {
        const count = this.state.play?.receipts.length ?? 0;
        this.patch({
            page: Math.max(
                0,
                Math.min(Math.max(0, Math.ceil(count / PAGE_SIZE) - 1), page),
            ),
        });
    }
    selectReceipt(receiptTurn: string) {
        if (
            this.state.play?.receipts.some(
                (r) => r.request.turn === receiptTurn,
            )
        )
            this.patch({ receiptTurn, inspectorOpen: true });
    }
    private control(
        op: Operation,
        action: "prepare" | "commit" | "cancel" | "turn_status",
    ) {
        return this.gateway.call({
            op: action,
            session: op.session.id,
            scope: op.session.scope,
            turn: op.request.turn,
        }) as Promise<TurnStatus>;
    }
    send(): Promise<void> {
        if (this.operation) return this.operation.promise;
        if (this.unresolved) {
            const op = this.unresolved;
            this.operation = op;
            this.patch({
                pending: {
                    session: op.session.id,
                    scope: op.session.scope,
                    turn: op.request.turn,
                    expectedRevision: op.request.expected_revision,
                    stage: "recovering",
                },
            });
            op.promise = this.recover(op).finally(() => {
                this.outstanding.delete(op.promise);
                if (this.operation === op) {
                    this.operation = null;
                    this.patch({ pending: null });
                }
            });
            this.outstanding.add(op.promise);
            return op.promise;
        }
        const session = this.selected(),
            play = this.state.play;
        if (!session || !play || this.state.disposed) {
            this.fail("SessionRequired");
            return Promise.resolve();
        }
        if (this.state.action === "dialogue" && !this.state.draft.trim()) {
            this.fail("DraftRequired");
            return Promise.resolve();
        }
        const op: Operation = {
            session,
            epoch: this.epoch,
            request: request(
                session.scope,
                `${this.prefix}-${++this.nextTurn}`,
                play.revision,
                this.state.action,
                this.state.draft,
            ),
            mode: this.state.fakeMode,
            submitted: false,
            cancelled: false,
            promise: Promise.resolve(),
        };
        const mode = this.state.fakeMode;
        this.operation = op;
        this.patch({
            pending: {
                session: session.id,
                scope: session.scope,
                turn: op.request.turn,
                expectedRevision: play.revision,
                stage: "submitting",
            },
            visibleError: null,
            notice: "",
        });
        op.promise = this.run(op, mode, play).finally(() => {
            this.outstanding.delete(op.promise);
            if (this.operation === op) {
                this.operation = null;
                this.patch({ pending: null });
            }
        });
        this.outstanding.add(op.promise);
        return op.promise;
    }
    private async run(op: Operation, mode: FakeMode, before: PlayView) {
        try {
            this.unresolved = op;
            let status = (await this.gateway.call({
                op: "submit",
                session: op.session.id,
                request: op.request,
                mode,
            })) as TurnStatus;
            op.submitted = true;
            if (op.cancelled || !this.current(op)) {
                const cancelled = await this.control(op, "cancel");
                if (this.current(op))
                    await this.publishResult(op, cancelled, before);
                return;
            }
            this.patch({
                turnStatus: status,
                pending: { ...this.state.pending!, stage: "generating" },
            });
            status = await this.control(op, "prepare");
            if (op.cancelled || !this.current(op)) {
                const cancelled = await this.control(op, "cancel");
                if (this.current(op))
                    await this.publishResult(op, cancelled, before);
                return;
            }
            this.patch({ turnStatus: status });
            if (status.phase === "ready") {
                try {
                    status = await this.control(op, "commit");
                } catch {
                    status = await this.control(op, "turn_status");
                    if (
                        status.phase === "ready" ||
                        status.phase === "running"
                    ) {
                        this.unresolved = op;
                        throw new Error("TransportUnknown");
                    }
                }
            }
            await this.publishResult(op, status, before);
        } catch (error) {
            if (this.current(op) && this.unresolved === op) {
                const uncertain = [
                    "Transport",
                    "TransportUnknown",
                    "Wire",
                ].includes(category(error));
                const value = uncertain ? "TransportUnknown" : category(error);
                if (!uncertain && this.unresolved === op)
                    this.unresolved = null;
                this.patch({
                    turnStatus: {
                        turn: op.request.turn,
                        scope: op.session.scope,
                        expected_revision: op.request.expected_revision,
                        phase: uncertain
                            ? "unknown"
                            : op.submitted
                              ? "failed"
                              : "rejected",
                        error: value,
                        receipt: null,
                    },
                });
                this.fail(value);
            }
        }
    }
    private async publishResult(
        op: Operation,
        status: TurnStatus,
        before: PlayView,
    ) {
        if (!this.current(op)) return;
        if (
            !status ||
            !status.scope ||
            status.turn !== op.request.turn ||
            !sameScope(status.scope, op.session.scope) ||
            status.expected_revision !== op.request.expected_revision ||
            ![
                "queued",
                "running",
                "ready",
                "committed",
                "cancelled",
                "failed",
                "stale",
            ].includes(status.phase)
        )
            throw new Error("Wire");
        if (
            status.phase === "committed" &&
            (!status.receipt ||
                structural(status.receipt.request) !== structural(op.request) ||
                !Array.isArray(status.receipt.events) ||
                !status.receipt.events.length ||
                status.receipt.events.some(
                    (e) =>
                        !e.scope ||
                        !sameScope(e.scope, op.session.scope) ||
                        !Number.isSafeInteger(e.sequence),
                ) ||
                typeof status.receipt.narration !== "string")
        )
            throw new Error("Wire");
        this.patch({
            turnStatus: status,
            visibleError:
                status.phase === "committed" || status.phase === "cancelled"
                    ? null
                    : (status.error ?? status.phase),
        });
        if (status.phase === "cancelled")
            this.patch({ notice: "Cancelled before commit. Draft preserved." });
        if (status.phase === "committed") {
            if (!status.receipt) throw new Error("Wire");
            this.patch({
                receiptTurn: status.receipt.request.turn,
                notice: this.state.workspace
                    ? "Committed and saved by the local Rust engine."
                    : "Committed by the local Rust engine.",
            });
            if (
                op.request.intent.kind === "dialogue" &&
                this.state.draft === op.request.intent.value.text
            )
                this.patch({ draft: "" });
        }
        if (
            ["committed", "cancelled", "failed", "stale"].includes(
                status.phase,
            ) &&
            this.unresolved === op
        )
            this.unresolved = null;
        await this.refresh();
        if (this.state.workspace) await this.library();
        if (
            this.current(op) &&
            status.phase === "committed" &&
            this.state.play
        ) {
            this.patch({
                diff: difference(
                    { player: before.player, inventory: before.inventory },
                    {
                        player: this.state.play.player,
                        inventory: this.state.play.inventory,
                    },
                ),
                diffRevision: this.state.play.revision,
                page: Math.max(
                    0,
                    Math.ceil(this.state.play.receipts.length / PAGE_SIZE) - 1,
                ),
            });
        }
    }
    async pendingStatus() {
        const op = this.operation;
        if (!op?.submitted) return null;
        const status = await this.control(op, "turn_status");
        if (this.current(op)) this.patch({ turnStatus: status });
        return status;
    }
    async cancel() {
        const op = this.operation;
        if (!op) return;
        op.cancelled = true;
        this.patch({
            pending: this.state.pending
                ? { ...this.state.pending, stage: "cancelling" }
                : null,
        });
        try {
            const status = await this.control(op, "cancel");
            if (this.current(op))
                await this.publishResult(op, status, this.state.play!);
        } catch {
            if (this.current(op)) this.fail("TransportUnknown");
        }
    }
    retry() {
        this.patch({ visibleError: null });
        return this.send();
    }
    private async recover(op: Operation) {
        try {
            let status: TurnStatus;
            try {
                status = await this.control(op, "turn_status");
            } catch (error) {
                if (!this.current(op) || this.unresolved !== op) return;
                if (category(error) !== "UnknownTurn") throw error;
                status = (await this.gateway.call({
                    op: "submit",
                    session: op.session.id,
                    request: op.request,
                    mode: op.mode,
                })) as TurnStatus;
                op.submitted = true;
            }
            if (!this.current(op) || this.unresolved !== op) return;
            if (op.cancelled) {
                status = await this.control(op, "cancel");
                await this.publishResult(op, status, this.state.play!);
                return;
            }
            if (status.phase === "queued")
                status = await this.control(op, "prepare");
            if (!this.current(op) || this.unresolved !== op) return;
            if (op.cancelled) {
                status = await this.control(op, "cancel");
                await this.publishResult(op, status, this.state.play!);
                return;
            }
            if (status.phase === "ready")
                status = await this.control(op, "commit");
            if (!this.current(op) || this.unresolved !== op) return;
            if (
                status.phase === "committed" ||
                ["failed", "cancelled", "stale"].includes(status.phase)
            ) {
                await this.publishResult(op, status, this.state.play!);
            } else if (this.current(op)) this.fail("TransportUnknown");
        } catch {
            if (this.current(op) && this.unresolved === op)
                this.fail("TransportUnknown");
        }
    }
    receipt() {
        const receipts = this.state.play?.receipts ?? [];
        return (
            receipts.find((r) => r.request.turn === this.state.receiptTurn) ??
            receipts.at(-1) ??
            null
        );
    }
    async copyReceipt(write: (text: string) => Promise<void>) {
        const receipt = this.receipt();
        if (!receipt) return;
        try {
            await write(JSON.stringify(receipt, null, 2));
            this.patch({
                notice: "Selected receipt copied by your explicit action.",
            });
        } catch {
            this.fail("CopyFailed");
        }
    }
    semantic() {
        const s = this.state,
            session = this.selected();
        return {
            version: 1,
            exports: s.exports,
            workspace: s.workspace,
            ephemeral: s.ephemeral,
            synthetic: true,
            uiRevision: s.play?.revision ?? 0,
            view: s.view,
            session,
            observer: s.view === "play" ? "player" : s.observer,
            pending: s.pending,
            turnStatus: s.turnStatus,
            receipt: this.receipt(),
            visibleError: s.visibleError,
            inspection:
                s.inspection === null
                    ? null
                    : {
                          revision: s.inspectionRevision,
                          observer: s.inspectionObserver,
                          data: s.inspection,
                      },
            rules: s.play?.rules ?? null,
            player: s.play?.player ?? null,
            inventory: s.play?.inventory ?? null,
            transcript: {
                page: s.page,
                total: s.play?.receipts.length ?? 0,
                rows:
                    s.play?.receipts.slice(
                        s.page * PAGE_SIZE,
                        (s.page + 1) * PAGE_SIZE,
                    ) ?? [],
            },
            draft: s.draft,
            diff: s.diff,
            diffRevision: s.diffRevision,
            layout: {
                textScale: s.textScale,
                sidebarSize: s.sidebarSize,
                inspectorSize: s.inspectorSize,
                inspectorOpen: s.inspectorOpen,
            },
            errors: this.errors.snapshot(),
            disposed: s.disposed,
        };
    }
    async dispose() {
        if (this.state.disposed) return;
        await this.invalidate();
        const sessions = this.state.sessions;
        this.state = {
            ...this.state,
            disposed: true,
            pending: null,
            inspection: null,
            inspectionRevision: null,
            inspectionObserver: null,
            play: null,
            sessions: [],
            selectedId: null,
            draft: "",
            turnStatus: null,
            receiptTurn: null,
        };
        this.listeners.forEach((listener) => listener());
        this.listeners.clear();
        this.drafts.clear();
        await Promise.allSettled(
            sessions.map((s) =>
                this.gateway.call({
                    op: "close",
                    session: s.id,
                    scope: s.scope,
                }),
            ),
        );
        await Promise.allSettled([...this.outstanding]);
    }
}
