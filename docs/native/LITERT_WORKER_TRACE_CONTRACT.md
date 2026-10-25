# Bounded LiteRT worker-stage observations

M05.05 / M01.05 prerequisite. This contract defines a small in-memory diagnostic
value, not a worker implementation, model qualification or gameplay event log.
The engine's accepted events remain canonical. Trace counts grant no storage,
inference, cancellation, ownership, cleanup or resource-release authority.

## API and closed vocabulary

`LiteRtWorkerTrace` is a final internal class with `record(LiteRtWorkerEvent)`
and `snapshot(): LiteRtWorkerSnapshot`. It has no string, exception, provider,
callback or filesystem input. It performs no IO, logging or status delivery.
The caller chooses where the finite event is recorded; the trace cannot prove
the correctness of that placement.

The exact enum declaration and serialization order is:

```text
ADMISSION_ENTERED, ADMISSION_RETURNED,
ENGINE_CREATE_ENTERED, ENGINE_CREATE_RETURNED,
INITIALIZE_ADMISSION_ENTERED, INITIALIZE_ADMISSION_RETURNED,
INITIALIZE_ENTERED, INITIALIZE_RETURNED,
ROLE_ADMISSION_ENTERED, ROLE_ADMISSION_RETURNED,
CONVERSATION_CREATE_ENTERED, CONVERSATION_CREATE_RETURNED,
SEND_ADMISSION_ENTERED, SEND_ADMISSION_RETURNED,
SEND_ENTERED, SEND_RETURNED,
MESSAGE_ENTERED, MESSAGE_RETURNED,
DONE_ENTERED, DONE_RETURNED,
ERROR_ENTERED, ERROR_RETURNED,
DRAIN_SETTLED,
CANCEL_ENTERED, CANCEL_RETURNED,
CONVERSATION_CLOSE_ENTERED, CONVERSATION_CLOSE_KNOWN,
ENGINE_CLOSE_ENTERED, ENGINE_CLOSE_KNOWN,
UNCERTAIN
```

These are diagnostic observations, not typed domain commands or canonical
events. Arbitrary ordering, unequal entered/returned counts and `UNCERTAIN`
remain representable; the trace does not invent a lifecycle validator or infer
that any handle was released. In particular, a `*_KNOWN` counter is not an
independent resource audit, and a `RETURNED` count does not establish success.

Recording points are historical. `DRAIN_SETTLED` records the settled branch
observed inside `withContext`; prompt cancellation may prevent the caller from
receiving a successful drain-call return. Callback `MESSAGE_RETURNED`,
`DONE_RETURNED` and `ERROR_RETURNED` record Kotlin callback-body exit, including
exit after caught failure. They prove neither valid content nor execution of a
hidden native callback epilogue. `CLOSE_KNOWN` records a historical checked SDK
return gate, not caller delivery or current ownership. Worker integration records
`UNCERTAIN` notifications after the original synchronous owner-fencing hook;
this is not an exact count of transitions. Callback accounting/fencing remains
ahead of the diagnostic entered point. `UNCERTAIN` being zero never means the
owner is healthy or every unsafe path has been observed.

For admission, construction, initialization, conversation, send, cancel and
close, `ENTERED` denotes reaching the source point immediately before the
SDK-neutral resource/admission call. It is an attempted call, not an
acknowledgment from inside the SDK or JNI callee. Its matching `RETURNED`
denotes reaching the point after that call returns. For example,
`INITIALIZE_ENTERED=1` / `INITIALIZE_RETURNED=0` locates the last observed
pre-call point; it does not establish native initialization entry, a native
hang or its cause. Callback entered counts instead follow the original
callback accounting/fence. The fixed observations do not inspect clocks,
thread stacks or hidden SDK state to fill such gaps.

## Fixed memory, concurrency and snapshots

The trace retains exactly thirty integer counters and thirty saturation flags;
it retains no history, timestamps, identifiers, text, paths or payloads.
`record` and `snapshot` synchronize on the trace instance. A snapshot copies all
counters under that lock, then owns immutable defensive copies of its complete
`Map<LiteRtWorkerEvent, Int>` and `Set<LiteRtWorkerEvent>`.

Each counter starts at zero and stops at `MAX_COUNT = 1_000_000`. Reaching that
number does not set saturation. A subsequent record for the same event leaves
the counter unchanged and permanently adds that event to the saturation set.
No integer can wrap. Overflow on one counter does not change another counter.

Snapshot construction refuses missing counters, values outside the range and
saturation entries whose counter is below the cap. Caller-owned collections,
returned maps, sets and map entries cannot mutate a snapshot or the trace.

Synchronization makes the counter copy coherent with `record`, but does not
make concurrent SDK callbacks, files, source counters, handles or external
resource state jointly atomic with the snapshot. Counts are observations only,
not a complete state proof or proof of continuous process identity.

## Exact JSON and instrumentation envelope

`snapshot.json()` has no parameters and returns exactly this shape, with all
thirty counter keys in the declaration order above:

```json
{"version":1,"counts":{"ADMISSION_ENTERED":0,"ADMISSION_RETURNED":0,"ENGINE_CREATE_ENTERED":0,"ENGINE_CREATE_RETURNED":0,"INITIALIZE_ADMISSION_ENTERED":0,"INITIALIZE_ADMISSION_RETURNED":0,"INITIALIZE_ENTERED":0,"INITIALIZE_RETURNED":0,"ROLE_ADMISSION_ENTERED":0,"ROLE_ADMISSION_RETURNED":0,"CONVERSATION_CREATE_ENTERED":0,"CONVERSATION_CREATE_RETURNED":0,"SEND_ADMISSION_ENTERED":0,"SEND_ADMISSION_RETURNED":0,"SEND_ENTERED":0,"SEND_RETURNED":0,"MESSAGE_ENTERED":0,"MESSAGE_RETURNED":0,"DONE_ENTERED":0,"DONE_RETURNED":0,"ERROR_ENTERED":0,"ERROR_RETURNED":0,"DRAIN_SETTLED":0,"CANCEL_ENTERED":0,"CANCEL_RETURNED":0,"CONVERSATION_CLOSE_ENTERED":0,"CONVERSATION_CLOSE_KNOWN":0,"ENGINE_CLOSE_ENTERED":0,"ENGINE_CLOSE_KNOWN":0,"UNCERTAIN":0},"saturated":[]}
```

Only overflowing event names appear in `saturated`, also in declaration order.
Input map/set iteration order never changes the wire. There are no optional or
additional fields and no arbitrary-string escaping or exception inspection.

Constants are fixed:

| Constant | Value |
| --- | --- |
| `STATUS_KEY` | `locallore_receipt_worker_v1` |
| `STATUS_CODE` | `1337` |
| `WIRE_PREFIX` | `INSTRUMENTATION_STATUS: locallore_receipt_worker_v1=` |
| `MAX_BYTES` | `4096` |
| `MAX_COUNT` | `1_000_000` |

The complete prefix plus JSON must be printable ASCII and at most 4096 UTF-8
bytes, excluding the line terminator. A delivery adapter may use the key/code;
the trace itself does not emit status, catch failures or replace an assertion.
Having a JSON snapshot proves neither delivery nor a passing instrumentation
method. No SDK output, provider exception, message content, model bytes, user
input, path, stack or raw identifier is accepted into this value.

## Verification and remaining gates

The JVM tests cover exact vocabulary/order/wire, per-event increments, bounded
overflow, defensive copies and Java collection immutability, invalid snapshot
refusal, maximum wire size, closed input signatures and concurrent recording.
They instantiate no worker, SDK, provider or Android component. Actual test
execution and any worker/status integration are separate coordinator checks;
source and test authorship alone is not a passing build or device result.

No deadline, retry, fallback, storage floor, role/prompt contract, model identity,
lease, cleanup rule or runtime admission is changed by this trace. Actual local
model inference, Android callback delivery, resource ownership and physical
device qualification still require their own authorized evidence.
