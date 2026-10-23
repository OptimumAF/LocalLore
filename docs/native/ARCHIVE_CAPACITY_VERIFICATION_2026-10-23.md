# Archive capacity rollback and retry verification — 2026-10-23

M08.06 bounded follow-up to open, unmerged PR79. Implemented and locally verified;
owner acceptance and the full milestone remain pending. No merge or release.
The [contract](ARCHIVE_CAPACITY_CONTRACT.md) defines the feature-only fixture,
fixed profile, UI boundaries and process owner. [Structured results](ARCHIVE_CAPACITY_RESULTS_2026-10-23.json)
retain the qualifying and failed attempts; [independent review](ARCHIVE_CAPACITY_REVIEW_2026-10-23.md)
is source/evidence review, not another execution or owner approval.

## What changed

The archive dialog now gives actionable storage-full guidance and requires a new
validated capability before retry. The native archive, Store, schema and engine
production interfaces are unchanged. No model, runtime dependency or permission
was added. The only extra JNI entry is a fixed development fixture, compiled
exclusively into the separately identified `.archivecapacity` debug build.

An original three-branch source retains divergent potion ownership and observer
canaries. A separate ten-turn control story supplies real deterministic memory
packets. Setup reaches 94 pages with six valid cache rows under the 96-page
connection default; the next cache publication reports actual SQLite Full.
An independent fresh Store successfully imports, replays, reexports and reopens
the same source under that cap before target pressure is tested.

Actual target import Full must leave zero source rows across eight canonical
tables, exact retained control counts/archive, unchanged Mira cache and a strict
reopenable database. Relief removes only the control player's derived cache
partition through the existing Store API, leaving Mira's one cache row and all
accepted history intact. The same capped binary then imports the source after
fresh validation/consent. No padding table, schema relaxation, accepted-history
deletion, raw canonical write or runtime cap increase is involved.

## Verification actually performed

| Check | Actual result |
|---|---|
| `python scripts/check.py host --offline` | 314 workspace Rust +3 linker +232 Python; formatting, strict Clippy and fixture audits pass |
| Default new native tests | Three pass; repeat Full, drop/reopen, exact rollback rows/canon/caches, scoped relief, import, Conflict, gift/retry/new-key Inventory refusal and ownership refusal |
| Separate compiled 96-page qualifier | One explicit ignored-by-default qualifier executed and passed with development-fixtures; no local test cap setter used |
| Final dedicated Gradle build | 79 tasks, 10 executed/69 up-to-date; 61 fresh JVM tests, zero failures/errors/skips; lint zero errors/one existing dependency warning |
| Configured ordinary `python scripts/check.py android --offline` | Pass, final 78 tasks, 8 executed/70 up-to-date; JVM task reused the preceding unchanged JVM source's results |
| APK audits | Both ABIs, 16 KiB ELF/ZIP alignment, seven product archive JNI exports, expected receiver permission and test-provider exclusion pass |
| Fixture isolation | Fixture export and MAX_PAGE_COUNT=96 string present only in capped libraries; absent from current ordinary and retained prior archiveverify libraries |
| Build guards | Six actual configuration checks pass: invalid false, combined variants, release request, debug-only inventory, missing exclusive cap cache and ordinary use of cap cache |
| Local APK preservation | Both capacity→ordinary build cycles preserve all eight nonordinary APK files byte-identically; ordinary outputs intentionally rebuild |
| Final selected A/B Android 15/API35/x86_64 | One actual Full/recovery method plus21 existing archive regressions each: **44 passing invocations**, zero failed/skipped/unfinished |
| Owned resources | Actual descriptor counters drain; all four archive and all four workspace lease slots can be reacquired after disposal; exact APK identities, all seven prior installed hashes, client cleanup and owned package/provider process absence pass |

The host gate leaves two entries explicitly ignored in default discovery: the
existing interruption IPC worker (invoked by its three parent qualifiers) and
this compiled-profile qualifier (executed separately). Neither is silently
counted as a default standalone pass. Rust/Python host checks ran at `44b81f6`;
the final `292be65ea372a742d8a815777e8faefd734f4a38` changes only four Android
instrumentation files afterward, verified by diff. The separate compiled-profile
run uses the final source. Later delivery commits contain documentation only.

The final capped APK pair is application
`aa09afc46d0921a1e43f739a3c6331f2fbd839301f533d2ca5ac0b5c4e4e6bb2`,
instrumentation `1d7fdbe216a7d720f0d3342711159cb61053f27dbdf45a2b8b572d4037aef967`.
The native library stayed identical during the test-only picker fix. Four
emulators and zero physical phones were visible; only the selected two received
this package. They were already running. No emulator restart, wipe, reset,
uninstall, data clear, root action or model copy occurred.

The actual Compose host uses real ShellViewModel, native workspace/archive
gateways and actual OpenDocument selection/grants. It is a ComponentActivity
instrumentation host. The 21 regressions include the two real MainActivity
tests and two actual system-chooser tests. Final tests exercise native Full,
rendered guidance, consumed-token InvalidToken, unchanged retained state,
fresh owners/selection/validation/consent, exact source reexport before play,
explicit Open, one gift, duplicate refusal and reopened revision3. The control
head remains10. Provider descriptors and both lease registries are checked
before the source-bound verified marker; the external owner then verifies
actual test terminals and stops only the hash-matching dedicated packages.

## Retained failures and corrections

Initial A passed the capacity method, while B failed. B's finally cleanup wait
masked its primary exception; the original cause remains unknown. This attempt
is a failure, not a cancellation or pass. Its owned cleanup and prior-package
guards passed. Extra regression A used a mistyped private selector
`ArchiveDocumentsTest` rather than `ArchiveDocumentTest`: the runner reported
17 entries, including15 passing bodies, one chooser-body failure and one JUnit
initialization error. The five document tests were not run in that attempt.
The private wrapper rejected the cohort rather than reporting21 passes.

Source review found a concrete coexistence hazard: the new and retained test
packages advertised the same DocumentsUI root title. Postfailure B was awake
on an empty root with that title. Wrong-root selection is consistent with the
observations, but is not proven to be B's masked primary cause. Provider titles
and all three chooser-test selectors now include the exact instrumentation
package. Capacity previews additionally assert the expected source story ID.
Teardown preserves the primary failure and records separate fixed-stage cleanup
failures while still attempting every independent cleanup. No timeout increased.
Both final capacity tests and both final21-test cohorts passed after these fixes.

All device attempts total **60 pass terminals, two failed test bodies and one
initialization error**. Only the final44 passes qualify the final test APK.
Superseded passes and failures remain separate rows with their actual APK/raw
hashes. A preliminary in-progress build was never installed; its artifacts are
not qualifying source evidence. The initial host check stopped on root module
formatting before tests; formatting was corrected and the full gate passed.
An author compilation failure selecting unsupported u64 SQLite row decoding was
corrected to bounded u32 before final handoff; coordinator independently verified
the integrated source. A private wrapper quoting error occurred before any build.

## Reproduce

Use existing pinned prerequisites: Rust1.93.1, Java17 (measured17.0.6),
Gradle8.11.1, AGP8.10.1, Kotlin2.2.21, compile/target SDK36, minimum26,
Build Tools35.0.0 and NDK29.0.14206865. Bundled SQLite is3.53.2 through
rusqlite0.40.2/libsqlite3-sys0.38.2. No new download is required with caches present.

```powershell
python scripts/check.py host --offline
# From apps/android, with JAVA_HOME and ANDROID_HOME configured:
& "$env:JAVA_HOME/bin/java.exe" -classpath gradle/wrapper/gradle-wrapper.jar `
  org.gradle.wrapper.GradleWrapperMain :app:assembleDebug :app:assembleDebugAndroidTest `
  :app:cleanTestDebugUnitTest :app:testDebugUnitTest :app:lintDebug `
  -PlocalLoreArchiveCapacityVerification=true --project-cache-dir .gradle-archive-capacity `
  --offline --no-daemon --console=plain -Pandroid.builder.sdkDownload=false
```

For the separate host compiled-profile qualifier, use a fresh shell with
`LIBSQLITE3_FLAGS=-DSQLITE_MAX_PAGE_COUNT=96` and an exclusive `CARGO_TARGET_DIR`;
run only the explicit qualifier in that profile:

```powershell
cargo +1.93.1 test -p locallore-storage --features development-fixtures --lib `
  archive_full_tests::native_compiled_page_profile_runs_the_unmodified_feature_boundary `
  --locked --offline -- --exact --ignored --nocapture
```

After authorized installation of **only** the dedicated app/test pair, the
public owner checks installed hashes and refuses other package identities:

```powershell
python scripts/archive_capacity.py --serial SELECTED_SERIAL --alias A `
  --adb PATH_TO_ADB --app-apk apps/android/app/build-archive-capacity/outputs/apk/debug/app-debug.apk `
  --test-apk apps/android/app/build-archive-capacity/outputs/apk/androidTest/debug/app-debug-androidTest.apk `
  --output-directory target/my-new-archive-capacity-proof
```

Use a new output directory/run for every attempt. The runner does not provision
devices or install APKs. Existing native/provider/Compose/MainActivity/chooser
regressions are explicitly selected as `ArchiveIntegrationTest` (6),
`ArchiveDocumentTest` (5), `ArchiveDialogTest` (6), `ArchiveActivityTest` (2)
and `ArchiveChooserActivityTest` (2); require matching21 starts/pass terminals.
Private all-attempt logs are retained under `target/checks/archive-capacity/`.

## Limits and handoff

This verifies actual SQLite Full from a bounded page default, not physical
partition ENOSPC. It does not qualify power loss, low-memory death, Android
mid-import transaction termination, arbitrary provider hard preemption, heap
release measurement, physical phones, ARM64 execution, 16 KiB OS pages or
real-model performance/quality. ARM64 is cross-built/audited only. M01.01 remains
blocked on an authorized available physical phone. Full M08 and owner acceptance
remain open; no checkbox was changed. Next runnable packet: M08.05 story deletion
and retained-branch resource cleanup, beginning with the shared Store contract.
