# Preparation parent preflight

Refs #14 (M10.02). B73 runtime evidence and B74 host fix are separate packets.

## Observed runtime failure

The owner authorized SDK14's exact nine-image retirement and one fixed fresh
API 35 guest, with 8 GiB RAM, four cores, a 40 GiB reservation, a 30-minute
maximum and nineteen model-free UI methods. The frozen source was PR #338,
`2b7aa56b303794c126cb9620ceb5090587e70708`; its PR #337 APK pair was unchanged.

The reviewed retirement executor completed: nine attempted, nine marked,
`cleanup_known=true` and `retirement_recorded=true`. It removed only the
authorized 18,959,696,384 logical bytes. Records and recovery were retained;
they cannot restore those guest images. Retirement result SHA-256:
`ad7acfbd53361b45f77b741ea47a2efa1cf27a04b15311884f22daaf93988be4`.

The subsequent preparation failed with `FileNotFoundError`, Windows error 3,
at `receipt_avd_environment.prepare`'s `root.mkdir()`. The approved guest's
parent directory was absent. The public guard had already recorded a
42,949,672,960-byte `preparing` reservation. Root creation preceded the SDK
worker and failed outside preparation's result-recording block. There was no
guest root, preparation result, boot, private ADB service, APK installation or
UI method from this invocation. All nineteen methods remain **unrun**.

The coordinator and independent preparation review both missed this parent
precondition. The initial operator and favorable review remain unchanged,
alongside a corrective failure review. The retrospective failure record is
explicitly labeled as an observation from the execution tool, rather than a
raw process capture. Source ordering and the exception establish that this
invocation did not dispatch the SDK worker; no global process roster was used.

No parent creation, retry, substitute guest, ledger edit, release of the
reservation, admission-builder execution or further activation followed.
The older model guest, other emulator, shared ADB service and system settings
were preserved. No model operation or merge occurred.

Private local preservation at
`D:/Dev/Recovery/LocalLore/2026-11-01-record-controls-ui-attempt-v1`
contains 39 verified original/copy pairs totaling 306,933 bytes, including
the ledger snapshot. Its preservation receipt SHA-256 is
`09407e75c25007310344c3ea6154e0227c066ebdad87ced3b99b4bbb792b4a78`.
These private records are not repository payloads or authorization to resume.
An independent file-only reader verified all 39 copies and their nonledger
originals; the ledger also matched its snapshot at that observation. Its review
SHA-256 is `2b3703e5773e069cf0167988cf32683353a9b13c43b0d50b13cfccf820917acf`.

## Narrow host correction

Planning and authoritative preparation require an existing ordinary parent
directory. The existing path validator rejects file, symlink and Windows
reparse-point parents and checks their ancestors. Planning checks before
installed SDK or protected metadata is inspected. Preparation checks again
before resource observation, storage reservation, root creation or SDK work.
The tool does not create missing parent directories.

This preflight does not eliminate concurrent parent removal or permission
changes after validation. Failures after successful reservation remain
charged; no implicit cancellation, closure, repair or ledger release is added.
The frozen SDK14 source, recipe and approval are not rewritten by the fix.

## Verification and remaining gates

Independent tests were committed as `18ad98e44f975c9a9470b6438da99087b927469c`
and integrated unchanged as `cba69836`. All nine test methods have SHA-256
`7968ce3ce2fdb00df2444cacad3bd242c9c4878cc2cb765407dc55d1fe47de34`.
On unchanged `2b7aa56b`, FIRST recorded **five assertion failures and four
passing controls, with zero errors/skips**, joined in 465 ms. The failures
observed metadata access or reservation before invalid-parent refusal; this
was not an import/setup failure. Raw stderr SHA-256:
`c9a5051536d089b4dff2d0a509384a3719333d72e7e0981fe2363e2030916c5a`.

After the three-line correction, two separate host cohorts passed:

| Cohort | Result | Unittest time | Raw stderr SHA-256 |
| --- | --- | --- | --- |
| Parent, environment, storage, retirement and host commit capacity | 218 passed, zero failures/errors/skips | 52.880 s | `92bda5f4176631a8e9651ddc7c85b6e50b38686c75ee00dfef0d79b0f919dd8e` |
| SDK14 activation fault graph | 11 passed, zero failures/errors/skips | 31.925 s | `27638043f5506cc4968aa70fa3cf990d97d3ad4d9bda9c7d0a55a8113dc8c71a` |

The 229 total comprises nine original regressions and 220 existing checks.
The original test bytes were identical for FIRST and both completed cohorts.
The tested environment source was 46,770 bytes, SHA-256
`102ce63378d5468e2a0a311ad5cd073ae643b4db990c42e37f145972c1f860b1`.
Independent source/test review found no actionable issue; review SHA-256
`e2b83a64198444210b65566e636dce3e4b5469dc3d7bfc6246729aa5ae314a8e`.
That review did not independently rerun the tests.

An earlier combined fifteen-module host attempt exceeded its 180-second
limit inside a slow SDK14 controller fixture. Its partial stdout/stderr and
retrospective timeout record remain retained and **are excluded from completed
cohort totals**. No combined-suite pass is claimed. The completed preparation/
storage and activation cohorts used separate 180/300-second bounds and fresh
output directories. Other SDK14 fixture suites were not repeated to completion
in this packet.

Actual capture commands, run from the physical D: source checkout with
`TEMP`, `TMP` and `TMPDIR` set process-locally to `D:/Dev/_Temp`, were:

```powershell
python -I -S -B D:/Dev/Experiments/LocalLore/2026-11-01-prepare-parent-preflight-v1/run-host-cohorts-v2.py parent-storage
python -I -S -B D:/Dev/Experiments/LocalLore/2026-11-01-prepare-parent-preflight-v1/run-host-cohorts-v2.py activation
```

The create-only request records contain exact unittest argv, module roster,
source bindings and Python version (Windows x64 CPython 3.14.7). Tests and raw
results are under the same D: experiment root, within a 16 MiB evidence budget.
These checks use synthetic paths and mocked resource, storage and SDK
boundaries. They execute no Android SDK, production-ledger operation or emulator.
`git diff --check` also passed. No APK rebuild or real runtime test was repeated.

The real SDK14 cohort remains blocked. Before any later runtime attempt,
review an explicit recovery disposition for the charged, root-absent
preparation and prepare matching execution authority. A source fix cannot
retroactively qualify this run or release its reservation. Physical-device,
ARM64, real-model, visual, accessibility and release gates remain separate.
