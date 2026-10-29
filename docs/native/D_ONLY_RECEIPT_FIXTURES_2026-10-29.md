# D-resident receipt fixtures, 2026-10-29

Refs #14 (M10.02), #13 (supporting M09.06). This host-only fixture migration
unblocks six legacy receipt environment tests under the D: project-storage
policy. It changes no production engine, Android, SDK, runtime or model code.

## What is simulated

The six tests need lexical C: paths to exercise the stronger explicit-C policy,
including C:/D: reserve floors and refusal to adopt a preparation from another
root. Their original `c_root()` allocated real scratch under
`LOCALAPPDATA/Temp`, irrespective of D: TEMP/TMP. That allocation is removed.

The new test-only `SyntheticCVolume` keeps a bounded synthetic C: namespace and
stores its ordinary fixture bytes/metadata beneath a fresh D: backing directory.
The C: spelling remains explicitly synthetic. No D: path is relabelled as a
physical C: observation, and no environment variable, production verdict, hash,
floor derivation, proposal validator or deadline is replaced. The scoped helper
routes the filesystem methods required by these fixtures, restores them on
exit, rejects mapping escapes and refuses unsupported C: operations. It is not
a general virtual filesystem, OS sandbox or production filesystem interface.

Pure paths manipulate spelling; concrete paths can perform IO. The [official
pathlib documentation](https://docs.python.org/3.14/library/pathlib.html) describes
that distinction. The installed interpreter is Python 3.14.7 on Windows;
method-routing review uses its actual installed source. Rolling online
documentation currently identifies 3.14.10. No dependency changed.

## Preserved acceptance checks

All six original method IDs and method ASTs remain unchanged. Independent
pre-change inventory records seven `c_root()` calls and 28 assertion/subtest
sites. Coverage retains:

- Exact D-plan bytes and the explicit C40/D40 GiB floor pair.
- Integer-only floors, wrong-drive floor pairs and one-byte-short reserves.
- No SDK admission for preexisting or injected linked roots; preserved sentinel.
- Exact child-path shape, no foreign paths or extra keys.
- Bound preparation/config/registry/initial-disk hashes and the 1,800-second
  real-candidate run window.
- Cross-root preparation refusal, consumed-run refusal and preserved bytes.

These checks exercise ordinary real D: file creation and hashing plus synthetic
C: spelling/metadata. They do not qualify an actual C: volume, capacity,
emulator boot, Android filesystem, live lease, inference or physical phone.

## Baseline and audit guard

One safe characterization called the original fixture helper under a fresh
Python audit hook. All 20 attempted C: `mkdir` operations were rejected before
mutation. Windows `tempfile` retries a PermissionError; the initial driver
incorrectly expected one attempt and returned1. That failed helper/result is
preserved. A separate closed readback verifies all 20 blocked attempts without
rerunning the original helper. No original unit method ran, no C: scratch was
created, and this is neither a product-test RED nor a feature pass.

Every new test run uses D: working directory and TEMP/TMP/TMPDIR. The outer
Python hook rejects non-D project file-write/mutation events and records attempted
violations. The corrected driver separately allows and counts only an open whose
raw path equals the standard-library `os.devnull` OS sink; no C: filesystem path,
normalized alias, suffix rule, or mutation operation receives that exception. As [Python documents](https://docs.python.org/3.14/library/sys.html#sys.addaudithook),
audit hooks do not provide a security sandbox; native calls, subprocesses and
unreported IO are outside that claim. The fixture tests also inspect mapped
destinations and refusal/restoration behavior independently.

## Verification

At executable/test source `d4958df6e289c15ad32e0e18218b0bba7b655bd3`, the
corrected source-bound Root run passes **all 2,169 tests** in 311.612s, with
**zero failures/errors/skips/exclusions**. This includes all original six and
all 18 policy cases; counts are not additive. The finite 600s owner completes
in 317,913ms with status 0, known cleanup/capture, empty stderr, all 2,208 tracked
source hashes unchanged and zero non-D project-write attempts. The eight exact
standard-library OS null-sink opens are counted separately.

| Final artifact | SHA256 |
| --- | --- |
| Helper source |0bc447dafcc77a9c77d527f669bb593073f3b938a620537e118a823aab41cff8|
| Original test module after setup migration |28c79ab16fd256d901cfaf0f5b13fd972fae5d17208c31c6ba0639948d4b5a26|
| Independent policy test source |40e350408eaabd70e13387499e70385f0de948b29724c979b8f95d9c19c643bd|
| Final Root result |daddae0c0d48cbf8c064306c7f131c1d1868e466c9cfc793b455a9cd4d033c21|
| Corrected finite driver |07e350defcdb3d7d94fb0edbaea29bfbb234b3c832ebb9f5b714c13510d34646|
| Pure guard-decision checks |9919fca303987dd854836ca14a019ce30718302d7f6c03585d4e01a5ca60d1a8|

Independent review confirms exact original method ASTs, no production source
diff, narrow routing and property refusal, compatibility scope, and all eight
prior null-sink error traces. Final source/guard review receipt SHA256
`008425f724f97ffba5ed047d4ae2fd83f93c8ddccf7396d39e7b4c80e4271755`.
This is source/evidence review, not owner acceptance or another test execution.
No Rust/Android build or device tests are needed or claimed for this test-only
migration.


The first adapter passes the original six methods (owner 4,152ms, status0, no failures,
errors, skips, exclusions or non-D write attempts; 2,207 stable tracked hashes).
Independent new policy fixtures first pass 16 methods, then add a concrete cached
`Path.info` regression. The unchanged 17-method cohort records three assertion
failures for C/foreign-C/UNC property access, with zero errors/skips and no actual
C/UNC query. The focused property refusal then passes the exact 17 methods
(owner 4,967ms, status0, 2,208 stable source hashes, empty stderr, no write attempts).

Compatibility review separately identifies unconditional APIs newer than the
existing Python 3.9+ runner promise. The helper now feature-detects
`os.path.isreserved`, retaining reserved-component checks through a legacy pure
path fallback. Only the Path.info-specific method is availability-guarded on
interpreters that lack it. On actual installed 3.14 all 18 policy methods run and
pass, including a local-feature-seam fallback simulation (4,766ms0,zero skips,
exclusions or non-D write attempts). No global API is removed, minimum raised or
older interpreter qualified by that simulation.

The first broad run at33034145 executes 2,168 tests but has eight errors:
its overly broad guard treats standard-library `subprocess.DEVNULL` opens as
project outputs. All eight traces point to `os.open(os.devnull, os.O_RDWR)`;
all recorded targets normalize to the Windows null device. That run remains
failed (owner 332,576ms, status1,zero assertion failures/skips,all 2,208 source hashes
stable). No C: scratch write was attempted. Its driver and raw streams remain
unchanged. Driver-v2 adds only the exact raw OS-sink exception and a separate
counter. Seven pure guard-decision cases confirm ordinary D: acceptance and
continued refusal of C: project files, C: nul spellings, normalized null aliases
and mkdir operations; those decision checks perform no OS IO.

Private source-bound drivers, source snapshots, selection rosters, raw streams,
requests and receipts remain outside Git at
`D:/Dev/Experiments/LocalLore/2026-10-29-d-only-fixtures-v1`. Actual runner entries
are `python -I -S -B <packet>/check-host-v1.py <mode> <create-only-label>`
for the original cohorts, and `check-host-v2.py all root-final-all-v2` for the
final corrected-guard cohort, with
`six`, `environment`, `policy` and `all` modes. No mode adds exclusions; any
failure, skip, forbidden write attempt, source mutation or unknown owner cleanup
fails its result.

The original [path-metadata report](SAFE_PATH_METADATA_VERIFICATION_2026-10-29.md)
retains its earlier six-UNRUN attribution. This later source cannot turn that
earlier cohort into a full pass. Original baseline/fixture failures and prior
closed runtime recoveries remain preserved.

M10.02 and supporting M09.06 remain in review for this bounded host prerequisite;
full task checkboxes remain unchanged. Android external restart, physical/ARM64,
model quality/performance and full mobile fault/journey gates remain separate.
No SDK/device/model command, emulator boot, system setting, other-emulator stop,
merge, release or private upload occurs in this packet.
