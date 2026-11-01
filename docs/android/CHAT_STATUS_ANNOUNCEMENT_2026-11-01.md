# Chat status announcements — 2026-11-01

Refs #13 (M09.05, supporting M09.03/M09.06). This slice is in review; full
accessibility/task criteria and owner acceptance remain open. It is stacked on
PR #320 at `24cabadcbc0469b7b872335ec4f5c0d371d8bdbe`.

## Source problem and change

The existing Polite notice and busy-status nodes were lazy-list footer items,
after the transcript. They could be absent or offscreen while reading older
messages. Android's [lazy-list documentation](https://developer.android.com/develop/ui/compose/lists)
explains viewport-dependent composition; the [semantics guidance](https://developer.android.com/develop/ui/compose/accessibility/semantics)
describes Polite live regions for changing alert content. This is a source-derived
availability gap, not an observed TalkBack failure.

The screen now renders a compact status Text above the weighted LazyColumn,
inside the existing inset-aware content Column. It uses Polite live-region
semantics, at most two visual lines and ellipsis; the original full string is
passed to Text. The compiled tests assert that full string in semantics despite
visual ellipsis, but that assertion has not yet run on Android.

Two small pure functions centralize presentation: `chatBusyStatus` reproduces
the existing preparing/cancellation/opening label precedence; `chatAnnouncement`
uses that label while busy, otherwise the current nonblank notice unchanged.
Busy state takes priority over a retained old outcome notice. Missing or
whitespace-only idle notices produce no announcement. No outcome is parsed,
classified or accepted by these functions.

The full original footer text, tags, lazy items, ordering and counts remain.
Only the two duplicate explicit chat live-region properties were removed.
Composer validation and draft-restoration live regions remain independent.
No auto-focus, speech API, scroll request, callback, new state owner, engine/FFI,
schema, provider, canonical history or dependency change was introduced.

The parent keyboard fix is retained. Compile/target SDK36, minSdk26 and existing
Compose Foundation1.8.2 stay unchanged. Frozen PR #317/#318/#319 source, APKs,
helpers, shared storage ledger and pending operations remain untouched.

## Original checks

Four new JVM methods cover explicit label precedence (including contradictory
flags), stale outcome notices while busy, exact long Unicode/whitespace notice
preservation and suppression of empty/blank idle notices. Expected labels use
an independent scenario table, not a duplicate of production branching.

New class `org.locallore.app.ui.ChatStatusAnnouncementTest` has two compiled
journeys:

| Method | Intended Android acceptance |
| --- | --- |
| `historyReaderKeepsItsAnchorWhileCurrentBusyAndOutcomeAnnouncementsStayAvailable` | Current Polite status remains available through preparing/cancellation/accepted/rejected snapshots while an older row keeps its offset relative to the list; actual footer nodes are explicitly brought into view and lack duplicate LiveRegion properties |
| `unicodeDialogueAndScopeStaySafeWhileEllipsizedNoticeKeepsFullSemantics` | Full long Unicode notice remains semantic text despite two-line ellipsis; unsent dialogue/kind, relative reading anchor and quiet callbacks survive status changes; a different branch clears its draft |

Root made history setup deterministic before executing any check: the fixture
aligns message10 at lazy index3+9, rather than merely finding a row near the
bottom that a new status band could obscure. Existing three prefix rows and
all production navigation counts are unchanged. Initial source is retained.

**Both Compose journeys remain UNRUN.** They use the real screen with inert
SCRIPTED snapshots and quiet callbacks; no native, model or accepted-turn
qualification follows. Actual TalkBack notification, focus, rendering, keyboard,
physical-phone accessibility and complete gesture behavior remain separate.

## Actual verification

Physical working directory:
`D:/Dev/Projects/The Hero's Journey/LocalLore-android-runtime-review/apps/android`.
TEMP/TMP/TMPDIR were process-local `D:/Dev/_Temp`; existing Gradle cache stayed
at `D:/Dev/Tools/Caches/Gradle`. Installed JDK21.0.4/SDK locations were preserved.
Gradle8.11.1, AGP8.10.1, Kotlin2.2.21 and Compose BOM2025.05.01 were unchanged.

```text
gradlew.bat --offline --no-daemon --console=plain --rerun-tasks :app:testDebugUnitTest :app:compileDebugAndroidTestKotlin :app:lintDebug -x :app:buildRustAndroid
```

The first actual Gradle invocation passed in70.269 seconds:

- **415 JVM tests in48 XML suites**, zero failures/errors/skips, including all
  four new mapping methods. Original/copy report bytes and unique case identities
  were checked.
- Production and Android-test compilation passed. Public bytecode declarations
  for both new Compose methods were inspected and retained.
- Lint passed with zero errors, one existing GradleDependency warning and one
  AutoboxingStateCreation hint. The existing FrameworkInterruptionTest
  AtomicReference/Boolean compiler warning was unchanged.
- Source/UTF-8 and whitespace checks passed. No executed test failure or Android
  baseline RED is claimed. A pre-build ad-hoc identifier-count checker initially
  matched `onMode` inside `LiveRegionMode`; its matcher was corrected to identifier
  boundaries without changing production code or assertions.

The native task was explicitly excluded for these UI-only checks. No Rust/JNI
build, APK packaging, Android journey or real-model result is qualified here.
Independent review read all four files and Root's fixture correction; it found
no concrete additional blocker and performed no test or device execution.

## Preservation and remaining gates

The old a6029afe branch/source ZIP and three ignored Rust metadata files were
preserved before reusing the clean checkout. Implementation used a separate
writer; Root integrated only the history fixture setup and documentation after
its writes closed. Reviewers used separate read-only checkouts.

Evidence is under
`D:/Dev/Experiments/LocalLore/2026-11-01-chat-status-accessibility-v1` (16MiB limit),
generated build output has a separate4GiB limit, and selected source/evidence
recovery a separate64MiB limit. Original/initial source, captures and reports
remain. Canonical Git and exact raw source archives preserve line-ending forms
without changing global Git settings.

Both existing emulator-operation questions remain pending. Their frozen scopes
do not include these new tests; no input, admission, authorization, guest, plan,
reservation or boot was created. No device/ADB/phone/model/runtime process/port
census, storage mutation, unrelated emulator/shared ADB stop, system-setting
change or merge occurred. No new approval question is issued here.

Next runtime task remains the already prepared SDK10 six-method run after its
applicable approval; this status fix and PR #320's keyboard fix need later
Android qualification. Full M09, phone/model/ARM64 and release gates remain open.
