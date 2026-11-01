# Archive UI: bounded Android execution

Date: 2026-10-30. Packet B32. Refs #14 (M10.02), supporting #13
(M09.03/M09.05/M09.06). The ten-method model-free Android cohort passes on
one freshly authorized API35 Google APIs/x86_64 emulator. This supporting
qualification is in review; full tasks remain unchecked pending their complete
criteria and owner acceptance. No merge or release occurred.

The [B25 host/build report](ARCHIVE_UI_HARNESS_VERIFICATION_2026-10-30.md)
retains its original attribution: it built and packaged these methods but did
not execute them. B32 supplies the separate target evidence. The
[operational contract](../runtime/android/ARCHIVE_UI_HARNESS.md) remains fixed.

## Source, target and admission

Executed source is the clean, frozen
`62ba698d064143d8602aa917c96b459c1a37594e`, with 2,328 tracked raw inputs, at
`D:\Worktrees\LocalLore-ui-runner-build-v1`. This later reporting change touches
documentation only in a separate checkout. It does not replace the executed
head in the build or runtime proof graph. PR #297's later narrator-name fix is
not part of these APKs.

| Existing artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Genuine build manifest | 15,424 | `823195e3770228b12c4f967c2b749efcc92aa0973385d7970369414a0ff3430e` |
| org.locallore.app.archiveverify APK | 27,756,156 | `b152ddea01363fc622a286dab3d59386739a997c5cb77a14d97851ec166ab192` |
| org.locallore.app.archiveverify.test APK | 2,220,071 | `0b58ff22bc0d51585fc695e20d2ce303a7e8d38fb621ee61464ba14cc3a5db70` |

Both APKs retain certificate SHA-256
`17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564`.
There was no rebuild, dependency change or new JVM/Rust/host test run in B32.
Earlier B25 checks are not represented as rerun.

The owner approved one fresh guest at
`D:\Dev\Experiments\LocalLore\2026-10-30-archive-ui-v1\avd-v1`, with
8 GiB RAM, four cores, a 40 GiB shared reservation and a 30-minute maximum.
The current shared storage guard reserved capacity before guest creation/SDK
preparation. Guarded preparation and exclusive private-port/ownership checks
passed. No previous guest was repurposed, and no test was retried.

The fixed `owned-emulator-archive-ui-v1` / `sdk-archive-ui-v1` profile uses
client version 6 and exactly three artifact roles: build, product APK and test
APK. It has no model material. SDK platform-tools report
37.0.1-15733141; the installed JDK is 21. The owned private ADB service uses
15937, with emulator console/ADB 5592/5593. Shared ADB and other emulators were
not stopped or replaced. Phone discovery and model operations were excluded.

## Actual procedures and results

The private controls call the current guarded preparation, public
`owned_ui_owner.py --admission … --admission-sha256 …`, and production
`archive_ui_controller.run(admission, running)` interfaces. They do not copy an
older lifecycle implementation or invoke SDK guest creation directly.

| Actual procedure | Result |
| --- | --- |
| Guarded preparation plan, then authorized preparation | Exit 0; respective finite owners 28,622 ms and 81,328 ms; complete cleanup/capture and actual child/request joins |
| One public UI owner | 656,525 ms; child exit 0, complete cleanup/capture, stdout/stderr zero; qualified target, reason `stop_requested` |
| One production controller | Completed in 500,059 ms; 36 qualified client records; all ten fixed methods start/pass/end exactly once |
| Controller's finite outer owner | 501,807 ms; child exit 0, complete cleanup/capture, stdout/stderr zero; actual caller identity joined to request/start/result |
| Exact owned stop after terminal controller | Stop published; observer handles closed; all 15 worker cleanup flags true |
| Shared storage closure | Guest recorded `closed`, retained logical charge 18,981,612,425 bytes; disks remain in place |

The controller verifies boot/API35/x86_64/user 0, initially absent isolated
packages, binary APK transfer and device hashes, installation, and installed
UID/path/hash before and after instrumentation. Its 36 contiguous client records
each retain before/after ownership proofs and raw results. This count includes
setup and postchecks, not 36 UI methods.

All selectors below use the `org.locallore.app` prefix. Every row passed once.

| Class | Method |
| --- | --- |
| TranscriptFollowScreenTest | readingHistoryKeepsPositionUntilLatestAndPreservesTheUnsentDialogue |
| TranscriptFollowScreenTest | seeingOnlyTheHeadOfALongTailDoesNotAuthorizeFollowingAnAppend |
| TranscriptFollowScreenTest | readingTheComposerPastTheTailFollowsTheNewReplyWithoutSubmittingTheDraft |
| TranscriptFollowScreenTest | retainedLatestCallbackCannotNavigateAnotherBranchWithReusedMessageIds |
| SystemThemeTest | systemDayNightRoundTripKeepsScopedDialogueDraftStateAndUserCallbacks |
| SystemThemeTest | nightDayChangesDoNotSubmitOrCancelBusyDraftAndExplicitCancelStillFiresOnce |
| ShellLayoutTest | pendingResponseCancelControlInvokesItsCallback |
| ShellLayoutTest | smallViewportAndDoubleFontScaleKeepControlsReachable |
| PlayInputScreenTest | exampleOnlyEditsAndAcceptedOriginalDraftsSurviveHeadsButNotStorySwitches |
| PlayInputScreenTest | validationRejectionDuplicatePendingCancelAndDisposalKeepDraftsAndCanonSafe |

The first eight methods use synthetic UI state. The final two use scripted
inference with the actual Rust engine. Pending cancellation in that fixture is
gated before native preparation; it does not establish cancellation while a
native inference provider is running.

## Independent readback and retained failures

After all producers closed, an independent file-only reader passed both
unchanged production readers: `verify_controller_result` with the externally
observed actual caller, and the version-6 owned-target result reader. It checked
the current 2,328 raw sources, genuine build/APKs, all 36 client/proof pairs,
ten ordered JUnit methods/claims, stop, all 15 cleanup flags, guest closure and
the fixed ledger's closed entry. Reader exit 0: 10,979 ms body, 11,082 ms outer.
The outer bound was stdlib subprocess timeout, not a separately attested
Windows Job. Receipt: 17,848 bytes, SHA-256
`1c6e97c0d9c68b7b91705b57b736edf34c7bd00adae32d786f5628f4136f1b77`.

This reader performed read-only Git and fixed installed-tool hashing, including
its own runtime DLL-path lookup. It did not replay SDK commands, target-native
observations, installation or instrumentation, or read images, keys or models.
Its cooperative Python audit is not an OS security boundary. Captured native
ownership/closure facts were authenticated through the production readers.

The first closed reader failed because its audit refused the standard-library
null sink; inspection also found Windows subprocess audit arguments use a
command-line string. Its failed receipt/trace remain. The correction permits
only that exact null sink and three exact read-only Git command strings at the
fixed checkout with optional Git locks disabled. Production checks and D:
boundaries remain unchanged. This was a checker failure, not a product failure,
and caused no emulator/test replay. Earlier static control findings were fixed
before their affected actual operation; no invented runtime RED is claimed.

## Retention and remaining gates

Controls, raw client/proof/session records, all failed/static review captures,
source bindings and shutdown evidence remain under
`D:\Dev\Experiments\LocalLore\2026-10-30-archive-ui-run-v1`, with selected
verified copies/archive in the matching `D:\Dev\Recovery\LocalLore` path.
The closing ticket comment records exact recovery counts/seals and measured
bytes against the separate 128 MiB control/recovery cap. Guest payload remains
under shared storage accounting; no images or model material are copied into
recovery. Existing build outputs, source and earlier recovery stay in place.

The shared ledger now contains one records-only retired root and two closed,
unretired roots. Closing a guest does not retire its disks or authorize another
boot. The one-run grant is spent; preserve guest state and recovery. B31's
approved older nine-image retirement remains a separate operation with its own
evidence, and B29's separate build-budget failure remains failed.

`feature_acceptance` remains false by design. This qualifies these fixed
model-free methods on one API35/x86_64 emulator. It does not qualify a physical
phone, ARM64 execution, a real model/import, provider-running cancellation,
causal OS process death/restart, TalkBack, physical touch/IME, traffic privacy,
story enjoyment, performance, production runtime selection or release readiness.
No phone operation, model copy, other-emulator/shared-service stop, system
setting, access change, merge or release occurred.

Next runnable task is review of PR #294's source and these closed records.
Further device/model/lifecycle qualification needs its own concrete protocol,
current source/artifacts, storage admission and applicable authorization; this
run supplies none of those missing results.
