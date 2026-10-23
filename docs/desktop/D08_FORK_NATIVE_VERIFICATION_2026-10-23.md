# D08.04 desktop fork UI/native verification

Partial D08.04 / M08.01–.02 implementation, coordinator review pending; full
milestones remain unchecked. Same isolated `impl/d08-desktop-fork` worktree,
base `5e44ea91bfa9e93ecf583e31a26937efdfa96366`. Read AGENTS/README/workflow,
current #3/#30/#12 and accepted PR109 source/claims before implementation.
Claims and additions are linked in the original adapter and journey-freeze reports.
Root owns integration with newer accepted main/Core2.4 and final PR/acceptance.

## Implemented boundary

Normal UI exposes an explicit new saved timeline at a selected completed receipt
boundary. It displays selected story/observer/head, selected player receipt with
its original scope, original fork parent/head/fork point, stable child identity,
consent, pending operation, visible failure and confirmed child/current head.
The next-request selector is distinct from the immutable exact request.
Consent display is owned by the same frontend controller as confirmation.
Opening a confirmed child uses the existing explicit resume path.

Both normal/dev native handlers, Tauri AppManifest/capability admission and three
generated exact command permissions are integrated. Native `fork_start` constructs
accepted shared typed Host input; `fork_lookup` only reads the existing bounded
catalog. The existing ArchiveBroker provides one worker, registration, operation
counter, status/cancel/retire/drain. Frontend cross-surface admission preserves its
terminal acknowledgement until the originating controller consumes it. No new
Store, canonical state owner, author grant, inference or memory implementation.

The exact four-field recovery identity is synchronously written to application
WebView local storage before dispatch; failure prevents dispatch. It contains
scope/IDs/revisions, not prose/receipts/models. It is a recovery hint, never
canonical authority. Restore and selected-context changes permit lookup only;
absence never executes a fork. Same-context exact retry is explicit. Cancellation
does not prove an earlier lost acknowledgement never committed. OS/browser cache
deletion or power loss durability of this small UI hint is not qualified.

## Executed checks and source attribution

Windows 11 Pro 10.0.26300 x64; Rust/Cargo 1.93.1; Node 24.22.1, pinned cached
TypeScript 7.0.2/esbuild 0.28.2/React 19.3.1/Prettier 3.9.10. No package installation
or pin/permission-scope expansion. Existing MSVC/Windows SDK/native cache reused;
this is not a clean toolchain/package reproducibility qualification.
The actual rendered WebView reports reduced navigator user agent
`Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36 Edg/155.0.0.0`.
This records the actual app-reported UA, not the full installed/loaded WebView2
build number, which is unavailable in this evidence.

All Cargo commands used one reserved ordinary `archive-ui-native` target,
empty `LIBSQLITE3_FLAGS`, debug0/incremental0/jobs1, offline/locked and own D TEMP.
No heavy builds overlapped. Native tests included all six newly named fork cases,
confirming this module was compiled/executed rather than an old app test binary.

```powershell
$env:CARGO_PROFILE_DEV_DEBUG='0'
$env:CARGO_PROFILE_TEST_DEBUG='0'
$env:CARGO_INCREMENTAL='0'
$env:CARGO_BUILD_JOBS='1'
$env:LIBSQLITE3_FLAGS=''
# TEMP/TMP and target must be task-owned; use an ordinary, uncapped target.
node apps/desktop/verify-frontend.mjs
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --offline --locked --target-dir <ordinary-target> -- --test-threads=1
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --offline --locked --features dev-harness --target-dir <ordinary-target> -- --test-threads=1
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --offline --locked --all-targets --target-dir <ordinary-target> -- -D warnings
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --offline --locked --all-targets --features dev-harness --target-dir <ordinary-target> -- -D warnings
$env:LOCALLORE_D08_FORK_ARTIFACT_ROOT='<own-local-output>'
$env:LOCALLORE_D08_TARGET_DIR='<ordinary-target>'
node apps/desktop/fork-harness.mjs
```

| Actual check | Exact result/source |
| --- | --- |
| Full frontend verifier | PASS at `ed33fd7`: strict types/schema/all existing controller suites, fork 63/timeline 83 mocked-IPC assertions; normal bundle excludes dev markers |
| Normal native Rust suite | 60 passed, 0 failed, 1 existing Windows symlink privilege ignore at `f61ee57`/`550873e`; production Rust unchanged since this run |
| Dev native Rust suite | 64 passed, 0 failed, 1 same ignore + 2 harness-contract passed at `9e07a70`; Rust unchanged since this run |
| Strict all-target Clippy | default PASS at `550873e`; dev PASS at `9e07a70`, unchanged Rust |
| Native fixture regression | actual Host/SQLite reused-session/stale-head case 1 passed at `cc49a81`; also included in final dev suite |
| Full actual app cohort | **132 distinct assertions, 14 native WebView images, two actual processes PASS** at clean `ed33fd792ba6e6d1a277211c961e078b532c9e88`, sourceDirty=false |
| Normal frontend restoration | Rebuilt after native harness; fork/native hooks absent, normal app.js SHA256 `c438088c618e35caae6c993ccf6e1ee4a8ab996649bef01eb84a0f9d2b8e64e1` |

Default and dev counts overlap; do not sum them as unique tests. No headless
browser run is claimed. Mock controller/inert React semantic checks are separate
from actual Rust Host/SQLite tests, actual native IPC and actual WebView pixels.

The actual app cohort covers midturn Rule, stale creation head, accepted boundary,
parent/canonical preservation, original receipt scopes, explicit fixed-ID retry,
held pending/Busy/cancel, session switch/late reply, sibling continuation isolation,
actual committed result with lost acknowledgement, observer isolation, explicit
child resume, restart lookup-only and missing-child no-recreation. The existing
fake typed-action provider continues one child; no model is loaded or called.
Mira retains the addressed inherited statement; absent Sable cannot inspect it;
inspection does not change player canonical bytes or original receipt scope.

## Retained failures and inspection corrections

Unchanged old timeline suite atc91 actually failed its obsolete broad "forking
unavailable" copy assertion. The single test now requires original preservation,
no automatic downstream replay, corrections unavailable and no author control;
all other oracles unchanged. Then83PASS. RED/GREEN hashes recorded below.

First actual native run550873e and diagnostic repeat98e22a5 both failed the frozen
Stale oracle. Exact diagnostic showed Closed: the dev helper had called Resume
and then Close, incorrectly treating the reused live app session as a new helper
session. Fixed only that fixture atcc49; actual Host/SQLite regression proves one
live reused session remains and stale fork returns Stale. Canonical/native oracles
were not loosened. Both failed UUID folders and their two images remain local.

Then112 actual assertions/14 images passed. Visual inspection found controller
confirmation could leave a local-only React checkbox unchecked; consent now lives
in the controller. Requested vs next-draft boundary wording was clarified and
six real DOM consent-state assertions added. Then118/14 passed; all14 inspected.
Final capture improvement adds selected-player-receipt metadata within ForkPanel
and14 visibility assertions, and closes only its own expanded catalog before
capture, so a scrolled sidebar cannot hide receipt context. No desktop control.

## Local evidence and limits

All generated artifacts stay outside Git under the task-owned
`D:/CodexLocalLore/01a165d9-ff25-7500-a550-1099087d4e37/desktop-fork-artifacts`.
Final cohort: `fork-native-f448bcac-b1d9-4a95-9482-18afb5f65cac`.
Both initial/restart ErrorBuffers are empty; two Chromium window-class
unregistration1412 shutdown stderr lines are retained separately. Every child
stdout/stderr is capped256KiB/channel with truncation metadata; no log is uploaded.
All four runner child processes exited 0 and all bounded log metadata has
`truncated=false`. All final 14 images were individually inspected: clear selected
story/observer/revision, player receipt identity/original scope, exact request,
pending/uncertain/error/result; no overlapping controls or horizontal overflow.
The 620px frame stacks fields and wraps IDs cleanly. Existing vertical page
scrolling remains intentional. Final receipt labels and pending consent agree
with controller/native semantic state. Earlier 118-assertion cohort remains local.

Each following name has `.png`, coherent `.json`, and `.capture.json` files:

| Folder | Frame names |
| --- | --- |
| initial | fork-prepared, fork-rejected, fork-accepted, fork-pending, fork-cancelled, fork-switched, fork-unknown, fork-retry, fork-observer, fork-narrow, fork-finished |
| restart | fork-restarted, fork-missing, fork-reopened |

| Local log/report | SHA256 |
| --- | --- |
| frontend-ed33fd7.log | aac428775fc1e908bdf66c97dce2f754fb6195e25cc0dfd749b702e62b1f229c |
| native-default-f61ee57.log | 40b58eca41fcd6d1d41fa5fdc9dc432bc2ed3dc3ad2a86c36be977dbb521b906 |
| native-dev-9e07a70.log | 508272db1dc92cbf72f94f4a31639eb7b21e4c682d2537cb8350ac2940092d9b |
| clippy-default-550873e.log | 4e824a04b11438f0dfb6aad001dc55e7b8cbdbf81ff08fcbeabae1816039b5bf |
| clippy-dev-9e07a70.log | 46adb9ca5551221c4ac9b2720347515aabc0e6bbbbc952b072af9bf8c5a060a62 |
| 712122f9 cohort summary.json | 92526ab0cc71691c444e78c24e1edc56f9195b9cb8c046651e3ad316c945c6c6 |
| f448bcac final summary.json | 5fbaa3e80d13a3c8940be9c4f72f98be167b90e054e5b3022dab15eaf36cdec6 |
| f448bcac initial/report.json | 0cb97002ac2a5df74a7565e66f216adab30eaa455446357e8394f82220e18a66 |
| f448bcac restart/report.json | 8ee718906837b7436cdd68cb07c825e59274d1d0c7b87b902ecdb3ea3a2c2411 |
| native-harness-ed33fd7.log | 23b5dd1bf01397e7e6a99409270739e617c6550359294cee3ca462e1fa39790c |
| timeline-copy-red-c91b772.log | 431b28f60d09293aeba4c264af1f36147c0b88db3f0e58615f1a215b9079132e |
| timeline-copy-green.log | 7d1d6527aa0f1c79d470f8489032160b68b0d8ab7657561e77cd3f1fd82ad096 |

Actual separate-process restart is clean shutdown/relaunch after a deliberately
withheld real commit acknowledgement, not forced termination, power loss or
physical storage exhaustion. No actual model, Android/emulator/phone, hosted CI,
network-blocked run, package/release/clean-build reproducibility or author-correction
qualification by this subagent. Android parity is separately owned; shared Rust
contracts/schema/engine/Store/Android were not edited. No desktop input/window
activation/screen capture/CUA or protected-chat resources. No PR/merge/settings
change; coordinator owns independent review, current-main integration and gates.
