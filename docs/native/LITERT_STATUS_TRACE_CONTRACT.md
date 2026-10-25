# Pinned wrapper-declared status observations

Refs #9 (M05.05), #5 (M01.05). Root decision6399899218; author claim6399907314.
This is a NEW, explicitly reviewed bounded public-prefix inspection. It is not
the no-message-access classifier from PR170, whose historical contract and
retained results remain unchanged. Earlier errors were not decoded by this
bridge; no prior cause or code is inferred retrospectively.

## Decision and exact SDK boundary

The pinned LiteRT-LM revision
`bda624851d74be34d4e1f7fac1fc4155939539c7` exposes a
[final message-only LiteRtLmJniException](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/LiteRtLmJniException.kt#L25),
with no numeric status property. Its
[callback wrapper](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/Conversation.kt#L652-L658)
embeds a fixed `Status Code: <integer>. Message: ` prefix before its private
payload; the cancellation branch uses a separate exception family. An upstream
structured-status API or native SDK rebuild would be a different dependency/API
change. This packet chooses only the pinned wrapper prefix, retaining the
original SDK/error/cancellation behavior and version.

`liteRtDeclaredStatus(failure:Throwable)` first checks membership in that final
SDK type. Every other Throwable, including cancellation subclasses, wrappers
with an SDK cause, custom hostile getters and foreign prefix lookalikes, returns
UNRECOGNIZED WITHOUT message/cause/stack/description access. It does not use class
name strings or traverse wrapped causes.

Only after the final-type guard does it retrieve the existing nullable message
reference once. Null returns UNRECOGNIZED. It compares ONLY seventeen complete
fixed literal prefixes using case-sensitive startsWith at index0:

```text
"Status Code: 0. Message: "
...
"Status Code: 16. Message: "
```

Every prefix includes the period and the final space. Unknown17+, negatives,
pluses, zero padding, leading/changed whitespace, case changes, and malformed
boundaries return UNRECOGNIZED. No regex, integer parsing, substring, trim,
toString, cause/stack/suppressed access, whole-message scan, logging, copying,
payload validation or message retention is performed. Comparisons inspect only
the expected header window of at most26 UTF-16 code units. Malformed or locally
constructed messages may put private characters within that bounded window;
none are retained or exported. In a well-formed wrapper, arbitrarily private,
large, control or Unicode suffix data does not affect classification and is
never traversed or exported. This source
property is not a measured allocation/timing guarantee for the entire SDK.

The root integration invokes this bridge ONLY when its receipt-only status
trace exists, AFTER original error(Boolean) bookkeeping/fence and the previous
closed error-category observation. Regular/default-null paths do not request
the message reference. No native getter is added on an uncertain owner. The
helper itself does not alter the Throwable or any worker result; caller-side
best-effort diagnostics cannot replace the original failure.

The result is wrapper-DECLARED prefix data, NOT authenticated native status,
exception origin, failing subsystem, cause, recovery eligibility or cleanup.
The public final exception can itself be constructed with arbitrary text.
CODE_0/CODE_1 are therefore representable even when not produced by this pinned
error branch. CODE_0 never means success; CODE_1 never acknowledges cancellation.
UNRECOGNIZED never means safe, non-native or harmless. Existing quarantine and
unknown-resource fences stay authoritative and unchanged.

## Independent closed wire

`LiteRtDeclaredStatus` declaration order is CODE_0 through CODE_16, then
UNRECOGNIZED. Final/internal `LiteRtStatusTrace` accepts only that enum through
record and produces `LiteRtStatusSnapshot` through snapshot. Fixed arrays,
synchronized record/snapshot, per-counter cap1000000 and overflow-only sticky
saturation are used. Exact cap can remain unsaturated; every saturated counter
must be at cap. Snapshots defensively copy unmodifiable maps/sets and their
entries. There is no clock, request/role ID or lifecycle validation.

```text
STATUS_KEY=locallore_receipt_status_v1
STATUS_CODE=1340
WIRE_PREFIX=INSTRUMENTATION_STATUS: locallore_receipt_status_v1=
MAX_BYTES=2048 (complete prefix + ASCII JSON, excluding newline)
MAX_COUNT=1000000
```

JSON has EXACT keys/order:

```text
{"version":1,"counts":{all18enumkeys:integers},"saturated":[declared-order subset]}
```

Counts include every enum in declaration order and range0..1000000. Saturated
is a unique declared-order subset with count==cap. No other key, arbitrary
string, payload, code number, status-name mapping, timestamp or cause is encoded.
Multiple declared statuses may coexist; the codec invents no causal/lifecycle
relationship among counters or between independent worker/send/callback wires.

The canonical dense sample uses all18 counts1000000 and all18 saturated. Its
JSON is532B / prefixed584B; JSON SHA256:
`14007fc5a07f286147fdae2350af4d203b2470d7a9e674d95645dd10e1b574b3`.
Authored JVM and independent host fixtures pin that exact static sample.
Serialization performs no IO or status delivery itself.

## Authored verification and remaining gates

Fifteen authored methods cover exact enums/wire, historical immutable copies
including entries, malformed manual snapshots, counter overflow/concurrency,
dense cross-language fixture/privacy, all17 actual final-SDK exception prefixes
(object construction only, no engine/native initialization), empty/huge/private/
control/Unicode suffixes, malformed prefix lookalikes, hostile foreign getters,
cancellation and wrapped SDK causes, and the non-authoritative0/1 distinction.
Tests never require payload rejection after a complete valid prefix or parse
the suffix to guess a more specific cause.

This author runs no tests, JVM/Gradle/build/SDK executable, ADB/AVD/model/cache
operations. Source review is not compilation. Root owns actual integration,
JVM/host/build/audits and any separately admitted controlled runtime. The
positive122-check grammar, runtime/profile/schema/dependency/60s+5s guards,
storage/privacy limitations and all broader milestone/physical-device gates
remain unchanged.
