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

The timeline catalog journey uses an isolated debug identity so existing saves
remain in their installed app. From `apps/android`, build with:

```powershell
.\gradlew.bat :app:assembleDebug :app:assembleDebugAndroidTest :app:testDebugUnitTest :app:lintDebug -PlocalLoreTimelineVerification=true --project-cache-dir .gradle-timeline -Pkotlin.incremental=false --offline --no-daemon
```

This selects `org.locallore.app.timelineverify`, `app/build-timeline`, and its
exclusive project cache. The profile rejects release and combined verification
modes. Install its two APKs only on authorized targets, then select
`TimelineNativeTest`, `TimelineProtocolTest`, `TimelineActivityTest` and
`TimelineMainActivityTest` with AndroidJUnitRunner. They use synthetic data;
the Activity tests require this isolated package. Ordinary builds keep their
usual identity/output directory.

Parent-retirement verification has its own debug identity and project cache:

```powershell
.\gradlew.bat :app:assembleDebug :app:assembleDebugAndroidTest :app:testDebugUnitTest :app:lintDebug -PlocalLoreParentRetentionVerification=true --project-cache-dir .gradle-parent-retention -Pkotlin.incremental=false --offline --no-daemon
```

It selects `org.locallore.app.parentverify` and `app/build-parent-retention`.
Release, mixed capacity/verification modes and mismatched caches are refused.
`ParentRetentionNativeTest`, `ParentRetentionProtocolTest` and
`ParentRetentionActivityTest` exercise actual JNI worker isolation, strict wire
metadata and the Compose retention/archive-v2 journey with synthetic data.
Install only this app/test pair on explicitly authorized targets. Existing
product and benchmark caches remain in their separate installed applications.

No platform Internet, media, contact or location permission is requested.
AndroidX adds an app-owned signature receiver permission. Backup exclusions
are configured; these tests do not qualify OS backup behavior. Existing Gradle,
AGP, Kotlin/Compose pins and locks remain explicit. See the [Android toolchain](../../docs/android/TOOLCHAIN_2026-10-22.md)
and [JNI source/license inventory](../../docs/native/SOURCES_2026-10-22.md).

## Optional external inference owner

`NativeWorkspaceTransport(context, localInference = owner)` attaches a trusted
`LocalInferenceOwner` to the same production Rust workspace lease used by saves,
forks and deletion. The owner accepts a bounded profile and a `LocalRoleWorker`;
ordinary app construction still explicitly uses scripted inference. There is no
production SDK adapter or model-loading UI in this packet.

Build the isolated synthetic JNI qualification pair from `apps/android`:

```powershell
.\gradlew.bat :app:assembleDebug :app:assembleDebugAndroidTest :app:cleanTestDebugUnitTest :app:testDebugUnitTest :app:lintDebug -PlocalLoreExternalInferenceVerification=true --project-cache-dir .gradle-external-inference -Pkotlin.incremental=false --offline --no-daemon --max-workers=2 -Pandroid.builder.sdkDownload=false
```

This selects `org.locallore.app.externalverify` and `app/build-external-inference`.
Release, mixed verification/capacity modes and another project cache are refused.
`ExternalInferenceInstrumentedTest` exercises actual JNI/Host/SQLite with synthetic
role results, including cancellation, deletion, restart, admission limits and
uncertain-resource quarantine. Install only this pair on an authorized target
that passes storage, identity and existing-data preservation checks.

See the [owner contract](../../docs/native/EXTERNAL_INFERENCE_OWNER_CONTRACT.md)
and [verification report](../../docs/native/EXTERNAL_INFERENCE_OWNER_VERIFICATION_2026-10-23.md).
These checks do not establish physical-device support or actual SDK/model cleanup.

## Concrete LiteRT worker candidate

The additional `-PlocalLoreModelSetupVerification=true` flag enables the local
file setup and real-worker construction candidate in a separate
`org.locallore.app.modelverify` package. Add it to the command below; retain all
existing SDK/analyzer/cache/toolchain flags. This profile requests a local file,
verifies the built-in artifact's full size/hash, and opens the existing story
shell with the paired local owner. It bundles no weights and adds no download
or network capability. Its sole launcher is setup; scripted MainActivity and
the local play Activity are not exported. One runtime attachment is permitted
per process; another requires a complete process restart. File verification is
not evidence of successful model load or supported phone performance.
Audit its APK with `scripts/audit_apk.py <apk> --litert-verification --model-provisioning`.
See the [provisioning contract](../../docs/native/MODEL_PROVISIONING_CONTRACT.md)
for cancellation, interrupted-copy recovery and API/filesystem limits, and the
[verification](../../docs/native/MODEL_PROVISIONING_VERIFICATION_2026-10-23.md)
for the passing synthetic checks on one API 35 x86_64 emulator. Real inference
through this setup profile remains unqualified.

The separate `-PlocalLoreModelVolumeVerification=true` flag requires the LiteRT
and model-setup flags and refuses picker mixing. It builds
`org.locallore.app.modelvolumeverify` in `build-model-volume`. On API 30+, this
explicit experiment selects exactly one suitable Context-owned removable-files
volume and refuses identity/capacity changes without fallback. Model/cache data
on removable media has different confidentiality and availability limits;
canonical saves stay internal. See the [storage contract](../../docs/native/MODEL_VOLUME_CONTRACT.md)
and proposed [ADR-0010](../../docs/adr/0010-candidate-volume-storage.md).
Audit with `scripts/audit_apk.py <apk> --litert-verification --model-provisioning --model-volume-verification`.
The [current verification](../../docs/native/MODEL_VOLUME_VERIFICATION_2026-10-23.md)
passes host/build checks but fails native publication on the selected emulator;
positive removable-filesystem compatibility remains blocked.
Real-model copies and SDK execution require their own admission; the flag does
not discharge existing device/runtime holds.

The additional `-PlocalLoreModelPickerVerification=true` flag requires both
candidate flags above and selects the separate `.modelpickerverify` debug
fixture. It inherits the real picker/resolver/setup flow with 63 original
synthetic bytes; its private fixture Activity always refuses inference. The
normal launcher still uses the fixed real candidate identity. Its conditional
TEST APK supplies a platform-protected DocumentsUI provider with observable
descriptor release. The source is excluded from ordinary and regular candidate
APKs. Outputs go to `app/build-model-picker`; audit that app with
`scripts/audit_apk.py <apk> --litert-verification --model-provisioning --model-picker-fixture`.
The preparation and process-readback methods must run in separate processes;
running the entire test class together intentionally fails readback. See the
[picker contract](../../docs/native/MODEL_PICKER_CONTRACT.md) and dated
[verification](../../docs/native/MODEL_PICKER_VERIFICATION_2026-10-23.md) for
exact selection, admission and qualification limits. The first phase requires
an absent synthetic root and performs no reset.

The explicit synthetic model-picker profile also has a separate
[interrupted-import contract](../../docs/native/MODEL_INTERRUPTION_CONTRACT.md).
Its two `ModelPickerInterruptionTest` methods must be selected individually in
separate processes: the arm intentionally kills its own target process and can
never count as PASS; recovery must pass normally. Run only after a fresh
source/APK-bound device admission, preserving the older fixture data. Do not
select this class through a broad connected suite. The new partial document
requires API 30; ordinary builds and production minimum SDK are unchanged.
The [dated interruption evidence](../../docs/native/MODEL_INTERRUPTION_VERIFICATION_2026-10-23.md)
records a real partial-read process interruption and separate recovery PASS on
one API-35 x86_64 emulator. It does not establish pending-picker callback
restoration, real inference or physical-phone support.

The optional [LiteRT worker](../../docs/native/LITERT_WORKER_CONTRACT.md) implements
`LocalRoleWorker` against the actual SDK. Its trusted configuration factory pairs
the native provenance/profile and worker. With only the LiteRT verification flag,
MainActivity continues constructing the scripted provider. The additional model
setup flag above selects the separate file-import launcher and paired owner.

With the already provisioned Java 21 installation configured for Gradle toolchain
discovery, keep Java 17 as the build daemon and run from `apps/android`:

```powershell
.\gradlew.bat :app:assembleDebug :app:assembleDebugAndroidTest :app:cleanTestDebugUnitTest :app:testDebugUnitTest :app:lintDebug :app:auditLiteRtDependencies :app:auditLintAnalyzer -PlocalLoreLiteRtVerification=true --project-cache-dir .gradle-litert-worker -Pandroid.experimental.lint.version=9.4.1 -Porg.gradle.java.installations.auto-download=false -Pandroid.builder.sdkDownload=false -Pkotlin.incremental=false --offline --no-daemon --max-workers=2
```

The profile selects `org.locallore.app.litertverify`, `app/build-litert-worker`,
`app/gradle-litert.lockfile` and source directories `litert`, `litertTest` and
`litertAndroidTest`. Ordinary builds exclude them and retain their original graph.
First-time dependency provisioning may use the declared public repositories;
no model or Java/Android toolchain is downloaded by this command. After changing
packaging inputs, clean the two package outputs before assembling to avoid
incremental APK gaps: `:app:cleanPackageDebug :app:cleanPackageDebugAndroidTest`.

From the repository root, with the SDK environment configured:

```powershell
python scripts/audit_apk.py apps/android/app/build-litert-worker/outputs/apk/debug/app-debug.apk --litert-verification
```

`LiteRtWorkerInstrumentedTest` covers packaged SDK library linkage and synthetic
file admission through the actual workspace owner. It does not initialize a
model or render Compose. Install only on a separately admitted target; current
model/cache holds still apply. See the [dated verification](../../docs/native/LITERT_WORKER_VERIFICATION_2026-10-23.md).

## Exercise the engine

Give the potion to Mira, then try giving it again and using the unlearned ability.
Only finalized shared-engine receipts enter the transcript. **Demo responses**
injects malformed, rejected, delayed and failing generation. **New story** creates
a new independent saved story and retains earlier stories in **Saved stories**.
Cancel reconciles against accepted history: a commit that already won remains
visible. Simulated delay is not a performance measurement.

Accepted state survives Activity recreation and native/process owner recreation.
Startup resumes a default saved story; use **Saved stories** to select another.
Use **Timelines** to resume an existing root, child or sibling in that story.
**New timeline…** reviews a completed accepted boundary and a fixed child
identity before explicit confirmation. It preserves the original and its later
choices. A small private recovery hint is saved before native admission;
**Recover timeline request…** only looks for that exact existing child after
restart. Creating/retrying and opening a confirmed child are explicit actions.
Cancellation never promises that an earlier commit was undone. Author
corrections remain unavailable. The current host/build checks cover controller
and native Rust behavior; Android JNI/framework/Compose, process-death and
filesystem runtime qualification remain pending. See the
[fork qualification report](../../docs/native/M08_ANDROID_FORK_APP_QUALIFICATION_2026-10-23.md).
Inherited accepted receipts retain their original ancestor scopes; Rust filters
history at fork boundaries. The selector does not create branches. Whole-story
deletion from a child still previews and confirms every timeline using the root
head. **Delete timeline** separately retires a selected nonroot timeline after
previewing retained descendants and removed data. Required original ancestry
remains readable only for retained children; retired IDs cannot be reused. See
the [retention contract](../../docs/native/PARENT_RETENTION_CONTRACT.md) and
[catalog contract](../../docs/native/TIMELINE_CATALOG_CONTRACT.md).
The displayed path is the actual database in app-private `noBackupFilesDir`,
with workspace contract version 1 and database schema version 3. Uncommitted responses remain separate from canon;
resuming does not regenerate or automatically apply them. Closing the app does
not delete saves. All SQLite/replay/JNI work runs on IO workers. Generation runs
outside the canonical lock and SQLite transaction. A lost commit acknowledgement
is looked up with its original turn key; **Recover saved progress** retries
uncertain work without allocating a new key. See [app durability](../../docs/native/APP_DURABILITY.md).

Cancellation also retains its original key until a matching terminal reply is
validated. A malformed or unfinished acknowledgement requires recovery before
another turn or story switch. A commit that won the race remains saved. See
[cancellation acknowledgement verification](../../docs/native/ANDROID_CANCEL_ACK_VERIFICATION_2026-10-23.md)
for the isolated protocol tests and their device limits.
The cancellation diagnostic reports completion only after the acknowledgement
and saved-history reconciliation succeed. An uncertain reply records an unknown
outcome and keeps recovery guidance visible; a commit that won the race is not
described as stopped. See the [presentation regression](../../docs/native/ANDROID_CANCEL_PRESENTATION_VERIFICATION_2026-10-23.md).
While cancellation is being reconciled, the screen shows **Checking cancellation…**.
If recovery is required, **New story** and **Saved stories** remain disabled along
with new turns until **Recover saved progress** succeeds. The in-memory demo
retains its separate Reset behavior. See the [Compose controls checks](../../docs/native/ANDROID_CANCEL_CONTROLS_VERIFICATION_2026-10-23.md).
The [native Compose checks](../../docs/native/ANDROID_NATIVE_CANCEL_CONTROLS_VERIFICATION_2026-10-23.md)
exercise the production transport, JNI, Rust and SQLite with fake inference.
Six cases passed on emulator B, including exact-key recovery, commit-before-cancel,
persisted player-history equality after reopen and availability of all four native
owner slots after calls drain. They hold ready reply delivery; active model
generation and OS process-death recovery remain separate gates. Emulator A's
storage gate remains blocked.
The [native free-text recovery checks](../../docs/native/ANDROID_NATIVE_TEXT_RECOVERY_VERIFICATION_2026-10-23.md)
exercise Action and Dialogue entered in the composer, original play-v2 receipts,
uncertain committed outcomes and recovery with the original request key.
Literal dialogue claims remain statements; the tested claim grants no ability
or inventory change. This coverage uses the same explicitly scripted provider.
Full or Busy storage errors show fixed recovery guidance and retain the original
request. The confirmed snapshot stays visible until recovery obtains an accepted
native outcome; new turns and mode changes stay disabled during uncertainty.
The [storage recovery report](../../docs/native/STORAGE_RECOVERY_VERIFICATION_2026-10-22.md)
distinguishes injected error replies from actual SQLite exhaustion.
The [actual SQLite contention fixture](../../docs/native/SQLITE_CONTENTION_VERIFICATION_2026-10-22.md)
adds a separate-process writer and unmodified Rust Busy recovery checks, without
changing production code or introducing a gameplay SQL interface.
The separate [current schema4 capacity profile](../../docs/native/SCHEMA4_CAPACITY_VERIFICATION_2026-10-23.md)
uses visibly labelled test-only apps with fixed SQLite compile-time ceilings.
Build/audit the Full fixture explicitly with
`python scripts/android_capacity_probe.py build --offline`; this command never
installs or runs a device. The current profile is SQLite schema4, fixture format3,
with v4 package/cache identities. Host/helper JSON wire version2 and the padding
owner marker formatv2 retain their existing shapes.

The current Full profile is23 pages: the unchanged Windows Host measured Ready23
and gift24; a23-page build reached Ready and returned repeated actual Full while
preserving the original key and canonical snapshot.17 failed at workspace open;
22 failed at story creation. The current Android APK output is
`app/build-capacity-v4`, application ID `org.locallore.app.capacityv4`, with the
helper's required `.gradle-capacity-v4` project cache. Task histories and outputs
must both be separate. Historical unversioned/v3 capacity caches are rejected,
and all modes are debug/testOnly and mutually exclusive. Ordinary
`scripts/check.py android` remains uncapped. Unset ambient `LIBSQLITE3_FLAGS`;
the reviewed native build owns the option. Host measurements do not qualify an
Android rebuild, device execution or partition-level exhaustion.

Historical [15-page evidence](../../docs/native/CAPACITY_VERIFICATION_2026-10-22.md),
[schema3 Host calibration](../../docs/native/SCHEMA3_CAPACITY_HOST_2026-10-23.md)
and [schema3 Android qualification](../../docs/native/SCHEMA3_CAPACITY_VERIFICATION_2026-10-23.md)
remain dated and unchanged. Their v3/17-page device results are not results for
this schema4/v4 source. The [capacity lifecycle follow-up](../../docs/native/CAPACITY_LIFECYCLE_VERIFICATION_2026-10-22.md)
explains the original native/Compose selector split: default discovery runs the
three original proofs once; the historical UI-class selector runs its one UI
method. No device control is performed by the build/audit commands above.

The distinct relief fixture uses
`python scripts/android_capacity_relief_probe.py build --offline`, application ID
`org.locallore.app.capacityreliefv4`, `app/build-capacity-relief-v4` and mandatory
`.gradle-capacity-relief-v4` cache. The fixed ceiling remains32 and padding payload
remains3500 zero bytes. The measured Windows Host/helper schema4 baseline is23
pages:8 fixed padding rows fill32; attempt9 returns actual Full; dropping only the
verified owned table frees9 pages and restores the exact schema. The current
reference includes all four migration contracts and schema SHA-256
`e9f19f3b384c52c5c7bd360e23c1db9e76314152f750a5b9f07f7a14071f8362`.

Schema/migration, marker and file identities are checked read-only before
writable helper admission and rechecked around mutations. Unknown helper
ownership fences subsequent native calls. Padding temporarily violates the exact
schema contract and is removed before a new Android native owner opens. Normal
production schema checks remain unchanged. Actual Windows Host tests preserve the
same Ready key through repeated Full, then commit once after relief or preserve
cancellation through relief/reopen. This is same-live-owner recovery after
freeing pages; it is not ordinary valid-schema restart under Full or partition
ENOSPC. The initial old14/15 expectation failed and cleaned up successfully;
that [measurement](../../docs/native/SCHEMA4_CAPACITY_CALIBRATION_2026-10-23.md)
is retained. Historical [schema1 relief evidence](../../docs/native/CAPACITY_RELIEF_VERIFICATION_2026-10-22.md)
and schema3 device results remain separate.

The opt-in [helper-failure boundary](../../docs/native/HELPER_FAILURE_CONTRACT.md)
has the separate `org.locallore.app.capacityfaultsv4` installation. Build/audit it
with `python scripts/android_capacity_fault_probe.py build --offline`; outputs/cache
are `app/build-capacity-faults-v4` and `.gradle-capacity-faults-v4`. Fixed fault
controls require this debug/testOnly identity and exact `faults_format=1`.
The helper requests complete nonincremental Kotlin test-module compilation.
Select each nested `SqliteHelperFaultTest` class in a fresh instrumentation
process: poisoning has no reset API. Default discovery retains the three normal
relief cases. Ordinary/full/relief/fault packages and historical artifacts remain
separate.

The current Windows Host cohort exercised five fixed helper faults with zero
later Host calls/workspace opens; it does not qualify Android process/reader
behavior. The [dated schema3 helper-failure verification](../../docs/native/HELPER_FAILURE_VERIFICATION_2026-10-23.md)
retains its actual device results. Current Android native/APK/device verification
is still required before reusing those claims. For a separately authorized,
verified selected device and installed v4 app/test hashes, the selector shape is:

```powershell
adb -s <authorized-emulator> shell am instrument -w -r -e class 'org.locallore.app.SqliteHelperFaultTest$MarkerDrift' org.locallore.app.capacityfaultsv4.test/androidx.test.runner.AndroidJUnitRunner
```

This documentation update did not execute that command. Run `MarkerDrift`,
`DispatchFence`, `Malformed`, `Oversize`, `Timeout` and `AfterFill` separately;
use the same runner without `-e class` for default discovery. Retain the existing
bounded client/process ownership checks. A timeout or uncertain owner is a failed
check; retain failed synthetic roots instead of clearing app data to reset the
process fence.
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

## Write an Action or Dialogue

The saved-story shell now offers **Write a turn**. It identifies its native provider
as **Scripted fixture · no language model**. Select Action or Dialogue, edit the
original text and press **Send**. **Potion example** only fills the Action draft;
it never sends automatically. The fixture proposes that gift and literal dialogue;
other actions may be rejected by the existing Rust intent guard/mechanical rules.
Dialogue records words as a statement, not world truth. There is no text-to-command
compiler in Kotlin and no cloud fallback.

Input is bounded to 2048 UTF-8 bytes with valid Unicode. Text remains unchanged
across the native request and exact-key recovery. Pending work disables editing;
**Cancel** stops preparation. Drafts remain after rejection or an accepted head
update, and reset on story/branch changes or composition disposal. Accepted prose
and state come from saved engine receipts. Existing typed sample actions and fake
modes remain available as separate regression fixtures.

The potion example, literal dialogue, cancellation, lost acknowledgements,
disposal, saved-story isolation and strict reopen passed on both API 35 x86_64
test emulators. No model is loaded and the real local-backend/physical-phone gate
remains open. Read [dated evidence](../../docs/native/ANDROID_INPUT_VERIFICATION_2026-10-23.md)
and [all attempts](../../docs/native/ANDROID_INPUT_RESULTS_2026-10-23.json).

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

The opt-in model picker profile also includes a non-exported pending-result
fixture. Its [contract](../../docs/native/MODEL_PENDING_CONTRACT.md) requires
actual saved-task restoration after process death, safe rejection of the old
selection, and a later explicit import. Run its two methods separately under
the documented external owner; a broad connected suite or ordinary runner
restart cannot verify that framework relationship. This fixture uses original
synthetic bytes and refuses inference. Dated reports distinguish actual results
from remaining device/model gates. The [pending-result verification](../../docs/native/MODEL_PENDING_VERIFICATION_2026-10-23.md)
records actual restored-result rejection and a later native import on one emulator.

The same explicit profile includes a private [setup recovery fixture](../../docs/native/MODEL_SETUP_RECOVERY_CONTRACT.md).
It exercises injected launch/construction failures through the actual setup
buttons, retained admission across Activity close/reopen, and a separately
verified fresh process. It never starts an SDK or story workspace; its contract
is not a real-model or phone qualification result. Its [dated verification](../../docs/native/MODEL_SETUP_RECOVERY_VERIFICATION_2026-10-23.md)
records both selected synthetic methods passing on one emulator.

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

The [whole-story deletion checks](../../docs/native/STORY_DELETION_VERIFICATION_2026-10-23.md)
use the separate `.storydelete` debug package and exclusive
`.gradle-story-deletion` cache. The real Store preview, explicit consent,
three-timeline removal, retained story, cancellation, and durable empty-library
flows run without deleting existing demo saves. Branch-only deletion is pending;
external copies and forensic erasure remain outside the logical-delete promise.

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
