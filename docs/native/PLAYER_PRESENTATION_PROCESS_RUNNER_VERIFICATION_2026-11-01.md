# Presentation-process runner host verification

2026-11-01. B44. Refs #14 (M10.02), #13 (M09.06), #307 (supporting M09.04).
[Draft PR #315](https://github.com/OptimumAF/LocalLore/pull/315) is a focused
host-only implementation, stacked on open/unmerged #314 at
`56be90c34ab6569501ff03561cfcd52cfb0b3104`. Full task checkboxes remain unchanged.
The host slice is **in_review**, with no owner acceptance or merge implied.

Tested executable/source checkpoint:
`1a3087f77c67e3c083df3ec56348f63033deab05` (2,553 tracked inputs).
Later report-only commits do not replace that attribution. The separately frozen
Android product remains `6302cb45b0a4397ee1313cc7b21e3d8cfe8f8fc8`;
no Android rebuild was performed in this packet.

## Implemented scope

The [SDK9 contract](PLAYER_PRESENTATION_PROCESS_RUNNER_V1.md) adds a concrete
owner/client/replay/controller family for the three B43 APKs, one external
`presentation_process` claim and three bounded original V3 probe leaves.
Admission determines the exact run/hash; no arbitrary package, method, command,
UID, profile or model selector is accepted. Successful replay consumes precisely
`Nboot+38` SDK records and invokes the real B43 proof reader.

The source-fixed build guard checks the original clean product/source roster,
closed public four-command pipeline, original JVM/lint/audit evidence, three
APKs and three closed signer outputs without running build/SDK/signing tools or
the private launcher. Parent, worker and live observer reject bad builds before
shared native setup. The sealed host build manifest is 3,262 bytes, SHA-256
`1aea0029eb32f1151956b80bff2ab5fb54b6f987a00f6a87b99c919419ee197f`.

Existing SDK4–8 contract/owner/client/verifier bytes remain unchanged. The only
existing production-file delta is two exact protocol identifiers in
`receipt_avd_retirement.PROTOCOLS`. All fifteen cleanup predicates and the
source/proof, exact-image authorization, held-handle and finalization checks stay
active. This lifecycle prerequisite does not execute a retirement or grant one.

No engine, canonical event, truth/knowledge, branch, inference, cancellation or
gameplay authority changed. No dependency or runtime version was introduced.
The deterministic engine remains authoritative; host summaries and proofs do
not replace canonical history.

## Actual verification

All commands ran from the physical D: integration checkout, using installed
Python3.14 with process-local TEMP/TMP/TMPDIR on `D:/Dev/_Temp`.

| Check | Observed result |
|---|---|
| Final combined new host cohort | 34 pass, 0 failures/errors/skips, 126.747s; direct child0, outer127.152s |
| Existing targeted regression cohort | 308 pass, 0 failures/errors/skips, 143.177s; direct child0, outer143.892s |
| Seven independent build methods after fix | 7 pass, 0 F/E/S, 16.993s |
| Seven complete/partial controller methods after fixture repair | 7 pass, 0 F/E/S, 95.853s |
| Unmocked current build guard seal and full artifact replay | PASS, worker4.268s / direct-child outer4.418s |
| Independent closed evidence/source reader | PASS, body1.819s / direct-child outer1.909s |
| Root recovery readback | PASS, 628 original/ZIP pairs plus incremental bundle, 663ms |

The final cohort hashes all 2,553 tracked files before and after; both maps are
327,015 bytes, SHA-256
`1ab27a558e4629daccaf0916eb11ca7d137cd18e91ffb25b97e4bfa12c24abca`.
The individual rows above overlap the final34 and are not additional tests.
The independent reader checks the34 exact unique named methods,308 regression
summary, source maps/current raw bytes, original failures, manifest and all three
APK bindings. Its result is38,426 bytes, SHA-256
`ad0d6d0b44178e22e1ef493499693bd624a0bf6b8a1b38bb9d1f260a89a1c428`.

The full positive controller fixture uses two boot polls,40 actual synthetic
wire clients,80 proof captures, all three package pre/post checks, one durable
claim, original probe stdout bindings and the genuine V3 parser. Build tests
patch only `_SPEC` to coherent byte-backed files and a real tiny Git repository;
they retain real source, command, XML, audit and signer verdict code. Controller
tests additionally mock native observations and transport, plus the documented
exact historical synthetic-ADB byte exception. These are **host synthetic
checks**, not an Android installation or process-death observation.

The new cohort command is:

```powershell
python -B -m unittest -v scripts.tests.test_presentation_process_runner_contract scripts.tests.test_presentation_process_runner_client scripts.tests.test_presentation_process_runner_build scripts.tests.test_presentation_process_runner_controller scripts.tests.test_presentation_process_runner_retirement
```

The separate regression command is:

```powershell
$legacy = @(
  'scripts.tests.test_owned_target_contract',
  'scripts.tests.test_android_process_client_v4',
  'scripts.tests.test_archive_ui_contract',
  'scripts.tests.test_archive_ui_owner',
  'scripts.tests.test_archive_ui_client',
  'scripts.tests.test_archive_ui_controller',
  'scripts.tests.test_archive_ui_build',
  'scripts.tests.test_record_ui_contract',
  'scripts.tests.test_record_ui_client',
  'scripts.tests.test_record_ui_controller',
  'scripts.tests.test_record_ui_build',
  'scripts.tests.test_player_presentation_ui_profile',
  'scripts.tests.test_player_presentation_ui_io',
  'scripts.tests.test_owned_target_storage',
  'scripts.tests.test_receipt_avd_storage',
  'scripts.tests.test_receipt_avd_storage_integration',
  'scripts.tests.test_receipt_avd_storage_adversaries',
  'scripts.tests.test_receipt_avd_retirement',
  'scripts.tests.test_receipt_avd_retirement_sdk7',
  'scripts.tests.test_receipt_avd_retirement_preview',
  'scripts.tests.test_receipt_avd_retirement_windows',
  'scripts.tests.test_android_presentation_process_evidence',
  'scripts.tests.test_presentation_process_build'
)
python -B -m unittest -q @legacy
```

Private finite direct-child controls retain actual commands, return codes,
raw stdout/stderr, helper/source pins and deadlines. They do not claim a
WindowsJob or descendant-closure attestation. This packet's reader revalidates
B43's existing417-JVM/48-XML/both-JNI-ABI build and retained lint warnings; it
does not rerun those Android checks. See the [original build report](PLAYER_PRESENTATION_PROCESS_VERIFICATION_2026-11-01.md).
A live GitHub query for tested code1a3087f7 returned zero workflow runs;
aggregate pending with an empty statuses list was not treated as a running job
or hosted CI success. No workflow was dispatched or setting changed.

## Failures and plan changes retained

- Initial contract absence was `NOT_IMPLEMENTED`, with zero new tests executed;
  the77 old controls passed. This is not a behavioral RED.
- The original retirement whitelist genuinely refused coherent SDK8 and SDK9
  closures:7 methods,2 positive assertion failures,5 guard/legacy methods pass.
  Add only those exact names as a prerequisite for this profile's lifecycle.
  The final tests reach the unchanged cleanup/source/proof guards.
- First build cohort:7 methods,6 pass,3 assertion-failing subcases in the
  nested-outcome method,0 errors/skips. Header totals and the direct roster
  could hide nested XML failure/error/skipped nodes. Commit `ec1070a1` rejects
  all descendant outcomes and nested suites/cases. The same seven methods pass
  without weakening their assertions.
- First controller cohort:6 methods,5 assertion failures before Live setup,
  1 early-owner-refusal method pass. Its late negative oracles were not reached
  and are not counted as verified. Two direct diagnostics identified the real
  cause: the inherited fixture globally replaced `threading.Thread` with an
  inline SDK sender lacking the optional arguments needed by Windows Git pipe
  readers. `1a3087f7` scopes that mock to the wire module; real Git and all
  production validators remain active. The corrected cohort has the original
  six methods plus an appended parent/worker pre-native refusal method.
- Unrun preservation-control drafts remain retained after source review
  corrections. They are not execution failures or successful copies.

The independent test author used a separate test branch/worktree; Root
integrated its commits centrally. Production files had disjoint ownership and
serialized commits. A separate reviewer checked source and then read the closed
evidence; those reviews are not owner acceptance.

## Private preservation

Originals remain on D:. The private packet root is
`D:/Dev/Experiments/LocalLore/2026-11-01-presentation-process-runner-v1`.
The create-only recovery at
`D:/Dev/Recovery/LocalLore/2026-11-01-presentation-process-runner-v1`
contains four files totaling6,218,962 bytes, below the128MiB cap. It preserves
628 original files/5,420,088 bytes, including three exact inert diagnostic
fixtures, in629 ZIP members (one is the50,995-byte source bundle). All original,
archive, full member readback and final original hashes match. Root independently
rechecked every pair; its derived925-byte receipt has SHA-256
`0020d56464a7bdfcea8c628493136fd2c79e6c7dd14dd249a0de20cec8bd6a0e`.

| Artifact | SHA-256 |
|---|---|
| ZIP,5,610,295 bytes | `8172e55a6babe07a62b73c1d722646ece4d688196f7342b46d934d086dac679c` |
| Manifest,556,459 bytes | `7d04a48cbd1c5560ac1fb577ff91b40e6a8209d1ec4d33af20549a3d4fe8a805` |
| Incremental bundle,50,995 bytes | `198b2b4e64e5097043e51d6df04b3264b9da71e948f349693696f27060cc6393` |

The bundle verifies and contains one pinned branch at tested1a3087f7. It
**requires base56be90c3**; it is not a complete cold-restoration archive or an
all-ref backup. Report-only commits follow separately. Original worktrees,
failed captures, other synthetic fixture roots, B43 build/recovery, models,
saves, credentials and all guests remain preserved. No private archive, raw
diagnostic, key, save or model is uploaded.

## Remaining gates and next task

Actual SDK9 target execution is **UNRUN**. B43's two compiled instrumentation
cases are also unrun by this profile. New actual saved-task/process deaths,
qualified owned guest/private-service closure and storage closure must be
recorded separately. Phone/ARM64/model performance, accessibility, broad
reliability and full M09.04/M09.06/M10.02/release acceptance remain open.

The earlier exact retirement/UI-run grant was spent by B42. This packet did not
prepare, boot, reset, stop, retire or copy models to any guest; did not discover
a phone, query ADB, alter shared services/settings, merge or release. The user's
other emulator remains outside this packet's actions.

Next runnable work is a read-only capacity/evidence inventory and concrete
SDK9 run proposal using these exact source/build inputs and the current shared
ledger. A new guest or exact-image retirement needs its own applicable approval;
the new host manifest and previous grants do not provide it. No alternate root,
registry, repeat attempt or timeout expansion is implied.
