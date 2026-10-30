import type { V2PlayController, V2PlayState } from "./v2-play-controller";

interface FocusTicket {
    settled(): void;
    cancel(): void;
}
interface Owner {
    controller: V2PlayController;
    button: HTMLButtonElement;
    context: NonNullable<V2PlayState["context"]>;
    snapshot: NonNullable<V2PlayState["snapshot"]>;
    document: Document;
    view: Window;
}
const inert: FocusTicket = { settled() {}, cancel() {} };

/** Own one pager interaction, never its data or a later read's focus. */
export function beginInspectionPagingFocus(
    controller: V2PlayController,
    button: HTMLButtonElement | null | undefined,
    context: V2PlayState["context"],
    snapshot: V2PlayState["snapshot"],
    direction: "previous" | "next",
): FocusTicket {
    const document = button?.ownerDocument;
    const view = document?.defaultView;
    const initial = controller.get();
    if (
        !button ||
        !document ||
        !view ||
        !context ||
        !snapshot ||
        typeof view.requestAnimationFrame !== "function" ||
        typeof view.cancelAnimationFrame !== "function" ||
        !button.isConnected ||
        button.disabled ||
        document.activeElement !== button ||
        initial.context !== context ||
        initial.snapshot !== snapshot ||
        !initial.inspectionPaging.bound ||
        initial.inspectionPaging.navigating !== null ||
        initial.readBusy ||
        initial.queryBusy ||
        initial.pending ||
        initial.uncertain ||
        context.pending ||
        context.blocked ||
        (direction !== "previous" && direction !== "next")
    )
        return inert;

    let owner: Owner | null = {
        controller,
        button,
        context,
        snapshot,
        document,
        view,
    };
    let phase: "armed" | "pending" | "complete" = "armed";
    let notifications = 0;
    let seen = new WeakSet<object>();
    let frame: number | null = null;
    let settledOnce = false;
    let unsubscribe = () => {};

    function cancel() {
        const current = owner;
        if (!current) return;
        owner = null;
        unsubscribe();
        unsubscribe = () => {};
        current.document.removeEventListener("focusin", intent, true);
        current.document.removeEventListener("pointerdown", intent, true);
        if (frame !== null) current.view.cancelAnimationFrame(frame);
        frame = null;
        seen = new WeakSet<object>();
    }
    function currentState(): V2PlayState | null {
        if (!owner) return null;
        const state = owner.controller.get();
        if (
            state.context !== owner.context ||
            state.snapshot !== owner.snapshot ||
            !state.inspectionPaging.bound ||
            state.readBusy ||
            state.pending ||
            state.uncertain ||
            owner.context.pending ||
            owner.context.blocked
        ) {
            cancel();
            return null;
        }
        return state;
    }
    function intent(event: Event) {
        if (!currentState() || !owner) return;
        if (event.type === "focusin" && event.target === owner.document.body)
            return;
        let owned = event.target === owner.button;
        try {
            owned ||= owner.button.contains(event.target as Node | null);
        } catch {
            /* Unknown target cannot authorize restoring focus. */
        }
        if (!owned) cancel();
    }
    function observe() {
        const state = currentState();
        if (!state) return;
        // Recursive delivery may expose the same newer public state twice.
        // Weak identities retain no bodies; ordinary get rechecks do not count.
        if (++notifications > 64 || seen.has(state)) {
            cancel();
            return;
        }
        seen.add(state);
        if (state.queryBusy) {
            if (
                phase === "complete" ||
                state.inspectionPaging.navigating !== direction
            )
                cancel();
            else phase = "pending";
        } else if (state.inspectionPaging.navigating !== null) cancel();
        else if (phase === "pending") phase = "complete";
    }
    function settled() {
        if (settledOnce || !owner) return;
        settledOnce = true;
        const state = currentState();
        if (!state || !owner) return;
        if (
            phase !== "complete" ||
            state.queryBusy ||
            state.inspectionPaging.navigating !== null
        ) {
            cancel();
            return;
        }
        frame = owner.view.requestAnimationFrame(() => {
            frame = null;
            const live = currentState();
            try {
                if (
                    live &&
                    owner &&
                    phase === "complete" &&
                    !live.queryBusy &&
                    live.inspectionPaging.navigating === null &&
                    owner.button.isConnected &&
                    !owner.button.disabled &&
                    owner.document.activeElement === owner.document.body
                )
                    owner.button.focus({ preventScroll: true });
            } finally {
                cancel();
            }
        });
    }
    const ticket = { settled, cancel };
    unsubscribe = controller.subscribe(observe);
    if (!owner) {
        unsubscribe();
        return ticket;
    }
    document.addEventListener("focusin", intent, true);
    document.addEventListener("pointerdown", intent, true);
    return ticket;
}
