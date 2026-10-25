# Future Archive3 shared source implementation — 2026-10-23

This is an isolated future source stack, not the current first-foundation PR or
an exposed app capability. No implementation/build/runtime result is claimed.
Root approved the exact Archive3 contract in #12 comment6378000457.

Base: `95db6af97107ba52918885759441a9a4eca953b6`;
branch/worktree: `impl/m08-archive3-shared` / `source-archive3-implementation`.
Claims before import/edit: [#12](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6378473801),
[#30](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6378474010).
Owned production paths only: `crates/locallore-storage/src/playable_archive.rs`,
minimal normalization extraction in existing `turns.rs` and
`author_correction.rs`. This new report is the only new implementation document.
No Core/DDL/schema/app/catalog/golden/dependency changes are allocated.

## Immutable tests imported before production

Exact original chain `b85b917` → `c1b8aec` → `d2be269` is imported unchanged as
`ddc51a5` → `75610e6` → `b749479`. Actual frozen filename is
`tests/m08_archive3_hostile.rs`, not a newly renamed review test. Corrected
roundtrip source SHA256 is
`e43d5b96c8555ac4b34c39063060b8ad2028605bf5bb5a01056579e0bdefdf10`;
hostile source SHA256 is
`643b16a93c406c37f88407e3a1f7f0cd9dfdb0b7c3f02b8fcb3d95c3be6fea67`.
The original actual RED (roundtrip0/7, hostile0/6 and its historical-asset
metadata mistake) remains coordinator evidence. Corrected tests remain unrun
by this author. No expectations or immutable assets are edited on this stack.

## Frozen normalization interface before production

Root explicitly approved both crate-private helper extractions before edits:

```rust
pub(crate) fn insert_author_record(
    connection: &Connection,
    record: &CanonicalRecord,
) -> Result<(), TurnError>;

pub(crate) fn insert_play_events(
    connection: &Connection,
    receipt: &Receipt,
    before_event: &dyn Fn() -> Result<(), TurnError>,
    after_event: &dyn Fn() -> Result<(), TurnError>,
) -> Result<(), TurnError>;
```

`author_correction::insert_author_record` derives the actual AuthorV1 scope,
fixed key, fork/sequence, exact full response and existing `request_index`.
It rejects other record kinds, keeps the65,536-byte response bound, writes the
existing author turn/event SQL with zero witnesses, and opens/commits no
transaction. Existing author apply calls it at precisely its former write block.
It adds no cancellation callback or projection writes.

`turns::insert_play_events` moves the existing ordinary accepted-event/witness
SQL loop verbatim into one native-only helper. `before_event` runs at each
event's loop entry. `after_event` runs immediately after that event INSERT and
before its witness loop. Ordinary commit keeps checkpoint0 before the helper,
passes a no-op before callback and checkpoint1 after callback, then keeps
checkpoint2 after it. Existing checkpoint0..6 order and SQL remain unchanged.
Archive import passes its existing per-event cancellation check as before
callback, mapped to `TurnError::Engine(Error::Cancelled)`, and no-op after.
Both callers retain their own existing transaction. Neither helper introduces
new canonical authority, a SQL transport, independent Store, or second writer.

## Qualification boundary

Source-only allocation: no Cargo, Node, Gradle, SQLite execution, provider,
native app/model/device/ADB, desktop/CUA/protected-resource, settings or merge
action. Root holds all heavy/runtime qualification. Archive3 app/native catalog
advertisement must stay closed until all separately owned consumers are ready.
Actual Full/Busy/atomicity or platform acceptance is not inferred from source.

## Explicit advertised-version preservation decision

During source inspection, existing `branch_retention_archive.rs` pins the public
`ARCHIVE_VERSION` at2 and rejects an ordinary old payload merely relabeled3 as
Unsupported. Root explicitly approved keeping `ARCHIVE_VERSION=2` as the latest
**advertised portable interop surface** until platform closure. A private
version3 constant drives this future shared implementation. Native catalogs
remain untouched; future consumer integration must deliberately advertise3 and
the full supported `[1,2,3]` set, with separately allocated metadata assertions.

The exact version3 domain2/sourceDB5/transcript tuple is checked before its
field-layout dispatch. Thus old1/2 merely relabeled3 remains Unsupported for a
real contract mismatch, while valid3 tuples with malformed closed fields remain
Malformed. This is version dispatch, not a test-specific exception. Old1/2
goldens, public metadata assertions and frozen tests are not edited.

## Source implementation handoff

Production source commit: `f0f7c5fd61ddad206902a5f6191b7a7194f17b20`;
the final report commit additionally clarifies canonical-record counter/plan
comments without changing those behaviors. Only the three allocated production
files changed. No private child module, `lib.rs` registration or dependency was
needed. Helper contracts were frozen in `07a4cd5`; advertised-version decision
was recorded in `3433168`, before the production commit.

Implemented source behavior, **not runtime verification**:

- Same archive parser/serializer and opaque import plan, with exact3/domain2/
  physical5/transcript tuple, required possibly-empty Payload3 retirement array,
  and closed `local_records`/`records_sha256` alternatives. Preflight rejects the
  other version's field even when null; ordinary deny-unknown-fields remains.
  Versions1/2 retain their old field sets, canonicalizer and selection.
- Export captures actual `canonical_records()` under the existing coherent
  read transaction. It chooses3 only if a captured physical branch is actually
  Domain2; legacy ancestors/siblings remain valid. Full author input/reason/
  before-source and discovery binding wrappers are serialized unchanged.
  Receipt-cache omission is not a completeness mechanism.
- Validation restores through actual public Core, forks through the same
  completed-boundary/retained-birth-floor algorithm and compares every local raw
  record against regenerated native serialization. Version3 requires at least
  one actual Domain2 replay. Reference collection reuses ordinary receipts from
  complete canonical records; profile/policy metadata stays validated by Core.
- Response/index accounting uses actual native request serialization or existing
  `request_index(record)`, including all author rows, under global and selected
  replay budgets. V3 opaque branches retain actual native complete source bases;
  old1/2 do not gain a new native-basis size restriction. All formats still
  check complete response/count/archive/seed/projection/lineage bounds.
- Import consumes the same immutable capability and uses one existing target
  `IMMEDIATE` transaction. Author and ordinary events use the approved shared
  normalization helpers. The ordinary index stores the full canonical response
  and correct legacy_play/play_v2 discriminator. Author rows retain the fixed
  key/full response/index/author event kind and zero witnesses.
- Actual inserted Store bytes are replayed before commit. Full local records,
  canonical projection, selected head and V3 native basis must agree with the
  validated plan. Active projection caches are written only through existing
  `turns::write_projection` on that actual replayed engine, with domain1/2
  version and an actual transaction-row readback. Retired prefixes remain
  cache-free. The old final precommit cancellation and conflict behavior remain.
- Ordinary commit fault order remains checkpoint0, per-event checkpoint1 before
  witnesses, checkpoint2/projection/checkpoint3/turn-row/checkpoint4/head/
  checkpoint5/commit/checkpoint6. No new cancellation/fault checkpoint was added
  to that writer. Archive per-event cancellation occupies the old loop-entry
  position. No new cancellation polls were added to legacy archive replay.
- Preview3 omits empty retirement metadata as approved, and counts actual
  canonical rows including authors. Its warning explicitly includes private
  correction/discovery binding content. Neither UI labels nor native catalogs
  were edited or qualified; advertised public version remains2.

Final production source SHA256:

| File | SHA256 |
| --- | --- |
| `src/playable_archive.rs` | `355b57e88a5d3772a79f674a052f6b3750674591c0e68cc4731b764fcdcce363` |
| `src/turns.rs` | `a4c8f52a2a8dc7b5ea21f09808a689c7b2fa8fa6e2e0ee82d9603776214dea20` |
| `src/author_correction.rs` | `4d5768acfc0a65f583b2044643115d0c20d1f180a5c5c08e8cc0b1b9825d5fcc` |

All three paths above are relative to `crates/locallore-storage`.

## Actual checks and pending gates

Author actually ran scoped source formatting/parser and whitespace checks:

```text
rustfmt --edition 2021 crates/locallore-storage/src/playable_archive.rs crates/locallore-storage/src/author_correction.rs crates/locallore-storage/src/turns.rs
git diff --check
```

They succeeded. Git/source inspection confirmed no app/Core/migration/dependency
changes and no changes to either imported frozen test. Source hashes were
collected directly. **No Cargo/typecheck/Clippy/test/Node/Gradle/SQLite/provider/
model/native/app/device execution occurred. All new source remains UNCOMPILED /
UNRUN.** Rustfmt parsing does not prove type correctness or runtime behavior.

Root's next allocated checks, not executed here:

```text
cargo test --locked --offline -p locallore-storage --test m08_archive3 --test m08_archive3_hostile -- --nocapture
cargo test --locked --offline -p locallore-storage --test playable_archive --test branch_retention_archive --test archive_interruption
cargo test --locked --offline -p locallore-storage --test m08_author_store --test m08_author_store_review --test m08_author_play25
cargo test --locked --offline -p locallore-storage --lib
```

Retain first actual compile/fixture/behavior failures distinctly; do not edit
the frozen expectations to hide them. Broader Store/Workspace/native/shared
strict checks remain Root-owned, especially ordinary fault checkpoints,
legacy cancellation poll counts, genuine schema5 Full/Busy rollback and
postcommit acknowledgement recovery. The frozen packet deliberately leaves
near16MiB combined-budget/deepest-boundary and generated-Play reference coverage
gaps, documented in its original handoff. No new actual Full/Busy/atomicity,
process-death, model, render or device acceptance is claimed.

Do not expose or advertise3 from this stack alone. Native supported-version
catalogs, exact desktop/Android preview/completion decoders, honest record labels,
cross-surface retained acknowledgements and actual Domain2 resume/inspection
limitations need their separately allocated implementation and qualification.
The current first-foundation PR/source and Root's active processes remain
unaffected. This source-only future stack stops at handoff, not merge or release.
