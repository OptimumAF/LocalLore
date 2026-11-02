# Pinned UCRT archive-padding observation contract

Refs #25 D04.01/.02/.04 supporting, #31 D09.03 supporting, #21.
Root claim6584315284; `prep/ucrt-padding-observation-v1`, existing physical
D: review checkout, based on accepted PR348/main`db2c23d0`.
**SOURCE PREPARATION ONLY; all new checks and observations UNRUN.**

## Question and boundary

The accepted V3 capture pinned `ucrt.lib`,285588B,
SHA256`7ef4eac926bf597d2f243f16cdfed7e0db22cb3ca34a1d7e088a84c994a03d66`.
Both parser modes refused `LibraryInputsFormat/archive_padding_byte`, member4,
member-header offset98452. The saved report does not contain that member's size,
padding position or byte. None of those values is known now.

Microsoft's [PE/COFF specification](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format)
describes even-address member headers and LF alignment padding. LLVM's primary
[archive-reader source](https://llvm.org/doxygen/Object_2Archive_8cpp_source.html),
`ArchiveMemberHeader::getNextChildLoc`, advances by aligned size without examining
the skipped byte. Neither source establishes this pinned file's actual byte or
authorizes changing the accepted parser. Keep helper9972/profile-v1/strict-v1
unchanged. No object-body, symbol, longname or DEFAULTLIB interpretation is added.

Prepare ONE fixed read-only observation of this already located input, not a
new library search. Use original root3 and the exact V3 root/leaf identity/pin;
verify both whole-file scans against its existing digest on ONE read-only handle.
Then inspect at most the first FIVE archive headers through member4/header98452,
emitting bounded header/padding facts. No library payload is saved. No additional
input, fallback root, recursive lookup, compiler/linker, worker/model/app/device,
OS setup, download, settings, deletion or desktop control belongs to this task.

This can falsify a padding hypothesis. An observed LF or even-sized target must
be reported honestly, with a false correlation flag, rather than discarded for
failing to match the expected refusal. Every qualification/link/closure flag
remains false; successful observation never grants metadata or build acceptance.

## Public development-only module and fixed callback API

New `native/llama-worker/library_padding_observation.mjs` has no filesystem,
environment, process or model access. It may use built-in crypto and Buffer.
It exports these exact names; no alternate parser implementation is adopted:

* `PADDING_OBSERVATION_PROFILE`: deeply frozen object with `id`=
  `ucrt-padding-observation-v1`, `version`=1, `purpose`=
  `build_input_error_site_only`, and a frozen `limits` object:
  `inputBytesInclusive:285588, headerCount:5, chunkBytes:65536, scans:2,
  selectedReadBytes:571176, reportBytes:8192, identityBytes:256`.
* `observeArchivePaddingV1(buffer,target)` returns a frozen observation.
  `target` has ONLY `memberIndex,memberOffset`, integer index0..4 and even
  offset≥8. The production caller supplies exactly4/98452; synthetic tests may
  use smaller targets. No path/command or runtime selector is accepted.
* `readPinnedArchiveV1(expected,adapter)` asynchronously returns a shallow-frozen
  `{buffer,io}` after both scans, closure and final identity checks succeed.
  `expected` has ONLY `bytes,sha256,rootIdentity,leafIdentity`: positive bytes≤285588,
  lowercase64-hex digest, identity tokens matching`[A-Za-z0-9_.:-]{1,256}`.
  Copy primitive expectations before callbacks; mutations cannot retarget a read.
* `encodePaddingReportV1(report)` validates the closed schema below and returns
  compact JSON plus exactly one LF,≤8192UTF8B, with no padding/truncation of facts.

Expected/report/observation/io records must be plain data, with Object.prototype
or null prototype, exact own enumerable keys and no symbols/accessors/extra array
properties. Adapter/API/wrapper holders may contain ONLY their specified callable
methods as own data properties. Arrays are dense. Numeric fields are safe
unsigned integers, flags are primitive Booleans. No callback-supplied raw error
message/path is exposed. Successful metadata snapshots contain no Buffer aliases.

Adapter/wrapper holders also have Object.prototype or null prototype. The FIRST
API holder has three specified callbacks PLUS its descriptor/proofs data. Invalid
observer target domains (index5/negative/fractional, odd/<8 offset) usePaddingType;
a valid target that disagrees with the reached header usesPaddingTarget. Buffers
outside the declared length range, including<8 or285589, usePaddingBounds; an
eight-byte wrong magic usesPaddingSignature. No other overlapping-error priority
is implied. Successful io is a frozen snapshot; only the returned Buffer remains
ordinary mutable data inside the shallow-frozen result.

`PaddingObservationError` has `name`=`PaddingObservationError`, `message` and
`code` equal to one fixed code, and `io` either null or a frozen current snapshot.
Fixed codes: `PaddingType,PaddingBounds,PaddingSignature,PaddingHeader,PaddingSize,
PaddingPrefix,PaddingTarget,PaddingPin,PaddingIdentity,PaddingRead,PaddingHash,
PaddingStopped,PaddingClose,PaddingSource,PaddingReport`.
No unrestricted callback or code/file/shell executor is exposed by an app API.

## Header observation, not object parsing

Require Buffer≤285588 and exact eight-byte archive magic. Start at offset8.
For each of at most five headers, require its60B range, trailer`60 0a`, printable
ASCII in the first58B, and an ASCII decimal size after trailing spaces are
removed. Match the accepted helper's digits-only decimal behavior, including
leading zeroes; reject signs, leading spaces, nondigits and unsafe values.
Bounds-check body start/end and any required alignment byte without overflow.

Before the target, a required padding byte must be LF; advance to the next even
header. A mismatched preceding pad stops with`PaddingPrefix`. Do not follow
names, inspect index bodies, resolve longnames or validate COFF contents.
At the exact requested index AND offset, observe any available required pad
value without assigning it a validity policy. An even-sized target has no pad.
Stop after this target; later bytes are not interpreted. A missing required pad
or truncated range is a failure, not an invented byte. No later member can
substitute for the requested one.

The observation has ONLY`headers,target`. `headers` is a frozen array of
index+1 frozen records with ONLY`index,offset,bytes,bodyStart,bodyEnd,
paddingRequired,paddingOffset,paddingByte`. `target` has ONLY`memberIndex,
memberOffset,memberBytes,bodyStart,bodyEnd,paddingRequired,paddingOffset,paddingByte,
nameHex,sizeHex,endHex`. It duplicates the final header's corresponding numbers.
`nameHex` is the16B field as32 lowercase hex characters; `sizeHex` is10B/20hex;
`endHex` is`600a`. These decoded field bytes must agree with the framing and size.
Pad offset/byte are null when not required; otherwise offset=bodyEnd, byte0..255.
Every prior header's paddingRequired agrees with parity and its next offset;
prior required pad values are10. Do not return dates, paths, object bodies or
whole library bytes as facts. Observing this prefix is not validating the archive.

Use `PaddingType` for bad argument/data shape, `PaddingSignature` for magic,
`PaddingHeader` for trailer/ASCII, `PaddingSize` for decimal, `PaddingBounds` for
missing ranges, `PaddingPrefix` for preceding pad, `PaddingTarget` for index/
offset mismatch. Never mutate caller buffers or alias them in returned facts.

## One-handle pinned streaming seam

The fixed real adapter is private to the local collector. Its ONLY callbacks
are synchronous`isLive()`, async`identify()` and async`open('r')`.
`identify()` returns ONLY`bytes,rootIdentity,leafIdentity`; the held wrapper
returns ONLY async`stat(),read(buffer,offset,length,position),close()`.
`stat()` returns ONLY`bytes,leafIdentity`; `read` returns ONLY`bytesRead`.
Production paths/root identity come from the pinned predecessor, never argv,
environment overrides, an archive name or a test callback.

Validate expectations/adapters before I/O; reserve one input, its bytes and twice
its bytes BEFORE the first identify/open/allocation. Require pre-open/final path
identity and held
identity to match. Allocate at most the expected input plus one≤65536B scratch
buffer. Read exactly two complete scans on the same handle in≤65536B requests;
positive short reads are valid. Both full digests and the retained first-scan
buffer's final digest must match the expected pin. Check that retained buffer
again AFTER the final identity callback, immediately before return. The fixed
caller checks its in-memory digest before and after synchronous observation.
These memory hashes add no SDK file scan. No retry/reopen/third hash
scan of the SDK file is permitted. Return no buffer on failure.

Check liveness around awaited operations; count valid returned bytes BEFORE
the late liveness check. EOF/zero progress, oversized/fractional/invalid counts,
read/hash/identity drift and stopped operations fail closed. Invalid read counts
cannot establish additional known bytes; retain the known stopped prefix rather
than claim exact unknown traffic. Always attempt one close for an acquired
handle, even after late stop/stat failure. First failure wins; later close
failure cannot replace it. A close exception leaves`closed:false`.

Once `open` resolves to a nonnull object/function wrapper, record`opened:true`
BEFORE wrapper/stat/read shape validation. Attempt an own data-property callable
`close` exactly once even if the remaining wrapper is malformed. If no callable
close exists, keep`closed:false` and fail`PaddingRead`; never fabricate closure.
A primitive/null open result fails`PaddingRead` without a recorded acquisition.
Do not invoke accessors merely to discover cleanup. Invalid read/wrapper shapes
map to`PaddingRead`; held-stat result/shape failures map to`PaddingIdentity`.

`io` has ONLY`reservedInputs,reservedBytes,reservedReadBytes,actualReadBytes,
opened,closed,verifiedPasses`. Initial counts are0 and flagsfalse. Reservation
is0or1; for1 its bytes equal expected and read reservation=2×bytes. Actual reads
are bounded by reservation; verifiedPasses0..2 require at least that many full
scans' bytes. `closed:true` requires`opened:true`. Success requires two verified
passes, actualReadBytes=2×bytes and opened/closedtrue. Hash mismatch does not
refund reads; error snapshots preserve known work. Pre-open error closes nothing.

Reservation0 requires all byte/pass counters0 and opened/closedfalse. Openedfalse
requires actualReadBytes0, verifiedPasses0 and closedfalse. Any returned bytes or
verified passes require openedtrue. Reservation1 always uses exact expected-byte
reservations, including a failed pre-open identity check; no fictitious reads.

Use `PaddingPin` for bad expected pins, `PaddingIdentity` for path/held checks,
`PaddingRead` for open/read/count failures, `PaddingHash` for digest/buffer drift,
`PaddingStopped` for false/non-Boolean liveness, `PaddingClose` for sole close
failure. A thrown`isLive` also maps to`PaddingStopped`; thrown`identify`/`stat`
to`PaddingIdentity`; thrown`open`/`read` to`PaddingRead`. Sanitize callback errors
into these causes, never raw paths. Invalid adapter shape is`PaddingType` before
reservation; invalid expectations are`PaddingPin` before reservation.

## Closed report and supervisor data validation

The report's ONLY keys are`version,kind,purpose,qualified,linkQualification,
closureComplete,captureComplete,status,selfchecks,proofs,input,io,observation,
priorRefusal,matchesPriorRefusal,critical`. Version1; kind=
`ucrt_padding_observation_v1`; purpose=`build_input_error_site_only`; all three
qualification flagsfalse. `status`=`complete|stopped`; captureComplete agrees.
Only a complete report has a nonnull observation and null critical. A stopped
prefix has observation/correlationnull, a fixed critical code and coherent io.

`input` has ONLY`name,rootIndex,sourceSlot,bytes,expectedSha256,rootIdentity,
leafIdentity`, binding `ucrt.lib`,3,33,285588 and its predecessor pin. It declares
an EXPECTED pin; a stopped read does not newly attest its payload. Complete io
must attest the matching two scans. The priorRefusal has ONLY`kind,site,
memberIndex,memberOffset`, fixed to`LibraryInputsFormat,archive_padding_byte,
4,98452`. For complete observations `matchesPriorRefusal` is computed ONLY as
target.paddingRequired AND target.paddingByte!=10. False is a valid diagnostic
observation, not a reason to discard counterevidence. It is not a full parser replay.

A COMPLETE report must bind observation.target.memberIndex/memberOffset exactly
to priorRefusal4/98452, contain exactly FIVE chained headers, and bind the final
header to target. Smaller synthetic targets are permitted only at the pure
observer API, not in a complete production report or report fixture. This prevents
a different member's non-LF byte from masquerading as the requested observation.

For stopped reports, `PaddingPin` requires zero reservation/read/acquisition.
`PaddingSignature,PaddingHeader,PaddingSize,PaddingBounds,PaddingPrefix,
PaddingTarget` describe framing AFTER successful pinned reading: require full
two-pass io with opened/closedtrue. `PaddingType` allows either zero initial io
or that full-read state. Sole`PaddingClose` requires openedtrue/closedfalse,
two verified passes and full returned bytes. `PaddingHash` requires openedtrue
and at least one full scan's returned bytes. `PaddingIdentity`/`PaddingRead`
require reservation1; `PaddingStopped`/`PaddingSource` may retain any otherwise
coherent prefix. `PaddingReport` may not be emitted as a valid stopped report:
an invalid encoder envelope is bounded raw failure. These rules do not replace
first-cause precedence when a later close also fails.

`proofs` has ONLY eleven lowercase64-hex values: `module,first,parentFirst,
reader,supervisor,roster,predecessorSnapshot,predecessorProcess,predecessorResult,
predecessorRootReview,descriptor`. Selfchecks are the actual Node summary below.
The parent independently binds real source/proof/pin values, strict UTF8, one-LF
compact roundtrip JSON, exact keys/types/counts, header chaining/hex/parity,
correlation, io prefixes and allfalse qualifications. LF/even-size observations
remain valid complete capture with false correlation. Oversized/invalid envelopes
stay raw failure; never trim fields or invent a smaller successful snapshot.

Fixed supervisor functions for independent parent FIRST:
`Validate-PaddingReport([byte[]]$Raw,$ExpectedProofs,$ExpectedPin)` returns only
the parsed record, or throws`InvalidPaddingObservationReport`;
`$ExpectedPin` has the same seven keys as report.input. `$ExpectedProofs` has
the eleven proof keys. `Validate-PaddingParentSummary($Value)` returns nothing
or throws`InvalidPaddingParentSummary`.
The trusted expected-proof/pin parameters are PSCustomObject/JSON-data values
in both production and FIRST. Only suite-summary handoff intentionally accepts
a live OrderedDictionary; do not broaden global raw-record type checks.
Normalize ONLY a trusted OrderedDictionary summary, keep global record checks
strict. No alternate function/path selector. Parent FIRST definitions perform
no I/O and do not run on import. START precedes these checks; child creation
requires actual canonical6/6, which the child independently pins before Node FIRST.

The independently authored pure validators live in the normal project module
`native/llama-worker/library_padding_validation.ps1`. The fixed local supervisor
imports this exact literal path after checking its owner-bound source digest,
and checks that digest again immediately after import and at postflight. This
supersedes the preparation claim that its definitions would be embedded verbatim
in the supervisor. Like the fixed public Node module and parent FIRST import,
this is a named source dependency, never an argument/environment/code selector.
Owner, source-review and Stage bind the complete six-source closure (module,
Node FIRST, parent FIRST, validation, reader, supervisor); Stage also binds the
validation digest explicitly. Review the entire imported module for top-level
work and name collisions. No existing artifact is moved or reclassified: both
local collector copies remain fully charged, uncompressed, within48KiB.

## Independent FIRST, frozen before producer

Node `runPaddingObservationSelfchecksV1(api)` receives a frozen API containing
ONLY the three functions,`descriptor,proofs`. Use synthetic Buffers/adapters,
no files/env/children/model. Execute all24 fixed groups; failures retain IDs.
Return ONLY`version:1,kind:'ucrt_padding_first_v1',executed,passed,failed,
failed_case_ids`, IDs F01–F12/I01–I08/E01–E04. No omitted/renamed assertions or
success shortcuts. Cases must test actual callbacks/encoder, not duplicate them.
If this summary fails its24/24 gate, retain it as bounded raw failure output
before returning nonzero, without constructing or calling the SDK adapter.

* F01–F03: exact non-LF, LF and other-byte observations; no qualification claim.
* F04–F08: magic/type/header/decimal/body and missing-pad boundaries.
* F09–F12: exact target, earlier padding, parity/even target, suffix-not-parsed,
  immutable facts and caller-buffer nonmutation. Combine related variants without
  losing those properties; document the mapping in source.
* I01–I08: two-scan positive/short reads; reservation-before-open/limits;
  path/held/final drift; EOF/bad counts; digest/buffer/expected mutation;
  early/late stop with actual-byte charging; callback/close first-cause behavior.
* E01–E04: complete true/false-correlation reports; closed data/proofs/types;
  coherent stopped prefixes; real bounded extrema, invalid framing/oversize.

Parent `Invoke-PaddingParentSelfchecksV1($ExpectedProofs,$ExpectedPin)` calls the
actual two fixed functions. Six groups V01–V06 cover live OrderedDictionary and
canonical summary handoffs/malformed counters, complete observations, closed
proof/pin/qualification checks, numeric/UTF8/LF/raw framing, header/hex/correlation
and stopped-I/O prefixes. Return the same six summary keys, kind=
`ucrt_padding_parent_first_v1`, executed6. Missing validators/unexpected errors
fail their group; never skip. All new cases remain UNRUN until a separate decision.

## Admission, retention and unavailable work

Prepare complete fixed local reader/supervisor sources before requesting any
run. Bind the settled V3 snapshot/result/process/Root review; preserve the exact
V1 nine-file pre-child failure exception and V2 four-file unlaunched boundary.
Unrelated stops/incomplete STARTs remain fatal. New current owner/Stage/START/
STOP leaf expectations derive consistently from their own fixed stem.

Use one pinned Node24.22.1 child,60s/one-kill/5s drain, stdout8192/stderr1024.
Proposed record ceilings: process20480, raw9216, decoded9216, snapshot8192,
START768, result2048, Root review1536, STOP512, parent summary1024 =52992B;
reserve57344B (56KiB),4352slack. The TWO whole local collector-source copies
(reader+supervisor) in the charged packet must total≤49152B (48KiB), retained
uncompressed; owner/Stage/source-review≤4096B. Complete ceiling110592B (108KiB)
would leave4370B under current114962B metadata headroom. This is a hard planning
ceiling, NOT measured full-source admission. After independent whole-source
review, Root may stage only the two exact source copies and a truthful source
review record under the existing cap, following fresh retention-only inventory
and complete future reserves. This is authorized source preparation for the
ongoing assignment, not a library read or execution of either collector.
No owner decision, Stage, START, suite or child may be fabricated or run during
that preparation. A new finite owner decision remains required for the packet.

The public module/FIRST files are normal source-controlled project code, as in
the preceding packets, not generated evidence or SDK-data repositories. Do not
move/reclassify prior evidence or put extra collector copies/outputs outside the
charged packet to evade its limit. Every new packet source/output is charged.

Carry current2440942/2555904 metadata and decoded32979, conservative group/joint
charge22154, all old output and original target baseline. Keep64MiB group,
724MiB joint,4GiB original target growth,576KiB old records/8MiB fixtures;
this read-only action may create no target/runtime products. Fresh inventory,
complete sources/envelopes, independent reviews and exact full-reserve forecast
must precede a NEW finite owner decision. V3 isSPENT, no current read authority.
No cap increase/reset, new output root, deletion or automatic retry is implied.

Engine, native IPC/WebView, frontend, Android, model/worker/OS and story-quality
qualification remain separate. No render artifacts are proposed. Full desktop
and D04/D09 acceptance remains open; this diagnostic cannot enable Author.
