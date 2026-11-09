# Current chat APK verification — 2026-11-01

Refs #14 (M10.02/M10.03), supporting #13 (M09.03/M09.05/M09.06).
This build/artifact packet is in review; full milestone criteria remain open.
Tested source is PR #325 at `fcf92fa30628a925da4138a8d68dd6aeef204fde`, retaining
the #320 keyboard, #322 status, #323 heading and #325 quick-action fixes.
No production source changed in this packet.

## Actual build

An inactive clean physical checkout at
`D:/Dev/Projects/The Hero's Journey/LocalLore-issue-tracking` was reused on
`verify/m10-current-chat-apks-v1`. Its old `efd195d4` branch and source ZIP remain;
there were no ignored or untracked files before reuse. The app build directory
was absent. A canonical source ZIP and all 2,540 tracked raw file bindings were
captured before dispatch and verified unchanged after the gate and DEX reader.
There were no EOL-only differences.

```text
python -I -S -B scripts/check.py android --offline
```

The existing gate verifies the wrapper, directly invokes its Java entry point,
builds both ordinary APKs, runs JVM tests/lint, then runs the product and paired
instrumentation audits. No clean, install or connected-test command was used.
Native compilation was included; no `-x :app:buildRustAndroid` exclusion occurred.

Process-local TEMP/TMP/TMPDIR used `D:/Dev/_Temp`; Gradle used the existing
`D:/Dev/Tools/Caches/Gradle`, Cargo the existing
`D:/Dev/Tools/Caches/Cargo-LocalLore-v1`. Gradle build cache and automatic Java
toolchain installation were disabled for this process; the gate explicitly
disables SDK downloads and passes offline mode to Gradle and locked Cargo.
The existing cached wrapper distribution was used. Global settings and tool
installations were preserved; no new runtime, model or dependency was selected.

Actual tool receipts confirm JDK21.0.4+8, Rust/Cargo1.93.1, Android SDK36 revision2,
Build Tools35.0.0, NDK29.0.14206865 and cached Gradle8.11.1. Existing AGP8.10.1,
Kotlin2.2.21, Compose BOM2025.05.01 and minSdk26 remain unchanged.

The first actual gate passes in **117.2967263 seconds**:

- **81 actionable tasks / 81 executed**, with no FROM-CACHE result. Required
  native, compilation, assembly, test, lint, merge and strip task headings are
  bare executed tasks. Empty assets/NO-SOURCE/SKIPPED entries remain distinguished.
- Fresh Rust release builds complete for x86_64 in30.17s and arm64-v8a in27.87s.
  These are compiler times, not application or model performance.
- **428 unique JVM cases / 50 XML suites**, zero failures, errors or skips.
- Lint passes with zero errors, one existing GradleDependency warning and one
  AutoboxingStateCreation hint. The inherited FrameworkInterruptionTest
  AtomicReference/Boolean compiler warning remains.
- Both actual product and ordinary paired-instrumentation audits pass.

## Exact artifacts and native joins

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `app-debug.apk` | 28,012,688 | `a25ab00c458ed5f531935a5dcad17dd8d667fe9ed3e32059a33d77671f063591` |
| `app-debug-androidTest.apk` | 2,308,386 | `e6acd6ec10960f0861ce3588864ec74eb44a8b468b38a750f76cc96709cfc1a3` |

Original paths are under `apps/android/app/build/outputs/apk/debug/` and
`apps/android/app/build/outputs/apk/androidTest/debug/` respectively. Exact private
copies are retained with the packet. Product package is `org.locallore.app`;
test package is `org.locallore.app.test`, using AndroidJUnitRunner.
The common debug certificate matches expected SHA-256
`17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564`.
No signing key was copied or published.

The product audit checks the manifest/backup policy and permits only the
existing app-specific receiver permission. The test audit records REORDER_TASKS.
All four packaged libraries (Rust JNI and AndroidX graphics path for both ABIs)
pass uncompressed ZIP/local-header and ELF LOAD alignment checks at16KiB.
This is static artifact policy evidence, not observed network traffic or full
privacy qualification.

For each Rust ABI, original release bytes equal generated JNI bytes and merged
native-library bytes. Stripped output equals the corresponding APK member.
Stripping changes bytes; equality across that transformation is not claimed.
Paths, sizes and hashes for every stage are retained. Fresh cross-build and
packaging do not prove ARM64 or JNI execution on a device.

## Defined UI methods, not just references

The pair audit verifies packages, manifests and signatures; it does not prove
that the eight new UI methods are packaged. A separate closed-file reader uses
the existing bounded `Dex` / `dex_classes()` implementation in
`scripts/audit_physical_model_apk.py`. It checks actual definitions across DEX
files, unique class/method ownership, public concrete classes and exactly two
JUnit-annotated methods per expected class. Each test is public, nonstatic,
nonabstract, nonnative, void and zero-argument. Source rosters match. All four
class families, including nested definitions, are absent from the product APK.
The reader attempts no child-process or socket operation.

All classes below are in `org.locallore.app.ui`:

| Class | Exact method definitions |
| --- | --- |
| `ChatImeInsetsTest` | `injectedImeKeepsLatestAboveOcclusionWithoutDoublePaddingSystemBars`; `doubleFontComposerKeepsSendReachableAndDraftScopedAcrossInjectedImeChanges` |
| `ChatStatusAnnouncementTest` | `historyReaderKeepsItsAnchorWhileCurrentBusyAndOutcomeAnnouncementsStayAvailable`; `unicodeDialogueAndScopeStaySafeWhileEllipsizedNoticeKeepsFullSemantics` |
| `StoryHeadingScreenTest` | `selectedAuthoredTitlesStayInsideTheIntroWhileDemoAndUnresolvedControlsRemainExact`; `titleRefreshRetainsDialogueButStoryAndBranchChangesFenceDraftsAndRetainedEdits` |
| `QuickActionScopeScreenTest` | `retainedStoryAndBranchClicksStayQuietWhileFreshControlsPreserveTheUnsentDialogue`; `persistentDemoAndWorkflowFencesDoNotTurnTextUnavailabilityIntoAnActionBlock` |

**All eight remain UNRUN on Android.** IME tests require API30+ and inject insets
under ComponentActivity/ADJUST_NOTHING; they do not prove actual keyboard or
MainActivity window behavior. Status semantics do not establish TalkBack speech.
Heading/action fixtures use inert snapshots and callback spies, not native
authoring or accepted mechanics. DEX presence is not a complete DEX verifier or
test execution result.

## Independent review, preservation and remaining gates

Separate reviewers inspect native/build policy and the source/DEX artifact
boundary. Independent closed-file review verifies original/copy APKs, source ZIP
and all 2,540 source bindings, original audit JSON/command records, report counts,
native joins, alignment and expected certificate result. No build/audit CLI or
product test was rerun by the reviewers. A reader-only CRLF task-regex setup
error is retained; splitlines/fullmatch corrects the reader while preserving the
bare-task invariant, without changing source, assertions or original outputs.

Original inner AAPT/apksigner raw stdout is not retained by the standard gate;
its actual audit results and policy source are retained. This is not a complete
supervised pipeline or SDK admission manifest. The standard gate has no overall
deadline/output meter; actual capture and generated bytes are recorded against
the declared budgets. No stronger cleanup or raw-transcript replay proof is
inferred from successful build exit.

Controls, selected APK copies and receipts remain at
`D:/Dev/Experiments/LocalLore/2026-11-01-current-chat-apks-v1` (64MiB budget).
Selected source/evidence recovery is at
`D:/Dev/Recovery/LocalLore/2026-11-01-current-chat-apks-v1` (128MiB budget).
Generated build output is about644MB, below the4GiB budget, and is retained.
Exact final seals and claim release are recorded on the linked tickets.
Raw private captures and APKs are not uploaded to the public repository.

These packages exclude sibling PR #317's rolling-window fix. They are different
from the frozen PR #317 APK pair used by pending SDK10 through #318/#319. No
existing source binding, proposal, six-method cohort, ledger or guest was
repointed. Current-source Android qualification needs its own reviewed binding
and applicable exact approval. Physical-phone/model, native/ARM64 execution,
accessibility, process-death, observed-traffic and full journey gates remain open.

No emulator, retirement, admission/prepare, device/USB/ADB census, phone, model,
system-setting, other-emulator/shared-service, new approval request or merge
operation occurred. Full task checkboxes remain unchecked. The next runnable
host step is a source-bound qualification cohort for the current UI fixes;
runtime execution stays behind the existing exact-operation authority rules.
