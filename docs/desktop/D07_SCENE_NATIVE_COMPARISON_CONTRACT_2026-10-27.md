# Protocol 4 native comparison: next bounded integration contract

2026-10-27. D07.03/.05 supporting D04.04 (#29/#25).
Source inspected: `6a38af111b8f4f3b99054cf03a7f18dd5edcb068`.
**PROPOSED / SOURCE ONLY / UNRUN.** This document does not implement or launch
a comparison, import/read a model, open a runtime or qualify SDK/model success.
It allocates the next focused integration and independent freezes. Root owns
interface acceptance, production, approved asset staging, serialized execution
and any subsequent bounded model cohort. No download/upgrade or other owner's
asset/target/workspace is authorized here. Claim #29 comment6454819303.

## Actual source findings

The Core entry `scene_v4::run_native_comparison<R: SelectedNativeReservation>`
already exists in `crates/locallore-eval/src/local_lane/comparison/scene_v4/native.rs`.
It uses the existing reservation/startup, both-arm ledgers, Host/Store pipeline,
watchdog, `native_owner::finish_owner`, checkpoint/settlement and uncertain-owner
return type. Protocol4 CLI execution is absent. Its Core reader is separate from
execution; selected source4 execution remains unavailable.

Desktop `evaluation/comparison_run.rs` is fixed to V3 at `Index.binding`,
`Record.index`, `PreparedWork::Inspected`, `FullOutcome.result`, manifest/index
validation, current-binding comparison, dispatch and status/catalog metadata.
`comparison_run/native.rs::full_work` calls `literal_v3::run_native_comparison`
and constructs protocol3 consent metadata. Merely changing a report/version
field would combine incompatible sources and is not an implementation.

`comparison_native_commands.rs` is the existing closed native transport;
`comparison_run_native_harness.rs::consent` currently accepts protocol3 only.
`ui/comparison-run-model.ts` fixes native status/catalog to version2/protocol3;
`comparison-run-controller.ts` has one existing native transport and ownership
fences. The first V4 run must extend these exact owners rather than fork them.

Historical public evidence is in
`D07_NATIVE_FULL_COMPARISON_CONSUMER_QUALIFICATION_2026-10-26.md` and its service/
UI-harness contracts. The earlier actual 0.6B Protocol3 cohort retained 48 rows,
78 known roles, two physical setups, 36 committed/12 failed phases and 41 expected
scenario passes; these are different metrics, not a V4 baseline prediction.
The unsupported forest narration at `courier-01/right` was accepted by the finite
old validator; its cause was unknown. The owner reviewed the eight actual
synthetic samples as **needs improvement**, not per-case scores or merge approval.
No historical output, SDK success, native-load result or human acceptance is
inherited by this proposed source. Raw samples remain private.

## Smallest first slice and typed signatures

Keep normal scripted and native run defaults on Protocol3. The first V4 entry
is a closed **development harness** path over the same native command/controller,
not a new CLI, arbitrary worker/provider, renderer recipe or external service.
Introduce a native-code enum with no Serde or renderer construction:

```rust
pub(crate) enum FullComparisonProtocol { LiteralV3, SceneV4 }
```

Existing public `full_comparison_*_native` methods retain signatures and delegate
to LiteralV3. Add crate-only typed counterparts in the same manager, including:

```rust
pub(crate) fn full_comparison_start_native_for(
    self: &Arc<Self>, lease: &Arc<WindowLease>, models: &Arc<ModelManager>,
    epoch: u64, granted: bool, protocol: FullComparisonProtocol,
    input: FullComparisonStart,
    consent: impl FnOnce(&Value)->Result<bool,String> + Send + 'static,
) -> Result<Value,String>;
pub(crate) fn full_comparison_resume_native_for(
    self: &Arc<Self>, lease: &Arc<WindowLease>, models: &Arc<ModelManager>,
    epoch: u64, granted: bool, protocol: FullComparisonProtocol,
    input: FullComparisonNativeResume,
    consent: impl FnOnce(&Value)->Result<bool,String> + Send + 'static,
) -> Result<Value,String>;
```

Apply the same typed protocol argument to internal catalog/lookup/open/status/
cancel/close/managed-read dispatch. No new renderer field changes the existing
`FullComparisonStart` or resume inputs. Root may mechanically consolidate private
helpers, but the default wrappers, token fences and legacy wire bytes must stay
unchanged. No new general engine, report importer, runtime owner or persistence.

Use private typed unions for index/binding and report results, with V3 and V4
variants holding the actual existing Rust types. Do not erase V4 into
`ComparisonReportV3`, invent retrieval fields, deserialize accepted receipts or
reconstruct an Engine from report JSON. Shared status reads only common completed
scene/completed/source-match fields after typed dispatch. Native failure payload
and its retained actual owner remain the existing `SelectedNativeFailure` path.

## One index namespace, exact version closure

Keep `comparison-evaluations/<native UUID>/desktop.json`, `work/` and paired-only
`reference-source/`. Preserve IndexV1 scripted3 and IndexV2 native3 exactly.
Propose new private `SceneNativeIndexV1` in that same index namespace with exactly
the existing keys, changing only this closed tuple and typed binding:

```text
version:3, protocol_version:4, input_lane:"approved_native",
run_id, client_id, kind, initial_batch:1..4, created_ms,
binding: memory_comparison_v4::CurrentBindingV4 with native:true
```

These proposed names/version3 are unreserved in the inspected run broker.
Unknown index keys/versions or mixed tuples refuse. Parse the outer exact known
version first into the correct closed type, validate all descriptors/budgets and
actual manifest equality, then apply protocol/lane filtering. A version number
alone is not validation. V4 binding keeps exact literal2.10 and memory2.9 scene
arms, grounded-prose2.4, schema/frame/capture-gate/forwarded-budget versions and
required nullable arm fields. Source/suite hashes may be well-formed historical
metadata during read only; execution requires exact current typed binding.

Both old and new catalogs must tolerate a valid retained opposite-protocol index
without relabelling it, while retaining global malformed-index refusal. Count
at most32 total runs and enforce unique client IDs across lanes/protocols, not
32 per selector. A same-client start retry must match protocol, lane, kind and
initial batch; cross-protocol reuse cannot create a duplicate or return an old
report as V4. Every token/lookup/managed entry is fenced by protocol **and** lane,
window/epoch/client identity. Existing valid2/3 errors/bytes/defaults stay intact.

V4 native catalog/status use closed envelope version3/protocol4 with the same
native keys as version2/protocol3. Native input lane stays approved_native;
cleanup/cause/source-match nullability stays exact. The V4 catalog returns only
V4 metadata and the V3 catalog only V3. Ordinary read-only Reader source4 is the
already qualified Core/manager path, not an execution grant.

## Actual dispatch, consent and ownership

`full_prepare_work` must dispatch actual V4 inspector/current binding. Historical
Open may show source_matches false; Start/Resume refuse drift before consent,
reference creation, new reservations or generation. Completed current-source
Resume returns an actual strict inspected V4 report **before** the consent/
reservation closure, reference preparation and model assets. Preserve the
distinction between cached status, fresh read and a new run.

Native `full_work` dispatches the existing seven-argument V3/V4 Core runner with
the same ModelManager-backed reservation closure; there is one existing JobKind
ComparisonRun, SelectedOwnership, worker, registration/cancellation slot and
cleanup witness. Consent metadata retains version1/full_comparison_execution
and names protocol4, exact run/client/kind/batch and original caps. Recheck lease,
operation and cancellation before and after consent, then `reserve_owned`.
Catch panic only at the existing pre-owner consent boundary, never wrap an
unknown post-owner runtime and claim cleanup. No execution reservation or runtime
asset acquisition before accepted execution consent. Reuse existing approved
weight publication without import/copy; separately approved worker-only staging
remains outside that job.
Bounded index/reference/work-manifest/empty-ledger files may already exist before
consent; denial does not imply a zero-file run. It must not admit a turn, load a
model, acquire a runtime or fabricate a checked source/privacy result.

Core retains both invocation reservations before native_startup assets, drains
the actual factory/Host before finish_owner and accounts cleanup time in live
clocks. Unknown cleanup retains the exact actual reservation/runtime pair in
the existing Job, blocks fresh admission/report-ready, and uses existing generic
cleanup status/retry. `running:false`, closed UI, elapsed time or captured output
is not cleanup proof. Cancel/close/retirement do not remove an active owner;
source/result publication remains fenced and uncertain work cannot be refunded.

Keep existing limits unchanged:32 admissions/96 roles/1,800,000ms per arm,
60,000ms turn watchdog,120,000ms preparation,3,000ms cleanup reserve and existing
2,000ms runtime cancellation/drain deadline. Fixed profile is CPU4,context4096,
Director/Narrator350 tokens, repair1,deadline120,000ms;16,384-byte role output.
Use existing32 MiB run/256 MiB library/64 MiB free-space boundaries, native path
pins and all shared capture/report/input caps. Limits are not measurements.

## Closed harness and approved assets

Extend existing `comparison-run-harness.mjs` with exactly one new mode
`--native-scene-v1`; noargs scripted3 and `--native` native3 stay unchanged.
Set existing D02/full/native flags plus fixed
`LOCALLORE_D07_SCENE_NATIVE_FULL_HARNESS=1`; old modes set/clear it to0. Existing
native command query keys remain unchanged. Only the checked active development
fixture selects typed SceneV4 internally. Normal command paths remain LiteralV3.
No raw protocol/recipe/policy/worker/model/asset/directory request key is added.

Keep the native-derived fresh UUID workspace and owned ancestor pins;
reuse the existing `full-comparison-native-<UUID>/stories-v1.sqlite` fixture shape,
the already published approved model root and `stage-runtime.mjs` for the worker
only. No new model root, import, weight copy, hard link or symlink is part of this
cohort. Never call ordinary model_import/model_load; the comparison reservation
starts its isolated owner using the existing read-only verified asset path.
Approved installed assets are the existing Qwen3-0.6B-Q8_0 model,639446688 bytes,
SHA256 `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`,
and worker SHA256 `b5dd124e484c67c9dda5aebb2cdff1878ccefd0fba99aba4788e00a166f68434`.
Those public constants were read from source; no asset availability/content was
probed in this contract. Root must identify and verify a previously published,
owned approved model directory before any run. Missing/changed assets or unknown
publication ownership block the cohort; no download/upgrade/import/copy fallback.

### Correction before generation: prior freeze controls slots and no-copy reuse

The earlier `D07_SCENE_COMPARISON_PROTOCOL4_CONTRACT_2026-10-27.md` is authoritative
for the existing no-copy constraint and predeclared eight review slots. The
initial integration proposal `3e18bd94` mistakenly proposed fresh-import semantics
and different slots. This source-only correction preserves the prior
`courier-01/05/12/22` both-arm selection and no-copy rule before any new model
generation. It grants no new execution or asset access and changes no producer,
scenario, expected outcome, immutable report or original human packet.

Exact existing reuse seam: `model-harness.mjs` maps launcher-only
`LOCALLORE_D04_REUSE_MODEL_ROOT` to native `LOCALLORE_D04_MODEL_ROOT`.
`main.rs` uses that root only under the D04 development gate; its later
`comparison_run_native_harness::model_root` override currently always selects
fresh `parent/model-native-v1`. Setting the old reuse variable alone therefore
does **not** make the current full-native harness reuse publication. The old D04
reuse journey is a source precedent, not an already working SceneV4 adapter.

Proposed focused adapter: in `--native-scene-v1` only, the trusted launcher
requires the existing reuse-root input, validates its ownership/ordinary pinned
path, and supplies `LOCALLORE_D04_MODEL_ROOT`; the checked scene branch of
`comparison_run_native_harness::model_root(&workspace)` returns that existing
absolute directory instead of computing a new model root. Do not enable the D04
Play harness flag to bypass the override. Legacy `--native` keeps its old path.
The expected child basename is exactly `Qwen3-0.6B-Q8_0.gguf`; the launcher may
read/hash that already approved file during Root's separately allocated
preflight, with no copying or rewriting it. Root must resolve the publication
from its own retained staging/ownership records, independently of renderer JSON,
and exclude other-owner/protected resources and the original review packet.
The public source documents omit a current usable absolute publication path;
none is inferred or probed here. A missing suitable publication is a real
availability/ownership blocker, not permission to copy the source weights.

`ModelManager::new(root, resource)` performs no filesystem work. Its fixed
`path()` appends the approved basename; `reserve_evaluation()` only obtains the
existing in-memory ownership slot and carries that model path plus the current
packaged worker resource path. `EvaluationReservation::assets()` borrows those
paths. Existing `native_startup::start_runtime` and
`LocalRuntime::spawn_packaged_owned_expected_cancelled` perform approved
`verified_model`/`verified_worker` read-only opening/hash checks and retain the
actual pins on success and uncertain-owner paths. Reuse that owner without a new
loader/publication/index. The constructor or imported=true status alone does not
verify file bytes or runtime availability.

Required mutation guard: both `ModelManager::import` and ordinary `load` call
`reap_imports(&self.root)` before picking/loading. Even a cancelled picker can
therefore alter existing staging files. In active SceneV4 reuse mode,
`model_commands::{model_import,model_load}` must refuse before entering either
manager method; `approved_model_source` must not offer a source/copy fallback.
The scene journey skips import/load entirely and checks actual model status;
normal commands and old modes remain unchanged. Existing comparison cleanup
status/retry and ModelManager reservation release remain available for the exact
owned runtime. Do not call reaping/import/cleanup on the publication directory,
retarget a live manager, or modify the original human-review packet. Record
existing publication file size/hash/last-write identity before/after the future
cohort without claiming all OS metadata or another process's activity is frozen.

Independent first oracles must freeze reuse-root precedence, missing/foreign/
malformed root refusal, no new model directory/import/link, and import/load
refusal **before** a synthetic existing `.import-<UUID>.part` sentinel can be
reaped. Test path plumbing with synthetic ordinary fixtures only; their tiny
files cannot pass approved-model validation or become SDK evidence. Actual
approved publication verification/load remains Root's separate model gate.

Add strict V4 native status/catalog types/decoders in `comparison-run-model.ts`
and a fixed development-only options branch in the existing controller; this
selects matching wire decoding, not native authority. Extend the same run view,
native journeys and managed Reader4 entry. Preserve all V3 controllers/defaults,
unknown-outcome same-client recovery and cleanup/lens/context fences. Update the
existing consent double to accept protocol4 only in the active scene gate.
Use existing deny/hold/lost-ACK/read-consent controls and strict failure abort
helper; unknown denial ACK never releases held consent.

## Independent first freezes and actual cohort gate

Do not implement against an untested speculative API: first independent freezes
must cover the typed service/index seam, closed command/decoder/controller seam,
then app-owned journey. Metadata-only native wrappers remain labelled metadata;
never relabel scripted checkpoints/reports as actual native success. Meaningful
initial cases include valid3 controls plus valid4 wrapper/catalog/denied-consent,
wrong nested tuple/budget/schema/frame/native flag/protocol and matching corrupt
outer+inner metadata, cross-protocol tokens/client retry, run-cap and quota
checks, stale source, consent panic/cancel/retirement before assets, unknown ACK,
same actual owner cleanup and managed read independent consent. Existing fixed
test-process owners may test protocol/cleanup plumbing only, not approved SDK.

Completed **native4** no-load/cold-reopen proof needs an actual native4 retained
cohort; do not fake its NativeProfile on scripted output. Before/after full
inventories and unchanged setup/admission/roles do establish no new durable work.
For a stronger no-reservation observation, independently freeze a narrowly gated
read-only observation of ModelManager's existing evaluation sequence plus native
consent invocation count. No arbitrary introspection/write command or alternate
counter/owner is needed. Unchanged sequence while the real owner is free and
consent count0, together with the source branch before reserve, support the
bounded no-load claim. Without that observation, state the instrumentation gap;
inventory/time alone do not independently count asset/load calls.

After Root's separate execution gate, use one approved paired cohort: batch1 then
explicit resume3,24 scheduled attempts per arm/48 rows total, not48 per arm.
At most the unchanged caps apply; admissions/roles/commits/failures/fallbacks and
physical setups are measured, never assumed42 successes/two loads. Retain partial
report before resume and completed report privately with hashes; cold restart
inspects/completed-resumes the same source without new generation. Domain2,
missing/recovered/failed evidence remains honestly unavailable, while observed
privacy violations retain their distinct cause. The scene gate checks fresh D1
committed Narrator inputs, not Director/raw-output/provider/cache authenticity.

Retain the earlier frozen eight review slots **before generation**:
literal/relevant rows for `courier-01`, `courier-05`, `courier-12`, `courier-22`.
These are Say, Move, Wait and Give in the unchanged frozen suite; do not replace
them with one first row per scene. Retain failed/unavailable slots instead of substituting
better prose or rerunning. Present actual generated text and phase/receipt/source
status, finite scene/agency/repetition/readability questions and honest fallback
labels; no synthetic scores or model-judge waiver. The new human declaration is
separate from immutable reports; original needs improvement remains recorded.

Capture source/lock/model/template/worker/runtime identities, sampling/profile,
actual load/setup and whole-turn/role/repair/commit/first-final latency evidence,
bounded traces/errors and explicit unknowns. Same input/reference is shown per
pair; differing channels are part of the experiment. Render via the same actual
frontend actions/controller/IPC in an owned hidden unfocused WebView; semantic
snapshots and bounded CapturePreview images only, every image inspected. No
desktop input/activation/images. Distinguish Rust, mocked/headless, native IPC,
WebView, actual model and human evidence. Existing app/launcher watchdogs remain
2,100/2,160 seconds; one heavy model process, no repeats to chase better results.

Root allocates broker/index/native dispatch first, independent transport/UI
second, existing harness/staging/journey/packet integration third. This commit
owns this document only; no future API/module is registered. All tests,
compilation/formatting/builds/native/model/human checks remain UNRUN here.
No merge/release/settings change or overall D07/phone/offline/security/quality
acceptance is implied by the design or a future synthetic pass.

## Source implementation handoff (uncompiled/unrun)

The subsequent Rust-only implementation uses the agreed crate-only
`*_native_for` methods with protocol immediately after granted. Their LiteralV3
branches call the existing public native wrappers; SceneV4 shares the same
private worker/lifecycle through `ComparisonLane::SceneNative`. Existing
`NativeExecution` fields and old admission fixtures stay unchanged.

New private `comparison_run/versioned.rs` holds exact typed IndexWire V3/V4
variants (Serialize only for the internal union; explicit version/tuple decode
into each closed type), actual binding shape/current checks and actual report
dispatch. The existing broker validates every recognized index before filtering
and uses the existing global run/client namespace, byte/free-space caps and
protocol-specific lane/token fences. New `native_for.rs` is thin method
delegation, not another index/owner. The existing native worker retains the exact
owner payload and dispatches the chosen actual Core runner after the same
pre-owner consent/reservation closure. Open/complete-resume use typed inspection.

`comparison_native_commands.rs` selects LiteralV3 normally and only accepts
SceneV4 from the checked development environment, without new action/query keys.
`comparison_run_native_harness.rs` requires the old fixed workspace/flags and
the scene flag1, forbids D04 Play-harness overlap, and takes the existing
launcher-only model-root override with local-disk/ordinary ancestor checks.
It creates no model directory, imports/copies no weights and offers no fallback.
`model_commands` refuses import/load before manager calls in any scene request,
including inconsistent flags. These native path checks do not establish Root's
publication ownership or perpetual file immutability; the separately recorded
Root preflight and actual Runtime pin/hash verification remain required.

The only `models.rs` addition is Root-approved `#[cfg(test)]`
`evaluation_sequence_for_tests()`, reading the existing counter under lock.
There is no new counter, mutation, runtime fixture or renderer inspection API.
No existing test/assertion, UI, launcher, Cargo feature, Core provider/Store or
selected-source4 execution adapter is changed. The independent service freeze
is separately authored; Root owns its registration/integration and every first
compile, source calibration, formatter, test, lint, native/model run and review.
Author checks source/API/callsite/Git/whitespace only. This handoff does not claim
that the new Rust compiles or that a native4 run, cleanup or completed no-load
resume has executed. Frontend/harness integration and model/publication gates
are explicitly separate work, not inferred from the source implementation.

## Additive full-run lease identity freeze

On source3c1f1146, a new child
`comparison_run/scene_native_review/lease_identity_review.rs` freezes four
additional oracles, source-only UNCOMPILED/UNRUN. Root owns child registration,
baseline execution and the production identity correction. Existing eleven
service assertions are unchanged. Metadata fixtures contain no canonical native
receipt/report, work prefix, provider, model or completed-generation claim.

Three independent per-mode tests cover scripted3/index1, native3/index2 and
native4/index3. Existing authorized lookup of the same run from distinct live
Arc<WindowLease> values with equal epochs must create distinct tokens. Browsing
again in one lease reuses only its own token. Both rightful capabilities remain
usable; reciprocal stolen-token status/cancel/resume/close must fail UnknownRun
before job/consent/assets. Closing one token must leave the other valid; explicit
fresh lookup remints a new proper handle. Files/synthetic assets and the existing
ModelManager reservation sequence remain unchanged/zero.

The fourth finite test admits four same-run/different-lease handles, ages only
the first existing private token's touched timestamp by one second, then requires
the unchanged four-token LRU cap on a fifth authorized owner. Only the oldest
handle expires; the remaining rightful handles keep their identities and the
fifth owner cannot use them. No sleep, TTL/budget increase, owner counter or
production API injection is added. This tests handle identity/cap preservation,
not arbitrary concurrent-window retirement or runtime cleanup correctness.

Existing actual diagnostics separately locate the preexisting full-run identity
gap at foreign WindowLease status with the same epoch; preceding protocol
refusals passed. That observed failure is not reattributed to cross-protocol
dispatch. The inventory/consumed-reader failures are separate fixture setup;
their calibration cannot count as a product fix or erase the original log.
These four new oracles themselves remain unexecuted at this freeze. Root's
proposed stable private Arc/Weak lease identity and owner-scoped reuse must bind
both full-run mint sites before lookup/status/cancel/resume/close can rely on it.
Never overwrite an old token's owner because generic same-run mint reused it.
