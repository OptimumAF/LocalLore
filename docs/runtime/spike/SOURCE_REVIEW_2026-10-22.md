# Independent source review: M01.02/M01.03 host spike

Checked 2026-10-22 by the separate `review/m01-spike` worktree, starting at
`3a7cb82`. This is source review, not owner acceptance, a runtime benchmark, or a
supported phone/model decision. No model bytes or executable were acquired or
loaded by this reviewer during these checks.

The 25 small sources in the existing runtime manifest were fetched independently
from their exact URLs with a 2 MiB response cap. All 25 byte lengths and SHA256
digests matched. The companion JSON records those checks. In particular, the
LiteRT-LM Apache-2.0 and llama.cpp MIT license files match the previously recorded
bytes. Their licenses do not inventory the transitive components of a future
binary.

The official release APIs still identify LiteRT-LM `v0.18.1` and llama.cpp
`v0.7.0` as their latest releases at review time. Their tag references resolve to
the pinned commits below; a release's branch-valued `target_commitish` is not a
substitute for resolving its tag.

| Runtime | Resolved commit | License |
|---|---|---|
| LiteRT-LM v0.18.1 | `bda624851d74be34d4e1f7fac1fc4155939539c7` | Apache-2.0 |
| llama.cpp v0.7.0 | `620d2225cc436ab0b001e3200e590e3b286ef9ab` | MIT |

Sources: [LiteRT-LM release API](https://api.github.com/repos/google-ai-edge/LiteRT-LM/releases/latest),
[LiteRT-LM tag](https://api.github.com/repos/google-ai-edge/LiteRT-LM/git/ref/tags/v0.18.1),
[llama.cpp release API](https://api.github.com/repos/ggml-org/llama.cpp/releases/latest),
[llama.cpp annotated tag](https://api.github.com/repos/ggml-org/llama.cpp/git/tags/757cad021b357f417065ddbc41a6e8f87c1f8136).

## Prepared Gemma candidate

The [pinned publisher tree](https://huggingface.co/api/models/litert-community/gemma-4-E2B-it-litert-lm/tree/a790a852d433991c0c0a41c1154cf9b3850300fa?recursive=true)
independently confirms `gemma-4-E2B-it.litertlm`, 2,588,147,712 bytes, with LFS
SHA256 `181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`.
That is a publisher digest, not a hash of local weight bytes. The exact
[prepared card](https://huggingface.co/litert-community/gemma-4-E2B-it-litert-lm/raw/a790a852d433991c0c0a41c1154cf9b3850300fa/README.md)
matches the existing manifest. It identifies the base model and mixed mobile
quantization; actual tensor types, tokenizer, backend load and memory use still
require inspection of the local bundle and executed runtime.

The [upstream card](https://huggingface.co/google/gemma-4-E2B-it/raw/3e22461f65e89153144f8adb70e3b8c2cc9845a7/README.md)
also declares Apache-2.0 and links Google's
[Gemma 4 license page](https://ai.google.dev/gemma/docs/gemma_4_license), which
currently presents Apache License 2.0. The pinned prepared tree has no separate
LICENSE file. This supports a local development experiment; redistribution would
need the complete package/build notices and provenance review.

## Smaller llama.cpp development candidate

The official Qwen publisher provides an already converted small GGUF that avoids
making an unmeasured Qwen3.5-4B conversion a prerequisite for exercising the host
boundary. This is a separate development candidate, not a replacement production
selection or an equal-model performance comparison.

The [exact publisher tree](https://huggingface.co/api/models/Qwen/Qwen3-0.6B-GGUF/tree/23749fefcc72300e3a2ad315e1317431b06b590a?recursive=true)
contains `Qwen3-0.6B-Q8_0.gguf`, 639,446,688 bytes, LFS SHA256
`9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`.
The [card](https://huggingface.co/Qwen/Qwen3-0.6B-GGUF/raw/23749fefcc72300e3a2ad315e1317431b06b590a/README.md)
identifies base model Qwen/Qwen3-0.6B and Apache-2.0. Its SHA256 is
`44adabae2153c3a7bb741b86fbffd48736bc95118831935fdfc4d3cc1854f2f5` (6,236 bytes).
The exact [LICENSE](https://huggingface.co/Qwen/Qwen3-0.6B-GGUF/raw/23749fefcc72300e3a2ad315e1317431b06b590a/LICENSE)
has SHA256 `5de36594c10839788a8c589443a8ef9d8b8d17c65a1b5807206ae037fc36c6bd`
(11,544 bytes). Local byte verification, GGUF metadata inspection, templating,
tokenizer behavior and successful inference are separate execution gates.

## Offline and reasoning flags

The pinned [llama.cpp argument definitions](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/common/arg.cpp)
include explicit `--offline`, `--reasoning off`, `--no-reasoning-preserve`,
`--no-display-prompt`, `--no-perf` and `--simple-io` controls. The host adapter
should use fixed reviewed flags, explicit local files and a sanitized environment
rather than accept arbitrary extra arguments. An offline flag and source review
are not a network trace or an OS network sandbox. Hidden reasoning must not be
retained or published even when a runtime/model ignores a requested mode.

An independent implementation check confirmed a caveat found by the runtime
agent: the pinned minimal
[completion tool](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/tools/completion/completion.cpp#L242)
calls `common_chat_format_single`, whose
[fresh formatting inputs](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/common/chat.cpp#L636)
do not carry the parsed reasoning options. Conversely, disabling conversation
mode bypasses that formatting path. Merely passing `--reasoning off` is therefore
insufficient evidence of non-thinking formatting in this tool. A constrained
adapter must apply the exact inspected template with explicit reasoning settings
or restrict a verified formatter to the supported artifact and message subset.
The completion tool also emits a terminal marker; that transport detail must not
be mistaken for model-generated proposal JSON.

The output, context and process deadline bounds apply independently of grammar
constraints. The Rust oracle must still validate typed proposals. A successful
model load alone cannot satisfy M01.03 quality or physical-device gates.
