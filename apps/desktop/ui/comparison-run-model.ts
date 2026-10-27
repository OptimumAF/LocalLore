// Closed transport metadata only. Rust owns execution, source validation,
// durable histories, resource accounting and actual worker cleanup.
export const comparisonRunErrors = [
    "Forbidden",
    "Closed",
    "InvalidEvaluationInput",
    "UnknownEvaluationRun",
    "StaleEvaluationOperation",
    "EvaluationBusy",
    "EvaluationBudget",
    "EvaluationRunLimit",
    "EvaluationTokenLimit",
    "EvaluationSourceMismatch",
    "EvaluationIntegrity",
    "EvaluationNotReady",
    "UnsafeEvaluationPath",
    "EvaluationIo",
    "EvaluationInternal",
    "Cancelled",
    "PickerUnavailable",
    "NativeUnavailable",
] as const;
export type ComparisonRunError =
    (typeof comparisonRunErrors)[number] | "ComparisonRunWire";
export type ComparisonRunKind = "paired" | "rollout";
export type ComparisonRunMetadata = {
    run_id: string;
    client_id: string;
    comparison_kind: ComparisonRunKind;
    initial_batch: number;
    created_ms: number;
    protocol_version: 3;
    input_lane: "scripted_baseline";
};
export type ComparisonRunCatalog = {
    version: 1;
    kind: "comparison_run_catalog";
    protocol_version: 3;
    input_lane: "scripted_baseline";
    max_new_scenes: 4;
    runs: ComparisonRunMetadata[];
};
export type ComparisonRunStatus = {
    version: 1;
    kind: "comparison_run";
    protocol_version: 3;
    input_lane: "scripted_baseline";
    client_id: string;
    run_id: string;
    run_token: string;
    operation_id: number | null;
    comparison_kind: ComparisonRunKind;
    batch: number;
    phase:
        | "retained"
        | "starting"
        | "running"
        | "opening"
        | "stopping_at_boundary"
        | "paused"
        | "completed"
        | "failed"
        | "closed";
    running: boolean;
    error: (typeof comparisonRunErrors)[number] | null;
    completed_scenes: number;
    completed: boolean;
    report_ready: boolean;
    source_matches: boolean | null;
};
type ObjectValue = Record<string, unknown>;
function wire(value: unknown): asserts value {
    if (!value) throw Error("ComparisonRunWire");
}
function object(value: unknown): ObjectValue {
    wire(value !== null && typeof value === "object" && !Array.isArray(value));
    return value as ObjectValue;
}
function exact(value: unknown, keys: readonly string[]): ObjectValue {
    const result = object(value);
    wire(
        Object.keys(result).length === keys.length &&
            keys.every((key) => Object.hasOwn(result, key)),
    );
    return result;
}
function detached(value: unknown, limit: number): unknown {
    try {
        const text = JSON.stringify(value);
        wire(
            typeof text === "string" &&
                new TextEncoder().encode(text).length <= limit,
        );
        return JSON.parse(text);
    } catch {
        throw Error("ComparisonRunWire");
    }
}
function number(
    value: unknown,
    minimum = 0,
    maximum = Number.MAX_SAFE_INTEGER,
): number {
    wire(
        typeof value === "number" &&
            Number.isSafeInteger(value) &&
            value >= minimum &&
            value <= maximum,
    );
    return value;
}
function boolean(value: unknown): void {
    wire(typeof value === "boolean");
}
function choice(value: unknown, values: readonly string[]): string {
    wire(typeof value === "string" && values.includes(value));
    return value;
}
export function comparisonRunUuid(value: unknown): string {
    wire(
        typeof value === "string" &&
            /^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/.test(value),
    );
    return value;
}
export function comparisonRunKind(value: unknown): ComparisonRunKind {
    return choice(value, ["paired", "rollout"]) as ComparisonRunKind;
}
export function comparisonRunBatch(value: unknown): number {
    return number(value, 1, 4);
}
export function checkedComparisonRunStatus(
    value: unknown,
): ComparisonRunStatus {
    const result = exact(detached(value, 32 * 1024), [
        "version",
        "kind",
        "protocol_version",
        "input_lane",
        "client_id",
        "run_id",
        "run_token",
        "operation_id",
        "comparison_kind",
        "batch",
        "phase",
        "running",
        "error",
        "completed_scenes",
        "completed",
        "report_ready",
        "source_matches",
    ]);
    wire(
        result.version === 1 &&
            result.kind === "comparison_run" &&
            result.protocol_version === 3 &&
            result.input_lane === "scripted_baseline",
    );
    [result.client_id, result.run_id, result.run_token].forEach(
        comparisonRunUuid,
    );
    if (result.operation_id !== null) number(result.operation_id, 1);
    comparisonRunKind(result.comparison_kind);
    comparisonRunBatch(result.batch);
    choice(result.phase, [
        "retained",
        "starting",
        "running",
        "opening",
        "stopping_at_boundary",
        "paused",
        "completed",
        "failed",
        "closed",
    ]);
    if (result.error !== null) choice(result.error, comparisonRunErrors);
    number(result.completed_scenes, 0, 4);
    [result.running, result.completed, result.report_ready].forEach(boolean);
    if (result.source_matches !== null) boolean(result.source_matches);
    // Presentation closure is not positive worker cleanup. Readiness, source
    // matching, completion and running are deliberately independent fields.
    return result as ComparisonRunStatus;
}
export function checkedComparisonRunCatalog(
    value: unknown,
): ComparisonRunCatalog {
    const result = exact(detached(value, 64 * 1024), [
        "version",
        "kind",
        "protocol_version",
        "input_lane",
        "runs",
        "max_new_scenes",
    ]);
    wire(
        result.version === 1 &&
            result.kind === "comparison_run_catalog" &&
            result.protocol_version === 3 &&
            result.input_lane === "scripted_baseline" &&
            result.max_new_scenes === 4,
    );
    const rows = result.runs;
    wire(Array.isArray(rows) && rows.length <= 32);
    const seen = new Set<string>();
    for (const row of rows) {
        const metadata = exact(row, [
            "run_id",
            "client_id",
            "comparison_kind",
            "initial_batch",
            "created_ms",
            "protocol_version",
            "input_lane",
        ]);
        const id = comparisonRunUuid(metadata.run_id);
        wire(!seen.has(id));
        seen.add(id);
        comparisonRunUuid(metadata.client_id);
        comparisonRunKind(metadata.comparison_kind);
        comparisonRunBatch(metadata.initial_batch);
        number(metadata.created_ms);
        wire(
            metadata.protocol_version === 3 &&
                metadata.input_lane === "scripted_baseline",
        );
    }
    return result as ComparisonRunCatalog;
}

// Additive native transport. The legacy allowlist and decoders above remain V1.
export const nativeComparisonRunErrors = [
    ...comparisonRunErrors,
    "EvaluationModelBusy",
    "Cleanup",
] as const;
export type NativeComparisonRunError =
    (typeof nativeComparisonRunErrors)[number] | "ComparisonRunWire";
type NativeProtocolTuple = { version: 2; protocol_version: 3 } | { version: 3; protocol_version: 4 };
export type NativeComparisonRunMetadata = Omit<
    ComparisonRunMetadata,
    "input_lane" | "protocol_version"
> & {
    protocol_version: 3 | 4;
    input_lane: "approved_native";
};
export type NativeComparisonRunCatalog = Omit<
    ComparisonRunCatalog,
    "version" | "protocol_version" | "input_lane" | "runs"
> & NativeProtocolTuple & {
    input_lane: "approved_native";
    runs: NativeComparisonRunMetadata[];
};
export type NativeComparisonRunStatus = Omit<
    ComparisonRunStatus,
    "version" | "protocol_version" | "input_lane" | "phase" | "error"
> & NativeProtocolTuple & {
    input_lane: "approved_native";
    phase:
        | ComparisonRunStatus["phase"]
        | "awaiting_confirmation"
        | "cleanup_required";
    error: (typeof nativeComparisonRunErrors)[number] | null;
    cleanup_required: boolean;
    cleanup_running: boolean;
    cause: (typeof nativeComparisonRunErrors)[number] | null;
};
export function checkedNativeComparisonRunStatus(
    value: unknown,
): NativeComparisonRunStatus {
    const result = exact(detached(value, 32 * 1024), [
        "version",
        "kind",
        "protocol_version",
        "input_lane",
        "client_id",
        "run_id",
        "run_token",
        "operation_id",
        "comparison_kind",
        "batch",
        "phase",
        "running",
        "error",
        "completed_scenes",
        "completed",
        "report_ready",
        "source_matches",
        "cleanup_required",
        "cleanup_running",
        "cause",
    ]);
    wire(
        ((result.version === 2 && result.protocol_version === 3) ||
            (result.version === 3 && result.protocol_version === 4)) &&
            result.kind === "comparison_run" &&
            result.input_lane === "approved_native",
    );
    [result.client_id, result.run_id, result.run_token].forEach(
        comparisonRunUuid,
    );
    if (result.operation_id !== null) number(result.operation_id, 1);
    comparisonRunKind(result.comparison_kind);
    comparisonRunBatch(result.batch);
    choice(result.phase, [
        "retained",
        "starting",
        "running",
        "opening",
        "stopping_at_boundary",
        "paused",
        "completed",
        "failed",
        "closed",
        "awaiting_confirmation",
        "cleanup_required",
    ]);
    if (result.error !== null) choice(result.error, nativeComparisonRunErrors);
    if (result.cause !== null) choice(result.cause, nativeComparisonRunErrors);
    number(result.completed_scenes, 0, 4);
    [
        result.running,
        result.completed,
        result.report_ready,
        result.cleanup_required,
        result.cleanup_running,
    ].forEach(boolean);
    if (result.source_matches !== null) boolean(result.source_matches);
    // No relationship among phases, readiness, running and cleanup is invented.
    return result as NativeComparisonRunStatus;
}
export function checkedNativeComparisonRunCatalog(
    value: unknown,
): NativeComparisonRunCatalog {
    const result = exact(detached(value, 64 * 1024), [
        "version",
        "kind",
        "protocol_version",
        "input_lane",
        "runs",
        "max_new_scenes",
    ]);
    wire(
        ((result.version === 2 && result.protocol_version === 3) ||
            (result.version === 3 && result.protocol_version === 4)) &&
            result.kind === "comparison_run_catalog" &&
            result.input_lane === "approved_native" &&
            result.max_new_scenes === 4,
    );
    const rows = result.runs;
    wire(Array.isArray(rows) && rows.length <= 32);
    const seen = new Set<string>();
    for (const row of rows) {
        const metadata = exact(row, [
            "run_id",
            "client_id",
            "comparison_kind",
            "initial_batch",
            "created_ms",
            "protocol_version",
            "input_lane",
        ]);
        const id = comparisonRunUuid(metadata.run_id);
        wire(!seen.has(id));
        seen.add(id);
        comparisonRunUuid(metadata.client_id);
        comparisonRunKind(metadata.comparison_kind);
        comparisonRunBatch(metadata.initial_batch);
        number(metadata.created_ms);
        wire(
            metadata.protocol_version === result.protocol_version &&
                metadata.input_lane === "approved_native",
        );
    }
    return result as NativeComparisonRunCatalog;
}
