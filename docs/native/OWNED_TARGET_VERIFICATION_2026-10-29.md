# Owned emulator/direct shell-v2 verification — 2026-10-29

Refs #14 (M10.02 support), #13 (M09.06 support), #5 (M01.01 support).
Draft PR #254 is stacked on open/unmerged #252 at `33188c6e`.
This supporting implementation remains in_review, with milestone checkboxes
unchanged until acceptance. Actual source for all checks below is
`0b8bb3057756bff2a7c12a81b28bd013c09caf94`; subsequent report-only changes do
not turn those checks into execution at another source revision.

## Boundary implemented

The new owner binds the exact approved D: AVD, finite inherited Windows job,
held guest/server/launcher identities, existing-key metadata, unused private
endpoint, original prepared inputs and exact guest port/transport observations.
It spends a create-only boot claim before launch. SDK4 uses direct framed
shell-v2 on the held private server, with separate before/after complete proof
graphs and exact raw byte counts. Imports and AUTHOR have distinct create-only
claims; failed attempts stay spent. No ordinary target ADB CLI recovery, generic
host-service dispatch or retargeting is exposed. An inert compiled refuser
returns64 for emulator external ADB commands. See the
[typed protocol](OWNED_TARGET_PROTOCOL_V1.md).

Root owns the contracts, independent record reader and integration; separate D
worktrees own the owner/client, original adversaries and compatibility/closed
review. No Rust/Kotlin application source or runtime dependency changes in this
packet. Rust remains the authority for author review/create and canonical
state; model output is untrusted. Original proof readers remain unchanged.

## Executed checks

| Check at the frozen source | Actual result |
| --- | --- |
| Integrated host checks | 529 tests; 0 failures/errors/skips; 40757ms parent, child0, capture/cleanup true, 36 source/test pins stable. |
| New focused tests within that suite | 72 contract/owner/lifecycle and 25 SDK4 client tests. Native/socket effects use mocked seams except the separate real inert-process check below. |
| Refuser compile | Installed MSVC14.34/SDK19041, C11 /W4 /WX /MT; 195ms, child0, known capture/cleanup. Three actual inert version/start-server/kill-server argv cases each return64 with empty streams; no ADB executable is invoked by them. |
| Real Windows owner API self-check | 262ms, child0, known capture/cleanup. Actual x64 PBI48-byte layout, own-job PID roster and one held inert Python child's ancestry/termination/wait/checked close. Qualifies these native calls on an inert process only. |
| Android offline build/JVM | 45822ms, child0; 588 tests / 58 report classes, no failures/errors/skips; both APKs assembled; 2059 tracked inputs stable. Build lint was up-to-date, not fresh analysis. |
| Separate fresh lint | 76708ms, child0; analysis_did_work=true, 0 errors / 10 warnings, 2059 tracked inputs stable. Kotlin/Gradle warnings also retained. |
| Fresh approved AVD preparation | 4040ms, child0; prepared=true, booted=false at this checkpoint; closure verified. 8GiB/four cores. Preparation stderr645B was counted but not retained by the older helper; its content is unknown. |

Product APK: 78289152B, SHA256
`0ad6f03adf0179438570c7d4a7933f2ef7b1fd929ce7361c2627749168439fa9`.
Test APK: 2251299B, SHA256
`58c423631737e312df4bc65082b6ae6723a4953336f735af3f7a832ef177db2d`.
Independent build audit rechecks all2059 Git/source inputs,921 compiled inputs,
all588 method reports, both ABIs' prompt1.1/export, test DEX prompt1.1,
62 dependency rows (including an identical duplicate core row), and67 analyzer
artifact rows. Separate fresh-lint audit verifies current artifacts and leaves
the original build-lint/up-to-date record unchanged. Ten lint warnings are
UsableSpace7, OldTargetApi1, GradleDependency1, ObsoleteSdkInt1.

Actual installed tools: emulator35.3.12.0/build12990079; ADB37.0.1-15733141;
Python3.14. LiteRT-LM Android0.18.1 and the Gemma4-E2B local model
configuration are unchanged. Local model is
2588147712B, SHA256
`181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`.
The approved guest is Android35/x86_64, not physical-phone or ARM64 evidence.

## Preserved failures and corrections

Original adversaries caught measured altered stdin being discarded, rejection
of the owned qemu self-bridge, loss of completed exit/EOF status after sender
cleanup failure, a cross-thread clock-check race, acceptance of the ordinary
qemu path and noncausal readiness, and incomplete commit/disk replay. The exact
negative assertion bodies pass after fixes. Expanded positive lifecycle/native
fixtures were corrected separately; those edits are not represented as identical
whole-cohort RED/GREEN tests. All original failed captures remain private.
Initial client-binding fixture errors and mocked native-constructor seam errors
are test setup failures, not product failures. A private preparation v1 script's
duplicate-keyword SyntaxError occurred before execution; v2 is a separate actual
preparation. The final private controller review fixed the raw-regex warning,
explicit late-failure reasons and collection of the known workspace-v1 /
archive-staging directories before any dispatch. It collects allowlisted proof
files only, never either database directory. The earlier scripts remain intact
in their separate recovery snapshots.

## Primary-source compatibility

The ordinary [ADB client's mismatch recovery branch](https://android.googlesource.com/platform/packages/modules/adb/+/9084198a2d4b0f6a0f174260fb42da33485b684d/client/adb_client.cpp)
can attempt kill/restart even with numeric-H; this is why SDK4 uses fixed raw
frames. [Shell protocol definitions](https://android.googlesource.com/platform/packages/modules/adb/+/9084198a2d4b0f6a0f174260fb42da33485b684d/shell_protocol.h)
and the [daemon implementation](https://android.googlesource.com/platform/packages/modules/adb/+/9084198a2d4b0f6a0f174260fb42da33485b684d/daemon/shell_service.cpp)
require a five-byte header, one-byte exit and empty CloseStdin. ID-selected
transport requires OKAY only, followed by the raw service on the same socket.
The implementation rejects malformed, trailing, oversized and unknown frames.

[QEMU's private notifier](https://android.googlesource.com/platform/external/qemu/+/ae9d18d2b6261179fbd57fffec720a04f7bfb053/android/emu/adb/interface/src/android/emulation/AdbHostServer.cpp)
uses process-local ANDROID_ADB_SERVER_PORT for host:emulator notification with
no default-port fallback. [ADB_EMU](https://android.googlesource.com/platform/packages/modules/adb/+/1cf2f017d312f73b3dc53bda85ef2610e35a80e9/client/main.cpp)
gates scanner initialization; [explicit registration](https://android.googlesource.com/platform/packages/modules/adb/+/9084198a2d4b0f6a0f174260fb42da33485b684d/client/transport_emulator.cpp)
remains available, deriving emulator-5592 from5593. No manual TCP alias is used.
Headless qemu is pinned separately. Installed hardware-properties default-1
and explicit0 disable the optional boot timeout; positive values refuse.
Earlier static reports' timer0-only wording is retained and explicitly corrected.
Three installed offline emulator help/environment/version calls complete71/46/
561ms with exit0; matching binary strings corroborate source, not exact installed
source attestation. Dependency/model versions and global settings are unchanged.

## Exact execution and recovery

All project commands execute from the physical D: Root checkout with process-
local TEMP/TMP/TMPDIR=`D:\Dev\_Temp`; outputs remain under D. Finite private
helpers retain exact argv/environment/source/request/receipt and raw captures:

- `python.exe -I -S -B <private>/check-owned-target-host-v1.py` loads the14 test modules recorded in its request.
- `python.exe -I -S -B <private>/build-sdk-v1.py` uses the installed Java Gradle wrapper, offline/no-daemon/no-build-cache/max-workers2, D caches and existing signer read in place. Tasks are cleanTestDebugUnitTest, testDebugUnitTest, lintDebug, auditLiteRtDependencies, auditLintAnalyzer, cleanPackageDebug, cleanPackageDebugAndroidTest, assembleDebug, assembleDebugAndroidTest.
- `python.exe -I -S -B <private>/lint-current-v1.py` preserves the same prefix and runs --rerun-tasks :app:lintDebug :app:auditLintAnalyzer separately.
- `python.exe -I -S -B benchmarks/owned_target_owner.py --admission <private>/target-admission-v1.json --admission-sha256 4ef2ff2f9f5677279f4d6b3559b948cb3eb8fcb8061694cef71b9a708e90556e` starts the sole1700-second owned run inside the approved1800-second maximum.
- `python.exe -I -S -B <private>/run-target-model-v1.py` binds both APKs/build and all2059 inputs before its1350-second supervisor /1200-second SDK session. No automatic retry is permitted.

Private root is `D:/Dev/Experiments/LocalLore/2026-10-29-owned-target-v1`.
The preboot recovery archive has484 private files /85384983 original bytes plus
all2059 source files at the frozen Git head. Independent readback verifies ZIP
members and source Git blobs. Its current-original equality audit fails solely
because the controller was subsequently revised before dispatch: original
13015B/SHA18dfcae3 versus final13431B/SHA01661675. The later five-file driver
archive matches all current originals. Both dated snapshots remain intact;
no audit is rewritten as favorable. Models, guest disks, credentials and raw
private diagnostics are not uploaded; repository push alone is not backup.

## Actual target and single-model attempt

The sole approved guest boots and self-registers on private15937 as the sole
owned transport. The first controller remains **failed**:228563ms, child1,
known capture/cleanup,20 qualified direct commands, both APKs installed and
installed byte hashes matched. It refused before probe/model/import/AUTHOR.
Its df parser expected mount `/data`; actual Android35 returned `/data/user/0`
with10833416KiB available, above the unchanged two-model-plus-2GiB floor.
This is a private controller mount-label defect, not insufficient capacity.
All148 original closed files are separately archived and readback-verified.

A distinct continuation binds/replays that failed graph, exact raw LF storage
bytes, original helper and recovery; checks the same live admission/owner/guest/
transport, user0, installed UIDs/APKs and absence of spent attempts; and skips
both boot and installation. It accepts only the additional exact `/data/user/0`
mount alias with the same available-byte floor. No clear/reset, favorable
rewrite or retry of an import/AUTHOR attempt occurs. A draft continuation's
CRLF expectation failed during a file-only check before dispatch; the raw
capture actually contains LF. Its draft is retained separately. Final helper
15197B/SHA55048085 binds the actual LF bytes, without normalizing the capture.

| Actual continuation gate | Result |
| --- | --- |
| Binary probe | All65 bytes transferred; device SHA matches the original probe, including 0x1a/CRLF/NUL. |
| Model source transfer | All2588147712 bytes and SHA match; measured SDK command41331ms, exit0; subsequent device hash matches. This is not inference latency. |
| Model import | Original proof passes;19920ms app phase /25869ms SDK instrumentation; source opened1/closed1 off-main; accepted model matches. |
| App-process boundary | Only the owned test app is force-stopped. AUTHOR runs in a different process with the same admitted app UID/APKs and bound prior import. |
| Real AUTHOR | One attempt, completed33336ms app phase /39500ms SDK instrumentation. One engine/conversation/send;349chunks,715response bytes; DONE1, errors/cancel/uncertain0; known conversation and engine close1each. |
| Canonical proof | Original AUTHOR, diagnostic and JUnit validators pass at prompt initial-world-v1.1. Native review/create, idempotent retry, archive provenance and created/reopened snapshot equality pass. |
| Complete continuation |532929ms supervisor, child0, empty streams, known capture/cleanup,39 clean fully replayed SDK4 commands, observer handles closed,2059 source inputs unchanged. |
| Owned shutdown |1072338ms parent, child0, qualified_target=true /stop_requested, all15 cleanup fields true. Held qemu termination/wait/checked close passes before launcher/server cleanup. Actual qemu/launcher/server intentional exit1 is retained, not rewritten as0. |

Import proof SHA256
`cef2f592f25a71d78342126716354b283f5e057008d03be712baf7c085926ba6`;
AUTHOR proof
`93fb4022992cb9cbea7fe52bf8caa6c84352bf4efa3c52b577f24d5ce4373ebe`;
diagnostic proof
`d90bf75bbe05e027a432a69a4937096a762b5df660afdecf10bd3371587e94aa`.
Raw response remains private; SHA256
`e2551fcc88a78b5a290a3629020599b8223c2631dd9035f6f3e862a7abf7a3f0`.
The import and AUTHOR claims are each spent exactly once; the first controller
consumed neither. No second boot, model import, AUTHOR or model-response repair
is performed. The whole owned run stays below the approved1800-second limit.

Independent file-only audit executes once after both real owners terminate:
16130ms, failures[],490 closed files /327 artifacts /842 audit steps. It replays
the full target/readiness/job/stop/cleanup graph, both distinct20/39-client
cohorts, all raw proofs,148-file first-failure recovery, import/AUTHOR/
diagnostic/JUnit evidence, exactGit0b2059-file source/build closure and fresh
lint bindings. It includes the original source-model hash read; no fresh
native, socket, SDK or device action is used to authenticate a closed run.
Audit305922B/SHA256
`be6ef3ef49f881076808fc3a4c156637d804950fc74cadbf9f79b1f3dc21f86c`.

Carrier records retain feature_acceptance=false: a finite target or data carrier
cannot accept an entire milestone. The separate scoped app proofs do qualify
the measured synthetic case. Raw captures and failed records stay private on D.
Final closed-packet/guest recovery is recorded separately after this report.

## Limits and handoff

M10.02 supporting code is in_review in #254, stacked on unmerged #252. The
M09.06 original synthetic AUTHOR/import/internal-reopen gate is measured on
this one x86_64 Android35 guest; broader AUTHOR/PLAYER/UI acceptance remains
pending. M01.01 physical-phone/ARM64/sustained thermal/performance qualification
is not established; physical phone availability was not assessed here. No full
milestone checkbox is checked or milestone closed without owner acceptance.

The successful reopened story snapshot is an inference-free **internal Rust
host/store reopen** with unchanged SDK counts, not an external OS/app death
after creation. The earlier import-to-AUTHOR process restart is a separate
measured boundary. Cancellation/error/frame/source/cleanup cases are host tests;
no actual mid-generation cancellation ran in this guest. One synthetic accepted
response does not establish generation quality, general reliability, model
licensing redistribution approval, or phone performance. No full-workspace
Rust/desktop/UI suite is claimed for this Python/native-boundary packet.

Exact installed-source attestation and universal transport behavior remain
unproven. The held-handle/job proof is scoped to recorded processes and bounded
execution; it is not a universal security boundary or evidence that unrelated
processes never ran. Existing shared5037/other emulators are not stopped or
reconfigured; guest state/models/captures remain on D. No system settings,
repository access, release, merge or private upload is performed.

Next runnable host task: expose this exact measured AUTHOR/internal-reopen case
through the bounded reader and add the separately specified external post-create
restart/PLAYER contract fixture before another owned live attempt. A new live
boot/import/AUTHOR requires a fresh reviewed scope; the existing create-only
claims and frozen captures cannot be reused as authorization. Resume the broader
M09.06/M10.02 plan from #13/#14, preserving these measured gates and limitations.
