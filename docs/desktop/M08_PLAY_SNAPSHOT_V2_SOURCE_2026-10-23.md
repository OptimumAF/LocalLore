# Future thin PlaySnapshotV2: frozen Host source contract

Date: 2026-10-23. Partial #12 M08.03 / #30 D08.05 / #26 prerequisites.
**Future source-only branch; excluded from the current first-foundation PR.**
Base `95db6af97107ba52918885759441a9a4eca953b6`, branch
`impl/m08-thin-play-snapshot-v2`, worktree `source-thin-play-snapshot-v2`.
Claims before writes: [#12 6378509772](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6378509772),
[#30 6378509932](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6378509932),
[#26 6378510093](https://github.com/OptimumAF/LocalLore/issues/26#issuecomment-6378510093).
Own only minimal existing `crates/locallore/src/host.rs`, NEW
`crates/locallore/tests/m08_play_snapshot_v2_review.rs` and this NEW document.
No Query/Core engine/Store/UI/schema/dependency/old test/fixture edits.

## Exact coordinator-frozen surface

Add HostCommand::PlaySnapshotV2 with operation `play_snapshot_v2` and exactly
the SAME three fields as legacy PlaySnapshot: session, scope, expected_revision.
Host envelope version remains1. The operation name identifies the new view;
there is **no request version field**, observer argument or grant flag. This
supersedes the earlier broad V2 Host/UI proposal's request.version2 and extra
player metadata for this thin snapshot only. Unknown/extra fields remain denied
by existing closed Envelope/HostCommand/Scope serde parsing.

```json
{"version":1,"command":{"op":"play_snapshot_v2","session":"session-1","scope":{"story":"synthetic","branch":"main"},"expected_revision":0}}
```

Successful data has EXACT keys:

```text
{
  version:2,
  domain_version:actual Engine.domain_version() (1|2),
  scope:actual selected scope,
  revision:actual selected current revision,
  rules:actual seed.profile,
  player:{observer:actual seed.player,self_state:actual state.actors[seed.player]},
  inventory:actual state.items filtered to owner == actual seed.player
}
```

The outer success envelope is unchanged version1/status ok/data. No extra
player version/scope/revision fields. No CharacterContextV2 materialization or
all-history allocation; no facts, beliefs, observations, receipts, author marker,
private canonical record, TruthSource, binding or author reason. This is native
player display state, not a generation/context port or inspection capability.
It works with either trusted native Story Lab grant value without altering
character knowledge. All detailed history/facts/transcript remain explicit
future Query2 app consumer work; none is silently supplied in this DTO.

## Existing ownership and refresh, not another persistence path

The existing Host generic dispatch obtains its owner lock. On a durable Host,
the new arm uses existing refresh_session before expected-head comparison:
get_session validates captured session/scope and current target admission;
Persistence.resume supplies the actual immutable Core engine; the existing
extends_accepted_history guard admits exact accepted-prefix appends but rejects
replacement seed/author truth/history at equal numeric head. Only then is the
selected engine updated and the new response built. A direct ephemeral Host
uses its existing selected engine without attempting Persistence access.

No new Store connection, SQL operation, callback, cancellation policy, worker,
grant, shared snapshot cache or engine constructor is introduced. The same
existing target admission handles NotFound retirement and fences that cached
session. Read-refresh never reselects a replacement accepted source implicitly.
Scope mismatch/unknown or closed session and stale revision return the existing
Scope/Closed/Stale categories. Port failures remain fixed rejected replies.
Existing Host MAX_INPUT24576 and MAX_OUTPUT262144 remain unchanged; global
serialized-output validation bounds the thin reply or returns TooLarge.

Legacy PlaySnapshot dispatch is untouched: Domain1 retains its old payload and
Domain2 retains typed Version refusal. Existing Inspect/Query1/compiler1 behavior
is unchanged. No capability advertisement or generated schema/TS hand edits are
part of this allocation. Root owns future generation and app decoder closure.

## Independent tests frozen before production

Test source commit `f217061827fed1cba5002c3c0409fde6d36f4947`, SHA256
`8a1c6453138a658d458057e1aeae96be6b6fd97077de9e535b14483afa4debef`.
This contract is frozen in its own subsequent commit before any host.rs edit.
The baseline lacks the new command; tests use wire JSON to avoid requiring a
future enum symbol. They are **UNCOMPILED/UNRUN**, not actual behavioral RED.

Seven substantive tests:

1. Actual Domain1 and actual Core prepare/apply-authored Domain2 engines through
   Host/Persistence: exact result/envelope/player keysets, actual rule/actor/item
   values, no private text/history/bindings, unchanged full source basis and old
   Mira-observedA despite worldB, under both native grant configurations.
2. Actual seed.player=mira proves identity/self-state/inventory use the seed's
   actor instead of hardcoding the literal player key.
3. An actual independent Core Give append in the fixture port must be refreshed
   before head comparison: old head Stale, current head succeeds with potion
   absent from player inventory; no Host write method invoked.
4. Actual two author histories at equal scope/head/state but different B/C truth
   basis: selected source replacement Stale; restoration of original source
   remains usable and unchanged.
5. Unknown session, cross-branch session/scope, stale head and fixture admission
   removal refuse without cached data; reappearance cannot resurrect a closed
   cached session, and explicit resume creates a new session.
6. Exact three-field command rejects extra version/observer/grant/facts,
   negative/fractional/string/null revisions, unknown operation and envelope2.
   Current valid read remains usable afterward.
7. Original Domain1 legacy shape retained, Domain2 legacy Version unchanged,
   owner still usable through the new read, explicit close fences further reads.

The read-only fixture Persistence contains **actual Core Engine values**, not
fake accepted JSON, forged Receipt or simulated Store commits. Every write port
increments a spy and refuses; tests require zero writes. External append is
actual Core typed preview/commit. Admission removal is fixture behavior, not an
actual SQLite retention/deletion test. There is no snapshot cancel argument;
existing session close/admission guards are tested instead of inventing one.
No provider/model is used or called. No SQLite/JNI/native UI execution is claimed.

## Source-only verification and handoff boundary

Only source inspection, Git/hash checks, scoped rustfmt parser/check and diff
whitespace checks are permitted in this allocation. All new source remains
UNCOMPILED/UNRUN until Root's serialized execution. No Cargo, Node, Gradle,
provider/model/app/native/device/ADB/CUA/desktop/protected-resource/settings/PR/
merge action is performed by this author.

Future qualification command, not executed here:

```powershell
cargo +1.93.1 test --offline --locked -p locallore --features host --test m08_play_snapshot_v2_review --target-dir <future-owned-target> -- --nocapture
```

Tests are feature-gated with host; a default-feature run executing zero methods
does not qualify them. Root must run frozen tests against their preproduction
commit, preserve compile/fixture/behavior attribution, then unchanged tests with
the minimal production commit and legacy/strict compatibility checks. Root later
regenerates Host JSON schema/TS and freezes frontend/Android exact-decoder/native
render checks when that separate consumer closure is allocated. This source
alone is not functional Domain2 UI or author permission. Exact production and
handoff hashes are recorded after the minimal edit, without backdating tests.

## Source handoff after implementation

The subsequent host.rs production commit adds exactly37 lines: the five-line
enum variant and one dispatch arm. It reuses existing refresh_session/get_session
and direct actual seed/player/item serialization, leaving the legacy arm and
all other code untouched. Production host.rs SHA256:
`b1125a1e3d351d3bd2d4e4c740d9b01760d5c38b967cb8d4affe5969d5118302`.
The frozen test SHA256 remains exactly8a1c6453…a4debef above.

Actually performed after the edit: scoped rustfmt parser/format check and
`git diff --check`, passed; source/Git/hash review shows only the claimed three
paths changed. No test/compiler execution occurred. There is no actual RED or
GREEN and no current first-foundation PR integration. Direct ephemeral Host
uses the same arm but is not separately exercised by these Persistence fixture
tests; actual Store/JNI/UI/render/generation integration remains Root-owned.
No new field is advertised in capabilities and generated schema/TS remain
intentionally unedited pending Root's separate full consumer closure. Their
future synchronization is a prerequisite, not a claimed passing schema gate.

The native display omits history by construction; it does not mean characters
forgot known values or that app generation may access world truth. Return to
Query2 and its safe observation provenance for detailed reads. No author
permission or automatic correction capability is introduced. At handoff, the
three exact path claims release to Root for isolated future qualification.
