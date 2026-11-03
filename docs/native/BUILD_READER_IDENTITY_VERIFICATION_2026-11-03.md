# Readiness guard verification — 2026-11-03

Refs M10.02 `RECORD_CANCELLATION_UI_OPERATION_READINESS`, supporting M09.04/M09.06.
Two guard fixes are implemented for review. Full task checkboxes remain unchanged.

Code `a1dd3d9ef172633f293e3594360a305198fd8186`, tested tree
`8124a1848dfeb46c5ff529122c7f5041a4b29de0`, on open/unmerged #389 at
`c5fcb827ac6400781d80e50e8ee32b7110f1dedd`. The source map contains 2,661 files:
2,659 inherited entries with only two production files changed, plus two original
test files. The four changed paths are explicitly staged through an alternate
index; the normal checkout and index remain preserved. Documentation is later.

## Actual Windows checks

Python 3.14, physical D: source/output directories, process-local TEMP/TMP on
`D:/Dev/_Temp`, bytecode disabled. Each worker is frozen before launch under the
unchanged checked 180-second host owner. The metadata driver denies SDK/process/
socket dispatch and restricts writes to owned scratch/captures. External SDK/
admission observations are fake in the synthetic port tests. The separate real
artifact verifier receives no alternate reader factory.

| Cohort | Methods | Actual result | Owner seconds |
| --- | ---: | --- | ---: |
| Original late-ledger FIRST | 2 | 1 pass, 1 assertion failure | 13.079 |
| Original reader FIRST (oracle v2) | 4 | 3 pass, 1 positive-path BuildRefused error | 1.137 |
| New corrected tests | 6 | 0 failures/errors/skips | 1.386 |
| Final metadata including unchanged parent regressions | 66 | 0 failures/errors/skips | 17.138 |
| Existing diagnostic/record build regressions | 35 | 0 failures/errors/skips | 36.518 |

**101 unique final method IDs** are the disjoint union of the final 66 and build
35. The six-method repeat and subtest variants are not additive. The 35 build
methods use retained synthetic data; they do not rerun Android or JVM tests.
No full-project or CI pass is claimed. Windows reader tests are NT-only; this
actual cohort has zero skips, not a Linux qualification claim.

Both original failures remain failures. The late-ledger oracle changed only its
isolated fixture ledger during the final activation observation and detected
that no refusal occurred. The reader positive oracle varies only a directory's
observed size across actual reads/final checks; it encountered the same existing
BuildRefused path. The three strict reader protection methods already pass before
the production change. The exact six test bodies are unchanged through final.

Reader tests keep the real shared bound-file reads/open/fstat/hash behavior.
They reject changed device, inode, mode/type, mtime and link count; link/reparse
observations refuse through the direct reader's finite existing error family.
Only those two link variants additionally accept EnvironmentRefused, because the
shared path guard may refuse before the stamp. Regular-file size stays strict;
a same-size byte rewrite with restored mtime still fails the final real hash.
An earlier unexecuted proposal with too narrow exception expectations is retained;
it is not a product RED. A separate unrun generation-test draft is also retained.

## Actual read-only artifact verification

Two attempted fixed inspections against the old frozen profile stop with known
cleanup, exit 1, at 5.242s and 5.757s owner. Both stop before output/planning.
The second worker adds an observational exception trace, without replacing or
altering the reader. At its refusal the report-directory size is 0 then 20,480;
device, inode, full mode, mtime and link count match. Both raw errors, workers and
exact attempted source remain preserved. No third old-profile retry occurred.

After the fix, the **public current-source** `verify_frozen_product` succeeds in
11.598s owner with known cleanup. It uses the actual corrected shared reader,
the sealed baseline and original saved descriptor; no factory seam is supplied.
The returned manifest is value-equal to the original 32,140-byte descriptor, SHA256
`4d39b74ad5aee455ce9060c01d760204022101e4b6b8ce58d12f666450d2894e`.
Source maps before/after match all 2,661 files and both final test cohorts.
This revalidates saved build/APK facts, not original JVM execution or Android.
No APK rebuild, selector/profile change, new model/runtime choice or feature
acceptance follows. Shared ledger stays
`c0d39a503e7ce86607215a33bdad84c0d6b9769cc762234a17105c69eb4d0673`.

Private frozen commands include `run_owned.py red-late-v1`, `red-reader-v1`,
`new-v1`, `final-v1`, `build-v1`, `run_inspection.py`,
`run_inspection_diagnostic.py`, `run_real_attestation.py` and `commit_code.py`.
All run from physical D: with the stated environment. The six new tests can be
reproduced from a physical D: checkout with process-local TEMP/TMP on D: using:

```
python -B -m unittest scripts.tests.test_record_cancellation_readiness_inspection scripts.tests.test_build_reader_directory_identity
```

## Review, preservation and limits

B72 authors the narrow shared-reader proposal; Root authors the late observation
check and integrates. B75 authors all six new oracles and independently reviews
production; B72 independently reviews Root's change and oracle quality. Nobody
receives independent-review credit for their own authored artifact. Final
source/evidence, documentation, publication and archive readback are separate
seals referenced from ticket handoff, not owner acceptance.

Originals are under `D:/Dev/Experiments/LocalLore/2026-11-03-record-cancellation-readiness-v1`;
recovery uses the matching basename under `D:/Dev/Recovery/LocalLore`.
The combined ordinary source/control/synthetic/recovery budget is 256 MiB.
Retain actual failed sources/logs/workers, unrun drafts, maps and synthetic data.
No preserved guest/evidence/model data is removed and no private raw diagnostics,
credentials, weights or player content are uploaded.

The managed worktree tool refused the physical repository outside chat roots.
The candidate is therefore verified from raw Git blobs, while independent agents
use their existing separate preserved worktrees and Root alone integrates. No
checkout/reset, ignored-data cleanup or manual worktree replacement occurred.
Normal HEAD `8924278c` and index SHA `897c9182...` are checked separately.
Remote main movement by other actors is recorded as a snapshot, not our merge.

**SDK18 Android 0/5.** No operational authority, refreshed input qualification,
preparation, boot, SDK/ADB/model/phone/service action, shared operational ledger/lock/admission write,
retirement, settings change or other-emulator stop occurred here. Tests create
and mutate isolated toy ledgers and authorization/admission records. The prior
retirement is separate and its grant is spent. The next source-coherent profile
integration is runnable host work; exact preparation/run approval remains a
separate gate after working current inputs and a reviewed concrete proposal.
