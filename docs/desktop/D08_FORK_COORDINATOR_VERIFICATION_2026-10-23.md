# Desktop completed-boundary forks: coordinator verification

Partial #30 D08.04 and #12 M08.01/.02 integration. Current accepted base is main `a14c89986378742f4a74e157eef6803746c8c47e` (PR120); initial integration used PR114. Branch `impl/d08-desktop-fork-integration` is coordinator-owned; claim #30 comment6375736370 precedes integration edits. No author-correction implementation or full D08 acceptance follows from this slice.

## Integrated application path

The normal UI prepares one exact parent/head/completed boundary/fixed child request, persists its bounded four-field recovery identity before dispatch, and requires explicit consent. Native `fork_start`/`fork_lookup` use the existing WindowLease and ArchiveBroker with shared Host/Store authority. Lookup does not create a branch, replay later turns, or select a child. Opening the returned child uses the existing explicit resume path. Recovery hints contain no story prose and are not canonical save data or a qualified power-loss guarantee.

Source imports from the author packet `5e44ea91..224e241972e5d08affce9f6e5932793832748e29` preserve the native closed parser, single-worker admission, lease retirement/drain, exact permissions and development-only fixture path. Parent/sibling canonical state, original accepted receipt scopes and actor filtering remain shared Rust responsibilities. Inspection is not an author-write grant. Author corrections remain visibly unavailable.

## Additional actual controller regressions

The author-attributed 63 fork and83 timeline assertions use mocked IPC. Coordinator froze six additional controller cases before repair (`5a61a7a`/`6fa7d68`): save callback context switch, exception or disposal; nested preparation; and presentation listeners retiring the owner immediately before start/lookup. Retained pre-fix checkout `source-desktop-fork-callback-red` at `db50ec5` actually produced **0PASS/6FAIL**. Correction `3ed5f77` adds a short synchronous save barrier, epoch/context checks, lookup-only retained identity and live checks before dispatch. It does not add an alternative controller or canonical evaluator.

Independent reviewer froze nine more cases at `35eea912`/`14bcf6dc`: terminal-operation notification context switch/disposal; nested confirm/lookup/restore during recovery save; and confirm/lookup result notification retirement before library refresh. Retained pre-fix checkout `source-desktop-fork-notification-red` at `e9dd8e0` actually produced **0PASS/9FAIL**. Correction `ef88694` extends the existing preparing gate to every admission control and rechecks the owner after terminal notifications. The actual successful native outcome is not mislabeled rollback; retired owners simply stop presentation and further refresh work.

All **six plus nine cases passed unchanged** after `ef88694`. Five-file formatting commit `754fd72` changes wrapping only. A complete frontend verifier at that source passed strict TypeScript, schema/request validation, existing controller suites, original63 fork/83 timeline mocked assertions and normal-bundle hook exclusion. Counts overlap and are not additive native coverage. The independent source-only report is `D08_FORK_INDEPENDENT_REVIEW_2026-10-23.md`; its unrun attribution describes the reviewer's own handoff, whereas the RED/GREEN results here are actual coordinator executions.

Local evidence: `desktop-fork-callback-red.log`, `desktop-fork-independent-red.log`, `desktop-fork-review-frontend.log`, and the structured `desktop-fork-review-artifacts/{callback-red,callback-green,independent-red,independent-green}` reports. Generated artifacts remain local and gitignored; no private story or model prompt is published.

```powershell
$env:LOCALLORE_CHECK_OUTPUT_DIR='<own-local-output>'
node apps/desktop/check-fork-callback-review.mjs
node apps/desktop/check-fork-independent-review.mjs
node apps/desktop/verify-frontend.mjs
```

The first two commands run the actual frontend controller with synthetic closed IPC replies in Node. They do not execute a browser, native IPC, WebView, engine, model or Android device.

## Native rendering evidence and source limits

The author's final actual cohort at clean `ed33fd792ba6e6d1a277211c961e078b532c9e88` reports **132 distinct assertions,14 application-owned native WebView2 CapturePreview images, two application processes**, sourceDirty=false. Its native Rust suites report60 normal and64 development cases plus2 harness-contract cases; each build has one existing Windows symlink privilege ignore. See `D08_FORK_NATIVE_VERIFICATION_2026-10-23.md` for commands, versions, retained REDs, hashes and bounds. Those results precede the coordinator callback repairs and current Play2.4/shared-source integration.

The coordinator independently opened **all14** final author PNGs from local cohort `fork-native-f448bcac-b1d9-4a95-9482-18afb5f65cac` (summary SHA-256 `5fbaa3e80d13a3c8940be9c4f72f98be167b90e054e5b3022dab15eaf36cdec6`): prepared/rejected/accepted/pending/cancelled/switched/unknown/retry/observer/narrow/finished and restarted/missing/reopened. Selected scope/head/observer, player receipt and original scope, exact request, pending/error/result agree visibly. No overlap or horizontal overflow was found at1280×900 or620×900. The narrow form stacks and wraps; vertical page scrolling remains intentional. Sable's inspection is empty while the player receipt stays explicitly separate. Restart lookup does not recreate a missing child; resume is explicit. This is image inspection of actual application-owned renders, not desktop capture or control.

## Current integrated execution

All following runs used clean `0742b8035837bf542170a97dffb50c451bc3cc6e`, including accepted PR120's shared source binding, passive Open compatibility and Play2.4. No production change followed these runs. Own source timestamps were refreshed before reusing the native target, and the logs show the actual current Core/Store/Workspace/native crates compiling. Rust/Cargo1.93.1; Node24.22.1; Windows11 Pro10.0.26300; existing MSVC19.34.31937/SDK19041. Cached dependencies, one build job, debug information and incremental compilation disabled; ordinary uncapped SQLite (`LIBSQLITE3_FLAGS` empty). No download or device/model execution.

| Check | Actual result |
|---|---|
| Full frontend verifier | PASS strict TypeScript, schema/request checks, existing controller suites, original63 fork/83 timeline mock assertions and normal hook exclusion |
| Coordinator/independent callback regressions | All6+9 PASS unchanged; actual controller with mocked IPC |
| Normal native Rust | 60PASS/0FAIL/1 existing Windows symlink privilege ignore |
| Development native Rust | 64PASS/0FAIL/1 same ignore, plus2 harness-contract PASS |
| Strict all-target Clippy | Normal and dev-harness PASS |
| Actual native application cohort | 132 distinct assertions/14 native WebView2 images/two actual app processes PASS; all four runner children exit0, truncated=false |
| Normal frontend restored after cohort | Full verifier PASS again; normal dist/app.js SHA-256 `8b2cef04b673cc4a364dc81298ec0a82eb7c428581f592d23a325a2b0ce23a3d` |

Reproducible commands (repository root, existing offline tools/dependencies):

```powershell
$env:CARGO_BUILD_JOBS='1'
$env:CARGO_PROFILE_DEV_DEBUG='0'
$env:CARGO_PROFILE_TEST_DEBUG='0'
$env:CARGO_INCREMENTAL='0'
$env:LIBSQLITE3_FLAGS=''
node apps/desktop/verify-frontend.mjs
node apps/desktop/check-fork-callback-review.mjs
node apps/desktop/check-fork-independent-review.mjs
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --offline --locked --target-dir <own-native-target> -- --test-threads=1
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --offline --locked --features dev-harness --target-dir <own-native-target> -- --test-threads=1
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --offline --locked --all-targets --target-dir <own-native-target> -- -D warnings
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --offline --locked --all-targets --features dev-harness --target-dir <own-native-target> -- -D warnings
$env:LOCALLORE_D08_TARGET_DIR='<own-native-target>'
$env:LOCALLORE_D08_FORK_ARTIFACT_ROOT='<own-local-artifact-root>'
node apps/desktop/fork-harness.mjs
node apps/desktop/verify-frontend.mjs
```

Current local cohort `fork-native-0e6117eb-78f7-4916-a63d-f1de1bc02ccc`, summary SHA-256 `8854977cf5d0156e7402264d780ed2648412cdfec44ffeb8c63e02aad3ee7313`, records sourceDirty=false/backend=native/actualProcessRestart=true/realModelGeneration=false. The coordinator inspected all14 current PNGs and corresponding semantic snapshots/capture metadata: prepared/rejected/accepted/pending/cancelled/switched/unknown/retry/observer/narrow/finished; restarted/missing/reopened. Every capture reports native-webview2 and matches its snapshot's selected UI revision. Recorded source-input hashes match the current files; the harness frontend is deliberately replaced by the normal bundle afterward. Native executable SHA-256 `9ea41b912394059a6e3344d0a1b9d5777c8063acba0ab2dbcc22810c12b54b81`.

No visible overlap or horizontal overflow was found at1280×900 or620×900. Selected story/branch/head/observer, original player receipt scope, exact saved request, pending consent, result and visible error agree with the snapshots. Rule rejection remains visible, cancellation/withheld acknowledgment stay uncertain, and session changes retain only the original lookup identity. Sable's context has no facts/observations while the separately labeled player receipt retains its original source. Restart is an actual clean application-process restart; missing lookup never recreates a child and explicit resume restores the validated prefix at head2. This does not qualify power loss or arbitrary process death.

Initial/restart report.errors arrays and all14 snapshot.errors arrays are explicitly empty. Expected UI Rule/Cancelled/Transport states remain captured and are not counted as unexpected errors. Bounded native stderr contains two Chromium shutdown diagnostics (one per app process): `Failed to unregister class Chrome_WidgetWin_0. Error = 1412`. Both app processes exit0; these retained diagnostics are not described as a completely clean native stderr stream. Actual app-reported reduced UA is Chrome/Edg155.0.0.0 on Windows10.0, not a verified full loaded-runtime version.

Local logs: `desktop-fork-current-{frontend,callback,independent,native-normal,native-dev,strict-normal,strict-dev,native-cohort,normal-restored}.log`. Native normal/dev log SHA-256 respectively `d3f957811742cc6e06ab3ef5e996c96944ca6e83136fcafa1682adb5d2248c2f` / `aa1e742ab7057fdbe1c919a948e75e732a82b35890bbf1bae142832c7cbdacfd`; all generated profiles, databases, renders and logs remain local. Historical author evidence above remains attributed to its original revision.

Next is the focused PR and exact-tree merge verification. No mock, source review or headless semantic test is presented as native execution. No model, Android/JNI/device, hosted CI, release/package reproducibility or physical-phone acceptance is claimed by this report. Full M08/D08 gates stay open.

No CUA, injected input, window activation, desktop screenshot, general debugging server, repository settings change, release, download or protected-thread action is part of this work. Existing-account merge override is owner-authorized; it does not fabricate an independent human review. Broad milestone boxes remain unchecked.
