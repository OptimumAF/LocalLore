# Domain2 fork native harness: code verification

Refs #30 D08.04/.07, #12 M08.04/.06 and PR290. This records development
harness code checks, not a native app run. The [native contract](D08_DOMAIN2_FORK_NATIVE_CONTRACT_2026-10-30.md)
and [earlier consumer verification](D08_DOMAIN2_FORK_CODE_VERIFICATION_2026-10-30.md)
retain their separate evidence. No application was launched in this cohort.

## Source and review

Independent Native12/Rust3 FIRST was frozen at `0abc6d66` before the different
author's Rust producer `56cb9908`. Independent finalization29 FIRST was frozen
at `4b4a03ba` before Root's helper and the different author's UI producer
`c9ff3c16`. Root integrates these on `impl/d08-domain2-fork-integration-v1`.
The recipe uses existing Engine/Store, Main controllers, broker/lease and IPC;
it introduces no production persistence, inference or memory implementation.

The Rust unit tests use one retained synthetic SQLite fixture, public Core/Store
fingerprints, closed development flags/actions and the existing artifact writer.
Frontend helper tests execute the actual helper and extracted owner with a
synthetic finish port. Launcher tests execute extracted actual JavaScript with
memory filesystem/process doubles. Native/TS route assertions are source checks.
None of those categories establishes native IPC, mounted WebView behavior,
rendered pixels, focus or process-tree containment.

Source-only independent UI/helper review at `9cb45698` found no actionable
finding. A separate source review at `a633c20b` found no actionable issue in
the closed launcher-mode correction or workspace fixture calibration. Reviewers
ran no compilation, tests, app, rendering or resource inventory.

## Preserved failures and corrections

- At baseline `475ce56e`, Native12 executed9:1 pass,8 fail,3 unrun; finalization29
  executed0 with29 unrun and2 setup errors. These are setup-aware baselines.
- TypeScript initially reported5 unknown-type errors. `0b64800c` changes the
  throwing helper to a `never` function declaration; validation is unchanged.
- The old path checker executed0/38 because its extraction expected the former
  signature. Independent `19790222` accepts the exact optional-mode signature,
  retaining all38 behavioral predicates. The corrected38 execute and pass.
- Native12 initially executed12:8 pass,4 fail. Three expose a real product bug:
  the decoder's initial mode allowlist omitted the new fork mode. Root
  `1a189512` adds only that closed mode, preserving legacy modes, record grammar
  and limits. Independent `5c643e1c` supplies missing base/deterministic UUID
  inputs in the workspace VM fixture, retaining all12 expectations/predicates.
  The resulting Native12 executes12 and passes12.
- Finalization29 initially executes29:26 pass,3 fail because its test wrapper
  feeds a top-level return to the TypeScript parser. Independent `2d16c1ae`
  strips the actual owner declarations, then appends the return inside the VM
  function body. The whole-file inverse matches its baseline; all29 assertions
  and expectations remain unchanged. Root integrates this as `1779b0bd`.

All failure logs, original sources and fixture roots remain charged and retained.
No failed run is reclassified as passing by a later correction.

## Execution environment and bounded authority

Root is the sole execution owner. Physical D checkout, TEMP/TMP and existing
Cargo cache/target are used throughout. Node24.22.1, TypeScript7.0.2,
Prettier3.9.10, esbuild0.28.2, React19.3.1, Tauri2.12.5, Rust/Cargo1.93.1,
rustfmt1.8.0, PowerShell7.6.5, Windows10.0.26300 x64. Cargo commands use
`--locked --offline`, one build job, incremental disabled and dev/test debug0.
No dependency/model download, SDK/JVM/ADB/emulator/device or OS qualifier runs.

The owner-approved code-only limits are576KiB of check records, counting both
physical storage and losslessly decoded logs;8MiB of all new fixtures; original
target baseline8,259,980,576B plus4GiB; and660MiB joint evidence. The64KiB
extension does not permit an app launch. All earlier failures, normal copies and
other cohorts remain charged. Compression never reduces the decoded charge.
Output overflow, unknown child closure, source/product/ownership changes or an
unknown/exceeded inventory stop later work. Direct-child closure does not prove
whole-process-tree containment. No evidence is deleted to fit.

## Actual checks

Commands run from `apps/desktop` with the environment above; Cargo rows below
abbreviate the additional actual `--locked --offline` flags. The ignored local
coordinator and immutable terminal/log/source records are retained under
`author-integration-artifacts/d08-fork-checks-20261030-v1` in the task-owned D root.

| Command | Actual result |
| --- | --- |
| `cargo test --manifest-path src-tauri/Cargo.toml --features dev-harness --bin locallore-desktop-spike harness::domain2_fork_native_review_tests -- --nocapture --test-threads=1` |3/3 pass;26.5340119s command |
| `node node_modules/typescript/bin/tsc --noEmit` |Pass;0.273497s |
| `node --check v2-inspector-paging-harness.mjs` |Pass;0.05584s |
| `node check-domain2-timeline-browser-native-mode-review.mjs` |47/47;0.1310482s |
| `node check-v2-inspector-paging-path-review.mjs` |38/38;0.0844205s |
| `node check-domain2-fork-native-review.mjs` |12/12;0.1198629s |
| `node check-domain2-fork-finalization-review.mjs` |29/29;0.1035118s |
| `node check-domain2-fork-review.mjs` |21/21;0.189356s |
| Full frontend/config Prettier check |Pass;2.7830004s |
| `cargo fmt --all -- --check` |Pass;2.0165904s |
| `cargo check --manifest-path ../../Cargo.toml -p locallore-android` |Pass;1.9261101s; Windows host only |
| `cargo clippy --manifest-path src-tauri/Cargo.toml --all-targets -- -D warnings` |Pass;8.6362805s |
| Same Clippy with `--features dev-harness` |Pass;9.5419851s |
| `node build.mjs` |Pass;1.0106634s; normal frontend |
| Actual existing normal-bundle verifier block only |73/73;0.0687632s |
| `cargo build --manifest-path src-tauri/Cargo.toml --bin locallore-desktop-spike` |Pass;9.9671251s; normal executable, unlaunched |

The final test/restoration source is `1779b0bd6d366971ccb95dec36a37d9a5abc2feb`.
All42 new direct-child records close:38 exit0 and4 retained ordinary failures
(the TypeScript, extraction, initial Native12 and parser-wrapper failures above).
There is no timeout, overflow, kill or new unknown. The two earlier setup-aware
FIRST baselines remain separate, not part of that42. The unchanged245 process-policy
block has an exact source-equality proof against accepted `977f3eed`;245 and
the full77-child verifier are not rerun or claimed. The normal exclusion check
executes the existing verifier's actual fixed block, original70 plus3 new
fork-specific exclusions, separately from that full suite.

Source-equivalent formatting is proven with actual direct esbuild transforms
before/after for all six frontend/check/launcher files. Rust formatting changes
only the allocated source/test paths. Later fixture calibrations have exact
whole-file inverse proofs. Final checks reuse only the changed finalization,
fork regression and style commands; they do not repeat unchanged passing tests.
The reviewed private coordinator lowers final/restoration stream caps and
preserves its8KiB terminal reserve, per-child admission and permanent STOP.
Its previous source remains exactly recoverable through a charged reversible
delta with before/after hashes. This reduces allowed output, not safety checks.

Restoration frontend SHA256
`574a665ac1448769c84293e52bc3043c474c5a4c656d79bbb253162c621b79e7`;
normal executable SHA256
`1d5142187c805a667c27ef0836de27319bae187ee9dd56882d999ae492b74014`.
Generated `fork_boundaries.toml` still grants/denies only `fork_boundaries`;
no origin/window/CSP scope is expanded. Normal readback excludes the new
journey, catalog label and oracle markers as well as the original70 markers.
Read-only process inspection finds no matching task-owned app/profile process;
this is current absence, not historical process-tree proof.

Before its final small phase record, restoration measures543,687B physical /
564,362B decoded-equivalent check records,671,744B across six new retained
fixture roots, target11,785,149,088B (growth3,525,168,512B from the original
baseline) and joint682,314,982B. Later metadata stays additionally charged.
All five failed/normal preservation copies match their admitted hashes.
Fresh final audit verifies all42 raw/decoded log hashes, the reversible coordinator
delta, current normal hashes and the named D07/D09/D05 inventories. Its exclusive
record brings check records to549,989B physical /570,664B decoded equivalent and
joint evidence to682,321,284B. The unchanged external totals are D07
501,920,772B, D09 40,267,990B and whole D05 79,500,962B. Generated audit source
and record are charged. No app/profile process is present in the read-only check.

The next gate is one separately admitted native fork journey, not an automatic
retry or the already spent browser V3 run. Its seven-success/max-eight image
ceiling,20MiB packet and8MiB writer remain prospective. Current app limits do
not fit the existing original-baseline target growth and full packet reserve.
Keep the app closed until a concrete resource decision and fresh admission.
No new native render artifacts exist to inspect. D08, the desktop epic, real
model quality, Android device, security/OS and release gates remain open.
