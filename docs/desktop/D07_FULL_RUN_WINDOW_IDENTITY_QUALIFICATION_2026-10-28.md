# Full-comparison window capability: accepted-main verification draft

2026-10-28 local date; measured commands below ran on 2026-10-29 UTC.
Refs #29 D07.06, supporting #23 native window-lifetime checks.
**In progress.** The focused four-case regression is measured RED then GREEN.
The first broad development-native run failed; its unchanged boundary case
passed separately. The serial broad run and subsequent compatibility checks are
**PENDING** in this document. This is neither merge acceptance nor completion
of D02, D07 or the desktop epic.

This document's author inspected existing source, bounded local logs and process
records only. The author did not compile, test, launch an application, read model
assets or control/capture the desktop. Root owns actual execution, integration,
the remaining checks, PR review and acceptance.

## Scope and source attribution

The focused backport starts from accepted main
`d5a6e84c861b8656ca65b4ed66b5387a8cacd4b7`. It supports the existing Protocol3
full-comparison service: version1 scripted metadata and version2 approved-native
metadata. It introduces no Protocol4 symbols, authoring dependency from draft
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

All five completed process records report a clean initial tree, unchanged source
at command exit and no dirty files. Commands ran from a physical D: checkout,
with process-local `TEMP`/`TMP` set to `D:\Dev\_Temp`, Cargo cache and target on D:,
locked/offline dependencies and Cargo jobs1. A Cargo build-job limit does not
specify libtest concurrency.

The local gitignored evidence root contains the following `.log` and
`-process.json` pairs. Times are complete command durations, including compilation
where applicable, rather than turn/runtime latency measurements.

| Evidence prefix | Source | Exit and measured result | Command seconds |
| --- | --- | --- | ---: |
| `d07-main-window-clean-before-baseline1` | `dc73db74` | Exit0; clean only the six owned project packages in the existing target, removing528 files/732.7MiB | 1.8556885 |
| `d07-main-window-baseline1` | `dc73db74` | Exit101; four cases executed, 0 passed/4 failed; test time0.24s | 28.8567389 |
| `d07-main-window-first-green1` | `6ffac492` | Exit0; the same four cases passed, 0 failed; test time0.36s | 13.1220237 |
| `d07-main-window-full-dev-rust1` | `2401fcd3` | Exit101; 250 passed/1 failed/9 ignored; test time306.32s | 329.1087729 |
| `d07-main-window-boundary-isolated1` | `2401fcd3` | Exit0; the unchanged failing broad-run case passed in isolation; test time3.50s | 4.1097070 |

The clean command was:

```text
cargo clean --manifest-path Cargo.toml --offline -p locallore -p locallore-storage -p locallore-workspace -p locallore-android -p locallore-eval -p locallore-desktop-spike --target-dir <owned D: target>
```

The baseline and first GREEN used the identical command and unchanged oracles:

```text
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --features dev-harness --bin locallore-desktop-spike --jobs 1 --target-dir <owned D: target> evaluation::comparison_run::window_identity_review:: -- --nocapture --test-threads=1
```

The four cases cover existing scripted/native Protocol3 same-epoch independent
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
Its unchanged 30-second boundary wait panicked with `completed_cases:6`,
`running:true`, phase `running`, operation2 and no reported operation error.
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
recorded commands. The source pins Tauri2.12.5 and requires Rust1.93. An existing
local version snapshot, `d07-selected-consumer-current-versions.txt`, was recorded
on 2026-10-25 at a different source: PowerShell7.6.5, WindowsNT10.0.26300.0,
rustc1.93.1 (`01f6ddf75`), cargo1.93.1 (`083ac5135`), x86_64-pc-windows-msvc and
Node24.22.1. It is historical environment context, **not** a fresh version capture
for these October29 UTC runs. Root should record current versions with final
verification if required; no current-version result is invented here.

## Pending acceptance and evidence boundaries

- The same broad development-native suite with explicit one-test-thread protocol
  is **PENDING** here. Root dispatched it without changing the assertions or
  their deadlines; no result from that ongoing run is incorporated in this draft.
- Frontend, normal-build Rust, strict Clippy, formatting-result capture, Android
  dependency/compatibility checks and any final integrated reruns are **PENDING**.
- Final evidence review, exact-head GitGuardian, focused PR and owner acceptance/
  merge are **PENDING**. No milestone task is checked or closed by this document.

These are Rust desktop-service unit tests, not native IPC, WebView rendering,
manual interaction, actual inference, worker cleanup or phone execution. The
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

The [contract](D07_FULL_RUN_WINDOW_IDENTITY_CONTRACT_2026-10-28.md) retains the
pre-implementation source freeze and its limits. Root must append actual later
results with their own revisions, commands and failure history before claiming
the focused change qualified for acceptance.
