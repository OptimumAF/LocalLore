# Bounded LiteRT send-call observations

Refs #9 (M05.05), #5 (M01.05). Root claim6398576419; author claim6398582360.
This independent optional failure metadata does not change the worker v1/v2
wires, ordinary scene positive proofs, SDK dependency, model, schemas, resource
guards, turn60s/cleanup5s or any host/phase budget. It does not diagnose earlier
sealed failures or establish a runtime result from source-only tests.

## Closed observations

`LiteRtSendTrace` is final/internal and implements the internal
`LiteRtSendObserver.record(LiteRtSendEvent)` interface. Declaration order:

```text
ARGUMENTS_ENTERED
ARGUMENTS_RETURNED
ARGUMENTS_THROWN
ASYNC_CALL_ENTERED
ASYNC_CALL_RETURNED
ASYNC_CALL_THROWN
```

The trace accepts only that enum. It owns its monotonic `System.nanoTime` origin,
fixed arrays and synchronization. No caller clock, text, role, request, model
data, Throwable, path, provider or callback is an input. Each count clamps at
1000000; only a later increment attempt sets its sticky saturation flag. Exact
cap may remain unsaturated. Per-event last observation is null iff count0.
Elapsed milliseconds clamp at180000; time_saturated becomes sticky only beyond
the cap, not exactly at it. Pure arithmetic can be tested without clock injection.

Snapshots defensively copy all maps/sets and expose unmodifiable collections,
including map entries. Serialization uses fixed field/event order and only
bounded numeric, Boolean and closed enum values. Exact JSON keys/order:

```text
{"version":1,"counts":{all six events},"saturated":[declared-order subset],
 "last_ms":{all six events},"snapshot_ms":integer,"time_saturated":boolean}
```

No extra fields or arbitrary keys are permitted. Counts are integers0..1000000;
saturated events must have count at cap, but the inverse does not follow.
snapshot_ms is0..180000; time_saturated implies snapshot_ms==180000. Nonnull
last_ms values are0..snapshot_ms. Snapshot metadata is one synchronized recording
history, not joint state of the SDK or its asynchronous callback machinery.

Constants:

```text
STATUS_KEY=locallore_receipt_send_v1
STATUS_CODE=1338
WIRE_PREFIX=INSTRUMENTATION_STATUS: locallore_receipt_send_v1=
MAX_BYTES=2048 (complete prefix + ASCII JSON, excluding newline)
MAX_COUNT=1000000
MAX_MS=180000
```

The dense canonical fixture (all counts at cap, every event saturated, all
last_ms/snapshot_ms180000, time_saturatedtrue) is552 JSON bytes /602 prefixed
bytes. JSON SHA256:
`12402ccfe90b5203a3abcf569d6cee9be95112778c8668b6a3733a5318bf86a6`.
The authored JVM fixture pins the same declared-order sample as the independent
host parser. A trace returns JSON but performs no IO/status delivery itself.

## Actual call boundary helper

The SDK-neutral helper has this exact internal API:

```kotlin
fun <T> observedLiteRtSend(
    observer: LiteRtSendObserver?,
    prepare: () -> T,
    dispatch: (T) -> Unit,
): Unit
```

It records ARGUMENTS_ENTERED before `prepare`. A thrown preparation records
ARGUMENTS_THROWN and rethrows the SAME original Throwable without wrapping,
message/cause/class/stack inspection or suppression changes; dispatch is not
called. Normal preparation records ARGUMENTS_RETURNED then ASYNC_CALL_ENTERED.
The exact prepared object is passed to dispatch once. A thrown dispatch records
ASYNC_CALL_THROWN then rethrows its SAME original; a normal return records
ASYNC_CALL_RETURNED.

Every observer call catches all Throwable and ignores that diagnostic failure.
An observer cannot replace the original exception, prevent the normal invocation
through an exception, or manufacture a normal SDK result. Production construction
must supply only the final bounded trace (or null); arbitrary observer injection
is only the existing SDK-neutral unit-test seam. There is no guarantee for a
blocking observer, blocked clock or process failure; no timeout was expanded or
blocking-observer test claimed.

THROWN observations happen INSIDE the helper, before the original exception
reaches the unchanged caller's failedStart/quarantine handling. This is not a
fence-before-all-diagnostics guarantee. The actual worker/owner retain their
original fencing, no-reuse and cleanup authority; trace counts never release a
resource or authorize a commit.

ASYNC_CALL_ENTERED marks the application public SDK call SITE, not entry to its
method body, JNI, native code or a successfully accepted request. The SDK may
perform more internal argument conversion. RETURNED means that synchronous
invocation returned; it says nothing about later async success, callback body
drain, known terminal state, engine close or native reclamation. A synchronous
error notification whose callback returns normally can coexist with CALL_RETURNED.
A callback/terminal notification followed by a thrown invocation is CALL_THROWN,
not RETURNED; that throw does not identify its lower-layer origin. A later
callback cannot retroactively change the completed invocation's observations.
Multiple sends may contribute counters; no role, exact failure attribution,
cross-counter causal pattern or clock-to-turn-budget equivalence is inferred.

## Authored verification and remaining gates

Pure tests cover closed/ordered wire, immutable copied maps/entries, typed bounds,
overflow-only saturation, clock arithmetic, concurrent recording/snapshots, dense
wire/privacy, exact argument object/order and failure identity, hostile Throwable
accessors, normal/synchronous/later callback distinctions, null/throwing observers.
An SDK-neutral integration uses the ACTUAL `LiteRtRoleWorker` and
`LocalInferenceOwner`, with original4-byte files and the existing fake resource/
native-port seams. Preparation/call failures, synchronous terminal-then-throw,
and returned callback error must leave zero native deliveries/commits, refuse
reuse, retain uncertain child/parent resources without closing them unsafely,
and preserve quarantine even when the observer throws. Those fake-port counters
are host regression evidence only, not actual SDK calls or canonical-story proof.

This author executes no JVM/Gradle/build/SDK/ADB/AVD/model/cache actions. Central
actual compilation/JVM tests, independent source review, signed artifacts and a
separate exact controlled admission remain required before any runtime finding.
