# Guarded preparation recovery verification

Refs #14 (M10.02), B75. Implemented host slice; owner acceptance and actual
recovery remain pending. Full milestone criteria stay unchecked. This packet
adds no gameplay, model, Android permission, dependency or release change.

## Implemented behavior

The [recovery contract](../runtime/android/PREPARE_RECOVERY.md) retains the
same root, active-root count and 40 GiB while linking a one-use recovery history
into ledger version 2. It handles the observed pre-SDK exclusive-mkdir failure,
not arbitrary missing roots or unknown SDK interruption. It never removes an
entry, releases its reservation, deletes evidence or retries automatically.

Ordinary preparation retains its existing parent check and resource floors.
Proposal generation and the admitted SDK body are shared. Recovery adds an
atomic native directory identity fence, a hash-bound operator authorization,
immutable intent/completion/outcome and exact external-history accounting.
Unknown cleanup blocks later retention/closure. Proposed state changes are
validated before ledger replacement. Legacy version 1 remains readable;
actual migration deliberately makes frozen version 1 owners fail closed.

Tested production source checkpoint:
`39389ee66516bd1b5afdbc12bb7446dd5e7daab9`, on
`impl/m10-prepare-recovery-v1`, based on unmerged PR #344
`cc728e020d1d73fee4259de5cac2e96b18502a5f`. Later report changes are documentation
only. No merge occurred.

## Completed host checks

Windows x64 build 26300, CPython 3.14.7. Project commands ran from the physical
D: checkout with process-local `TEMP`, `TMP` and `TMPDIR` set to
`D:/Dev/_Temp`. No Android SDK, production-ledger write or emulator was used
by the test cohorts. Fixtures use isolated D: files and registries. Native
directory tests use real Windows handles; SDK behavior is mocked separately.

| Cohort | Completed result | Unittest time | Raw stderr SHA-256 |
| --- | --- | --- | --- |
| Recovery protocol and native fence | 27 passed, zero failures/errors/skips | 5.259 s | `527daa04c08408c95c1be377333ce1156fa0ceac132048bb9eda45d816e3a21b` |
| Existing environment/storage/ownership/resource checks plus missing-contract-pin regression | 178 passed, zero failures/errors/skips | 20.853 s | `2499860dcc712f66c2ea6f1a8538260ae6f70c3c21d6eb8b97e12bb03d9c6948` |
| Distinct RUN-digest handoff | 1 passed, zero failures/errors/skips | 0.641 s | `89aa767466a590fc2ef4b3d895ca61f613f135f9a1904fa0e38cccfc99e84930` |

Total: **206 completed checks**, comprising 29 new checks and 177 existing
regressions. Counts exclude earlier failed and superseded runs.

The original sixteen independent recovery adversaries were committed as
`d04e361f759ae567c9cf15743df3a92e8af67f80`, integrated as `bee356ec`, and
remained byte-identical through execution. Test SHA-256:
`76c639b131906f201e8de5b85f00b5e8ff376feb8539855cc31ea2a247e14d21`.
They cover snapshot-only planning, insufficient stage proof, stale authority,
entry/evidence/source drift, both parent modes, contention, spent fault points,
guest removal/replay, missing/tampered history, unknown cleanup, exact charge
conservation and deduplicated closed/retired history accounting. A separate
case verifies later RUN digests preserve preparation provenance and that an
invalid reverse transition leaves the prior ledger bytes unchanged.

The native source/test commit was `39c18f00`, integrated as `9f158646`.
Its same eleven test methods cover atomic creation, existing-path refusal,
root/ancestor rename and deletion refusal, child writes and unknown close
outcomes. They establish a host directory fence, not Android qualification.

Actual capture commands:

```powershell
python -I -S -B D:/Dev/Experiments/LocalLore/2026-11-01-prepare-recovery-v1/run-checks-v1.py recovery recovery-v1
python -I -S -B D:/Dev/Experiments/LocalLore/2026-11-01-prepare-recovery-v1/run-checks-v1.py regressions regressions-v3
python -I -S -B D:/Dev/Experiments/LocalLore/2026-11-01-prepare-recovery-v1/run-handoff-v1.py
```

Create-only requests preserve exact unittest argv, source bindings and bounded
deadlines (180/180/60 seconds). Python 3.9 syntax parsing, definitions-only
import and `git diff --check` passed. Source/evidence review independently
matched 28 bindings and all three raw terminals, without rerunning tests.
Review SHA-256:
`d8e03e8550d0948be37b2bbc0f6e0467c9548c7b92a6eee95f39a0b000d87dff`.

## Retained failures and corrections

The first native eleven-method run had one assertion failure and three errors.
Metadata-only handles did not fence directory rename on this host.
`CreateDirectory2W` was exported, but its documented redirect-disallow flag
returned error 87. No flags-zero creation or mkdir/open fallback was accepted.
The corrected implementation uses documented atomic `NtCreateFile`, relative
to a held parent, with directory/list access and no deletion sharing. The
unchanged tests then passed eleven, zero failures/errors/skips, in 0.039 s.
Initial raw stderr SHA-256:
`acd361d0ec2d5bbc2a7ba2fe21d59223952345d63b9818a16701c2ec5a261a30`.
The initial source was reconstructed from the known correction and accepted
only after matching its previously recorded byte hash; it is labeled as such.

The first existing-regression run executed 177 checks with 53 failures and
22 errors. Its old synthetic proposal fixture omitted the newly mandatory
recovery-contract source pin, causing earlier `invalid_proposal` refusals.
The fixture now supplies that dependency, and a new negative test explicitly
requires missing-contract rejection. Existing refusal assertions were retained.
The corrected 178 passed twice; final-source evidence uses only v3 above.
The sixteen recovery tests were first run after integration; no missing-module
failure is presented as an original behavioral FIRST result.

Independent review also prompted external-history charging, proposed-state
validation, fresh authorization binding, actual installed-digest outcome
recording and the separate RUN handoff regression. Original B73/B74 failed
evidence, operator observations, favorable and corrective reviews remain intact.

## Actual charged-attempt inspection

The real B73 entry was inspected only through the file-only planner, without
creating authorization or executing recovery. The 2,588-byte snapshot plan
SHA-256 is
`3323eff386566311cd3c896f6a9d9638a7ddaf46778b3763d72be4a775e0df7e`.
It records `create_one` for the still-missing parent and explicitly labels the
original evidence as an operator-observed mkdir failure, not process closure.
No fresh prepare proposal or current resource/process observation was fabricated.

The 41,230-byte live ledger had the same SHA-256 before and after inspection:
`4917ec696f7c9f9de5917838aafbd9c2d11184e17c8cbecd71f4eb66ae6a58c5`.
The original 42,949,672,960-byte reservation remains `preparing`. No parent or
guest root was created; no SDK, ADB, emulator, model or phone operation occurred.
The other emulator, shared service, older model guest and system settings were
not changed. Local outputs and selected recovery have a 32 MiB retention budget.
Private raw records and credentials are not repository payloads.

## Remaining gates and next operation

Live ledger-v2 migration and SDK preparation are **unexecuted**. Actual
execution requires a dedicated preserved reviewed checkout, unchanged bound
evidence, exact operator authorization accepting the evidence type, fresh
resource/admission checks and known native/SDK cleanup. The inspection snapshot
from a development checkout is not permission to apply migration or replay the
spent SDK14 grant.

After recovery, a separate current-source owner/admission handoff must support
ledger v2 before any boot. PR #338's frozen v1 activation recipe remains
unchanged and cannot be reused as-is. All nineteen SDK14 Android UI methods
remain **unrun**. Phone/ARM64, real inference, visual/accessibility, causal
process-death and release qualification remain separate. No task is marked
owner-accepted, and no merge or release is included.
