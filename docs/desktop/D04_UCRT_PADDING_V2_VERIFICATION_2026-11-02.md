# Corrected UCRT padding V2: bounded observation passed

Refs #25 D04.01/.02/.04 supporting; #31 D09.03 supporting; #21; PR364.
**ONE approved V2 packet PASSED / grant SPENT. Observation only.**
The earlier V1 remains FAILED. No parser, build, linking, worker, model, app,
device or release qualification follows from this result.

## Authority, source and admission

Actual owner call `call_3b5c8a2dcb184da09fc80cdd390c2cc9`, verbatim answer:
`Approve one bounded corrected V2 packet`. This activated ONLY the extra44KiB
metadata allowance2496 to2540KiB (2,600,960B), one corrected V2 and the narrowly
validated13-file historical failed-V1 exception. Every other limit and output
was preserved. The [reviewed admission](D04_UCRT_PADDING_V2_ADMISSION_2026-11-02.md)
retains all six source identities and the full scope; it is not reusable authority.

Executed project source: `8fd3da7512daf5d5271bd2619c18d23f614f66f1`.
The actual complete reader11622B and supervisor34315B matched their reviewed
SHA256 identities `d1fecdfd…` and `5805bc2e…`. Both were retained uncompressed in
the same charged group and independently source-reviewed before invocation.
The calibrated E04 JSON-copy fixture was the previously reviewed `48d1d625…`;
no production observer/helper policy changed. The independent reviewer ran no
code, imports, tests, hashes, SDK observations or inventory.

An initial32799-character source-transfer command was rejected by Windows
CreateProcess with os error206 before any shell/process/project script began.
It produced no packet invocation and no library read. Its261B preparation
record is retained. The two unchanged sources were transferred separately,
with the entire remaining source/envelope/run reserve checked each time.
This was not a second packet invocation or a retried failed test.

Initial metadata was2488706B. The full prospective2596083B reserve fit the new
cap by4877B. Actual source-review584B, owner1007B, Stage446B and transport261B
fit the4096B envelope allocation. Fresh pre-START metadata2536941B plus57344B
full run reserve forecast2594285B, leaving6675B. The reserve included Root
review, raw and decoded logs, process/result, snapshot, summaries and STOP.

Root's fresh admission verified all six source hashes,75 fixed pins, the
earlier nine failed-runtime and four unlaunched-runtime pins/absences, all13
failed-padding-V1 pins/absent snapshot, existing START/STOP fences, normal
unlaunched executable and pinned Node. All751 pre-START top-level files were
hashed into a sorted roster. The separate desktop source branch/PR366 remained
at `c29e0d64`; it supplied no authority or changes to this packet.

## Actual invocation and results

From the existing physical D: frozen legacy checkout, with process-local
TEMP/TMP `D:/Dev/_Temp`, exactly ONE invocation:

```powershell
& '<existing charged packet>/b2-ucrt-padding-v2-supervisor-v1.ps1'
```

PowerShell7.6.5/Core and pinned Node24.22.1 were used. Node executable SHA256:
`d702daa815eabbff763c7d3808e235cf031cf2ca70211b56847bc72f51e240e5`.
No installation, download or tool upgrade occurred. The terminal yielded
session55511 then returned exit0 when that same session was resumed; this was
not a second invocation.

* Six parent groups executed/passed, zero failures.
* All24 Node groups executed/passed, zero failures/failed case IDs.
* Both suites passed before the SDK adapter was constructed.
* One pinned input, one read-only handle, two complete verified scans:
  285588B input and571176B actual/reserved selected-library read bytes.
* Capture complete; status complete; critical null; prior-refusal correlation true.
* Node PID83936 closed normally, exit0; stdout2826B, stderr0B. No timeout,
  overflow, kill attempt, unknown closure or I/O error. No process-tree
  containment claim is made.

The capture stopwatch measured277ms. The process receipt begins at
2026-11-02T21:02:02.2632019Z and ends at21:02:03.9474508Z (1.6842489s,
including later record work). Neither is a measured whole-supervisor wall
duration or a model/build performance result. The fixed60-second child and
five-second drain limits were unchanged.

## Observed facts and their limits

The same `ucrt.lib`, source slot33/root index3, was verified against
SHA256 `7ef4eac926bf597d2f243f16cdfed7e0db22cb3ca34a1d7e088a84c994a03d66`.
The collector inspected only five archive headers through the prior error
site. No new library search, object/symbol/default-library parse or payload
publication occurred.

| Header index | Header offset | Member bytes | Body end | Padding |
| ---: | ---: | ---: | ---: | --- |
|0|8|48520|48588|not required|
|1|48588|48608|97256|not required|
|2|97256|470|97786|not required|
|3|97786|606|98452|not required|
|4|98452|309|98821|required, byte0 at98821|

The target body starts98512. Its end marker is hex600a; size field hex is
33303920202020202020. The required alignment byte is **NUL (0)**. The current
helper's `archive_padding_byte` branch requires LF (10), so this observation
correlates with its earlier refusal. This proves an error-site fact for the
one pinned input; it does not decide archive conformance or authorize a more
permissive parser. The strict helper9972 and its historical behavior remain
unchanged. The member's long name, COFF contents, symbols, dependencies and
linkability were not established by these header facts.

Handle/read counters and before/after identities are application-owned evidence,
not an independent OS file-I/O trace. Source/tool/normal-image and retained-record
guard hashes are separate disclosed reads outside the571176B library-payload
scan budget. No SDK payload is included in this public record. Raw reports and
local root/leaf identities stay in the local, gitignored packet.

## Retained evidence and Root audit

All files use prefix `b2-ucrt-padding-v2-` in the same existing charged group.
There is no V2 STOP. Every old failure/STOP and unlaunched source stays intact.

| Suffix | Bytes | SHA256 |
| --- | ---: | --- |
|`preparation-transport-v1.json`|261|`0657bc6639a91a1e1136cd9c0754d9bfea7706988e2c18ccb6f40c771ce03362`|
|`source-review-v1.json`|584|`d27fd24088ff2a38e535a3c26a031f5c410aef3415be43c3d38b55e0d4b23560`|
|`owner-decision-v1.json`|1007|`29333dfd34f9dbb43ba5f91aaed60df739168bc9efad0ce5a1171a6f003396c9`|
|`stage-v1.json`|446|`868025d3aa84bc87704fe06da3974d8785e9f90292fa7928829715e903398e5b`|
|`start-v1.json`|450|`9bb8fc829040c545b87f977bb4685e0ad4afce15f497a5f059f18c69b866f7d2`|
|`parent-selfchecks-v1.json`|108|`206fd88e478129290f098663000f7ac88f46b14d710219b62c5e0fe4a3542973`|
|`process-v1.json`|5076|`ffa45bae0f6a6a1322513d85fc694138c6fd1896bc600e70f93ba22d1e36ccea`|
|`result-v1.json`|724|`fc77b7d4228c2d8c2769a7100f2ca1a8b22369f9cbe546b7b47a3a5c710e2268`|
|`stdout-v1.bin`|2826|`221320817405dbb93cfe6398ebf9de255dac9775f3fb27f4d02511e4d4021a1f`|
|`stderr-v1.bin`|0|`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`|
|`snapshot-v1.json`|2826|`221320817405dbb93cfe6398ebf9de255dac9775f3fb27f4d02511e4d4021a1f`|
|`root-review-v1.json`|937|`8ccb3fe5cd0db374d1eda1cfc88db519062bd155aac315624450e25911990ccb`|

Root verified raw/Base64 bytes/counts/hashes and canonical report encoding,
all eleven report proofs, actual parent/Node summaries, process/result/START
bindings, source/normal/tool pins and all historical exceptions. All751
pre-START files still yield the exact roster SHA256
`a00e1e84179e6581b9eeec3c0d0901f6a44c9b5b6ef18547da7e0bad0183a59d`.
Root retained its937B audit within the1536B allocation. Independent retained
record review found no inconsistency among the raw report, process/result,
owner/Stage/START/source review, parent summary and Root audit. That reviewer
did not recompute hashes or rerun code; preservation/canonical/growth checks
above are Root's actual audit attestations. A separate documentation/record-text
review also found no factual, arithmetic, privacy or scope blocker; it ran no
hashes, inventory, code, imports or SDK reads. These are source/evidence reviews,
not fabricated GitHub approvals or human quality acceptance.

Final metadata2552714/2600960B leaves48246B. Cumulative decoded evidence35971B,
conservative group/joint carry25146B. Physical group54728633B and physical
joint737050127B plus that carry remain under64MiB/724MiB. Old code records
remain549989B physical/570664B logical under576KiB. Existing fixtures671744B
plus runtime210B remain under8MiB. Target12356228504B is unchanged and below
the original baseline8259980576B plus4GiB ceiling12554947872B. Nothing was
deleted, moved, overwritten, reset, deduplicated or reclassified to fit.

## Next task and unavailable qualification

Assess the exact observed NUL-padding case against the intended strict versus
metadata-profile parser contract. Freeze independent synthetic FIRST before
any policy implementation; preserve strict historical refusals and all earlier
observations. This packet permits **no further input observation, test child,
native build/link, worker/model/app/device/OS work or automatic retry**.

Qualification/linkQualification/closureComplete remain false. Author remains
disabled. Rust/frontend/Android checks were inapplicable to this unchanged
Rust/frontend/Android source slice and were not run; native IPC/WebView/render,
model/worker behavior, physical-device parity, human story quality and full
D04/D09/desktop acceptance remain unverified/open. No full task is checked off.
