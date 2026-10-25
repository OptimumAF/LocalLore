# Pinned SDK constraint-path research — 2026-10-25

Refs #9 (M05.05), #5 (M01.05). Independent source-research claim
[6400800039](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6400800039)
under root packet6400786067. Sole owned file, branch `review/m05-mask-sdk`,
verified-clean existing worktree based on `090a8694`. This is source evidence,
not an SDK execution, defect attribution, owner acceptance or completed gate.

All LiteRT-LM links below pin `bda624851d74be34d4e1f7fac1fc4155939539c7`.
Its [build dependency](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/components/constrained_decoding/BUILD#L240-L264)
names LLGuidance1.3.0. LLGuidance links pin the corresponding upstream source
`29e33a219f77be1cc37d8394630440f448d19945`. Equal release labels do not prove
identical compiled features or Android/Windows binary behavior. Line numbers
were checked against actual raw source, including blank lines.

## Keep the two observed failures separate

The coordinator's [host-oracle verification](LLGUIDANCE_ORACLE_VERIFICATION_2026-10-25.md)
records an ordinary425-byte schema passing the synthetic byte path. A different
escaped-literal positive fails at65/103; its full-literal const-only reduction
fails at13/48. Preserve both positives and the unchanged schema binding.

The [SDK status verification](LITERT_STATUS_VERIFICATION_2026-10-25.md) instead
records the ordinary real-provider call with425 schema bytes,15 worker-validated
chunks/58 UTF-8 bytes and one wrapper-declared CODE_13. It records neither the
failing native operation nor the token/matcher state at failure. These are
historical coordinator results, not independently replayed by this researcher.
No source correspondence here establishes a common cause.

## The SDK actually masks and commits tokens

| Boundary | What the pinned source establishes |
| --- | --- |
| [ResponseFormat.kt40–47](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/ResponseFormat.kt#L40-L47) | The string overload parses JSON syntax, then preserves the original schema string. This is not independent JSON-schema compiler validation. |
| [Conversation.kt293–327](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/Conversation.kt#L293-L327) | Enabled response format supplies its type/string to the asynchronous native call. Automatic tool handling can suppress a format, but the local owner disables tools. |
| [JNI1119–1121](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/jni/litertlm.cc#L1119-L1121), [1245–1259](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/jni/litertlm.cc#L1245-L1259) | Enabling the feature installs a default LlGuidanceConfig; response type2 becomes a JSON-schema constraint argument. |
| [Provider37–57/142–164](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/components/constrained_decoding/llg_constraint_provider.cc#L37-L164), [conversation397–415](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/conversation/conversation.cc#L397-L415) | Creates the native JSON constraint with `llg_new_constraint_json`, checks its error, and attaches it to decode configuration. This path does not call the separate matcher validation API. |
| [LlgConstraint79–118](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/components/constrained_decoding/llg_constraint.cc#L79-L118) | `llg_compute_mask` determines legal vocabulary tokens; `llg_commit_token` advances the constraint. Either failing C call maps to InternalError. A stopped null mask allows only configured EOS; a nonstopped null mask allows all vocabulary tokens. |
| [Decoder75–143](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/components/constrained_decoding/constrained_decoder.cc#L75-L143) | Applies a computed mask to each batch's logits; state updates consume sampled IDs. The implementation requires sequence length1, and restarts a constraint state after it reports ended. |

The [external-sampling branch](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/core/tasks.cc#L444-L509)
commits the previous decode ID after the first step, masks logits and samples.
The other branch passes the decoder into the executor. The
[compiled-model executor](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/executor/llm_litert_compiled_model_executor.cc#L1367-L1387)
also updates state before masking its next logits, excluding the prefill ID.
This proves a generation-time constraint path in the inspected source; it does
not identify which executor branch or native error site the historical call used.

## Vocabulary, fast-forward, EOS and callback boundaries

The [provider70–135](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/components/constrained_decoding/llg_constraint_provider.cc#L70-L135)
builds token lengths/bytes from `Tokenizer.GetTokens()`, prefixes configured
special strings with0xff, supplies a `TextToTokenIds` callback and declares
`tokenize_assumes_string=false`. Callback errors become a zero-token result.
No model vocabulary was read here. The provider configuration has no explicit
special-token entries in this default path. The
[factory43–58](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/components/constrained_decoding/constraint_provider_factory.cc#L43-L58)
selects the first single-token session stop sequence as EOS when none is supplied.
This differs from the host oracle's byte vocabulary262/EOS261.

The [C tokenizer factory](https://github.com/guidance-ai/llguidance/blob/29e33a219f77be1cc37d8394630440f448d19945/parser/src/ffi.rs#L101-L150)
uses supplied byte strings directly when tokenizer JSON is absent, builds the
trie with the supplied EOS, and selects general slicing when partitions are
unspecified. Its [callback routing](https://github.com/guidance-ai/llguidance/blob/29e33a219f77be1cc37d8394630440f448d19945/parser/src/ffi.rs#L59-L75)
uses the callback directly when `tokenize_assumes_string=false`. The
[C contract215–231](https://github.com/guidance-ai/llguidance/blob/29e33a219f77be1cc37d8394630440f448d19945/parser/llguidance.h#L215-L231)
then requires arbitrary-byte, including invalid-UTF8, tokenization and thread
safety. Source alone does not prove the selected model callback meets that
contract. In particular, the SDK's
[SentencePiece vocabulary](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/support/tokenizer/sentencepiece_tokenizer.cc#L100-L118)
returns model pieces, whereas its
[HuggingFace vocabulary](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/support/tokenizer/huggingface_tokenizer.cc#L95-L105)
queries ID-to-token strings. Neither fact identifies the historical model's
chosen implementation or demonstrates a bad token mapping.

The SDK invokes default constraint initialization without overriding its flags.
Those [actual C defaults](https://github.com/guidance-ai/llguidance/blob/29e33a219f77be1cc37d8394630440f448d19945/parser/src/ffi.rs#L458-L474)
disable fast-forward and backtracking. The SDK does not apply the commit result's
extra token array, but ignored fast-forward tokens are not a demonstrated defect
under those defaults. The distinct
[C matcher API](https://github.com/guidance-ai/llguidance/blob/29e33a219f77be1cc37d8394630440f448d19945/parser/llguidance.h#L454-L485)
has its own construction/validation interface; its documentation says matcher
construction ignores those two flags. A successful matcher validation/consume
comparison cannot replace mask-before-sampling legality.

The local [LiteRtRoleWorker](../../apps/android/app/src/litert/java/org/locallore/app/LiteRtRoleWorker.kt)
uses CPU4, request context/output caps, topK1/topP1/temperature0/seed1, empty tools
and channels, automatic tool calls false, response format true, thinking false
with budget0 and speculative decoding false. It forwards the request schema
and output cap at send. No local EOS, vocabulary, slicing, fast-forward or
chunk-size override is present in that construction. Seed1 does not promise
identical generation across platforms.

[Streaming decode714–753](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/core/tasks.cc#L714-L753)
can omit updates for partial BPE or stop sequences. Hence15 accepted chunks and58
validated application bytes do not locate the failed token, parser offset or EOS
transition. Configured caps, native steps, emitted chunks and accepted bytes are
different quantities. The earlier
[callback research](LITERT_CALLBACK_RESEARCH_2026-10-25.md) documents additional
executor/response-processing routes to the same error family.

## Candidate hypotheses and evidence still required

These are investigation candidates, not diagnoses or permission for an SDK run.

1. **Language-construction path differences.** During this research the
   coordinator reported that the original literal rejects under JSON, default
   Lark and explicit Lark no_forcing, and also fails direct consumption and
   validation; an explicit regex for its serialized JSON bytes accepts with EOS.
   This researcher did not replay that native comparison. For those reported
   cases, mask-versus-consume divergence is not the result, and no_forcing is not
   a fix. Retain the exact same-input/path comparison and failing positives.
   Investigate compiled literal/quoted-string language construction before
   attributing a mask-only bug or transferring a Python-matcher conclusion to
   the SDK's distinct C constraint family. A regex control alone proves neither
   general JSON-schema equivalence nor safe real-model generation.
2. **Real-vocabulary integration.** A multi-byte token boundary, piece-byte
   representation, callback byte-domain mismatch or slice/trie interaction could
   differ from the byte oracle. Establish the actual tokenizer implementation,
   vocabulary-byte conversion, callback contract and compile flags in a separately
   admitted experiment. Source inspection and mocked provider tests cannot supply
   that evidence. Do not infer such a failure merely from GetTokens' name or from
   the existing host escaped-literal rejection.
3. **EOS/stop or decode-state alignment.** Establish the actual selected EOS/stop
   relationship and whether the first failure is mask computation, sampled-token
   commit, executor sampling or response processing. Ended-state reset and delayed
   commit ordering are source mechanisms to examine, not observed errors. Public
   output needs only bounded stage/status/count/consistency metadata; do not
   retrieve private prefixes, generated token sequences, raw native error text or
   logs to fill this gap. Increasing caps or enabling fast-forward/speculation is
   unsupported by current evidence.

### What the existing Kotlin adapter can express

The pinned [public response-format type](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/ResponseFormat.kt#L28-L68)
offers only JSON_OBJECT2 and REGEX1. `ResponseFormat.regex(pattern)` preserves
the supplied pattern, and the JNI mapping above selects `llg_new_constraint_regex`.
Thus a separately admitted regex diagnostic has a source-supported public API;
no actual Kotlin/SDK regex test was performed here. The application currently
always uses the JSON constructor.

There is no exposed Lark/internal-grammar variant in that Kotlin type. Valid JSON
passed to the JSON constructor still reaches the JSON-schema branch, not a
serialized arbitrary grammar: compare
[C dispatch511–525](https://github.com/guidance-ai/llguidance/blob/29e33a219f77be1cc37d8394630440f448d19945/parser/src/ffi.rs#L511-L525)
with [tag dispatch334–341](https://github.com/guidance-ai/llguidance/blob/29e33a219f77be1cc37d8394630440f448d19945/parser/src/api.rs#L334-L341).
Sending Lark text through JSON or fabricating private constraint-type values is
not a supported adapter option.

The schema compiler's optional `x-guidance` override uses the
[closed JsonCompileOptions type](https://github.com/guidance-ai/llguidance/blob/29e33a219f77be1cc37d8394630440f448d19945/parser/src/json/compiler.rs#L22-L33)
and [override reader89–101](https://github.com/guidance-ai/llguidance/blob/29e33a219f77be1cc37d8394630440f448d19945/parser/src/json/compiler.rs#L89-L101).
Its fields concern separators, whitespace, oneOf coercion and leniency; unknown
fields are denied. It exposes no no_forcing, arbitrary Lark or FF setting.
Changing these options can alter accepted language and is not justified by this
research. C-level support for Lark elsewhere does not make it a public Kotlin
feature, and a diagnostic regex does not authorize replacing production schema
binding or the Rust validator.

The next runnable host task is the coordinator's bounded same-input native API
comparison/minimization. A future SDK comparison additionally needs explicit
ownership/admission, exact build provenance and safe causal instrumentation; this
document grants none. The ordinary SDK failure still lacks a native cause, and
its schema passing a host byte path supplies no real-tokenizer qualification.

## Research checks and status

Read instructions/workflow, #3/#9 and current claims; inspected the frozen local
Kotlin source and retained public reports; fetched only pinned official source
and tree metadata in memory. No SDK executable, native import/build/test, model,
tokenizer file, cache, AVD/ADB, private or sealed disk evidence was accessed.
No dependency or implementation file changed. Only this document is committed;
`git diff --check` is the relevant documentation check. M05.05/M01.05 remain
partial/in review; reference-phone and broader execution/quality gates remain
open. The engine continues to validate and commit canonical outcomes; neither
grammar acceptance nor narration changes its authority.
