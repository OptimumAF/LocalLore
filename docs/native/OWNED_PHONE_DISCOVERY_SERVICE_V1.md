# Owned phone discovery service, version 1

Refs #5 (M01.01, supporting M01.05); #14 (supporting M10.03).
This is a development harness, not a gameplay service or supported-device claim.
It addresses the missing existing-service prerequisite without restarting any
existing ADB service. Local play remains independent of host tooling.

## Two explicit profiles

| Protocol | Port | USB | Readiness exchanges | Lifetime |
|---|---|---|---|---|
| `isolated-adb-lease-v2` | 15937 | Disabled | Exact version and empty roster | 30–1700 seconds |
| `owned-phone-discovery-service-v1` | 5037 | Enabled | None; native ownership readiness only | 30–120 seconds |

Both reuse the existing foreground owner and fixed installed tools. A protocol
selects one literal port; there is no arbitrary command, port or backend selector.
Old captured results retain their original source/protocol attribution.

The new mode enables ordinary USB discovery and authentication. It does not
select an authorized phone or grant installation, model or device commands.
The [roster CLI](HELD_DEVICE_ROSTER_PROTOCOL_V1.md) performs its own fresh version
and roster exchanges while the owned service is alive. The file-only
[identity workflow](PHONE_IDENTITY_ENROLLMENT_PROTOCOL_V1.md) then creates a
private review proposal; a human must explicitly choose the intended candidate.
No candidate is selected automatically.

## Startup and ownership

The existing metadata-only authentication guard must open the installed native
profile's existing private key with write/delete sharing denied. Our code does
not read, hash, copy, generate or relocate credential contents. Missing or
uncertain authentication metadata refuses before startup. The SDK still performs
its normal authentication work; do not equate a host metadata guard with device
permission or authentication of JSON records.

Before launch, capture both native TCP families and refuse every existing row
on the selected port, including wildcard and IPv6 entries. An exclusive IPv4
loopback bind must succeed and close. The foreground child must then match the
held executable/process identity and actual native listener. Any port race,
unexpected client or ownership mismatch refuses; never kill an occupant or try
another port automatically. The parent/worker start receipt, source/runtime/tool
bindings, deadlines, output capture and owned cleanup remain required.

The exact new command is:

```text
<pinned installed adb.exe> -L tcp:localhost:5037 server nodaemon
```

Remove inherited ADB/Android control variables and obsolete aliases. Set only
process-local `ADB_USB=1`, `ADB_EMU=0`, `ADB_MDNS=0`,
`ADB_MDNS_AUTO_CONNECT=0`, `ADB_LOCAL_TRANSPORT_MAX_PORT=0`, the private log path
and D temporary directories. The old profile retains `ADB_USB=0`. Do not invoke
`start-server`, `kill-server`, version-mismatch recovery or a shell command.

Phone-mode readiness sends no host frame: its running record must have both
`version_proof` and `devices_proof` explicitly null, and its closed worker must
have exactly zero proofs. The actual running-file binding and full owner,
worker, server, source and deadline joins are still required. The old profile
continues to require both verified proofs; missing evidence is not optional.
Stop records bind the actual admission hash and protocol. Only the owned child
is terminated; unknown cleanup cannot qualify the lease.

Active emulator scanning and mDNS discovery are disabled. A running emulator
may independently register with a newly available default server. This harness
does not promise transport invisibility and must not stop that emulator or
change its settings. Ordinary USB discovery may contact attached phones before
the later identity choice; no zero-contact claim is made.

## Official compatibility evidence

The existing pinned baseline is ADB 1.0.41 / Platform Tools 37.0.1-15733141,
SHA-256 `b4a6b455702684652cccf7b46258b29e653538904359a58fd4931cf3ef286b3f`.
No dependency is added or updated. The current
[official release notes](https://developer.android.com/tools/releases/platform-tools)
describe the Windows libadbusb default and its legacy opt-out. This harness
keeps that default; legacy `--one-device` behavior is not used as an isolation
claim. Exact installed binary-to-source provenance remains unproven.

Pinned AOSP `9084198a2d4b0f6a0f174260fb42da33485b684d` provides the relevant
[startup guards](https://android.googlesource.com/platform/packages/modules/adb/+/9084198a2d4b0f6a0f174260fb42da33485b684d/client/main.cpp),
[emulator scanner](https://android.googlesource.com/platform/packages/modules/adb/+/9084198a2d4b0f6a0f174260fb42da33485b684d/client/transport_emulator.cpp),
[authentication initialization](https://android.googlesource.com/platform/packages/modules/adb/+/9084198a2d4b0f6a0f174260fb42da33485b684d/client/auth.cpp)
and [legacy Windows USB ordering](https://android.googlesource.com/platform/packages/modules/adb/+/9084198a2d4b0f6a0f174260fb42da33485b684d/client/usb_windows.cpp).
The max-port variable alone is insufficient: scanner startup precedes its
override, so the direct emulator startup guard remains required. The legacy USB
backend opens endpoints before filtering a serial; a SetupAPI interface path is
not a supported substitute there. These observations guide the scope and do
not assert that a private port isolates USB access.

## Verification and storage

Implementation is subject to original mocked profile/ownership/fault tests and
the unchanged host-only lease tests. Code compilation, host tests and actual
device execution are separate evidence. A bounded live attempt requires fresh
admission after source/test review; importing or validating metadata starts
nothing. A refusal spends that attempt without an automatic fallback or retry.

Private scripts/captures and recovery live under physical D in the
`2026-10-30-phone-service-v1` experiment/recovery directories. Expected storage
is 0.15–0.35 GiB, capped at 512 MiB including three source trees and recovery.
No emulator, guest image, model, APK or credential contents are copied. Earlier
failures and frozen worktrees remain retained. Full M01/M10 acceptance, physical
inventory, inference, restart and model qualification remain separate gates.
