# Traced SDK independent review, 2026-10-23

Refs [#5](https://github.com/OptimumAF/LocalLore/issues/5), M01.03/M01.05,
claim `6374988994`. The one real guarded gift attempt returned a structured
director timeout, with a false first-output flag. A later source audit found
that ordinary-run flag was unmeasured, so it cannot prove no output. Its reported owners drained;
strict Rust replay independently established a failed turn at revision zero,
zero accepted events/receipts and the player's one potion intact. This is
verified failure handling, not a successful guarded gift or full task acceptance.
No remaining concrete source or evidence discrepancy was found within this
packet after the corrections below.

I reviewed sources, Git deltas, retained raw records, XML, APK contents and
private hash indexes. I did not run builds, tests, ADB, model operations or
device controls. The coordinator and authors performed the recorded executions.
This report is the reviewer's sole owned change.

## Source and adversarial findings

The base is `731b46cfc818a17e15140d466c403e1f1c1a51b2`. Java is bound to
`5123c3c42a74479b6f23509fe0dd6b634edb208f`, build orchestration to
`e8ef8e77e74570ea1ceb9d6dfa54f25753847361`, and final artifact/controller
binding to `0b89eb6b295aac58b864bbaec0e998194ec7d1ee`. This qualifies the
specified narrow experiment, not every later main-branch combination.

The source review identified and checked these corrections before device entry:

- The reader initially admitted legacy play APK pins. It now accepts only the
  qualified reader-capable artifact and rejects older known pins before device
  access. Legacy play pins and default session generation remain unchanged.
- The new controller initially rejected oversized output before its dedicated
  raw sink. It now retains bounded transport bytes before size, transport or
  decoder rejection, including known-clean failed transport.
- A one-row summary could claim a generation checkpoint even though the Java
  journal requires its first row to be `instrumentation_start/none`. The decoder
  now rejects that impossible combination. The added hostile regression passes;
  this finding was a source counterexample, not a separately executed red run.
- Android exit enumeration could leave partial availability fields after a
  caught API exception. The adapter now resets the complete optional observation
  to unavailable, rather than publishing an apparent zero-match enumeration.
- The unexecuted first critical script could perform closure reads after a
  recovery owner became uncertain. Version two propagates the recovery owner's
  sticky cleanup flag into the shared device in `finally`, before post-capture
  checks or metadata closure. Retained host fixtures cover failure and return
  paths. No such uncertain-owner device outcome was injected in this cohort.

The existing base already propagated journal reader-close uncertainty; no new
fix to that existing `PhaseJournal.read` behavior is claimed here. The new owner
marker reader follows the same typed-close rule.

The early `read_phase` branch precedes descriptor redirection, external-volume
discovery, model inspection, native engine and SDK setup. It requires exactly
the two frozen extras, fixed private namespace, exact owner marker, bounded
complete journal, the SDK initial row and no deliberate-kill probe vocabulary.
It creates or repairs no session and publishes no new process summary. Close
uncertainty cannot become a graceful error receipt. The distinct host decoder
requires exact 15/4-field schemas, strict JSON and terminal framing, role/phase
coherence and coherent exit counts. The controller requires original namespace
absence and binds APK/UID around the reader's own stop and absence proof.

The caller-selected nonce is validated before measurements, model callbacks or
device access, persisted privately before the single dispatch, and absent from
public results. The critical script binds the same tracked device, fresh model
verification, current physical backing/storage observations, one dispatch and
no automatic retry. Checkpoints, structured SDK results and canonical replay
remain independent authorities for their respective observations.

## Qualification and actual outcome

The APK is **63,666,936 bytes**, SHA256
`f4d247f3e24c302a7e8d2431d7ee8c9fccc476909c0d82789ea1f84083ddfd81`.
I parsed all eleven JVM XML suites: **105 tests, zero failures/errors/skips**.
Lint reports zero errors and nine warnings: OldTargetApi1, GradleDependency1,
UsableSpace7. The retained Gradle log ends successfully with 50 executed tasks.
All 35 before/after input hashes match. Actual manifest, permissions, locked
dependency/analyzer, exports and ZIP audits support the stated qualification.

All four packaged native libraries independently compare byte-for-byte with
the previous `0cf4c253...` APK; their ELF load alignments are 16 KiB. The two
Rust libraries retain native source
`ba31932665eab2079c54a02a0182857f598fa0c4`. Git deltas confirm no production
Rust/build-input change; the excluded native delta is an integration test.
There was fresh Java qualification and no new native compilation or ARM run.

Retained final logs end with **343 script, 140 benchmark and 34 SDK-helper
tests passing**. The two focused author runs each passed 36 JVM tests; those
selections overlap the 105-test qualification and are not additional unique
coverage. Qualification also retains the pre-spawn 600-second-budget refusal
and a subsequent exact-HEAD precondition refusal before the successful bounded
build. The latter retains stderr length, not stderr payload. These are setup
refusals, not failed JVM or gameplay test executions.

Preparation completed in 63,187 ms with 376 recorded commands, known cleanup,
zero SDK calls and zero model copies. Its two full source-model passes match
the pinned 2,588,147,712-byte SHA256 and all 78 chunk observations, with stable
identity. The qualified update preserves UID/app-root identity and prior
artifacts. The critical cohort completed in 124,687 ms with 338 commands. I
independently matched every command's retained stdout size/hash and known
completion/cleanup metadata: 714 commands total, including 22 expected absence
exit1 responses and one remote-exit-37 control. Seven host metadata clients are
recorded separately. These counts describe retained owned commands.

The raw 2,341-byte SDK terminal exactly matches the controller's inner result
and metrics. It reports model initialization, one director call, zero narrator
calls/repairs, false first-output flag (later found unmeasured), timeout and balanced one-Engine/
one-Conversation closure, with cancellation and terminal callbacks. The gift
check correctly remains false. Load and failed-generation observations are
7,524.4987 ms and 50,703.7637 ms; token counts are unavailable. Error-row flags
and aggregate default counters do not prove zero work, schema incompatibility
or successful constrained generation. The 92,953-ms controller wall time is
not successful complete-turn latency. Before/after storage admission passed;
observed cache growth was 788,412,770 bytes, not a proven maximum or reservation.

The raw 400-byte phase terminal exactly matches its 15-field observation:
27 checkpoints ending `terminal/none`, a fresh reader and one exact historical
process-instance match, reason10/status0 after the controller's own stop.
The app validated its private journal; the host did not export or parse all raw
journal rows. A terminal checkpoint or exit-instance match proves neither a
canonical commit nor the cause of this or the earlier SDK process exit.

Qualified read-only transport captured a stable 65,536-byte SQLite main file,
SHA256 `e16975473712cc1663bbf9e6c2c2274f50345018b374e88cf46d4680cf2c8aba`;
all three sidecars were absent and source facts matched before/after. The
previously qualified Rust helper completed in 62 ms on a create-new copy,
validating schema2, foreign keys and strict accepted-history replay. Its result
is one story/branch, failed requested turn, revision0, zero events/receipts,
no draft or projection rebuild, and one potion owned by the player. Pristine
and working main bytes remain unchanged; working-sidecar immutability is not
claimed. No device SQLite open or model call was used for recovery.

## Final bindings and limits

I rehashed every selected entry in all five indexes bound by the
[safe aggregate](TRACED_SDK_RESULTS_2026-10-23.json): author 13, qualification
48, device 1,515, extended replay 14 and root checks 11. Sizes, counts and
SHA256 values match with zero discrepancies. These selections overlap and are
not a count of distinct files. The final reviewed aggregate is **9,800 LF bytes**,
SHA256 `da53320fba3d8f9acc084cbb404cc98e3391e6be7bd48acfdfe04c3d0341d10e`.
Committed blob `eb08780` independently matches those exact workspace bytes.
Its outcome, phase, replay, storage and preservation projections match retained
records. Public JSON/prose contain fixed synthetic categories and hash bindings,
without private paths, nonces, device identities, raw journals or model bytes.
The [verification](TRACED_SDK_VERIFICATION_2026-10-23.md),
[device report](TRACED_SDK_DEVICE_2026-10-23.md) and
[protocol](TRACED_SDK_PROTOCOL_V1.md) preserve the same distinctions.

Both prior failed workspaces, the separate phase journal, original model/cache
metadata and other package identities were preserved. Final maps are A21/B23;
A received metadata reads only. No post-SDK whole-model hash was taken, so
final model preservation is a metadata observation. The new failed turn and
cache remain retained. There was no retry, model copy/download, budget change,
emulator lifecycle action, private payload publication or merge/release.

Successful director/schema response, narration, committed gift, phone/ARM
execution, model quality, sustained memory/thermal behavior and production
runtime selection remain unqualified. The earlier crash cause remains unknown.
The useful next step is bounded timeout diagnosis from retained observations
and host prompt/profile inspection, before proposing another freshly admitted
control. M01.03/M01.05 remain partial, with owner acceptance pending.
