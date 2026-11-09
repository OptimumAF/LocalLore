# D04 native parent for one Windows compiler attempt

Refs #25 (D04.01/.02/.04), #31 (D09.03/.05) and #21.
This private Windows x64 source owns the Node entry for the candidate A
compile supervisor. It shares the compiler launcher's Win32 Job and pipe
mechanics. It has no CLI, build target, download, or automatic retry.
Future admission still needs the actual runner and the checked inputs.

## Fixed plan

Call `locallore::compile_parent_v1::Parent::run(plan, cancelled)` once
from a dedicated, single-threaded, admitted parent. The private Plan
contains exactly three file pins with canonical D: paths, exact lengths,
and SHA-256 digests. The leaves are `node.exe` (128 MiB maximum),
`worker_artifact_compile_attempt_v1.mjs` (2 MiB), and
`locallore-compile-host-v1.exe` (8 MiB). The entry is the sealed,
self-contained attempt module, with only pinned built-in Node modules as
external imports. Building that entry and the helper and pinning their
provenance are separate steps.

The Plan also binds existing, distinct evidence and private temp
directories. Neither may overlap a protected input directory. Scope,
spent grant, independent writer policy and external namespace proof are
nonzero SHA-256 values referring to actual retained records. This
component does not mint any of those decisions. The enclosing owner
must validate their bytes and scope and reserve all outputs first.
It must also establish the protected DLL/loader cohort and a sealed
input namespace, including no competing writers or fallback siblings.
Open handles do not establish the absence of an external PDB service
or exclude concurrent users from a directory.

## Held Windows objects

Open the actual mounted D: root and each needed ordinary ancestor
without delete sharing, reject reparse points, and check the final
normalized handle path and volume. The D: root must resolve to its
mounted volume GUID root. Hold a read handle to each file with read
sharing only, rejecting hard links. Compare exact lengths, scan once
on each held handle with SHA-256 and an EOF probe, and recheck the
same metadata and identities. This is at most 138 MiB of selected
payload plus three EOF probes. Use CNG SHA-256 through bcrypt.
The acquired exact files stay held through process and Job observation.
The directory lease prevents renaming held directory objects. It does
not prevent insertion of a new child name, so the outer sealed-directory
proof remains necessary.

## Suspended admission

Start the pinned Node executable directly with the sealed entry as its
only argument. Use the exact application name, bounded private pipes,
no window, and explicit Unicode environment. The parent sets
`LOCALLORE_COMPILE_PARENT_READY` to its fixed evidence leaf
`parent-ready.json`. There are no other parent-supplied script arguments
or inherited environment variables. The child is created suspended
inside a new unnamed Job by the creation-time Job list. Its three
standard handles are the only inherited handles. The parent closes its
copies of the child ends before any readiness evidence.

Read back the exact kill-on-close flag, without either breakaway flag,
before creation and while suspended. Verify actual membership using the
child handle, one active process in this new Job, and its exact image path.
Record whether the parent itself is in a Job as an observed fact. The
outer admission covers relevant ancestor restrictions and independently
checks this arrangement. Refuse if association fails. Resume only
after successful ready retention and another cancellation and deadline
check. The previous suspend count must be one.

The canonical compact ready record contains version, kind
`compile_parent_ready_v1`, scope, spend, writerPolicy, namespace,
evidenceId, tempId, parentPid, nodePid, jobFlags, parentInJob,
activeProcesses and three ordered pin records (Node, entry, helper).
Each pin contains id, sha256 and bytes. Ids bind the actual volume
serial and file ID. Ready is an observation of suspended admission,
not evidence that the process resumed, compiled, or shut down.

Use create-new, write, flush and exact readback, close the write handle
and reopen read-only with the same identity and exact bytes. The
read-only ready handle stays held. The parent returns the ready SHA-256.
An entry must verify the exact ready record and its own PID against the
private plan before supplying the supervisor's admission bindings.
A failed or partial ready file is preserved. There is no second offer.

## Completion and remaining evidence

Use one 180-second parent window including setup and a single five-second
observation window for cleanup. Retain the bounded direct result with
exit, Job count, true pipe EOFs and known handle closure. The enclosing
runner records the returned captures and elapsed time. Maximum parent
outputs are a 4,096-byte ready record, 65,536-byte stdout and 4,096-byte
stderr, before the runner's separate records and the child supervisor's
reserves. Do not reuse a quarantined object or its directory. Retain the
parent object and its held handles when group closure is unproven. The
fallback kill-on-close policy never substitutes for observed Job zero.
A known lease close is recorded separately. External postflight still
audits the actual directories and outside-writer exclusion.

No compiler, Node, filesystem fixture, native process or app ran in
this source slice. Windows x64 verification must exercise compatibility
of the held PE and script with the actual loader, creation-time Job
membership, ready refusal and exact readback, separate process and pipe
closure, cancellation, timeout, overflow and quarantine. A later
candidate A compiler launch needs its own fresh admission. LINK,
artifact adoption, model inference and desktop qualification are
separate gates.
