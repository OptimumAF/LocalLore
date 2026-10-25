# LLGuidance host-oracle source research — 2026-10-25

Refs #9 (M05.01/M05.05), #5 (M01.05). Independent reviewer
`/root/model_picker_review`; root claim6400493037, review claim6400555516.
Research base `3f20b5744a38b33e07c1d8990705ab900360b676`.

An isolated LLGuidance1.3.0 byte-token oracle is a suitable next compiler check
for exact engine-produced Dialogue schemas. It can establish host compilation
and byte-language examples; it cannot establish the actual Gemma tokenizer,
LiteRT/JNI integration, successful generation, or the cause of the prior
wrapper-declared INTERNAL13. This report is source research, not an executed
compiler result or permission to relax a production gate.

## Version, license and packaging

The pinned LiteRT-LM revision
`bda624851d74be34d4e1f7fac1fc4155939539c7` names
[`llguidance-1.3.0` in its constraint dependency](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/components/constrained_decoding/BUILD#L240-L264).
The public upstream tag v1.3.0 resolves to commit
`29e33a219f77be1cc37d8394630440f448d19945` in the
[official tag reference](https://api.github.com/repos/guidance-ai/llguidance/git/ref/tags/v1.3.0).
Equal version numbers do not prove equal build features, tokenizer state or
the SDK's complete native execution path.

The pinned [LICENSE](https://github.com/guidance-ai/llguidance/blob/v1.3.0/LICENSE)
is MIT and requires retention of its copyright/permission notice with copies
or substantial portions. The host tool does not change LocalLore's license.
Retain the wheel's license metadata when provisioning its isolated directory.

The official [PyPI1.3.0 metadata](https://pypi.org/pypi/llguidance/1.3.0/json)
declares Python>=3.9, no required distribution dependencies, and this unyanked
WindowsAMD64 artifact:

- Filename: `llguidance-1.3.0-cp39-abi3-win_amd64.whl`.
- Published size: 2,789,946 bytes.
- Published SHA256: `1d1cd1c8618d1a13605d3e057c978651e551c8c469b481ee4041f1d6c436002d`.
- [Exact wheel URL](https://files.pythonhosted.org/packages/5a/7e/809349638231f469b9056c0e1bfd924d5ef5558b3b3ec72d093b6fad33b1/llguidance-1.3.0-cp39-abi3-win_amd64.whl).

The [Python extension manifest](https://github.com/guidance-ai/llguidance/blob/v1.3.0/python_ext/Cargo.toml#L1-L24)
uses PyO3's `abi3-py39` extension mode. These are published compatibility and
integrity expectations, not a reviewer download, local artifact hash, import,
or successful ABI-load observation. Root must separately verify downloaded
bytes, ZIP members/metadata and the actual interpreter/architecture before
loading code. A verified wheel avoids source-build dependencies; the source
[pyproject](https://github.com/guidance-ai/llguidance/blob/v1.3.0/pyproject.toml#L1-L25)
would otherwise require a build backend.

## Keep the exporter outside the compiler dependency graph

LLGuidance's [parser manifest](https://github.com/guidance-ai/llguidance/blob/v1.3.0/parser/Cargo.toml#L10-L17)
enables `serde_json/preserve_order`. Adding it to the engine's Cargo graph,
including an unreviewed dev-dependency, could change serialization feature
selection and the bytes being measured. Build the real-engine exporter using
the unchanged production dependency graph, freeze its raw `schema_json`
strings, then pass that corpus into the separately provisioned Python tool.
Do not regenerate schemas with a Python dictionary or add lenient/options
overrides to make examples pass.

The current author draft `crates/locallore/examples/llguidance_cases.rs` was
read directly in its separate worktree. It captures actual Director
`Input::Structured` requests through `play::execute`, refuses at the provider,
and verifies unchanged canonical bytes/revision/receipt count. Its post-gift
case first accepts an original synthetic gift through the real engine path;
it does not copy a failed device's private prompt. Its independent bitmask
reference covers all nonempty eligible sets of size<=4 for n1..6, including
30/56 sets for n5/n6. The escaped literal, representation negatives, and three
provider-free refusal controls are useful distinct checks. Eight tests were
authored in that draft; this reviewer did not execute them or certify a later
changed draft. Prompt data is not retained by its capture object.

## Correct API and byte semantics

The Rust binding special-cases exact `LLTokenizer("byte")` before the
[file-backed tokenizer branch](https://github.com/guidance-ai/llguidance/blob/v1.3.0/python_ext/src/py.rs#L34-L64).
This constructor needs no HuggingFace tokenizer, tokenizer file or network.
That source fact is narrower than guaranteeing all imports are isolated:
the launcher must still control package/module provenance and search paths.

The [builtin vocabulary](https://github.com/guidance-ai/llguidance/blob/v1.3.0/toktrie/src/tokenv.rs#L153-L177)
has byte IDs0..255 followed by six test special tokens. Its total vocabulary
is262 and EOS is261, not256. Exact UTF8 bytes can therefore be consumed as
their numeric byte IDs. Verify those runtime properties in the admitted tool
and keep special tokens out of sample bytes; no tokenizer-file substitution
is needed.

`grammar_from_json_schema` packages schema JSON; compilation must occur
separately. The binding's validator invokes native grammar validation, while
constructor failures can become sticky matcher error states. Mask computation
can fall back to an EOS-only mask on error, and consuming EOS on an already
stopped matcher can return true. Consequently neither constructor success,
an EOS bit, nor EOS consumption alone proves acceptance. For every sample,
require an initially error-free matcher; check the mask bit before each byte,
consume that byte, and check errors again. After all bytes, require
error-free `is_accepting()`, an allowed EOS bit and successful EOS handling;
check errors after mask computation and after EOS consumption too.
The relevant implementation is
[validation/packaging](https://github.com/guidance-ai/llguidance/blob/v1.3.0/python_ext/src/llmatcher.rs#L277-L375)
and [mask/consumption](https://github.com/guidance-ai/llguidance/blob/v1.3.0/python_ext/src/llmatcher.rs#L223-L235).
The API stub's exception wording conflicts with the sticky-error implementation.

Packed bit indexing is `mask[token//8] & (1 << (token%8))`, as used by the
[upstream matcher tests](https://github.com/guidance-ai/llguidance/blob/v1.3.0/python/torch_tests/test_matcher.py#L357-L405).
Use bounded safe mask bytes rather than pointer APIs. A fresh matcher per
sample avoids contamination from a previously rejected sample.

LLMatcher supplies
[default inference capabilities](https://github.com/guidance-ai/llguidance/blob/v1.3.0/python_ext/src/llmatcher.rs#L239-L260),
whose [booleans default false](https://github.com/guidance-ai/llguidance/blob/v1.3.0/toktrie/src/lib.rs#L14-L32).
It has no LLInterpreter-style `enable_ff_tokens` argument. Avoid forced-token
helpers and untested byte splices.

## Controls, privacy and interpretation

The pinned [JSON-schema documentation](https://github.com/guidance-ai/llguidance/blob/v1.3.0/docs/json_schema.md#L63-L85)
fixes property order to schema order and excludes leading/trailing whitespace
by default while permitting internal whitespace. Preserve raw sample bytes;
do not strip whitespace or sort/rebuild objects before testing. Check property
reordering and outer whitespace separately as representation controls.
Duplicate/permuted audience rejection by the grammar does not change the
engine's existing typed BTreeSet normalization or make the grammar canonical
authority.

The old unsupported `uniqueItems` schema is a useful compile-refusal control:
packaging alone must not earn it credit. Invalid/incomplete byte samples must
be rejected by a compiled grammar, not merely reported as a generic exception.
Unexpected faults, compilation refusal and expected sample rejection need
separate closed outcomes. Strict corpus keys, finite IDs, bounded total bytes,
schema/sample lengths and sample counts are required before native calls.
Native compilation needs an outer owned timeout; a Python deadline between
calls cannot preempt a blocking native call.

Compiler errors can contain grammar or input excerpts. Public output should
contain closed outcomes, counts, sizes and hashes only, with no arbitrary
exception text/stack, prompt, schema or sample echo. Original public synthetic
corpus bytes may be retained deliberately as source fixtures, separately from
the bounded result. Control package imports and capture child output before
interpreting it; cleanup uncertainty cannot become a passing run.

This research performed public HTTP source/metadata reads and static local
source review only. No wheel was downloaded or imported by this reviewer; no
build, native compiler, SDK/ADB/AVD/model/cache/image/disk operation occurred.
The next runnable gate is root's verified isolated provision and bounded
actual compiler/corpus run, followed by independent result review. Even a
complete byte-oracle pass leaves the real SDK/Gemma-tokenizer path and earlier
INTERNAL13 cause unproven. Full milestone and phone gates remain open.
