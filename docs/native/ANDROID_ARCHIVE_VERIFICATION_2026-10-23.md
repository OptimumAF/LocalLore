# Android playable archive verification — 2026-10-23

M08.04/.06 partial Android adapter, based on accepted main `a2bb6639` and shared
archive v1. [Claim](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6361861928).
Implemented for review; no milestone acceptance, release, physical-device,
model-quality, or ARM64 execution claim. The shared Store validates/replays and
commits; Kotlin presents consent and transfers bytes. No new third-party
dependencies or dependency pins, shared schema, gameplay authority, or model
runtime changed. Android adds a direct dependency on the existing shared Store.

## Changes and independent work

The [frozen boundary](ANDROID_ARCHIVE_BOUNDARY.md) assigns seven JNI calls,
strict control replies, original-scope single-use capabilities, a four-owner
budget including draining retired owners, and a private fresh staging Store.
Shared archive validation, replay and transaction code is reused. Stage cleanup
must succeed before the target import; preexisting stages are never adopted.
Cancellation fences publication and new side effects; it cannot roll back a
commit already accepted by Store. Whole-story imports retain IDs and conflict
on duplicates rather than overwriting or silently remapping them.

Separate worktrees produced native `de1b173`, consent/controller/document UI
`032a578`, provider/dialog fixtures `e7b805b`, and independent adversarial cases
`211aefd`/review `4f0614a`. Coordinator integration preserves workspace-v1 and
exposes database-schema-v2 separately, fences shell mutations while archive
work/picker tombstones drain, retains picker tickets through ViewModel recreation,
refreshes the real library on close, and opens an imported root only explicitly
with a fresh Host session. Read the [independent review](ANDROID_ARCHIVE_REVIEW_2026-10-23.md).

## Checks actually performed

All content is original synthetic Lantern Quay material. Two selected test AVDs
were observed booted: aliases A/B, Android 15/API 35, x86_64, 4 KiB pages. No
other AVD or installed app package/data was reset, removed or replaced. An
explicit `-PlocalLoreArchiveVerification=true` build uses separate build outputs
and `org.locallore.app.archiveverify[.test]` identities; production keeps its
original package ID. Test providers exist only in the test APK, with isolated
authorities and processes. No phone was observed; no model files were copied.

| Command / cohort | Actual result |
|---|---|
| `cargo +1.93.1 test -p locallore-android --locked --offline` | 27 passed, including four independent actual-Store adversarial cases |
| `python scripts/check.py host --offline` | Exit 0: fmt, workspace Clippy with warnings denied, 300 workspace Rust tests, 3 linker tests, 191 Python tests, Android fixture drift check |
| Isolated assembleDebug / assembleDebugAndroidTest / testDebugUnitTest / lintDebug, offline | Pass; 60 JVM tests, zero failures/errors/skips; lint zero errors, one existing dependency-version warning |
| Initial integrated `ArchiveIntegrationTest` on A and B | Six actual JNI tests passed per AVD; zero failures/skips/unfinished |
| `python scripts/check.py android --offline --clean` | Exit 0, all 79 Gradle tasks executed; both ABIs built; 60 JVM passed; lint zero errors/one existing warning; standard production APK audit passed |
| Explicit isolated APK audit | Expected isolated package/receiver permission, no test providers in app manifest; both ABIs have 16 KiB ZIP/ELF alignment and exactly seven NativeArchive JNI symbols |
| Corrected provider cohort on A and B | 17 passed per AVD: 6 actual JNI, 5 real ContentResolver, 6 state-only Compose; zero failure/skip/unfinished |
| Final code `8c38917`, lifecycle-listener cleanup cohort on A and B | 19 passed per AVD, 38 total; six JNI + five provider + six presentation + two actual Activity tests each; zero failure/skip/unfinished; prior identities/process/client guards confirmed |

The six JNI cases exercise separate workspace/database metadata, accepted gift
export/import/reopen/re-export byte equality and unrelated-story preservation,
unspent import followed by actual Rust fake-provider commit and duplicate-spend
rejection, wrong-kind/consumed/stale/cancelled/closed capabilities, duplicate JSON,
future version and checksum refusal, and repeated four-owner close/reacquire.
The fixture creates and retains unique private synthetic database directories
and checks staging cleanup; it never clears the app's normal workspace.
The 60 JVM cases include 18 new controller/portable document tests and four
shell guard/import-session integration cases; these are not Android provider tests.

Exact per-attempt counts, APK identities, terminal status categories and raw-log
hashes are in [structured results](ANDROID_ARCHIVE_RESULTS_2026-10-23.json).
Private raw logs remain excluded from Git. The provider tests use actual remote
descriptors: nontruncating empty/regular/seekable writes, close counts, old-byte
preservation, read-only/null/failure paths, physically 32 MiB and 32 MiB+1 streams,
and a blocked open. The blocked case proves a Main dispatcher pulse completes,
cancel stays pending until explicit provider release, zero bytes are written,
descriptors drain, and a subsequent write works. It does not promise interruption
of a provider that never returns. Compose checks are state-only; synthetic small
viewport and doubled-font constraints are not real device orientation changes.

The corrected Activity cohort passes all 19 methods per AVD. Its two additional
cases use actual MainActivity and NativeArchiveGateway: native preview capture/
revocation, library refresh with unchanged canon, and actual OpenDocument launch
to DocumentsUI. The stopped Activity is recreated while DocumentsUI remains
foreground, its replacement retains the same ViewModel/picker ticket, and guarded
Back delivers a null result that drains the ticket and re-enables controls.
No document is selected or written in these Activity cases. First app startup can
initialize the default synthetic story; tests then make no gameplay mutation.
The test lifecycle listener is removed in finally, including recreation failure.
After that final listener correction, both APKs were rebuilt (79 tasks, 32
executed/47 up-to-date) and the full 19-method selector passed again on both
AVDs. The separate production incremental rebuild/audit also passed (78 tasks,
31 executed/47 up-to-date). Java 17.0.6, Gradle 8.11.1, AGP 8.10.1 and Kotlin
2.2.21 were observed. Exact final code is `8c3891700ca5e7dbca3f92e6e6219ccab2527a78`;
subsequent commits update evidence/documentation only. Across all 14 retained
device cohorts there are 182 passes and six negative/fixture failures, with zero
skipped/unfinished records. The latest 38 passes are the final acceptance evidence
for this adapter slice; earlier failed attempts are retained, not relabelled.

For reproduction on separately owned, authorized test AVDs, build the isolated
variant from `apps/android` with the verified Gradle wrapper and configured JDK/SDK:

```powershell
.\gradlew.bat :app:assembleDebug :app:assembleDebugAndroidTest :app:testDebugUnitTest :app:lintDebug "-PlocalLoreArchiveVerification=true" "-Pandroid.builder.sdkDownload=false" --offline --no-daemon
```

Install only the resulting `app/build-archive-verification/outputs/apk/debug/`
and `androidTest/debug/` APKs into the separately owned archiveverify packages.
The executed instrumentation selector is
`org.locallore.app.ArchiveIntegrationTest,org.locallore.app.ArchiveDocumentTest,org.locallore.app.ArchiveDialogTest,org.locallore.app.ArchiveActivityTest`
with runner `org.locallore.app.archiveverify.test/androidx.test.runner.AndroidJUnitRunner`
and `am instrument -w -r -e class <selector>`. Coordinator guarded package hashes
before/after install, retained raw terminal records, and confirmed all owned
app/provider processes and ADB clients drained. Successful ADB exit alone was
never counted as a test pass. No existing app data was cleared or uninstalled.

## Failure accounting and limits

- Two metadata-only device tests failed initially (one per AVD): actual database
  metadata was absent from the Kotlin snapshot, expected 2 / actual null. Both
  passed in the integrated cohort after exposing that separate field. Workspace
  contract 1 opened correctly throughout; this was not a migration failure.
- The first provider/dialog cohort ran six JNI plus six Compose tests successfully
  per AVD, but JUnit rejected the provider test class: its `@After` expression
  inferred a Bundle return instead of Unit. One class initialization failure per
  AVD; the five provider methods did not run. The failed attempts are retained.
- The first 19-method Activity cohort passed 18 and failed one per AVD:
  `ActivityScenario.recreate()` first waited for RESUMED while the real picker
  correctly kept the app STOPPED. The test now directly recreates that stopped
  Activity and observes its replacement through the framework lifecycle monitor,
  rather than dismissing the picker early or forcing the Activity foreground.
  This was a test-harness failure, not evidence of a production lifecycle defect.
- Initial build setup failed before tests because a relative log directory was
  missing, then an unquoted PowerShell `-P` option was split. Structured argv fixed
  invocation. The UI author's first JVM compile had three `fail()` return-type
  errors, corrected before its 18-test pass. Native author's first Clippy found a
  large enum variant, boxed before its successful test/Clippy rerun.
- A one-line APK audit invocation failed in PowerShell/Python quoting before
  executing an audit. The structured script then passed all checks above.
- Source review found stale post-await side effects and retired-owner budget
  omissions; authors corrected them before integration. These are source findings,
  not fabricated executed red tests. No private source text or model output was
  uploaded.

Provider/OS stalls have no hard preemption guarantee; a partial new document can
remain. Same-UID filesystem compromise and concurrently malicious providers are
outside this app-private boundary. Full D08 cross-platform/branch/correction gates,
physical phones, ARM64 execution, legacy migration UI, broad story deletion and
real inference remain separate. No full M08 task is checked or closed here.
