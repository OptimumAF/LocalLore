// Read-only transport boundary. Rust owns source validation, eligibility and
// canonical state. Parsed objects cannot reveal duplicate keys in raw JSON.
import { checkedPageV2 } from "./v2-view-model";
import type {
    ObserverV2,
    ScopeV2,
    ViewV2,
    InspectionPageV2,
} from "./v2-view-model";
export type { ObserverV2, ScopeV2, ViewV2 } from "./v2-view-model";

export type Json =
    null | boolean | number | string | Json[] | { [key: string]: Json };
export type RowId = { turn: string; arm: "left" | "right" };
export type ContextPolicy =
    "state_recent_transcript_v1" | "state_relevant_memory_v1";
export type ReaderError =
    (typeof readerErrors)[number] | "ComparisonReaderWire";
export const readerErrors = [
    "InvalidEvaluationInput",
    "Forbidden",
    "Closed",
    "EvaluationBusy",
    "UnknownEvaluationRun",
    "EvaluationTokenLimit",
    "PickerUnavailable",
    "Unsupported",
    "EvaluationSourceMismatch",
    "EvaluationIntegrity",
    "UnsafeEvaluationPath",
    "EvaluationBudget",
    "EvaluationIo",
    "EvaluationInternal",
] as const;
export type ReaderStatus = {
    version: 1;
    kind: "comparison_reader";
    client_id: string;
    operation_id: number | null;
    phase:
        | "choosing"
        | "opening"
        | "reading"
        | "ready"
        | "cancelled"
        | "closing"
        | "closed"
        | "failed";
    running: boolean;
    run_token: string | null;
    binding: string | null;
    error: (typeof readerErrors)[number] | null;
    read_only: true;
    execution_available: false;
};
export type RowAvailability = {
    row: RowId;
    source: {
        status: "available";
        scope: ScopeV2;
        before_head: number;
        after_head: number;
        input_semantic_sha256: string;
    };
    capture_available: boolean;
    receipt_available: boolean;
    recording_available: boolean;
    unavailable: string[];
};
export type ReaderSource = {
    binding: string;
    protocol_version: 2 | 3;
    rows: RowAvailability[];
    read_only: true;
    execution_available: false;
};
export type ForwardedEstimate = {
    version: 1;
    prompt_bytes: number;
    schema_bytes: number;
    repair_extra_bytes: number;
    actual_prompt_schema_estimated_tokens: number;
    admission_prompt_schema_estimated_tokens: number;
    output_tokens: number;
    template_reserve_tokens: number;
    estimated_total_tokens: number;
};
export type ComparisonTurnV2 = {
    turn: string;
    scene: number;
    arm: "left" | "right";
    policy: ContextPolicy;
    phase: string;
    error: string | null;
    expected: string;
    passed: boolean;
    failures: string[];
    quality_flags: string[];
    roles: number;
    roles_known: boolean;
    recovered_without_checkpoint: boolean;
    admission: number | null;
    elapsed_ms: number;
    first_final_response_ms: number | null;
    commit_elapsed_ms: number | null;
    input_semantic_sha256: string;
    output_semantic_sha256: string;
    mechanical_sha256: string;
    policy_matches: boolean;
    context_evidence_available: boolean;
    context_requirement: string;
    privacy_passed: boolean;
    fallback: boolean | null;
    capture_sha256: string | null;
    recording_sha256: string | null;
    raw_sha256: string[];
    role_metrics: Json;
    trace: Json;
    actual_receipt_sha256: string | null;
    source_fallback_reason: string | null;
    compiler_fallback_reason: string | null;
    narration: string | null;
    repairs: number | null;
    stages: Json[];
    mandatory_sha256: string | null;
    optional_detail_selected: boolean | null;
    director_private_target_present: boolean | null;
    selected_context_bytes: number | null;
    estimated_context_tokens: number | null;
    forwarded_director_estimates?: ForwardedEstimate[];
};
export type ComparisonArmDescriptorV3 = {
    arm: "literal_player_v1" | "relevant_memory_v1";
    prompt_version: string;
    narration_policy: "grounded-prose-v2.2";
    director_schema_id: "locallore-director-literal-v1" | "locallore-director-v2";
    context_policy: "state_relevant_memory_v1" | null;
    compiler_version: 2 | null;
    context_version: 2 | null;
    literal_source_version: 1 | null;
    literal_render_version: 1 | null;
    literal_schema_version: 1 | null;
    literal_packing_version: 1 | null;
    forwarded_budget_version: 1;
};
export type ConstructionEvidenceStatusV3 = "validated_literal" | "validated_relevant" |
    "not_applicable_guard" | "not_applicable_dependency" | "unavailable";
export type ComparisonTurnV3 = Omit<ComparisonTurnV2, "policy" | "policy_matches" | "forwarded_director_estimates"> & {
    construction: ComparisonArmDescriptorV3;
    construction_matches: boolean;
    construction_evidence_status: ConstructionEvidenceStatusV3;
    literal_source_units: number | null;
    literal_selected_start: number | null;
    literal_selected_units: number | null;
    forwarded_director_estimates: ForwardedEstimate[] | null;
};
export type ComparisonTurn = ComparisonTurnV2 | ComparisonTurnV3;
export type ComparisonProfile = {
    id: string;
    model_sha256: string;
    runtime_revision: string;
    template_sha256: string;
    worker_sha256: string;
    profile_manifest_sha256: string;
    context_tokens: number;
    director_tokens: number;
    narrator_tokens: number;
    deadline_ms: number;
    repair_limit: number;
};
export type ComparisonReportV2 = {
    version: 2;
    kind: "paired_snapshots" | "continuous_rollout";
    lane: string;
    source_matches: boolean;
    completed: boolean;
    completed_scenes: number;
    turns: ComparisonTurnV2[];
    human_reviewed: number;
    human_rubric: string;
    quality_accepted: boolean;
    physical_setups: number;
    physical_setup_ms: number | null;
    native_load: Json;
    left_charged_ms: number;
    right_charged_ms: number;
    left_reserved_roles: number;
    right_reserved_roles: number;
    first_semantic_divergence: string | null;
    first_mechanical_divergence: string | null;
    same_input_pairs: number;
    unavailable: string[];
    profile: ComparisonProfile;
    suite_sha256: string;
    source_sha256: string;
    reference_sha256: string | null;
    limitations: string[];
};
export type ComparisonReportV3 = Omit<ComparisonReportV2, "version" | "turns"> & {
    version: 3;
    arms: ComparisonArmDescriptorV3[];
    turns: ComparisonTurnV3[];
};
export type ComparisonReport = ComparisonReportV2 | ComparisonReportV3;
export type ReaderSummary = ReaderSource & {
    version: 1;
    report: ComparisonReport;
    unavailable: string[];
};
export type EvidenceRequest =
    | {
          kind: "query";
          edge: "before" | "after";
          observer: ObserverV2;
          view: ViewV2;
      }
    | { kind: "receipt" | "capture" | "outputs"; observer: ObserverV2 };
export type EvidenceBody =
    | { kind: "query"; page: InspectionPageV2 }
    | { kind: "receipt"; receipt: Json }
    | { kind: "capture"; capture: Json }
    | {
          kind: "outputs";
          outputs: {
              role: "director" | "narrator";
              bytes: number;
              sha256: string;
              text: string;
          }[];
      }
    | {
          kind: "missing";
          reason:
              | "capture_unavailable"
              | "recording_unavailable"
              | "no_accepted_receipt";
      };
export type ReaderEvidence = {
    version: 1;
    binding: string;
    row: RowId;
    scope: ScopeV2;
    before_head: number;
    after_head: number;
    observer: ObserverV2;
    edge: "before" | "after" | null;
    read_only: true;
    generation_grant: false;
    body: EvidenceBody;
};

const encoder = new TextEncoder();
type Obj = Record<string, unknown>;
function wire(ok: unknown): asserts ok {
    if (!ok) throw new Error("ComparisonReaderWire");
}
function object(value: unknown): Obj {
    wire(value !== null && typeof value === "object" && !Array.isArray(value));
    return value as Obj;
}
function exact(
    value: unknown,
    required: readonly string[],
    optional: readonly string[] = [],
): Obj {
    const o = object(value),
        keys = Object.keys(o);
    wire(
        required.every((k) => Object.hasOwn(o, k)) &&
            keys.every((k) => required.includes(k) || optional.includes(k)),
    );
    return o;
}
function text(v: unknown): string {
    wire(typeof v === "string");
    return v;
}
function integer(v: unknown, min = 0, max = Number.MAX_SAFE_INTEGER): number {
    wire(
        typeof v === "number" &&
            Number.isSafeInteger(v) &&
            v >= min &&
            v <= max,
    );
    return v;
}
function bool(v: unknown): void {
    wire(typeof v === "boolean");
}
function choices(v: unknown, options: readonly string[]): string {
    const s = text(v);
    wire(options.includes(s));
    return s;
}
function nullable(v: unknown, check: (v: unknown) => unknown): void {
    if (v !== null) check(v);
}
function list(
    v: unknown,
    check: (v: unknown) => unknown,
    max = Number.MAX_SAFE_INTEGER,
): unknown[] {
    wire(Array.isArray(v) && v.length <= max);
    v.forEach(check);
    return v;
}
function strings(v: unknown): void {
    list(v, text);
}
function id(v: unknown): string {
    const s = text(v);
    wire(/^[a-zA-Z0-9_-]{1,64}$/.test(s));
    return s;
}
function guid(v: unknown): string {
    const s = text(v);
    wire(/^[a-fA-F0-9]{8}(?:-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12}$/.test(s));
    return s;
}
function hash(v: unknown): string {
    const s = text(v);
    wire(/^[a-f0-9]{64}$/.test(s));
    return s;
}
function scope(v: unknown): ScopeV2 {
    const o = exact(v, ["story", "branch"]);
    id(o.story);
    id(o.branch);
    return o as ScopeV2;
}
function sameScope(a: ScopeV2, b: ScopeV2): boolean {
    return a.story === b.story && a.branch === b.branch;
}
export function sameReaderObserver(a: ObserverV2, b: ObserverV2): boolean {
    return (
        a.kind === b.kind &&
        (a.kind !== "character" || (b.kind === "character" && a.id === b.id))
    );
}
function observer(v: unknown): ObserverV2 {
    const o = object(v);
    if (o.kind === "character") {
        exact(o, ["kind", "id"]);
        id(o.id);
    } else {
        exact(o, ["kind"]);
        choices(o.kind, ["player", "omniscient"]);
    }
    return o as ObserverV2;
}
function rowId(v: unknown): RowId {
    const o = exact(v, ["turn", "arm"]);
    id(o.turn);
    choices(o.arm, ["left", "right"]);
    return o as RowId;
}
export function readerRowKey(v: RowId): string {
    return `${v.arm}:${v.turn}`;
}
export function sameReaderSource(a: ReaderSource, b: ReaderSource): boolean {
    return (
        a.binding === b.binding &&
        a.protocol_version === b.protocol_version &&
        a.rows.length === b.rows.length &&
        a.rows.every((row, index) => {
            const other = b.rows[index],
                x = row.source,
                y = other.source;
            return (
                readerRowKey(row.row) === readerRowKey(other.row) &&
                sameScope(x.scope, y.scope) &&
                x.before_head === y.before_head &&
                x.after_head === y.after_head &&
                x.input_semantic_sha256 === y.input_semantic_sha256 &&
                row.capture_available === other.capture_available &&
                row.receipt_available === other.receipt_available &&
                row.recording_available === other.recording_available &&
                row.unavailable.length === other.unavailable.length &&
                row.unavailable.every((v) => other.unavailable.includes(v))
            );
        })
    );
}
function utf8(s: string): number {
    for (let i = 0; i < s.length; i++) {
        const c = s.charCodeAt(i);
        if (c >= 0xd800 && c <= 0xdbff) {
            const n = s.charCodeAt(++i);
            wire(n >= 0xdc00 && n <= 0xdfff);
        } else wire(c < 0xdc00 || c > 0xdfff);
    }
    return encoder.encode(s).length;
}
// Clone with data descriptors only, charging serialized UTF-8 as we walk. No
// getter, toJSON, prototype assignment, cycles, sparse arrays or lossy numbers.
function detached(input: unknown, maximum: number): unknown {
    let charged = 0;
    const active = new Set<unknown>();
    const charge = (n: number) => {
        charged += n;
        wire(charged <= maximum);
    };
    const visit = (v: unknown, depth: number): unknown => {
        wire(depth <= 64);
        if (typeof v === "string") {
            utf8(v);
            charge(encoder.encode(JSON.stringify(v)).length);
            return v;
        }
        if (typeof v === "number") {
            wire(Number.isFinite(v) && Math.abs(v) <= Number.MAX_SAFE_INTEGER);
            charge(String(v).length);
            return v;
        }
        if (v === null || typeof v === "boolean") {
            charge(v === false ? 5 : 4);
            return v;
        }
        wire(typeof v === "object" && !active.has(v));
        const array = Array.isArray(v),
            proto = Object.getPrototypeOf(v);
        wire(
            array
                ? proto === Array.prototype
                : proto === Object.prototype || proto === null,
        );
        const keys = Reflect.ownKeys(v);
        wire(keys.every((k) => typeof k === "string"));
        active.add(v);
        charge(2);
        let result: unknown;
        if (array) {
            wire(keys.length === v.length + 1);
            const a: unknown[] = [];
            for (let i = 0; i < v.length; i++) {
                const d = Object.getOwnPropertyDescriptor(v, String(i));
                wire(d && "value" in d && d.enumerable);
                if (i) charge(1);
                a.push(visit(d.value, depth + 1));
            }
            result = a;
        } else {
            const o = Object.create(null) as Obj;
            (keys as string[]).forEach((key, i) => {
                const d = Object.getOwnPropertyDescriptor(v, key);
                wire(d && "value" in d && d.enumerable);
                utf8(key);
                charge(
                    encoder.encode(JSON.stringify(key)).length +
                        1 +
                        (i ? 1 : 0),
                );
                Object.defineProperty(o, key, {
                    value: visit(d.value, depth + 1),
                    enumerable: true,
                });
            });
            result = o;
        }
        active.delete(v);
        return result;
    };
    const result = visit(input, 0);
    wire(encoder.encode(JSON.stringify(result)).length <= maximum);
    return result;
}
function encoded(v: unknown): number {
    return encoder.encode(JSON.stringify(v)).length;
}
function wrapper(
    v: unknown,
    key: string,
    token: string,
    maximum: number,
    overhead = 4096,
): unknown {
    const o = exact(detached(v, maximum + overhead), [
        "version",
        "kind",
        "run_token",
        key,
    ]);
    wire(
        o.version === 1 &&
            o.kind === "comparison_reader" &&
            guid(o.run_token) === guid(token),
    );
    wire(encoded(o[key]) <= maximum);
    return o[key];
}
function readonly(o: Obj): void {
    wire(o.read_only === true && o.execution_available === false);
}

export function checkedReaderStatus(
    v: unknown,
    clientId: string,
): ReaderStatus {
    const o = exact(detached(v, 4096), [
        "version",
        "kind",
        "client_id",
        "operation_id",
        "phase",
        "running",
        "run_token",
        "binding",
        "error",
        "read_only",
        "execution_available",
    ]);
    wire(
        o.version === 1 &&
            o.kind === "comparison_reader" &&
            guid(o.client_id) === guid(clientId),
    );
    readonly(o);
    nullable(o.operation_id, (v) => integer(v, 1));
    nullable(o.run_token, guid);
    nullable(o.binding, hash);
    nullable(o.error, (v) => choices(v, readerErrors));
    bool(o.running);
    choices(o.phase, [
        "choosing",
        "opening",
        "reading",
        "ready",
        "cancelled",
        "closing",
        "closed",
        "failed",
    ]);
    wire((o.run_token === null) === (o.binding === null));
    if (o.running) wire(o.operation_id !== null);
    if (["choosing", "opening", "reading"].includes(o.phase as string))
        wire(o.running === true);
    if (["ready", "cancelled", "closed", "failed"].includes(o.phase as string))
        wire(o.running === false);
    if (o.phase === "ready" || o.phase === "reading")
        wire(o.run_token !== null && o.error === null);
    else if (o.phase !== "closing") wire(o.run_token === null);
    wire(o.phase === "failed" ? o.error !== null : o.error === null);
    return o as ReaderStatus;
}
const unavailableRows = [
    "capture_unavailable",
    "recording_unavailable",
    "no_accepted_receipt",
];
function rows(v: unknown): RowAvailability[] {
    const values = list(
        v,
        (value) => {
            const o = exact(value, [
                "row",
                "source",
                "capture_available",
                "receipt_available",
                "recording_available",
                "unavailable",
            ]);
            rowId(o.row);
            const s = exact(o.source, [
                "status",
                "scope",
                "before_head",
                "after_head",
                "input_semantic_sha256",
            ]);
            wire(s.status === "available");
            scope(s.scope);
            integer(s.before_head);
            integer(s.after_head, s.before_head as number);
            hash(s.input_semantic_sha256);
            [
                o.capture_available,
                o.receipt_available,
                o.recording_available,
            ].forEach(bool);
            const missing = list(o.unavailable, (v) =>
                choices(v, unavailableRows),
            );
            wire(new Set(missing).size === missing.length);
            wire(
                missing.includes("capture_unavailable") ===
                    !o.capture_available &&
                    missing.includes("recording_unavailable") ===
                        !o.recording_available &&
                    missing.includes("no_accepted_receipt") ===
                        !o.receipt_available,
            );
        },
        48,
    ) as RowAvailability[];
    wire(
        new Set(values.map((v) => readerRowKey(v.row))).size === values.length,
    );
    return values;
}
function sourceValue(v: unknown, binding: string): ReaderSource {
    const o = exact(v, [
        "binding",
        "protocol_version",
        "rows",
        "read_only",
        "execution_available",
    ]);
    hash(o.binding);
    wire(o.binding === binding && (o.protocol_version === 2 || o.protocol_version === 3));
    readonly(o);
    rows(o.rows);
    return o as ReaderSource;
}
export function checkedReaderSource(
    v: unknown,
    token: string,
    binding: string,
): ReaderSource {
    return sourceValue(wrapper(v, "source", token, 65536, 0), binding);
}
function profile(v: unknown): void {
    const p = exact(v, [
        "id",
        "model_sha256",
        "runtime_revision",
        "template_sha256",
        "worker_sha256",
        "profile_manifest_sha256",
        "context_tokens",
        "director_tokens",
        "narrator_tokens",
        "deadline_ms",
        "repair_limit",
    ]);
    wire(/^[a-zA-Z0-9_.-]{1,64}$/.test(text(p.id)));
    [
        p.model_sha256,
        p.template_sha256,
        p.worker_sha256,
        p.profile_manifest_sha256,
    ].forEach((v) => wire(/^[a-fA-F0-9]{64}$/.test(text(v))));
    wire(/^[a-fA-F0-9]{40}$/.test(text(p.runtime_revision)));
    integer(p.context_tokens, 512, 4096);
    integer(p.director_tokens, 1, 350);
    integer(p.narrator_tokens, 1, 350);
    integer(p.deadline_ms, 1, 120000);
    integer(p.repair_limit, 0, 1);
}
function estimate(v: unknown): void {
    const keys = [
        "version",
        "prompt_bytes",
        "schema_bytes",
        "repair_extra_bytes",
        "actual_prompt_schema_estimated_tokens",
        "admission_prompt_schema_estimated_tokens",
        "output_tokens",
        "template_reserve_tokens",
        "estimated_total_tokens",
    ];
    const o = exact(v, keys);
    wire(o.version === 1);
    keys.slice(1).forEach((k) => integer(o[k]));
}
// Mirrors the closed metadata tuples from memory_comparison_v3::arm_descriptors.
// These descriptions grant neither a Host policy nor an execution capability.
const constructionValues = [
    { arm: "literal_player_v1", prompt_version: "locallore-play-v2.6-literal-director-v1",
        narration_policy: "grounded-prose-v2.2", director_schema_id: "locallore-director-literal-v1",
        context_policy: null, compiler_version: null, context_version: null, literal_source_version: 1,
        literal_render_version: 1, literal_schema_version: 1, literal_packing_version: 1, forwarded_budget_version: 1 },
    { arm: "relevant_memory_v1", prompt_version: "locallore-play-v2.5", narration_policy: "grounded-prose-v2.2",
        director_schema_id: "locallore-director-v2", context_policy: "state_relevant_memory_v1", compiler_version: 2,
        context_version: 2, literal_source_version: null, literal_render_version: null, literal_schema_version: null,
        literal_packing_version: null, forwarded_budget_version: 1 },
] as const;
function construction(v: unknown, physicalArm?: unknown): ComparisonArmDescriptorV3 {
    const o = exact(v, Object.keys(constructionValues[0]));
    choices(o.arm, ["literal_player_v1", "relevant_memory_v1"]);
    const index = o.arm === "literal_player_v1" ? 0 : 1;
    if (physicalArm !== undefined) wire(physicalArm === (index === 0 ? "left" : "right"));
    wire(Object.entries(constructionValues[index]).every(([key, value]) => o[key] === value));
    return o as ComparisonArmDescriptorV3;
}
function turn(v: unknown, protocol: 2 | 3 = 2): void {
    const o = exact(
        v,
        [
            "turn",
            "scene",
            "arm",
            ...(protocol === 2 ? ["policy"] : ["construction", "construction_matches", "construction_evidence_status",
                "literal_source_units", "literal_selected_start", "literal_selected_units", "forwarded_director_estimates"]),
            "phase",
            "error",
            "expected",
            "passed",
            "failures",
            "quality_flags",
            "roles",
            "roles_known",
            "recovered_without_checkpoint",
            "admission",
            "elapsed_ms",
            "first_final_response_ms",
            "commit_elapsed_ms",
            "input_semantic_sha256",
            "output_semantic_sha256",
            "mechanical_sha256",
            ...(protocol === 2 ? ["policy_matches"] : []),
            "context_evidence_available",
            "context_requirement",
            "privacy_passed",
            "fallback",
            "capture_sha256",
            "recording_sha256",
            "raw_sha256",
            "role_metrics",
            "trace",
            "actual_receipt_sha256",
            "source_fallback_reason",
            "compiler_fallback_reason",
            "narration",
            "repairs",
            "stages",
            "mandatory_sha256",
            "optional_detail_selected",
            "director_private_target_present",
            "selected_context_bytes",
            "estimated_context_tokens",
        ],
        protocol === 2 ? ["forwarded_director_estimates"] : [],
    );
    id(o.turn);
    integer(o.scene, 0, 255);
    choices(o.arm, ["left", "right"]);
    if (protocol === 2) {
        choices(o.policy, ["state_recent_transcript_v1", "state_relevant_memory_v1"]);
        bool(o.policy_matches);
    } else {
        const descriptor = construction(o.construction, o.arm);
        bool(o.construction_matches);
        const status = choices(o.construction_evidence_status, ["validated_literal", "validated_relevant",
            "not_applicable_guard", "not_applicable_dependency", "unavailable"]);
        [o.literal_source_units, o.literal_selected_start, o.literal_selected_units].forEach((v) => nullable(v, (v) => integer(v)));
        const literal = descriptor.arm === "literal_player_v1";
        wire(status !== (literal ? "validated_relevant" : "validated_literal"));
        if (status === "validated_literal") {
            const total = integer(o.literal_source_units), start = integer(o.literal_selected_start), count = integer(o.literal_selected_units);
            wire(start <= total && count <= total - start);
        } else wire(o.literal_source_units === null && o.literal_selected_start === null && o.literal_selected_units === null);
        if (literal) [o.mandatory_sha256, o.optional_detail_selected, o.source_fallback_reason, o.compiler_fallback_reason,
            o.selected_context_bytes, o.estimated_context_tokens].forEach((v) => wire(v === null));
    }
    [o.phase, o.expected, o.context_requirement].forEach(text);
    [
        o.error,
        o.source_fallback_reason,
        o.compiler_fallback_reason,
        o.narration,
    ].forEach((v) => nullable(v, text));
    [
        o.passed,
        o.roles_known,
        o.recovered_without_checkpoint,
        o.context_evidence_available,
        o.privacy_passed,
    ].forEach(bool);
    [
        o.fallback,
        o.optional_detail_selected,
        o.director_private_target_present,
    ].forEach((v) => nullable(v, bool));
    [o.failures, o.quality_flags].forEach(strings);
    [o.roles, o.elapsed_ms].forEach((v) => integer(v));
    [
        o.admission,
        o.first_final_response_ms,
        o.commit_elapsed_ms,
        o.selected_context_bytes,
        o.estimated_context_tokens,
    ].forEach((v) => nullable(v, (v) => integer(v)));
    nullable(o.repairs, (v) => integer(v, 0, 255));
    [
        o.input_semantic_sha256,
        o.output_semantic_sha256,
        o.mechanical_sha256,
    ].forEach(hash);
    [
        o.capture_sha256,
        o.recording_sha256,
        o.actual_receipt_sha256,
        o.mandatory_sha256,
    ].forEach((v) => nullable(v, hash));
    list(o.raw_sha256, hash);
    list(o.stages, () => {});
    if (protocol === 3) nullable(o.forwarded_director_estimates, (v) => list(v, estimate));
    else if (Object.hasOwn(o, "forwarded_director_estimates")) list(o.forwarded_director_estimates, estimate);
}
function report(v: unknown): ComparisonReport {
    const version = object(v).version;
    wire(version === 2 || version === 3);
    const o = exact(v, [
        "version",
        ...(version === 3 ? ["arms"] : []),
        "kind",
        "lane",
        "source_matches",
        "completed",
        "completed_scenes",
        "turns",
        "human_reviewed",
        "human_rubric",
        "quality_accepted",
        "physical_setups",
        "physical_setup_ms",
        "native_load",
        "left_charged_ms",
        "right_charged_ms",
        "left_reserved_roles",
        "right_reserved_roles",
        "first_semantic_divergence",
        "first_mechanical_divergence",
        "same_input_pairs",
        "unavailable",
        "profile",
        "suite_sha256",
        "source_sha256",
        "reference_sha256",
        "limitations",
    ]);
    let descriptors: ComparisonArmDescriptorV3[] = [];
    if (version === 3) {
        descriptors = list(o.arms, (v) => construction(v), 2) as ComparisonArmDescriptorV3[];
        wire(descriptors.length === 2);
        construction(descriptors[0], "left"); construction(descriptors[1], "right");
    }
    choices(o.kind, ["paired_snapshots", "continuous_rollout"]);
    text(o.lane);
    [o.source_matches, o.completed, o.quality_accepted].forEach(bool);
    text(o.human_rubric);
    [
        o.completed_scenes,
        o.human_reviewed,
        o.physical_setups,
        o.left_charged_ms,
        o.right_charged_ms,
        o.left_reserved_roles,
        o.right_reserved_roles,
        o.same_input_pairs,
    ].forEach((v) => integer(v));
    nullable(o.physical_setup_ms, (v) => integer(v));
    [o.first_semantic_divergence, o.first_mechanical_divergence].forEach((v) =>
        nullable(v, text),
    );
    [o.unavailable, o.limitations].forEach(strings);
    profile(o.profile);
    hash(o.suite_sha256);
    hash(o.source_sha256);
    nullable(o.reference_sha256, hash);
    const turns = list(o.turns, (value) => turn(value, version), 48) as ComparisonTurn[];
    wire(new Set(turns.map(readerRowKey)).size === turns.length);
    if (version === 3) turns.forEach((value) => {
        wire("construction" in value);
        const expected = descriptors[value.arm === "left" ? 0 : 1];
        wire(Object.keys(expected).every((key) => object(value.construction)[key] === object(expected)[key]));
    });
    return o as ComparisonReport;
}
export function checkedReaderSummary(
    v: unknown,
    token: string,
    binding: string,
): ReaderSummary {
    const o = exact(wrapper(v, "snapshot", token, 2 * 1024 * 1024), [
        "version",
        "protocol_version",
        "binding",
        "report",
        "rows",
        "read_only",
        "execution_available",
        "unavailable",
    ]);
    wire(
        o.version === 1 &&
            (o.protocol_version === 2 || o.protocol_version === 3) &&
            hash(o.binding) === binding,
    );
    readonly(o);
    strings(o.unavailable);
    const entries = rows(o.rows),
        r = report(o.report);
    wire(o.protocol_version === r.version && entries.length === r.turns.length);
    entries.forEach((entry, index) => {
        const t = r.turns[index];
        wire(
            readerRowKey(entry.row) === readerRowKey(t) &&
                entry.source.input_semantic_sha256 === t.input_semantic_sha256,
        );
    });
    return o as ReaderSummary;
}
export function checkedReaderRequest(value: unknown): EvidenceRequest {
    const o = object(detached(value, 4096));
    if (o.kind === "query") {
        exact(o, ["kind", "edge", "observer", "view"]);
        choices(o.edge, ["before", "after"]);
        choices(o.view, [
            "profiles",
            "history",
            "relationships",
            "knowledge",
            "promises",
            "provenance",
            "turn_diff",
            "summaries",
            "retrieval_indexes",
        ]);
    } else {
        exact(o, ["kind", "observer"]);
        choices(o.kind, ["receipt", "capture", "outputs"]);
    }
    observer(o.observer);
    return o as EvidenceRequest;
}
export function checkedReaderRow(value: unknown): RowId {
    return rowId(detached(value, 4096));
}
export function checkedReaderObserver(value: unknown): ObserverV2 {
    return observer(detached(value, 4096));
}
export function checkedReaderEvidence(
    v: unknown,
    token: string,
    source: ReaderSource,
    selected: RowId,
    rawRequest: EvidenceRequest,
): ReaderEvidence {
    const request = checkedReaderRequest(rawRequest);
    wire(request.kind === "query" || request.observer.kind === "omniscient");
    const entry = source.rows.find(
        (v) => readerRowKey(v.row) === readerRowKey(selected),
    );
    wire(entry);
    const o = exact(wrapper(v, "evidence", token, 256 * 1024), [
        "version",
        "binding",
        "row",
        "scope",
        "before_head",
        "after_head",
        "observer",
        "edge",
        "read_only",
        "generation_grant",
        "body",
    ]);
    wire(
        o.version === 1 &&
            hash(o.binding) === source.binding &&
            readerRowKey(rowId(o.row)) === readerRowKey(selected),
    );
    wire(
        sameScope(scope(o.scope), entry.source.scope) &&
            integer(o.before_head) === entry.source.before_head &&
            integer(o.after_head) === entry.source.after_head,
    );
    wire(
        sameReaderObserver(observer(o.observer), request.observer) &&
            o.read_only === true &&
            o.generation_grant === false,
    );
    wire(
        o.edge ===
            (request.kind === "query"
                ? request.edge
                : request.kind === "receipt"
                  ? "after"
                  : null),
    );
    const body = object(o.body);
    if (body.kind === "missing") {
        exact(body, ["kind", "reason"]);
        const reason =
            request.kind === "receipt"
                ? "no_accepted_receipt"
                : request.kind === "capture"
                  ? "capture_unavailable"
                  : request.kind === "outputs"
                    ? "recording_unavailable"
                    : null;
        wire(
            reason !== null &&
                body.reason === reason &&
                entry.unavailable.includes(reason),
        );
    } else {
        wire(body.kind === request.kind);
        if (request.kind === "query") {
            exact(body, ["kind", "page"]);
            const head =
                request.edge === "before"
                    ? entry.source.before_head
                    : entry.source.after_head;
            // No experiment player ID is carried by the reader. Do not infer it
            // from the live game or an observer ID; Character messages fail closed.
            try {
                checkedPageV2(body.page, {
                    version: 2,
                    scope: entry.source.scope,
                    expected_head: head,
                    at_revision: null,
                    observer: request.observer,
                    view: request.view,
                    cursor: null,
                    limit: 64,
                    search: "",
                });
            } catch {
                throw new Error("ComparisonReaderWire");
            }
        } else if (request.kind === "receipt") {
            exact(body, ["kind", "receipt"]);
            wire(
                entry.receipt_available &&
                    body.receipt !== null &&
                    typeof body.receipt === "object" &&
                    !Array.isArray(body.receipt),
            );
        } else if (request.kind === "capture") {
            exact(body, ["kind", "capture"]);
            wire(entry.capture_available && encoded(body.capture) <= 196608);
        } else {
            exact(body, ["kind", "outputs"]);
            wire(entry.recording_available);
            list(body.outputs, (output) => {
                const r = exact(output, ["role", "bytes", "sha256", "text"]);
                choices(r.role, ["director", "narrator"]);
                integer(r.bytes, 0, 16384);
                hash(r.sha256);
                wire(utf8(text(r.text)) === r.bytes);
            });
        }
    }
    return o as ReaderEvidence;
}
