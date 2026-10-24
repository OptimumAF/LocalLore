# Native publication-origin verification — 2026-10-24

Refs #9 (M05.05 prerequisite), #5 (M01.05 supporting). Compiled source
`69342d8ccc87fad61045ec516caca52bf74961d5`, based on unmerged PR #142 at
`e05fc86`. This slice implements the [closed origin contract](MODEL_PUBLICATION_ORIGIN_CONTRACT.md),
not a publication fallback, supported backend or physical-phone qualification.
Independent test, device and review work used separate owned worktrees.

**Actual outcome:** one diagnostic method passed and observed RENAME_INVALID
(the resolved wrapper returned EINVAL), `origin_classified=true`,
`publication_succeeded=false` and `positive_store_qualification=false`.
The exact 63-byte stage remained; destination and real candidate root were absent.
There is still no successful removable publication/import qualification.

## Executed host checks

```powershell
cargo +1.93.1 fmt --all -- --check
cargo +1.93.1 clippy --locked --offline -p locallore-android --all-targets --features model-provisioning -- -D warnings
cargo +1.93.1 test --locked --offline -p locallore-android --features model-provisioning
python -B -E -m unittest discover -s scripts/tests
```

Formatting and strict clippy pass. The package suites pass **90 tests**, zero
failed/ignored, including three new classifier tests. The classifier tested on
the host is used by the actual Android rename-error path. The sequential owned
Rust job returned zero/known cleanup in 75,984 ms; output SHA256
`77dcb3fd9aa427b9af97f9a2e8c0dfd000eaa1d2c879b26a41bcb2d191d53396`.
This is a package/feature check, not a rerun of the complete workspace suite.
The script suite passed **446 tests** in 20.668 seconds; retained output SHA256
`bb3e2d16600aa73f9fe132c2448505057327dbe3e4ae1f89a304108d9e743805`.

Both SDK profiles executed the following from `apps/android`, with the volume
profile additionally setting `-PlocalLoreModelVolumeVerification=true`:

```powershell
.\gradlew.bat :app:assembleDebug :app:assembleDebugAndroidTest :app:cleanTestDebugUnitTest :app:testDebugUnitTest :app:lintDebug :app:auditLiteRtDependencies :app:auditLintAnalyzer -PlocalLoreLiteRtVerification=true -PlocalLoreModelSetupVerification=true --project-cache-dir .gradle-litert-worker -Pandroid.experimental.lint.version=9.4.1 -Porg.gradle.java.installations.auto-download=false -Porg.gradle.java.installations.paths="C:/Program Files/Java/jdk-21" -Pandroid.builder.sdkDownload=false -Pkotlin.incremental=false --offline --no-daemon --console=plain --max-workers=2
```

| Profile | JVM tests / suites | Failure / error / skip | Lint errors / warnings | Owned elapsed ms |
|---|---:|---:|---:|---:|
| Regular setup | 299 / 31 | 0 / 0 / 0 | 0 / 7 | 353,454 |
| Removable volume | 299 / 31 | 0 / 0 / 0 | 0 / 7 | 318,703 |

Both bounded Windows jobs returned zero with known descendant cleanup. Their
output hashes are respectively
`2a514caeb2c5cd45013e61d33f0950b7407bc07b3cfe44940fe18d211fe0a4a2` and
`dfa99a7d9a69e72a875511b36f5510252483845ea73e0ea5ce8496af6a786d3e`.
The updated five-method JVM fixture covers every legacy/new category, integer
boundaries, unchanged fixed failures and observer ordering/cardinality.

Signed APK, exact package/permission/launcher, SDK/notices, dependency/analyzer,
native ZIP/ELF alignment and packaged cloud/device-transfer backup exclusions
pass. Actual DEX inspection places the new origin fixture only in volume TEST,
absent from APPs and regular TEST. Both Android ABIs cross-built; ARM64 and
16 KiB execution were not performed. Ordinary Android was not rebuilt here.
Existing pinned SDK 0.18.1, Kotlin/Compose 2.4.0, Java toolchains, AGP 8.10.1,
Gradle 8.11.1 and NDK 29 remain; no dependency/model/license input changed.

| Artifact | Bytes | SHA256 |
|---|---:|---|
| Regular APP | 74,818,360 | `f11bcf88905a3b58d04a93599ed1d0e13a4927596f532172e474f509b30e232e` |
| Regular TEST | 1,860,315 | `a69f1d9f09ad9d42b7b7b69428a66e13d881e3e6b4cdd94dc488558c7c377849` |
| Volume APP | 74,818,364 | `318f84bd85400bc58ee67b6c843427f0cf927baa36a846739831e8273a218c4e` |
| Volume TEST | 1,876,503 | `185aac71e0a4d00ba9367425fc982a9cc942ea57a4fe65e0c55c8003aa5230b9` |

The final host seal covers 1,488 files / 170,117,736 bytes, SHA256
`81835dcbcfe140154f56c11432a4749ba6294d740ccd7fc187a469dd5c7dca5d`,
independently rehashed without mismatch. Its snapshot captures all 1,376 tracked
files at compiled source; scratch temp files are excluded.

## Actual device observation

One separately admitted B/API35/Android15/x86_64/4KiB cohort selected only
`ModelPublicationOriginTest#classifyFreshPublicationOriginWithoutFallback`.
It returned **1 PASS / 0 FAIL for diagnosis** and made exactly one actual native
publication call in its fresh fixed sibling. Source-bound assertions checked
one callback, fixed STORAGE, exact stage bytes/full hash and absent destination.
It called no store import, SDK, Engine, workspace, model source or launcher.
Earlier failed/diagnostic roots were not read or written; their categories and
sealed evidence are not retroactively changed.

The original execution handle 58255 was consumed with actual tool exit zero
(chunk 55f900), child zero/known cleanup in **43,891 ms**. Its 482-byte output
SHA256 is `b8bf2132b6866c31055f299a7c7e66c7f2499dc73dd0e1712b3af4424ed77ed1`;
stderr byte count is zero. All **105 clients** have known terminal receipts.
Two own-pair updates preserve the other 33 APK hashes and all 35 installed UIDs;
all conditional pre/post force-stop counts are zero and final own/passive
process rows are absent. Captured PID/UID/name subset checks do not observe
process start identity or establish natural SDK/resource drainage. No whole
userdata byte audit is claimed.

Before root admission, both reviews rehashed the disabled proposal's 1,663
bindings / 172,484,785 bytes, including 64 shared and 13 private source copies.
Its SHA256 is `bc7d7413915e40bad4de1df92c58d6e3c6362915dcf0a04dc134454a1e7fd131`.
The durable preparation run passed all **37 mocked controller tests** in
10.261 seconds; these cover strict result/type/category/ordering refusals,
including legacy results that do not qualify an origin. Root changed only the
two admission flags; authorization SHA256
`51cc3981744f3e8067f03f610e403cb5ed48ee2847332eded1527bb68caed3be`.
After original-terminal acceptance, the frozen local closure returned zero.
Final device seal: **327 files / 1,957,888 bytes**, SHA256
`7a87494483a08197d9fd59c889d835080be8e6ada88b4e6d995051826ad923d5`,
independently rehashed without mismatch. No further device authority remains.
Raw identifiers, paths and diagnostics stay local.

## Limits and next runnable work

The fresh call establishes that lookup returned a callable wrapper and that
the wrapper rejected this rename with classified EINVAL. It does not identify
the rejecting layer or classify older attempts. Official Android15 MediaProvider
[FuseDaemon.cpp](https://raw.githubusercontent.com/aosp-mirror/platform_packages_providers_mediaprovider/android-15.0.0_r1/jni/FuseDaemon.cpp)
rejects nonzero rename flags with EINVAL. That is a source-consistent hypothesis
for NOREPLACE=1, not proof this particular device traversed that implementation.
No replacing rename, hard-link, alternate-volume or other fallback was enabled.

External free space was 3,556,827,136 bytes before and **3,556,818,944** after.
The latter is **1,178,812,416 bytes** short of unchanged real-artifact admission
4,735,631,360. Userdata was 1,299,030,016 at the source checks and 1,299,017,728 at
the final controller check. These observations do not attribute consumption or
authorize cleanup, a lower reserve, benchmark adoption or model copying.

Next: separately claim an executable host proof of a compatible publication
and capacity design, retaining atomic visibility/no-clobber requirements and
existing files. A larger environment must preserve the exact-one eligible-volume
contract or separately review explicit selection; it does not automatically fix
the observed publication refusal. No new environment or storage route is enabled
by this packet. Positive native/import, real model/SDK, A/#117/#119, physical
reference phone and full M01/M05 gates remain. Full tasks stay unchecked pending
their complete criteria and owner acceptance; no merge or release occurred.

See [device evidence](MODEL_PUBLICATION_ORIGIN_DEVICE_2026-10-24.md) and
[independent review](MODEL_PUBLICATION_ORIGIN_REVIEW_2026-10-24.md).
