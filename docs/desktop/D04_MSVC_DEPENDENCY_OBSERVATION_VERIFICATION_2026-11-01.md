# Same32 dependency observation: completed bounded packet

Refs #25 D04.01/.02/.04 supporting, #31 D09.03 supporting, #21; PR #346.
Tested source `025fe3101fce7f9f510afe655bc49692a6b9d815`.
Owner call_2271406f7a15456f8e55c6ad9d2d8bc4 approved ONLY+176KiB metadata and
ONE bounded same32 packet. The grant is **SPENT**. Actual cap is now2048000B
(2000KiB); every other limit and all prior output remain unchanged.

The packet passed99 gates (52 cohort+32 projection rerun groups,15 new observer
groups) before constructing the real adapter/state. It completed the same32
inputs/64 strict-profile attempts, exactly matching all saved PR334 rows and
whole metadata digests before projection. Complete facts contain71 references
across9 names. **ucrt.lib and vcruntime.lib are outside the provided15-entry
catalog**; their existence/location on the machine was not checked. No extra
lookup occurred. The capture passed; DEFAULTLIB resolution/selected link closure
and all qualification flags remain false. Author stays Disabled.

## Actual result and interpretation

| Check / observation | Result |
| --- | --- |
| FIRST summaries |52/52,32/32,15/15; no failed IDs |
| Cohort |32 ordered inputs,64 attempts, live job, null critical |
| Strict/profile baseline |13 strict successes+19 refusals;32 profile parses;32/32 full row matches |
| Job input / selected read bytes |359493030 /718986060; exact two-scan reservation |
| Job sections |1227142 of2097152, both modes charged |
| Dependency facts |32 graph rows,71 references,9 names,2 outside catalog |
| Child |PID61280, closed, exit0; observed completion5424ms of60000ms |
| Output |10484B stdout,0B stderr, complete raw/base64 |
| Failure flags |unknown/timeout/overflow/kill allfalse; postflight null |
| Target/runtime growth |0B/0B |

| Name ID | Name | Provided catalog slot |
| --- | --- | --- |
|0 |kernel32.lib |18 |
|1 |msvcprt.lib |28 |
|2 |msvcrt.lib |29 |
|3 |oldnames.lib |30 |
|4 |ucrt.lib |null |
|5 |uuid.lib |25 |
|6 |vcomp.lib |31 |
|7 |vcruntime.lib |null |
|8 |ws2_32.lib |32 |

The two outside names occur in observed slot29's metadata, alongside kernel32
and msvcrt. A self-reference is retained as a graph fact, without recursion or
link-member selection. Seven names match existing catalog records; this does not
prove search resolution, ABI compatibility or a linker's chosen inputs. Outer,
inner and facts qualified/linkQualification/closureComplete flags all stayfalse;
allReferencesInProvidedCatalog=false. No missing-file claim is made.

Projection pins SHA256
`fa5a21e1bbe3ffb76618ed086b8bdb5096be623967b88f3051811b4e54a15202`;
catalog SHA256
`c28391bc7b508761d10915b66229f8ab20144f38217f1549cf0aa368faf5ab45`.
Root independently rebuilt these from retained PR334/original roster JSON,
checked all32 saved rows,71 edges/exact referenced union, provided slots and
unresolved indices, seven actual source proofs/seven inner couplings,36 fixed
historical hashes, source/Node/normal identities, whole canonical JSON+LF and
complete raw/base64/snapshot agreement. This was retained-data readback, not
another SDK lookup or binary parsing pass. Independent retained-record text/data
review found no coherence issue; Root performed byte/hash/inventory checks.

## Exact sources, environment and command

Sources and complete [admission history](D04_MSVC_DEPENDENCY_OBSERVATION_ADMISSION_2026-11-01.md)
remain frozen. Reader65151B/SHA
`50fcae73eb362dbb7b116116e0fe0ecffe5708f758ad678d2301c0674f202be6`;
supervisor45718B/SHA
`a5a7ef6fc9caa58934845e68dec0cf8e327b656fd05ca65dbc3be23d9aa970f9`;
observer FIRST17704B/SHA
`8f1b6c3ccc96dbe3e1dbc2073895e45668212ffe0c506dee020288797432ee31`.
Accepted helper9972,cohort FIRST7ca,projectionf4,projection FIRSTafee unchanged.
Original12/14 FIRST authorship and every original assertion/ID remain in Git.
Source-only/UNRUN comments describe the frozen pre-execution authorship, not the
current status; the tests were not edited to rewrite that history after the run.
The preflight source-review record's newCases99 means TOTAL packet gates;
84 groups were rerun and15 observer groups were new.

Windows NT10.0.26300 x64; PowerShell7.6.5; pinned Node24.22.1 SHA
d702daa815eabbff763c7d3808e235cf031cf2ca70211b56847bc72f51e240e5.
Actual invocation after real owner/source/Stage/fence/full-reserve admission:

```powershell
$env:TEMP='D:/Dev/_Temp'
$env:TMP='D:/Dev/_Temp'
# cwd: existing physical source-resource-metrics-review at frozen7051d46.
$packet='D:/CodexLocalLore/01a165d9-ff25-7500-a550-1099087d4e37/author-integration-artifacts/d08-fork-native-20261030-v1'
& "$packet/b2-msvc-dependency-observation-supervisor-v1.ps1"
```

One supervisor invocation and one fixed Node child, no separate syntax/test
child or retry. Seven nonempty Node override variables refused. Imports came
from the separate ForkReview at tested source; TEMP/TMP were process-local.
UTC bookkeeping timestamps2026-11-02T05:51:44.8798953Z–05:51:53.0023247Z
(November1 local evening) include output recording; they are not the5424ms
child stopwatch. Logical guard hashing is separate from selected read bytes,
as disclosed in admission; no physical-disk, memory or inference benchmark.
Installed tools/global caches/system configuration were unchanged; the two
frozen runtime source copies were retained only as admitted.

Actual source retention matched both approved hashes. Full retained-source
reviews and PowerShell ParseFile0errors preceded launch. Source-string assembly
refusals/bad drafts and review-recovery refusals remain in chat history; no
candidate was executed to repair them. Fresh actual admission1915135B metadata
+126976B full reserve =2042111B, leaving5889B. All global/prior-START/own-START,
source/tool/normal, physical path and storage guards passed. The normal image
remains unlaunched/SHA7a68992bc35d2e778d71e8db80ef4050a281d65d785a054e77abb569aadaf192.

## Local evidence and charged retention

All leaves below have prefix `b2-msvc-dependency-observation-` in the existing
packet. Raw local diagnostics and machine paths stay outside Git.

| Leaf | Bytes | SHA256 |
| --- | ---: | --- |
| owner-decision-v1.json |1241 | `8bd154e97622547a0249ae7cefb73f3698a3d4601248687904a1b31950fcca63` |
| source-review-v1.json |686 | `5abea2fb734a65d49e04c1a11fe916cc6977c47f244d983cb7fcc612f211331b` |
| stage-v1.json |565 | `50a74e91c71b8afb0f1eb243ce0ae373dcfe8ac060e53632d391af008b211d87` |
| start-v1.json |616 | `f72fb9e9a1b03eb0c29714b14f098382f868f6dc28a9165241cc78dce1c82e00` |
| process-v1.json |16690 | `23c7b42634ed2a986a784634f864cbb185414e8cc0eb3e29dbc16f97092a9926` |
| result-v1.json |513 | `143f6242b2a136fdf982efd88a3514679cc7360f7e80ff9ce36de398bea2d21f` |
| snapshot-v1.json / stdout-v1.bin |10484 each | `47b15b415307185f21eb0c06842c26cfc9021f8cb2454830b474b32a203e5391` |
| stderr-v1.bin |0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| root-review-v1.json |1237 | `ee56cfb05b735ba10fd1483c20c491750e8d211189e5a83010875865e4dfcda0` |

Final **charged metadata1965643B of2048000B**, leaving82357B. It includes prior
decoded allowance18014B plus NEW10484B; future cumulative allowance is28498B.
`result.after` already includes the new decoded charge but predates its own513B
result and the1237B Root review. Physical group54149035B/joint736470529B;
conservative latest log charges17673B give54166708B/736488202B, below unchanged
67108864B/759169024B caps. Target12356228504B remains below original-baseline
12554947872B ceiling; runtime fixtures210B plus prior671744B remain within8MiB.
Old records physical549989B/logical570664B within576KiB and browser41584016B
are unchanged. No output/failure/source/recovery data was deleted, compressed,
relocated or reclassified. Future gates must carry NEW10484B forward.

## Remaining work

This is complete same32 metadata/dependency-fact capture. It is not complete
DEFAULTLIB resolution, selected-link closure, ABI/build/worker/runtime, real
inference, native UI/IPC/rendering, Android/device/OS-offline or story-quality
qualification. A clean checkout cannot reproduce this machine-bound admission
ledger; full D09 reproduction remains separate. Rust/Host/canonical state,
persistence, observer permissions and model capability are unchanged.

Next runnable source work is a bounded fixed-two-name resolution contract for
ucrt.lib/vcruntime.lib under the established search rule, keeping original
root/provenance/order and budgets. It may report unknown/unavailable facts;
no new lookup/read/job reset/build is permitted under this spent grant. Any
additional input observation requires a separately reviewed finite admission.
Full D04/D09/desktop and human narrative-quality gates remain open. No app,
model, native build, device, settings/release/deletion or desktop control occurred.
