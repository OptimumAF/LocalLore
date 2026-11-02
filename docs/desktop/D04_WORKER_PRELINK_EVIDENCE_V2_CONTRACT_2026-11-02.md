# Worker prelink evidence v2: source-only binding contract

Refs #25 D04.01/.02/.04 supporting; #31 D09.03 supporting; #21.
Claim6591518066; accepted main027ddbaf (PR373). SOURCE ONLY / UNRUN.
All previous finite grants are SPENT. No new child or build is admitted.

## Purpose and scope

PR346 retained a32-input/v1 all-member dependency observation:71 references,
nine names, two names outside its supplied15-name catalog. PR348 separately
found/pinned UCRT and vcruntime. PR373 now observes BOTH in explicit v2;
their parsed defaultLibraries arrays are empty. These are different historical
captures/profiles, not34 fresh simultaneous files or selected link closure.

The next gap is an explicit evidence policy that can bind those two profiles
without laundering v2 through the v1 projection. Prepare a pure development
JSON-evidence binder, no binary parser, SDK reader, resolver, new graph engine,
compiler launcher or application IPC. Preserve every accepted parser/reader/
projection and original assertion. This evidence NEVER grants a build/run.

Root owns this NEW contract, then NEW
`native/llama-worker/worker_prelink_evidence_v2.mjs`. An independent author
first freezes NEW `worker_prelink_evidence_v2_first.mjs` on a separate serialized
branch BEFORE producer. Reviewers read only; Root integrates and owns shared
checkout/Git mutations. No other implementation path belongs to this slice.

## Private pure API and trust boundary

Export ONLY `createWorkerPrelinkEvidenceV2(anchors)`, returning a frozen object
with ONLY `bind(input)`. No filesystem/environment/process access or top-level
execution; node:crypto only. No parser/reader import or injected callback.

anchors is an exact ordinary/null-prototype enumerable own-data record with
ONLY dependencySnapshot,runtimeSnapshot,catalog,dependencyRoot,runtimeRoot;
values primitive lowercase64hex. Copy at construction; malformed/extra/symbol/
accessor/coerced fields reject `WorkerPrelinkEvidenceV2Setup` without getters.
Actual future driver binds FIXED accepted report/Root/catalog identities;
synthetic tests may supply synthetic anchors. Caller-selected synthetic anchors
are NOT real provenance, a signature, filesystem permission or build authority.

`bind` takes an exact record with the SAME five keys, each a Buffer of original
UTF8 JSON bytes. Snapshot buffers<=24576B each, catalog<=8192B, Roots<=4096B each;
each must be nonempty. Validate type/size then SHA against the copied anchors
BEFORE strict UTF8 decoding/JSON.parse. Reject a UTF8 BOM rather than stripping
it; no replacement decoding or normalization. Never evaluate source or directives.
No canonicalization, trimming, byte patching or accepting a parsed replacement
before digest verification. Reject invalid UTF8/JSON/extras/schema/couplings
with fixed `WorkerPrelinkEvidenceV2Invalid`; bound excess uses
`WorkerPrelinkEvidenceV2Limit`. No raw input/error/path/name excerpts.
Inputs are not mutated or retained by reference. No sticky session/budget or
retry is added: each pure call returns its own detached frozen result or fails.

Raw-byte digests bind original complete accepted envelopes, not only favorable
fields. The future actual driver separately validates their full fixed source/
process/result/Root chains before this binder; this binder is not a general
replacement for historical schema or receipt validators. Minimum structural
checks below prevent passing unrelated hash-pinned JSON as the intended type.

## Required accepted evidence structure

Dependency outer exact12keys in its accepted contract: version,kind,qualified,
linkQualification,closureComplete,captureComplete,status,selfchecks,proofs,
cohort,facts,critical. Version1/kind msvc_dependency_observation_v1, complete
capture/status, critical=null, all qualification flags false. Require old
successful cohort52/projection32/observer15 summaries and matching inner summary.
Inner cohort is the accepted exact17-key report; require version1, correct
kind/profile, complete/not stopped,32 inputs/64 attempts,32 ordered rows, seven
proof couplings and inherited pins/catalog facts. Inner.reader=outer.reader,
inner.supervisor=outer.supervisor, inner.helper=outer.helper,
inner.first=outer.cohortFirst, inner.roster=outer.roster,
inner.descriptor=outer.descriptor, inner.codebook=outer.codebook.
Do not relabel its profile.
Existing historical limits/counters remain bounded; this is not a new parse.

facts has the accepted exact16keys, v1 profile/kind/purpose, complete metadata
capture/status, false qualification flags. pinsSha256/catalogSha256 equal outer
proofs.pins/catalog; supplied catalog's CANONICAL JSON array hash equals that
catalogSha256 (its raw bytes ALSO match anchors). Catalog exactly15 ordered
{slot,name} rows, slots18..32, unique canonical ASCII .lib names<=259B.
Facts names<=32, sorted unique; exactly32 ordered {slot,libraryIds} rows;
IDs dense/strictly increasing/in range and every name referenced at least once.
Each ordered inner profile is the accepted10-element parsed encoding; its
metadata digest at index9 and library count at index4 generate a fresh
canonical array of {slot,metadataSha256,libraryCount} records in that order.
Hash that array's JSON and require equality to facts.pinsSha256/outer.pins.
Every corresponding facts row length must equal profile[4]; never accept an
unrelated graph merely because both supplied envelopes have pinned digests.
providedSlots must EXACTLY match supplied catalog by name (or null);
unresolvedNameIds and allReferencesInProvidedCatalog recompute from that join.
Keep old rows as evidence references, not a newly emitted graph.

Runtime exact13keys/11proofkeys from accepted PR373 report, version2/kind
fixed_two_runtime_metadata_v2/purpose, complete capture/status, critical=null,
false qualification flags. Exactly fixed rows33/ucrt.lib/root3 then
34/vcruntime.lib/root1, both complete, valid primitive pin identities/SHA,
positive sizes within285588/38478 ceilings. Each exact settled reader I/O has
one input, both scans verified, opened+closed, actualReadBytes=2*pin.bytes.
Aggregate I/O sums both, job exact6keys with v2 ID,2 inputs,4 attempts, summed
bytes, not stopped; sections equal parsed sections plus refusal.context.sections
(null means0), within2097152. The accepted parser charges declared sections
BEFORE per-member/input section refusals. A job-overflow failure before charge
stops the job and cannot enter this complete/not-stopped evidence policy.
Retain the actual authoritative snapshot, not invented replacement counters;
the current accepted counter235 equals0+112+55+68. Refusal fields/contexts are accepted bounded
fixed-category/site/numeric data; do not emit raw messages. Parsed summaries
use EXACT three strict/four v2 deviation keys and existing limits/digests/names.
Strict outcomes may be parsed or known refused. Runtime profile outcomes may
be parsed or known refused; no failed/unattempted/partial mode can be supported.

The two Root records must identify their accepted distinct kinds, passed=true,
knownClosed=true, spent/noAutomaticRetry=true, false qualification flags, and
snapshot digest equal the corresponding anchor. Require dependency Root
settled=true and approvedPacketSpent=true, runtime Root grantSpent=true.
Each retains its sourceRevision40hex/process/result64hex. Hash-pinned historical
extra Root fields remain as accepted records; never strip them before hashing.
Do not claim verifying signatures or rerunning their audits.

## Bounded result and honest unavailable outcomes

Result keys/order ONLY version,kind,purpose,qualified,linkQualification,
closureComplete,status,anchors,profiles,counts,knownNames,providedSlots,
unresolvedNameIds,runtimeMetadataAvailable,knownNamesCovered,requiresFreshAdmission.
version2, kind worker_prelink_evidence_v2, purpose build_input_metadata_only;
ALL qualification flags false, requiresFreshAdmission=true in EVERY result.
profiles exactly [{firstSlot:1,lastSlot:32,profileId:v1},
{firstSlot:33,lastSlot:34,profileId:v2}]. No merged parse-job counters.
counts ONLY historicalInputs=32,runtimeInputs=2,historicalReferences=sum of old
row lengths. knownNames is the unchanged old facts libraryNames; output
providedSlots is the OLD15 catalog extended ONLY with validated runtime
presence pins33/34, matching names. No recursive lookup or additional graph.
unresolvedNameIds/knownNamesCovered recompute; no omitted unknown names.

runtimeMetadataAvailable means BOTH profile outcomes parsed, independently of
presence/name coverage. A complete known refusal returns status
metadata_unavailable, that boolean false; it can still cover a name's presence.
If any parsed runtime defaultLibraries is nonempty, status
unsupported_runtime_dependencies: preserve the old knownNames/output unchanged,
and do NOT infer absence/coverage of the additional dependencies. This narrow
policy explicitly needs a later owning decision to extend the graph; never
silently discard those names as supported. Otherwise, when both parsed and
old known names covered, status metadata_available_known_names_covered;
when both parsed but old names unresolved, status known_names_unresolved.
Unavailable takes precedence over unsupported, then unresolved/covered.

Even the favorable status is historical metadata support, NEVER link-ready,
selected closure, ABI safety, new worker identity or Author enablement.
Deep-freeze detached output including anchors; JSON UTF8<=12288B. Resource
excess refuses without truncation. No old result or caller mutation can alter
anchors/output/another call. No raw directives, member names, installed paths,
Root identities or original rows are copied to this result.

## Independent FIRST and future execution

Export `runWorkerPrelinkEvidenceV2Selfchecks(api)` taking ONLY the one-field
factory object. It constructs independent small valid synthetic complete
v1/v2/Root/catalog JSON Buffers and anchors; no producer fixture helper.
Exactly16groups E01..E16, finite summary ONLY version,kind,executed,passed,
failed,failed_case_ids; version1,kind worker_prelink_evidence_v2_first,
16/16/0/[] is the sole passing gate. Each fixture set<128KiB, total synthetic
fixture bytes<2MiB/group; no memory/RSS measurement is claimed.

E01 factory/anchors shape/no getters; E02 exact favorable result/false flags;
E03 byte-SHA-before-JSON/strictUTF8/no rewriting; E04 input/encoded caps;
E05 old outer/cohort/profile/selfcheck/proof coupling;
E06 old facts/catalog SHA/slots/duplicates; E07 dense graph rows/IDs/unusednames;
E08 old provided/unresolved/boolean join; E09 fixed runtime row/pin/I/O bounds;
E10 real v2 job/attempt/section refusal charges;
E11 parsed/refused result/deviation/name/digest schemas;
E12 Root identities/flags/digest bindings;
E13 metadata unavailable versus presence coverage;
E14 nonempty runtime dependencies unsupported/no new graph;
E15 unresolved names retained and status precedence;
E16 deep-copy/freeze/repeated calls/nonmutation/output bounds/privacy.
Keep every subcase. Missing API is UNRUN_SETUP, never a passing RED.

A separate future finite code packet may run unchanged old112/94 plus accepted
alignment18/runtime20 and new16 groups, then bind only existing retained JSON.
It performs NO SDK lookup/read/build/link/model/app/device operation. Exact
programs/hashes/finite capture/full retention reserve and fresh inventory must
be reviewed before requesting execution. No code-check grant exists now.
Current metadata2673057/cap2863104B,190047B free; every other cap/output and
failure fence unchanged. Do not assume another packet fits or reset allowance.

The future B2 compiler/link/MT supervisor still needs its own contract, fresh
source/tool/environment/search/ALL input bytes, candidate-object directives,
closed library resolution, no-shadow checks, outputs, child closure, storage,
independent review and finite owner admission. No metadata success removes
those prerequisites. Six-child reused-dependency artifact comparison remains
UNRUN; no new build/model/app authorization is inferred. AuthorDisabled,
full D04/D09/desktop/human-quality gates open; PR366/protected chat untouched.
