# LocalLore Android engine demo

The Compose shell calls the actual Rust engine through a bounded JNI interface.
It uses **fake inference**, original Lantern Quay fixtures and the shared SQLite
workspace for durable accepted history. Kotlin implements no gameplay rules.
No real model, account or network dependency during play is present.

## Build and run

Install Java 17, Android SDK platform 36, Build Tools 35.0.0, NDK 29.0.14206865,
and Rust 1.93.1 with rustfmt/clippy. Provision both Rust Android targets:

```powershell
rustup target add --toolchain 1.93.1 x86_64-linux-android aarch64-linux-android
cargo fetch --locked
```

Set JAVA_HOME and ANDROID_HOME (or ignored local.properties SDK path).
From apps/android/ on Windows (use ./gradlew on Unix):

```powershell
.\gradlew.bat :app:assembleDebug :app:assembleDebugAndroidTest :app:testDebugUnitTest :app:lintDebug --no-daemon
.\gradlew.bat :app:connectedDebugAndroidTest --no-daemon
.\gradlew.bat :app:installDebug --no-daemon
```

preBuild compiles/packages Rust for x86_64 and arm64-v8a. Generated binaries stay
under app/build; none are checked in. See [native build details](../../docs/native/BUILD.md),
including Windows linker handling. After provisioning, add --offline for cached
Gradle/Cargo builds. Provisioning can use network; installed gameplay cannot.

For the complete host-independent Android build gate, run from the repository root:

```powershell
python scripts/check.py android --offline --clean
```

This checks wrapper integrity, invokes Gradle through Java, disables automatic
SDK downloads, builds app/test APKs, runs JVM tests/lint, and audits final APK
permissions/native alignment. Set `ANDROID_HOME` or `ANDROID_SDK_ROOT` for the
audit even when standalone Gradle uses `local.properties`. No SDK licenses are
accepted and no device is changed. See [shared check details](../../docs/ci/CHECKS.md).

Connected tests install the app/test APK. Use authorized targets only. Set
ANDROID_SERIAL to select one, then repeat for the second. Omit transport IDs
from public reports. This packet executes on two x86_64 API-35 emulators;
ARM64 runtime and physical-device qualification remain separate gates.

No platform Internet, media, contact or location permission is requested.
AndroidX adds an app-owned signature receiver permission. Backup exclusions
are configured; these tests do not qualify OS backup behavior. Existing Gradle,
AGP, Kotlin/Compose pins and locks remain explicit. See the [Android toolchain](../../docs/android/TOOLCHAIN_2026-10-22.md)
and [JNI source/license inventory](../../docs/native/SOURCES_2026-10-22.md).

## Exercise the engine

Give the potion to Mira, then try giving it again and using the unlearned ability.
Only finalized shared-engine receipts enter the transcript. **Demo responses**
injects malformed, rejected, delayed and failing generation. **New story** creates
a new independent saved story and retains earlier stories in **Saved stories**.
Cancel reconciles against accepted history: a commit that already won remains
visible. Simulated delay is not a performance measurement.

Accepted state survives Activity recreation and native/process owner recreation.
Startup resumes a default saved story; use **Saved stories** to select another.
The displayed path is the actual database in app-private `noBackupFilesDir`,
with workspace contract version 1 and database schema version 2. Uncommitted responses remain separate from canon;
resuming does not regenerate or automatically apply them. Closing the app does
not delete saves. All SQLite/replay/JNI work runs on IO workers. Generation runs
outside the canonical lock and SQLite transaction. A lost commit acknowledgement
is looked up with its original turn key; **Recover saved progress** retries
uncertain work without allocating a new key. See [app durability](../../docs/native/APP_DURABILITY.md).
The earlier [ADR-0004](../../docs/adr/0004-android-engine-boundary.md) remains the
legacy in-memory boundary fixture; production now uses the shared Host-v1 adapter.

Disposal is terminal: retained Reset callbacks cannot reopen native sessions.
The [ownership follow-up](../../docs/native/OWNERSHIP_FOLLOWUP_2026-10-22.md)
records the regression and additional lifecycle/worker replacement checks.

The recorded adapter/samples live only in src/test. The legacy NativeDemoGateway
and Registry remain boundary-test fixtures; MainActivity selects DurableGateway
and NativeWorkspaceTransport. Their host drift check remains:

```powershell
cargo run --locked --offline -p locallore --example android_fixtures -- --check
```

The exporter regenerates apps/android/app/src/test/lantern_quay_cases.json;
preserve UTF-8/LF without BOM after intentional changes.

## Transfer a playable story

Open **Story archive** while the saved story is idle. **Capture export preview**
captures accepted history for every timeline, including hidden facts, messages,
and model/provenance/timing references. Review the full-private plaintext warning
before **Export this full private archive** opens the system document picker.
The writer refuses an opened destination that is nonempty, nonregular, or not
seekable. A cancelled or failed write can leave a partial new document.

**Choose archive to validate** reads a bounded document, validates it through
the shared Rust archive contract, then shows a preview. **Import validated
archive** is separate consent. Rust replays into a fresh private staging Store
and cleans that stage before the target transaction. Existing story IDs conflict;
imports never overwrite/remap them. **Open imported story** is explicit and starts
a fresh session. Closing refreshes the accepted saved-story library.

Model weights, separate diagnostics/raw prompt logs, caches, and uncommitted
operations are excluded. The document provider may sync plaintext elsewhere.
Checksums establish consistency, not authorship. Cancellation can race an
already committed import; refresh the library before retrying. A provider that
does not return can delay cancellation cleanup; Close holds the shell guard
until active work and outstanding picker callbacks drain.

The [narrow native boundary](../../docs/native/ANDROID_ARCHIVE_BOUNDARY.md),
[verification](../../docs/native/ANDROID_ARCHIVE_VERIFICATION_2026-10-23.md), and
[shared format](../../docs/storage/M08_PLAYABLE_ARCHIVE_V1.md) describe limits.
This adds no inference dependency, network/storage permission, or automatic upload.

The separate [Windows–Android proof](../../docs/native/PLATFORM_ROUNDTRIP_VERIFICATION_2026-10-23.md)
transfers original fixture bytes through actual Rust/JNI and verifies replay,
branch snapshots and continued play. It uses a headless Windows fixture tool;
full system-chooser and desktop UI transfer remain separate gates.

## Review local diagnostics

Open **Local diagnostics** while the demo is idle to review its frozen JSON.
The log holds at most 64 enum/numeric timing/error records in memory, without
story text, identifiers, paths or exception messages. **Clear** empties the log
without changing accepted events. **Export JSON** opens the system
document picker and writes exactly that preview (at most 16 KiB).

The export is plaintext; your selected provider may sync outside the device.
Failure or cancellation can leave an incomplete file. Clearing the log does
not delete copies you exported. There is no automatic file, issue upload,
collector, crash-report SDK, new dependency or storage permission. A provider
that ignores cancellation can delay future exports; provider I/O and its
cancellation listener remain off the UI thread. See [diagnostic evidence](../../docs/diagnostics/VERIFICATION_2026-10-22.md)
and [privacy boundaries](../../docs/PRIVACY_AND_THREAT_MODEL.md).

## Verification and limits

The opt-in isolated archive application also has an explicit
[system chooser verification procedure](../../docs/native/ARCHIVE_CHOOSER_VERIFICATION_2026-10-23.md).
Its synthetic DocumentsProvider is packaged only in the instrumentation APK;
the normal application receives no provider or storage permission. These tests
retain their synthetic imported stories and never reset the existing workspace.
The [interruption follow-up](../../docs/native/ARCHIVE_RECOVERY_VERIFICATION_2026-10-23.md)
adds an explicit external owner for live app force-stop/relaunch. Deliberately
interrupted arms are separate from passing verification tests; independent host
transaction-kill checks do not imply Android mid-transaction or power-loss proof.
The separate [capacity follow-up](../../docs/native/ARCHIVE_CAPACITY_VERIFICATION_2026-10-23.md)
uses `.archivecapacity` and an enforced exclusive Gradle cache to exercise actual
SQLite Full, exact rollback and cache-only relief before fresh consent/retry.
Its fixture JNI and 96-page SQLite default are absent from ordinary builds.
This is a bounded page-limit proof, not physical device ENOSPC qualification.

Host tests cover strict bytes, scoped IDs, ownership, idempotency, provider
failures, cancellation/commit races and cleanup. JVM tests cover publication,
cancellation/disposal and uncertain outcomes. JNI instrumentation exercises
actual events/resources, invalid arrays and repeated cancellation/disposal;
Compose tests cover flows, reset/recreation/disposal and doubled-font layout.
Exact evidence is in [native verification](../../docs/native/VERIFICATION_2026-10-22.md).

Shared durability is wired to the app; real-device/process-kill instrumentation
and M01 physical/model feasibility remain separate unmeasured gates.
Local build checks do not establish hosted CI execution or release readiness.
