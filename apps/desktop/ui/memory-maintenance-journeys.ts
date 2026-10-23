// Development-only fixed synthetic journey; coordinator imports only from its harness.
// The normal application must never import this file.
import { MemoryMaintenanceController } from "./memory-maintenance-controller";
import type { MemoryContext } from "./memory-maintenance-controller";

export async function runMemoryMaintenanceJourney(
    controller: MemoryMaintenanceController,
    context: MemoryContext,
    checkpoint: (name: string) => Promise<void>,
) {
    if (context.scope.story !== "memory-controls-synthetic" || context.expected_head !== 1)
        throw Error("SyntheticFixtureRequired");
    controller.contextChanged(context);
    async function observe() {
        const deadline = performance.now() + 20_000;
        while (controller.get().operation?.running) {
            if (performance.now() >= deadline) throw Error("SyntheticOperationDeadline");
            await new Promise(resolve => setTimeout(resolve, 25));
            await controller.act("status");
            if (controller.get().error || controller.get().uncertain) throw Error("SyntheticObservationUnavailable");
        }
        if (controller.get().error || controller.get().uncertain) throw Error("SyntheticObservationUnavailable");
    }
    async function action(value: "status" | "admit" | "cancel" | "prune" | "step") {
        if (!controller.can(value)) throw Error("SyntheticActionUnavailable");
        await controller.act(value);
        await observe();
    }
    await action("status");
    if (controller.get().reply?.maintenance.job !== null) throw Error("SyntheticFixtureNotFresh");
    await checkpoint("memory-native-passive-status");
    controller.consent(true);
    await action("admit");
    if (controller.get().reply?.maintenance.job?.status !== "ready") throw Error("SyntheticAdmissionMissing");
    await checkpoint("memory-native-admitted");
    await action("cancel");
    if (controller.get().reply?.maintenance.job?.status !== "cancelled") throw Error("SyntheticCancellationMissing");
    await checkpoint("memory-native-cancelled");
    controller.consent(true);
    await action("prune");
    if (controller.get().reply?.maintenance.job !== null) throw Error("SyntheticPruneMissing");
    await checkpoint("memory-native-pruned");
    controller.consent(true);
    await action("admit");
    await action("step");
    if (controller.get().reply?.maintenance.job?.status !== "complete") throw Error("SyntheticChunkIncomplete");
    await checkpoint("memory-native-one-chunk-complete");
}
