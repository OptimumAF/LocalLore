# Selected Protocol4 scene rerun proposal

2026-10-29. **Proposal only: not an accepted API, implementation or test result.**
Refs #29 D07.04/D07.06, [allocation6505713281](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6505713281).
Inspected accepted main: `f4d2de0cb25fcc8dc2db48558fb489701f251fd8`.
Root must accept interfaces, then freeze independent FIRST source, before production.
No runtime/model/native/device/OS probe or new run directory was used for this proposal.

## Existing capability and the actual missing adapter

Source anchors refer to the inspected commit. Paths below start in
`crates/locallore-eval/src/local_lane/comparison/` unless stated otherwise.

| Accepted source/evidence | Capability and limit |
| --- | --- |
| `scene_v4.rs:989`, `:1008`, `:1080`; `scene_v4/desktop_api.rs:27`, `:77`, `:125` | Full scripted4 execution, explicit optional companion entry, strict cold inspection and read capability exist. The reader explicitly reports `selected_protocol4_rerun_not_implemented`. |
| `scene_v4.rs:504`, `:571`, `:652`; `turn_execution.rs:119` | Actual committed-turn recovery, shared Host/Store execution, checkpoint/ledger settlement and evidence-derived TurnReportV4 already exist. No new narrator, validator, provider or canonical persistence is needed. |
| `literal_v3/selected_v2.rs:133`, `:220`, `:363`, `:645`, `:673` | Selected2 binds source3, derives actual two-arm prefixes, preflights and resumes through existing owners. Its manifest explicitly requires source3/version2 and its rows are TurnReportV3. It is not a Protocol4 adapter. |
| `selected.rs:45`, `:88`, `:475`, `:491`, `:564`, `:610`, `:823`, `:928` | Existing SelectedIntent, selection/input DTOs, single-link/directory pins, disjoint target admission, partial-prefix validation, ledgers and escaped reports can be reused. |
| `apps/desktop/src-tauri/src/evaluation/selected/versioned.rs:9`, `:34`, `:114`; `ui/selected-evaluation-model.ts:68`, `:90` | Desktop selected versions are currently source2→selected1 and source3→selected2. Source4 has no prepared plan/opened-read dispatch or frontend selected3 decoder. |
| `apps/desktop/src-tauri/src/evaluation/selected.rs:742`, `:1317`, `:1378`; `scene_v4/native.rs:137`; `selected/native_owner.rs:15` | Window/job admission and shared model reservation/uncertain-cleanup ownership exist. Full native4 execution exists through its own reservation path. These do not confer native selected4 support. |

The existing [selected scripted contract](D07_SELECTED_CASE_SCRIPTED_CONTRACT_2026-10-25.md),
[selected recovery qualification](D07_SELECTED_RECOVERY_QUALIFICATION_2026-10-25.md),
[selected2 qualification](D07_LITERAL_SELECTED_SCRIPTED_QUALIFICATION_2026-10-26.md)
and [Protocol4 qualification](D07_SCENE_COMPARISON_PROTOCOL4_QUALIFICATION_2026-10-27.md)
establish reusable designs and their source-bound evidence. Their historical PR or
dependency status is not current status. Current #29 records the owner-accepted
reader PR262/main f4; that gate does not implement selected4 reruns.

## Smallest staged gate and public API proposal

First gate: a **scripted-only shared Rust producer and strict selected reader** in
NEW `scene_v4::selected_v3`, plus its narrow source-access bridge. Selected manifest,
report and read metadata use **selected version3, source_protocol_version4**.
The version3 tag is a selected artifact version, not a full Protocol3 report.
Do not relabel TurnReportV4 as V2/V3, route4 into literal selected_v2, or counterfeit
`run.json`/a full48-row report. Existing selected1/2 bytes, defaults and APIs stay closed.

Reuse shared `SelectedIntent`, `SelectedLane`, `desktop_api::RowId`, `Arm`,
`EvidenceRequest`, `Cancellation`, `Observer` and existing fixed-error Result style.
Proposed signatures mirror selected2:

```rust
pub struct PreparedSelectedPlan { /* opaque, native-owned; no Serde/Clone/Debug */ }
pub struct SelectedComparisonReportV3 { /* serialize-only; not execution authority */ }
pub fn prepare_selected(source_dir: &Path, expected_source_binding: &str,
    row: &RowId, intent: SelectedIntent, cancel: &Cancellation)
    -> Result<PreparedSelectedPlan>;
pub fn prepared_metadata(plan: &PreparedSelectedPlan) -> Result<Value>;
pub fn run_selected(plan: PreparedSelectedPlan, new_dir: &Path,
    cancel: &Cancellation) -> Result<SelectedComparisonReportV3>;
pub fn resume_selected(dir: &Path, source_dir: &Path, expected_binding: &str,
    cancel: &Cancellation) -> Result<SelectedComparisonReportV3>;
pub fn inspect_selected(dir: &Path) -> Result<SelectedComparisonReportV3>;
```

Admit only `SelectedLane::ScriptedBaseline`; reject ApprovedNative with
`SelectedNativeUnavailable` before source/destination probes, provider/factory,
model assets or reservations, in builds with and without local-model. No native
selected4 function, asset import or automatic fallback is included in this gate.
An originally native source remains labelled source_native with its source_profile;
the new rerun's lane/profile remain genuinely scripted.

Minimal bridge: add the same comparison-private just-opened typed snapshot accessor
as `literal_v3/desktop_api.rs:121` to Scene4's OpenedComparison, plus narrowly permit
Scene4 selected code to call the existing snapshot validator on refresh. The plan
owns that actual opened capability/run lock and pins; JSON metadata cannot construct
it. A cached accessor is only for the just-validated open, not fresh integrity proof.
No public Engine constructor from report JSON, raw path RPC or second read owner.

Second, separately accepted gate: extend the existing desktop selected versioned
Plan/Opened/index dispatch and selected DTO/view/controller for source4→selected3,
using existing IPC actions, native lease, explicit preparation/start consent and
job/cleanup/catalog owners. Do not remove the full reader's unavailable label or
enable its rerun control merely because shared Rust tests pass. Native selected4
requires its own later reservation/cleanup/resource contract and qualification.

## Exact source and destination authority

Preparation takes the existing source `run.lock` read-only without creating it,
retains ordinary-directory pins and strictly validates the whole full4 source,
including both arms, required files, source/suite/recipe/profile and reference.
Resolve the clicked turn to its actual frozen corpus index0..23; clicking either
arm chooses that same index and attempts **both** constructions, left literal
scene and right relevant-memory scene. Require both source checkpoints at that index.
Missing other arm/unknown row refuses; do not substitute the next available row.
Require the actual supported Domain1 seed/history before destination mutation;
Domain2 is not promoted through this scene recipe adapter.

Derive each before Engine by cutting its actual Store at StoredTurn4.before_head.
Validate actual request, source turn/index, scope, full typed Intent/text, before/after
heads, semantic input/output and mechanical hashes against the checkpoint/Store.
Paired input prefixes equal the validated reference prefix. Rollout keeps each arm's
actual divergent accepted prefix. Preserve original seed/scope/turn IDs and exact
requests; generate no preceding turns. An accepted source receipt is not required
for a failed source row, but its real before Engine and checkpoint binding are.
Fail/dependency/guard metadata cannot create missing canonical receipts.

The destination is a new disjoint pinned ordinary directory, not a live-story import.
Reuse existing isolated evaluation Store copies with original scope IDs for exact
input parity; do not register them as live workspace stories or claim a new canonical
branch identity was created. Same path, ancestor, descendant, reparse/alias or existing
target refuses without deleting/repairing anything. Source and reference remain
read-only throughout; original evidence and failed/frozen packets stay intact.
Existing cooperative locks, directory pins and ordinary/single-link checks are not
a universal adversarial filesystem-race or OS isolation guarantee. No new platform
probe is proposed as evidence for this gate.

Consuming run starts the existing preparation clock and revalidates source/input
identity before target, ledger or provider mutation. Require actual current-source
matching for prepare/run/resume, including paired reference source matching. A
retained historical source may remain inspectable but is not thereby rerunnable.
SourceMismatch is honest refusal; no source-hash rewriting, compatibility bypass,
native cohort rerun or automatic fresh-source generation is authorized here.

## Closed identity, reports and bounded read API

Proposed `selected.json` keys are exactly the existing selected2 identity extended
to the distinct version/arm type, not an opaque full-source/profile escape:

```text
version, run_type, source_protocol_version, arms, client_id, binding,
source_binding, source_kind, source_profile, source_native, selection,
lane, profile, suite_sha256, source_sha256, source_reference_sha256, source_inputs
```

Constants: version3, run_type selected_case, source_protocol_version4,
lane scripted_selected_case, exact ArmDescriptorV4 pair. `selection` remains
`{turn,clicked_arm,index}`. `source_inputs` contains two exact left/right
`{arm,scope,before_head,request,prefix_sha256,input_semantic_sha256}` entries.
Prefix hash uses actual before.receipts; source_binding is the full reader's snapshot
binding, while binding hashes this complete selected manifest excluding binding.
They are not the full run manifest key and cannot be interchanged. Source profile,
native flag and reference hash describe the source; execution profile is the fixed
ScriptedBaseline profile and both scene constructions. Nullable reference stays
required; all codecs reject unknown/duplicate/missing keys and unsupported versions.
Hashes establish consistency, not authenticated history/model-output origin.

Report flattens that identity and adds exactly `rows`, `completed`,
`per_arm_progress`, `physical_setups`, `physical_setup_ms`, `native_load`,
`left_charged_ms`, `right_charged_ms`, `left_reserved_roles`, `right_reserved_roles`,
`human_reviewed`, `human_rubric`, `quality_accepted`, `unavailable`, `limitations`.
Rows are zero..two actual **TurnReportV4**, in left/right order, reconstructed by
load_turn4. Retain every required nullable field and actual phase/error/fallback,
construction/scene evidence, privacy status, admission, role/timing uncertainty.
Do not derive all-passed or scene-source validation from a committed row.
Progress is `{arm,state}` with not_started/interrupted/finished; finished requires
a validated terminal checkpoint. Completed means both finish, including failure,
cancelled, guard or dependency-only outcomes. No full-scene/sample count is claimed.
Scripted physical_setups0, setup time/load null, human_reviewed0,
human_rubric not_reviewed, quality_accepted false. JSON plus bounded escaped inert
HTML use existing publish_report; cached files never override actual inspection.

NEW `selected_v3::desktop_read` mirrors selected2's public signatures:

```rust
pub struct OpenedSelected { /* opaque held read capability */ }
pub fn open_read_only(dir: &Path) -> Result<OpenedSelected>;
pub fn summary(run: &OpenedSelected, native_inspection_granted: bool) -> Result<Value>;
pub fn evidence(run: &OpenedSelected, expected_binding: &str, arm: Arm,
    request: EvidenceRequest, native_inspection_granted: bool) -> Result<Value>;
pub fn diagnostics(run: &OpenedSelected, expected_binding: &str, observer: Observer,
    native_inspection_granted: bool) -> Result<Value>;
```
Use the existing strict pins/run lock, accounting seal, fresh revalidation and
render_evidence_view/missing_evidence paths; do not add a second renderer.
Prepared metadata is the existing versioned selected_prepared shape, now version3 /
source4 with exact V4 constructions. Read summary likewise uses selected_read3 /
source4 with binding/selection/lane/arm scope/before/optional after/availability and
read_only true/execution_available false. Summary omits outcomes/prose/full requests.
Its read binding seals actual manifest, validated turns/report and accounting;
it is distinct from the destination resume binding.

Raw receipt/capture/outputs and diagnostic projection retain existing access rules:
native grant plus appropriate observer, refusal **before** binding/row/source/file
probes. Query2 remains filtered by Rust. Diagnostic rows expose a finite explicit
projection of actual V4 phase/error/expected/failures/construction/privacy/fallback/
role/timing/receipt-presence evidence, not a full-report JSON escape. Reuse existing
bounded evidence wrapper/local context; never let inspection change character
knowledge, source filtering or generation. Cold open itself takes no grant: a future
transport wrapper must deny before opening it; do not claim old open_read_only does.

Proposed diagnostic wrapper keeps selected2's keys/versioned meaning, with version3,
source_protocol_version4 and exact V4 constructions. Its rows have exactly:
`turn, arm, phase, error, expected, passed, failures, quality_flags, roles,
roles_known, elapsed_ms, actual_receipt_sha256, construction,
construction_evidence_status, construction_evidence_reason, construction_matches,
privacy_evidence_status, fallback, repairs, recovered_without_checkpoint,
first_final_response_ms, commit_elapsed_ms, narrator_prompt_sha256,
narrator_schema_sha256, scene_frame_sha256`.
Do not retain obsolete selected2 `privacy_passed`, `context_evidence_available` or
literal-source-unit fields as invented V4 values. Wrapper adds human_rubric alongside
human_reviewed0/quality_accepted false. Both projection and source report are bounded;
raw outputs remain behind the separate existing evidence request/access gate.

## Admission, cancellation, recovery and quotas

Reuse shared validate_prefixes/Store bootstrap, Scene4 ready_turn4/execute_turn4/
load_turn4/make_row4, ActualTurn.checkpoint_and_settle and existing Ledger/finish_pair.
Validate both destinations before checkpoint decoding/admission: exact partial prefix,
full selected prefix, or that prefix plus the identical selected committed Request.
Changed text/Intent/seed/scope/head, extra suffix, checkpoint mismatch or alias refuses
before either arm reserves work. Preflight both required invocations/admissions before
either durable reservation or Store bootstrap. Use existing alternating-first order
for the original index/kind; exclude only measured other-arm time.

Cancellation before admission makes no provider call. Between-arm cancellation keeps
the validated completed half for explicit resume. An actual committed receipt wins
over late cancellation. Failed/cancelled/dependency/guard checkpoints are terminal
attempts, not invitations to retry generation. A genuinely new experiment requires
a new client and destination. No silent turn renumbering, request regeneration,
unknown-work refund, fresh deadline or repeat-until-good prose.

Committed-without-checkpoint recovery uses actual Store lookup and ready_turn4
**before** constructing any script/provider or admission. It never commits twice;
absent trace/raw/capture/timing/roles/validation cause remain unavailable and scene
construction evidence stays recovered/unqualified. Save only the actual recovered
workflow row through existing bounded write/settlement; preserve charged unknown work.
An interrupted bootstrap may refuse cold inspection; resume can complete it only
after freshly validating against the actual source. Completed resume still validates
the exact source/manifest; after that it returns read-only with unchanged whole
destination inventory, no invocation/admission/provider/setup/report rewrite.
Preserve existing `TerminalCheckpointMissing` refusal for a cancelled/failed/stale
Store key without its checkpoint (`selected.rs:665`); do not rebuild its missing cause
or clear that key for generation. Missing/malformed partial manifest/identity is not
recoverable canonical bootstrap and cannot be silently overwritten or repaired.

Keep current caps: manifest128KiB, prepared/read metadata16KiB, checkpoint256KiB,
report JSON/HTML2MiB each and evidence256KiB, plus existing capture/raw limits and
selected directory/file guards (512 entries per checked directory). Ledger remains
32 invocations/admissions per arm,96 reserved roles,30min active time,120s preparation,
60s turn reservation/absolute-turn machinery and3s cleanup reserve. Profile's existing
120s deadline is not an excuse to reset/extend that shared turn clock.
Desktop owner retains32MiB/run,256MiB library and64MiB free-space floor; standalone
Core is not a new global library quota manager. Later desktop integration must reuse
that owner and fail closed at its existing checks. No cap increase, new retention
store, atomic-rename claim or generic persistence engine. Root separately admits any
future test/build artifact budget on D before execution; none is admitted by this doc.

Optional full4 narration-diagnostic companions are **not** source-read/rerun
prerequisites or copied authority. Do not harvest, reconstruct or add selected
companions in this gate. Ordinary extra source files retain the existing full-loader
meaning: unvalidated extras are not causal evidence. Missing historical30causes remain
missing; both retained human assessments remain needs improvement.

## Independent FIRST and later qualification

Freeze finite actual-producer tests before code, including noninitial paired and
rollout selections, failed-source row inputs, real divergent prefixes and both exact
scene constructions; no copied validator or private report-to-Engine reconstruction.
Verify new selected3 closed fields/required nulls/V4 descriptors and old1/2 rejection
and regression bytes. Current scripted sources are future admitted fixtures, not new
model runs. Historical source drift refuses execution without losing read evidence.

Required hard oracles: source locks/immutability including unclicked arm; native-lane
early refusal; client/binding/row/cancel/source/reference faults before writes;
disjoint/existing/metadata alias controls using accepted fault seams, with no new OS
probe claim; exact source/destination request/prefix checks; guarded/dependency/failed
phases; half-cancel/resume; capacity/deadline/no-refund boundaries; real committed Store
workflow-file-loss recovery; partial bootstrap; completed byte-identical resume;
tampered checkpoint/receipt/capture/raw/ledger/source/read binding; read permission
before probes, actor canaries and no source/canonical/knowledge mutation. Missing
construction or APIs is setup/unrun, not behavioral RED; controls remain labelled.

Only after the shared gate passes: independent desktop FIRST for versioned routing,
native lease/consent/client epochs/late worker cleanup and selected3 safe decoding,
then actual scripted native IPC/WebView journeys with bounded local semantics/errors
and individually inspected app-owned images. No desktop control, real inference,
asset/SDK/device/OS experiment, quality acceptance or full epic completion follows
from source tests. Core shared gate first; desktop scripted integration is the next
runnable stage, and native selected4 remains a separately owned later task.
