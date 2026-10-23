# D06/D08 teardown correction review — 2026-10-23

This is an independent, narrow review of coordinator-authored desktop cancellation and Host story-invalidation corrections. It supplements `D06_PRIVATE_CAPTURE_REVIEW_2026-10-23.md` and `D08_NATIVE_ARCHIVE_REVIEW_2026-10-23.md`. It is not acceptance of either milestone, a new Store review, or a platform qualification. The reviewer previously authored the shared archive/staging work; that implementation is outside this independent scope.

## Source and ownership

Claims: #28 comment 6368612299 and #30 comment 6368612913. The only authored change for this review is this document. No production source, coverage-v2 handoff, Android files, runtime, models, device state, or desktop controls were changed.

Reviewed desktop commits:

- `0bb10d07155b9fa8d988658e952b6b1a4b5d858a`: defer native cancellation until admission; mark old operations cancelled before asynchronous invalidation cleanup.
- `6cf458160e0787968edf14cf3abfd1e49fce33a3`: bound expected cancellation diagnostic count while retaining the category check.
- `4ff02b02344d67bfec266735ee4071c4c14dde29`: resolve cancellation during uncertain recovery through a separate original-key lookup. The reviewer tested its exact delta cherry-picked onto 6cf4581 as isolated commit `76c84cc9739b45a52bc360ac7ab06d150dfdae1c`.

Reviewed Host implementation `7fad1852b4c9122eb8db2a58abfe5c2bfbb3fc72` and final explanatory wording at `744b7220e1dcfa2ba964db4a82404e0ffade7bdc`. The accepted deletion adapter was read only as an integration dependency.

## Findings and correction disposition

No additional publication blocker was found in these final deltas. This conclusion is limited to the source and focused executions below.

**The first desktop correction needed the subsequent recovery fix.** The reviewer's original four-schedule check passed at 6cf4581, covering admission, definite rejection, a lost acknowledgement followed by recovery, and switching stories. The coordinator's native legacy run then demonstrated a missing schedule: cancellation while a first recovery status lookup was held and later failed with Transport. At 6cf4581, cancellation deferred because the original submit acknowledgement was absent, leaving that schedule unresolved. The coordinator reports that the appended actual-controller schedule first failed with `unknown != cancelled` before 4ff02b0; the reviewer did not execute that before-fix failure. Passing the original four schedules was insufficient evidence for this race.

At 4ff02b0, `cancel()` captures whether recovery was already active before replacing the visible pending stage. An ordinary in-flight initial submission only sets the cancellation flag; its acknowledgement path cancels the original key before Prepare. During uncertain recovery, a separate status read must prove the original turn, scope, expected revision, and an admitted/terminal phase before setting `submitted` and issuing native Cancel. UnknownTurn, malformed identity, and lookup/transport failures do not prove admission. The catch preserves uncertainty and the original unresolved operation; it does not invent rejection, resubmit a replacement key, or enter Prepare/Commit. The existing recovery path can retry only the original request after an explicit UnknownTurn.

Terminal publication validates the original identity and clears that operation's unresolved reference. Consequently, the older held lookup's later Transport error cannot replace the newly published cancelled result. Context invalidation marks the old operation cancelled before awaited export cleanup; delayed admission cancels that original operation without publishing into a newly selected story. A recovery cancellation that finishes after switching can still control only the captured old session/key; publication remains fenced by `current(op)`. No new commit authority was introduced.

**The archive diagnostic assertion remains restrictive.** The source-stage count changed from exactly two to at most two because early cancellation can avoid a native Prepare call. The immediately preceding assertion still requires every captured error to be native `Cancelled`. Render errors, unhandled errors, other categories, and more than two errors still fail. Canonical-state and cancellation assertions remain separate. This is a bounded scheduling allowance, not a waiver of arbitrary native errors.

**Story invalidation now retires private capture ownership before removing matching sessions.** `Host::invalidate_story` recovers a poisoned State mutex only for teardown, retires each matching owner's capability, cancels that session's turns, and removes matching-story sessions across branches. It leaves unrelated owners/sessions live and does not clear the mutex poison or claim gameplay recovery. The State guard is dropped before trace cleanup; `try_lock` prevents a busy diagnostic reader from becoming a teardown prerequisite.

When the trace lock is busy, retained diagnostic metadata is not synchronously erased. Removed sessions cannot read it through Host, and owner retirement prevents late private writes; existing capture access/sweep logic purges retired owners on subsequent access. This is access invalidation with deferred cleanup, not immediate physical erasure or revocation of already detached copies. When the trace lock is available, the existing whole-ring clear remains; unrelated diagnostic metadata may also be cleared even though unrelated session ownership survives.

For accepted #81, `WorkspaceRegistry::with_story_deletion` was read at 744b722: it holds the mutation gate, identifies leases by the canonical database path, performs deletion successfully, then invalidates that story in those leases. Session-creating/committing calls share the mutation gate. Prepare intentionally bypasses that gate for cancellation, so retirement/cancel/removal must still fence late work. The new focused unit verifies the cleanup primitive, not a fresh deletion transaction or complete live worker/deletion schedule. This review does not requalify Android or accepted #81 end to end.

## Reviewer-executed checks

All inputs were synthetic. No native app, model, picker, desktop automation, device, hosted inference, or protected-chat resource was used. Build/test outputs stayed in this task's own ignored D-drive targets.

At 744b722, with Rust 1.93.1, `CARGO_PROFILE_DEV_DEBUG=0`, `CARGO_PROFILE_TEST_DEBUG=0`, and `CARGO_INCREMENTAL=0`:

```powershell
cargo +1.93.1 test -p locallore --all-features --lib --locked --offline --target-dir D:/CodexLocalLore/01a165d9-ff25-7500-a550-1099087d4e37/d06-private-capture-review host::tests::story_invalidation_retires_only_matching_owners_even_with_busy_trace_and_poison -- --exact --nocapture
```

Result: **1 passed**, zero failed. This test exercises both ordinary and deliberately poisoned State while holding the trace lock, checks selected-owner retirement, unrelated-owner survival, selected-session removal, and poison preservation. Its caught synthetic panic is expected. Log: task-local `d06-invalidation-delta-test.log`.

In the isolated desktop checkout, using the existing bundled Node **v24.19.0** and `LOCALLORE_CHECK_OUTPUT_DIR` pointing to task-local `d08-early-cancel-review-checks`:

```powershell
& 'C:\Users\Avery\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' check-early-cancel.mjs
```

Result at 6cf4581: **PASS, four schedules** (`d08-early-cancel-initial-review.log`). Result at the exact 4ff02b0 delta/local 76c84cc: **PASS, five schedules** (`d08-early-cancel-final-review.log`). The latter runs the actual bundled Controller with a deferred synthetic Gateway, including the held-failing-lookup recovery cancellation. It asserts original-key control, no speculative cancellation before admission proof, truthful rejection/uncertainty, cancelled terminal result, unchanged revision, no Prepare/Commit calls, and stale-story display fencing. This is controller plumbing evidence, not real native IPC execution or a Node security/support qualification.

The coordinator separately reports native legacy **21 checkpoints / 163 assertions passing at 4ff02b0**, after the earlier native failure, and a seven-cohort rerun in progress at handoff. Those native checks were not executed by this reviewer and are not substituted for their final publication evidence.

## Exact reviewed file bytes

SHA256, desktop final isolated source 76c84cc (coordinator 4ff02b0 delta):

| File | SHA256 |
| --- | --- |
| `apps/desktop/ui/controller.ts` | `e81b842f3e23c69f4bf7476c1ca76ab34b07a3a8a409d054272c505a4ad088c2` |
| `apps/desktop/check-early-cancel.mjs` | `de29ac11bcf89fe9770104235e03a3aff838818aa9416fbe7221919455378787` |
| `apps/desktop/ui/archive-journeys.ts` | `07c61d5900d966e0c1483f745c74b22758730c28f0862a981ccac4ab63415309` |
| `apps/desktop/verify-frontend.mjs` | `798c1c4fb7e7640462900d1b060ddc1c965d19e4e4e8f2225b789ccee5e3f13b` |

SHA256, Host final source 744b722 and read-only dependencies:

| File | SHA256 |
| --- | --- |
| `crates/locallore/src/host.rs` | `c64fe0eac17c0a6002fb5b5e3acb250dd91e50e07c12fa42fcd9a5646f34a122` |
| `crates/locallore/src/turn_capture.rs` | `4522814d02281639220505b3865340027aebc4e3383746224d7f944f13b22a98` |
| `crates/locallore/src/turn_trace.rs` | `05bc6e7998f698e88712a48650cf654efd2a8af494d6f05e86bd8516ba206b70` |
| `crates/locallore-android/src/workspace.rs` | `d9e4db4ded3d4db21614428cc37b14c3f4ec2390c6ace7bf4d623bb73751c0ac` |

The next qualification belongs to the coordinator's frozen final native cohorts and integration checks. Full D06 capture UI/export and full D08 platform/acceptance gates remain outside this delta review.
