# Session close and private capture ordering: first regression freeze

2026-10-27. Refs #29 D07.06, supporting #25 D04.04. Source base97106af7;
qualification-only draft350a6131 precedes this independent freeze. **SOURCE ONLY,
UNRUN**: author ran no Node/esbuild/compiler/formatter/Cargo/test/native/model/
device/desktop or protected-resource action. Root owns the first unchanged
baseline and production correction. No production or existing assertions change.

The second actual native reader cohort retained an unexpected native Closed
after its new gameplay Host session-close/reopen path. Source shows a concrete
ordering candidate: Controller.closeSession awaits Host close before removing
the selected session; the synchronous main subscription then asks
CaptureController.contextChanged to revoke the old session. IpcGateway records
Closed even though the capture cleanup catches it. Existing error records lack
operation identity, so this is a source-based diagnosis, not an authenticated
trace of that specific native error. Both original failed cohorts remain failed.
Do not waive the native error assertion or globally suppress Closed diagnostics.

## Agreed minimal interface before implementation

Keep all existing constructor arguments/defaults and the fifth development flag.
Add one optional argument to the **existing fourth callback** type:

```typescript
coordinatePrivateMetadata(
    work: () => Promise<void>,
    closingSession?: Session,
): Promise<void>;
```

Controller.closeSession captures its actual Session as before, invalidates old
gameplay work, then awaits this coordinator around its actual Host-close call,
passing that Session. main forwards the same optional value to the existing
`CaptureController.metadataControl(work, closingSession?: Session)` method.
No new wire field, native command, privilege, alternate runtime or Engine writer
is introduced. Calls without closingSession retain existing metadata semantics;
the default coordinator still simply runs its work.

For an explicit closing owner, compare both session ID and scope. Clear/fence
private presentation synchronously, retire that matching owner and serialize
actual native capture_revoke and Host trace_capture_revoke before Host close.
Reuse the existing control queue; do not synthesize revoked/enabled success.
Keep a private closing-identity fence so repeated old-session notifications cannot
reattach that owner while close is pending or enqueue a second revoke after it.
One suitable implementation normalizes a closing session to null through
contextChanged, then queues work behind the existing actual revoke; it does not
perform another global revoke. If the current capture already belongs to a
different session B, closing A must not clear/revoke B. Async completion/finally
must not overwrite B. On Host-close failure retain honest selected-session/error
state, keep old private presentation cleared and permit normal context sync plus
explicit fresh consent/read to recover and retry. No automatic old data revival.

## Four finite oracles and their exact limits

NEW `apps/desktop/check-capture-session-close-review.mjs` bundles the actual
Controller, CaptureController, IpcGateway and ErrorBuffer. Its raw invoke double
accepts only existing fixed native/Host operations. A modeled session becomes
closed only when its close operation succeeds; old-session calls thereafter
return actual-shaped Closed through the real IpcGateway. Failures therefore
remain in the shared bounded error buffer. Empty player snapshots and trace/
private-diagnostic DTOs are explicitly synthetic transport data, with no accepted
receipts/events, canonical commits, model execution or new provider/fault hook.

The integrated fixture uses the same public contextChanged subscription as main,
including actual Controller-selected session/head/view/lens/traceAttempt. It
obtains a nonempty synthetic private reply through actual capture decoding before
close, so clearing is not tested against an already empty object. Cases are:

1. Actual Controller.closeSession with independently held native and Host revoke
   effects: Host close cannot begin before both settle. Repeated old selected
   context notifications cannot reinstall the owner. Private reply/preview clear,
   session closes, no post-close old-scope Host call and no Closed error occur.
2. A failed modeled Host close returns Busy and leaves that session open/selected
   with truthful Controller error and cleared private data. Normal refresh/context
   sync and explicit fresh capture actions remain usable; a subsequent successful
   close preserves ordering without hiding the earlier Busy.
3. Direct Capture optional-Session unit case: a ready private capture B is
   unchanged when metadata work closes A; no global or B Host revoke is sent.
   This is not an end-to-end concurrent native gameplay-selection claim.
4. Default Controller without capture integration closes normally with no new
   capture IPC, preserving optional/default compatibility.

Held-gate discovery uses finite polling, and every gate is released in finally.
Each case has isolated transport/session/controller state; no shared live lock,
filesystem save/model asset, SQL or arbitrary execution endpoint is introduced.
Result JSON labels headless_ordered_ipc_double and actual public controllers/
IpcGateway, with Rust Host/native IPC/WebView/canonical commit/model false.
It writes unique create-new bundle/result files under the existing gitignored
artifacts/checks directory or existing explicit LOCALLORE_CHECK_OUTPUT_DIR.

Because the existing JavaScript APIs accept calls with an extra ignored optional
argument, Root can run this checker against the pre-fix source; missing ordering
is a meaningful potential behavioral failure, not a missing-module setup failure.
No RED or GREEN is claimed before that actual run. Any fixture/API calibration
must be separately attributed without weakening these ordering/privacy assertions.

From apps/desktop, after source freeze:

```powershell
node check-capture-session-close-review.mjs
```

Root then implements the agreed production path, reruns unchanged cases and
existing capture/gameplay/frontend checks, and verifies bounded actual native
operation provenance where needed. Finally rerun the fixed Reader4 cohort with
all original error/layout/inventory checks and both stages. Headless doubles are
neither proof of actual Tauri/Host timing nor permission to mark the two failed
native cohorts passed. No Android/model/human qualification follows; the original
human needs-improvement assessment remains unchanged.

## Root execution and independent failure-cleanup correction

This section records later actual owner execution; it does not change the
historical source-only first-freeze status above. Process JSON/logs remain local
and gitignored under author-integration-artifacts. Every row below reports clean,
unchanged source and runs Node24.22.1 `check-capture-session-close-review.mjs`
from apps/desktop. Durations are process wall time, not native latency:

| Evidence prefix | Exact source | Actual result | Seconds |
| --- | --- | --- | --- |
| d07-capture-session-close-baseline1 | e86befb124f2118168d63bcad92fac98a662c7a8 | Original4:1 passed,3 failed; exit1 | 0.2967524 |
| d07-capture-session-close-first-green1 | d811f4684de73211ce293a52dbac1d915430770d | Unchanged original4 passed,0 failed; exit0 | 0.2465065 |
| d07-capture-session-close-listener-baseline1 | 843809274fd5e29117a7de0cf9405ce15aecd03a | Original4 passed; new listener case failed; exit1 | 0.2468925 |
| d07-capture-session-close-listener-green1 | 9c04722b532d405052076c747f67693c4b0f61ac | Same5 passed,0 failed; exit0 | 0.3885606 |

The first baseline fails on missing pre-close Host revoke, post-close old-scope
Host calls and clearing an unrelated B capture; the default compatibility control
passes. The correction forwards the actual closing Session through the existing
coordinator and reuses the private capture control queue. Matching context
retirement queues actual revocation before Host close. A private identity/count
map prevents repeated matching notifications reattaching an owner while any close
is pending; normal metadata semantics remain unchanged. The closing branch does
not globally revoke/clear another owner B or patch B in an old async finally.
No Closed error suppression, accepted-state constructor or native API is added.

Independent source review of d811 identified a second concrete failure path:
the map increment preceded contextChanged retirement outside try/finally. A
synchronous public subscriber exception could leave the count permanently held,
preventing a still-open session from recovering after the bad listener was
removed. Independently frozen `ce906218e8f591ec597c05782fd197136b30e767` adds
exactly35 checker lines while preserving original4 assertions. It injects one
listener throw at explicit matching retirement, verifies no Host close, truthful
selected-session/Transport error and cleared private data, removes the listener,
then requires normal context recovery, fresh consent/read and a successful retry.
The35 lines were integrated verbatim at84380927 against the formatted checker;
its measured failure is `failed retirement released its private closing identity`
with false!==true. This is actual behavioral RED rather than API/setup absence.

9c04722b moves that same matching-owner retirement inside the existing try, so
the reference-count finally covers synchronous listener failure as well as
queued work failure. It does not hide the original error: the unchanged fifth
case still requires visible/frontend Transport and no Host close before recovery.
Independent source-only rereview confirms the finding is closed and found no
other concrete blocker in that delta. The author ran no checker or application.

Listener-baseline process-record SHA256:
`824670ee4ba1a2181969951533d54499f91668528a14ab289abcd449d7dbaa51`;
listener-GREEN process-record SHA256:
`6db913d008bcc154d55d907ede775393173564f7c888f4944259af992000406e`.
The original additive checker SHA256 atce906218 is
`715f6c88936f2697a0a06302b3773530a1cb944c2b88e6877a2303a0e9654c0a`.
Hashes bind retained observations, not execution authenticity.

A preceding full frontend run at a301fa1a6c0a1d91443ead9de8598640ba3aa46e
passed in19.0489807s, before the additive listener test/fix. A later formatted
five-case/full-frontend result and post-fix actual native Reader4 cohort are
not established by this append. Both historical native cohort failures and14
initial images remain separately retained; these five headless ordered-transport
checks cannot turn them into a pass. Actual Host/Tauri timing, both native stages,
complete error/inventory/render checks, Android, model and human-quality gates
retain their separate limits. The original needs-improvement assessment is unchanged.
