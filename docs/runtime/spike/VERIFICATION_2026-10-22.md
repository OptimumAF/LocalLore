# Host runtime spike evidence — 2026-10-22

Scope: M01.02 host slice, supporting M01.03 preparation, [#5](https://github.com/OptimumAF/LocalLore/issues/5).
Implemented for review, not complete M01 acceptance. Baseline is owner-merged
main `3a7cb82`; M03.06 PR #32 remains separate. No Android application/runtime
dependency, engine rule, model distribution, merge, release or setting changes.

## Actual local paths exercised

- LiteRT-LM v0.18.1 / `bda624851d74be34d4e1f7fac1fc4155939539c7`:
  official Windows `litert-lm-api` wheel, verified SHA-256, isolated Python
  3.12.14 venv. Actual prepared Gemma E2B bytes match the publisher's exact
  size/hash. The API describes a dynamic-context LLM, CPU/GPU text capability,
  maximum context 32003, and no thinking/function-call support for this bundle;
  only CPU with a 4096-token cap is executed. Per-tensor quantization and
  original tokenizer/template parity remain pending. Vendor DLL notice review
  is required before future binary redistribution.
- llama.cpp v0.7.0 / `620d2225cc436ab0b001e3200e590e3b286ef9ab`:
  official completion/tokenize examples and a small explicit API helper built
  with existing MSVC 19.34 and CMake 3.22.1, at most four build jobs. The helper
  uses the runtime's template/tokenizer/grammar/sampler and RAII owners. Actual
  Qwen3-0.6B GGUF v3 is `qwen3`, 310 tensors (113 F32 + 197 Q8_0), 28 layers and
  file type 7; local bytes match the official publisher hash. Its embedded
  template differs from a later upstream tokenizer template; the helper uses
  the actual embedded one. This tiny model is a plumbing smoke only; the
  original Qwen3.5-4B conversion/load remains pending.

Sources/licenses/byte counts/hashes are retained in the linked runtime and
independent source reports, not inferred from a filename. Source licenses are
Apache-2.0 / MIT; model cards and exact available license files are reviewed.
No weights or upstream binary is committed. Only public synthetic fixtures run.

The Windows x64 host reports 68,399,599,616 bytes of memory; this is not reference
phone RAM or a supported tier. No power, thermal, memory high-water or controlled
OS cache measurement was performed. Python host tests use 3.9.12, Rust is 1.93.1.
Each role has a newly loaded engine/process, with one model active at a time.
The legacy JSON scope name `windows_host_cold_smoke` means that fresh process;
it does not mean cold disk pages. Different model sizes and sampling settings
are documented in each worker; timings are not a fair ranking or product target.

## Final coordinator cohort and checks

[HOST_RESULTS_2026-10-22.json](HOST_RESULTS_2026-10-22.json) retains every attempt
in the declared final cohort: **8 requests, 10 attempted inference roles**.
Four requests (two per runtime, with cancellation between them) committed the
gift; both director and narrator completed. Each had one event/revision, exact
retry equality, one recipient observation and zero absent-NPC observations.
Two requests were cancelled with their process trees/pipe threads cleaned up;
each records one attempted director. Two invalid-intent requests were rejected
by Rust before inference (Inventory/Ability, zero attempted roles).

Cancellation offsets were four seconds for LiteRT and three for llama.cpp,
after hash verification. The parent cannot observe the exact native phase at
termination and does not label it load versus decode. Fresh successful calls
after both cancellations exercised reload. The LiteRT API additionally completed
one cooperative streaming check: cancel returned, stream ended 62 ms later with
one subsequent queued event, native owners closed, and fresh reload succeeded.
The 60-second watchdog did not trigger. These are single Windows observations,
not Android cancellation guarantees or native memory-release measurements.

| Command/check actually run | Result |
|---|---|
| `python scripts/check.py host --offline` | Passed: 26 domain + 8 FFI + 5 example Rust tests; 4 fixture comparisons; 21 top-level benchmark tests (5 existing + 16 parent), 10 LiteRT worker, 14 llama worker, 18 runner/APK Python tests; 3 linker tests; format/Clippy |
| `cargo build --locked --offline -p locallore --example runtime_spike` | Executable oracle built; proposal parsing and validation use unchanged actual engine |
| Coordinator commands in README, per runtime; repeated after cancel | Four actual two-role paths committed, no raw model text persisted |
| Same commands with `--cancel-after 4` (LiteRT) / `3` (llama.cpp) | Expected nonzero cancellation; both cleanup flags true; subsequent requests committed |
| `--case spent` / `--case unlearned` | Expected preflight rejection, no worker invocation |
| Official llama examples build/version/help and missing/corrupt files | Passed/error behavior observed; details in LLAMA_HOST report |
| `python benchmarks/spike/llama/smoke.py --model <verified-file> --executable <built-helper>` | Agent ran 7 native checks, all passed: three generations, missing/corrupt/context failures, live process termination |
| LiteRT metadata/missing/corrupt files and cooperative cancel helper | Agent executed actual API; fixed error categories, cooperative stream drain and reload observed |
| `powershell -NoProfile -File benchmarks/inspect-device.ps1` | Expected exit 2: five authorized emulators, zero physical candidates; sanitized DEVICE_PROBE file |
| `git diff --check` | Passed before PR handoff |

The final cohort is compatibility evidence, not an acceptance-rate or latency
sample. Exploratory development calls exposed a CLI reasoning-forwarding bug
and absent grammar installation; those failures and corrections are retained
in runtime reports. Their exploratory total is not a benchmark denominator;
no quality/speed/repair-rate estimate is derived from selected successful calls.

## Corrections and independent work

Separate worktrees own the LiteRT worker/provisioning/evidence, llama native
helper/worker/evidence, and independent review/adversarial parent tests. The
coordinator owns shared request/result contracts, process containment, Rust
oracle, integration and ticket reconciliation. Claims/handoffs are on #5.

Review reproduced and corrected malformed JSON/Unicode failures, buffered native
diagnostic leakage on exceptions, a blocking pipe-close hazard, per-role rather
than shared deadlines, incompatible fixed error registries and an unmeasured
canonical-equality assertion. Windows fault tests exercise overflow, a child
refusing stdin, a root exiting while descendants retain pipes, cancellation and
failed-cleanup bounded return. The review report preserves exact finite checks;
another agent's review does not grant owner acceptance.

## Remaining gates

No physical phone, ARM64/mobile inference, GPU/NPU, Android background/memory
pressure/low storage, complete v1 schema coverage, tokenizer/conversion parity,
original Qwen3.5-4B, warm shared model, sustained session, memory high-water,
prose quality, repair-rate or support-profile acceptance follows. Narration is
the existing exact-render gate, not semantic validation. Saves remain in memory.
No runtime traffic capture or general native security/leak audit was performed.

M01.01 and physical/model-dependent M01.03–M01.06 remain blocked/pending. M01.02's
host slice transfers to PR review with its full task unchecked. Next runnable
technical preparation is an isolated Android runtime build/load experiment
against the reviewed APIs on available emulators; it cannot replace the phone
gate. M04 still follows foundation acceptance. Hosted CI is independently
blocked because Actions is disabled; no setting was changed.
