# SDK16 fresh guest and read-only capacity verification

2026-11-02. B92; Refs #14 (M10.02), supporting #13 (M09.06).
Supporting implementation is in review, not accepted milestone completion.
This packet stacks on unmerged PR #361 at `096c517857c95fc854154bbf60d46cb85b6d6d74`.

## Result and source

The SDK16 profile now admits exactly the fresh November 2 Knowledge guest and
rejects the used November 1 SDK15 guest before build freshness, owner construction
or worker dispatch. SDK14/SDK15 and the frozen product/APKs are unchanged.
The new `receipt_avd_storage.preview_prepare` reads the authoritative ledger and
current charges without writing, reserving, creating a registry/root/lock or
granting execution. See [the contract](KNOWLEDGE_FRESH_CAPACITY_V1.md).

Initial implementation `bfb070d501f6549566d94c4922d1dc7859502250` passed the new
12 methods and 44 storage regressions. The final executable/test source is
`eda2e7acc13acb40ea88bca2b8d5eb5a496b42c8`. Its only change after the initial
implementation is four lines of synthetic fixture setup across three test files.
The production preview/contract and both independent test files are byte-identical
between these heads. Subsequent README/report changes are documentation only.

No new dependency, SDK, model, runtime version or license is introduced. Actual
host interpreter: installed Windows CPython 3.14.7; Python 3.9 syntax for the storage
module is also parsed by the tests. No Android/native rebuild or CI pass is claimed.

## Executed checks

All commands ran from physical
`D:/Worktrees/LocalLore-original-input-compose-review-v1` with process-local
`TEMP`, `TMP`, `TMPDIR` set to `D:/Dev/_Temp` and Python `-I -S -B`.
The retained `run-checks-entry-v1.py` inserts only this fixed checkout and loads:

```text
python -B -m unittest scripts.tests.test_prepare_capacity_preview scripts.tests.test_knowledge_ui_fresh_root -v
python -B -m unittest scripts.tests.test_receipt_avd_storage scripts.tests.test_owned_target_storage -v
python -B -m unittest scripts.tests.test_knowledge_ui_profile scripts.tests.test_knowledge_ui_controller scripts.tests.test_knowledge_ui_activation -v
```

Those are the exact unittest rosters, not a claim that the shell forms above were
separate additional runs. Actual dispatch was `python -I -S -B <OUT>/run-host-v1.py
<mode> <phase>`; `new-v3` uses the corrected `run-host-v2.py`. OUT is
`D:/Dev/Experiments/LocalLore/2026-11-02-knowledge-fresh-capacity-v1`.
Each dispatched phase has original binary captures, command/start/terminal
identities, requests, equal before/after source maps and known host-owner closure.

| Phase | Source | Actual result | Entry / owned worker seconds |
|---|---|---|---|
| new-v1 | bfb070d5 | 12 pass, 0 failures/errors/skips | 1.281 / 3.058 |
| storage-v1 | bfb070d5 | 44 pass, 0 failures/errors/skips | 4.193 / 6.036 |
| reuse-v1 | bfb070d5 | Genuine frozen B88 manifest/APKs verify | 16.525 / 18.369 |
| profile-v1 | bfb070d5 | 39 ran; 0 failures, 2 errors, 0 skips | 214.194 / 216.021 |
| new-v3 | eda2e7ac | Same 12 pass, 0 failures/errors/skips | 1.390 / 3.205 |
| profile-v2 | eda2e7ac | 39 pass, 0 failures/errors/skips | 129.484 / 131.237 |

Final passing coverage is **95 unique methods**, not 107 after counting the
12-method repeat again. Storage/build checks retain their bfb source attribution;
their production inputs did not change in eda. Timings measure host entry and
supervised worker, not model/phone performance or archive/preservation overhead.
The 900-second worker ceiling is unchanged and excludes that metadata overhead.

The original independent tests cover exact count/byte boundaries, monotonically
retained closed charges, fresh file growth, retired evidence charging, no retired
reuse, missing/locked/corrupt/orphaned recovery inputs, stale closure/proofs,
detected ledger/lock/root/proof changes, path/parent/ancestry rejection and no
mutator/process/socket work or import-time I/O. Semantic cases use real shared storage
validation on tiny retained synthetic ledgers; historical byte floors do not
allocate GiB files. SDK16 cases also require early rejection of the old literal.

The profile cohort exercises four ordered one-use claims and complete 29-client
synthetic replay, malformed/late/missing JUnit or exit records, cancellation,
unknown cleanup, source drift and joined caller/owner closure. Native/transport/
build boundaries in those fixtures remain simulated. All four real Knowledge
Android journeys remain **0/4 unrun**.

Frozen artifact replay verifies the unchanged 8,656-byte manifest
`97037d90a3b738a09054a07d03caf659cb2276774935d0b46535712b31d6f55c`,
28,398,622-byte product APK
`0b93c6af0772ff6216a0dcbeb2f8b19b1564129f3855336ced7dcafbfca662cd`,
and 2,645,072-byte test APK
`3241aaff3c42fc6c155f04da40cae88aa54e39cd68c10f7cb5178a0b77a9c5db`.
No new product, APK or ARM64 execution is credited.

## Actual file-only capacity observation

The fixed SDK16 parent and guest are absent. Calling the real preview for that
fixed path refuses `missing_path`; neither is created. A distinct representative
absent candidate beneath OUT supplies only shared accounting facts:

| Observation | Value |
|---|---:|
| Unretired roots / maximum | 2 / 2 |
| Current remeasured charge, including retained evidence | 44,012,146,871 bytes |
| Additional preparing/live reservation | 42,949,672,960 bytes |
| Projected charge / budget | 86,961,819,831 / 68,719,476,736 bytes |
| Root limit / byte limit exceeded | true / true |
| would_fit / admission_granted | false / false |

This is not a successful fixed-target preview or admission. Current charge can
exceed earlier recorded floors; no capacity is released by observing it. The
42,221-byte production ledger remained byte-identical, SHA256
`84ad23a43f6c4abd6be82164fcec2e4e7b51277f1e250a507af22654be1a7294`.
The exact read-only helper/result and original ledger copy are retained locally.
No resource, port or native process check was substituted for this file-only claim.

## Preserved failures and corrections

Two original coordinator-authored baseline scope tests each produced an actual
AssertionFailure: SDK16 equaled SDK15's used root, and SDK16 accepted that old root.
These are distinct from the independent 12 passing methods and from device tests.

`profile-v1` remains failed. The old SDK15-positive fixture inherited the new
SDK16 root while retagging only protocol/sources, so the unchanged SDK15 validator
correctly refused `path`. The correction explicitly supplies SDK15's old root;
all existing assertions remain. The second error was `fixture_budget_refused`
after earlier retained SDK16 cases filled its 128 MiB own-tree limit. Only test
fixtures move to this packet's declared sdk16 subtree, with controller/activation
children derived from one root. Existing 128/256 MiB inner limits stay unchanged,
and this packet's tighter 64 MiB aggregate generated limit includes the failed
old-tree additions plus all new packet fixtures. No evidence was removed.

Two coordinator-only refusals occurred before test dispatch: an initial wrapper
IndentationError and `new-v2` BadZipFile when parallel phases read a shared archive
before its writer finished. Their helpers, observations and partial metadata
remain. v2 stages a complete Python archive in its unique phase directory and
atomically publishes it; a losing complete pending file is retained. No running
v1 helper was edited, and no product code changed for these coordinator fixes.
`new-v2` has no request/child/test record and is not another failing product run.

## Preservation and review

Root verified all **5,463 original/copy pairs**, 67,640,034 copied bytes, and all
**28,298 pre-existing fixture files**, 183,197,994 bytes, unchanged. The latter
were rehashed in place, not copied again. Six closed phases cover full tracked
source maps of 2,698 files. Three archives cover **Python sources only**:
468 members each, 1,404 member-byte checks total. They are not full-tree archives.

The canonical receipt is 224,764 compressed bytes, SHA256
`c23d3a8e8c72e0e7306eb2008d7fc031104e69f9dc50d007edb56d1f6d764dc3`;
decoded 2,656,657 bytes, SHA256
`f92e79c32e4b97ec4000c4c781e84b2eb177e8c65df73e96fda4399bc90cb340`.
Records-only recovery is under matching
`D:/Dev/Recovery/LocalLore/2026-11-02-knowledge-fresh-capacity-v1`.
Initial copied payload plus receipt is 67,864,798 bytes; summary, later reviews
and publication copies are additive and separately verified.

Before further test dispatch, the 16 MiB controls estimate was refined to 32 MiB
because the conservative baseline metadata alone is 7,414,139 bytes. Before the
first recovery copy, its 64 MiB estimate was refined to 80 MiB because combined
retained generated outputs and controls already exceeded 64 MiB. Generated
outputs remain capped at 64 MiB; no emulator/accounting/test guard was enlarged.
Final phase observations are 47,532,146 generated bytes and 20,093,877 control
bytes. These are selected retained outputs, not a whole-host high-water,
temporary-file ownership, disk quota or complete TEMP/cache accounting claim.

Independent design/source review verified the preview equals its reviewed
proposal and every pre-existing storage AST is unchanged after removing only
that function. Separate refinement review found all assertion and budget-check
ASTs unchanged. The 9+3 independent test files are byte-identical to their
original proposals. Review is evidence, not human acceptance. Private raw
captures, process identities and ledger history stay local; source/tests and
sanitized reports are published. No real guest images, model
weights or credentials were copied; tiny synthetic fixture bytes are included.

## Remaining gate and next task

M10.02 supporting implementation is in review; full M10.02/M09.06 criteria remain
unchecked. The old SDK15 grant is spent. Prepare an exact evidence-preserving
capacity/retirement disposition and fresh SDK16 run-input proposal through the
reviewed current tooling. Any actual retirement, SDK preparation or
boot must have its applicable exact authorization and fresh admission; this
packet supplies none. Do not adopt/reset the SDK15 guest or replace its images.

No emulator/ADB lifecycle, phone/model operation, system setting change,
unrelated-emulator stop, shared-ledger mutation, real guest-image deletion, private upload, release
or merge occurred. Physical-device/model/ARM64, real Android rendering/TalkBack,
full journeys and release acceptance remain separate open gates. Tests do mutate
their tiny isolated ledgers, and existing storage fixtures clean up their own
synthetic files; those operations do not touch the protected shared ledger or
real guest images.
