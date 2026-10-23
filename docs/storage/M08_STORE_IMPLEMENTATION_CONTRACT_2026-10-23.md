# Mixed canonical history in the shared Store: implementation contract

Source-only coordinator freeze for #12 M08.03 and #30 D08.05. This specifies
pending implementation, not a migration, durable author capability or acceptance.
Core/consumer contracts in this directory remain authoritative: domain/history2,
projection2,schema5,archive3,query/compiler/context2,fresh Play2.5. Old domain1
and Play2.1–2.4 bytes retain their exact validation dispatch.

## One existing history owner

Keep `turns.response_json` as the existing committed history row, now containing
the exact Core `CanonicalRecord` encoding. LegacyPlay remains the original bare
Receipt JSON. PlayV2 stores its Core wrapper with private observation bindings;
AuthorV1 stores its private Core wrapper. Do not introduce a second author table
or merge two independently ordered histories. Engine.records alone determines
replay, canonical head, boundaries, source binding and encoded budgets.

Add bounded discriminators to existing turns/accepted_events through schema5:
`turns.canonical_kind` defaults to legacy_play and permits exactly legacy_play,
play_v2,author_v1; author_v1 requires committed status. Existing request/response
byte limits remain unchanged. `accepted_events.record_kind` defaults to play and
permits exactly play,author_correction. The migration contract is
locallore-storage-v5-mixed-history. Freeze executable DDL/test source before
implementation. Both public ordinary
AcceptedEvent and private author receipt retain their own format version1;
mixed canonical wrapper version2 is a separate discriminator. Never interpret an
author wrapper as an ordinary accepted actor event. Normalized author rows store
the exact serialized AuthorCorrectionReceiptV1 (wrapper.receipt), with
record_kind=author_correction,event_version=1,ZERO witnesses. The full wrapper2
is stored only in the canonical turn response. All normalization must equal the rebuilt Core receipt/event
before a selected history is admitted. These normalized rows remain redundant
verified indexes, never an alternate source of author input or character truth.

The existing branch_projections cache must admit version2 only for a Domain2
Engine and compare exact Core canonical_bytes; version1 retains old bytes. A
missing/mismatched cache remains nonauthoritative. Rebuild the cache table if
required by its old SQL CHECK; do not weaken canonical validation to retain it.

Schema5 uses the existing reserved consistent backup, single IMMEDIATE migration
transaction, exact sqlite_schema reference and migration-contract checks. Accept
only verified versions1–4 as predecessors, preserve their rows byte-for-byte,
and rollback on failure. Old schema3 archive-fixture bytes remain immutable.
No UI/Kotlin/TypeScript SQL writer or migration is introduced.

## Store-owned preparation and atomic application

Proposed native APIs, to be finalized against actual tests:

```text
prepare_author_correction(&mut self, &AuthorCorrectionInputV1, cancel)
    -> PreparedStoreAuthorCorrection
apply_author_correction(&mut self, &PreparedStoreAuthorCorrection, cancel)
    -> AuthorCorrectionOutcome
lookup_author_correction(&mut self, &AuthorCorrectionInputV1, cancel)
    -> Option<AuthorCorrectionOutcome>
```

PreparedStoreAuthorCorrection is opaque/non-Serde, bound to one Store incarnation,
the exact full input, actual full parent accepted basis and Core's opaque plan.
Read all preparation source and catalog/retention/derived-count enrichment in
one real read transaction. Core preview cannot invent Store counts. A foreign
Store, clone or reopened owner cannot reuse a preparation, even with equal
database bytes or colliding story/branch IDs.

Host/native explicit author grant and second consent are separate prerequisites;
the Store port is not a renderer grant. Never deserialize a prepared capability,
trust a supplied Engine, accept an inspector grant as author consent, log a
private plan, or reconstruct authority from displayed preview JSON.

The unchanged request_json limit is24,576 encoded bytes. Valid control-byte
author replacement/reason strings can exceed that limit together after JSON
escaping. Store a small closed author index in request_json, not a duplicate full
input: version1,kind author_correction,actual child scope,fixed author turn key,
expected_revision=f and SHA-256 of the full canonical response record. Regenerate
and compare this index against validated Core serialization and SQL scope/key/
revision; it has no independent authority. Full author input remains only in the
canonical response. Never silently narrow Core's accepted text budget or widen
the ordinary request limit. All INSERTs use explicit column lists after adding
discriminators, including ordinary admission/commit and archive import.

Keep the actual typed preview and exact bytes inside the opaque preparation.
Any impact counts displayed for second consent must be recomputed and compared
in the application transaction or return Stale. Omit irrelevant unaffected
catalog/job counts instead of fabricating them or adding unnecessary invalidation.

Application opens one IMMEDIATE transaction and rechecks actual parent complete
basis/head, fixed child identity, tombstone admission, completed fork boundary,
branch/depth/count budgets and exact Core plan. Insert the new child, inherited
entity metadata, private author committed row/normalization and projection2 in
that same transaction. Reuse narrowly extracted existing fork insertion logic;
calling the public transaction-opening fork method and committing afterward
would be an invalid two-transaction implementation. Check latched cancellation
before commit; panic in a cancellation callback is cancellation. Late cancellation
after commit cannot relabel the saved outcome as rollback.

The author record is exactly at f+1, advances no story time and grants no actor
witness/knowledge. Original/siblings remain unchanged. Preserve actual known A
when world proposition changes to B; later eligible Discover observes actual B
only for the discovering player. No automatic downstream replay or mutation of
the original Seed. New child starts without a copied derived proof/job cache.

Exact recovery compares full author input and validated original author record,
including reason, operation, parent, guarded head, fork and fixed child ID. It
is read-only, returns the child's current validated head, never creates/replays
or rewrites later progress, and distinguishes an ordinary fork using the same
ID. Conflicting input is RetryMismatch. Existing matching outcomes can be looked
up after parent progress changes; fresh application must still satisfy the full
guard. Lookup validates the active child and actual retained source; it must not
require a live original parent at H when excluded parent future history was
legitimately collected. Parent/child tombstones cannot be resurrected. Ordinary
fork retry must also refuse an authored child with matching parent/fork, so
operation-kind collisions are symmetric. Ordinary turn admission/status must detect an author-key occupant before
attempting Request decoding and fail closed without mutating it.

## Every canonical consumer must use the mixed ledger

Read history/requests, verify normalization, count/byte budgets, prepare/commit,
full accepted-source fingerprints, branch catalogs/boundaries, ancestor prefix
rebuild, nested prebirth forks, retention/collection, story deletion and archive
validation/import/export must dispatch on actual CanonicalRecord. Never derive
their authority from the filtered receipts() compatibility view. Ordinary public
turn status may still return an unchanged ordinary Receipt under its old scope.

Old derived proof/job formats reject Domain2 before source hashing, cache read,
admission or publication; a coherent generation snapshot returns actual Engine
plus honest RawFallbackUnsupported. No Domain1 proof can certify filtered mixed
history. New model/compiler/query consumers remain a separate frozen contract.

Archive1/2 remain strict Domain1 formats. Archive3 is required for a story with
any retained mixed record and preserves original scopes, parent lineage, author
input/reasons and observation bindings under explicit full-private export.
Domain1-only export keeps its existing archive version/shape. Archive3 integrity
counts/hashes cover full canonical records and canonical projection2, not only
ordinary receipts; reference validation version-dispatches Play2.5. Import builds
all rows atomically through the same owner and replays exact records before
success. Source workflow drafts/jobs/private traces/models are still excluded.
Native adapters/closed frontend and Android decoders require explicit archive3
support before that format is advertised as available there.

Archive2's known source-schema range must explicitly include schema5 for an
otherwise unchanged Domain1 archive: the existing3..=4 bound would make a new
schema5 export reject itself. This extends known metadata compatibility only;
archive1/2 still reject mixed canonical records and retain all old shape/hash/
replay/privacy checks. Historical archive fixture bytes remain immutable.

## Frozen acceptance families before implementation

Use real synthetic Store/Core transactions, not a second evaluator:

1. Versions1–4 migration backup/exact schema/rollback, old bytes and old archives.
2. Exact child+author+normalization+projection2 atomicity/reopen and ordinary
   progress on that child; original and siblings byte-equivalent.
3. Stale/same-head replaced parent, scope/owner/clone/reopen capability refusal.
4. Exact-input lost-ack lookup/retry after later progress; mismatched reason,
   expected guard or child-kind collision refuses without writes.
5. Cancellation, callback panic and actual SQLite-full/injected failure boundaries
   leave no partial child/history/cache; late cancel preserves committed outcome.
6. Known A/world B/reobserve B, repeated discoveries and A→B→A retain actual
   source refs after reopen; no NPC knowledge/actor-input leakage.
7. Mixed normalization tampering/unknown wrappers/duplicate JSON fields/private
   binding changes fail closed; caps count private author records and wrappers.
8. Nested authored and ordinary forks, prebirth rewind, selected source heads and
   inherited original scopes never invent parent future history.
9. Retired/collected ancestors retain exactly required author prefixes; tombstones
   prevent ID resurrection and deletion removes the intended story atomically.
10. Domain2 old proof/jobs refuse before work, both generation policy fallbacks
    remain honest, and Domain1 memory checks remain unchanged.
11. Archive3 exact private mixed round trip/continuation, strict archive1/2 and
    version/collision/corruption/transaction rollback cases.

Independent source findings and the selected compact-index/normalization design
are preserved in M08_STORE_CONTRACT_INDEPENDENT_REVIEW_2026-10-23.md at review
d6038a4. Additional frozen cases must cover maximum valid escaped author inputs,
exact preview metadata staleness, symmetric child-kind conflicts, schema5
Domain1 archive2 self-roundtrip and source retirement after exact creation.

All these new Store/schema/author/archive checks are unimplemented/unrun at this
freeze. Root owns implementation and exact runnable test-source allocation;
independent review and platform qualification remain required before exposure.
