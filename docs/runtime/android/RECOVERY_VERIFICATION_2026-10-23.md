# Read-only recovery of the guarded SDK attempt, 2026-10-23

Refs [#5](https://github.com/OptimumAF/LocalLore/issues/5), M01.03/M01.05
partial, claim `6373651169`. This packet is stacked on unmerged
[#111](https://github.com/OptimumAF/LocalLore/pull/111). It addresses the next
diagnostic prerequisite; it does not retry inference or qualify a runtime.

## Problem and narrow fix

The [guarded SDK attempt](GUARDED_SDK_VERIFICATION_2026-10-23.md) crashed
without a structured terminal. Its original recovery control received 1,101
bytes instead of 262 and stopped before reading the database. The actual
mismatching payload was omitted; its contents cannot now be reconstructed from
its length and hash. The original sealed evidence is unchanged.

Source inspection found that the private helper pre-quoted a script argument
passed to `adb exec-out`, whose official implementation already quotes those
arguments. That service also returns a client exit code rather than the remote
command's exit status. The [transport author report](RECOVERY_TRANSPORT_TESTS_2026-10-23.md)
links the pinned official AOSP sources and explains the demonstrated command
contract defect separately from the unknown historical payload.

New `benchmarks/android_recovery_transport.py` uses the existing bounded byte
runner and shell-v2 with `-T`, `-e none` and exactly one joined shell command.
Before any session facts or file read, it requires shell-v2 features, an empty
remote exit-37 control and an exact decoded 262-byte fixture containing every
byte value. The final wire format is canonical base64 without line wrapping;
the raw sink durably saves wire bytes before parsing or decoding. Re-encoding,
decoded size, full SHA256 and the main SQLite header remain mandatory. ASCII
metadata accepts only defined LF/CRLF framing; binary CR bytes are never stripped.
Any failure blocks further reads; ordinary API assignment cannot replace the
qualified device/session/sink or reset cleanup/failure state.

Only the fixed cacheprobe package, the original 32-hex session and four SQLite
leaves are eligible. The exact regular owner marker, directories, link checks,
file metadata and complete hashes bind the snapshot. All sidecars are present
or explicitly absent; each file is bounded to 128 KiB. Repeated facts must be
identical. The 128 KiB decoded file cap needs at most 174,764 base64 wire bytes.
Only file transfers explicitly select a 262,144-byte host output budget, already
within the existing runner's absolute cap; default calls retain their original
limit. No SQL executes on Android. These sampled checks are not a same-UID
or compromised-OS sandbox.

## Source, checks and unchanged artifacts

Base `fbf0542e0b56dea5ab99f30ca5e3b2d4193b207c` is #111's exact head.
Coordinator commit `401a839` initially integrated author
`5ebbc5a9236d7921bab554ded1b825b7260c1f02`: only the new transport, 24 original
tests and their report. No Rust, Java, SDK, model, runtime or dependency changed.
The existing APK remains `0cf4c253c41483973fd1578837d0ba147a7ed3d6d6cd8eb5818a989e185c09dd`,
native source `ba31932`. Its storage contract is **schema2**; this is not a
whole-current-main or schema-upgrade experiment. Earlier APK/native build and
model qualification are linked evidence, not builds or inference rerun here.

Final source `187321c` additionally integrates author `c760a25` and coordinator
`216ff1a`: strict encoded wire and a bounded optional `Device.raw` output limit.
The same fixed session/file API and 128 KiB logical file cap remain unchanged.

Actual coordinator commands:

```powershell
python -B -E -m unittest discover -s scripts/tests -v
python -B -E -m unittest discover -s benchmarks -v
python -B -E -m unittest discover -s benchmarks/spike/android/litert -v
```

Final source passed: **297 script**, **140 benchmark**, **33 SDK-helper** tests.
These include 30 transport methods and three output-budget methods. The earlier
288-script run preceded the encoded-wire refinement and is not additional
independent coverage. Actual trusted
host child processes retained the exact byte fixture with exits zero and 37
and known cleanup. No host test called ADB or a model. The SDK-helper selection
used a dedicated D-drive temporary root. An actual host child emitted 174,764
encoded bytes: the default call correctly reached its output limit with known
cleanup; an explicit bounded call retained exact bytes with exit zero and known
cleanup.

Independent review found comma-only feature framing and a late cleanup-state
propagation gap in the first draft; both were fixed before the first test run.
All three author invocations passed (22, then 23, then 24); none is a device
qualification. The author index binds 14 selected files, 143,172 bytes, SHA256
`575dc311c143d446502b99a4190daa39acd2de2aedce839f284fa706e3defb53`;
the coordinator independently rehashed every entry.

The encoded refinement retained a genuine parser regression: a 30-test run
passed 29 and failed one because `splitlines()` admitted control characters as
metadata separators. Explicit LF splitting after strict LF/CRLF checks fixed
it; the final 30 passed. The second author index binds 14 files, 17,290 bytes,
SHA256 `93e3a23653c0a240e752b39fad4cb0c4913c50f652d239731613e7815c673c4c`;
all entries were independently rehashed. Official Android 15 Toybox source
supports the direct `base64 -w 0` file encoder; no new dependency was installed.

The private host replay orchestration additionally passed three synthetic
fence checks: uncertain helper cleanup saves raw/status then performs no
dependent file reads; unexpected manifest keys fail before copying; physical
file size is bounded before loading. These spawned no helper process or model
and inspected no actual session. They are not strict-replay results.

## First actual cohort: binary qualification refused

Fresh identity/capacity/protected-metadata checks, shell-v2 features and an empty
remote exit-37 control passed. The raw binary fixture arrived as 265 bytes
instead of 262. Full current bytes were retained; independent comparison proves
the exact transformation `expected.replace(b'\n', b'\r\n')` for this control.
The component introducing CR was not established. This evidence explains the
encoded-wire refinement; it does not reconstruct the older omitted payload.

Qualification stopped before any database facts, hash, copy, crash-log read or
replay. The pristine directory remained empty and no manifest existed. Separate
read-only closure under known cleanup verified original package/model/cache
metadata and namespace absence. All 119 initial plus 125 closure commands
completed with known cleanup, retaining the expected exit-37 and three pidof
absence exit-one records. Inventory changed from seven emulators to four, with
A/B ready and zero other devices; this packet performed no AVD lifecycle action
and attributed no cause. No inference was retried.

The failed cohort is sealed separately: 525 files, 302,409 bytes, index SHA256
`52fda46926fec28f51ba80f6574e8b9bd7dd036c3ce881938a2d6e1a647c8bce`.
Every entry was independently rehashed. Its 265-byte control receipt remains
distinct from any later encoded qualification.

## Read-only replay boundary

After successful byte qualification, the device observer can retain a pristine
snapshot with the original SQLite basenames. A separate create-new local working
copy must receive every present sidecar. This path was not executed in the first
cohort because its byte control failed. The existing hash-bound Rust helper uses
only `Store::open_read_only`,
strict schema validation, branch replay and original `sdk-play-1` status lookup.
It does not migrate, repair, rebuild a projection, commit or call inference.
The snapshot caller requires exactly one story/branch and the frozen schema2;
no scope is inferred from a title, transcript or model summary.

Raw helper output and process metadata precede verdicts. Unknown worker
ownership fences subsequent file inspection. Known completion permits checking
that the pristine set and working main database are unchanged, then reading
the typed replay result. Working SQLite coordination sidecars are not claimed
immutable merely because the main database is read-only. Process exit zero
alone establishes neither a committed gift nor its absence.

## Actual encoded capture and canonical outcome

The separately admitted encoded cohort passed its actual controls: 352 canonical
wire bytes decoded to the exact 262-byte fixture. The 87,384-byte database wire
decoded to 65,536 bytes, SHA256
`420541d81d1b80c408f84a2e14321b757994978e75cc564c408203ed0b4a4cd9`.
Source facts matched before and after; WAL, SHM and journal were explicitly
absent both times. The [device report](RECOVERY_DEVICE_2026-10-23.md) records
the package, namespace, capacity and protected-metadata gates and their limits.

The first host replay orchestration refused before copying or spawning because
its exact owner-marker assertion expected LF while the existing marker contained
CRLF. That failed attempt is retained. Only the expected marker bytes changed;
the next orchestration passed the unchanged strict Rust helper on a create-new
working copy. Its 31 ms host execution is not a phone performance measurement.

Actual replay validated schema2, foreign keys and exactly one story/branch.
Revision, accepted receipts and accepted events are all **zero**. The original
requested turn is **failed**, with no receipt; the player still owns one potion.
No projection was rebuilt. Both pristine data and the working main database
remained unchanged. The strict typed report SHA256 is
`737faa58b62c9d1d7f038b1fbd0d3b0e7fcc9a46e54e2e28096f03eef342da04`.
This resolves canonical noncommit independently of the missing SDK result.

The UID-scoped crash buffer was empty. One separately scoped package exit-history
query retained 16 records: 15 reason10/status0 and one reason2/status9. Without
the original SDK process identity these records cannot be attributed to that
attempt. They establish neither a watchdog nor a memory-pressure or native-crash
cause. No trace file was opened. SDK output and resource-owner balance remain
unknown, and guarded schema compatibility remains unqualified.

The two device namespaces are sealed: first 525 files/302,409 bytes and encoded
573 files/602,635 bytes. All 512 recorded commands completed with known cleanup;
seven expected namespace-absence exit-one probes and two expected exit37
controls remain visible. The final encoded index SHA256 is
`4dda8e9c7da0353ccefaa12af0a9312aeb9522066c1652ac26d35c29274cbc9f`.
The separate host index binds 36 selected files/5,666,848 bytes, SHA256
`ecef2dbcf03bd8bc46864ef0d208d115ba8fa5d9ef7c7240cc2242c346b4011f`.
Raw databases, identifiers, diagnostics and model/cache payloads stay private.

The [safe aggregate](RECOVERY_RESULTS_2026-10-23.json) binds source, checks,
outcomes and all five evidence indexes. See the
[independent review](RECOVERY_REVIEW_2026-10-23.md) for its audit and limitations.
No further device action or inference is part of this packet; leases are released.
M01.03/M01.05 remain partial and in review, M01.01 remains blocked without an
authorized physical phone, and A remains below write/inference admission.
Full M01 acceptance, ARM execution, model quality and sustained memory/thermal
checks remain pending. The next runnable task is bounded persisted SDK phase
and termination evidence, bound to the original process identity, before another
freshly admitted guarded control. Preserve this recovered failed turn.
