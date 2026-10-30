# Guarded receipt AVD storage integration

Refs #14 (M10.02), #13 (supporting M09.06). This is host verification of storage
admission and lifecycle wiring. It does not establish a real guest, phone, model
or Android restart result. Full milestone checkboxes remain unchanged.

## Reviewed source

The owner-supplied uncommitted guard was copied with before/copy/after hashes
from the named coordinator checkout into an isolated worktree. Both original
dirty checkouts remain untouched. The fourteen-file snapshot is 461,707 bytes;
its manifest SHA256 is
`e5685c9cbb3c9c2a60133b7e932a627d6243038f7b1b953a1527bc2737607280`.
Commit `3b87a7ab` preserves that candidate for review. The integration is stacked
on unmerged #264 (`c3102ddc`), with the earlier prerequisites still unmerged.

The fixed production registry is `D:/Dev/_Migration/LocalLore-AVD-Storage`.
Preparation reserves before creating the guest or invoking SDK tools. The
shared SDK4/SDK5 launcher restores the retained reservation before its boot claim
and launch. Verified parent closure adds a separate source-bound receipt before
recording closure, preserving the existing owner/worker result schemas.
Admission allows at most two unretired roots within 64 GiB; each preparing/live
guest reserves 40 GiB. Retirement plans and tombstones are verified separately;
this change supplies no image deletion executor or retirement authorization.
See [the lifecycle contract](../runtime/android/RECEIPT_AVD_STORAGE.md).

Independent review found one concrete accounting failure. Repeating closure
after externally shrinking a tiny synthetic image reduced the prior charge
from 3,135 to 158 bytes and admitted another 4,000-byte reservation into a
scaled 6,400-byte budget. Commit `4a250931` adds the original regression before
the fix: one method with two failing invariant subtests. Commit `4c53db36`
preserves the previous charge only when the entry was already closed; the first
verified closure still replaces the live reservation with measured bytes.
The exact unchanged regression passes after that fix. No threshold, assertion,
retirement requirement or deadline was relaxed.

## Actual host verification

Commands ran from physical D: worktrees with TEMP/TMP/TMPDIR set to
`D:/Dev/_Temp`. The private finite runner pins all tracked source bytes and its
own helper before/after each run, captures raw output and uses a Windows owned
job. Its cooperative Python audit rejects non-D project writes and Python
open/listing/mutation attempts under `D:/Dev/_Migration`. Only the exact stdlib
OS null sink is exempt from the write rule. It is not an OS sandbox: native IO,
lstat and subprocess hook inheritance are not covered. Environment imports
precede the hook; their source was independently inspected for import IO.

| Check | Actual result |
| --- | --- |
| Original regression RED at `4a250931` |1 method, 2 failed invariant subtests, 0 errors/skips; owner 3,241 ms, exit 1.|
| Same regression GREEN at `4c53db36` |1 pass; owner 3,090 ms, exit 0.|
| Independent supplied storage/wiring/owner roster at `3b87a7ab` |51 pass; owner 7,385 ms, exit 0.|
| Independent existing environment/contracts/SDK4/SDK5/controller/fault roster at `3b87a7ab` |251 pass; owner 111,234 ms, exit 0.|
| Full current Python suite at `4c53db36` |2,229 pass; owner 216,139 ms, exit 0; all 2,218 tracked raw files stable.|

All successful runs have zero failures, errors, skips and exclusions, known
output capture/cleanup and empty parent stderr. No forbidden audit attempts
occurred. Full discovery recorded eight exact stdlib null opens. The independent
51 and 251 use the original supplied source; they are not relabelled as runs of
the later fix. Current full discovery includes the fix and original regression.

Private command entry:

```text
python -B <packet>/check-storage-v1.py module:scripts.tests.test_receipt_avd_storage_adversaries root-red-v1
python -B <packet>/check-storage-v1.py module:scripts.tests.test_receipt_avd_storage_adversaries root-green-v1
python -B <packet>/check-storage-v1.py all root-all-v1
```

The packet is
`D:/Dev/Experiments/LocalLore/2026-10-29-storage-guard-integration-v1`.
It retains the supplied snapshot, RED/GREEN, full captures, independent reviews
and exact selected method rosters. The original regression uses retained tiny
D: files; provided lifecycle tests use isolated synthetic registries and mocked
SDK/native operations. No production registry, real guest image, device, model
or service was accessed by these test runs.

## Limits and next admitted cohort

These checks establish trusted local operator/producer accounting and refusal
behavior. Closure flags and file hashes do not authenticate arbitrary producers
to Windows. The ledger does not automatically discover historical guests or
create an OS disk quota. No hostile concurrent-filesystem or power-loss
guarantee is made. Retirement provenance does not authorize deletion or prove
discarded guest disks recoverable. Legacy standalone lease/SDK3 ten-file source
closures are outside this SDK4/SDK5 qualification and must not be used to bypass
the current guarded entry points.

The frozen `f1b81363` build and all older guests/recoveries remain preserved and
ineligible for this new guarded cohort. The human subsequently approved the
current code-fixed fresh `restart-after-metadata-v1/avd-v1` root, after read-only
inspection found the earlier named root already existed. That approval does not
reuse the old root, claims or results. The next action is a new frozen
`4c53db36` source/build/admission binding followed by fixed shared-ledger
admission and one bounded import/AUTHOR/passive restart case. Device/model
results require actual execution and separate evidence. No merge occurred.

The subsequently executed [guarded cohort](GUARDED_RESTART_RUN_2026-10-29.md)
verifies real import/AUTHOR and owner/storage closure, but refuses complete
restart collection at the fixed session boundary. That failure stays failed.
