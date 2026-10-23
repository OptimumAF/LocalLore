import { checkedPage } from "./query-model";
import type { InspectionQuery } from "./query-model";
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
    model: string | null;
    runtime: string | null;
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
    "EvaluationModelBusy",
    "EvaluationModelUnavailable",
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
        ![
            "deterministic_fake_shared_host",
            "scripted_curated_shared_host",
            "native_curated_shared_host",
        ].includes(String(s.lane)) ||
        (s.lane === "native_curated_shared_host"
            ? !(
                  typeof s.model === "string" &&
                  /^[a-f0-9]{64}$/.test(s.model) &&
                  typeof s.runtime === "string" &&
                  /^[a-f0-9]{40}$/.test(s.runtime)
              )
            : s.model !== null || s.runtime !== null) ||
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

export interface CuratedCatalog {
    version: 1;
    cases: {
        id: string;
        turns: number;
        sources: { turn: string; scope: { story: string; branch: string } }[];
    }[];
    runs: {
        run_id: string;
        client_id: string;
        lane: "scripted" | "native";
        selection: string | null;
        batch: "one" | "all";
        created: number;
    }[];
    location: string;
    caps: unknown;
    approved_profile: unknown;
    model: Record<string, unknown>;
}
export interface CuratedSnapshot {
    version: 1;
    binding_sha256: string;
    resume_compatible: boolean;
    completed: boolean;
    checkpointed_stories: number;
    budget: Record<string, unknown>;
    report: EvaluationReport;
}
export interface CuratedStatus extends EvaluationStatus {
    source_binding: string;
    lane: "scripted" | "native";
    client_id: string;
    snapshot: CuratedSnapshot | null;
}
export interface CuratedEvidence {
    version: 1;
    run_token: string;
    run_id: string;
    evidence: {
        case_id: string;
        turn_id: string;
        binding_sha256: string;
        scope: { story: string; branch: string };
        revision: number;
        canonical_sha256: string;
        observer: InspectionQuery["observer"];
        page: unknown;
        receipt: unknown;
        outputs: {
            role: string;
            text: string;
            sha256: string;
            bytes: number;
        }[];
        role_metrics: unknown;
        missing: string[];
        exact_reconstruction: false;
        read_only: true;
        generation_grant: false;
    };
}
const hash = (v: unknown) => typeof v === "string" && /^[a-f0-9]{64}$/.test(v);
export function decodeCuratedCatalog(value: unknown): CuratedCatalog {
    const c = record(value);
    if (
        JSON.stringify(value).length > 65536 ||
        c.version !== 1 ||
        !Array.isArray(c.cases) ||
        c.cases.length !== 6 ||
        !Array.isArray(c.runs) ||
        c.runs.length > 32 ||
        !small(c.location, 4096) ||
        !c.model
    )
        throw Error("EvaluationInvalidReply");
    const ids = new Set();
    for (const v of c.cases) {
        const x = record(v);
        if (
            !small(x.id, 48) ||
            ids.has(x.id) ||
            x.turns !== 4 ||
            !Array.isArray(x.sources) ||
            x.sources.length !== 4
        )
            throw Error("EvaluationInvalidReply");
        ids.add(x.id);
        for (const item of x.sources) {
            const t = record(item),
                scope = record(t.scope);
            if (
                !small(t.turn, 128) ||
                !small(scope.story, 64) ||
                !small(scope.branch, 64)
            )
                throw Error("EvaluationInvalidReply");
        }
    }
    for (const v of c.runs) {
        const r = record(v);
        if (
            !guid(r.run_id) ||
            !guid(r.client_id) ||
            !["scripted", "native"].includes(String(r.lane)) ||
            !["one", "all"].includes(String(r.batch)) ||
            !(r.selection === null || ids.has(r.selection)) ||
            !integer(r.created)
        )
            throw Error("EvaluationInvalidReply");
    }
    return c as unknown as CuratedCatalog;
}
export function decodeCuratedStatus(value: unknown): CuratedStatus {
    const s = record(value);
    decodeEvaluationStatus(value);
    if (
        JSON.stringify(value).length > 2 * 1024 * 1024 ||
        !["scripted", "native"].includes(String(s.lane)) ||
        !guid(s.client_id) ||
        !hash(s.source_binding)
    )
        throw Error("EvaluationInvalidReply");
    if (s.snapshot !== null) {
        const p = record(s.snapshot);
        if (
            p.version !== 1 ||
            !hash(p.binding_sha256) ||
            typeof p.resume_compatible !== "boolean" ||
            typeof p.completed !== "boolean" ||
            !integer(p.checkpointed_stories, 6) ||
            !p.budget
        )
            throw Error("EvaluationInvalidReply");
        const report = decodeEvaluationReport(p.report);
        if (
            report.binding_sha256 !== p.binding_sha256 ||
            p.binding_sha256 !== s.source_binding ||
            report.completed !== p.completed ||
            report.cases.length !== p.checkpointed_stories ||
            report.lane !==
                (s.lane === "native"
                    ? "native_curated_shared_host"
                    : "scripted_curated_shared_host")
        )
            throw Error("EvaluationInvalidReply");
    }
    return s as unknown as CuratedStatus;
}
export function decodeCuratedEvidence(
    value: unknown,
    run: CuratedStatus,
    caseId: string,
    turn: EvaluationTurn,
    scope: { story: string; branch: string },
    observer: InspectionQuery["observer"],
    view: InspectionQuery["view"],
): CuratedEvidence {
    const v = record(value),
        e = record(v.evidence),
        b = run.snapshot?.binding_sha256;
    if (
        JSON.stringify(value).length > 256 * 1024 ||
        v.version !== 1 ||
        v.run_token !== run.run_token ||
        v.run_id !== run.run_id ||
        e.version !== 1 ||
        e.case_id !== caseId ||
        e.turn_id !== turn.id ||
        e.binding_sha256 !== b ||
        e.revision !== turn.revision ||
        e.canonical_sha256 !== turn.canonical_sha256 ||
        record(e.scope).story !== scope.story ||
        record(e.scope).branch !== scope.branch ||
        record(e.observer).kind !== observer.kind ||
        (observer.kind === "character" &&
            record(e.observer).id !== observer.id) ||
        e.exact_reconstruction !== false ||
        e.read_only !== true ||
        e.generation_grant !== false ||
        !Array.isArray(e.outputs) ||
        e.outputs.length > 3 ||
        !Array.isArray(e.missing) ||
        !e.missing.every((x) => small(x, 128))
    )
        throw Error("EvaluationInvalidReply");
    for (const value of e.outputs) {
        const raw = record(value);
        if (
            !["director", "narrator"].includes(String(raw.role)) ||
            !small(raw.text, 16384) ||
            !hash(raw.sha256) ||
            !integer(raw.bytes, 16384) ||
            new TextEncoder().encode(String(raw.text)).length !== raw.bytes
        )
            throw Error("EvaluationInvalidReply");
    }
    if (
        observer.kind !== "omniscient" &&
        (e.outputs.length !== 0 ||
            e.receipt !== null ||
            e.role_metrics !== null)
    )
        throw Error("EvaluationInvalidReply");
    const page = record(e.page);
    checkedPage(page, {
        version: 1,
        scope,
        expected_head: Number(page.head),
        at_revision: turn.revision,
        observer,
        view,
        cursor: null,
        limit: 32,
        search: "",
    });
    return v as unknown as CuratedEvidence;
}
