# Selected desktop consumer — qualification, 2026-10-25

Refs #29 D07.06 and #25 D04.02/.03. **Partial developer integration: UI5,
current-source compatibility and the approved-asset lifecycle repeat passed.**
GitHub owns task status and owner acceptance. This document does not
close D07/D04, approve story quality, or establish phone/runtime parity.

## Source and evidence boundary

Guide source: `5187065eef87c6f8fbb74d8e4c3792b246dce74a`, the coordinator's
selected desktop consumer candidate. It includes the correction that retirement
waits for actual native acknowledgement rather than treating a context change
as worker completion. Earlier measurements below retain their executed source;
they are not relabeled as tests of this final guide source.

Root executed the commands and visually inspected all41 UI5 images. A bounded
documentation contributor read historical source/logs; Root then integrated
and updated this record from the terminal cohort. No desktop input/capture or
device command was used.
Raw traces, databases, private absolute paths and generated render artifacts
remain local/gitignored. `<artifact-root>`, `<native-target>`, `<eval-target>`
and `<task-temp>` below are task-owned absolute paths, not product inputs.

Dependencies and earlier evidence remain separately described in the
[selected native contract](D07_SELECTED_CASE_NATIVE_CONTRACT_2026-10-25.md),
[desktop contract](D07_SELECTED_CASE_DESKTOP_CONTRACT_2026-10-25.md),
[read-only qualification](D07_SELECTED_CASE_DESKTOP_READ_QUALIFICATION_2026-10-25.md)
and [owned runtime prerequisite](D07_OWNED_RUNTIME_CLEANUP_QUALIFICATION_2026-10-25.md).
Their historical model, Rust, Android and render results are not new consumer
qualification. In particular, a shared native result is not native service,
IPC, native WebView or real-model UI execution.

## Developer flow and authority

The dedicated selected model/controller/view uses the existing evaluation
manager and shared selected driver. Native `evaluation_selected` accepts a
closed action plus a UTF-8 JSON request capped at 4096 bytes. Core's
`parse_unique_json` rejects recursive duplicate keys. UUID/hex identities,
JS-safe integers, observer/view/arm enums and exact field sets are checked.
There are no renderer paths, executable names, profile overrides, native consent
booleans, arbitrary tools or report-as-canonical-state commands.

`prepare` consumes a same-window, same-epoch comparison source capability under
the existing admission gate, then releases its reader lock outside metadata
locks. Shared Rust fresh preflight owns original request, both arm snapshots,
source/dependency validation, resource admission and destination safety. An
existing foreign pin yields honest Busy. The prepared descriptor is native
validated metadata, not a renderer reconstruction of a Request or Engine.

Execution consent and private reading consent are separate native affirmations.
`start` consumes the bound plan, returns/recovers the same admitted operation,
and does not create a read grant. Explicit `open` independently affirms reading;
`resume` uses a current read identity plus a fresh source capability and fresh
execution consent. Native source paths stay in opaque capabilities. Durable
run UUIDs select native-computed `selected-evaluations/<id>/work`; the envelope
and shared work directory are distinct. Missing work on resume is an integrity
error, not permission to recreate, repair or silently restart it.

The wire actions are `catalog`, `prepare`, `start`, `status`, `cancel`, `open`,
`resume`, `summary`, `evidence`, `diagnostics`, `close`, `cleanup_status` and
`retry_cleanup`. Close and generic cleanup remain available without a Story Lab
grant; other actions use the actual Host grant and current WindowLease.
Raw actor evidence/diagnostics is denied before private token/Host probes.
Private read grants are never promoted to execution authority.

`scripted_baseline` means fake inference through the actual Core/Store pipeline;
`approved_native` selects the existing approved worker/model path. Stored lane
names remain `scripted_selected_case` / `native_selected_case`. Generation's
actor is the original player. Inspection lens changes clear/filter private
reads without changing that actor, request, profile, knowledge or execution
identity. Character views use actual Query2 edges; there is no inferred player
identity from the active game or a character named `player`. Full report,
source Requests, traces and outputs are not actor summary fields.

The UI distinguishes experiment scope/head/lens from live gameplay context.
There is no shared live progress callback beyond reservation: running is
indeterminate, not an invented load percentage. `completed` means both attempts
finished, not both passed or human-approved. An unknown acknowledgement keeps
the same client for explicit recovery; it never auto-rekeys or retries inference.
Historical inspection does not execute a case or import it into a live story.

## Owned lifetime, curated path and shutdown

The same parent Job owns worker-active state, cancellation and optional selected
ownership. There is no second worker/model manager or resource-owner registry.
Unknown cleanup retains the actual reservation R plus the same runtime Arc, or
its exact ModelManager cleanup witness after successful same-slot handoff.
Selected opt-in reservation fencing survives rejected handoff/stale ticket
faults; legacy inherent reservation semantics are not silently reinterpreted.

Worker completion, window retirement and removal of a JoinHandle are not proof
of runtime cleanup. Cleanup runs outside metadata locks and clears only the
captured matching Job/owner after positive terminal proof. A runtime-busy retry
remains unconfirmed. No JSON flag, status label, dropped token or arbitrary old
lease can acknowledge cleanup or stop a replacement runtime. The generic owned
cleanup also supports the upgraded curated Job payload, regardless of JobKind.

The owned-curated leaf reuses the existing Session/Ledger/body and runtime.
Entry time reaches admission before new durable reservation; after its one
preparation reservation, the same turn predicate is checked before assets.
Absolute preparation deadline covers opening/load; actual cleanup precedes
invocation finish/final report. Unknown cleanup retains full unknown reservation
and does not publish completion. Cached curated restore preserves its existing
invocation/finalize-write behavior; this is different from a completed selected
resume's byte-read-only workflow. Neither path receives fake known role costs.

CloseGate is owner-free coordination, not cleanup authority. Native close/exit
invalidates the captured lease, retires access, drains workers and attempts
matching cleanup. Models.close can confirm a handed-off witness; the same old
evaluation Job is reconciled afterward before `finish_close`/destroy/exit.
Cleanup uncertainty pauses continuation and exposes explicit retry. Renderer
status cannot force window destruction or certify child/thread termination.

At guide source518, retired frontend clients close-poll only their captured
native identity while actual `running` remains true. Malformed, transport,
nonclosed or cleanup-uncertain replies retain the barrier. The corrected source
completed native UI5 as recorded below.

## Terminal focused evidence — coordinator executed

Every row is source-bound and separate; overlapping groups are not added into
a fabricated aggregate. Times are test/build seconds from completed logs.

| Evidence / executed source | Result | Scope |
|---|---|---|
| Selected service first clean, `d947f012` | Compile failed, five serde errors; zero tests executed | Missing direct serde dependency/derive bounds; not behavior RED |
| Selected service review, `3820c707` | 13 passed, 155 filtered; 139.20 / 15.91 | Actual scripted service/Store, identity/replacement/gating; not GUI/model |
| Completed service resume, `83e97280` | 1 passed, 171 filtered; 56.15 / 30.12 | Genuine completed scripted run, fresh source/read grant; same run/heads/binding/full bytes; inert old start receipt; denied resume |
| CloseGate, `1cc80e21` | 8 passed, 133 filtered; 0.00 / 18.45 | Native Rust coordination units, not actual OS close UI |
| Owned-curated original, `79ec8fe2` | 4 passed, 2 opt-ins ignored, 103 filtered; 0.15 / 10.07 | Model-free ownership/preflight units |
| Owned-curated approved opt-ins, same79ec | 2 passed, 107 filtered; 89.03 / 0.16 | Historical explicitly installed-asset execution; not current-source repeat or UI/model quality |
| Owned-curated budget baseline, `4a3e4382` | 1 existing pass, 2 new failures; 9.53 / 19.58 | Assets touched before turn admission; exhausted entry clock admitted a durable invocation |
| Same budget regressions, `8ae0e99d` | 2 passed, 109 filtered; 0.30 / 7.98 | Existing predicate/entry-clock correction, unchanged oracles |
| Curated native service, `6977a23b` | 3 passed, 146 filtered; 5.89 / 17.55 | Fixed native unit fixture, including caught test panic; not GUI or new asset cohort |
| Controller check, `c94c6975` | First wrapper invoked module `c`: zero cases; corrected command 22/22 | Synthetic transport, no headless component/native rendering/IPC/model execution |
| Full frontend, `5c7d599c` and `7da12e1c` | Both exit0 | Historical integrated synthetic/strict frontend gates, not current518 final gate |
| Native strict all-target/all-feature Clippy, `83e97280` | Exit0; 14.65s | Historical wired source, not final518 qualification |

The completed-resume group holds a real Models metadata reservation while
checking that scripted cached resume does not acquire/replace it. It compares
summary/diagnostics and complete source/run inventories after read caps/pins
and actual workers are released. It does not manufacture a native lane/profile,
prove actual UI resume, or execute a real model.

## Failed native UI cohorts retained

Each initial process rendered through the application's actual hidden/unfocused
WebView2 and native IPC. These are failed cohorts, not successful qualification.
Counts are recorded passing check entries before the failed check, not distinct
test families. No restart stage completed in these four cohorts.

| UI / source / cohort UUID | Checks / actual PNGs / app seconds | Failure and bounded interpretation |
|---|---|---|
| UI1 `fbe19ea1`, `83e69be7-7763-4e1d-904d-0d0396216f0e` | 11 / 1 / 141.440; exit1 | `actual-scripted-selected-both-attempts-finished`; EvaluationIo. Fresh selected-only startup exposed capacity checking an absent built-in root. Prepared image alone was Root-inspected. |
| UI2 `23623490`, `e58310fc-e508-4940-bfc2-2812af337622` | 95 / 12 / 295.221; exit1 | `no-unexpected-errors-before-deliberate-lost-start-ack`; two unexpected Transport entries from closing a transferred empty reader. Closed-only token handling corrected separately; no ordinary repick expansion. |
| UI3 `9d5f1da2`, `78a3948d-5b4f-4108-b6d0-157bf2f0b643` | 127 / 17 / 602.059; exit2 | Native600s watchdog, last failed label `fresh-source-native-reader-ready`; one Transport plus four Closed records after shutdown. Outer runner timedOut=false does not erase native watchdog failure. |
| UI4 `83e97280`, `0b0bd3bb-ca36-477d-8ac7-8fa940599d4e` | 140 / 18 / 552.767; exit1 | `captured-old-client-drained-after-context-retirement`; actual callback entry/hold confirmed. Only expected lost-start-ack Transport; worker-retirement assertion still failed. |

All four outer runners recorded overflow=false and timedOut=false. UI1/2/4
retained115-byte Chromium `Chrome_WidgetWin_0` unregister1412 stderr; UI3
retained142 bytes. This is not zero native stderr. Raw diagnostics are not
reproduced here. None of these failed image sets has a new blanket visual/layout
approval in this draft. Source checkpoints and failure explanation are also
recorded on [#29](https://github.com/OptimumAF/LocalLore/issues/29).

## Successful native UI5 cohort

Source `5187065eef87c6f8fbb74d8e4c3792b246dce74a`, local synthetic cohort
`5cb7f856-cad9-4616-9fb3-d990898bad83`. Both processes exited0, with no outer
timeout or output overflow. Source remained clean and unchanged through both.

| Stage | Recorded checks | Actual native PNGs | App wall seconds |
|---|---:|---:|---:|
| Initial executable process |154|20|516.315|
| New executable process, same workspace |160|21|419.869|

The launcher also verifies every required semantic field and native capture
marker, complete original/final source-fixture hashes and cross-process source
byte equality. Each stage records exactly one deliberate lost-start-ACK
Transport error; each retains115 bytes of the existing WebView unregister1412
stderr warning. These are not zero-error-output claims.

Actual normal controllers/native IPC exercise accepted Move4 to5 in both
isolated arms, rejected guard8 to8 with unavailable receipt, independent private
read consent, both observer lenses, same-client status/retry after lost ACK,
actual held consent cancellation/denial and context retirement. Live gameplay
stays unchanged. New-process open is historical inspection, not the explicit
resume action. Native consent/picker responses are fixed development doubles;
inference is scripted. No model executes in this cohort.

Root inspected all20 initial and21 restart application-owned images: prepared,
completed, summary, both arm queries, receipt, capture, outputs,620px narrow,
Mira3/Sable0 history, guard missing evidence, unknown ACK/recovery, pending/actor
consent, cancel/deny, retired context, finished and cold reopen. No visible
layout/state defect was observed. Raw JSON views wrap in bounded scroll panes;
capture truncation is labeled. Retirement clears story/revision/pending/receipt
and visible error. These observations are model visual QA, not human narrative
quality acceptance. A requested150ms scheduling probe measured163ms in one
summary snapshot; this is not foreground performance qualification.

| Local evidence | SHA256 |
|---|---|
| UI5 qualification.json |6c649763a0f4034545f44acec59af4ba2300f5fa5e8c60557556397292fddfc6|
| UI5 visual-review-initial.json |a7cf5961d25fad3534404126a88157a32b2db60e199a65284e8524ab27a501ed|
| UI5 visual-review-restart.json |a32b27206a3b8986bb960e5ba3ab365506dfdb9cfbd124a7fc60d1b8b9dd9f1e|

The retirement controller regression at `e9df2377` failed22pass/1fail, then
`5187065e` passed23/23. Independent regressions adopted from `af698d7f` and
registered/formatted at `904c26b1` passed29/29 using the actual bundled
controller with mock transport. This adds no native/model/rendering claim.

## Final compatibility and installed-asset cohort

All following commands executed at clean source
`85669fed40c732a98218d516c2ad112025bf9cac`, with terminal source unchanged.
Production code is unchanged from the successful UI5 source; later changes
register/format independent mock regressions and update documentation.
Logs use the local prefix `d07-selected-consumer-final-first`.

| Gate | Exact result | Test / command wall seconds |
|---|---|---:|
| `node verify-frontend.mjs` | Exit0; includes29 selected-controller mock cases,18 close-controller cases, strict checks and normal hook exclusion |16.467 first;24.724 restoration gate|
| Native `cargo test --all-features` |171 passed,0 failed,1 ignored Windows symlink-privilege test; separate2 harness-contract tests passed|401.02 native test;448.834 whole command|
| Eval owned-curated, `--features protocol-owner-tests --lib local_lane::owned_curated` |6 passed,0 failed,2 explicit asset opt-ins ignored|0.43 test;2.703 command|
| Eval selected, `--features local-model --lib local_lane::comparison::selected::` |32 passed,0 failed,4 explicit asset opt-ins ignored|1399.47 test;1416.126 command|
| Eval all-feature/all-target strict Clippy | Exit0, warnings denied|11.217|
| Android Rust-host `--lib` tests |20 passed,0 failed|2.36 test;24.225 command|
| Android normal/build/dev dependency graph | Exit0; no Tauri, eval or local-runtime edge|0.572|
| Frontend Prettier / Rust workspace format | Both exit0|11.802 /11.319|
| Native all-feature/all-target strict Clippy | Exit0, warnings denied|49.666|
| Normal native build, no extra features | Exit0; normal frontend/executable restored|59.335|

These are separate suite entries, not one aggregate count of independent
invariants. The long shared test includes fresh reference/comparison producers,
indexed post-commit cancellation, missing-arm resume, source corruption and
complete file inventories; its duration is not a gameplay latency measurement.
No JVM/Gradle, Android ABI build, emulator or physical device was run here.

The separately admitted installed-asset command was:

```powershell
# Existing approved resources/model only; set the two variables to those assets.
$env:LOCALLORE_SELECTED_NATIVE_TEST_RESOURCES='<approved-resource-directory>'
$env:LOCALLORE_SELECTED_NATIVE_TEST_MODEL='<approved-existing-model-file>'
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <eval-target> --lib local_lane::owned_curated::review_tests::approved_ -- --ignored --nocapture --test-threads=1
```

Both actual native lifecycle tests passed,0 failures,160.10 test seconds /
161.574 command seconds. Each retained synthetic `gift-agency` case passed69
finite checks and recorded6 actual role requests: gift/thanks/power-claim
committed; the attempted second potion spend failed with Inventory. Cached
curated resume kept its case checkpoint and accessed no assets. Forced cleanup
uncertainty kept the actual R/runtime pair and full unknown invocation charge,
without publishing a successful final report; explicit owned cleanup followed.
This is actual Rust/runtime execution, not native IPC/WebView/model UI.

**Quality defect retained:** Root inspected a power-claim narration that wandered
into an unrelated library scene. The69 finite checks did not detect that prose
failure. Canonical effects remained bounded by Rust; these passes do not
establish grounded narration, enjoyment or quality acceptance. D07.04 and its
human-review gate remain open. Raw synthetic output stays local.

Assets were rehashed before this cohort; nothing was downloaded or upgraded:

- Qwen3-0.6B-Q8_0,639446688 bytes,
  SHA256 `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`.
- Existing worker,6014464 bytes,
  SHA256 `b5dd124e484c67c9dda5aebb2cdff1878ccefd0fba99aba4788e00a166f68434`;
  llama.cpp `620d2225cc436ab0b001e3200e590e3b286ef9ab`.
- Profile manifest `01ad542001b04a96f4a8ed6c841be1866eb025350836e0c5d0a4969fdb361d38`;
  CPU4/GPU0, context4096,350 tokens per role, one repair,120000ms turn deadline.

Fresh version query: Windows NT10.0.26300.0 x64, PowerShell7.6.5,
rustc1.93.1 (`01f6ddf7588f42ae2d7eb0a2f21d44e8e96674cf`), LLVM21.1.8,
Cargo1.93.1 (`083ac5135`), Node24.22.1. Actual UI5 WebView UA reports
Chrome155.0.0.0 / Edge155.0.0.0, DPR1. No other platform is qualified.

Normal outputs at856: `app.js`565555 bytes,
SHA256 `04ac7c52a84fe0506d92f29b7f4690aa84dbd5f291679bfeb3882e55ded1a495`;
native executable34142720 bytes,
SHA256 `221facdfb3a4f1bb9007efaa8c11ac7325e8e8e9575ac7bc1ba0d5c64db0e256`.
These are source/build identifiers, not a claim of byte reproducibility or an installer.

| Additional local evidence | SHA256 |
|---|---|
| Final production-results.json |6d4739ecba3883e1bd00236c5ca735d64ad987dfaa1a554d69bb569938f1f37f|
| Final production-build-artifacts.json |487437d7336a9e503373f039a5c6d17a2c854b02be55790618d86a61edb9203e|
| Current versions.txt |b7c56388c097d04bbdd102c3cc913ca0d5a7c3b78b4ff162ee0aa5013cf018f7|
| Current installed-model test log |532c4dee2ef0af30e7321ff11be2ed764010e111753ae61732fff9013eccd176|
| Current installed-model process record |78338ce6fd4987dfc3541a87cf6b28198f95f1f80146d7e7371d4b991ce5d419|
| Current installed-asset hash record |f3cf35d8ad38a5488435e038b86d73f26dc1c82ecf43dac973d5246fbdc24e8d|

### Accepted-main reconciliation

Accepted PRs176–179 advanced main from `a7feb420` to
`dbcc40f6fedc1cb6539611b21a772570e6fb162f` during qualification. Normal merge
`453606afaffdb1f12e2d47043e8f9910fdd6c5cd` preserved their Android diagnostics,
tooling, docs and new Core integration test without conflict. No other working
directory or running application was touched.

Git object comparisons confirm byte-identical qualified inputs at856 and453:
the entire desktop directory, Core source, evaluation/runtime/Android Rust/
storage/workspace crates, root Cargo manifest/lock and Rust toolchain. These
prior runs retain their original source IDs; they are not relabeled as fresh
executions after the merge. The newly accepted integration test and format were
checked on453:

```powershell
cargo test --locked --offline -p locallore --features host --test dialogue_json_spelling --jobs 1 --target-dir <native-target> -- --nocapture --test-threads=1
cargo fmt --manifest-path apps/desktop/src-tauri/Cargo.toml --all -- --check
```

Four integration tests passed,0 failures,0.09 test seconds /12.61 compilation
seconds; formatting exit0. This includes equivalent Unicode JSON spellings,
malformed surrogate/authority refusal and observer isolation. No Kotlin/JVM,
SDK, Android device or benchmark execution is inferred from accepted files.
Local input-identity record SHA256
`dd3540b98094a51f0228333134473bce97f6ae70d9dedd0bd8ed718e0cf0eaf2`;
integration process record
`9e22005c05e15a34944600b5b11e3914ec779328b9493c65ebaedfe6f24705c1`.

## Reproducing the bounded checks

Use the existing locked dependencies and already approved installed environment:
Rust/Cargo1.93.1, Node24.22.1, Windows10.0.26300 X64 qualification environment.
These are reused provenance, not tools freshly queried by this document author.
Set CARGO_BUILD_JOBS=1, CARGO_INCREMENTAL=0, both DEV/TEST DEBUG=0,
LIBSQLITE3_FLAGS empty, and TEMP/TMP to the same existing task-owned directory.
Serialize these with other heavy work. Commands below are examples of the actual
recorded invocations with private target paths replaced; they are not new runs.

```powershell
# From repository root; exact historical sources are in the table.
cargo test --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --jobs 1 --target-dir <native-target> -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features protocol-owner-tests --jobs 1 --target-dir <eval-target> --lib local_lane::owned_curated -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <eval-target> --lib local_lane::comparison::selected:: -- --nocapture --test-threads=1
cargo clippy --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --all-features --all-targets --jobs 1 --target-dir <eval-target> -- -D warnings
cargo test --locked --offline --manifest-path crates/locallore-android/Cargo.toml --jobs 1 --target-dir <native-target> --lib -- --nocapture --test-threads=1
cargo tree --locked --offline --manifest-path crates/locallore-android/Cargo.toml --edges normal,build,dev --prefix none
cargo fmt --manifest-path apps/desktop/src-tauri/Cargo.toml --all -- --check
cargo clippy --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --jobs 1 --target-dir <native-target> --all-targets --all-features -- -D warnings
# Focused historical groups:
cargo test --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --jobs 1 --target-dir <native-target> --bin locallore-desktop-spike evaluation::selected::tests -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --jobs 1 --target-dir <native-target> --bin locallore-desktop-spike resume_completed_review_tests -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features protocol-owner-tests --jobs 1 --target-dir <eval-target> --lib owned_curated::review_tests::budget_review_tests -- --nocapture --test-threads=1
# From apps/desktop; cached dependencies, no install.
node check-selected-evaluation-controller.mjs
node verify-frontend.mjs
node node_modules/prettier/bin/prettier.cjs --check 'ui/*.{ts,tsx,html,css}' '*.{json,mjs}'
$env:LOCALLORE_D07_SELECTED_ARTIFACT_ROOT='<artifact-root>'
$env:LOCALLORE_D07_SELECTED_TARGET_DIR='<native-target>'
$env:TEMP='<task-temp>'; $env:TMP='<task-temp>'
node selected-evaluation-harness.mjs
# Restore normal application assets and executable after any dev harness.
node build.mjs
cargo build --manifest-path src-tauri/Cargo.toml --locked --offline --jobs 1 --target-dir $env:LOCALLORE_D07_SELECTED_TARGET_DIR
```

The launcher requires clean source and an absolute artifact root; it creates
one UUID cohort, builds the harness frontend and dev-harness native binary,
then launches two fixed hidden/unfocused app stages. Current expected minimums
are154 initial /160 restart recorded check entries and20/21 actual captures.
UI5 met those requirements as recorded above. Its own child environment uses the fixed
development-only background-timer-throttling flag; it changes no registry,
desktop focus, security setting, debugging endpoint or production browser flag.

The selected harness additionally requires the existing comparison harness and
LOCALLORE_D07_SELECTED_HARNESS=1, exact native synthetic workspace layout and
dev-harness build. It offers only fixed hold/release/deny consent, consent-status
and lost-start-ack scenarios. Consents are explicitly synthetic dev doubles;
the normal Windows native Yes/No dialog was not automated or qualified here.
CapturePreview captures the application's WebView, not the desktop. Semantic
snapshots are bounded selected/observer/revision/pending/receipt/error metadata.
Normal-build exclusion and restoration passed in the final cohort above;
repeat restoration after another harness run. A dev binary is not the normal artifact.

## Local evidence SHA256 anchors

Completed raw logs remain under `<artifact-root>`; do not publish their private
contents. Equal UI1/2/4 outer-log hashes reflect identical launcher error text,
not identical runs; per-cohort report/execution hashes distinguish them.

| File / cohort report | SHA256 |
|---|---|
| d07-selected-consumer-native-service-first-clean.log | bfe39d66f1c4dae28e3e047d8c8327eb47f3176d9aba2e3b9e68a11ac4f689e6 |
| d07-selected-service-review-green-first.log | 4ea187c670eab6809d064faf065a43591e55557322c3c89f44624e6c25affaf2 |
| d07-completed-service-resume-first.log | a57457d96814f675d8b01bc055cae9f435c8cc1425a3d0bd172418349606ef81 |
| d07-selected-consumer-close-gate-first.log | f1875b8759828796efd66280a243d43288400b7adc904b6c50ee95a7b39ec30e |
| d07-owned-curated-first.log | c5f61faa6ea8634708bf725107f2d0d78bb79739edf573e0a2d51a02e1256e56 |
| d07-owned-curated-installed-first.log | 8ae29a148da3e025dde89213c18a4e673c064ae303fc43036f2e34a0ba270e36 |
| d07-owned-curated-budget-red-first-clean.log | a26b32300988a00f02f857b2cf1d440153521a563d612681f1716ea2582ab5f6 |
| d07-owned-curated-budget-green-first.log | fddc585f9d0541bbe3c71368362aaa6952187ffb54446266f4c609e239908875 |
| d07-owned-curated-native-integration-first-clean.log | d46fcc7185feff2b74b166b7693255b3fceac8c7ffd78ed9766d2e5dc8035fee |
| d07-selected-consumer-wired-clippy-sixth.log | 5542eefad2a686a03b6de3614768e8e0559d26a81b7e7148a7dbd586f5d03cac |
| d07-selected-ui-first/second/fourth.log (each) | 15b4b3b05ee34af76460d60eb3471aee71ab953eb958ce8c92d97379e0ced705 |
| d07-selected-ui-third.log | dd3e4fe6380828290001804b9538de008fd7feaa87cb53caeb570f3cbb8d95d5 |
| UI1 initial/report.json | 54a944c81a3002d1f51d21c90fef32568ab7d505d454029aafcd44792319756d |
| UI1 executions.json | 97fa5e5936a3e0847f8003b5ba7bc44810d6bff2b79308086bbbe457d032d949 |
| UI2 initial/report.json | 2758cce585a0e4444ae4ed4b995f9f8ed8ee434a21834c6c83732bc9f6239d3f |
| UI2 executions.json | feacf2b847a357e3f4f60498e9bb60305c085be5019a7ee0e8e1d4ecfec4e807 |
| UI3 initial/report.json | be13513a2ac2cd09b7610a84e95c2897158ea8efc461912536e1205c756c63e3 |
| UI3 executions.json | baf0ede469bffeea4e0afd5b8f2e8e24e7f7ab380cdcdea92687221345033643 |
| UI4 initial/report.json | 7d9b0e47e8994b1a0afb6c8ae7ceb2ccfc1dc59b31505265fa5c29dd0689dc16 |
| UI4 executions.json | 48123870c08aa2a3a47f36fe217c890e6560cf55b5ba915e6c0de9edaf7a0bcc |

## Handoff and remaining gates

UI5 at518 and final compatibility/installed-asset cohorts at856 passed as
recorded above; earlier failures remain retained and normal artifacts restored.

Actual direct UI resume, native-model service resume, native model UI, real
normal-build OS consent/picker interaction, performance claims, human quality
review, physical phone execution and desktop/Android semantic parity remain
unavailable. The retired-client correction has source review,29 passing mock
cases and the actual UI5 native rerun; these are separate evidence cohorts.
The next runnable D07.04 allocation is a model-free literal-control input
contract/oracle through the existing compiler and Director. Both current
policies retain mandatory state; Director frame/schema channels also require
review. `ScriptedBaseline` is a provider lane, not a transcript-only policy.
No acceptance checkbox or whole-milestone/readiness claim follows from this record.
