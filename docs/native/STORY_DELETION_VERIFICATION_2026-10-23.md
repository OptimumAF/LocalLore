# Whole-story deletion verification — 2026-10-23

Refs #12 (M08.05). Locally verified, pending owner acceptance; full M08.05 remains
unchecked. This packet is stacked on PR80, base `dfb2aa2`, and merges nothing.
The [contract](STORY_DELETION_CONTRACT.md) defines the exact boundary;
[sanitized results](STORY_DELETION_RESULTS_2026-10-23.json) bind source, code hashes,
APKs, all actual device attempts and limits. Private logs remain local.

## Implemented scope

The shared Store prepares a root-scoped, all-timeline deletion preview and
consumes its opaque confirmation in an atomic SQLite transaction. A retained
distinct read-only observer detects intervening commits, including identical
delete/reimport ABA. All nine story-scoped tables are checked and removed;
unrelated story canon, workflow, caches and knowledge remain isolated. There is
no schema migration, new dependency or model integration.

Two JNI calls reuse the archive registry's owner/token/cancel/close lifecycle.
A native workspace mutation gate covers deletion plus matching-session
invalidation, preventing old Ready turns and cached committed replies from
crossing into an explicitly reimported story. Kotlin renders the native preview,
binds consent to that exact rendered object, drains work on cancel/close, and
always reconciles the library. The actual product factory and empty-library
screen require explicit New story; last-story deletion survives owner/Activity
recreation without silently making a replacement.

Whole-story deletion removes every timeline together. Branch-only deletion with
retained descendants remains unimplemented; no parent branch can be deleted
through this UI. Logical deletion does not remove external exports/backups,
shared models, separately captured UI/archive buffers, or forensic remnants.
The app-private database/ancestors must not be replaced while Stores are open.

## Exact validation

Executable/test source: `4dc5c1e`; native implementation `1e4f236`, public native
regressions `f62338e`. Later changes are documentation/evidence only.

| Check | Actual result |
|---|---|
| `python scripts/check.py host --offline` | 327 Rust workspace tests + 3 linker tests + 232 Python tests; fmt, strict Clippy, four generated fixture cases passed |
| Eight new Store tests | All nine tables, four timelines, every workflow status, genuine derived packets, retained four-timeline control/canon/knowledge/cache parity, foreign plans, real Busy, all observed cancellation checkpoints, same-Store and delete/reimport ABA, reopen/reimport |
| Five new public native tests | Root/child Ready and cached receipts across owners invalidated; same-ID reimport/new identical draft cannot reuse old owner; other-story/same-ID other-DB sessions survive; owner/kind/single-use/replacement tokens; failed/stale delete retains sessions; gate wait/cancel/close/draining-owner limit |
| Dedicated Android build | Both ABIs; 72 JVM tests, zero failure/error/skip; lint passed; final build 79 tasks, 10 executed/69 up-to-date |
| Ordinary `python scripts/check.py android --offline` | Passed; fresh 72 JVM tests, lint; 78 tasks, 26 executed/52 up-to-date |
| APK audit | Both ELF/ZIP 16 KiB alignment; exactly nine archive JNI symbols, no capacity fixture/MAX_PAGE_COUNT=96, no INTERNET permission/test provider in app |
| Build isolation | Six negative configuration/release guards rejected as expected; ten nonordinary local APK files unchanged by ordinary build |
| Final APK device cohort | 35 passes on each of two API35/x86_64 emulators: 9 deletion/recovery + 26 archive/durability; zero failed/skipped/unfinished |

The 9-test cohort includes the actual ComponentActivity Compose/native journey
on a fresh synthetic private root (cancel preserves exact archive, three-timeline
fixture deleted, retained spent-potion transcript/revision preserved, last empty
reopen/explicit Create), actual MainActivity factory/overlay/Activity recreation,
and seven Android JSONObject recovery protocol cases. The 26 regressions include
actual native durability/cancellation/recovery, system-chooser import/export,
archive documents, dialogs, and read-only Activity cancellation checks. All four
archive and workspace owner slots are reacquired after deletion-journey disposal.

Environment: Rust1.93.1, Java17.0.6, Gradle8.11.1, AGP8.10.1, Kotlin2.2.21,
compile/target SDK36, NDK29.0.14206865. Two selected Android15/API35 x86_64
emulators executed; ARM64 was built/packaged only. Fresh final inventory showed
four emulators and zero physical phones. No model generation/phone performance
measurement is claimed.

Final dedicated app SHA256:
`5bc796b6ec25d7d3a40915c0965e7e03473a532760314766e1b2b42210df4319`.
Final test APK:
`3181eea3396d4378b9250c9896e9dccc4823695c86536745e18d6e5a0fb8063b`.
Both were verified installed on both targets. The ordinary build's native
libraries equal the dedicated app's libraries byte-for-byte. The ordinary APK
was audited, not installed over the user's existing demo.

## Reproduce safely

Run host/ordinary checks above with the documented toolchains. For an isolated
debug test app, from `apps/android`, run the verified Gradle wrapper JAR:

```powershell
java -classpath gradle/wrapper/gradle-wrapper.jar org.gradle.wrapper.GradleWrapperMain :app:assembleDebug :app:assembleDebugAndroidTest :app:cleanTestDebugUnitTest :app:testDebugUnitTest :app:lintDebug -PlocalLoreStoryDeletionVerification=true --project-cache-dir .gradle-story-deletion --offline --no-daemon -Pandroid.builder.sdkDownload=false
```

Outputs are in `app/build-story-deletion`; application ID is
`org.locallore.app.storydelete`, with a separate test package. Never substitute
the user's production package or clear existing saves. Install only the reviewed
pair on explicitly selected test emulators. The MainActivity case requires an
empty dedicated package's initial library and leaves one fresh synthetic story
for subsequent read-only archive regression tests. Other new tests create fresh
private synthetic roots and retain them. No uninstall/data-clear is required by
this packet. Select these classes with AndroidJUnitRunner:

- `StoryDeletionActivityTest`, `DurableDeletionRecoveryTest`,
  `StoryDeletionMainActivityTest` (9 tests).
- `ArchiveIntegrationTest`, `ArchiveDocumentTest`, `ArchiveDialogTest`,
  `DurableNativeTest`, `ArchiveActivityTest`, `ArchiveChooserActivityTest`
  (26 tests; five are in DurableNativeTest).

Use their fully qualified `org.locallore.app` class names and the dedicated
test package. Raw start/end method pairs and the terminal runner result must
all agree; a process exit code alone is not evidence of passing tests.

## Attempts and limits retained

All actual device attempts passed: initial A8 on the superseded test APK
`82f9cb4c…`, then final A9/B9 and regression A26/B26: **78 actual passes**, of
which **70** use the final pair. B never ran the superseded test APK. Both
regression collectors originally expected24 by miscounting DurableNativeTest;
original failed collector reports remain. Strict reparse of the actual complete
26-test raws verified all ordered start/end pairs and terminal OK; no device
rerun or invented product failure. All five attempts' client/process cleanup and
all nine prior installed package hashes were checked. Only the owned dedicated
pair was installed/stopped; no prior package was uninstalled, stopped or cleared.

Initial host linking and dedicated build failed when C: actually filled:
LNK1318 and mergeNative/dex errors. Task-generated `target/debug` was moved
intact to a task-owned D: directory, preserving its original path through a
junction; no user files or caches were deleted. Builds then passed. Initial
strict Clippy found a large capability enum, corrected by boxing the plan before
final builds. Native author tests initially had4pass/1failure, followed by two
targeted diagnostic failures; these exposed a test's forbidden child-scope
preview assumption, corrected to root scope with an explicit child rejection.
Final5/5 and strict Clippy passed. The first negative-guard collector checked a
reversed error phrase; the already-correct rejection log was reparsed before the
other five guards ran. A reviewer report write was interrupted by real host
disk exhaustion. A later false unresolved UTF-8 report came from Windows'
default cp1252 decoding; explicit UTF-8 raw-blob comparison confirmed the fix.

No injected accepted-delete/running-prepare schedule or cancellation deliberately
after SQLite's commit is claimed. Ready/recreated-draft races, waiting-gate
cancellation, controller noncooperation/disposal and uncertain-ack reconciliation
are the tested schedules. Cross-process captured memory, standalone desktop
deletion UI, physical-phone/real-model gates and full M08 acceptance remain
pending. Owner review/merge is required; hosted CI is reported separately.
