# D04 compiler search directory change detection v1

Refs #25 (D04.01/.02/.04), #31 (D09.03/.05) and #21.
This native development guard detects changes to the exact admitted
absence-parent directories and helper directory while the owned compile
attempt runs. It supplements the held positive files, named absence
checkpoints and independent sealed-namespace requirement.

## Arm before checking absence

Use the existing parent Plan and actual held directory identities.
Arm one notification request for each distinct admitted absence parent
and the fixed helper directory, before the first absence sample.
The helper directory covers the two fixed libuv fallback names.
Verify the separately opened watch handle matches the held native
directory identity, canonical path and ordinary object type.
Use read access, no delete sharing, one manual-reset event and one
overlapped request per directory. No recursive watch, volume-wide
journal, external service lookup, event-name retention or new output
file is introduced. The evidence directory is outside the watch scope.

Each watch has a stable DWORD-aligned 4,096-byte buffer.
The existing directory count cap limits the set to 256 watches and
1 MiB of notification buffers, plus the corresponding handle and
operation state. Request file and directory names, attributes,
size, last write, creation and security changes. Do not request last
access, because normal reads are part of the qualification flow.
The guard is fail-closed on any delivered change, even an unrelated
name inside a watched directory. It never parses or publishes the
notification names.

## Refusal and shutdown

Poll every armed watch at explicit admission boundaries, before and
after READY retention, while supervising the owned Node Job, and after
the child returns. The in-Job poll uses a ten-millisecond cadence.
Any observed nonempty completion, zero-byte completion or provider
loss refuses. An in-Job watch refusal requests termination through
the existing owned Job path. The parent records it separately from
caller cancellation. Existing CL launcher defaults stay the same.

At retirement, first collect completed notifications. Request
cancellation once per still-pending exact operation, then observe
actual completion. CancelIoEx success or ERROR_NOT_FOUND alone
does not prove completion. A normal completion racing cancellation
still refuses. A canceled completion is expected only after the
parent's own request. Pending, failed or ambiguous observation
cannot produce success. There is one shared cleanup cutoff for the
Job, pipe, postflight and watch evidence. If no process was created,
use one bounded cleanup window within the absolute parent limit.
Never start a separate five-second clock per watch.

The parent report records armed watches, watches that delivered a
change, loss observations, scoped cancellation attempts, pending
operations and known watch handle closes. These are observations
about this exact set. If an operation is still pending, do not close
or free its directory handle, event, OVERLAPPED or buffer. Retain
the parent object and existing leases in quarantine. If the parent
object is destroyed while a watch remains pending, its stable watch
allocation is kept until process exit so the kernel cannot write into
freed memory. Do not reuse the parent or its namespace.

## Evidence boundary

A clean notification shutdown means no change was delivered to these
requests before their known retirement. It does not prevent namespace
changes, authenticate complete ordered search topology, provide a
filesystem event trace, or prove outside-writer exclusion. The parent
still requires the independently established sealed input/loader
namespace, the checked positive files and exact absence slots.
The live outside-writer check remains separate before the artifact
reader. An otherwise positive child result cannot qualify if the
native parent observed change, loss, late cleanup or unknown closure.

A separately admitted synthetic Windows packet needs actual evidence
for quiet retirement, a created or renamed shadow, helper fallback
change, overflow or loss, change racing cancellation, cancellation
with known completion, and an unconfirmed completion that retains its
buffer and event. The existing input and compile budgets and a
separate exact native grant still apply. No filesystem watch, Node,
fixture, SDK read, build, compiler, app, model or device was run for
this source slice. PR #403 and PR #420 remain separate pending packets.
