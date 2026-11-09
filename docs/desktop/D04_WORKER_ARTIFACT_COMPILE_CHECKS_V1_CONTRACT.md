# D04 live Windows compiler checks v1

Refs #25 (D04.01/.02/.04), #31 (D09.03/.05) and #21.
This check port observes the fixed candidate A compile inputs, output
lease and storage at admit, before and after. The existing library
cohort reader remains separate. No code here discovers an SDK, runs
a compiler, creates candidate roots or attests writer closure.

## Sealed inputs and bounds

The sealed attempt constructs the production check with
`createWorkerArtifactCompileChecksV1(manifest, targetRoot, inputCatalog,
checkManifest)`. The exact manifest has pins, absent, topology, roots and
diskFloor. It is reviewed and bound before admission, and never loaded
from a runtime user path. The constructor validates and freezes one copy,
then compares both digests before the attempt performs any file I/O.
Each pin is an exact
`{role,path,identity,bytes,sha256}`. Roles are source, headers, tool
and normal. Require the actual worker main.cpp, compiler cl.exe and
one approved normal worker pin. Other source pins stay under the worker
directory, header pins under the worker, selected upstream A or ordered
INCLUDE roots, and tool pins under the selected compiler directory.
Every pin must have a distinct path and Node file identity. Library and
model payloads are excluded.

An absent row is exactly `{path,parentIdentity}`. It is a fixed
shadow or loader candidate in those admitted include or tool directories,
with an existing known ordinary parent. Only ENOENT for the leaf,
bracketed by a stable parent identity and metadata, can count as absent.
This is not a recursive search. Topology is the digest of the independent
complete source/include-resolution and loader admission. The outer owner
must establish the actual full dependency cohort, ordered search and
the complete absence roster for that cohort, then hold the admitted
physical input and namespace proof through CL. These checks reobserve
the declared scope. Pre/post agreement is not a continuous write lock
or proof that no external writer existed.

At most 1,024 pins and 2,048 named absence slots are accepted.
Each pin may hold at most 128 MiB. One phase can read at most
512 MiB including a one-byte EOF probe per pin. A future exact
execution must authorize its actual paths, counts and read bytes
across all three phases. These design maxima provide no run authority.
Check ordinary resolved named paths, expected Node identity and size,
the same held metadata, exact SHA-256, actual EOF and known handle
close, then recheck the named identity. A deadline or cancellation
never skips owned cleanup. Each phase allows at most ten seconds of
observed guard time within the native parent's separate full deadline.
A late filesystem return refuses. The parent remains responsible for
a blocked OS call and for outside-writer exclusion.

## Complete Node manifest binding

`workerArtifactCompileCheckManifestV1(manifest)` hashes compact UTF-8
JSON. Its top-level key order is version, kind, pins, absent, roots,
topology and diskFloor. Version is 1 and kind is
`compile_check_manifest_v1`. Setup canonicalizes field order, preserves
the ordered pin and absence rows, and writes roots as a temp, target,
evidence array with role first in each root. The digest covers Node file
and parent identities, root identities and caps, per-phase reserves and
the free-space floor. `checkManifest` is part of the profile used to
compute the native READY scope. `inputCatalog` remains the separate
cross-language catalog and already binds the target path. A change that
leaves the native catalog unchanged still requires a different scope if
it changes the Node manifest. This binding does not establish loader
closure, prevent writes, or replace independent writer evidence.

## Measured phase storage

Roots is the exact temp, target and evidence map. Each root has
identity, maxBytes, maxEntries, maxDepth and pending. Pending has
numeric admit, before and after byte reserves. DiskFloor is the
independent free-space floor, at least 1 MiB. The real root paths come
from the verified profile. Require one admitted D: volume, distinct
root identities, at most 512 rows and depth eight per root, and
no aliases or nonordinary entries. Walk using bounded directory
reads with one-entry buffering, verify each named identity and actual
held link count for files, record logical bytes and
recheck each directory across its read. Require total plus pending
to fit each separate cap, then observe BigInt available blocks times
block size for the admitted volume and require the floor plus
all remaining reserves. This is a live observation and budget
check. It is not a disk quota or allocation guarantee.

Admit sees an empty target and only native READY in evidence. Before
sees the two candidate marker roots and READY, check-admit and START.
After sees the same actual lease identities and the accepted candidate
A object roster, with B still marker-only. Evidence now contains
the earlier checks, START/OFFER, request, response and stderr,
transport and CAPTURE. Keep independent input/authority/writer
records outside this exact evidence root. Match every target row to
the production lease snapshot that #408 already validated and hashed.
Do not advance the lease during the check. Reserve the full remaining temp capacity at admit and before. Keep
enough target reserve for the full profile bound before compilation
and enough evidence reserve for all still-absent fixed leaves. The three
new check files add at most 12,288 bytes to the earlier supervisor
allowance, for eleven leaves and 184,412 bytes. Parent-ready is separate
and capped at 4,096 bytes.

## Exact check retention

The same compile observation calls check at most once per phase.
The sealed entry provides the real lease snapshot on before/after.
The check returns the existing compact #408 wire with actual
source, headers, tool, environment, normal, temp, storage and reserve
digests. Stable fields are phase independent. Storage and reserve
hash the current bounded inventories and physical availability.
The retained wire contains those digests, not a copy of every
observed file row. Underlying independent admission and live
outside-writer proof are separate retained evidence.

Before #408 uses a successful check, the supervisor uses its existing
create-new write, flush, close and exact readback path to retain
check-admit.json, check-before.json or check-after.json. START binds
the actual admit hash. The compiler offer needs the retained before
check, which is rechecked with START/OFFER before spawn and bound
in the transport record. Terminal binds every check hash it claims,
requiring all three and actual readback for observed status. A lost or
changed retained wire can leave a fixed terminal retention-refusal record
binding the offered report hash without acknowledging that report. An
earlier refusal or incomplete check can still retain a stopped terminal
record.
No repeated check offer or partial-file overwrite is permitted.

Source review and Git checks do not exercise Windows behavior.
An exact admitted manifest, actual sealed bootstrap, hold-through-CL
proof, independent outside-writer check, and bounded synthetic and
real Windows packets remain required. No Node, SDK, fixture, build,
compiler, app, model or device operation ran for this source slice.
PR #420 remains pinned to its unchanged earlier code-only cohort.
