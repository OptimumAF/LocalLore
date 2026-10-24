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

## Addendum: actual coordinator RED and historical-submit correction

The coordinator subsequently executed the first three immutable oracles at 1816 production plus its test imports: **1 passed / 2 failed**, compile 10.28s/test 0.10s. Both F1's unintended replacement draft and F2's historical-draft mutation were observed; the committed historical retry passed. Test SHA remained `622475ca63abc62ab436788074acf995b7fb104af7a8e76b421d01d5e2c683d4`. These are coordinator executions, not reviewer runs.

Reviewed exact corrective commit `2028ca86d3077b8bc9da7ab80c60b7ff3073aa6d` source-only. It verifies containment of an original cached basis, captures full selected basis, uses bound read-only status for historical requests (absent key → Stale), retains exact current-head bound admission, uses full selected source for the no-provider historical read, and skips typed proposal preview only for an existing historical draft. Store exact-header APIs are unchanged. This addresses F1/F2 in source without blanket rejection of historical requests. Coordinator reports 40 focused tests passed across the new three and existing forwarding/source/maintenance selections; the wider all-feature rerun was still underway at that message. That report is not execution of the additional oracles below.

## F3: explicit Open retains cached outcomes from the old selection

`HostCommand::Open` loads an actual new Engine and assigns it to the existing session, but 1816/2028 retain all cached Turns. A cached committed Request at expected head 1 can outlive an explicit valid rewind from head 2 to its exact prefix 1. If that Request is a draft in the reopened Store, both Submit and TurnStatus read the actual Draft and then return the old cached Committed view. Its original basis can still match because it identifies the prefix before the accepted turn. The result disagrees with the explicitly selected current canonical history; no new canonical commit bypass is asserted.

Commit `1befb008e1b17211ccd773282c1345953208b153` freezes separate status/submit cases. They use real accepted typed receipts, a valid public prefix archive, actual deletion/import and same exact Request redraft. Require queued/no invented receipt and unchanged current Draft/canonical prefix. The oracles permit either coherent successful Open, or Stale refusal followed by old-session fail-closed reads and explicit close/fresh resume. They do not require retaining an unsafe Open behavior.

## F4: clearing the cache alone does not retire admitted Work

Work is outside the Host lock during provider execution. Its completion path performs persistence/status/refresh and mutates a Turn by string key; it does not identify the session selection incarnation. Simply cancelling and clearing cached Turns on Open can therefore make old completion panic on a missing key, insert an old saved result, or cancel/overwrite a newly admitted same-key Turn. An unchanged source prefix is insufficient to distinguish those owners. `generation_input_failure` also finds a turn by session/key and needs the same incarnation check before returning it to Queued.

Commit `61600e03d171262196a4009c3558739981c7b5f2` adds an actual held-production-director case with a valid same-Seed/head/projection but different-receipt replacement, explicit reselection and a new same-key queued owner. Old completion must not panic, replace new presentation, terminalize its actual Draft, or generate extra roles.

Commit `1997aa50e52fdbd888be6915b796b5fdca6bb138` adds the stronger **same actual source** case. No replacement or canonical change occurs; the old Work basis exactly matches. After successful same-source Open and explicit same-key retry, release the held old provider. Its cancelled/retired completion must leave the new owner Queued and the persisted Request Draft, preserve canonical bytes/receipts, make no narrator/extra provider call and drain the old worker. Each test uses bounded five-second owned channels, scoped thread join and release-on-drop; it adds no production hook or model call. They test a new queued owner rather than claim a second provider was started.

The coordinator's proposed repair is a private native session work-owner identity, cloned into Work and rotated only after successful Open resume. Before assigning the new Engine, cancel old Turns, clear their cache and retire/revoke their trace owner; mint a fresh trace owner. `finish_work_inner` must require the same work-owner identity **before any persistence read, refresh or mutation**, and transient input-failure cleanup must require it before cache writes. Failed Open must leave the old selection intact. No serialized epoch, model authority, Store schema change or alternate canonical owner is needed. This repair remained coordinator-owned/pending at this additive source freeze.

The retained reviewer production remains 1816. Seven frozen test cases now have SHA-256 `482fd36e8b56c6226d1250100039b9941c975799b42f4c547a294187418e885f`; the original three oracles were not weakened. All seven remain **uncompiled/unexecuted by the reviewer**. The earlier three-case hash and coordinator RED above remain historical bindings. Final qualification must bind its actual source/unchanged test bytes and retain initial failures; no completion/acceptance claim follows from this addendum.

## Final corrective-source review and coordinator evidence

The coordinator executed unchanged seven-case source at `6d5ebf3`: **3 passed / 4 failed**. The two obsolete Committed views, held replacement Submit returning Stale instead of a fresh queued owner, and same-source Open retaining Running were observed. Initial three-case F1/F2 RED is separately preserved above; do not combine these runs as unique cases. No test oracle was changed to produce the subsequent result.

Reviewed exact final owner correction **`30735b5d07988bad164b8bba4a22f0c0e705fb8d`**, after historical-submit correction 2028, through read-only `git show` and current dependent trace/capture source. It changes Host only:

- Every Session creates a private native `Arc<()>` work owner; Work clones that identity. The finish entry rejects a missing/different incarnation **before any persistence status/read, source refresh, write or cache mutation**. The check and continuation hold the same Host guard, so a simultaneous Open cannot rotate it midway through that local completion.
- Transient generation-input failure similarly filters by owner before resetting a running Turn to Queued. Terminal input failures go through the guarded finish path.
- Explicit durable Open loads the actual Engine successfully before retiring anything. It cancels old Turn tokens, clears cached Turns, rotates the work owner, retires/revokes the old trace owner, creates a new trace owner, then installs the Engine. A failed resume leaves the previous cache/owner/selection intact. Open performs no persisted cancel/fail/stale write or automatic replay.
- Worker admission is not prematurely released by Open: the old Work's existing Drop still releases its count when it actually exits. A held provider may consume its slot until return; no detached-work or hard-deadline claim is made.
- Private capture safety does not depend solely on successful `try_lock` revocation. Retiring `TraceOwner` changes its atomic liveness immediately. Existing CaptureStore record/read/begin sweep clears consent/details and advances its epoch when it observes that retired owner; an old RingSink cannot resurrect raw artifacts into the new epoch. A new trace owner also excludes old metadata from the selected owner's reads. Under contention this is access/epoch fencing, not a promise of immediate physical erasure of every old allocation.

The identity is not serialized, model data, an inspection grant or a new Store authority. Store exact-header/source-bound APIs remain unchanged. No further concrete blocker was found in this finite corrective-source pass. This is not blanket approval, independent approval of the reviewer's earlier Play implementation, or unmeasured platform/capture-export qualification.

Coordinator reports **53 focused tests passed**, including unchanged final review 7/7, six source-fence cases, ten direct bound Store cases, fifteen ownership cases, six production-forwarding cases and nine trace cases. All are coordinator executions; this reviewer ran none. Wider all-target/all-feature qualification was running at that handoff and is not assigned a final result here. The actual final tests retain SHA `482fd36e8b56c6226d1250100039b9941c975799b42f4c547a294187418e885f`.

Reviewer production remains frozen pre-fix in its separate clean tree; only new tests/report were committed. Whitespace checks passed. Claim #11 is released with the exact report commit. Next: coordinator records final broad results at the corrected source and prepares the focused PR; native desktop/Android controls, actual UI/runtime/device integration, model-quality and full milestone gates retain their separate owners and evidence requirements.
