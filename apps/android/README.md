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
with shared schema version 1. Uncommitted responses remain separate from canon;
resuming does not regenerate or automatically apply them. Closing the app does
not delete saves. All SQLite/replay/JNI work runs on IO workers. Generation runs
outside the canonical lock and SQLite transaction. A lost commit acknowledgement
is looked up with its original turn key; **Recover saved progress** retries
uncertain work without allocating a new key. See [app durability](../../docs/native/APP_DURABILITY.md).
Full or Busy storage errors show fixed recovery guidance and retain the original
request. The confirmed snapshot stays visible until recovery obtains an accepted
native outcome; new turns and mode changes stay disabled during uncertainty.
The [storage recovery report](../../docs/native/STORAGE_RECOVERY_VERIFICATION_2026-10-22.md)
distinguishes injected error replies from actual SQLite exhaustion.
The [actual SQLite contention fixture](../../docs/native/SQLITE_CONTENTION_VERIFICATION_2026-10-22.md)
adds a separate-process writer and unmodified Rust Busy recovery checks, without
changing production code or introducing a gameplay SQL interface.
The separate [capacity fixture](../../docs/native/CAPACITY_VERIFICATION_2026-10-22.md)
uses a visibly labelled, test-only app with an immutable SQLite compile-time ceiling
to exercise actual Full replies. Build/audit it explicitly with
`python scripts/android_capacity_probe.py build --offline`; this never installs or
runs a device. Its APKs live under `app/build-capacity`, with application ID
`org.locallore.app.capacity`, separate from ordinary saves and instrumentation.
The helper supplies a separate `.gradle-capacity` project cache: distinct task
histories are required as well as distinct output directories, or Gradle can
delete the previous mode's APKs as stale outputs. Property-only direct capacity
builds are rejected. Only debug exists in capacity mode. Ordinary `scripts/check.py android` remains
uncapped. Unset ambient `LIBSQLITE3_FLAGS` for either build; the reviewed native
build owns that option. This immutable fixture cannot prove recovery after freeing
capacity or partition-level exhaustion.
The [capacity lifecycle follow-up](../../docs/native/CAPACITY_LIFECYCLE_VERIFICATION_2026-10-22.md)
separates native-only proofs from the single Compose case and adds an explicit
ordered cohort with Activity-only controls. Default capacity discovery runs the
original three proofs once; the historical UI-class selector now runs only its
one UI method. The report explains nested-suite selection and remote-shell quoting.
The distinct [capacity-relief fixture](../../docs/native/CAPACITY_RELIEF_VERIFICATION_2026-10-22.md)
uses `python scripts/android_capacity_relief_probe.py build --offline`, application
ID `org.locallore.app.capacityrelief`, `app/build-capacity-relief` and the helper's
mandatory `.gradle-capacity-relief` cache. It is debug/testOnly, with a fixed
32-page native ceiling and separate test sources. Its one-shot helper fills then
drops only a verified owned padding table in a fresh synthetic workspace. Padding
temporarily violates the exact schema contract; it is removed before any new
Android native owner opens. Production schema checks stay unchanged. This probes
same-live-owner commit recovery after freeing pages, not ordinary valid-schema
restart under Full or partition ENOSPC. The ordinary, 15-page and relief modes
are mutually exclusive and keep independent task histories and APKs.
Cancellation that reaches Rust before submit exists is reconciled as an uncommitted
request. A late submit remains a draft; recovery does not regenerate or commit it.
The earlier [ADR-0004](../../docs/adr/0004-android-engine-boundary.md) remains the
legacy in-memory boundary fixture; production now uses the shared Host-v1 adapter.

Disposal is terminal: retained Reset callbacks cannot reopen native sessions.
The [ownership follow-up](../../docs/native/OWNERSHIP_FOLLOWUP_2026-10-22.md)
records the regression and additional lifecycle/worker replacement checks.
The [current durable-transport verification](../../docs/native/APP_DEVICE_VERIFICATION_2026-10-22.md)
adds actual production IO/async-close ownership checks. The explicit
[process-restart runner](../../docs/native/APP_DEVICE_RUNNER.md) runs two test-only
phases around a verified app stop, retaining existing saves. These phases skip
ordinary discovery without their coordination argument; do not count skips as passes.

The recorded adapter/samples live only in src/test. The legacy NativeDemoGateway
and Registry remain boundary-test fixtures; MainActivity selects DurableGateway
and NativeWorkspaceTransport. Their host drift check remains:

```powershell
cargo run --locked --offline -p locallore --example android_fixtures -- --check
```

The exporter regenerates apps/android/app/src/test/lantern_quay_cases.json;
preserve UTF-8/LF without BOM after intentional changes.

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

## Browse the player story record

Open **Story record** from an idle saved story to inspect **Progression**, **History**,
**Relationships**, or **Knowledge**. Each read uses the Rust engine's player lens at
the selected story's accepted revision. Search is literal, limited to visible rows;
pages contain at most eight records. Seed/event references explain recorded values.
Statements, beliefs, discoveries, narration, and known world facts retain separate labels.

Browsing never submits a turn, invokes inference, advances time, or changes accepted
history. Closing, leaving the foreground, starting a turn, switching stories, recovery,
and disposal revoke pending publication. An unavailable or stale read displays a fixed
error; it cannot repair saves or promote a summary into canonical state. Native reads
already executing may finish on their IO worker after dismissal; their results are discarded.

Use **Open event #N** on a visible record to read its eligible accepted event at the
same story/head. Event story time and the frozen accepted head have separate labels.
**Back to records** or platform Back restores the same section, search and page;
**Close** dismisses the whole record. Seed and withheld sources have no event link.
Opening the source of a statement or belief shows its recorded origin, without
establishing its proposition as a world fact. No NPC/omniscient controls are offered.

Unsupported engine fields remain explicitly limited. See
[record verification](../../docs/native/ANDROID_RECORD_VERIFICATION_2026-10-23.md)
and [event navigation verification](../../docs/native/ANDROID_EVENT_VERIFICATION_2026-10-23.md)
for exact checks and the remaining milestone gates.

## Verification and limits

Host tests cover strict bytes, scoped IDs, ownership, idempotency, provider
failures, cancellation/commit races and cleanup. JVM tests cover publication,
cancellation/disposal and uncertain outcomes. JNI instrumentation exercises
actual events/resources, invalid arrays and repeated cancellation/disposal;
Compose tests cover flows, reset/recreation/disposal and doubled-font layout.
Exact evidence is in [native verification](../../docs/native/VERIFICATION_2026-10-22.md).

Shared durability is wired to the app; the reports above record explicit
process-stop/resume checks on two selected API 35 x86_64 emulators. Physical
phones, ARM64 execution and M01 model feasibility remain separate unmeasured gates.
Local build checks do not establish hosted CI execution or release readiness.
