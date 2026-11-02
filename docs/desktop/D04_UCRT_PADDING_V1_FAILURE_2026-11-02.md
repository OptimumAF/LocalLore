# UCRT padding V1: failed synthetic gate, no input observation

Refs #25 D04.01/.02/.04 supporting; #31 D09.03 supporting; #21; PR364.
**FAILED / grant SPENT. No automatic retry.** At this failed cohort's handoff,
the source correction below was UNRUN. A separately approved
[V2 packet](D04_UCRT_PADDING_V2_VERIFICATION_2026-11-02.md) subsequently passed;
it does not change this V1 outcome or retroactively establish a V1 observation.

## Actual approved invocation

Actual source`562fa75230fce402ac34b732402a3f5d2a4068fb`, exact six-source hashes
and local pair in the historical
[admission](D04_UCRT_PADDING_OBSERVATION_ADMISSION_2026-11-02.md).
User call`call_6ab43cece1654b3ab2b0dedcae611215` answered verbatim:
`Approve one bounded read-only packet`. A new owner and Stage were bound after
fresh source/tool/normal/history/fence/storage checks. Actual pre-START metadata
2484435B plus57344B reserve forecast2541779/2555904B, leaving14125B.

From the existing physical D: frozen legacy checkout, with process TEMP/TMP
`D:/Dev/_Temp`, ONE invocation:

```powershell
& '<existing charged packet>/b2-ucrt-padding-v1-supervisor-v1.ps1'
```

Terminal exit1, `PacketFailed`, supervisor line406. No second invocation or
rerun occurred. The terminal tool first yielded session80131 and the same handle
then returned terminal failure; resuming that handle was not a second run.

Actual parent summary:6 executed/6 passed/0 failed. Actual Windows Node summary:
24 executed/23 passed/1 failed, only`E04` in failed_case_ids. The other23 groups
reported pass; no assertion-level exception or progress within E04 was retained.
Do not infer that E04's earlier positive/extrema assertions passed.

Node PID81924 closed normally, exit1. No timeout, overflow, kill attempt,
unknown closure or I/O error. Capture stopwatch684ms; process receipt begins
`2026-11-02T19:10:20.8242216Z` and ends`2026-11-02T19:10:23.6467422Z`,
an interval2.8225206s including later record work. These are different clocks;
the full supervisor wall duration was not measured as a single value.
stdout166B, stderr0B. No process-tree containment claim.

The raw failed-summary output is not an observation report, hence the parent
records`InvalidPaddingObservationReport` and null nodeChecks/inputReservations
in its result. The raw summary supplies the actual24/23/1 counts. Known closure
and settled result do not imply a passed packet.

## Read boundary and retained evidence

The pinned reader validates the Node summary then, on failure, writes that raw
summary and returns BEFORE constructing the SDK adapter. The preserved output
matches that branch. Therefore the SDK observation was not reached according to
the frozen program's gate; this is not a separate OS file-I/O trace measurement.
No library read, padding observation, canonical snapshot or SDK payload was
produced. Member size, padding offset/byte remain unknown. No app, worker, model,
build/link, device, Rust/frontend/native IPC/WebView/Android or render check ran.

All artifacts below are local, with prefix`b2-ucrt-padding-v1-` in the same
existing charged packet group. No originals were overwritten or deleted.

| Suffix | Bytes | SHA256 |
| --- | ---: | --- |
| `owner-decision-v1.json` |970|`023a6b944a768557f687669f774d5b65702d9d85b5ae678b6b10605364ddc021`|
| `source-review-v1.json` |584|`4d1ec9c0d5a697d88a44219d2f9a5cae5ab62f036e145fd51a403131b8d3f353`|
| `stage-v1.json` |446|`0fed0acdd68ff9c432bdf2b5f8c6c7de8c64a2c3718e0b6a67a0f5c30df2b617`|
| `start-v1.json` |450|`3cdccabfb268861e929fb9d1a26d8979244c25bebaea95e0f8befea35f59f3cc`|
| `parent-selfchecks-v1.json` |108|`206fd88e478129290f098663000f7ac88f46b14d710219b62c5e0fe4a3542973`|
| `process-v1.json` |1560|`8008556e7684657ebb5e1e8b92e68f1045b33c02c5d0c50098e197051054df22`|
| `result-v1.json` |730|`ce777c72feafbd989a656fd1e92fbd9c21c4e99ebba18d286962875110e739ff`|
| `stdout-v1.bin` |166|`98ba5023e3a87341b43ddf3a6446bcf78012054b69a4cb4fdd8de0c93313c4f4`|
| `stderr-v1.bin` |0|`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`|
| `STOP.json` |134|`0672ffd4f407558fd348481adbc2b2b1672d13027d4bae26811efd591e8f0af1`|
| `root-review-v1.json` |957|`1db09d08382ca3794aa04556be5f6385aac7717287742564c3b1eb3ac3582c9d`|

The two unmodified local source copies10484/31009B retain the admission hashes.
Root verified raw/Base64/canonical failure summary, counts/closure/result/STOP,
six actual source hashes BEFORE calibration, all75 historical/predecessor pins,
the unchanged13 earlier failure/unlaunched guards, no snapshot and ledgers.
The source-review's`executed:false` remains its truthful pre-run checkpoint;
it was not rewritten to manufacture a later result. Failed source562fa752 and
its original FIRST remain preserved in Git when the working source moves on.

Final post-audit charged metadata2488706/2555904B; cumulative decoded33145B,
conservative carried group/joint charge22320B. Physical group54667451B,
physical joint736988945B. Target12356228504B and runtime210B are unchanged.
Root review957B fits the reserved1536B. All other caps remain unchanged.

## Source defect and unrun calibration

Independent inspection confirms a deterministic fixture defect consistent with
E04's recorded failure: `reportFixture(api)` contains the observer's deeply
frozen target, while E04 directly assigned target.bodyEnd OUTSIDE`rejects()`.
Strict ES-module code throws TypeError at that assignment if reached, before
the intended encoder rejection. The group-only log cannot prove that this was
the first failing E04 assertion; do not replace the recorded ID with an invented
exception/stack or pass claim.

Original FIRST author supplied focused correction
`102fe624ff1773918118fc092fb27decd36ffe2e`, integrated as`8fb23f29`:
copy the JSON-data report before mutating the negative fixture; assert the copy
really contains MAX+1 and the original target remains frozen/unchanged. Preserve
the original encoder-rejection assertion, every prior assertion and all24 IDs.
No production module, parser policy, frozen-return contract or accepted helper
was relaxed. Whitespace checks pass; the calibration itself is UNRUN.

Independent calibration source review is released; execution remains UNRUN.
Next source-only work: prepare a separate corrected packet and exact admission
preserving this failed namespace/STOP and
all earlier output. A fresh finite decision is mandatory before another run.
Current cap headroom is67198B; even the old41493B pair plus4096B envelopes and
57344B full reserve would need102933B, a35735B shortfall before new guard text.
Do not materialize another pair under an incomplete reserve or delete evidence
to fit. Finish the complete corrected source and forecast before any new
storage/run question. No cap increase is authorized here.
