# D04 fixed candidate A compile observation v1

Refs #25 (D04.01/.02/.04), #31 (D09.03/.05) and #21.
This private development entry point composes one candidate A CL observation
from the accepted recipe, output-root lease and held-output reader. It
terminates after the compile process, object read and evidence record.
A later six-stage attempt needs its own admission, roots and writer owner.

## Boundary and interface

`createWorkerArtifactCompileObservationV1({config,authority,outputRoots,
outputReader,ports})` returns frozen `{run,cancel,snapshot}`. It performs
no I/O at construction and offers no configurable command. `config` goes to
the accepted recipe planner. Its only tool offer is recipe step zero
(candidate A compile). The compiler policy is exactly
`{timeoutMs:120000,drainMs:5000,stdoutCap:65536,stderrCap:4096}`.
The outer Windows owner must enforce those limits and retain direct
process, pipe and possible descendant writer evidence.

Authority is the exact own-data record `{attempt,baseline,closure,grant}`
with nonzero lowercase SHA-256 values. The captured context is
`{attempt,recipe,baseline,closure,grant}`, where recipe is the hash of the
accepted recipe's JSON. The external owner must validate the actual one-use
grant and the current closure policy. A hash is a binding, not a grant.
Use the same prepared-for-attempt Windows lease and reader configuration.
The entry point owns the exclusive use of both objects until settlement.
Capture the own data methods `prepare,recheck,cancel,close` from outputRoots
and `readNext` from outputReader. The genuine factories remain their
implementations.

`ports` has exact own data methods `check,launch,journal`. These are
trusted private owner capabilities. The check port owns the physical D:
parent, complete current source and transitive headers, selected installed
compiler, ordered environment, approved normal worker, independent temp
ownership, process and storage bounds. Its digests bind those proofs.
The launch port must perform only the given CL offer and journal the actual
direct process and descendant-writer closure. The journal port writes each
offered record exclusively to the approved namespace and acknowledges its
actual bytes. This module supplies none of those Windows ports. It does
not run the six-stage coordinator or mark its unresolved link inputs fresh.

Construction errors throw `WorkerArtifactCompileObservationV1Input`.
The first no-argument run consumes the entry point. Any later run, including
one while pending, rejects `WorkerArtifactCompileObservationV1Used`.
Cancel latches CANCELLED before terminal record selection, signals the
active launcher or reader and asks an offered lease to stop. It returns
true once. Later cancel returns false. Scope methods take no arguments.
There is no retry or promise race. The owner keeps the run promise and all
pending ownership until actual settlement. The frozen snapshot is exactly
`{version:1,kind:'worker_artifact_compile_observation_snapshot_v1',phase,
started,offered,cancelled,writerUnknown,objectUnknown,stop}`. Phase is new, admit, start,
prepare, before, launch, roster, read, after, close, record or done.

## Checks and single-use journal

Each of the three ports returns canonical compact JSON text within 4,096
UTF-8 bytes. A wire shape or binding mismatch refuses. A check receives
`{version:1,context,index:0,when,roster}` and the same signal as a second
argument. When is admit, before or after. Roster is null for admit, otherwise
the SHA-256 of the exact verified lease snapshot. The returned record is
exactly `{version:1,kind:'worker_artifact_compile_check_v1',context,when,
roster,source,headers,tool,environment,normal,temp,storage,reserve}`.
The eight proof fields are nonzero SHA-256 values. Source, headers, tool,
environment, normal and temp agree across all accepted checks. Storage and
reserve attest each fresh checkpoint. Do not obtain CL-only evidence by
setting unrelated library and no-shadow flags.

After the admit check, offer the frozen START record
`{version:1,kind:'worker_artifact_compile_observation_start_v1',context,
preflight,runCount:1}` to journal. Preflight hashes the admit receipt.
The exact journal acknowledgement for START or the terminal record is
`{version:1,kind:'worker_artifact_compile_journal_ack_v1',sha256,stored:true}`,
with the SHA-256 of the offered record. A failed START stops before lease
preparation. The owner must consume the grant before offering START and
never authorize another invocation after a pre-START failure.

Prepare the lease. Require a Ready, complete, known-closed directory roster
with two open owned markers, exactly one 167-byte marker in each fixed root,
distinct ordinary identities and aggregate 334 bytes. The same two roots
and markers must remain. Accept the before check on this roster before
offering the compiler.

## Compiler, object and closure

Launch receives `{version:1,context,index:0,step,policy,signal}`.
The step and policy are derived above and all fields except the signal are
frozen. Mark offered and writerUnknown immediately before the single call.
The result is exactly
`{version:1,kind:'worker_artifact_compile_writer_v1',process,writersClosed,
writerProof}`. Process is the existing exact worker_artifact_process_v1
record at index 0, with the attempt, recipe, baseline and closure digests
from context. Validate its fixed bounds, fields and booleans. A writer
proof is a nonzero SHA-256 binding to actual closure, required only when
writersClosed is true, otherwise null. A malformed process or writer
receipt cannot attest closure. Clear writerUnknown only on a valid receipt
with writersClosed, process.closed, !process.unknown and !process.ioError.
The direct record never claims process-tree containment.

Retain a valid process receipt before applying the semantic gate. Require
known writer closure, exit zero and no timeout, overflow or kill for the
object read. On success recheck the real lease. The active A root must add
exactly the positive bounded object and may add the ordinary recipe
compiler PDB. B stays marker-only. No LINK or MT output may be present.
Recompute logical sizes, require the exact complete roster, and match both
root and marker identities and sizes to prepare. Feed row 0 to the held
reader with the observed A root identity, object identity and length, and
the same genuine signal. Mark objectUnknown before the offer. Clear it
only for a valid scoped proof with known handle closure. Accept only its
exact scoped proof, complete
two-scan accounting and known closure. A known strict COFF refusal is
retained evidence and stops the attempt. After a positive object result,
check after using the post-compile roster digest.

On a stopped attempt, preserve the first cause and any valid observations.
A later unknown writer or reader closure is still recorded even when
cancellation supplied the first cause. If writer closure or object handle
closure is unknown, retain the lease for quarantine. Otherwise try exactly
one explicit close when preparation was offered. Require the lease's Closed
receipt and known closure for all opened markers and streams. Outer owner
postflight still audits partial output, untouched normal bytes and all
temp files, including on refusal. Never reopen or adopt the roots.

## Terminal record

Offer one frozen terminal report to journal, including on refused admit or
START. Terminal acknowledgement failure leaves retained false and preserves
the original report. The report is exactly
`{version:1,kind:'worker_artifact_compile_observation_v1',context,status,
code,started,offered,checks,process,output,writerUnknown,objectUnknown,leaseClosed,
linkAllowed:false,qualified:false}`. Checks has admit, before and after
hashes or null. Process is the validated writer receipt or null. Output is
the validated held reader result or null. Status is observed only with
successful checks, known closure and a positive object fact, otherwise
stopped. The report is bounded to 16 KiB UTF-8 JSON. Code is null on success or one of CANCELLED, PREFLIGHT, START,
LEASE, ROSTER, PROCESS, CLOSURE, OBJECT, POSTFLIGHT. `run` returns frozen
`{report,retained}`. No report grants LINK, artifact adoption or runtime
qualification.

Independent FIRST exercises the actual recipe and the lease/reader cores
with bounded in-memory adapters, plus controlled owner ports for receipt,
writer, cancellation and journal failures. Native CL and output reads
need a separate exact packet with current pins, complete output and temp
reserves and an explicitly authorized candidate A-only offer.
