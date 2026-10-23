# Desktop shared-memory controls: coordinator verification

Partial #11 M07.01/.03/.04 and #29 D07.02/.06. Accepted base main
`946c73ce354aac8fa3c6ff1915269683f0a3da5d`; branch
`impl/m07-desktop-memory-integration`. Agent release6376693729 transferred the
packet to Root; coordinator claim6376777162 was corrected to the existing task
IDs in6376790914. This is a bounded consumer of the accepted Rust maintenance
port, not a second persistence owner, compiler, model or background scheduler.

## Actual regressions and repairs

The original source handoff remains attributed in
`M07_MEMORY_INTEGRATION_2026-10-23.md`. Root retained actual pre-fix worktrees:

| Source/check | Actual result |
| --- | --- |
| `ace6dd6`, original30 callback assertions | exit1 at first `status-context-notification-retires-before-native-dispatch`; the fail-fast runner did not execute all30 |
| `4c6c1df`, added Stop notification assertions | exit1 at `stop-context-terminal-notification-cannot-install-old-followup-notice` |
| Current corrected controller | all32 callback assertions PASS unchanged, aside from formatting |
| Root frozen six gate cases `cd8d9dc` | 0PASS/6FAIL: malformed memory reply certainty after context change, and two valid native archive picker phases |
| Gate repair `346029f` | six PASS; reuses the existing strict memory decoder before accepting a result and recognizes picker phases |
| New seventh case `152ea61` | 6PASS/1FAIL: prior consumed status was mistaken for an unread result when the next action announced Busy |
| Consumption latch/subscriptions `f0f1cae` | all7 PASS with the full frontend verifier |

The pure18-case gate fixture was completed at647d7ba/88b3a9c with actual
version/nested maintenance/action metadata before the decoder repair. All18
assertions are unchanged; the corrected fixture passed against the old gate
before repair and against the new gate afterward. The four malformed-result
regressions remain malformed and rejected. This fixture correction is not
reported as an unchanged wire payload or a native test.

## Native failures retained

Clean `ccff2fa` cohort `memory-native-bd2f7974-d53e-4b6f-8d83-d732ea16e1e2`
failed `explicit-admit-ready` after passive Status: the new action's Busy state
made the presentation gate reread previous consumption as incomplete. The
seventh frozen regression above reproduces this application defect.

Clean `f0f1cae` cohort `memory-native-4ad17049-4518-450a-b534-e3f455f9c606`
passed102 assertions/generated12 initial captures, then failed the fixture's
zero-error-buffer assertion. The exact two native Cancelled entries come from
the deliberately cancelled held-Prepare gameplay turn. Existing IpcGateway
records both cancelled-status replies; actual final phase was cancelled,
pending=null, visibleError=null and canon unchanged. The existing timeline
native suite independently expects that exact pair. Original failed report,
images and logs remain local; the old zero-buffer assertion was explicitly
superseded in #11 comment6376925946, never called passing.

Test-only correction06b3746 requires zero buffer entries immediately before
intentional cancellation, exactly two native Cancelled immediately afterward,
actual cancelled turn/no pending/no visible error, no additional entries through
completion, and zero entries after restart. It clears or filters no errors and
changes no production error handling. This is a corrected harness expectation,
not proof that native stderr is empty.

## Actual integrated cohort at06b3746

Clean source `06b3746c1774d9c7b6ae3fd1b5b8a750f9ffb98f` passed **113 distinct
assertions,14 actual application-owned WebView2 captures,two app processes**.
Local cohort `memory-native-25e11fcc-20f5-49f4-8cd6-9982a90727e6` summary SHA-256
`1cb109224576884c2dc2fe8b38823d7fb0a2d15219baede0d2e400897806291e`.
All four runner children exit0/truncated=false. Native executable SHA-256
`43fafc30efc2420837685c5e9ec416f09528dfc7c2e2429dba639665356def4c`.

Root opened all14 PNGs: passive/admitted/pending/cancelled/pruned/unknown/
observer/switched/other/turn-busy/complete/narrow/restarted/reopened. Scope,
revision, player/inspection observer, job/cursor, pending operation, player
receipt and visible error agree with semantic snapshots. Capture metadata
reports native-webview2 and matches every snapshot UI revision. Recorded source
input hashes were rechecked. The selected other story correctly shows head0,
no receipt and no copied job. Sable's inspection has facts={} and observations=[];
the separately labeled original player receipt is retained. Completed restart
status remains1 of1 after a repeated passive read, without another step.

No overlap or horizontal overflow was observed at1280×900 or620×900. Narrow
labels stack, controls wrap, receipt text wraps, and vertical page scrolling is
intentional. This is inspection of the app's own render artifacts, not desktop
capture, input injection or window activation.

Initial report has exactly2 expected native Cancelled categories; restart has0.
All frontend error categories remain absent. Both app stderr logs retain the
Chromium shutdown diagnostic `Failed to unregister class Chrome_WidgetWin_0.
Error = 1412`, one per process, with exit0. Reduced app-reported UA is
Chrome/Edg155.0.0.0 on Windows10.0; this is not the full loaded-runtime version.
No real model was called. Restart is clean process restart, not a power-loss or
arbitrary process-death qualification.

## Other actual checks and reproduction

Windows11 Pro10.0.26300 x64; Rust/Cargo1.93.1; Node24.22.1; existing cached pinned
dependencies/MSVC19.34.31937/SDK19041. Ordinary uncapped SQLite. Own D outputs,
TEMP/TMP, one heavy suite at a time; no download or SDK change.

Normal native suite atccff2fa:65PASS/0FAIL/1 existing Windows symlink privilege
ignore. Development suite:69PASS/0FAIL/1 same ignore plus2 contract PASS. These
include the original five actual maintenance adapter/Host/Store tests. Both
strict Clippy configurations passed. Rust source is unchanged through06b3746.
Scoped rustfmt and changed frontend Prettier checks passed. Full frontend
verifier passed before the cohort and after restoring the normal frontend:
strict TypeScript/schema, existing suites, original63 memory/mock assertions,
32 callback assertions,18 pure gate assertions,7 Root review cases, original
fork/timeline and their6+9 review cases, and normal test-hook exclusion. These
counts are different evidence layers and must not be added as native coverage.

```powershell
$env:CARGO_BUILD_JOBS='1'
$env:CARGO_PROFILE_DEV_DEBUG='0'
$env:CARGO_PROFILE_TEST_DEBUG='0'
$env:CARGO_INCREMENTAL='0'
$env:LIBSQLITE3_FLAGS=''
$env:LOCALLORE_CHECK_OUTPUT_DIR='<own-local-check-output>'
node apps/desktop/verify-frontend.mjs
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --offline --locked --target-dir <own-native-target> -- --test-threads=1
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --offline --locked --features dev-harness --target-dir <own-native-target> -- --test-threads=1
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --offline --locked --all-targets --target-dir <own-native-target> -- -D warnings
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --offline --locked --all-targets --features dev-harness --target-dir <own-native-target> -- -D warnings
$env:LOCALLORE_M07_MEMORY_ARTIFACT_ROOT='<own-local-artifact-root>'
$env:LOCALLORE_M07_MEMORY_TARGET_DIR='<own-native-target>'
node apps/desktop/memory-harness.mjs
node apps/desktop/verify-frontend.mjs
```

Normal restored dist/app.js SHA-256 at06b3746:
`bff83b330006302d2979f4512115b98063a1e8c89648f9d3a201b0e6cbc4701a`.
Local logs in memory-controls-artifacts include callback-red.log,stop-red.log,
broker-review-red.log,consumption-red.log,frontend-consumption-green.log,
native-normal.log,native-dev.log,strict-normal.log,strict-dev.log,
native-cohort-first.log,native-cohort-consumption.log,
native-cohort-current-final.log,normal-restored.log and format-final.log.
Profiles/databases/snapshots/renders/raw logs stay local and gitignored.

## Remaining review gate

Independent source review found F1/F2 after the passing06b3746 cohort. Frozen
two-case tests d532c43 (importedc521c0c) and report3e7e994 (importedaee07c5)
identify late foreign-ID poisoning before the current decoder and passive
recovery inheriting an old consumption latch. See
`M07_BROKER_RETENTION_REVIEW_2026-10-23.md`. Both new cases are **unrun** at this
checkpoint. Root must execute unchanged RED, make narrow repairs, run unchanged
GREEN/full frontend, repeat the current native cohort and inspect its images
before a PR/acceptance. The earlier113-pass cohort is historical evidence, not
proof of those future repairs. No full M07/D07, Android/device, model-quality,
hosted CI, final packaging/reproducibility or release acceptance is supplied.
