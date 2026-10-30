# Original-story Compose input journeys — 2026-10-30

Refs #13 (M09.06, supporting M09.02); #14 (supporting M10.02/M10.03).
[Draft PR #284](https://github.com/OptimumAF/LocalLore/pull/284) remains unmerged.
This packet is stacked on unmerged [PR #282](https://github.com/OptimumAF/LocalLore/pull/282)
at `e808c9ab204690cbe177977f192b9dfcd777112b`. The owner chose to continue
without the phone. No Android target, service or emulator is operated here.
The new instrumented journeys remain **unrun** until separately admitted.

## Changes

`OriginalStoryInputDialogTest` mounts the actual dialog and controller with an
explicitly SCRIPTED counting gateway. The fixture opens the form; the tested
edits, additions, generation, review and Cancel use rendered UI controls. It
never confirms Create and throws if the creation gateway is reached.

The three original methods cover:

- Player/cast and cast/cast names differing only in case: disabled Generate,
  visible warning, no gateway calls; correction enables one generation. A
  post-generation character edit makes the draft invalid again, and Cancel
  must close it with one cancellation and no review or creation.
- Individually valid fields whose combined encoded input exceeds 4,096 bytes:
  text remains visible, Generate stays disabled, and shortening the premise
  permits one generation without dropping the other descriptions.
- A valid small generated world followed by 18 actual field edits: the encoded
  proposal exceeds 8,192 bytes and Review stays disabled. Shortening its eight
  facts enables one review. Create is displayed but never selected.

Counters and controller state are observed on the main thread, waits are
bounded, and cleanup disposes the controller and cancels its scripted scope.
These tests do not establish JNI cleanup, canonical commits or model quality.
No gameplay predicate, parser bound, dependency, provider or consent changes.

The manifest auditor also admits the exact existing
`org.locallore.app.archiveverify` package used by the Gradle archive profile.
The single literal addition retains exact package, SDK, permission-owner and
signature protection checks. It introduces no prefix or arbitrary-package
acceptance, permission relaxation, profile or public CLI flag.

## Original evidence and review

Independent original archive-policy tests were committed at `c04a637e` before
the allowlist change. On unchanged production they execute **2 methods,
1 assertion failure, 0 errors/skips**: the existing profile is refused with
`Unreviewed app package`. The normal-package control and ten unsafe variants
are rejected or accepted as intended. The owner closes cleanly in 262 ms and
all 2,291 raw source files remain stable. Result SHA-256:
`b2f7bd1c27d1a1c6fb906cdbbc1fcd8364293412816f45182fa065947467216a`.

After the one-literal fix, the unchanged original two methods plus all 31
existing APK-auditor methods execute **33 unique tests, 0 failures/errors/skips**.
The 60-second owner closes cleanly in 1,524 ms; all 2,292 raw source files stay
unchanged. Result SHA-256:
`5fa8a0204410c5bd479b39df5c444dc33881779590ce88841fb8c433a3d4f024`.

The original Compose source at `44382396` contained a two-codepoint mojibake
premise, exceeding the individual limit before reaching its aggregate witness.
Source review caught it before compilation or device execution. The final
literal is ASCII Kotlin `"\u00e9".repeat(1024)`: 1,024 scalars / 2,048 UTF-8
bytes. The final file differs from the original only by that literal, SHA-256
`01ccda0bc139ae16c8e091ff85dc65774f6cad0f7394bbfba4f9323ca75ef4f2`.
An intermediate unrun edit was reverted after inspecting the controller's
world-character-to-input-cast synchronization. All source commits are retained;
neither source correction is claimed as a runtime failure or pass.

Independent review confirms the actual UI transition paths, indexed unique
aggregate fields, main-thread observations and single-cancel source path.
Review of the fixed build recipe found no concrete blocker; that source review
does not replace executing Gradle, artifact checks or instrumented tests.

## Frozen offline build

Executed source is `84e9bfcea0c678959f52a4c1a8243e1ec8ae8639`: 2,292 tracked
raw files, with 996 entries in the declared build-input prefix map. Later
report/provenance documents are separate from this executable checkpoint.

The existing pinned stack is Rust 1.93.1, Java 21.0.4, Gradle 8.11.1,
AGP 8.10.1, Kotlin/Compose plugin 2.2.21, SDK platform 36, Build Tools 35.0.0
and NDK 29.0.14206865. This packet changes none of those versions. The current
[AGP compatibility table](https://developer.android.com/build/releases/agp-8-10-0-release-notes)
lists API 36, Gradle 8.11.1 and Build Tools 35.0.0;
[Gradle's versioned table](https://docs.gradle.org/8.11.1/userguide/compatibility.html)
supports Java 21, and the
[Kotlin plugin table](https://kotlinlang.org/docs/gradle-configure-project.html)
includes this Gradle/AGP pair for 2.2.21. This is build compatibility, not a
new model/runtime selection or physical-device qualification.

The first actual offline attempt is retained as failed. Gradle stops at
`lintAnalyzeDebug` because five exact existing analyzer dependencies are absent
from the cache. Both Rust release targets and product Kotlin/Java compilation
complete; no JVM test execution, Android-test compilation, APK packaging or
artifact audit is reached. The owner exits with worker 1 after 188,664 ms,
with known capture/cleanup and all 2,292 source/tool pins unchanged. The helper's
later `report_count_cap` exception reflects absent JVM XML, not a product test
failure; the original chained Gradle failure and stderr remain retained.

The repair provisions only those five fixed existing tool artifacts through a
separate bounded Maven Central setup, then returns the application build to
offline mode. Versions and app dependencies are unchanged. Official POMs and
the Commons Codec parent chain identify Apache-2.0 licensing (seven documents,
116,243 bytes); exact artifact hashes and the actual analyzer classpath are
recorded separately. This setup is build-tool provisioning, not model download
or installed gameplay network access.

Actual provisioning closes cleanly in 7,229 ms, resolves exactly five JARs /
13,116,731 bytes, and observes 13,331,354 bytes of shared Gradle-cache growth.
That observation is not exclusive attribution or a measured HTTP byte count.
The standalone setup uses 120/180-second command/owner bounds, with a 64 MiB
selected-artifact cap and 128 MiB growth allowance. The original application
source and tool pins remain unchanged. The public
[tool provenance record](COMPOSE_INPUT_LINT_TOOL_PROVENANCE_2026-10-30.json)
contains exact coordinates, hashes, official POMs and licensing sources.

The repaired application build returns to **offline** mode and runs
`:app:buildRustAndroid --rerun` explicitly, followed by
`:app:cleanTestDebugUnitTest :app:testDebugUnitTest :app:lintDebug
:app:recordArchiveLintMetadata :app:cleanPackageDebug
:app:cleanPackageDebugAndroidTest :app:compileDebugAndroidTestKotlin
:app:assembleDebug :app:assembleDebugAndroidTest`.
The existing `localLoreArchiveVerification=true` profile is used. The fixed
recipe also sets no-daemon/no-build-cache, two workers, disables SDK/toolchain
downloads, uses the external D: project cache and in-process Kotlin compiler,
and routes TEMP/TMP/TMPDIR and project/cache outputs to D:. The existing debug
signer is read in place; no key is copied or generated.

The actual repaired owner closes **PASS in 90,246 ms**, worker 0, with complete
capture/cleanup and empty owner streams. The nested command ceiling remains
600 seconds and the owner ceiling 1,260 seconds. Gradle reports success in
1m21s (85 tasks: 55 executed, 30 up to date). All 2,292 raw source and bound
tool pins remain stable. Result SHA-256:
`311daf147d23457e245903daffcb7c8e494dcc3c7afca110a31707bd2f276b84`.

- **JVM:** 332 unique executed methods / 39 XML suites, zero failures/errors/
  skips; exact unfiltered source-method roster matches. The test task executes,
  and all eight original #282 input regressions pass unchanged.
- **Lint:** analyzer 31.10.1 actually does work, with zero errors/fatal issues
  and one version-availability warning for the unchanged coroutines 1.10.2 pin.
  All five provisioned JAR hashes match the actual same-job analyzer classpath.
  This ordinary profile has `checkDependencies=false`; it is not a full
  dependency-lint gate. The existing nullable-Boolean unit-test compiler warning
  is also retained; nothing is suppressed for this packet.
- **Instrumentation compilation/package:** all three new methods are public,
  annotated, no-argument void DEX definitions in the test APK and absent from
  the product APK. This verifies packaging, not their runtime assertions.
- **Native:** the JNI task executes with both target markers. Cargo may reuse
  its cache. Release, generated and merged library hashes match for x86_64 and
  arm64-v8a; the stripped files match both actual APK entries. Native ABI and
  16 KiB alignment checks pass. The installed strip tool is bound, but Gradle
  supplies no separately captured per-strip command receipt. Cross-compilation
  is not Android or ARM64 execution.
- **APK policy:** original AAPT/signature captures pass exact product/test
  packages, SDKs, signer pair, test runner/target, backup resource/rules and
  receipt-service checks. Product permission is only its scoped signature
  receiver permission; test permission is REORDER_TASKS. No INTERNET permission.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `org.locallore.app.archiveverify` product APK | 27,739,312 | `7ac3c6f9471ccc89975e5ad3d342e5028377895eb67723d2ea0294f80b3e9608` |
| `org.locallore.app.archiveverify.test` test APK | 2,200,091 | `29955f526518dc034fbcaad250bee95e6c6211ea8d9e70838cc91d4bf515346a` |

APK audit SHA-256:
`54f136924b7417436736f48baf29ddf52aebd1b7ba80978b924609012069fa75`;
native join record:
`c532b69f8b39c943c4a63c5b2d2d6032589bf60f52b361cf7b57bfb9be586c9e`.

Independent closed-file review replays the actual 39 XML reports, source/ZIP,
command/task evidence, APK ZIP/AAPT/DEX policy, both ABI chains and all five
lint-provision joins. It passes in 7.499 seconds, reading 2,393 inputs /
274,978,611 bytes, without running SDK tools, native code, tests or a target.
Receipt SHA-256:
`5e214b94a8a091309f2906e6bba052b20d0ff47e55c5994690b3f298c9bd0e1e`.
Its first checker refuses the known Cargo hardlink assumption; that failed
receipt and unrun intermediate draft are retained. The corrected checker
admits only the exact two release/deps same-inode pairs and retains all other
file, roster, byte, hash and size checks. It does not recapture or rerun the
application. Root separately parses the actual XML, lint and APK receipts.

## Limits and handoff

The three new Compose methods are compiled and packaged but are not executed
in this packet. Touch, keyboard/scroll behavior,
accessibility, lifecycle stress, physical performance, ARM64 execution and real
model inference remain unqualified here. The Rust cross-build is not an ARM64
device result. Existing historical cohorts retain their original attribution.

M09.06 and supporting M09.02/M10.02/M10.03 slices are in review. Full task
checkboxes and owner acceptance stay open. No merge,
release, model or SDK installation, system setting change or private upload occurs.

All new sources, scripts, captures, outputs and selected recovery live on D:.
The packet's declared total cap is 8 GiB, expected 1–3 GiB, including three
source trees, generated builds, cache/temporary growth and recovery. Shared
cache contents are not bulk copied; no OS quota or exclusive peak claim.

The exact executed-source archive contains 2,292 raw files / 31,935,992 bytes,
10,224,289 compressed bytes, SHA-256
`05325281e2cc66938113b02c7f1956a3b5094c5831192fc2c2a47454ab90d8e4`.
Manifest SHA-256:
`9cbc9c810ab47794a031d1e48f796ed543da00f2f4792bf759b8307cbef32774`.
Root independently compares every original and ZIP member to the actual build
request. Git-normalized blobs do not replace these raw executed bytes.

First-attempt native outputs are preserved before the repaired build. The
initial preservation helper refused Cargo's release/deps hardlink pair before
copying any file. Its failed receipt is retained. The corrected read-only
copy admits only the exact proven same-inode pair, retains all path/held-file
stability and hash checks, and copies all four release/generated libraries /
45,065,504 bytes. This is a copy-helper assumption correction, not artifact
corruption, a Rust failure or a weakened product boundary test.
Original scripts, failed/fixed captures, source archive, native copies and APKs
remain under `D:\Dev\Experiments\LocalLore\2026-10-30-original-input-compose-v1`.
Selected recovery uses the matching
`D:\Dev\Recovery\LocalLore\2026-10-30-original-input-compose-v1` root. The final
ticket handoff records exact copy/ZIP manifest seals, independent readback and
measured scope totals after preservation closes. It includes the three named
B17 source branches and report checkpoint, not unrelated Git refs.

The declared Gradle project caches and the original generated archive build
remain in place, with metadata-only retention records. Existing global caches
are not duplicated. This is not a claim that every ignored/generated byte was
backed up. Sources, failures and recovery are not deleted or retired.

Next runnable host work: M10.03 supporting CLI selection for this existing
archive-profile audit, with default/unknown/mutually-exclusive option tests
and the preserved APKs. The current public CLI has no archive selector; this
packet calls its existing pure auditors with the exact admitted package.
Running these three UI journeys still requires a separately approved Android
target and admission. Full task criteria remain required.
