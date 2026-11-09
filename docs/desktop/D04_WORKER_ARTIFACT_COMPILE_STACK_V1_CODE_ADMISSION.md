# D04 compile-stack v1 code verification admission

Refs #25 (D04.01/.02/.04), #31 (D09.03/.05) and #21.
This proposed packet is unadmitted and unrun. It would run existing
in-memory checks together against the exact test stack at
`a13dc2448f774c93f6ea5994fcfd70ec6674a168`. It does not need an
evidence-cap increase. PR #403's separate unspent proposal remains
pending. A different packet changes its measured baseline. If this
packet runs first, refresh the #403 forecast before any invocation.

## Exact child and boundary

Use the already pinned Windows x64 Node 24.22.1 binary with the exact
SHA-256 below, the installed PowerShell 7.6.9 Core and .NET 10.0.14 on
Windows 10.0.26300.0, and the existing clean physical D: desktop source
checkout at this reviewed packet head. Use one approved retained
supervisor copy in the existing evidence group. Its only child is
the pinned Node binary with the fixed collector as its only script
argument. Set D: TEMP and TMP. Clear the child environment, set only
the reviewed system directories and temp, and supply no preloads,
options, coverage or cache flags.

Use Node's enforcing permission model and one exact file-read grant
per each of the 12 content leaves. There are no child, write, worker,
addon, WASI or inspector grants. This is a safeguard for reviewed source.
It does not assert that the OS performed only 12 reads or that the
permission model contains hostile code. Normal module-loader metadata
and pinned source, installed tool, normal image and historical evidence
guard reads remain. No code or native fixture creation, SDK/library
payload observation, downloads, link/build, model, app or device work
are part of the packet.

1. Run H01–H14 with the actual held output reader through its in-memory
   adapter. Retain its exact emitted group result.
2. Only after all 14 pass, run C01–C11 with the actual compile observation,
   recipe, root lease and reader cores using in-memory adapters. Retain
   its exact emitted group result.
3. Only after all 11 pass, dynamically import the readiness FIRST file.
   It runs A01–A12 and emits one exact summary on success. This exercises
   profile and READY validation only. It does not invoke the entry runner.

The parent requires direct process exit zero, known stdin/process handle
closure, both output EOFs and closed handles, no timeout/overflow/kill/I/O
uncertainty, exact ordered stdout and empty stderr. Run allowance is
30 seconds plus at most five seconds of bounded direct closure observation.
Capture at most 4,096 raw bytes per stream with a one-byte overflow probe.
Retain raw prefixes and STOP on refusal, including any earlier passing
groups. No Base64 mirror is retained. No automatic retry. A pass means
37 code groups only. This packet cannot qualify native Job, filesystem,
loader, worker, compiler, app or desktop behavior.

## Exact pins and records

The transitive local source content leaves in the checkout are fixed.

| Source | Bytes | SHA-256 |
| --- | ---: | --- |
| `library_inputs.mjs` | 17,906 | `c6bd3309db944bf431838fd1e98670a6e8ed937f104e66a31735c5cc1372c5dc` |
| `worker_artifact_recipe_v1.mjs` | 6,477 | `93269f12448f4539c8b1e1ec035cd0d8da522740eff979b38b525db02fbb622b` |
| `worker_artifact_output_roots_v1.mjs` | 15,919 | `fc79d4f73e10d2ab628162f08cf95d0c4746017df50eaa4813ce53f43fee5642` |
| `worker_artifact_held_outputs_v1.mjs` | 14,590 | `9a6147474ad135cce60268d2d80baedce2e2773010b546d33621e93463cdddde` |
| `worker_artifact_held_outputs_v1_first.mjs` | 28,144 | `7c0aacf20ab82fc566a45c1c3bf404e9a85fd2b3ef40a5e423db19a55e8954ed` |
| `worker_artifact_compile_observation_v1.mjs` | 20,678 | `8b5b08bb13fb6a18981250eb1b77a12f17cd8b9fdb9d53b983d20ad37f99a75e` |
| `worker_artifact_compile_observation_v1_first.mjs` | 29,208 | `487c011f586367d766bd6d945cf7d8d0121c069372039ed02e54c6869b60ed56` |
| `worker_artifact_compile_host_v1.mjs` | 12,498 | `c194f981d7c07f4036ff7ca202216b8c9ebc60247cdb7f4d2b4e4181c8a51b1f` |
| `worker_artifact_compile_supervisor_v1.mjs` | 22,022 | `12dd4ded00b6fd6dfe5ff23b8f829e04b7f9b43c61e7065428e963bcbe80353a` |
| `worker_artifact_compile_attempt_v1.mjs` | 13,605 | `5ac0668f773a6aeffe0e30d09c7ef243276a4e878e0221ddf06836226d406601` |
| `worker_artifact_compile_attempt_v1_first.mjs` | 6,737 | `41349dbeb1e29d5d2405f918e43fdfff0e605f03a432dc0e10dfe9bc57d30834` |

Before any execution, separately approve this packet, verify the clean
reviewed checkout and physical D: namespace, and durably record the grant
as spent. Create the two exact packet copies plus the decision and retained
source-review envelopes in the existing group only after that approval.
Independently reread and compare the actual retained sources. Keep both
copies byte-for-byte equal to the reviewed repo files. Readback exact
hashes are below.

| Packet source | Bytes | SHA-256 |
| --- | ---: | --- |
| `worker_artifact_compile_stack_v1_code_first.mjs` | 2,680 | `e7ca4f7bebff4fd455e6b4b6d4dd32def518b20e73769adb992517c72a40347f` |
| `worker_artifact_compile_stack_v1_code_supervisor.ps1` | 18,849 | `3438a2745cd14ecc90d20ed6704bbf244894326b735be8945b3d0ac8d7e35bef` |

Retain the four preparation files under the fixed prefix
`b2-worker-artifact-compile-stack-v1-code-`, using the suffixes
`supervisor.ps1`, `collector.mjs`, `owner.json` and `source-review.json`.
The owner decision includes version 1, kind compile_stack_code_owner_v1,
decision, approved true, cap 3125248, runCount 1, roster, testRevision and
codeOnly true. Decision binds the actual user approval. The source review
includes version 1, kind compile_stack_code_review_v1, owner file hash,
collector and supervisor hashes, testRevision, release (exact reviewed PR
head), independent true and retained true. A locally written envelope is
not authority without the actual approval and retained-source review.
Invoke the exact retained supervisor once, with no arguments, from the
physical D: source checkout. It verifies scope, exact source bytes, current
envelopes and roster and writes its own START before offering the child.

Installed Node image SHA-256 is
`d702daa815eabbff763c7d3808e235cf031cf2ca70211b56847bc72f51e240e5`.
The normal unlaunched desktop image SHA-256 remains
`7a68992bc35d2e778d71e8db80ef4050a281d65d785a054e77abb569aadaf192`.
The supervisor verifies the complete pinned normal image before and after
the child. Preserve all previous STOP, refusal and unlaunched files.

## Current inventory and complete reserve

Read-only inventory found the fixed prefix absent, 877 prior top-level
files, and the following prior roster SHA-256 under this packet's format:
`39ae1d968b71aed86061f40d9cc308b21bd28aef37db5064db6aaf6320517e7c`.
Hash each line as UTF-8 name, tab, decimal byte count, tab, lowercase
SHA-256 and LF, with names sorted ordinally. The 877 files include
historical failure and unlaunched records. No history exception is added.
The 42,616-byte decoded metadata charge and 31,791-byte joint/group carry
for prior records stay charged. No duplicate encoded stream is added.

| Complete allowance | Bytes |
| --- | ---: |
| Supervisor/collector cap | 24,576 |
| Owner and retained review caps | 4,096 |
| START, both raw streams, process, result and STOP | 17,408 |
| Complete addition | 46,080 |
| Current charged metadata | 3,060,788 |
| Full forecast | 3,106,868 |
| Unchanged metadata cap | 3,125,248 |
| Remaining after full forecast | 18,380 |

Physical group and joint totals were 55,230,062 and 737,551,587 bytes.
Full forecasts including carry are 55,307,933 and 737,629,458 bytes,
below the existing 64 MiB group and 724 MiB joint limits. Target
12,356,228,504, runtime fixture 241, old code files 549,989 and browser
41,584,016 bytes remain unchanged. No new target or fixture space is
reserved. Require at least 1 MiB free on D: and repeat full admission before
retaining sources and before START and the one child offer. Any mismatch
refuses. No earlier native grant or pending #403 approval can be reused.
