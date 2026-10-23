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
