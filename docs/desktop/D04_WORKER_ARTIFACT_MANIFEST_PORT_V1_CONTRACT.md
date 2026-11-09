# D04 worker artifact manifest port v1

Refs #25 (D04.01/.02/.04), #31 (D09.03/.05), #21.
This development port composes the fixed coordinator, the output-root lease
from #400 and the exclusive pre-embed copy from #395. The supported setup
installs its `prepareManifest` function in the coordinator's existing ports
record. It runs after LINK has been inspected and before the coordinator
offers MT. The caller owns the independently admitted output lease and copy
session. The port can therefore be tested with the same real coordinator and
injected, memory-only helper adapters.

## Owner boundary

Create the port for one independently admitted attempt after establishing the
expected physical D: target, exact recipe and provenance, real writer
exclusion, and full remaining reserves. The owner provides the same config and
context it gives the coordinator. Use the already prepared, same-attempt
output lease and the same-recipe exclusive copy object. The owner must
serialize the port with any build child and any other use of either helper.
The lease observes direct files under its private roots. Its logical size
does not include output elsewhere or previously retained records. The
owner's supplied `maxBytes` bounds these two rosters and must fit within
the separately reserved allowance.

The contract is cooperative. It relies on owner-controlled quiescence between
LINK and MT and on the copy helper's held-handle hash verification. It does
not prevent a hostile concurrent writer from replacing a file after a check.
Output rows do not prove source freshness, object directives, compiler temp
ownership or final PE identity. Stage-specific checks, fresh admission and
actual process closure remain the owner/coordinator responsibilities.

## Interface

`createWorkerArtifactManifestPortV1({config,context,outputRoots,preembedCopy,maxBytes})`
returns frozen `{prepareManifest,snapshot,drain}`. The config is passed to
the accepted recipe planner. Context contains the exact four nonzero
lowercase hex64 digests `attempt,recipe,baseline,closure`. The recipe digest
must equal SHA-256 of the fixed recipe JSON. `maxBytes` is a safe integer
from 1 through 67108864. Capture `outputRoots.recheck/cancel` and
`preembedCopy.copyNext/cancel` as own data methods. The real objects also
have their existing methods, including the owner's lease close. Creating
this port performs no I/O. Invalid setup throws
`WorkerArtifactManifestPortV1Input`.

The coordinator passes its existing AbortSignal as a second positional
argument to `prepareManifest(request, signal)` only. The request object and
all receipt/report shapes are unchanged. The original five-second port
deadline and original cancellation grace are unchanged. The signal is the
same object for both manifest offers and launched steps. A valid request has
the exact keys and data described in the coordinator contract, matches the
captured context and the exact fixed manifest step, and supplies positive
nonzero-hash LINK facts. Accept index 2 for A then index 5 for B. Accept B
only after the complete A port succeeds and with the same signal object.
Malformed, wrong-context, repeated
or out-of-order requests stop an idle port before any helper call. A concurrent
offer rejects `WorkerArtifactManifestPortV1Busy` and leaves the active one
owned. Other refused operations reject `WorkerArtifactManifestPortV1Stopped`
without copying a thrown value or inventing positive file facts.

`snapshot()` returns frozen
`{version:1,kind:'worker_artifact_manifest_port_snapshot_v1',pending,next,
completed,stop,copyCode,uncertain}`. `pending` is null, `before`, `copy`
or `after`. `next` is 2, 5 or null. While pending, it still names the
current index unless a stop has latched. `completed` counts successful
receipts. `stop` is null or `REQUEST, CANCELLED, ROSTER, BUDGET, COPY,
UNCERTAIN`. `copyCode` is null or the recognized fixed failure code from
the current copy receipt. No paths, identities or raw diagnostics enter
this snapshot. `drain()` waits for the currently offered operation's actual
settlement and returns a snapshot, including when the offer rejects. The
owner calls it after the coordinator is terminal and retains the whole
reservation and both helpers while an operation is pending. If uncertainty
remains after settlement, the owner preserves the evidence and quarantines
the attempt. The coordinator's process-specific closure field and its
terminal record cannot authorize lease reuse.

## Sequence

1. Bind the request and genuine signal before I/O. Publish pending ownership
   synchronously before either helper is offered. Listen for abort and check
   the signal again before the first offer. Abort latches `CANCELLED` and
   asks both helpers to stop once, even if one stop request throws. Helpers
   are awaited through settlement. Detach the listener after settlement.
2. Recheck both roots. Require a Ready snapshot with complete, known-closed
   directory scans, open owned markers and `withinBudget:true`. Bind
   the active root and its object, executable and manifest rows. The object
   is positive, the executable and manifest lengths match the LINK facts,
   and the pre-embed name is absent. At A, the B roster contains just its
   marker. At B, the A roster still contains its pre-embed file. Reserve
   `observedBytes + linked.executable.bytes` exactly within `maxBytes`.
   Recompute both passes' aggregate from their bounded file rows and require
   exact agreement with each reported total.
3. Ask the exclusive copy to preserve the active executable, using the
   observed root, executable and manifest identities and the LINK facts.
   Wait for the actual copy receipt and inspect it even after abort. Require
   the correct candidate, `ok:true`, known cleanup, no uncertain I/O and
   exact matching executable, manifest and copy facts. The port never creates
   an alternative output or retries a refused copy.
4. Recheck both roots again. They must retain the same identities and every
   previous file's name, identity and size. Only the active root may gain
   exactly its fixed pre-embed file. Its length must match the verified copy
   and aggregate growth must equal that length within `maxBytes`. The
   approved helper and quiescent-owner contract bind content through the
   copy's held verification. The roster recheck binds the later observation.
5. While still live, return canonical JSON for
   `worker_artifact_manifest_v1` with the four context digests, index,
   `ordinary/exclusive/equal/withinBudget:true` and the existing
   `manifest/preEmbed/copy` facts. The coordinator still independently
   checks the receipt and runs `recheck(manifest)` before MT.

An abort or failed validation latches the first reason and fences new work.
An offered helper that throws or produces a malformed receipt is uncertain
because settlement alone does not attest cleanup. Known lease stop snapshots
can report failure without uncertainty when closures are known. A reported
unknown close or uncertain write remains uncertain, even if cancellation
already supplied the first reason. Invalid, failed or late completion never
emits a positive manifest receipt. There is no port-level timer race or
release on coordinator timeout.

## Evidence gate

Independent FIRST covers the two-manifest coordinator path, pre/post roster
and reserve refusals, cancellation before and during I/O, a coordinator
deadline with a still-held copy, and quarantine after uncertain completion.
Keep the original coordinator, lease and copy FIRST suites. Source review
and Git checks are distinct from execution. Actual synthetic execution,
Windows output/copy I/O, compile/link/MT and desktop qualification require
their applicable evidence and admission. This port never launches a tool.
