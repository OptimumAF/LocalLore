# Future desktop V2 decoder — source handoff

2026-10-23. Partial #12 M08.03, #30 D08.05 and #26 D05.01/.03/.04/.06/.07.
**SOURCE ONLY / UNRUN. No current PR131 changes or app exposure.**

Base `95db6af97107ba52918885759441a9a4eca953b6`; separate branch
`impl/m08-desktop-v2-decoder`, worktree `source-desktop-v2-decoder`.
Own ONLY NEW `apps/desktop/ui/v2-view-model.ts`,
`apps/desktop/check-v2-view-model.mjs`, and this report. Claims:
[#12](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6378599226),
[#30](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6378599372),
[#26](https://github.com/OptimumAF/LocalLore/issues/26#issuecomment-6378599590).

## Exact pre-implementation contract

Producer references are thin Host `903d8803b4b026a8de35df4f4220038b56275bdd`,
thin-view source oracles `f217061827fed1cba5002c3c0409fde6d36f4947`, and Query2
scoped-message/Player-marker source `8d46402a444de8feb9c96ed6a2655ba0ae639a57`.
They are inspected source, not execution of those producers in this worktree.

The standalone module exports closed DTO types plus:

```text
checkedPlaySnapshotV2(value:unknown, scope:ScopeV2, revision:number): PlaySnapshotV2
checkedPageV2(value:unknown, query:InspectionQueryV2): InspectionPageV2
```

Both return a detached validated JSON copy or throw `Error("Wire")`. The thin
snapshot has exactly seven fields: version2, domain_version1|2, scope, revision,
rules, player{observer,self_state}, inventory. Player is thin actual Actor state;
inventory entries must belong to that observer. Knowledge, receipts, author
reason/truth/bindings and arbitrary extra fields are refused.

Query/Page versions are exactly2; every request binding is checked. Existing
Rust caps are Page65536 bytes, at most64 rows, cursor128 bytes, search256 bytes;
Host snapshot262144 bytes. Integers must be safe JS integers. Source event IDs
are positive and at most the inspected revision. Inherited original branch IDs
are allowed within the same story; Rust alone establishes actual lineage and
eligibility. Source serde shape is **content-tagged**:
`{kind:"scoped_event",value:{original_scope,sequence}}`, never flattened.

ScopedMessage uses actual producer fields only; legacy Message is rejected in
Page2. Marker is exactly `{kind:"author_correction",revision}` and only allowed
for literal Player + History. No key/origin is added to its wire DTO. NPC rows
cannot include prose. Granted Omniscient may include already eligible prose but
no marker. KnownAsObserved is a distinct closed origin. Row keys and scoped
message/event/marker identities must be unique within a page. Cursor syntax is
`2:<positive offset>:<64 lowercase hex>`, not a new literal `v2` format; the
decoder does not authenticate cursor hashes or canonical authority.

Actual Rust Actor bounds: energy0..100, attribute values-100..100, ability
ranks1..65535; Item quantity1..65535, nullable return_to and boolean healing.
Narrative profile requires empty abilities/attributes and zero energy. Actor
name/set strings have no invented2048-byte per-field limit; the actual overall
Host cap applies. Sets reject duplicates. Other numeric DTO fields follow their
closed Rust types and safe-integer transport limit.

Literal HTML/control characters and valid Unicode remain inert string data.
The module has no DOM, eval, file, network, shell or renderer API. Lone UTF16
surrogates are refused because Rust strings cannot serialize them. The decoder
checks own data descriptors, plain/null prototypes and rejects accessors,
symbols, cycles, holes and non-JSON values. Actual valid map IDs including
`constructor` and `__proto__` remain own data keys in a detached JSON copy;
there is no assignment/merge into a prototype. This is validation of transport
JSON values, not a sandbox for arbitrary JavaScript Proxy traps.

**Raw duplicate JSON object members cannot be detected after a transport parser
has overwritten them.** These value-taking functions do not claim otherwise.
Raw-text duplicate-member refusal remains a transport/parser prerequisite;
duplicate set members and wire identities are checked here. Unknown raw author
fields and malformed closed DTO/source/effect variants fail closed.

## Frozen oracles and qualification boundary

Independent synthetic wire checker frozen BEFORE module source in commit
`b99e040d0c1009f90f3f88b027b50d5250a11006`, SHA-256
`97ed3c572f19bf3c270746917c1d1edab7de2de741f20f522dea9d4d3c78e0a3`.
It covers exact thin state, both domains/profiles, actual bounds, detached-copy
behavior, valid special dictionary names, invalid prototypes/getters/cycles,
source tagging/observer/head/history binding, inherited scopes/same-turn
identity, marker privacy, legacy-message refusal, caps/cursors, duplicate
identities/sets, literal HTML/control/Unicode, and supported row families.
Every fixture is synthetic wire data, **not actual native/Core JSON evidence**.

No Node/parser/type-check, Cargo/Gradle, app/browser/native, model/provider,
device/ADB/CUA/desktop or protected-resource execution is authorized. Only
source/Git/hash/whitespace checks are permitted. Do not label these tests RED,
GREEN, native IPC or rendering evidence before actual execution. Existing
query1 decoder, bindings, controllers, UI, schema, package scripts and test
runners are untouched. Root later owns actual action/render integration,
source-bound producer fixtures, decoder execution and consumer parity.
