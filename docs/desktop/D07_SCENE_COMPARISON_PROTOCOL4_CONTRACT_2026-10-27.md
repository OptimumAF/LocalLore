# Proposed scene comparison Protocol4 contract

2026-10-27. Refs #29 (D07.01/D07.04), supporting #25 (D04.04) and shared
#9 (M05.03). Independently authored from source
`232ad3791f4cc01bc83350c7d79c97d7eaa34abf`.

**Status: proposed, source-only, not implemented or qualified.** This document
precedes allocation of independent Protocol4 tests and producer implementation.
No Protocol4 compilation, tests, resume, model inference, native application,
WebView, Android or device execution is claimed. Root owns interface review,
later allocation, integration and execution. Existing Core/Host/capture checks
are separate evidence and do not implement this producer by implication.

The purpose is to compare the two new scene-narrator constructions through the
established Host/Store/provider path, while preserving Protocol3 and the original
human eight-sample **needs improvement** assessment and private packet unchanged.
This is neither an alpha release gate nor a claim of improved prose.

## Separate modules and public native APIs

Proposed new modules:

- `locallore_eval::memory_comparison_v4`: immutable descriptors, bindings and
  report types. Metadata deserialization never constructs runtime authority.
- `locallore_eval::local_lane::comparison::scene_v4`: protocol-specific producer,
  checkpoints, strict inspection and report publication.
- `scene_v4::native`, behind the existing `local-model` feature: thin adapter to
  the established reservation/runtime owner, not a new inference owner.
- Later, separately frozen `scene_v4::desktop_api` and
  `scene_v4::selected_v3`: read capability and isolated selected reruns.

The initial producer signatures use the existing native types:

```rust
pub fn run_comparison(
    dir: &Path,
    resume: bool,
    kind: ComparisonKind,
    cancel: &Cancellation,
    max_new_scenes: usize,
    factory: LaneFactory,
    reference: Option<&ValidatedReference>,
) -> Result<ComparisonReportV4, String>;

#[cfg(feature = "local-model")]
pub fn run_native_comparison<R: SelectedNativeReservation>(
    dir: &Path,
    resume: bool,
    kind: ComparisonKind,
    cancel: &Cancellation,
    max_new_scenes: usize,
    reserve: impl FnOnce() -> Result<R, String>,
    reference: Option<&ValidatedReference>,
) -> Result<ComparisonReportV4, SelectedNativeFailure<R>>;

pub fn inspect_comparison(dir: &Path) -> Result<ComparisonReportV4, String>;
```

`ComparisonKind` remains the existing closed PairedSnapshots/ContinuousRollout
type. `max_new_scenes` remains 1..=4. The scripted entry refuses a native factory;
only the native reservation entry may acquire assets. Inspection is read-only:
no provider, invocation, checkpoint repair, source import or model access.

If a CLI is added, use a new `scene-comparison` dispatch. It may expose scripted
run/resume, reference and inspect using the existing bounded argument grammar.
Native CLI execution remains unavailable without the trusted native lease;
there are no new arbitrary worker/model/command arguments. Existing
`literal-comparison` remains Protocol3.

## Closed descriptors and native construction mapping

New `ComparisonArmV4` has exactly `LiteralSceneV1` and `RelevantMemorySceneV1`,
serialized as `literal_scene_v1` and `relevant_memory_scene_v1`. Arm order is
fixed: left LiteralSceneV1, right RelevantMemorySceneV1.

`ArmDescriptorV4` is a closed `deny_unknown_fields` metadata object with exactly:

| Field | Type | LiteralSceneV1 | RelevantMemorySceneV1 |
| --- | --- | --- | --- |
| `arm` | `ComparisonArmV4` | LiteralSceneV1 | RelevantMemorySceneV1 |
| `prompt_version` | `String` | `locallore-play-v2.10-literal-director-v1-scene-frame-v1` | `locallore-play-v2.9-scene-frame-v1` |
| `narration_policy` | `String` | `grounded-prose-v2.4-scene-frame-v1` | same |
| `director_schema_id` | `String` | `locallore-director-literal-v1` | `locallore-director-v2` |
| `narrator_schema_id` | `String` | `locallore-narrator-v2` | same |
| `context_policy` | required nullable `Option<ContextPolicy>` | null | StateRelevantMemoryV1 |
| `compiler_version` | required nullable `Option<u16>` | null | 2 |
| `context_version` | required nullable `Option<u16>` | null | 2 |
| `literal_source_version` | required nullable `Option<u16>` | 1 | null |
| `literal_render_version` | required nullable `Option<u16>` | 1 | null |
| `literal_schema_version` | required nullable `Option<u16>` | 1 | null |
| `literal_packing_version` | required nullable `Option<u16>` | 1 | null |
| `forwarded_budget_version` | `u16` | 1 | 1 |
| `scene_frame_version` | `u16` | 1 | 1 |
| `scene_capture_gate_version` | `u16` | 1 | 1 |

Every nullable key is mandatory even when null. `validate()` compares the entire
object to the exact corresponding descriptor; omission, unknown fields,
mixed-arm fields and unknown versions are refused. Construct prompt/policy
strings from the existing Core constants rather than maintaining alternate
prompt text. Descriptor versions describe intended construction, not measured
execution or a persisted cache proof.

Only a private native match maps these two arms to
`HostPlayConstructionV1::PlayerLiteralSceneV1` and
`HostPlayConstructionV1::MemorySceneV1(StateRelevantMemoryV1)`. Expected Core gate
recipes are respectively `SceneRecipeV1::LiteralV1` and
`SceneRecipeV1::Memory(StateRelevantMemoryV1)`. Do not convert deserialized
descriptors into policies, add a Host JSON policy selector or change defaults.

## Versioned data and compatibility

All new protocol-specific decoders deny unknown fields. Required nullable keys
remain required rather than silently accepting absent Option members.

`CurrentBindingV4` has exactly the existing binding-shaped fields:
`protocol_version` (4), `arms` (the exact two V4 descriptors), `source_sha256`,
`suite_sha256`, `forwarded_budget_version` (1), `max_admissions`, `max_roles`,
`max_active_ms`, `attempts` (24), `expected_accepted` (21),
`expected_guard_only` (3), and `native`.

`ManifestV4` has exactly `version` (4), `source_sha256`, `binding`
(`CurrentBindingV4`), `profile` (full existing `PlayProfile`), `kind`,
required nullable `reference_sha256`, and `order` (`alternate-first-v1`). The
reference is required for paired snapshots and forbidden for rollout. Reuse
the established typed reference preparation/validation; do not synthesize a new
reference ledger or regenerate reference outcomes with a model. Execution and
resume require current complete source/profile/reference binding before assets.

`StoredTurnV4` has exactly `version` (4), `binding`, `index`, `arm`, `request`,
`before_head`, `after_head`, `row` (`TurnReportV4`), required nullable
`capture_file`, and required nullable `recording_file`.

Full-run scene seals have `version` (4), `binding`, `scene` and ordered
`checkpoints`. Full-run setup envelopes have `version` (4), `binding`,
`left_invocation`, `right_invocation`, `native`, `physical_ms`, `status`, and
required nullable `load`. Reuse the existing strict native-load metric decoder
with expected setup version4. Shared reservation/settlement/recording/raw-output
and capture formats keep their existing versions and limits; their binding
keys prevent cross-run adoption. Do not relabel their formats merely because
the surrounding report is version4.

A later selected manifest/report uses selected version3 and
`source_protocol_version` 4, exact V4 arms, original source binding/profile/kind,
the exact original selection and requests, per-arm prefix/input fingerprints,
and the existing native PreparedSelectedPlan capability/refresh discipline.
Selected2/source3 must remain closed to its original versions. Its first API and
field freeze is a separate allocation, not silently included in this document's
initial producer implementation.

Core `PlayRecord.version`, optional omitted `scene`/presentation encodings,
generation protocol, worker protocol and existing narrator schema remain
unchanged. Old records retain their actual historical recipes. New records use
the established scene tuple and Core restore dispatch. No storage migration or
old-to-new recipe conversion is introduced by Protocol4.

## Report fields and precise evidence statuses

`TurnReportV4` is a new closed type, never a relabeled `TurnReportV3`. Its exact
proposed fields are grouped here; nullable means a required nullable key:

| Fields | Types |
| --- | --- |
| `turn`, `arm`, `phase`, `expected` | `String` |
| `scene` | `u8` |
| `construction` | `ArmDescriptorV4` |
| `error` | nullable `Option<String>` |
| `passed`, `roles_known`, `recovered_without_checkpoint`, `construction_matches` | `bool` |
| `failures`, `quality_flags` | `Vec<String>` |
| `roles` | `usize` |
| `admission` | nullable `Option<usize>` |
| `elapsed_ms` | `u64` |
| `first_final_response_ms`, `commit_elapsed_ms` | nullable `Option<u64>` |
| `input_semantic_sha256`, `output_semantic_sha256`, `mechanical_sha256` | `String` |
| `construction_evidence_status` | `ConstructionEvidenceStatusV4` |
| `construction_evidence_reason` | nullable `Option<String>` |
| `narrator_prompt_sha256`, `narrator_schema_sha256`, `scene_frame_sha256`, `actual_receipt_sha256` | nullable `Option<String>` |
| `privacy_evidence_status` | `PrivacyEvidenceStatusV4` |
| `fallback` | nullable `Option<bool>` |
| `repairs` | nullable `Option<u8>` |
| `narration` | nullable `Option<String>` |
| `capture_sha256`, `recording_sha256` | nullable `Option<String>` |
| `raw_sha256` | `Vec<String>` |
| `role_metrics`, `trace` | nullable `Option<serde_json::Value>` |
| `stages` | `Vec<serde_json::Value>` |
| `source_fallback_reason`, `compiler_fallback_reason` | nullable `Option<String>` |

Do not duplicate old optional retrieval metrics as newly verified source facts.
Their actual capture/receipt evidence remains accessible through separately
bounded privileged inspection. Semantic/mechanical digests retain existing
defined meanings, which exclude Play provenance; they do not replace the full
native accepted-history basis or actual receipt binding.

`ConstructionEvidenceStatusV4` has exactly
`ValidatedCommittedSceneNarratorV1`, `NotApplicableGuard`,
`NotApplicableDependency`, and `Unavailable`, with snake_case encodings.
`PrivacyEvidenceStatusV4` has exactly `CheckedFiniteSentinels`,
`NotApplicableGuard`, and `Unavailable`, also snake_case.

`ComparisonReportV4` has exactly `version` (4), `arms`, `kind`, `lane`,
`source_matches`, `completed`, `completed_scenes`, `turns`, `human_reviewed`,
`human_rubric`, `quality_accepted`, `physical_setups`, required nullable
`physical_setup_ms` and `native_load`, `left_charged_ms`, `right_charged_ms`,
`left_reserved_roles`, `right_reserved_roles`, required nullable
`first_semantic_divergence` and `first_mechanical_divergence`, `same_input_pairs`,
`source_bound_committed_rows`, `unavailable`, `profile`, `suite_sha256`,
`source_sha256`, required nullable `reference_sha256`, and `limitations`.
Use the existing corresponding primitive/container types, `TurnReportV4` rows,
V4 descriptors and exact full profile. Lane strings are
`scripted_scene_literal_relevant_comparison` and
`native_scene_literal_relevant_comparison`.

For a fresh committed Domain1 row, obtain actual before/after Engines and receipt
from the existing Host/Store path and call `scene_capture_v1` with expected native
recipe/profile, actual capture attempt and ordered recordings. Only its success
sets the validated status and increments `source_bound_committed_rows`. Its exact
receipt hash must equal the row's actual receipt hash; obtain the validated frame
hash from that same actual receipt. The gate rechecks complete source prefix,
one immediate append, full captured candidate/proposal/approved equality, closed
record tuple, and actual Core stage/bind/render/commit regeneration. Prompt string
and schema Value content plus compact serde hashes must match actual forwarding.

No missing/truncated/expired/disabled capture, failed/cancelled/noncommitted turn,
recovered receipt without its original checkpoint/calls, or Domain2 source may
be labeled validated. Preserve unavailable reasons and unknown call counts;
never infer zero historical work from missing files. Domain2 is outside this
producer's fixed suite and unavailable/unsupported to this evidence gate. Actual
authored-world scene refusal also stays visible; it is not replaced with a fixture.

Expected guards require the existing exact rejection, zero known roles and
unchanged canon, and receive NotApplicableGuard rather than a fabricated narrator
source pass. Dependency-skipped rows remain not executed and cannot satisfy their
expected accepted outcome. A visited row or sealed four-scene run can be complete
while failed or unavailable. `completed` never implies all rows passed.

Fresh evidence contradictions produce a failed/unavailable row with a bounded
gate error, never success. Cold inspection reconstructs actual rows from retained
Store/raw/capture/recording/ledger evidence and rejects checkpoint mismatch;
it does not silently trust or repair a stored status. Source mismatch permits
only explicitly historical reading, never current resume or asset admission.

The narrow gate establishes narrator input-source consistency, **not** actual
provider execution, raw-output origin/causality, Director source reconstruction,
memory compiler/cache execution, semantic privacy or prose quality. Director
prompt and schema content receive envelope/identity/role-budget/schema-ID/hash/
order checks only. Counts and selected-context claims are not cache proofs.
`details.exact_reconstruction=false` remains untouched. Both new arms may have
identical narrator bytes when actual proposal/frame/presentation agree;
cross-arm refusal concerns native recipe/receipt/context binding, not an invented
arm-specific narrator tag.

Privacy status is CheckedFiniteSentinels only when the existing actual recorded
prompt/output checks and relevant retained evidence are available and pass.
Missing evidence remains Unavailable, not a vacuous privacy pass. This finite
check is never universal semantic privacy proof. Narrator leakage, scenario
failure, source failure, provider/parse failure and fallback stay distinguishable.
Fallback does not claim accepted generated prose. `human_reviewed=0`,
`human_rubric="not_reviewed"` and `quality_accepted=false` initially, with no
invented quality threshold, score or automatic improvement claim.

## Existing owners, budgets and immutable source identities

Reuse `comparison/turn_execution::{execute, load_evidence, recover_actual,
assess_outcome}` and `ActualTurn::checkpoint_and_settle`. These own real
Host/Store/provider calls, diagnostic consent/revocation, watchdog, actual receipt
lookup and checkpoint-before-settlement. Reuse `native_startup`,
`SelectedNativeReservation`, `native_owner` and the existing native workflow
ownership/drain rules. Do not copy Engine, source compiler, memory compiler,
Director recipe, provider/runtime, model manager or persistence implementations.

Both durable invocation reservations precede asset open/load. Keep exclusive
runtime ownership, cancellation, panic containment, bounded drain and retained
uncertain ownership. No success publication, refund or replacement owner is
allowed while cleanup is uncertain. Completed current-source resume returns
before loading/reserving native assets. Unknown work keeps its existing
conservative reservation. Tests must retain cleanup/accounting evidence.

The exact existing per-arm caps are 32 admissions, 96 reserved roles and
1,800,000ms active time. Keep the 60,000ms turn watchdog, 120,000ms preparation
reservation and 3,000ms cleanup reserve. The existing runtime cancellation/drain
deadline remains 2,000ms. Role output caps remain 350 tokens/16,384 visible bytes,
context 4096, maximum one Director repair, profile deadline 120,000ms, and existing
whole-turn accounting. The watchdog and profile deadline are distinct existing
limits; do not enlarge either to make a run pass. Raw/capture/report/file caps,
source/destination pins, locks and ordinary-path refusal remain unchanged.

Native assets must be the already installed, approved profile and worker only.
No downloads, new weights/backend, copying weights, retuning, altered template or
larger context/profile is part of this proposal. The inspected source pins are:

| Identity | Existing expected value |
| --- | --- |
| Profile | `qwen3-0.6b-q8-cpu-v1` |
| Qualification label | `experimental_windows_x64_cpu_lifecycle_only` |
| Runtime | llama.cpp `620d2225cc436ab0b001e3200e590e3b286ef9ab` |
| Model | `Qwen/Qwen3-0.6B-GGUF`, revision `23749fefcc72300e3a2ad315e1317431b06b590a` |
| Artifact | `Qwen3-0.6B-Q8_0.gguf`, 639446688B |
| Model SHA256 | `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031` |
| Worker SHA256 | `b5dd124e484c67c9dda5aebb2cdff1878ccefd0fba99aba4788e00a166f68434` |
| Template SHA256 | `57f1fd00f0013a2be96aa79b857391f27e23df5b5f847072b524c897e24d0361` |
| Sampling | seed 42, temperature 0.7, top_p 0.8, top_k 20, min_p 0, presence_penalty 1.5 |
| CPU | threads 4, GPU layers 0, batch 512, ubatch 512; thinking/tools false |

These are source-derived expected identities, not a fresh installed-file check.
The existing native admission must verify actual installed worker/model/profile
before use and refuse missing/mismatching assets. `PlayProfile` also binds the
profile manifest hash of its compact JSON content. Do not guess a hash of the
future Protocol4 build: freeze its actual full SOURCE_INPUTS map/build identities
before execution. Eval's existing build script recursively includes new src
modules plus shared Core/Host/Store/workspace sources, locks and native
runtime/profile sources. Any actual run records those exact current bindings.

## Frozen scenarios and first bounded model cohort

Reuse `memory_comparison::frozen_suite()` verbatim: 24 original steps in four
scenes, 21 expected accepted commands and 3 expected guards per arm. Existing
request text, seed/rules, expected commands/guards, sentinel exclusions and
reference outcomes remain immutable. Do not alter grammar, scenarios or expected
outcomes to obtain favorable model output. The existing per-step assessment
checks actual canonical receipt/effects; a model judge cannot waive a hard failure.

The proposed first real-model cohort is **one paired run of all four scenes**,
one scheduled attempt per row in each fixed arm, under the caps above. This is
24 planned attempts per arm, 48 total, not a promise that all generate or commit.
Alternate first arm using the existing index-based paired rule. Use validated
identical original reference prefixes rather than each arm's generated history;
report that limitation rather than calling paired rows a continuous generated
session. Continuous rollout remains a separately labeled supported scripted
oracle and a separately authorized later model workload.

Predeclare this reading packet before any model execution. Source inspection
verified all four actual IDs from the existing rows and `courier-{:02}` indexing:

| Turn | Zero-based index | Existing player text | Existing expected outcome |
| --- | --- | --- | --- |
| `courier-01` | 0 | The pennant I carry has an amber stitch. | Say exact text to Mira |
| `courier-05` | 4 | I move to pier. | Move to pier |
| `courier-12` | 11 | I wait for one tide tick. | Wait one tick |
| `courier-22` | 21 | I give pennant to oren. | Give one pennant to Oren |

Include both arms for eight planned samples. These are a new predeclared packet,
not a claim to match every sample in the original human-reviewed packet. If a
selected turn fails, skips, cancels or falls back, retain that outcome in its slot;
do not replace it with a successful sample. Retain every attempt, raw bounded
output, failure, fallback, role measurement, capture and cancellation/drain result
privately. No favorable rerun/resampling or silent threshold change is authorized.
Infrastructure refusal may prevent the cohort; preserve it with its source and
cause rather than restarting without a separately reviewed correction.

Generated samples need a new human assessment of scene consistency, agency,
repetition and readability. Keep the original eight-sample needs-improvement
assessment immutable and do not invent case-specific ratings. The new packet's
automated flags or absence of flags do not confer human approval or superiority.

## First independent oracles and later application gate

Root reviews this proposal's field/API seams before allocating tests. Freeze
independent public producer/native-owner oracles before production, including:

- Exact descriptors/nullable keys and refusal of cross-arm/old-version relabels;
  unchanged Protocol3/selected2 regression behavior and retained bytes.
- Actual scripted paired and rollout 24-step outcomes, unchanged 21/3 expectation,
  alternating order and full native prefix/receipt/tuple binding through the
  new gate; rehashed narrator forgeries and explicit Director/output limits.
- Actual Host consent/capture, missing/noncommitted/recovered/D2 statuses,
  sentinel evidence availability, fallback and unknown-role accounting.
- Strict reopen/inspection reconstructing checkpoints from actual Store and
  evidence; source/profile/reference drift refusal before native admission.
- Cancellation, interrupted checkpoint/commit, completed no-load resume,
  known/uncertain owner drain and publication/settlement rules, with existing
  resource caps and no speculative cleanup.

Actual desktop integration is a separate versioned branch of the established
comparison controller/native IPC and read capabilities. Existing
`comparison_run` binds Protocol3; existing selected source3 maps to selected2.
Do not change those historical mappings or admit Protocol4 as their default.
Bind new prepared metadata to exact Protocol4 arms/source/profile/caps before
existing closed native consent; JSON/report metadata never grants execution.

Use application-owned programmatic harnesses for prepare/start/pending/cancel,
completion, stale-context refusal, restart/reopen, actual receipt/trace inspection
and Player/NPC/Story Lab isolation. Keep privileged raw diagnostics out of actor
views; inspection grants do not change actor knowledge or generation context.
No desktop control, injected input or system screenshots are needed. Label
frontend/headless, native IPC, actual WebView rendering, Core/Store and model
evidence separately; a successful producer run does not qualify the UI journey.

No implementation, selected rerun, model cohort, quality acceptance, Android
parity, physical-phone/offline qualification, merge or release is authorized by
this source-only proposal itself. Subsequent claims and evidence belong on the
owning tickets with exact source/results and the remaining limitations.
