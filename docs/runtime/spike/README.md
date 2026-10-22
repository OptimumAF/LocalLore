# Local runtime compatibility spike

M01.02 host preparation with supporting M01.03 fixtures. This explicitly runs
local model files on Windows x64 CPU, outside the Android app. Neither runtime
is selected for production. M01's physical-device, original Qwen3.5-4B,
language-quality and full-turn acceptance gates remain open.

The harness gives an actual model the engine's trusted action and filtered
player context. Rust strictly parses/validates its proposal. Only an accepted
public description reaches a separate narrator call; Rust's existing exact
narration rule still controls commit. One accepted gift event, an unchanged
exact retry, recipient observation and absent-observer isolation are checked.
The narrator repeats the rendered description as a compatibility test; this is
not a prose-quality or unrestricted story-writing evaluation.

Each role loads a fresh engine in a fresh process. One model is active at a time,
but this does **not** test one loaded model reused across roles, a warm session,
durable saves or mobile performance. OS file-cache state is uncontrolled.
Different model sizes, architectures and samplers prevent a fair speed/quality
ranking. [Dated verification](VERIFICATION_2026-10-22.md) separates observations
from the full [evaluation protocol](../EVALUATION_PROTOCOL.md).

## Prepare explicit local inputs

Use Rust 1.93.1 and Python 3.9+ for the coordinator. LiteRT's exact Windows API
wheel requires Python 3.10+; this packet used an isolated Python 3.12.14 venv.
Follow [LiteRT provisioning](../../../benchmarks/spike/litert/README.md) and
[llama.cpp build instructions](../../../benchmarks/spike/llama/README.md).
Their source/release/license pins are reviewed before execution. No global
environment changes, production dependency, runtime server or app model
downloader is introduced. llama.cpp's example decode pattern retains its MIT
[notice](../../../benchmarks/spike/llama/NOTICE).

Manually provision the following public development artifacts into ignored
`models/`, keeping their publisher revision and applicable license notices:

| Development artifact | Exact local bytes | SHA-256 |
|---|---:|---|
| [Gemma E2B .litertlm](https://huggingface.co/litert-community/gemma-4-E2B-it-litert-lm/resolve/a790a852d433991c0c0a41c1154cf9b3850300fa/gemma-4-E2B-it.litertlm) | 2,588,147,712 | `181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c` |
| [Official Qwen3-0.6B Q8_0 GGUF](https://huggingface.co/Qwen/Qwen3-0.6B-GGUF/resolve/23749fefcc72300e3a2ad315e1317431b06b590a/Qwen3-0.6B-Q8_0.gguf) | 639,446,688 | `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031` |

The coordinator verifies size/hash before a worker starts. The Qwen worker also
verifies them independently. This identifies bytes; it is not a hostile-file
parser certification. Use trusted local paths: concurrent replacement after
hashing is outside this development tool's threat boundary. Weights, binaries,
source checkouts and venvs stay ignored and are never bundled or uploaded.
No command below downloads a model. API wheel provisioning is a separate,
explicit network action with a hash-pinned artifact; inference uses local files.

The small Qwen model permits a bounded backend smoke and does not replace the
planned Qwen3.5-4B conversion/load. No public official Qwen3.5 GGUF was established
in this packet. Exact Gemma tensor quantization and tokenizer/template parity
against original conversion inputs also remain unverified.

## Run the synthetic compatibility path

Run from the repository root after explicit provisioning. These examples use
the local filenames from this packet; substitute your verified paths.

```powershell
cargo build --locked --offline -p locallore --example runtime_spike
python scripts/check.py host --offline
python benchmarks/runtime_spike.py --runtime litert --python target/litert-spike/venv/Scripts/python.exe --model models/gemma4-e2b.litertlm --oracle target/debug/examples/runtime_spike.exe --output target/litert-result.json
python benchmarks/runtime_spike.py --runtime llama --model models/qwen3-0.6b-q8.gguf --executable target/runtime-spike/adapter-build/locallore-llama-spike.exe --oracle target/debug/examples/runtime_spike.exe --output target/llama-result.json
```

The `gift` case is the default. `--case spent` and `--case unlearned` demonstrate
engine preflight rejecting invalid intent before hashing/loading a model or
spawning an inference worker. These do not test a model's handling of bad intent.
`--cancel-after 3` requests process cancellation three seconds after inference
starts, after hash verification. A short task may finish before that offset.
The default deadline is 60 seconds **shared across both role calls**, including
their load/worker time and intervening validation. Hashing/oracle setup is
outside it. This clock is not the product's measured full-turn latency.

Only enum/numeric aggregate results reach stdout or `--output`: no prompt,
generated prose, raw exception, model path, native stderr or hidden reasoning.
Every attempted role is retained, including cancellation/timeout/errors. A
nonzero exit reports a failed/cancelled attempt. `preflight_rejected` is a safe
engine result with zero attempted roles. Report all cohorts rather than
discarding failures or treating successful-call counts as all-attempt rates.

## Ownership and bounds

Workers read one request (at most 32 KiB) before native import/child execution.
Windows job assignment precedes releasing stdin; a non-inherited kill-on-close
job owns descendants. POSIX uses a process group, but this packet verifies the
Windows implementation only. The parent drains both pipes concurrently with
a combined 128 KiB retained cap, bounds input writes and enforces cancellation
and deadline. Cleanup waits are bounded separately; a failure is reported as
`cleanup_failed`, never as proof of release. No blocking pipe close is attempted
on a reader which failed to exit. This controls trusted experiment workers,
not arbitrary executables supplied by an adversarial developer.

Workers fix CPU threads at four, total context at 4096 and output at 350 director
or 220 narrator tokens. Their own model template/tokenizer checks reserve the
output budget and reject overflow. Unknown fields, invalid UTF-8/nonfinite
values, tools and unsupported reasoning output fail safely. Engine validation
remains mandatory even when a JSON grammar is installed.

Default host checks run only Rust and stdlib synthetic/mock tests. They do not
install either runtime or load weights. Real calls, the native smoke script and
the LiteRT cooperative-cancellation script are explicit development checks.
The latter distinguishes cancel-call return, stream drain, owner close and
fresh reload; a queued event after cancellation is not accepted gameplay.

See [independent source review](SOURCE_REVIEW_2026-10-22.md),
[boundary review](REVIEW_2026-10-22.md), [LiteRT checks](LITERT_VERIFICATION.md)
and [llama.cpp checks](LLAMA_HOST_2026-10-22.md). Model and optional vendor-binary
distribution terms require separate review before any future app packaging.
