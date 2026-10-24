# Current-pipeline comparison integration contract — 2026-10-23

Refs #29 D07.03/.04/.05 prerequisite. **Source-only proposal, not an executed
comparison or implementation approval.** Agent resource_metrics_review owns
ONLY this NEW document in `design/d07-comparison-current` /
`source-comparison-current`, from exact
`d8e248419369abad5d75d5dd6d378864b9d0d83b`. Claim #29 6378067558. Root owns
production, future path allocation, actual tests, native/model authorization
and integration. No existing source/test/fixture/report was changed.

Bindings: pending packet `c67d278b14b3d55e844c7a84a088a784ae9b17ae` in
`source-memory-comparison`, including NEW eval source/test
`memory_comparison.rs` and
`docs/eval/D07_MEMORY_COMPARISON_PROTOCOL_2026-10-23.md`; frozen source/oracles
68e2101. That packet is unregistered/uncompiled, with no runner. Current Core
source has actual Play2.5/compiler2/context2, both real policies, safe staged
narration2.2 and Store revalidation; their availability is not evidence that a
two-arm comparison ran. Earlier raw/verified2.4 reports remain exactly that.

## What exists and what is missing

| Actual source | Current behavior / smallest required change |
|---|---|
| Core `play::execute_traced_with_policy`, `PlayConstructionInput` | Both actual enum arms use the shared compiler and canonical stage/commit. Reuse unchanged; no new compiler, narrator memory feed or command repair. |
| Host `LocalPlay`, configure_local_provider/configure_fixture_provider, prepare/Work | LocalPlay holds profile/provider/real_model only; prepare calls default-Relevant coverage entry. A native-only closed policy port is missing. Core availability cannot configure a Host arm today. |
| Pending memory_comparison.rs | Private frozen courier suite, actual Core reference oracle, observation checks, semantic comparator and human renderer exist only as pending source. `require_execution` unconditionally refuses both policies; version1 renderer explicitly says unsupported. Do not flip an enum/boolean and call that execution. |
| Eval local_lane.rs | Actual Host/Store/provider loop, LaneFactory, Ledger, locks, immutable checkpoints and native resource admission exist. Extend their shared control, not a second inference or persistence system. Its four-turn Story format/failure-stop behavior cannot silently become the courier's24-turn semantics. |
| local_recording.rs | Actual bounded role envelopes/raw outputs, lost-capture flag, native role metrics, immutable request identity and per-role forbidden lists. Reuse this exact provider wrapper and runtime adapter. Add current policy/evidence attribution without rewriting old capture types/reports. |
| Host private trace capture | Actual ContextPackage is captured, but exposed to native caller as bounded private JSON. The pending pure checker accepts `&ContextPackage`, which is Serialize-only. A report-evidence bridge is needed; do not add Core Deserialize or invent a package. |

## Freeze the experiment, not just two labels

Keep the pending `frozen_suite()` Seed/24 exact texts/expected commands/errors
unchanged, including punctuation, five Dialogue attempts, one Wait and the
existing four scenes of six attempts. Expected denominators per arm are24
attempts,21 accepted provider turns and3 guard-only refusals: attempt09
Inventory,10 Ability,24 ClarificationRequired. These are planned expectations,
not promised actual results. Do not add a supported CompletePromise form,
automatically complete the seed promise, insert an expected Receipt after a
failure, rewrite initial ownership/energy, or tune the corpus to model output.
Measure the unchanged suite's canonical SHA through its actual constructor at
first model-free qualification; this document invents no hash/result.

Requested policies are the SAME Core enum:
`StateRecentTranscriptV1` versus `StateRelevantMemoryV1`. Both preserve common
mandatory rules/current state/observed values/beliefs/relationships/promises,
their evidence, references/aliases and the recent-event floor. Optional units
and exact/lexical selection differ; coverage representation is independent.
Use names state+recent-transcript control and state+relevant-memory, not literal
transcript-only or raw-versus-verified. Recommend an explicit #29 plan
clarification retaining D07.04's ID/history; do not silently check off its
literal transcript-only criterion or ask a new architecture question here.

One run chooses ONE experiment kind. Running both is two distinct bound runs,
not an automatic hidden multiplier:

- **PairedSnapshots:** for each of24 attempts, two isolated physical Stores
  receive exactly the SAME previously frozen canonical reference prefix,
  Seed/Scope/head/original Requests/events/narration. Never rename canonical
  story/branch IDs to isolate them; filesystem/run IDs are separate. Rehydrate
  validated reference receipts through actual Store begin/commit/replay APIs,
  not SQL or projection insertion. Require exact full accepted-basis equality
  before admitting either arm. Discard each arm's post-step history for the
  next pair; failures remain reported, not patched into a success.
- **ContinuousRollout:** two independent Stores each retain their own actual
  accepted chain across all four scenes. Rejections leave that arm's state
  unchanged. Continue a later expected-accepted action only when the SAME Core
  reference oracle says it is viable in that actual state; otherwise record
  NotRunDependency with the actual error. Do not skip every subsequent step
  merely because one failed, and do not insert the common reference history.
  Mark first semantic divergence and stop calling later rows same-snapshot A/B.

Paired mode requires a privately frozen **actual scripted reference bundle**,
created once through the same Host/Play/Store path and validated/replayed before
native admissions. That is an explicit bounded scripted prerequisite run,
with its own existing Ledger/caps, not extra hidden model work in either arm.
Its expected21 accepted turns imply42 fake role calls without repair; report
actual calls, failures, timings and profile separately. If reference construction
fails, no native comparison starts. Complete/freeze its exact receipt prefixes,
full bases and manifest before binding the pair run. Do not regenerate it on
resume (timings/provenance can change the exact bases). Missing/drifted reference
means closed refusal/new run, not recomputation. Stored reference outcomes
remain labeled scripted; model-arm failures are never teacher-forced away.

Courier reference/current comparison is explicitly Domain1. If an unexpected
Domain2/author record appears, refuse UnsupportedScenarioVersion before a
receipts-only semantic hash. Shared Domain2 tests remain separately necessary;
do not silently flatten author history into this original corpus.

## Proposed native Host port and exact ownership

Proposed signatures, not allocated implementation in this document:

```rust
// Existing methods keep their default-Relevant behavior.
impl Host {
    pub fn configure_local_provider_with_policy(
        &self, profile: PlayProfile, provider: ProviderFactory,
        policy: ContextPolicy,
    ) -> Result<(), String>;
    pub fn configure_fixture_provider_with_policy(
        &self, profile: PlayProfile, provider: ProviderFactory,
        policy: ContextPolicy,
    ) -> Result<(), String>;
}
```

Store the closed policy alongside profile/provider in LocalPlay and freeze it
in Work with the existing provider/profile snapshot. Prepare invokes the SAME
current `execute_traced_with_policy`, borrowing its coherent CoverageRead. No
HostCommand/JSON/model/inspection capability, schema change, policy setter for
a live renderer, availability boolean or independent knowledge source. Native
comparison configures each isolated Host once before submitting any turn.
Profile/policy reconfiguration cannot relabel an already accepted receipt;
recorded retry wins. New accepted receipt.context_policy must equal its bound
arm; a different saved policy means checkpoint mismatch, not regenerate/relabel.

Proposed future write ownership, requiring Root approval/claims first:

| Paths | Narrow allocation |
|---|---|
| existing `crates/locallore/src/host.rs`; NEW Workspace test `tests/comparison_policy.rs` | Root/shared owner: native policy methods, LocalPlay→Work forwarding; actual durable Host default/both-arm/pending/retry/source/consent tests. No Store/compiler/Play production changes anticipated. |
| pending eval `src/memory_comparison.rs`, `tests/memory_comparison.rs` | Protocol owner: preserve immutable suite/version1 unsupported/report history, add explicit current observation/binding/partial-evidence validation; no caller-enabled gate. Use/re-export Core ContextPolicy, not a competing selection enum. |
| existing eval `src/local_lane.rs`; NEW `src/local_lane/comparison.rs` | Runner owner: additive child module can reuse private parent Ledger/LaneFactory/profile/provider/raw/checkpoint helpers without broad visibility refactor. Factor only the common actual turn-control lifecycle if needed; keep curated suite behavior/checkpoints unchanged. New courier loop uses actual shared Host and Store. |
| existing eval `src/local_recording.rs`, `src/lib.rs` | Recorder/registration owner: current-only versioned policy/context/evidence metadata and module registration; unchanged old serde/report validation. Do not copy runtime or reservation code. |
| existing eval `src/main.rs`; NEW focused integration tests/docs | Fixed compare reference/run/resume CLI grammar and bounded native APIs; no arbitrary corpus/schema/provider/SQL/shell flags. Reuse NativeAssets and current approved runtime, worker/profile checks and error categories. |
| desktop native evaluation/UI, Android, model broker | Later separate allocation. First shared runner/CLI qualification does not add UI/native IPC parity, new background work or model authorization. Existing broker reservation must still exclude other app model owners if later adopted. |

Suggested eval public native surface, exact error/report DTO names may be frozen
with implementation approval:

```rust
pub enum ComparisonKind { PairedSnapshots, ContinuousRollout }
pub fn prepare_comparison_reference(directory: &Path, cancel: &Cancellation)
    -> Result<ReferenceReport>; // fixed suite, scripted only, no asset arguments
pub fn run_comparison(directory: &Path, resume: bool, kind: ComparisonKind,
    cancel: &Cancellation, max_new_scenes: usize, factory: LaneFactory,
    reference: Option<&ValidatedReference>) -> Result<ComparisonReport>;
// Native wrapper reserves setup BEFORE asset hashing/loading; cached complete
// path returns before constructing/opening assets/runtime/provider.
pub fn run_native_comparison(/* same bounded arguments, NativeAssets */)
    -> Result<ComparisonReport>;
```

ValidatedReference is native/read-only, built by strict actual replay of fixed
bounded reference files; checksums alone cannot construct authority. Only
paired mode accepts/requires it. No new canonical save format, database schema,
inference engine, memory implementation or arbitrary snapshot import is added.

## Actual context/evidence bridge and current version binding

Reuse existing explicit synthetic StoryLab trace capture per turn: enable the
existing exact-session private capture with consent, read the actual
selected_context artifact immediately while its owner/attempt is live, then
revoke/close through existing fences. Same already-authorized synthetic corpus
only, never user stories. Use the actual observed attempt identity, not assumed
attempt0. Read at actual current head while matching original base/turn/player.
TraceUnavailable/expiry/truncation yields unavailable evidence, never rebuilt
historical capture or a false privacy pass. No new debug server or generic hook.

An eval-only `CapturedContext::from_host_capture(before, request, identity,
reply, admitted_requests)` validates bounded JSON, outer owner/selection,
package2 scope/head/revision/player/Director, and selected-record projection
against the ACTUAL Director envelope. Compute mandatory/selection fingerprints
from those actual recorded rows. This report-only wrapper has private fields;
it is not a Core ContextPackage/proof/Engine and has no generation/commit route.
Do not add Deserialize to Core or silently pass a fresh compiler reconstruction
as actual capture. A typed direct-Core test capture remains a separate input
variant. Missing capture means missing metrics/failure of that evidence gate.
Persist only actual bounded artifacts through existing fixed-name/raw-ref
writers, hash/size validation and inert escaped rendering; no renderer bytes
become authoritative state. Respect capture3 attempts/16 artifacts/49,152B each,
196,608B per attempt/524,288B total and600s access TTL; read per turn rather than
assuming a30-minute run fits in the in-memory ring.

New current experiment/checkpoint format is explicit version2 (not rewriting
old report1). Binding includes suite canonical SHA, protocol/constructor/order
versions, run+arm+kind, exact requested Core policy, source_inputs hash, seed/
scope/rules/domain, context2/compiler2, Play2.5/narrator2.2, actual profile/model/
worker/template/runtime/manifest hashes, sampling settings, fixed budgets and
reference manifest hash where applicable. Existing recursive source_inputs
already covers all new Rust files/locks/migrations. Source/profile/policy/kind/
suite/order/reference drift refuses resume; old artifacts stay read-only.

Accepted observations require actual receipt's full current tuple and matching
requested policy. Guard-only has no accepted policy receipt/role execution:
record requested policy but execution not_run_guard. Failures/recovery without
receipt/capture carry explicit unknown fields, not invented policy/model proof.
Actual source-fallback and compiler coverage/cached/raw counters are independent
of selection policy. Default comparison creates fresh isolated stores, performs
no derivative maintenance, and records the actual raw/no-cache conditions;
do not call Relevant a verified-cache arm. A later cache-representation study
is a separately bound experiment, not a renamed old raw-versus-verified report.

## Semantic input equality, not canonical authority

Keep opaque accepted-history bases for every before/after and each arm's exact
chain. They alone protect canonical source; never replace them with comparison
hashes. A versioned comparison-only semantic hash covers actual Seed, Scope,
head, original Request/Proposal/accepted events/displayed narration across the
Domain1 prefix, plus current attempt identity. Exclude Play timings/profile/
coverage diagnostics/policy provenance only from this semantic equality view.
Include original speech and displayed narration because Recent may consume
them. Never normalize away actual narrative/effect divergence.

Thus timings/policy metadata may make exact full bases differ after turn1 while
semantic input remains equal. Paired mode STILL requires exact original basis
equality. Rollout separately reports first semantic output divergence, first
mechanical-effect divergence, exact-source pairs and eligible same-semantic-
input pairs. Later rollout rows after divergence remain observed outcomes, not
same-snapshot causal comparisons. Same-input common mandatory fingerprints
must agree, including actual rule/state/knowledge evidence, or hard-fail. Hashes
never grant knowledge or authenticate a raw JSON evidence packet.

## Unchanged caps, accounting and restart semantics

Per arm retain the existing32 admissions /96 charged roles /30 active minutes /
32 invocations. Per admitted turn reserve60,000ms +3 roles before work, profile
context4096/role350/deadline<=120,000ms/repair<=1, setup reserve120,000ms and
cleanup reserve3,000ms. Actual guard0roles and accepted2/repair3 settle only
after durable settlement. Raw role output cap16,384B stays. One two-arm run
ceiling is64 admissions/192 roles/60 active minutes/64 invocations; no automatic
second kind or retry cohort. Scripted reference is separately budgeted/labeled,
not charged as native model output or silently hidden. Existing caps are not
permission to execute any model call.

Use the SAME Ledger implementation and immutable reservation/settlement files
in each bound arm directory, one run lock/one sequential runtime owner. Unknown
reservations survive crash/resume at full original charge; neither cached
replay, a planned guard nor missing raw output refunds them. Explicit settled
measurements may replace reservations by the existing rules. Record admissions
across all attempts, observed versus charged/unknown roles, elapsed setup/turn/
cleanup and exhaustion separately. No reset by new process, cancellation or
checkpoint reread. Wall-clock cooperative deadlines can overshoot; report it.

Checkpoint actual per-turn results/source/immutable artifacts, group completed
six-turn scene manifests with their hashes; max_new_scenes is1..4. Old curated
four-turn files stay unchanged. After Store commit but lost result/ack, lookup
the exact stable key, strict-replay before/after and preserve the committed
outcome without another provider call. Missing original envelopes/metrics stay
unknown; create no historical prompt. An interrupted draft may get a NEW charged
admission if explicitly resumed, under the same request/source and remaining
caps; original unknown charge remains. Never inject the expected command.

On cancel stop new admissions, use existing Host cancellation/DeadlineGuard,
drain only owned provider/runtime work and report the actual final Store phase;
committed wins over late cancellation. No unrelated process/device control.
After crash, replay actual Stores plus checkpoints/reservations, never trust
serialized TurnRow as canonical authority. Report-only open uses the existing
read-only strict validators: no ledger/invocation/provider/asset/report rewrite.
Completed execution resume may charge the existing lightweight invocation path
honestly, but MUST skip native asset open/load/provider; do not claim zero
invocation charges unless actually implemented/measured. Stale source is
viewable read-only but not resumable for new work.

Freeze order before real calls: paired attempts alternate first arm; rollout
scenes alternate first arm, one runtime sequentially serves both. Bind that
order and report actual cold/warm/setup placement; do not duplicate one shared
load as two independent cold measurements. Actual profiler/token/RAM unknowns
remain unknown, no budget-as-phone-simulator or speed/quality superiority claim.

## Hard failure, human packet and qualification gates

Keep every rejection, repair, fallback, dependency skip, cancel, unknown charge
and capture loss. Canonical mutation on failure, cross-scope leakage, mandatory
mismatch or source substitution is a hard failure: stop new admissions and
preserve the failing packet. An ordinary rejected model proposal is retained;
later dependency skips require the actual same Core refusal, not blanket
post-failure omission. Planned24/21/3, observed attempts, actual accepted turns,
actual/charged/unknown roles and generated versus fallback narration have
distinct denominators. Empty samples yield no percentages.

The old pennant/amber statement at22 is an optional-selection target, not truth.
Measure actual context AND actual Director-envelope presence. If common
mandatory selection makes it nondiscriminative, report that; do not retune the
fixture. The finite action schema often fixes the command, and narrator2.2
receives only approved this-turn evidence. Neither optional retrieval presence
nor equal commands demonstrates causal recall, narrator-memory benefit or NPC
voice distinctiveness. The 24-attempt/21-expected-accepted courier is distinct
from the1,032-event retrieval stress and from a measured model-quality session.

Freeze the existing human rubric: faithfulness, agency, repetition, readability,
enjoyment all not_reviewed; npc_distinctiveness unsupported_narrator_only;
human_acceptance=false, quality_accepted=false; lexical checks finite/not semantic
oracle; fallback not generated-prose acceptance. Review all chronological
attempts, including guard/failure/fallback rows, not selected successes. Blind
arm labels A/B where practical and retain a separate immutable unblinding key.
Use escaped inert local HTML/Markdown with original inputs/actual displayed
text/error/fallback and hashes to exact private outputs. Preserve128KiB per
arm human-page cap,2MiB encoded protocol cap; a bounded index can link two
fixed arm pages instead of silently doubling the page bound. Human findings
remain separate append-only evidence, never a model judge or waiver of hard
privacy/canonical failures. No human review or score has occurred here.

Before any native cohort: qualify unchanged24/21/3 scripted reference, both
actual Host policies/record labels/guard0roles, actual captured mandatory and
optional selection, semantic-versus-full identity, rejected outcome/dependency
handling, same-key committed lost-ack0roles, draft unknown-charge restart,
cancel/late-commit, source/profile/reference mismatch, exhausted caps, complete
resume0asset/provider, raw evidence corruption/loss and inert output. Strict
old/current replay/source binding and existing curated nine/six-story suites
must stay green. Freeze executable oracles/source before fixes and run actual
default/local-model synthetic/strict checks in one allocated target. Then Root
can separately authorize a bounded source-bound cohort using already approved
assets; no new model/download/provider/worker or changed corpus after failures.

## Actual work and handoff

Only source/issue/Git reads, this one NEW document, `git diff --check`, owned-path
and clean-tree checks ran. Git2.33.0.windows.2, PowerShell7.6.5. No Rust/Node/
Gradle build, provider/model/asset/runtime/native/app/device/ADB/CUA/desktop,
transport/download/settings/protected-resource/PR/merge action. Prior tests and
model outcomes are their authors' attributed evidence, not this packet's run.

Root must approve exact path/API/version allocation and scripted-reference
prerequisite before implementation. First runnable task is the native Host
policy forwarding + shared scripted comparison qualification; current policy
enums alone satisfy no comparison/human/D07 acceptance gate. Release this
single-doc claim after handoff; leave full D07 checklists pending.
