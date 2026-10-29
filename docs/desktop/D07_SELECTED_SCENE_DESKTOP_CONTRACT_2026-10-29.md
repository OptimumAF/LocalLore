# Selected Protocol4 scene desktop integration proposal

2026-10-29. **Proposal only; pending Root acceptance and the shared gate.**
Refs #29 D07.04/D07.06 and
[proposal allocation6507762125](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6507762125).
Author branch: `plan/d07-selected-scene-desktop-v1` from `a3f6025d`.
Accepted desktop source anchor: `a6f235ae74c4e3ade80175a499ecd7fc20751314`.
The shared [selected Scene4 contract](D07_SELECTED_SCENE_V4_CONTRACT_2026-10-29.md)
is the prerequisite, including its Root binding, source-fixture and preparation
reservation clarifications (the latter recorded in append `ea464324`).
Its new FIRST source at this proposal base is not implementation or qualification.
This document does not enable a control, accept a test, admit execution or close D07.

## Gate boundary and existing authority

The proposed second gate wires source protocol4 to selected artifact version3 in
the existing desktop selected workflow. It supports **ScriptedBaseline only**.
It does not implement native selected4 inference, improve the recorded prose,
requalify historical cohorts or infer human acceptance. Both retained human
assessments remain needs improvement; unavailable historical causes stay unavailable.

Shared Rust continues to own canonical state, exact source inputs, Store copies,
validation, receipts, revisions, idempotency, cancellation, recovery, observer
filtering and ledger accounting. Desktop adapts opaque capabilities and bounded
data; the frontend remains presentation. Reuse the current native job, window
lease, execution/read consent, selected catalog, model owner and cleanup paths.
Do not add an evaluator, provider, inference/memory implementation, journal,
renderer path authority, generation grant or separate persistence schema.

The inspected accepted implementation has selected1/source2 and selected2/source3
variants only. Source4 full reports are readable, but selected preparation refuses
both lanes and the UI deliberately withholds source4 from selected controls.
The new shared producer alone must not change that desktop state. Integrate only
after its implementation, independent checks, review and owner acceptance/merge
are recorded. Refresh actual main and ownership before implementation; do not
assume a historical plan or this proposal proves those prerequisites.

## Proposed paths and ownership split

All paths are repository-relative. Root claims final ownership before edits;
independent FIRST files and production writers receive disjoint allocations.

| Path | Proposed change |
| --- | --- |
| `apps/desktop/src-tauri/src/evaluation/selected/versioned.rs` | Closed Protocol/Plan/Opened V3 dispatch, source4/selected3 identities and safe native refusal. |
| `apps/desktop/src-tauri/src/evaluation/selected.rs` | Strict V3 prepared/index validation, exact source binding checks, finite error mapping and existing lifecycle integration. |
| `apps/desktop/ui/selected-evaluation-model.ts` | Separate closed V3 prepared/summary/diagnostic DTOs; retain V1/V2 decoders. |
| `apps/desktop/ui/comparison-reader-model.ts` | At most a narrow export of its existing Scene4 construction validator; preserve old reader behavior and error category. |
| `apps/desktop/ui/selected-evaluation-controller.ts` | Presentation source-version/binding expectations and existing stale/lifecycle fencing. |
| `apps/desktop/ui/selected-evaluation-view.tsx` | Source4 scripted controls, precise scene diagnostics and unavailable-native presentation. |
| `apps/desktop/ui/App.tsx` | Pass actual reader source4 identity/version into the existing selected surface. |
| `apps/desktop/ui/ComparisonReaderPanel.tsx` | Replace the blanket selected4-unavailable sentence only at the accepted desktop gate. |
| `crates/locallore-eval/src/local_lane/comparison/scene_v4/desktop_api.rs` | Narrow unavailable-note supersession described below; keep full reader read-only. |
| `crates/locallore-eval/src/local_lane/comparison/scene_v4/selected_v3.rs` | Narrow current report-writer GUI-unavailable note supersession only; preserve stored historical reports, projections and accounting evidence. |
| `apps/desktop/src-tauri/src/selected_harness.rs`, `apps/desktop/ui/selected-evaluation-journeys.ts`, `apps/desktop/selected-evaluation-harness.mjs` | Fixed development-only source4 discriminators/journeys and bounded launcher qualification, if reused. |
| `apps/desktop/src-tauri/src/harness.rs`, `apps/desktop/ui/main.tsx` | Only necessary fixed labels/mode wiring after a frozen harness contract; no generic execution facility. |

New native/frontend FIRST sources, their module/check registration, the specific
availability/scripted-refusal assertion sites below, qualification documentation and the
normal frontend check entry must be separately named in Root's allocation.
This proposal author owns only this new document. No production/test paths are
claimed by the author, and no architecture-wide refactor is proposed.

## Closed version dispatch and native failure

Extend desktop-private `Protocol` with V3: `from_source(4)`, selected_version3 and
source_version4. Add `Plan::V3(Box<scene_v4::selected_v3::PreparedSelectedPlan>)`
and `Opened::V3(Box<scene_v4::selected_v3::desktop_read::OpenedSelected>)`.
Only actual shared preparation constructs a plan. Versioned metadata is not a
constructor or grant. Route V3 prepare/metadata/run/resume and open/summary/
evidence/diagnostics to those exact shared functions; never route4 through
literal selected2 or make a fake full comparison report to reuse a parser.

`prepared_protocol` recognizes version3 only together with source_protocol_version4.
Unknown combinations refuse. Existing V1/V2 meanings, APIs, default lanes and
stored artifacts retain their current validators. The native `Index.version`
remains the selected artifact version, not the full source protocol. No migration
or rewrite of older saved experiments is required.

Source4 ApprovedNative must yield the existing desktop `NativeUnavailable`
category before consent, target/index creation, model status/asset/profile lookup,
reservation, provider construction or native execution. Preserve grant, pure
scalar/client/binding validation and current window/job admission precedence.
A previously opened source capability may already exist and its transfer/drop
uses existing owners; do not claim globally zero filesystem work from the refusal.
After native transfer, that reader token remains consumed even on refusal; the
frontend requires a fresh reader token for another attempt. No silent scripted
fallback for an explicitly requested native lane is permitted.

Map shared `SelectedNativeUnavailable` explicitly to `NativeUnavailable` before
the generic `Selected*` integrity mapping. Keep finite public categories and avoid
exposing private file paths, arbitrary error text, assets or runtime objects.
V3 manifests/index metadata must admit only `scripted_selected_case`; a forged
V3/native combination refuses cold open, start and resume before new work.

Existing `Plan::run_native` and `resume_native` return
`SelectedNativeFailure<R>`. Its `from_error` constructor is crate-private, and
the desktop cannot fabricate that owner payload. Do not widen Core visibility,
add a Core native selected4 API, call a legacy native route or panic to fill a V3
match arm. Proposed desktop-only result adapter:

```rust
enum NativeDispatchFailure<R> {
    Unavailable,
    Owned(producer::SelectedNativeFailure<R>),
}
```

V1/V2 wrap their existing owned failures unchanged; V3 returns Unavailable without
calling its reservation callback. Parent dispatch maps Unavailable to
`Outcome::plain(Err("NativeUnavailable".into()))`; Owned follows the existing
retained-cleanup path. Also reject V3/native before destination/index mutation.
This is a finite adapter, not another cleanup owner or arbitrary error channel.

## Distinct bindings and closed transport data

| Identity | Required meaning |
| --- | --- |
| Full reader snapshot binding | Actual validated source4 snapshot; native prepare/resume source transfer checks it. |
| Prepared `source_binding` | Same source4 snapshot binding; compare against the native Prepared/Index source binding. |
| Prepared `binding` | Selected3 destination manifest identity; shared resume takes this value. |
| Selected read summary binding | Separately sealed actual selected manifest, turns, report and accounting snapshot; evidence/diagnostics take this value. |
| Plan/run/source tokens | Existing opaque native presentation capabilities, with current lease/epoch/client ownership; hashes never replace them. |

Keep `SelectedSourceIdentity` exactly `{readerClientId, runToken, binding}` and
the existing `evaluation_selected` IPC action/request shapes. Do not add a path,
version-to-route instruction, provider setting or grant Boolean from the renderer.
Native dispatch determines protocol from its retained validated source/index.
The selected status/catalog/cleanup/result envelopes keep their current version1
meaning. Their nested prepared/summary/diagnostic payloads may be selected3.
Catalog entries remain bounded IDs/created/lane/selection; opening validates the
native index rather than trusting a renderer-supplied version.

Prepared3 has exactly:

```text
version, kind, binding, source_binding, lane, selection, arms,
source_protocol_version, constructions
```

Constants are version3, kind selected_prepared, source_protocol_version4 and
lane scripted_selected_case. `selection` and the exact two ordered arm entries
retain shared selected semantics; each arm contains only arm/scope/before_head/
prefix_sha256/input_semantic_sha256. Require both 64-character hex bindings and exact
ArmDescriptorV4 constructions. Compare prepared source_binding with its native
Index.source_binding when creating and reading that index. Preserve the older
prepared key sets; do not add this new field to selected1/2 by accident.

Summary3 has exactly the existing selected_read keys with version3,
source_protocol_version4 and exact V4 constructions:

```text
version, kind, binding, lane, selection, arms, read_only,
execution_available, source_protocol_version, constructions
```

Its ordered arms contain arm/scope/before_head/after_head/available. Nullable
after_head and availability retain the existing relation. Summary is metadata,
not full Requests, outcomes, prompts or a private report. Require read_only true
and execution_available false. There is no invented summary source_binding field.
Status.binding is the selected **read** binding only when a native read cap was
published; execution completion does not manufacture that cap or its token.

Diagnostics3 uses exactly the accepted shared selected3 projection. The wrapper
has the current selected_diagnostics keys plus source_protocol_version4,
constructions and human_rubric; version3, human_reviewed0, human_rubric not_reviewed
and quality_accepted false remain explicit. Each row contains exactly:

```text
turn, arm, phase, error, expected, passed, failures, quality_flags, roles,
roles_known, elapsed_ms, actual_receipt_sha256, construction,
construction_evidence_status, construction_evidence_reason, construction_matches,
privacy_evidence_status, fallback, repairs, recovered_without_checkpoint,
first_final_response_ms, commit_elapsed_ms, narrator_prompt_sha256,
narrator_schema_sha256, scene_frame_sha256
```

Bind diagnostics version/lane/constructions/read binding and row turn/arm to the
actual selected summary; allow at most one left and one right row. Reject missing,
unknown, duplicate-wire and cross-version keys at their existing parser boundary;
frontend parsed-object checks do not independently detect raw duplicate JSON.
Retain required nulls and finite V4 construction/privacy states, nullable hashes,
timings/fallback and recovery uncertainty. Do not import selected2 privacy_passed,
context_evidence_available or literal suffix metrics as false/zero substitutes.
If sharing descriptor validation, narrowly export the existing Scene4 validator
and translate its error to SelectedEvaluationWire at the selected boundary.

Keep detached, frozen frontend records and current bounds: 16KiB prepared/summary,
24KiB native status, 32KiB native index and 256KiB evidence/diagnostics. Existing
frontend outer-envelope bounds remain separate. Bounded evidence wrappers and
Rust Query2 are reused; do not add an arbitrary full-report/raw JSON escape.

## Frontend preparation, lifecycle and visible state

App uses the actual ready reader source protocol, token, binding and selected row.
Pass source4 through the existing SelectedExperiment surface only after acceptance.
Proposed presentation-only view prop `sourceProtocolVersion?: 2 | 3 | 4` keeps
version hints separate from the exact three-key native source identity. Extend
`SelectedEvaluationController.prepare` with an optional fourth argument of the
same union for expected-response validation; do not serialize that hint into IPC.
App/view passes the actual source version. Existing three-argument callers retain
their current behavior. For a supplied hint require the corresponding selected
payload version (2->1,3->2,4->3), and require any prepared3 source_binding to equal
the requested source snapshot binding. Resume expectations derive from its actual
opened selected summary and fresh source; a UI hint never selects a native route.

Native consent remains necessary for prepare, and Start remains a separate explicit
action consuming the actual prepared token once. Repeated Start/retry preserves
current consumed-operation behavior; no second destination, new provider call or
fresh request is created after an unavailable acknowledgement. Preparation is not
execution, and successful execution is not private-inspection consent. Open uses
the existing separate native affirmation. Resume retains its existing fresh-source
and execution-affirmation path; read permission alone cannot resume generation.

For a known source4 selection, the view offers the scripted lane and explicitly
labels native selected scene execution unavailable. Disable the native option
and normalize a stale local lane choice before enabling Prepare; do not send a
scripted request when a native choice is still displayed. Direct IPC/native tests
still establish the real refusal. Keep old source2/3 lane choices unchanged.
Use literal scene and relevant memory scene arm labels for selected3. Present
finite privacy evidence, construction reason, fallback/repair/recovery and timing
availability honestly. A committed row is not an automatic scenario/privacy/
human-quality pass. Render bounded text/escaped data with current controls;
never inject report HTML, scripts or raw model markup into the WebView.

Preserve current independent lifecycle/read-lens epochs, context/session fencing,
operation/client/run identity, acknowledgement uncertainty, close retirement,
cleanup retention and source-token freshness. Observer switching clears old
private bodies and stale completions without cancelling or rekeying execution.
Selecting a source/row cannot relabel a saved selected run or its displayed receipt.
Changing story/session/branch/head/Play-Lab availability or disposing the surface
retires its old presentation. A late response cannot repopulate it. Cleanup status
and retry remain available after Story Lab permission is lost.

## Inspection and existing resource owners

All evidence/diagnostic requests retain native Story Lab/read capability plus
appropriate observer checks before binding/row/source/file probes. Player/NPC
views use Rust-filtered Query2; raw receipts/capture/outputs and diagnostics remain
behind existing omniscient inspection rules. Neither changing a UI lens nor
viewing an omniscient result alters character knowledge or generation access.
Metadata/read_summary remains separate from private body data. Cold shared open
has no grant argument: desktop must refuse permission before opening the path.

Use the same single parent Job/worker and WindowLease identity, not an additional
runtime/worker registry. Keep selected TTL 300s, four presentation clients, 32 saved
selected runs and 32KiB index limit. Keep the evaluation owner's 32MiB/run,
256MiB combined builtin/curated/selected/full library and 64MiB free-space floor;
no new selected3 bucket may evade the aggregate. Keep all existing safe integer,
directory/entry/link and output caps. No automatic evidence expiry/deletion.
The shared ledger limits and entry-origin clock from the prerequisite contract
remain unchanged; frontend polling is not a deadline/reset authority.
As clarified by Root in `ea464324`, PREPARATION_MS=120,000 is the existing durable
preparation reservation and aggregate-capacity allowance, not a hard timeout for
blocking filesystem/snapshot work. Retain the run/resume entry Instant across
refresh and both ledgers, charge actual known opening work (including work above
that reservation), and preserve full unknown reservations. Keep the unchanged
30-minute aggregate accounting and 60-second absolute turn/watchdog machinery.
Do not invent physical model-load/elapsed evidence, reset that clock or claim an
independent hard filesystem cutoff from source wiring or reservation-capacity
tests. Those tests do not advance a physical 120-second opening or 60-second turn.

Scripted selected3 does not need a model reservation or setup. Reuse its actual
Store copies, not live workspace registration/import. Source immutability means
whole retained file inventory checked where asserted, including reference files.
Cooperative locks/pins are not universal filesystem-race or OS isolation proof.

## Narrow supersession of identified availability and scripted-refusal assertions

Changing availability requires an explicit reviewed behavior change, not removal
of inconvenient invariants. Retain the original source in Git and identify the
original/derived oracle hashes. Independent new behavior tests freeze first.

1. `apps/desktop/src-tauri/src/evaluation/comparison/scene_read_review.rs` has
   `v4_selected_prepare_refuses_both_lanes_before_consent_target_or_model_reservation`.
   Replace only the obsolete scripted-refusal expectation with actual scripted
   preparation/consent semantics; retain the native refusal and no model-owner,
   no destination-before-start, source immutability, consumed-token and lock checks.
   Its exact old unavailable-array assertion also follows the new precise note.
2. `scene_v4/desktop_api.rs` currently returns the blanket
   `selected_protocol4_rerun_not_implemented` unavailable note. Proposed replacement:
   `selected_protocol4_native_rerun_unavailable`. The full report reader remains
   read_only true/execution_available false; its inspection capability itself
   never becomes an execution grant. Update related UI copy only at this gate.
3. The new shared FIRST helper `source_binding` in
   `scene_v4/selected_v3/review_tests.rs` asserts that blanket old note to ensure
   shared code did not silently enable desktop. Preserve that stage's frozen
   source/evidence, then supersede only this stage-specific note assertion with
   the precise native-unavailable note and read-only/no-execution checks. Do not
   alter its source/request/prefix, recovery, cancellation, access or accounting
   oracles. Root must allocate this existing test path explicitly before editing.
4. `crates/locallore-eval/tests/scene_comparison_reader_v4.rs:145` asserts the exact
   old unavailable array. Supersede only that note expectation. Preserve report
   equality, protocol/arm descriptors, read-only/no-execution, human0/unreviewed/
   unaccepted state, actual row/turn count, source hashes/heads and all subsequent
   evidence/observer and source-immutability assertions.
5. `apps/desktop/src-tauri/src/evaluation/comparison_run/scene_native_review.rs:908`
   has another exact old-array assertion. Its enclosing
   `separate_actual_scripted_scene_source_is_raw_readable_but_both_selected_lanes_refuse_before_consent`
   also panics on consent and requires failure for both lanes. Explicitly split
   only that obsolete scripted-refusal branch into actual scripted preparation/
   consent expectations; keep the ApprovedNative refusal before consent, null
   plan/run capabilities on refusal and no selected destination. Preserve actual
   source/report row assertions, whole source inventory, native runtime/cleanup
   ownership and `f.sequence()==0` (no real-model execution). No ownership/runtime
   assertion is waived to permit scripted preparation. Update the availability
   note only to the same precise value; Root must allocate this test path too.
6. `apps/desktop/ui/comparison-reader-journeys.ts:1334` currently requires the old
   blanket sentence in `actual-protocol4-visible-scope-and-limits`. Supersede only
   that text clause with the precise scripted-available/native-unavailable copy.
   Preserve its literal/relevant scene labels, recorded narrator-input check,
   needs-improvement assessment and all other actual IPC/render assertions. Root
   must explicitly allocate this existing journey path before the UI copy changes.
7. The pending shared writer in
   `crates/locallore-eval/src/local_lane/comparison/scene_v4/selected_v3.rs` currently
   emits `selected_protocol4_gui_unavailable` from `report` (inspected at shared
   branch commit `ea464324`, not claimed accepted main). That note is truthful for
   the current shared-only stage and must remain unchanged there. The later desktop
   gate must explicitly allocate only its replacement with
   `selected_protocol4_native_rerun_unavailable`. Keep all other unavailable/
   limitation entries and row, ledger, timing and human-quality evidence unchanged.
   `SelectedEvaluationView` displays the actual diagnostics.unavailable list; do
   not suppress the old note only in the UI to conceal an inconsistent current
   writer. Preserve all historical report.json/HTML and frozen evidence bytes;
   no migration, backfill or stored-file rewrite is authorized. A newly computed
   read projection may describe current adapter availability without recasting
   an original stored report as having been generated with desktop support.

Accepted anchors were inspected at main `a6f235ae`, with the pending shared writer
explicitly anchored separately above; refresh the actual
symbol/assertion sites before implementation rather than assuming line numbers
or this list are exhaustive. Source-only changes in this proposal and the current
shared gate do not change any of these production notes or test expectations.
`apps/desktop/check-scene-reader-review.mjs` also retains an old-note mock snapshot
and its lossless-decoding expectation, and
`apps/desktop/check-narration-diagnostic-reader-review.mjs` has an old-note mock
fixture. These may remain historical reader-fixture compatibility cases unchanged;
do not relabel their data as current desktop availability or infer that their old
note grants execution. Changing a real note does not require rewriting history.

Selected1/2 behavior tests and unrelated reader/harness oracles stay unchanged.
Missing APIs or registrations are SETUP/unrun; do not report zero selected tests
as a pass or call source-only construction a behavioral failure.

## Independent FIRST and actual verification proposal

Freeze independent source before production, with exact branch/commit, counts,
hashes, construction limits and ownership release. Different-author code follows
only after Root accepts this contract and those tests. Source/Git checks are the
author allowance; Root alone admits and runs each finite heavy workload.

Native manager/closed IPC tests should use fresh actual scripted source4 paired
and rollout inputs, including noninitial selection and exact two-arm prefixes.
Cover native refusal while another model reservation is held, consent deny/cancel,
duplicate/lost-ACK start, shared-job contention, wrong lease/client/source token,
stale source/binding/index, cold catalog/open/resume and completed unchanged resume.
Use actual saved receipts and full source inventories. Assert the intended protocol
route and no source2/3 regression. Distinguish manager tests from actual IPC.

Frontend FIRST should cover all closed V3 keys/nulls/types/constructions/versions,
source/resume/read binding confusion, wrong returned turn/arm/scope/head, oversized
records, hostile parsed objects, detached frozen results and bounded projection.
Exercise the actual controller and Main/App selection path, preserving context,
pending/cancel/retry/late reply, source refresh, observer fencing and cleanup state.
Missing raw duplicate detection in parsed objects stays a stated boundary.

Before native harness execution, freeze a fixed source4 mode/journey contract.
Existing `LOCALLORE_D07_SCENE_COMPARISON_READER=1` app-owned fixtures already use
public Scene4 paired/rollout producers. Reuse them with the selected harness;
do not add model configuration, a free-form fixture loader, arbitrary command/path/
code/file execution, generic IPC or a remote debugging server. Development/test
hooks stay absent from ordinary production output and must be checked there.
Consent hold/deny and lost-ACK controls are synthetic doubles, not human approval.
The shared cfg(test) after-arm cancellation control is not available in a normal
native build; do not claim a native between-arm interruption without a separately
accepted finite mechanism. Shared/manager cancellation evidence can be separate.

Actual hidden/unfocused application WebView2 execution should use the same
frontend controller/actions and native IPC as UI. Capture coherent semantic/UI
snapshots with story/session/scope, observer, selected source/row, before/after
revision, pending operation, displayed receipt/result/error and cleanup state.
Capture application-owned render images only, with each image individually viewed
for wrapping, overflow, clipped controls, correct state and private-body removal.
Check narrow/wide layouts and genuine 150% text scale by asserting actual scale
state/classes/computed fonts; a wide viewport or a clamped 1.5 value is not 150%.
Record actual native version/user agent and distinguish installed-file metadata
from loaded-module proof. No desktop capture/input/window activation or user click
through is needed. Headless render, VM/fake transport, shared Rust, manager tests
and actual native IPC/WebView results must be separately reported.

Include initial and cold-restart scripted selected3 open/inspection, proper native
unavailable presentation, pending consent/cancel/deny, same-operation retry, context
retirement, observer isolation, receipt/state inspection and source immutability.
No model assets or real inference runs are necessary to qualify this adapter.
Run appropriate frontend, shared Rust, native compile/tests and Rust Android host
compatibility checks; an Android host compile is not emulator/device qualification.
Do not run ADB, JVM/Gradle, SDK, emulator, device or stopped OS/network probes.

Use the corrected bounded process-owner policy accepted with D06 as the launcher
baseline. Do not copy the older selected launcher unchecked: pipe errors and failed
inventory must latch unknown state, preserve evidence and prevent unsafe restore.
Require exact direct-child identity, bounded stdout/stderr, finite deadlines and
settlement, source identity/cleanliness, one workload at a time, fail-closed storage
inventories and normal-build restoration rules. Closing a direct child is not a
proved process-tree containment guarantee. Record unavailable checks honestly.

## Storage and handoff

All local project source, scripts, cache/temp and generated evidence remain
physically on D, with project commands started there and process-local TEMP/TMP
set to `D:/Dev/_Temp`. Preserve installed tooling/global caches. Proposal source
is bounded below 1MiB. This document admits no build, fixture, native run or new
experiment root. Before later execution Root declares one cumulative finite
budget for fixture/native packets, source/frontend outputs and target growth,
measures baseline/free space and specifies exact output/retention paths. No cap
reset, repeated fresh roots, model copies/downloads or deletion to regain budget.
Keep generated artifacts local and gitignored/outside source by default; retain
failures, frozen captures, recovery and ignored/uncommitted data unchanged.

The next reviewable gate must report exact source/test lineage, commands, counts,
environment versions, elapsed results, retained failures, hashes/packet locations,
independent findings/fixes, native-versus-headless limits and normal build status.
GitHub #29 owns claim/evidence/task status; this contract does not duplicate that
tracker. Full D07, real-model quality, Android runtime parity and stopped platform
security gates remain separate. Do not merge another owner's PR, change settings,
publish a release or affect the protected concurrent chat/resources.

## Root accepted desktop interface before independent FIRST

Root accepts this corrected proposal for the bounded scripted desktop adapter on
accepted main `4c83ed79e0e42bb489a46fbd777aecdcfc2838d8`, merged PR268. Its tree
matches the reviewed shared gate. Postmerge types, seven shared clock tests,
Android Rust Windows-host check and normal unlaunched desktop build pass.
Original proposal dd2f8ca1 and correction bfeb7ce1 remain in history. The original
426-line proposal is retained above; this append updates acceptance and fixes
test-facing interface choices before any desktop implementation or supersession.

Use the proposed V3/source4 closed native Protocol/Plan/Opened/prepared/index
dispatch and private NativeDispatchFailure<R> wrapper. Owned V1/V2 failures keep
their existing retained-cleanup behavior; V3 Unavailable never calls reservation.
Map SelectedNativeUnavailable to NativeUnavailable before generic Selected*
integrity handling. Require prepared3 source_binding to equal the native retained
source binding both when creating and loading an index, before destination writes.
V3 permits only scripted_selected_case. No Core native-failure visibility or
reservation interface is widened, and no new IPC field or action is introduced.

Keep SelectedSourceIdentity exactly its current three keys. The controller's
prepare(source,row,lane,expectedSourceProtocol?) optional fourth argument is
presentation-only type 2|3|4. It never goes into the request body. Bind prepare
response version to any supplied expected protocol and bind every prepared3
source_binding to the actual requested source binding. Preserve three-argument
old callers, all existing context/client/operation/read epochs and unknown-ACK
cleanup behavior. Do not turn an untrusted returned value into its own expectation.
App passes the actual ready reader's source version. A source4 native option is
disabled and stale local lane state normalized before enabling scripted Prepare;
an explicitly displayed native choice must not silently dispatch scripted work.

If sharing the existing private sceneConstruction validator, export the narrow
alias checkedReaderSceneConstruction. Retain its existing reader error category;
the selected decoder translates errors to SelectedEvaluationWire. All prepared3,
summary3 and diagnostics3 key sets/nulls/bounds above are accepted exactly.
Preserve source2/selected1 and source3/selected2 behavior and old default lanes.

Independent FIRST paths are proposed as only NEW
apps/desktop/check-selected-scene-v4-review.mjs and
apps/desktop/src-tauri/src/evaluation/selected/scene_v4_review_tests.rs. Root will
claim them separately before authoring. The native file is a child of existing
selected::tests, registered by Root using the existing #[path] pattern, so it can
reuse actual manager/lease/ModelManager fixtures and public Scene4 producers
without exposing fixture helpers or creating another model owner. Prefer actual
existing manager APIs; report any construction gap before freeze, never fabricate
a plan, index, report-to-Engine authority or source receipt. New source fixtures
may be generated only by Root's later admitted execution. Source-only authors
do not format, compile, run tools/workers or create fixture roots.

The listed existing scripted-refusal/note/writer/UI assertions are approved only
for those narrow stage supersessions after new FIRST release. Preserve their
original source/hashes/history and all remaining ownership/privacy/state/runtime
oracles. An informed player may read the fact explicitly granted by the seed;
character/history exclusions and exact Rust Query2 equality remain required.
Do not reproduce the shared gate's corrected blanket sentinel assumption.

Actual hidden WebView/IPC journeys, fixed native fixtures/labels and bounded
launcher policy require a separate frozen harness allocation before editing those
paths. The Core cfg(test) after-arm control is not an app test hook. Distinguish
controlled fixture loss, manager cancellation and post-IPC reply holds from actual
between-arm native interruption or held Rust inference. No new real-model cohort,
assets, SDK/device/emulator, OS probe, desktop input/capture/activation or generic
debugging service is admitted. Later execution has its own cumulative storage
baseline/budget; this acceptance admits source-only FIRST, not a runtime root.

Root owns coordination, existing shared registrations/note supersessions and
integration; disjoint native/frontend production paths follow independent test
freeze. Source authors keep each new contribution below1MiB on physical D and
preserve the current shared gate's original failed/qualified packets unchanged.
This acceptance does not enable the UI, accept the later adapter or close D07.

### Decoder versus controller immutability precision before FIRST freeze

Existing standalone selected decoders return detached mutable DTO copies; an
accepted selected2 regression intentionally mutates its detached copy. Preserve
that behavior for V1/V2 and use the same detached-copy convention for V3. The
frozen-record requirement above applies to the controller's recursively frozen
published state, not a new standalone decoder freeze. FIRST must distinguish
decoder detachment from immutable controller publication, preserving both owners
without changing old tests or adding a special V3-only freeze rule.

### Selected parsed-input hygiene precision before FIRST freeze

For the existing public selected decoder/transport boundary, V1/V2/V3 valid
parsed-JSON behavior stays compatible. Reject non-wire real objects/arrays such
as accessor/toJSON payloads without invoking their getters or toJSON during a
size check or copy. FIRST may assert those explicit counters along with finite
wire errors, inherited/non-enumerable/symbol/extra keys, cycles, bigints,
undefined and nonfinite values. Detached standalone outputs remain mutable;
controller publications remain recursively frozen. Use a narrowly bounded
selected input validator/copy or an established compatible helper, not a new
schema, global serialization framework or persistence owner.

This is not a promise to prevent arbitrary Proxy traps/JavaScript side effects,
detect duplicate raw JSON keys from an already parsed object, authenticate input
or replace native/Core permission enforcement. Preserve the old valid-wire tests;
do not loosen their schemas or rewrite old fixtures to satisfy the new cases.
