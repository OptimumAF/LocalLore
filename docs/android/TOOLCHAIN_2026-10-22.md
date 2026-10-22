# Android shell toolchain decision — 2026-10-22

Scope: M03.02, [ticket #7](https://github.com/OptimumAF/LocalLore/issues/7).
Official-source compatibility and direct dependency metadata were verified on
2026-10-22. This is a fake-provider shell decision, not a production model,
minimum-device, physical-phone, security-audit, distribution or release claim.
Build and emulator evidence belongs in the implementation evidence document and
ticket comments; source availability alone does not prove successful execution.

## Selected versions and compatibility

| Input | Pin | Reason and official source |
|---|---|---|
| Android Gradle Plugin | 8.10.1 | Its [release notes](https://developer.android.com/build/releases/agp-8-10-0-release-notes) support API 36 and require Gradle 8.11.1, Build Tools 35.0.0 and JDK 17. The patch fixes include a Kotlin/R8 issue. |
| Gradle | 8.11.1 | Matches that AGP minimum/default. The wrapper must pin the official distribution SHA-256, as described by [Gradle wrapper verification](https://docs.gradle.org/8.11.1/userguide/gradle_wrapper.html#sec:verification). |
| Build JVM / bytecode target | 17 | AGP's required build JVM; align Kotlin and Java targets. |
| Kotlin Android + Compose compiler plugin | 2.2.21 | Use the same version for both. The [Kotlin compatibility table](https://kotlinlang.org/docs/gradle-configure-project.html) supports Gradle 7.6.3–8.14 and AGP 7.3.1–8.11.1 for Kotlin 2.2.20–2.2.21. The cached Kotlin 2.1.21 only fully supports AGP through 8.7.2; selecting it merely because cached would exceed that tested range. [Compose setup](https://developer.android.com/develop/ui/compose/setup-compose-dependencies-and-compiler) specifies the Kotlin-version-matched compiler plugin for Kotlin 2.0+. |
| Compose BOM | 2025.05.01 | Stable dated pin; official [May 2025 announcement](https://android-developers.googleblog.com/2025/05/whats-new-in-jetpack-compose.html) and [Google Maven POM](https://dl.google.com/dl/android/maven2/androidx/compose/compose-bom/2025.05.01/compose-bom-2025.05.01.pom). Resolves UI/foundation/test 1.8.2 and Material3 1.3.2. Compiler is outside the BOM. |
| Activity Compose | 1.10.1 | Exact Google Maven POM inventoried below. |
| Lifecycle ViewModel/Runtime Compose | 2.8.7 | Exact Google Maven POMs inventoried below. |
| Coroutines Android / test | 1.10.2 | Exact Maven Central POMs inventoried below. |
| JUnit | 4.13.2 | Test-only, exact Maven Central POM inventoried below. |
| AndroidX test runner / ext JUnit | 1.6.2 / 1.2.1 | Instrumentation-only, exact Google Maven POMs inventoried below. |
| AndroidX graphics path (transitive) | 1.0.1 | Selected by Compose's resolved runtime graph; bundles native path helpers. Exact Google Maven POM inventoried below. |

The current Compose setup page recommends the latest BOM (2026.09.00 at source
verification). This bounded shell deliberately uses the smaller established
2025.05.01 set aligned with available dependencies, with explicit versions and
actual build/UI validation required. It does not claim latest-library status.
No dynamic `+`, `latest.release`, model downloader, production native runtime or
Google Play Services dependency is selected by this decision.

## SDK and distribution boundaries

Use `compileSdk = 36`, `targetSdk = 36`, Build Tools `35.0.0`, and provisional
shell-only `minSdk = 26`. API 36 is within AGP 8.10's documented maximum. The
[current Play target requirement](https://developer.android.com/google/play/requirements/target-sdk)
requires ordinary new apps and updates to target Android 16/API 36 from August
31, 2026. A debug APK installed on authorized emulators is the scope here;
targeting 36 alone establishes neither store eligibility nor release readiness.

Minimum 26 is a conservative shell floor, not a measured product support tier.
The two available targets report Android 15/API 35; testing them does not cover
API 26, Android 16 target behavior on API 36, ARM64, physical hardware or all
screen/accessibility configurations. Keep those gaps explicit. Model runtime,
ABI, RAM and minimum OS selection remain gated by M01 measurements. The pinned
[LiteRT-LM Kotlin getting-started guide](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/docs/api/kotlin/getting_started.md)
and its Maven-integration reference were inspected; no universal model/device
minimum was established from them. The shell adds no LiteRT-LM dependency.

The official [16 KB page-size guide](https://developer.android.com/guide/practices/page-sizes)
distinguishes Java/Kotlin-only apps from native-library requirements. This
shell's debug APK includes AndroidX graphics-path native helpers even though
it adds no Rust or inference runtime. See the separately scoped
[implementation review](REVIEW_2026-10-22.md) for actual APK inspection and
host alignment checks. M03.03 and any inference runtime introduce a separate
native packaging/test gate. SDK numbers alone prove no page compatibility.

## License and provenance inventory

[DEPENDENCY_SOURCES.json](DEPENDENCY_SOURCES.json) records exact source URLs,
byte counts, SHA-256 hashes, license declarations and direct dependencies for
15 pinned POMs fetched from Google Maven or Maven Central, including the native
transitive AndroidX graphics-path dependency. These are hashes of
POM metadata, not downloaded AAR/JAR checksums or a full transitive inventory.
No dependency source/sample code was copied into the application as part of
this research. LocalLore's own original code remains Apache-2.0.

The inspected AndroidX, AGP, Kotlin/compiler and coroutine POMs declare
Apache-2.0; JUnit 4.13.2 declares EPL-1.0. JUnit and instrumentation dependencies
belong only in test configurations. Confirm the resolved release/debug graphs
and preserve applicable license/NOTICE material before distribution. Gradle's
[versioned license](https://github.com/gradle/gradle/blob/v8.11.1/LICENSE) includes
its license and bundled third-party notices; Kotlin's [versioned license](https://github.com/JetBrains/kotlin/blob/v2.2.21/license/LICENSE.txt)
and coroutines' [versioned license](https://github.com/Kotlin/kotlinx.coroutines/blob/1.10.2/LICENSE.txt)
are Apache-2.0. Do not treat this metadata inventory as legal clearance for
unreviewed binaries or a vulnerability audit.

Android SDK/platform tools are development prerequisites governed by their
[SDK terms](https://developer.android.com/studio/terms) and individual component
licenses. Do not commit or redistribute the installed SDK, emulator images,
accepted-license files, signing keys, machine-local paths, caches or APKs in
this source PR. Dependencies may need network access during initial build
provisioning; gameplay must remain fully local and omit unused permissions.

## Executed research checks

- Read AGENTS, README, kickoff, issue workflow, #3/#7, initial-direction and
  host-proof ADRs, architecture, privacy, licensing and pinned M01 report.
- Fetched the 15 exact official POMs in the linked source inventory, parsed
  their XML, recorded direct dependencies/license declarations and hashed the
  returned bytes. The Compose BOM maps the selected versions listed above.
- Read current primary compatibility, compiler, SDK and Play documentation.
- Fetched the [official Gradle 8.11.1 binary distribution checksum](https://services.gradle.org/distributions/gradle-8.11.1-bin.zip.sha256):
  `f397b287023acdba1e9f6fc5ea72d22dd63669d59ed4a289a29b1a76eee151c6`.
  It matches the implementation's wrapper property at review time. This checks
  the configured expected digest, not a clean-checkout build or downloaded ZIP.
- No phone operation, model download, benchmark, native integration, release,
  merge, permission change or application test is claimed by this research.
