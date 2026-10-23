# Native generation snapshot independent review — 2026-10-23

Partial #11 M07.01/.03/.04, supporting #29 D07.01/.02/.04. Claims #11 comment6374274667 / #29 comment6374274911. Coordinator-delegated reviewer `app_storage_review`; isolated `review/m07-generation-snapshot` / `source-generation-snapshot-review`. Own only this NEW document and NEW `crates/locallore-workspace/tests/generation_snapshot_port_review.rs`. No existing production/original-test edits, PR or merge.

## Exact reviewed boundary and independence

Reviewed final source `3a2206c40cff843dc4ddc70644f338fdeff161aa`, production/test source `e1968eb8d77ab978515f19dcbb3207598398b929`, base coordinator `33e5d3ed36b14bb62d39323fc78701e54d2fe4b5`; commits1a2017b/d9d6bab/830ca4e/d1ae2c6/e1968eb plus final source-author evidence. Scope is the native Host/Persistence/Repository snapshot delta and its actual Store dependency, not future Play/prompt2.4 forwarding or Android/native UI.

This reviewer did not author the new generation-snapshot port or schema4 maintenance owner. The reviewer previously authored parts of the pure coverage/verified compiler input and playable archive implementation; this is not an independent reapproval of all those dependencies. Existing author tests/reports are read as attributed evidence, not reviewer executions.

| Frozen input | SHA-256 |
| --- | --- |
| Core host.rs |a2f340ff43c82f2ace76c3c4da801df2f1167f75f09bff1a0a607f90dcca749a|
| workspace lib.rs |97be177173bf02511372c394f6ad85372e9a0f75d82f6eebeddce8f97c6db438|
| original Core snapshot tests |884fc4c8174ea29a8cfda747d586b1a392e17ffd500e9f9d10e2177f5b9ac13c|
| original SQLite snapshot tests |1ad4b61b43e63db65dd285a8ded7241b3b1546c5f9310860d0d18d34bbc95fd2|
| Store memory_jobs.rs dependency |f36901a65cfb42d7613d9f40b8b6df12dd221db969794dd89f703ddc2e0f5019|
| Store lib.rs dependency |9ef11c943b57f64e3cdc3106d50317355e23de2224e7ef72daa14d82dceae508|

## F1 — selected accepted-prefix and ancestry replacement is not fenced

Source `host.rs:551` retains the selected full Seed and an ephemeral clone only; lines575–584 check returned scope/head/player/full Seed. It does **not** retain/compare the selected accepted receipt prefix or actual selected→root lineage binding. Consequently public Store story deletion followed by independently valid archive import can replace a live selected session's history while preserving exactly the same Seed, selected scope, player and head. A different turn identity can even leave canonical projection bytes identical. A zero-history selected child can be reparented under a different valid ancestor chain while all current checked values and projection/receipts remain identical.

This is a source-derived concrete selected-session correctness gap, not a forged proof or canonical replay bypass: the replacement itself is valid and authoritative in the Store. The gap is allowing the **old live session** silently to consume that different world under an apparently matching revision. The coordinator explicitly confirmed that this session must become Stale. Current schema4 Store publication need not be blocked by this separately unintegrated Host prerequisite.

Do not solve it by requiring cached head==current head, or by comparing only projection bytes. Ordinary other-owner appends of the same accepted prefix are supported: a fresh expected head may exceed the selected cached head. The narrow proposed Host fix preserves full Seed equality, requires no rewind and exact original `Receipt` prefix extension, and compares the existing crate-private `Engine::memory_lineage_binding()` selected→root chain. Original receipt equality includes request/proposal/events/narration/PlayRecord; projection equality alone loses accepted identity/provenance. Lineage binding omits current heads, so genuine parent/external advancement does not itself change ancestry identity. Root owns implementation and any compatibility decision; reviewer does not modify production.

## Frozen original reviewer regressions

Test-only commit **`8f97b22555e7a9a6a55b981c15fe9294e449651e`** precedes every compilation. Exact new test SHA-256 **`b370696a5eff13a0ed2bec7649fa6a1e94bad0dd9c8cbe516daeab908f4b8ecd`**. The five fixed synthetic public API vectors are:

1. Same full Seed/scope/player/head, accepted Wait1 replaced by Wait2: changed canonical truth must return Stale.
2. Same full Seed/head/projection, original accepted turn identity replaced: exact accepted provenance still must return Stale.
3. Same Seed replacement rewinds an already selected completed receipt prefix: return Stale even when caller supplies actual replacement head0.
4. Positive other-owner append of the exact selected accepted prefix: a fresh head2 succeeds and returns the actual Engine, preserving the prefix.
5. Same Seed/scope/head0/empty receipts/projection, selected child is reparented through another valid branch via whole-story archive replacement: return Stale.

Each refusal case checks replacement canonical bytes and receipts unchanged **before** asserting the Stale oracle. Fixtures use actual shared Host and normal Store create/begin/commit/fork/export/validate/delete/import/replay; no raw SQL, JSON archive editing, fake accepted events, private-field access, forged opaque proof or model. Fresh paths combine PID/atomic serial/nanoseconds in task-owned TEMP. Recursive cleanup asserts canonical exact owned path/parent/prefix before deleting only that fixture. The source was inspected for actual u16 tick type before freeze; no compiler error was silently corrected afterward.

At this document's initial freeze no Cargo/test/Clippy has run. The coordinator Android owner holds the compiler resource; the reviewer requested one unchanged focused run after explicit release. Source/rustfmt/whitespace checks passed. All expected failure/pass statuses above are declared **before execution**, not actual measured results yet.

## Other source dispositions

- Repository override (`workspace/lib.rs:190`) calls only `Store::context_snapshot` and forwards its Engine/proof. Store begins one read transaction, strictly restores selected canonical Engine before querying derived jobs, verifies coverage against that same immutable Engine/request and commits the read. There is no second resume after proof, repair, maintenance admission or canonical write. Source coherence is sound for this delta; existing source-author SQLite tests cover actual observer cache separation/nonmutation.
- Default native Persistence uses actual resume and honest Missing; ephemeral Host uses selected immutable clone and Missing. Scope, expected actual head, cached player/full Seed and poison checks fail closed. Native full Engine is **trusted application data, not a redacted character prompt**. No Serialize/Deserialize/HostCommand capability or inspection grant was added. Future production consumer must use the accepted compiler and recheck proof against its actual Engine/observer; this review does not claim that future wiring exists.
- Callback is short/nonreentrant and invoked while Host mutex is held. Final e196's safe wrapper catches callback panic, latches the first true/panic and forwards that same closure through overriding ports. Its final check cannot forget an ignored one-shot cancellation. Source-author d9d6bab and d1ae2c6 REDs are preserved in the original report, with subsequent fixes830ca4e/e1968eb. This reviewer has not rerun those original tests at this freeze.
- Returning a coherent immutable snapshot is not a future canonical lease. Concurrent ordinary append after return can stale later commit. No provider/inference, memory-quality/performance, app/JNI/Android/device, OS/resource-control, protected chat or hosted-network lane is exercised by source review.

## Pending evidence and disposition

F1 is handed to the coordinator immediately. Await explicit portable slot, run unchanged new five-case integration test, preserve exact initial outcome/log before any root fix, then independently inspect/recheck the narrow correction if supplied. Existing author evidence reports272 Core/workspace tests in default/allfeatures,166 portable Core tests and strict Clippy; these remain **author-attributed**, not reviewer pass counts. No favorable-score, full M07/D07 gate or human acceptance is asserted.
