# SDK role observations, version 1

Refs #5, M01.04/M01.05 partial. This is diagnostic metadata in the isolated
experiment. It cannot establish accepted events, validate generated text,
authorize a retry, change the turn deadline or substitute for canonical replay.

## Correction to the preceding experiment

The ordinary-gift path in #116 never assigned `first_output_observed`: that
assignment was inside the active-cancellation test branch. Its false field was
unmeasured, not evidence that no text or callbacks occurred. The reported
director timeout, resource drain and independent failed-turn/revision0 replay
remain valid. Original raw/index/aggregate bytes are preserved. The earlier
no-output interpretation is superseded by this explicit source-based correction.

## Per-role output observation

Every generation row adds exactly three fields:

| Field | Meaning |
|---|---|
| `output_observation` | `unknown`, `not_observed` or `observed` |
| `first_output_elapsed_ms` | Null unless observed; finite 0–180,000 ms observer upper bound from immediately before role start |
| `terminal_observation` | Null when unavailable/unsupported; otherwise the fixed object below |

`WarmRunner.Role.observeOutput()` defaults to unknown (`null`). The actual cache
adapter reports whether its bounded text buffer is nonempty. The runner samples
ordinary roles as well as cancellation cases, before deadline checks and after
known terminal drain. Positive evidence is sticky; output-query failure keeps
negative evidence unknown. A positive terminal buffer independently establishes
a positive observation. The legacy turn flag is the OR of positive observations
and is no longer specific to active cancellation.

The elapsed value includes observation/poll scheduling and possibly cancellation
drain. It is not SDK time-to-first-token or first final-response latency.
`not_observed` means a successful local buffer observation was negative; it
does not count all native output or prove absence of hidden channel activity.
Buffered text can still contain rejected thinking tags or coexist with an
earlier callback rejection. Neither positive observation nor buffered byte
count establishes a valid final answer or an accepted proposal.

## Frozen terminal snapshot

`observeTerminal()` defaults to unavailable (`null`). It runs only after known
terminal/drain, before Conversation close. It never queries an undrained owner
or a closed Conversation. Failure of this optional query is independent from
the output probe and cannot replace the primary turn result or skip cleanup.

The exact eight keys are `version=1`, `callback_messages`,
`buffered_text_bytes`, `callback_error`, `benchmark_available`,
`sdk_input_tokens`, `sdk_output_tokens`, and `configuration`.

`callback_messages` counts pre-terminal Java `MessageCallback.onMessage` calls,
saturating at 65,535. It does not count all native callbacks, terminal callbacks
or every channel item. `buffered_text_bytes` is 0–16,384 and a positive count
requires at least one message. `callback_error` is the first observed callback
category: `none`, `unsupported_output`, `output_too_large` or
`generation_failed`. Later cancellation errors cannot erase an earlier exposed
channel/tool/nontext/oversize rejection. No rejected text or exception prose is
copied into diagnostics. Existing primary text-validation behavior is retained.

The adapter makes one optional terminal-snapshot benchmark query only at the
live/drained boundary. A successful `result()` has its own existing required
benchmark read, so the successful path can make two queries. If available,
both raw SDK counters are integers 0–2^31−1. If
unavailable, both are null. SDK zero can be a default or an incomplete-turn
counter; it does not prove zero work. Raw diagnostic counts may exceed gameplay
caps without authorizing any output. Normal successful-generation validation
still enforces its separate positive token/context limits.

`configuration` is null or exactly six bounded metadata fields:
`schema_requested`, `thinking_disabled_requested`, `template_rendered`,
`max_tokens` (1–350, narrator at most220), `prompt_utf8_bytes` (1–32,768), and
`schema_utf8_bytes` (0–32,768). Schema presence agrees with a positive schema
byte count. These describe arguments and a nonempty template render, not proven
schema enforcement, disabled hidden reasoning or complete template semantics.
The older successful-generation feature flags retain that same limitation.

The pinned implementation has an alive-only benchmark query path without an
explicit cancelled-state rejection. This is implementation evidence, not a
guarantee of complete or valid cancelled-turn metrics. The best-effort read
occurs while alive after acknowledged terminal; failing/incomplete observations
remain unavailable or ambiguous. Cancellation poisons the session and subsequent
operations can fail. No extra generation is allowed after cancellation.
No cancelled Conversation is reused. The official
[Conversation implementation](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/Conversation.kt)
and [JNI counters](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/jni/litertlm.cc)
also expose fewer channel details than the native message representation.

## Host admission and outcome separation

The cache controller admits this extended schema only for its separately
qualified role-observation APK pin. All older artifact pins retain the original
exact schema. The standalone play transport accepts either complete known schema
and rejects mixed/extra rows. Both use the unchanged canonical receipt validator
after separately checking diagnostic fields; metadata cannot invent a commit.

Malformed or contradictory diagnostics make the terminal observation invalid.
The controller retains raw bytes, reports an unknown/invalid terminal and
performs only known-owned cleanup. A committed-looking invalid protocol is not
reported as a proven failed turn or safe retry. Stopped-session capture and
strict Rust replay resolve canonical outcome independently.

The [existing readback boundary](TRACED_SDK_PROTOCOL_V1.md) still requires
APK/UID/namespace identity and reader termination before capture. No new model,
dependency, canonical schema, permission, inference retry or budget is introduced.
