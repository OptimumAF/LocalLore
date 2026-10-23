import type { Controller } from "./controller";
import type { MemoryContext } from "./memory-maintenance-controller";
export function memoryContext(
    c: Pick<Controller, "get" | "selected">,
    epoch: number,
): MemoryContext | null {
    const s = c.get(),
        selected = c.selected(),
        play = s.play;
    if (
        !selected ||
        s.disposed ||
        !play ||
        play.scope.story !== selected.scope.story ||
        play.scope.branch !== selected.scope.branch
    )
        return null;
    return {
        session: selected.id,
        scope: { ...selected.scope },
        expected_head: play.revision,
        player: play.player.observer,
        observer:
            s.view === "play" || s.observer === "player"
                ? play.player.observer
                : s.observer,
        view: s.view,
        epoch,
        persistent: s.workspace?.persistent === true,
    };
}
