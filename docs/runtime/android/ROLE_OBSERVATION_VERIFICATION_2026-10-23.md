# Role observation verification, 2026-10-23

Refs [#5](https://github.com/OptimumAF/LocalLore/issues/5), M01.04/M01.05 partial,
claim `6375456753`. Exact base is open/unmerged
[#116](https://github.com/OptimumAF/LocalLore/pull/116),
`a5a0fae10743c0132ff68285faca9a7333f454c3`.

The old ordinary-gift first-output flag was unmeasured because its assignment
was inside the cancellation-case branch. False did not prove no callbacks or
buffered text. The prior timeout, owner cleanup and failed-turn/revision-zero
replay remain valid; its sealed aggregate and raw evidence are unchanged.
The preceding verification/review and PR #116 now carry the explicit correction.

## Implemented and tested boundary

The [protocol](ROLE_OBSERVATION_PROTOCOL_V1.md) defines strict optional per-role
observations for ordinary and cancellation cases. Callback activity, buffered
bytes, first-observation timing and requested configuration remain separate
from validated output, gameplay token budgets and canonical state. Optional
metrics are read only after known drain before Conversation close. Expected
linkage failures remain unavailable; unexpected Errors still trigger native
cancellation/join and known owner closure before propagation. Unknown close
ownership requires process termination. First callback rejection categories
survive later cancellation errors without changing primary text validation.

The host validates the complete extended schema before reusing the unchanged
canonical receipt validator. Invalid diagnostics retain raw bytes and yield an
unknown terminal; they cannot turn a committed-looking result into a safe retry.
Only the separate qualified artifact admits this schema. Three older artifact
pins retain their original parsers, and readback admits only the old traced and
new role-observation artifacts. No runtime/model/dependency, native library,
permission, canonical schema or workload budget changed.

## Host and artifact evidence

Actual commands:

```powershell
python -B -E -m unittest discover -s scripts/tests -v
python -B -E -m unittest discover -s benchmarks -v
python -B -m unittest discover -s benchmarks/spike/android/litert -v
```

Final **360 script tests passed** (5.014 seconds); **140 benchmark and 34
SDK-helper tests passed** at the earlier integrated source. Relevant helper
sources were unchanged afterward. SDK-helper checks used a dedicated D-volume
temporary directory. The new 17 script methods cover strict observations,
ordinary/timeout metadata, malformed accepted-looking terminals, preserved
receipts after outer errors and the separate final reader pin.

The [author report](ROLE_OBSERVATION_AUTHOR_2026-10-23.md) records actual
focused JVM checks and two fresh offline builds. The first qualified artifact
passed 123 JVM tests but was superseded before installation after review found
sticky-error and Error-cleanup gaps. All its bytes remain retained. The corrected
build at `604cb991ade7cb922ef3c89b08e6a296ecab4b4b` passed **132 JVM tests,
zero failures/errors/skips**. These selections overlap and are not added.

Gradle ran `:app:assembleDebug :app:testDebugUnitTest :app:lintDebug
:app:auditLintAnalyzer`: 50 tasks executed, build success in 41 seconds. The
corrected qualification controller completed in **44,390 ms**, exit 0, no stderr,
known cleanup. Lint: **0 errors, 9 existing warnings** (OldTargetApi 1,
GradleDependency 1, UsableSpace 7). Locked dependency/analyzer metadata,
package/runner, zero permissions, JNI exports, ELF and ZIP 16-KiB alignment
passed. All four final native library entries match the prior traced artifact;
no new Rust native compilation or ARM execution occurred. Native provenance
remains `ba31932665eab2079c54a02a0182857f598fa0c4`, schema 2; this does not
qualify a newer native build. Before/after qualification APK inputs matched.

Qualified APK: **63,666,936 bytes**, SHA256:

```text
9417a3e914975918d018c8a7d8954f192c09e40e10320b08c86be8a50fd7217f
```

The reviewer independently checked all 107 combined qualification entries,
132 actual XML results, native bytes and parser pins. Root independently
rehashed every author (23), source-fix (16), official-source (21) and combined
qualification (107) selected entry, with zero mismatches. Official pinned-source
review establishes only a best-effort alive benchmark path; cancelled-session
counts may fail or be incomplete, and zero may be a default. It does not prove
schema enforcement or identify a timeout cause.

The author disclosed a private evidence-location mistake: new followup logs
and an unbound compiled-class cache were initially added to the earlier author
namespace. Its 23 indexed source/log entries and index stayed unchanged; the
new evidence was copied to a fresh fix namespace and the additions preserved.
The index seals selected files, not an immutable whole directory.

## Actual emulator observation and failed cohort

Separate author, device and review worktrees retained explicit file ownership;
the coordinator integrated contracts, SDK adapter, host parsing, canonical replay
and publication. The device specialist ran only the centrally admitted new
controllers and authored its [report](ROLE_OBSERVATION_DEVICE_2026-10-23.md).
The independent [review](ROLE_OBSERVATION_REVIEW_2026-10-23.md) performed source,
artifact and evidence reads, with no device/model execution.

Preparation completed **67,672 ms / exit 0 / known cleanup**. All **382** recorded
commands completed with known cleanup. Two complete local source-model integrity
passes matched 2,588,147,712 bytes / SHA256 `181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`
in 22,313 ms. Only B's isolated cacheprobe APK updated from the old traced pin to
the new qualified pin; UID/app-root, A21/B23 package maps, original model metadata
and all retained failed workspaces/journals/cache metadata matched through
preparation and the pre-inference check. No model was copied. The selected
API35/x86_64 emulators were ready; inventory showed four emulators/zero other
devices. A received metadata reads only. The dangling-symlink absence guard was
fixed before admission; 14 private host-only controller regressions passed.

Exactly one new nonce-bound B gift ran after a fresh app-domain full model hash
and live storage/backing admission. The critical driver completed with known
cleanup in **122,562 ms**, but **exit 2**, with a retained closure assertion.
The SDK control itself took **92,203 ms** and reported a structured director
timeout. This is an observed failed experiment, **not a passing cohort**.

| Measured boundary | Actual result |
|---|---|
| Primary outcome | Failed / timeout; 1 director, 0 narrator, 0 repairs; model initialized |
| Director load / generation | 8,726.0237 / 49,043.3789 ms |
| Output observation | Observed; 15 Java message callbacks, 56 buffered UTF-8 bytes |
| First positive observation | 46,075.8019 ms upper bound from role start; not SDK TTFT or final-response latency |
| Terminal callback category | `generation_failed`; no generated text copied into diagnostics |
| Optional SDK snapshot | Available; SDK-reported 1,855 input / 16 output tokens, incomplete cancelled-turn semantics apply |
| Configuration | Schema/thinking-disable requested, nonempty template; cap350, prompt7111/schema355 UTF-8 bytes; no enforcement proof |
| Cancellation / resources | Cancel call28.8084ms, terminal callback acknowledged, owner drained; Engine1/1, Conversation1/1; no termination-required flag |
| Post storage | Blocked `host_consumption_budget`; overall `check_passed=false` |
| Readback | 27 checkpoints, terminal/none, fresh reader, one exact exit-instance match; reason10/status0 after controller stop |
| New snapshot | 65,536-byte main, all three sidecars absent, before/after facts stable |
| Strict Rust copied-snapshot replay | Passed250ms/exit0/knowncleanup; schema2/FK/one story/branch; failed turn/revision0/zero events or receipts; player retains1potion |

The snapshot SHA256 is
`fea955219d41d9fecedafd3934cfda82a335f8c9e53b058f24cb0b15e32a4019`.
Replay opened only a separately created local working copy, invoked no model,
and preserved every pristine file and the working main database bytes. Its
canonical conclusion is independent of diagnostic output and storage verdicts.
Legacy aggregate SDK token totals remain default zero for this failed role;
they are not measurements of zero generation and do not override the optional
raw per-role counters. Buffered bytes do not establish a valid final proposal.
No cause is inferred from the exit record or the callback category.

## Storage and preservation failures retained

SDK post-sampling was valid but failed the unchanged host-consumption bound.
C-volume free space fell from **12,667,879,424 to 10,284,752,896 bytes**, a net
2,383,126,528 bytes, exceeding the C/userdata-host 64-MiB allowance. This is host-wide observation;
its cause is not attributed to the app. Cache growth was **788,412,770 bytes**;
userdata net consumption90,112 bytes. No bound was relaxed. Fresh app/model
identity and initial admission do not turn this post-run failure into a pass.

The cohort's final preservation function stopped on B's old guarded-cache
metadata comparison. Local analysis of already retained output found a changed
directory inode and the 34-byte owner marker's mtime/ctime shifted back one
second. The model stat and two generated-cache-file metadata rows matched.
No marker/cache payload hash had been captured, and the cause remains
**unestablished**. The assertion and raw bytes are preserved; the result was not
rewritten or repaired. Final package maps still matched A21/B23, and A's metadata
comparison completed, but full post-run old-database/journal preservation,
final storage and final inventory checks did **not** complete. The new snapshot
capture and its known-owner/absence conditions completed before that assertion.
They establish the new turn's replay result, not preservation of older sessions.

All **711** recorded commands (382 preparation +329 critical) had known client
cleanup: 22 expected absence exit1 probes and one intentional remote-exit37
control are retained. Separate host metadata clients and the two outer drivers
also had known cleanup. No device calls followed the closure failure. There was
no inference retry, model copy/download, AVD lifecycle change or A write/inference.
The new turn/cache and all prior evidence remain retained. Post-inference whole
model integrity was not rehashed; final model observations were metadata only.

## Evidence, limits and next runnable task

The [safe aggregate](ROLE_OBSERVATION_RESULTS_2026-10-23.json) is **12,321 LF
bytes**, SHA256 `9235a18aaa707194bbc6f46842308e3423fdbaf3c32481c52be2392b72db8358`.
It includes actual failures and independent canonical replay, with no private
nonce, unique process identity, user path, model text or database/journal payload.
Private selected-file indices bind raw evidence without uploading it.

M01.04/M01.05 are **in_review, partial**, not accepted or checked. The central
measurement bug is fixed and real buffered output is now evidenced despite the
timeout. Physical-phone M01.01 remains **blocked**; successful guarded generation,
narration, quality, sustained memory/thermal, ARM execution and production
runtime/profile acceptance remain unqualified. No phone/performance/backend
selection follows from this single emulator attempt.

Next runnable task: host-only analysis of the retained storage/cache metadata
boundary and director timing before proposing another control. Preserve all
failed turns and evidence; no further inference is admitted by this packet.
Fresh device ownership/capacity and preservation gates are required before a
later separately reviewed experiment. Tickets own status and work-log history;
retired Markdown trackers remain pointers. No merge, release or access/protection
change is part of this packet.

### Private selected-file integrity checkpoints

These bind selected local files, not whole immutable directory trees. Selections
overlap and are not added as unique evidence counts. Root rehashed every entry;
the independent reviewer also checked source/build, command, snapshot and replay
selections. No private payload is published.

| Selection | Files / selected bytes | Index bytes / SHA256 |
|---|---|---|
| Initial author | 23 / 93,307 | 4,081 / `e47862b3dc7a9840437e91a5c74ee3db9c7912fd1f2590e7ac3fd5df3d9d3edc` |
| Source-fix author | 16 / 108,312 | 2,967 / `dba428f3d33237d94494d27307b669e00b8af8504c8bdc7b6af0dca48744dcd5` |
| Official-source review | 21 / 901,889 | 4,004 / `3b7eeece6da10296654e8b1f11b968439d8c59f43ad7e7c8790092bea01cd34b` |
| Combined qualification | 107 / 279,486,028 | 27,048 / `44eba5ceddfa6d263607be341a61bafb55b61f7301f0cf5145f30144f9a1abbd` |
| Device controls / retained failures | 1,530 / 1,345,878 | 272,853 / `cb676ad461d2038e3c533ce10bbafc3049a047d76562e2c843bbc77b023f8b8a` |
| Copied-snapshot replay | 12 / 4,721,551 | 2,627 / `acd26d5a3196fab8c2a59ffec485634a869861900d46ece6d4f83049979f1563` |
| Host checks / root rehash receipt | 10 / 104,739 | 1,621 / `f3e9db586034384fa99aeaf3ca4bec8357b76b0974910387cac7b4dfe906078b` |
