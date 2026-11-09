# D04 worker artifact output roots v1

Refs #25 (D04.01/.02/.04 prerequisite), #31 (D09.03/.05 prerequisite), #21.
The [accepted recipe](../../native/llama-worker/worker_artifact_recipe_v1.mjs)
owns the fixed candidate paths. This helper creates and observes just those
two directories under the recipe's existing target parent. It neither starts a
build nor makes any artifact, closure, runtime, model or packaging qualified.

## Caller boundary

This is a cooperative lease for one independently admitted private target
parent on physical D:. Before calling it, the future owner must establish
physical storage, same-attempt authority, root absence, no other writers,
known process closure, fresh remaining bytes in the existing 64 MiB group
limit, and a reservation for all new writes. This helper does not discover
these facts. Between observations only the admitted owner may write. During
prepare/recheck no writer may be live. The wrapper must keep ownership while
an operation or child remains unsettled, including after a caller-side
deadline. No coordinator port is wired in this slice. A successful roster is
a point observation of logical file lengths, not a file lock, sandbox,
physical disk quota, atomic snapshot or approval to launch a child. The future coordinator must establish
admission prerequisites before mutating prepare, then use its result as
one additional observation before allowing any child. It
excludes prior retained output and output elsewhere, including compiler temp
files, streams and descendant writes; the owner must account for those
separately. It does not establish expected stage files, freshness, hashes,
PE identity or that a file stopped changing outside the owner contract.

## Interface

`createWorkerArtifactOutputRootsV1({config, attemptSha256, parentIdentity, maxBytes})`
is synchronous, Windows-only and performs no I/O. The testing export
`createWorkerArtifactOutputRootsV1ForTesting(spec, adapter)` uses the same
core. Specs and adapter records have exact enumerable own data fields on an
ordinary or null-prototype record; no getters, extras or symbols. The
accepted recipe validates `config`; the parent and two output roots are
derived from its returned paths. `attemptSha256` is exactly 64 lowercase hex
digits and not all zero; the owner binds it to a real admission record later. The recipe
digest is SHA-256 of its UTF-8 `JSON.stringify(recipe)` in returned field
order. Identity tokens are canonical unsigned decimal `dev:ino` (two
uint64s, nonzero ino, at most 41 characters). All root and file
identities must use the same dev as the parent. `maxBytes` is an integer in 1..67108864; the helper
never treats that whole ceiling as newly available evidence space.
Invalid construction throws `WorkerArtifactOutputRootsV1Input`; production
on a non-Windows host throws `WorkerArtifactOutputRootsV1Platform`.

The factory returns frozen `{prepare,recheck,cancel,close,snapshot}`. Each
method takes no arguments. `prepare`, `recheck` and `close` are async and
return the same snapshot shape as `snapshot()`; operational failures settle
with a stopped snapshot. `cancel()` returns a snapshot synchronously, latches
`Cancelled` if no earlier failure, and starts no I/O. The states are
`New`, `Ready`, `Stopped`, `Closed`. While prepare runs the underlying
state stays New until success, and while recheck runs it stays Ready until
success or stop. A latched stop changes the state to Stopped immediately,
even during pending close, until explicit close settles in Closed. Closed
means the lease cannot be used again; it does not prove known closure. `pending` is `prepare`, `recheck`, `close` or null.
Only prepare from New and recheck from Ready are legal; limit 32 started
rechecks per lease (attempt 33 latches `Limit`, no I/O). Concurrent
prepare/recheck/close reject `WorkerArtifactOutputRootsV1Busy` and invalid
state/arguments reject `WorkerArtifactOutputRootsV1State` without changing
the lease. Close is legal after settlement in any state and idempotent once
Closed. Cancellation after Closed does not alter the result. Supplying
arguments to cancel/snapshot throws the same State error.

Each prepare/recheck has a monotonic 4000 ms cooperative budget (elapsed
`>=4000` refuses); invalid/nonfinite/negative/retrograde clock stops. Check
before every ordinary I/O await and after the result, and between native
adapter substeps. No timeout races, forced promise resolution or retries.
Latch the first known failure and never replace it with cleanup failure.
Capture known side effects and own close functions **before** post-await
checks. Pending work remains pending until actual settlement. On recheck or
prepare refusal, marker handles remain owned until explicit close. Transient
directory streams close once in their scan's cleanup. Explicit close tries
each captured marker close exactly once, B then A, regardless of cancellation,
time or other close failure; close is deliberately not a false hard deadline.
A rejected/missing close is unknown, never retried or claimed closed.
For transient stream cleanup check liveness before and after close without
skipping it; a close rejection already known on resumption is recorded
before the post-close clock observation. Explicit close ignores the clock.

## Fixed operations

- Prepare first checks that two full markers fit. Confirm the expected
  parent identity before and after each exclusive nonrecursive mkdir, in
  order A then B. A known existing root refuses; never adopt it. Bind the
  new ordinary directory's identity (different from the parent and the other
  root); verify root and parent around later operations. A generic failed
  mkdir does not establish absence. Once A is created, B failure does not
  remove A. No deletion, renaming, overwrite, recreation or fallback path.
- In each new root open only `.locallore-output-owner-v1` using `wx+`.
  Its exact bytes are ASCII
  `locallore-worker-artifact-owner-v1\n<attemptSha256>\n<recipeSha256>\n<A or B>\n`
  (literal LF, no BOM). Require a new zero-length ordinary file, with identity distinct from the
  parent, bound roots and other marker; compare held and named identity, write with bounded positive short-write progress,
  sync, and read back the exact bytes. A partial marker is preserved. Named
  and held checks bracket each marker verification: equal identity, exact
  length, byte equality and zero-byte EOF probe. For each verification read only
  this marker's expected length plus one EOF probe byte; no other file payload reads.
- After both markers, prepare scans A then B; each must contain exactly its
  marker. Recheck likewise observes both roots. Both passes verify the
  marker before and after each scan. Assert the same parent and each candidate
  directory identity at scan start/end and before each pathname stat.
  Use a manual nonrecursive directory stream; at most nine reads per root
  (eight allowed names plus EOF), buffer size one in production. The only
  accepted direct files are marker plus the seven recipe leaves: object,
  executable, pre-embed copy, manifest, compiler PDB, linker PDB and import
  library. Unlisted compiler sidecars, subdirectories, alias names, repeated
  names and malformed entries refuse; the helper does not join or stat
  unknown names. Require each directory entry itself to indicate a file,
  as well as the pathname check below. For each accepted name require an ordinary one-link file and unique
  identity across both rosters. The marker path must match the held marker.
  A roster with no marker refuses. Use exact BigInt arithmetic on uint64
  lengths. Stop as soon as a known aggregate length exceeds maxBytes; retain
  the full observed lower bound, including the crossing file, and keep the
  current roster incomplete unless EOF and all postchecks succeeded. A
  failed read/stat, unknown remainder or unknown closure never qualifies
  storage. No recursive fallback.

## Adapter and evidence

The test adapter has exactly `{identify,mkdir,openMarker,openDirectory,now}`.
Capture each function once at construction; methods need no bound receiver.
`identify(path,kind)` returns an exact own-data
`{identity,bytes,ordinary,real}`, with kind `directory` or `file`,
BigInt uint64 bytes, and ordinary/real booleans. A file fact is valid only
for the expected direct pathname, ordinary kind, and matching real path.
`mkdir(path)` returns `created` or `exists`. The marker handle exposes own
data methods `identity()` (same fact without real), `read(buffer,offset,length,position)`,
`write(buffer,offset,length,position)`, `sync()` and `close()`. Read/write
return byte counts; sync/close fulfill without a value. The directory handle
exposes own `read()` returning an exact own-data `{name,ordinary}` record
or null (EOF), and `close()`.
Handle methods use the captured handle as receiver and may be nonenumerable.
Acquire and record a callable own close even when another method is malformed;
missing close is unknown. Treat thrown adapter values as opaque I/O failure
(no error inspection or leaked paths). Only the native mkdir wrapper maps
known EEXIST; all other operations use the normal failure path.

The production adapter uses Node Windows `lstat`, `realpath`, `mkdir`,
`open`, FileHandle operations and manual `opendir` reads/close. It requires
ordinary, non-symbolic paths with physical spelling matches (normalize backslashes to slashes and fold
ASCII A–Z only),
nonzero ino and one-link file checks. This is cooperative pathname evidence,
not directory-relative open, arbitrary reparse-tag inspection, ACL isolation,
or a defense against an adversarial concurrent namespace. The pinned Windows
libuv [enumeration implementation](https://github.com/nodejs/node/blob/v24.22.1/deps/uv/src/win/fs.c#L1562)
classifies reported reparse entries as links; this does not make parent/root
`lstat` a complete reparse-tag check. See the pinned
[Node v24.22.1 filesystem API](https://nodejs.org/download/release/v24.22.1/docs/api/fs.html).
No commands, arbitrary paths, process execution, SDK access or product API.

Snapshots are deeply frozen and contain only
`{version:1,kind:'worker_artifact_output_roots_v1',qualified:false,state,pending,stop,
rechecks,withinBudget,observedBytes,roots}`. `stop` is null or one of
`Cancelled, Deadline, Clock, Limit, Exists, Identity, Marker, Roster, Budget,
IO, Closure`. `observedBytes` is the decimal lower bound for the latest
started scan pass, never a JS number. `withinBudget` is true only in Ready
with no pending work and two complete rosters. Each ordered root row is
`{candidate,creation,identity,marker,markerClosure,directoryClosure,
complete,files}`; `creation` is `unattempted, unknown, created, exists`,
`identity` is the bound directory token or null, `marker` is
`unattempted, unknown, created`. Closure is `none, open, closed, unknown`;
a directory close rejection does not erase a prior failure. `complete`
requires EOF, marker, known stream closure, and matching postchecks. Files are reported in recipe order (marker first) as
`{name,identity,bytes}` using allowlisted names, opaque identity tokens and
decimal strings. Per-file facts in a stopped/incomplete pass are diagnostics,
not a proof for the copy helper. A stopped pre-scan attempt may report zero
observed bytes even after a write; the owner must retain and charge its
reserved bytes until complete external accounting, without assuming absence. Reset pass observations at prepare/recheck
start, preserve them across failure and close. No result exposes the
absolute paths, marker payload, raw exceptions, or process/run authority.

## Verification boundary

Independent FIRST freezes the synthetic assertion groups before the
producer. Coverage includes exact happy prepare/recheck, existing/partial
root preservation, marker readback and identity mismatch, unknown entries,
budget/overflow, close ordering/first cause and delayed I/O/cancellation.
Source review is not execution. No actual Windows output-root creation,
worker copy, compile/link/MT, native app, model, Android/device, release or
full desktop acceptance is claimed by this helper. Actual checks need a
separate retained-evidence admission.
