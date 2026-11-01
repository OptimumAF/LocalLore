# Saved-story headings — 2026-11-01

Refs #13 (M09.02/M09.03, supporting M09.06). This slice is in review; full
task acceptance remains open. It is stacked on PR #322 at
`90930c673bd6a7c2f49a2f82117934debd75584e`, preserving its status announcement
and PR #320's keyboard inset behavior.

## Problem and authoritative input

The screen previously introduced every selected saved story as Lantern Quay,
with Mira nearby and Oren's borrowed key in the player's satchel. Actual authored
fixtures include Copper Orchard and North Pier. A fixed demo introduction can
therefore contradict the selected world or its accepted history.

`DurableGateway` already joins the current native player scope/head to the
catalog root's title when constructing `SavedStory`. The header now uses exactly
`state.selectedStory.title`, with the neutral prompt
`Choose what to try or say next.` and an explicit `Saved story` label. This is
story metadata, not a claim about the player's current location. Every saved
story, including the starter, receives the neutral prompt.

`SavedSnapshot.location` and `ShellState.storageLocation` are database paths.
They must not become a location label. No eligible typed location display value
is published to this header. The private authored-scene narration frame is not
a header interface; no prose, facts, message history, IDs, paths or model output
are parsed to manufacture one. See [initial presentation ADR0012](../adr/0012-initial-story-presentation.md)
and the [authored scene V2 contract](../runtime/AUTHORED_SCENE_V2_CONTRACT.md).

The nonpersistent demo retains the exact old Lantern Quay title and body with
a `Demo scene` label. A persistent state without a selected story has no scene
heading. Both labels, title and introduction remain in the same existing lazy
scene item; the title retains heading semantics. Original item counts, keys,
ordering, styles, accepted messages, draft/follow policy and callbacks remain.
The pure immutable `StoryHeading` projection owns no gameplay state.

This fix covers the introduction only. Other existing demo-specific controls
can still name Mira. Legitimate accepted narration or a user-selected title can
also contain Lantern Quay, Mira or Oren; no global text ban is appropriate.
No engine, FFI, schema, provider, dependency or canonical-state change occurs.

## Actual regression and verification

Physical checkout:
`D:/Dev/Projects/The Hero's Journey/LocalLore-durability-review`, branch
`fix/m09-saved-story-heading-v1`. Commands ran from `apps/android` with
process-local TEMP/TMP/TMPDIR at `D:/Dev/_Temp` and the existing Gradle cache at
`D:/Dev/Tools/Caches/Gradle`. Installed JDK21.0.4, Gradle8.11.1, AGP8.10.1,
Kotlin2.2.21, Compose BOM2025.05.01 and SDK locations were unchanged.

First, commit `4a9c86fcc2cb9a1b78dc00cd061ab6a4bab8e485` extracted the original
scene predicate and exact demo constants into a helper wired to the real screen.
Independent review verified this behavior-preserving baseline before the fix.

```text
gradlew.bat --offline --no-daemon --console=plain --rerun-tasks :app:testDebugUnitTest --tests org.locallore.app.ui.StoryHeadingTest -x :app:buildRustAndroid
```

Actual result: five methods executed, three assertion failures, zero errors or
skips, 42.276 seconds. The selected-nonfirst, saved starter/authored neutral
introduction, and Unicode/branch metadata cases failed. Demo and unresolved
controls passed. This is a JVM projection regression, not an observed rendered
Android failure. The baseline source, XML, log and terminal receipt remain.

Implementation commit `a4964e7c59ab0534b3a24ea125ef689a706450b5` fixes the
projection and adds two Compose journeys. All five original JVM methods remain
byte-identical (SHA-256
`c122635108cc1811394659842a679871129599ba2337cc8ed2f0d7ca75b247e8`).

```text
gradlew.bat --offline --no-daemon --console=plain --rerun-tasks :app:testDebugUnitTest :app:compileDebugAndroidTestKotlin :app:lintDebug -x :app:buildRustAndroid
```

The actual full gate passes in 75.433 seconds:

- **420 JVM cases / 49 XML suites**, zero failures, errors or skips. Unique case
  identities, all five original regression identities and report copy bytes
  were checked.
- Production and Android tests compile. Public bytecode declarations for both
  new Compose methods were inspected and retained.
- Lint passes: zero errors, one existing `GradleDependency` warning and one
  `AutoboxingStateCreation` hint. The existing `FrameworkInterruptionTest`
  AtomicReference/Boolean compiler warning remains.
- The four implementation/test source hashes match the tested commit; original
  regression source bytes and three preexisting ignored Rust metadata bindings
  remain unchanged. Whitespace checks pass.

The native task was explicitly excluded. No Rust/JNI build, APK packaging,
Android execution, phone, model, TalkBack or performance result follows.
Independent final-source review found no concrete additional issue and ran no
test or device operation.

## Compiled journeys and remaining gates

Both methods are in `org.locallore.app.ui.StoryHeadingScreenTest` and remain
**UNRUN**:

| Method | Intended Android check |
| --- | --- |
| `selectedAuthoredTitlesStayInsideTheIntroWhileDemoAndUnresolvedControlsRemainExact` | A selected second saved story, Unicode/title/branch changes, saved starter, demo and unresolved controls have exact introduction-scoped text/semantics; accepted narration with legitimate starter names survives |
| `titleRefreshRetainsDialogueButStoryAndBranchChangesFenceDraftsAndRetainedEdits` | Same-scope title refresh preserves unsent dialogue/kind; story or branch changes fence drafts and retained SetText/Send actions; callbacks remain quiet and accepted messages remain unchanged |

These use the real screen with inert SCRIPTED snapshots. They do not qualify
native authored-story creation, actual model behavior or complete user journeys.
Rendered accessibility, physical-device behavior and full M09 acceptance remain
separate. Frozen PR #317 APKs and #318/#319's prepared six-method SDK10 operation
do not contain this change or these two methods. That pending exact proposal
cannot silently be expanded to test this source.

## Preservation and handoff

The reused checkout's old `de72af76` branch, tracked-source ZIP and three ignored
Rust metadata files remain. A separate writer owned only the four source/test
paths; Root integrated this report and README after writer closure. Independent
reviewers used separate checkouts and did not modify the implementation.

Private controls are retained at
`D:/Dev/Experiments/LocalLore/2026-11-01-story-heading-v1` (16 MiB budget).
Selected source/evidence recovery is retained at
`D:/Dev/Recovery/LocalLore/2026-11-01-story-heading-v1` (64 MiB budget), including
both canonical Git source and exact raw working-tree bytes. Raw captures are
not uploaded. GitHub ticket handoff records the final seal and verification.

No guest, ledger, model, phone, ADB, system-setting, unrelated emulator or merge
operation was performed for this packet. Current frozen prerequisites and
pending exact operation are preserved. Next dependent runtime task is the
already prepared SDK10 cohort after its separate exact approval; these new
two methods require their own source-bound qualification. Full task checkboxes
remain unchecked pending their actual gates and owner acceptance.
