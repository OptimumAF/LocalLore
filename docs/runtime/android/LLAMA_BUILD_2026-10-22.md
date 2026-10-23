# Android llama.cpp build experiment

M01.02 preparation, branch `research/m01-llama-android`, baseline main
`2c095ea066fe1101f756d5153e46c75f77806bd3`. The coordinator's claim is
[#5 comment 6353871377](https://github.com/OptimumAF/LocalLore/issues/5#issuecomment-6353871377).
The first x86_64 cross-build was preserved in `5286adb` when the user redirected
work to M03.03. The continuing goal then resumed this slice under
[#5 comment 6354076434](https://github.com/OptimumAF/LocalLore/issues/5#issuecomment-6354076434).
The current helper adds a parent-independent Android-only deadline. No emulator
or phone is accessed by this build agent; execution evidence belongs to the
coordinator. Both x86_64 and ARM64 cross-builds are now verified below; no ARM64
execution is inferred.

## Actual checks

Run from the separate `LocalLore-llama-android` worktree:

```powershell
python benchmarks/spike/android/llama/build.py --source ../LocalLore-llama-spike/target/runtime-spike/llama.cpp --sdk "$env:LOCALAPPDATA/Android/Sdk" --abi x86_64
python benchmarks/spike/android/llama/build.py --source ../LocalLore-llama-spike/target/runtime-spike/llama.cpp --sdk "$env:LOCALAPPDATA/Android/Sdk" --abi arm64-v8a
python -m unittest discover -s benchmarks/spike/android/llama -p 'test_*.py' -v
```

Both ABI cross-build commands exited 0: each ran 137 CMake/Ninja steps for the unchanged
C++ API helper plus the new Android-only deadline translation unit. Cargo
`--locked --offline --release --example runtime_spike` built the existing Rust
engine oracle for `x86_64-linux-android` and `aarch64-linux-android`. The unchanged pinned upstream source
was clean before/after. Thirteen synthetic source-pin/ELF tests passed,
including wrong source revision, dirty source, malformed ELF, wrong architecture,
missing PIE, 4 KiB alignment, unexpected shared dependency, direct initializer,
x86_64/AArch64 relative initializers and missing/unretained constructor.
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
The ARM64 cache and generated flags confirm baseline `armv8-a`, with native
tuning, OpenMP and llamafile disabled. No global higher ARM ISA was added.

## Actual ELF bytes

The build's byte inspector and NDK `llvm-readelf --file-header
--program-headers --dynamic` agree on both ABIs: matching ELF64 machine, ET_DYN, DF_1_PIE,
`/system/bin/linker64`, three LOAD segments each aligned to 16384 with 16 KiB
file/virtual offset congruence. No `libc++_shared` or OpenMP shared dependency.

| ABI/output | Bytes | SHA-256 | NEEDED |
|---|---:|---|---|
| x86_64 C++ helper | 98427296 | `148f24f8a3346826817646fae79a08dd989485b7957e05b4234d4ffc7d9b5ba9` | libm.so, libdl.so, libc.so |
| x86_64 Rust oracle | 1382376 | `1b3e12e94470cea37a5ccbddeec568e9cca7c2ac723b620f0a494cd12305d228` | libdl.so, libc.so |
| arm64-v8a C++ helper | 99469632 | `b6de3131c851bfdb3eea36b9e1a42894473d8128310ba8393a6402011007ee39` | libm.so, libdl.so, libc.so |
| arm64-v8a Rust oracle | 1334560 | `8afded0df72c73ad47afa872e1cc8f2f94c20c4dcda433ca01a680c724c632d5` | libdl.so, libc.so |

Ignored output locations: `target/android-runtime/llama/<abi>/host-helper/`
and `target/android-runtime/llama/rust/<rust-target>/release/examples/`.
Both C++ executables retain upstream build debug information; this is no app
size or release packaging result. Hashes identify this actual build, not a
promise of reproducible compiler bytes across machines. No binaries or weights
are committed. Source build instructions and audit tests are versioned.

## Native deadline ownership

`deadline.cpp` is a direct executable source, not an optional static archive
member. Its priority-101 constructor runs before ordinary C++ dynamic
initialization and `main`: reset `SIGALRM` to `SIG_DFL`, construct/unblock its
signal set, then `alarm(90)`. Setup failures call `_exit(124)` with no logging.
The fixed bound has a compile-time assertion and no command-line/environment
override. It covers blocked request input as well as model load/generation;
the trusted helper exposes no process-creation entry point.

Actual ELF inspection proves the linked constructor symbol is retained in
`.init_array`, resolving PIE relocations on both ABIs. Actual NDK
`llvm-objdump --disassemble-symbols=locallore_android_arm_deadline` shows reset,
unblock, failure and `alarm` calls with argument `0x5a` (90), rather than relying
solely on the source constant, in both x86_64 and AArch64 output. The actual signal firing/remote process exit is
not tested by these host builds. The default action is abrupt OS termination;
no cooperative RAII cleanup, instant scheduling, descendant cleanup or safe
continuation of model state is inferred. A fresh process is required.

API declarations were inspected in installed NDK r29 `signal.h` (SHA-256
`fc93227032832f7ec26e87402cfabec900dbf1d4c7647015ca60b131afae3f3d`)
and `unistd.h` (`05045cfbd60c8dd1abd13fec471a6e96965d133bfb69f1269223ecd189f0fce4`).
`signal`, `sigemptyset`, `sigaddset`, `sigprocmask`, `alarm` and `_exit` are
available to the API-28 target; compilation and linking validate those NDK
declarations. Current official [bionic signal declarations](https://android.googlesource.com/platform/bionic/+/refs/heads/main/libc/include/signal.h)
and [unistd declarations](https://android.googlesource.com/platform/bionic/+/refs/heads/main/libc/include/unistd.h)
were also checked. No new library or source copy is added.

## Official compatibility and license references

Verified before building against the pinned upstream source and current
official Android docs:

- [llama.cpp Android NDK instructions at the exact source revision](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/docs/android.md): Android toolchain, API 28, native tuning/OpenMP/llamafile/OpenSSL disabled.
- [Official NDK CMake toolchain](https://developer.android.com/ndk/guides/cmake): ABI, platform and STL are explicit toolchain arguments.
- [Official C++ runtime guidance](https://developer.android.com/ndk/guides/cpp-support): static libc++ is suitable for this one standalone executable; this does not justify multiple independent static runtimes in a future app.
- [Official page-size guidance](https://developer.android.com/guide/practices/page-sizes): ELF alignment and actual 16 KiB OS execution are separate checks.
- [llama.cpp MIT license at the pinned revision](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/LICENSE), [existing attribution](../../../benchmarks/spike/llama/NOTICE) and [prior source/license manifest](../spike/LLAMA_SOURCES_2026-10-22.json). NDK libc++ uses Apache-2.0 with LLVM exceptions; any future redistribution requires the existing third-party notice review.

## Pending gates and handoff

No model load/generation, Android cancellation,
remote process cleanup, 16 KiB OS, ARM64 execution, thermal/memory measurements,
phone tier or backend selection is established by this build packet. Device
execution requires coordinator PID/start-time/command-line identity checks and
explicit remote TERM/KILL/reap evidence; killing a host ADB client alone cannot
prove remote native cleanup. The unchanged Rust oracle does not inherit this
helper-specific deadline and needs its own coordinator control.

Owned code and outputs remain on the separate branch for coordinator review
and central integration. M01's physical/model and full comparison gates remain
pending; these builds select no production runtime.
