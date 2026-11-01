# Worker library refusal diagnostics: actual bounded packet

Refs #25 D04.01/.02/.04, #31 D09.03 supporting and #21.

The owner-approved diagnostic packet completed. All112 synthetic cases and
the fixed coordinator syntax check pass. One read-only inspection localizes
the SAME19 refusals among32 pinned inputs; it does **not** qualify those
libraries, a complete input closure, linking, a worker or production Author.
All three new children are spent. All prior output remains retained.

## Source and review

The diagnostic helper/test were actually executed at
`a4f61e90dd5638ae5685ce5230f8f3f108471392`. The original85 predicates, error
messages, successful return contract and every admission bound remain intact.
The patch adds fixed refusal-site IDs, eight numeric/null context fields and
27 synthetic diagnostic cases. It does not add filesystem, process or network
access to the Buffer-only helper.

After execution, the two-file patch alone was cherry-picked onto accepted main
`c09380d6d9ad9fd3947405355ed5b9a058300acf`, producing
`f3b67ce18e1315383e0f636f96bbb1b101be037c`. Git comparison and actual file SHA256
checks establish that both integrated files equal the tested bytes. No check
was rerun after this integration. Other main changes are not covered by this
packet. The original diagnostic branch and frozen old-inspector checkout remain.

PR309 was independently merged as `a971199738dc476f03b21ea747505f916e25ee02`
before this packet resumed. Its merge does not change the earlier unqualified
result or satisfy this new packet's acceptance. The
[original result](D04_WORKER_LIBRARY_COMPATIBILITY_2026-10-31.md) and
[reviewed admission](D04_WORKER_LIBRARY_DIAGNOSTIC_ADMISSION_2026-10-31.md)
retain their historical status and limits.

Independent source review preceded execution. Root checked actual complete
raw logs, process/result/source bindings, old proofs, global stops, incomplete
START fences, ordinary physical paths, fresh storage reserves and the unchanged
normal binary. Separate read-only review of the actual records found no
consistency blocker; this is not independent re-execution or human acceptance.

## Environment, commands and exact results

PowerShell7.6.5 reports Win32NT / Microsoft Windows10.0.26300. The installed,
hash-pinned Windows x64 Node24.22.1 executable is reused. No new version child,
dependency installation, SDK setup, download or operating-system qualification
ran. TEMP/TMP are process-local `D:/Dev/_Temp`. All project commands start from
the physical D: frozen `source-resource-metrics-review` checkout. The seven
Node preload/path/debug/coverage/cache/warning-file overrides must be absent.

Let `$base` be the existing physical D: LocalLore task root, `$packet` its
`author-integration-artifacts/d08-fork-native-20261030-v1` directory and `$node`
its `d09-build-security/node-v24.22.1-win-x64/node.exe`. These are the actual
fixed invocations, after the corresponding unique actual owner/Stage and
complete-reserve admission:

```powershell
$env:TEMP = 'D:/Dev/_Temp'
$env:TMP = 'D:/Dev/_Temp'
& "$packet/b2-library-diagnostic-unit-runner-v1.ps1" -Check unit
& "$packet/b2-library-diagnostic-unit-runner-v1.ps1" -Check syntax
& $node "$packet/b2-library-diagnostic-v1.mjs"
```

These three grants are consumed; this is a reproduction record, not permission
to repeat them. Retain unique records and obtain fresh applicable admission
for another packet. The public synthetic helper command is
`node native/llama-worker/library_inputs_test.mjs`; actual execution above used
its fixed isolated-worktree absolute path and bounded capture wrapper.

| Actual child | Result | Complete stdout/stderr | Time evidence |
| --- | --- | --- | --- |
| Synthetic helper |112 executed /112 pass /0 fail, empty failed IDs; closed0 |111B /0B |756ms stopped child stopwatch |
| Fixed coordinator syntax |closed0, empty logs |0B /0B |68ms stopped child stopwatch |
| Fixed32-input diagnosis |closed0; `diagnostic_complete`; capture complete |141B /0B |5.279s process-record UTC interval |

No timeout, overflow, forced kill, unknown closure or critical stop occurred.
PowerShell process-record UTC ends include later receipt bookkeeping; they
must not replace the unit/syntax stopwatch values. Diagnostic timing is a
recorded interval, not an inference/application benchmark or peak-memory
measurement. Absolute OS process-tree containment is not claimed.

## Actual first-refusal sites

The7640B snapshot contains13 parsed inputs and19 refusals, matching the old
coarse result. All32 aliases, paths, sizes and hashes bind to that original
snapshot. Each input is hashed across two complete scans on one held read-only
handle and identity-checked. No default-library lookup or replacement input
cohort ran. Input bytes359493030 imply718986060 recorded child file-read bytes;
this I/O counter is not a memory measurement.

| Fixed refusal site | Rows | Actual observation and limit |
| --- | --- | --- |
| `coff_sections_total` |4 |first/b llama-common:71623 sections at refusal; first/b llama:65576. Existing aggregate bound65536. |
| `coff_relocation_pointer` |10 |kernel32, user32, gdi32, winspool, ole32, oleaut32, comdlg32, advapi32, msvcprt, vcomp. Source rejects zero relocation count with nonzero pointer; actual pointer values/range validity are not recorded. |
| `directive_encoding` |3 |shell32, uuid, ws2_32. Rejected byte class; exact byte values or padding interpretation are not recorded. |
| `coff_machine` |2 |msvcrt, oldnames. Actual machine values and member semantics are not recorded. |

Indexes are zero-based; `memberOffset` identifies the archive HEADER offset.
Section counts above are aggregate counts at FIRST refusal, not final totals
for whole archives. The context schema contains exactly memberIndex,
memberOffset, sectionIndex, sections, directiveBytes, tokenCount, actual and
limit, each a safe nonnegative integer or null. It contains no raw bytes,
member names, paths or directives.

These observations locate guards, not every incompatibility behind them.
They do not establish malformed SDK libraries, a non-x64 library, a particular
control byte, safe ignored fields or selected linker members. Microsoft’s
[PE/COFF specification](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format)
is the format reference, rather than treating whatever a local linker accepts
as sufficient parser policy. Further policy changes need bounded evidence and
adversarial cases. No inspector admission bound was increased, member omitted
or failed predicate relaxed. Incomplete members can hide more default-library
requests.

Snapshot and settled result both retain `qualified=false`,
`linkQualification=false`, `closureComplete=false`. A complete diagnostic
capture is not a complete library closure or link qualification.

## Storage and evidence identity

The owner's direct message explicitly approved only metadata1472→1536KiB
(1507328→1572864B) and the reviewed packet. The actual607B owner record binds
that answer; all other limits are unchanged. Source was retained only after
that decision and fresh full-reserve admission, with exclusive creation.

| Admission/retention point | Charged metadata bytes |
| --- | --- |
| Prior output including prepared18345B PowerShell wrapper |1489446 |
| After actual607B owner and28028B diagnostic source |1518081 |
| Unit Stage458B plus complete38912B reserve forecast |1557451 |
| After unit result, syntax Stage458B plus38912B reserve forecast |1560428 |
| After syntax result |1523692 |
| Actual807B check review +520B diagnostic Stage +34560B full reserve forecast |1559579 |
| After diagnostic614B result |1534825 |
| After924B Root actual diagnostic review |1535749 |

Final group53736814B and joint736058308B remain below unchanged64MiB/724MiB
caps. Target12356228504B and runtime fixtures210B did not grow; the original
target ceiling12554947872B/baseline4GiB allowance remains. Old record
physical549989B/logical570664B, browser41584016B, old576KiB record and8MiB
fixture limits remain. No output was deleted, moved or reclassified. New raw
unit/syntax bins and complete diagnostic base64 streams stay local outside
the source checkout, with all prior failures/refusals and sources.

| Input/local proof | SHA256 |
| --- | --- |
| New helper12709B | `5682460909b69f85763d1919d6b1e7f0a49e26f41c938f87fc61104ce0bdcfc5` |
| New test15402B | `36ec3c81ec02ad4844b91ff7d0de20dae1c8665dbeef697f98476de4fc2e5022` |
| Actual new owner607B | `a4d0b1114cbff048d1a8e32ea333de7936802cfcc563842b1092b91600c66fb9` |
| PowerShell capture18345B | `f6741372d26c4c02d81e71fea3a9c23bdd2896edb03891f6f0fe0d0c6874fcaf` |
| Diagnostic source28028B | `1b5f8a5cb6f26a8741ecda9aa84acf3e792749670ad152d14fa80123f17a9850` |
| Unit process | `b1ad02909db17ec57b6b24c976dd6c0ad1128f9cec66b23258f60c881314ca8a` |
| Unit result | `b3c65ec2611b0f828064e549db3f7e330880411eba06ce3833fa8ba81b08c17f` |
| Syntax process | `b3701fb991fdf8c9c168fbd827a25b1978a466f895ef3820c32a4a97fe545a89` |
| Syntax result | `68130138a1484bb3a1cdefc58224243b837bb0a2bf305c36753280c4d6499a96` |
| Root check review807B | `29a1c263efc05c8bda4e624836278dcca5a6ff9040e1c3c9adf2773a0df3bd9c` |
| Diagnostic Stage520B | `b656c553ded8db2e1afd452e9526ebae00ab1b810d1c5332d8261e71350e243c` |
| Diagnostic process1356B | `96fe41c91600258367620607f56618f62352507267a0d061103bd71f05e8b563` |
| Diagnostic snapshot7640B | `c7bce3ceb14e57fc260aa9e65c4edb0efad97dec2b020bf37eb6f1b34d7d8678` |
| Diagnostic result614B | `f65914e019e0b256f49943c0dc30cb70ce081947bb4322b52a5523a9d3ef5f02` |
| Root actual diagnostic review924B | `34c69b86afb207934ecf22932e41a6acb565946cc9946b18d344394393c48a42` |
| Node24.22.1 | `d702daa815eabbff763c7d3808e235cf031cf2ca70211b56847bc72f51e240e5` |
| Unchanged normal desktop binary, unlaunched | `7a68992bc35d2e778d71e8db80ef4050a281d65d785a054e77abb569aadaf192` |

## Remaining gate and next work

The diagnostics-only helper is tested and reviewable. Actual-library
compatibility remains unqualified. Next source work is a bounded, reviewed
plan to identify the rejected member header/encoding facts and choose a
standards-backed parser/resource policy, retaining the current rejections and
all original negative assertions. No new inspection child is authorized here.
An actual supported-input correction must then pass its applicable synthetic
and real-input checks before the separately admitted artifact packet.

No Rust/frontend/native/Android build or test, compiler/link/MT, worker/model,
application/WebView/native IPC/render, device, network-blocked/offline runtime,
VS setup, download, settings change, deletion or release ran in this packet.
Those checks cannot be inferred from Node data parsing. Production Author stays
Disabled; packaged pins, Rust/Host/Android contracts and quality verdicts stay
unchanged. Full D04/D09 and desktop acceptance remain open.
