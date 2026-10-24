# Desktop memory-maintenance controls — 2026-10-23

Partial #11 M07.04 and #29 D07.02/.06 integration packet, coordinator-delegated `desktop_runtime_profile`. Branch `impl/m07-desktop-memory-controls`, isolated `source-desktop-memory-controls`, base `c71716a91f6439aac8cca2610c58921bfa6d86f4`. Claims before editing: #11 comment6375747687, #29 comment6375747928; interface refinement #11 comment6375752663. Source/test freeze `ff2e449`, formatting `39f452c`, stale-job regression freezes `7dc4856`/`1a4c3b3`, corrected final source **`0097c93`**. No existing desktop/Core/Host/Store/JNI/schema/capability/build/verification file was edited.

This packet is **not wired into the application**. It does not yet provide an app button, registered IPC or native WebView evidence. The coordinator owns existing main/App/style/build/permissions/verification and the shared archive/fork result-retention integration. No PR or merge was performed here. Broad M07/D07 gates remain open.

## Surface and authority

Visual thesis: a calm secondary inspector surface using the existing application typography and spacing, with no decorative cards or competing color system. Content plan: selected story/timeline/player/head, last observed job/cursor and pending operation/error, then explicit actions. Interaction thesis: accessible pending/error announcements and disabled controls expose operation state; exact context changes remove stale metadata immediately. No decorative animation or new image/dependency is needed for this utility panel.

NEW `MemoryMaintenancePanel.tsx` uses the actual controller external store, native HTML controls, wrapped scope identifiers and `role=status`/`role=alert`. It says derived memory, one bounded chunk, model-generated summaries unavailable, and no changes to canonical events or character knowledge. Ready/Complete/Cancelled/Stale/Blocked, processed-through versus basis revision and a historical Stale failure category are distinct. It does not claim retrieval quality, token savings, inference, performance or all-head coverage from a progress cursor.

NEW `memory_maintenance_commands.rs` registers only the proposed **`memory_maintenance_start`**. It manually parses exactly this payload, rejects unknown keys/fields/actions and bounds identifiers and safe integer heads before admission:

```json
{"request":{"session":"session-1","scope":{"story":"synthetic","branch":"main"},"expected_head":4,"action":"status"}}
```

Actions are `status`, `admit`, `step`, `cancel`, `prune`. There is no actor/observer/grant/job-ID/path/SQL/author/tool input. The actual shared Host selects the Seed player, validates live Session/scope/current source/head and owns Store/CAS/cancellation semantics. The adapter uses the existing `WorkspaceState`, `WindowLease`, same `Arc<ArchiveBroker>` single worker and `Host::memory_maintenance` only. Worker cancellation reads `Work::cancelled` outside the Host lock; no Store, scheduler, broker, service or general execution endpoint is added. Existing **`archive_status` / `archive_cancel`** observe/stop the admitted operation, so no duplicate wrappers or permissions are proposed.

Each successful worker result is a Serialize-only JSON envelope capped at4096 bytes; it binds version/kind/Session/scope/head/action around the existing typed `MaintenanceReply`:

```json
{"version":1,"kind":"memory_maintenance","session":"session-1","scope":{"story":"synthetic","branch":"main"},"expected_head":4,"action":"status","maintenance":{"version":1,"scope":{"story":"synthetic","branch":"main"},"head":4,"action":"status","job":null}}
```

Errors are fixed categories. No raw exception, path, prompt, output, event contents, handle capability or excluded-observer metadata is emitted. The native adapter does not perform a late cancellation check after a successful shared mutation and pretend rollback; window retirement still suppresses delivery through the broker's existing owner fence.

## Controller contract

The frontend context binds `{session, scope, expected_head, player, observer, view, epoch, persistent}`. `player` is the actual selected Seed player actor ID from the existing player snapshot, not a literal actor named `player`. The coordinator maps its Play/player lens to that actual actor and preserves a selection epoch. Other observer lenses and nonpersistent sessions cannot use these controls. Native IPC never receives these frontend actor/lens fields; they are presentation/stale-reply guards, not generation/maintenance privileges.

- Passive Status requires no mutation consent and never admits, repairs or steps a job. Admission is enabled only after a successful no-job observation plus explicit consent.
- One explicit Step admits one bounded shared operation. No automatic Step, restart, pruning, readmission or mutation retry occurs. Cancel job and Stop current operation are different controls: the latter requests broker cancellation and does not invent a persisted terminal state.
- Completed/Cancelled/Blocked jobs can be pruned with new consent. A passively Stale view can represent a persisted Ready row, so it first offers explicit Cancel; it does not blindly offer terminal Prune. The actual saved outcome must be observed before pruning/readmission.
- A known pending operation is observed with the same broker ID. Lost start acknowledgement without an ID leaves uncertainty and blocks mutations; explicit Status attempts a passive shared read and reports `ArchiveBusy` while the old worker remains active. It does not repeat the unknown operation.
- Session/scope/head/player/observer/view/epoch changes clear prior metadata and consent, suppress late responses and cancel known or late-delivered running IDs. A stale panel receives no old-context content. Closed decoder fields, exact request/action/context/operation identity, bounded numbers and detached data guard every response.

An unidentified lost-ack operation cannot be cancelled by an unknown ID using the existing broker. It may finish its one previously authorized chunk under the old still-valid Session/head; output is suppressed on context change. The coordinator must retain this uncertainty across surfaces, avoid silently overwriting unconsumed results and continue honest Busy/status recovery. That global retention/owner integration is deliberately not implemented in this isolated controller packet. No claim of cancelling an unidentified operation is made.

## Frozen checks and actual results

Windows x64, installed Node24.22.1, TypeScript7.0.2, esbuild0.28.2, Prettier3.9.10 and React19.3.1. Dependencies are the existing reviewed lockfile installation, read-only through this checkout's local `node_modules` junction; no package/tool download or update. The coordinator granted short sequential Node-only slots; no Cargo/Gradle/app/worker/model/device execution occurred.

From `apps/desktop`, using the installed `node` and a task-owned `LOCALLORE_CHECK_OUTPUT_DIR`:

```powershell
node check-memory-maintenance-controller.mjs
node node_modules/typescript/bin/tsc --noEmit
node node_modules/prettier/bin/prettier.cjs --check ui/memory-maintenance-controller.ts ui/MemoryMaintenancePanel.tsx ui/memory-maintenance-journeys.ts check-memory-maintenance-controller.mjs
```

| Source/check | Actual result |
| --- | --- |
| Frozen `ff2e449` mock transport/actual controller/strict decoder/inert React semantics |60PASS; no native IPC/render/model |
| Initial frontend formatting |FAIL four NEW files; retained, corrected only by Prettier |
| Formatted same source/oracles |60PASS, TypeScript exit0, format PASS |
| Frozen `1a4c3b3` with new stale-job oracle |Actual RED exit1: Stale Cancel unavailable while Prune offered; original60 assertions unchanged |
| Corrected content committed `0097c93`, same stale oracle |**63PASS**, TypeScript exit0/no diagnostics, format PASS |
| Rust NEW-file `rustfmt --edition 2021`; `git diff --check` |PASS |

Private local evidence is task directory `memory-controls-artifacts`, not tracked. Important hashes:

| Retained file | SHA-256 |
| --- | --- |
| `mock-frozen.log`, `mock-formatted.log` |`22fde999b7c73aff7fdb996b9c55114a2504f16be7093961a4375d583f00fa4a` |
| `format-frozen.log` |`628a86514c4532128049b8fe238fbe2ebb56a97cfe90a76aff73b96ceb1939dd` |
| `stale-mock-red.log` |`029046e6207ee882f172a5547ae66418509fbfbe118302740d7edcddb9471e3f` |
| `stale-mock-green.log` |`c55e97b5808289f660879174f60bbdf9786f6f4c1078042b42758ea6b42a843c` |
| `typescript-final-status.log` |`92e815e93e2c329ea28743b9aebd2709a80e7a65ccae69d56178142aa8e21125` |
| `format-final.log` |`f20510a9da4717c51c4cffee6d0dd88d6c9a723d0a83711d01216f5b48961283` |

The first two TypeScript invocations had empty diagnostics and actual exit0 in command results; their empty Tee stream produced no log file. The final invocation separately recorded its actual exit status. The 63 checks cover consent, one-step/no automatic work, persistent Cancel versus operation Stop, unknown and known lost-ack recovery, Busy, all context fields, strict unknown/foreign/action/revision/operation/unsafe-number/error/capability fields, imported-player eligibility and headless selected-state/error/unavailable copy. Inert React markup is semantic evidence, not pixel layout/native WebView execution.

## Native and app qualification still required

NEW `memory_maintenance_command_tests.rs` contains **five model-free native adapter cases**, not yet compiled/executed: closed input/grants/bounds; actual broker→Host→Repository→SQLite Status/Admit/Cancel/Prune/one Step with canonical nonmutation; shared single-worker Busy/stop; stale/retired owner refusal; and actual passive Stale raw-Ready→Prune Busy→explicit Cancel→Prune. The first four were frozen with the initial source; the fifth was frozen before the controller correction. It uses the same `start_owned` function as the proposed IPC, not a copied adapter.

Coordinator integration must first add the existing-main module line and start handler registration, then run, with a coordinated own target/TEMP and the existing Rust1.93.1 installation:

```powershell
cargo test --locked --offline --jobs 1 -p locallore-desktop-spike --bin locallore-desktop-spike memory_maintenance_commands::tests -- --test-threads=1
```

That is a **pending command**, not an executed result. Root also owns strict native/default/dev checks, shared-current-source compatibility, frontend verification registration, normal-bundle hook exclusion and actual native IPC/WebView layout/error evidence. No Android check was rerun here and no current Android compatibility is inferred from this unwired packet.

NEW `memory-maintenance-journeys.ts` is a fixed development-only synthetic journey for story `memory-controls-synthetic` at head1. It uses these actual controller actions, bounded status observation and five coherent checkpoint names; it refuses other fixtures. Root may wire it only into the development harness and must prove normal-bundle exclusion. It is not imported by the normal app or executed here. No new file/code/shell/server/model/path control is introduced.

Next runnable task: coordinator reviews/integrates the closed adapter/controller and shared cross-surface retention, supplies the fixed synthetic fixture, executes unchanged native tests and actual IPC/WebView journey, inspects wide/narrow app-owned renders and records bounded local errors. Reopen/passive status/lost acknowledgement/observer-switch and zero-canonical-mutation proofs must use the integrated source before claiming a usable app control. Model archivist, prose quality, jobs scheduled in the background and complete M07/D07 acceptance remain unavailable/open.
