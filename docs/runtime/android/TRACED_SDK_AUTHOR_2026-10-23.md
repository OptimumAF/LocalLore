# Existing SDK phase journal readback, 2026-10-23

Refs [#5](https://github.com/OptimumAF/LocalLore/issues/5) (M01.03/M01.05), claim
`6374988994`, source base `731b46c`. This adds a diagnostic read path to a newly
qualified cacheprobe artifact. It does not execute a model, diagnose a crash,
recover canonical outcomes or establish any runtime/model performance result.

## Explicit operation

The existing cacheprobe runner accepts an early `read_phase` operation with
**exactly** the argument keys `operation` and `session`. The session is 32
lowercase hexadecimal characters. Volume UUID, play case, profile and unknown
extras are rejected, including extras present with null values. Example template:

```text
adb -s <explicit-serial> shell am instrument -w -r -e operation read_phase -e session <existing-session> org.locallore.runtimebench.litert.cacheprobe/org.locallore.runtimebench.litert.CacheProbeInstrumentation
```

The new path checks the exact cacheprobe package and a non-main instrumentation
thread. It resolves only the target context's canonical no-backup root and the
existing `locallore-cache-probe-v1-<session>` child. The framework root accessor
can establish its own app directory; this code creates no session, owner,
journal, model/cache path or database. It runs before quiet-descriptor setup,
volume requests/discovery, profile handling, SDK/Engine initialization and native
store access. The existing watchdog/pulse lifecycle still applies.

The session directory and every ancestor must be real directories, without
symlink traversal or canonical-path drift. The only marker is `owner-v1`, whose
exact 34 bytes are `locallore-explicit-cache-probe-v1` followed by LF. Marker
reads use a fixed 35-byte buffer and a read-only `NOFOLLOW_LINKS` channel. Unknown
marker-channel closure is a typed `PhaseJournal.OwnershipUnknown`, never a normal
error receipt. Paths/markers are checked again before publication. These are
app-private trusted-ancestor checks, not protection against a malicious same-UID
actor or an OS filesystem replacement adversary.

`PhaseJournal.read` remains unchanged. It enforces the existing complete strict
JSONL format, identity/session, allowed vocabulary, 96-row/65,536-byte limit and
clock bounds. The SDK reader additionally requires first row
`instrumentation_start`/`none` and rejects `probe_ready` or `probe_kill` anywhere.
An SDK journal can validly end before `terminal`. Conversely, `terminal` is only
a diagnostic checkpoint and cannot prove accepted canon.

## Pure Java boundary and terminal

`SdkPhaseReadback.read(Path fixedSessionDir, String session,
long readerProcessStartElapsedMs, ExitObservation exits)` returns a sanitized
`JsonObject`. `ExitObservation.observe(PhaseJournal.Identity)` supplies immutable
`Exit(available, examined, matches, reason, status)` fields. Counts are bounded
0..16, matches cannot exceed examined, unavailable implies zero counts, and
reason/status remain -1 unless exactly one instance matches. Negative reader
start time is refused. `fresh_reader_process` reports only whether the reader's
start elapsed time is later than the recorded process start; callers must require
it before treating the read as a fresh-process observation.

The Android adapter uses the existing `PhaseAndroidEvidence.addExitObservation`
with its exact immutable session/process-summary matching. It does not publish a
new process summary or overwrite the journal. Optional exit-query failure yields
an unavailable observation while keeping a validated journal readable. A typed
or suppressed ownership-unknown failure propagates instead; the early adapter
self-terminates before `finish` using the existing bounded throwable classifier.

The wrapper is `sdk_phase_result`. A completed object has exactly 15 keys:

```text
version, status, error, model_execution, journal_valid, checkpoint_count,
last_phase, last_role, fresh_reader_process, exit_history_available,
exit_records_examined, exit_instance_matches, exit_instance_matched,
exit_reason, exit_status
```

Version is 1, status `completed`, error `none`, model_execution false and
journal_valid true. Count is 1..96. Phase/role come only from the validated fixed
vocabulary. No session, PID/UID, path, prompt, generated text, model bytes,
exception prose or canonical story content is returned. Every ordinary error
resets all partial fields to exactly:

```json
{"version":1,"status":"error","error":"sdk_phase_read_failed","model_execution":false}
```

Unknown ownership yields no graceful terminal. Missing OS history or no exact
instance match is an observation, not evidence of the cause of process death.

## Author checks and limitations

Author checks used installed JDK 21 `javac --release 17`, existing cached Gson
2.14.0/JUnit 4.13.2/Hamcrest Core 1.3, and fresh D-volume output/temp directories.
No dependencies, Android build, ADB/device calls, SDK inference or model reads
were used. Compilation selected the existing `Request`, `WarmRunner`,
`PlayRunner`, `PhaseJournal`, `PhaseFailure`, their existing journal/runner tests,
and the new reader/tests. Command templates:

```powershell
javac "-J-Djava.io.tmpdir=$readTemp" --release 17 -cp $cachedJars -d $readClasses $selectedSources
java "-Djava.io.tmpdir=$readTemp" -cp "$readClasses;$cachedJars" org.junit.runner.JUnitCore org.locallore.runtimebench.litert.PhaseJournalTest org.locallore.runtimebench.litert.PlayRunnerTest org.locallore.runtimebench.litert.SdkPhaseReadbackTest
```

Both compilation attempts exited 0 without diagnostics. Both focused runs passed
**36 tests** (the existing 27 plus nine new reader tests). The second run took
1.773 seconds. Between runs, the Windows junction test was strengthened to prove
that the alias actually resolved to the real fixture parent before testing
refusal; both versions passed. The actual host junction helper was bounded,
reaped and its output retained. No tests were skipped. All synthetic directories
and per-attempt logs remain retained. `git diff --check` passed.

New coverage includes exact output keys and unchanged journal/marker bytes,
SDK/probe separation, early nonce/path/owner refusal, missing session without
creation, actual ancestor junction refusal, malformed/torn/oversized journal
nonmutation, same/older/new reader starts, unavailable/failed exit queries,
malformed exit data and late marker drift resetting partial output, and direct
or suppressed ownership-unknown propagation.

Direct JDK tests do not qualify the Android API compile classpath, installation,
actual new-process read or OS exit-history behavior. Those require the
coordinator's fresh Android build and explicit device admission. The existing
27 journal/runner tests include fake SDK plumbing; they are not real-model proof.

## Integrated offline Android artifact qualification

The coordinator integrated the reader and reset partial exit-history observations
on an internally caught Android query failure. The Java input binding is
`5123c3c42a74479b6f23509fe0dd6b634edb208f`; the actual qualification source is
`e8ef8e77e74570ea1ceb9d6dfa54f25753847361`. The intervening commit contains
controller/decoder work outside the APK inputs. An explicit diff over the Java,
Gradle, manifest, wrapper and native input scopes was empty, and per-file APK
input hashes were identical before/after qualification.

The independently qualified cacheprobe APK is **63,666,936 bytes**, SHA256:

```text
f4d247f3e24c302a7e8d2431d7ee8c9fccc476909c0d82789ea1f84083ddfd81
```

Its package is `org.locallore.runtimebench.litert.cacheprobe`, with only the
expected `org.locallore.runtimebench.litert.CacheProbeInstrumentation` runner.
The manifest audit found no permissions. This is a new artifact, not the prior
`0cf4c253...` APK.

Native binaries were reused only after validating the full prior qualified
`0cf4c253c41483973fd1578837d0ba147a7ed3d6d6cd8eb5818a989e185c09dd`
APK hash and its frozen build-result library identities. Production Rust inputs
matched that prior source; the only native-scope delta was an integration test.
Each extracted Rust ABI library was checked for exact byte identity, expected
five JNI exports and ELF alignment before staging. All four final SDK/Rust ABI
library entries remained byte-identical to the prior APK. No Rust rebuild,
runtime upgrade or model change was performed or claimed.

Actual offline Gradle commands were `:app:assembleDebug :app:testDebugUnitTest
:app:lintDebug :app:auditLintAnalyzer`, with separate D-volume project/output/temp
paths, explicit cacheprobe true/playprobe false/phaseprobe false, no SDK/toolchain
downloads and no daemon. The stage completed successfully in 38 seconds with
50 actionable tasks, all executed. The bounded outer controller completed in
42,000 ms with exit 0 and known process cleanup. XML results show **105 tests,
0 failures, 0 errors, 0 skips**, including all nine new reader methods.

Lint had **0 errors and 9 warnings**: OldTargetApi 1, GradleDependency 1 and
UsableSpace 7. UsableSpace warnings remain the existing nonreserving capacity
observations; qualification does not claim storage reservations or guaranteed
future capacity. Locked SDK/test dependency binary hashes, actual pinned lint
analyzer/dependency metadata, package/runner/permissions, both ABI ELF/native
entry inventory and 16-KiB ZIP alignment checks passed.

All attempts were retained. A first controller call requested 600 seconds and
was refused by the existing maximum-180-second process helper before spawning.
The next bounded controller exited 1 with known cleanup before output creation
because the coordinator HEAD advanced from `5123c3c` to `e8ef8e7`; its exact-HEAD
precondition prevented any build. Its stderr byte count is retained, but that
helper does not retain stderr contents. The approved subsequent controller
explicitly bound both revisions and used the unchanged maximum 180-second
budget. No build/test assertion or timing bound was relaxed.

Private build source, before/after input hashes, old-to-new native provenance,
all stage commands/logs/results, full JVM XML, lint/analyzer metadata and the
frozen APK are retained in fresh evidence directories. An immutable file-hash
index accompanies the handoff. No prior artifact was overwritten or removed.
This author performed no installation, ADB, device process action, model read or
SDK inference. Fresh storage admission and any device experiment remain separate
coordinator gates; APK qualification alone does not authorize or prove them.
