# Narration-validation diagnostics v1: scoped qualification

2026-10-29. Refs #9 **M05.03/M05.04**; supports #29 **D07.04**.
**Implemented; focused, portable, Eval and scoped native compatibility checks measured.**
This note records coordinator-run evidence at source
`223b6a3f22eb35d9c2d1aedb7b6ed4e5c7f8ea19`. It is not task acceptance,
release qualification, a model-quality result or permission to merge.

## Scope and authority

The existing precommit narration validation now offers a provided default-no-op
`TraceSink::narration_validation` callback. Its opaque, fixed-size, Copy native
metadata exposes version, outcome, error category and an optional reason.
Only the two existing generated-scene refusal branches assign
`SceneFirstPerson` or `SceneUnapprovedMovement` when actually reached.
Other actual Narration failures are `Unclassified`; other errors have no reason.
Accepted means that finite validation call returned Ok. It establishes neither
final commit nor semantic truth, privacy acceptance or prose quality.

A crate-private failure carries the original Error through one validation pass.
The original stage callback runs first, the new panic-isolated callback second,
then the existing Scene4 cancellation poll precedes fallback. Trace diagnostic
overhead uses existing accounting. The used scene-record compatibility function
projects one detailed call. Two unused private helpers were renamed directly
under the accepted contract refinement; no warning suppression was introduced.

The four production paths are `crates/locallore/src/turn_trace.rs`, `play.rs`,
`play/scene_narration.rs` and `play/scene_narration/renderer.rs`.
The slice adds no validation or cancellation pass, provider/repair request,
model owner, persistence writer, public constructor, Serde payload, IDs/text,
PlayRecord/Report4 field or permission. Existing prompts, schema/policy versions,
canonical events, receipts, fallback, retry/replay and observer rules remain
the compatibility boundaries checked below.

## Frozen provenance

The [contract](D07_SCENE_NARRATION_DIAGNOSTICS_CONTRACT_2026-10-28.md) and
independent oracles preceded production:

| Step | Source |
| --- | --- |
| Original contract / integrated contract | `5a4bdaa5` / `cfe99672` |
| Original independent test / integrated test | `6d65e85b` / `c21d1f02` |
| Root test-only child registration | `0ac20cef` |
| Root private-helper contract refinement | `da3ef8b6` |
| Production / integrated production | `600b8a5d` / `26fea6ff` |
| Formatted qualification source | `223b6a3f` |

Independent source review at `26fea6ff` reported no blocker; that is separate
from execution. Root's rustfmt-stdout equality record proves that formatting
the original 557-line test yields the current test after newline normalization.
The ten test functions remain. Frozen SHA256:
`31819a8719e45edfe5f971ebac6050f17c7a236487a6e5b6047c1fee06f87693`;
formatted SHA256:
`8bb0a4e9a472cf1138f6b34467d7e76a32c4d0156f8754004137258aca6816d3`.

## Measured checks and preserved failures

Commands below ran from the physical D: repository with existing locked/offline
dependencies. Private target-directory arguments are replaced with
`<owned-D-target>` and the private absolute Node executable with `node`;
local process records retain exact paths, arguments and timings.

```text
cargo test --manifest-path Cargo.toml -p locallore --lib --features host --locked --offline --target-dir <owned-D-target> play::scene_narration::diagnostics_review_tests:: -- --test-threads=1 --nocapture
cargo test --workspace --exclude locallore-desktop-spike --all-features --locked --offline --target-dir <owned-D-target> -- --test-threads=1
```

| Actual run at clean `223b6a3f` | Result | Duration |
| --- | --- | --- |
| Focused host-enabled library filter | 10 passed, 0 failed, 0 ignored; 73 filtered | 0.29s test; 8.7440136s command |
| Portable workspace, excluding desktop | 1,029 passed, 0 failed, 11 ignored across 142 test/doc-test result groups | 511.1091717s command |
| Full Eval with `local-model` feature | 274 passed, 0 failed, 17 ignored across 33 test/doc-test result groups | 3132.3080431s command |

These process records report exit0, source unchanged and an empty dirty list.
The aggregate was independently recounted from the bounded portable log.
The focused run uses the real Engine/Play pipeline, a recording synthetic
provider and TraceRing-backed test sinks. Its ten functions cover:

- Default/no-op, disabled/retired/mismatched sinks and provider/budget parity.
- Both existing scene recipes, reached refusal codes and first-failure order.
- Earlier generic/non-Narration errors and malformed Narrator parsing.
- Accepted output, including a documented existing finite semantic gap.
- Stage/hook cancellation before excluded fallback, and cancellation after Ok.
- Stage/hook panic isolation, exact cancellation-predicate counts, retry/replay,
  canonical bytes, legacy controls and unchanged old wire keys.

Expected caught synthetic observer panics remain visible in the passing focused
log. They are deliberate isolation cases, not suppressed failures.

Earlier setup failures remain distinct:

| Attempt | Actual result and classification |
| --- | --- |
| `cargo fmt --manifest-path Cargo.toml` on the virtual workspace | Missing `--all`; “Failed to find targets”; no source change. Setup failure. |
| Initial focused command at `26fea6ff`, otherwise as above but omitting `--lib --features host` | Existing `m08_narration_ownership_review` import of host-gated `locallore::inspection` failed to compile; exit101 in 35.2000800s, source unchanged. No ten-test execution or behavioral RED. |
| First strict all-feature/all-target workspace Clippy at `223b6a3f` | Exit101 in 37.6264941s: duplicate test-only attribute and `Vec::len() >= 1` in the new test child. No production warning or lint allowance. |

Test-only `d4dc966d` removes the redundant inner `cfg(test)` while preserving the
parent's test-only registration, and uses equivalent `!is_empty()`. Assertions,
fixtures and all four production files remain unchanged. Focused tests and strict
lint passed after those corrections, as recorded below. The earlier broad passes
remain at their actual `223b6a3f` source and are not relabeled as reruns.

The additional measured Eval command was:

```text
cargo test --manifest-path crates/locallore-eval/Cargo.toml --features local-model --locked --offline --target-dir <owned-D-target> -- --test-threads=1
```

The feature enables the existing local-runtime test surfaces. These are Rust
synthetic/recorded-fixture regressions, not a new approved-model invocation or
another human-quality cohort. Explicitly ignored genuine/historical tests remain
ignored; no frozen packet is regenerated.

Root's recorded environment is Windows, Rust/Cargo1.93.1, one heavy job,
one Cargo build job, incremental disabled and dev/test debug0. TEMP/TMP were
process-local `D:/Dev/_Temp`; source, Cargo cache and targets were on D:.
The documentation author read source and bounded result records only and ran
no compiler, formatter, Node, browser, app, model/assets, device or desktop tool.

## Later compatibility checks at clean `a84e0799`

All four production files are byte-identical to `223b6a3f`. Only the two reviewed
test lint corrections and qualification documentation intervene. Each following
process record reports exit0, unchanged source and an empty dirty list:

| Check | Actual result | Command duration |
| --- | --- | --- |
| Same focused host/library filter | 10 passed; 0 failed; 73 filtered | 8.4569509s; 0.28s test |
| Strict all-feature/all-target workspace Clippy | Passed | 12.7085590s |
| Android Rust host compilation | Passed | 3.3442320s |
| Workspace formatting | Passed | 1.8296697s |
| Core without default features | Passed | 3.7248167s |
| Normal Windows native build; unlaunched | Passed | 24.3015048s |
| Normal Windows native strict Clippy | Passed | 9.3931504s |
| Development native suite, serial | 282 unit + 2 contract passed; 0 failed; 11 ignored | 723.9802339s |
| Full frontend checks/build | Passed; normal frontend excludes development hooks | 14.4595115s |
| Android normal dependency graph for aarch64 | Expected root present; zero desktop/Eval/local-runtime/Tauri/Wry/WebView2 packages | 0.4143478s |

```text
cargo clippy --workspace --all-features --all-targets --locked --offline --target-dir <owned-D-target> -- -D warnings
cargo check -p locallore-android --locked --offline --target-dir <owned-D-target>
cargo fmt --all --manifest-path Cargo.toml -- --check
cargo check --manifest-path Cargo.toml -p locallore --no-default-features --locked --offline --target-dir <owned-D-target>
cargo build --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --target-dir <owned-D-target>
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --all-targets --target-dir <owned-D-target> -- -D warnings
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --features dev-harness --target-dir <owned-D-target> -- --test-threads=1
node apps/desktop/verify-frontend.mjs
cargo tree --manifest-path Cargo.toml -p locallore-android --target aarch64-linux-android --locked --offline --edges normal --prefix none
```

The attempted normal `harness_contract` target stopped with exit101 in
0.3885447s: that target requires `dev-harness`. No tests ran in that attempt.
The valid development command above includes its two passing contract tests.
The feature requirement was preserved. Android host compilation and dependency
metadata establish neither Android ABI compilation nor device/emulator execution.

## Actual retained native read and source-mismatch refusal

The separate development command `node apps/desktop/comparison-run-harness.mjs
--native-scene-review-v1` ran against the existing immutable synthetic cohort,
with explicit retained-packet, approved-publication and owned target paths in
process-local environment variables. It executed the real frontend controller,
native IPC and hidden, unfocused WebView2 application-owned rendering. No desktop
input or desktop capture was used. This is native execution, not a headless render.

At clean `a84e0799`, 2026-10-29 09:53:39.2591654Z–09:54:48.2920328Z:
**257 checks passed, 12 PNGs, zero recorded broker errors**, 69.0328674s.
The retained completed report opens. Explicit resume returns the authoritative
`EvaluationSourceMismatch` / `source_mismatch`, expected after changing Core.
This is a verified historical-read/refusal journey, not a successful completed
resume at the new source. No stored source fingerprint was rewritten.

All twelve images were individually inspected; nine artifact views also have
positive, in-viewport heading/source/outcome rectangles without selection-header
overlap. The original `full-idle.png` initially appeared blank in the inspection
tool. Read-only PNG decoding found 15,730 bright pixels and 951,300 pixels unequal
to its first pixel. An encoding-only derived preview showed the readable UI;
decoded RGBA bytes match exactly, SHA256
`7cf95d7d86a403f96a0e497e7c9b0ead159eced80d64e87e847033ae84202cd4`.
Original PNG SHA256
`fffdeb43e969a105ff5ad61cab0856b1ff9a0df19fe00420ecf1d18e734bb908`
is unchanged. This resolves an inspection-preview anomaly; it is neither a
repaired capture nor a rerun. No capture-readiness code was changed.

All 2,072 retained result files remain byte-identical, aggregate SHA256
`f22cd3ec7c40c8870684b025fe1bcd909a4664e34f92f552779f2068bce429e5`.
Original workspace SQLite remains absent. Sequence, consent and retained-Eval
observations remain zero, with no active owner. These observations support the
source-reviewed no-inference path; they are not an independent SDK-load counter.
All 32 known child executions closed; unknown drain is false. Normal products
were restored successfully and left unlaunched. The frozen model run and its
human assessment are unchanged.

Environment: Rust/Cargo1.93.1, Node24.22.1, PowerShell7.6.5,
WindowsNT10.0.26300.0. The native user agent reports Chromium/Edge156.0.0.0;
an independent installed WebView runtime build was not obtained. These checks
do not qualify every native journey or a release.

## Remaining scope and limits

Local evidence is retained under the `d07-narration-diagnostics-*` process/log
names, format-equality JSON, the fourth native review process/packet, twelve-image
review manifest and identical-pixel decoder proof; private absolute paths and
raw model material are excluded from this public note. Root will append actual
later results and independent review without replacing the preserved failures.

Phase1 leaves RingSink retention, authorized Host reads, versioned Eval evidence,
Report4 and UI display to separate adapter contracts. Historical absent causes
remain unavailable: the callback cannot backfill the frozen 30 generic fallback
causes. No captured prose, report, input, recipe or human assessment is repaired.
Both original and newer human assessments remain **needs improvement**.
This slice does not improve semantic grounding or model prose.

The focused [PR #251](https://github.com/OptimumAF/LocalLore/pull/251) remains a draft stacked above open, unmerged draft
[PR #247](https://github.com/OptimumAF/LocalLore/pull/247) and its dependencies;
the other owner's open, unmerged draft
[PR #225](https://github.com/OptimumAF/LocalLore/pull/225) is not accepted or
authorized for merge by this work. M05.03/M05.04 and D07.04 remain in progress
and unchecked. Next: independent evidence review, then the separately contracted
bounded RingSink retention slice. The focused callback slice has a reviewable
local verification gate; this is not acceptance of its unmerged dependency stack.
