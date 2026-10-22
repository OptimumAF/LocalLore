# Bounded M01 comparison protocol v1

This is a runnable host preparation and a procedure for a later real-model spike.
It contains no phone/model results. Use only original synthetic LocalLore
fixtures. Neither a fake provider nor this calculator passes M01 acceptance.

## Preparation and compatibility

1. Record inventory using `powershell -NoProfile -File benchmarks/inspect-device.ps1`.
   It accepts `-AdbPath` for an existing executable, never emits serials, ignores
   recognized emulators, and stops if exactly one physical candidate cannot be
   identified. Confirm the selected physical phone and retail RAM tier. Save only
   reviewed, sanitized aggregate output; missing metrics stay unavailable.
2. Use a separate experiment checkout at an exact runtime commit from
   `source-manifest.json`. Follow that commit's official example/build guide.
   Do not add production app dependencies or upgrade a candidate silently.
   LiteRT-LM uses its official C++ build-and-run example and a local `.litertlm`
   file. llama.cpp uses its pinned Android example or NDK CLI build and a local
   GGUF. Do not run download-enabled `-hf` or `--from-huggingface-repo` during play.
3. Verify local model SHA256 against the reviewed manifest or local conversion
   record. Hash each input shard/tokenizer/template and converted/quantized
   output. Record conversion dependency lock/environment, command, precision,
   model architecture and actual tensor metadata. Qwen Q4_K_M is a proposed test,
   not an artifact already produced. An architecture registration is source
   evidence; a successful exact-model load is separate evidence.
4. Verify role formatting, tokenizer IDs, EOS/stop behavior and an ordinary
   one-turn text response. Try the exact v1 proposal schema; reject unknown
   fields/operations with the engine, even if constrained decoding succeeds.
   Exercise cancellation, unload/reload, corrupt/truncated/wrong-format files,
   and unsupported backends before longer workloads. Capture failure categories
   without dumping model paths, private story content, or hidden reasoning.

## Shared role workload

Use `fixtures/lantern_quay.json`, `docs/DOMAIN_CONTRACT_V1.md`, and the implemented
contract tests as the shared world and mechanical oracle. Export a frozen
synthetic request/schema set from that version before any model comparison;
record fixture, schema, and prompt hashes. Do not invent a separate runtime
proposal format. Contract v1 bounds (at most eight commands, 16384 proposal
bytes, 2048 speech bytes) still apply independently of token limits. The actual
engine decides validity, scope and accepted outcomes.

Start with a total 4096-token context allocation per call, including template,
mandatory context and output reserve. Count with the candidate tokenizer. Bound
director output at 350 tokens, narrator at 220, and at most one 350-token repair
per turn; explicitly disable or budget thinking. Proposed total inference wall
deadline: 60 seconds. These are initial experiment caps, not measured capacity or
a change to the existing p50/p95 product targets. If mandatory context cannot
fit, stop safely. A later 8192-token run is a separate profile. Record actual
generation settings, thread count, backend and caches. Never silently truncate
authoritative facts to make a test fit.

For each candidate run the identical fixtures at least three times in cold and
warm conditions (record actual counts). Separate director and narrator results:

| Workload | Director assessment | Narrator assessment |
|---|---|---|
| Last potion, duplicate request, spent potion reuse | Schema valid; transfer only once; invalid repeat rejected | Describes only accepted transfer, no restored potion/reward |
| Unlearned ability and privileged dialogue injection | No ability grant, author edit, external tool or scope change | Understandable refusal/outcome without invented powers |
| False accusation and royal-ancestry claim | Claim/belief provenance stays separate from world truth | Attributes claims; does not establish ancestry/guilt |
| Private exchange, nonwitness NPC, two same-name actors | Eligible IDs and observer contexts only | No inaccessible secret; distinct voices assessed by human |
| Fork and story switch while a response is pending | Stale/cross-scope response rejected | No narrative attached to another story or revision |
| Summary contradicts accepted events | Events win; summary never changes inventory | Grounding uses accepted outcome, not fabricated recap |

Run director alone against fixed context, narrator alone against fixed accepted
outcomes, then the complete director/validate/narrator/commit path. Do not prompt
the narrator to resolve mechanics again. Compare naive recent-chat prompting,
structured state, and the eventual full pipeline only when each actually exists;
mark unavailable baselines pending. Use one loaded model and sequential isolated
role contexts. Reset conversations/caches between scope-isolation cases.

Record malformed output, engine-invalid plans, bounded repair attempts, safe
rejections and unsupported consequential prose separately. Human quality review
covers attribution, meaningful consequences, agency, distinctiveness,
repetition/pacing and readability. An automated judge is not the acceptance
authority. No private player traces or hosted judge are needed.

## Measurement and host tool

Use a monotonic clock; separate load from ordinary turns and distinguish cold,
warm and sustained runs. Record retrieval, role prefill/decode, validation,
repair, commit, total turn and first final-response times. Public narration is
available only after commit. Do not substitute token-stream TTFT for first
final-response latency. Report peak memory method/process/device scope, thermal
status and power conditions. Unsupported memory/energy APIs yield `null`, never
an estimate labeled measured. Keep every attempted-run count, failure, timeout,
cancellation, OOM and warmup exclusion in the report. A 30-minute sustained
session reports actual duration and completed-turn count.

`python -m unittest discover -s benchmarks -p 'test_*.py' -v` runs host calculator
tests with invented data. `python benchmarks/summarize_runs.py <reviewed.jsonl>`
aggregates one homogeneous set of **completed real-model** turns. It does not
launch inference, score prose, discover a phone, verify measurement provenance,
or qualify a supported profile. Failed/cancelled/incomplete attempts are
reported separately with the total attempted denominator; this calculator's
completed-turn denominator must not be used as the acceptance-rate denominator
for all attempts. The report must disclose that selection.

Each JSONL object requires these fields (no raw prompt/output):

- `kind`: `real_model_measurement`; `environment`: `host` or `physical_android`.
- `profile_id`, `fixture_version`, `schema_version`, `prompt_version`:
  nonempty version references; the report binds them to exact hashes.
- `app_commit`, `runtime_commit`: 40 lowercase hex digits; `model_sha256`:
  64 lowercase hex digits from verified local artifact bytes.
- `condition`: `cold`, `warm`, or `sustained`; `turn_id`: unique synthetic ID.
- `retrieval_ms`, `director_prefill_ms`, `director_decode_ms`, `validation_ms`,
  `repair_ms`, `narrator_prefill_ms`, `narrator_decode_ms`, `commit_ms`, `turn_ms`,
  `first_final_response_ms`: finite nonnegative monotonic durations. Sequential
  stages cannot exceed total turn time; final response cannot precede commit.
- `schema_valid_before_repair`, `proposal_accepted`, `repaired`,
  `narrator_faithful`: explicit Boolean assessments from parsing, engine
  validation and human narrative review; `repair_count`: 0 or 1.
- `peak_memory_bytes`: observed numeric value or `null`. Document method and
  missing sample count; different memory scopes require separate profiles.

The calculator rejects fake traces, mixed profile/revision/condition groups,
duplicate IDs, nonfinite/negative values and unbounded repairs. Percentiles use
nearest rank; counts and denominators stay visible. Unit-test numbers are never
published as benchmark results. No confidence or performance support is inferred
from a small sample.

## Gate decision

Keep M01.01–M01.03 unchecked until their full device/spike/quality criteria are
met. M01.04/M01.05 require actual complete-turn, sustained and fault measurements.
M01.06 requires a measured comparison and owner-reviewed ADR. The current
research selects neither backend and supports no phone/profile. See
`../MODEL_EVALUATION.md` for unchanged provisional quality and latency targets.
