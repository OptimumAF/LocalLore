import { initialTrace, checkedTrace, attemptKey } from "./trace-model";
import type { TraceQuery } from "./trace-model";
import { initialQuery, checkedPage } from "./query-model";
import { checkedPlaySnapshotV2 } from "./v2-view-model";
import type { InspectionQuery, Source, Row } from "./query-model";
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
    ModelState,
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
        trace: initialTrace(),
        query: initialQuery(),
        labPending: false,
        model: null,
        modelBusy: false,
        modelCancelReady: false,
        modelShown: false,
        playMode: "fixture",
        inputKind: "action",
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
        playV2: null,
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
    private modelOperation: { baseline: number; id: number | null } | null =
        null;
    private modelReadSequence = 0;
    private listeners = new Set<() => void>();
    private drafts = new Map<string, string>();
    private epoch = 0;
    private inspectionEpoch = 0;
    private queryEpoch = 0;
    private traceEpoch = 0;
    private traceControlPending = false;
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
        private coordinatePrivateMetadata: (
            work: () => Promise<void>,
        ) => Promise<void> = (work) => work(),
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
    private clearExportPreview(cancelNative = true) {
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
        if (token && cancelNative)
            void this.native("inspection_cancel", { token }).catch(() => {});
        return token;
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
        const token = this.clearExportPreview(false);
        if (token) {
            try {
                await this.native("inspection_cancel", { token });
            } catch {
                /* Native expiry or window destruction already revokes authority. */
            }
        }
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
            const savedStory = this.state.workspace?.stories.find(
                (s) => s.scope.story === scope.story,
            );
            const saved =
                savedStory && sameScope(savedStory.scope, scope)
                    ? savedStory
                    : undefined;
            const session = {
                id: reply.session,
                scope,
                revision: reply.revision,
                name: savedStory?.title ?? "Saved story",
            };
            this.patch({
                sessions: [...this.state.sessions, session],
                selectedId: session.id,
                draft: "",
                play: null,
                playV2: null,
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
                playV2: null,
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
            playV2: null,
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
            playV2: null,
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
        const old = this.operation ?? this.unresolved;
        if (old) old.cancelled = true;
        this.clearTrace(true);
        this.clearQuery(true);
        await this.cancelExport();
        if (old?.submitted) {
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
                if (this.gateway.playSnapshotV2) {
                    const thin = checkedPlaySnapshotV2(
                        await this.gateway.call({
                            op: "play_snapshot_v2",
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
                        (this.state.playV2 &&
                            this.state.playV2.revision > thin.revision)
                    )
                        return;
                    if (
                        thin.domain_version === 2 ||
                        thin.player.observer !== "player"
                    ) {
                        this.clearQuery();
                        this.clearTrace();
                        this.queryPatch({ shown: false });
                        this.tracePatch({ shown: false });
                        this.patch({
                            play: null,
                            playV2: thin,
                            inspection: null,
                            inspectionRevision: null,
                            inspectionObserver: null,
                            sessions: this.state.sessions.map((s) =>
                                s.id === session.id
                                    ? { ...s, revision: thin.revision }
                                    : s,
                            ),
                        });
                        return;
                    }
                }
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
                if (this.state.play?.revision !== view.revision) {
                    this.clearQuery();
                    this.clearTrace();
                    this.tracePatch({
                        baseRevision:
                            view.receipts.at(-1)?.request.expected_revision ??
                            view.revision,
                    });
                }
                this.patch({
                    play: view,
                    playV2: null,
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
                if (this.state.query.shown) await this.queryInspection();
                if (this.state.trace.shown) void this.readTrace();
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
    private tracePatch(value: Partial<State["trace"]>) {
        this.patch({ trace: { ...this.state.trace, ...value } });
    }
    private clearTrace(reset = false) {
        this.traceEpoch++;
        this.tracePatch({
            reply: null,
            selected: null,
            busy: false,
            error: null,
            notice: "",
            ...(reset ? { baseRevision: 0 } : {}),
        });
    }
    private traceContext(): TraceQuery | null {
        const session = this.selected(),
            play = this.state.play;
        if (!session || !play || this.state.disposed) return null;
        const lens =
            this.state.view === "play" ? "player" : this.state.observer;
        return {
            op: "trace_read",
            session: session.id,
            scope: session.scope,
            expected_head: play.revision,
            base_revision: this.state.trace.baseRevision,
            observer:
                lens === "player"
                    ? { kind: "player" }
                    : lens === "omniscient"
                      ? { kind: "omniscient" }
                      : { kind: "character", id: lens },
            turn: null,
            attempt: null,
        };
    }
    private sameTraceContext(query: TraceQuery) {
        const current = this.traceContext();
        return (
            this.state.trace.shown &&
            current !== null &&
            structural(current) === structural(query)
        );
    }
    async showTrace(shown = true) {
        this.clearTrace();
        if (shown) {
            this.clearQuery();
            this.queryPatch({ shown: false });
        }
        this.tracePatch({ shown });
        if (shown) await this.readTrace();
    }
    async traceBasis(baseRevision: number) {
        if (
            !Number.isSafeInteger(baseRevision) ||
            baseRevision < 0 ||
            baseRevision > (this.state.play?.revision ?? 0)
        )
            return;
        this.clearTrace();
        this.tracePatch({ baseRevision });
        await this.readTrace();
    }
    async readTrace() {
        const query = this.traceContext();
        if (!query || !this.state.trace.shown) return;
        const sequence = ++this.traceEpoch,
            selected = this.state.trace.selected,
            player = this.state.play!.player.observer;
        this.tracePatch({
            busy: true,
            reply: null,
            selected: null,
            error: null,
            notice: "",
        });
        try {
            const value = checkedTrace(
                await this.gateway.call(query),
                query,
                player,
            );
            if (sequence !== this.traceEpoch || !this.sameTraceContext(query))
                return;
            const attempts = value.snapshot.attempts;
            this.tracePatch({
                busy: false,
                reply: value,
                enabled: value.snapshot.status !== "disabled",
                selected: attempts.some((a) => attemptKey(a) === selected)
                    ? selected
                    : attempts.length
                      ? attemptKey(attempts.at(-1)!)
                      : null,
            });
        } catch (error) {
            if (sequence === this.traceEpoch && this.sameTraceContext(query))
                this.tracePatch({ busy: false, error: category(error) });
        }
    }
    async controlTrace(action: "enable" | "disable" | "clear") {
        const query = this.traceContext();
        if (!query || this.traceControlPending) return;
        this.traceControlPending = true;
        this.clearTrace();
        this.tracePatch({ controlBusy: true });
        const work = async () => {
            let succeeded = false;
            try {
                const command: Command =
                    action === "clear"
                        ? {
                              op: "trace_clear",
                              session: query.session,
                              scope: query.scope,
                              expected_head: query.expected_head,
                          }
                        : {
                              op: "trace_configure",
                              session: query.session,
                              scope: query.scope,
                              expected_head: query.expected_head,
                              enabled: action === "enable",
                          };
                const value = (await this.gateway.call(command)) as Record<
                    string,
                    unknown
                >;
                if (
                    !value ||
                    value.configuration_scope !== "window_host" ||
                    value.capture !== "metadata_only" ||
                    value.full_capture !== "unsupported" ||
                    (action === "clear"
                        ? value.cleared !== true
                        : value.enabled !== (action === "enable"))
                )
                    throw new Error("Wire");
                succeeded = true;
            } catch (error) {
                if (this.sameTraceContext(query))
                    this.tracePatch({ error: category(error), enabled: null });
            } finally {
                this.traceControlPending = false;
                this.tracePatch({ controlBusy: false });
            }
            if (succeeded && this.state.trace.shown) await this.readTrace();
        };
        if (action === "enable") await work();
        else await this.coordinatePrivateMetadata(work);
    }
    selectTrace(selected: string) {
        if (
            this.state.trace.reply?.snapshot.attempts.some(
                (a) => attemptKey(a) === selected,
            )
        )
            this.tracePatch({ selected });
    }
    traceAttempt() {
        return (
            this.state.trace.reply?.snapshot.attempts.find(
                (a) => attemptKey(a) === this.state.trace.selected,
            ) ?? null
        );
    }
    debugReceipt() {
        const a = this.traceAttempt();
        if (
            !a ||
            this.state.view !== "play" ||
            a.identity.observer !== this.state.play?.player.observer
        )
            return null;
        return (
            this.state.play.receipts.find(
                (r) =>
                    r.request.turn === a.identity.turn &&
                    r.request.expected_revision === a.identity.base_revision &&
                    sameScope(r.request.scope, a.identity.scope),
            ) ?? null
        );
    }
    async traceToInspection() {
        const receipt = this.debugReceipt(),
            epoch = this.epoch,
            session = this.selected(),
            view = this.state.view,
            observer = this.state.observer,
            head = this.state.play?.revision;
        if (!receipt || !session) return;
        const current = () =>
            this.current({ session, epoch }) &&
            this.state.view === view &&
            this.state.observer === observer &&
            this.state.play?.revision === head;
        this.patch({ receiptTurn: receipt.request.turn });
        await this.showTrace(false);
        if (!current()) return;
        const opening = this.showQuery(true);
        const queryEpoch = this.queryEpoch;
        await opening;
        if (
            !current() ||
            !this.state.query.shown ||
            queryEpoch !== this.queryEpoch
        )
            return;
        await this.browseInspection({
            view: "turn_diff",
            atRevision: receipt.events.at(-1)?.sequence ?? null,
            search: "",
        });
    }
    private queryPatch(value: Partial<State["query"]>) {
        this.patch({ query: { ...this.state.query, ...value } });
    }
    private clearQuery(resetContext = false) {
        this.queryEpoch++;
        this.queryPatch({
            page: null,
            busy: false,
            error: null,
            selectedKey: null,
            cursor: null,
            cursors: [],
            notice: "",
            trace: null,
            ...(resetContext ? { search: "", atRevision: null } : {}),
        });
    }
    returnToPlay() {
        void this.showQuery(false);
        this.setView("play");
    }
    async showQuery(shown = true) {
        if (shown) {
            this.clearTrace();
            this.tracePatch({ shown: false });
        }
        this.clearQuery();
        this.queryPatch({ shown });
        if (shown) await this.queryInspection();
    }
    async browseInspection(
        value: Partial<
            Pick<State["query"], "view" | "atRevision" | "search" | "limit">
        >,
    ) {
        this.clearQuery();
        this.queryPatch(value);
        await this.queryInspection();
    }
    async queryInspection(cursor: string | null = this.state.query.cursor) {
        const session = this.selected(),
            play = this.state.play;
        if (!session || !play || !this.state.query.shown) return;
        const seq = ++this.queryEpoch,
            epoch = this.epoch;
        const observer: InspectionQuery["observer"] =
            this.state.view === "play" || this.state.observer === "player"
                ? { kind: "player" }
                : this.state.observer === "omniscient"
                  ? { kind: "omniscient" }
                  : { kind: "character", id: this.state.observer };
        const state = this.state.query;
        const query: InspectionQuery = {
            version: 1,
            scope: { ...session.scope },
            expected_head: play.revision,
            at_revision: state.atRevision,
            observer,
            view: state.view,
            cursor,
            limit: state.limit,
            search: state.search,
        };
        const key = structural({
            session: session.id,
            query,
            view: this.state.view,
        });
        const stillCurrent = () =>
            seq === this.queryEpoch &&
            this.current({ session, epoch }) &&
            this.state.query.shown &&
            key ===
                structural({
                    session: this.state.selectedId,
                    query: {
                        ...query,
                        expected_head: this.state.play?.revision,
                        at_revision: this.state.query.atRevision,
                        observer:
                            this.state.view === "play" ||
                            this.state.observer === "player"
                                ? { kind: "player" }
                                : this.state.observer === "omniscient"
                                  ? { kind: "omniscient" }
                                  : {
                                        kind: "character",
                                        id: this.state.observer,
                                    },
                        view: this.state.query.view,
                        search: this.state.query.search,
                        limit: this.state.query.limit,
                        cursor: this.state.query.cursor,
                    },
                    view: this.state.view,
                });
        this.queryPatch({
            busy: true,
            error: null,
            page: null,
            selectedKey: null,
            cursor,
            notice: "",
        });
        try {
            const page = checkedPage(
                await this.gateway.call({
                    op: "inspection_query",
                    session: session.id,
                    query,
                }),
                query,
            );
            if (!stillCurrent()) return;
            this.queryPatch({ page });
        } catch (error) {
            if (stillCurrent())
                this.queryPatch({
                    error: category(error),
                    notice:
                        category(error) === "Stale"
                            ? "Story changed. Refresh the current head before inspecting again."
                            : category(error) === "TooLarge"
                              ? "The search, row or page exceeds inspection limits. Shorten the search or reduce the page size."
                              : category(error) === "InvalidBoundary"
                                ? "Choose revision 0, current, or the end of a completed turn. Partial turns cannot be inspected."
                                : category(error) === "InvalidRequest"
                                  ? "Search allows 256 UTF-8 bytes without control characters. No inspection data is shown."
                                  : category(error) === "UnsupportedBranch"
                                    ? "Historical inspection for this branch is not implemented."
                                    : "No inspection data is shown for this request.",
                });
        } finally {
            if (stillCurrent()) this.queryPatch({ busy: false });
        }
    }
    async nextInspection() {
        const q = this.state.query;
        if (q.busy || !q.page?.next_cursor) return;
        this.queryPatch({ cursors: [...q.cursors, q.cursor] });
        await this.queryInspection(q.page.next_cursor);
    }
    async previousInspection() {
        const q = this.state.query;
        if (q.busy || !q.cursors.length) return;
        const cursors = [...q.cursors],
            cursor = cursors.pop()!;
        this.queryPatch({ cursors });
        await this.queryInspection(cursor);
    }
    selectInspection(key: string) {
        if (this.state.query.page?.rows.some((row) => row.key === key))
            this.queryPatch({ selectedKey: key });
    }
    async followInspectionSource(source: Source) {
        if (source.kind === "withheld") return null;
        const pending = this.browseInspection(
            source.kind === "seed"
                ? { view: "profiles", atRevision: 0, search: "" }
                : { view: "history", search: `"sequence":${source.value},` },
        );
        const sequence = this.queryEpoch;
        await pending;
        if (sequence !== this.queryEpoch || !this.state.query.page) return null;
        const row = this.state.query.page.rows.find(
            (r) =>
                source.kind === "seed" ||
                (r.kind === "event" && r.event.sequence === source.value),
        );
        if (row) this.selectInspection(row.key);
        return row ? sequence : null;
    }
    async whyInspection(row: Row) {
        const page = this.state.query.page;
        // A delayed click must not transplant a row from a previous private lens.
        if (!page?.rows.includes(row)) return;
        if (row.kind === "provenance") {
            this.queryPatch({
                notice: "This record already lists its permitted sources.",
            });
            return;
        }
        if (row.kind === "event") {
            const sourceEpoch = await this.followInspectionSource({
                kind: "event",
                value: row.event.sequence,
            });
            if (
                sourceEpoch !== null &&
                sourceEpoch === this.queryEpoch &&
                this.state.query.page?.rows.some(
                    (r) =>
                        r.kind === "event" &&
                        r.event.sequence === row.event.sequence,
                )
            )
                this.queryPatch({
                    notice: "Accepted event source; this observation has no separate field-provenance row.",
                });
            return;
        }
        if (row.kind === "message") {
            if (!row.event_ids.length) {
                this.queryPatch({
                    notice: "No accepted event source is attached to this recorded message.",
                });
                return;
            }
            const pending = this.browseInspection({
                view: "history",
                atRevision: page.revision,
                search: `"turn":${JSON.stringify(row.turn)},`,
            });
            const sequence = this.queryEpoch;
            await pending;
            if (sequence !== this.queryEpoch || !this.state.query.page) return;
            const event = this.state.query.page.rows.find(
                (r) =>
                    r.kind === "event" &&
                    row.event_ids.includes(r.event.sequence),
            );
            if (event) this.selectInspection(event.key);
            this.queryPatch({
                notice: event
                    ? "Permitted accepted events support this display record; the message itself is not canonical truth."
                    : "No supporting accepted event is visible in this lens and page.",
            });
            return;
        }
        const underlying =
            row.kind === "change" ? (row.after ?? row.before!) : row;
        const revision =
            row.kind === "change"
                ? row.after
                    ? row.after_revision
                    : row.before_revision
                : page.revision;
        const pending = this.browseInspection({
            view: "provenance",
            atRevision: revision,
            search: JSON.stringify(underlying.key),
        });
        const sequence = this.queryEpoch;
        await pending;
        if (sequence !== this.queryEpoch || !this.state.query.page) return;
        const record = this.state.query.page.rows.find(
            (r) => r.kind === "provenance" && r.key === underlying.key,
        );
        if (record) this.selectInspection(record.key);
        this.queryPatch({
            trace:
                row.kind === "change"
                    ? {
                          change: row,
                          stage: row.after
                              ? "field_provenance"
                              : "prior_provenance",
                      }
                    : null,
            notice: record
                ? row.kind === "change" && !row.after
                    ? `Prior field provenance at r${revision}; the field is absent at r${row.after_revision}. This is not a current field.`
                    : "Permitted field provenance at the inspected revision."
                : "Field provenance is unavailable in this lens and snapshot. No substitute evidence is asserted.",
        });
    }
    async showChangeTurnHistory() {
        const trace = this.state.query.trace;
        if (!trace) return;
        const change = trace.change;
        // Resolve the boundary event through the same observer-filtered API. Never
        // look up raw Player receipts to discover a private turn ID for an NPC.
        let pending = this.browseInspection({
            view: "history",
            atRevision: change.after_revision,
            search: `"sequence":${change.after_revision},`,
        });
        let sequence = this.queryEpoch;
        await pending;
        if (sequence !== this.queryEpoch || !this.state.query.page) return;
        const boundary = this.state.query.page.rows.find(
            (r) =>
                r.kind === "event" &&
                r.event.sequence === change.after_revision,
        );
        if (boundary?.kind !== "event") {
            this.queryPatch({
                trace: { change, stage: "turn_history" },
                notice: "The completed-head event is not visible to this lens. Causal event evidence is unavailable; no hidden turn is inferred.",
            });
            return;
        }
        pending = this.browseInspection({
            view: "history",
            atRevision: change.after_revision,
            search: `"turn":${JSON.stringify(boundary.event.turn)},`,
        });
        sequence = this.queryEpoch;
        await pending;
        if (sequence !== this.queryEpoch || !this.state.query.page) return;
        const event = this.state.query.page.rows.find(
            (r) =>
                r.kind === "event" &&
                r.event.sequence === change.after_revision,
        );
        if (event) this.selectInspection(event.key);
        this.queryPatch({
            trace: { change, stage: "turn_history" },
            notice: "Permitted accepted history for the completed turn in which this change occurred. A turn may contain several effects; no single-event cause is inferred.",
        });
    }
    async traceReceipt() {
        const receipt = this.receipt();
        if (!receipt) return;
        if (!this.state.query.shown) await this.showQuery();
        await this.inspectEventTurn(receipt.request.turn);
    }
    async capturedEvidence(
        nativeSessionId: string,
        expectedScope: Scope,
        turn: string,
        baseRevision: number,
    ) {
        const session = this.selected(),
            epoch = this.epoch,
            head = this.state.play?.revision;
        if (
            !session ||
            session.id !== nativeSessionId ||
            !sameScope(expectedScope, session.scope) ||
            this.state.view !== "lab" ||
            this.state.observer !== "omniscient"
        )
            return;
        const receipt = this.state.play?.receipts.find(
            (r) =>
                r.request.turn === turn &&
                r.request.expected_revision === baseRevision &&
                sameScope(r.request.scope, session.scope),
        );
        if (!receipt) return;
        const opening = this.showQuery(true),
            queryEpoch = this.queryEpoch;
        await opening;
        if (
            !this.current({ session, epoch }) ||
            this.queryEpoch !== queryEpoch ||
            !this.state.query.shown ||
            this.state.view !== "lab" ||
            this.state.observer !== "omniscient" ||
            this.state.play?.revision !== head
        )
            return;
        await this.inspectEventTurn(turn);
    }
    async inspectEventTurn(turn: string) {
        const boundary = this.state.play?.receipts
            .find((r) => r.request.turn === turn)
            ?.events.at(-1)?.sequence;
        if (boundary === undefined) {
            this.queryPatch({
                notice: "Completed turn boundary is unavailable in this snapshot.",
            });
            return;
        }
        await this.browseInspection({
            view: "turn_diff",
            atRevision: boundary,
            search: "",
        });
    }
    async copyInspection(write: (text: string) => Promise<void>) {
        const q = this.state.query,
            row = q.page?.rows.find((r) => r.key === q.selectedKey);
        if (!row || !q.page || q.busy) return;
        const context = {
            scope: q.page.scope,
            head: q.page.head,
            revision: q.page.revision,
            observer: q.page.observer,
            privacy: q.page.privacy,
        };
        try {
            await write(JSON.stringify({ context, row }, null, 2));
            this.queryPatch({
                notice: "Selected read-only record copied by your explicit action.",
            });
        } catch {
            this.queryPatch({ error: "CopyFailed" });
        }
    }
    showModel() {
        this.patch({ modelShown: !this.state.modelShown });
        if (this.state.modelShown) void this.refreshModel();
    }
    setPlayMode(playMode: State["playMode"]) {
        if (this.state.pending) return;
        if (playMode === "local" && !this.state.model?.loaded) {
            this.fail("ModelUnavailable");
            return;
        }
        this.patch({ playMode, visibleError: null });
    }
    setInputKind(inputKind: State["inputKind"]) {
        if (!this.state.pending) this.patch({ inputKind });
    }
    async refreshModel() {
        const sequence = ++this.modelReadSequence;
        try {
            const model = (await this.native("model_status")) as ModelState;
            if (
                !model ||
                typeof model.loaded !== "boolean" ||
                typeof model.phase !== "string"
            )
                throw new Error("Wire");
            if (!this.state.disposed && sequence === this.modelReadSequence) {
                const op = this.modelOperation;
                if (
                    op &&
                    op.id === null &&
                    Number.isSafeInteger(model.operation_id) &&
                    model.operation_id > op.baseline &&
                    ["choosing", "checking", "copying", "loading"].includes(
                        model.phase,
                    )
                ) {
                    op.id = model.operation_id;
                    this.patch({ modelCancelReady: true });
                }
                this.patch({ model });
            }
        } catch (error) {
            if (!this.state.disposed) this.fail(error);
        }
    }
    async modelAction(command: "model_import" | "model_load" | "model_unload") {
        if (this.state.modelBusy || this.state.disposed) return;
        const operation = {
            baseline: this.state.model?.operation_id ?? 0,
            id: null as number | null,
        };
        this.modelOperation = operation;
        this.patch({
            modelBusy: true,
            modelCancelReady: false,
            visibleError: null,
        });
        let polling = false;
        const timer = setInterval(() => {
            if (polling) return;
            polling = true;
            void this.refreshModel().finally(() => {
                polling = false;
            });
        }, 150);
        try {
            await this.native(command);
            // A periodic status read must not supersede the definitive post-action
            // refresh and let the action resolve with the previous loaded state.
            clearInterval(timer);
            await this.refreshModel();
        } catch (error) {
            clearInterval(timer);
            if (!this.state.disposed) {
                this.fail(error);
                await this.refreshModel();
            }
        } finally {
            clearInterval(timer);
            if (this.modelOperation === operation) {
                this.modelOperation = null;
                if (!this.state.disposed)
                    this.patch({ modelBusy: false, modelCancelReady: false });
            }
        }
    }
    async cancelModel() {
        const operation = this.modelOperation;
        const operationId = operation?.id;
        if (!operationId) {
            this.fail("ModelOperationUnknown");
            return;
        }
        try {
            await this.native("model_cancel", { operationId });
        } catch (error) {
            if (this.modelOperation === operation) this.fail(error);
        }
    }
    requestLab() {
        this.patch({ labPending: true });
    }
    acknowledgeLab(confirmed: boolean) {
        this.patch({ labPending: false });
        if (confirmed) this.setView("lab");
    }
    setView(view: State["view"]) {
        this.clearTrace();
        this.clearQuery(true);
        if (
            view === "play" &&
            ["full", "database"].includes(this.state.exports.mode)
        ) {
            this.clearExportPreview();
            this.exportPatch({ mode: "diagnostics" });
        }
        this.patch({
            view,
            observer: view === "play" ? "player" : "omniscient",
            visibleError: null,
        });
        void this.inspect();
        if (this.state.query.shown) void this.queryInspection();
        if (this.state.trace.shown) void this.readTrace();
    }
    setObserver(observer: string) {
        if (this.state.view !== "lab") return;
        this.clearTrace();
        this.clearQuery(true);
        this.patch({ observer });
        void this.inspect();
        if (this.state.query.shown) void this.queryInspection();
        if (this.state.trace.shown) void this.readTrace();
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
        ) {
            this.patch({ receiptTurn, inspectorOpen: true });
            if (this.state.query.shown)
                void this.browseInspection({
                    view: "turn_diff",
                    atRevision: this.receipt()?.events.at(-1)?.sequence ?? null,
                    search: "",
                });
        }
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
        if (this.state.playMode === "local" && !this.state.model?.loaded) {
            this.fail("ModelUnavailable");
            return Promise.resolve();
        }
        if (
            (this.state.playMode === "local" ||
                this.state.action === "dialogue") &&
            !this.state.draft.trim()
        ) {
            this.fail("DraftRequired");
            return Promise.resolve();
        }
        const op: Operation = {
            session,
            epoch: this.epoch,
            request:
                this.state.playMode === "local"
                    ? {
                          version: 1,
                          scope: session.scope,
                          turn: `${this.prefix}-${++this.nextTurn}`,
                          expected_revision: play.revision,
                          intent: {
                              kind: "free_text",
                              value: {
                                  kind: this.state.inputKind,
                                  text: this.state.draft,
                              },
                          },
                      }
                    : request(
                          session.scope,
                          `${this.prefix}-${++this.nextTurn}`,
                          play.revision,
                          this.state.action,
                          this.state.draft,
                      ),
            mode:
                this.state.playMode === "local"
                    ? "accepted"
                    : this.state.fakeMode,
            submitted: false,
            cancelled: false,
            promise: Promise.resolve(),
        };
        const mode = op.mode;
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
            let status = (await this.gateway.call(
                op.request.intent.kind === "free_text"
                    ? {
                          op: "free_text",
                          session: op.session.id,
                          request: op.request,
                      }
                    : {
                          op: "submit",
                          session: op.session.id,
                          request: op.request,
                          mode,
                      },
            )) as TurnStatus;
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
                (op.request.intent.kind === "dialogue" ||
                    op.request.intent.kind === "free_text") &&
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
        if (op.request.intent.kind === "free_text") await this.refreshModel();
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
        const recovering = this.state.pending?.stage === "recovering";
        op.cancelled = true;
        this.patch({
            pending: this.state.pending
                ? { ...this.state.pending, stage: "cancelling" }
                : null,
        });
        // Admission is still in flight. run() observes this flag after the
        // acknowledgement and cancels the original key before preparing it.
        if (!op.submitted && !recovering) return;
        try {
            if (!op.submitted) {
                // A lost submit acknowledgement may already be admitted. A
                // separate lookup can resolve Cancel while an older recovery
                // lookup is delayed or lost; it must prove the original key.
                const known = await this.control(op, "turn_status");
                if (
                    !known?.scope ||
                    known.turn !== op.request.turn ||
                    !sameScope(known.scope, op.session.scope) ||
                    known.expected_revision !== op.request.expected_revision ||
                    ![
                        "queued",
                        "running",
                        "ready",
                        "committed",
                        "cancelled",
                        "failed",
                        "stale",
                    ].includes(known.phase)
                )
                    throw new Error("Wire");
                op.submitted = true;
            }
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
                status = (await this.gateway.call(
                    op.request.intent.kind === "free_text"
                        ? {
                              op: "free_text",
                              session: op.session.id,
                              request: op.request,
                          }
                        : {
                              op: "submit",
                              session: op.session.id,
                              request: op.request,
                              mode: op.mode,
                          },
                )) as TurnStatus;
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
            session = this.selected(),
            play = s.play ?? s.playV2;
        return {
            version: s.playV2 ? 2 : 1,
            query: s.query,
            trace: s.trace,
            model: s.model,
            playMode: s.playMode,
            inputKind: s.inputKind,
            exports: s.exports,
            workspace: s.workspace,
            ephemeral: s.ephemeral,
            synthetic: true,
            uiRevision: play?.revision ?? 0,
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
            rules: play?.rules ?? null,
            player: play?.player ?? null,
            inventory: play?.inventory ?? null,
            transcript: s.playV2
                ? {
                      source: "query2",
                      status: "owned_by_scoped_controller",
                  }
                : {
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
            playV2: null,
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
