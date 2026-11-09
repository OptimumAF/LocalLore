# Current Windows and Android archive fixture preparation

The [historical report](PLATFORM_ROUNDTRIP_RESULTS_2026-10-23.json) records the earlier archive-v1 transfers. Its Android APK fixtures remain frozen at source database schema 2. The current Windows fixture generator writes archive v1 with the active Store schema, currently 5.

For an owned physical D: checkout with the pinned tools already provisioned, build the Windows fixture executable and generate fresh expected fixtures.

```powershell
$env:TEMP = 'D:/Dev/_Temp'
$env:TMP = $env:TEMP
$target = 'D:/LocalLore proof/target'
$fixtures = 'D:/LocalLore proof/current-fixtures'
$check = 'D:/LocalLore proof/fixture-check'
cargo +1.93.1 build -p locallore-android --example platform_roundtrip --locked --offline --target-dir $target
$fixtureExe = Join-Path $target 'debug/examples/platform_roundtrip.exe'
& $fixtureExe --development-fixtures generate --directory $fixtures
& $fixtureExe --development-fixtures check-fixtures --directory $check --inputs apps/android/app/src/androidTest/assets/platform-roundtrip-v1 --fixtures $fixtures
```

Use the fresh generated directory for `scripts/platform_roundtrip.py --fixtures`. The runner separately verifies the test APK against the tracked historical assets. It runs the same bounded Rust fixture check before APK badging or device commands. Both archives must validate as archive v1. Only the source schema and its dependent payload digest may differ. The complete generated archive bytes must match the normalized compatibility record, and the expected snapshots must match byte for byte. Android's returned Windows archives still have to match the fresh current fixtures exactly.

The isolated Android app and test APKs are produced by `python scripts/check.py android --archive-verification --offline` with the provisioned Android build environment. Build and fixture preflight evidence are separate from actual transfer. A current run still requires an exact isolated APK pair and a separately admitted target under the [shared guest storage procedure](../runtime/android/RECEIPT_AVD_STORAGE.md). The fixture preflight issues no device command.
