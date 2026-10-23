# Android native storage fault review — 2026-10-22

Scope: M04.04, coordinator claim [#8 comment 6356808717](https://github.com/OptimumAF/LocalLore/issues/8#issuecomment-6356808717). Independent source review from `review/m04-android-storage-faults`, baseline `bc6420030b500e7dd0cea5d59ec2f5d2e7e798e6`. The reviewer owns only this report. The coordinator owns cross-build integration and emulator execution; the pressure fixture has a separate author. The final evidence audit below verifies retained coordinator results without reviewer device access.

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

Follow-up source review covered pressure fixture commit `a613660` and the coordinator's test-only module registration. Its first case proves the exact gift envelope and witnesses fit under the capped page budget, rolls that proof back, and requires two actual `TurnError::Full` results from the owner transaction. It compares every persisted scoped table, the complete draft and response absence, canonical bytes, observer contexts and a separately committed control story. After raising capacity it requires the reference eight-event outcome, stable full-table contents across exact retries, and one potion owned by Mira after reopen. It also preserves truth/belief/discovery boundaries. The second case requires actual Full during draft creation, no residual turn or canonical change, successful same-connection recovery and exact retry after reopening the successful result. Temporary database files remain bounded below 2 MiB. No production schema or API change is needed.

One evidence gap was sent to the coordinator: the initial two cases did not reopen the failed sole-potion draft before retrying. Author follow-up `164df13d`, integrated by the coordinator as `8a4abad`, closes this gap with a third case, `full_then_reopen_preserves_draft_and_exact_retry_spends_potion_once`. It drops the owner immediately after the first actual Full, reopens before comparing all rows, canonical state, contexts and the durable draft, queries the new connection's cap and explicitly reapplies the limit. It then requires another actual Full before relieving capacity and verifying the same exact recovery invariants. The original same-connection case remains. An atomic sequence suffix supplements process/time directory names while retaining create-new semantics. This is source verification; native execution results remain coordinator-owned evidence.

## Coordinator native procedure review

Reviewed ignored `target/checks/storage-faults/run_device.py` before device dispatch. It creates an exclusive local evidence journal, flushes/fsyncs the start and terminal records, and confines remote work to a fresh UUID root. The direct native executable has a unique basename that fits Linux's 15-byte process name limit. Each ADB client uses the existing bounded process helper; uncertain client cleanup stops subsequent calls. The remote native execution has a 120-second deadline and the host client a 150-second deadline. Test-only child-control environment variables are cleared before launching the owner.

The parser requires the exact twelve substantive test identifiers, one successful result per identifier, no unknown matched test, the twelve-pass/one-filtered summary and a completed zero-exit client. It cannot count the auxiliary `crash_child` as an independently exercised fault test. The full output is bounded and kept locally; the JSON journal contains fixed test identifiers and status fields. Hash checks bracket execution. The final process-absence check precedes hash-guarded deletion of the exact executable and nonrecursive removal of empty TMPDIR/root; surviving processes or unknown cleanup retain the root and fail the run. The coordinator must stop dispatch after a failed or uncertain target rather than continue to B automatically.

One low-risk procedure correction was requested before execution: create the root and TMPDIR with mode 700 rather than relying on default mkdir permissions. The reviewed fixtures contain only synthetic data, but restrictive creation matches the stated private-directory boundary. The final procedure contains both mode-700 operations; the coordinator reports applying them before the first device call. No other blocking source concern was found. This ignored procedure is not a shipped default runner. Source review preceded execution; the retained results were independently audited afterwards as described below.

## Review checks and limits

Read-only inspection covered the actual checkpoint placement, error mapping, private fault tests, temporary-directory ownership, child spawn/wait/exit handling, crate dependency configuration, existing durability review tests, baseline native verification instructions and coordinator cross-build changes. Official references above establish pinned Rust behavior and SQLite error semantics. No device, ADB, Gradle, model or GitHub mutation was performed by this reviewer.

Independently ran `python -B -m unittest discover -s scripts/tests -p test_storage_android_smoke.py -v` against the coordinator's helper: 7 tests passed. These use synthetic temporary artifacts and mocked Cargo execution; they cover current-artifact selection, stale/duplicate/malformed/wrong-target rejection, required build flags, failed-build propagation and mutually exclusive modes. They do not establish a successful native build or emulator execution. `git diff --check` passed in the report worktree.

## Final retained-evidence audit

Independently inspected the coordinator's integrated [verification report](ANDROID_FAULT_VERIFICATION_2026-10-22.md), [sanitized results](ANDROID_FAULT_RESULTS_2026-10-22.json), both complete ignored `A-native.jsonl`/`B-native.jsonl` journals, both native text outputs, `host-final.log`, `build-final.log`, ELF metadata and actual native artifacts. This audit read files only; it did not run another build or device command.

A read-only assertion script verified all five published source hashes against local bytes and their tracked contents at `3267aa6`. Both build entries exactly match the build log and `elf.json`; independently rerunning the ELF inspection on each existing artifact reproduced its ABI, byte count, hash, PIE, alignment and shared-dependency fields. The frozen executed x86_64 file matches `9d998b2f6991764ded0c68c98fc05ae3fe01fe08e561736c4b9e4f3a79c01dc3`.

Both published journal arrays exactly match their complete ignored originals, including the start and terminal records, and both journal hashes recompute correctly. Each terminal record reports completed exit 0, successful protocol, unchanged binary identity, process absence before/after, host-client cleanup and owned-root removal. The raw native outputs independently match the exact twelve expected case names and order: all pass, with the auxiliary child entry filtered once per target. Totals are **24 native passes across 12 unique substantive cases**, two started/finished attempts, zero failed or skipped substantive cases. The nested seven error boundaries and seven child exits are not inflated into separate top-level passes.

The full host log independently totals **125 workspace Rust test entries**, including the auxiliary entry, plus **3 linker tests** and **198 Python tests** in suites of 116, 10, 14, 20, 13 and 25. It records successful format, strict Clippy and four engine fixture comparisons. The new three pressure cases are present in the thirteen-entry storage unit cohort; the seven helper tests are included in the final scripts suite. These counts agree with the published report.

No concrete inconsistency or unsupported scope claim was found. The published artifacts avoid raw emulator identifiers, host user paths, temporary root names and story/database contents. They preserve the author-side directory-collision finding and the intermediate-reopen correction. They explicitly distinguish SQLite page-cap Full from partition ENOSPC, process exit from hardware power loss, native Store checks from a Compose storage-error journey, and ARM64 build/audit from execution. The earlier graphics watchdog cause remains unknown and no fix is claimed. Assertions that app/model data and unrelated devices were untouched are coordinator procedure attestations; the reviewer did not independently inspect those devices.

## Accepted-main integration audit

Accepted main independently advanced to `51ec963` through D03/#47. Read-only comparison confirms its storage additions are read-only open, bounded inspection backup and one private budget test; they do not change ordinary open/configure, turn commit, fault hooks, schema or this packet's pressure/helper logic. The new budget test uses the supplied TMPDIR and removes its destination. Accepted optional-host sha2 and lockfile changes belong to D03. They are not a new dependency choice made by this packet. Local integration `4be9698` is recorded separately from the initial native source.

The retained first integrated host log confirms a concrete failure in `inspection_review`: temporary directory creation returned `AlreadyExists`, with ten passing cases and one failing case. Independently reviewed `5710112`: it adds an atomic suffix to that fixture's PID/time directory name, retaining create-new behavior and every assertion. Relaxed atomic ordering suffices for unique counter values; no inter-thread publication is needed. It changes no production or native Store code. Both retained targeted rerun logs show eleven passing cases; the coordinator records sixteen test threads for those runs.

The version-2 results preserve the original cohort and append an integrated cohort. A second read-only assertion script verified all four full journal copies and hashes, all four raw native outputs, each cohort's exact result membership, terminal status and cleanup fields, and each pair of ELF artifacts against its own build log/metadata. It independently re-audited all four existing ELF files and checked both frozen x86_64 binaries. Published source hashes match the corresponding committed source contents; integrated hashes also match the local files. Native build source `4be9698` remains distinct from final host source `5710112`, whose only subsequent source correction is the workspace test fixture.

Both integrated A/B attempts have thirteen substantive passing cases and one auxiliary child entry filtered, completed exit 0, matching binary identity and affirmative native/client/root cleanup records. The sole added substantive case is the accepted inspection-backup budget test. The integrated x86_64 hash is `835e5657d127c6821c6a503de6cf8434730100501006462d80011df880e2600c`; the separately audited ARM64 hash is `3dd8827d7a8240b5fc569185038c823da1825a0e422c8ab008cd260dce4c89f8`. No ARM64 execution is implied.

Independently recomputed final totals are **26 integrated native passes**, plus the retained **24 initial passes**: **50 passing executions, four complete attempts and 13 unique substantive cases**. The successful integrated host log totals **140 workspace Rust entries, 3 linker tests and 198 Python tests**, with successful format, strict Clippy and four fixture comparisons. The earlier failed integrated gate is preserved alongside the two targeted reruns and final successful gate. No failure is erased or counted as a pass.

No new concrete concern was found in the final version-2 report or artifacts. Privacy and the native-only, page-cap, process-exit, physical-phone/model/ARM64 limitations remain explicit. The reviewer performed no build, device or GitHub action during this integration audit.

This is a bounded native storage fault packet. It does not close the broader M04 milestone, establish physical-phone durability, prove hardware power-loss recovery, or diagnose unrelated graphics/runtime failures.
