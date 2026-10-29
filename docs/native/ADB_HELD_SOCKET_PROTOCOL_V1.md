# Held ADB socket ownership, protocol v1

Implementation decision for M10.02, supporting M09.06/M01.01. Explicit protocol
identifier: `adb-held-socket-server-owner-v1`. This is separate from legacy
LISTEN2/SDK2 and the unimplemented dual-ESTABLISHED proposal. No fallback,
historical reclassification, model/device qualification or product-policy change.

The fixed source-owned socket stays open with the same handle/object and exact
local/peer endpoints throughout the observation and exchange. One pre-send
complete native OWNER_PID_ALL view must contain exactly one matching server
reverse tuple, admitted PID and raw ESTABLISHED5. It must also contain exactly
one reciprocal client tuple/own PID; its raw state is preserved without a state5
gate for every DWORD equally. This uses positive server connection ownership;
it does not reinterpret listener0/client0 as another state. Missing, conflicting,
duplicate or foreign matching rows refuse before sending.

The client-table state is an extra consistency observation. A successful new
proof must not claim dual-ESTABLISHED or LISTEN2 evidence. The held resource and
reverse tuple provide the join; a correct reply alone supplies no ownership.
This inference assumes a trusted local OS, one declared network view and source
controlled socket lifetime. It is not cryptographic or process-code attestation.

## Frozen Python interfaces

Root owns `benchmarks/adb_held_socket.py`, with no import-time IO:

```python
PROTOCOL = 'adb-held-socket-server-owner-v1'
REQUEST = b'000Chost:version'
MAX_SECONDS = 3.0

@dataclass(frozen=True, slots=True)
class TableCapture:
    family: int
    raw: bytes
    allocated_bytes: int
    table_class: int = 5

@dataclass(frozen=True, slots=True)
class Snapshot:
    tables: tuple[TableCapture, TableCapture]  # exact IPv4 then IPv6
    abi_checked: bool = True

class ProbeRefused(ValueError):
    reason: str  # fixed categories; never provider text or private paths

def validate_admission(value: dict) -> dict: ... # exact deep copy or refusal
def probe(backend, admission: dict) -> dict: ... # retained success/refusal/cleanup
```

Admission has exactly `version` (exact int1), `protocol`, `server`, `adb_file`,
`candidates`, `expected_version`. `server` is exactly `{pid, creation_filetime,
executable}`. `adb_file` is exactly `{path, bytes, sha256, identity}`; identity
is a five-int list `[st_dev, st_ino, st_size, st_mtime_ns, st_ctime_ns]`, with
size equal to bytes. This is the **path API** identity. Windows Python can report
different ctime values through path stat and descriptor fstat for the same file;
do not equate those observations. Both must retain their exact five-int values
before/after each read. Backend descriptor identity additionally stays equal
across all brackets. Join the two APIs using exact dev/inode/size/mtime plus
explicit `st_birthtime_ns`; birth time must exist, agree and remain stable in both
APIs, otherwise refuse. Full bytes/hash and admitted path identity remain required.
Executable/path must agree exactly and be absolute Windows
paths to the existing installed tool. Expected version is exactly four lowercase
hex characters, selected before execution, never learned from the response.

Candidates is a nonempty, unique, sorted list of at most two exact objects:
`{family, address, port, pid, scope_id}`. It permits only IPv4/127.0.0.1 or
IPv6/::1, port5037, scope0 and admitted PID; IPv4 is required. Raw state is not
candidate identity. Observed candidates are local5037 rows with remote
unspecified/port0 or rawLISTEN2; LISTEN remote fields are undefined and ignored.
Every local5037 row must have an admitted loopback address/scope/PID, including
accepted connections. Extra wildcard/foreign/scoped/duplicate candidates refuse.
This roster is the captured API view, never a claim of global absence.

Backend interface (only the Windows implementation performs IO):

```python
now() -> float                              # monotonic
open(admission, deadline) -> None            # own/server held process handles
bracket(admission, deadline) -> dict          # exact keys below
snapshot(deadline) -> Snapshot               # one sizing+read per family, no retry
connect(deadline) -> None                    # create/connect one own socket once
endpoint(deadline) -> dict                   # same resource, exact keys below
send(data: bytes, deadline) -> None           # single fixed request, once
recv(limit: int, deadline) -> bytes            # clamp timeout to deadline remainder
close() -> dict                              # exact socket/process closure flags
```

Bracket is exactly `{server, client, adb_file, held_processes_alive}`. Server/file
must equal admission; client has the same process schema, remains equal across
all brackets and differs from server. Held handle liveness, native identity and
fresh PID observations must agree. File pin includes stable open/path identities
and full hash, rejecting byte-identical replacement. Cross-API ctime equality is
not a file-identity requirement; each API's ctime stability is. The same binding
rule applies to CLI reads of hash-bound private JSON. Endpoint is exactly
`{handle, socket_id, local_address, local_port, peer_address, peer_port}`, with
positive integer handle/id, local127.0.0.1:allocated-port, peer127.0.0.1:5037;
local port differs from5037. Backend exposes no socket object/borrow/transfer.
Close returns exactly `{socket_closed, process_handles_closed}` as exact booleans.
It must attempt every owned close even if another close fails.

Ordered orchestration: validate admission; start total3-second deadline; open;
initial bracket + candidate snapshot; connect once; endpoint; **one** pre-send
snapshot and join/candidate checks; endpoint + immediate bracket; fixed send;
bounded fragmented receive (at most13 bytes including trailing detection), exact
`OKAY0004` + admitted version + orderly EOF; final endpoint, process/file bracket
and candidate snapshot; finally close every owned resource. All snapshot calls
are fixed by stage; no favorable polling, reconnect or resend. Every operation
checks the remaining total budget, never a fresh per-byte deadline. Noninterruptible
native calls also sit inside the CLI's bounded worker/job owner.

`probe` returns an exact versioned report with admission, ordered stages, fixed
intended request, actual send/completion fields, partial response, ownership and
client raw state, elapsed time, resource flags, fixed refusal reason and
`feature_acceptance=false`. It retains failures. No report alone authenticates
execution; the CLI additionally requires source/request pins and known owner
cleanup/capture before labeling the narrowly scoped server proof verified.

CLI is explicit `python -B -m benchmarks.adb_held_socket_probe --admission
<bound JSON> --admission-sha256 <digest> --output <missing physical D directory>`.
It creates only private physical-D evidence outside any Git ancestor, uses D:
TEMP/TMP, pins its full source closure/installed Python and has a30-second owner.
Invalid admission/output refuses before dispatch. No ADB CLI, device/transport
selection, server lifecycle, emulator operation or settings change is permitted.

## Evidence obligations

Tests independently vary client state without changing ownership outcome and
reject every server state other than5. They challenge every identity/tuple,
complete family roster, bounds/ABI, ambiguity, process/file/handle replacement,
partial/fractured/wrong/FAIL/trailing response, absent EOF, cancellation, source
mutation, deadlines and cleanup. Legacy suites remain unchanged. A fake backend
or fake server tests plumbing only. A real host-only probe is a separate measured
result after source/tests/assurance review, not implied by this decision.

Microsoft documents the [owner-PID tuple/state fields](https://learn.microsoft.com/en-us/windows/win32/api/tcpmib/ns-tcpmib-mib_tcprow_owner_pid).
AOSP's pinned [host service implementation](https://android.googlesource.com/platform/packages/modules/adb/+/fe344857fc92ff4f1b16d77b086c7dd59aec1828/adb.cpp)
and [client](https://android.googlesource.com/platform/packages/modules/adb/+/ec7028fb5c2cde5c18522dd08f7c34c5e668fc83/client/adb_client.cpp)
establish framing/finite service behavior and explain why the lifecycle-recovering
CLI is excluded. Source-backed protocol versions do not attest the installed
binary. No dependency or runtime/model version is selected by this host tool.
