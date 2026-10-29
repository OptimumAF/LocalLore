# Held-socket server ownership verification — 2026-10-28

Refs #14 (M10.02 support), #13 (M09.06 support), #5 (M01.01 support).
Executed implementation: `10c92b00e00131ecf051277c08b91671bfb09ef9`.
Stacked on open/unmerged [PR #246](https://github.com/OptimumAF/LocalLore/pull/246),
at `f57650e26b3be41fabc38e83e7d8a3abf71957c7`.

The new explicit host-only ownership proof passes once against the admitted
existing ADB process. Current integrated tests pass163 cases. Independent
closed-evidence audit verifies the captured worker/CLI ownership, source/runtime
pins, selected raw rows and fixed exchange. The existing legacy listener guard
still requires LISTEN2; its defaults, schemas, validators and old failures remain
unchanged. No emulator boot, SDK/device command, model copy/import/inference or
application acceptance follows from this host proof.

## Implementation

The [separate protocol](ADB_HELD_SOCKET_PROTOCOL_V1.md) is named
`adb-held-socket-server-owner-v1`. Root owns pure orchestration/record replay in
`benchmarks/adb_held_socket.py`. The Windows backend owns query-only native
process handles, transient read-only executable descriptors, complete bounded
IPv4/IPv6 owner-PID table acquisitions and exactly one client socket. The opt-in
CLI binds an exact private admission and full public source closure, interpreter
and loaded Python DLL before/after its worker, with a30-second owner and a
3-second total protocol deadline. The actual external CLI also has its own
bounded owner and known terminal/capture evidence.

One pre-send view must contain an exact unique reverse server tuple/PID with
raw ESTABLISHED5. A reciprocal client tuple/own PID is also mandatory, with raw
state retained equally for every DWORD. The same held socket object/handle and
endpoints are checked throughout. Candidate endpoint identities, held/fresh
process identities and executable file identity/hash are bracketed. Only then
may the worker send `000Chost:version`, once. Exact admitted reply framing and
orderly EOF are required. There is no reconnect, resend, favorable polling or
legacy fallback. Uncertain cleanup remains a refusal. No ADB CLI is used.

Only selected relevant row bytes are saved. Complete table hashes/counts/caps
describe source-bound acquisitions; unretained whole tables cannot be
independently replayed. Metadata cannot authenticate its own acquisition. The
known source, source/runtime hashes, actual started process identities, closed
owners and terminal captures provide additional evidence. A trusted OS, declared
API view and source-controlled handle lifetime remain assumptions.

Backend `process_handles_closed` conservatively covers all its held/temporary
native process and file resources. Reused CLI metadata/supervisor helpers have
their own existing behavior; actual worker and CLI termination/capture are
additional closure evidence. This packet makes no universal Win32-handle claim.

## Verification and original failures

Environment: Windows NT10.0.26300.0; Python3.14.7/AMD64. No dependency, runtime,
model, global SDK configuration or system setting is changed. All new project
commands, scripts, temporary files, private captures and recovery use physical
D: locations. Installed Python/Windows/ADB remain in their supported locations.

| Actual cohort | Result |
| --- | --- |
| Original core27 on831750ea | 4 assertion failures,0 errors/skips; owner215 ms |
| Exact same27 after89627451 | 1 assertion failure remains,0 errors/skips; owner266 ms |
| Final core28 | All pass; owner265 ms |
| Windows cleanup20 | 3 assertions fail before9e6d4c52; exact same20 pass afterward |
| Expanded/contained Windows23 | Pass; later fixture cleanup containment is separately recorded |
| Timestamp28 | 2 assertions +2 errors on old backend; same28 pass after25911129 |
| Final Windows32 | All pass; owner317 ms |
| CLI25 | 7 assertions fail before9d04667e; exact same25 pass afterward, owner1,125 ms |
| Final CLI32 | All pass; owner1,073 ms |
| Root integrated163 | 0 failures/errors/skips; owner1,935 ms, child0, complete cleanup/capture, no stderr,15 source hashes unchanged |

These overlapping cohorts are not additive. The163 are core28 + backend32 +
CLI32 + prior decoder18/control28/legacy-client25. Additional private adapter18
checks retain their own RED/GREEN and earlier scope. Host tests use original
synthetic fixtures and mocks, with no service/device connection. Supervisors do
observe their own bounded workers. The Root command is
`python -I -B D:/Dev/Experiments/LocalLore/2026-10-28-held-socket-observer-v1/check-integrated-v1.py`;
it starts an isolated `-I -S -B` child with the exact six-module roster.

The core's genuine failures are two backend-argument aliasing paths that alter
preserved admission data, and intermediate clock rollback above the initial
timestamp. Deep argument isolation and nondecreasing monotonic checks fix them;
all three assertions pass with unchanged test bytes. The remaining original
fixture incorrectly treats an immediate synthetic provider TimeoutError as
observed deadline exhaustion. Its correction retains refusal, partial bytes and
closure, and adds a separate genuinely exhausted EOF-deadline case.

Windows failure tests expose blind retry after an uncertain final native/file
close. The fix keeps those values uncertain and attempts remaining owned closes;
it also refuses a replaced socket handle. A test-harness review finds that an
original assertion failure could let automatic cleanup attempt `os.close` on a
synthetic descriptor in its own supervised test worker. Later containment wraps
that cleanup in mocks. Original failed records remain; no existing-service or
other-process control occurred. Later contained/final results have separate
source attribution.

CLI failures expose five closed-schema gaps allowing synthetic canaries into
nested refused-report serialization, and two false refusals of unchanged files.
The serializer now closes nested fields and binds decoded rows. No actual
private-data leak is claimed by those synthetic tests.

The file refusals reveal differing Windows path-stat/fd-fstat ctime projections.
The exact owned-D fixture has matching device/inode/size/mtime/birthtime/hash and
stable values within each API. The corrected binding retains admitted PATH5,
full HELD5 stability within reads/across backend brackets, exact cross-API shared
identity plus mandatory stable birthtime, and full hash/replacement checks.
Missing/mismatched birthtime refuses. This preserves distinct observations;
it does not drop timestamp guards. The official
[CPython issue](https://github.com/python/cpython/issues/157671) documents the
same Windows behavior; [Python's documentation](https://docs.python.org/3.14/library/os.html#os.stat_result.st_ctime_ns)
describes deprecated Windows ctime and explicit birthtime.

## One actual host-only query

`run-host-proof-v1.py` invokes the explicit CLI with the bound605-byte admission
and a new D: output directory, from the physical checkout with D: TEMP/TMP.
It runs once. Outer CLI owner:768 ms, child0, complete cleanup/capture, no stderr.
Inner worker owner:363 ms, child0, complete cleanup/capture, no stderr. Core
protocol elapsed:67 ms. The eight public source pins, installed interpreter and
loaded Python DLL match before/after/final; no source change or recovery replay
is used to qualify the query.

Three snapshots retain1/3/3 selected rows. Before sending, exact server and
client tuples are both raw5 in this capture; the client value remains a recorded
observation, not an extra gate retrofitted onto the protocol. Candidate state0
is retained in every phase and never called LISTEN2. The fixed16-byte request
receives the exact12-byte admitted-version reply and orderly EOF. Final teardown
states are retained as observed; the protocol does not require the accepted
connection to remain established after a finite reply.

An initial independent audit wrongly adds that final-state5 requirement and
fails. Its source and tool-transcribed failure are preserved. The corrected
auditV2 enforces server5 only pre-send and retains final states/absence. It
actually exits0, rehashing/decoding all7 selected rows, matching source/runtime
pins and joining actual outer/inner started identities, terminal captures,
admission, process/file/endpoint brackets and closure. The host query is neither
rerun nor modified. The failure transcription is not a raw stream capture.

| Private artifact | Bytes | SHA256 |
| --- | ---: | --- |
| Bound admission | 605 | `73596a4012bb3da15f67364dbeb90ce72224e54038c2c4478d095dfa04548aec` |
| Live CLI result | 1,276 | `988b8ddf715fe7b8f91300c1f104a5c77163f84c90c4d9d2f9e5016c234ebb54` |
| Live report | 7,094 | `81118c8950ad1e351b389fa68627d751322f287f8fb378c5ec815479366bce17` |
| Closed auditV2 | 8,417 | `c8a171cc22d2b81b9a4e137a4711dce15bf5bfe3947d022b80108f5bdccc972b` |
| Executed-source ZIP at10c92b00 | 8,640,563 | `ad95d089baef0b6d16ddad37a5ef08523e0217c2738593bfe196f4240fcc74fb` |

Every outcome retains `feature_acceptance=false`. The result establishes a
narrow held-connection server proof in the captured view, with no SDK, emulator,
phone, model quality/performance or gameplay acceptance. Raw identifiers, socket
bytes, process paths and private diagnostics remain local.

## D: recovery

The create-only producer and independent verifier both actually exit0. At
`D:/Dev/Archives/LocalLore/2026-10-28-held-socket-observer-v1`,189 original/copy
entries,190 ZIP members and192 output files total17,888,283 bytes. Exact
original/copy/ZIP/index hashes and rosters match with zero missing/mismatched
entries. The independent replay rechecks all closed cohorts and their unchanged
test/source identities, the original host proof's seven rows, both owners,
source/runtime phases, source ZIP and failed/corrected audit attribution.

Selection is a finite188-file roster plus the admitted selection control. It
includes failed and corrected tests, original source snapshots, source-only
helpers/reviews, Root163 results, admission, actual host proof, both auditors,
explicitly transcribed audit failure, and SDK3 proposal. It excludes models,
saves, caches, emulator state, credentials and APKs. Original and historical
recovery data stay untouched. This proves byte preservation, with no new
experiment, service request or feature acceptance.

| Private recovery artifact | Bytes | SHA256 |
| --- | ---: | --- |
| Index | 130,051 | `feabb2da1be9b51c599fd719745f66cbf5ad6ea96140ed32583ea039c55ffa71` |
| ZIP | 8,536,354 | `78b888da04ce135ff2e179491ee5eca46bf8bab32e37fb64bcd1d9e6acc2b798` |
| Producer result | 850 | `efbe04f571f5d1f7cbe98a96ed14bb93a05929524b770f6904af2eefeae33c14` |
| Independent verification | 1,882 | `59715e55296ef7b2d8cec114b367d4a97fe2239534879cf1c2ad0873f035cb00` |

Producer source is30,131 bytes/SHA256
`b0c911ef37bee27591faa1a09325656d4d3cb874786b67219cd4aa035a594adb`;
independent verifier23,861 bytes/SHA256
`5d825b8659d8aa6ea75f6b10b4ac9bb440a9dfb09754518f203af156455a290e`.
Root executes `run-preservation-v1.py` and then `verify-held-socket-v1.py` with
four reviewed admission/index/ZIP/result digests, using `python -I -B` from the
physical D: checkout with D: TEMP/TMP. The immutable source ZIP binds exact
10c92b00 and matches all15 tested-source members. It is a source snapshot, not
complete Git history. This later verification/recovery prose is separately
committed/pushed after that seal and is not inside that ZIP.

## Remaining bridge

Supporting M10.02 implementation is in_review. Full task/milestone checkboxes
remain unchanged. M09.06/M01.01 import/AUTHOR execution is pending explicit SDK3
integration and fresh build/source/resource admission. Existing SDK2 consumers
must reject the new record. A source-only integration review identifies a new
client/validator and explicit private runtime, binary-transfer/JUnit and closure
ports; recognizing a new row alone does not make the old harness runnable.

The approved fresh D: emulator/model setup remains unused. Next: implement the
new bridge with preserved command/target/timing/raw/cleanup boundaries, freeze
and build its current source, then use that approval for import and one AUTHOR
attempt. No existing emulator stop, state reset/relocation, system setting,
server lifecycle, model download/private upload, merge or release occurs here.
Physical-device identity/availability is not re-observed and no phone absence
is claimed. Application Rust/Kotlin/SQL and runtime/model dependencies are
unchanged; no new Android/ARM64, accessibility or complete-journey result.
