# D04 desktop profile prerequisite investigation

Refs #25 (D04.01 investigation, D04.02–D04.04 design); shared prerequisites #9.
Base inspected: accepted main `bc6420030b500e7dd0cea5d59ec2f5d2e7e798e6`.
Claim: [#25 comment6356208682](https://github.com/OptimumAF/LocalLore/issues/25#issuecomment-6356208682).
This is a source/artifact feasibility report, not a supported-profile decision,
new production implementation, new model run or D04 acceptance evidence.

## Decision available to the implementation owner

The smallest justified first desktop integration candidate is a **managed native
llama.cpp CPU worker using the already provisioned official Qwen3-0.6B Q8_0**.
Keep the exact existing pin and workload for a comparable experimental profile.
Do not ship the Python benchmark launcher or silently substitute a larger model.
The tiny model has demonstrated structured transport compatibility; its story
quality has not been accepted. A supported-quality claim requires actual D04.06
journeys and the declared evaluation, including severe failures and repairs.

The existing LiteRT/Gemma path is a measured alternative, not a second proposed
production integration. It needs a Python/native distribution and vendor notice
review beyond the existing experiment. The original Qwen3.5-4B conversion/load
is still pending. No additional model is needed to begin the shared lifecycle
and pipeline work. A larger desktop-quality profile requires separate evidence.
Neither choice closes the physical-phone gates in #5/#9.

## Current evidence and actual local inventory

Read AGENTS.md, README.md, ISSUE_WORKFLOW.md, #3, current #25/#9/#5 bodies and
claims, ADR-0006, host-v1, model evaluation plan, accepted spike source and its
verification/review evidence. #9 had no active claim at inspection; #5 records
accepted #40/#41 Android experiment follow-ups with physical qualification open.
No production runtime/model was selected by those experiment merges.

The following existing files were read and hashed on this investigation. Personal
absolute cache paths are deliberately omitted. No weight was copied, downloaded,
loaded, altered or executed; no emulator, ADB or desktop control was used.

| Local asset | Bytes | SHA-256 |
|---|---:|---|
| Official Qwen3-0.6B Q8_0 GGUF | 639446688 | `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031` |
| Existing Gemma4 E2B LiteRT bundle | 2588147712 | `181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c` |
| Existing Windows llama experiment helper | 6009856 | `7711f91d068445af24ed0edac18ef9995b09131a7ae8bc51514502fa322b7908` |

The helper hash matches the accepted report. Its local upstream source checkout
is clean at `620d2225cc436ab0b001e3200e590e3b286ef9ab` (v0.7.0).
This establishes available local bytes, not trust in arbitrary user executables
or byte-reproducible compilation. A production worker will be a different build
and must have its own build/provenance record.

The metadata-only command
`python benchmarks/spike/llama/inspect_model.py <existing-qwen-gguf>` passed:
GGUF v3; architecture `qwen3`; 28 layers; width1024; 310 tensors, 113 F32 and197
Q8_0; file type7 and quantization version2. Tokenizer is `gpt2`/`qwen2`, vocabulary
151936, BOS/padding151643, EOS151645, add-BOS false. Actual embedded template is
4100 UTF-8 bytes, SHA-256
`57f1fd00f0013a2be96aa79b857391f27e23df5b5f847072b524c897e24d0361`.
Its context metadata is40960; that does not expand the experimental4096 cap.
The template differs from the current base-tokenizer template; use the actual
GGUF template, never a guessed replacement. Metadata inspection did not load
tensors into an inference runtime or emit the template/weight bytes.

Historical actual calls are retained in
[host results](../runtime/spike/HOST_RESULTS_2026-10-22.json): eight requests,
ten attempted roles, four committed fixture requests, two cancellations and two
mechanical preflight rejections across both candidates. Each role used a fresh
model process. The llama gift director/narrator used459/64 input and89/9 output
tokens in one retained run; its generation scopes were3732.9381/468.4165ms,
and load/setup377.6581/386.438ms. These are historical individual host samples
with uncontrolled OS cache, not a new measurement, sustained result, model
ranking, free-text prose result or full app latency. The nine-token narrator
matched exact engine prose. It is especially weak evidence for story quality.

## Pins and licensing

| Component | Exact pin and evidence |
|---|---|
| llama.cpp | v0.7.0 / `620d2225cc436ab0b001e3200e590e3b286ef9ab`; MIT |
| Qwen publisher | `Qwen/Qwen3-0.6B-GGUF`, revision `23749fefcc72300e3a2ad315e1317431b06b590a`, `Qwen3-0.6B-Q8_0.gguf`; Apache-2.0 |
| Existing comparison | LiteRT-LM0.18.1 / `bda624851d74be34d4e1f7fac1fc4155939539c7`; Gemma bundle revision `a790a852d433991c0c0a41c1154cf9b3850300fa` |

Official primary sources rechecked for this report:
[pinned native API](https://raw.githubusercontent.com/ggml-org/llama.cpp/620d2225cc436ab0b001e3200e590e3b286ef9ab/include/llama.h),
[MIT license](https://raw.githubusercontent.com/ggml-org/llama.cpp/620d2225cc436ab0b001e3200e590e3b286ef9ab/LICENSE),
[schema converter](https://raw.githubusercontent.com/ggml-org/llama.cpp/620d2225cc436ab0b001e3200e590e3b286ef9ab/common/json-schema-to-grammar.h),
[official model card](https://huggingface.co/Qwen/Qwen3-0.6B-GGUF/blob/23749fefcc72300e3a2ad315e1317431b06b590a/README.md),
[exact model license](https://huggingface.co/Qwen/Qwen3-0.6B-GGUF/blob/23749fefcc72300e3a2ad315e1317431b06b590a/LICENSE).
The license raw URL was inaccessible through the web-reader service; a direct
read-only HTTPS GET returned11544 UTF-8 bytes with SHA-256
`5de36594c10839788a8c589443a8ef9d8b8d17c65a1b5807206ae037fc36c6bd`, matching
the accepted source manifest. Apache2.0 was present in those actual bytes.
Do not infer licensing of every dependency from the top-level license. Preserve
upstream runtime/vendor notices, attribution for adapted example code and the
model license in any eventual redistribution. This proposal bundles no weights.
No claim is made that this pin remains the latest release.

## Existing worker protocol and its gaps

`benchmarks/spike/llama/run.py` accepts exactly one request then exits. Request v1
fields are `version`, `role` (`director`/`narrator`), `prompt`, `max_tokens`
(1–350), `context_tokens`4096, `threads`4, `schema`object/null. Input cap32768
bytes; final visible text cap16384; each native pipe cap65536; outer native
deadline55s. Response fields are version/status/text/error/load_ms/generation_ms/
output_tokens/input_tokens/schema_enforced/thinking_disabled/template_applied.
The Python boundary rejects duplicates, nonfinite numbers, wrong fields/types,
invalid UTF-8, incorrect model bytes and mismatched exit/status. Neither a path
nor executable name is supplied by model text.

The C++ helper loads model/context/template/sampler per invocation. CPU only,
four threads, context4096, batch/ubatch512, GPU layers0, KQV/op offload false;
seed42, temp0.7, top-p0.8, top-k20, min-p0, presence1.5. It uses actual embedded
Jinja template, disables thinking/preserved reasoning/tools, tokenizes user
parts without interpreting role-control tokens, and installs the official
JSON-schema grammar converter explicitly. Input tokens plus reserved output
must fit4096. It discards parsed reasoning/tool output. A seed does not promise
cross-hardware generation reproducibility.

Cancellation today is parent termination/reaping. The helper has no cancel
reader, native abort callback, persistent loaded model or idle status protocol.
It also reads request stdin to EOF, so it cannot simply be kept open and reused.
Its native parser does not enforce all Python duplicate-key protections itself.
It has no complete-turn timing/memory accounting. Existing build disables
server/app/UI/subprocess/TLS/GPU/RPC/dynamic-backend integrations, but upstream
`common` still compiles an HTTP utility; it is not an OS network sandbox.

The pinned native header supplies a model-load progress callback (false aborts
load) and context decode abort callback (true aborts CPU decode), plus context
synchronization. This is source capability, not tested cooperation in the
current helper. Keep initial production candidate explicitly CPU; do not claim
GPU abort support or silently fall back from GPU. Full selected-backend recovery
and cancellation must be tested with actual model runs.

## Smallest integration design for implementation

Use one app-owned native helper executable built from reviewed source and a
Rust owner over private inherited pipes. No Python runtime, socket listener,
arbitrary executable picker, shell, model tools or frontend-supplied prompts.
The native owner chooses the packaged worker; the model picker chooses only
candidate weight bytes. Keep benchmark sources unchanged and reuse their
reviewed API pattern rather than making a second story pipeline.

Proposed narrow framed protocol: `load`, `generate`, `cancel`, `unload`, `status`,
`shutdown`, with protocol version and monotonic owner epoch/request ID. Each
message has a fixed maximum before allocation; exact fields/types, duplicate
keys, UTF-8, nonfinite values and trailing bytes reject. `load` carries the
verified profile ID and private artifact identity. `generate` carries role,
bounded already-filtered prompt, schema ID and deadline/output budgets. Reply
identity must match the active owner/role, and only one generation runs at once.
The parent enforces framing/time/pipe limits independently; worker metrics never
grant canonical authority. Avoid persisting raw prompts/reasoning/errors.

Load one model, then create fresh role context/chat/sampler state for director
and narrator sequentially. Do not share KV/text sessions across observers or
stories. Retaining model weights is sufficient for the first warm optimization.
Worker input/control reader sets an atomic cancellation flag; generation owns
all context/session objects, installs CPU decode abort and load-progress abort,
then drains/synchronizes before destruction. Publish `cancelled` only after
that owner is terminal. `unload` first cancels and drains, then releases model.
Timeout/worker crash closes pipes, waits/reaps the exact owned process and makes
the original turn recoverable through the existing scoped storage lookup.
Unknown cleanup cannot publish a successful prepared turn. A bounded forced
termination path must remain distinguishable from cooperative completion.
No stop-all-processes, global daemon, ADB or unrelated-resource controls.

Candidate starting budgets: context4096 including template/schema; director350
tokens; narrator220; final text16KiB; input32KiB; one bounded director repair at
most, zero implicit recursive repairs, and120s complete-turn watchdog. These
are proposed workload limits, not latency targets or accepted measurements.
Retain the existing identical350-or-lower comparison profile separately.
Configure and persist exact effective budgets; worker queueing must be bounded.
Report load, context/tokenization, prefill and decode per role, validation/
repair, persistence, total first-final latency and peak process memory with
their actual timer scopes. Missing metrics remain unavailable.

For model management, verify size/hash/metadata on a blocking worker; use
explicit selection/import and atomic publication into app-owned local storage
only after checking free space. No gameplay auto-download. A path containing
spaces/non-ASCII must reach the local loader correctly. Validate the same
opened/copied bytes used by the worker; a check-then-reopen path alone is a
TOCTOU gap. On insufficient space, preserve story data and explain the model
failure. Capture selected artifact/template/runtime/prompt/schema/profile/
budgets with each prepared and accepted turn; later profile changes do not
rewrite history. Existing accepted-event `rules` is a game-rules profile, not
model provenance; do not repurpose it.

## Shared M05 work that cannot be skipped

`inference.rs::generate` currently polls immediately up to a numeric count with
no wait/waker. `execute` hard-codes `deterministic-fake-v1`, derives the expected
typed proposal before invoking inference and supplies only the engine-rendered
accepted description to its narrator. `engine.rs::preview` requires model
commands equal `Engine::proposal(request)`; ambiguous/thought requests require
clarification. `Engine::commit`, restore, replay and stored receipt validation
require exact engine-rendered narration. Existing Command resolution primarily
describes player actions; free NPC actor authority is not implemented by adding
strings to a prompt. These restrictions deliberately protect the fake proof.

Therefore a worker replacement alone cannot fulfill D04.04. The shared owner
must record an ADR/versioned contract under #9 and evolve portable Rust once:

- Distinguish raw attempted action/dialogue from author correction, inner
  thought and explicit typed fixture intent. A local director proposes a
  bounded interpretation; it cannot grant abilities, possessions, discoveries,
  arbitrary actor control or author privileges. Existing scope/revision/turn
  checks and mechanical resolver apply to every resulting command. Preserve
  exact raw intent and accepted interpretation for retries and provenance.
- Resolve planner attempts against canonical state, then derive the actual
  approved outcome. Recompute dependent reactions after rejection/change;
  never narrate the initially requested gift if the potion is already spent.
  New entities/temp refs and NPC reactions need explicit shared authorization
  and deterministic resolution, not unvalidated UI/model event creation.
- Separate trusted mechanical outcome from generated visible narration in a
  versioned accepted receipt. Preserve v1 exact-render restore semantics.
  New replay restores recorded text/outcomes without an LLM and validates the
  complete versioned encoding/provenance, bounds and approved outcome links.
  An arbitrary nonempty string or deletion of the equality check is inadequate.
- Define bounded narrator input and supported speech/description policy.
  Character speech gets only that character's eligible context; inspector
  grants never widen it. Use typed speaker/outcome references and conservative
  unsupported-claim checks, with explicit rejection/repair behavior. Syntax,
  claim-reference and canary checks cannot prove arbitrary prose faithful;
  measure semantic errors and retain visible correction/recovery. Do not claim
  a keyword filter or model self-approval proves factual consistency.
- The shared host owns queued/running/ready states and persistence continues
  to own atomic commit. Draft text never enters canonical transcript. Capture
  immutable scope/revision/profile before work; cancel/session change/late
  completion and lost acknowledgement retain the existing Rust fences. No
  transaction or host canonical mutex may span model generation.

The implementation should keep deterministic fake tests and their strict v1
contract, add real-provider tests separately and regenerate affected frontend/
Android wire artifacts centrally. Do not silently make Android depend on a
Windows executable or count desktop evidence as phone qualification.

## Proposed path ownership and adversarial gate

Coordinator: shared `contracts.rs`, `engine.rs`, `inference.rs`, `host.rs`, shared
storage migration/restore/provenance and Android-compatible wire generation;
new #9 ADR/contract tests. Native runtime specialist: new narrow
`crates/locallore-local-runtime/` and native-worker source/build/profile manifest
(final names require a coordinator claim), with no changes to protected runtime
experiments or weights. Desktop specialist: app-owned model IPC/controller/UI
and real native harness journeys after the shared contract freezes. One writer
per path; do not concurrently modify shared schemas/lockfiles.

Required model-free hostile-worker tests include wrong epoch/role/ID; duplicate,
oversized, truncated and delayed frames; stderr flood; no stdin consumption;
parent/worker death; cancel during load/prefill/decode and just before reply;
unload while active; owner reuse; queue saturation; corrupt or changed artifact;
spaces/non-ASCII; unknown cleanup; no implicit network/GPU fallback. Model tests
must separately prove callback terminal ownership, fresh model recovery and
same-loaded-model role reuse. Worker failure cannot alter canonical bytes.

Required shared cases: forged abilities/item ownership/rewards; author injection;
spent-potion request; dependent reaction invalidation; malformed proposal and
bounded repair; invented consequential narration and foreign speaker; secret
canaries absent before model input; omniscient inspection leaves generation
input unchanged; cancel and stale completion at every phase; simultaneous
writers; exact retry after restart; lost commit acknowledgement; v1/v2 restore
and tamper rejection; no LLM on replay; profile change affects future turns only.

Required app proof: actual controller/native IPC imports approved local model,
free-text potion/secret/invalid actions, visible non-canonical pending state,
cancel/rephrase/retry, process restart/resume and inspected single durable effect.
Collect app-only semantic/native renders, bounded error enums and all attempted
synthetic runs. Run offline/network-blocked after provisioning, record desktop
hardware/tool/runtime/model/source manifests and distinguish forced/cooperative
cancel. A real render is not an inference measurement. Sustained-session and
human quality evaluation remain explicit requirements from MODEL_EVALUATION.md.

## What was checked in this investigation

Read-only Git head/status inspection of the cached upstream source; SHA-256 and
byte counts of the three assets above; metadata-only inspector; exact upstream
API/license/card/schema source review; current shared source/contract analysis;
and `git diff --check` on this report. No build, unit-suite rerun, inference,
native UI render, network-blocked run, worker cancellation, memory/performance
measurement or device execution was performed. Historical evidence is labeled.
Disk was constrained during assignment; creating/importing another large model
copy must wait for sufficient confirmed space. Availability of existing bytes
does not grant permission to delete another chat's caches or stop its processes.

D04.01 is ready for implementation-owner review as a concrete candidate/design.
It remains unchecked until actual profile selection and required evidence.
D04.02–D04.06 and shared M05 remain unimplemented by this docs-only packet.
