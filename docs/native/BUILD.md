# Building the Rust Android boundary

Scope: [M03.03 / #7](https://github.com/OptimumAF/LocalLore/issues/7).
The native library contains the actual Rust engine and deterministic fake
inference provider. It supplies no model weights, inference backend, saved-story
database, network transport, or physical-device qualification.

The application applies `apps/android/native-build.gradle.kts` after its Android
application plugin. `preBuild` depends on `buildRustAndroid`; regular APK and
instrumentation builds therefore compile and package the engine automatically.
The parent application DSL sets NDK `29.0.14206865`, minimum API 26, main
`jniLibs.srcDir(layout.buildDirectory.dir("generated/rustJniLibs"))`, and ABI
filters `x86_64` / `arm64-v8a` to match the script. Keeping the external task script
free of AGP classes avoids classloader coupling and another plugin dependency.

## Provision once

Retain the shell's pinned JDK 17, AGP 8.10.1, Gradle 8.11.1, Android platform 36,
and Build Tools 35.0.0. Set `JAVA_HOME` and either `ANDROID_HOME` or an ignored
`apps/android/local.properties` `sdk.dir` for your machine. Install NDK
`29.0.14206865` with Android Studio's SDK Manager. Do not accept new SDK terms on
someone else's behalf, commit license-acceptance files, or copy SDK binaries into
the repository. The build reports a missing NDK instead of installing one.

From the repository root, using the Rustup-managed Cargo on `PATH`:

```text
rustup toolchain install 1.93.1 --profile minimal
rustup target add --toolchain 1.93.1 x86_64-linux-android aarch64-linux-android
```

Provision the Cargo/Maven/Gradle dependency caches through an ordinary first
build. This may need network access; no model is downloaded. `Cargo.lock` remains
authoritative and every native Cargo build uses `--locked`. Build-time downloads
are independent of gameplay's fully local operation.

## Build

From `apps/android/`:

```powershell
.\gradlew.bat :app:buildRustAndroid --offline --no-daemon --console=plain
.\gradlew.bat :app:assembleDebug :app:assembleDebugAndroidTest :app:testDebugUnitTest :app:lintDebug --offline --no-daemon --console=plain
.\gradlew.bat :app:connectedDebugAndroidTest --offline --no-daemon --console=plain
```

On Linux/macOS use `./gradlew` with the same arguments. Only run connected tests
against authorized devices/emulators. Gradle `--offline` also adds Cargo
`--offline`; absent cached dependencies fail clearly instead of accessing the
network. `clean` removes generated native output with other app build artifacts.

For each target, the task runs an argument-array process equivalent to:

```text
cargo +1.93.1 build --locked --release --package locallore-android --lib --target <target> --target-dir <app/build/rust-target> [--offline]
```

It sets the target-specific Cargo linker to the pinned NDK's real Clang executable
(`clang.exe` on Windows), and passes `--target=<target>26`, its sysroot, and
`-Wl,-z,max-page-size=16384` as individual linker arguments. The encoded Rust flag
environment uses ASCII unit separators, so spaces in SDK/repository paths do not
split arguments. No shell, generated command string, Cargo-NDK plugin or CMake
wrapper is involved. Cargo's stdout/stderr are merged and drained into Gradle's
lifecycle log while it runs; inheriting the Gradle daemon's native console can
stall on Windows. The task closes stdin and releases child streams, terminating
the child on interruption or output failure.

| Rust target | Packaged ABI | Generated library |
|---|---|---|
| `x86_64-linux-android` | `x86_64` | `app/build/generated/rustJniLibs/x86_64/liblocallore_android.so` |
| `aarch64-linux-android` | `arm64-v8a` | `app/build/generated/rustJniLibs/arm64-v8a/liblocallore_android.so` |

Only those generated directories are added to the main `jniLibs` source set by
the parent app DSL.
Native build products and Cargo's target directory remain under ignored
`app/build/`; source control contains no compiled engine. Incremental inputs
include all crate sources/manifests, fixtures, workspace manifest/lockfile,
toolchain file, and native script. The task declares both packaged `.so` outputs
and its NDK/toolchain/minimum-API/target pins.

## Compatibility and licensing sources

Official sources were checked on 2026-10-22 before choosing the native toolchain:

- Android's [NDK revision history](https://developer.android.com/ndk/downloads/revision_history)
  lists stable r29 (October 2025), with r27 identified as an older LTS. The installed
  `source.properties` identifies r29 as `29.0.14206865`; this precise version is
  pinned instead of silently using another installed NDK.
- The [r29 changelog](https://github.com/android/ndk/wiki/Changelog-r29)
  identifies its LLVM revision as `clang-r563880c`.
- Android's [custom build-system guide](https://developer.android.com/ndk/guides/other_build_systems)
  recommends direct Clang plus an API-suffixed target. It documents
  `windows-x86_64`, `linux-x86_64` and `darwin-x86_64` host directories (the macOS
  directory name also covers Apple Silicon). The script implements those paths.
- Android's [16 KB page-size guide](https://developer.android.com/guide/practices/page-sizes)
  says NDK r28+ defaults to 16 KB ELF alignment and AGP 8.5.1+ handles uncompressed
  library packaging. We choose installed r29 rather than r27's 4 KB default, and
  explicitly pass the maximum page-size linker flag through Rust. Validate final
  ELF load segments and APK ZIP alignment; these host checks do not constitute
  execution on a 16 KB device.
- Cargo's [environment-variable reference](https://doc.rust-lang.org/cargo/reference/environment-variables.html)
  documents target-specific linker configuration and unit-separated
  `CARGO_ENCODED_RUSTFLAGS`. The [Rust Android target documentation](https://doc.rust-lang.org/rustc/platform-support/android.html)
  lists both targets and guarantees support for the latest LTS NDK. It does not
  specifically certify this Rust/r29 combination; the actual cross-build and
  emulator checks are required evidence. API 26 matches the shell's provisional
  minimum rather than establishing a production device tier.
- The NDK has component-specific notices in installed `NOTICE` and
  `NOTICE.toolchain`, alongside the [SDK terms](https://developer.android.com/studio/terms).
  LLVM's upstream [license](https://llvm.org/LICENSE.txt)
  describes Apache-2.0 with LLVM exceptions and included third-party material.
  Do not label the entire SDK/NDK as LocalLore's Apache-2.0 source or redistribute
  build tools with the application. Review applicable native dependency notices
  before any release; this build integration is not release clearance.

The existing [Android toolchain decision](../android/TOOLCHAIN_2026-10-22.md)
retains the reasons for the Java/Kotlin/Compose pins. This native build does not
choose a production model/runtime or establish supported device/RAM tiers.

## Evidence boundary

The coordinator's dated native verification report and ticket #7 record actual
build, JNI instrumentation, cancellation/resource ownership and packaging checks.
An ARM64 cross-build is not an ARM64 execution result. A host-compatible script
branch is not evidence that Linux/macOS builds ran. A successful emulator JNI
call does not establish physical-device performance, process-death durability,
real-model cancellation, release readiness, or byte-identical signed APK output.
