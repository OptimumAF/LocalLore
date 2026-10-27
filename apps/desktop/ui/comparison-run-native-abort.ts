// Development journey abort only. Extracted legacy behavior for frozen review oracles.
import type { ComparisonRunController } from "./comparison-run-controller";

export async function abortHeldNativeComparisonConsent({
    full,
    invoke,
    dispose,
}: {
    full: Pick<ComparisonRunController, "close" | "get">;
    invoke: (name: string, args?: Record<string, unknown>) => Promise<unknown>;
    dispose: () => Promise<void>;
}): Promise<{ released: boolean; cleanupUnconfirmed: boolean }> {
    let released = false,
        cleanupUnconfirmed = false;
    try {
        try {
            await full.close();
        } catch {
            cleanupUnconfirmed = true;
        }
        await invoke("harness_native_comparison_case", {
            scenario: "release-execution-consent",
        });
        released = true;
        await dispose();
    } catch {
        cleanupUnconfirmed = true;
    }
    return { released, cleanupUnconfirmed };
}
