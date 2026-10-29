# Windows TCP controls — 2026-10-28

Refs #14 (M10.02 support), #13 (M09.06 support), #5 (M01.01 support).
Implementation checkpoint: `dcb5379c2939b20a1eb4624ae203663aa1e72ce1`.
This packet is stacked on open/unmerged [PR #244](https://github.com/OptimumAF/LocalLore/pull/244),
at `6a58e6f09a0aed6e878ef7578827fdc0f00a3dcf`. No product/runtime dependency changes.

The public diagnostic reproduces an inconsistent Windows listener observation
using only sockets it owns. Acquisition completes and all three sockets close,
but raw listener states are0 or1 across four query paths, never LISTEN2. The result is
`observation_inconsistent`, with `feature_acceptance=false`. Existing strict
ADB admission remains refused. No emulator boot, target call, model copy,
import or inference is performed in this packet. The earlier AUTHOR rejection
and all earlier failed captures retain their original outcomes.

## Implementation

`benchmarks/windows_tcp_observation.py` decodes bounded owner-PID table bytes:
IPv4 rows24 bytes, IPv6 rows56 bytes, count header/first-row offset4. It rejects
unsupported families, non-exact types, short/truncated rows, oversized captures
and excessive counts. Unused trailing capacity never becomes additional rows.
It preserves raw states and converts network-order IPv6 scope IDs. A state2
flag is diagnostic only; it cannot establish endpoint or process admission.

`benchmarks/windows_tcp_control.py` is explicit and Windows-only. Imports do not
create files/sockets or call native APIs. Its create-only physical-D output
preflight refuses repository ancestors, broken Git markers, existing output,
reparse components and unsafe Windows aliases. The owner uses a start barrier,
30-second limit, source/tool hashes, complete bounded capture and known cleanup.
The worker checks the ctypes ABI, creates an exclusive ephemeral IPv4 loopback
listener, observes before/after listen and after its own connection/accept,
exchanges one fixed17-byte payload and closes three socket contexts. Fragmented
receives accumulate only the fixed remaining bytes; premature EOF refuses.

Four paths are queried: GetExtendedTcpTable OWNER_PID_LISTENER and OWNER_PID_ALL,
GetTcpTable, and GetTcpTable2. Only selected owned loopback-port rows are saved;
the PID-capable APIs additionally filter the current process. Basic GetTcpTable
has no PID: its selection label is not observed ownership evidence. Extended
rows are independently decoded through ctypes and the pure decoder before
selection. Full unrelated native table buffers are not retained.

The pure assessor checks exact report schemas, raw hashes/fields, ABI, query
roster, ordered actions, process metadata, fixed exchange and closure. Genuine
state2 listener observations are required for consistency after listen and
connect; raw0 remains0. LISTEN remote fields are not required to be zero because
they are undefined for that state. Acquisition and consistency are separate.
No assessment authenticates execution or qualifies a service.

## Verification

Host: reported Windows NT10.0.26300.0; Python3.14.7, 64-bit AMD64. Installed
Windows SDK10.0.19041 headers and pure ctypes layout checks agree on field order,
row sizes/alignment4 and first-row offset4. No compiled C ABI test was run.
All new project scripts, commands, temporary files and evidence are physically
on D:. Installed Python/PowerShell/SDK paths remain in their supported locations.

| Actual check | Result |
| --- | --- |
| Root initial decoder + unchanged client suites | 43 passed; owner971 ms, child0, cleanup/capture known |
| Independent first control suite | 25 passed; distinct preliminary cohort |
| Meaningful broken-Git-marker RED | 26 tests,1 assertion failure,0 errors/skips; owner317 ms |
| Same26 test bytes after preflight fix | 26 passed; owner316 ms |
| Final independent control suite | 28 passed,0 failures/errors/skips; owner315 ms |
| Root integrated decoder/control/client suites | 71 passed,0 failures/errors/skips; owner1,283 ms, child0, no stderr, complete cleanup/capture, six source hashes unchanged |
| Public diagnostic, executed once | Acquisition completed; listener consistency failed; worker0, owner211 ms, no stderr, complete cleanup/capture |
| Source review and Git diff whitespace check | Passed |

The integrated command, run from the physical native checkout with D: TEMP/TMP,
was `python -I -B D:/Dev/Experiments/LocalLore/2026-10-28-listener-observation-v1/check-python-integrated-v1.py`.
Its fixed module roster is `scripts.tests.test_windows_tcp_observation`,
`scripts.tests.test_windows_tcp_control`, and
`scripts.tests.test_android_process_client`. Those71 are18+28+25, not additional
to the narrower overlapping runs. The public command was
`python -B -m benchmarks.windows_tcp_control --output D:/Dev/Experiments/LocalLore/2026-10-28-listener-observation-v1/public-control-v1`.
PowerShell's outer tool reports exit1. The CLI source maps the inconsistent
status to2, but the inner CLI exit code was not separately captured; the retained
worker result is0. None of those statuses changes failed observation into success.

The same26-test RED/GREEN covers a real gap: `.exists()` misses a dangling
ancestor `.git` marker, allowing dispatch under a historical worktree path.
Using `lexists()` refuses it. Final additional tests challenge device names,
alternate streams, trailing dots/spaces and control characters while permitting
valid Unicode/apostrophe/space paths. Dispatch and native calls are mocked in
these tests. No actual symlinks, SDK calls or network connections occur there.
The decoder's earlier RED is only a missing-module import error, not a behavior
failure; its original17-test source differs from the final18-test suite.

## Observations and limits

Private source-v2 controlled sockets first recorded successful listen/accept,
SO_ACCEPTCONN=1 and17-byte exchange with listener0 in both extended table classes.
Source-v4 extended the experiment to the basic and owner2 APIs: all four paths
again returned listener0. The public implementation reproduces failed listener
consistency, with a different exact state distribution: the extended listener
class reports1 after listen and connection; the other three paths report0 for
the listener. The selected server connection is5 and client connection0 in the
three all-connection paths. These captured differences are retained.
Before listen SO_ACCEPTCONN is0; afterward it is1. All three socket objects have
fileno=-1 after closure. Selected connection rows can report state5; one earlier
client row reported1. No conflicting state is repaired or dropped from evidence.

This reproduces outside ADB and rules out an ADB-only explanation for the
controlled mismatch. It does not establish its OS/provider/execution-environment
cause, nor the integrity of any existing service. Microsoft defines LISTEN as2
and ESTABLISHED as5. The listener class alone cannot reinterpret0 as2.
[Native row documentation](https://learn.microsoft.com/en-us/windows/win32/api/tcpmib/ns-tcpmib-mib_tcprow_owner_pid).

Microsoft describes returned table size as estimated. An eight-byte unused tail
in older captures therefore does not establish a row-stride/offset error. The
decoder parses only the count-delimited rows after ABI verification.
[GetExtendedTcpTable](https://learn.microsoft.com/en-us/windows/win32/api/iphlpapi/nf-iphlpapi-getextendedtcptable).
IPv6 scope IDs are network-order DWORDs and remain distinct; this packet has
synthetic IPv6 coverage, with no live IPv6 control execution.
[IPv6 row documentation](https://learn.microsoft.com/en-us/windows/win32/api/tcpmib/ns-tcpmib-mib_tcp6row_owner_pid).

The first independent closed-row audit checks six selected rows from the earlier
extended-only control. It constructs derived single-row frames from exact saved
rows; it does not reconstruct or claim original full OS tables. Raw unrelated
tables, identifiers and private diagnostics are not uploaded.

The independent public-result audit verifies all five source/tool pins, known
owner/worker closure, request/result/report bindings and all14 selected raw rows.
Their state counts are0:9,1:2,5:3; no2 occurs. Exact hashes and fields agree with
independent decoding. Its byte/metadata checks do not authenticate execution by
themselves. Public controls hash:
`289f46e5f62cf41bce518ecde21d247c1b39d7358a77ab9003a789ea5e71868d`;
private audit JSON hash:
`ba61d6cc5a1f2a959685635954147d167203c8de2e72203518034afe4d240aa4`.

Correction to the initial report at3b800160 and ticket progress: saying all four
public paths reported listener0 was inaccurate. The exact distinction above is
established by the independent audit; both0 and1 fail LISTEN2. The initial
source ZIP remains unchanged, preserving that historical report alongside this
correction. The diagnostic did not rerun or modify any captured observation.

## D: evidence recovery

The create-only producer and independent verifier both actually exit0. Recovery
at `D:/Dev/Archives/LocalLore/2026-10-28-listener-observation-v1` contains115
original/copy entries,116 ZIP members and118 files totaling17,470,536 bytes.
Both passes find zero missing/mismatched bytes and exact output/ZIP rosters.
Selection is a fixed finite list of closed test/control families, private
helpers/reviews/audits, source-only controls, the source ZIP and its metadata,
and the separately attributed corrected report. No broad input inventory,
model weights, caches, emulator state, credentials, saves or APKs are included.
Originals and earlier recovery sets remain untouched.

The independent verifier repeats every original/copy/ZIP hash, closed owner
chain, exact same26 test/source/ordered-ID RED/GREEN comparison, final28 and
integrated71 counts, source snapshot binding and public failed consistency
outcome. The exact26 test bytes are recovered from Git with CRLF conversion
matching both captured request hashes. The decoder import-only RED is retained
with its narrower attribution. A pre-execution review also corrects the
verifier's initial assumption that Root's inline owners use separate owner files;
the corrected verifier runs against the original recorded formats.

| Private artifact | Bytes | SHA256 |
| --- | ---: | --- |
| Source ZIP at3b800160 | 8,602,900 | `ad7c447b766a9207c1d58298f1a5ad6e63994da13003c45c13b52f01b7f19a74` |
| Recovery index | 76,345 | `10dfb6aa0e2ac76fa0565737c7652f8ba7c0e8c8d7678f3ce25082a26ef25ea2` |
| Recovery ZIP | 8,426,485 | `628e1b3099786efeaeec5d24b74bfaccf403ba998953632ac4074c6ddc6d9386` |
| Producer result | 846 | `7027610499ce973f135a89a0e0419c44c85d78788549d32f6af8fb3dfa02abd7` |
| Independent verification | 2,039 | `dfa2dc0f18edada189c42f763f244606a81b68202a39509ab00ce1793a5f6ef9` |

Producer source is22,334 bytes/SHA256
`025eaba9377a14e51363f96efe564a24ffb7daa69f10063d8e6764180000cdab`;
independent verifier24,944 bytes/SHA256
`4b1b8017c0172c5b4b5b2bc92e235bed38db1c59756c9a2f0ceae67c97a2e270`.
Root's `run-preservation-v1.py` creates the exact admitted selection and invokes
the producer; `verify-listener-v1.py` runs with all four actual admission/index/
archive/result digests. Both commands use `python -I -B` from the physical D:
checkout with D: TEMP/TMP. Source archive metadata binds exactly3b800160 and the
Git ZIP comment, not full Git history. Its initial prose and c0a1f6be's correction
are separately preserved. This later recovery paragraph is committed/pushed in
Git after that immutable seal; it is not inside that source ZIP. Private recovery
proof establishes byte preservation, never feature acceptance.

## Next admission task

The legacy observer, default, record schemas and25 client tests are unchanged.
Unknown0 is not a fallback. No existing service is contacted by this packet.
The approved fresh D: emulator/model setup remains unused and gated by reliable
service admission plus current source/build/resource checks.

An independent design review proposes a separate explicit versioned observer:
hold one connection, require exact reciprocal ESTABLISHED5 tuples attributed to
the pinned kernel processes before sending, then require a bounded fixed
host:version frame/EOF and process/file/endpoint brackets. A canned reply or
successful connect alone cannot qualify it. This protocol is not implemented or
executed here, and cannot reclassify legacy failures. Implement/test that distinct
proof next, retaining strict ambiguity, identity, timeout and resource refusals;
then execute the approved fresh import and one AUTHOR attempt if it qualifies.

M10.02 supporting diagnostic implementation is in_review. M09.06/M01.01 runtime
qualification remains blocked; full milestone checkboxes remain unchanged.
Physical-device availability/identity is not re-observed here. No phone absence,
ARM64, quality, performance, complete journey or release claim follows. No
existing emulator stop, state reset/relocation, system setting, service lifecycle,
merge, release, new dependency or private/model upload occurs in this packet.
