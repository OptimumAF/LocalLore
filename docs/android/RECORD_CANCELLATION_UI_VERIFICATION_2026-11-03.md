# Story-record cancellation UI coverage

B110; Refs #14 (M10.02), supporting #13 (M09.04/M09.06).
Supporting tests are implemented and host-verified; full acceptance remains open.
The five new Compose methods are **compiled, 0/5 executed on Android**.

This packet stacks on open/unmerged [PR #385](https://github.com/OptimumAF/LocalLore/pull/385)
at `7a0602df0db96fa5aa78c1a3667c5ec7fb3eca23`. Executable test commit
`b591dcc1e7f4d49cd21b7c727d09e0fa6f5959d9`, tested tree
`b0bdf62d2e3f98f46c27faff89bc0f781802edb4`, adds two test files. The final
report is documentation only. No production, engine, JNI, model, permission,
build configuration or dependency change; the parent cancellation fix stays frozen.

## Executable coverage and authority

Three new host methods exercise the real ShellViewModel and its real record
controller through an original synthetic DemoGateway. They test first/later-page
cancellation with exact query/cursor retry, scoped-detail cancellation with the
current child lens and original ancestor event tuple, and obsolete cancellation
after close/reopen/disposal. Each preserves the accepted shell state and uses
tripwires for unexpected gameplay, snapshot, recovery, resume or creation calls.
This is adapter/fake-reader evidence, not canonical SQLite or native execution.

The five instrumentation methods collect the real ViewModel/controller StateFlows
into production LocalLoreScreen, LocalLoreTheme, StoryRecordDialog and event
detail components. They drive rendered controls rather than assigning final UI
error/loading states. Scoped navigation forwards the captured record context,
as MainActivity does. This directly composed fixture does not exercise actual
MainActivity construction, native transport, inference, real saves or OS death.

| Exact method in `org.locallore.app.StoryRecordCancellationScreenTest` | Written assertion scope | Android result |
| --- | --- | --- |
| cancelledCurrentPageShowsSafeRetryAndReusesTheExactFrozenCursor | Safe visible problem, enabled explicit Retry, exact later-page query, no automatic read/gameplay | UNRUN |
| cancelledScopedDetailRendersSafeProblemAndRetriesTheSamePlayerLens | Exact eligible scoped reference, safe event error, same-lens Retry, preserved underlying page | UNRUN |
| obsoletePageCancellationCannotReplaceSectionSelectionOrClosedAndReopenedRecords | Old held cancellation cannot replace a selected section or reopened record view | UNRUN |
| oldDetailCancellationAfterBackCannotFinishTheReplacementDetail | Old completion cannot finish a newer held detail with the same reference | UNRUN |
| disposedOwnerAndRemountedScreenCannotBorrowOldReadsOrRetainedCallbacks | Cleared old ViewModel and retained method references cannot read/revive after mounting a new owner/story | UNRUN |

The last case clears the old owner and mounts a new one. It is not same-live-owner
per-mount action authorization. Existing rendered-action work remains separate.
Fake read-only saved snapshots and eligible references establish no world truth,
character knowledge, native source eligibility or gameplay authority.

## Checks actually run

Physical D: source snapshot; process TEMP/TMP `D:/Dev/_Temp`; existing D: Cargo
and Gradle caches. Existing Java 21.0.4, Gradle 8.11.1, AGP 8.10.1, Kotlin 2.2.21,
coroutines 1.10.2, Rust 1.93.1 and SDK36/NDK29.0.14206865 pins are unchanged.
Offline mode, disabled SDK/toolchain downloads, in-process Kotlin and two workers.
No dependency or runtime compatibility choice/download was introduced.

Private commands were `python -I -S -B <OUT>/run_owned.py <phase>`. Each saves
an exact worker copy and launch hash before release to the reviewed checked host
owner (PR #361 runtime blob `64cde2f5c014b01798cd7e945e3bd592434a5993`,
SHA256 `51e94325ed5e59a31c64fcc274e7a41c40b9dd969b09d39df7be56b0ee941598`).
The owner is host verification tooling, not a new app dependency. The 180-second
parent and 170-second Gradle limits are unchanged; cleanup returned known.

| Phase / actual Gradle work | Actual result | Capture / owned elapsed |
| --- | --- | --- |
| focused-v1: `:app:testDebugUnitTest --tests org.locallore.app.StoryRecordCancellationViewModelTest` | 3 new methods passed, 0 failures/errors/skips | 92.375 / 101.813 s |
| validation-v1: `:app:testDebugUnitTest` | 425 methods / 50 suites, 0 failures/errors/skips; 422 parent baseline + 3 new | 11.551 / 11.859 s |
| package-v1: `:app:assembleDebug :app:assembleDebugAndroidTest :app:lintDebug` and two actual APK audits | Both APKs built; lint 0 errors, 1 warning/1 hint; product and instrumentation-pair audits passed | 67.690 / 67.996 s |

Both JVM test tasks actually executed; unchanged native/build work was reused
where Gradle reported up-to-date. The full run includes the focused three, so
there are 425 unique executed JVM methods, not 428. No new RED claim: the parent
PR's original cancellation failures keep their prior attribution. All actual
B110 build/test phases passed. The preserved author draft v1 was unrun; v2 adds
stricter fixture/gate/cleanup checks and was integrated byte-for-byte.

Source maps agree before/after each phase: focused 2,587 files, full/package 2,588.
All 2,586 base files are unchanged; only the two new test files are added.
Instrumentation source is 24,107 bytes, SHA256
`338d5dc34814d8368d8bb1c9ad60c4961e72c2a05f53db2ae35b6e11ac9daf5c`.
Host integration source SHA256
`431e375e5cc4106efaa5339fd7056e572ab76820abd158106b6d7cc3188388dd`.

## APK identity, compiled eligibility and limits

Product: 28,012,664 bytes, SHA256
`47b74e97b94cace7ac6f32d82c49b6d1665c66d508803f65d505e2b95d6e5c18`,
byte-identical to the parent's recorded APK. This does not extend any older
runtime result to the new tests. Test APK: 2,290,164 bytes, SHA256
`48087f6c7279596cfc87e7cbc9414cc2fea5cd193315dbee1654b980c8902579`.

Existing source-roster and bounded DEX definition readers join all five names to
the actual test APK. The class and methods are public/concrete; each method is
nonstatic, void/noargs, with its actual runtime JUnit annotation. The test class
and nested fixture classes are absent from the product APK. Definition/annotation
checks establish compiled eligibility, not successful assertions or runner output.
Independent source/closed-evidence review also verifies aligned, bounded nonzero
code items for every selected method, without executing that code.
The lint warning is GradleDependency; the hint is AutoboxingStateCreation, both
in unchanged source and neither suppressed.

Gates have a 10-second hold timeout, UI state waits use 8 seconds and fixture
cleanup is bounded at 12 seconds. Tests require held producers still unfinished
before explicit release; timeout cannot silently satisfy the stale-result oracle.
Those timing/geometry/idling assumptions remain unverified on Android. Cleanup
releases gates, clears owned ViewModelStores on Main, waits for entered producer
finally markers and Compose idle. A marker precedes full coroutine completion:
this is not an explicit read-job join or native cancellation/resource proof.

Private source, raw XML/logs, frozen workers, proposals, maps, APKs and recovery
remain under the D: namespace `2026-11-03-record-cancellation-ui-v1`; integrated
synthetic tests and this report are published. Generated Android output measured
648,693,092 bytes after packaging, below the 2 GiB planning bound. That is
post-run accounting, not an enforced quota. Ordinary source/control/recovery has
a separate 256 MiB bound. Older B109 evidence and generated outputs stay preserved.

The managed worktree tool refused attachment scope; a separate D: snapshot was
verified against every base Git blob. Normal checkout/index and the shared AVD
ledger stay unchanged. No current-head CI pass or fresh complete installed-tool
fingerprint is claimed. No SDK management, ADB/emulator/phone/model operation,
image retirement, other-emulator stop, system setting, merge or release occurred.

Full M10.02/M09.04/M09.06 acceptance, MainActivity/native/phone/ARM64/model,
accessibility and privacy/performance gates remain open. Device execution is
blocked by shared capacity and fresh exact-source approval; the pending retirement
question grants no run. Next dependent task is a reviewed, fixed five-method
cohort in the existing guarded UI flow; source/roster preparation can proceed on
the host, while any actual preparation/boot needs separate approval and admission.
