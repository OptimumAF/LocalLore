# Bounded send response-format observations, V2

Refs #9 (M05.01/M05.05), #5 (M01.05 supporting). Root claim6402500798;
trace author claim6402525661. This extends the optional send-call metadata in
[the V1 contract](LITERT_SEND_TRACE_CONTRACT.md). It changes no gameplay,
generation budget, resource guard, model, SDK dependency or accepted-proof gate.
No runtime result is established by this contract or source-only test authoring.

## Interface and observations

The SDK-neutral interface remains a Kotlin SAM:

```kotlin
internal enum class LiteRtSendFormat { REGEX, JSON_OBJECT, OTHER }
internal fun interface LiteRtSendObserver {
    fun record(event: LiteRtSendEvent)
    fun format(value: LiteRtSendFormat) { }
}
```

Existing event-only lambdas remain valid; the default format method does nothing.
The final `LiteRtSendTrace` overrides it with synchronized fixed arrays and a last
enum. No SDK value object, text, pattern, schema, hash, size, path, role, caller
clock, Throwable or callback enters this interface. Production classification of
the actual prepared SDK format is a separately owned call-site hook. `OTHER`
is a closed classification, not an arbitrary description or error cause.

The original six events, their private monotonic last times, and
`observedLiteRtSend` argument/dispatch behavior remain unchanged. Each format
count independently clamps at1000000. An additional observation beyond the cap
sets its sticky saturation flag; exactly reaching the cap need not set it.
`lastFormat` changes on every format observation, even after saturation.
Format observations do not increment events or set event observation times.

Snapshot construction defensively copies the three-key format map and bounded
format set into unmodifiable enum collections. Counts must be0..1000000;
saturated members must be at cap. `lastFormat` is null iff every format count is
zero; otherwise its own count must be positive. Trailing constructor defaults
give older event-only construction an exact zero map, empty set and null last.
Snapshots are historical copies of the synchronized trace, not joint SDK state.

## Closed wire

Serialization now emits version2 with these exact fields in this order:

```text
version, counts, saturated, last_ms, snapshot_ms, time_saturated,
format_counts, format_saturated, last_format
```

The first six fields preserve their V1 bounds and event order. `format_counts`
contains exactly `REGEX`, `JSON_OBJECT`, `OTHER`, in declaration order.
`format_saturated` contains a unique declaration-order subset of those names.
`last_format` is one of those names or null with the invariants above. No
additional or caller-supplied keys or strings are emitted. The host retains a
strict historical V1 decoder; the producer emits only V2.

These transport constants are unchanged despite the retained `_v1` key:

```text
STATUS_KEY=locallore_receipt_send_v1
STATUS_CODE=1338
WIRE_PREFIX=INSTRUMENTATION_STATUS: locallore_receipt_send_v1=
MAX_BYTES=2048 (complete prefix + ASCII JSON, excluding newline)
MAX_COUNT=1000000
MAX_MS=180000
```

The canonical dense V2 fixture has all six event counts at cap and saturated,
all last event times/snapshot_ms180000, time_saturatedtrue, all three format
counts at cap and saturated, and last_formatOTHER. It is697 JSON bytes /747
prefixed bytes. JSON SHA256:
`4359c8f70c2e3024b59e94fe7738e7d117a72a8caf9f682a944b6558f7e6fd65`.
These static bytes are pinned in the authored JVM test and independent Python
test; actual JVM execution is a central gate. The trace performs no IO itself.

## Interpretation and verification limits

An observed format kind describes the application call-site value only. It does
not prove SDK body/JNI entry, grammar compilation, tokenizer behavior, successful
generation, callback drain, ownership release, canonical validity or commit.
Independent event/format counts are not a causal consistency classifier. An
absent optional record differs from a present all-zero record. Diagnostic data
cannot replace the unchanged runner, resource, model or engine proof gates.

The existing helper still ignores any Throwable from event observation and
preserves the identical preparation/dispatch failure. Format observation at the
separately owned SDK call site must preserve the same diagnostic-only policy.
No exception text, cause, class, stack or payload is inspected or serialized.

The26 authored JVM methods retain the prior argument/dispatch/failure/actual
worker-owner seam regressions and add default-method SAM compatibility, format
independence and last-kind ordering, copied/immutable collections, malformed
manual snapshots, pre-copy collection bounds, exact-cap versus overflow and
concurrent event/format/snapshot recording. No JVM/Gradle/build/SDK/model/device
actions were performed by this author. Actual central JVM tests, integrated
call-site tests, strict host regressions, signed artifact audits and separate
controlled admission remain required. Source review is not runtime qualification.
