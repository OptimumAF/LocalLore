# Feasibility helpers

These tools prepare M01 and do not establish phone support. The inventory and
aggregate tools use Python's standard library; PowerShell device discovery
requires existing Android platform-tools and never prints serial numbers.
The separate [runtime spike](../docs/runtime/spike/README.md) can explicitly run
verified local models through reviewed development runtimes. Default tests use
fake subprocesses and SDK mocks, with no model/runtime installation or download.

```powershell
python -m unittest discover -s benchmarks -p 'test_*.py' -v
powershell -NoProfile -File benchmarks/inspect-device.ps1
python benchmarks/summarize_runs.py <reviewed-completed-turns.jsonl>
```

The probe returns nonzero while physical hardware is blocked/ambiguous; it may
start the local ADB daemon. It filters known emulators and does only bounded
read-only inventory commands. It never selects a device for a benchmark or
modifies device data. `MemTotal` is kernel-visible memory, not confirmed retail
physical RAM. Inspect and redact output before saving it publicly.

The aggregate calculator keeps host/physical and cold/warm/sustained profiles
separate and refuses fake-provider traces. Its unit tests contain invented
numbers. It is not the application's turn engine or a semantic evaluator. Keep
failures/incomplete attempts and their denominator in the full benchmark report.
The narrow host spike has compatibility observations, separate from this
calculator and the physical-device/full-turn evaluation protocol.

Read [the source/device report](../docs/runtime/FEASIBILITY_2026-10-22.md) and
[bounded evaluation protocol](../docs/runtime/EVALUATION_PROTOCOL.md) for exact
pins, schema/fixture dependencies, data format and remaining gates.
