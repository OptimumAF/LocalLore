# Worker artifact Windows inputs v1: bounded real-filesystem component

Refs #25 D04.01/.02/.04; #31 D09.03/.05 supporting; #21.
Base accepted PR390/main a635686c. SOURCE ONLY / ALL NEW CHECKS UNRUN.
PR390's finite grant is SPENT. Current retained metadata cap2860KiB and every
other allowance/failure fence remain unchanged. This document grants no read,
fixture creation, code execution, native build or new source retention packet.

## Small effectful slice and unchanged owners

Prepare NEW `native/llama-worker/worker_artifact_windows_inputs_v1.mjs`: a real
Node filesystem adapter plus one bounded read core for ONLY the original
cohort32 component. This is not another metadata projection. It reads only a
trusted developer's frozen pin list, returns verified read-time bytes, and
retains bounded counters. It does NOT implement all14 admission checks, search
resolution/no-shadow, tool/environment freshness, source/header manifests,
exclusive output reservation, process launch, native qualification or Author
authority. A future `admit`/`recheck` must compose those separate proofs live;
this component cannot emit their all-true receipts by itself.

Derive the read core and concrete adapter from the accepted preserved SOURCE
`b2-msvc-profile-cohort-reader-v1.mjs`: `readPinnedInput`, `productionAdapter`,
`ordinary` and `signature`. That source was read as TEXT for this contract;
no SDK/input/report payload or hash was observed. Preserve the original private
collector, `library_inputs.mjs`, its job/parser/projection, accepted coordinator,
and `library_runtime_metadata_v2.mjs` unchanged. No binary parser is added.

The two runtime inputs stay in their SEPARATE accepted runtime observer/job.
The285588B `readPinnedArchiveV1` is NOT widened to read the large archives.
Do not collapse34 inputs into a32-input job, reset budgets, deduplicate equal
contents, relabel metadata-v2 as v1 or turn historical reports into fresh proof.

Root owns this contract, then the one new producer module. Independent authors
freeze mock FIRST and the separate optional Windows-filesystem FIRST below
BEFORE producer work, on serialized separate branches. Root integrates; no
concurrent shared checkout/Git mutation. No producer/FIRST file is created by
this contract-only change. No app, model, renderer, IPC or remote interface uses
these development-only functions.

## Closed spec and factories

Exports ONLY:

```javascript
createWorkerArtifactWindowsInputsV1(spec)
createWorkerArtifactWindowsInputsV1ForTesting(spec, adapter)
```

Production imports only Node builtin filesystem/crypto/performance facilities;
its concrete adapter uses `lstat`, `realpath`, `open`, held `stat/read/close` and
`performance.now`. No shell, environment selection, subprocess, downloads,
recursive enumeration, arbitrary reader callback or source evaluation.
The explicit ForTesting export is a trusted development seam for the SAME
core, never an alternate product reader. It accepts exactly three captured
own-data functions `identify`, `open`, `now`; production supplies them itself.

spec is an exact ordinary/null-prototype enumerable own-DATA record `{pins}`.
pins is a dense own-data array of1..32 exact records, in read order:

`{slot,kind,path,root,bytes,sha256,rootIdentity,leafIdentity}`.

slot=index+1. kind is project for slots1..17, sdk for18..32; a shorter list is
an explicit prefix, not a renumbered SDK-only list. project paths/roots must be
physically intended D: paths; sdk may name installed C: or D: data. The schema
does not itself prove physical location. Freeze/copy all data and function
values before any adapter invocation, including initial `now`. Never invoke
input getters; reject symbols, extras, inherited/sparse/boxed/coerced fields.
Caller mutations cannot replace pins, callback functions, counters or time.

Paths are primitive safe ASCII strings <=1024B, uppercase C:/ or D:/, forward
slashes, nonempty components <=255B; no root-only/trailing/duplicate slash,
dot/dotdot, trailing dot/space, controls/DEL, backslash/UNC/device/ADS, quote,
wildcard or `= , ; #` backtick `< > | &` syntax. Spaces and parentheses support
the existing installed roots and `clean build`. Reject reserved DOS component
stems con/prn/aux/nul/com1..9/lpt1..9, case-insensitively before the first dot
after removing trailing ASCII spaces. Non-ASCII paths, including superscript
device spellings, are outside this narrower component's scope and refuse.
path must lie strictly beneath root at a '/' component boundary; compare only
ASCII case-insensitively. Reject duplicate full path aliases under that same
comparison. Do not normalize/rewrite caller paths or accept dot aliases.

bytes is positive safe integer STRICTLY LESS THAN268435456B. sha256 is primitive
lowercase64hex. rootIdentity/leafIdentity are primitive ASCII tokens1..256B,
letters/digits/underscore/dot/colon/hyphen only; they bind the exact expected
recorded signatures. Actual filesystem signatures retain the accepted order
`dev:ino:size:mtimeNs:ctimeNs`, decimal String values joined by colons, no atime.
Synthetic tests may use synthetic tokens; they are not real-file provenance.

At construction require total declared bytes <=536870912 and twice that sum
<=1073741824; each individual and count limit is unchanged. Accept inclusive
total ceilings. Factory shape/path/identity/initial-clock failures throw ONLY
`WorkerArtifactWindowsInputsV1Invalid`; string/component/count/input-byte/job
byte excess throws `WorkerArtifactWindowsInputsV1Limit`. No I/O on setup failure.
Validate all descriptors/spec/limits before calling initial now. Initial now
must be finite nonnegative Number; fractional performance values are allowed.

## Private state, fixed reads and cancellation

Each factory returns frozen `{readNext,cancel,snapshot}`. No public state,
caller slot/path/size selection, reset, retry, mode or read budget override.
`readNext()` accepts ZERO arguments and consumes the next captured pin once.
It resolves ONLY `{buffer,proof}` after successful close/final hash validation;
the wrapper is frozen, but buffer is an explicitly mutable caller-owned Buffer.
It is not sealed, an Author capability, a durable canonical record, or a promise
that later caller-mutated bytes still match proof.sha256.

Private pending/poison state rejects concurrent readNext or unexpected arguments
as `InputSequence`; no second reservation or adapter call. The active read must
still charge known returned work and close its known handle. A critical failure
is sticky; subsequent reads reject its exact first code without I/O or refund.
Once all pins complete, further reads reject `InputSequence` WITHOUT changing
the completed snapshot. No additional job is silently constructed.

`cancel()` returns true once before complete/stopped, including before any read;
latches `InputCancelled`, and returns false thereafter. It starts no I/O and
does not skip cleanup or delete anything. A pending adapter call is not forcibly
interrupted; when it settles, the same core checks stop and closes any returned
known handle. An external bounded supervisor is still needed for a never-settled
filesystem promise; do not claim hard timeout/OS containment.

The fixed60000ms job clock starts at factory construction, not per input. now
must remain finite/nonnegative/monotone; a later backward/nonfinite/throwing
clock is `InputFailure`. Elapsed60000ms is accepted; greater is `InputDeadline`.
Check clock/poison around asynchronous work. Concrete adapter repeats the same
private guard between its internal filesystem awaits. Cleanup close is always
deadline/cancel-exempt. No real timer, sleep or clock override is added.

Per started read reserve1 input, pin.bytes and2*pin.bytes BEFORE filesystem
access/allocation; never refund. The admission snapshot counts reservations,
not falsely completed reads. Live guards may stop a reserved read with zero
actual bytes. A positive safe returned count <=requested length is charged to
actualReadBytes BEFORE a late cancellation/deadline/poison check. Zero,
overlong, malformed counts or throws stop `InputFailure`; never charge invented
counts. Keep actual<=reservedReadBytes and both fixed job limits.

## Accepted held-input protocol, concrete adapter and safe cleanup

For each captured pin, in this exact successful filesystem-method order:

`identify,open('r'),stat,(scan1 reads),stat,identify,(scan2 reads),stat,identify,close`.

identify returns exact `{path,root,leaf,bytes}`. Require its path/size and BOTH
root/leaf signatures equal the captured pin, not merely before/after agreement.
This is an explicit strengthening of the NEW extraction: the preserved old
core checked path/size and later agreement, while its old production adapter
pre-pinned only SDK roots. The old source is not changed or described as having
performed these new expected root/leaf checks for every project/SDK input.
open receives only that captured pin and literal'r'. Held wrapper has exact
own-data stat/read/close functions. stat returns exact `{leaf,bytes}` matching
the pin/before identity. Compare complete before/after identity records.

Before checking liveness or validating any returned handle's other methods,
capture a known own-DATA close function WITHOUT invoking getters. An objectlike
returned handle counts as known opened, even if its stat/read shape is invalid.
If close is safely available, make ONE close attempt in finally, including
malformed wrappers and late cancellation. Missing/accessor close or close
rejection poisons the job; report unknown closure, never a false closed count.
Preserve a prior Identity/Input/Sequence/Cancelled/Deadline cause if cleanup
also fails. Never retry close, reopen or continue with another pin.
After cleanup, check live clock/poison once more before returning proof or
advancing the successful prefix. Cancellation/deadline during a successful
close still stops without another close; retain the confirmed closed count.

One read-only handle per pin. First full scan fills ONE pin-sized Buffer;
second scan independently hashes the SAME handle using <=65536B scratch space.
Both use explicit positions, requests <=65536B, positive short-read support,
and must independently equal expected SHA256. Check held stat and full path/
root/leaf identity after EACH scan. After the one close, hash the retained
first Buffer again before returning proof; this final in-memory check does not
add a filesystem scan. No parser, mutation, normalization or third file scan.

Concrete identify checks only the captured root and leaf using Node lstat:
ordinary directory/file, !isSymbolicLink, and realpath equal to the supplied
path after slash conversion and ASCII case comparison. Require expected root
and leaf signatures and exact size. Concrete held stat also requires isFile.
Concrete reads validate Buffer/offset/length/position against pin.bytes before
calling FileHandle.read. Always return known actual bytes to the core before
post-await stop checks. Do not add an after-open guard that loses the returned
handle before core cleanup can capture it.

These checks are COOPERATIVE observations, not Windows share-mode locking,
root-to-leaf opened-handle proof, hardlink uniqueness, every reparse-tag audit,
Unicode/8.3 alias qualification, no-shadow proof or protection against concurrent
OS actors. Equal signatures/hashes do not establish physical disjointness.
Do not label a source-reviewed Node adapter a completed Windows admission gate.

## Closed proof/snapshot, counters and conservation

Operation errors ONLY InputFailure,IdentityFailure,InputSequence,InputCancelled,
InputDeadline. IdentityFailure covers expected/path/held/hash disagreement;
InputFailure covers other I/O/wrapper/read/close/clock failures. No raw OS/error
message, path, filename or identity signature is copied to proof/snapshot/error.
Factory Invalid/Limit remain separate as above; first operation error wins.

Proof exact keys/order version,kind,slot,role,bytes,sha256,pinHash,identityHash,io,
qualified,linkQualification,closureComplete,requiresFreshAdmission. version1,
kind worker_artifact_windows_input_v1, role project/sdk. pinHash hashes the
copied pin's exact JSON key order above; identityHash hashes `{root,leaf,bytes}`
in that order. No raw paths/root/leaf signatures in either public tree.
io has exact keys reservedInputs,reservedBytes,reservedReadBytes,actualReadBytes,
openAttempts,opened,closeAttempts,closed,verifiedScans,unknownClosures.
Successful proof values are1,n,2n,2n,1,1,1,1,2,0. All qualification flags false;
requiresFreshAdmission=true. Deep-freeze detached proof DATA, not buffer.

snapshot exact keys/order version,kind,purpose,status,pinCount,nextIndex,
pendingIndex,completedInputs,io,lastProof,critical,cancelRequested,qualified,
linkQualification,closureComplete,requiresFreshAdmission. version1,
kind worker_artifact_windows_inputs_snapshot_v1, purpose bounded_build_input_read_only;
status ready/pending/stopped/complete. nextIndex/completedInputs count the
successful prefix; pendingIndex is its zero-based active index or null.
While an operation is still unsettled, status remains pending even after a
critical stop was latched; critical exposes that cause. Only after settlement
does it become stopped. Otherwise complete takes precedence over ready.
lastProof is the last successful detached proof or null, never a failed read
masquerading as success. critical null or first code. snapshot is detached,
deep-frozen, JSON UTF8<=4096B; proof JSON<=2048B. No whole pin roster is emitted.

Snapshot io totals all known work, including failed/pending reads. openAttempts
increments before offering open; opened counts objectlike returned handles;
closeAttempts increments before known cleanup; closed ONLY after success.
verifiedScans increments after each matching full scan. Unknown closure is
zero for a settled successful read; if a terminal failed open attempt has no
confirmed close (including open throw/null/missing close), unknownClosures=1
for that attempt, even without a known handle. During an unsettled open/read,
outstanding work is marked pending, not falsely classified settled/closed.
No later pin after unknown closure. Conservation: completed<=reserved<=pinCount,
actual<=reservedRead=2*reservedBytes, closed<=closeAttempts<=opened<=openAttempts,
verifiedScans<=2*reservedInputs. No refund/reset after failure or cancellation.

## Independent FIRST, then a separately admitted Windows filesystem check

Mock FIRST is NEW `worker_artifact_windows_inputs_v1_first.mjs`, exporting
`runWorkerArtifactWindowsInputsSelfchecksV1(api)` with exact one-field API
`{createWorkerArtifactWindowsInputsV1ForTesting}`. Exactly24 groups W01..W24;
six-key summary version,kind,executed,passed,failed,failed_case_ids, version1,
kind worker_artifact_windows_inputs_first_v1,24/24/0/[] as sole successful gate.
Missing factory is UNRUN_SETUP, never a passing behavioral RED.

W01 exact spec/pin/adapter shapes/no getters; W02 dense/prefix roles and captured
pins/functions; W03 canonical path/containment/duplicate aliases; W04 first
successful complete trace/proof; W05 sequential two-input conservation;
W06 positive short reads/positions; W07 chunk/scratch independent second scan;
W08 first SHA mismatch; W09 second SHA mismatch; W10 root/leaf/path drift;
W11 held stat/type/size disagreement; W12 zero/overlong/malformed read counts;
W13 identify/open/stat/read throw without payload leak; W14 one close and
close-only failure/unknown accounting; W15 first cause preserved if close also
fails; W16 safe close capture before late stop/bad methods/no getters;
W17 cancel before read and pending identify/open/read; W18 concurrent poisoning
and returned positive-byte charge; W19 final retained-buffer hash/isolation;
W20 frozen private-path-free snapshots/proofs; W21 no caller path/slot/args or
reset/retry and post-terminal no I/O; W22 per-input/count limits inclusive and
+1 refusal; W23 declared512MiB/1GiB inclusive and+1 using only small pin records,
NO payload allocations/reads or claim actual512MiB work; W24 monotone/fractional
clock,60000/+1 deadline, late positive-byte charge and cleanup exemption.
Specify independent expected traces, counts and partial statuses before producer.
Mock buffers/fixtures<2MiB/group; no actual memory/RSS claim or real timers.

Separate NEW `worker_artifact_windows_inputs_v1_native_first.mjs` later exports
`runWorkerArtifactWindowsInputsNativeSelfchecksV1(api,fixtureSpec)`, API exact
`{createWorkerArtifactWindowsInputsV1}`. TWO groups N01/N02, six-key summary
kind worker_artifact_windows_inputs_native_first_v1, version1,2/2/0/[] required.
The fixed private launcher, not this library, must separately admit/create and
pin ONE tiny original synthetic D: file/root before tests, under the unchanged
8MiB fixture allowance. fixtureSpec exact `{pin}` for slot1/project, with the
known original UTF8 payload `LocalLoreWindowsInputFixtureV1\n` and its actual
ordinary root/leaf signatures. No caller-selected SDK/private story fixture.

N01 uses production factory and two actual held-file scans; compare returned
bytes to the independent fixed payload, expected proof/hash and closed counts.
N02 uses a SECOND explicitly admitted factory/job on that SAME file/pin with
only expected SHA's first hex digit toggled; first-scan IdentityFailure, actual
bytes n, reserved2n, verified0, one confirmed close, no second scan/Buffer return.
This is actual Windows Node-filesystem evidence only when run there, NOT a
compiler/native IPC/model/WebView/reparse/hardlink/no-shadow qualification.
No fixture creation/read or either native group has occurred for this plan.

All new code/Windows filesystem/SDK/header/tool observations remain UNRUN until
exact programs/source hashes, retained source/reviews, fresh storage/full reserves
and separate finite owner authority exist. Preserve all historical failures,
outputs and original limits. No automatic retry, new evidence root, deletion,
build/link/MT/worker/model/app/device/OS qualification, download/settings/release
or desktop control. Full D04/D09/desktop gates stay open; AuthorDisabled.
