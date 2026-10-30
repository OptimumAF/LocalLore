# Public Android check: fresh offline archive build

Date: 2026-10-30. Scope: M10.03 supporting verification, in review;
full task criteria and owner acceptance remain open.

The complete public checker now has an actual successful execution after
[#287](https://github.com/OptimumAF/LocalLore/pull/287)'s paired-APK gate.
This packet changes documentation only. The implementation under test is
`c5edb388d9c7714dfcaac7ba82f41a6a3cc4f494`, with 2,299 tracked raw inputs.
The checkout and archive output directory were fresh. Earlier packets and
their failed or successful results retain their original attribution.

## Actual command and result

```powershell
python scripts/check.py android --archive-verification --offline
```

The owned child used Python's `-I -S -B` interpreter flags and the unmodified
repository script. No private Gradle replacement, task exclusion, source patch,
init script, extra profile, dependency change or device command was used.
The actual public sequence was:

1. The verified Gradle wrapper: `:app:assembleDebug`,
   `:app:assembleDebugAndroidTest`, `:app:testDebugUnitTest`, `:app:lintDebug`,
   `--no-daemon --console=plain -Pandroid.builder.sdkDownload=false`,
   `-PlocalLoreArchiveVerification=true --offline`.
2. `scripts/audit_apk.py` on the new archive product APK, with
   `--archive-verification`.
3. `scripts/audit_instrumentation_apk.py` on the new product/test pair, with
   `--archive-verification`.

The public call returned **0 in 218,002 ms**. Its single 900-second Windows
process-tree owner closed in **220,020 ms**, with worker exit 0, complete cleanup
and capture, stdout 10,948 bytes and stderr zero. Source and all seven recorded
tool/helper/proof pins matched before and after. The raw log contains all three
command boundaries and both successful audit outputs. Individual command success
also follows from the unchanged runner's first-failure return behavior; there
are no invented independent per-command execution receipts.

| Check actually performed | Result |
| --- | --- |
| Rust Android builds | Both `x86_64-linux-android` and `aarch64-linux-android` compiled offline |
| JVM tests | 332 unique cases / 39 XML reports; 0 failures, errors or skips |
| Lint | 0 Error/Fatal; 1 existing `GradleDependency` warning |
| Product APK audit | Passed, including the existing manifest/backup/ZIP/ELF contract |
| Instrumentation pair audit | Passed, exact archive packages/runner/permission policy and matching verified signer |

The warning is the existing coroutines-Android 1.10.2 versus 1.11.0 update
notice. This packet does not update dependencies. Lint's XML identifies
`lint 8.10.1`; ordinary `checkDependencies` scope is unchanged.

Gradle records 81 actionable tasks / 81 executed. The native build, unit-test,
lint analysis/report and both assembly task lines have no cached/up-to-date
suffix. Empty asset-generation tasks are up-to-date and several tasks are
`NO-SOURCE`; this is not a claim that every printed task executed work.

## Environment and signing

The existing pins remain Gradle 8.11.1, AGP 8.10.1, Kotlin/Compose plugin 2.2.21,
Rust 1.93.1, SDK platform 36, Build Tools 35.0.0 and NDK 29.0.14206865.
This run selected the installed JDK 21 and Python 3.14. All checkout, build,
project-cache, Cargo/Gradle/Android-user, temporary and recovery outputs use D:.
Installed tools and the existing debug credential remain in their installed
locations. No global tool settings or credentials were changed.

The command inherited four complete process-local project properties through
`ORG_GRADLE_PROJECT_`: `android.injected.signing.store.file`,
`android.injected.signing.store.password`, `android.injected.signing.key.alias`
and `android.injected.signing.key.password`. No signing values appear in the
public command or captures. Kotlin compilation was process-local in-process,
and Java toolchain auto-download was disabled.

Compatibility was checked before execution against the
[official AGP 8.10.1 source JAR](https://dl.google.com/dl/android/maven2/com/android/tools/build/gradle/8.10.1/gradle-8.10.1-sources.jar),
the actual cached AGP classes, and the
[pinned Gradle environment-property loader](https://raw.githubusercontent.com/gradle/gradle/v8.11.1/subprojects/core/src/main/java/org/gradle/initialization/properties/DefaultProjectPropertiesLoader.java).
Gradle preserves dots in property names. All four signing fields are required:
an incomplete group permits AGP's default fallback and must not be used here.
A complete group selects `externalOverride` before DSL/default signing for both
app and AndroidTest. Its missing-store path fails instead of creating a default
key. Optional store type was not guessed. The existing key binding matched
before/after; both fixed D: default-key paths remained absent. No key was copied
or generated. The independent artifact reader examined public certificates,
not private key bytes.

## Newly built artifacts and independent review

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Product APK | 27,739,312 | `7ac3c6f9471ccc89975e5ad3d342e5028377895eb67723d2ea0294f80b3e9608` |
| Test APK | 2,200,091 | `29955f526518dc034fbcaad250bee95e6c6211ea8d9e70838cc91d4bf515346a` |

The packages are `org.locallore.app.archiveverify` and its `.test` package.
The test's sole permission is `android.permission.REORDER_TASKS`.
The verified common certificate SHA-256 is
`17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564`.
The newly built APK bytes equal B17's preserved pair. The fresh directory,
compilation logs and task execution establish this build; equality does not
mean old outputs were reused or qualify any earlier unrun Android test.

Root and a separate read-only reviewer independently compare each ABI's
release/generated/merged library bytes, then its stripped library against the
APK member. Both chains match. ELF machines are 62 and 183 respectively;
the actual product audit checks the existing 16 KiB alignment rules.
No separate strip-command execution trace is claimed.

The reviewer parses the actual test DEX: `OriginalStoryInputDialogTest` is
absent from the product, present as a public concrete test class, and has the
exact three public no-argument void JUnit methods from the frozen source.
These scripted Compose journeys are **compiled and packaged, still unrun on
Android**. Public certificate DER digests extracted independently from both
APKs agree with the real pair CLI's cryptographic verification.

One initial file-reader assertion incorrectly required each selected task line
to occur exactly once. Gradle prints the Kotlin AndroidTest compile line twice.
That reader failure is preserved; the corrected reader checks nonempty bare
task lines without inventing unique log occurrences. No build/product test
failed, no assertions in repository tests changed, and no build rerun occurred.

## Source preservation and limits

Exact executed source is retained as 2,299 raw files / 32,014,064 raw bytes,
10,253,850 compressed bytes; archive SHA-256
`d59efe5c8d58ddcb73751a6fb55d2896145b16d174086f6144bc526b5ec4df89`.
Manifest SHA-256:
`4d24e5362959ddc92c764b9c402944c8aa94a9ec2046996147a4f4202d8513dd`.
Every original and ZIP member was reread. Git-normalized history does not
substitute for these executed raw bytes.

Scripts, original captures, static source/class proof and review records remain
under `D:\Dev\Experiments\LocalLore\2026-10-30-public-android-gate-v1`.
Selected recovery uses the matching `D:\Dev\Recovery\LocalLore` root; final
ticket handoff records copy/ZIP/bundle seals and independent readback. The
fresh generated build remains in its worktree; caches, previous packets,
guest state and failed captures are not deleted. Recovery is selected evidence,
not a backup of every ignored/generated byte.

The original expected growth was 1–3 GiB, with an 8 GiB packet budget including
two source trees, build outputs, temporary/cache growth and selected recovery.
Shared before/after aggregate observations show Cargo, Android-user and temp
totals unchanged and Gradle net growth 100,747 bytes. These observations do not
attribute concurrent changes or establish exclusive peak allocation; no OS
quota claim is made. Exact retained totals are recorded in the final handoff.

No phone discovery, ADB/service, emulator, model, instrumentation execution,
outbound-traffic experiment, offline gameplay, physical/ARM64 execution,
system-setting, merge or release action occurs. M10.03 remains unchecked.
The next runnable host check is the ordinary-package public Android gate in a
separate bounded fresh packet; compiled UI journeys and runtime qualification
still require separately authorized target admission.
