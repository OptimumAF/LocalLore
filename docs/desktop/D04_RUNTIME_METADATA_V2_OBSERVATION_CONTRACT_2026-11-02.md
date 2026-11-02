# Fixed-two runtime metadata v2 observation: source contract

Refs #25 D04.01/.02/.04 supporting; #31 D09.03 supporting; #21.
Claim6591090481. Base accepted main dcbb4bdb (PR369). SOURCE ONLY / UNRUN.
The PR369 code grant is SPENT. This contract grants no child or SDK read.

## Scope and ownership

PR348 observed slots33/34 with metadata-v1: UCRT refused required NUL archive
alignment, vcruntime parsed only in compatibility mode. PR364 separately
observed the UCRT error-site byte. PR369 now passes224 synthetic groups for
an explicit metadata-v2 job. None of those results observes either file in v2.

Prepare one distinct, development-only observation session using the accepted
v2 job and UNCHANGED `readPinnedArchiveV1` from `library_padding_observation.mjs`.
No binary parser, resolver, alternate reader, dependency graph, linker model,
worker adoption, application IPC or configurable filesystem API is added.
The old v1 projection, snapshots, tests and error ordering remain untouched.

Root owns this NEW contract, then NEW `library_runtime_metadata_v2.mjs` only.
An independent serialized author first freezes NEW
`native/llama-worker/library_runtime_metadata_v2_first.mjs` on a separate
branch, against this contract, BEFORE producer code. Reviewers read only.
Root integrates; all shared checkout/Git mutations are serialized.

## Actual future input plan, not an observation

Exactly the already observed two pins, no search or fallback:

| Index/slot | Name/root | Bytes | SHA256 |
| --- | --- | ---: | --- |
|0/33|ucrt.lib /3|285588|`7ef4eac926bf597d2f243f16cdfed7e0db22cb3ca34a1d7e088a84c994a03d66`|
|1/34|vcruntime.lib /1|38478|`d8fe742a11b6babde717141b9316702fca0a876c7ef68055e9aedac66f31768c`|

Actual production adapter paths/root/leaf signatures must match retained
PR348V3 pins and original roots, not merely the names/hash above. No old32
payloads are re-read. One held read-only handle and two full scans per input:
324066 input bytes,648132 selected read bytes; <=65536B positive short reads,
held/path/root identities, SHA checks, retained-buffer hash and one close
attempt reuse the accepted reader unchanged. Source/tool/normal-image guard
hashing is separately disclosed, not charged as selected payload scans.

The pure session seam below accepts smaller synthetic pins for FIRST. It is
NOT authority to select real files. A future fixed driver must compare both
complete pins with retained evidence before adapter construction. Adapter
construction and real path/root observations occur ONLY after all required
selfchecks pass in the separately admitted sole child.

## Closed private API

Export ONLY `createRuntimeMetadataObservationV2(proofs)`. It returns a frozen
object with ONLY async `observe(index,pin,adapter)`, `snapshot()`, `encode()`.
There are no filesystem/environment/process imports or top-level execution.
The module imports node:crypto, the accepted real v2 job and accepted reader.

`proofs` is an exact plain data record with ONLY module,first,reader,supervisor,
runtimeSnapshot,runtimeRootReview,paddingSnapshot,paddingRootReview,descriptor.
Each is primitive lowercase64hex. Copy it at construction; later caller
mutation cannot alter evidence. The actual driver binds real source/record
digests, including the descriptor's JSON digest. Synthetic tests may use
synthetic digests, explicitly never real provenance. Wrong setup throws fixed
`RuntimeMetadataV2Setup` before any adapter call.

`pin` is exact plain data with ONLY bytes,sha256,rootIdentity,leafIdentity.
bytes is positive safe integer <= the index's285588/38478 ceiling; SHA is
primitive lowercase64hex; identities are ASCII letters/digits/underscore/dot/
colon/hyphen,1..256 characters. Reject accessors, symbols, inherited extras,
sparse arrays, boxed/coerced values and wrong prototypes without invoking
accessors. A snapshot copies primitive pin values, never adapter references.
Adapter is the accepted reader's exact isLive,identify,open callback shape;
no new read protocol. No bypass or monkey-patched reader/parser seam is added.

Create ONE real `createLibraryMetadataJobV2('msvc-library-metadata-v2')` per
session. Private state permits exactly index0 then1, once each, no overlap or
retry/reset. Wrong index, invalid pin, reentry or call after completion poisons
the session with first cause `RuntimeMetadataV2Sequence` or `RuntimeMetadataV2Pin`;
no adapter call for the refused request. A caller cannot recover by changing
snapshots/flags/pins. An in-flight read must still settle/close through the
accepted reader; retain its returned I/O work before honoring the poisoned
session. Never inspect after poison or advance to the next input.

On successful acquisition use its SAME Buffer for `strict-v1` then the exact
v2 mode in that ONE job. Hash it before and after each synchronous inspect;
no mutation/normalization. Entry identity, attempts, sections, stop state and
work ceilings remain authoritative in the real job. Snapshot real counters,
including sections charged by refused attempts; never infer them from success
rows. If the job stops, stop before the next mode/input. Ordinary known parser
refusals retain category, fixed safe source site and eight numeric/null context
fields, and allow the next mode only while the same job remains live. Unknown
errors/result shapes/mutation stop with `RuntimeMetadataV2Inspect` or
`RuntimeMetadataV2Hash`. Reader failures preserve their accepted fixed Padding*
code and actual I/O; never expose OS messages or replace the first cause.

`observe` resolves to a detached frozen snapshot after a completed input,
including known parser refusals. A critical failure rejects with Error.message
equal to the first fixed cause, while `snapshot`/`encode` retain partial work.
Report calls are read-only and allowed before/during/after acquisition.

## Report and privacy

Canonical report keys/order: version,kind,purpose,qualified,linkQualification,
closureComplete,captureComplete,status,proofs,job,io,rows,critical. version2,
kind `fixed_two_runtime_metadata_v2`, purpose `build_input_metadata_only`;
ALL qualification flags false. status is incomplete/pending/stopped/complete;
complete iff both rows completed, no pending operation and critical=null.
A complete capture may contain unavailable metadata; it is not parse success.
critical is null or the first fixed failure code. Snapshot deeply freezes a
detached plain data tree; `encode` serializes that canonical tree with JSON.stringify,
at most24576 UTF8 bytes. Resource excess becomes sticky
`RuntimeMetadataV2ReportLimit`; no truncation, partial-success or flag promotion.

job is the real six-key v2 snapshot (inputCount<=2,attempts<=4). io has ONLY
reservedInputs,reservedBytes,reservedReadBytes,actualReadBytes, summed from
settled reader records. Pending work is explicitly unreported until settlement;
it is NOT asserted zero live work. rows is exactly two ordered records, each
ONLY slot,name,rootIndex,status,pin,io,strict,profile. Fixed slot/name/root are
33/ucrt.lib/3 and34/vcruntime.lib/1. Status unstarted/reading/complete/failed.
pin=null until validated; io=null until reader success/failure settles. Its
settled exact reader record retains opened,closed,verifiedPasses and reservations.
No omitted row, invented pin or refunded work after failure.

strict/profile=null if unattempted. Otherwise an exact record with ONLY
status,summary,error. Refused: status=refused,summary=null,error ONLY kind,site,
context; kind one of the real six LibraryInputs categories, site bounded ASCII
source token1..64, context exact memberIndex,memberOffset,sectionIndex,sections,
directiveBytes,tokenCount,actual,limit (nonnegative safe integer or null).
Unknown errors are critical, not ordinary refusals. Parsed: status=parsed,
error=null, summary ONLY profileId,objects,imports,sections,deviations,
metadataSha256,defaultLibraries. The full actual metadata is hashed using its
existing canonical insertion order, not included in output. Never emit raw
directives/member names/payloads/paths. Preserve every defaultLibraries name,
sorted unique canonical ASCII .lib names<=259B, at most32 per row; excess is
ReportLimit, not truncation or inferred absence. No recursive lookup or graph
join is performed. A new name is data only, never a command or permission.

Strict summaries have EXACT old three deviation keys; profile summaries have
EXACT four including nulArchivePaddingMembers. All counts/bounds derive from
accepted descriptor. Results are validated/copied immediately, so mutation of
reports/results cannot alter the job/session/other row. No v2 relabeling as v1,
no old observations upgraded to v2 and no graph completeness assertion.

## Independent FIRST and next admission

Independent export `runRuntimeMetadataV2Selfchecks(api)` takes ONLY the factory;
no producer fixture/expected-data helper. No top-level execution/filesystem/
process/SDK access. It constructs synthetic Buffers/adapters and its own expected
reports. Exactly20 groups T01..T20. Summary ONLY version,kind,executed,passed,
failed,failed_case_ids: version1,kind runtime_metadata_v2_first,20/20/0/[]
is the sole successful gate. Failed finite groups return actual IDs; a missing
factory is UNRUN_SETUP, never a passing behavioral RED.

T01 setup/proof schema/copy; T02 frozen empty report/encoding; T03 actual two
LF-object strict/v2 parses and same-job counters; T04 NUL archive strict refusal
then v2 success and exact three/four shapes; T05 ordinary two-mode refusal
remains complete capture; T06 wrong order/repeat/third request sticky;
T07 reentry/poison/settled read/close accounting; T08 invalid pin before I/O;
T09 first/second digest mismatch; T10 positive short/chunked reads and two scans;
T11 held/path identity drift; T12 zero/overread/read throw; T13 close-only and
first-failure retention; T14 late stop charges positive bytes and closes;
T15 report/pin/result isolation; T16 sorted DEFAULTLIB extraction/full metadata
digest/no raw directives; T17 32 names accepted/33 rejected without truncation;
T18 complete/partial/pending statuses and unattempted nulls; T19 invalid
callback/wrapper schemas/unknown I/O failures; T20 false qualification flags,
v1 projection isolation and exact report keys across success/failure branches.
Keep every subcase; fixtures<=2MiB/group, no large boundary buffers required.

A future packet must retain/review exact programs/sources, these FIRST, old224
checks where applicable, source/owner/Stage/START, concurrent bounded stdout/
stderr, deadline/closure, complete prior-file/failure fences and full reserves.
All selfchecks precede real adapter construction/input observations. Actual
program sizes, all source/record hashes, synthetic count/finite child plan,
full stream/report/STOP accounting and fresh storage inventory are prerequisites
to a separate owner execution decision. Do not infer that this source contract
is a ready or approved observation packet.

Current last audited metadata2604606/2732032B, spare127426B. All other limits
unchanged, all prior output retained. No cap reset, new evidence root, deletion,
automatic retry, native build/link/worker/model/app/device/OS operation, download,
settings change or desktop control. D04/D09/full epic and human story-quality
gates remain open; AuthorDisabled. PR366 and the protected chat stay untouched.
