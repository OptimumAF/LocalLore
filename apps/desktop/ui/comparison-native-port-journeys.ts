// SOURCE ONLY / UNRUN: fixed app-owned native IPC checks, not a native UI,
// model, OS-dialog or quality qualification. Root wires and executes the helper.
import { checkedComparisonRunStatus } from "./comparison-run-model";
import type { ComparisonRunStatus } from "./comparison-run-model";
import { checkedSelectedCleanup } from "./selected-evaluation-model";

export type NativeComparisonPortPhase =
    "lab_denied" | "empty_native" | "scripted_open";

type Invoke = (
    name: string,
    args?: Record<string, unknown>,
) => Promise<unknown>;
type Check = (condition: unknown, name: string) => void;
// Issued native UUIDs are random v4. This fixed valid-shape value is never an
// app-created run/client/token in the fresh, owned synthetic harness workspace.
const UNKNOWN = "ffffffff-ffff-ffff-ffff-ffffffffffff";

export async function nativeComparisonPortChecks({
    invoke,
    check,
    phase,
    scripted,
}: {
    invoke: Invoke;
    check: Check;
    phase: NativeComparisonPortPhase;
    scripted?: ComparisonRunStatus;
}): Promise<void> {
    const call = (action: string, query: unknown) =>
        invoke("evaluation_comparison_native", { action, query });
    const refused = async (
        action: string,
        query: unknown,
        expected:
            "Forbidden" | "InvalidEvaluationInput" | "UnknownEvaluationRun",
        label: string,
    ) => {
        let code = "NoError";
        try {
            await call(action, query);
        } catch (error) {
            const value =
                typeof error === "string"
                    ? error
                    : error instanceof Error
                      ? error.message
                      : "UnknownNativeError";
            code = value.length <= 64 ? value : "UnknownNativeError";
        }
        // No error-buffer injection, reset, private error prose or simulated
        // response. The expected category comes from the actual native reply.
        check(code === expected, `native-port-${phase}-${label}`);
    };
    const emptyCatalog = async () => {
        const raw = await call("catalog", {});
        const text = JSON.stringify(raw);
        if (typeof text !== "string")
            throw Error("NativeComparisonPortCatalogWire");
        check(
            new TextEncoder().encode(text).length <= 64 * 1024,
            `native-port-${phase}-catalog-byte-bound`,
        );
        const value: unknown = JSON.parse(text);
        check(
            value !== null &&
                typeof value === "object" &&
                !Array.isArray(value),
            `native-port-${phase}-catalog-object`,
        );
        const catalog = value as Record<string, unknown>;
        const keys = [
            "version",
            "kind",
            "protocol_version",
            "input_lane",
            "runs",
            "max_new_scenes",
        ];
        check(
            Object.keys(catalog).length === keys.length &&
                keys.every((key) => Object.hasOwn(catalog, key)),
            `native-port-${phase}-catalog-closed-keys`,
        );
        check(
            catalog.version === 2 &&
                catalog.kind === "comparison_run_catalog" &&
                catalog.protocol_version === 3 &&
                catalog.input_lane === "approved_native" &&
                catalog.max_new_scenes === 4,
            `native-port-${phase}-catalog-native-version-tags`,
        );
        check(
            Array.isArray(catalog.runs) && catalog.runs.length === 0,
            `native-port-${phase}-catalog-has-no-native-execution`,
        );
    };

    if (phase === "lab_denied") {
        await refused("catalog", {}, "Forbidden", "actual-lab-grant-required");
        for (const action of ["cleanup_status", "retry_cleanup"] as const) {
            const cleanup = checkedSelectedCleanup(await call(action, {}));
            check(
                !cleanup.cleanup_required &&
                    !cleanup.running &&
                    cleanup.error === null,
                `native-port-lab-denied-${action}-actual-empty-cleanup-without-lab`,
            );
        }
        await refused(
            "catalog",
            "{}",
            "InvalidEvaluationInput",
            "query-string-rejected-before-host",
        );
        // Deliberately use non-generating catalog, never even a malformed start
        // whose accidentally ignored extra field could reach a native dialog.
        await refused(
            "catalog",
            { provider: "native" },
            "InvalidEvaluationInput",
            "renderer-provider-key-rejected-before-host",
        );
        await refused(
            "catalog",
            { nativeConsent: true },
            "InvalidEvaluationInput",
            "renderer-consent-key-rejected-before-host",
        );
        return;
    }
    if (phase === "empty_native") {
        await emptyCatalog();
        await refused(
            "lookup",
            { clientId: UNKNOWN },
            "UnknownEvaluationRun",
            "unknown-client-lookup",
        );
        await refused(
            "open",
            { runId: UNKNOWN },
            "UnknownEvaluationRun",
            "unknown-run-open",
        );
        await refused(
            "status",
            { runToken: UNKNOWN },
            "UnknownEvaluationRun",
            "unknown-token-status",
        );
        await refused(
            "close",
            { runToken: UNKNOWN },
            "UnknownEvaluationRun",
            "unknown-token-close",
        );
        await refused(
            "managed",
            { clientId: UNKNOWN, runId: UNKNOWN },
            "UnknownEvaluationRun",
            "unknown-managed-before-read-consent",
        );
        await emptyCatalog();
        return;
    }
    if (phase === "scripted_open") {
        // This input must be the actual existing controller's completed native
        // scripted-service reply. Its normal decoder checks the legacy wire.
        const original = checkedComparisonRunStatus(scripted);
        check(
            original.completed &&
                original.report_ready &&
                !original.running &&
                original.phase === "completed",
            "native-port-scripted-open-requires-actual-completed-scripted-status",
        );
        await refused(
            "lookup",
            { clientId: original.client_id },
            "UnknownEvaluationRun",
            "scripted-client-is-not-native",
        );
        await refused(
            "status",
            { runToken: original.run_token },
            "UnknownEvaluationRun",
            "scripted-token-is-not-native",
        );
        await refused(
            "close",
            { runToken: original.run_token },
            "UnknownEvaluationRun",
            "native-close-cannot-revoke-scripted-token",
        );
        // Sole additional command authorized by Root: fixed read-only status of
        // the supplied validated scripted token. No execution or read grant.
        const current = checkedComparisonRunStatus(
            await invoke("evaluation_comparison_run", {
                action: "status",
                query: { runToken: original.run_token },
            }),
        );
        for (const key of Object.keys(
            original,
        ) as (keyof ComparisonRunStatus)[]) {
            check(
                current[key] === original[key],
                `native-port-scripted-status-preserved-${key}`,
            );
        }
        await emptyCatalog();
        return;
    }
    throw Error("NativeComparisonPortPhaseInvalid");
}
