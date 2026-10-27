import {
    checkedComparisonRunCatalog,
    checkedComparisonRunStatus,
    checkedNativeComparisonRunCatalog,
    checkedNativeComparisonRunStatus,
    comparisonRunBatch,
    comparisonRunErrors,
    comparisonRunKind,
    comparisonRunUuid,
    nativeComparisonRunErrors,
} from "./comparison-run-model";
import type {
    ComparisonRunCatalog,
    ComparisonRunError,
    ComparisonRunKind,
    ComparisonRunStatus,
    NativeComparisonRunCatalog,
    NativeComparisonRunStatus,
    NativeComparisonRunError,
} from "./comparison-run-model";
import { checkedSelectedCleanup } from "./selected-evaluation-model";
import type { SelectedCleanup } from "./selected-evaluation-model";
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
export type ComparisonRunMode = "scripted_baseline" | "approved_native";
export type NativeComparisonRunOptions = Readonly<{ mode: "approved_native" }>;
export type NativeComparisonRunState = Omit<
    ComparisonRunState,
    "status" | "catalog" | "error"
> & {
    mode: "approved_native";
    status: NativeComparisonRunStatus | null;
    catalog: NativeComparisonRunCatalog | null;
    error: NativeComparisonRunError | null;
    cleanup: SelectedCleanup | null;
    cleanupPending: "status" | "retry" | null;
    cleanupUncertain: boolean;
    cleanupError: NativeComparisonRunError | null;
};
export type ComparisonRunConsumerState =
    | (ComparisonRunState & { mode: "scripted_baseline" })
    | NativeComparisonRunState;
type Status = ComparisonRunStatus | NativeComparisonRunStatus;
type Catalog = ComparisonRunCatalog | NativeComparisonRunCatalog;
function isNativeStatus(status: Status): status is NativeComparisonRunStatus {
    return status.input_lane === "approved_native";
}
type Update = Partial<
    Omit<ComparisonRunState, "status" | "catalog" | "error">
> & {
    status?: Status | null;
    catalog?: Catalog | null;
    error?: NativeComparisonRunError | null;
};
type CleanupUpdate = Partial<
    Pick<
        NativeComparisonRunState,
        "cleanup" | "cleanupPending" | "cleanupUncertain" | "cleanupError"
    >
>;
type Transport =
    | Readonly<{
          mode: "scripted_baseline";
          command: "evaluation_comparison_run";
          status: typeof checkedComparisonRunStatus;
          catalog: typeof checkedComparisonRunCatalog;
      }>
    | Readonly<{
          mode: "approved_native";
          command: "evaluation_comparison_native";
          status: typeof checkedNativeComparisonRunStatus;
          catalog: typeof checkedNativeComparisonRunCatalog;
      }>;
const SCRIPTED: Transport = Object.freeze({
    mode: "scripted_baseline",
    command: "evaluation_comparison_run",
    status: checkedComparisonRunStatus,
    catalog: checkedComparisonRunCatalog,
});
const NATIVE: Transport = Object.freeze({
    mode: "approved_native",
    command: "evaluation_comparison_native",
    status: checkedNativeComparisonRunStatus,
    catalog: checkedNativeComparisonRunCatalog,
});
type Owner = {
    readonly transport: Transport;
    client: string | null;
    runId: string | null;
    token: string | null;
    kind: ComparisonRunKind | null;
    initialBatch: number | null;
    operation: number | null;
    protocol: 3 | 4 | null;
    sent: boolean;
    inFlight: number;
    retired: boolean;
    releasing: Promise<void> | null;
    cleanupObserved: boolean;
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
function nativeCategory(error: unknown): NativeComparisonRunError {
    const value =
        error instanceof Error
            ? error.message
            : typeof error === "string"
              ? error
              : "";
    return value === "ComparisonRunWire" || value === "SelectedEvaluationWire"
        ? "ComparisonRunWire"
        : (nativeComparisonRunErrors.find((code) => code === value) ??
              "EvaluationIo");
}
type ConstructorArgs =
    | [
          invoke: ComparisonRunInvoke,
          onError?: (error: ComparisonRunError) => void,
      ]
    | [
          invoke: ComparisonRunInvoke,
          onError: ((error: NativeComparisonRunError) => void) | undefined,
          options: NativeComparisonRunOptions,
      ];
export class ComparisonRunController {
    private state: ComparisonRunConsumerState;
    private readonly invoke: ComparisonRunInvoke;
    private readonly transport: Transport;
    private readonly reportError: (error: NativeComparisonRunError) => void;
    private listeners = new Set<() => void>();
    private epoch = 0;
    private serial = 0;
    private active = false;
    private disposed = false;
    private currentUncertain = false;
    private reporting = false;
    private current: Owner | null = null;
    private globalAuxEpoch = 0;
    // Admission waits for every retired captured capability. This is a
    // presentation barrier, never a second worker/cleanup authority.
    private retired = new Set<Owner>();
    constructor(
        invoke: ComparisonRunInvoke,
        onError?: (error: ComparisonRunError) => void,
    );
    constructor(
        invoke: ComparisonRunInvoke,
        onError: ((error: NativeComparisonRunError) => void) | undefined,
        options: NativeComparisonRunOptions,
    );
    constructor(...args: ConstructorArgs) {
        if (typeof args[0] !== "function" || args.length > 3)
            throw Error("ComparisonRunWire");
        this.invoke = args[0];
        const initial: ComparisonRunState = {
            context: "",
            allowed: false,
            clientId: null,
            status: null,
            catalog: null,
            pending: null,
            busy: false,
            uncertain: false,
            error: null,
        };
        if (args.length === 3) {
            if (!args[2] || args[2].mode !== "approved_native")
                throw Error("ComparisonRunWire");
            this.transport = NATIVE;
            const callback = args[1];
            this.reportError = (code) => callback?.(nativeCategory(code));
            const state: NativeComparisonRunState = {
                ...initial,
                mode: "approved_native",
                status: null,
                catalog: null,
                error: null,
                cleanup: null,
                cleanupPending: null,
                cleanupUncertain: false,
                cleanupError: null,
            };
            this.state = frozen(state);
        } else {
            this.transport = SCRIPTED;
            const callback = args[1];
            this.reportError = (code) => callback?.(category(code));
            const state: ComparisonRunState & { mode: "scripted_baseline" } = {
                ...initial,
                mode: "scripted_baseline",
            };
            this.state = frozen(state);
        }
    }
    get mode(): ComparisonRunMode {
        return this.transport.mode;
    }
    get(): Readonly<ComparisonRunConsumerState> {
        return this.state;
    }
    subscribe(listener: () => void): () => void {
        if (!this.disposed) this.listeners.add(listener);
        return () => this.listeners.delete(listener);
    }
    private install(next: ComparisonRunConsumerState): void {
        next.busy = this.active || next.status?.running === true;
        next.uncertain = this.currentUncertain || this.retired.size > 0;
        const old = new Map(Object.entries(this.state));
        if (
            Object.entries(next).every(([key, value]) => value === old.get(key))
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
    private patch(update: Update): void {
        const status =
            update.status === undefined ? this.state.status : update.status;
        const catalog =
            update.catalog === undefined ? this.state.catalog : update.catalog;
        const error =
            update.error === undefined ? this.state.error : update.error;
        if (this.state.mode === "approved_native") {
            if (status !== null && !isNativeStatus(status))
                throw Error("ComparisonRunWire");
            if (catalog !== null && catalog.input_lane !== "approved_native")
                throw Error("ComparisonRunWire");
            this.install({ ...this.state, ...update, status, catalog, error });
        } else {
            if (status !== null && status.version !== 1)
                throw Error("ComparisonRunWire");
            if (catalog !== null && catalog.version !== 1)
                throw Error("ComparisonRunWire");
            this.install({
                ...this.state,
                ...update,
                status,
                catalog,
                error: error === null ? null : category(error),
            });
        }
    }
    private patchCleanup(update: CleanupUpdate): void {
        if (this.disposed || this.state.mode !== "approved_native") return;
        this.install({
            ...this.state,
            cleanup:
                update.cleanup === undefined
                    ? this.state.cleanup
                    : update.cleanup,
            cleanupPending:
                update.cleanupPending === undefined
                    ? this.state.cleanupPending
                    : update.cleanupPending,
            cleanupUncertain:
                update.cleanupUncertain === undefined
                    ? this.state.cleanupUncertain
                    : update.cleanupUncertain,
            cleanupError:
                update.cleanupError === undefined
                    ? this.state.cleanupError
                    : update.cleanupError,
        });
    }
    private report(code: NativeComparisonRunError): void {
        if (this.reporting) return;
        this.reporting = true;
        try {
            this.reportError(code);
        } catch {
            /* no authority */
        } finally {
            this.reporting = false;
        }
    }
    private failed(error: unknown, uncertain = true): void {
        const code =
            this.mode === "approved_native"
                ? nativeCategory(error)
                : category(error);
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
            if (owner.transport.mode === "approved_native")
                this.currentUncertain = false; // the captured retired barrier now owns this uncertainty
            void this.release(owner);
        }
        this.patch({
            error: code,
            ...(loss
                ? { status: null, catalog: null, clientId: null, pending: null }
                : {}),
        });
        this.report(code);
    }
    private call(
        action: Action | "cleanup_status" | "retry_cleanup",
        query: Record<string, unknown>,
        transport: Transport = this.transport,
    ): Promise<unknown> {
        const encoded = JSON.stringify(query);
        if (new TextEncoder().encode(encoded).length > 4096)
            return Promise.reject(Error("ComparisonRunWire"));
        return this.invoke(transport.command, { action, query });
    }
    private owner(client: string | null, runId: string | null = null): Owner {
        return {
            transport: this.transport,
            client,
            runId,
            token: null,
            kind: null,
            initialBatch: null,
            operation: null,
            protocol: this.state.catalog?.protocol_version ?? null,
            sent: false,
            inFlight: 0,
            retired: false,
            releasing: null,
            cleanupObserved: false,
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
    private bind(owner: Owner, next: Status, rebind = false): void {
        if (
            next.input_lane !== owner.transport.mode ||
            (owner.protocol !== null && next.protocol_version !== owner.protocol) ||
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
        owner.protocol = next.protocol_version;
    }
    private async ownedCall(
        owner: Owner,
        action: Action,
        query: Record<string, unknown>,
    ): Promise<Status> {
        owner.sent = true;
        owner.inFlight++;
        try {
            const next = owner.transport.status(
                await this.call(action, query, owner.transport),
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
    private async observeRelease(owner: Owner): Promise<void> {
        if (
            this.disposed ||
            !owner.sent ||
            owner.transport.mode !== "approved_native" ||
            owner.cleanupObserved
        )
            return;
        owner.cleanupObserved = true;
        await this.cleanup("status");
    }
    private async release(
        owner: Owner,
        acknowledgedClose?: Status,
    ): Promise<void> {
        if (!owner.retired || owner.inFlight) return;
        if (owner.releasing) return owner.releasing;
        // Install the release guard before any cleanup-state notification can
        // synchronously reenter close(), including an already-ACKed close.
        const work = Promise.resolve().then(async () => {
            try {
                if (!owner.sent) {
                    this.retired.delete(owner);
                    return;
                }
                if (!owner.token) {
                    // A lost cold-open ACK has a known run ID, not an invented
                    // client. Resolve only its actual bounded native metadata.
                    if (!owner.client && owner.runId) {
                        const catalog = owner.transport.catalog(
                            await this.call("catalog", {}, owner.transport),
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
                        owner.transport.status(
                            await this.call(
                                "lookup",
                                {
                                    clientId: owner.client,
                                },
                                owner.transport,
                            ),
                        ),
                        true,
                    );
                }
                const token = owner.token;
                if (!token || owner.inFlight) return;
                const next =
                    acknowledgedClose ??
                    owner.transport.status(
                        await this.call(
                            "close",
                            { runToken: token },
                            owner.transport,
                        ),
                    );
                if (
                    next.client_id !== owner.client ||
                    next.run_id !== owner.runId ||
                    next.protocol_version !== owner.protocol ||
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
                ) {
                    // Presentation closure does not establish global cleanup.
                    if (
                        next.running ||
                        (isNativeStatus(next) &&
                            (next.cleanup_required || next.cleanup_running))
                    )
                        await this.observeRelease(owner);
                    if (!owner.inFlight) this.retired.delete(owner);
                }
            } catch (error) {
                const code =
                    owner.transport.mode === "approved_native"
                        ? nativeCategory(error)
                        : category(error);
                if (
                    !owner.inFlight &&
                    ["UnknownEvaluationRun", "Closed"].includes(code)
                ) {
                    if (code === "UnknownEvaluationRun")
                        await this.observeRelease(owner);
                    if (!owner.inFlight) this.retired.delete(owner);
                }
            } finally {
                if (!this.disposed) this.patch({});
            }
        });
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
    private generationBlocked(): boolean {
        if (this.state.mode !== "approved_native") return false;
        return (
            this.state.cleanupPending !== null ||
            this.state.cleanupUncertain ||
            this.state.cleanupError !== null ||
            this.state.cleanup?.cleanup_required === true ||
            this.state.cleanup?.running === true ||
            this.state.status?.cleanup_required === true ||
            this.state.status?.cleanup_running === true
        );
    }
    private invalidateAuxiliary(): void {
        ++this.globalAuxEpoch;
        if (
            this.state.mode === "approved_native" &&
            this.state.cleanupPending !== null
        )
            this.patchCleanup({ cleanupPending: null, cleanupUncertain: true });
    }
    private async cleanup(
        action: "status" | "retry",
        origin?: () => boolean,
    ): Promise<boolean> {
        if (this.disposed || this.state.mode !== "approved_native")
            return false;
        const serial = ++this.globalAuxEpoch;
        const live = () =>
            !this.disposed &&
            serial === this.globalAuxEpoch &&
            (!origin || origin());
        this.patchCleanup({ cleanupPending: action, cleanupError: null });
        try {
            if (!live()) return false;
            const raw = await this.call(
                action === "status" ? "cleanup_status" : "retry_cleanup",
                {},
                NATIVE,
            );
            if (!live()) return false;
            const next = checkedSelectedCleanup(raw);
            this.patchCleanup({
                cleanup: next,
                cleanupUncertain: false,
                cleanupError: next.error,
            });
            return (
                live() &&
                !next.cleanup_required &&
                !next.running &&
                next.error === null
            );
        } catch (error) {
            if (live()) {
                const code = nativeCategory(error);
                this.patchCleanup({
                    cleanupUncertain: true,
                    cleanupError: code,
                });
                if (live()) this.report(code);
            }
            return false;
        } finally {
            // A retired admission must clear its own pending indicator without
            // publishing its stale clean result. Newer auxiliary requests win.
            if (!this.disposed && serial === this.globalAuxEpoch)
                this.patchCleanup({ cleanupPending: null });
        }
    }
    async cleanupStatus(): Promise<void> {
        await this.cleanup("status");
    }
    async retryCleanup(): Promise<void> {
        await this.cleanup("retry");
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
    private publish(next: Status, ticket: Ticket, action: Action): void {
        if (!this.owns(ticket)) return;
        const old = this.state.status;
        if (
            old?.phase === "completed" &&
            old.operation_id === next.operation_id &&
            action !== "close" &&
            (action === "cancel" || action === "status")
        ) {
            if (isNativeStatus(old) && isNativeStatus(next)) {
                if (next.phase !== "closed") {
                    const blocked =
                        next.phase === "cleanup_required" ||
                        next.cleanup_required ||
                        next.cleanup_running;
                    next = {
                        ...old,
                        running: next.running,
                        error: next.error ?? old.error,
                        cleanup_required: next.cleanup_required,
                        cleanup_running: next.cleanup_running,
                        cause: next.cause,
                        phase: blocked ? next.phase : old.phase,
                        report_ready: blocked ? false : old.report_ready,
                    };
                }
            } else if (old.version === 1 && next.version === 1) {
                next = {
                    ...old,
                    running: next.running,
                    error: next.error ?? old.error,
                };
            } else throw Error("ComparisonRunWire");
        }
        this.currentUncertain = false;
        if (next.phase === "closed") {
            this.current = null;
            ticket.owner.retired = true;
            this.retired.add(ticket.owner);
            // An actual native close already revoked this exact token. Other
            // closed metadata responses still require explicit token closure.
            void this.release(
                ticket.owner,
                isNativeStatus(next) && action === "close" ? next : undefined,
            );
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
        const generation =
            owner.transport.mode === "approved_native" &&
            (action === "start" || action === "resume");
        if (generation && this.generationBlocked()) return;
        const entered = this.epoch;
        if (owner.transport.mode === "approved_native" && (generation || fresh))
            this.invalidateAuxiliary();
        if (
            this.disposed ||
            !this.state.allowed ||
            this.epoch !== entered ||
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
            if (generation) {
                const clear = await this.cleanup("status", () =>
                    this.owns(ticket),
                );
                if (!this.owns(ticket)) return;
                if (!clear || this.generationBlocked()) {
                    if (!owner.sent) {
                        this.current = null;
                        owner.retired = true;
                        this.patch({
                            clientId: null,
                            status: null,
                            pending: null,
                        });
                    }
                    return;
                }
                if (!this.owns(ticket)) return;
            }
            let next = await this.ownedCall(owner, action, query);
            if (!this.owns(ticket)) {
                await this.late(owner, next);
                return;
            }
            this.publish(next, ticket, action);
            if (
                action === "close" &&
                isNativeStatus(next) &&
                next.phase === "closed"
            ) {
                // One explicit close gesture waits for its known presentation
                // acknowledgement/observation; no unknown-ACK retry is implied.
                await this.release(owner, next);
                return;
            }
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
    private async late(owner: Owner, next: Status): Promise<void> {
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
                if (live()) {
                    const catalog = this.transport.catalog(value);
                    if (this.current?.protocol !== null && this.current?.protocol !== undefined &&
                        this.current.protocol !== catalog.protocol_version) throw Error("ComparisonRunWire");
                    this.patch({ catalog });
                }
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
            if (this.generationBlocked()) return;
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
                !this.state.allowed ||
                this.generationBlocked()
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
                this.generationBlocked() ||
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
            if (owner.transport.mode === "approved_native")
                this.currentUncertain = false;
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
        ++this.globalAuxEpoch;
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

export function createNativeComparisonRunController(
    invoke: ComparisonRunInvoke,
    onError?: (error: NativeComparisonRunError) => void,
): ComparisonRunController {
    return new ComparisonRunController(invoke, onError, {
        mode: "approved_native",
    });
}
