# ADR-0007: One Rust owner for scoped SQLite storage

- Date: 2026-10-22
- Status: implemented for review; owner acceptance pending
- Scope: M04.01, [#8](https://github.com/OptimumAF/LocalLore/issues/8)
- Prerequisite: stacked on [#35](https://github.com/OptimumAF/LocalLore/pull/35)

The accepted engine/mobile foundations have stable v1 types. The next useful
step is a real database owner with executable migration and scope constraints.
Kotlin and inference must never maintain a second schema or mutate gameplay SQL.

Use `locallore-storage`, a small Rust crate with a private `rusqlite::Connection`.
Pin rusqlite 0.40.2 with bundled SQLite and backup support, default features off.
The bundled source gives host and Android builds the same SQLite version instead
of depending on a device's system library. Official API/source/license checks and
actual compiler/ABI evidence live in [storage sources](../storage/SOURCES_2026-10-22.md).
This adds neither a model dependency nor a database writer to Android's Kotlin UI.

Each owned connection enables and checks foreign keys, disables trusted schema,
uses FULL synchronous mode and a bounded busy timeout. Runtime extension loading
stays disabled; no raw connection or arbitrary SQL method is public. The bundled
SQLite source includes extension support, so it is not claimed compiled out.

Schema 1 stores validated seeds, branch/entity namespaces, and the constrained
slots needed for later turns/events/witnesses/projections. IDs and foreign keys
include story/branch and entity type where required. Display names never identify
records. JSON payloads do not replace validation by the engine. The schema cannot
by itself establish that a proposal is accepted or that a witness is entitled.

An application ID, user version, migration record and exact known schema shape
identify owned databases. Foreign, nonempty unversioned, future-version and
altered-schema databases fail closed. Initialization's DDL, migration record and
version markers share one IMMEDIATE transaction. An existing empty version-0
database requires an explicitly selected, non-overwriting consistent SQLite
backup before initialization. New paths need no preexisting-data backup. There
is no fabricated historical production schema: version 0 is empty, and version 1
is the first version. Future migrations must add historical fixtures and tests.

Use SQLite's online backup API, including committed WAL data, rather than copy a
live main file. Reserve destinations with create-new semantics, bound backup
retries, and flush the completed standalone file. Existing destinations remain
untouched. Callers retain the backup; no automatic destructive restore or downgrade
occurs. Backup copies contain plaintext story data and are not publicly exported
or uploaded by this crate. This is not a power-loss or hostile-filesystem guarantee.

This packet persists and reloads engine-validated root seeds. It does not expose
an accepted-event deserializer, commit a turn, use projections as canon, implement
branch forking/import, recover interrupted gameplay, or provide UI save/resume.
M04.02/.03 will add outcome replay and atomic accepted-turn persistence against
these constraints; M04.04/.06 own broader fault/recovery/snapshot tools. All store
calls are blocking and belong on an owning IO worker when wired to the app.

Using platform SQLite independently in Kotlin would split migration authority.
Persisting transcripts or cached projections alone would lose the accepted-history
boundary. An ORM, connection pool or speculative memory tables add no value to
this slice. The host and explicit Android smoke exercise the actual bundled C
library without an LLM. Build, emulator and physical-device evidence stay distinct.

## Schema2 derived-memory extension

The M07 implementation adds a STRICT derived-memory table through migration002.
Historical001 remains byte-for-byte unchanged. Before altering an exact owned
v1 database, the same owner holds an IMMEDIATE transaction, rechecks identity and
schema, creates and flushes a consistent new backup through a separate reader,
then applies002/version markers/exact verification and commits. New databases
execute both migrations atomically. The application-private open policy selects
a unique backup sibling; direct Store callers still explicitly provide a new
backup path. Read-only inspection can verify either historical1 or current2.
No automatic downgrade, destructive restore or foreign-schema adoption exists.

The canonical tables, accepted outcomes and receipt formats remain unchanged.
Derived caches use exact original accepted-source provenance and actor-only
eligibility, and stale/cancelled work cannot publish as current. Temporary FTS
contains only the verified actor/scope/revision partition. Typed extractive event
digests are not an LLM archivist or an alternate truth store. Durable job cursors,
model consumption and semantic-summary quality remain separate M07 work.

Workspace host-v1 compatibility and SQLite implementation version are distinct:
existing `schema_version:1` remains the workspace contract; the new explicit
`database_schema_version` reports2. Native database metadata/export labels use
the actual SQLite field, while canonical readable-export schema1 stays unchanged.
