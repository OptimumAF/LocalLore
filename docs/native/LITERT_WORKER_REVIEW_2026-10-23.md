# LiteRT worker independent review

Refs [#9](https://github.com/OptimumAF/LocalLore/issues/9), M05.05
prerequisite; [#5](https://github.com/OptimumAF/LocalLore/issues/5), M01.02
supporting. Review base `327c99226cc2f7a3b53b203da50670ad4c4c5413`;
reviewer `/root/native_cancel_review`, separate `review/m05-litert-worker`
worktree. The reviewer owns only this report and performed source, publisher
metadata and retained-artifact inspection. Builds, tests, device actions and
model operations belong to their named executors. This report grants no owner
acceptance or production backend selection.

## Publisher and toolchain inspection

The current [official release](https://github.com/google-ai-edge/LiteRT-LM/releases/tag/v0.18.1)
identifies LiteRT-LM 0.18.1 at `bda624851d74be34d4e1f7fac1fc4155939539c7`.
A fresh read of [Google Maven metadata](https://dl.google.com/dl/android/maven2/com/google/ai/edge/litertlm/litertlm-android/maven-metadata.xml)
returned latest/release 0.18.1, lastUpdated `20261020175555`.
The freshly retrieved [publisher POM](https://dl.google.com/dl/android/maven2/com/google/ai/edge/litertlm/litertlm-android/0.18.1/litertlm-android-0.18.1.pom)
matches the cached 1,543-byte artifact SHA256
`3d6ea70f41bc6305c5985a52c5f5d00da97402d6531c9a395f3145cb5c1a89a5`:
Gson 2.14.0, Kotlin reflection 2.4.0 and coroutines Android 1.11.0.

Read-only inspection of the cached 20,905,360-byte AAR independently matched
SHA256 `05c6bdc8acda834efcca12c0ad5d06d2cd8c83e60770f056d8d222f699f3012b`.
Every class inspected in its `classes.jar` has major version 65. A Java 17
output target does not make that SDK readable by a Java 17 compiler or runnable
in a Java 17 host test process. Java 21 compilation and test launchers are
separate from the Java 17 bytecode target and Gradle daemon.

The [current Kotlin matrix](https://kotlinlang.org/docs/gradle-configure-project.html)
lists Kotlin 2.4.0-2.4.10 with Gradle 7.6.3-9.5.0 and AGP 8.5.2-9.1.0;
the proposed Gradle 8.11.1/AGP 8.10.1 combination is within those ranges.
The [Compose compiler instructions](https://developer.android.com/develop/ui/compose/setup-compose-dependencies-and-compiler)
use the same version for Kotlin and its Compose compiler plugin.
[AGP 8.10 compatibility](https://developer.android.com/build/releases/agp-8-10-0-release-notes)
specifies Gradle 8.11.1 and JDK 17. These published ranges do not replace an
actual build of this app's resolved graph.

The isolated 32.4.1 lint graph is a build-only analyzer dependency. The newer
analyzer mechanism remains [experimental](https://googlesamples.github.io/android-custom-lint-rules/usage/newer-lint.md.html).
Its actual task classpath, analyzed SDK/Kotlin dependency model and infrastructure
diagnostics must be checked together; a zero Gradle exit or empty issue report
alone does not establish metadata-compatible analysis. Prior benchmark evidence
is described in [the analyzer report](../runtime/android/LITERT_ANALYZER_2026-10-22.md),
and does not automatically qualify this app's new Kotlin source compilation.

## SDK API and evidence limits

The exact tag's [configuration source](https://github.com/google-ai-edge/LiteRT-LM/blob/v0.18.1/kotlin/java/com/google/ai/edge/litertlm/Config.kt)
exposes CPU threads and engine context capacity, per-conversation output caps,
tool disabling, channels and constrained decoding. A worker must preserve the
native request's prompt/schema/budgets, create fresh conversations and explicitly
disable automatic tool execution. [ResponseFormat.json](https://github.com/google-ai-edge/LiteRT-LM/blob/v0.18.1/kotlin/java/com/google/ai/edge/litertlm/ResponseFormat.kt)
syntax-parses JSON; it does not independently validate the Rust schema's meaning.

The [public Message API](https://github.com/google-ai-edge/LiteRT-LM/blob/v0.18.1/kotlin/java/com/google/ai/edge/litertlm/Message.kt)
exposes content, tool calls and channels separately; `toString()` cannot enforce
the text-only boundary. The SDK's private JSON conversion normalizes the role
and drops unsupported raw content before the adapter sees a Message. Rejection
can therefore cover SDK-visible metadata, not invisible original native fields.
The [conversation implementation](https://github.com/google-ai-edge/LiteRT-LM/blob/v0.18.1/kotlin/java/com/google/ai/edge/litertlm/Conversation.kt)
also marks its object dead before native close returns. A thrown close remains
uncertain even when `isAlive` is false; cancellation does not promise rollback.

There is a further native evidence boundary. The exact [JNI implementation](https://github.com/google-ai-edge/LiteRT-LM/blob/v0.18.1/kotlin/java/com/google/ai/edge/litertlm/jni/litertlm.cc)
invokes Java terminal callbacks before deleting its global reference and
detaching the callback thread. Deletion calls the native object destructor.
The [session destructor](https://github.com/google-ai-edge/LiteRT-LM/blob/v0.18.1/runtime/core/session_advanced.cc)
ignores its wait status, while the [threaded execution manager](https://github.com/google-ai-edge/LiteRT-LM/blob/v0.18.1/runtime/framework/resource_management/threaded_execution_manager.cc)
waits and destroys its owned pools, with wait errors logged/ignored internally.
The [pool destructor](https://github.com/google-ai-edge/LiteRT-LM/blob/v0.18.1/runtime/framework/threadpool.cc)
does call each worker's join and logs failures; this is not a claim that the
SDK omits joining its threads.
Java callback accounting and returned public close calls establish the adapter's
observed SDK lifecycle; they cannot expose those ignored native statuses. Fake
callback tests cannot establish real active-model cancellation, native thread
cleanup or memory reclamation. Those qualifications remain separate.

## License and native packaging findings

The AAR declares Apache-2.0 but carries mixed third-party attribution texts.
Its root `LICENSE` is 16,086 bytes, SHA256
`ec40a2da15ab0e8b44a9f787ab210203d3cad32572f5f99744a88eb90ff9ba4e`;
root `THIRD_PARTY_NOTICE.txt` is 2,198,164 bytes, SHA256
`52a70c82685debf85d4ea9d677615b8636ffd3b75435ce71f247bf5982fb2ba2`.
Neither text is inside `classes.jar`. Their AAR presence is not proof that AGP
includes them in an APK. The concrete review finding was to copy both exact
texts into candidate APK assets and verify the packaged bytes, preserving the
full publisher notices rather than declaring every bundled component Apache.
The upstream [Apache redistribution terms](https://github.com/google-ai-edge/LiteRT-LM/blob/v0.18.1/LICENSE)
require provision of the license and retention of applicable notices; embedded
third-party terms must also remain available. Build-only analyzer licenses are
distinct from redistributed runtime components.
The aggregate notice includes GPL-family, MPL, EPL and runtime-exception texts
alongside permissive licenses; some sections describe source files, build tools
or alternatives. Presence in that aggregate neither proves every listed file
is linked nor supplies a complete binary redistribution analysis. Preserving
the exact texts is required evidence, not release licensing clearance. This
source-only packet must not publish SDK binaries or claim that clearance.

Both AAR JNI libraries have 16,384-byte PT_LOAD alignment. ARM64 library SHA256
is `cf4c55139c6fc86425ecfe75f8a907e6193ca665ecc19fbabcaba7ab361bdc43`;
x86_64 is `ba879b2b46be1f7e08df8c8365a276cfc54c1e21383090e058a24f25e603cdd7`.
Their RELRO ranges occupy a separate matching load segment; subsequent writable
segments begin beyond its rounded 16 KiB boundary. This source-artifact
inspection does not replace checking APK ZIP offsets or executing on a 16 KiB
device. [Android guidance](https://developer.android.com/guide/practices/page-sizes)
distinguishes ELF alignment, APK packaging and runtime verification.

The model identity stays **Gemma 4 E2B**, not Gemma 3n. The exact
[Google model card](https://huggingface.co/google/gemma-4-E2B-it/blob/3e22461f65e89153144f8adb70e3b8c2cc9845a7/README.md)
declares Apache-2.0 and links Google's [license text](https://ai.google.dev/gemma/apache_2).
No weights, model cache, model load or new inference result was inspected or
produced by this reviewer. Existing #117/#119 consumption/preservation holds
remain unchanged; licensing identification is not runtime qualification.

## Implementation and execution review

The first adapter draft had an observed-late-callback propagation defect:
after a successful role close, a late callback marked the worker uncertain but
left the engine able to report successful cleanup. The reviewer supplied
sequences both before and during engine close. The revised draft invalidates
the role proof, retains its physical-close guard, and checks sticky worker
uncertainty before and after engine close, including its idempotent path.
Dedicated regressions cover those observed orderings and are included in the
final JVM result inspected below.

A related post-Ready boundary was raised centrally: a callback observed after
all cleanup returned must also revoke reuse of the paired native owner, rather
than merely preventing the worker's next open. The paired factory now notifies
that same owner outside adapter locks. Its close fences admission synchronously
and schedules native invalidation; that schedule is not itself proof that the
native lease has already closed. The new paired-owner test distinguishes the
immediate control fence, eventual invalidation and an already accepted synthetic
receipt. Already accepted canonical events must not be rolled back.

A subsequent reviewer sequence found that the draft used the poison flag as
both an opening reservation and sticky uncertainty, clearing it after loader
success. A callback from a previously closed role during the next engine's
initialization could therefore erase observed uncertainty. The revised source
separates the opening reservation from poison, never clears observed poison,
checks it after initialization, and retains the initialized but unreturned owner.
The held-loader regression checks the old close proof, new resource retention
and refusal to reopen. Source resolution was independently reviewed and its
regression is included in the final JVM result inspected below.

The reviewer also found that the initial candidate lint configuration omitted
`checkDependencies=true`. The coordinator acknowledged this and is preserving
the initial compatibility attempt before correcting and rerunning the affected
analysis. The explicit candidate notice-copy task verifies AAR/license/notice
hashes, and the final packaged bytes were independently inspected below.

The first actual candidate compiled the adapter and instrumentation, but its
231 JVM cases had 14 failures, all at the helper's null-cause assertion; the
reviewer independently parsed that retained XML. Coroutines 1.11.0
[recovers stack traces](https://github.com/Kotlin/kotlinx.coroutines/blob/1.11.0/kotlinx-coroutines-core/jvm/src/internal/StackTraceRecovery.kt)
by [copying exceptions with the original as cause](https://github.com/Kotlin/kotlinx.coroutines/blob/1.11.0/kotlinx-coroutines-core/jvm/src/internal/ExceptionsConstructor.kt).
The corrected helper accepts at most eight acyclic, exact-class, fixed-message
copies ending in null, and still rejects private SDK causes. Its production
source and lifecycle assertions were unchanged. The matching instrumentation
helper was corrected before device admission. The earlier script-compilation
failure and the initial compatibility attempt remain retained separately.

The coordinator's final offline Android run returned exit 0 with known process
cleanup in 78,844 ms. Independent XML inspection found 24 reports, **231 JVM
tests including all 28 worker cases, zero failures/errors/skips**. Lint reported
zero errors and eight advisories: six Gradle dependency suggestions, one target
API advisory and one AGP-version advisory. No warning suppression was added.
The retained raw script-test log reports 189 passing tests in 17.113 seconds;
the reviewer inspected that result without executing the suite.

The final analyzer audit has 67 entries matching every coordinate/file/size/hash
in the existing frozen analyzer manifest, analyzer 32.4.1 and dependency checking
enabled. The analyzed dependency and library models contain SDK 0.18.1 and Kotlin
reflection/stdlib 2.4.0. Final main analysis was up-to-date from the preceding
candidate analysis; `analysis_did_work=false` is preserved rather than described
as a fresh analysis. The final runtime audit lists 62 artifacts including the
publisher's exact SDK, Gson, reflection and coroutine pins.
The ordinary dependency report independently retains Kotlin stdlib 2.2.21 and
coroutines 1.10.2 without the SDK. Six retained negative probes refused release,
mixed/capacity profiles, wrong cache, missing analyzer pin and automatic Java
toolchain download permission, each with expected exit 1 and known cleanup.

The coordinator subsequently repackaged outputs without source changes, retaining
the prior APK pair. Independent comparison found identical names and decompressed
bytes for all 156 app entries and 121 test entries. Final ZIP/ELF inspection
matched the app APK, 73,776,528 bytes,
SHA256 `945b368f66b90e1788b235dd8f7d692a804538da4a3d29d3cab4ee13dc0d437b`,
and test APK, 1,744,113 bytes,
`6a76dd65b3c9ae9869e6a045a4966e0aff7c230343734acca73b30340a1dee83`.
All six app native libraries have stored 16 KiB ZIP offsets and 16 KiB ELF load
alignment. Both SDK native hashes and both complete notice assets match the AAR
identities above. The test APK carries no native libraries. The retained
signature-verifier captures report successful v2 verification for both exact
APKs; these are coordinator executions inspected by the reviewer. Manifest
inspection is a separate audit from signature verification and installation.

The reviewer independently rehashed the closed host selection: **306 files,
358,364,451 bytes, zero mismatches**. Its 65,310-byte index SHA256 is
`10753184862cf68a24aeacee7e08e972cf69e2296fb793efcbf9f443c7fc6e4a`.
This covers the declared source/scripts/reports/logs/APK selection, including
retained failures; it is not a claim that the live build/cache namespace is
immutable or that unselected files were audited.

## Emulator evidence inspection

Before dispatch, the reviewer independently rehashed all 50 disabled-proposal
bindings with zero mismatches, checked the final source's three method names
and final APK hashes, and reviewed the B-only controller's fixed floors,
27-to-29 package-map boundary, dynamic TEST UID and all-PASS-before-cleanup fence.
The coordinator alone promoted the two authorization flags and dispatched the
single admitted cohort. The promotion changed no other proposal field.

The device executor's owned cohort completed in **13,063 ms**, exit zero with
known cleanup. Independent parsing of the 2,232-byte instrumentation output,
SHA256 `300694b66bbb2c4f5e00d72d902321b15a14e1005f2e0ddcad9262c51892c132`,
found exactly three paired start/PASS records and final runner code -1. All 44
client status/stdout records rehashed correctly and reported completed, exit
zero and known cleanup. The TEST process was already absent; no force-stop ran.
The conditional stop path therefore has host-fixture evidence, not new device
execution. The complete before map had 27 entries; installed/after/final maps
had exactly 29, preserving every prior hash and adding only the final APK pair.
Final userdata availability was 1,542,373,376 bytes, above the unchanged
1,207,959,552-byte floor.

Both successful installation clients recorded nonzero stderr counts, 174 and
196 bytes. The existing capture retained counts but not that content. The
reviewer makes no claim about its cause or a zero-stderr cohort. The outer
runner's stderr count was zero. A local sealing audit initially added an
unrequired zero-stderr assertion; its original failure/script remain retained.
The corrected local audit removed that extra assumption, explicitly recorded
the counts, and preserved dispatch gates and stdout/status/package/test checks.
No device retry or extra query followed that correction.

Independent inspection of the device's closed selection found **134 files,
226,678 bytes, zero mismatches**; every selected file and the index has its
read-only attribute set. The 22,677-byte index SHA256 is
`ae7c26282f95cf52725f3ca0ca6ffe4ff38d34c29043b580771239872e7ed71e`.
This is a bounded selection, not an assertion about every live namespace file.
The [device report](LITERT_WORKER_DEVICE_2026-10-23.md) and
[coordinator verification](LITERT_WORKER_VERIFICATION_2026-10-23.md) retain
execution attribution and limitations.

These methods exercised packaged x86_64 SDK library loading on API 35 with 4 KiB
pages and real Rust/JNI/Host/SQLite failure handling on fresh synthetic paths.
Missing-file/digest/confinement refusal precedes SDK engine construction. The
injected construction counter establishes that ordering; it is not actual SDK
model initialization. The tests establish canonical player-projection equality
and native-owner-slot release before external cleanup, not NPC privacy,
real-generation callbacks, model cancellation, physical-phone performance,
ARM64 execution or 16 KiB device execution. No Compose screen/MainActivity was
selected. No model was initialized, generated with, copied or repaired.

## Disposition

M05.05 runtime-adapter prerequisite and M01.02 supporting work are locally
verified for review within the boundaries above; milestone acceptance remains
unchecked. The ordinary app still selects scripted inference, and this debug
profile chooses no production backend. Existing #117/#119/A/cache holds remain
unchanged. The reviewer performed no build, test-suite, SDK, device or model
execution and changed only this report.

Next runnable product work is trusted model/profile provisioning and application
construction around the paired owner. Real initialization, active cancellation,
cleanup, quality and sustained device qualification require their unresolved
admission gates. No merge, release or repository-access change is authorized
by this review.
