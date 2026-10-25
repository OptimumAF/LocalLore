# Fixed-name publication diagnostics

This records the initial combined-code boundary. The subsequent
[native-origin contract](MODEL_PUBLICATION_ORIGIN_CONTRACT.md) adds closed
origin categories while retaining these legacy mappings and fixed UI failures.

Refs #9 (M05.05 prerequisite), #5 (M01.05 supporting). This slice builds on
the unmerged candidate-volume experiment in PR #141. It introduces no runtime,
dependency, JNI symbol, syscall, candidate/runtime storage destination, or
publication fallback. Its new synthetic sibling is a test destination only.

`NativeModelPublication.publish(File)` retains its original signature and fixed
failure behavior. An internal overload accepts a trusted observer that receives
exactly one `ModelPublicationResult` after the native call returns and before
the existing failure mapping. The default call uses a no-op observer. Neither
setup UI nor normal diagnostics subscribes, and no automatic log is written.

| Existing JNI result | Closed observation | Existing outcome |
|---|---|---|
| 0 | PUBLISHED | Return |
| 1 | DESTINATION_EXISTS | UNSAFE_PATH |
| 2 | UNSUPPORTED | STORAGE |
| 3 | IO_FAILURE | STORAGE |
| 4 | INVALID_INPUT | UNSAFE_PATH |
| Any other integer | UNKNOWN | STORAGE |

The enum contains no path, URI, provider text, exception, errno, or raw integer.
Unknown native results fail closed. The observer is internal test instrumentation,
not a model callback or a public error API. An observer exception propagates;
observation happens after the native operation and cannot roll it back. An
exception or cancelled caller must never imply that publication did not happen.

UNSUPPORTED combines a missing dynamically resolved Bionic `renameat2` symbol
and EINVAL/ENOSYS/EOPNOTSUPP. It does not identify which condition occurred or
prove that a particular filesystem lacks support. IO_FAILURE combines directory
open failure, other rename errors, and a caught native panic. These categories
are deliberately narrower evidence than an errno, syscall trace, or root cause.
The implementation of those native codes and `RENAME_NOREPLACE` is unchanged.

The official Android 15 [Bionic header](https://raw.githubusercontent.com/aosp-mirror/platform_bionic/android-15.0.0_r1/libc/include/stdio.h)
declares the wrapper at API 30; its [symbol map](https://raw.githubusercontent.com/aosp-mirror/platform_bionic/android-15.0.0_r1/libc/libc.map.txt)
places it in LIBC_R. The installed pinned NDK 29 header agrees. This source
check confirms the existing compatibility assumption, not actual symbol
resolution or filesystem support in an executing app. No dependency changes.

Pure JVM tests check all five existing codes, unknown integer boundaries,
unchanged redacted failures, default observation, and observation ordering. They
do not load JNI or execute native publication. Android packaging/cross-builds
and actual filesystem checks are separate evidence.

A separately admitted synthetic fixture may observe a fresh publication in a
new fixed sibling under the same Context-owned volume. It must preserve the
previous failed synthetic root and real-candidate slot. A passing diagnostic
method can establish that a refusal was classified and its tiny files preserved;
it cannot be counted as a successful import, SDK turn, or positive filesystem
qualification. The exact observed enum and preservation checks must accompany
the result. A new refusal cannot retroactively classify the earlier attempts.

No result authorizes retry, stage cleanup, replacing rename, hard-link fallback,
alternate volume selection, real-model copying or inference. The A, #117/#119,
physical-reference-phone and full M01/M05 gates remain independent.
