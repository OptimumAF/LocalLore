# Archive3 coordinator qualification — 2026-10-23

This is a partial qualification record for #12 M08.03/.04/.06 and #30
D08.01/.02/.07. Archive3 remains unmerged at this checkpoint. Shared Store
tests have executed; app interoperability, consumer closure and the remaining
compatibility gates below have not. No milestone acceptance, device support,
release approval or human review is inferred.

Root performed the executions reported here. The documentation agent read
source and completed logs, calculated hashes and checked its isolated Git
diff; it ran no build, test, formatter, provider, application or device.
Raw logs and synthetic databases stay local. Basenames and SHA256 identify
them below without publishing private absolute paths.

## Source and historical evidence

- Executed shared source: `9884a1727b17fb318eb79aa0dc301c2f6fe22684`
  on `qual/m08-archive3`, reconciled with accepted main `c6d0088`.
- Documentation checkpoint base: `8df48905cc12b2816234f684883bebb241a1bd0f`.
  Its only difference from the executed source is the two new, unexecuted
  consumer test files. It does not imply a new shared test execution.
- Shared implementation: `f0f7c5fd61ddad206902a5f6191b7a7194f17b20`;
  original source-only handoff: `0c640c50238c72ad3b5597ea18277fa34a1ec25c`.
  Reconciliation retained accepted main changes; do not replace main with the
  old producer tree. This report supplements the dated
  [source handoff](M08_ARCHIVE3_SOURCE_IMPLEMENTATION_2026-10-23.md) and
  [frozen oracles](M08_ARCHIVE3_FROZEN_ORACLES_2026-10-23.md), preserving their
  original source-only status rather than rewriting it as execution evidence.
- Original roundtrip test freeze `b85b917` and imported `ddc51a5` precede
  implementation. The later historical-asset fixture correction is imported
  as `b749479`. The original hostile file's frozen hash remains unchanged.
- Combined-budget test: `a64e3be`, formatted in `900a041`; actual Host Play2.5
  transfer test: `d115e54`, accessor/serialized-preview fixture correction
  `a8c7eeb`, formatted in `cdd6626`; pressure source: `0e2b7fc`, registered
  and formatted in `9884a17`. These source preparations are not executions.

Actual executed-file SHA256, also read at the documentation base:

| Path relative to `crates/locallore-storage` | SHA256 |
| --- | --- |
| `src/playable_archive.rs` | `355b57e88a5d3772a79f674a052f6b3750674591c0e68cc4731b764fcdcce363` |
| `src/turns.rs` | `a4c8f52a2a8dc7b5ea21f09808a689c7b2fa8fa6e2e0ee82d9603776214dea20` |
| `src/author_correction.rs` | `305500d839ef3e9f3fc264fe81b5e4982f84f5b997048c4f8bc8dc8c1d6e959b` |
| `tests/m08_archive3.rs` | `e43d5b96c8555ac4b34c39063060b8ad2028605bf5bb5a01056579e0bdefdf10` |
| `tests/m08_archive3_hostile.rs` | `643b16a93c406c37f88407e3a1f7f0cd9dfdb0b7c3f02b8fcb3d95c3be6fea67` |
| `src/archive3_pressure_tests.rs` | `8dcdb8a86717112198f70be526d4e86b9b4f04eea717e401c181c1886efea137` |

## Retained first failures

The original coordinator runs compiled but returned **0 passed / 7 failed**
and **0 passed / 6 failed**. Six roundtrip cases and all six hostile groups
stopped while constructing a genuine mixed fixture because preimplementation
export returned `Unsupported`. Those setup failures do not demonstrate that
each hostile mutation reached its semantic validator.

The seventh roundtrip failure was an incorrect fixture expectation:
`parent-retention-v1.json` is immutable archive1, not archive2. Its pinned
bytes/hash were already correct and were not replaced. The subsequent narrow
correction expects1, retains the byte/hash assertions and adds a real public
Store retirement fixture proving version2 selection. The hostile test source
was frozen after that metadata correction; its original actual RED still
failed at the mixed fixture setup. Neither failure is hidden or called a
successful negative test.

| Local log | Bytes | SHA256 | Actual result |
| --- | ---: | --- | --- |
| `archive3-original-red.log` | 4173 | `7bc3d982248dee1fb8f0b91377b092206ec9e11cd228b36f2557761c765bc9c9` | Compile1.38s; 0/7, tests0.53s |
| `archive3-hostile-original-red.log` | 3431 | `27ee11855f157491883e28ea8a406e7c19ec5a1b94998e2a826ba78576fdf51e` | Build0.21s; 0/6, tests0.33s |

## Completed shared checks

Root ran locked, offline, one-job Rust tests on Windows using the serialized
shared target directory. The log reports the unoptimized test profile. Root
confirms the reused, already verified Rust/Cargo1.93.1 installation, with no
upgrade or fresh `--version` invocation in this phase. Its completed-test
environment was `CARGO_BUILD_JOBS=1`, `CARGO_PROFILE_DEV_DEBUG=0`,
`CARGO_PROFILE_TEST_DEBUG=0`, `CARGO_INCREMENTAL=0`, `LIBSQLITE3_FLAGS=''`,
`TEMP`/`TMP=<task-root>/memory-controls-temp`, and
`<shared-target>=<task-root>/memory-jobs-target`. Manifests and lockfiles were
unchanged. Existing host qualification identifies Windows11 Pro10.0.26300 x64,
i7-12700K and approximately64GiB RAM; no fresh OS/hardware query was made for
these checks. Commands below use local placeholders rather than private paths
and are run from the repository root.

```text
cargo test --locked --offline --jobs 1 --target-dir <shared-target> -p locallore-storage --test m08_archive3 --test m08_archive3_hostile -- --test-threads=1
cargo test --locked --offline --jobs 1 --target-dir <shared-target> -p locallore-storage --lib archive3_pressure_tests:: -- --nocapture --test-threads=1
```

| Local log | Bytes | SHA256 | Actual result at `9884a17` |
| --- | ---: | --- | --- |
| `archive3-corrected-original13-first.log` | 2067 | `867d090f97d38a53484f0aff81f4725786a77a3de96081ff427ba6d97b81c236` | Compile10.89s; roundtrip7 passed in1.91s; hostile6 passed in3.84s; no failures/ignores/filters |
| `archive3-pressure-first.log` | 10437 | `3cb6061e1ad533675da2d5de7d4ee6d0dcc0d9bc027a626f4172b607c349757e` | Compile3.99s; 3 passed,0 failed,0 ignored,26 filtered,16.08s |

These are two focused commands, not an unfiltered Store/workspace pass. The
13 tests cover mixed canonical roundtrip/recovery, original source identities,
private observation bindings, retirement, conflict/no overwrite, escaped
author fields, legacy byte continuity and the six frozen hostile groups.
Checksums do not authenticate an author's intent; strict replay and closed
record/lineage validation remain necessary.

The three pressure cases use actual accepted author+typed-play history and
the actual Store connection. Failure assertions compare complete logical
raw-table state, canonical fingerprints and source-story absence, including
nonempty derived-job state and `sqlite_sequence`, then check cold reopen.
This is logical rollback evidence, not bitwise SQLite-file identity.

- **Busy:** a separate connection holds `BEGIN IMMEDIATE`; import returns
  `ArchiveError::Busy`. After release, restoring the test connection's timeout
  and reopening, a freshly validated token imports successfully and preserves
  the destination's existing story.
- **Full:** measured target26 pages ×4096 bytes, freelist0, scoped quota106496
  bytes; incoming native canonical/index text872923 bytes, archive668749 bytes.
  Both import attempts return actual `ArchiveError::Full` at observed callback
  poll1. Exact failing SQL is not observed; this does not establish failure
  after author insertion. Only that connection's prior `max_page_count` is
  restored to relieve capacity, followed by exact retry/cold-state checks.
  No deletion, physical ENOSPC, power loss or global SQLite change is claimed.
- **Cancellation/panic:** the successful fixed mixed import exposes33 callback
  polls. All33 cancellation positions and all33 panicking positions execute:
  **66 targets**, including the final precommit poll33. Each returns the
  expected closed cancellation, leaves complete logical state unchanged across
  reopen and admits a fresh exact retry. The emitted panic messages are the
  intentionally caught callback cases; the final test result is passing.
  This is exhaustive for this observed fixture path, not every possible SQL
  schedule or an operating-system process-kill experiment.

## Consumer packet: frozen, not executed

Original producer `145086afe93f92cc8c2b4aef97e67d98ef37af38` is imported as
`8df48905cc12b2816234f684883bebb241a1bd0f`:

| New path | Frozen coverage | Status |
| --- | --- | --- |
| `apps/desktop/check-archive-v3.mjs` | 82 synthetic decoder/controller/headless-panel source cases | UNRUN |
| `apps/android/app/src/androidTest/java/org/locallore/app/ArchiveV3WireTest.kt` | 9 actual Android decoder/JSONObject instrumented test methods | UNCOMPILED / UNRUN |

The available frontend executable is the previously verified Node24.22.1 with
the existing D09 dependency junction; it has not executed this Archive3 checker
at this checkpoint. The desktop fixtures are synthetic transport shapes, not newly generated
native responses. Headless React checks are not native WebView execution.
Android's host-JVM `JSONObject` stub cannot qualify this decoder: the tests
are deliberately in `androidTest`, using the actual platform implementation.
Instrumented compilation alone will not establish runtime behavior. No
Android device/emulator/ADB execution is authorized for this cohort.

The public archive2 constant and catalogs listing `[1,2]` are not a reliable
exposure fence: shared export/import can already produce/accept genuine3 on
this future stack, while current app decoders reject3. Root must close the
native preview/completion DTOs, strict TS/Kotlin version dispatch, omitted
empty versus nonempty retirement fields, canonical-record count labels,
consent/token/recovery and supported-version advertisement before accepting
Domain2 app transfer. Counts include author records; calling all of them
gameplay turns would misdescribe the archive.

## Pending gates and next runnable work

All items below remain pending at this checkpoint; commands are reproduction
instructions, not results. Use Root's serialized target/TEMP environment.

```text
cargo test --locked --offline --jobs 1 --target-dir <shared-target> -p locallore-workspace --test m08_archive3_play25 -- --nocapture --test-threads=1
cargo test --locked --offline --jobs 1 --target-dir <shared-target> -p locallore-storage --test m08_archive3_combined_budget actual_records_cross_only_combined_response_and_native_index_archive_budget -- --ignored --exact --nocapture --test-threads=1
cargo test --locked --offline --jobs 1 --target-dir <shared-target> -p locallore-storage --test playable_archive --test branch_retention_archive --test archive_interruption -- --test-threads=1
```

The Host Play2.5 test must establish generated-current-record metadata,
per-event corrected observations and durable cold transfer through the real
shared port; earlier typed-history results do not substitute for it. The
ignored expensive boundary case must measure the last legal <=16MiB combined
canonical-response/native-index total and the next accepted crossing record,
with every other cap independently legal; no exact-boundary result is claimed
before execution. Existing Full/checkpoint/interruption and broader Rust,
Workspace/native compatibility, formatting and strict lint checks remain
Root-owned and pending on the final integrated source.

From `apps/desktop`, Root's consumer command is `node check-archive-v3.mjs`.
From `apps/android`, compilation-only is
`./gradlew.bat --offline :app:compileDebugAndroidTestKotlin`. Preserve the first
actual fixture/compile/behavior failures before any narrow correction, and
record exact source and results for each rerun. Actual Android instrumented
runtime, native picker/IPC transfer, desktop↔Android roundtrip, app-owned render
inspection, physical-phone qualification and owner acceptance are not supplied
by this report. D07 model/timing cohorts are separate evidence and are not
relabeled as Archive3 qualification.

Documentation ownership remains open under
[#12 claim6381144573](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6381144573)
and [#30 claim6381144716](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6381144716)
for later coordinator results. Next runnable task is Root's actual Host Play2.5
transfer and combined-budget execution, followed by consumer RED/GREEN and
the compatibility closure; no milestone checkbox changes at this checkpoint.
