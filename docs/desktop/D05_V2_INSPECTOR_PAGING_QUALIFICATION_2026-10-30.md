# D05 V2 inspector paging qualification

Refs #26, D05.03/D05.07 supporting slice. **The scoped native journey passes;
the final frontend evidence allocation fails. Whole D05 remains unaccepted.** GitHub
owns current status and claims. This report records
the preserved failures as well as subsequent checks; a later result does not
replace an earlier observation.

## Product boundary

The V2 read-only inspector adds Previous/Next navigation over the existing Rust
Query2 interface. It retains one displayed page and at most32 predecessor
cursors/4096 UTF-8 cursor bytes. Previous refetches from Rust, including the null
first-page cursor. There is no prior-page body cache or inferred total page count.
The rolling bound does not prevent further forward navigation.

Context/lens/session/head/form edits, fresh reads, source navigation, snapshot
replacement and disposal retire the chain. Navigation publishes a checked reply
transactionally; failed delivery retains the old page and cursor chain for an
explicit retry. Pending/private sequence guards fence reentrancy and late results.
The controls stay mounted before the unbounded row list. Existing legacy inspector
and Play history pagination are separate surfaces.

Rust continues to own scope, grants, observer filtering before search/count/page,
historical revisions, accepted records and actor knowledge. No Store schema,
provider, memory engine, Host wire contract or generation permission changes.
Summary/index views retain their existing unsupported results.

V2 base/header text now derives from the enclosing app text scale while retaining
the original100% sizes. Some existing descendant provenance/source labels still
use rem; this is not universal text-scale or accessibility qualification. The
native journey measures12 actual targets at100%,150% wide/narrow and restored100%,
preserving node/text/query identity; the measured results appear below.

## Independent source lineage

The frontend contract is f3add8f8 plus eca52680; native/launcher precision is
5cf0b6c2, including c4f59058/a76c500a/893e5824/1bd234fc. Independent FIRST precedes
different-author production. Root retains raw sources and executable-equivalent
formatting proofs locally.

| Layer | Independent source | Production/integration |
| --- | --- | --- |
| Frontend92 checks |32b51ecb; raw SHA6550d034f2740fdb72bb136a2be43cd732d1f58145128bf7b9cf1646ec3f8230 |6813dcb0; disposal correction dc8069fa |
| Native8 groups |ef8925de; raw SHA277fecf4c56a7f5684335262357085f5c8d1efe3df65191c2d791744ef404e16 |c5590d7e; import3528b955/formatad462979/registration5ea55714 |
| Launcher243 checks |fb86cee6; raw SHAf80bd5465eae0c6ccd5e4dc4e1b5c6b8692340d9e430b937e468793c3ad35c2d |ebc11fff |
| Actual mounted journey |eabd3d1d; raw SHA7bfb9145c7f52b7e2322a275dff726ca5200d455a61a4f0f4568a99630864cb0 |332e624b/b8a4a92b |
| Target font assertions |2efd4de6; raw SHA7560acdd2b93627565df95208d7a1cf1fa66d98e8e15f128d58e7657c4f2f1d7 |6389cf33; CSS792ffc76 |
| Restoration245 checks |57ce05b3; raw SHA27fafc9d59390bf10ad8a3b46c77940c0b5d73ea6b5735a6c3b2625a8fcf53b0 |f4ba609f; fix1f7271a5; formatdfb3a372 |
| Fixed-path38 checks |7a9284c0; raw SHA2afee4043e048058819142d415d98d7ecd6cdf4e4c28982f91747c582ab233e2 |cd7a239e/815a7bc3; production2da3ee84 |
| Native profile5 groups |b9b6d1c9; raw SHA334adc50d9067de3643da5112cd3dc4a6787a597f5f63c4f26274f373cf7a187 |6cdde0d3/a8202add; productiona66d6852 |
| Pager focus84 checks |fbd60688; raw SHAb0251401904dfc12e4ae5aaf629eaf261aeb93bb0b93b39b33b8595168147c2e |2db35501/c08df7c3; productionfe4b44d5 |

The old controller test stalled at dc8069fa: it changed context before the older
refresh had entered its intended fake RPC. Independent f7c8e158 adds bounded
readiness assertions, preserving all original stale-result assertions. Import
c9a7c316 passes21 controller checks plus existing receipt60, recorded25,
provenance46, decoder99 and routing8 checks. The original exit13/case trace and
source remain retained. This calibration does not change production scheduling.

Native FIRST initially failed compilation because its adapter parsed Host::call's
already-parsed Value as bytes. Independent978ca342 corrects only that adapter;
clean58037793 --no-run compilation passes. The first full8-group process then
reported7PASS/1FAIL at792ffc76: the history group expected catalog version1,
where the accepted constructor/decoder/contract require2. Independent daa348bd
changes that one expected token; the corrected group passes separately at
1f7271a5. Do not report a repeated all8-green process.

Independent launcher review found that restoration could overwrite changed
captured products. Its two new actual-finally cases first report244PASS/1FAIL;
1f7271a5 adds the conditional fresh product check before the first normal build,
then245/245 pass. A null snapshot still permits ordinary guarded restoration
after a known closed initial build failure. Source re-review closes the finding.

## Executed checks

All commands use physical-D checkout/caches/target and process-local TEMP/TMP on
D:. Locked offline dependencies; no upgrades or model assets. Rust1.93.1,
Cargo1.93.1, rustfmt1.8.0, Node24.22.1, PowerShell7.6.5, Windows10.0.26300.0 x64,
React19.3.1, TypeScript7.0.2, Tauri2.12.5, esbuild0.28.2, Prettier3.9.10.

| Source/check | Exact command from repository root unless noted | Result |
| --- | --- | --- |
|792ffc76 types |`node apps/desktop/node_modules/typescript/bin/tsc --noEmit --project apps/desktop/tsconfig.json` |PASS;0.328s |
|792ffc76 frontend FIRST |desktop cwd: `node check-v2-inspector-paging-review.mjs` |92/92;0.837s; synthetic Gateway/controller and actual-panel SSR/handlers, no mounted browser |
|58037793 fixture calibration |`cargo test -p locallore-desktop-spike --bin locallore-desktop-spike --features dev-harness --locked --offline v2_inspection_paging_harness::review_tests::actual_recipe_has_exact_seed_fork_receipts_and_readonly_oracle_tuple_hashes -- --exact --nocapture --test-threads=1` |1/1;4.692s command/4.13s test; retained template339,968B |
|792ffc76 original native FIRST |same package/bin/features/locked/offline, filter `v2_inspection_paging_harness::review_tests:: -- --test-threads=1` |7PASS/1FAIL;12.287s command/11.76s tests |
|1f7271a5 corrected group |same flags, exact filter `v2_inspection_paging_harness::review_tests::actual_host_current_historical_search_and_marker_pages_match_the_fixed_roster -- --exact --nocapture --test-threads=1` |1/1;16.609s command/3.34s test |
|792ffc76 strict native lint |`cargo clippy -p locallore-desktop-spike --features dev-harness --all-targets --locked --offline -- -D warnings` |PASS;11.393s; compilation only, no qualifier execution |
|792ffc76 Rust format |`cargo fmt --all -- --check` |PASS;3.853s |
|792ffc76 Android bridge |`cargo test -p locallore-android --lib --locked --offline` |23/23;3.466s command/1.32s tests; Windows-host Rust only |
|a940c3a8 launcher FIRST |desktop cwd: `node check-v2-inspector-paging-process-review.mjs` |245/245;0.307s; actual private source in VM with disclosed child/timer/file doubles |
|a940c3a8 changed frontend targets |Prettier --check over10 changed UI/launcher/verifier/FIRST targets |PASS;0.650s |
|2da3ee84 fixed paths |desktop cwd: `node check-v2-inspector-paging-path-review.mjs` |38/38;0.133s; actual private path block in VM, string/caller-order checks only |
|2da3ee84 launcher policy |desktop cwd: `node check-v2-inspector-paging-process-review.mjs` |245/245;0.290s |
|a66d6852 native profile |same native package/bin/features/locked/offline; filter `v2_inspection_paging_harness::profile_review_tests:: -- --test-threads=1` |5/5;42.367s command/0.03s tests; filesystem helper only |
|3b835f9f strict lint |same strict native Clippy command above |PASS;8.110s |
|3b835f9f Rust format |`cargo fmt --all -- --check` |PASS;5.532s |
|3b835f9f calibrated profile boundary |same native flags; exact `v2_inspection_paging_harness::profile_review_tests::profile_limit_counts_utf16_units_with_exact190_and191_unicode_boundaries -- --exact --test-threads=1` |1/1 separately;23.131s command; Rust reports0.00s test |
|628b4434 focus FIRST |desktop cwd: `node check-v2-inspector-paging-focus-review.mjs` |84/84;0.165s; actual helper/controller/panel handlers with disclosed DOM/rAF/hooks doubles, no browser/native execution |
|628b4434 paging regression |desktop cwd: `node check-v2-inspector-paging-review.mjs` |92/92;1.009s |
|628b4434 types |desktop cwd: `node node_modules/typescript/bin/tsc --noEmit` |PASS;0.317s |
|b87ecc3a native UI/IPC |desktop cwd: `node v2-inspector-paging-harness.mjs` with the admitted closed budget record and existing physical-D artifact/target/Cargo directories |PASS;47.247s launcher/11.356s app;5,248 assertions/942 distinct checks;20 app-only captures |
|b87ecc3a full frontend |desktop cwd: `node verify-frontend.mjs`, with explicit D05 `LOCALLORE_CHECK_OUTPUT_DIR` |Functional PASS;76 child commands;23.179s. Final evidence allocation FAIL below |
|b87ecc3a frontend format |`node apps/desktop/node_modules/prettier/bin/prettier.cjs --check "apps/desktop/ui/*.{ts,tsx,html,css}" "apps/desktop/*.{json,mjs}"` |PASS;2.801s |
|b87ecc3a Rust format |`cargo fmt --all -- --check` |PASS;1.957s |
|b87ecc3a strict native dev lint |same strict dev/all-target Clippy command above |PASS;8.616s; compile only |
|b87ecc3a strict native normal lint |same Clippy command without `--features dev-harness` |PASS;9.498s; compile only |

Native FIRST executes production Store/Workspace/Host/Engine, not IPC/WebView.
Its source-planned positive recipe has45 canonical operations/44 ordinary turns
and91 public setup writes;91 is a reviewed call roster, not invocation telemetry.
One extra typed Wait exists only on an isolated negative-control copy. Eleven
roots from calibration/full process/corrected group are retained, including tiny
and empty controls. Passed existing Android tests own their ordinary ephemeral
test cleanup; no manual deletion or recovery cleanup occurred.

## Preserved launcher/native setup failures

`dfb3a372` launcher exits1 in16.318s at source-freeze metadata: duplicate long
absolute keys produce272,389B, exceeding the unchanged256KiB cap. No harness
build, fixture, app, IPC or PNG. Global finally restores normal frontend/native
products without launching them. Packet suffix53230c24-109f-4137-a251-0792a3840b13
is retained. a940c3a8 uses relative keys for exactly the same726 resolved files,
hashes and order; roster153,325B. Independent source review closes this alias-only
correction; the resolved-roster proof SHA is
9debca44511227476a5eb5afaec19abb5aee2921f898caee5fee0221ef977837.

`a940c3a8` launcher exits1 in28.260s. Its native app process known-closes with
exit2/SyntheticFixtureInvalid after0.325s, before a WebView exists. Four empty
reserved SQLite files remain; ordinary database path length269 UTF-16 units.
Packet suffixcf28335d-34d9-476e-91d6-385020d92b05 is retained; no UI checks/PNG.
Normal frontend/native products are restored and left unlaunched; no unknown
drain or storage latch in either attempt.

Pinned-source review supports a Windows path-length hypothesis, without proving
the exact collapsed failure stage. Rust reserves the four leaves first. rusqlite
passes the ordinary string to SQLite's default win32 VFS; its mxPathname is
260*4 UTF-8 bytes, not a direct260-character SQLite rejection. That VFS converts
to UTF-16 without adding an extended prefix before CreateFileW. The existing
Tauri default manifest lacks longPathAware. No Store/VFS/manifest/registry/global
setting is changed. Independent7a9284c0 freezes38 path/caller assertions before
Root production2da3ee84: fixed p-UUID packet basename, unchanged workspace leaf,
one planned database before Git/admission/mkdir, and refusal above248 UTF-16 units.
The first missing-seam run at815a7bc3 is UNRUN_SETUP:38 authored/0 executed/0 pass,
not behavioral RED. After production,38/38 and the unchanged245 policy cases pass.
No fallback or alternate base; all prior packets remain counted. These are VM
string tests; their pass alone is not successful native database creation.

`33e85a38` subsequently creates the actual339,968B fixture at a244-unit ordinary
database path. Its native process then known-closes with exit101 after67.078s:
Tauri setup reports WebView2 HRESULT0x80080005, Server execution failed, before
frontend/IPC/UI execution. Launcher95.803s; packet
p-dd46903c-8ffe-4684-b8d0-f1118b142a14 retains the database, empty evidence/profile
directories and bounded stderr. Zero PNGs and no journey report. Normal products
restore successfully and remain unlaunched; no unknown drain/storage latch.
Final packet498,820B; paging14,406,423B; joint516,051,076B; target growth76,895,207B.
Successful shorter database setup supports the earlier path diagnosis, without
proving the exact prior collapsed failure stage or this new WebView2 cause.

A D05-only shorter fresh profile layout is implementeda66d6852 after independent
b9b6d1c9 FIRST. It derives packet/webview-profile beside the unchanged workspace
directory, under the same measured packet; the source-known old/new profile
addresses are242/174 UTF-16 units. It creates nothing itself, accepts only absent
metadata, and does not move/reuse/delete the failed profile or affect normal/other
modes. A conservative190-unit ceiling is a local test-layout budget, not a
Microsoft limit or proven HRESULT remedy. [Microsoft's UDF guidance](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/user-data-folder)
supports custom writable app-owned data directories; it does not establish this
failure's cause. WebView rendering was unverified at that source; the later actual
runs are recorded below. No installed runtime, registry, permission, browser option or other
app is changed. Absence validation is cooperative, not atomic OS isolation.

Five actual-helper filesystem groups pass at a66d6852, retaining seven tiny
packet roots/two padding ancestors. Subsequent strict Clippy stops on two FIRST
style diagnostics; no production warning is reported. Independent0de936c1 keeps
the Windows assertion in a const block, expresses the same inclusive range with
contains, and uses unique ASCII hex material in the unchanged emoji padding length
so a later explicitly admitted run need not collide with preserved test parents.
All five groups and190/191 assertions remain. Raw calibration SHA is
aca7fd3c6759e63e4b055405dde3b7b1c7f774ee1ea826d654a3025cb6c51fba;
format-only derived/actual SHA3111da425ca9f271c3c72cd9bc00cfafab8d905f4cf1d7ca234bc443f8a41de9.
At3b835f9f strict Clippy/format pass and only the calibrated boundary group runs
again, passing and retaining two more tiny packet roots/two padding ancestors.
No repeat of the full five/recipe cohorts, SQLite, WebView or model in these tests.

## First actual mounted pager result

At cleanfa1d5e38 the shortened fresh profile successfully creates the hidden,
unfocused WebView2. This does not prove the prior HRESULT's exact cause. Actual
normal native IPC reads the fixture, mounts the first Player history page,
follows/refetches permitted original-event evidence, and Next displays the real
second64-row page of130. The journey then fails
next-second-no-row-or-unrelated-panel-focus-steal: the same Next control remains
mounted and is reenabled, but automatic pending-disable blur leaves focus on BODY.
The enabled-completion assertion remains unchanged. Runtime UA is
WindowsNT10.0/Win64/x64, Edg156.0.0.0.

The launcher exits1 after60.268s with known child closure, normal frontend/exe
restored/unlaunched and no unknown drain/storage latch. Native error buffer is
empty. This is a failed partial native journey, not a twenty-capture pass.
Packet p-e1d4ed35-07b9-4527-a6d5-0445273d1912 is retained10,737,705B; measured
cumulative paging25,232,868B/joint526,877,521B at closure. No final canonical oracle,
observer-switch,150% or disposal acceptance follows the early failure.

Exactly two PNGs were produced and individually inspected by Root: d05-page-first
and d05-page-failure. Both show coherent primary/paging, Player/gameplayactorplayer,
head44/inspected44, fake fixture/durable/idle labels and readable real row identities.
Context header and actual pager/status fit together without required pager clipping
or overlap. The upper query form is partly scrolled behind the sticky context by
the chosen navigation framing. The failure frame shows a real second page, one
predecessor, enabled controls and absent button focus; Player-only row022 is
authorized under Player. No physical input/accessibility acceptance is implied.
Local per-image path/SHA/UA/notes record native-fa1d5e38-image-review1.json has SHA
497b863a20eaee5b02e28cfe3cd816cd28f69c689005494f35ad67f6c45f54aa.

The [guarded focus correction contract](D05_V2_PAGER_FOCUS_CONTRACT_2026-10-30.md)
is independently reviewed at91acb40e before different-author FIRST/production.
It preserves disabled semantics, guards context/user focus and requires actual
reentrant-controller cases. Acceptedmain328eefe5 is reconciled asdd761ed4; its69 commits do
not change desktop/shared Rust/Cargo inputs compared with the testedfa source.

Independent FIRSTfbd60688 freezes84 cases before Root productionfe4b44d5.
The missing-helper baselinec08df7c3 is UNRUN_SETUP,84 authored/0 executed/0 pass.
The first production process reports80PASS/4 fixture-readiness failures; all four
real-controller cases stop at RealControllerFixtureMustBeBound before focus.
The test loads the actual strict decoder into a different VM realm while passing
ordinary outer-realm DTOs; its prototype guard correctly refuses those objects.
Independent calibration1bdc5572 changes only bundle loading to a local CommonJS
IIFE in the same Node realm, with evaluation still under the original1000ms
timeout. All84 case bodies/assertions and actual imports remain unchanged; no
production decoder or fixture is weakened. Raw/derived bytes are identical, SHA
3c198202ad6664a2786f72e70d93bf354874d6840d55ec69c2536f0a637ac660.
At628b4434 all84 execute/pass, including both actual-controller reentrant listener
orders, disposal and six actual-panel handler/cleanup cases. These use disclosed
DOM/rAF/public-state and panel-hook doubles, not a mounted browser. Original80/4
and setup baseline remain retained.

The focus helper and panel subscribe only to public state, own one interaction,
retire on user/context/new-operation changes, and use one guarded animation frame
to restore only the original enabled button from BODY. Weak identity metadata is
bounded to64 notifications and retains no page bodies. Independent source review
atfe4b44d5 closes without actionable findings.

Independent journey calibrationfd29335f recognizes only the two existing capture
revocation operations during normal disposal. It adds a stronger settled
close/revocations-only post-dispose roster assertion; every original20-label and
focus assertion remains. That postcondition executes successfully in the run below.

## Completed scoped native journey

At cleanb87ecc3a, one admitted closed run passes in47.247s including builds and
restoration; the actual app runs11.356s. Hidden, unfocused native WebView2 uses
normal IPC and the actual mounted UI handlers. No headless/browser substitution,
desktop capture/input, model execution or SDK/device work occurs. It produces
exactly20 success captures,5,248 assertions/942 distinct checks,79 Gateway calls,
48 inspection queries,42 page proofs and5 read-only oracle proofs. The four
deliberate native negative probes return exactly Scope, Stale, UnknownObserver
and InvalidCursor; those are the bounded error buffer's four expected entries.

Actual first/second/last pages, backward refetch, repeated forward refetch,
post-successful-IPC held/drop/retry delivery, literal-search reset, historical
revision23, Player/Mira/Sable/Omniscient lenses, another story/session, same-head
snapshot replacement and stale delivery execute. Canonical/actor/seed/projection/
record/receipt/turn hashes remain unchanged across all three fixture scopes,
including the final oracle after disposal. Post-dispose Gateway work is limited
to settled close and the two exact capture revocations. Inspection does not
change gameplay actor permissions or character knowledge.

All six enabled-completion observations restore the original focused pager.
Six first/last disabled-boundary observations leave focus on BODY without a peer
fallback; this is an explicit accessibility limitation, not universal focus
qualification. Each of12 named actual font targets measures baseline100%,150%
at1280x900 and620x900, and restored100%, within0.05px. Existing descendant rem
labels outside that roster remain outside the scaling claim.

Root individually viewed every generated PNG. Context, pager labels/status and
record identities remain readable without required-control clipping, horizontal
overflow or overlap, including enlarged narrow layout. The upper query form is
partly scrolled under the sticky context in navigation framing. Other-story
selection shows its own receipt; empty observer/stale snapshots show no old row
body. Unsupported summaries show the actual unavailable response and no substitute.
Per-image hashes/notes are retained in native-b87ecc3a-image-review1.json, SHA
3faa03dcbbf445436b1f9b29338a9b17ae4bcbcbba3c2cb4f10b02f917e2694a.

Packet suffix5d2d0b8c-52d1-4359-a1ee-afdeaba3d052 retains the reports, semantic
snapshots,20 images, synthetic database and app-owned WebView profile. At launcher
closure: packet12,717,243B, D0539,917,353B, joint541,562,006B and target growth
78,023,959B. All children known-close, normal frontend/executable restore and
remain unlaunched, with no unknown drain or launcher storage latch.

## Final frontend allocation failure

The76-command registered frontend driver functionally passes, including strict
types, all existing checks and exclusion of development controls/journey markers
from the normal frontend. Both final native Clippy configurations compile only;
the stopped qualifier, AppContainer/network probes and frozen real-model cohorts
are never executed. This does not replace the native UI evidence above.

The subsequent inventory FAILS UnchangedResourceCap: the explicit frontend output
root retains38,790,893B/214 entries against its declared32MiB/33,554,432B allocation,
an overrun of5,236,461B. Multiple retained actual-source bundles account for the
underestimate. This coordinator allocation had a post-run inventory, not a live
pre-write enforcement guard. Functional PASS and resource FAIL are separate.
The failed boundary is not raised, reset or reported green; no output is deleted,
and further test/build/native execution stops. Only the originally reserved final
metadata/documentation and source review proceed.

Measured D05 is79,221,913B/1,083 entries, joint580,866,566B and target8,338,402,270B/
growth78,421,694B. The original D05128MiB, joint640MiB and target-growth2GiB caps
remain intact; all previous failures/captures remain charged. Local failure record
final-frontend-allocation-failure-b87ecc3a1.json SHA is
c1a5b24b9b74afc9d2594531087287ffe7969740e1337203cde75bda398d3a7a.
No further run is admitted by this report. Future verification needs a fresh,
prospective bounded output plan; it must not reinterpret this failed allocation.

## Resource and acceptance limits

All raw/derived/proofs/logs/failures/SQLite/packets remain local and ignored under
the same D05 gate. No cleanup, baseline reset or hidden replacement root. The
preserved selected4 qualification is501,644,653B under its512MiB cap, including
40 separately measured external entries. D05 has128MiB and joint selected4+D05
640MiB caps, with64MiB expected headroom before a native packet. Original shared
target baseline remains8,259,980,576B, with2GiB growth cap. Packet/native writer
64MiB; source growth128MiB; inventory2million entries; final metadata reserve1MiB.
These named rosters do not claim to inventory all historical model/project data.

Closed launcher has no CLI selector, scrubs all case-insensitive LOCALLORE_
aliases and gives its native child only the four fixed mode/workspace/artifact
keys. Git15s, Node240s, Cargo900s, app180s, one best-effort stop/5s grace; each
stream256KiB. Unknown direct-child ownership or failed/over-budget inventory
sticks and forbids later Git/native/restoration work. This is cooperative
child-boundary accounting, not process-tree containment or OS isolation.

The20-label mounted UI/IPC journey, every resulting image inspection and12-target
font measurements pass. The final frontend driver functionally passes while its
evidence allocation fails as recorded above. No all-gates-green result is claimed.
Physical keyboard/screen-reader, native restart/process death, actual model,
Android SDK/device, OS/network isolation, packaging/release and whole D05/desktop
epic gates are not qualified by these checks. Delivery hold/drop are explicitly
post-successful-IPC doubles, never Rust worker cancellation or inference tests.
