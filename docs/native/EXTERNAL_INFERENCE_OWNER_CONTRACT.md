# External inference on the app workspace owner

Refs [#9](https://github.com/OptimumAF/LocalLore/issues/9), M05.05 prerequisite
and M05.04 supporting; [#5](https://github.com/OptimumAF/LocalLore/issues/5),
M01.02 supporting. This adds a trusted app-construction boundary, not a selected
production SDK or a claim that a model is loaded.

## One gameplay owner

The app's workspace handle owns the existing Rust Host, validated SQLite store,
sessions, fork operations and story/branch invalidation. An external provider
must attach to that same lease. A second experimental registry cannot replace
it while leaving archive/fork operations attached to the first registry.

Ordinary `open(path)` explicitly configures the existing scripted fixture.
Trusted `openLocal(path, profileBytes)` instead configures the external provider
before any session opens. Configuration failure fails closed; it never selects
scripted inference. Neither model output nor Host JSON can choose paths,
profiles, SDKs, executables or provider factories.

The existing `call`, `close` and borrowed `forkHandle` continue using the same
owner. Generation stays outside canonical locks and storage transactions.
Only the existing guarded Rust pipeline interprets and validates proposed
commands, narration and commits. Accepted events and validated projections
remain authoritative; summaries and model replies cannot replace them.

## Narrow native requests

`pollInference(handle)` returns the same immutable pending ticket and structured
request until a one-shot response is accepted. The request carries version,
role, prompt, max_tokens, context_tokens, threads and schema. Preserve the exact
Rust schema and original scope/turn/revision/profile binding; the worker cannot
choose another request. `respondInference(handle, ticket, bytes)` accepts bounded
strict UTF-8 only for that active owner's ticket. Foreign, stale, cancelled,
duplicate or closed tickets fail closed. Closing or invalidating the native
session makes its pending ticket ineligible; late worker output must be discarded.

Bounds: profile 4,096 bytes, worker request 32,768 bytes, poll reply 40,000 bytes,
worker response 16,384 bytes. Existing Host input/output bounds remain separate.
JNI checks array bounds before copying. Native code retains no Java references,
model resources or worker threads. Profile provenance describes trusted
configuration; it does not establish model-file integrity or successful load.

## Preparation and resource ownership

The optional Android owner runs blocking native preparation and external role
work independently off Main. While a role runs, it checks the native ticket so
story/branch deletion and native cancellation also cancel and drain the worker.
The caller's coroutine cancellation alone is insufficient evidence that a
blocking loader or runtime has stopped.

Returning native Ready to the ViewModel requires known role terminal state,
drain and role close, engine close, and joined native preparation. Otherwise the
ViewModel could commit while model resources remain uncertain. Cleanup runs on
failure and cancellation, including Error paths. Unknown ownership permanently
quarantines commit/reuse and cannot trigger a new generation or fixture fallback.
Uncertain cleanup also invalidates the native lease, including handles borrowed
by fork operations. Recovery cannot reuse a poisoned lease or select a scripted
provider. The gateway retains its original pending turn key on this fixed
uncertainty exception. Already accepted outcomes remain saved; cancellation
never promises rollback.

One owner reserves exactly one transport before native allocation; its transport
reservation and native-port binding are atomic. Each turn has one engine and
fresh role calls. A single whole cleanup deadline bounds the sequence. Cancellation
is skipped for a role already proven terminal and closed. A cancelled waiter is
not proof of worker terminal state: the worker must report an actual terminal
result, including a terminal empty result when cancellation discards generation.
Late allocation tasks remain tracked, and an undrained child prevents claiming
its parent engine safely closed.

The injected worker contract makes these states testable without an SDK. A
future SDK adapter must establish them from actual callbacks and resource joins;
returning a Boolean in a fake test is no real-model ownership measurement.

## Runtime and device gates

This boundary adds no runtime, model, SDK or dependency choice. MainActivity
continues using explicit scripted construction. Existing LiteRT-LM 0.18.1
experiments use Java 21 to read major-65 classes and resolve Kotlin 2.4 metadata;
they do not qualify adding that graph to this app's Kotlin 2.2.21 dependencies.
The exact prepared model is Gemma 4 E2B, distinct from older Gemma model families.
Actual SDK integration, model import/integrity, storage admission, physical-phone
performance, active-model cancellation and narrative quality stay separate.

Local-copy permission was already used in earlier work. The preserved A model
mismatch and the #117 consumption/#119 preservation failures are unchanged;
this boundary admits no new inference, copy or repair. No player data, model
weights, private paths or raw diagnostics belong in public reports.

Current official compatibility references (no dependency added here):
[LiteRT-LM 0.18.1 release](https://github.com/google-ai-edge/LiteRT-LM/releases/tag/v0.18.1),
[publisher POM](https://dl.google.com/dl/android/maven2/com/google/ai/edge/litertlm/litertlm-android/0.18.1/litertlm-android-0.18.1.pom),
[Kotlin/Gradle compatibility](https://kotlinlang.org/docs/gradle-configure-project.html),
[exact prepared artifact revision](https://huggingface.co/litert-community/gemma-4-E2B-it-litert-lm/tree/a790a852d433991c0c0a41c1154cf9b3850300fa),
and [Gemma 4 E2B model card](https://huggingface.co/google/gemma-4-E2B-it/blob/3e22461f65e89153144f8adb70e3b8c2cc9845a7/README.md).
The SDK adapter must resolve its actual toolchain/dependency graph independently;
this contract does not qualify mixing that graph into the ordinary app.
