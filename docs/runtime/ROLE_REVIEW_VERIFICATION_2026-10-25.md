# Source-bound role review verification — 2026-10-25

Supporting M01.03/M05.06 and D07.04/.06. Base: accepted main `4511d67d`
(owner-merged PR #187). Final executed source: `a1cb5034`.
The new tool is a private assessment workflow, not a model-quality result.
Full tasks remain unchecked pending their actual criteria and owner acceptance.

## What changed

The existing comparison runner already stores engine-validated outcomes,
captures and role recordings. A separate `quality-review` binary now exports
a bounded review packet and summarizes reviewer declarations against freshly
validated evidence. It reuses the retained read capability and explicit Author
inspection boundary. It does not add a comparison runner or another gameplay
authority. See the [versioned protocol](ROLE_REVIEW_PROTOCOL.md).

Every original report row stays in the denominator. Only a deterministic prefix
exports private capture/output evidence. Director and Narrator judgments remain
separate; repaired attempts keep their original order and hash. Missing output,
fallback, scripted/native lanes and source mismatch stay visible. A rationale
alone does not count as an assessed output. All summaries keep
`quality_accepted=false`; reviewer tokens are self-reported, not authenticated
human identities. No subjective score can override engine or privacy failures.

Existing engine, Store, Host, runtime, comparison report/runner/facade, fixture
corpus, Android, UI and dependency/lock sources are unchanged. New Rust source
does enter the existing build-source inventory, so an older retained run can
correctly show `source_matches=false`. The tool does not rewrite its history.
This is independent of open phone/emulator PRs #181 and #186; neither is merged
or modified by this implementation branch.

## Actual focused checks

Windows x64; existing Rust/Cargo 1.93.1 and cached locked dependencies, offline.
Task-local target directory, two compiler jobs; no persistent environment or
system setting changes.

| Procedure | Actual result |
| --- | --- |
| `cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --bin quality-review -- --test-threads=1` | Initial 11 contract tests pass, 0.16 s; owned 26,150 ms/child 0, known cleanup/capture, 247 unchanged source hashes. An unused import warning was subsequently fixed. |
| `cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --test role_review_cli -- --test-threads=1` | Initial seven Windows CLI tests pass, 157.37 s; owned 162,947 ms/child 0, known cleanup/capture, 248 unchanged source hashes. |
| Actual CLI RED controls against a newly produced 12-row ScriptedBaseline comparison | Malformed entry reproduces panic/exit 101 with 275 stderr bytes; U+2028 rationale incorrectly accepts/exit 0. Source directory inventory unchanged. Owned 13,069 ms/child 0 credits reproduction only. |
| Actual CLI GREEN controls after `07fd983b`/`a1cb5034` | Fresh template and pending summary succeed; malformed entry and U+2028/U+2029 notes each give controlled exit 2, fixed JSON and zero stderr. Owned 15,760 ms/child 0, known cleanup/capture, unchanged source and comparison inventories. |

The CLI tests produce genuine comparison files through the production
Host/Engine/Store path with an explicitly scripted provider. They check exact
facade evidence, sampling, partial/rationale-only declarations, strict tamper
and duplicate refusal, create-only output outside the run, permission refusal,
actual corrupted recording refusal and complete source file inventories.
Windows DOS-device/alternate-stream cases execute here; the conditional Unix
symlink test does not. Test declarations are not human reviews or native model
quality measurements.

## Findings fixed before publication

Independent review found two malformed-input defects. Mutable string indexing
could panic on a primitive review entry before checking its shape. The contract
now checks all seven entry keys before mutable access and adds primitive/null/
array/object regression cases. “One line” rationale validation now explicitly
rejects U+2028/U+2029 as well as control characters. New CLI regressions require
exit 2, empty stderr and a fixed refusal envelope rather than accepting any
nonzero exit as sufficient. These changes add two contract methods and one
Windows CLI method to the initial counts above.

The GREEN workflow rebuilds a packet from the same preserved RED comparison.
Its source mismatch is correctly labelled after the code change. A valid pending
packet still opens successfully; negative results are not merely stale-binding
refusals. No source database, checkpoint or raw recording is altered.

## Broad gate setup and retained failed attempt

The initial all-feature run enabled existing protocol-owner tests before their
tiny child fixture had been built. Seven such cases failed; a separate exact
case confirms `WorkerUnavailable` before child creation. That 217 ms owned
diagnostic expects internal test exit 101 and is not a passing ownership test.

Root stopped only the failed run's exact library test process after verifying
its executable, creation time and Cargo/Python parent chain. Its parent
supervisor stayed alive to record known cleanup/capture: 781,373 ms, worker
`0xffffffff`, 248 unchanged source hashes. The partial suite is not credited as
a completed pass. Synthetic partial fixtures and logs remain retained. No other
project emulator or system setting was touched.

Root then built `protocol-fixture` with `development-worker` in the same target
directory. It is a tiny Rust protocol child, not an LLM or model file. Actual
fixture build, format check and strict all-target/all-feature Clippy each
return 0: 6,226 / 462 / 10,663 ms. Combined owner 17,486 ms/child 0, known
cleanup/capture and 248 stable source hashes. The reporting helper initially
looked for obsolete combined-log filenames after the successful commands; that
helper error is retained. A separate readback checks every per-stage result and
raw log, rather than crediting aggregate exit zero alone.

The corrected four-thread run passes the library's 114 tests (seven existing
opt-in cases ignored) and all 13 review-contract tests, but then fails three
existing desktop-reader integration cases with Windows file-region lock error
33. Those tests share a retained fixture: concurrent inventory reads conflict
with its reader lock. The partial combined run is a failure, not a broad pass:
owner 516,203 ms/child 101, known cleanup/capture and 248 unchanged source hashes.
No production locking behavior was relaxed to make the tests pass.

The final complete gate runs all targets serially, with the same pinned code
and assertions. A task-local optimized test build reduces the expensive
synthetic history work; debug assertions and overflow checks remain explicitly
enabled. No test is removed or weakened. The exact environment is
`CARGO_BUILD_JOBS=2`, `CARGO_INCREMENTAL=0`, both `CARGO_PROFILE_TEST_DEBUG` and
`CARGO_PROFILE_DEV_DEBUG=0`, both `CARGO_PROFILE_TEST_OPT_LEVEL` and
`CARGO_PROFILE_DEV_OPT_LEVEL=1`, and both profiles' `DEBUG_ASSERTIONS` and
`OVERFLOW_CHECKS=true`. A separate task-local target directory is used.

```text
cargo build --locked --offline --manifest-path crates/locallore-local-runtime/Cargo.toml --features development-worker --bin protocol-fixture
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --all-features --all-targets -- --test-threads=1
```

Actual fixture build: 11,060 ms/exit 0. Full Cargo command: 848,676 ms/exit 0
(including compilation); enclosing owner: 859,870 ms/child 0, known cleanup
and complete capture, zero owner stderr, all 248 source hashes unchanged.
The 20 target results contain **188 passed, zero failed and 14 ignored**.
These include **13 review-contract tests** (0.03 s) and **eight Windows CLI
tests** (54.88 s). Seven ignored library cases require approved native assets;
the other seven require genuine retained historical/native evidence. None is
credited as executed or as a native-model result. The Unix-only symlink method
is not part of the Windows roster. This gate covers `locallore-eval` targets,
not every crate in the repository.

An older unoptimized serial integration run was still repeating cases after
the complete pass. Root stopped only its exact test process after rechecking
executable, creation time and Cargo/private-worker parents. Its supervisor
records 1,549,595 ms/worker `0xffffffff`, known cleanup/capture, zero owner
stderr and 248 stable source hashes. This retained partial run is not counted
as another pass. The task-specific 1,800-second owners do not change inference,
turn, device, emulator, or generic supervisor limits. No other project's
emulator or system setting was changed.

## Limits

No real model load/generation, human assessment, Android build/emulator run or
physical-model result follows from this packet. Existing host comparison
outputs are integrated turns, not independent Director-only/Narrator-only
experiments; Director failure can censor Narrator availability. Host Qwen/
llama.cpp evidence does not qualify Android Gemma/LiteRT or a phone profile.

A bounded discovery earlier in this packet using the previously reviewed
`70d40068` collector finds the selected USB phone absent: owned 5,779 ms/worker 2 expected
refusal, known cleanup/capture, unchanged source, zero target calls. No alternate
device, install, model copy, inference, app stop or setting action follows.

Private packets contain Author capture material and remain outside Git. Raw
diagnostics, identifiers, test databases, binaries and model weights are not
uploaded. Public evidence consists of commands, counts, hashes, scope and limits.
The tool binds retained bytes under cooperative reader locks; it is not proof
against a hostile host or adversarially rewritten evidence, and it does not
authenticate who supplied a judgment.

The selected private evidence index covers 226 files / 3,447,368 bytes across
eleven terminal check directories, including failures, actual RED/GREEN
controls and final raw logs/source-owner maps. Index SHA256:
`a331507ac3afbff0b0cb6ddd132c05e5a7d4352869ea0edfe68bd84baa9a2ea1`.
It excludes target binaries, external temporary integration datasets, weights,
APKs and prior packets; it is not an all-machine or artifact-authenticity seal.
The underlying evidence remains private. A separate readback verifies the
20 raw target summaries, ignored roster and final 248 source hashes.
