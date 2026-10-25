# Candidate volume verification, 2026-10-23–24

Refs #9 (M05.05 provisioning prerequisite), #5 (M01.05 supporting).
Compiled source: `f3cb9a1fdc8894cb89b0ba57f651cc219c17e7b7`, based on
owner-merged main `1a9a314`. This is a debug storage experiment, not a backend,
phone, real-model or full milestone qualification. No merge was performed.

**Outcome:** both final SDK profiles pass all 294 JVM tests and package audits,
but the corrected emulator method is still **0 PASS / 1 FAIL**, now at native
publication. The positive removable-filesystem gate is blocked. No real-model
copy, SDK use or successful publication compatibility is admitted by this packet.

The [contract](MODEL_VOLUME_CONTRACT.md) and proposed
[ADR-0010](../adr/0010-candidate-volume-storage.md) describe the separate
Context-owned route, retained reserves, owner fences and privacy limits.
Independent policy, fixture and review work used separate branches/worktrees.
The coordinator integrated shared interfaces and serialized builds.

## Executed host checks

`python -B -E -m unittest discover -s scripts/tests` passed **446 tests**.
The final captured run reports 24.234 seconds, child exit zero; its 732-byte
output SHA256 is `999462d78e8daf37206d1ce9313499f3468b60e778815758dcc0c07c6f46fe31`.
`python -B -E -m unittest discover -s benchmarks/spike/android/litert`, with
TEMP/TMP on D:, passed **34 tests**, 0.158 seconds. An earlier default C:
temporary-directory run failed one existing D:-only helper precondition; no
production change or threshold relaxation was made to bypass it.

| Profile | JVM tests / suites | Failures / errors / skips | Lint errors / warnings |
|---|---:|---:|---:|
| Ordinary | 206 / 24 | 0 / 0 / 0 | 0 / 1 |
| Regular setup candidate | 294 / 30 | 0 / 0 / 0 | 0 / 7 |
| Removable storage candidate | 294 / 30 | 0 / 0 / 0 | 0 / 7 |

The final SDK task set, from `apps/android`, was:

```powershell
.\gradlew.bat :app:assembleDebug :app:assembleDebugAndroidTest :app:cleanTestDebugUnitTest :app:testDebugUnitTest :app:lintDebug :app:auditLiteRtDependencies :app:auditLintAnalyzer -PlocalLoreLiteRtVerification=true -PlocalLoreModelSetupVerification=true --project-cache-dir .gradle-litert-worker -Pandroid.experimental.lint.version=9.4.1 -Porg.gradle.java.installations.auto-download=false -Porg.gradle.java.installations.paths="C:/Program Files/Java/jdk-21" -Pandroid.builder.sdkDownload=false -Pkotlin.incremental=false --offline --no-daemon --console=plain --max-workers=2
```

Adding `-PlocalLoreModelVolumeVerification=true` built the separate volume
profile. Ordinary verification used the first five tasks without SDK/setup
flags, dependency/analyzer tasks or analyzer override, and the ordinary project
cache. Its sources exclude the changed LiteRT/test source sets; its earlier
206-test result and artifact remain applicable after their corrections.

The owned final SDK builds returned child zero with known WindowsJob cleanup:
regular **147,453 ms**, output SHA256
`0d299ab70849f9be520637d3efa7951756af2593ca07a8eb8283ba43448e2647`;
volume **144,531 ms**, output SHA256
`0c1aac060c122cb1db21ae187bc0253b1689c5814521ce4c39a58d3cc95385e9`.
The ordinary build returned zero/known cleanup in **277,360 ms**.
Build owners bounded each cohort to 900 seconds/2 MiB output/two workers.
No Java, SDK, dependency or model download was enabled.

Lint retains the SDK-profile target/dependency, obsolete-condition and four
usable-space advisories; ordinary lint retains one dependency advisory. None
was suppressed. SDK 0.18.1, Kotlin/Compose 2.4.0, Java-21 compiler/test launcher,
Java-17 Gradle daemon, AGP 8.10.1 and Gradle 8.11.1 remain pinned. The ordinary
Kotlin/coroutines graph remains separate. The worker changed and its normalized
source provenance is now `aabbe5e27a5f53e8ddf02a16124a3cb14d1898d57bbc552df4f5d1dd257391a4`;
model/runtime revisions and licensing inputs did not change.

Three explicit configuration probes reject missing setup, picker mixing and
false volume flags with the intended guard, child exit one and known cleanup
(10,390 / 12,344 / 9,297 ms). Release variants remain disabled for the required
LiteRT profile, including when a generic assemble task is requested.

Actual signed APK audits passed package/permission, exact SDK binary/notices,
ZIP/ELF 16 KiB alignment and locked dependency/analyzer checks. TEST APKs have
the exact instrumentation target, no shared UID, no native library and only
REORDER_TASKS. Actual packaged cloud-backup and device-transfer rules exclude
all five configured domains including external; allowBackup/fullBackupContent
are false. OEM backup behavior is not established by these checks. Ordinary
DEX excludes the LiteRT/volume classes and its native entries exclude the SDK.

| Artifact | Bytes | SHA256 |
|---|---:|---|
| Ordinary APP | 30,854,648 | `6a3597629bc1340f504bb35cec855b2688c8a9ac2c21d83ef0199fa4cfe039cb` |
| Ordinary TEST | 1,839,443 | `71039aaa8b47c36553db2bc74eab5abe42655227d903f62a032fc91a3948a7ee` |
| Regular APP | 74,818,280 | `978a0a70f733ab4335712f23bc22389a14d9d0ed69c578bf5d7d502c8a201aa4` |
| Regular TEST | 1,860,315 | `a69f1d9f09ad9d42b7b7b69428a66e13d881e3e6b4cdd94dc488558c7c377849` |
| Volume APP | 74,818,284 | `7cae58f2c27c3d8949c724c27eca12555e4b725a033958524fd3052fdabbeba6` |
| Volume TEST | 1,870,807 | `48a5a8fd741ec9c11eab86175f57ada727a14416b13d45544ba4f29640b93823` |

Both Android ABIs were cross-built from current main during the initial full
builds. No Rust source changed in this packet; the Rust host suite was not
rerun. Cross-build/alignment checks do not establish ARM64 or 16 KiB execution.

## Corrections and retained failures

The first regular JVM run reported 293 tests/one failure: a new negative host
fixture used the Android native publisher default and loaded JNI on Windows.
Injecting the existing host publication seam fixed the fixture; actual Android
publication remains the native default. That child-one/known-cleanup receipt
and failed XML remain retained, alongside the successful 293-test intermediate
runs and final 294-test suites.

Review also separated the synthetic child from the real candidate slot before
any device test, and corrected preflight arithmetic: an import must retain
the runtime floor after copying. The fixed model needs **4,735,631,360 bytes**
free externally before import. Eleven pure policy tests cover selection,
wrong/ambiguous/remounted volumes, app ownership, device separation, exact
0/63/model byte boundaries, one-less refusals, overflow and the previously
doomed 3 GiB case. Store tests refuse before source/root access and preserve a
stage when volume invalidation prohibits cleanup. Worker tests fence hashing,
construction, initialization, conversation and send without closing unknown
parents. These finite tests do not reserve storage or predict opaque SDK cache
growth.

The first emulator method failed before select returned: **0 PASS / 1 FAIL**,
25 known-clean clients, two first installs, no stops and no source/native/proof
dispatch. Its owned wrapper returned child two/known cleanup in 14,406 ms;
382-byte output SHA256 is
`d316b1831fa05939f7dcb2ef12dbd9b2deda709023124117c5822e69d12ab821`.
Its 148-file/1,373,941-byte stopped selection has index SHA256
`db81c6182740c25e4da0dd1bbcab577b079a661cb26ed3d800b8d94b00926d4f`.
No post-test process/capacity or native compatibility result was inferred.

The fixed STORAGE error did not identify a predicate. Official Android15
Zygote source independently exposed the legitimate internal Context alias
that the validator could reject. The correction resolves only that trusted
internal anchor; external/model-child checks stay strict. The revised test
reports a finite last-entered stage/alias boolean if refusal persists. It never
exposes the original exception or treats a diagnostic as a successful test.

See the [device report](MODEL_VOLUME_DEVICE_2026-10-23.md) and
[independent review](MODEL_VOLUME_REVIEW_2026-10-23.md) for the separately admitted
corrected cohort and its actual result.

The corrected cohort updated only the same isolated pair after fresh 35-package,
UID, process and capacity checks. Its 59 clients completed with known cleanup;
the single selected method passed select/STABILITY and reached first-import
`NativeModelPublication.publish`, which returned fixed STORAGE. That mapping
combines unsupported native result 2 and I/O/panic result 3; the raw error does
not identify which occurred. There is no native-success, reopen, no-clobber,
rollback, final candidate-absence or post-test process/capacity credit.

Its original owned wrapper returned child two/known cleanup in **31,922 ms**;
497-byte output SHA256 is
`e9ca8eb3b44f59a83eeaf0ba6324deca119415aad84a41c52c1a2eeae4ed4c57`.
There were two same-pair updates and zero before/after force-stops. The last
full observation preserved all old 33 APKs and all 35 UIDs with no owned process
before the method. State after the failure remains unobserved. The 219-file/
1,468,527-byte stopped selection has index SHA256
`97950aa889e180465aca65673279581e76cd9bf131d84df06fa731c1804b9c14`.
Its consumed admission is closed. Thirty separately labeled mocked controller
checks pass; they do not turn this failed device method into a pass.

The final host selection has 594 files/312,653,936 bytes, including 388 source
snapshots, signed copies, XML, audits and terminal receipts. Index SHA256:
`7e1e09ebccbd43da2e837cf47c27da9b1c7dea70073d3f721e91f8ef4173faa8`.
It links the independently preserved initial 645-file/269,546,044-byte selection
`06d1dc9eff4fb87a0589be5cd476c01c852f885619fca19ba64c9781f6e914bf`.
Raw diagnostics, filesystem identities and unique process/device facts stay local.

No real weights were copied, opened or uploaded; no SDK Engine or canonical
workspace was created by the fixture. A integrity and #117/#119 SDK holds,
physical-phone, real-model quality/performance, cache provenance/privacy and
full M05.05 acceptance remain pending. The next runnable packet is narrow native
result diagnosis distinguishing unsupported publication from I/O while retaining
the no-replace contract and all preserved roots. Real-model transfer/turn
admission follows resolution of that gate and the separate copy/runtime holds.
