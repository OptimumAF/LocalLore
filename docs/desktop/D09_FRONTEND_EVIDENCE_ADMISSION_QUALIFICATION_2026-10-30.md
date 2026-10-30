# Prospective frontend evidence guard qualification

Refs #31, partial D09.03/.04/.07. **Focused checks and the actual bounded77-child
frontend runner pass. Whole D09 remains unchecked.** This report
does not change the failed D05 allocation or admit another run.

The [contract](D09_FRONTEND_EVIDENCE_ADMISSION_CONTRACT_2026-10-30.md) defines the
closed opt-in `node verify-frontend.mjs --bounded` interface. The existing76 checks
retain their order/arguments, with one independent guard check added. Legacy
zero-argument mode remains available. No UI, Rust, Host schema, inference, Android,
dependency, repository setting or application capability changes.

## Trigger and product boundary

The [D05 paging qualification](D05_V2_INSPECTOR_PAGING_QUALIFICATION_2026-10-30.md)
records actual native success and a separate frontend evidence FAIL. Its declared
32MiB allocation retained38,790,893 bytes in the designated directory. A later
source audit finds four additional unique bundles/276,119 bytes outside that
directory: combined39,067,012 bytes, exceeding32MiB by5,512,580 bytes before outer
logs/build products. The original narrower report/failure record is frozen;
append-only reconciliation charges those four files once, without duplicating
older D07 bundles. No deletion, cap reset or retroactive passing result occurs.

The new runner validates an existing ordinary physical-D output directory/_tmp
and a separate canonical eight-key, source-bound admission record. It inventories
before/after each fixed step, reserves4MiB plus1MiB metadata before advancing,
and checks positive per-step output/product growth. Fixed dist/host.generated.ts
products have their own16MiB ceiling and count in aggregate accounting. Four old
checks now honor the explicit output directory; their original mkdir/UUID/build/
assertion suffixes remain unchanged.

Children receive the owned output/_tmp directory as TEMP/TMP. Fixed Git reads
and Node checks use bounded streams/deadlines; total encoded console output is
4MiB with a jointly reserved32KiB final record. Unknown closure or a budget failure
stops later children/Git/bundle-read/success. Unknown-close cleanup attempts both
pipe destructions and child unref independently, while keeping ownership unknown.
This is cooperative accounting/reference cleanup, not an OS filesystem quota,
process-tree containment, network/privacy qualification or proof a child stopped.

## Independent tests and retained failures

Root implements production after different-author FIRST freeze and a missing-
producer baseline. The source author runs no checks. Raw sources, formatter
equivalence proofs, reports and earlier failures stay local/ignored.

| Source | Check/result |
| --- | --- |
| e6519c7f | Original148-case FIRST; raw SHAb940461447098a70e40fb1aa06a267871dbac55cc351cb3a2e112b7fc3505af9 |
| a3b37167 | Pre-producer oracle calibration distinguishes quoted child PASS from global success; adds149th case, preserves all148 bodies; raw SHA1b1ec6052e405ade057aeb5cabb8b822c7b8b34de60e8b0682716a7fdef57810 |
| 1964aed5 | Actual missing-producer baseline:149 authored/0 executed/0 pass, exit2/UNRUN_SETUP;0.081s; not behavioral RED |
| d2407902 | First actual149 process:139PASS/10FAIL;0.222s; original report retained |
| 43639ff4 | Independent adapter correction only; actual149/149;0.264s; production unchanged |
| 918d6637 | Independent22-case review extension,171 total; raw SHAb307130616db8b1d6b485ba9f7944ee2f0e7c5f9e146a28d29bebb10d6caef43 |
| 14633299 | Actual171 process before production fixes:149PASS/22FAIL;0.368s; every new review control fails |
| f3499b92 | Narrow production fixes, unchanged171 checks:171/171;0.265s |

The first ten failures arise from adapter semantics: the URL double discarded a
directory separator that actual Node preserves, and its fixed microtask batch
could advance a virtual four-minute timeout ahead of an already queued close.
Independent43639ff4 preserves the directory separator and yields one actual event-
loop turn before advancing virtual time; no real deadline is waited. All149 case
bodies/limits remain. The first diagnostic copy refused an argv prerequisite
before any case; a separate corrected one-case diagnostic and actual Node URL
primitive support the diagnosis. These are not native application tests.

Source review then finds three real defects: coordinator pipe/process references
could remain after unknown-close grace, initial Git preceded D: validation, and a
missing required ui parent counted as zero products. Independent918d6637 freezes
22 controls before Root fixes them. Default synthetic fixtures gain a faithful ui
parent/valid parent TEMP; original149 case statements are unchanged. Root's exact
range comparison hashes both copies to
99aa92214f8910911b0839b75f6447dd8b875dbcb8036ee45e4f06368ebdc7e3.
Raw171 and formatted171 have executable-equivalent canonical SHA
da43c9a33bf22f62850b12085182f6db7b5792fa7189ebc6acd6d590ccdb6827.

The171 checks execute actual helper/driver/preamble source with disclosed in-
memory filesystem, process, Git and virtual-deadline doubles. They are neither
actual Windows child-lifetime nor filesystem quota measurements. One explicitly
test-only derived module changes only the compiled entries literal from2million
to12, proving prefix/suffix identity and exercising combined unique-entry counting.
The unmodified2million constant is separately asserted; an actual two-million-file
boundary is unrun. No million-entry physical fixture is created.

## Actual focused commands

Physical-D checkout, pinned installed Node24.22.1, esbuild0.28.2, Prettier3.9.10;
PowerShell7.6.5/Windows10.0.26300 x64. Commanding shells set TEMP/TMP D:/Dev/_Temp.
No provisioning, downloads or upgrades. esbuild uses its installed native BUILD
TOOL service; this is not native app, WebView, Rust engine, model or SDK execution.

From apps/desktop, at clean unchanged f3499b92 with an explicit owned D: output:

| Command | Result |
| --- | --- |
| `node check-frontend-evidence-policy-review.mjs` |171/171;0.265s; actual source with disclosed doubles |
| `node check-contract.mjs` |exit0;0.214s;25 original fixture/schema cases and four controller action builders |
| `node check-export-controller.mjs` |exit0;0.113s; actual controller, synthetic Gateway |
| `node check-model-controller.mjs` |exit0;0.089s; actual controller, synthetic Gateway |
| `node check-inspection-controller.mjs` |exit0;0.179s; actual controller, synthetic Gateway |

All four actual routed bundles appear under the designated output:276,119 bytes
total. Their original tests/assertions are retained; this does not imply actual
native IPC despite older test messages referring to native operations.

## Actual bounded frontend runner

After independent source closure of f3499b92 and a fresh prospective admission,
clean14f3f8dc executes `node verify-frontend.mjs --bounded` successfully in25.853s
(2026-10-30T14:30:34.1056092Z–14:30:59.9587112Z). Its only later source changes
are documentation. This is actual Windows Node/build-tool/filesystem execution,
not desktop app, browser, native IPC, Rust engine, model, SDK or device execution.

All77 recorded direct Node outcomes are code0/known-closed, with no stop attempt,
timeout, stream truncation or child error. The added self-check executes171 cases;
the retained76 arguments/order hash remains
d021b7a801f051bac71799528cb000c5b8a6636cfa6f81cc2d615877e79a0ec0.
Initial/final fixed Git source fences succeed; this is not independent OS-wide
invocation tracing or process-tree containment. Source remains clean/unchanged.
Strict TypeScript, fixture/schema/controller checks and all67 normal-bundle hook
exclusions pass. Full frontend format check additionally passes in2.657s.

The driver records initial output276,119B, final39,343,131B and live products718,456B.
The prospective48MiB output limit,4MiB per-step positive retained growth,1MiB
metadata reserve,16MiB product limit and640MiB aggregate checks all pass. This
does not measure peak transient writes or enforce an OS quota. No file is created
or modified in the legacy source artifacts/checks directory during the measured
interval. The normal frontend retains its D05-tested SHA
ddde5846787854b27dbcf39fdb082622444273b5e7c62ae91fd92b8436ad490e.

Independent local record replay verifies all77 indexes/outcomes, the original76
roster and the single finished summary. Actual encoded console output354,604B
has SHA9887c43dd29071534503e4ed9a662f5102c95279dd9eede4c3c1f6cd6514c99a,
within4MiB. The338-byte canonical admission record has SHA
4788d6a2e575c5fd7ce7c0d5ea62cf3ce0c613c452f508678cb37814b80af7a4.
It binds the source/output/baseline and is consumed, not reusable run permission.

At the final read-only inventory, D09 retains40,267,350B/264 entries, including
both phases, every earlier failure/proof, routed bundles, console and metadata.
Its focused phase closed at834,526B under8MiB before this separate full-run plan;
combined D09 remains under64MiB. D07 retains501,644,653B; D05 root plus its four
escaped bundles retains79,500,962B; live normal products add718,456B. Named total
622,131,421B plus the reserved1MiB final metadata fits the unchanged640MiB ceiling.
No manual cleanup, discarded evidence, baseline reset or alternative root occurs.
Ordinary build-tool scratch cleanup is distinct from deleting retained evidence.
This new prospective gate passes; the original D05 allocation stays FAILED.

Rust/Host/UI/Android/dependency input paths have no changes in this slice. Their
previous qualified evidence keeps its original attribution; no additional native
app/Rust/Android/device qualification is inferred from these developer checks.

For a FUTURE separately admitted whole run, use existing physical-D directories
and a NEW canonical record as specified by the contract, then:

```powershell
$env:TEMP = 'D:/Dev/_Temp'
$env:TMP = $env:TEMP
$env:LOCALLORE_CHECK_OUTPUT_DIR = 'D:/Dev/LocalLore-evidence/owned-checks'
$env:LOCALLORE_CHECK_BUDGET_FILE = 'D:/Dev/LocalLore-evidence/new-admission.json'
# owned-checks and owned-checks/_tmp already exist; record matches fresh inventory
# and exact clean source HEAD. Do not reuse a consumed/failed admission.
node verify-frontend.mjs --bounded
```

These illustrative paths are not an admission or a command to recreate old roots.
Retain previous failures and charge all named external evidence; no full driver
or application run follows merely from this document. The measured bounded-driver
gate above is complete for this scope; remote PR review is separate.
UI/Rust/Android/real-model/
keyboard/offline-install/OS isolation and whole D09 gates are separate.
