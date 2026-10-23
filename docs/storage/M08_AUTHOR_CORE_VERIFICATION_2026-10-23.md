# M08 pure Core author-correction source freeze — 2026-10-23

Refs #12 (M08.03), #30 (D08.05 prerequisite). Status: implementation under
Core verification. This is neither native authoring acceptance
nor permission to expose Domain 2 through the current applications.

## Binding and ownership

Contract: `03e25f26d85d151853dd26f45ea62602940b6362`.
Base: `42ca071c8221288f35c3db65e407eeab9d279bb0`; its relevant production is
the accepted M07 `f486043` source. The coordinator confirmed that subsequent
M07 acceptance at `a14c89986378742f4a74e157eef6803746c8c47e` changes no relevant
Core production. No reset, rebase or other worktree modification was performed.

Branch `impl/m08-author-core`, separate `source-author-core` worktree. Exclusive
existing ownership is `crates/locallore/src/engine.rs`; `lib.rs` has only the new
module alias. Other files are the new `author_correction.rs`,
`tests/m08_author_core.rs`, `tests/m08_author_legacy.rs`, and this report. Host,
Store, schemas, contracts, compiler, Play, inspection, and applications are not
edited. Claims: #12 comments 6376379551/6376543015; #30
6376379801/6376543259.

## Frozen sequence and limits

1. `cc4bb65b34e01a58811985c7c005af2ce909d585`: seven author and two legacy
   tests, before production changes. Never compiled or run at that source.
2. `b3d314e8cbf87a7eee7edf6e031a3d97db90e51f`: the NEW private Say fixture
   was corrected from a non-colocated NPC to the colocated player self using
   the existing admission rule. The privacy oracle is unchanged. Three
   same-scope/inherited-scope fixed-key tests were added before production.
3. `5476e36310101fe2a6c240cbe8cd9169d291bf04`: pure Core implementation.
4. `326792b081cd447d03c4609786a378da2e8b97a1`: four additional unexecuted
   replay, lineage, cancellation and escaped-string oracles. No original
   expectation was removed or weakened.

There are 14 new author tests and two new legacy tests. Their assertions are
frozen before the first build. Any compile failure, fixture correction or
production failure must be recorded separately; source review is not a test
result.

One `records: Vec<CanonicalRecord>` owns revision, boundaries, source prefix,
restore and record limits. Legacy records serialize directly as their unchanged
Receipt. Domain 2 wraps play receipts with sparse private observation bindings;
private author records consume one revision and no mechanical time or actor
observation. The existing Receipt/Effect/Request declarations are unchanged.

The read-only `receipts()` compatibility slice is lazily cloned from play
records into a `OnceLock`. It contains no author records and is invalidated on
append. It is never used by Core to determine history, source identity,
revision, caps or replay. This has a real bounded memory cost: ordinary receipt
data may be duplicated, including when a populated Engine is cloned. It is not
a memory or speed improvement claim. New admission applies the existing
4096-record / 16 MiB history / 64 KiB record / 256 KiB projection limits to the
mixed authority; source-prefix hashing remains bounded separately.

Fresh native prepare/apply compares actual parent head H and full parent/fork
bases. The opaque plan has no Deserialize implementation. The pure outcome is
a new child; parent history is unchanged. A history-only restore onto an actual
forked child checks its real immediate parent/fork f, retained old value and
prior truth binding, then compares the entire regenerated author record. It
retains H >= f as creation provenance without inventing the unavailable parent
future. Original scopes remain original. Root replay cannot invent ordinary
fork nodes absent from the supplied history; restore_continuation uses the
actual native fork metadata.

The physical author key is exactly `author-correction-v1`, reserved only in a
scope containing an actual author record. Legacy arbitrary use and another
branch's namespace remain valid. All current legacy context/visitor and
generated-play paths refuse Domain 2 with existing `Error::Version` until the
coordinator closes compiler/query/Play 2.5 and Store/schema 5 integration.

One explicitly reconciled native DTO detail: `ObservationSource::Event {
source: EventRef }` uses an explicit named source field (serialized with
`kind: "event"`), rather than the contract sketch's `Event(EventRef)` syntax.
The coordinator accepted this actor-safe shape on 2026-10-23. It identifies the
actual eligible observation, never its private truth/author source. This is not
a new current wire capability.

## Oracles awaiting execution

- Known player/NPC A survives private world correction to B; actor views omit
  B, reason, truth references and stale/source-comparison flags.
- Uniform eligible discovery, including same-value rediscovery, updates only
  the observing player and preserves exact retry behavior.
- A→B→A retains distinct canonical sources without an actor-facing oracle.
- Multi-event partial boundaries reject; private author head appears in the
  boundary catalog independently of the ordinary receipt cache.
- Mixed restore reconstructs full records and rejects sequence, witness and
  foreign truth-binding tampering.
- Stale/cancelled/invalid/bounded plans leave the parent unchanged.
- NPC receipt views contain only eligible events and no raw player Request,
  Proposal, narration or private author record; empty records are filtered.
- Fixed-key collision is scoped to the actual author record's branch.
- H>f restore preserves retained prefix and excludes parent future; authored
  inherited prefixes and prebirth snapshots preserve scope/lineage.
- Version refusal and panic-safe cancellation produce no actor callbacks.
- Escaped 2048-byte input fields round-trip within encoded record limits;
  compatibility-cache invalidation cannot determine canonical head.
- Legacy projection and Receipt serialization/restore remain byte exact;
  known discovery and AuthorIntent admission remain unchanged.

## Actual local checks and queued commands

Only standalone formatting and whitespace checks have run:

```text
rustfmt --edition 2021 --config skip_children=true crates/locallore/src/engine.rs crates/locallore/src/author_correction.rs crates/locallore/src/lib.rs crates/locallore/tests/m08_author_core.rs crates/locallore/tests/m08_author_legacy.rs
git diff --check
```

Both succeeded. `rustfmt 1.8.0-stable (01f6ddf758 2026-02-11)` on Windows.
This confirms formatting/parser acceptance, not typechecking or behavior.

After the coordinator grants the exclusive build slot, use a fresh owned
D-drive target and UUID TEMP/TMP, `CARGO_BUILD_JOBS=1`,
`CARGO_INCREMENTAL=0`, and debug info zero. Planned checks, sequentially:

```text
cargo test --locked -p locallore --test m08_author_core --test m08_author_legacy --jobs 1
cargo test --locked -p locallore --all-features --test m08_author_core --test m08_author_legacy --jobs 1
cargo test --locked -p locallore --all-targets --jobs 1
cargo test --locked -p locallore --all-targets --all-features --jobs 1
cargo clippy --locked -p locallore --all-targets --jobs 1 -- -D warnings
cargo clippy --locked -p locallore --all-targets --all-features --jobs 1 -- -D warnings
```

Coordinator-owned full workspace/Store/compiler compatibility
and actual wire/UI authoring remain separate gates. No schema 5 durability,
Domain 2 compiler support, quality, performance or human acceptance is claimed.

## First execution and preserved failure

The coordinator subsequently granted the exclusive Core slot. Environment:
Windows, rustc `1.93.1 (01f6ddf75 2026-02-11)`, cargo
`1.93.1 (083ac5135 2025-12-15)`. Dedicated `author-core-rust` target and
`author-core-temp-ae16228d-d6b0-4ce6-91dd-137241487fb2` TEMP/TMP are outside the
repository. Locked/offline, jobs 1, incremental/debug info disabled, ordinary
`LIBSQLITE3_FLAGS` empty. No dependencies, models or assets were downloaded.

Actual frozen focused command (with `--offline` added to the above command)
at production `5476e36` / test `326792b`: **16 passed, zero failed/ignored**;
compile 19.57 s. No compile or fixture correction was needed.

The first full default Core `--all-targets` run then failed in two unchanged
legacy restore tests: `empty_history_and_alternate_seed_do_not_inherit_other_story_state`
and `every_recorded_envelope_field_is_checked_including_resolved_effects`.
Actual mismatch: returned `Scope`, required `CorruptHistory` (restore result
7 passed / 2 failed; process exit 101). The new restore helper had omitted
the old `.recorded(...)` error mapping. This was a production compatibility
defect, not an invalid fixture. The original log `02-core-default.log` is
retained locally unchanged. No test or expected output was altered.

Narrow production fix `9a9a616` reinstates only the closed `CorruptHistory`
mapping in `author_correction.rs`. The identical nine existing restore tests
plus all 16 frozen tests then passed: **25 passed, zero failed/ignored**;
compile 7.47 s, restore 0.93 s. Log `03-restore-corrected.log` retained.
Full default/all-feature and strict Clippy reruns remain pending at this
intermediate report. All commands add `--offline`; no app/device/model check
has been performed.

Frozen test file SHA-256 (unchanged through this fix):

```text
m08_author_core.rs    10617971e8029f82baaaeb036225ce32e76ee8175d32970382044fd2eb12c279
m08_author_legacy.rs  c2151b3ea252777c8c0d815dcb70f0d439f91a64e3c8366ab8f80e2ff8552843
```
