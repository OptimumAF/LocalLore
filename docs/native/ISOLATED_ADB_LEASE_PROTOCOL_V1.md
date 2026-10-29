# Isolated owned ADB lease, v1

M10.02 supporting M09.06/M01.01. Explicit protocol `isolated-adb-lease-v1`.
This controls a NEW foreground child at127.0.0.1:15937, never shared5037. It is
not an SDK2/SDK3 fallback and cannot reinterpret their failed consistency proofs.
Native TCP states remain opaque recorded DWORDs, with no ESTABLISHED/LISTEN
claim. Positive identity instead requires the actual newly launched child/job,
fresh private endpoint ownership and reciprocal held client tuples. A reply
alone is never admission. Trust assumptions include the local OS and byte-pinned
installed binary; JSON metadata does not authenticate itself.

## Startup scope and source evidence

Only the coordinator may consume the existing owner authorization for a fresh
local service on a verified unused port, without touching any existing service
or emulator. A machine-readable admission is not human authorization. V1 is a
host-only readiness lease: no device registration, emulator boot, target command,
model operation or automatic discovery. Importing, parsing or planning starts
nothing. Explicit `run` starts only after all gates and independent tests.

Installed baseline is ADB1.0.41/37.0.1-15733141, SHA256
`b4a6b455702684652cccf7b46258b29e653538904359a58fd4931cf3ef286b3f`.
Pinned AOSP `1cf2f017d312f73b3dc53bda85ef2610e35a80e9` and
`9084198a2d4b0f6a0f174260fb42da33485b684d` show the direct startup guards.
Release37.0.1 changes the Windows USB backend; neither a bogus `--one-device`
selector nor old libusb defaults proves isolation. Use these exact process-local
values, regardless of inherited SDK/developer settings:

```text
ADB_USB=0
ADB_EMU=0
ADB_MDNS=0
ADB_MDNS_AUTO_CONNECT=0
ADB_LOCAL_TRANSPORT_MAX_PORT=0
ANDROID_ADB_LOG_PATH=<admitted root>/adb.log
TEMP=TMP=TMPDIR=D:\Dev\_Temp
```

Remove inherited keys beginning `ADB_`/`ANDROID_` and obsolete aliases before
adding this exact map. In particular remove ADB_VENDOR_KEYS, never set it empty
as a substitute. Do not export environment changes to the caller or system.
Foreground argv is exactly `[adb,-L,tcp:127.0.0.1:15937,server,nodaemon]`.
Never invoke start-server, fork-server, kill-server or an ordinary SDK command.
The fixed foreground route bypasses daemon launch and preserves stderr/stdout in
bounded private capture. All log/temp paths remain physically D:.

Windows ADB uses SHGetFolderPathW(CSIDL_PROFILE)/.android/adbkey; HOME and
ANDROID_USER_HOME are not proven redirects. Require the existing directory and
regular nonempty key, with the actual native profile path. Hold a checked native
read handle denying write/delete throughout the lease, allow ADB's read-only
load, compare file identity/metadata before and after, and close that handle
explicitly. Refuse missing/replaced/reparse key or missing directory before
launch. Never read/copy/hash key contents, generate keys or change permissions.
This is existing OS authentication state permitted in its normal C: location,
not project source/output. Missing stat causes key generation in AOSP; parse
failure after successful stat does not regenerate. No credential bytes go into
receipts or recovery. Normal before/after metadata and fixed path stay private.

## Frozen shared Python interfaces

Root owns `benchmarks/isolated_adb_lease.py`; owner specialist owns only
`benchmarks/isolated_adb_owner.py`; independent adversaries own only
`scripts/tests/test_isolated_adb_lease.py`. Separate branches/physical D worktrees.

```python
PROTOCOL = 'isolated-adb-lease-v1'
PORT = 15937
class LeaseRefused(ValueError): ...
def validate_admission(value: dict) -> dict: ...  # strict deep copy
def server_command(admission: dict) -> list[str]: ...
def child_environment(admission: dict, inherited: dict) -> dict: ...
def source_bindings() -> list[dict]: ...
def validate_running(value: dict, admission: dict, admission_binding: dict) -> dict: ...
def check_stop(value: dict, admission_sha256: str) -> None: ...
def validate_observation(value: dict, server: dict, client: dict | None,
                         endpoint: dict | None, *, require_empty=False) -> None: ...
```

Admission exact keys: `version`=1, `protocol`, `run_id` (32 lowercase hex),
`root` (new absolute physical-D output outside Git), `port`=15937, `seconds`
(exact int30..1700), `adb` (byte binding), `tools` (six sorted byte bindings for
adb.exe/AdbWinApi.dll/AdbWinUsbApi.dll/libwinpthread-1.dll/source.properties/
NOTICE.txt in the same installed platform-tools folder), `sdk_version`
=`37.0.1-15733141`, `expected_version`=`0029`, `sources` (complete sorted source
bindings), `python` (executable/runtime_dll bindings), `auth_key` (absolute native
profile key path), `capabilities` (bound offline version/help result),
`source_review` (bound official-source review). Bindings are exactly
`{path,bytes,sha256}`. Processes are exactly `{pid,creation_filetime,executable}`.
No source report, flag, hash or supplied key path grants authority by itself.
The live owner revalidates actual byte/source/profile/capability/OS path inputs.

Running exact keys: `version`=1, `protocol`, `admission` (byte binding), `run_id`,
`port`, `owner`, `worker`, `server` (three distinct actual process identities),
`started_epoch`, `deadline_epoch`, `sources`, `adb`, `version_proof`, `devices_proof`
(bound private proof JSONs). Deadline minus start equals admitted seconds;
clock checking/ongoing lease liveness remains the live client's obligation.
Do not infer ongoing readiness from this saved descriptor after termination.
Server executable equals admitted adb; owner/worker equal admitted Python.
`check_stop` accepts exactly `{version:1,protocol,admission_sha256,action:'stop'}`.
Stop acts on the held new child/job only; no PID-text kill or daemon command.

Observation exact keys: `version`=1, `port`, `rows` (list of at most64 selected
rows), `families`=[2,23]. Each row has exactly `family`, `local_address`,
`local_port`, `remote_address`, `remote_port`, `local_scope_id`, `remote_scope_id`,
`state`, `pid`, `ordinal`, `raw_hex`. Decode raw24/56-byte Windows OWNER_PID_ALL
layout independently and require exact field agreement. Retain only local15937
rows, plus reciprocal client-local rows when endpoint is supplied; never retain
unrelated tables. Unknown state values stay raw. Both family snapshots must be
complete/ABI checked in live capture, not inferred from this scoped record.

Empty preflight requires no selected rows. Ready observation requires exactly
one listener-local candidate (remote unspecified/port0) for admitted server PID
and127.0.0.1/zero scopes, no other candidate/wildcard/IPv6/private-port owner.
With endpoint, additionally require exactly one reciprocal server tuple/serverPID
and client tuple/clientPID; do not select by expected state. Endpoint is exactly
`{local_address,local_port,peer_address,peer_port}`, loopback, peer15937, local
positive/distinct/non5037. All other local15937 rows remain recorded; live
foreign nonzero PID refuses. PID0 teardown rows may be retained only after a
request, without asserting ownership or current connection state for them.
Pre-send proof may not hide ambiguity with a PID filter.

## Owner and fixed readiness flow

Parent saves a source/request/admission/Python-bound private request. Launch one
trusted Python worker under the existing finite job supervisor. The worker waits
for BOTH its binary start barrier and parent's actual `started-v1.json` matching
its own PID/birth/executable before any auth/port/server action. This closes the
legacy late-announcement race without changing that supervisor. Parent callback
creates that receipt; a missing/malformed/mismatched receipt times out before
server startup. Parent budget admitted seconds+30, maximum1730 seconds.

Worker locks existing auth key, checks no IPv4/IPv6 row on15937, confirms an
exclusive loopback bind and closes only its own preflight socket. Then starts
exact foreground ADB under the already assigned inherited job. Hold its Popen
process handle, exact native identity and byte pins. Bound readiness wait10s
may wait only for that actual child to bind; record each selected observation.
Conflicts/changed identity or source refuse immediately, never connect another
candidate. Kernel raw state is not a readiness selection or label.

Two direct smart-socket exchanges only, each with its own held client socket and
total3-second budget: `000Chost:version` -> exact`OKAY00040029`+EOF, then
`000Ehost:devices-l` -> exact`OKAY0000`+EOF. Before sending require actual
process/file brackets and reciprocal tuple ownership; after exchange keep the
same client resource, record final observation and require server/listener and
lease identity unchanged. Preserve fragmented bytes/deadline/closure, no whole
request retry/reconnect/polling for a favorable proof. Empty devices proves only
that observation, not all future transport exclusion or device qualification.

Save `running-v1.json` only after both proofs pass. Loop on finite monotonic
deadline, actual server identity/liveness, source/auth guards and exact stop
file. Close only the held child with Popen.terminate/wait, drain/join/close every
owned pipe and capture, release auth handle, record actual return code. A
requested termination need not produce server exit0; do not fabricate one.
Every failure still attempts owned cleanup, retains captures and poisons the
lease. Parent closes its own job on every exit and validates worker/source
evidence independently. No blanket unchecked CloseHandle success assertion.

V1 device/model/target actions remain zero. Future SDK/guest integrations require
their own explicit target/lease/current-build admission; they cannot use an
expired descriptor, automatic SDK server recovery or this host-only proof as
phone/model acceptance.
