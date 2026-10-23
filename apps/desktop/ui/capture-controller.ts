import { category, sameScope } from "./model";
import type { Gateway, Session } from "./model";
import type { TraceAttempt } from "./trace-model";
import { checkedCapture, checkedCapturePreview, object } from "./capture-model";
import type {
    CaptureReply,
    CaptureQuery,
    CapturePreview,
} from "./capture-model";
export class CaptureController {
    private state = {
        permitted: false,
        consentEpoch: 0,
        enabled: null as boolean | null,
        busy: false,
        controlBusy: false,
        reply: null as CaptureReply | null,
        preview: null as CapturePreview | null,
        saved: null as string | null,
        error: null as string | null,
        cleanup: "",
    };
    private session: Session | null = null;
    private head = 0;
    private attempt: TraceAttempt | null = null;
    private context = "";
    private selection = "";
    private epoch = 0;
    private readEpoch = 0;
    private disposed = false;
    private controls: Promise<unknown> = Promise.resolve();
    private pendingControls = 0;
    private listeners = new Set<() => void>();
    constructor(
        private gateway: Gateway,
        private refreshMetadata: () => Promise<void> = async () => {},
    ) {}
    get = () => this.state;
    subscribe = (listener: () => void) => {
        this.listeners.add(listener);
        return () => {
            this.listeners.delete(listener);
        };
    };
    private patch(value: Partial<typeof this.state>) {
        if (this.disposed) return;
        this.state = { ...this.state, ...value };
        this.listeners.forEach((l) => l());
    }
    private native(
        command: "capture_preview" | "capture_save" | "capture_revoke",
        args: Record<string, unknown>,
    ) {
        if (!this.gateway.native)
            return Promise.reject(new Error("Unsupported"));
        return this.gateway.native(command, args);
    }
    private clear() {
        this.readEpoch++;
        this.patch({
            reply: null,
            preview: null,
            saved: null,
            error: null,
            busy: false,
        });
    }
    private control<T>(action: () => Promise<T>): Promise<T> {
        this.pendingControls++;
        this.patch({ controlBusy: true });
        const work = this.controls.then(action);
        this.controls = work.catch(() => {});
        return work.finally(() => {
            this.pendingControls--;
            this.patch({ controlBusy: this.pendingControls !== 0 });
        });
    }
    private async revoke(session: Session | null) {
        await this.native("capture_revoke", {}).catch((error) =>
            this.patch({
                cleanup: `Window details cleared. Export revocation unavailable: ${category(error)}.`,
            }),
        );
        if (!session) return true;
        try {
            const v = await this.gateway.call({
                op: "trace_capture_revoke",
                session: session.id,
                scope: session.scope,
            });
            if (
                !object(v) ||
                v.version !== 1 ||
                v.revoked !== true ||
                !object(v.scope) ||
                v.scope.story !== session.scope.story ||
                v.scope.branch !== session.scope.branch
            )
                throw new Error("Wire");
            return true;
        } catch (error) {
            this.patch({
                cleanup: `Window details cleared. Native capture revocation unavailable: ${category(error)}. Capture may remain until access-time expiry or session close.`,
            });
            return false;
        }
    }
    contextChanged(
        session: Session | null,
        head: number,
        permitted: boolean,
        attempt: TraceAttempt | null,
    ) {
        const context = `${session?.id}|${session?.scope.story}|${session?.scope.branch}|${permitted}`;
        const selection = JSON.stringify([head, attempt?.identity]);
        if (context !== this.context) {
            const old = this.session;
            this.epoch++;
            this.context = context;
            this.clear();
            this.patch({
                permitted,
                enabled: null,
                consentEpoch: this.state.consentEpoch + 1,
            });
            if (old) void this.control(() => this.revoke(old));
        } else if (selection !== this.selection) {
            this.clear();
            void this.native("capture_revoke", {}).catch((error) =>
                this.patch({
                    cleanup: `Preview cleared. Native export revocation unavailable: ${category(error)}.`,
                }),
            );
        }
        this.session = session;
        this.head = head;
        this.attempt = attempt;
        this.selection = selection;
    }
    private query(): CaptureQuery | null {
        const s = this.session,
            a = this.attempt;
        if (
            !this.state.permitted ||
            !s ||
            !a ||
            this.disposed ||
            !sameScope(a.identity.scope, s.scope)
        )
            return null;
        return {
            op: "trace_capture_read",
            session: s.id,
            scope: s.scope,
            expected_head: this.head,
            base_revision: a.identity.base_revision,
            turn: a.identity.turn,
            attempt: a.identity.attempt,
        };
    }
    async configure(consent: boolean) {
        const session = this.session,
            epoch = this.epoch,
            head = this.head;
        if (
            !session ||
            !this.state.permitted ||
            this.state.busy ||
            this.state.controlBusy ||
            !consent
        )
            return;
        this.clear();
        await this.control(async () => {
            try {
                if (epoch !== this.epoch) return;
                const v = await this.gateway.call({
                    op: "trace_capture_configure",
                    session: session.id,
                    scope: session.scope,
                    expected_head: head,
                    enabled: true,
                    consent: true,
                });
                if (epoch !== this.epoch) {
                    await this.revoke(session);
                    return;
                }
                if (
                    !object(v) ||
                    v.version !== 1 ||
                    !object(v.scope) ||
                    v.scope.story !== session.scope.story ||
                    v.scope.branch !== session.scope.branch ||
                    v.head !== head ||
                    v.enabled !== true ||
                    v.capture !== "explicit_private_details" ||
                    v.retention_seconds !== 600
                )
                    throw new Error("Wire");
                this.patch({ enabled: true, cleanup: "" });
                await this.refreshMetadata();
            } catch (error) {
                if (epoch === this.epoch)
                    this.patch({ error: category(error), enabled: null });
            }
        });
    }
    async disable() {
        this.epoch++;
        this.clear();
        this.patch({ enabled: null });
        const epoch = this.epoch;
        const session = this.session;
        const revoked = await this.control(() => this.revoke(session));
        if (epoch === this.epoch)
            this.patch({ enabled: revoked ? false : null });
    }
    async read() {
        const q = this.query();
        if (!q || this.state.busy || this.state.controlBusy) return;
        this.clear();
        const sequence = this.readEpoch;
        const actor = this.attempt!.identity.observer;
        this.patch({ busy: true });
        try {
            const reply = checkedCapture(await this.gateway.call(q), q);
            if (
                reply.details.identity &&
                reply.details.identity.observer !== actor
            )
                throw new Error("Wire");
            if (sequence === this.readEpoch && this.state.permitted)
                this.patch({
                    reply,
                    enabled: ["disabled", "expired"].includes(
                        reply.details.status,
                    )
                        ? false
                        : true,
                });
        } catch (error) {
            if (sequence === this.readEpoch)
                this.patch({ error: category(error) });
        } finally {
            if (sequence === this.readEpoch) this.patch({ busy: false });
        }
    }
    async preview() {
        const q = this.query();
        if (!q || this.state.busy || this.state.controlBusy) return;
        this.clear();
        const sequence = this.readEpoch;
        const actor = this.attempt!.identity.observer;
        this.patch({ busy: true });
        let token: string | null = null;
        try {
            const raw = await this.native("capture_preview", {
                selection: {
                    session: q.session,
                    scope: q.scope,
                    expected_head: q.expected_head,
                    base_revision: q.base_revision,
                    turn: q.turn,
                    attempt: q.attempt,
                },
            });
            if (object(raw) && typeof raw.token === "string") token = raw.token;
            const preview = await checkedCapturePreview(raw, q);
            const reply = checkedCapture(JSON.parse(preview.text), q);
            if (
                reply.details.identity &&
                reply.details.identity.observer !== actor
            )
                throw new Error("Wire");
            if (sequence !== this.readEpoch || !this.state.permitted) {
                await this.native("capture_revoke", { token: preview.token });
                return;
            }
            this.patch({
                preview,
                reply,
            });
        } catch (error) {
            if (token)
                await this.native("capture_revoke", { token }).catch(() => {});
            if (sequence === this.readEpoch)
                this.patch({ error: category(error) });
        } finally {
            if (sequence === this.readEpoch) this.patch({ busy: false });
        }
    }
    async save(consent: boolean) {
        const preview = this.state.preview,
            sequence = this.readEpoch;
        if (!consent || !preview || !this.state.permitted || this.state.busy)
            return;
        this.patch({ busy: true, error: null });
        try {
            const v = await this.native("capture_save", {
                token: preview.token,
                consent: true,
            });
            if (sequence !== this.readEpoch || !this.state.permitted) return;
            if (
                !object(v) ||
                !["saved", "cancelled"].includes(v.status) ||
                (v.status === "saved" &&
                    (v.mode !== "private_trace" ||
                        typeof v.location !== "string" ||
                        v.location.length > 4096))
            )
                throw new Error("Wire");
            this.patch({ saved: v.status === "saved" ? v.location : null });
        } catch (error) {
            if (sequence === this.readEpoch)
                this.patch({ error: category(error) });
        } finally {
            if (sequence === this.readEpoch) this.patch({ busy: false });
        }
    }
    async dispose() {
        this.epoch++;
        this.clear();
        const session = this.session;
        this.session = null;
        this.disposed = true;
        await this.control(() => this.revoke(session));
        this.listeners.clear();
    }
}
