import {
    checkedComparisonRunCatalog,
    checkedComparisonRunStatus,
    comparisonRunBatch,
    comparisonRunErrors,
    comparisonRunKind,
    comparisonRunUuid,
} from "./comparison-run-model";
import type {
    ComparisonRunCatalog,
    ComparisonRunError,
    ComparisonRunKind,
    ComparisonRunStatus,
} from "./comparison-run-model";
export type ComparisonRunInvoke = (
    name: string,
    args: Record<string, unknown>,
) => Promise<unknown>;
type Action =
    | "catalog"
    | "start"
    | "lookup"
    | "open"
    | "status"
    | "resume"
    | "cancel"
    | "close";
export type ComparisonRunState = {
    context: string;
    allowed: boolean;
    clientId: string | null;
    status: ComparisonRunStatus | null;
    catalog: ComparisonRunCatalog | null;
    pending: {
        action: Action;
        clientId: string | null;
        runToken: string | null;
        operationId: number | null;
    } | null;
    busy: boolean;
    uncertain: boolean;
    error: ComparisonRunError | null;
};
type Owner = {
    client: string | null;
    runId: string | null;
    token: string | null;
    kind: ComparisonRunKind | null;
    initialBatch: number | null;
    operation: number | null;
    sent: boolean;
    inFlight: number;
    retired: boolean;
    releasing: Promise<void> | null;
};
type Ticket = { epoch: number; serial: number; owner: Owner };
const POLL_MS = 300,
    MAX_POLLS = 1000;
function frozen<T>(value: T): T {
    if (
        value !== null &&
        typeof value === "object" &&
        !Object.isFrozen(value)
    ) {
        Object.values(value).forEach(frozen);
        Object.freeze(value);
    }
    return value;
}
function category(error: unknown): ComparisonRunError {
    const value =
        error instanceof Error
            ? error.message
            : typeof error === "string"
              ? error
              : "";
    return value === "ComparisonRunWire"
        ? value
        : (comparisonRunErrors.find((code) => code === value) ??
              "EvaluationIo");
}
export class ComparisonRunController {
    private state: ComparisonRunState = frozen({
        context: "",
        allowed: false,
        clientId: null,
        status: null,
        catalog: null,
        pending: null,
        busy: false,
        uncertain: false,
        error: null,
    });
    private listeners = new Set<() => void>();
    private epoch = 0;
    private serial = 0;
    private active = false;
    private disposed = false;
    private currentUncertain = false;
    private reporting = false;
    private current: Owner | null = null;
    // Admission waits for every retired captured capability. This is a
    // presentation barrier, never a second worker/cleanup authority.
    private retired = new Set<Owner>();
    constructor(
        private invoke: ComparisonRunInvoke,
        private onError?: (error: ComparisonRunError) => void,
    ) {}
    get(): Readonly<ComparisonRunState> {
        return this.state;
    }
    subscribe(listener: () => void): () => void {
        if (!this.disposed) this.listeners.add(listener);
        return () => this.listeners.delete(listener);
    }
    private patch(update: Partial<ComparisonRunState>): void {
        const next = { ...this.state, ...update };
        next.busy = this.active || next.status?.running === true;
        next.uncertain = this.currentUncertain || this.retired.size > 0;
        if (
            Object.entries(next).every(
                ([key, value]) =>
                    value === this.state[key as keyof ComparisonRunState],
            )
        )
            return;
        this.state = frozen(next);
        for (const listener of [...this.listeners]) {
            if (this.disposed) break;
            try {
                listener();
            } catch {
                /* no authority */
            }
        }
    }
    private failed(error: unknown, uncertain = true): void {
        const code = category(error);
        if (
            uncertain &&
            [
                "EvaluationIo",
                "EvaluationInternal",
                "ComparisonRunWire",
            ].includes(code)
        )
            this.currentUncertain = true;
        const loss = ["Forbidden", "Closed", "UnknownEvaluationRun"].includes(
            code,
        );
        if (loss && this.current) {
            const owner = this.current;
            this.current = null;
            owner.retired = true;
            this.retired.add(owner);
            void this.release(owner);
        }
        this.patch({
            error: code,
            ...(loss
                ? { status: null, catalog: null, clientId: null, pending: null }
                : {}),
        });
        if (!this.reporting) {
            this.reporting = true;
            try {
                this.onError?.(code);
            } catch {
                /* no authority */
            } finally {
                this.reporting = false;
            }
        }
    }
    private call(
        action: Action,
        query: Record<string, unknown>,
    ): Promise<unknown> {
        const encoded = JSON.stringify(query);
        if (new TextEncoder().encode(encoded).length > 4096)
            return Promise.reject(Error("ComparisonRunWire"));
        return this.invoke("evaluation_comparison_run", { action, query });
    }
    private owner(client: string | null, runId: string | null = null): Owner {
        return {
            client,
            runId,
            token: null,
            kind: null,
            initialBatch: null,
            operation: null,
            sent: false,
            inFlight: 0,
            retired: false,
            releasing: null,
        };
    }
    private owns(ticket: Ticket): boolean {
        return (
            !this.disposed &&
            this.state.allowed &&
            this.epoch === ticket.epoch &&
            this.serial === ticket.serial &&
            this.current === ticket.owner &&
            !ticket.owner.retired
        );
    }
    private bind(
        owner: Owner,
        next: ComparisonRunStatus,
        rebind = false,
    ): void {
        if (
            (owner.client !== null && next.client_id !== owner.client) ||
            (owner.runId !== null && next.run_id !== owner.runId) ||
            (owner.kind !== null && next.comparison_kind !== owner.kind) ||
            (!rebind && owner.token !== null && next.run_token !== owner.token)
        )
            throw Error("ComparisonRunWire");
        owner.client = next.client_id;
        owner.runId = next.run_id;
        owner.kind = next.comparison_kind;
        owner.token = next.run_token;
        owner.operation = next.operation_id;
    }
    private async ownedCall(
        owner: Owner,
        action: Action,
        query: Record<string, unknown>,
    ): Promise<ComparisonRunStatus> {
        owner.sent = true;
        owner.inFlight++;
        try {
            const next = checkedComparisonRunStatus(
                await this.call(action, query),
            );
            if (
                (action === "status" || action === "cancel") &&
                owner.operation !== null &&
                next.operation_id !== owner.operation
            )
                throw Error("ComparisonRunWire");
            this.bind(owner, next, action === "lookup" || action === "open");
            return next;
        } finally {
            owner.inFlight--;
            if (owner.retired) void this.release(owner);
        }
    }
    private async release(owner: Owner): Promise<void> {
        if (!owner.retired || owner.inFlight) return;
        if (owner.releasing) return owner.releasing;
        const work = (async () => {
            try {
                if (!owner.sent) {
                    this.retired.delete(owner);
                    return;
                }
                if (!owner.token) {
                    // A lost cold-open ACK has a known run ID, not an invented
                    // client. Resolve only its actual bounded native metadata.
                    if (!owner.client && owner.runId) {
                        const catalog = checkedComparisonRunCatalog(
                            await this.call("catalog", {}),
                        );
                        const metadata = catalog.runs.find(
                            (run) => run.run_id === owner.runId,
                        );
                        if (!metadata) throw Error("UnknownEvaluationRun");
                        owner.client = metadata.client_id;
                        owner.kind = metadata.comparison_kind;
                    }
                    if (!owner.client) return;
                    this.bind(
                        owner,
                        checkedComparisonRunStatus(
                            await this.call("lookup", {
                                clientId: owner.client,
                            }),
                        ),
                        true,
                    );
                }
                const token = owner.token;
                if (!token || owner.inFlight) return;
                const next = checkedComparisonRunStatus(
                    await this.call("close", { runToken: token }),
                );
                if (
                    next.client_id !== owner.client ||
                    next.run_id !== owner.runId ||
                    next.comparison_kind !== owner.kind ||
                    next.run_token !== token
                )
                    throw Error("ComparisonRunWire");
                // This acknowledges revoked presentation only. A running=true
                // worker still belongs to the native parent until its own drain.
                if (
                    next.phase === "closed" &&
                    owner.token === token &&
                    !owner.inFlight
                )
                    this.retired.delete(owner);
            } catch (error) {
                const code = category(error);
                if (
                    !owner.inFlight &&
                    ["UnknownEvaluationRun", "Closed"].includes(code)
                )
                    this.retired.delete(owner);
            } finally {
                if (!this.disposed) this.patch({});
            }
        })();
        owner.releasing = work;
        try {
            await work;
        } finally {
            owner.releasing = null;
        }
    }
    // Root must exclude observer/lens changes from this execution-context key.
    setContext(key: string, allowed: boolean): void {
        if (
            this.disposed ||
            (this.state.context === key && this.state.allowed === allowed)
        )
            return;
        const old = this.current;
        this.epoch++;
        this.serial++;
        this.active = false;
        this.current = null;
        this.currentUncertain = false;
        if (old) {
            old.retired = true;
            this.retired.add(old);
        }
        this.patch({
            context: key,
            allowed,
            clientId: null,
            status: null,
            catalog: null,
            pending: null,
            error: null,
        });
        if (old) void this.release(old);
    }
    private async admission(): Promise<boolean> {
        if (
            this.disposed ||
            !this.state.allowed ||
            this.active ||
            this.state.status?.running
        )
            return false;
        const epoch = this.epoch;
        for (const owner of [...this.retired]) await this.release(owner);
        return (
            !this.disposed &&
            this.state.allowed &&
            this.epoch === epoch &&
            !this.active &&
            this.retired.size === 0 &&
            !this.currentUncertain
        );
    }
    private publish(
        next: ComparisonRunStatus,
        ticket: Ticket,
        action: Action,
    ): void {
        if (!this.owns(ticket)) return;
        const old = this.state.status;
        if (
            old?.phase === "completed" &&
            old.operation_id === next.operation_id &&
            action !== "close" &&
            (action === "cancel" || action === "status")
        ) {
            next = {
                ...old,
                running: next.running,
                error: next.error ?? old.error,
            };
        }
        this.currentUncertain = false;
        if (next.phase === "closed") {
            this.current = null;
            ticket.owner.retired = true;
            this.retired.add(ticket.owner);
            void this.release(ticket.owner);
        }
        this.patch({
            status: next,
            clientId:
                next.phase === "closed" && !next.running
                    ? null
                    : next.client_id,
            error: next.error,
            pending:
                next.running && next.phase !== "closed"
                    ? {
                          action: "status",
                          clientId: next.client_id,
                          runToken: next.run_token,
                          operationId: next.operation_id,
                      }
                    : null,
        });
    }
    private async operation(
        owner: Owner,
        action: Action,
        query: Record<string, unknown>,
        fresh = false,
    ): Promise<void> {
        if (
            this.disposed ||
            !this.state.allowed ||
            this.current !== owner ||
            owner.retired
        )
            return;
        this.active = true;
        const ticket = { epoch: this.epoch, serial: ++this.serial, owner };
        this.patch({
            ...(fresh ? { status: null } : {}),
            clientId: owner.client,
            pending: {
                action,
                clientId: owner.client,
                runToken: owner.token,
                operationId:
                    action === "cancel" || action === "status"
                        ? (this.state.status?.operation_id ?? null)
                        : null,
            },
            error: null,
        });
        try {
            if (!this.owns(ticket)) return;
            let next = await this.ownedCall(owner, action, query);
            if (!this.owns(ticket)) {
                await this.late(owner, next);
                return;
            }
            this.publish(next, ticket, action);
            for (
                let count = 0;
                count < MAX_POLLS &&
                this.owns(ticket) &&
                next.running &&
                next.phase !== "closed";
                count++
            ) {
                await new Promise((resolve) => setTimeout(resolve, POLL_MS));
                if (!this.owns(ticket) || !owner.token) return;
                next = await this.ownedCall(owner, "status", {
                    runToken: owner.token,
                });
                if (!this.owns(ticket)) {
                    await this.late(owner, next);
                    return;
                }
                this.publish(next, ticket, "status");
            }
            if (this.owns(ticket) && next.running && next.phase !== "closed")
                this.failed(Error("EvaluationIo"));
        } catch (error) {
            if (this.owns(ticket)) this.failed(error);
            else if (owner.retired) void this.release(owner);
        } finally {
            if (
                !this.disposed &&
                this.epoch === ticket.epoch &&
                this.serial === ticket.serial
            ) {
                this.active = false;
                this.patch({
                    pending:
                        !this.currentUncertain &&
                        this.state.status?.running &&
                        this.state.status.phase !== "closed"
                            ? {
                                  action: "status",
                                  clientId: owner.client,
                                  runToken: owner.token,
                                  operationId: this.state.status.operation_id,
                              }
                            : null,
                });
            }
        }
    }
    private async late(owner: Owner, next: ComparisonRunStatus): Promise<void> {
        if (
            this.current === owner &&
            !owner.retired &&
            !this.disposed &&
            this.state.allowed &&
            next.phase === "completed" &&
            next.operation_id === this.state.status?.operation_id &&
            this.state.status.phase !== "closed"
        ) {
            this.publish(
                next,
                { epoch: this.epoch, serial: this.serial, owner },
                "status",
            );
        } else if (owner.retired) {
            await this.release(owner);
            // An earlier close can precede this exact late admission/rebinding.
            // One bounded post-reply close targets the latest captured token.
            if (this.retired.has(owner) && !owner.inFlight)
                await this.release(owner);
        }
    }
    async loadCatalog(): Promise<void> {
        if (
            this.disposed ||
            !this.state.allowed ||
            this.active ||
            this.state.status?.running
        )
            return;
        const epoch = this.epoch,
            serial = ++this.serial;
        this.active = true;
        this.patch({
            pending: {
                action: "catalog",
                clientId: null,
                runToken: null,
                operationId: null,
            },
            error: null,
        });
        const live = () =>
            !this.disposed &&
            this.state.allowed &&
            this.epoch === epoch &&
            this.serial === serial;
        try {
            if (live()) {
                const value = await this.call("catalog", {});
                if (live())
                    this.patch({ catalog: checkedComparisonRunCatalog(value) });
            }
        } catch (error) {
            if (live()) this.failed(error, false);
        } finally {
            if (live()) {
                this.active = false;
                this.patch({ pending: null });
            }
        }
    }
    async start(kind: ComparisonRunKind, batch: number): Promise<void> {
        try {
            const requested = comparisonRunKind(kind),
                amount = comparisonRunBatch(batch);
            if (this.current) {
                if (
                    this.active ||
                    this.state.status?.running ||
                    this.currentUncertain
                )
                    return;
                if (
                    this.current.kind !== requested ||
                    this.current.initialBatch !== amount
                ) {
                    this.failed(Error("InvalidEvaluationInput"), false);
                    return;
                }
                if (this.state.allowed && this.current.client)
                    await this.operation(this.current, "start", {
                        clientId: this.current.client,
                        comparisonKind: requested,
                        batch: amount,
                    });
                return;
            }
            const epoch = this.epoch;
            if (
                !(await this.admission()) ||
                this.epoch !== epoch ||
                this.current ||
                this.active ||
                !this.state.allowed
            )
                return;
            const owner = this.owner(crypto.randomUUID());
            owner.kind = requested;
            owner.initialBatch = amount;
            this.current = owner;
            await this.operation(
                owner,
                "start",
                {
                    clientId: owner.client,
                    comparisonKind: requested,
                    batch: amount,
                },
                true,
            );
        } catch (error) {
            if (!this.disposed) this.failed(error, false);
        }
    }
    async lookup(): Promise<void> {
        if (this.disposed || !this.state.allowed || this.active) return;
        const client = this.current?.client ?? this.state.clientId;
        if (!client) return;
        const owner =
            this.current ??
            this.owner(client, this.state.status?.run_id ?? null);
        this.current = owner;
        await this.operation(owner, "lookup", { clientId: client });
    }
    async open(runId: string): Promise<void> {
        try {
            const id = comparisonRunUuid(runId);
            if (
                this.disposed ||
                !this.state.allowed ||
                this.active ||
                this.state.status?.running
            )
                return;
            const epoch = this.epoch;
            if (this.current) await this.close();
            if (
                !(await this.admission()) ||
                this.epoch !== epoch ||
                this.current ||
                this.active ||
                !this.state.allowed
            )
                return;
            const owner = this.owner(null, id);
            this.current = owner;
            await this.operation(owner, "open", { runId: id }, true);
        } catch (error) {
            if (!this.disposed) this.failed(error, false);
        }
    }
    async status(): Promise<void> {
        if (
            !this.disposed &&
            this.state.allowed &&
            !this.active &&
            this.current?.token
        )
            await this.operation(this.current, "status", {
                runToken: this.current.token,
            });
    }
    async resume(batch: number): Promise<void> {
        try {
            const amount = comparisonRunBatch(batch);
            if (
                this.disposed ||
                !this.state.allowed ||
                this.active ||
                this.state.uncertain ||
                this.state.status?.running ||
                !this.current?.token
            )
                return;
            await this.operation(this.current, "resume", {
                runToken: this.current.token,
                batch: amount,
            });
        } catch (error) {
            if (!this.disposed) this.failed(error, false);
        }
    }
    async cancel(): Promise<void> {
        const owner = this.current,
            operation = this.state.status?.operation_id;
        if (
            this.disposed ||
            !this.state.allowed ||
            this.state.uncertain ||
            !owner?.token ||
            !operation ||
            !this.state.status?.running
        )
            return;
        await this.operation(owner, "cancel", {
            runToken: owner.token,
            operationId: operation,
        });
    }
    async close(): Promise<void> {
        const owner = this.current;
        if (this.disposed) return;
        if (!owner) {
            for (const old of [...this.retired]) await this.release(old);
            return;
        }
        if (this.state.pending?.action === "close") return;
        if (!owner.token) {
            this.current = null;
            owner.retired = true;
            this.retired.add(owner);
            this.patch({ clientId: null, status: null, pending: null });
            await this.release(owner);
            return;
        }
        // Close is cleanup and remains available without presentation eligibility.
        if (!this.state.allowed) {
            this.current = null;
            owner.retired = true;
            this.retired.add(owner);
            this.patch({ clientId: null, status: null, pending: null });
            await this.release(owner);
            return;
        }
        await this.operation(owner, "close", { runToken: owner.token });
    }
    dispose(): void {
        if (this.disposed) return;
        const owner = this.current;
        this.disposed = true;
        this.epoch++;
        this.serial++;
        this.active = false;
        this.current = null;
        if (owner) {
            owner.retired = true;
            this.retired.add(owner);
        }
        this.state = frozen({
            ...this.state,
            allowed: false,
            clientId: null,
            status: null,
            catalog: null,
            pending: null,
            busy: false,
        });
        this.listeners.clear();
        for (const old of this.retired) void this.release(old);
    }
}
