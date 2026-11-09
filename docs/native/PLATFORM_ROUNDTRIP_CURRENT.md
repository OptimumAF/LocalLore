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

## Bind the verified APK and fixture inputs before guest admission

The retained archive-verification APK pair and Windows fixture packet from
[#30](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6747415942)
have a host-only preflight. Supply the two existing physical D: evidence roots
from the build and fixture checks.

```powershell
$env:TEMP = 'D:/Dev/_Temp'
$env:TMP = $env:TEMP
python -B -m benchmarks.archive_roundtrip_build --apk-root $apkEvidence --windows-root $windowsEvidence
python -B -m unittest discover -s scripts/tests -p test_archive_roundtrip_build.py
```

The preflight returns the eight exact byte-count and SHA-256 bindings. It checks
the exact bytes of the previously audited APKs and custody receipt, the Windows
fixture executable, the three generated fixtures and the successful Rust
compatibility receipt. It refuses missing or linked inputs, changes during
the check, and any owner binding outside the fixed roster. The output contains local
paths and belongs in local evidence. The build source in this record identifies
where the APKs were built. A later owner must revalidate the artifact roster
and live bytes, and must establish its own source, lease and shared-ledger
admission. This command performs no SDK, device, or archive-transfer operation.

## Verify the owned archive profile on the host

The model-free SDK25 profile reuses the existing owned-target worker, shared
guest ledger, bounded shell-v2 client, and retained capture verifier. It binds
the exact eight artifacts above during admission and rechecks their bytes
before the live lease or worker opens its shared process resources, and
again when verifying the retained guest proof. The fixed target scope is
API 35, x86_64 and Android user 0.

The first phase uses a run ID derived from the admission. Its two isolated
APKs use exclusive staging paths and no-replace installation. The outbound
instrumentation consumes one durable claim. Private reads accept only that
run's owner marker and three outbound files, with a combined 128 KiB capture
limit in both live and retained verification.

```powershell
python -B -m unittest discover -s scripts/tests -p test_owned_archive_roundtrip_profile.py
```

These host checks exercise admission, command policy, one-shot claim and
live/replay wiring with synthetic inputs. The worker entry requires the
shared parent barrier. The operator launcher and return phase are still
pending, including ordered package identity checks, verified Windows
continuation, the single return write, final Rust replay and separately
approved guest admission.

## Check the ordered outbound transfer evidence

The outbound controller checks boot readiness, the fixed target and Android
user, and absence of both isolated packages before writing either APK. It
checks the staged hashes, installs without replacing, and records package
UIDs, paths and APK hashes before and after the single outbound test. The
test must pass and emit the exact owner marker. Both returned Windows
archives must match the admitted sizes and SHA-256 digests.

Host verification uses a synthetic 31-command capture with two boot reads.
The live adapter allows at most 60 boot reads, gives each read at most the
remaining time in the 120-second boot window, and refuses late readiness.
Replay checks the command count, individual command deadlines, and the
same ordered setup and transfer evidence. SDK25 caps raw captures at 128 KiB.
Setup commands request 4 KiB and a retained setup record exceeding that
size is refused.

```powershell
python -B -m unittest discover -s scripts/tests -p test_archive_roundtrip_outbound.py
```

The result carries the exact session, contiguous record pins, and verified
archive bytes. A return controller must match those frozen pins when replaying
the prefix, run the pinned Rust continuation, and verify the exclusive return
write before dispatch. These host tests use no SDK, emulator, or device.

## Verify the Windows continuation receipt

The continuation replays the exact outbound record prefix and compares its
session, ordered record pins and bytes before creating the fixed attempt
directory. It materializes only the three verified outbound archives. The
retained Rust executable runs with its owned-stdin barrier and fixed
`verify` arguments, a 120-second deadline and 4 KiB combined process
capture. Its executable and fixture bytes are checked before and after the
child under exclusive artifact custody.

The receipt is create-only. It binds the request, owned process terminal and
the complete native output roster. Each retained SQLite file must be at
most 1 MiB when inspected after the child closes. This check measures
retained files after execution. Closed verification replays the prefix,
rechecks the exact materialized input and output bytes, and returns only
the two archive pins for the next phase.

```powershell
python -B -m unittest discover -s scripts/tests -p test_archive_roundtrip_bridge.py
```

The actual Windows CLI smoke used the retained Rust test executable to
generate a synthetic Android-origin archive. The Android capture records
were simulated. The exclusive write back to Android, final transfer replay,
and real guest admission are separate steps.
