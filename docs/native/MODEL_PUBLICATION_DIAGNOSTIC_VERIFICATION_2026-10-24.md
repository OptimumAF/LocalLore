# Publication diagnostic verification — 2026-10-24

Refs #9 (M05.05 prerequisite), #5 (M01.05 supporting). Compiled source:
`cb351a63c107758f615ad80104adee80e920abed`, based on unmerged PR #141
at `ab88cb9`. This is a focused stacked diagnostic slice, not an inference
backend or phone qualification. No merge or release was performed.

The [contract](MODEL_PUBLICATION_DIAGNOSTIC_CONTRACT.md) preserves native codes,
the original one-argument publisher, fixed UI errors and no-replace behavior.
The new trusted observer supplies only a closed category. Pure tests and the
separate synthetic-device fixture were authored in independent worktrees;
integration/builds were serialized centrally. The
[independent review](MODEL_PUBLICATION_DIAGNOSTIC_REVIEW_2026-10-24.md) and
[device report](MODEL_PUBLICATION_DIAGNOSTIC_DEVICE_2026-10-24.md) retain evidence
and interpretation limits.

## Host checks actually executed

Both SDK candidate profiles executed:

```powershell
.\gradlew.bat :app:assembleDebug :app:assembleDebugAndroidTest :app:cleanTestDebugUnitTest :app:testDebugUnitTest :app:lintDebug :app:auditLiteRtDependencies :app:auditLintAnalyzer -PlocalLoreLiteRtVerification=true -PlocalLoreModelSetupVerification=true --project-cache-dir .gradle-litert-worker -Pandroid.experimental.lint.version=9.4.1 -Porg.gradle.java.installations.auto-download=false -Porg.gradle.java.installations.paths="C:/Program Files/Java/jdk-21" -Pandroid.builder.sdkDownload=false -Pkotlin.incremental=false --offline --no-daemon --console=plain --max-workers=2
```

The volume profile adds `-PlocalLoreModelVolumeVerification=true`.
Each build ran within an owned Windows job with a 900-second/2 MiB limit;
the terminal results are zero exit with known descendant cleanup.

| Profile | JVM tests / suites | Failure / error / skip | Lint errors / warnings | Elapsed ms |
|---|---:|---:|---:|---:|
| Regular setup candidate | 299 / 31 | 0 / 0 / 0 | 0 / 7 | 321,984 |
| Removable-volume candidate | 299 / 31 | 0 / 0 / 0 | 0 / 7 | 296,593 |

Five new pure test methods cover every existing wire code, unknown integer
boundaries, exact fixed failure redaction, default observation and callback
ordering/count. They do not initialize JNI. The actual diagnostic fixture is
present only in the volume TEST APK, absent from both APPs and regular TEST.
Signed APK/permission/launcher, pinned SDK/notices, dependency/analyzer,
native ZIP/ELF alignment and actual packaged cloud/device-transfer external
backup exclusions pass. Both Android ABIs were cross-built; ARM64 and 16 KiB
execution were not performed. No Rust source changed or Rust host suite was
rerun. Ordinary source sets exclude these changes and were not rebuilt here;
the prior ordinary result is not a new execution claim.

`python -B -E -m unittest discover -s scripts/tests` passed **446 tests** in
19.063 seconds, exit zero. Its retained output SHA256 is
`019285a2ae316bc1ca0d9d81f50e66e1c57dbc7564ea7583fb1f8b66f95b3426`.
A standalone APK-audit subset also passed 18 tests. The separate controller's
32 mocked tests pass; they test refusal/order/proof parsing and do not establish
Android execution. The final durable preparation run took 7.478 seconds.

SDK 0.18.1, Kotlin/Compose 2.4.0, Java 21 compilation/testing with a Java 17
Gradle daemon, AGP 8.10.1, Gradle 8.11.1, NDK 29 and Rust 1.93.1 remain pinned.
No dependency, model, worker provenance, permission, gameplay or licensing
input changed. Official Bionic sources and the installed NDK still place the
existing wrapper at API 30; this does not prove actual symbol resolution.

| Artifact | Bytes | SHA256 |
|---|---:|---|
| Regular APP | 74,818,280 | `41b2cfb4cacc563460f6aae7c0072cd0d4e5bf7835d19e7846df3d90e4da7086` |
| Regular TEST | 1,860,315 | `a69f1d9f09ad9d42b7b7b69428a66e13d881e3e6b4cdd94dc488558c7c377849` |
| Volume APP | 74,818,284 | `c5d37c91c5b4125d997b0a3cbf7a0038af29a78d63fca2f1ba98794176963e7f` |
| Volume TEST | 1,873,559 | `1d12f85fe8e71a2381d80407a201392c8d7452e5ee495e8e5ddec7ee015ed6a0` |

Regular/volume build-output hashes are respectively
`d390f67de34b6e74e6c03206a047d05c18c5488f5d787f67cb8683700155bad3` and
`1423a30a2e7a89990ce156a0608a36215f4cc28a6980698703d0ea1599e177b9`.
The final host seal independently verifies 1,480 files / 170,062,269 bytes,
index SHA256 `2f38c54bb15b6ddbc5b1ffa3c93f28f76a0c1b7f64f53134e7a94a11f0a61318`.
Its public-source snapshot captures all 1,370 tracked files at compiled source.
Scratch temp files are excluded; raw local evidence is not uploaded.

## Actual synthetic diagnostic

One separately reviewed cohort on B (Android 15 / API 35, x86_64, 4 KiB pages)
selected only `ModelPublicationDiagnosticTest#classifyFreshVolumePublicationResultWithoutFallback`.
The ordinary method returned **1 PASS / 0 FAIL for diagnosis**, with native
result **UNSUPPORTED**, `publication_succeeded=false` and
`positive_store_qualification=false`. Its one callback preceded fixed STORAGE.
All 63 original staged bytes/full SHA256 remained; the destination was absent.
The real candidate slot remained absent. No store import, SDK, Engine, story
workspace, model source or launcher ran.

The original wrapper result records child zero / known client cleanup in
36,937 ms, 486 output bytes, SHA256
`2d97c4b0014a87802e6f62cb72e9978f81d6e1d4c3a7fe8fc80d4d604c6224d9`.
The 105 clients perform two own-pair updates, zero pre/post force-stops, fresh
35-package/UID preservation gates and final owned-process absence. Captured
PID/UID/name subset checks do not observe process start identity or qualify
SDK/resource drainage. No previous failed external child was inspected or
modified by the fixture; there is no whole-userdata byte-audit claim.

The disabled proposal independently bound 1,640 inputs / 172,291,478 bytes,
61 shared and 11 private source copies, SHA256
`df32b2e50ef17b4cbe53926ccce86c99bf1604e9bf7ae97a1fba95d2db583fbf`.
Root promoted only its two admission flags after both reviews. The authorization
SHA256 is `8e8acc2005b1948eec4c4c6db1af6e37e8d7a3ea3cf80d882a45c33092978086`.
It authorizes one cohort only, without retry or follow-on authority.

After coordinator acceptance of the consumed original execution terminal, the
frozen local closure helper verified all raw clients/bindings and returned zero.
The final device seal contains 320 files / 1,935,440 bytes, index SHA256
`4b758f955b43ff5c70af57322a07d9ff7a722aa532f76c99f6c275ff1ef5cee5`.
Its entries were rehashed without mismatch. This closes the consumed cohort;
it grants no further device authority and does not turn the refusal into
positive publication qualification.

## Remaining gates and next work

UNSUPPORTED does not distinguish a missing wrapper from EINVAL/ENOSYS/EOPNOTSUPP
and cannot prove a particular filesystem limitation. It does not retroactively
classify either earlier failed method; their failures/seals remain unchanged.
There is still no successful removable publication/import/no-clobber gate.

Fresh external free space after the tiny attempt was **3,556,827,136 bytes**,
below the unchanged real-artifact preflight **4,735,631,360 bytes** by
**1,178,804,224 bytes**. Final userdata free space was **1,222,049,792 bytes**.
This establishes another real-copy admission blocker, independent of the
native result. It identifies neither the cause nor ownership of consumed space
and authorizes no deletion, threshold reduction or benchmark adoption.

Next runnable task: separately claim a closed native-origin diagnostic that
distinguishes missing-symbol refusal from syscall rejection, before choosing
a storage/publication remedy. Capacity planning must preserve current files
and reserves. No fallback, real-model copy or SDK turn follows from this result.
A integrity/capacity, #117 consumption, #119 preservation, physical reference
phone, ARM64/16 KiB execution, sustained performance and full M01/M05 gates remain.
Full task checkboxes stay unchecked pending their criteria and owner acceptance.
