import type { Scope } from "./model";
import { sameScope } from "./model";
import { contextIdentity, timelineId, timelineNumber } from "./timeline-model";
import type { TimelineContext } from "./timeline-model";
type Invoke = (
    name: string,
    args?: Record<string, unknown>,
) => Promise<unknown>;
export interface ForkRequest {
    readonly parent: Scope;
    readonly child_branch: string;
    readonly expected_parent_revision: number;
    readonly at_revision: number;
}
export interface ForkOutcome {
    readonly version: 1;
    readonly scope: Scope;
    readonly parent: Scope;
    readonly fork_revision: number;
    readonly head_revision: number;
    readonly created: boolean;
}
function object(v: unknown): v is Record<string, unknown> {
    return !!v && typeof v === "object" && !Array.isArray(v);
}
function exact(v: unknown, keys: string[]): v is Record<string, unknown> {
    return (
        object(v) &&
        Object.keys(v).length === keys.length &&
        keys.every((k) => Object.hasOwn(v, k))
    );
}
export function decodeForkRequest(v: unknown): ForkRequest {
    if (
        !exact(v, [
            "parent",
            "child_branch",
            "expected_parent_revision",
            "at_revision",
        ]) ||
        !exact(v.parent, ["story", "branch"]) ||
        !timelineId(v.parent.story) ||
        !timelineId(v.parent.branch) ||
        !timelineId(v.child_branch) ||
        v.child_branch === v.parent.branch ||
        !timelineNumber(v.expected_parent_revision) ||
        !timelineNumber(v.at_revision) ||
        v.at_revision > v.expected_parent_revision
    )
        throw Error("InvalidForkInput");
    return Object.freeze({
        parent: Object.freeze({
            story: v.parent.story,
            branch: v.parent.branch,
        }),
        child_branch: v.child_branch,
        expected_parent_revision: v.expected_parent_revision,
        at_revision: v.at_revision,
    });
}
function outcome(v: unknown, request: ForkRequest): ForkOutcome {
    if (
        !exact(v, [
            "version",
            "scope",
            "parent",
            "fork_revision",
            "head_revision",
            "created",
        ]) ||
        v.version !== 1 ||
        !exact(v.scope, ["story", "branch"]) ||
        !exact(v.parent, ["story", "branch"]) ||
        v.scope.story !== request.parent.story ||
        v.scope.branch !== request.child_branch ||
        v.parent.story !== request.parent.story ||
        v.parent.branch !== request.parent.branch ||
        v.fork_revision !== request.at_revision ||
        !timelineNumber(v.head_revision) ||
        v.head_revision < request.at_revision ||
        typeof v.created !== "boolean"
    )
        throw Error("Wire");
    return Object.freeze({
        ...v,
        scope: Object.freeze({ ...v.scope }),
        parent: Object.freeze({ ...v.parent }),
    }) as unknown as ForkOutcome;
}
const errors = new Set([
    "InvalidForkInput",
    "ForkConsentRequired",
    "Closed",
    "Scope",
    "Stale",
    "Busy",
    "Mismatch",
    "NotFound",
    "Unsupported",
    "Cancelled",
    "Transport",
    "StorageUnavailable",
    "Io",
    "Full",
    "Integrity",
    "Malformed",
    "Rule",
    "RetryMismatch",
    "TooLarge",
    "Internal",
    "ArchiveInternal",
    "ArchiveBusy",
    "ArchiveBudget",
    "UnknownArchiveOperation",
]);
function errorName(e: unknown) {
    const value = e instanceof Error ? e.message : String(e);
    return errors.has(value) ? value : "Wire";
}
export class ForkController {
    private state = {
        busy: false,
        status: "idle" as
            | "idle"
            | "prepared"
            | "pending"
            | "uncertain"
            | "complete"
            | "not_found"
            | "error",
        request: null as ForkRequest | null,
        result: null as ForkOutcome | null,
        operation: null as number | null,
        error: null as string | null,
        notice: "",
        lookupOnly: false,
        consent: false,
    };
    private context: TimelineContext | null = null;
    private key = "none";
    private requestKey = "";
    private epoch = 0;
    private disposed = false;
    private cancelRequested = false;
    private preparing = false;
    private listeners = new Set<() => void>();
    constructor(
        private invoke: Invoke,
        private refreshLibrary: () => Promise<unknown>,
        private saveRecovery: (request: ForkRequest) => void,
    ) {}
    get = () => this.state;
    subscribe = (listener: () => void) => {
        this.listeners.add(listener);
        return () => {
            this.listeners.delete(listener);
        };
    };
    private patch(p: Partial<typeof this.state>) {
        this.state = { ...this.state, ...p };
        for (const listener of this.listeners) listener();
    }
    private cancelOperation(id: number) {
        void this.invoke("archive_cancel", { operationId: id }).catch(() => {});
    }
    contextChanged(context: TimelineContext | null) {
        if (this.disposed) return;
        let key: string;
        try {
            key = contextIdentity(context);
        } catch {
            key = "invalid";
            context = null;
        }
        if (key === this.key) return;
        this.epoch++;
        if (this.state.operation !== null && this.state.busy)
            this.cancelOperation(this.state.operation);
        this.key = key;
        this.context = context
            ? Object.freeze({
                  ...context,
                  scope: Object.freeze({ ...context.scope }),
              })
            : null;
        this.patch({
            busy: false,
            operation: null,
            result: null,
            error: null,
            lookupOnly: !!this.state.request,
            consent: false,
            status: this.state.request
                ? this.state.status === "complete" ||
                  this.state.status === "not_found"
                    ? this.state.status
                    : this.state.status === "prepared"
                      ? "not_found"
                      : "uncertain"
                : "idle",
            notice: this.state.request
                ? "Selection changed. Recover this exact identity by lookup; no fork will run automatically."
                : "",
        });
    }
    prepare(at: number, child: string) {
        if (this.disposed || this.preparing || this.state.busy || !this.context?.persistent)
            return;
        // Replacing an unresolved request requires the caller to retain its saved
        // recovery identity. Do not silently discard an uncertain native outcome.
        if (
            this.state.request &&
            ["pending", "uncertain"].includes(this.state.status)
        )
            return;
        const epoch = this.epoch, key = this.key, context = this.context;
        this.preparing = true;
        try {
            const request = decodeForkRequest({
                parent: context.scope,
                child_branch: child,
                expected_parent_revision: context.revision,
                at_revision: at,
            });
            this.saveRecovery(request); // Persist identity BEFORE native dispatch.
            if (this.disposed) return;
            if (this.epoch !== epoch || this.key !== key || this.context !== context) {
                this.requestKey = "";
                this.patch({ request, result: null, operation: null, error: null,
                    status: "uncertain", lookupOnly: true, consent: false,
                    notice: "Recovery identity saved for the original selection. Lookup never creates a missing timeline.",
                });
                return;
            }
            this.requestKey = key;
            this.patch({
                request,
                result: null,
                operation: null,
                error: null,
                status: "prepared",
                lookupOnly: false,
                consent: false,
                notice: "Request a new timeline at this revision. The engine verifies that it is a completed turn boundary before saving. The original and its later choices stay intact.",
            });
        } catch (e) {
            if (!this.disposed && this.epoch === epoch && this.key === key && this.context === context)
                this.patch({ error: errorName(e), status: "error" });
        } finally { this.preparing = false; }
    }
    restore(value: unknown) {
        if (this.disposed || this.preparing || this.state.busy) return;
        try {
            const request = decodeForkRequest(value);
            this.requestKey = "";
            this.patch({
                request,
                result: null,
                operation: null,
                error: null,
                status: "uncertain",
                lookupOnly: true,
                consent: false,
                notice: "Recovered identity only. Check saved timelines; absence will never recreate this request.",
            });
        } catch (e) {
            this.patch({
                request: null,
                result: null,
                operation: null,
                error: errorName(e),
                status: "error",
                lookupOnly: true,
                consent: false,
            });
        }
    }
    private live(epoch: number) {
        return !this.disposed && epoch === this.epoch;
    }
    setConsent(value: boolean) {
        if (!this.disposed && !this.state.busy) this.patch({ consent: value });
    }
    async confirm(consent: boolean) {
        const request = this.state.request,
            context = this.context;
        if (
            this.disposed ||
            this.preparing ||
            this.state.busy ||
            !request ||
            !context?.persistent ||
            this.state.lookupOnly ||
            this.requestKey !== this.key
        )
            return;
        if (!consent) {
            this.patch({ error: "ForkConsentRequired", consent: false });
            return;
        }
        const epoch = ++this.epoch;
        this.cancelRequested = false;
        this.patch({
            busy: true,
            status: "pending",
            error: null,
            result: null,
            operation: null,
            consent: true,
            notice: "Fork pending. Cancellation or a lost acknowledgement does not prove the child is absent.",
        });
        try {
            if (!this.live(epoch)) return;
            const initial = await this.invoke("fork_start", {
                session: context.session,
                input: request,
                consent: true,
            });
            if (!this.live(epoch)) {
                if (
                    object(initial) &&
                    timelineNumber(initial.operation_id) &&
                    initial.operation_id > 0 &&
                    initial.running === true
                )
                    this.cancelOperation(initial.operation_id);
                return;
            }
            if (
                this.cancelRequested &&
                object(initial) &&
                timelineNumber(initial.operation_id) &&
                initial.operation_id > 0 &&
                initial.running === true
            )
                this.cancelOperation(initial.operation_id);
            await this.poll(initial, request, epoch);
        } catch (e) {
            if (this.live(epoch)) this.failure(e);
        }
    }
    private failure(e: unknown) {
        this.patch({
            busy: false,
            status: "uncertain",
            error: errorName(e),
            notice: "No automatic retry. Keep the original identity; check saved timelines or explicitly retry it in this session. Cancelled does not prove an earlier attempt never committed.",
        });
    }
    private async poll(first: unknown, request: ForkRequest, epoch: number) {
        let v = first,
            operation: number | null = null;
        for (let i = 0; i < 200; i++) {
            if (!this.live(epoch)) return;
            if (
                !exact(v, [
                    "version",
                    "operation_id",
                    "running",
                    "phase",
                    "error",
                    "result",
                ]) ||
                v.version !== 1 ||
                !timelineNumber(v.operation_id) ||
                v.operation_id === 0 ||
                typeof v.running !== "boolean" ||
                typeof v.phase !== "string" ||
                (v.error !== null && typeof v.error !== "string")
            )
                throw Error("Wire");
            if (operation !== null && v.operation_id !== operation)
                throw Error("Wire");
            operation = v.operation_id;
            this.patch({ operation });
            if (!this.live(epoch)) return;
            if (!v.running) {
                if (v.error) throw Error(String(v.error));
                if (
                    !exact(v.result, ["kind", "outcome"]) ||
                    v.result.kind !== "fork"
                )
                    throw Error("Wire");
                const result = outcome(v.result.outcome, request);
                this.patch({
                    busy: false,
                    status: "complete",
                    result,
                    error: null,
                    notice: "Saved timeline confirmed. Open it explicitly through the existing timeline picker; no downstream turn was replayed.",
                });
                if (this.live(epoch)) await this.refreshLibrary().catch(() => {});
                return;
            }
            await new Promise((r) => setTimeout(r, 25));
            if (!this.live(epoch)) return;
            v = await this.invoke("archive_status", { operationId: operation });
        }
        throw Error("Transport");
    }
    async cancel() {
        const operation = this.state.operation;
        if (this.disposed || !this.state.busy) return;
        this.cancelRequested = true;
        if (operation === null) return;
        try {
            await this.invoke("archive_cancel", { operationId: operation });
        } catch {
            /* Poll/lookup remains authoritative. */
        }
    }
    async lookup() {
        const request = this.state.request;
        if (
            this.disposed ||
            this.preparing ||
            this.state.busy ||
            !request ||
            !this.context?.persistent ||
            !sameScope(request.parent, this.context.scope)
        )
            return;
        const epoch = ++this.epoch;
        this.patch({ busy: true, error: null, result: null });
        try {
            if (!this.live(epoch)) return;
            const value = await this.invoke("fork_lookup", { input: request });
            if (!this.live(epoch)) return;
            if (
                !exact(value, ["version", "kind", "found", "outcome"]) ||
                value.version !== 1 ||
                value.kind !== "fork_lookup" ||
                typeof value.found !== "boolean" ||
                (!value.found && value.outcome !== null)
            )
                throw Error("Wire");
            const result = value.found ? outcome(value.outcome, request) : null;
            if (result?.created) throw Error("Wire");
            this.patch({
                busy: false,
                status: result ? "complete" : "not_found",
                result,
                notice: result
                    ? "Existing child verified at its current accepted head. Open it explicitly."
                    : "No matching saved child exists in this catalog snapshot. Recovery never creates it; absence is not a rollback guarantee.",
            });
            if (result && this.live(epoch)) await this.refreshLibrary().catch(() => {});
        } catch (e) {
            if (this.live(epoch)) this.failure(e);
        }
    }
    dispose() {
        if (this.state.busy && this.state.operation !== null)
            this.cancelOperation(this.state.operation);
        this.disposed = true;
        this.epoch++;
        this.context = null;
        this.patch({
            busy: false,
            operation: null,
            result: null,
            consent: false,
        });
        this.listeners.clear();
    }
}
