# M07 derived-memory independent source review

Refs #11 M07.02/.03/.04, partial. Reviewer `/root/app_storage_review` did not
author this prototype. Claim
[6359684489](https://github.com/OptimumAF/LocalLore/issues/11#issuecomment-6359684489)
preceded this report. Isolated `review/m07-derived-independent`,
`source-memory-review`, starts at frozen coordinator
`f5ac344c004f8a27978192a15ce884b6a9536189`. Sole changed path is this document.
No implementation edits, tests/builds, app/model/worker/device/CUA operations,
process control, publication or merge were performed by the reviewer. The separate
evaluation checkout at94848db was preserved.

Scope is the derived-memory module and its11 test definitions, with Store wrappers,
schema, actual Engine actor visitor and public owner tests read as dependencies.
This supplements the separate coordinator-integration review whose author wrote
the prototype; it does not repeat its author-independent migration review or
constitute owner acceptance of M07.

## Concrete P2 finding: TEMP FTS lacks an explicit memory policy

At f5ac344, `derived_memory::search` line525 creates a TEMP FTS5 table and inserts
verified packet plaintext. `Store::configure` sets foreign keys, trusted_schema,
synchronous and busy timeout but never sets or verifies `temp_store`. The pinned
ordinary bundled Windows SQLite build defaults to `SQLITE_TEMP_STORE=1`; its
libsqlite3-sys0.38.2 build.rs adds TEMP_STORE=3 specifically for Android and2 only
for its separate SQLCipher feature. LocalLore selects ordinary bundled SQLite.

[SQLite TEMP database documentation](https://www.sqlite.org/tempfiles.html#temp_databases)
states that TEMP storage can use a separate file and that its lifetime can extend
until connection close. Its
[temporary-storage explanation](https://www.sqlite.org/tempfiles.html#the_sqlite_temp_store_compile_time_parameter_and_pragma)
describes cache spill and the Windows VFS GetTempPath location. The
[temp_store pragma](https://www.sqlite.org/pragma.html#pragma_temp_store) provides
a memory policy subject to the compile-time setting. Therefore successful logical
DROP/rollback tests do not prove story text stayed inside the app-private database
location. Up to32 packets of64KiB plus FTS structure can reach a file-backed TEMP
cache. This is a source/configuration finding and documented permitted behavior,
**not an observed spill, demonstrated exfiltration or forensic-erasure claim**.
OS paging and ordinary canonical DB journals are separate existing boundaries.

Reported to coordinator before publication; coordinator accepted the finding and
owns the correction: set `PRAGMA temp_store=MEMORY` and verify its readback for
every Store connection before TEMP DDL, retaining actual bundled tests and scoped
FTS cleanup checks. The reviewer has no implementation writer ownership.
**Correction source rechecked:** coordinator commit
`591fb600100585360fa20a8d2793223dedf47698` changes only storage/lib.rs. Every
configured owner/read-only/reference connection now requests MEMORY before TEMP
DDL and reads back `temp_store` as2, failing Integrity otherwise. The pinned
ordinary bundled Windows compile-time policy allows that override; Android's
always-memory build also retains it. This resolves the reported source gap for
the supported pinned build. It does not control OS paging, promise forensic erasure
or qualify arbitrary third-party SQLite builds with incompatible compile options.

The new file-backed-owner test creates actual bundled TEMP FTS, inserts2.4MB of
synthetic text, searches it, checks TEMP metadata/cleanup and reopens read-only
with the same required policy. A blank TEMP filename is corroborating metadata,
not by itself proof that arbitrary file-backed TEMP implementations never create
a VFS file. The substantive controls are the verified policy plus the pinned
SQLite configuration. Coordinator reports **250 workspace tests passed**, including
this new case,11 module tests,4 owner cases and migration rollback, with strict
all-target Clippy. This reviewer inspected the exact test/code diff; no rerun is
claimed. Previously recorded236 fresh native compatibility assertions predate
this policy fix; final native/Android rebuilds were ongoing at this handoff and
are separate coordinator evidence.

## Authority and privacy observations

- Preparation calls the accepted Engine's borrowed `visit_actor_observations`.
  Exact scope/current head/actor/range and lineage+witness eligibility occur
  before its callback. Only then does typed target filtering run, serialize a
  source, consume selected-event/byte capacity or build an entry. There is no
  duplicate witness predicate or omniscient projection passed to a summarizer.
  Hidden/absent entity targets with no qualifying observed event both return
  NotFound; hidden/absent start boundaries both fail InvalidInput. Seed-only
  facts/commitments are outside these accepted-event packets.
- PreparedMemory's fields are private, with no Deserialize/constructor exposed
  for caller-supplied history. Public Store preparation replays its own validated
  source. The native actor selector remains trusted: choosing another actor is
  not authorization obtained from the packet. At this freeze the memory methods
  have no app/Host IPC caller; production consumption is a future boundary to
  authorize explicitly.
- Extractive entries retain typed Said claims as statements, Believed entries as
  beliefs, and other witnessed accepted effects as canonical observations. Only
  consecutive observed TimeAdvanced endpoints merge; all source IDs remain.
  Original messages/thoughts, narration, hidden seed facts and prior summaries
  are not source text. Entity summaries match the documented finite direct-effect
  cases, not a comprehensive current profile or arbitrary graph expansion.
- Search's main SELECT binds story, branch, observer and exact revision before
  packet fetch/parse. At most33 rows are requested to detect the32-row cap.
  Each current-partition packet is rederived and fully compared before any FTS
  corpus materialization. A corrupt other-observer packet is not parsed. A corrupt
  requested-partition packet fails the entire search, rather than entering FTS or
  being silently accepted as a cache hit.
- User query text never becomes SQL or FTS grammar. Bounded alphanumeric/underscore
  terms are individually quoted, AND-combined and bound as a SQL value. Empty
  punctuation yields no hits. Corpus order is stable packet order; the result
  exposes verified packets, not global BM25, snippets, external row IDs, exclusion
  counts or a second corpus. Structural JSON keys can match: this is literal
  lexical packet search, not measured semantic relevance.

## Freshness, integrity and failure observations

Publish takes an IMMEDIATE transaction before checking the root branch/head and
every selected exact accepted envelope. Only the derived table is written. A
same-basis identical packet returns Unchanged. Fresh publication deletes older
rows only in that actor/scope partition; cap failure, cancellation or SQL failure
rolls the transaction back, including any deletion. Read/search create a coherent
deferred main snapshot; their Engine may predate that transaction, but head/source
fences reject a newer captured database head. A writer committing after the read
snapshot does not relabel the returned old-basis packet as current.

Read reconstruction compares complete canonical serialized bytes, not just a
self-reported checksum or source list. Search also verifies the cache key against
its parsed typed target/range before this comparison. Changes to packet content,
extra/duplicate keys, attribution, target or source list cannot become accepted
memory merely by recomputing a hash. Exact source comparison is against the Store's
accepted history; it is not authentication of an arbitrary malicious database or
OS. A cache never changes a receipt, projection, knowledge record or generation
authority. No generation consumer of these Store methods exists at this freeze.

Private cancellation callbacks are caught as cancellation if they panic. The
visitor checks excluded histories periodically and each eligible event before
callbacks; a failed preparation discards accumulation and returns no token.
Publication and invalidation check cancellation immediately before commit. TEMP
search cleanup executes after the search body on success/error/cancel; failed
transactions are dropped and rolled back. A cleanup error on an otherwise
successful search is returned instead of reporting successful hits. Busy/Full
and other database failures remain fixed categories without SQL/path/story text.

Limits are256 selected events,1MiB selected source envelopes,64KiB packet,
32 packets per partition,256 query bytes,16 terms and16 hits. These are finite
payload limits, not bounded total replay latency or maximum-scale memory evidence.
Store::resume has no cancellation callback; the nonzero-boundary receipt lookup,
individual SQLite calls and serialization also have no mid-call cancellation.
Read/search rebuild capped packets against original history and can rescan history
for each packet. No constant-time isolation or prompt whole-operation cancellation
is established. Both module and integration documents retain this limitation.

## Test source and evidence attribution

Read all11 prototype test definitions. They cover the actual bundled FTS feature,
statement/belief distinction, compression with source retention, corrupt foreign
observer exclusion, typed entity/unknown-hidden facts, source/packet tamper,
stale basis, reopen/idempotency/invalidation, callback cancellation/panic and TEMP
cleanup, query syntax/bounds, equal-observation paired1025-event hidden histories,
root-only/range/cap behavior, and an actual SQLite AFTER INSERT abort preserving
prior cache/canonical rows. They construct real accepted Engine events; helper
SQL populates test-owned canonical fixture tables rather than granting a new
production history-import interface.

Public Store tests additionally exercise actual owner wrappers and backed-up
v1 migration. These are stronger integration evidence than the module's borrowed
test connection, but they do not imply native cached-memory model consumption.
The coordinator's M07_STORE_INTEGRATION.md records249 integrated Rust passes,
strict checks and separate Android/native compatibility results; the original
M07_DERIVED report records11 passes. These are attributed execution reports read
by this reviewer, **not reviewer reruns**. No counts or native images are used as
proof of this new TEMP storage-policy correction.

Useful future focused cases include cancellation after FTS rows have been inserted,
before returning the last hit; a reader/writer same-head timing fixture around
snapshot capture; and migration-era stale-row replacement failure after deletion.
They are suggestions for stronger finite coverage, not newly demonstrated defects
or a reason to manufacture another retrieval implementation.

## Frozen source inventory

SHA256 values below are exact local checkout file bytes at f5ac344. Git line-ending
conversion can change raw byte hashes without changing behavior. They are source
identifiers, not authenticity assertions or execution measurements.

| Path | SHA256 |
|---|---|
| crates/locallore-storage/src/derived_memory.rs | `fe74ef51b9502162c00177a9dc4aba727a4733881332d8a66ff1c755cd428924` |
| crates/locallore-storage/tests/derived_memory.rs | `c87e7cd045de59a0f0451793ef942f3335ea000c8e723b7197fb8aca320bd661` |
| crates/locallore-storage/src/lib.rs | `17a3b3d6402244de97ed1ad6eff8854a116454752e80e47a5ef6e08988dfc5f9` |
| crates/locallore-storage/migrations/002_derived_memory.sql | `bfecd8c0a765993d463b53d6099c4d80453eef85e8c227ceb00e5ae011843f91` |
| crates/locallore-storage/tests/derived_store.rs | `39e8297e17d18c811df25783d38454fa5fdb921982f91df685a324d77a93acdc` |
| crates/locallore/src/engine.rs | `4c9a51ca780f50b4cd32c30dcd7c40ce1885301e8694a334bc6bd300c108a0ef` |
| crates/locallore-storage/Cargo.toml | `7b51e87c76561ce06cf8fd7353804d0e25d9c6349e68fc09218ac6f95c73665d` |
| Cargo.lock | `30a35c6f12bbe1c8f49a2c257b721f82f72a6523a5370c72dbf83c54bea303eb` |

The correction's local source-memory storage/lib.rs SHA256 is
`28b641e5716b5ab3d60d219e205393e801a0b0db9d2bf4cdd47ce6dedabcc7da`.
The prototype module/tests and other inventory entries are unchanged by591fb60.

## Disposition and remaining gates

One concrete publication finding was reported and its exact591fb60 correction
was source-rechecked: TEMP storage policy. No remaining blocking prototype defect
was found in this source pass. This is not a favorable score, proof of all inputs, full M07
acceptance or human quality review. Independent Store/migration review remains a
separate packet. LLM archivist/semantic compression, persistent resumable jobs,
corrections/branches/deltas, model consumption/usefulness,1000+ eligible-event
quality and whole-operation responsiveness remain open. Next: coordinator reconcile
final compatibility/source/check evidence, then separately authorize any generation
consumer and retain exact-source verification before its prompt boundary.
