# D04 worker output-root lease v1 code verification

Refs #25 (D04.01/.02/.04 prerequisite), #31 (D09.03/.05 prerequisite) and
#21. One approved packet passed all 15 synthetic groups R01–R15 at
`9b27f60219f2b2e51c0130c0d98665919f3a4911`. The one-run grant is spent.
See the [approval and spend record](https://github.com/OptimumAF/LocalLore/pull/400#issuecomment-6734165847)
and the [frozen admission plan](D04_WORKER_ARTIFACT_OUTPUT_ROOTS_V1_CODE_ADMISSION.md).

The groups exercise the injected lease core. They cover exact initial and
ready snapshots, A/B root exclusivity and partial preservation, short marker
reads and writes, physical identity drift and aliases, strict file rosters,
exact size accounting through the uint64 boundary, late acquisitions,
cancellation, cleanup uncertainty, the cooperative deadline and the recheck
limit. The Windows filesystem factory was not invoked. Actual root and
marker creation, the pre-embed copy path, coordinator integration, MT,
native app/IPC, model and Android qualification remain separate gates.

## Exact run

PowerShell 7.6.9 Core, .NET 10.0.14, Windows 10.0.26300 and Git for Windows
2.33.0. Node 24.22.1 Windows x64 was identified by its pinned executable
SHA-256 `d702daa815eabbff763c7d3808e235cf031cf2ca70211b56847bc72f51e240e5`.
The execution checkout was the frozen `source-resource-metrics-review`
at `7051d46e754e78e9d9946440a6aae1b37695b3d4`. The public lease and FIRST
came from the separate PR #400 checkout at the tested head.

From that execution checkout, `$packetRoot` denotes the existing private
`d08-fork-native-20261030-v1` evidence group.

```powershell
$env:TEMP = 'D:/Dev/_Temp'
$env:TMP = $env:TEMP
& (Join-Path $packetRoot 'b2-worker-artifact-output-roots-v1-code-supervisor-v1.ps1')
```

The supervisor offered exactly one child with the retained collector as
its only argument. The child loaded the pinned recipe, lease and FIRST,
then called `runWorkerArtifactOutputRootsSelfchecksV1` once. The timeout
was 30 seconds with up to five seconds for drain and 4096 retained bytes
per stream. Node PID 67860 exited 0 with known closure. The capture timer
read 640 ms. The supervisor recorded the UTC interval
2026-11-09T06:55:18.5722984Z to 2026-11-09T06:55:21.7802037Z, which includes
supervisor accounting outside the capture timer. Stdout was 119 bytes and
stderr was empty. No timeout, overflow, kill or I/O uncertainty was reported.
The supervisor exited 0 in the same execution session.

```json
{"version":1,"kind":"worker_artifact_output_roots_first_v1","executed":15,"passed":15,"failed":0,"failed_case_ids":[]}
```

The reviewed inputs are the lease at `e31698fa` (15,919 bytes,
`fc79d4f73e10d2ab628162f08cf95d0c4746017df50eaa4813ce53f43fee5642`),
FIRST at `55c2fc92` (28,864 bytes,
`8b1924ac43383676f3096974531595d3b04672ad17402e54323d8e2d2c130bad`),
and the accepted recipe (6,477 bytes,
`93269f12448f4539c8b1e1ec035cd0d8da522740eff979b38b525db02fbb622b`).
Original FIRST `f260b949` preceded the initial producer `fe62a8f9`.
The additive R11 control preceded the corrected producer.

## Evidence and accounting

The actual retained supervisor and collector were reread in full and
independently reconstructed byte for byte before invocation. The pair,
owner decision, Stage, START, process and result are bound by SHA-256.
Readback verified the raw and Base64 streams, exact JSON summary and
receipt chain, all 865 pre-existing top-level files, and unchanged normal
executable, target and runtime totals. The first read-only preflight had
a PowerShell path-array construction error. The corrected preflight passed
before any packet output was written. There was one supervisor invocation
and one child, with no test rerun.

| Accounting | Bytes |
| --- | ---: |
| Metadata before retention | 2,999,041 |
| Full proposal including all reserves | 3,121,096 |
| Approved metadata cap | 3,125,248 |
| Metadata after source and envelope retention | 3,055,224 |
| Full run reserve at invocation | 61,440 |
| Actual added physical bytes | 61,628 |
| Actual added decoded charge | 119 |
| Final charged metadata | 3,060,788 |
| Remaining metadata allowance | 64,460 |
| Final physical group / joint | 55,230,062 / 737,551,587 |
| Final group / joint including carry | 55,261,853 / 737,583,378 |
| Target / runtime fixture bytes | 12,356,228,504 / 241 |

The cumulative decoded charge is 42,616 bytes and the conservative carry is
31,791 bytes. The prior roster digest is
`a398df697980a75a7b6e8da01b08fcdfda41d06df8858f232db7fef5d48cf4c4`.
The target, group, joint, older code record, fixture and browser ceilings
remain at their existing values. The normal app executable hash is
`7a68992bc35d2e778d71e8db80ef4050a281d65d785a054e77abb569aadaf192`.

The retained files use the local prefix
`b2-worker-artifact-output-roots-v1-code-`. The result's inventory is
pre-self-write. Its 3,058,275 bytes plus the 865-byte result and 1,648-byte
root review reconcile to 3,060,788 bytes.

| Retained suffix | Bytes | SHA-256 |
| --- | ---: | --- |
| `child-01-process-v1.json` | 1,658 | `cd82dad305ed1830edd3c985e48186530aadf7fed37457ad78a4c6e9504c1e7a` |
| `child-01-stderr-v1.bin` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `child-01-stdout-v1.bin` | 119 | `190476d93d6dde57679f861bd5d7263f1c6f63e9f87c2cf7f34277a124857509` |
| `collector-v1.mjs` | 5,103 | `86f6b16ef7a53fa1e5e07f35131aca2acf67f1ddfaed6503f411a5d3a1b076a8` |
| `owner-decision-v1.json` | 875 | `183d8aae7b4d5016ccce2344a299209dd58cc6e9460539257ad0fa17fb5030eb` |
| `process-v1.json` | 747 | `f26392746709bb7a7d22fd6e773c1f5738ce39e23cdc39c167fe4ad0bd719c03` |
| `result-v1.json` | 865 | `2f2cd656bc7cba404e85e4035b254d267070a9ae883c396e40c9c50f9fbf5d94` |
| `root-review-v1.json` | 1,648 | `c8b603f470fd2498b8a16efd16bed1fccba7d16d2fb001f9188b209f7311c100` |
| `source-review-v1.json` | 447 | `9a814c685f1787e4d8e070b6cab33ccdb646adc14bbcf6b05b4b47db9a8ab24e` |
| `stage-v1.json` | 390 | `86c0d1d7a7f3d6c87f260e90ed150c8ccb9596b0ccc68a2f616e11089e5dab7a` |
| `start-v1.json` | 408 | `85e38d90522407d66ee12f093672a4d8781a9da1b3081b630c58bcfd2bc0271a` |
| `supervisor-v1.ps1` | 49,368 | `678ec9153c7b0e2c4ae6328f304cc3c62f88ae23184bbcee6c0cc756cfff6e54` |
