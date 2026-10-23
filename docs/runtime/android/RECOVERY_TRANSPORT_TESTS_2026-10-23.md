# Read-only recovery transport tests, 2026-10-23

Refs [#5](https://github.com/OptimumAF/LocalLore/issues/5) (M01.03/M01.05
partial), claim `6373651169`. Base `fbf0542` preserves the preceding crashed SDK
attempt and failed recovery control. This packet adds only a host transport,
original tests and this report. It performs no inference, device operation,
SQLite open/repair or model read/copy, and changes no application/runtime API.

## Diagnosis and its limits

The preceding recovery attempt expected 262 bytes but received 1,101 bytes,
with client exit zero and known host-client cleanup. The returned bytes were
not retained. No database/sidecar capture or crash-log read followed that failed
control. The original evidence remains unchanged; canonical outcome is unknown.

The old helper pre-quoted its script before supplying it as a separate
`exec-out` argument. Official AOSP's
[ADB client implementation](https://android.googlesource.com/platform/packages/modules/adb/+/refs/tags/android-15.0.0_r1/client/commandline.cpp)
already escapes those arguments. The additional quoting survives the daemon's
shell parse and makes the inner shell see a quoted command name instead of the
intended script. A host tokenization regression demonstrates this mismatch.
That source-level defect does not reconstruct the omitted 1,101 bytes or prove
their exact content.

The same official client returns zero after the raw `exec-out` copy; that is not
a remote command exit result. The official
[daemon service](https://android.googlesource.com/platform/packages/modules/adb/+/refs/tags/android-15.0.0_r1/daemon/services.cpp)
selects raw, nonprotocol execution for that service. The
[shell service's protocol description](https://android.googlesource.com/platform/packages/modules/adb/+/refs/tags/android-15.0.0_r1/daemon/shell_service.cpp)
distinguishes raw nonprotocol merged output from shell-v2's separated output and
exit status. Therefore client zero alone could not establish successful capture.

Installed SDK metadata identifies platform-tools 37.0.1. The author retained
that metadata and the executable hash, plus the three official Android 15 source
files. The matching behavior was also checked in official AOSP main; an exact
binary-to-source build revision for the installed client was not established.
Actual target qualification is consequently mandatory, rather than inferred
from source or a mocked device.

The existing host `Device.raw` delegates to `runtime_spike.run_process`: binary
`Popen` pipes, byte reads and bounded byte accumulation, without text decoding or
newline normalization. No conversion was found in that host path. The existing
combined stdout/stderr cap remains unchanged.

## Narrow interface and caller responsibilities

`benchmarks/android_recovery_transport.py` exposes:

```python
ReadOnlyRecovery(device, session, raw_sink)
recovery.qualify()
recovery.facts()
recovery.read_file(name, expected_bytes, expected_sha256)
```

The caller supplies the existing explicitly targeted, sticky-cleanup device and
an exact 32-lowercase-hex session. Package identity is fixed to the separate
cacheprobe package. The coordinator must verify the expected installed APK,
known package/process absence, authorized original session and fresh host/guest
capacity before capture and again after it. The helper neither stops processes
nor turns a storage sample into permission. No generic shell/script API is
exposed by its public methods.

Qualification requires bounded shell-v2 features, an empty-output remote exit-37
control and the exact 262-byte fixture (all 256 byte values, NUL, CRLF and an
escape-like line). Features admit the installed client's LF/CRLF line-per-token
shape and a strictly separated comma form; duplicate/malformed/mixed shapes fail.
The new commands use one explicitly joined shell string with `-e none` and the
existing Device-inserted `-T`, with no `-x`, terminal or pre-quoted script argv.
The mandatory real controls verify the actual client/target behavior before any
source facts or file content may be requested.

`raw_sink(stage, stdout, safe_process_metadata)` must synchronously retain the
exact available bounded bytes, create-only, or raise. It receives each result
before decoding, status/exit/size/hash validation, including partial failed
results. Stage labels are deterministic and unique within the helper. Sink
failure, any transport/control/fact/file failure, or unknown cleanup poisons the
instance; it admits no bytes and dispatches no dependent command. Ownership is
rechecked even after the sink, including the device-exception path. Metadata
contains only fixed status, typed counts, exit code, hash and cleanup flag;
remote errors are not echoed. Host output-limit results retain the available
bounded prefix, not a claim to the full remote stream.

Session-derived directory, device and sink bindings have read-only properties,
as do the qualification, poison, cleanup and sequence state. Ordinary attribute
assignment cannot replace an already-qualified owner or clear its failure fence.
This prevents accidental rebinding; it is not a sandbox against hostile Python
reflection or a compromised caller.

## Fixed capture boundary

Only the original session's four fixed leaves are eligible:
`stories.sqlite3`, `stories.sqlite3-wal`, `stories.sqlite3-shm` and
`stories.sqlite3-journal`, each at most 128 KiB. The script checks `no_backup`,
the session directory, the regular owner marker and every requested leaf for
links/type. Dangling sidecars are refused rather than reported absent. The
owner is exactly 34 bytes and its full SHA256 is fixed; shell newline-stripping
of marker content is not used as proof.

Private facts include bounded directory/owner/file stat fields and complete
file hashes, each bound to its fixed path; all four leaves must be present or
explicitly absent, with the main database present. Known regular/regular-empty
stat labels are accepted, the latter only for size zero. Repeated facts must be
identical or the helper poisons. Returned dictionaries cannot mutate its private
file admission state. A capture must match the latest size/hash and the main
file must start with the SQLite header. No SQL is executed on Android.

The coordinator retains pristine captures, checks before/after facts and uses
the shared strict Rust read-only replay on a separate local working copy. A
header or row count alone never establishes an accepted effect. These stopped
app/private-path checks are not immunity to concurrent same-UID or OS changes,
and seconds-resolution stat fields are not a complete change detector.

## Host verification

The author ran:

```powershell
python -B -m unittest discover -s scripts/tests -p test_android_recovery_transport.py -v
```

The final invocation passed **24 tests**. Cases include quote/token roundtrips,
raw retention before parser/status rejection, strict remote-exit/features,
all-byte corruption/short/extra output, exception/sink cleanup fences, metadata
duplicates/path/owner/ancestor/sidecar changes, exact bounds and filename rules,
main header checks, empty sidecars, mutation of returned facts and immutable
owner/failure-state bindings. Two actual
trusted Python child processes through the existing bounded host runner emitted
the full fixture with exits zero and 37: both retained exact bytes, zero stderr
and known host process/thread cleanup. This is host-pipe evidence, not ADB proof.

Independent source review found the initial draft assumed comma-only feature
framing and missed a late sink cleanup-state change on the exception path.
Both were corrected and covered before the first test invocation; no failed
device or model operation was attempted. All three host invocations passed:
22 tests initially, 23 after immutable owner bindings and 24 after immutable
failure state. Private official-source/installed-tool records and every test
log/exit are retained in the dedicated read-only-recovery
author D-drive root. The old sealed attempt was neither edited nor retried by
the author. Actual recovery, strict replay or an explicit unknown outcome remain
coordinator/device-observer work; full milestone and physical-device gates stay
unchecked.
