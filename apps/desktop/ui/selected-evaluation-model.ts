// Transport-only closed DTOs. Rust owns source validation, grants, canonical
// history and worker cleanup. Parsed JSON cannot prove absence of raw duplicates.
import {
    checkedReaderObserver,
    checkedReaderConstruction,
    checkedReaderSceneConstruction,
    checkedReaderRequest,
    sameReaderObserver,
} from "./comparison-reader-model";
import type {
    ComparisonArmDescriptorV3,
    ComparisonArmDescriptorV4,
    ComparisonTurnV4,
    ConstructionEvidenceStatusV3,
    EvidenceRequest,
    Json,
    RowId,
} from "./comparison-reader-model";
import { checkedPageV2 } from "./v2-view-model";
import type { ObserverV2, ScopeV2, InspectionPageV2 } from "./v2-view-model";
export type { EvidenceRequest, RowId, ObserverV2, ScopeV2 };
export const selectedErrors = [
    "InvalidEvaluationInput",
    "EvaluationBusy",
    "EvaluationModelBusy",
    "EvaluationIo",
    "EvaluationInternal",
    "EvaluationBudget",
    "EvaluationRunLimit",
    "EvaluationSourceMismatch",
    "EvaluationIntegrity",
    "EvaluationTokenLimit",
    "UnknownEvaluationRun",
    "Closed",
    "Forbidden",
    "PickerUnavailable",
    "Cancelled",
    "Cleanup",
    "NativeUnavailable",
] as const;
export type SelectedError =
    (typeof selectedErrors)[number] | "SelectedEvaluationWire";
export type SelectedLane = "scripted_baseline" | "approved_native";
export type StoredSelectedLane =
    "scripted_selected_case" | "native_selected_case";
export type SelectedArm = "left" | "right";
export type SelectedSelection = {
    turn: string;
    clicked_arm: SelectedArm;
    index: number;
};
export type SelectedSourceIdentity = {
    readerClientId: string;
    runToken: string;
    binding: string;
};
type SelectedPreparedV1 = {
    version: 1;
    kind: "selected_prepared";
    binding: string;
    lane: StoredSelectedLane;
    selection: SelectedSelection;
    arms: {
        arm: SelectedArm;
        scope: ScopeV2;
        before_head: number;
        prefix_sha256: string;
        input_semantic_sha256: string;
    }[];
};
type SelectedPreparedV2 = Omit<SelectedPreparedV1, "version"> & {
    version: 2;
    source_protocol_version: 3;
    constructions: ComparisonArmDescriptorV3[];
};
type SelectedPreparedV3 = Omit<SelectedPreparedV1, "version" | "lane"> & {
    version: 3;
    source_protocol_version: 4;
    source_binding: string;
    lane: "scripted_selected_case";
    constructions: ComparisonArmDescriptorV4[];
};
export type SelectedPrepared = SelectedPreparedV1 | SelectedPreparedV2 | SelectedPreparedV3;
type SelectedSummaryV1 = {
    version: 1;
    kind: "selected_read";
    binding: string;
    lane: StoredSelectedLane;
    selection: SelectedSelection;
    arms: {
        arm: SelectedArm;
        scope: ScopeV2;
        before_head: number;
        after_head: number | null;
        available: boolean;
    }[];
    read_only: true;
    execution_available: false;
};
type SelectedSummaryV2 = Omit<SelectedSummaryV1, "version"> & {
    version: 2;
    source_protocol_version: 3;
    constructions: ComparisonArmDescriptorV3[];
};
type SelectedSummaryV3 = Omit<SelectedSummaryV1, "version" | "lane"> & {
    version: 3;
    source_protocol_version: 4;
    lane: "scripted_selected_case";
    constructions: ComparisonArmDescriptorV4[];
};
export type SelectedSummary = SelectedSummaryV1 | SelectedSummaryV2 | SelectedSummaryV3;
export type SelectedStatus = {
    version: 1;
    kind: "selected_evaluation";
    client_id: string;
    operation_id: number | null;
    phase:
        | "preparing"
        | "prepared"
        | "running"
        | "cancelling"
        | "cleanup_required"
        | "completed"
        | "paused"
        | "failed"
        | "closed";
    running: boolean;
    lane: SelectedLane | null;
    plan_token: string | null;
    run_id: string | null;
    run_token: string | null;
    binding: string | null;
    prepared: SelectedPrepared | null;
    error: (typeof selectedErrors)[number] | null;
    cause: (typeof selectedErrors)[number] | null;
    cleanup_required: boolean;
};
export type SelectedCatalog = {
    version: 1;
    kind: "selected_catalog";
    runs: {
        run_id: string;
        created: number;
        lane: SelectedLane;
        selection: SelectedSelection;
    }[];
};
export type SelectedCleanup = {
    version: 1;
    kind: "selected_cleanup";
    cleanup_required: boolean;
    running: boolean;
    error: (typeof selectedErrors)[number] | null;
};
type SelectedDiagnosticRowV1 = {
    turn: string;
    arm: SelectedArm;
    phase:
        | "committed"
        | "failed"
        | "rejected"
        | "cancelled"
        | "stale"
        | "not_run_dependency";
    error: string | null;
    expected: string;
    passed: boolean;
    failures: string[];
    quality_flags: string[];
    roles: number;
    roles_known: boolean;
    elapsed_ms: number;
    actual_receipt_sha256: string | null;
    privacy_passed: boolean;
    context_evidence_available: boolean;
};
type SelectedDiagnosticRowV2 = SelectedDiagnosticRowV1 & {
    construction: ComparisonArmDescriptorV3;
    construction_evidence_status: ConstructionEvidenceStatusV3;
    construction_matches: boolean;
    literal_source_units: number | null;
    literal_selected_start: number | null;
    literal_selected_units: number | null;
    fallback: boolean | null;
};
type SelectedDiagnosticRowV3 = Omit<SelectedDiagnosticRowV1,
    "privacy_passed" | "context_evidence_available"> & Pick<ComparisonTurnV4,
    "construction" | "construction_evidence_status" | "construction_evidence_reason" |
    "construction_matches" | "privacy_evidence_status" | "fallback" | "repairs" |
    "recovered_without_checkpoint" | "first_final_response_ms" | "commit_elapsed_ms" |
    "narrator_prompt_sha256" | "narrator_schema_sha256" | "scene_frame_sha256">;
export type SelectedDiagnosticRow =
    SelectedDiagnosticRowV1 | SelectedDiagnosticRowV2 | SelectedDiagnosticRowV3;
type SelectedDiagnosticsV1 = {
    version: 1;
    kind: "selected_diagnostics";
    binding: string;
    lane: StoredSelectedLane;
    completed: boolean;
    rows: SelectedDiagnosticRowV1[];
    physical_setups: number;
    physical_setup_ms: number | null;
    left_charged_ms: number;
    right_charged_ms: number;
    left_reserved_roles: number;
    right_reserved_roles: number;
    human_reviewed: 0;
    quality_accepted: false;
    unavailable: string[];
};
type SelectedDiagnosticsV2 = Omit<SelectedDiagnosticsV1, "version" | "rows"> & {
    version: 2;
    source_protocol_version: 3;
    constructions: ComparisonArmDescriptorV3[];
    rows: SelectedDiagnosticRowV2[];
};
type SelectedDiagnosticsV3 = Omit<SelectedDiagnosticsV1, "version" | "rows" | "lane"> & {
    version: 3;
    source_protocol_version: 4;
    lane: "scripted_selected_case";
    constructions: ComparisonArmDescriptorV4[];
    human_rubric: "not_reviewed";
    rows: SelectedDiagnosticRowV3[];
};
export type SelectedDiagnostics = SelectedDiagnosticsV1 | SelectedDiagnosticsV2 | SelectedDiagnosticsV3;
export type SelectedEvidence = {
    version: 1;
    binding: string;
    row: RowId;
    scope: ScopeV2;
    before_head: number;
    after_head: number | null;
    observer: ObserverV2;
    edge: "before" | "after" | null;
    read_only: true;
    generation_grant: false;
    body:
        | { kind: "query"; page: InspectionPageV2 }
        | { kind: "receipt"; receipt: { [key: string]: Json } }
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
                  | "checkpoint_unavailable"
                  | "capture_unavailable"
                  | "recording_unavailable"
                  | "no_accepted_receipt";
          };
};
type Obj = Record<string, unknown>;
const utf8 = (s: string): number => new TextEncoder().encode(s).length;
function requireWire(value: unknown): asserts value {
    if (!value) throw new Error("SelectedEvaluationWire");
}
function object(v: unknown): Obj {
    requireWire(v !== null && typeof v === "object" && !Array.isArray(v));
    return v as Obj;
}
function exact(v: unknown, keys: readonly string[]): Obj {
    const o = object(v);
    requireWire(
        Object.keys(o).length === keys.length &&
            keys.every((k) => Object.hasOwn(o, k)),
    );
    return o;
}
function detached(v: unknown, max: number): unknown {
    try {
        // Inspect own data descriptors before any serialization. These inputs
        // are JSON data, not objects whose getters/toJSON may run during copy.
        const ancestors = new Set<object>();
        let nodes = 0, minimumBytes = 0;
        const spend = (bytes: number) => {
            minimumBytes += bytes;
            requireWire(minimumBytes <= max);
        };
        const copy = (value: unknown, depth: number): unknown => {
            requireWire(++nodes <= max && depth <= 128);
            if (value === null || typeof value === "boolean") {
                spend(value === null || value === true ? 4 : 5);
                return value;
            }
            if (typeof value === "string") {
                spend(utf8(value) + 2);
                return value;
            }
            if (typeof value === "number") {
                requireWire(Number.isFinite(value));
                spend(String(value).length);
                return value;
            }
            requireWire(typeof value === "object" && !ancestors.has(value));
            const sequence = Array.isArray(value);
            requireWire(Object.getPrototypeOf(value) === (sequence ? Array.prototype : Object.prototype));
            const descriptors = Object.getOwnPropertyDescriptors(value);
            const keys = Reflect.ownKeys(descriptors);
            requireWire(keys.length <= max && keys.every((key) => typeof key === "string"));
            spend(2);
            ancestors.add(value);
            let result: unknown;
            if (sequence) {
                const length = integer(descriptors.length?.value, max);
                requireWire(keys.length === length + 1);
                const items: unknown[] = [];
                for (let i = 0; i < length; i++) {
                    const field = descriptors[String(i)];
                    requireWire(field && Object.hasOwn(field, "value") && field.enumerable);
                    if (i) spend(1);
                    items.push(copy(field.value, depth + 1));
                }
                result = items;
            } else {
                const fields: Obj = Object.create(null);
                let count = 0;
                for (const key of keys) {
                    requireWire(typeof key === "string");
                    const field = descriptors[key];
                    requireWire(Object.hasOwn(field, "value") && field.enumerable);
                    spend(utf8(key) + 3 + (count++ ? 1 : 0));
                    fields[key] = copy(field.value, depth + 1);
                }
                result = fields;
            }
            ancestors.delete(value);
            return result;
        };
        const encoded = JSON.stringify(copy(v, 0));
        requireWire(typeof encoded === "string" && utf8(encoded) <= max);
        return JSON.parse(encoded);
    } catch {
        throw new Error("SelectedEvaluationWire");
    }
}
function text(v: unknown, max = 256 * 1024): string {
    requireWire(typeof v === "string" && utf8(v) <= max);
    return v;
}
function integer(v: unknown, max = Number.MAX_SAFE_INTEGER): number {
    requireWire(
        typeof v === "number" && Number.isSafeInteger(v) && v >= 0 && v <= max,
    );
    return v;
}
function bool(v: unknown): void {
    requireWire(typeof v === "boolean");
}
function one(v: unknown, values: readonly string[]): string {
    const s = text(v);
    requireWire(values.includes(s));
    return s;
}
function array(
    v: unknown,
    visit: (value: unknown) => unknown,
    max = 256 * 1024,
): unknown[] {
    requireWire(Array.isArray(v) && v.length <= max);
    v.forEach((item) => {
        visit(item);
    });
    return v;
}
function nullable(v: unknown, visit: (v: unknown) => unknown): void {
    if (v !== null) visit(v);
}
function id(v: unknown): string {
    const s = text(v, 64);
    requireWire(/^[A-Za-z0-9_-]{1,64}$/.test(s));
    return s;
}
export function selectedUuid(v: unknown): string {
    const s = text(v, 36);
    requireWire(/^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/.test(s));
    return s;
}
export function selectedHash(v: unknown): string {
    const s = text(v, 64);
    requireWire(/^[a-f0-9]{64}$/.test(s));
    return s;
}
function scope(v: unknown): ScopeV2 {
    const o = exact(v, ["story", "branch"]);
    id(o.story);
    id(o.branch);
    return o as ScopeV2;
}
export function selectedLane(v: unknown): SelectedLane {
    return one(v, ["scripted_baseline", "approved_native"]) as SelectedLane;
}
function storedLane(v: unknown): void {
    one(v, ["scripted_selected_case", "native_selected_case"]);
}
export function selectedArm(v: unknown): SelectedArm {
    return one(v, ["left", "right"]) as SelectedArm;
}
function selection(v: unknown): void {
    const o = exact(v, ["turn", "clicked_arm", "index"]);
    id(o.turn);
    selectedArm(o.clicked_arm);
    integer(o.index, 23);
}
export function checkedSelectedSource(v: unknown): SelectedSourceIdentity {
    const o = exact(detached(v, 4096), [
        "readerClientId",
        "runToken",
        "binding",
    ]);
    selectedUuid(o.readerClientId);
    selectedUuid(o.runToken);
    selectedHash(o.binding);
    return o as SelectedSourceIdentity;
}
export function checkedSelectedRow(v: unknown): RowId {
    const o = exact(detached(v, 4096), ["turn", "arm"]);
    id(o.turn);
    selectedArm(o.arm);
    return o as RowId;
}
export function checkedSelectedObserver(v: unknown): ObserverV2 {
    try {
        return checkedReaderObserver(detached(v, 4096));
    } catch {
        throw new Error("SelectedEvaluationWire");
    }
}
export function checkedSelectedRequest(v: unknown): EvidenceRequest {
    try {
        return checkedReaderRequest(detached(v, 4096));
    } catch {
        throw new Error("SelectedEvaluationWire");
    }
}
function arms(v: unknown, fields: string[], visit: (o: Obj) => void): void {
    const values = array(
        v,
        (v) => {
            const o = exact(v, fields);
            selectedArm(o.arm);
            scope(o.scope);
            integer(o.before_head);
            visit(o);
        },
        2,
    );
    requireWire(
        values.length === 2 &&
            object(values[0]).arm === "left" &&
            object(values[1]).arm === "right",
    );
}
function selectedConstruction(
    v: unknown,
    arm?: unknown,
    scene = false,
): ComparisonArmDescriptorV3 | ComparisonArmDescriptorV4 {
    try {
        return scene ? checkedReaderSceneConstruction(v, arm) : checkedReaderConstruction(v, arm);
    } catch {
        throw new Error("SelectedEvaluationWire");
    }
}
function versioned(v: unknown, fields: string[], prepared = false): Obj {
    const version = object(v).version;
    requireWire(version === 1 || version === 2 || version === 3);
    const o = exact(v, [
        ...fields,
        ...(version !== 1 ? ["source_protocol_version", "constructions"] : []),
        ...(version === 3 && prepared ? ["source_binding"] : []),
    ]);
    if (version !== 1) {
        requireWire(o.source_protocol_version === (version === 3 ? 4 : 3));
        const values = array(
            o.constructions,
            (v) => selectedConstruction(v, undefined, version === 3),
            2,
        );
        requireWire(values.length === 2);
        selectedConstruction(values[0], "left", version === 3);
        selectedConstruction(values[1], "right", version === 3);
    }
    if (version === 3) requireWire(o.lane === "scripted_selected_case");
    return o;
}
export function checkedSelectedPrepared(v: unknown): SelectedPrepared {
    const o = versioned(detached(v, 16 * 1024), [
        "version",
        "kind",
        "binding",
        "lane",
        "selection",
        "arms",
    ], true);
    requireWire(o.kind === "selected_prepared");
    selectedHash(o.binding);
    if (o.version === 3) selectedHash(o.source_binding);
    storedLane(o.lane);
    selection(o.selection);
    arms(
        o.arms,
        [
            "arm",
            "scope",
            "before_head",
            "prefix_sha256",
            "input_semantic_sha256",
        ],
        (a) => {
            selectedHash(a.prefix_sha256);
            selectedHash(a.input_semantic_sha256);
        },
    );
    return o as SelectedPrepared;
}
export function checkedSelectedStatus(
    v: unknown,
    clientId?: string,
): SelectedStatus {
    const o = exact(detached(v, 32 * 1024), [
        "version",
        "kind",
        "client_id",
        "operation_id",
        "phase",
        "running",
        "lane",
        "plan_token",
        "run_id",
        "run_token",
        "binding",
        "prepared",
        "error",
        "cause",
        "cleanup_required",
    ]);
    requireWire(o.version === 1 && o.kind === "selected_evaluation");
    selectedUuid(o.client_id);
    if (clientId !== undefined)
        requireWire(o.client_id === selectedUuid(clientId));
    nullable(o.operation_id, integer);
    one(o.phase, [
        "preparing",
        "prepared",
        "running",
        "cancelling",
        "cleanup_required",
        "completed",
        "paused",
        "failed",
        "closed",
    ]);
    bool(o.running);
    nullable(o.lane, selectedLane);
    nullable(o.plan_token, selectedUuid);
    nullable(o.run_id, selectedUuid);
    nullable(o.run_token, selectedUuid);
    nullable(o.binding, selectedHash);
    nullable(o.prepared, checkedSelectedPrepared);
    nullable(o.error, (v) => one(v, selectedErrors));
    nullable(o.cause, (v) => one(v, selectedErrors));
    bool(o.cleanup_required);
    if (
        o.phase === "closed" ||
        o.error === "Forbidden" ||
        o.error === "Closed" ||
        o.error === "UnknownEvaluationRun"
    ) {
        requireWire(
            o.plan_token === null &&
                o.run_id === null &&
                o.run_token === null &&
                o.binding === null &&
                o.prepared === null,
        );
    }
    return o as SelectedStatus;
}
export function checkedSelectedCatalog(v: unknown): SelectedCatalog {
    const o = exact(detached(v, 32 * 1024), ["version", "kind", "runs"]);
    requireWire(o.version === 1 && o.kind === "selected_catalog");
    const seen = new Set<string>();
    array(
        o.runs,
        (v) => {
            const r = exact(v, ["run_id", "created", "lane", "selection"]);
            const key = selectedUuid(r.run_id);
            requireWire(!seen.has(key));
            seen.add(key);
            integer(r.created);
            selectedLane(r.lane);
            selection(r.selection);
        },
        32,
    );
    return o as SelectedCatalog;
}
export function checkedSelectedCleanup(v: unknown): SelectedCleanup {
    const o = exact(detached(v, 4096), [
        "version",
        "kind",
        "cleanup_required",
        "running",
        "error",
    ]);
    requireWire(o.version === 1 && o.kind === "selected_cleanup");
    bool(o.cleanup_required);
    bool(o.running);
    nullable(o.error, (v) => one(v, selectedErrors));
    return o as SelectedCleanup;
}
function wrapper(
    v: unknown,
    kind: string,
    field: string,
    token: string,
): unknown {
    const o = exact(detached(v, 256 * 1024 + 256), [
        "version",
        "kind",
        "run_token",
        field,
    ]);
    requireWire(
        o.version === 1 &&
            o.kind === kind &&
            selectedUuid(o.run_token) === selectedUuid(token),
    );
    return o[field];
}
export function checkedSelectedSummary(
    v: unknown,
    token: string,
    binding?: string,
): SelectedSummary {
    const o = versioned(
        detached(wrapper(v, "selected_summary", "summary", token), 16 * 1024),
        [
            "version",
            "kind",
            "binding",
            "lane",
            "selection",
            "arms",
            "read_only",
            "execution_available",
        ],
    );
    requireWire(
        o.kind === "selected_read" &&
            o.read_only === true &&
            o.execution_available === false,
    );
    selectedHash(o.binding);
    if (binding !== undefined) requireWire(o.binding === selectedHash(binding));
    storedLane(o.lane);
    selection(o.selection);
    arms(
        o.arms,
        ["arm", "scope", "before_head", "after_head", "available"],
        (a) => {
            bool(a.available);
            nullable(a.after_head, integer);
            requireWire(a.available === (a.after_head !== null));
            if (a.after_head !== null)
                requireWire(integer(a.after_head) >= integer(a.before_head));
        },
    );
    return o as SelectedSummary;
}
export function checkedSelectedDiagnostics(
    v: unknown,
    token: string,
    summary: SelectedSummary,
): SelectedDiagnostics {
    summary = checkedSelectedSummary({ version: 1, kind: "selected_summary", run_token: token, summary }, token);
    const raw = detached(wrapper(v, "selected_diagnostics_result", "diagnostics", token), 256 * 1024);
    const o = versioned(
        raw,
        [
            "version",
            "kind",
            "binding",
            "lane",
            "completed",
            "rows",
            "physical_setups",
            "physical_setup_ms",
            "left_charged_ms",
            "right_charged_ms",
            "left_reserved_roles",
            "right_reserved_roles",
            "human_reviewed",
            "quality_accepted",
            "unavailable",
            ...(object(raw).version === 3 ? ["human_rubric"] : []),
        ],
    );
    requireWire(
        o.version === summary.version &&
            o.kind === "selected_diagnostics" &&
            selectedHash(o.binding) === summary.binding &&
            o.lane === summary.lane,
    );
    bool(o.completed);
    const seen = new Set<string>();
    array(
        o.rows,
        (v) => {
            const r = exact(v, [
                "turn",
                "arm",
                "phase",
                "error",
                "expected",
                "passed",
                "failures",
                "quality_flags",
                "roles",
                "roles_known",
                "elapsed_ms",
                "actual_receipt_sha256",
                ...(o.version === 3 ? [
                    "construction", "construction_evidence_status", "construction_evidence_reason",
                    "construction_matches", "privacy_evidence_status", "fallback", "repairs",
                    "recovered_without_checkpoint", "first_final_response_ms", "commit_elapsed_ms",
                    "narrator_prompt_sha256", "narrator_schema_sha256", "scene_frame_sha256",
                ] : ["privacy_passed", "context_evidence_available"]),
                ...(o.version === 2
                    ? [
                          "construction",
                          "construction_evidence_status",
                          "construction_matches",
                          "literal_source_units",
                          "literal_selected_start",
                          "literal_selected_units",
                          "fallback",
                      ]
                    : []),
            ]);
            requireWire(id(r.turn) === summary.selection.turn);
            const arm = selectedArm(r.arm);
            requireWire(!seen.has(arm));
            seen.add(arm);
            one(r.phase, [
                "committed",
                "failed",
                "rejected",
                "cancelled",
                "stale",
                "not_run_dependency",
            ]);
            nullable(r.error, text);
            text(r.expected);
            bool(r.passed);
            array(r.failures, text);
            array(r.quality_flags, text);
            integer(r.roles);
            bool(r.roles_known);
            integer(r.elapsed_ms);
            nullable(r.actual_receipt_sha256, selectedHash);
            if (o.version === 3) {
                selectedConstruction(r.construction, arm, true);
                one(r.construction_evidence_status, [
                    "validated_committed_scene_narrator_v1", "not_applicable_guard",
                    "not_applicable_dependency", "unavailable",
                ]);
                nullable(r.construction_evidence_reason, text);
                bool(r.construction_matches);
                one(r.privacy_evidence_status, ["checked_finite_sentinels", "not_applicable_guard", "unavailable"]);
                nullable(r.fallback, bool);
                nullable(r.repairs, (v) => integer(v, 255));
                bool(r.recovered_without_checkpoint);
                nullable(r.first_final_response_ms, integer);
                nullable(r.commit_elapsed_ms, integer);
                for (const key of ["narrator_prompt_sha256", "narrator_schema_sha256", "scene_frame_sha256"])
                    nullable(r[key], selectedHash);
            } else {
                bool(r.privacy_passed);
                bool(r.context_evidence_available);
            }
            if (o.version === 2) {
                const descriptor = selectedConstruction(r.construction, arm);
                bool(r.construction_matches);
                const status = one(r.construction_evidence_status, [
                    "validated_literal",
                    "validated_relevant",
                    "not_applicable_guard",
                    "not_applicable_dependency",
                    "unavailable",
                ]);
                nullable(r.fallback, bool);
                [
                    r.literal_source_units,
                    r.literal_selected_start,
                    r.literal_selected_units,
                ].forEach((v) => nullable(v, integer));
                const literal = descriptor.arm === "literal_player_v1";
                requireWire(
                    status !==
                        (literal ? "validated_relevant" : "validated_literal"),
                );
                if (status === "validated_literal") {
                    const total = integer(r.literal_source_units),
                        start = integer(r.literal_selected_start),
                        count = integer(r.literal_selected_units);
                    requireWire(start <= total && count <= total - start);
                } else
                    requireWire(
                        r.literal_source_units === null &&
                            r.literal_selected_start === null &&
                            r.literal_selected_units === null,
                    );
            }
        },
        2,
    );
    for (const k of [
        "physical_setups",
        "left_charged_ms",
        "right_charged_ms",
        "left_reserved_roles",
        "right_reserved_roles",
    ])
        integer(o[k]);
    nullable(o.physical_setup_ms, integer);
    requireWire(o.human_reviewed === 0 && o.quality_accepted === false);
    if (o.version === 3)
        requireWire(o.human_rubric === "not_reviewed" && o.physical_setups === 0 && o.physical_setup_ms === null);
    array(o.unavailable, text);
    return o as SelectedDiagnostics;
}
export function checkedSelectedEvidence(
    v: unknown,
    token: string,
    summary: SelectedSummary,
    selected: SelectedArm,
    rawRequest: EvidenceRequest,
): SelectedEvidence {
    summary = checkedSelectedSummary({ version: 1, kind: "selected_summary", run_token: token, summary }, token);
    const request = checkedSelectedRequest(rawRequest);
    requireWire(
        request.kind === "query" || request.observer.kind === "omniscient",
    );
    const entry = summary.arms.find((a) => a.arm === selectedArm(selected));
    requireWire(entry);
    const o = exact(
        detached(
            wrapper(v, "selected_evidence", "evidence", token),
            256 * 1024,
        ),
        [
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
        ],
    );
    const row = checkedSelectedRow(o.row),
        s = scope(o.scope);
    requireWire(
        o.version === 1 &&
            selectedHash(o.binding) === summary.binding &&
            row.turn === summary.selection.turn &&
            row.arm === selected,
    );
    requireWire(
        s.story === entry.scope.story &&
            s.branch === entry.scope.branch &&
            integer(o.before_head) === entry.before_head &&
            o.after_head === entry.after_head,
    );
    requireWire(
        sameReaderObserver(
            checkedSelectedObserver(o.observer),
            request.observer,
        ) &&
            o.read_only === true &&
            o.generation_grant === false,
    );
    const body = object(o.body);
    if (!entry.available) {
        exact(body, ["kind", "reason"]);
        requireWire(
            body.kind === "missing" &&
                body.reason === "checkpoint_unavailable" &&
                o.edge === null &&
                o.after_head === null,
        );
    } else {
        requireWire(
            o.edge ===
                (request.kind === "query"
                    ? request.edge
                    : request.kind === "receipt"
                      ? "after"
                      : null),
        );
        if (body.kind === "missing") {
            exact(body, ["kind", "reason"]);
            requireWire(
                body.reason ===
                    (request.kind === "receipt"
                        ? "no_accepted_receipt"
                        : request.kind === "capture"
                          ? "capture_unavailable"
                          : request.kind === "outputs"
                            ? "recording_unavailable"
                            : null),
            );
        } else {
            requireWire(body.kind === request.kind);
            if (request.kind === "query") {
                exact(body, ["kind", "page"]);
                try {
                    checkedPageV2(body.page, {
                        version: 2,
                        scope: entry.scope,
                        expected_head:
                            request.edge === "before"
                                ? entry.before_head
                                : integer(entry.after_head),
                        at_revision: null,
                        observer: request.observer,
                        view: request.view,
                        cursor: null,
                        limit: 64,
                        search: "",
                    });
                } catch {
                    throw new Error("SelectedEvaluationWire");
                }
            } else if (request.kind === "receipt") {
                exact(body, ["kind", "receipt"]);
                object(body.receipt);
            } else if (request.kind === "capture") {
                exact(body, ["kind", "capture"]);
                detached(body.capture, 196608);
            } else {
                exact(body, ["kind", "outputs"]);
                array(body.outputs, (v) => {
                    const r = exact(v, ["role", "bytes", "sha256", "text"]);
                    one(r.role, ["director", "narrator"]);
                    requireWire(integer(r.bytes, 16384) === utf8(text(r.text)));
                    selectedHash(r.sha256);
                });
            }
        }
    }
    return o as SelectedEvidence;
}
