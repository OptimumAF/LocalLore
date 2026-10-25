# Bounded worker timing and creation observations — v2

Refs #9 (M05.05 / M01.04 / M01.05 prerequisite). This diagnostic replaces neither
worker ownership checks nor the engine's canonical events. It does not change
runtime configuration, role schemas, deadlines, cancellation, storage admission,
or cleanup. The [v1 contract](LITERT_WORKER_TRACE_CONTRACT.md) is historical and
unchanged; host parsing retains its separate v1 support.

## Closed API

`LiteRtWorkerTrace` remains a final internal class with `record(event)` and
`snapshot()`. The thirty `LiteRtWorkerEvent` names and their declaration order
are unchanged from v1, including `DRAIN_SETTLED`. Added operations are:

```kotlin
creationEntered(role: LiteRtTraceRole): Int
creationReturned(ordinal: Int)
creationFailed(ordinal: Int, failure: LiteRtTraceFailure)
```

`LiteRtTraceRole` is exactly `DIRECTOR, NARRATOR`. A repair uses `DIRECTOR`; its
retained ordinal distinguishes the successive attempt, without storing a prompt,
schema, generated text, turn identifier, or arbitrary label. `LiteRtTraceFailure`
is exactly `NONE, CANCELLED, OTHER`. The trace receives no Throwable, message,
class name, callback, clock provider, path, handle, model, or IO input. It reads
only its own `System.nanoTime()`; a separate pure arithmetic helper permits
boundary tests without an injectable clock or runtime observer.

Calls synchronize on the trace. Creation entry increments a total capped at
1,000,000 and retains at most three immutable records, returning their ordinals
1, 2, 3. Later entries return zero but still update the bounded total. Reaching
the total cap does not set `creations_saturated`; an additional observation does.
Thus `creations_total > 3` explicitly means the list is truncated, even when
`creations_saturated` is false. No unbounded list is allocated.

Zero, negative, out-of-range, and locally unissued ordinals are ignored. A
`creationFailed(..., NONE)` observation is ignored. The first terminal observation
for an owned slot wins; later return/failure calls cannot rewrite it. These
diagnostic methods do not validate or transition worker resources. Ordinals are
local slot numbers, not unforgeable capabilities: a trusted caller must send a
returned integer only to its originating trace. Another trace's equal integer
cannot be distinguished once the same local slot exists.

## Timing and snapshot bounds

Timing is integer elapsed milliseconds since trace construction, based on a
monotonic clock rather than wall time. Sub-millisecond fractions are truncated;
negative arithmetic input is clamped to zero. Elapsed time is clamped at
`MAX_MS = 180000`. `time_saturated` is sticky only after an observed elapsed
nanosecond value exceeds the exact 180000-millisecond boundary. Reaching the
boundary exactly does not claim overflow. Saturation implies
`snapshot_ms == MAX_MS`, but that equality alone does not imply saturation.

Each event has a last observation time, null exactly when its count is zero.
Every non-null event time is within `0..snapshot_ms`. Updating a capped event
still updates its last observation time; the event's existing overflow-only
saturation semantics are unchanged. These timestamps are source recording
points, not measurements inside JNI or native code, and are not per-call
durations. Counts and creation slots are independent observations: no equality
or lifecycle relationship is imposed between them.

`snapshot()` copies under the same lock and returns `LiteRtWorkerSnapshot` with
immutable defensive copies of `counts`, `saturated`, `lastMs`, and `creations`,
plus `snapshotMs`, `timeSaturated`, `creationsTotal`, and `creationsSaturated`.
Each creation exposes only `ordinal`, `role`, `enteredMs`, `returnedMs`,
`failedMs`, and `failure`. Enums and primitive immutable fields are copied into
the retained records. Returned maps, entries, sets, and lists cannot mutate the
snapshot or later observations.

Manual snapshot construction refuses missing event keys, invalid numeric ranges,
inconsistent null times, unjustified saturation flags, malformed ordinal lists,
two terminal timestamps, or mismatched failure category. A creation has at most
one return/failure time; each end is at least entry and at most snapshot time.
`failure == NONE` holds exactly when `failedMs == null`. The list contains
ordinals `1..min(creationsTotal, 3)`, in that order.

The synchronized diagnostic copy does not make source counters, callbacks,
native state, filesystem state, model validity or resource ownership jointly
atomic. No cross-counter causal inference is permitted. `DRAIN_SETTLED` remains
the historical settled branch inside `withContext`, not a successful suspend
return delivered to its caller. Callback `*_RETURNED` points remain Kotlin body
exit, including caught failures, and exclude hidden JNI epilogues. `CLOSE_KNOWN`
is a historical checked-return gate, not current reclamation. `UNCERTAIN` counts
notifications after the original synchronous fence, not unique transitions;
zero never establishes a healthy owner.

## Exact JSON and envelope

Top-level keys are exactly this ordered sequence:

```text
version, counts, saturated, last_ms, snapshot_ms, time_saturated,
creations_total, creations_saturated, creations
```

`version` is 2. `counts` and `last_ms` contain all thirty event keys in enum
declaration order. Counts are integers `0..1000000`. The `saturated` array is a
unique subset in declaration order, with every listed counter at the cap.
Creation keys are exactly `ordinal, role, entered_ms, returned_ms, failed_ms,
failure`; roles and failures serialize only their closed enum names. A pending
creation has both end times null and failure `NONE`; a returned creation has
failure `NONE`; a failed creation has null return time and failure `CANCELLED`
or `OTHER`. There are no additional or optional fields.

| Constant | Value |
| --- | --- |
| `STATUS_KEY` | `locallore_receipt_worker_v2` |
| `STATUS_CODE` | `1337` |
| `WIRE_PREFIX` | `INSTRUMENTATION_STATUS: locallore_receipt_worker_v2=` |
| `MAX_BYTES` | `4096` |
| `MAX_COUNT` | `1000000` |
| `MAX_MS` | `180000` |
| `MAX_CREATIONS` | `3` |

Encoding is printable ASCII JSON with no extra spaces. The complete prefix plus
JSON must fit 4096 UTF-8 bytes, excluding a line terminator. The dense maximum
fixture has all counters 1000000, all events saturated, all last times and
snapshot 180000, time saturation true, total 1000000 with creation saturation
true, and three `NARRATOR` creations entered/failed at 180000 with `CANCELLED`.
Its JSON is 2908 bytes and prefix-inclusive wire is 2960 bytes. This is a bound
fixture, not a claim that those observations happened together.

The trace performs no status delivery and cannot turn a failed operation into a
pass. The host parser and instrumentation integration are separately owned.
No diagnostic failure is authority to skip a guard, drop a schema, retry, close
unknown owners, extend a deadline, or commit a turn.

## Verification boundary

Authored JVM cases cover exact enums/envelope/JSON order; event and creation
overflow boundaries; elapsed arithmetic at and around the cap; null and terminal
constraints; unissued/invalid/duplicate tokens; truncated totals; copied Java
collection immutability; private-input API restrictions; and concurrent records,
creation terminals and snapshots with joined futures. These instantiate no SDK,
Android component, model or provider. The source author performed source/diff
checks only. Central JVM compilation/execution and any runtime/device
qualification remain separate gates; authored tests are not passing results.
