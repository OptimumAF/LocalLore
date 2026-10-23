# Compose storage recovery verification — 2026-10-22

Scope: M04.04 ([#8](https://github.com/OptimumAF/LocalLore/issues/8)) and the
production Rust boundary from M03.03 ([#7](https://github.com/OptimumAF/LocalLore/issues/7)).
This focused follow-up is stacked on unmerged #44, source `80c7196`, rather than
duplicating accepted main's independent D03 work or the separate #48 storage
fault packet. M03.03's original #20/#35 integration was already owner-accepted.
No PR is merged by this packet. GitHub tickets own the work log; the retired
Markdown trackers remain pointers.

## Reproduced failures and implementation

Busy during submit/prepare discarded the pending key even when Rust had already
created the draft. Full/Busy during commit followed by a real ready status hid
the primary error behind Prepared. A malformed committed fallback discarded the
key before decoding narration and replaced the primary Busy with a JSON error.
The shell supplied generic uncertainty instead of fixed storage guidance.

`DurableGateway` now retains Busy uncertainty, accepts only a valid terminal
fallback, preserves the primary error when status remains unfinished or malformed,
and clears only the same pending operation after fully constructing the result.
A real committed receipt still resolves immediately. `ShellViewModel` maps only
the exact Full/Busy categories to fixed guidance, retains the last confirmed
player snapshot, blocks new turns/mode changes until recovery, and continues to
fence late callbacks by generation/disposal. Diagnostics retain only existing
bounded enums. Unknown categories/details never enter the notice.

Rust owns accepted outcomes, receipts, inventory and snapshots. Kotlin adds no
gameplay reducer, SQL, schema, native API, fault hook, dependency or permission.
Inference remains the deterministic local fake; no model or network is required.

## Baseline retained before the fix

Independent JVM tests at `c71d328` over production `80c7196` ran nine methods:
five passed and four failed, zero errors/skips. Failing parameter loops stopped
at their first Full assertion; this does not establish every later Busy variant.
The first unquoted PowerShell Gradle property invocation failed before tasks;
the corrected quoted invocation produced these actual test results.

The baseline command in the independent test worktree used JDK 17.0.6:

```powershell
& "$env:JAVA_HOME/bin/java.exe" -classpath apps/android/gradle/wrapper/gradle-wrapper.jar org.gradle.wrapper.GradleWrapperMain -p apps/android :app:testDebugUnitTest --tests org.locallore.app.StorageRecoveryShellTest --offline --no-daemon '-Pandroid.builder.sdkDownload=false'
```

Root integrated only test commits as `9f5cbde`, built app/test APKs offline, and
ran the new eight-method native class on emulator A before production edits.
Three controls passed and five methods failed; no skips or unfinished cases.
The retained failures directly demonstrate Busy-before-prepare,
Full-before-commit, malformed committed narration, the missing Full notice and
Busy-before-submit. Later variants in failed parameter loops were not all reached.
ADB exit 0 did not override the failing instrumentation protocol. Cleanup passed.

Baseline app SHA-256:
`56ec9d0c20736a772ed7bda9372cdccb300ed8ef1ce609a3158c926e75839ebb`.
The test APK was unchanged for the candidate, SHA-256:
`faaa378f307b5144e764b3ca9fc1fc59c18a2ee35ba9eb44f1218856e692c264`.

## Candidate checks

Production fix: `2220a5aaf92c75cdd25b4fb19bf42737f190e86d`.
Subsequent review/report commits change only documentation. Candidate app SHA-256:
`f17db036fed45bac28d1a27d8632e3f6631d641092be8247a4ef053a7b324393`.

Actually run from the repository root with the configured Java 17 runtime and
Android SDK:

```powershell
python scripts/check.py android --offline
```

Passed: app and instrumentation APK build, JVM **47/47** (including all nine new
methods), lint **zero errors / one existing GradleDependency advisory**, and
APK/native alignment/permission audit. Gradle reported 78 actionable tasks:
16 executed, 62 up-to-date. Both x86_64 and arm64-v8a libraries were packaged;
this was an incremental build, not a clean-room build. Configured pins remain
Rust 1.93.1, NDK 29.0.14206865, Gradle 8.11.1, AGP 8.10.1, Kotlin 2.2.21,
compile/target SDK 36 and minimum API 26. No dependency was selected or changed.
No new Rust/Python host gate was run for this Kotlin-only packet; parent #44's
host results remain separate evidence.

The same frozen APK pair passed these ordinary groups on each selected Android
15/API 35 x86_64 emulator:

| Group | A | B |
| --- | ---: | ---: |
| New storage recovery | 8 | 8 |
| Existing JNI, cancellation and ownership | 15 | 15 |
| Existing shell and layout | 8 | 8 |
| Existing diagnostics, consent and resource cleanup | 17 | 17 |
| Ordinary total | 48 | 48 |

All 96 candidate ordinary executions passed, zero failures/skips/unfinished.
These are 48 unique methods across two targets, not 96 distinct scenarios.
All nine ordinary attempts, including the failed baseline, retain separate
results and successful final app-process absence/client cleanup. The explicit
checkpoint/verified app stop/resume procedure passed on each target: four more
passing test-method executions, **100 candidate case executions total**. The
resumed production Activity restored the exact accepted transcript/revision and
rejected duplicate potion use. Both restart reports verify final app absence
and client cleanup; no failed candidate attempt was omitted or rerun.

The [sanitized results](STORAGE_RECOVERY_RESULTS_2026-10-22.json) retain every
ordinary attempt and both restart procedures. The [independent review](STORAGE_RECOVERY_REVIEW_2026-10-22.md)
records source/result inspection. These finite tests do not establish general
fault or device qualification.

## Test design and reproduction

`StorageRecoveryShellTest` uses a fake gateway for controller-only initialization,
prepare, commit, repeated recovery, unknown/private categories and stale/disposed
callbacks. These are JVM tests, not JNI evidence.

`StorageRecoveryInstrumentedTest` wraps actual production
`NativeWorkspaceTransport`/Rust/SQLite with one-shot fixed error envelopes before
or after selected real operations. Assertions cover original request/session/
scope/key, no redundant preparation of ready work, valid committed-receipt
reconciliation, malformed status, exact Full/Busy UI notices, disabled unsafe
controls and authoritative snapshots. A held actual Ready reply is cancelled
before a new story; it cannot commit or publish into that story. This held reply
case does not claim overlap with active inference. Existing ownership regressions
independently observe running Rust work and Main-thread responsiveness.

Each new fixture uses a create-new synthetic private root. Cleanup releases held
delivery, clears ViewModels, closes the actual transport on Main, drains tracked
exchanges, acquires/releases all four native slots and removes only that verified
root. Primary and cleanup failures are retained together. No production save is
deleted. Existing UI tests create synthetic saved stories in the normal library.

After the documented build, explicitly select an authorized emulator, update
the two APKs with `adb install -r -t`, and run each class group with:

```powershell
adb -s $env:ANDROID_SERIAL shell am instrument -w -r -e class org.locallore.app.StorageRecoveryInstrumentedTest org.locallore.app.test/androidx.test.runner.AndroidJUnitRunner
```

The recorded coordinator used bounded test-only transport with installed/local
APK hash guards, a durable start/terminal journal per cohort, the strict parser
from #46 (`ad173d9`), expected method identities/counts and final app/client
cleanup. Some A/B candidate groups briefly overlapped; this is not a globally
serial schedule or a performance experiment. Its ignored driver lives under `target/checks/storage-recovery/` and
is not a new default check or shipped app feature. Native, shell and diagnostics
class groups are listed by every completed case in the JSON. Method discovery
was corrected before the first diagnostics run to include the intervening
`@SdkSuppress` annotation, yielding all eight writer cases; no earlier diagnostic
attempt was discarded. Clients use 180-second instrumentation deadlines and
128-KiB output caps. Missing/mismatched/skipped/unfinished records fail closed.
Explicit process restart uses the checked-in
[two-phase runner](APP_DEVICE_RUNNER.md), not ordinary skipped discovery.

## Limits

Injected Full/Busy frames exercise protocol and UI recovery through real Rust;
they are not actual partition exhaustion. #48 separately tests actual SQLite
page-limit Full. No physical phone, ARM64 execution, real model, heap high-water,
partition ENOSPC, hardware power loss, hosted CI or release qualification follows.
M01.01 remains blocked on an authorized physical phone. The earlier graphics
watchdog abort from #45 remains unexplained/unfixed; favorable later cohorts do
not establish its cause or repair. The other three emulators, model packages and
existing saves are preserved. No root/reboot/data clear/uninstall, renderer flag,
fake-delay change, PR merge, release or access/protection change was performed.
