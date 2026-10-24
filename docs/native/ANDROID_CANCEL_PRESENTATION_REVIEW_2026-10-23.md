# Cancellation presentation review, 2026-10-23

Scope: M05.04 partial, with M04.04 supporting. Independent test/review agent;
production integration and check execution belong to the coordinator. Input is
PR #122 commit `73cd948e9c215bfa50f0eb9912f3171d1bd1b603`, an unmerged
prerequisite when the test selection was frozen.

## Independently identified failures

`ShellViewModel.cancel` recorded `CANCEL/COMPLETED` immediately after scheduling
`gateway.cancelSaved()`. That suspending operation could still be waiting for its
original turn's acknowledgement, could reject a foreign or unfinished reply, or
could fail while reconciling the accepted snapshot. A completion record therefore
claimed more than the observed operation established. Existing diagnostic
disposal clears the log; no retained post-disposal completion is asserted as a
baseline defect.

The same operation supplied the fixed notice `Response stopped. Showing the
accepted saved history.` A valid original committed receipt can win the race;
`DurableGateway.cancelSaved` then correctly returns that accepted saved history.
The notice still said the response stopped, contradicting the displayed committed
outcome. Architecture guidance explicitly requires showing the committed result
when commit wins; cancellation cannot roll back accepted history.

These are presentation/diagnostic defects. PR #122's complete original-binding
and terminal-acknowledgement validation remains the correct gateway boundary.
No gameplay rule, receipt, schema, native dependency or Kotlin gameplay authority
needs changing.

## Frozen regression selection

Commit `27346b6259fe32694a0c582de83bbb3c0b043b40` froze the sole new test
class, `org.locallore.app.CancelPresentationTest`, before a production correction.
It uses the actual `ShellViewModel`, actual `DurableGateway` and Android platform
`JSONObject`. A private synthetic `WorkspaceTransport` supplies delayed and
malformed replies. All owner operations run on Android's main dispatcher.
Explicit deferred gates hold preparation, cancellation and snapshot refresh;
noncooperative completion exercises obsolete results. An eight-second fixture
bound and unconditional owner cleanup release every held gate.

| Method | Regression oracle | Observed Android baseline |
|---|---|---|
| `cancellationDoesNotCompleteBeforeAcknowledgement` | No cancellation completion while the original acknowledgement is withheld | Fail |
| `cancellationDoesNotCompleteBeforeAcceptedSnapshotReconciliation` | Terminal acknowledgement alone does not complete saved-history reconciliation | Fail |
| `invalidAcknowledgementsRetainHistoryBlockSubmissionAndRecoverOriginalKey` | Foreign turn, ready phase and missing committed receipt retain history/recovery guidance, block replacement submit, retry identical cancel key; diagnostic stays unknown | Fail at diagnostic outcome |
| `explicitTransportFailureRecordsUnknownWithoutRawPayload` | Explicit Full failure retains accepted messages, gives storage guidance and records only fixed unknown failure metadata | Fail |
| `committedCancellationRaceDisplaysAcceptedHistoryWithoutStoppedClaim` | Accepted revision/inventory/narration come from snapshot, without a false stopped/cancelled claim | Fail |
| `lateNoncooperativePreparationCannotPublishOrCommitAfterCancellation` | Old prepared reply cannot attach or commit after cancellation reconciles | Pass |
| `disposalDuringDelayedAcknowledgementCannotPublishOrRecordCompletion` | Owner close is once-only, blocks late publication/calls and has no completed cancellation record | Pass |

The initial source prediction incorrectly expected disposal to fail; inspection
of the existing diagnostic log clear corrected that prediction before Android
execution. Actual baseline execution confirmed five failures and two passes.
Loop subcases do not add JUnit method counts. The committed-race fixture
represents accepted transport data; it does not execute an actual engine commit.

## Correction and independent evidence review

I source-reviewed production commit
`efc962543d6f47180a98dcca93114da79dd009c7`: the existing saved operation now
records cancellation completion after `cancelSaved()` returns its reconciled
snapshot. Failures record `UNKNOWN` with existing fixed error mapping and rethrow
into unchanged recovery guidance. Coroutine cancellation rethrows, disposed
owners cannot log late results, and the success notice acknowledges reconciliation
without asserting a rollback. No actionable source findings remain from this
bounded review; it is not owner acceptance.

The coordinator/device owner executed the checks; I independently inspected
closed evidence, rather than claiming additional execution:

- Baseline B: seven exact start/terminal pairs, **2 passed / 5 failed**. Raw
  instrumentation stdout is 27,161 bytes, SHA256
  `bf2da61f42ebab3659c94fbad15687552519cf9f48f0425f15661fcba97bbb4d`.
- Candidate B: the same seven method oracles, **7 passed / 0 failed**. Raw stdout
  is 5,026 bytes, SHA256
  `b7ef41c4f26e214d322cd06c11a089999ae3cb8031beea2ff125cba249865a83`.
  Both transcripts end with runner code -1 after all seven terminal statuses;
  no skipped or unfinished method was counted as a pass.
- All **84** baseline/candidate command stdout records independently matched
  recorded byte lengths and hashes, completed status, zero exit and known
  client cleanup. The sealed private selection rehashed **224 files / 297,843
  bytes**, zero mismatches; its 38,037-byte index SHA256 is
  `f0b1057eab86815c74fa2c5121bb9480c7b721b915a6352d3ab815148ad14cba`.
- I parsed the candidate's **19 actual JUnit XML files**: **150 tests**, zero
  failures, errors or skips. Separate frozen JVM regressions were 1 pass / 2
  failures on baseline, independently inspected in their XML. Candidate lint
  reports zero errors and one existing pinned-coroutines dependency warning.
- Baseline/candidate APK audit records have identical test APK bytes
  (2,312,557 bytes, SHA256
  `1161ac649721f22dab3d812364b4f92711c53969dfe67cff214bd4c3cbb49b8e`)
  and all four packaged native library hashes match. Gateway source hash stays
  `67f217690914ad05ff1b34b3cff165890265b4bf41a6971a5da5044a3b8eefd2`.

Raw diagnostics, package maps, APKs and local paths remain private. The device
owner's report and coordinator's verification document own exact admission,
package-preservation, timing, build commands and environment details. This review
performed no additional device, process, build, inference or storage operation.

## Verification boundary

This selection invokes no Activity, `NativeWorkspace`, JNI, SQLite or inference
provider. It cannot establish native worker ownership, canonical replay,
process-restart recovery, model cancellation, real generation, ARM execution,
physical-phone behavior or a two-emulator gate. Build execution and emulator
admission/results are reported separately by their actual owners. A remains
blocked by its previously measured storage deficit; this is B-only verification. Full
M05/M04 acceptance remains subject to repository acceptance rules.
