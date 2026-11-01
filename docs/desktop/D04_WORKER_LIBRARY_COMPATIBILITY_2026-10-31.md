# B2 actual library-input inspection: complete, unqualified

Refs #25 D04.01/.02/.04, #31 D09.03 supporting, and draft PR309.
**The single admitted inspection completed and refused compatibility. It does
not qualify a worker artifact or establish the complete effective library set.**

The owner approved the [reviewed read-only admission](D04_WORKER_LIBRARY_INPUT_ADMISSION_2026-10-31.md)
in actual request `call_54dbc54f7d4c403abba07f47a552ae06`, answering
"Approve bounded read-only inspection". Only retained metadata increased from
1408 to1472KiB (1441792 to1507328B). All other storage limits and exclusions
remain unchanged. Both approved children are now spent: one syntax check and
one read-only metadata collection. No automatic retry follows from this result.

## Source, tools and execution category

Actual repository source is `8ef6a975108d80810cf02d88d86f46ee8dc8d28f`, based
on accepted main760a5d4b/PR308. The pure inspector/test files are unchanged from
their [85-case synthetic verification](D04_WORKER_LIBRARY_INPUTS_VERIFICATION_2026-10-31.md).
Those cases do not establish real SDK compatibility.

Root ran existing pinned Node24.22.1 from the physical D: checkout, using
PowerShell7.6.5 with process-local TEMP/TMP `D:/Dev/_Temp`. The syntax wrapper
is13384B; the metadata coordinator is28218B. Root read and independently
reviewed both sources before execution. Source review corrected optional-field
access in historical logs and closed local read pipes before uncertain-closure
bookkeeping. Those were unexecuted source amendments, not failed Node attempts.

The exact child shapes were:

```text
<pinned Node24.22.1> --check <fixed N>/b2-library-closure-v1.mjs
<pinned Node24.22.1> <fixed N>/b2-library-closure-v1.mjs --metadata-child
```

The metadata parent, invoked without script arguments, alone creates the second
child. Here `N` is the existing charged local evidence packet, not a new output
root. The old coordinator/Stage names are single-use evidence; these commands
are execution records, not permission to repeat them. Node preload, path, debug,
coverage, cache and warning-file redirects were refused before parent startup.

This is **Node syntax and binary-as-data inspection**. No C++/Rust compiler,
linker/MT, CMake, packaged worker, model, desktop app, renderer, native IPC,
Android, device, OS qualification, Developer Shell setup or download ran.
No library, object or extracted directive executed. Installed SDK inputs remain
in their existing C: tool locations; every new project output stays on D:.

## Exact observed results

| Check | Actual outcome |
| --- | --- |
| Collector syntax | closed exit0;91ms stopped child stopwatch; complete empty stdout/stderr |
| Metadata child | closed exit0;4.429s from recorded child start/close; complete193B stdout/empty stderr |
| Transport/closure guards | no timeout, overflow, forced kill, unknown closure or critical stop |
| Snapshot |15630B; `unsupported_input`; `qualified=false` |
| Completeness | `captureComplete=true`; `completeForFixedRecipe=false`; no selected-member/link qualification |

The syntax process record's UTC end is populated after raw-record bookkeeping;
its timestamp span is not the91ms child stopwatch. Neither timing is inference
or application performance. OS process-tree containment is not claimed.

The snapshot contains17 fixed inputs and15 resolved SDK/CRT inputs. Of the
fixed inputs,13 parsed and four returned `LibraryInputsSize`: the preserved
`first` and `b` copies of llama-common.lib (92584312B each) and llama.lib
(49295154B each). Each file is below the256MiB input limit. The coarse category
does not identify which internal aggregate/count/size guard refused it.

All15 resolved SDK/CRT inputs returned `LibraryInputsFormat`. These are the ten
explicit SDK names, plus msvcprt, msvcrt, oldnames, vcomp and ws2_32. There are19
refusals in total. The snapshot does not locate a precise format rejection or
prove that an installed library is malformed. Unsupported inspected members
can contain additional default-library requests that were not discovered.

All15 discovered requests were processed/resolved in the fixed search order;
no missing-library result,64-request cutoff or16KiB fallback occurred. Capturing
all those observations is different from completing the fixed recipe. Existing
thresholds, member inspection and refusal behavior were not weakened.

Recorded input bytes total359493030. The child read718986060B across its two
passes. The parent separately read1038545986B across admission/revalidation;
those counters are file reads, not peak memory. The snapshot records actual
hashes for all32 inputs, fixed search-root identities and no cwd `.lib` entries.
These are preparatory historical/B1 objects, not a new experimental main object.
The [Microsoft PE/COFF specification](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format)
remains the format reference; the current inspector supports only a subset.

## Storage and retained evidence

Before the syntax child, metadata1450476B plus its complete35840B reserve fit
1507328B. After retaining the syntax result, metadata1452236B plus the complete
34560B collector reserve forecast1486796B, leaving20532B. Both actual steps
therefore passed fresh admission rather than relying on the earlier forecast.

Before writing its own635B result, collection measured metadata1469539B,
group53670604B and joint735992098B. After that result the totals are1470174,
53671239 and735992733B. Root's927B actual-log/source review brings them to
1471101,53672166 and735993660B. These remain under1472KiB/64MiB/724MiB.
The original target ceiling12554947872B and its baseline remain unchanged;
actual target12356228504B and runtime fixtures210B did not grow. Old576KiB
record and8MiB fixture limits are unchanged. No output was deleted, moved or
reclassified. All earlier executed sources, refusals, failures and copies remain.

Root decoded/read the complete raw summary and empty stderr, rechecked actual
process/result/snapshot/source hashes and the unchanged normal desktop binary
`7a68992bc35d2e778d71e8db80ef4050a281d65d785a054e77abb569aadaf192`.
The app remains unlaunched. Independent actual-record review agreed with the
unqualified result and the accounting/timing distinctions above.

| Local evidence/input | SHA256 |
| --- | --- |
| Actual owner decision | `2ee076768d5c4154f75144454950460db3b53ae1388398657b5140f84a1f326a` |
| Actual Stage | `a2cec31387592d3a5d1bfd5b939583d2abe39cdf8de632695c49d3fbf83cb2be` |
| Syntax wrapper | `bc99011f842e02994e1d3101204a2e29d4900c25f6630151895458f16589749d` |
| Metadata coordinator | `fc344e8abaae475860935a3efe2236552586b5f31b834e6cfc8caff2cdf867fd` |
| Syntax process | `8f7f4fc4cc7e3321e46dccedb0a95f448c8d891dd141dbbbb0e8a45898fcecdf` |
| Syntax settled result | `ff78229622690fbf75cd0a7e3a17a262a07ff44236be9533d71caa84446708cb` |
| Metadata process | `122e6c81a806a91ff4ad40f5ee1f2ec7933094306aa25492b29f9500b14d69b5` |
| Snapshot | `62eb0ab9ff6296b13d4a8cebd49a69ffe95444f75da6ac29971c4cf7729a6dbc` |
| Metadata settled result | `aec15b9786f6281f16afcad6825c23eae459eddcb0151e3847245b4f6dbf5a74` |
| Root actual-log/source review | `654fcff3ea386a91071a35985085c82746b9089914672b1faca5666085466995` |
| Node24.22.1 | `d702daa815eabbff763c7d3808e235cf031cf2ca70211b56847bc72f51e240e5` |

## Next gate

PR309 remains draft at actual-library compatibility. Prepare bounded refusal
site/counter diagnostics and synthetic controls without changing existing limits
or speculatively accepting SDK layouts. Preserve the original85 predicates and
this unqualified packet. Any new diagnostic execution needs a concrete reviewed
protocol, fresh source/proof/storage admission and separate authority; neither
spent child may be rerun automatically. Further harness source preparation is
within the recorded decision, subject to unchanged aggregate caps.

The [candidate artifact plan](D04_AUTHOR_WORKER_ARTIFACT_PLAN_2026-10-31.md)
remains unexecuted and separately gated, including its larger proposed metadata
allowance. A future candidate must inspect its NEW object before linking and
bind the effective input set. Production Author stays Disabled; native worker
adoption, quality, offline application journeys, Android and full D04/D09/desktop
acceptance remain open. No release or settings change follows from this packet.
