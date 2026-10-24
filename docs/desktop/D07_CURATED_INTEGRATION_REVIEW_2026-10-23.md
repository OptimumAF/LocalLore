# Curated desktop integration boundary review — 2026-10-23

Refs #29, partial D07.01–.06; #28, partial D06.03/.06/.07. In review;
no milestone, model quality or distribution acceptance. Claims #29 6371783830
and 6371915936, #28 6372052108. Separate reviewer worktree
`source-curated-integration-review`, branch `review/d07-curated-integration`.

Reviewed integration `3a0aae28e2409834e248ebe895d56e8808aee09b`, based on
accepted prompt-2.3 `a13b80b`; new adapter/UI packet plus root-workspace lock
reconciliation. Reviewed repair `82c0297af4ed14cc01eb406e6bf239884753d3fe`,
exact cherry-pick `a37e18e` in this worktree. Reviewer owns only this report and
two new test files. The coordinator owns all implementation and test wiring.
The reviewer previously authored the underlying CLI runner, not the new
desktop/read-only adapter or UI; this is not independent approval of the
unchanged runner or the complete evaluation stack.

## Concrete finding and correction

**P2: Destroyed retirement could lose evaluation cancellation when presentation
state was contended or poisoned.** Frozen `evaluation.rs:841` used
`if let Ok(...) = state.try_lock()` as the only cancellation path. Failure to
acquire that mutex silently skipped `job.cancel.cancel()`. `drain` joined the
worker but did not independently signal it. The new curated worker checks its
window lease before entering the runner (`curated.rs:439`), then passes only
the cancellation token through the bounded native/scripted invocation
(`curated.rs:454/471`). Therefore the missed token can delay closing/draining
active curated work until its invocation/deadlines finish. This is an ownership
and cancellation defect; no canonical live-story mutation or data leak was
demonstrated.

New reviewer tests in `evaluation/retirement_review.rs` call actual
`manager.catalog`/`manager.start`, capture the real admitted job token and use
the existing actual-worker pre-publication barrier. They do not construct an
alternate Job/retirement implementation or load assets. The barrier prevents
completion racing the contention/poison assertion. They invalidate the real
window lease, call the actual retirement path, release the worker and drain it
before the final cancellation assertion.

- Initial representation-only test commit `54b0285` is preserved but was not
  used as acceptance evidence. Refinement `f6d2c0f` uses actual admission; the
  test bytes remain unchanged through the repair.
- Coordinator execution before repair: **0 passed / 2 failed / 0 ignored**,
  exit 101, both missing cancellation assertions. Reviewer read and rehashed
  `core-rust/curated-retirement-red.log`:
  `2214cb4336474bb5fc5d2c2c29cc4a8b6a3d252d7a9c54693015a35787e76c65`.
  This RED execution is the coordinator's, not the reviewer's.
- Repair `82c0297` adds a short independent cancellation slot. Both admission
  paths register the actual token and immediately recheck `lease.valid(epoch)`.
  If invalidation preceded registration, that recheck cancels the new token;
  otherwise retirement sees it. Terminal/spawn-failure cleanup clears only the
  exact `(epoch, operation)` pair.
- Reviewer execution after repair: **2 passed / 0 failed / 0 ignored** using
  the same actual-admission tests, own fresh native unit target. No GUI,
  inference process, model assets or native inference execution occurred.

The source lock audit found no remaining blocker in this repair. Registry
guards cover only replacement, exact-match clearing and atomic cancellation;
`Cancellation::cancel` is an atomic store. They are released before acquiring
presentation/lease/worker locks, doing I/O or joining. Admission can hold
lease/state then briefly register; retirement has no held reverse
registry-to-state edge. Cleanup recovers registry poison without authorizing
ordinary presentation operations through poisoned state. Old-operation cleanup
cannot erase the newer token. Existing worker-slot draining releases its locks
before joining. The coordinator's added late-registration/old-cleanup test
passed in its focused suite; that additional test was not independently rerun
here after resource failures described below.

## Actual historical read-only compatibility

New public-API integration test `curated_integration_review.rs` was executed
explicitly against a task-owned byte-exact copy of a real earlier **scripted**
curated WebView run (`29204f24`, run `0090e0d0`). It contains **102 files /
1,163,163 bytes**, six actual SQLite databases with header `user_version=2`,
and recorded `locallore-play-v2.2`/storage-schema-2 source binding. No model
assets or the live story database were opened. Original retained files were
read only; test operations used the new copy.

Current prompt-2.3/schema-3 code produced **1 passed / 0 failed / 0 ignored**
when this normally explicit-fixture/ignored test was selected:

- Historical `inspect` returns six completed cases and
  `resume_compatible=false`, with generation-this-view false.
- **24/24** historical turn evidence requests succeed, zero unavailable.
  Each revision/canonical fingerprint matches its validated checkpoint;
  actual receipt presence matches committed versus rejected/noncommitted turns.
- Player evidence has no receipt, raw role outputs or role metrics.
- Attempting current-source execution resume is refused.
- Every copied file's bytes and the complete file inventory remain identical,
  including all six schema-2 databases; no backup, migration or admission file
  is created. Store's version-specific read-only verification and historical
  retention guard support this exact case. This does not promise future-schema
  or arbitrary historical corruption compatibility.

Reviewer also ran the three existing `desktop_api::tests`: **3 passed / 0
failed / 0 ignored**. They exercise source mismatch/view-only behavior,
conservative unknown-work charging, immutable evidence, observer filtering and
all original branch/revision/actual-receipt bindings. Focused strict Clippy for
the new historical integration test passed; both new files' rustfmt checks and
Git diff checks passed.

## Other reviewed boundaries

No further concrete blocker identified in the finite source review:

- Shared view reuses the actual checkpoint validator and accepts only the
  compiled corpus/known case/turn, profile, scope, revision and bound raw hashes.
  Evidence loads a read-only Store, validates replay and canonical fingerprint,
  and calls the existing inspection query. Omniscient receipt/raw/metrics are
  separate from filtered player/character pages. No live Host or generation
  knowledge grant is supplied.
- Native actions/fields are closed and bounded, with no renderer file path,
  executable, provider or fixture-content option. UUID metadata and source
  binding are synced before worker admission; original-request lookup recovers
  the same run. Completed cache inspection does not reserve a model or invoke
  inference. Source-incompatible resume is refused rather than rewriting data.
- ModelManager reservation shares its existing mutex with import/load/unload
  admission and retains an RAII owner through runner completion. Asset paths
  remain native-owned; model/worker verification reuses the accepted runtime.
  Missing model assets are not replaced by scripted inference.
- Controller epoch/evidence sequence fences clear context and reject late
  selected-run/case/turn replies. The decoder bounds status/report/output and
  checks run/token/binding/scope/revision/observer/grant identity. React displays
  retained output as inert text. Reports distinguish fake/native, rejected
  actions, absent receipts, unavailable historical context/schema/staged plans,
  finite checks and human-quality false. This is source review, not visual QA.
- New dev journeys remain application-owned, fixed-action and build-gated.
  No desktop input/capture, arbitrary code/file/shell endpoint or debugging
  server was introduced in the reviewed packet.
- Root keeps the retired desktop lock absent, transfers the same single
  eval-to-local-runtime dependency edge to the consumed root lock, and updates
  the new harness inventory literal. No dependency version/checksum change
  was present in that reconciliation.

## Commands, execution attribution and limits

Reviewer used Windows x64, Rust/Cargo 1.93.1, Node 24.22.1 for normal frontend
compile setup, debug info 0, incremental off, locked/offline Cargo, own D:
targets/TEMP. Normal `build.mjs` supplied Tauri unit-test frontend assets;
generated tracked source stayed unchanged. This is not GUI execution.

```powershell
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --test curated_integration_review -- --ignored --nocapture
cargo clippy --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --test curated_integration_review -- -D warnings
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --lib local_lane::desktop_api::tests -- --nocapture
cargo test --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --bin locallore-desktop-spike retirement_review -- --test-threads=1
rustfmt --check --edition 2021 apps/desktop/src-tauri/src/evaluation/retirement_review.rs crates/locallore-eval/tests/curated_integration_review.rs
git diff --check
```

The historical test requires `LOCALLORE_REVIEW_HISTORICAL_CURATED` pointing
to an owned exact fixture copy; it is deliberately ignored in ordinary runs
when that local artifact is absent. Local copy driver/manifest document the
source and per-file hashes. The fixture/raw outputs stay outside Git.

| Reviewer artifact in `curated-integration-review-artifacts` | SHA-256 |
| --- | --- |
| native-retirement-independent-green.log | `465b8ed14ce39b63dd424573de967c23233b471fb20431995c183059fd658f82` |
| historical-review-final.log | `2d18baba20441b8dd9059b118a264e6b6174b6f8e316b2a94d59372de0fffbc9` |
| historical-review-clippy.log | `6f2be465816f57c0bc775b5b96374d7ec496b49947816bb06396ea9ea3fb4d79` |
| shared-desktop-api-tests.log | `6aaaa7dfc0ca90535c81b1bf66bddc87eabbbabeab47634dc8432fd1b8f334ea` |
| historical-copy-manifest.json | `d1e1cf6d74fbb3cc91f9f7f6640e64e7427aaff16cc4edd9183f20a2a6d2a1d6` |

Additional native setup/Clippy was **not completed by this reviewer**. A
follow-up PowerShell process aborted during .NET EventSource startup with stack
overflow; alternative-shell attempts failed syntax before running a test.
These setup failures occurred during coordinator-reported system memory
pressure; no causal diagnosis or product failure is inferred. No test pass is
counted for those attempts. No further native builds were started after the
coordinator serialized memory-heavy work. Future builds use jobs=1.

Coordinator-reported broader checks are separate: original RED 2 failures,
repaired focused 16 passes/full native 54 passes (one existing ignore),
development 56 plus two contract checks and strict checks. Coordinator also
reports an actual repaired scripted WebView2 cohort at clean `82c0297`:
51 assertions, 16 application-owned images, two processes plus window reopen;
summary `curated-retirement-artifacts/curated-native-44b1f2ba-76d7-4a33-8117-8cab9913afb0/summary.json`.
This reviewer did not execute that GUI cohort or inspect its render images.

The retirement issue is resolved in the reviewed repair with independent unit
GREEN evidence. Current-source real-model cohort, prose/voice/human quality,
transcript-only/verified-memory comparison, long-history evaluation, Android or
device parity, blocked-network/offline installation and full D06/D07 gates
remain unqualified by this review. No model/worker process, package, native
GUI, device, desktop control, protected resource, settings, release or merge
was operated by the reviewer.
