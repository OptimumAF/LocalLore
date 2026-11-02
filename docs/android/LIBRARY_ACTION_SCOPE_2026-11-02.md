# Storage navigation belongs to its displayed view

B80, 2026-11-02. Refs #13 (M09.02/M09.03; supporting M09.06), #14 (M10.02
host checks). Supporting implementation is in review; full criteria remain
unchecked pending owner acceptance and broader qualification. Based on
open/unmerged PR #350 at `080b191fb1bbc9ad9684d7eb95af6e70da61882b`.
The existing operation namespace retains its initial `2026-11-01` path.

## Reproduced boundary and implementation

Unscoped recovery and story selection could act on replacement views. Timeline
selection already checked its current DTO, but an old view could borrow the new
DTO. A slow collector also missed new, equal-valued completed refresh/error views,
making reference-based controls unusable if only the callback check were added.

Three scoped overloads now require the exact current eligible persistent view.
Recovery additionally requires its displayed recovery-required condition. Story
selection accepts only the actual shown row object; timeline selection delegates
to its existing identity, selected-story and native validation checks. Missing
selection remains supported for an otherwise available story library or initial
storage recovery. Existing compatibility/lifecycle APIs keep their behavior.

All 30 Shell publication sites now emit a transient `ShellFrame` containing the
actual current state. Main collects those frames and captures plain state for
forwarding. The legacy state stream and DTO equality remain; B79's per-response
owner and its retirement rules stay intact. These frames are display identity,
not canonical state, native review or gameplay authority.

The UI uses a referential wrapper for both keys and `rememberUpdatedState`:
passing raw value-equal ShellState would retain an old reference. Five narrow
action-key families cover recovery, two openers and two kinds of menu rows.
Each popup opening mints a local owner; rows check that owner and the current
view before consuming it, closing the menu or forwarding. A remembered lifetime
holder is retired on Screen disposal, so old controls cannot borrow a surviving
ViewModel when the Screen is remounted with the same state. Dismiss callbacks
only update their matching popup's private remembered cells.

Composer/transcript/popup containers are not keyed wholesale. Native validation,
accepted history, recovery/acknowledgement, Rust/JNI/wire/schema, inference and
dependency choices are unchanged. Kotlin adds no gameplay or storage authority.

## Independent cases and actual execution

Independent test commit `d196162eb86259ffdbdeebc7a7f4c78fd38c4d94` supplies only
LibraryActionScopeShellTest.kt. Root integrated it as `e3322589` before production
changes. Its twelve methods remain byte-identical across every phase, SHA-256
`98d5ddd36a109531df44f8faad745867ab949d2cc0a9fa42f9a4ab6d07ad31fb`.
Private overload/flow fallbacks exercise old production for behavioral FIRST,
without missing-symbol compilation failures or invented flow tokens.

All phases ran from physical `D:/Worktrees/locallore-player-profile-ui-v1` with
process-local TEMP/TMP/TMPDIR=`D:/Dev/_Temp`, D: caches/outputs, installed JDK21,
pinned Rust1.93.1 and locked offline dependencies. Each uses a 900-second Windows
Job owner, actual child/start barrier, complete binary capture, known cleanup and
identical before/after source maps. No device command ran. Targeted command:

```text
apps/android/gradlew.bat -p apps/android --offline --no-daemon --max-workers=2 :app:testDebugUnitTest --tests org.locallore.app.LibraryActionScopeShellTest
```

Full command:

```text
python -I -S -B scripts/check.py android --offline
```

| Phase | Actual result |
| --- | --- |
| FIRST `e3322589`, unchanged production from #350 | 12 methods: 11 `java.lang.AssertionError` failures, one positive control, zero errors/skips. Owned 13,935 ms. |
| Intermediate GREEN `1e308da3` | Same 12 pass, 23,748 ms. Before the Screen-remount fence; not final UI qualification. |
| Intermediate GREEN `10daaf03` | Same 12 pass, 15,408 ms; production includes remount fencing. |
| First full gate, `10daaf03` | **FAILED**, 41,875 ms: new UI test referenced unavailable Espresso/pressBack symbols. JVM task actually passed 550 methods / 67 XML, but no full-gate, current test-APK, lint or audit qualification follows. |
| Final GREEN `85168714` | Same 12 pass, zero failures/errors/skips, 8,791 ms. |
| Final full gate, same `85168714` | **550 unique JVM / 67 XML**, zero failures/errors/skips; lint zero errors, one existing warning and one hint; both public APK audits pass. Owned 43,352 ms. |
| `git diff --check` | Pass. |

Repeated cohorts are not additional distinct tests. Final Gradle execution is
81 tasks: eight executed, 73 up-to-date. Native build is up-to-date in all B80
phases; existing binaries are revalidated/packaged, not freshly compiled or run
on Android/ARM64. Four ZIPs preserve FIRST's 2,595 and each fixed checkpoint's
2,596 raw source files; final GREEN/full share one exact code/archive.

The cases cover copied/foreign/prior views borrowing current DTOs, hidden healthy
recovery, copied/unshown/branch-only story targets, story/branch replacement,
current one-shot selection, existing timeline rules, actual slow collection after
equal-valued successful refresh and failed recovery, pending/failed recovery
history, opening/acknowledgement/creation fences and disposal. No native rule,
assertion or timeout was weakened.

Four real ViewModel/Compose journeys cover equal failed recovery with unavailable
selection, equal library refresh, same-state popup close/reopen, old opener/row
callbacks, fresh timeline selection, and Screen disposal/remount while keeping
the exact same ViewModel/state. All use synthetic snapshots. Runtime-JUnit
definitions and the journey helper compile only into the test APK; **UNRUN on
Android**. Rendered/touch/accessibility, native storage, phone/model and causal
process-death evidence remain separate.

## Retained failure and compatibility correction

The first full build's raw compiler errors, source ZIP, 67 current JVM XML and
partial product APK remain frozen. The surviving test APK was still B79's
`0f61c5b7...69f`; it is explicitly inherited and unqualified for this source.
Partial record: 44,802 bytes, SHA-256
`741fa7a539cd0b36b86812b4f6c734c587e36eccc68fde9ca978fb56b5f64a54`.

The test had assumed a cached Espresso artifact was on the classpath. A test-only
commit replaces that unavailable reference with the project's existing
InstrumentationRegistry / `sendKeyDownUpSync(KEYCODE_BACK)` pattern. Installed
official android-36.jar confirms the method signature. Calls remain outside the
UI-thread blocks and wait for popup disappearance. No dependency, permission,
assertion, selector or production byte changed for this correction. Earlier
passing and failed phases retain their original attribution.

## Artifacts, review and preservation

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Ordinary app APK | 28,365,001 | `3c355ec7568e8a6468790c417d986d413f5414f43cde2719f77a9041ea15abb6` |
| Test APK | 2,541,802 | `5a96cfd007e42a5eb7e739375316c2ba43263490c2cca784b35d91b83712b698` |

Common signer remains
`17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564`.
Test permission remains only REORDER_TASKS. Both APK audits and four packaged
native ELF/ZIP 16 KiB alignment checks pass; runtime permission behavior is separate.

Independent source review verifies all 30 publications, the sole direct assignment
inside the helper, preserved conditional publication branches, current-view/DTO
eligibility, Main forwarding, referential UI updates, popup tokens, lifetime fence,
unchanged strings/native contracts and the original test oracles. V1 remains
4,554 bytes, SHA-256
`2e2b7826eaec53bc6182745655c32953964890131ec4b9cb36c6f754603259f3`.
Final v2 verifies the test-only compatibility change, unchanged production and
failure attribution: 3,673 bytes, SHA-256
`b7d9153ee271e1a0d7dccbc47d240bf8b0b946b7a62577babe9722013c24c1bc`.
The closed collector joins all six phase chains, four ZIPs, test hashes, report
copies and current artifacts; it keeps the failed full gate separate. Record:
12,667 bytes, SHA-256
`a94272386147b8761e9e0a9d875cb01028041a3d5f3d07761519b2f7987c189a`.
An independent closed reader verifies 411 recorded pins, all six actual phase
chains, 10,383 ZIP entries, unchanged oracle bytes, 151 historical references
and 72 final report/artifact rows. All four five-unit JUnit wrappers invoke the
compiled 686-unit journey helper; this remains compile-only evidence. It finds
no issue and has no product/test authorship overlap. Closed review: 5,777 bytes,
SHA-256 `0122299abf2337081ffd13bd5e2e3b4d42f106367d0862644451a956eb7dfa39`.

Captures use `D:/Dev/Experiments/LocalLore/2026-11-01-library-action-scope-v1`;
selected recovery uses the matching `D:/Dev/Recovery/LocalLore` root. Before
regeneration, 151 inherited records/artifacts totaling 54,318,045 bytes were
verified: 81 frozen prior bindings reused and 70 unique files (342,537 bytes)
copied. Their original working paths may regenerate; immutable history remains.
Each targeted XML/raw phase, both failed and qualified full cohorts, all current
67 JUnit XML, lint, APKs and generated native libraries are retained before reuse.
The failed product copy remains separate even where final product bytes match.

Controls remain below 64 MiB and selected recovery below 256 MiB including prior
referenced data; generated output is sampled every two seconds and at terminal
below 3 GiB (terminal 666,290,412 bytes). These are observations/budgets, not a
filesystem quota or full generated-tree/global-cache/TEMP peak backup. No raw
private data is uploaded, and public pushes do not preserve ignored evidence.

## Remaining gates

Current-source Android journeys, physical-device/model quality/performance,
ARM64 execution, accessibility, causal process death and full acceptance remain
open. B77's failure, frozen Flow source/ledger and SDK14/B66 inputs are preserved.
No emulator/ADB/phone discovery or lifecycle, model operation, ledger change,
deletion, system setting, unrelated-emulator stop, merge or release occurred.
Device execution still needs fresh matching authority and guards. The next
validation packet is current-source recovery/library journey qualification;
host preparation can proceed while Android execution remains separately gated.
