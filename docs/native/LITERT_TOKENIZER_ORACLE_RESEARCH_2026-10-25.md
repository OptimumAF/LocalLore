# Actual-tokenizer comparison: source contract — 2026-10-25

Refs #9 (M05.01/M05.05), #5 (M01.05 supporting). Independent research claim
[6402516423](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6402516423),
root6402500798. Sole new document on `review/m05-tokenizer-oracle`, clean base
`1c3602fd`. The existing worktree is `LocalLore-control-review` under the shared
workspace; the requested D-drive spelling did not exist. Earlier branches remain.

This is a source-supported implementation roadmap, not model inspection or a
native result. No trusted original model source, old target, tokenizer artifact,
cache, image or SDK installation was opened. No download, import, build, test,
SDK/device call or inference occurred. The ordinary425B SDK failure after15
validated chunks/58 UTF8 bytes/declared INTERNAL13 remains unexplained; the host
escaped-literal counterexample is separate. See the dated
[mask-path research](LITERT_MASK_PATH_RESEARCH_2026-10-25.md),
[host literal verification](LLGUIDANCE_LITERAL_VERIFICATION_2026-10-25.md), and
[phase-duration review](FINITE_REGEX_PHASE_DURATION_REVIEW_2026-10-25.md).

SDK source links pin `bda624851d74be34d4e1f7fac1fc4155939539c7` (0.18.1).
LLGuidance links pin `29e33a219f77be1cc37d8394630440f448d19945` (1.3.0).
Raw source, including blank lines, determined line anchors. Version labels alone
do not prove binary build features or Android/Windows equivalence.

## Smallest useful next path

Prepare a bounded, selected-section container reader using the existing Python
standard library. After synthetic malformed/valid-format tests and a separate
explicit source-read admission, read only the file header and selected tokenizer
and LlmMetadata ranges from the trusted original source into a fresh private
output root. Never invoke generic unpack. If the selected artifact is HF JSON,
reuse the already verified isolated LLGuidance wheel to compare the original
ordinary schema and original synthetic examples against its real vocabulary.
Keep semantic-HF and raw-piece controls distinct; neither is automatically the
SDK's complete tokenizer/constraint path.

This does not require loading model graphs/weights, creating an inference engine,
installing Python `tokenizers`, resolving a HuggingFace ID or rebuilding the SDK.
It does require a newly implemented/tested reader and explicit access to the
model's selected ranges. Nothing in this research grants that access or claims
the real bundle's tokenizer type, section count, EOS or vocabulary size.

## Exact container layout and selection

The [core constants](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/python/litert_lm_builder/litertlm_core.py#L24-L31)
and [official header reader](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/python/litert_lm_builder/litertlm_peek.py#L90-L122)
establish:

| File range | Meaning |
| --- | --- |
|0–7|Eight literal bytes `LITERTLM`|
|8–19|Three little-endian uint32 major/minor/patch values; current source1.7.0|
|20–23|Padding|
|24–31|Little-endian uint64 absolute header-end offset|
|32–header_end|FlatBuffer metadata; its own root offset is relative to this region|

The [FBS schema](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/schema/core/litertlm_header_schema.fbs#L68-L164)
defines root slots0=`system_metadata`,1=`section_metadata`; SectionMetadata
slot0=`objects` vector. SectionObject slots are0=`items` vector,1=`begin_offset`
uint64,2=`end_offset` uint64,3=`data_type` uint8. Implicit enum values are
SP_Tokenizer4, LlmMetadataProto5, HF_Tokenizer_Zlib6; TFLiteModel3 and
TFLiteWeights7 must never have their payload read by this experiment.
KeyValuePair slots are0=key string,1=union discriminator,2=union table;
StringValue discriminator9 points to a table with slot0=value string.
Section ranges are absolute half-open file intervals.

[FlatBuffers internals](https://flatbuffers.dev/internals/#tables) require a
signed int32 vtable displacement subtracted from the table address; a shared
vtable can follow the table. Vtable sizes/slot offsets are uint16. Root/table/
vector/string references are relative uint32 offsets; strings have uint32 byte
length and trailing NUL. Omitted slots use schema defaults, not guessed offsets.
Validate every reference, object extent, count and arithmetic operation inside
the bounded header buffer. Do not require fixed field order or positive vtable
displacement, and do not confuse vector counts with byte lengths.

Section starts are16KiB aligned. The
[actual builder1323–1358](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/python/litert_lm_builder/litertlm_builder.py#L1323-L1358)
uses ceiling alignment; if one section ends exactly on a block boundary, the next
may start there. This is less strict than the FBS comment's wording. Enforce
header separation, nonnegative ordered extents, no section overlap and file-size
bounds without inventing an additional empty block. Record the actual version;
agree a supported-version policy rather than silently treating future versions
as the pin. The C++ reader checks major compatibility, not exact1.7.0 equality.

The [loader's buffer-key handling](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/util/litert_lm_loader.cc#L136-L188)
and [tokenizer fallback418–446](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/util/litert_lm_loader.cc#L418-L446)
select `model_type=tf_lite_prefill_decode`, case-normalized, with an untyped
tokenizer fallback for the base model. A tokenizer for audio/vision is not the
text tokenizer. The [resource factory178–214](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/components/model_resources_litert_lm.cc#L178-L214)
prefers SP when present/enabled, then HF. Read the unique LlmMetadata section
separately; its loader key is untyped. Fail closed on duplicate keys, duplicate
eligible sections, conflicting typed/untyped choices or unavailable build-feature
knowledge; do not silently choose a different tokenizer to get a pass.

HF payloads contain **uint64 little-endian uncompressed length followed by zlib**,
not a bare zlib stream. The
[builder1172–1188](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/python/litert_lm_builder/litertlm_builder.py#L1172-L1188)
writes that prefix; [native decompression337–363](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/schema/core/litertlm_read.cc#L337-L363)
consumes it. Bound both lengths before allocation, then require exact decoded
length, stream completion, no trailing/concatenated stream and strict UTF8 JSON.
SP payload is serialized SentencePiece ModelProto, not HF JSON; refuse an HF-only
oracle route on SP rather than converting or guessing a tokenizer.

## Reader closure and provenance requirements

The upstream generic peek/unpack loop can dump TFLite graphs and weights too;
it is not a selected-section command. A small reader should first validate the
entire section *directory* without reading unselected payloads, then read only
the selected tokenizer and LlmMetadata. Suggested initial development caps are
header4MiB/256 sections/64 items per section, metadata1MiB, tokenizer32MiB
compressed/128MiB decoded. These are proposed policy bounds, not observations
or format limits; exceedance must refuse and trigger explicit plan revision.

Require a no-link regular source, fresh create-only output root, bounded exact
reads, one captured file handle and stable identity/size/mtime before/after;
retain fixed error enums and range/length/hash metadata without path/template/
tokenizer text. Preserve original section bytes and decoded JSON separately.
Hash only admitted selected bytes; citing an earlier full-model digest does not
re-authenticate current weight bytes. Source-file provenance must be supplied
by the coordinator's trusted-source admission, not invented from a file name.
No recursive scanning, shell unpacker or dependent old-target/model/cache read.

Meaningful synthetic reader checks include malicious root/vtable/vector offsets,
negative/shared vtable placement, omitted fields, wrong unions, duplicate sections,
exact-boundary alignment, overlaps/EOF/header aliases, oversized length/deflate
bombs, truncated or trailing streams, source mutation and partial-write cleanup.
Instrument the fake reader to prove no read overlaps a weight range. Do not
credit an expected invalid input when the parser actually crashed or ran out of
resources.

## Stop/EOS metadata must follow the SDK order

[LlmMetadata fields1–2](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/proto/llm_metadata.proto#L97-L103)
are start_token and repeated stop_tokens. Each
[TokenUnion](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/proto/token.proto#L19-L40)
contains token_ids field1 (TokenIds repeated int32 IDs field1) or token_str field2.
The bounded wire subset must handle packed and unpacked int32 forms, preserve
order, cap lengths/varints, reject negative/out-of-vocabulary IDs and conflicting
oneof/duplicate singular fields. Unknown protobuf fields need bounded wire-type
skipping; malformed lengths/groups cannot become empty-success metadata. See
[official wire encoding](https://protobuf.dev/programming-guides/encoding/).

The [SDK metadata conversion272–305](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/engine/engine_settings.cc#L272-L305)
tries exact TokenToId for strings, then TextToTokenIds, without reordering.
[Session stop collection716–725](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/engine/engine_settings.cc#L716-L725)
retains nonempty ID sequences. The
[constraint factory43–58](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/components/constrained_decoding/constraint_provider_factory.cc#L43-L58)
chooses the first singleton stop as EOS when no explicit EOS is supplied. Thus
byteEOS261, a guessed `<eos>`, or whichever HF JSON special looks plausible is
insufficient. Resolve strings by validated exact raw-vocabulary lookup; refuse
unresolved fallback cases until equivalent tokenization is available. This is
a deliberately narrower experiment, not a reimplementation of all SDK metadata.

## Two tokenizer modes, with different claims

**Semantic HF artifact control.** Public
[LLTokenizer construction35–64](https://github.com/guidance-ai/llguidance/blob/29e33a219f77be1cc37d8394630440f448d19945/python_ext/src/py.rs#L35-L64)
accepts a JSON string beginning `{` in memory, plus explicit EOS/vocabulary/slice
arguments. Its [ByteTokenizer46–71](https://github.com/guidance-ai/llguidance/blob/29e33a219f77be1cc37d8394630440f448d19945/toktrie_hf_tokenizers/src/lib.rs#L46-L71)
uses Tokenizer::from_bytes, but removes Prepend normalizers. It also
[decodes ByteLevel/ByteFallback pieces and marks special tokens120–177](https://github.com/guidance-ai/llguidance/blob/29e33a219f77be1cc37d8394630440f448d19945/toktrie_hf_tokenizers/src/lib.rs#L120-L177).
Vocabulary padding through n_vocab must not hide a mismatch. Compare general
slices versus explicitly disabled slices as separately labeled controls.

That branch performs local JSON deserialization, not from_file/from_pretrained:
the [underlying tokenizers API443–453](https://github.com/huggingface/tokenizers/blob/v0.21.2/tokenizers/src/tokenizer/mod.rs#L443-L453)
separates those operations. No model-ID lookup, filename fallback or external
vocabulary fetch belongs in the admitted JSON route. Require exact JSON shape,
supported decoder/model configuration and a leading `{`; preserve the original
artifact. Unsupported features must refuse, not install/download another backend.
This avoids a new Python tokenizer dependency; it does not prove equivalence to
the SDK's native tokenizer version, normalizer or adapter bytes.

**Raw-piece vocabulary control.** The SDK
[HF GetTokens95–111](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/support/tokenizer/huggingface_tokenizer.cc#L95-L111)
returns ID-to-token strings, including added-token vocabulary size. Its
[SP GetTokens113–122](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/support/tokenizer/sentencepiece_tokenizer.cc#L113-L122)
returns raw model pieces in index order. Neither decodes metaspace, ByteFallback
names or ByteLevel encodings there. The SDK
[provider70–125](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/components/constrained_decoding/llg_constraint_provider.cc#L70-L125)
uses those UTF8 strings unchanged, adding0xff only for configured special strings;
the JSON response-format path uses default empty special_tokens. Its callback
uses TextToTokenIds and declares tokenize_assumes_string=false.

This continues through the SDK's pinned
[tokenizers-cpp v0.1.1 dependency](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/WORKSPACE#L444-L450):
[ID-to-token237–251](https://github.com/mlc-ai/tokenizers-cpp/blob/v0.1.1/rust/src/lib.rs#L237-L251)
returns the underlying raw string, with an absent ID becoming empty. No hidden
decoder conversion occurs at that boundary. HF SDK
[TextToTokenIds56–76](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/support/tokenizer/huggingface_tokenizer.cc#L56-L76)
calls encode with add_special_tokens=false; the dependency's
[encoder142–151](https://github.com/mlc-ai/tokenizers-cpp/blob/v0.1.1/rust/src/lib.rs#L142-L151)
requires valid UTF8 with unwrap. This conflicts with the arbitrary-byte callback
contract implied by false, but does not prove invalid input occurred. A panic or
piece mismatch is not an established explanation of the observed INTERNAL13.

Public LLTokenizer can receive a
[TokenizerWrapper](https://github.com/guidance-ai/llguidance/blob/29e33a219f77be1cc37d8394630440f448d19945/python/llguidance/_tokenizer.py#L5-L36)
whose properties supply raw byte tokens, EOS, optional BOS and special IDs.
The [binding261–307](https://github.com/guidance-ai/llguidance/blob/29e33a219f77be1cc37d8394630440f448d19945/python_ext/src/py.rs#L261-L307)
constructs the trie from them, so a checked contiguous HF JSON vocabulary plus
added-token mapping can supply SDK-equivalent raw strings. Validate IDs and
conflicts; do not let a sparse/unsupported model layout silently become another
vocabulary. Set special IDs empty for the default SDK provider control, not HF's
automatic special set.

Exact public construction is `LLTokenizer(wrapper, slices=...)`, not a tokens
keyword. The object must expose `is_tokenizer_wrapper=True`, `tokens:list[bytes]`,
`eos_token_id:int`, `bos_token_id:int|None`, `special_token_ids:list[int]`, and
be callable as `(text:str)->list[int]`. EOS must be non-None or the binding
appends an empty token. Constructor n_vocab/eos_token overrides apply only to the
string branch; supply the wrapper properties explicitly and check the resulting
vocabulary/EOS. No decoder-name heuristic can replace these source contracts.

**Remaining fidelity gap:** its
[Python callback321–327](https://github.com/guidance-ai/llguidance/blob/29e33a219f77be1cc37d8394630440f448d19945/python_ext/src/py.rs#L321-L327)
uses UTF8 plus greedy fallback. Reusing the semantic HF tokenizer as callback
also inherits the normalization changes above. This is not the SDK C callback's
arbitrary-byte behavior. Label this a raw-vocabulary comparison, not a faithful
SDK oracle. A full C adapter would require the exact raw token bytes, original
tokenizer callback, EOS, slices and C constraint API; exported wheel symbols and
ABI availability have not been inspected here. Do not begin a broad SDK build
or use raw function pointers as an unreviewed shortcut.

One concrete conditional hypothesis is that raw piece names lack ASCII-space
representations that the decoded semantic vocabulary has, affecting the ordinary
speech literal while action IDs need none. That must first be checked on the
admitted artifact and corresponding mask state;58 emitted bytes do not prove it.
Keep the original ordinary candidate and all existing positives/negatives. An
alternative JSON serialization with `\u0020` for a decoded space can be a
separately labeled representation control after admission, never a replacement
positive or an assumed production workaround. The current finite regex and
JSON-schema paths can accept different representation sets; compare explicitly.

## Existing tools, dependencies and licensing

Repository [host-worker provenance](../runtime/spike/LITERT_SOURCES.md) and
[verification](../runtime/spike/LITERT_VERIFICATION.md) record a previously
verified Windows0.18.1 API wheel and actual host usage. The pinned Python Engine
has [tokenize/detokenize488–505](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/python/litert_lm/engine.py#L488-L505),
but these require an engine pointer, not a standalone metadata tokenizer. They
are unsuitable for quietly satisfying this no-engine/no-old-target step. Existing
benchmark wrappers provide owned deadlines/output/error handling, not a selected
tokenizer extractor. Historical installed state is not a fresh availability check.

The [official builder0.18.1 metadata](https://pypi.org/pypi/litert-lm-builder/0.18.1/json)
declares Python>=3.10, Apache-2.0 and protobuf/flatbuffers/absl-py/tomli dependencies.
Its published platform-independent wheel is41527B,
SHA256`2f3b15ab0f0532acc0ee74f5c3a9573abad45342f23d866d43436e83c28f926c`.
No installed builder or resolved dependency versions were verified here. Adding
it requires separate pin/license review; the stdlib selected reader avoids that
new dependency graph. Generic unpack also has broader data/output scope.

The already preserved LLGuidance1.3.0 WindowsABI3 wheel is2789946B,
SHA256`1d1cd1c8618d1a13605d3e057c978651e551c8c469b481ee4041f1d6c436002d`;
[official metadata](https://pypi.org/pypi/llguidance/1.3.0/json) declares
Python>=3.9 and no required distributions. Its
[upstream license](https://github.com/guidance-ai/llguidance/blob/29e33a219f77be1cc37d8394630440f448d19945/LICENSE)
is MIT. The embedded HF adapter declares tokenizers0.21.2 with default features
disabled in its [manifest](https://github.com/guidance-ai/llguidance/blob/29e33a219f77be1cc37d8394630440f448d19945/toktrie_hf_tokenizers/Cargo.toml#L10-L19).
Reuse the coordinator's existing exact interpreter/runtime verification rather
than assuming today's source-reading Python qualifies the native wheel. No new
dependency is selected or installed by this document. Tool licenses do not
relicense extracted model tokenizer data; keep derivatives private and preserve
the model's separate terms. Model redistribution is not part of this path.

## Public response-format conversion and next command shape

The SDK [value object](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/ResponseFormat.kt#L28-L68)
exposes type, type.value and schemaOrPattern; REGEX1 and JSON_OBJECT2 are the only
variants. Kotlin
[send314–326](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/Conversation.kt#L314-L326)
forwards those properties. The
[JNI1245–1259](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/jni/litertlm.cc#L1245-L1259)
maps1→regex and2→JSON Schema, then native constraint creation uses that type.
The application's format-kind observation can prove its actual prepared public
argument; it cannot prove JNI entry, token bytes or masks. This researcher owns
none of that implementation.

Proposed **not yet implemented or executed** coordinator-owned command shape:

```text
<existing-python> -I -S -B <new-selected-reader> extract
  --source <explicitly-admitted-trusted-original.litertlm>
  --output <fresh-private-root> --model-type tf_lite_prefill_decode
<verified-llg-python> -I -S -B <new-owned-oracle> compare
  --runtime <existing-verified-1.3.0> --extraction <fresh-private-root>
  --corpus <unchanged-ordinary-and-original-controls> --output <fresh-results>
```

Only after reader acceptance/admission, the actual public call can be
`LLTokenizer(exact_json_string, eos_token=resolved_eos, slices=[])` with the
strictly observed vocabulary size checked, then a separate default-slice control.
Compile/validate the unchanged schema, compute each token's mask before consume,
retain first divergence/sticky errors/acceptance/EOS consistency, and require known
owned-process cleanup. Compare semantic and raw modes with closed numeric/hash
reports; do not publish vocabulary strings, template, model paths or private
generated IDs/prose. No passing result alone diagnoses the prior SDK failure.

Source research and staged `git diff --check` are this document's checks; no
runtime tests are claimed. The next safe action is implementation plus original
synthetic extraction/adapter tests, followed by a separately granted selected
source read. Full M05.05/M01.05 and physical-phone/quality gates remain open.
