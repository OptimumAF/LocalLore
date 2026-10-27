// Development journey abort only. Denial ACK is required before releasing a hold.
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
        const denial = await invoke("harness_native_comparison_case", {
            scenario: "deny-execution-consent",
        });
        if (
            !denial ||
            typeof denial !== "object" ||
            Array.isArray(denial) ||
            Object.keys(denial).length !== 5 ||
            !["version", "kind", "synthetic", "active", "held"].every((key) =>
                Object.hasOwn(denial, key),
            )
        )
            throw Error("NativeConsentAbortAckInvalid");
        const ack = denial as Record<string, unknown>;
        if (
            ack.version !== 1 ||
            ack.kind !== "native_full_comparison_fixture" ||
            ack.synthetic !== true ||
            typeof ack.active !== "boolean" ||
            ack.held !== true
        )
            throw Error("NativeConsentAbortAckInvalid");
        // close() reports transport errors in controller state as well as through
        // rejection. Its resolved Promise alone never proves cleanup.
        try {
            await full.close();
            const state = full.get();
            if (
                state.uncertain ||
                state.error ||
                (state.mode === "approved_native" &&
                    (state.cleanupUncertain ||
                        state.cleanupError ||
                        state.cleanupPending ||
                        state.cleanup?.cleanup_required ||
                        state.cleanup?.running))
            )
                cleanupUnconfirmed = true;
        } catch {
            cleanupUnconfirmed = true;
        }
        // Only an acknowledged, armed denial reaches release. Unknown denial
        // delivery keeps the native hold and relies on disposal/its deadline.
        await invoke("harness_native_comparison_case", {
            scenario: "release-execution-consent",
        });
        released = true;
    } catch {
        cleanupUnconfirmed = true;
    } finally {
        try {
            await dispose();
        } catch {
            cleanupUnconfirmed = true;
        }
    }
    return { released, cleanupUnconfirmed };
}
