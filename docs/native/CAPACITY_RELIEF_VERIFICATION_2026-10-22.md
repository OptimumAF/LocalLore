# Actual SQLite capacity relief — 2026-10-22

Bounded M04.04, [#8](https://github.com/OptimumAF/LocalLore/issues/8),
stacked on open [#56](https://github.com/OptimumAF/LocalLore/pull/56)
(`666f524`) and its unmerged prerequisites. **Host and two-emulator cold-cohort
proofs pass; in review.** Six Android method executions pass with twelve actual
Rust Full assertions. The earlier unavailable-device attempt remains recorded.
No full task, physical-device gate, merge or release is accepted here.

See the [machine-readable all-attempt report](CAPACITY_RELIEF_RESULTS_2026-10-22.json)
and [independent source/artifact review](CAPACITY_RELIEF_REVIEW_2026-10-22.md).
Claims [6358563385](https://github.com/OptimumAF/LocalLore/issues/8#issuecomment-6358563385)
and [refinement 6358621703](https://github.com/OptimumAF/LocalLore/issues/8#issuecomment-6358621703)
freeze ownership, Ready-before-padding ordering and the deliberate host schema
rejection control. Code head is `61b3432`; Android compilation used `260714b`.
The intervening correction changes only Python artifact auditing/tests.

## Mechanism and its boundary

The prior 15-page app proves real Full but cannot free capacity through the
frozen wire. This adds a distinct debug/testOnly app, fixed 32-page native
profile and test sources. The production Rust engine, Store, migration, JNI,
Host-v1 wire, gateway and Compose shell are unchanged. No dependency is added.

The real Rust owner first creates a fresh synthetic story and prepares its
original potion gift. A separate one-shot process verifies ownership and
database identity, creates only the fixed `locallore_capacity_pad_v1` table,
and inserts bounded 3500-byte zero blobs until actual SQLite Full. SQL closes
and the child exits before the original Rust owner attempts commit. Two actual
Full replies must leave its Ready/key and accepted player view unchanged.
A second one-shot child verifies and drops only the owned padding, proves
schema restoration and free pages, closes and exits. The same live owner can
then retry the original Ready key without submit/prepare or regeneration.

**Padding temporarily violates the application's exact schema contract.**
Store verification is unchanged. The host deliberately attempts one new Store
open while padded and requires `SchemaMismatch`; it never adopts the fault.
Android permits no new native owner or four-slot probe until restoration.
The cleanup helper necessarily opens its own connection. A crash during padding
would leave an intentionally invalid-schema synthetic root. This does not prove
ordinary valid-schema restart under Full, partition ENOSPC, or power-loss safety.

CREATE/DROP legitimately changes internal SQLite schema/data counters. No
counter is reset; neither the file nor its internal versions are claimed
byte-identical. Only exact application schema definitions, application ID/user
version/journal policy and accepted engine state are compared. The helper never
writes canonical tables, uses VACUUM, copies a live database or fills global disk.

Separate processes avoid the locking hazards of two independently linked SQLite
libraries accessing one file in a process. The host helper uses Python SQLite
3.38.2; the Rust owner uses bundled SQLite 3.53.2. Android's helper uses platform
SQLite, with read-only identity/schema/DELETE preflight before a verified RW
open. Compatibility is measured only on the two API 35 targets below. Existing dependencies, pins,
licenses and official sources are covered in the review.

## Actual host proof and checks

Independent calibration author `417ae032` integrated as `e0b7c43`; separate
Android author `d7ab4d0` integrated as `e7bc7bb`. Coordinator owns integration,
builds, artifact checks and device dispatch. Reviewer owns the review document
and independently ran focused synthetic Python checks. Separate worktrees and
exclusive paths were used; no shared gameplay files were changed.

Final host acceptance and cancellation both passed:

- Initial 15 pages/free 0; 16 padding rows; insertion 17 returns actual Full;
  page count 32/free 0.
- Two actual Rust commit Full replies, original Ready key, unchanged accepted
  snapshot. The extra-schema rejection control passes.
- Separate removal child drops 16 owned rows, restores schema and frees 17 pages.
- Acceptance: same live Ready/key commits once, no later submit/prepare,
  one receipt/revision 1/potion absent; duplicate and strict reopen agree.
- Cancellation while full: the key stays cancelled after relief, late commit
  and strict reopen; revision 0/no receipt/no potion spending.

All six host attempts remain recorded: initial directory-guard and generic
helper/URI-setup failures, two intermediate passes, and two frozen final passes.
Windows extended-path normalization and URI spelling were corrected before
qualification. No native Full evidence is attributed to failed helper attempts.

Reproduction from a checkout with pinned Rust and Python 3.9+ (directories must
be new; keep these synthetic files private):

```powershell
$env:CARGO_TARGET_DIR='target/capacity-32'
$env:CARGO_PROFILE_DEV_DEBUG='0'
$env:CARGO_INCREMENTAL='0'
$env:LIBSQLITE3_FLAGS='-DSQLITE_MAX_PAGE_COUNT=32'
cargo run --locked --offline -p locallore-workspace --example capacity_relief_probe -- --directory target/relief-accept-fresh --python python
cargo run --locked --offline -p locallore-workspace --example capacity_relief_probe -- --directory target/relief-cancel-fresh --python python --cancel
cargo clippy --locked --offline -p locallore-workspace --example capacity_relief_probe -- -D warnings
Remove-Item Env:LIBSQLITE3_FLAGS
python -m unittest discover -s scripts/tests -q
cargo fmt --all -- --check
git diff --check
```

Focused offline Clippy/format and 16 helper guard tests passed in the calibration
worktree. Coordinator's complete script suite passed **64 tests, zero failures,
errors or skips**, including the added artifact-audit regression. Root full
Rust formatting/diff checks passed. No new full-workspace Rust test gate is claimed.
Host child output lengths are polled at 10 ms with a 4096-byte threshold per file;
overshoot is possible. This is not an OS quota. Execution/kill/reap confirmation
is bounded; unknown ownership retains the root and stops later Host calls.

## Android build and isolation evidence

With Java 17/SDK 36/Build Tools 35.0.0/NDK 29.0.14206865 and existing Rust targets:

```powershell
python scripts/check.py android --offline
python scripts/android_capacity_probe.py build --offline
python scripts/android_capacity_relief_probe.py build --offline
python scripts/android_capacity_relief_probe.py audit
```

Ordinary build: 78 tasks, 9 executed/69 up-to-date. Existing 15-page build:
77 tasks, 9 executed/68 up-to-date. Both complete helpers/audits passed; their
47/0 JVM XML results were reused, not freshly executed.

Relief Gradle build compiled/packaged both APKs: **77 tasks executed, 47 fresh
JVM tests, zero failures/errors/skips**, both native ABIs built, lint zero errors
and one existing `GradleDependency` advisory. Two metadata API deprecation
warnings remain. The first wrapper exited 1 *after successful Gradle execution*
because the new audit counted expected AndroidX startup metadata as capacity
metadata. The correction counts only LocalLore capacity metadata, still rejects
duplicate/conflicting profiles, and adds an AndroidX-metadata regression. The
corrected audit passed the **same APKs**, without a rebuild or device retry.

All three app artifacts pass identity/permission/ABI/16 KiB ELF+ZIP alignment
audits. Relief libraries contain `MAX_PAGE_COUNT=32`, reject default/15 markers,
and its test APK targets only `org.locallore.app.capacityrelief`. Relief fixture
DEX symbols are present only in its test APK, absent ordinary/15 artifacts and
the relief app. No diagnostic provider is registered by the relief test APK.

Nine actual configuration probes rejected both flags, invalid values, ambient
SQLite flags and every mismatched special-cache pairing. Each mode owns distinct
app ID/test-source root/build/native/Cargo/tool outputs and Gradle project cache. Only debug
exists for capped modes. After ordinary → 15 → relief builds, all four previous
local APK hashes remained unchanged; all six current hashes are in the artifact.
Local ordinary APKs differ from the older installed pair verified at preflight;
they are not described as the same binaries.

## Two-emulator execution and retained availability failure

The APK keeps minSdk 26; these fixture classes use an API 28 minimum guard for
their helper APIs. That guard does not establish older platform SQLite
compatibility. Only API 35 was executed.

Default discovery ran exactly these three methods once on each target:

- `SqliteReliefNativeTest#actualFullThenOwnedPaddingRemovalCommitsOnlyOriginalReadyKeyOnce`
- `SqliteReliefNativeTest#cancelledFullReadyTurnRemainsUnspentAfterPaddingRemovalAndReopen`
- `SqliteReliefInstrumentedTest#collectedFullRecoveryAfterOwnedPaddingRemovalPublishesOnlyOriginalAcceptedReceipt`

Each asserted two actual Rust Full replies. Native cases allocate no Activity;
Main-thread before/after hooks inspect all non-DESTROYED Activity stages. The UI
case collects the real screen and retains normal Compose teardown. It checks
Full guidance, frozen accepted view/controls, same-key recovery, one accepted
receipt, disposed callbacks and strict reopen. Resource checks require closing
and draining old owners, then restored-schema four-concurrent-owner capacity.
Both complete cohorts passed: **six method executions, three unique methods,
twelve actual Rust Full assertions, four accepted relief cases and two terminal
cancellation/no-spend cases**, zero failures/skips/unfinished. The same app/test
APK hashes were used without candidate source/timeout changes or method retries.
The observed discovery order was UI first, then the two native cases; this is
not a new ordered Suite contract.

Review corrected failure cleanup before execution: fence models/close and drain
existing owners first, then remove padding with known child ownership, then
probe/delete only after restoration. Unknown helper/drain/restoration/slot state
retains the root and poisons later fixture bodies before further root/helper/
native dispatch. It does not abort JUnit discovery or Compose rule construction.
The helper has bounded pipes/waits and a self-expiry lease. Normal helper exit,
reader/owner drain, schema restoration, strict reopen, Activity boundaries and
root cleanup executed successfully. Forced cleanup, expiry and poison branches
remain source-reviewed without deliberate execution qualification.

Initial preflight saw five emulators/zero phones. Selected A/B were Android 15,
API 35, x86_64, 4096-byte OS pages; ordinary and prior capacity installed APK
hashes were verified and relief packages absent. Later A dispatch failed its
preserved-package identity guard **before install or instrumentation**. Read-only
checks then found zero ADB devices and no emulator/qemu processes. Cause unknown.
In that initial attempt neither new APK was installed, no app was stopped, no
test method ran, and B was not dispatched. The private journal's false final flags mean *unverified*, not
that an app/hash changed. Local ADB clients were cleaned. Final device package
identity/absence for the vanished instances remains unavailable.

Avery then explicitly authorized relaunching the two test AVDs. Read-only
discovery found saved October 20 port/AVD/executable/argument records. Only A/B
were launched using those records and AVD home; their console names, boot and
API/ABI checks passed. An unrelated third emulator was left untouched. Actual
launch logs identify A Emulator 37.2.12.0/build 16428233 and B 35.3.12.0/build
12990079. Both run Android 15/API 35/x86_64 with 4096-byte OS pages. These are
different emulator versions, not a performance comparison.

The old-package identity preflight failed after this cold launch: all four prior
LocalLore packages were absent on both persistent images. The historical launch
records do not prove the latest vanished processes' exact image/argument state.
No earlier package was reinstalled, stopped, cleared or replaced. A separate
cold-cohort baseline was explicitly recorded before installation: prior packages
absent, new relief packages absent. This fresh-root fixture needs no old save.
It does not establish continuity with or recover the vanished live instances.
Both this failed identity preflight and the initial dispatch remain recorded.

Only the two new relief APKs were installed with `-t` on each selected target.
Each ran the fixed three-case cohort once. Final guards verify their installed
hashes, stopped relief-app absence, boot readiness, clean local ADB clients and
unchanged absence of the four older packages. Supplemental checks require zero
stderr as well as package-query exit 1/empty stdout; an unreachable device is
never accepted as package absence. The private collector strengthened that
guard before B; supplemental final guards covered **both** targets without
repeating tests. Local APK hashes still match the frozen candidates.

No wipe/reset/data-clear/uninstall/root/configuration edit occurred. Saved
snapshot/graphics arguments were reused; no comparison with the prior live
cohort's runtime state is inferred. The two relaunched emulators remain running;
only the identified relief app processes were stopped. Host raw logs, private
protocol details and calibration databases remain under ignored `target/`.
Android synthetic roots were app-private; passing cleanup removed them. Unknown
cleanup would retain those roots on-device. Public results contain only
sanitized stages, fixed cases/counts and hashes.

## Handoff and remaining gates

M04.04 remains partial/in review; this bounded Android relief gate now passes. The prior
framework teardown failure remains unknown/unfixed; no reproduction or repair
follows from this packet. Physical phone/M01, real-model app inference, ARM64/
16 KiB OS/API 26/36 execution, heap/power-loss/performance, valid-schema Full
restart, partition ENOSPC and hosted CI remain unqualified.

Next scoped runnable task: deliberately exercise helper/cleanup failure and
unknown-ownership fencing in this isolated fixture. Valid-schema Full/restart
and partition ENOSPC require separate mechanisms/evidence. To rerun the current
normal-path proof, first freeze the actual target baseline/boot/ABI and candidate
hashes, then install only the new package and run A followed by B. Use `am instrument -w -r
org.locallore.app.capacityrelief.test/androidx.test.runner.AndroidJUnitRunner`;
retain every attempt and verify owned app stop/absence plus prior APK identities
afterward. Preserve the actual baseline, which may differ from an earlier live
instance. Do not treat an ADB transport failure as package absence or a JUnit
pass. No merge, milestone checkbox or global goal completion is authorized here.
