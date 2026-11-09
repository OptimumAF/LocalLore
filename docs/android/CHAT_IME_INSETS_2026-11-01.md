# Chat keyboard insets — 2026-11-01

Refs #13 (M09.05, supporting M09.03/M09.06). This bounded source fix is in
review. Full task criteria, Android behavior and owner acceptance remain open.
Base: current `main`, `c09380d6d9ad9fd3947405355ed5b9a058300acf`.

## Source gap and correction

`MainActivity` enables edge-to-edge drawing. The chat applied Scaffold's
system-bar padding without consuming it or applying keyboard (IME) insets.
Its composer and Send control share the scrolling list, and Latest is pinned
below that list. Both need the keyboard boundary handled by their common parent.
This is a source-derived gap; no rendered baseline failure was measured here.

The activity now declares `android:windowSoftInputMode="adjustResize"`.
The common content Box applies
`padding(safePadding).consumeWindowInsets(safePadding).imePadding()`.
Consuming the already applied Scaffold padding prevents adding the navigation
bar twice when keyboard padding is applied. The list and Latest share the
remaining keyboard space. This follows Android's
[edge-to-edge setup](https://developer.android.com/develop/ui/compose/system/setup-e2e),
[inset consumption](https://developer.android.com/develop/ui/compose/system/insets-ui)
and [Scaffold guidance](https://developer.android.com/develop/ui/compose/system/material-insets).

The setting is local to the app Activity; no device setting changes. No new
dependency, model/runtime choice, draft/follow policy, engine/FFI/schema,
canonical state or inference behavior is introduced. Existing compile/target
SDK36 and minSdk26 stay unchanged. Frozen PR #317/#318/#319 sources, APKs,
helpers and pending run proposals remain separate and untouched.

## Original compiled regressions

New class: `org.locallore.app.ui.ChatImeInsetsTest`, scoped to API30+ using
`@SdkSuppress`. It renders the actual screen with inert accepted snapshots,
quiet callbacks and a nested ComposeView. A small original FrameLayout retains
injected native inset values so a later system inset request cannot replace
them. The fixture strategy was checked against
[AndroidX's inset tests](https://android.googlesource.com/platform/frameworks/support/+/ffbddbd1295b99a57b395a5dcfb86af31f451492/compose/foundation/foundation-layout/src/androidInstrumentedTest/kotlin/androidx/compose/foundation/layout/WindowInsetsPaddingTest.kt).

| Method | Compiled acceptance checks |
| --- | --- |
| `injectedImeKeepsLatestAboveOcclusionWithoutDoublePaddingSystemBars` | Latest bottom equals content height minus max(navigation, IME), list top respects status inset, opening changes geometry and closing restores it; callbacks and snapshot stay quiet |
| `doubleFontComposerKeepsSendReachableAndDraftScopedAcrossInjectedImeChanges` | At doubled font, Send scrolls fully above the injected occlusion without clipping; unsent Unicode dialogue/kind survives opening/closing; changing branch rejects a retained old-branch edit and clears its draft |

Both methods compiled and their public bytecode declarations were inspected.
**Neither ran on Android.** The fixture explicitly uses a test Activity with
ADJUST_NOTHING and injects insets; it does not show or measure a real keyboard.
Actual MainActivity behavior, focus/IME animation, TalkBack, broad gesture
conservation and physical-phone accessibility remain unverified. The first
method establishes its initial history position but does not assert full
viewport conservation after every inset change.

## Actual host checks and preserved failure

Physical working directory:
`D:/Dev/Projects/The Hero's Journey/LocalLore-diagnostic-review/apps/android`.
Process-local TEMP/TMP/TMPDIR were `D:/Dev/_Temp`; existing Gradle cache was
`D:/Dev/Tools/Caches/Gradle`. Installed JDK21.0.4 and Android SDK stayed in place.
Gradle8.11.1, AGP8.10.1, Kotlin2.2.21, Compose BOM2025.05.01 were unchanged.
All commands used `--offline --no-daemon --console=plain --rerun-tasks`.

| Invocation | Actual result |
| --- | --- |
| `gradlew.bat :app:testDebugUnitTest :app:compileDebugAndroidTestKotlin :app:lintDebug -x :app:buildRustAndroid` | 411 JVM tests/47 XML suites pass, zero failures/errors/skips; production and Android tests compile; overall command fails lint, 59.114s |
| `gradlew.bat :app:compileDebugAndroidTestKotlin :app:lintDebug -x :app:buildRustAndroid` | Pass, 49.529s, after the test-only annotation correction |
| Merged main manifest inspection | MainActivity has `adjustResize` |
| Final lint | Zero errors, one existing GradleDependency warning and one AutoboxingStateCreation hint |
| Final source/whitespace checks | Pass; production bytes unchanged across both commands |

The first real failure was lint's `UseSdkSuppress` error: the test redundantly
declared `@RequiresApi(30)` alongside `@SdkSuppress(minSdkVersion = 30)`.
Only the redundant import/annotation were removed. The runtime API floor and
all test assertions remain; no lint baseline, rule suppression or boundary
relaxation was added. The original source at `112b30ae07b4fa73d94df4bf40075581a6626e66`,
first log and lint XML remain preserved. An existing AtomicReference/Boolean
compiler warning in FrameworkInterruptionTest was unchanged.

JVM cases actually ran against the final production implementation in the first
invocation. They were not rerun for the test-only annotation correction. The
second invocation freshly recompiled the production/Android-test code and lint.
All47 JUnit reports have byte-identical local copies and unique case identities.
Independent source review found no additional concrete blocker; it ran no tests
and does not provide runtime evidence or owner acceptance.

The native build task was explicitly excluded in these UI-only checks. No Rust
library, JNI integration, APK packaging or Android execution is qualified by
this packet. No device/emulator/ADB operation, model transfer/inference, runtime
process/port census, ledger mutation, retirement, boot or merge occurred.

## Preservation and next gate

Old branch/source3cdd3cc5 and46 ignored files were verified and preserved before
reusing the clean checkout. Source/test implementation used an independent
writer; Root integrated the annotation correction and documentation after its
writes closed. Separate agents reviewed source and acceptance limits.

Evidence lives at
`D:/Dev/Experiments/LocalLore/2026-11-01-chat-accessibility-v1` (16MiB limit).
Generated build output has a separate4GiB limit; selected source/evidence
recovery has a separate64MiB limit. All originals and failed captures remain.

The current pending SDK10 proposal covers six tests against its frozen PR #317
build. It does not authorize this new source or the two keyboard tests. Next
runtime step remains the already prepared SDK10 run after applicable approval;
this keyboard fix needs its own later Android qualification. No additional
emulator approval is requested by this packet.

A separate M09.05 finding about lazy-list status announcements is recorded in
ticket #13 for follow-up. It is outside this keyboard edit. Full accessibility,
phone/model/ARM64, lifecycle and release acceptance remain separate gates.
