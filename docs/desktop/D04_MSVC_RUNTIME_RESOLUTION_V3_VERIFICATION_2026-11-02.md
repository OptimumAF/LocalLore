# V3 fixed-two runtime metadata: actual verification

Refs #25 D04.01/.02/.04 supporting, #31 D09.03 supporting and #21;
[PR348](https://github.com/OptimumAF/LocalLore/pull/348).
Tested source: `cced53936c5609498cc15a90c89e188613468c2f`.

The ONE approved V3 packet **PASSED complete capture**: 6/6 independent parent
groups, 24/24 independent Node groups, two acquired inputs and four actual
strict/profile attempts. Only `vcruntime.lib` produced profile metadata.
`ucrt.lib` retained a known profile refusal. Both files now provide name-presence
matches, but their dependency metadata is not wholly available. All qualified,
linkQualification and closureComplete flags remain false; Author stays Disabled.
This supporting result does not accept full D04, D09 or the desktop epic.

The V3 run grant is **SPENT**. There was no retry. Its actual owner decision
superseded V2's unused grant; V2 never launched. The earlier V1 FAILED packet,
its incomplete START and CODE2_STOP, and all four unlaunched V2 files remain
unchanged. Their thirteen exact historical pins and required absent outputs
were checked under the narrow V3 authority; no other stop was waived.

## Actual action and outcome

The approved action followed the
[V3 admission](D04_MSVC_RUNTIME_RESOLUTION_V3_ADMISSION_2026-11-02.md) and
[frozen contract](D04_MSVC_RUNTIME_RESOLUTION_CONTRACT_2026-11-01.md).
One PowerShell supervisor wrote immutable START, loaded the fixed hashed parent
FIRST definitions and retained the canonical 6/6 summary. Only then did it start
one fixed Node child; that child passed 24/24 before creating its production
state/job/SDK adapter. No separate syntax or version-query child was launched.

| Recorded check | Actual result |
| --- | --- |
| Parent FIRST |6 executed, 6 passed, 0 failed; empty IDs |
| Node FIRST |24 executed, 24 passed, 0 failed; empty IDs |
| Candidate probes |6 ordered probes; first existing entry selected for each name |
| New accepted job |2 inputs; 324066 input bytes; 4 attempts; 123 sections; stopped=false |
| New selected-file scans |648132 actual bytes, equal reserved bytes for two full scans |
| Search/final identity guards |finalVerified=true; no current-directory library shadow |
| Owned Node process |PID 53236; closed=true; exit 0 |
| Child output |4481 B complete stdout; 0 B complete stderr |
| Failure flags |unknown/overflow/timedOut/killAttempted all false; no report/postflight error |
| Output growth |target 0; runtime fixtures 0 |

Both inputs were read through their admitted read-only held handles, with
canonical root/leaf/size checks, two matching scan digests, first-cause-preserving
close and post-inspection Buffer/final identity checks. Their sizes and hashes
were NEW observations from this packet, not pre-established payload pins.
The old 32 payloads were not reread. Their prior 32/64 job, metadata pins and
71 graph references remain separately bound historical evidence. This packet
does not form a single 34-input job or a simultaneous fresh observation of 34 files.

Root's completed audit read back retained records, canonical raw/Base64
couplings, source/owner/Stage/START references and final accounting. It did not
rerun SDK parsing. Its receipt records 15 report proofs, 48 prior pinned files,
13 V1/V2 history pins, unchanged source/tool/normal bytes and preserved prior
output. Independent record review also released. This verification document
was authored from those retained records and source text, without another
suite, parser, payload read, hash audit or inventory run.

## Newly observed inputs and unavailable metadata

Root indices are zero-based positions in the original fixed five-root recipe.
No later root was probed after selection. No recursive DEFAULTLIB lookup ran.

| Global request | Selected root | Bytes | Strict outcome | Profile outcome |
| --- | --- | ---: | --- | --- |
|33: `ucrt.lib` |3: Windows SDK 10.0.19041.0 UCRT x64 |285588 |Format refusal, `archive_padding_byte` |Same known refusal; metadata unavailable |
|34: `vcruntime.lib` |1: MSVC 14.34.31933 x64 |38478 |Format refusal, `coff_relocation_pointer` |Parsed 8 objects/74 imports/68 sections |

The observed input SHA256 values are:

- `ucrt.lib`: `7ef4eac926bf597d2f243f16cdfed7e0db22cb3ca34a1d7e088a84c994a03d66`.
- `vcruntime.lib`: `d8fe742a11b6babde717141b9316702fca0a876c7ef68055e9aedac66f31768c`.

For `ucrt.lib`, both mode refusals retain memberIndex=4/memberOffset=98452,
sectionIndex=null, sections=0, directiveBytes=0/tokenCount=0 and actual/limit=null.
The member offset identifies the archive member header; the report does not
retain the offending padding byte's position or value. The unchanged helper
checks archive padding at `archive_padding_byte`; the refusal site alone does
not establish a format-policy correction or justify relaxing the parser.

For `vcruntime.lib`, the strict refusal retains memberIndex=5/memberOffset=27372,
sectionIndex=2, sections=55, directiveBytes=6/tokenCount=0 and actual/limit=null.
The successful profile has 0 directive tokens, 0 DEFAULTLIB names,
unknownMachineObjects=0, unusedRelocationPointers=2 and terminalNulSections=0.
Its full metadata SHA256 is
`cceeefd36214a8d2f01d11df72376377d27d4280232d8c2534b424af0eebd782`.
The total job charge 123 includes 55 from the refused strict attempt and 68 from
the profile attempt. A refusal does not refund declared work. The two unused
relocation-pointer deviations are metadata observations, not ABI/link approval.

The compact facts preserve all nine prior names. `ucrt.lib`/`vcruntime.lib`
map to new provided slots 33/34; the other matches retain the historical old 15
catalog's provenance. `allKnownNamesProvided=true` is this explicit name join,
not a fresh attestation of every old library or evidence of complete resolution.
`bothProfileMetadataAvailable=false`: request 33's libraryIds is **null**, while
request 34's libraryIds is **[]**, an observed successful empty list. Unknown
dependencies of the refused `ucrt.lib` must not be inferred absent. All three
qualification/closure flags stay false despite complete capture and name presence.

## Timing and environment

The process record's observed child completion is 1360 ms under the 60000 ms
deadline, with no kill or drain required. Its UTC started/ended fields are
`2026-11-02T17:29:13.7447264Z` and `2026-11-02T17:29:16.4752288Z`:
the 2.7305024 s receipt interval includes work after the child stopwatch stopped.
It is distinct from the 1360 ms child interval. The outer wrapper wall time was
not measured; poll session 99324 closed with exit 0. None of these values measures inference,
linker or application latency. Process-tree containment is explicitly false.

PowerShell 7.6.5/Core was enforced by the running supervisor. Node 24.22.1 used
the pinned executable SHA256
`d702daa815eabbff763c7d3808e235cf031cf2ca70211b56847bc72f51e240e5`;
no extra Node version command ran. Windows NT 10.0.26300/x64 is the inherited
observation from preceding accepted evidence, not a new OS qualification.
Physical D: cwd/temp and all seven Node override refusals remained enforced.
The unchanged unlaunched normal image stayed pinned to 7a68992b.

The actual operator command was this sanitized fixed-path invocation from the
physical legacy checkout, using its existing approved D: chat root:

```powershell
$env:TEMP='D:/Dev/_Temp'
$env:TMP='D:/Dev/_Temp'
$chatRoot='D:/CodexLocalLore/<existing approved chat root>'
Set-Location -LiteralPath "$chatRoot/source-resource-metrics-review"
& "$chatRoot/author-integration-artifacts/d08-fork-native-20261030-v1/b2-msvc-runtime-resolution-v3-supervisor-v1.ps1"
```

This records the spent invocation; it authorizes no repeat. Source/proof/tool/
normal-image hashing is separate from 648132 selected-payload bytes, with no
claim that the 1 GiB selected-read limit covers every filesystem read. The two
scans and identity checks are cooperative observations, not a filesystem lock
or atomic snapshot.

## Exact sources and retained evidence

All local packet files remain uncompressed in the SAME charged
`author-integration-artifacts/d08-fork-native-20261030-v1` under the existing
private D: chat root. Raw machine identities and SDK payloads are not copied
into this public document. Source and record hashes below are Root's completed
audit identities, not new hashes calculated during documentation.

| Tested source | Bytes | SHA256 |
| --- | ---: | --- |
| V3 reader |80928 |`463e0bbb6377dbeb2fc189709c4eafd176826ac06a5fe9036a10ff175c88bff9` |
| V3 supervisor |69156 |`c8c49691f739388766213e53773bd36024a189f1abb5092d6e543d744a9faecc` |
| Accepted helper |16987 |`9972c0eb4d8cf936f252b090a8f0794b0d6b5328a2245b8720cdec32d5fafa53` |
| Node FIRST |42661 |`5070e734a093b0903d050a18b63f1af3ff8f9861c468e7006828939f28e5554c` |
| Parent FIRST |23857 |`653df7938858947d30fb8ec62bd40727c546a2f2b4dd8fc81869114df08b1314` |

File prefixes below are `b2-msvc-runtime-resolution-v3-`.

| Retained record | Bytes | SHA256 |
| --- | ---: | --- |
| `owner-decision-v1.json` |1305 |`45cd0102c2b946f15c778062e43dbd491a6c6e1899541db10599440d299e5f98` |
| `stage-v1.json` |585 |`0688c3d64f9e15c46ce8ab030af6d61890161ac2c5037796d044b35df7dcff94` |
| `start-v1.json` |611 |`182b556ce347dc3bd8acfc68b481506ea4ea48d3d8136c40c0f824d733e4a703` |
| `source-review-v1.json` |889 |`7789b122d60996f82323cb0b4712038176d9533e139ac8e1203a4e16896fb530` |
| `parent-selfchecks-v1.json` |105 |`d9b733d680a09465dc3e0c95280b2537b42d8c32b6464c6151d7cd4fea6a24f7` |
| `process-v1.json` |8430 |`5ad76f4c876abb1b01a0ec9c6a63d076f8ca1fcf07dfd4bea82b5d634db968c7` |
| `result-v1.json` |512 |`05a2a626e3321b69f0befa3aa1dd5924562057236dcdabb77cf1bbf0cc42980d` |
| `snapshot-v1.json` / `stdout-v1.bin` |4481 each |`910f9af0d7030c78cb06095d34134f542eb36c9be9fb29c08ef17f531c262463` |
| `stderr-v1.bin` |0 |`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `root-review-v1.json` |1113 |`b0a8ece87e89af6dd8c02479d153d552e88ff47f1be34bdbab98fc41f2b8d9b8` |

The actual owner answer, `Approve V3 amendment only`, was recorded through
`call_fbeb6f4a18394bc4b5aeaadb185a3930`. It binds the five exact sources,
6+24 groups, the two fixed requests and limits, supersession of unused V2 and the
known V1 failure-review digest. The V3 own-START owner check and STOP guard
use the current fixed stem. No V3 failure marker was needed by this passed run.
The [V1 failure](D04_MSVC_RUNTIME_RESOLUTION_V1_FAILURE_2026-11-02.md) and
[V2 unlaunched source block](D04_MSVC_RUNTIME_RESOLUTION_V2_SOURCE_BLOCK_2026-11-02.md)
retain their exact outcomes and files; neither was retroactively passed.

## Final retained accounting

| Charged item | Actual bytes | Unchanged limit |
| --- | ---: | ---: |
| Metadata, including cumulative decoded 32979 |2440942 |2555904 |
| Physical packet group |54619853 |67108864 |
| Conservative group including 17673 prior +4481 new decoded |54642007 |67108864 |
| Physical joint evidence |736941347 |759169024 |
| Conservative joint including 17673 prior +4481 new decoded |736963501 |759169024 |
| Target |12356228504 |12554947872 |
| Runtime fixtures / runtime+prior fixture charge |210 /671954 |8388608 |

The result's `after.metadata=2439317` already includes 4481 new decoded bytes,
but precedes its own 512 B result. Adding that result gives 2439829; adding the
1113 B Root review gives 2440942. Carry the cumulative decoded charge 32979 into
future admission, including the 4481 new bytes. Target/runtime growth is zero.
All earlier outputs, failures, frozen sources and recovery remain. The activated
2496 KiB cap retains this evidence; remaining capacity grants no new execution.

## Open gates and next source-only task

The next primary work is a frozen archive-padding error-site observation
proposal and contract/format research, with independent cases before any
correction. The current refusal site and file hash are insufficient to infer
the offending byte or relax accepted validation. No further SDK lookup, payload
read or retry is authorized by the spent V3 grant; a later observation requires
its own exact scope, source review, full reserves and explicit decision.

No new Rust, frontend, native IPC/WebView, Android, app/device/OS, model-quality,
compiler/linker or worker checks ran. This is host Node metadata execution,
not native desktop application qualification. No render artifacts were produced
to inspect. No build, inference, deployment, release or desktop control occurred.
Full D04/D09/desktop acceptance and the earlier human needs-improvement findings
remain open; Author remains Disabled. The protected chat and concurrent work
were not changed by this packet.
