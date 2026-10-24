# Android schema5 admission: frozen protocol oracles

Date: 2026-10-23. Partial M08.06 / M04.06 prerequisite, source-only, not Android
runtime qualification or milestone acceptance.

Branch `review/m08-android-schema5`, worktree `source-android-schema5-review`,
base `9eb73da7a8facbbb493293267266526bd0bb646f`. Exact amended claims before
writes: [#12 6378058332](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6378058332)
and [#8 6378058593](https://github.com/OptimumAF/LocalLore/issues/8#issuecomment-6378058593).
Only NEW `apps/android/app/src/androidTest/java/org/locallore/app/M08Schema5AdmissionTest.kt`
and this NEW document are owned. The initially proposed `src/test` path was
released before creation; no file was created there.

## Actual source seam and narrow coordinator change

In the base, `DurableGateway.kt:88` admits only
`database_schema_version == 4` when reading workspace metadata. Its snapshot
path repeats `databaseSchema == 4` at line 158. The shared Store has physical
schema5, independently of Host-v1's wire protocol. Therefore a valid current
schema5 workspace is refused before resume. Updating only one fence is
insufficient: initialization and later snapshot refresh must both work.

The minimal proposed coordinator-owned production correction is those two
physical checks from exact4 to exact5. Preserve the envelope version1 check at
line 56 and workspace protocol1 check at line 87. Preserve all revision, scope,
observer, timeline, pending-operation and cancellation checks. This does not add
Domain2 UI support or expose author editing; existing legacy consumer closure
remains independently required. It is not an archive format bump or an Android
implementation of persistence.

No existing production or tests were edited here. Current #9/#8 claims were read
before this allocation. The coordinator must reconcile shared Gateway ownership
with active external inference/cancellation/transport/UI tracks before changing
either production line. This reviewer did not read or operate their protected
checkout, processes, devices, native handles or model resources.

## Frozen actual Gateway protocol tests

Source commit `5909571adcc2c0b24be660bffe6295b4aef08ab0`; test file SHA256
`7c5e9bf45119b0146728b68aec2d2e6d9adbcdaF74a9b9bbc02787121c653837`
(hexadecimal case is insignificant).

The five new methods invoke the same existing `DurableGateway.initialize`,
`snapshot`, `respond` and `recoverSaved` paths used by the app. The bounded fake
`WorkspaceTransport` supplies synthetic protocol replies and records commands.
It performs no domain validation, persistence, native loading or inference.

| Frozen method | Required behavior |
| --- | --- |
| schemaFiveKeepsProtocolOneAcrossInitializeAndRefresh | Physical5 and protocol1 survive actual workspace/resume/open/player snapshot/catalog/capability decoding; coherent selected story, revision0, inventory and unavailable provider are preserved; no gameplay writes. |
| emptySchemaFiveLibraryNeverBootstrapsDuringAdmission | Empty5 library publishes an empty protocol1 snapshot with no resume, create or gameplay. |
| futureSchemaSixRefusesBeforeResumeAndGameplay | Future6 fails at workspace admission; only workspace is exchanged. |
| incompatibleEnvelopeOrWorkspaceProtocolRefusesBeforeResume | Envelope2 and workspace protocol2 independently fail before resume; physical5 does not broaden protocol acceptance. |
| incompatibleRefreshAndStatusNeverReplaceThePendingRecoveryKey | A real Gateway-prepared operation survives failed future6 refresh and incompatible turn-status acknowledgement. Restoring valid metadata recovers the exact original request/turn/session/scope with one submit, one prepare and one commit; no regenerated key. |

The recovery fixture's initial head is zero; its synthetic committed response
advances the fixture to one and appears in the returned player transcript. This
is finite protocol setup for checking Gateway ownership, not SQLite atomicity
or an alternate engine. Protocol exceptions must refuse publication; tests do
not invent a new public error category for existing `check` failures. There is
no assertion that a fake reply demonstrates Rust validation or durable saving.

## Why instrumentation source, not a JVM success claim

The existing Gateway JSONObject protocol suite is
`src/androidTest/.../TimelineProtocolTest.kt`, explicitly using AndroidJUnit4.
Current local unit dependencies declare JUnit4.13.2 and coroutine-test1.10.2,
but no real org.json JVM implementation, Robolectric or replacement JSON
runtime was found in the scoped build/dependency-lock inspection. A JSONObject
import also exists in `src/test/.../RecordedDemoGateway.kt`; that import alone
does not supply executable Android JSON methods to a JVM Gateway test.

The coordinator directed use of the existing instrumentation allocation rather
than introducing a dependency, JSON stub, decoder copy, public test hook or
runtime discovery/download. Android framework JSONObject is required to execute
these tests. APK compilation alone does not execute that decoder or prove any
assertion. No instrumented device is currently allocated to this packet; the
protected and active Android tracks remain untouched.

Source configuration inspected: Java/Kotlin JVM target17, compileSdk36,
buildTools35.0.0, NDK29.0.14206865, coroutine1.10.2, AndroidX runner1.6.2 and
AndroidX test JUnit1.2.1. These are configured versions, not a newly measured
installed environment. Source work used Git2.33.0.windows.2 / PowerShell7.6.5.

## Existing fixture inventory for later coordinator reconciliation

These are exact source observations, not edits authorized to this reviewer:

- `TimelineProtocolTest.kt:47` defaults its synthetic live metadata to4;
  lines111/134 assert4. The current schema-named method at line106 and these
  current-owner assertions need deliberate modernization when its owner is free.
- Its incompatible-live list at line120 contains `(2, 3, 5)`; retain old-source
  refusal intent and use future6 in place of the now-current5. Its refresh
  mutation at line135 is also future5 and must become6, while its starting live
  metadata becomes5. Preserve every no-resume/no-gameplay/refusal assertion.
- `DurableDeletionRecoveryTest.kt:41/90` supplies/asserts synthetic **live**4;
  this is another coordinator-owned compatibility call site, not an old archive.
- `ArchivePlatformRoundTripTest.kt:342–344` carries source schema4/2 archive
  metadata and an explicit mutation test. Do not mechanically replace these or
  accepted archive1/2 assets. Archive source schema and live owner admission are
  distinct. Its archive owner must decide any modern current-export case.
- Capacity/capacity-relief/fault profiles deliberately use schema4 namespaces
  and calibrated pages. Historical schema4 device/capacity fixtures, hashes,
  accepted archives, old source metadata and calibration remain unchanged.
  Branch revisions, counts and four-handle assertions are not schema versions.

## Verification and handoff

Actually performed: read source/claims, Git isolation, scoped searches, source
hashing and `git diff --check` (passed). No Kotlin compiler, Gradle, Cargo, Node,
JVM test, instrumentation, JNI, SQLite, app, model, device, ADB, CUA, desktop
control, settings, PR or merge operation was run here. All five new tests remain
**UNCOMPILED/UNRUN**. The predicted schema5 rejection is a source finding, not an
executed RED. This packet cannot establish native storage, device preservation,
recovery durability, model operation or functional Domain2 UI.

After importing the frozen source and reconciling path ownership, the
coordinator may compile the existing ordinary app/test APKs in its serialized
build slot with `gradlew.bat --offline --no-daemon :app:assembleDebug :app:assembleDebugAndroidTest`
from `apps/android`, using its verified build environment. This is a proposed
compile command, not a run performed here. Any actual instrumentation invocation
must await an independently authorized isolated device/package allocation;
none is requested or implicitly granted by this source packet. Preserve any
compile/fixture failure separately from behavior failures.

Next runnable task is Root's source integration and APK compilation, followed by
its exact two-line compatibility correction and existing-fixture reconciliation.
Runtime checks remain pending until an admitted device exists. Both exact NEW
path claims are released at handoff; the coordinator retains all production and
verification ownership.
