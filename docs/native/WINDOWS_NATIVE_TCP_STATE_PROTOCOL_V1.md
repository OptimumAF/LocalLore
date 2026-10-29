# Independent native TCP state control, v1

M10.02 supporting M09.06/M01.01. Diagnostic identifier:
`windows-native-owned-tcp-state-v1`. This separates a compiled Microsoft-header
API path from the previous Python FFI path. It is not an ADB admission protocol,
SDK fallback, model benchmark or replacement for any existing gate. Prior
failed captures and their interpretations remain unchanged.

## Fixed experiment

Compile `benchmarks/native/windows_tcp_state_control.c` as x64 C11 with the
installed Microsoft compiler and Windows SDK headers/libraries; no new library
or package. Root records actual source/tool/header/library/command and resulting
binary pins. Do not label a supplied binary SHA as source/build authentication.
The public launcher additionally binds its actual started process and source
closure; the admitted build remains the executing parent's responsibility.

The executable accepts no arguments and requires exactly the start barrier
`LL_NATIVE_TCP_STATE_V1\n` on binary stdin. Binary stdout holds one finite JSON
report plus newline; no unrelated rows, process paths or table buffers are
printed. Explicit launch has a30-second owned subprocess/job and complete
bounded binary capture. No import or build runs the diagnostic.

Worker creates only its own exclusive IPv4 loopback listener on port0, then one
client and accepted socket. Require assigned ports positive/distinct and not5037;
never connect an existing endpoint. Set finite socket send/receive timeouts.
Three phases are fixed: `after_listen`, `connected`, `exchanged`. Each records
SO_ACCEPTCONN and exactly four queries in order: `owner_listener`, `owner_all`,
`basic`, `owner2`. They mean GetExtendedTcpTable(AF_INET,OWNER_PID_LISTENER=3),
GetExtendedTcpTable(AF_INET,OWNER_PID_ALL=5), GetTcpTable and GetTcpTable2,
respectively. Each query has one sizing call and one data call, never a retry.
Bounds: allocation/returned buffer at most1MiB, count at most16,384, rows begin
at offsetof(table,table)=4 with strides24/24/20/28. Verify ABI from the installed
native structure definitions and compile-time assertions, not custom structs.

Retain every IPv4 row whose local address is127.0.0.1 and local port is the
listener or assigned client port, irrespective of state/PID. Do not prefilter by
expected state or PID. At most eight selected rows per query; excess refuses.
Each selected row retains its original count-delimited ordinal and raw bytes.
Do not retain unrelated native tables. Candidate-state interpretation and the
unknown-state rules remain unchanged.

After the connected snapshot, client sends exactly `LL_NTCP_CONTROL1!` (17 ASCII
bytes), accepted socket reads all17, echoes all17, client reads all17. Handle
partial send/receive with finite total10-second worker budget; do not reconnect,
resend an entire payload or retry an experiment. Then take exchanged snapshot.
Always attempt all owned socket closes and WSACleanup, recording actual masks
and outcomes. Child timeout/unknown closure stays failed; process termination
must not be presented as checked explicit socket closure.

## Exact report schema

Top-level keys are exactly:

```text
version                 exact int1
protocol                windows-native-owned-tcp-state-v1
pid                     positive DWORD
creation_filetime       positive 64-bit native GetProcessTimes value
abi                     object below
listener_port           int0..65535, positive on completed acquisition
client_port             int0..65535, positive on completed acquisition
stages                  fixed ordered prefix of phases, complete on success
exchange                object below
resources               object below
acquisition_completed   exact boolean
reason                  null on success, otherwise one fixed category
elapsed_ms              nonnegative integer from native monotonic clock
```

`abi` has exactly `owner_pid`, `basic`, `owner2`. Each has exactly `row_bytes`,
`row_offset`, `field_offsets`. Values respectively are24/4/[0,4,8,12,16,20],
20/4/[0,4,8,12,16],28/4/[0,4,8,12,16,20,24]. Values are emitted using actual
sizeof/offsetof expressions and checked independently by the Python reader.

Each stage has exactly `stage`, `acceptconn`, `queries`. Each query has exactly
`name`, `initial_code`, `final_code`, `allocated_bytes`, `returned_bytes`, `count`,
`rows`. Codes and sizes are exact nonnegative DWORDs; success needs initial122
(or0 with a valid nonzero allocation), final0 and bounded complete count/stride.
Each row is exactly `{ordinal:int, raw_hex:lowercase hex of exact stride}`.
Ordinals must be unique, increasing and less than count. Decode raw DWORD state
unchanged at offset0; addresses and low16-bit ports are network order. owner2
additionally retains the offload DWORD; basic has no observed PID.

`exchange` has exactly `client_sent`, `server_received`, `server_sent`,
`client_received`, `server_hex`, `client_hex`. Counts are int0..17, hex strings
represent exactly the actually received prefixes (max17 bytes). Full success
needs all four counts17 and both complete hex strings equal to fixed payload.

`resources` has exactly `created_mask`, `close_attempted_mask`, `closed_mask`,
`winsock_started`, `winsock_cleanup_attempted`, `winsock_cleanup_succeeded`.
Bit1 is listener, bit2 client, bit4 accepted. Masks are exact ints0..7; attempted
is a subset of created, closed a subset of attempted. Full success needs all
masks7 and all three exact booleans true. Incomplete startup retains zero masks
and actual flags; absence is not an invented successful close.

Refusal categories: `barrier`, `identity`, `abi`, `startup`, `socket`, `bind`,
`listen`, `connect`, `accept`, `endpoint`, `api`, `exchange`, `deadline`, `cleanup`.
Partial refusal stages/queries may be prefixes; the launcher preserves raw
stdout even when a partial report cannot qualify. No error text/unknown code
can become acquisition success. Native exit0 means completed acquisition with
explicit closure, not consistent states; a refused acquisition exits1.

## Closed reader and acceptance

Root owns `benchmarks/windows_native_tcp_state.py`:

```python
PROTOCOL = 'windows-native-owned-tcp-state-v1'
class NativeControlRefused(ValueError): ...
def assess_report(raw: bytes, expected_process: dict) -> dict: ...
```

Reader is pure, import-safe and bounded (report512KiB). `expected_process` is the
actual owner's `{pid,creation_filetime,executable}`; only the first two fields
are asserted by the native report. Parent/source/binary/tool/owner pins are
additional launch/build evidence, never inferred from metadata. Reject duplicate
JSON keys, wrong exact types/keys, malformed hex/ABI/rosters, unowned selected
rows, impossible count/stride bounds, swapped tuples and foreign PID. Basic
rows supply tuple/state consistency only. Do not claim PID ownership for them.

Assessor returns an exact summary: `version`=1, `protocol`, `feature_acceptance`
=false, `acquisition_completed`, `observation_consistent`, `listener_states`,
`connection_states`, `selected_rows`, `resources_closed`. It accepts only a full
success-shaped report with known actual identity and closure. Inconsistency is
a valid acquired diagnostic result, never service admission. Listener states
are12 ordered integers (four queries per phase); connection_states is6 ordered
objects `{stage,query,server,client}` for connected/exchanged × owner_all/basic/
owner2, preserving every DWORD. Every listener path must uniquely contain the
listener tuple; every all-connection path must uniquely contain the reciprocal
owned connection tuples, with exact PID where supplied. Consistency requires
all listener raw states2, all server/client connection states5 and acceptconn1.
Unknown values remain raw and yield observation_consistent=false.

Independent synthetic/adversarial tests must cover those distinctions and fixed
resource/command/source/capture limits before the ONE actual native control.
Old decoder/control/held/SDK3 suites remain unchanged. Only a measured compiled
control can distinguish the native path from prior Python observations; no
favorable test fixture, build or source review establishes that result.

Microsoft references: [GetExtendedTcpTable](https://learn.microsoft.com/en-us/windows/win32/api/iphlpapi/nf-iphlpapi-getextendedtcptable),
[OWNER_PID row](https://learn.microsoft.com/en-us/windows/win32/api/tcpmib/ns-tcpmib-mib_tcprow_owner_pid),
[GetTcpTable2](https://learn.microsoft.com/en-us/windows/win32/api/iphlpapi/nf-iphlpapi-gettcptable2),
[getsockopt](https://learn.microsoft.com/en-us/windows/win32/api/winsock2/nf-winsock2-getsockopt).
