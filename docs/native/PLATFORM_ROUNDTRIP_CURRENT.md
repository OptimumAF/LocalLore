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
shared parent barrier. The operator launcher and separately approved guest
admission remain pending.

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

## Verify the ordered Android return evidence

The return controller revalidates the Windows receipt and exact outbound
prefix on the same SDK25 session. It rechecks installed identity and the
private owner marker before spending the distinct write claim. The fixed
private write uses noclobber and the receipt's exact archive input. A
byte-exact readback is required before the return instrumentation claim.
The final archive must match the Windows oracle and package identity must
still match the outbound evidence.

The client checks the retained receipt and prerequisites again before each
return-only dispatch. A generic SDK call cannot use the return commands
without this gate. Live execution closes the capture at the end. Closed
verification requires the complete outbound and return capture roster,
with no extra client or proof records.

```powershell
python -B -m unittest discover -s scripts/tests -p test_archive_roundtrip_return.py
```

Host tests exercise the 18-command return sequence using synthetic records.
End-to-end acceptance requires the final Windows replay on a real admitted
guest's returned archive.

## Check the final Windows archive replay

The final step replays the complete Android return evidence and binds its
session, bridge receipt, write claim and exact command records. It writes
only the verified final archive into a fresh input directory. Before the
one-shot child, it bounds and reads back the complete request. The retained
Rust executable runs with the owned-stdin barrier and fixed `check-final`
arguments, a 120-second deadline and 4 KiB combined capture. The create-only
receipt requires known process closure, the exact terminal and the two
expected output files. Closed verification checks the receipt without
running a child.

```powershell
python -B -m unittest discover -s scripts/tests -p test_archive_roundtrip_final.py
```

The actual Windows smoke checked the independently continued synthetic final
archive retained by the earlier Rust test. Its Android return evidence was
simulated. The typed exchange entry now calls the four transfer legs over an
already-admitted SDK25 lease. The operator admission and stop/ledger
closure remain separate from this exchange.

## Reverify the shared owner stop and closure

The controller accepts an already-running SDK25 lease and a separate
controller process identity. It needs at least 1,210 seconds remaining
on the owner lease, including a 10-second stop reserve. It verifies all
four transfer legs before publishing the shared, admission-bound
`stop-v1.json` through a non-replacing Windows rename. A failed exchange
preserves the attempt and leaves the finite owner to expire. Unconfirmed
observer cleanup is reported separately and prevents a controller receipt.

The closed check ties the expected owner and controller identities to the
running lease, transfer receipts, scoped stop and shared worker/parent
terminals. It requires every shared cleanup flag and the exact closure
record in a closed entry of the shared ledger. The existing ledger
validator checks either supported ledger schema. The closed check reads
evidence and has no guest command or ledger write.

```powershell
python -B -m unittest discover -s scripts/tests -p test_archive_roundtrip_lifecycle.py
```

The lifecycle tests use synthetic owner and ledger records. The fixed
operator launcher and real guest admission remain separate.

## Verify the operator's prepared-run admission

The host gate accepts one externally approved authority record at the fixed
SDK25 operation root. That record binds the exact admission and the current
prepared v2 snapshot of the shared storage ledger. The admission binds the
reviewed source, retained APKs and fixture executable, and scoped run
proposal and authorization. The target must already be prepared by the
shared workflow. The gate allows one boot, with a 1,700-second owner lease
and 1,800-second guest ceiling. Preparation, model work and retirement
require separate authority.

The preboot check performs no launch or reservation. Spending writes a
create-only attempt claim. The future owner must recheck it and use the
same ledger pin and prepare digest in the shared locked transition to
`retained` before publishing its boot claim. That atomic transition uses
ledger v2. The closed verifier can still replay either supported schema.
A v1 ledger, changed snapshot or observed storage lock refuses this
prepared-run admission. The check reads the pinned installation and
registry metadata and rehashes the prepared guest's initial SD image.

```powershell
python -B -m unittest discover -s scripts/tests -p test_archive_roundtrip_admission.py
```

These host tests use synthetic admission, authorization and ledger
records. The real operator launcher, authority and guest run are separate.

## Verify the guarded owner handoff

An already-owned supervisor job can publish one handoff for the spent
SDK25 attempt. The fixed owner parent and inherited worker require the
same handoff digest, held Windows process ancestry, and bounded launch
window. The worker rechecks the handoff before starting the isolated
server and again at the shared owner's last pre-emulator guard.

The shared storage transition receives the exact approved prepared ledger
pin and preparation digest under its lock before a boot claim is written.
If the supervisor or authority disappears after the transition or boot
claim, the worker refuses launch and preserves the spent evidence and
reservation. A later supervisor must verify the controller's remaining
lease budget after guest registration.

```powershell
python -B -m unittest discover -s scripts/tests -p test_archive_roundtrip_handoff.py
```

These are synthetic handoff, Job membership and ledger-transition checks.
The supervisor launcher, its controller process supervision, and separate
guest authorization are still required.
