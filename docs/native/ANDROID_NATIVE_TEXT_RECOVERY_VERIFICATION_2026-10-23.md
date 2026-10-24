# Native free-text recovery through Compose, 2026-10-23

Refs [#9](https://github.com/OptimumAF/LocalLore/issues/9), M05.04 partial and
M05.05 supporting. Prerequisite: open [#126](https://github.com/OptimumAF/LocalLore/pull/126),
exact `b2d9fce1c08a24887c9eb6abb580d4b7b3d44a35`. Owner acceptance remains pending.

## Boundary and original intent

The prior six native cancellation cases use the typed demo action operation.
This separate fixture exercises Action and Dialogue entered into the Compose
text field, through production ShellViewModel, DurableGateway,
NativeWorkspaceTransport, JNI, Rust Host and SQLite. The original free_text
request keeps its kind, untrimmed text, scope, accepted revision and turn key.
Kotlin sends intent; Rust owns interpretation, validation, canonical events,
narration checks and commit. A literal dialogue claim is a recorded statement,
not world truth or permission to grant progression.

The native provider remains explicitly android-scripted-play-v2, with no loaded
language model. Existing dependency, runtime, SDK and model choices are unchanged.
The fixture uses a fresh contained synthetic child of the isolated verification
application's no-backup directory. It never opens original saves or model files.

In-test exchange drain, native owner close, simultaneous acquisition and closing
of all four registry owner slots, and exact permitted player projection/accepted
receipt equality across SQLite reopen are required before external test-host
cleanup. This is owner close/reopen rather than Android process-death recovery.
Ready reply delivery holds do not establish active model cancellation.

Two accepted cases compare the actual original request and complete play-v2
profile with the native configured fixture profile. Action preserves leading
and trailing spaces. Dialogue preserves spaces, a newline and non-ASCII text;
its sole proposed Say and sole Said event leave permitted player self-state,
facts, beliefs and inventory unchanged, including no granted blink ability.
These are finite player-view and event checks, not NPC-private inspection.

Cancellation holds a real prepared reply and the real native cancellation
acknowledgement before delivery. A foreign delivered acknowledgement forces
visible recovery using the original cancel command, with one free_text submit
and one prepare. Disposal clears the ViewModel before releasing both replies
and must fence all later publications and retained callbacks.

The uncertain-commit case actually commits once in Rust, retains its real receipt,
then substitutes a Busy reply for delivery and for the first status lookup.
The UI must retain prior visible accepted history and disable new turns until
the recovery click fetches the original committed turn. Recovery must use one
original free_text request, one prepare, one commit and two status calls, and
publish the stored receipt exactly once. This controlled delivery fault does
not establish that SQLite or the real engine spontaneously returned Busy after
committing. The accepted outcome remains authoritative throughout uncertainty.

## Verification

Independent source `1824334a814a8c505d2c3e80514bbffc95b7bc85`, imported as
`cb9f63a`, adds six methods in NativeTextRecoveryTest. Final source: 23,825 bytes,
458 LF lines, SHA256 `bae23dba98f32953c215280ea297c23c91bb25457e4309e262ee21298e35e867`.
The preceding NativeCancelControlsTest remains byte-identical; its previous
six passes are not counted as new execution in this packet.

Actual debug app/test assembly, fresh JVM selection and lint completed in
75,156 ms, child zero with known Windows Job cleanup. All 150 JVM tests passed,
zero failures/errors/skips across 19 XML reports. Lint: zero errors and one
existing GradleDependency warning for pinned coroutines. Only the unrelated
existing FrameworkInterruptionTest AtomicReference/Boolean compiler warning
remains; the new fixture produces no compiler warning. Native build tasks were
reused; no fresh Rust compilation is claimed.

The APK audit passed exact package/runner/target/permissions and native ELF/ZIP
alignment checks. Application bytes and all four native library hashes match
#126 exactly. No production code, dependency, schema, permission or wire change
was needed.

| Artifact | Bytes | SHA256 |
|---|---:|---|
| Unchanged app APK | 22,479,391 | `fc01b1ce8516b499d5ca47c518176cba1a93ba4350c2e27d1a14f7ec99950e40` |
| Test APK | 2,368,766 | `eb11f1dd45cee19aadd972b99210fc0a9777352ead35250d94a830f97e664a06` |

Existing toolchains: Java 17.0.6, Gradle 8.11.1, AGP 8.10.1, Kotlin 2.2.21,
coroutines 1.10.2, SDK compile/target 36/minimum 26, Build Tools 35.0.0,
NDK 29.0.14206865 and Rust 1.93.1. From apps/android:

```powershell
.\gradlew.bat :app:assembleDebug :app:assembleDebugAndroidTest :app:cleanTestDebugUnitTest :app:testDebugUnitTest :app:lintDebug -PlocalLoreCancelAckVerification=true --project-cache-dir .gradle-cancel-ack -Pkotlin.incremental=false --offline --no-daemon --console=plain --max-workers=2 -Pandroid.builder.sdkDownload=false
```

Actual owned wrapper invokes the existing Java wrapper directly, within a
900-second / 2 MiB Windows Job with an input barrier and known cleanup.
Forty-three pure parser/namespace/ownership/control-flow fixtures passed without
device calls before dispatch. Final source/APKs/controller and 25 proposal
bindings were independently reviewed and rehashed before the one admitted run.
Promotion changed only the two admission flags; the original disabled proposal
remains retained. No gate or deadline was relaxed.

The closed host selection contains 44 files / 25,039,809 bytes. Its 8,295-byte
index has SHA256 `da4e8bfdcc615c2f293b8294e1e568fdb4d9124c5c90eb196ec5c5db25cc7657`.
The coordinator and independent reviewer rehashed all selected files with zero
mismatches. The temporary directory and index itself are excluded; this is a
bounded closed selection, not an immutability claim about every live file.

## Actual emulator B cohort

All six methods passed, with six exact start/terminal pairs, no skipped or
unfinished methods, and the final runner terminal after all pairs. The single
owned cohort completed in 54,531 ms, child zero with known Windows Job cleanup.
All 46 client records completed with exit zero and known cleanup. The coordinator
and independent reviewer separately rehashed every raw stdout length/hash and
terminal record with zero mismatches. Instrumentation stdout was 4,348 bytes,
SHA256 `f35f70b8cb20b035fb988d0bff7feeed46b71f29a48e5d64a7b506255dca60b6`.

Before/installed/after/final maps contain the expected 25 packages and preserve
all original 23 package hashes. Namespace, ownership and original storage gates
passed. Final userdata was 1,644,441,600 bytes, above the unchanged
1,207,959,552-byte floor. Emulator B is API 35/x86_64 with 4096-byte pages.

All in-test original-request, actual-receipt, permitted-player-projection,
exchange-drain, four-owner-slot and reopen assertions passed before one
separately admitted conditional exact TEST-package stop. Fresh process/package
UID and exact map checks preceded that action. This is explicit OS test-host
hygiene, not natural Android process exit or model-resource qualification.
Any failed or unfinished method would stop the cohort before post-instrument
observation or cleanup under this admission. No extra cohort was run; all
device calls are terminal and the exclusive lease is released.

The actual selected instrumentation command, after full admission, was:

```powershell
adb -s <authorized-target> shell am instrument -w -r -e class org.locallore.app.NativeTextRecoveryTest org.locallore.app.cancelack.test/androidx.test.runner.AndroidJUnitRunner
```

The private controller retains its 90-second instrumentation and 180-second
outer limits, original package-map/namespace/floor checks and owned client
cleanup. The command alone does not replace those gates or paired-result parsing.

The closed device selection contains 134 files / 215,225 bytes. Its 22,707-byte
index has SHA256 `80fcd17373fa9384e45ac98e11dd830c3500c32521ec4ab96ec86bb88df8671d`.
The coordinator's later read-only audit is outside this selection; no sealed
file was changed to add it. Raw diagnostics, APKs, identifiers and local paths
remain private. Closed evidence from #126 remains unchanged.

## Scope and handoff

Only emulator B was admitted under the unchanged source/APK, namespace,
package-map, ownership and storage gates. A's prior storage deficit and M01.01
physical-phone gate remain blocked. Real inference, ARM64 execution, sustained
performance, reference-phone quality and the whole M05 exit gate remain pending.
Acceptance checkboxes stay unchecked. No merge, release, access/protection
change or private payload upload is part of this packet.

See the [device report](ANDROID_NATIVE_TEXT_RECOVERY_DEVICE_2026-10-23.md) and
[independent review](ANDROID_NATIVE_TEXT_RECOVERY_REVIEW_2026-10-23.md).
M05.04 remains in_review, partial; M05.05 receives supporting fake-provider
integration evidence. No new production correction or real-backend gate is
claimed. The source author's initial unsupported Python newline argument failed
before creating the file and was corrected; no failing device cohort or failed
test execution is hidden by the successful result.

Next runnable product task: inspect and resume the existing authorized local
inference experiment with fresh target identity/namespace/capacity admission.
The owner's permission for local model copies persists, but this packet copied
or loaded no weights. Preserve the original storage floors and qualify actual
inference separately from this scripted integration evidence.
