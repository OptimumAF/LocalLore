# Android cancellation presentation, 2026-10-23

Refs [#9](https://github.com/OptimumAF/LocalLore/issues/9), M05.04 partial,
and [#8](https://github.com/OptimumAF/LocalLore/issues/8), M04.04 supporting.
Prerequisite: unmerged [#122](https://github.com/OptimumAF/LocalLore/pull/122),
exact `73cd948e9c215bfa50f0eb9912f3171d1bd1b603`. This follow-up stacks on
that branch; it does not merge its prerequisite or claim milestone acceptance.

## Reproduced problem and correction

ShellViewModel scheduled cancellation reconciliation and immediately recorded
`CANCEL / COMPLETED`. A delayed acknowledgement, malformed reply or storage
failure could therefore leave a false completion record. A valid committed race
loaded its accepted history but displayed the misleading notice `Response stopped`.

Correction `efc962543d6f47180a98dcca93114da79dd009c7` records completion only
after DurableGateway returns its validated acknowledgement and saved snapshot.
Failure records `UNKNOWN` with an existing fixed error category and preserves
the original recovery guidance. Coroutine cancellation propagates; disposal
prevents late logging/publication. The notice now says `Cancellation checked.
Showing the accepted saved history.` It accommodates a commit that won the race.

The existing saved-operation publication, original-key recovery, generation
fence and authoritative snapshot remain intact. No engine, JNI, wire, database,
runtime, model, dependency, permission or diagnostic schema changed. Kotlin
does not gain gameplay authority. No raw exception text enters the diagnostic.

## Frozen tests and actual results

Root controller tests were frozen in `43915d6` before correction. The targeted
JVM baseline ran three methods: **one passed / two failed** (delayed and failed
acknowledgement). Disposal already passed and is retained coverage. The owned
build completed child one with known Windows Job cleanup in **25,922 ms**.
Its XML and raw diagnostics remain local; failure was expected, not a green run.

Independent actual-Android tests were frozen in
`27346b6259fe32694a0c582de83bbb3c0b043b40`, imported as `74d4a7b`, before
production correction. Seven methods use actual ShellViewModel, DurableGateway,
the Android main dispatcher and platform JSONObject with a synthetic transport.
Finite gates hold preparation, cancellation acknowledgement and snapshot reads.
They do not launch an Activity or invoke NativeWorkspace, JNI, SQLite or inference.

| Same frozen seven methods on emulator B | Passed | Failed | Owned commands | Elapsed |
|---|---:|---:|---:|---:|
| Unchanged ShellViewModel | 2 | 5 | 42 | 10,125 ms |
| Corrected ShellViewModel | 7 | 0 | 42 | 10,703 ms |

The five baseline failures were premature completion before acknowledgement,
premature completion before snapshot reconciliation, uncertainty reporting after
invalid acknowledgements, uncertainty reporting after Full, and the false stopped
notice after a committed race. The invalid-ack method first fails at its final
diagnostic assertion after testing foreign-turn recovery; the candidate also
executes its ready and malformed committed-receipt variants. The baseline does
not independently reproduce failure for every later variant. Late preparation
and disposal passed both versions. No oracle, source or test APK changed between
these runs. Each run had all seven start/terminal pairs, no skips/unfinished
methods, and the final runner terminal after every pair. ADB exit zero alone
was not considered a test pass.

The candidate freshly ran **150 JVM tests**, zero failures/errors/skips, across
19 XML files, including all three new controller methods. Lint reported **zero
errors / one GradleDependency warning** for the existing pinned coroutines.
App/test builds, identity/permission/runner audits, native ELF 16 KiB alignment
and ZIP alignment checks passed. Native build outputs were reused; all four
packaged native-library hashes match the baseline. No new native compilation or
ARM execution is claimed. The baseline retained the existing unrelated
FrameworkInterruptionTest AtomicReference/Boolean compiler warning.

## Reproduction and environment

Existing pins: Java 17.0.6, Gradle 8.11.1, AGP 8.10.1, Kotlin 2.2.21,
coroutines 1.10.2, SDK compile/target 36, minimum 26, Build Tools 35.0.0,
NDK 29.0.14206865 and Rust 1.93.1. No new compatibility choice was made.

From `apps/android`, with those existing toolchains configured:

```powershell
.\gradlew.bat :app:testDebugUnitTest --tests org.locallore.app.CancelDiagnosticsShellTest -PlocalLoreCancelAckVerification=true --project-cache-dir .gradle-cancel-ack --offline --no-daemon
.\gradlew.bat :app:assembleDebug :app:assembleDebugAndroidTest :app:cleanTestDebugUnitTest :app:testDebugUnitTest :app:lintDebug -PlocalLoreCancelAckVerification=true --project-cache-dir .gradle-cancel-ack -Pkotlin.incremental=false --offline --no-daemon
```

The actual owned commands also selected plain console, two workers,
`android.builder.sdkDownload=false` and the existing Java wrapper directly.
They ran inside a 900-second, 2 MiB output Windows Job with an input barrier
before launching Gradle and verified cleanup. Baseline app/test assembly took
**39,984 ms**; candidate assembly/fresh JVM/lint took **70,907 ms**, both child
zero with known cleanup. Root's 185 script tests from #122 were not rerun or
counted as new results; no script changed here.

On an admitted authorized emulator, select only this class:

```powershell
adb -s <authorized-target> shell am instrument -w -r -e class org.locallore.app.CancelPresentationTest org.locallore.app.cancelack.test/androidx.test.runner.AndroidJUnitRunner
```

Use exact source/APK bindings, package maps, storage and process checks before
installation. Each cohort has a 180-second owned outer limit and 45-second
instrumentation limit. Never substitute this command alone for admission or
method-pair/terminal parsing.

## Source and artifact binding

| File | Baseline SHA256 | Candidate SHA256 |
|---|---|---|
| ShellViewModel | `1cfe225a31c407fa28056a17b03491758ab716d7113664471871f4cae0430bac` | `8a8075478029cbefbdcb0a286805b2bc53b5a487f36c3295fa643ddc9e34c948` |
| App APK | `342d71e5d68913af1ec16f3f4789723f082739e4836b101b716d78906f36a1cd` | `d8b82930934304a3352b8cbab415c69b490fafa189364815d71e6d88382fc94d` |
| Test APK | `1161ac649721f22dab3d812364b4f92711c53969dfe67cff214bd4c3cbb49b8e` | same |

The baseline app is byte-identical to #122's candidate. App sizes are
22,524,075 / 22,524,394 bytes; the unchanged test APK is 2,312,557 bytes.
Integration test source SHA256:
`29024f68c30e44307a8c115830b39c95b4b03545a53e23a32ceb7a6838b229a1`.
Controller test source SHA256:
`77dae7774b79f23b88213f58d3ab82eb3fd92a9d84eafe37e69c171188db9e17`.
These exact checkout bytes match the committed Git blobs. The gateway SHA256
remains `67f217690914ad05ff1b34b3cff165890265b4bf41a6971a5da5044a3b8eefd2`.

## Device scope, retained failures and handoff

Only the existing B emulator was queried: API 35, x86_64, 4096-byte pages.
Both cohorts completed all 42 clients with exit zero and known cleanup.
The original 23 package hashes matched before/installed/after/final observations;
the expected app/test pair accounts for the other two packages. Final userdata
free space was **1,622,237,184 / 1,599,746,048 bytes**, above the unchanged
**1,207,959,552-byte** admission floor. Namespace process-absence checks passed.
No lifecycle action, data clearing, device reset or model copy was performed.

The coordinator and independent reviewers rehashed the completed command
outputs against their metadata. Raw baseline instrumentation: **27,161 bytes**,
SHA256 `bf2da61f42ebab3659c94fbad15687552519cf9f48f0425f15661fcba97bbb4d`;
candidate: **5,026 bytes**, SHA256
`b7ef41c4f26e214d322cd06c11a089999ae3cb8031beea2ff125cba249865a83`.
Raw diagnostics, process/transport identifiers and APKs remain local.

The closed device selection has **224 files / 297,843 bytes**, all rehashed by
the coordinator and reviewer with zero mismatches. Its **38,037-byte** index
SHA256 is `f0b1057eab86815c74fa2c5121bb9480c7b721b915a6352d3ab815148ad14cba`.
The selected closed host evidence has **53 files / 49,870,725 bytes**: exact
APKs, source copies, build logs/receipts, JVM XML and lint XML, excluding temporary
build files. Its **9,899-byte** index SHA256 is
`ca894077eec29444dd9953ffc50103709e37f5ca5aeba7b8a2727ec7eada3be2`.
These selections include overlapping bytes, not additional experiments.

Runner preparation initially retained the old evidence path in two draft
sources. Root caught this before authorization/dispatch; corrected sources used
the new namespace. Drafts and the correction receipt remain retained, and no old
sealed root was mutated. Twenty pure runner fixtures passed on the corrected
source; overlapping earlier fixture runs are not additional unique tests.

A remains **blocked** by the prior cold storage preflight: 1,045,565,440 bytes
free, 162,394,112 below the unchanged floor. It was not queried or tested again.
M01.01 physical-phone verification remains blocked. Earlier M01 timeout,
storage and preservation failures remain unchanged. No two-emulator, rendered
Compose, native cancellation/reclamation, database replay, process-restart,
real-model, quality, sustained-session or physical/ARM qualification follows.

See the [device report](ANDROID_CANCEL_PRESENTATION_DEVICE_2026-10-23.md) and
[independent review](ANDROID_CANCEL_PRESENTATION_REVIEW_2026-10-23.md).
M05.04 remains **in_review, partial**; M04.04 receives supporting evidence.
Acceptance boxes stay unchecked pending full criteria and owner acceptance.
No merge, release, access/protection change or private payload upload occurred.

Next runnable task: exercise the visible Compose recovery controls with these
delayed/invalid acknowledgement cases and accepted commit races. Real backend
and reference-phone gates still require their independent admission/evidence.
