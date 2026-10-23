import type { Command, Scope } from "./model";
export type TraceQuery = Extract<Command, { op: "trace_read" }>;
export const traceStages = [
    "intent",
    "retrieval",
    "context",
    "director",
    "parsing",
    "validation",
    "repair",
    "accepted_candidate",
    "narration",
    "narration_validation",
    "atomic_commit",
    "publication",
    "memory_maintenance",
] as const;
export const traceOutcomes = [
    "not_run",
    "running",
    "accepted",
    "rejected",
    "committed",
    "failed",
    "cancelled",
    "stale",
    "truncated",
    "unknown",
] as const;
type Outcome = (typeof traceOutcomes)[number];
type Token = { value: number; basis: "measured" | "estimated" };
export interface TraceStage {
    stage: (typeof traceStages)[number];
    outcome: Outcome;
    started_us: number;
    duration_us: number;
    counts: {
        eligible_records: number;
        input_tokens: Token | null;
        output_tokens: Token | null;
        operations: number;
        repairs: number;
    };
    error: string | null;
}
export interface TraceAttempt {
    identity: {
        scope: Scope;
        base_revision: number;
        observer: string;
        turn: string;
        attempt: number;
    };
    provenance: Record<string, string | null>;
    outcome: Outcome;
    elapsed_us: number;
    truncated: boolean;
    stages: TraceStage[];
}
export interface TraceReply {
    scope: Scope;
    head: number;
    base_revision: number;
    observer: TraceQuery["observer"];
    configuration_scope: "window_host";
    capture: "metadata_only";
    full_capture: "unsupported";
    snapshot: {
        version: 1;
        status: "disabled" | "bounded_metadata_window";
        exact_reconstruction: false;
        attempts: TraceAttempt[];
    };
}
export interface TraceState {
    shown: boolean;
    busy: boolean;
    controlBusy: boolean;
    enabled: boolean | null;
    baseRevision: number;
    reply: TraceReply | null;
    selected: string | null;
    error: string | null;
    notice: string;
}
export const initialTrace = (): TraceState => ({
    shown: false,
    busy: false,
    controlBusy: false,
    enabled: null,
    baseRevision: 0,
    reply: null,
    selected: null,
    error: null,
    notice: "",
});
export const attemptKey = (a: TraceAttempt) =>
    `${a.identity.turn}:${a.identity.attempt}`;
const object = (v: unknown): v is Record<string, any> =>
    !!v && typeof v === "object" && !Array.isArray(v);
const keys = (v: Record<string, any>, expected: string[]) =>
    Object.keys(v).sort().join() === [...expected].sort().join();
const number = (v: unknown) => Number.isSafeInteger(v) && (v as number) >= 0;
const id = (v: unknown) =>
    typeof v === "string" && /^[A-Za-z0-9_-]{1,64}$/.test(v);
const scope = (v: unknown, expected: Scope) =>
    object(v) &&
    keys(v, ["story", "branch"]) &&
    v.story === expected.story &&
    v.branch === expected.branch;
const observer = (v: unknown, expected: TraceQuery["observer"]) =>
    object(v) &&
    v.kind === expected.kind &&
    (expected.kind === "character"
        ? keys(v, ["kind", "id"]) && v.id === expected.id
        : keys(v, ["kind"]));
const token = (v: unknown) =>
    v === null ||
    (object(v) &&
        keys(v, ["value", "basis"]) &&
        number(v.value) &&
        ["measured", "estimated"].includes(v.basis));
const provenanceKeys = [
    "model_sha256",
    "worker_sha256",
    "profile_sha256",
    "config_sha256",
    "prompt_sha256",
    "schema_sha256",
    "runtime_revision",
    "engine_revision",
    "profile_label",
    "prompt_label",
    "schema_label",
];
const errors = new Set(
    "malformed version scope rule agency narration storage unavailable busy deadline cancelled stale internal unknown retry_mismatch too_large author_ui_required clarification_required unknown_reference dead_actor location inventory resource ability knowledge provider corrupt_history unsupported".split(
        " ",
    ),
);
export function checkedTrace(
    value: unknown,
    query: TraceQuery,
    player: string,
): TraceReply {
    const fail = () => {
        throw new Error("Wire");
    };
    if (
        !object(value) ||
        !keys(value, [
            "scope",
            "head",
            "base_revision",
            "observer",
            "configuration_scope",
            "capture",
            "full_capture",
            "snapshot",
        ]) ||
        !scope(value.scope, query.scope) ||
        value.head !== query.expected_head ||
        value.base_revision !== query.base_revision ||
        !observer(value.observer, query.observer) ||
        value.configuration_scope !== "window_host" ||
        value.capture !== "metadata_only" ||
        value.full_capture !== "unsupported" ||
        new TextEncoder().encode(JSON.stringify(value)).length > 65_536
    )
        return fail();
    const s = value.snapshot;
    if (
        !object(s) ||
        !keys(s, ["version", "status", "exact_reconstruction", "attempts"]) ||
        s.version !== 1 ||
        !["disabled", "bounded_metadata_window"].includes(s.status) ||
        s.exact_reconstruction !== false ||
        !Array.isArray(s.attempts) ||
        s.attempts.length > 32 ||
        (s.status === "disabled" && s.attempts.length)
    )
        return fail();
    const actor =
        query.observer.kind === "character" ? query.observer.id : player;
    for (const a of s.attempts) {
        if (
            !object(a) ||
            !keys(a, [
                "identity",
                "provenance",
                "outcome",
                "elapsed_us",
                "truncated",
                "stages",
            ])
        )
            return fail();
        const i = a.identity,
            p = a.provenance;
        if (
            !object(i) ||
            !keys(i, [
                "scope",
                "base_revision",
                "observer",
                "turn",
                "attempt",
            ]) ||
            !scope(i.scope, query.scope) ||
            i.base_revision !== query.base_revision ||
            i.observer !== actor ||
            !id(i.observer) ||
            !id(i.turn) ||
            !number(i.attempt) ||
            i.attempt > 0xffffffff ||
            (query.turn != null && query.turn !== i.turn) ||
            (query.attempt != null && query.attempt !== i.attempt)
        )
            return fail();
        if (
            !object(p) ||
            !keys(p, provenanceKeys) ||
            !provenanceKeys.every(
                (k) =>
                    p[k] === null ||
                    (typeof p[k] === "string" &&
                        (k.endsWith("sha256")
                            ? /^[a-f0-9]{64}$/.test(p[k])
                            : k.endsWith("revision")
                              ? /^[a-f0-9]{40}$/.test(p[k])
                              : /^[A-Za-z0-9._-]{1,64}$/.test(p[k]))),
            )
        )
            return fail();
        if (
            !traceOutcomes.includes(a.outcome) ||
            !number(a.elapsed_us) ||
            typeof a.truncated !== "boolean" ||
            !Array.isArray(a.stages) ||
            a.stages.length > 24
        )
            return fail();
        for (const r of a.stages) {
            if (
                !object(r) ||
                !keys(r, [
                    "stage",
                    "outcome",
                    "started_us",
                    "duration_us",
                    "counts",
                    "error",
                ]) ||
                !traceStages.includes(r.stage) ||
                !traceOutcomes.includes(r.outcome) ||
                !number(r.started_us) ||
                !number(r.duration_us) ||
                (r.error !== null && !errors.has(r.error))
            )
                return fail();
            const c = r.counts;
            if (
                !object(c) ||
                !keys(c, [
                    "eligible_records",
                    "input_tokens",
                    "output_tokens",
                    "operations",
                    "repairs",
                ]) ||
                !number(c.eligible_records) ||
                !number(c.operations) ||
                !number(c.repairs) ||
                !token(c.input_tokens) ||
                !token(c.output_tokens)
            )
                return fail();
        }
    }
    return value as TraceReply;
}
