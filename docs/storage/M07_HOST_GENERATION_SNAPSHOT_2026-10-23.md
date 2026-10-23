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
on a poisoned Host mutex. The method-local cancellation observation is latched:
even an overriding port that ignores a one-shot true/panic and returns a valid
Engine cannot erase cancellation at the final Host check. It does not refresh or replace sessions, mutate a turn,
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

Three additional unit oracles were frozen separately: an override invoking the
callback without its own panic catcher must leave the owner usable, and overrides
ignoring a one-shot true or one-shot panic must still return Cancelled. The original
five Core tests and all six actual SQLite tests were unchanged by those additions.

## Verification status at source freeze

Rust 1.93.1 (01f6ddf75 2026-02-11), Cargo 1.93.1 (083ac5135 2025-12-15),
rustfmt 1.8.0-stable. Test oracles were authored and frozen before compilation.
The initial freeze preceded coordinator resource GO and every Cargo execution.
All results below were executed by this agent, sequentially with one jobs1 Cargo
process; none are inherited coordinator or source-author evidence.

Executed scoped commands used an isolated D target and task-unique TEMP/TMP,
`CARGO_PROFILE_DEV_DEBUG=0`, `CARGO_PROFILE_TEST_DEBUG=0`,
`CARGO_INCREMENTAL=0`, `--jobs 1`, locked dependencies:

```text
cargo test --locked --jobs 1 -p locallore --features host --lib generation_snapshot_tests
cargo test --locked --jobs 1 -p locallore --no-default-features
cargo test --locked --jobs 1 -p locallore -p locallore-workspace
cargo test --locked --jobs 1 -p locallore -p locallore-workspace --all-features
cargo clippy --locked --jobs 1 -p locallore -p locallore-workspace --all-targets -- -D warnings
cargo clippy --locked --jobs 1 -p locallore -p locallore-workspace --all-targets --all-features -- -D warnings
cargo fmt --all -- --check
git diff --check
```

Final tested source: `e1968eb8d77ab978515f19dcbb3207598398b929`.

| Check | Actual result at final source |
| --- | --- |
| Snapshot Core unit filter | 8 passed, 0 failed, 28 filtered |
| Core + workspace default | 272 passed, 0 failed, 0 ignored |
| Core + workspace all features | 272 passed, 0 failed, 0 ignored |
| Portable Core, no default features | 166 passed, 0 failed, 0 ignored |
| Strict Clippy, both feature modes/all targets | Both passed, warnings denied |
| Workspace fmt and diff whitespace | Both passed |

The broad suites each include the same six actual Host/Repository/SQLite tests.
These are Windows native Rust tests, not native WebView rendering, JNI/device
execution or an inference cohort. No fixture/type/compiler failure occurred in
the original frozen port: `1a2017b310c4be3760b159ea5a08e63d7dd60bbb`
passed the default suite (269/0/0), including initial Core5 and SQLite6.

### Preserved RED to GREEN evidence

1. New regression-only `d9d6babdba6bfea66138f3b2701c704ef7ae327e`
   on unchanged original production: 0 passed, 1 failed. The callback panicked
   inside the override and the subsequent Host read failed the usable-owner
   assertion. `830ca4e65e0a1ef0198043a3f5aa01c2b0bf4446` forwarded a
   panic-safe callback; unchanged regression and all Core6 then passed. Broad
   default and all-features suites at 830 each passed 270/0/0.
2. Coordinator review identified that a non-latched wrapper could forget an
   ignored one-shot result. New regression-only
   `d1ae2c6dba853c806f923fc062634b982a9433db` on unchanged 830 production:
   0 passed, 2 failed. Both one-shot true and caught panic incorrectly returned
   success. Final e196 added only the local latch and its entry/forwarded/final
   checks; both unchanged regressions and the original override regression pass.

Exact RED commands, in chronological order:

```text
cargo test --locked --jobs 1 -p locallore --features host --lib cancellation_panic_inside_override_is_cancelled_and_host_owner_remains_usable -- --exact host::generation_snapshot_tests::cancellation_panic_inside_override_is_cancelled_and_host_owner_remains_usable
cargo test --locked --jobs 1 -p locallore --features host --lib ignored_one_shot_
```

Logs/targets remain local outside the worktree. Sanitized bindings (SHA-256):

| Local log | SHA-256 |
| --- | --- |
| override-red.log | c3a4759a802de15623c1fd2372b53355fd4433ee35226dfba5dabe26886e8d3b |
| latch-red.log | 6d0296de23b50b1c94c5d3b3a84cf04c675e07f799634644b37499521d7b2f3c |
| final-default.log | 9e99ed4dd8126129bcfe0b781844fc83c08335d9773c85361d7aba58a4f6293c |
| final-allfeatures.log | d8b1bb598da54093dc7a78d6997eb473fa4ef930d34cc7f41fdee11c0fad55f8 |
| portable.log | 3408ed0e4097caf7c3208850457aab4ed38ca3cb7106f9ab427469a76baf1453 |

Final Core test file SHA-256:
`884fc4c8174ea29a8cfda747d586b1a392e17ffd500e9f9d10e2177f5b9ac13c`.
Unchanged actual SQLite test file SHA-256:
`1ad4b61b43e63db65dd285a8ded7241b3b1546c5f9310860d0d18d34bbc95fd2`.

## Remaining gate

Independent coordinator review/integration remains required. Claims are released
to the coordinator with this clean handoff; no task checkbox or milestone was
marked accepted. Play prepare/Work execution, consumer prompt2.4, opportunistic job
maintenance and desktop/JNI callers are deliberately untouched and require the
next coordinator slice. No native UI, Android/device, actual inference, memory
quality, performance, schema4 acceptance, release or whole M07/D07 completion is
claimed by this port.
