# Android cancellation acknowledgement protocol checks

Refs #9 (M05.04 partial), #8 (M04.04 partial).

This packet exercises the actual Kotlin `DurableGateway` and Android
`JSONObject` through an independent synthetic `WorkspaceTransport`. The nine
selected instrumentation methods do not launch an Activity, invoke JNI, open
SQLite, read a save or model, or run inference. Native libraries packaged in an
APK do not establish execution of those libraries.

On the second selected emulator, the unchanged nine-method suite reproduced
four baseline failures, then passed all nine methods against the corrected
gateway. The first selected emulator remains blocked by userdata capacity.
Initial preparation failures remain retained. The coordinator owns artifact
builds, manifest/native/permission audits and production correction.

## Bounded protocol

Use only the two existing selected Android 15/API 35 x86_64 emulators. Each
selected target must report boot complete and 4096-byte pages. Each admission
requires at least 4 GiB plus 128 MiB free on the host userdata volume, 10 GiB on
the private evidence volume, and 1 GiB plus 128 MiB in each target's userdata.
All LocalLore process namespaces must be absent before work. The pre-existing
complete LocalLore package maps must equal the preceding sealed read-only
inspection's exact APK hashes.

The fixed `df -k /data` response may display `/data/user/0` only with a matching
same-device `stat -L` proof for both paths. The exact previously reviewed pure
`android_phase_storage.parse_df` source is copied into the new private evidence
namespace and hash-bound; it introduces no production dependency. Machine
instrumentation records require consistent LF or CRLF framing and reject
vertical-tab/form-feed separators, an early runner terminal, or status records
after the runner terminal. These pre-admission corrections preserve the floors
and nine-method gate.

Install only the new isolated `org.locallore.app.cancelack` and `.test` packages.
Both must be absent for the baseline; a candidate admission instead requires the
exact previously pinned baseline pair. Every install verifies local artifact
hashes first. Complete installed package maps are checked before instrumentation,
after each target, and again for both targets at the final cohort boundary.
The only selected test invocation is:

```text
am instrument -w -r -e class org.locallore.app.CancelAcknowledgementTest org.locallore.app.cancelack.test/androidx.test.runner.AndroidJUnitRunner
```

The parser requires all nine exact method identities, paired start/terminal
records, sequential test counters, no duplicates, missing records, skips or
aborts, and the final runner completion marker. Assertion failures remain failed
tests even when the instrumentation command exits zero. Baseline failures must
be retained; the candidate is a separately admitted cohort, never a retry that
replaces baseline evidence.

The outer process uses the existing `runtime_spike.run_process` Windows Job,
180-second deadline and stdin-EOF barrier before any controller device dispatch.
Each adb client has a bounded output/deadline and sticky host cleanup status.
Raw stdout is durably retained before interpretation; the existing process
helper retains stderr byte counts, not its content. Any unknown client cleanup,
retention failure, identity/capacity/process mismatch or malformed test protocol
stops subsequent actions. The immediate post-run namespace probe may fail if
Android leaves a runner process alive; that is a stopped cohort, not permission
to force-stop or retry. Host Job cleanup does not prove an Android application
process exited if the controller did not complete its process probe.

There is no download, emulator lifecycle/reset, root, clear-data, uninstall,
force-stop, model operation, save access or old evidence mutation. Initial
source preparation includes pure host parser and cleanup-failure fixtures;
these do not qualify Android execution or real native cancellation.

## Observed baseline admission failure

The one admitted outer invocation completed in 2,328 ms with child return code
2 and known host Job cleanup. The first selected target's `ps -A -o PID,NAME`
command completed with return code 1, zero stdout bytes, 122 stderr bytes and
known host-client cleanup. Raw stdout and the bounded fixed result were retained
before interpretation. The helper intentionally retains stderr byte counts,
not stderr content; those counts do not prove the cause of failure.

The controller stopped at `before`, command count 1, with no device test rows.
There was no install, package-map collection, second-target command or test
execution. Boot, current package identity, capacity and Android process absence
were not established. No baseline RED result or candidate GREEN result can be
claimed. No force-stop, retry, lifecycle change, model operation, JNI or SQLite
operation followed under that admission; the device lease was released to the
coordinator.

Eighteen pure host controller fixtures passed, covering all-nine success,
retained assertion failures, missing/duplicate/foreign/skipped/aborted records,
runner completion ordering, LF/CRLF/control framing, same-device storage alias
proof, sticky unknown cleanup and retention failure. Their private raw log hash
is `b349f7b454537f00993d6ba680d3ab314a2a1b8935e5da7c72106152058e70b6`.
These fixtures do not qualify Android execution, real native cancellation or
physical-device performance. A fresh separately admitted inventory/identity
investigation is required before another device cohort; no automatic retry is
authorized by the failed observation.

## Separate cold-start admission

The coordinator independently observed no live emulators and used the user's
standing authorization to relaunch only the two existing test AVDs. This is a
fresh cold-start cohort, with no assertion of prior process continuity. A new
private namespace copied the reviewed controller and driver with only their
output-root constants changed. Source diffs, new hashes and another 18 passing
host fixtures were retained before admission; the earlier failure stayed
immutable.

The cold baseline outer invocation completed in 562 ms, child return code 2,
with known host Job cleanup. Seven read-only commands on the first target
completed successfully with known client cleanup. They observed boot complete,
API 35, x86_64, 4096-byte pages and no LocalLore process namespace. The fixed
`/data` query displayed `/data/user/0`, and the captured `stat -L` identities
matched, satisfying the alias proof.

Available userdata was 1,021,060 KiB (1,045,565,440 bytes), below the unchanged
1 GiB plus 128 MiB admission floor (1,207,959,552 bytes) by 162,394,112 bytes.
The controller stopped before package-map collection, installation, tests or
second-target operations. No capacity cleanup, deletion, resize, forced stop,
automatic retry or additional device calls followed under that admission. Its
baseline test results were unmeasured; the first target's capacity gate remains
blocked, and its failure is not evidence of a cancellation test failure.

## Independent second-target preparation

With the first target explicitly blocked, the coordinator admitted a separate
second-target-only packet with the same capacity floors, all nine tests and the
same exact old package-map criteria. The full earlier 44-package map receipt
remained an immutable input; only the second target's 23 installed packages
were freshly observed. This does not qualify the blocked first target.

The second-target preparation completed in 5,188 ms, child return code 2, with
known host Job cleanup. Sixteen commands ran. Fresh boot/API/ABI/page-size,
process absence and storage floors passed, and the old 23-package map matched.
The first isolated application install returned zero with known cleanup and
the exact stdout `Performing Push Install` followed by `Success`. The initial
install-output decoder accepted only the success line and incorrectly rejected
this valid two-line output. It stopped before installing the test APK or running
tests. No post-install map or process check ran, so the install result alone is
not a final preservation proof. Stderr's 169-byte count is uninterpreted.

That failed preparation remains immutable. A separately reviewed controller
accepts only the two exact observed/known install-success forms with consistent
LF or CRLF framing. It requires the old second-target package map plus the
exact already-installed baseline application hash and an absent test package.
It hashes the local application artifact but skips reinstalling that app, then
installs only the pinned test APK. Candidate admission separately requires both
baseline package hashes before replacing them with the candidate pair. There
is no generic resume or arbitrary package-map override. Twenty host fixtures
passed before any new admission; their raw log hash is
`19e6ed28eb5632ca61ddecdb0d6925956a8b8e63fcfb72e9ad6066f2f5918ee5`.

## Actual baseline RED on the second target

The separately admitted final preparation completed in 10,781 ms with child
return code 0 and known host Job cleanup. Its 41 commands completed with known
client cleanup. The exact already-installed application was retained, only the
pinned test package was installed, and all nine method starts and terminals
were observed. The actual result was **four failing methods and five passing
methods**, not the earlier hypothesized five/four split.

| Method group | Actual baseline result |
|---|---|
| `cancelSaved`, create-release, resume-release malformed acknowledgement loops | Failed at acceptance of a foreign turn |
| Cancelled recovery malformed acknowledgement loop | Failed at acceptance of `ready` as cancellation acknowledgement |
| Malformed committed receipt loop | Passed already on the baseline |
| Matching cancelled/failed/stale outcomes | Passed |
| Matching committed cancellation race | Passed |
| Explicit `UnknownTurn` disposition | Passed |
| `Closed` release versus generic cancellation disposition | Passed |

These are assertion outcomes from Android execution, not inferred from
instrumentation's zero return code. Baseline application SHA-256 was
`c75741d371b39067de2bf1c0ecb290f3d688ace78437183c9771f7c65f1cda6b`
(22,335,188 bytes); the test APK was
`43cecd946901b002a9056ec2522d8255ff66f94785660055aa775637ade9c147`
(1,693,073 bytes). The gateway was unchanged from accepted main `b90ddc9`.
Final package maps retained all 23 old second-target hashes plus the exact
isolated baseline pair; final namespace absence and capacity floors passed.
The first target was not queried by this packet and remains capacity-blocked.
No source or build mutation occurred during the admitted baseline cohort.

## Actual candidate GREEN on the second target

After the coordinator's correction, build and artifact audits, a separate
candidate admission used the same controller and unchanged nine-method test
source. The outer invocation completed in 11,016 ms with child return code 0
and known host Job cleanup. All 42 commands completed with known client cleanup.
The before map required the exact baseline application/test pair plus all 23
old packages; only the two isolated packages were replaced using `install -r`.
All nine exact method starts and terminals passed, with no failures, skipped or
unfinished methods. Final old package hashes, candidate pair, namespace absence
and capacity floors all passed. Final available userdata was 1,645,486,080 bytes.

The candidate application was 22,524,075 bytes, SHA-256
`342d71e5d68913af1ec16f3f4789723f082739e4836b101b716d78906f36a1cd`.
The test APK remained byte-for-byte identical to baseline `43cecd94…c147`.
Candidate gateway source `8b30155` was pinned by file SHA-256
`67f217690914ad05ff1b34b3cff165890265b4bf41a6971a5da5044a3b8eefd2`;
unchanged test source was pinned by
`eb84c0a579dcbbf63baca901c318f95baa3c3c7653365a92e5aa9d00ff4053c4`.
The coordinator separately verified all four packaged native library hashes
equal baseline; these tests did not load those libraries.

The private raw instrumentation hashes are
`42e8c236658f718b5b9c659d1904ce46e5cf1f8b4d9744ed345d8bd66ff50455`
for baseline and
`66dde76c25e87ebac36726c811e21cd8d608840abfff915d668c23ac52d5293c`
for candidate. A local-only audit rechecked every raw stdout length/hash,
command status/cleanup, exact parser result and old/candidate package map
before sealing. No further device calls followed the candidate terminal result;
all device leases are released.

## Retention and limits

Four private immutable indexes retain source-review drafts, host-fixture
failures/corrections, authorizations, raw command stdout, status metadata and
terminal results. No raw diagnostics or private device identifiers are added to
the repository.

| Packet | Selected files | Selected bytes | Index bytes | Index SHA-256 |
|---|---:|---:|---:|---|
| Initial absent-target admission | 21 | 51,058 | 3,364 | `e691ffeee9986ae6d6f442a4c29e9f351b6afdc206f24ef61c8f7edc6c48aa34` |
| Separate cold two-target admission | 30 | 60,743 | 4,999 | `f71b6dfc591f6503fc128d2ad5db58768b4007b71dbf9042ad5c3fef9ec2c907` |
| Second-target partial install | 50 | 78,949 | 8,415 | `b8790d68ed2d768b4018aaf5a12689ef83bff1cef91c47be258e34ece9e16e4e` |
| Final second-target baseline/candidate | 207 | 274,928 | 35,300 | `7ce760cb00ed570a22298ceabe9c920d08ca03558da607c4b20f565e5432c508` |

This establishes an Android transport-protocol regression and correction on one
API 35 x86_64 emulator. It does not qualify the capacity-blocked first emulator,
real JNI/SQLite cancellation, physical-device performance, ARM64 execution or
real-model behavior. Old save contents and model/cache files were not opened or
hashed by this packet; unchanged APK maps are not a canonical-file preservation
proof. The full M05/M04 acceptance gates remain pending owner acceptance and
their separate required evidence.
