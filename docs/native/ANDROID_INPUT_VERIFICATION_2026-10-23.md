# Android Action and Dialogue plumbing — 2026-10-23

Refs #9 (bounded M05.05), #7 (M03.02/.04 integration) and roadmap #3.
This packet stacks on unmerged PR #67, which stacks on PR #64. It connects
original typed text input to the actual Rust guarded play-v2 pipeline using an
explicitly scripted native fixture. It does not qualify a real local backend,
reference phone, narrative quality or the full M05.05 acceptance gate.

## Authority and visible behavior

The composer offers Action and Dialogue, a non-binding potion example, and Send.
The example only edits the draft. Text is nonblank, at most 2048 UTF-8 bytes,
well-formed Unicode and free of control characters except newline/tab. Valid text
is sent unchanged, including whitespace. Drafts remain in the composition through
rejections and accepted head updates; changing story/branch or disposing the
composition forgets them. There is no automatic draft persistence or diagnostic
text capture. Pending/recovery/unavailable states disable edits and submission.

Kotlin does not interpret prose or create gameplay commands. It sends the original
Host-v1 `free_text` request with action/dialogue kind, text, story/branch, captured
accepted head and one UUID turn key. Rust owns context filtering, intent guards,
proposal validation, mechanics, narration policy and atomic commit. Preparation
adds no accepted transcript. The UI publishes the authoritative saved snapshot,
not fields invented by a provider response. Recorded dialogue is a statement,
not proof of its proposition. Existing typed demo actions/modes remain regression
fixtures and do not silently substitute for text play.

Lost acknowledgements retain the original immutable request. Recovery checks that
key, resubmits the same `free_text` command only after actual UnknownTurn, and
validates the exact accepted request. Commit acknowledgement loss checks status;
it does not allocate another key. Busy/storage/transport uncertainty retains the
pending key. Receipt decoding completes before releasing it. Cancellation of an
unknown original turn never resubmits it.

A coroutine mutex orders a finite, noncancellable submit exchange before cancel.
This prevents Stop overtaking a submission and leaving a later queued turn
uncancelled. Generation/prepare never holds this mutex. Existing Rust session,
revision, cancellation and handle ownership fences remain authoritative. Disposal
closes the underlying native owner; retained callbacks cannot reopen it. Already
executing native IO can finish while stale publication is fenced.

## Explicit synthetic provider

Trusted native WorkspaceRegistry construction configures
`android-scripted-play-v2` through a new fixture configuration API; JSON cannot
configure providers or grant privileges. Capability and status types are checked
exactly. Unknown or malformed metadata cannot enable text play. The UI labels the
fixture as **Scripted fixture · no language model**. `real_model=false`,
`loaded=false`; no model/tokenizer/runtime artifact is loaded. The existing real
provider configuration API retains configured-owner semantics, without asserting
that a model is loaded.

Each turn gets a fresh provider. Action always proposes one potion gift to Mira;
the existing Rust intent guard and inventory/mechanical rules decide whether that
matches the original request and can commit. Dialogue copies only the literal
schema-constrained text and one eligible nearby audience member. The provider
does not parse prompts, discover secrets or duplicate the action compiler. The
narrator uses exact approved event references and fixed harmless prose subject to
the existing narration validator/fallback.

Each role yields Pending for 400 ms without sleeping in poll; the core turn
budget/deadline/cancellation remains in force (5 s, one configured repair maximum).
Profile identity fields are all-zero synthetic placeholders required by the
existing receipt shape, never measured model/artifact hashes. Diagnostic trace
provenance omits those artifact/config/runtime identities and keeps only software
labels. No new dependencies, network permission, thread service, schema migration,
model download or production backend choice is introduced.

## Verification and scope

Final executable source: `77dcda9`. The [results JSON](ANDROID_INPUT_RESULTS_2026-10-23.json)
retains complete attempt accounting; the [independent review](ANDROID_INPUT_REVIEW_2026-10-23.md)
distinguishes evidence from inference.

Final host checks passed 243 workspace Rust tests, 3 native-linker tests and 191
Python tests, with formatting, warnings-denied Clippy and four-case fixture drift
checks. Final Android build/lint passed, with 77 JVM tests, zero failures/errors/
skips, zero lint errors and one existing dependency advisory. Both native ABIs were
freshly built during integration; later test-only builds reused those binaries.
The final APK passed manifest, ABI, ELF and ZIP alignment checks, with no INTERNET
permission and 16384-byte native load alignment.

Both final emulator cohorts passed all 15 methods (30 final-source passes, zero
failures/skips/unfinished). All four cohorts are retained: 58 passes and two initial
fixture failures, zero skips/unfinished. The recovery test initially compared JSON
object serialization order across Kotlin and Rust. Its correction compares every
key/value and array position structurally, preserving original text/kind/scope/
head/turn assertions and repeated-request identity. The initial failure interrupted
the fault loop after its first variant; all three variants passed on both final
cohorts. This correction changed only the test oracle, not production behavior.

Earlier checks also retain one new JVM fake-fixture cancellation-count assertion
failure (corrected fixture semantics, then full 77-test passes) and one existing
Windows process-ownership test timeout with no captured child-PID output. That test
verified cleanup before failing to parse empty output; the capture cause is unproven; a targeted rerun and full unchanged
host runner passed. No benchmark implementation/deadline fix is claimed. Raw logs,
local paths and fixture databases stay private; sanitized results are checked in.

The existing pinned toolchain is Rust 1.93.1, JDK 17, Gradle 8.11.1, AGP 8.10.1,
Kotlin 2.2.21, NDK 29.0.14206865, SDK 36/minimum 26, with unchanged locked dependencies.
Run host checks from the repository root:

```powershell
python scripts/check.py host --offline
```

With JAVA_HOME and ANDROID_HOME configured, from apps/android:

```powershell
.\gradlew.bat :app:cleanTestDebugUnitTest :app:testDebugUnitTest :app:assembleDebug :app:assembleDebugAndroidTest :app:lintDebug --offline --no-daemon
```

From the repository root, with ANDROID_HOME configured:

```powershell
python scripts/audit_apk.py apps/android/app/build/outputs/apk/debug/app-debug.apk
```

Device checks use the two existing authorized Android 15/API 35 x86_64 emulators
with 4096-byte pages. APK identities and stopped ownership are guarded before
install-r, preserving app data. Prior capacity fixture packages remain unchanged.
Native-only tests run before Compose; each uses an owned synthetic no-backup root,
real JNI, bounded owner drain and reacquisition of all four native slots before
owned-root cleanup. Uncertain cleanup retains the fixture. No default player save,
unrelated emulator, uninstall, app-data clear, root or storage filling is involved.
Require all 15 method start/terminal pairs and successful runner protocol:

```text
am instrument -w -r -e class org.locallore.app.StoryRecordInstrumentedTest,org.locallore.app.EventSourceInstrumentedTest,org.locallore.app.PlayInputInstrumentedTest,org.locallore.app.StoryRecordScreenTest,org.locallore.app.EventSourceScreenTest,org.locallore.app.PlayInputScreenTest org.locallore.app.test/androidx.test.runner.AndroidJUnitRunner
```

The seven new methods cover original v2 action/dialogue receipts and no precommit
canon, strict reopen/exact retry, actual UnknownTurn and lost acknowledgements,
malformed provider metadata, cancellation/disposal of running native preparation,
ordered cancellation after a deferred submission, and collected Compose behavior.
Eight existing player-record/source navigation methods remain regression checks.
Running phase begins before provider polling, so the device test proves cancellation
of running preparation, not observed entry into a particular provider poll. The
Rust provider unit separately tests Pending then Cancelled. UI pending gates are
test transport gates, not model timings. Exact retry/reopen validates receipts and
canon; it has no independent device provider invocation counter.

Physical-phone performance, ARM64 execution, 16 KiB-page execution, real model
loading, model quality, offline phone scene/enjoyment comparisons, process-death
continuity and keyboard/OS backup privacy qualification remain unmeasured here.
Static ARM64 packaging/alignment and fake-provider emulator behavior do not close
those gates. The finite supported-English Rust action guard remains deliberately
limited; unsupported actions reject or require clarification. Full M05.05 stays
unchecked pending its real-backend and reference-phone acceptance criteria.
