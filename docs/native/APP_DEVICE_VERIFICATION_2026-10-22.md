# Durable Compose/Rust boundary verification — 2026-10-22

Scope: M03.03 / [#7](https://github.com/OptimumAF/LocalLore/issues/7), with bounded
M04.03/.04/.05/.06 adapter checks under [#8](https://github.com/OptimumAF/LocalLore/issues/8).
The original engine integration #20 and ownership fix #35 were already accepted.
This packet preserves them and exercises the SQLite-backed production app from
#42, owner-merged into main `2612001` in a separate task. It introduces no model,
dependency, permission, schema change or production test hook. No upstream PR was
merged by this packet. The retired Markdown trackers remain compatibility pointers.

## Reproduced problems and changes

Four legacy UI assertions inferred Mira's current holdings from absence in the
player inventory. The production player-filtered snapshot correctly says
`Not in your inventory`. The assertions now retain accepted revision 1, exactly
two messages and the exact Rust gift narration. Duplicate transfer must still
reject without advancing revision or changing the transcript.

Two cancellation fixtures scrolled/clicked after the 200 ms fake had completed,
so their Cancel node no longer existed. These tests now control submit/cancel
ordering on one Main stack; a stable busy-state UI test independently clicks
the Cancel callback. Active native cancellation has its own synchronized test.
The recreation test explicitly covers an already-cancelled response. An initial
attempt to manually invoke Activity.onStop disrupted ActivityScenario's lifecycle;
that fixture was removed. It is not evidence of a production lifecycle defect or
of pending-work cancellation during actual OS rotation.

That deterministic ordering exposed a production edge case: cancellation can
reach Rust before the IO submit has registered its turn. `cancelSaved` treated
the explicit `UnknownTurn` rejection as storage uncertainty, unnecessarily
requiring recovery. Two independent, gated, actual-JNI regressions failed with
that exact category before the fix. The fix catches only this category, clears
only the same pending operation and retains cancellation on its captured request.
A late original submit may remain a draft, but cannot prepare, commit, regenerate
during recovery or clear a replacement operation. Other storage/transport errors
continue to require reconciliation. Accepted history remains authoritative.

## Ownership and process evidence

`DurableTransportOwnershipTest` uses the actual production transport and its
adapter-owned IO cleanup scope. A test-only ContextWrapper selects a newly
created private synthetic root; no path capability enters the production wire.
It observes Rust `turn_status=running`, pulses Main, cancels the original key,
awaits the worker and asserts revision 0, no receipts and the retained potion.
Six cycles repeat Main-thread close, reject future calls and verify that all
four native registry slots become available. Probe handles always close in
`finally`. A separate disposal case permits a prepared reply to win before
asynchronous close, but rejects a late commit on the disposed adapter and checks
unchanged canon after reopen. A prepared reply is not an accepted outcome.

The independent Rust registry test also prepares two owners on the same SQLite
file, closes one twice and proves that the survivor and a replacement retain the
same exact receipt. An abandoned draft remains separate. See
[independent review](APP_DEVICE_REVIEW_2026-10-22.md).

`DurableRestartTest` uses the production Activity, saved-story menu and transport.
Its explicit first phase creates a new synthetic story and commits one gift,
then saves a bounded private checkpoint of story/branch, revision, message digest
and process identity. The [explicit host runner](APP_DEVICE_RUNNER.md) verifies
both installed APK hashes, stops only the app, proves process absence and starts
the second phase. The second phase requires a changed process identity, selects
the exact saved story, compares the transcript digest and revision, rejects a
second gift, creates an independent story and resumes the original unchanged.
Only its checkpoint file/empty directory are deleted; actual saves remain.

The process start API is available from API24 according to the official
[Process documentation](https://developer.android.com/reference/android/os/Process#getStartElapsedRealtime()),
below the existing minimum26. No dependency was added. Normal discovery skips
the two externally coordinated methods without their validated token. The runner
requires actual matching pass records; a skip, missing test or ADB exit0 is insufficient.
Its 20 synthetic host tests include failure, malformed/duplicate/skip records,
APK replacement, unknown client ownership, failed cleanup and private canaries.

## Verification

Windows x86_64, Rust/Cargo1.93.1, Python3.9.12, JDK17.0.6, Gradle8.11.1,
AGP8.10.1, Kotlin/Compose compiler2.2.21, NDK29.0.14206865,
SDK compile/target36/min26. Existing pins/locks are unchanged.
Both selected emulators are `sdk_gphone64_x86_64`, Android15/API35,
x86_64, 4096-byte pages. Inventory showed five emulators and no physical phone;
the other three were untouched. Data-preserving APK updates used `install -r -t`.
The isolated SDK benchmark package, processes and cached model were not operated.

| Command/procedure | Actual result |
|---|---|
| `python scripts/check.py host --offline` | Passed: 123 Rust workspace entries, 211 Python tests, four fixture comparisons, three linker tests, format/strict Clippy |
| `python scripts/check.py android --offline` at final production fix `e6af9c7` | Passed: both native ABIs, app/test APKs, 38 JVM tests, lint and APK audit; zero lint errors, one existing dependency-version advisory |
| Final native instrumentation group on A and B | 15 passed on each; zero failures/skips |
| Final Compose group on A and B | 12 passed on each; zero failures/skips |
| Final diagnostic resource/dialog group on A and B | 13 passed on each; zero failures/skips |
| Final explicit process-restart phases on A and B | Both phases passed on each; verified intermediate/final app absence and host-client cleanup |
| `git diff --check` | Passed |

The host test count includes the existing auxiliary storage process helper; it
does not mean 123 gameplay scenarios. Independent review compiled its two new
instrumentation cases offline; only the coordinator performed emulator execution.

The final APKs are app SHA-256
`56ec9d0c20736a772ed7bda9372cdccb300ed8ef1ce609a3158c926e75839ebb` and test APK
`ab116c176524f13493105941cbc1e6bf79707d5e1fa72f8cb444f94596ca7651`.
Each class group verifies installed app/test hashes before execution. On each
target the three ordinary groups cover40 distinct cases, followed by two actual
passing externally coordinated phases: **42 per target /84 total**, zero final
failures/skips. This is grouped complete coverage, not one monolithic invocation.

From the repository root, with final matching app/test APKs already installed,
the actual class selections were:

```text
adb -s <authorized-target> shell am instrument -w -r -e class org.locallore.app.NativeBoundaryTest,org.locallore.app.NativeLifecycleOwnershipTest,org.locallore.app.DurableNativeTest,org.locallore.app.DurableTransportOwnershipTest,org.locallore.app.DurableCancellationReviewTest org.locallore.app.test/androidx.test.runner.AndroidJUnitRunner
adb -s <authorized-target> shell am instrument -w -r -e class org.locallore.app.ShellInstrumentedTest,org.locallore.app.ShellLayoutTest,org.locallore.app.DiagnosticsIntegrationTest org.locallore.app.test/androidx.test.runner.AndroidJUnitRunner
adb -s <authorized-target> shell am instrument -w -r -e class org.locallore.app.DiagnosticWriterTest,org.locallore.app.DiagnosticsDialogTest org.locallore.app.test/androidx.test.runner.AndroidJUnitRunner
python scripts/android_app_restart_smoke.py --adb <adb-path> --serial <authorized-target> --apk <final-app.apk> --test-apk <final-test.apk> --output <ignored-local-report.json>
```

Repeat on the second selected target. The coordinator used the bounded existing
process owner,180s maximum per instrumentation group, with ignored local raw
capture and installed-hash guards. Final ordinary JUnit durations were A:2.348s,
150.952s,46.321s; B:2.349s,132.599s,39.041s. These include test/UI overhead and
are not gameplay performance measurements. APK digests establish the tested
artifacts, not a byte-identical build guarantee.

All intermediate instrumentation attempts are retained in the
[sanitized result artifact](APP_DEVICE_RESULTS_2026-10-22.json). Two initial
attempts lost their output because the host collector referenced nonexistent
`ProcessResult.stderr`; they are unverified, not counted as passing or failing.
The corrected A baseline reached 33 terminal records out of35 before its180s
deadline:29 passes/four failures, with one started/unfinished and one unstarted.
The candidate1 Shell run was4/6 and diagnostics3/4, with the fixture and recovery
issues described above. The gated pre-fix regression was0/2. B's initial durable
JNI5/5, candidate production ownership2/2 and candidate restart phases passed.
Final tests are grouped to stay within the same bounded deadline; no timeout or
canonical assertion was relaxed to turn an earlier attempt into a pass.

Raw instrumentation, checkpoint identities, paths and transport IDs remain under
ignored local build output. Public evidence contains fixed case names, APK hashes,
aggregate results and cleanup flags. The runner's final app stop and host-client
cleanup are distinct checks; a successful earlier phase cannot hide failed cleanup.

## Limits and handoff

This is real Rust/JNI/SQLite and Compose execution with deterministic fake
inference. It is not Android integration of the experimental LiteRT provider,
physical-phone/model performance, ARM64 execution, 16KiB OS qualification, hardware
power-loss testing, heap profiling or proof about future inference allocations.
Main responsiveness was observed in finite delayed fake runs. Broader M04 fault,
disk-exhaustion and recovery tooling gates remain separate. No hosted CI run,
release, merge, settings change or milestone closure is inferred.

M03.03 retains its accepted status; this bounded follow-up awaits its own review.
M01.01 remains blocked on an authorized physical phone. The next runnable app task
is M04.04: coordinated framework Activity stop while durable prepare is in flight,
with accepted-history reopen checks. The current recreation fixture deliberately
does not claim that lifecycle interleaving. Real inference, broader free-text and
memory features retain their dependency gates.
