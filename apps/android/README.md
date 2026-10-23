# LocalLore Android engine demo

The Compose shell calls the actual Rust engine through a bounded JNI interface.
It uses **fake inference**, original Lantern Quay fixtures and in-memory events.
Kotlin implements no gameplay rules. No real model, saved progress, account or
network dependency during play is present.

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
Only Rust-accepted outcomes enter the transcript. **Demo responses** injects
malformed, rejected, delayed and failing generation. Cancel a delayed turn or
reset while pending. Cancellation before commit leaves canon unchanged;
reset starts fresh. Simulated delay is not a performance measurement.

Accepted state survives Activity recreation through the ViewModel. onStop
cancels pending work; disposal destroys the native session and signals workers.
Process death starts fresh. Preparation runs on Kotlin IO; owner-thread commit
and UI publication never suspend. Unknown commit transport failure requires
reset rather than claiming rollback. [ADR-0004](../../docs/adr/0004-android-engine-boundary.md)
defines this lifecycle and bounded control protocol.

Disposal is terminal: retained Reset callbacks cannot reopen native sessions.
The [ownership follow-up](../../docs/native/OWNERSHIP_FOLLOWUP_2026-10-22.md)
records the regression and additional lifecycle/worker replacement checks.

The former recorded adapter/samples now live only in src/test and are not
packaged or used by the app. Their host drift check remains:

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

## Verification and limits

Host tests cover strict bytes, scoped IDs, ownership, idempotency, provider
failures, cancellation/commit races and cleanup. JVM tests cover publication,
cancellation/disposal and uncertain outcomes. JNI instrumentation exercises
actual events/resources, invalid arrays and repeated cancellation/disposal;
Compose tests cover flows, reset/recreation/disposal and doubled-font layout.
Exact evidence is in [native verification](../../docs/native/VERIFICATION_2026-10-22.md).

M04 durability and M01 physical/model feasibility remain separate work.
Local build checks do not establish hosted CI execution or release readiness.
