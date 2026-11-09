# Original-story cancellation status verification — 2026-11-03

Refs #13 M09.02/M09.03 and #14 M10.02 supporting fault injection.
Implementation is in review; full task criteria remain unchecked.

## Problem and change

A current original-story generation/review/create gateway cancellation reached
the controller's `finally` and cleared busy/creating, but left the old progress
notice visible. The dialog reads this notice directly. A player could therefore
see “Generating…” or “Reviewing…” after that attempt had stopped; a cancelled
Create retained its one-shot lock without a specific uncertainty notice.

`OriginalStoryController.run` now changes only its cancellation catch: when
`current(ticket)`, revoke review and publish a finite status. Before Create,
the draft is preserved and nothing was created by that attempt. After Create
starts, the message admits a story may already exist and directs library
refresh. The same exception is rethrown. All generation/closing/disposal fences,
gateway calls, createStarted/key consumption and finalization remain unchanged.
No raw exception payload is displayed and no automatic retry/cancel is added.

Base main: `a635686c8b18acf796d940522e974b88ded834ae`, tree
`5cb2c2c75103853f7f068bbfc6fb0b953982488a`, 2,592 raw Git files.
Tested code: `c916f4649efc4bfc21f803c12c143fc066170206`, tree
`48034f4e55ad7784b77453ec9de487f061b98f47`, 2,593 files.
Subsequent documentation is separate from that tested tree. Only the controller
and one new regression file change in the code commit.

## Actual checks

Windows host; existing JDK21, Gradle8.11.1, AGP8.10.1, Kotlin2.2.21,
Rust1.93.1 and NDK29.0.14206865. No dependency/version change or download.
Project source/output and process-local TEMP/TMP/TMPDIR are physical D:.
Gradle uses the existing D: cache. The first attempt inherited an unsuitable
Cargo cache; later attempts explicitly select the existing D: Cargo cache.
Installed JDK/SDK/tool locations and global settings are preserved.

| Attempt | Actually credited result | Checked host owner |
| --- | --- | --- |
| first-v1 | Offline Rust setup failed on missing cached unicode-general-category; zero JUnit methods | completed, exit1, known cleanup, 38.238s |
| first-v2, unchanged controller | 6 methods, 3 assertion failures, 0 errors/skips | completed, exit1, known cleanup, 125.099s |
| final-v1, minimal fix | 55 methods / 7 suites, 0 failures/errors/skips | completed, exit0, known cleanup, 16.257s |

Timed worker bodies were 23.471s / 124.591s / 15.765s respectively. All use the
unchanged checked Windows owner, 180-second deadline and 262,144-byte combined
pipe ceiling, with the byte barrier released only after job assignment. No
source, task, assertion, output or time guard was loosened after setup failure.
No native task was skipped to repair that failure.

Fresh XML and the actual `:app:testDebugUnitTest` task line qualify execution;
stale or absent XML and zero methods cannot pass. The setup failure retains
zero-case attribution. Phase-specific XML, IDs, before/after maps and workers
remain preserved before Gradle later rewrites its build output.

FIRST's failures are exactly current generation, current review and current
Create. Generation/review fail the explicit stopped-status assertion (line121);
Create fails its uncertainty assertion (line248; Gradle's line233 names the
method entry). Positive flow and held late dismiss/dispose controls pass before
the fix. FIRST stops at those first assertions, so later subcase assertions are
not retroactively credited as having executed in FIRST.

The same new file is 15,459B/SHA256
`2ffcfedc3d87cfd498e780f9579ca9b25c88329818f95f524c4fa476a9f7e6ef`
through FIRST and final. Final **55 includes the six new methods** and 49 existing
checks: OriginalAuthorOwner5, OriginalPlayerBinding3, OriginalStoryController18,
OriginalStoryInputValidation8, StoryCreationController10, StoryCreationShell5.
The six new methods cover current cancellation, explicit retry only, draft/
consent retention, consumed Create with refreshRequired, successful exact-review
creation once, and held late cancellation after dismiss/disposal in three phases.
Cancelled child/active parent checks preserve coroutine propagation. Local and
scripted provider labels in fake ports do not represent model execution.

Full tracked source maps close all 2,593 files before/after both semantic runs;
only the controller changes between FIRST and final. Tests remain byte-identical.
Both Rust JNI ABIs compile during first-v2; final reuses unchanged native output.
This is compilation, not JNI/ARM64 or emulator execution, APK packaging/install,
or native Store/resource-ownership qualification.

## Evidence, review and limitations

Private controls are `run_jvm_owned.py first-v2` and `final-v1` under
`D:/Dev/Experiments/LocalLore/2026-11-03-original-cancel-status-v1`, run from its
physical `candidate-source-v1`. The original setup failure is `first-v1`;
versioned workers/control provenance retain exactly what each attempt ran.
Matching recovery uses the same basename under `D:/Dev/Recovery/LocalLore`.
The declared ordinary source/build/test/control/recovery retention cap is2GiB;
final manifests measure coverage without deleting old evidence to fit.

The owner retains bounded stdout and stderr byte counts. Raw first-v1/first-v2
stderr payloads (401/434B) were not retained or reconstructed; their stdout and
fresh JUnit failure records remain. Final stderr count is zero. No complete
failed-stderr preservation claim follows from the archive.

B75 authors the six original tests; B72 independently reviews their quality and
source/evidence. Production and closed-evidence review exclude a reviewer's own
oracle-quality credit. Root integrates shared source and publication. Snapshot
and alternate-index publication preserve normal892/index897; the managed
worktree tool refuses this physical repository outside the attached chat roots.

No actual native/provider cancellation without dismissal is established. The
suspend gateway permits it; native transport/owner timeout and uncertain-cleanup
paths remain separately qualified. No real commit, native cleanup, physical
device, ARM64 execution, model/story quality, full CI or Android UI pass is claimed.
Parent-scope cancellation before coroutine entry is outside this exercised slice.

No emulator/ADB/phone/model action, shared-ledger mutation, evidence deletion,
settings change, other-emulator stop, release or merge. PR392's frozen source,
five-test proposal and pending approval are unchanged. Next dependent device
task remains its guarded run after separate explicit approval; this patch does
not qualify it.
