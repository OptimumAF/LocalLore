# Android saved-task process restoration — 2026-10-26

M05.05 supporting lifecycle work, M09.03 draft-persistence preparation and
M10.02 supporting mobile fault testing. **In review; full task criteria and
owner acceptance remain pending.** Based on unmerged input-draft PR #191 at
`78ec2523`; this packet does not merge that dependency or any implementation PR.

## Product behavior

After a background process death, the Android Activity supplies only the saved
story/branch IDs as an initial navigation hint. The gateway validates the full
fresh native workspace catalog and the hinted story's active branch catalog
before resuming that selection. Native revision, session and accepted history
are reread rather than restored from a Bundle. This fixes the case where lexical
story A was reopened instead of previously selected story B, causing B's scoped
unsent draft to be discarded.

Missing, unknown or retired selections resolve to the available library with a
one-shot notice. Malformed catalogs, storage/transport failures and resume/head
races remain recovery errors; the hint survives incomplete initialization and
is consumed only after a coherent snapshot or empty resolution. Later explicit
navigation cannot reapply it. A retained ViewModel keeps its existing owner.
Restoration never sends a message, creates a story or restarts inference.

The hint is a strict versioned three-field UI record, with native ASCII IDs,
not authoritative gameplay state. Existing draft limits and scope fences remain
unchanged. No Rust, SQLite schema, dependency, inference backend or model choice
changes. Ordinary builds disable the debug observers and accessibility tag
export. The [closed protocol](ANDROID_PROCESS_RESTORATION_PROTOCOL.md) specifies
the isolated product/controller, fixed arguments, bounded private observations,
saved-state acknowledgement and terminal-operation checks.

## Commands and environment

Windows x64, Python 3.14, Java21, Rust1.93.1; cached AGP8.10.1, Kotlin2.2.21,
Compose runtime-saveable1.8.2/BOM2025.05.01; compile/target36, min26,
NDK29.0.14206865. No dependencies downloaded or added. Existing toolchain and
dependency sources remain applicable. The controller uses Android framework
APIs only, including an API34-guarded UiAutomation cache refresh; this does not
change accessibility settings or clear application data.

From `apps/android`, with task-local Java/SDK variables and cached prerequisites:

```powershell
.\gradlew.bat :app:testDebugUnitTest :app:lintDebug :app:assembleDebug :app:assembleDebugAndroidTest :draft-process-controller:assembleDebug :draft-process-controller:lintDebug --offline --no-daemon --console=plain --max-workers=2 --project-cache-dir .gradle-input-process -PlocalLoreInputDraftVerification=true -PlocalLoreInputProcessVerification=true -Pkotlin.incremental=false -Pandroid.builder.sdkDownload=false -Porg.gradle.java.installations.auto-download=false
```

The final rebuild additionally executes `:draft-process-controller:clean` first.
It records Java as well as Kotlin/Rust/configuration sources. From the root:

```powershell
python scripts/audit_apk.py apps/android/app/build-input-process/outputs/apk/debug/app-debug.apk --input-process-verification
python scripts/audit_process_controller.py apps/android/draft-process-controller/build/outputs/apk/debug/draft-process-controller-debug.apk
python -m unittest discover -s scripts/tests -p test_audit_apk.py -v
python -m unittest discover -s scripts/tests -p test_audit_process_controller.py -v
```

The product is `org.locallore.app.draftprocessverify`, using the real
`org.locallore.app.MainActivity`, JNI/Rust/SQLite and scripted inference. The
self-targeted controller is `org.locallore.app.draftprocesscontroller` with
`org.locallore.processverify.ProcessRestoreInstrumentation`. Run it using
`am instrument -w -r`, supplying exactly `case=restore_non_default`, fresh
hex16 `run_id`, the actual product SHA256 and `cohort=create`. Require the
complete bounded JSON proof and `INSTRUMENTATION_CODE: -1`; ADB exit0 alone
does not qualify the case. Product instrumentation uses
`org.locallore.app.draftprocessverify.test/androidx.test.runner.AndroidJUnitRunner`.

Actual execution pins the existing ADB server/binary and exact owned emulator
identity/transport, validates installed package UIDs and hashes, captures each
client with known process-owner cleanup and checks sources before/after. Fresh
API35 Google APIs x86_64 targets use2GiB/two CPUs,320×640 and4KiB pages. These
are scripted UI targets, not supported model profiles. The task-specific budget
requires4GiB available physical memory,2GiB guest commit plus2GiB reserve and
C:64GiB/D:16GiB free. Existing AVD registries/configuration, the unrelated
emulator, the shared ADB server and system settings remain unchanged.

## Actual evidence and corrections

| Gate | Observed result |
| --- | --- |
| Original product RED | Actual saved-task kill/relaunch restores A instead of selected B. Expected FIRST_RESTORE/SCOPE failure, one real death; owner188,592ms/0,103 clean clients,509 stable enumerated sources. Original product hash `7745e5a639e3f4d10d78bc0d283a4d77a3ed11e25cf22b1aeff3b4da89cd0519`. |
| Production fix | Gateway `e4a1691a`,12 platform tests `2deb66ac`, Activity wiring `5997ca92`. Build161,606ms/0;234 JVM tests/27 classes actually execute, zero failures/errors/skips. |
| Same-cohort first Green | Both deaths/restorations and one B commit succeed, but the final native catalog check fails because the tagged menu parent has empty text. Owner171,406ms/1; retained as partial failure, not a full pass. |
| Controller correction `9766084a` | Read the unique nested label only within the exact tagged menu item's bounded subtree. Fresh equivalent cohort passes81 checks, two actual deaths,80 clean clients; owner172,590ms/0. The earlier B1 cohort is preserved, not reset or adopted. |
| Original broader regressions |13 classes/72 methods:40 pass,32 fail, no skips. All32 failures retained before correction: Timeline6/M08 admission2/cancellation24. New navigation12/probe1, parent draft/UI15, existing shell6 and actual JNI ownership7 pass. Observation owner237,904ms/0 is not a passing regression gate. |
| Test-only corrections | `37d4158e` removes an extra workspace-row `retired` field from two fixtures and changes three valid cancellation fixtures from obsolete database schema4 to5. Branch-catalog retirement metadata and intentionally invalid schemas remain. `3f4e3376` requires the initial malformed-schema error's typed `WorkspaceFailure("Malformed")`; refresh expectations/no-gameplay assertions remain unchanged. No production validation is weakened. |
| Final source/build record | Initial510-file maps omitted Java; they describe only those enumerated files. The final clean-controller build records515 unchanged files including all five Java sources:23,621ms/0,45 tasks executed/80 UP-TO-DATE.234 JVM results are retained from the actual production-fix execution, not claimed rerun. |
| Artifact checks | Actual signed product/test/controller pass11 audit/badging/manifest/signing commands; owner2,239ms/0. Same certificate, exact package/permissions, disabled backup, runner target and dual-ABI/16KiB native alignment checked. Product lint0 errors/1 existing warning; controller lint0 errors/2 warnings (DataExtractionRules, MissingApplicationIcon). This is not a whole-DEX SDK-absence audit. |
| Final APK process oracle | Fresh cohort, final APKs: **81 checks/two genuine deaths pass**, three distinct PID/start identities, one task, restored-state true on both relaunches, factory1 in every process. Exact old terminal vectors and final native A0/B1/draft checks pass. Owner214,241ms/0,95 clean completed clients,515 stable sources/helpers; model calls0. |
| Audit regressions/profile refusals |51 Python audit tests pass/2.435s. Eight invalid Gradle configurations actually refuse for their expected reasons: missing parent, false flag, three wrong-cache/profile combinations, release, mixed profile and capacity mode. Earlier46-test run remains dated evidence. |

The clean controller APK differs from the previous passing APK in archive
layout/hash, despite matching indexed entry payloads. The matching preflight
therefore refuses before updating the device. The final artifact requires its
own fresh-cohort qualification rather than a retrospective source-binding claim.

Retained final signed artifacts:

| APK | Bytes | SHA256 |
| --- | ---: | --- |
| Product |24,662,902| `934f939bd48781216f749dc0173efab94bf70f4a2a2438938c23ef0251c1fc42` |
| Android tests |2,645,834| `6cfec70fa6c4ab9f4c09f744a4932b2579c639a33b704ed603efe6111bfb9845` |
| External controller |37,473| `ce5ae972e5d6173ac3550ed4238935583a4d30ad3919e868048c83b6f69295c3` |

The corrected regression run passes **all72 methods in13 classes**, zero
failures/skips, owner251,022ms/0 with known cleanup/capture,515 stable source
hashes and89 completed/0/clean clients with zero stderr. Every source method
roster, start/pass pair and final `OK` is checked, not merely the client code:

| Class | Passing methods |
| --- | ---: |
| InitialNavigationGatewayTest |12|
| ProcessVerificationProbeTest |1|
| PlayDraftRestorationTest |6|
| PlayDraftActivityTest |1|
| PlayInputScreenTest |2|
| ShellInstrumentedTest |6|
| TimelineProtocolTest |8|
| M08Schema5AdmissionTest |5|
| CancelAcknowledgementTest |9|
| CancelControlsTest |8|
| CancelPresentationTest |7|
| DurableNativeTest |5|
| DurableTransportOwnershipTest |2|

The last seven methods exercise actual JNI/Rust/SQLite and native owner
release; protocol fixture tests do not establish SQLite replay by themselves.
Both installed product and controller are the exact final audited APKs.

After every client closes, only the exact owned LocalLore emulator job is
stopped:507,097ms, `stop_requested`, known cleanup/capture, helper/manifest and
external registry/token observations unchanged. Worker1 reflects requested
termination, not a successful guest exit. No guest-flush claim is made.

The selected private evidence index binds4,398 files/24,420,164B, SHA256
`af5aa751303dd7ab26e9197d2751c080e4df1308b753b29f15d46510d92d3761`.
It includes retained original failures, source snapshots, raw client/proof
records, JVM/lint reports and the external owner/controller drivers. APKs are
retained separately with the hashes above; weights, guest images, compiled
caches and other-project data are excluded. This index is local evidence, not
an upload of private diagnostics or a claim to have saved every intermediate
APK. The final515-input source snapshot includes Java; older510-input maps do
not retroactively acquire that coverage.

Earlier failures remain retained: manifest namespace/multidex/badging parser
assumptions, framework shell tokenization, empty/hidden accessibility headers,
task-dump delimiter assumptions, cumulative create-counter expectations and a
wrong external launcher-record path. Each is distinguished from the genuine
product RED. No unique cause is claimed for multi-change UI-readiness progress.
Old artifact versions not separately retained are not claimed retained as APKs.
Closing a timed-out descriptor never establishes remote-child termination.

## Limits and next runnable work

This qualifies a root-branch saved-task path with scripted inference on one
API/ABI configuration. It does not qualify branch/fork process death, force-stop,
task dismissal, cold-launch draft retention, whole-device power loss, every
Android version, sustained inference, phones, accessibility or narrative quality.
Both native ABIs package, but this packet executes only x86_64. No model is
loaded, copied, downloaded or uploaded in this lifecycle packet. Synthetic
fixture IDs, private raw diagnostics, APKs, guest images and weights stay out
of Git. Known host-owner closure is not a guest-disk-flush guarantee.
Owner durations include admission, client startup and verification; they are
not inference latency, cancellation latency or supported-device benchmarks.

The Samsung reconnected during the independent [phone harness follow-up
PR #186](https://github.com/OptimumAF/LocalLore/pull/186). Windows USB selection
and unrelated process names containing whitespace are handled with strict
independent identity proof.1191 host tests pass; actual read-only discovery
completes74 clean clients but refuses model admission: available memory
4,196,491,264B is98,476,032B below the unchanged4GiB minimum. No phone APK update,
model copy/load/inference, app stop or system-setting change occurs. Earlier
phone-absence evidence is historical. Do not repeatedly sample until favorable.

Next runnable lifecycle task: extend the same external oracle to an active
non-root branch, including retired/missing-selection recovery. Phone model work
requires a meaningfully fresh state and complete fresh admission before the
already-authorized local model phases. Full M05.05/M09.03/M10.02 and the
reference-phone/quality gates remain unchecked pending their wider criteria and
owner acceptance. No merge or release.
