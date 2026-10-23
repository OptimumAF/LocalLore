# D08.04 desktop UI/native journey freeze

Coordinator-delegated follow-up to `47ab8d7`, same isolated desktop-fork worktree.
Claims #30 comment6374887103 and #12 comment6374887363.
The source/oracles in this commit are frozen before the new integration checks.
Earlier actual controller-only56PASS remains historically attributed; the expanded
suite/new native integration have NOT run at this freeze.

Production: existing UI/main/native handlers and closed Tauri build/config
allowlists, new ForkPanel, same fixed-input ForkController and existing
ArchiveBroker worker/registration/lifecycle. Original recovery request is saved
synchronously into application-local WebView storage before dispatch; it holds
scope/identity/revision metadata, no receipt, prose or model bytes. Restore is
lookup-only. A known confirmed or absent child does not permanently block starting
a separate explicit new request after selection changes. Unknown outcomes remain
protected from accidental replacement. Rule/RetryMismatch are honest native errors.
Native request parsing borrows and validates closed/bounded parent IDs before
copying renderer-owned strings; oversized IDs fail without an unbounded clone.

Development-only new fork_harness fixture: actual Store first receipt has two
events (Mira-addressed statement + wait), followed by a later parent statement.
Closed hooks: hold/release worker before Host dispatch, withhold one acknowledged
actual commit result, and one fixed guarded parent wait through actual Host. No
renderer-controlled paths/SQL/provider/fixture/code/shell; no new persistence owner.
The same existing hidden WebView2 CapturePreview mechanism captures only this app.

Fixed initial oracles, in order:

1. Existing durable fixture has head3 and two-event first receipt; UI offers
   completed boundaries0,2,3. Direct actual controller attempt at1 must fail Rule
   and read-only lookup must find no child.
2. Prepare at2/head3, commit the fixed external parent wait, then require actual
   Store Stale; lookup absent and normal refresh observes head4.
3. Create accepted-child at2/head4; original canonical Play bytes and selected
   main/head4 unchanged. Explicit exact retry returns same child/created=false.
4. Hold cancel-child in the existing worker; pending operation visible, concurrent
   native fork refuses ArchiveBusy, cancellation preserves parent and child absent.
5. Hold switch-child, switch through existing resume to accepted-child, wait for
   cancellation, release. Late reply cannot replace selection/result; actual child
   prefix has original main scope and excludes future parent statement. Lookup
   confirms no switch-child.
6. Withhold actual committed uncertain-child acknowledgement, require Transport
   with original identity retained; explicit exact retry finds committed same child.
   Before this new fork, continue accepted-child through the existing explicitly
   fake typed-action controller; uncertain-child must exclude that sibling turn
   and retain its original prefix/head2. No alternate inference implementation.
7. Explicitly open child; Mira sees inherited addressed statement, Sable cannot;
   neither lens changes canonical Play or original receipt scope. Narrow620px has
   no horizontal overflow. No model call.
8. Leave final actual committed restart-child acknowledgement uncertain, exact
   identity saved. Only main, accepted-child, uncertain-child, restart-child exist.
9. Close/dispose all Host sessions/workers; bounded frontend/gameplay errors empty.

Second actual process: same SQLite + own WebView profile, restored restart-child
is lookup-only; confirm cannot dispatch; lookup finds existing child/currenthead2.
Restore a missing fixed identity, lookup absent and confirm cannot recreate it;
catalog count unchanged. Restore original again, explicitly open child, prefix
replay head2 excludes future parent. Dispose sessions/workers and errors empty.

Expected CapturePreview artifacts: initial11 + restart3 =14 native app images,
each coherent semantic snapshot includes selected story/session/observer/revision,
pending fork operation/result/error, existing receipt and bounded semantic DOM.
All14 images require inspection after execution. This freeze reports no such run.
Normal frontend verifier must exclude fixed journey/hook markers. Compiler checks,
controller-mock tests, native Rust Host/SQLite tests, native IPC and actual WebView
rendering are reported separately; unavailable checks remain unavailable. No CUA,
input injection, desktop activation/capture, model/device/ADB/protected resource.
