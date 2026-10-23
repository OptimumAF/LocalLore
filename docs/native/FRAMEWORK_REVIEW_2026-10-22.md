# Independent framework interruption fixture review

Delegated scope: M04.04 and bounded M04.05, under #8 comment 6356188382.
Baseline: `80c7196`; branch `review/m04-framework-stop` in the separate
`LocalLore-app-device-review` worktree. The coordinator owns the test fixture,
integration, ticket updates and device execution. This reviewer owns only this
report. Host-v1, schema 1 and production sources remain frozen for this packet.

## Pre-create injection boundary

The proposed fixture preloads the ordinary `ShellViewModel` through
`ViewModelProvider` in the API-29 `Application.ActivityLifecycleCallbacks`
pre-create callback. `MainActivity` then finds that same ViewModel through its
normal provider lookup. This changes test construction without a production
factory hook or second gameplay authority. The supplied transport must still
delegate to the actual `NativeWorkspaceTransport` and SQLite-backed Host.

Read-only inspection of the cached, pinned AndroidX Activity 1.10.1
`ComponentActivity` bytecode confirms:

- `getViewModelStore` checks that the Activity has an attached Application and
  then calls `ensureViewModelStore`.
- `ensureViewModelStore` first restores a store from the last nonconfiguration
  instance, otherwise allocates one.
- Default creation extras add owner/Application references; this custom factory
  does not request a `SavedStateHandle` before saved-state restoration.

The inspected cached `classes.jar` SHA-256 was
`d19ee4f4c616611d74d4908531caa6f81bd97cb0a2d8a96fc08cfad3b1f50076`.

Local Android SDK 34 `Activity.java` separately shows Application assignment
during `attach`, pre-create dispatch before `onCreate`, and pre-stop dispatch
before `onStop`. This supports the construction order; it is not Android 35
device execution evidence. Transport/model construction should occur inside
`Factory.create`, so configuration recreation returning the retained ViewModel
does not allocate an unused native owner.

## Lifecycle and race acceptance

`MainActivity.onStop` calls `model.cancel`. For a preparing durable response,
the ViewModel advances its generation, marks the captured gateway operation
cancelled, cancels its response job and starts authoritative cancellation
reconciliation. Opening or switching saved stories is intentionally not treated
as a cancellable generation. `onCleared` permanently disposes the gateway and
uses the transport's independent IO cleanup scope.

The fixture must use actual `ActivityScenario` transitions. Manually calling an
Activity callback does not establish the framework state transition and has
already proved unsuitable for ActivityScenario recreation in the preceding
packet.

The following distinctions matter to avoid false passes:

| Observation | What it can establish |
|---|---|
| Exact original key reports `running` | Actual Rust preparation started; local UI `busy` alone is insufficient. |
| Intended pre-stop callback observes native call still in flight | Framework stop began while JNI had not returned. This must be recorded once for that Activity/operation. |
| Reply delivery is gated after actual JNI returns | A controlled late transport reply; it must not be described as extending native execution. |
| Canonical reopen has revision 0, potion and no receipt | No accepted effect survived; an uncommitted draft is a separate, admitted state. |
| Fresh turn commits before old reply is released | The replacement path is runnable and the old response cannot be used as its result. |
| Old reply drains and UI/save remain identical | That measured late response did not replace accepted state. It does not prove which particular cancellation/generation guard discarded it. |
| All native owner slots recover | Async native owner release, separately from merely retaining the database file. |

A native-return flag must be recorded inside an uncancelled IO boundary. If it
is set only after a cancellable `withContext` returns to Main, cancellation may
skip the assignment and falsely report that JNI is still running. A failed
finite overlap observation must fail as insufficient overlap, not be converted
into proof of a blocked Main thread or silently retried as if the attempt passed.

Real close can cancel the on-stop reconciliation coroutine before it completes.
The native lease must still close and preserve zero accepted receipts; retaining
an unfinished draft is allowed. Cleanup should release reply gates, drain owned
workers, close scenarios and native transports, unregister lifecycle callbacks
and remove only the exact synthetic directory after native ownership is gone.

## Review and verification scope

This review has so far inspected actual production sources, local SDK lifecycle
source and the pinned ComponentActivity bytecode using `javap -p -c`. It has run
no ADB, emulator, phone, network, model, Gradle or JNI action. Fixture source
findings and coordinator execution evidence are recorded separately below when
available; no device pass is inferred from this design review.

## Concrete fixture source review

The reviewed `FrameworkInterruptionTest.kt` SHA-256 was
`0ac766ba6e900ae80fa842f71c0d655a83906cd75af529ffc8fb24696bd71838`.
It uses an outer fixture rule around the
Compose Activity rule. Lifecycle callback registration therefore precedes
Activity launch, and ordinary scenario teardown precedes outer cleanup. New
native owners are constructed only by the custom factory; recreation verifies
that every seen ViewModel is the same retained instance and that exactly one
owner exists.

The first actual prepare runs under `NonCancellable + Dispatchers.IO`, records
its return and completes `nativeReply` there, then holds reply delivery. This
addresses the false in-flight flag risk. Its explicit handling of cancellation
on the return dispatch deliberately supplies the captured obsolete reply to the
cancelled controller. After gate release, a Main barrier and exact ShellState
comparison check that it did not replace the fresh accepted story. The calls
list excludes any commit of the old turn key. Reopen compares accepted revision,
receipt-derived messages and player inventory; the new-story case separately
reopens the original cancelled story and checks revision 0 and no messages.

No concrete production defect was found in this source review. Two fixture
qualifications were returned to the coordinator:

1. `stoppedBeforeNativeReturn` requires the captured native reply to be
   `cancelled`. Even if pre-stop observes actual native work, JNI can finish
   `ready` before the subsequently dispatched cancel reaches the Host. A ready
   proposal followed by persisted cancellation is an admitted no-commit race.
   A failure of this narrow reply assertion alone does not prove a production
   cancellation defect. If retained, the assertion qualifies the narrower
   native-cancellation-winning cohort.
2. Four available native-owner slots prove registry admission capacity recovered.
   `WorkspaceRegistry.close` removes an entry before waiting for retained
   lease/control work. The gate drains its first prepare, but capacity alone
   cannot establish completion of every other in-flight exchange or the
   asynchronous close worker. The normal stop/recreate cases additionally wait
   for authoritative reconciliation; the destruction case tests reopen and
   retained callbacks. Report these exact observations rather than asserting
   that every native resource was measured as drained. A wrapper active-exchange
   counter would add direct evidence for other outstanding calls if needed.

The fixture's destruction case correctly permits the native reply to race
disposal: its required outcome is zero canonical receipts after reopen, no new
calls through retained callbacks, and recovered owner capacity. The cleanup
releases gates, closes owners, waits for the gated return and capacity, then
deletes only the exact create-new synthetic roots. Primary and cleanup failures
are preserved together using `MultipleFailureException`.

This reviewer did not run or compile the fixture. Actual lifecycle overlap,
device outcomes and the final source identity remain the coordinator's evidence
to record.

## Revised interleavings at dd11ab2

The coordinator reported that the initial emulator-A run at `68c35cf` produced
one passing active-native recreation case and two explicit insufficient-overlap
failures: ordinary stop and destruction reached pre-stop after the 200 ms fake
had returned. This reviewer did not execute or independently inspect that device
run. Those failures establish a fixture timing limit, not a production defect.
The coordinator recorded the refinement under #8 comment 6356274263.

Read-only review of `dd11ab2f918217e574595cb57b02fe84c4b07bc7` inspected fixture
SHA-256 `646be544705311870aa12f4812e55767e021ea537fcf77326e6dad44041ef840`:

- Recreation retains its strict native-active pre-stop requirement. Failure to
  observe that finite overlap remains insufficient evidence rather than a
  cancellation pass.
- Ordinary stop and destruction now wait for an actual Rust `ready` reply held
  outside the controller, require no commit and require native-inactive
  pre-stop. These explicitly test the completed-generation/uncommitted-delivery
  window without claiming to extend native execution.
- Stop/recreation permit the native reply to be `ready` or `cancelled`, then
  separately require cancellation of the original persistent turn key and zero
  accepted canon. The original native-return race no longer produces a false
  production failure solely from a `ready` reply.
- Destruction still allows on-cleared disposal to interrupt cancellation
  reconciliation. It requires zero canonical receipts on reopen rather than
  pretending that every close persisted a cancelled draft.
- An atomic exchange count now increments before every wrapped call and
  decrements in `finally`, including exceptional/cancelled returns. Destruction
  and fixture cleanup require zero after releasing the held reply. Direct
  native status probes are individually awaited. This adds drainage evidence
  alongside separate registry-capacity recovery.

No further concrete defect was found in the revised source. Native slot
recovery remains an admission-capacity observation, and it is now accompanied
by completion of owned wrapped exchanges. The test still does not expose or
measure arbitrary internal allocator state. This reviewer made no Kotlin,
production, device, build or network changes. Final device outcomes must be
read from the coordinator's verification artifact.

## Unexplained reference-queue crash investigation

The coordinator reported that one emulator-A invocation at unchanged `dd11ab2`
passed the three new framework cases, then the first subsequent shell case
terminated with `TimeoutException` from `FinalizerWatchdogDaemon`, naming
`HardwareRenderer$DestroyContextRunnable`. The other twelve selected cases were
not reached. The same APK completed all sixteen selected cases on emulator B.
These are coordinator-reported outcomes, not independent device execution by
this reviewer. The aborted A invocation remains a failed attempt; B's pass does
not erase it or explain its cause.

Claim #8 comment 6356342586 authorized read-only public-source research using
only the public exception/class names, with no diagnostic upload. Official
Android API-35 source shows two relevant mechanisms:

- `HardwareRenderer` registers a Cleaner action when constructing its native
  proxy. `DestroyContextRunnable.run` invokes `nDeleteProxy`. Rendering instances
  share a render thread; a stalled surface consumer can block that thread. These
  details locate a framework cleanup path, but do not establish which operation
  stalled this particular run. See the [API-35 HardwareRenderer source](https://android.googlesource.com/platform/prebuilts/fullsdk/sources/+/refs/heads/androidx-swiperefreshlayout-release/android-35/android/graphics/HardwareRenderer.java),
  inspected blob `940cd93c53f2b37d8903c44fd5647a12ccfe0e21`.
- The watchdog monitors reference-queue progress and constructs the reported
  exception after repeated observed timeouts. The exception names the current
  cleanup target; it is not a LocalLore leak detector or a causal attribution to
  the most recent test. See the [API-35 Daemons source](https://android.googlesource.com/platform/prebuilts/fullsdk/sources/+/refs/heads/androidx-constraintlayout-release/android-35/java/lang/Daemons.java),
  inspected blob `36c1c7461946acae5c28b842e6b40f08ed2749a7`.

These official source snapshots explain the public mechanism; they have not
been matched to every binary or configuration detail of the affected emulator.
No exact matching official issue or verified upstream fix was found in the
public searches performed. This is therefore not classified as a known fixed
Android bug.

An additional read-only `rg` audit found no direct HardwareRenderer, RenderNode,
SurfaceView, TextureView, SurfaceTexture, EGL or GLES allocation, explicit
`System.gc`/`runFinalization`, or uncaught-handler suppression in Android app or
native-crate sources. The fixture retains ViewModels and an Application-backed
context wrapper, and delegates Activity/Compose rendering teardown to their
ordinary framework/rule lifecycle. No concrete fixture graphics-owner leak was
identified. This source audit cannot exclude an indirect framework/library,
driver, emulator-scheduling or application contribution.

The justified next check is a separately recorded serial run of the unchanged
APK after the previous live run is terminal, retaining both attempts. A later
pass would provide additional execution evidence while leaving this cause
unexplained. No timeout suppression, renderer workaround, dependency change or
emulator reset follows from the exception alone. Rust owner-slot and transport
drainage assertions do not qualify graphics cleanup reliability.
