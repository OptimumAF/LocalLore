# Read-only physical phone inventory, version 1

Refs #5 (M01.01, supporting M01.05); #14 (supporting M10.03).
This explicit host tool supports future phone qualification. It neither
installs an app nor copies/loads a model, changes a setting, stops a process,
starts a service or runs arbitrary commands. Gameplay is unchanged.

The ordinary ADB executable can restart a mismatched shared service. This tool
uses fixed socket requests and the existing held Windows process/file/socket
owner instead. It does not reuse an emulator lease or create an emulator.
It depends on the separate [roster protocol](HELD_DEVICE_ROSTER_PROTOCOL_V1.md).

## Admission and request sequence

```text
python -B -m benchmarks.physical_phone_inventory_probe --admission <existing D: JSON> --admission-sha256 <sha256> --output <missing D: directory>
```

Admission has exactly `version`, `protocol`, `server`, `adb_file`, `candidates`,
`expected_version` and `authorized_serial`. Protocol is
`physical-phone-inventory-v1`. The first six fields retain the held service's
strict process creation, executable identity/hash, loopback5037 candidates and
expected version requirements. The serial is a declared exact retained target;
the file and its hash are not themselves human authorization. A coordinator
must separately establish the applicable user authorization before execution.
Do not recover missing authority by selecting a similarly named model.

One source-bound worker performs version, roster and inventory in that order.
The version/roster retain their existing three-second exchange limits. Only a
fully qualified roster and its embedded version proof can precede inventory;
all three must identify the same actual worker. The authorized serial must
match exactly one online `device` row with product/model/device metadata.
Otherwise inventory opens no connection and sends no request. Roster metadata
remains private and untrusted; devpath and power fields do not prove USB type.

The inventory exchange holds one new socket throughout:

1. Prove its original endpoint, held/fresh process and executable identities,
   and a unique admitted-server reverse ESTABLISHED5 connection plus reciprocal
   current-client tuple before sending `host:tport:usb`.
2. Read `OKAY` and the native 64-bit transport ID. Compare it with the exact
   authorized roster row **before sending any device service**. The server's
   selector requires one USB transport; there is no fallback selector.
3. On that same socket, repeat the ownership bracket before the code-fixed
   `shell,v2,raw:` inventory request, and require its `OKAY` acknowledgment.
4. Repeat the ownership bracket before the fixed empty close-stdin packet.
   Receive only bounded stdout/stderr/exit packets, successful exit and orderly
   EOF, then retain the final bracket and close all owned resources.

The original rows remain the inputs to every live ownership join. Only the
exact qualified closed version/roster endpoints receive the existing narrow
history treatment. There is no arbitrary ignored-port list, generic PID0
exception, poll-until-favorable behavior, reconnect, command retry or clock
extension. The new inventory exchange is bounded to20 seconds; its worker to45.
Unknown cleanup refuses qualification.

TPORT returns native `TransportId` bytes, not a hex string or length-prefixed
payload. This implementation targets little-endian Windows and is not a
portable host-endian wire definition. Same-socket selection avoids a second
selection/reconnection gap; cached serials and IDs are not cryptographic phone
or hardware attestation. The trusted local OS/service remains an assumption.

## Fixed inventory and private evidence

The source owns every outgoing byte. JSON cannot supply a shell command,
script, operation, backend, target fallback or stdin. The fixed shell first
requires user0, then reports seven identity properties, page size,
MemTotal/MemAvailable, `/data/local/tmp` free blocks/block size, selected battery
fields and thermal status. No serial, property or other roster value is
interpolated into the command.

The decoder requires the fixed ordered `LLPI_V1` sections, exact property keys,
bounded text/numbers, consistent units and ranges, a valid page size, complete
memory/battery/thermal fields and no emulator property claim. Returned facts
preserve observed values; low memory, thermal load or unplugged power are not
rewritten into eligible values. Facts do not assert installed-package/APK state
or satisfy the existing model pre-install admission contract.

Wire cap is65,536 bytes, stdout32,768, stderr4,096 and packet count256. Server
packets must be stdout, stderr or one one-byte successful exit. Nonempty stderr,
truncation, unsupported channels, duplicate/post-exit packets, nonzero exit,
missing EOF and trailing bytes refuse. Receive bytes are retained before
post-read deadline/resource checks; an expired or otherwise refused read does
not become successful because its bytes are available.

Private reports distinguish attempted sends from known completed sends. A
false completion flag after an attempted write does not prove zero bytes.
Target mismatch before a service attempt does prove that the tool did not
attempt its inventory service. Reports retain raw bounded wire, selected TCP
rows, typed facts, prior proofs and cleanup; public output contains only fixed
status categories. Full table hashes/counts do not imply retained whole tables.

The CLI pins project source closure, interpreter/runtime, admission, actual
parent/worker, started receipt and all report/sidecar files before and after.
Only fixed code imports instantiate the three backends, after the worker gate.
Report consistency cannot authenticate its own acquisition. Known owner exit,
complete captured streams, stable pins and real worker identities are separate
requirements. A fake transport or forged JSON does not establish phone access.

## Compatibility and qualification limits

Primary AOSP revision
[`1cf2f017d312f73b3dc53bda85ef2610e35a80e9`](https://android.googlesource.com/platform/packages/modules/adb/+/1cf2f017d312f73b3dc53bda85ef2610e35a80e9/)
defines the [USB TPORT selection](https://android.googlesource.com/platform/packages/modules/adb/+/1cf2f017d312f73b3dc53bda85ef2610e35a80e9/adb.cpp)
and fixed shell protocol. The current source review is not installed-binary,
device or runtime attestation. No SDK/runtime/model dependency is introduced.

Battery USB power does not prove charging status; thermal and identity fields
are software observations and may be overridden on a modified device. Filtered
`dumpsys` pipelines expose the last pipeline status rather than independently
attesting every upstream process exit. Strict complete facts are still required.
Free space at the sampled path is not an app-volume reservation. Installation,
package/APK hashes, actual memory/thermal qualification and real local inference
remain separate checks.

Actual phone execution requires retained exact authorization and fresh target
admission. The earlier empty roster is a closed historical observation; do not
poll it repeatedly or infer global phone absence. Existing emulators, shared
service lifecycle, settings, failed captures and recovery remain preserved.
