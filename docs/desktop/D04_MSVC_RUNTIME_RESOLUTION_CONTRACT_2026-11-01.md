# Fixed-two runtime-library resolution and metadata: preparation contract

Refs #25 D04.01/.02/.04 supporting, #31 D09.03 supporting, #21.
Root claim6570570273, branch `prep/msvc-runtime-resolution-v1` from accepted
main6651877a1d0b81e0982db4c6d673989e5e0e3d0b, existing physical D: checkout
`source-desktop-fork-review`. **SOURCE PREPARATION ONLY.** PR346's ONE packet
and +176KiB decision are SPENT. No new lookup, SDK input read, code-check child,
source retention in the bounded evidence packet, build or runtime is admitted.

## Observation and complete next slice

[PR346 verification](D04_MSVC_DEPENDENCY_OBSERVATION_VERIFICATION_2026-11-01.md)
records99 passing gates and a complete metadata observation of the SAME32
inputs. Its nine-name graph has71 references. IDs4/7 are `ucrt.lib` and
`vcruntime.lib`, both requested by existing global slot29. They are outside
the provided15-entry SDK catalog, **not known absent from the machine**.

Prepare ONE supervised child that first passes independent synthetic checks,
then both resolves these names AND inspects any found inputs. A lookup-only
result cannot replace the metadata goal. Reuse the accepted helper unchanged:
16987B, SHA256
`9972c0eb4d8cf936f252b090a8f0794b0d6b5328a2245b8720cdec32d5fafa53`.
No additional binary, archive, COFF or directive parser, linker simulation,
default-library suppression, member selection or worker adoption is introduced.

Only the following two request slots belong to this slice:

| Request index | Global request slot | Name | Prior name ID | Requested by |
| --- | --- | --- | --- | --- |
|0 |33 |ucrt.lib |4 |29 |
|1 |34 |vcruntime.lib |7 |29 |

Slots33/34 identify requests even when a file is not found. Do not report34
observed files unless both requests actually produce validated observations.
Original32 inputs/64 attempts remain a separate completed job. This new job
contains at most2 inputs/4 attempts, explicitly preserving both jobs' provenance;
it neither resets the old job nor changes its32-input limit.

## Frozen evidence and search recipe

Bind and validate retained original roster62eb0ab9, diagnosticc7bce3ce,
profile-cohort snapshot611d5c5d, and complete dependency-observation snapshot
`47b15b415307185f21eb0c06842c26cfc9021f8cb2454830b474b32a203e5391`.
Bind their settled source/Stage/process/result/Root-review proofs too; a bare
filename or partial summary is insufficient. Preserve original32 pins, all19
strict refusals,71 graph edges, the nine names and false qualification flags.
No old payload needs another read for this slice. Retained JSON is provenance,
not a claim that all old binaries are simultaneously unchanged now.

Use EXACTLY the original five roots and their recorded identities, in order:

1. MSVC14.34.31933 ATL/MFC x64.
2. MSVC14.34.31933 x64.
3. NETFXSDK4.7.1 UM x64.
4. Windows SDK10.0.19041.0 UCRT x64.
5. Windows SDK10.0.19041.0 UM x64.

The original roster owns their exact absolute installed paths and signatures.
Do not discover a newer SDK, read LIB/LIBPATH, scan other roots or substitute
another filename. Existing installed C: tool inputs stay installed data;
all project source, temporary work and evidence remain physically D:.

Preserve the recorded effective LINK current directory:
`source-resource-metrics-review/native/llama-worker`. Before probing and again
after acquisition, require ordinary canonical roots with the original identities
and reject ANY `.lib` entry in that current directory, case-insensitively.
The complete directory check is intentional: checking just the two new names
would weaken the original current-directory-before-LIB rule. Reject nonordinary
entries/identity changes or an exceeded explicit directory-entry bound, rather
than silently skipping them. This is a cooperative check, not a filesystem lock.

For each name, probe roots0..4 in order. Only an actual ENOENT means continue;
permission errors, reparse points, directories, identity failures and other I/O
errors stop. Select the FIRST existing entry and validate it; an unusable first
entry cannot be skipped in favor of a later root. Do not probe later roots after
selection. At most10 candidate probes, plus disclosed root/cwd guard observations.
All-five-ENOENT means only `not_found_in_fixed_roots`. Record that outcome
honestly, without searching elsewhere or calling it machine absence.

No recursive lookup of DEFAULTLIB names found in the new metadata. Report them
as names and match only against the explicitly supplied old15 plus actually
found new inputs. Unmatched names remain visible for a later owning decision.
An all-member name match is never selected-link, ABI or runtime qualification.

## Newly observed file identities and one bounded job

New payload sizes/digests are unknown BEFORE a separately admitted lookup.
Do not describe a source-pinned path/name as a pre-pinned payload hash. Observe
the first existing entry's canonical path, ordinary leaf/root identities and
exact size, then reserve one input and TWO full scans before allocation/open.
Refuse zero or exclusive256MiB-or-larger files and prospective total input/read
overruns. Keep accepted512MiB job-input/1GiB selected-read/2097152 job-section
ceilings; the additional caller limit is2 inputs, not a relaxed parser limit.
Both strict/profile attempts charge through ONE accepted job, never replaced.

Reuse PR334/346's corrected held-input protocol: one read-only handle; lstat to
held-stat agreement; at most65536B chunks with positive short-read support;
private pending/poison latches; actual returned bytes charged before post-await
stop checks; unchanged canonical path/root/leaf/size checks after each scan;
first-failure-preserving close in finally. No refund/reset/automatic retry.
The first scan fills one Buffer and establishes a NEW observed SHA256; the
second independently hashes the SAME held handle and must match it. No third
payload scan or reopen is needed. Final opened-identity-only rechecks and an
in-memory hash after inspection remain required. Do not copy the obsolete
closure collector's stable() implementation, which reopens and has weaker
read-size/close handling than the accepted later protocol.

On each found Buffer attempt `strict-v1`, then `msvc-library-metadata-v1`.
Unlike the old32 rows, these two files have no pre-established strict verdict.
Record a known strict refusal without inventing a baseline; continue to profile
ONLY while the same job is live. Record known profile refusals as unavailable
metadata; never turn them into a successful parse or use partial results for a
dependency graph. Unknown exceptions/job stop/input/source/identity failure are
sticky critical failures. Preserve actual attempt/section/read counters and
partial outcomes. A close failure must not overwrite the first failure.

Output no payload/member contents or raw directives. For each successful mode,
retain the existing compact counts/sections/deviation/full-metadata digest.
For successful profile additionally retain its sorted canonical DEFAULTLIB
names, under an explicit bounded name/report limit. A refusal retains accepted
fixed code/site/numeric context, not an OS error payload or arbitrary exception.
No inspection is permission to execute an input or a directive string.

## Independent FIRST, envelope and admission gate

Freeze a small private callback interface and closed complete/stopped report
schema BEFORE producer work. Independent FIRST uses synthetic Buffers, retained
JSON fixtures and fake adapters only; it has no production adapter/state,
SDK/filesystem/environment/process access, source evaluation or network.
Retain its original assertions/IDs and source revisions. All required suites
must pass in the proposed sole child BEFORE constructing the real adapter or
performing root/cwd/candidate observations. Parsing/import/startup/gate failure
cannot trigger a fallback read or a second child.

Required cases cover exact names/order/root precedence, missing outcomes,
current-directory shadow and root drift, non-ENOENT/unsafe first entries, no
later-root/recursive follow, no calls before ready/after poison, overlapping
operations, newly observed SHA versus second-scan mismatch, short/zero/overlong
reads, bytes charged on late stop, reservation limits, held/root/leaf drift,
single close and first-cause retention, same-Buffer mode order, live known
refusal versus sticky job/unknown failure, post-inspection mutation, exact
report schemas/counters/provenance, unavailable cases and all false flags.

The eventual complete envelope must bind all prior evidence, new sources,
owner/Stage and successful independent selfchecks; both ordered request rows;
root/cwd/probe outcomes; new payload provenance where found; actual separate
job and I/O counters; bounded names and catalog matches; and explicit unavailable
or critical outcomes. Keep qualified/linkQualification/closureComplete=false
in EVERY branch. Distinguish complete capture from both-profile success and
from complete dependency resolution. Missing/known-refused inputs remain
unavailable; a failed partial report must never masquerade as a complete capture.
Do not omit rows/names or accept an aggregate summary to make a report fit.

ONE fixed PowerShell supervisor/ONE fixed Node24.22.1 child; no arbitrary path,
command, code, shell or remote-debug interface. Reuse established source/owner/
Stage/START, concurrent bounded stream, observed deadline/closure, global-stop,
full-retention and prior-START fences. Preserve all seven Node override refusals
and normal unlaunched image identity. Source/tool/normal-image guard hashing
must be disclosed separately from selected payload scans, without a claim that
the1GiB selected-read ceiling covers every filesystem read.

Exact private interfaces, report/stream bounds, complete source text and hashes,
independent reviews, full-envelope worst cases and concrete full retention
forecast are required before any owner execution decision. This document is
not an unbounded schema license, a syntax pass or an input observation.

## Current storage and next runnable action

Last verified charged metadata1965643/2048000B leaves82357B. Carry cumulative
decoded allowance28498B forward. Physical group54149035B/joint736470529B;
conservative new-log charge17673B gives54166708B/736488202B. Target12356228504B
and runtime210B unchanged. These are PR346's final records, not a fresh admission.

Retain all prior output. Keep64MiB group,724MiB joint, original-baseline4GiB
target growth,576KiB old check records and8MiB fixtures. No cap increase,
deletion, compression, second evidence root or relabeling is authorized. Exact
new retained sources/owner/Stage/prep records plus complete physical/base64/
decoded/snapshot/process/START/result/review/STOP reserves must fit a separately
approved allowance and fresh actual inventory before execution.

Next runnable work is independent interface/FIRST and source preparation for
the COMPLETE fixed-two resolution+metadata packet. No SDK lookup/read or child
is currently runnable. No build/link, C++ worker, model/app/native UI/device/OS
work, download, settings/release or desktop control belongs to this preparation.
Author staysDisabled; full D04/D09/desktop and human narrative-quality gates
remain open. The protected chat and all concurrent ownership stay untouched.

## Private interface frozen before producer work

Independent FIRST receives ONLY the following private callback references,
the fixed accepted codebook and JSON proof constants. It never receives a
production adapter. These are development collector seams, not app IPC or a
public configurable resolver API. Plain records/dense arrays and primitive
typed fields are required; reject extras, sparse arrays and boxed primitives.

`resolveFixedLibraryV1(index,state,adapter)` asynchronously returns a frozen
candidate or null. Index is ONLY0/1 in order; names are closed literals, never
arguments. State has ONLY ready,stopped,pending,nextIndex,searchContext,probes,
resolved,reservedInputs,reservedBytes,reservedReadBytes,actualReadBytes,opened.
Fresh fields are false,false,false,0,null,[],[],0,0,0,0,[]. FIRST may construct
fresh synthetic ready states. The actual driver sets ready only after all
required selfchecks pass; no real adapter exists before that barrier.

Private WeakMap/WeakSet latches retain next index, pending, poison and minted
candidates. Public field resets cannot recover a stopped operation. Wrong
index, overlap, malformed state or unconsumed earlier found candidate refuses
BEFORE any adapter call. A prior not-found request needs no read. A found
candidate must complete acquisition AND its same-job strict/profile pair before
the next request resolves. The read-produced Buffer is privately associated
with its state/candidate; a pair only marks it consumed after its in-memory
hash remains equal to the newly observed pin. A live known profile refusal can
consume it, with metadata unavailable. Skipping acquisition or inspection
cannot yield a complete lookup-only run.

The adapter's `guardSearch()` returns ONLY cwdIdentity,cwdLibraryCount,
rootIdentities. Require cwdLibraryCount=0, cwdIdentity a nonempty string≤256B,
and exactly5 nonempty identity strings≤256B in original order. Production also
checks those roots against the original roster's exact pins, ordinary canonical
paths and the whole cwd's≤4096 entries. It refuses any case-insensitive `.lib`
entry or nonordinary entry. Resolver calls and compares this context before
and after each request; the driver repeats it after final identity-only checks.
Every opaque identity string uses ONLY ASCII letters/digits/underscore/dot/
colon/hyphen,1..256 characters. Production numeric stat signatures satisfy
this rule; arbitrary control/Unicode/escaped strings do not. This also makes
their serialized size bounded without a JSON-escaping multiplier.

`adapter.probe(index,rootIndex)` takes ONLY the two closed integer indexes. It
returns null ONLY for leaf ENOENT; otherwise it returns ONLY index,rootIndex,
bytes,rootIdentity,leafIdentity. Require exact indexes, a nonnegative safe size,
the corresponding guarded root identity and nonempty leaf identity≤256B.
Production derives the path from fixed roots/name and checks ordinary canonical
file/root identity. No caller supplies a path. Record at most10 ordered probe
outcomes in state.probes, each ONLY index,rootIndex,outcome; outcome is
missing/selected/failed. Append a failed placeholder BEFORE awaiting a probe;
commit a valid returned outcome BEFORE checking a late stop, so a known result
is not lost. Failed includes a thrown/malformed probe and stops, never a
later-root fallback. No probe precedes the first successful search guard.
state.resolved is the ordered completed-resolution prefix, candidates or null;
nextIndex advances once per started request, with no retry after failure.
The production adapter owns ENOENT-to-null conversion; ANY exception from the
closed probe callback, even one bearing code ENOENT, is a failed probe.
An incomplete request may have candidate=null and a terminal selected probe:
the known result was committed but its post guard/late-live check failed.

`readDiscoveredLibraryV1(candidate,state,adapter)` returns ONLY buffer,pin.
Require the exact frozen candidate minted by this state's resolver, once.
Reserve1 of2 inputs and2*bytes before identify/open. Reject bytes=0 or
bytes≥268435456 and all prospective total overruns. `adapter.identify(candidate)`
returns the same closed five-field identity; `adapter.open(candidate,'r')`
returns a read-only handle with stat/read/close. stat returns ONLY
leafIdentity,bytes; read takes Buffer,offset,length,position and returns ONLY
bytesRead. Only close may run after poisoning. The established two-scan/pending/
charge/first-failure protocol above applies. Both scan hashes and the final
in-memory Buffer hash must match the NEW observed hash.

The frozen returned pin has ONLY slot,name,rootIndex,bytes,sha256,rootIdentity,
leafIdentity. Slot33/34 and name come from the request index. The immutable
roster root plus name reconstructs its exact canonical path; do not expose a
new arbitrary-path seam or duplicate machine paths in reports. Add the validated
pin and identity to state.opened only after successful acquisition/close.
No pin is invented for a missing, oversized, failed or unread candidate.

`inspectDiscoveredPairV1(job,buffer,slot)` returns ONLY row,profileResult,
stopped,critical. row has ONLY slot,strict,profile using the unchanged accepted
compact mode arrays/codebook. Slots33/34 strictly increase; first34 is allowed
when33 was not found. Private seen-Buffer/slot and sticky-failure state prevent
repeats. One actual job performs strict then profile on that SAME Buffer;
profileResult is the actual accepted eight-key profile result or null, never
reconstructed from counts. Known ordinary refusals retain their arrays; a live
known profile refusal may finish the pair with profileResult=null. Unknown
result/error/snapshot, repeated slot/Buffer or stopped job refuses critically.
Hash the Buffer after the pair and before retaining names or its success.

`encodeFixedTwoReportV1(report)` performs no I/O and returns validated canonical
strict UTF-8 JSON+LF, at most24576B. Freeze its concrete closed schema and
independent complete/stopped fixtures before its producer. The exact new FIRST
case count, summary kind and complete source/report bounds must be pinned
before the production driver can use them. No source evaluation/import of
the proposed collector is permitted during source preparation.

## Name presence and graph knowledge

Callback refusal messages are fixed, with a private first-cause latch per state.
Resolver/read failures THROW Error(fixedCode). Pair failures RETURN their actual
partial row, profileResult=null, stopped=true and fixed critical; success has
stopped=false,critical=null. Encoder failures THROW Error(ReportFailure) or
Error(ReportLimit). No callback returns a success after an earlier failure.
Bad readiness/state/overlap is InputFailure; wrong index/order, forged/replayed
candidate, skipped pair, repeated Buffer/slot or replacement job is RequestOrder.
Malformed search context/cwd shadow/probe schema or generic search I/O is
SearchFailure; changed context/root/leaf/held identity or scan digest is
IdentityFailure. Admission size/count/read overruns are InputLimit. Generic
acquisition/close errors are InputFailure. Pair unknown result/error/snapshot
is UnknownInspection, a valid stopped job is JobStopped and post-pair Buffer
change is BufferMutation. Encoder invalid data is ReportFailure; explicit
name/union/serialization resource excess is ReportLimit. Preserve any earlier
latched cause on concurrent return or close; never expose an OS exception text.
First-state failure is sticky even if public flags/counters are reset.

A validated two-scan pin may enter the extended presence catalog even if its
profile inspection has a known refusal. This is a name-to-observed-file join,
not evidence that the file's own dependency metadata is available. Never
equate these facts. A selected candidate with no successful pin cannot enter
that catalog. Old15 catalog entries retain their historical evidence dates;
this slice does not re-attest their live payloads or simulate a current link.

The new compact graph contains the exact sorted union of the prior nine names
and all successful new profile DEFAULTLIB names; at most32 names total,
at most32 per successful new row, canonical ASCII names≤259B. Use integer name
IDs, corresponding providedSlots (old18..32, validated new33/34 or null),
the nine priorNameIds in old order and exactly2 new graph rows. Each new row
has slot33/34 and libraryIds; IDs are strictly increasing and equal its parsed
profile's library count. libraryIds=null for not-found/known-profile-refused
requests; an empty array is only an observed successful empty library list.
All names in the union must be referenced by priorNameIds or a successful new
row; no padding or sparse/unused entries. Unmatched names are retained without
lookup. If any name/union/report bound is exceeded, retain a failed packet
with a fixed ReportLimit cause; never truncate or substitute a subset.

Report separate booleans for bothProfileMetadataAvailable and
allKnownNamesProvided. The former requires BOTH requests found, fully acquired
and profile-parsed; the latter compares ONLY known names to the explicit
presence catalog. It can be true while metadata is unavailable. Neither can
set qualified/linkQualification/closureComplete. Immutable prior graph hash
preserves all32 old rows/71 edges without copying or re-observing them; the
new graph must not be represented as34 freshly inspected rows.

## Closed report and finite FIRST roster

The independent suite exports `runFixedTwoRuntimeSelfchecksV1(api)`. api has
ONLY resolveFixedLibraryV1,readDiscoveredLibraryV1,inspectDiscoveredPairV1,
encodeFixedTwoReportV1,codebook,proofs. The four callbacks are functions;
codebook is the accepted fixed kinds/sites/contexts/helper/descriptor mapping;
proofs is the15-key dictionary below. No producer fixture factory is provided
to construct expected outcomes. The suite authors its expected report data.

Exactly24 groups, IDsR01..R08,I01..I08,P01..P04,S01..S04, are all required.
Summary has ONLY version,kind,executed,passed,failed,failed_case_ids; version1,
kind`fixed_two_runtime_first_v1`, executed24, passed24, failed0, empty IDs is
the sole successful gate. A failed suite runs its finite groups and returns
the corresponding failed IDs; it never admits real observations. These are
source-only proposed groups, not recorded execution results.

R01: gate/wrong index/no calls. R02: exact priority/first wins. R03: all-five
misses/no open. R04: non-ENOENT/unsafe first existing/no fallback. R05: whole
cwd .lib/.LIB shadow. R06: search-context schema/root/cwd drift, including
post-missing guard. R07: reentry/public-reset poisoning and known late probe
outcome retention. R08: consume-found before next resolution/third request.
I01: newly observed first SHA/matching second scan. I02: positive short reads,
65536B chunk ceiling and independent scratch scan. I03: second-hash mismatch.
I04: selected/root/leaf/held/size identity drift. I05: zero/overread/throw and
known positive bytes charged before late stop. I06: one close, close-only
failure and first-cause retention. I07: coupled input/count/read reservations
using tiny fixtures. I08: forged/replayed/foreign candidates and distinct
charges for equal bytes. P01: actual accepted strict/profile results. P02:
ordinary strict/profile refusal. P03: stopped job/unknown result or error,
no later mode/request. P04: repeated Buffer/slot/job replacement refused.
S01: complete inherited/new provenance and false flags. S02: missing,
incomplete and selected-unread partials without fake pins. S03: malformed
trace/context/counters/digests/dense arrays. S04: exact union/catalog/name IDs,
unavailable metadata, no lookup and overlimit refusal. Keep all subcases.
R05's fake guard verifies shadow counts/refusals at this adapter seam, not
actual filesystem enumeration. Production≤4096/case-insensitive .LIB policy
is additionally source-reviewed; do not describe these fakes as real SDK I/O.

Report has ONLY these keys, in this canonical insertion order:
version,kind,purpose,qualified,linkQualification,closureComplete,captureComplete,
status,selfchecks,proofs,search,job,io,requests,facts,critical. version1,
kind`fixed_two_runtime_metadata_v1`, purpose`build_input_metadata_only`;
three qualification flags false. status=complete iff captureComplete=true
and critical=null; otherwise status=stopped and captureComplete=false.
selfchecks is the exact successful24-group summary, never just an aggregate.

proofs has ONLY reader,supervisor,helper,first,roster,diagnostic,cohortSnapshot,
dependencySnapshot,dependencyProcess,dependencyResult,dependencyReview,
descriptor,codebook,priorPins,priorCatalog, each a lowercase64hex digest.
Bind original roster62eb0ab9, diagnosticc7bce3ce, cohort611d5c5d and
dependency snapshot47b15b41/process23c7b426/result143f6242/reviewee56cfb0;
prior pinsfa5a21e1/catalogc28391bc. Use their FULL recorded hashes, not
abbreviated prefix comparisons. Supervisor independently checks actual
source/owner/Stage/proof identities and every output coupling. The report
does not embed another full old snapshot or a self-referential report hash.
Its source-digest references are required and independently parent-verified;
child-supplied digest strings are not self-authentication.

search has ONLY context,probes,finalVerified. context=null before the first
successful guard, otherwise the first three-key guardSearch result, unchanged.
probes is the at-most10 dense completed/failed trace described above. Within
each index roots begin0, increase by1, and stop at selected/failed or five
misses; index1 never precedes a terminal index0 result. finalVerified is a
boolean set true ONLY after all final opened-identity and root/cwd checks.

job is the exact six-key accepted snapshot, profileId,inputCount,inputBytes,
attempts,sections,stopped. Keep accepted bounds, plus inputCount≤2, attempts≤4.
io has ONLY reservedInputs,reservedBytes,reservedReadBytes,actualReadBytes;
reservedInputs≤2, reservedBytes≤536870912, reservedReadBytes=2*reservedBytes
≤1073741824, actualReadBytes≤reservedReadBytes. There is no read refund.

requests is ALWAYS exactly2 ordered rows. Each has ONLY slot,name,priorNameId,
requestedBySlot,outcome,candidate,pin,strict,profile. Fixed identities are the
table above. outcome is not_reached/incomplete/missing/selected. not_reached
means this resolver request was never entered; incomplete means entered but
did not yield a validated resolution (including a pre-probe guard refusal).
missing means five valid ENOENT outcomes plus its successful post guard;
selected means a valid first candidate plus its successful post guard.
candidate is null except selected; then the exact five-field minted identity.
pin is null until two scans AND close succeed; then the exact seven-field
observed pin, coupled to candidate, request and root context. strict/profile
are null until their attempts yield known encoded outcomes. Use the unchanged
10-item parsed or11-item refusal arrays, fixed codes/sites and eight numeric
contexts (safe nonnegative integers or null). Successful mode digest hashes
the WHOLE accepted metadata; all strict deviations remain zero. A non-null
profile requires a prior non-null strict outcome. Never invent a pin/mode
for not_reached/incomplete/missing. At most one request can be incomplete;
later requests are not_reached. Selected rows may have pin/modes null on a
critical acquisition/inspection failure; later rows remain not_reached.

facts is null in EVERY stopped report. In a complete capture it has ONLY
libraryNames,providedSlots,priorNameIds,rows,bothProfileMetadataAvailable,
allKnownNamesProvided. Arrays/name limits and exact-union rules are above;
rows has exactly `{slot:33,libraryIds}` and `{slot:34,libraryIds}`. A successful
profile's parsed library count equals its IDs length; null means no successful
profile. providedSlots is derived from the old15 catalog plus only successful
new observed pins, not selected unread candidates. The booleans are computed
from the rows/pins and complete known union; they confer no qualification.

Complete requires both requests missing/selected, all final guards true, a live
job, and EACH selected file acquired with both known mode outcomes. Number of
pins=selected count=job.inputCount=io.reservedInputs; inputBytes and reservedBytes
equal the sum of their exact sizes; attempts=2*inputCount and actualReadBytes
=reservedReadBytes=2*inputBytes. Both missing is valid0/0/0; missing33/found34
is valid1/2 with slot34 first. Known profile refusal is complete observation
with unavailable metadata, never a parsed result.

Stopped must retain the actual ordered prefix and first fixed critical cause:
SearchFailure,IdentityFailure,InputFailure,InputLimit,RequestOrder,
UnknownInspection,JobStopped,BufferMutation,SourceFailure,ReportLimit,
ReportFailure. Let j=job inputs,p=successful pins,r=admitted read reservations.
Require j≤p≤r≤j+1 with all three≤2. The consume-found rule forbids having BOTH
an acquired-unpaired pin and a second reserved-unpinned acquisition. reservedBytes
equals the ordered selected sizes of the first r admitted reservations,
including any one failed/unpinned acquisition. Actual reads
are at least twice completed pins' sizes but no more than reservedReadBytes.
Job inputCount≤pin count; inputBytes equals its acquired prefix's sizes;
inputCount≤attempts≤2*inputCount, and encoded known outcomes≤attempts.
Zero attempts REQUIRES inputCount/inputBytes/sections=0 and a live job.
JobStopped REQUIRES job.stopped=true and the last attempted mode to be a known
encoded refusal; attempts equals the encoded-outcome count. Every other
coherent critical report REQUIRES job.stopped=false. UnknownInspection permits
exactly ONE terminal unencoded attempt (strict or profile) after the exact
known-outcome prefix; attempts=encoded outcomes+1, with no later attempt.
A missing/invalid snapshot, or an unknown failure while merely obtaining a
snapshot after a known mode, cannot use this coherent-report exception: retain
bounded raw failure instead. All other critical causes require attempts equal
the encoded-outcome count. SearchFailure/IdentityFailure/InputFailure/
InputLimit/SourceFailure/ReportLimit/ReportFailure occur outside a pair and
require BOTH known modes for every represented job entry, attempts=2*inputCount;
there may be at most one acquired-but-unpaired pin. BufferMutation requires
the just-completed known pair and no earlier pair failure relabeled.
RequestOrder also permits one terminal known strict-only prefix if an internal
reentry poisoned that pair; it never permits a profile without strict or any
later attempt. If no attempts, or if NO terminal unencoded attempt exists and
EVERY attempted mode parsed, sections equals the sum of encoded successful-mode
sections; with known
refusals or an unknown terminal attempt it is at least that sum, never above
the accepted job ceiling. These constraints do not infer unobserved sections.
No later acquired/attempted row may follow a failed prefix. Preserve a valid
stopped job snapshot; do not reset sections or replace an unknown snapshot.
If even a coherent stopped envelope cannot be validated, retain bounded raw
failure/startup evidence instead of manufacturing a successful report.

These are schema/resource limits, not a demonstrated whole-envelope bound.
Before admission prove both complete/stopped envelopes, raw/base64/decoded
record costs and actual source retention against all caps, including a STOP
reserve. The proposed24576B report ceiling cannot justify dropping fields or
padding test inputs. Independent parent validation must not trust the child's
captureComplete, source proof values, counters or name joins on their own.
Additionally bound the canonical outer JSON+LF with facts=null to12288B,
and the standalone facts JSON+LF to12288B. Validate each and the WHOLE24576B
envelope explicitly. These conservative parts include replaced null/newline
overcounts; they introduce no arbitrary padding fields. Actual worst-case
construction/measurement and independent review remain admission prerequisites.

## Pre-producer FIRST freeze and source-review clarifications

Independent FIRST is now frozen as SOURCE ONLY/UNRUN,41187B, SHA256
`c35df1fe95685e92caffddff7aaef57d8b595ed39069e4493e6f51994c39830d`.
The original author's exact draft and the separate review amendments remain
preserved locally before any producer. Only the final sanitized file snapshot
is integrated for publication; private draft ancestry is not pushed. All24
group IDs and original assertions remain, with review cases appended.
No behavioral RED, passing suite or SDK observation is claimed.

FIRST uses synthetic opaque root-0..root-4 identities. The private encoder
tests structural/context/candidate coupling with these tokens; this is not
physical root attestation. Production guardSearch MUST enforce the original
root pins, and the independent parent MUST compare actual report context to
them. Neither check may be relaxed to accommodate a synthetic fixture.

I07 does not seed fictitious valid near-limit history. A fresh state with
nonzero/incoherent counters is InputFailure before callbacks. Test candidate
sizes0/268435456 as InputLimit before allocation/reservation/open, tiny actual
reservation/read arithmetic and replay/count controls. Under2 exclusive
<256MiB files, dynamic512MiB-input/1GiB-scan overrun is mathematically
unreachable. Those inherited ceilings remain enforced and source-reviewed;
the suite does not claim to have crossed an unreachable bound or allocate
huge buffers/change limits to do so.

For a COHERENT fixed-two JobStopped report, the terminal refusal MUST be
LibraryInputsSize (kind3), site metadata_job_sections, limit2097152 and
2097152<actual≤4297064447, with context.sections≤actual and the existing
stopped snapshot/terminal-attempt rules. Other global stop sites/categories
are prevented by this closed caller protocol; unexpected ones remain bounded
raw failure, not a successful/coherent substitute. The independent56-byte
bigobj fixture declares4294967295 sections: context.sections=actual4294967295,
directiveBytes/tokenCount0, position contexts null, while job.sections=0,
inputCount1/inputBytes56/attempts1/stopped=true. The refused global charge is
not committed; per-attempt declared sections must never be confused with it.

Review additions also require exact whole canonical JSON+LF; coherent strict-
and profile-terminal unknown attempts; isolated critical/attempt adversaries;
first-identity and held-size refusal before payload work; open-failure sticky
poisoning; and row32/33/name259/260 controls. A row33 case also exceeds union32;
it is explicitly not claimed as an isolated reachable resource boundary.
The proposed producer, source reviews, actual envelope/source sizes and full
retention forecast remain pending. No source-retention/run/cap authority is
inferred from this freeze.
