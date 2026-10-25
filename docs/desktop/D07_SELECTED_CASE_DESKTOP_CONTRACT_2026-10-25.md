# Proposed selected-case desktop consumer — 2026-10-25

Refs #29 D07.06 and D04.02, partial. **The desktop consumer remains proposed.**
Only the frozen shared read-only allocation below is implemented; its
[qualification](D07_SELECTED_CASE_DESKTOP_READ_QUALIFICATION_2026-10-25.md)
owns executed checks and limits. The remaining consumer proposal is unimplemented.
Source inspected: `33c17d88857473b9e6c688c370d16caedb7f3713`.
This is the next consumer proposal after shared PR172 owner acceptance, not an
acceptance record for that PR, a native UI implementation, or a D07 exit gate.
The [native shared contract](D07_SELECTED_CASE_NATIVE_CONTRACT_2026-10-25.md)
continues to own execution, cleanup, timing, budgets and durable evidence.
Issue #29 owns current status. No model, application, build or test was run to
prepare this document; observations below are source inspection only.

## Existing authorities and concrete gaps

- `evaluation.rs` has one `Job`, cancellation slot, registered worker handle and
  registration gate for builtin, curated and comparison-read work. Reuse it.
  Do not introduce another evaluator, worker registry or model manager.
- `selected.rs` provides an opaque `PreparedSelectedPlan`, isolated destination,
  fresh whole-source preflight, durable per-arm Stores/checkpoints and read-only
  `inspect_selected`. The native driver owns both Ledgers through cleanup. Its
  `SelectedNativeFailure<R>` can retain the actual reservation and runtime.
- `evaluation/comparison.rs` retains a pinned `OpenedComparison` and private
  `ReaderGrant`; its capability currently does **not** retain the native picker
  origin. Its status is deliberately read-only with execution unavailable.
- `SelectedComparisonReportV1` is not a safe actor DTO: it includes full source
  Requests and row trace/capture information. Serde availability is not read
  permission. Existing comparison desktop evidence expects protocol2/run.json;
  a selected target is selected.json/report1 and cannot impersonate that format.
- The current curated worker drops its reservation and clears its job after a
  string result. That legacy path must not be copied for selected owned failure.

Normal ModelManager retirement **preserves** the evaluation ticket:
`models.rs::retire` changes cancellation/closing state but never clears
`inner.evaluation`; `finish_cleanup` also leaves it intact. Only the matching
`EvaluationReservation::drop` clears that ticket. Both `begin` and
`reserve_evaluation` reject a present ticket. `EvaluationManager::retire`
cancels/revokes presentation but does not release the ModelManager reservation.
There is no demonstrated ordinary-retirement ticket-loss defect here.

The existing deliberate stale-ticket fault exposes a separate prerequisite:
`retain_uncertain` returns the actual Arc on mismatch, but a stale R alone does
not block model admission if its ticket was already removed. The consumer must
not claim exclusion merely because a typed failure owns R. Before exposing that
fault path, freeze a narrow fail-closed fence in the **same** ModelManager which
survives rejected handoff, cannot overwrite a different owner, and is released
only by actual cleanup or exact-slot transfer. Root must choose its private
representation and tests. No second manager, quarantine list, caller-supplied
"cleanup succeeded" boolean, or new public authority is proposed.

## Closed command and capability proposal

Add a separate `evaluation_selected` Tauri command. Leave
`evaluation_comparison` and its `read_only:true/execution_available:false`
contract unchanged. Every action uses exact own-key checking, bounded strings,
existing lower-case UUID identities, JS-safe integers and closed enums. No
renderer path, asset name, executable, shell command, arbitrary JSON profile,
prompt, expected effect, policy replacement or source Request is accepted.

Proposed request bodies (names pending coordinator freeze):

| Action | Exact body | Meaning |
| --- | --- | --- |
| `catalog` | `{}` | Bounded native-owned selected-run metadata only. |
| `prepare` | `{clientId,readerClientId,runToken,binding,turnId,arm,lane}` | Explicit native confirmation, yield reader lock, fresh shared plan. |
| `start` | `{clientId,planToken}` | Consume that one prepared plan once. |
| `status` | `{clientId}` | Same-client lookup, including unknown start acknowledgement. |
| `cancel` | `{clientId,operationId}` | Cancel only that owned operation; no rollback promise. |
| `open` | `{clientId,runId}` | Native-owned target, independent private read consent; never executes. |
| `resume` | `{clientId,runToken,readerClientId,sourceToken,sourceBinding}` | New native execution confirmation and fresh source/target preflight. |
| `summary` | `{clientId,runToken,binding,observer}` | Rust-filtered last validated result. |
| `evidence` | `{clientId,runToken,binding,arm,request}` | Closed selected evidence request, with native lens authorization first. |
| `close` | `{clientId}` | Revoke presentation/unused plan; cancellation is cooperative. |
| `cleanup_status` / `retry_cleanup` | `{}` | Generic model exclusion/cleanup only, no old private result access. |

`lane` is exactly `scripted_baseline` or `approved_native`, mapped to the actual
shared enum; it is never inferred from an old report profile. A clicked source
arm identifies the original row; the shared selected workflow still compares
both fixed policies. `observer` never enters an execution Request.

Bind each in-memory capability to the actual WindowLease identity/epoch,
EvaluationManager and ModelManager identities, workspace root, selected source
binding and actual row. Require the existing native Story Lab grant for private
prepare/start/resume/open/read calls. Close and generic cleanup remain possible
after grant revocation, without granting access to private content. A window
session/scope/head change invalidates presentation ownership; it never mutates
the experiment's original scopes or the live gameplay session.

Use distinct private native `ExecutionGrant` and read grant types. A ReaderGrant
cannot be upgraded, a token cannot encode a path, and a renderer checkbox alone
cannot create either grant. `prepare`/`resume` invoke affirmative native
confirmation describing isolated experiment creation, selected source and lane.
Start requires the granted prepared token; do not auto-start after pick/open.
Reject canceled consent without invoking assets, model reservation or producer.

Keep at most four presentation clients and a fixed prepared/read TTL (proposed
300 seconds). TTL may revoke a plan or private view; it must never discard an
active worker, retained failure or uncertain model owner. Durable run identity
is separate from expiring in-memory tokens. A cold app must repick the original
source and obtain fresh consent for resume; persisted report data grants none.

## Source handoff and isolated destination

Retain the original native picker origin alongside the existing reader cap;
keep it private rather than adding a renderer path or public path getter.
Capture the bound source/row while the cap is valid, revoke that reader's usable
token and take its cap, then drop the source read lock **outside** metadata and
lease gates. Recheck current lease/context before any subsequent side effect.
Call actual shared `prepare_selected` on that native origin; never reconstruct
its canonical before Engines or request from UI metadata. The consumed run and
resume entries still perform their own full fresh source validation.
Another reader may still pin that source: return honest Busy rather than
forcibly closing foreign capabilities or bypassing the shared lock.

If consent needs a fresh descriptor from the opaque plan, a narrow native-only
metadata getter is a prerequisite for Root approval: source binding, source
kind, selection, per-arm original scope/head and semantic hash only. Do not
expose full Request or make cached reader metadata appear freshly validated.
Without that getter, label pending header metadata explicitly last validated.

Use a sibling `selected-evaluations` namespace derived from the existing
EvaluationManager root, like curated runs. Native creates an opaque GUID run
identity/envelope and computes its work path; the renderer supplies only runId.
Keep that envelope distinct from the shared destination, which must remain
absent until shared preflight permits creation. Do not place incompatible
selected metadata in the builtin `native.json` catalog namespace. Apply current
per-run/root caps and ordinary-directory/link/overlap guards to the new catalog;
never evict active or uncertain-owner work to satisfy a quota.

An isolated selected Store retains the real source Scope and canonical prefix.
It is not an imported live story, a new relabeled branch, or a gameplay resume.
Do not call Host.open/import or change active game selection after evaluation.
No copied source file, failed checkpoint or old report is repaired to run it.

## Worker, reservation and cleanup lifetime

Add one Selected JobKind and a typed payload in the existing evaluation job
lifetime. Use its existing single admission/registration handshake, cancellation
and join-outside-lock pattern. Do not register another worker before it is safe
to release the old one. Worker completion is not synonymous with child cleanup.

Implement `SelectedNativeReservation` directly for existing
`EvaluationReservation`. Its assets are the same approved ModelManager assets;
its handoff delegates the existing exact-owner `retain_uncertain`. Remove the
scoped unwired-method lint expectation when this real consumer is installed.
The shared native entry receives a single-use reservation callback. It controls
when that callback runs, after its model-free preflight; the desktop must not
reserve/load assets preemptively. Scripted uses `run_selected`, native uses
`run_native_selected`/`resume_native_selected`; no second LaneFactory or driver.

On success publish the actual final report after shared cleanup/settlement. On
failure preserve fixed code and `cleanup_uncertain`, then consume
`into_retained` only to retain the actual pair in the typed job payload. Do not
stringify/drop a retained pair, clear state.job unconditionally, or let
`drain`/window destruction discard it. Successful handoff leaves the same model
slot responsible for cleanup; rejected handoff uses the prerequisite fence
above while the typed job still owns the pair. Generic cleanup retry must run
actual direct cleanup and exact identity checks, not inference or a re-run.

Retirement synchronously cancels/revokes access and returns promptly. Blocking
joins/direct cleanup occur outside registration, state and window metadata
locks, following existing close-worker ordering. A late worker can settle its
owned experiment but cannot publish into a replacement lease/context, clear a
new job, revoke a new Host supplier or release another model ticket. No automatic
inference retry follows cancellation, unknown acknowledgement or Cleanup.

## Status, private evidence and frontend behavior

Use a small checked status envelope with version/kind, client/operation/run
identities, phase, running, lane, original selected source metadata, last known
binding, fixed error and cleanup state. Separate `plan_token`/`run_token` from
the durable runId. Phase is closed: preparing, prepared, running, cancelling,
cleanup_required, completed, paused, failed or closed. `completed` means attempts
finished, not successful outcomes or human quality. Keep completed result
metadata distinct from an actual pending operation. Cleanup/unknown remain
visible even after private presentation is revoked.

There is no current shared progress callback except reservation. Show generic
running/indeterminate state and cancellation request honestly; do not invent
hash/load stages, percentages, per-arm live progress or measured token counts.
A target `run.lock` held by execution does not make partial `inspect_selected`
available. Pending headers come from native-bound metadata; final summaries
come from actual inspection after cleanup and lock release. Do not scrape
partially written files to fabricate progress.

Add a dedicated Rust selected summary/evidence adapter before JSON exposure.
Never return `serde_json::to_value(SelectedComparisonReportV1)` to an actor lens.
Actor summary is bounded metadata/outcome status plus actual observer-filtered
Query2 pages from the selected Store and inspected edge. No source fullRequests,
trace, capture, raw prompt/output, author data or diagnostic prose is included.
Omit private empty units before search/count/paging. Lens selection never changes
the experiment generation actor (the player), knowledge or permissions.

Raw receipt/capture/output and spoiler summary need a separate native private
read grant and an explicit omniscient/spoiler request. Reject actor raw requests
before token/source probes. Preserve missing versus corrupt distinctions and
actual original_scope/event provenance. Reuse common selected validation and
Store/Query2; never counterfeit protocol2 run.json or feed a selected report to
the old reader decoder. Until this additive shared evidence seam exists, label
selected detail links unavailable rather than rebuilding canonical views in TS.

New strict model/controller/panel files should reuse `checkedPageV2` and closed
scalar/own-key/total-byte checks. Keep the existing reader unchanged. There is
no native experiment-player ID in the current public reader DTO: do not infer
Character-own-player message eligibility from a live game, query ID or literal
`player`; offer the Player lens separately and keep the closed fallback.
Local actor changes immediately clear full summary/raw evidence. Inspection-lens changes clear/filter private pending reads under their own
epoch, but never cancel, rekey or alter generation. Execution identity keeps the
original player Request/profile. Explicit cancel or defined source/window-lease
retirement cancels only the captured original operation. Install
epochs before notifications and recheck after every synchronous listener and
await before dispatch, publication or cleanup affecting a current capability.
Lost acknowledgement preserves the same client/operation for explicit status;
never auto-rekey/start again. Cancellation cannot erase a proven real commit.

## Proposed allocations and frozen gates before exposure

Root must freeze exact signatures, wire caps and ownership transfer before
implementation. Candidate paths: native `evaluation.rs`, new
`evaluation/selected.rs`/`selected_commands.rs`, narrow `models.rs` adapter/fence,
command registration/permissions; new selected model/controller/panel/checker;
narrow comparison native-origin transfer and shared selected read-only adapter.
No Store/schema/Core/compiler/Play/corpus/budget change is requested. Shared
metadata/evidence additions require their own explicit coordinator allocation.

Freeze tests before production in these families:

1. Actual shared preflight refuses corrupt unselected source, aliased target,
   insufficient other-arm capacity and incompatible history before callback or
   target creation. Exact completed recovery invokes zero factory/reservation.
2. Native authority: foreign window/manager/token, expired plan, reader-only
   grant, canceled second consent, stale source and duplicate start/lost ack.
   Actual worker registration is single; readonly historical open never runs.
3. Ownership: normal retire preserves R exclusion; accepted and rejected same
   owner handoff; cleanup fault/retry; stale ticket/close cannot release or
   revoke replacement. Retained pair survives worker end, drain and window close.
4. Privacy: actual selected player/NPC Query2, scoped inherited events, guard
   missing capture; actor raw denied before source lookup; no fullRequests or
   raw report hidden in actor summary; lenses leave canonical knowledge equal.
5. Actual controller listener reentrancy, held replies after context/lens change,
   same-client recovery, cancel versus real committed result and cleanup status.
   Headless/mocked checks are labeled accordingly, not native execution.
6. Fixed development-only native fixture commands through the same controller
   and IPC, not arbitrary paths/callbacks/server. Hidden unfocused WebView
   snapshots separate experiment scope/head/lens from liveGameplayContext and
   real pending/receipt/error. Bound semantic capture metadata rather than
   embedding a full report/file inventory in CapturePreview. Inspect wide/narrow
   images, retained errors and normal-build hook exclusion. Use owned synthetic
   source/output roots; original source inventories remain byte-identical.

Approved-native asset execution is a separate explicit opt-in after source
freeze and model-free gates. Record actual setup/ledgers/receipts, unknown role
reservations, restart and cleanup separately from synthetic fixtures; no score,
human quality acceptance, Android parity or selected WebView evidence follows
from this proposal. Root chooses the smallest allocation and runs qualification.


## Frozen first allocation: selected read-only capability

Root claim6401286275, accepted base PR172 merge
`5f1a49f1e18c954f2fc6b85ed875736dd4c414ea`. The remainder above stays proposed.
The additive shared `selected::desktop_read` interface uses a separate name to
avoid shadowing the existing full-comparison `desktop_api` source capability:

```rust
pub struct OpenedSelected; // opaque retained selected lock/pins; never JSON
pub fn open_read_only(dir: &Path) -> Result<OpenedSelected>;
pub fn summary(run: &OpenedSelected, native_inspection_granted: bool) -> Result<Value>;
pub fn evidence(run: &OpenedSelected, expected_binding: &str, arm: Arm,
    request: EvidenceRequest, native_inspection_granted: bool) -> Result<Value>;
```

`Arm` and `EvidenceRequest` are the existing full-comparison enums. The caller
owns the native inspection grant; none of these APIs grants execution. Summary
keys are exactly version1, kind selected_read, opaque snapshot binding, selection
(turn/clicked_arm/index), lane, arms (arm/scope/before_head/nullable after_head/
available), read_only true, execution_available false. This metadata has no full
Request, source binding, profile, diagnostic prose, outcome, capture or metrics.
Private contents are obtainable only through the checked evidence request.

Every permitted read freshly validates the entire selected destination and
compares the retained snapshot, including both checkpoints, report, manifest
and exact bounded ledger/setup file seals. Aggregate charges alone cannot seal
offsetting settlement changes. Refuse drift rather than mix an old summary with
new evidence. This is stricter than the existing full-comparison selective-read
contract; that contract remains unchanged. Raw actor denial precedes binding and
filesystem probes. Query evidence uses the same actual Store edges and Core
Query2 as the existing reader; raw receipt/capture/outputs use its common checked
renderer. No serialization of the whole selected report is returned.

A missing checkpoint remains `checkpoint_unavailable`, including a genuine
committed Store with lost workflow evidence. Do not recover/write a checkpoint
or infer its after-head. Validate the requested observer on the actual before
Engine when present; an absent database has no actor-context authority and
returns missing without inventing a seed Engine. Corrupt retained evidence is
an error, not missing. No source, model assets, runtime, native app or execution
is needed to inspect supported historical evidence, including feature-off native
records. Initial implementation and frozen tests remain unverified until the
separate qualification record reports their actual terminal checks.
