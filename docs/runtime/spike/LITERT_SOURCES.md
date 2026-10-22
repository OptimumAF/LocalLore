# LiteRT-LM spike sources and artifact identity

Checked 2026-10-22 for M01.02, supporting M01.03. No production dependency or
backend selection is introduced. No weights are redistributed.

The official [v0.18.1 release](https://github.com/google-ai-edge/LiteRT-LM/releases/tag/v0.18.1)
is stable, published 2026-10-20. The official
[tag reference](https://api.github.com/repos/google-ai-edge/LiteRT-LM/git/ref/tags/v0.18.1)
resolves directly to `bda624851d74be34d4e1f7fac1fc4155939539c7`, the existing
research pin. Its GitHub release has Apple framework assets; it supplies no
Windows CLI executable. The pinned build guide calls for Bazel 7.6.1, VS 2022
and Python 3.13 for a Windows C++ source build. That toolchain is unnecessary for
the official Python wheel used in this bounded experiment.

The official [Python API guide](https://developers.google.com/edge/litert-lm/python)
supports Windows and points to the
[litert-lm-api package](https://pypi.org/project/litert-lm-api/0.18.1/).
The package's [release metadata](https://pypi.org/pypi/litert-lm-api/0.18.1/json)
declares Python >=3.10, Apache-2.0, and no `Requires-Dist` dependencies. The
package ownership is `google-ai-edge`; its homepage is the official repository.
The API wheel avoids installing the separate CLI/builder packages and their
additional Python dependencies. This machine's existing bundled Python 3.12.14
was used in a worktree-local venv; no system package or PATH change was made.

| Artifact | Bytes | SHA256 |
|---|---:|---|
| `litert_lm_api-0.18.1-py3-none-win_amd64.whl` | 26403799 | `2c786288b0e41291e52a611a51a6ab6ec755a3196b86c60d5269779010042895` |
| Installed `litert-lm.dll` | — | `a226cbead46a2eef152f3009aa0a83262f1c2123f108aa3385bbdba07d427bd3` |

The wheel's published digest matched downloaded local bytes before installation.
The immutable official wheel URL and byte/hash check are in
`benchmarks/spike/litert/provision.py`. The installed Python files below matched
the exact upstream commit byte for byte. This ties the Python API to the pin;
it is not a reproducible-build claim for the publisher's compiled DLL.

| Pinned upstream source | Bytes | SHA256 |
|---|---:|---|
| [LICENSE](https://raw.githubusercontent.com/google-ai-edge/LiteRT-LM/bda624851d74be34d4e1f7fac1fc4155939539c7/LICENSE) | 11357 | `c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4` |
| [python/litert_lm/engine.py](https://raw.githubusercontent.com/google-ai-edge/LiteRT-LM/bda624851d74be34d4e1f7fac1fc4155939539c7/python/litert_lm/engine.py) | 17547 | `5a4b3dbc6749086334e084d132c6d34596a0572a694b2ea039211f85d4f7b0c3` |
| [python/litert_lm/conversation.py](https://raw.githubusercontent.com/google-ai-edge/LiteRT-LM/bda624851d74be34d4e1f7fac1fc4155939539c7/python/litert_lm/conversation.py) | 20211 | `cb2eb733a44b7fd921e8d85b796729a06529119f8c682dcf371276c5aa51ed93` |
| [python/litert_lm/model_info.py](https://raw.githubusercontent.com/google-ai-edge/LiteRT-LM/bda624851d74be34d4e1f7fac1fc4155939539c7/python/litert_lm/model_info.py) | 13362 | `87058c500fc56ccf96cf8ff16b30f0df6e39cfa0cb9a987d959f658d81c0e7b4` |
| [runtime/core/tasks.cc](https://raw.githubusercontent.com/google-ai-edge/LiteRT-LM/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/core/tasks.cc) | 41306 | `bd731f46d33272bbfc0f2ae4a951c7b042db58360403b902e0d08732a993134e` |

`Engine` exposes CPU thread count, total-token capacity, tokenizer/BOS/EOS, and
explicit close. `Conversation` exposes native template rendering, output cap,
thinking configuration, constrained JSON, token counts and close/cancel.
Native `Prefill` rejects an input token tensor at or above the engine limit;
it does not silently truncate that input. Decode stops at total/output limits.
The worker also checks templated input plus output reserve before generation.

The API's `ModelInfo` reports supported modalities/backends, context capacity,
minimum runtime version and thinking/function-call capabilities. It does not
expose per-tensor quantization or a tokenizer/template artifact digest. The
publisher's mixed-precision statement is therefore source evidence until a
separate bundle inspection provides actual tensor metadata. Supported API
settings do not by themselves prove the exact model loads or generates.

Upstream source and package metadata declare Apache-2.0. The wheel also contains
DirectX/compiler and Intel dispatch DLLs, which this CPU worker does not select.
Its `.dist-info` has no bundled license/notice files. This development experiment
does not redistribute the wheel or those DLLs; a production distribution must
review their separate notices and obligations rather than treating the package
metadata as a blanket license for every vendor binary. Android dependencies and
production packaging remain outside this worker's scope.
