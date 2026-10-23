# Shared derived memory jobs and coherent context snapshots

Refs #11 M07.03/.04 partial; #29 D07 prerequisite. Implementation and
qualification are in progress, not full milestone acceptance.
Coordinator claim #11 comment6372984169. Root owns schema/migrations,
Store protocol and integration; test/review contributors have isolated branches.

## Native API

`locallore_storage::memory_jobs` exposes `MemoryJobRequest { scope, observer,
expected_head }`, opaque cloneable `MemoryJobHandle` (`id()` only),
`MemoryJobInfo`, closed status/failure enums, opaque one-use
`PreparedMemoryJobStep`, and `ContextSnapshot { engine, coverage }`.

The Store methods are `ensure_memory_job`, `memory_job_status`,
`prepare_memory_job_step`, `publish_memory_job_step`, `cancel_memory_job`,
`prune_memory_job`, and `context_snapshot`. They reuse the existing fixed
`derived_memory::MemoryError` categories and panic-safe cancellation callback.
No SQL connection, caller-constructed packet/Engine, Deserialize capability,
provider, arbitrary execution hook or second canonical history is exposed.

Handles and prepared capabilities belong to one actual Store instance through
private pointer identity. They expire when that owner closes. After reopen or
process restart, call `ensure_memory_job` to reissue a native handle for the same
persisted ID, generation, status and completed cursor. Passing another owner's
handle returns `NotFound` before opening a transaction. This also applies to two
connections to the same database or identical/cloned databases. Equality includes
owner identity. Persisted job IDs use SQLite AUTOINCREMENT and are never recycled
by pruning/deleting stories.

## Schema and work protocol

Schema4 adds only `memory_jobs` and `memory_job_packets`; accepted events,
witnesses, receipts, seeds, projections and turn rules are unchanged. The sole
Store owner verifies exact schema and migration records. Known1/2/3 upgrades
require a newly reserved safety backup and one rollback-capable transaction.
Historical read-only schemas remain supported. Archive1/2 formats retain their
existing semantics; archive2 explicitly accepts source schemas3/4, future source
versions remain rejected. Playable exports omit all jobs/cache. Database
inspection copies remain explicitly private and contain all data.

Each job is bound to exact scope/actor, method
`deterministic-event-extractive-v2`, packet version2, expected canonical head,
seed, immutable SQL ancestry and a streaming fingerprint of the actual selected
accepted history. Fingerprinting is bounded to64MiB; this limit is not a claim
of a model context size. SQL ancestry hashing and Core packet lineage hashing
have different encodings; packet authority always comes from actual Core
verification, never equality of those differently encoded digests.

There is at most one retained job per scope/actor/method (a stricter limit than
the declared eight-per-partition ceiling), at most256 jobs per Store, and at
most32 packets of at most64KiB per job. Admission never silently removes history
or another job. Explicit terminal pruning releases a job slot. The cache has a
separate namespace from accepted v1 derived memory, so v1 invalidation does not
erase/relabel v2 jobs.

`ensure` is idempotent at the same basis. Advancing the head retargets the same
job and increases its generation, preserving only a contiguous sealed prefix
that re-verifies against the actual new Engine. The old open tail is dropped
before whole-set verification. Corrupt/missing packet prefixes are conservatively
reverified/reset with a generation change; they never become canonical history.
A cancelled job stays cancelled across ensure/reopen. Prune and explicitly ensure
again to create a new higher job ID. Ready work cannot be pruned.

Preparation reads the strict Engine, source basis, current generation/cursor and
verified prefix in one SQLite read transaction, then releases that transaction
before Core chunk construction. Publication uses a fresh IMMEDIATE transaction,
strict replay, identical basis and job generation, exact existing prefix, and a
fresh Core rebuild of the proposed chunk. Only identical bytes/boundary publish.
Packet insertion and cursor/status/generation update commit together, after the
last cancellation check. Competing, cancelled or retargeted prepared values
cannot advance a cursor. Busy, Full, cancellation or SQL failure rolls back the
entire attempted publication. A committed chunk remains committed if a later
cancellation arrives. There is no persisted Running state, wall-clock lease,
automatic recovery worker or claim that a process is still alive.

An indivisible oversized Core turn or the packet ceiling can produce an explicit
Blocked terminal result with a closed reason, without advancing its cursor.
The preparation token does not itself mutate status; its fresh verified
publication records that result. No background scheduler is added here.

## Context and privacy

`context_snapshot` performs a read-only transaction that supplies both the actual
strict Engine and its coverage proof from that same SQLite snapshot. Another
owner's later commit cannot mix newer cache with older Engine. Missing, malformed,
foreign or unprovable cache falls back conservatively through the accepted Core
verifier; malformed canonical history still fails strict replay. No cache repair
or job admission occurs during a read. Context proof alone grants no actor,
inspector or author privilege.

Packets retain original source scopes/sequences, actor filtering and complete
turn boundaries. Forking copies no job/cache. Retirement and story deletion
remove affected packets before their jobs, including retained retired ancestry,
and old capabilities cannot revive deleted targets. Ordinary inherited canonical
history and live descendants remain authoritative. No memory packet changes
what a character knows.

The pure verified compiler input is already on accepted main via PR #110.
Production Host/Play forwarding, maintenance scheduling/cancellation ownership,
explicit new prompt/provenance version, UI state and actual model comparison
remain separately required integration work. This Store API alone does not
qualify those capabilities, performance, tokenizer savings or Android devices.

## Qualification record (pending final cohort)

Initial production `e98ff6a` compiled with locked/offline Cargo. Independent
unchanged tests reproduced five cross-Store handle failures; `502cacd` bound
capabilities to actual owners. A sixth regression reproduced schema3 retired
catalog failure; `3680437` gates new-table queries by the actual historical
schema. The independent unchanged six tests then passed at the fixed source.
The reviewer evidence records exact hashes/results separately.

The first broader integration compile stopped at eight test-helper u64 SQLite
conversion errors; zero tests ran. Integer-only checked conversions corrected
those helpers without changing the frozen oracles. The initial pressure fixture
stopped before Full because strict canonical writes left four reusable pages.
An explicit owned-fixture VACUUM, with identical canonical/receipt assertions,
establishes zero free pages before the same fixed page clamp; actual SQLite Full
and reopened same-boundary retry then passed. These failed attempts remain
distinct from the final cohort. No test failure is hidden by a gate change.

Final complete results, source revisions, commands, environment and limitations
will be recorded before this change is proposed for merge. Capacity17/32 schema3
profiles are not qualified by these unit tests and require separate schema4
measurement/requalification; their historical reports are not re-labelled.

The schema4 preflight passed seven independent review regressions, seven retained
branch tests and eight story-deletion tests. Two migration fixture assumptions
failed: a filename filter still required `before-v3` while the actual owner
correctly created `before-v4`; the newly added v3 backup test demanded identical
whole-file bytes. A diagnostic rerun retained the original failing assertion and
measured equal126,976-byte files differing only at offsets27,43,95. These are
SQLite header change-counter, schema-cookie and version-valid-for fields, per
the [official file format](https://www.sqlite.org/fileformat.html#the_database_header).
The pinned bundled SQLite backup implementation explicitly updates its destination
schema cookie (`sqlite3.c`, backup step near85131–85142). The test now requires
every byte outside those three four-byte header fields to match, exact canonical
and cache SQL rows, literal receipts, historical schema identity and replay.
No production backup code, historical payload or original migration oracle was
altered. `semantic-migration-preflight.log`, `schema3-backup-diagnostic.log` and
`schema3-backup-offsets.log` retain the failed attempts. A mistakenly shortened
exact-name diagnostic matched zero tests and is not counted as verification.
