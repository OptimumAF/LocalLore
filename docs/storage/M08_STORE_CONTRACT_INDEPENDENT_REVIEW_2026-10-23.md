# Independent shared Store contract review

2026-10-23. Refs #12 M08.03 / #30 D08.05. **Source and contract review only.**
No schema 5 DDL, Store author implementation or new executable tests existed in
the reviewed source. Recommendations and proposed oracles below are unrun.

## Source and ownership

Reviewed coordinator `672da96a9d8352da226791c6400b6714600bfad7`, including
`M08_STORE_IMPLEMENTATION_CONTRACT_2026-10-23.md`, the frozen Core contract,
actual Store migrations, identity/backup/open logic, turns, branches, retention,
archive validation/export/import and derived/job source entry points. AGENTS,
README and issue workflow were already read; recent #12/#30 ownership and
coordinator claim `6377042550` were checked. Prior Core source review is separate.

Coordinator explicitly allocated this ONE NEW document before writing. Claims
#12 `6377075060` / #30 `6377075329`: agent `/root/author_core_review`, separate
`review/m08-store-contract` / `source-m08-store-contract-review` from `672da96`.
All existing source, tests, migrations and contracts remain unchanged. Root owns
final typed interfaces, DDL, frozen executable tests and implementation.

## Concrete contract seams to resolve before implementation

### 1. Author input cannot always fit the existing ordinary request column

`migrations/001_initial.sql` limits `turns.request_json` to **24,576 encoded
bytes**. Valid Core input permits 2,048-byte replacement and reason strings.
Using control characters that JSON encodes as six-byte escapes consumes exactly
24,576 bytes for those two string contents alone, before quotes, field names,
IDs, prior value or other metadata. Such input can fit the 65,536-byte Core
record/preview ceilings, yet a full input copy in the existing request column
would violate SQL's CHECK. This is a concrete capacity seam, not an executed SQL
failure or a reason to widen every ordinary request's allowance.

Root selected a small closed redundant author index in `request_json`:

```text
{version:1, kind:"author_correction", scope:<actual child>,
 turn:"author-correction-v1", expected_revision:f,
 record_sha256:<full rebuilt Core canonical-record encoding hash>}
```

The complete author input lives ONLY inside the authoritative Core wrapper in
`response_json`. The index is not a proposal, author grant or second journal.
Read it with strict bounded duplicate/unknown-field checks, regenerate it from
the validated Core record and compare every field/hash against both SQL metadata
and actual record. In particular, index `expected_revision` is **f**, whereas
the embedded input's guarded parent creation head is **H**, potentially H > f.
Do not confuse them in ordering, ancestor caps, retention or replay.

The hash must use the explicitly frozen complete Core canonical serialization,
including private input/reason/bindings, not filtered receipts or arbitrary raw
JSON formatting. A matching index hash cannot replace Core replay validation.

Proposed oracle: prepare/apply/reopen valid escaped input, assert ordinary SQL
24,576-byte CHECK unchanged, full exact input recovered from the single response
record, and tampered index scope/f/reason-dependent hash fails without writes.

### 2. Domain 1 archive 2 must explicitly admit known schema 5 provenance

`playable_archive.rs::validate_archive` currently accepts archive 2 only with
source schema **3..=4**. Export records the actual source database schema and
chooses archive 2 for a Domain 1 story with retired IDs. Merely raising Store's
schema constant to 5 would therefore make that new, otherwise unchanged Domain
1 export fail its own import validator.

Freeze archive 2's known-schema range through 5 while preserving its exact
Domain 1 payload shape, retirement rules, canonicalization, hashes and strict
version dispatch. Archive 1 continues rejecting even explicit-null retirement
fields; archive 2 still requires its nonempty retired list. Do not claim the
old program can read new schema provenance, rewrite historical fixture bytes,
lie about source schema, or label a mixed story archive 1/2.

Proposed oracles: immutable historical archive 1/2 byte fixtures still validate;
new schema 5 Domain 1 archive 1 and archive 2 self-validate/round-trip; unknown
schema remains Unsupported; mixed record in old archive format fails even when
all external hashes are recomputed. Archive 3 is a separately frozen mixed
record format, not permissive reinterpretation of old local_receipts.

### 3. Cross-kind child identity must be checked in both directions

`branches.rs::fork_branch` currently treats any existing child with matching
parent/fork as an ordinary fork retry. Once author creation exists, that test
alone would also accept an authored child as the ordinary operation's outcome.
The proposed author lookup already rejects an ordinary fork using its fixed ID;
Root selected the symmetric refusal too.

Determine operation kind from validated actual local canonical history, not
presence of the fixed turn key alone: ordinary legacy/play turns may legitimately
use `author-correction-v1`, and inherited ancestor keys do not occupy a child's
namespace. Ordinary fork recovery finding a local AuthorV1 creation record must
return RetryMismatch without selecting, creating, replaying or mutating a child.
Author recovery finding only an ordinary fork must likewise refuse.

Proposed oracles: both collision directions with identical parent/fork; ordinary
same-named key remains valid; inherited author keys do not reserve another scope;
known matching operation returns current validated head after later progress.

### 4. Exact recovery must not demand a still-live creation parent head

The existing ordinary fork method admits parent and child before recovery. That
ordering must not be copied mechanically to the new author lookup. A successful
child can remain active after its parent advances, is retired, or loses excluded
future H through retention. Matching the complete original embedded input and
validated retained child source is sufficient for read-only recovery; reloading
live parent H first could incorrectly make the known saved outcome unrecoverable.

Validate actual active child admission/tombstones, its real parent/fork lineage,
retained canonical history, local author record and exact full input. Return
current child head, preserving subsequent progress. A missing child returns None;
a retired/collected child is unavailable and is never recreated. Fresh creation
still requires a live parent and exact complete guarded source/head under the
IMMEDIATE transaction. Recovery never invents an excluded historical parent
future or weakens a new creation guard.

Proposed oracle: create at H > f, advance child and parent, recover exact input;
retire a nonroot parent and collect excluded future, recover active child again;
change reason/H/f/operation and refuse; retire/collect the child and never
resurrect its tombstoned fixed ID.

## Typed Store, schema and transaction recommendations

Use a distinct Store opaque token such as `PreparedStoreAuthorCorrection`,
containing an Arc-backed per-Store incarnation identity, exact input, Core plan,
complete parent basis and bounded enriched preview. It is non-Serde, with private
fields; it is not interchangeable with Core's pure plan. A foreign open/reopen
or cloned database cannot reuse it even if persisted IDs and bytes match. Store
currently is not Clone; do not introduce connection/capability cloning to solve
this port. Reuse existing native owner-identity techniques with explicit types.

Native APIs can retain prepare/apply/lookup names, but final tests must freeze
the difference between fresh guarded apply and read-only exact-input recovery.
The outcome needs actual child scope, parent/fork, original author receipt and
current validated child head; any Engine it contains is native-only. Avoid a
wire serialization of the complete Engine or private canonical wrapper.

Root selected additive schema 5 discriminators:

- `turns.canonical_kind`: `legacy_play`, `play_v2`, `author_v1`, default
  `legacy_play` for unchanged existing rows; author kind requires committed status.
- `accepted_events.record_kind`: `play` or `author_v1`, default `play`.
  Ordinary normalization remains the original AcceptedEvent; author normalization
  is the **full Core author wrapper**, exactly compared to replay, with no
  event_witnesses rows. `event_version=1` remains the contained record's own
  version, separate from canonical wrapper `record_version=2`.
- Rebuild only the replaceable projection table as needed to admit version 1/2;
  compare its version and bytes against actual Engine domain/canonical bytes.
  A version 2 cache beside Domain 1, or converse, is a mismatched cache.

Freeze exact DDL CHECK expressions and migration contract before code. Preserve
ordinary draft/terminal request semantics: a draft has no accepted PlayV2 record;
choose/document discriminator treatment before writing tests. At commit derive
the committed kind from the actual last Core record, never a caller flag.

All insert paths must use explicit column lists after additive schema changes.
Current ordinary begin/commit and archive import contain positional
`INSERT INTO turns VALUES` / `INSERT INTO accepted_events VALUES`; changing only
the new author path would break existing operations. Verify migrations with
foreign_keys enabled, exact schema references/contracts, reserved backup, copied
old payload text unchanged, foreign_key_check and rollback on injected failure.

Preparation should read full actual parent and any consent metadata coherently.
Apply uses one IMMEDIATE transaction: verify owner, full source/input/plan,
child/tombstone admission and budgets; insert branch/entity metadata, exactly one
author response/index/normalized wrapper and projection, then commit. Extract a
narrow transaction-local fork insertion helper; never call the public
transaction-opening fork API and append author state in a second transaction.

If the preview displays descendant/job/catalog counts, recompute and compare the
same bounded enriched preview during apply. Checking only parent basis and
still-under-budget catalog state does not establish equality of displayed
consent metadata. Omit unnecessary unaffected counts instead of introducing
unneeded stale dependencies. Native second consent binds the exact displayed
preview and owner/epoch; Store admission remains separate and cannot infer that
consent from an inspector grant or JSON flag.

Use latched panic-safe cancellation and check before the actual commit. Once
commit succeeds, a late cancellation cannot replace success with a rollback
claim. A lost acknowledgement is recovered by full-input lookup, not another
creation identity. Tests need real SQLite failure/full rollback boundaries;
fake cancellation callbacks alone do not prove disk/transaction behavior.

## Canonical consumer closure inventory

Migrate `turns::read_history`, local-record matching and `verify_ledger` to actual
record dispatch before ordinary Request decoding; reject author occupants in all
ordinary begin/status/lookup/finish/commit APIs without mutating them. Keep
original scope and prefix accounting at f/f+1, including wrapper bytes and the
separate existing request-plus-response Store budget.

Migrate retention graph fingerprints away from filtered receipts, preserve real
birth floors and completed boundaries, and prune author response/normalization
consistently. A prebirth child may legitimately require only its parent's fork
boundary, excluding that parent's later author record; no recovery can resurrect
that retired operation. Deletion must still validate every retained branch and
tombstone. Do not flatten scoped records under a new child.

Archive 3 import/export must operate on complete records and actual Core
projection2, private reasons and observation bindings under full-private consent.
Reference/policy extraction traverses only ordinary Play records while integrity
counts/hashes cover every canonical record. Branch caps and ordering cannot read
`record["request"]["expected_revision"]` for every wrapper. Preserve old format
and policy interpretation exactly through separate dispatch.

Current derived_memory and memory_jobs still use ordinary receipts/source rows.
Reject Domain 2 before their old proof source hash, cache read/admission or job
publication; actual generation snapshots pair the validated Engine with explicit
unsupported raw fallback. Query/compiler/Play and all native adapters remain
separate consumer-closure gates. No author UI or wire capability is exposed by
this document or a future schema migration alone.

## Actual evidence and handoff

Only source reads, Git state/diff inspection and Git whitespace verification were
performed. No executable new test, DDL, SQLite migration, Cargo/Node/Gradle, app,
WebView, model, device, ADB, CUA, desktop control/capture, download, protected
resource, setting, PR or merge operation ran in this review. Git
`2.33.0.windows.2`, PowerShell `7.6.5`.

Root should reconcile its Store contract with these selected decisions, freeze
the exact DDL and executable real Store/Core oracle sources, then implement and
qualify under the exclusive resource allocation. Existing Core tests, six prior
independent Core cases and historical fixtures remain unchanged. These findings
are design/compatibility seams before implementation, not reported failures of
nonexistent schema 5 code. No score, human approval, durability or M08/D08
acceptance is claimed. Scoped ownership is released in the ticket handoff.
