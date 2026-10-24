# Traced guarded SDK verification, 2026-10-23

Refs [#5](https://github.com/OptimumAF/LocalLore/issues/5), M01.03/M01.05
partial, claim `6374988994`. Exact base is open, unmerged
[#115](https://github.com/OptimumAF/LocalLore/pull/115),
`731b46cfc818a17e15140d466c403e1f1c1a51b2`. This packet extends the isolated
experiment; production inference and Rust canonical rules are unchanged.

## Implemented boundary

The [readback protocol](TRACED_SDK_PROTOCOL_V1.md) adds the existing-session
`read_phase` operation before volume/model/native/SDK setup. It validates the
fixed owner and full bounded journal without creating or repairing anything.
Optional Android exit-query exceptions discard partially enumerated values.
Unknown close ownership still requires process termination.

The host play controller accepts a caller-persisted private nonce. The separate
reader controller admits only the new artifact, requires original namespace
absence, retains raw bytes before parsing, and binds APK/UID around reader
cleanup. Cleanup uncertainty revokes verification without erasing observations.
The strict decoder rejects duplicate/nonfinite/extra JSON, old probe wrappers,
probe phases, mismatched roles, impossible one-row summaries and inconsistent
exit counts. SDK results, diagnostic observations and canonical replay remain
independent; none may silently override another.

## Actual host and artifact qualification

Commands actually run:

```powershell
python -B -E -m unittest discover -s scripts/tests -v
python -B -E -m unittest discover -s benchmarks -v
python -B -m unittest discover -s benchmarks/spike/android/litert -v
```

Final results: **343 script / 140 benchmark / 34 SDK-helper tests passed**.
The SDK-helper selection used a dedicated D-volume temporary directory.
The 22 new script methods include full SDK phase/role combinations, exit-data
coherence, invalid nonce early refusal, exact selected-session dispatch, real
artifact pin binding, original-process refusal, large bounded process inventory,
raw retention before failed/oversized output, unknown-client fencing, sink
failure and replacement APK/UID cleanup refusal. Independent review found the
impossible one-row generation summary; its regression test now passes.

The [author report](TRACED_SDK_AUTHOR_2026-10-23.md) records two focused JDK runs,
each **36 tests**, and fresh offline Android qualification with **105 JVM
tests, zero failures/errors/skips**. These selections overlap. Gradle executed
`:app:assembleDebug :app:testDebugUnitTest :app:lintDebug :app:auditLintAnalyzer`;
50 actionable tasks executed successfully in 38 seconds. The bounded outer
controller completed in 42,000 ms, exit0, known cleanup.

Lint: **zero errors / nine existing warnings** (OldTargetApi1,
GradleDependency1, UsableSpace7). Locked dependency/analyzer metadata,
package/runner, zero permissions, native inventory/export and 16-KiB ELF/ZIP
alignment audits passed. The new APK is **63,666,936 bytes**, SHA256:

```text
f4d247f3e24c302a7e8d2431d7ee8c9fccc476909c0d82789ea1f84083ddfd81
```

Java inputs are bound to `5123c3c42a74479b6f23509fe0dd6b634edb208f`; actual build
orchestration is `e8ef8e77e74570ea1ceb9d6dfa54f25753847361`. The intervening
controller commit changes no APK inputs; all 35 input hashes matched before and
after. Later artifact-pin and documentation commits do not alter Java inputs.
All four packaged native libraries are byte-identical to qualified `0cf4c253...`.
The two Rust binaries were extracted from that full hash-verified APK; native
source is `ba31932665eab2079c54a02a0182857f598fa0c4`, with only a subsequent
integration-test delta excluded. No new native compilation or ARM execution is
claimed. Runtime/model/profile/schema2 are unchanged.

The actual target was Android API35/x86_64, LiteRT-LM Android0.18.1 revision
`bda624851d74be34d4e1f7fac1fc4155939539c7`, Gemma4 E2B at the pinned hash,
CPU4 threads, context4096, director350/narrator220 tokens, one repair, shared
60-second turn deadline, 90-second app watchdog and 110-second play client.
No dependencies were introduced or upgraded; existing official-source/runtime
provenance and license records remain applicable. Emulator execution does not
establish phone or ARM support.

Retained qualification refusals precede the successful build: a requested
600-second controller budget was refused before spawn, and an exact-HEAD guard
refused the next attempt before output creation. The successful controller
explicitly bound both source revisions and retained the existing 180-second
maximum. No budget or test assertion was relaxed.

The build index binds **48 selected files**, including JVM XML, lint/analyzer
metadata, source fingerprints, prior-artifact/native provenance, controllers,
refusals and the frozen APK. Independent review rehashed every file, parsed all
11 test suites and inspected all four actual ZIP library entries.

## Actual emulator preparation

The preparation cohort completed in **63,187 ms**, exit0, known cleanup. All
**376 recorded commands** completed with known cleanup; three exit1 responses
were expected process-absence probes. Inventory showed four emulators and zero
other devices. A received metadata reads only. Its 21-package map matched; B's
23-package map changed only the explicitly selected cacheprobe APK.

Fresh process/backing graph, independent physical host-volume identity, storage
and original-data preservation gates passed before installation. Two complete
read-only passes through one held local model handle covered **2,588,147,712
bytes**, matching SHA256
`181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`.
The fingerprint and all repeated chunk hashes matched. Source verification took
23,218 ms; it is integrity timing, not inference performance.

B was updated from `0cf4c253...` to `f4d247f3...` with `install -r -t`.
The UID, app-root identity, original model/cache metadata, both old SQLite
workspaces and sidecars, and existing separate phase journal matched before,
after and at closure. No model copy/download, app instrumentation invocation,
SDK call or AVD lifecycle action occurred during preparation. Guest userdata available bytes
were 1,674,694,656 before and 1,674,502,144 after installation. Host C available
bytes were 8,475,906,048 before and 8,474,816,512 after. Independent D capacity
afterward was 325,075,374,080 bytes. These are observations, not reservations.

## One actual guarded SDK attempt

After separate admission, the critical cohort completed in **124,687 ms**,
exit0, known cleanup. Its **338 commands** completed with known cleanup.
Fresh app-domain verification read the full fixed model leaf and matched its
expected size/hash immediately before the single selected-session gift. This
operation opened zero SDK Engines or Conversations. No cached integrity receipt
substituted for the actual app read.

The requested gift **failed with a director timeout**. Android returned a valid
structured terminal and reported model initialization, one director call, zero
narrator calls, zero repairs, no observed first-output callback and drained
ownership. SDK counters show one Engine and one Conversation opened/closed,
acknowledged cancellation and terminal callbacks, and no termination-required
flag. Cancellation-call timing was 67.3024 ms. The model-load observation was
7,524.4987 ms and the timed-out generation observation 50,703.7637 ms; token
counts are unavailable. These emulator observations do not qualify a phone or
successful generation. The controller's 92,953-ms wall time includes measurement
and integrity work and is not a complete-turn latency benchmark.

Transport, storage and stopped-process checks passed; the requested gift check
correctly remained **false**. The worker's `completed` status means it returned
its structured result, not that gameplay succeeded. Canon remained revision0
with zero receipts according to that result. The original result was preserved
independently of later diagnostic and recovery observations. No inference retry,
profile/token/context/repair/deadline change or smaller workload followed.

Storage admission passed before and after the SDK control. Cache grew
**788,412,770 bytes** within the unchanged 1-GiB observation allowance, from
1,576,825,574 to 2,365,238,344 bytes. Userdata net consumption was 139,264 bytes;
external-cache available bytes afterward were 3,619,602,432. These remain
nonreserving measurements, not a proven cache maximum.

## Phase readback and canonical recovery

One stopped-session `read_phase` passed: **27 checkpoints**, last `terminal`,
role `none`, fresh reader, one examined exit record and one exact process-instance
match, numeric OS reason10/status0. The controller had already stopped the SDK
process; this record is not evidence of a crash cause. The reader was separately
hash/UID-bound, stopped and proven absent before capture. It invoked no model,
SDK or native engine, and its journal result did not establish canonical state.

Qualified shell-v2 exit37/all-byte controls preceded the new stopped-workspace
capture. The main database is **65,536 bytes**, SHA256
`e16975473712cc1663bbf9e6c2c2274f50345018b374e88cf46d4680cf2c8aba`;
WAL, SHM and rollback-journal leaves were absent. Source owner/facts/hashes matched
before and after, with known client cleanup and full package namespace absence.

The coordinator used the previously qualified read-only Rust helper on a
create-new working copy. It completed in **62 ms**, exit0, known cleanup, and
validated schema2, foreign keys, one story/branch, strict accepted-history replay
and requested-turn status. Canonical result: **failed turn, revision0, zero
accepted receipts/events, player owns one potion**; no projection rebuild or
draft remains. The pristine snapshot and working main file were unchanged. No
device SQLite open, migration, repair, model call or original-session mutation
was used for recovery. Working-copy sidecar immutability is not claimed.

All **714 recorded device commands** across the two cohorts had known cleanup.
The old failed turns, prior phase journal, original model/cache metadata and all
other package identities were preserved. The new timed-out turn is retained.
No further device commands or SDK attempts followed the critical cohort.
The seven separately recorded host metadata clients also completed with known
cleanup. Device exits included 22 expected absence probes returning1 and one
intentional remote-exit control returning37. Final available bytes were
8,430,669,824 on C, 324,255,764,480 on D and 1,674,469,376 on B userdata.
No post-SDK full model hash was performed; post-run preservation is metadata
evidence rather than renewed model-content integrity proof.

## Evidence bindings

The [safe aggregate](TRACED_SDK_RESULTS_2026-10-23.json),
[device report](TRACED_SDK_DEVICE_2026-10-23.md) and
[independent review](TRACED_SDK_REVIEW_2026-10-23.md) contain fixed synthetic
categories, counts and numeric observations. Private session nonces, PIDs,
process identity, raw diagnostics, checkpoints, database payloads and model
weights remain outside GitHub. No post-run inference retry was used to obtain
a favorable result.

The coordinator and independent reviewer rehashed all bound entries in these
immutable private indexes. Counts are per selected index; repeated references
across indexes do not imply distinct files.

| Selection | Entries / bytes | Index SHA256 |
|---|---|---|
| Focused author | 13 / 48,214 | `f6c178ed3006a7af2595a8457e0c70def90e963aaf8ce10959a2e60a7ea8217f` |
| APK qualification | 48 / 139,690,183 | `48d6fc2c521f04897f21c8b1a3236413081fd053c41f3dd45cb56aa2536fdb57` |
| Device cohorts | 1,515 / 1,135,954 | `01ed9984f0f0dc1b9883f06f3417e8575b923623c0f5dbf9261e6ce1b5815445` |
| Strict replay and snapshots | 14 / 4,725,902 | `220198ee27d15a7c03aa87d11cdaa03334d3f978e1cb5cff281a5942f5dbfcd2` |
| Root tests and rehash receipts | 11 / 100,242 | `5e2d5bf419fd39aeefd437578641477d1e822bf977394641bbf355e417be3314` |

The safe aggregate is **9,800 canonical LF bytes**, SHA256
`da53320fba3d8f9acc084cbb404cc98e3391e6be7bd48acfdfe04c3d0341d10e`.
It binds all five selected indexes using counts/bytes/hashes, without private
paths or payloads. The additional replay index extends the first ten-entry
selection to include exact pristine/working main bytes and the source manifest.

## Limitations and next task

This establishes bounded real model initialization, timeout cancellation and
resource drain, stopped-session diagnostics, and no canonical mutation after
this failure. It does **not** establish a successful guarded director response,
narration or committed gift. It cannot explain the earlier SDK crash. Semantic
quality, successful complete-turn latency, sustained memory/thermal behavior,
ARM execution and production runtime/profile selection remain unqualified.

M01.03/M01.05 remain partial and unchecked pending full criteria and owner
acceptance. M01.01 remains blocked without an authorized physical phone; A has
no fresh inference/write admission. No merge, release, repository-access change,
private-payload upload, model copy/download or AVD lifecycle action occurred.
Retired Markdown trackers remain pointers; ticket comments own progress.

Next runnable task: diagnose the director's bounded no-output timeout using
these retained phase/SDK observations and host-side prompt/profile inspection,
before proposing another freshly admitted real-model control. Preserve this
failed turn and the existing workload budgets; do not automatically retry it.
