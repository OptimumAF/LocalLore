# Independent Android fork caller source review (2026-10-23)

Refs #12 M08.01/.02 and #30 D08.04, partial caller prerequisite. Reviewer:
`resource_metrics_review`; separate `review/m08-android-fork` /
`source-android-fork-review`. Frozen source
`e38b06f59077dc85ec533932e75760e75d3c2b03`, behavior `2fcbead`, base `5e44ea9`.
Claims: #12 comment6375306963 / #30 comment6375307235. Existing production and
author tests remain unchanged. Own additions are this report and NEW
`BranchForkReviewTest.kt` only.

## Finding: recovery-save callback can cross the confirmation origin

**Fix required before application wiring. Source finding; no measured RED yet.**
`BranchForkController.kt` checks confirmation context/reference/consent before
calling the injected synchronous `saveRecovery` (lines103–109), but does not
recheck generation/context/disposal afterward:

1. The callback calls `contextChanged(replacement)` and throws an ordinary or
   CancellationException. The catch at110–112 assigns `before.copy(notice=...)`,
   restoring the OLD context/input/visible state over the new selected context.
2. The callback changes context and returns normally. Lines114–119 still assign
   recovery and start work, then register with the captured OLD context. The first
   `current(ticket)` check is after registration (line121). The native child worker
   is not then dispatched, but stale registration and uncertainty can still affect
   the new context. This does not prove an unauthorized canonical fork occurred.
3. The callback calls `dispose()` and returns normally. Confirmation still calls
   work after disposal, mutates the disposed presentation and can enter the fake
   gateway. The real gateway's closed check is an additional native defense; it
   does not make the controller's disposed-state mutation correct.
4. The same callback class exists in `forgetRecovery`: `saveRecovery(null)` changes
   context then throws; catch at184–185 labels the new context with the old
   clear-failure notice. It does not restore old context in this path.

The published injection contract requires synchronous durable save-or-throw; it
does not require a nonreentrant callback. The existing onResolved path explicitly
handles synchronous context changes. These new vectors apply the same origin
fence to the other injected callback, without requiring actual Activity behavior
or inventing asynchronous persistence.

Recommended correction: capture the original generation/context/input and fence
both success/failure continuations around recovery-save/clear callbacks before
presentation writes or native dispatch. Never restore a stale `before` state or
restart a disposed owner. A successfully saved old identity remains honest
lookup-only recovery after an origin change; cancellation is not proof of absence.
The coordinator/author owns the precise persistence ordering and production fix.

## Frozen independent regression source

`bf1461cade5001509e3a55cb8c7f20e857daffc9` adds the first three NEW controller
vectors; `84d785cb0cde9689dd2dba54d692566cfe575325` adds the fourth. They use the
actual BranchForkController and typed fake gateway, with no JSON/JNI/Store/device.
The ordinary and cancellation exception variants are both predeclared. Tests
require no stale source labels, no old native registration, no fork worker, and
an unchanged empty disposed presentation. Existing fifteen author oracles were
not edited. New test file SHA-256:
`26ee0f80a236ca3d7862462e86a6ced6a3432f1f5f941eef64b01715c023298f`.

All four tests are **uncompiled and unexecuted**. The coordinator prohibited
Cargo/Gradle while desktop fork verification owns the heavy slot. Reproduce the
unchanged tests against e38 BEFORE a fix, retain any actual setup/semantic failure,
then run the identical vectors and original15 on the separately frozen correction.
The future filtered command is:

```text
:app:testDebugUnitTest --tests org.locallore.app.BranchForkReviewTest --offline --no-daemon --max-workers 1 -Pandroid.builder.sdkDownload=false
```

Use the established author task-local build-output init script/JBR/SDK/NDK and
coordinator resource scheduling. This line is a planned Gradle task invocation,
not reviewer execution evidence or a complete standalone environment setup.

## Other reviewed boundaries

No additional concrete native canonical-authority issue was found in this source
pass. This is not a test pass or a blanket acceptance:

- `branch_fork.rs` accepts bounded exact typed fields and explicit native consent,
  one immutable pending operation per actual existing workspace lease, globally
  nonreused positive operation IDs, four owner slots and 4096-byte controls/replies.
  Native operation storage is not a second Store. Host/Store remain the sole
  completed-boundary/new-creation expected-head/fixed-child retry authority.
- `fork_with_owner` takes existing mutation/control gates and rechecks the actual
  Arc lease identity. Registry/phase locks are not held during Host work. Close
  marks the lease closed, removes/cancels the operation before drain; concurrent
  registration either sees closed or is retired. Status/cancel need no Host lock.
  Running cancellation is cooperative; committed result wins late cancellation.
- Lookup invokes the existing branches catalog only, checks parent/fork/child/
  retired identity and returns current head. It creates/resumes no child or live
  session. Missing remains a catalog snapshot, not rollback evidence. No inspection,
  observer or author grant is added by native fork/recovery APIs.
- NativeForkGateway uses the existing transport-supplied owner handle, bounds
  control JSON and retains operation/input/owner binding. Early/closed registration
  acknowledgements are cancelled; root still owns the single transport close.
- Kotlin status/lookup decoding checks exact keys, closed versions/labels,
  primitive number/boolean types and fixed input/outcome identity. UTF-8 byte bounds
  and JSONObject canonical round-trip code aim to reject duplicate/lenient JSON;
  actual Android JSONObject and JNI behavior is still an unexecuted gate here.
- Existing controller reference-consent, save-before-dispatch, restored lookup-only,
  explicit same-context retry, bounded polling, accepted-result-over-cancel and
  onResolved context fencing are preserved. The injected recovery callback gap
  above prevents acceptance of the complete controller origin boundary.

Reviewed source hashes:

| File | SHA-256 |
| --- | --- |
| branch_fork.rs | bf6c7358c929aa01e04fe5ada8311b477a9f4bc29ae0d4f135f06ff5832f8176 |
| NativeFork.kt | 5f3677975ba77e7e804b61e6b9f559e8ff383ab2f62d62d82780c5942aa60db0 |
| BranchForkController.kt | e320100abd65ac25efde2463d730f0c8f2f80383efb47d5462b9ea7a1040e8b1 |

## Evidence attribution and remaining gate

The author report at e38 records Rust integration9 + module2 PASS, strict Rust
alltarget/allfeature/fmt PASS, ordinary JNI release compilation for x86_64 and
arm64-v8a, and actual typed-fake-gateway controller JVM15 PASS. It preserves initial
Rust E0063/Kotlin helper-shadowing compile failures and lifecycle/lookupOnly REDs.
Those results were not rerun or independently measured by this reviewer. Author
Rust tests exercise actual Registry/Host/Store, JVM tests do not; ordinary JNI
compilation is not JNI execution. Four JSONObject wire and two JNI instrumented
cases remain source-only. No broad JVM/APK/lint/device/ARM64 runtime or UI execution
is inferred from that evidence.

Reviewer execution was limited to Git/source/issue reads, source hash checks,
new regression/report authoring and `git diff --check`. No Cargo/Gradle/JVM/native
app/device/ADB/CUA/desktop/model/settings/dependency/PR/merge action ran. Claims are
released to the coordinator with this source-only handoff. Status remains in_review
with the concrete callback finding open, not done/full M08/D08 acceptance.

Next runnable task: coordinator/author reproduces the four frozen vectors before
fixing the recovery callback fences, then integrates the single NativeWorkspace
handle allocator, real durable bounded recovery store and Activity/ViewModel/UI
context/admission/consent wiring. Actual wire/JNI/device qualification remains a
separate authorized gate; this caller packet is not yet an exposed Android feature.
