# Quick-action story and branch fencing — 2026-11-01

Refs #13 (M09.03, supporting M09.06) and #14 (M10.02). This slice is in review;
full task acceptance remains open. It is stacked on PR #323 at
`e19f6b3c4c0d1a365d91c6b3fe9dbaacac36b7a8`, retaining that saved-story heading
fix and its status/keyboard prerequisites.

## Routing defect and boundary

The two quick buttons previously called `onAction(DemoAction)` without a target.
`MainActivity` forwarded the unscoped `model::submit`. If an old callback from
story A was invoked after a settled switch to compatible story B or a different
branch, the ViewModel read B's current state. `DurableGateway` then built a
request using its current scope and that current revision. Native validation
correctly checked B; the request carried no record of A's rendered target.

This is an input-routing gap. The [architecture](../ARCHITECTURE.md) and
[domain contract](../DOMAIN_CONTRACT_V1.md) retain engine validation and accepted
events as authority. The fix adds UI admission fences without accepting any
gameplay effect in Kotlin:

- `MainActivity` stores a plain `renderedActionStory` value during composition
  and captures it in the callback. Reading the delegated Compose `state` inside
  the click lambda would read the latest selection and recreate the gap.
- The new `submit(DemoAction, expectedStory)` entry point compares logical story
  and branch IDs, including null/saved mismatches, before any state or gateway
  work. It then delegates to the original submission path, preserving busy,
  workflow, recovery, disposal, generation and native validation fences.
- Only the two button controllers are keyed by persistence mode and logical
  scope. Their retained callbacks also read current scope and blocking flags.
  This prevents a retained Material controller from being retargeted to a new
  rendered callback during recomposition.

The scope policy matches typed-text submission. A different object, title or
head on the same story/branch remains usable; the submission reads the current
revision and the engine still validates it. This does not promise head-specific
consent. Direct programmatic `submit(DemoAction)` calls retain current-selection
behavior; production rendered buttons use the scoped entry point.

Existing action availability is unchanged: busy, archive, deletion, fork,
creation, recovery and unresolved persistent selection block quick actions.
Text-provider unavailability does not block these typed demo commands. The
screen does not reuse the stricter text-editor gate. Button labels, commands,
outer lazy item keys/counts/order, drafts, scroll policy and accepted history
remain. No FFI, native protocol, schema, provider, dependency or engine change
was introduced.

The commands still refer to the original potion/Mira and blink demo. Providing
generic authored-world quick actions requires a separate authoritative contract;
this fix does not derive actor or item IDs from names. Native validation owns
rejection or acceptance of every submitted command.

## Original regression and actual checks

Physical checkout:
`D:/Dev/Projects/The Hero's Journey/LocalLore-compose-ui`, branch
`fix/m09-quick-action-scope-v1`. Commands ran from `apps/android`, with
process-local TEMP/TMP/TMPDIR at `D:/Dev/_Temp` and the existing Gradle cache at
`D:/Dev/Tools/Caches/Gradle`. Installed JDK21.0.4, Gradle8.11.1, AGP8.10.1,
Kotlin2.2.21, Compose BOM2025.05.01 and SDK locations were unchanged.

Baseline commit `1c5c03b902417131be713c7986aebafd3554cfcb` adds a
behavior-preserving scoped overload that ignores its expected target and
delegates to the old route. MainActivity captures the rendered value and calls
that overload. Independent review and exact reverse-source checks verify the
baseline preserves the old behavior. No screen guard was added before FIRST.

```text
gradlew.bat --offline --no-daemon --console=plain --rerun-tasks :app:testDebugUnitTest --tests org.locallore.app.QuickActionScopeShellTest -x :app:buildRustAndroid
```

Actual FIRST: **8 methods, 4 assertion failures, zero errors/skips**, 44.507
seconds. Wrong-story/same-head, wrong-branch/same-head, null-to-saved and
saved-to-null callbacks unexpectedly reach the gateway. Four valid-call and
ownership controls pass. Original source, XML, log and terminal receipt remain.
This is real ViewModel execution with synthetic gateway-owned histories, not
Rust mechanics or an observed Android failure. Both action types are counted
at dispatch: a real unlearned-ability rejection must not hide wrong-scope work.

Implementation commit `b713d87498003ca6349e606bce8a0974bb229835` adds the
guards and two Compose journeys. The original eight-method test source is
byte-identical, SHA-256
`af7f3e82551db7b9aeddbd03d7cc81f961334457503a59346146fbf6f00075ce`.

```text
gradlew.bat --offline --no-daemon --console=plain --rerun-tasks :app:testDebugUnitTest :app:compileDebugAndroidTestKotlin :app:lintDebug -x :app:buildRustAndroid
```

Actual full gate passes in **68.380 seconds**:

- **428 unique JVM cases / 50 XML suites**, zero failures, errors or skips.
  All eight FIRST case identities, original oracle bytes, tested source hashes
  and report copy bytes were checked.
- Production and Android tests compile. Both new Compose public method
  declarations were inspected in actual class bytecode and retained.
- Lint: zero errors, one existing `GradleDependency` warning and one
  `AutoboxingStateCreation` hint. The existing `FrameworkInterruptionTest`
  AtomicReference/Boolean compiler warning remains.
- Whitespace checks pass. Independent actual final-source review found no
  concrete additional blocker and performed no test or device operation.

The eight methods cover quiet stale-target rejection with zero gateway calls,
commits and state/history changes; current actions with text unavailable;
same-scope copied/title/head refresh using the current revision; demo-null and
direct-call controls; busy, recovery, unresolved and disposed ownership.
The synthetic gateway can accept a compatible command to expose routing; this
does not change or qualify native ability/inventory rules.

The native task was explicitly excluded. No Rust/JNI build, APK packaging,
Android execution, native authored-world, phone, model, accessibility or
performance qualification follows from this gate.

## Compiled Android journeys and remaining gates

Both methods in `org.locallore.app.ui.QuickActionScopeScreenTest` remain
**UNRUN**:

| Method | Intended Android check |
| --- | --- |
| `retainedStoryAndBranchClicksStayQuietWhileFreshControlsPreserveTheUnsentDialogue` | Capture actual enabled OnClick actions from both buttons; old story/main-branch actions stay quiet after selection changes while fresh buttons work; unsent Unicode dialogue/kind and accepted history remain |
| `persistentDemoAndWorkflowFencesDoNotTurnTextUnavailabilityIntoAnActionBlock` | Previously enabled callbacks stay quiet under six blocking flags, unresolved selection and saved/demo transitions; fresh demo/current saved actions work with text unavailable |

These use the actual screen with inert SCRIPTED snapshots and callback spies.
They do not simulate native acceptance or complete the production lifecycle
journey. Real rendering/controller behavior, current-source JNI execution,
accessibility, process death, phone/model and full milestone gates remain open.

The pending SDK10 operation through PR #318/#319 targets the frozen PR #317 APKs
and six other methods. It cannot silently be expanded or treated as evidence
for this change, PR #320 keyboard journeys, PR #322 status journeys or PR #323
heading journeys. Their source-bound Android qualification remains separate.

## Preservation and handoff

The reused checkout's old `16250dac` branch and source ZIP remain. It had no
ignored/untracked project files before reuse. One separate writer owned only
the five source/test paths; Root integrated this report and README after all
writes closed. Reviewers used separate checkouts and made no source changes.

Private controls:
`D:/Dev/Experiments/LocalLore/2026-11-01-action-scope-v1` (16 MiB budget).
Selected source/evidence recovery:
`D:/Dev/Recovery/LocalLore/2026-11-01-action-scope-v1` (64 MiB budget), preserving
canonical Git source, exact raw bytes and the original failing evidence.
Final seals and claim release are recorded on the linked tickets. Raw private
captures are not uploaded; generated build output remains in the D: checkout.

No guest, ledger, approval, phone, ADB, model, system-setting, unrelated emulator,
shared-service or merge operation occurred. Frozen prerequisites and existing
pending exact proposals remain unchanged. Full checkboxes stay unchecked;
the prepared SDK10 cohort still needs its existing exact approval, and these
two new methods need separately source-bound Android qualification.
