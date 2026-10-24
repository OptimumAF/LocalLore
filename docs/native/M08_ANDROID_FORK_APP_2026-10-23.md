# Android app fork caller: implementation freeze, 2026-10-23

Refs #12 (M08.01/.02 partial), #30 (D08.04 partial).

Status: implemented source packet awaiting compilation, execution and independent review. No full M08/D08 acceptance. This is app wiring for the existing shared fork port, not an author-correction editor.

## Source and ownership

Branch `impl/d08-android-fork-app`, separate `source-android-fork-app` checkout, based on `e4b3759f525f273880084373c70844631eaa7ca5`. The base contains the existing native fork adapter, its original controller and callback corrections. Those source files and original 22 JVM cases are unchanged in this packet. Claims: [M08 scope](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6375903726), [D08 scope](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6375904000); narrow ShellState/LocalLoreScreen additions [M08](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6375930602), [D08](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6375930828).

Existing files changed only in the approved Kotlin caller boundary: `DurableGateway.kt`, `NativeWorkspace.kt`, `ShellState.kt`, `ShellViewModel.kt`, `MainActivity.kt`, `ui/LocalLoreScreen.kt`. New production files: `ForkRecoveryStore.kt`, `ui/BranchForkPanel.kt`. No Rust/Core/Store/Host/schema/JNI/runtime/model-backend, existing NativeFork/BranchForkController, archive or deletion implementation changes.

## App path

MainActivity constructs one NativeWorkspaceTransport and shares that exact owner's allocator between DurableGateway and NativeForkGateway. `forkHandle()` borrows the original IO-only allocation/teardown path; it does not open another workspace. Existing archive/deletion adapters retain their preexisting architecture.

The readonly DurableGateway `forkContext(selected, expectedHead, epoch)` returns a session/scope/head binding only after successful coherent player snapshot decoding, with no pending turn and an exact live selected scope/head. Any prepare/recovery/release/snapshot attempt invalidates that binding until a successful new coherent snapshot. This is admission metadata: Rust remains the only fork/permission/history authority.

One BranchForkController belongs to each ViewModel lifetime. Opening the panel captures the original parent/head and a fixed child identity. Reviewing another requested completed boundary retains that child identity. Creation requires the exact rendered input reference and explicit consent; Rust validates completion. No automatic child selection, downstream replay, correction, knowledge, ability or inference grant is added. Explicit resume calls the existing `resumeSaved` path using the confirmed child outcome. The parent history remains unchanged.

Fork review/work disables turn input, new-story/library/timeline switching, archive, deletion, record, diagnostics and mode controls. The VM also enforces admission for retained callbacks. Session/lens/background changes retire the old presentation before cancellation; fork cleanup continues to block other work until drained. Clearing the ViewModel disposes/cancels the fork controller before closing the shared transport. MainActivity.onStop hides/cancels fork work, including rotation, without deleting accepted data or its recovery hint.

## Exact recovery hint

The fixed app-private `noBackupFilesDir/fork-recovery-v1/pending.json` contains only version 1 and the original four fork fields. It does not contain a native operation ID/session, story text, model output or a second canonical history. The strict existing ForkNativeWire codec admits at most 4096 bytes. Startup reads the hint but does not register/execute a fork. Reopening it is lookup-only, even if the original child is absent. The user must explicitly forget a hint before preparing a different identity.

AtomicForkRecoveryStore serializes its fixed AtomicFile operations under one process-wide gate, compares the previously observed fixed record/artifacts before replacing/clearing, performs synchronous file and directory sync plus exact readback before native dispatch, and refuses a conflicting existing identity. Explicit retry keeps the exact input. A malformed/oversized/orphan record is reported unavailable and cannot be silently replaced; a separately consented clear can remove the unchanged invalid hint. Failures after a write may have occurred remain uncertain; they do not assert rollback/absence. This is a bounded local hint, not a cross-process lock, OS security boundary or hardware power-loss guarantee. Android's AtomicFile documentation requires caller-provided threading protection; the store provides that protection for this app process. [Android AtomicFile](https://developer.android.com/reference/android/util/AtomicFile), [Os.fsync](https://developer.android.com/reference/android/system/Os#fsync(java.io.FileDescriptor)).

## Frozen checks and execution status

All following test sources are new and currently UNRUN/UNCOMPILED for this packet:

| Suite | Source cases | Boundary |
| --- | ---: | --- |
| BranchForkShellTest | 13 | Actual VM plus actual BranchForkController; typed fake workspace/native/recovery ports; save-before-dispatch, admission, exact identity/consent, restored lookup-only, failed persistence, late registration/background cleanup, explicit resume, dispose order, pending turn/lens fences, reentrant save and lost acknowledgment |
| ForkAppWiringInstrumentedTest | 2 | Actual production NativeWorkspaceTransport/DurableGateway/NativeForkGateway/JNI on unique synthetic noBackup roots; unchanged parent suffix, explicit child continuation, reopened identity and missing lookup nonmutation |
| ForkRecoveryStoreInstrumentedTest | 4 | Actual Android AtomicFile; exact reopen, stale writer/refused replacement, malformed/future/duplicate/oversized data, orphan new artifact and unavailable fixed directory |
| BranchForkPanelTest | 3 | State-only Compose; exact rendered identity and consent, lookup-only/forget separation, pending cancellation and explicit confirmed resume |

The 13 JVM sources are not canon/JNI/filesystem qualification. The nine instrumented/component cases require authorized Android execution to establish their assertions; building a test APK alone cannot do that. No device/emulator/ADB was used. No application-owned native or Compose UI journey was executed by this packet. No model/worker/asset was loaded or downloaded. Protected chat resources were untouched.

Actual static checks at initial freeze: `git diff --check` passes; no diff to existing NativeFork/BranchForkController or prior fork tests. No Cargo, Node, Gradle, JVM, APK, lint or connected task was run because the coordinator owns the current heavy build slot. There are no fabricated pass counts or screenshots.

## Next runnable qualification

After coordinator resource GO, use the pinned JDK17/SDK36/NDK29, existing offline Gradle cache, a separate task-local output redirect and D-drive TEMP. Preserve unchanged initial failures before correction. Run ordinary preBuild (do not exclude buildRustAndroid), the original 22 plus new 13 focused JVM cases, then full JVM, ordinary both-ABI JNI/APK/testAPK/lint and package audit as allocated. Build/compilation and actual JNI/device execution must remain separately attributed. Keep local outputs/logs outside tracked source. Independent review must assess actual VM/gateway/AtomicFile/callback/UI wiring before integration. Android device/rotation/process-death/Compose/JNI journey gates and full milestone acceptance remain open.


## Source-only explicit-resume correction

Initial source freeze `0e5f469383da4e9c4f3036ab6b79eaa6e8924ecc` is retained. Subsequent source review found that `resumeFork` silently returned when a confirmed recovered child's story was absent from the UI's older library, even though another owner could have restored it before native lookup. Claim addenda: [M08](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6376241829), [D08](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6376242080).

NEW thirteenth VM schedule was frozen BEFORE the production correction at `1adf7b91d760bb7e25200c726f94e57d1899cfc3` (`test/d08-fork-app-resume-before`). Its typed workspace port initially exposes another story only; readonly lookup finds the exact restored identity; only an explicit snapshot reveals the current root metadata. Copied/stale outcome callbacks must not refresh or select. The original twelve test bodies are unchanged. This vector is UNRUN, so the before-fix checkpoint is not claimed as a measured RED.

Narrow source fix `fb35db58769c6b6d5af759dcf62eb6dce8c4949f` removes the silent stale-library return. Only an explicit exact-outcome resume enters the existing saved operation, refreshes the actual workspace snapshot, requires current root metadata and resumes the exact confirmed child through existing `resumeSaved`. Missing metadata produces the existing sanitized visible recovery/error path. Lookup alone still cannot create/select; no ID is rerolled. HostOpen passively refreshing identical/extended history is coordinator-owned and unchanged in this packet.

All 22 new source cases (13 JVM, nine instrumented/component) remain UNRUN/UNCOMPILED at this documentation checkpoint. Coordinator requested qualification against its later integrated Shared M07 baseline to avoid a redundant old-core ABI rebuild; no heavy command has been started here. `git diff --check` passes after both source freezes. Independent review remains pending.
