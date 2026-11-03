# Diagnostic UI build attestation evidence — 2026-11-02

Refs #14 (M10.03 DIAGNOSTIC_UI_BUILD_ATTESTATION, supporting M10.02) and roadmap #3. B104 is implemented and ready for review; milestone criteria remain unchecked. This packet adds file-only tooling and tests. It does not run Android, qualify diagnostic export, or authorize a guest. No production app/engine/dependency/permission/model change is included.

The product being attested is PR #380 `dafff3bce95cdcb7125095f9fee483e8373d45a8`, stacked on unmerged PR #377. The attestor's tested raw source tree is `959f3a4b631b494bff213daf8bd45c7e8a5d54da`; the final publication adds only this report. The substantive operator checkout remains at `8924278ce1c877e6d67c90c15a35fb23ca7198dc` with its normal index unchanged. Publication uses an explicit alternate D: index, without switching or resetting that checkout. The candidate is a raw Git snapshot, not a managed clean worktree. External main/Desktop additions were not silently added to the product qualification.

## Executed checks

Installed Python 3.14 was invoked with `-I -S -B`, explicit physical D: source insertion and owned D: temporary directories. The private packet runner dispatches each child through the existing bounded Windows process owner with a 180-second ceiling. Each listed phase closed with known owner cleanup. No installed SDK tool, ADB, compiler, Android guest or model was dispatched by the new APIs.

Final `final-v4`: **137 tests, zero failures/errors/skips**, 18.849 seconds (owner 18.969 seconds). Cohort: 21 independent full-count attestation methods, 14 independent actual DEX/ZIP methods, 12 file/XML/CLI methods, and 90 existing APK/DEX/instrumentation/archive/record admission regressions. Counts are unittest methods, not subtest scenarios. Independent authors froze proposals before root execution; they did not execute this cohort themselves.

Equivalent repository test command, from a physical D: checkout with D: TEMP/TMP:

```powershell
python -I -S -B -c "import sys, unittest; sys.path.insert(0, '.'); names=['test_diagnostic_ui_build','test_diagnostic_ui_dex','test_diagnostic_ui_build_files','test_audit_physical_model_apk','test_audit_apk','test_instrumentation_apk','test_archive_ui_build','test_record_ui_build']; result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(['scripts.tests.'+name for name in names])); raise SystemExit(not result.wasSuccessful())"
```

The synthetic attestation graph retains the full 2,581/2,580 source counts, 2,725 preservation pairs, 49 JVM suites/427 cases and six selectors. It uses tiny byte leaves and independently constructed Git IDs. Public-front-end negative tests retain the unchanged golden baseline and actual baseline decoder; they do not substitute a permissive source/count/validator callback. Fake definitions in those graph tests establish eligibility logic only. The separate DEX corpus parses actual independently constructed ZIP/DEX bytes and proves legacy four-tuples, exact opt-in booleans, missing/empty/truncated/unaligned bodies, oversized spans, annotation/reference/definition roles and multi-DEX refusal.

Actual D: tests prove bounded guarded bytes, final content rehash, changed cached pin, hardlink refusal, resident/read caps, cooperative deadline, ancestor mutation, and decoding the already verified bytes. The same-size/same-inode mutation test restores mtime before final rehash and still refuses. Pure tests cover UTF8/XML DTD boundaries and fixed CLI refusal output. No test replaces actual Android/SAF/provider execution.

## Genuine saved-artifact replay

`genuine-v3` performed public create/verify/create in **24.543 seconds**, with child process creation denied inside the checked APIs. Both create results were structurally and serialized-byte identical; verify returned the same detached metadata. The exclusive-created manifest is **20,564 bytes**, SHA256 `3921123a149bcd5a41919c56d3a5306d889bfcef39ac07a1f8672ab3d69e2c28`. After the XML/CLI refinements, genuine CLI create and verify independently passed (owner 8.385/8.540 seconds), with zero stderr and no child tool dispatch. Their JSON values agree with that manifest.

Replayed raw product source tree: `e91cffdb2ebfc6760985cd65f7a06d56718c51e4`; tested B103 subset: `d9b518139d6f95f497aba2d064b03c25542813dd`. All selected original/copy records were checked from current files, not accepted from the old summary alone. The **427/49** values remain B103's recorded JVM executions, not fresh JVM runs. The saved audit records were bound without relaunching AAPT/Java/signature tools.

| Saved artifact | Bytes | SHA256 |
| --- | ---: | --- |
| Product APK | 28,012,664 | `53ce76a5d431e6109b51475765845efcae90ead71a33ad676118c50fc1c73c07` |
| Test APK | 2,265,104 | `e703d6ef202b86ef256e8c3edfd625725354db92cb98438f2f96da45da85c1e9` |

The six fixed compiled selectors have positive instruction-unit counts, in roster order: **296, 185, 78, 157, 304, 407**. This is compiled-definition evidence; **zero Android executions** were performed in this packet. Neither body length nor a JUnit annotation proves a passing assertion.

## Findings, corrections and preserved failures

- Independent review found that reopening the APK pathname after hashing could decode other bytes. The reader now passes the exact verified immutable bytes through `BytesIO`, and rehashes tracked files at session end. A separate CLI pre-pin path now normalizes missing/foreign-reader errors instead of exposing a traceback. Strict UTF8 decoding before the XML text guard closes an encoding gap in the private fixture seam; fixed public hashes were not shown bypassed.
- Initial source inspection caught the preserved 490-byte stderr: two known JAVA_TOOL_OPTIONS echoes. The validator requires those exact echo values and matching request options, rather than assuming empty stderr. The existing Kotlin warning is in stdout.
- `genuine-v1` and `genuine-v2` refused the task-log predicate. Diagnosis showed task-name prefix collisions and Gradle's duplicate unsuffixed compile-test header. Parsing now uses exact names and the explicit recorded count; cached/missing/duplicated JVM task evidence still refuses. Both failed results and diagnosis remain preserved; these were attestor refusals, not application failures or behavioral RED.
- Publication `diff-tree --check` refused one extra trailing LF in the independent attestation test. The immutable 35,320-byte proposal remains intact. Only that blank LF was removed in the integrated 35,319-byte file; its AST including source locations is unchanged. Integrated SHA256 is `2caef95ed131ecfaadadd1910e2d5105753e6957926913d31c46ea20960c66c2`. A first formatting helper assumed CRLF and asserted before writing; its failed source is retained. `final-v3` consequently checked unchanged bytes; `final-v4` checks the actual final formatting. Earlier passing 113/134/137 cohorts are distinct captures, not extra acceptance runs to aggregate.

Independent source review closed with no remaining concrete findings (closure SHA256 `9d48ed48bddcb32987e9f729371bba9d50215107434ffd75f697d9e784b8871c`). An independent captured-evidence review read the raw test log, request pins, owners, failed/successful replay and CLI outputs without rerunning the tests. Its pre-formatting snapshot is retained separately; final source/preservation readback follows the final publication and formatting receipt. Agent review is not owner acceptance.

## Retention and remaining gates

Private evidence is under `D:\Dev\Experiments\LocalLore\2026-11-02-diagnostic-ui-build-v1`, selected source/evidence recovery under the matching `D:\Dev\Recovery\LocalLore` basename. Preserve failed phases, frozen proposals, formatting receipt, publication manifests, all original source and logs. The primary recovery manifest and later small tail records identify exact original/copy pairs. B103 captures and recovery remain untouched. No model, credentials, private stories, APKs or raw private diagnostics are added to Git.

Declared disk bounds remain source128 MiB, synthetic256 MiB, controls128 MiB, selected recovery512 MiB; no compiler/native target, Python bytecode disabled. The shared ledger remained schema v2 at SHA256 `84ad23a43f6c4abd6be82164fcec2e4e7b51277f1e250a507af22654be1a7294`; its existing `ledger-v1.json` filename does not imply schema v1. No reservation, guest, deletion, other-emulator stop, shared ADB or system setting was changed.

M10.03 diagnostic Android/SAF/offline/privacy checks, the separately pending Knowledge UI 0/4 device run, physical-device/model qualification and M10.05 remain unaccepted and separately capacity/approval blocked. Existing spent grants are not revived by this attestor. Next runnable host task: prepare a reviewed diagnostic run-profile/controller binding to this exact verifier and six-selector roster, with closed capability/ownership/cancellation fixtures; keep SDK execution gated on fresh exact admission and authorization. No merge or release is included.
