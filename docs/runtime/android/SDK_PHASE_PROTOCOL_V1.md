# Private SDK phase evidence, version 1

Refs #5, M01.03/M01.05 diagnostic prerequisite. This experiment adds no
production inference backend or gameplay authority. A checkpoint says which
boundary was durably observed; it does not establish an operation's completion,
the cause of a crash, successful resource disposal or a canonical event.
Accepted outcomes still require strict Rust replay.

## Durable records

Each fresh private session owns a create-new `sdk-phases-v1.jsonl`, at most
96 rows and 65,536 bytes. Every complete numbered JSON row is forced to storage
before its checkpoint returns. The limit accommodates the maximum supported
two-turn spent case, including repair roles. The byte limit accounts for all
12 repeated identity/phase fields at valid numeric bounds. This is a process
death diagnostic, not a power-loss or compromised-OS guarantee.

Exact fields: `version`, `sequence`, `session`, `pid`, `uid`,
`process_start_elapsed_ms`, `capture_wall_ms`, `capture_elapsed_ms`, `phase`,
`role`, `elapsed_ms`, `wall_ms`. Session is a trusted fresh 32-character lowercase
hex nonce. Process start and capture elapsed time use Android elapsed realtime;
wall time is a separately sampled epoch value. Wall-clock changes are retained,
not converted into false process identity. Elapsed reset or regression fails.

Phase and role use fixed allowlists. They cannot contain paths, prompts,
generated text, story/branch IDs, SDK errors or exception prose. The journal
reader requires exact keys/types, contiguous sequence, consistent identity,
known vocabulary and a complete final LF. It rejects duplicates, extra fields,
malformed UTF-8, torn tails, links and excessive input. It does not salvage a
prefix as a valid complete journal. Raw failed bytes must remain private.

## Side effects and cleanup

The cache experiment creates and syncs its journal before entering native/SDK
work. PlayRunner records boundaries around model creation/initialization,
Conversation opening/start/drain/cancellation/close, native preparation and
responses, commit and reopen. Legacy callers retain a no-op checkpoint sink.

A checkpoint failure prevents later SDK or commit entry. Mandatory cancellation,
drain, close and worker join still run when cleanup checkpoints fail. The first
checkpoint failure remains sticky. Resource-close uncertainty requires process
termination rather than reporting graceful disposal. If the post-commit
checkpoint fails, accepted history cannot be undone: the caller receives an
uncertain result and must recover canonical state without automatic retry.

## Optional Android exit correlation

On API 30+, the app best-effort publishes one process-state summary:
`LLP1:<session>:<process_start_elapsed_ms>`. It is below the official
[128-byte limit](https://developer.android.com/reference/android/app/ActivityManager#setProcessStateSummary(byte[]));
missing support, throttling or a runtime exception does not erase the
durable journal. Summary bytes contain no player text and stay private.

A fresh reader queries at most 16
[historical exit records](https://developer.android.com/reference/android/app/ActivityManager#getHistoricalProcessExitReasons(java.lang.String,int,int)) for the exact own
package and original PID. A process-instance match requires exact PID, package
UID, process name and summary token derived from the validated journal. Missing,
stale or ambiguous summaries remain unknown. PID and wall time alone are not a
reuse-safe match. History is bounded and can omit records; its reason/status
does not establish a watchdog, memory-pressure or native-crash cause. No trace
file is opened. An instance match alone does not attribute a death to a
particular run in a process that executed multiple runs.

## Deterministic device control

The explicit `--phase-probe` build profile selects only
`org.locallore.runtimebench.litert.phaseprobe` and its
`PhaseEvidenceInstrumentation`. The old cacheprobe package and its model,
database and failed turn are preserved. The profile requires the existing
isolated build paths, offline dependencies, no permissions and no additional
manifest components. The control uses Android APIs and the pure Java journal.

The build entry point is `python benchmarks/spike/android/litert/cache_build.py
--phase-probe --java21 <existing-jdk21> --output <fresh-D-directory>`. It uses
existing offline tools and dependencies; the normal CLI builds both native ABIs.
The dated qualification report separately identifies its verified native reuse.

After fresh package/hash, namespace, storage and client-ownership checks, the
caller runs exactly one `crash` operation with a fresh nonce. It creates the
journal, syncs `probe_ready`, attempts the summary, syncs `probe_kill`, then kills
only its own process. Independent process absence must precede one `read`
operation for the same nonce. The reader never modifies that journal.

Instrumentation component:
`org.locallore.runtimebench.litert.phaseprobe/org.locallore.runtimebench.litert.PhaseEvidenceInstrumentation`.
Pass `-e operation crash` or `-e operation read`, and `-e session <fresh-32-hex>`,
to `am instrument -w -r` on the explicitly selected emulator. Keep the same nonce
for the single read and retain the full output before decoding it.

`android_phase_result.parse_result` validates the fixed bounded instrumentation
terminal. `journal_verified` additionally requires two checkpoints, last phase
`probe_kill`, role `none` and a fresh reader process. `control_passed` also
requires exactly one exit-instance match. A valid journal with unavailable or
ambiguous exit history is retained as partial evidence, not promoted to a full
control pass. A deliberate self-kill control cannot diagnose the prior SDK crash
or qualify real inference, physical-phone support or ARM execution.
