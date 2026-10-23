# Native lifecycle ownership follow-up — 2026-10-22

Scope: [M03.03 / #7](https://github.com/OptimumAF/LocalLore/issues/7).
Baseline main `2c095ea` already contains the accepted Compose/Rust JNI integration
from [#20](https://github.com/OptimumAF/LocalLore/pull/20). This follow-up fixes a
reproduced lifecycle leak without changing the control-v1 contract or dependencies.
The original [execution report](VERIFICATION_2026-10-22.md) remains dated evidence.

## Reproduction and fix

`ShellViewModel.reset()` previously called `gateway.reset()` after `onCleared`.
A retained UI callback could therefore create a native session after the
ViewModel store had released its owner, with no subsequent disposal to close it.
The new JVM regression first failed against the baseline: three retained Reset
calls caused three gateway resets; expected zero. The fix returns immediately
when the ViewModel is disposed, before changing state or calling the gateway.

The actual JNI regression creates the production gateway, starts a delayed IO
worker, clears its ViewModel store, waits for all resource counts to return to
baseline, and invokes Reset three times. No new session or state change is
allowed. Test cleanup explicitly closes the gateway even if this assertion fails.

A second JNI test repeats twelve delayed-worker resets followed by fresh accepted
turns. Each fresh session must commit revision 1, retain exactly two transcript
messages, and leave only its one session/current operation; obsolete workers and
sessions must drain. Final disposal returns all four counts to baseline. Existing
native/Compose tests also cover twenty cancellation/destruction cycles per
emulator, pending cancel/reset, Activity recreation/disposal, invalid byte arrays,
owner-thread controls, actual events and observer isolation.

Independent reviewer branch `review/m03-native-ownership` contributed only
`crates/locallore-android/tests/ownership_review.rs` (source commit `912ae6e`,
integrated as `32a634c`). These two host regressions verify wrong-thread
begin/commit cannot allocate/mutate, cross-thread destruction releases resources,
and late cancelled operation IDs cannot affect their same-session replacement.
No additional Rust production defect was found. The reviewer also inspected the
Kotlin fix and proposed the explicit test-failure cleanup above. Coordinator owns
the shared contract, production change, Android tests, emulator execution and
integration. Paused M01 Android runtime artifacts remain on separate branches.

## Checks

Windows x86_64; Rust 1.93.1, JDK 17.0.6, Gradle 8.11.1, AGP 8.10.1,
Kotlin/Compose compiler 2.2.21, NDK 29.0.14206865, SDK compile/target36/min26.
No new dependency, permission, callback or native thread is introduced.

| Actual command/procedure | Result |
|---|---|
| Targeted `:app:testDebugUnitTest --tests org.locallore.app.ShellViewModelTest.retainedResetCallbackCannotReopenADisposedGateway` before the fix | Failed with reset calls 3, expected 0 |
| `python scripts/check.py host --offline` after integration | Passed: 26 domain + 5 runtime example + 10 native boundary tests; 63 Python tests; 4 fixture comparisons; 3 linker tests; format/Clippy |
| `python scripts/check.py android --offline --clean` | Passed: 79 executed Gradle tasks, both native ABIs, app/test APKs, 31 JVM tests, lint and APK audit |
| `python scripts/check.py android --offline` after reviewer-requested test cleanup | Passed: 7 tasks executed/71 up-to-date; lint zero issues; APK audit passed |
| Install final app/test APKs and execute full instrumentation on emulator A | Passed: 30 tests, zero failures/skips |
| Same final APKs/full instrumentation on emulator B | Passed: 30 tests, zero failures/skips |

Both targets are `sdk_gphone64_x86_64`, Android15/API35, x86_64, with 4,096-byte
pages. The ADB inventory contains five emulators and no physical phone. Only
these two targets were used; no new emulator or SDK was provisioned. The final
app APK came from the clean build; only the test APK was rebuilt after the
reviewer's cleanup change. Exact final hashes, sanitized environment and all
thirty passing case names on each target are in
[the result artifact](OWNERSHIP_RESULTS_2026-10-22.json). The two new cases passed
through the actual JNI library on each emulator, as did the existing
cancellation/disposal suites: **60 passed, zero failures/skips** in total.

The coordinator installed both APKs and ran instrumentation directly, selecting
one authorized transport at a time. With `ANDROID_SERIAL` set to that local
target, equivalent commands from the repository root are:

```powershell
adb install -r -t apps/android/app/build/outputs/apk/debug/app-debug.apk
adb install -r -t apps/android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk
adb shell am instrument -w -r org.locallore.app.test/androidx.test.runner.AndroidJUnitRunner
```

Repeat for the second selected target. Each actual run returned `OK (30 tests)`
and thirty successful per-test status records. The raw outputs remain in ignored
`target/checks/m03-ownership/`; public evidence contains no transport IDs,
private story content, device identifiers or raw diagnostics.

The first targeted PowerShell invocation split an unquoted Gradle `-P` property
and failed before running tests. Quoting the argument fixed the command. The
standard check runner uses argument arrays and was unaffected.

## Evidence limits and handoff

The inference provider is deterministic and fake; the Rust engine, JNI transport,
IO dispatch and lifecycle are real. Registry count assertions are finite ownership
checks, not a heap profiler or proof about future inference-runtime resources.
ARM64 is cross-built/packaged only. No physical phone, real-model Android inference,
API26/36 or 16KiB OS execution, process-death durability, performance qualification
or hosted CI result is inferred. Gameplay remains local and in memory.

M03.03 retains its earlier accepted status. This follow-up awaits its own PR
review/owner acceptance. No merge, release or repository setting change is made.
The GitHub tickets own status and handoff; retired Markdown trackers remain pointers.
