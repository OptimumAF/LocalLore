# SDK18 record cancellation profile verification — 2026-11-03

M10.02 `RECORD_CANCELLATION_UI_PROFILE`, supporting M09.04/M09.06, is implemented
for review. Full milestone criteria remain unchecked pending owner acceptance.

Code: `3b09e2f26649739cb7b90ba1ffcca84846f45a86`.
Tested tree: `71bae7582cdfa4f19591390b2cbe7caa25924e78`.
Tooling parent: PR #387, `029f5dab4a60e34f4c75f270ef054e5dbe261815`.
Product: PR #386, `7e29fb724ed781e953f321385f66a5f8982ad0f1`, on #385.
The code was preserved and pushed after 131 closed passing checks; the remaining
39 subsequently passed against the same unchanged tree. Documentation is added
after executable verification. No application, Rust, Kotlin or dependency changed.

## Actual checks

Windows/Python3.14, physical D: working/output directories, process-local
TEMP/TMP `D:/Dev/_Temp`, bytecode disabled. `run_owned.py` checks the reviewed
host-owner source and freezes the selected worker bytes/command before each
launch. The generic 180-second owner ceiling is unchanged. Test bodies deny real
process/socket dispatch; ordinary checked Python host workers do execute.

| Final scope | Unique methods | Capture seconds | Owner seconds |
| --- | ---: | ---: | ---: |
| SDK18 original31 + Root3 + separate activation edge1 | 35 | 115.565 | 116.115 |
| Shared typed contract/storage | 80 | 7.444 | 8.161 |
| Existing B111 build/boundary | 16 | 12.526 | 13.233 |
| Unchanged SDK17 profile/controller/activation | 39 | 302.796 total | 308.587 total |

**170 distinct test IDs, zero failures/errors/skips in final scopes.** This is a
union across 13 bounded workers, not a single-process full-project test claim.
The SDK17 scope uses one metadata30 worker and nine fixed one-method controller
workers. The longest final worker is116.115seconds. Repeated FIRST/targeted runs
and mutation-like fault variants do not add to this count.

Executed commands from the private packet root include:

```
python -B run_owned.py first-v1
python -B run_owned.py edge-first-v1
python -B run_owned.py boundary-v2
python -B run_owned.py final-new-v2
python -B run_owned.py final-core-v2
python -B run_owned.py final-build-v2
./run_diagnostic_regressions.ps1
python -B run_owned.py genuine-v6
python -B commit_code.py
```

The fixed final selection covers
`test_record_cancellation_ui_profile`, `test_record_cancellation_ui_controller`,
`test_record_cancellation_ui_activation`,
`test_record_cancellation_ui_profile_boundary`,
`test_record_cancellation_ui_activation_edge`, the four unchanged
`test_diagnostic_ui_*` profile/controller/activation/activation_cleanup modules,
`test_owned_target_contract`, `test_owned_target_storage`, and the two existing
`test_record_cancellation_ui_build*` modules, all under `scripts.tests`.
The private phase manifests retain the exact nonduplicated IDs and source maps.

Real controller/replay methods process synthetic binary frames, raw JUnit,
claims and complete transcript graphs. Positives require30 clients/60 brackets
and the five exact selectors before adversarial mutations. Cases reject borrowed
SDK17 roots/sessions/proofs, reordered or extra records, changed installed
UID/path/hash, foreign concrete types, malformed/boolean facts, origin drift,
valid legacy force-stop authority, stale evidence and uncertain closure. The SDK18
controller/activation native, socket, owner and storage observations are explicit
fake ports. Shared storage regressions also write real isolated temporary test
registries.
The two physical-D Root supplement methods explicitly require Windows; this
host ran them, with zero skips. No non-Windows CI result is claimed.

## Preserved failures and fixes

1. **Original FIRST31:**31 methods, one assertion failure, zero errors/skips,
   114.812s capture/115.414s owner. The standalone controller attempted mkdir once
   before full running/source/build validation. The final new controller performs
   `_inputs` before output creation and reuses its admitted manifest. The original
   test suite is unchanged. Three additional tests exercise actual typed
   retargeted D: parents and actual preflight control flow with external reads
   mocked, shared-reader alias origin, and valid legacy `--user 0` force-stop.
2. **Wrong intermediate replacement:** a coordinator edit initially matched the
   `_inputs` function instead of `run`, introducing recursion and leaving late
   validation. Actual `final-new-v1`34 methods record10 assertion failure events,
   zero errors/skips,12.666s capture/13.237s owner. The exact bad source and review
   are retained. Function-scoped correction and actual focused4/5-method passes
   resolve it; no failed capture is promoted to a pass.
3. **Independent activation edge FIRST:** one method with positive and interrupted
   variants, one assertion failure, zero errors/skips. A local dict subclass
   raises KeyboardInterrupt immediately after actual `execute` sets its success
   flag. The old catch left it true. The new catch explicitly clears `passed`.
   This is an injected host control-flow exception, not real native cancellation.
4. **Old-profile full worker:** the original39-method SDK17 worker times out at
   180.009s with known host cleanup. Its partial live log/fixtures remain
   unqualified. The same unchanged39 tests subsequently pass in the bounded
   groups above. Neither the deadline nor their assertions changed.

Original B75 four-file FIRST proposal bytes and the separate edge test remain
unchanged. Root3 later adds only Windows applicability to two methods; its prior
4,528-byte form was reconstructed by reversing those imports/decorators and
SHA-joined to the failed capture. That is source attribution, not original mtime.

## Genuine file-only preflight

`genuine-v6` completes in10.173s capture/10.759s owner. It invokes actual B111
`create_manifest` and `verify_frozen_product` against the existing saved
32,140-byte descriptor (SHA256
`4d39b74ad5aee455ce9060c01d760204022101e4b6b8ce58d12f666450d2894e`), projects
its five real compiled method rows and fixed APK/signer facts, checks current
checker origins/bytes and all28 source bindings, then refuses absent run input.
It writes no authority or operational input and does not overwrite the saved
descriptor. It does not positively validate a current run admission, installed
Python/native tools, prepared guest, native owner/cleanup or Android execution.

Earlier private preflight failures remain separate. Genuine-v1 exits1 with320
stderr bytes counted by the shared owner; raw stderr was not retained, so no
exact original trace/cause is asserted. Genuine-v2 retains the runner's wrong
29-binding assertion; the optional initializer is absent and the real count28
passes after correcting the runner, without production changes. Genuine-v3/v4
cover create/source inspection. Genuine-v5's stronger saved verification correctly
refuses a forward-slash spelling that differs from its exact pinned Windows path;
genuine-v6 uses canonical `str(Path(...))`. No artifact-role guard was relaxed.

## Source, review and retention

Every final scope and genuine-v6 has identical before/after maps across all2,642
tested files; all2,629 inherited Git blobs are unchanged. Seven profile modules
and six test/fixture files are added. Existing SDK16/SDK17 source is unchanged.
The final documentation-only delta is separate from the tested executable tree.

B72 authored controller/activation and independently reviewed Root's five modules,
original31 tests, Root3, the independent edge oracle and captured evidence. B75
authored original31/edge1 tests and independently reviewed all production and
Root3. Neither receives independence credit for their own authored artifact.
Sealed reviews and exact failed/closed workers remain private on D:; owner
acceptance is still pending. Publication and preservation are separately sealed
and linked from the final ticket handoff, not inferred from source review.

Private root:
`D:/Dev/Experiments/LocalLore/2026-11-03-record-cancellation-profile-v1`.
Recovery root:
`D:/Dev/Recovery/LocalLore/2026-11-03-record-cancellation-profile-v1`.
The initial256MiB ordinary-output estimate was revised explicitly to512MiB after
the first synthetic wire cohort alone measured43,879,339bytes. Originals,
failures, frozen sources, controls and fixtures are retained; a lossless recovery
archive is verified member-by-member instead of duplicating an uncompressed
fixture tree. Standard passing host tests may clean their own new temporary
registries and tiny owned toy image/proof files; captured evidence trees and
preexisting data remain preserved. No preexisting or preserved evidence, guest
or model data was deleted or deduplicated. No operational guest/model/compiler
output or shared AVD budget change is part of this packet. Final manifests/audit record actual
storage and recovery coverage. Byte recovery is not live process/NTFS identity,
fixture-link-topology or guest-image recovery.

## Remaining gates

Recorded B110 JVM425/50 and five compiled Compose methods are not fresh JVM or
Android results. **Android execution0/5**; no physical phone/model/ARM64/CI or
feature acceptance result. No SDK/ADB/guest/model operation or shared operational
ledger write, phone discovery,
settings change, other-emulator stop, release or merge occurred. The normal
checkout/index and shared ledger are separately rechecked at closure.

Next runnable M10.02 host work is a fixed fresh-preparation/input handoff to this
profile. Device execution still requires capacity, reviewed exact inputs,
guarded preparation and fresh exact approval. Existing spent grants and pending
retirement-only authority do not authorize this new run.
