# Android player story record — 2026-10-23

Refs #10 (bounded M06.06, displaying existing M06.01/M06.03/M06.04 fields), #7
(M03.02/M03.03 integration), and roadmap #3. Base: `ac7fe2c`. Executable source:
`65dae1a`. This packet adds an Android reader over the accepted shared inspection API.
It does not complete the M06 milestone or change its acceptance criteria.

## Implemented boundary

The saved-story shell offers Progression, History, Relationships and Knowledge.
`DurableGateway` sends Host-v1 `inspection_query` with a fixed player observer,
selected story/branch and expected current head. The Rust engine applies visibility
before search, counts and pagination. Kotlin renders accepted typed rows; it never
submits gameplay, supplies an observer grant, repairs storage or invokes inference
while browsing. Canonical facts, recorded statements, subjective beliefs,
discoveries, observations and messages retain distinct origin labels.

Pages contain at most eight rows, literal search is at most 256 UTF-8 bytes without
control characters, and decoded pages are at most 65,536 UTF-8 bytes. The adapter
checks scope/head/revision, player privacy, view, known row/origin combinations,
typed values, source bounds, event scope/time, cursor structure/offset continuity,
counts and duplicate keys. This is selected-field and known-variant validation;
it is not another domain engine or a complete independent JSON-schema validator.
Only the Rust engine validates cursor query binding. Error text is a fixed enum;
raw replies, exception strings and private diagnostics do not reach the dialog.

The controller retains page count/clock boundaries across later-page failures and
retries. It clears visible rows on a new load, and generation/disposal fences
discard noncooperative late completions. Closing, starting a turn, switching saves,
recovering, resetting, foreground loss via the existing `onStop` callback, and
disposal dismiss the reader. Dismissal does not call gameplay cancellation. An
already executing native IO read may complete; dismissal prevents publication.

## Reproduce

Use the repository's existing pinned environment: Rust 1.93.1, JDK 17, NDK
29.0.14206865, Gradle 8.11.1, AGP 8.10.1, Kotlin 2.2.21, compile/target SDK 36,
minimum SDK 26. No runtime/model/SDK/native dependency or permission was added.

From the repository root:

```powershell
python scripts/check.py host --offline
```

From `apps/android`, with `JAVA_HOME` and `ANDROID_HOME` configured:

```powershell
.\gradlew.bat :app:cleanTestDebugUnitTest :app:testDebugUnitTest :app:assembleDebug :app:assembleDebugAndroidTest :app:lintDebug --offline --no-daemon
```

On an authorized emulator, install only when the package is absent, or update a
known matching test build while preserving its data. Select the exact serial;
never use a blanket connected-device task against unrelated running emulators.
The selected instrumentation cohort is:

```text
am instrument -w -r -e class org.locallore.app.StoryRecordInstrumentedTest,org.locallore.app.StoryRecordScreenTest org.locallore.app.test/androidx.test.runner.AndroidJUnitRunner
```

Require all four named start/terminal pairs and the final successful runner code;
ADB exit zero alone is insufficient. Native fixtures use newly allocated synthetic
no-backup roots. They clear owned ViewModel stores, close transports, drain pending
reads and reacquire/release all four native handle slots before deleting only their
owned root. Uncertain ownership poisons cleanup and retains the fixture. Existing
default saves and unrelated packages are never reset or cleared.

## Evidence and limits

Exact aggregates, build identities and every execution cohort are in
[the sanitized results](ANDROID_RECORD_RESULTS_2026-10-23.json).
[Independent review](ANDROID_RECORD_REVIEW_2026-10-23.md) distinguishes source,
JVM, actual JNI and Compose evidence. Raw logs, emulator identifiers, local paths
and temporary databases remain private build artifacts.

The full host command initially failed the existing storage migration timing test:
it returned `Busy` where `FutureVersion` was expected after waiting for a writer.
The exact targeted test passed, then the same full host command passed. No storage
source or timeout was changed; this observation is retained rather than omitted.
Two early emulator preflight attempts failed an overly broad process-absence
guard on pre-existing packages, before installation. Their failure attribution
comes from coordinator tool output, not independently retained raw logs. Revised
preflight preserved package hashes without stopping processes owned outside this
packet. Successful cohorts retain strict guards for this packet's own builds.

The four instrumentation methods cover actual Rust pagination, literal no-match
search, unchanged accepted snapshots and inference/turn call counts during reads,
gift-event provenance and strict reopen, observed claims/beliefs/known truth,
hidden NPC canaries and forbidden character/omniscient queries, malformed Android
JSON frames, collected Compose paging/search/section labels/dismissal, accepted
head refresh and terminal ViewModel disposal. JVM tests additionally cover busy
and recovery gates, noncooperative success/failure, cross-story stale reads,
retry coherence and the existing lifecycle callback. That callback test does not
establish a new real framework `onStop` or native cancellation measurement.

Source references are text; there is no event-detail navigation yet. Aliases,
motivations, background and additional relationship dimensions remain unsupported
by the current shared fields. This packet does not implement summaries, NPC or
omniscient play views, alternate branches, complete multi-scene memory, or new
progression rules. Real inference remains a separate gate. Both selected devices
are API 35 x86_64 emulators with 4,096-byte pages; ARM64 was compiled, not executed.
No physical phone was available, and no model quality, phone latency, thermal,
ARM64 execution, hosted CI, process-kill or release qualification is claimed.

M06.06 remains a partial implementation in review, with all milestone checkboxes
unchanged pending owner acceptance. M01.01 physical-device/runtime qualification
remains blocked on an authorized phone. The next bounded M06.06 task is player
navigation from a visible source-event reference to its eligible history detail,
with cross-scene secrecy fixtures, after reconciling current claims on #10.
