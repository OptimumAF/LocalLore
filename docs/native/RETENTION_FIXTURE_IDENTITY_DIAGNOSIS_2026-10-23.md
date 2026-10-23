# Native retention fixture identity diagnosis, 2026-10-23

Refs #7 M03.05 host-test reliability and #85 retained-parent qualification.
Coordinator-delegated reviewer `/root/app_storage_review`; claims
[#7 6371054675](https://github.com/OptimumAF/LocalLore/issues/7#issuecomment-6371054675)
and [#85 6371055090](https://github.com/OptimumAF/LocalLore/pull/85#issuecomment-6371055090).
Only `crates/locallore-android/tests/branch_retention.rs` temporary-directory
allocation, its original allocator regression, and this NEW report are changed.
No production behavior, dependency, original semantic assertion, deadline,
checker, Android app/device or root M05 source ownership is changed.

## Original failure and attribution

Coordinator source `8d7fac239999c1d648b3f44ec16612603186d041` full all-feature
workspace execution failed in
`accepted_retirement_fences_only_target_across_owners_and_retained_child_ready_can_commit`
at the fixture's `create_dir` (line27), OS183 / AlreadyExists. The other two
retention tests passed. A read-only copy of the complete original log is
retained in the task-local diagnosis directory with the digest below.

All three test functions construct `Fixture::new()` and can run concurrently.
The original name is `locallore-native-retention-{pid}-{SystemTime.as_nanos()}`.
A nanosecond representation is not a unique allocation identity; simultaneous
reads can return the same clock value. `create_dir` correctly refuses the
collision, but the fixture immediately unwraps the refusal.

The original test Git blob is identical at accepted `3485aa4` and failed
integration `8d7fac2`: `3a9de41fe99d16f938a79f03a20331f308bb82a5`.
This is an existing test allocator flaw, not an M05 production regression.
The original log contains no exact selected path or process ID, so it cannot
establish which precise original pair collided or completely exclude a leftover
path in that particular incident. The independent evidence below demonstrates
that leftover paths are unnecessary to produce the failure.

## Isolated evidence and minimal correction

A task-local Rust standard-library probe used a freshly created own D directory,
the exact original PID+live-clock naming expression, and32 batches of32 parallel
allocations. Sampling and allocation barriers allowed concurrent timestamps;
only directories successfully created in that batch were removed. The first
run produced11 actual AlreadyExists failures; the second produced10. No prior
process directories or existing filesystem namespace were adopted. Serial
100,000 clock samples had zero repeats, illustrating why a serial timestamp
sample would miss this concurrent defect.

The first diagnostic incorrectly asserted that serial samples must duplicate
as well, so its overall run failed after the useful parallel collisions. That
log is retained. The second diagnostic corrected only that unsupported serial
assertion and passed the parallel-create assertion. These are private diagnostic
artifacts, not replacements for the actual fixture regression.

Frozen RED commit `2aa81b6741dd1f44f5cf898397cfe754aca620a4` extracts the
unchanged allocator into this same integration-test file; `Fixture::new()`
uses it. A NEW eight-thread regression passes one captured clock value to that
actual allocator. It collects results and removes only its successfully created
empty directories before asserting. The test FAILED with seven AlreadyExists
errors. It does not require lucky scheduling or a clock-resolution assumption.

Correction `f157a5624733734df1eadd1afdc8232af93bba30` adds one process-local
`AtomicU64` suffix, using relaxed ordering solely to allocate distinct IDs. This
matches the neighboring branch-catalog fixture's existing pattern. PID and clock
remain in the name. The actual allocator still uses exclusive `create_dir`;
it never retries by adopting/deleting an existing path, and semantic tests
remain parallel. The same regression now passes. Original fixture initialization
after directory allocation and all three original semantic test bodies compare
byte-for-byte equal after newline normalization. No safety assertion or limit
was removed. A first format check identified only the new regression's assertion
wrapping; rustfmt corrected it before the RED source commit.

## Actual checks and source binding

Own isolated `source-retention-fixture` / `fix/native-retention-fixture-identity`,
base8d7fac2, own `retention-fixture-target` and fresh D TEMP/TMP. Windows
10.0.26300; Rust/Cargo1.93.1. `CARGO_PROFILE_DEV_DEBUG=0`,
`CARGO_INCREMENTAL=0`; locked/offline throughout.

```text
cargo test --locked --offline -p locallore-android --test branch_retention \
  --target-dir <own-D-target> \
  concurrent_fixtures_with_the_same_clock_value_have_distinct_directories -- --exact
RED: 0 passed / 1 failed / 3 filtered; seven AlreadyExists errors

cargo test --locked --offline -p locallore-android --test branch_retention \
  --target-dir <own-D-target>
4 PASS, including all three original semantic tests, default parallel runner

cargo test --locked --offline -p locallore-android --all-features \
  --test branch_retention --target-dir <own-D-target>
4 PASS, default parallel runner

cargo clippy --locked --offline -p locallore-android --all-targets \
  --target-dir <own-D-target> -- -D warnings
PASS
cargo clippy --locked --offline -p locallore-android --all-targets \
  --all-features --target-dir <own-D-target> -- -D warnings
PASS
cargo fmt --all -- --check
PASS
git diff --check
PASS
```

Final test checkout SHA256:
`780d7f49df22136e76264cdb9127999b3e40b1ec3d7875a2548ba3080696fde6`.

| Retained private task-local log | SHA256 |
| --- | --- |
| complete original root workspace failure | `9b074043cef2fc531ec655b8f3182bacf6e1bb84be23fa77f45940430ada7e62` |
| first clock diagnostic, serial assertion error retained | `cf960e126b3face3fd2ca73f9a7c5d64d10b245e5e1740efc3c98f8a7f33f13f` |
| second parallel clock diagnostic | `df9757966d6c190287a157b64962077a9c35a5c294e5b5e00bf0858a767d6dcf` |
| actual allocator RED regression | `1ca887e74b3fb4b158388b00b4ae9fa41f1cd3ffc0d3bb54f5d72ebefeb473d5` |
| default final4 | `7ce98b93199f7920522e48e0ffb14c18453bc0c8af4f8d1f0150e511cd1f2169` |
| all-feature final4 | `1b36c078d5085313084cf2db43f0fe5246b3eaade55107a2230de7da742dc93c` |
| strict default Clippy | `b82ebee5c84afb853225f4a15b3a157b8f416ccb5ed09a013e8a7f4ee5e334d4` |
| strict all-feature Clippy | `29f239fef970a7b405a56be9e4e4befe936873d05f0310bcddfb2c29e04ac2ef` |

This is a bounded test-fixture identity correction, not a product retention,
process-ownership or filesystem-security change. Coordinator owns the complete
combined workspace rerun and publication. No broad cleanup, devices, models,
workers/assets, desktop/CUA, protected resources, settings, merge or milestone
acceptance were performed. Existing directories are always refused; the counter
solves current-process same-clock collisions rather than granting authority over
leftovers or another process's resources.
