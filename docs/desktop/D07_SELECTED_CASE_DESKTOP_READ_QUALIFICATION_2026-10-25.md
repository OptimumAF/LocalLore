# Selected-run read capability qualification — 2026-10-25

Refs #29 D07.06 / #25 D04.02, partial. **The shared read-capability checks below
passed; desktop consumer integration remains unavailable.** Accepted base PR172 merge
`5f1a49f1e18c954f2fc6b85ed875736dd4c414ea`. Claim6401286275 owns this slice.
The [contract](D07_SELECTED_CASE_DESKTOP_CONTRACT_2026-10-25.md) separates this
implemented shared prerequisite from the unimplemented desktop consumer.

## Behavior and authority

`comparison::selected::desktop_read` retains an opaque selected-run read lock
and directory pins. `summary` returns only selection/lane/arm scope/validated
heads/availability and an opaque snapshot binding. It never returns the full
report, source Requests, profiles, outcome prose, traces or model inputs.
`evidence` uses the existing closed comparison request enums and the extracted
common Store/Query2/raw-artifact renderer. Native inspection permission is still
the caller's responsibility; actor raw requests are denied before binding/file
probes. Read permission never grants execution or changes character knowledge.

Every permitted read freshly validates both arms and requires the same manifest,
full checkpoint/report snapshot and exact bounded accounting-file seal.
Aggregate-cost equality alone cannot hide offsetting settlement edits. An old
capability never silently rebinds. These hashes detect drift, not adversarially
authenticate a rewritten experiment. Missing checkpoint evidence remains
explicitly unavailable, even when its Store contains a real committed outcome.
No checkpoint recovery/write, generation, model assets or source run is required.

## Executed checks and source boundaries

Production was introduced at `8ca63d0a`; the missing-response size fix is
`c5944faf2ff4e55b48ba7ef0beaca6617ec95f7f`. Through `cf33d3a1` later Rust changes
are test registration/new frozen tests and formatting only. All checks below
were locked/offline, jobs1, incremental/debug info disabled, serial tests and a
source-owned target. Each recorded command required a clean, unchanged source.
Logs and process records remain local and gitignored.

| Source | Actual check | Result |
| --- | --- | --- |
| `8ca63d0a` | Evaluator `cargo check`, local-model | PASS 2.56s |
| `8ca63d0a` | Existing full comparison reader / authorization / snapshot public targets | 8 PASS/1 genuine-history opt-in skip 210.67s; 2 PASS 14.68s; 4 PASS 29.72s |
| `2cf35125` | Frozen missing-response bound regression | RED, 0 PASS/1 FAIL 8.64s: 262526 bytes exceeded 262144; inventory assertion passed |
| `c5944faf` | Same bound regression, shared cap helper applied | 1 PASS 9.05s; assertions unchanged except rustfmt wrapping |
| `c5944faf` | Existing immutable Core edge-binding unit tests | 4 PASS 3.77s |
| `042378c7` | Initial five selected-reader groups | 4 PASS/1 fixture FAIL 46.21s, described below |
| `90f836b0` | Corrected selected-reader groups plus bound case, local-model | 6 PASS 60.32s |
| `90f836b0` | Same six groups, feature-off | 6 PASS 57.90s |
| `c1d245d0` | Genuine prior-native selected read capability, feature-off | 1 PASS 27.01s; opens twice, complete inventory unchanged |
| `90f836b0` | Desktop native all-features tests | 123 PASS/1 existing Windows privilege skip 159.39s; harness contracts 2 PASS 0.01s |
| `cf33d3a1` | Offsetting genuine invocation settlements, equal whole report/charges | 1 PASS 20.67s |
| `cf33d3a1` | Evaluator all-target/all-feature Clippy, warnings denied | PASS 9.76s |
| `d8be05de` | Same accounting regression, feature-off | 1 PASS 20.47s |
| `d8be05de` | Same genuine native-history read test, local-model | 1 PASS 22.90s |
| `d8be05de` | Android Rust-host tests / normal-build-dev graph | 20 PASS 1.65s; graph excludes evaluator/local runtime |
| `d8be05de` | Full frontend verification / frontend format / native workspace format | exit0; 10.14s / 2.33s / 2.12s command elapsed |
| `d8be05de` | Native all-target/all-feature Clippy / normal build | exit0; 10.50s / 15.48s command elapsed |
| `d8be05de` | Separate evaluator workspace format check | exit0 |

The six-group runs and later single accounting case cover seven distinct new
groups through complementary executions, not one seven-test run. Existing-reader
14-case preservation was not repeated after the small shared cap-helper
extraction; later checked-edge, selected-reader, native-host and lint/build checks
are separately attributed above. All production Rust bytes after `c5944faf` are
unchanged; later differences are tests, cfg(test) registrations and Markdown.
Frontend verification runs existing controllers with mocked IPC/headless DOM,
strict TypeScript, build and normal-bundle hook exclusion. It does not exercise
the new selected capability through IPC or render a new selected UI.

The first drift fixture changed a checkpoint elapsed time without changing its
bound admission settlement, so the existing validator correctly returned
`LedgerIntegrity` before the intended `SnapshotMismatch`. Reviewer correction
`659396d3` (adopted `57b3b2dc`) coherently changes both diagnostic fields and both
expected inventory entries. Original old-cap rejection/new-cap binding assertions
remain unchanged. This fixture failure is not a production regression.

The accounting test uses two actual invocation settlements produced by public
lost-checkpoint resume, offsets them by one millisecond, and proves the entire
recomputed private report remains equal. The old capability rejects; a fresh
one obtains a new binding. This is synthetic diagnostic drift, not new measured
work. Source/canonical histories remain unchanged.

The frozen tests compare actual Player/Mira/Sable Query2 pages at both Store
edges; preserve generation contexts, receipts, accepted-history basis and all
files; check raw denial before corruption/stale binding; distinguish genuine
recovery's missing capture from corrupt required capture; and require locks to
exclude another reader/resume. The native-history fixture is the genuine Move4
target from [PR172's qualification](D07_SELECTED_CASE_NATIVE_QUALIFICATION_2026-10-25.md),
not a new native run, relabeled scripted fixture or model-quality judgment.

## Reproduce

From the repository root, with an owned target directory and dependencies
already provisioned:

```powershell
# Use one owned CARGO_TARGET_DIR consistently across these separate manifests.
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --jobs 1 --lib local_lane::comparison::selected::desktop_read -- --nocapture --test-threads=1
# Repeat with --features local-model for the alternate compilation path.
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --test comparison_desktop_review --test comparison_reader_authorization_review --test comparison_reader_snapshot_review -- --nocapture --test-threads=1
cargo clippy --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --all-features --all-targets --jobs 1 -- -D warnings
cargo fmt --manifest-path crates/locallore-eval/Cargo.toml -- --check
# Existing native ownership tests require the fixed development fixture first.
cargo build --locked --offline --manifest-path crates/locallore-local-runtime/Cargo.toml --features development-worker --bin protocol-fixture --jobs 1
cargo test --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --jobs 1 -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path crates/locallore-android/Cargo.toml --jobs 1 --lib -- --nocapture --test-threads=1
# From apps/desktop, with the already provisioned frontend dependencies:
node verify-frontend.mjs
# Restore/build the normal native binary after development-feature tests.
# From the repository root:
cargo build --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --jobs 1
```

One historical test is explicitly ignored by default. Set
`LOCALLORE_SELECTED_NATIVE_HISTORY` only to the genuine previously produced
completed native Move4 target, then run `--test
comparison_selected_desktop_native_historical_review -- --ignored --nocapture
--test-threads=1`, once feature-off and once with local-model. This reads retained
synthetic evidence; it does not provision or load any model/worker.

The historical target is required only for that explicit opt-in. Default
synthetic producer/read tests create their own isolated fixtures. Protocol
fixtures are tiny local test workers; they do not qualify model weights.

Normal artifacts built at `d8be05de438f8637833b48eb4ec43653bafbf716` after native
development tests: frontend525661 bytes, SHA256
`5c7f13bc24d244396dd535002cb12beb4523aa2868f63e55584669798829d489`;
EXE32682496 bytes, SHA256
`ee06c51cd45d955b60dedf0320a8814dffa7dfaae67089f38e5a0661d6e79915`.
The build artifact record identifies native features as empty. These are local
unsigned build fingerprints, not byte-reproducibility or package qualification.

Environment: Windows x64 build26300, Rust/Cargo1.93.1, rustc01f6ddf75,
cargo083ac5135, LLVM21.1.8, Node24.22.1 and PowerShell7.6.5. No new dependency,
model, SDK, browser or tool installation/download occurred.

## Limits and next integration

No new frontend/controller/IPC command, consent, ModelManager reservation
consumer, app-owned render or native WebView execution exists in this slice.
Native tests above are Rust host/contract tests, not native window rendering.
No new model generation, UI image, quality/human review, Android device/JNI/JVM,
phone parity, network-blocked/offline-install, packaging or byte-reproducibility
claim follows. Broad evaluator suites from PR172 were not rerun here; the table
identifies the actual focused coverage, skips and preserved failures.

Next runnable task: the separately frozen desktop selected consent/job/owner
consumer, then checked DTO/controller/panel and application-owned IPC/render
qualification. Inspection-lens epochs must remain separate from generation
identity. Full D07/D04 and epic checklists stay open.
