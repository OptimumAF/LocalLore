# Stopped-session SDK phase readback, version 1

Refs [#5](https://github.com/OptimumAF/LocalLore/issues/5), M01.03/M01.05
partial. This extends the [private phase journal](SDK_PHASE_PROTOCOL_V1.md)
for an actual cacheprobe SDK session. Diagnostic phases and Android exit
records cannot establish canonical events, successful disposal or a crash cause.
Recover accepted history with strict Rust replay of a stopped-workspace copy.

## Android boundary

The existing isolated cacheprobe runner accepts exactly two extras for the new
operation: `operation=read_phase` and `session=<32 lowercase hex characters>`.
Its component is
`org.locallore.runtimebench.litert.cacheprobe/org.locallore.runtimebench.litert.CacheProbeInstrumentation`.
This branch executes before volume discovery, model inspection, native engine,
SDK initialization and normal play setup. It never creates or repairs a session.
Unknown extras, including play/profile/volume extras, fail closed.

`SdkPhaseReadback.read` requires the exact existing private session directory,
34-byte owner marker and bounded complete journal. It rejects links and changed
ownership, requires the first `instrumentation_start/none` record and rejects
the separate deliberate-kill probe vocabulary. Marker and journal close
uncertainty require process termination. An optional exit-query failure yields
unavailable history rather than partially enumerated or fabricated matches.
The reader revalidates ownership before publishing its fixed observation.

The distinct `sdk_phase_result` instrumentation result contains either exactly
four error fields (`version=1`, `status=error`, `error=sdk_phase_read_failed`,
`model_execution=false`), or exactly fifteen completed fields:

| Field | Constraint |
|---|---|
| `version`, `status`, `error`, `model_execution` | `1`, `completed`, `none`, `false` |
| `journal_valid` | `true` |
| `checkpoint_count` | Integer 1–96; one row must end at `instrumentation_start/none` |
| `last_phase`, `last_role` | Fixed SDK phase vocabulary and matching role; no probe phases |
| `fresh_reader_process` | Boolean; reader process start is later than original start |
| `exit_history_available` | Boolean; false requires zero examined/matched rows |
| `exit_records_examined`, `exit_instance_matches` | Integers 0–16, matches no greater than examined |
| `exit_instance_matched` | True only for exactly one process-instance match |
| `exit_reason`, `exit_status` | Nonnegative integers for one match; otherwise both `-1` |

No nonce, PID, path, prompt, generated text or exception prose is exported by
this result. A fresh process and exact exit-instance match strengthen diagnostic
identity, not interpretation of the phase or OS reason.
The controller's final verified force-stop can itself create an exit record
after a successful SDK operation; a matching record does not imply a crash.

## Host boundary

The trusted caller persists a fresh nonce privately before calling
`android_cache_control.run_control(..., session_nonce=nonce)`. Existing callers
retain the generated UUID default and frozen workload. Invalid explicit nonces
are refused before measurements, model callbacks or device operations. Reports
never echo the nonce. Do not adopt or automatically retry an earlier session.

After the original control has known client cleanup and stopped-process
evidence, call `android_sdk_phase_control.read_phase(device, apk_sha, nonce,
raw_sink)` once. The reader admits only its newly qualified artifact pin.
Older supported play artifacts cannot dispatch this operation. The caller owns
fresh capacity, backing identity and preservation gates.

The controller binds installed APK bytes and UID, requires both primary-process
and namespace absence, then dispatches a 45-second read. It does not stop a
present original SDK process. Full bounded raw bytes are retained before any
transport/size/decoder verdict, including failed or oversized output. Unknown
client ownership prevents parsing and all dependent device operations.

The decoder accepts only the distinct complete instrumentation wrapper, uniform
LF or CRLF, strict JSON and the fixed schema above, with a 16 KiB maximum.
`journal_verified` additionally requires a fresh reader; `instance_matched`
requires exactly one matching exit record. The reader may remain alive after
Android finishes instrumentation. Before admitting a snapshot, the controller
rechecks APK/UID, stops that reader and verifies full namespace absence. Failed
cleanup revokes verification while preserving the observation. A changed APK
or UID prevents stopping the replacement owner.

Keep the original SDK result, diagnostic observation and canonical replay result
independent. A reader error cannot erase an accepted SDK receipt. A terminal or
commit checkpoint cannot substitute for canonical replay. No automatic
inference retry, migration, repair, model copy or device lifecycle operation is
part of these interfaces.
