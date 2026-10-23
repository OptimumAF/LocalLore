# Android native storage fault review — 2026-10-22

Scope: M04.04, coordinator claim [#8 comment 6356808717](https://github.com/OptimumAF/LocalLore/issues/8#issuecomment-6356808717). Independent source review from `review/m04-android-storage-faults`, baseline `bc6420030b500e7dd0cea5d59ec2f5d2e7e798e6`. The reviewer owns only this report. The coordinator owns cross-build integration and emulator execution; the pressure fixture has a separate author. This report does not record an emulator pass.

## Accepted private fault fixtures

`crates/locallore-storage/src/turns.rs` contains test-only, thread-local fault injection. Production builds have a no-op checkpoint. No fault environment variable or test hook is added to production storage APIs.

The error and process-exit tests each loop through seven checkpoints. They are two Rust test cases containing fourteen fault iterations, not fourteen independently reported test cases:

| Stage | Boundary |
| --- | --- |
| 0 | Validated turn and size budgets, before event insertion |
| 1 | Event inserted, before its witnesses; first event reaches this hook |
| 2 | All accepted events and witnesses inserted |
| 3 | Projection written |
| 4 | Turn status and stored response updated |
| 5 | Branch head updated, transaction not yet committed |
| 6 | SQLite transaction committed |

Stages 0–5 must reopen at revision 0 with the potion owned by the player. Stage 6 must reopen at revision 2 with the potion owned by Mira. The fixture commits a gift and a wait: two accepted events, one turn. The error fixture also verifies story time, durable phase and projection consistency. Both fixtures retry the original request and require the final revision to stay at 2. A stage-6 error is an ambiguous acknowledgement after a successful commit; describing all seven stages as rollback would be incorrect.

The process fixture starts the exact current executable, selects only `turns::tests::crash_child`, supplies its owned synthetic database and stage, suppresses child output, and requires exit code 77. It waits for its own child and kills/reaps that child after ten seconds. This exercises exit without Rust destructors. It does not simulate physical power loss, a failed storage controller, or termination during an individual filesystem synchronization.

## Android execution boundaries

The pinned [Rust 1.93.1 Unix implementation](https://github.com/rust-lang/rust/blob/1.93.1/library/std/src/sys/pal/unix/os.rs) reads `TMPDIR` before selecting the Android fallback and implements Android `current_exe` through `/proc/self/exe`. Run the audited PIE directly, retain it unchanged until its child completes, and set `TMPDIR` to a newly created private synthetic directory under the exact owned `/data/local/tmp` root. An explicit linker invocation would change the executable-discovery assumptions.

The existing `Temp` helper creates a unique directory rather than reusing an existing path. Its recursive cleanup is confined to that newly created fixture directory. The coordinator should create the containing root with restrictive permissions and refuse an existing root. Remote timeout or client-disconnection outcomes require explicit process/child cleanup before deleting that root or starting another run; the child’s normal ten-second watchdog does not prove cleanup after the parent is externally killed.

No app installation, app data deletion, model access, real save, device-wide disk filling, or arbitrary process termination is needed. Keep full synthetic test output local and ignored. Public evidence should contain fixed test identifiers, exit status, audited binary hash/ABI, iteration counts and cleanup outcome; do not copy arbitrary panic output or environment contents into the report. Retain failed attempts rather than replacing them with a successful retry.

## Cross-build review

Reviewed the coordinator's initial `--unit-tests` implementation read-only. It invokes pinned Cargo with `test --lib --no-run --locked --offline --release`, targets only `locallore-storage`, and parses Cargo's emitted executable instead of choosing a stale glob. It requires one library test artifact inside the requested target's release/deps directory and applies the existing ELF/PIE, alignment, interpreter and dependency audit. It does not run cross-compiled tests on the host. The original example path remains the default and explicit example/unit selection is mutually exclusive. No blocking source issue was found in that inspected version; final integration and helper-test results remain separate evidence.

An x86_64 executable can be exercised on the available x86_64 emulators. Auditing or building an arm64 executable alone is not arm64 execution evidence. A/B results must retain their respective emulator API, ABI and observed page-size scope.

## SQLiteFull and sole-potion evidence

The existing `sqlite_full_rolls_back_events_projection_response_status_and_head` fixture restricts SQLite's page budget after durable draft creation and requires `TurnError::Full`. It verifies unchanged canonical bytes, a draft turn and revision 0 after reopen. Its large commands are speech; it does not itself prove sole-potion retry after freeing capacity.

SQLite documents [`max_page_count`](https://www.sqlite.org/pragma.html#pragma_max_page_count) as a database page limit; it cannot be reduced below the current page count. [`SQLITE_FULL`](https://www.sqlite.org/rescode.html#full) is error 13. The fixture therefore exercises actual SQLite capacity failure without claiming the emulator's storage partition reached ENOSPC. For the new pressure fixture, review requires an effective page-limit check, the sole-potion command in the failing proposal, unchanged events/projection/response/status/head after failure and reopen, relief of the artificial limit, and an original-key retry that transfers that potion exactly once. A subsequent retry must return the stored receipt without further canonical effects.

At this review checkpoint the new pressure fixture was not yet integrated. Its source, host checks and coordinator emulator results require follow-up; none are inferred here.

## Review checks and limits

Read-only inspection covered the actual checkpoint placement, error mapping, private fault tests, temporary-directory ownership, child spawn/wait/exit handling, crate dependency configuration, existing durability review tests, baseline native verification instructions and coordinator cross-build changes. Official references above establish pinned Rust behavior and SQLite error semantics. No device, ADB, Gradle, model or GitHub mutation was performed by this reviewer.

Independently ran `python -B -m unittest discover -s scripts/tests -p test_storage_android_smoke.py -v` against the coordinator's helper: 7 tests passed. These use synthetic temporary artifacts and mocked Cargo execution; they cover current-artifact selection, stale/duplicate/malformed/wrong-target rejection, required build flags, failed-build propagation and mutually exclusive modes. They do not establish a successful native build or emulator execution. `git diff --check` passed in the report worktree.

This is a bounded native storage fault packet. It does not close the broader M04 milestone, establish physical-phone durability, prove hardware power-loss recovery, or diagnose unrelated graphics/runtime failures.
