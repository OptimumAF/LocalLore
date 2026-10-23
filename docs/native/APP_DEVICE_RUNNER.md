# Explicit Android app process-restart runner

`scripts/android_app_restart_smoke.py` is test-only transport for M04.03/M04.04.
It calls the source-built instrumentation phases
`org.locallore.app.DurableRestartTest#checkpointAcceptedStory` and
`#resumeAfterProcessStop` with the same fresh private checkpoint token, with a
verified app force-stop between them. Kotlin instrumentation owns the UI and
checkpoint assertions; this runner owns transport ordering and cleanup evidence.
It does not implement gameplay, alter the storage schema, or supply inference.

The two APKs must already be installed on an explicitly authorized device. Use
matching local source-built APKs, then run explicitly (PowerShell example):

```powershell
python scripts/android_app_restart_smoke.py `
  --adb "$env:LOCALAPPDATA/Android/Sdk/platform-tools/adb.exe" `
  --serial emulator-5582 `
  --apk apps/android/app/build/outputs/apk/debug/app-debug.apk `
  --test-apk apps/android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk `
  --output target/app-restart-A.json
```

Create the explicit output's parent directory beforehand. The runner neither
installs nor creates a report anywhere else. Both phase methods skip during
ordinary instrumentation without this token. The checkpoint token, process
identity, saved story identifiers, paths, raw instrumentation logs, and exception
text remain outside the public report. APK SHA-256 digests, fixed phase/stage
names, pass flags, and aggregate cleanup flags are the only report metadata.

Each phase requires both installed package paths to have exactly one APK and its
SHA-256 to equal the local APK captured before the run. Local files are rehashed
before each phase. Every force-stop separately revalidates the app identity;
only `org.locallore.app` is stopped. Split APKs fail closed. No PID from output is
signalled. An explicit `pidof` exit-0/exit-1 protocol distinguishes a live app
from absence; errors and malformed responses remain unknown. Instrumentation
must return one matching test start and one matching passing completion with
`current=1`, `numtests=1`, final success code and `OK (1 test)`. Missing, duplicate,
failed, skipped, malformed, and crash records fail the run.

All ADB clients use the existing bounded standard-library process owner (Windows
Job / POSIX process group), with a 20-second control deadline, a 180-second phase
deadline, and 128-KiB output limit. Host-client cleanup and app-process absence
are separate report booleans. Unknown client ownership prevents subsequent ADB
calls and any absence claim. Failed phase attempts are retained before final
cleanup. A failed final cleanup revokes the overall passing status without
rewriting preceding phase results. Failed runs may leave their own checkpoint
for diagnosis; the runner never clears app data, deletes saves, or retries phases.

Synthetic verification, without ADB or any installed APK:

```powershell
python -m unittest discover -s scripts/tests -p test_android_app_restart_smoke.py -v
```

The runner tests cover successful ordering, identity mismatch, split APKs,
malformed/duplicate/skipped/failing JUnit records, unknown host cleanup, nonzero
and boolean exit codes, stop/probe failure, local APK replacement, final cleanup
failure, missing local inputs, and private canaries. These host tests establish
transport behavior only. Actual production UI durability across process death
requires both phases to pass on each authorized emulator; physical-device,
ARM64, crash-at-every-transaction-boundary, and real-model claims require separate
evidence.
