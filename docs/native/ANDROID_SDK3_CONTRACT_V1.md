# Explicit held-server SDK3 bridge

M10.02 supporting M09.06/M01.01. This contract selects a new client and reader;
legacy SDK2, observer defaults, schemas and captures remain unchanged. Host proof
success does not establish device/model acceptance. Product authority and local
gameplay rules do not change.

## Shared interfaces

`benchmarks.android_process_client_v3.HeldServerSdkCapture(directory, seconds,
adb, powershell, admission_binding, launcher_pin=None)` owns one private session.
`directory` is a missing physical-D `clients` folder outside Git, with an existing
parent. Parent files are `sdk-session-v3.json` and `server-proofs-v3/`; both must
be new. Preserve the legacy `target`, `count`, `clean`, `adb`, `shell`, `capture`
conventions. `capture(command,label,seconds=15,cap=131072,*,full_budget=False)`
adds the explicit full-budget gate. `adb` and `shell` accept that keyword too.
No legacy constructor/observer/capture is called. Pure restrictive helpers and
command policy can be reused with an explicit adapter; the old observer command
is always refused.

Root owns `benchmarks.android_process_verification_v3`:

```python
SDK_PROTOCOL = 'sdk-held-server-v3'
BUNDLE_PROTOCOL = 'sdk-held-server-proof-bundle-v1'
class Sdk3Refused(ValueError): ...  # fixed reason, no provider/private text
def sdk_source_bindings() -> list[dict]: ...
def python_bindings() -> dict: ...
def validate_session(value: dict) -> dict: ...
def command_digest(argv: list[str]) -> str: ...
def validate_command(argv, adb_path, transport_id) -> None: ...
def acquire_owned_server_bundle(directory, session_binding, context, seconds: int) -> dict: ...
def verify_owned_server_bundle(binding, expected_session, expected_context) -> bool: ...
def client_record_shape_v3(value) -> bool: ...
def require_current_clients_v3(out, count, expected_session) -> None: ...
def require_host_checks_v3(out, expected_session) -> None: ...
```

`verify_owned_server_bundle` returns True only on full success, otherwise raises
Sdk3Refused. Acquisition returns a bound manifest even for a retained refused
attempt where capture permits; callers MUST verify it before dispatch/return.
It accepts no substitute callback or boolean proof provider. All functions are
import-safe; only explicit acquisition starts an owned host-only CLI.

Session has exact keys `version`=1, `protocol`=SDK_PROTOCOL,
`server_admission` (path/bytes/sha binding), `admission` (normalized held-protocol
admission), `sdk_sources`, `held_sources`, `python`, `adb`, `powershell`, `owner`,
`launcher`. Sources are complete exact sorted bindings: SDK client/reader and
legacy client/verification helper source, plus the held CLI's source closure.
`held_sources` is exactly that CLI closure. Python is its interpreter/DLL binding.
ADB/PowerShell are installed-tool byte bindings, additionally identity-guarded
in the live client. Owner is the actual SDK caller's native process identity;
launcher is null or an immutable native launcher identity. Descriptor is saved
create-only as `sdk-session-v3.json`, with its binding retained by the client.
Captured descriptors/receipts require external source/worker admission; they do
not authenticate themselves. A parent runtime must bind the actual worker and
source request before accepting its saved descriptor.

Context has exact keys `kind`, `index`, `phase`, `label`, `command_sha256`,
`transport_id`. Kinds/phases are command/before|after, check/check, or
external/before|after. Index is a positive exact integer. Label is bounded legacy
label syntax. Check has null command digest; command/external has the SHA256 of
the canonical `env.encoded(argv)` bytes. Transport is null for preselection
discovery/check or an immutable positive ID. External requires a positive ID.

## Dispatch and records

Preserve fixed ADB executable and `-H 127.0.0.1 -P 5037`. Before selection only
`devices -l` is allowed. All targeted commands use one immutable positive `-t`
transport. Preserve the legacy daemon/reconnect/global verb refusals. Discovery
cannot resume after target selection. Actual target/guest ownership is a
separate runtime admission; arbitrary transport IDs are not device authorization.

Reserve a command attempt before pre-proof. Proof directories are
`server-proofs-v3/command-NNNN-before` and `command-NNNN-after`. A refused
pre-proof is retained without an SDK row or SDK dispatch. It poisons the session.
Compute remaining SDK budget AFTER successful pre-proof. Full-budget dispatch
requires all requested seconds then; otherwise refuse before dispatch. Every
proof consumes the same finite caller deadline. Proof owner budget is a positive
integer floor of min(45, remaining), never rounded upward. SDK budget remains
the exact min(requested, remaining) and measured elapsed excludes proof work.

Persist actual binary stdout and result before considering return; preserve
trusted SDK failures and explicit missing/refused post-proof. Attempt a post-proof
only while its source/identity/ownership/deadline guards permit it. Return bytes
only after SDK completion0/clean/stderr0, valid post-proof and final guards.
Every failure permanently closes dispatch. Never infer cleanup or timing when
the process owner has no trusted measurement.

V3 command JSON is exactly the11 v2 scalar keys (`version`, `index`, `label`,
`status`, `returncode`, `cleanup_complete`, `stdout_bytes`, `stdout_sha256`,
`stderr_bytes`, `elapsed_ms`, `effective_deadline_ms`) plus `protocol`,
`server_admission`, `server_before`, `server_after`, `transport_id`,
`command_sha256`, `argv`, `client_qualified`. Version is exact int3. Before/after are manifest byte
bindings; after may be null only in a failed record. Recorded argv is bounded,
canonical-hashed and policy-checked; its hash is metadata, not execution
authentication. The source-admitted runtime checks its own exact phase/command
roster. `client_qualified` is an exact boolean: true only after subprocess
completion, post-proof and the final caller/source/deadline guards all pass.
Failed guards preserve the actual SDK result with this flag false; a completed
subprocess alone cannot qualify the row. Clients remains exactly JSON/raw pair
per ACTUALLY dispatched command.

`check_server()` returns a freshly acquired verified bundle without a fake SDK
row. Its folders are `check-NNNN`, independent sequential check indices. Context
uses kind/phase check/check, label check-server and current transport/null.

The fixed binary-transfer bypass uses
`prove_external(command,label,phase,index)` returning a verified bundle, with
folders `external-NNNN-before|after`. It validates the same target/command policy,
caller/source/deadline guards and binds the exact command hash. An after call
must match the previously opened before context; no overwrite, duplicate, swap
or parallel external attempt. Private stream records MUST bind both references,
actual child/source-FD/raw/hash/destination/cleanup evidence and the admitted
request; these server proofs alone do not prove a transfer occurred. No model
weights are passed through text or ordinary bounded capture.

## Bound proof acquisition

Bundle root has create-only `launch/` and `held/`, plus `bundle-v1.json`. Launch
contains request-v1.json, started-v1.json, owner-result-v1.json,
source-after-v1.json and the two owner
stdout/stderr .bin files. The fixed request binds session/context/source/Python,
actual caller and exact CLI argv; started records the actual external CLI.
Held contains the existing CLI's exact13-file success roster. The external CLI
gets a bounded owner; its nested worker retains its existing barrier/pins and
resource checks. Both terminal captures are required, with joined actual CLI
and worker identities. Source-after has exact SDK/held source, Python and caller
bindings and must match the request/session. No legacy observer or SDK/device
service is called here.

Bundle manifest has exactly `version`=1, `protocol`=BUNDLE_PROTOCOL, `session`,
`context`, `verified`, `files`. Files is a sorted list of exact `{relative,
binding}` entries for the finite launch/held roster, excluding the manifest
itself. Failed acquisition may retain a subset and verified=false; success
verification requires the full exact roster and no unlisted files/directories.
All bindings must stay inside that exact physical-D bundle without reparse
components. Verify every byte/hash, owner capture/status/terminal, request and
admission, expected sources/Python, actual started identities, pure held report,
source closures before/after/final, SDK caller identity and context. No proof
reuse across commands, phases or sessions. A verified flag alone is insufficient.

Current-client verification requires exact clients roster/count, sequential
indices, strict measured completed records/raw hashes, one transport, exact
session/admission/source/tool pins, canonical argv/command policy and fresh
before/after bundles at prescribed paths. Extra check/external folders must
each have their own verified exact context; no unknown proof namespace. Complete
runtime external-transfer validation additionally checks the paired stream
record. Parent validation occurs after its SDK worker terminates.

Host-only machine/boot/postflight admission selects `require_host_checks_v3`
explicitly: clients must be empty and the nonempty proof roster must be exactly
contiguous check-NNNN bundles with null transport and the same session. Command
verification still requires a positive dispatched count; a failed pre-command
attempt or an empty directory cannot masquerade as host-only admission.

## Execution gate

Run independent synthetic/mock tests and unchanged legacy/held regression first.
Then exercise one owned SDK3 read-only discovery. All-source/HEAD build maps
change with SDK3: run a fresh complete offline Android/JVM/lint/audit/build and
new admission; historical maps are immutable. New private runtime/admit/boot/
stream/JUnit/close/postflight ports select this protocol explicitly. Preserve
known guest closure even if a later proof refuses. Only then use the existing
fresh-D emulator/model approval for import, one AUTHOR and inference-free reopen.
