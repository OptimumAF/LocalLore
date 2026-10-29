# Receipt AVD storage lifecycle

This host tooling supports M10.02 / issue #14. It limits newly prepared receipt
AVDs through one durable host registry. It does not qualify an Android run,
create a filesystem quota, clean an emulator automatically, or change snapshot
flags, deadlines, SDKs or historical evidence.

`benchmarks/receipt_avd_storage.py` has no import side effects and never invokes
an SDK or deletes guest data. Production integration uses the fixed default
`D:/Dev/_Migration/LocalLore-AVD-Storage`. The registry parent must already exist
on physical D:. Synthetic tests supply isolated D: registry directories; moving
or replacing the production registry is an operator recovery action.

## Admission and retention

Before the central prepare entry point creates its root or invokes SDK tools,
it calls:

```python
storage.reserve_prepare(root, admitted_prepare_sha256)
```

First initialization builds and forces the initial ledger in a unique sibling
staging directory, then atomically publishes the completed directory using
Windows' no-overwrite rename. A contender never sees a deliberately empty new
registry. A preexisting empty or corrupt directory is still refused; there is no
implicit repair. The create-only lock and flushed, atomically replaced ledger
serialize admissions across unrelated parent folders and processes. At most two unretired roots are
allowed, within a 64 GiB accounting budget. A preparing, prepared or retained
guest reserves 40 GiB: 8 GiB SD base, up to 8 GiB SD overlay, 12 GiB userdata,
8 GiB RAM and 4 GiB overhead. Two simultaneously preparing/live guests therefore
do not fit the budget. A verified closed guest instead charges the measured
logical bytes of **all** files still under its root. Closed roots are measured
again before admission, using at least their previous recorded charge.
Repeating verified closure also preserves that previous closed charge; external
truncation alone cannot release capacity. The first closure may replace the live
40 GiB reservation with measured bytes. Verified retirement is a separate path.
These are conservative admission estimates, not guaranteed free space or limits
on writes by the emulator, Windows or another process. Existing free-space
admission remains necessary.

After successful prepare creates files, record `prepared`. A failed preparation
stays `preparing` and keeps its full 40 GiB reservation, including when no root
was created. A terminal result may separately establish verified closure.
Before any run dispatch, reopen the tracked root as retained
and bind its distinct run proposal digest:

```python
storage.record_state(root, "prepared")
storage.record_closed(root, root / "prepare-result-v1.json")
storage.record_state(root, "retained", proposal_sha256=admitted_run_sha256)
# Only now may the existing run owner launch the guest.
storage.record_closed(root, root / "owner-result-v1.json")
```

`record_state` restores the full 40 GiB reservation and refuses if it cannot fit.
`record_closed` requires the currently admitted proposal digest,
`closure_verified: true`, and `cleanup_complete: true` (or the prepare result's
`child_cleanup_complete: true` when there is no `cleanup_complete` key). Closure
is a process/evidence fact, not a successful guest test or graceful guest flush.
An interrupted preparation stays charged even if it never created a root.
Missing previously prepared/closed/retired roots, malformed/missing ledgers,
changed closure evidence, stale locks, links and overlapping registrations fail
closed. There is no automatic stale-lock recovery or reservation cancellation.

Exceptions must not turn unknown cleanup into closed. If final tracking fails,
the earlier reservation remains. Failed and frozen runs remain tracked until
their actual evidence and closure qualify for an explicitly reviewed retirement.
Fresh admission does not discover or adopt untracked historical roots; their
inventory and disposition remain a separate operator task.

The SDK4 owned-target and SDK5 restart-target owners launch through the shared
`owned_target_owner._TargetRuntimeCore` instead of `receipt_avd_environment.run`.
Their shared launcher verifies the guest proposal binding and restores the full
`retained` reservation before publishing any boot claim or starting an emulator.
An untracked root, changed source or unavailable ledger refuses before boot.

After the parent owner has verified the worker result, known owner cleanup,
retained process identities, closed handles and unchanged final source bindings,
it creates `guest-storage-closure-v1.json` inside the guest root. This separate
create-only receipt binds the admitted guest proposal digest plus the verified
owner-result, worker-result and final source/handle record. Existing frozen
owner/worker result schemas stay unchanged. Only this qualified path calls
`record_closed`; unknown cleanup, failed verification or failed storage tracking
keeps the previous reservation. The new closure is retained and archived with
every other non-disposable guest file. A qualified host fixture does not qualify
a real device, model or restart run.

If any direct-owner proof key (`admission`, `owner_result`, `worker_result`,
`after`) is present in a closure, all four bindings are required and their original
files must still match bytes/hash. Closed-ledger loading, charging, retirement
planning and finalization recheck those original proof files. Mutating or deleting
an external owner proof therefore refuses subsequent lifecycle operations.
The four declared proof paths stay charged for closed and retired guests; paths
already counted in the guest root or declared archive roster count only once
within an entry.

Keep those external proof files and their original owner output tree in place.
The guest manifest archives guest-root records; it does **not** archive the entire
owner output tree or transitively preserve every raw file referenced by those
proofs. Operators must retain that separate evidence tree and any frozen captures.
These checks cover the four explicitly bound proof files, without claiming full
recursive proof preservation or replaying owner verification during admission.

## Evidence-aware retirement planning

Retirement defaults to a dry-run plan. First preserve **every non-disposable
file** outside the guest root, including failed captures, receipts, generated
configuration and logs. Build an external manifest with this exact shape:

```json
{
  "version": 1,
  "root": "D:\\example-guest",
  "complete": true,
  "files": [
    {"relative": "owner-result-v1.json", "binding": {
      "path": "D:\\example-evidence\\owner-result-v1.json",
      "bytes": 123,
      "sha256": "<64 lowercase hex>"
    }}
  ]
}
```

The example's size/hash are placeholders. Each binding must match actual bytes,
and every current non-disposable guest file must have an external byte-identical
copy. The closure result must itself be one of the preserved files. Both the
manifest and its files must be outside the guest root, regular, singly linked,
and on D:. `complete: true` alone supplies no evidence.

```python
plan = storage.plan_retirement(root, outside_manifest_path)
# Review and separately authorize the exact host operation represented by plan.
# This module does not perform that operation.
storage.record_retired(root, plan)  # Only after that operation actually finishes.
```

Planning checks closure and all evidence hashes, scans without following links,
hashes the exact proposed image roster and pins the plan in the ledger. The
only eligible paths beneath `content/locallore_receipt_api35_v1.avd/` are:

- `cache.img`, `cache.img.qcow2`
- `encryptionkey.img`, `encryptionkey.img.qcow2`
- `sdcard.img`, `sdcard.img.qcow2`
- `userdata-qemu.img`, `userdata-qemu.img.qcow2`
- `snapshots/default_boot/ram.img`

Other `.img` / `.qcow2` paths refuse planning; other files must be preserved.
The planner does not infer disposability from age, extension, apparent size or
snapshot launch flags. RAM mapping files can remain despite `-no-snapshot` and
`-no-snapshot-save`. Hashing a large image is deliberate work; it is never an
import/admission side effect.

An explicitly authorized host executor must recheck closure, plan and file
identities immediately before removing only those exact files. It must prevent
concurrent guest dispatch during the operation, reject reparse points/hardlinks
and races, and retain the original root, receipts, config, logs and recovery
evidence. Do not use recursive removal, mirror deletion or wildcard cleanup.
This module supplies **no** such executor or implicit authorization. An archived
record set is not a full recovery backup of the discarded guest disks.

Finalization accepts only the unchanged pinned plan, with all planned images
absent, no other disposable images present, all preserved guest files unchanged,
and all external evidence hashes still matching. A partial cleanup or changed
evidence keeps the reservation. Finalization creates a separate, create-only
`retired-<root-path-hash>.json` in the registry and binds its exact bytes/hash in
the retired ledger entry. Before excluding a retired entry from the active-root
count or recomputing its reduced byte charge, admission verifies that source
tombstone, strict original plan, current image
absence, complete preserved file set and all external evidence hashes again.
Changing a ledger state to `retired` alone cannot release capacity. The original
root name cannot be registered again. Original record files stay in place.
External archives, tombstones and the registry must be preserved and backed up.
Every enumeration error refuses charging, planning or finalization; an unreadable
subtree never counts as an empty subtree.

Retirement removes a root from the two-unretired-root count, but does not make
retained bytes free in budget accounting. Remaining root files, declared external
evidence copies, manifest and retirement tombstone stay charged at current logical
size. Duplicate declared paths within an entry count once; evidence is already
required to reside outside that root. Shared paths across separate entries may
be conservatively charged more than once. Unrelated project outputs and
undeclared archives are outside this accounting guard. No evidence is pruned to
make another admission fit.

## Host verification and boundaries

Run with process-local `TEMP` and `TMP` set to `D:/Dev/_Temp`:

```text
python -B -m unittest scripts.tests.test_receipt_avd_storage -v
python -B -m unittest scripts.tests.test_owned_target_storage -v
```

Fixtures are tiny files on D:; tests never invoke Android tools, boot a guest,
touch the production registry or delete real guest data. The suite covers count
and byte admission, interrupted preparation, concurrent admissions, corrupt
ledgers, stale locks, missing roots, changed phase digests, closed-state reopening,
hardlinks/reparse paths, exact disposable roster, external evidence tampering,
partial retirement, preserved-record integrity and durable tombstones.
Regressions include corrupt retired entries, images reappearing after retirement,
tombstone/archive drift and unreadable guest subtrees.
Python 3.9 syntax is parsed; the actual host test interpreter version is reported
separately. Real lifecycle integration and any host cleanup need their own
verification. Filesystem checks assume a trusted local operator; they do not
provide a hostile concurrent filesystem attack boundary or Windows directory
power-loss durability guarantees. Atomic replacement never makes an incomplete
prepare reservation automatically reclaimable.
