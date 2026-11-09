# D04 held Windows compiler input catalog v1

Refs #25 (D04.01/.02/.04), #31 (D09.03/.05) and #21.
The private native parent holds the exact admitted positive compiler
inputs while the fixed Node/CL attempt runs. The Node check port binds
its independently observed input list to that actual native admission.
This adds no public launcher or model capability.

## One catalog, two observations

The sealed bootstrap computes
`workerArtifactCompileInputCatalogV1(manifest, targetRoot)` from the
same exact ordered check manifest used at runtime. Its SHA-256 is
`inputCatalog` in the sealed Node profile and `input_catalog` in the
native Plan. The Plan has the target path, independent topology digest,
ordered positive compile inputs and ordered named absence paths. Each
positive native row carries the role and existing path, bytes and
SHA-256 pin. The native parent recomputes the catalog and refuses a
different value before opening inputs. The Node guard recomputes it
and compares it with the verified profile and parent READY before
performing its own reads.

Hash the following exact UTF-8 records. Tabs delimit fields, LF ends
each line, sizes are unsigned decimal, and no path or line is folded
or reordered. SHA-256 fields use lowercase hexadecimal. The first
line binds the already independent topology record. Target is the
canonical D: target root. Preserve the ordered positive and absence
vectors from the reviewed manifest.

```text
compile-input-catalog-v1<TAB>topology<LF>
target<TAB>path<LF>
file<TAB>role<TAB>path<TAB>bytes<TAB>sha256<LF>
absent<TAB>path<LF>
```

The file and absent lines repeat for the respective vectors. The
catalog describes exact bytes and paths. Node and Windows file IDs
remain separate. Both sides reject ambiguous paths, duplicate paths
and library or model payloads. The external topology record must be
acyclic and cannot include the catalog or final profile hash as an
input to itself.

## Native custody

Use the existing parent Lease. Establish each needed C: and D: root
as a fixed mounted volume and bind its volume identity. Project
source, normal worker, Node, helper, entry, target, temp and evidence
remain on D:. The only C: positive paths are admitted headers and
tool files. No C: path is opened for writing. The lease holds up to
256 distinct ancestor directories and up to 1,028 file handles,
including the three earlier entry pins and eventual READY handle.

At most 1,024 positive compile pins and 2,048 absent slots are
accepted. Positive input payloads total at most 512 MiB including
one EOF probe per file. These are design maxima. The three earlier
Node, helper and entry pins still have their separate bounds. A future
run must independently authorize its exact counts, paths, cumulative
reads and complete time and output reserves. This source does not
authorize any SDK or tool observation.

Open ordinary ancestor directories without delete sharing. Open every
positive leaf for read with FILE_SHARE_READ only. Reject reparse
objects and hard links, check canonical handle path and corresponding
volume, hash the exact held bytes and verify EOF, identity and metadata.
Hold those actual handles through the native attempt. This denies
ordinary write/delete opens on the selected objects. Windows loader
and compiler compatibility with the held sharing policy still require
an admitted test.

Hold the target and each absence slot's ordinary ancestor chain.
Require absence at preflight, while suspended around READY, and in
postflight. A held directory can still allow an unrelated process to
insert a new name. These are checkpoints. A continuous sealed-directory
and complete ordered include/loader resolution proof must still be
established independently. Do not infer outside-writer exclusion or
absence throughout CL from before/after snapshots.

## READY and outcome

Immediately after namespace, add inputCatalog, inputSeal, inputFiles
and absenceSlots to the compact READY field order. InputSeal hashes
the exact catalog, target directory identity, ordered actual positive
native file IDs and ordered absence-parent native IDs. It describes
native custody at admission. Node checks the catalog and count bindings
against the actual sealed manifest. It keeps the independent topology,
Node identity and live file checks from the earlier guard. The native
record remains trusted only within the admitted namespace.

The parent rechecks held identities and absence after the child.
A failure refuses qualification even if a child emitted an otherwise
positive report. Known handle closure remains separate from process,
Job and pipe closure. If closure is unknown, keep the existing
parent quarantine and preserve all partial outputs. Never reuse that
lease or offer a second run.

The updated readiness FIRST has fourteen in-memory groups, including
the exact UTF-8 catalog vector and native READY seal/count refusals.
They remain unrun. The separately pending PR #420 packet remains
pinned to the older 37-group cohort. No Node, SDK, fixture, native
build, compiler, app, model or device ran in this source slice.
The concrete sealed bootstrap, complete independently admitted
loader/no-shadow inputs, independent outside-writer exclusion, and
synthetic Windows/native execution remain open.
