# Selected recovery prerequisite qualification — 2026-10-25

Refs #29 D07.06, partial prerequisite; draft [PR #159](https://github.com/OptimumAF/LocalLore/pull/159).
Root executed the checks below. This author read source/logs/hashes only and
edited this sole new document; no build, test, formatter, model, native app,
GUI, device or desktop execution was performed by the documentation author.
[Claim 6395057217](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6395057217):
sole new document, isolated `docs/d07-selected-recovery-qualification` branch.

## Exact scope and source

Base is accepted main `aa9d4689707a6880de63e18056dccfc955473ab2`.
Candidate `42d7652088cc283f6f331e37baba597d2bff8757` changes only
`crates/locallore-eval/src/local_lane/comparison.rs`: private extraction plus
three focused test groups. Private `RecoveryJob` / `recover_committed_turn` takes
validated profile, actual Engine/path and comparison identity; no factory,
provider, runtime, cancellation or ledger. Read-only Store lookup, actual
receipt-completed cuts and existing replay/request validation drive the result.
Full-run committed recovery reuses it; profile validation now precedes lookup.
Noncommitted admission/clock/provider/watchdog/persistence behavior is unchanged.

The helper is **not yet wired to a native selected entry**. Full native setup
still constructs its factory first. It does not yet avoid native model load on
completed recovery, implement selected execution/public authority or change GUI.

## Frozen failures, correction and actual results

| Source | Retained prefix `d07-selected-recovery-…` | Actual result |
| --- | --- | --- |
| `69eadbc8afbd5e358fd2787cb720e86e60d32de3` | `first-red` | compile exit 101: four absent-helper E0422/E0425 errors; no tests executed, not behavior RED |
| `57386dd49ae618a5e1ff8146bb64e538c969077b` | `first-green` | compiled 7.36s; 1 PASS / 2 fixture FAIL, 51 filtered, tests 0.66s, exit 101; filename is not a GREEN claim |
| `8410b404100e0f0e3e549dad5acd6eb475c0fa9c` | `corrected-green` | 3 PASS, 0 FAIL/ignored, 51 filtered; build 5.50s / tests 0.61s; exit 0 |
| same `8410b404` | `first-format` | format check exit 1, style in new test block; source unchanged |
| `42d7652088cc283f6f331e37baba597d2bff8757` | `full-library` | 53 PASS, 0 FAIL, 1 existing ignore, 0 filtered; build 5.48s / tests 54.94s; exit 0 |
| same `42d76520` | `integration` | resume-basis 5 PASS / 563.97s and comparison-runner 9 PASS / 234.08s, each 0 FAIL/ignored/filtered; build 9.71s; exit 0 |

Every completed process record reports initial clean source and terminal source
unchanged. The fixture incorrectly assumed `execute_turn` had not emitted a
checkpoint. 8410 proves that real file exists, removes **only** it and preserves
all recovery/inventory assertions, Store history, raw evidence and ledger files.
This models workflow-file loss, not process-kill/crash. 42d76520 formats only new
tests; original compile/fixture failures and production assertions stay retained.

The groups cover exact receipt/semantic/mechanical hashes, repeated identical
recovery and whole-directory byte equality; uncommitted `None` without creating
a supplied missing database; and an earlier cut after later commits. Historical
roles remain unknown (`roles_known=false`), with absent capture/recording/metrics/
admission/first-response/commit timing. Elapsed zero is a recovery sentinel, not
original latency or measured zero calls. Fixtures use the existing scripted producer.

The library ignore is existing
`clock_tests::public_comparison_rejects_a_real_preowned_native_before_admission`:
approved-assets ownership opt-in, not run. Intentional poison/forwarding-fault
diagnostics remain in the passing library log; passing does not mean empty stderr.

## Commands and environment

Recorded Rust/Cargo 1.93.1 / Windows 10.0.26300 X64; no installs/version probes.
One job, dev/test debug info 0, `CARGO_INCREMENTAL=0`, `LIBSQLITE3_FLAGS=''`,
TEMP/TMP `<task-root>/memory-controls-temp`, evaluator target
`<task-root>/d07-comparison-view-eval-target`; existing locked dependencies.

```powershell
# Repository root, focused tests (same args at each frozen source):
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <owned-target> --lib selected_recovery_tests -- --nocapture --test-threads=1
# Full-library record includes an actual empty filter argument:
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <owned-target> --lib '' -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <owned-target> --test comparison_runner --test comparison_resume_basis_review -- --nocapture --test-threads=1
# First format attempt, not a claim of final format success:
cargo fmt --manifest-path crates/locallore-eval/Cargo.toml --all -- --check
```

The `local-model` feature compiles that code; these checks did not run a model.
`d07-selected-recovery-check.ps1` preserves exact argv, UTC start/end, source,
cleanliness and exit. SHA256 `d77de721634072f4d44dc48b9ca67d672291ae6f48edeffa947b2f208c8ffab9`.
Public commands use placeholders; private absolute paths remain in local evidence.

| Completed log | SHA256 |
| --- | --- |
| `d07-selected-recovery-first-red.log` | `df144837eb692de6baa95d62d4f3dc383b3a5645e61e617372c89b1decc91d14` |
| `d07-selected-recovery-first-green.log` | `be93d96de374d99cc5a7ab7864d2ba529110364878875d979496861dead25aca` |
| `d07-selected-recovery-corrected-green.log` | `a2768e2802c20beaf2b42b0cd26f84757642e5aa69c5c4c45521b798b90e6f91` |
| `d07-selected-recovery-first-format.log` | `cc63de813affb7261ea3441b8333befaad1cb973620ff0e2cdea82e06100983d` |
| `d07-selected-recovery-full-library.log` | `7be1efa2c11d6fa42311d563fdf99f4984aee8c56308e3aeb4e6fc679b6ad1f1` |
| `d07-selected-recovery-integration.log` | `1e21c2c0eb6d7d3fee22e8232ab15ae1ff8d3174edccb2ba910f64477b483f38` |

## Final source-bound checks and review

All remaining prerequisite checks completed at clean/unchanged42, exit 0:

| Check | Actual result / UTC interval |
| --- | --- |
| Full frontend + normal-hook exclusion; frontend format; Rust format | PASS, sequential 07:53:49.4025486Z–07:54:01.6081704Z; frontend is synthetic/controller evidence |
| Native all-target/all-feature strict Clippy; normal default-feature build | PASS, 8.44s / 14.26s; 07:54:01.7014268Z–07:54:24.9926266Z; no native tests/app launched |
| Evaluator all-target strict Clippy with `local-model`; evaluator format | PASS, Clippy 5.46s; 07:54:25.1472863Z–07:54:32.8959676Z |
| Genuine retained historical cohort | 1 PASS/8 filtered in desktop target, 8.54s; 1 PASS/0 filtered in original readonly target, 2.94s; build 1.47s; 07:54:33.0171702Z–07:54:46.8713631Z |

The five Native/Node commands exactly repeat
[reader normal restoration](D07_COMPARISON_READER_NATIVE_QUALIFICATION_2026-10-25.md),
Node 24.22.1 / same environment / `<task-root>/d07-comparison-reader-native-target`.
Only commands are reused, not old results. Additional evaluator commands:

```powershell
cargo clippy --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <owned-target> --all-targets -- -D warnings
$env:LOCALLORE_D07_HISTORICAL_COHORT = '<retained-original-33356-rollout>'
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <owned-target> --test comparison_desktop_review --test comparison_historical_readonly -- --ignored --nocapture --test-threads=1
```

The genuine old cohort was not manufactured by deleting current fields. Actual
inspection preserves its bytes and original report, while current resume is
refused. This is Rust read-only evidence, not historical GUI/model execution.
Normal artifacts restored: JS 525441 bytes, SHA256
`f387418355885ecb025326284ea767a03c008215ff2e66d01795e220a634d0a2`;
debug EXE 32024576 bytes, `d2275c5d82e1b779043dba1168edf960352d6d7d5b6d5137ec6c4bb1b1e723c4`.

Additional SHA256 (all names prefixed `d07-selected-recovery-`):

| Evidence suffix | SHA256 |
| --- | --- |
| `native-frontend.log` | `32a1137ae707f7d06eedf39e686a5a34a4948152b5e4248cedc350ce4e1348ed` |
| `native-frontend-format.log` | `f20510a9da4717c51c4cffee6d0dd88d6c9a723d0a83711d01216f5b48961283` |
| `native-rust-format.log`, `final-format.log` (empty) | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `native-native-clippy.log` | `a5c0969f2276a236b2ad35a7d2aeb2a5bb2d9043f9e4bb4b5da40e37ac580ca1` |
| `native-native-normal-build.log` | `3b4d701b58cab0a0ae1eb6445af1e22e0769c059931286643f487fb24f49f5db` |
| `native-results.json` | `dc525f2ea01cd972181723127cca29d0fb904269be95e74498794d2b73f976cb` |
| `native-build-artifacts.json` | `47cb7a802afa2b018f856cf18cd05fb8890a79d3f1207e81a4d270f611696074` |
| `final-clippy.log` | `cd9850af60fc933c9afee951c38d5d0d6b01f7adfe9feed31dc67fef5bcffbcd` |
| `genuine-historical.log` | `2f99c36ec7525c6308a720f94b097843e2d6830c92a10243258fffa5b8d372b2` |

[Independent source review](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6394966880)
found no new concrete production defect: 493ab101 versus d2222fd0 plus 8410/42,
source-only, no execution or human approval. Future callers must preserve coherent
validated Engine/path/profile/binding; this is not a deserializable execution grant.

The serial integration completed at clean/unchanged42, from
07:39:00.7099281Z to 07:52:29.9867129Z. Only its terminal log is hashed above.
The prerequisite's stated internal checks are complete; no in-flight log was
treated as a completed result. No native Rust test execution, fresh GUI/render,
real model, Android/device, selected producer/native entry or whole D07 acceptance
is inferred. Core/Store/schema/UI/Android were unchanged; earlier reader results
are not this source's checks. Next: Root reviews the focused prerequisite, then
separately implements and qualifies selected execution and native/UI adoption.
