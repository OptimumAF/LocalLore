# M07 final shared integration: source review

2026-10-23. Partial #11 M07.01/.03/.04, with #29 production-consumer prerequisite. Status: concrete admission finding and three frozen source oracles; coordinator correction/execution pending. No acceptance score or complete milestone claim.

## Bound source and ownership

Reviewed coordinator `1816b288e1c57a34e1b2111216b0d1217d4f136f` against accepted main `b90ddc9c0ed955c034a6c1f9e331caf3323e4e9a` (schema 4). Separate `review/m07-final-integration` / `source-m07-final-review` preserves that production unchanged. Claim #11 `6376019374` preceded edits. Own only this new report and `crates/locallore-workspace/tests/m07_final_integration_review.rs`.

The reviewer previously authored the Play 2.4 consumer slice. Its behavior is inspected here as an integration dependency, not independently approved by its own author. The new Host/Store admission finding and test sources below are independent of the coordinator's production implementation. Existing independent review findings and original tests remain unchanged.

| Actual reviewed file | SHA-256 |
|---|---|
| `crates/locallore/src/host.rs` | `2a33973797e9c1e81b8740836708321a91dfe7ac60756805a979a08c68d2fe14` |
| `crates/locallore/src/engine.rs` | `59f504cc3bffa0e1e6414ed2c44ad8091eb2dfb257fd223865275629647db387` |
| `crates/locallore/src/play.rs` | `916e66d814b34500b6b45e421027636f23bc64daf2dc13d230bbc1e46e72a53e` |
| `crates/locallore-storage/src/turns.rs` | `8ca821c4591c60dbbb55ca45aa59289035514803e013c97f19261e3c254a0757` |
| New three-case review test | `622475ca63abc62ab436788074acf995b7fb104af7a8e76b421d01d5e2c683d4` |

## F1: historical Submit still admits under a weaker prefix

In durable `HostCommand::Submit`, 1816 first refreshes the selected Engine with the full source-extension guard. It then derives a basis at `request.expected_revision`, which can be older than the now-selected head. `begin_bound` correctly requires that basis to match the Request header exactly, but this consequently guards only the historical prefix, not the stronger selected history already observed by the Host.

Concrete path: select source A@2; submit a new typed key with expected head 1. The first refresh sees A@2. Between refresh and bound admission, another native owner deletes/imports a valid archive containing the identical accepted prefix A@1. The shorter request basis still matches that source, and actual `Store::begin_bound` sees current head 1, so it inserts the draft. The subsequent Host refresh rejects the rewind as Stale, but the replacement-source draft has already been created. A normal no-race submission at old head 1 would be stale. This is a draft-ownership/admission race, not a demonstrated new accepted-canonical commit bypass.

Commit `9a0a502b213d0abb272d6dce6b446a9746900ae7` freezes the source vector before a fix. The new native `Persistence` wrapper delegates to actual Store methods and injects a valid public deletion/archive import precisely at `begin_bound`; it performs no canonical SQL writes and creates no forged receipts. The test requires Stale, unchanged actual canonical receipts/projection, and **UnknownTurn**, not a newly admitted replacement draft. An early Stale refusal before calling the mutation port is also correct; in that case the original head 2 must remain intact. The callback boundary is a deterministic test injection, not proof of an independently scheduled process race.

The same commit freezes the positive exact committed historical Submit case. After a real accepted suffix advances the selected head, resubmitting the original committed Request must return that same receipt without inference or canonical changes. A fix must not reject every old header and thereby lose idempotent historical outcomes.

## F2: uncached historical draft retry can be terminalized

If the old exact Request already exists as a durable draft, 1816 `begin_bound` returns it. With no cached Turn, the typed preview then runs against the newer selected head and returns Stale; Host calls `finish_bound(... Failed)` under the old basis. A retry that should observe an existing historical draft can therefore change it to Failed. This follows directly from the current control flow and is not yet an executed result.

Follow-up commit `37c009f68f3198351eb65cfe855e61f8b1d2fb18` freezes a third case: admit an actual draft at head 1, independently commit a different typed turn to head 2, resume through a new Host (no cached Turn), then resubmit the exact old draft. Require queued/no invented receipt, unchanged database bytes, the same persisted Draft/Request, and unchanged canonical receipts/projection. No provider is configured or called.

All three tests are **uncompiled and unexecuted by this reviewer**. Preserve their original source and actual setup/RED/GREEN outputs when the coordinator runs them. They do not change existing budgets or fixtures.

## Proposed narrow correction

Keep Store's exact-header `begin_bound`/`commit_prepared_bound` contract. The coordinator's proposed Host-only correction is:

1. Retain/derive the original Turn/Request basis and verify that the actual selected Engine still contains it.
2. Capture the full selected basis.
3. If Request expected head differs from selected head, perform only `status_bound(request, full_selected_basis)`. Return an existing exact recorded outcome/draft; map absent key to Stale. Never call bound admission for that historical header.
4. If heads match, admit using the full selected basis, which also matches the exact Request header.
5. Use the full selected basis for the no-provider free-text historical read too; do not silently adopt a different source or weaken Store to accept arbitrary covering bases for creation.

This uses the existing authority and ports, preserves historical read/retry behavior and avoids a new API or schema. It remains proposed at this source handoff; this reviewer makes no production edits. A later explicit Prepare may correctly detect stale draft work and perform bound cleanup; merely resubmitting an existing historical identity should not do that cleanup.

## Remaining inspected production paths

- **Coherent prepare:** Repository obtains Engine and `CoverageRead` from one actual `Store::context_snapshot` transaction. Host derives the observer from the selected Seed's player, validates scope/head/full Seed and original accepted prefix/private lineage, and carries the same Engine/proof pair to Play. The generation read admits no job and changes no selection/inspection grant. Provider work occurs after releasing Host/Store locks.
- **Source identity:** `AcceptedHistoryBasis` streams a bounded digest over domain, scope/revision, full Seed, immutable selected lineage and exact original receipts. It is opaque/native-only and absent from serialized receipts, archives, schemas and provider data. Ordinary exact-prefix appends are allowed; implicit refresh cannot adopt a rewind or changed prefix/Seed/lineage. Hash comparison is not authorization or imported-history authenticity.
- **Atomic acceptance:** Bound Store begin/status/commit/terminal methods rebuild actual Engine inside existing read or IMMEDIATE transactions. Begin/commit require exact Request basis headers; read/cleanup may use a stronger full selected basis. The checks happen before adoption/mutation, rather than relying on a prior Host read. The new finding is selection of too-short a valid admission basis, not absence of the Store check.
- **Completion and cleanup:** Work retains its source basis. Finish checks actual bound status and original Request, accepts another owner's actual stored winner, and refreshes only an extension. Ready commit verifies its original basis, captures the strongest selected basis and either commits at the exact header or uses full-prefix stale cleanup. Cancel/failure/stale cleanup similarly carries the strongest selected basis into the actual transaction; source rejection must not terminalize a replacement draft. Close uses a full selected basis. Prior source-replacement/cleanup REDs and positive historical cancellation tests remain preserved.
- **Transient errors and ownership:** Snapshot Busy/Full/Database/Unsupported/Internal returns the original key to Queued without provider work. Terminal categories reconcile through persisted outcomes. Work Drop decrements the admitted worker count, including early snapshot errors. Override panic is caught inside the owner guard, and snapshot cancellation true/panic is latched; no claim of a hard real-time cancellation deadline is made.
- **Proof consumer:** Play 2.4 uses the accepted `compile_verified_cancelled` on the actual Engine. Opaque coverage is reverified; rejected/missing coverage follows the actual raw eligible path. Source fallback is recorded separately from compiler Missing. Count-only provenance is not proof, retrieval authority, measured savings or model-quality evidence. Narrator approved-outcome restrictions and Engine canonical/intent validation remain in force; inspection does not select generation knowledge.
- **Historical bytes:** Current generation requires 2.4 context provenance. Recorded 2.1/.2/.3 retain absent context fields and strict history/retry admission; fresh historical prepared receipts remain refused. The 2.3 fixture and original compact-byte probes are preserved. Current-label/future-version test updates are narrow; they do not regenerate old fixtures. The earlier consumer qualification is historical attributed evidence, not new execution in this review.
- **Explicit maintenance:** The native method is separate from HostCommand/JSON, fixes the selected player and exact scope/source, returns bounded status/count metadata, and blocks mutations while same-scope turns are active. Status uses passive lookup; only explicit Admit admits/retargets. Step prepares/publishes one existing chunk, Cancel/terminal Prune use existing job ownership, and completed late cancellation does not undo publication. No scheduler, hidden provider/model call, competing cache, serialized handle or automatic mutation retry after unknown acknowledgment is added. Desktop/Android controls remain separately owned integration work.
- **Compatibility:** Unbound Store APIs retain their existing contract. New bound Persistence defaults return Unsupported, so custom legacy ports fail closed instead of pretending atomic support. This is a native implementer compatibility requirement, not a host-v1 JSON/schema bump. Schema remains 4; no new persistence format is introduced by this slice.

No additional concrete production blocker was found within that finite inspection beyond F1/F2. This is not an exhaustive proof, an independent approval of the reviewer's earlier consumer code, or a replacement for actual regression execution.

## Evidence attribution and exact checks

The coordinator reports 323 default Core/workspace tests, 192 Store tests, and 393 all-feature aggregate tests after correcting the historical archive fixture comparison; strict checks of four packages passed. These are coordinator executions, not tests run by this reviewer, and predate the new three-case oracles. Counts overlap and should not be added as unique cases. Existing `docs/native/M07_GENERATION_CONSUMER_COORDINATOR_VERIFICATION_2026-10-23.md` retains actual source-fence failures, stale-target setup failure, corrections and focused evidence; earlier review documents retain their own source bindings.

The `parent_retention_fixture` correction keeps the packaged historical schema-3 asset unchanged, validates both historical/current archives independently, and compares the complete decoded structure after removing only explicit source-schema metadata and its dependent payload hash. Seed, branch, canonical receipt/state integrity and nested rewind/retained-ID oracles remain. It does not claim a current schema-4 export came from schema 3. The review did not execute that example.

Reviewer checks: Git 2.33.0.windows.2 / PowerShell 7.6.5; read-only issue/source/history inspection, file SHA-256 and staged `git diff --check` passed. Two initial documentation reads used the wrong `docs/storage`/`docs/eval` directory and failed; the actual `docs/native` reports were then inspected. No conclusion depends on absent files. Production diff inspection covered Engine/Host/Play, Store turns/jobs, Repository and maintenance, plus narrow existing test/example changes. No Cargo, rustfmt, Node, Gradle, compiler, native runtime, model, device, ADB, CUA, desktop, settings, download, PR or merge action ran.

Coordinator reproduction after allocating its own sequential slot:

```powershell
cargo +1.93.1 test -p locallore-workspace --test m07_final_integration_review --locked --offline --jobs 1 --target-dir <fresh-owned-target> -- --test-threads=1
```

Use task-owned TEMP/TMP and debug0/incremental0 as in existing qualification, verify the actual source is compiled and retain all setup failures. First run unchanged tests at 1816, then the same tests at the frozen correction; follow with appropriate existing ownership, source-basis, trace, historical replay and strict checks. This command is documentation, not reviewer execution. The next gate is that concrete correction and evidence, then coordinator PR review. Claims are released at handoff; full M07/D07 and platform/model/release gates remain open.
