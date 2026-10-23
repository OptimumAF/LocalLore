# Actual SQLite Full through Compose — 2026-10-22

Scope: bounded M04.04 / [#8](https://github.com/OptimumAF/LocalLore/issues/8),
stacked on unmerged #50 → #49 → #44. This is an explicitly different test binary
over the existing production Rust workspace/JNI/gateway and Compose shell.
Inference remains deterministic and fake. No production fault command, SQL
capability, storage schema, gameplay rule, permission or dependency is added.
GitHub tickets own acceptance; no milestone checkbox or merge follows from this report.

The same frozen APK pair completed three methods on each selected emulator:
**six final passes, sixteen asserted actual Full commit replies**, zero final
failures/skips/unfinished methods. Across all three retained attempts there are
eight passes and one initial B framework-teardown failure. That earlier failure
remains unexplained; this is not failure-free reliability qualification.

## Mechanism and bounded calibration

The pinned bundled SQLite is compiled with `SQLITE_MAX_PAGE_COUNT=15` only in
capacity mode. The actual Rust Pager therefore returns SQLITE_FULL when the
gift commit needs another page. An external Android SQLite connection cannot
set this owner's limit. This exercises real SQLite failure through Rust, JNI,
gateway, ViewModel and collected Compose state; it does not exhaust a partition.
The [independent review](CAPACITY_REVIEW_2026-10-22.md) links official/pinned
compile-option, Gradle/AGP API and licensing evidence. Existing pins are unchanged.

The new explicit Host-v1 `capacity_probe` example uses the original synthetic
setting, a fresh directory and actual submit/prepare/commit/status/snapshot calls.
It neither opens raw SQL nor reads live database bytes. Metadata length after
completed calls was 61,440 bytes at create/draft/Ready and 65,536 after an uncapped
gift. A separate capped build returned Full on commit and retry, retained Ready
and the entire player snapshot, then reopened the original draft queued at
revision 0. SQLite's pinned default page size is 4,096; calibration did not query
PRAGMA page_size. Stop-at-first-sufficient selection chose no dialogue prefix
(K0), not an exhaustive search of all supported prefixes.

The author retained six positive focused host executions: two uncapped K0,
one uncapped K1 control, three capped K0. Four captured JSON artifacts supply
the public calibration rows; not every earlier execution produced JSON.
Focused offline example Clippy with `-D warnings`, rustfmt and diff checks passed.
Representative commands, with fresh directories and distinct target caches:

```powershell
$env:CARGO_PROFILE_DEV_DEBUG='0'
$env:CARGO_INCREMENTAL='0'
$env:CARGO_TARGET_DIR='target/capacity-baseline'
# LIBSQLITE3_FLAGS must be absent for the ordinary baseline.
cargo run --locked --offline -p locallore-workspace --example capacity_probe -- --directory target/capacity-baseline/verify0 --prefix 0
$env:CARGO_TARGET_DIR='target/capacity-15'
$env:LIBSQLITE3_FLAGS='-DSQLITE_MAX_PAGE_COUNT=15'
cargo run --locked --offline -p locallore-workspace --example capacity_probe -- --directory target/capacity-15/verify0 --prefix 0 --expect-full
Remove-Item Env:LIBSQLITE3_FLAGS
```

The compile setting is immutable through the app's frozen wire. Repeated Full
and reopen safety do **not** establish accepted same-key recovery after freeing
capacity. That remains a separate technical gate.

## Isolation and discovered corrections

`python scripts/android_capacity_probe.py build --offline` selects the fixed
source-controlled profile, application ID `org.locallore.app.capacity`, visible
`LocalLore · SQLite capacity test` label, testOnly flag and exact N15/K0 metadata.
Only debug exists. Capacity instrumentation has its own source root and
provider-free manifest; it cannot collide with the installed ordinary test
APK's diagnostics authority. App classes/JNI names remain unchanged.

Cargo, generated JNI, tools, APKs and reports use `app/build-capacity`. The
helper also passes a separate `--project-cache-dir` at `apps/android/.gradle-capacity`.
Both mode/cache pairing and nonempty ambient `LIBSQLITE3_FLAGS` are checked at
configuration, even for otherwise up-to-date tasks. The ordinary Cargo child
receives an empty flag value; the capacity child receives the one fixed macro.
Native-task inputs include mode/profile/flags. Build/check helpers never install
or operate ADB; no default check runs capacity or model experiments.

Initial configuration had a release-label escape; independent review caught it
and non-debug capacity variants were disabled before any APK qualification.
An initial native build failed due Kotlin's `java` extension shadowing the
Properties type; an explicit import corrected it. Both attempts are retained.
The first full APK build passed, but its new audit expected a different AAPT
representation. The audit now uses actual pinned AAPT true/decimal records and
the instrumentation XML element, with rejection tests. APK contents did not
change for that correction.

More significantly, the first ordinary-mode rebuild **removed the packaged
capacity APKs**. Separate output directories alone do not isolate Gradle task
history: previous outputs may be removed from another location during task
execution. The corrected helper/configuration require separate project caches.
Regeneration reproduced the exact initial capacity APK hashes. Subsequent
ordinary and capacity alternation retained all four APK hashes; neither mode's
task history now removes the other's artifacts in the measured sequence.
This is measured Windows evidence, not a universal build-reproducibility claim.
Ordinary rebuilt APKs differ from the previously installed pair; no byte identity
to that earlier build is claimed or required. Neither ordinary APK was installed.

## Actual device cases and collection

The three capacity-only methods require runtime package/testOnly/label/profile
identity before creating a fresh private synthetic root. A recording wrapper
passes native envelopes through unchanged. Assertions cover:

- Actual Ready commit Full, two original-key recovery failures, one submit/prepare,
  no receipt or revision advance, unchanged player snapshot and one queued draft
  after owner close/reopen without automatic prepare/commit.
- Collected Compose's exact fixed Full guidance, retained confirmed presentation,
  disabled action/mode controls, blocked retained callbacks, two repeated recovery
  attempts, terminal disposal and the same unchanged view after reopen.
- Explicit cancellation after two actual Full replies, no potion spend, persisted
  Cancelled status, no pending draft, and original-request resubmission after reopen
  still cancelled without prepare/commit.

A complete passing cohort requires eight actual Full commit replies (3+3+2).
Checks compare the accepted **player-scoped** snapshot/receipts and presentation;
they are not an independent omniscient inspection of every world record. Each
fixture closes models/transports, drains exchanges, proves all four native owner
slots available, and deletes only its verified tiny synthetic root. Cleanup
failures are combined with primary failures. These are finite registry ownership
checks, not heap measurements or real-model allocation tests.

Only the two authorized Android15/API35/x86_64 emulators were operated. Fresh
inventory: five emulators, zero physical phones; other three untouched. Both
selected targets use 4,096-byte OS pages. New capacity IDs were absent before
data-preserving installation; ordinary installed app/test hashes are verified
before and after each successful cohort. No ordinary stop/install, data clear,
uninstall, root, reboot, mount, disk filler or device setting change occurred.

The explicit ignored collector retained start/terminal JSONL and raw output,
used the existing bounded process owner and strict parser from #46, required
all three expected matching pass records, and guarded installed/local APK hashes.
Instrumentation deadline remained 180 seconds and output cap 128 KiB. ADB exit 0
or an `OK` substring alone is insufficient. Final verified cap-app stop/absence
and host-client cleanup are separate from method passes. Equivalent device command:

```powershell
adb -s $env:ANDROID_SERIAL install -t apps/android/app/build-capacity/outputs/apk/debug/app-debug.apk
adb -s $env:ANDROID_SERIAL install -t apps/android/app/build-capacity/outputs/apk/androidTest/debug/app-debug-androidTest.apk
adb -s $env:ANDROID_SERIAL shell am instrument -w -r -e class org.locallore.app.SqliteCapacityInstrumentedTest org.locallore.app.capacity.test/androidx.test.runner.AndroidJUnitRunner
```

Use only an authorized selected target and verify installed identities; do not
blindly replace an existing capacity app. Raw logs, transport IDs, private paths
and story identifiers remain ignored. Public results contain fixed case names,
hashes, counters and cleanup flags.

## Retained failed B attempt

The initial A cohort passed all three methods. Initial B returned two passes
and one failed cancellation method: ActivityScenario teardown never reached
DESTROYED, reporting last state PAUSED. The reported stack is framework
`ActivityScenario.close` / rule teardown, with no reported fixture body frame.
That is a failed method; absence of a body stack does not prove all internal
assertions or cleanup passed.

The initial B collector's final local hash guard could not read the deleted
capacity APKs, so its original final app absence/ordinary hash cleanup flags are
unverified. Separate supplemental checks verified installed cap identities,
captured bounded diagnostics, stopped only the cap app, proved absence and
ordinary installed hashes/client cleanup. They do not rewrite the original row.
The captured logs lack the earlier graphics-finalizer/system-server Watchdog
signatures; cause and fixture relationship remain unknown. No framework repair
or abort-free reliability is claimed.

After the build-isolation correction, byte-identical cap APK regeneration,
readiness checks and completion of host builds, one unchanged-fixture B rerun
was authorized as the bounded final qualification attempt. Results and exact
all-attempt counts are in [the artifact](CAPACITY_RESULTS_2026-10-22.json).

## Verification and limits

Windows x86_64, Rust1.93.1, Python3.9.12, JDK17.0.6, Gradle8.11.1,
AGP8.10.1, Kotlin/Compose compiler2.2.21, NDK29.0.14206865,
compile/targetSDK36, min26, BuildTools35.0.0. No new dependency or license choice.

| Actual check | Result |
|---|---|
| Focused Host example Clippy, Rust format | Passed; no fresh complete workspace Rust gate claimed |
| `python -m unittest discover -s scripts/tests -p test_*.py` | Final43 passed; initial42 also passed before cache regression test |
| Initial native-only capacity build retry | Both ABIs passed; first Kotlin script failure retained |
| Capacity full build1 / corrected build2 | 47 fresh JVM tests each, zero failures/errors/skips; build1 audit-format failure retained; corrected audit passed |
| Ordinary offline Android build | Both uncapped ABIs,47 fresh JVM tests, lint/APK audit passed |
| Default/capacity alternating builds | Audits passed; reused JVM/native tasks explicitly not new test execution; all four APK hashes retained |
| Configuration failure/success probes | Seven passed, including mode/cache/ambient/release guards |
| APK audits | Distinct manifests, test target/provider isolation, both ABI limits and 16KiB ELF/ZIP alignment passed |
| Emulator cohorts | See all-attempt artifact; failed initial B retained separately |

Lint has zero errors and one existing GradleDependency advisory; capacity
instrumentation compilation also reports two existing-API metadata access
deprecation warnings in the new fixture. No runtime compatibility result is
inferred from warnings or a successful cross-build.

M04.04 remains partial/in_review pending owner acceptance and wider gates. No
physical phone, real-model Android inference, ARM64 execution, API26/36 or16KiB
OS execution, partition ENOSPC, power loss, heap/performance qualification,
successful capacity-relief recovery, hosted CI, merge or release is established.
Next runnable reliability work is an ordered control/fixture investigation of
the retained Activity teardown failure; actual same-key recovery after capacity
relief needs its own separately claimed test mechanism.
