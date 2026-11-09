# D04 manifest port v1 Windows packet admission

Refs #25 (D04.01/.02/.04), #31 (D09.03/.05) and #21.
This is the proposed next packet for [PR #403](https://github.com/OptimumAF/LocalLore/pull/403).
The run remains unadmitted. PR #400's single-run grant is spent.

## Fixed execution and evidence

Use the pinned Windows x64 Node 24.22.1 binary and the installed PowerShell
7.6.9 Core supervisor, in the frozen execution checkout with D: TEMP and TMP.
The supervisor offers exactly one Node child with the collector as its only
argument. The child has a 30-second deadline, up to five seconds for drain,
and a 4,096-byte cap for each stream. No interactive window is needed.

1. Bind the exact owner, Stage and START records, source hashes and process
   environment. Run M01–M12 through the existing manifest FIRST, with the
   actual coordinator, lease and copy cores and in-memory adapters. Emit the
   canonical synthetic result before proceeding.
2. Require all 12 passes. Recheck the nine sources and the owner/Stage/START
   hashes. Check the physical temporary parent and the absence of the one
   fixed fixture root. Import the Windows runner only at this gate.
3. Create only the fixed new parent
   `D:/Dev/_Temp/locallore-runtime-resource-manifest-port-v1-20261109-v1`
   and its two recipe candidate roots. The real lease creates both 167-byte
   owner markers. The runner writes three fixed files for A, then calls the
   real manifest port for index 2. After A settles successfully, repeat for B
   at index 5 on the same signal. Each direct port call has its own five-second
   timer and awaits actual settlement after abort.
4. Verify the exact roster totals 334, 340, 342, 348 and 350 bytes. Bind each
   of the two production copy receipts, read back both two-byte copies
   through held handles, await drain and require known marker closure.
   Emit the distinct canonical Windows filesystem result.
5. After the Node child has closed, independently verify the exact ten
   retained files, both marker sizes, the eight non-marker hashes, and the
   350-byte runtime delta. The child verifies the held marker contents.
   Preserve partial output and raw receipts on refusal and stop the packet.

The six inputs are fixed ASCII bytes. A has `a`, `A\n` and `ma\n` in
the object, executable and manifest roles. B has `b`, `B\n` and `mb\n`.
The names come from the accepted recipe. Each input has one positional write
on an exclusive `wx+` handle, with sync, held identity and known close.
The real copy creates two additional two-byte files. The 350-byte limit is
logical content. The parent separately requires at least 1 MiB free on D:
before START and again before the child offer.

The two success records are separate, ordered JSON lines. Failure can leave
only the synthetic record or add a typed Windows phase and closure result.
The Windows `bytes` field is the last verified roster total, so partial
retained bytes may exceed that reported value. The parent inventory is
authoritative for actual storage. Keep every partial file and STOP record.
There is one offer and no retry, alternate root, reuse or overwrite.

The packet exercises actual Windows Node filesystem operations and the real
manifest port on literal files. Compiler, linker, MT, native worker, model,
app, IPC/WebView, Android and desktop qualification remain separate gates.

## Source and record pins

The production branch is the independently reviewed manifest port at
`aa78a843` with the Windows runner from `7fd1e4e1` and its independently
reviewed held-handle access correction at `77bd89c8`. The seven public
source bindings are exact.

| Source | Bytes | SHA-256 |
| --- | ---: | --- |
| `worker_artifact_manifest_port_v1.mjs` | 16,858 | `e0f90d3ab573b0872e918ee4f5df123cfe3ddb98967a2d5fa1f55d0ca41b5107` |
| `worker_artifact_manifest_port_v1_first.mjs` | 37,684 | `09b46d22234e64430e4a06890828023b81983a9d315bf42a5c8ff641f3141e28` |
| `worker_artifact_manifest_port_v1_windows_first.mjs` | 12,138 | `44f17a38d605d61b8435b915d764a7af9342721eaf165e7966b98139513273eb` |
| `worker_artifact_coordinator_v1.mjs` | 14,268 | `d9baa194f71d796579c3e038d7e2d04b5bfe72d123e5637518757e7e1a8a9088` |
| `worker_artifact_recipe_v1.mjs` | 6,477 | `93269f12448f4539c8b1e1ec035cd0d8da522740eff979b38b525db02fbb622b` |
| `worker_artifact_output_roots_v1.mjs` | 15,919 | `fc79d4f73e10d2ab628162f08cf95d0c4746017df50eaa4813ce53f43fee5642` |
| `worker_artifact_preembed_copy_v1.mjs` | 15,653 | `cbb64bab4b85926c47c38d01848cd9e516becdffc12c763b04ecf0c5a506a4dc` |

The proposed private sources were prepared as literal data in memory.
Retain the complete exact pair only after an explicit grant, then verify
both byte arrays and hashes and have an independent reviewer reread the
actual retained pair. The owner and Stage receipts both bind 350 fixture
bytes. START binds the approved owner, Stage, source revision and parent.
Record the grant as spent before the one supervisor invocation, including a
pre-START refusal. Keep source review distinct from execution.

| Private source | Bytes | SHA-256 |
| --- | ---: | --- |
| Supervisor | 54,200 | `80c5f5263caa6c32c2c40c960e12e06e87eaf571a351cdd489c859f3a5c9c7d6` |
| Collector | 7,474 | `1b7965504640deb60ba6e31d0451dc90e62d81ec5aa778c42a60c0fa2e465b32` |

Use the existing evidence group with the new local prefix
`b2-worker-artifact-manifest-port-v1-packet-`. The parent carries forward
all 195 prior regular pins and the twelve PR #400 records. The separate
historical failure and unlaunched guards are inherited intact. No new
historical exception is requested. All sources, installed tool, normal image,
prior packet files and failure fences must be verified again before launch.
The stored programs and records use exclusive creation.

## Full reserve

Fresh read-only inventory found 877 prior top-level files and an absent
packet prefix and fixture root. Charged metadata was 3,060,788 B. The physical
group and joint were 55,230,062 B and 737,551,587 B. The cumulative decoded
charge is 42,616 B, and the conservative group and joint carry is 31,791 B.

| Metadata accounting | Bytes |
| --- | ---: |
| Complete uncompressed pair | 61,674 |
| Owner, source review and Stage maxima | 6,144 |
| Full capture and control reserve | 61,440 |
| Complete addition | 129,258 |
| Charged forecast | 3,190,046 |
| Existing cap (3,052 KiB) | 3,125,248 |
| Shortfall at existing cap | 64,798 |
| Proposed cap (3,116 KiB) | 3,190,784 |
| Margin under proposal | 738 |

The charged group forecast is 55,391,111 B under 64 MiB. The charged
joint forecast is 737,712,986 B under 724 MiB, including the complete 350-byte
fixture reserve. The combined fixture charge would be 672,335 B under 8 MiB.
The target remains 12,356,228,504 B against the existing original-baseline
ceiling of 12,554,947,872 B. The browser and old check allowances remain
at their approved values. The 61,440-byte run reserve covers full raw,
encoded and decoded streams and the existing bounded control records.
Use the full reserve before retention and again before START and child
offer, with no forecast discount based on the usual small output.

Only the proposed 64 KiB increase and one fixed packet require a fresh
decision. All checks and fixture creation remain pending until approval,
actual retained-source review and fresh admission.
