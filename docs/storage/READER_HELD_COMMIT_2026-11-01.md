# Reader-held final COMMIT regression

Date: 2026-11-01. Scope: M10.02, supporting M04.03/M04.04 in
[#14](https://github.com/OptimumAF/LocalLore/issues/14) and
[#8](https://github.com/OptimumAF/LocalLore/issues/8). This is host regression
coverage of existing behavior, not a newly demonstrated production defect.
Full milestone acceptance remains separate.

## Boundary and oracle

The existing writer-contention test refuses another writer at transaction
admission. This case holds a real SQLite reader through final COMMIT instead.
It uses the ordinary durable Store, verifies DELETE journal mode, persists a
Give+Wait draft, and performs an actual SELECT in a separate read-only deferred
transaction. BEGIN alone would not establish the required reader lock.

The unmodified commit path must return `Storage(Busy)`. A thread-local observer
inside the existing **test-only** checkpoint function records boundary 5, after
all event, projection, response/status and branch-head writes returned, before
`tx.commit()`. Boundary 6 is not reached. This distinguishes final COMMIT
contention from failed writer admission or an earlier cache-spill write. No
injected error, new production fault control, SQL endpoint, dependency, schema
change, or alternate gameplay authority is added.

After releasing the reader, strict resume must report no projection rebuild and
identical canonical bytes, revision zero, the player's potion, original story
time and the original draft without a response. The exact retry must commit two
events once. Repeated retry and reopening must return the same receipt and
canonical bytes, with the potion owned by Mira, time advanced once and no draft.
The private atomic-turn fixture helper now retains its owned synthetic directory
if an assertion panics; normal successful cleanup is unchanged.

## Execution

The coordinator reused the clean inactive physical D: storage-review checkout,
preserved its previous `review/m04-storage` branch at `73f0f335`, snapshotted its
tracked tree, and verified the four pre-existing ignored probe/build files
unchanged. The new branch starts at accepted main `c09380d6` and changes only
test code and this report. Frozen Android builds, pending runner inputs and
emulator storage are untouched.

Use the existing pinned Rust 1.93.1 toolchain and Cargo lockfile. On Windows,
set process-local TEMP/TMP/TMPDIR and build/cache paths to physical D: locations
before these commands. This run used the existing D: Cargo cache in offline
mode, a dedicated target with a declared 6 GiB ceiling, and at most 32 MiB of
retained logs/source preservation outside that target. No dependencies were
introduced or downloaded.

```powershell
cargo +1.93.1 test --locked --offline -p locallore-storage --lib turns::tests::reader_held_commit_rolls_back_and_exact_retry_commits_once -- --exact --nocapture
cargo +1.93.1 test --locked --offline -p locallore-storage --features development-fixtures
cargo +1.93.1 clippy --locked --offline -p locallore-storage --all-targets --features development-fixtures -- -D warnings
cargo +1.93.1 fmt -p locallore-storage -- --check
```

The initial compilation failed because the fixture requested a SQLite integer
as unsupported `u64`; correcting it to `i64` preserves the oracle. No test ran
in that attempt, and it is not a product-failure baseline. The corrected exact
targeted command passes **1 test, 0 failures, 0 ignored**, in **0.40 s**. The
original failed log is retained. The full storage command then passes **244
tests, 0 failures, 6 ignored**, including the new test and the existing
thousand-event replay, process-interruption and actual SQLite pressure cases.
The 31 result summaries include one empty doc-test cohort. Six existing ignored
entries remain unchanged: a special compiled page profile, two parent-owned IPC
worker entry points, the explicit expensive combined archive budget case, and
two Windows symlink-privilege cases. They are not counted as passes or newly
qualified here. Clippy with warnings denied and the formatting check both exit
zero. No further test rerun was needed after those checks.

The retained suite log has SHA-256
`2a4ea5e0882df8d7aed9c105f2eff0fbe3d99e242bb697dc22350db37b5b2f34`.
Raw host logs/source-preservation records stay under
`D:/Dev/Experiments/LocalLore/2026-11-01-reader-held-commit-v1` and are not
uploaded as private diagnostics. The public reproducible regression is
`turns::tests::reader_held_commit_rolls_back_and_exact_retry_commits_once`.

Independent source review found no concrete blocker. The reviewer did not run
tests; coordinator execution and source review are separate evidence.

## Limits

This checks one original synthetic turn against the bundled SQLite library on a
Windows host. It does not establish Android/phone behavior, another journal
profile, model quality/performance, partition ENOSPC, power-loss durability or
full M04/M10 acceptance. No emulator, ADB, phone, model, system-setting, shared
storage-ledger, retirement or merge operation is part of this packet.
