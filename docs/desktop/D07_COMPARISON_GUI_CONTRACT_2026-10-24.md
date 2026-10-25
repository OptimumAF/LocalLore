# Proposed comparison GUI and shared facade contract — 2026-10-24

Refs #29 D07.01/.02/.05/.06, partial. **UNIMPLEMENTED.** The coordinator's
Gate1 reader contract at the end is now frozen for tests; other interfaces
in this original proposal remain proposed.
This document requests coordinator review; it is not implementation approval,
an executed comparison, a frozen test implementation, or milestone acceptance.
Root owns decisions, source allocation, integration and all actual execution.

The documentation author owns only this new file on
`docs/d07-comparison-gui-contract` / `source-d07-comparison-gui-contract`,
from exact Root `65b1ee4d5ca25cf596016d03fed0f797d2fd89e6`.
Claim: [#29 comment 6392782376](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6392782376).
No production, tests, fixtures, dependencies, reports or previous worktrees
are changed. All commands below are prospective and **UNRUN** by this author.

## Observed source boundary

The accepted [PR154 qualification](D07_CURRENT_COMPARISON_QUALIFICATION_2026-10-23.md)
records actual producer/Core/Store/model and compatibility evidence at its
named sources. It explicitly leaves current-comparison GUI/source navigation
and isolated selected-case reruns open. Do not relabel its CLI/model results
as new app execution or new-source measurements.

At this document's base:

| Existing source | Actual capability / missing seam |
| --- | --- |
| [comparison.rs](../../crates/locallore-eval/src/local_lane/comparison.rs), `prepare_reference`, `open_reference`, `inspect_comparison`, `run_comparison`, `run_native_comparison` | Validated reference, readonly report reconstruction and whole/scene-batch runs exist. `max_new_scenes=1..4` is not an isolated selected-turn rerun. No comparison desktop evidence facade or selected-rerun API exists. |
| [memory_comparison_v2.rs](../../crates/locallore-eval/src/memory_comparison_v2.rs), `TurnReportV2` / `ComparisonReportV2` | Protocol2 reports actual policy/roles/capture/latency/provenance and missing values. A row has no scope or before/after heads. Those must be obtained from validated `StoredTurn` and actual Store history. |
| [local_lane/desktop_api.rs](../../crates/locallore-eval/src/local_lane/desktop_api.rs) | Existing curated reader shares its runner's validation and locks. Its evidence is Query1 and explicitly lacks historical context/full prompt/schema; it cannot be presented as exact current-comparison evidence. |
| [evaluation.rs](../../apps/desktop/src-tauri/src/evaluation.rs), [evaluation/curated.rs](../../apps/desktop/src-tauri/src/evaluation/curated.rs) | Existing native single worker, registration, cancellation, run tokens, private roots and model reservation are reusable. Run dispatch currently distinguishes built-in and curated data, not comparison data. |
| [evaluation-model.ts](../../apps/desktop/ui/evaluation-model.ts), [EvaluationEvidencePanel.tsx](../../apps/desktop/ui/EvaluationEvidencePanel.tsx) | Version1 built-in/curated contracts and six-story UI are not protocol2 comparison contracts. Preserve them. |

The current experiment remains state+recent transcript versus
state+relevant memory, with the same Core mandatory evidence. It is not a
literal transcript-only baseline, verified-cache comparison, general prose
quality result, or Domain2 corpus. Preserve all 24 frozen texts, the two
actual policies, current Play2.5/compiler2/context2 and historical replay.
No alternative evaluator, provider, selector, narrator or Store writer is proposed.

## Three reviewable gates

1. **Readonly comparison GUI:** inspect real current/historical reports and
   available source/capture evidence through shared validation.
2. **Full comparison admission:** optional GUI start/resume of existing paired
   or rollout scene batches, with truthful native resource accounting.
3. **Required isolated selected-case rerun:** run only the selected turn in both
   policy arms, each from its actual source prefix, in fresh isolated storage.

Gate2 cannot stand in for Gate3. A selected rerun has an explicit selected-run
result and at most two rows; it must not claim four completed scenes or a full
comparison. A readonly first PR must keep selected rerun visibly unavailable
and the owning D07.06 acceptance unchecked until the shared prerequisite lands.

## Additive shared interfaces

Place the facade and selected runner inside the existing `comparison` module
so they can reuse private `RunManifest`, `StoredTurn`, `load_turn(s)`,
`validate_pair_source`, `TurnJob`, `execute_turn`, captures and ledgers.
The following names and signatures are a proposed API, not existing Rust:

```rust
pub enum Arm { Left, Right }
pub struct RowId { pub turn: String, pub arm: Arm }
pub enum Edge { Before, After }

// Fields private. Owns validated native root/pins/existing-read-lock and
// reconstructed report/checkpoints, not a deserialized canonical authority.
pub struct OpenedComparison { /* private */ }
pub struct PreparedSelectedComparison { /* private; not Deserialize/Serialize */ }

pub fn open_read_only(dir: &Path) -> Result<OpenedComparison>;
pub fn summary(
    run: &OpenedComparison, native_inspection_granted: bool,
) -> Result<ComparisonDesktopDto>;
pub fn evidence(
    run: &OpenedComparison, row: &RowId, request: &EvidenceRequest,
    native_inspection_granted: bool,
) -> Result<ComparisonEvidenceDto>;
pub fn prepare_selected(
    run: &OpenedComparison, turn: &str,
) -> Result<PreparedSelectedComparison>;
pub fn run_selected(
    plan: PreparedSelectedComparison, new_dir: &Path,
    cancel: &Cancellation, factory: LaneFactory,
) -> Result<SelectedComparisonReportV1>;
pub fn run_native_selected(
    plan: PreparedSelectedComparison, new_dir: &Path,
    cancel: &Cancellation, assets: NativeAssets<'_>,
) -> Result<SelectedComparisonReportV1>;
// A separate resume_selected entry reconstructs the same immutable selected
// identity from native-owned metadata and validates source+destination before work.
```

No renderer can construct these opaque handles, a Core Receipt, ContextPackage,
AcceptedHistoryBasis or prepared command from JSON. Do not add `Deserialize`,
`Serialize` or `Debug` to opaque/private Core types to implement transport.
Native code supplies paths and inspection grant; neither is a wire parameter.

Proposed Serialize-only DTO shapes, constructed only after shared validation:

```text
ComparisonDesktopDto {
  version: 1, protocol_version: 2,
  binding: native-computed selection/snapshot binding,
  report: unchanged actual ComparisonReportV2,
  rows: [RowSourceDto; bounded by actual retained rows],
  read_only: bool, resume_allowed: bool, selected_rerun_allowed: bool,
  unavailable: [closed reason + optional RowId]
}
RowSourceDto {
  row: RowId,
  source: Available {
    scope: actual Scope, before_head: actual completed boundary,
    after_head: actual completed boundary,
    input_semantic_sha256: actual validated value
  } | Unavailable { reason: closed reason },
  capture_available: bool, receipt_available: bool, unavailable: [closed reason]
}
ComparisonEvidenceDto {
  version: 1, binding, row: RowId, scope, before_head, after_head,
  observer, edge: Before|After, read_only: true, generation_grant: false,
  body: Query2Page | AcceptedReceipt | ValidatedCapture | RecordedOutput | Missing
}
SelectedComparisonReportV1 {
  version: 1, run_type: "selected_case", source_protocol_version: 2,
  source_binding, source_kind: existing ComparisonKind, selected_turn,
  source_inputs: [native per-arm scope/head/input bindings],
  rows: actual TurnReportV2 values (0..2), completed: bool,
  per_arm_progress, actual per-arm budget/setup/provenance,
  human_reviewed: 0, quality_accepted: false, unavailable, limitations
}
```

Use the proposed closed `Available{...}|Unavailable{reason}` source union;
never guess scope/heads when a valid row lacks reconstructable source.
A missing capture is not a corrupt
report by itself. Corrupt retained evidence that the producer requires remains
an integrity error. Root should freeze the union's exact serde tagging before tests.

`binding` detects drift and matches replies; it does not authenticate adversarial
files or grant execution. Authority remains native path ownership, shared replay,
full request/source equality and actual prepared objects. Never reconstruct a
canonical engine from report hashes, narration or stored prompt text.

Readonly opening pins ancestors and takes an **existing** `run.lock` without
creating files, ledgers, reservations, reports or settlement. Current `take_lock`
uses `create(true)` and is an execution helper, not this reader. Reuse the existing
curated pin/read-lock mechanism through a narrow shared helper extraction if
needed. Reject a busy external writer; do not race a multi-file snapshot. A
manager's active run exposes its last validated immutable snapshot, labelled as
such, rather than rebuilding unsealed current files while its worker writes.

## Evidence and privacy

Revalidate with the same `load_turn`/recording/capture checks that inspect uses:
run/source/profile/suite/policy binding, exact full request, actual before/after
history and semantic hashes, raw recording hashes, repaired prompt relation,
privacy/output/forwarded-budget checks. A matching report hash alone is insufficient.

Derive source edges in Rust from actual StoredTurn and completed Core boundaries.
For Query2 evidence, create the appropriate actual historical engine and bind
the returned query to that engine's scope/head. The user's gameplay head is a
different authorization/presentation fence. Renderer changes cannot choose an
arbitrary source head, filename, Store path or request text.

Return one evidence variant per request. Proposed wire bounds: existing report
cap 2 MiB; at most 48 full-run rows, two selected rows; Query2 page at its existing
64 KiB cap; current private capture at existing `MAX_PRIVATE_CAPTURE=196608` bytes;
one complete evidence response at most 256 KiB. Split query/capture/raw-output
navigation rather than combining every cap into one oversized reply. Preserve
the existing per-output limits and validated stored byte lengths. Never truncate
captured evidence and call it complete; return a typed unavailable/too-large result.

Raw capture/role text is available only to a trusted private omniscient view.
The full unchanged report envelope is also private: `summary` refuses a missing
native inspection grant, and the native adapter permits it only in the trusted
omniscient lens. A public catalog exposes bounded run metadata, never that report.
Actor inspection is derived and filtered by Rust before return; it must not
receive the full report/raw capture and rely on client-side hiding. Preserve
original scoped sources. Readonly inspection never alters an actor's knowledge,
the generation observer, memory policy, prompt eligibility or canonical history.
Render all text inertly; no HTML execution, external navigation or renderer paths.

Historical omitted forwarded estimates stay omitted. `roles_known=false` means
unknown even if a stored numeric field is zero. Null first-response/commit times,
missing capture, guard-only, dependency, fallback and recovered-without-checkpoint
rows remain explicit. Do not synthesize tokens, timings, traces, repaired prompts
or human scores. Display actual two-arm charges and one physical setup with their
declared meanings, not a sum implying two physical loads. Forwarded byte/token
estimates are estimates, including their unmeasured envelope reserve, not tokenizer
measurements or phone performance. Retain every report limitation.

## Selected plan, source preflight and recovery

The native selection is a frozen-suite turn ID. Clicking either row proposes
rerunning that turn in both arms; it does not choose a new policy or expected result.
Reject a missing/unreconstructable selected input explicitly.

- **PairedSnapshots:** derive both inputs from the actual validated reference
  prefix for that exact step. Validate each existing pair Store against the full
  reference prefix and entire current Request. Preserve same-input semantics.
- **ContinuousRollout:** derive each arm's own actual pre-turn Engine/Request.
  Preserve divergence; do not replace either chain with reference outcomes or
  equalize the two inputs. No implicit replay/generation of preceding turns.

Prepare validates both arms read-only, including current source/profile/suite,
checkpoint identity, full request and accepted prefix, before destination creation,
invocation reservation or native assets. Revalidate at execution before any new
invocation and immediately before `execute_turn`. Reuse the accepted
`validate_pair_source` rule: an extra accepted receipt is recoverable only for
the exact full same current request after the exact prefix. Same turn key with
different FreeText or another accepted turn fails closed. Preserve the existing
five resume-basis regressions and absolute clock oracles unchanged.

Use the existing actual Store bootstrap/replay and recorded outcomes to create
fresh destination arm histories. No SQL history copy/writer, forged receipt,
expected-outcome injection, new provider or selector is allowed. Only the selected
turn is newly evaluated. Inspecting/planning/resuming committed output calls no LLM.
New model outcomes may fail or diverge; publish those results honestly.

The selected-run manifest is additive and separately tagged. Do not change the
meaning/bytes of protocol1, full ComparisonReportV2 or historical Play2.1–2.5.
Persist native run/client/source-selection identity before starting its worker so
a lost start acknowledgement is resolved through readonly exact-client lookup.
UI recovery never silently generates another client key, invokes another start,
changes the selected input or resumes on opening a report.

Execution uses existing ledgers and immutable per-arm checkpoint publication.
Keep current caps (32 admissions, 96 roles, 30 active minutes, 32 invocations per
existing ledger); selected mode may use less work, never a larger quota. Each
selected attempt admits at most the selected turn once per unfinished arm;
role/repair charges use the unchanged actual execution path and ledger, not a new
unbounded per-case allowance. Charge
actual execution preflight/setup/capture/commit/cleanup under the original clock
origin and absolute deadline rules. Preserve unknown interrupted reservations.
Do not hide work under a free replacement invocation or invent a physical setup time.

Cancellation requests stop future admission and signal the actual provider; it is
not a rollback promise. Preserve a committed selected arm and its recorded reply
if cancellation races completion. A cancelled partial selected run records actual
completed rows and missing/unfinished arms; resume addresses only those unfinished
arms under the same native manifest. Exact committed recovery makes zero new roles
and never invents missing historic capture. Publication/state settlement remains
existing runner-owned; native/UI cannot manufacture a successful terminal report.

## Source fingerprint and historical runs

[build.rs](../../crates/locallore-eval/build.rs) fingerprints Rust/SQL sources
across Core/Storage/Workspace/Eval and relevant fixtures/manifests/locks. Archive3
changes and the new shared facade/selected code change the current fingerprint.
Retained PR154/model cohorts keep their original source and become readonly when
`source_matches=false`. Do not waive this fence because the visible suite is equal.

Freeze final shared APIs first; then generate fresh source-matching scripted
reference/cohorts for the new tests. Separate new-source native execution is needed
for native claims. Pure desktop-only edits need not be misrepresented as changing
an unchanged shared fingerprint. Historical report opening preserves all original
values and missing fields; no new-source timing/quality attribution is permitted.

## Native owner and closed wire boundary

Add a comparison child of the existing EvaluationManager, not another manager,
worker, resource ledger, inference process or result broker. Explicitly dispatch
built-in/curated/comparison run kinds in token/status/cancel handling rather than
assuming every non-built-in token is curated. Reuse registration, single worker,
cancellation registry, lease retirement/drain and current root/run quotas.

Proposed one `evaluation_comparison` command with exact action-specific keys:

| Action | Renderer fields in addition to action |
| --- | --- |
| catalog | none |
| open | runId |
| lookup | clientId |
| status/read | runToken |
| evidence | runToken, binding, turnId, arm, evidenceKind, edge, observer, view |
| start | clientId, lane, kind, batch, consent |
| resume | runToken, batch, consent |
| rerun | clientId, sourceToken, binding, turnId, consent |

Root must freeze a tagged Rust request enum and matching TS schema before tests;
irrelevant keys are rejected, not ignored. Envelope cap starts at existing 4096
bytes. Use primitive IDs and closed kinds/arms/lanes/batches/views; strict scalar
types and key sets, no `String(array)` enum coercion. A native-only trusted game
session/scope/head and inspection grant authorize private access independently of
these experiment IDs. Never accept a JSON `grant` or caller filesystem path.

Existing `evaluation_cancel(runToken, operationId)` may be reused after explicit
run-kind routing. Writes are exclusively under the application's owned comparison
root, pinned and subject to existing run/root/free-space/retention caps. No CLI
subprocess or renderer output filename is accepted. Optional existing CLI-cohort
opening requires a native-selected pinned readonly capability; it cannot be
promoted into a write/resume token. A dev harness can substitute only a fixed
owned source root, not expose a general directory API.

Native execution uses the existing approved imported model/resource paths and
`ModelManager::reserve_evaluation`. Ordinary Play must unload its model first.
No fallback from native to scripted, auto model load/download, arbitrary profile
or renderer-supplied worker path. Show the actual bound approved profile and
availability. Source-mismatch/basis rejection happens before opening assets or
admitting roles; release the reservation on every error/retirement path.

## Frontend state and navigation

Add a dedicated strict comparison model/controller/panel instead of casting into
version1 EvaluationReport or changing curated behavior. Root supplies coherent
native-granted context. Bind each result to run token/operation, source binding,
selected turn/arm/evidence kind/edge/observer and a monotonically increasing reply
epoch. Model/lane/kind/run/selection changes reset consent and selected evidence.

On game session/scope/head, Story Lab permission or lens retirement, clear private
presentation and suppress late replies. Preserve only the original bounded pending
operation/client identity for explicit lookup/status/cancel; do not claim that
clearing the panel cancelled or rolled back native work. Opening a report does
not start/resume inference. Avoid synchronous subscription self-invalidation from
own pending/blocked updates, as in prior author/archive coordination fixes.

Source navigation stays in the isolated run's readonly evidence panel. Never use
`Controller.resume(source.scope)`, inject a fake gameplay Context/empty receipts,
or import experiment canon into the user's active workspace. Native-derived scoped
source links retain original scope and sequence. New admission joins Root's model,
gameplay/author pending and unknown-operation readiness deliberately; do not assume
the existing dispatcher guards include comparison commands.

## Allocation proposal and first frozen tests

These paths require separate claims; this document grants no edit ownership:

- Shared: existing `local_lane/comparison.rs`; new `comparison/desktop_api.rs`
  and `comparison/selected.rs`; additive selected DTOs in `memory_comparison_v2.rs`
  if needed. A minimal visibility extraction from existing curated reader helpers
  is an explicit extra allocation, not a hidden rewrite.
- Native: new `src-tauri/src/evaluation/comparison.rs`; Root owns existing
  evaluation/commands/model-owner dispatch, handler/permissions and integration.
- Frontend: new `ui/comparison-model.ts`, `comparison-controller.ts`,
  `ComparisonPanel.tsx`; Root owns EvaluationPanel/main/App mounting/context.

First freeze actual API tests before production, on final agreed signatures:

| Proposed frozen test target | Meaningful required oracles |
| --- | --- |
| `comparison_desktop_review.rs` | Real producer scripted paired/rollout data; strict report/source/capture reconstruction; actual scope/heads; complete before/after inventory unchanged and zero provider calls on read; actor privacy; missing capture/unknown historic roles; unknown/foreign row/arm/binding rejection; historic source readonly with every original byte retained. |
| `comparison_selected_review.rs` | Exact isolated two-arm pre-turn inputs, paired equal reference vs divergent rollout; no preceding turns regenerated; source inventory/canon unchanged; wrong full request/extra accepted source on either arm refused before new destination/reservation/assets/roles; stale plan/source mismatch; budget exhaustion, cancel before/between/after arm commits and exact lostack recovery with zero duplicate roles/evidence. |
| Native comparison adapter tests | Real shared runner plus model-owner/lease state: one worker, exact run kinds/token/operation, missing/loaded/busy model refusal, closed paths and private grant, unknown-start client lookup, retired-window no publication, source and consent fences. No models executed unless separately allocated. |
| `check-comparison-controller.mjs` | Bounded fixtures captured from actual Rust producer; strict scalar/key/null/missing/array-enum cases, source-match readonly, exact row/lens epochs, pending/cancel/lookup recovery, zero unintended dispatch, truthful optional metrics; headless rendering explicitly labelled. |
| App-owned comparison harness | Actual same controller/native IPC and hidden WebView2 render; source/capture navigation, historical readonly refusal, selected rerun/cancel/resume/restart and late completion; coherent semantic snapshots and inspected CapturePreview images. Scripted and actual native-model evidence stay separate. |

Do not invent a native capture from manually assembled JSON or reuse a mock as
actual rendering. Keep generated fixture captures/databases/outputs local and
gitignored. Reuse existing synthetic providers only to test plumbing; no production
test-only arbitrary execution API or exposed debug server.

Prospective Root commands, all **UNRUN** here; the new targets/scripts do not yet
exist. Allocate source-owned targets and the exclusive execution slot first:

```powershell
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --test comparison_desktop_review --test comparison_selected_review -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --test comparison_runner --test memory_comparison_v2 --test comparison_resume_basis_review --test comparison_historical_readonly -- --test-threads=1
cargo clippy --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --all-targets --all-features -- -D warnings
cargo test --locked --offline -p locallore-desktop-spike --bin locallore-desktop-spike evaluation::comparison:: -- --test-threads=1
# apps/desktop; proposed new checker, then existing whole frontend gate:
node check-comparison-controller.mjs
node verify-frontend.mjs
# Proposed fixed app-owned runtime harness, only after native registration/build:
node comparison-harness.mjs
```

Require nonzero expected test counts and retained first failures; an absent filter
matching zero tests is not a pass. Root then runs affected normal/dev builds,
strict shared/native lint, formatting, Android compatibility and normal-hook
exclusion. No device/physical/model/UI result follows merely from compilation.
Inspect generated native images for visible-state/layout defects before GUI
acceptance. Existing private model resources and protected chats stay untouched.

Next runnable task is Root review of this proposal and signature/path allocation,
then the first frozen shared facade/selected-plan tests. This document reports no
implementation, runtime versions newly queried, measurements, approval score,
merge/release or completed D07 gate.

## Coordinator Gate1 decision — 2026-10-24

Root reviewed the proposal and actual producer/reader sources, then integrated
accepted main `a06109893d678bc8b3b28c5d5ca9d1a4529fdf54` into the reused
worktree on `impl/d07-comparison-view` (integration `7861454d`). Only this
proposal differs from that accepted tree. Claim:
[#29 6393104388](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6393104388).
The following reader API and tests are frozen first. Selected execution,
native/GUI write commands and all migration proposals remain unapproved.

Root owns `comparison.rs`, new `comparison/desktop_api.rs`, this document and
only a minimal reusable directory-pin/read-lock helper extraction in the
existing curated `local_lane/desktop_api.rs`. The independent test writer will
own only new `tests/comparison_desktop_review.rs` on a separate worktree.
No provider, model assets, invocation, ledger settlement, report publication,
database migration, canonical write or new dependency is allowed in the reader.

Public API under `local_lane::comparison::desktop_api`:

```rust
use locallore::inspection_query::{Observer, View};
use serde_json::Value;
use std::path::Path;

pub enum Arm { Left, Right } // Clone + Copy + Debug + Eq + PartialEq
pub struct RowId { pub turn: String, pub arm: Arm } // ordinary typed identity
pub enum Edge { Before, After } // Clone + Copy + Debug + Eq + PartialEq
pub enum EvidenceRequest {
    Query { edge: Edge, observer: Observer, view: View },
    Receipt { observer: Observer },
    Capture { observer: Observer },
    Outputs { observer: Observer },
}
pub struct OpenedComparison { /* private fields, no Debug/serde/Clone */ }
pub fn open_read_only(dir: &Path) -> Result<OpenedComparison, String>;
pub fn summary(run: &OpenedComparison, native_inspection_granted: bool)
    -> Result<Value, String>;
pub fn evidence(run: &OpenedComparison, expected_binding: &str,
    row: &RowId, request: EvidenceRequest, native_inspection_granted: bool)
    -> Result<Value, String>;
```

The returned JSON is data, never an accepted-history or permission capability.
Private Core objects remain opaque and unchanged. Gate1 summary has exactly:
`version:1`, `protocol_version:2`, a64-character native-computed `binding`,
the actual reconstructed `report`, `rows`, `read_only:true`,
`execution_available:false`, and `unavailable` listing
`selected_rerun_not_implemented` / `full_comparison_gui_not_implemented`.
This supersedes the proposed `resume_allowed`/`selected_rerun_allowed` booleans:
a matching source alone must not imply execution/resource permission.
The binding hashes the validated snapshot/report/row-source identity, including
its original source and actual hashes; it is a drift fence, not authentication.

Each row contains `row:{turn,arm}`, `source:{status:"available",scope,
before_head,after_head,input_semantic_sha256}`, `capture_available`,
`receipt_available`, `recording_available`, and `unavailable`. Values come from
actual validated StoredTurn/Core data. A required missing/corrupt database or
checkpoint is an integrity failure; do not disguise it as missing optional data.
All current valid producer rows require reconstructable source. Existing report
values, absent estimates, unknown roles, null timings and limitations remain
unchanged; no scope/head is guessed from row ordinal or admission index.

Every evidence reply contains `version:1`, `binding`, `row`, `scope`,
`before_head`, `after_head`, `observer`, `edge`, `read_only:true`,
`generation_grant:false`, and one `body`:

- `kind:"query", page:<actual Query2 page>` for the requested actual edge.
- `kind:"receipt", receipt:<actual accepted receipt>` at edge `after`.
- `kind:"capture", capture:<validated recorded capture>` with edge null.
- `kind:"outputs", outputs:[{role,bytes,sha256,text}]` with edge null.
- `kind:"missing", reason:<closed missing reason>` for an optional absence.

Capture/output evidence spans actual recorded stages; a null edge does not
pretend they all came from one before/after context. Closed missing reasons are
`capture_unavailable`, `recording_unavailable`, `no_accepted_receipt`.
Present required evidence that fails its producer hash/semantic checks is an
error, not a missing capture. A guard-only row has no invented accepted receipt.
Query2 first cuts the actual Store engine with `at_revision(edge_head)`, then
queries that cut with version2, its exact scope, expected_head=edge_head,
at_revision=None, limit64 (existing MAX_ROWS), empty search and no cursor.
Both page.head and page.revision therefore equal the requested edge; a later
full-run head is not presented as this selected snapshot. This gate supplies
one bounded page, not an invented full-history view.

Missing native inspection grant returns `Forbidden` for summary and evidence.
Receipt/capture/output additionally require `Observer::Omniscient`; a granted
actor query still uses Rust's actual Query2 filtering. Wrong snapshot binding
returns `SnapshotMismatch`; unknown row returns `UnknownRow`. Existing source
integrity failures retain fixed errors without paths/story content. Readonly
opening requires an existing ordinary `run.lock`, rejects a held writer lock,
pins owned ancestors/known child directories and creates nothing. The snapshot
must remain coherent; evidence may revalidate source under that retained lock.
Summary is capped at2 MiB/48 rows; Query2 keeps its64 KiB page cap, capture keeps
196608 bytes and the complete evidence envelope is capped at256 KiB. Refuse
oversized evidence explicitly rather than truncating it as complete.

First frozen tests use actual scripted paired and rollout producers. They check
report equality/derived scope and heads, exact before/after Query2 actor views,
private raw-evidence denial, wrong row/binding/grant, honest guard/missing data,
actual corrupt evidence refusal, existing/held/missing lock behavior and complete
inventory/ledger nonmutation. A genuine retained historical opt-in fixture must
preserve its original bytes and source mismatch; never synthesize a historical
report by editing source labels. No provider/execution inputs exist in this API;
no inference/model/runtime result is inferred from reader compilation or metadata.
Root will retain the first compile/behavior results separately, then proceed
through native/UI and the independently frozen selected-run prerequisite.
