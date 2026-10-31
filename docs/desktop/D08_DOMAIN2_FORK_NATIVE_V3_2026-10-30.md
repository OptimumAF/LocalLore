# Domain2 fork V3: bounded admission and attempt record

Refs #30 D08.04/.07, #12 M08.04/.06 and PR290. This continues the
[failed V2 attempt and source correction](D08_DOMAIN2_FORK_NATIVE_V2_ATTEMPT_2026-10-30.md).
Both earlier failures, STOP/attempt scopes, packets, products and limitations
remain unchanged. V1's missing raw diagnostic copies are not repaired by V2.

## Owner decision and frozen bounds

The owner answers `call_983daf6fa26f4dc89bcb271b29ee59b5`, “Approve one bounded
V3 run.” The grant covers bounded preparation/checks/builds, ONE further native
fork run, seven success captures/max eight, individual image review and normal
restoration after confirmed closure. It permits no automatic retry, desktop
control, model/device/SDK/OS qualification, download, deletion or release.

| Resource | Approved V3 bound |
| --- | ---: |
| Same retained fork group, including both old packets |48MiB =50,331,648B |
| Joint retained evidence |708MiB =742,391,808B |
| Group metadata, including decoded source operations |768KiB =786,432B |
| Target growth from original8,259,980,576B |4GiB; ceiling12,554,947,872B |
| One packet, including workspace/profile/images/logs |20MiB |
| Sticky application artifact writer |8MiB |
| Existing old code records |576KiB, both physical and decoded |
| Existing new synthetic fixtures |8MiB |

The full joint forecast740,409,631B retains the entire48MiB group and old
record/fixture reserves. Target forecast12,359,391,057B includes a NEW ordinary
42,143,744B normal executable copy,128MiB diagnostic bound and256MiB cached build
allowance. Metadata forecast767,979B includes decoded source operations and the
separate safety delta reserve. Fresh admission must remeasure every cohort,
physical-D source/product identities, free space, original target and process
ownership; these forecasts are refusal checks, not OS quotas.

## Independent baseline and producer

FIRST `6950de08` integrates as `bf7b056a` before the different-author producer.
Root's actual Native12 baseline executes12:8pass/4fail/setup0, child exit1 as
expected. The no-app coordinator closes0 and records the failed behaviors
without changing their status. It neither seeds a fixture nor launches an app.

Producer `4ba2286c`, integrated `61b585f6`, changes exactly two fork constants:
group32→48MiB and joint692→708MiB. Paging remains2GiB target/640MiB joint,
browser remains4GiB/660MiB; fork target4GiB/packet20MiB/writer8MiB stay unchanged.
Independent source review finds no further defect in that two-line change.

The first verification passes Native12/47mode/38paths/6retention/syntax, then
fails style on the independent checker. That source failure stays retained;
no native attempt starts. `62e080c7` formats only that checker. Actual before/after
esbuild transforms are identical (13,404B each), and independent diff review
confirms all12 cases/predicates unchanged. The complete fixed code gate is rerun.

## Coordinator and preservation controls

The exact reviewed local source pair is materialized only after the new grant:
runner20,160B SHA256
`4e60da196fcc683ad4edb7b1460a4dbac6bb9647b8a714ea09ae498a222a3906`;
preparer21,936B SHA256
`2ce19edefa02535b0cff10fea0191e00e91100c85315623f31a67192e7950bbc`.
The original compressed patch, separate plain safety delta and both static
records remain retained. Metadata charges10,825 decoded original-operation
bytes in addition to physical file sizes. Neither group nor target accounting
mislabels decoded memory as physical disk growth.

The new authority rejects both spent call IDs. Admission/runner bind both old
failure histories, five-child known closures/restorations, V2 physical diagnostic
copies, current normal products, clean Git head, current complete source and
fresh code proofs. Admission age must be0–30s before marker and fixed spawn.
The new normal copy is exclusive and preserves the earlier D144 copy.

The bounded no-app verifier has only baseline/verify phases and eight fixed Node
commands, with8KiB per output channel and an8KiB terminal reserve. It launches
no Cargo/app/native path. Review catches a missing prior CODE2 stop check before
execution; the corrected source checks it before/after children and writes the
shared V3 STOP on critical/unknown failures. The small inverse edit preserves
the exact earlier unrun source. Verifier+edit total15,985B fits its16KiB allocation.

The outer native runner parses four required inner terminal booleans BEFORE
recording or rejecting nonzero exit. Missing/malformed terminal data becomes
unknown. Inner uncertainty/storage flags remain sticky; outer inventory failures
also stop permanently by reason. `storageBreached` specifically reports the
inner storage latch. Unknown closure/storage/ownership blocks later operations;
normal restoration is not allowed to overwrite unpreserved failed products.

## Reproduction and evidence boundaries

Use the physical-D checkout and `TEMP=TMP=D:\Dev\_Temp`, Node24.22.1,
PowerShell7.6.5 and the existing pinned offline Rust1.93.1 cache/target. Native
build settings remain one job, incremental0 and dev/test debug0. Do not add
global SDK/cache overrides. See the V2 report for frontend/runtime versions.

From `apps/desktop`, source checks are:

```powershell
node check-domain2-fork-native-review.mjs
node check-domain2-timeline-browser-native-mode-review.mjs
node check-v2-inspector-paging-path-review.mjs
node check-domain2-fork-retention-review.mjs
node --check v2-inspector-paging-harness.mjs
node node_modules/prettier/bin/prettier.cjs --check 'ui/*.{ts,tsx,html,css}' '*.{json,mjs}' src-tauri/tauri.conf.json
node build.mjs
```

The fixed local `v3-code-checks.mjs` stores exact arguments, tool/source hashes,
streams, counts, closure and timing in `v3-code-process-*.json`; normal readback
uses the existing `normal-exclusions.mjs` and its73 assertions. Seven source-bound
proofs are required before admission. Earlier TypeScript/Rust/Android-host/Clippy
checks keep their existing attribution; no source/shared/Rust change justifies
claiming those checks rerun here. The245 process-policy/full77 suite is not rerun.

Source/VM/controller doubles, parsers, build checks, actual native IPC, actual
WebView rendering and model/device/OS acceptance are separate evidence classes.
No native success or whole-D08/desktop acceptance follows from this code gate.
Only synthetic fixtures are used; raw local generated evidence stays outside Git.

## Actual results

The corrected code gate PASSES at `62e080c7`: Native12/12, legacy mode47/47,
paths38/38, retention6/6, syntax, full style, normal frontend and73 actual normal
exclusion assertions. All15 fixed helper children close:13 exit0 plus expected
baseline exit1 and the retained style exit1. No timeout, overflow, kill, unknown
closure or new critical STOP. Final proof uses fresh children8–15; earlier
passing children are not substituted for the rerun.

Nine bounded in-memory cases additionally execute the actual extracted runner
terminal-classification statements: known failure, pass, inner unknown, inner
storage, both latches, missing field, malformed JSON, null and sticky outer
unknown. All9 pass. These synthetic terminal inputs spawn no children and prove
no actual shutdown or storage behavior. The796B record is retained separately.

Metadata after that record is652,330B logical (including10,825 decoded operation
bytes), below768KiB. The full new source, formatting failure/equivalence and
repeat verification costs stay charged. Normal frontend remains
`574a665ac1448769c84293e52bc3043c474c5a4c656d79bbb253162c621b79e7`;
normal native remains
`0d21c6e587cf51fcbe2c56cec3290a55a2e02c78f04785d1b37f1c784fb68e2f`,
unlaunched. No Cargo build, native app or new packet occurs during this code gate.

The one native attempt is pending at this checkpoint. Fresh admission is
required before the sole invocation. No second attempt is authorized if it fails.
This section will record the actual outcome without reclassifying earlier
failures. D08, the desktop epic and the broader acceptance gates remain open.
