# Paused Android llama.cpp build experiment

M01.02 preparation, branch `research/m01-llama-android`, baseline main
`2c095ea066fe1101f756d5153e46c75f77806bd3`. The coordinator's claim is
[#5 comment 6353871377](https://github.com/OptimumAF/LocalLore/issues/5#issuecomment-6353871377).
The user subsequently redirected work to M03.03. The already-running x86_64
cross-build was allowed to finish; further runtime work is paused. ARM64 was
**not built or executed** in this packet. No emulator or phone was accessed.

## Actual checks

Run from the separate `LocalLore-llama-android` worktree:

```powershell
python benchmarks/spike/android/llama/build.py --source ../LocalLore-llama-spike/target/runtime-spike/llama.cpp --sdk "$env:LOCALAPPDATA/Android/Sdk" --abi x86_64
python -m unittest discover -s benchmarks/spike/android/llama -p 'test_*.py' -v
```

The cross-build exited 0: 136 CMake/Ninja steps linked the existing C++ helper,
then Cargo `--locked --offline --release --example runtime_spike` built the
existing Rust engine oracle for `x86_64-linux-android`. The unchanged pinned
upstream source was clean before/after. Eight synthetic source-pin/ELF tests
passed, including wrong source revision, dirty source, malformed ELF, wrong
architecture, missing PIE, 4 KiB alignment and unexpected shared dependency.
They do not test inference, cancellation or device resource ownership.

Actual tools: Windows x64; NDK `29.0.14206865` (r29), its Clang 21.0.0;
SDK CMake `3.22.1` with bundled Ninja `1.10.2`; Rust `1.93.1`; Python `3.9.12`. Android API 28,
standalone CPU executable, static libc++. No SDK/dependency/model installation
or download. The source checkout is reused read-only; no relocation or patch.
No shared engine/helper source was edited.

Actual CMake cache has OpenMP, llamafile, native tuning, SSE4.2, AVX/AVX2,
AVX512, FMA, F16C, BMI2, AMX and OpenSSL disabled. Generated compiler commands
have no `-mavx`, `-mfma`, `-mf16c`, `-mbmi`, `-msse4` or `-march=native`.
No host AVX2 assumption is carried into this x86_64 build. Upstream reports a
nonfatal missing-ccache warning; no compiler error was suppressed.

## Actual ELF bytes

The build's byte inspector and NDK `llvm-readelf --file-header
--program-headers --dynamic` agree: x86_64 ELF64, ET_DYN, DF_1_PIE,
`/system/bin/linker64`, three LOAD segments each aligned to 16384 with 16 KiB
file/virtual offset congruence. No `libc++_shared` or OpenMP shared dependency.

| Output | Bytes | SHA-256 | NEEDED |
|---|---:|---|---|
| C++ `locallore-llama-spike` | 98424480 | `f0b59c538c211e936f2c556c2b202b28d1a56d19878f9a1bf83fde6af8fd7db0` | libm.so, libdl.so, libc.so |
| Rust `runtime_spike` | 1382376 | `1b3e12e94470cea37a5ccbddeec568e9cca7c2ac723b620f0a494cd12305d228` | libdl.so, libc.so |

Ignored output locations: `target/android-runtime/llama/x86_64/host-helper/`
and `target/android-runtime/llama/rust/x86_64-linux-android/release/examples/`.
The first executable retains upstream build debug information; this is no app
size or release packaging result. Hashes identify this actual build, not a
promise of reproducible compiler bytes across machines. No binaries or weights
are committed. Source build instructions and audit tests are versioned.

## Official compatibility and license references

Verified before building against the pinned upstream source and current
official Android docs:

- [llama.cpp Android NDK instructions at the exact source revision](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/docs/android.md): Android toolchain, API 28, native tuning/OpenMP/llamafile/OpenSSL disabled.
- [Official NDK CMake toolchain](https://developer.android.com/ndk/guides/cmake): ABI, platform and STL are explicit toolchain arguments.
- [Official C++ runtime guidance](https://developer.android.com/ndk/guides/cpp-support): static libc++ is suitable for this one standalone executable; this does not justify multiple independent static runtimes in a future app.
- [Official page-size guidance](https://developer.android.com/guide/practices/page-sizes): ELF alignment and actual 16 KiB OS execution are separate checks.
- [llama.cpp MIT license at the pinned revision](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/LICENSE), [existing attribution](../../../benchmarks/spike/llama/NOTICE) and [prior source/license manifest](../spike/LLAMA_SOURCES_2026-10-22.json). NDK libc++ uses Apache-2.0 with LLVM exceptions; any future redistribution requires the existing third-party notice review.

## Pending gates and handoff

The source wrapper contains a planned ARM64 build path, but the current steering
paused it before execution. No model load/generation, Android cancellation,
remote process cleanup, 16 KiB OS, ARM64 execution, thermal/memory measurements,
phone tier or backend selection is established. The unchanged helper has no
native self-deadline. Before future device execution, independent review
recommends a bounded native self-deadline plus coordinator PID/start-time/
command-line identity checks and explicit remote TERM/KILL/reap evidence;
killing a host ADB client alone cannot prove remote native cleanup. No such
deadline change is implemented here.

Owned code and outputs remain on the separate branch for coordinator review;
there is no runtime implementation PR from this paused packet. Resume only
under a fresh relevant claim after the current M03.03 task. M01's physical/model
and full comparison gates remain pending.
