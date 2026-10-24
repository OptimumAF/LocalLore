# Isolated Python cleanup-test bootstrap diagnosis, 2026-10-23

Refs #7 M03.05 partial; supporting #85 integration qualification. Coordinator
approved a bounded diagnosis and then the test-only correction. Claims:
[#7 comment 6370445264](https://github.com/OptimumAF/LocalLore/issues/7#issuecomment-6370445264),
[#85 comment 6370445655](https://github.com/OptimumAF/LocalLore/pull/85#issuecomment-6370445655).
Only `benchmarks/test_runtime_spike.py`'s failed-cleanup watchdog method and
this new report are owned by this packet.

## Failure and attribution

The coordinator's full `scripts/check.py host --offline` run at retention
source `58ce35` reached the 140-case benchmark group and failed
`ProcessOwnershipTests.test_cleanup_failure_with_live_readers_returns_without_close_deadlock`.
The previous `check=True` raised `CalledProcessError` without exposing the
captured child stderr in that unittest report.

The independent reviewer reproduced that exact method using the actual
task-local Python `3.14.9 (tags/v3.14.9:ead82c0, Oct 21 2026, 06:26:14)`
`[MSC v.1944 64 bit (AMD64)]`, Windows NT `10.0.26300.0`. An untracked diagnostic
wrapper caught the exception and recorded actual child exit1, empty stdout,
and this stderr:

```text
Traceback (most recent call last):
  File "<string>", line 4, in <module>
    import runtime_spike as m
ModuleNotFoundError: No module named 'runtime_spike'
```

This occurs **before constructing a WindowsJob or spawning the sleeping
synthetic worker**. The portable interpreter has `sys.flags.isolated == 1`
and `safe_path == True`; its existing `python314._pth` contains only
`python314.zip`, `.` and a commented `import site`. The fixed child's cwd is
not an implicit import location in this observed configuration.

`git diff --exit-code 59fa8e8..58ce35 -- benchmarks/runtime_spike.py
benchmarks/test_runtime_spike.py` returned0. The integration and accepted
baseline bytes are identical for both files; no retention causality or
Python language/runtime defect is established. This was a pre-existing test
bootstrap assumption exposed by the isolated portable interpreter.

## Minimal correction

Source-only fix `4c2de9a54e66c07010fa5fbe4d9612490122a295`:

- The parent passes its resolved, trusted `runtime_spike` module directory
  as a fixed argv entry. The fixed synthetic child inserts that entry into
  its own `sys.path` before importing the module.
- A nonzero child exit now fails an explicit assertion containing at most
  4096 captured stdout bytes and 4096 stderr bytes. Failure is not accepted,
  retried, downgraded to a skip or hidden by JSON parsing.
- The 15s outer watchdog, .1s inner deadline, elapsed <14000ms assertion,
  `cleanup_failed`/`clean == false` assertions, empty-stderr assertion and
  original real-job release in `finally` are unchanged. No product job
  ownership code, production budget, environment variable, global `._pth`,
  Python install, model or worker configuration changes.

The untracked diagnostic's preliminary explicit-import experiment returned
exit0, stdout `{"status":"cleanup_failed","clean":false,"elapsed":9120}`,
and empty stderr under the original assertions. It is separate from the
actual committed-source checks below.

## Actual checks and retained evidence

Executed from the separate `source-d08-design` checkout with the task-local
Python3.14.9 executable, `-B`, fresh task-owned D-drive `TEMP/TMP`; no model,
device, ADB, app/desktop operation, process enumeration or unrelated process
control. The test launches only its fixed Python child and owns its Windows
job cleanup.

```text
python.exe -B -m unittest discover -s benchmarks -p test_runtime_spike.py -k test_cleanup_failure_with_live_readers_returns_without_close_deadlock -v
1 test PASS, 9.280s

python.exe -B -m unittest discover -s benchmarks -p test_*.py
140 tests PASS, 10.614s

git diff --check
PASS
```

Private task-local `retention-process-diagnosis/` logs are retained:

| Attempt | SHA256 |
| --- | --- |
| `python314-first.log`, original actual failure | `d0d8c3b88700ba2d5408f4f0f5746e4a7a4f275d5c011020db6e602c2426477b` |
| `python314-explicit-import.log`, preliminary experiment | `da1abbb1ae231ec84690e01f88828858d79ec6faf84b80efaf8f7d7e794f69b0` |
| `python314-source-fix.log`, final exact test | `507f30ab58050133cd5b1b39e5692d3b0d5672a16ee7f8fc3148980aef2c03c8` |
| `python314-full-benchmarks.log`, final 140-case group | `1d4a7013fceb003ce3800f3b1f03ea6bdbbfa57c9718ec14ef3c9d004600c578` |

Unchanged product `benchmarks/runtime_spike.py` SHA256:
`237ae7a2fcc2469b27f79c4266e2e45f653d4e5b09af7009a4299dee31e73816`.
Original test SHA256:
`b658f8dc29059e118160193ca7824cb7cebc5ae6a5dce6175e77b340842368f5`.
Corrected test SHA256:
`2ce43c697b4966d5b6806bd447b402651838b614c4fb8112ddb44adc377862c2`.

This packet does not claim the complete host gate: the coordinator will rerun
it on the integrated source. No source change was made to the concurrent
workspace/checker writer's files. This bounded passing synthetic watchdog is
not proof of all process-cleanup incidents, real runtime/model behavior,
device ownership or physical performance, and closes no milestone checklist.
