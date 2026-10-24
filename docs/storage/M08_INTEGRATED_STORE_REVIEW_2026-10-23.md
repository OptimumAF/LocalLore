# Current integrated Store author source review — 2026-10-23

No new concrete safety failure was established in this bounded source review.
This is neither a runtime PASS nor owner acceptance of #12 M08.03/M08.06 or
#8 M04.04/M04.06. No new regression test was added: the reviewed cases already
have meaningful actual-API oracles, and no distinct failing case was found to
justify another implementation-mirroring test.

Reviewed base: `e4d24c4389a75441e7b9f7a6854300fafe29f745` on isolated
`review/m08-integrated-store` / `source-integrated-store-review`. Claims before
this document: [#12](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6378230687),
[#8](https://github.com/OptimumAF/LocalLore/issues/8#issuecomment-6378230869).
Only this new document is owned/changed. Conditional permission for a new
`m08_author_integrated_review.rs` was unused. Existing production, tests,
historical assets, migrations and assertions remain untouched.

## Concrete boundaries inspected

| Area | Source observation and relevant existing oracle |
| --- | --- |
| Full source identity | Store author preparation captures the actual parent's `AcceptedHistoryBasis`, actual Core preparation and immutable preview bytes. Apply compares the full native parent basis inside `IMMEDIATE`, rebuilds the preview through actual Core, and applies the original opaque Core preparation. Equal head/mechanical state is insufficient. Core bases include seed, selected lineage and complete canonical records. Existing Store13 cover parent advance and valid same-head seed replacement; author Play2.5 source test covers B/C private-source divergence and bound rejection. |
| Capability owner | `PreparedStoreAuthorCorrection` has a private owner Arc and no deserializer. Store assigns a fresh Arc in `from_connection`; apply checks pointer identity before using the capability. A second opener, backup clone or reopened Store cannot use another owner's preparation even with equal canonical content. Read-only explicit lookup is the recovery path. Existing Store13 exercise same-file/clone/reopen refusal. |
| Recovery after progress/retention | `lookup` first validates input and child admission, then replays the child's actual retained ancestry. It compares the entire original author input, returns the child's current head and does not re-run the creation guard against the parent's new head. Apply resolves an already-created matching child before fresh parent-basis checks. Parent retirement does not grant public access to that parent; retained ancestry remains private replay input. Collected child tombstones are admitted before existence checks, preventing resurrection. Existing Store13 cover progress, mismatch, parent retirement, excluded-future collection and prebirth/tombstone recovery. |
| Operation/key kind | Author lookup requires a local actual AuthorV1 record and exact input. Ordinary `recorded`/`lookup_turn` check `author_v1` before ordinary Request deserialization and return RetryMismatch. Fork's existing-child path rejects a local AuthorV1 occupant, while inherited author history does not ban unrelated local ordinary keys. Existing symmetric kind/key tests cover these boundaries. |
| Canonical source vs indexes | The response retains the full actual canonical record. `request_index` hashes its exact native serialization, not the projection or a shortened receipt cache. Author readback regenerates that index and compares the stored canonical discriminator/expected revision/full response. Ordinary PlayV2 similarly compares the full serialized wrapper. The index is an integrity/index aid, not a second canonical source. |
| Private normalization | `verify_ledger` distinguishes play versus author rows. Author rows must have exact sequence/key/version/serialized author receipt/record kind and zero witness rows. Ordinary event envelopes and ordered witness sets must equal actual regenerated receipts. Core restores and exact-compares full canonical wrappers, including private discovery source bindings; rehashing an unknown wrapper cannot bypass that regeneration. Existing Store13 have normalized-row/index/witness/kind/rehash corruption cases. |
| Single transaction / budgets | Author apply performs child/registry/projection and author index/event writes in one Store `IMMEDIATE` transaction. It replays actual transaction bytes before publication and compares the complete native basis to the applied Core result. Replay budgets count persisted request/index plus response and inherited prefixes; Core separately bounds record/projection history. Failures before commit drop the transaction. Cancellation catches panicking callbacks; final author cancellation check precedes commit. |
| Actual Full boundary | The inspected private pressure test sets a real SQLite page cap on a synthetic owned Store and requires exact `TurnError::Full`, all application-row rollback, later success using the same preparation, one known retry and reopen. Its source distinguishes genuine Full from synthetic trigger ABORT. This review does not execute that test or claim physical-disk exhaustion. |
| Current staged Play2.5 | Stage is non-Clone/non-Deserialize and keeps full basis, approved native receipt and sanitized evidence. Consuming commit checks winning exact request first, then cancellation/source/regenerated stage/evidence and current record validation; it installs the candidate only after final cancellation. Store current commit revalidates actual prepared output through `Engine::commit_play`, rather than inserting a caller's event list. Bound begin/commit/finish/status use actual native source identities; Workspace adapter forwards those bound methods. Existing author Play3 cover discovery, cancelled draft, bound private-source mismatch and unbound prose revalidation. |
| Retention and migration5 | Current deletion predicates retain only completed canonical prefixes, remove noncommitted workflow beyond retired scope and drop retired projections/derivatives. Core fork/restore handles original scopes and prebirth lineage. Migration005 adds explicit canonical/event discriminators, restricts author rows to committed status and allows projection1/2; projection writes use actual engine domain. No author value is added to actor witness knowledge by DDL. |
| Historical read-only dispatch | `read_history`, `verify_ledger`, ordinary `recorded` and `lookup_turn` query actual schema identity and synthesize legacy discriminator literals before5. They do not require nonexistent new columns for1–4. Exact schema verification still reconstructs the known DDL and does not migrate a read-only opener. Existing independent historical review3 cover completed status/lookup and draft status/lookup/listing across1–4. This is not a claim that author writes run against old read-only schemas. |

Important distinctions retained by the implementation:

- `Engine::receipts()` remains an ordinary receipt view, not complete mixed
  canonical history. Store validation uses `canonical_records()` and actual
  normalized source rows. A receipt-only Domain2 UI/export remains unavailable.
- An unbound prepared ordinary output is revalidated against the actual current
  source; it does not carry a Store owner capability. Worker stale-source
  fencing must continue to use the bound Store/Workspace path. Existing
  cross-source prose rejection is not a guarantee that every unsupported
  natural-language claim can be semantically detected.
- A late cancel/lost response is not rollback evidence. Explicit child/input
  recovery or ordinary original-key lookup determines the actual committed
  state. This source review does not change callback precedence or add a new
  recovery endpoint.
- The in-memory native basis is not an imported archive proof. Archive3 and
  future V2 UI/native decoders remain separately allocated capabilities.

## Source identity

SHA256 values collected directly from the reviewed checkout:

| Reviewed production file | SHA256 |
| --- | --- |
| `crates/locallore-storage/src/author_correction.rs` | `4da6f31bda143f46800c7044173068f315e232cd9dbcc52b556700c1da69d5dc` |
| `crates/locallore-storage/src/turns.rs` | `044c31880fe2b816538b2e4ff67ce198547915697fb608d54f787a56838c4d2f` |
| `crates/locallore-storage/src/branches.rs` | `62c06aa148e22c47b9c2082a3d57c53ac429ad5ce2b666c0ce228c7b557f2f4d` |
| `crates/locallore-storage/src/branch_retention.rs` | `ee04d6d4a1787a9c875e40a374bb3fa048d28bdbe45e8b1560ac0e7ad2e2678a` |
| `crates/locallore-storage/migrations/005_mixed_history.sql` | `e0a382a42ff1cc49c662afacfeF0b2e73174270ad19fe1999c1f4d82d7213f14` |
| `crates/locallore/src/author_correction.rs` | `211d4ead1831d1005872c8f0b0a9a5bda401cb0d2467359544270dc34fa64750` |
| `crates/locallore/src/engine/staged_play.rs` | `4b998fbc2590fa71f3fa371573872857d393884fb91d5173457cc7ebac251bde` |
| `crates/locallore/src/engine.rs` | `d0599b6e088386b3787851efb381cd6be85d5de0d650e3824d654c5333764b56` |
| `crates/locallore/src/play.rs` | `d41fdf1c4815b75ed10c5623d09c3e1c9ef616b647186fec243f687c4ad8ba66` |

## Evidence attribution and limits

Root reported Store13 plus independent historical3, actual author Full,
author Play2.5 integration3, broad Store209 passing/5 old ignores before the
current Play integration, and current Core302 passing across complementary
cohorts. Those are **coordinator-reported results**, not new reviewer execution
or one invented unfiltered run. See Root's current verification report and issue
evidence for exact commands, versions, original failures and retained artifacts.

Reviewer actions: source/API/test inspection, Git checks and source hash
collection; `git diff --check` passed. No Cargo/Clippy/typecheck, Node, Gradle,
SQLite execution, provider, app/native IPC/WebView, emulator/device/model or
desktop/protected-resource action ran. No runtime processes or heavy execution
slot were used.

This pass does not independently replay all 4096-record/16MiB boundaries,
concurrent process races, disk/power loss or every SQLite corruption surface.
It does not requalify platform builds, historical model compatibility, actual
native migration renders or physical devices. No new failure was established
to freeze in the conditionally allocated new regression file; that path remains
uncreated and its conditional claim is released unused.

Next: coordinator completes its already-running native legacy/model compatibility
cohorts and reports their exact results, then prepares the focused shared-author
PR. Keep unimplemented Archive3 oracles on their separate future stack and
retain legacy Domain2 typed consumer refusal until the approved V2 route is
implemented and qualified. No merge, release, milestone closure or owner
acceptance is implied by this independent source review.
