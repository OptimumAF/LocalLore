# Worker artifact recipe v1: actual bounded code verification

Refs #25 D04.01/.02/.04; #31 D09.03/.05 supporting; #21; PR379.
**ONE approved code packet PASSED on November 3, 2026 / grant SPENT.**
This verifies pure argument data and compatibility, not a native build.

## Source, authority and admission

Tested source `6c68578b3ae18f04f6b6fea0c111760891446387`, producer
`aee17812`; independent FIRST `31cab4d8` / integration `f7adc150` froze
326 lines / R01–R16 BEFORE the producer. The accepted binder/parser/readers,
C++ worker, normal worker and profiles were unchanged. No fabricated RED.

The owner directly answered the question `call_e5b0cef6361f45e7bfc1f539caa5c283`:
“Approve one bounded code packet for PR #379 under the same evidence cap and all
other unchanged limits. Preserve all prior output and failures, and continue.”
This authorized one code-only packet, SAME 2796 KiB / 2,863,104 B evidence cap;
all other limits stayed unchanged. Every prior failure/output was preserved.

Read the [contract](D04_WORKER_ARTIFACT_RECIPE_V1_CONTRACT_2026-11-02.md) and
[historical admission](D04_WORKER_ARTIFACT_RECIPE_V1_CODE_ADMISSION_2026-11-02.md)
for exact source identities, interfaces, finite cases and allocation forecasts.
After volatile session state reset, Root recovered the exact reviewed literal
pair from this chat's retained record as DATA, without evaluating it. Both
whole programs were exclusively retained uncompressed, with byte/SHA equality
checked before and after writing: supervisor 43,437 B / `f063cb12...`;
collector 5,526 B / `33bea292...`. An independent reviewer read the actual
supervisor in contiguous untruncated chunks and the complete collector before
truthful review/owner/Stage records. That was text review, not hash verification.

Fresh Root checks passed all 147 fixed pins, existing narrow failure fences,
six source bindings, Node and normal unlaunched image hashes. Initial metadata
2,743,728 + full 116,547 B reservation = 2,860,275 B, 2,829 B spare.
After actual source/envelope retention, pre-START metadata was 2,794,837 B;
the FULL 61,440 B run reservation left 6,827 B. Actual envelopes were owner
1,158 + source-review 604 + Stage 384 = 2,146 B, within the 6,144 B allowance.
Before the child, the parent retained all unconsumed reserve minus the actual
402 B START, without reducing it to typical output sizes.

All 822 pre-START files were bound to the exact ordered name/SHA roster:
`ccc51102c0006695e25cfb692438363a8a16a10855636c80fad6cff4025ca4e2`.

## Exact execution and result

Existing physical D: frozen legacy checkout `source-resource-metrics-review`;
process-local TEMP/TMP `D:/Dev/_Temp`. One no-argument invocation:

```powershell
& '<existing charged packet>/b2-worker-artifact-recipe-v1-code-supervisor-v1.ps1'
```

The packet is the existing local `d08-fork-native-20261030-v1` evidence group.
The placeholder keeps private workspace paths out of Git. These are the actual
invocation semantics, not authority to repeat it: fresh authority, retained
reviewed inputs and full admission are required for any future execution.
Terminal session 36202 yielded and was polled through the SAME handle to exit 0.
There was exactly one supervisor invocation and one direct Node child.

Environment: PowerShell 7.6.5/Core; Node 24.22.1 SHA256
`d702daa815eabbff763c7d3808e235cf031cf2ca70211b56847bc72f51e240e5`.
All seven Node overrides were empty. No tool/version/download/settings change.

| Actual synthetic suite | Executed | Passed | Failed |
| --- | ---: | ---: | ---: |
| Unchanged prelink binder E01–E16 | 16 | 16 | 0 |
| New artifact recipe R01–R16 | 16 | 16 | 0 |
| Total, one child | 32 | 32 | 0 |

All finite failed-ID arrays were empty. The unchanged 244 binary-reader cases
were NOT rerun. New cases check the exact six DATA descriptors, 31 compile /
29 link / 4 manifest arguments, includes/pathmaps/archive and SDK-name order,
output/pre-embed requirements, detached deep freezing, unsafe lexical paths,
DOS devices, inclusive 1,024 B path / 255 B component and +1 controls,
multibyte and whole-output bounds. The FIRST's independent expected arrays
were frozen before production code.

Child PID 31716; exit 0, known closed, stdout 370 B / stderr 0 B.
No timeout, overflow, kill, I/O error or unknown closure. The unchanged bounds
were 30 seconds and 4,096 B per stream. Capture stopwatch 560 ms; receipt
begin `2026-11-03T15:55:53.2780341Z`, end
`2026-11-03T15:55:55.7455605Z`. Receipt intervals include record work;
no whole-parent duration, RSS/GC/heap or process-tree containment is claimed.
Raw, Base64 and canonical summaries were retained losslessly.

## Root audit and retained receipts

The read-only Root audit passed on its first attempt: six sources/envelopes,
raw/Base64/canonical equality, both 16-case summaries, actual one-child
aggregate and all owner/Stage/START/result bindings, exact counts and empty IDs.
Both PowerShell Int32 and Int64 were accepted for bounded integral receipt
values, with unchanged expected counts. All 822 prior files matched after
excluding EXACTLY the six new post-START files. The 147-pin/Fence/tool/normal
guard passed again after execution. Target and runtime growth were both zero.
No new failure, STOP exemption, packet rerun or test-source change occurred.

The existing failed runtime-V1, unlaunched V2, padding-V1 and later Root/prep
failures remain unchanged and charged. Nothing was deleted or reclassified.
The Root record is 916 B within its 2,048 B slot. Full local packet receipts
remain outside the checkout; only synthetic curated evidence is committed.

All names below have prefix `b2-worker-artifact-recipe-v1-code-` in that
existing group:

| Receipt | Bytes | SHA256 |
| --- | ---: | --- |
|child-01-process-v1.json|2233|`2e8ea60cb056945a5d3e56916c96fa515ed805cf26ae08da7a5bdf88c1d27197`|
|child-01-stderr-v1.bin|0|`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`|
|child-01-stdout-v1.bin|370|`406bfab09b8637b9ace7f1a9b58b14e74e15afaafcc815a1837ed44b5433f471`|
|collector-v1.mjs|5526|`33bea292fa639c5228dda923bedc65a44b73b5fea4ed3397f7ec244316c70f31`|
|owner-decision-v1.json|1158|`7825a3e4f94446944a4cc58cb98916aa097618f52bef9122312b7655183e436a`|
|process-v1.json|741|`cbf8f5762095f86a8327cd71eb3f6eae755e3806de3c2d50295f94fa50cfd81e`|
|result-v1.json|859|`4252db2db197b8310ccf9fd9a7978ac384023624fd3c5bc9a413bf9e7497cdb4`|
|root-review-v1.json|916|`afc48eff29f3bfa8520bd900e77aef3f08f5edf0ce629cbf5c541749bc19e6ed`|
|source-review-v1.json|604|`eb2b3d9709f0ff57e64adfadea1eab64a6d3c741b3b4d08b3a6e6226a0a2c5bc`|
|stage-v1.json|384|`3631343399a6288df6d3561ea2ad22d2235939d1b38473b710eeab48f3b09856`|
|start-v1.json|402|`5c1e9b3048367c9d9717c1cec8243a4ba97a2567594436d5157cff161930513a`|
|supervisor-v1.ps1|43437|`f063cb128eb508101660c177568a93614d419835ede46e712516634d58c0b110`|

Independent actual-record and public-document reviews are recorded on the PR.
They are source/record TEXT reviews; Root owns hash, inventory and closure
attestations. Model review does not replace human quality acceptance.

## Final storage and unavailable qualification

Final metadata **2,800,728 / 2,863,104 B**, **62,376 B spare**.
Decoded charge 39,268 B; conservative carry 28,443 B. New physical files total
56,630 B plus 370 B new decoded charge explain the exact 57,000 B increase
from 2,743,728 B. Physical group 54,973,350 B / 64 MiB and physical joint
737,294,844 B / 724 MiB; conservative carry remains charged in guard comparisons.
Target 12,356,228,504 B is unchanged under original baseline 8,259,980,576 B
+ 4 GiB ceiling 12,554,947,872 B. Runtime 210 B unchanged; old records
549,989 physical / 570,664 logical B within 576 KiB; fixtures 671,744 B plus
runtime within 8 MiB; browser evidence 41,584,016 B unchanged.
These checks detect excess; they are not filesystem-enforced quotas.

NO SDK/library payload or retained-report binding, compiler/linker/manifest,
worker/model/app/IPC/WebView/render/Android/device/OS operation ran.
Rust/frontend/native/Android checks were not run for this pure Node-only change;
there was no engine, desktop UI, shared interface or Android source change.
No headless/native rendering or model quality claim. No desktop capture/control,
release, downloads, settings change, normal-worker adoption or protected-chat work.

The recipe is lexical DATA: ASCII case folding is not physical Windows or
Unicode path identity, and synthetic argv arrays do not prove native quoting
or compiler acceptance. All qualification flags stay false, with fresh admission
and unchanged normal worker required. Full D04/D09/desktop/human-quality gates
remain open, AuthorDisabled; PR366 remains uncompiled/unrun.

Next runnable task: source-only fixed coordinator and independent finite tests
for actual inputs, quoting, storage, output/pre-embed and supervised six-child
build lifecycle. Any SDK/input observation or build requires its own reviewed
admission and finite owner decision; this grant is SPENT.

