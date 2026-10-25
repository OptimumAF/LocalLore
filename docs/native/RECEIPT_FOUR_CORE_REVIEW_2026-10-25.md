# Four-core receipt experiment review — 2026-10-25

**Actual result:** one authorized four-vCPU API35 x86_64 experiment passes production receipt import, a guarded real SDK player turn and separate-process reopen: **56 protocol checks and four selected JUnit passes**. This is functional evidence for that experiment, not proof of a causal speedup or a supported phone profile. Earlier two-core failures remain preserved.

Refs #9, M05.05 / M01.04 / M01.05. Independent claim 6396099096 under root 6396079595. Owns this report only. The reviewer performed source and retained-evidence checks; no build, host test suite, SDK/ADB/emulator execution, model transfer/read, runtime-cache access or AVD disk read. Private token hashes were compared without output or copying token contents. See the [coordinator's full execution record](RECEIPT_FOUR_CORE_VERIFICATION_2026-10-25.md) for complete hashes and original tool attribution.

## Source and test review

At execution freeze `bbf3628d14ba6061e20015649de1b859779121a3`, the helper admits exactly three integer tuples: `(2048 MiB, 4 GiB host RAM, 2 cores)`, `(8192, 12 GiB, 2)` and the explicit new `(8192, 12 GiB, 4)`. Actual-boolean selectors and CLI phase restrictions prevent accidental promotion. Existing two-core profile values, launch arguments and resource-fact shape remain unchanged; their resource check does not query CPU count. New source hashes naturally require new exact authorizations.

Four-core admission requires an actual integer logical host CPU count of at least eight. Unknown/None, booleans, floats, strings and insufficient counts refuse. Parent checks precede root/child creation; the authorized worker rechecks before its SDK dispatch. The same bound core count reaches immutable config and emulator arguments. Prepare/run common-field equality refuses switching even between otherwise valid profiles. Logical count is sampled metadata, not physical-core count, idle CPU or a speedup promise.

The controller's four-core branch performs one fixed `cat /sys/devices/system/cpu/online` per cohort after boot and before facts/install/copy/SDK work, requiring `0-3` with the existing strict line normalization. Its ordinary client retains raw output and known cleanup/owner state before interpreting the response. A fixed three-integer observation is written only on success; mismatches, owner/cleanup loss or evidence-write failure stop before further work. Two-core runs add no command. The guard grants no post-uncertainty inspection or general shell authority.

Reviewed tests cover exact defaults/profile triples, malformed selectors/counts, config/argv agreement, parent and worker no-spawn refusals, CPU re-admission ordering, unchanged two-core behavior, prepared/config drift and CLI dispatch. Controller cases cover positive observation/one-shot behavior and mismatch, unknown cleanup, late owner loss, wrong phase and failed proof retention. No concrete source blocker was found. Existing SDK four threads, APK/Rust inputs, required schemas, token budgets, 60-second turn, five-second cleanup, phase/owner limits, resource floors, fences and held targets are preserved.

The retained full host result reports **718 tests passed** in 102.066 seconds; completed-zero, known cleanup in 102,828 ms. Its 84,620-byte stdout independently hashes to `6acbadb5065ca49a35d71961656e002ff5c3475aff7250f50780ceb2cec4d7d5`. The log includes 88 environment and 24 controller test methods. This review did not rerun them. A refusal JSON emitted by an intentional CLI test is interleaved in the host log; it is not a test failure.

## Reused artifacts and fresh prepare inputs

All 1,529 current/copied source rows match the frozen index. The actual nine-file change set from compiled `2ea73aa10f549c70d5117dcdac89413de5fb2fcd` contains no Android, Rust or build changes. All 206 compiled Android source rows match; the reused APP/TEST and regular APP were independently rehashed. This is source/artifact equality, not new Android/JVM execution.

Receipt APP: `83d0709efbd9a72266214d526fadc4f435880ea113b942ddada716e3ea82fda3`; TEST: `6def97ed744cabb5c98a906a37c976c4a33b6bd0973effcbeda09bef282d7d8a`. The preceding packet retains their actual build/audit/signature evidence.

Fresh disabled PREPARE `32ebf859d2e470d66966bba3f0ec5c55466237140d11dab351db5e0b203aeb82` passed independent closed-policy checks. Its complete 909-entry binding set totals 5,046,140,683 bytes: **905 source/tool content hashes and four public SDK .img metadata checks**. SDK images and AVD disk contents were not read; the coordinator's unchanged stock guard performs the full check.

The new explicit C target was absent with no grant at prepare review. Token-hash/default-registry preservation, free ports and unchanged 40 GiB C/D and 12 GiB host-RAM floors passed. Independent host facts were C 266,004,086,784 bytes free, D 47,099,637,760, available RAM 35,984,048,128 and 20 reported logical CPUs. These are admission observations only. Root alone owns grants and actual dispatch; preparation alone establishes no guest CPU count or performance.

After the coordinator's successful preparation, RUN `aeb41ca08550f12402ba6d409bab4a8a0558ca776c90205e817dda488055107b` independently passed the same 905-content/four-image-metadata replay. It links the exact PREPARE, prepared record `406bd88c872351019c7968dd4d1cd77c26f9a7459859d5ecf18570b2e31d5bf3` and successful closure `959d609d83a34b389cfd65629e5c43a8b42e4dbd475545d1e10496d784bafb4e`. All three immutable config/registry files match. CPU configuration and argv agree on four, with unchanged 8 GiB RAM, 12 GiB userdata and 8 GiB SD; initial SD was metadata-checked and userdata remained absent. Host logical count was 20 and resources/ports/preservation passed before any RUN grant or descriptor existed. The 1,800-second owner ceiling and inference limits are unchanged. The coordinator separately performs full initial-disk and stock installation checks.

## Preflight and candidate admission

Preflight `be2d6df9ff09e9c33fbde74e20c662ae5878b659d265394fd2662492a14ab073` bound 81 current/archived nonweight inputs (86,722,433 bytes), all independently rehashed. The scope admits only the 61-byte staging probe, with no model-copy or SDK grant. The exact descriptor and three host process identities passed a cheap metadata-only live check with 1,747.1 seconds remaining; the coordinator's full stock lease check remains separate.

The actual preflight's 44 contiguous client records independently match completed-zero/known-cleanup statuses and raw hashes. Its strict runner has one pass and its proof `c59ff1e088a4ad9b3474bd56c112748e9e410467770a74e040458f8e9374f68f` satisfies all twelve checks with SDK false. The CPU client at index two is individually verified: exact five-byte `0-3` response with line ending, SHA `5673d827d554439943a513b6a2cc7dbbc730ce668740cf1db297f7b32f114a34`, 128-byte cap and at most five seconds. The retained JSON is exactly version one, requested four, observed four. This is one sampled guest online mask, not proof of physical cores or continuous CPU availability.

Candidate `010122fafcc7c4b8afb9e96c595af616f6a7be937cd72457f1eb47aaddfb3cce` bound 85 current/archived nonweight inputs (86,728,674 bytes), all independently rehashed. Strict validation links the successful preflight/known-clean outer result, exact reused APKs and direct human consent. Model identity was metadata-checked only; the 2,588,147,712-byte weight file remains excluded from generic bindings and archives. The cheap live-owner check passed with 1,547.2 seconds remaining, above the unchanged 920-second entry gate, before candidate authorization.

## Actual guarded turn and reopen

All 56 candidate client records have contiguous indices, completed-zero/known-cleanup status and matching raw stdout hashes. Each of the three exact selected runners independently parses as one pass. The raw proof chain links preflight → import → PLAY → REOPEN through prior proof hashes, process/UID metadata and the unchanged model identity. Both cohorts retain exactly one successful four-CPU observation before their work.

| Phase | True checks | Proof observation elapsed |
| --- | ---: | ---: |
| Source preflight | 12 | 200 ms |
| Import | 16 | 101,237 ms |
| Real SDK PLAY | 15 | 95,363 ms |
| Separate-process reopen | 13 | 35,766 ms |

Import independently verifies and imports the full model, each with one open/close and 2,588,147,712 bytes; transfer-client zero alone was not treated as destination proof. PLAY submits one production free-text player turn through the actual local SDK, reaches Prepared through the existing known-close gates, performs the mandatory post-SDK full model recheck and commits the Rust-validated potion gift to Mira. Its proof records revision one, one receipt, zero repairs and fallback false. REOPEN has a changed app process identity pair, no source open or SDK call, and the same revision/receipt. Both proofs agree on receipt SHA `3ef744f27ce40a10e35dd80dbc88af00cbd4009389981723bae7e060a691fb2e`.

The four raw process snapshots independently replay through the frozen continuation boundary: APP absent at observed endpoints, with one allowed TEST helper row at the final endpoint. This is not continuous helper liveness or an unobserved-PID-reuse guarantee. Known-close/handle checks use the existing bounded public ownership contract; they are not an audit of every hidden native epilogue. No worker failure trace was emitted on this passing run.

These elapsed values are whole test/proof observations including setup, full model checks, SDK work, commit and teardown. They are **not** isolated generation or complete player-turn latency. Host load, caches and scheduling were not controlled for a causal two-versus-four-core benchmark. A successful four-core experiment does not diagnose the prior failed attempts or weaken their holds.

The coordinator consumed original preflight 84014 and candidate 75519 at tool terminal zero. Their retained workers completed zero with known capture/cleanup in 43,328 and 380,500 ms. After candidate completion, original owner 55581 consumed terminal zero; its retained stop_requested result records 735,500 ms, known capture/cleanup/preservation closure and worker exit one from requested drain. Output lengths 15,825/1,079 bytes match the copied sealed stdout/stderr. Host post-stop records show all three original identities absent and ports free. Guest flush, VM cold-reboot/power-loss durability and hidden-native reclamation are not inferred.

## Final sealed verification and limits

All four final indexes and **1,980 recorded files / 193,173,659 bytes** were independently rehashed with zero mismatches. Model weights and VM disks were excluded from these inventories and unread by the reviewer. The final 980 non-Markdown rows (12,980,526 bytes) still match frozen `bbf3628d`.

| Inventory | Files / bytes | SHA-256 |
| --- | --- | --- |
| Host | 1,542 / 19,075,064 | `c793e2564a752e3553d11957ce3279c04b18c137c54bdf090bbf97f149a8fd6d` |
| Environment | 27 / 394,542 | `0df2085dd673b9c3c5d3200dad8fe1de9a89b373f2b7f8cec3ab3c1e5dc4df3d` |
| Preflight | 188 / 86,832,481 | `36d3380c888f33fdcad5bf96333c72003a6ea4eed154ef41adcc8fe67d2b02f9` |
| Candidate | 223 / 86,871,572 | `b0b576628547df1d2566cd72f2db092883bea6554319d60361a7fe52a0a82950` |

The retained planning refusals precede any SDK action: a short commit reference left only empty metadata directories, and an intermediate builder syntax failure wrote nothing. The corrected create-only plan required full source identity and empty directories; neither refusal was treated as an executed prepare or a reused grant.

No concrete source/evidence blocker was found for this scoped experiment. M05/M01 remain partial/in_review pending broader criteria and owner acceptance. Physical phone, ARM64/16-KiB execution, DocumentsUI, real-model cancellation/recovery, cache privacy/peak growth, sustained quality/thermal/latency and power-loss gates remain unqualified. The next separately admitted cancellation/recovery task can use this working profile while preserving receipt/canon, original limits and old data. No merge or blanket backend/phone acceptance follows this report.
