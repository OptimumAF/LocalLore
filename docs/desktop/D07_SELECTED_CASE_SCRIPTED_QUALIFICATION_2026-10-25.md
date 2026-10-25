# Selected-case scripted producer qualification — 2026-10-25

Refs #29 D07.06, partial prerequisite; [PR #163](https://github.com/OptimumAF/LocalLore/pull/163)
is a draft at this evidence checkpoint; owner acceptance is pending.
No whole-D07 acceptance is claimed.
Root executed every command and test reported below. This documentation author
read source, terminal logs, process records and hashes only; no tests, builds,
formatter, provider, app, device or desktop automation were executed here.
[Documentation claim](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6396171090)
owns this sole new file on isolated `docs/d07-selected-scripted-qualification`.

## Source and supported boundary

Accepted dependency is main `782c068938534b987e7195226ea41f6d0d92d5df`
(selected-recovery prerequisite PR #159). Candidate is
`2838cef87b4bfb6d916f76461caba79df8536ebc`. Its production correction is
`6bbbb9077ee2ccff29339aef82e7a63b2fffe3ce`; `0a0a8075` formats the patch,
and `2838cef8` changes a test error-observation idiom without changing errors
or assertions. Earlier result sources remain identified individually below.

The candidate changes 13 paths: evaluator `local_lane.rs`, comparison modules,
eight new test modules/binaries and the frozen selected-case contract. This
qualification adds the fourteenth path. The post-matrix guide update
`09ed`/Root `5a3373a9` adds README:15 proposed PR paths in total; its contract
status edit changes an already counted path. Those documentation changes do
not relabel the qualified source or frozen contract hash. Core, Store, schemas, runtime,
desktop UI and Android production files are unchanged. The Android dependency
graph at `e0d2899b` excludes `locallore-eval`; that command is not an Android
build or runtime check.

The [frozen contract](D07_SELECTED_CASE_SCRIPTED_CONTRACT_2026-10-25.md) defines
trusted native Rust functions `prepare_selected`, `run_selected`,
`inspect_selected` and `resume_selected`. An opaque, nonserializable,
non-Clone plan retains the freshly opened source lock/pins and actual typed
inputs. `SelectedLane` has only `ScriptedBaseline`. No renderer token, arbitrary
callback, CLI execution request or report JSON grants this capability.

Protocol 2 sources produce a distinct closed selected manifest/report version 1,
lane `scripted_selected_case`, zero to two actual rows. Selecting either arm
selects the original corpus index in both arms, retaining original request,
scope, head, policy and accepted prefix. Paired cases use their validated
reference prefix; rollout cases preserve actual per-arm divergence. They do
not regenerate earlier turns, import canon into a live story, or write source.

Preparation reuses only the snapshot of the capability newly opened within
that call. Consuming run/resume repeat full fresh source validation before
mutation. Both destination Stores, checkpoints and resource limits must pass
before either invocation is reserved. Existing Host/Store/Play2.5/compiler2,
forwarded-budget1 and actual command validation remain authoritative.

The selected checkpoints and ledgers are durable. The current GUI reader's
capability/progress remains in memory; this packet does not wire selected
execution to native IPC, GUI consent, rendering or a real-model provider.
Report `completed` means both attempts finished, including failures, guards,
dependency blocks or cancellation; it does not mean quality accepted.
`human_reviewed=0`, `human_rubric=not_reviewed`, `quality_accepted=false`.

## Authority, persistence and resource checks

Source/destination must be ordinary, pinned, disjoint paths. Single-link checks
cover existing root and arm files, refusing a destination that aliases source
through a hardlink. The Windows fixed FFI and Unix link-count guard are local
preflight checks under cooperative ownership, not OS-wide immutability.
Manifest/checkpoint hashes detect drift; they do not authenticate an adversary
who rewrites all evidence. JSON reports and escaped inert HTML are bounded
2 MiB, selected manifest 128 KiB and checkpoints 256 KiB.

Original inputs come from actual Store history and validated completed cuts.
The common `load_turn` now compares every checkpoint to actual Store request
and terminal outcome: a committed Store requires a committed checkpoint with
matching receipt heads; a failed/rejected Store permits failed status; Draft
refuses; allowed no-Store/dependency outcomes stay noncommitted with
`before_head == after_head`. Contradictions return `CheckpointOutcomeMismatch`.
Source open and selected inspect/resume share this validator.

Before reserving, selected execution computes actual committed recoveries and
which missing arms require generation. Both ledger preflights use the existing
counter math: at most 32 invocations, 32 admissions, 96 reserved roles and
1,800,000 active ms per arm; preparation reservation 120,000 ms, turn 60,000 ms,
cleanup 3,000 ms. Required generation must still fit after preparation and have
capacity for three roles. Unknown reservations remain charged, without refund.
Actual recovered commits require no new factory/role admission. Only measured
other-arm intervals are excluded from each arm's active time.

Committed checkpoint-loss recovery consults the actual Store before a factory.
Missing historic role/capture/metrics/timing evidence stays unknown; an elapsed
zero sentinel is not a measured inference latency. Failed finished halves are
retained while only missing work runs. Completed resume is byte-inventory
read-only: no provider, assets, invocation, report rewrite or ledger mutation.

The fixed `cfg(test)`-only thread-local `CANCEL_AFTER_ARM`, default false,
cancels after an actual turn/checkpoint is retained. Its tests reset it through
RAII. It introduces no production/app/dev hook, supplied closure, environment
command, IPC, file/code/shell execution or server. It tests a retained boundary,
not a live provider's cancellation or OS process death.

## Retained failures and corrections

Times below are Cargo-reported test time; build times are stated separately.
All are coordinator executions on immutable sources recorded by process JSON.
No frozen behavior assertion was weakened to obtain the listed results.

| Evidence suffix after `d07-selected-scripted-` | Executed source | Actual result |
|---|---|---|
| `first-red` | `a51e6c82` | E0432, selected module absent; no behavior tests executed. |
| `first-green` | `f1377ea7` | Six public groups pass,567.87 s; build5.82 s. |
| `alias-first-red` | `68a47512` | Fixture fails before linking: actual Play receipt timings differ,68.93 s. Not an alias behavior failure. |
| `alias-corrected-red` | `382560cf` | Real hardlink established;0 pass/1 fail,198.73 s. Source pair09 and14 destination paths mutate. |
| `alias-first-green` | `18186896` | Same corrected hardlink oracle passes,136.43 s; build5.97 s. |
| `private-first` | `0100d76f` | Four groups pass,333.00 s; build5.37 s. |
| `divergent-first` | `f4f861fa` | Actual divergent-rollout group passes,13.96 s; build5.23 s. |
| `lifecycle-first` | `ec5d8d94` | One group covering both arm orders passes,285.15 s; build5.42 s. |
| `first-clippy` / `second-clippy` | `68a47512` / `7b8c0821` | `needless_range_loop` in production, then test loop; both retained exit101. |
| `first-format` / `third-clippy` | `ec5d8d94` / `a21609a0` | Format exit1; format-only correction then strict Clippy exit0,6.76 s. |
| `final-historical` / `final-library` | `e0d2899b` | Three genuine historical tests pass9.91/3.12/11.60 s; library59 pass/1 existing ignore,614.33 s. |
| `preflight-first-red` | `cd85741c` | Two failures,153.80 s; build7.49 s. Contradictory failed checkpoint/committed Store permits inspect/resume and14 destination mutations; insufficient right capacity permits left commit and11 mutations. |
| `source-outcome-first-red` | `a0e98677` | Independent common-source contradiction permits inspect/open;0 pass/1 fail,1.33 s. |
| `source-outcome-first-green` | `6bbbb907` | Shared validator oracle passes,1.12 s; build5.58 s. |
| `preflight-first-green` | `6bbbb907` | Both unchanged preflight oracles pass,154.51 s; fault inventories unchanged. |
| `preflight-clippy` / `preflight-clippy-corrected` | `0a0a8075` / `2838cef8` | Test `manual_inspect` exit101; equivalent `.inspect` correction then strict Clippy exit0,6.34 s. |

The first `e0d2899b` final matrix was deliberately held before public/native
stages after independent findings. Its parent orchestrator exit1 is a
candidate-held decision, not a failing library test. Those results do not
qualify the later production fix. Historical source/fixture/logs remain intact.
Root observed the parent exit in turn-local tool output; it has no independent
file hash in the log inventory below. The completed per-stage logs are hashed.

The four private groups use actual producer/Store history to test unselected
required-capture corruption before destination creation, exhausted entry clock
before invocation, unknown preparation charges without other-arm mutation,
and failed-left/missing-right recovery plus completed read-only retry. The
divergent fixture uses an actual failed WrongCommand attempt, not renamed
paired output. Lifecycle tests preserve the first retained commit in both
index-dependent arm orders and generate only the missing half on resume.

## Candidate matrix at `2838cef8`

The final serial matrix is terminal, all stages exit0, with clean source
`2838cef8` and `terminalSourceUnchanged=true` throughout. Only terminal logs
were read/hashed. It began at09:46:21.7396176Z and ended10:27:56.6659076Z.

| Stage | Actual source-bound result |
|---|---|
| Evaluator format | Exit0. |
| Three opt-in genuine historical tests | Pass11.60/3.99/15.38 s; build7.58 s. Reader binary has8 filtered tests; other two have0 filtered. |
| Complete evaluator library |62 pass/0 fail/1 existing asset-dependent ignore/0 filtered,827.17 s; build5.60 s. |
| Legacy runner, resume-basis and reader binaries |22 pass/0 fail/1 default historical ignore/0 filtered: reader8 pass224.60 s; resume-basis5 pass507.95 s; runner9 pass217.68 s. Build3.81 s, parent exit0/source unchanged. |
| Six public selected groups and hardlink group |7 pass/0 fail/ignore/filter: alias1 pass128.55 s, public6 pass477.60 s; build1.81 s. Parent ends10:27:01.8261989Z. |
| Full frontend, frontend format, Rust format |All exit0. Strict TypeScript/schema/controller/headless checks pass; no development journey/control hooks in normal frontend. |
| Native all-target/all-feature Clippy; default native build |Both exit0; Cargo18.72 s/18.07 s respectively. No native Rust test or app execution in these stages. |

Frontend output separately identifies99 synthetic V2 decoder checks,8
controller V2 routes,116 author checks,76 retention checks and67 comparison
reader checks, with mocked transport/no native rendering. Other existing
frontend suites also pass; these overlapping labels are not summed into an
invented unique-test count. This does not expose selected execution in UI.

Normal artifact manifest records `normalFrontend=true`, `nativeFeatures=[]`:
`app.js`525,441 B, SHA256
`f387418355885ecb025326284ea767a03c008215ff2e66d01795e220a634d0a2`;
`locallore-desktop-spike.exe`32,237,056 B, SHA256
`000986842555306264273a1b9f7a56e81eebd2b4fa9dc08e9ca798be85e9dd00`.
These identify restored normal build outputs, not launched-app evidence.

The genuine retained33356 cohort predates forwarded-budget fields. Tests open
its original bytes, refuse new selected preparation/resume for source mismatch,
and compare inventories. They do not strip current fields to manufacture old
history. The default ignored historical test is an explicit opt-in local-data
gate. Asset-ownership ignore is separately identified in library output.

## Reproducible environment and commands

Root reused already measured Windows 11 x64 build 10.0.26300, Rust/Cargo 1.93.1,
Node 24.22.1 and PowerShell 7.6.5; no upgrade or fresh hardware/version query was
performed by this author. Existing cached dependencies only, no downloads.
Evaluator target is source-owned `<task-root>/d07-selected-scripted-eval-target`;
native compatibility uses `<task-root>/d07-comparison-reader-native-target`.
`TEMP`/`TMP` name `<task-root>/memory-controls-temp`. Exact commands/UTC start,
end, source-clean and unchanged flags live in companion `*-process.json`.
Public paths below are placeholders, not a request to read unrelated resources.

```powershell
$env:CARGO_BUILD_JOBS='1'; $env:CARGO_INCREMENTAL='0'
$env:CARGO_PROFILE_DEV_DEBUG='0'; $env:CARGO_PROFILE_TEST_DEBUG='0'
$env:LIBSQLITE3_FLAGS=''
$env:TEMP='<task-root>/memory-controls-temp'; $env:TMP=$env:TEMP
# Run from the candidate checkout; <eval-target> is the source-owned target.
cargo fmt --manifest-path crates/locallore-eval/Cargo.toml --all -- --check
cargo clippy --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <eval-target> --all-targets -- -D warnings
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <eval-target> --lib '' -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <eval-target> --test comparison_runner --test comparison_resume_basis_review --test comparison_desktop_review -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <eval-target> --test comparison_selected_review --test comparison_selected_alias_review -- --nocapture --test-threads=1
$env:LOCALLORE_D07_HISTORICAL_COHORT='<owned-original33356-rollout>/run'
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <eval-target> --test comparison_desktop_review --test comparison_historical_readonly --test comparison_selected_historical_review -- --ignored --nocapture --test-threads=1
# Fixed unit filters after --lib select review_tests, divergent_tests,
# lifecycle_tests, preflight_review_tests or outcome_review_tests.
```

Desktop compatibility commands use the approved Node executable directly:

```powershell
# First two from apps/desktop; remaining commands from repository root.
& '<approved-node24.22.1>' verify-frontend.mjs
& '<approved-node24.22.1>' node_modules/prettier/bin/prettier.cjs --check 'ui/*.{ts,tsx,html,css}' '*.{json,mjs}'
cargo fmt --manifest-path apps/desktop/src-tauri/Cargo.toml --all -- --check
cargo clippy --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --jobs 1 --target-dir <native-target> --all-targets --all-features -- -D warnings
cargo build --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --jobs 1 --target-dir <native-target>
```

These are synthetic frontend checks and native lint/build, not app execution.

## Retained log integrity

Logs are local `<artifact-root>/d07-selected-scripted-<suffix>.log`; process
records beside them identify exact full source SHA/arguments/UTC intervals.
SHA256 below identifies raw retained bytes, including diagnostics. Empty
successful format log has the standard empty SHA, not missing evidence.

| Log suffix | Raw SHA256 |
|---|---|
| `first-red` | `279f4e07d751c061b28f2da6e57f4826a8e610e2bfd6297fd9f67ff96b3df42a` |
| `first-green` | `44f38ee3530bc7eab49bf2845d05745d19323fab185bcf24ec31e0d28f0b672e` |
| `alias-first-red` | `4b0f6448446709812e0c61b439e49f92d82165e6d30dd09d8bba5a1a10b1a715` |
| `alias-corrected-red` | `9b51e9ae0908fbd3c03bedc921e12239088e86326a45dd512af3049ed28d830d` |
| `alias-first-green` | `2e315c81fdd39bb569911464d985cbf953430f898ee13e3758bd0b44bdc9fa0a` |
| `private-first` | `59643a0d711b9f92ec489c5106ec387b163cd4c0c585a8cd5a52cbdc0d4ce058` |
| `divergent-first` | `354e55d0c737803d0ea398b6e5e169183cd1cb0d922a67832f9b1bc682455d3f` |
| `lifecycle-first` | `b52950a8d519750d9b5e5ee980db5b20d3023bd5938ccce6edfcf59f1aac6ee7` |
| `first-clippy` | `0edbb9387ac8407db59c3f2390233ff8828f231f25c60d8db9076e463ea13aac` |
| `second-clippy` | `70a43ea40d5a89660db3666ddb7394d8b062d76d82a5472f7f6af859f84c3b38` |
| `first-format` | `5eca07a86a42e5ee31b3a164c65bebf095c0b974f349c931fe8beeeff15f022c` |
| `third-clippy` | `46b2db15edbec02d3c1a8177a0edf70d56073bae01f5d2e0151182a79ad1d8ed` |
| `final-format` / `final2-format` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `final-clippy` | `10e55c300d2ff12471e571993ef88379ff3e4af5812c317447b3b689d0f79972` |
| `final-historical` | `8da51eb2bed0681395e675da6cc84cbf9ec15b154a7553442eacd0312d475e0d` |
| `final-library` | `5cabeeab3e3376fa87fbfadbf7c2b65e1786ebc5eab191ea2e10324620447f32` |
| `preflight-first-red` | `9e67f0431fac6065b5b185d963b09a05005533609b96c3dd2ae6cf0a02469744` |
| `source-outcome-first-red` | `e56392f1b46b33f71d0d38e8b88ecf2da6d451916d145f75d462ba65da8af478` |
| `source-outcome-first-green` | `cf878356d9462eaf33332ad8de958efcf16d549b9d20bfccc94b185c863c15ad` |
| `preflight-first-green` | `526d2754ae4dcdcf63c4572197664ee048183f5ee9b421602fe60bbe90d10450` |
| `preflight-clippy` | `b7b84d411b122947c5081b2d4b9fd8a29c407ed8e3b5a7e791aa848ac83b848b` |
| `preflight-clippy-corrected` | `c4567015698d8dca53f032238fae8e9750decd360c34390ab6f199c5359225ea` |
| `final2-historical` | `4dbdde72c5a6fb5fa113c46fe3afa34d699d8889657ff088c0cf8435183dde48` |
| `final2-library` | `d1858ff5f43c20d104395f1579ba27a940fff636b1a608fd57298287b2311539` |
| `final2-legacy` | `cec62b77e75eba7486b640877beebea51afa3fdc420b39b951af6977918bc13a` |
| `final2-public` | `f39e21904057abcda5799b0076db743a50ff3c0d69b32ff40ac93441a2925980` |
| `final2-native-frontend` | `32a1137ae707f7d06eedf39e686a5a34a4948152b5e4248cedc350ce4e1348ed` |
| `final2-native-frontend-format` | `f20510a9da4717c51c4cffee6d0dd88d6c9a723d0a83711d01216f5b48961283` |
| `final2-native-rust-format` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `final2-native-native-clippy` | `758c2e9bf6a7d081bdfc45c5c09a079e05ce811b253e9274196956ceec125cf6` |
| `final2-native-native-normal-build` | `377937fa625934c188396164c96e3da692d05d0f989732639f97f5f559d7e295` |
| `android-dependency-graph` | `0eb1445c466c9fad0e2badef6546a9f60b9ee348b303cfc0544e6296e37442d4` |

Final native `-results.json` SHA256:
`504d9414748e786ee244693cca783d5c716cfaf103131678fe201e3fd3b2d0a7`;
`-build-artifacts.json` SHA256:
`d747f04404e84be9ff9df58a096fca3e1e89fa626633c649cbe05cfd3483a452`.

Candidate source-byte SHA256 pins (repository paths under
`crates/locallore-eval/src`), cross-checked equal to the coordinator's clean
`2838cef8` source, not generated model or save artifacts:

| Path | SHA256 |
|---|---|
| `local_lane.rs` | `fc0123029f876fc96a9c4b70f878ceb6d6ced738038873a72a2f2bcb663842d4` |
| `local_lane/comparison.rs` | `22c71f5e4e48e899a037d63607e75b896e11f4e5823b0b7a1c6a909665960a61` |
| `local_lane/comparison/desktop_api.rs` | `5b571a451d00abdedca1362d2d0ff44294f1872eb48d46aeb09682eaadc8b9b9` |
| `local_lane/comparison/selected.rs` | `4a666e4ce40e02ae8279c745e3de74643a9802e4db507396da3bf9384297a3a4` |

Frozen contract SHA256 at exact candidate `2838cef87b4bfb6d916f76461caba79df8536ebc`
(later documentation status updates are separate source):
`8392b7fc6ad5e44176c5fb0959cdba2b7a45ea00ff8bb9c3e512269e7018205e`.

## Review and remaining gates

Independent [alias/FFI review](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6395389622)
checks the Windows fixed layout and lifetime, with cooperative-race limits.
[Driver review](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6395876227)
identified the two preflight defects before their frozen execution.
[Fix review](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6396123369)
found no additional concrete defect within that correction.
[Final source-only review at exact2838](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6396324364)
found no new actionable counterexample within the frozen selected-driver scope.
Suggested additional Draft/Cancelled-vs-failed vectors are unrun suggestions,
not extra passing tests or acceptance gates. These are source-only reviews,
not human approval or independent runtime execution.

Native selected provider execution, explicit GUI consent/job ownership,
pending-provider/late-commit native lifecycle, selected IPC/WebView snapshots,
Android/device parity and human narrative-quality assessment remain separate.
No model calls, asset loading, downloads, app launch or device action belongs
to this scripted qualification. Earlier comparison model scores and reader
renders retain their original sources and do not qualify this producer.
The next runnable gate after coordinator acceptance is a separately frozen
native selected-execution/ownership contract and its meaningful tests.
