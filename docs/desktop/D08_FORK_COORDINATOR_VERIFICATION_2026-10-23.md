# Desktop completed-boundary forks: coordinator verification

Partial #30 D08.04 and #12 M08.01/.02 integration. Accepted base is main `b90ddc9c0ed955c034a6c1f9e331caf3323e4e9a` (PR114). Branch `impl/d08-desktop-fork-integration` is coordinator-owned; claim #30 comment6375736370 precedes integration edits. No author-correction implementation or full D08 acceptance follows from this slice.

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

Pending: rerun the15 review cases after formatting; integrate current accepted shared generation code; compile/test/strict-check current normal/development native builds; repeat the actual132-assertion/14-image cohort and inspect its current images; focused PR and exact-tree merge verification. No mock, source review, historical render or headless semantic check substitutes for those pending native checks. No model, Android/JNI/device, hosted CI, release/package reproducibility or physical-phone acceptance is claimed by this report.

No CUA, injected input, window activation, desktop screenshot, general debugging server, repository settings change, release, download or protected-thread action is part of this work. Existing-account merge override is owner-authorized; it does not fabricate an independent human review. Broad milestone boxes remain unchecked.
