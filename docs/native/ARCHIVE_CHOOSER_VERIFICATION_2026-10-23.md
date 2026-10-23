# System document chooser verification — 2026-10-23

M08.06 partial implementation evidence. Stacked on open PR77 and its open PR76
prerequisite. Owner acceptance and the complete milestone exit gate remain open.
See the [test boundary](ARCHIVE_CHOOSER_CONTRACT.md).

## Reproduction

Build the isolated verification application and its instrumentation APK without
replacing the normal application or resetting any data:

```powershell
cd apps/android
./gradlew :app:assembleDebug :app:assembleDebugAndroidTest :app:testDebugUnitTest :app:lintDebug -PlocalLoreArchiveVerification=true --offline --no-daemon
```

The installed target must be `org.locallore.app.archiveverify`, with matching
`org.locallore.app.archiveverify.test` instrumentation. Inspect the existing
installed identities before `adb install -r -t`; do not replace an unrelated APK.
Run each method separately with the selected emulator serial:

```text
adb -s <selected-serial> shell am instrument -w -r -e class org.locallore.app.ArchiveChooserActivityTest#validChooserImportContinueExportAndConflict org.locallore.app.archiveverify.test/androidx.test.runner.AndroidJUnitRunner
adb -s <selected-serial> shell am instrument -w -r -e class org.locallore.app.ArchiveChooserActivityTest#invalidChooserInputsRemainRecoverable org.locallore.app.archiveverify.test/androidx.test.runner.AndroidJUnitRunner
```

These commands interact with the actual system DocumentsUI. Use a dedicated
verification app, keep the device unlocked, and do not interact with its picker
concurrently. Each test creates synthetic evidence and retains imported test
stories; repeated runs consume storage and story admission capacity. No test
clears the app or default workspace. A native fresh fixture workspace and a
separate test-provider run hold only original synthetic content.

## Verification status

Final executable/test source: `af83753`; later changes are documentation only.
The [structured evidence](ARCHIVE_CHOOSER_RESULTS_2026-10-23.json) records source,
APK and private raw-log hashes for every attempt. Raw files and databases remain
private. No native engine, Store, Host, schema or dependency pin changed.

- `python scripts/check.py host --offline`: 308 workspace Rust tests, 3 linker
  tests, 206 Python tests, formatting, strict Clippy and fixture audits; exit0.
- Isolated Gradle assemble application/instrumentation, clean JVM test rerun and
  lint: exit0, 79 tasks (12 executed, 67 up-to-date), 60 JVM tests with zero
  failures/errors/skips, lint zero errors and one existing version warning.
- `python scripts/check.py android --offline` with configured Java/SDK: exit0,
  78 tasks (32 executed, 46 up-to-date), production APK audit passes. Its first
  attempt lacked ANDROID_HOME and failed before compilation; that log is retained.
- Both ABI ELF/ZIP 16 KiB alignment, the seven archive JNI symbols, receiver-only
  application permission and absence of test providers from the application
  manifest pass. The test APK alone contains the DocumentsProvider and control.
- Two authorized selected API35/x86_64 emulators, 4 KiB pages: each passed the two
  new chooser tests and all 19 existing archive native/provider/Compose/Activity
  cases. **42 passes, zero skipped/unfinished** on the final artifact pair.
  Three earlier fixture-setup failures are separate from these passing runs.

The unchanged isolated application APK SHA-256 is
`5a058eef62d1e56e9326ac71a959bd1205ae9a96820b42626abda6530e93944f`;
the final instrumentation APK is
`cea55bc65736a6ed289efbe75df617d1d4b8e26137c105523f731c5d7f39e911`.
Installed identities were checked before every install, only the isolated pair
was replaced with `install -r -t`, and five prior package hashes were preserved.
No data clear, uninstall, default-story reset, model action or emulator restart.
Every observed cohort ended with confirmed client cleanup and absence of both
owned package processes, including all provider subprocesses.

## Observed behavior

Actual MainActivity OpenDocument selected a provider source. Native validation
produced a preview while the library and prior accepted state stayed unchanged.
Explicit confirmation added only the new engine-allocated story ID. A fresh
native open/reexport matched the exact original archive before gameplay. Explicit
Open attached the imported story; one potion gift committed, another was refused,
and a separate reopened native snapshot retained two receipts and no player potion.

Actual CreateDocument selected the test root and Save created a new document.
After descriptor closure, its bytes equaled a separately captured native export.
Read access was denied before source selection; write access was denied before
creation and granted afterward. No chooser grant was persisted. A selected
same-ID archive failed without overwrite; future-format and malformed documents
failed without import, then a valid preview could be selected and cancelled.
Prior stories/accepted state were preserved and the prior selection was restored.

Provider counts reached opened=closed, active=0 and zero close failures. Existing
regressions separately exercised actual pending-picker cancellation across Activity
recreation, late callbacks and native/provider cancellation/ownership. The new
invalid-input case cancels a validated preview; it is not itself a pending-picker
cancellation case. A provider handler thread lives until process teardown; no
per-test thread-join or arbitrary-provider preemption claim is made.

Two explicit shell-UID attempts to call the control authority were refused with
the provider's fixed SecurityException. Their client and process cleanup passed.
An earlier observation captured stdout alone and missed the denial on stderr;
it is retained as failed evidence collection, not a successful permission proof.
The corrected fixed command captured both streams and verified the exact denial.
The local report parser also required a singular `OK (1 test)` spelling fix;
terminal start/pass records were independently inspected before report generation.

## Limits

The first two emulator attempts failed in fixture setup before launching a
picker. A third diagnostic attempt identified SecurityException during protected
provider acquisition. Reviewing custom call dispatch alone had missed that
earlier permission check. The correction adds a separate test-only `.control`
authority: exact Binder UID authentication and strict bounded request validation
precede delegation under the provider's own process identity, restored in finally.
The document authority keeps MANAGE_DOCUMENTS, and product callbacks use system
URI grants without adopting permissions. All failed attempts remain accounted
for; they are not passing chooser evidence.

The test provider limits retained runs to128 and outputs to8 per run. Synthetic
input and stats readback are capped at128 KiB. A granted writable regular file
descriptor cannot enforce that write quota itself; oversize readback fails.
No hard hostile-provider or storage-exhaustion guarantee follows.

Typed fake inference and original synthetic archives only. Emulator execution
does not establish real-model quality, physical-phone feasibility, ARM64
execution, arbitrary third-party-provider behavior, model compatibility, disk
exhaustion or process-death recovery. A selected provider may sync exports; the
app's local-only gameplay contract does not control that provider. No model
weights or private story data are uploaded. No merge or release is authorized.
Full M08.06 and owner acceptance remain open. Next runnable work is bounded
archive-specific process-death/failure recovery with preservation of accepted
state; real phone/model gates remain blocked on authorized physical hardware.
