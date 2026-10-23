# Player source-event navigation — 2026-10-23

Refs #10 (bounded M06.06), #7 (Android integration) and roadmap #3. This packet
stacks on unmerged [PR #64](https://github.com/OptimumAF/LocalLore/pull/64), base
`ab5416405050634739572866863b1b53c424a071`. It adds working source-history navigation
to that player reader. Full memory, narrative-quality and device gates stay open.
Final executable source: `54847ac`.

## Authority and user flow

Visible records carry typed event-source IDs separately from human source labels.
Only a currently displayed eligible reference can open a detail. Source-like prose,
seed labels, withheld evidence and an arbitrary supplied number grant no access.
The adapter retains the fixed player lens, story/branch and frozen accepted head.

Detail reads reuse Host-v1 `inspection_query` and its existing literal search over
eligible serialized history. The fixed filter is `"sequence":N,`, constructed only
from a validated positive integer. It cannot match a longer numeric sequence or
quoted input/narration text. No SQL or new native endpoint is introduced. Rust
still filters eligibility before search/counts; Kotlin requires exactly one
observed event with matching sequence, scope/head, turn ID and event time, or a
fixed unavailable/error state. Unknown/malformed variants and duplicate event
identities fail closed. A serialization change may safely make lookup unavailable;
Kotlin cannot broaden the query or use a different authority to invent a result.

The detail distinguishes accepted head from event story time and retains origin
labels. A recorded statement or belief proves that it was recorded, not that its
proposition is a world fact. It offers no recursive source lookup or spoiler grant.
Back, including platform Back, restores the exact page, section, search and cursor
without a reread. Explicit Close dismisses everything. Retry remains a detail read;
it does not restart the list or create gameplay. New queries, story/head changes,
gameplay, recovery, dismissal and disposal revoke old read publication. Already
executing native IO may finish; dismissal is a publication fence, not a promise to
interrupt that IO operation.

Rendered source callbacks capture a nondelegated immutable context value. Comparing
that context again at the ViewModel prevents an old rendered click from opening a
same-numbered event in another story, even when the new page independently permits
that event number. Reads never prepare/commit a turn, advance time, or repair saves.
No Rust engine, Host, storage, migration, runtime, dependency or permission changed.

## Reproduce and inspect evidence

The existing toolchain remains Rust 1.93.1, JDK 17, Gradle 8.11.1, AGP 8.10.1,
Kotlin 2.2.21, NDK 29.0.14206865 and compile/target SDK 36 (minimum 26).

From repository root:

```powershell
python scripts/check.py host --offline
```

From `apps/android`, with `JAVA_HOME` and `ANDROID_HOME` configured:

```powershell
.\gradlew.bat :app:cleanTestDebugUnitTest :app:testDebugUnitTest :app:assembleDebug :app:assembleDebugAndroidTest :app:lintDebug --offline --no-daemon
```

With `ANDROID_HOME` configured, from repository root:

```powershell
python scripts/audit_apk.py apps/android/app/build/outputs/apk/debug/app-debug.apk
```

Guard the exact selected emulator and installed APK identities before an update.
Use install-r only for a matching known test build, preserving data. Never clear,
reset, uninstall or operate an unrelated emulator. Select these four classes,
native-only cases before the Compose cases:

```text
am instrument -w -r -e class org.locallore.app.StoryRecordInstrumentedTest,org.locallore.app.EventSourceInstrumentedTest,org.locallore.app.StoryRecordScreenTest,org.locallore.app.EventSourceScreenTest org.locallore.app.test/androidx.test.runner.AndroidJUnitRunner
```

All eight start/terminal pairs and successful runner protocol are required. Fresh
synthetic no-backup roots, bounded owner drain, all-four-handle reacquisition and
owned-root cleanup reuse #64's fixture. Uncertain cleanup retains/poisons that
fixture rather than deleting a root with unconfirmed writers. Default saves are
not opened/reset; prior capacity-test package hashes are preserved. Raw logs,
paths, emulator identifiers and temporary databases remain private.

Exact cohort hashes, counts and retained failures are in
[sanitized results](ANDROID_EVENT_RESULTS_2026-10-23.json).
[Independent review](ANDROID_EVENT_REVIEW_2026-10-23.md) separates source/JVM/actual
JNI/Compose evidence and does not grant owner acceptance.

The final source passed 71 JVM tests, build/lint, APK manifest/ABI/ELF/ZIP audit,
and all eight selected instrumentation methods on each emulator (16 final-source
passes, no failures/skips/unfinished cases). Native build outputs were unchanged
and reused; both ABIs were packaged/audited, not freshly cross-compiled here. The
full host command passed 233 workspace Rust, three linker and 191 Python tests,
plus format/Clippy and fixture/schema checks. Final lint has zero errors and one
existing dependency advisory; a new optional-parameter advisory was corrected.
All seven retained emulator cohorts total 55 passes and the one deliberately
reproduced callback failure, with zero skipped or unfinished methods. The earlier
green cohorts and the negative cohort are not final-source qualification.

## Scope and retained discoveries

The cross-scene fixture gives the potion to Mira, moves to the pier, returns Oren's
brass key and explicitly completes its promise: four events across three receipts.
Movement progression, event/message references and recorded statement/belief
knowledge navigate to exact observed events. Gift witnesses are player/Mira; key
transfer witnesses are player/Oren; promise completion is player-witnessed even
though Oren is a participant. Participants are not silently treated as witnesses.
Browse checks compare accepted snapshots, receipts and submit/prepare/commit counts;
there is no separate provider-call counter. Strict reopen preserves canon.

Current outgoing player relationships are seed-backed. Give changes incoming NPC
obligation evidence, which the player lens intentionally hides. Those visible seed
rows have no link; generic relationship Source::Event decoding is frame-mapping
evidence only. Withheld-source tests use explicit local JSON mutations and do not
claim the engine produced withheld evidence in this scene. Known truth seed sources
remain unlinked. None of this changes M06.03 or M06.06 acceptance criteria.

Review corrected turn-ID metadata bounds, duplicate event identities, nested Back
and explicit detail retry. The first integration test compilation failed on a
coordinator variable-name typo, then compiled after correction. The first APK
audit lacked ANDROID_HOME and stopped before inspection; the configured rerun
passed. Earlier successful emulator cohorts did not cover an actual retained
render callback with a colliding event number in the new story. Review found the
delegated-state capture gap and added that stronger UI regression; its negative
and corrected cohorts remain separately recorded. No earlier pass is relabelled
as proof of the corrected callback binding.

JVM tests additionally cover noncooperative completion/failure, retry, Back,
page/query changes, busy/recovery gates, story/head/gameplay/disposal and retained
callbacks. Compose tests exercise platform Back and the rendered callback boundary;
they do not establish a new framework onStop or native in-flight IO cancellation
measurement. Both selected emulators are API 35 x86_64 with 4096-byte OS pages;
APK alignment for both ABIs is not ARM64 or 16 KiB-OS execution.

No phone, real model, prose quality, performance/thermal, process-kill, hosted CI
or release qualification is claimed. M01.01 is blocked on an authorized available
physical phone. M06.06 remains partial/in review pending owner acceptance; all
milestone checkboxes stay unchanged. The next product-facing task is bounded
M05.05 Android Action/Dialogue input over the guarded play contract, reconciling
the active shared Host/Store ownership and keeping production runtime selection
and real-backend qualification separate from fake-provider plumbing.
