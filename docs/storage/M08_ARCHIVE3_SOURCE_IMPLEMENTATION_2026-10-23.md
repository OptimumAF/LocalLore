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
