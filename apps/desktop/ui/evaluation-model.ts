export interface EvaluationStatus {
    version: 1;
    run_token: string;
    run_id: string;
    operation_id: number | null;
    running: boolean;
    phase: string;
    error: string | null;
    completed_cases: number;
    completed: boolean;
}
export interface EvaluationCheck {
    id: string;
    turn: string | null;
    stage: string;
    status: "passed" | "failed" | "unsupported";
    expected: unknown;
    actual: unknown;
}
export interface EvaluationTurn {
    id: string;
    intent: unknown;
    phase: unknown;
    error: unknown;
    revision: number;
    canonical_sha256: string;
    narration: string | null;
    fallback: boolean | null;
    repairs: number | null;
}
export interface EvaluationCase {
    id: string;
    status: "passed" | "failed" | "unsupported";
    checks: EvaluationCheck[];
    turns: EvaluationTurn[];
    provider_requests: unknown[];
    unsupported: string | null;
}
export interface EvaluationReport {
    version: 1;
    lane: string;
    synthetic: true;
    quality_accepted: false;
    completed: boolean;
    cancelled: boolean;
    binding_sha256: string;
    cases: EvaluationCase[];
    model: null;
    runtime: null;
    hardware: null;
    android_parity: string;
    unsupported_lanes: string[];
    provenance: unknown;
    [key: string]: unknown;
}
export interface EvaluationCatalog {
    version: 1;
    cases: { id: string; unsupported: string | null }[];
    runs: {
        run_id: string;
        selection: string | null;
        created: number;
        phase: string;
    }[];
    location: string;
    retention: string;
    caps: unknown;
}
export const evaluationErrors = new Set([
    "Closed",
    "EvaluationBusy",
    "EvaluationBudget",
    "EvaluationRunLimit",
    "EvaluationTokenLimit",
    "EvaluationSourceMismatch",
    "EvaluationIntegrity",
    "EvaluationIo",
    "EvaluationInternal",
    "UnsafeEvaluationPath",
    "UnknownEvaluationRun",
    "UnknownEvaluationCase",
    "EvaluationNotReady",
    "InvalidEvaluationInput",
    "StaleEvaluationOperation",
    "EvaluationInvalidReply",
]);
const record = (v: unknown): Record<string, unknown> => {
    if (!v || typeof v !== "object" || Array.isArray(v))
        throw Error("EvaluationInvalidReply");
    return v as Record<string, unknown>;
};
const small = (v: unknown, max = 128) =>
    typeof v === "string" && v.length <= max;
const integer = (v: unknown, max = Number.MAX_SAFE_INTEGER) =>
    Number.isSafeInteger(v) && Number(v) >= 0 && Number(v) <= max;
const guid = (v: unknown) =>
    typeof v === "string" &&
    /^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$/.test(v);
const status = (v: unknown) =>
    ["passed", "failed", "unsupported"].includes(String(v));
export function decodeEvaluationStatus(v: unknown): EvaluationStatus {
    const s = record(v);
    if (
        s.version !== 1 ||
        !guid(s.run_token) ||
        !guid(s.run_id) ||
        typeof s.running !== "boolean" ||
        typeof s.completed !== "boolean" ||
        !integer(s.completed_cases, 32) ||
        !(
            s.operation_id === null ||
            (integer(s.operation_id) && Number(s.operation_id) > 0)
        ) ||
        ![
            "retained",
            "starting",
            "validating_checkpoints",
            "running",
            "stopping_at_boundary",
            "error",
            "paused",
            "completed",
        ].includes(String(s.phase)) ||
        s.running !== (s.operation_id !== null) ||
        !(s.error === null || evaluationErrors.has(String(s.error)))
    )
        throw Error("EvaluationInvalidReply");
    return s as unknown as EvaluationStatus;
}
export function decodeEvaluationCatalog(v: unknown): EvaluationCatalog {
    const s = record(v);
    if (
        s.version !== 1 ||
        !Array.isArray(s.cases) ||
        s.cases.length > 32 ||
        !Array.isArray(s.runs) ||
        s.runs.length > 32 ||
        !small(s.location, 4096) ||
        !small(s.retention, 1024)
    )
        throw Error("EvaluationInvalidReply");
    const ids = new Set<string>();
    for (const x of s.cases) {
        const c = record(x);
        if (
            !small(c.id, 48) ||
            ids.has(String(c.id)) ||
            !(c.unsupported === null || small(c.unsupported, 2048))
        )
            throw Error("EvaluationInvalidReply");
        ids.add(String(c.id));
    }
    for (const x of s.runs) {
        const r = record(x);
        if (
            !guid(r.run_id) ||
            !integer(r.created) ||
            !(r.selection === null || ids.has(String(r.selection))) ||
            !small(r.phase, 48)
        )
            throw Error("EvaluationInvalidReply");
    }
    return s as unknown as EvaluationCatalog;
}
export function decodeEvaluationReport(v: unknown): EvaluationReport {
    const s = record(v);
    if (
        JSON.stringify(v).length > 2 * 1024 * 1024 ||
        s.version !== 1 ||
        s.synthetic !== true ||
        s.quality_accepted !== false ||
        s.lane !== "deterministic_fake_shared_host" ||
        s.model !== null ||
        s.runtime !== null ||
        s.hardware !== null ||
        s.android_parity !== "not_run" ||
        typeof s.completed !== "boolean" ||
        typeof s.cancelled !== "boolean" ||
        !(
            typeof s.binding_sha256 === "string" &&
            /^[a-f0-9]{64}$/.test(s.binding_sha256)
        ) ||
        !Array.isArray(s.cases) ||
        s.cases.length > 32 ||
        !Array.isArray(s.unsupported_lanes) ||
        s.unsupported_lanes.length > 16 ||
        !s.unsupported_lanes.every((x) => small(x, 128))
    )
        throw Error("EvaluationInvalidReply");
    const ids = new Set();
    for (const value of s.cases) {
        const c = record(value);
        if (
            !small(c.id, 48) ||
            ids.has(c.id) ||
            !status(c.status) ||
            !Array.isArray(c.checks) ||
            c.checks.length > 512 ||
            !Array.isArray(c.turns) ||
            c.turns.length > 256 ||
            !Array.isArray(c.provider_requests) ||
            c.provider_requests.length > 128 ||
            !(c.unsupported === null || small(c.unsupported, 4096))
        )
            throw Error("EvaluationInvalidReply");
        ids.add(c.id);
        for (const value of c.checks) {
            const x = record(value);
            if (
                !small(x.id, 128) ||
                !small(x.stage, 48) ||
                !status(x.status) ||
                !Object.hasOwn(x, "expected") ||
                !Object.hasOwn(x, "actual") ||
                !(x.turn === null || small(x.turn, 128))
            )
                throw Error("EvaluationInvalidReply");
        }
        for (const value of c.turns) {
            const x = record(value);
            if (
                !small(x.id, 128) ||
                !integer(x.revision) ||
                !(
                    typeof x.canonical_sha256 === "string" &&
                    /^[a-f0-9]{64}$/.test(x.canonical_sha256)
                ) ||
                !Object.hasOwn(x, "intent") ||
                !Object.hasOwn(x, "phase") ||
                !Object.hasOwn(x, "error") ||
                !(x.narration === null || small(x.narration, 16384))
            )
                throw Error("EvaluationInvalidReply");
        }
    }
    return s as unknown as EvaluationReport;
}
