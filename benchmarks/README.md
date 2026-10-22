# Feasibility helpers

These tools prepare M01; they do not implement real inference or establish phone
support. Run them from the repository root. Python uses only its standard
library. PowerShell requires an existing Android platform-tools installation for
device discovery and never prints serial numbers.

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
No completed-turn statistics exist yet.

Read [the source/device report](../docs/runtime/FEASIBILITY_2026-10-22.md) and
[bounded evaluation protocol](../docs/runtime/EVALUATION_PROTOCOL.md) for exact
pins, schema/fixture dependencies, data format and remaining gates.
