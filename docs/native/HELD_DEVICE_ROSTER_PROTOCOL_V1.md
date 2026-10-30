# Read-only held device roster, version 1

M01.01 / supporting M01.05 and M10.03. This explicit host tool lists untrusted
metadata from an existing ADB service. It never launches ADB, starts/restarts a
service, selects a target, sends a device command or grants phone admission.
It does not replace the existing physical-phone collector or qualify a model.

The ordinary ADB client can restart a mismatched server. This tool instead
uses two fixed host-protocol requests through ownership-checked loopback
sockets: the existing version probe, then `host:devices-l`. These are distinct
required queries, each attempted once; a failure is never retried or repaired.
The old version protocol, resource backend and collector stay unchanged.

## Entry point and authority

```text
python -B -m benchmarks.adb_device_roster_probe --admission <existing D: JSON> --admission-sha256 <sha256> --output <missing D: directory>
```

Admission has exactly `version`, `protocol`, `server`, `adb_file`, `candidates`
and `expected_version`, using protocol `adb-held-device-roster-v1`. The existing
[held ownership contract](ADB_HELD_SOCKET_PROTOCOL_V1.md) checks the exact
process creation identity, executable file identity/hash, loopback port 5037
candidate roster and expected version chosen before execution. Installed tools
are read in place; the ADB program is never executed. There is no automatic
admission, default device, caller-chosen command, implementation, port or target.

The production worker/backend types are fixed in code. The parent binds source,
Python/runtime, request and admission before launching one owned worker. It
atomically publishes a create-only `{worker, request}` started receipt. The
worker verifies its actual identity, parent and all bindings before creating
either backend. An absent receipt has a bounded five-second wait; a present
malformed or foreign receipt refuses immediately. The worker owner stays at
30 seconds; each complete protocol exchange stays below three seconds.

Both exchanges retain the original socket anchor/endpoints and held/fresh
process/file identities, with bounded IPv4/IPv6 owner-PID tables. Before byte
zero, an exact reverse server tuple with ESTABLISHED5 must exist. The reciprocal
client state is preserved as its raw DWORD without inventing state meaning.
The two proofs must use the same actual worker. Uncertain cleanup refuses.

A completed version connection can leave an ownerless row in the next native
snapshot. The new profile permits only the exact IPv4 reverse tuple derived
from its fully qualified, EOF-complete, closed version proof, with PID0 and raw
state11. At most one such row per derived tuple is permitted. It remains in the
raw snapshot; only candidate validation treats it as history. Unknown, foreign,
wrong-state or duplicate ownerless rows still refuse. The original live join
always reads the original rows and still needs a unique live admitted-server
ESTABLISHED5 connection and reciprocal current-client tuple before byte zero.
History never replaces live ownership. The old validators remain unchanged.

Post-CLI native checks may additionally use the exact endpoint of a positively
qualified closed roster proof with the identical embedded version witness.
There are no caller-provided ignored-port lists or generic PID0 exceptions.
The failed earlier capture remains refused at its frozen source; this same-wire
unmerged revision does not reinterpret that result as a successful roster.

The imported production source closure includes the transitive storage helper;
importing that helper neither reads nor changes the shared guest ledger. Actual
owner/capture termination, source/runtime pins and external terminal evidence
are additional to report consistency. Reports cannot authenticate themselves.

## Raw framing, rows and privacy

The roster response is `OKAY`, four ASCII hex length digits, exactly that body
and orderly EOF. Body cap is 65,535 bytes, frame cap 65,543, and row cap 256.
One extra byte can detect overflow. FAIL, truncation, trailing bytes, mismatch
or expired clocks refuse without reconnect, fallback or deadline extension.
These are this tool's bounded compatibility limits, not universal AOSP limits.

Actual received bytes are retained before post-read validation. A bounded
private exception channel carries roster bytes if the backend's post-read
clock/resource guard refuses. The protocol then remains refused. A separate
fixed version adapter records the original version receive bytes while keeping
the original version probe/verdict unchanged; a successful version report must
match its sidecar exactly. No failed report is rewritten into a success.

Private files include `version-bytes-v1.bin`, `version-report-v1.json`,
`report-v1.json` and their source/request/owner records. All are bound and
rechecked after acquisition. Standard output contains only fixed categories
and qualified counts, never serials, model strings, paths or private payload.
Selected TCP rows are restricted to local 5037 or the exact client port; the
initial view permits only 5037. This applies to both the roster and embedded
version proof. Whole table hashes/counts do not imply retained whole tables.

Rows have exactly `serial`, `state`, `devpath`, `product`, `model`, `device` and
`transport_id`. Metadata is untrusted data and never becomes command text.
Current ordinary AOSP long listing uses a minimum 22-byte serial field, then
state, optional keyless devpath, product/model/device and final uint64 transport
ID. The no-serial placeholder becomes null. Multiword permission-error states
and bounded UTF-8 metadata/spaces are supported. Devpath is not proof of USB
transport or physical hardware. Duplicate identifiers, ambiguous markers,
malformed final rows and unsupported control-bearing/exotic strings refuse;
their bounded raw bytes stay private. The format is not universally reversible
because AOSP does not escape all serial/property text.

## Compatibility and verification boundaries

Primary AOSP revision
[`1cf2f017d312f73b3dc53bda85ef2610e35a80e9`](https://android.googlesource.com/platform/packages/modules/adb/+/1cf2f017d312f73b3dc53bda85ef2610e35a80e9/)
provides the [wire services](https://android.googlesource.com/platform/packages/modules/adb/+/1cf2f017d312f73b3dc53bda85ef2610e35a80e9/docs/dev/services.md),
long-list formatting in `transport.cpp`, state names in `adb.cpp` and the
separate restart logic in `client/adb_client.cpp`. Original implementation uses
the existing Python standard library and Windows resource backend; no runtime,
model, native or SDK dependency is introduced. Source review is not binary,
OS or physical-device attestation.

Host tests use original fake IO and byte-backed JSON/TCP rows. They exercise
framing, parser bounds, bad identity, request/source mutation, cancellation,
post-read expiry, cleanup, strict counters, raw-sidecar tampering and unrelated
row rejection. A fake or recorded roster does not prove acquisition, a phone's
identity, hardware eligibility, offline gameplay or model performance.

Run from the physical D: checkout with process-local TEMP/TMP/TMPDIR set to
`D:\Dev\_Temp`:

```powershell
python -B -m unittest discover -s scripts/tests
python -B -m unittest discover -s benchmarks -p test_runtime_spike.py
```

Live host-only acquisition requires an explicitly pinned existing service and
closed source/test review. It does not require or authorize a new emulator.
The missing retained authorized phone identity remains a separate gate; never
pick a similar model from this list as a substitute. Future target reads,
installation, import and inference require their own admission. Existing
emulators, shared service, settings, private captures and recovery are preserved.
