# MSVC dependency facts: pure projection contract

Refs #25 D04.01/.02/.04 supporting, #31 D09.03 supporting, #21.
Root claim6568896942, branch `prep/msvc-dependency-facts-v1` from accepted
a9cf8c61422d5b67a9877c1f1ffa3c4f02adbc31. **SOURCE PREPARATION ONLY.**
PR334's single packet is SPENT. No new check, input read or executable retention
is authorized by this contract. Author remains Disabled.

PR334 observed32 profile parses but intentionally retained only metadata digests
and counts. It did not retain the actual DEFAULTLIB names from previously
refused archives/SDK libraries. Those names cannot be recovered from their
hashes, inferred from counts or treated as absent. The next fact is a bounded
name/edge projection from the SAME accepted helper metadata. Do not create a
second COFF/archive/directive parser, filesystem resolver or linker.

## Pure private development interface

New module `native/llama-worker/library_metadata_dependencies.mjs` exports only
`projectLibraryMetadataDependenciesV1(pins, observations, catalog)`. It imports
only Node crypto and the existing accepted profile descriptor. No top-level
run, files, paths, processes, environment, network, eval, app IPC or authority
token. It consumes data from existing helper results; it never parses binaries
or directives. This is developer metadata, not gameplay state or production
Author capability. Caller-supplied hashes/data do not authenticate provenance;
the separately admitted collector must bind actual source/input/result bytes.

- `pins`: exactly32 plain records in slot1..32 order, each ONLY
  `{slot,metadataSha256,libraryCount}`; lowercase64hex digest and integer0..32
  count. A future collector derives these from the retained PR334 profile rows,
  verifying snapshot611d5c5d first. No arbitrary replacement actual roster.
- `observations`: exactly32 plain records ONLY `{slot,result}`, same slot order.
  `result` has exactly the accepted job's eight keys: profileId,purpose,
  qualified,linkQualification,closureComplete,metadata,sections,deviations.
  Profile is `msvc-library-metadata-v1`, purpose `build_input_metadata_only`,
  qualification/link/closure booleans false. Exact descriptor identity/version/
  limits stay unchanged. This function cannot attest job/I/O counters.
- `metadata`: exactly objects,imports,directives,defaultLibraries. Counts are
  nonnegative safe integers, each≤65536 and objects+imports≤65536. Directives
  and libraries are ordinal-sorted unique string arrays, each≤65536; the new
  projection additionally limits each row to32 libraries and union to32 names.
  Directives are printable ASCII (32..126), each≤65536 UTF-8 bytes. Do not parse
  or reinterpret them. SHA256 of JSON.stringify the entire existing metadata
  object must equal that slot's pin, including original property insertion
  order. Library count must equal the pin. Hashing names alone is insufficient.
- Every library name must already be canonical lowercase, trimmed, not start
  with '.', contain no '..', end '.lib', and match the accepted helper's
  `[a-z0-9_+ -]+(?:\.[a-z0-9_+ -]+)*` grammar. No slash, backslash, colon,
  quotes, control or Unicode. Maximum canonical length259: the unchanged helper
  can append '.lib' to a255-character extensionless input. This projection does
  not increase the helper's255-byte input-name limit or accept a new token.
- `sections`: integer0..262144. `deviations`: ONLY unknownMachineObjects
  (0..65536), unusedRelocationPointers and terminalNulSections (0..262144).
  These counts are metadata; no known-machine/ABI/link inference is allowed.
- Additional projection resource bounds: canonical metadata JSON≤1048576 bytes
  per row and≤8388608 bytes summed across32 rows. Before whole-object stringify,
  walk bounded arrays/strings, count each JSON-escaped string's byte length and
  stop when its running contribution alone exceeds either bound. Then verify
  exact full metadata bytes before hashing. These are NEW projection refusal
  limits, not a relaxation or substitution of the accepted parser/job limits.
- `catalog`: exactly15 plain records ONLY `{slot,name}`, slots18..32 in order,
  distinct canonical library names. A future collector binds them to the saved
  original15 SDK requestedName records. This is a join against a provided
  catalog, not a filesystem search, first-existing-path attestation or complete
  library universe. Self/cyclic references are reported without recursion.

Invalid data or exceeded projection bounds throw only fixed
`LibraryMetadataDependencyFactsInvalid`; no raw value/path/exception payload.
Refusal is not an empty successful graph. No limits/options/callback selector
are supplied by callers. Getter/proxy/hostile in-process JavaScript behavior is
not a security boundary of this JSON-data projection.

## Exact returned value

Return a deeply frozen object with ONLY version,kind,profileId,purpose,qualified,
linkQualification,closureComplete,captureComplete,status,pinsSha256,catalogSha256,
libraryNames,providedSlots,rows,unresolvedNameIds,allReferencesInProvidedCatalog.

Version1, kind`msvc_library_dependency_facts_v1`, accepted profile/purpose,
three qualification flags false, captureComplete=true,
status`metadata_facts_complete`. No `closureComplete=true` even for zero unknowns.
`pinsSha256`/`catalogSha256` hash JSON.stringify the complete provided arrays,
after validation. They are data references, not authenticated owner proofs.

`libraryNames` is the ordinal-sorted unique union (at most32). `providedSlots`
has the same length; each element is matching catalog slot or null. `rows` is
exactly32 records ONLY `{slot,libraryIds}`, original slot order. Each libraryIds
array is sorted unique integer indices into libraryNames, preserving every
row's original library count; never omit unresolved names. `unresolvedNameIds`
is the sorted indices with null providedSlots. `allReferencesInProvidedCatalog`
is exactly whether that array is empty, including an empty-reference graph.
It does not claim all link inputs were selected, found or qualified.

Every encoded row≤128 bytes. Empty rows/libraryNames envelope≤2048 bytes;
JSON.stringify(result)+'\n' independently≤16384 bytes. Canonical names need no
JSON escaping;32 names of259 bytes occupy at most8385 bytes including array
punctuation. Row/residual envelope bounds conservatively total below14600 bytes.
No raw directive tokens or machine paths appear in the result. Return fresh
arrays/objects, deeply frozen; do not mutate inputs or retain mutable aliases.

## Independent FIRST before producer work

New `native/llama-worker/library_metadata_dependency_first.mjs` exports only
`async runLibraryMetadataDependencySelfchecksV1(api)`, no top-level run or I/O.
Its sole callback is `api.projectLibraryMetadataDependenciesV1`; missing callback
throws `UNRUN_SETUP: dependency facts API unavailable`. Fixtures independently
construct metadata and compute their own pin digests with Node crypto. They may
import the accepted descriptor, never the new producer. No SDK/binary input.
All synthetic fixtures together must fit a conservative16MiB string/buffer
budget; the aggregate-refusal case uses at most10MiB synthetic text, not a real
memory/peak benchmark. No filesystem/process/environment/network or source eval.

Freeze32 groups D01..D32, preserving all original assertions after review:

| ID | Required case / control |
| --- | --- |
| D01 |32 valid empty-reference metadata records; exact successful shape/false flags |
| D02 | Known catalog reference maps to its original SDK slot |
| D03 | Unknown reference retained and unresolved; no closure claim |
| D04 | Shared names deduplicate globally, sort and retain each row edge |
| D05 | Self/cyclic provided references never recurse or claim link closure |
| D06 | Observation slot order/duplicate slot refuses |
| D07 | Wrong whole-metadata digest refuses, including directives-only mutation |
| D08 | Wrong pinned library count refuses |
| D09 | Observation count31/33 refuses |
| D10 | Unknown observation field refuses |
| D11 | Strict/unknown profile or wrong purpose refuses |
| D12 | Any true or nonboolean qualification/link/closure refuses |
| D13 | Unknown/missing result field refuses |
| D14 | Unknown/missing metadata field refuses |
| D15 | Unsorted directives refuse |
| D16 | Duplicate directives refuse |
| D17 | Non-ASCII/control directive refuses |
| D18 |65537-byte directive refuses |
| D19 | More than1MiB metadata row refuses before whole-row hashing |
| D20 | More than8MiB aggregate metadata refuses;≤10MiB synthetic text |
| D21 | Unsorted/duplicate libraries refuse |
| D22 | Path-bearing/traversal/quoted/colon/control library refuses |
| D23 | Uppercase/untrimmed/extensionless canonical library refuses |
| D24 |259-character helper-canonical name accepted;260 refuses |
| D25 |33 distinct names globally or33 per-row refuses |
| D26 | Catalog count/order/duplicate name/unknown key refuses |
| D27 | Unsafe/noninteger/negative/over-limit count,section,deviation refuses |
| D28 | Pin count/order/shape/digest/count types refuse |
| D29 | Inputs unchanged; fresh deeply frozen output and no mutable alias |
| D30 | Sorted ID alignment/known slots/unknown IDs match full deterministic projection |
| D31 | Exact output keys/hashes/counts/status and no directive/path output |
| D32 |32 maximum-length names/rows fit all byte limits and retain all edges |

Return ONLY version,kind,executed,passed,failed,failed_case_ids; version1,
kind`library_metadata_dependency_first_v1`,32 groups, IDs only on failure.
Source review is not an executed result. Do not weaken a test to match a
producer; findings require explicit preserved amendment and reviewed fix.

## Execution boundary and next work

The independent FIRST source must be frozen in its author branch/commit before
the producer is written. Root owns integration and documentation, one writer
per file and exclusive checkout handoffs. A separately reviewed bounded code
check can import the pure producer and invoke FIRST on synthetic data; this
contract authorizes neither that child nor a later real-input collector.

Current charged metadata1773064B of1867776B leaves94712B, including PR334's
7071B new decoded-log charge. Future inventories must include it. Preserve all
other caps, sources, failures and outputs. Exact runner/source/Stage/owner/full
reserve sizes and reviews must precede any new decision; no cap increase is
inferred. The source-only Git files are not new run evidence.

After pure code verification, prepare a separately admitted same32 observation
that verifies every new full metadata digest against PR334 before projection.
That collector must retain existing source/proof/owner/START/closure/deadline/
stream/I/O/storage controls, and original strict evidence. No new library lookup,
replacement input, section budget increase, compiler/link/build/app/model/device
run, download/settings/deletion/release or desktop control belongs to this slice.
Actual missing-name resolution, selected-link behavior and runtime qualification
remain later owning work; a complete metadata graph cannot enable Author.
