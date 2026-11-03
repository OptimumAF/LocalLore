# Exclusive pre-embed preservation v1: source contract

Refs #25 D04.01/.02/.04 supporting; #31 D09.03/.05 supporting; #21.
Base accepted main a635686c / PR390. SOURCE ONLY / ALL NEW CHECKS UNRUN.
PR393 is separate, unchanged and not a dependency. Its approval is pending.
Current evidence cap2860KiB and every prior limit/failure remain unchanged.

## Why this concrete component

The accepted coordinator requires an ordinary exclusive pre-embed copy BEFORE
MT, equal to the linked executable, with failed copies preserved. Implement the
actual development-only Node filesystem algorithm, plus a narrow injected
filesystem/clock seam for independent tests. Do not use fs.copyFile/cp: Node
documents removal of a destination after some copy errors; retain every
partially created file instead. No unlink/rm/rename/truncate, overwrite, hardlink,
reflink, fallback copy, mkdir, adoption, subprocess, lookup or general file API.

[Node v24 filesystem semantics](https://nodejs.org/docs/latest-v24.x/api/fs.html#fspromisescopyfilesrc-dest-mode)
are a source reference, not evidence this implementation ran on Windows.
Installed Node24.22.1 remains the proposed test runtime; linked latest-v24 docs
currently report24.22.2. No download or runtime upgrade.

This helper is NOT an admission port. The caller still needs independently
proved fresh exclusive output-root ownership/lease, complete output roster,
authority/storage/full reserves, ordinary roots, source/tools/headers/inputs,
environment, ordered resolution/no-shadow, process containment limitations,
normal worker invariance and fresh object directives. Existing output roots
must already exist; this component creates only the fixed preEmbedCopy file.
A boolean or this proof cannot establish the missing prerequisites.
The accepted coordinator has a5000ms prepareManifest outer timer and no signal
in that request; this helper has a60000ms cooperative deadline. It is NOT yet
wired as that port. A future reviewed wrapper must handle cancellation, late
settlement and continued ownership of every pending handle/output; it cannot
release a lease or claim closure when the outer coordinator has timed out.
No MT or later child can follow an unsettled/failed preservation operation.

Root owns this NEW contract then NEW producer
native/llama-worker/worker_artifact_preembed_copy_v1.mjs.
Independent serialized author owns NEW worker_artifact_preembed_copy_v1_first.mjs
before producer. No accepted module/shared engine/app/model/persistence edits.

## Factories and closed surface

Export ONLY:
- createWorkerArtifactPreembedCopyV1(spec)
- createWorkerArtifactPreembedCopyV1ForTesting(spec,adapter)

spec exact plain/null-prototype own enumerable DATA {config}. Pass config to
accepted planWorkerArtifactComparisonV1; propagate its two fixed recipe errors.
Capture its immutable A/B recipe paths; never accept a supplied recipe/path.
Production factory refuses non-Windows with Error('WorkerArtifactPreembedCopyV1Platform').
Other invalid factory/adapter shape -> Error('WorkerArtifactPreembedCopyV1Invalid').
No getters/symbols/extras/coercion; capture all functions and config at factory.

Test adapter exact own DATA {identify,open,now}, functions captured, trusted
development capabilities, never player/model input.
identify(path,kind) -> {identity,ordinary,real}, kind 'directory' or 'file'.
identity nonempty ASCII [A-Za-z0-9_.:-] <=256; ordinary boolean; real boolean
meaning canonical realpath equals that exact requested Windows path modulo
slash/case. Production uses lstat, realpath and dev/ino identity; directories
ordinary and file nlink===1 required. Reject missing/zero identity, symlinks,
nonfiles/nonfolders, mismatched realpath or multihardlinks. Node cooperative
identity checks are NOT complete Windows reparse/alternate-name/race protection.
Unknown native identity cannot be asserted safe. Production identity is decimal
dev:ino with bigint dev>=0 and ino>0; zero inode refuses. Path comparison folds
ASCII A-Z only after slash normalization; Unicode code units stay exact.
No OS settings/ACL changes.

open(path,mode) returns exact own DATA {identity,read,write,sync,close}.
mode 'r' for linked exe/manifest, 'wx+' for fixed preEmbedCopy ONLY.
identity() -> {identity,bytes,ordinary}; identity token rules above,
bytes integer0..67108864; ordinary boolean with same file/nlink rules.
read(buffer,offset,length,position) -> integer bytesRead;
write(buffer,offset,length,position) -> integer bytesWritten;
sync() -> undefined; close() -> undefined.
Capture close BEFORE validating other methods or doing any later await. If
returned value has a valid own DATA close function, attempt it ONCE even if
another field is invalid or cancellation/deadline occurred during open.
An offered open with throw/rejection/invalid result/missing close is uncertain
unless a captured close succeeds. No fabricated closure; no cleanup retry.

Return frozen {copyNext,cancel,snapshot}. copyNext(request) takes one argument
exact DATA {candidate,rootIdentity,executableIdentity,manifestIdentity,linked}.
linked exact DATA {executable,manifest}; each exact DATA {sha256,bytes}, nonzero
lowercase hex64; executable integer1..67108864, manifest1..65536.
candidate must be current fixed 'A' then 'B'; identity tokens as above and
executableIdentity !== manifestIdentity. Never caller paths/commands/limits.
Malformed/wrong candidate/extra args -> terminal INPUT, zero new reservations
or I/O. Concurrent call rejects Error('WorkerArtifactPreembedCopyV1Busy') with
no effect on the original call; after any terminal failure/cancel or two
successes, further calls reject Error('WorkerArtifactPreembedCopyV1Used').
Consume each offered job before first await; a failed job is never retried.
cancel() returns true once before terminal state, false thereafter; pre-run
cancellation leaves zero I/O/reservation and next copyNext returns CANCELLED.
Busy check precedes used, cancel and request validation. Used precedes other
validation. Idle cancellation (before A or between A/B) permits ONE unoffered
CANCELLED proof with candidate null and zero new reservation, then Used; snapshot
stopped is already true/nextCandidate null after that cancellation. In-flight
cancel affects the current proof; no extra cancellation proof follows.
Cancelled/failed partial output stays. No reset, authority token, record or MT.

## Bounded algorithm and invariants

One reused65536B buffer and incremental SHA256; no whole-file allocation.
Per-copy deadline60000ms inclusive from its first now(), checked before and
after every awaited operation and before final proof selection. now finite
nonnegative monotone across the entire factory including A/B; invalid/throw/
backward -> CLOCK. Each copy starts a new60000ms deadline, not a new monotonic
history. Deadline -> DEADLINE. Cancellation takes precedence at a live check.
Cancellation -> CANCELLED after a pending operation settles. No timers, retry
or hard containment claim; an unresponsive native promise needs the caller's
outer supervisor and makes closure uncertain there. Check liveness before any
new ordinary operation; cleanup closes still occur after stop.

Valid offered job reserves BEFORE first I/O: copies1, readBytes=4*exe+2*manifest,
writeBytes=exe. Job clock setup failure after valid input still spends reserve.
Totals at most2copies,537133056read,134217728write. These algorithmic maxima do
NOT extend the existing physical64MiB aggregate target forecast: future admission
must fit actual copies AND all other outputs in the unchanged full allowances.
Invalid/concurrent/used/
pre-cancel calls reserve zero. Reservations never returned after failure.

Fixed algorithm; all identity/size/hash checks fail closed:
1. identify outputRoot directory; require pinned rootIdentity/ordinary/real.
2. open source executable 'r'; capture methods; stat matches pinned identity,
   expected exe bytes/ordinary. Scan exactly exe bytes + one EOF read; hash
   expected. Stat again; re-identify source path/root before destination open.
3. open manifest 'r'; stat matches its pinned identity/size/ordinary. Scan to
   expected size + EOF, hash expected, stat again. Keep source+manifest handles.
4. re-identify root, executable and manifest paths; require pins/ordinary/real.
   Only now open fixed preEmbedCopy with 'wx+'. Capture close first. Its stat
   must be ordinary, bytes0 and identity distinct from source/manifest.
5. Second source scan to exact length+EOF, incremental hash expected, writing
   each returned chunk to destination at exact position with short-write loop.
   Each write returns1..remaining; zero/negative/NaN/oversize -> IO, no retry of
   failed operation. After full source hash equality, stat source again and
   count its second verified scan, then sync destination ONCE.
6. Stat source/manifest and re-identify all paths/root; scan manifest second
   time+EOF, hash expected, stat manifest again, count its second verified scan.
   Stat destination exactly expected exe bytes and
   original exclusive identity; scan destination twice+EOF, both hashes equal
   linked exe; stat after each. No source/copy alias, inode swap or size change.
7. Re-identify root/source/manifest/destination after scans. Close ALL captured
   handles ONCE in reverse acquisition order (copy,manifest,source), then final
   liveness check. Success only after all closes succeed. No reopen/delete.

EOF reads request length1 into same buffer and must return0. They do not add
reserved selected bytes; any positive EOF return is actual read evidence,
charged before CONTENT failure (ioUncertain false for a valid positive EOF).
A zero non-EOF read is IO with ioUncertain false (known premature EOF); zero
write is invalid, IO with ioUncertain true. Returned integer positive bytes are charged
BEFORE later cancellation/deadline/hash checks, even after stop; safe integer
positive oversize also charged then IO. Overflow actual counters -> IO. Invalid
byte counts or thrown read/write have unknown side effects; mark ioUncertain.
For positive oversize reported counts, do not hash/write outside buffer.
Actual selected counters may exceed reserves on a failing/lying adapter; never
erase/clamp evidence or claim success in that case. Accumulate actual read/write
internally as BigInt; normally expose safe nonnegative integer Numbers. If an
addition exceeds MAX_SAFE_INTEGER, retain its exact canonical decimal string
in that actual counter, mark ioUncertain and stop IO immediately. No overflow
rounding/truncation or BigInt in JSON; reservation/other counters stay Numbers.
Positive oversize and negative/NaN/noninteger counts are invalid/uncertain.
Production wrappers return
Node's bytesRead/bytesWritten, do not silently coerce/repair malformed responses.
All bytes physically written stay charged even if subsequent sync/hash fails.
One open attempt counted immediately before offer; opened increments when a
close-capable object is captured. closeAttempts/closed count successful close
or uncertain close once; unknownClosures count opens with missing usable close,
open failures or captured-close failures (including wx+ rejection/EEXIST; no
error-code inference of closure). Identity or expected-size mismatch -> IDENTITY;
expected hash mismatch -> CONTENT; malformed handle/byte operation -> IO.
Preserve first failure code through
cleanup/clock errors; only an otherwise good job becomes CLOSE after close
failure. Missing close marks unknown, other handles still close.
IO flags are independent: unknownClosure follows unknownClosures>0;
ioUncertain also covers thrown/invalid byte-return operations.

No errors/messages/paths/buffers/identity tokens in proof. Never forge a
coordinator receipt: this low-level result needs an actual port wrapper.

## Results

copyNext resolves detached deep-frozen proof exact keys:
version1,kind 'worker_artifact_preembed_copy_v1',candidate ('A'/'B' or null
for malformed/unoffered request),ok,code,executable,manifest,copy,io,
unknownClosure,ioUncertain,qualifiedfalse,linkQualificationfalse,
closureCompletefalse,requiresFreshAdmissiontrue,normalWorkerUnchangedRequiredtrue.
Success code null; three facts equal detached request facts (copy==exe).
Failure facts all null, code finite:
INPUT,CANCELLED,CLOCK,DEADLINE,IDENTITY,CONTENT,IO,CLOSE.
Filesystem throw outside close -> IO unless a more specific earlier failure.
Per-job io exact counters {reservedCopies,reservedReadBytes,reservedWriteBytes,
actualReadBytes,actualWriteBytes,openAttempts,opened,closeAttempts,closed,
unknownClosures,verifiedScans}. verifiedScans increments only after an entire
expected hash/stat scan: source first+second,manifest first+second,copy twice=6.
Cumulative snapshot exact {version:1,kind:'worker_artifact_preembed_copy_snapshot_v1',
nextCandidate:'A'/'B'/null,busy,stopped,io,unknownClosure,ioUncertain,
qualified:false,linkQualification:false,closureComplete:false,
requiresFreshAdmission:true,normalWorkerUnchangedRequired:true}.
Failure stops forever with nextCandidate null; successA advancesB; successB
terminal with next null.
Detached snapshots/proofs cannot change private counters or future jobs.

## Independent FIRST, source review and execution gate

Export runWorkerArtifactPreembedCopySelfchecksV1(api) from FIRST, API exact two
factory functions (do not use actual production factory in mock checks).
Exactly20groups P01..P20; success six-key summary version1,
kind 'worker_artifact_preembed_copy_first_v1',executed20,passed20,failed0,
failed_case_ids[]. Missing API -> UNRUN_SETUP, no invented RED.
Mocks only, each fixture<256KiB, no filesystem/process/tool/SDK/native/model/app
or real timers. Source review is not execution.

P01 exact factory/adapter/descriptor/getter refusal; P02 actual full A/B algorithm
trace+mode/closed paths/exact success facts and six scans; P03 source/manifest
pre-open hash refusal, no destination; P04 root/path/identity/ordinary/nlink seam
refusal and source/dest alias; P05 wrong sizes/hash/source mutation during second
scan leaves partial output retained; P06 destination exists/open reject, no
overwrite/fallback/delete; P07 short reads/writes and exact EOF; P08 zero/
negative/NaN/oversize returns and uncertain/actual counters; P09 sync/readback/
second-copy-scan failures preserve partial output; P10 all source/manifest/copy
open failures/malformed acquired handles and close capture before validation;
P11 each close failure, reverse cleanup, first cause retained, no retry;
P12 cancellation before/at await boundaries and positive late read/write charge;
P13 inclusive deadline/invalid/backward clock and late return; P14 concurrent/
consumed A/B/failed job refusal; P15 immutable captured config/adapter/request
and detached proof/snapshot; P16 worst-case reservation arithmetic with no large
allocation; P17 invalid/extra request args/wrong order stop without reservation;
P18 no filesystem or production factory invoked by mock runner, closed surface;
P19 actual counter/snapshot cumulative totals and no refund after failure;
P20 every path unqualified, no receipt/adoption/MT/deletion and bounded summaries.
Freeze FIRST before producer. Preserve all assertions; clarify contract FIRST
before targeted producer fixes. No code/syntax/import/FIRST/actual FS invocation
under current standing source authority. A later exact retained-program review,
full fresh inventory/reserve and finite owner decision is required for checks.
No run grant or cap increase follows from source review, this contract or merge.
