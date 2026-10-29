# Desktop narration diagnostic read v1: scoped qualification

2026-10-29. Refs #29 **D07.04/D07.06**.
**Implemented; static-HTML, frontend and lint checks measured; original focused
native run failed in fixture cleanup. Corrected rerun pending. No native IPC/pixel gate.**
Prepared against `9f57bba8c45c098dd0f0c5aaebc184d447ae6ea3` under
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
It is separate from runtime and acceptance. At this note's freeze, the corrected
focused run, new native Clippy, Android Rust host and formatting batch are
**PENDING**; no running command is counted as passing.

## Remaining gates and limits

Actual app-owned hidden/unfocused WebView IPC journeys, cold restart, wide/narrow
geometry and individual native render-image inspection remain **UNRUN** for
this new adapter. Pending-picker pixels cannot prove held diagnostic I/O.
The actual 30-second timeout passed within the original failed focused run;
that does not erase the cleanup failure or prove a hard filesystem deadline.
No new OS reparse/race/isolation or isolated valid-envelope8KiB boundary proof is
claimed; exact response-cap enforcement was reviewed in source. Finite stored
controls are not authenticated causes, SDK-load measurements or model outcomes.

No real model/assets/publication/import/reservation, original cohort mutation,
new desktop-control capture, phone/Android ABI/device or quality qualification
is established. Historical missing causes stay missing. Both human assessments
remain **needs improvement**; unaccepted dependencies and the full D07/desktop
epic exit gates remain open. D02 #23 is already closed; this supporting work
does not reopen it. This note grants no merge/release authority.

The documentation author performed bounded record/source/Git/hash/whitespace
inspection only, with TEMP/TMP on D:/Dev/_Temp and project work physically on D:.
Root owns measured execution and final evidence updates. The next runnable step
is to finish and separately qualify the corrected checks, then review and execute
the accepted finite native harness before its render/IPC gate.

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
