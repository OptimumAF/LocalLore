# Framework interruption checks — 2026-10-22

Scope: M04.04 and bounded M04.05, [#8](https://github.com/OptimumAF/LocalLore/issues/8).
This test-only follow-up is stacked on [#44](https://github.com/OptimumAF/LocalLore/pull/44)
at `80c7196`. It changes no production source, dependency, manifest permission,
Host wire, schema or inference delay. The actual production app APK matches
#44 byte-for-byte; the instrumentation APK adds `FrameworkInterruptionTest`.
No PR was merged by this packet.

## Executed boundaries

The fixture registers an API29 Application pre-create callback before the
Compose Activity rule launches the real `MainActivity`. It constructs a
`ShellViewModel` in the normal ViewModel store through a custom test factory.
Production `MainActivity.onCreate` obtains that same entry through its ordinary
provider; the test asserts identity. Recreation must retain the same instance
and allocate only one native owner. There is no reflection or production test hook.

The custom transport delegates all commands to the actual
`NativeWorkspaceTransport`, Rust Host and SQLite. A test-only ContextWrapper
selects a create-new private synthetic root. It neither edits the production
workspace nor introduces a path capability in the Host protocol. The first
prepare runs uncancelled on IO so its real return is recorded even if Main's
coroutine is cancelled. Only reply delivery is held. On release, the wrapper
deliberately supplies the obsolete response to the controller rather than
relying only on coroutine cancellation to discard it.

Three explicit interleavings are required:

| Case | Required observation and outcome |
|---|---|
| Real framework recreation | Rust `running` observed before transition; atomic JNI-in-flight flag true at the first framework pre-stop callback; original persistent turn then cancelled, revision0/no messages. The retained controller accepts one replacement turn. Releasing the old reply cannot change that receipt or UI; fresh native reopen matches. |
| Stop/resume, then new story | A real Rust `ready` reply is held before delivery, with no commit. ActivityScenario moves through actual stop to CREATED; JNI-in-flight must be false. Original-key cancellation and zero canon are checked. After resume, an independent new story accepts one gift. Late old reply cannot attach to it; reopen proves old story revision0 and exact new transcript. |
| Actual destruction | A real ready reply is held, then ActivityScenario closes through framework destruction. Releasing it cannot commit or publish. Retained reset/submit/recover callbacks make no new exchanges. Wrapped exchanges reach zero, four owner slots recover, and a fresh owner reopens unchanged revision0/no receipts. Disposal may retain an uncommitted draft if on-cleared interrupts cancellation reconciliation. |

The native-active assertion is a finite observation, not an inference from a
busy spinner. Failure to observe it is insufficient evidence, not a passing
cancellation test. A native ready reply can legitimately beat the IO cancellation;
the stop/recreation cases separately query the original key and require persisted
`cancelled` status. No prepared response is treated as canonical.

An atomic counter wraps every controller exchange and decrements in `finally`.
Cleanup releases the delivery gate, closes the production transport, awaits the
held return and zero wrapped exchanges, verifies four registry admission slots,
then deletes only that test's exact synthetic root. Probe handles always close.
Slot recovery is not a heap profile or a direct measurement of every internal
cleanup worker. Primary and cleanup errors are preserved together. Application
callbacks are unregistered; ordinary Shell regressions run later in the same
instrumentation process to check that construction remains unaffected.

## Compatibility and independent review

Android's [ActivityScenario reference](https://developer.android.com/reference/androidx/test/core/app/ActivityScenario)
documents CREATED as the path after onStop and DESTROYED as terminal; methods
run from the instrumentation thread. The
[Application callbacks reference](https://developer.android.com/reference/android/app/Application.ActivityLifecycleCallbacks)
places the pre-create/pre-stop methods at API29, before their Activity callbacks.
New tests use `@SdkSuppress(minSdkVersion=29)`; the production minimum26 is unchanged.
The [ComponentActivity reference](https://developer.android.com/reference/androidx/activity/ComponentActivity)
requires an attached Application for the ViewModel store. Independent inspection
of the actual pinned Activity1.10.1 bytecode and installed SDK source confirmed
the fixture's construction order; emulator execution checks the API35 behavior.
See [independent review](FRAMEWORK_REVIEW_2026-10-22.md). No dependency was added.

## Commands and evidence

Windows x86_64, JDK17.0.6, Rust1.93.1, Gradle8.11.1, AGP8.10.1,
Kotlin/Compose compiler2.2.21, NDK29.0.14206865, SDK compile/target36/min26.
The two selected targets remain Android15/API35 x86_64 emulators. Inventory
showed five emulators and no ADB-authorized physical phone; the other three,
runtime benchmark package, model cache and unrelated processes were untouched.

| Actual command/procedure | Result |
|---|---|
| `python scripts/check.py android --offline` after `68c35cf` | Passed: both native ABIs, app/test APKs,38 JVM tests, lint and APK audit |
| Same gate after final test source `dd11ab2` | Passed; lint zero errors/one existing dependency-version advisory |
| First three-case framework run on A | One pass/two explicit insufficient-native-overlap failures |
| Revised combined run on A | Three framework cases passed; the first subsequent Shell case aborted in an Android graphics finalizer watchdog; other selected cases not reached |
| Revised combined run on B |16 passed, zero failures/skips |
| Serial A combined rerun, unchanged source/APKs |16 passed, zero failures/skips |
| Hash-guarded final app-stop/absence and host-client cleanup | Passed on both targets |
| `git diff --check` and sanitized JSON/count validation | Passed |

Host Rust/Python sources are unchanged from #44. Its123 Rust/211 Python results
remain separate evidence; this packet does not claim to have rerun them.
No model, download, provisioning, self-hosted runner or emulator operation occurs
in the default check command. APK updates used `install -r -t`, preserving data.

Final app SHA-256:
`56ec9d0c20736a772ed7bda9372cdccb300ed8ef1ce609a3158c926e75839ebb`.
Test APK SHA-256:
`e4d57cf5d735f642ea474f0ecbf3a098849377e559181e7eabf50134452024d3`.
The selected complete runs have16 distinct cases per target,32 passes in total:
three new framework cases and13 relevant regressions on each. Their actual JUnit
durations were A160.766s and B168.264s; these are test/UI overhead, not gameplay
performance. Earlier failures remain separate below and in the result artifact.
Installed app/test identities are checked before each bounded instrumentation
call. Actual class selection, repeated for the second explicitly selected target:

```text
adb -s <authorized-target> shell am instrument -w -r -e class org.locallore.app.FrameworkInterruptionTest,org.locallore.app.ShellInstrumentedTest,org.locallore.app.DurableNativeTest,org.locallore.app.DurableTransportOwnershipTest org.locallore.app.test/androidx.test.runner.AndroidJUnitRunner
```

The coordinator uses the existing bounded process owner,180s maximum per call,
with raw output in ignored `target/checks/framework/`. The selected package is
hash-guarded before force-stop; explicit process absence and ADB-client cleanup
are separate checks. The [sanitized artifact](FRAMEWORK_RESULTS_2026-10-22.json)
retains every attempt, fixed test names, APK identities and aggregate flags,
without raw story text, scope/turn IDs, private paths or device identifiers.

## Unresolved observation and limits

The initial revised A run aborted with `ReferenceQueueDaemon` timing out in
`HardwareRenderer.DestroyContextRunnable`, after the three framework cases
passed. The app process aborted; the selected emulator stayed booted/reachable.
This is retained as a failed run. The exact app was stopped with verified
absence before an additional serial attempt. No graphics flag, animation setting,
watchdog, dependency, fake delay or timeout was changed or suppressed.
No renderer root cause or production fix is established; a later pass does not
erase this observation. Independent source investigation is recorded in review.

This is real framework/Kotlin/Rust/JNI/SQLite with fake inference, not phone/model
performance, ARM64 execution, hardware power loss, allocator qualification or a
hosted-CI result. Full M04 includes additional conflict/exhaustion/recovery gates;
these bounded cases do not close it. M01.01 remains blocked on an authorized phone.
The claims and local evidence await PR review, without new accepted checkboxes.
The next runnable task is bounded isolation/repetition of the unexplained renderer
cleanup abort, preserving default renderer/watchdog behavior and every attempt.
