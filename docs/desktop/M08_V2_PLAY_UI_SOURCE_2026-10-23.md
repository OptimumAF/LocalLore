# V2 Play and read-only inspection source contract — 2026-10-23

Refs #12 M08.03/.06, #26 D05.01–.07 partial, #30 D08.04/.05 consumer prerequisites.
Base `a9f79b760ec6ff20f85a6e2d788c09b327f6aade`, isolated
`impl/m08-v2-play-ui` / `source-v2-play-ui`. Only four NEW paths: controller,
`V2PlayPanel.tsx`, standalone checker and this document. Root owns existing
model/controller/main/App/style/Host/schema/global guards and integration.

## Frozen interface before implementation

`V2PlayController(gateway: Gateway, refreshRoot: () => Promise<void>, prefix?)`
exports `get`, `subscribe`, `selectedContextChanged`, `setDraft`, `refresh`,
`send`, `cancel`, `retryExact`, `status`, `readQuery`, `page`, `source`, `dispose`.
Root supplies actual coherent session/scope/revision/player/view/observer,
persistence, other-work pending/blocked flags, playMode/inputKind/action/fakeMode.
Own pending/uncertain state is exposed separately for Root's global mutation
guards: feeding it back as other-work would incorrectly retire its own operation.

Current native thin Snapshot2 and Query2 use existing closed decoders. State holds
one current thin snapshot, bounded history/inspection page, bounded current draft,
one exact operation identity/request and actual last status/receipt. No fabricated
legacy Context, full canonical ledger, alternate inference or persistence. Root
routes only an actual Domain2 thin view to this panel and retains existing
advanced controls elsewhere.

Reserve request before subscriber notification; retain original session/scope/
head/key/full request on unknown acknowledgement across context retirement.
Passive status/cancel target that original identity. Exact explicit retry reuses
its request/key; a different new turn cannot pass an unresolved barrier. Every
session/scope/head/view/observer/input/control transition fences late reads and
further prepare/commit, while canonical committed result latches before any late
cancel. A malformed result never proves cancellation or releases uncertainty.
No context-change auto-admission, automatic retry, canonical rollback or new key.

Status/receipt decoding is bounded transport validation of actual Rust serde
shapes, exact request/scope/sequence binding and plain provenance data. Rust owns
all canonical/semantic checks. No stricter invented legacy Play version policy,
duplicate raw JSON key claim or competing outcome validator is introduced.

Read-only query uses selected child scope and actual completed historical boundary.
A scoped source retains its original scope/sequence separately; only an actual
returned event with both identities may be labelled matched. Source sequence is
not assumed to be a completed turn boundary. NPC/private inspection never changes
the actor/knowledge used by generation, and Player marker never appears as NPC
generation content. Play uses Player lens; Story Lab uses Root's granted lens.

## Frozen checker and evidence limits

The standalone Node checker freezes accepted/rejected actions, local unavailable
model without fixture fallback, pending/cancel-before-ack, exact lost-ack retry,
uncertainty across session/context changes, committed-before-late-cancel,
malformed receipt, all control/read fences, readonly nine-view inspection,
original-scope source matching and subscriber reentrancy. It executes the SAME
new controller through a synthetic Gateway. Those are mock scheduling results,
not actual Host/Core/IPC/render/model acceptance. Root's separate actual producer
capture/strict decoder evidence is not relabelled controller or rendering proof.

At the initial freeze, all new code was UNCOMPILED/UNRUN. No Node/Cargo/app/SQLite/provider/model/
device/browser/desktop execution is authorized here. Root owns execution,
existing-file integration, concrete consumer fixes and native rendering checks.

Initial fourteen-case checker/contract freeze:
`d0e7a9ff5818f33bf3a378aecf01f419e46192f1`, before controller/panel source.
Six additive source oracles preserve all original assertions and cover approved
Root head reconciliation/receipt retention, retired-status errors, coherent
custom-player binding, unresolved-ack cancel recovery, other-work admission
guards and private-query observer races. These additions are source-only; no
RED/GREEN execution is claimed. The existing source case also now checks a
wrong-original-scope event cannot be called a match.

Approved refresh handshake: `refresh(reconcile=true)` invokes the injected Root
callback once before capturing the new coherent context. Root callback refreshes
its existing controller/library only and MUST NOT call V2.refresh. Passive panel
context effects use `refresh(false)`; actual committed completion uses refresh()
once. Preserve actual last receipt/status across same-session/scope head advance
only when the new head includes its accepted final sequence; other lens/session/
scope presentations are cleared. Source links may pass their exact current bound
page to preserve its completed boundary; stale page objects cannot navigate.

## Coordinator first execution and typing correction

Root imported implementation `d646b383e7ee3748b560bce812b4cb76bbb9ea6b` as
`904d8f4` and actually ran the standalone synthetic Gateway checker: **20/20 PASS**.
This is controller scheduling evidence, not IPC, rendering or real inference.
Root's first strict TypeScript pass then failed with eight errors in this new
controller: unknown-string/array narrowing and consequent callback parameter
typing, retained in `author-v2-ui-types-first.log`; checker evidence is retained
in `v2-play-ui-first.log`. These results are attributed to Root, not this agent.

The minimal source correction changes the throwing `wire` helper from an inferred
const function binding to a function declaration with explicit `never` return.
That lets TypeScript recognize its terminating control flow for existing guards.
No runtime check, assertion, cap, request shape or oracle changes; no `any` cast.
This correction is source-only and has not been typechecked or executed by this
agent. Root owns the actual strict rerun and all IPC/render/native qualification.
