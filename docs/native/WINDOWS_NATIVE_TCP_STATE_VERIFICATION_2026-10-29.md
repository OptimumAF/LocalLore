# Compiled Windows TCP control — 2026-10-29

M10.02 supporting M09.06/M01.01. Executed source is
`12ece0ea04ba01aea6e9285fe09b6a775dd02ef0`, stacked on open/unmerged PR #249 at
`d0088f3f`. Later evidence/documentation commits are separate. Full task
checkboxes and owner acceptance remain required.

The independent compiled control **acquires successfully but is inconsistent**.
Every listener observation is raw0; connected server/client pairs are raw5/1,
despite successful listen, SO_ACCEPTCONN1 and a complete bidirectional exchange.
This reproduces listener inconsistency outside Python FFI. It does not establish
the specific ADB server0 cause, an OS/provider diagnosis, or service admission.
No existing gate or failed historical result is changed.

## Implementation

See the [frozen protocol](WINDOWS_NATIVE_TCP_STATE_PROTOCOL_V1.md).
`benchmarks/native/windows_tcp_state_control.c` uses actual Microsoft SDK
definitions, compile-time sizeof/offsetof/table-class assertions and direct
native calls. It creates only three self-owned exclusive/ephemeral loopback
sockets, refusing port5037. Its10-second work budget and nonblocking socket
operations sit under a30-second owned job, with additional bounded cleanup.
One sizing/data pair per query, fixed phases, raw row ordinals and finite
partial send/receive prevent favorable polling, reconnect or replay.

`benchmarks/windows_native_tcp_state.py` adds a pure closed-schema assessor and
explicit launcher. The assessor preserves every raw state, assigns reciprocal
roles by endpoint tuples, checks exact observed PID where supplied, and treats
basic-table rows as tuple observations without PID authority. Acquisition and
LISTEN2/ESTABLISHED5 consistency are separate. Metadata and hashes alone do not
authenticate a build or execution; the executing parent admits actual source,
tool, command, binary and started-process evidence separately.

The new scoped owner assigns its job and records actual native PID/creation/
executable BEFORE releasing binary stdin. The legacy owner announces after
stdin, so a fast compiled worker could otherwise finish without a started
receipt. Legacy owners, observers, held-v1, SDK2/SDK3 readers and original tests
remain unchanged. Resource failure retains an unqualified result. Safe pipe
closes continue after a job failure; an unstarted reader cannot escape cleanup.
The inherited process/job helpers still have unchecked CloseHandle returns;
captured cleanup flags are not a blanket proof of every Windows handle close.

Independent agents own C source and original adversarial tests in separate D:
worktrees; Root owns shared contract/reader/owner, integration and execution.
Another independent read-only review exposes the thread-start error before its
fix. Review is source evidence, not human acceptance or native execution.

## Actual checks and preserved failures

All commands start from physical
`D:/Dev/Worktrees/LocalLore/LocalLore-starter-native`, with process TEMP/TMP/
TMPDIR=`D:/Dev/_Temp`. Private root B is
`D:/Dev/Experiments/LocalLore/2026-10-29-native-tcp-state-v1`.
Installed Python3.14.7 uses `-I -S -B`. No runtime/model dependency changes.

| Check | Actual result |
| --- | --- |
| Original pure report fixtures | 27 pass, known child0/213ms/cleanup and capture true |
| Expanded launcher coercion cohort | 36 tests, two failing assertion subcases; False/0.0 stderr counts incorrectly qualify |
| Exact same36 after closed owner typing | All pass, known child0/767ms; test bytes unchanged |
| New scoped owner cohort | 46 pass, child0/870ms; mock target changes explicitly from legacy env owner to new scoped owner |
| Thread-start exhaustion cohort | 48 tests, one actual RuntimeError, not an import error; unstarted join skips receipt/capture cleanup |
| Exact same48 after fix | All pass, child0/819ms, nine selected source hashes stable; no weakened assertions |
| Root integrated cohort | **355 pass, zero failures/errors/skips**, child0/31,883ms, cleanup/capture true, stderr0,25 selected hashes stable |
| One actual fast Python barrier child | child0/40ms,21 stdout bytes/stderr0, actual started identity recorded, known cleanup/capture; no native TCP calls |
| First native C11 compile | Compiler2/worker1, owner1,523ms, complete capture/cleanup; installed SDK C5105 under/WX |
| Corrected native compile, same C bytes | Compiler0/worker0, owner1,220ms, full capture/cleanup; ABI assertions compile |
| ONE actual compiled control | Acquisition true; observation consistency **false**; native child0/48ms, full capture/cleanup |
| Git diff whitespace check | Pass |

Root command is `python -I -S -B B/packet-native-v1.py check`. Its exact unittest
modules are new `scripts.tests.test_windows_native_tcp_state` plus all10 modules
from the [previous SDK3 integrated307](ANDROID_SDK3_VERIFICATION_2026-10-29.md).
The355 are48+307, not additional to those overlapping cohorts. SDK/target calls
are mocked; unchanged legacy driver cases include owned Windows subprocesses.
Selected25 source/test bytes exactly match the executed Git source ZIP. This
does not claim every repository file was tested.

`packet-native-v1.py fast` executes the one actual barrier child. The first build
uses `packet-native-v1.py build`; corrected build uses `packet-native-v2.py build`.
The original private helpers/captures remain immutable. A V2 pre-control wrapper
incorrectly still references failed build-v1 and refuses BEFORE any native
dispatch. Its exact source and explicitly labeled tool-output transcription
(not invented raw capture) remain retained. V3 changes only those two references
to successful build-v2; `packet-native-v3.py native` dispatches the control once.

## Toolchain and build boundary

Installed cl.exe file version19.34.31937.0 (MSVC directory14.34.31933) and Windows
SDK10.0.19041.0 are used in place. First `/std:c11 /W4 /WX` compilation genuinely
fails on SDK `winbase.h` C5105. Corrected command uses Microsoft's documented
[`/external:I` and `/external:W0`](https://learn.microsoft.com/en-us/cpp/build/reference/external-external-headers-diagnostics)
for the installed SDK/compiler include directories; own C `/W4 /WX`, static ABI
assertions and all48 adversarial assertions remain. There is no broad source
warning-disable, SDK edit, package install or global tool setting change.
Record this build-policy distinction rather than calling the first build passed.

Sixteen selected installed compiler/linker/header/library byte pins remain
unchanged. Compilation records165 include observations/139 unique header paths,
bound after compilation; this is not a claim that every transitive header was
pinned before compilation. Source and build requests bind the fixed command and
same25 critical sources. The139,264-byte AMD64 PE is private recovery data,
SHA256 `e7e18cd4a4a1206e253dc59e6f7b22ff8d1efdf4da10d1cf37621504a4a3b48d`.
Only compiler/OS libraries already installed are used; no binary/SDK files are
published. Microsoft lists SDK19041 as [out of support](https://learn.microsoft.com/en-us/windows/apps/windows-sdk/);
this existing diagnostic toolchain is not a production SDK support decision.

## Acquired native observation

The native report is4,223 bytes, core15ms. All12 fixed API pairs complete;
selected raw rows24, with independent 20/24/28-byte ABI decoding. State results:

| Phase | Four listener paths | owner_all/basic/owner2 connection pairs |
| --- | --- | --- |
| after_listen | 0 /0 /0 /0 | Not connected yet |
| connected | 0 /0 /0 /0 | Each server5 /client1 |
| exchanged | 0 /0 /0 /0 | Each server5 /client1 |

SO_ACCEPTCONN is1 at each phase. Exactly17 bytes are sent, received, echoed and
received back, with both actual buffers equal to `LL_NTCP_CONTROL1!`. Created,
close-attempted and successfully closed masks are7/7/7; WSA startup/cleanup flags
are true. The scoped owner measures child0/48ms, stderr0, complete capture and
cleanup. Source/Python/binary/caller before/after pins agree; actual started
native identity joins its report. `qualified_acquisition=true`,
`observation_consistent=false`, `feature_acceptance=false` remain separate.

PowerShell's outer tool reports exit1. The Python source maps acquired
inconsistency to2, but a standalone CLI2 is not separately measured; do not
invent it. The actually captured native worker exit is0. No exit code converts
the inconsistent observation into a passed consistency or device gate.

Independent closed audit runs8,712ms, manually decodes every selected row and
ordinal using `<5I`/`<6I`/`<7I`, checks12 API pairs, bounds, identities/endpoints,
exchange, closure, PE machine, sources/tools/builds and known owners. It calls
the pure assessor only as a second comparison. It does not rerun the control,
any SDK command or native observation. Audit27,433 bytes/SHA256
`a4f041687e0fd734aca3e9a795a6e14559fed63fa5fec07039be6d91fb78ef1b`;
verifier14,253 bytes/SHA256
`8a67b1d7a31fdec0a18828289beea5e558be2263090b0dc4098fa520374bb78a`.

| Captured artifact | SHA256 |
| --- | --- |
| Root355 result | `9c9130bc44ef7d0686467da6dd85252744a4f43007e4b09973d9e6ca18d97d26` |
| Failed first build result | `5ee618ca3944f65812a87a791cf86af9e8c72afeea7fdaa6a8d2496fbb0683bf` |
| Native control result | `3a9def08d29b111315157f1ede608f5648490344f5bd0d511386bfeed2559e9a` |
| Original native report bytes | `4b748b39d9b23b07dc61dcb2db6a7108d6897272672dbe3ec9adc536c4dd4f3e` |

## D: preservation and next runnable work

Create-only recovery at
`D:/Dev/Archives/LocalLore/2026-10-29-native-tcp-state-v1` retains1,124 original/
copy pairs and1,126 ZIP members, including failed/corrected tests/builds/helpers,
exact source snapshots, binary/object, actual fast/native records, reviews and
closed audit. It also preserves102 specifically owned synthetic launcher fixture
directories/1,014 files from D: TEMP; their fake `.exe` bytes are not real apps or
device tests. Source ZIP binds executed12ece and all25 selected test/source SHA
bytes exactly, with no line-ending or evidence normalization. Models, saves,
emulators, credentials, installed tool/header/library contents and prior recovery
are not copied or modified. Later documentation commits are outside this source
ZIP and are separately committed/pushed.

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| Index | 694,281 | `65d76b72e5e577b57b85a949ee2cb81a14da12e154a5eb8e94198bb01188f673` |
| Evidence ZIP | 9,143,021 | `dcd5d6a5a2e49c002c23b16052db34a9a1fcbf7a5ffa7f5b763803822ce65625` |
| Source ZIP | 8,706,599 | `939ab55f2eb0ac12075abc72a77cd04779160bfb5d5a4e7fcad53b94527f1d8c` |
| Producer result | 762 | `da49b2a3bbfd715fbb869df05dee425f72ef7baf6cf200fa64a0cd1d46e49129` |

Producer actually exits0 in9,834ms, checking every original/copy/ZIP byte and
source Git blob. This is preservation, not replay or device qualification.

M10.02 supporting implementation is proposed for review. M09.06/M01.01 current
runtime remains blocked on trustworthy service admission; fresh full Android
build, model import, one AUTHOR and inference-free reopen are unrun. The exact
fresh D:8GiB/four-core/30-minute guest/model permission remains unused. No phone
availability/identity is re-observed, and no phone absence or ARM64/performance/
model-quality/full-journey acceptance is claimed.

Next runnable work is an explicit isolated owned-server feasibility/protocol
slice, preserving current shared-service refusals. AOSP documents
[`-L`/`-P` and a USB-only `--one-device` filter](https://android.googlesource.com/platform/packages/modules/adb/+/refs/tags/android-16.0.0_r4/docs/user/adb.1.md);
a private port alone does not isolate automatic transports. Pinned upstream
[emulator scan code](https://android.googlesource.com/platform/packages/modules/adb/+/290ccb5dfe946d4dd39a6b8e584dd11ecd61779e/transport_local.cpp)
supports a process-local scan limit, but installed-binary behavior, USB/mDNS
exclusion, actual lease/endpoint ownership, lifecycle authorization and a single
authorized guest target still require implementation/tests/admission. No new
server is launched here. Do not replace positive ownership with a reply-only
check, silently drop a gate, or reclassify any previous failure.

No other emulator stop, system/global tool setting change, existing/global
service lifecycle, SDK/device/emulator/model operation, private upload, merge or
release occurs in this packet. Application Rust/Kotlin/SQL and inference
dependencies remain unchanged.
