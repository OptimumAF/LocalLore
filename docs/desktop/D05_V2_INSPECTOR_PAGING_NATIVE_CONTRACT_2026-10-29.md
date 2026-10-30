# D05 V2 inspector paging native harness proposal

2026-10-29. **Native fixture/oracle source contract accepted with Root precisions
below; no implementation, fixtures or native execution admitted yet. Launcher
extraction interfaces/policy FIRST and actual runtime admission remain pending.**
Refs #26 (bounded D05.03/D05.07 supporting slice), allocation6512170345 and the
[accepted frontend contract](D05_V2_INSPECTOR_BACK_PAGING_CONTRACT_2026-10-29.md)
at f3add8f84d5aea63d5987e31c3314d5e3072f265. The later eca52680 precision permits
valid public row-body/total edits; it requires exact binding/navigation scalars,
object ownership and strict decoder checks, not universal body immutability or
whole-page hashing/copying. This proposal does not reopen that frontend boundary.
GitHub owns status. Root must accept this recipe/interfaces/policy and independently
freeze native/policy FIRST before different-author harness implementation.

Source anchor is accepted main8b023194 and Root's f3add8f8 import; the actual
V2PlayController/V2PlayPanel files are unchanged between those anchors. The author
owns only this new document on plan/d05-v2-inspector-native-harness-v1 in the
released physical-D Reader checkout. No runtime result is implied below.

## Existing authority and exact fixture recipe

Use the existing Store/Engine/Host and Domain2 Query2. Never insert SQL, fabricate
pages/receipts, deserialize a prepared capability, create a provider, load a model,
or add a second query/storage engine. The fixture is prepared once before the
application Host opens, following timeline_harness.rs and author_harness.rs.
Store::create_new_pinned must refuse an existing database. There is one fresh
workspace, three scopes, two story seeds, one author correction and44 ordinary
single-command Dialogue turns:45 validated operations in total, below128. No
setup commit is allowed after the navigation baseline is taken.
Two seed-story creations are separate. There are44 begin_turn/44 commit_prepared
calls plus those two creations and one author application:91 fixed public setup
write calls, also below128. This is an API-call roster, not physical SQLite write
or transaction telemetry; author preparation and native opens have their own
ordinary implementation effects.

1. Parse the committed fixtures/lantern_quay.json; preserve its seed ID, actor
   IDs/names/locations, rules, item quantities and all other fields. Change scope
   to {story:"d05-inspector-native",branch:"main"}. Replace relic-location's
   proposition with "D05_PLAYER_SEED_SECRET_731"; retain known_by={player} and
   discoverable_at=dry-well. Replace Mira's existing seed belief proposition with
   "D05_MIRA_PRIVATE_BELIEF_812", retaining its original source/confidence.
   Create this story through Store::create_story. Its parent remains head0.
2. Through Store::prepare_author_correction then apply_author_correction, fork
   that exact parent at0/expected_parent_revision0 into child_branch="paging".
   Operation is ReplaceFactProposition for beacon-mark, expected proposition
   exactly "An old repair mark is scratched inside the dry well.", replacement
   "D05_UNOBSERVED_AUTHOR_TRUTH_913", reason="D05_AUTHOR_REASON_PRIVATE_914".
   The original seed fact has no knowers. The child is Domain2/head1; the author
   record is not an observation or a gameplay message. Parent stays Domain1/head0.
3. For i=1..43 in order, resume the child using Store::resume. Turn key is
   d05-page-NNN with three decimal digits, text is D05_PAGING_ROW_NNN plus suffix
   "_MIRA" for odd i or "_PLAYER_ONLY" for even i. Use Engine::request with
   Intent::Dialogue and audience={mira} for odd i, audience={player} for even i.
   Engine::proposal resolves exactly one Command::Say; Engine::preview validates
   it. Persist with Store::begin_turn and commit_prepared of that actual preview.
   No free_text/provider/Host prepare worker is involved. Check each committed
   receipt against the preview and exact request before continuing.
4. Create the second story from the same original committed seed, changing only
   scope.story="d05-inspector-other" and relic-location proposition to
   "D05_OTHER_STORY_SEED_515". Its branch is main; duplicate display names/IDs
   are deliberate. Commit one direct Dialogue turn d05-other-001 with text
   "D05_OTHER_STORY_MESSAGE_516" and audience={mira} by the same public APIs.

The three scopes are primary/main@0, primary/paging@44 and other/main@1. There
are43 child ordinary receipts/events, one child author record, one other receipt/
event and no parent ordinary record. Each Say leaves story_time100, inventory,
energy and actor locations unchanged. Mira witnesses22 odd child events; Sable
witnesses none. The21 even child events are player-only; all43 are visible to
Player. Do not change this43/22/21 roster during debugging.
Core validation, including fork-at-zero and self-audience, must be proven by
independent fixture FIRST; source-derived expectations are not execution results.

Query2 history emits one event plus original_input and narration per Dialogue
for Player/Omniscient. Player additionally receives one author_correction marker;
Character Mira receives observed events only; Sable receives none. The private
author input/reason/replacement must never appear in history, including Omni.

| Exact history query, empty search, limit64 | Permitted total | Proposed page lengths |
| --- | ---: | --- |
| Child/head44/current/Player |130 |64,64,2 |
| Child/head44/current/Omniscient with trusted grant |129 |64,64,1 |
| Child/head44/current/Character Mira with trusted grant |22 |22 |
| Child/head44/current/Character Sable with trusted grant |0 |0 |
| Child/head44/at_revision23/Player |67 |64,3 |
| Child/head44/at_revision23/Omniscient |66 |64,2 |
| Child/head44/at_revision23/Mira |11 |11 |
| Child/head44/at_revision1/Player |1 marker |1 |
| Parent/head0/Player or Omni |0 |0 |
| Other/head1/Player or Omni |3 |3 |
| Other/head1/Mira; Sable |1;0 |1;0 |

These page-length expectations require the fixed short rows actually to fit the
existing65,536-byte page budget. FIRST must assert every serialized history row
is at most768 bytes and the actual pages have the lengths above;64*768 fits below
the61,440 row-payload allowance. If that bound fails, retain the failure and revise
the proposal explicitly; never pad rows, truncate authority, raise limits or count
a byte-limited early page as64. General UI code must support variable page sizes.
No page number or reliable total-page count is added to the product.

Searching D05_PAGING_ROW_ returns86 Player rows (43 events+43 original inputs),
44 Mira-targeted Player rows when searching the _MIRA suffix, and two Player rows
for exact D05_PAGING_ROW_043_MIRA. Narration does not contain the request text.
Mira's history contains exactly22 event keys and no scoped_message; Sable has none.
Native FIRST must test these actual queries rather than constructing row arrays.

Knowledge checks have presence/absence oracles, not invented total counts:
Player sees its seed secret and cannot see Mira's private belief or the unobserved
author replacement/reason. Mira sees its private seed belief and cannot see the
Player seed secret, even-only statements or author replacement/reason. Sable sees
none of those. Omni knowledge may inspect the canonical replacement and secret;
it must not confer them on an actor. Neither primary lens may receive either
other-story sentinel. Other-story Player/Omni knowledge contains its seed
sentinel515; Player/Omni/Mira history contains its message516. Sable history is
empty and its knowledge need not contain either sentinel. All exclude primary
sentinels. Actor context/event fingerprints must remain unchanged after
inspection and after returning from Omni to an actor.

## Fixed native surface and canonical oracle

Proposed paths, requiring exact later claims before edits:

| Path | Smallest future responsibility |
| --- | --- |
| NEW apps/desktop/src-tauri/src/v2_inspection_paging_harness.rs | Fixed seed recipe, requested/active mode checks, read-only oracle and native FIRST module inclusion. |
| NEW apps/desktop/src-tauri/src/v2_inspection_paging_harness_review_tests.rs | Independently authored actual Store/Host-library fixture/oracle FIRST. |
| NEW apps/desktop/ui/v2-inspector-paging-native-journeys.ts | Actual mounted panel/controller/Gateway/host_call journeys and semantic/render checks. |
| NEW apps/desktop/v2-inspector-paging-harness.mjs | Closed launcher, fixed budgets and direct-child supervision only. |
| NEW apps/desktop/check-v2-inspector-paging-process-review.mjs | Independent actual-launcher VM child/Git/storage FIRST, not a policy copy. |
| apps/desktop/src-tauri/src/main.rs and build.rs | Dev-only seed before Host open, one command/permission registration and fixed mode bootstrap. |
| apps/desktop/src-tauri/tauri.conf.json and permissions/autogenerated/harness_v2_inspection_paging.toml | Only this command's named permission; normal registration remains absent. |
| apps/desktop/src-tauri/src/harness.rs | Fixed capture labels and existing reserve-before-create writer for this mode. |
| apps/desktop/ui/main.tsx and journeys.ts | Dev-only closed journey selection, existing delivery-gate reuse and finite instrumentation. |
| apps/desktop/verify-frontend.mjs | Later register accepted frontend policy checks and normal hook exclusions. |

Actual inspector-harness.mjs drives legacy QueryInspector/query-journeys and uses
exit-based/unbounded-inherited child handling; trace-harness.mjs has the same older
launcher pattern. Neither supplies this mounted V2 panel or the accepted new
bounded process policy. Keep both sources and historical results unchanged; do
not rename their results as V2 coverage. A new small private fixed launcher is
proposed, retaining the accepted policy semantics with its own actual-source
FIRST. Do not introduce a common runner/refactor merely for reuse. HarnessState
already owns create-new labels/files, JSON256KiB, PNG16MiB and40-checkpoint caps,
app-owned CapturePreview and viewport presets. Extend only this closed mode's
label/budget activation to the existing reserve-before-open writer; preserve D07
writer behavior/tests and other mode behavior. This is the entire render surface.

Use one exact native environment selector LOCALLORE_D05_INSPECTOR_PAGING_HARNESS=1
with existing dev-harness/base guard, existing owned workspace/artifact paths and
no unrelated harness selectors. Requested-but-mixed/invalid mode refuses before
seed/Host open; normal builds compile no fixture/command/journey. No new path,
scope, cursor, code, filename, shell or command selector is accepted over IPC.
No restart selector is proposed for this slice: one actual application process.
Reuse LOCALLORE_D05_ARTIFACT_ROOT and LOCALLORE_D05_TARGET_DIR as launcher-owned
paths. Do not set legacy LOCALLORE_D05_HARNESS=1. The finite dev bootstrap boolean
inspectorPaging selects this new actual V2 journey; inspecting retains its legacy
meaning. No configurable mode/fixture/scenario selection is exposed to renderer.

Only new command is harness_v2_inspection_paging with no renderer arguments.
It requires this exact development mode, active main-window lease and task-owned
fixed workspace; captures/rechecks the lease around blocking read work. It opens
Store::open_read_only at the native-owned path and returns one <=32KiB JSON object:
{version:1,kind:"v2_inspection_paging_oracle_v1",fixture_version:1,scopes:[...]},
where the ordered three scopes each contain scope,domain_version,head,story_time,
seed_sha256,projection_sha256,records_sha256,receipts_sha256,turns_sha256 and
actors_sha256. Each hash is64 lowercase hex over actual serde_json bytes, with
fixed ordering declared below. It returns no actor private body, SQL or full query
pages, and grants no normal application authority. Error strings are a small
declared finite set for forbidden mode, stale lease, missing/invalid fixture,
read-only failure, canonical mismatch or bounded output failure.

Projection hashes Engine::canonical_bytes; it does not cover records by itself.
Records hash serde_json::to_vec(engine.canonical_records()); receipts hash actual
engine.receipts(). Seed hashes the actual seed. Actor hash encodes the ordered
player,mira,oren,sable tuples of actual character_context_v2 and actor_receipts_v2
at that scope's head. Turns hash the fixed key-order list from Store::lookup_turn
for43 child keys or the one other key, including committed phase, exact request
and receipt; empty for parent. Encode phase as the fixed string committed after
matching actual TurnPhase::Committed; TurnRecord itself is not a Serialize DTO.
The author is covered by canonical records; native FIRST separately exercises
lookup_author_correction of the fixed input with created=false after setup. The
live oracle does not call author lookup or use a writable Store fallback.
All fields/counts must match the recipe before a baseline oracle is accepted.

Compare complete oracle replies before navigation, after actor/session/reset/error
journeys and after final controller/session cleanup while the main-window lease
is still active, BEFORE harness_finish/app.exit. No IPC oracle is available after
OS app closure in this one-process gate. Also compare selected actual play_snapshot_v2
and fixed Query2 actor pages. This establishes unchanged canonical projections,
records/receipts/fixed fixture turns and actor observations. The public fixed-key
turn lookup does not enumerate arbitrary unknown draft keys; zero navigation
write dispatch is separately established by the actual command roster. This is
not SQLite/WAL/profile byte
equality: native opens may update runtime metadata. No new public query/admin API.

The desktop currently opens its Host with story_lab=true (main.rs WorkspaceState).
Play's enforced Player lens is a frontend behavior; do not claim that a renderer
query is denied solely because the panel currently shows Play. Prove real native
Scope/Stale/UnknownObserver/InvalidCursor refusals with fixed malformed-bound
queries through normal host_call. Separately, native FIRST creates an actual
Host-library instance with story_lab=false and proves Character Mira/Omni queries
Forbidden while Player succeeds. Label this as Host-library evidence, not an
actual second app/IPC privilege boundary. No Host grant design changes here.

## Actual panel journeys, focus and finite evidence

Use actual V2PlayController and mounted V2PlayPanel, strict checkedPageV2 and the
normal Gateway->host_call->Host::inspection_query->Store reload->Query2 route.
No private controller-state mutation or replacement mini UI. Resume the exact
fixed child from the actual workspace catalog; do not choose "first recent".
Navigation uses actual rendered Previous inspection page/Next inspection page
handlers and Read permitted view form. Application-owned DOM semantic activation
may use the existing control's click() and DOM focus() only; it must never inject
OS mouse/keyboard input, activate a window, synthesize hardware keys or drive a
general script/debug server. Root explicitly accepted this tightly scoped DOM
activation/focus mechanism before this proposal freeze. Any focus-boundary defect
requiring a product fallback needs a separate narrow accepted proposal before
production, as required by the frontend contract.
The current panel places context above the row list and its Next button below;
this source contract does not assume64 rows fit a viewport. If actual geometry
requires a small pager-context/status repeat or bounded row scroll region, freeze
that specific V2PlayPanel/style.css allocation before changing product code.

Initial fresh read -> Next -> Next reaches64/64/2, Previous -> Previous returns to
the actual first page, then Next refetches. Compare each displayed key/row/hash and
query identity against the completed actual IPC reply and Rust source oracle.
Navigation changes cursor only, never story/lens/head/search/view/revision. Count
exactly one normal inspection_query call per eligible action and none for a
disabled/no-predecessor action. Never parse or synthesize a cursor or restore a
cached page. Source fingerprints prove canonical nonmutation independently.

Keep the actual controls mounted. Focus the rendered pager control through DOM
focus, invoke its real action and observe document.activeElement through pending,
completion and disabled boundary; no row/other-panel focus stealing or stale-focus
effects. Record the actual boundary result rather than asserting browser focus
behavior from SSR. Programmatic focus/order evidence is not physical keyboard or
screen-reader usability qualification. Root's native image review remains required.

Reuse FaultGateway.heldQuery only when no other query is pending; arm it immediately
before one pager action and assert the exact request/query/real IPC reply that
entered it. It holds delivery AFTER successful native read, not a Rust worker.
Use it for pending duplicate-action suppression, a form/context reset and a lens
switch before release; late delivery must not restore private rows/source links/
history counts or clear newer pending/error state. Always release in finally.
No general request rewrite, callback evaluator or renderer-controlled delay.

For one error/retry image, propose one dev-only, single-use inspection delivery
drop after an actual successful native read, armed only by this fixed journey.
It throws the existing Transport category and records that real IPC completed;
it never alters the page. Retry reissues the exact cursor to native and succeeds.
The resulting expected error is a delivery double, never a native Host failure.
No other fault mode, arbitrary target selection or fabricated page is admitted.

Exercise search/view/historical form-edit reset; identical fresh Read; refresh
and same-head snapshot replacement; Play/Lab/Player/Mira/Sable changes; other
story/session and back; unsupported summaries and empty Sable results; retained
body with disabled paging after a failed fresh Read. Head44 versus inspected23
must remain distinct. Native overflow beyond32 predecessors is unnecessary here;
the independent frontend FIRST owns35+ transitions and the rolling32 cursor cap.
Valid external row-body edits are not grounds for a new whole-body hash/cache.

From navigation baseline to final oracle, allow only read/session/catalog/lifecycle
operations. Count the actual app Gateway command roster and reject any submit,
prepare,free_text,commit,cancel,retry,author,model,memory,export or fork operation.
At most192 inspection_query dispatches in this single finite journey; cap bounded
metadata records at256. Fixture45 accepted operations and91 public write calls
are separately counted before Host open.
No provider construction/calls are allowed in fixture or journey source. Command
instrumentation and no-provider source review do not measure independent SDK loads
or all OS side effects; report ordinary metadata probes honestly. Use the existing
bounded frontend/native ErrorBuffer (at most64 finite category/source entries),
expect exactly the one labeled delivery-drop Transport observation if buffered,
and fail on any unexpected entry. Fixed native negative-probe replies are counted
separately; do not disguise a deliberate refusal as an unexplained app failure.

Freeze these20 success labels before code: d05-page-first, d05-page-second,
d05-page-third, d05-page-back-second, d05-page-back-first,
d05-page-forward-refetched, d05-page-pending-next, d05-page-error,
d05-page-retry-second, d05-page-search-reset, d05-page-historical,
d05-page-mira, d05-page-sable, d05-page-other-story, d05-page-same-head-refresh,
d05-page-stale-delivery, d05-page-unsupported, d05-page-enlarged-wide,
d05-page-enlarged-narrow, d05-page-final. One additional d05-page-failure label
is allowed only on failure, preserving the failed check and any original image.
No automatic repeat/replacement capture or successful-roster relaxation.

Semantic snapshots <=256KiB include selected session/story/branch, effective
player/lens, actual head/inspected revision/view/search, displayed row keys/count/
total, actual bound query and cursor digest (not raw cursor in visible UI), paging
bound/canPrevious/canNext/retainedPrevious/earlierOmitted/navigating, busy/error,
displayed receipt availability, actual active control and all measured rectangles.
Private synthetic bodies stay local. DOM text must exclude forbidden current-lens
and other-story sentinels, including stale frames before effect completion.

Capture only app-owned WebView2 CapturePreview through existing harness_checkpoint.
For each image require actual matching DOM, two animation frames, nonzero bounded
rectangles, viewport fit, no horizontal page/panel overflow and no fixed/sticky
occlusion at top/middle/bottom of the pager/status/context. Context and actual
actionable controls must fit together; do not scroll the button offscreen to make
rows look correct. At1280x900 and620x900 check real150% state/class/computed-font
ratio, then restore100%. Every generated PNG requires individual inspection.
Neither PNG signatures, DOM geometry, SSR nor a favorable source review replaces
that visual review. No desktop screenshot/input or native-dialog automation.

## Independent FIRST, launcher and execution admission

Native FIRST freezes exact recipe/row counts/pages/source keys, scope/lens/history
boundaries, knowledge sentinels, canonical/turn/actor equality, read-only open and
refusal to reseed. Verify actual Host wire grants, stale/cross-scope/cross-query
cursors, malformed query fields and no story-time advance. Fixed no-provider
construction is source reviewed; Query2 tests execute actual Rust/SQLite and are
not WebView/IPC evidence. Do not generate large fixtures during source authoring.
Missing helper/registration/fixture prerequisite is SETUP_UNRUN, never zero PASS.

Launcher FIRST must execute actual new launcher helper text in a bounded VM with
fake children/timers/files, not copied policy functions. Freeze extraction markers
and exact ambient/helper names separately before code. Cover child close/nonzero,
spawn/no-PID/PID errors, both pipe errors, output overflow, timeout/one kill/grace/
late close, sticky unknown ownership; Git admission/source/product checks; every
normal restoration position; and safe-integer/source/target/evidence arithmetic.
Time tests first verify intended fake child identity/PID/pending timer before
advancing; unreachable readiness is setup/unrun, preserving original failures.

Proposed closed launcher has zero CLI arguments and only fixed mode/bootstrap.
Use existing installed offline tool paths and existing admitted Cargo cache/target;
physical-D source/cwd/TEMP/TMP. Validate ordinary non-reparse/disjoint source,
workspace, artifact, target and cache paths; clean exact committed Git and frozen
source/product hashes. Scrub every case-insensitive LOCALLORE_ inherited alias,
including model roots, then set only the fixed required harness additions. No
fallback browser, model, download, SDK/ADB/device, service/server or OS probe.

Proposed deadlines: Git15s, frontend240s, Cargo900s, app180s; each child output
stream256KiB; one best-effort stop then5s grace. An error with known PID, pipe
failure, timeout or overflow permanently latches unknown ownership and forbids
later native/Git/restoration work. Exit alone is not owned close. No process-tree
containment claim. Keep one global finally; restore normal frontend/no-feature
native products only after known closure, fresh source/product/storage checks,
and never launch the restored normal executable. Preserve partial/failed writes.

Before any actual execution, Root must declare/measure a separate exact D05
retention roster including this gate's tests/frontend/native packets, original
target baseline/free capacity and all prior D05 failures. Declare the joint
retained total and an explicit accepted joint ceiling, including all preserved
D07 evidence (last reported501,639,443 bytes, to be remeasured) plus every D05
root/provenance output; separate task names cannot hide those costs. The existing
D07 gate stays closed with its512MiB cap, failures and bytes intact. No runtime
is admitted without this joint declaration. Proposed D05-only ceilings are
128MiB cumulative D05 evidence,64MiB expected cohort headroom,64MiB native writer
per process reserved before create-new open,64MiB whole packet observed between
children,2GiB target growth and128MiB source growth. These are proposals, not an
admission or permission to allocate those bytes. Root must tighten or explicitly
revise them using measured forecasts BEFORE execution. Bound source inventory to
2million entries, every file size/sum to safe integers and metadata to256KiB.
Do not silently reset a baseline, choose a fresh base to hide old evidence or
delete a capture to fit. D07's retained512MiB gate and original target baseline
remain intact; this distinct D05 claim cannot erase or reclassify its costs.
For the existing shared native target, retain the original8,259,980,576-byte
baseline and account all later growth against it. A new task, source branch or
artifact parent cannot replace that baseline with today's target footprint.

Use one create-new packet and one synthetic SQLite workspace for this finite
qualification. Normal resource/code/tool locations stay unchanged. Failed
inventory/over-cap/unknown-drain observations are permanent and forbid further
work; reserve1MiB for bounded final metadata and record unavailable final
measurement honestly. No cleanup, expiry, repeat root or second cohort is admitted
without a new measured decision. Root alone owns the heavy slot.

Later evidence must separate frontend synthetic Gateway/SSR, actual Store/Host-
library tests, native IPC and actual hidden WebView/render/focus observations.
Run current frontend/native checks, lint/format/normal hook exclusion and Rust
Android Windows-host compatibility as applicable. No Android runtime, SDK/JVM/
Gradle/ADB/emulator/device, native-model, OS/network isolation, accessibility,
release, whole D05 or desktop-epic acceptance follows. GitHub receives exact
lineage/commands/counts/environment/errors/resource/capture-review limitations
and the next runnable task. Source-only fixture/oracle acceptance and independent
FIRST allocation are fixed below; no implementation/runtime admission follows.

## Root pre-FIRST fixture and oracle precision

Root accepts the source-derived recipe, bounded fixture/oracle interfaces and
finite journey boundaries after independent source review. Original proposal
3e7c5421 is imported e5495dee; its unrun expectations remain explicit. This accepts
no observed row count, fixture generation, app launch or model result. The separate
launcher extraction/FIRST contract still must freeze before launcher production.

Actual environment-free helper signatures in the new native module are:

```rust
fn validate_mode(
    selector: Option<&str>, development: bool,
    legacy_inspecting: bool, other_harness: bool,
) -> Result<bool, String>;
fn validate_workspace_path(path: &std::path::Path) -> Result<(), String>;
fn prepare_fixture(path: &std::path::Path) -> Result<(), String>;
fn fixture_oracle(path: &std::path::Path) -> Result<serde_json::Value, String>;
```

`path` is the fixed SQLite path, not its directory and never a renderer argument.
Helpers may remain private, with the independent review file included as a child
test module. Tests exercise these actual helpers; no test-only recipe or copied
mode/path/oracle implementation establishes success. Independent FIRST uses the
current production `locallore_workspace::open(path, story_lab)` and normal session
resume for grant checks, with no fake Persistence adapter or private session
injection. Host grant denial follows Store reopen, so it is not zero-file-probe
evidence.

Absent selector means Ok(false), preserving existing modes. Exactly Some("1")
requires development=true, legacy_inspecting=false and other_harness=false;
all other present selectors return Forbidden. The runtime wrapper preserves
var_os presence: a present non-Unicode value must fail, never become absent through
`.ok()`. Runtime development includes the existing dev-harness compile boundary
and exact D02 base guard. In the requested new mode, allow only these case-folded
LOCALLORE_ child keys: LOCALLORE_D02_HARNESS, LOCALLORE_D02_ARTIFACT_DIR,
LOCALLORE_TEST_WORKSPACE, LOCALLORE_D05_INSPECTOR_PAGING_HARNESS. Any other present
LOCALLORE_ key is conflicting, including fixture/memory/restart/model selectors.
The launcher scrubs all inherited aliases before setting these four fixed keys.
Validate requested mode before ANY existing fixture/Host/model setup; absence
must retain existing bootstrap behavior. Unit tests do not mutate global env.

The path guard accepts only ordinary physical D paths, fixed leaf
stories-v1.sqlite, and a parent named d05-v2-inspector-paging-native-<UUID>, with
a canonical lowercase hyphenated UUID suffix. Parent exists and is ordinary;
all ancestors and an existing file must be non-reparse ordinary entries.
Reject raw literal dot/parent segments, including interior '.' that Rust
Path::components can normalize away; do not normalize a negative input into a
valid test. An absent database is allowed by validation, because the same guard
serves preparation and oracle. Only prepare_fixture demands a fresh database
through create_new_pinned and refuses an existing ordinary file without repair.
Runtime wrappers additionally require exact equality with the task-owned
LOCALLORE_TEST_WORKSPACE/WorkspaceState path. These are cooperative path controls,
not an AppContainer/race-free OS filesystem isolation claim.

Exact helper/command error vocabulary is Forbidden, Closed,
SyntheticWorkspaceRequired, SyntheticFreshWorkspaceRequired,
SyntheticFixtureInvalid, SyntheticReadOnly, SyntheticOracleBudget,
SyntheticWorker. Mode errors use Forbidden; lexical/ordinary-path errors use
SyntheticWorkspaceRequired; an existing ordinary preparation target uses
SyntheticFreshWorkspaceRequired. Invalid recipe/failed setup/missing canonical
records or turns map to SyntheticFixtureInvalid. Failed read-only Store open
uses SyntheticReadOnly. Failed/oversize JSON encoding uses SyntheticOracleBudget;
failed blocking task uses SyntheticWorker. Preserve native WindowLease's existing
Forbidden/Closed semantics. Never forward arbitrary Store/SQLite/path error text.
Normal host_call Query2 negative probes keep their existing native error types.

The no-argument command captures the actual main-window lease, dispatches the
bounded read-only helper in blocking work, then rechecks with lease.dispatch
AGAIN before publishing. Dispatch only around the whole blocking closure checks
before the action and is insufficient as an after-read lease check. No writable
WorkspaceState/get fallback, renderer token, user path or grant is introduced.

Scope order is primary/main, primary/paging, other/main. Hash raw
Engine::canonical_bytes directly, not a serialized Vec<u8>. Seed, records and
receipts use their actual serde_json::to_vec bytes. actors_sha256 hashes ordered
Vec<(String, CharacterContextV2, Vec<ActorReceiptViewV2>)> for seed.player, mira,
oren, sable, each actual scope/head. turns_sha256 hashes ordered
Vec<(String, &'static str, Request, Receipt)> in NNN001..043 order for child,
other001 for other and empty for parent. Require actual TurnPhase::Committed and
Some(receipt), encode the phase as literal "committed" and include the actual
request/receipt. No synthetic surrogate hash or inferred canonical equality.

AuthorCorrection wire rows are exactly {kind:"author_correction",revision}; their
native sorting key is serde-skipped. Across IPC use typed kind+revision identity
for that marker, actual keys for other rows, and compare actual serialized DTOs.
Do not invent a marker key/source identity or change the shared schema.

The other/main story is Domain1 with literal player ID and no scene mode. The
current app routes it to the legacy surface, so d05-page-other-story must capture
the actual selected other-story header, absence of V2 pager/old private body,
then return to the exact paging child with a fresh V2 chain. Domain1 Query2
counts/sentinels are actual Host-library/direct native reads, not mounted V2
paging evidence. Do not enable a scene/provider or alter routing to force V2.

For actual fixed form-edit journeys, Root permits only the mounted inspector's
existing view/select, completed-revision and literal-search controls: native DOM
value setters followed by input/change events, and form.requestSubmit or its
normal submit button. These run the real React handlers on app-owned elements.
They inject no OS keys/mouse input, use no React fiber/private-state mutation,
accept no arbitrary selector/value over IPC and expose no general event/script
service. Values/actions are fixed in the reviewed development journey. DOM
click/focus and these form events remain separate from physical keyboard or
screen-reader qualification. Mounted stale local-draft behavior needs actual
WebView observation; SSR does not establish it.

Independent native FIRST owns only the new review-test file, frozen before
different-author helper production. During eventual execution, all test fixtures
must be retained under the admitted D05 paging artifact base via its explicit
environment, with unique fixed-prefix child folders and no drop-time cleanup.
Missing admission/helper/module is setup/unrun, never zero-test pass. FIRST source
authoring itself is source/Git/hash only and creates no fixture/output roots.
