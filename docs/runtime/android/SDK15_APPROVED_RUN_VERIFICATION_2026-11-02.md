# One guarded SDK15 recovery and Android UI run

B91; refs #14 (M10.02), supporting #13 (M09.06). Verified implementation/evidence
is in review; full criteria remain unchecked. No merge or feature acceptance.

The owner explicitly approved the exact PR #354 proposal on 2026-11-02. The
frozen operator ran **once**, exited zero, recovered the charged preparation and
completed **4/4 model-free LibraryActionScope UI tests** on the approved API35
Google APIs / x86_64 emulator configuration (8 GiB RAM, four cores).
The one-run grant is spent. No second boot or image retirement is authorized.

[Sanitized result artifact](../../../benchmarks/results/sdk15-approved-ui-run-2026-11-02.json)
contains exact method names, command timings, source/APK/JUnit hashes and limits.
Private raw logs, process identities, credentials and images are not published.

## Exact frozen scope and results

Operator checkout `D:/Worktrees/LocalLore-record-query2-tests-v1` remained clean
at `b6cda49410bdf4aaa067a15ce165f64c793fbe53`. Operational checkout
`D:/Worktrees/locallore-record-actions-tests-v1` remained clean at
`18809566af72530408e2e25007ee4d501e6bf12a`. Product is PR #351,
`7ab4918fa1044d960edcb1172fe7684474eb3a89`. The later B90 cleanup fix in PR #361
was not substituted into this authorized operation.

Original product/test APK SHA256 values remain
`3c355ec7568e8a6468790c417d986d413f5414f43cde2719f77a9041ea15abb6`
and `5a96cfd007e42a5eb7e739375316c2ba43263490c2cca784b35d91b83712b698`.
The real B81 build role, source25/server10 closure, Python executable/runtime-DLL,
installed tool, failure-observation and immutable recovery-plan pins passed.
The approved proposal stayed 7,398 bytes / SHA256
`62901283bbf781efd8c47a7f0923e218652abd8b9130b269a5f83956b6fcb190`.

All methods are in `org.locallore.app.ui.LibraryActionScopeScreenTest`:

| Method | Original JUnit / shell exit | Recorded command time |
| --- | --- | ---: |
| oldRecoverCannotBorrowAnEqualFailedRetryAndFreshUnselectedRecoveryWorks | PASS / 0 | 7.783 s |
| oldStoryRowsAndOpenerCannotActOnReopenedOrEqualRefreshedLibrary | PASS / 0 | 8.205 s |
| oldTimelineRowCannotActOnReopenedMenuAndFreshChoiceWorks | PASS / 0 | 8.033 s |
| disposedScreenRowCannotBorrowSameViewModelAfterRemount | PASS / 0 | 7.984 s |

Read-only replay revalidated the original JUnit start/pass/final records,
four ordered one-use claims and all **29** finite client operations, including
binary staging, device hashes/install and unchanged package/UID/path/hash
checks before and after. Exit zero alone was not treated as JUnit evidence.

Reported whole-operation time was **605.957 s**, activation **437.761 s** and
controller **304.662 s**. These are development-harness timings, not inference
benchmarks. Whole-operation 2,400-second and guest 1,800-second ceilings stayed
unchanged. Preflight observed 28.38 GiB available physical memory; CPU, drive,
commit and private-port gates passed without threshold or system-setting changes.

The operation and activation results passed their original complete replay,
source/capture/caller/worker/stop/history/storage joins. Independent read-only
OS checks found all **nine named original owned process identities absent**
after the command exited. No verifier restarted a guest, ADB service or test.

## Ledger, images and retained evidence

The guarded operation migrated the shared ledger from v1 to v2, preserving the
old fields/history and original 40 GiB charge through preparation. The original
error-3 pre-SDK mkdir observation remains eligibility evidence accepted by this
grant; it was not relabeled as native process-closure proof.

Only normal qualified RUN closure then changed this same guest to `closed`,
with **18,957,702,908 bytes (17.66 GiB)** measured retained charge. Final ledger
is 42,221 bytes / SHA256
`84ad23a43f6c4abd6be82164fcec2e4e7b51277f1e250a507af22654be1a7294`.
Guest path remains
`D:/Dev/Experiments/LocalLore/2026-11-01-record-controls-ui-v1/avd-v1`.
Its disk/app/cache/RAM image state remains in place; stopping did not delete it.

Private operation root is
`D:/Dev/Experiments/LocalLore/2026-11-02-library-recovery-operator-v1`.
Runtime is `D:/Dev/Experiments/LocalLore/2026-11-02-current-library-ui-run-v1`.
The selected records-only backup at
`D:/Dev/Recovery/LocalLore/2026-11-02-library-recovery-operator-v1/approved-run-v1`
contains **353 original/copy pairs, 39,063,400 copied bytes**. Receipt is
21,447 bytes / SHA256
`dffeed884bc216c7bcd37f410abd05c32fa0e7debb8a5518c6f74c12c2e67201`;
decoded JSON is 182,024 bytes / SHA256
`31df8b1155c399ff84f8da1149cd5fd2104750c1f27c9967d1d71bcda6416db2`.
Initial selected backup totals 39,085,039 bytes, below 128 MiB; later small review
and report files are separately retained. No model, key or image bytes were
copied. Metadata backup cannot restore deleted guest images.

The independent raw-JUnit/public-record audit checked all four methods,
29 operation vectors and 257 file bindings, including 58 proofs and 58 query
bundles. Its record is 16,636 bytes / SHA256
`a773d1ec219ba7334144867c3102a51d4280cdd4593776148e73cd763b25e38b`.
It did not rerun tests or independently repeat OS stop checks. An additional
coordinator reader initially supplied an unsupported redundant JUnit keyword
after complete controller replay; its TypeError/helper were retained. The
corrected read-only verification passed. This was not an Android failure/retry.

The B90 host-test boundary snapshot at 16:50:04.370247Z predates this separate
authorized operation. Its old-ledger/absent-authority claims were valid then;
the later authorized v2 transition does not invalidate that historical snapshot.

## Limits and next task

This is the original ordinary-app/fake-provider SDK15 four-method cohort, not
the four SDK16 Knowledge journeys. Those remain unrun. No model import or
inference, physical phone/ARM64, TalkBack, complete story journey, sustained
performance, thermal, battery or network-traffic qualification occurred.
The frozen code did not record its native job-handle `CloseHandle` BOOL; later
read-only PID absence does not retroactively add that missing return evidence.
PR #361's stronger host cleanup checks are separate.

The other emulator, shared ADB, older model guest and system settings were not
targeted. No model copy, image deletion/reset/compaction/relocation, release,
repository administration or merge occurred. Full M10.02/M09.06 acceptance
remains open and `feature_acceptance` remains false.

There are now two unretired closed roots with 43,994,123,462 total charged bytes.
The SDK16 v1 guest path has been used by this SDK15 run; it cannot silently
inherit this spent grant or be adopted/reset for another boot. Next runnable
work is a reviewed SDK16 fresh-path/capacity proposal under the same two-root /
64 GiB policy. Any retirement and new boot require applicable exact approval;
preserve the older model guest and all current images/records meanwhile.
