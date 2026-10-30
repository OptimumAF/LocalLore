// Development-only report transport. Canonical proof remains in Rust.
const mode = "domain2_fork_v1";
const labels = [
    "catalog",
    "rejected",
    "pending",
    "preauthor",
    "authored",
    "recovered",
    "enlarged",
].map((label) => `d08-fork-${label}`);
const failureLabel = "d08-fork-failure";
const reportLimit = 262144;
type Report = Record<string, unknown>;
type Category =
    | "D08ForkReportInvalid"
    | "D08ForkCheckpointSummary"
    | "D08ForkFinalReportBudget";
function invalid(category: Category): never {
    throw Error(category);
}
function object(value: unknown): value is Report {
    return value !== null && typeof value === "object" && !Array.isArray(value);
}
function exact(value: Report, keys: string[]) {
    return Object.keys(value).sort().join("\0") === [...keys].sort().join("\0");
}
function validate(value: unknown): asserts value is Report {
    if (
        !object(value) ||
        value.synthetic !== true ||
        value.mode !== mode ||
        typeof value.passed !== "boolean"
    )
        invalid("D08ForkReportInvalid");
    if (!Array.isArray(value.captures)) invalid("D08ForkCheckpointSummary");
    const captures = value.captures;
    const hasFailure = captures.at(-1) === failureLabel;
    const count = captures.length - Number(hasFailure);
    if (
        count < 0 ||
        count > labels.length ||
        captures.length > 8 ||
        (value.passed && (hasFailure || count !== labels.length))
    )
        invalid("D08ForkCheckpointSummary");
    for (let i = 0; i < count; i++)
        if (captures[i] !== labels[i]) invalid("D08ForkCheckpointSummary");
    const summary = value.scrollObservations;
    if (
        !object(summary) ||
        !exact(summary, ["retainedInCheckpoints", "total", "checkpoints"]) ||
        summary.retainedInCheckpoints !== true ||
        !Number.isSafeInteger(summary.total) ||
        (summary.total as number) < 0 ||
        (summary.total as number) > 168 ||
        !Array.isArray(summary.checkpoints) ||
        summary.checkpoints.length !== count
    )
        invalid("D08ForkCheckpointSummary");
    let total = 0;
    for (let i = 0; i < count; i++) {
        const row: unknown = summary.checkpoints[i];
        if (
            !object(row) ||
            !exact(row, ["label", "json", "count"]) ||
            row.label !== labels[i] ||
            row.json !== `${labels[i]}.json` ||
            !Number.isSafeInteger(row.count) ||
            (row.count as number) < 1 ||
            (row.count as number) > 24
        )
            invalid("D08ForkCheckpointSummary");
        total += row.count as number;
    }
    if (summary.total !== total) invalid("D08ForkCheckpointSummary");
}
function detached(value: unknown): Report {
    validate(value);
    let compact: string;
    let report: unknown;
    try {
        compact = JSON.stringify(value);
        report = JSON.parse(compact);
    } catch {
        return invalid("D08ForkReportInvalid");
    }
    validate(report);
    const utf8 = new TextEncoder();
    if (
        utf8.encode(compact).length > reportLimit ||
        utf8.encode(JSON.stringify(report, null, 2)).length > reportLimit
    )
        invalid("D08ForkFinalReportBudget");
    return report;
}
function fallback(failureCategory: string): Report {
    return {
        synthetic: true,
        mode,
        passed: false,
        originalPassed: false,
        detailReportUnavailable: true,
        failureCategory,
        noFinalStateProof: true,
    };
}
export function createDomain2ForkFinalizer(
    finish: (report: Report) => Promise<unknown>,
) {
    let pending: Promise<unknown> | null = null;
    // Assign the shared promise before normalization or any caller callback.
    return (input: unknown): Promise<unknown> => {
        if (pending) return pending;
        pending = Promise.resolve().then(async () => {
            let report: Report;
            try {
                report = detached(input);
            } catch (error) {
                const category =
                    error instanceof Error &&
                    [
                        "D08ForkReportInvalid",
                        "D08ForkCheckpointSummary",
                        "D08ForkFinalReportBudget",
                    ].includes(error.message)
                        ? error.message
                        : "D08ForkReportInvalid";
                return finish(fallback(category));
            }
            try {
                return await finish(report);
            } catch {
                // Failure here remains failure; a rejected fallback propagates.
                return finish(fallback("D08ForkFinishRejected"));
            }
        });
        return pending;
    };
}
