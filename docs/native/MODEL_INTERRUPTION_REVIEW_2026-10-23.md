# Synthetic model-import interruption review — 2026-10-23

Refs #9 (M05.05; M05.04 supporting). Independent review claim: [6379642795](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6379642795). Review began from `32161fe743c7a9f8fec22395261b8de35b2d41f0`, with PR #134 open and unmerged.

## Scope and current disposition

This report concerns the fixed synthetic partial-import fixture, its ownership protocol, and the evidence distinguishing interrupted-file recovery from pending-picker result restoration. One actual bounded emulator cohort produced the expected arm interruption followed by a fresh-process recovery PASS. This verifies the narrow synthetic prerequisite; M05.05's complete exit gate remains pending. The reviewer owned this report only and ran no builds, test suites, device commands, or model/cache operations.

The packet reuses only the disposable `.modelpickerverify` APP/TEST pair. Its new fixed private root is `model-picker-interruption-v1`; the existing `model-picker-fixture-v1` full copy and private receipt must survive unchanged. The fixture contains 63 original synthetic bytes, never model weights, player stories, an Engine workspace, or inference. Existing package, device, and real-model holds remain in force.

## Concrete source findings

1. **Partial proxy reads are unsuitable for the arm.** `ProxyFileDescriptorCallback.onRead` requires the requested byte count unless EOF intervenes. A deliberately short 17-byte read from a 63-byte proxy file cannot reliably establish the desired stage. The fifth fixed document instead uses a pipe with a 17-byte prefix and a separately blocked writer, with the public API30 `ParcelFileDescriptor.wrap` close listener. The four existing API26 proxy documents remain separate. See the [official proxy callback contract](https://developer.android.com/reference/android/os/ProxyFileDescriptorCallback#onRead(long,%20int,%20byte[])).

2. **Allocation failure must retain uncertainty.** SDK34 `ParcelFileDescriptor.wrap` detaches its input before constructing its communication channel. Closing the original wrapper after a subsequent allocation failure does not prove that the detached descriptor closed. The reviewed correction retains the partial reservation, records sticky allocation uncertainty/failure, and refuses further configuration or opens. It does not report a successful drain from best-effort cleanup.

3. **Consumer closure and writer completion are different gates.** A close callback may arrive while the writer still waits. Subsequent source admission must require both writer terminal and writer descriptor closure, as well as consumer drain. The author corrected both `openDocument` and `configure`; rereading the source confirmed both gates.

4. **The crash identity must match the target application.** The draft allowed either APP or TEST process names and accepted a merely positive saved UID. The arm and recovery must instead bind the actual target Activity's `applicationInfo.processName` and UID. Surviving TEST provider helpers cannot satisfy that identity. The author corrected the self-process checks, actual launched Activity check, saved proof, and recovery identity; rereading confirmed the TEST fallback was removed.

5. **Recovery must inspect before invoking the store.** The real `installed()` path acquires the persistent lock and removes the fixed staging file. The draft recovery correctly reads the bounded arm proof, verifies the exact 17-byte stage and preserved sentinels, and observes the old provider before launching the recovery Activity. Otherwise a successful cleanup could erase the evidence it purports to recover.

The [official close-listener contract](https://developer.android.com/reference/android/os/ParcelFileDescriptor.OnCloseListener) distinguishes clean close, error, and descriptor detachment. A generic `IOException` does not identify peer death specifically; it is recorded as a finite non-clean close observation and correlated with the independent process evidence. Detachment is uncertain ownership, not closure. A provider deadline is a fixture failure, never evidence of successful cancellation or cleanup.

The additional host process test uses an exact owned child JVM, a forced fixed readiness acknowledgement, a real 17-byte stage, and competing-store BUSY assertions while the child's OS lock remains held. It kills and awaits that exact child before reacquiring the lock and recovering the stage; its `finally` also kills and waits for that child. Host publication is explicitly a substitute. The Android fixture must separately verify actual native publication. The APK audit changes reject interruption fixture/helper markers outside the conditional profile and require its exact non-exported Activity inside it. These observations are source review, not test execution.

The coordinator reported and retained preliminary host failures: unavailable Java APIs in the Android test compile boot classpath, a missing child classpath entry caused by an implicit coroutine receiver, and a null filesystem file key on the actual Windows host. The revised source uses compatible readiness/output APIs, explicitly includes the child class's code source, and verifies fixed nonempty lock contents plus real lock contention/death/reacquisition. File-key comparison occurs only where supplied. This Windows run cannot establish lock inode identity; no null-equality assertion is counted as such evidence. A further run observed OS BUSY after the exact child had terminated. The corrected passing test retried only BUSY for at most five seconds, rechecked the unchanged stage on each refusal, and required actual subsequent store acquisition. It did not assume `waitFor` proved immediate lock release.

## Pending-picker process-death boundary

Ordinary instrumentation is unsuitable as proof of normal pending-result restoration. Android15's `startInstrumentation` normally force-stops the target before launching the runner; normal instrumentation finish also force-stops it. A selected arm/recovery pair can therefore establish persisted-file recovery across process interruption, but not preservation of the original Activity task or delivery of its pending document result. The process-death handler supplies a canceled instrumentation result containing `shortMsg=Process crashed.`; that framing alone does not identify why the process died. These are source observations, not an executed system-image trace. See [Android15 ActivityManagerService](https://raw.githubusercontent.com/aosp-mirror/platform_frameworks_base/android-15.0.0_r1/services/core/java/com/android/server/am/ActivityManagerService.java), especially `handleAppDiedLocked`, `startInstrumentation`, and `finishInstrumentationLocked`.

Android15 also exposes `--no-restart`, which changes attachment and finish behavior. A future pending-picker experiment could combine an already-running fixed target, a source-bound no-restart arm, an independent UI driver that survives the killed runner, and a finite fixture callback observation before no-restart readback. That topology has not been implemented or executed here. The present packet lacks those independent delivery observations; fresh-controller stale-result rejection remains the host boundary, and the actual pending-picker restoration gate remains open. See [Android15 command parsing](https://raw.githubusercontent.com/aosp-mirror/platform_frameworks_base/android-15.0.0_r1/cmds/am/src/com/android/commands/am/Am.java) and [instrumentation flags, watcher, and text reporter](https://raw.githubusercontent.com/aosp-mirror/platform_frameworks_base/android-15.0.0_r1/cmds/am/src/com/android/commands/am/Instrument.java).

The existing `restoredControllerIgnoresOldPickerDelivery` host test directly supplies a source lambda to a fresh controller, verifies zero source opens, and observes MISSING after foreground recheck. It does not recreate an Android process or deliver a framework callback. Production defers `ContentResolver.openInputStream` inside that rejected lambda, so this policy avoids opening an unrecognized result without automatically restoring a URI or READY state.

## Disabled controller review

The first disabled cohort draft used exactly selected arm/recovery methods, required the arm marker and source-derived canceled/crash framing, read only the bounded fixed private proof and process table in the ten-second inter-method gap, and allowed cleanup only after recovery PASS. Its lifecycle paths contained two APP/TEST update installs and conditional final stops of newly captured exact owned processes; there was no APP-data clear path. Full package hashes and UIDs guarded admission and final cleanup, and passive legacy provider observations conferred no lifecycle authority.

A concrete parser issue was reported: recovery parsing ignored result fields, so a contradictory crash/error result could coexist with an apparent method PASS. The corrected draft rejects that input, malformed machine records, and unexpected failure framing, and checks a successful final summary when supplied. Closed APP/TEST artifact-key sets and once-only proof-then-process reads in the inter-method gap were also confirmed on reread. Mocked adverse-flow fixtures cover these failures, deadline expiry, wrong UID, surviving APP, uncertain client cleanup, failed recovery, package/UID drift, and changed captured process identity. The reviewer did not execute those fixtures. That draft review preceded the final freeze and dispatch; disabled preparation by itself supplied no device result.

## Retained host results

The coordinator's corrected regular build completed with exit 0 and known cleanup in 53,047 ms. Independent reads of its copied XML reports counted 276 tests across 28 suites with zero failures, errors, or skips. The new child-process test passed in 0.33 seconds using the bounded eventual lock-acquisition gate. Regular lint contained four warnings and no errors.

The first fixture lint run reported three `UseSdkSuppress` errors. Commit `24742e67e0274fc1e4576f4ec6d20b542982ac4d` replaces the test-only API annotations with the runner's class-level API30 SDK filter while retaining explicit runtime guards. The corrected fixture XML independently counted 276 tests across 28 suites, zero failures/errors/skips. A filtered or skipped arm cannot qualify as the expected selected interruption.

Independent size/hash checks matched the final fixture audit records:

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| APP | 73,829,632 | `0777a0c81a601a345170c4a3203cf25c09742baab0120a6ec461bfce1eebe49c` |
| TEST | 2,509,313 | `21aa7e166e6128c26ace7dbd6205fb2ef311c03c4439f6cfb9386f66404f20dc` |

The audit's fixture, interruption test, host test, provider, and fixture-manifest hashes matched current source. A separate APP ZIP read found both private fixture Activity markers, no provider or interruption-test marker, six native libraries, and no model-extension files. The retained manifest showed the two private fixture Activities unexported without filters and the fixed setup as sole launcher. Audit records report signatures, permission restrictions and native alignment/hash checks passed; the reviewer did not rerun the auditor or signing tools.

The final disabled proposal `da992be188e848e36d74e776a76a92160637af4066a30e809a9c0599054c7c71` independently rehashed all 133 bindings, 77,969,114 bytes, without mismatch. All 48 live sources, copied sources, and source-record hashes matched revision `24742e67e0274fc1e4576f4ec6d20b542982ac4d`; the prior 33 hashes and UIDs matched the previous closed actual selection. The final pure-fixture receipt recorded 42 passes, zero failures/errors/skips, with mocked dispatch. The reviewer read the receipt and source rather than running the suite. The inter-method clients use the actual remainder of the ten-second gap as their deadline. The preparer permits only a globally clean tree or the exact sole root-owned untracked verification report.

The earlier disabled draft had a mixed historical live/copied-source relationship; matching its individual bindings did not prove coherence. It was retained and superseded without dispatch. An initial final-proposal preparation also stopped on the coordinator's unrelated untracked report; the final exact-path exception replaced the broader draft exception. No runtime or source behavior was relaxed. At final admission review, device calls were disabled and root GO remained pending. The coordinator subsequently admitted the exact final proposal for one cohort; actual results follow.

The host selection index `fc4f16b481737e039826eaabef1e5f475986c9d72a57602c10e0b3cda8e25de7` independently rehashed all 261 entries, 155,162,191 bytes, without mismatch. The copied ordinary XML independently counted 203 tests across 23 suites with zero failures/errors/skips. These host results do not supply Android interruption or model-performance evidence.

## Actual emulator cohort

The original owned invocation was confirmed terminal by its executor. Its retained outer receipt reported completed, exit 0, known cleanup, 51,000 ms, zero stderr bytes, and stdout SHA-256 `182e83bc92eb227577f58f228de02a26d098f7465eda252e19c941caaa53339e`. The reviewer independently read both raw selected-method outputs, the bounded proof and process observations, final facts, and all 64 client records/raw-output hashes.

| Observation | Actual result |
| --- | --- |
| Environment | One Android15/API35 x86_64 emulator, 4KiB pages |
| Arm | One exact selected START, fixed status-2 armed marker, expected canceled/crash result; no method PASS |
| Inter-method gap | 0.421 seconds; fixed bounded proof read then process table only |
| Recovery | One exact selected PASS, zero failures; normal runner success footer |
| Clients | 64 completed, exit 0, known cleanup; all retained output sizes/hashes matched |
| Controller lifecycle commands | Two exact APP/TEST update installs; one exact TEST stop after recovery PASS; zero explicit APP stops or clears |
| Final identity | 33 expected installed hashes and all 33 UIDs retained; other 31 hashes unchanged |
| Final processes/capacity | Zero owned processes, two passively observed legacy providers; 1,386,983,424 userdata bytes, above the 1,207,959,552-byte floor |

The bounded nine-key arm proof matched the actual target identity, fixed 17-byte stage, run-token format and original model hash. Recovery's executed assertions required the preserved real stage before store startup, a different actual process, non-clean consumer closure, separate writer FD closure/terminal bookkeeping with zero provider failures, real store lock acquisition/stage cleanup, preserved sentinels and old copy/receipt/proof, then a new explicit picker selection, native publication of all 63 bytes, and full rehash on reopen. These are assertions of the executed selected test; no independent raw provider-counter trace or power-loss durability is claimed.

All five retained identity/capacity gates independently matched their expected 33 hashes and UIDs, with no mismatch and all storage floors passing. Passive-provider appearance/disappearance supplied no cleanup credit or lifecycle authority. The cohort did not invoke inference or mutate real weights, stories, another app namespace, or the held emulator. Normal instrumentation still has the framework task/force-stop effects described above.

The sealed device index `4547ca25e356b5976a83d1059b0bf8f09efcc51b522091f269f4bf0f0fac4743` independently rehashed all 193 files, 548,138 bytes, without mismatch. Closure and released-lease receipts link the executor-confirmed original terminal to the owned result and that seal. The coordinator confirmed all 133 bindings matched at admission/closure. On the reviewer's later repeat check, 132 live bindings still matched; the sole difference was the coordinator's announced post-closure README evidence-link addition. Its frozen copy remained intact. This later documentation edit is not a different executed code selection.

These results cover one API35 x86_64/4KiB emulator and the original tiny synthetic payload. They do not establish API30-device execution, ARM64/16KiB execution, model inference, power-loss durability, physical-phone support, or ordinary pending-picker restoration. Full real-model/reference-phone gates remain separate; M01.01 remains blocked on its physical-device gate. The next runnable M05.05 packet is the independently controlled pending-picker process-death/callback experiment described above. No task checkbox, milestone closure, or merge follows from this review alone.
