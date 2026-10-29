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

## Windows TCP observation controls

`windows_tcp_observation.py` is a pure bounded decoder for native owner-PID
IPv4/IPv6 table bytes. It preserves unknown states and IPv6 scope IDs. Its
`has_listen_state` flag requires raw state2; it does not qualify a service.
Callers must check the native ABI before decoding live tables.

The opt-in Windows control below creates only its own short-lived IPv4
loopback listener, client and accepted socket. It compares bound, listening
and connected observations across four native query paths and exchanges one
fixed17-byte payload. It does not connect to ADB or invoke SDK/device tools.
Run from a physical D: checkout with a new output directory outside Git:

```powershell
$env:TEMP='D:\Dev\_Temp'; $env:TMP='D:\Dev\_Temp'
python -B -m benchmarks.windows_tcp_control --output D:\Dev\Experiments\LocalLore\tcp-control-new
```

Keep the private output: it contains local process and selected socket metadata.
Existing directories, reparse paths, repository ancestors and Windows path
aliases refuse before dispatch. The bounded owner retains request/source pins,
worker capture, raw selected rows and resource closure. Unrelated table rows
are not written. The command returns0 for consistent observations,2 for acquired
but inconsistent observations, and1 for acquisition failure. Every outcome has
`feature_acceptance=false`; even consistent owned controls do not qualify ADB,
an emulator, a phone or inference. See the
[actual verification and remaining gate](../docs/native/WINDOWS_TCP_CONTROL_VERIFICATION_2026-10-28.md).
