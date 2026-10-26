# Native full-comparison desktop service and IPC contract

Supporting D07.03/.06/.04 under #29, Root claim6425826959. **FROZEN SERVICE/IPC
BOUNDARY / UNIMPLEMENTED / UNRUN at this freeze.** Root owns interfaces and
integration. Accepted scripted PR211 is merged as6099135e with an identical
qualified tree and post-merge frontend/normal-build checks. This next slice owns
the native Rust service and closed IPC only. The ordinary full-comparison UI
remains explicitly scripted until a separately frozen consumer and actual native
render/model journey are implemented. No native UI or model qualification is
granted by this contract.

Sources inspected: checked `7e628ded` and accepted `6099135e`. The current
desktop full-comparison adapter is scripted only. The accepted shared native
producer and existing model ownership APIs are dependencies, not evidence that
this proposed desktop path already executes native inference.

## Existing seams and narrow ownership

The adapter should call the existing seven-argument
`literal_v3::run_native_comparison<R: SelectedNativeReservation>` with its native
profile and actual `ModelManager::EvaluationReservation`. It must not introduce
another inference pipeline, ledger, canonical Store, model manager or provider.
The existing shared runner performs source/reference validation, both-arm ledger
preflight, durable reservations, startup, Host execution, factory drain,
`native_owner::finish_owner`, setup accounting and report publication.

Reuse `JobKind::ComparisonRun` and the existing parent registration, Job,
cancellation and worker. For native execution, initialize the same Job's
`selected: Some(SelectedOwnership { models, witness: None, retained: None,
cleanup_running: false })`; scripted jobs remain `None`. The field's current
name does not restrict it to selected cases: owned curated jobs already use it.
There is no expiring owner record, second registry or persistence of a runtime.

Frozen production allocation:

- `evaluation/comparison_run.rs`: version dispatch, native worker outcome and
  native start/resume/read selection within the existing service.
- `evaluation/selected.rs`: extract the narrow reservation helper and reconcile
  confirmed cleanup with a ComparisonRun presentation record.
- `evaluation.rs`: only necessary internal helper visibility/dispatch; preserve
  the existing Job kind and actual worker ownership.
- A new `comparison_native_commands.rs`, plus Root-owned registration/ACL/native
  confirmation; later frontend model/controller/view version closure.

No shared Core/Store/Runtime/schema change is proposed by this draft. A concrete
API gap must be returned to Root before expanding that allocation.

## Index coexistence in the same native-owned namespace

Keep `comparison-evaluations/<uuid>/desktop.json`, `work/` and paired-only
`reference-source/`. UUID leaves and paths are computed by native code. There
are at most32 runs **across both lanes**, not32 per lane; existing per-run,
whole-library, free-space, path pin and file-size caps apply to both.

Legacy IndexV1 remains exactly its existing scripted shape and serialized values.
Propose IndexV2 with the same exact keys:

```text
version:2, protocol_version:3, input_lane:"approved_native",
run_id, client_id, kind, initial_batch, created_ms, binding
```

Both IDs are lowercase UUIDs; directory name must equal `run_id`; batch is1..4;
`created_ms` is a nonnegative safe JS integer. IndexV1 requires
`input_lane:"scripted_baseline"` and `binding.native=false`; IndexV2 requires
`binding.native=true`. Exact native/shared source and profile eligibility before
execution remains the shared runner's decision, not an index assertion.
No model path, supplied profile, consent token or runtime owner is serialized.

Use one internal strict reader returning a closed `IndexV1 | IndexV2` enum.
Unknown version/lane combinations, unknown keys, malformed opposite-lane entries,
invalid UUIDs and contradictory shared manifest/index binding fail closed.
Validate a known opposite-lane index before filtering it from a public catalog;
silently skipping arbitrary malformed entries would hide corruption.

The existing wireV1 catalog includes only validated scripted entries and retains
its current bytes/keys for those entries. The new wireV2 catalog includes only
validated native entries. Neither valid lane poisons the other's catalog.
The internal cache and client uniqueness checks span both lanes: the same client
cannot be rebound to a different lane, kind or original batch. Exact same-lane
start retry returns its original identity. A cross-lane client collision is
`InvalidEvaluationInput`, not an unknown client that can start another run.

Legacy status/open/resume cannot execute or reinterpret a native token/index;
the proposed native equivalents cannot reinterpret a scripted one. A token on
the wrong command surface returns `UnknownEvaluationRun` without mutation.
Cold indexes remain metadata until actual shared inspection succeeds. Unknown or
missing work is not reconstructed from an index, seed or report label.

## Explicit native command and wire

Use new closed `evaluation_comparison_native`; no lane field is added to
`evaluation_comparison_run`. Existing command/actions/wireV1 stay scripted.
The new command uses `{action,query}` with compact UTF-8 query cap4096 bytes,
exact keys, lowercase UUIDs and positive safe JS operation IDs. Parsed `Value`
cannot prove absence of raw duplicate keys that a transport already overwrote.

| Native action | Exact query keys |
|---|---|
| `catalog` | none |
| `start` | `clientId`, `comparisonKind` (`paired`/`rollout`), `batch` (1..4) |
| `lookup` | `clientId` |
| `open` | `runId` |
| `status` | `runToken` |
| `resume` | `runToken`, `batch` |
| `cancel` | `runToken`, `operationId` |
| `close` | `runToken` |
| `managed` | `clientId`, `runId` |
| `cleanup_status`, `retry_cleanup` | none |

There is no renderer lane/provider/policy/profile/path, arbitrary source, native
model capability, consent boolean, cleanup ID or boolean cleanup proof.
Capture actual WindowLease/epoch and actual Models Arc in native code. All data
and admission actions require current actual Host Story Lab permission. Close
and generic cleanup must remain usable without that grant; they grant no read.
The public cleanup call still requires a valid current native lease, while the
internal CloseGate hook targets only its captured retired epoch.

Native status wireV2 retains the current status key set, with
`version:2`, `kind:"comparison_run"`, `protocol_version:3`,
`input_lane:"approved_native"`, and adds exactly:

```text
cleanup_required:boolean, cleanup_running:boolean, cause:closed_error|null
```

Retain existing identity/kind/batch/operation fields, `running`, `error`,
`completed_scenes:0..4`, `completed`, `report_ready`, `source_matches:boolean|null`.
Add phases `awaiting_confirmation` and `cleanup_required` to the existing phases.
Publish awaiting_confirmation before invoking the actual native callback, without
claiming model execution. `running` describes the
actual execution worker, separately from cleanup work. Closing presentation
does not claim that either worker or actual runtime has terminated. A report is
ready only after the shared runner has completed known cleanup and publication.

Native catalog wireV2 retains the current catalog keys with `version:2` and
native input lane. Each RunMetadata retains the existing seven keys, with
`input_lane:"approved_native"`; no full report, profile or asset path appears.
Metadata counts/ID bounds remain unchanged. Catalog cap remains64KiB and status
cap32KiB. The existing generic `selected_cleanup` version1 envelope may be reused
unchanged for the two cleanup actions: it is a separate closed cleanup DTO.

Native errors extend the existing closed set with `EvaluationModelBusy` and
`Cleanup`. Reuse the selected consumer's bounded native cause categories:
RuntimeBusy maps to EvaluationModelBusy; known cancellation to Cancelled;
deadline/budget failure to EvaluationBudget; unavailable feature/worker/model to
NativeUnavailable; uncertain cleanup to Cleanup. Unknown/private messages map
to EvaluationIntegrity or EvaluationInternal, never arbitrary text. `cause`
does not expose raw paths, runtime errors or prompts. No ScriptedBaseline fallback
is permitted when native execution is unavailable.

## Consent and actual execution order

Execution confirmation is an independent native
`FnOnce(&Value) -> Result<bool,String> + Send + 'static`, constructed by the
command and bound to the actual window. Its code-owned metadata identifies the
lane, fixed comparison kind/batch and native run; it contains no private full
requests, prompts, report or source paths. A true result creates a private,
one-use execution grant. It is never ReaderGrant or a serialized authority.

Native-only service signatures are frozen below. A denied callback returns the
shared closed category `Interrupted` (mapped to public `Cancelled`), rather than
an arbitrary desktop error string. Source and quota failures precede consent.

Sequence in the registered worker:

1. Check actual lease/cancel, pins, native index/lane, current source, quota and
   shared/reference inputs; completed current-source resume returns here without
   confirmation, model reservation, asset read, invocation or inference.
2. Invoke the existing shared native producer with its actual reference. Its
   reserve callback runs only after shared preflight of both arm ledgers.
3. Inside that callback, check lease/cancel, ask independent execution confirmation,
   recheck lease/cancel, then reserve through the owned helper. No asset getter,
   worker spawn or model load occurs before the actual shared reserve boundary.
4. The shared runner rechecks its absolute deadline/cancel after the callback,
   reserves both invocations and starts the existing runtime. No adapter-created
   replacement deadline or second load/settlement is introduced.
5. Transfer the typed outcome to the actual matching parent Job before any
   presentation publication or owner release.

The existing shared entry clock begins when `run_native_comparison` is called.
In this sequence, confirmation waiting inside the callback consumes that entry's
deadline; a late confirmation must fail before assets, even if the callback briefly
obtained a reservation. OS dialog responsiveness/cancellation is not proven by
that deadline. Reference creation and adapter work before entry require separate
elapsed attribution; do not claim they were included in shared ledger time.
The shared API may create provisional manifest/directories before asking for R;
denial must not be described as guaranteeing zero metadata files or a commit.

The completed shortcut requires actual fresh current-source validation. An
incomplete report with committed turns or lost checkpoints may still load the
model even when subsequent recovery generates zero roles. Do not claim the
stronger selected-case recovery optimization for full comparisons.

## Exact ownership and finalization

Extract a private `reserve_owned(models,expected_kind,epoch,operation)` from
`selected_reserve`. It must check the actual matching parent Job, exact Models
Arc and ownership payload, then install `R.cleanup_witness()` before returning R
to shared startup. Existing selected behavior remains equivalent.

Use a private typed full-run outcome carrying `result`, bounded `cause`,
`cleanup_uncertain`, and optional actual `(EvaluationReservation, SharedRuntime)`.
Consume `SelectedNativeFailure` exactly as the existing selected consumer does:
accepted uncertain handoff leaves the actual owner in Models with its captured
witness; rejected handoff returns the same R and Arc into the matching Job.
Neither path is replaceable by an error string or `runtime=None` assertion.

Install any returned owner pair before setting `job.worker_active=false`, even
after originating-window retirement. Clear the actual Job only for known terminal
cleanup/no-owner outcomes. Preserve it on uncertainty; prevent another evaluation
or model admission through the existing owner fence. TTL, close, stale callback
and drain cannot discard that payload or declare completion.

Reuse existing generic cleanup: actual rejected pair calls
`R.cleanup_retained(&sameArc)`; otherwise the captured witness selects
`models.cleanup_selected(&witness)`. Cleanup happens outside metadata/lease locks;
clear only the same job/epoch/operation/Models identity after actual confirmation.
An older confirmed witness has no effect on a newer slot. Generic cleanup already
accepts every `job.selected.is_some()`; add ComparisonRun presentation
reconciliation rather than another owner list. Do not wrap/drop a typed unknown
owner in the current scripted worker's blanket catch or unconditional job clear.

Confirmed cleanup does not reconstruct a missing publication or generate a
report. Reconcile a matching native record's cleanup flag; cleanup_required
becomes failed with its bounded diagnostic, and an already closed record stays
closed. Do not publish its private counts after retirement. Recovery/resume is
an explicit later action, with actual shared validation and no double counting.

## Exact Rust service interface

Reuse exported `FullComparisonStart { client_id:String, kind:ComparisonKind,
max_new_scenes:usize }`. Export new
`FullComparisonNativeResume { run_token:String, max_new_scenes:usize }`.
All service methods return the bounded `Result<serde_json::Value,String>`.

- `full_comparison_catalog_native/lookup_native/status_native/cancel_native/close_native`
  take `&self, &WindowLease, epoch:u64, granted:bool`, followed respectively by
  no extra argument, `client:&str`, `token:&str`,
  `token:&str,operation:u64`, `token:&str`.
- `full_comparison_open_native` takes `self:&Arc<Self>, &Arc<WindowLease>,
  epoch:u64, granted:bool, run_id:&str`. It only inspects, with no Models argument
  or execution confirmation.
- `full_comparison_start_native` takes `self:&Arc<Self>, &Arc<WindowLease>,
  &Arc<ModelManager>, epoch:u64, granted:bool, FullComparisonStart, consent`.
- `full_comparison_resume_native` takes the same context, replacing the start
  input with `FullComparisonNativeResume`.
- The start/resume consent is `impl FnOnce(&Value)->Result<bool,String> + Send +
  'static`. Exact-client retry, lookup, open and completed verified resume never
  call it or reserve/load assets.
- `full_comparison_pick_native` takes `self:&Arc<Self>, &Arc<WindowLease>,
  epoch:u64, granted:bool, client:&str, run_id:&str,
  impl FnOnce()->Result<bool,String> + Send + 'static`, and returns unchanged
  comparison-reader wireV1. It is independent of execution consent.
- Native cleanup IPC forwards existing `selected_cleanup_status` and
  `selected_retry_cleanup` signatures/closed DTO unchanged. No second cleanup
  registry is introduced.

The common catalog reader may use a strict validated version/lane enum over
shared index fields; a duplicate enum serialization is not required. Serialized
IndexV1 is unchanged. Current-source requirements apply before native execution;
catalogs may retain valid historical source metadata with no invented report.
Expose only the narrow existing selected error mapper and a private
`reserve_owned(models,expected_kind,epoch,operation)` helper as needed. Preserve
the old selected reservation behavior through that same helper.

## Read scope and frozen oracle allocation

Legacy `evaluation_comparison managed` remains a scripted-index resolver. Add
the native command's `managed` action as a native-index resolver, then reuse the
same existing comparison reader/pins/independent native spoiler confirmation.
It returns unchanged reader wireV1 with actual report protocol3 metadata.
An execution token is not a read token; completion is not spoiler consent.
The ordinary OS picker remains independently capable of opening supported
historical reports under its existing read-only contract. Query2/raw actor
restrictions and inspection-lens separation remain unchanged.

Before production implementation, freeze independent packets covering:

- Valid mixed indexes: each lane's catalog filters the other, corrupt/unknown
  opposite entries fail closed, global run/client limits and cross-lane retry
  collisions remain enforced, old scripted bytes remain exact.
- Native deny/cancel, stale window/model Arc and malformed source/right-arm
  budget refuse before assets; no native-to-scripted substitution.
- Actual completed current native resume: zero reserve callback/assets/roles,
  same report and complete durable inventory; incomplete recovery labeled honestly.
- Fixed protocol-owner accepted and rejected handoff: exact witness/pair survives
  worker completion/retire, excludes competing work and cleans only on explicit
  matching retry. These are not installed-model generation tests.
- Lost acknowledgement/exact-client retry, closed/stale operation, known cleanup
  versus uncertain cleanup and no late private publication after retirement.
- Independent reader denial/held close, Player/Mira/Sable actual Query2 pages,
  early actor raw denial and read-lock Busy before any competing resume writes.

Actual installed-model service and native IPC/WebView/image-review cohorts,
runtime/device quality, full-comparison GUI native admission and final broad
regressions remain later explicit gates. No such results are supplied here.

## Verification allocation and limits

Independent service and command-parser packets must commit before production
edits. Existing actual protocol-worker/ModelManager test helpers may establish
real reservation, returned Arc, witness and parent cleanup behavior. Such payload
tests are not installed-model generation or proof that an injected outcome came
from the shared producer; retain that distinction explicitly. No arbitrary
test execution/provider injection may enter normal code.

Default tests require no model. Genuine completed-native fixture recovery needs
recorded source provenance and must be opted into explicitly if unavailable in
the default fixtures; fabricated scripted/native relabelling is prohibited.
Initial installed-model allocation, when Root records its actual launch, is at
most two new service invocations: one paired batch1 and one rollout batch1,
existing approved assets only, with the compiled CPU/context/token/repair/
invocation/deadline limits. Record actual outcomes/roles/loads; bounds are not
measurements. Any further allocation is recorded before its execution. No new
asset, download, device, JVM, release, settings or protected-resource action.

Run legacy scripted service/parser/controller compatibility, native ownership/
closed-schema checks, strict Rust/frontend checks, Android Rust host/graph and
normal build restoration as appropriate. Keep generated fixtures/errors local,
bounded and ignored. The later native frontend/action/IPC/render journey has its
own claim, frozen consumer interface and all-image inspection gate.
