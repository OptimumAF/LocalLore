# Local checks

The standard-library Python runner finds the checkout from its own file, so these
commands work from any directory when given an absolute script path. Python 3.9+
and the existing pinned tools must already be installed. The runner does not
install SDKs, accept licenses, download model weights, start emulators, change
machine settings, or modify environment variables.

```powershell
python scripts/check.py host --offline
python scripts/check.py android --offline --clean
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
coordinator-owned debug APK packaging/manifest audit (`scripts/audit_apk.py`).
It does not install APKs or run device tests. `--clean` cleans Android outputs
before these checks and is rejected for `host`. Android checks require Java 17,
SDK platform 36, Build Tools 35.0.0, NDK 29.0.14206865 and the Rust 1.93.1
`x86_64-linux-android` and `aarch64-linux-android` targets. `JAVA_HOME` selects an
existing JDK; otherwise `java` must be on `PATH`.
The APK audit requires `ANDROID_HOME` or `ANDROID_SDK_ROOT` pointing to the SDK
with Build Tools 35.0.0, even when standalone Gradle uses `local.properties`.

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
