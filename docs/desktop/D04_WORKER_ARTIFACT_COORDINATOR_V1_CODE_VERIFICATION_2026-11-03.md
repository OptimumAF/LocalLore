# Worker artifact coordinator v1: actual bounded code verification

Refs #25 D04.01/.02/.04; #31 D09.03/.05 supporting; #21; PR390.
**ONE approved code packet PASSED on November 3, 2026 / grant SPENT.**
These are synthetic coordinator journeys, not native Windows build execution.

## Source, authority and preserved chronology

Tested head `0f79fff509a44ab1adc42b68cb4c753fb8beca8b`, corrected sourcee3e889ff.
The [contract](D04_WORKER_ARTIFACT_COORDINATOR_V1_CONTRACT_2026-11-03.md) and
[historical admission](D04_WORKER_ARTIFACT_COORDINATOR_V1_CODE_ADMISSION_2026-11-03.md)
record exact interfaces/source hashes, cases, limits and full reservation.

Independent518-line FIRST author8c1168cb / integrationeb6b4b6a froze20 C01–C20
and passed full text review BEFORE original255-line producer532b7747.
Source review found a real defect: timer cleanup could overwrite an earlier
timeout/grace failure. Original source remains in history; it was NOT executed
as a behavioral RED. Contract8b9e931d clarified first-failure precedence;
independent28 ADDITIVE C14 lines author8d9ff442 / integration1d3c49bb froze
BEFORE targeted fixe3e889ff. All original20 groups/assertions stayed intact.
The corrected256-line module and546-line FIRST passed targeted/full text review.
The six additive cleanup races are included inside C14, not six extra groups.
No producer/FIRST/accepted recipe/binder/whole harness source changed after run.

Owner question `call_e322b1e573a547ac912839d82f3e72f2` received verbatim
`Approve one bounded code packet`: ONLY +64KiB evidence2796→2860KiB /
2,928,640 B, and one code-only packet. All other limits and every previous
output/failure stayed unchanged. No SDK/native/build authority was inferred.

Both WHOLE private programs were exclusively retained uncompressed with exact
byte/SHA checks before/after writing: supervisor45,371B /0cb2e8c4...;
collector6,112B /715b885f... . Independent actual-retained text review read every
supervisor chunk and complete collector before truthful review/owner/Stage.
Reviewers did not recompute Root's hashes, inventory or closure.

Fresh159-pin/Fence/source/tool/normal-image/full-reserve checks passed.
Initial2,800,728 +119,067 full reservation =2,919,795 B,8,845 B spare.
Actual envelopes owner1,200 + source-review772 + Stage389 =2,361 B within6,144.
Pre-START metadata2,854,572 + FULL61,440 run reserve =2,916,012 B,
12,628 B spare. Before the child, ALL remaining reserve minus the actual407B
START was retained. No typical-log discount or second run.

All834 pre-START files were bound to the ordered name/SHA roster:
`e9fbbc3709f48955ed6ae8af040a7d9cd13840821308b167d338d09646866aed`.

## Exact invocation, finite results and closure

Existing physical D: frozen legacy checkout `source-resource-metrics-review`;
process-local TEMP/TMP `D:/Dev/_Temp`. Exactly one no-argument invocation:

```powershell
& '<existing charged packet>/b2-worker-artifact-coordinator-v1-code-supervisor-v1.ps1'
```

The packet is the existing local `d08-fork-native-20261030-v1` group.
Placeholder avoids private workspace paths in Git. This records actual semantics;
any repetition requires fresh authority/inputs/review/full admission. It does
not authorize reproducing this spent packet. Session65615 yielded and was polled
through the SAME handle to exit0; no extra syntax/Node child or retry occurred.

PowerShell7.6.5/Core; pinned Node24.22.1 SHA256
`d702daa815eabbff763c7d3808e235cf031cf2ca70211b56847bc72f51e240e5`.
All seven Node overrides empty; installed tools/global settings unchanged.

| Actual synthetic suite | Executed | Passed | Failed |
| --- | ---: | ---: | ---: |
| Unchanged prelink binder E01–E16 |16|16|0|
| Unchanged argument recipe R01–R16 |16|16|0|
| New coordinator C01–C20, including additive C14 races |20|20|0|
| Total, ONE Node child |52|52|0|

All finite failure-ID arrays were empty. The unchanged244 binary-reader cases
were NOT rerun. The coordinator uses synthetic local ports and a MANUAL clock:
31-call/30-receipt success trace; all14 fresh-proof refusals; new-object directives
before LINK; ordinary exclusive pre-embed before MT; process/ownership/roster/
budget/manifest/compare faults; wrong-step/context/kind/schema/canonical replies;
every boundary cancellation; known versus uncertain closure; deadline/grace and
late replies/timers; single use; captured immutable inputs; evidence failure;
byte/integer bounds; no adoption and bounded complete reports.
The real outer30-second Node deadline and its capture stopwatch are separate
from those manual test clocks.

Child PID19580, exit0/known closed, stdout507B/stderr0. No timeout, overflow,
kill, unknown closure or I/O error. Capture stopwatch319ms; receipt begin UTC
`2026-11-03T16:41:34.7004082Z`, end `2026-11-03T16:41:36.4706669Z`.
Receipt interval includes record work, not a whole-parent duration measurement.
Captured bytes were exactly preserved in raw/Base64/canonical summaries.
The unchanged4096B/stream limit would preserve incomplete bounded prefixes and
fail/stop on overflow; no universal full-log or OS/process-tree quota is claimed.

## Root audit, receipts and storage

Root read-only audit passed first attempt: all8 source/envelope bindings, exact
raw/Base64/canonical and16+16+20 summaries, actual one-child/owner/Stage/START/
aggregate/result links, typed integral counts and empty IDs. Both PowerShell
Int32/Int64 integral receipts were handled with unchanged expected bounds.
All834 prior files matched after excluding EXACTLY six new post-START files.
The159-pin/Fence/tool/normal guard passed again afterward; target/runtime
growth zero. Root938B fits2,048B slot. No new packet/Root failure or retry.
The source-review defect above remains preserved; all historical runtime/
padding/Root/preparation failures and narrow exceptions remain unchanged.

All names below use prefix `b2-worker-artifact-coordinator-v1-code-` in the
same existing group. Actual receipts stay local outside the checkout.

| Receipt | Bytes | SHA256 |
| --- | ---: | --- |
|child-01-process-v1.json|2560|`01ce51e1a34a5fcace4b52299a407081e4f62772e0d31bea691d96546bf97cf2`|
|child-01-stderr-v1.bin|0|`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`|
|child-01-stdout-v1.bin|507|`fd2282c14dd3121a1e1d2fd833ec2a64ce6a0417d44d90b5c03f4b27c68e1d8c`|
|collector-v1.mjs|6112|`715b885f2793c7a3a7a547e3f62fd54c137b962e67986368a7a875692c9aa036`|
|owner-decision-v1.json|1200|`c117f1e35a8d593376be4f56181f8f09904109ef859342e5b3f6bafa444bd428`|
|process-v1.json|746|`b66d6708373c9060e479c5b8465726e9d721a4afa7fccddba64b83d2b21536c4`|
|result-v1.json|864|`de5c89051f5480cfb27256f424781e193791384d1b2b72a32c103173037fc363`|
|root-review-v1.json|938|`b6aa927581b80cfa8134ef74b2156f436ae0955290fc7a29d00b9a1dbacf5c7a`|
|source-review-v1.json|772|`5b87a8eb7fe8d77644524baed857097161627159688e9a9198819dae8a13ca4f`|
|stage-v1.json|389|`dc63daac35a5592408595742b5436a833025de758862b7351edd8318a5b7bc99`|
|start-v1.json|407|`e667226ca80229cb9ce0252fcab6bd72bd455f06adf818b404027b830de40af2`|
|supervisor-v1.ps1|45371|`0cb2e8c439f882871f098107c44f089e2d0ec1c0e548fa10d2a9da42c8243e25`|

Independent actual-source/actual-nine-record text reviews released; public-doc
review is recorded separately on the PR. These are model-assisted reviews,
not human story-quality assessment or independent recomputation of Root's audits.

Final metadata **2,861,101 / approved2,928,640 B**, **67,539 B spare**.
New physical files59,866B + new decoded507B =60,373 B increase from2,800,728.
Cumulative decoded39,775 B; conservative carry28,950 B.
Physical group55,033,216 B /64MiB; physical joint737,354,710 B /724MiB;
guards continue adding the carry to physical group/joint comparisons.
Target12,356,228,504 B and runtime210 B unchanged. Original target baseline
8,259,980,576+4GiB ceiling12,554,947,872 B, old549,989 physical/570,664 logical
records within576KiB, fixtures671,744+runtime within8MiB and browser41,584,016 B
all unchanged. These byte-length checks detect excess, not filesystem quotas.

## What this does and does not establish

The accepted recipe now has tested single-use orchestration and finite synthetic
failure/cancel/late-result/evidence semantics. Trust still resides in the
concrete local development adapter, not in public booleans or historical JSON.
No concrete Windows adapter is supplied by this PR. Fresh physical/tool/env/
ALL input bytes, ordered search/no-shadow and actual newly compiled object
directives still need guarded implementations and observations before build.

NO SDK/library payload lookup/read, retained-report binding, compiler/linker/MT,
worker/model/app/IPC/WebView/render/Android/device/OS operation ran. Rust,
frontend, native and Android checks were not run for this Node-only development
slice and were outside its finite grant. No shared engine/observer/persistence/
memory schema, C++/normal worker/profile or Android source changed.
No rendering/native argv/compiler/artifact/model performance or quality claim.
No desktop capture/control, downloads/settings/deletion/release or protected-chat work.

All qualification flags stay false, requiresFreshAdmission and unchanged normal
worker stay mandatory. FullD04/D09/desktop/human-quality gates remain open,
AuthorDisabled; PR366 stays preserved uncompiled/unrun.
Next task: concrete fixed Windows admit/recheck/input/output/launch adapters,
independent synthetic tests and their separate reviewed finite admission.
Fresh SDK/tool observations and the actual six build children are not authorized
by this spent code packet.
