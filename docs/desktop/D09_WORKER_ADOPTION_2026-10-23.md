# D09 fixed worker adoption qualification

Refs #31 D09.03/.05 and #25 D04.02/.03/.04/.06, partial prerequisites.
Claims [6360854674](https://github.com/OptimumAF/LocalLore/issues/31#issuecomment-6360854674)
and [6360854924](https://github.com/OptimumAF/LocalLore/issues/25#issuecomment-6360854924).
Contributor `/root/desktop_runtime_profile`, isolated
`impl/d09-worker-adoption` / task-owned `source-worker-adoption`, initially
accepted main `55ade00c1db8df39c62fb61cbe46c7c38edadd28`, reconciled with
accepted `d5a76d2308a6863e49b3d088041d0eccadf8bb38` before final qualification.
Final measured source is clean `b534fa781b9cabd4b7749a44f6ceb4ace58536e2`.
This report is the subsequent documentation-only change.

The new fixed worker passes bounded native runtime/model/controller/render and
developer-package checks. Both accepted native turns still use engine fallback
narration. **Prose quality, observed offline operation, installation, sustained
performance, device qualification and the complete D04/D09 gates remain open.**
No merge, release, repository-setting change or public binary upload occurred.

## Fixed identity and scope

The coordinator independently reviewed the reproducibility source/evidence and
rehashed both outputs before authorizing this adoption slice. Unchanged reviewed
net changes from `a91be8d` are integrated as `980381c`; the actual reproducibility
implementation remains `4258b365a61ccba70cbcfb9ebe2cf356e7bcd055`.
See [the two-clean-path report](D09_WORKER_REPRODUCIBILITY_2026-10-23.md).

The only adoption policy edits replace the old fixed SHA256 in
`apps/desktop/stage-runtime.mjs`, `apps/desktop/ui/model-journeys.ts` and
`scripts/desktop-package.py` with
`b5dd124e484c67c9dda5aebb2cdff1878ccefd0fba99aba4788e00a166f68434`.
The candidate is6,014,464 bytes, pinned llama.cpp
`620d2225cc436ab0b001e3200e590e3b286ef9ab`. There is one accepted hash, no caller
override, permissive allowlist or runtime contract change. Existing `build.ps1`
already invokes the Release CMake policy and needs no source change; clean
comparison is the separate explicit `test_reproducible.py` command.

The additional owned development-only journey changes reject blank DOM or
RenderError/UnhandledError, require a visible heading, and capture pending/error/
cancel notices inside the viewport. No App/controller/main, engine, storage,
schema, historical receipt fixture, inference profile or Android source changed.
The accepted main merge preserves its existing shared changes unchanged.

Approved existing Qwen3-0.6B Q8_0:639,446,688 bytes, SHA256
`9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`.
The previous synthetic app-owned imported model root was reused read-only;
no second model copy, import, download, rename or deletion occurred. Its hash,
size and last-write time match before/after. The original qualified worker
remains unchanged at `add98cf02249141942c88e2517c2f5a4c9a91dbe9638bf7d3cd30c26916bce87`.

Actual receipts retain model/template/profile/runtime identities:
profile `qwen3-0.6b-q8-cpu-v1`, manifest SHA256
`01ad542001b04a96f4a8ed6c841be1866eb025350836e0c5d0a4969fdb361d38`,
template `57f1fd00f0013a2be96aa79b857391f27e23df5b5f847072b524c897e24d0361`,
prompt `locallore-play-v2.2`, policy `grounded-prose-v2.1`. One resident model,
fresh contexts per role, CPU4 threads/GPU0, context4096,350-token role caps,
one repair and whole-turn120000ms remain unchanged.

## Executed checks

Windows11 Pro10.0.26300 x64; Rust/Cargo1.93.1; Node24.22.1/npm11.19.1;
Python3.14.9; installed WebView2 Runtime155.0.4283.62 (read from EdgeUpdate
registration); native toolchain/SDK identities are in the reproducibility report.
Existing dependencies only, locked/offline Cargo, debug0/incremental0. New
`worker-adoption-native` target and `worker-adoption-artifacts` outputs were
used; the coordinator's busy native target was not used.

| Check | Result | What executes |
| --- | --- | --- |
| Candidate hostile protocol | 11 passed | Actual C++ worker, no model |
| Standalone runtime all-target tests | 23 passed;1 existing privilege-dependent ignore | Synthetic child processes, no real model |
| Explicit ignored reparse case | 1 passed | Local synthetic resource-path protection |
| Runtime strict Clippy/fmt | Passed | Rust static/build checks |
| Actual runtime probe | Passed | Approved model; reuse/fresh contexts, generation cancel, recovery, unload/reload, load abort, fresh owner |
| Actual shared scene | Passed | C++ model + Rust engine/SQLite; no desktop IPC/render |
| Final model native harness | 52 distinct assertions;10 PNGs;real restart passed | Same production frontend controller + native IPC + hidden native WebView2 |
| Workspace | 267 passed;0 failed/ignored;strict Clippy/fmt passed | Host/core/store/workspace compatibility, not model qualification |
| Native default | 18 passed;1 existing ignore;strict Clippy/fmt passed | Native Rust units |
| Native development | 20 units +2 wrapper tests passed;1 existing ignore;strict Clippy passed | Native Rust/harness wrappers |
| Frontend | Check/strict TypeScript/schema/controller/error/privacy/hook-absence +format passed | Programmatic model-free frontend checks; no new headless browser claim |
| Packaging adversarial/policy tests | 12 passed;workflow policy passed | Model-free package/source validation, not a hosted CI run |
| Normal developer folder/ZIP | Built and independently verified;446 members | Default native executable and closed package inventory; no normal-package launch |

The real runtime probe records one model load across director/narrator, context
counts1→2, generation cancellation224ms, load cancellation393ms with abort
callback, successful generation recovery, explicit reload model_loads2, shutdown
and a fresh owner. These single-run observations exclude model hash verification
from worker load metrics and establish no latency/thermal target.

The shared scene reports gift committed, exact retry without inference,
restart/replay equality and speaker-scoped secret isolation all true; total54153ms.
It includes canonical invalid-ability/clarification/cancel checks. It writes only
synthetic local output and reports `quality_accepted=false`, `network_blocked=false`.
Concurrent local compilation and finite synthetic requests preclude performance
qualification.

## Native UI, durable journeys and render evidence

Definitive output: `worker-adoption-artifacts/`
`model-native-c27c4eac-3ba9-4bd8-9877-b68967029f26`.
Source binding is clean `b534fa7`; summary SHA256
`43e1c62d8ec40629d1d6a87e7b3090bb34968c1a57458766f9bbe24f5049e2a6`.
All10 actual app-owned WebView2 images were inspected, including loaded model,
pending noncanonical generation, receipt/state diff, errorAbility, cancelled
draft, absent-Sable inspection, unload, resumed receipt and real process restart.
Text and controls are legible; pending/error/cancel notices are in the captured
viewport. Snapshots retain exact story/session/revision/observer/pending/receipt/
error semantics and DOM structure; app scroll position differs by checkpoint.
This is not a desktop capture, injected input, window activation or headless mock.
The native harness creates invisible, unfocused app windows and uses WebView
capture; no user's desktop was controlled or captured.

The production controller/IPC paths verify hash/load cancellation, explicit
local profile selection, one potion spent once, lost acknowledgment recovery of
one original receipt, double-spend refusal, exact Dialogue, invalid/unlearned
ability refusal, unsupported-action clarification, generation cancellation,
absent-NPC secret isolation, independent new story/original resume, explicit
unload/reload and real executable restart. The exact original request recovers
its durable receipt with no loaded model after restart. Inspection remains a
read lens; no character knowledge or generation authority changes.

Both native accepted turns use fallback2/2, repairs0. Visible narration is the
engine's bounded potion/Dialogue text, expressly labelled as fallback. Final
single-run timings: UI load8658ms, potion9990ms, Dialogue9854ms, reload8503ms,
restart load8665ms. These are plumbing measurements, not prose or latency acceptance.

Bounded initial errors are expected Cancelled/Inventory/ClarificationRequired/
Ability/ModelUnavailable categories; restart buffer is empty. Neither phase has
RenderError or UnhandledError. Both exiting WebView processes emit the retained
Chromium shutdown message `Chrome_WidgetWin_0`, error1412; they exit successfully
and produce their reports/captures. This stderr is not relabelled an empty log.

### Failed render attempt retained

The first local dependency junction targeted a directory named
`node_modules-locked`. The bundler resolved React for App hooks there, but the
ReactDOM peer dependency resolved into its sibling `node_modules`, yielding two
React runtime copies. The existing model journey reported31 controller checks
passed while every capture was blank, DOM text/headings empty and the frontend
error buffer contained RenderError. That run (`model-native-d4403716-8b75-49f5-8565-de4197cc8142`)
is a **failed render qualification**, regardless of its old success marker.

Only the verified fresh-checkout junction was removed and relinked to the actual
existing dependency directory named `node_modules`; neither dependency tree was
changed/deleted. Locked versions match and the rebuilt bundle contains one React
runtime. No App/main/controller fix or raw diagnostic hook was needed. New
development journey guards prevent empty DOM/heading or render/unhandled errors
from passing, while failure captures remain available. A populated intermediate
run passed49 distinct checks; final52 additionally assert pending/error/cancel
status visibility. Old and intermediate artifacts remain local.

## Reproduce

Use new task-owned output directories and existing approved source/model assets.
The complete existing synthetic model root is a trusted launcher input, not a
renderer path authority. Production ignores the harness overrides. In a supplied
MSVC/Rust environment, with `$taskRoot`, `$node`, `$python`, `$modelRoot` and
`$worker` naming the reviewed existing local assets:

```powershell
$target = "$taskRoot\worker-adoption-native"
$artifacts = "$taskRoot\worker-adoption-artifacts"
$env:CARGO_PROFILE_DEV_DEBUG='0'
$env:CARGO_PROFILE_TEST_DEBUG='0'
$env:CARGO_INCREMENTAL='0'
cargo +1.93.1 build --manifest-path crates/locallore-local-runtime/Cargo.toml --features scene-probe --bins --locked --offline --target-dir $target
cargo +1.93.1 test --manifest-path crates/locallore-local-runtime/Cargo.toml --features development-worker,engine-adapter --all-targets --locked --offline --target-dir $target
cargo +1.93.1 test --manifest-path crates/locallore-local-runtime/Cargo.toml --features development-worker,engine-adapter --locked --offline --target-dir $target model_and_worker_reparse_paths_reject -- --ignored
& $python native/llama-worker/test_protocol.py $worker
& "$target\debug\runtime-probe.exe" $worker "$modelRoot\Qwen3-0.6B-Q8_0.gguf"
# Stage the fixed resource, then run the shared scene against that resource directory.
$env:LOCALLORE_D04_WORKER_SOURCE=$worker
$env:LOCALLORE_D04_TARGET_DIR=$target
& $node apps/desktop/stage-runtime.mjs
& "$target\debug\play-scene-probe.exe" "$target\debug\runtime" "$modelRoot\Qwen3-0.6B-Q8_0.gguf"
$env:LOCALLORE_D04_ARTIFACT_ROOT=$artifacts
$env:LOCALLORE_D04_REUSE_MODEL_ROOT=$modelRoot
$env:LOCALLORE_D04_MODEL_SOURCE="$modelRoot\Qwen3-0.6B-Q8_0.gguf"
# Run from apps/desktop; launcher builds harness assets/native and starts/restarts only its app.
& $node model-harness.mjs
```

Additional actual commands (from repo root; use the same `$target` and pinned
Node/npm CLI):

```powershell
cargo +1.93.1 test --workspace --locked --offline --target-dir $target
cargo +1.93.1 clippy --workspace --all-targets --locked --offline --target-dir $target -- -D warnings
cargo +1.93.1 clippy --manifest-path crates/locallore-local-runtime/Cargo.toml --features development-worker,engine-adapter --all-targets --locked --offline --target-dir $target -- -D warnings
cargo +1.93.1 test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --target-dir $target
cargo +1.93.1 test --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --locked --offline --target-dir $target
cargo +1.93.1 clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --locked --offline --target-dir $target -- -D warnings
cargo +1.93.1 clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --all-targets --locked --offline --target-dir $target -- -D warnings
cargo +1.93.1 fmt --all -- --check
cargo +1.93.1 fmt --manifest-path crates/locallore-local-runtime/Cargo.toml -- --check
cargo +1.93.1 fmt --manifest-path apps/desktop/src-tauri/Cargo.toml -- --check
& $node $npmCli --prefix apps/desktop run check
& $node $npmCli --prefix apps/desktop run format:check
& $python scripts/desktop-package-tests.py
& $node scripts/desktop-package-workflow-check.mjs
& $python scripts/desktop-package.py build --node $node --npm-cli $npmCli --target-dir $target --worker $worker --output "$taskRoot\worker-adoption-package\Unicode candidate é"
& $python scripts/desktop-package.py verify "$taskRoot\worker-adoption-package\Unicode candidate é.zip"
```

Normal frontend assets and the default native executable were rebuilt by the
packager after the harness. Logs and all model outputs/SQLite/PNG artifacts stay
outside Git. No normal package executable, installer or device was launched.

## Artifact binding and remaining gates

| Local artifact | SHA256 |
| --- | --- |
| Actual runtime model JSON | `cc3ef130cb8c43301e0c3124d641593b27ffba798847275cbb5dd920105de5e6` |
| Shared scene JSON | `4bc2dd0fd234661f9812f0f7f2eba5c76b45730e160fd1e9ae73d96b9f96e763` |
| Normal executable,19,739,648 bytes | `4e99383dc8def9496873a69b29e3d62ef3f3334dec7efa5b824664bec14fc074` |
| Package manifest | `457c09356076d99399c609fda18b82f6f7a91c97c992c91cd7930f4723885d83` |
| ZIP,9,612,728 bytes,446 members | `760e8827e5e9aecfdd521e3ba949d962721a5fd3794a2142490381bf2f36b195` |

The developer package has the fixed worker, profile and notices, no weights or
development frontend hooks. It is unsigned, not an installer; complete native/
transitive license audit and WebView2/VC runtime provisioning remain distribution
gates. This build does not repeat clean separate-path application reproducibility;
the successful two-path claim belongs to the C++ worker report only. Full Unicode
worker builds remain unqualified as documented there, even though native model
reuse, saved workspace and package paths contain Unicode/spaces.

Missing/corrupt/import-copy cases were skipped explicitly by approved-model reuse;
their earlier evidence is historical, not freshly rerun here. No outbound-denial/
traffic observation, sustained run, installer/update/uninstall, hosted workflow,
Android/physical-phone or full desktop acceptance matrix was executed by this
slice. Android/core/storage contracts have no adoption changes; accepted-main
Android evidence remains separately attributed, not a new run.

Status: in_review, coordinator acceptance/PR pending; no milestone checkbox is
completed here. Next runnable task is independent adoption diff/evidence review,
then coordinator publication and separately scoped offline/package-installation/
quality qualification.
