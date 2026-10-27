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
