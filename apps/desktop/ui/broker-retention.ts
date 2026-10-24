// Presentation retention only. Native broker/Host/Store remain authoritative.
import {
    decodeMemoryOperation,
    type MemoryAction,
} from "./memory-maintenance-controller";
import {
    decodeStatus,
    decodeArchiveCompletion,
    decodeArchiveBinding,
    type ArchiveBinding,
    type ArchiveCommand,
} from "./archive-model";
import {
    decodeForkOutcome,
    decodeForkRequest,
    isForkError,
} from "./fork-controller";
import {
    checkedAuthorBrokerBinding,
    checkedAuthorBrokerOperation,
    authorBrokerOperationId,
    type AuthorBrokerBinding,
} from "./author-broker-binding";
export type BrokerSurface = "memory" | "fork" | "archive" | "author";
export interface BrokerIdentity {
    surface: BrokerSurface;
    session?: string;
    story?: string;
    branch?: string;
    head?: number;
    action: string;
    token?: string;
    child?: string;
    at?: number;
    archive?: ArchiveBinding;
    author?: AuthorBrokerBinding;
}
interface Retained {
    identity: BrokerIdentity;
    inFlight: boolean;
    operation: number | null;
    terminal: boolean;
    unknown: boolean;
    acknowledgedUnresolved: boolean;
    recoveringMemory: boolean;
    consumed: boolean;
}
function identity(value: BrokerIdentity): BrokerIdentity {
    if (
        !value ||
        typeof value !== "object" ||
        Object.keys(value).some(
            (k) =>
                ![
                    "surface",
                    "session",
                    "story",
                    "branch",
                    "head",
                    "action",
                    "token",
                    "child",
                    "at",
                    "archive",
                    "author",
                ].includes(k),
        ) ||
        !["memory", "fork", "archive", "author"].includes(value.surface)
    )
        throw Error("InvalidInput");
    if (value.surface === "author") {
        const author = checkedAuthorBrokerBinding(value.author);
        const expected = {
            action: author.action,
            session: author.session,
            story: author.input.parent.story,
            branch: author.input.parent.branch,
            head: author.input.expected_parent_revision,
            child: author.input.child_branch,
            at: author.input.fork_revision,
        };
        if (Object.hasOwn(value,"archive") || Object.hasOwn(value,"token") ||
            value.action !== author.action ||
            Object.entries(expected).some(([key,v]) => Object.hasOwn(value,key) && value[key as keyof BrokerIdentity] !== v))
            throw Error("InvalidInput");
        return Object.freeze({...value,author});
    }
    if (Object.hasOwn(value,"author")) throw Error("InvalidInput");
    for (const [key, v] of Object.entries(value)) {
        if (key === "archive") {
            if (value.surface !== "archive") throw Error("InvalidInput");
            decodeArchiveBinding(v);
        } else if (["head", "at"].includes(key)) {
            if (!Number.isSafeInteger(v) || Number(v) < 0)
                throw Error("InvalidInput");
        } else if (
            typeof v !== "string" ||
            v.length < 1 ||
            v.length > 128 ||
            !/^[A-Za-z0-9_-]+$/.test(v)
        )
            throw Error("InvalidInput");
    }
    if (typeof value.action !== "string") throw Error("InvalidInput");
    if (
        value.surface === "archive" &&
        ["archive_export", "archive_import"].includes(value.action) &&
        (!value.archive ||
            value.archive.token !== value.token ||
            value.archive.kind !==
                (value.action === "archive_export" ? "export" : "import"))
    )
        throw Error("InvalidInput");
    if (
        value.surface === "memory" &&
        (!value.session ||
            !value.story ||
            !value.branch ||
            value.head === undefined)
    )
        throw Error("InvalidInput");
    return {
        ...value,
        ...(value.archive
            ? { archive: decodeArchiveBinding(value.archive) }
            : {}),
    };
}
interface AuthorChecks {
    admission: boolean;
    validating: number;
    fault: boolean;
}
export class BrokerRetention {
    private retained: Retained | null = null;
    private listeners = new Set<() => void>();
    private authorChecks = new WeakMap<BrokerIdentity,AuthorChecks>();
    constructor(
        private awaitingConsumption: (surface: BrokerSurface) => boolean,
    ) {}
    get = () => this.retained;
    subscribe = (listener: () => void) => {
        this.listeners.add(listener);
        return () => {
            this.listeners.delete(listener);
        };
    };
    private patch(value: Partial<Retained>) {
        if (this.retained) this.retained = { ...this.retained, ...value };
        for (const f of this.listeners) f();
    }
    private blocked() {
        this.refreshConsumption();
        const r = this.retained;
        return (
            !!r &&
            ((r.identity.surface === "author" && r.inFlight) ||
            !r.acknowledgedUnresolved &&
            (r.inFlight || r.unknown || !r.terminal || !r.consumed))
        );
    }
    // Consumption is latched while the previous controller is idle. A later
    // pending notification belongs to the next action, not the old result.
    refreshConsumption = () => {
        const r = this.retained;
        if (
            r &&
            !r.consumed &&
            !r.inFlight &&
            !r.unknown &&
            r.terminal &&
            !this.awaitingConsumption(r.identity.surface)
        )
            this.patch({ consumed: true });
    };
    async start(
        value: BrokerIdentity,
        work: () => Promise<unknown>,
    ): Promise<unknown> {
        const selected = identity(value);
        if (this.blocked()) throw Error("ArchiveBusy");
        if (selected.surface === "author") return this.startAuthor(selected,work);
        this.retained = {
            identity: selected,
            inFlight: true,
            operation: null,
            terminal: false,
            unknown: false,
            acknowledgedUnresolved: false,
            recoveringMemory: false,
            consumed: false,
        };
        this.patch({});
        try {
            const result = await work();
            this.record(result, true);
            this.patch({
                inFlight: false,
                ...(this.retained?.operation === null ? { unknown: true } : {}),
            });
            this.refreshConsumption();
            return result;
        } catch (error) {
            const name = error instanceof Error ? error.message : String(error);
            this.patch({
                inFlight: false,
                unknown: name !== "ArchiveBusy",
                terminal: name === "ArchiveBusy",
            });
            throw error;
        }
    }
    observe(value: unknown) {
        this.record(value, false);
    }
    private sameAuthor(owner:Retained) {
        return this.retained?.identity === owner.identity && owner.identity.surface === "author";
    }
    private async startAuthor(selected:BrokerIdentity,work:()=>Promise<unknown>) {
        const owner:Retained={identity:selected,inFlight:true,operation:null,terminal:false,unknown:false,acknowledgedUnresolved:false,recoveringMemory:false,consumed:false};
        const checks:AuthorChecks={admission:true,validating:0,fault:false};
        this.authorChecks.set(selected,checks);
        this.retained=owner;
        this.patch({});
        try {
            const result=await work();
            if (this.sameAuthor(owner)) await this.recordAuthor(result,true,owner);
            return result;
        } catch(error) {
            if (this.sameAuthor(owner)) {
                const busy=error instanceof Error?error.message === "ArchiveBusy":error === "ArchiveBusy";
                if (!busy) checks.fault=true;
                this.patch({unknown:checks.fault,terminal:busy && !checks.fault,consumed:false});
            }
            throw error;
        } finally {
            checks.admission=false;
            if (this.sameAuthor(owner)) {
                this.patch({inFlight:checks.validating>0});
                this.refreshConsumption();
            }
        }
    }
    async observeAuthor(value:unknown):Promise<void> {
        const owner=this.retained;
        if (owner?.identity.surface === "author") await this.recordAuthor(value,false,owner);
    }
    private async recordAuthor(value:unknown,admission:boolean,owner:Retained) {
        if (!this.sameAuthor(owner)) return;
        const current=this.retained!;
        if (current.operation === null && !admission) return;
        const incoming=authorBrokerOperationId(value);
        if (current.operation !== null && incoming !== undefined && incoming !== current.operation) return;
        const checks=this.authorChecks.get(owner.identity)!;
        checks.validating++;
        this.patch({inFlight:true,consumed:false});
        try {
            const status=await checkedAuthorBrokerOperation(value,owner.identity.author!,current.operation ?? undefined);
            if (!this.sameAuthor(owner)) return;
            // Faults are sticky for this reservation; a panel reset or later partial
            // update does not prove the original private completion was valid.
            this.patch({operation:status.operation_id,terminal:!status.running,unknown:checks.fault});
        } catch {
            checks.fault=true;
            if (this.sameAuthor(owner)) this.patch({unknown:true,consumed:false});
        } finally {
            checks.validating--;
            if (this.sameAuthor(owner)) {
                this.patch({inFlight:checks.admission || checks.validating>0});
                this.refreshConsumption();
            }
        }
    }
    private record(value: unknown, admission: boolean) {
        const r = this.retained;
        if (!r) return;
        if (r.identity.surface === "author") {
            if (r.operation === null && !admission) return;
            const incoming=authorBrokerOperationId(value);
            if (r.operation !== null && incoming !== undefined && incoming !== r.operation) return;
            // Full private preview validation is asynchronous. Call observeAuthor.
            this.patch({unknown:true,consumed:false});
            return;
        }
        // External status/cancel replies can only update an already known ID.
        // Only this reservation's awaited admission reply may establish it.
        if (r.operation === null && !admission) return;
        if (!value || typeof value !== "object") {
            this.patch({ unknown: true });
            return;
        }
        const incoming = value as Record<string, unknown>;
        // A late status/cancel reply belongs to its original operation. Exclude
        // a known different ID before decoding against the current identity.
        if (
            r.operation !== null &&
            Number.isSafeInteger(incoming.operation_id) &&
            Number(incoming.operation_id) > 0 &&
            incoming.operation_id !== r.operation
        )
            return;
        if (r.identity.surface === "memory") {
            try {
                decodeMemoryOperation(
                    value,
                    {
                        session: r.identity.session!,
                        scope: {
                            story: r.identity.story!,
                            branch: r.identity.branch!,
                        },
                        expected_head: r.identity.head!,
                    },
                    r.recoveringMemory
                        ? "status"
                        : (r.identity.action as MemoryAction),
                    r.operation ?? undefined,
                );
            } catch {
                this.patch({ unknown: true });
                return;
            }
        }
        if (r.identity.surface === "archive" || r.identity.surface === "fork") {
            try {
                if (r.identity.surface === "archive") {
                    if (
                        ![
                            "archive_export_preview",
                            "archive_import_preview",
                            "archive_export",
                            "archive_import",
                        ].includes(r.identity.action)
                    )
                        throw Error("Wire");
                    const status = decodeStatus(value);
                    if (!status.running && !status.error)
                        decodeArchiveCompletion(
                            status,
                            r.identity.action as ArchiveCommand,
                            r.identity.archive,
                        );
                } else if (
                    incoming.error !== null &&
                    !isForkError(incoming.error)
                ) {
                    throw Error("Wire");
                } else if (
                    incoming.running === false &&
                    incoming.error === null
                ) {
                    const result = incoming.result as Record<
                        string,
                        unknown
                    > | null;
                    if (
                        !result ||
                        Object.keys(result).length !== 2 ||
                        result.kind !== "fork" ||
                        !Object.hasOwn(result, "outcome")
                    )
                        throw Error("Wire");
                    decodeForkOutcome(
                        result.outcome,
                        decodeForkRequest({
                            parent: {
                                story: r.identity.story,
                                branch: r.identity.branch,
                            },
                            child_branch: r.identity.child,
                            expected_parent_revision: r.identity.head,
                            at_revision: r.identity.at,
                        }),
                    );
                }
            } catch {
                this.patch({ unknown: true });
                return;
            }
        }
        const v = value as Record<string, unknown>;
        if (
            Object.keys(v).length !== 6 ||
            ![
                "version",
                "operation_id",
                "running",
                "phase",
                "error",
                "result",
            ].every((k) => Object.hasOwn(v, k)) ||
            v.version !== 1 ||
            !Number.isSafeInteger(v.operation_id) ||
            Number(v.operation_id) < 1 ||
            typeof v.running !== "boolean" ||
            !(
                v.error === null ||
                (typeof v.error === "string" && v.error.length <= 64)
            )
        ) {
            this.patch({ unknown: true });
            return;
        }
        if (r.operation !== null && r.operation !== v.operation_id) return;
        if (
            v.running
                ? ![
                      "starting",
                      "memory_maintenance",
                      "forking",
                      "capturing",
                      "choosing_input",
                      "validating",
                      "choosing_destination",
                      "writing",
                      "staging",
                      "importing",
                  ].includes(String(v.phase)) ||
                  v.result !== null ||
                  v.error !== null
                : v.phase === "completed"
                  ? !v.result ||
                    typeof v.result !== "object" ||
                    v.error !== null
                  : v.phase !== "error" ||
                    typeof v.error !== "string" ||
                    v.result !== null
        ) {
            this.patch({ unknown: true });
            return;
        }
        let unresolved = false;
        if (r.recoveringMemory) {
            const result = v.result as Record<string, unknown> | null;
            const scope = result?.scope as Record<string, unknown> | undefined;
            unresolved =
                v.running ||
                v.phase !== "completed" ||
                result?.kind !== "memory_maintenance" ||
                result?.action !== "status" ||
                result?.session !== r.identity.session ||
                scope?.story !== r.identity.story ||
                scope?.branch !== r.identity.branch ||
                result?.expected_head !== r.identity.head;
        }
        this.patch({
            operation: Number(v.operation_id),
            terminal: !v.running,
            unknown: unresolved,
        });
        this.refreshConsumption();
    }
    async recoverMemory(value: BrokerIdentity, work: () => Promise<unknown>) {
        const selected = identity(value),
            r = this.retained;
        if (
            !r ||
            r.identity.surface !== "memory" ||
            selected.surface !== "memory" ||
            selected.action !== "status" ||
            r.inFlight ||
            !["session", "story", "branch", "head"].every(
                (k) =>
                    selected[k as keyof BrokerIdentity] ===
                    r.identity[k as keyof BrokerIdentity],
            )
        )
            throw Error("ArchiveBusy");
        const oldOperation = r.operation;
        this.patch({ inFlight: true, recoveringMemory: true, consumed: false });
        try {
            const result = await work();
            // A successful explicit passive read has a new broker operation.
            // Exact original selection is required; no different-scope recovery.
            this.patch({ operation: null });
            this.record(result, true);
            if (this.retained?.operation === null)
                this.patch({ operation: oldOperation, unknown: true });
            this.patch({ inFlight: false });
            return result;
        } catch (error) {
            this.patch({ inFlight: false, unknown: true });
            throw error;
        }
    }
    acknowledgeUnresolved(consent: boolean) {
        if (!consent || !this.retained?.unknown || this.retained.inFlight)
            return false;
        this.patch({ acknowledgedUnresolved: true });
        return true;
    }
}
