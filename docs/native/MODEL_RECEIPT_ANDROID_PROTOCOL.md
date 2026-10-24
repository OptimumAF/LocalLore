# Isolated Android receipt qualification protocol

Refs #9 (M05.05 prerequisite), #5 (M01.05 supporting). Implementation/qualification
packet only; this is not setup activation, a native rename fallback or a model
runtime result. The [core contract](MODEL_RECEIPT_CONTRACT.md) remains unchanged.

## Isolation and admission

Use only the existing explicit volume debug profile, package
`org.locallore.app.modelvolumeverify` and its test APK. The volume flag adds the
`src/modelVolume/java` debug source and debug manifest overlay; ordinary and
regular SDK profiles must exclude ReceiptAndroidFixture and ReceiptProofService
code and declaration. The sole launcher, permissions, SDK graph, native library
set, backup exclusions, default setup and canonical story storage stay unchanged.

ReceiptAndroidFixture derives paths only from Context and an unchanged
AndroidModelVolume selection on IO. Control parents use the trusted resolved
no-backup anchor; data parents use the selected Context app-files anchor,
beside the existing candidate root. Cases are closed constants ACCEPT,
CANCEL_BEFORE, CANCEL_AFTER, PARTIAL, FOREIGN, FOREIGN_CONTROL, GUARD and
PROCESS, with fixed `receipt-android-<lowercase-hyphen-case>-v2` children. The
consumed first qualification used v1 children; preserve those roots and their
evidence. A corrected trial uses only fresh v2 children, never clearing or
adopting v1.
FOREIGN_CONTROL may reference the FOREIGN data root solely to prove refusal.
Initial case roots must be absent; no previously failed or benchmark root can
be adopted or cleared to prepare the test. Only intentional PROCESS recovery
reopens data created by its owned child in that run. Preserve accepted/unknown
bytes; explicit discard targets matched unaccepted fixture files only.

Identity: `synthetic-receipt-android-v1`, 63 bytes, SHA256
`648c91a9de82e613189b3920a2098f5d803eb6e244f39b2b631cce24b7be8de0`,
default 268,435,456-byte import reserve. Bytes are the existing original picker
fixture, not weights or story content. Actual volume guards retain exactly-one
selection, sticky identity refusal and all capacity floors: 2,147,483,648 external
bytes, 1,140,850,688 userdata bytes; missing bytes are added to the external
floor. Controlled guard revocation calls actual volume admission then returns a
fixed refusal. It is synthetic revocation, not physical media removal evidence.

## Process and lifecycle boundary

ReceiptProofService is fully qualified in the volume-only debug manifest,
exported false, isolatedProcess false, process `:receiptproof`, with no filters
or permission. Guard the exact build/package, own UID and exact process before
fixture work or self-kill. No URI, path, fixture selection, intent extras or
external source can select an operation. Binder token:
`org.locallore.app.receiptproof.v1`. Same-UID, synchronous callers only, with a
nonnull reply and no trailing payload. Reject FLAG_ONEWAY. Do not require the
entire received flags word to be zero: Android may add framework bookkeeping
flags to synchronous calls. The first v1 trial demonstrated a remote START
refusal but did not identify the failing remote check. Official Android 15
[BinderProxy](https://android.googlesource.com/platform/frameworks/base/+/android-15.0.0_r1/core/java/android/os/BinderProxy.java)
adds FLAG_COLLECT_NOTED_APP_OPS under its collection policy, and
[Binder](https://android.googlesource.com/platform/frameworks/base/+/android-15.0.0_r1/core/java/android/os/Binder.java)
forwards received flags to onTransact. Replacing the zero-word check corrects
that independently demonstrated compatibility defect; no actual received bit
value or sole cause is inferred from the old exception.

- START (1): fixed acknowledgment 1, then one IO worker imports PROCESS. At
  DATA_FORCED it holds the actual store/OS lock and waits at most 30 seconds;
  timeout fails and preserves pending data, without acceptance.
- SNAPSHOT (2): after writeNoException, state int IDLE=0/RUNNING=1/
  DATA_FORCED=2/FAILED=3, PID int, UID int, start elapsed realtime long.
- HALT (3): validate held DATA_FORCED/identity, atomically arm self-halt and
  return acknowledgment 1 only while at least ten seconds remain before the
  hold deadline. Parent binding release/death observation is bounded to five
  seconds. This acknowledgment does not prove death.

The parent links a death recipient to that exact binder, proves distinct PID
and same UID, validates actual pending files, and proves all three competing
operations BUSY. It then arms HALT, releases its exact AUTO_CREATE binding,
and the guarded child onUnbind self-hardkills while still holding the lock.
Guarded onDestroy provides fixture-only failure cleanup. Do not release/join
the worker before the designed death or leave a binding that permits restart.
Observe binder death and actual parent lock reacquisition; a bounded BUSY-only
wait may account for delayed OS release while verifying preserved bytes. Resume
without a source, then rehash accepted data. This proves only that owned process
death/recovery path, not a general SDK teardown or power-loss guarantee.

Android documents that AUTO_CREATE keeps a binding eligible for creation and
that disconnection does not remove it. The protocol removes that connection
before self-kill. [Bound services](https://developer.android.com/develop/background-work/services/bound-services),
[ServiceConnection](https://developer.android.com/reference/android/content/ServiceConnection#onServiceDisconnected(android.content.ComponentName)),
[service manifest](https://developer.android.com/guide/topics/manifest/service-element).

## Instrumentation and private evidence

Only `ReceiptVolumeQualificationTest` is selected, with exactly four methods:
acceptsAndReopensReceipt, cancelsAcrossAcceptanceBoundary,
refusesForeignAndUncommittedData and recoversAfterOwnedProcessDeath. They assert
real file/cancellation/ownership outcomes before recording booleans. No SDK,
native publication, engine or workspace call. A diagnostic refusal is not an
accepted pass: qualification requires four actual passing tests and all proofs.

Fresh internal `no_backup/receipt-android-proof-v2` contains exactly eight files:
accept-v1.json/accept-ready-v1.txt, cancellation-v1.json/
cancellation-ready-v1.txt, refusal-v1.json/refusal-ready-v1.txt and
process-v1.json/process-ready-v1.txt. Each JSON is forced CREATE_NEW, ASCII,
1..4096 bytes, followed by its forced **empty** ready file. No raw artifact is
uploaded. Closed JSON keys:

`version`=1, `phase`=ACCEPT/CANCELLATION/REFUSAL/PROCESS, `pid`, `start`, `uid`,
`process`, `fixture_bytes`=63, `fixture_sha256`, `candidate_root_absent`=true,
`publication_native_invoked`=false, `sdk_invoked`=false,
`external_free_before`, `external_free_after`, `userdata_free_before`,
`userdata_free_after`, `checks`. PROCESS additionally records `child_pid`,
`child_start`, `child_uid`. All four parent identities must agree; the child is
distinct and same-UID. Reading proof after instrumentation is not a claim that
its recorded PID remains alive. Reject unknown keys, duplicate JSON keys,
nonfinite numbers, wrong types/identity/phase/hash, missing or extra entries.

The exact checks sets are frozen in the instrumentation and controller parser:
accept/reopen/preservation; before/after acceptance cancellation with one source
close; partial/unknown/foreign/discard and synthetic guard refusal; actual child
identity, pending bytes, OS contention, halt arming, binding release, death,
reacquisition and source-free verified acceptance. Every check must be true.

The device controller starts disabled, binds exact source/artifact hashes and a
fresh admission, owns/bounds all client processes, and permits only the planned
app/test pair update. Preserve prior APK hashes/UIDs outside that pair and all
UIDs including the pair. No explicit controller force-stop, clear, uninstall, old-root cleanup,
emulator/storage creation, model copy or SDK call. Require final own app/test/
service/provider absence. Known unrelated chooser providers may only be
classified against exact installed UID evidence, never acted on; unknown state
refuses. Report actual counts rather than claiming passive absence by assumption.
Ordinary instrumentation/framework setup may restart its target; controller
command counts are not evidence that Android made no lifecycle changes.
Existing A/#117/#119, capacity, physical-phone/ARM64/16 KiB, cache privacy and
model-quality gates remain independent.
