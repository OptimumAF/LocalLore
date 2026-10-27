# Scene construction: Host and capture qualification

2026-10-27. Refs #9 M05.03 / #25 D04.04, supporting slice, **in review**.
This packet qualifies synthetic Rust Host/Store integration and a bounded
Domain1 narrator-input consistency gate. It does not qualify native IPC,
WebView rendering, a real model, Android execution or prose quality. The
owner's existing **needs improvement** assessment remains unchanged. Full
milestone checklists and owner acceptance remain separate.

## Boundary exercised

`crates/locallore/src/host.rs` adds native-only
`HostPlayConstructionV1::MemorySceneV1(PlayContextPolicy)` and
`PlayerLiteralSceneV1`. The enum has no Serde/wire selector. Memory uses the
existing coherent generation snapshot and coverage; literal uses the existing
canonical literal snapshot and remains Domain1-only. Both call the shared
scene Play pipeline. Unsupported scene seeds are checked before constructing
the provider. No new Host command, canonical writer, storage implementation,
model manager, dependency or inspection grant is introduced. Default provider,
old construction mappings and public JSON commands remain unchanged. This
Host slice does not activate a scene recipe in the desktop UI.

| Native construction | Prompt version | Trace schema label |
| --- | --- | --- |
| Memory scene | `locallore-play-v2.9-scene-frame-v1` | `locallore-play-v2` |
| Player literal scene | `locallore-play-v2.10-literal-director-v1-scene-frame-v1` | `locallore-director-literal-v1` |

Both use `grounded-prose-v2.4-scene-frame-v1`. Actual generation requests retain
the existing Director schema IDs (`locallore-director-v2` or
`locallore-director-literal-v1`) and Narrator ID `locallore-narrator-v2`.

Four Core Host tests use actual `Host::new`, sessions, queued/prepare/commit,
recording providers and opt-in capture. They compare the actual forwarded
requests/frame to native snapshots and captures, prove prepare is noncanonical,
check exact zero-inference retries after future configuration changes, queued
and prepared cancellation, a competing real Host commit/stale candidate, Player
capture isolation, rejected wire selectors and unchanged old 2.5/2.6 paths.
These are in-memory Host tests, explicitly separate from durability.

The Workspace tests use actual `locallore_workspace::open` and the existing
Repository/Store adapter. Both constructions run with ordinary and genuinely
reviewed typed presented starters. Tests compare actual candidate, durable
receipt, canonical records, source frame and forwarded capture; fully close,
drop and reopen; recover persisted turns; and retry under a different future
configuration without new inference. Cancellation/stale candidates leave no
durable receipt. Old 2.5/2.6/2.7/2.8 paths remain controls. Private capture
consent/details are process-local and cannot be recreated retroactively by a
retry. Public Host has no arbitrary `initial_world` seed-import route; that
unsupported-seed refusal is separately covered by Core.

## Meaning of the capture gate

`crates/locallore-eval/src/scene_capture_v1.rs` implements the independently
frozen [capture contract](D04_SCENE_CAPTURE_GATE_CONTRACT_2026-10-27.md).
Its borrowed native input requires actual before/after Engines, request,
expected recipe/profile, attempt, details and indexed recording hashes. Its
opaque result has no deserialization or execution-authority conversion.

Success requires one fresh immediate Domain1 append, the complete accepted
source prefix, exact recipe/profile/receipt, regenerated source-bound staging
and narrator input, and actual candidate/proposal/approved equality. It checks
closed artifact kinds/order, identity, role-specific budgets, recording order
and hashes. The 17-test suite includes a 16-combination recipe/presentation/
repair/fallback matrix, unequal Director/Narrator budgets, full-prefix and
rehash-consistent narrator forgeries, actual Domain2 refusal, cancellation,
unavailable captures, exact retry refusal and explicit scope limits.

This is narrator-input consistency, not provenance authentication of supplied
snapshots or raw model output. Director inputs receive envelope/hash checks,
not source regeneration. Positive limit tests admit a self-consistent Director
suffix and replacement raw-output diagnostic. Memory/compiler/cache execution
is not established. Identical narrator bytes across constructions are allowed
when the actual source/approved outcome is identical. The existing
`details.exact_reconstruction=false` flag remains false. Historical Protocol3
reports/gates are not upgraded retroactively. The gate tests use actual Core
Play and TraceRing/RingSink with synthetic recording replies; they do not
execute Host dispatch or Store themselves. The separate Host/Workspace tests
provide that integration evidence without claiming that the Domain1 gate
supports corrected Domain2 captures.

## Source attribution and retained failures

The first independent freezes are Host `c37eff69` and capture `9140c4a3`.
Missing future APIs at freeze were uncompiled prerequisites, not behavioral RED.
An initial source-only reference-type calibration in the Workspace assertion
was integrated before execution; it preserved exact expected JSON equality.

At clean unchanged `0c7fda33b35eef68f2165de8af3f7704c5a9d1db`, Core Host
passes four tests. Workspace actually runs three: one passes and two stop with
`InvalidInput` before their intended assertions. The presented fixture supplied
`scene-presented-creation`, violating the established requirement for exactly
32 lowercase hexadecimal characters. Independent second freeze `8e977dac`,
integrated as `d1597ddb37e2ffc56420438c4e1097eaf52c3923`, changes only that
positive ID and adds positive/original-negative public-validator calibration.
All original seven Host/Workspace function oracles remain; the corrected
Workspace suite has four functions. No creation rule or desired outcome was
relaxed. The initial capture gate also passes 17 tests at 0c7.

Broad integration source is clean unchanged
`232ad3791f4cc01bc83350c7d79c97d7eaa34abf`, including the accepted selected-test
fixture isolation correction. Its first normal native compilation fails with
four missing scene API/field errors. A separate verbose no-run diagnostic
repeats that failure. Cargo reports Core as Fresh while the selected `.rmeta`
has no scene module dependencies in its relative-path dep-info. The retained
observation records metadata SHA-256
`2c029c8d58e966125adee887b676e0768cf01cff32b08bb03a256e894a52ccd9`,
5,524,564 bytes, written 18:43:10.9769670 UTC; actual `play.rs` was written
18:18:22.8097212 UTC. These observations do not establish the artifact's
historical source/origin or another process's responsibility.

A package-scoped clean in the verified task-owned target removes 5,329 files,
8.0 GiB, without source changes. Unchanged 232ad then passes normal and dev
native tests under the default parallel runner. This is a measured cache
rebuild recovery; original compiler failures stay failed. It is not evidence
that every cache is interchangeable or that arbitrary shared targets are safe
to clean. There is no test-runner serialization workaround.

Strict Eval Clippy at 232ad separately fails on two `Result.ok().expect()` style
diagnostics. `9de3782e` removes the two redundant `.ok()` conversions, preserving
success requirements and all oracle intent. Rustfmt then reports one layout
line at `1de30b8a`; `f7a0870e20656259bf9b3f22a1b720bb9187732d` formats it.
Relative to 232ad, shared Rust production is byte-identical; the only Rust delta
is those capture-test assertion conversions/layout. The stack also reconciles
accepted desktop receipt transport PR235 through `02581a73`/`6a874e50`, plus
documentation. Broad 232ad test results are not relabeled as whole-suite f7 runs.

## Exact completed results

Durations are process-record UTC end minus start, including command overhead.
Each listed record reports source clean and unchanged, exit zero unless marked
failed. All heavy checks were coordinated serially.

| Check | Executed source | Result | Command seconds |
| --- | --- | --- | ---: |
| Core Host focused | 0c7fda33 | 4 passed / 0 failed | 14.2230886 |
| Workspace first | 0c7fda33 | 1 passed / 2 setup failures | 17.1910655 |
| Capture gate first | 0c7fda33 | 17 passed / 0 failed | 24.9206585 |
| Workspace corrected | d1597ddb | 4 passed / 0 failed | 2.4570527 |
| Portable workspace, all features, desktop excluded | 232ad379 | 1,019 passed / 0 failed / 11 ignored; 142 summaries | 439.0894051 |
| Eval, local-model feature | 232ad379 | 249 passed / 0 failed / 17 ignored; 31 summaries | 1633.3707714 |
| Normal native first compile | 232ad379 | FAILED, four missing scene API/field errors | 4.2620343 |
| Verbose native no-run diagnostic | 232ad379 | FAILED, same errors | 3.9100020 |
| Owned package cache clean | 232ad379 | PASS, source unchanged | 4.4794559 |
| Normal native default-parallel | 232ad379 | 240 passed / 0 failed / 9 ignored | 333.6703333 |
| Dev native default-parallel | 232ad379 | 247 unit + 2 contract = 249 passed / 0 failed / 9 ignored | 338.8391544 |
| Strict portable workspace Clippy | 232ad379 | PASS | 41.0865834 |
| Strict Eval Clippy first | 232ad379 | FAILED, two style diagnostics | 10.8559687 |
| Rustfmt first | 1de30b8a | FAILED, one layout line | 0.3562598 |
| Rustfmt corrected | f7a0870e | PASS | 0.2782884 |
| Capture gate final, local-model feature | f7a0870e | 17 passed / 0 failed | 25.0619358 |
| Strict Eval Clippy corrected | f7a0870e | PASS | 17.4444824 |
| Strict normal native Clippy | f7a0870e | PASS | 21.5181148 |
| Strict dev native Clippy | f7a0870e | PASS | 12.1889486 |
| Full frontend verifier | f7a0870e | PASS | 19.5338920 |
| Normal native build | f7a0870e | PASS, unlaunched | 36.3841058 |

The 142/31 summaries include integration and documentation-test summaries;
ignored tests are excluded from pass counts and were not executed by this
packet. Native default-parallel commands include no `--test-threads` option;
the process records do not themselves record an inherited `RUST_TEST_THREADS`
environment value. The frontend verifier covers strict TypeScript, current
schemas, normal bundle and its wired mock/controller/headless suites. It
explicitly reports no native/model execution. Native Rust unit tests and an
unlaunched binary build are not native IPC or WebView journeys.

## Reproducible command forms

From the checked-out source corresponding to each row, use the already
provisioned exact-lock offline package cache and a task-owned target. Do not
substitute an arbitrary occupied shared target. These forms replace only
private machine paths with variables:

```powershell
$ownedTarget = '<owned Rust target directory>'
$taskNode = '<installed Node 24.22.1 executable>'
$common = @('--locked', '--offline', '--jobs', '1', '--target-dir', $ownedTarget)
cargo test -p locallore --features host --test host_scene_recipe_v1 @common
cargo test -p locallore-workspace --test host_scene_recipe_v1 @common
cargo test --manifest-path crates/locallore-eval/Cargo.toml --test scene_capture_v1 @common
cargo test --workspace --exclude locallore-desktop-spike --all-features @common
cargo test --manifest-path crates/locallore-eval/Cargo.toml --features local-model @common
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml @common
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness @common
cargo clippy --workspace --exclude locallore-desktop-spike --all-targets --all-features @common -- -D warnings
cargo clippy --manifest-path crates/locallore-eval/Cargo.toml --all-targets --features local-model @common -- -D warnings
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets @common -- -D warnings
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --all-targets @common -- -D warnings
& $taskNode apps/desktop/verify-frontend.mjs
cargo build --manifest-path apps/desktop/src-tauri/Cargo.toml @common
rustfmt --edition 2021 --check crates/locallore/src/host.rs crates/locallore/tests/host_scene_recipe_v1.rs crates/locallore-workspace/tests/host_scene_recipe_v1.rs crates/locallore-eval/src/scene_capture_v1.rs crates/locallore-eval/tests/scene_capture_v1.rs
```

The final focused gate adds `--features local-model` to its focused command.
The failed diagnostic adds `--no-run -vv` to normal native tests. Historical
cache recovery used `cargo clean --offline -p locallore -p locallore-storage
-p locallore-workspace -p locallore-android -p locallore-eval
-p locallore-desktop-spike --target-dir <verified owned target>`; that is an
attribution record, not a routine qualification prerequisite.

Environment: Windows NT10.0.26300 x64, rustc1.93.1 (`01f6ddf75`), cargo1.93.1
(`083ac5135`), Node24.22.1, TypeScript7.0.2, React19.3.1, esbuild0.28.2,
Tauri2.12.5/Wry0.57/Tao0.37.1. These are the existing provisioned/report versions;
this documentation pass performs no new runtime/version probe or upgrade.
Existing offline environment uses isolated `CARGO_HOME`, `CARGO_NET_OFFLINE=true`,
one build job, incremental disabled, dev/test debug info disabled and owned
TEMP/TMP. Actual commands, source cleanliness and UTC times remain in local
gitignored process JSON and logs.

| Public source path | SHA-256 at f7a0870e |
| --- | --- |
| `crates/locallore/src/host.rs` | `054cb661ceb6a1e0f82c890674b13e3fcf0b71d1ff50ba65a65eed8fb898471a` |
| `crates/locallore/tests/host_scene_recipe_v1.rs` | `5b4b72b9c82d27aa89f86d2f1dd002d0709bda1a8a4b57c8f7820f66bee2e860` |
| `crates/locallore-workspace/tests/host_scene_recipe_v1.rs` | `fc4107c8983d5964a5cb4066dc31649f1bd8948e1fc2183cb2ed9b4a055c93f0` |
| `crates/locallore-eval/src/scene_capture_v1.rs` | `02831ff8af5d34b8ca8a2adffe02d10b7e55a90f704e2fb2a62b8f07b4a6c658` |
| `crates/locallore-eval/tests/scene_capture_v1.rs` | `47ded39f81ea12715cdcd7ce22e3234d4d8ce36fca99e34163a3253bcb5e41ad` |
| `Cargo.lock` | `4fb7c498ca0ecc62c4ea1f65c63b370ab4336eb75133d08b3a71f5664156cf93` |

Private evidence stems are `d04-scene-host-*` and the initial
`d04-scene-capture-gate-first*`, not `d04-scene-eval-gate-first*`. Original
failures, cache observation and corrected outcomes remain distinct. No raw
private path, prompt, save or model artifact is published here.

## Remaining gates

Final-source Android dependency metadata compatibility is pending at this
document freeze; prior Core Android graph evidence is not relabeled. No new
Android cross-build/JVM/device/phone result is claimed. Native IPC, mounted UI,
app-owned render images, model loading/inference, offline containment,
accessibility, package/distribution and human scene-quality gates are absent
from this packet. No render artifact exists here to inspect. The smallest next
verification is the coordinator-owned Android dependency graph, followed by a
separately frozen fixed scene native journey using the same controller/IPC/
Store paths and honest synthetic-provider labeling. No task checkbox, release
readiness or merge approval follows from these supporting results.
