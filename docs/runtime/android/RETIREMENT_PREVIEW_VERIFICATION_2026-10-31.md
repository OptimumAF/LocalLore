# Read-only AVD retirement preview verification

B39, 2026-10-31. Refs #14 (M10.02), #13 (supporting M09.06).
This host prerequisite is locally verified and in review; full task criteria
and owner acceptance remain open. No actual image retirement or new Android
run is claimed. The consumer inspector is separately frozen in draft #305.

## Change and executed source

Existing `plan_retirement` writes/pins the production ledger even without
deletion. Proposal preparation therefore now has an additive strict read-only
API and a fresh-output, fixed-registry CLI. See the
[contract](RETIREMENT_PREVIEW_CONTRACT_2026-10-31.md) and
[operating instructions](RECEIPT_AVD_RETIREMENT.md).

Base is reviewed/unmerged #296 at
`f8d4a769d2501c46be65c78bc54952c9e53f1a27`, rather than the inspector stack.
Executable/test head `74ff469e68d29c680f0e69b1a9113cf3311d34f6`
has 2,341 tracked raw inputs. All four actual host cohorts bind the same bytes.
Later reporting changes are documentation only. Independent source inspection
finds all 28 preexisting storage functions/classes AST-identical when the new
function is removed; executor and Windows backend are byte-identical to #296.
There are no app/native/runtime/model/SDK/dependency/lockfile changes. No
Android, JVM or Rust build/test rerun is needed for these host-only changes.

## Actual checks

From the physical D: source checkout, with process-local TEMP/TMP on D:, the
finite Windows process-tree owner runs this isolated stdlib driver:

```powershell
python -I -S -B D:\Dev\Experiments\LocalLore\2026-10-31-record-ui-capacity-v1\run-preview-tests-v1.py v2
```

The driver loads `test_receipt_avd_retirement_preview`,
`test_receipt_avd_storage`, `test_receipt_avd_storage_adversaries`,
`test_receipt_avd_storage_integration`, `test_owned_target_storage`,
`test_receipt_avd_retirement`, and `test_receipt_avd_retirement_windows` from
the frozen source. **96 unique named tests pass; zero failures, errors or
skips.** This includes all 15 new FIRST tests and 81 existing regressions.
Seven existing Windows cases exercise actual native calls on their own tiny
files/processes; none retires the retained real guest.

The new tests exercise the real nine-name tiny fixture, unchanged old pinned
plans, caller mutation, malformed/unknown/open inputs, ledger/lock/roster/
evidence drift, no-write/no-lock traps, fresh output, links/alternate streams,
all-root output exclusion, partial publication and rejection of the outer
preview by the executor. Imports perform no file operations.

| Owned cohort | Owner elapsed | Child result | Observation |
| --- | ---: | --- | --- |
| `python-v2` | 18,854 ms | 0 | All 96 tests pass |
| `preserve-v1` | 1,176 ms | 1 | Key-copy fence refuses; 16 ordinary partial copies retained |
| `preserve-v2` | 4,107 ms | 0 | 414 ordinary original/copy pairs verified |
| `preview-v1` | 32,833 ms | 0 | Strict actual read-only preview passes |

All four owner records have matching request/helper/source/admission/actual
child/capture/cleanup joins and no unexpected meter errors. Two earlier host
launcher setup failures (admission field-name mismatches) are retained; neither
launched its test worker. They are not product test failures or test passes.

## Actual preserved guest and preview

Candidate is only the closed model-free B32 guest at
`D:/Dev/Experiments/LocalLore/2026-10-30-archive-ui-v1/avd-v1`.
An independent read-only Windows process check finds all five original owner
PIDs absent and verifies the four original closure-bound proofs. It performs
no process termination, lifecycle operation or broad process enumeration.

The corrected collector verifies **414 ordinary original/copy pairs,
42,485,347 bytes**. Its complete manifest covers all 30 guest records and all
372 external capture files, with two credential records referencing their
already-existing outside recovery copies. No new key files are copied. Extra
ordinary inputs include original APK/build proofs and ledger snapshots. The
failed collector's partial files and all originals remain. The strict preview
subsequently verifies the borrowed key hashes; those contents/fingerprints
are not published. The existing validator may also hash prior retired key
evidence. No claim of globally avoiding all credential reads is made.

The executed preview wrapper invokes the real CLI `main` in-process under a
file/process/network audit fence, rather than spawning a standalone CLI.
It hashes **all nine exact images once, 18,979,357,184 bytes (17.68 GiB)**,
validates the complete retained-record/evidence chain and produces the exact
ten-key snapshot envelope. Its internal measured body takes 32,325 ms; owner
time above includes orchestration. Protected writes, process/network actions
and unlisted image access are denied. No audit refusals occur.

The production ledger is unchanged before/after: 11,400 bytes, SHA256
`3a4a1e3911660375bde523e9c39fbdee773b72eb3a659ee91a88f487233fd749`.
Guest/external file stamps are unchanged; no lock is created, plan pinned,
capacity reserved, image copied/deleted or guest prepared/booted. The preview
is an unlocked snapshot, not a hostile-writer or future ownership guarantee.

Independent closed-file review rehashes all 414 ordinary pairs, checks all
2,341 source bindings and four cohort joins, the 96/15 named results, preview
schema/audit, exact proposal roster, original closure/proof bindings and
capacity arithmetic. That reviewer uses only image stats and credential
metadata, not their contents. Source, closure and result reviews are distinct
from human operation approval.

## Next run, retention and limits

An actual file/Git-only `record_ui_build.verify_current` replay passes in
14,149 ms against inspector source
`535acb855177ca1df87743a7afabd7e5d18ad273` and its original 2,355 inputs.
Build manifest SHA256 is
`5cceffeea484ca15abaa156f83b23dd9cdd6e6cf66cd93b1456dceac28750d28`;
product APK is 27,756,156 bytes / SHA256
`60656e21a4dbdfcd506c473290067ea61b835c35fc01e7abd761738dd28cde78`;
test APK is 2,261,656 bytes / SHA256
`929b302275b82dfd56014fbad20e813808c89e03f4834c50dbe793103aef5784`.
The ten fixed SDK7 inspector methods remain **unrun**, and their future guest
path is absent. This replay starts no target admission, SDK, server or device.

Read-only projection, if the exact candidate were qualified as retired, gives
67,995,099,647 charged bytes including a fresh 40 GiB reservation, below the
68,719,476,736 budget by 724,377,089 bytes, with two unretired roots. This is
arithmetic only, not admission or authority. Actual fresh guards must pass.
Current two retained roots still prevent another preparation.

Private controls, failures, ordinary copies, raw joins, exact image proposal
and reviews live under
`D:/Dev/Experiments/LocalLore/2026-10-31-record-ui-capacity-v1`.
The matching selected recovery root is
`D:/Dev/Recovery/LocalLore/2026-10-31-record-ui-capacity-v1`;
ticket handoff records its terminal archive/readback seal when created.
Keep loose evidence-manifest copy paths and all old recovery in place: a ZIP
does not replace those absolute paths. No images, weights or new key copies
belong in this packet's recovery. Planned new source/records/recovery is
128–384 MiB, cap 1 GiB with stop-before 768 MiB; owned temporary cap 256 MiB,
stop-before 192 MiB; selected recovery cap 512 MiB. Existing guest state remains
separately charged and retained. These are process observations, not OS quotas.

Next operation requires separate exact-scope owner approval for nine-image
retirement and one bounded model-free inspector UI run. Record backups cannot
restore discarded disk/app/cache/RAM state. Preserve the older real-model guest,
all other emulators, shared ADB, settings and recovery. M10.02/M09.06 and
M09.04 remain unchecked/in review for their full criteria; M01.01/M01.02 and
M10.05 device/model/performance gates remain blocked/unverified. No phone,
real-model, ARM64 execution, privacy, release or merge qualification follows
from this packet.

## Approved execution follow-up

The subsequent B40 grant was actually executed: all nine approved images were
retired with qualified finalization; one fresh guarded SDK7 guest ran eight
passing methods, then the ninth failed and the tenth remained unrun. Owned
guest/service cleanup and storage closure passed. The native Host reproduction
confirms the separate Android Domain2 snapshot-consumer prerequisite in
[#307](https://github.com/OptimumAF/LocalLore/issues/307). See the
[actual execution, failures, recovery and limits](https://github.com/OptimumAF/LocalLore/blob/c6dfd53e0993aa98c42cf268c10a36c43f3522b1/docs/android/RECORD_UI_EXECUTION_2026-10-31.md).
This later authorized executor operation does not change the preview's read-only
contract or qualify the failed corrected-history UI cohort. No further boot,
deletion, model operation or merge is granted.
