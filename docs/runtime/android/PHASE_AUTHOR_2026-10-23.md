# Content-free SDK phase journal, 2026-10-23

Refs [#5](https://github.com/OptimumAF/LocalLore/issues/5) (M01.03/M01.05), claim
`6374428287`. This is an experimental diagnostic boundary. It does not establish
real-model correctness, device execution, power-loss durability or canonical
outcomes after a crash. Accepted outcomes remain owned by the Rust engine.

## Format and Java interface

`PhaseJournal` implements `PlayRunner.Checkpoints` and `AutoCloseable`. Its
constructor takes an existing real absolute parent directory, a fresh 32-character
lowercase-hex session, immutable `Identity(pid, uid, processStartElapsedMs,
captureWallMs, captureElapsedMs)`, and an injectable `Clock.wallMs()/elapsedMs()`.
It exclusively creates `sdk-phases-v1.jsonl` with `CREATE_NEW` and `NOFOLLOW_LINKS`;
it creates no directories and writes no implicit first record. Existing files
are refused. The caller owns the fresh app-private directory and process identity.

Each `mark(phase, role)` writes one UTF-8 JSON object followed by LF, completes the
bounded write and calls `FileChannel.force(true)` before returning. Each record
contains exactly twelve fields:

```text
version, sequence, session, pid, uid, process_start_elapsed_ms,
capture_wall_ms, capture_elapsed_ms, phase, role, elapsed_ms, wall_ms
```

Version is 1 and sequence starts at 1. Elapsed time cannot precede the capture or
move backwards; positive wall-clock jumps, including backwards jumps, remain
observations. No prompt, generated text, model bytes, filesystem path, private
story identifier or exception text belongs in this format. Session/process IDs
are private diagnostic bindings and require sanitization before publication.

`read(parent, session)` returns `Snapshot.identity` and immutable
`Snapshot.records`. Records expose final `sequence`, `phase`, `role`, `elapsedMs`
and `wallMs` fields. The reader bounds bytes before decoding, checks strict UTF-8,
exact JSON keys/types, duplicate keys, session/identity, consecutive sequences,
clock bounds, vocabulary and complete LF framing. Partial rows, CRLF, empty rows,
unknown fields and over-budget files are refused; the reader never repairs them.

Phases are `instrumentation_start`, `probe_ready`, `probe_kill`, `terminal`, and
`before`/`after` pairs for `native_create`, `native_submit`, `native_prepare`,
`native_respond`, `native_commit`, `native_reopen`, `model_create`,
`model_initialize`, `model_close`, `role_open`, `role_start`, `role_drain`,
`role_cancel`, `role_close`. Generation phases (`role_*`, `model_create_*`,
`model_initialize_*`, `native_respond_*`) require `director` or `narrator`; other
phases require `none`. Concurrent native preparation means sequence is observed
write order, not a fabricated strictly paired state machine.

The fixed limits are 96 rows and 65,536 bytes. The executed two-turn, three-role
fake protocol trace plus outer start/terminal markers uses 92 rows and 31,439
bytes. A separate valid 96-row maximum-numeric-field test uses 33,399 bytes,
exceeding the initially proposed 32-KiB limit. The approved 64-KiB diagnostic
limit leaves the row bound unchanged and changes no generation budget.

## Work and ownership failure behavior

`PlayRunner` keeps its existing constructors with no-op checkpoints. New
constructor overloads accept `Checkpoints`, with optional existing execution and
drain budgets. Checkpoints surround native create/submit/prepare/respond/commit/
reopen, SDK model create/initialize/close, and conversation open/start/drain/
cancel/close. A sticky journal failure prevents later work and commit while
mandatory cancellation, drain and known-owned resource closure still execute.
Cleanup journal failure cannot replace a required cleanup action. Undrained SDK
ownership remains a process-termination condition. Earlier rejection/cancellation
and distinct cleanup failures are retained privately as suppressed exceptions.

A post-commit journal failure cannot undo an accepted outcome. It propagates as
uncertainty without automatic commit retry or a claim that canon is unchanged.
A forced row establishes only that the Java write/force returned; absence of a
later row does not prove which native or SDK instruction executed before death.

`PhaseJournal.OwnershipUnknown` is a fixed-message `IOException` subtype with a
package-private no-argument constructor. Writer close failure is sticky: later
close calls rethrow the same uncertainty without retrying closure or claiming
known ownership. Constructor rollback-close and reader-close failures use the
same type. Because try-with-resources can suppress a close failure beneath a
body exception, Android callers must inspect bounded cause/suppressed chains
before finishing normally; the coordinator owns that Android classifier and
self-termination wiring. Ordinary persistence failure followed by successful
closure can remain a normal failed operation.

## Author verification and retained attempts

The author used JDK 21, Java source/target 17, and existing cached Gson 2.14.0,
JUnit 4.13.2 and Hamcrest Core 1.3. No dependencies were added. Compilation selected
`Request`, `WarmRunner`, `PlayRunner`, `PhaseJournal`, `PlayRunnerTest` and
`PhaseJournalTest`; outputs and Java temporary files used a fresh D-volume evidence
root. Commands were equivalent to:

```powershell
javac "-J-Djava.io.tmpdir=$phaseTemp" -source 17 -target 17 -cp $cachedJars -d $phaseClasses $sixSources
java "-Djava.io.tmpdir=$phaseTemp" -cp "$phaseClasses;$cachedJars" org.junit.runner.JUnitCore org.locallore.runtimebench.litert.PhaseJournalTest org.locallore.runtimebench.litert.PlayRunnerTest
```

All attempts were retained, including failures:

- First javac invocation: exit 2 because PowerShell split the unquoted JVM
  temporary-directory argument. No tests ran or source compilation completed.
- Second javac invocation: exit 0; one advisory about the module path with
  `-source 17`.
- First JUnit invocation: 25 run, 24 passed, 1 failed. The new worst-path test
  incorrectly expected its 31,439-byte trace to exceed 32 KiB. The assertion was
  corrected to the actual acceptance criterion (nonempty and within the approved
  limit); the separate 96-row test already demonstrated the larger valid record
  budget. No runtime gate was relaxed.
- Third javac invocation: exit 0, same module-path advisory.
- Second JUnit invocation: **27 run, 27 passed**, 1.58 seconds. This includes the
  existing ten PlayRunner tests, seven new runner tests and ten journal tests.
- `git diff --check`: passed before the focused source commit.

Coverage includes real filesystem force/write/read behavior, exact identity and
immutable snapshots, no-clobber construction, clock jumps/reset, row/byte bounds,
concurrent serialization, partial write/force failures, sticky typed closure
uncertainty, try-with-resources suppression, hostile JSON/framing, 23 work/cleanup
checkpoint failure subcases, mandatory cleanup/no commit, undrained ownership,
post-commit uncertainty and preservation of earlier failures.

No full Gradle build, Android API qualification, emulator, physical phone, SDK
inference or actual process-death experiment was run by this author. Those are
coordinator-owned gates. The fake Host/SDK tests do not substitute for them.
