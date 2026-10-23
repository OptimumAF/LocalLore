# Explicit native memory maintenance — 2026-10-23

Partial #11 M07.04, supporting M07.03 and #29's production consumer prerequisite. Coordinator-delegated `desktop_runtime_profile`; separate `impl/m07-memory-maintenance` / `source-memory-maintenance`, accepted base `b90ddc9c0ed955c034a6c1f9e331caf3323e4e9a`. Claims before edits: #11 comment6374667239 and #29 comment6374667610. This is one native library service over the existing schema4 Store, not a scheduler, new cache, model archivist, app UI or full M07/D07 acceptance.

## Frozen interfaces and ownership

Initial source and20 new test oracles frozen **before compilation** at `a96056d7fef32516e7d036e086f4d77b8ac2d746`. Own production paths are narrow additions to `crates/locallore-storage/src/memory_jobs.rs`, new `crates/locallore/src/host/memory_maintenance.rs` and new `crates/locallore-workspace/src/maintenance.rs`. New focused tests live alongside those interfaces. Root owns existing Host/Repository files and all Core/schema/Play/app/Android integration.

Two separately marked local dependencies precede the authored slice:

- `fd7176a` imports only coordinator `705f6bb`'s pure `Engine::extends_accepted_history` comparator. Root already owns that change; do not import this duplicate dependency on handoff.
- Coordinator-authored `e6fe552f838ad42a10bbfdb5f48c5e443f9e9853` adds only the Host module line/default Persistence method and Repository module/trait delegation. Root must integrate that bridge with the new modules; this author did not edit existing `host.rs` or workspace `lib.rs`.

Native-only entry point:

```rust
Host::memory_maintenance(
    &self,
    session: &str,
    scope: &Scope,
    expected_head: u64,
    action: MaintenanceAction,
    cancel: &dyn Fn() -> bool,
) -> Result<MaintenanceReply, MaintenanceError>
```

The trusted native Persistence port receives the actual cached selected `&Engine`, expected head, typed action and cancellation function. Its default is `Unsupported`. No `HostCommand`, JSON schema, deserializable grant, native handle or renderer-controlled observer is added. The Repository fixes the observer to `selected.seed().player`.

`MaintenanceReply` is Serialize-only: version1, selected scope, requested current head, action and optional job view. The job view contains only closed status/failure enums and basis revision, cursor and generation. It has no job ID, packet/event IDs, packet text, model context, prompts, paths, source hash or hidden-exclusion metadata. Host validates matching identity/action/version, coherent bounded counters and at most4096 serialized bytes. Errors are fixed typed categories; arbitrary persistence strings map to `Internal`.

## Explicit operations

| Action | Behavior |
| --- | --- |
| Status | Passive selected lookup. Missing stays missing. Reopen reissues a Store-instance-only handle internally without admission, retarget, repair or write. A changed source may be reported as a stale view without rewriting the persisted job. |
| Admit | Explicit create/retarget via `ensure_selected_memory_job`. Existing cancelled state remains terminal; this never silently restarts it. |
| Step | Lookup only, then at most one existing Store prepare/publication. Never implicitly admits or retargets. Complete/blocked returns its current terminal view without another computation; cancelled/stale refuses. |
| Cancel | Existing persisted job cancellation through Store. A late cancellation does not relabel a completed publication as rolled back. |
| Prune | Existing Store prune; Ready remains Busy. Missing is an idempotent absent result. Re-admission is a separate explicit Admit action. |

There is no automatic loop, timer, background worker, alternate database connection, arbitrary path/SQL/code endpoint or inference call. After an uncertain Step acknowledgment, read passive Status. Automatically replaying Step is not an exact-once operation guarantee; a newly authorized Step can advance a further chunk. Caller/native broker lifecycle and request deduplication remain separate integration responsibilities.

## Source and transaction authority

`lookup_memory_job(request, selected, cancel)` rebuilds the actual strict Engine in one Store read transaction, validates exact scope/head and selected player, then calls the shared accepted-history comparator. The comparator covers scope, full Seed, no revision rewind, exact original receipt-prefix extension and immutable lineage. A matching head or projection alone is insufficient. The lookup reuses the Store's existing job parser and native owner token, never reconstructing a handle from caller-supplied JSON or a separate database.

`ensure_selected_memory_job` delegates to the existing admission implementation with an optional selected basis. It applies that same guard in both the initial strict read and the existing IMMEDIATE publication transaction. Existing public actor-general `ensure_memory_job` delegates with no selected basis and retains its behavior; NPC partition capability is not removed from the underlying Store.

After lookup, existing Store handle/prepare/publication rules still own authority. Public story deletion removes old job rows, while AUTOINCREMENT job IDs do not reuse deleted IDs; public archive import does not restore job/cache rows or reset that sequence. A recreated same-source job therefore cannot acquire an old native handle's ID. Cross-Store/reopen native owner tokens remain distinct. Prepare/publication additionally compare the full stored source fingerprint, generation and independently rebuilt packet. A new test uses actual public delete/import/re-admission and an actual old prepared token to verify this argument; it does not inject canonical SQL.

Host serializes the operation with local gameplay admission. Every mutating action refuses active queued/running/Ready work on the selected scope across cached sessions. Status may observe while such work exists. Wrong/closed sessions, wrong scope and poisoned owner fail closed; ephemeral/default legacy persistence explicitly reports Unsupported. Story Lab privileges do not change the selected player or expand generation knowledge.

## Cancellation and lifecycle limits

The native owner must call on its IO worker and change its operation AtomicBool outside Host. Cancellation callbacks must be short, non-reentrant and must not take Host/Store locks or perform IO. The service wraps true/panic as a latched cancellation; callback exceptions cannot poison gameplay state. An override panic is caught inside the Host lock and becomes Internal.

Read operations check cancellation again before returning. A successful mutating Store return is a committed outcome; the service does not poll a newly arriving cancellation afterward and falsely claim rollback. An already observed cancellation cannot be ignored by an override. Existing Store transaction checks determine whether publication or cancellation won.

Cancelling an operation aborts that particular computation/publication, retaining the last durable boundary if one exists. It is different from explicitly cancelling the persisted job. Explicit Cancel stores terminal cancellation; restarting requires explicit Prune and Admit. Close/window retirement and owned worker draining belong to the future native lifecycle adapter; this synchronous library does not claim it has implemented them.

One chunk bounds output/work admission according to existing Core limits; it is not a hard real-time deadline. Strict Engine replay and whole-source fingerprinting still have existing history-dependent cost and cancellation checkpoints. No independent process termination, arbitrary timeout, new benchmark or latency claim is introduced.

## Verification status

At this initial documentation freeze, only source reads, format and whitespace checks ran. The coordinator owns the compiler slot for the separate Play consumer. No Rust tests or Clippy, Gradle/JVM/JNI, native app/WebView, worker/model, device/ADB/CUA, download, settings, protected resource, PR or merge ran for this slice yet. Source/tests are implemented but **unverified/in_progress**, not a passing service.

Frozen planned focused checks are six actual Store lookup/admission tests, eight actual Host admission/lifecycle tests with fixed test ports, and six actual Host/Repository/SQLite integration tests. The129-receipt fixture deliberately exceeds Core's128-receipt chunk bound; the test requires exactly one verified packet after the first explicit Step and unchanged canonical receipts/state across completion and reopen. Other cases cover passive byte preservation, current-owner handle reissue, player/head/scope and receipt replacement, cancelled/pruned/re-admitted jobs, ignored true/panic callbacks, pending/poison guards, AtomicBool cancellation outside Host lock and separate NPC/player partitions. Fixed test ports are not SQLite or native UI evidence.

Blocked-state forwarding is source-reviewed; existing accepted Store tests cover derived blocked-state refusal/prune. This slice does not claim a valid workload actually exhausted the production packet budget. No oracles or budgets are changed to force that outcome.

Next: obtain an exclusive coordinator build slot, execute the frozen focused tests with locked/offline/debug0/incremental0/jobs1 in an own D target, preserve setup/semantic failures, run appropriate strict scoped checks, update this report with exact source/environment/results and hand off immutable commits for independent review. Root then integrates actual maintenance ownership and the verified Play consumer. Full milestone, model-quality, device and final package gates stay open.
