# Independent Android control review — 2026-10-22

Scope: M01.02/M01.05, synthetic controller tests only. The reviewer owns
`benchmarks/test_android_control_review.py` and this report in separate branch
`review/m01-control`, initially based on `91d2ec2` (#37). The coordinator owns
implementation and device experiments. Earlier review branches and worktrees
were preserved. This review neither accepts the milestone nor chooses a runtime.

## Reproduced baseline failures

Command: `python -m unittest discover -s benchmarks -p test_android_control_review.py -v`.
Against `91d2ec2`, all 11 independent tests failed: nine assertions and two
uncaught thread-start exceptions. The run took 0.037 seconds; no ADB command,
runtime, model, emulator, physical phone, or network request was executed by
these tests.

- SDK request publication and instrumentation launch occur before package stop
  and process-absence proof. A package identity that changes at the second hash
  check cannot authorize force-stop, but the baseline has already published the
  request and launched instrumentation.
- A surviving SDK process makes cleanup fail, yet the baseline result retains
  generated text and metrics. The same problem occurs when an initially clean
  package cannot be stopped after a completed generation.
- A controlled launcher that starts only after host cancellation records its
  launch **after** the baseline's final package stop. Process absence observed
  before a late launch is insufficient cleanup evidence.
- Native setup failures do not distinguish an inference process that was never
  launched from an ADB client whose cleanup is unknown. Verified drained setup
  failures leave known UUID-owned files behind. Unknown transfer cleanup must
  instead preserve those files until the writer is known drained.
- Both SDK and native `Thread.start()` errors escape their guards. The native
  path has already created its run directory at that point. The synthetic
  exception carries a canary to make accidental exception-text exposure visible.

All failures were reported to the coordinator before fixes. The tests use a
controlled clock and bounded synthetic event waits for cancellation ordering;
they do not infer Android process behavior from host-client termination.

## Additional review and verification after fixes

The coordinator supplied `f87e02b`, `adf581a`, and `0737845`; these were
cherry-picked into the review worktree without changing production files here.
Additional regressions reproduced two in-progress faults: an unclean file-removal
ADB client incorrectly retained earlier ADB cleanup proof on both paths, and
native error recovery let an `OSError` from cancel-marker publication escape.
The latter was reproduced as an uncaught exception against `adf581a`. A separate
SDK launch exception lacked its primary failure stage. The final coordinator
commit repairs these cases.

Final independent checks at reviewed implementation `0737845`:

| Command | Actual result |
| --- | --- |
| `python -m unittest discover -s benchmarks -p test_android_control_review.py -v` | 19 tests pass, 0.135 seconds |
| `python -m unittest discover -s benchmarks -p test_android_runtime*.py` | 28 existing controller tests pass, 0.040 seconds |
| `python -m py_compile benchmarks/test_android_control_review.py` | Pass |
| `git diff --check` | Pass |

The final tests cover known versus unknown setup-client cleanup; exact owned-file
removal without deleting an uncreated directory; separate process, ADB, and file
cleanup outcomes; initial and final SDK stop/absence; APK identity changes;
launch and cancellation ordering; both thread-start and launcher exceptions;
attempt accounting; and bounded, typed public diagnostics. Malicious stage
strings, lists, dictionaries, boolean counts, nonfinite values, and oversized
integers cannot expose the synthetic canary or crash metadata projection.
Noncompleted SDK results discard generated text and SDK metrics.

No remaining concrete acceptance or ownership failure was found within this
synthetic review scope. This is evidence assessment, not owner acceptance or
proof of actual Android process cleanup. Device fault probes and recovery belong
to the coordinator's separate evidence. Original device transients remain
unexplained until supported by causal evidence; passing regressions or fresh
successful attempts do not explain them. Physical-phone feasibility and the
full M01 exit gate remain outside this review.
