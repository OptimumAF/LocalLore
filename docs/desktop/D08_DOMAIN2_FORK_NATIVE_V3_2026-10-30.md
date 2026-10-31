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

## Actual V3 native attempt: failed and spent

Fresh admission passes for clean pushed source
`288e438140714cca3e0ad01b3fb7b729317212bc`: zero owned/ambiguous processes,
full joint reserve740,409,631B, group reserve46,187,817B and target
forecast12,359,391,057B. Root immediately chains the fixed V3 coordinator.
The one grant is consumed; no retry follows.

The actual owned app runs5.838s,03:58:29.058Z–03:58:34.896Z October31
(October30 local). Outer coordinator144.3316512s. All five inner children
close0/0/1/0/0. No timeout, output truncation/overflow, kill, unknown closure
or storage breach. Normal builds restore UNLAUNCHED. Root's subsequent
read-only process check finds0 owned/0 ambiguous app/profile processes. This
does not substitute OS process absence for the failed in-app resource check.

The report records1052 assertions/724 distinct checks and127 settled product
calls. All seven planned native images are captured. Pre-author and after-author
children are created; lost-ack recovery finds its existing child rather than
duplicating it. All three final Core-prefix child proofs match, and the
post-dispose canonical/observer fingerprints match the completed and original
histories. The final check `actual-owned-sessions-and-workers-zero` then fails
with `HarnessAssertion`. Four bounded gateway-classified `Transport` errors appear during
disposal. The raw sessions/workers values were not saved; the report does not
establish their exact values or a process leak after shutdown.

The source/report support a harness-budget diagnosis: exactly64 Host rows and
ZERO close rows are recorded. The trace counts `close` against the same exhausted
64-call allowance and rejects it before native dispatch. Controller disposal
attempts its owned closes through that trace; its rejected promises are settled
without closing the Rust sessions. The subsequent resource assertion remains
strict. A separate actual-controller/trace regression is required to test this
causal diagnosis; neither seven images nor a later source fix changes this
native failure into a pass.

## Original render inspection and diagnostic retention

Local SAME group packet `p-770a7d99-3bd0-42d9-9e4b-f28b6bcdeabc`, workspace
`d08-domain2-fork-native-c86461a9-6984-4f2b-b5fc-b7c62aa7b693`.
The205,713B report SHA256 is
`97bc9ec58b6278299f33878b3191bf665876fa9e924294fa9a54389edc2712a8`.
Root individually views all seven original application-owned CapturePreview
PNGs; no desktop imagery or control is used:

| Capture | Root's visual inspection |
| --- | --- |
| Catalog | Authored3/player, boundary selector and no-selected-receipt label readable. |
| Rejected | Authored3/omniscient; unchecked consent, disabled confirm and `ForkConsentRequired` visible. |
| Pending | Operation3; cancel enabled, retry/lookup disabled; selected context outside this documented target frame. |
| Pre-author | Selected child2/player; inherited receipt explicitly retains original main scope; identity wraps within the panel. |
| After-author | Selected child3/omniscient; no selected receipt is honestly labeled; original authored3 fork identity readable. |
| Recovered | Saved child0/player, exact lookup-only identity and no selected receipt readable. |
| Enlarged | Actual620×900 app view/150% text; UUID wraps, head3/player and fork controls readable without horizontal overlap. |

The other six images are1280×900/100% text. No visible overlap or horizontal
clipping is found in the captured targets. Content above/below each target frame
is not whole-page visual qualification. There is no eighth failure image because
the UI is already disposed when the final resource assertion fails. Actual
WebView UA remains Chrome/Edg156.0.0.0. These pixels do not prove physical-input,
screen-reader, device, model-quality or OS isolation behavior.

Root physically reads back the exclusive ordinary diagnostic copies after
restoration, comparing both length and SHA256 against their retained proof:

| Product | Bytes | SHA256 |
| --- | ---: | --- |
| Packet `diagnostic-app.js` |2,238,323 |`43ad441ab47c0c377d2f2fc4e6e7be19e13aecee5bcfd30217542cea7e508165` |
| Target `d08-fork-diagnostic-p-770a7d99-3bd0-42d9-9e4b-f28b6bcdeabc.exe` |44,253,696 |`839d3f1bf4383d65a5cc72ffc775e18eea3a569f5cd83076657c83e8f929be3f` |

Normal frontend remains574a665a…; native becomes
`ff2faad00dd7d96b41e5caac4125f08b4a740da47a14b6a64d24088ee9223220`,
matching the actual restoration record, unlaunched. The prior0d21 normal copy
is separately preserved. Both old failure histories still match their hashes.
Before Root's3,950B review record: group38,864,474B, joint721,185,758B,
target12,001,443,443B. That record brings logical metadata to667,436B, below768KiB.
No output is deleted, deduplicated or reclassified to fit.

## Bounded source correction after known closure

Separate3,048B code-only adjudication binds V3's five known closures,
STOP/attempt, both raw diagnostics, restoration, new normal hashes and Root's
process/image audit. All THREE native approvals are spent; no fourth run follows.
Code-only work retains the same768KiB metadata/48MiB group/708MiB joint,
original4GiB target and old576KiB physical/decoded records/8MiB fixtures.
The expected additional code-source/record forecast is80KiB from670,484B,
giving752,404B. A missed forecast must be disclosed; it cannot raise a hard cap.

Independent close FIRST `f2c48963` integrates as `2f118078`. Its first baseline
exits1 with EMPTY stdout because a test's rejected pending promise is observed
too late. This is retained setup failure, not valid eight-case RED evidence.
Author calibration `3a61ee88` (Root `5729823d`) immediately observes rejection
without changing the pending promise, later await or eight predicates. The
corrected baseline actually executes8:4pass/4fail/setup0, child exit1 expected and
coordinator0. Formatting `217b2939` preserves actual executable transforms.

Different-author producer `8b10581c` (Root `5f1c98a0`) changes only the fixed
development journey. Ordinary Host reads stay capped at64; four attempted
`close` dispatches get a separate cleanup allowance. Maximum Host dispatches
are thus explicitly64 reads plus4 closes, still inside256 total trace rows;
fork calls stay at128. The65th ordinary read, fifth close,129th fork and257th
row remain rejected, as do forbidden canonical Host writes. Close attempts count
before native work and are never refunded on failure. Every accepted close still
uses the real native dispatch, digest and settlement trace. This is an explicit
bounded lifecycle-policy correction, not a bypass of the boundary test.

Additive report counters distinguish reads/close attempts/fork calls/rows and
save finite sessions/workers values before the unchanged strict zero assertion.
No Controller/Rust/canonical state or observer privilege changes. Eight close,
six session, TypeScript, Native12,47mode,38path,6retention and syntax checks pass;
style then fails on two files. Both formatting failures remain retained.
`ace23470` normalizes those files, with identical actual before/after esbuild
transforms for each. Source review finds no weakened predicate or acceptance
check.

The corrected CODE gate PASSES at `ace23470`: fresh close8/style/normal build/73
normal exclusions in children12–15. Seven earlier passes4–10 (session6, types,
Native12,47mode,38path,6retention, syntax) are carried only after all named inputs
match exactly or match the two actual before/after formatter-equivalence hashes.
The actual trace/controller close cases are rerun against the final formatted
source. All15 code children close:12 exit0, plus initial setup1, valid expected
baseline1 and style1. No timeout, overflow, kill, unknown or global critical STOP.
The existing source/proof snapshots are referenced; raw streams and failures stay
retained. No Cargo/app/native invocation occurs in this reconciliation.

Final logical metadata is767,063B, under768KiB by19,369B. Actual additional
code-source/records cost96,579B from670,484B exceeds the80KiB forecast by14,659B;
the hard limit remains unchanged. Final measured group38,967,558B and joint
721,288,842B precede the small final phase record; target stays12,001,443,443B.
Normal ff2/5744 hashes remain exact. This is a corrected code result with no
post-fix native pass.

PR290 stays draft. D08, the desktop epic and model/device/OS/release gates remain
open. Any later native attempt needs a separate concrete resource decision and
fresh admission; another full20MiB packet does not fit the current48MiB group
while preserving all three failures.

## Prospective fourth attempt: not authorized or activated

The tested close correction preserves64 ordinary reads and adds only four
attempted native closes. A future application run must exercise that exact
policy and still satisfy the unchanged zero-session/zero-worker gate. No fourth
grant exists. Independent prospective Native12 FIRST `02f39139` is pushed on its
own proposal branch, UNRUN and not integrated into the active launcher.

| Resource | Current | Proposed |
| --- | ---: | ---: |
| Same retained fork group |48MiB |64MiB |
| Joint retained evidence |708MiB |724MiB |
| Fork-group logical metadata |768KiB |1152KiB |

The original-baseline4GiB target,20MiB packet,8MiB app writer, old576KiB
physical/decoded records and8MiB fixtures stay unchanged. Full joint reserve
757,186,847B fits proposed759,169,024B by1,982,177B. Target forecast
12,001,443,443+42,143,744 new normal copy+134,217,728 diagnostic bound+
268,435,456 cached build=12,446,240,371B, below the original12,554,947,872B
ceiling by108,707,501B. Fresh admission may refuse changed measurements.

The complete metadata forecast reserves the ENTIRE current768KiB allocation
(including any source-only patch/static records prepared within it),48KiB new
expanded pair,20KiB verifier,128KiB streams for eight checks,32KiB check records,
16KiB authority/admission,16KiB outer outcome,16KiB post-run review and8KiB reserve:
1,077,248B below proposed1,179,648B by102,400B. Nothing is deleted or reset to make
these forecasts fit. The prospective source patch, static/source review and
concrete new owner decision must be complete before any new admission or launch.

### Prospective source review completed; owner decision still absent

The plain local `v4-source.patch.json` is9,054B, SHA256
`56f0c483e20901dc97c3887b13926ca19ddb24a29a3450d660da3b2fe77f2400`.
Its separate plain `v4-source-safety-delta.json` is1,033B, SHA256
`e906ce3d4ceb3db38e7562350ccbeb3354299c355ca403e8ffeaa20a0f63bc99`.
Both stay immutable. Their10,087B physical source has no compression inflation;
the existing original10,825 decoded bytes remain charged independently.

Root strictly checks all22 common literal-replacement counts, subsequent file
operations, base/result byte lengths and SHA256s, and exact inverses back to the
two retained V3 scripts. Expansion happens in memory only. The final46,410B pair
fits its48KiB forecast. Node's non-executing module syntax check and PowerShell's
non-executing parser pass. Independent source review finds no remaining must-fix:

| Prospective source | Bytes | SHA256 |
| --- | ---: | --- |
| Runner |22,074 |`adef7f91dc9844873f0a5cad27d004b67e2fe6a203b4c878766001024d38e851` |
| Preparer |24,336 |`c2081ebf520a47480b210d2a14aab4b2410bf7efe2049b60252a1a6f656b1d7a` |

Source authoring retains two sizing refusals before any patch file is written
(9,959B then8,969B against the initial8KiB source allocation). Root permits9KiB
within the existing shared768KiB hard cap; no user cap changes. The primary then
reveals a PowerShell temporary clobbering the old checks-root variable. That
primary remains intact; the separate delta isolates the entire new history
block in a fixed function and renames its file temporary. One in-memory literal
anchor refusal precedes the delta write. Refused candidates and the uncorrected
primary are never parsed or executed; only the final combined source is
syntax-parsed. No experiment or native artifact is overwritten.

The prospective V4 authority rejects ALL three spent call IDs. New verification
requires the exact38-key post-V3 source roster, permitting only the separate
Native12/launcher budget amendment to differ. Seven fresh proof references and
three exact carried close8/types/session6 references bind the existing passing
code gate. All three native failure histories, known closures, ordinary raw
copies, restored products and old markers remain hash-bound. Old restoration
checks do not incorrectly demand that a freshly rebuilt normal executable keep
its predecessor's bytes. The new exclusive normal backup preserves ff2 before
build while earlier0d21/D144 backups stay intact.

Both final strict zero-owned-process observation time and admission-record time
must be0–30s old before the attempt marker and again before the sole fixed spawn.
Unknown/ambiguous ownership, storage, terminal parse or shutdown still stops.
This source refinement adds no general command or debugging service.

The1,017B static record brings current metadata to767,342B physical/778,167B
logical, under the UNCHANGED768KiB limit by8,265B. No expanded V4 script,
authority, admission, canonical record, packet or app exists. Current active
launcher bounds remain48MiB/708MiB; prospective64MiB/724MiB/1152KiB requires a
NEW owner decision, actual independent baseline/producer/checks and fresh
admission. Syntax and source review are not native execution or permission.
