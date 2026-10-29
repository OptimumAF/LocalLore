# Owned emulator target, v1

M10.02 supporting M09.06/M01.01. Distinct `owned-emulator-target-v1` authority;
`sdk-owned-target-v1` sessions and `owned-target-socket-proof-v1` observations.
Host-only v2 descriptors cannot substitute for this admission. No old reader,
failed capture, state predicate or SDK3 contract is changed.

Root owns `owned_target_contract.py`, `android_process_verification_v4.py`, this
specification, the tiny native refuser and integration. The Android specialist
owns only `owned_target_owner.py` and `android_process_client_v4.py`. Original
adversaries own only the two correspondingly named new test files. Separate D
branches/worktrees; commit shared contracts before dependent implementation.

## Authority and lifetime

Admission has exactly `version:1`, `protocol`, `run_id`, `root`, `seconds`,
`server`, `guest`, `artifacts`, `sources`, `python`, `compatibility`. The root is
fresh physical D outside Git. Seconds is1200..1700. `server` is an embedded valid
v2 host admission with matching run_id/seconds and root=`root/server`. Its ten
source pins are a subset of the target's full fourteen-source closure. It is
reused only for initial empty readiness primitives, never published as a live
host-only descriptor while target work is permitted.

`guest` is exactly `root`, `proposal`, `authorization`, `emulator`, `qemu`,
`refuser`, `refuser_source`, `console_port:5592`, `adb_port:5593`,
`serial:emulator-5592`, `memory_mib:8192`, `cores:4`, `max_seconds:1800`,
`api:35`, `abi:x86_64`. Bindings are `{path,bytes,sha256}`. The approved root is
`D:/Dev/Experiments/LocalLore/2026-10-28-author-player-contract-v1/avd-v1`.
Proposal/authorization bind the existing create-only AVD preparation and
explicit run authorization. Validate actual prepared data/config/tool/resource
pins before boot; metadata is not human authorization. No prior AVD is reset,
moved, compacted, deleted or reused. Existing OS auth tokens must remain intact.

`artifacts` has exactly `build`, `product_apk`, `test_apk`, `model`, `probe`.
Model is the already authorized2588147712-byte local model, SHA256
181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c.
The original binary probe is the public physical_model_probe_v1.txt fixture.
Model/source paths are physical D; installed executables may remain C.
Revalidate fresh current-source qualified Android build/APK bindings before
installation, and model/probe byte identity before/after binary transfer.

Running is exactly `version`, `protocol`, `admission`, `run_id`, `root`,
`owner`, `worker`, `server`, `launcher`, `guest`, `guest_ancestry`,
`started_epoch`, `deadline_epoch`, `sdk_port`, `console_port`, `adb_port`,
`serial`, `transport_id`, `sources`, `python`, `ready`. Five actual held process
identities are distinct; executable paths match pinned Python/ADB/emulator/qemu.
Actual qemu listeners, ancestry from the held launcher and inherited job
containment must be checked, not assumed from Popen's launcher PID. Descriptor
metadata is not liveness. Stop is exactly `{version:1,protocol,
admission_sha256,action:stop}` and acts only on owned handles/jobs.

One finite parent/worker barrier, complete atomic started receipt and separate
supervisor capture namespace precede side effects. Worker owns server and guest
in its inherited finite job. Lock/check the existing auth key by metadata only.
Start the new foreground server, prove unused endpoint and exact version/empty
devices, then boot only the prepared guest. No concurrent/favorable startup
retry. Capture each launch, actual return/cleanup and failures. Shutdown guest
before server. A stopped/expired descriptor can never authorize a later command.

## Private routing and direct protocol

Source-verified emulator `ANDROID_ADB_SERVER_PORT=15937` confines automatic
`host:emulator:5593` notification to the owned server; expect only emulator-5592,
never a second127.0.0.1:5593 alias. No manual generic TCP registration. Strip all
inherited ADB/ANDROID aliases; retain direct transport exclusions and physical D
AVD/user/emulator/cache/temp locations. Freeze headless/no snapshots/no metrics,
test.quitAfterBootTimeOut=0 and approved8GiB/four-core profile. Set `-adb-path`
to a pinned D native refuser which unconditionally returns64 and performs no
process/network/file action. Do not select `-no-direct-adb`. Official headless
pre-override source paths permit offline adb-version/raw host-version probes
only; record exact installed/source attestation limitations. Refuser failure
must not select an external ADB fallback.

Ordinary ADB CLI is not used by SDK4: its mismatch branch can kill/restart a
service even with numeric-H. Connect only to127.0.0.1:15937. Bounded smart frames
select exact `host:transport-id:N`, require OKAY, then select
`shell,v2,raw:<shlex.join(argv)>` and require OKAY. Host version/device queries
are separately fixed, source/identity guarded frames. No generic host service,
kill/connect/disconnect/recovery or default5037 route is exposed.

Shell-v2 header is one channel byte plus little-endian uint32 length. IDs are
stdin0, stdout1, stderr2, exit3 and close-stdin4. Exit is exactly one byte;
close-stdin is length0. Require one exit followed by EOF, known channel/bounds,
no output after exit, exact byte counts and complete owned closure. Concurrent
bounded sender/reader avoids pipe deadlock. Model/APK/probe input is binary;
0x1a, CRLF and NUL are preserved. No text-mode/native-shell redirection on host.

Only bounded typed target-shell recipes from the contract are accepted. No
arbitrary shell script. APK staging uses dd into fixed fresh guest paths then
pm install. App binary input uses run-as for the isolated test package, fixed
no_backup model/probe paths. Instrumentation is only the two original import/
AUTHOR-reopen methods; no automatic repair or repeated AUTHOR attempt. Getter,
hash and scoped canonical artifact reads remain separate measured commands.

## Shared APIs

`owned_target_contract.py` imports without IO and exposes strict pure validators:
`validate_admission(value)`, `validate_running(value, admission, binding)`,
`validate_session(value, admission)`, `validate_operation(value, admission)`,
`operation_digest(value)`, `check_stop(value, sha)`,
`validate_observation(value, server, caller, endpoint, guest, after=False)`,
`validate_guest_observation(value, guest, server)`,
`validate_proof(value, session, context)`, `validate_client_record(value,session)`.
Explicit `source_bindings()` and `revalidate_inputs(admission)` perform local
byte checks only; no native process/TCP/credential inspection.

`owned_target_owner.py` exposes `LiveOwnedTarget(admission_binding,
running_binding)` with copied `.admission`, `.descriptor`, `.admission_binding`,
`.running_binding`; `.guard(min_seconds=0)` checks current source/clock/stop and
actual held process/guest/server identity; `.fast_guard()` checks live handles
and finite clock while streaming; `.prove(path, session, context, socket,
anchor, after=False)` publishes a bound complete proof; `.close()` releases only
its own observer handles. The owner CLI accepts --admission/--admission-sha256.
It never exposes a host-only v2 lease as target authority.

`android_process_client_v4.py` exposes `OwnedTargetSdkCapture(directory,seconds,
lease)`, `.shell(argv,label,seconds=15,cap=131072,full_budget=False)`,
`.stream(argv,source_binding,label,seconds=180,cap=131072,full_budget=True)`,
`.check_server()`, `.close()`, copied `.target` (transport_id immutable),
`.session`, `.session_binding`, `.count`, `.clean`, `.until`. Input authority is
limited to bound model/APKs/probe. Return stdout bytes only after exact exit0,
complete capture and post-proof; preserve nonzero/partial/error measurements
before poisoning. No legacy SDK constructor/runner or global monkeypatch.

Session exact keys: `version:1`, `protocol`, `admission`, `running`, `descriptor`,
`caller`, `sources`, `python`, `root`, `seconds`, `started_epoch`, `deadline_epoch`.
Operation exact keys: `argv` and `stdin` (binding or null). Context exact keys:
`index`, `phase` (before/after), `label`, `operation_sha256`, `transport_id`.
Each command files command-NNNN.json/stdout.bin/stderr.bin live under clients;
proof files under sibling proofs; session is sibling sdk-session-v4.json.

Client record exact keys: `version:4`, `protocol`, `session`, `index`, `label`,
`operation`, `operation_sha256`, `transport_id`, `status`, `returncode`,
`cleanup_complete`, `elapsed_ms`, `effective_deadline_ms`, `stdout`, `stderr`,
`stdin_sha256`, `stdin_bytes`, `stdin_complete`, `server_before`, `server_after`,
`client_qualified`, `socket_closed`, `sender_joined`, `input_closed`.
Missing/unmeasured stages are null/false, never fabricated success. A passed
command does not prove a feature, device performance or native callback drain.

Proof exact keys: `version:1`, `protocol`, `session`, `context`, `admission`,
`running`, `caller`, `endpoint`, `anchor`, `brackets`, `observation`, `tables`,
`version_response_hex`, `devices_response_hex`, `after_request`, `elapsed_ms`.
Brackets before/after exactly `owner`, `worker`, `server`, `launcher`, `guest`,
`sources`, `python`, `server_alive`, `guest_alive`; they equal the admitted live
descriptor/source closure. Endpoint/anchor match the same owned socket resource
before and after. Every proof rechecks exact version and one exact registered
serial/transport using guarded raw queries, without treating them as authority
on their own. Separate private query/closure evidence is retained by owner.

## Observation extension for multiple target requests

The previous v2 two-exchange history is not repurposed after guest registration.
The new scope retains every row local OR remote to15937, with full raw row and
family-table metadata. Require a unique owned IPv4 loopback listener and exact
reciprocal held caller tuple before dispatch. After EOF that current pair may
vanish or retain0/original PID. No extra IPv6/wildcard listener is accepted.
Other loopback auxiliary rows are retained without a positive ownership claim:
server-side PID must be0/owned server; client-side PID0/actual caller/actual
owned qemu only. A foreign nonzero client refuses. Auxiliary state values never
qualify the current connection, target or caller. This distinct multi-client
rule permits recorded teardown and emulator notification without claiming its
unattributed rows are earlier authenticated proofs. Raw states stay opaque.

Guest5592/5593 observations are separate, permitting documented IPv4 plus
optionalIPv6 loopback listeners owned by the pinned qemu. Actual ADB transport
peers must belong to the new server/guest, with scoped teardown observations;
never substitute the launcher's PID for endpoint ownership.

`android_process_verification_v4.py` owns explicit closed bound-file replay:
`verify_client_record(binding,session,admission)` and
`require_current_clients(root,count,session_binding,admission)`. It validates
the entire source/session/context/proof/raw graph and exact roster, not a
caller flag. Old SDK2/3 and model proofs remain unchanged. Current app proof
bytes receive separate original native/canonical validators after SDK4 coverage.
