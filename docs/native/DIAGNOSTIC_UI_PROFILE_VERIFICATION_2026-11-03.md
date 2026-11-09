# SDK17 diagnostic profile host verification — 2026-11-03

B105. Refs #14 (M10.03 DIAGNOSTIC_UI_PROFILE; supporting M10.02) and #3.
Implemented for review; full task criteria remain unchecked. This is a concrete
host qualification profile for the fixed B103 product, not a new Android test
run or run grant. It stacks on PR #381 `1c426411356777e45f7ee1ee1c76f663186650aa`,
which depends on unmerged #380/#377. No merge or release is included.

The tested raw source tree is `728ae9bff9a5ca0f59997c63a32f769813574e88`:
2,607 files, identical before/after every final cohort. Final publication adds
only this report. The substantive operator remains at
`8924278ce1c877e6d67c90c15a35fb23ca7198dc`, normal index SHA256
`897c91824eb4ad6ecd5034e1eecb2874c34dfd499675763a4d44a4a55ba80119`.
Publication uses an alternate D: index. Neither that checkout nor dirty storage
control worktree is reset, switched, cleaned or used as an unreviewed fallback.
The candidate is honestly labeled a raw Git snapshot, without a managed-worktree
or clean Git/HEAD claim. Managed attachment was refused for the physical repo;
no C: source workspace or `git worktree` bypass was created.

## Final actual host results

**533 unique unittest methods, zero failures/errors/skips.** All 11 sequential
cohorts completed with known owned-process cleanup and the exact same complete
source map. The original180-second per-child ceiling was retained. Splitting
complete controller methods bounds their repeated full-wire subscenarios; no
assertion or method was omitted. The longest owner lasted79.196seconds. Summed
test-capture wall times are377.491seconds, verification cost rather than device
or model performance.

| Cohort | Methods | Test capture seconds |
| --- | ---: | ---: |
| Shared/storage/owner/client/runtime/B104 regressions | 476 | 78.702 |
| New contract, source, activation, cleanup, bound-read, ledger and CLI | 48 | 0.799 |
| Complete31-client positive | 1 | 9.797 |
| Complete32-client boot-poll positive | 1 | 10.060 |
| Missing/additional/reordered/borrowed method records | 1 | 57.315 |
| Count/closure scalar coercion | 1 | 60.345 |
| Rebound client return/index/namespace/operation | 1 | 54.467 |
| Pre/post UID/path/package/hash identity | 1 | 45.984 |
| Extra output and invalid raw JUnit | 1 | 14.760 |
| Unknown observer/capture closure | 1 | 34.806 |
| Late source drift and cancelled command | 1 | 10.457 |

The57 new methods comprise53 original methods from two independent authors and
four Root ledger/CLI methods. The476 shared/existing methods include14 selected
unchanged PR #361 WindowsJob constructor/close oracles and the carried reviewed
environment tests. The selected14 are regression credit, not new independent
tests. Their absent Library executor/transfer callers were not copied or claimed.
Subtest scenarios and earlier overlapping cohorts are not added to533.

Installed Python3.14 used `-I -S -B`, explicit D: source paths and owned D:
temporary directories; project commands ran from physical D:. The private host
runner recorded full source maps, requests, raw unittest IDs, results and owner
captures. Equivalent test selections, from a physical D: checkout with D: TEMP/TMP
and bytecode disabled:

```powershell
python -I -S -B -c "import sys,unittest; sys.path[:0]=['.','benchmarks']; names=['profile','activation','checker','activation_cleanup','bound_reads','storage','cli']; result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(['scripts.tests.test_diagnostic_ui_'+name for name in names])); raise SystemExit(not result.wasSuccessful())"
```

Run each `DiagnosticUiControllerTests` method separately through the same bounded
host owner. Exact final shared selections and all eleven process arguments are
retained under the packet's `final-plan-request-v2.json`, per-phase `request.json`
and owner records. They cover storage/environment, SDK4/5 contracts, finite client,
runtime ownership, B104/DEX/APK/archive/record build readers. No Cargo, Gradle,
Android build, SDK installation or external CI result is claimed here.

## What the new tests exercise

The tiny controller fixture substitutes metadata-only APK markers and explicit
native/process/socket observation ports. Production finite wire framing,
session/proof/claim validators, complete ordered trace replay and raw JUnit
parsing still run. The31-client positive contains62 before/after proofs, six
ordered methods and closed synthetic sockets; the two-poll positive contains32
clients. These are **synthetic host traces**, not31 device operations or six
executed Android methods. Both complete positives pass before adversaries are
allowed to count as meaningful refusals.

Tests deny borrowed SDK16/legacy namespaces and targets, caller-selected
implementations/artifact roles, nonconcrete lease types, malformed scalar
authority, missing current sources, invalid selectors and changed APK joins.
The wrapper returns the same unchanged verified B104 manifest; the controller's
private projection cannot become a second saved authority. Exact checker hashes
and cached origins are tested using actual copied D: bytes, including a
same-size/same-inode/restored-mtime mutation and a separate foreign decoder base.

Actual cleanup/run/publication methods run against explicit fake observations.
False/nonboolean/raised close, cancelled/unknown wait, spent stop, unavailable
capture evidence, terminal publication failure and dispatch/qualification-edge
cancellation cannot produce an overall pass. Remaining safe tails are still
attempted. One qualified synthetic storage closure is not actual shared-ledger
closure. Separate tiny isolated schema-v2 registry cases prove read-only preview
and the80GiB second-live reservation refusal under the unchanged64/40GiB policy.

## FIRST failures, fixes and retained unqualified captures

Independent proposals were frozen before execution and remain immutable. Only
trailing blank LF cleanup is applied during integration, with identical AST and
source locations. Fixture revisions are versioned separately; old assertions
are unchanged.

- Actual unpublished pre-fix helpers: `red-v1` ran15methods, five assertion
  failure events across three failed methods,12 positive methods, no errors or
  skips. Two negatives exposed consuming wrong equal-length bytes without a
  digest of that actual read. The dispatch cancellation method failed for
  KeyboardInterrupt/SystemExit/RuntimeError after an already accepted controller.
  The new profile now hashes consumed `_bound`/`_raw` bytes and latches overall
  failure across dispatch and qualification exceptions. Existing shared JSON
  consumed-byte hashing was already correct and its two controls passed; it is
  not invented as another defect. Exact pre-fix helper bytes/source maps remain.
- Genuine startup first reached an uncaught `EnvironmentRefused`: that class
  derives from RuntimeError, absent from the inherited operator CLI catch set.
  Separate `cli-red-v1` ran2methods/one assertion failure/no errors or skips;
  the actual typed refusal escaped while the no-observation unknown-action
  positive passed. The new activation now returns1 for that category without
  dispatch or private exception output. The exact pre-CLI-fix source is retained.
- First475-method regression had54 failure records/22 errors.75 records came
  from the older positive environment fixture omitting the newly mandatory
  recovery pin; one child import expected the source working directory. Carry
  the reviewed892 fixture exactly, including a new missing-pin refusal, and run
  children from the physical source directory. These were fixture/setup
  failures, not application behavior RED.
- The old sparse fixture extended an8GiB logical test file through the Windows
  CRT. Its transient allocation was not sampled before its own teardown, so the
  first run does **not** establish the declared256MiB scratch bound. The corrected
  reviewed fixture uses checked kernel EOF and verifies at most64KiB allocated
  for that explicitly declared8GiB logical sparse metadata file. It uses no real
  guest/model/user image. Ordinary retained payload and sparse logical extent
  are reported separately; no retrospective resource acceptance is claimed.
- The513-method intermediate had29 error records in new controller constructors
  because the small fixture lacked the accepted helper's `core` alias; its476
  shared methods were clean. Fixture-v2 adds only that alias. The next52-method
  cohort had23 positive-control failures: its fake package query returned both
  package lines for the test-only filter. Fixture-v3 corrects only the fake
  observation to follow [official Android15 substring filtering](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/android15-release/services/core/java/com/android/server/pm/PackageManagerShellCommand.java).
  The production UID guard is unchanged. This is not source validation weakened
  to accommodate a fixture. Both failed cohorts are retained.
- The first final48-method pure cohort had two errors from Root misspelling
  the existing `preview_prepare` callable. Only those two fixture calls changed;
  assertions and failed source are retained. A fresh source-identical final plan
  reran all476/48/9 methods. Earlier successful shared captures remain distinct.

No original failure is relabeled passed or erased. The new qualification-return
edge oracle was added after that guard was fixed and carries no extra FIRST/RED
claim. Neither independent author reran the tests themselves. Source-review v3
SHA256 `35bfbd46b7d8c494acdfa91924e6dd9fdf31914cadde39631b01cb8effe58c6b`
closes the exact-byte, sticky-failure and CLI findings; it is not owner acceptance.
Captured-evidence and complete preservation readbacks are separate later records.

## Genuine file-only startup

`genuine-v2` passes in8.301seconds (owner8.579seconds), unchanged15 explicit
implementation/checker pins and27 complete benchmark bindings. Actual fixed
checker/source startup, B104 saved-artifact verification and the SDK17 private
projection pass. The real missing-input entry returns1 while process and socket
creation are denied. Input/runtime/guest paths remain absent. This is not a
genuine SDK17 admission: no authorization, preparation, reservation, installed
package or target observation was created.

The unchanged B104 manifest is20,564bytes, SHA256
`3921123a149bcd5a41919c56d3a5306d889bfcef39ac07a1f8672ab3d69e2c28`.
Its source,2,725 original/copy pairs, recorded427 JVM cases/49 suites and six
compiled definitions are rechecked by B104. Those remain historical B103 data.
This packet has **zero Android, JNI/ARM64, phone or model executions**.

## Retention, dependency boundaries and next step

The six current shared guards are byte-exact from unmerged892, independently
reviewed before use, not dirty storage-worktree changes or a merge of its whole
branch. No recovery executor is copied merely to read history. Actual APK
decoder/base scripts stay at parent #381. Current app/Rust/Kotlin/permissions,
runtime/model versions and product APKs are unchanged. See [the fixed protocol](DIAGNOSTIC_UI_PROFILE_V1.md).

Private OUT/REC use basename `2026-11-02-diagnostic-ui-profile-v1` under
`D:\Dev\Experiments\LocalLore` / `D:\Dev\Recovery\LocalLore`. Source bounds128MiB,
ordinary synthetic256MiB, controls128MiB and selected recovery512MiB remain;
no compiler target, bytecode disabled. Keep every failed/frozen capture, proposal,
pre-fix source, exact publication map and all originals. Primary and later small
tail manifests bind actual copies. Sparse logical fixture exception and the
initial unmeasured allocation remain explicit above; no OS quota/continuous peak
claim is made. Windows host job and file APIs are used; no Android native engine
or SDK management is exercised.

Shared ledger stayed at SHA256
`84ad23a43f6c4abd6be82164fcec2e4e7b51277f1e250a507af22654be1a7294`.
No shared-ledger migration/write, guest/ADB/model operation, other-emulator stop,
system-setting change, user-data deletion, private upload or merge occurred.
Synthetic fixture registries are isolated and confer no production admission.

Actual diagnostic Android/SAF/offline/traffic/privacy acceptance, Knowledge0/4,
physical/model qualification and M10.05 remain separately unaccepted and gated.
Next runnable task: file-only current-source capacity/preparation/run-input
inspection and an exact SDK17 operation proposal using the reviewed guards,
preserved evidence and fixed six selectors. Any retirement, preparation or boot
still needs applicable fresh exact authorization and admission. A valid manifest,
green host tests or old spent answer cannot substitute for that grant.
