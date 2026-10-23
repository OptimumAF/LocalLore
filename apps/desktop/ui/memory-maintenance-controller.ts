import type { Scope } from "./model";

export type MemoryAction = "status" | "admit" | "step" | "cancel" | "prune";
export interface MemoryContext {
    session: string;
    scope: Scope;
    expected_head: number;
    player: string;
    observer: string;
    view: "play" | "lab";
    epoch: number;
    persistent: boolean;
}
export interface MemoryJob {
    status: "ready" | "complete" | "cancelled" | "stale" | "blocked";
    basis_revision: number;
    next_from: number;
    generation: number;
    last_error: "budget" | "packet_limit" | "integrity" | null;
}
export interface MemoryReply {
    version: 1;
    kind: "memory_maintenance";
    session: string;
    scope: Scope;
    expected_head: number;
    action: MemoryAction;
    maintenance: {
        version: 1;
        scope: Scope;
        head: number;
        action: MemoryAction;
        job: MemoryJob | null;
    };
}
export interface MemoryOperation {
    version: 1;
    operation_id: number;
    running: boolean;
    phase: "starting" | "memory_maintenance" | "completed" | "error";
    error: string | null;
    result: MemoryReply | null;
}
const errors = new Set([
    "Closed",
    "Scope",
    "Stale",
    "Busy",
    "Unsupported",
    "Cancelled",
    "NotFound",
    "TooLarge",
    "Integrity",
    "Database",
    "Full",
    "Internal",
    "InvalidInput",
    "ArchiveBusy",
    "ArchiveInternal",
    "ArchiveBudget",
    "InvalidArchiveInput",
    "UnknownArchiveOperation",
    "StorageUnavailable",
    "Transport",
    "Wire",
]);
const actions = ["status", "admit", "step", "cancel", "prune"] as const;
const object = (v: unknown): v is Record<string, unknown> =>
    !!v && typeof v === "object" && !Array.isArray(v);
const integer = (v: unknown): v is number =>
    Number.isSafeInteger(v) && Number(v) >= 0;
const id = (v: unknown, max = 64): v is string =>
    typeof v === "string" && v.length <= max && /^[A-Za-z0-9_-]+$/.test(v);
function wire(): never {
    throw Error("Wire");
}
function keys(
    v: unknown,
    names: string[],
): asserts v is Record<string, unknown> {
    if (
        !object(v) ||
        Object.keys(v).length !== names.length ||
        names.some((k) => !Object.hasOwn(v, k))
    )
        wire();
}
function scope(v: unknown): Scope {
    keys(v, ["story", "branch"]);
    if (!id(v.story) || !id(v.branch)) wire();
    return { story: v.story, branch: v.branch };
}
const same = (a: Scope, b: Scope) =>
    a.story === b.story && a.branch === b.branch;
export function memoryContextIdentity(v: MemoryContext | null): string {
    if (v === null) return "none";
    keys(v, [
        "session",
        "scope",
        "expected_head",
        "player",
        "observer",
        "view",
        "epoch",
        "persistent",
    ]);
    const s = scope(v.scope);
    if (
        !id(v.session, 128) ||
        !integer(v.expected_head) ||
        !id(v.player) ||
        !id(v.observer) ||
        !["play", "lab"].includes(String(v.view)) ||
        !integer(v.epoch) ||
        typeof v.persistent !== "boolean"
    )
        wire();
    return JSON.stringify([
        v.session,
        s.story,
        s.branch,
        v.expected_head,
        v.player,
        v.observer,
        v.view,
        v.epoch,
        v.persistent,
    ]);
}
export function decodeMemoryOperation(
    value: unknown,
    context: MemoryContext,
    action: MemoryAction,
    operation?: number,
): MemoryOperation {
    // Detached, bounded JSON data only; no foreign surface/permission fields.
    try {
        if (new TextEncoder().encode(JSON.stringify(value)).length > 4096)
            wire();
    } catch {
        wire();
    }
    keys(value, [
        "version",
        "operation_id",
        "running",
        "phase",
        "error",
        "result",
    ]);
    if (
        value.version !== 1 ||
        !integer(value.operation_id) ||
        value.operation_id === 0 ||
        (operation !== undefined && value.operation_id !== operation) ||
        typeof value.running !== "boolean" ||
        !["starting", "memory_maintenance", "completed", "error"].includes(
            String(value.phase),
        ) ||
        !(
            value.error === null ||
            (typeof value.error === "string" && errors.has(value.error))
        )
    )
        wire();
    let result: MemoryReply | null = null;
    if (value.result !== null) {
        const r = value.result;
        keys(r, [
            "version",
            "kind",
            "session",
            "scope",
            "expected_head",
            "action",
            "maintenance",
        ]);
        const s = scope(r.scope);
        if (
            r.version !== 1 ||
            r.kind !== "memory_maintenance" ||
            r.session !== context.session ||
            !same(s, context.scope) ||
            r.expected_head !== context.expected_head ||
            r.action !== action
        )
            wire();
        const m = r.maintenance;
        keys(m, ["version", "scope", "head", "action", "job"]);
        const ms = scope(m.scope);
        if (
            m.version !== 1 ||
            !same(ms, s) ||
            m.head !== r.expected_head ||
            m.action !== action
        )
            wire();
        let job: MemoryJob | null = null;
        if (m.job !== null) {
            const j = m.job;
            keys(j, [
                "status",
                "basis_revision",
                "next_from",
                "generation",
                "last_error",
            ]);
            if (
                ![
                    "ready",
                    "complete",
                    "cancelled",
                    "stale",
                    "blocked",
                ].includes(String(j.status)) ||
                !integer(j.basis_revision) ||
                !integer(j.next_from) ||
                !integer(j.generation) ||
                j.generation === 0 ||
                j.next_from > j.basis_revision ||
                !(
                    j.last_error === null ||
                    ["budget", "packet_limit", "integrity"].includes(
                        String(j.last_error),
                    )
                ) ||
                (j.status === "complete" && j.next_from !== j.basis_revision) ||
                (j.status === "ready" &&
                    (j.next_from >= j.basis_revision ||
                        j.basis_revision !== context.expected_head)) ||
                (j.status === "blocked" && j.last_error === null) ||
                (!["blocked", "stale"].includes(String(j.status)) &&
                    j.last_error !== null)
            )
                wire();
            job = {
                status: j.status as MemoryJob["status"],
                basis_revision: j.basis_revision,
                next_from: j.next_from,
                generation: j.generation,
                last_error: j.last_error as MemoryJob["last_error"],
            };
        }
        result = {
            version: 1,
            kind: "memory_maintenance",
            session: context.session,
            scope: s,
            expected_head: context.expected_head,
            action,
            maintenance: {
                version: 1,
                scope: ms,
                head: context.expected_head,
                action,
                job,
            },
        };
    }
    if (
        value.running
            ? !["starting", "memory_maintenance"].includes(
                  String(value.phase),
              ) ||
              value.error !== null ||
              result !== null
            : value.phase === "completed"
              ? result === null || value.error !== null
              : value.phase !== "error" ||
                value.error === null ||
                result !== null
    )
        wire();
    return {
        version: 1,
        operation_id: value.operation_id,
        running: value.running,
        phase: value.phase as MemoryOperation["phase"],
        error: value.error as string | null,
        result,
    };
}
type Invoke = (
    command: string,
    args?: Record<string, unknown>,
) => Promise<unknown>;
export class MemoryMaintenanceController {
    private state = {
        context: null as MemoryContext | null,
        busy: false,
        consent: false,
        operation: null as MemoryOperation | null,
        action: null as MemoryAction | null,
        reply: null as MemoryReply | null,
        uncertain: false,
        error: null as string | null,
        notice: "",
    };
    private epoch = 0;
    private key = "none";
    private disposed = false;
    private listeners = new Set<() => void>();
    constructor(private invoke: Invoke) {}
    get = () => this.state;
    subscribe = (f: () => void) => {
        this.listeners.add(f);
        return () => {
            this.listeners.delete(f);
        };
    };
    private patch(v: Partial<typeof this.state>) {
        this.state = { ...this.state, ...v };
        for (const f of this.listeners) f();
    }
    matchesContext(context: MemoryContext | null) {
        try {
            return (
                !this.disposed && this.key === memoryContextIdentity(context)
            );
        } catch {
            return false;
        }
    }
    contextChanged(context: MemoryContext | null) {
        if (this.disposed) return;
        let key: string;
        try {
            key = memoryContextIdentity(context);
        } catch {
            context = null;
            key = "invalid";
        }
        if (key === this.key) return;
        this.stopKnown(this.state.operation);
        this.epoch++;
        this.key = key;
        this.patch({
            context: context
                ? { ...context, scope: { ...context.scope } }
                : null,
            busy: false,
            consent: false,
            operation: null,
            action: null,
            reply: null,
            uncertain: false,
            error: key === "invalid" ? "Wire" : null,
            notice: "",
        });
    }
    dispose() {
        this.contextChanged(null);
        this.disposed = true;
        this.epoch++;
    }
    consent(value: boolean) {
        this.patch({ consent: value === true });
    }
    private eligible() {
        const c = this.state.context;
        return (
            !!c &&
            c.persistent &&
            (c.view === "play" || c.observer === c.player)
        );
    }
    can(action: MemoryAction) {
        if (
            this.disposed ||
            !this.eligible() ||
            this.state.busy ||
            !actions.includes(action)
        )
            return false;
        if (action === "status") return true;
        if (
            this.state.uncertain ||
            this.state.error ||
            this.state.operation?.running ||
            !this.state.reply
        )
            return false;
        const j = this.state.reply.maintenance.job;
        if (action === "admit") return j === null && this.state.consent;
        if (action === "step" || action === "cancel")
            return j?.status === "ready";
        return (
            !!j &&
            ["complete", "cancelled", "stale", "blocked"].includes(j.status) &&
            this.state.consent
        );
    }
    private stopKnown(operation: MemoryOperation | null) {
        if (operation?.running)
            void this.invoke("archive_cancel", {
                operationId: operation.operation_id,
            }).catch(() => {});
    }
    private failure(error: unknown) {
        const name = error instanceof Error ? error.message : String(error);
        this.patch({
            busy: false,
            error: errors.has(name) ? name : "Wire",
            uncertain: true,
            consent: false,
            notice: "Acknowledgement unavailable. Read status; do not repeat maintenance. A completed change may already be saved.",
        });
    }
    private accept(value: MemoryOperation) {
        this.patch({
            busy: false,
            operation: value,
            reply: value.result ?? this.state.reply,
            uncertain: false,
            error: value.error,
            consent: false,
            notice: value.running
                ? "One operation is running. Read status or stop the operation; no automatic steps."
                : value.error
                  ? "No automatic retry. Read status before another action."
                  : "Snapshot read from shared storage. No model was called.",
        });
    }
    async act(action: MemoryAction): Promise<void> {
        if (!this.can(action)) return;
        const context = this.state.context!,
            epoch = ++this.epoch;
        const prior = this.state.operation;
        // Known pending operations are observed, never restarted or resubmitted.
        const observing =
            action === "status" &&
            !!prior &&
            (prior.running || this.state.uncertain);
        const expected = observing ? this.state.action! : action;
        this.patch({
            busy: true,
            error: null,
            action: expected,
            operation: observing ? prior : null,
        });
        try {
            const raw = await this.invoke(
                observing ? "archive_status" : "memory_maintenance_start",
                observing
                    ? { operationId: prior!.operation_id }
                    : {
                          request: {
                              session: context.session,
                              scope: { ...context.scope },
                              expected_head: context.expected_head,
                              action,
                          },
                      },
            );
            const result = decodeMemoryOperation(
                raw,
                context,
                expected,
                observing ? prior!.operation_id : undefined,
            );
            if (epoch !== this.epoch || this.disposed) {
                this.stopKnown(result);
                return;
            }
            this.accept(result);
        } catch (error) {
            if (epoch === this.epoch && !this.disposed) this.failure(error);
        }
    }
    async stop(): Promise<void> {
        const operation = this.state.operation,
            context = this.state.context,
            action = this.state.action;
        if (
            !operation?.running ||
            !context ||
            !action ||
            this.state.busy ||
            this.disposed
        )
            return;
        const epoch = ++this.epoch;
        this.patch({ busy: true, error: null });
        try {
            const result = decodeMemoryOperation(
                await this.invoke("archive_cancel", {
                    operationId: operation.operation_id,
                }),
                context,
                action,
                operation.operation_id,
            );
            if (epoch !== this.epoch || this.disposed) return;
            this.accept(result);
            if (result.running)
                this.patch({
                    notice: "Stop requested. Read status to learn the saved outcome; cancellation is not rollback.",
                });
        } catch (error) {
            if (epoch === this.epoch && !this.disposed) this.failure(error);
        }
    }
}
