# D04 worker output-root lease v1: proposed code check

Refs #25 (D04.01/.02/.04 prerequisite), #31 (D09.03/.05 prerequisite), #21.
This proposal is **unrun**. The #395 grant is spent. This document neither
extends the retained-evidence limit nor authorizes a new attempt.

## Exact scope

One pinned Windows Node 24.22.1 process, a 30-second deadline and at most a
five-second capture drain, with at most 4096 bytes retained per output stream.
The child calls `runWorkerArtifactOutputRootsSelfchecksV1` once. The only
passing summary is canonical JSON with exactly `version:1`,
`kind:"worker_artifact_output_roots_first_v1"`, `executed:15`, `passed:15`,
`failed:0`, and `failed_case_ids:[]`, followed by LF, with exit 0, empty
stderr and known closure. No timeout, overflow, I/O uncertainty or attempted
kill can pass. The synthetic adapter uses only in-memory marker data, a fake
clock and deferred promises. The Windows production factory is not invoked.

Contract `92a531d7`; independent FIRST `f260b949` preceded the initial
producer `fe62a8f9`. Additive R11 `55c2fc92` preceded the correction
`e31698fa`, which keeps creation unknown when a malformed reply provides no
handle. The original assertions remain. [The lease contract](D04_WORKER_ARTIFACT_OUTPUT_ROOTS_V1_CONTRACT.md)
defines exclusive ownership, marker verification, the allowed roster and
storage/closure boundaries. Static Git scope and whitespace checks do not
count as executing R01–R15. Source review findings and their corrections
remain visible in Git.

No actual candidate roots or fixture files, build/compile/link/MT, SDK or
library observations, retained build/library report analysis, worker/model/app/device
operations, desktop control, downloads, settings changes, deletion or retry.
Fixed source, prior record and tool/normal image guard reads remain. No new
target or fixture bytes are reserved. The unlaunched normal image stays
unchanged.

## Pair and chain

Reuse the entire accepted
[#395 capture pattern](D04_WORKER_ARTIFACT_PREEMBED_COPY_V1_CODE_ADMISSION_2026-11-03.md)
with only this packet's fixed source/export/summary/namespace bindings,
current storage and PowerShell version pins and the addition of all twelve exact #395 record
pins. Do not loosen the historical-failure fence. The same two narrow
historical pre-child/padding exceptions still require their exact existing
hash and closure/absence guards. A new STOP or incomplete attempt refuses.
A closed historical packet does not authorize a new attempt.

The whole uncompressed candidate pair, prepared as text only:

| Source | Bytes | SHA-256 |
| --- | ---: | --- |
| PowerShell supervisor | 49,368 | `678ec9153c7b0e2c4ae6328f304cc3c62f88ae23184bbcee6c0cc756cfff6e54` |
| Node collector | 5,103 | `86f6b16ef7a53fa1e5e07f35131aca2acf67f1ddfaed6503f411a5d3a1b076a8` |

The namespace `b2-worker-artifact-output-roots-v1-code-` is absent in
the existing retained group. If separately approved, retain the exact two
programs using create-new files, check actual bytes and hashes, and have an
independent reviewer reread the entire actual retained pair before any
invocation. Bind exact lease and FIRST bytes as well as the two programs;
the accepted recipe is an additional immutable guard.

Current public source pins:

| Public source | Bytes | SHA-256 |
| --- | ---: | --- |
| Lease at `e31698fa` | 15,919 | `fc79d4f73e10d2ab628162f08cf95d0c4746017df50eaa4813ce53f43fee5642` |
| FIRST at `55c2fc92` | 28,864 | `8b1924ac43383676f3096974531595d3b04672ad17402e54323d8e2d2c130bad` |
| Accepted recipe | 6,477 | `93269f12448f4539c8b1e1ec035cd0d8da522740eff979b38b525db02fbb622b` |

Carry forward all 183
earlier packet guards plus the 12 accepted #395 pins, along with the existing
read-only source and tool/normal guards. Recheck actual owned paths, historical
records/fences, source equality and every full reserve after retention. Record
the truthful owner decision, actual-source review and Stage receipts, and
mark the grant spent before invoking the supervisor, including any pre-START
refusal. Preserve partial output and every prior failure. No alternate
path, cap reset, overwrite, automatic retry or second test child.

The intended parent is PowerShell 7.6.9 Core in the frozen execution
checkout with process-local D: TEMP/TMP. This was the only version observed
on PATH (Windows 10.0.26300, .NET 10.0.14); the old 7.6.5 pin would refuse
before START. No tool installation or settings change is
proposed. The reviewed parent starts only the exact collector, with no extra Node flags,
and records bounded raw, encoded and decoded charges and observed closure.
The child checks its tool/cwd/source/owner/Stage/START bindings before
importing the lease and FIRST. No raw local artifacts go in Git.

## Full reserve

Read-only inventory: metadata 2,999,041 B, group 55,168,434 B physical,
joint 737,489,959 B physical, target 12,356,228,504 B and runtime fixture
241 B. Cumulative decoded charge 42,497 B; conservative group/joint carry
31,672 B. The older check records and browser totals remain unchanged.

| Addition or limit | Bytes |
| --- | ---: |
| Entire uncompressed source pair | 54,471 |
| Owner + source review + Stage maxima | 6,144 |
| Full capture/control reserve | 61,440 |
| Total addition | 122,055 |
| Metadata with all reserves | 3,121,096 |
| Current 2,988 KiB cap | 3,059,712 |
| Shortfall at current cap | 61,384 |
| Proposed 3,052 KiB cap (+64 KiB) | 3,125,248 |
| Margin under proposal | 4,152 |

The 61,440 B reserve keeps all raw/encoded/decoded output and START,
aggregate, result, STOP and root-review records at their full limits; no
typical-output discount. Group forecast including carry is 55,322,161 B
under the unchanged 64 MiB limit. Joint forecast including carry is
737,643,686 B under the unchanged 724 MiB limit. The original-baseline 4 GiB
target growth, 8 MiB fixtures, 576 KiB older check records and browser
allowance are unchanged. Fresh accounting must pass before retention and
again before the child. The current cap remains active until a new decision.

A passing packet would test only the shared injected lease core. It would
not verify production Windows filesystem behavior, the pre-embed copy path,
stage freshness/late-operation wiring, native IPC/WebView, model quality,
Android, packaging or the full D04/D09 or desktop gates.
