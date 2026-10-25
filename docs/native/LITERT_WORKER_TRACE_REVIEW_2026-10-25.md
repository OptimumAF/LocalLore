# Independent bounded worker-observation review — 2026-10-25

Refs #9 (M05.05 prerequisite), #5 (M01.05 supporting).

## Disposition

Source and independently replayed host evidence reveal no remaining concrete
blocker after the corrections below. No new device/model experiment has run in
this packet. This observation code does not diagnose the previous
`LocalInferenceUncertain`, qualify SDK entry/generation/cleanup, or complete
PLAY/restart or either full milestone.

Review claim6394907548 is under root6394899896. The separate branch
`review/m05-worker-stage-observation` starts at main
`0c12413ed0d236e5b74e8626e434b0f074c3cdfc`; prior review branches are preserved.
Only this new report is owned. Reviewer makes no SDK/ADB/AVD/build/model/cache
operation or model-byte read/copy. Source, retained host evidence and metadata
inspection remain distinct from coordinator-attributed original tool terminals.

## Source and privacy boundaries

The final internal trace accepts only a closed thirty-event enum. Fixed arrays
hold counters capped at1,000,000 and overflow-only saturation flags. Synchronized
snapshots own immutable defensive copies; serialization contains only finite
ASCII keys/names, integers and flags. Prefix plus JSON is bounded to4096 bytes.
There is no arbitrary string, Throwable, callback/provider, identifier, path,
prompt, response or filesystem input. The trace itself performs no IO/status
delivery and grants no storage, inference, cancellation or ownership authority.

The optional parameter follows the same default worker/resource path; it does
not replace the SDK with a test provider. Existing60-second turn/5-second
cleanup, admission, quarantine, retained-resource and canonical gates remain.
The LF-normalized worker SHA-256 independently computes
`aaf476a9ad3928c0a21168c0949776abbcf876bcbb20180ba4da82eae067db29`, matching
the reviewed build pin and Candidate constant/manifest. SDK/model/version and
budgets are unchanged; this is new source provenance, not a new runtime choice.

Counts identify historical recording points, not a lifecycle validator:

- `*_ENTERED` usually records a reached pre-call site, not acknowledged native
  callee entry. `*_RETURNED` identifies the corresponding source point after a
  call; callback body exits can include caught failure and exclude JNI epilogues.
- `DRAIN_SETTLED` records an internal settled branch; prompt cancellation can
  prevent delivery of a successful suspend return.
- `CLOSE_KNOWN` is a historical checked public-return gate, not current ownership,
  caller delivery or hidden native reclamation.
- `UNCERTAIN` counts poisoned notifications after the existing synchronous fence,
  potentially repeatedly. Zero never proves health or complete coverage.

The fixture's single companion reporter claims its emission slot once and emits
only on failure, before the existing catch/finally teardown. It preserves the identical original Throwable
even if snapshot/encoding/send fails. The existing Prepared assertion now sits
inside the reporter so a non-Prepared return also yields an observation; no
retry, forced success, extra SDK probe or failure-path file/model read is added.

The passive Python decoder enforces closed keys, exact integer types/ranges,
duplicate/nonfinite rejection, bounded ASCII, known unique saturation entries
and strict single1337 framing. It performs no cross-counter inference. PLAY
owns the worker channel; other phases only forbid its key and leave the existing
setup-failure1337 channel to its original parser. Persistence is create-only and
any failure propagates. Raw evidence precedes parsing, and the original strict
runner/proof gates remain the only phase-success gates.

## Concrete findings corrected before final qualification

1. Callback entry tracing initially preceded the original counted-callback
   registration. It now counts/fences first, preserving the safety-first ordering
   before a possibly contended trace monitor.
2. `DRAIN_RETURNED` misleadingly described an internal settled branch. It is now
   `DRAIN_SETTLED`, with explicit cancellation/return-delivery limits.
3. Direct engine-close failure originally bypassed the traced unknown path.
   Recording now follows the original synchronous notification/fence, including
   that path; counts are notifications rather than unique poison transitions.
4. A privacy assertion inside the intentionally swallowed send closure could
   falsely pass. The test now captures JSON and checks it outside the catch path.
5. The integration regression now exercises direct engine-close-false and checks
   that fencing precedes the uncertainty observation. Normal non-Prepared results
   are also inside the reporter, rather than silently losing that failure trace.

These fixes preserve the existing error/resource outcome; observations cannot
clear quarantine or make a late return safe.

## Independently checked host evidence

The pure trace author supplies eleven source-level JVM tests covering exact
vocabulary/order/wire, immutable maps/sets/entries, invalid values, overflow,
maximum payload and concurrent recording/snapshot. Source authorship is not
execution. The parser author attributes twelve targeted Python tests to an
actual0.053-second pass; these remain separate from coordinator full-suite runs.

Independent retained XML/raw replay checks the first receipt build:384 tests /
38 suites, zero failures/errors/skips; known completion320,094 ms, raw10,678B
SHA-256 `fa17215b833affc35da90e55c92a13dc48a2f17fb179d7f41ec39a4c793635af`.
That pass precedes the final test-oracle/engine-false/assertion corrections.

The corrected receipt build independently has385 tests /38 suites, zero F/E/S:
worker suite35, pure trace11, reporter2. Raw9,644B SHA-256
`2431fb4894b7fab3ccd3149185201f001dc842d2e705983ae70aa4d6aa3b8fd3`
matches completed zero/known cleanup90,750 ms; lint records zero errors and19
warnings. The new worker regressions cover
blocked admission/construction/initialization/send, callback body drain, failed
close, cancellation and late initialization that must not clear quarantine.
These use synthetic resources and do not execute the actual model/SDK.

The initial full host raw80,486B SHA-256
`9fd7af10259a5456921774971eed87ffea06566ea7b0b9b9fbe3187ba5e6fb18`
matches completed zero/known cleanup71,766 ms and683PASS/69.818 seconds. The
final full run with actual APK pins is683PASS/66.812 seconds, completed
zero/known cleanup67,563 ms, raw80,486B SHA-256
`fb6761d19f57c2d57d9ac190b015f963d9a29f22e50c4a9618752a7d6b836a06`.

The regular profile independently has361 tests/36 suites, zero F/E/S and
lint0 errors/9 warnings. Raw10,152B SHA-256
`518caf65da8285c606f85a4519d93d0f0b7324e6a06c56edbcfd74d06e4dc88e`
matches completed zero/known cleanup252,219 ms. Original terminal attribution
belongs to the coordinator: initial receipt16973, corrected receipt39203,
regular12919 and final host26311 were consumed terminal zero. Local metadata
reads are not substituted for those original handles.

Copied APP74,987,568B SHA-256
`fea69522642c5562134eab602cce55d006632fa451b40e55a247ce6a649c6140`
and TEST2,867,979B SHA-256
`7a8a32bedc574b4b3d57e476be54518d05dc641d6952c01ac8f70def2a326eb9`
independently match the recorded artifacts. Corrected receipt/regular APP
audits and both signature result/raw digests match actual completed-zero,
known-cleanup records. Failed helper attempts remain retained: unsupported
`cwd` TypeError before child dispatch, then an audit child1 with missing SDK
environment; corrected explicit environment succeeds without changing artifacts
or suppressing a gate. No new ordinary build/physical-device result is claimed.

All206 tracked Android index rows/2,216,712B independently match source freeze
`ea924a2c2cd7db78e342062225e0aaff52ff7b05`. The final nonweight host inventory
independently rehashes177 rows/154,244,091B, zero mismatches, SHA-256
`10317ff800aec8cd78a24e05f05c454b09b71632f81afb638668f74951a80a3a`.
Model weights/virtual-disk contents are not read. Post-execution documentation
changes do not imply another build or device run. The coordinator's
[verification](LITERT_WORKER_TRACE_VERIFICATION_2026-10-25.md) and draft
[#160](https://github.com/OptimumAF/LocalLore/pull/160) preserve full command and
result context; no merge is performed by this review.

## Capacity and next runnable work

The earlier during-build metadata records D free43,203,670,016 bytes and
headroom253,997,056 bytes above the unchanged floor42,949,672,960. That
transient v1 record remains preserved. Latest post-build v2 instead records
D free47,762,575,360 minus the same floor: headroom4,812,902,400 bytes. The
prior SD image's metadata has logical and allocated size8,589,934,592 bytes;
one equivalent fresh allocation alone is short3,777,032,192 bytes before
userdata/model/cache. Arithmetic is independently checked. This blocks the
current exact D-root plan before mutation. No old image/model/cache deletion,
held-target reuse, reserve reduction or automatic fallback follows.

This is not a general host-capacity impasse. The next useful separately claimed
work is an explicit create-only C-root policy (v2 C free316,256,886,784B),
retaining D's40 GiB floor and using a40 GiB C floor, with tests and fresh
source/artifact/admission checks
before any live call. Existing local-copy consent persists; no fresh permission
question is implied merely by that planned host-path correction. No target or
device trace is qualified by the proposed plan.

Previous real import remains verified; successful SDK PLAY, canonical gift and
restart remain unverified. Old A/#117/#119, reference phone/ARM64/16 KiB,
privacy/cache, power-loss, sustained inference and narrative-quality gates stay
separate. No merge or full milestone checkbox follows this review.
