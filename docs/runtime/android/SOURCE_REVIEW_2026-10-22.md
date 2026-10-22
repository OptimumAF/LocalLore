# Independent Android runtime source review

Scope: M01.02 development experiment, supporting M01.03/M01.05 preparation.
The reviewer read the current #3/#5 tickets and claim 6353871377, AGENTS.md,
the evaluation protocol and prior host evidence. This review introduces no
production dependency and selects no Android backend or supported phone.

The accompanying [JSON record](SOURCE_REVIEW_2026-10-22.json) records 16
independently retrieved official source/metadata URLs, byte lengths and SHA256
digests. All retrievals succeeded. Runtime commits remain LiteRT-LM
`bda624851d74be34d4e1f7fac1fc4155939539c7` and llama.cpp
`620d2225cc436ab0b001e3200e590e3b286ef9ab`. These are the existing host-spike
pins; no silent runtime upgrade was made.

## Compatibility boundaries

- The pinned [llama.cpp Android guide](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/docs/android.md)
  documents NDK cross-compilation, an ARM64/API 28 example and adjustable ABI.
  Its portable configuration disables host-native tuning, OpenMP, llamafile
  and OpenSSL. The experiment must verify the actual output ELF, dependencies
  and target CPU flags; an example command is not execution evidence.
- Android's [ABI documentation](https://developer.android.com/ndk/guides/abis)
  requires one explicit ABI per CMake build. Optional AVX and newer ARM
  instructions cannot be assumed from the baseline ABI. Cross-built ARM64
  output is distinct from ARM64 execution; x86_64 emulator success cannot
  qualify a phone.
- LiteRT-LM's pinned [native build guide](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/docs/getting-started/build-and-run.md)
  recommends prebuilt SDKs for app developers and documents NDK r28b or newer
  for its Android source example. Its [.bazelrc](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/.bazelrc)
  defines both ARM64 and x86_64 configurations. Source configurations do not
  establish which ABIs a published AAR contains.
- The pinned [Kotlin guide](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/docs/api/kotlin/getting_started.md)
  identifies `com.google.ai.edge.litertlm:litertlm-android`. The experiment must
  use an exact version rather than its illustrative `latest.release`.
  [Engine source](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/Engine.kt)
  requires explicit initialization/close; loading belongs off the UI thread.
  Conversation lifetime and active-stream completion must precede engine
  disposal. Declaring AutoCloseable alone is not a cancellation test.

## Maven metadata checked independently

Google Maven's [version metadata](https://dl.google.com/dl/android/maven2/com/google/ai/edge/litertlm/litertlm-android/maven-metadata.xml)
reported latest/release `0.18.1`, last updated `20261020175555`. The exact
[0.18.1 POM](https://dl.google.com/dl/android/maven2/com/google/ai/edge/litertlm/litertlm-android/0.18.1/litertlm-android-0.18.1.pom)
is 1,543 bytes, SHA256
`3d6ea70f41bc6305c5985a52c5f5d00da97402d6531c9a395f3145cb5c1a89a5`.
It declares Gson 2.14.0, kotlin-reflect 2.4.0 and coroutines-android 1.11.0.
The production app's Kotlin 2.2.21 compiler must not be assumed compatible
with newer library metadata. An isolated Java SDK harness can exercise public
JVM overloads without claiming that a production Kotlin upgrade was tested.
The runtime agent owns actual AAR/ELF and executable build evidence.

The reviewer subsequently read the runtime agent's already downloaded AAR
without another binary download. Its 20,905,360 bytes hash to
`05c6bdc8acda834efcca12c0ad5d06d2cd8c83e60770f056d8d222f699f3012b`.
Independent ZIP/ELF parsing found exactly ARM64 and x86_64 JNI libraries;
both machine IDs and byte hashes match the runtime agent's report. All three
PT_LOAD segments in each library have 16,384-byte alignment. The manifest
declares minSDK 24 with no permissions/components; both Android ELF ident
notes record API 26. The ident is a build-target observation, not a measured
minimum supported OS. API 24/25 compatibility and actual 16 KiB OS execution
remain untested. ELF alignment also does not establish a future APK's ZIP
alignment or successful native loading. Exact aggregate values are in JSON.

The runtime [LiteRT-LM license](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/LICENSE)
and POM state Apache-2.0; the pinned
[llama.cpp license](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/LICENSE)
is MIT. Neither statement grants blanket redistribution rights to every
transitive vendor binary or model. Preserve the existing helper's MIT
adaptation notice. Existing model license/provenance evidence remains in the
host-spike source report; weights are not published by this experiment.

No phone, emulator, SDK binary or model was downloaded or executed by the
reviewer for the source retrieval recorded here. An SDK build, model load,
16 KiB alignment and measured process cleanup require separate actual
evidence. A Maven release number alone does not prove that its AAR was built
from the reviewed source commit.
