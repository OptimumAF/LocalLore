# Native cancellation through Compose, 2026-10-23

Refs [#9](https://github.com/OptimumAF/LocalLore/issues/9), M05.04 partial,
and [#8](https://github.com/OptimumAF/LocalLore/issues/8), M04.04 supporting.
Prerequisite: unmerged [#125](https://github.com/OptimumAF/LocalLore/pull/125),
exact `c9aa4c5429c7f8bcf3924e8fdc21732fa9266e96`.

## Executable native boundary

The six new NativeCancelControlsTest methods render LocalLoreScreen with actual
ShellViewModel, DurableGateway and production NativeWorkspaceTransport, JNI,
Rust Host and SQLite. Inference remains the existing deterministic fake.
No production code, dependency, schema, wire contract or permission changed.
The application APK is byte-identical to #125; this packet adds executable
native integration coverage rather than manufacturing a production correction.

Each fixture creates a unique contained child of app-private noBackupFilesDir
and overrides applicationContext/noBackupFilesDir for the production transport.
It seeds real accepted dialogue at revision one and retains its two messages
and the player's potion. Holds apply only after actual native preparation is
ready, or after real cancellation has returned; they delay reply delivery.
These are not active real-model generation or process-death tests.

Three methods corrupt only the delivered cancellation acknowledgement after
Rust actually cancels: foreign turn, ready phase and missing committed receipt.
Visible recovery must reuse the original session/scope/turn without another
submit, prepare or commit. Another controlled ordering actually commits in Rust
before cancel; the UI must show revision two, four accepted messages and the
spent potion once. Valid cancellation and disposal/late-delivery paths are
separate methods. Existing player-only inspection rejects Mira, Sable and
omniscient observer requests; this is negative admission coverage, not inspection
of NPC-private knowledge or omniscient canonical bytes.

Every method drains wrapper exchanges, closes the production transport on Main,
then requires simultaneous availability of all four real native owner slots.
Every probe handle closes on IO. Fresh production transport reopen must exactly
match the whole permitted player projection, accepted receipts and inventory,
and retain exactly the one fixture story. Ownership proof occurs within JUnit
before test completion and any external test-host cleanup. Only the contained
fixture root is deleted after drain/close/slot proofs. Failures retain their
diagnostics and do not become ownership passes through an OS kill.

## Actual B execution

All **six methods passed**, with all six exact start/terminal pairs, no skips or
unfinished methods and final runner terminal after those pairs. The owned cohort
completed in **48,782 ms**, child zero with known Windows Job cleanup. All
**46 clients** completed with exit zero and known cleanup. Exact before,
installed, after and final 25-package maps retained the original 23 package
hashes and the admitted app/test pair. Final userdata was **1,644,118,016 bytes**,
above the unchanged **1,207,959,552-byte** floor. Original after/final namespace
absence and capacity checks passed.

The native projection/receipt/inventory equality, original-key recovery,
exchange drain and four-slot assertions finished successfully within the six
tests before one separately admitted conditional exact TEST-package stop.
Fresh process/package UID and exact map checks preceded that stop. This is OS
test-host hygiene, not natural process exit, active-model cleanup or a fix for
the earlier unexplained graphics abort. No failed/unfinished native assertion
could reach this cleanup path. All calls stopped and the dispatch lease released.

Raw instrumentation was **4,412 bytes**, SHA256
`46b34ea40b530bd8639d6e0cb8e547e298f7ed7d8ddfa038ee831c9357b4c0d4`.
The coordinator and independent reviewer rehashed all 46 client stdout lengths,
hashes and terminal metadata with zero mismatches. Raw diagnostics stay local.

The closed device selection contains 146 files / 270,802 bytes; its 24,640-byte
index has SHA256 `c691d7f7bf2e2890d55b294ca5079d050bd4db3e804e693181320319c9fa0a93`.
The coordinator separately rehashed this selection with zero mismatches.
The closed host selection contains 54 files / 49,870,762 bytes, excluding its
temporary directory and the index itself. Its 10,166-byte index has SHA256
`314cd1a297216a1885a7a2f3c38c36ab3c303531d50101ee3ae6760b7c9befc7`.
All selected host files were rehashed with zero mismatches. These are bounded
closed selections, not a claim that every live file in either namespace is sealed.

## Source and host verification

Independent fixture freeze `075c0498d15fdc05630079d61f528cdbff6e7615`, imported
as `b95c32e`, compiled successfully with the app/test/fresh JVM/lint selection in
**69,359 ms**, child zero with known Windows Job cleanup. **150 JVM tests
passed**, zero failures/errors/skips across 19 XML files. Lint: **zero errors /
one existing GradleDependency warning** for the pinned coroutines version.

That build exposed a nullable-parent compiler warning in the new containment
check. Sole correction `edcd93d16c8d1f730950b9322abc5e5214c76d5b`, imported as
`39a4c8d`, binds checkNotNull(parentFile) before the same two containment
assertions. All six methods/assertions remain. First source/artifacts/logs are
retained. Final Android test assembly/lint completed in **45,328 ms**, child
zero/known cleanup; the new warning is gone. The unchanged JVM suite was not
repeated after this instrumentation-only correction. The unrelated existing
FrameworkInterruptionTest AtomicReference/Boolean compiler warning remains.

Both artifact sets passed identity/permissions/runner and native ELF/ZIP alignment
audits. All four native libraries and the app APK match #125 exactly; native
build tasks were reused. No new native compilation or ARM execution is claimed.

| Artifact/source | Bytes | SHA256 |
|---|---:|---|
| Unchanged app APK | 22,479,391 | `fc01b1ce8516b499d5ca47c518176cba1a93ba4350c2e27d1a14f7ec99950e40` |
| Final test APK | 2,348,183 | `ed5b4e1a66bf4519b89c651cf451ad9d059a5b4d4bb24935a2334d38a2aab605` |
| Final fixture | 20,712 | `bb157bb788ca5ea132dd4664a6664f59c1fca55181c2986ab3f5051e51ef8147` |

First fixture SHA256 `936e7598daca77b9be658f2efbaddaca918ba05132eacf4a8dded509a275c1ba`;
first test APK `db201d61f92026afd5bd2d68c100689d41452b5c3dfcdddc865dee8eb9c552d7`.
Production native-adapter source remains
`b77d0b541ae10ccda8593ecebed1158fc6eec9d7532d2611d2e6ea78680dcb25`.

## Reproduction and admission

Existing pins: Java 17.0.6, Gradle 8.11.1, AGP 8.10.1, Kotlin 2.2.21,
coroutines 1.10.2, SDK compile/target 36/minimum 26, Build Tools 35.0.0,
NDK 29.0.14206865 and Rust 1.93.1. No new compatibility choice was made.
From `apps/android`, with those toolchains configured:

```powershell
.\gradlew.bat :app:assembleDebug :app:assembleDebugAndroidTest :app:cleanTestDebugUnitTest :app:testDebugUnitTest :app:lintDebug -PlocalLoreCancelAckVerification=true --project-cache-dir .gradle-cancel-ack -Pkotlin.incremental=false --offline --no-daemon
.\gradlew.bat :app:assembleDebugAndroidTest :app:lintDebug -PlocalLoreCancelAckVerification=true --project-cache-dir .gradle-cancel-ack -Pkotlin.incremental=false --offline --no-daemon
```

Actual owned wrapper calls also selected plain console, two workers and
android.builder.sdkDownload=false, within 900-second/2 MiB Windows Jobs with
input barriers and verified cleanup. No script or Rust implementation changed;
previous unrelated test counts are not new executions.

After exact source/APK, namespace, identity, storage and package-map admission:

```powershell
adb -s <authorized-target> shell am instrument -w -r -e class org.locallore.app.NativeCancelControlsTest org.locallore.app.cancelack.test/androidx.test.runner.AndroidJUnitRunner
```

The command alone does not replace admission and paired-result parsing. The
private cohort retains 90-second instrumentation and 180-second outer limits,
the fixed 1,207,959,552-byte userdata floor, and original package-map checks.
All six methods must pass before any post-instrument action. A failed or
unfinished method stops the cohort without external cleanup under that admission.
After success, at most one exact TEST-only stop is allowed after fresh process/
package UID and exact map verification, followed by original absence/map/floor
checks. That is separate OS-host hygiene; it is not the native owner proof.

Independent review caught the inherited RED-capable cleanup path before any
dispatch; its draft and tightening receipt remain. Forty-three pure parser,
namespace, ownership and control-flow fixtures passed, including no action after
failed/unfinished native methods. Overlapping reruns are not extra unique tests.
Preparation errors for unsupported Python newline keyword and the final audit
phase label are retained zero-device-call setup failures, corrected under the
same admission policy.

## Scope and handoff

Only B, API 35/x86_64/4096-byte pages, is admitted. A remains blocked by its
previous storage deficit and is not queried again. M01.01 physical-phone
verification remains blocked. Real model behavior/quality, active inference,
process death, power loss, ARM and two-emulator gates remain separate. Prior
stopped cohorts, storage/timeout/preservation failures and unknown graphics
cause remain unchanged. User MainActivity, original saves and model files are
outside this fixture; no emulator relaunch/reset or data clearing is involved.

See the [device report](ANDROID_NATIVE_CANCEL_CONTROLS_DEVICE_2026-10-23.md) and
[independent review](ANDROID_NATIVE_CANCEL_CONTROLS_REVIEW_2026-10-23.md).
M05.04 remains **in_review, partial**; M04.04 receives supporting evidence. Acceptance boxes
stay unchecked. Raw diagnostics/APKs/identifiers remain local. No merge,
release, access/protection change or private payload upload occurs in this packet.

Next runnable integration task: extend this native fixture to free-text play-v2
cancellation/recovery rather than the current seeded dialogue and Give-potion
control. Claim that separate slice first, retain this exact coverage, and keep
active-model and OS-restart qualification separate. The authorized local model
copies belong to the independent inference experiment; no model was copied or
run by this packet.
