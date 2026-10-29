# Stopped AppContainer prototype: default checks and unlaunched builds

2026-10-27. Refs #31 D09.02/.03/.07. **Unqualified; draft source/evidence
handoff only.** The ordinary positive control previously failed with Access5;
the boxed case was not reached. Further unchanged canary, ignored-probe and
profile creation/deletion attempts remain stopped. Passing the checks below
does not establish application, renderer, worker or network isolation, offline
installation, whole-app offline operation or package readiness.

## Source and narrow change

Executed source is clean unchanged `dfe4fa67987417c4d555a38876e72d3cdb9ebd4c`.
It reconciles the preserved prototype `5d32a715` with accepted main
`d5a6e84c861b8656ca65b4ed66b5387a8cacd4b7`. The implementation delta is only
`apps/desktop/src-tauri/src/bin/offline-qualifier.rs`, existing Windows API feature
forwarding inside `dev-harness`, and its contract. This report adds documentation.
There is no dependency/version/lock, normal application handler, inference,
storage or model change. The default executable remains the desktop application;
the qualifier requires an explicit development feature and binary selection.

The [frozen feasibility contract](D09_APPCONTAINER_FEASIBILITY_CONTRACT_2026-10-26.md)
retains the historical failed controls, unknown-cause diagnostics, cleanup
limitations and stopped commands. It is not a current instruction to run those
commands. No passing unit/build result rewrites those failures. Prior independent
source review of the preserved prototype is source evidence, not security or
offline approval. This handoff does not merge or publish the prototype.

## What actually ran

One heavy workload ran at a time, using the provisioned exact-lock offline
cache, one build job, disabled incremental/debug info and task-owned TEMP/TMP.
Before changing source checkouts, an explicitly verified ordinary owned target
was cleaned for six project packages only. The separately retained process
record reports 1,427 files /681.9MiB removed in2.9821669s. This avoids the earlier
shared-target stale-project-cache problem; it is not a feature or test pass.
No package, model or runtime download occurs.

| Check at dfe4fa67 | Result | Command seconds |
| --- | --- | ---: |
| Normal frontend build | PASS; no development server | 0.4918178 |
| Qualifier default unit tests | 6 passed,0 failed,3 ignored;0.06 test seconds | 22.8659463 |
| Development all-target strict native Clippy | PASS | 19.5443925 |
| Qualifier binary build | PASS; parent image unlaunched | 8.7493279 |
| Normal desktop binary build | PASS; application unlaunched | 13.8974121 |
| Rust formatting | PASS | 3.7134952 |

All process records report clean unchanged source and exit0. The six default
tests exercise fixed path/marker binding, newly owned-directory protection and
outside-sentinel preservation, create-only image behavior, ordinary challenge
file access, actual small anonymous-pipe deadline handling and the pure cleanup
predicate. Their synthetic file/ACL operations are confined to newly owned task
fixtures. Deriving a synthetic package SID does not create an AppContainer
profile. No ignored reparse-privilege, Low-token parent or fixed-child probe ran.
The six tests do not exercise the qualifier's profile/canary/network workflow.

The test runner executes those six unit functions. Neither standalone qualifier
parent mode nor the desktop application is launched. No WebView, model, worker,
socket listener, firewall/settings change, profile creation/deletion or external
application is exercised by this packet. The three ignored tests remain ignored,
not waived or counted as passes. Historical cleanup of the original retained
profile is separate and is not repeated here.

## Reproduce the limited checks

From the repository root, use an already provisioned exact-lock cache and an
ordinary task-owned target. Do not use a target occupied by another workload.
Only the default unit command is authorized by this plan; do not add `--ignored`
or invoke the built qualifier executable. Its parent mode would run the stopped
workflow.

```powershell
$taskNode = '<existing Node 24.22.1 executable>'
$env:CARGO_HOME = '<existing isolated exact-lock package cache>'
$env:CARGO_NET_OFFLINE = 'true'
$env:CARGO_BUILD_JOBS = '1'
$env:CARGO_INCREMENTAL = '0'
$env:CARGO_PROFILE_DEV_DEBUG = '0'
$env:CARGO_PROFILE_TEST_DEBUG = '0'
$env:LIBSQLITE3_FLAGS = ''
$env:TEMP = '<existing owned temporary directory>'
$env:TMP = $env:TEMP
$ownedTarget = '<ordinary owned Rust target>'
& $taskNode apps/desktop/build.mjs
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --bin offline-qualifier --locked --offline --jobs 1 --target-dir $ownedTarget -- --test-threads=1
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --all-targets --locked --offline --jobs 1 --target-dir $ownedTarget -- -D warnings
cargo build --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --bin offline-qualifier --locked --offline --jobs 1 --target-dir $ownedTarget
cargo build --manifest-path apps/desktop/src-tauri/Cargo.toml --no-default-features --bin locallore-desktop-spike --locked --offline --jobs 1 --target-dir $ownedTarget
cargo fmt --manifest-path apps/desktop/src-tauri/Cargo.toml --all -- --check
```

Measured environment is Windows NT10.0.26300 x64, Rust/Cargo1.93.1 and
Node24.22.1, with existing Tauri2.12.5/Wry0.57/Tao0.37.1 and pinned Windows0.62.2
bindings. No fresh device/model/runtime inventory or platform support claim is
added. These are local development builds, not a clean-machine installer test,
signed package, new byte-reproducibility comparison or public release.

## Retained products and remaining blocker

Bounded local evidence uses the `d09-feasibility-*` stems. Both built images
were copied create-only into a local artifact folder and their hashes checked
before the shared target could be reused. They remain unlaunched; the copies
alone are not a complete application distribution with its prerequisites.
The product record is `d09-feasibility-built-products1.json`.

| Product | Bytes | SHA-256 |
| --- | ---: | --- |
| Development qualifier executable | 1,072,640 | `1f4d85b726323a21185114d98dedc3903c768868443156065e13802e429ccbf5` |
| Normal desktop executable | 37,228,544 | `0b38fcc53e980210eeac9f11f74f02fab06906e042de0a7b5c923fbdf388ea09` |
| Normal frontend | — | `b90efa33524821aef162509ae42399e9ba233c8aa45e670847cfb7e7cdd159f7` |
| Unchanged Cargo.lock | — | `4fb7c498ca0ecc62c4ea1f65c63b370ab4336eb75133d08b3a71f5664156cf93` |

The unresolved ordinary Low-integrity file-access control prevents the proposed
AppContainer feasibility result. No raw-open success or fallback has been
observed; the cause remains unknown. Successful unit tests/builds cannot imply
that the boxed process runs, local I/O works inside it or outbound traffic is
blocked. Managed profile storage absence remains unmeasured after the separate
historical cleanup. Existing whole-app offline/renderer/worker/installation,
privacy acceptance matrix, package/license and physical-phone gates remain open.

Next work is independent source/evidence review of this draft and an explicitly
revised qualification plan for the unresolved environment/control. Do not repeat
the unchanged stopped workflow, weaken gates, change system/repository settings,
merge, release or present this handoff as a security recommendation.
