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

## Held read and evidence

Resolve the known root and selected ordinary one-link file without following
an alias. Require the expected real pathname, identity and length. Compare
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
reservations. At most one 64 MiB object buffer and one 64 KiB scratch buffer
may be held for parsing. Other roles stream through the scratch buffer.
Never return raw file bytes. The owner must record the actual smaller
per-stage forecast before any native offer.

The supplied genuine abort signal and a four-second monotonic cooperative
deadline fence new reads before and after every awaited operation and around
parser entry. Cancel or timeout does not race the promise away from the
owner. Retain a late handle long enough to close it once. Closure is attempted
even after an earlier refusal and cannot overwrite its first reason.
`snapshot()` exposes a bounded private status, current sequence position,
pending state, accumulated exact byte counts and closure uncertainty. The
stage owner separately retains a terminal coordinator report and drains
any pending output observation before releasing its lease. This boundary
also applies to future positional abort wiring for the inspector port.

## Reuse the accepted COFF parser

At index 0 or 3, pass only the matched object bytes to the accepted
`inspectLibraryInputs` parser. Reject an archive container, import object,
unsupported machine, nonordinary or malformed object. A successful parse
must describe exactly one bare x64 object and zero imports. Its bounded
directive and default-library lists stay in the private owner journal.
Emit at most 64 distinct entries and 8 KiB of encoded metadata per
compile object. Refuse oversize output. Later object reads verify bytes
and hashes and reuse the original compile proof.

The parser supplies structure and the default-library names it found.
The stage owner must still reject unreviewed directive tokens, apply the
approved resolution policy, and prove the current ordered search and
absence of earlier shadows before LINK. An earlier archive observation or
a historical name catalog cannot stand in for that proof. Bind the new
object hash and resolved directive proof in the stage journal before
offering LINK. Leave the pre-admission closure policy digest stable.

The reader's positive result contains only the fixed index, candidate,
role, exact SHA-256 and byte length, and the bounded compile metadata when
applicable. It reports no qualification flag that the caller can use as
authority. The owner separately checks expected stage roles, unchanged
object and manifest hashes, verified pre-embed copy, final executable
hashes, and A/B equality before producing the coordinator receipts.

## Verification boundary

Before implementing, claim the reader and independent synthetic FIRST paths.
Freeze checks for fixed order and scope, changed names or identities, content
drift across scans, short and malformed reads, EOF, caps, cancellation, late
open and unknown close, and real accepted parser behavior on fixed synthetic
COFF bytes. A later actual packet must bind new compiler output and the
stage owner's current tool, input and resolution proofs. This contract
does not authorize inspection of a real output or any process launch.
