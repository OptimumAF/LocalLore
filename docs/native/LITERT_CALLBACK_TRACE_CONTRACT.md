# Bounded per-call callback observations

Refs #9 (M05.05), #5 (M01.05). Root claim6399434479; author claim6399461669.
This independent optional status does not change worker v1/v2 or send-v1 wires,
positive ordinary-route proof grammar, SDK/model/profile selection, budgets,
schemas, cancellation or resource authority. Source-only observations are not
an SDK execution result or diagnosis of a prior failure.

## Closed API and recording points

Final/internal `LiteRtCallbackTrace.begin(role,contextTokens,maxOutputTokens,
promptBytes,schemaBytes)` returns a final `LiteRtCallbackCall?`.
Roles are DIRECTOR/NARRATOR. Valid configured metadata: context512..4096,
max output1..350, prompt0..32768 bytes, schema2..32768 bytes, sum≤32768.
The parent validates metadata BEFORE changing requests/slots, including when
all three slots are already occupied. Its own request counter clamps at1000000
and sets requests_saturated only on a later increment attempt. The first three
calls are retained in order with contiguous ordinals1..3; further valid begin
requests return null and never replace earlier calls. Omission is explicit,
not attributed to one of the retained requests.

Each handle exposes only `output(bytes)`, `done()` and `error(category)`.
Counter declaration order is OUTPUT_CHUNKS, OUTPUT_BYTES, DONE, CANCELLED,
SDK_JNI, OTHER. Error category is the closed CANCELLED/SDK_JNI/OTHER enum.
output requires0..16384 bytes BEFORE mutation and updates its chunk/byte counters
together; zero-byte accepted chunks still count. done/error increment the
corresponding counter. Multiple, late, repeated and mixed terminals remain
representable: there is no lifecycle validator. Handles mutate only their own
retained slot through one parent monitor; an unretained/cross-parent handle
does not gain another slot. Parent snapshots and every handle mutation use
that same monitor. No caller content, String, Throwable, IO, callback or clock
is a trace input, and no timer is recorded.

Each counter clamps at1000000 using safe addition; overflow alone sets its
sticky saturation flag. Adding zero at an exact byte cap does not saturate it.
Saturated implies count at cap; exact cap can remain unsaturated. Snapshots
copy lists/maps/sets and map entries defensively and expose only immutable
metadata, including all retained slots' counts at one recording observation.

The coordinator owns actual integration: begin is best-effort after existing
validated request/storage admission and BEFORE conversation creation, so begin
does not prove SDK send was reached. output is called only after the original
chunk-field validation, strict UTF8 buffer write and `<think>` checks succeed.
Thus it counts accepted worker message callbacks/bytes, including valid zero
chunks, not all SDK chunks or token counts. No parser change may convert this
into a complete rejected-output accounting claim.

done is observed after original callback bookkeeping/finally. A new default
no-op errorCategory delivery follows the original error(cancelledBoolean)
return/fence; old fake resources need not emit the extra category. Root's adapter
must preserve original SDK error behavior if diagnostics fail. SDK_JNI indicates
a finite SDK/JNI provenance category, not the lower-layer cause, native status,
exception text/class/cause or a token-limit diagnosis. No native getter is added
after uncertainty. Absence of errors never proves a healthy owner or callback
quiescence; known close and quarantine gates remain separate.

## Exact independent wire

```text
STATUS_KEY=locallore_receipt_callback_v1
STATUS_CODE=1339
WIRE_PREFIX=INSTRUMENTATION_STATUS: locallore_receipt_callback_v1=
MAX_BYTES=4096 (complete prefix + ASCII JSON, excluding newline)
MAX_CALLS=3
MAX_COUNT=1000000
```

Top-level keys/order are EXACT:

```text
{"version":1,"requests":integer,"requests_saturated":boolean,"calls":[...]}
```

Each call's canonical producer keys/order are:

```text
ordinal,role,context_tokens,max_output_tokens,prompt_bytes,schema_bytes,counts,saturated
```

counts has all six counters in declaration order. saturated is their unique
declared-order subset. Metadata ranges are as above; requests is0..1000000,
requests_saturated implies requests==1000000; calls length==min(requests,3).
No extra fields/arrays/role names/arbitrary strings are encoded. Configured byte
lengths/caps are not measured tokenizer work, actual context use, generated
tokens or SDK-native request admission. No cross-counter lifecycle consistency
or inference/canonical/resource authority follows from this metadata.
The host accepts JSON object key permutations while refusing duplicate keys;
array order, contiguous ordinals and the ordered saturation subset remain checked.

Canonical dense fixture: requests1000000/saturatedtrue; three NARRATOR calls
ordinal1..3, context4096/output350/prompt16384/schema16384, every counter1000000,
every counter saturated in declaration order. JSON1055B / prefixed1109B,
SHA256 of JSON:
`754c4eef06b6ea5fa2bd395ec449be37779c875799f8a71cce5115e368d754b3`.
The same static sample is pinned in authored JVM and independent host tests.
Serialization itself performs no IO/status send.

## Authored verification and limits

Fifteen pure test methods cover exact wire/enums, valid metadata limits,
invalid-no-sideeffects before and after omission, stable first-three slots,
zero/max chunks and invalid bytes, exact byte/request/terminal cap boundaries,
overflow-only flags, mixed/late terminals, handle identity, nested immutable
collections/entries, malformed manual snapshots, concurrent handle mutations
and snapshots, dense cross-language wire/hash and closed privacy signatures.
The controlled concurrent test's fixed two-byte chunks verify atomic paired
output accounting; that is not a general cross-counter parser assumption.

This author runs no JVM/Gradle/build/SDK/ADB/AVD/model/cache actions. Central
actual compilation/tests, independent review, integration/audits and a separate
admitted controlled runtime remain necessary. No model quality, token-limit
cause, callback-native epilogue, future-callback immunity, phone compatibility,
resource release or positive milestone completion is established by this file.
