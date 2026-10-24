# Read-only Android recovery — 2026-10-23

The retained workspace from the [guarded SDK crash](GUARDED_SDK_DEVICE_2026-10-23.md) was captured without device SQL or another inference call. Coordinator strict Rust replay resolves the narrow canonical outcome: **no accepted gift**. Revision, accepted receipts and accepted events are zero; the requested turn is stored as failed without a receipt, and the player still owns one potion. The generated command, SDK generation/owner metrics and crash cause remain unestablished.

This is a locally verified M01.03/M01.05 diagnostic prerequisite, not completion of those full tasks or phone/model-quality/runtime-profile acceptance. The earlier Agency rejection and failed controls remain preserved.

## Two separately authorized recovery cohorts

Both cohorts used the stopped experimental package at APK SHA256 `0cf4c253c41483973fd1578837d0ba147a7ed3d6d6cd8eb5818a989e185c09dd`, with fresh package/UID, namespace, capacity and protected-metadata checks. No install, AVD lifecycle, model-content hash/copy, cache eviction, SDK invocation or device SQLite open occurred. A remained read-only and below the app-work userdata floor. All actual bytes were retained before validation.

| Check | First raw-wire cohort | Corrected encoded cohort |
| --- | --- | --- |
| Invocation | One; no automatic retry | One; separate source review and GO |
| `shell_v2` | Passed | Passed |
| Remote exit37, empty stdout/stderr | Passed | Passed |
| All-byte control | Expected 262 B; received 265 B; rejected | Canonical 352 B Base64 wire, no LF; decoded 262 B exact |
| Database facts/capture | Not reached | Passed, before/after facts identical |
| Package-scoped crash buffer | Not read | Command passed; zero bytes |
| Final namespace/client cleanup | Passed in separate metadata-only closure | Passed |

The complete first 265-byte control is retained, SHA256 `0040f59988bc06b0e13c69e48e0e82c917e988f7a83715d2e57ae62e4b7e4f8e`. It exactly matches the expected fixture after inserting CR before each of its three LF bytes, including CRLF becoming CRCRLF. This proves that transformation for this observation; it does not identify the responsible layer. The older 1,101-byte mismatch in #111 was not saved, so its cause remains unknown.

The corrected transport retains raw wire bytes and strictly checks canonical Base64, decoded length and SHA256. It handles defined LF/CRLF framing only for ASCII metadata. The logical file limit remains 128 KiB; maximum Base64 wire size 174,764 B fits the existing 262,144 B runner cap. Source and model bytes are not newline-normalized. See [transport tests and source evidence](RECOVERY_TRANSPORT_TESTS_2026-10-23.md).

Frozen encoded source bindings:

- Launcher: `e43c06f5e7839db8df06977bbc7be18ac6c996b9cf0ed6bd99595ce14454ff0a`.
- Transport: `06ef072836e74dd962e9ebf4d371aa0b3a029a7177c7cf89901af5203aa3e6ed`.
- Device byte runner: `e75464bc21130eb3adf300de3d17475f5cc2f4f6c80efd7360f8480f1e66b095`.
- Capture helper: `9199d3f7a6d33f19eb688d408d649bd704baecc9b3f6294b7939dc87edb5c782`.

The actual encoded control wire SHA256 is `6cc1a8e22ffee622a5133b25d51f5aa9bc1031ffe5f6932f3f8bf3f6e5ca6d5c`; its decoded 262 B SHA256 is `b905c1b82d628e1ce2d152af2a60f935d7b6cf3d471176b5638b7c2503d74b12`.

## Stable snapshot and strict replay

The source directory/owner and fixed database leaves were validated through the qualified package. Named-file metadata, full SHA256 and sidecar presence matched before and after transfer. The pristine capture keeps exact SQLite filenames; the coordinator used a separate host working copy.

| Artifact | Observation |
| --- | --- |
| `stories.sqlite3` | 65,536 B; SHA256 `420541d81d1b80c408f84a2e14321b757994978e75cc564c408203ed0b4a4cd9` |
| WAL / SHM / journal | All absent before and after |
| Encoded DB wire | 87,384 B; raw retained before decoding |
| Snapshot manifest | SHA256 `e7c58482103bec4ad08112f3c0785a346b35869c31001bdd4312333d89581592` |

Coordinator strict replay passed with schema 2, valid foreign keys and one story/branch. It found revision 0, zero accepted receipts/events/gift events, no projection rebuild requirement, and the failed requested turn with no receipt. No model executed. Source facts, pristine data and the working main file remained unchanged. The observer independently rehashed the pristine file afterward. This uses the frozen #111 schema 2 source, not then-current schema 3 main.

Strict replay result SHA256: `737faa58b62c9d1d7f038b1fbd0d3b0e7fcc9a46e54e2e28096f03eef342da04`; separate preservation receipt SHA256: `226581960783bbc1b1d4238dba368bdac6d8d97b1dcf111451d2ad209ef01009`.

## Exit-history limits and preservation

The UID-filtered crash buffer was empty; that does not establish absence of a crash or system-owned diagnostic records. A separately authorized, exact package-filtered exit-history read retained 6,878 B privately, SHA256 `b14d7a629ec02bb17f605b7ca45ef5544f0586bcec4b1b9b1ed774e197193fcb`. Its 16 record headers contain 15 reason10/status0 entries and one reason2/status9 entry. These are package-history observations, without a captured crashed-process PID binding. They do not establish which record belongs to the SDK attempt or its cause. No trace files were opened, cleared or modified.

Final encoded-cohort checks preserved the original 21 APK identities per emulator, the experimental B package (22 total), original model/cache metadata and both retained experimental cache sessions. Benchmark namespaces were absent and owned clients had known cleanup. Inventory was four emulators/no other devices, with A/B ready. It had been seven at first preflight; this observer performed no AVD lifecycle action.

At encoded-cohort close, free bytes were C: 9,117,745,152; D: 328,954,097,664; B userdata: 1,738,366,976. The later exit-history read ended with C: 9,080,549,376; D: 328,952,913,920; its fresh package/UID and pre/post namespace checks passed. These are read-only capture checks, not inference/install admission. Metadata preservation does not replace a fresh model-integrity gate before future inference.

## Sealed evidence and next task

The first namespace binds 525 files/302,409 B: index SHA256 `52fda46926fec28f51ba80f6574e8b9bd7dd036c3ce881938a2d6e1a647c8bce`, safe handoff `5092f5ba1a704001b8b6384345fd488c9a7d66a7d37de949796dfbf0fad9e6cb`. It contains 119 initial and 125 closure commands. The encoded namespace binds 573 files/602,635 B: index `4dda8e9c7da0353ccefaa12af0a9312aeb9522066c1652ac26d35c29274cbc9f`, safe handoff `0a904c1122dbca7e1c82726777ac96f4d734fb182c9d0292512d6f0bdde770e0`. It contains 252 capture and 16 exit-history commands. Counts exclude each index and safe handoff themselves.

All 512 recorded owned commands completed with known cleanup and independently rehashed raw stdout. Seven exit-one namespace probes and two expected exit37 controls are retained; this is not an all-zero-exit or global all-started-client claim. Raw SQLite, wire payloads, process identifiers, paths and exit descriptions remain private. No weights, image or cache payload was transferred by this packet.

Device leases are released. The next runnable task is time/PID-bound memory and process-exit diagnosis before considering another guarded SDK attempt. This recovery establishes canonical noncommit in the retained workspace; it does not explain the crash or qualify physical-phone/ARM execution, model quality or a supported runtime profile.
