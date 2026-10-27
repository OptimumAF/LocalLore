# Scripted literal/Relevant comparison producer qualification

Scope: D07.03/.04/.05/.06 supporting implementation and M07.01. Accepted base
PR188 / `97d1f670`. Production source `71c73d91` is locally qualified by the results below. No whole milestone or human quality gate is accepted by this slice.

## Delivered boundary

`comparison::literal_v3` runs the original 24-attempt Courier suite through the
existing durable Host, Store, passive recorder and resource Ledger. LEFT uses
Host construction `PlayerLiteralV1`; RIGHT uses `Memory(StateRelevantMemoryV1)`. Each has its
actual descriptor in protocol3. This is explicitly scripted inference.
Native protocol3, selected-case protocol3 and desktop UI exposure are unavailable.

The fixed CLI is `literal-comparison reference|run|resume|inspect`. Reference
creation deliberately reuses the existing opaque validated reference owner and
its version2 actual accepted receipts. It is not a relabeled literal run. Both
paired snapshots and independent continuous rollouts use those original inputs;
paired starts verify the complete semantic input and actual reference prefix.
Four six-attempt scenes alternate the first arm. Separate Store files never touch
live stories. A complete rollout records 48 rows:42 accepted and6 guard-only,
with84 scripted role calls. Those counts describe that run, not all test fixtures.

The new typed manifest/binding/row/report3 have closed keys, required nullable
fields and exact arm/profile/version validation. Source-fingerprint-only drift under an otherwise supported closed protocol recipe
remains readable as `source_matches=false`; it cannot authorize resume. Unsupported
format, profile or construction tuples are refused. Literal memory-only
metrics are null, including mandatory-memory fingerprint, optional-memory detail,
selected context bytes, token estimate and memory fallback reasons. Literal
source/selected counts come only from validated actual capture. A guard or
unmet dependency is explicitly not applicable; missing/recovered input is
unavailable. None is positive evidence that literal generation ran.

One private shared `turn_execution` module owns actual Host construction,
provider/recording, absolute watchdog/cancellation, Store outcome reads and
checkpoint validation. Existing v2/selected wrappers retain their codecs. Actual
checkpoints are durable before settling reservations. Unknown calls retain full
reservations and unknown role counts. Both existing Ledgers preflight before
either new invocation reservation: known RIGHT exhaustion no longer creates an
avoidable unknown LEFT reservation, including on the existing v2 path.

Cold inspection reopens actual Store request/phase/receipt boundaries, validates
raw hashes and ledger files, rechecks full literal Core rendering, binds any
checked committed candidate to the actual Store receipt, and rebuilds the row.
It creates no invocation, provider or repair. Completed resume is also read-only.
Missing committed checkpoints recover actual receipts without generation, but
remain failed/unavailable with unknown historical roles and no invented counts.

Setup metadata is scripted-only, bounded and linked to actual preparation
reservations. Its version3 decoder requires all eight keys, including explicit
null load, and advancing right invocation identities. Unknown gaps retain their
charges; a setup cannot reuse or reorder a previous pair. The root enumeration
is bounded to256 entries and setup names00..31; both reservation references must
exist with exact preparation identity/budget. Historical v2 setup decoding is
unchanged.

## Execution and test provenance

Windows x64 NT10.0.26300; PowerShell7.6.5; Rust/Cargo1.93.1
(rustc01f6ddf75/cargo083ac5135, LLVM21.1.8); Node24.22.1. Existing dependencies,
locked/offline, one build job, incremental/debug information0. No install,
SDK/ABI/device/emulator/ADB, model asset or external service is needed.

Frozen source packets precede their corresponding implementation:

- Original twelve-row v2 projection `07e8f76a`, captured before any mechanics
  edit and anchored `ea999158`; PASS1/5.11s. All row fields except the explicit
  live timing/trace/capture/recording/receipt hash and role-metric fields remain.
  Projection18505 bytes/SHA256
  `9134ccc9609b3f9c5942c04f8c2c9fe1e008e962bcae537b42139e0e4642a065`.
  It passes after the first shared extraction at `c23aed84` (5.08s).
- Public six-group packet `0a9bb31b` (integrated `f0bd573c`) first observes the
  missing API at compile time. Initial actual execution `d407c264` PASS6/216.08s:
  genuine reference/paired starts, rollout12->24->48, preserved old evidence,
  cold/completed read-only resume, committed lost checkpoint, metadata/raw/capture
  tamper refusal, cancellation before creation and v2/selected refusal of v3.
- Root lifecycle `91ce27de`: actual pending Director cancellation passes without
  canonical commit; invalid kind/reference combination demonstrates RED.
  Fixed `6332a5b2`, both tests PASS2/.67s.
- Actual CLI test `519c66eb` demonstrates missing command behavior, then the
  closed route is implemented. Children are fixed application-owned binaries;
  Windows tests request CREATE_NO_WINDOW. They exercise no desktop input/window.
- Three resource tests `a4a37710` (registered `a1d0f6ca`) demonstrate RED3/9.51s:
  known RIGHT exhaustion writes LEFT invocation01; absent RIGHT setup reference
  is accepted; setup32 is ignored. Fixed `e73dfe0c`, GREEN3/9.67s.
- Final bounded metadata packet `dc1a2e31` (adopted `0f939e9c`/`e5ddd650`):
  repeated valid RIGHT invocation and omitted explicit-null load demonstrate
  RED3pass/2fail28.17s. Fixed `71c73d91`; all5 cases GREEN27.21s. This changes
  only the version3 reader; no historical v2 decoder requirement is tightened.

Retained integration failures also include the first extraction missing its
moved request variable (corrected `c23aed84`) and two strict-lint findings:
redundant result pattern and production CLI after an inline test module. Neither
was suppressed. Original capture sentinels are reference capture, not behavioral
RED. Exact compiler/fixture failures remain local with the successful evidence.

## Final checks

Final production source is `71c73d91`. The prior broad cohort at `6f9ba87a`
completed with every process exit0 and clean/unchanged terminal source. The last
change adds only strict version3 setup decoding; affected checks repeat below.
Evaluator tests use `local-model` compile feature unless the table says otherwise;
Android and frontend checks do not enable it. Documentation-only commits after
this source do not change Rust/TypeScript or the source-input fingerprint.

| Check / source | Actual result |
| --- | --- |
| Literal/capture/old v2 producer + lifecycle/resource, `71c73d91` | PASS26/34.67s; the four old-v2 CapturedContext stable semantic-result projection hashes (package, both prompt lists, estimates) and the twelve-row producer projection are unchanged. |
| Public producer + actual CLI seven journeys, `71c73d91` | PASS7/225.02s. Previous `6f9ba87a`:PASS7/221.22s, command229.61s. |
| Genuine retained UI5 comparison + selected inventory/source mismatch, `71c73d91` | PASS1/14.70s. Previous `6f9ba87a`:PASS1/15.24s. |
| Forwarded budgets, `6f9ba87a` | PASS8/10.04s. |
| Existing clocks, `6f9ba87a` | PASS14/6.54s; one explicit approved-assets ownership skip. |
| Existing dependencies, actual outcome, selected recovery, `6f9ba87a` | PASS4/.27s, PASS1/1.26s, PASS3/.63s. |
| Evaluator all-target strict Clippy and format, `71c73d91` | FormatPASS; strict ClippyPASS10.69s. Previous strict Clippy6f:PASS10.00s. |
| Complete frontend/type/controller/normal-hook exclusion, `71c73d91` | PASS10.77s command (initial6f16.80s); actual controllers use synthetic transport, no browser/native rendering. |
| Native all-feature/all-target Clippy + normal default build, `71c73d91` | ClippyPASS10.73s; normal buildPASS19.90s. Previous6f:PASS11.41s/18.66s Cargo. |
| Android Rust host and dependency graph, unchanged Android/Core `6f9ba87a` | PASS20/1.70s; graphPASS/.29s command, no Tauri/evaluator/local-runtime edge. No Android file or dependency changes in later setup correction. |
| Version3 library without local-model feature, `71c73d91` | PASS7/29.20s; no optional local runtime feature or model assets. |

The ignored clock method is
`public_comparison_rejects_a_real_preowned_native_before_admission`, requiring
explicit approved assets. It is not counted as a pass or a native3 run. Whole
workspace/core, physical phone, GUI/rendering and real-model gates are not newly
executed for this evaluator-only change. Exact local process records/logs use
`d07-literal-producer-final-*` and `final2-*`; both cohorts are terminal with exit0 and clean/unchanged source. Logs and
process records remain local; no raw diagnostics or machine paths are uploaded.

No real model or native WebView is executed here. CLI tests are actual compiled
Windows process execution of the Rust evaluator, not Tauri native IPC or app
rendering. Controller checks use synthetic fixtures. Native Clippy/build and
Android Rust host/graph checks are compatibility evidence, not new native UI or
device execution. No frontend rendering change is introduced, and prior UI5
images retain their original source and evidence class.

## Reproduce with cached dependencies

Substitute ordinary task-owned absolute target/output/temp paths. Run serially.
The scripted lane requires no local-model feature or assets; the qualification
cohort also compiles the existing optional feature used by the desktop reader.

```powershell
$env:CARGO_BUILD_JOBS='1'; $env:CARGO_INCREMENTAL='0'
$env:CARGO_PROFILE_DEV_DEBUG='0'; $env:CARGO_PROFILE_TEST_DEBUG='0'
$env:LIBSQLITE3_FLAGS=''; $env:TEMP='<owned-temp>'; $env:TMP=$env:TEMP
cargo run --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --target-dir <eval-target> -- literal-comparison reference <new-reference-dir>
cargo run --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --target-dir <eval-target> -- literal-comparison run <new-paired-dir> --kind paired --lane scripted --reference <reference-dir> --max-scenes 1
cargo run --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --target-dir <eval-target> -- literal-comparison run <new-rollout-dir> --kind rollout --lane scripted --max-scenes 1
cargo run --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --target-dir <eval-target> -- literal-comparison resume <rollout-dir> --kind rollout --lane scripted --max-scenes 4
cargo run --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --target-dir <eval-target> -- literal-comparison inspect <rollout-dir>
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <eval-target> --test literal_comparison_v3 -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <eval-target> --lib literal -- --nocapture --test-threads=1
cargo clippy --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --all-targets --jobs 1 --target-dir <eval-target> -- -D warnings
cargo fmt --manifest-path crates/locallore-eval/Cargo.toml --all -- --check
```

run/resume exit1 for failed/unavailable evidence; misuse/refusal exits2. Inspect
returns the actual report without turning failures into success. Local JSON and
escaped bounded HTML retain synthetic narration and private diagnostic copies;
keep generated directories local and ignored. No live private story is accepted
as a scenario input and no model/runtime path is accepted by this scripted CLI.

Additional executed compatibility commands (the same environment/targets):

```powershell
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <eval-target> --lib forwarded_budget_tests -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <eval-target> --lib local_lane::comparison::clock -- --nocapture --test-threads=1
# Repeat this library command with dependency_review_tests, outcome_review_tests,
# and selected_recovery_tests as the filter; exact results are in the table.
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --jobs 1 --target-dir <eval-target> --lib literal_v3:: -- --nocapture --test-threads=1
$env:LOCALLORE_LITERAL_HISTORICAL_COMPARISON='<genuine-preserved-UI5-comparison>'
$env:LOCALLORE_LITERAL_HISTORICAL_SELECTED='<genuine-preserved-UI5-selected-work>'
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <eval-target> --test literal_control_historical_review -- --ignored --nocapture --test-threads=1
node apps/desktop/verify-frontend.mjs
cargo clippy --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --all-targets --jobs 1 --target-dir <native-target> -- -D warnings
cargo build --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --jobs 1 --target-dir <native-target>
cargo test --locked --offline --manifest-path crates/locallore-android/Cargo.toml --jobs 1 --target-dir <native-target> --lib -- --nocapture --test-threads=1
cargo tree --locked --offline --manifest-path crates/locallore-android/Cargo.toml --edges normal,build,dev --prefix none
```

## Limits and next gate

The scripted provider follows fixed scenario commands. A passing mechanical run
is not a model's understanding, retrieval use, narrative quality, distinctiveness,
privacy proof, performance result or human review. Literal and Relevant arms
intentionally receive different information channels; no invented opening or
mandatory-memory-fingerprint equality is imposed on Literal. Narrator input
remains grounded; sentinel/hash consistency is not semantic authentication.

The entire source/row/Store/raw/ledger validation is finite evidence. Hashes do
not authenticate an adversarially rewritten run. Old unknown work is never
refunded or reconstructed as successful inference. Existing source/version2 and
selected1 formats remain separate; neither can consume protocol3 implicitly.

Next: qualify the separately owned native3 runtime/resource entry, real paired
models, retained v3 inspection/selected integration and desktop consumption.
Human rubric, whole-app memory/performance, portability/device and packaging
requirements retain their own gates. Full D07/M07 and epic21 remain open.
