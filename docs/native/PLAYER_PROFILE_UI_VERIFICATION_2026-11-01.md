# SDK13 Player state UI host verification - 2026-11-01

Refs #14 (M10.02), #13 (supporting M09.06) and #307 (M09.04).
The supporting host implementation is in review; full criteria remain unchecked.
No Android execution or milestone acceptance is claimed.

## Implementation and source

This separate [fourteen-method profile](PLAYER_PROFILE_UI_V1.md) preserves the
SDK12 eleven-method prefix and adds the three current Player state methods.
It has its own fixed source/APK/baseline/roster/session/proof/owner identity.
The only shared source edit adds its protocol to the closed-guest metadata
reader; existing protocol entries and all validation remain.

Harness base is unmerged PR #332 `affdaa38b39d8a7b425df7e92fbb5d7162fbffa2`
on #331. Product dependency is separately unmerged PR #333 at
`d687f5d560f61a704a91cbaf5c742cb7eac64996`, actually built at
`b42a34f15d323ba2234aa3e4f125014af2a6163b`. No Kotlin, Rust, schema, native
dependency or SDK version changes. No gameplay authority moves into Kotlin.

Four source-only physical D: worktrees had exclusive ownership. Root owns
integration. Authority adapters `db487125` and tests `efb158f3`, build adapter
`445042ba` followed by strict fixes/tests `dce241aa`, and controller/activation
`82dd8434` are integrated. Root added the source/document scope regression and
the sole protocol registration `894811cd`. Integrated executable head is
`fb4f08086b99b1bf8ec08ff4b5521627b966e3ab`; the final handoff changes only README
and this report. All 2,617 tracked raw inputs stayed unchanged during integrated
manifest collection. Each earlier cohort retains its own source maps; this is
not one combined full-suite execution on a common final head.

## Checks actually executed

Selected Python unittest modules ran in separate bounded, captured workers
from their explicit physical D: checkout, with TEMP/TMP/TMPDIR on D:/Dev/_Temp
and bytecode output disabled. No dependency or global tool settings changed.

| Actual selection | Result | Recorded duration |
| --- | --- | --- |
| Original exact SDK13 closure test, before registration | 1 assertion failure, no errors/skips | owner0.462s |
| `scripts.tests.test_profile_ui_profile` after registration | 13 pass, 0 failures/errors/skips | suite1.715s / owner2.037s |
| First build-unit cohort | 10 pass, 1 metadata error, no assertion failures/skips | owner4.138s |
| New DEX8193 bound counterexample | 1 assertion failure, no errors/skips | owner0.521s |
| New growing-file counterexample | 1 assertion failure, no errors/skips | owner0.464s |
| Corrected `scripts.tests.test_profile_ui_build` | 13 pass, 0 failures/errors/skips | suite4.155s / owner4.254s |
| `test_profile_ui_controller` and `test_profile_ui_activation` | 9 + 11 pass, 0 failures/errors/skips | suites54.812s / 7.094s; one owner75.753s |
| Source/document test plus existing instrumentation-reader module | 1 + 26 pass, 0 failures/errors/skips | suite0.082s / bounded child0.260s |
| Genuine fixed-B62 artifact graph, separate build worktree | pass, data returned only | body1.291s / owner1.389s |
| Integrated manifest publication and exact replay | pass, one manifest / 24 source bindings / 14 selectors | body2.583s / bounded child2.734s |

The final passing host cohorts total **47 new checks and 26 existing
regressions**, not including earlier failed witnesses or historical B62 JVM
results. The controller/activation cohort uses an explicit mocked build/native
boundary; its tested implementation bytes remain unchanged. The isolated later
build-reader fixes are covered by its own thirteen checks and actual artifact
guard; no repeated controller run or same-source full-suite claim is substituted.

Tests cover old-authority retagging, exact command/source/artifact rosters,
typed clocks/identities/claims, product rejection before native entry, all cleanup
bits, growing input bounds and native hardlink roles. The controller fixture
uses one 39-client/14-method positive binary graph, plus preserved first-uncertain
and skipped-thirteenth-method partial graphs. Wrong/late/duplicate/reordered/
missing client, bad JUnit despite exit0, borrowed proof/caller, drifted package/
UID/hash, failure/deadline and unknown cleanup cannot pass. Activation exercises
start barriers, caller termination, sticky cleanup/publication faults and replay
of the same result after owner closure. Synthetic framing is not actual ADB,
process ownership, JNI/SQLite or Android qualification.

## Current artifact evidence

Root freshly inspected all fourteen definitions in the actual current B62 test
APK: public concrete instance methods, void/no arguments, runtime JUnit
annotations and bounded nonempty bodies; source declarations also match. Their
class families are absent from product. Code-unit counts in roster order are
130,406,568,664,553,800,451,642,490,857,395,859,1227,881. The 0.735s readback
record is 10,803B, SHA256
`1e79aeb1ee5cfee788a6cf68249dd265999d27265bee2e7a35994d6e83b9ad44`.
This repeats DEX definition inspection only, not JUnit execution, signing or ELF
tools. Imports precede its external-operation trap, as recorded.

The integrated fixed-byte manifest is 10,792B, SHA256
`a42a683a1b16db59c9b596e5cbfce1cf4b0491fdbed782df5de453f2c7fe945d`.
It binds source2,561/tested2,560 with exactly three documentation changes,
historical454 JVM cases/55 reports, native-stage chains, producer/capture and
the85-pair recovery seal. That historical evidence is not rerun by attestation.
The separate genuine graph read285,170,841B/2,806files. Integrated collection
performs ten fixed read-only Git calls across creation and replay, with zero
forbidden calls after imports. Its canonical manifest is data, not permission,
input, admission, prepared guest or runtime acceptance.

| Exact artifact | Bytes | SHA256 |
| --- | ---: | --- |
| Product APK | 28,045,456 | `4129009f12f9bc21528c08afcd4d81ff56e8a96d8bc9cbb324b8130778f15a86` |
| Test APK | 2,336,350 | `4935ef0df5b10a8dd718556c2d92a9b46d2b29c7ea4ece7eb287c3908117cba2` |

The recorded common signer is
`17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564`.
No historical signing-tool execution is repeated or promoted into a new result.

## Failures, corrections and review

The first unit cohort's `path_changed` error was a strict parent-metadata
refusal. A quiescent diagnostic did not reproduce it; the historical changed
parent and cause remain unresolved. Concurrent fixture work is not established
as the cause. The parent guard was retained; the earlier error stays an error.

The original8193 witness exposed a mismatch with the actual8192-unit reader
bound. The growing-file witness consumed4,099B for a declared3B pin, despite
eventual identity/hash refusal. Reads now stop at declared size plus one byte,
preserving before/held/final identity, hash, deadline and512MiB total limits.
Both original assertion failures and source snapshots remain. A Windows-only
fixture class guard prevents non-Windows discovery from running physical D:
fixtures; all thirteen methods actually ran on Windows without skips.

Root's first integration wrapper expected list-form subprocess audit arguments.
Windows supplies the serialized command string, so it refused before the first
Git process and before manifest creation. The append-only v2 wrapper compares
only exact serialization of the same three fixed Git vectors; no command or
product guard was broadened. Original capture is retained; no unit/Android test
was rerun to hide the wrapper failure.

Independent non-owned reviews checked authority, controller/activation, build
guards and test oracles. Final review closes both bounded-read/DEX findings;
no concrete blocker remains within scope. Authorship overlap is disclosed and
review is not owner acceptance. Source/static reader typos and failed setup
observations retain their separate attribution.

## Preservation and remaining gates

Exact helpers, raw captures, source maps, refused and passing cohorts and the
data-only manifest remain under
`D:/Dev/Experiments/LocalLore/2026-11-01-profile-ui-harness-v1`. Independent
recovery/source readback and publication seals are linked from the ticket
handoff after execution. Declared budgets: four source trees256MiB,
host fixtures128MiB, controls64MiB and selected recovery256MiB. Existing B62
build output/APKs/recovery remain in place; no new build or model output.
There is no global-cache/TEMP high-water or full generated-tree backup claim.

All fourteen current-product Android methods remain **UNRUN**. The pending
SDK12 proposal covers older inputs and remains separate; no grant was reused.
Actual JNI/SQLite, physical/ARM64, process death, touch/TalkBack/real IME/
orientation/visual geometry, real-model story quality, full journeys and release
acceptance remain required. The fixed content Box is not a Dialog-window proof.
No production ledger, authorization, admission, input, guest or runtime root
was created. No emulator/ADB/phone discovery or lifecycle, retirement/deletion,
model transfer, settings/shared-service/unrelated-emulator action or merge.

Next runnable task: current read-only capacity/preservation inventory and a
reviewable exact fourteen-method run proposal. Matching fresh execution
authority and current admission/ownership gates are still required before boot.
