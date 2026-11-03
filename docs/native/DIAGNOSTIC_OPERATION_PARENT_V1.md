# Fixed SDK17 parent deadline

B108. Refs #14 M10.03 DIAGNOSTIC_UI_OPERATION_READINESS, supporting M10.02.
The frozen [SDK17 fresh handoff](DIAGNOSTIC_UI_FRESH_HANDOFF_V1.md) enforces a
2400-second budget, but its hard job begins after expensive preflight. The
general host `runtime_spike.run_process` accepts at most180seconds and cannot
simply be passed2400. This small separate parent uses the reviewed owned-job
mechanism to supervise the **entire frozen fresh invocation**, including its
canonical source and928-file installation preflight. It does not change the
general runner's limit, the1800-second guest, app, engine, APKs or dependencies.

## Fixed metadata and source

`scripts/diagnostic_operation_contract.py` defines only pure metadata checks.
`scripts/run_diagnostic_operation.py` binds a single parent scope, operator,
contract, proposed operation and inner authority. Its only public switch is
`--authority-sha256`; neither target/profile, registry, command nor executable
is caller selectable. Parent authority fixes2400seconds, permits one operation,
forbids model and retirement, binds frozen B107 head
`62ffccfef23e737bd4a6049faf3edb0e558df093`, and records human approval provenance.
The inner authority's proposal and approval reference must match. These are
local records of explicit reviewed consent, not authentication against a local
administrator. No record or successful validation supplies missing consent.

The operator remains a raw D: snapshot at the packet's fixed candidate path.
Managed worktree creation refused the physical repository's attachment scope;
the refusal is preserved. There is no invented clean-Git/head claim, C: project
or `git worktree` bypass. Runtime source stays the unchanged B105 snapshot;
the inner operator/rules come from their **original fixed B107 path**, not the
copied scripts under this new snapshot, whose computed operator ROOT differs.
Unmerged #383/#382/#381/#380/#377 remain explicit dependencies.

Before runtime imports, bootstrap checks the fixed frozen handoff, all27 small
runtime source bindings and both B107 files. Every imported project module must
have that source origin and a basename in the hash-bound set. Current Python
executable/runtime-DLL bindings must equal the frozen handoff before an attempt
or native job, and are rechecked with authority reads. The imports perform no
SDK, ADB, guest, model or ledger operation. This adds no runtime version choice.

The frozen activation's import-only loader prepends its source directory on
first initialization. The parent scopes that initialization inside a temporary
source-path context and restores it afterward, then restores the original path
before the inner invocation. The actual frozen fresh importer therefore retains
its strict single-source/origin checks. It never accepts a foreign path or
weakens a count assertion to hide duplicated namespace locations.

## One parent attempt, then owned child

Small fixed source/runtime/authority bootstrap and final metadata reads are
cooperative. The2400-second clock starts at CLI entry; these steps consume its
budget. This is not hard preemption of bootstrap OS/file I/O, Python startup or
final metadata reads. The hard job deadline covers the spawned child and all
of `fresh._execute(fresh_authority, original_begin)`, including the expensive
inner preflight. Checked child/pipe cleanup follows the deadline; it is not an
OS disk/memory quota or an extension to the guest deadline.

Both actual authority files must exist and match separately reviewed exact
scope. Live-parent, inner-live and guest roots must be unused. A create-only
parent live directory and durable no-retry attempt are written before spawning.
A failed preflight or partial parent publication remains spent; nothing is
removed, repaired or retried automatically.

The child reads a distinct parent barrier before operational imports. The
parent must assign its new process to the owned Windows job and publish the
exact started/request join before releasing that barrier. Worker/parent native
creation/executable identities and one-use authority/attempt/request joins
precede the worker claim and inner invocation. Parent-side code never calls
`fresh._parts`, `fresh.read_authority` or other inner operational helpers.
Only pure rules and import-only definitions are used outside the assigned child.

The native job and capture use the same reviewed supervisor body as corrected
B107, with strict literal-True close results. Unknown job, reader, capture,
identity, deadline, publication or worker state cannot qualify success. Parent
exceptions explicitly retain failure, including cancellation after a positive
inner result. Only the owned job/process and its streams are closed.

## Final joins and storage ownership

The inner frozen helper still owns preparation, current capacity/admission,
installed/external-state checks, run-input creation, one activation, and all
underlying guest/private-server ownership. A parent wrapper is not a replacement
for those gates. No broad shell, alternate registry, model role, recovery,
retirement or additional instrumentation is introduced.

The worker binds the exact inner final result. Parent qualification rechecks
that fixed final file, its authority/attempt, known inner job/capture completion,
stage/input/activation/runtime joins and current closed ledger-v2 entry, without
calling an inner operational helper outside the job. The guest proposal must
match the accepted run-input result; recovery/retirement must be absent for this
fresh guest. Current storage validation rechecks its existing proof history.
Parent native closure and accepted storage closure remain distinct facts.

Timeout, interruption or partial output never causes this parent to hand-mark
storage closed. The inner guard owns that operation; unknown outcomes remain
failed/charged and their images, attempts, captures and records stay intact.
This operator cannot delete guest images or restore/reuse a spent root.

## Actual operation remains gated

Imports and host tests create no real parent/inner authority. Those files remain
absent until fresh applicable human approval. Synthetic ports and benign literal
Python host children do not qualify SDK17 preparation, Android, SAF, offline
traffic/privacy, JNI/ARM64, phone or model performance. See the separate packet
verification report for exact executed coverage, failures and preservation.

Current storage has two unretired roots and cannot admit the new40GiB guest.
The refreshed nine-image retirement proposal is a **separate irreversible
operation**: it requires its own exact authorization and the reviewed SDK15-aware
executor. This parent grants no retirement. After any successful retirement,
fresh resulting-ledger/capacity/installation/resource/port/ownership checks and
a separately reviewed SDK17 operation/authority are required. Do not transform
old SDK16 target text, a hypothetical ledger or a spent answer into a run grant.
Other emulators/shared ADB, settings, the older model guest and all records stay
preserved. No merge or release is part of this work.
