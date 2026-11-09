# SDK16 Knowledge profile: host verification

B89. Refs #14 (M10.02), supporting #13 (M09.04/M09.05/M09.06).
Implementation is in review; full tasks remain unchecked. No owner acceptance,
merge, Android execution or feature acceptance follows from these host checks.

## Scope and fixed inputs

The [FIRST contract](KNOWLEDGE_UI_PROFILE_V1.md) was committed at `23a844b3`
before implementation. This packet stacks on unmerged PR #359 (`a04a9711`),
using its unchanged B88 attestor/baseline and separately frozen PR #358 product
`286c0905613e9bbff2d69796155105339000eceb` at
`D:/Worktrees/LocalLore-record-query2-fixtures-v1`.

Seven new modules provide the fixed SDK16 contract, concrete owner/client,
shared proof replay adapter, build adapter, controller and activation. There are
28 mandatory source names (plus optional package initializer), including the
current recovery guard and both build readers/baselines. The shared library
baseline is conservatively pinned; this grants no SDK15 selector authority.
No existing guard/profile, gameplay code, dependency or build bytes changed.

`knowledge_ui_profile_build.verify_current` validates and revalidates SDK16
inputs around the unchanged B88 verifier, checks its exact four ordered
instrumentations, then returns the raw manifest object unchanged. Only the
controller privately projects verified package/certificate/artifact fields.
No manifest conversion, publication or second gameplay authority is added.

APK pair retained from B88:

- Product: 28,398,622 bytes, SHA256
  `0b93c6af0772ff6216a0dcbeb2f8b19b1564129f3855336ced7dcafbfca662cd`.
- Test: 2,645,072 bytes, SHA256
  `3241aaff3c42fc6c155f04da40cae88aa54e39cd68c10f7cb5178a0b77a9c5db`.

Four fixed Knowledge selectors, three artifact roles, no model, no retries,
unchanged deadlines, binary-safe staging, before/after package checks and exact
original JUnit/shell-exit evidence are required. One boot poll produces exactly
29 consumed client records and four one-use method claims. Import performs no
I/O. Activation creates no preparation, input, admission or authorization.

## Actually executed

Root writer: `D:/Worktrees/LocalLore-original-input-compose-review-v1`, branch
`impl/m10-knowledge-ui-profile-v1`. Python 3.14.7, installed tools preserved;
process `TEMP`/`TMP`/`TMPDIR=D:/Dev/_Temp`, offline D: caches. No APK rebuild.
Capture root (`OUT`):
`D:/Dev/Experiments/LocalLore/2026-11-02-knowledge-ui-profile-v1`.

Exact local commands, using the preserved/pinned host helper:

```powershell
python -I -S -B "$OUT/run-host-v1.py" build build-v1
python -I -S -B "$OUT/run-host-v1.py" new unit-v1
python -I -S -B "$OUT/run-host-v1.py" existing regression-v1
python -I -S -B "$OUT/run-host-v1.py" new unit-v2
```

Each command used the installed Python executable explicitly. The helper pins
the separate test entry, waits for the actual child identity and stdin barrier,
uses the unchanged Windows job supervisor, captures both pipes as bytes, and
compares complete raw source maps/archive members before and after. Its 900-second
limit covers supervised work; source/archive/meter/preservation operations are
outside that timer. The two test cohorts overlapped after their shared source
archive had completed; this is not a general archive-publication race guarantee.

| Phase / source | Actual result | Test/operation time | Owned-job time |
| --- | --- | ---: | ---: |
| build-v1 / f14bff0d | Real B88 create + verify, exact existing manifest/APKs: PASS | 2.501 s | 4.150 s |
| unit-v1 / 9ba5a5e9 | 39 methods, 0 failures / **1 error** / 0 skips | 130.399 s | 132.319 s |
| regression-v1 / 9ba5a5e9 | 97 methods, 0 failures/errors/skips: PASS | 156.235 s | 158.216 s |
| unit-v2 / 30563740 | 39 methods, 0 failures/errors/skips: PASS | 146.892 s | 148.824 s |

Final executable/test source is
`30563740a33673c825144b933c71842287673ac5`. Later report-only changes do not
relabel an untested implementation. Source counts are 2,687 for build-v1 and
2,691 for all test phases; every phase has identical before/after raw maps.
Three complete source archives retain 8,069 unique-per-archive entries.

The first error was an independent test expecting `TargetRefused` when concrete
owner substitution correctly raised `OwnerRefused('owner_type')`. Only the two
owner/worker expectations changed to exact `OwnerRefused` plus anchored reason.
The initial raw/proposal/archive remain intact; the rest of that failed method
was unexecuted then. Unit-v2 establishes all its subclass and no-dispatch checks.
No production change or broader exception allowance was needed.

New tests cover exact source/selector authority, subclass refusal, wrapper
return identity/order, raw-manifest projection, complete 29-client/four-claim
replay, missing/reordered/borrowed/boolean records, truncated binary input,
counterfeit JUnit/late failure/missing exit, stale sources, first-instrument
cancellation, unknown caller/cleanup, stop-once and independent cleanup tails.
The existing regression cohort covers SDK15 profile/controller/activation and
the shared target contract. Test payload files are synthetic, not APKs.

The added metadata oracle exercises real `env.authorize`: a structurally valid
current-path proposal passes, while old SDK15 source paths refuse before a
second authorization read or installation/external observation. Token lookup
is mocked; no authority file is published. Fixed activation authorizes before
live dispatch. The raw shared owner instead authorizes its guest after private
ADB setup, before guest claim/boot; no earlier refusal claim applies to that CLI.

## Preservation and independent review

Before reuse, B88 preservation matched 341 current source/control pairs,
145 current artifact joins and 74 historical retained copies. B89's create-only
snapshot retains all selected closed captures, helpers, original proposals,
three source archives and both complete host fixture trees: **13,101 pairs,
160,401,332 copied bytes**. Receipt is 9,024,483 bytes, SHA256
`8769f35b1e9002a1a8f3de2019428e35ece4be919909f49bc419a0517999f866`.
Its canonical copy matches under
`D:/Dev/Recovery/LocalLore/2026-11-02-knowledge-ui-profile-v1` (169,425,815 bytes
including receipt, below 192 MiB). Subsequent review artifacts are separately
mirrored; they are not retrospectively inserted into this sealed snapshot.

Root integrated proposal-only work from `/root/b72_branch_first` and original
tests from `/root/b75_directory_fence`, each using a separate existing D: review
worktree; `/root/sdk14_activation_review` independently reviewed source.
Root remained the only tracked writer. Original tests were preserved, with
three fixture-path literal changes, one added metadata test and the two exact
exception corrections documented above. The initial review's lifecycle-pointer
typo is corrected by a separate erratum; the original review remains intact.

The test author's oracle review (30,412 bytes, SHA256
`8d4bd99c349a2d190c933a6e6cf75522561e3d9de0cc56cc83f312a3742dc5af`)
independently joins all four closed captures and 10,760 phase/archive entries;
it is independent of the production writer/executor, not of test authorship.
The separate capture/preservation reviewer confirms all 13,101 original/copy
pairs match. Current README results text is an explicit post-test documentation
delta; its tested version remains in the archives. No production/test source
changed after `30563740`. The new report is also post-test documentation.

At final unit closure, measured generated outputs were 799,108,073 bytes below
3 GiB and controls 40,016,132 bytes below 64 MiB (before the 9,024,483-byte
preservation receipt and later small reviews). These are selected-output
meters, not a disk quota or complete global cache/TEMP measurement.

## Limits and next work

Four Android journeys remain **0/4 executed**. Host fixtures simulate transport,
native observations, owner/controller outcomes and ledger closure; they prove
protocol behavior, not Android UI, TalkBack, JNI/ARM64, physical-device or model
performance. B88's real data-only verifier ran; the complete SDK16 admission
wrapper was tested with mocked freshness because prospective proposal/authority
inputs intentionally do not exist. No full workspace/CI or native build rerun.

Inherited supervisor limitation: `runtime_spike.WindowsJob.close` checks job
termination/zero descendants but ignores `CloseHandle`'s BOOL. Reported cleanup
establishes its implemented process/reader/capture checks, not independently
checked success of that close return. Keep this M10.02 shared-owner follow-up
visible; this thin-profile packet does not silently alter the mechanism.

Shared ledger remains v1/hash `4917ec69...`, original 40 GiB charge retained;
PR #354's exact proposal/hash `62901283...`, frozen operator/source/product and
failed pre-SDK evidence remain unchanged. No SDK16 input, actual authority,
guest, SDK/ADB lifecycle, model, phone, deletion, system settings, other-emulator
stop or merge occurred. Earlier spent grants were not repurposed.

Next runnable work is the shared-owner close-result follow-up and then a
source-bound SDK16 recovery/input operation against these fixed artifacts.
Actual recovery/boot retains exact approval, shared admission and ownership gates.
