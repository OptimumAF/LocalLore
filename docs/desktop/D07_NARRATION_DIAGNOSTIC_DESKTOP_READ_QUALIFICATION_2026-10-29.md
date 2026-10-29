# Desktop narration diagnostic read v1: scoped qualification

2026-10-29. Refs #29 **D07.04/D07.06**.
**Implemented and verified at accepted-main integration: actual synthetic native
IPC/WebView, Core/Host, workspace, application, frontend, lint, formatting and
normal-build checks passed. This is a scoped reader gate, not full D07 acceptance.**
Current completed verification is exact `54603e31281b23010e040e3eab002fa0a260fef0`,
which includes accepted main `3db75eff`. Earlier `0bbf8eed` native results and
both failed harness packets retain their original, separate source attribution.
Originally prepared against `9f57bba8c45c098dd0f0c5aaebc184d447ae6ea3` under
[#29 comment6502868048](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6502868048).
This note qualifies only the read-only desktop adapter above the
[Core companion slice](D07_NARRATION_DIAGNOSTIC_EVAL_COMPANION_QUALIFICATION_2026-10-29.md).
The [accepted contract and historical source handoffs](D07_NARRATION_DIAGNOSTIC_DESKTOP_READ_CONTRACT_2026-10-29.md)
retain exact interfaces, original freezes and later scheduling decisions.

## Implemented boundary

The existing `evaluation_comparison` IPC gains action
`narration_diagnostic_v1` with exactly `runToken`, `binding`, `turnId`, `arm`
and `observer`. There is no renderer path, attempt/session/owner, grant,
execution switch or model option. Requested observer is a lens, not authority.
The existing compact request cap remains 4,096 bytes; overflow returns
`InvalidEvaluationInput`, and bounded parse errors may precede authorization.
The already parsed Value cannot establish raw JSON duplicate-key rejection.

`ComparisonNarrationDiagnosticRequestV1` and
`EvaluationManager::comparison_narration_diagnostic_v1` reuse the existing reader
capability and retained owner. Manager denial of an absent native grant or any
non-Omniscient lens precedes scalar validation, expiry, lease/token/row/source
lookup and new filesystem work. The existing outer command still acquires its
workspace/Host; this is not a zero-filesystem guarantee for app initialization
or that transport layer. The Core Outputs access check remains authoritative.

The same live WindowLease, epoch, client/token, operation, cancellation and
one-worker ownership fences govern admission, transfer and publication. Source
I/O runs outside metadata locks. The capability returns only through the existing
current-owner completion path; close/retire/replacement cannot revive it.
The unchanged 30-second response timeout is neither cancellation nor a hard
filesystem deadline. A timed-out worker retains its real ownership until existing
status/close/drain completes; no shortened-timeout seam was introduced.

Only `OpenedRead::V4` calls the accepted Core companion reader. V2/V3 return
`Unsupported`, without a companion-file probe or fallback reopen. Dedicated
diagnostic error projection occurs inside the worker before old generic failure
mapping: wire/binding failures become `EvaluationIntegrity`, budget failures
`EvaluationBudget`, I/O `EvaluationIo` and unsafe paths `UnsafeEvaluationPath`.
Existing actions and their error projections remain unchanged.

The distinct result is version1,
`kind:comparison_reader_narration_diagnostic_v1`, `run_token` and `diagnostic`.
The **entire** serialized envelope is capped at 8,192 bytes, without truncation
or the old wrapper's extra allowance. The frontend uses `detached(raw, 8192)`
and exact nested fields, five statuses, 25 finite decisions and 43 Host rejection
codes. It refuses unsafe JavaScript integers and invalid index/admission/u32
attempt values, getters/prototypes and malformed query/reply or selected context.

The frontend checks available token, snapshot binding, selected row, scope,
BEFORE head, query/reply equality and hash shapes. Snapshot binding is distinct
from companion `run_binding_sha256`. Rust owns exact manifest/source/checkpoint/
ledger/base-revision/attempt binding; no latest-attempt lookup or historical
repair is added. Stored hashes/typed metadata are consistency evidence, not
authenticated historical origin. `generation_grant` remains false throughout.

`ComparisonReaderController::inspectNarrationDiagnosticV1()` explicitly reads
only with local eligibility, Omni lens, selected Protocol4 row and ready source.
It clears/busies synchronously, checks its ticket after synchronous subscribers,
and checks again before and after decoding a completion. Context, permission,
observer, selection, ordinary reads, clear/close and dispose clear private
diagnostics and fence obsolete results. Presentation never changes character
knowledge or what generation can access.

The Panel's diagnostic artifact contains source story/branch, turn/arm/lens,
BEFORE/AFTER, selected case phase/error, accepted-receipt availability, fallback
and quality limitation before raw metadata. A stored Host rejection is explicitly
separate from the current successful metadata read and from narration rejection.
No declaration/observation supplies no missing cause; recorded validation does
not establish commit or prose quality. Actor lenses hide the private artifact.

Normal native execution remains Protocol3. No future-run opt-in/admission,
idempotency/index change, Host operation/schema, provider, store, catalog,
selected-Protocol4 execution or default start/resume behavior is introduced.
Old report/evidence/trace/capture/recording DTOs remain unchanged.

## Independent FIRST and formatting provenance

Independent `99b400c6` freezes six native-manager and three parser functions,
plus the original 151-case decoder/controller/Panel checker. Integration is
`963bb9a0`. The author performed source checks only: the original
UNREGISTERED/UNCOMPILED/UNRUN labels describe that handoff, not later execution.
Actual opted-in scripted Host harvest/both recipes and actual default legacy
absence are separate from trusted stored unavailable/rejected controls.
The original sources and immutable hashes remain in the accepted contract.

Additive `b76858a9` integrates as `5edf62d7`. Five artifact-local context cases
bring the authored roster to 156; original 151 cases are preserved. The added
assertions examine each artifact before its raw-details body rather than accept
selected context shown elsewhere on the page. Their existing typed fixture has
case error null; no error or canonical outcome is fabricated to satisfy display.

Independent policy FIRST `e5ebf445` integrates as `90f7466c`: 61 authored checks
for the closed mode, aliases, complete namespace/model-root stripping and fixed
fake-child overlay. Helpers are absent at original adapter source `9f57bba8`;
the checker was SETUP/UNRUN at that freeze, not behavioral RED. Later harness
integration `8c86c312` has a separate measured policy result below. Its native
six-fixture/17-capture execution remains unrun here; no capture-whitelist or main
routing change is part of the adapter.

Root registration is `f652139f`; formatter-only normalization is `9f57bba8`.
Local `d07-diag-desktop-format-equality1.json` retains the first failed proof:
Rust matches, but two JavaScript formatter comparisons do not. That invocation
did not use the repository Prettier configuration for the original comparisons.
It is a proof/configuration error, not a product test failure or oracle change.
`d07-diag-desktop-format-equality2.json` explicitly uses
`apps/desktop/.prettierrc.json` and reports all four exact equalities true:

| Frozen source | Original SHA256 | Formatted/current SHA256 |
| --- | --- | --- |
| Six native functions | `606cf2c8c226fa71c047d55aac84f5c5332ddb65006b91ede651545f4aee3b14` | `ca394ca5f228b42f988b6174342976de859800881a68712bcce5a7140d2ca5e8` |
| Three parser functions | `797a6e24c148f837f2976a3c3e954810d41136326d57b5a8c72a0314cbddc5f4` | `777573e9894d55634017c43bb4e50e2a828dc26f7284b1c92375106f304f7de1` |
| Additive 156-case checker | `8601050b6e769ecf9ec1193bcc138cefdf0e0b09487af90458bdfbd3e8e9c4ca` | `3f19c5d4b9585faffa0e7ed9de9622656989f7d87f1617bbfbc4d2fafa11d8b4` |
| 61-case policy checker | `a5b61e581ed6f3a3c50505f4d70502fc47bac7669836052fb9f7f57c0bc6271f` | `2277d34a00e33e7e36b168fc2c7c7fb3dcd1e44aa6a04ee503c5bfe965ec80d8` |

The proof records rustfmt1.8.0-stable/Rust1.93.1, edition2021 and Prettier3.9.10.
Formatting equality preserves frozen assertions; it does not execute them.

## Measured frontend baseline and context correction

Both original local process records identify clean, unchanged source, D: temp
settings and the existing Node24.22.1 executable. Only the private executable
path is normalized here:

```text
node apps/desktop/check-narration-diagnostic-reader-review.mjs
```

| Source | Actual result | Exact UTC interval / command duration |
| --- | --- | --- |
| `90f7466c4dbbef50d127741a1c5cc20991ee74ad` | 151 passed, 5 failed, setup0; exit1 | 16:32:55.5986039Z–16:32:56.7814687Z / 1.1828648s |
| `c222becb25739e61f9161e7554dad475181cdde2` | 156 passed, 0 failed, setup0; exit0 | 16:34:27.0878996Z–16:34:27.4103467Z / 0.3224471s |

The five original failures are retained. `c222becb` changes only Panel context
and wording: local source/heads, explicit case error, quality limitation and
stored Host-rejection distinction. The unchanged checker then passes all 156.
Original local log SHA256 values are respectively
`f8de28903c4a5ef4d032db237f9affa870cc6efd9347051eb9f233e0b0849ff1`
and `c976368cd99095ab081abcd654be8873f6ff93c4b50fbb9e43ae4ee6152536af`.

These are actual frontend decoder/controller and React Panel static-HTML tests
with synthetic transport fixtures. They produce HTML, not browser layout,
geometry, PNGs, actual native IPC or WebView rendering. No visual inspection or
native execution result is inferred from the passing assertions.

## Original native failure, correction and later bounded checks

At clean, unchanged `9f57bba8`, the original focused run exited101:
**8 passed, 1 failed, 0 ignored, 293 filtered; 154.21s test,
188.8130829s command**, 16:47:06.5154613Z–16:50:15.3285442Z.
Local record `d07-diag-desktop-native-focused1-process.json` and original log
remain intact; log SHA256 is
`2fa076b88a45edd299510e4adb603cae33ec0c6ae2158f775ab39423e5c8702e`.
Both recipe reads, five statuses, worker/retirement checks and the actual
30-second response-timeout function passed in this failed overall run.

The permission test had already completed its three Forbidden/state assertions
and authorized expiry refusal. It then called `drain`, which removes all epoch
records, before closing that removed client. Existing Fixture::close unwrapped
`UnknownEvaluationRun`; the failing location is the parent helper, not one of
the permission assertions. Expiry closes the capability but retains the same
internal token; exact-token cleanup is valid before drain. This source diagnosis
does not turn the original failure into a passing run.

Authorized independent correction `c8b17880` integrates as `6afda895`. It changes
one insertion/one deletion in the test child: assert the same exact-token close
returns phase closed BEFORE the same drain. All permission/expiry/state,
reacquire and complete-byte assertions remain. No product code or other eight
functions change. Corrected test SHA256:
`c7e0d117b24b26f6a23e1a035c1f44309aecb99b30d07c4bf59930249a7258a5`.
The original/formatted/failing freezes are preserved; corrected execution is
pending and must receive separate source/timing attribution.

Further completed records are clean, unchanged at their own sources, exit0:

| Source / check | Actual result | Command duration |
| --- | --- | --- |
| `9f57bba8` full frontend/normal frontend build | Passed | 20.4386906s |
| `9f57bba8` development all-target strict native Clippy | Passed | 20.4481837s |
| `8c86c3127ec6458acf474857edd27462bc2a76eb` policy FIRST | 61 passed, 0 failed, setup0 | 0.1407027s |
| `3a84b1d37bc46302f8d666550faede6bee45a52d` full frontend including SSR156 and policy61 | Passed | 15.6089432s |

The policy result is trusted-source VM/fake-child simulation: native execution,
IPC, model execution, filesystem probes and desktop capture/control are false.
It does not qualify an actual process launch, SDK load or native render. Later
harness-source integration is not relabeled as execution at original `9f57bba8`.
Original record families are `d07-diag-desktop-frontend1`,
`d07-diag-desktop-native-clippy1`, `d07-diag-desktop-policy-first1` and
`d07-diag-desktop-harness-frontend1`, each with process JSON and log retained
under the local artifact root. Reproducible normalized commands:

```text
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --features dev-harness --target-dir <owned-D-target> narration_diagnostic_review_tests -- --test-threads=1
node apps/desktop/verify-frontend.mjs
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --features dev-harness --all-targets --target-dir <owned-D-target> -- -D warnings
node apps/desktop/comparison-reader-process-policy-check.mjs
```

Source-only independent adapter review at `9f57bba8` found no blocker. It
examined native admission/worker/timeouts, strict wire validation, frontend
stale/private clearing and artifact-local context against the accepted contract.
It is separate from runtime and acceptance. At the original note's freeze, the corrected
focused run, new native Clippy, Android Rust host and formatting batch are
**PENDING**; no running command is counted as passing.

## Remaining gates and limits

The third run below supplies actual app-owned hidden/unfocused WebView IPC,
cold restart, wide/narrow geometry and Root's individual render-image inspection
at `0bbf8eed`. Requalification at the accepted-main integration remains pending.
Pending-picker pixels cannot prove held diagnostic I/O.
The actual 30-second timeout passed within the original failed focused run;
that does not erase the cleanup failure or prove a hard filesystem deadline.
No new OS reparse/race/isolation or isolated valid-envelope8KiB boundary proof is
claimed; exact response-cap enforcement was reviewed in source. Finite stored
controls are not authenticated causes, SDK-load measurements or model outcomes.

No real model/assets/publication/import/reservation, original cohort mutation,
new desktop-control capture, phone/Android ABI/device or quality qualification
is established. Historical missing causes stay missing. Both human assessments
remain **needs improvement**; the full D07/desktop epic exit gates remain open.
Dependency acceptance is recorded on GitHub. D02 #23 is already closed; this supporting work
does not reopen it. This note grants no merge/release authority.

The documentation author performed bounded record/source/Git/hash/whitespace
inspection only, with TEMP/TMP on D:/Dev/_Temp and project work physically on D:.
Root owns measured execution and final evidence updates. The next runnable step
is to finish and separately qualify the integrated compatibility/native checks,
then complete independent evidence review before the scoped reviewable PR gate.

## Root corrected component checks — 2026-10-29

The following completed at clean, unchanged `6afda8950d20826b867f80411d5d61ba0ef1c97e`.
The source includes the finite three-path harness from original `300e4106`,
integrated as `8c86c312`, registration/formatting `3a84b1d3`, and the independently
reviewed cleanup-only correction `c8b17880` integrated as `6afda895`.

| Check | Result | Command duration |
| --- | --- | --- |
| Focused native/parser functions | 9 passed, 0 failed, 0 ignored; 293 filtered | 157.5014315s |
| Strict native dev-harness all-target Clippy | exit 0 | 8.5818871s |
| Android Rust host `cargo check -p locallore-android --locked --offline` | exit 0 | 0.5851512s |
| Root `cargo fmt --all -- --check` | exit 0 | 1.9839218s |
| Broad frontend Prettier check | exit 1; six inherited files | 3.3142250s |

The nine-function test body took 128.23s. The separately filtered contract binary
ran zero tests and adds no coverage. The original eight-pass/one-failure record
remains unchanged. This rerun changes no production permission behavior or
permission/state/expiry/source-byte assertions; it closes before draining and
adds an explicit closed-phase assertion. These are Rust component tests, with no
IPC, browser/native WebView, real model, phone or OS-isolation qualification.

The full frontend suite at clean `3a84b1d3` also passed in 15.6089432s after
harness integration, including strict TypeScript, the unchanged 156 diagnostic
cases and the 61 launcher-policy cases. The latter remain trusted-source VM and
fake-child simulation, not actual native/process execution.

The broad style failures are `ui/comparison-run-controller.ts`,
`ui/comparison-run-model.ts`, `ui/comparison-run-view.tsx`,
`ui/scene-model-guard-journeys.ts`, `check-scene-native-transport-review.mjs` and
`scene-model-guard-harness.mjs`, all relative to `apps/desktop/`. A Git comparison
against base `e95232fa` confirms all six byte-identical and outside this slice.
They are preserved; this is an inherited failed check, not a passing broad style
gate. A separate changed-file formatting check and actual native harness remain
pending at this append. No native pixels or IPC result follows from compilation.

Local records use `d07-diag-desktop-native-focused-corrected1`,
`d07-diag-desktop-harness-clippy1`, `d07-diag-desktop-android-host1`,
`d07-diag-desktop-root-format1`, `d07-diag-desktop-frontend-format1` and
`d07-diag-desktop-harness-frontend1`, each retaining original logs/process JSON.

## First actual native execution and retained harness failure

At clean, unchanged `fd57ce5510d35ed4b2918ef32301b4234711286f`, changed frontend
formatting passed in 0.5223339s and the full frontend suite in 15.4034497s.
Independent harness review first corrected capture targeting: a CSS selector
list chooses document order, so `fd57ce55` explicitly prefers diagnostic, then
evidence, then selection context, then controls. No assertions changed.

The first actual hidden/unfocused WebView2/native-IPC run then exited 1 in
120.4823624s. Packet `comparison-reader-native-6a855ced-5024-4d63-8c9d-9d348dbbdf59`
retains all original reports, six PNGs, semantic snapshots and logs. It exercised
recorded-left, accepted receipt, trusted stored unavailable/rejected, narrow
recorded-right and Mira clearing. Every generated image was individually
inspected: artifact-local source, revisions, status, receipt and quality framing
were visible; Mira showed its selected context with no diagnostic/private report.
This is partial actual native execution, not completion of the 17-image cohort.

Failure `comparison-mira-context-not-covered-by-sticky-header` is an independently
confirmed harness-oracle defect: with no artifact, the sticky header is both
target/context and alleged obstruction. The snapshot records identical bounds
for each: top -0.453125, bottom 113.296875, height 113.75. Positive area, viewport,
hit testing and private-state clearing passed before the impossible self-overlap
predicate. Correction `adeab968` exempts only exact `node === header` identity;
distinct-header overlap, positive-area, viewport and hit-test checks remain.
No product CSS, permission, fixture or state assertion changes.

The app exited without timeout, unknown-owned-drain was false, and the launcher
restored normal frontend/native builds without launching the product. A separate
bounded read-only collection after known direct app exit found all 641 fixture
file hashes equal to the frozen map: 660 entries, 5,313,354 bytes. The external
freeze is 74,900 bytes, SHA256
`c3ba3bbe60d0ff06b60d5b9ee881f0a1347b139470b1e42ad6b46d06a65551a3`.
The unchanged 256KiB proof and 128MiB collector ceilings fit this measured set;
they are ceilings, not runtime budget increases or a proof for every valid set.
Record `d07-diag-desktop-native-first1-postexit-fixtures.json` preserves this
collection separately without modifying the failed packet. A fresh synthetic
cohort remains required; no restart or remaining journey result is inferred.

## Second actual native execution and mounted-DOM synchronization

At clean, unchanged `f0820c519f07c20bc4e513598b22edf560b4e839`, the next fresh
synthetic run exited 1 in 107.1927913s. Separate packet
`comparison-reader-native-a621b798-e779-40b5-99b5-b826936ec413` preserves seven
images and the original reports. All seven were individually inspected. Header
self-overlap correction passed; actual Mira clearing and native Sable `Forbidden`
before malformed binding/row lookup passed. Both actor images contain selected
source context without diagnostic or private report. Broker errors were empty
at this point; the later malformed-control error had not yet been exercised.

It stopped at `actual-mounted-button-Show private report` immediately after
synchronously changing the controller lens from Sable to Omniscient. Independent
source review confirms the strict button lookup ran before any await and before
React was required to commit the Omni-only button. Controller ready/busy-false
state does not establish mounted DOM readiness. This is a harness synchronization
failure, not failed native permission enforcement or a completed cohort.

Correction `ef23e7ea` adds an existing bounded DOM wait only in diagnostic mode:
mounted panel data-observer and actual observer select must be Omniscient, with
exactly one enabled Show private report button. The original strict button
assertion/click and Protocol4 summary assertion remain. No native request retry,
direct loadSummary bypass, private state mutation, flushSync, new hook, default
mode change or product repair is introduced.

The app closed without timeout/unknown drain, and normal builds were restored
unlaunched. Separate post-exit collection confirms all 641 frozen file hashes,
660 entries and 5,313,289 bytes unchanged. The 74,900-byte freeze has SHA256
`7d85c71081da22ef78818c8f8493f2256a89cb3e7d98458fae61e7d8adae85d7`.
Record `d07-diag-desktop-native-second1-postexit-fixtures.json` is separate from
the preserved failed packet. The remaining journeys and cold restart still
require a fresh complete run; neither failed packet is relabeled successful.

## Third complete synthetic native cohort — 2026-10-29

Refresh claim: [#29 comment6503708164](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6503708164).
`0bbf8eed` adds diagnostic-only bounded mounted-DOM waits before row/read/capture
actions, binding the rendered lens, selected row and diagnostic/evidence presence
before existing strict assertions. It also records/checks the existing selected
header's visible error text, rectangle and hit test. Geometry failures remain
asserted after checkpoint capture. No product/controller/native/API/CSS change,
native-call retry, new timing hook or default-mode relaxation is introduced.
Source review found no further blocker; presence checks do not replace checking
the actual displayed status/text or individual images.

At clean, unchanged exact `0bbf8eed61315d580001464ff60a0899a474b427`, full
frontend verification passed in **14.8290703s**. The fresh native launcher then
exited0 in **203.4606851s**, 17:20:17.6299059Z–17:23:41.0905910Z.
Original records are `d07-diag-desktop-settled-ui-frontend1-process.json` and
`d07-diag-desktop-native-webview-settled-ui1-process.json`, with matching logs.
They retain clean/unchanged source, empty dirty lists, D: cache/target paths
and process-local TEMP/TMP `D:/Dev/_Temp`.

Packet `comparison-reader-native-637464b0-6622-4c93-b6fd-46adb32a8895` contains:

| Actual stage | Passing assertion occurrences | Distinct assertion labels | Native images |
| --- | --- | --- | --- |
| Initial | 139 | 74 | 15 |
| Cold restart | 21 | 20 | 2 |

These are occurrence/label counts, not 160 independent test cases. Both native
reports pass. Journeys use the actual frontend action/controller and native IPC:
both recipe reads, actual accepted receipt, all five diagnostic statuses,
actor clearing and native refusal, row/context/permission stale completion,
malformed integrity refusal, held-picker cancellation/close, fresh explicit
recovery and cold reread with a fresh capability. Stored unavailable/rejected
and malformed cases remain labeled trusted controls, not actual model failures.

Initial broker errors contain exactly **one** `{source:native,category:Transport}`:
the actual malformed companion read returns `EvaluationIntegrity`. The direct
actor request separately returns `Forbidden` with **zero** broker entries;
it does not use the controller callback. Restart has zero errors. No error is
hidden, renamed lost ACK, or counted as evidence of an unrelated rejection.
Picker-pending pixels are explicitly `held_picker_only`; diagnostic-I/O pending
pixels remain `unavailable_no_io_hold_seam`.

Root reports individually viewing all **17 original app-owned PNGs**, including
wide/narrow artifact-local source/revision/status/receipt/fallback/quality framing,
actor views without private diagnostics, and the selected malformed-error alert.
This documentation author read the records and did not perform that pixel review.
The run uses actual hidden/unfocused WebView2 rendering, not desktop capture,
headless browser rendering or static HTML. Snapshot user agent is:

```text
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36 Edg/156.0.0.0
```

This is the reported user agent, not an independently queried full WebView2
runtime version. The Node executable in the original process record is 24.22.1;
formatter/compiler provenance above remains separately attributed.

Both released-stage inventories equal the same frozen **641-file** map:
**660 entries, 5,313,467 bytes**. The 74,900-byte external freeze SHA256 is
`9c2b044d7e87ad19ee1d7a880ec3c3af6e72e057c419374dd5ded8713d526140`.
The 139,588-byte `qualification.json` SHA256 is
`0cb00627d65b5d9d59c0132dbcf8a51f75152baf18c1554c4f9aafdb2e4ff334`.
Initial/restart checks preserve original file bytes, including retained malformed
and moved-observation controls, and the external freeze itself. Counts/hashes
belong to this fresh packet; different earlier synthetic runs remain unchanged.

Both stages observe reservation sequence 0, no evaluation owner and retained 0.
The model directory remains absent after exit. These are managed-state and
directory observations, not independent SDK-load telemetry. Ordinary shutdown's
absent task-owned model-candidate metadata probe remains acknowledged. No real
model/assets/publication/import/copy/link/reservation is used. All six recorded
build/app/restoration children closed without timeout or unknown-owned-drain;
normal frontend/native restoration passed and the normal product was unlaunched.
This does not establish Job/process-tree containment or universal filesystem race
safety. No model-quality, Android ABI/device or new OS-probe gate is satisfied.

Reproduce this finite mode from the physical D: checkout, using existing owned
D: directories and the already locked/offline cache. Only private absolute paths
and the Node executable are normalized; no package/model download is implied:

```powershell
Set-Location '<physical-D-checkout>'
$env:TEMP = 'D:/Dev/_Temp'
$env:TMP = 'D:/Dev/_Temp'
$env:CARGO_HOME = '<existing-owned-D-locked-cargo-cache>'
$env:LOCALLORE_D07_COMPARISON_READER_ARTIFACT_ROOT = '<existing-owned-D-artifact-root>'
$env:LOCALLORE_D07_COMPARISON_READER_TARGET_DIR = '<existing-owned-D-native-target>'
$env:LOCALLORE_D07_NARRATION_DIAGNOSTIC_READER = '1'
$env:LOCALLORE_D07_SCENE_COMPARISON_READER = '1'
$env:LOCALLORE_D07_LITERAL_COMPARISON_READER = '0'
node apps/desktop/comparison-reader-harness.mjs
```

The launcher validates D: source/base/target, strips the complete inherited
case-insensitive LOCALLORE namespace before fixed child flags and creates a fresh
packet. Failure packets must not be overwritten or retrofitted. All collector,
proof and runtime budgets remain unchanged. Both earlier native failures, their
images and the original component cleanup failure remain failures.

## Accepted-main integration: verification pending

Accepted main `3db75eff` includes owner-merged #225/#258/#259/#260. Local merge
`54603e31281b23010e040e3eab002fa0a260fef0` completed without conflicts. This
refresh is doc-only on that base; the completed `0bbf8eed` run does not qualify
the merged source automatically. Root's integrated 17-capture native, app/shared Rust,
frontend, strict lint, Android Rust host and formatting checks are **PENDING**
at this document freeze. No running or future result is counted as completed.

Accepted main also adds a dev-harness `offline-qualifier` binary with OS-probing
tests. Root may compile/lint it but will not execute that binary or those probes
in this slice. App component/contract test selection is explicitly bounded:

```text
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --features dev-harness --target-dir <owned-D-target> --bin locallore-desktop-spike --test harness_contract -- --test-threads=1
```

This command is a pending integrated check, not an executed result here. Existing
unrelated broad-suite guard fixtures and compilation of the qualifier do not
establish new companion-specific OS isolation. Root owns final measured updates
and independent evidence review. D02 #23 stays closed; D07/desktop epic and human
quality acceptance remain separate. This note grants no merge/release authority.

## Completed accepted-main integration — 2026-10-29

All following commands completed at clean, unchanged
`54603e31281b23010e040e3eab002fa0a260fef0`. Root's local merge incorporates
accepted main `3db75eff` without conflict. These results replace the earlier
pending integration gate; they do not erase any historical failed record.

| Check | Exact result | Command duration |
| --- | --- | --- |
| Actual hidden/unfocused native WebView2 and IPC, fresh initial/restart | exit 0; 15 + 2 images | 213.0003273s |
| Full frontend, including existing 156 diagnostic and 61 policy cases | exit 0 | 14.9768733s |
| Strict native dev-harness all-target Clippy, `-D warnings` | exit 0 | 16.3425085s |
| Rust Android host check | exit 0 | 3.6415607s |
| Root Rust formatting | exit 0 | 3.1209259s |
| Full frontend formatting | exit 0 | 2.5034123s |
| Core/Host Rust suite | 535 passed, 0 failed, 4 ignored; 64 result groups | 88.3019911s |
| Workspace Rust suite | 182 passed, 0 failed, 1 ignored; 32 result groups | 65.3588560s |
| Application native components and harness contracts | 291 + 2 passed, 0 failed, 11 ignored | 833.1913156s |
| Normal application build restoration | exit 0; product unlaunched | 9.3705077s |

Rust suite totals include their emitted unit/integration/doc-test groups; they
are not a count of unique invariants across suites. The application unit body
took 802.74s, with two separately selected contract tests. The actual command is
the explicit application `--bin locallore-desktop-spike --test harness_contract`
selection documented above. The accepted offline qualifier compiled/linted,
but neither it nor its tests/probes were executed. Existing stopped D09 and
SDK/device gates remain separate. The six inherited formatting failures were
resolved by accepted PR260; this slice preserves those files and now passes the
complete style check after integrating main.

Native packet `comparison-reader-native-be8635cf-801a-4e25-be14-26415e92df57`
contains the initial 139 assertions (74 distinct labels) and restart 21
assertions (20 distinct labels); repeated journey assertions are not relabeled
as 160 distinct cases. Root individually viewed every one of its 17 original
CapturePreview PNGs. No layout or visible-state defect was found: wide/narrow
diagnostic context is readable; all five statuses are distinct; Mira/Sable
contain no private diagnostic/report; picker pending, close and context clear
contain no stale selection; the integrity error is visibly adjacent to source,
observer and revisions, separate from the committed canonical case outcome.
Fresh-process read and final closure are visible in the restart images.
`d07-diag-desktop-main-native1-render-inspection.json` records each image hash
and individual finding separately. Geometry failure arrays are empty in all 17.

The initial error buffer contains exactly one expected native Transport entry
from malformed-companion `EvaluationIntegrity`; direct native actor `Forbidden`
has an empty broker delta. Restart errors are empty. Known direct children
closed without timeout/unknown drain, and both post-exit fixture inventories
match the frozen map: 641 files, 660 entries, 5,313,563 bytes. External freeze
SHA256 is `2a1591a8199d98469362e8e3e799ceef49a6f3850ab1360e31ae39fe9a8d4c2b`;
qualification JSON SHA256 is
`6b829eeb99f126a7c4e708cfe76b32b3dc675057207b610a523687fb17bb8b7b`.
No process-tree containment or independent SDK-load proof follows from these
observations. The absent task-owned model-candidate shutdown probe remains.

All records use `d07-diag-desktop-main-` process/log families in the local
artifact root. The standalone Core/Host and workspace log hashes are respectively
`5a939181b9dedd78073f369f7ab87d0b1a88705eb277f761533ce6ddf95e0d4f`
and `b766b38a0f0a80f86f5e1e8d23053d2b0616e9627183558d3e85c4fdc021f495`.
The application component/contract log hash is
`a4a9937e06bff38dccba2f7d719fa639ca6142a2e54e37339d9cc5edec9ebcd5`.
Exact commands, timestamps, clean-source checks and exits remain in their
original process records. The normal frontend bundle hash remains
`656f14c372e1b9b544ab480ac18072a01b4d9e4ae7876c93def94853b4283dc9`
after restoration, matching the pre-main reader build; no normal product was
launched to establish that restoration.

Fresh environment record `d07-diag-desktop-main-tool-versions1.json` records
Rust/Cargo 1.93.1, rustfmt 1.8.0-stable, Node 24.22.1, PowerShell 7.6.5,
Windows 10.0.26300.0, Prettier 3.9.10, TypeScript 7.0.2 and React 19.3.1.
Installed WebView2 file metadata is 156.0.4314.50; this is not loaded-module
verification. Actual rendered UA reports Chrome/Edg 156.0.0.0, as recorded above.
TEMP/TMP and project/cache/artifact paths remain on D:.

This gate establishes the bounded read adapter and its synthetic/native
integration. It does not establish real-model prose improvement, restore the
30 historical missing causes, enable Protocol4 managed generation/selected
reruns, qualify Android SDK/device behavior, waive stopped OS/offline/package
gates, or complete the desktop epic. Both human assessments remain
**needs improvement**. The next implementation work requires its own contract,
FIRST tests and scoped acceptance; no unrelated capability is inferred here.
