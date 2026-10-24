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

ALL new code is currently UNCOMPILED/UNRUN. No Node/Cargo/app/SQLite/provider/model/
device/browser/desktop execution is authorized here. Root owns execution,
existing-file integration, concrete consumer fixes and native rendering checks.
