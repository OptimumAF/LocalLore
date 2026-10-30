# Retirement executor: host verification

Date: 2026-10-30. B27, M10.02 / supporting M09.06: implemented and locally
verified, in review. Full milestone criteria and owner acceptance remain open.
Based on open/unmerged [PR #295](https://github.com/OptimumAF/LocalLore/pull/295),
`3b08da16c9577b6dab18884d295b508a0b7936e8`.

The [operating contract](RECEIPT_AVD_RETIREMENT.md) covers the new coordinator
and Windows held-object backend. The existing finalizer body is extracted into
an internal helper so the original admission lock remains held through deletion
and finalization. Public ledger/tombstone schemas, charging, limits and default
registry are unchanged. No app, Rust, Kotlin, inference or SDK code changes.

## Actual checks and exact attribution

Final executed source is `211c8b47c55db51d60b73bd0b15aa6f0650a8a93`, 2,336
tracked raw inputs. Physical D: commands use TEMP/TMP/TMPDIR `D:\Dev\_Temp`.
Host: Python **3.14.7**, Windows NT **10.0.26300.0**, eight-byte pointers,
observed NTFS D:. Installed tools remain in their existing locations.

| Closed check | Source | Actual result |
| --- | --- | --- |
| First new + legacy cohort | fd401332 | 78 methods; 1 failed assertion + 4 errors across 3 new methods/subtests; all 52 legacy pass |
| Own-child raw API diagnosis | native agent 2e2a2017 | Exit259 retains matching creation time; image-name query fails31 while wait0 is signaled; all owned handles close |
| Corrected new + legacy cohort | 4bb9f040 | 79 unique methods; zero failures/errors/skips/load/audit violations |
| Whole native module, including combined execution | b9d4bab7 | 14 methods pass, including actual nine tiny images / five owned exited processes |
| First complete six-suite Python discovery | b9d4bab7 | 2,595 unique composite IDs pass; all 28 then-current new cases once |
| Whole coordinator module after interruption case added | 211c8b47 | 15 methods pass, including interruption between marks; production bytes unchanged |
| Final complete six-suite Python discovery | 211c8b47 | **2,596 unique loaded/run IDs; all 29 new cases once; zero failures/errors/skips/load/expected/unexpected/audit outcomes** |

The final suite counts are 140 / 10 / 14 / 34 / 13 / 2,385 for benchmarks,
LiteRT, llama, Android LiteRT, Android llama and scripts/tests. A separate
isolated child uses ordinary `unittest.TestLoader.discover(pattern='test_*.py')`
for each existing root, with no filters. The unchanged cases are retained.
The final 900-second Windows process-tree owner closes in **352,220 ms**, worker
exit0, known cleanup/capture, stdout 2,152 / stderr 4,390 bytes, and equal raw
source/helper/runtime pins before/after. The scripts discovery body takes
336,228 ms. This is complete Python regression, not `check.py host`: Cargo,
fmt, Clippy, Android/JVM builds and native linker tests were not rerun for this
Python-only host change.

Private command: `python -I -S -B <packet>/run-python-final-v1.py`.
The capture is `<packet>/python-final-v1`; the preceding 2,595-case capture is
separately retained at `<packet>/capture-v1/python-full-v1`. Both actually pass;
the later added interruption test accounts for the one-case difference.

## What the tests establish

New methods comprise 15 coordinator and 14 native tests. Seven native methods
use actual Windows operations on explicitly created tiny D: files/processes;
the remaining cases use isolated registries and private API simulations or
import/consent checks. These new tests use isolated registries and test-created
files/processes, without production registry or real guest access.

The combined case calls the actual executor, native file/process primitives
and real storage finalizer with no native/verdict mocks. Nine tiny files have
the literal allowed image names; five separately created Python processes are
observed alive, exited and retained through their process handles. The test
verifies all marks, cleanup, exact image absence, preserved original/copy pins,
tombstone, no remaining admission lock and positive independently enumerated
retained charge. Admission/closure JSON is deliberately synthetic; this does
not authenticate a real emulator owner or qualify production retirement.

Original adversaries cover absent/nonboolean consent without I/O, import without
metadata/native calls, stale/typed plan and proof refusals, changed evidence,
continuous lock and durable intent, partial mark/unknown close, sharing/rename/
hardlink/identity/hash/deadline refusals, process numeric bounds, failed wait,
interruption between marks, and truthful commit-versus-output/unlock errors.
Unknown handles are not retried. No recursive/path-wildcard deletion is used.

Each full-suite child has a cooperative Python audit that denies open/listing/
mutation under the real ledger and both registered guest roots and denies
non-D project writes; only the exact stdlib null sink is exempt. Actual violation
lists are empty. This is not an OS sandbox: native FFI, subprocess inheritance,
preopened descriptors and hostile aliases are outside that event guard.
Changed tests were independently source-reviewed for their tiny fixture scope.

## Failures and corrections remain preserved

The original failed cohort is never promoted to a pass. Added image bytes
legitimately increase measured charge; unknown images and changed bound proofs
make charging/admission refuse. The first accounting helper incorrectly required
a fixed numeric charge after those mutations. Its correction requires unchanged
persisted reservation, nondecreasing valid charge, and exact charge **and** new
synthetic-admission refusals for corrupt cases. Production rules remain strict.

The native failure is independently measured with one owned child: after exit259,
OpenProcess/GetProcessTimes succeed with matching birth, image-name lookup
returns error31, and wait0 returns signaled. The corrected predicate requires
that known kernel termination state; it adds no error31 catch or favorable
fallback. Open/times/wait failure and live state still refuse. Executable remains
historical provenance. The original exit259 test remains unchanged, with an
additional known/live/unknown private-API regression. Microsoft documents
[signaled termination and retained object lifetime](https://learn.microsoft.com/en-us/windows/win32/procthread/terminating-a-process)
and [wait results](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-waitforsingleobject).

Pre-run static findings (path metadata during import and an incorrect zero-charge
test oracle) are explicitly source corrections, not invented observed RED.
Original commits, the genuine failed 78-case capture, all corrected captures,
the raw API diagnosis and unrun templates remain retained.

## Independent review and recovery

Independent source review checks ABI definitions, NTFS scope, strict numeric
bounds, lock/mark/close/finalizer ordering and the original tests. Closed file-only
results replay then independently verifies all six actual requests/results,
2,596 unique IDs, all 29 AST-derived new IDs once, zero adverse outcomes, raw
channels/owner counters, runtime/helper pins, every raw source/ZIP member and
distinct historical attribution. It exits0 in **1,084 ms** (974 ms body), without
test/native/device replay or a separately claimed WindowsJob owner.
Receipt SHA-256:
`e6fce8843b8da5bb30448cc97dbbe23c738ddd0c59b1c429dae7afa755139ced`.

Final executed raw sources total **32,321,499 bytes**, preserved/read back before
reporting edits in a **10,361,418-byte ZIP**, SHA-256
`2a02d066878fd9004005b2dd5b3caed8b58d787a7c4fd150b7e871d8cbd6ee16`.
Preserved-source manifest SHA-256:
`2a51929425b65e1dfb5c9d4662d7365777777bf1a16a9e33215c9e1ea28e6105`.
The final complete ID report SHA-256 is
`31ec90c7cbc0327c80d3f42364ebc5b555c5c5e970051849a2524fdbb1535156`.

Original packet:
`D:\Dev\Experiments\LocalLore\2026-10-30-retirement-executor-v1`.
Selected recovery uses the matching `D:\Dev\Recovery\LocalLore` root; final
ticket handoff records source-bundle/archive seals and readback. Original source
trees, prior evidence, guest images and recovery remain in place. The disclosed
1 GiB packet cap includes four source trees, tiny fixtures/captures, source and
selected recovery plus temp/cache allowances. No full ignored-data backup or
exclusive peak/OS quota claim is made.

## Limits and next authorized work

No actual retirement plan is pinned, real image content read/deleted, emulator
created/booted, ADB/device/model called, other emulator stopped, system setting
changed, PR merged or release published. Continue without the phone as requested.
The ten Android UI methods remain unrun; full lifecycle, physical/model/ARM64,
accessibility/privacy, power-loss and release gates remain open. The clock is
cooperative, compatible readers may defer deletion, and multi-file deletion is
not atomic. Trusted local operator/producer assumptions remain explicit.

Next prepare one bounded read-only exact-image proposal and fresh preservation/
ownership checks against the older B26 candidate. Only then request owner
approval for that concrete destructive operation. Real retirement, ledger
planning/finalization and a fresh guest each require their applicable scope and
guarded execution. This implementation grants none of those actions.
