# Android cancellation acknowledgement, 2026-10-23

Refs [#9](https://github.com/OptimumAF/LocalLore/issues/9), M05.04 partial,
and [#8](https://github.com/OptimumAF/LocalLore/issues/8), M04.04 supporting.
Base: accepted `b90ddc9c0ed955c034a6c1f9e331caf3323e4e9a`.

## Boundary and frozen regression

The actual Android gateway discarded its pending recovery key after any
non-committed cancellation reply. Unlike the existing committed-receipt decoder,
that path did not first validate the turn, scope, expected revision or terminal
phase. Cancellation through recovery and story switching shared this gap.

A cancellation acknowledgement must match the original request's turn, scope
and expected revision and be committed, cancelled, failed or stale. An unfinished,
foreign or malformed reply leaves the original key cancelled and retained.
Recovery can retry cancellation with that key; it must not submit, prepare,
commit, close or replace the session based on the invalid acknowledgement.
The existing explicit UnknownTurn disposition and release-only Closed handling
remain separate. A matching committed race reconciles accepted saved history.

This is transport/recovery validation, not a new gameplay authority. Rust still
owns proposals, accepted events, receipts and SQLite transactions. No host wire,
canonical rule, schema, prompt, runtime, model or dependency changes are needed.
The volatile gateway key is retained for that gateway lifetime; this packet
does not add process-restart persistence or prove native worker reclamation.

Independent tests were frozen at `b6e3b0842393c2708b4a41e475bdc0a53b9d7363`
before production correction, imported as `e8bd390`. Nine AndroidJUnit4 methods
exercise the actual DurableGateway and platform JSONObject with a synthetic
WorkspaceTransport. They cover cancellation, cancelled recovery, create/resume
release, wrong identifiers/revision, missing fields, unfinished replies, malformed
committed receipts and valid terminal races. No Activity, NativeWorkspace,
SQLite or inference call is made. Local JVM Android stubs are not used as proof
of these protocol cases.

## Reproduction commands

The explicit debug profile keeps installations and task history separate from
existing apps and saves. From `apps/android`, with the existing Java 17/SDK/NDK
and Rust toolchain configured:

```powershell
.\gradlew.bat :app:assembleDebug :app:assembleDebugAndroidTest :app:cleanTestDebugUnitTest :app:testDebugUnitTest :app:lintDebug -PlocalLoreCancelAckVerification=true --project-cache-dir .gradle-cancel-ack -Pkotlin.incremental=false --offline --no-daemon
```

It selects `org.locallore.app.cancelack`, `app/build-cancel-ack` and the exclusive
project cache. Release, mixed verification/capacity profiles and mismatched
caches are refused. Ordinary package/output defaults remain unchanged.

After source/artifact/identity/capacity admission, install only this app/test pair
on an authorized emulator and select this exact class with AndroidJUnitRunner:

```powershell
adb -s <authorized-target> shell am instrument -w -r -e class org.locallore.app.CancelAcknowledgementTest org.locallore.app.cancelack.test/androidx.test.runner.AndroidJUnitRunner
```

Require all nine method start/terminal pairs, no skips/unfinished methods, and
the final runner terminal after those pairs. ADB exit zero is not a test pass.
Private diagnostics and transport identifiers remain local.

## Checks observed before device regression

The full host script selection passed **185 tests in 13.952 seconds**. The
baseline app/test APK build completed once in **213,641 ms**, child zero with
known Windows Job cleanup, including both native ABIs. It retained the unchanged
base gateway SHA256 `ba0542f22673da56a49ae9fd58928a1824265298d9c4f156cd259cea44ff125f`.
An existing FrameworkInterruptionTest AtomicReference/Boolean warning remains.

Four configuration probes correctly refused release, mixed verification,
capacity mixing and wrong project cache. The APK audit passed exact isolated
app identity, SDK26/target36, its one signature permission and four aligned
native libraries. The test APK has the exact runner/target and its existing
test-only REORDER_TASKS permission; it contains no native libraries.

Private build/audit preparation errors remain retained: the model-process
helper refused a build-sized budget before launch; a separate build-only Job
owner was used without changing production inference bounds. Audit drafts
initially omitted universal newline handling and looked for instrumentation
identity in badging rather than its actual XML tree. Corrected raw-first audits
used the same unchanged APK bytes and original policy. No failed draft was
presented as a device result.

The device harness passed 18 overlapping host mock methods after independent
review corrected mount-alias proof and runner-terminal ordering/framing. These
are parser/ownership fixtures, not induced native faults. Fresh namespaces
retain every stopped admission rather than retrying or overwriting it.

## Device admission limitations

The first cohort stopped after one failed A process-query client, with no install
or test. A separate inventory proved no emulators were present. Under the user's
earlier explicit permission, only the two existing test AVDs were relaunched
hidden with exact prior settings and existing data. Previous live-instance
continuity remains unverified.

The new cold two-target cohort passed seven A read-only commands, including
API35/x86_64/4096-byte pages, process absence and same-device alias proof. It
then stopped at storage: **1,045,565,440 bytes** available versus the fixed
**1,207,959,552-byte** admission threshold, deficit **162,394,112 bytes**.
It performed no package-map query, installation, test or B call. A remains
blocked; its data and admission criteria were not removed or weakened.

A separate B-only cohort retains the same storage, source/APK, package-map,
ownership and nine-method requirements. It cannot establish a two-emulator,
physical-phone, ARM, real-model or full M05/M04 gate. Actual regression and
candidate results are recorded below only after execution.

The first B-only attempt passed its preflight and original 23-package map, then
successfully installed the isolated app. Its parser rejected the actual bounded
`Performing Push Install` / `Success` output and stopped before test installation.
The raw success, stderr count and stopped result are retained. A new fixed
partial-state admission required the exact app hash and absent test package;
it skipped that already installed app and installed only the missing test APK.
It did not clear data, reinstall the baseline app or turn that stopped attempt
into an executed test. Uniform LF/CRLF success framing is now checked exactly.

## Actual regression and correction

| Same nine frozen methods on B | Passed | Failed | Owned commands | Duration |
|---|---:|---:|---:|---:|
| Unchanged base gateway | 5 | 4 | 41 | 10,781 ms |
| Corrected gateway | 9 | 0 | 42 | 11,016 ms |

Both invocations completed child zero with known Windows Job cleanup, all exact
method start/terminal pairs, no skips or unfinished methods, and successful final
namespace-absence, capacity and package-map checks. Child zero alone was not
used as test success. The original 23 B package hashes matched in every observed
before/installed/after/final map. No A protocol test ran.

The three cancel/create/resume methods first failed at the foreign-turn reply.
Cancelled recovery first failed at `ready`. The malformed committed-receipt
method already passed on the baseline, as did the other four positive methods;
it is preserved regression coverage, not a newly failing case. The same test
APK and source bytes were used for RED and GREEN without oracle changes.

Production correction `8b30155a2132ef59a4f69d2089e41eb9332475d0` adds one
shared acknowledgement check before the existing complete result decoder can
release the key. Cancel, cancelled recovery and release all use it. Existing
committed receipt validation, UnknownTurn and release-only Closed handling stay
intact. No successful result is manufactured from an incomplete response.

The candidate app/test build plus a fresh JVM selection and lint completed in
**77,218 ms**, child zero with known cleanup: **147 JVM tests passed**, zero
failures/errors/skips; lint **zero errors / one GradleDependency warning** for
the deliberately pinned coroutines version. Rust build outputs were reused;
all four packaged native-library hashes are identical to the baseline. Both
ABIs were built in the baseline; ARM execution is not inferred.

| Artifact | Baseline SHA256 | Candidate SHA256 |
|---|---|---|
| App APK | `c75741d371b39067de2bf1c0ecb290f3d688ace78437183c9771f7c65f1cda6b` | `342d71e5d68913af1ec16f3f4789723f082739e4836b101b716d78906f36a1cd` |
| Test APK | `43cecd946901b002a9056ec2522d8255ff66f94785660055aa775637ade9c147` | same |

App sizes were 22,335,188 / 22,524,075 bytes; the unchanged test APK is
1,693,073 bytes. Candidate gateway SHA256 is
`67f217690914ad05ff1b34b3cff165890265b4bf41a6971a5da5044a3b8eefd2`;
frozen test source SHA256 is
`eb84c0a579dcbbf63baca901c318f95baa3c3c7653365a92e5aa9d00ff4053c4`.
The final B userdata sample was 1,645,486,080 bytes free, above the unchanged
1,207,959,552-byte admission floor. This is protocol-test admission, not a
passing result for any earlier M01 inference consumption budget.

The [safe aggregate](ANDROID_CANCEL_ACK_RESULTS_2026-10-23.json) is **6,029 LF
bytes**, SHA256 `6a1d6605c76c50b7a6644137946b331828800ea00734bdca39185f861d506e31`.
The coordinator checked all 83 completed RED/GREEN command stdout sizes/hashes
against raw files with zero mismatches. See the [device report](ANDROID_CANCEL_ACK_DEVICE_2026-10-23.md)
and [independent review](ANDROID_CANCEL_ACK_REVIEW_2026-10-23.md). Private paths,
process/transport identities, command output and APKs remain local.

M05.04 remains **in_review, partial**; M04.04 receives this supporting slice.
The A storage gate and M01.01 physical-phone gate remain blocked. No two-device,
native cancellation, database replay, real-model, quality or sustained-session
qualification follows from these synthetic transport tests. Earlier M01
timeout/storage/preservation failures remain unchanged. No merge, release,
access/protection change or private payload upload was performed.

Next runnable task: exercise the same gateway cancellation fault through the
ShellViewModel recovery presentation, with hostile delayed replies, before any
broader native/device or model qualification. Reuse the frozen nine-method
protocol suite; second-emulator execution requires a separate capacity solution.

## Selected-file integrity

The coordinator rehashed all four device selections, **308 files / 465,678
bytes**, with zero mismatches. Their individual index hashes are in the device
report. These selections overlap source/fixture bytes and do not add up to
unique experiments. The independent reviewer separately checked the final
207-file selection and all 83 completed-cohort command outputs.

The selected host evidence binds **98 files / 48,497,497 bytes**, including
closed logs/receipts, exact app/test APKs, source copies, JVM XML, lint XML and
the public reconstruction. Index: **17,109 bytes**, SHA256
`8a913136f78f63b19f5850308577246064c24fb92f9496b1b231a2f609a6554c`.
It excludes live emulator log files and temporary build files; it is not a seal
of the entire host directory or proof of continuing emulator liveness.
