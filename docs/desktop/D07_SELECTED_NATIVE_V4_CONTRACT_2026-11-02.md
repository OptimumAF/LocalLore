# Native selected artifact4 over scene protocol4

Refs #29 D07.06 supporting D07.03/.07; #28 D06.05; #21.
Root claim6586912289; `prep/scene-selected-native-v4`, accepted base`db2c23d0`.
**Source preparation only. No new API, check, build or execution is accepted.**

## Boundary and preserved contracts

Current source4 comparison has native full-run support and scripted selected3
support. Selected3 deliberately rejects ApprovedNative before source/assets;
its manifest/readers/profile/setup rules require scripted execution. Preserve
that behavior and every old assertion. Do not enable the desktop checkbox or
widen selected3 to make native data appear compatible.

Add `scene_v4::selected_v4`, a DISTINCT native-only selected artifact with
`version:4,source_protocol_version:4,lane:"native_selected_case"`. This version
is the selected artifact version, not a new scene-comparison protocol. Source4
scripted reruns remain selected3. Source1/2/3 and historical data are unchanged.

Reuse `native_selected_workflow::Workflow/run/finish_prepared`, `native_startup`,
`selected::native_owner`, `SelectedNativeReservation/SelectedNativeFailure` and
the actual scene `ready_turn4/execute_turn4/load_turn4` path. No new inference
provider, runtime owner, store, canonical format, memory rule or cleanup owner.
This is the existing Play Director/Narrator path; it does not enable Author.

First shared scope owns new `scene_v4/selected_v4.rs`,
`selected_v4/desktop_read.rs`, `selected_v4/first_review_tests.rs`, module
registration in `scene_v4.rs`, and ONLY private visibility of the existing
`selected_v3::SourceSnapshot` and `source_inputs` helper if required. Reuse that
actual before-Engine derivation once; do not change its implementation or any
selected3 manifest/API/read rule. No desktop/UI/worker/descriptor/profile edits
belong to this shared slice. Coordinator owns integration; independent FIRST
is frozen before production, on a separate serialized author branch.

## Public API and capabilities

The new namespace exports:

```rust
pub struct PreparedSelectedPlan; // private fields, no Deserialize or public constructor
pub struct SelectedComparisonReportV4; // Serialize, private identity/data fields
pub fn prepare_selected(source_dir: &Path, expected_source_binding: &str,
    row: &shared_read::RowId, intent: shared::SelectedIntent,
    cancel: &Cancellation) -> Result<PreparedSelectedPlan>;
pub fn prepared_metadata(plan: &PreparedSelectedPlan) -> Result<Value>;
pub fn inspect_selected(dir: &Path) -> Result<SelectedComparisonReportV4>;
// Both execution entry points are gated by feature="local-model".
pub fn run_native_selected<R: shared::SelectedNativeReservation>(
    plan: PreparedSelectedPlan, new_dir: &Path, cancel: &Cancellation,
    reserve: impl FnOnce() -> Result<R>)
    -> Result<SelectedComparisonReportV4, shared::SelectedNativeFailure<R>>;
pub fn resume_native_selected<R: shared::SelectedNativeReservation>(
    dir: &Path, source_dir: &Path, expected_binding: &str,
    cancel: &Cancellation, reserve: impl FnOnce() -> Result<R>)
    -> Result<SelectedComparisonReportV4, shared::SelectedNativeFailure<R>>;
```

The two-error `Result` above means `std::result::Result`; other signatures use
the existing evaluation Result alias. `shared` is the existing selected owner;
`shared_read` is the existing comparison read API, not a new request format.
Metadata/report JSON cannot construct a plan, reservation or generation grant.

Prepare checks cancellation, then client/binding syntax (`SelectedIdentity`),
then requires ApprovedNative (`SelectedLaneMismatch`). Without local-model,
return `NativeFeatureUnavailable` before source/assets/reservation/target I/O.
With it, obtain the current native profile using the EXISTING lane profile
function, resolve the selected corpus row (`UnknownRow`), open/retain the actual
source read capability, bind its current snapshot (`SnapshotMismatch`), derive
both before-Engines and validate the native manifest. Require current source
matching (`SourceMismatch`) as existing fresh selected preparation does.
Refresh rederives that whole manifest and each accepted-history basis from the
locked source; data-only plans and stale sources cannot authorize execution.

No generic scripted `run_selected` or `resume_selected` is added in selected4.
There is no silent scripted fallback, arbitrary source/profile/command selector,
model download, renderer-issued authority or new IPC operation.

## Closed native manifest and report

`SelectedManifest4` is private, deny_unknown_fields, with ONLY:
version, run_type, source_protocol_version, arms, client_id, binding,
source_binding, source_kind, source_profile, source_native, selection, lane,
profile, suite_sha256, source_sha256, required-nullable source_reference_sha256,
source_inputs. Fields have the existing selected3 meanings and types.

Require version4, source protocol4, run_type selected_case, ONLY native lane,
valid current whole arm family, client/hash/selection/source-input invariants,
and manifest digest excluding binding. Execution Manifest is scene protocol4
with native=true; source_profile/source_native remain INDEPENDENT provenance of
the source comparison. A genuine scripted source may provide the input to a
native rerun; that never converts its recorded past to native generation.
Fresh preparation chooses the exact current native profile; recorded validation
reuses the existing scene Manifest/profile rules without loading model assets.
Historical native reads must not require a provider or execution grant.

Private implementation seams for FIRST follow existing selected naming:
`new_destination`, `open_destination`, `validate_destination`, `inspect_work`,
`preflight`, `finish_workflow`, `report`; opaque plan has private
`source_dir,manifest,before` plus its held source capability. `Destination` has
private `dir,manifest` plus pins/lock. `Work` has private `turns,ready,ledgers,
needs_admission`. These are tests of actual implementation, not replacement
engines or exported test commands. Adding test hooks needs separate review.

Freeze these private seam signatures for actual FIRST fixtures:
`new_destination(&PreparedSelectedPlan,&Path)->Result<Destination>`,
`open_destination(&Path)->Result<Destination>`,
`validate_destination(&Path,&SelectedManifest4,Option<&[Engine;2]>)
 ->Result<[Option<StoredTurn4>;2]>`,
`inspect_work(&PreparedSelectedPlan,&Path,Instant)->Result<Work>`,
`preflight(&Work)->Result<()>`,
`report(&Path,&SelectedManifest4,&[Option<StoredTurn4>;2],&[Ledger;2])
 ->Result<SelectedComparisonReportV4>`, and
`finish_workflow(&PreparedSelectedPlan,&Destination,&mut Work)
 ->Result<SelectedComparisonReportV4>`.
Native Workflow's execute bridge has the additional existing
`Option<&LaneFactory>` argument; it may use None ONLY for actual ready receipts.

Report fields match the selected3 report data surface, with manifest4 identity,
actual native setup accounting and unchanged TurnReportV4 rows. Validate setups
through the existing SELECTED SetupRecord-v2/native=true helpers, not full-run
Session4 SetupRecord-v4. physical_setups is the number of validated setup records;
physical_setup_ms/native_load come ONLY from them. No setup records means0/null/
null plus explicit unavailable measurement, never proof of zero historical work.
Failed setup attempts stay failed and measured; a native label is not generation.
Keep `human_reviewed:0,human_rubric:"not_reviewed",quality_accepted:false`.
Record exactly one selected original turn per arm, not a full comparison.

Setup aggregation matches existing native selected2: checked sum of every
validated record.physical_ms; zero records means physical_setup_ms/native_load
both null; otherwise native_load is an ORDERED array of each record.load,
including null for failed loads, never a fabricated load-success object.
Always include `human_quality_not_reviewed`; zero setups includes
`native_setup_measurement_unavailable`; each failed setup includes
`native_setup_failed_invocation:{left_invocation}`. Existing bounded ledger
unavailable notes remain. Recovery must report roles_known=false, unavailable
construction/privacy evidence, passed=false and actual receipt hash/provenance;
construction_matches remains its actual helper result, not forced true.

Reuse bounded manifest/checkpoint/report/source helpers and all existing limits.
No overwrite of source history; target must be new/disjoint and ordinary/pinned.
Recovery imports only genuine validated Engine/Store receipts, with original
provenance. Missing checkpoint measurements/roles/construction evidence remain
unavailable and cannot be invented from a successful canonical replay.

## Lifecycle, timing and uncertain ownership

Capture entry Instant before fresh source/target/work preparation. Preserve the
same clock through refresh, reserve, preflight, startup, execution and cleanup;
use native_startup's existing preparation_deadline/check_preparation. Do not
change/reset/clamp established preparation/invocation/role/cleanup limits.
Preflight BOTH arm ledgers before reserve/assets or target mutation. Preserve
existing preflight ordering and unknown-role/time refusal. Reserve once only
if unfinished work actually needs generation. Both invocations become durable
before assets/startup through the shared owned workflow.

The codec-specific Workflow passes the supplied Native LaneFactory into actual
scene Job4; only imported receipt/checkpoint recovery may execute with None.
No actor observer or generation audience changes during read/inspection.
Selected4 Job4 keeps diagnostics=false; do not borrow the full-run narration
companion namespace or manufacture selected diagnostic evidence.

Retain existing panic/poison/WouldBlock/cleanup uncertainty behavior. Unknown
cleanup retains the actual reservation/runtime ownership pair and returns its
existing typed failure; never settle/publish/refund/replace the owner. Known
cleanup may publish honest partial/failed accounting, then return the error.
Completed CURRENT-source resume is read-only even at the invocation cap: no
new reservation/assets/provider work, invocation or rewrite. Source and full
manifest equality are still required before that early return.

## Read-only capability and later desktop routing

New `desktop_read` exports opaque `OpenedSelected`, open_read_only, summary,
evidence and diagnostics with the SAME parameter types as selected3. Reply
version4/source_protocol_version4; read metadata says read_only=true and
execution_available=false. Revalidate files/manifest/checkpoints/accounting and
private snapshot binding on every read. Reuse exact existing early access checks,
Query2/receipt render helpers, source scope/observer/grant/privacy and reply bounds.
Actor-facing summary omits requests/outcomes/prose; spoiler diagnostics remain
explicitly privileged. Reading never reserves, loads, generates, mutates or grants.

Freeze exact Value projections against the accepted selected3 surface:

* prepared metadata ONLY version,kind,source_protocol_version,binding,
  source_binding,lane,selection,arms,constructions; kind selected_prepared,
  version4/source4/native lane. Each of two arms ONLY arm,scope,before_head,
  prefix_sha256,input_semantic_sha256. Bound the whole reply at16KiB.
* read metadata ONLY version,kind,source_protocol_version,constructions,binding,
  selection,lane,arms,read_only,execution_available; kind selected_read,
  version4/source4/native lane,true,false. Each arm ONLY arm,scope,before_head,
  after_head(nullable),available. Bound at16KiB and retain source-binding versus
  private-read-binding distinction; no execution grant in either.
* diagnostics ONLY version,kind,source_protocol_version,constructions,binding,
  lane,completed,rows,physical_setups,physical_setup_ms,left_charged_ms,
  right_charged_ms,left_reserved_roles,right_reserved_roles,human_reviewed,
  human_rubric,quality_accepted,unavailable; kind selected_diagnostics,version4.
  Each row uses the existing selected3 manual projection: turn,arm,phase,error,
  expected,passed,failures,quality_flags,roles,roles_known,elapsed_ms,
  actual_receipt_sha256,construction,construction_evidence_status,
  construction_evidence_reason,construction_matches,privacy_evidence_status,
  fallback,repairs,recovered_without_checkpoint,first_final_response_ms,
  commit_elapsed_ms,narrator_prompt_sha256,narrator_schema_sha256,scene_frame_sha256.
  Use the existing bounded_evidence limit; no raw native_load/report/request/
  prompt/receipt payload is added to this projection.

Follow-on desktop work must explicitly choose selected codec from source protocol
AND lane, and decode recorded selected-version4 separately. Existing source4->
selected3 scripted routing/readers stay unchanged. Reuse ModelManager evaluation
reservation, source transfer, lease/client/operation/consent/idempotency/unknown-
ACK and retained cleanup. Do not enable controls until shared/native/consumer
contracts and their own verification are accepted. This shared source slice
adds no manager/native IPC/frontend behavior or UI/render acceptance.

## Independent FIRST and evidence fidelity

Freeze tests before producer. Shared FIRST groups must cover closed version/lane
and cross-version denial; actual paired/rollout noninitial source prefixes and
immutability; identity/cancel/freshness/locks/disjoint/path precedence; both-arm
budget refusal before reserve/assets/mutation; actual imported-receipt recovery
and read-only completed resume; setup/checkpoint/report bounds and read grants/
observers/privacy. Preserve all existing selected1/2/3 tests, especially selected3
native refusal and zero-setup oracles. Reuse existing lifecycle/clock/protocol-
owner suites for the shared owner; do not duplicate it with a new fake owner.

Independent FIRST may use a Trap reservation whose assets method panics to prove
zero access. Genuine SCRIPTED receipts imported into Store prove recovery only;
their original provenance/unknown metrics stay labelled. Existing fixed protocol
child tests with execute forbidden prove cleanup only. None proves successful
Scene4 native inference. No mocked counter, native label, parsed report, headless
render or model-free unit run may be presented as actual native generation.

The independent source-only author may reuse the existing selected3 FIRST's
FIXED private Scene4 SOURCE-construction pattern: real Session4/execute_turn4,
left WrongCommand at turn0 then scripted baseline, producing real divergent
Store histories for rollout. No new production hook or native execution is
introduced. It is not permission to edit JSON/receipts/checkpoints to invent
divergence or native provenance. Paired sources keep their genuine shared
reference-prefix rules; do not force artificial divergence where the protocol
requires equal prefixes. Public scripted comparison sources remain the ordinary
paired/rollout baseline. This allowance is frozen before FIRST/producer and
requires separate future fixture/storage admission before execution.

Register FIRST under cfg(test), with feature-dependent individual groups and
imports gated by local-model. The prepare-order group must also compile without
that feature to cover NativeFeatureUnavailable before I/O. No positive native
setup/generation fixture is required to be fabricated: zero/unavailable recovery
and rejected cross-codec setup data are honest unit evidence; unchanged common
owner suites and separately admitted model/IPC/render work own positive evidence.

All source/tests are UNCOMPILED/UNRUN now. Current standing source authorization
does not spend any old/pending finite run grant. First author/integrator get
separate serialized branches; sources/output/temp stay physically D:. Preserve
all data, failed/frozen captures, foreign work and the padding PR364 branch.
Before code or runtime checks, inventory and admit exact tools, dependencies,
test fixture/output retention and original target growth with full bounds.
No fixtures, build/cache products or check records are created during this phase.
Compilation, Rust/frontend/Android checks, owned child/model/IPC/render and quality
journeys remain separate later gates. Do not close D07/D06/desktop on source review.
