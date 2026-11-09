# Android fresh-task navigation test

Refs [#13](https://github.com/OptimumAF/LocalLore/issues/13) (M09.06) and
[#8](https://github.com/OptimumAF/LocalLore/issues/8) (supporting M04.05).
The test covers the private navigation hint from
[#433](https://github.com/OptimumAF/LocalLore/pull/433).

The case uses the existing input-process verification build and launches the
actual MainActivity twice. It creates two synthetic stories with the Rust
workspace and saves a distinguishable child timeline. The first activity
starts without a navigation hint, then selects that child. The test waits
for the real private hint file to contain the exact story and timeline IDs.
It closes the first activity and launches a new task without saved-instance
navigation. A fresh factory must resolve the private hint and display the
child's accepted history. The existing process probe checks that the second
launch uses read-only Host operations.

The test changes only a fresh, isolated `org.locallore.app.draftprocessverify`
installation. It refuses existing workspace, navigation or probe state
before creating the synthetic fixture. It retains the fixture and proof
files for inspection. It uses scripted inference to seed accepted history.
The two activities run in one Android process, so this case measures fresh
task navigation and file-backed selection separately from OS process death.

## Offline build

Run from `apps/android` using the installed SDK and the repository's Java
wrapper entry point. These tasks build both APKs and run host checks.

```powershell
& "$env:JAVA_HOME/bin/java.exe" -classpath gradle/wrapper/gradle-wrapper.jar `
  org.gradle.wrapper.GradleWrapperMain :app:assembleDebug :app:assembleDebugAndroidTest `
  :app:testDebugUnitTest :app:lintDebug --offline --no-daemon --console=plain `
  --project-cache-dir .gradle-input-process '-Pandroid.builder.sdkDownload=false' `
  '-PlocalLoreInputDraftVerification=true' '-PlocalLoreInputProcessVerification=true'
```

The outputs are under `app/build-input-process/outputs/apk`. From the
repository root, `scripts/audit_apk.py` supports
`--input-process-verification` for the product APK.

The offline verification passed 427 JVM tests across 49 suites, Android
instrumentation compilation, lint and both APK assemblies. The product
audit checked the isolated manifest and both packaged native ABIs. The
pair check matched signing identities and found the annotated test method
in the test APK only.

## Bind the APK pair and selector

From the repository root, audit the exact input-process outputs:

```powershell
python -I -S -B scripts/audit_instrumentation_apk.py `
  apps/android/app/build-input-process/outputs/apk/debug/app-debug.apk `
  apps/android/app/build-input-process/outputs/apk/androidTest/debug/app-debug-androidTest.apk `
  --cold-navigation-verification
```

The resulting `cold-navigation-apk-pair-v1` JSON binds byte counts and
SHA-256 hashes for both APKs, their verified signing identity, the reviewed
manifest and the exact `instrumentation_args` array. The audit verifies that
the concrete public test class and its single annotated method exist in the
test APK only. It rechecks both APK identities after inspection. Use the
complete result as a file binding for a reviewed device plan. The APK audit
does not allocate a guest or grant operation authority.

The cold-navigation command policy in
`benchmarks/owned_cold_navigation_ui_contract.py` checks the retained #434
APK bytes and #436 attestation against fixed bindings. The existing owned
client's operation validator and test claim lookup use the same exact
argument vector. The cold profile also refuses force-stop and model commands.
Its host replay requires a zero exit code, empty stderr and a complete
start/pass pair for the one selected method. A skip or an incomplete
instrumentation record fails replay.

The v4 adapter in `benchmarks/owned_cold_navigation_ui_client.py` attaches
to an already owned target and checks the retained APKs before observing it.
It uses a fixed 120-second test command and requires the existing v4 client,
socket and one-use claim proofs before replaying the test output. It compares
the retained stdout with the bytes returned by the live client.

The controller in `benchmarks/cold_navigation_ui_controller.py` consumes
an already owned target. It checks the booted API, ABI and user, then
requires both package queries to be empty before staging either APK.
Installation uses `pm install -R` because Android 15 permits replacement
by default. [Android 15 package-manager source](https://android.googlesource.com/platform/frameworks/base/+/refs/tags/android-15.0.0_r1/services/core/java/com/android/server/pm/PackageManagerShellCommand.java)

The controller checks the installed UID, path and APK hash before and after
the one test. It retains command records on refusal and replays the full
ordered client roster before recording a completed result. Observer handle
closure has its own result field.

The SDK20 owner in `benchmarks/owned_cold_navigation_ui_owner.py` accepts
the fixed cold-navigation admission only. Both the parent and the worker
verify the operation-specific approval and one-use attempt claim, reviewed
plan, exact APK pair and prepared guest before handing off to the shared
owner. The plan binds the proposal, source roster, Python and installed
tools. The owner checks the current v2 storage ledger for the same guest's
prepared 40 GiB reservation, and refuses an existing boot claim. The human
approval binds the pre-preparation ledger snapshot through the reviewed
proposal. At boot the owner consumes the matching preparation digest
inside the ledger lock, so a changed entry refuses before guest dispatch.
The run authorization carries the cold-navigation scope. The generic
receipt runner rejects that record.

The activation supervisor in `benchmarks/cold_navigation_ui_activation.py`
accepts an already prepared admission and the operation's start time. It
uses the remaining 40-minute window and a 30-minute activation ceiling.
The job-owned worker publishes the boot handoff with its process identity
and deadline. The owner checks the published digest, supervisor and time
remaining before dispatch. The
activation worker replays the exact controller result, requested stop,
process cleanup and closed ledger entry. A failed controller with known
cleanup can still yield a verified guest closure.

The outer preparation operator still needs to perform fresh admission,
create the prepared records and invoke activation under its own watchdog.
The activation checks use the reviewed SDK19 shared ownership and cleanup
guards.

## Guarded device selector

After separate approval and normal storage, process ownership and device
admission, select the following runner, method and argument for one attempt.
Require an executed pass for the exact method. An assumption skip gives
no qualification evidence.

- Runner `org.locallore.app.draftprocessverify.test/androidx.test.runner.AndroidJUnitRunner`
- Method `org.locallore.app.ColdNavigationFreshTaskTest#reopensConfirmedChildFromPrivateHintWithoutSavedTaskState`
- Instrumentation argument `cold_navigation_v1=true`

The application and test APKs must come from the same isolated build. The
test leaves previous runs ineligible for reuse. Retain test output and the
bounded created/command proof records under `noBackupFilesDir/process-verify-v1`.
Actual Android execution remains pending.
