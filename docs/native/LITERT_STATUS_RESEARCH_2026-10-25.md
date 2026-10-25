# Pinned wrapper-declared status research — 2026-10-25

Refs #9 (M05.05), #5 (M01.05). Root claim/explicit prefix decision 6399899218;
independent research claim 6399916466. Sole reviewer-owned file on
`review/m05-declared-status`, from `3c808389992f8ddb1f071daf6d2ccbb94d6c8a05`.
This is public-source/privacy review, not an implementation test, SDK result,
error diagnosis or owner acceptance.

## Exact pinned source and license

The candidate still uses LiteRT-LM 0.18.1, public revision
`bda624851d74be34d4e1f7fac1fc4155939539c7`. Primary sources were read over HTTP
without persisting a checkout or changing dependencies.

| Source | Verified fact |
| --- | --- |
| [SDK LICENSE](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/LICENSE) | The pinned repository carries Apache License 2.0. SDK source headers identify the same license. This is separate from model licensing. |
| [Final exception, line25](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/LiteRtLmJniException.kt#L25) | A final-by-default Kotlin RuntimeException subclass accepts a message and exposes no numeric status property or custom getter. |
| [Kotlin callback, lines652–658](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/Conversation.kt#L652-L658) | Code1 becomes CancellationException. Other codes construct the final SDK exception with fixed wrapper text before the private payload. |
| [Async JNI marshaller, lines1318–1325](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/jni/litertlm.cc#L1318-L1325) | Native code is a separate integer argument. Its other argument comes from `status.message()`, not a code-prefixed `ToString()` representation. |
| [Synchronous start refusal, lines1333–1338](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/jni/litertlm.cc#L1333-L1338) | Failed start throws through a different formatted exception path; it does not establish an asynchronous callback. |

The public wrapper prefix is exactly `Status Code: <integer>. Message: `.
The declaration is Kotlin wrapper output; its prefix is not an Absl label
copied from the native message argument. Existing JNI warning logging is also
distinct from this diagnostic channel; no logs or actual error payload were
read for this research.

## Deliberately new, bounded privacy boundary

The released #170 record correctly states that it never retrieved or parsed
Throwable.message. This packet's explicit root decision separately permits a
narrower new operation: only for the pinned final SDK exception type, retrieve
its existing message reference once and compare complete fixed public prefixes
for codes0–16. It does not reinterpret the historical no-access finding.

The inspected producer draft checks final SDK type before the getter, stores
the reference only in a local, and uses17 literal `startsWith` comparisons.
Each includes the complete punctuation and trailing space before the payload.
There is no substring, split, trim, regex, generic numeric parse, search within
the message, logging, snapshot field or callback retaining that reference.
The classifier never inspects payload characters after a complete prefix.
No memory erasure or whole-process secrecy guarantee is implied by local scope.

Foreign exceptions, cancellation exceptions and wrappers around an SDK cause
return UNRECOGNIZED before any getter access. No cause traversal is allowed.
The SDK class is final; an arbitrary hostile subclass cannot substitute a
message getter for this eligible class. Disabled/null receipt status tracing
must skip the classifier entirely, so the regular/default path gains no getter
access. These are concrete control-flow requirements, not a blanket permission
to inspect private error text elsewhere.

Literal full delimiters distinguish code1 from10, reject signed/padded/unknown
codes and tolerate no leading whitespace or normalization. Malformed prefixes
stay UNRECOGNIZED. Empty, huge, Unicode, control or deceptive content after a
valid prefix must remain opaque rather than trigger payload validation. The
comparison bound depends on the17 public literals, not payload length.

## Trust and authority limits

Any application code can construct the final SDK exception with a matching
prefix. Therefore CODE_0 through CODE_16 are **wrapper-declared observations**,
not authenticated native status, error cause or SDK-entry proof. A constructed
CODE_0 is not success. Actual pinned cancellation uses a different exception
branch, so a constructed CODE_1 is not proof of cancellation or its ACK.
UNRECOGNIZED is not harmlessness or a reusable owner. Old callback provenance,
send-site and worker observations remain independent.

Even a genuine native status is many-to-one. For example, pinned LLGuidance
[construction](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/components/constrained_decoding/llg_constraint_provider.cc#L127-L159)
and [commit/mask](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/components/constrained_decoding/llg_constraint.cc#L79-L129)
errors share InternalError with other SDK paths. The bridge cannot select a
decoder, grammar, token/EOS, capacity, cancellation or model cause from that
category. Prior observed61 output bytes and21 chunks are not token counts.

A structured upstream API retaining the already separate integer would remove
the textual-format dependency and improve provenance. A fork instead adds SDK
patch/build/reproducibility/maintenance and fresh verification work; no such
build is performed or needed merely to express this bounded application-side
observation. The chosen bridge uses the existing pinned public type and changes
no native binary, dependency or model. It remains brittle to wrapper format/API
changes and must be re-reviewed when the dependency pin changes, not generalized
to arbitrary Throwable formats.

## Actual draft review and required counterexamples

The read-only root integration calls the unchanged original error Boolean first,
then its old closed category, then optional status recording in a suppressed
finally. Original callback failure identity survives diagnostic failure. Only
the explicit receipt Candidate creates/stores the final status trace; null
default owners skip the getter. There is no native getter, alternate factory,
resource release, retry, schema or budget change in the inspected draft.

The producer codec retains only18 enum counts with overflow-only saturation,
defensive immutable snapshots and2048-byte ASCII prefix-plus-JSON bound.
The independent new1340 decoder preserves absence versus explicit zero, exact
fields/types/overflow order and adjacency, refusing a failure-only record beside
an OK runner. CODE_0 never promotes a positive proof. Old1337/1338/1339 channels
remain separate. No concrete source blocker was found in these drafts; this
does not qualify a later frozen integration or an actual runtime outcome.
The producer handoff is `9a2e5cff25e2c5e1a06e35c1d18378dd2e3d11e8`;
its final contract explicitly separates this prefix access from historical
PR170. The root integration reviewed here is still an uncommitted draft.

Meaningful source/test cases include all17 exact prefixes; empty/large/private
Unicode or control payload; leading whitespace, case changes, missing spacing,
negative/plus/padded/17+ and prefix-in-payload refusals; code1/10 collisions;
foreign/hostile/cancelled/wrapped getters never accessed; original callback
throw plus diagnostic throw; disabled trace bypass; fence/category/status
ordering; immutable/concurrent bounds and saturation; absent versus zero;
and malformed or persistence-failed transport retaining raw without proof or
later dispatch. Producer/host tests may construct synthetic SDK exceptions but
must not call that native status authentication or SDK execution.

This reviewer ran no tests, build, Gradle, SDK executable, ADB/AVD, native getter,
model/image/disk/cache-content operation or current-error/logcat inspection.
Only public HTTP and static synthetic source were read; no sealed evidence was
modified. Root owns central compilation, actual validation, any fresh grant and
the later independent outcome review. Full Dialogue/reopen, phone and milestone
gates remain open, and prior error causes remain unknown.
