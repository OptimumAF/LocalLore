# Independent Android save/resume follow-up review

Tasks: M04.03/M04.04/M04.05/M04.06, delegated under #8 comment
6355725278. Baseline: `66df9cc14362d405870ad861ec59b328fdba4a71` (PR #42,
unmerged when assigned). Review worktree: `LocalLore-app-device-review`, branch
`review/m04-app-device`. The coordinator owns device actions, production fixes,
instrumentation changes and integrated evidence. This report does not accept the
milestone or duplicate the earlier shared Host/storage review.

## Concrete finding

`ShellInstrumentedTest` has four legacy assertions expecting
`Healing potion · Mira` (baseline lines 56, 76, 87 and 93). Production
`DurableGateway.snapshot` instead derives its inventory label from
`play_snapshot.inventory`: `You` when the potion exists, otherwise
`Not in your inventory`. The Host filters this map to player-owned items before
serializing it. The production label correctly avoids inferring a recipient's
current holdings from absence in the player's inventory.

Keep that boundary. Update the legacy UI expectation to the player-safe label
and retain strong evidence of the actual gift: revision 1, exactly one finalized
turn/two rendered messages, the engine's `You give 1 potion to mira.` narration,
and equality after reopen. A repeated give must reject and retain revision and
transcript. Merely checking inventory absence would not prove the recipient or
the committed effect.

## Additional acceptance checks

| Concern | Reviewed evidence and device follow-up |
|---|---|
| Cancellation before commit | `DurableGateway` retains original pending key and cancellation intent; existing real-JNI tests cover cancellation and failed-cancel recovery. Retain no-receipt/revision-0 assertions. |
| Lost acknowledgement | Commit falls back to original-key status; existing instrumentation tests retain one submitted key and one receipt. Reopen must observe the same receipt rather than prepare another reward. |
| Late completion | Gateway compares pending object identity/serial; ViewModel generation fences publication. Existing replacement-key instrumentation must remain effective. |
| IO/Main | Production transport opens directories/database and invokes JNI inside `Dispatchers.IO`; adapter-owned cleanup survives ViewModel scope cancellation. Existing test transport does not establish production transport's Main responsiveness or disposal, so execute that path separately. |
| Resource ownership | New independent test below checks the actual native registry, including two owners of one database and duplicate close after replacement allocation. |
| Process restart | Activity recreation and an in-process JNI owner reopen do not prove OS process death. Coordinator's separate explicit stop/relaunch evidence is required. |

The UI cancellation fixtures scroll to `cancel-turn` after selecting a fake
whose delay is only 200 ms. Scrolling may outlast generation, making the button
legitimately disappear after commit. This is a source-derived test timing risk,
not a reproduced production failure. Establish pending overlap with explicit
synchronization when proving cancellation; do not relax canonical-state checks
or claim a cancellation rolled back a completed commit.

## Independent executable proof

`crates/locallore-android/tests/app_device_review.rs` uses only synthetic local
SQLite files through `WorkspaceRegistry`. Two owners prepare distinct keys in
the same story. Closing one owner twice invalidates its handle while the other
commits exactly one potion gift. A replacement owner survives a delayed duplicate
close, restores the identical player snapshot and exact receipt, and reports
the abandoned draft separately. Closing all owners and reopening through a
fresh registry preserves that snapshot. This is host execution of the native
adapter, not JNI or an actual process restart.

Checks actually run in this review worktree:

```text
cargo test -p locallore-android --test app_device_review --locked --offline
  1 passed, 0 failed
cargo test -p locallore-android --locked --offline
  16 passed, 0 failed (1 unit + 1 new review + 8 boundary + 4 durable + 2 ownership)
  0 doc tests
cargo fmt --all -- --check
  passed after formatting the new test; initial check reported only that file
git diff --check
  passed
```

No production defect beyond the concrete legacy instrumentation mismatch was
found in the examined device-facing paths. This review ran no ADB, emulator,
phone, network, model, Gradle, JNI or OS-restart action. Coordinator results must
be read from the integrated device evidence; they are not inferred here.

## Main-based M03.03 verification follow-up

The coordinator subsequently integrated this review and owner-merged main
`2612001` into its local `LocalLore-m03-reverify` checkout. The following is a
read-only review of its pending `DurableRestartTest.kt` and
`ShellInstrumentedTest.assertAccepted` changes. This reviewer performed no
upstream merge and did not inspect or operate a device.

The `assertAccepted` change addresses the concrete stale-label finding while
retaining the exact engine narration, accepted revision 1 and two-message
transcript assertions. No current recipient ownership is inferred from inventory
absence.

No concrete failure was found in the new restart test. Its two explicit phases
require a valid coordination token, changed PID or process-start time, exact
story/branch selection, matching revision, and a length-framed SHA-256 digest
over message IDs, player flags and UTF-8 text. Resume checks the gift narration,
repeat-give rejection, an independent new story and the original saved
transcript again. The checkpoint is bounded to 8192 bytes when read. Cleanup
removes only the exact checkpoint file and then its empty directory, preserving
the database and saved stories. Failed phases retain their checkpoint evidence.
The test requires actual execution with a host process stop between phases;
compilation or Activity recreation cannot substitute for that evidence.

The remaining production transport coverage gap is distinct from the already
tested Rust registry. `DurableNativeTest.TestTransport` closes synchronously;
it does not execute `NativeWorkspaceTransport`'s adapter-owned coroutine cleanup
scope. Checking that the database file remains after Activity disposal also
does not establish native handle release. A useful device test should use the
production transport, establish an actual delayed `prepare` in `running` phase
with bounded original-key status polling, verify a Main dispatcher pulse,
cancel/reconcile that key and assert no receipt/revision advancement. Disposal
should independently demonstrate that native owner capacity recovers. A host
Rust test alone cannot establish Kotlin IO/Main scheduling or coroutine cleanup.

The earlier scroll/recreation timing concern remains a source-derived risk,
not a reproduced failure in this review. No additional native test was added
for a Kotlin scheduling boundary. Integrated emulator results remain owned by
the coordinator's evidence report.

## Cancellation and transport fixture review

The coordinator subsequently reported an actual emulator-A baseline capture
with missing `cancel-turn` and touch-injection failures after the 200 ms fake
window, plus legacy label failures. This reviewer has not independently read
those device logs; exact terminal counts, deadline handling and reruns belong
in the coordinator's integrated evidence.

Read-only review of the proposed `DurableTransportOwnershipTest` confirms that
durable `turn_status` returns the local `running` phase when persisted status is
still `draft`; bounded phase polling is therefore valid. Opening all four real
native-owner slots and closing each successful probe in `finally` is a useful
release proof without a production statistics hook. The isolated
`ContextWrapper` preserves use of the production transport while redirecting
only the create-new synthetic private directory.

Two scheduling qualifications were returned to the coordinator:

- A Main pulse after observing `running` still has only the finite 200 ms fake
  window. Failure to overlap is not, by itself, evidence that Main was blocked.
- Production `close()` schedules native teardown asynchronously. A prepare can
  finish as a noncanonical `ready` proposal before that cleanup worker runs.
  Rejection with `Closed` proves that teardown won that measured race, but is
  not guaranteed merely because Kotlin `close()` returned. ViewModel generation
  and job fences own late UI publication; a draft response is not a commit.

Moving shell cancellation onto the same Main stack avoids the scroll race but
introduces a distinct pre-submit path. Native `submit` may not have executed
when `cancelSaved` calls `cancel`. The actual Host then returns `UnknownTurn`.
At the reviewed baseline `cancelSaved` propagates this error, whereas
`recoverSaved`'s cancelled branch clears the same pending operation and returns
the canonical snapshot. This is a concrete source-level asymmetry; independent
device reproduction is not claimed here.

Under the coordinator's additional #8 ownership claim, the new instrumented
`DurableCancellationReviewTest.kt` gates the first submit **before** delegation
to real JNI/SQLite. It expects cancellation to reconcile `UnknownTurn`, releases
the old submit and verifies that its retained cancellation intent prevents any
prepare, commit or recovery regeneration. The late draft stays outside canon
across reopen. A second case verifies that late completion cannot clear a
replacement operation: only the replacement key prepares and commits, exactly
one gift is saved, and reopen preserves its receipt-derived transcript.

Mirroring the existing cancelled-recovery handling is appropriate only while
clearing `operation` by identity (`operation === pending`). The original pending
object must stay cancelled, so a late submit reply cannot initiate preparation
or clear a replacement. The test asserts that distinction. No production change
was made in this review worktree.

The coordinator subsequently reported that its first revised shell run did
reproduce the pre-submit cancellation recovery state, and that manually calling
`Instrumentation.callActivityOnStop` left ActivityScenario's lifecycle state
incompatible with the later recreation. That callback shortcut was removed.
The revised test is explicitly about recreation of an **already cancelled**
draft; it does not claim framework-triggered cancellation during a running
generation. The coordinator also reported successful production-transport and
two-phase restart cases on emulator B. These are attributed reports, not
independent executions by this reviewer; final counts and source identity must
come from the integrated verification artifact.
