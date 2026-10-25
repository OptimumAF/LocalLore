# Independent Android receipt qualification review — 2026-10-24

Refs #9 (M05.05 prerequisite), #5 (M01.05 supporting).

## Disposition

The Android qualification remains partial: the one admitted four-method run
recorded three passes and one PROCESS failure. The subsequent read-only
inspection validated the three historical proofs and current quiet package
state. A focused Binder flag repair passed host checks but has not been run on
the emulator. Its fresh v2 qualification is blocked by unestablished update
headroom; no blind retry, cleanup or floor reduction follows from this review.
M05.05 and M01.05 remain incomplete.

## Scope

This packet implements synthetic qualification of the existing receipt transaction
on the admitted Android volume. It does not activate that protocol for model
setup, replace native publication, qualify a real model or satisfy the full
M05/M01 gates. The reviewer owns only this report and performs no builds,
shared-cache changes, device/ADB operations, model operations or SDK calls.
Source, artifacts, bounded controller admission and retained execution evidence
must be checked separately; proposed behavior is not an execution result.

## Lifecycle finding and proposed correction

Keeping an AUTO_CREATE service binding after killing its child can recreate the
service. Conversely, removing the last AUTO_CREATE binding from a bound-only
service can destroy it before a later HALT transaction. A second non-AUTO binding
does not keep it running: Android 15 service-needed logic checks explicit start
state or auto-create connections. This is a concrete ordering concern, not a
claim about a device attempt. [Context binding flag](https://developer.android.com/reference/android/content/Context#BIND_AUTO_CREATE),
[Android 15 ActiveServices](https://raw.githubusercontent.com/aosp-mirror/platform_frameworks_base/android-15.0.0_r1/services/core/java/com/android/server/am/ActiveServices.java).

The coordinator's revised protocol separates HALT arming/acknowledgment from
death: arm the exact held child, release the exact AUTO_CREATE connection, then
have guarded `onUnbind` kill its own fixture process while the worker still
holds the transaction lock. A previously captured Binder death recipient must
observe death before recovery. A successful acknowledgment or unbind alone is
not death proof. The reviewed implementation follows this ordering; actual PROCESS execution did not reach its death/recovery gate.

Connection callbacks run on the client main thread; a Binder death callback may
run on a Binder thread. State and completion therefore need thread-safe
publication. Explicit unbind does not invoke `onServiceDisconnected`; null/dead
bindings still require releasing connection tracking. [ServiceConnection](https://developer.android.com/reference/android/content/ServiceConnection),
[Binder death recipient](https://developer.android.com/reference/android/os/IBinder.DeathRecipient).

## Concrete source review

The reviewed source uses one ordinary class-selected instrumentation invocation
containing exactly four methods. Equal parent process identity across its four
proofs is therefore required; this is not four independent instrumentation
launches. Only the private `:receiptproof` child is deliberately killed.
Ordinary framework instrumentation setup may restart its target even when the
controller issues no explicit force-stop command.

The child waits at DATA_FORCED for at most 30 seconds. A timer expiry could
otherwise release its lock between HALT acknowledgment and death, falsely
crediting a death-held-lock test. The final test measures from before START
and requires accepted death within 25 seconds, plus less than five seconds from
HALT through binding release and death. Since the child timer starts later,
these assertions exclude timeout-driven lock release from a passing result.

The initial source review also exposed two failure-path concerns: connection tracking must be
released even when `bindService` returns false, and a fixed local exception may
acquire copies of that same sanitized exception during coroutine stack recovery.
The final authored source tracks binding attempts separately from successful
connection and checks a bounded sanitized exception chain, rather than requiring
an always-null cause. Failure cleanup attempts exact unbinding and fixed-service
stopping, retains cleanup errors without replacing the primary failure, and
checks captured Binder death where linked. These are fixture operations, not
host force-stop commands. API 30 runtime refusals are present before the app helper's
newer process-name API calls; no manifest minimum or dependency change is needed.

Each proof boolean was traced to corresponding assertions in the source:
exclusive acceptance/reopen; actual cancellation on both sides of marker
creation; 17-byte partial preservation, explicit discard/retry, cross-control
ownership and unknown-byte refusal; synthetic admission revocation; and actual
child contention/death/source-free recovery. Synthetic revocation is not
physical ejection. The actual transaction, volume selection and reserve policy
remain unchanged.

## Filesystem basis and limits

Android exposes CREATE_NEW from API 26 with an atomic existence check/create.
This can support the exclusive marker; it is not a multi-file transaction or
power-loss guarantee. File-channel force does not establish containing-directory
durability or removable-media identity. The experiment must retain the existing
Context-derived volume admission and full receipt/owner/model validation.
[Android StandardOpenOption](https://developer.android.com/reference/java/nio/file/StandardOpenOption#CREATE_NEW),
[Android FileChannel](https://developer.android.com/reference/java/nio/channels/FileChannel#force(boolean)).

## Read-only readiness evidence

The separately admitted read-only readiness operation completed before receipt
qualification. The coordinator confirmed its original terminal; the reviewer
checked the retained owned result and all 25 raw clients: completed zero,
known cleanup, matching lengths/digests, zero installs and zero instrumentation.
Before/final maps preserved all 35 package hashes and UIDs. Final owned and
passive process counts were both zero; userdata availability was
1,299,050,496 bytes. Inventory observed four emulators and no other devices.
This is neither a receipt test nor a new external-volume capacity observation.

The owned result recorded 9,297 ms and 291 output bytes, SHA-256
`7ec05e239f3db1b10e6c924f74130b791b1da03b51ad6ae1134ca35fa980b896`.
All eight archived input bindings, 125,114 bytes, independently rehashed with
zero mismatches. Input archive index SHA-256:
`053b448809b5375cf41bfcad0a5cba611d98fbdd2cda55412d922388b128676f`.
That readiness authorization was consumed. It grants no qualification or
follow-on authority.

## Qualification evidence status

The compiled fixture source is `4d06b51ca4b9c531af70d0ad7687d1a763c61635`;
the controller integration is `95d6722f81bed8077f0d0ed4fbd4556e2f41b454`.
All 1,391 compiled source records and all 1,394 integrated source records
independently matched their copies and live files, with zero mismatches. The
integration added controller/report files; every compiled source record remained
unchanged. The core receipt transaction and active storage implementations were
not modified by this packet.

The reviewer checked actual copied test/lint XML and artifact evidence:

| Profile | JVM tests / suites | Failures / errors / skips | Lint errors / warnings | Receipt app service/fixture |
|---|---:|---:|---:|---|
| Explicit volume debug | 323 / 33 | 0 / 0 / 0 | 0 / 14 | Present only here |
| Regular SDK candidate | 323 / 33 | 0 / 0 / 0 | 0 / 9 | Absent |
| Ordinary app | 206 / 24 | 0 / 0 / 0 | 0 / 1 | Absent |

The private service's actual manifest attributes, signatures, sole launcher,
permissions and both backup exclusion sections were checked. The app APK
excludes the instrumentation test class; its test APK contains all four method
markers. Regular and ordinary app/test APKs contain no receipt fixture, service
or qualification-test marker and no service declaration. Native libraries are
packaged for both ABIs; this is not ARM64 execution. The 62 runtime and 67
analyzer artifact records match the prior origin packet; analyzer work was
reported. No new dependency or runtime selection was made.

The controller's retained 18 pure mocked tests passed with a completed owned
child and known cleanup (3,156 ms; 2,310 log bytes, SHA-256
`4f1a101eed6039af1a52e3c2c9ba3a30a4fd15bc418a74e68634460a421ad0f9`).
The mocks cover the real CLI worker arguments/barrier/deadline and refusal or
uncertain cleanup, as well as post-update package/UID drift before instrumentation.
The after-copy proof threshold was corrected to the actual retained 2 GiB
floor; no extra 63-byte runtime reserve is invented.

Before admission, the exact disabled qualification proposal independently
rehashed twice: 25 bindings, 85,780,294 bytes, zero mismatches. Proposal SHA-256:
`670f351939d93c8fbfe28d555fa12605ba378601b374aea4d74c74bcbcc84dc0`.
It binds the volume app/test APKs, exact source, source snapshots, audit and
fresh readiness identity. The reviewed controller permits two pair updates,
one class-selected four-method run and bounded proof/metadata reads. It requires
all four passes, exact proof files and final owned-process absence; it cannot
force-stop, clear, uninstall, adopt an old root or invoke a model/SDK route.
The first actual qualification stopped after three passing methods and one
failure. Acceptance/reopen, both cancellation boundaries, and refusal/discard
passed. The process method received a remote `IllegalStateException` at START,
before establishing its held-lock/death/recovery proof. All 25 raw clients
completed with known cleanup; two pair updates and one instrumentation occurred.
The owned child ended with code 2 after 30,844 ms. No after-facts or proof-read
commands ran. The reviewer checked the raw method statuses, retained output and
client hashes. This attempt does not satisfy the four-method gate.

The failed device selection independently rehashed: 178 files, 86,270,754 bytes,
zero mismatches, index SHA-256
`f00b8696e3677616a830b7ac226d7de4928da3252dbab8d7cc33704cb91ab79b`.
The complete 25-input archive (85,780,294 bytes) also matched its admitted
digests: index SHA-256
`ea603dcfde6ebea29f7d77672e35b7fb57829194a1a0e28be3d538f662cb2b6a`.
An earlier partial archive stopped when a post-terminal protocol edit changed
one live source. It remains preserved; the complete archive uses the verified
admitted source snapshot for those repository inputs. The first host selection
also independently rehashed all 2,946 files, 213,227,823 bytes, index SHA-256
`ec105395b3d0a158ebff426ca23c958d5e1648e9c8ab21fab031d231574a5b4d`.

## Focused repair under review

The service originally required the received Binder transport flags to equal
zero. Official Android 15 Java and native Binder sources show that framework
bookkeeping flags may be added and propagated to `onTransact`, even when the
caller requests synchronous flags zero. Requiring no public `FLAG_ONEWAY` bit
and a reply parcel is the appropriate synchronous check. The first raw failure
does not identify its exact failed remote check or flag value, so this source
defect is not asserted to be the captured failure's sole cause.

The reviewed two-file repair, integrated as
`5fcb7246c21f6d5ef5fa4e0816215f0d8e8cf32c`, makes that semantic check while
retaining same-UID, fixed-token and empty-payload checks. Failure messages are
fixed, bounded categories. It moves every case and proof root to a fresh `v2`
namespace; identity, token, proof schema and method logic remain unchanged. It
does not read, adopt, delete or replace the failed `v1` data. No concrete source
blocker was found in this repair. The separate recovery observation is recorded below. No repaired Android
process qualification is claimed.

The corrected volume build completed with a coordinator-confirmed original
terminal and a retained completed-zero child, known cleanup, 135,937 ms. Its
actual XML again records 323 tests / 33 suites with no failures, errors or skips;
lint reports zero errors and 14 warnings. All 1,394 snapshot records,
16,320,273 bytes, match their live files and retained copies. Only the two
volume helper/service app sources differ from the first compiled snapshot.
The app APK is 74,851,232 bytes, SHA-256
`8232c5f81284b31d392e447968a0aa87ba853e2781fa2ae7245feaec405447f8`;
the test APK is byte-identical to the first attempt. The app DEX includes the
v2 proof root and excludes its v1 literal and the test class. Signature,
nonexported nonisolated service process, backup exclusions and native packaging
remain as reviewed. Runtime and analyzer artifact records are exactly unchanged.
A passing host build does not qualify the repaired Android process path.

Primary source basis: [BinderProxy](https://raw.githubusercontent.com/aosp-mirror/platform_frameworks_base/android-15.0.0_r1/core/java/android/os/BinderProxy.java),
[Java Binder dispatch](https://raw.githubusercontent.com/aosp-mirror/platform_frameworks_base/android-15.0.0_r1/core/java/android/os/Binder.java),
[native transaction flags](https://android.googlesource.com/platform/frameworks/native/+/refs/tags/android-15.0.0_r1/libs/binder/IPCThreadState.cpp),
[native Binder dispatch](https://android.googlesource.com/platform/frameworks/native/+/refs/tags/android-15.0.0_r1/libs/binder/Binder.cpp),
and [JNI Binder bridge](https://raw.githubusercontent.com/aosp-mirror/platform_frameworks_base/android-15.0.0_r1/core/jni/android_util_Binder.cpp).

## Read-only recovery and remaining capacity gate

The separately admitted recovery completed with a coordinator-confirmed
original terminal, owned child zero, known cleanup, 8,781 ms and 290 output
bytes. The reviewer checked all 29 retained raw clients and their metadata:
all completed zero with matching hashes; no installation or instrumentation
command ran. Before/final package hashes and UIDs match all 35 expected entries;
owned and passive process counts were zero at both observations. Exactly six
old proof files were read. Their three closed check sets are true and their
recorded parent identities agree; this independently supports the three earlier
passes, not the failed PROCESS phase. The fresh v2 proof namespace was absent.
Candidate absence in these old proofs is historical; this inspection did not
remeasure internal or Context-derived external candidate-root absence.

All 75 recovery selection files, 115,994 bytes, independently rehashed with
zero mismatches. Index SHA-256:
`759a743b82ea98c62e23d958de6c663e763cb493349ad6366d48840f5836fad8`.
The corrected host selection also independently rehashed all 2,851 files,
110,206,738 bytes, index SHA-256
`63bf622725db993b92069c3258c93ea94bc493f5521ceedfebb31a7872d25dbd`.
Its final script gate passed 469 tests; the owned child completed zero with
known cleanup. These sealed results grant no follow-on execution authority.

Current userdata availability is 1,223,741,440 bytes, only 15,781,888 bytes
above the unchanged controller floor. The earlier pair update was followed by
a 74,911,744-byte decrease; the evidence does not attribute that decrease to a
specific artifact or guarantee reclamation. The corrected incoming pair totals
76,755,379 bytes. Android's installer writes a separate stage before commit,
and old resource cleanup occurs later; update-in-place is not a zero-headroom
guarantee. Reserving even the incoming pair above the existing floor would
require 1,284,714,931 bytes before update, 60,973,491 bytes above this observation;
that lower-bound calculation still does not calibrate all installer overhead.
The final reviewed controller guard validates both incoming APK files' bounded
sizes and pinned hashes before the first install, then deducts their actual
sizes from availability above the unchanged floor. Its exact-boundary positive,
one-byte-short refusal and invalid second-APK cases exercise the actual flow;
shortage or changed inputs stop before either update. This is a necessary
reserve, not a claim of sufficient installer overhead. The measured current
headroom does not meet it. No v2 retry was admitted or executed.

No retry capacity acceptance or installed-gate failure is claimed. Floors,
existing data, old failed roots and environment boundaries remain preserved.

The guard was integrated as `388d107`; final protocol/source revision is
`5e62e23d372e690deefb2654fb99fed50e6374e1`. The retained targeted mocked suite
passed 22 tests (owned child zero, known cleanup, 4,312 ms). The final broad
script gate passed 471 tests in 19.826 seconds; its owned child completed zero
with known cleanup in 20,375 ms. Output SHA-256:
`6f05935794dd49b7d4d560acf7fadb6b336df90e142af657b8b5fe01fbdf731b`.
No app source changed after the repaired Android build.

The final 1,394-source snapshot, 16,337,466 bytes, independently rehashed with
zero mismatches. All 1,445 final host selection files, 103,451,922 bytes, also
matched, index SHA-256
`f363993e4390a79e3712a267642e200afcd8485b1ed618248a224db5106a0461`.
The complete 37-input recovery archive preserves all admitted digests, including
the former live controller from its sealed source snapshot; archive index
SHA-256 `9dc7db2a357f15b103c9be8b3edf5685f0bf1f37796cd1a0d579c93437011090`.
Post-closure controller/document edits do not rewrite those historical inputs.

Source basis: [Android 15 staged writes](https://raw.githubusercontent.com/aosp-mirror/platform_frameworks_base/android-15.0.0_r1/services/core/java/com/android/server/pm/PackageInstallerSession.java)
and [post-install old-resource cleanup](https://raw.githubusercontent.com/aosp-mirror/platform_frameworks_base/android-15.0.0_r1/services/core/java/com/android/server/pm/InstallPackageHelper.java).

Android media removal, power loss, real-model capacity/runtime, reference-phone
behavior, A/#117/#119 and full milestone gates remain open. The next runnable task is a separately scoped read-only capacity settlement or an independently admitted larger isolated environment that preserves existing data. Neither current capacity recovery nor authority to create that environment is inferred.
