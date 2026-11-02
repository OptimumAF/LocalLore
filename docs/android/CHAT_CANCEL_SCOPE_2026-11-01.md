# Chat Cancel belongs to its displayed response

B79, 2026-11-01. Refs #13 (M09.03; supporting M09.06), #14 (M10.02 host
checks). Supporting implementation is in review; full criteria remain unchecked
pending owner acceptance and broader qualification. Based on open/unmerged
PR #349 at `a15dd6499d7b3493545f649efdb58c1b230f97ee`.

## Reproduced behavior and fix

Main previously forwarded an unscoped Cancel callback. An old response's retained
button could cancel a newer response, including another story/timeline or a turn
at the same head after rejection or acknowledged cancellation. A slow collector
could also miss the new busy owner when the visible payload equaled the old one.

The scoped `cancel(rendered: ShellState)` now requires the exact current object,
a nonnull response owner, busy/preparing response status and eligibility outside
other workflows before delegating to the existing cancellation path. Copied,
foreign, idle, disposed and stale callbacks cannot dispatch cancellation, write
its diagnostics or cancel a different workflow.

An internal opaque `responseOwner` is minted only after the existing submission
guards accept a response start. Its identity distinguishes otherwise equal busy
states for `StateFlow`; it is transient UI state, never persisted or sent to the
native protocol, model or gameplay engine. It is explicitly cleared at six
non-response boundaries, including the copy-based saved publication and storage
operation paths, current-response completion, demo cancellation and disposal.
Main captures a plain rendered state. Only the response Cancel node is keyed by
referential owner identity (or referential rendered state for inert fixtures),
preserving composer, transcript and form state.

The lifecycle `cancel()`/onStop route remains. Current cancellation still uses
the existing native acknowledgement/reconciliation contract: no premature success,
no invented rollback when commit wins, and recovery required on uncertainty.
Generation fences prevent old preparation/completion from attaching to newer
work. Rust rules, accepted events, SQLite schema, JNI/wire protocol, dependencies,
runtime/model choices and native resource ownership are unchanged.

## Independent regressions and actual checks

Independent writer branch `test/m09-chat-cancel-scope-v1` at
`425d6df4349d2fd63cb86ad6bcfe18c2de718107` owns only the new ten-case JVM file.
Root integrated it as `50043456` on unchanged production before the fix.
Private extension fallback invokes the actual old Cancel route for behavioral
FIRST; the real scoped member takes precedence afterward. Its bytes remain
unchanged throughout: SHA-256
`3b59d961651c43dbf87d55b4cbc0e4ded4ed7dc04790661e7897e18085deda54`.

Checks ran from physical `D:/Worktrees/locallore-player-profile-ui-v1`, using
process-local TEMP/TMP/TMPDIR=`D:/Dev/_Temp`, D: caches/outputs, installed JDK21,
pinned Rust1.93.1 and locked offline dependencies. Each phase had a 900-second
Windows Job owner, actual child/start identity barrier, complete binary output
capture, verified cleanup and identical before/after source maps. No device
command was invoked. Targeted command:

```text
apps/android/gradlew.bat -p apps/android --offline --no-daemon --max-workers=2 :app:testDebugUnitTest --tests org.locallore.app.ChatCancelScopeShellTest
```

Full command:

```text
python -I -S -B scripts/check.py android --offline
```

| Phase | Actual result |
| --- | --- |
| FIRST `50043456`; production identical to #349 | Ten methods: six `java.lang.AssertionError` failures, four positive controls, zero errors/skips. Owned 15,868 ms. |
| GREEN `1bd20ab7` | Same ten methods pass, zero failures/errors/skips. Owned 27,577 ms. |
| Full gate, same `1bd20ab7` | 538 unique JVM methods / 66 JUnit XML, zero failures/errors/skips; lint zero errors, one existing warning and one hint; both public APK audits pass. Owned 55,786 ms. |
| `git diff --check` | Pass. |

Full Gradle gate: 81 tasks, 15 executed and 66 up-to-date. Native build is
up-to-date throughout B79; existing compiled libraries are revalidated and
packaged, with no fresh native compilation or Android/ARM64 execution claim.
The preexisting FrameworkInterruptionTest AtomicReference compiler warning
remains; this packet does not change that test. Two ZIPs retain all 2,592 FIRST
and 2,593 fixed raw source inputs; GREEN/full share the fixed code/archive.

Tests exercise copied/foreign/idle controls, rejected and acknowledged prior turns
at the same revision, cross-story/branch replacement, actual slow collection of
`model.state` through cancellation acknowledgement and another equal-payload busy
turn, pending acknowledgement, failed acknowledgement/UNKNOWN recovery, commit-wins
accepted history, late noncooperative preparation and disposal. Four controls pass
before the fix as well. All ports are synthetic; assertions and timeouts are
unchanged between FIRST and GREEN. This is finite plumbing/race evidence.

Two real ViewModel/Compose journeys retain actual Cancel semantics actions across
a same-head replacement or another timeline response, require the old action to
stay quiet, then verify current Cancel works and accepted history is preserved.
Both runtime-JUnit wrappers compile only into the test APK and invoke the compiled
journey helper. **UNRUN on Android**; no touch/accessibility/native/model or causal
process-death qualification follows.

## Artifacts, review and preservation

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Ordinary app APK | 28,360,760 | `7776a685b4aff7b8a21abc6e63424e9c86b4cdba95558f759e284b07aa4c3ece` |
| Test APK | 2,530,577 | `0f61c5b7a26557f10ff8d7c4ac69ecd76370a89c69a02249307e53a6069fd69f` |

Common signer remains
`17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564`.
Test permission remains only REORDER_TASKS. Both APK audits and four packaged
native ELF/ZIP 16 KiB alignment checks pass; runtime permission behavior is separate.

Independent source review verifies one owner mint/six explicit clears, the scoped
guard, Main capture and narrow key, all existing string/non-ASCII sequences,
unchanged native/wire/gateway contracts, and the race-test oracles. It finds no
concrete blocker: 4,539 bytes, SHA-256
`aceeafd7a261a948adc23cc565988cbc14a682d75443538341fc4e216f51afdb`.
The closed collector joins actual raw captures, owner terminals, source maps,
every ZIP entry, saved XML, exact test bytes, lint and compiled-only UI definitions:
7,196 bytes, SHA-256
`c82ed0255956355e1eb02557ced110f44ce396b26a209514e5240f8a48f0dab2`.
The independent closed reader verifies 313 recorded pins, 5,185 source ZIP
entries, actual command/owner/helper/capture chains, XML counts, all 149 inherited
copies and 71 current report/artifact rows. Both five-unit UI wrappers invoke
the compiled 272-unit journey helper; Android execution remains unrun. It finds
no issue and has no product/test authorship overlap. Closed review: 4,286 bytes,
SHA-256 `65daaddb19963901f9ec96aaa7507af848352c4c1554d07a240de02f8c0b314f`.

Captures use `D:/Dev/Experiments/LocalLore/2026-11-01-chat-cancel-scope-v1`;
selected recovery uses the matching `D:/Dev/Recovery/LocalLore` root. Before
regeneration, all 149 inherited reports/artifacts (54,302,401 bytes) were verified:
80 existing immutable B78 copies are reused and 69 unique files (336,661 bytes)
copied. No redundant old APK/native copies were created. Their original working
paths may regenerate; the immutable copies retain their historical attribution.
FIRST/GREEN XML and raw captures remain before full rebuild. All current 66 JUnit
XML, lint, both APKs and both generated native libraries are separately preserved.
Public Git pushes do not substitute for these private generated-evidence copies.

Controls stay below 64 MiB, selected recovery below 256 MiB; generated build
output is sampled every two seconds and at terminal below 3 GiB (terminal
661,260,895 bytes). These are observations/budgets, not a filesystem quota or
full generated-tree/global-cache/TEMP peak backup. No raw private data is uploaded.

## Remaining gates

Current-source Android execution, physical-device/model quality/performance,
ARM64 execution, accessibility, causal process death and full milestone acceptance
remain open. The separate B77 refusal, frozen Flow source/ledger and SDK14/B66
inputs are preserved. No emulator/ADB/phone discovery or lifecycle, model operation,
ledger change, deletion, system setting, unrelated-emulator stop, merge or release
occurred. Any device operation still needs fresh matching authority and guards.
Next host-runnable task: inspect other retained chat lifecycle controls against
their exact operation/scope, reproducing a fault before changing behavior.
