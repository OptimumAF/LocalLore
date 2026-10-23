# Branch-aware derived caches — shared prerequisite, 2026-10-23

Status: implemented and independently reviewed/tested, in_review; not full
M07.03/.04, M08.01 or D08 acceptance. Contributor `/root/app_storage_review`;
coordinator review and final integration are recorded in
[the integration review](M07_DERIVED_LINEAGE_REVIEW_2026-10-23.md). Claims #11 comment 6361263296 and #12
6361263601. Isolated branch `impl/m07-derived-lineage`.

## Source and interface boundary

Implementation `a034e44`, final test/reconciliation
`2b5028aa489fd4d4ceab1b7d56203cdf4ce27fb2`. Accepted main
`2f4efc29e989823a4cf6abf35e2a42fcfc8ee218` was reconciled locally in `a80983d`.
The net source/test diff is six storage-only files: derived module, Store memory
helper/wrappers, new actual-Store test, and narrowly obsolete child-cache
expectations in prototype/durable-branch/lineage-consumer tests.

No public Store signature, public request/result type, packet v1 JSON shape,
schema 2 object, dependency, Engine, Host, compiler, native/app or Android source
changes. `MemoryError::Unsupported` remains for unsupported schema access; an
empty supported child cache returns NotFound. No caller can supply a replacement
Engine or construct/deserialize `PreparedMemory` through a public API.

## Canonical authority and transactions

Removing the old child rejection alone would have been incorrect: the old head
query selected roots only, source fencing assumed every event belonged to the
target branch, and Store replay and cache reads used separate transactions.

Each public memory operation now loads the normal strict `turns::read_engine`
**inside its own operation transaction**. This reuses the accepted branch loader,
original receipt scopes, canonical event/witness validation, completed boundary
and lineage rules. Projection accelerators never establish authority, and cache
operations do not repair them.

- Prepare captures accepted history in one read transaction and returns an opaque
  token after actor-eligible extraction.
- Publish takes an IMMEDIATE writer, freshly loads accepted history, checks the
  expected child head, re-prepares the exact request and compares the complete
  eligible sources and packet with the token. It then fences source rows and
  publishes atomically. Failure/cancellation rolls back deletions and insertion.
- Read and search each load one strict Engine in their read transaction and
  reconstruct/compare cached packets inside that same snapshot. Search validates
  the selected partition before inserting any of it into TEMP FTS.
- Invalidate loads strict accepted history and checks the actor/head inside its
  writer transaction, then deletes only the selected story/branch/observer cache.

Private source identity now contains **original Scope + sequence + serialized
accepted event**. SQL fencing uses that original scope, so ancestor events are
neither copied into nor relabelled as child events. Packet v1 still exposes event
sequence IDs: they resolve within its explicitly declared selected lineage,
where each retained sequence is unique. Cross-lineage/global sequence lookup is
not an authorized resolution mechanism.

A later parent or sibling continuation cannot enter a frozen child. Parent
advancement after preparation does not stale an unchanged child. Child advancement
does; selected ancestor-event/witness corruption fails strict replay before cache
read or publication. An excluded parent-future event is outside the child's
canonical prefix and is not accidentally required as a child source.

Actor eligibility still comes from the Engine visitor before target extraction,
serialization, search/count or FTS materialization. Unknown and hidden targets
retain existing indistinguishable categories. Cached statements and beliefs keep
their attribution classes and cannot become established truth.

## Prototype adapter integration finding

The existing `tests/derived_memory.rs` includes the module via `#[path]` and calls
its internal helpers against synthetic SQLite plus an Engine. Referencing Store
internals from that included module or changing all of its signatures would break
this independent prototype suite.

The coordinator approved preserving its original call signatures as explicitly
`cfg(test)` fixture-only transaction adapters. They share actual insert/read/FTS
implementation, but their supplied-Engine/raw-fence setup is **not** a production
Store authority path or its qualification. Normal builds contain no such adapter
call path. The new `tests/derived_lineage.rs` uses public actual Store operations
to verify the stronger coherent authority boundary. All eleven original prototype
cases remain, with only the now-obsolete child preparation refusal changed.

## Executed evidence

Windows; Rust/Cargo 1.93.1, locked/offline, DEV/TEST debug 0, incremental off.
Own target `D:/CodexLocalLore/01a165d9-ff25-7500-a550-1099087d4e37/m07-derived-lineage`,
own task TEMP/TMP. Synthetic data only. No model, device, CUA, app execution,
protected resources or shared/global build target used.

```text
cargo +1.93.1 test -p locallore-storage --all-features --locked --offline --target-dir <own-target>
93 passed; 0 failed; 0 ignored.
cargo +1.93.1 clippy -p locallore-storage --all-targets --all-features --locked --offline --target-dir <own-target> -- -D warnings
PASS
cargo +1.93.1 fmt --all -- --check
PASS
git diff --check
PASS
```

Earlier nine-case default/non-Host focused execution also passed. Final ten new
Store cases are included in the 93 count:

1. Exact root v1 golden packet bytes, inherited/local original scopes after
   reopen, unchanged invalid projection accelerator, and read-only-owner search.
2. Positive nested pre-birth rewind, parent/sibling/secret canaries, unknown versus
   hidden targets and range-boundary categories.
3. Parent advancement permits unchanged child publication; child advancement
   rejects old publication/read/search without changing retained cache bytes.
4. Tampered inherited accepted event or normalized witness rejects publication,
   read, search and invalidation before any cache change.
5. Tampered excluded parent-future event does not become a child dependency.
6. Poisoned foreign observer/sibling partitions exceeding local packet caps never
   consume the selected partition; a forged selected packet fails even for a
   search term that would otherwise return no hit.
7. Every observed publication cancellation checkpoint restores the previous
   partition. An actual SQL trigger abort after stale-row deletion rolls back;
   retry without the trigger succeeds.
8. Coordinated second owner commits after strict replay while a synthetic WAL
   read snapshot is held: the search returns the earlier coherent packet and its
   next call reports Stale. This is isolation evidence, not a latency claim.
9. Competing owners publish once/Unchanged or bounded Busy, retain one row, and
   cancelled searches recover on the same connection before scoped invalidation.
10. A held actual writer causes Busy without changing prior cache/canon;
    already-cancelled publication returns Cancelled before acquiring that writer.

Retained local logs: `derived-lineage-first-check.log` (initial test-adapter dead
code warnings), `derived-lineage-first-tests.log` (test lifetime/unused import),
`derived-lineage-focused-tests.log` (initial 8/9),
`derived-lineage-focused-final.log` (9/9), `derived-lineage-storage-tests.log`,
`derived-lineage-clippy.log` (test manual_contains lint),
`derived-lineage-clippy-final.log`, and `derived-lineage-storage-final.log`.
The initial concurrent-commit fixture used the default rollback journal and
correctly encountered Busy; the final test explicitly enables WAL on **its own
synthetic database**. No production journal-mode setting was changed.

SHA-256 of frozen actual source bytes:

| File | SHA-256 |
| --- | --- |
| storage/src/derived_memory.rs | `72c73ddcc7f66e5883f537838737cbde8a98f7b9f4823fc8b07287714507ed37` |
| storage/src/lib.rs | `13bf8a73a59c9351f4a7437b74abe85a947a6e68f1ba41edcc8827b30eeda2a3` |
| storage/tests/derived_lineage.rs | `197975482e3d0f042222fd475ec5ba4cbec4d14e8ad1ea3382117c55a3508e18` |

## Costs, limitations and next gates

This slice improves correctness, not retrieval speed. Every operation reconstructs
strict canonical history; reads re-extract packets. Search can re-extract up to
32 packets, each scanning the accepted lineage, then materialize up to 32 bounded
64-KiB packets in memory-only TEMP FTS. The existing configured/read-back
`temp_store=MEMORY` policy is unchanged. Its actual bundled-policy unit and the
prototype cancellation/TEMP cleanup tests ran in the storage suite.

Replay, one SQLite operation and some extraction work remain synchronous. Callback
checks do not promise immediate interruption, a hard latency or peak-memory bound.
IMMEDIATE publication/invalidation hold the writer during replay. No new cache-
specific process-death or SQLite-Full injection was run; existing Store crash/full
regressions passed separately within the suite. Independent review and central
workspace/eval/platform compatibility execution remain coordinator gates.

Packet v1 requires `through_revision == expected_revision`, caps selected events
at 256, and stales its partition on every new child head. It cannot yet represent
independently maintained old chunks or efficient exact-delta reuse. No durable
job ledger, scheduler, process-restart job continuation or automatic maintenance
was added. The old prototype test named maintenance resume demonstrates manual
reopen/idempotent cache operations, not a durable maintenance job system.

Future work needs a separately frozen coverage/policy contract distinguishing
authority head from covered completed range. Durable jobs require coordinator-
owned schema/migration/backup decisions; cache rows must not become a second job
ledger. A compiler consumer must preserve authoritative mandatory state and use
the exact eligible-event fallback on missing/stale/invalid/unsupported cache,
with explicit complete coverage and original-source deduplication. This change
does not wire summaries into generation or complete any native/Android gate.

## Coordinator integration cohort

Coordinator claim #11 comment 6369504352; branch
`impl/m07-lineage-transactions`. The author evidence above remains attributed to
its original source. At integrated source `9425add7f6406517eec8eb3c4291c386fdd8aea5`,
the coordinator ran 417 workspace tests (zero failures, four existing qualification
ignores), strict default/all-feature workspace Clippy, formatting and diff checks.
Android rebuilt both JNI ABIs, debug and instrumentation APKs, ran 128 JVM tests
(zero failures/errors/skips), lint and APK audit: PASS, 3m59s, all 78 tasks executed.
No emulator, device or ADB operation was used.

Accepted PR #95 was then reconciled at
`b21b119d9261bdde5e54720194ce850df8aba567`. Its changes are confined to evaluation
code/docs; shared Core/Store/workspace/JNI and Android source bytes are identical
to the preceding cohort. On this integrated source, frontend verification,
44 native module tests plus two native harness contracts (one existing ignored
qualification), strict native Clippy, 23 default/24 local-model-feature evaluation
tests and strict feature evaluation Clippy passed. These are native IPC/module
compatibility tests; no new UI render or model execution is claimed for this fix.
Commands, source attribution, review findings and local evidence hashes are in
the linked integration review. Full M07 and D08 gates remain open.
