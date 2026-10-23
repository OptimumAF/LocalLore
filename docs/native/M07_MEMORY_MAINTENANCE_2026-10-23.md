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

`MaintenanceReply` is Serialize-only: version1, selected scope, requested current head, action and optional job view. The job view contains only closed status/failure enums and basis revision, cursor and generation. It has no job ID, packet/event IDs, packet text, model context, prompts, paths, source hash or hidden-exclusion metadata. Host validates matching identity/action/version, coherent bounded counters and at most4096 serialized bytes. Errors are fixed typed categories; arbitrary persistence strings map to `Internal`. `last_error` is the historical persisted job failure: a passive Stale view may retain its previous blocked error without claiming the current source is itself blocked. Persisted Blocked still requires an error, and Ready/Complete/Cancelled views require none.

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

## Retained failures and narrow correction

Coordinator source review found that the initial DTO guard rejected a legitimate Store view: a formerly Blocked job becomes passively Stale after a canonical append, while retaining its persisted `last_error`. Two additional oracles were frozen **before execution/fix** at `40064fb517c1cb87771d35cec151a1595424bcd0`. The actual Store fixture changes only derived status to Blocked/Budget, commits a normal accepted append through Store and requires Stale/SomeBudget with database bytes unchanged by lookup. It passed1/1. The actual Host test uses a fixed native port returning that same metadata shape; it failed1/1 at its preserved `unwrap`, receiving Integrity. This is a real executed regression, not a compile-fail stand-in or claim that a production workload exhausted its budget.

`029e0fcf03a100c07276f1820fce136afd68c99f` changes only the new DTO guard to permit a historical closed failure on Stale, while preserving the stricter Blocked and other-status rules. No DDL, persisted parser, job status, canonical invariant or oracle changed. The unchanged Host regression then passed.

The first full nine-Host-test run had8PASS/1FAIL: the fixed test port's `status()` returned Unsupported, so the actual Host's post-generation durable draft observation could not reach Ready. This is retained as a test-fixture failure, not a service semantic pass. Test-only `545273be896cfa781e63b976dc22abf91a1142f9` retains its one submitted draft and returns that matching draft on status. All queued/running/Ready Busy and other original assertions remain unchanged, use actual Host admission/prepare, and then passed. The initial source and failed logs remain available.

## Actual focused verification

Final tested source **`545273be896cfa781e63b976dc22abf91a1142f9`**, Windows x64, Rust `1.93.1 (01f6ddf75 2026-02-11)`, Cargo `1.93.1 (083ac5135 2025-12-15)`. The coordinator released an exclusive sequential Cargo slot. Target `maintenance-rust` and artifacts/TEMP/TMP `maintenance-artifacts` are private task-owned D directories outside Git. Debug info0, incremental0, jobs1, locked/offline; no ambient SQLite flags, new dependencies or downloads. All owned build/test processes exited before the slot was released.

| Actual check | Result |
| --- | --- |
| Host maintenance guard/lifecycle unit selection |9PASS/0FAIL/0ignored,28 other tests filtered; test0.01s |
| Actual Store selected lookup/admission integration |7PASS/0FAIL/0ignored/0filtered; test0.30s |
| Actual Host/Repository/SQLite service integration |6PASS/0FAIL/0ignored/0filtered; test3.63s |
| Three-package all-target/all-feature strict Clippy |PASS,21.10s |
| `cargo +1.93.1 fmt --all -- --check` / `git diff --check` |PASS / PASS |

These are **22 distinct focused tests**, not a full workspace test run. The earlier actual Store shape check and failing Host selection are repeated subsets, not additional passing cases. The strict Clippy command compiles/checks other targets; it does not execute their test bodies or erase unrelated historical suite failures.

The129-receipt fixture exceeds Core's128-receipt chunk bound. It actually published exactly one verified packet after the first explicit Step, with cursor strictly between0 and current head; each later separately authorized Step advanced one generation, ending Complete. Reopen preserved the first cursor without admission or extra work. A repeated Step at Complete and late Cancel preserved the completed view. Canonical state and exact receipts remained unchanged by maintenance.

Other executed cases prove passive database-byte preservation, current-owner-only handle reissue after reopen, player/head/scope and valid same-seed/head receipt replacement refusal, old prepared/handle rejection after public delete/import/new-ID admission, stale-view/explicit retarget, terminal cancellation/prune/re-admit, ignored true/panic callback latching, all cached-session queued/running/Ready guards, poison/default/ephemeral failures, cancellation via AtomicBool outside the held Host lock, and separate NPC/player partition identities. Fixed test ports prove Host boundaries, not SQLite or native UI execution.

The historical blocked-error path has actual Store and actual Host fixed-port coverage, plus source review of their direct Repository mapping. It is not one combined Android/native-app blocked workload, nor proof that a valid workload exhausted the production packet budget. Existing accepted Store tests cover derived blocked-state refusal/prune. No budget was altered to manufacture an outcome.

Commands, from this worktree, using the process-local environment and target described above:

```powershell
cargo +1.93.1 test -p locallore --features host --lib host::memory_maintenance::tests::passive_stale_view_preserves_historical_blocked_failure --locked --offline --jobs 1 --target-dir <own-target> -- --exact --test-threads=1
cargo +1.93.1 test -p locallore-storage --test memory_job_lookup stale_lookup_preserves_historical_blocked_error_without_rewriting_job --locked --offline --jobs 1 --target-dir <own-target> -- --exact --test-threads=1
cargo +1.93.1 test -p locallore --features host --lib host::memory_maintenance::tests --locked --offline --jobs 1 --target-dir <own-target> -- --test-threads=1
cargo +1.93.1 test -p locallore-storage --test memory_job_lookup --locked --offline --jobs 1 --target-dir <own-target> -- --test-threads=1
cargo +1.93.1 test -p locallore-workspace --test memory_maintenance_host --locked --offline --jobs 1 --target-dir <own-target> -- --test-threads=1
cargo +1.93.1 clippy -p locallore -p locallore-storage -p locallore-workspace --all-targets --all-features --locked --offline --jobs 1 --target-dir <own-target> -- -D warnings
cargo +1.93.1 fmt --all -- --check
git diff --check
```

Private retained log hashes:

| File | SHA-256 |
| --- | --- |
| `stale-metadata-red.log` |903f1306dbe664c583f86823d28745a84233b9335244e7be49b57a3980edc095 |
| `stale-actual-store.log` |777c750b3c019f7c08f24197615b6e04f9b8214afc57cd11fdd0a22db6981adc |
| `host-focused.log` (8PASS/1 fixtureFAIL) |8640de93f7a9a1275c0b65b56d14096f91f7e6e82d5b3d6702446dd4f03891d6 |
| `host-focused-fixed.log` |2e5bb5f00fdd4a8f795f2f893dc52893714c6be33cc2d887af5793baf70c281e |
| `store-focused.log` |f9e98856a46ffb10149905d4c3ffb06f847fea89c579377ea1f60926694e9a09 |
| `workspace-focused.log` |1e7bc67c16954675c5e2f7b12a96365638acd600f511884ac17eb937ee6b8922 |
| `clippy.log` |1513084573bc830bfde88ba044493f4a2a97e52c1f56262ec81c4063554a80ec |

Final test source hashes: Store lookup `1299d5da59fdfcfce29bce0ac43a96a29f1d4e19bc8117ad3cffba6a9ddca16c`; Host units `275865ee31da300101657139e27ff0e755d543bab29ec3b8bcc5d33884db1abf`; Repository integration `424c3544e23b0e7095f3317d8734c39ce1257ef7120efc7dca93590f9818e4f5`.

## Reviewable gate and next integration

The native library slice is focused-verified and **in_review**, not self-approved. No Gradle/JVM/JNI, native application/WebView, worker/model, device/ADB/CUA, download, OS/settings, protected-resource, PR or merge action ran here. No existing HostCommand/schema or public job-handle serialization changed. The separately advancing production Play2.4/Host generation-forwarding source is not part of this tested baseline and requires coordinator integration checks.

Handoff authored commits in order: `a96056d`, `3847970`, `40064fb`, `029e0fc`, `545273b`, then the final report-only update. Root owns the shared comparator/bridge and must reconcile its current Host/Repository sources rather than import the duplicate comparator dependency. Root next independently reviews/integrates, qualifies the combined portable/platform source and adds actual native operation ownership/cancellation/retirement around this synchronous API. Full milestone, model-quality, device and final package gates stay open.
