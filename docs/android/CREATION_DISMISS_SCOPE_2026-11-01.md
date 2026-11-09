# Closing a new-story view belongs to that displayed view

B78, 2026-11-01. Refs #13 (M09.02; supporting M09.06), #14 (M10.02 host
checks). Supporting implementation is in review; full milestone criteria stay
unchecked pending owner acceptance and broader qualification. Stacked on
open/unmerged PR #342 at `025f75ebb10c5382d216e8012e32148658b172b2`.

## Behavior and authority

Main previously passed an unscoped creation Close callback. A retained callback
could close a replacement starter/original review or cancel newer creation work.
Slow controller/ViewModel collectors also missed a new, value-equal busy owner
after an actual close, drain and reopen.

The outer controller now requires the exact current visible rendered state and
a live owner before delegating dismissal. Its 31 publication sites emit identity
frames containing the actual current state. The ViewModel forwards that stream;
Main collects it and captures a plain rendered state for the callback. Only the
Cancel buttons in the starter and original forms receive reference-based keys,
retiring old clickable nodes without resetting the form, scroll or editor.

Current busy/creating work remains cancellable. Existing joined drain,
uncertain-create refresh, generation/disposal fencing, same-render field intents,
exact native review and one-shot creation behavior remain. No new child-controller
dismissal API is needed: the sole production route checks its current outer
owner before synchronously delegating to the existing original controller.
Rust/native rules, canonical state, persistence, JNI/protocol, dependencies and
runtime/model selections are unchanged. New tests use synthetic ports.

## Actual checks and retained FIRST

Independent writer branch `test/m09-creation-dismiss-scope-v1` at
`f5042e8175f9819e07636df508d70ffbf1438df9` supplies only the new JVM file.
Root integrated it as `7e69107e` before changing production. The nine-case file
remains byte-identical in FIRST, GREEN and the full gate: SHA-256
`28fbbce05ee6494870d4433b619a955aad2f7524a17903b389582c98ae6c140a`.
The baseline extension and reflective flow fallback execute the old production
behavior, allowing assertion failures rather than missing-API compile errors.

All commands ran from physical
`D:/Worktrees/locallore-player-profile-ui-v1`, with process-local TEMP/TMP/TMPDIR
at `D:/Dev/_Temp`, D: caches/outputs, installed JDK21, pinned Rust1.93.1 and
locked offline dependencies. No dependency was introduced. Each phase used a
900-second Windows Job owner, actual-child identity/start barrier, complete
binary output capture and verified cleanup. No device task was invoked.

Targeted command:

```text
apps/android/gradlew.bat -p apps/android --offline --no-daemon --max-workers=2 :app:testDebugUnitTest --tests org.locallore.app.StoryCreationDismissScopeTest
```

Full command:

```text
python -I -S -B scripts/check.py android --offline
```

| Phase | Actual result |
| --- | --- |
| FIRST `7e69107e`; production identical to #342 | Nine methods: six `java.lang.AssertionError` failures, three positive controls, zero errors/skips. Owned 225,337 ms. |
| GREEN `45acfc7dcc8b72401ef66a20ae2577eadbd0fbf2` | Same nine methods pass, zero failures/errors/skips. Owned 30,543 ms. |
| Full gate, same `45acfc7d` | 528 unique JVM methods / 65 JUnit XML, zero failures/errors/skips; lint zero errors, one existing warning and one hint; both public APK audits pass. Owned 72,634 ms. |
| `git diff --check` | Pass. |

Full Gradle gate: 81 tasks, 15 executed and 66 up-to-date. FIRST freshly built
both Android native ABI prerequisites; the full gate's native task is up-to-date.
Cross-compilation and packaged ELF checks do not establish Android/ARM64 execution.
Two source ZIPs preserve 2,589 FIRST and 2,590 fixed source files; each phase has
matching before/after maps. GREEN and full use the same fixed ZIP/code.

Oracles cover copied/foreign/hidden/prior-edit/prior-instance Close, a newer
noncooperative create, real controller and VM slow collection through equal busy
reopen, starter-to-original and edited-original routing, current joined preview
close, current uncertain creation close, and disposal. Three positive controls
pass before the fix as well. No assertion, timeout or native rule was weakened.

Two real-controller Compose journeys retain actual Cancel semantics actions,
replace the starter review or edit an original draft, require the old action to
stay quiet, then verify current Cancel works. Both runtime-JUnit methods compile
only into the test APK; **UNRUN on Android**. They do not establish touch,
rendering, accessibility, device/model, JNI or process-death acceptance.

## Artifacts, review and preservation

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Ordinary app APK | 28,360,528 | `a51ecf05b91f39f46ce0a7c2e1146ef964a9c4c2d51abaf5e085244035865652` |
| Test APK | 2,522,993 | `fc264fb58d19df3bd6c7b85771d3c2dfdc19d43d602f6fa75c80a35a7c54937b` |

Both audits pass; common signer remains
`17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564`.
Test permission remains only REORDER_TASKS. Native libraries retain 16 KiB ELF
and ZIP alignment checks. Audits do not establish runtime permission behavior.

Independent source review verifies all 31 publication sites, the sole direct
assignment inside the publication helper, VM/Main wiring, both narrow keys,
unchanged existing string literals/non-ASCII text and unchanged original child
controller. Review: 2,466 bytes, SHA-256
`24bd94fb0a88bf50fa273072080b9dfa25a46f4ef8ccaa843e309760366ae5c7`.

Captures use
`D:/Dev/Experiments/LocalLore/2026-11-01-creation-dismiss-scope-v1`; selected
recovery uses the matching `D:/Dev/Recovery/LocalLore` root. Before build reuse,
137 inherited reports/artifacts totaling 53,838,992 bytes were copied and
hash-checked; they retain their historical attribution. FIRST/GREEN JUnit XML
and binary captures were preserved before the next phase. All current 65 JUnit
XML, lint report, both APKs and both generated native libraries are separately
retained before any future regeneration. Artifact copies live in recovery,
outside the 64 MiB control-output budget. Existing failures are not rewritten.

The closed collector joins raw captures, owner terminals, report copies,
source maps and every source ZIP entry. It verifies unchanged oracle bytes,
actual counts, lint and compiled-only UI definitions. Closed record: 7,310 bytes,
SHA-256 `fd7431863ea8d0c3d6940b7bba8d2dcbbf718851c6243589a45556bf1d1eeb49`.
The independent closed reader verifies 299 file pins, 5,179 ZIP entries,
actual child/command/owner identity and capture chains, preserved XML counts,
all 137 inherited copies and current 70 report/artifact rows. Both five-unit
JUnit wrappers invoke the compiled 361-unit private form helper; this remains
compile-only evidence. It reports no findings, with authorship separate from
the product and test writers. Closed review: 4,230 bytes, SHA-256
`3de5077060bd59deab593d547e928fcadd26ef1faf7eae303e51fbb0b2330609`.
Generated output was sampled every two seconds and at terminal below 3 GiB
(terminal 658,904,868 bytes); controls below 64 MiB and selected recovery below
256 MiB. These are observations/budgets, not a filesystem quota or a full
generated-tree/global-cache/TEMP peak backup. Original captures remain private.

The separate B77 refusal, frozen recovery source, ledger, SDK14/B66 APK pair,
pending device proposals and other emulators remain untouched. No new emulator,
ADB/phone discovery or lifecycle, model operation, ledger change, deletion,
settings change, private upload, merge or release occurred.

## Remaining gates

Actual current-source Android journeys need matching execution authority and
fresh admission/resource/ownership gates. The spent B77 grant cannot qualify
this new source or authorize another attempt. Physical-device, model quality,
performance, ARM64 execution, accessibility, process-death and full milestone
acceptance remain open. The next host-runnable investigation is chat Cancel
callback scope across turn replacement, reproducing any fault before changes.
