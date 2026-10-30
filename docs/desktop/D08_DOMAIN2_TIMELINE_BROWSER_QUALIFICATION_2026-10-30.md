# Saved Domain2 timeline browser: source checks and failed native attempts

Refs #30, partial D08.04/.07; supporting #26 D05.01/.07. **Frontend implementation
and focused source checks pass. The new native browser journey has not passed.**
Full D08 and the desktop epic remain unchecked. Native4's human assessment remains
"Reviewed: needs improvement"; this slice makes no model-quality claim.

## Product and authority

Accepted main3178f085 already has the shared saved catalog and Domain2 resume
adapter. This change exposes the existing Saved timelines panel in Domain2 Play
and Story Lab, validates its selected scope/head, and fences captured callbacks
after story/session/head/view/observer changes. It keeps the Domain2 Fork panel
excluded. The browser uses the existing catalog and normal Controller resume path;
it adds no storage writer, session owner, inference, character knowledge, archive
format or shared engine API. The observer remains an inspection lens.

The [product contract](D08_DOMAIN2_TIMELINE_BROWSER_CONTRACT_2026-10-30.md) and
[native contract](D08_DOMAIN2_TIMELINE_BROWSER_NATIVE_CONTRACT_2026-10-30.md)
separate implementation, source tests, actual rendering and resource admission.
The private native launcher adds one literal `--timeline-browser-v1` mode with a
new source-bound record. Its original no-argument paging mode retains its original
64MiB packet reservation and twenty captures; that cohort is not rerun here.

## Independent source lineage

All original raw files, derived formatting proofs, failed reports and fixtures
remain local. Authors perform source/Git/hash work; Root executes measured checks.

| Source | Actual result and attribution |
| --- | --- |
| 077c8da2 / Root e84a11b6 | Thirty independent App/Panel/controller cases frozen before product changes; actual20PASS/10FAIL, setup empty,0.154s |
| b7b1a3a7 | Same unchanged30 cases:30/30,0.147s after the three-file product change |
| 117b9694 | Formatting only, executable-equivalent production JSX; strict TypeScript passes0.279s |
| 86e471f9 / Root bbd6e4e1 | One additional public-helper mixed-slot case:30PASS/1FAIL,0.148s; original30 bodies unchanged |
| 386fe51c / measured b99194e8 | V2-first revision precedence;31/31,0.157s. Normal Controller publishes exclusive slots; no runtime mixed-slot collision is claimed |
| c9ea1623 / Root26a60be0 | Native-mode checker baseline:47 authored/0 executed/0 pass, missing future API UNRUN_SETUP,0.070s; not behavioral RED |
| b7b4185e | New actual private launcher/helper source with VM dependencies:47/47,0.125s |
| 15df8ff5 | Three environment-dependent Rust writer tests ignored by default; annotation-only inverse hash preserves every body; explicitly included in the six-test run below |
| 83687a38 / Root1392bf53 | Pre-execution geometry-oracle correction: separate normal-scroll reachability from final PNG framing; original unrun all-content-in-one-viewport source retained |
| 0f2a4fba / Root62ef3e2b | Four independent actual bootstrap-prefix groups:0PASS/4FAIL, setup empty,0.112s before the setup correction |
| 99d38a05 / Root11684ea0 | Same unchanged four groups:4/4,0.109s after explicit library initialization; no native rerun |

The31 frontend cases evaluate actual App and real routed panels with disclosed
inert React/hooks/JSX/static HTML and synthetic Gateway data. They are not mounted
React, browser pixels, native IPC, Rust canon or durable saves. The47 mode checks
execute actual launcher blocks with memory-only filesystem/child/budget doubles.
Three explicitly identified checks inspect source call/writer order. Malformed
browser flags are not separately qualified by Rust runtime tests.

The first formatter comparison used preserved lexical JSX and refused before
writing App.tsx. Its partial checker-only formatting and refusal record remain.
The later production JSX lowering proves executable equivalence before formatting
the product/checkers. Rustfmt changes are separately attributed and reviewed.

Three compatibility corrections retain their original failures:

- The old timeline checker aborted at a literal requiring "corrections remain
  unavailable". Independent3f58b2f9 replaces only that obsolete copy clause with
  the saved-draft warning and absence of the false global author claim. Existing
  no-Fork/no-Apply/preservation/downstream assertions remain; all83 checks pass.
- The original245-case launcher checker reports234PASS/11FAIL. Independent
  a9f73b83 restores the actual zero-argument mode/plan module ambient in its VM;
  every245 case body/limit is unchanged. On unchanged production it passes245/245.
- The original frontend guard reports170PASS/1FAIL because the normal bundle
  exclusion list grew67 to70. Independent4e135f48 requires the three new unique
  exclusions while retaining the original ordered67-marker hash and predicate;
  all171 cases pass. The verifier's77-child roster/arguments are unchanged.

## Focused checks actually run

Commands run from physical D with process TEMP/TMP D:/Dev/_Temp, installed pinned
Node24.22.1, Rust/Cargo1.93.1, rustfmt1.8.0, PowerShell7.6.5 and Windows10.0.26300
x64. Package inputs retain React19.3.1, TypeScript7.0.2, Prettier3.9.10,
esbuild0.28.2 and Tauri2.12.5. Cargo uses the existing exact-lock D cache/target,
offline, one build job, no incremental/debug data. No downloads/upgrades or SDK,
ADB/JVM/device/emulator/model/OS-boundary operations occur.

From apps/desktop, with an existing explicit D `LOCALLORE_CHECK_OUTPUT_DIR`:

| Command | Measured result |
| --- | --- |
| `node check-domain2-timeline-browser-review.mjs` |31/31 at b99194e8;0.157s |
| `node check-timeline-controller.mjs` |83 actual source/decoder/static HTML checks;0.200s |
| `node check-domain2-timeline-resume-review.mjs` |7/7;0.094s |
| `node check-v2-routing.mjs` |8;0.082s |
| `node check-domain2-timeline-browser-native-mode-review.mjs` |47/47 at d21bc019;0.099s |
| `node check-v2-inspector-paging-process-review.mjs` |245/245 after adapter correction;0.264s |
| `node check-v2-inspector-paging-path-review.mjs` |38/38;0.070s |
| `node check-frontend-evidence-policy-review.mjs` |171/171 after exclusion correction;0.244s |
| `node node_modules/typescript/bin/tsc --noEmit` |Pass at d21bc019;0.257s |
| `node node_modules/prettier/bin/prettier.cjs --check 'ui/*.{ts,tsx,html,css}' '*.{json,mjs}'` |Pass;2.650s |
| `node build.mjs` |Normal frontend pass;0.234s |

The actual verifier's unchanged normal read/assert block was also executed alone
against the real built bundle: all70 exclusions pass, app.js SHA256
`57045763cf10f39a62ec454037224c71491da9f791e895072e97f5a6eed52cb7`.
This is not another full77-child run. Installed esbuild is a native BUILD TOOL,
not native application or inference execution.

From the repository root, using `--locked --offline`:

| Rust command scope | Result |
| --- | --- |
| `cargo test -p locallore-desktop-spike --features dev-harness --bin locallore-desktop-spike harness::domain2_timeline_browser_artifact_review_tests -- --include-ignored --nocapture --test-threads=1` |6/6 at4a68ef3b, including the three separately admitted mode cases;17.418s compile+test command |
| Same exact bin/filter, `harness::selected_scene_artifact_budget_review_tests`, without browser flags/`--include-ignored` |7/7 old writer controls;0.492s |
| Same exact bin, `v2_inspection_paging_harness::review_tests::exact_mode_selection_is_pure_and_never_turns_requested_invalid_into_absent -- --exact --nocapture --test-threads=1` |1/1 old pure selector;0.449s |
| `cargo check -p locallore-android` |Pass, Windows-host Rust compilation only;0.397s |
| `cargo clippy -p locallore-desktop-spike --all-targets --features dev-harness -- -D warnings` |Pass, compile-only;8.943s |
| Same Clippy without `--features dev-harness` |Pass, compile-only;6.458s |
| `cargo fmt --all -- --check` |Pass;1.965s |

The six-case writer process explicitly sets D02=1/D05fixture=1/D08browser=1 after
clearing other LOCALLORE flags. Its tiny counter-prefilled fixtures retain5 bytes
in three unique D temporary roots. The legacy writer retains14 bytes in three
other roots. Nothing is deleted. No stopped qualifier executable/test or broad
ignored test suite executes. Compiling an Android adapter or qualifier is not
Android/device/OS-isolation qualification.

## Actual native attempt: failed before browser initialization

Clean d21bc019 executes `node v2-inspector-paging-harness.mjs
--timeline-browser-v1`,2026-10-30T15:45:32.4592131Z–15:46:20.2017050Z:
47.7404436s, exit1. All five direct children close; no timeout/truncation/unknown
drain/storage breach occurs. Both normal products restore and remain unlaunched.

The real hidden/unfocused WebView2 renders the empty shell. The fixed journey
fails `actual-Main-existing-workspace-ready` / `D08BrowserDeadline` before any
story Host call: failure snapshot traceCount0, buffered errors0, no selected story/session/revision,
no receipt and no baseline/final Rust oracle. Report3 assertions/3 distinct,
zero successful captures; one actual failure PNG is retained and individually
viewed by Root. Its snapshot honestly says Storage unavailable/no session.
Checkpoint/finish and CapturePreview use actual native harness IPC; no
successful story Host IPC/browser journey is inferred from that evidence.
The final report records one settled native `capture_revoke` cleanup call after
disposal. That final trace is distinct from the empty failure-snapshot trace;
neither contains a story Host call.

Original failure PNG SHA256:
`c8b0b9af9d9d5b2da7108d0eaaec657be6ead1f18abb2df786e6b82c2fa6a260`.
It is1280x900 and reports Chrome/Edg156.0.0.0; no independent loaded runtime build
is claimed. The image does not qualify the new browser layout or150% text.

Source diagnosis: Main's development branch dispatches its journey; only the
ordinary branch calls Controller.start. The existing paging journey explicitly
loads its library. The new journey instead waited for workspace plus selection
before its own resume, so it could not initialize. The prepared correction uses
the same public library read, validates the two fixed saved roots, then resumes
the exact child. It is a harness setup correction, not a production storage fix.
The independent four-group regression executes the actual journey prefix and
Controller/strict decoder with synthetic transport, symbolic oracle and disclosed
idle/owner-observer controls. It checks empty startup, public preselected OTHER,
seven invalid/unavailable library variants and an awaited pending library. All
four fail before the correction and pass unchanged afterward. It does not mount
Main, render, invoke native IPC or prove Rust canonical state.

Formatting8271e130 has executable-equivalent bootstrap/checker hashes. Its final
four-group report also passes with independently matched source hashes; shell
bookkeeping then refuses the misspelled `-Depth4` option, so that extra execution's
exact duration/exit is not retained. The log and wrapper failure remain; no rerun
is invented to fill missing metadata. The earlier0.109s four-group execution has
complete process metadata. Remaining final checks execute separately on clean8271:
strict TypeScript0.285s, complete frontend format2.828s, normal build0.243s, all
passing. The rebuilt normal bundle is byte-identical to the70-exclusion-tested
bundle above. Rust inputs are unchanged from their attributed checks.

Standalone reproduction from apps/desktop, with existing D toolchain/output and
TEMP/TMP set as above: `node check-domain2-timeline-bootstrap-review.mjs`.
It emits a bounded64KiB stdout report and retains no bundle/HTML. This command
does not admit the separate native application journey.

## Retention and next gate

The source phase passes at4,225,038B against8MiB, including19B in six external
unit roots. The actual native packet measures10,797,745B before final small
records. Every raw/derived source, failed check, image/profile/database and process
record remains charged. D07501,644,653B, D0579,500,962B and D0940,267,990B stay
retained; original D05's separate32MiB allocation remains FAILED.

The first native admission reserves20MiB packet/8MiB app writer,32MiB browser
base,16MiB products and1MiB metadata under the original640MiB joint ceiling.
The fresh preflight forecast664,435,955B fits. Original target baseline is
8,259,980,576B with2GiB growth; actual post-run growth79,470,760B remains below it.
Normal restored app.js retains the hash above; executable SHA256 is
`46c558b9ca6210e6aa5baa3bdd044370f765aa8ec2e906dc8fdf5a991b116544`.

The retained browser base is now about15MiB. Another mandatory20MiB reservation
would exceed its32MiB cap; a renewed joint forecast is also required. **No second
native run, lowered reservation, old-data omission, deletion or cap reset is
authorized by this report.** Bootstrap source verification is complete; prepare a
reviewable draft PR and obtain an explicit prospective resource decision.
No previous native failure becomes green when its harness source is corrected.

The owner subsequently approved a single further fixed run with a40MiB browser
base and648MiB joint ceiling, retaining the20MiB packet reservation, all earlier
costs and original target/D05/D07 limits. See the native contract's explicit
revision2 appendix and [decision record](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6527673039).
Version2 guard implementation, independent revised checks, source review and a
fresh source-bound record precede that one attempt. At that decision point the
corrected run had not executed; its subsequent failure is recorded below. The
original failed version1 packet remains failed.
All native browser, keyboard/screen-reader, Android parity, real-model quality,
offline/OS, installer/release and whole-epic gates remain open.

After the bootstrap source correction, a read-only inventory measures source
evidence4,357,092B including the19B external unit roots, retained native
packet10,838,148B and whole browser base15,195,221B. Every native byte remains
included in the base/joint count. With all previous named evidence and current
718,574B products, actual joint retention is637,327,419B before later small
metadata. Retaining16MiB product/1MiB metadata reserves and admitting another
20MiB packet would forecast675,406,157B, exceeding640MiB; the proposed648MiB
ceiling accommodates it. This calculation alone is not runtime admission.

## Approved revision2 execution: failed finalization, execution stopped

Independent revised47-case source fc513a78 freezes before producer597d1e8e.
Root1247ef73 measures37PASS/10FAIL before the six-line budget revision; the same
checks then pass47/47 at597d1e8e. Formatting d29a7081 preserves executable hashes.
Final actual checks at d29a7081:47/47 in0.143s, old process245/245 in0.245s,
launcher syntax0.040s and complete frontend format2.700s, all passing. These are
source checks, not actual native execution or authorization enforcement.

Clean d29a70819730792c5efb92714116d074bae9e129 then executes the single approved
`node v2-inspector-paging-harness.mjs --timeline-browser-v1` attempt:
2026-10-30T16:32:31.1038837Z–16:35:48.7577702Z,197.6389288s, exit1.
The actual hidden/unfocused WebView2 produces all six planned PNGs plus one
failure PNG. Root individually views all seven originals. Wide images are
1280x900; enlarged narrow is620x900. The selected timeline controls, ancestry and
head/status are readable; enlarged narrow text wraps without visible horizontal
clipping. The normal scroll framing centers the selected row control, so other
controls may be offscreen. The failure PNG frames a lower selected-case panel;
it does not visually display the harness assertion failure.

Retained semantic checkpoints record child44/player, root0/player, child44/player,
then child44/Mira for observer and both enlarged views. All record no pending
operation, visible error or buffered error, and explicitly no displayed receipt.
Sixteen reachability observations per planned checkpoint remain in the original
JSON, total96. The failure checkpoint records28 settled native/Host calls; its
last successful checks include exact-six captures and finite ordered call metadata.
No final `report.json` exists. Final Rust oracle comparisons, disposal completion,
the complete call roster and overall assertion count are therefore unavailable.
Do not infer their success from the images or source tests.

The application child sequence3, PID64220, reaches its180s deadline. One stop
returns true; its close record reports SIGTERM, but `OwnedDrainUnknown` remains
true and `processTreeContained` false. Normal product restoration is skipped;
the diagnostic frontend/native products remain in place and have not been
launched again. The recorded `storageBreached:false` is not a completed final
inventory. The launcher retains its last-known inventory and the failed packet.

Read-only observation at16:42:52Z finds no recorded PID, direct child of64220 or
WebView2 with the exact owned profile. This does not prove retrospective tree
closure and does not reset the failed guard. All subsequent work is source-only
review, documentation and bounded evidence accounting; no build, test, app,
manual process stop or native repeat occurs.

Independent source review identifies a read-only roster defect: the new journey
excludes native `capture_revoke` before disposal, although normal session/context
changes invoke that existing privacy cleanup and the accepted D05 journey allows
it. The checkpoint boundary supports that diagnosis, but no full trace was saved
to identify the individual offending call. A second source finding is the compact
frontend versus formatted Rust256KiB report limit. Known retained checks,96 scroll
records and four font groups alone reconstruct to about149,143 compact or261,008
PowerShell-formatted bytes, excluding proofs and calls. This is an encoding-risk
estimate, not the missing actual report. Disposal stall versus subsequent report
rejection cannot be distinguished from the saved artifacts.

The claimed source-only correction and independent FIRST cover the existing
cleanup allowance, references to unchanged per-checkpoint geometry instead of
duplicating it, both report encodings and a fixed failed-finalization fallback.
Until executed under a separate safe reconciliation decision these sources are
**UNRUN**, and neither native attempt becomes green. Native generic writer,
shared Host, canonical storage, inference and observer authority stay unchanged.

Read-only accounting measures the failed revision2 packet12,074,264B/216 files
and whole browser base27,406,181B before its6,753B handoff record. The original
failure packet, profiles, databases and all source/results remain charged. A
further20MiB reservation does not fit the40MiB browser cap; its one-run authority
is also consumed. No further attempt or cap change is authorized here. PR286
remains draft; native browser acceptance, full D08 and epic gates remain open.

## Source-only finalization freeze, before reconciliation

Independent FIRST f8429358ecfccb46a895863d9f07d254d10a32c9, Root42febdc6,
freezes32 cases in `check-domain2-timeline-finalization-review.mjs` before the
different-author producer900c8815, Root714a17d2. The checker is21,577B with SHA256
`66eab7c88bb69f0af87d277cdef09bcedb768f1b75bd14bf4e23b6d0085e4b37`.
At this freeze no checker or producer command had run. An absent helper is explicitly a
per-case UNRUN_SETUP prerequisite, not behavioral RED; actual old roster/finish
closures can be evaluated independently when execution is admitted.

The development-only helper is4,486B, SHA256
`317ca27b72abbe55e3783f9dbff40bff8d7715f258f9c87f441109c4235255df`.
The integrated journey is45,063B, SHA256
`655e8ce3ca057da06a03bb025c1fe8086ea6c56e91611072ac820e592ad40504`.
Source/Git review proves changes only to its helper import, final-report closure
and read-only roster closure. Original checkpoint capture-body LF SHA256 remains
`704910042dd9ddfb2ca3c285dbb5998425407a9c64af237b35bf73afb9e7d4b8`.
No original checkpoint fields, capture procedure, journey actions, Rust checks,
observer/privacy fence or native generic writer changed. This source proof does
not replace compilation, regression execution or native acceptance.

The fixed helper allows established normal `capture_revoke`, rejects mixed or
unknown call channels, references the six original per-checkpoint observation
files, requires96 observations for success, checks compact and formatted UTF8
limits, and makes at most one detailed finish plus one fixed failed fallback.
The journey retains a single finalization promise before invoking native code,
so its outer catch cannot dispatch a third finish. All32 cases use actual helper
or extracted actual closures with disclosed synthetic metadata/invoke outcomes;
they are not browser, IPC, Rust serialization or process-lifetime evidence.

Reproduction after a separate execution admission, from `apps/desktop` with
existing D toolchain and TEMP/TMP above:
`node check-domain2-timeline-finalization-review.mjs`. It retains no HTML/bundle
and bounds its stdout report at64KiB. At the source-only freeze it was **STOPPED**,
along with TypeScript, formatting, builds and application launches. Proposed
normal restoration must preserve the failed diagnostic products before overwrite;
it is distinct from and does not admit a further native application attempt.

## Approved reconciliation: code checks pass, storage boundary fails

The owner answered **"Approve checks and restoration"** to the separate bounded
proposal. Fresh17:09:08Z reads find no exact owned executable, recorded-PID direct
child or exact-profile WebView. The original failed run/latch remain unchanged.
Before overwrite, ordinary copies preserve the failed frontend2,169,685B and
native44,007,424B; hashes match the original products before and after all children.
The frontend copy is charged to source/browser evidence; the native copy is
charged in full to the original target-growth allowance. No hardlink is used.

Root temporarily checks out frozen FIRST42febdc6, then restores the claimed
branch. Its actual32 authored cases yield10 executed:5PASS/5FAIL, with22 separately
UNRUN_SETUP because the helper is absent;0.1135637s, exit2. Failures exercise the
actual pre-disposal cleanup roster, duplicated observations, formatted overflow,
missing failure fallback and missing single-flight behavior. This is not a
32-case behavioral RED. Corrected raw sources at12a6904b run the same32 cases:
32/32,0.1201019s; bootstrap4/4,0.0944094s; strict TypeScript0.2787898s.

Formatting compares actual esbuild executable hashes before/after all three
owned files; each pair is identical. Same formatted32/32 then pass0.1239666s,
bootstrap4/4 in0.0966115s, strict TypeScript0.274826s and complete frontend format
in2.720351s. The initial Git stage used a wrong prefix from apps/desktop and
refused; corrected Root45937afbd4db8c692bdb16e5f193b6ba4e399921 commits the exact
already-verified bytes. No clean-head rerun is invented. Independent source/hash
review matches every raw/derived hash, the32 named cases and original capture body.

| Formatted source at45937afb | SHA256 |
| --- | --- |
| Independent checker |2703223455d7cdc44733150a028e0670168fa73021cec5b16dc704f8526e9cce |
| Development finalization helper |d03917535f521c32581a6c6e1c12bfa07fedd19ebe7acf5f0f318b6fc00bdbf7 |
| Fixed native journey |9c1c297005a4c3fe2cfc441f554c2aa3af14bfb22804a43250b6ea83a94da4c2 |

Normal `node build.mjs` passes0.2437901s and produces byte-identical app.js
`57045763cf10f39a62ec454037224c71491da9f791e895072e97f5a6eed52cb7`;
the actual unchanged verifier block passes70 exclusions. Then normal
`cargo build --manifest-path src-tauri/Cargo.toml --bin locallore-desktop-spike
--locked --offline` exits0, closed,44.9805331s. All16 direct children have terminal
records; none times out, overflows output or produces a new unknown closure.
No browser, app, Rust test binary, model, SDK/device or stopped OS qualifier runs.

**The overall reconciliation fails `OriginalTargetGrowthCap`.** Its local runner
omits the earlier process-local one-job/no-incremental/no-debug settings. Cargo
reports a broad rebuild with `unoptimized + debuginfo`; retained compiler metadata
still identifies Rust1.93.1. This supports build-settings drift as the cause,
without attributing every added byte. The repository native launcher already
pins these settings at module initialization; the omission belongs to the new
private orchestration, not a demonstrated public-launcher defect. A proposed
public hardening claim is withdrawn before any checker/producer edit.

Separate read-only measurement finds target12,034,874,788B versus original
8,259,980,576B: growth3,774,894,212B, exceeding2GiB by1,627,410,564B.
The83B stop record contains the failure category; the separate read-only observation
preserves the exact measured totals. There is no restoration-success record.
Normal products were produced and stay unlaunched, but no successful overall
restoration/admission is claimed. Normal executable SHA256 is
`902e5c37abdea753bd90fbb1a0d26eafc5527f2e03e9a332b7c8e340cd12ce49`.
Read-only hashes confirm the checked sources and both failed-product copies remain
unchanged. All generated output is retained; no deletion, budget reset or retry.

Before its final small read-only record, browser29,678,495B, source6,766,102B and
combined check records95,876B remain below40MiB,8MiB and512KiB respectively.
The target-growth boundary alone is failed. Further execution is **STOPPED**
pending a separate resource decision; the original native lifetime failure and
both failed application attempts remain failed. Source checks do not establish
native acceptance. PR286 stays draft; all wider gates remain open.

## Owner-approved revision3: source checks before the single native attempt

The owner explicitly approves retaining all output and exactly one further
six-capture attempt, after revised checks/review/fresh admission: browser-only
4GiB target growth,52MiB browser and660MiB joint evidence, unchanged20MiB packet
reservation. The original target baseline8,259,980,576B and every earlier failure
remain. No automatic repeat, deletion, model/device/SDK/OS qualifier or desktop
control is admitted. The separate source-only fork integration in PR290 is not
part of this fixed browser recipe.

Independent V3 FIRST c4a781ac, integrated549b7042, freezes the same47 groups before
the producer. Raw checker SHA256
`7338cf44306400ef26f6f6cac8382076c78e69e94b3addd7b562ef7c7f6bee82`.
Against the unchanged V2 launcher, actual47 execute:37PASS/10FAIL, zero setup
failures, exit1,0.1352741s. The seven producer substitutions update only browser
budget kind/prefix/version and approved limits. Raw corrected47/47 pass0.1252565s;
unchanged245 launcher checks pass0.3000924s; Node syntax passes0.0618156s.
These are source/VM dependency-double checks, not OS admission or native IPC.

Prettier3.9.10 `--debug-check` exits2, known closed,0.4342214s: its AST serializer
cannot encode the checker's BigInt. No file was written and the native attempt
remains unused. Preserve the complete failure and original coordinator; an
immutable reconciliation binds continuation to the exact process/stop/source
hashes. This is a known tool incompatibility, not an unknown-lifetime or storage
failure. Four directly spawned installed esbuild0.28.2 CLI transformations then
compare the two exact files before/after the fixed Prettier write. Both canonical
output hashes match, with no persistent service. All children close without
timeout, output overflow or kill; bounded records and inventories remain local.

Fresh inventory corrects a prior D07 charge by276,119B for four later retained
source files omitted after its preapp record. Current D07 cost501,920,772B includes
all eight distinct source paths; historic records and outcomes stay unchanged.
The independent four-file D05 cohort remains separately charged. Updated external
evidence/reserves560,014,573B and D05total79,500,962B carry forward to V3 admission.
An ordinary45,176,832B copy preserves the prior normal binary (SHA902e5c37...) in
the existing target before any diagnostic build. All prior failed copies remain.
Source-check admission reserves512KiB new combined records and the later20MiB
packet, forecasting browser51,176,988B, joint690,692,523B and target12,348,487,076B
(including the ordinary copy and256MiB cached-build forecast). Final native
admission must remeasure these figures against the clean reviewed source.

At this source checkpoint the one V3 native attempt is still unused. Actual
native execution, image inspection and normal restoration must be reported
separately; no whole-D08, Android-device, story-quality or release gate is met.
