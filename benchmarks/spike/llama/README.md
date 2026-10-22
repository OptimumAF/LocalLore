# llama.cpp host experiment

M01.02 preparation uses official llama.cpp v0.7.0, commit
`620d2225cc436ab0b001e3200e590e3b286ef9ab`. It adds no production dependency.
The runtime is MIT licensed; its bundled dependencies retain upstream licenses.
Only public, original synthetic fixtures belong in this experiment.

Prepare an ignored source directory explicitly, with existing Git, Visual Studio
2022 C++ tools, and CMake/Ninja. No script installs tools or downloads weights:

```powershell
git -c core.longpaths=true clone --depth 1 --branch v0.7.0 https://github.com/ggml-org/llama.cpp.git target/runtime-spike/llama.cpp
powershell -NoProfile -File benchmarks/spike/llama/build.ps1 -SourceDir target/runtime-spike/llama.cpp -BuildDir target/runtime-spike/adapter-build -CmakePath "$env:LOCALAPPDATA/Android/Sdk/cmake/3.22.1/bin/cmake.exe"
python -m unittest discover -s benchmarks/spike/llama -p 'test_*.py' -v
```

The CMake project verifies the local commit and rejects tracked modifications.
It disables shared libraries, external accelerated/network backends, server,
application, UI, subprocess tools, OpenSSL/BoringSSL/LibreSSL, and LLGuidance.
Upstream `common` still compiles its bundled HTTP utility; this helper calls only
the local-file model API and exposes no URL, download, server, or tool API.
`LLAMA_CURL` is a deprecated, removed option at this pin, not a working network
control. This Windows build uses AVX2; no generic CPU, ARM64, or Android claim.

`run.py --model <local.gguf> --executable <locallore-llama-spike.exe>` reads exactly
one bounded JSON request from stdin, then invokes the compiled helper. The
coordinator verifies executable/source provenance and owns its process tree and
outer deadline. The worker independently verifies the exact model size/SHA256,
bounds both native pipes at 64 KiB each, enforces a 55 second native deadline,
and forwards neither native stderr nor exception text. The helper has no child
process path. This is a development experiment, not a general sandbox for
arbitrary executables.

Request v1 has exactly `version`, `role` (`director` or `narrator`), `prompt`,
`max_tokens` (1–350), `context_tokens` (4096), `threads` (4), and `schema` (object
or null). Response v1 has status, final visible text or a fixed error category,
load/generation timings, input/output token counts, and explicit schema/template/
thinking flags. Requests are at most 32 KiB; final text is at most 16 KiB.
Each invocation loads fresh model/context/session/sampler objects and releases
them before exit. OS process termination supplies the experiment cancellation
boundary; this is not evidence for an in-process Android abort callback.

The helper follows the official `examples/simple` batch/decode ownership pattern
and uses upstream chat/session/sampling APIs. It applies the embedded Jinja
template with `enable_thinking=false`, disables reasoning preservation, supplies
no tools, tokenizes user parts without interpreting role-control tokens, and
rejects prompts whose actual token count plus output reserve exceeds 4096.
Schema calls explicitly install the official JSON-schema-to-grammar converter;
grammar compliance still grants no engine authority. Narrator calls receive a
separate fresh session with only coordinator-approved context. The final parser
rejects reasoning/tool-call output before the response can leave the helper.
Sampling is fixed at seed 42, temperature 0.7, top-p 0.8, top-k 20, min-p 0 and
presence penalty 1.5; a seed does not promise cross-hardware determinism.

The direct official `llama-completion` example was separately built and its
startup/missing/corrupt-file behavior tested. It was not used as a transport:
at this pin its single-message formatter does not forward `--reasoning off`
template kwargs, and its stdout contains transport markers. The explicit API
helper avoids making unsupported claims about those flags.

Only the reviewed official `Qwen/Qwen3-0.6B-GGUF` Q8_0 artifact is permitted by
this worker. See [pinned sources and actual checks](../../../docs/runtime/spike/LLAMA_HOST_2026-10-22.md).
This tiny model is a plumbing smoke; it does not replace the original Qwen3.5-4B
candidate or satisfy phone performance, story quality, or backend selection.
