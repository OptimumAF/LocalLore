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
