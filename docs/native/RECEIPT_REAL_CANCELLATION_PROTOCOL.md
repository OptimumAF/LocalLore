# Real receipt sampled-cancellation and process recovery — v1

Refs #9 (M05.05 / M01.05 prerequisite). This packet tests the real public gateway
cancellation path, then recovery in another target process and no-SDK canonical
reopen in a third. It adds no provider, artificial callback, SDK delay, model
replacement, retry, owner reset, or weaker schema. Authored fixture code is not
device qualification; actual source/APK/controller review and admission remain
separate coordinator gates.

## Selection, phases and ownership

Each class has exactly one test and refuses normal package discovery before
accessing Context/storage. Instrumentation's `class` argument must equal the
exact class name, without a method suffix. The coordinator selects each
separately with the ordinary runner and verifies terminal cleanup/process
boundaries. All three classes are in `org.locallore.app`:

| Phase | Class / method | App phase cap |
| --- | --- | ---: |
| CANCEL | `ReceiptRealCancelTest#cancelsSampledPublicInferenceWithoutCommit` | 170000 ms |
| RECOVER | `ReceiptRealRecoverTest#recoversCancelledWorkspaceAndCommitsOneRealGift` | 170000 ms |
| REOPEN | `ReceiptRealCancelReopenTest#reopensRecoveredReceiptWithoutSdk` | 120000 ms |

The existing source-preflight/import phases run first. Their
`receipt-real-proof-v1` family remains exactly its two JSON files and two empty
readiness files; none is rewritten. The new family is only the fixed Context
no-backup child `receipt-cancel-proof-v1`. New tests use the existing typed PLAY
or REOPEN deadline solely to reuse its unchanged 170/120-second cap. They never
invoke an old PLAY/REOPEN class selector or old proof writer.

The controller's 870-second aggregate, 900-second owned wrapper, 920-second
candidate entry, SDK 60-second turn/five-second cleanup and environment lifetime
remain unchanged. Per-phase maxima do not promise that all worst cases fit the
aggregate. No action can continue after uncertainty merely because another
timer has remaining time.

## Actual cancellation operation

Gateway state is Main-confined. An explicitly owned independent
`SupervisorJob + Dispatchers.Main.immediate` scope starts the original
`gateway.respondText` task; returning a Deferred from a `withContext` child
scope would incorrectly wait for generation. The test observer checks Main
entry and delegates directly to production `NativeWorkspaceTransport.exchange`.
It does not insert an IO wrapper to hide a broken production handoff. The
production transport/worker guards themselves enforce native work off Main.

The native handle is captured before starting the turn. Passive bounded trace
polling requires one returned DIRECTOR creation, one entered/returned send,
at least one MESSAGE_RETURNED, no observed DONE/ERROR/CANCEL entry, no engine
close entry, no uncertainty notification, and the original Deferred still
active. Any already-ended/missed window fails the sole attempt. This is a
**sampled public-inflight** observation, not an atomic native-active instant,
duration inside JNI, guarantee cancellation caused termination, or health
proof. No prompt, schema body or generated text is retained.

On Main, the test invokes actual `gateway.cancelSaved()` exactly once. It then
awaits the original response without cancelling its Job and requires the actual
`DemoResult.Rejected("Cancelled")`. An acknowledgement or `isCompleted` flag is
insufficient. Native cancellation commands may be idempotently repeated by the
production owner; only the foreground method call and actual SDK trace counts
are required to equal one. There is no early join, skipped snapshot, retry or
replacement native response to hide a production cancellation failure.

After original response cleanup returns, the test requires the frozen cancel,
drain, conversation-close and engine-close observations. A post-join
`actual.forkHandle()` must pass the original active/poison guard and return the
captured handle; it does not create another SDK call. Only then may the test
inspect canonical state and rehash the accepted model. Both pre/post snapshots
must have revision zero, no receipts, and the player's potion quantity one.
No Prepared result or commit call is permitted. Closing the gateway and the
existing InvalidHandle check establish the app's finite native-handle boundary.

Failure cleanup closes only that gateway and boundedly observes the original
Deferred; it never cancels an unreturned task as proof of drain. Only a completed
original permits disposal of the otherwise empty supervisor scope. An unknown
task/owner fails the method, retains the uncertainty, and emits no positive proof.
The existing worker failure reporter preserves the original exception and may
emit one closed v2 diagnostic per process on CANCEL/RECOVER. That failure status
is distinct from positive trace sidecars and never counts as a pass.

## Recovery and reopen

RECOVER requires a different `(pid, start)` pair from CANCEL, reads the exact
prior proof/trace hashes, and resumes existing canonical state with automatic
story creation disabled. It requires revision zero, zero receipts and potion
quantity one before a single real SDK gift attempt. It preserves every required
director/repair/narrator schema and fresh conversation. Only actual Prepared
after known worker closure permits commit. The accepted result must be revision
one, the single compiled potion transfer to Mira and one receipt. The accepted
model is fully rechecked and its runtime admission retained.

REOPEN requires another different `(pid, start)` pair, production setup READY,
a full accepted-model check, and the exact recovered canonical receipt SHA.
It makes no free-text or commit call and initializes no SDK engine. Source
streams are not resolved/opened in any of these three new classes; their six
source counts remain zero. PID reuse with a changed start is permitted. No
in-process owner/quarantine reset substitutes for either process boundary.

## Closed proof format

`CancellationProof` is an org.json-free pure Kotlin encoder. Its only strings
are closed enum/check names and validated lowercase 64-hex SHA-256 values. It
receives no Throwable, IO object, provider, callback, path, prompt or arbitrary
extra-field map. Identity/capacity values are bounded integers; Boolean values
cannot stand in for integer parameters. Check maps must equal the phase's exact
set, all true, and are defensively copied/immutable. Encoding is canonical
sorted-key printable ASCII JSON, at most 4096 bytes, with no newline.

All phases use exactly the existing real-proof common keys:

```text
version, phase, pid, start, uid, process, model_bytes, model_sha256,
source_verify_opened, source_verify_closed, source_verify_bytes,
source_import_opened, source_import_closed, source_import_bytes,
sdk_invoked, publication_native_invoked, elapsed_ms,
userdata_free_before, userdata_free_after, external_free_before,
external_free_after, memory_total_bytes, memory_available_before,
memory_available_after, checks
```

Version is 1. Process/model identity are the existing fixed candidate constants.
All six source counts are zero, native publication is false, SDK invoked is true
only for CANCEL/RECOVER. Unchanged floors are userdata 1 GiB + 128 MiB,
external runtime 2 GiB, total guest RAM 7–8 GiB and initial available RAM at least
4 GiB; final available RAM is an observation in `0..total`. Every proof adds
`prior_pid`, `prior_start`, `revision`, `receipt_count`, plus:

| Phase | Prior link | Other exact extra fields |
| --- | --- | --- |
| CANCEL | `prior_import_sha256` | `sample_worker_trace_sha256`, `worker_trace_sha256` |
| RECOVER | `prior_cancel_sha256` | `receipt_sha256`, `repairs`, `fallback`, `worker_trace_sha256` |
| REOPEN | `prior_recover_sha256` | `receipt_sha256` |

CANCEL revision/count are zero; RECOVER/REOPEN are one. CANCEL carries no
invented empty receipt hash. `repairs` is 0 or 1 and fallback is the actual
Boolean from the accepted recovered receipt. The prior chain and all fixed
values are re-encoded on reads to refuse unknown/coerced/duplicate JSON fields.
Exact check sets are declared in `CancellationPhase`: CANCEL21, RECOVER19,
REOPEN14, totaling54 new checks. No check becomes authority independently of
the signed source, actual selected ordinary method PASS and coordinator gates.

## Progressive files and worker traces

Every JSON/sidecar is a regular, nonlinked, own-UID fixed file of 1–4096 bytes;
readiness files are exactly zero bytes. Writes use CREATE_NEW/NOFOLLOW, complete
writes and force, with readiness created after the proof closes. Existing files
are never overwritten. Failure retains partial/new files. Root whitelists are:

* After CANCEL: `cancel-v1.json`, `cancel-ready-v1.txt`,
  `cancel-sample-worker-v2.json`, `cancel-worker-v2.json` (4 files).
* After RECOVER: those four plus `recover-v1.json`, `recover-ready-v1.txt`,
  `recover-worker-v2.json` (7 files).
* After REOPEN: those seven plus `reopen-v1.json`, `reopen-ready-v1.txt` (9 files).

The sample/final snapshots are copied in memory and written only after the
method's success assertions. Their exact SHA values appear in the phase proof;
host parsing independently enforces closed worker v2 shape and these frozen
positive predicates, with all saturation sets/flags empty/false:

* Sample: one returned DIRECTOR creation with failure NONE; send entered and
  returned one; MESSAGE_RETURNED at least one; DONE_ENTERED, ERROR_ENTERED,
  CANCEL_ENTERED, ENGINE_CLOSE_ENTERED and UNCERTAIN zero.
* CANCEL final: matching returned creation; send and cancel entered/returned,
  DRAIN_SETTLED, conversation-close entered/known and engine-close entered/known
  all one; UNCERTAIN zero. Exactly one paired DONE terminal and no ERROR, or
  one paired ERROR terminal and no DONE. The final snapshot time, every event
  count and every previously nonnull event timestamp must not decrease from
  the sample; the first already-returned creation record must match exactly.
  These are consistency requirements for one trace object's history, not
  native-state or atomic-cancellation claims. MESSAGE_RETURNED does not decrease
  from the sample. Either terminal can race after sampling; no causal native
  cancellation claim is inferred.
* RECOVER: two roles `[DIRECTOR,NARRATOR]` or three
  `[DIRECTOR,DIRECTOR,NARRATOR]`, all returned/failure NONE. Creation/send/DONE/
  drain/conversation-close entered/known counts equal the number of creations;
  ERROR/CANCEL/UNCERTAIN are zero; engine close entered/known one and returned
  message count positive.

These are recording-point observations. They do not reveal hidden native
epilogues, make callback/state snapshots jointly atomic, or independently prove
resource reclamation. The actual response result, post-join production guard,
canonical checks, full model verification and selected-method PASS remain
separate required evidence.

## Verification boundary

Pure JVM cases cover closed phase/check cardinalities, immutable copies,
phase-specific keys/flags, exact hashes/privacy, invalid identity/timing/capacity,
PID reuse versus unchanged identity, bounded deterministic ASCII output, and no
callback/Throwable/IO input API. The source author runs no Gradle/JVM/SDK/device/
model operations. Central compilation, tests, APK/source binding, independent
review and any separately admitted actual cancellation/recovery run remain
pending; no acceptance or cleanup result is claimed by this document.

Source review at the author base `b23f100b8c91b1c09a69b362043ffa727f98d100`
also identified a production ordering risk: `cancelSaved()` acknowledges cancel
and immediately calls `snapshot()`, whose `open`/`branches` operations may run
while `LocalInferenceOwner.active` still excludes them. The coordinator owns
reproduction and any narrow production fix. This fixture neither retries nor
skips that public call, and no successful cancellation result is inferred from
the source review.
