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

## Independent review regression execution

The 06b3746 cohort above remains historical. Independent review continued on the
coordinator diff; its original source-only reports remain preserved as handoffs.
Root actually ran the frozen F1/F2 pair: **0 passed / 2 failed**, then repaired
foreign-known-ID exclusion before decode and reset consumption before passive
recovery at085a72a. The unchanged pair passed afterward. A third frozen case
reproduced an external old reply adopting an unidentified new reservation:
**2 passed / 1 failed**. Repair038dfe9 permits only the awaited admission reply
to establish that reservation's operation ID; all three unchanged cases passed.
Both subsequent113/14 native cohorts passed, but their images were not inspected
and they are not the final render qualification.

The next frozen eight actual-controller/mock-IPC cases8b9b371/43ca19c
(imported5fc50cc/8a461af) actually produced **2 passed / 6 failed**. Malformed
Archive results, wrong preview-command kinds, malformed Fork outcomes and wrong
child identities lost global uncertainty, including after owner retirement.
Root0d067c2 shares the existing Archive completion checks between controller and
gate, retains five bounded preview identifiers before dispatch, and exports and
reuses the unchanged Fork outcome decoder. It retains no private story preview
or filesystem path. The same eight cases passed afterward. Existing gate-only
positive fixtures were transparently upgraded to native-shaped metadata at
a97670b (importedaeb2e30); original assertion bodies and labels remain unchanged.
See M07_BROKER_FIXTURE_METADATA_2026-10-23.md. These are mocked IPC tests.

At cleanaeb2e30a0060399ce17451f06464807075fe0f27 the full frontend verifier
passed strict TypeScript/schema, all existing suites and hook exclusion, including
63 memory cases,32 callback assertions,18 gate assertions,7 Root review cases,
3 incarnation cases,8 surface cases and the existing Fork63/6/9 and Timeline83.
These counts describe different suites, never additional native assertions.

Actual native cohort memory-native-4bae79ab-ff57-4741-b402-609f8da28e04 then
passed113 distinct assertions/14 WebView2 captures/two app processes, all four
runner children exit0. Summary SHA-256
0994109dba8e12a28770645ac037500f0bfaa853c6132cd69fee16a8a31ef9c7;
executable SHA-256
6c06f010b26d0be1a253d9d5915d1d10261cc3ae8e2a1dd94bd5d0a3269afb04.
Root opened all14 images and checked matching native-webview2 capture/snapshot
revisions and recorded input hashes (no mismatches). No overlap or horizontal
overflow was observed at1280x900/620x900; narrow wrapping and vertical scrolling
are intentional. Selected other story is head0/no receipt/no copied job; Sable
inspection is facts={} and observations=[], separate from the labeled original
player receipt. Complete job remains1 of1 through restart/passive reread. Initial
errors are exactly two expected native Cancelled, restart errors empty; no
frontend errors. Both app logs retain one Chromium shutdown1412 line, exit0.

Bounded subsequent source review found an unknown Fork terminal error category
is mapped to Wire by its controller but is not retained as global uncertainty.
Frozen new two-case packet54165b9/994d6dc (imported9ed9677/a0eab86) is not yet
executed at this documentation checkpoint. Known Cancelled must retain its native
meaning, remain locally uncertain, and recover only through explicit exact-child
read-only lookup. Root must execute unchanged RED/GREEN, reuse the same existing
closed error set, restore normal frontend, and record the final native cohort
before PR acceptance. No full M07/D07, model-quality, Android/device, hosted CI,
final packaging/reproducibility or release acceptance is supplied.

## Final desktop slice qualification

The two Fork-category cases above actually ran at a0eab86: **1 passed /1 failed**.
The failed assertion was retained global uncertainty for the unknown category;
known Cancelled/recovery passed. Repair ea03f72 exports one predicate backed by
ForkController's existing closed error set and reuses it in BrokerRetention.
No native error category, canonical rule or cancellation meaning changed. Both
unchanged tests and the full frontend verifier passed afterward, and the new
checker is included in routine verification.

Final clean executable/frontend source:
`ea03f724ede6672ad147f93d4f1d052dfc495a28` (accepted main5e18015 included).
Native cohort `memory-native-d273571f-9fd2-4a9c-96d6-a362cd649545` passed
**113 distinct assertions /14 application-owned native WebView2 captures /
two app processes**; four runner children exit0. Summary SHA-256:
`7432eb86f46654cec39c7a513fe2e54a53c7ced82a041de2186df24aa2c689e0`.
Native executable SHA-256:
`63c2a391f4f32d9de3e154fbfe321a6db294e5d8385690c26434148162068e91`.
Root opened all14 final PNGs, rechecked capture/snapshot revisions and all recorded
source/executable hashes. The development frontend hash remains recorded in the
summary; the current dist file was deliberately replaced by the normal build.
The same coherent scope/revision/pending/receipt/error/observer and layout checks
reported above passed inspection, including other-story head0/no receipt,
Sable facts={} and observations=[], and completed1-of1 after restart/reread.
Initial107 check entries and restart20 overlap; they are113 distinct assertions.
Initial buffer exactly2 expected native Cancelled/restart0; no frontend errors.
Both app stderr logs retain one shutdown1412 diagnostic, exit0. No model call,
device run, desktop capture/input or power-loss claim.

Normal frontend was restored with the full verifier after this final cohort:
strict TypeScript/schema, all routine controller/mock suites and development-hook
exclusion PASS. Normal dist/app.js SHA-256:
`604ec37bceaa5a50bd60d094933ba32cab32dc759a576278a49ee03dc247f046`.
Final local logs: fork-category-red.log, fork-category-full-green.log,
category-native-final.log and normal-final.log in memory-controls-artifacts.
No source or artifact outside the task-owned worktrees/targets was controlled.

The normal65/native-development69+2-contract and strict Rust checks atccff2fa
remain applicable: `git diff --exit-code ccff2fa HEAD -- apps/desktop/src-tauri`
is0 at this final source. Shared Rust and Android source have no changes in this
desktop slice; accepted Android fork PR124 carries its182-JVM/compiled-APK/lint
compatibility evidence. Android device/framework execution remains unavailable.
Original source-only handoff reports are historical; this coordinator report
records which tests were actually executed and supersedes their unrun status.
This qualifies only explicit desktop shared-memory maintenance and retained
broker presentation, not the full M07/D07/D08/D09 milestones or a release.
