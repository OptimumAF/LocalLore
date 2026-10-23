# LiteRT-LM Android experiment: sources and compatibility

Checked 2026-10-22 for M01.02. This is a development experiment, not a production
dependency decision or completed physical-device feasibility gate.

The exact [Google Maven metadata](https://dl.google.com/dl/android/maven2/com/google/ai/edge/litertlm/litertlm-android/maven-metadata.xml)
identifies `0.18.1` as latest/release, last updated `20261020175555`. The pinned
[v0.18.1 source](https://github.com/google-ai-edge/LiteRT-LM/tree/bda624851d74be34d4e1f7fac1fc4155939539c7)
is the same runtime revision used by the host spike. The
[official Kotlin guide at that revision](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/docs/api/kotlin/getting_started.md)
documents Google Maven, explicit Engine/Conversation ownership, CPU selection,
background initialization, callbacks, and disabling automatic tool calling.
Its `latest.release` example is replaced with an exact experiment pin.

| Actual publisher artifact | Bytes | SHA256 |
|---|---:|---|
| [Android AAR 0.18.1](https://dl.google.com/dl/android/maven2/com/google/ai/edge/litertlm/litertlm-android/0.18.1/litertlm-android-0.18.1.aar) | 20,905,360 | `05c6bdc8acda834efcca12c0ad5d06d2cd8c83e60770f056d8d222f699f3012b` |
| [Android POM 0.18.1](https://dl.google.com/dl/android/maven2/com/google/ai/edge/litertlm/litertlm-android/0.18.1/litertlm-android-0.18.1.pom) | 1,543 | `3d6ea70f41bc6305c5985a52c5f5d00da97402d6531c9a395f3145cb5c1a89a5` |
| Embedded `classes.jar` | 191,250 | `0ff0098f64407752c115bf2569a7cd3005c894ecb934e7fdbcd744037f398ce8` |
| Embedded ARM64 JNI library | 22,155,680 | `cf4c55139c6fc86425ecfe75f8a907e6193ca665ecc19fbabcaba7ab361bdc43` |
| Embedded x86_64 JNI library | 26,353,160 | `ba879b2b46be1f7e08df8c8365a276cfc54c1e21383090e058a24f25e603cdd7` |

The [machine-readable artifact audit](LITERT_ARTIFACTS_2026-10-22.json) records
the inspected bytes, not just upstream build configurations. Both supported
ABIs are present. Both ELF Android identification notes specify API 26,
NDK r29/build 14206865; the manifest says API 24. The experiment conservatively
uses API 26 and makes no claim that API 24 can load these native libraries.
Every inspected ELF LOAD segment has 16 KiB alignment. These facts do not prove
ARM64 execution or operation on a 16 KiB-page Android OS.

The AAR manifest contains no requested permission, service, provider or activity.
Native `DT_NEEDED` names are Android platform libraries: `libandroid`, `libz`,
`libGLESv2`, `libEGL`, `libGLESv3`, `liblog`, `libdl`, `libm`, and `libc`.
The CPU experiment does not request optional GPU/NPU vendor libraries.

The POM declares Gson 2.14.0, kotlin-reflect 2.4.0 and
kotlinx-coroutines-android 1.11.0. The resolved closure is version-locked in
the isolated app's `gradle.lockfile`; exact POM/module/JAR/AAR identities and
declared license names are retained in
[dependency evidence](LITERT_DEPENDENCIES_2026-10-22.json). No Kotlin compiler
plugin or production dependency is changed. The classes' major version is
**65 (Java 21)**. Actual JDK 17 compilation failed with `wrong version 65.0,
should be 61.0`; merely choosing Java source syntax cannot fix that gate.

The coordinator authorized the already installed Oracle JDK 21.0.4
(`21.0.4+8-LTS-274`) as this experiment's compiler only, targeting Java 17.
The build daemon remained on the existing Android Studio JBR 17.0.6. Gradle's
[8.11.1 compatibility matrix](https://docs.gradle.org/8.11.1/userguide/compatibility.html)
supports Java 21 toolchains (since 8.4). Android's
[Java toolchain guidance](https://developer.android.com/build/jdks) separates
the compiler toolchain from the daemon JDK and Android runtime APIs.
[AGP 8.10 compatibility](https://developer.android.com/build/releases/agp-8-10-0-release-notes)
requires Gradle 8.11.1/JDK 17 and supports SDK 36. The actual Java 21 compiler,
D8 and debug APK assembly passed with the exact SDK; no bytecode was rewritten.
Automatic JDK downloads and SDK installation are disabled.

**Lint limitation:** AGP 8.10.1's embedded Kotlin analyzer reports metadata
2.4.0 versus expected 2.1.0 for SDK/stdlib/reflection modules. The Java-only
application compiles and D8 packages them, and the final lint issue report says
`No issues found`, but dependency analysis is incomplete. The build helper
returns exit 2 when those diagnostics occur. No suppressed check, older SDK,
production toolchain upgrade or full analyzer-compatibility claim is used.

The publisher POM and upstream first-party source declare Apache-2.0. The AAR
includes `LICENSE` (SHA256 `ec40a2da15ab0e8b44a9f787ab210203d3cad32572f5f99744a88eb90ff9ba4e`)
and a 2,198,164-byte `THIRD_PARTY_NOTICE.txt` (SHA256
`52a70c82685debf85d4ea9d677615b8636ffd3b75435ce71f247bf5982fb2ba2`).
That aggregate notice contains multiple license families and components;
it is not evidence that every listed component is linked into both binaries,
nor blanket Apache licensing for every included component. This source-only
experiment redistributes no SDK binary, APK or weights. Production redistribution
still requires a component/notice obligations review. Test-only JUnit 4.13.2
declares EPL-1.0, Hamcrest 1.3 BSD; runtime Kotlin/Gson/coroutines/annotations
POMs declare Apache-2.0.

Missing/corrupt model checks deliberately pass fixed synthetic paths into the
actual SDK. The pinned
[Conversation implementation](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/Conversation.kt)
warns cancellation does not roll internal state back. The experiment therefore
drains the terminal callback, returns from native close, and creates a new
engine/conversation for reload. Kotlin exposes benchmark counts and template
rendering but no public `Engine.tokenize`; no host API parity is inferred.
