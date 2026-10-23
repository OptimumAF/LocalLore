# Actual SQLite contention through Compose — 2026-10-22

Scope: bounded M04.04 ([#8](https://github.com/OptimumAF/LocalLore/issues/8)),
stacked on open #49 at `fe5c151`. No merge or full milestone acceptance follows.
GitHub owns the work log and claims; the retired Markdown trackers remain pointers.

The preceding recovery packet injected Full/Busy protocol replies through real
Rust/SQLite. This packet adds an actual conflicting SQLite writer against a
fresh synthetic app-private database and requires unmodified native Busy replies.
The ordinary app and Rust engine are unchanged. Inference remains the local
deterministic fake.

## Mechanism and rejected approach

An in-process Android SQLite holder was rejected during independent source
review before any build or device run. Android and Rust link separate SQLite
copies; their independent in-process bookkeeping cannot safely coordinate
POSIX process-owned locks. A worker thread alone does not solve this.

The replacement is a test-APK-only `SqliteWriterProcess` entry point launched
through the installed Android `app_process` runtime. It inherits the app UID
but must report a distinct process identity. Its classpath contains only the
already-installed read-only test and app APKs. It opens only the verified fresh
fixture's existing SQLite file, using platform SQLite on its main worker thread.
It never loads Rust or `NativeWorkspace`.

The holder verifies identity/schema and existing DELETE journal mode, opens with
`NO_LOCALIZED_COLLATORS` and explicit DELETE configuration, then obtains an
IMMEDIATE reservation. It executes no gameplay write or migration. Readers may
continue while Rust's writer admission fails. A bounded private token protocol
acknowledges acquisition and rollback/close; successful tests require explicit
release, exit 0 and drained pipes. Process cleanup uses only the owned Java
Process handle, with bounded waits and a preselected self-lease expiry.

The parent wraps timing and records fixed native operation/status/error/key
metadata, returning every Rust reply unchanged. It opens no platform-SQLite
connection to that file. New fixtures use create-new private roots, retain
primary and cleanup failures, release the holder before native teardown, drain
exchanges and acquire/release all four native owner slots before removing only
the verified fixture root. No component, manifest, permission, dependency,
production SQL capability, native API or fault hook is introduced.

See the [independent mechanism review](SQLITE_PRESSURE_REVIEW_2026-10-22.md)
for official SQLite/Android sources and the separate actual-Full prerequisite.
API 28+ holder APIs are used only by the test entry point; this is not minimum
API 26 qualification or a production subprocess design.

## Build and source identities

The fixture was authored as `61e44f0b74bda573e526245dbddfe4020ab7fc9f` and
integrated as `58a5c98`. Review and evidence commits change only documentation.
No fixture or production source has changed since the build.

```powershell
python scripts/check.py android --offline
```

This incremental gate passed on the first attempt with the existing Java 17 /
Android SDK environment: new instrumentation Kotlin compiled and the test APK
was packaged; APK audit passed; lint has zero errors and one existing
GradleDependency advisory. Gradle reported 78 actionable tasks, seven executed
and 71 up-to-date. `testDebugUnitTest` reused #49's verified 47-test XML
(zero failures/errors/skips); those JVM tests were **not re-executed here**.
Native Rust build and app packaging were likewise up-to-date. Both native ABIs
remain packaged; this is not a fresh native rebuild or clean-room build. No
Rust/Python host gate was rerun for this test-only Kotlin change. The existing
SDK/NDK/Gradle/dependency pins are unchanged; no dependency was selected.

App SHA-256 (unchanged from #49):
`f17db036fed45bac28d1a27d8632e3f6631d641092be8247a4ef053a7b324393`.
New test APK SHA-256:
`6cd6e37925fe2d362be904e0a55a87133eca71b6fdad0c060c9eda83b01300a2`.

## Actual device execution

The new fixture ran on both selected targets with unchanged APKs. Each complete
three-method cohort requires two actual Busy submit replies, three Busy commit
replies and two Busy cancellation replies. Acquisition/release token, distinct
PID/same UID, normal child exit, drained pipes, native exchange drain, all four
native owner slots and exact-root cleanup are assertions in the fixture. A
passing method also requires the original request/key, unchanged accepted
history while blocked, exact single gift after release or safe cancellation,
and an actual Rust-owner reopen. These successful-cohort checks qualify normal
release. Forced destruction and self-lease expiry were not deliberately exercised
or independently qualified; the unfinished method's child lifecycle is unknown.

The same frozen APKs passed these final groups on each target:

| Group | A | B |
| --- | ---: | ---: |
| New actual SQLite contention | 3 | 3 |
| Existing injected-frame recovery | 8 | 8 |
| Existing JNI/cancellation/ownership | 15 | 15 |
| Complete final cohorts | 26 | 26 |

That is **52 passing executions / 26 unique methods** across six complete final
cohorts, zero failures/skips/unfinished within those cohorts. The separate
incomplete B attempt below adds two passing completions and one unfinished
start: **54 pass completions and one unfinished case across all seven attempts**.
This is not abort-free reliability evidence. All six final cohorts prove app
absence/client cleanup; the aborted attempt needs the separate recovery checks.
No candidate test source, timeout or assertion changed between attempts.

The [sanitized results](SQLITE_CONTENTION_RESULTS_2026-10-22.json) retain all seven
attempts, build/preflight metadata and supplemental abort recovery. The
[independent review](SQLITE_PRESSURE_REVIEW_2026-10-22.md) records source and
artifact inspection. Existing diagnostics/layout and explicit process-restart
results from #49 remain separate; their unchanged sources were not rerun here.

### Retained incomplete B attempt

The first B cohort completed the Compose-commit and cancellation/late-story
cases, then started the submit case without a completion record. Instrumentation
explicitly reported `INSTRUMENTATION_ABORTED: System has crashed`. ADB exited 0,
but the strict parser correctly marked the cohort invalid: two passed methods,
one started/unfinished, no assertion-failure record. Original final app absence
could not be verified; client cleanup succeeded. This is not a passing cohort.

Bounded read-only log capture identified Android **system-server Watchdog**
killing itself after WindowManager's global lock/display/animation monitors
were blocked for 63 seconds. The animation stack was in
`ScreenCapture.nativeCaptureLayers`, task snapshot creation and BLAST transitions.
The earlier app graphics-finalizer signature was absent. The underlying cause
and relationship to the fixture remain unknown/unfixed; no app or OS repair is
claimed. Raw system logs remain ignored/private, with only fixed classifications
in the public report.

After framework recovery, separate bounded checks verified both installed APK
hashes, stopped only the verified app and proved absence/client cleanup. A
process-command snapshot found zero holder-class matches; it does not retroactively
prove the unfinished method's child release or original cleanup. Boot/window/
activity readiness was checked before **one unchanged-APK rerun**, which passed
all three methods. No source, delay, timeout, renderer, disk, app-data or system
setting changed. The failed synthetic root was not manually deleted. The original
attempt and supplemental cleanup/readiness evidence remain separate.

## Reproduction and evidence collection

After the documented build, select an explicitly authorized emulator and update
the app/test APKs with `adb install -r -t`, preserving its existing saves. Run:

```powershell
adb -s $env:ANDROID_SERIAL shell am instrument -w -r -e class org.locallore.app.SqliteContentionInstrumentedTest org.locallore.app.test/androidx.test.runner.AndroidJUnitRunner
```

The coordinator used separate serial A-then-B cohorts under
`target/checks/sqlite-contention/`: durable start/terminal journals, installed and
local APK hash guards, the existing bounded process owner, a 180-second
instrumentation deadline, 128-KiB output cap and the strict parser from #46
(`ad173d9`). All expected method identities/counts and final status must match;
ADB exit 0 alone is insufficient. The ignored collector is not a production
dependency/default check. Existing recovery and JNI/ownership groups followed
the new fixture to check for interference. Raw stacks, paths, holder tokens/
PID/UID and synthetic content remain private.

Fresh preflight observed five attached emulators and zero physical phones. Only
A and B were selected: Android 15/API 35, x86_64, sdk_gphone64_x86_64. Their
installed app matched #49's `f17db036fed45bac28d1a27d8632e3f6631d641092be8247a4ef053a7b324393`;
bounded identity-guarded app stops proved absence and client cleanup. Other
emulators/models/saves are preserved. M01.01 remains blocked on an authorized
physical phone.

## Limits and remaining gates

Actual Full-through-Compose is not achieved by this Busy fixture. External
`max_page_count` configures its own Pager and cannot impose a quota on Rust's
owner. The review identifies the missing isolated capacity/test-binary
prerequisite. #48's native Store page-cap Full and #49's injected UI errors
remain distinct evidence. I/O errors, read-only files or fabricated replies
cannot substitute for actual SQLITE_FULL.

No physical-phone/model performance, ARM64 execution, heap high-water, partition
exhaustion, hardware power loss, hosted CI or release readiness is claimed.
The earlier graphics watchdog cause remains unknown/unfixed. No data clear,
uninstall, reboot, root, emulator setting change, merge, release or repository
administration is part of this packet.
