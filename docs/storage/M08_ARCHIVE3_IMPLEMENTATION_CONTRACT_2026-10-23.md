# Archive3 implementation contract — 2026-10-23

**Proposed, source-audited, unimplemented and unverified.** Coordinator decision
and a subsequent implementation claim are required. Scope: #12 M08.04/M08.06
and #30 D08 prerequisites. This document does not approve exposure of Domain2
play, author UI, model execution, or device qualification.

Frozen source: `a1cc243d2d21e8a35895aff7d88195c8d3ef0df3` on
`design/m08-archive3`, isolated `source-archive3-contract`. Claims before this
new document: [#12](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6377949638)
and [#30](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6377949814).
Reviewer ownership is **only this new document**; all allocations below are
proposals, not permission for other agents to edit those files.

## Decision and existing authority

Extend the existing single-file, full-private JSON archive with an explicit
version3 for a story containing any Domain2 canonical history. Keep Domain1
export selection unchanged: version1 without retirement, version2 with
retirement. Do not relabel old archives, receipts, captured metadata, or hashes.

Keep `Store::export_archive`, `validate_archive`, opaque `ValidatedArchive`,
`Store::import_archive`, and existing native brokers as the only archive path.
No database migration, second archive engine, raw-SQL transport, alternate
interpreter, job service, or new dependency is needed.

Actual reusable source boundaries:

- `locallore-storage/src/playable_archive.rs` already bounds unique JSON,
  canonical checksums, one coherent export transaction, ancestry, retirement,
  opaque validated import capabilities and one target `IMMEDIATE` transaction.
  Its export explicitly refuses Domain2, avoiding silent omission. Current
  `ValidatedBranch`/import are receipts-only and write projection version1.
- `Engine::restore(seed, &[String])` and `restore_continuation` already replay
  mixed serialized canonical records, regenerate them through actual Core, and
  compare complete regenerated JSON against the input. No public
  `Deserialize<CanonicalRecord>` or constructor is needed. `replay_records`
  accepts already-native records; it is not the untrusted parser.
- `CanonicalRecord::{original_scope,first_revision,last_revision,turn_key,kind}`
  and `Engine::canonical_records` supply actual local history. `receipts()`
  deliberately excludes AuthorV1 and must never source Archive3 completeness.
- `turns::read_engine_retained` reconstructs private original ancestry and
  validates normalized ledger rows. `turns::canonical_kind`,
  `author_correction::request_index` and `turns::write_projection` already encode
  the relevant Store contracts. Author source rows have zero witnesses.

## Exact version3 wire tuple

Use the existing canonicalizer: recursively sorted UTF-8 object keys, retained
array order, serde_json scalars, no whitespace. Checksums are integrity checks,
not signatures or trust. Keep the same fixed JSON file; there are no archive
members, compressed streams, external paths, scripts, executable references or
automatic downloads to interpret.

The strict top-level fields remain exactly:

```text
format = "locallore-playable-archive"
version = 3
canonicalization = "locallore-json-v1"
privacy = "full_private"
payload = Payload3
integrity = Integrity3
```

`Payload3` fields, all required and with unknown fields rejected:

```text
domain_version = 2
source_database_schema_version = 5
story = { id, title, seed }                 # same seed/config object, seed.version1
transcript = "accepted_canonical_records_v2"
branches = [Branch3, ...]                  # strictly ascending branch IDs
retired_branch_ids = [id, ...]             # required, ascending; may be empty
required_policies = [{policy,prompt_version}, ...]
model_references = [{sha256,profile}, ...]

Branch3 = { id, parent, fork_revision, head_revision, local_records }
Integrity3 = { payload_sha256, seed_sha256, branches }
Integrity3.branches[] = { id, records_sha256, canonical_state_sha256 }
```

`local_records` contains each **actual serialized CanonicalRecord** whose
`original_scope()` equals that branch's scope, once and in accepted order:

- Historical LegacyPlay remains its exact unwrapped Receipt JSON.
- Domain2 PlayV2 remains `{record_version:2,kind:"play",receipt,observations}`.
- AuthorV1 remains
  `{record_version:2,kind:"author_correction",receipt}`.

Do not flatten wrappers, rewrite original scopes, derive bindings from current
truth, or put an author correction into the dialogue transcript. Preserve full
private author input/reason/expected parent creation revision, before truth
source, rules, seed, sequence/time, and zero author witnesses. Preserve every
discovery observation's actor/fact, event `original_scope`/sequence, and truth
source (`seed_fact` identity or author EventRef), even when currently obsolete.
An A→B→A value is not permission to merge source identities.

The whole payload hash covers lineage and references; each local record hash
covers its full private wrapper; the replayed canonical-state hash covers the
Domain2 mechanical **and knowledge/source-reference** projection. Never hash
only `Engine::state()` or the receipts cache. Do not serialize opaque
`AcceptedHistoryBasis` as a proof. In-memory validation/import parity can compare
actual native bases reconstructed through the same Engine; archive data cannot
construct a native source token or memory coverage proof.

Require at least one replayed Domain2 branch for version3; Domain1 root/ancestors
and siblings in that story are valid. Match the fixed source-schema5 tuple;
future schema6/format4 is a closed `Unsupported` until separately allocated.
Old version1/2 payload/domain/config rules and original accepted assets remain
unchanged, including Domain2 rejection on those formats. Their source database
metadata remains truthful, not relabeled as a different schema.

Derive sorted unique policy/prompt and model/profile references from all local
records' optional ordinary receipts/PlayRecord, using the existing reference
collector. Full PlayRecord retains policy, prompt, profile, narration, fallback,
timings, context provenance and current context_policy when present. Core's
exact history dispatch owns 2.1–2.5 compatibility; Archive3 must not independently
accept arbitrary compiler/narrator/context-policy tuples. Author policy stays
inside the validated author receipt and never names a model to load.

## Replay, retention and budgets

Reuse the existing bounded topological ancestry walk and Core fork/restore
path. Select ancestor records by actual completed record boundaries, not by
`raw.request` (author records have no ordinary request). For each ancestor cap,
include whole records ending at/before that cap; a cap inside a multi-event
record is invalid. Preserve the existing parent-birth floor for nested rewinds.
After each reconstruction, require exact scope/head and exact branch-local raw
JSON equality with regenerated native records. Validate every physical branch,
including retained retired ancestors, and all source refs through Core replay.

Keep existing retirement rules: root never retired; IDs sorted/unique; physical
retired branches only when required ancestors; their head is the exact retained
prefix cap; collected identities remain tombstones with no invented history;
public resume of retired scopes remains `NotFound`. No descendant gains later
parent or sibling history. Do not import caches or new leases for retired data.

All bounds are checked with overflow-safe byte/count accounting and cancellation:

| Item | Frozen maximum |
| --- | --- |
| Input/canonical envelope | 32 MiB UTF-8; no compression |
| Physical archive branches / lineage depth | 32 / 32 |
| Physical plus retired/tombstoned identity union | 256 |
| Unique local canonical records across archive | 4096 |
| One full serialized canonical record | 65,536 bytes |
| Seed / reconstructed canonical projection | 131,072 / 262,144 bytes |
| Model and required policy references | 64 each |
| IDs / title | ASCII `[A-Za-z0-9_-]` 1–64 / 1–256 Unicode scalars, no NUL |
| Persisted response **plus request index** budget | 16 MiB globally and per restored lineage |

For ordinary records the request index is the actual Receipt request; for an
author record derive the actual native `request_index(record)`. Count each
record once, including author rows; also enforce Core's response-only history
budget. Do not add synthetic `{}` request bytes or assume author data is free.
Use actual persisted serialization for response/index lengths. Existing
version1/2 acceptance budgets are not silently tightened by this version3 rule.
Existing safe-integer platform control limits remain; Rust `i64` conversion
guards must precede SQL. Platform controls remain bounded separately from the
32 MiB archive body (Android control replies currently 16 KiB).

## One Store import and broker recovery

Extend the opaque validation plan to contain native local records and replayed
engines/projections, with a closed internal version discriminator. It must not
gain public mutation/Deserialize. Keep one shared target import transaction:

1. Validate bytes and immutable plan before destination mutation. Keep existing
   native disposable pinned staging database, cleanup and revalidation paths.
2. Begin the existing `IMMEDIATE` transaction, check story count/conflict,
   insert the validated story, topological branch metadata, entities and
   retention tombstones using current Store ownership.
3. Insert each actual local native record into the existing canonical tables.
   Extract a **crate-private Store normalization helper**, shared with the
   author writer where needed, rather than inventing a platform SQL writer.
   Legacy/PlayV2 rows use actual request/index and full record response with
   `legacy_play`/`play_v2`; normalized events retain actual scopes/witnesses.
   Author rows use `request_index`, fixed `author-correction-v1`, `author_v1`,
   the full canonical record response and author event `record_kind` with no
   witnesses. This is importing accepted history, not re-running the public
   author apply operation or checking the parent's current head as fresh intent.
4. Use existing `turns::write_projection` on active replayed engines so
   projection_version is the engine's actual domain1/2. Keep retired prefixes
   cache-free. Do not write summaries, embeddings, memory jobs, drafts or model
   selection. Do not import noncommitted workflow keys/status.
5. Before commit, replay **actual transaction bytes** with
   `read_engine_retained`; require full records, projection, scope/head and
   native accepted-history-basis equality with the validated reconstruction.
   Propagate genuine `Full`/Busy/cancellation; any failure rolls back all rows.
6. Check cancellation immediately before commit. Commit is the linearization
   point. A later cancellation/lost acknowledgement cannot claim rollback.

Keep existing conflict/idempotency semantics: importing any existing story ID,
even identical content, is `Conflict`; do not overwrite, rename or merge.
Desktop operation-ID status plus retained broker acknowledgement barrier and
bounded token/hash/root binding own recovery. Android native tokens/generation
and library reconciliation retain their current semantics. A consumed token
is not a new import operation. Lost acknowledgement requires explicit original
operation/library inspection; no automatic retry, pending workflow resume or
model load. No new persistent import journal/current-operation endpoint is
introduced. Check preservation of cross-surface archive/fork/memory retention.

## Preview/control closure before exposure

Keep operation/JNI control envelope version1. Reuse current metadata-only
preview fields with `preview.version=3`. For minimal compatibility,
`committed_turns` remains the bounded count of committed **canonical ledger
records**, including author rows for3; label it “Accepted records (play and
author corrections)” in version3 views/results. In versions1/2 the same number
continues to count ordinary accepted turns. This counter definition must be
explicitly approved; do not silently show author rows as ordinary play turns.

Preview3 retains the existing optional serialized retirement field convention:
absent when empty, otherwise sorted nonempty `retired_branch_ids`. That is
distinct from Payload3's required possibly-empty array. Freeze these two exact
preview key sets; do not just accept arbitrary extra keys. No author prose,
private binding, seed, model prompt or filesystem path is added to recovery
identity. Existing payload hash/root/token binding is sufficient.

Before any version3 export/import button/catalog can succeed:

- Desktop `archive-model.ts` currently types/decodes only1/2; extend the exact
  preview3 shape/retirement combinations and same shared completion decoder
  used by ArchiveController and BrokerRetentionGate. Reject malformed3 and
  wrong command/kind/root/hash before accepting a terminal result. Preserve
  uncertainty across context retirement and unknown admission acknowledgements.
- Desktop native `archive.rs::catalog` currently emits
  `[1, ARCHIVE_VERSION]`; changing latest to3 would silently omit2. Emit exact
  `[1,2,3]` only after shared/platform closure, with latest3. Preserve broker
  single worker, existing result retention, preview TTL/token cap, consent,
  pinned path/staging/finalization and cleanup behavior.
- Android `NativeArchive.kt::prepared` currently requires1..2 with exact field
  sets and nonempty retirement for2. Add explicit3 decode preserving old1/2;
  test empty/absent/nonempty3 retirement behavior. `imported` control shape can
  stay `{root,branches,committed_turns}` with the approved canonical-row count.
  `ArchiveController`/`ui/ArchiveDialog.kt` labels must use honest record counts
  (generic “accepted records” also works when result DTO lacks version).
- Android native `locallore-android/src/archive.rs` and desktop native staging
  already import through Store. Retain all-active-head verification and retired
  skip rules; verify Domain2 actual full records, not only root revision.
  Existing JNI byte-array archive transport needs no new function/signature.
- Database schema5 admission and paired ordinary platform builds must be
  qualified. Transfer success does not imply legacy Host PlaySnapshot/Inspect
  can read Domain2: the typed legacy refusal remains until the actual V2 view
  route is ready. Keep Archive3 hidden/unavailable in product flows until they
  can explain supported transfer and the actual resume limitation honestly;
  never present receipt-cache fallback as complete Domain2 playback.

## Proposed exclusive ownership and freeze order

These are allocations for coordinator review, not active overlapping claims:

| Owner | Exact proposed production/test paths |
| --- | --- |
| Root shared Store | Existing `crates/locallore-storage/src/playable_archive.rs`; existing `turns.rs` and `author_correction.rs` only for one shared normalization helper; no migration/DDL or Core validator edits. Optional NEW `src/playable_archive/v3.rs` is a private DTO/adapter of the same importer, not a second importer. |
| Independent Store oracle author | NEW `crates/locallore-storage/tests/m08_archive3.rs` and NEW `tests/m08_archive3_hostile.rs`, frozen before production; a NEW source-only review doc if separately claimed. Root owns any pressure hooks in existing private test modules. |
| Desktop adapter author after Store interface freeze | Existing `apps/desktop/ui/archive-model.ts`, `ArchivePanel.tsx`, `src-tauri/src/archive.rs`; NEW focused controller/gate3 vectors and runner, existing suites preserved. No competing controller/broker or unallocated main edits. |
| Android owner after DTO freeze | Existing `apps/android/.../NativeArchive.kt`, `ArchiveController.kt`, `ui/ArchiveDialog.kt`; `crates/locallore-android/src/archive.rs` only actual staging parity; NEW JVM/native3 cases. JNI production signatures unchanged. |
| Root integration | Existing shared archive spec/README and exact harness expectations only after claims; current locked Rust/frontend/native/ordinary Android compatibility commands and artifact review. |

## Oracles to freeze before implementation

Use actual public Core/Store authors, typed accepted commits and synthetic
current Play2.5 provider plumbing to create native accepted records. Do not
forge receipt authority. Hostile variants may mutate serialized genuine
archives and recompute their untrusted checksums to prove semantic rejection.

| Frozen group | Required observations |
| --- | --- |
| Mixed round trip | Legacy prefix → actual author B → old-knowledge A actor → actual discovery B → later author C/A on child, siblings and nested rewind. Export/import/reopen/export; compare exact full canonical records, actual bases, canonical bytes, transcript/provenance, original refs, all active heads and retirement catalogs; no provider during replay. |
| Source identity | Equal mechanical state/head and equal visible values with different private author sources must produce different full record/source fingerprints. Retain duplicate/re-observation and A→B→A event refs; later truth never retroactively changes actor observation. Actor Query2/Compiler2 reads after transfer match each actor's pre-transfer view and exclude omniscient/private author reason. |
| Historical compatibility | Exact accepted archive1/2 assets/hashes and Play2.1–2.4 receipt encodings unchanged; ordinary Domain1 export still selects1/2. Format3/domain1-only, 1/2 mixed wrappers, bad source tuple, unknown policies/context tuple and future4/schema6 reject without writes. |
| Hostile structure/source | Recomputed hashes cannot admit extra/duplicate JSON keys, truncation, missing/private wrapper fields, changed author input/before/witnesses, dropped/forged discovery binding, wrong original scope/sequence, nonexistent/sibling/future truth source, changed narration/Play metadata, duplicate turn key, split completed boundary, cycles/depth/missing parent or altered retirement caps. |
| Boundaries | Exact/over caps for bytes, record/index aggregate, individual full wrapper, projection, branches/union/depth/models/IDs; genuine Core-generated escaped text counts encoded UTF-8. Oversize request-index+record combined must fail even when each response alone fits. |
| Atomicity/recovery | Pre-existing unrelated stories remain byte-equivalent in canonical rows. Cancel true/panic at validation and after intermediate import inserts; real SQL Busy and genuine SQLITE_FULL during normalization/projection/commit must leave zero new canonical rows. No injected fake error counts as actual Full. Cancellation after winning commit/lost ack leaves exactly one story, no retry duplicate; same identity reimport Conflict. |
| Native/platform closure | Actual desktop3 preview/export/import with honest count/privacy/retirement; cross-surface unknown/known-ID acknowledgement retention and stale completions; Android strict3 decode/exact keys, native staging/reopen/continuation and bidirectional archive transfer preserve actual source/ref/knowledge. Wrong-format controls never publish or clear uncertainty. No old pending workflow/model load. |

Keep all old hostile/path/sidecar/pinning/cleanup/TTL/consent tests. Physical
phone, emulator, actual WebView/native IPC and headless mock results must be
reported separately. Current schema4 capacity profiles/fixtures cannot establish
schema5 Full calibration; preserve old profiles and use a separately identified
actual schema5 test setup.

## Handoff status

This reviewer ran only Git/source searches and `git diff --check`; no Rust,
Node, Gradle, SQLite, provider, native app, device, desktop or protected-resource
execution. All proposed Archive3 tests and interfaces are **UNRUN**. Root owns
the format/counter decision, exact path claims, independent source-test freeze,
first actual RED and implementation/GREEN sequence. Next runnable work is to
freeze the two independent Store oracle files against this approved contract;
do not expose version3 by changing a latest-version constant alone.
