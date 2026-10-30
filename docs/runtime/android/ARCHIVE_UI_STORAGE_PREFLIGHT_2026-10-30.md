# Archive UI storage preflight

Date: 2026-10-30. B26, M10.02 / supporting M09.06. This is read-only
prerequisite evidence for the [guarded UI harness](ARCHIVE_UI_HARNESS.md) in
open/unmerged [PR #294](https://github.com/OptimumAF/LocalLore/pull/294),
`a27e4dfd80217e956255866cd8ad8e10d161437a`. No guest was retired or admitted.
Full tasks remain unchecked. Actual Android execution is still blocked.

## Observed inventory and capacity

The production ledger is
`D:\Dev\_Migration\LocalLore-AVD-Storage\ledger-v1.json`.
Before/after bytes match: 1,054 bytes, SHA-256
`530773cadb45ae511fa6a63aaa8c7058bcca8c070548c7662c0e00158ab663d9`.
It records two closed unretired roots, no retirement plans or tombstones.
This packet never acquires its lock or writes its files.

| Registered root below D:\Dev\Experiments\LocalLore | Image bytes | Non-image record bytes | Recorded charge |
| --- | ---: | ---: | ---: |
| 2026-10-29-restart-after-metadata-v1\avd-v1 | 25,016,074,752 | 2,227,612 | 25,018,332,463 |
| 2026-10-29-buffered-restart-v1\avd-v1 | 25,034,162,688 | 2,227,547 | 25,036,420,554 |

Each root contains 39 regular singly linked files: nine exact eligible image
names and 30 records. There are no unknown image names. The metadata-only
inventory passes in 337 ms, checking both root rosters and small bound closure
proofs twice. It reads no image content. The recorded charge also includes the
four external owner proofs; it is larger than the guest-root file sum.

Retiring only the first root is a candidate; keep the newer buffered guest
intact. The remaining recorded charge plus a fresh 40 GiB reservation is
67,986,093,514 bytes, leaving 733,383,222 bytes below 64 GiB **before** the
retired records, evidence and tombstone charges. Even adding this entire
512 MiB packet cap leaves 196,512,310 bytes before any additional retained
charge not covered by that cap. Actual admission must remeasure all required
charges under the current guard. This arithmetic is neither an admission
verdict nor a free-space, peak-use or OS quota guarantee. Root-count limits
also apply; no budget threshold is changed.

## Exact first-root candidate, not an executable plan

The only candidate image paths are beneath the first root's
`content\locallore_receipt_api35_v1.avd\` directory:

| Relative image | Observed bytes |
| --- | ---: |
| cache.img | 69,206,016 |
| cache.img.qcow2 | 197,120 |
| encryptionkey.img | 18,874,368 |
| encryptionkey.img.qcow2 | 2,097,152 |
| sdcard.img | 8,589,934,592 |
| sdcard.img.qcow2 | 589,824 |
| userdata-qemu.img | 12,058,624 |
| userdata-qemu.img.qcow2 | 7,733,116,928 |
| snapshots\default_boot\ram.img | 8,590,000,128 |

This is the exact allowed-name inventory, not a wildcard operation. Image
contents have not been hashed, copied or discarded. Removing these images
would discard that guest's disk/RAM state; records-only preservation would
not restore it. Owner approval for that actual scope is still required.

A separate 78 ms Windows observation finds the first run's recorded worker,
private server, launcher and QEMU PIDs absent. All nine images open
simultaneously for read-only exclusive access, their lengths match, and all
handles close. No bytes are read and no process is stopped. This is a
point-in-time observation of those original identities and files. It does not
prove future closure, identify all possible mappings, prevent a later launch,
or authorize deletion. The historical closure's 15 cleanup flags remain
separate evidence.

## Records preserved before any destructive proposal

All 30 non-image guest files and the **complete** first external owner-run
tree (737 files, including the APK artifact) are preserved outside the guest.
The 767 original/copy/ZIP triples total 98,763,655 bytes per set. Producer
readback passes in 18,156 ms; original hashes and rosters match again after
copying. Original files, both sets of guest images, previous failed captures,
all worktrees, caches and recovery stay in place.

The private recovery root is
`D:\Dev\Recovery\LocalLore\2026-10-30-archive-ui-storage-preflight-v1`.
Its `candidate-v1\retirement-evidence-v1.json` matches the existing 30-file
evidence schema: 9,527 bytes, SHA-256
`18466a7130aa6a6d2963dc8e9e20957be4529342675858865e350715730b9d2b`.
The records ZIP is 47,520,722 bytes, SHA-256
`02fd4fc8d53230242cf565f262907da17fe2a373c68776e904d620a82b1b70a8`.
The producer manifest SHA-256 is
`3b781bfdfc3b06e4af0c639798d1c43b1cde0013a91fd99ce7df45168fc4bf93`.
Full original capture references are preserved locally; private raw diagnostics
and device identifiers are not uploaded. Final ticket handoff supplies
independent readback and source-recovery seals.

The initial metadata phase cap was 64 MiB. After observing the complete
96,536,043-byte owner tree, the disclosed packet cap became 512 MiB, including
one documentation worktree, record copies/ZIP, source recovery and 32 MiB of
late/temp allowance. No model or disk-image copies are included.

## Required implementation before destructive authorization

The existing `plan_retirement` takes the shared lock, hashes all images and
pins its plan into the ledger. Its private `_plan` also hashes image content.
Neither was called for this read-only assessment. `record_retired` validates
an externally completed operation and writes a tombstone; it does not remove
images. The repository deliberately supplies no deletion executor.

The designated Native checkout still contains human uncommitted changes and
an earlier storage implementation (`d452104e`); it is preserved untouched.
Current reviewed source (`b6ad7355`) retains the monotonic closed-charge fix.
Use the reviewed guard for any later lifecycle operation; do not execute the
earlier charge-reset behavior or overwrite the human checkout to reconcile it.

The next runnable implementation is a narrowly scoped, tested executor that
rechecks the exact pinned plan, image identities/hashes, closure, preserved
records and external evidence; prevents concurrent guest dispatch; refuses
links, sharing conflicts, changed evidence and unknown cleanup; and touches
only the reviewed image objects. It must retain the reservation on partial
failure. Tiny synthetic D: fixtures and actual host file-ownership checks can
test that boundary without deleting a real guest. Do not substitute a recursive
shell deletion, lower the budget, or treat this report as an executable plan.

Only after that implementation is concrete and reviewed should the owner be
asked to authorize the exact retirement operation. A fresh guest/run approval
and successful guarded admission remain separate. No phone is used, as
requested; other emulators, system settings and the October 27 records-only
retired roots remain untouched. No merge or release occurs.
