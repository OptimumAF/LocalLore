# llama.cpp Windows host compatibility experiment, 2026-10-22

Refs #5 (M01.02 host slice, supporting M01.03). This is measured host
compatibility, not an accepted M01 task, phone qualification, quality review,
production backend choice, or a fair speed comparison across different models.
The original Qwen3.5-4B candidate remains pending conversion/load evaluation.

## Exact inputs and licensing

- Official [llama.cpp latest stable release](https://github.com/ggml-org/llama.cpp/releases/tag/v0.7.0)
  rechecked as v0.7.0, commit `620d2225cc436ab0b001e3200e590e3b286ef9ab`.
  [MIT license at that commit](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/LICENSE).
- Official [Qwen/Qwen3-0.6B-GGUF](https://huggingface.co/Qwen/Qwen3-0.6B-GGUF/tree/23749fefcc72300e3a2ad315e1317431b06b590a),
  revision `23749fefcc72300e3a2ad315e1317431b06b590a`;
  `Qwen3-0.6B-Q8_0.gguf`, 639,446,688 bytes, SHA256
  `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`.
  Published LFS metadata and locally read weight bytes match. The card identifies
  `Qwen/Qwen3-0.6B` as base model, Apache-2.0, Q8_0. No local conversion is claimed.
  It is public/ungated at this observation; no authentication or license click
  was used. The coordinator provisioned weights into ignored `models/` only.
- The official Qwen public GGUF listing contained Qwen3-0.6B and Qwen3-4B, but
  neither Qwen3.5-4B-GGUF nor Qwen3.5-0.8B-GGUF. Direct API requests for the latter
  two returned HTTP 401, which does not distinguish an absent repository from a
  private one. This observation is **not** a 404 or proof of all distributions.
  The existing exact Safetensors Qwen3.5-4B conversion prerequisite is preserved.

[Source URLs, raw-byte hashes and licenses](LLAMA_SOURCES_2026-10-22.json) pin
the evidence. Windows Git checked some source files out with CRLF; those working
file hashes differ from the linked raw LF bytes without a tracked source change.
No weights, compiled binary, full template, native diagnostic trace, or hidden
reasoning is committed or redistributed. Bundled runtime dependency licenses
remain with the official source checkout; no new package manager dependency.

## Actual artifact inspection

`python benchmarks/spike/llama/inspect_model.py <reviewed-local-model>` read
GGUF v3 metadata and tensor descriptors, without dumping tensor bytes:

| Field | Actual value |
|---|---|
| Architecture / layers / embedding width | `qwen3` / 28 / 1024 |
| Tensor descriptors | 310: 113 F32, 197 Q8_0 |
| GGUF file type / quantization version | 7 (Q8_0) / 2 |
| Tokenizer family / pretokenizer | `gpt2` / `qwen2` |
| Vocabulary / BOS / EOS / padding | 151936 / 151643 / 151645 / 151643 |
| Add BOS | false |
| Embedded context metadata | 40960; experiment cap remains 4096 |
| Embedded chat template | 4100 UTF-8 bytes; SHA256 `57f1fd00f0013a2be96aa79b857391f27e23df5b5f847072b524c897e24d0361` |

The current official base tokenizer config at revision
`c1899de289a04d12100db370d81485cdf75e47ca` contains a 4168-byte template with
SHA256 `a55ee1b1660128b7098723e0abcd92caa0788061051c62d51cbe87d9cf1974d8`.
It differs from the converted artifact. The helper applies the **actual embedded
template** through the pinned runtime's Jinja API; it does not approximate the
current base template or claim conversion parity without evidence.

## Build and transport

Actual environment: Windows x64; MSVC 19.34.31937.0 from installed Visual Studio
2022 Community 17.4.3; CMake 3.22.1 and Ninja from the existing Android SDK.
Build parallelism was four. CPU backend uses AVX2/FMA/F16C/BMI2 and OpenMP;
other CPU instruction sets/platforms were not tested.

1. Clone the official tag into ignored `target/runtime-spike/llama.cpp` with
   Git's **local command** `-c core.longpaths=true`. Initial checkout without it
   failed on upstream UI path lengths; the owned source checkout/index was
   repaired and verified clean. No global Git or OS setting changed.
2. The official CMake example was configured with static libraries,
   `LLAMA_BUILD_TOOLS=ON`, examples/tests/server/app/UI/OpenSSL/subprocess/
   LLGuidance disabled; RPC, GPU APIs, BLAS, dynamic backends and native CPU
   tuning disabled. Build only `llama-completion llama-tokenize --parallel 4`.
   Startup/version/help passed: `0.7.0 (build 1, commit 620d222)` (shallow count).
   Missing file and synthetic truncated GGUF each exited 1, stdout 0 bytes,
   stderr 209 bytes captured locally and not forwarded/published.
3. `powershell -NoProfile -File benchmarks/spike/llama/build.ps1 -SourceDir
   target/runtime-spike/llama.cpp -BuildDir target/runtime-spike/adapter-build
   -CmakePath <existing-cmake.exe>` built the narrow API helper successfully.
   A repeat ran CMake successfully and Ninja reported no work to do.
   Nonfatal upstream compiler warnings were observed (Windows SDK macro,
   GCC pragmas, and numeric conversions); no source patch suppressed them.

Final local helper binary SHA256:
`7711f91d068445af24ed0edac18ef9995b09131a7ae8bc51514502fa322b7908`.
This identifies this build, not a promise of byte-identical compiler outputs.
The helper follows upstream `examples/simple` batch/decode lifetime rules,
using RAII for model, context, sampler, batch and templates. It calls the local
file API directly and exposes no downloader, socket server or arbitrary tool.
The upstream HTTP utility is still compiled in `common`; this is not a static
claim that every upstream CLI has no networking code. The unused old CURL
switch is deprecated; actual OpenSSL and remote backends were disabled.

Source review caught that the official minimal completion formatter does not
forward reasoning kwargs to its single-message template call. Rather than
trusting a parsed-but-ineffective `--reasoning off` flag, this helper explicitly
sets `inputs.enable_thinking=false` and disables preservation. Actual template
input parts are tokenized with user parts unable to create role-control tokens.
It supplies no tools, starts a fresh role session per invocation, caps actual
input tokens plus reserved output at 4096, and rejects parsed reasoning/tool
output before writing one bounded JSON response. No stdout marker stripping.

A first real schema smoke demonstrated that pure-content chat formatting alone
left `schema_enforced=false` and produced fenced output. The helper was corrected
to install upstream `json_schema_to_grammar` explicitly after chat formatting;
the final verified sample produced parseable `{"ok":true}` and reported the
constraint as installed. Engine validation remains required, independently of
schema enforcement. No production engine rule changed.

## Checks and limits

`python -m unittest discover -s benchmarks/spike/llama -p 'test_*.py' -v`:
**14 passed**. They cover strict worker fields/types/duplicates/size/UTF-8,
missing/corrupt local artifact rejection, output and stderr overflow,
concurrent pipe draining, timeout while a child refuses stdin, malformed native
responses/reasoning, and bounded/truncated GGUF metadata. These tests use
synthetic subprocesses; they are not model benchmark numbers.

`python benchmarks/spike/llama/smoke.py --model <reviewed-local-model>
--executable target/runtime-spike/adapter-build/locallore-llama-spike.exe`:
**7 actual native checks passed**. [Sanitized results](LLAMA_SMOKE_2026-10-22.json)
record three separately loaded generations (schema, narrator, schema reload),
missing/corrupt file failures, over-budget context rejection, and termination/
reaping of a live native process. Final schema/reload each had 24 actual input
tokens and 6 output tokens; narrator had 35 input and 14 output tokens.
Terminated process emitted zero stdout/stderr. A separate real Python-worker
call verified the reviewed model hash and returned installed-schema JSON with
zero worker stderr. The smoke script deliberately withholds generated prose.

Per-process `load_ms` includes model load, template/context/sampler setup;
`generation_ms` includes prefill plus decoding/parsing. It does not split them,
include parent hash verification/engine/persistence, measure high-water memory,
distinguish OS-cold pages from warm pages, or implement a sustained loaded
session. Individual timing samples in JSON are host observations only. No
thermal, energy, phone latency, ARM64, physical memory pressure, Android
backgrounding, full-turn durability, model quality or supported tier is inferred.
The coordinator owns broader shared-fixture/oracle runs and the outer process
tree boundary; see its separate report. M01.01 and device-dependent M01.03–M01.06
remain blocked/pending. M01.02's full comparison and owner acceptance remain open.
