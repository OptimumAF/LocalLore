# Native publication-origin categories

Refs #9 (M05.05 prerequisite), #5 (M01.05 supporting). This slice builds on
unmerged PR #142. The previous fresh attempt returned UNSUPPORTED without
distinguishing missing symbol from a rejected rename. Its result and sealed
files remain unchanged; a new attempt cannot retroactively classify it.

The same native operation now returns four additional closed categories. JNI
signature, fixed child names, directory descriptor ownership, validation,
`RENAME_NOREPLACE`, one rename attempt, and default redacted UI behavior remain.
No new library, syscall, resource owner, telemetry or fallback is introduced.

| Wire result | Observation | Meaning | UI failure |
|---|---|---|---|
| 0 | PUBLISHED | Native operation returned zero | None |
| 1 | DESTINATION_EXISTS | EEXIST | UNSAFE_PATH |
| 2 | UNSUPPORTED | Legacy combined refusal | STORAGE |
| 3 | IO_FAILURE | Directory open, other rename error or caught panic | STORAGE |
| 4 | INVALID_INPUT | Existing input/path/stage validation refused | UNSAFE_PATH |
| 5 | SYMBOL_UNAVAILABLE | Dynamic lookup returned null before rename | STORAGE |
| 6 | RENAME_INVALID | Rename returned failure with EINVAL | STORAGE |
| 7 | RENAME_UNAVAILABLE | Rename returned failure with ENOSYS | STORAGE |
| 8 | RENAME_UNSUPPORTED | Rename returned failure with EOPNOTSUPP | STORAGE |
| Other | UNKNOWN | Unrecognized wire value | STORAGE |

The pure Rust classifier is used by the actual rename-error path and tested on
the host. Unknown/missing errno values remain IO_FAILURE; EEXIST still refuses
existing destinations. Kotlin observes only the finite enum, never an arbitrary
errno, path, exception or provider text. Older clients still refuse new codes as
STORAGE; newer clients retain legacy code 2 without inventing its origin.

These are operation observations, not diagnoses of a kernel, filesystem,
permission or particular device defect. SYMBOL_UNAVAILABLE proves only that
this lookup returned null. A rename category establishes that the resolved
wrapper was called and returned the specified error; it does not prove which
layer rejected it. EINVAL does not by itself identify a bad flag. No result
authorizes cleanup, retry, replacing rename, hard link or alternate destination.

Official Android 15 [Bionic stdio.h](https://raw.githubusercontent.com/aosp-mirror/platform_bionic/android-15.0.0_r1/libc/include/stdio.h)
defines NOREPLACE and the API-30 wrapper. The installed pinned NDK 29 UAPI
headers define EEXIST=17, EINVAL=22, ENOSYS=38 and EOPNOTSUPP=95. No dependency
or license input changed; these source facts do not establish device execution.

A fresh synthetic fixture uses a distinct fixed origin sibling and internal
proof root, preserving all prior roots without reading them. It calls the real
publisher once. It checks exact tiny stage/destination effects, closed mapping,
one callback and candidate-root absence. A diagnostic PASS can represent refusal;
`publication_succeeded` and `positive_store_qualification=false` remain separate.
`origin_classified` is true only for the four new categories. Legacy UNSUPPORTED
or an unknown/other failure does not establish the requested origin distinction.

The independent real-artifact capacity shortfall remains a separate gate.
Canonical saves, SDK/model identity, reserves, default storage, A/#117/#119,
physical-phone and complete M01/M05 acceptance remain unchanged. A successful
synthetic observation does not authorize real-model copy or inference.
