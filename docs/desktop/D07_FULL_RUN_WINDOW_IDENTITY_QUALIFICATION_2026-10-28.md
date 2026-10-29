# Full-comparison window capability: local qualification

2026-10-28 local date; measured commands below ran on 2026-10-29 UTC.
Refs #29 D07.06, supporting #23 native window-lifetime checks.
**The local checks below are qualified at `2401fcd3` under an explicit
one-test-thread protocol.** The focused four-case regression is measured RED
then GREEN. The first broad development-native run failed; that failure remains
recorded. Its unchanged boundary case passed separately, and the unchanged full
suite passed serially. Frontend, build, strict Clippy, formatting and Android
host checks also passed. This is neither merge acceptance nor completion of
D02, D07 or the desktop epic. PR publication and the final security scan remain
pending in this handoff.

This document's author inspected existing source, bounded local logs and process
records only. The author did not compile, test, launch an application, read model
assets or control/capture the desktop. Root owns actual execution, integration,
PR review and acceptance.

## Scope and source attribution

The focused backport starts from accepted main
`d5a6e84c861b8656ca65b4ed66b5387a8cacd4b7`. It supports the existing Protocol 3
full-comparison service: version 1 scripted metadata and version 2 approved-native
metadata. It introduces no Protocol 4 symbols, authoring dependency from draft
#225, new canonical state, storage schema, inference owner or renderer fields.

| Source | Meaning |
| --- | --- |
| `27bab9ef5b723dcf0c1816343ccf8ecc701cdfcd` | Independent four-case test/contract freeze and test-module registration; no production fix |
| `dc73db7471c65e344c09c9abc067b200c8857c63` | Source-only fixture calibration before implementation: require `retained` on the initial metadata lookup, without inventing a phase reset after close |
| `6ffac4926fcb46fcf36c8d72c76bd661dd2a97c0` | Production backport in exactly `lease.rs`, `evaluation.rs` and `evaluation/comparison_run.rs` |
| `2401fcd3914550c073062248d472063b4e16f4c3` | Formatting of those production files and the new test fixture; the assertions and production semantics remain unchanged |

The production backport has the same patch ID as reviewed `35630d3e` on the
separate scene-integration stack. That relationship does not import the other
stack's test results into accepted main. The direct main-source measurements
below are the evidence for this backport.

Both full-run mint sites now scope token reuse to the existing native
`WindowLease`'s private `Arc` allocation identity. Tokens retain only `Weak`
identity references. Status, resume, cancel and close validate that identity,
the numeric epoch and the run lane before refreshing token expiry or performing
the control. Explicit authorized lookup from another lease obtains its own
capability rather than transferring the original token. No serialized identity,
new counter or parallel window/inference manager is introduced.

Ordinary minting keeps its original reuse defaults. The existing access-time
expiry, four-handle per-epoch bound and LRU logic remain unchanged. The full-run
identity map is pruned against existing tokens and on close/epoch retirement;
lock acquisition remains parent state then full-run state.

Scope limit: existing `EvaluationManager::retire` and `drain` remain epoch-wide.
This change does **not** establish independent multi-window retirement isolation.
The reviewed capability cases distinguish same-epoch typed leases for lookup
and token controls; they do not prove a separate multi-window application model.

## Actual commands and results

All thirteen completed process records report a clean initial tree, unchanged source
at command exit and no dirty files. Commands ran from a physical D: checkout,
with process-local `TEMP`/`TMP` set to `D:\Dev\_Temp`, Cargo cache and target on D:,
locked/offline dependency commands and Cargo jobs 1. A Cargo build-job limit does not
specify libtest concurrency.

The local gitignored evidence root contains the following `.log` and
`-process.json` pairs. Times are complete command durations, including compilation
where applicable, rather than turn/runtime latency measurements.

For reproduction, substitute an existing task-owned physical D: target for
`<owned D: target>`, run from the owned D: checkout and set `CARGO_HOME` to the
owned D: cache containing the exact locked packages. Original local process
records retain the exact private checkout, cache, target and evidence paths;
their basenames and SHA256 anchors below identify the measured executions.

| Evidence prefix | Source | Exit and measured result | Command seconds |
| --- | --- | --- | ---: |
| `d07-main-window-clean-before-baseline1` | `dc73db74` | Exit 0; clean only the six owned project packages in the existing target, removing 528 files / 732.7 MiB | 1.8556885 |
| `d07-main-window-baseline1` | `dc73db74` | Exit 101; four cases executed, 0 passed / 4 failed; test time 0.24 s | 28.8567389 |
| `d07-main-window-first-green1` | `6ffac492` | Exit 0; the same four cases passed, 0 failed; test time 0.36 s | 13.1220237 |
| `d07-main-window-full-dev-rust1` | `2401fcd3` | Exit 101; 250 passed / 1 failed / 9 ignored; test time 306.32 s | 329.1087729 |
| `d07-main-window-boundary-isolated1` | `2401fcd3` | Exit 0; the unchanged failing broad-run case passed in isolation; test time 3.50 s | 4.1097070 |
| `d07-main-window-full-dev-rust-serial1` | `2401fcd3` | Exit 0; 251 unit tests and 2 contract tests passed, 9 ignored; unit-test time 641.08 s | 642.5067157 |
| `d07-main-window-dev-clippy1` | `2401fcd3` | Exit 0; development-feature Clippy on all targets with warnings denied | 15.2826221 |
| `d07-main-window-rustfmt1` | `2401fcd3` | Exit 0; Rust formatting check | 0.5302155 |
| `d07-main-window-frontend1` | `2401fcd3` | Exit 0; full frontend verifier, including strict TypeScript, request/schema checks and absence of development hooks in the normal frontend | 13.7379577 |
| `d07-main-window-normal-native1` | `2401fcd3` | Exit 0; normal native build without default features; built application unlaunched | 15.9613308 |
| `d07-main-window-normal-clippy1` | `2401fcd3` | Exit 0; normal-feature Clippy on all targets with warnings denied | 7.6577820 |
| `d07-main-window-android-host1` | `2401fcd3` | Exit 101; nonexistent manifest path, a setup failure rather than a product test | 0.1321509 |
| `d07-main-window-android-host-corrected1` | `2401fcd3` | Exit 0; corrected Android Rust crate check on the Windows host, all targets | 5.6020926 |

The clean command was:

```text
cargo clean --manifest-path Cargo.toml --offline -p locallore -p locallore-storage -p locallore-workspace -p locallore-android -p locallore-eval -p locallore-desktop-spike --target-dir <owned D: target>
```

The baseline and first GREEN used the identical command and unchanged oracles:

```text
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --features dev-harness --bin locallore-desktop-spike --jobs 1 --target-dir <owned D: target> evaluation::comparison_run::window_identity_review:: -- --nocapture --test-threads=1
```

The four cases cover existing scripted/native Protocol 3 same-epoch independent
handles, same-owner reuse, reciprocal stolen status/cancel/resume/close refusal,
dropping the original lease, and the unchanged four-handle/LRU bound. The two lane
cases compare application model-manager status, and all cases compare complete
quiescent fixture file bytes. The fixture contains typed wrapper metadata only:
no work directory, report, accepted receipt, canonical Store or model output.

The baseline failures are behavioral rather than compiler/setup failures:
explicit lookup by another lease reused the same token, a dropped owner's token
was accepted by another same-epoch lease, and the four independent allocations
did not receive distinct handles. After applying only the production fix, those
same four cases passed. Source fixture calibration preceded both measured runs.

The broad development-native command was:

```text
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --features dev-harness --all-targets --jobs 1 --target-dir <owned D: target>
```

It supplied no explicit test-thread override; the exact runtime thread count was
not recorded. The failed existing case was
`evaluation::tests::boundary_cancel_resume_old_operation_and_retired_lease_are_fenced`.
Its unchanged 30-second boundary wait panicked with `completed_cases: 6`,
`running: true`, phase `running`, operation 2 and no reported operation error.
The test and deadline already existed in accepted main; this backport did not
alter either. Other tests also emitted long-running notices in that attempt.

Root then ran that same case and assertions without changing the source or
deadline:

```text
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --features dev-harness --bin locallore-desktop-spike --jobs 1 --target-dir <owned D: target> evaluation::tests::boundary_cancel_resume_old_operation_and_retired_lease_are_fenced -- --nocapture --test-threads=1
```

The isolated pass establishes a narrower successful execution. It does not make
the broad attempt GREEN or prove why that attempt failed. Resource contention
is a plausible explanation, not a measured causal conclusion. The default-
concurrency failure remains retained and must remain visible in the PR/evidence.

Root subsequently ran the full suite at the same clean `2401fcd3` source with
only the test-thread protocol made explicit:

```text
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --features dev-harness --all-targets --jobs 1 --target-dir <owned D: target> -- --test-threads=1
```

All 251 unit tests, including the boundary case, and the 2 artifact-contract tests
passed. No assertion or 30-second deadline was changed. The 9 ignored cases
comprise 8 explicit opt-in model-asset cases and 1 Windows symlink-privilege case;
they did not run and gain no qualification from this pass. The serial result
qualifies that execution protocol. It does not make the earlier default-
concurrency attempt successful or establish its cause.

The remaining completed commands were:

```text
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --features dev-harness --all-targets --jobs 1 --target-dir <owned D: target> -- -D warnings
cargo fmt --manifest-path apps/desktop/src-tauri/Cargo.toml --check
D:/CodexLocalLore/01a165d9-ff25-7500-a550-1099087d4e37/d09-build-security/node-v24.22.1-win-x64/node.exe apps/desktop/verify-frontend.mjs
cargo build --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --no-default-features --jobs 1 --target-dir <owned D: target>
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --no-default-features --all-targets --jobs 1 --target-dir <owned D: target> -- -D warnings
cargo check --manifest-path apps/android/native/Cargo.toml --locked --offline --jobs 1 --target-dir <owned D: target>
cargo check --manifest-path crates/locallore-android/Cargo.toml --all-targets --locked --offline --jobs 1 --target-dir <owned D: target>
```

The first Android command failed because `apps/android/native/Cargo.toml` does
not exist. Root corrected only that command's manifest path and added the
all-targets check; no source fix or dependency upgrade was required. The corrected
check is a Windows-host compile check of `locallore-android` and its targets. It
is not an Android ABI build, JNI/device execution, Gradle check, emulator run or
physical-phone qualification. The normal native application was built but not
launched; Clippy's all-targets checks do not imply that normal-feature tests ran.

## Reproduction and environment limits

From the physical D: checkout, set `TEMP`/`TMP` inside the commanded shell before
project tools, retain the existing D: Cargo cache, and select an owned D: target:

```powershell
$env:TEMP = 'D:\Dev\_Temp'; $env:TMP = $env:TEMP
$env:CARGO_NET_OFFLINE = 'true'
$env:CARGO_BUILD_JOBS = '1'; $env:CARGO_INCREMENTAL = '0'
$env:CARGO_PROFILE_DEV_DEBUG = '0'; $env:CARGO_PROFILE_TEST_DEBUG = '0'
$env:LIBSQLITE3_FLAGS = ''
# Set CARGO_HOME and --target-dir to existing owned D: paths before commands above.
```

No global cache/SDK settings or installed tool locations were changed by these
recorded commands. The source pins Tauri 2.12.5 and requires Rust 1.93.
The fresh `d07-main-window-versions-20261029.json` observation was captured at
`2026-10-29T04:58:46.4425223Z` on the same `2401fcd3` source:

| Tool or environment | Recorded value |
| --- | --- |
| Rust | `rustc 1.93.1 (01f6ddf75 2026-02-11)` |
| Cargo | `cargo 1.93.1 (083ac5135 2025-12-15)` |
| Node | `v24.22.1` |
| PowerShell | `7.6.5` |
| OS | `Microsoft Windows NT 10.0.26300.0` |
| `TEMP` and `TMP` | `D:/Dev/_Temp` |

This fresh observation supersedes the earlier document's historical October 25
version context for these measurements. It does not supply a WebView/runtime,
Android device, model or worker version, because those were not exercised by
this focused check set.

## Pending acceptance and evidence boundaries

- The exact local checks listed above are complete at `2401fcd3`. Qualification
  applies to those sources, commands and limits; later integration changes need
  appropriate verification of their own.
- The failed default-concurrency broad run and nonexistent-manifest setup attempt
  remain retained. No default-concurrency success or causal diagnosis is claimed.
- Focused PR publication, final evidence review, exact-head GitGuardian and owner
  acceptance/merge remain **PENDING** in this handoff. No milestone task is
  checked or closed by this document.

The focused capability cases are Rust desktop-service unit tests, not native IPC,
WebView rendering, manual interaction, actual inference, worker cleanup or phone
execution. The
finite metadata fixture and unchanged model status do not independently count
reserve-and-release calls. Synchronous stolen-token rejection plus source review
support the intended before-admission boundary. There is no new prose-quality
or human approval result; the prior model-sample judgment remains needs
improvement. Observer knowledge/generation permissions and canonical validation
remain with the existing shared Rust engine.

Process-record SHA256 anchors for the retained completed measurements:

| Record prefix | `-process.json` SHA256 |
| --- | --- |
| `d07-main-window-clean-before-baseline1` | `3284ae76a11028355d939bae5cc3dab01a52d9e6936093c4851c4f0387812964` |
| `d07-main-window-baseline1` | `56c49360e2075671086c20f811f4650a252ef3e038eb0057d9dcff81039ea217` |
| `d07-main-window-first-green1` | `1df58c2eeffe4b1b3faee238f3aae24a426b99b59cc95ba224b4773cd9733e0c` |
| `d07-main-window-full-dev-rust1` | `e3df21932fe06e6a3437e2359e67340d78efb53cdd3b362e981938b6b400ab7d` |
| `d07-main-window-boundary-isolated1` | `dba7199609975bd1a7fd7d1fbf64123a10b89a0c2dd52e8ffcd28a6a1da74fcd` |
| `d07-main-window-full-dev-rust-serial1` | `f623e946275e84c2bef0c8731f70636d36e603f49794284ad8a778c40e356c58` |
| `d07-main-window-dev-clippy1` | `48be36dca983ae3f3f52cc938ac7e4b952ae96c492b6a1003426ceabacf7cc20` |
| `d07-main-window-rustfmt1` | `064f56b783c4423dcdbcc06f625566d099589eb2aff6cb2c344f33ad5559ebe0` |
| `d07-main-window-frontend1` | `7c031cd6e5e97942bc78221bd36f0f85ea00527112b1b9665da238a8c130b329` |
| `d07-main-window-normal-native1` | `9d5ce695de935a23e15092856f1ac3b2890a8e1bd6a77efad13376e413992c9e` |
| `d07-main-window-normal-clippy1` | `ff4cf6c06b60f8b76fdd4dbce64ab8220d984116279423b99f281ab8aa2ff52d` |
| `d07-main-window-android-host1` | `0a662d6a1f211aa8a92d1fe4a4e7df48408a40560d36b937fb00bb1693e81d16` |
| `d07-main-window-android-host-corrected1` | `e8c65fd45029425548749057de440082b89b1760b2334521dab8265031674b10` |

The fresh version-record SHA256 is
`3b81ca4f4a392e4f3631056f4e9ace0ac7b462a050d80b597ea7c5fd6eb17056`.

The [contract](D07_FULL_RUN_WINDOW_IDENTITY_CONTRACT_2026-10-28.md) retains the
pre-implementation source freeze and its limits. Root owns final PR/scan/merge
evidence and must preserve this failure history when reporting acceptance.
