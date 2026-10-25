# Selected-case native extension contract — 2026-10-25

Refs #29 D07.06, partial. **PROPOSED / UNIMPLEMENTED / UNRUN until Root freezes.**
Accepted base: `008c54182a5d7d51574d3f059bf7210085721df4` (PR166).
This revision supersedes the assets-only reservation proposal at `7fba1fdd`;
that proposal remains in Git history. Root claim6397635480 owns reconciliation.
No native selected driver, GUI, model quality or whole-D07 acceptance follows
from this document. All interfaces below are proposals, not existing API claims.

## Scope and accepted prerequisites

Extend the [scripted selected driver](D07_SELECTED_CASE_SCRIPTED_CONTRACT_2026-10-25.md),
using its actual per-arm Core histories, full Requests, source locks/pins,
`execute_turn`, `load_turn`, `recover_committed_turn`, both existing Ledgers and
common outcome handling. One existing packaged LocalRuntime serves both arms
sequentially through `LaneFactory::Native`; no alternate backend/manager/Store,
schema, corpus, policy, replay validator or public Core/Host guard API.

PR166's [owned cleanup contract](D07_OWNED_RUNTIME_CLEANUP_CONTRACT_2026-10-25.md)
and [qualification](D07_OWNED_RUNTIME_CLEANUP_QUALIFICATION_2026-10-25.md) establish
the prerequisite: boxed post-spawn owner, Failed-safe direct cleanup and the
same ModelManager runtime slot. Legacy full native comparison still uses its
legacy constructor; this selected extension must not imply that caller changed.
Its actual failure/ownership behavior needs a separate allocation if upgraded.

## Proposed exact native surface and owned failure

```rust
pub enum SelectedLane { ScriptedBaseline, ApprovedNative }
#[cfg(feature = "local-model")]
pub trait SelectedNativeReservation {
    fn assets(&self) -> NativeAssets<'_>;
    fn retain_uncertain(&mut self, owner: Arc<Mutex<LocalRuntime>>)
        -> std::result::Result<(), Arc<Mutex<LocalRuntime>>>;
}
#[cfg(feature = "local-model")]
pub fn run_native_selected<R: SelectedNativeReservation>(
    plan: PreparedSelectedPlan, new_dir: &Path, cancel: &Cancellation,
    reserve: impl FnOnce() -> Result<R>,
) -> std::result::Result<SelectedComparisonReportV1, SelectedNativeFailure<R>>;
#[cfg(feature = "local-model")]
pub fn resume_native_selected<R: SelectedNativeReservation>(
    dir: &Path, source_dir: &Path, expected_binding: &str,
    cancel: &Cancellation, reserve: impl FnOnce() -> Result<R>,
) -> std::result::Result<SelectedComparisonReportV1, SelectedNativeFailure<R>>;
```

`Result<R>` above is the existing fixed-code evaluator result used by the
reservation callback. Callback errors must be mapped to closed codes, not paths
or arbitrary caller text. The native failure is opaque, non-Clone, non-Serde,
with redacted Debug; it is not a JSON authority or a String carrying ownership.
Proposed accessors are `code(&self)->&str`, `cause(&self)->Option<&str>`, and
`cleanup_uncertain(&self)->bool`. Codes are allowlisted existing driver/runtime
categories plus Cleanup; no raw output, filesystem path or Debug dump is exposed.
`into_retained(self) -> Result<(R, Arc<Mutex<LocalRuntime>>), Self>` uses the
standard Result type and returns the actual reservation and owner only when
uncertain handoff failed. Otherwise it returns the unchanged failure.

Thus a rejecting handoff cannot stringify/drop the child or reservation while
claiming completion. The consumer must keep the owned failure in its existing
EvaluationManager job lifetime until cleanup is confirmed or transfer succeeds;
it cannot publish owner-free completion or admit replacement first. This needs
a typed payload in that existing job, not another manager/quarantine list.
No read-token promotion, native grant, path or callback is deserialized.

Keep ApprovedNative recognizable without local-model so inspection can decode
its retained evidence. Preparing/executing it feature-off refuses fixed
NativeFeatureUnavailable. Scripted entrypoints reject native plans and vice
versa; neither silently changes lane or profile. PreparedSelectedPlan stays
opaque/non-Clone and retains the actual source capability.

## Ordered preflight, callback and model-free paths

1. Capture `entry_started` at consuming run/resume entry before whole-source
   revalidation. Recheck current source fingerprint, suite/reference and actual
   both-arm prefix/full Request/semantic bindings, preserving rollout divergence.
   Cached summary is insufficient. Retain cooperative source lock/pins; the
   native caller separately yields its reader and obtains execution consent.
2. Before any new destination, callback, invocation or assets, read-only validate
   both existing destination arms, checkpoints/phases/full inputs, aliases,
   ordinary single-link/reparse constraints, disjoint pinned canonical parent
   and both ledger capacities. Refuse missing terminal noncommitted checkpoints;
   never clear their keys. Known terminal checkpoints remain finished.
3. Classify completed, actual committed-recoverable, dependency-only and missing
   provider-eligible work. Completed resume returns unchanged inventory.
   Committed recovery uses the profile-only helper before any runtime factory.
   Dependency-only work uses the separately frozen private DependencyJob seam:
   the SAME existing actual-prefix/reference-proposal dependency branch, not an
   Expected-only guard interpreter or fabricated row. Persist neither half until
   full both-arm preflight has succeeded. These three paths call reserve/assets
   zero times and do not spawn/load; unknown historical charges remain unknown.
4. Call reserve exactly once iff unfinished, nonrecovered, nondependency work
   exists. This includes finite Core guards: the normal Host/Core path can
   reject before inference, but measured startup is allowed after consent.
   The callback only reserves existing owner exclusion; no probing/hash/load/
   spawn. Callback refusal leaves a new destination absent and ledgers unchanged.
5. Recheck cancellation, absolute deadline and both capacities after callback.
   Only then create a new destination and durably begin BOTH existing ledger
   invocations before assets/hash/spawn/load. Source files are never repaired.
   Host/Store guard phases, trace/profile and recorded/error/cancel precedence
   continue through actual `execute_turn -> Host -> Play -> finish_work`.
   No dummy/ProfileOnly provider, supplierless Host or new guard implementation.

Count callback, actual load/setup, provider factories and inference polls
separately: guard rejection with zero polls does not imply zero native startup.
Existing completed-half validation and same-step lost-ACK recovery remain exact;
a changed Request or extra suffix refuses before either arm mutates.

## One actual owner through startup, cleanup and handoff

Use `spawn_packaged_owned_expected_cancelled` with existing approved resource/
model/worker/profile identities. BeforeChild means no runtime owner exists.
AfterChild supplies the original cause and Box<LocalRuntime>; retain that same
object, pipes/joins/pins, and move it into one Arc<Mutex<LocalRuntime>> shared by
the native factory/Host. Do not clone a runtime or fall back to legacy startup.

Hold R throughout actual worker/Host/provider lifetime. On startup, load, profile,
execution, cancellation, deadline or publication error, first stop/drain the
actual Host/provider references, then call terminate_and_reap on the same owner.
It works in Failed; poisoned locking permits cleanup only, never inference.
Confirmed cleanup permits dropping R. Drop/shutdown/error/timeout alone is not
confirmation. Already committed rows remain real even if later cleanup fails.

If cleanup is uncertain, call R.retain_uncertain with that same Arc BEFORE
dropping R. The desktop adapter delegates directly to existing private
`EvaluationReservation::retain_uncertain(&mut self, SharedRuntime)
-> Result<(), SharedRuntime>`: same ticket,
same Arc idempotence, no newer-owner overwrite. Success installs quarantine in
the SAME ModelManager slot before ticket Drop; it stays resident/loaded=false/
Cleanup and blocks load/reserve until explicit existing unload cleanup succeeds.
Remove the production handoff's expect(dead_code) when this consumer is wired;
do not add a replacement lint suppression.

If handoff returns Err(owner), return SelectedNativeFailure retaining BOTH
owner and R; no owner loss, second list or unconditional guard drop. Native job
status reports cleanup uncertainty and keeps admission excluded while it holds
that payload. A matching reservation normally transfers deterministically;
private stale/fault tests must prove the rejection path still owns both values.
Keep initial fixed cause separately from the visible Cleanup category. After
confirmed cleanup, ordinary fixed driver failure need not retain R or an owner.

## Absolute clocks and terminal setup cost

Retain existing 32 invocation/admission, 96 role, 30-minute active, 120-second
preparation, 60-second absolute turn and 3-second cleanup-reserve constraints.
Pass one cooperative preparation deadline through preflight/callback/assets/
hash/spawn/load: `min(entry_started + PREPARATION_MS,
now + min_current_remaining.saturating_sub(CLEANUP_RESERVE_MS))`.
Remaining includes original-entry elapsed time; subsequent checks may shorten,
never restart/extend this deadline. Turn timing still begins before Host prelude.
Only actual measured other-arm/setup shares are excluded, never nominal refunds.

File reads, process creation and kill/wait/join have no universal OS bound.
Recheck after load: a late load must be cleaned up and failed before any turn.
Measure actual physical startup through terminal failure cleanup, even above
120000ms. Do not clamp it, raise budgets or pretend expiry proves child exit.

Current Ledger::record_shared_setup rejects physical>PREPARATION_MS, while
Ledger::load already accepts settlement.ms above its reservation. Propose one
private selected-only known-terminal setup/accounting seam that reuses existing
validation/splitting but permits the true overrun AFTER confirmed cleanup (or
BeforeChild). Its terminal proof stays private; no caller JSON/bool grants it.
Write failed SetupRecord and actual ceil/floor split once, then settle real
overhead using existing finish. Exhausted remaining budget blocks later work.
Full-run record_shared_setup behavior stays unchanged unless separately frozen.
Unconfirmed cleanup/interruption leaves both full reservations outstanding,
with unknown timing/roles and a fixed visible failure. Do not settle/refund it
as known terminal or count it as an on-time loaded setup.
Preserve any already proven admission settlements and committed rows; uncertainty
does not delete them. A later cleanup failure also does not rewrite a previously
measured loaded setup into a fabricated failed startup.

## Closed reports, profiles and read-only history

Keep the exact selected version1 manifest/report keys, digest omitting only its
own binding, 128KiB manifest and existing 2MiB report/inert-HTML caps. Rows remain
0..2 actual TurnReportV2 with original index, per-arm scope/head/full input.
Target lane native_selected_case and target current native_profile differ from
the actual source profile/lane; no reference normalization of divergent rollout.
Old scripted manifest/report bytes and null native measurements stay unchanged.

Execution requires current source/approved target profile and actual identities.
Read-only inspection instead validates structurally supported retained native
profile/history, including feature-off builds, without assets or native approval.
Derive internal load_turn native mode from stored lane; do not substitute
ScriptedBaseline or require a runtime factory merely to read. Unknown versions/
lanes refuse. Preserve old Play2.1–2.5 replay validators and exact retry bytes.

Reuse SetupRecord version2 keys exactly, actual selected binding and both ledger
invocation IDs, status loaded/failed and nullable measured load metrics.
Expand pin_selected only for ordinary single-link setup-00.json..setup-31.json;
reject other names. Validate setup, ledgers/settlements, row capture/recording/
raw bytes/profile through existing paths. Missing records remain unknown.
physical_setups counts validated measured attempts, including failed startup,
not successful model loads. Null is not zero. Late cleanup failure cannot erase
real saved outcomes or invent measured timing/role success.

## First frozen tests and separate later gates

Freeze tests before production: full source/both-arm path/budget/phase refusal,
complete/committed/dependency-only zero callbacks/assets; eligible Core guards
exactly one callback, actual Host rejection trace/Store phase and zero polls.
Assert callback after both preflights and before assets/reservations; callback
refusal/cancel/expiry preserves source and refused destination inventories.
Use actual Requests/Store histories, not only reported role counts.

Freeze original-entry clock/preflight delay, callback delay, late load and
confirmed terminal >120s accounting; unknown cleanup keeps full reserves;
asymmetric budgets and half-resume preserve completed evidence without calls.
Fixed worker tests cover boxed partial startup, profile/load error, retained
joins/pins, poison, actual cleanup retry, same-Arc successful handoff and rejected
handoff returning R+owner. Verify no replacement reservation while uncertain,
and removal of the unwired expectation only when the adapter genuinely exists.

Installed approved-asset opt-ins later verify exact worker/model hashes, one
runtime/two policies, actual load/generation/repair/cancel/cleanup timings and
guard startup-versus-polls. Scripted/protocol fixtures cannot qualify weights,
prose quality, native IPC/WebView/GUI, offline/hardware or device behavior.
Root assigns shared driver/helper/native job/UI paths separately after freeze.
This sole-doc revision performed source/Git inspection only; no test/build/
formatter/compiler/worker/model/app/device/SDK/desktop/protected execution.
