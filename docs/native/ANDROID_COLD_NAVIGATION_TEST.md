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

The adapter has no target-launch entry point. A controller still needs to
bind the exact preparation, installation, test and teardown to a separately
approved one-use run.

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
