# Native generation snapshot port (2026-10-23)

Refs #11 (M07.01/.03/.04), #29 prerequisite. This is a shared read-only port,
not the production Play consumer. Base: coordinator schema4 source
`33e5d3ed36b14bb62d39323fc78701e54d2fe4b5`; that base was not accepted main
at implementation time. Claims: #11 comment6373833132 and #29 comment6373833453.

## Implemented contract

`HostGenerationSnapshot { engine: Engine, coverage: CoverageRead }` is native
only, with no Serialize/Deserialize or HostCommand variant. The selected live
session fixes the scope and player from its actual cached Seed. The caller
supplies an expected head, never an observer. A successful return must match
that scope/head/player and the complete selected Seed, so reimporting a different
seed at the same identity and revision is stale. Inspection mode cannot select
an NPC for generation. The native Engine is trusted application data, not a
redacted prompt; callers must use the existing compiler and recheck retained
opaque coverage against that actual Engine before consumption.

The compatibility default reads the actual `Persistence::resume` Engine and
returns `RawFallback(Missing)`. Ephemeral Hosts return their coherent selected
Engine clone with the same honest fallback. The repository override uses only
`Store::context_snapshot(MemoryJobRequest)` for Engine and proof from one read
transaction; it does not construct a proof, duplicate eligibility checks, admit
a job or run maintenance. There is no second resume/read on that path.

The coordinator approved a narrowly scoped error rule before implementation:
missing selected source/player (`NotFound`) means `Stale` for this generation
port. Otherwise an archive replacement that removes the cached player would
fail before the full Seed comparison. This does not change Store errors or
other native ports. Other closed memory errors preserve their existing category.

The Host owner mutex serializes selection and snapshot validation. Native callers
must use their I/O worker and a short, nonreentrant cancellation callback. The
snapshot path catches cancellation callback panics as Cancelled and fails closed
on a poisoned Host mutex. It does not refresh or replace sessions, mutate a turn,
grant author/Story Lab privileges, or alter observer knowledge. Returned historical
snapshots can become stale after return; they are not a lease on future canon.

## Frozen model-free test oracles

New Core module `host/generation_snapshot_tests.rs` covers the legacy default's
actual newer source head, honest missing cache, scope/head/nonplayer refusal,
early/panicking/late cancellation, native override returned scope/head/full Seed
guards, and fail-closed poison before persistence dispatch. Those are native
boundary doubles, explicitly separate from SQLite integration.

New workspace integration `generation_snapshot_host.rs` uses actual Host,
Repository, Store and typed accepted turns. Its six tests require:

1. Missing cache yields Missing without SQLite byte changes or job admission;
   a real four-event receipt remains canonical and missing-cache fallback honest.
2. Completed actual player and NPC caches stay separate. Player proof rechecks
   against the same returned Engine using Core; omniscient/character inspection
   cannot change selected player, NPC knowledge, receipts, cache status or DB bytes.
3. Live session/scope/head/cancel/closed/JSON and inspection privilege boundaries.
4. Actual story deletion and archive import of a changed Seed at the same
   scope/head/id/player is Stale, leaving replacement state unchanged.
5. Actual replacement without the cached selected player maps NotFound to Stale.
6. Ephemeral scope/head/Engine and explicit in-memory missing-cache fallback.

All histories and SQLite paths are synthetic, local temporary artifacts. No
canonical SQL fixture writes, model calls, UI hooks or new dependencies occur.
Existing public deletion/import APIs create the ABA fixture; no copied/forged
receipts establish its replacement world.

## Verification status at source freeze

Rust 1.93.1 (01f6ddf75 2026-02-11), Cargo 1.93.1 (083ac5135 2025-12-15),
rustfmt 1.8.0-stable. Test oracles were authored and frozen before compilation.
Coordinator heavy-build slot is required before Cargo execution. No current-task
compile/test/Clippy result is claimed in this initial document.

Planned scoped commands use an isolated D target and UUID TEMP/TMP,
`CARGO_PROFILE_DEV_DEBUG=0`, `CARGO_PROFILE_TEST_DEBUG=0`,
`CARGO_INCREMENTAL=0`, `--jobs 1`, locked dependencies:

```text
cargo test --locked --jobs 1 -p locallore --features host generation_snapshot_tests
cargo test --locked --jobs 1 -p locallore-workspace --test generation_snapshot_host
cargo test --locked --jobs 1 -p locallore --no-default-features
cargo test --locked --jobs 1 -p locallore -p locallore-workspace
cargo test --locked --jobs 1 -p locallore -p locallore-workspace --all-features
cargo clippy --locked --jobs 1 -p locallore -p locallore-workspace --all-targets -- -D warnings
cargo clippy --locked --jobs 1 -p locallore -p locallore-workspace --all-targets --all-features -- -D warnings
cargo fmt --all -- --check
```

## Remaining gate

Independent coordinator review/integration and actual test execution remain
required. Play prepare/Work execution, consumer prompt2.4, opportunistic job
maintenance and desktop/JNI callers are deliberately untouched and require the
next coordinator slice. No native UI, Android/device, actual inference, memory
quality, performance, schema4 acceptance, release or whole M07/D07 completion is
claimed by this port.
