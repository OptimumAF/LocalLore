# Standalone Android llama.cpp cross-build

This M01.02 development experiment compiles the existing bounded
[C++ API helper](../../llama/main.cpp) and the existing Rust `runtime_spike`
example unchanged. It adds no production runtime, JNI API, model downloader,
app permission or Kotlin rules. Coordinator-owned scripts perform device
process ownership and actual emulator checks separately.

The source checkout is read-only and must match llama.cpp
`620d2225cc436ab0b001e3200e590e3b286ef9ab` (v0.7.0), with no tracked or untracked
changes. Pin/review its MIT license and the existing helper's
[attribution](../../llama/NOTICE) before provisioning the checkout. Build outputs
and model weights are ignored and must not be committed.

Use the already installed Windows Android SDK, NDK `29.0.14206865`,
CMake/Ninja `3.22.1`, Python 3.9+ and Rust `1.93.1` with
`x86_64-linux-android` and `aarch64-linux-android` installed. Run from the
repository root, substituting the path to your reviewed local source checkout:

```powershell
python benchmarks/spike/android/llama/build.py --source ../LocalLore-llama-spike/target/runtime-spike/llama.cpp --sdk "$env:LOCALAPPDATA/Android/Sdk"
python -m unittest discover -s benchmarks/spike/android/llama -p 'test_*.py' -v
```

No command installs an SDK, fetches sources, downloads a model, invokes ADB or
executes an Android binary. `--abi x86_64` or `--abi arm64-v8a` selects one build;
the default builds both sequentially. `--build-dir` selects an output directory
(default `target/android-runtime/llama`). CMake uses the NDK toolchain, API 28,
static libc++, CPU only, no native host tuning, and no OpenMP, llamafile,
dynamic backend, SSL, server or accelerator. Optional x86 SSE4.2/AVX/FMA/F16C/
BMI2/AMX flags are disabled; ARM64 uses baseline `armv8-a`. CMake's dependency
fetching is disconnected. The upstream HTTP utility remains compiled in
`llama-common`, but the helper exposes only a local file API and no network
entry point. This is not a whole-runtime networking certification.

The Rust build reuses the existing response-file linker adapter, preserving
workspace apostrophes and SDK spaces. Cargo uses `--locked --offline`; it
cannot install targets. Both linkers request 16 KiB maximum page alignment.
The script inspects actual output bytes: matching ELF64 machine, ET_DYN plus
DF_1_PIE, `/system/bin/linker64`, every LOAD alignment and virtual/file offset
congruence at 16 KiB, and only reviewed system shared libraries. It emits a
sanitized size/hash/dependency report per ABI. ELF alignment is build evidence,
not execution on a 16 KiB OS or ARM64 hardware.

Outputs for each ABI:

- `target/android-runtime/llama/<abi>/host-helper/locallore-llama-spike`
- `target/android-runtime/llama/rust/<rust-target>/release/examples/runtime_spike`
- `target/android-runtime/llama/<abi>-elf.json`

See [dated build evidence](../../../../docs/runtime/android/LLAMA_BUILD_2026-10-22.md)
for exact results, source references and limitations. The actual runtime/model
acceptance gates remain on [M01 #5](https://github.com/OptimumAF/LocalLore/issues/5).
