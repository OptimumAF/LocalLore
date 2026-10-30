# Held AUTHOR and observed process death, version 1

This is a new, unexecuted Android experiment protocol supporting M10.02 and
M09.06. It does not authorize an emulator, model transfer, device operation or
release. It preserves the older SDK5 passive-restart protocol and its captures.

## Why a separate protocol

The buffered restart run completed model import, one AUTHOR creation and a
later passive reopen. Its selected AUTHOR PID was already absent before the
host's force-stop, so it did not demonstrate an alive-to-dead transition.
Android normally stops the target when instrumentation finishes. A completed
JUnit method followed by a missing PID cannot prove the intended fault.

The new instrumentation method
`OriginalAuthorModelInstrumentedTest#recordsOneRealAuthorCreationWithLiveDeathCheckpoint`
finishes the existing real-model AUTHOR checks, closes the inference owner,
then reopens the same Rust/SQLite workspace in the same process. It checks the
unchanged catalog and player snapshot, idempotent creation recovery and no
pending turn, and retains that real native handle while instrumentation waits.
The host must observe this process alive before force-stop and absent or exited
afterwards, within the same advertised hold interval and Android boot.

## Checkpoint and clocks

The isolated LiteRT test profile publishes only these new files under its
`no_backup/original-author-live-checkpoint-v1` directory:

- `catalog-v1.json` and `snapshot-v1.json`: the actual passive native replies.
- `ready-v1.json`: exact version/protocol/package/process identity, import and
  AUTHOR proof hashes, catalog/snapshot hashes, `workspace_open=true`,
  `model_owner_closed=true`, `pending=false`, ready time and expiry.
- `terminal-v1.json`: a refusal if the method ends without external death.

Ready bytes are forced before create-only hard-link publication. The redundant
pending alias is outside the checkpoint directory and removed only after the
complete ready file exists. Existing output is never overwritten.

The hold is exactly 120 seconds and must fit the existing overall 180-second
instrumentation budget; the shell limit stays 210 seconds. Self-reported
`/proc/self/stat` field 22 supplies the process start ticks. Those ticks are not
derived from Android process start milliseconds. The bounded parser handles
spaces and parentheses in the process name and rejects invalid input.

Ready and expiry use `SystemClock.elapsedRealtimeNanos()`. The read-only native
probe's new `--snapshot-v2 PID UID` samples `CLOCK_BOOTTIME` after its actual
proc/pidfd observation and descriptor-close attempts. Official Android source
maps the Java clock to that same clock, including sleep. Comparability requires
an identical boot ID; host timestamps never replace either Android observation.
The v1 probe output and command remain unchanged for SDK5.

The first native observation must be alive with matching PID, UID and start
ticks, after ready and with at least 60 seconds left. The second must be later
and strictly before expiry, and report absent or exited without identity reuse.
Uncertain observation or descriptor cleanup is refused. Neither packets nor
checkpoint assertions by themselves grant SDK ownership or execution authority.

On cancellation or timeout, the Android method must force a terminal refusal
before closing the held native handle. If publishing that refusal fails, it
retains the handle until the advertised expiry under non-cancellable cleanup.
There is one close attempt. Hold expiry never becomes a JUnit pass.

## Host ownership and replay

SDK6 uses fixed code-selected owner, contract, capture and verifier modules.
Admission JSON cannot select another implementation. It retains the shared
storage ledger, fixed tools, source/artifact bindings, isolated service
ownership and claim rules. It adds only the held AUTHOR selector, v2 snapshots
and app-parent absence polling required by this protocol.

The aggregate controller limit stays 1,200 seconds. Pending AUTHOR runs in a
separate owned Python worker with its own observer, capture, command index and
240-second session under a 270-second owner. The control session must have at
least 300 seconds remaining before it starts. Request, started receipt, actual
worker, capture caller and session are joined before dispatch. Worker intervals
must fit the control interval. Capture objects are never shared concurrently.

Before force-stop, one fixed TAR read authenticates the completed AUTHOR proof,
its records/traces and all three checkpoint files. The real proof validators
must establish the canonical baseline before the fault is allowed. The host
checks that the worker is still pending, takes the qualified alive observation,
checks pending again, issues exactly the app's user-0 force-stop, and takes the
second qualified observation. Failed preconditions never dispatch the fault;
an uncertain fault is not retried.

The killed instrumentation output must match the pinned Android process-crash
report. A normal shell exit code alone is insufficient, and this interruption
is never reported as a successful JUnit method. The worker must join and close
its handles before post-fault collection and passive restart. The restart
prerequisite binds both sessions, preflight and later identical files, command
order, raw qualified client proofs, process observations and canonical state.
Known file roles are checked before opening their contents. Subsequent passive
restart invokes the existing method and compares canonical history without
another model request.

SDK6 build admission uses the distinct
`owned_live_death_android_build_admission_v1` scope and exactly 600 JVM cases in
59 XML reports, including the twelve new checkpoint-policy cases. It checks
unique actual case IDs and report counts, source maps, build/lint ownership,
fresh lint, both APK bindings and the native probe build. The offline build
also compares the exact source-derived JVM roster and compiled DEX selectors.
Old SDK5 admission remains at its original scope and 588 cases/58 reports.
Native compilation requires a request-bound, actual-worker started receipt
before compiler dispatch; existing compiler/owner deadlines remain unchanged.

## Validation and remaining gates

Original host tests cover clock/identity/expiry refusal, prevention of unsafe
fault dispatch, pending-worker cleanup and cancellation, fixed SDK6 commands,
byte-backed cross-session prerequisite replay and native compilation admission.
Synthetic replay is not Android execution or model-quality evidence. Build and
execution results must name their exact source and artifacts in a separate
verification report.

Run host regression from the physical D: checkout with process-local `TEMP`,
`TMP` and `TMPDIR` set to `D:\Dev\_Temp`:

```powershell
python -B -m unittest discover -s scripts/tests
python -B -m unittest discover -s benchmarks -p test_runtime_spike.py
```

The prospective guest path constant is not permission to create, reserve or
boot a guest. The prior one-run grant is spent. A future real run requires
separate user authorization and admission through the current shared storage
guard; its two-root and 64 GiB budget are unchanged. Existing guests, unique
captures, recovery, unrelated emulators, shared ADB and system settings are
preserved. Physical-phone, broad reliability and model-quality gates remain
separate. The engine continues to validate and commit canonical events;
narration, claims and summaries gain no new authority.
