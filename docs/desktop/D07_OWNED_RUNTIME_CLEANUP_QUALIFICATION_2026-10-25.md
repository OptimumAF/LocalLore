# Owned runtime cleanup qualification — 2026-10-25

Refs #29 D07.06, supporting #25 D04.02/.03 and D09.06.
**Measured focused prerequisite; GitHub owns review and acceptance status.**
This is a focused ownership prerequisite, not native selected-case execution,
model-quality acceptance, or completion of D07/D04/D09.
PR: [#166](https://github.com/OptimumAF/LocalLore/pull/166).

## Source and evidence boundary

Final Rust candidate:
`3bafb93cded2bd7220029e7e04361b91e7470ab8`, recorded clean at launch and unchanged
at completion by the terminal process records cited below. Accepted-main baseline:
`7838a7ca6b4e85c59e4139fdebcf1fbec018e998` (PR163).
Final compatibility/build source is `e31e4908c0f66604d54826de7bd990952637b0c2`.
Its difference from3bafb is the new panel checker, verifier registration,
ModelPanel/checker formatting and contract documentation; no Rust source changed.
The [frozen contract](D07_OWNED_RUNTIME_CLEANUP_CONTRACT_2026-10-25.md) defines the
owner-retention behavior. Implementation and new tests were absent at its
initial freeze; these measurements describe the subsequent implementation.

Root ran all commands serially. This document's author read source, terminal
logs/process records and review comments, and edited this report only. No command
in the reproduction section was executed by this document's author.
Generated fixtures, raw diagnostics and process records stay local/gitignored.
Paths below use `<task-root>`, `<source>` and `<native-target>` placeholders.

Evidence classes are deliberately separate:

| Evidence | What actually ran |
| --- | --- |
| Runtime Rust tests | Actual owned child processes using the fixed tiny protocol fixture |
| Desktop native Rust tests | Actual ModelManager/Host lifecycle with synthetic protocol owners |
| Frontend checks | Full verifier and four synthetic actual-controller + headless React cases passed |
| Native IPC / WebView / render images | No new execution in this qualification |
| Android compatibility | Twenty Rust-host tests; no JNI/Gradle/device execution |
| Real model / physical device | No weights, model inference, SDK/device execution |

## Implemented behavior

`OwnedStartFailure` distinguishes failure before child creation from an error
which still owns an actual child. `AfterChild` carries the original fixed cause
and `Box<LocalRuntime>`; it is not Clone or serialized. Manual Debug omits paths,
handles and raw worker output. Storage for the box is allocated before spawn,
so returning a post-spawn error does not need a new owner allocation.

One private startup body serves the additive owned packaged constructor and
legacy wrappers. Acquired pipes, joining handles and verified worker/model/
ancestor pins remain attached on post-spawn failure, including partial pipe
thread startup. Such owners are Failed and cannot load or infer before cleanup.

`terminate_and_reap` operates directly on the retained child even in Failed.
It closes the writer and positively observes/reaps that child before joining
pipe threads. An unresolved handle remains owned on error. A joined panicking
thread produces Cleanup; remaining handles can still be drained by retry.
Repeated confirmed cleanup is idempotent. Kill requests and elapsed deadlines
alone do not prove cleanup, and no universal OS wall-time bound is claimed.

The existing ModelManager retains an uncertain owner in its existing runtime
slot. Resident/Failed, loaded=false and Cleanup remain visible while that owner
blocks replacement. This remains true while the runtime mutex is held or
poisoned. Direct cleanup is used by ordinary load failure, unload, retire and
close; only confirmed cleanup with the matching owner/job fences clears it.

The private reservation handoff installs the same Arc before its ticket drops.
Matching same-Arc transfer is idempotent; a foreign ticket/owner cannot overwrite
another owner, and failure returns ownership to the caller. Pending startup
continues to exclude replacement until its matching cleanup/publication ends.
A close-worker gate serializes side effects and identity revalidation before
revoking Host suppliers, without holding the manager metadata mutex across Host
work. It prevents an older close from revoking a replacement supplier.

There is no second process manager, quarantine registry, provider backend,
canonical store, schema, wire keyset or new renderer execution command.
Legacy constructors still map to the original error and best-effort Drop.
Existing full native evaluator callers remain on their legacy API: this PR
does **not** make every existing native evaluation failure cleanup-proven.

## Test fixtures and normal-build boundary

Runtime tests use the existing protocol-fixture executable and narrowly scoped
private test faults. Owner-carrying ModelManager tests use real LocalRuntime
owners; the two pending-startup cases are metadata-only. A zero-argument development-worker-only
helper chooses the fixed executable relative to the test executable and creates
its own synthetic temporary fixture. Callers cannot supply an executable,
mode, argument list or arbitrary command. It exposes no IPC/server interface.

Desktop dev-dependencies enable engine-adapter + development-worker on the same
existing local-runtime path. No package/version, third-party dependency, lock
upgrade or download was added. Resolver-2 normal/build graph evidence at
`0458ae475de25fd73991ff65808a8570763b5b59` excludes development-worker; this is
graph evidence, not proof of production app execution. Final normal artifact
restoration is recorded separately below, with nativeFeatures=[] and normalFrontend=true.

One explicit non-test `expect(dead_code)` documents the tested reservation
handoff while the selected native adapter is unwired. Remove it when that
consumer is added; an unused expectation fails strict lint. No runtime lint
was suppressed. Tests retain bounded local diagnostics; synthetic panic output
is expected in panic/poison tests and is not a hidden production model error.

## Preserved first failures and corrections

All filenames below are relative to `<task-root>/author-integration-artifacts/`
and start with `d07-owned-runtime-`. Each executed stage has a matching
`-process.json` with command, arguments, source, cleanliness, exit and timestamps.
Filtered/focused groups overlap later full suites; their counts are not added.

| Stage / source | Actual result and disposition | Local log suffix |
| --- | --- | --- |
| Accepted baseline `7838a7ca` | Fixed worker build exit0, 17.01s; Runtime 40 passed / 1 existing privilege ignore, 23.88s | `baseline-fixture`, `baseline-library` |
| Native baseline `251e5d45` | Model tests 8 passed / 1 existing ignore, 106 filtered, 0.02s | `baseline-native-models` |
| Pending startup `5c3af5e2` | 0 passed / 2 failed: unloaded was shown while startup remained owned | `pending-first-red` |
| Pending fix `908d2cb6` | Same two cases passed | `pending-first-green` |
| Compatibility `0458ae47` | Models 10 passed / 1 existing ignore, 106 filtered, 0.01s | `pending-models-compatibility` |
| Runtime API absent `5c3af5e2` | Exit101, 29 missing-API compile errors; zero tests executed | `api-first-red` |
| Initial Runtime `fb7f4851` | Frozen six groups passed, 41 filtered, 0.15s; not a full qualification | `api-first-green` |
| Manager API absent `fb7f4851` | Exit101, 21 missing-API compile errors; zero tests executed | `manager-first-red` |
| Partial owner `e89bcf2f` | Actual 0/1 failure: returned owner Unloaded rather than Failed | `partial-start-first-red` |
| Bounded diagnostic `5a519903` | Actual 0/1 failure: owner.load returned Ok; request ID advanced 0→1 | `partial-start-diagnostic-red` |
| Failed-owner fix `cc0e78a8` | Same seven Runtime groups passed, 41 filtered, 0.15s | `api-corrected-green` |
| Manager quarantine `c0d98237` | Eight model-ownership groups passed: two metadata-only, six fixed-owner; 115 filtered, 0.30s | `manager-first-green` |
| Runtime strict lint `c0d98237` | Five large_enum_variant/result_large_err errors, exit101 | `first-clippy` |
| Box amendment `90fed0e1` | Seven groups passed, 0.16s; strict Runtime Clippy passed, 2.02s | `boxed-green`, `boxed-clippy` |
| Stale close `9698c34e` | Actual 0/1 failure after replacement installed: Host free_text became false | `close-race-first-red` |
| Close gate `e9047529` | Nine owner/lifecycle groups passed, 115 filtered, 1.34s | `close-race-first-green` |
| Native strict lint `90fed0e1` | Unwired retain_uncertain dead_code error, exit101 | `first-native-clippy` |
| First format `9ddc00d6` | Exit1; original formatting evidence retained | `first-format` |
| Final Rust `3bafb93c` | Runtime 47 passed / 1 existing ignore, 23.58s | `full-library` |
| Final Rust `3bafb93c` | Native all-target/all-feature Clippy exit0, 8.67s | `corrected-native-clippy` |
| Final Rust `3bafb93c` | Native default 119 passed / 1 existing ignore, 162.06s | `full-native-default` |
| Final Rust `3bafb93c` | Native development 123 passed / 1 existing ignore, 178.36s; standalone harness contract 2 passed, 0.02s | `full-native-development` |

The partial-owner and stale-close cases were source findings first, then actual
behavioral failures. The missing-API failures were compilation failures, not
behavioral RED. The boxing amendment changed owner representation/type-only
test dereferences; it did not weaken the original behavioral assertions.
The formatting commit also documents the unwired handoff expectation.

The dedicated panel check first failed at its launcher, before any semantic
case: a scalar argument was indexed as characters and Node attempted to load
`c`. The corrected argument array ran all four cases at `3b5f4750`: resident
Cleanup, resident loaded, clean unloaded/imported, and pending unload. This is
synthetic actual-controller state plus React static HTML, with all native IPC,
native rendering, render-image and model-execution flags false. It checks the
real held unload action's busy behavior and visible cleanup retry guidance.
Logs `panel-first` / `panel-corrected` preserve that distinction; the launcher
failure is not a panel behavioral RED. First frontend formatting flagged
ModelPanel and this checker; `e31e4908` formats only those two files.
Root inspected all four resulting HTML cases for controls/status/alert/progress
semantics. The retained semantic-review JSON pins each HTML byte hash. This
inspection measured no graphical layout or pixels and used no native WebView.

Independent source reviews:
[6396934525](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6396934525)
identified post-startup owner reuse, and
[6397068264](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6397068264)
identified the check-to-revoke close race. The latter specifically distinguished
an old close already superseded at entry from one superseded after its initial
check. Neither review is human approval or a runtime test result.

## Final measured matrix

| Check at final Rust source | Result | Compile / measured test time |
| --- | --- | --- |
| Fixed protocol fixture build | Exit0 | 1.39s |
| Complete Runtime library, all features | 47 passed, 0 failed, 1 ignored | 2.14s / 23.58s |
| Complete desktop native default binary | 119 passed, 0 failed, 1 ignored | 15.37s / 162.06s |
| Complete desktop native development binary | 123 passed, 0 failed, 1 ignored | 34.95s / 178.36s |
| Standalone development harness contract | 2 passed, 0 failed | Included build / 0.02s |
| Desktop native all-feature/all-target strict Clippy | Exit0 | 8.67s |
| Runtime + desktop Rust format checks at e31e | Exit0, both | No test count |
| Full frontend + frontend format at e31e | Exit0, both; includes four-case headless check | No native execution |
| Native strict Clippy repeated at e31e | Exit0 | 11.57s |
| Normal production build at e31e | Exit0 | 20.16s |
| Android Rust-host library at e31e | 20 passed, 0 failed, 0 ignored | 4.62s / 1.68s |

The ignored cases retain explicit existing Windows symlink-privilege reasons;
they were not executed. Development is an all-feature test build, not a native
application launch. Test durations are reported as their actual scopes, not
combined into an invented latency or cleanup-time guarantee.

## Reproduction

Use the existing Windows x64 task environment and owned targets. Prior accepted
qualification records Windows11 build10.0.26300, Rust/Cargo1.93.1,
Node24.22.1 and PowerShell7.6.5; no environment upgrade is attributed to this PR.
These are inherited recorded versions, not fresh queries by this author.
`<source>` is the clean source checkout; `<native-target>` is the existing owned
target used by Root. Configure the recorded serial environment:

```powershell
$env:CARGO_BUILD_JOBS='1'; $env:CARGO_INCREMENTAL='0'
$env:CARGO_PROFILE_DEV_DEBUG='0'; $env:CARGO_PROFILE_TEST_DEBUG='0'
$env:LIBSQLITE3_FLAGS=''
$env:TEMP='<task-root>/memory-controls-temp'; $env:TMP=$env:TEMP
```

Run from `<source>`; build the fixed protocol fixture before owner tests:

```powershell
cargo build --locked --offline --manifest-path crates/locallore-local-runtime/Cargo.toml --all-features --jobs 1 --target-dir <native-target> --bin protocol-fixture
cargo test --locked --offline --manifest-path crates/locallore-local-runtime/Cargo.toml --all-features --jobs 1 --target-dir <native-target> --lib -- --nocapture --test-threads=1
cargo clippy --locked --offline --manifest-path crates/locallore-local-runtime/Cargo.toml --all-features --all-targets --jobs 1 --target-dir <native-target> -- -D warnings
cargo test --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --jobs 1 --target-dir <native-target> --bin locallore-desktop-spike -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --jobs 1 --target-dir <native-target> -- --nocapture --test-threads=1
cargo clippy --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --all-targets --jobs 1 --target-dir <native-target> -- -D warnings
cargo fmt --manifest-path crates/locallore-local-runtime/Cargo.toml --all -- --check
cargo tree --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --target x86_64-pc-windows-msvc --edges normal,build,features --invert locallore-local-runtime
cargo test --locked --offline --manifest-path crates/locallore-android/Cargo.toml --jobs 1 --target-dir <native-target> --lib -- --nocapture --test-threads=1
cargo tree --locked --offline --manifest-path crates/locallore-android/Cargo.toml --edges normal,build,dev --prefix none
cargo fmt --manifest-path apps/desktop/src-tauri/Cargo.toml --all -- --check
cargo build --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --jobs 1 --target-dir <native-target>
# From apps/desktop, using the recorded approved Node24.22.1 launcher:
node check-model-cleanup-panel.mjs
node verify-frontend.mjs
node node_modules/prettier/bin/prettier.cjs --check 'ui/*.{ts,tsx,html,css}' '*.{json,mjs}'
```

These commands are reproducible recipes; source/timestamp attribution for an
actual recorded invocation comes from its process JSON. Root's local helper
refuses overwritten evidence and requires a clean source before launching.
Focused original groups use the same command with their recorded filter.
The final Runtime strict-lint pass predates the final formatting-only source;
the final native strict pass includes the dependency at3bafb.

## Final compatibility and retained hashes

`final-normal-results.json` records five terminal exit0 stages at e31e: frontend,
frontend-format, rust-format, native-clippy and native-normal-build. Its companion
progress JSON still says running for the final stage; completed per-stage results,
terminal build output and matching artifacts establish completion. No active log
was read/hashed. `final-runtime-format-process.json` separately records exit0.
Android graph output is dependency evidence only; no SDK rebuild is implied.

The document author independently matched both built files against the artifact
JSON. Normal frontend verification includes strict TypeScript/request checks and
development journey/control-hook exclusions. These are static/build checks,
not a native production UI launch or an exhaustive absence proof.

| Retained item | Bytes / SHA256 |
| --- | --- |
| Normal app.js, e31e | 525,661 / `5c7f13bc24d244396dd535002cb12beb4523aa2868f63e55584669798829d489` |
| Normal desktop EXE, e31e | 32,314,368 / `f677bf0c01447f0355db20c1f576f6b83f73726b9217836c755eb71ec7bf5075` |
| Runtime lib.rs, 3bafb/e31e | `7c6d95fa82374dbb1620aa324ac3e04e5735ad77a48c89225a93708887c42961` |
| ModelManager models.rs, 3bafb/e31e | `ba937c2bbfdbc707d70e458dc6e2d8cd5328605963581348e86071febe926729` |
| Full Runtime log | `2b992eee94631b620d2595c343170bab614b20acdf0d623e475d553b3a745705` |
| Full default native log | `e81e21a6cf03c5397f02fc84c04247d4ee831fb012621e5e3b66fb72be523571` |
| Full development native log | `cde457a8d74007dd375f6864ba9b3a35a14aeddb0754c3164dbdfa724335d714` |
| Final normal results JSON | `3b91d40cbe5f511fd056d015f80c5334784a6d37a27df7453c42cae4655078d8` |
| Final normal artifact JSON | `2319c4fd05a76d2b852d28ca61f8b3c2fb046f12919f997fd2382bbc77d5a613` |
| Root four-case semantic-review JSON | `51f82f8ae1911fa48d1ab444e96af945b3b3883228bdaf24be3ff8f6542e598f` |

The terminal evidence inventory is **75 files / 196,335 bytes**: all local
`d07-owned-runtime-*` regular files except the stale `*-progress.json`.
It includes the command helper, terminal log/process pairs, five-stage result
record, artifact and semantic-review JSON, not generated saves or binaries themselves.
An ordinal filename-sorted UTF8 manifest of `filename<TAB>bytes<TAB>lowercaseSHA256<LF>`
has SHA256 `e4ccaad064bd1b717e648930b00e32b69554f5620ca3fdfc8ab91775942827b6`.
All process records in this inventory were terminal before hashing. This
inventory preserves original failures rather than replacing their files.

## Limits and next runnable task

This establishes finite observed ownership behavior for the frozen fault cases,
including real child retention, direct reap, poisoned ownership, stale close and
explicit cleanup retry. It does not promise successful or bounded cleanup under
every OS failure, or make best-effort Drop a cleanup acknowledgement.
The actual controller checks loaded/phase; this report makes no claim of a strict
closed model-status decoder. Headless UI evidence remains
separate from IPC, actual native WebView rendering and app-owned render images.

No model weights were loaded or inferred, no physical device check ran, and no
new offline/licensing/model-quality/hardware qualification is claimed. Android
Rust-host compatibility is distinct from JNI/Gradle/device testing.
No protected chat/resources, desktop control, unrelated application automation,
release or repository-setting change was part of this work.

Native selected-case execution, its reservation ownership hook and its GUI
remain unavailable. The next runnable task is Root's separately frozen native
selected-driver allocation using this retained-owner prerequisite, with actual
generation and cleanup/recovery evidence before consumer exposure. Existing
canonical history, old recorded Play validators and retry bytes remain authoritative.
The issues own acceptance status for this prerequisite and the remaining gates;
these measurements do not establish whole-milestone completion.
