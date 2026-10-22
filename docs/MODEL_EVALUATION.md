# Local model and runtime evaluation

Status: experiment plan, not benchmark results. Prepared 2026-10-22. No physical phone or RAM configuration has been confirmed or tested for this project.

## Selection principle

Choose the smallest model/runtime/profile that meets the story application's quality and sustained latency requirements. A model that merely loads is not a supported configuration. A model's disk file size, advertised context window, or desktop benchmark does not establish its memory use, speed, or quality on a phone.

Initially share one model across director, narrator, and archivist calls. Measure additional-role calls and context-switch overhead before adding them. Avoid simultaneous models or a separate model per NPC by default.

## Research shortlist, not a recommendation backed by project measurements

| Candidate | Reason to evaluate | What remains unverified |
|---|---|---|
| Gemma 4 E2B / E4B through a compatible LiteRT-LM package | Official mobile/edge direction and local runtime path | Exact artifact, device/backend support, structured-output quality, end-to-end speed and memory |
| Qwen3.5-4B through a compatible pinned native runtime | Small published model to compare for planning and prose | Correct conversion/template/backend support, thermal behavior, schema compliance and story quality |
| Qwen3.5-9B or another larger model | Optional high-memory experiment only | Whether the full app can run reliably at useful sustained speed |

Google's official Gemma documentation identifies its smaller models as mobile/edge targets; Qwen publishes the 4B model and license. These facts motivate an experiment, not a claim that either wins this workload. See [S03–S08](REFERENCES.md). Recheck available releases and artifacts when implementation starts. Do not silently upgrade a supported model or runtime mid-benchmark.

The original discussion included unsupported device-specific assumptions. Do not publish those as facts about the user. Obtain the actual test device information through the development environment or owner before assigning a support tier.

## Reproducible manifest

Record device model, chipset, physical RAM tier, OS/build, app commit, runtime commit/version, CPU/GPU/NPU backend, model publisher/revision/hash, conversion tool/revision, quantization, tokenizer and chat template, context/output/repair limits, threads/acceleration settings, prompt/schema versions, fixture version, session length, and power/thermal conditions. Do not record serial numbers, advertising identifiers, personal filesystem paths, private chats, or authentication tokens.

Keep aggregate results in the public repository. Raw synthetic traces may be included when useful and reasonably sized. Never upload actual user stories to an external evaluation service. A desktop run is explicitly a desktop run.

## Experiment stages

**Compatibility:** load a small fixture, verify tokenization/template, run constrained output, cancel, unload, and reload. Test unsupported/corrupt files without crashing the app or modifying story state.

**Role quality:** evaluate director schemas/mechanics, narrator prose/faithfulness, and archivist attribution independently. A model can be good at prose and poor at valid state proposals.

**Integrated workflow:** evaluate complete ordinary turns and turns requiring repair, not just isolated decode speed. Include fresh and warm contexts, retrieval, persistence, and role switching.

**Sustained use:** run a scripted synthetic session for at least 30 minutes where hardware is available, reporting starting and ending conditions and the number of completed turns. Report performance degradation, OOMs, cancellations, and thermal events. This is a proposed protocol, not a claim that a session has been run.

## Initial workload profiles

Start with a compact, approximately 4k-token context profile and short responses, then test an approximately 8k profile only if the device budget allows. Use explicit caps such as a 200–350-token director proposal, a 120–220-token final narrative, and at most one bounded repair in the initial experiment. These are adjustable product hypotheses, not values copied from a model card. Include template/schema overhead and any extra inference passes in the real measurement.

Provide concise and expressive output profiles rather than assuming longer is always better. Thinking/reasoning mode, where supported, must be explicitly budgeted and tested; do not persist or display hidden reasoning by default.

## Metrics and provisional targets

| Metric | Proposed initial target | Important qualification |
|---|---|---|
| Input UI response | Under 100 ms on reference device | Separate from model latency; measure rather than infer |
| Cancellation acknowledgment | Within 1 s; backend cleanup separately measured | Acknowledgment is not proof memory is already released |
| Ordinary full turn, compact profile | p50 at most 15 s; p95 at most 30 s | Product target for calibration, not promised phone performance |
| Canonical commit failures/duplication | Zero in the finite reference suite | Hard correctness gate, not statistical prose quality |
| Director schema validity before repair | At least 95% of a declared test set | Report sample size, invalid examples, and confidence limits where appropriate |
| Structured plan accepted after allowed repair | At least 98% of a declared test set | Safe rejection is preferable to accepting invalid mechanics |
| Story/branch/observer isolation | Zero unauthorized records in context fixtures | Content-level guess/hallucination evaluated separately |
| Sustained stability | No crash or corrupted state in the prescribed session | Publish tested device/profile, not a general guarantee |

Latency thresholds may be revised by owner-approved ADR after measurement, with a clear UX consequence and explanation. They must not be quietly relaxed to declare success. Memory targets should be defined relative to the actual device/process budget, with measured peak usage and a documented safety margin; do not fabricate a universal GB threshold.

Report load time, first final-response latency, prefill time, per-role decode time, end-to-end latency distribution, repair rate, peak resident/native/device memory where observable, temperature/thermal status, and available energy measurements. If an API cannot expose a metric reliably, mark it unavailable instead of estimating it as a measurement.

## Quality comparison and decision

Use the same synthetic tasks, device, output budget, and generation settings for a fair comparison. Evaluate at least naive recent-chat prompting, structured state without long-memory retrieval, and the complete proposed pipeline. Additional embeddings/critics/multiple models need an ablation showing benefit relative to cost.

Human review should evaluate distinct voices, meaningful consequences, repetition, pacing, player agency, and unsupported consequential facts. A local model judge can help find candidate failures but cannot be the only quality authority. Do not use a hosted judge on private player content.

Select a backend/model/profile in an ADR with evidence and rejected alternatives. Publish only verified supported profiles. Include a smaller-model or reduced-context path where feasible, and a clear unsupported-device explanation otherwise. No silent cloud fallback.
