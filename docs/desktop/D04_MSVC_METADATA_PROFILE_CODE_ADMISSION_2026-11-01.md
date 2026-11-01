# MSVC metadata profile: code-only admission

Refs #25 D04.01/.02/.04, supporting #31 D09.03 and #21;
Root claim6561774956. Branch `feat/msvc-library-metadata-profile-v1`, physical
checkout `D:/CodexLocalLore/01a165d9-ff25-7500-a550-1099087d4e37/source-desktop-fork-review`.
Owned paths are the Buffer module, new FIRST suite and three profile documents.
**Source preparation only. Neither Node check has run or been authorized.**
PR324's one member-facts packet is spent; its accepted main is
`f81257bf910a0a82420cbeb20e6e9b4a30e2896b`.

## Reviewable change and acceptance

The [contract](D04_MSVC_METADATA_PROFILE_CONTRACT_2026-11-01.md) closes the new
API, limits, counting order and interpretation rules. The standalone strict
API still ignores extra arguments. Profile selection is explicit; no global
constant, environment selector, filesystem input or app policy selects it.
One shared private parser processes all members. No app/worker adopts it here.
Both success wrappers retain qualified/linkQualification/closureComplete=false.
The descriptor's read-byte limit needs a future separately admitted collector;
a Buffer parser cannot observe file reads or establish DEFAULTLIB closure.

Independent FIRST commit `e55baf58a45061c35ba019c7a235fae879d17682` predates
the producer edit. Its94 fixed groups cover F01–10 selection/shape, S01–06
standalone strict behavior, J01–16 job accounting/sticky failures, C01–10
member/input/job boundaries, R01–12 unused relocation pointers, H01–12 machine/
layout restrictions, T01–16 terminators/quotes/raw-byte budgets and D01–12
unchanged unsafe-library/archive/name/token constraints. The original112-case
file remains byte-identical. No test body was changed to fit the implementation.
All206 cases remain UNRUN; source review is not a behavioral pass or RED result.
Independent producer review found no concrete source blocker: strict ordering/
shape, conservative job charges/sticky stops, the three narrow interpretation
rules and absence of I/O/worker authority match the contract. Root's whitespace
diff check also passes. Neither observation executes the JavaScript module.

The new suite makes one actual256MiB in-memory Buffer allocation for the
exclusive input boundary. Distinct views charge their full logical lengths to
test the512MiB job limit without allocating512MiB or reading files. Section
boundary cases construct and inspect valid synthetic tables. These are logical
work tests, not measured peak memory, SDK compatibility or native performance.
The checks import only this module and fixed Node builtins, with no SDK/data
reads, test-created file writes, children or model operations.

| Source | Bytes | SHA256 |
| --- | --- | --- |
| `native/llama-worker/library_inputs.mjs` |16987 | `9972c0eb4d8cf936f252b090a8f0794b0d6b5328a2245b8720cdec32d5fafa53` |
| `native/llama-worker/library_inputs_test.mjs` |15402 | `36ec3c81ec02ad4844b91ff7d0de20dae1c8665dbeef697f98476de4fc2e5022` |
| `native/llama-worker/library_metadata_profile_test.mjs` |29151 | `477b31ba971bc4199e5f0915e90fb30715d1f91f5ef4217dc8fdac8523223a38` |

No new Node syntax invocation is proposed. A startup/import failure is UNRUN
setup failure, not a behavioral test result. Missing exports yield exit2,
fixed stderr and an executed0 summary. Every actual result needs its process,
complete raw/base64 streams and exact six-key numeric summary independently read.

## Fixed capture and proposed finite action

The retained local `b2-msvc-profile-code-check-v1.ps1` is23104B, SHA256
`d20241c1a40fe644e8ec3c272a7bb8867532b761088d11ac701c3d971c68ea61`.
It has zero errors under PowerShell's source-only parser; its body has NOT run.
Independent capture review resolved preread physical-path checks, exact prior
phase binding and late observed completion; final source review found no further
concrete defect. This review is not execution or permission.

Propose ONE `legacy` check, followed ONLY after an exact112/112/0 pass and fresh
full admission by ONE `profile` check expecting94/94/0. Fixed Node24.22.1,
SHA256 `d702daa815eabbff763c7d3808e235cf031cf2ca70211b56847bc72f51e240e5`,
PowerShell7.6.5, Windows10.0.26300 x64. Run from the unchanged frozen physical
`source-resource-metrics-review` checkout at7051d46; process-local TEMP/TMP
must be `D:/Dev/_Temp`. The helper paths are the three fixed files above.
Seven Node override environment variables are refused. Each Node child has
30s observed completion limit, stdout2048B/stderr4096B and at most one owned
child kill followed by5s drain. A closed child first observed beyond30s fails
without killing it. Any timeout/overflow/kill/unknown remains failure; closure
does not claim OS process-tree containment. Admission/hash/filesystem operations
have no absolute OS deadline. No automatic retry or third child is authorized.

Unique phases are `b2-msvc-profile-code-legacy-*` and
`b2-msvc-profile-code-profile-*`. Each binds actual owner, runner, Stage,
source revision and exact source hashes. Profile admission independently checks
the Legacy Stage/START/current owner, exact command/caps, complete canonical
raw/base64 records, source projection and both actual passing summaries.
Different or stale evidence cannot unlock it. Failure or insufficient reserve
leaves profile UNRUN. All prior evidence/normal binary/source and global-stop/
incomplete-START fences remain; target/runtime growth must be zero.

Only a future actual answer/origin may create the unique
`b2-msvc-profile-code-owner-decision-v1.json`, kind
`b2_msvc_profile_code_owner_decision_v1`, scope`msvc_profile_two_code_checks`.
It must bind these three sources, runner, revision, cases112/94, metadata1703936B
and all other limits unchanged. Neither it nor either Stage currently exists.
Stage has exactly version,kind,noApp,runner,sourceRevision,metadataCap,
ownerDecision,expectedCases,summaryKind. No proposed owner/Stage is execution
authority. Prospective fixed commands, only after applicable actual admission:

```powershell
& "$packet/b2-msvc-profile-code-check-v1.ps1" -Check legacy
# Only after exact Legacy pass, independent readback and fresh complete reserve:
& "$packet/b2-msvc-profile-code-check-v1.ps1" -Check profile
```

`$packet` is the existing charged
`author-integration-artifacts/d08-fork-native-20261030-v1` directory beneath the
physical D: chat root. The runner cannot accept arbitrary commands/paths/caps.
Ordinary suite entry points are Node with the fixed legacy/profile test file;
they do not bypass this experiment's capture/admission rules.

## Fresh measured storage and retention

Root's source-only preparation inventory, after exclusive runner retention:
metadata1647521B of1703936B; group53848586B of67108864B;
joint736170080B of759169024B; target12356228504B of12554947872B;
runtime fixtures210B. Target/fixtures did not grow. Old F physical549989B,
logical570664B and browser41584016B remain unchanged. Metadata includes10825B
decoded historical source, the12709B frozen strict helper and23104B runner.
No input/test/native/app process ran to obtain this inventory.

Reserve2048B for an actual owner and1024B for EACH future Stage. Each phase
requires38912B for START768B, process16384B, result2048B, Root review1536B,
raw6144B, separately decoded logical6144B and stop512B, plus5376B headroom.
Base64 copies live inside the process ceiling. The all94 failure-ID summary
has an in-memory static size682B, below2048B; this is not executed output.

```text
1647521 current +2048 future owner +1024 first Stage +38912 full phase reserve
=1689505B, leaving14431B under the unchanged1664KiB cap.
```

Two full worst-case phase reserves simultaneously do not fit. This proposal
does not promise both children: after preserving all actual Legacy output and
Root readback, charge the second Stage and require a fresh38912B reserve.
Stop before profile if that reserve does not fit; no cap increase or deletion
is implied. Existing64MiB group,724MiB joint, original-baseline4GiB target,
old576KiB records and8MiB fixture limits stay unchanged. Preserve all sources,
failed packets, raw/decoded output and earlier refusals. No classification or
output-root change can evade accounting.

This is code-only permission preparation. No app/model/worker/native Rust or
C++ build/link/MT, SDK input inspection, Android/device/OS qualification,
download/setup/settings change, deletion, desktop control or automatic retry.
Actual fixed32 profile parsing and DEFAULTLIB closure remain future separate
gates. Author stays Disabled; full D04/D09 and desktop epic acceptance are open.
