# Active-child saved-task restoration contract v1

Refs #14 M10.02 supporting, #9 M05.05 lifecycle supporting, #12 M08.01
integration supporting and #13 M09.03 preparation. This extends the
[root process oracle](ANDROID_PROCESS_RESTORATION_PROTOCOL.md); it is not an
execution result or new canonical/fork API.

## Boundary and admission

Use the existing isolated debug product, real MainActivity, shared JNI/Rust
workspace, scripted inference and external self-targeted controller. Existing
UID/signing/APK/transport/source ownership, private bounds, saved-ack/STOPPED,
postmortem counters, same-task/new-process and descriptor-uncertainty rules
remain. No instrumentation replaces the product process or application factory.
The original `restore_non_default` case and its fixture are preserved.

The additional closed case is exactly `restore_child_branch`, with the same
four arguments (`case`, `run_id`, `product_sha256`, `cohort`). It accepts only
`cohort=create`. Refuse reuse before changing any product state. A partial
setup, an uncertain fork or an already committed child is not a reusable
fixture; preserve that cohort and qualify a fresh one instead.

All fixture writes stay in the controller's fixed app-private
`no_backup/process-controller-child-v1` directory. The closed child fixture
includes its version/scope/case, exact owner UIDs/signing/origin run/APK, two
ordered root identities as observed at creation, the parent/child identities
and head1, and hashes of the compiled original parent text and child draft.
Only after the actual reviewed fork, explicit child resume and exact setup
counter vector are verified may this create-only fixture be finalized. No raw
text, path argument, arbitrary command, database access or fixture adoption is
provided by the instrumentation interface.

## Genuine product journey

1. Create exactly two native stories through the actual New story control;
   freeze their lexical order A/B and original roots at head0. Select B.
2. Enter the compiled original parent Dialogue and explicitly Send once.
   Require accepted parent head1 and that exact text in `message-body-1`.
3. Open the existing New timeline review. Keep the captured completed boundary1,
   prepare the request, read the exact displayed fixed child ID, give explicit
   consent and confirm. Require the returned story/parent/fork/head identity,
   then press the existing explicit Resume this timeline control. No replay,
   direct native command or fixture seeding substitutes for these actions.
4. Require selected child head1 and inherited original parent text. Enter a
   distinct original Unicode/newline Dialogue as the child's unsent draft.
   The parent draft is not the restored child editor. Verify exact text/kind.
5. HOME, require a newer after-super save acknowledgement for the child digest
   and the exact stopped task, then background `am kill` only the fixed product.
   Observe old PID disappearance and its final saved/commands vector before
   relaunch. Require the same task, new PID/start, factory1, restored state,
   selected child head1, inherited parent text and exact child draft/kind.
6. Explicitly reselect the same child through the actual timeline menu and
   require increased native read/resume counters, unchanged head and draft,
   with no automatic gameplay/fork mutation attempts. Selecting the story root
   instead would not satisfy this step.
7. Send the child draft exactly once. Require child head2 and inherited parent
   text. Repeat the saved-task death and restoration, now at child head2.
   Verify new-process counters remain zero before any further explicit action.
8. Read the fresh native story and timeline catalogs through the real UI. A
   remains0, B's root remains1, child is2 with parent/fork1. Do not navigate to
   another scope and intentionally clear the child draft merely to read a head.
   Reselect only the child, verify native reread and the exact retained draft.

The root list's B0 observation belongs to initial fixture creation; B1 is the
current parent after its explicit setup Send. These must not be confused.
Inherited receipts retain their original native source scope; displaying their
text does not rewrite their ownership to the child.

## Mutation observation and expected vectors

`NativeForkGateway` borrows the existing workspace owner. Its optional
`mutationObserver: (() -> Unit)? = null` runs immediately before actual JNI
`register` and `run` attempts, after local input/owner/epoch guards. It records
attempts, including native rejection, not canonical success. Status/lookup and
cancel/close resource operations are outside this mutation observation. The
default null observer preserves ordinary callers, including their existing
one-argument trailing-lambda constructor form.

Only the process-verification MainActivity wires this callback to
`ProcessVerificationProbe.operation("fork_mutation")`. The unchanged closed
12-key probe v1 maps it to `other`; unknown workspace calls still map to
`other` too. No arbitrary names are silently ignored and no payload is stored.

Require these exact vectors for `free_text,submit,prepare,commit,cancel,other`:

| Observation | Vector |
| --- | --- |
| First old process, after explicit parent Send and reviewed fork | `1,0,1,1,0,2` |
| First restored process, before explicit child Send | `0,0,0,0,0,0` |
| First restored process, after that single child Send / second old process | `1,0,1,1,0,0` |
| Second restored process, before any additional action | `0,0,0,0,0,0` |

The two register/run attempts in the first vector are explicitly authorized
setup. No automatic author operation after restoration is permitted. Final
postmortem saved/commands vectors must agree exactly with their pre-HOME
vectors, preventing new-process counter resets from hiding extra calls.

## Presentation and result bounds

Existing timeline-popup and fork-dialog test tags are exported as raw resource
IDs only under the existing opt-in flag. `fork-scroll` tags only the existing
dialog scroll column, allowing bounded traversal inside that dialog. Default
false behavior, user-facing text and callbacks remain unchanged; no system
accessibility setting is altered. Exact menu labels are read only within each
tagged product item, using the existing bounded descendant-label rules.

The complete case retains the existing120s controller cap and per-client
limits; no partial cycle is a pass. Result scope/version remain v1 with the
explicit child case, child fixture and the common process/terminal observations.
Root and child cases require separate fresh cohorts and actual exact-APK
execution. No model, phone, non-root ancestor retirement, sibling-history,
force-stop, power-loss, cancellation-latency or all-API qualification follows.
