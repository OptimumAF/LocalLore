# Initial player-name setup — 2026-10-26

M09.02, with M09.03/M09.06 interaction coverage. This packet is stacked on
[draft PR #221](https://github.com/OptimumAF/LocalLore/pull/221), exact prerequisite
`6b4ccab9df0afbeb1178611a016bc2dbf0f7e16b`; it does not merge that work. Prior
native10/chooser7/creation19/broad89 results keep their original834-input source
attribution and do not qualify this changed source or its APKs.

## Behavior and authority

The creation review now offers a player-name field. Editing it invalidates old
Create consent; explicit Review changes obtains a new native preview before
creation. Rust constructs the selected original starter, changes the player
Actor's display name and the exact template-declared subject references in the
contract, validates the engine and binds the reviewed setup with exact
template/derived-seed hashes. Entity IDs, mechanical rules, NPC identity and
knowledge eligibility remain unchanged. The truth/belief distinction and all
epistemic fields are preserved. The reference refinement below records why the
initial name-only implementation is insufficient.

Names are at most64 Unicode scalars/256 UTF-8 bytes with no normalization or
silent trimming. Source inspection found the existing context compiler's256-byte
actor-name ceiling; the new bound keeps valid setups inside that existing
runtime contract. Save titles keep their separate80/320 limits. Cancellation
before Create preserves the selected library and play draft; uncertain creation
retains the existing refresh rules. Exact retained retries compare the full
seed and title and cannot rename an existing story or reset accepted history.

See the [closed setup contract](STORY_PLAYER_SETUP_V1.md) and
[fixed eight-method Android protocol](ANDROID_PLAYER_SETUP_PROTOCOL.md). Legacy
catalog/preview/named-creation formats and existing Android rosters are unchanged.
The debug probe maps configured creation to named creation and ignores the new
read-only setup operation without changing its fourteen counters.

## Verification at this checkpoint

The native author actually runs8 new focused unit adversaries and3 legacy
creation tests, all passing, in the separate native worktree. Their835-input
maps remain unchanged; the retained original streams include ordinary Cargo
compiler stderr. These are focused native results, not integrated Android proof.

Root's bounded generation completes24409ms/worker0 with cleanup/capture true.
All four generation commands return0. The1948-file before/after maps differ
only in the two expected generated frontend schema/type files. The separate
frontend/schema/type/controller/format check passes27601ms/worker0,
cleanup/capture true, with1948 tracked sources unchanged. Later changes add
only Python tests and Rust workspace/Android test or production inputs; their
actual integrated checks are still required.

Independent review finds no mismatch in the frozen native/Android contracts or
callback/ownership paths. Ten original workspace tests independently derive the
expected seed and hash from fixture bytes. They cover durable retry/fork/archive
round trips, duplicate-name ambiguity and canonical context compilation at the
64-emoji/256-byte boundary. Eight new JVM methods and eight fixed Android methods
cover wire bounds, exact retained consent, review cancellation and actual native
state after ordinary Activity reopen. At this checkpoint those integrated tests
are authored, not yet executed; compilation and source review are insufficient.

The integrated Python discovery subsequently passes all1485 tests,0 failures,
errors or skips, owner269478ms/worker0 with cleanup/capture true and1954 tracked
inputs unchanged. This includes the new parent-path timingless-pair, rebound-raw
and unknown-ownership refusal tests. Rustfmt also returns0.

The first combined three-package Rust owner expires at600015ms before the full
suite finishes. Cleanup/capture are known true, tracked inputs remain unchanged,
and the original record stays `passed:false`. Partial successful frames are not
promoted to a complete Rust result; its raw streams and missing final Cargo
command receipt are preserved without reconstruction.

The next verification runs each complete package suite under a separate existing
600-second owner, serially. All-feature tests and examples remain included;
the workspace command explicitly enables `locallore-storage/development-fixtures`
to preserve the original package union's host feature. No test filter, timeout
increase or emulator budget change is used. Those package results are pending
until actually executed and read back.

The first package-wrapper preparation refuses the Cargo launcher symbolic link
through the existing safe-path guard, before creating a request/owner or running
Cargo. Its partial source-map folder and original helper remain unchanged. A
separate explicitly derived tool-observation note records that preparation gap;
it is not reconstructed process output or a test result. The next wrapper pins
the actual installed Cargo/Rustc/Rustdoc executables and checks their1.93.1
versions before running a package suite.

That workspace run actually reaches the ten new persistence tests:9 pass and1
fails. The instruction-shaped-name test incorrectly expects an unlearned ability
submission to return a queued phase before failing preparation. Submit instead
returns `Ability` while retaining a terminal failed-turn ledger entry. Its
owner records35859ms/worker1, cleanup/capture true and unchanged1954-file maps;
the original failed Cargo/result/streams remain failed. A first test correction
incorrectly expects no stored turn and also fails9/10, owner36434ms/worker1 with
known cleanup/capture. A separate one-test diagnostic (nine filtered out, not a
full-suite result) then exposes the actual `Failed` record and no receipt;
owner4580ms/worker1, known cleanup/capture. Those original failed records remain
unchanged.

Source inspection confirms the distinction: Store preflight checks request
shape and bounds before staging; Host then runs mechanical preview, records
terminal failure and rejects the ability without inference or canonical commit.
The corrected test asserts exact `Ability` rejection, a matching terminal failed
ledger entry with no receipt, no drafts, unchanged host resource counts/catalog,
and unchanged canonical engine/accepted receipts. It does not mistake normal
failure bookkeeping for accepted history or weaken production validation.
Full package qualification requires a fresh complete run after this correction.

## Complete host-package follow-up

At behavior checkpoint `4d268b92`, all three complete package runs pass on the
same1954 tracked inputs, unchanged within every owner:

| Package | Passed / failed / ignored | Harness summaries | Owner elapsed / worker |
|---|---|---|---|
| `locallore` |426 /0 /4 |56 |99610ms /0 |
| `locallore-storage` |239 /0 /6 |30 |271859ms /0 |
| `locallore-workspace` |149 /0 /1 |27 |43322ms /0 |

The total is814 passes,0 failures and11 ignored cases across113 summaries.
All ten new workspace tests pass, including canonical alias compilation at the
64-emoji/256-byte boundary, duplicate-name ambiguity and durable fork/archive
round trips. Core's eight new unit adversaries are included in its complete
426-test result. These are overlapping coverage with the focused author runs,
not additive unique-test totals. Every owner reports complete cleanup/capture
and stderr0; ordinary Cargo compiler/test stderr is retained in the separate
command captures. The original combined expiry and failed package/diagnostic
runs keep their failed or incomplete status.

Clippy over all three packages/all targets/all features, with warnings denied,
also passes22485ms/worker0, cleanup/capture true and1954 tracked inputs unchanged.
The healthy-store failure assertion distinguishes terminal bookkeeping from
accepted effects; it does not promise a failed ledger write can never be lost
under storage faults. `live_counts()` proves session/worker conservation, while
the Store query separately proves no draft. Current archives exclude
noncommitted workflow keys/status; those records do not become canonical events.

Android build/JVM/lint/artifact and actual emulator qualification remain pending
at this follow-up. No older834-input runtime result is reused for this source.

## Pre-reference-fix checkpoint and consistency discovery

The first offline Android build subsequently passes253649ms/worker0 with known
cleanup/capture:274 executed JVM tests/32 XML suites,0 failures/errors/skips,
both lints0 errors/3 warnings and11 artifact audits. Deep replay verifies841
mapped inputs,108641-byte before/after maps, SHA256
`6e16de5f19f72ead0562e91e12f83c965a1e5d291771fd2be9d956b98521323d`.
These checks actually pass on the initial source; no emulator has run it.

Before runtime admission, direct fixture inspection discovers a consistency
gap those tests miss: Lantern's ancestry fact and Oren's seed belief still name
Rowan after a custom name is chosen. The factory contract is refined to derive
the two exact identity-neutral subject strings, preserving truth/belief types,
eligibility and provenance. Default/legacy fixture bytes and Bracken's derivation
are unchanged. There is no arbitrary name interpolation, global replacement,
accepted-history edit or wire/schema/dependency change. An independent original
RED case is required before integrating the correction and rerunning affected
checks/build/runtime on a fresh source cohort.

The initial host/build records are already sealed as a pre-reference-fix
checkpoint with explicit `feature_acceptance:false`. All266 entries/44904248
bytes match originals, copies and ZIP members, independently and in Root replay.
The84191-byte index has SHA256
`6a0312fc6cf04d4e9b4947097177fbd5df3e5294ebc7868f8f75465146b148bd`;
the21314185-byte ZIP has SHA256
`8802b2679fac945bb12f74eb1ddace8653f1848e120c353064b400ec55cc3910`.
It retains the original expiry, preparation refusal and test-oracle failures.
Those passed checks remain passed for their exact source; they cannot qualify
the corrected feature or replace its missing semantic test/runtime evidence.

## Corrected-reference host qualification

The independent semantic case actually fails against the name-only constructor:
0 passes/1 failure/10 filtered cases, owner4524ms/worker1, cleanup/capture true.
Its original preview contains `Player: Eira` beside the ancestry proposition
still naming Rowan. This focused RED is not a complete package result and is
retained unchanged.

The corrected constructor is integrated at `02c91f92`. It validates both exact
template reference declarations before either replacement, preserves their
typed epistemic fields and never interpolates the input name into prose. Native
author checks pass9 player-setup tests plus1 declaration-guard test covering11
contradictions on their own unchanged841-input map. Independent production
review and the fresh complete workspace run confirm the new semantic case is
green, without promoting an NPC belief to player knowledge or world truth.

Fresh complete package results on unchanged1954-file maps are:

| Package | Passed / failed / ignored | Harness summaries | Owner elapsed / worker |
|---|---|---|---|
| `locallore` |428 /0 /4 |56 |88548ms /0 |
| `locallore-storage` |239 /0 /6 |30 |300094ms /0 |
| `locallore-workspace` |150 /0 /1 |27 |72924ms /0 |

The total is817 passes,0 failures and11 ignored cases across113 summaries.
All11 new workspace cases pass. These complete all-feature package suites retain
the same600-second owner ceilings, feature union and unfiltered scope. They do
not reuse the earlier814-pass checkpoint as corrected-source qualification.

The fresh Python suite passes1485 tests with0 failures/errors/skips,
owner149807ms/worker0. Frontend/schema/types/controller/format checks pass23434ms,
and Clippy across all three packages/targets/features with warnings denied
passes15266ms. All report worker0, known cleanup/capture and unchanged1954-file
maps within their own execution. The schema/type artifacts stay unchanged: this
fix changes the configured seed's declared subject wording, not wire shapes.

A new Android build and fresh native/component/player-setup guest cohorts are
still required. Old APKs, initial checkpoint and original failures retain their
exact earlier scope and cannot satisfy those gates.

No dependency is introduced or repinned. Existing locked offline toolchains are
reused. All requested verification will retain original bounded output and exact
source/APK/owner bindings in create-only private C: evidence; no model weights,
private saves, raw diagnostics or guest images are uploaded. Public checkpoints
are committed and pushed incrementally.

Original premise generation, tone/content boundaries and broader character
editing remain required M09.02 work. Full journeys, accessibility, joined drain,
current-source external OS-death, real-model, physical-phone and ARM64 execution
remain separate gates. Full milestone checkboxes stay unchanged. No merge,
release, persistent setting change or unrelated emulator stop is performed.

## Corrected Android build and preservation checkpoint

The corrected offline Android build now actually passes: owner148240ms/worker0,
known cleanup/capture and stderr0;274 executed JVM tests across32 XML suites,
0 failures/errors/skips; both lints0 errors/3 existing warnings;11 artifact
audits. Deep readback verifies all841 inputs and identical108641-byte source
maps, SHA256
`b0b1dc2d2ffcbdc44bf7463101ae5c4077fb432258eb980fb5bd434af5dbe802`.
The product APK is32770328 bytes, SHA256
`9e31dfa15c3309a756d1553df61e4600f847afd085f095fcf2fcb9acca9fbb24`;
the test APK is3110123 bytes, SHA256
`4e74892a23aa9fe3dc9c1b9519ff60995762c015bf364daa23b4a43d2b0e30f1`.
These corrected APKs supersede the earlier build for new runtime qualification.
ARM64 compilation/auditing does not establish ARM64 execution.

In response to the owner's preservation request, the corrected host/build
records are sealed in a separate create-only C: recovery set. Independent fresh
replay checks195 original files,196 copies and196 ZIP members,41691046 bytes,
with0 missing files or mismatches. Its62515-byte index has SHA256
`d20a0ce5581c69b7f33d3b20629a7ceab483906ae5092596ec9fc90e393252fb`;
the20085998-byte ZIP has SHA256
`bd26820bd0718c727ec4666c0686b005d2553578669574dd99698e6b7a5c8f05`.
The seal retains the failed semantic RED and references the earlier266-entry
checkpoint without rewriting it. Public source, original tests, contracts and
reports are committed/pushed; private evidence, weights, saves and guest images
are excluded from public Git. A fresh read-only runtime admission verifies the
corrected host/build/source bindings and the existing server without changing
its lifecycle. No new emulator instrumentation or model result is claimed at
this checkpoint; the fixed native10 and player-setup8 phases remain pending.

## Corrected emulator execution and terminal preservation — 2026-10-27

The corrected841-input source now passes both fixed phases in separate fresh
owned API35 Google APIs/x86_64 guests,2GiB RAM/two CPUs each. Root prepares and
plans both before launching either; continuous same-tool readiness-to-dispatch
uses the actual live owner handle. Each phase retains the existing850-second SDK
session/900-second verification owner/180-second class caps, measured-v2 client
requirements and one-shot guest admission. No source, dependency, roster or
deadline is changed to obtain these results.

| Fixed phase | Classes / methods | Complete SDK2 pairs | Owner elapsed / worker | Maximum SDK / observer elapsed |
|---|---|---|---|---|
| `components` |3 /10 |90 (29 SDK,61 observers) |254261ms /0 |10501ms /3049ms |
| `player-setup` |3 /8 |93 (30 SDK,63 observers) |268917ms /0 |17463ms /2467ms |

Both actual phase handles terminate0. Their original owner records report known
cleanup/capture,18 stdout bytes and0 stderr bytes. Exact source method rosters,
runner frames and matching SDK raw copies pass worker, parent and independent
file-only readback. All183 client/observer pairs are current measured-v2,
complete and clean; each SDK call has matching pinned-listener observations
before and after. These timings are diagnostics, not phone performance or a
general timeout-cause claim. The841-input map and three corrected APK bindings
match before/after/current source and the deeply validated build-v2 records.

The eight new methods exercise strict native setup wire fields/hashes/name,
explicit review before Create, retained actions, invalid/busy states, native
failure without fallback, Cancel preserving the selected library/play draft,
and configured creation plus ordinary Activity reopen retaining the stored
player name. These real Compose/MainActivity/JNI checks use scripted inference.
They do not kill the OS process, qualify a real model or prove joined drain.
The legacy creation19, chooser7, broad89 and external-controller rosters remain
unchanged and require their own current-source cohorts.

Root stops only each exact owned guest after its verification clients have
known terminal capture/cleanup. Both stop helpers and original guest handles
actually return0. Their guest owners record `stop_requested`,worker1,
cleanup/capture/closure true, no guest-flush claim, elapsed287467/342171ms and
exact proposal-bound stops. Original guest stderr1085/1084 bytes is retained;
it is separate from the verification owners'0-byte stderr. The second guest is
launched only after the first closes.

The reviewed final helper executes once after both closures and passes: one
matching observation of the existing server,0 device calls and no server
lifecycle operation. The new raw-bound preflight inventory contained0 protected
emulator identities; no inherited comparison to older processes is claimed.
The server is deliberately left available. The2827-byte final-postflight file
has SHA256
`f4b6d9cf6e903c86816047659908f7534e3b452f212a51739bfddb1f6fa127c5`.

Independent terminal audit seals450 existing originals plus1 derived assessment,
451 entries/1397812 bytes, into a new create-only C: recovery set. Independent
second replay and Root replay verify every original/copy/ZIP member, with0
missing files or mismatches. Its154147-byte index has SHA256
`91963035900e1d2cfcf436facef7b67230ce2c07c00a2c7d22f6a043efcf35ad`;
the493727-byte ZIP has SHA256
`efdd3cb67ab5564c2999ed546364f517c512e7448bd0d668fa3912e565e38155`.
The corrected host/build seal stays unchanged and is referenced by index rather
than duplicating its APK payloads. Recovery includes exact raw SDK2/runner,
request/source/build bindings, owners, preparation/STOP/INI/closure records,
helpers and explicitly derived coordination/audit records. It excludes images,
models, saves, DBs, live service logs and unknown subtrees. Feature acceptance
remains false in these private seals because full task/owner acceptance is open;
this does not relabel the successful fixed tests as failed executions.

Only the native phase's existing device-list capture is assessed for phone
availability: one authorized explicit SDK-emulator profile, no physical
candidate established in that capture. This is neither a fresh hardware
admission nor a claim that a connected phone is absent. M01.01/M01.02 physical
identity/performance remain blocked on a freshly established eligible device.

### Executed checks and reproducibility

Commands below abbreviate the pinned executable paths; private requests and
original command captures retain the exact arguments, environment and bindings.
Rust package owners use actual1.93.1 Cargo/Rustc/Rustdoc executables, offline
mode/two build jobs and unchanged600-second ceilings. Python is3.14.7; Android
uses JDK21,Gradle8.11.1,AGP8.10.1,NDK29.0.14206865 and SDK/build-tools35.

| Command or fixed procedure actually executed | Outcome |
|---|---|
| `cargo test --locked --offline -p locallore --all-features` |428 pass/4 ignored |
| `cargo test --locked --offline -p locallore-storage --all-features` |239 pass/6 ignored |
| `cargo test --locked --offline -p locallore-workspace --all-features --features locallore-storage/development-fixtures` |150 pass/1 ignored |
| `cargo +1.93.1 clippy --locked --offline -p locallore -p locallore-storage -p locallore-workspace --all-targets --all-features -- -D warnings` |Pass |
| Full Python `unittest` discovery of `scripts/tests/test_*.py` |1485 pass/0 failures/errors/skips |
| `node verify-frontend.mjs` and pinned Prettier checks in `apps/desktop` |Pass |
| Fixed offline Android build worker: controller clean, app JVM test clean/test, both lints, product/test/controller assembly,11 artifact audits |274 JVM pass/32 suites;0 lint errors/3 existing warnings;11 audits pass |
| `python -I -B benchmarks/android_process_verification.py components` with exact current build/proposal/running/server inputs |10 methods pass |
| `python -I -B benchmarks/android_process_verification.py player-setup` with its distinct guest and same corrected build |8 methods pass |
| Exact proposal-bound owned stops, reviewed final postflight, independent terminal audit and original/copy/ZIP replays |Pass |

No test results from the earlier834-input starter packet or pre-reference841
checkpoint are promoted to this source. Later public commits update only this
report/README; executable source remains02c91f92 and the corrected841-input map
above. GitHub Issues retain task status and handoffs; the retired Markdown
trackers remain pointers. This M09.02 slice/supporting M09.03/M09.06 is locally
verified/in review, with full checkboxes unchanged. Owner acceptance/merge,
broader authoring, accessibility, physical/model/ARM64, current-source OS-death
and joined-drain gates remain open. Next runnable verification: current841
legacy creation19 and broad89 in fresh owned guests; then the corresponding
current-source lifecycle controls. No merge, release, persistent setting change,
unrelated-emulator stop or private upload is performed.

## Existing creation and broad regressions — 2026-10-27

The next packet qualifies the pending existing creation and broad suites on the
same corrected executable02c91f92/841-input map. Root claims #13/6436375720 and
supporting #14/6436375986 before work. Fresh deep readback validates the retained
build-v2 and native10 prerequisites, including their actual APK/source/owner/raw
bindings and all90 measured SDK2 pairs. Host/build tests are not rerun, and no
earlier834-input outcomes are substituted. Independent file-only replay also
finds all host196/runtime451/source239 recovery bindings intact.

Two new standard2GiB/two-CPU API35 Google APIs/x86_64 guests are prepared and
planned before either launch. They run serially under unchanged fixed rosters,
source guards and time/output limits. Continuous same-tool readiness-to-dispatch
uses the actual live owner handles. Both fixed CLI phases actually pass:

| Fixed phase | Classes / methods | Complete measured SDK2 pairs | Owner elapsed / worker | Maximum SDK / observer elapsed |
|---|---|---|---|---|
| `story-creation` |4 /19 |100 (32 SDK,68 observers) |286815ms /0 |16291ms /2002ms |
| `regression` |18 /89 |183 (60 SDK,123 observers) |560203ms /0 |44379ms /2095ms |

Both actual verification handles terminate0. Their original owners have known
cleanup/capture,18 stdout bytes and0 stderr bytes. Worker, parent and independent
readback validate all283 complete metadata/raw pairs, exact source method
rosters, original runner frames, SDK raw copies, requests/start records, source
maps and current build/APKs. The timings are diagnostics, not physical-device
performance or a general timeout-cause claim.

### Coverage attribution

The existing MainActivity creation journey retains its historical named-creation
test name, but the current production UI now obtains `story_setup` and dispatches
default-name `create_configured`. Its success qualifies those default configured
UI workflows, including two-story/gift/reopen behavior. It is not evidence of a
direct legacy `create_named` native invocation. Legacy wire fixtures and exact
default cross-API retry remain separately covered in retained host/JVM tests.

Creation19 does not edit the player name or select narrative rules. Broad89
exercises its selected navigation/editor/lifecycle, cancellation, native resource,
fork and fallback suites. Its probe test checks the existing fourteen keys and
`story_templates` behavior; the new `story_setup` read-only and configured-create
counter assertions belong to the separately executed player-setup8 phase.
Neither new result replaces that custom-name phase, current-source chooser7,
archive2, external OS-death, real-model, physical/ARM64, accessibility or joined
drain qualification. No acceptance criterion is removed or weakened.

### Closure and recovery

Root requests each exact proposal-bound STOP only after known terminal client
cleanup/capture. Both stop helpers and original owned guest handles actually
terminate0. Guest owners record `stop_requested`,worker1,cleanup/capture/closure
true and no guest-flush claim, elapsed318240/587440ms. Original stdout/stderr
9418/1086 bytes and9410/1083 bytes are retained separately from the verification
owners'0-byte stderr. The second guest launches only after the first closes.

The reviewed final helper executes once after both actual closures. It passes
one matching observation of the existing server,0 device calls and no server
lifecycle operation. The newly captured, raw-bound preflight has0 protected
identities; no earlier process pins or old-two comparison are adopted. The
server remains available. Final-postflight2829-byte SHA256:
`02b3545c4a3680d7b8a235623e1ea986298bd90dcdf594a6d785b87de9b5d98e`.

Independent audit creates a new private recovery set with668 existing originals
plus1 derived assessment:669 entries/1773825 bytes. Independent second replay
and Root replay verify every original/copy/ZIP member, with0 missing files or
mismatches. Index229136-byte SHA256:
`48a98e3930505e4e3805fba2838c968e20e7366162748495a8354f28041400d9`.
ZIP600242-byte SHA256:
`793764468d12bdc2a63de408e31d4407bf3e188f4c13a7e679080417e83d68f3`.
All three referenced prior index/ZIP-or-bundle pairs remain unchanged. The new
seal copies only those indices, avoiding duplicate APK, model, image, DB, save
or prior archive payloads. Public source/tests/contracts/report are committed;
raw machine evidence remains in the private C: recovery folders.

The latest complete existing creation and broad device-list captures each show
one authorized explicit SDK-emulator profile and no potential physical candidate.
Creation's earlier empty boot-time snapshot is not used for availability wording.
These file-only assessments make no new hardware call and establish neither
fresh physical admission nor absolute phone absence. M01.01/M01.02 retain their
fresh eligible-physical-identity/performance gates.

Actual commands are the fixed `python -I -B
benchmarks/android_process_verification.py story-creation` and `regression`
phases, each with its exact current build/proposal/running/server bindings;
private requests and captures retain full arguments. Versions, corrected APKs
and841-input SHA remain those recorded above. Source/dependencies/rosters,
SDK850/owner900/class180/guest1200-second limits and full checkboxes are unchanged.
M09.06/M10.02 supporting qualification and the M09.02 slice remain in review.
Broader authoring is still required; this verification packet does not complete
the product. Current-source lifecycle/chooser/archive, physical/model/ARM64,
accessibility and joined drain remain separate gates. No merge, release,
persistent system-setting change, unrelated-emulator stop or private upload is
performed.
