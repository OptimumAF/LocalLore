# Local checks

The standard-library Python runner finds the checkout from its own file, so these
commands work from any directory when given an absolute script path. Python 3.9+
and the existing pinned tools must already be installed. The runner does not
install SDKs, accept licenses, download model weights, start emulators, change
machine settings, or modify environment variables.

```powershell
python scripts/check.py host --offline
python scripts/check.py android --offline --clean
python scripts/check.py android --archive-verification --offline
```

`host` runs Rust 1.93.1 workspace formatting, warning-free Clippy over all targets,
workspace tests, the Rust-generated Android fixture comparison, benchmark metadata
and calculator Python tests, runner tests, and formatting/compiled tests for the
standalone native linker adapter. Cargo dependency resolution uses `--locked`.
The linker test executable lives in ignored `target/checks/`.

Workspace tests also exercise the [Rust SQLite owner](../storage/README.md):
schema identity/version refusal, atomic initialization, scoped foreign keys,
consistent migration/WAL backups, seed isolation, Busy/retry and fixed errors.
These tests need a C compiler for the locked bundled SQLite source, but no model,
SDK or device. Explicit Android storage cross-build/smoke commands remain separate.

The M01 host spike adds five Rust example tests and stdlib-only process/worker
regressions. These use synthetic fake processes and SDK mocks: default host/CI
checks never install inference packages, build third-party runtimes or load or
download model weights. Real local calls require the separate explicit commands
in [the spike instructions](../runtime/spike/README.md).

The isolated Android experiment adds stdlib-only ownership/envelope and artifact
audits to `host`. They never invoke ADB, build a runtime, load/download a model
or install the SDK harness. Explicit native/SDK builds and emulator commands live
in [Android experiment instructions](../runtime/android/README.md). Its known
SDK lint metadata limitation does not weaken the production Android check gate.

`android` runs debug app and instrumentation APK assembly, JVM tests, lint and the
coordinator-owned product APK audit (`scripts/audit_apk.py`), followed by the
instrumentation pair audit (`scripts/audit_instrumentation_apk.py`). The existing
build and product-audit command prefix is retained; pair verification is now the
third command, and its failure stops the gate.
An actual fresh offline archive-profile execution, including 332 passing JVM
cases, lint and both public audits, is recorded in the
[2026-10-30 public Android gate report](../android/PUBLIC_ANDROID_GATE_VERIFICATION_2026-10-30.md).
The [updated system-theme archive report](../android/SYSTEM_THEME_ARCHIVE_VERIFICATION_2026-10-30.md)
records a later fresh run of the same gate with 337 passing JVM cases and the
current theme resources; device execution remains separate.
The [transcript-navigation archive report](../android/TRANSCRIPT_ARCHIVE_VERIFICATION_2026-10-30.md)
records the subsequent fresh run with 345 passing JVM cases, both public audits
and four compiled, unrun transcript journeys.
It does not install APKs or run device tests. `--clean` cleans Android outputs
before these checks and is rejected for `host`. Android checks require Java 17,
SDK platform 36, Build Tools 35.0.0, NDK 29.0.14206865 and the Rust 1.93.1
`x86_64-linux-android` and `aarch64-linux-android` targets. `JAVA_HOME` selects an
existing JDK; otherwise `java` must be on `PATH`.
The APK audit requires `ANDROID_HOME` or `ANDROID_SDK_ROOT` pointing to the SDK
with Build Tools 35.0.0, even when standalone Gradle uses `local.properties`.

`android --archive-verification` selects the existing isolated archive profile
with `-PlocalLoreArchiveVerification=true`. It builds the app/test APKs, runs
JVM tests/lint, audits the product APK under
`apps/android/app/build-archive-verification/outputs/apk/debug/`, and checks its
instrumentation pair under `outputs/apk/androidTest/debug/`. The ordinary
command still selects `build/` and `org.locallore.app`. The archive option is
rejected for `host` before any checks start. It does not install APKs or execute
instrumented tests.

To audit an already built archive-profile product APK without rebuilding:

```powershell
python scripts/audit_apk.py apps/android/app/build-archive-verification/outputs/apk/debug/app-debug.apk --archive-verification
```

This selects only `org.locallore.app.archiveverify`, including its exact scoped
signature permission and backup-resource namespace. Mixing the archive option
with any model/input verification option is refused before reading the APK or
starting AAPT. Omitting the option retains the ordinary package contract; an
archive APK is not accepted as an ordinary APK. These entry points reuse the
same ZIP, SDK, manifest, backup-rule and receipt-service policies. They accept
no arbitrary package name.

To verify an already built archive-profile app/test pair without rebuilding:

```powershell
python scripts/audit_instrumentation_apk.py apps/android/app/build-archive-verification/outputs/apk/debug/app-debug.apk apps/android/app/build-archive-verification/outputs/apk/androidTest/debug/app-debug-androidTest.apk --archive-verification
```

Omit the archive option for the ordinary `build/` pair. This command verifies
distinct, stable APK bytes; exact packages/SDKs and runner target; the existing
test permission/activity/provider inventory; no shared/aliased or overridden
test-application identity; and one matching verified signer. It reuses the
phone auditor's closed test-manifest policy rather than defining a second
provider policy. Product ZIP validation also runs; full product backup checks
remain in the preceding product audit.

Signature verification uses the installed SDK's `lib/apksigner.jar` through the
existing selected Java executable (`JAVA_HOME` or `java` on PATH). Only
`verify --verbose --print-certs` runs; no private key is read, generated or used
to sign an APK. Matching certificates establish pairing, not a trusted release
publisher. No device or instrumented test is run by this artifact check.

The audit checks the current debug contract: min26/target36, only the app-owned
signature receiver permission, exactly the two supported ABI/library sets,
uncompressed 16 KiB-aligned native ZIP entries, and ELF64 type/machine/bounds/
LOAD alignment. It rejects duplicate APK entries and the former recorded JSON
fixture. Intentional dependency/capability/SDK changes require reviewing this
contract. This is not a general hostile-APK verifier or a device execution test.

Before executing Java, the runner checks the wrapper JAR SHA-256 and the complete
existing wrapper property configuration, including the pinned Gradle 8.11.1
distribution URL/checksum. It invokes the verified JAR directly with an argument
list, avoiding Windows batch command parsing. Pins come from the existing
[Android toolchain evidence](../android/TOOLCHAIN_2026-10-22.md), not from a new
download. A mismatch is a failure; updating these pins requires a reviewed update
against official artifacts. SDK automatic download is explicitly disabled.

`--offline` forwards Cargo and Gradle offline flags. Cached dependencies, the
Gradle distribution and tools are prerequisites; missing artifacts fail. Without
`--offline`, Cargo/Gradle may fetch declared development dependencies and the
checksum-verified Gradle distribution. This development network access is separate
from the app's fully local gameplay contract. Provision tools explicitly using
the existing [Android instructions](../../apps/android/README.md).

Commands run serially with inherited environment and output. The first failed
command stops the suite and returns its exit code. Missing tools/configuration
return 1; invalid CLI arguments return 2; keyboard interruption returns 130.
No passing host or APK build proves emulator execution, physical phone performance,
ARM64 execution, model quality, durable storage, or repository owner acceptance.

The Android crate's `platform_roundtrip` development example is registered with
`test=true`, so the normal host suite checks its real Store/Host fixtures and
engine-to-packaged-asset drift. Platform-specific junction/symlink cases differ
by OS. These host tests do not launch ADB. The explicit
[cross-platform runner](../native/PLATFORM_ROUNDTRIP_VERIFICATION_2026-10-23.md)
requires already installed, hash-matching test APKs and an authorized selected
device; it is not part of default CI and performs no model provisioning.

The explicit [archive recovery runner](../native/ARCHIVE_RECOVERY_VERIFICATION_2026-10-23.md)
also requires matching installed isolated APKs and an authorized selected device.
It deliberately force-stops only that verified app after a live-PID readiness
check, then requires a real passing relaunch test. It is not part of default CI.
Its Python fault tests and three host Store transaction-interruption tests run
in the normal host suite. The latter invoke one explicitly ignored IPC worker;
that entry is not an additional standalone qualification test. No model or
private save is provisioned, and no directory is recursively deleted by them.

The explicit [archive capacity runner](../native/ARCHIVE_CAPACITY_VERIFICATION_2026-10-23.md)
requires preinstalled exact `.archivecapacity` APKs and its exclusive build cache.
It verifies actual SQLite Full and cache-only recovery through the real native
gateways and Compose surface. Its nine Python ownership/evidence fault tests
and three Store regressions run in the host gate. The separate compiled-page
qualifier is explicitly ignored there and must be selected in its documented
isolated Cargo profile. No default CI step provisions a device, fills a partition
or enables the feature-only JNI fixture in an ordinary build.

The explicit [whole-story deletion checks](../native/STORY_DELETION_VERIFICATION_2026-10-23.md)
build `.storydelete` with an exclusive project cache and no test-only native
feature. Eight Store and five public native-owner regressions run in the host
gate; consent/empty-library tests run in the JVM suite. Actual product Activity,
Compose/JNI and Android protocol cases require a separately authorized test
emulator. The first product Activity test requires an initially empty dedicated
library; never substitute or clear a user's installed workspace.
