# Native narration diagnostic retention: partial qualification

2026-10-29. Refs #29 **D07.04**; supports #9 **M05.03/M05.04**.
**Implemented; focused and scoped compatibility checks measured; broad checks pending.**
Measured source: `ea8bdc2a6f4d165feca9c30807f55893995c33a3`.
This is a native in-memory collector slice, not full cause reporting, task
acceptance, model-quality qualification, device evidence or merge authority.

## Scope and frozen boundaries

The [accepted retention contract](D07_NARRATION_DIAGNOSTIC_RETENTION_CONTRACT_2026-10-29.md)
extends the existing Phase1 callback with one private optional diagnostic per
`LiveAttempt`. RingSink forwards through its existing best-effort `try_lock`;
`NarrationValidationReadV1` and `read_narration_validation_for_owner` provide a
separate native read. The sole production path is
`crates/locallore/src/turn_trace.rs`.

First valid write wins. Status order is Disabled; stale/foreign/unowned/retired
Dropped; truncated flag OR Truncated outcome yields Truncated; finished/duplicate Dropped;
missing/mismatched last NarrationValidation stage/outcome/error InvalidMetadata;
then Recorded. A write appends no stage, advances no clock and changes neither
serialized bytes nor eviction. It cannot repair a dropped stage or callback.

Read authorization keeps Scope, Forbidden, InvalidSelection order before
availability. Both turn and attempt are required, with exact owner, scope,
revision and observer matching. Disabled, retired, absent or truncated data is
Unavailable. Ordinary finish can retain an earlier accepted/rejected decision,
including after Failed/Cancelled/Stale finish. That decision is not relabeled
as final commit or fallback. Clear, disable/re-enable, owner cleanup/retirement,
eviction and stale opaque handles cannot revive a slot.

Frozen tests require the Option payload to be at most32 bytes and at most1,024
bytes across the existing32-attempt ceiling. Existing24-stage/65,536-byte
serialized budgets and trace-v1 keys remain unchanged. There is no new registry,
owner, history, persistence, Serde field, capture kind, PlayRecord/Report4 field,
provider/validator/cancellation pass or permission. Scoped native readers still
depend on their caller's current session/head authority and bounded lock policy.
An `&TraceRing` read cannot detect mutex poison; busy/poisoned callers report
Unavailable. Metadata consistency is not authenticated origin or a generation
grant. No forensic erasure or independent TTL guarantee is introduced.

## Test-first provenance

[Phase1 qualification](D07_NARRATION_VALIDATION_DIAGNOSTICS_QUALIFICATION_2026-10-29.md)
and its independent scoped evidence gate precede this production allocation.
The original accepted retention contract is `d7da151b`; the original independent
ten-function source freeze is `810f5cae` (integrated as `a5e57c21`). Root integrated
the Phase1 evidence precision fix `08e847f9` before registering/formatting the
retention child at `c3f89968`. Production `4458132c` integrates as `ea8bdc2a`.
The independent test author reviews production separately; execution does not
replace that source/evidence review or owner acceptance.

`d07-retention-oracle-format-equality1.json` records exact equality after removing
the redundant whole inner `cfg(test)` line and formatting with rustfmt1.93.1;
the parent's outer test-only registration remains. Original SHA256:
`a88f1e96b5e60eacedf3fffaf6ca843b34523d05b003a67ea606533b26b8663f`;
registered/formatted SHA256:
`dcf6c98e4447bdd37ae8b6b9989a1b3394475a424bcaa8ed05e90a63d60136c6`.
No fixture/assertion change was needed. The first equality helper removed only
the attribute text and left its blank line; that comparison failed with source
unchanged. The corrected helper removes the whole line and proves equality.
This preserved helper setup failure is not a behavioral RED or test execution.

## Actual completed checks

All six completed process records below report clean, unchanged `ea8bdc2a`,
exit0 and empty dirty lists. Private target arguments are normalized to
`<owned-D-target>`; local process records retain exact arguments and timestamps.

| Check | Measured result | Command duration |
| --- | --- | --- |
| Independent retention filter | 10 passed, 0 failed, 0 ignored; 83 filtered; 0.32s test | 9.1575873s |
| Existing Phase1 diagnostic filter | 10 passed, 0 failed, 0 ignored; 83 filtered; 0.28s test | 0.5767882s |
| Workspace format check | Passed | 1.8622533s |
| Strict all-feature/all-target workspace Clippy | Passed | 34.6928577s |
| Core without default features | Passed | 1.9497234s |
| Android Rust host compilation | Passed | 3.2497157s |

```text
cargo test --manifest-path Cargo.toml -p locallore --lib --features host --locked --offline --target-dir <owned-D-target> turn_trace::narration_diagnostic_retention_review_tests:: -- --test-threads=1 --nocapture
cargo test --manifest-path Cargo.toml -p locallore --lib --features host --locked --offline --target-dir <owned-D-target> play::scene_narration::diagnostics_review_tests:: -- --test-threads=1 --nocapture
cargo fmt --all --manifest-path Cargo.toml -- --check
cargo clippy --workspace --all-features --all-targets --locked --offline --target-dir <owned-D-target> -- -D warnings
cargo check --manifest-path Cargo.toml -p locallore --no-default-features --locked --offline --target-dir <owned-D-target>
cargo check -p locallore-android --locked --offline --target-dir <owned-D-target>
```

The ten new functions exercise actual synthetic Engine/Play → RingSink → native
read for both scene recipes and finite reason precedence; stage alignment and
first-write rules; authorization before availability; retirement, teardown,
finish, truncation, count/byte pressure and eviction; foreign/unowned handles;
busy/poisoned locks; cancellation/panic; and retry/replay/provider/canonical/wire
parity. Explicit collector controls copy actual emitted diagnostics and stage
metadata; they do not authenticate origin. Expected caught synthetic observer
and mutex-poison panics remain visible in the passing focused log.

The coordinator uses Windows and Rust/Cargo/rustfmt1.93.1, locked/offline existing
dependencies, one heavy job, one Cargo build job, incremental disabled and
dev/test debug0. Process-local TEMP/TMP are `D:/Dev/_Temp`; project source,
Cargo cache, targets and local records reside on D:. The documentation author
performed source and bounded record reads plus Git checks only, with no compiler,
formatter, Cargo, Node, browser, app, model/assets, device or desktop execution.

## Pending gates and next step

At this freeze the coordinator's serialized portable-workspace/development-native
sequence is in progress. Neither completed process record exists yet; both broad
results remain pending here. No prior Phase1 suite result is relabeled as a
Phase2 rerun. Independent source/evidence review and later qualification updates
remain Root-owned. Android host compilation is not an Android ABI/device run;
these Rust tests are not native IPC/WebView rendering or model inference.

Local `d07-narration-retention-*-process.json`/logs and the format-equality record
retain bounded evidence. Private absolute paths and raw model material stay out
of this public note. No new model cohort, historical-cause backfill or captured
output repair occurs. Original and newer human assessments remain
**needs improvement**. The finite validator's semantic gap and prose quality are
unchanged.

Host/Eval/IPC/wire/UI retention or display requires separate contracts and
claims. Historical absent causes stay Unavailable. Full M05.03/M05.04 and D07.04
remain in progress and unchecked. Next: Root records completed broad results,
obtains independent review and prepares the focused retention PR stacked above
the Phase1 [PR #251](https://github.com/OptimumAF/LocalLore/pull/251) dependencies.
This document authorizes no merge, release or acceptance of that stack.
