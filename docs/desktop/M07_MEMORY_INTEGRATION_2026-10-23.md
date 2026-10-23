# Desktop explicit derived-memory integration — source handoff, 2026-10-23

Partial #11 M07.01/.03/.04 and #29 D07.02/.06; coordinator-delegated `desktop_memory_ui`. **Implemented source, uncompiled and unexecuted in this handoff.** This document does not establish usable native controls, a passing frontend, native IPC, WebView rendering, retrieval quality, Android execution or a completed milestone.

Isolated `impl/m07-desktop-memory-integration` / `source-desktop-memory-integration` starts from desktop `a10d01b`, locally merges frozen Shared `42ca071`, and imports the seven-file prior controls packet `ff2e449` through `d3b7814`. Shared PR #120 subsequently accepted the same production source; coordinator reports merge `a14c899`. No upstream merge was performed by this agent. Initial pre-edit claims: #11 comment6376394226 / #29 comment6376394477; resumed claims6376541770 /6376542021. Coordinator approved imported controller/panel fixes, fixed harness labels/faults, new retention module and closed test vectors before those edits. No competing Store, job scheduler, context compiler or persistence implementation is added.

## Application behavior and authority

The normal app now supplies `MemoryMaintenancePanel` with the selected live session, actual Seed player from the existing player snapshot, accepted scope/head, current observer/view, persistence state and a selection epoch. The panel preserves the existing typography, accent and plain secondary-surface hierarchy. Selected scope/head/observer, job/cursor, pending acknowledgement, displayed player receipt and fixed errors remain together. Narrow widths stack the description list and wrap controls; actual render inspection is still required.

Explicit controls read passive Status, Admit with consent, ONE bounded Step, Cancel the saved job and Prune a terminal job with new consent. A passively Stale view offers Cancel before terminal Prune. No background step, automatic admission, retry or restart is added. Inspector lenses do not grant maintenance access; the native command never accepts an observer/grant. Model-generated summaries remain unavailable. Existing fake inference labeling remains intact.

Only `memory_maintenance_start` is registered in the normal Tauri handler, manifest and exact permission. Its closed, bounded parser and reply come from the prior packet. It calls actual `Host::memory_maintenance` through the existing selected `WindowLease`, `WorkspaceState` and `Arc<ArchiveBroker>` worker. Existing `archive_status` and `archive_cancel` observe/stop admitted operations. Rust owns source validation, jobs, cancellation outcomes and canonical nonmutation. The frontend guard additionally refuses maintenance mutations while its actual gameplay controller has a pending turn; native Host pending guards remain authoritative.

Two concrete synchronous callback hazards were source-identified before execution: subscribers could retire a context after pending notification but before IPC dispatch; and Stop's accepted-result notification could retire a context before a follow-up notice. New frozen mock-controller oracles precede their narrow fixes. Post-notification epoch/disposed checks suppress the retired dispatch/notice. This is source reasoning, **not an actual RED/GREEN claim**.

## Shared broker retention protocol

`broker-retention.ts` is a bounded presentation reservation around the existing native broker. It stores only surface, exact original session/scope/head/action and applicable fixed child/boundary or archive token, plus operation/uncertainty flags. It accepts no prose, paths, SQL, code or general execution. Other archive/fork/memory starts cannot replace an in-flight or unconsumed result. Actual native status/cancel responses update only the same known operation ID. A malformed acknowledgement retains uncertainty.

Context changes do not clear the reservation. For an unknown memory start without an operation ID, recovery is an explicit passive Status on the **original session/scope/head**. A different selection or Stale/Closed result cannot resolve it. A known retired operation is observed by its retained exact ID before a new passive read; no current-operation endpoint is introduced. Unknown passive recovery remains unresolved until a successful exact-original memory Status result; Busy is honest while the native worker still runs.

If that original selection is no longer available, the global panel displays its retained scope/head/action and requires an explicit, identity-bound checkbox plus **Acknowledge unresolved outcome**. This releases the presentation barrier only. Copy explicitly says the operation may already be saved and this neither cancels nor undoes it. The next explicitly requested start still faces the actual native broker's Busy guard. There is no automatic action following acknowledgement. Existing fixed fork recovery hints and archive previews are preserved; this gate adds no persisted recovery ledger.

## Fixed application-owned harness

New `memory_harness.rs` and all native fault branches compile only with `dev-harness`. Trusted local launch environment selects a fresh synthetic workspace and fixed original Mira-only receipt. Renderer input is limited to literal hold/release/lose-ack fixture actions. No model/path/code/shell/file selection or server endpoint is accepted. Normal handlers do not register the fixture command.

`memory-native-journeys.ts` exercises the same normal app maintenance/gameplay controllers and native start/status/cancel IPC. It plans twelve initial checkpoints and two after an actual process restart: passive no-admission, consent/admission, held operation, cross-surface Busy, stop versus saved cancellation, terminal prune, lost acknowledgement, observer isolation, stale completion, actual story/session switch, queued gameplay Busy, one chunk, narrow viewport, and passive reopen without restart. Canonical player context/receipts must remain byte-equivalent. The prior native five-case packet also covers actual Store stale-Ready cancellation before pruning.

Semantic checkpoints include selected story/scope, observer, revision, pending work, displayed receipt, visible errors, controller/job metadata, accessible controls, viewport and user agent. They use existing bounded `harness_checkpoint` and invisible/unfocused WebView2 `CapturePreview`; only its fixed label allowlist is extended. This captures the application's renderer, never the desktop. The runner bounds stdout/stderr to256KiB per child and records truncation and exit status, source/build hashes and actual rendering category. Generated files require a trusted local artifact root and remain local; repository artifact directories and dependency junctions are already gitignored.

The runner deliberately does **not** call a native test a headless render or a headless/mock test native execution. A successful runner still requires manual programmatic-image inspection by the coordinator before layout acceptance. Its normal frontend must be restored and normal hook exclusion rechecked after the opt-in harness build.

## Frozen source and actual checks

| Source | Meaning |
| --- | --- |
| prior packet `ff2e449`..`d3b7814` | Original63 controller/mock assertions and5 native adapter tests; previous author's63 PASS is attributed prior evidence only |
| `ace6dd6` | NEW30 callback assertions, frozen before dispatch-fence fix |
| `c2079e8` | NEW pure retention vectors, frozen before implementation; later fixture reply metadata aligned to the approved exact-recovery protocol before any execution, assertions unchanged |
| `8e14191` / `975ab95` | Initial callback fence and approved unknown-recovery reservation implementation |
| `b1086e9` | NEW fixed native journey oracles before native fixture/fault hook implementation; additional queued-turn/session/observer oracles frozen before execution |
| `992d8f7` | Normal app/native registration, exact permissions and fixed development harness source |
| `4c6c1df` | NEW2 Stop-notification callback assertions before notice-fence fix; total32 callback assertions |
| `bc16f70` | Notice retirement and malformed acknowledgement uncertainty correction |
| `b39af9a` | Rust formatting only |

Actual checks in this delegated source-only session: repository/source/ticket reads, clean checkpoints, `git diff --check` PASS and scoped `rustfmt --edition2021 --config skip_children=true` PASS. **No Cargo, Node, Gradle, app, model, device, browser or desktop-control execution occurred.** No rendered images were generated or inspected here. No dependencies were downloaded or changed. No protected chat/checkout/process was accessed. All new frontend/native/runtime checks below remain pending until the coordinator grants an exclusive resource slot.

## Reproducible pending qualification

Use the installed reviewed Node/dependencies, Rust1.93.1 and the coordinator's bounded, uncapped, locked/offline jobs1 environment. Set own `LOCALLORE_CHECK_OUTPUT_DIR`, target, TEMP/TMP; do not share concurrent build outputs. From `apps/desktop`:

```powershell
node check-memory-maintenance-controller.mjs
node check-memory-callback-review.mjs
node check-broker-retention.mjs
node verify-frontend.mjs
cargo test --manifest-path src-tauri/Cargo.toml --locked --offline --jobs 1 --target-dir <own-target> memory_maintenance_commands::tests -- --test-threads=1
cargo test --manifest-path src-tauri/Cargo.toml --locked --offline --jobs 1 --target-dir <own-target>
cargo test --manifest-path src-tauri/Cargo.toml --locked --offline --jobs 1 --features dev-harness --target-dir <own-target>
cargo clippy --manifest-path src-tauri/Cargo.toml --locked --offline --jobs 1 --all-targets --all-features --target-dir <own-target> -- -D warnings
```

For actual native IPC/WebView qualification, set `LOCALLORE_M07_MEMORY_ARTIFACT_ROOT` to a task-owned local directory and `LOCALLORE_M07_MEMORY_TARGET_DIR` to an exclusively allocated target, then run `node memory-harness.mjs`. It builds the development frontend/native app and runs two own hidden/unfocused processes against the same fixed synthetic database. Inspect all14 planned images, semantic/control states, error buffers, bounded logs and source hashes. Retain every actual failure and correct production/fixture defects without relaxing behavioral oracles. Restore with `node build.mjs`, then rerun `node verify-frontend.mjs` to prove normal hook exclusion. Root owns any final shared/frontend/native/Android compatibility reruns, PR and acceptance.

The prior author's original63 vectors and five native tests are preserved. For an actual callback RED, use frozen `ace6dd6`; for the additional Stop notice RED use `4c6c1df` (earlier dispatch fix already present). These are planned reproducible source comparisons, not executed failures. Full M07/D07, retrieval/model quality, physical-device and final-package gates remain open. Next runnable task: coordinator source review, frontend formatting and exclusive actual focused tests, followed by native render qualification.
