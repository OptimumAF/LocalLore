# B2 library-input inspection: proposed bounded admission

Refs #25 D04.01/.02/.04, #31 D09.03 supporting and draft PR309.
**The collector source is reviewed but unexecuted. No new metadata limit or run
is approved by this document.**

The [85-case synthetic inspector result](D04_WORKER_LIBRARY_INPUTS_VERIFICATION_2026-10-31.md)
does not establish actual archive/SDK compatibility. The next step reads fixed
existing library/object files as data, binds a conservative set of SDK/CRT byte
identities, and reports unavailable inputs honestly. It executes no library or
extracted directive. The [artifact build plan](D04_AUTHOR_WORKER_ARTIFACT_PLAN_2026-10-31.md)
remains a later proposal; no compile/link/worker/model/app step belongs here.

## Exact prepared source and scope

The retained local `b2-library-closure-v1.mjs` is28218B, SHA256
`fc344e8abaae475860935a3efe2236552586b5f31b834e6cfc8caff2cdf867fd`.
Root read the whole source, and independent review found no remaining concrete
source blocker. Short file reads accumulate/hash their actual bytes; no false
identity failure is inferred from a valid positive short read. Source review
is preparation evidence, not a syntax-check or SDK execution result.

The source has two closed modes: a parent with no script arguments and one
parent-created `--metadata-child` argument after the fixed source filename.
There is no debugger flag/server, arbitrary command/path argument, renderer
hook or execution of parsed directive strings. The installed Node24.22.1 hash,
cwd, source files, prior85-pass proof, retained V1 refusal and parent PID/START
binding are checked. Node preload/cache/coverage/debug/warning-file redirects
are refused before parent startup and again in the coordinator.

The child reads17 fixed inputs: the two preserved main objects, B1's passing
validator object and seven exact pinned archives in each preserved clean-build
path. The three object pins are explicit, and both seven-archive sets already
match in a separate read-only observation. Reads are sequential; raw buffers
are not stored in snapshots. Each payload is below256MiB or explicitly refused
without loading an oversized payload. Sizes, actual hashes and held-file/path
identity checks are repeated. Read counters remain separate for parent/child.
This is not an absolute OS memory or process-tree containment guarantee.

The current-directory-before-LIB rule is accounted for by refusing any `.lib`
entry in the fixed future native-source cwd. The five fixed search roots retain
their reviewed order: MSVC ATL/MFC x64, MSVC x64, NETFXSDK4.7.1 x64, SDK19041
UCRT x64, SDK19041 UM x64. The collector follows ALL inspected members' DEFAULTLIB
requests recursively, with at most64 resolved/discovered requests processed.
It rejects path/drive/UNC/ADS/wildcard forms, DOS device basenames and overlong
leaf names before filesystem probing. No replacement/default-library suppression
or fallback root is added. [Microsoft library lookup reference](https://learn.microsoft.com/en-us/cpp/build/reference/dot-lib-files-as-linker-input?view=msvc-170).

Missing discovery-only default libraries and unsupported formats/options produce
explicit unqualified metadata; missing expected pins, changed identities, hard
I/O failures, unknown closure or storage failure stop critically. A `capture_limit`
record includes counts and, for an oversized metadata serialization, its required
bytes/full digest. No rows are silently dropped to make a qualified result.
`captureComplete` is distinct from `completeForFixedRecipe`; only
`qualified_superset` can set the latter true. Parent validation checks the full
status/flag/count/row/path schema. No status establishes selected linker members.

The historical/B1 objects are preparatory inputs. A later artifact coordinator
must inspect the NEW experimental object and force the same cwd/LIB order before
LINK. This snapshot cannot authorize that future link or private Author capability.

## Closed prospective execution

First perform one bounded syntax-only check of the exact source with the pinned
Node executable. Only after a complete passing result, perform ONE fixed
read-only collection. No automatic retry, source replacement or extra cohort.
All failed/refused output stays retained; fresh source/proof/storage checks
precede each step.

| Step | Child timeout and drain | Stdout/stderr caps | Complete retained reserve |
| --- | --- | --- | --- |
| `node --check` of the fixed collector |30s, one kill/5s drain |512/4096B |35840B |
| Fixed metadata child |60s, one kill/5s drain |512/1024B |34560B including16KiB snapshot and768B START |

The syntax check executes no collector body. Root will retain complete bounded
logs and a settled known-closure result before collection. All new syntax STARTs
must satisfy the same globally consulted completion fence. Unknown closure stays
unknown, not a passing check. These timeouts cover the child, not an absolute
wall-clock limit on all filesystem admission/hash work.

The actual commands will use the pinned existing Node path, from the physical
D: checkout, after refusing the seven Node environment overrides:

```powershell
$env:TEMP='D:/Dev/_Temp'
$env:TMP='D:/Dev/_Temp'
# $Node is the already provisioned, hash-verified Node24.22.1 executable.
& $Node --check '../author-integration-artifacts/d08-fork-native-20261030-v1/b2-library-closure-v1.mjs'
& $Node '../author-integration-artifacts/d08-fork-native-20261030-v1/b2-library-closure-v1.mjs'
```

These are prospective commands, not evidence they ran. Root's finite capture
and admission surround them; do not invoke the collector without the actual
closed Stage/owner decision and full reserves.

The Stage has exactly version, kind, noApp, runner, sourceRevision, metadataCap
and ownerDecision. The cap remains1441792 until a fixed hash-bound
`b2-library-closure-owner-decision-v1.json` validates actual owner approval for
1507328. That record permits only read-only SDK input inspection and further
harness SOURCE preparation, with native/model/device execution false and all
other limits unchanged. No approval is supplied by source or a placeholder.
The old cap accepts only a null decision. Both modes and all writers use the
verified cap. Existing global stops, the exact adjudicated historical exception,
prior proof/normal-artifact retention and incomplete-START refusal remain.

## Fresh measured proposal

Root's659B local preapproval record has SHA256
`403e3116a805dcd17f5353e1d1ca1f446f1cfea45c01d85bfe701e0bf85bf9e0`.
It measures metadata1435634B before itself and1436293B afterward; group53636699B
and joint735958193B are BEFORE that record. Target12356228504B and runtime
fixtures210B remain unchanged. No SDK child, collector syntax check, owner
decision or actual Stage exists at this checkpoint.

The367B Stage sizing projection used a64-zero placeholder owner digest only
in memory; it was never written as a real Stage. Reserve1024B for the actual
owner reply record. Including that owner and Stage reserve:

| First-step forecast | Total metadata | Excess above current1441792B | Margin below proposed1507328B |
| --- | --- | --- | --- |
| Complete syntax reserve |1473524B |31732B |33804B |
| Complete collector reserve |1472244B |30452B |35084B |

The proposed decision therefore raises ONLY retained metadata1408→1472KiB
(+64KiB). These are forecasts, not admission. New check/source/review records
and actual prior-step output must be included in fresh full-reserve checks;
passing one forecast never grants the next child automatically.

Keep the original12554947872B target ceiling,64MiB evidence group,724MiB joint,
old576KiB physical/logical records and8MiB fixtures unchanged. No project output
is moved to another root or classification to fit. Earlier executed/evidence
sources, refusals, failed captures, retained copies and records remain; no cleanup
is authorized. Unexecuted working candidates were amended during ordinary source
review before any run. The B2 checkpoint is not reset to hide preparation cost.

The larger2176KiB future artifact-packet proposal in the earlier plan remains
unapproved and outside this decision. Native compiler/link/MT execution, worker
or model launch, app/WebView/native IPC/rendering, Android/device/OS qualification,
downloads, settings, deletion and release remain excluded. Production Author is
still Disabled. PR309 stays at its actual-library compatibility gate until the
observed result justifies progress; full D04/desktop scope remains open.
