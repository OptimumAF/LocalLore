# Full comparison desktop adapter: frozen scripted slice

Supporting D07.06/.02/.04, following accepted PR209. This is an interface and
acceptance specification, not execution evidence. Rust owns implementation and
integration. No new engine, canonical Store, memory policy or inference provider.

## Scope and authority

The adapter calls accepted `comparison::prepare_reference/open_reference` and
`literal_v3::run_comparison/inspect_comparison` with fixed `ScriptedBaseline`.
Protocol3 Literal/Relevant descriptors, scenarios, validation, receipts, resources,
source matching and checkpoints come from those shared APIs. Paired runs create
one native-owned scripted reference and retain it unchanged on resume. Rollout
runs use no reference. A chunk is1..4 new scenes; completed resume does no work.
The shared native producer is already implemented, but ordinary desktop native
execution is unavailable in this first slice. It must not silently use scripted
inference. Status/open/lookup/repeated start do not resume inference.

One existing EvaluationManager parent Job/registration/cancellation/worker owns
the operation. New `JobKind::ComparisonRun` has no model owner in this scripted
slice. Native-owned bounded index metadata identifies durable runs and client
requests; actual shared files remain the result authority. No renderer path,
provider, canonical state, policy, model path, consent or cleanup proof is accepted.

## Closed command transport

Command `evaluation_comparison_run`, args `{action,query}`. Exact keys only;
UUIDs are lowercase36-character UUIDs, operations positive safe JS integers.
All actions except cleanup close require the actual Host Story Lab permission
and current native WindowLease. Native code captures both; JSON cannot grant them.

| Action | Exact query keys |
|---|---|
| `catalog` |none (`{}`)|
| `start` |`clientId`, `comparisonKind` (`paired` or `rollout`), `batch` (integer1..4)|
| `lookup` |`clientId`|
| `open` |`runId`|
| `status` |`runToken`|
| `resume` |`runToken`, `batch`|
| `cancel` |`runToken`, `operationId`|
| `close` |`runToken`|

Catalog exact envelope: `{version:1,kind:"comparison_run_catalog",protocol_version:3,
input_lane:"scripted_baseline",runs:[RunMetadata],max_new_scenes:4}`.
RunMetadata exact keys: `run_id`, `client_id`, `comparison_kind`, `initial_batch`,
`created_ms` (safe nonnegative integer), `protocol_version:3`,
`input_lane:"scripted_baseline"`. Catalog lists metadata, not verified report facts.

Status exact envelope: `version:1`, `kind:"comparison_run"`, `protocol_version:3`,
`input_lane:"scripted_baseline"`, `client_id`, `run_id`, `run_token`,
`operation_id` (positive safe integer or null), `comparison_kind`, `batch`,
`phase`, `running`, `error` (closed code or null), `completed_scenes` (0..4),
`completed`, `report_ready`, `source_matches` (boolean or null).
Phases: `retained`, `starting`, `running`, `opening`, `stopping_at_boundary`,
`paused`, `completed`, `failed`, `closed`.
Operation remains the last admitted operation after completion; `running` is
authoritative. A report is ready only after actual shared inspection/publication.
Cold lookup can return retained metadata with unknown source/no verified report.
Same client/same original kind+batch returns the same run; conflicting input is
rejected. Tokens are in-memory capabilities tied to the actual window epoch.

Closed errors: `Forbidden`, `Closed`, `InvalidEvaluationInput`,
`UnknownEvaluationRun`, `StaleEvaluationOperation`, `EvaluationBusy`,
`EvaluationBudget`, `EvaluationRunLimit`, `EvaluationTokenLimit`,
`EvaluationSourceMismatch`, `EvaluationIntegrity`, `EvaluationNotReady`,
`UnsafeEvaluationPath`, `EvaluationIo`, `EvaluationInternal`, `Cancelled`,
`PickerUnavailable`, `NativeUnavailable`. Frontend decoder failure is
`ComparisonRunWire`; unknown transport acknowledgement remains uncertain and
retains its client/token for explicit lookup/status/close, without automatic retry.

## Inspection remains independent

Existing `evaluation_comparison` gains closed action `managed`, exact query
`{clientId,runId}`. It resolves only a validated native-owned full-comparison run
and obtains independent fixed native spoiler-read confirmation before calling
the existing reader. It returns the unchanged comparison-reader status/source/
summary/evidence wire types. Generated run completion is not a read grant.
`ComparisonReaderController.pick(runId?)` uses `managed` only for an explicit
provided UUID; no argument preserves the existing OS picker. Existing reader
close/recover, source transfer, observer Query2 and raw restrictions remain.

## Native API frozen for independent oracles

`FullComparisonStart {client_id:String,kind:comparison::ComparisonKind,
max_new_scenes:usize}`. Methods on EvaluationManager:
`full_comparison_catalog/lookup/open/status/cancel/close`, each starts with
`(&WindowLease,epoch:u64,granted:bool,...)`; remaining arguments respectively
none, `client:&str`, `run_id:&str`, `token:&str`,
`token:&str,operation:u64`, `token:&str`.
`full_comparison_start(self:&Arc<Self>,lease:&Arc<WindowLease>,epoch,granted,input)`
and `full_comparison_resume(self:&Arc<Self>,lease:&Arc<WindowLease>,epoch,granted,
token:&str,max_new_scenes:usize)` return the status JSON.
Root owns registrations; independent source tests freeze before implementation.
Native-owned root helper `full_comparison_root()` resolves
`self.root.with_file_name("comparison-evaluations")`; each UUID leaf has closed
`desktop.json` wrapper metadata, shared comparison output in `work/`, and a
paired-only `reference-source/`. Tests may inspect only their synthetic root.

## Acceptance boundaries

Actual service tests use shared generated histories, not handwritten reports.
Cover paired1→resume3, rollout4, exact-client idempotency/conflicts, completed
resume byte equality, native index/source/reference rejection before writes,
pending/cancel/retire/late completion, one global worker and safe cold reopen.
Frontend mock/controller/SSR evidence is separate from actual native IPC and
WebView captures. The app-owned harness uses synthetic fixtures, fixed native
consent/picker faults and bounded logs; all produced images require inspection.
Native-model UI, human quality, whole-app measurements and phone parity remain
separate gates. No milestone acceptance is awarded by this contract.
