# Isolated selected-case scripted producer contract

Refs #29 D07.06, partial. Root freezes this first producer gate in
[#29 comment6394962471](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6394962471).
This document defines intended behavior before implementation and tests. It is
not verification evidence. Native selected execution, GUI consent/job ownership,
real models, human quality and the whole D07 gate remain separate work.

The reviewed design proposal is commit
`f61444dda93e4bcc2d4f75eef2a174765625ce32`. This narrower gate implements only
its scripted shared API. It does not introduce a second provider, ledger, Store,
canonical database format, context compiler or validator.

## Implementation status, pending qualification

At source `2838cef87b4bfb6d916f76461caba79df8536ebc`, the shared scripted Rust API
below is implemented; final qualification/owner acceptance are pending in the
[separate incoming evidence record](D07_SELECTED_CASE_SCRIPTED_QUALIFICATION_2026-10-25.md),
not yet an accepted `main` result. This status note is not measured verification.
Both arms' admission capacity and preparation budgets are checked before reservation;
common `load_turn` validates actual Store phase/full request/receipt against checkpoints.
Existing destination files with hardlink aliases refuse before writable Store access;
neither source nor contradictory evidence is silently repaired. Frozen keys/caps stay unchanged.
Native/GUI selected start/resume remain unavailable: later integration needs a new
native affirmation and shared model owner; a read-only token is never upgraded.

## Shared API and authority

Module `local_lane::comparison::selected` exposes:

```rust
pub enum SelectedLane { ScriptedBaseline }
pub struct SelectedIntent { pub client_id: String, pub lane: SelectedLane }
pub struct PreparedSelectedPlan { /* private, nonserializable, not Clone/Debug */ }
pub struct SelectedComparisonReportV1 { /* Serialize-only, data-only */ }

pub fn prepare_selected(source_dir: &Path, expected_source_binding: &str,
    row: &desktop_api::RowId, intent: SelectedIntent,
    cancel: &Cancellation) -> Result<PreparedSelectedPlan>;
pub fn run_selected(plan: PreparedSelectedPlan, new_dir: &Path,
    cancel: &Cancellation) -> Result<SelectedComparisonReportV1>;
pub fn inspect_selected(dir: &Path) -> Result<SelectedComparisonReportV1>;
pub fn resume_selected(dir: &Path, source_dir: &Path, expected_binding: &str,
    cancel: &Cancellation) -> Result<SelectedComparisonReportV1>;
```

Use the existing fixed-error evaluator `Result`. Client IDs are 1–128 ASCII
alphanumeric/hyphen bytes. Bindings are exact lowercase SHA256 strings.
`expected_binding` on resume names the selected destination identity; the
manifest names the original source identity separately.

Preparation takes the existing source `run.lock` without creating it, retains
ordinary-directory pins, and fully validates the original producer, both arms,
all required evidence and reference. A live read capability holding that lock
refuses preparation. It must first be explicitly dropped; an inspection token
never becomes an execution grant. Minimal typed snapshot access is private to
the comparison modules (`pub(super)`), with no new renderer paths or grants.

Resolve the original corpus index in both actual arms. Derive each pre-turn
engine, full Core Request, seed and accepted prefix from the actual Store.
Paired inputs must equal their validated reference prefix. Rollout inputs keep
each arm's actual divergence. Preserve original index, turn ID, text, scope,
head, Intent, policy and current Play2.5/compiler2/forwarded-budget1 behavior.
Generate no preceding turns. A selected plan owns actual typed inputs and the
source lock; diagnostic JSON is not execution authority.

Consuming run entry starts the existing preparation clock and freshly repeats
full source validation and both input checks. Historical/source mismatch,
stale binding, missing other arm, cancellation or required evidence corruption
refuses before destination/ledger/provider changes. A destination must be new,
ordinary, pinned through its parent and disjoint from source (no same path,
ancestor, descendant or reparse alias). Source is never repaired or written.

## Destination and report

Use a separate closed `selected.json`, never counterfeit `run.json` or a full
comparison report. Manifest keys are exactly:

```text
version, run_type, client_id, binding, source_binding, source_kind,
source_profile, selection, lane, profile, suite_sha256, source_sha256,
source_reference_sha256, source_inputs
```

Constants: version1, run_type `selected_case`, lane `scripted_selected_case`.
`selection` is exactly `{turn, clicked_arm, index}`; clicking either arm chooses
the same original index and executes both actual policy arms. `source_inputs`
is exactly two entries in left/right order with keys
`{arm, scope, before_head, request, prefix_sha256, input_semantic_sha256}`.
The prefix digest uses existing `digest(encode(actual_before.receipts()))`.
The selected binding hashes the complete manifest excluding its own binding
key. All on-disk metadata is bounded, ordinary-file and deny-unknown-fields;
duplicate fields fail decoding. Neither hash nor manifest authenticates
adversarially rewritten evaluation evidence.

Report keys are exactly:

```text
version, run_type, source_protocol_version, binding, source_binding,
source_kind, source_profile, selection, lane, profile, suite_sha256,
source_sha256, source_reference_sha256, source_inputs, rows, completed,
per_arm_progress, physical_setups, physical_setup_ms, native_load,
left_charged_ms, right_charged_ms, left_reserved_roles, right_reserved_roles,
human_reviewed, human_rubric, quality_accepted, unavailable, limitations
```

Source protocol is2; human_reviewed0, human_rubric `not_reviewed`,
quality_accepted false. Rows are zero to two actual unchanged TurnReportV2s in
left/right order. No full-scene count. Progress is exactly two `{arm,state}`
entries with `not_started`, `interrupted` or `finished`; finished requires a
validated terminal checkpoint. Completed means both attempts finished, even if
failed or cancelled. Native setup/load metrics are unavailable for scripted
work, not fabricated measurements. Bounded JSON and inert escaped HTML reports
are local private diagnostics; maximum encoded report2 MiB, checkpoint256 KiB.

Inspect regenerates rows from actual Store/ledger/checkpoints, never trusts a
cached report. An incomplete canonical bootstrap that cannot yet prove its
full prefix may refuse inspection; resume must validate it against the freshly
opened source and complete it through existing Store APIs.

## Resume, cancellation and resource accounting

Before either arm reserves work, validate both destinations as an exact partial
bootstrap, complete selected prefix or that prefix plus the same full selected
Request. Extra accepted suffix, changed same-key text/Intent/seed/scope/head or
mismatched checkpoint refuses without either ledger changing. Preserve current
admission/role/invocation/active-time limits and entry-origin preparation and
absolute-turn clocks. Do not clear terminal keys, refund unknown crash work,
renumber the turn or multiply budgets by prefix length.

Reuse `ensure_database`, `validate_pair_source`, actual Store begin/commit,
`execute_turn`, `load_turn`, `recover_committed_turn` and both existing ledgers.
Both invocation reservations precede new provider work. Exclude only measured
other-arm work. Cancellation before admission executes no provider; cancellation
between arms preserves a completed half for resume. An actual committed receipt
wins over a late cancel. Failed/cancelled/guarded/dependency-blocked checkpoints
are finished attempts; explicit new destination/client is needed to try again.

Committed-without-checkpoint recovery uses actual Store lookup and the extracted
profile-only helper before any factory or native reservation. Keep roles,
capture and timing evidence unknown when absent. Recovering a workflow file
does not commit again; prior unknown reservations remain charged. Fully
checkpointed completed resume is read-only with byte-identical inventory and
no invocation, provider, assets or ledger mutation.

## Verification boundary

Freeze actual-producer tests before implementing the module. Initial public
oracles cover noninitial paired/rollout inputs, source locks and immutability,
early binding/client/cancel/corruption refusals, exact destination requests and
prefixes, completed read-only resume, lost checkpoint recovery and off-reference
resume refusal. Actual private divergent/failure/half-resume/budget/deadline
oracles and existing full-run regressions remain necessary before accepting
the entire selected producer gate. Synthetic tests never qualify native model
execution, GUI IPC/rendering, Android/device parity or narrative quality.
