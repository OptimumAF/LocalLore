// One presentation client for Rust's selected evaluator. No generation/storage
// authority. Lifecycle and read-lens epochs deliberately have separate ownership.
import {
    checkedSelectedCatalog,
    checkedSelectedCleanup,
    checkedSelectedDiagnostics,
    checkedSelectedEvidence,
    checkedSelectedObserver,
    checkedSelectedRequest,
    checkedSelectedRow,
    checkedSelectedSource,
    checkedSelectedStatus,
    checkedSelectedSummary,
    selectedArm,
    selectedErrors,
    selectedLane,
    selectedUuid,
} from "./selected-evaluation-model";
import { sameReaderObserver } from "./comparison-reader-model";
import type {
    EvidenceRequest,
    ObserverV2,
    RowId,
    SelectedArm,
    SelectedCatalog,
    SelectedCleanup,
    SelectedDiagnostics,
    SelectedError,
    SelectedEvidence,
    SelectedLane,
    SelectedSourceIdentity,
    SelectedStatus,
    SelectedSummary,
} from "./selected-evaluation-model";
export type SelectedEvaluationInvoke = (
    name: string,
    args: Record<string, unknown>,
) => Promise<unknown>;
export type SelectedPending = {
    action:
        | "prepare"
        | "start"
        | "status"
        | "cancel"
        | "open"
        | "resume"
        | "close"
        | "summary"
        | "evidence"
        | "diagnostics"
        | "catalog"
        | "cleanup_status"
        | "retry_cleanup";
    clientId: string | null;
    operationId: number | null;
};
export type SelectedEvaluationState = {
    context: string;
    allowed: boolean;
    observer: ObserverV2;
    clientId: string | null;
    status: SelectedStatus | null;
    catalog: SelectedCatalog | null;
    summary: SelectedSummary | null;
    evidence: SelectedEvidence | null;
    diagnostics: SelectedDiagnostics | null;
    cleanup: SelectedCleanup | null;
    pending: SelectedPending | null;
    busy: boolean;
    uncertain: boolean;
    error: SelectedError | null;
};
type Ticket = { context: number; serial: number; client: string };
type ReadTicket = {
    context: number;
    lens: number;
    request: number;
    client: string;
    token: string;
    binding: string;
};
type ExpectedIdentity = {
    turn?: string;
    arm?: SelectedArm;
    lane?: SelectedLane;
    planToken?: string;
    runId?: string;
};
const POLL_MS = 300,
    MAX_STATUS_POLLS = 1000;
function frozen<T>(value: T): T {
    if (
        value !== null &&
        typeof value === "object" &&
        !Object.isFrozen(value)
    ) {
        Object.values(value).forEach((item) => {
            frozen(item);
        });
        Object.freeze(value);
    }
    return value;
}
function category(error: unknown): SelectedError {
    const s =
        error instanceof Error
            ? error.message
            : typeof error === "string"
              ? error
              : "";
    return s === "SelectedEvaluationWire"
        ? s
        : (selectedErrors.find((v) => v === s) ?? "EvaluationIo");
}
function unknown(error: SelectedError): boolean {
    return (
        error === "EvaluationIo" ||
        error === "EvaluationInternal" ||
        error === "SelectedEvaluationWire"
    );
}
export class SelectedEvaluationController {
    private state: SelectedEvaluationState = frozen<SelectedEvaluationState>({
        context: "",
        allowed: false,
        observer: { kind: "omniscient" },
        clientId: null,
        status: null,
        catalog: null,
        summary: null,
        evidence: null,
        diagnostics: null,
        cleanup: null,
        pending: null,
        busy: false,
        uncertain: false,
        error: null,
    });
    private listeners = new Set<() => void>();
    private contextEpoch = 0;
    private lifecycleEpoch = 0;
    private lensEpoch = 0;
    private readEpoch = 0;
    private auxiliaryEpoch = 0;
    private lifecycleBusy = false;
    private readBusy = false;
    private auxiliaryBusy = false;
    private currentUncertain = false;
    private disposed = false;
    private reporting = false;
    private sent = new Set<string>();
    private inFlight = new Map<string, number>();
    private replies = new Map<string, number>();
    private expected = new Map<string, ExpectedIdentity>();
    private retired = new Set<string>();
    private releasing = new Map<string, Promise<void>>();
    constructor(
        private invoke: SelectedEvaluationInvoke,
        private onNativeError?: (error: SelectedError) => void,
    ) {}
    get(): Readonly<SelectedEvaluationState> {
        return this.state;
    }
    subscribe(listener: () => void): () => void {
        if (!this.disposed) this.listeners.add(listener);
        return () => {
            this.listeners.delete(listener);
        };
    }
    private notifyError(error: SelectedError): void {
        if (this.reporting) return;
        this.reporting = true;
        try {
            this.onNativeError?.(error);
        } catch {
            /* presentation callback has no authority */
        } finally {
            this.reporting = false;
        }
    }
    private patch(update: Partial<SelectedEvaluationState>): void {
        if (update.uncertain !== undefined)
            this.currentUncertain = update.uncertain;
        const next = {
            ...this.state,
            ...update,
            uncertain: this.currentUncertain || this.retired.size > 0,
            busy:
                this.lifecycleBusy ||
                this.readBusy ||
                this.auxiliaryBusy ||
                (update.status !== undefined
                    ? update.status?.running === true
                    : this.state.status?.running === true),
        };
        if (
            Object.entries(next).every(
                ([key, value]) =>
                    value === this.state[key as keyof SelectedEvaluationState],
            )
        )
            return;
        this.state = frozen(next);
        for (const listener of [...this.listeners]) {
            if (this.disposed) break;
            try {
                listener();
            } catch {
                this.notifyError("EvaluationInternal");
            }
        }
    }
    private call(
        action: string,
        body: Record<string, unknown>,
    ): Promise<unknown> {
        const request = JSON.stringify(body);
        if (new TextEncoder().encode(request).length > 4096)
            return Promise.reject(new Error("SelectedEvaluationWire"));
        return this.invoke("evaluation_selected", { action, request });
    }
    private privateBody(): Partial<SelectedEvaluationState> {
        return { summary: null, evidence: null, diagnostics: null };
    }
    private owns(t: Ticket): boolean {
        return this.ownsClient(t) && this.lifecycleEpoch === t.serial;
    }
    private ownsClient(t: Ticket): boolean {
        return (
            !this.disposed &&
            this.state.allowed &&
            this.contextEpoch === t.context &&
            this.state.clientId === t.client
        );
    }
    private ownsRead(t: ReadTicket): boolean {
        return (
            !this.disposed &&
            this.state.allowed &&
            this.contextEpoch === t.context &&
            this.lensEpoch === t.lens &&
            this.readEpoch === t.request &&
            this.state.clientId === t.client &&
            this.state.status?.run_token === t.token &&
            this.state.status.binding === t.binding
        );
    }
    private failed(error: unknown, t?: Ticket): void {
        if (t && !this.owns(t)) return;
        const e = category(error);
        const loss =
            e === "UnknownEvaluationRun" || e === "Forbidden" || e === "Closed";
        const status =
            loss && this.state.status
                ? {
                      ...this.state.status,
                      plan_token: null,
                      run_id: null,
                      run_token: null,
                      binding: null,
                      prepared: null,
                  }
                : this.state.status;
        this.patch({
            ...this.privateBody(),
            status,
            error: e,
            uncertain: unknown(e) || (loss && status?.running === true),
        });
        this.notifyError(e);
    }
    private async release(client: string): Promise<void> {
        if (!this.retired.has(client)) return;
        const existing = this.releasing.get(client);
        if (existing) return existing;
        const reply = this.replies.get(client) ?? 0;
        const work = (async () => {
            try {
                const value = checkedSelectedStatus(
                    await this.call("close", { clientId: client }),
                    client,
                );
                if (
                    value.phase === "closed" &&
                    !value.running &&
                    !value.cleanup_required &&
                    !this.inFlight.get(client) &&
                    (this.replies.get(client) ?? 0) === reply
                ) {
                    this.retired.delete(client);
                    this.sent.delete(client);
                    this.replies.delete(client);
                    this.expected.delete(client);
                    if (!this.disposed) this.patch({});
                }
            } catch (error) {
                // Unknown means this exact client has no native presentation owner;
                // cleanup_status remains a separate native worker-retention check.
                if (
                    category(error) === "UnknownEvaluationRun" &&
                    !this.inFlight.get(client) &&
                    (this.replies.get(client) ?? 0) === reply
                ) {
                    this.retired.delete(client);
                    this.sent.delete(client);
                    this.replies.delete(client);
                    this.expected.delete(client);
                    if (!this.disposed) this.patch({});
                }
            }
        })();
        this.releasing.set(client, work);
        try {
            await work;
        } finally {
            this.releasing.delete(client);
        }
    }
    private retire(client: string | null): void {
        if (client && this.sent.has(client)) {
            this.retired.add(client);
            void this.release(client);
        }
    }
    private async clientCall(
        t: Ticket,
        action: string,
        body: Record<string, unknown>,
    ): Promise<SelectedStatus> {
        this.inFlight.set(t.client, (this.inFlight.get(t.client) ?? 0) + 1);
        try {
            const value = checkedSelectedStatus(
                    await this.call(action, body),
                    t.client,
                ),
                expected = this.expected.get(t.client);
            if (expected) {
                if (
                    (expected.lane &&
                        value.lane !== null &&
                        value.lane !== expected.lane) ||
                    (expected.runId &&
                        value.run_id !== null &&
                        value.run_id !== expected.runId) ||
                    (expected.planToken &&
                        value.plan_token !== null &&
                        value.plan_token !== expected.planToken)
                )
                    throw new Error("SelectedEvaluationWire");
                if (
                    value.prepared &&
                    ((expected.turn &&
                        value.prepared.selection.turn !== expected.turn) ||
                        (expected.arm &&
                            value.prepared.selection.clicked_arm !==
                                expected.arm) ||
                        (expected.lane &&
                            value.prepared.lane !==
                                (expected.lane === "approved_native"
                                    ? "native_selected_case"
                                    : "scripted_selected_case")))
                )
                    throw new Error("SelectedEvaluationWire");
                if (!expected.runId && value.run_id !== null)
                    expected.runId = value.run_id;
                if (!expected.planToken && value.plan_token !== null)
                    expected.planToken = value.plan_token;
            }
            return value;
        } finally {
            const count = (this.inFlight.get(t.client) ?? 1) - 1;
            if (count) this.inFlight.set(t.client, count);
            else this.inFlight.delete(t.client);
            this.replies.set(t.client, (this.replies.get(t.client) ?? 0) + 1);
        }
    }
    private async lateReply(t: Ticket, value?: SelectedStatus): Promise<void> {
        if (this.ownsClient(t)) {
            // Cancellation can supersede a poll without retiring its client.
            // The actual completed reply still wins over that late cancellation.
            if (
                value?.phase === "completed" &&
                this.state.status?.phase !== "closed" &&
                this.state.status?.operation_id === value.operation_id
            ) {
                this.applyStatus(value, { ...t, serial: this.lifecycleEpoch });
            }
            return;
        }
        this.sent.add(t.client);
        this.retired.add(t.client);
        // An earlier close may have preceded the late admission/reply. One exact
        // post-reply close is required; never close a replacement client's owner.
        await this.release(t.client);
        if (this.retired.has(t.client) && !this.inFlight.get(t.client))
            await this.release(t.client);
    }
    private async flushRetired(): Promise<boolean> {
        for (const client of [...this.retired]) await this.release(client);
        return this.retired.size === 0;
    }
    // Root supplies only execution/source/session/window identity here. Observer
    // and inspector controls belong to setObserver/read requests, never this key.
    // `allowed` is a presentation guard; native eligibility is still mandatory.
    setContext(context: string, allowed: boolean): void {
        if (
            this.disposed ||
            (context === this.state.context && allowed === this.state.allowed)
        )
            return;
        const old = this.state.clientId;
        ++this.contextEpoch;
        ++this.lifecycleEpoch;
        ++this.lensEpoch;
        ++this.readEpoch;
        ++this.auxiliaryEpoch;
        this.lifecycleBusy = false;
        this.readBusy = false;
        this.auxiliaryBusy = false;
        // Preserve captured owner before synchronous subscribers can admit anything.
        if (old && this.sent.has(old)) this.retired.add(old);
        this.patch({
            context,
            allowed,
            clientId: null,
            status: null,
            catalog: null,
            ...this.privateBody(),
            pending: null,
            uncertain: false,
            error: null,
        });
        this.retire(old);
    }
    setObserver(value: ObserverV2): void {
        if (this.disposed) return;
        let observer: ObserverV2;
        try {
            observer = checkedSelectedObserver(value);
        } catch (error) {
            this.failed(error);
            return;
        }
        if (sameReaderObserver(observer, this.state.observer)) return;
        const reading = this.readBusy;
        ++this.lensEpoch;
        ++this.readEpoch;
        this.readBusy = false;
        // Safe scope/head identity survives. No close/cancel or execution epoch change.
        this.patch({
            observer,
            evidence: null,
            diagnostics: null,
            ...(reading ? { pending: null } : {}),
            error: null,
        });
    }
    private canAdmit(): boolean {
        if (this.disposed || !this.state.allowed) return false;
        if (
            this.state.clientId ||
            this.state.busy ||
            this.currentUncertain ||
            this.state.cleanup?.cleanup_required ||
            this.state.cleanup?.running
        ) {
            this.patch({ error: "EvaluationBusy" });
            return false;
        }
        return true;
    }
    private async newClient(
        action: "prepare" | "open",
        body: Record<string, unknown>,
    ): Promise<void> {
        if (!this.canAdmit()) return;
        const epoch = this.contextEpoch;
        if (!(await this.flushRetired())) {
            if (!this.disposed && epoch === this.contextEpoch)
                this.patch({ error: "EvaluationBusy" });
            return;
        }
        if (this.disposed || epoch !== this.contextEpoch || !this.canAdmit())
            return;
        const client = crypto.randomUUID();
        this.expected.set(
            client,
            action === "prepare"
                ? {
                      turn: checkedSelectedRow({
                          turn: body.turnId,
                          arm: body.arm,
                      }).turn,
                      arm: selectedArm(body.arm),
                      lane: selectedLane(body.lane),
                  }
                : { runId: selectedUuid(body.runId) },
        );
        this.lifecycleBusy = true;
        const t = {
            context: this.contextEpoch,
            serial: ++this.lifecycleEpoch,
            client,
        };
        ++this.readEpoch;
        this.patch({
            clientId: client,
            status: null,
            ...this.privateBody(),
            pending: { action, clientId: client, operationId: null },
            uncertain: false,
            error: null,
        });
        if (!this.owns(t)) {
            this.expected.delete(client);
            return;
        }
        this.sent.add(client);
        await this.operation(t, action, { clientId: client, ...body });
    }
    async prepare(
        source: SelectedSourceIdentity,
        row: RowId,
        lane: SelectedLane,
    ): Promise<void> {
        try {
            const s = checkedSelectedSource(source),
                r = checkedSelectedRow(row),
                l = selectedLane(lane);
            await this.newClient("prepare", {
                readerClientId: s.readerClientId,
                runToken: s.runToken,
                binding: s.binding,
                turnId: r.turn,
                arm: r.arm,
                lane: l,
            });
        } catch (error) {
            if (!this.disposed) this.failed(error);
        }
    }
    async open(runId: string): Promise<void> {
        try {
            const id = selectedUuid(runId);
            if (
                this.state.clientId &&
                this.state.status?.run_id === id &&
                !this.state.status.running &&
                !this.state.uncertain
            ) {
                await this.existing("open", { runId: id });
            } else await this.newClient("open", { runId: id });
        } catch (error) {
            if (!this.disposed) this.failed(error);
        }
    }
    private applyStatus(
        next: SelectedStatus,
        t: Ticket,
        action = "status",
    ): void {
        if (!this.owns(t)) return;
        const old = this.state.status;
        if (old && old.operation_id === next.operation_id) {
            for (const key of [
                "run_id",
                "run_token",
                "binding",
                "plan_token",
            ] as const) {
                if (
                    (action === "open" || action === "resume") &&
                    (key === "run_token" || key === "binding")
                )
                    continue;
                if (
                    old[key] !== null &&
                    next[key] !== null &&
                    old[key] !== next[key]
                )
                    throw new Error("SelectedEvaluationWire");
            }
        }
        // A real completed attempt remains completed if an older cancel/status
        // reply arrives later; cleanup uncertainty is still visible and retained.
        if (
            old?.phase === "completed" &&
            next.phase !== "closed" &&
            old.operation_id === next.operation_id &&
            (action === "cancel" || action === "status")
        ) {
            next = {
                ...old,
                cleanup_required: old.cleanup_required || next.cleanup_required,
                running: next.cleanup_required ? next.running : old.running,
                error: next.cleanup_required ? next.error : old.error,
                cause: next.cleanup_required ? next.cause : old.cause,
            };
        }
        const cleared =
            next.phase === "closed" ||
            next.error === "Forbidden" ||
            next.error === "Closed" ||
            next.error === "UnknownEvaluationRun";
        const released =
            next.phase === "closed" && !next.running && !next.cleanup_required;
        if (released) {
            if (this.inFlight.get(t.client)) this.retired.add(t.client);
            else {
                this.sent.delete(t.client);
                this.expected.delete(t.client);
                this.replies.delete(t.client);
            }
        }
        this.patch({
            status: next,
            ...(cleared ? this.privateBody() : {}),
            clientId: released ? null : t.client,
            pending: next.running
                ? {
                      action: "status",
                      clientId: t.client,
                      operationId: next.operation_id,
                  }
                : null,
            uncertain: false,
            error: next.error,
            ...(next.cleanup_required
                ? {
                      cleanup: {
                          version: 1,
                          kind: "selected_cleanup",
                          cleanup_required: true,
                          running: next.running,
                          error: next.error,
                      } as SelectedCleanup,
                  }
                : {}),
        });
    }
    private async operation(
        t: Ticket,
        action: string,
        body: Record<string, unknown>,
    ): Promise<void> {
        try {
            if (!this.owns(t)) return;
            const response = await this.clientCall(t, action, body);
            if (!this.owns(t)) {
                await this.lateReply(t, response);
                return;
            }
            this.applyStatus(response, t, action);
            for (
                let count = 0;
                count < MAX_STATUS_POLLS &&
                this.owns(t) &&
                this.state.status?.running;
                count++
            ) {
                await new Promise<void>((resolve) =>
                    setTimeout(resolve, POLL_MS),
                );
                if (!this.owns(t)) return;
                const status = await this.clientCall(t, "status", {
                    clientId: t.client,
                });
                if (!this.owns(t)) {
                    await this.lateReply(t, status);
                    return;
                }
                this.applyStatus(status, t, action);
            }
            if (this.owns(t) && this.state.status?.running)
                this.patch({ uncertain: true, error: "EvaluationIo" });
        } catch (error) {
            if (this.owns(t)) this.failed(error, t);
            else await this.lateReply(t);
        } finally {
            if (
                !this.disposed &&
                this.contextEpoch === t.context &&
                this.lifecycleEpoch === t.serial
            ) {
                this.lifecycleBusy = false;
                this.patch({
                    pending: this.state.status?.running
                        ? {
                              action: "status",
                              clientId: t.client,
                              operationId: this.state.status.operation_id,
                          }
                        : null,
                });
            }
        }
    }
    private async existing(
        action: "start" | "status" | "cancel" | "open" | "resume" | "close",
        body: Record<string, unknown>,
        interrupt = false,
    ): Promise<void> {
        const client = this.state.clientId;
        if (
            this.disposed ||
            !this.state.allowed ||
            !client ||
            (!interrupt && (this.lifecycleBusy || this.readBusy))
        )
            return;
        if (action === "open" || action === "resume") {
            // These explicit native confirmations may return a newly prepared
            // token. It is not a replay of the old consumed start grant.
            const expected = this.expected.get(client);
            if (expected) delete expected.planToken;
        }
        ++this.readEpoch;
        this.readBusy = false;
        this.lifecycleBusy = true;
        const t = {
            context: this.contextEpoch,
            serial: ++this.lifecycleEpoch,
            client,
        };
        this.patch({
            evidence: null,
            diagnostics: null,
            pending: {
                action,
                clientId: client,
                operationId:
                    action === "cancel" || action === "status"
                        ? (this.state.status?.operation_id ?? null)
                        : null,
            },
            error: null,
        });
        if (!this.owns(t)) return;
        await this.operation(t, action, { clientId: client, ...body });
    }
    async start(): Promise<void> {
        if (this.state.status?.phase === "completed") return;
        if (
            this.state.uncertain ||
            this.state.cleanup?.cleanup_required ||
            this.state.cleanup?.running
        )
            return;
        const token = this.state.status?.plan_token;
        if (!token || this.state.status?.phase !== "prepared") return;
        await this.existing("start", { planToken: token });
    }
    async status(): Promise<void> {
        await this.existing("status", {});
    }
    async cancel(): Promise<void> {
        const s = this.state.status;
        if (
            !s ||
            s.operation_id === null ||
            s.phase === "completed" ||
            s.phase === "closed" ||
            this.state.uncertain
        )
            return;
        if (this.lifecycleBusy && s.phase === "prepared") return; // start ACK has not identified its operation
        await this.existing("cancel", { operationId: s.operation_id }, true);
    }
    async resume(source: SelectedSourceIdentity): Promise<void> {
        if (
            this.state.uncertain ||
            this.state.cleanup?.cleanup_required ||
            this.state.cleanup?.running
        )
            return;
        try {
            const s = checkedSelectedSource(source),
                token = this.state.status?.run_token;
            if (!token) return;
            await this.existing("resume", {
                runToken: token,
                readerClientId: s.readerClientId,
                sourceToken: s.runToken,
                sourceBinding: s.binding,
            });
        } catch (error) {
            if (!this.disposed) this.failed(error);
        }
    }
    async close(): Promise<void> {
        await this.existing("close", {}, true);
    }
    private async auxiliary(
        action: "catalog" | "cleanup_status" | "retry_cleanup",
    ): Promise<void> {
        if (
            this.disposed ||
            (action === "catalog" && !this.state.allowed) ||
            this.auxiliaryBusy ||
            this.lifecycleBusy ||
            this.readBusy
        )
            return;
        const epoch = this.contextEpoch,
            serial = ++this.auxiliaryEpoch;
        this.auxiliaryBusy = true;
        this.patch({
            pending: { action, clientId: null, operationId: null },
            error: null,
        });
        const live = () =>
            !this.disposed &&
            (action !== "catalog" || this.state.allowed) &&
            this.contextEpoch === epoch &&
            this.auxiliaryEpoch === serial;
        try {
            if (!live()) return;
            const response = await this.call(action, {});
            if (!live()) return;
            if (action === "catalog")
                this.patch({ catalog: checkedSelectedCatalog(response) });
            else {
                const cleanup = checkedSelectedCleanup(response);
                this.patch({ cleanup, error: cleanup.error });
            }
        } catch (error) {
            if (live()) this.failed(error);
        } finally {
            if (live()) {
                this.auxiliaryBusy = false;
                this.patch({ pending: null });
            }
        }
    }
    async catalog(): Promise<void> {
        await this.auxiliary("catalog");
    }
    async cleanupStatus(): Promise<void> {
        await this.auxiliary("cleanup_status");
    }
    async retryCleanup(): Promise<void> {
        await this.auxiliary("retry_cleanup");
    }
    private beginRead(
        action: "summary" | "evidence" | "diagnostics",
    ): ReadTicket | null {
        const s = this.state.status,
            client = this.state.clientId;
        if (
            this.disposed ||
            !this.state.allowed ||
            !client ||
            !s?.run_token ||
            !s.binding ||
            this.lifecycleBusy ||
            this.readBusy ||
            s.running ||
            this.state.uncertain
        )
            return null;
        const t = {
            context: this.contextEpoch,
            lens: this.lensEpoch,
            request: ++this.readEpoch,
            client,
            token: s.run_token,
            binding: s.binding,
        };
        this.readBusy = true;
        this.patch({
            ...(action === "summary" ? { summary: null } : {}),
            evidence: null,
            diagnostics: null,
            pending: { action, clientId: client, operationId: null },
            error: null,
        });
        return this.ownsRead(t) ? t : null;
    }
    private async read(
        action: "summary" | "evidence" | "diagnostics",
        request?: EvidenceRequest,
        arm?: SelectedArm,
    ): Promise<void> {
        const summary = this.state.summary;
        if (action !== "summary" && !summary) return;
        const t = this.beginRead(action);
        if (!t) return;
        try {
            if (!this.ownsRead(t)) return;
            const body = {
                clientId: t.client,
                runToken: t.token,
                binding: t.binding,
                ...(action === "evidence"
                    ? { arm, request }
                    : action === "diagnostics"
                      ? { observer: this.state.observer }
                      : {}),
            };
            const response = await this.call(action, body);
            if (!this.ownsRead(t)) return;
            if (action === "summary")
                this.patch({
                    summary: checkedSelectedSummary(
                        response,
                        t.token,
                        t.binding,
                    ),
                });
            else if (action === "evidence" && summary && request && arm)
                this.patch({
                    evidence: checkedSelectedEvidence(
                        response,
                        t.token,
                        summary,
                        arm,
                        request,
                    ),
                });
            else if (action === "diagnostics" && summary)
                this.patch({
                    diagnostics: checkedSelectedDiagnostics(
                        response,
                        t.token,
                        summary,
                    ),
                });
        } catch (error) {
            if (this.ownsRead(t)) this.failed(error);
        } finally {
            if (
                !this.disposed &&
                this.contextEpoch === t.context &&
                this.lensEpoch === t.lens &&
                this.readEpoch === t.request
            ) {
                this.readBusy = false;
                this.patch({ pending: null });
            }
        }
    }
    async loadSummary(): Promise<void> {
        await this.read("summary");
    }
    async readEvidence(
        arm: SelectedArm,
        value: EvidenceRequest,
    ): Promise<void> {
        try {
            const request = checkedSelectedRequest(value),
                selected = selectedArm(arm);
            if (
                !sameReaderObserver(request.observer, this.state.observer) ||
                (request.kind !== "query" &&
                    request.observer.kind !== "omniscient")
            )
                return;
            await this.read("evidence", request, selected);
        } catch (error) {
            if (!this.disposed) this.failed(error);
        }
    }
    async readDiagnostics(): Promise<void> {
        if (this.state.observer.kind !== "omniscient") return;
        await this.read("diagnostics");
    }
    dispose(): void {
        if (this.disposed) return;
        const old = this.state.clientId;
        this.disposed = true;
        ++this.contextEpoch;
        ++this.lifecycleEpoch;
        ++this.lensEpoch;
        ++this.readEpoch;
        ++this.auxiliaryEpoch;
        this.state = frozen({
            ...this.state,
            allowed: false,
            clientId: null,
            status: null,
            ...this.privateBody(),
            pending: null,
            busy: false,
        });
        this.listeners.clear();
        this.retire(old);
    }
}
