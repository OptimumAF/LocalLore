# Shared application storage verification — 2026-10-22

Scope: M04.03/.04/.05/.06 application adapter integration and D03.01/.02 plus
the durability portion of D03.07. Based on accepted main `414f02d` (including
the existing storage/durability and desktop shell PRs). This record does not
grant task acceptance, merge or milestone closure.

The final shared recovery implementation is `7bf5b7e`; its transient-read
regression is integrated as `a5ef78d`. Android rules/details are `aa7d6d3`,
native registry opening is `ec017cc`, and desktop lifetime fencing is `99d9759`.
Documentation-only followups do not alter those inputs.

## Shared and Android results

On Windows, Rust 1.93.1, Java 17.0.6, Gradle 8.11.1, AGP 8.10.1, Kotlin 2.2.21,
SDK 36 / build tools 35.0.0 and NDK 29.0.14206865:

- `python scripts/check.py host --offline`: PASS. Formatting, strict workspace
  Clippy, **122 workspace Rust tests**, four Rust/Android fixture cases,
  **63 Python tests** and **three native-linker tests** pass. The new workspace
  crate contributes 3 integration and 15 adversarial ownership tests.
- `python scripts/check.py android --offline --clean`: PASS for app/test APKs,
  both native ABIs, **38 JVM tests** and lint. After the final shared transient-read
  fix, `python scripts/check.py android --offline` rebuilt both native ABIs and
  the app, repeated the same checks, and passed. Final lint: **0 errors,
  1 existing Gradle dependency advisory**.
- Final APK audit passes: no unexpected network/backup capabilities, expected
  native libraries for `x86_64` and `arm64-v8a`, and 16 KiB ELF load alignment.
- Android `DurableShellTest` contributes seven JVM cases. Five new actual JNI
  instrumentation cases compile into the test APK; **connected instrumentation
  was not run**. Native registry/Host tests execute real synthetic SQLite on
  the Windows host; they do not establish Android device execution.

Android uses an isolated `GRADLE_USER_HOME` under this checkout's ignored
`target/` directory. Only wrapper/dependency cache files were copied from the
existing cache; no shared daemon was stopped. SDK auto-download remained disabled.
There were no ADB commands, emulator operations, model operations or desktop
input/capture commands. Dedicated checkouts and target directories preserve
the concurrently active runtime-control chat's working files and resources.

Final local APK SHA-256 (artifacts remain ignored; no upload):

| Artifact | SHA-256 |
|---|---|
| `app-debug.apk` | `0a303e5f768979506550c35fbe80c7cf13dc35b8c064d707ea047acdcfc90b7b` |
| `app-debug-androidTest.apk` | `5d8dffe753a6e4f3edd13fc98279ac0d2807bd2ced530a1a1a9f8a7cf410fc2e` |

## Source identity

| Input | SHA-256 |
|---|---|
| `crates/locallore/src/host.rs` | `57796d6c8bfec5ad290e5368d95bc94961393025cc6c328745da95057f6c1e0d` |
| `crates/locallore-storage/src/catalog.rs` | `ef893b10589569527bee213a8197173397ecb696a85a34fffcead40529f13cfc` |
| `crates/locallore-workspace/src/lib.rs` | `2c8e0d8a36943ce70d1f8d5d6924930536941b00a36b78be7cf6a28999ec2928` |
| `crates/locallore-android/src/workspace.rs` | `829f7f3440029f22e710a06c3dd5bb87757c01ae3029734c4a79acb003c0f99d` |
| `apps/android/native-build.gradle.kts` | `5e7652e8c27fb04ccb7b2ca2bb259d69259b6fa8cd5100c516f286603c14d035` |

## Limits

This is a bounded root-branch fixture app with explicitly fake inference. It
does not implement cross-device synchronization, real models, last-used story
preferences, saved unsent composer text, automatic orphan adoption, fork/import,
readable inspection exports or storage reveal. Database/commit fault injection
is finite boundary evidence, not an OS power-loss or physical-device claim.
No releases, repository settings or milestone checkboxes were changed.

See [integration behavior](APP_INTEGRATION.md), [independent review](APP_INTEGRATION_REVIEW.md),
[Android details](../native/APP_DURABILITY.md) and [desktop details](../desktop/APP_DURABILITY.md).
