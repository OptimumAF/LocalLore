# Pinned UCRT padding observation: source and admission

Historical preparation below. The ONE subsequently approved invocation
[failed its Node E04 gate](D04_UCRT_PADDING_V1_FAILURE_2026-11-02.md) before
SDK adapter creation. Its grant is SPENT; the source calibration is UNRUN.

Refs #25 D04.01/.02/.04 supporting; #31 D09.03 supporting; #21.
This is a source-ready diagnostic proposal. **The packet, both suites and all
30 new groups are UNRUN. No new run approval is recorded here.**

Accepted base is PR348/main`db2c23d09c1fd97986b2f58e1a19ac4de1ceb405`,
freshly fetched during preparation. Its successful V3 grant is SPENT. No retry,
second V2 invocation or further input read follows from that grant.

## Fixed question

The prior V3 report pins `ucrt.lib` to285588B and
`7ef4eac926bf597d2f243f16cdfed7e0db22cb3ca34a1d7e088a84c994a03d66`.
Both modes refused `LibraryInputsFormat/archive_padding_byte`, member4,
header offset98452. The member size, padding offset and actual byte are still
**unknown**. The accepted parser has not changed.

Propose ONE read-only packet, after fresh admission: verify the same root3/leaf
identities and exact digest, one read-only handle, two complete scans,571176B
maximum selected-file traffic. Observe at most five archive headers ending at
member4/header98452. No other library, root search, object/symbol/DEFAULTLIB
interpretation or payload copy is permitted. Hash the retained buffer before
and after synchronous observation; those memory hashes are not extra SDK scans.

An LF padding byte or even target size is valid counterevidence and must yield
false correlation rather than a rejected or manufactured matching observation.
Every qualification/link/closure flag remains false. Even a successful packet
cannot establish metadata parsing, linking, ABI compatibility or a usable worker.
Author remains disabled; full D04/D09, desktop and human quality gates stay open.

The [contract](D04_UCRT_PADDING_OBSERVATION_CONTRACT_2026-11-02.md) freezes APIs,
error codes, report framing, I/O-prefix semantics, invariants and stop rules.

## Complete prepared source closure

The normal project modules have no top-level application work. The Node module
has no filesystem, environment, process or model API. The PowerShell validation
module only defines pure data validators. The local supervisor imports the
literal, hash-bound validator and parent FIRST paths; it exposes no path/function
selector. All six sources are bound by owner/source-review/Stage, with validation
also explicitly bound in Stage. The eleven report-proof fields stay unchanged.

| Source | UTF-8 bytes | SHA256 |
| --- | ---: | --- |
| `native/llama-worker/library_padding_observation.mjs` |16804|`b832d320c70eb38c8fe6f673fdd4e7987f1243f5fc8ef06578255e93155f1075`|
| `native/llama-worker/library_padding_observation_first.mjs` |35079|`f12254344fc8108b87684ba0c1badee1af98268d8011729e695a6bf797146637`|
| `native/llama-worker/library_padding_parent_first.ps1` |24131|`5f49ae076fac4f9ec20e882f8dfe49ef458be374ca26f8482563fcd4a0e034d9`|
| `native/llama-worker/library_padding_validation.ps1` |13794|`0fb18d59e82adc83504f8fcfce72b3cb2de866becc1267a37826830f5bbd0575`|
| local `b2-ucrt-padding-v1-reader-v1.mjs` |10484|`ac62ebd7c123049510bf622425dd632749a117bf8816d1a374b5dbfe723ec02b`|
| local `b2-ucrt-padding-v1-supervisor-v1.ps1` |31009|`51204a871e948b9bc4aa8b0d0a22124f2e948cd13ff370b22a9d9488affe14d0`|

The two whole local source copies total41493B, below49152B (48KiB), uncompressed
in the SAME existing charged native packet group. They are retained and have
**not been invoked**. No program source or generated output was placed in a new
root. The pure project modules are ordinary reviewed Git source, not relocated
packet evidence. Nothing previously retained was moved, reclassified or deleted.

## Independent FIRST and source review

Node FIRST author58dc8c2 and parent FIRST author93136d32 were frozen before their
producers. Parent null-return strengthening e4160853/integration3369bfea and
Node cleanup strengthening675c8477/integration2bf7646b also preceded the Node
producer ca08f369. All original groups/assertions remain. Parent validator author
cd00b572 is integrated at b492cacc.

Root found JavaScript terminal-anchor acceptance after the first module review.
Independent trailing-LF/CR regressions25ac332b/integration180c6a69 preceded the
producer fix5d02b734. The fix has independent source review. These are source
findings and frozen regressions, **not executed RED or passing test results**.

Independent reviews of the module, pure parent validators, complete collector
literals and finally both retained source files are released. Concrete findings
were fixed before retention: truthful/nonempty actual owner answer/call, exact
Node invocation, unexpected read failures without fabricated zero I/O, uncertain
capture stopping before snapshot/postflight, preservation of every existing
top-level packet file, current review/summary readbacks, honest reservation
labels and fixed D: temporary-path checks. Original source/history is preserved.

Root verified retained source bytes/hashes against the prepared literal text;
reviewers checked the actual retained text. They did not execute or hash code.
The supervisor has the exact62-entry union of the retained V3 parent/reader
historical pin maps plus13 settled V3 record pins, alongside the unchanged nine
failed-V1 pins/five absent child outputs and four unlaunched-V2 pins/nine absent
advance files. Unrelated STOPs/incomplete STARTs remain fatal. Before START,
snapshot hashes of every existing top-level packet file; compare them afterward.

A truthful source-review checkpoint is retained:584B, SHA256
`4d1ec9c0d5a697d88a44219d2f9a5cae5ab62f036e145fd51a403131b8d3f353`.
Its `executed:false` describes this preparation checkpoint. No new owner,
Stage, START, parent summary, process, result, snapshot or STOP exists.

## Actual preparation checks and environment

Actual checks were Git whitespace/scope checks, literal-text transport/retained
SHA256 equality, four project-source hashes, fresh retention-only inventories
and complete future-reserve checks. Commands included:

```powershell
git diff --check
git diff --check origin/main...HEAD
git fetch origin main
git rev-parse origin/main
Get-FileHash -LiteralPath <one fixed prepared source> -Algorithm SHA256
```

All project commands ran from existing physical D: checkouts, setting process
TEMP/TMP to`D:/Dev/_Temp`. Actual preparation shell: PowerShell7.6.5/Core.
Literal-text SHA256/GZip serialization used managed Node builtins without
evaluating/importing the project source; this is **not Windows Node execution,
a syntax check or a suite run**. Native packet Node remains the previously
recorded24.22.1 executable,93915464B, pinned to
`d702daa815eabbff763c7d3808e235cf031cf2ca70211b56847bc72f51e240e5`.
The packet must verify that identity freshly. No Node version child was started
in this preparation. No new OS qualification is claimed.

Rust, frontend, native IPC, native WebView, Android, compiler/linker, packaged
worker, model, app and device checks are UNRUN for this source proposal. No UI
or render artifact was produced or inspected. Existing product evidence retains
its prior attribution; this diagnostic does not substitute for any of it.

## Retention and complete reserve

First retention-only inventory: metadata2440942B, physical group54619853B,
physical joint736941347B. The exact pair added41493B; source review added584B.
No owner/Stage/START or experimental output was created.

| Current measured item | Bytes |
| --- | ---: |
| Charged metadata, including cumulative decoded32979B |2483019|
| Existing metadata ceiling,2496KiB |2555904|
| Physical group |54661930|
| Physical joint |736983424|
| Additional conservative carried group/joint charge |22154|
| Target, unchanged |12356228504|
| Runtime products, unchanged |210|
| Remaining owner2048B + Stage1024B reserve |3072|
| Full future post-START reserve |57344|
| Complete conservative metadata forecast |2543435|
| Forecast headroom |12469|

The full run reserve covers process20480, raw9216, decoded9216, snapshot8192,
START768, result2048, Root review1536, STOP512 and parent summary1024 =52992B,
leaving4352B inside its57344B. Source review was bounded separately at1024B.
No evidence-cap increase is proposed. Keep group64MiB, joint724MiB, original
target baseline8259980576B plus4GiB/ceiling12554947872B, old records576KiB and
fixtures8MiB. The new read-only action may create no target/runtime products.
Old physical549989/logical570664B records and browser41584016B remain unchanged.
Fresh admission must remeasure all ledgers and reserve the entire packet before
START; these preparation measurements do not preapprove later drift.

## Proposed ONE-packet invocation and stop boundary

Only after an explicit new decision, construct the actual owner record with its
verbatim answer and call identity, bind all six source hashes and the reviewed
source revision, then create matching Stage. No normalized/fictitious approval
token is used. From the existing frozen physical D: legacy checkout:

```powershell
$env:TEMP='D:/Dev/_Temp'; $env:TMP='D:/Dev/_Temp'
& '<existing charged packet>/b2-ucrt-padding-v1-supervisor-v1.ps1'
```

The private packet location and original root/leaf identities remain local. The
exact two retained sources, reviewed project source and pinned predecessor are
required; this is not a claim that the private packet exists in a clean clone.

One immutable START precedes six actual parent groups V01–V06. Validate/preserve
their canonical6/6 summary before the ONE Node child; the child independently
checks that summary before24 Node groups F01–F12/I01–I08/E01–E04. If Node checks
fail, retain their bounded summary as raw failure and return without constructing
the SDK adapter. Missing/bad summaries or source/proof/ledger drift stop the run.

Only after both gates may the fixed adapter read the one pinned library. One
60-second child, one kill attempt and5-second drain, stdout8192/stderr1024.
No process-tree containment claim. Preserve bounded raw/Base64/process evidence;
unknown closure, timeout, overflow or kill stops before snapshot/postflight.
Cleanly closed coherent stopped reports may be retained but do not pass the
packet. Recheck current owner/Stage/review/summary, six sources, all old files,
normal image and ledgers; result and Root audit must preserve failures.

This proposes no automatic retry, build/link, worker/model/app/device/OS work,
extra library lookup, download, settings change, deletion or desktop control.
Do not spend a second run after a fix. The next decision is required because
PR348's V3 grant is spent and this is a different fixed read/observation packet.
If approved and successful, the next task is to assess the actual observed facts
before proposing any parser-policy or worker-build change; no outcome is assumed.
