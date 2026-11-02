# Fixed-two runtime metadata: retained V1 failure

Refs #25 D04.01/.02/.04 supporting, #31 D09.03 supporting, #21; draft PR348.
Tested source: `3bb900af1bc68270e7688fae5a08fb059d8c9434`.
The ONE owner-approved packet FAILED. Its approval is SPENT. No retry ran.

## Actual outcome

The fixed PowerShell supervisor returned exit1 after7.5283623s observed wrapper
time. Its output was `True`, then `Runtime resolution supervisor refused:
ReportKeys`. That first Boolean is consistent with the existing unconsumed
prior-cohort `Same-Data` comparison; it is not output from a Node child.

The immutable START exists. The actual canonical105B parent summary records
six executed, six passed, zero failed and an empty failed-ID array. The next
summary-validation boundary threw before `ProcessStartInfo` or child creation.
There is no Node process record, Node raw log, result or snapshot for this packet.
The24 Node groups, helper import and new SDK directory/candidate/payload work
never began. Six parent report-data groups passing does not qualify the composed
supervisor or the full packet.

`CODE2_STOP.json` remains165B, with `unknown:false`, reason
`RuntimeResolutionSupervisorCritical` and the retained START name. The START is
intentionally incomplete; no fabricated settled result was written. Both files
remain fatal to ordinary subsequent admission.

## Failure and correction boundary

The independent FIRST returns an actual PowerShell `OrderedDictionary`.
`Validate-FirstSummary` passed that object to the shared `Keys` helper, which
accepts only `PSCustomObject`. Serializing the object produced the correct saved
JSON, but did not convert the live object passed to the next function.
Independent retained-record/source review confirmed this exact boundary.

The original six groups exercised the report validator and missed this live
summary handoff. Before changing the producer, independent author commit
`4a9fbd0cb9a4dddb5e360acf90097d72dbc4a19c`, integrated as `55626f62`, appended
V01 assertions against the actual summary validator: ordered and canonical
positive forms; missing/extra keys; Boolean, string and floating counters;
wrong version/count/kind; nonempty/nonarray failed IDs. All original six group
IDs/assertions/counts and the24 Node groups remain. These additions are UNRUN;
no behavioral RED/green result is claimed.

The prepared correction normalizes only an `OrderedDictionary` at this trusted
summary boundary. Global `Keys` and strict report schemas remain unchanged.
The [separate V2 proposal](D04_MSVC_RUNTIME_RESOLUTION_V2_ADMISSION_2026-11-02.md)
requires new authority; this failure grants none.

## Retained identities

Files remain local in the SAME charged `d08-fork-native-20261030-v1` packet.
The prefix below is `b2-msvc-runtime-resolution-` unless otherwise stated.

| File | Bytes | SHA256 |
| --- | ---: | --- |
| `reader-v1.mjs` |77795 |`0557512c6fae1928097417552c0f6a1843f381c89b32f75f46fd65fde33404c4` |
| `supervisor-v1.ps1` |65313 |`4846695cdb1ec9164f7d9e9bcb4002ff7f7d166695fe6d015cb6dd6b3a5a994d` |
| `owner-decision-v1.json` |1354 |`2c7d7406668c9a5bf12b9fed403c0727cb17dd833d1693cc5e860a687051444a` |
| `source-review-v1.json` |971 |`c06ffac35c8dbee1c86a25fd75b6ab89c75618f2d9b53d075d8692c90a530f1b` |
| `stage-v1.json` |582 |`0dc442dcae94251a9b5f56c21707484541f73b7e0006356d83e02c81381b134c` |
| `start-v1.json` |608 |`50fd889325799479fe6fe349295775496fef36e58a340ed40b57bf619c4e6164` |
| `parent-selfchecks-v1.json` |105 |`d9b733d680a09465dc3e0c95280b2537b42d8c32b6464c6151d7cd4fea6a24f7` |
| `failed-root-review-v1.json` |1133 |`8d141f08739697d3be56b51765b74488458795ec05b9672f5bb2660ba849ea74` |
| `CODE2_STOP.json` (no prefix) |165 |`1cb8bcab943fc4fa8f2a960d2d1038ccabdeaf28b3f050993497c9e198334ee3` |

Root independently verified the complete canonical parent summary and bound
owner/Stage/START/source identities, unchanged normal/Node pins and48 prior
pinned evidence files. Independent review was text/record review, not another
execution. Final charged metadata2113669/2244608 includes the unchanged28498
cumulative decoded allowance; no new Node decoded charge exists. Physical
group54297061, joint736618555, target12356228504 and runtime210. Target/runtime
growth is zero. Every other allowance and all previous output remain.

## Commands and unavailable checks

PowerShell7.6.5/Core; Windows NT10.0.26300/x64 is the preceding accepted packet's
OS observation. Node24.22.1's pinned bytes were checked, but Node was not launched.
The actual command, from the physical legacy review checkout with process-local
TEMP/TMP=`D:/Dev/_Temp`, was the following sanitized fixed path:

```powershell
$env:TEMP='D:/Dev/_Temp'; $env:TMP='D:/Dev/_Temp'
$chatRoot='D:/CodexLocalLore/<existing approved chat root>'
Set-Location -LiteralPath "$chatRoot/source-resource-metrics-review"
& "$chatRoot/author-integration-artifacts/d08-fork-native-20261030-v1/b2-msvc-runtime-resolution-supervisor-v1.ps1"
```

Preparation restored exact reviewed literal/gzip source DATA from this chat and
retained both programs uncompressed. One preparatory extraction command refused
a missing `gzipBase64` key under strict mode before any program write or START;
only its data-key presence check was corrected. A later Root audit tool request
had a JavaScript syntax error before dispatch; its corrected request performed
only the admitted record audit. Both command failures remain in chat evidence;
neither was a new supervisor or Node invocation. Retained-source PowerShell syntax
analysis reported0 errors with bodies UNRUN; it did not prove the summary handoff.

No Rust/frontend/Android checks, native IPC/WebView rendering, linking, worker,
model, app/device/OS or prose-quality qualification ran here. No render artifacts
were generated to inspect. Author remainsDisabled; full D04/D09/desktop and the
earlier human needs-improvement findings stay open. No desktop control, download,
settings, deletion or protected-chat change occurred.
