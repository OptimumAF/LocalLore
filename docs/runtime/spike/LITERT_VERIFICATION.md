# LiteRT-LM host spike verification

2026-10-22; M01.02 host slice, supporting M01.03. Windows x64, Python 3.12.14,
official `litert-lm-api==0.18.1`, pinned source commit
`bda624851d74be34d4e1f7fac1fc4155939539c7`.

Actual checks in the isolated `research/m01-litert-spike` worktree:

| Check | Result |
|---|---|
| Official wheel SHA256 and byte count before local installation | Matched published metadata |
| `pip install --no-index --no-deps <verified-wheel>` in local venv | Succeeded; API imported |
| Installed API Python sources versus pinned upstream files | Three files matched byte for byte |
| `python benchmarks/spike/litert/run.py --help` | Exit 0 |
| `python -m unittest discover -s benchmarks/spike/litert -p 'test_*.py' -v` | 10 passed |
| Missing local model using actual installed API worker | Exit 2, `model_missing`, one result JSON, stderr empty |
| Synthetic 21-byte corrupt `.litertlm` using native `ModelInfo` | Exit 2, `model_invalid`, one result JSON, stderr empty |

The unit suite covers strict input bounds/types/keys, duplicates/nonfinite JSON,
reasoning-channel omission, unsupported tool/content rejection, native settings
through a test double, overflow before generation, fixed exception categories,
context-manager ownership on success/error, and subprocess verification that
buffered Python diagnostics stay discarded when the SDK raises. Independent
review found that exceptional exits originally skipped the flush; the flush now
runs before descriptor restoration on every exit. Its fake SDK tests establish
worker control flow only. They do not establish native resource cleanup,
inference compatibility or performance.

## Actual local model smoke

The coordinator separately downloaded and verified the pinned public Gemma 4
E2B bundle: 2588147712 bytes, SHA256
`181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`.
No model weights were downloaded by this agent. The isolated worker loaded those
local bytes on Windows x64 CPU using four threads and the actual Rust oracle's
original `fixture gift` director request. The caller closed stdin and enforced a
120-second process deadline. This is one cold compatibility smoke, with no
warmup/sample distribution, human quality verdict or phone inference claim.

`describe.py --model <verified-local-model>` succeeded: LLM, dynamic context,
maximum context 32003, minimum runtime unspecified; text/vision/audio inputs,
no video; text backends CPU/GPU. This exact bundle reports thinking and function
calling unsupported, speculative decoding supported. These metadata values are
reported as observed; they do not establish that every modality/backend works.

`run.py --model <verified-local-model>` completed with 473 native prefill tokens,
64 decode tokens, LL_GUIDANCE schema enabled, native template applied, thinking
disabled, and 176 bytes of final visible text. The outer caller observed exit 0,
428 stdout bytes (one result JSON), and zero stderr bytes. The final text was
passed in memory to `runtime_spike.exe validate gift`; actual Rust
`Proposal::parse` and engine preview accepted it, with canonical state unchanged.
No raw prompt, model text, thought channel or exception string was persisted.

Observed single-call timings were 2297 ms model load and 5562 ms generation;
outer process wall time was 12422 ms. These monotonic host observations include
different scopes and cannot support complete-turn latency, sustained throughput,
memory, Android speed or model quality acceptance. Machine load was not
controlled as a benchmark. See [sanitized aggregates](LITERT_SMOKE.json).

## Actual cooperative API cancellation and fresh reload

One separate call used `cancel_smoke.py` with the same verified local model,
Rust `fixture gift` request, CPU/four threads, 4096 total-token capacity,
350-token-or-lower request budget, no tools, native schema/template and disabled
thinking. Its outer caller used `subprocess.run(..., timeout=60)` with stdin
closed after the request. The watchdog was not triggered.

After the first nonempty final-visible stream event, the helper invoked official
`Conversation.cancel_process()`. The void API returned within the monotonic
clock's observed resolution (reported 0 ms); the iterator ended 62 ms later.
One further event was delivered after cancellation. Both conversation and engine
context-manager exits completed. A fresh engine reload and short original
synthetic call then completed with 16 native input tokens and two output tokens.
The helper exited 0 with no stderr and emitted only aggregate JSON. No streamed
event content, final generated text or thought channel was saved or printed.
See [sanitized cancellation aggregate](LITERT_CANCEL_SMOKE.json).

The pinned official
[Python stream implementation](https://raw.githubusercontent.com/google-ai-edge/LiteRT-LM/bda624851d74be34d4e1f7fac1fc4155939539c7/python/litert_lm/conversation.py)
calls the native cancellation API and ends its iterator upon a cancellation
status. Cancellation does not promise to retract queued stream events. Here,
call return and stream completion are separate observations; returning from
context-manager close is not an RSS measurement. This one cooperative Windows
CPU result establishes neither all-input termination nor Android/backgrounding,
memory-pressure or thermal behavior. Parent process containment is tested
separately and must not be substituted for this native cooperative result.

No emulator or phone was modified or benchmarked. M01 task and physical-device
exit gates remain unchecked.
