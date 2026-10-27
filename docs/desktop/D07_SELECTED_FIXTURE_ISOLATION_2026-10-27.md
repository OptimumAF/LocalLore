# Selected native fixture source isolation

2026-10-27. Supporting D07.01/D07.06 (#29), D09.02 native CI regression
(#31). FIRST oracle freeze: SOURCE ONLY, UNCOMPILED, UNRUN. This is not
native IPC, WebView, real-model, offline-runtime or full milestone acceptance.

## Observed failure and source boundary

Root's unchanged `79a50caa` full default-parallel workspace run finished with
native **236 passed, 10 failed, 9 ignored** (native binary 301.18 seconds;
whole command 529.380 seconds, exit 101). All ten failures were the existing
`inventory` `fs::read(...).unwrap()` in `selected/tests.rs`, Win32 error 33.
The original panic did not capture the failed pathname. This report does not
attribute the measured failure to a particular file. The exact first failed
test passed alone on unchanged source in 8.57 seconds test time (33.294 seconds
command time). The full serial control was still running at this source freeze.

The four owned Rust files are byte-identical between accepted `c6c21f28` and
`79a50caa`; this change is independent of the scene-recipe/dependency stack.
`selected/tests.rs::source` caches one producer directory for every Fixture.
Actual native Readers retain the exclusive `run.lock` capability via
`locallore-eval/.../comparison/desktop_api.rs::open_read_only` until closed.
Inventory recursively reads every ordinary file, including lock files. Sharing
one root allows one test's inventory to overlap another test's retained Reader.
This is a source-proven ownership conflict; it is not measured filename evidence.

`.github/workflows/desktop.yml` declares normal and `dev-harness` native Cargo
test commands with default parallelism, within the existing 45-minute job.
Historical serial qualification does not establish that those commands pass.
This fix does not serialize CI, increase budgets, skip files, ignore IO errors,
change production locks or weaken existing assertions and in-test races.

## Frozen regression and implementation contract

The new `concurrent_fixture_readers_own_distinct_sources_and_close_without_cross_fixture_lock_interference`
oracle uses two real native EvaluationManagers/WindowLeases, a real scripted
comparison producer and native Reader/evidence paths. It admits both Readers
from concurrent calls, retains both actual locks, exercises actual Player
history evidence, closes the first while the second remains admitted and
locked, then closes the second. It compares complete source inventories before
and after, and reads the never-opened template inventory while both Readers are
held. It checks the fixture paths differ and each actual source lock remains
exclusive. It does not fabricate native replies or suppress file-read failures.

The initial test refers to the planned `Fixture::source()` and `source_template`
helper names. Those absent names are compilation prerequisites, **not** an
executed behavioral RED. The actual original parallel failure remains the
runtime RED evidence. No new test execution is claimed by this source author.

Implementation must retain one immutable closed producer template, never pass
it to a Reader, and give each Fixture its own ordinary byte copy under its
existing unique temporary root. Copy the existing bounded inventory (depth 8,
4096 entries, 8 MiB/file, 64 MiB total), including empty directories and every
file byte. Reject links using the existing inventory checks; do not use shared
hardlinks or symlinks. Verify the completed copy against the template snapshot.
All native Reader inputs and source inventories in the four owned files must
use that Fixture's copy. Retain original Fixture close/retire/drain ordering.

The existing `literal_selected_review::copy_files` is the reviewed local pattern:
its closed producer roots are copied before a native Reader receives a path.
Its separate Protocol3 source construction is unchanged.

## Handoff and verification

Owned branch `fix/d07-selected-fixture-isolation`, based on accepted `c6c21f28`.
Exact scope: selected `tests.rs`, `transfer_close_review_tests.rs`,
`resume_completed_review_tests.rs`, `open_replacement_review_tests.rs`, and this
new report. First freeze precedes helper implementation. Claims:
[#29](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6450034118),
[#31](https://github.com/OptimumAF/LocalLore/issues/31#issuecomment-6450034649).

Author checks are source inspection and `git diff --check` only. No formatter,
compiler, test, model, native app, device, desktop control or protected resource
was used. Root owns formatting/review, the targeted regression, original serial
controls, then unchanged default-parallel workspace/native normal and
`dev-harness` commands. Exact commands, counts, timings, toolchain/environment
and failures must be recorded after execution; source review is not runtime
qualification. Keep original assertions, all internal race checks and budgets.

## Source implementation handoff

First oracle/contract commit: `4b6647a7`. The second source-only change adds
`copy_source_template`, a private `Fixture.source` path and its `source()`
getter. Every existing global-source Reader/input/inventory caller in the four
owned files now uses its own Fixture's copy; the existing assertion expressions
otherwise retain their original expectations. The first frozen regression is
unchanged. The global name is now `source_template`, used only for byte copying
and regression inventory, never native admission.

Copying follows the bounded inventory pattern already used by the Protocol3
review tests, with create-new ordinary output files instead of overwrite. Each
new Fixture copies under its existing fresh UUID root and verifies every copied
directory and file against the complete original inventory before opening a
Reader. `inventory` itself and Fixture's Drop lifecycle are unchanged. No
production, dependency, workflow, budget or other-owner file is modified.

Both source commits remain **UNCOMPILED / UNRUN**. `git diff --check` passes;
no formatting tool was run. Root's next runnable work is independent source
review, targeted execution, then the declared default-parallel native CI
commands (normal and `dev-harness`). Preserve serial controls as separate
evidence and rerun the complete parallel workspace cohort where appropriate.
Do not replace a failed parallel result with a serial pass.


## Root execution and qualification

Executed source is clean, unchanged `f8a2bf6439b1cef7caf2e2c19ceea36e4bc2c729`
(formatting only after33cb75e5). Base is accepted main `c6c21f28`;
the four affected native test files are byte-identical between that base and the
Core stack79a where the original parallel failure was observed. No shared
engine/Host/storage/runtime or UI production source changes in this fix.

The original failure stays attributed to79a: its parallel workspace run reports
native236 passed/10 failed/9 ignored, all ten at inventory `fs::read` Windows33
before intended assertions. The failed filename was not retained; source shows
the conflicting shared-source/exclusive-Reader pattern, but this is not a
measured run.lock pathname diagnosis. An unchanged79a isolated control passes
one previously failing test. The separate serial79a workspace result is not
substituted for parallel verification.

Root independently reviews the copy/helper/caller changes before running them.
The new two-Fixture test uses real native Readers concurrently on private byte
copies, checks both actual retained locks and read-only Player evidence, closes
one while the second remains valid/locked, then closes the second and checks
all file/directory inventories against the unchanged closed template. No file
or lock is skipped, no I/O error is swallowed and no deadline is enlarged.

Actual local Windows x64 results, one heavy process at a time:

| Check | Actual result / command duration |
| --- | --- |
| Normal frontend build prerequisite | PASS0.477s; local normal bundle, no server |
| Exact concurrent two-Reader regression, dev-harness | 1 passed;62.142s command (includes compile); all other tests filtered |
| Normal native tests, default parallel runner | 240 passed/0 failed/9 ignored;322.679s command,307.07s unit execution |
| Dev-harness native tests, default parallel runner | 247 unit+2 compile-contract=249 passed/0 failed/9 ignored;318.656s command |
| Normal all-target strict Clippy | PASS18.115s |
| Dev-harness all-target strict Clippy | PASS11.601s |
| Workspace Rust formatting check | PASS2.502s |

All process records show exactf8a source clean and unchanged throughout, exit0.
Normal/dev parallel commands use no test filter, `--test-threads` flag or test
serialization change. The inherited `RUST_TEST_THREADS` observation is unset.
The nine ignored cases remain eight explicitly opt-in installed-model/asset
qualifiers and one Windows symlink-privilege test; none is counted as executed.

Using the installed pinned toolchain/cache/dependencies from repository root:

```powershell
$env:CARGO_HOME = '<existing isolated exact-lock cache>'
$env:CARGO_NET_OFFLINE = 'true'
$env:CARGO_BUILD_JOBS = '1'
$env:CARGO_INCREMENTAL = '0'
$env:CARGO_PROFILE_DEV_DEBUG = '0'
$env:CARGO_PROFILE_TEST_DEBUG = '0'
$env:LIBSQLITE3_FLAGS = ''
$env:TEMP = '<existing owned task temporary directory>'
$env:TMP = $env:TEMP
& $taskNode apps/desktop/build.mjs
cargo +1.93.1 test --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness evaluation::selected::tests::concurrent_fixture_readers_own_distinct_sources_and_close_without_cross_fixture_lock_interference --locked --offline --jobs 1 --target-dir $ownedTarget -- --exact --test-threads=1
cargo +1.93.1 test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --jobs 1 --target-dir $ownedTarget
cargo +1.93.1 test --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --locked --offline --jobs 1 --target-dir $ownedTarget
cargo +1.93.1 clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --locked --offline --jobs 1 --target-dir $ownedTarget -- -D warnings
cargo +1.93.1 clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --features dev-harness --locked --offline --jobs 1 --target-dir $ownedTarget -- -D warnings
cargo +1.93.1 fmt --all -- --check
```

These reproduce the committed desktop workflow's normal/dev test and strict
Clippy choices locally, with explicit existing cache/target/offline/jobs1
controls. They are not hosted Actions results. Rust/Cargo1.93.1,
Node24.22.1, Windows NT10.0.26300 x64; unchanged locked dependency versions.
Private logs/process records retain the `d07-fixture-*` prefix and stay local,
outside Git. This is synthetic producer/native Rust service evidence, not a
model, Tauri IPC, WebView/desktop render, physical device, narrative quality,
whole-app offline or release result. No desktop control or model ran. The
owner's original needs-improvement quality assessment remains unchanged.

The shared fixture ownership conflict is addressed at the tested scope; the
original failures are not rewritten into passes. Full D07/D09 acceptance,
resource/performance qualification beyond these measured fixtures and other
independent epic gates remain open. CI settings and production Reader behavior
are unchanged.
