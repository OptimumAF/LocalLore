# Combined portable Rust acceptance -- 2026-11-02

Refs #14 (M10.01/M10.02); supporting #9 (M05.01/M05.03) and #12 (M08.06).
This records an actual combined four-crate run, beyond the earlier focused
isolated-package checks. It adds no production behavior or new dependency.
No integration failure or fix was needed; full milestone acceptance remains open.

## Exact candidate

Actual tested base main: `d3862614cb6654305d88d44901eda36b83f2a4e8`.
Tested content tree: `fdc9797ea80b516a970909fb47ebb7f433802999`.

The [machine-readable inputs](COMBINED_PORTABLE_INPUTS_2026-11-02.json) pin:

| Constituent PR | Exact head |
|---|---|
| #368 | `327a729080c1717027e9900fb2a2c7e27d64291b` |
| #370 | `211d64715f56395f156d1096c72b56e890460b23` |
| #371 | `4d119d3953ef9c37f1683c8a9c1fd7ab4c43a55d` |
| #372 | `d623ed0200d23c231c8f3b3b9efc3176ce5f6e59` |

All2,568 main files remain byte-identical. Exactly11 disjoint additions from
those heads add seven test files/eight test methods and four unchanged historical
reports:2,579 files/36,446,507bytes. No baseline file is modified or deleted.
All constituent source/test/report bytes are preserved, including their original
source attribution, limitations, warnings and dated results. This combined PR
contains those same additions and two new verification artifacts; the latter
are not executable inputs to the tested source tree. The original four PRs
remain open/unmerged; this does not silently supersede, close or accept them.
No Git merge, cherry-pick or upstream merge operation was performed.

Publication base main is `027ddbaf298cd05ebdcdf65d716962e783bcad31`.
External PRs #369 and #373 landed after the checks finished. Two exact-main
publication preflights correctly refused before any branch/commit/push; both
failed preflights and superseded prepared artifacts remain preserved. The
coordinator performed neither external merge. Compared with the actual tested
base, they change exactly ten paths: six `docs/desktop/D04_*` documents and
four `native/llama-worker/*.mjs` paths. The machine-readable inputs pin every
path, mode, old/new blob, size and digest. All ten upstream changes are preserved
verbatim in publication ancestry, outside this PR's additions.

Independent source-closure audits, including an extension for the second drift,
found all 460 tracked Rust source files, all 255 selected-crate files, Cargo
manifests/lock, toolchain/config and fixture inputs unchanged. The 283 literal
include/module references remain identical; the unchanged desktop
host-v1.schema.json fixture is included in that audit. Directory readers and
subprocesses use fixed fixtures, owned synthetic roots or self-workers and do
not discover/execute the changed JavaScript. Rust formatting inputs are also
identical. Actual old-source results therefore apply to the unchanged Rust
inputs without another redundant run. The ten upstream JS/docs paths were not
executed or qualified by this cohort. Both tested and publication trees,
ten-path blob delta and review digests are pinned in the inputs manifest;
further relevant drift requires new review or checks.

The operator checkout stayed clean/frozen at
`8924278ce1c877e6d67c90c15a35fb23ca7198dc`, normal index unchanged. The coordinator
created an exclusive physical D: Git-content INPUT SNAPSHOT from raw Git blob
bytes, with no .git directory or managed worktree. Independent agents used
separate existing read-only worktrees for audit. Every snapshot file's Git blob,
SHA256, mode, size and origin was checked against actual main/PR objects before
execution; all2,579 source files, roster and Cargo.lock stayed unchanged afterward.
This run used that real repository-shaped Cargo workspace, not the earlier
external43-package proof manifest.

## Actual commands and scope

Pinned Rust1.93.1, host x86_64-pc-windows-msvc. From the physical candidate root:

```powershell
cargo +1.93.1 fmt --all -- --check
cargo +1.93.1 clippy --workspace --exclude locallore-desktop-spike --all-targets --locked --offline -- -D warnings
cargo +1.93.1 test --workspace --exclude locallore-desktop-spike --locked --offline -- --test-threads=1
```

All three commands actually completed with exit0 on their first run; no
assertion change, retry, new skip or source fix was needed. The test command
completed in557.25s; this is verification time, not inference/device performance.
Metadata and feature-tree commands also ran offline/locked. Exact closed logs,
command/environment records and structured results are retained privately.

Compiled/tested workspace packages: `locallore`, `locallore-storage`,
`locallore-workspace`, `locallore-android`. Defaults are used, without
--all-features. Workspace intrinsically enables Core's host feature; actual
feature-tree output confirms host on Core and no optional root features on the
other three. The original415-package workspace lock is byte-identical to base.
That does not mean all415 packages compiled or that Desktop was qualified.

fmt--all checks all workspace Rust source, including Desktop source read-only.
Desktop compilation/tests are explicitly excluded. Windows host tests of the
Rust Android bridge do not execute JNI, Android, ARM64 or an emulator. Production
runtime/model crates excluded from the workspace are not qualified here.

This is the Rust portion of scripts/check.py's host checks, not the complete
host gate. Python suites, standalone native-linker checks, fixture generation,
frontend, Gradle/JVM, APK audits and on-device runs were not rerun in this packet.

## Closed results

| Result category | Passed | Failed | Ignored |
|---|---:|---:|---:|
| Unit, integration and test-enabled examples,157 target harnesses | 1,134 | 0 | 12 |
| Compile-fail doctests,4 crate groups | 10 | 0 | 0 |
| Total | 1,144 | 0 | 12 |

No tests were filtered by a --skip/--exact selection; existing ignored states
remain unchanged. Counts are actual top-level Rust summaries with no nested
child-summary double counting. Doctests are compile-fail checks and are reported
separately, rather than implying runtime coverage.

All eight new methods execute exactly once and pass:

- `locallore::m10_query2_observation_chain::remembered_and_per_event_values_survive_two_corrections_without_same_revision_branch_bleed`.
- `locallore::m10_staged_epistemic_rejection::rejected_epistemic_and_mechanical_prefix_does_not_reserve_turn_or_event_sources`.
- `locallore-storage::m10_durable_epistemic_rollback::final_commit_busy_rolls_back_composed_knowledge_and_mechanics_then_exact_retry_spends_once`.
- `locallore-storage::m10_durable_observation_chain::sqlite_reopens_preserve_query2_observation_history_and_same_head_branch_isolation`.
- `locallore-storage::m08_archive_epistemic_journey::archive3_preserves_query2_pages_and_sources_then_only_imported_future_observes_c`.
- `locallore-storage::m08_archive_observation_authority::genuine_wrapper_from_existing_same_value_sibling_cannot_authorize_a_recipient_observation`.
- `locallore-workspace::m08_imported_generation::imported_cold_host_generates_new_observation_from_b_to_c_only_after_explicit_commit`.
- `locallore-workspace::m08_imported_generation::imported_cold_host_cancel_discards_late_valid_narration_and_never_regenerates_terminal_turn`.

The actual `ten_thousand_seeded_attempts_preserve_conservation_bounds_and_replay`
method also executes and passes. Its fixed seed0x1a172026 runs10,000 generated
singleton transition attempts, including rejection checks, inventory/energy/
ability bounds and final provider-free replay equality. That is one deterministic
trajectory and one method, not10,000 independent seeds/tests, exhaustive behavior
or per-step observer-context proof. The eight composed knowledge/SQLite/archive/
Host oracles complement that bounded property trajectory.

The cases retain their precise coverage limits: the small DELETE-journal commit
edge is inferred from source/locking rather than a statement trace; the imported
Host cancellation checks integrated rejection and synthetic Script/logical Host
ownership rather than one isolated guard or native backend drainage; hostile
archive pre-write validation is distinct from mid-write rollback. Canonical-state
checksums are not original-author authentication and are not described as valid
states for impossible histories. See the unchanged constituent reports.

## Environment, preservation and reproduction

All commands, source, output, temporary settings and project cache are physical
D:. Child environments clear inherited LOCALLORE_* capture/worker flags,
B34_LEGACY_CAPTURE_PATH, LIBSQLITE3_FLAGS and CARGO_BUILD_TARGET before running
ordinary tests; none happened to be present in this captured parent environment.
Tests' own subprocesses still set their exact owned worker variables. Parent/global
settings are not changed. TEMP/TMP/TMPDIR select the owned synthetic output root;
Cargo uses the existing D: cache and retained target, jobs2, dev/test debug0,
CARGO_INCREMENTAL=0 and RUSTUP_AUTO_INSTALL=0. The command/data manifest records
these choices and raw lock/test/source identities separately.

Preflight reviewed241 Rust files,12 source ignore declarations and10 pure
compile-fail doctests. No additional exclusion was required. Test subprocesses
are owned child harnesses, not process-name inventories or real SDK/model jobs.
One Windows example creates a junction only within its fresh synthetic fixture.
Existing tests keep their original owned-fixture cleanup; new-case captures,
source, originals and all packet evidence remain retained. No manual/shared-data
cleanup or target deletion is performed.

Private output/recovery basename: `2026-11-02-combined-portable-v1`.
Declared budgets: candidate source128MiB, build increment3GiB above the retained
1,998,055,072-byte target baseline, controls64MiB, synthetic outputs1GiB,
recovery2GiB. The entire tested source snapshot and all closed evidence have
verified recovery copies. Build cache payload is retained at its existing target
and is not represented as a copied evidence payload. No private stories, model
weights, credentials or raw device diagnostics are published.

To reproduce the actual tested full source tree, reconstruct the original
tested base plus the eleven pinned additions and use the Cargo commands above
with cached pinned dependencies and an equivalent clean fixture environment.
The final PR adds thirteen paths to its newer publication base: the same eleven
additions, this report and the input manifest. Compared with the actual tested
content tree, it additionally preserves the ten upstream JS/docs changes
described above. These ten paths and two evidence artifacts do not change the
selected Rust inputs, but the final entire tree is not claimed to have executed.
Exact source/data identity can be reconstructed without merging the original PRs.

## Remaining gates

This is host portable Rust acceptance evidence, not full M05/M08/M10 acceptance,
all-platform/privacy assurance, app quality, Android UI/JNI lifecycle, real-model
quality/performance, native/GPU drainage, physical power-loss or release readiness.
Owner review/acceptance is separate from a passing finite test cohort.

The frozen operator, unrelated emulator, system settings, original PRs and
shared emulator ledger remain preserved. No emulator/phone/model/SDK operation,
image deletion, ledger write or merge occurs. Knowledge Android0/4 still needs
its exact retirement/capacity disposition and separate fresh-boot approval and
admission; real-backend/reference-phone and M10.05 qualification are unadvanced.
