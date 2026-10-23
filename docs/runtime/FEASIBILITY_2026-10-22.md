# M01 feasibility preparation — 2026-10-22

This preserves the initial source-preparation observations below. Later on the
same date, the [host runtime spike](spike/README.md) verified local model bytes
and exercised actual Windows CPU calls. Its evidence supersedes the initial
"not loaded/downloaded" observations for those exact host artifacts only;
the original source manifest remains a dated provenance record. No phone
qualification or production backend selection follows.

Status: **source verification and host tooling only; no production backend selected**.
M01.01–M01.03 remain incomplete. No model was loaded or benchmarked. No weights
were downloaded. Exact metadata and source hashes are in
[source-manifest.json](source-manifest.json); published artifact digests have not
been verified against local weight bytes.

## Accessible hardware

The read-only probe found ADB outside PATH in the standard Android SDK location.
Two authorized transports both reported `sdk_gphone64_x86_64`, Android 15,
`ro.kernel.qemu=1`, and SoC `ranchu`. They are emulators. No authorized physical
candidate was found. No serial numbers, transport IDs, private diagnostics, app
data, or personal content were printed or committed. The initial PATH-only
absence observation was insufficient and is superseded by this inventory.

`powershell -NoProfile -File benchmarks/inspect-device.ps1` reports
`status=blocked`, `authorized_count=2`, `emulator_count=2`, and
`physical_candidate_count=0`. The script deliberately returns nonzero for an
unavailable/ambiguous physical target. It never pairs, installs, pushes files,
roots, reboots, or downloads. ADB may start its local daemon. This is device
discovery, not a device benchmark or proof about every disconnected phone.

Reference-phone OS/chipset/RAM tier, available resources, thermal/power state,
inference compatibility, cancellation, full-turn latency, peak memory, and the
30-minute sustained session are **blocked on an authorized physical phone and
provisioned, hash-verified model/runtime**. Emulators cannot pass those gates.
Kernel-visible `MemTotal` must not be presented as the physical retail RAM tier.

## Pinned comparison paths

Stable releases were resolved through official GitHub REST metadata on
2026-10-22. Pin commits, not moving `main`, `master`, `latest.release`, or an
unpinned model repository. These are experiment inputs, not app dependencies.

| Runtime | Exact stable source pin | Candidate path | Evidence and remaining test |
|---|---|---|---|
| LiteRT-LM v0.18.1 | `bda624851d74be34d4e1f7fac1fc4155939539c7` | Prepared Gemma 4 E2B `.litertlm` bundle | Official runtime has CPU/Android build instructions and constrained-decoding C++ API. Actual bundle load, tokenization, schema coverage, backend behavior and cleanup untested. |
| llama.cpp v0.7.0 | `620d2225cc436ab0b001e3200e590e3b286ef9ab` | Official Qwen3.5-4B Safetensors -> local text GGUF -> proposed Q4_K_M | Pinned converter registers `Qwen3_5ForConditionalGeneration`; loader has `qwen35`. Conversion, quantization, tokenizer parity, and physical backend execution untested. |

The llama.cpp release uses annotated tag object
`757cad021b357f417065ddbc41a6e8f87c1f8136`, which resolves to the commit above.
The converter is now split into `conversion/qwen.py`; inspecting only the root
`convert_hf_to_gguf.py` misses architecture registrations.
See the [pinned Qwen converter](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/conversion/qwen.py),
[architecture registry](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/src/llama-arch.cpp),
and [Android example/build instructions](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/docs/android.md).

Gemma's upstream `Gemma4ForConditionalGeneration` includes multimodal components;
the E2B/E4B text configurations are dense. Use text only for the first comparison.
The `.litertlm` candidate is a separate packaged conversion, not arbitrary GGUF or
the upstream Safetensors file. The official Google runtime documentation links
the LiteRT Community packages. Start with generic
`gemma-4-E2B-it.litertlm`; device-specific Tensor/Qualcomm/Intel variants require
matching backends and cannot establish compatibility for other chips. E4B is a
separate, optional larger experiment. The E2B publisher describes mixed 2/4/8-bit
mobile quantization; exact loaded tensor/backend metadata still needs inspection.
No exact E4B quantization was established in this packet.
See the [prepared E2B package](https://huggingface.co/litert-community/gemma-4-E2B-it-litert-lm/tree/a790a852d433991c0c0a41c1154cf9b3850300fa)
and [prepared E4B package](https://huggingface.co/litert-community/gemma-4-E4B-it-litert-lm/tree/e6a3892a8c22cf87ff99583996149cf3cb32452b).

Qwen3.5-4B is the dense hybrid-attention `qwen3_5_text` configuration, not the
separate MoE architecture. The base tokenizer configuration names
`Qwen2Tokenizer` with `<|im_end|>` EOS. Gemma names `GemmaTokenizer` with `<bos>`,
`<eos>`, and `<pad>`. Preserve the exact upstream tokenizer files and
`chat_template.jinja`; the manifest hashes the small configuration/template
sources. Generated GGUF must retain the intended template and produce matching
token IDs on fixed text/role fixtures. An embedded template is not proof of
tokenizer/template parity. The prepared Gemma package's embedded tokenizer has
not been inspected. Qwen defaults to thinking; explicitly test the published
non-thinking template option and enforce a total output/deadline cap. Do not
store hidden reasoning. The compact 4k profile is a project hypothesis, not the
model publisher's recommended long-context reasoning profile.
See the [pinned Qwen configuration](https://huggingface.co/Qwen/Qwen3.5-4B/blob/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a/config.json),
[tokenizer configuration](https://huggingface.co/Qwen/Qwen3.5-4B/blob/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a/tokenizer_config.json),
and [model instructions](https://huggingface.co/Qwen/Qwen3.5-4B/blob/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a/README.md).

LiteRT-LM's pinned C++ docs expose tool constraints and custom LLGuidance JSON
Schema/regex/Lark constraints. This does not establish identical custom-schema
availability in Kotlin/JNI. llama.cpp documents a subset of JSON Schema and
silently ignored unsupported features. Test the exact LocalLore v1 schema and
always parse and validate output in the engine. No runtime tool executor is
authorized by model function calls.
See [LiteRT-LM constrained decoding](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/docs/api/cpp/constrained-decoding.md)
and [llama.cpp grammar limitations](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/grammars/README.md).

## License and artifact gate

| Component | Source-declared license | Distribution evidence still required |
|---|---|---|
| LiteRT-LM source | Apache-2.0 | Inventory exact binary/transitive libraries, notices, build provenance, optional accelerator terms. |
| llama.cpp source | MIT | Preserve license and inventory enabled libraries/backends and conversion dependencies. |
| Official Qwen3.5-4B revision | Apache-2.0, exact `LICENSE` available | Record local conversion command/tool/dependencies, output hash, tokenizer/template and notices. |
| Gemma 4 official and prepared candidate cards | Apache-2.0 metadata at recorded revisions | Verify full applicable notices and package provenance before redistribution; no standalone `LICENSE` file appears in these pinned model trees. |

Source-license checks are not an approval to redistribute unknown binaries or
weights. No model artifacts are bundled. Exact license-source hashes are in the
manifest; Gemma license metadata is in its pinned README. See [LiteRT-LM LICENSE](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/LICENSE),
[llama.cpp LICENSE](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/LICENSE),
and [Qwen LICENSE](https://huggingface.co/Qwen/Qwen3.5-4B/blob/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a/LICENSE).

## Next runnable work

Run the host contract suite and the benchmark utility tests independently of a
phone. On the next authorized provisioned physical target, run the inventory,
confirm its RAM tier, verify local artifact bytes, and execute the compatibility
checklist in [EVALUATION_PROTOCOL.md](EVALUATION_PROTOCOL.md). M01.04–M01.06 and
real-model M01.02/M01.03 remain pending; source availability cannot choose a
supported profile or satisfy performance/quality gates.

## Executed verification

- Python 3.9.12: `python -m unittest discover -s benchmarks -p 'test_*.py' -v`
  passed all five tests. Numbers in calculator tests are invented unit data;
  manifest tests validate metadata shape/pins, not runtime/model compatibility.
- PowerShell's `System.Management.Automation.Language.Parser.ParseFile` accepted
  `benchmarks/inspect-device.ps1` with zero syntax errors. The actual probe ran
  and returned the blocked inventory above, with no hardware benchmark.
- `git diff --check` passed after staging the owned files.
- Official GitHub release/ref APIs and Hugging Face pinned tree/raw APIs were
  read. SHA256 and byte counts were computed over 25 small source documents,
  capped at 2 MiB each. No weight URLs were fetched. Source-hash integrity does
  not prove downstream binary provenance or exact model execution.
