// Development-only fixed browser finalization; no native authority or I/O policy.
const MODE = "domain2_timeline_browser_v1";
const MAX_REPORT_BYTES = 262144;
const LABELS = [
    "d08-browser-catalog",
    "d08-browser-root",
    "d08-browser-child",
    "d08-browser-observer",
    "d08-browser-enlarged-wide",
    "d08-browser-enlarged-narrow",
] as const;
const HOST_READS = new Set([
    "workspace",
    "branches",
    "resume",
    "open",
    "close",
    "play_snapshot",
    "play_snapshot_v2",
    "inspection_query",
    "inspect",
    "trace_capture_revoke",
]);
const NATIVE_READS = new Set([
    "model_status",
    "inspection_storage",
    "capture_revoke",
]);
const REPORT_ERRORS = new Set([
    "D08BrowserReportInvalid",
    "D08BrowserCheckpointSummary",
    "D08BrowserFinalReportBudget",
]);

export function browserReadOnlyCallAllowed(item: {
    channel: string;
    command: { op: string } | null;
    nativeAction: string | null;
}): boolean {
    if (!item || typeof item !== "object") return false;
    if (item.channel === "host")
        return (
            item.nativeAction === null &&
            item.command !== null &&
            typeof item.command === "object" &&
            !Array.isArray(item.command) &&
            typeof item.command.op === "string" &&
            HOST_READS.has(item.command.op)
        );
    return (
        item.channel === "native" &&
        item.command === null &&
        typeof item.nativeAction === "string" &&
        NATIVE_READS.has(item.nativeAction)
    );
}

export function browserFinalReport(
    report: Record<string, unknown>,
    checkpoints: readonly { label: string; count: number }[],
): Record<string, unknown> {
    if (
        !report ||
        typeof report !== "object" ||
        Array.isArray(report) ||
        !["synthetic", "mode", "passed"].every((key) =>
            Object.hasOwn(report, key),
        ) ||
        report.synthetic !== true ||
        report.mode !== MODE ||
        typeof report.passed !== "boolean"
    )
        throw Error("D08BrowserReportInvalid");
    if (!Array.isArray(checkpoints) || checkpoints.length > LABELS.length)
        throw Error("D08BrowserCheckpointSummary");
    for (let index = 0; index < checkpoints.length; index++)
        if (!Object.hasOwn(checkpoints, index))
            throw Error("D08BrowserCheckpointSummary");
    let total = 0;
    const retained = checkpoints.map((entry, index) => {
        if (
            !entry ||
            typeof entry !== "object" ||
            Array.isArray(entry) ||
            Object.keys(entry).length !== 2 ||
            !Object.hasOwn(entry, "label") ||
            !Object.hasOwn(entry, "count") ||
            entry.label !== LABELS[index] ||
            !Number.isInteger(entry.count) ||
            entry.count < 0 ||
            entry.count > 16
        )
            throw Error("D08BrowserCheckpointSummary");
        total += entry.count;
        return {
            label: entry.label,
            count: entry.count,
            json: `${entry.label}.json`,
        };
    });
    if (
        total > 96 ||
        (report.passed &&
            (retained.length !== LABELS.length ||
                total !== 96 ||
                retained.some((entry) => entry.count !== 16)))
    )
        throw Error("D08BrowserCheckpointSummary");
    const value = {
        ...report,
        scrollObservations: {
            retainedInCheckpoints: true,
            total,
            checkpoints: retained,
        },
    };
    let compact: string | undefined, pretty: string | undefined;
    try {
        compact = JSON.stringify(value);
        pretty = JSON.stringify(value, null, 2);
        if (typeof compact !== "string" || typeof pretty !== "string")
            throw Error("D08BrowserReportInvalid");
    } catch {
        throw Error("D08BrowserReportInvalid");
    }
    const encoder = new TextEncoder();
    if (
        encoder.encode(compact).length > MAX_REPORT_BYTES ||
        encoder.encode(pretty).length > MAX_REPORT_BYTES
    )
        throw Error("D08BrowserFinalReportBudget");
    return value;
}

export async function browserFinish(
    invoke: (
        name: "harness_finish",
        args: { report: Record<string, unknown> },
    ) => Promise<unknown>,
    report: Record<string, unknown>,
    checkpoints: readonly { label: string; count: number }[],
): Promise<void> {
    try {
        const detailed = browserFinalReport(report, checkpoints);
        await invoke("harness_finish", { report: detailed });
    } catch (error) {
        const message = error instanceof Error ? error.message : "";
        await invoke("harness_finish", {
            report: {
                synthetic: true,
                mode: MODE,
                passed: false,
                originalPassed: false,
                detailReportUnavailable: true,
                failureCategory: REPORT_ERRORS.has(message)
                    ? message
                    : "D08BrowserFinishRejected",
                noFinalStateProof: true,
            },
        });
    }
}
