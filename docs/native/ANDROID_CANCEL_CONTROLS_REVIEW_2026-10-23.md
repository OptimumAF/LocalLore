# Visible cancellation controls review, 2026-10-23

Refs [#9](https://github.com/OptimumAF/LocalLore/issues/9), M05.04 partial;
[#8](https://github.com/OptimumAF/LocalLore/issues/8), M04.04 supporting.
Independent fixture/source/evidence review. The coordinator and delegated device
owner executed the builds and emulator checks; this reviewer did not execute
another build, Android client, Activity, native call or model request.
The input was unmerged [#123](https://github.com/OptimumAF/LocalLore/pull/123),
exact source `58904bd`. Owner acceptance remains separate.

## Defects and correction

The existing busy label said `Opening saved progress…` while cancellation was
waiting for its original acknowledgement or for the accepted snapshot. The
pending cancellation had no visible status that distinguished that reconciliation
from opening storage. The coordinator also identified a related control gap:
after an invalid acknowledgement, Send and mode were disabled but saved-library
and New story remained enabled. Retained `resume` and durable `reset` callbacks
also admitted a story switch while the original outcome remained uncertain.

These are presentation/control-boundary defects. The existing gateway still
retained the original recovery key until a matching terminal acknowledgement;
the controls defect does not establish canonical data loss. Cancellation cannot
roll back a committed result.

I source-reviewed coordinator correction
`2dedd502798b0f75647048d1d64444d8fc81f4e2`. A default-false presentation field
distinguishes cancellation reconciliation, becomes true only for `cancelSaved`,
and clears on successful publication, failure/finally and disposal. Other saved
operations select the default opening status. Library button and popup admission
both exclude recovery-required state; controller guards also reject retained
resume/durable-reset callbacks. In-memory reset recovery remains available.
No actionable source findings remain in this bounded review. No engine, wire,
schema, gateway, runtime, permission or dependency change is required, and Kotlin
gains no gameplay authority.

## Frozen Compose selection

`cf94aebbd6913338f00ef0250966f68587014ae9` froze eight methods before the
production correction. The new class uses actual `LocalLoreScreen`, collected
`ShellViewModel` state, actual `DurableGateway`, Android main dispatch and platform
`JSONObject`. Its private synthetic transport controls acknowledgement,
preparation and snapshot gates. A generic Compose host displays the surface;
`MainActivity`, `NativeWorkspace`, JNI, SQLite and inference are never invoked.

The fixture fills a valid scripted-capable draft and first observes enabled Send,
then clicks Give potion and Cancel. It uses semantic scrolling for lazy content,
clicks the actual Recover button, and unconditionally releases every held gate
before host teardown. Explicit waits are bounded at eight seconds; the owner
also bounds instrumentation separately.

| Method | Actual baseline |
|---|---|
| `checkingCancellationIsVisibleBeforeAcknowledgementAndBlocksCompetingControls` | Fail: opening label instead of checking cancellation |
| `checkingCancellationRemainsVisibleUntilAcceptedSnapshotArrives` | Fail: opening label while snapshot is held |
| `foreignAcknowledgementShowsRecoveryAndRecoveryClickUsesOriginalKey` | Fail: saved-library remains enabled |
| `unfinishedAcknowledgementShowsRecoveryAndRecoveryClickUsesOriginalKey` | Fail: saved-library remains enabled |
| `incompleteCommittedAcknowledgementShowsRecoveryAndRecoveryClickUsesOriginalKey` | Fail: saved-library remains enabled |
| `committedRaceShowsAcceptedHistoryAndNeverClaimsRollback` | Pass |
| `lateNoncooperativePreparationCannotReplaceCancelledVisibleHistory` | Pass |
| `disposalWhileCheckingCannotPublishLateAcknowledgementOrPreparation` | Pass |

The three invalid-ack methods fail at library availability before reaching their
later New story/retained-callback and Recover assertions. Those later assertions
are not separately reproduced baseline failures. The passing candidate reaches
all of them, including equality of the two cancel commands and no replacement
submit/commit. A committed transport fixture represents accepted data; it does
not perform a real engine commit.

The frozen baseline source is 17,810 bytes, SHA256
`8f4b902dc6214f810d9919a1a377a9b49c8e8f89f6a50f14f1f824eee03e05a8`.
After the baseline finished, `c31593de13498ca322f77cfd9f6687316929b446`
(integrated as `32258cb`) removed exactly one extra terminal LF. Candidate source
is 17,809 bytes, SHA256
`05db4e41f6eeb60d0a9e209c81531b625551d542421cbbea03d18f0c32d1c494`.
I independently verified the original bytes equal the candidate bytes plus that
single LF; all test methods, oracles and assertions remain unchanged. Adding a
ShellState constructor field also legitimately recompiles test callers, so test
APK byte identity is not claimed.

## Actual evidence inspected

The baseline raw transcript has all eight exact start/terminal pairs: **three
passed / five failed**, no skipped/unfinished method, and final runner code -1
after every pair. It is 26,700 bytes, SHA256
`dcc64674c0e8e7961395e6450342c27337fede2316f488d77a6290ee5e0d5c64`.
I independently rehashed all **27** completed baseline command stdout records:
zero mismatches, zero child exits and known client cleanup.

The overall baseline cohort nevertheless **stopped** at its first post-test
process check because the isolated generic test-host process survived. It has
no after/final map or final floor qualification. Before/installed observations
matched the original 23 package hashes. These test statuses are actual results,
but they do not turn the stopped cohort into a preservation pass.

I independently parsed the candidate's **19 actual JVM XML files**: **150 tests**,
zero failures, errors or skips. Lint XML contains zero errors and the one existing
GradleDependency warning for the pinned coroutine dependency. This is inspection
of owner-executed checks, not another test run.

The candidate raw transcript has the same eight method oracles, **eight passed /
zero failed**, no skip/unfinished method, and final runner code -1 after all eight
success terminals. It is 5,728 bytes, SHA256
`eea20d3b8b7633d0295f64325b4e3857c765bc070c3081f22cafc9e95a7bf7d0`.
Its 46 completed clients all independently matched stdout byte counts/hashes,
zero exits and known client cleanup. The owned cohort completed in 53,234 ms.

Between the stopped baseline and candidate, a separate read-only settlement
completed ten clients; the same test-host process matched its installed package
UID, exact 25-package map and capacity floor. The attempted system instrumentation
subcommand returned unsupported output; it proves no absence of active
instrumentation. A separately admitted cleanup then completed 26 clients, with
one force-stop of the exact owned TEST package after adjacent PID/UID/package-map
and terminal-method checks. Its after/final namespace, package-map and floor
checks passed. The original baseline remains stopped.

The candidate likewise performed one explicitly admitted exact TEST-package stop
after all eight terminal methods and adjacent UID/map checks, before its successful
after/final namespace, map and floor checks. Final userdata free space was
1,644,175,360 bytes, above the unchanged 1,207,959,552-byte admission floor.
These cleanup observations are separate from natural process exit and from native
or model ownership. I source-reviewed the bounded exact-ownership helper and
baseline cleanup controller without dispatching any process action.

Across stopped baseline, read-only settlement, explicit baseline cleanup and
candidate, I independently rehashed **109 command stdout records**, zero
mismatches. Every observed package map preserves the original 23 hashes and the
admitted app/test pair. I also independently rehashed both app/test APK pairs
against their bindings and verified that all four packaged native-library byte
sequences match baseline/candidate. Both APKs changed; frozen source-oracle
continuity is established by the one-LF comparison above.

I independently rehashed the closed device evidence selection: **327 files /
457,715 bytes**, zero mismatches. Its 55,854-byte index SHA256 is
`f5d99fb0dad7cef4a567ed6f5514792160b4e745acea35d15313b8cf77a60376`.
The selected closed host evidence also rehashed without mismatch: **54 files /
49,933,687 bytes**; 10,129-byte index SHA256
`ed70b9de8eebcd0a5663d8004b6d5a05083e68a8db1f4bcf9f30593a000a48f5`.
These selections include overlapping source/artifact records, not extra test
execution. Raw diagnostics, identifiers and APKs remain private.

## Boundaries and handoff

The test-host process observation does not establish a native/model leak: this
selection invokes neither. Explicit owned test-host cleanup is reported
separately from natural process exit and cannot retroactively qualify the stopped
baseline cohort. No natural test-host exit or native/model ownership gate is
claimed.

This finite rendered Compose selection cannot establish native worker ownership,
model cancellation, canonical replay, process-restart recovery, ARM execution,
physical-device behavior, model quality or a two-emulator gate. A remains blocked
by its prior storage deficit; M01.01 physical-phone verification remains blocked.
M05.04 stays partial/in review and M04.04 receives supporting evidence. Checkboxes
remain unchanged pending full criteria and owner acceptance.
