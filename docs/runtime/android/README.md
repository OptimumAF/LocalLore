# Isolated Android runtime experiment

M01.02 with supporting M01.03/M01.05 preparation. This is development tooling,
outside the Compose application. Both candidate runtimes use local model files
and the existing Rust oracle on two Android15/API35 x86_64 emulators. No backend,
phone tier, prose quality or production minimum OS is selected.
Python on the development host orchestrates ADB and transient IPC; inference and
the Rust oracle execute on the emulator. A standalone gameplay adapter remains
future work.

The [dated verification](VERIFICATION_2026-10-22.md) and
[all-attempt aggregate results](RESULTS_2026-10-22.json) distinguish successful
turns, cancellation, expected rejection, uncertain cleanup and follow-up checks.
The original Qwen3.5-4B conversion and M01 physical-device gate remain pending.

## Build explicitly

Use the existing pinned Rust1.93.1, NDK29.0.14206865, SDK36/BuildTools35,
CMake3.22.1, JDK17 and cached Gradle8.11.1 dependencies. LiteRT's isolated Java
compiler additionally needs an already installed JDK21. The official AAR is
classfile65; the production Kotlin/Java toolchains are unchanged.

```powershell
python scripts/check.py host --offline
python benchmarks/spike/android/controller/build.py --sdk $env:ANDROID_HOME
python benchmarks/spike/android/llama/build.py --sdk $env:ANDROID_HOME --source <pinned-llama-source>
python benchmarks/spike/android/litert/build.py --java21 <existing-jdk21> --offline
```

The llama source must be exactly `620d2225cc436ab0b001e3200e590e3b286ef9ab`.
Build scripts do not download it, install SDKs, operate devices or load weights.
The isolated LiteRT project pins a newer, separately audited analyzer while
retaining AGP and the production toolchain. Its normal build now returns zero
only after assembly/D8, fourteen JVM tests, APK checks and actual SDK/Kotlin
dependency analysis pass. `--probe-incompatible-analyzer` deliberately uses the
original analyzer and must return **2** for its reproduced metadata failure.
See [analyzer compatibility and limitations](LITERT_ANALYZER_2026-10-22.md),
[SDK sources/build](LITERT_SOURCES_2026-10-22.md) and
[native build](LLAMA_BUILD_2026-10-22.md) for exact pins, hashes and licenses.
No model weight, compiled runtime or APK belongs in Git.

## Run only on authorized targets

Choose one authorized target and repeat on the second. The controller requires
an explicit `--serial` argument; use its local transport ID, never publish it.
Install only the source-built isolated SDK APK, selecting the target explicitly:

```powershell
adb -s <authorized-target> install -r -t benchmarks/spike/android/litert/app/build/outputs/apk/debug/app-debug.apk
```

The model files must match the publisher hashes recorded by the
[host spike](../spike/README.md). Set local paths for these arguments:

```powershell
python benchmarks/android_runtime_spike.py --runtime llama --adb <adb> --serial <authorized-target> --owner target/android-runtime/controller/remote-owner-x86_64 --binary target/android-runtime/llama/x86_64/host-helper/locallore-llama-spike --oracle target/android-runtime/llama/rust/x86_64-linux-android/release/examples/runtime_spike --model <verified-qwen-gguf> --output target/android-llama.json
python benchmarks/android_runtime_spike.py --runtime litert --adb <adb> --serial <authorized-target> --owner target/android-runtime/controller/remote-owner-x86_64 --binary unused --oracle target/android-runtime/llama/rust/x86_64-linux-android/release/examples/runtime_spike --apk benchmarks/spike/android/litert/app/build/outputs/apk/debug/app-debug.apk --model <verified-gemma-litertlm> --output target/android-litert.json
```

`--cancel-after 3` exercises parent-requested process termination and requires a
fresh run afterwards. `--case spent` / `--case unlearned` stop at Rust preflight
before model provisioning or generation. For SDK-specific checks, use
`--sdk-mode metadata`, `missing`, `corrupt` or `cancel`. The latter waits for a
real streaming callback, cancels, drains the terminal callback, closes both
owners and reloads a fresh engine; it is a separate API check, not a story turn.
The SDK may report `generation_failed` for an oversized context; no tokenizer
preflight API is invented. Current CLI process status and `worker_status` are
separate fields; a completed diagnostic process can report an expected model error.

The first valid request copies/hashes files only into the owned benchmark
directory or the isolated package's private files. Gemma provisioning streams
binary bytes through `adb exec-in`, verifies the full device SHA256, then renames
the private staging file. Transfer output is discarded; no model bytes enter
Python memory or public logs. Existing mismatched cache/package identities fail
closed. Provisioning reserves at least 1GiB free storage; do not exhaust a device
to simulate failure. The coordinator removed its verified Qwen cache before
provisioning the larger Gemma model. The benchmark APK and private Gemma files
remain on the two selected emulators for subsequent explicit experiments.

## Exercise control failures without inference weights

Install the exact source-built isolated SDK APK first, then run explicitly:

```powershell
python benchmarks/android_control_probe.py --adb <adb> --serial <authorized-target> --owner target/android-runtime/controller/remote-owner-x86_64 --oracle target/android-runtime/llama/rust/x86_64-linux-android/release/examples/runtime_spike --apk benchmarks/spike/android/litert/app/build/outputs/apk/debug/app-debug.apk --output target/android-control.json
```

Repeat on the second authorized target. This issues actual native/SDK operations
and six deliberately injected host-control failures, checking fail-closed results
and fresh recovery; three additional corrupt-file SDK diagnostics need no model
weights. Every attempted check is retained before recovery. Successful fault
assertions are not successful generations. No ADB invocation enters default
checks. The [control verification](CONTROL_VERIFICATION_2026-10-22.md) preserves
the earlier unexplained transients separately from this follow-up.

## Bounds and authority

The native [process owner](../../../benchmarks/spike/android/controller/README.md)
owns/reaps one trusted direct child. An ADB-client exit is never native cleanup
evidence. Package termination is limited to the hash-verified isolated SDK app;
its reviewed manifest/runtime uses a single process and threads, not arbitrary
descendants. Unknown or disconnected cleanup remains unverified. Do not reuse
this controller as a sandbox for arbitrary programs.

Every role uses a fresh process/engine. One model is active at a time; a warm
shared-model turn is not tested. Director<=350/narrator<=220 tokens, 4096 context,
four CPU threads and the shared 60-second turn budget are development limits.
Hashing/provisioning are outside inference timing; OS file cache and host load
are uncontrolled. Independent native/Java watchdogs bound abandoned work, but
an uninterruptible kernel task cannot promise graceful reclamation.

Only an accepted director proposal reaches the narrator. Rust on the emulator
checks exact narration, commits one event, retries idempotently and verifies
recipient/absent-observer context. Oracle processes reconstruct an ephemeral
fixture, so this is no durable or Compose-integrated inference proof. Model text
is transient IPC only; public reports contain fixed categories and numeric/bool
metadata. Default host checks use synthetic fixtures/mocks, never models or ADB.
