# Schema3 capacity coordinator integration, 2026-10-23

Refs #8 M04.04 and PR #87. This is the coordinator's actual integration
evidence, separate from the author's historical emulator qualification.
Accepted parent retention #85 is now main `3485aa4a8137e2408d6cbcf067296fd98b108e98`.
Exact #87 head `540dff07e5e09019bd04bcc4ea5ad7dc32cacb1f` was merged normally
with that main at `e1a88a25b50a40552e532ac46cfa24e6649f05a0`.
Independent new CLI tests `49bf2fb` and review `af8551a` were imported unchanged
as `2211ad0` and `889dcf2`. Later differences are this report only.

Claims: [PR claim](https://github.com/OptimumAF/LocalLore/pull/87#issuecomment-6370659280)
and [M04 claim](https://github.com/OptimumAF/LocalLore/issues/8#issuecomment-6370659616).
Owner authorized implementation and tested merges, subsequently explicitly
authorized using existing owner merge privileges. No repository settings,
required checks, reviews or release controls were changed or fabricated.

## Actual coordinator checks

Windows 11 Pro 10.0.26300; Rust/Cargo 1.93.1; isolated Python 3.14.9,
whose SQLite is 3.50.4; JDK 17.0.6, Gradle 8.11.1, AGP 8.10.1,
Kotlin 2.2.21, SDK 36, NDK 29.0.14206865. All outputs are private,
task-owned D-drive paths. No ADB, emulator, phone, model, worker or UI launch
was performed by this integration. No desktop capture or control occurred.

Run from the repository root, using distinct new directories and target trees:

```powershell
# These flags belong ONLY to each isolated capacity target, never ordinary tests.
$env:LIBSQLITE3_FLAGS='-DSQLITE_MAX_PAGE_COUNT=17'
cargo +1.93.1 run -p locallore-workspace --example capacity_probe --locked --offline --target-dir <target17> -- --directory <new-full17> --prefix 0 --expect-full
$env:LIBSQLITE3_FLAGS='-DSQLITE_MAX_PAGE_COUNT=32'
cargo +1.93.1 run -p locallore-workspace --example capacity_relief_probe --locked --offline --target-dir <target32> -- --directory <new-relief-accept> --python <python.exe>
cargo +1.93.1 run -p locallore-workspace --example capacity_relief_probe --locked --offline --target-dir <target32> -- --directory <new-relief-cancel> --python <python.exe> --cancel
Remove-Item Env:LIBSQLITE3_FLAGS
python scripts/check.py host --offline
cargo +1.93.1 clippy --workspace --all-targets --all-features --locked --offline -- -D warnings
python -m unittest discover -s scripts/tests -p test_capacity_integration_review.py -v
python scripts/android_capacity_probe.py build --offline
python scripts/android_capacity_relief_probe.py build --offline
```

The isolated portable Python disables ordinary sibling-module discovery. The
two Android scripts were invoked with this fixed trusted bootstrap, passing the
script name and `build --offline` as argv; no global interpreter setting changed:

```python
import sys, runpy
from pathlib import Path
script = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(script.parent))
sys.argv = sys.argv[1:]
runpy.run_path(str(script), run_name="__main__")
```

| Check | Actual result |
| --- | --- |
| Native host Full17 | Ready stays at 17 pages; actual commit Full; canon unchanged; same Ready key and strict reopen at revision 0 |
| Native host relief32 acceptance | Initial17, 14 owned rows, insert15 Full, free15 after removal, exact schema restored; same live Ready key accepted once, revision1, strict reopen; zero new submits/prepares |
| Native host relief32 cancellation | Same measured pressure/removal; original key remains terminal, revision0 and zero receipts; zero new submits/prepares |
| Full host check runner | 441 workspace Rust + 3 linker checks, 364 Python, four fixture bindings, formatting/default strict Clippy PASS; four existing explicit Rust ignores |
| Additional all-feature strict Clippy | PASS |
| Imported independent actual helper CLI tests | Root reran 3 PASS after import; author/reviewer coverage and source findings remain separately attributed in the linked review |
| Android Full17 profile | Both ABIs and app/test APK built offline, 146 JVM PASS with zero failures/errors/skips; lint zero errors/one existing warning; fixed17/schema3/format2/testOnly/16KiB audit PASS; 77 tasks executed, 3m16s |
| Android relief32 profile | Same checks and 146 JVM PASS; fixed32/schema3/format2/testOnly/16KiB audit PASS; 77 tasks executed, 3m12s |

The helper's exact schema digest is
`c05ced1f0439fb767f97d2ff93a34ef44eb6fbc27da6814a75fad455fb0b2c17`.
The full host run preceded the imported three independent CLI tests; their
separate pass is additive, not silently counted in the 364 run.
No ordinary Android rebuild is claimed here; accepted #85's ordinary build is
separate evidence. No production Core, Host, Store, JNI, migration, dependency,
model or inference source differs from accepted main in this packet.

## Retained invocation error and bounded claims

The coordinator's first log named `cap32-cancel.log` accidentally omitted
`--cancel`. Its JSON actually records a second acceptance (revision1/one
receipt). That attempt is retained and is **not cancellation evidence**.
The fresh `cap32-cancel-corrected` directory and log include `--cancel` and
demonstrate the terminal revision0 result above. No product correction,
assertion change, ceiling adjustment or destructive cleanup was used.

The author's prior 22 emulator executions remain historical, attributed in
[original verification](SCHEMA3_CAPACITY_VERIFICATION_2026-10-23.md).
Root build/JVM/audit checks are not device execution. Physical partition
ENOSPC/power loss, phone/ARM64 execution, real models and broad M04 acceptance
remain unqualified. The 17/32-page ceilings are deliberate synthetic native
SQLite pressure. Full M04.04 stays unchecked.

[Independent stack review](CAPACITY_STACK_INTEGRATION_REVIEW_2026-10-23.md)
identifies two #87 injected-schedule gaps corrected by dependent #94, plus a
source-only suspended release-loop admission concern for the coordinator to
resolve during #94 adoption. This packet does not claim those fault schedules
are qualified. Next runnable slice is #94 helper-failure integration and its
per-open ownership guard, preserving cleanup of existing owners.

## Private artifact bindings

Raw logs/APKs remain local and ignored. SHA256 binds the observed files without
publishing private paths or claiming byte reproducibility of APKs.

| Artifact | SHA256 |
| --- | --- |
| full host log | `d7b3c74ba7ee39c6f7848bbbbe7fd6947632bc010e39eca469d7df59b2bcf11f` |
| all-feature strict Clippy log | `c4b29a002c47d6236c2cc448ecf41986e0841ad0f98d51270798eb35972a2523` |
| Full17 log | `7f0fe871714dbd888270cd734163d437271b25960cf13ba43e2fc49018f3af04` |
| relief acceptance log | `4043fc1af7200d702185b9c2cc8161c938a04f5022573997a975fd1916b697b3` |
| mislabeled second acceptance log | `5ff42ff870fd7dec970af1c74472dbc97b2e39cd9ecea4d223203d973ffe0b37` |
| corrected cancellation log | `c69ea472d5635e9a5642e271add1c2792d3afdec11c47b195e97cb445d8967bf` |
| Full17 Android build/audit log | `f08280b72c07fc545dff835192d4cb355a6a4df8af009fa303844864f5e9a1b2` |
| relief32 Android build/audit log | `bc62e9f9af3451ec99612fa4ae81b7f87fe9abfe10028c834f094e07707c6a91` |
| Full17 app APK | `ff7b43f3371df92084579519e70a75eb6c3ea7b4a09ffc53b2aeb84d1101e88c` |
| Full17 test APK | `f367b24c3c53902371c9ec1411ab553e22c3b218c773feeb34794fc913c46634` |
| relief32 app APK | `b63a5f25b79a0ebff345878785e412af62fee980f49477563bdb475b0bbff612d` |
| relief32 test APK | `c795af855cf80dd52adb1452c1e4be985074da813de2a7d7aec9d74218438334` |
