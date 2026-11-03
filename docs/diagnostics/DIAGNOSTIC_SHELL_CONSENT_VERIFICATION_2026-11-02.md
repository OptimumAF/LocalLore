# Diagnostic consent through the Android ViewModel

B103, 2026-11-02. Refs #14 (M10.03; supporting M10.02 host fault coverage).
Implemented and locally verified for review; full tasks stay unchecked.
This PR stacks on **unmerged PR #377**, exact parent
`2268fe19b6ffa64b3df2507dbe3dbb2d1d18cf94`, branch `fix/m10-local-egress-v1`.
It adds tests/documentation only. No production, engine, schema, permission,
dependency, provider or canonical-contract change is introduced.

During closure, external main advanced from027ddbaf to752e0b06 by merging #375's
five added Desktop worker/evidence-document paths. They are outside this packet's
recorded inputs and qualification. The explicitly stacked parent remains unchanged.

## Concrete coverage gap

PR #377's eight original cases exercise the real DiagnosticsController and the
same captured-action binder used by the Dialog. Main/ViewModel forwarding was
inspected and compiled. Those controller cases would still pass if a future
ViewModel adapter ignored the received review and called its unconditional
current-owner overload instead. The new tests exercise that distinct layer.

Eight original DiagnosticsShellConsentTest methods use the real ShellViewModel,
diagnosticsActions and controller with a scripted durable gateway and a bounded
coroutine test scheduler. The gateway supplies synthetic private title/path
markers; it is not a Kotlin gameplay engine or native/storage/model proof.

The cases cover stale Export/Clear/Close, equal JSON and foreign review identities,
frozen bytes, private exception/cancellation notices, disposal, old-picker draining
and current-review positives. They assert no gameplay response call. A counted
forkContextProvider is deliberately reachable without a fork gateway: a legitimate
owner Close refreshes it once, while an old review Close after that owner closure
must not refresh it at all. This catches a forwarding-side effect beyond hiding
or clearing a diagnostic dialog. Exact shell/log/review conservation assertions
prevent privacy by accidentally discarding the underlying UI state.

The held synthetic writer is always released, models cleared and scheduler
drained in finally, including when a mutation assertion fails. These are finite
host lifetime tests, not real ContentResolver resource-termination guarantees.

## Sensitivity control and original production restoration

The explicit **adapter-only mutant** changes exactly three ViewModel scoped
wrappers to call their no-argument overloads, ignoring the received review.
Controller guards, Main/Dialog binding, original Controller8 and all new test
assertions remain unchanged. It is neither unchanged-main RED nor a newly
confirmed production defect. No mutant is published.

| Phase | Actual outcome |
|---|---|
| First mutant attempt | Gradle startup failure, missing planned D: temp directory; zero JVM methods/task absent |
| Qualified mutant attempt | 16 declared methods:6 assertion failures,10 passes,0 errors/skips;25/25 tasks execute |
| Controller8 within mutant | All8 pass |
| New ViewModel8 within mutant | Six assertion failures, two current-flow positives pass |
| Original production full build | 427 JVM methods/49 suites pass,0 failures/errors/skips;81/81 actionable tasks execute |

The first attempt is retained as a setup failure. The helper pointed Java at
the planned owned D: temporary directory before creating it. Its original helper,
request, raw outputs, source ZIP/maps and known closure remain retained. The
correction creates/validates that ordinary physical-D directory before Java and
requires a real JVM task marker for successful mutation capture. No test source
changed. Setup/compiler/loader errors cannot substitute for assertion evidence.

The qualified mutant's six failures are five java.lang.AssertionError plus one
JUnit ComparisonFailure. Its two positives cover current frozen export with
failure/cancellation and the picker tombstone. The eight controller positives
demonstrate why the new ViewModel layer matters. The reviewer initially classified
only AssertionError; it corrected its read-only audit to include ComparisonFailure,
without changing or rerunning any test.

After known mutant-job closure, the original ViewModel bytes were restored exactly:
SHA256 `2cb9090e606801dfc00e39e2b750294fc1c91d936f16baf32b87391aea628605`.
The same original new8 and old Controller8 bytes then pass in the full build.
**419 existing +8 new =427 actual JVM methods**; do not add the mutation cohort
again or call the expected mutation failures production failures.

## Android source and actual build scope

DiagnosticsIntegrationTest strengthens the existing pending-export recreation
case to pass the captured review explicitly and require the same review object
after Activity recreation. It adds two cases using the actual Main/native fixture:

- Stale scoped Clear/Close cannot change a replacement preview or accepted
  native-facing projection; current UI Clear/Close remain positive controls.
- Stale scoped Export cannot borrow current consent across recreation; current
  consent writes exactly the frozen bytes through a controlled sink, once.

These six integration methods (four existing, two new) **compiled but were not
executed on Android in this packet**. Stale application callers are injected
through scoped ViewModel APIs. Current positive buttons use actual UI actions;
this is not retained Material semantics-node thunk replay, pointer/mount liveness,
an actual picker/provider or real SAF coverage. Same-review recreation legitimately
retains consent; replacement identity is the scope of [ADR-0005](../adr/0005-local-diagnostic-exports.md).

Installed pinned tools: Java21, Gradle8.11.1, ordinary Kotlin2.2.21, SDK36,
Build Tools35.0.0, NDK29.0.14206865 and Rust1.93.1 on Windows. No dependency/tool
installation, upgrade or new runtime/model/license choice occurred.
Actual requests use the verified wrapper JAR and absolute installed Java path:

```text
java -classpath gradle/wrapper/gradle-wrapper.jar org.gradle.wrapper.GradleWrapperMain :app:testDebugUnitTest --tests org.locallore.app.DiagnosticsShellConsentTest --tests org.locallore.app.DiagnosticsReviewActionsTest --offline --no-daemon --console=plain --max-workers=2 --rerun-tasks -Pandroid.builder.sdkDownload=false -Pkotlin.compiler.execution.strategy=in-process
java -classpath gradle/wrapper/gradle-wrapper.jar org.gradle.wrapper.GradleWrapperMain :app:assembleDebug :app:assembleDebugAndroidTest :app:testDebugUnitTest :app:lintDebug --offline --no-daemon --console=plain --max-workers=2 --rerun-tasks -Pandroid.builder.sdkDownload=false -Pkotlin.compiler.execution.strategy=in-process
```

Run from the physical D: Android root with process-local D: temp/cache settings.
Each child waits at a stdin barrier before assignment to the frozen checked
WindowsJob owner. All three phases have known owned-job closure, unchanged
selected tools and identical before/after2,580-file maps within each phase.
The two mutant phase ZIPs capture the same project source bytes; corrected
launcher/temp setup is retained separately. Final project source restores only
the original ViewModel. No source is edited during a live phase.

Full lint has0 errors,1 existing GradleDependency warning and1 existing
AutoboxingStateCreation hint. The existing Kotlin AtomicReference<Boolean?>
compiler warning remains separately recorded. Do not claim zero warnings.
Two no-action asset-generation headers are also marked up to date; they are not
extra executed actions or evidence that the JVM test task was skipped.
Setup11.685s, qualified mutant275.635s and full157.196s are host verification
durations, not inference or device performance.

Main and paired APK CLI audits pass. A separately pinned unmerged PR #376
component/permission auditor also passes; that read-only observation adds no
product dependency on #376. Both JNI ABIs compile; no Android/JNI/ARM64 executes.

| Artifact | Bytes | SHA256 |
|---|---:|---|
| Rebuilt product APK | 28,012,664 | 53ce76a5d431e6109b51475765845efcae90ead71a33ad676118c50fc1c73c07 |
| Android-test APK | 2,265,104 | e703d6ef202b86ef256e8c3edfd625725354db92cb98438f2f96da45da85c1e9 |

The rebuilt product is compared directly and is byte-identical to the retained
PR #377 product. The new code is host regression/Android-test coverage, not a
production fix. Artifact assembly/audits do not establish installation or runtime.

## Source and preservation

Tested code tree `d9b518139d6f95f497aba2d064b03c25542813dd` contains only the
new JVM test and changed Android test relative to the pinned parent. The final
PR adds only this report afterward. Production files match #377 exactly.

| Test input | Bytes | SHA256 |
|---|---:|---|
| Original new JVM8 | 13,311 | f235c2074a51ca24a7c4ed1bfd0bac020b73439d10e4e63c95aa44a40b89bb4f |
| Android integration source | 7,769 | 17681f092965cbd160c59bcaadd327eb3e8dddf15d1996eee248f469e28c0b8c |

Original Controller8 remains SHA256
`247b27e53daef734e447646bccd34e7173cfa7f75b830caf091fa47e1664a6de`.
Independent source/oracle and closed-mutation reviews completed; later complete
build/report/preservation reviews are recorded with their actual status.
Reviews do not constitute owner acceptance.

Private output/recovery basename `2026-11-02-diagnostic-shell-consent-v1`.
Retain setup failure, mutant/original bytes, three phase source ZIPs/maps, raw
outputs/XML, partial/final captures and protocol records. A posthoc review-only
B101 file is explicitly copied as supplemental evidence outside B101's old seals;
it does not backdate a capacity-failed review or change old source/manifests.
No private stories, credentials or model weights enter this PR.

Bounds: source128MiB, generated3GiB, synthetic256MiB, controls128MiB, selected
recovery512MiB. Final sampled generated644,168,254B stays in place; selected
recovery does not claim a build-cache backup. Sampling is not an OS quota or
continuous peak proof. The shared two-root/64GiB AVD budget is unchanged.

No device/ADB/emulator/phone/model, settings, shared-ledger/image retirement,
deletion, private upload, release or merge occurred. Original checkout/index and
other worktrees are preserved. Full Rust/Python/frontend/CI, actual Android UI/SAF,
installed offline/traffic/SDK/OS privacy, physical/model/M10.05 and Knowledge0/4
remain separate unadvanced gates requiring applicable authority and evidence.
