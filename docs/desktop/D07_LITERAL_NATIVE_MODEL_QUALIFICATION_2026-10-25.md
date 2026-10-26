# Approved-model native protocol3 qualification

Scope: D07.03/.04/.05/.06 and supporting M07.01. Base accepted PR #192,
`470bdeaf`. Test source `00da6f6c` adds opt-in native-unit qualification using
the actual desktop `ModelManager` and its existing `EvaluationReservation`.
No production backend, owner, schema, prompt, profile or context policy changes.

## Evidence class and operation

These tests execute the approved installed Windows CPU worker and model through
`literal_v3::run_native_comparison`. They exercise the actual native reservation,
Host, durable Store, recorder, cleanup and report reader. They do not instantiate
a native WebView, use native IPC, render the UI, or control the desktop. Existing
UI5 and other native-render evidence remain separate historical qualifications.

The paired test creates an original scripted validated reference through the
existing evaluator. That preparation is synthetic plumbing, separate from its
subsequent real-model roles. It generates one paired scene, cleans up, resumes
the remaining three with another owned worker, cold-inspects the completed run,
and repeats completed resume with a callback that counts and refuses any lease.
The completed report and full artifact inventory must stay identical and the
callback count must be zero. Rollout runs all four scenes independently.

Both tests retain all 48 outcomes, including rejections, unavailable or dependency
evidence and narration fallback. They require observed load metrics and actual
role/raw-output evidence. They do not require a flattering all-passed result or
claim human quality acceptance. Synthetic raw outputs and diagnostics remain
local; fixtures and model assets are never copied into Git or uploaded.

Tests are `#[ignore]` and `#[cfg(test)]` only. They read two explicitly provided
installed asset paths, verify the fixed model basename, and use fresh internally
generated temporary destinations. They add no renderer action, arbitrary command,
file/shell execution service or remote debugging listener. Existing runtime
verification checks the actual worker/model before generation. Exact cleanup
objects are retained on uncertainty and later test admission is blocked; no
replacement owner or `mem::forget` workaround is used. Artifacts are preserved.

## Reproduction

From the repository root, set `LOCALLORE_SELECTED_NATIVE_TEST_RESOURCES` to the
already installed approved worker resource directory and
`LOCALLORE_SELECTED_NATIVE_TEST_MODEL` to the approved installed model file.
No test downloads assets. Use isolated local `TEMP`/`TMP` and build targets,
one worker/build at a time, and preserve the printed
`LOCALLORE_LITERAL_NATIVE_TEST_ARTIFACT` directory.

```powershell
cargo test --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --jobs 1 --bin locallore-desktop-spike models::literal_native_asset_tests:: --no-run
cargo test --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --jobs 1 --bin locallore-desktop-spike models::literal_native_asset_tests::approved_literal_paired_resumes_and_completed_read_is_zero_asset -- --ignored --exact --nocapture --test-threads=1
cargo test --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --jobs 1 --bin locallore-desktop-spike models::literal_native_asset_tests::approved_literal_rollout_records_all_outcomes -- --ignored --exact --nocapture --test-threads=1
```

Coordinator also used explicit external target directory, jobs1, incremental0,
dev/test debug0, empty `LIBSQLITE3_FLAGS`, clean source and terminal unchanged
source guards. Commands, logs, output and terminal records stay local.

## Environment

Windows NT 10.0.26300 x64; PowerShell 7.6.5; Rust/Cargo 1.93.1
(rustc01f6ddf75, cargo083ac5135, LLVM21.1.8). Intel i7-12700K, 12 cores/20 logical processors,
68,399,599,616 bytes installed RAM. This is a desktop measurement, not a phone
simulator or whole-app memory measurement.

Approved profile `qwen3-0.6b-q8-cpu-v1`: Qwen3-0.6B Q8_0 with F32 tensors,
model 639,446,688 bytes, Apache-2.0;
SHA256`9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`.
llama.cpp MIT commit`620d2225cc436ab0b001e3200e590e3b286ef9ab`, worker
SHA256`b5dd124e484c67c9dda5aebb2cdff1878ccefd0fba99aba4788e00a166f68434`;
template SHA256`57f1fd00f0013a2be96aa79b857391f27e23df5b5f847072b524c897e24d0361`.
Both files freshly matched before execution; native runtime verifies its held
assets again. Profile settings remain the committed profile-v1.json: CPU, 4 threads,
no GPU, context 4096, output 350/role, seed 42, temperature.7/top_p.8/top_k20,
60s operation deadline. Same scenario/profile/budgets do not mean identical
information channels or deterministic prose across machines.

## Results

Compile-only PASS in 19.73s at `00da6f6c`. Paired: 1 PASS in 730.29s, clean/unchanged source:
all 48 outcomes/four scenes, 2 physical loads/78 real roles, 24 same-input pairs,
completed cold inspect and repeated completed resume callback count 0/inventory identical.
The wall time includes scripted reference preparation, fixture and integrity
work plus real model execution and cold reads; it is not model latency alone.

| Paired arm | Expected outcomes | Committed | Real roles | Narration fallbacks |
|---|---:|---:|---:|---:|
| Literal |17/24|15|36|7|
| Relevant |24/24|21|42|8|

Literal failures: four UnknownReference refusals (courier-01/06/08/14), two safe
Agency refusals (16/19), and one committed scenario mismatch (20). All remain in
the report. Its failure categories overlap: scenario_outcome: 5,
no_matching_construction_receipt: 6, player_agency: 2. No-matching-receipt here is
the absence of an accepted matching construction receipt after a refusal; the
21 literal input captures themselves validate. The same starting snapshot does
not supply the literal arm with structured seed knowledge or an invented opening.
These finite results establish no general memory/model superiority.

All 42 generation-bearing rows have validated literal/Relevant construction and
privacy_passed=true. The 6 guard-only rows have not_applicable_guard and a false
privacy boolean: they carry no generation privacy proof. Do not label them a
privacy pass or infer a leak. Human reviewed: 0; quality accepted: false. A committed
action and a passing mechanical expectation do not approve its narration.

Native load observations: 248.5614/249.4702ms; actual preparation 8,654/8,646ms
(includes asset verification),17,300ms total. Accounting charges are 202,241ms
left/539,019ms right, not a whole-app performance result. Among 21 role-bearing
rows per arm, nearest-rank p50/p95/max evaluator elapsed_ms is 4,110/7,216/8,547
Literal and 22,071/25,016/25,334 Relevant. These are debug host row timers, with
different information channels and accepted/failed outcomes, not a controlled
quality-equivalent speed comparison or native UI response measurement.

Source binding: d4cca78ea2264d69765bc428a1a6b700167cc969722ba7f0d7bcfe2f55970916;
suite: 6e7172c6c8bedb4b82b703aac30b7b92c5a924d0203578cb2f027611d7def21a.
Rollout: 1 PASS in 524.98s at the same clean/unchanged source: all 48 outcomes/four
scenes and cold inspection/full inventory identical. 1 physical load/75 real
roles. Literal 15/24 expected, 13 committed, 33 roles, 5 narration fallbacks;
Relevant 24/24 expected, 21 committed, 42 roles, 8 fallbacks. One literal case 04 was
not_run_dependency and did not call generation. Three literal safe Agency
refusals (02/16/19), four UnknownReference refusals (01/06/14/20), and one
committed scenario mismatch (08) are retained. Overlapping categories are
no_matching_construction_receipt: 8, not_run_dependency: 1, player_agency: 3,
scenario_outcome: 5. All 41 role-bearing construction/privacy flags pass; six
guards and one dependency have no generation privacy proof. Human reviewed: 0; quality accepted: false.

Rollout has only 1 same-input pair: both states diverge after courier-01; it must
not be treated as 24 equivalent starting snapshots. First semantic/mechanical
divergence is courier-01 in both runs. Observed rollout load 244.3288ms and total
preparation 8,585ms; accounting: 91,246ms left/433,885ms right. Role-bearing row
nearest-rank p50/p95/max: Literal, 20 rows: 3,109/5,259/5,886ms; Relevant, 21 rows:
19,967/24,338/24,722ms, with the same row-timer limitations above.

Combined: 96 recorded outcomes, 153 real role calls, 3 observed loads, 28 narration
fallback flags. These are two finite runs with one installed profile. No human
review, repetition or enjoyment result is inferred from a mechanical match.

The initial formatting check failed only the new cfg(test) module declaration
order. Commit `398dab69` moves that declaration; no test body or production
behavior changes after the actual model runs. Formatting then PASS. At `398dab69`,
strict native all-feature/all-target Clippy PASS in 8.15s and existing model-manager
unit cohort: 27 PASS, 3 ignored, in 1.84s. Two ignored methods are the separately
executed real-model tests above; the third is the existing Windows symlink
privilege test, unrun. An existing synthetic poisoned-owner panic prints its
fixed message and is contained by its passing test; no production panic is
claimed. Both command terminal records assert clean/unchanged source.

Independent review found the model helper checked ownership only after helper
cleanup. Thus the00da comparison runs prove cleanup after the safe helper, not
a separate observation of unassisted producer return. The accepted owner-unit
evidence remains separate. Test correctionf452b8ae captures cleanup_complete
before safe cleanup and asserts that captured state, including completed resume.
A third ignored first-scene ownership smoke exercises the stronger observation;
its execution result is pending at this documentation source. It is separate
from the96-outcome comparison totals and adds no quality acceptance.

```powershell
cargo fmt --manifest-path apps/desktop/src-tauri/Cargo.toml --all -- --check
cargo clippy --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --all-targets --jobs 1 -- -D warnings
cargo test --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --jobs 1 --bin locallore-desktop-spike models:: -- --nocapture --test-threads=1
```

This slice changes only cfg(test) registration, test code and documentation.
The accepted PR #192 production build, frontend/type/normal-hook exclusions,
Android Rust 20 and dependency graph remain the relevant production compatibility
evidence; they were not rerun or relabeled as new measurements here. Android
receives no new dependency or code. No SDK/JVM/device/model installation occurs.

## Limits and next task

No human quality acceptance, whole-app peak memory or latency/performance distribution,
new native UI/IPC/render, native3 CLI, selected-case protocol3, physical-phone,
installation, packaging or release acceptance. Literal Director starts with no
invented opening or structured seed state; missing initial information and safe
rejections remain comparison results. Narrator remains Core-grounded. Finite
privacy sentinel checks do not prove universal semantic privacy.
