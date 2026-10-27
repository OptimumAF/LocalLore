import type { Controller } from "./controller";
import type { MemoryInspectionContext } from "./memory-inspection-model";

// Presentation eligibility only. The native Host independently enforces its
// grant, selected session, exact source/head and explicit Player request.
export function memoryInspectionContext(
    controller: Pick<Controller, "get" | "selected">,
    epoch: number,
    labGranted: boolean,
): MemoryInspectionContext | null {
    const state = controller.get(),
        selected = controller.selected(),
        play = state.play ?? state.playV2;
    if (
        state.disposed ||
        !selected ||
        !play ||
        selected.scope.story !== play.scope.story ||
        selected.scope.branch !== play.scope.branch ||
        selected.revision !== play.revision
    )
        return null;
    return {
        session: selected.id,
        scope: { ...selected.scope },
        expected_head: play.revision,
        player: play.player.observer,
        observer:
            state.observer === "player" ? play.player.observer : state.observer,
        view: state.view,
        epoch,
        persistent: state.workspace?.persistent === true,
        domainVersion: state.playV2?.domain_version ?? 1,
        // The selector's Player variant is authoritative for presentation;
        // a character with an equal native ID must not be silently promoted.
        lab: labGranted && state.view === "lab" && state.observer === "player",
    };
}
