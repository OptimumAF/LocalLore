# Narration-validation diagnostics v1: partial qualification

2026-10-29. Refs #9 **M05.03/M05.04**; supports #29 **D07.04**.
**Implemented; focused and portable checks measured; broader gates pending.**
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
dependencies. Only the private target-directory argument is replaced with
`<owned-D-target>`; local process records retain the exact argument and timings.

```text
cargo test --manifest-path Cargo.toml -p locallore --lib --features host --locked --offline --target-dir <owned-D-target> play::scene_narration::diagnostics_review_tests:: -- --test-threads=1 --nocapture
cargo test --workspace --exclude locallore-desktop-spike --all-features --locked --offline --target-dir <owned-D-target> -- --test-threads=1
```

| Actual run at clean `223b6a3f` | Result | Duration |
| --- | --- | --- |
| Focused host-enabled library filter | 10 passed, 0 failed, 0 ignored; 73 filtered | 0.29s test; 8.7440136s command |
| Portable workspace, excluding desktop | 1,029 passed, 0 failed, 11 ignored across 142 test/doc-test result groups | 511.1091717s command |

Both process records report exit0, source unchanged and an empty dirty list.
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

Root's recorded environment is Windows, Rust/Cargo1.93.1, one heavy job,
one Cargo build job, incremental disabled and dev/test debug0. TEMP/TMP were
process-local `D:/Dev/_Temp`; source, Cargo cache and targets were on D:.
The documentation author read source and bounded result records only and ran
no compiler, formatter, Node, browser, app, model/assets, device or desktop tool.

## Pending gates and limits

At this documentation freeze, Eval/local-model tests are running. Strict
workspace Clippy, Android Rust host compatibility and corrected workspace format
verification remain queued; normal/dev desktop native checks, frontend
compatibility and any justified no-inference native read/resume remain pending.
No completion is inferred from a running log or an earlier branch's results.
Android Rust host checks will not qualify an Android ABI, emulator or physical
device. Headless/static tests will not qualify native WebView execution.

Local evidence is retained under the `d07-narration-diagnostics-*` process/log
names, format-equality JSON and coordinator draft1; private absolute paths and
raw model material are excluded from this public note. Root will append actual
later results and independent review without replacing the preserved failures.

Phase1 leaves RingSink retention, authorized Host reads, versioned Eval evidence,
Report4 and UI display to separate adapter contracts. Historical absent causes
remain unavailable: the callback cannot backfill the frozen 30 generic fallback
causes. No captured prose, report, input, recipe or human assessment is repaired.
Both original and newer human assessments remain **needs improvement**.
This slice does not improve semantic grounding or model prose.

The planned focused PR remains stacked above open, unmerged draft
[PR #247](https://github.com/OptimumAF/LocalLore/pull/247) and its dependencies;
the other owner's open, unmerged draft
[PR #225](https://github.com/OptimumAF/LocalLore/pull/225) is not accepted or
authorized for merge by this work. M05.03/M05.04 and D07.04 remain in progress
and unchecked. Next: Root completes the pending checks, records exact results,
obtains independent review and presents the focused PR at its reviewable gate.
