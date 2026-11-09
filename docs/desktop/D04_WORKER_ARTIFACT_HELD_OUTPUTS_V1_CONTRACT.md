# D04 held worker output reads v1

Refs #25 (D04.01/.02/.04), #31 (D09.03/.05) and #21.
This contract specifies the private reader used by the stage inspector
after an owned CL, LINK or MT process has closed. The coordinator accepts
content facts for the object, executable and manifest. These facts must
come from the files this attempt actually produced. Retained hashes from a
prior build cannot establish the new output.

## Fixed recipe and caller boundary

The proposed Windows factory is
`createWorkerArtifactHeldOutputsV1({config})`. It derives every pathname
from `planWorkerArtifactComparisonV1`. It performs no I/O during
construction. The test factory
`createWorkerArtifactHeldOutputsV1ForTesting({config}, adapter)` injects
only ordinary identity, held read and monotonic clock operations. Both
return a single-use reader with `readNext(request, signal)` and
`snapshot()`.

The injected adapter contains exactly four own data functions.
`identifyRoot(path)` returns `{identity,ordinary,real}`.
`identifyFile(path)` returns
`{identity,ordinary,real,bytes,links,modified,changed}`.
`openRead(path)` returns an owned handle with own data methods
`stat()`, `read(buffer,offset,length,position)` and `close()`.
The held stat returns the file identity record without `real`. Length and
link count are integers. The two timestamp fields are canonical signed
64-bit decimal nanoseconds. Read returns a byte count and close returns undefined.
`now()` returns finite nonnegative monotonic milliseconds. The native
adapter uses guarded `lstat`, `realpath` and positional FileHandle reads.

The private stage owner must already have a known-closed writer, a current
complete and in-budget roster from the admitted output lease, and reserved
time and read bytes. It supplies exact own data
`{index,candidate,role,rootIdentity,fileIdentity,bytes}` using the observed
row. Root and file identities are canonical unsigned decimal dev:ino
tokens with nonzero inode, on the same device and distinct. `bytes` is
the observed positive length. The owner retains the lease and reservation
through actual settlement. The reader consumes only the next fixed row.

| Stage | Candidate | Ordered roles |
| --- | --- | --- |
| 0 after compile | A | object |
| 1 after link | A | object, executable, manifest |
| 2 after embed | A | object, executable, manifest, preEmbedCopy |
| 3 after compile | B | object |
| 4 after link | B | object, executable, manifest |
| 5 after embed | B | object, executable, manifest, preEmbedCopy |
| 6 compare | A then B | object, executable for each |

This is one sequence of 20 offers. The factory accepts no pathname, command,
arbitrary role or fallback. A second operation while one is pending rejects
without replacing the pending operation. A refusal, cancellation or unknown
closure stops further offers. The owner may reuse the same attempt's verified
facts in reports, and has no retry or alternate file path. The owner enforces
stage-specific freshness and checks all ordinary output and temporary files.
The reader does not confer permission to spawn or release anything.

Invalid construction throws `WorkerArtifactHeldOutputsV1Input`. Busy or
already terminal offers reject with the fixed Busy or Stopped suffix.
Wrong request shape, sequence or signal produces one terminal REQUEST
result before file I/O. Capture the same genuine signal for the attempt.

## Held read and evidence

Require the known root and selected ordinary one-link file to match the
expected real pathname, identity and length. These are cooperative
pathname and held identity checks under the private owner contract.
They are not an OS no-follow guarantee. Compare
named and held fingerprints including device, inode, link count, length,
modification time and change time. A regular-file handle is opened read-only.
Capture its own close method before any post-await cancellation or validation.

Read the exact positive length twice from that one handle, at most 64 KiB per
positional read, with one EOF probe per scan. Accept short reads with positive
progress. Hash the payload from both scans and require equality. Check the
held fingerprint before and after each scan, then recheck the root and
named file. Return a positive fact only after known close. Track actual
returned read counts even when the operation subsequently refuses. An
unattested read or cleanup remains uncertain. Never delete, rename, reopen
or substitute output.

The file limit is 64 MiB and manifests additionally have a 64 KiB limit.
Reserve both complete payload scans and the two probe bytes before each
offer. The fixed sequence provides an overall upper bound of 20 such
reservations and 2,684,354,600 read bytes. At most one 64 MiB object buffer and one 64 KiB scratch buffer
may be held for parsing. Other roles stream through the scratch buffer.
Never return raw file bytes. The owner must record the actual smaller
per-stage forecast before any native offer.

Use a private follower of the supplied genuine abort signal and a
four-second monotonic cooperative deadline per offer. A pre-aborted signal
does not offer file I/O. Keep monotonic history across the reader. Fence new
reads before and after every awaited operation and around parser entry.
Cancel or timeout does not race the promise away from the
owner. Retain a late handle long enough to close it once. Closure is attempted
even after an earlier refusal and cannot overwrite its first reason.
`snapshot()` exposes a bounded private status, current sequence position,
pending state, accumulated exact byte counts and closure uncertainty. The
stage owner separately retains a terminal coordinator report and drains
any pending output observation before releasing its lease. Future
`inspectOutputs` and `compare` positional abort wiring must supply the
same coordinator signal across the complete attempt.

Check cancellation first, then clock and elapsed time. The deadline is
inclusive at 4,000 ms. Capture a returned handle or known count before the
post-await check. An opaque rejected operation is IO, with read or closure
uncertainty recorded as applicable. On cleanup, check liveness before and
after the one close attempt. Keep the first latched cause. A known close
after timeout cannot turn the stopped read into a positive result.

## Reuse the accepted COFF parser

At index 0 or 3, pass only the matched object bytes to the accepted
`inspectLibraryInputs` parser. Reject an archive container, import object,
unsupported machine, nonordinary or malformed object. A successful parse
must describe exactly one bare x64 object and zero imports. Check and refuse
`!<arch>\n` before parsing because a one-member archive can return the
same object count. Permit bare x64 BigObj accepted by the strict parser.
The private metadata is exactly `{directives,defaultLibraries}`, with at
most 64 entries across both lists and 8,192 UTF-8 JSON bytes. A strict parse
refusal stays a refusal. Later object reads verify bytes
and hashes and reuse the original compile proof.

The parser supplies structure and the default-library names it found.
The stage owner must still reject unreviewed directive tokens, apply the
approved resolution policy, and prove the current ordered search and
absence of earlier shadows before LINK. An earlier archive observation or
a historical name catalog cannot stand in for that proof. Bind the new
object hash and resolved directive proof in the stage journal before
offering LINK. Leave the pre-admission closure policy digest stable.

Each result is frozen
`{version:1,kind:'worker_artifact_held_output_v1',index,candidate,role,ok,
code,file,metadata,io,unknownClosure,ioUncertain}`. A successful file fact
is exactly `{sha256,bytes}`, with null metadata outside a compile row.
A refusal has null file and metadata and one fixed code from REQUEST,
CANCELLED, DEADLINE, CLOCK, IDENTITY, CONTENT, COFF, IO or CLOSE. An
unbound REQUEST has null index, candidate and role. Counters are
`{reservedReadBytes,actualReadBytes,opened,closed,verifiedScans}` with
canonical unsigned decimal strings for byte totals and integers for counts.
The snapshot is frozen
`{version:1,kind:'worker_artifact_held_outputs_snapshot_v1',next,pending,
completed,stop,io,unknownClosure,ioUncertain}`. The next and pending values
are null or the fixed row ordinal from 0 through 19. A latched stop makes
next null while any actual pending operation remains visible.

The owner separately checks expected stage roles, unchanged
object and manifest hashes, verified pre-embed copy, final executable
hashes, and A/B equality before producing the coordinator receipts.

## Verification boundary

Before implementing, claim the reader and independent synthetic FIRST paths.
Freeze checks for fixed order and scope, changed names or identities, content
drift across scans, short and malformed reads, EOF, caps, cancellation, late
open and unknown close. Use the real strict parser on a fixed x64 object
with a directive, a valid bare BigObj and a one-member archive to test the
envelope refusal. A later actual packet must bind new compiler output and the
stage owner's current tool, input and resolution proofs. This contract
does not authorize inspection of a real output or any process launch.
