# D05 pager focus correction contract

Refs #26, D05.03/D05.07 supporting slice. Source proposal after actual native
failure atfa1d5e38; no new runtime or acceptance follows this document. Existing
frontend/native paging contracts, disabled controls, Rust authority and all
failed captures remain intact. Root accepts routine implementation only after
independent source review and different-author FIRST freeze.

## Observed defect

Actual mounted Next dispatches exactly one normal native inspection read, holds
the original control mounted, and displays the real second page. While pending,
native disabled state blurs the focused button to BODY. After completion, Next
is enabled but focus stays on BODY. The native assertion
next-second-no-row-or-unrelated-panel-focus-steal fails. Both generated app-owned
PNGs were individually inspected; this is actual WebView behavior, not an SSR
prediction. The enabled-completion assertion will not be relaxed.

## Small product boundary

Root owns new ui/v2-inspector-paging-focus.ts and existing V2PlayPanel.tsx, with
later verifier/report wiring. No controller, shared engine, Host, storage, wire,
observer or generation permission change. Only application DOM focus changes;
there is no desktop input/control, window activation or script/debug service.

The internal product export is:

```ts
beginInspectionPagingFocus(
    controller: V2PlayController,
    button: HTMLButtonElement | null | undefined,
    context: V2PlayState["context"],
    snapshot: V2PlayState["snapshot"],
    direction: "previous" | "next",
): { settled(): void; cancel(): void }
```

Use the exact real controller's get/subscribe only. Do not query, reset, validate
canon, read private controller fields or retain page bodies/cursors. Owner
references and small booleans identify one interaction; this is not a page cache.

Arm only if the supplied actual pager is focused, connected, enabled, and has a
live ownerDocument/defaultView, and public state has the captured nonnull context
and snapshot references, a bound idle frame, no read/query busy or gameplay block.
All other cases return an inert, idempotent ticket. SSR/no-event handler calls
must still perform their existing eligible action without requiring a DOM.

The panel keeps its existing livePager/current-owner/cursor guards. Each eligible
handler cancels its prior ticket, arms the new ticket before dispatch, calls its
one existing page(cursor) or previousInspectionPage() operation, and settles only
that ticket when that promise finishes. No new query, changed cursor or native
cancellation is introduced. Component cleanup cancels the ticket. At most one
active ticket is retained by the panel.

## Guarded lifecycle

During the interaction, listen to public controller notifications and only the
owner document's focusin and pointerdown. Automatic blur to BODY is not itself
cancellation. Focus to another focusable target or pointer intent on another
target cancels immediately; restoring focus must not override a user move.

Retire on context/snapshot reference replacement, disposal, unbound/reset/fresh
Read/source navigation, readBusy, gameplay pending/uncertainty/block or a navigation
direction that no longer belongs to this interaction. Observe the actual pending
direction once. After its first idle completion, another read/navigation retires
the old ticket, even if the old promise/animation frame runs late. Public-state
notifications must be observed directly, not inferred only from batched React
renders. Do not broaden this into a new data-authority or public-mutation API.

settled schedules at most one owner-document requestAnimationFrame only after
the owned navigation has actually begun and completed. Keep cancellation guards
live until that callback. Recheck context/snapshot/bound/idle/current interaction,
connected button and native disabled state. If focus is still BODY and the
original button is enabled, call its focus({preventScroll:true}). Already-focused
controls need no extra focus call. A different focused element always wins.

If the original button is disabled at a first/last boundary, do not focus a peer,
row or heading. Preserve and label the observed disabled-boundary behavior; this
small correction does not qualify that accessibility path. No invented focus
target, hidden tabindex or changed native disabled semantics.

cancel and completed callbacks clean up idempotently: remove controller/document
listeners, cancel any queued frame and prevent all late callbacks. No polling,
timer, frame loop, arbitrary selector or long-lived history of tickets. A stale
context, unmount or newer operation must never trigger an old focus effect.

## Independent tests and actual verification

The separate author owns only check-v2-inspector-paging-focus-review.mjs. Freeze
it before Root helper/panel production. Test actual future helper source with
disclosed DOM/rAF/state doubles; use actual-controller and actual panel handlers
where useful, without a copied focus policy or replacement panel. Source-only
authoring does not execute any checks or allocate fixtures/artifacts.

Cover automatic BODY blur, enabled success/error retry, initially unfocused or
detached/disabled/no-op controls, final disabled boundary, user focus/pointer moves,
reset/fresh Read/source/refresh/same-head replacement/lens/session/head/disposal,
newer navigation, unmount/cancel before queued callback, repeated settled/cancel
and complete bounded cleanup. Preserve all existing92 frontend,245 process and38
path checks and the actual native focus assertion. Missing module/registration is
UNRUN_SETUP, never zero-case PASS or an invented behavioral result.

Root must measure/declare a small frontend evidence allocation before running the
new FIRST and existing affected checks. A later separately admitted native
20-capture journey must exercise the real handlers/native IPC/WebView and inspect
every image. No new cohort is admitted here. Keep all prior packets and costs
under the original D05/selected4/joint/target caps; no cleanup or budget reset.
Physical keyboard/screen-reader, OS/process-tree isolation and whole D05/desktop
acceptance remain separate from simulated DOM or this native interaction slice.
