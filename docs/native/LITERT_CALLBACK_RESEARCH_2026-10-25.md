# Pinned SDK callback and accounting research — 2026-10-25

Refs #9 (M05.05), #5 (M01.05). Root claim 6399434479; independent research
claim 6399442616. Sole reviewer-owned file on `review/m05-callback-observation`,
from `11d3fc1e994de151799e0747cac27d7655209216`. This is source research and
review, not an SDK execution, implementation acceptance or completed play gate.

## Proven public API boundary

All SDK links below pin `bda624851d74be34d4e1f7fac1fc4155939539c7`, the existing
LiteRT-LM 0.18.1 candidate. No dependency, runtime or model choice is changed.
Line anchors use the actual raw/GitHub source line numbers; a browser text
extractor previously omitted blank lines and reported smaller line numbers.

| Source | Proven behavior |
| --- | --- |
| [Conversation.kt 652–658](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/Conversation.kt#L652-L658) | Native callback status 1 becomes `CancellationException`; other statuses become `LiteRtLmJniException` with status/text embedded in its message. |
| [LiteRtLmJniException.kt 25](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/LiteRtLmJniException.kt#L25) | A message-only RuntimeException subclass, final by Kotlin default; no public numeric status property. |
| [Conversation.kt 682–696](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/Conversation.kt#L682-L696) | Benchmark access and KV token count invoke native functions. Token count includes prefill and decode; it is not a pure input-token estimate. |
| [Config.kt 262–284](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/Config.kt#L262-L284) | Conversation output-token override is optional and must be positive when present. |

Finite local type membership can safely map to closed categories
`CANCELLED`, `SDK_JNI`, `OTHER`. Check cancellation first, preserving subclasses
and the original cancelled Boolean. The JNI category describes an exposed SDK
exception family, not an exact native status, phase or error cause. `OTHER`
does not mean non-native, harmless or reusable. Missing observation means
unobserved, not success. No message parsing, `javaClass.name`, reflection,
`toString`, cause/suppressed traversal or stack access is needed.

There is no approved method here to recover the native numeric code from the
public Throwable. Parsing its string is not an alternative status API. No pure
token-count method was found in the inspected pinned Kotlin API; native KV or
benchmark getters add operations and cannot be invoked on an uncertain owner.

## Native provenance is many-to-one

The [JNI callback adapter](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/jni/litertlm.cc#L1283-L1339)
passes non-OK conversation status code/text to Kotlin and then disposes its
callback global reference. Empty successful messages signal completion; other
messages are streamed. A synchronous failure to start throws through a separate
path. Neither callback-reference disposal nor Kotlin callback return establishes
the application's conversation/engine close, drain or native reclamation.

Several distinct constrained-decoding operations collapse to InternalError:
[tokenizer/constraint construction](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/components/constrained_decoding/llg_constraint_provider.cc#L127-L159),
[token commit and mask computation](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/components/constrained_decoding/llg_constraint.cc#L79-L129).
Other model/executor/conversation failures can traverse the same status path.
Therefore even a future `SDK_JNI` observation cannot isolate one of these causes.
An observed returned send followed by message callbacks narrows the application
boundary reached; it does not disclose where a later error originated.

The JNI adapter itself logs a status at its warning site. The new closed channel
can promise that it exports no private error text; it cannot promise that the
entire pinned SDK never logs text. Capturing raw logs to recover hidden status
or prose is outside this design. No device logs were read for this research.

## Output limits and completion are distinct

The positive configured override is forwarded into native optional arguments
([JNI 1236–1237](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/jni/litertlm.cc#L1236-L1237))
and into decode configuration
([conversation.cc 365–366](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/conversation/conversation.cc#L365-L366)).
It is a configured cap, not measured usage.

The native decode loop stops for stop tokens, benchmark configuration, KV bound
or output-step limit
([tasks.cc 92–114](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/core/tasks.cc#L92-L114),
[749–753](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/core/tasks.cc#L749-L753)).
In this streaming implementation, its final state is max-num-tokens only when
the current KV step reaches the maximum; otherwise it returns done, including
an output-cap stop ([829–833](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/core/tasks.cc#L829-L833)).
The loop can skip a text update for partial byte/stop sequences; message chunks
are not a one-to-one count of decode tokens
([714–746](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/core/tasks.cc#L714-L746)).

The internal callback can turn KV-max into ResourceExhausted when its explicit
flag is true; that flag defaults false
([callback 319–340](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/conversation/internal_callback_util.cc#L319-L340),
[configuration 277–278](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/conversation/conversation.h#L277-L278)).
Completion also parses the accumulated response and may forward a processor
error instead of final success
([callback 130–148](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/conversation/internal_callback_util.cc#L130-L148)).
These are source alternatives, not a diagnosis of the prior real Dialogue error.
No evidence here selects grammar, EOS, truncation, context exhaustion, model,
cancellation or capacity as its cause. This research justifies no budget change.

## Minimal safe observation design

1. At the existing admitted role boundary, capture only closed role and actual
   configured context/output caps, plus bounded prompt/schema UTF-8 byte lengths.
   Keep the actual request, schema, prompt, identifiers and paths out of snapshots.
   These are pre-rendered application bytes, not tokenizer usage, model context
   occupancy or complete SDK-rendered input size.
2. Bind a bounded observation handle to that actual owned call. Never obtain a
   mutable global current-call handle from a callback; no reset/replacement or
   setter may redirect observations after Activity/process changes.
3. Preserve the exact original error Boolean and call error handling first.
   Only afterward record the finite category in a suppressed diagnostic block.
   A diagnostic exception cannot replace any original callback exception or
   defer the existing owner fence. Categories grant no close/commit/reuse power.
4. Count only text bytes/chunks that passed the original role/content/UTF-8,
   cumulative output and think-marker checks. Reuse the existing bounded byte
   conversion where possible. Such totals omit rejected/filtered content and
   are not all generated output, raw callback counts or token counts.
5. Treat DONE and categories as historical notifications. Preserve independent
   worker/send traces and their distinct clock origins; do not impose invented
   cross-channel terminal/close consistency. Keep the strict positive runner,
   canonical proof grammar, raw-first retention and stop-on-persistence-failure.

A source-only read of the coordinator's then-uncommitted integration found no
concrete semantic blocker in these points: `observedLiteRtError` invokes the
original error Boolean before its guarded category callback; request accounting
is after existing admission; the handle is captured per actual OwnedCall;
validated-output accounting follows original checks; DONE accounting follows
the original callback's finally. Candidate construction/getter is receipt-only,
nullable and does not replace the owner. This is not a frozen-commit review or
compile/test result, and later changes require their own source verification.

## Required counterexamples and handoff

Meaningful checks should cover hostile Throwable accessors; cancellation
subclasses; final SDK exception versus OTHER; classification with no private
access; original callback throw plus diagnostic throw; quarantine visible before
category; invalid, late and post-terminal chunks earning no validated bytes;
malformed UTF-16; bounded overflow/saturation and immutable concurrent snapshots;
same-call identity despite later call creation; DONE then throw/error histories;
and missing versus zero observation. A decoder must reject unknown keys/types,
oversized/malformed/private strings and passing transcripts with failure-only
records. Retained raw must survive refusal without promoting a partial proof.

Read-only checks performed: repository instructions/workflow and current issue
claims/specifications; local production source/diff; HTTP reads of pinned public
SDK/native source. No test, build, Gradle, SDK executable, device, model, image,
AVD disk or cache-content action occurred. No dependency/source download was
persisted, and no sealed evidence was modified. Prior real evidence remains the
dated 56/122 partial result; complete Dialogue/reopen, phone and milestone gates
remain open. Root owns implementation, actual verification and any fresh grant.
