# Comparison reader native qualification — 2026-10-25

Refs #29 D07.06, partial prerequisite. Root executed the checks recorded here.
This document's author only read source, retained logs and local artifact JSON,
computed hashes, and checked the sole-document Git diff. No build, test,
formatter, application, provider, model, device or desktop operation was run by
the documentation author. Raw artifacts remain local and gitignored. Paths in
commands use `<task-root>`, `<artifact-root>`, `<source>` and `<node24>` placeholders.

**Native IPC journeys at `6c2caf2a` passed, but their top-level semantic snapshot
qualification remains incomplete.** Delegated visual review is recorded below;
Root's disposition of its corrected manifest is pending. The retained cohort has
100 check entries and 26 actual WebView2 PNGs. It is not the later planned
semanticVersion2/30-PNG cohort. It does not establish model quality, selected-case
execution, Android runtime behavior, human approval or whole-D07 completion.

This document is based on exact
`56650ebe64d496080252f7b5b4db956989ef2e11`, isolated branch
`docs/d07-reader-native-qualification` / `source-d07-reader-native-qualification`.
The sole owned new path is this document;
[claim 6394574444](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6394574444).
Earlier source-only/UNRUN headers in frozen contributors' files are historical
provenance. The subsequent executions below do not rewrite those frozen sources.

## Contract and acceptance boundary

The frozen
[native reader contract](D07_COMPARISON_NATIVE_READER_CONTRACT_2026-10-25.md)
defines closed pick/status/source/summary/evidence/close actions, native Host
eligibility plus per-source affirmative picker consent, the SAME manager/worker,
window/root ownership, bounded in-memory recovery and access-time expiry.
The shared reader's
[prior qualification](D07_COMPARISON_READER_QUALIFICATION_2026-10-24.md)
separately records actual scripted Rust source/recording/capture/Query2 checks
and their preserved failures. Neither document grants generation or imports
the inspected source into the user's gameplay session.

Shared [PR #156](https://github.com/OptimumAF/LocalLore/pull/156) merged at
`108848c052795e48df00b7c917c50f2678ad4eb5`, with qualified head
`423f43e5473282e5823e8ddeca7a140f34171cd7`. A read-only Git comparison of
those full trees returned exit 0 during this documentation task. Native/viewer
[PR #157](https://github.com/OptimumAF/LocalLore/pull/157) was OPEN/DRAFT with
head `6c2caf2ac3df79777bff7449399c5cebdbee8780` when checked. Its description
can lag later local evidence; this document records the source-bound artifacts.
The separate selected-execution proposal `f614` is unaccepted and outside this
packet. No task checkbox, selected-rerun gate or milestone is closed here.

## Environment and reproducible commands

Coordinator environment: Rust/Cargo 1.93.1, approved existing Node 24.22.1,
PowerShell 7.6.5, Windows 10.0.26300 X64. These are the recorded installed
environment, not new tool-version/OS probes by this author. No downloads,
dependency installation or toolchain changes were made. Captured WebView UA is
`Chrome/155.0.0.0` / `Edg/155.0.0.0`; the installed full patch version was not
collected. Existing cached frontend dependencies were reused.

Native commands ran from `<source>` with:

```powershell
$env:CARGO_BUILD_JOBS = '1'
$env:CARGO_PROFILE_DEV_DEBUG = '0'
$env:CARGO_PROFILE_TEST_DEBUG = '0'
$env:CARGO_INCREMENTAL = '0'
$env:LIBSQLITE3_FLAGS = ''
$env:TEMP = '<task-root>/memory-controls-temp'
$env:TMP = $env:TEMP
$nativeTarget = '<task-root>/d07-comparison-reader-native-target'

cargo test --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --jobs 1 --target-dir $nativeTarget --bin locallore-desktop-spike evaluation::comparison::tests:: -- --nocapture --test-threads=1
cargo clippy --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --jobs 1 --target-dir $nativeTarget --all-targets --all-features -- -D warnings
cargo test --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --jobs 1 --target-dir $nativeTarget --bin locallore-desktop-spike -- --test-threads=1
cargo test --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --jobs 1 --target-dir $nativeTarget --features dev-harness -- --test-threads=1
```

The retained `d07-native-check.ps1` records the exact argv, source, initial
cleanliness, UTC start/end, exit and terminal changes for each command. Its
SHA256 is `ab3884fa40a381332586bd784f1d051994e36ce16137cca27868973927e096fb`.
The source-owned target is this desktop reader target, not an unrelated shared
Cargo cache. The targeted native reader tests use actual scripted producer,
Engine/Store and manager/lease behavior; they do not launch WebView2 or a model.

Frontend reproductions, from `<source>/apps/desktop`, use the direct approved
Node executable:

```powershell
& '<node24>' check-comparison-reader.mjs
& '<node24>' check-comparison-main-review.mjs
& '<node24>' check-comparison-capability-review.mjs
& '<node24>' verify-frontend.mjs
```

Actual application harness invocation:

```powershell
$env:LOCALLORE_D07_COMPARISON_READER_ARTIFACT_ROOT = '<artifact-root>'
$env:LOCALLORE_D07_COMPARISON_READER_TARGET_DIR = '<task-root>/d07-comparison-reader-native-target'
& '<node24>' comparison-reader-harness.mjs
```

The fixed runner records `node build.mjs --harness`, then
`cargo build --manifest-path src-tauri/Cargo.toml --locked --offline --features
dev-harness --jobs 1 --target-dir <source-owned-target>`, then the owned executable
with no command-line arguments for `initial` and `restart`. Each process has
bounded output and an explicit deadline. Development-only environment selects
fixed fixture/picker scenarios; normal IPC accepts neither a source path nor
renderer-supplied consent. No OS dialog automation, desktop capture, activation,
mouse/keyboard input or remote debugging server was used.

## Native Rust and strict qualification

Counts below overlap across focused/default/development suites; they are not a
deduplicated grand total.

| Retained log prefix | Actual source | Result | Build / test duration |
| --- | --- | --- | --- |
| `d07-native-reader-first` | `034905ca81b698d9429af4d691f5c06177de231c` | 10 PASS, 0 FAIL, 0 ignored, 101 filtered; exit 0 | 3m53s / 138.29s |
| `d07-native-clippy-first` | `32a5e3ddbf01d54ab914076ff82838f9c49b7d66` | all-target/all-feature strict Clippy exit 0 | 1m13s |
| `d07-native-normal-all` | `464222ee0e143cb6dd94078c3f61d0a1ff42f658` | 110 PASS, 0 FAIL, 1 ignored, 0 filtered; exit 0 | 10.18s / 161.09s |
| `d07-native-development-all` | `a6f9eb4d089f561d10c2cd7036336044288f42e3` | 114 PASS, 0 FAIL, 1 ignored, 0 filtered; standalone harness contract 2 PASS; exit 0 | 23.82s / 152.08s plus 0.01s |

The first targeted run started clean at 05:49:01.7531777Z and ended
05:55:13.8850686Z. Its `terminalSourceUnchanged` is **false**: build generation
created exactly two untracked permission files,
`permissions/autogenerated/evaluation_comparison.toml` and
`permissions/autogenerated/harness_comparison_reader_case.toml`. This is not
an immutable-source execution claim. Root retained the generated permissions
in `dee633bd9d821c044f474fb1d8c1ff8ef30ffdba`. Subsequent strict/default/dev
process records are clean and terminal-source-unchanged, with no changes listed.

The default/dev ignore is the existing
`models::tests::abandoned_import_reparse_file_is_preserved`, requiring Windows
symlink privilege. No privilege was acquired or OS setting changed. The targeted
reader log deliberately prints a fixed worker-panic diagnostic in its passing
failure/cleanup test; a passing suite does not mean empty diagnostic output.
Default/dev include the two closed comparison-command parser tests; those tests
are not added again to the counts above.

## Frontend failures retained before correction

These are actual controller/decoder and test-owned React callback checks with
mocked transport. They are not native IPC, Main execution, DOM rendering or
canonical receipt-validation evidence. A mocked opaque receipt display payload
is a transport fixture, not a fabricated accepted Core receipt.

| Log | Source attribution | Result / preserved finding |
| --- | --- | --- |
| `d07-comparison-frontend-first.log` | initial dirty Root integration; no immutable HEAD claim | 67 synthetic checks PASS; flags explicitly native=false/rendering=false/model=false |
| `d07-comparison-frontend-integrated-first.log` | integrated `034905ca` | full frontend verifier PASS, including strict TypeScript, request/schema checks and normal-hook exclusion |
| `d07-comparison-panel-first-red.log` | frozen `4da97ec8296329d2e990e95ff626aef065a699b5` | 1 PASS / 3 FAIL: pending edge/view and idle selection could retain/publish old query evidence |
| `d07-comparison-panel-corrected.log` | fix recorded in `32a5e3dd`; exact measured source-file hashes in log | 4 PASS / 0 FAIL |
| `d07-comparison-capability-first-red.log` | frozen `e04dd3e930aab0c2dadc6a0ada13a279f35b8482` | 0 PASS / 5 FAIL: capability loss retained private data; a failed new read retained an older receipt |
| `d07-comparison-capability-corrected.log` | fix `99531a3c61826fd420d3e562f8100df0798d7334`, exact file hashes retained | 5 PASS / 0 FAIL |
| `d07-comparison-query-selection-first-red.log` | frozen `d53a12157b72732e0302809a54dd9d454efa04cb` | 4 PASS / 1 FAIL: direct controller before/history query left panel controls after/knowledge |
| `d07-comparison-query-selection-corrected.log` | fix `38e6289610acf6eecb851ba1fcc22d061430c32b`, exact file hashes retained | 5 PASS / 0 FAIL |
| `d07-comparison-frontend-query-corrected.log` | post-query-selection integrated source `38e62896` | full verifier PASS; not a claim of 38 tests |

The capability correction clears private presentation on observed
UnknownEvaluationRun/Forbidden/Closed, while integrity failure retains only the
labelled last-validated summary and clears old evidence. Query selection is now
shared actual controller state. No assertion or privacy condition was waived.
The standalone logs carry exact source-file digests; where no process manifest
records a clean HEAD, this document does not invent one or command timing.

## Actual app-owned WebView cohorts

The application processes were hidden/unfocused and exercised the same frontend
controller and native IPC as the UI. Fixed scripted paired/rollout producers,
native picker doubles and real shared inspection were used. These are actual
native WebView2 renders, not headless mock images, and no real model was run.

| Cohort suffix | Source | Actual result |
| --- | --- | --- |
| `a86a377c-12e9-4d09-be39-a4d7fa3f72d5` | `a6f9eb4d` | initial process exit 1 after 4 checks, failed `comparison-open-capture`; 0 PNG, restart not run |
| `bd2bc132-3ec6-4ffa-8c79-10a83feed320` | `99531a3c` | initial process exit 1 after 15 checks, failed `mira-actual-known-private-fact`; 3 PNG, restart not run |
| `bbc74652-b6c0-4790-b311-76921cd3f446` | `6c2caf2ac3df79777bff7449399c5cebdbee8780` | initial and restart exit 0; 50 check entries and 13 PNG each; 100 entries / 26 PNG overall |

All three prefixes are `comparison-reader-native-` under `<artifact-root>`.
Their execution records report no timeout, no output overflow and null exit
signals. The first failure's report did **not** capture a failure category.
Root's diagnosis was a 222324-byte full report plus 626-file inventory exceeding
the 256KiB harness snapshot cap. The bounded semantic projection correction
`6a8e181850316bdbcd7acd0f5904681261e34de6` did not raise that cap or truncate
the live reader's actual report as if it were complete.

The second failure was an incorrect harness oracle: it expected Mira to know a
player-only seed fact. Rust correctly withheld it. The corrected checks require
Mira's actual witnessed dialogue, Sable's lack of that unseen dialogue, both
NPCs' lack of the player-private fact, and the Player lens's own original seed
knowledge. The failed cohort remains intact; it is not relabelled a privacy pass.

The completed 6c2 cohort records fresh scripted paired and rollout fixtures,
actual accepted receipt/capture/output inspection, actor transitions clearing all
raw presentation, native raw-actor denial, before-state Player knowledge,
guard-only no-receipt behavior, close/late picker suppression, deliberate lost
acknowledgement and SAME-client recovery, surrounding-context retirement and
unchanged live synthetic gameplay canon. Hash equality covers **626 original
fixture files** after initial inspection and again after process restart. These
are 100 check entries, not 100 independent fixtures or a model-quality score.

| Completed 6c2 execution | UTC start → end | Elapsed | Exit |
| --- | --- | --- | --- |
| frontend build |06:39:12.996 →06:39:13.398 |0.402s |0 |
| native dev-harness build |06:39:13.399 →06:39:25.750 |12.351s |0 |
| initial actual application |06:39:25.750 →06:41:27.894 |122.144s |0 |
| restarted actual application |06:41:28.178 →06:42:17.121 |48.943s |0 |

Each completed app report contains exactly one expected `{source:"native",
category:"Transport"}` error from deliberately lost opening acknowledgement.
It is not an empty app error buffer. Both apps retain 115 bytes of Chromium
stderr: `Chrome_WidgetWin_0` unregister error 1412. Earlier failed applications
also retain 115 bytes with that diagnostic. No zero-native-stderr claim is made.
Fixture creation is scripted; flags such as `modelExecution:false` and a
non-executing reader API are not numerical measurements of provider/role counts.

## Semantic and visual supplement remains pending

After the completed 6c2 run, Root found top-level snapshots mixed the live
gameplay `selectedStory` with an experiment revision. `pendingOperation` also
reported the last completed native operation ID as if it were pending. This
invalidates a claim that all old top-level semantic snapshots coherently describe
the inspected experiment, even though their nested evidence/IPC checks passed.

Source-only followups `e4f952af48c638d3ff55f4306d6a79cf26428a1c` and
`56650ebe64d496080252f7b5b4db956989ef2e11` add semanticVersion2: exact selected
experiment scope/report token and displayed edge revision, actual observer,
receipt/error, native pending operation only while running, unknown-ack pending
with null ID, and a separate live `gameplayContext`. They also check actual query
control values and add explicit wide/narrow raw-output and unknown-ack images.
The planned cohort is 15 PNG/stage, 30 total. It has **not** been executed in the
evidence supplied to this document. A read-only diff confirms these changes are
limited to the journey, fixed harness runner and dev artifact allowlist, with no
production UI/controller/native-reader behavior change after 6c2.

Root had viewed the three earlier bd2 images. During this documentation task,
the delegated image reviewer reported viewing all 26 completed 6c2 images,
finding no visible blocking layout defect and a minor adjacent Role/Inspect
header. Its first local manifest mistakenly had an empty image list; that
artifact is preserved. The corrected manifest lists 26 images, SHA256
`e32e9098288f1fdd89377ad5d4969fb0af2ad9773c1bb7d5358d3d59c0782d48`.
Root had not yet reviewed that corrected manifest at this update. This is
an attributed reviewer observation, not human approval or a cure for the known
semantic defect. The original manifest SHA256 is
`ac968d795d22bdfc6d4776515f169828ea062c7bd8c5c25d546c86e6ffba7969`.
This author read metadata only and did not inspect images. DOM overflow checks
do not replace visual review. Final raw-output layout and coherent
semanticVersion2 images remain required gates.

## Immutable evidence identifiers

SHA256 below hashes the actual retained bytes, not sanitized copies. Private
absolute paths contained within local process metadata are not reproduced here.

| Local artifact basename | SHA256 |
| --- | --- |
| `d07-native-reader-first.log` | `391c5a61ec60dd12c40250cec13d4b760a6ba66c93e235ca916775b605f64208` |
| `d07-native-reader-first-process.json` | `494c35d778c514f05b68b1bb277ea3d113cf834977f084379bbf92f6f1f22ad3` |
| `d07-native-clippy-first.log` | `f48c2443d90ea66c689335a6b37eae776c99336a7bf0455a349d01e97a9330fe` |
| `d07-native-clippy-first-process.json` | `53a47c16adf7881d25131a5fccdc6ba6d609aa3895d19608f76a23d0e47498d0` |
| `d07-native-normal-all.log` | `0d4868fa5559c7209796c0aa948e1640b2bf216c58ba7928e640e9543299ea26` |
| `d07-native-normal-all-process.json` | `02bda0494193a72f974b7fcd71a514028a284af288af81b201ace6f9a6be8be9` |
| `d07-native-development-all.log` | `716e4e0bcf3c47c5c757bb17beadbf84814f1cdb12d7957d9abdcc9432c6cc72` |
| `d07-native-development-all-process.json` | `d8cc666383c48f40dd0f4319c487229cd29b995e366cb18f1f6834c3408542c1` |
| `d07-comparison-frontend-first.log` | `80a735c1156fe4d668d98fbe690273563d764d339736949a878e0ff9e94cbce9` |
| `d07-comparison-frontend-integrated-first.log` | `16036abeb404a8c99bf2b97273b2ab312b6ee7fa6890ab06e01f076b9258d5b3` |
| `d07-comparison-panel-first-red.log` | `17bc799316b0cc7eafc0a2e985bbb1a80c34c8aec99bb5857e29c2687fa4e021` |
| `d07-comparison-panel-corrected.log` | `1f80e7f7011b98bfe73199e55e4e3d50435c50dc3f96e476d2172f6fd8406043` |
| `d07-comparison-capability-first-red.log` | `f5174297f31316a3178f7462c4cc892ad8dd7db801a72dd1e58a57e2069f15ee` |
| `d07-comparison-capability-corrected.log` | `7cfd399b9b705c16d5e62679a3648ec0c95fb688368206e8c12aa6e87bf6e19b` |
| `d07-comparison-query-selection-first-red.log` | `afc8c7e65819a9600c33c2df413cf3fe08f5db43838c7ecbff2cac8e2744e8f8` |
| `d07-comparison-query-selection-corrected.log` | `200452b5d1841b861e3ad525a74820619492a9c8f0eb21f7a83f94b75e66ab68` |
| `d07-comparison-frontend-query-corrected.log` | `32a1137ae707f7d06eedf39e686a5a34a4948152b5e4248cedc350ce4e1348ed` |
| `d07-comparison-native-harness-first.log` | `a083b2765a59a7784272b71cf62a87732c902d4a14aea568a44ad81867d8ae63` |
| `d07-comparison-native-harness-bounded.log` | `a083b2765a59a7784272b71cf62a87732c902d4a14aea568a44ad81867d8ae63` |
| `d07-comparison-native-harness-query-corrected.log` | `a661fd2341e21096efa199f24446beff040be6e368dce8582d63414be33651e5` |

The first two harness runner logs have identical bytes/SHA despite different
cohorts. Distinct cohort `executions.json` and `initial/report.json` bind their
different failures:

| Cohort suffix / file | SHA256 |
| --- | --- |
| `a86a377c…/executions.json` | `4bf20a75943724b566064002a5aeaa904a5bf31d2a81cf987e1b8765980acf91` |
| `a86a377c…/initial/report.json` | `3b0d2c6388d711d13782acbaa865efba591f1c92748a4ece35e29b5ce3e9346e` |
| `bd2bc132…/executions.json` | `d454a58e8c9a6545f8a129d667924eaae37d211deabae8b0729729bb52462fa6` |
| `bd2bc132…/initial/report.json` | `f370915c0ca0ab6dc2b8ae81e5a19019449d443d8dbd7e76105b3cb183d1e2f6` |
| `bbc74652…/qualification.json` | `abfe37c2724b47811d8ade873c1a43f15fe27726415d2e56b0a97bd976258157` |
| `bbc74652…/executions.json` | `380953e713c5e1e38a7c173e853708ee9ce498068205b1673e58f52d0ecd7b7e` |
| `bbc74652…/initial/report.json` | `609f9a986d5a472ca81810de09d703b6c08625b2fb2ccac046911dadb5db3f53` |
| `bbc74652…/restart/report.json` | `a76aca431219b71ef9dff4076738a1de5592b22ebc4f0de932a725f5c390f567` |

Completed 6c2 qualification binds executable SHA256
`3ede891e8203f48cc0c6c3b302c8673b0945c640e89c47b182d53e59f9db49de`,
frontend `dist/app.js`
`29cb264b4ea0518a7c62dbfb2f7ed4be9f5d875c7a21c2f301adb1b85aaf55a6`,
model TS `f1c35edb8582866c25dec9857e7568e3aa9e9fea039b57b825a019fa6baff533`,
controller TS `417d1f19ae968d7b7e12ac94227f8d117cf31e3d10318366cde45c07cfa11bd3`
and panel TSX `f8a75a4e76bd1ae39e859dc68aa0c5c7b7e6672ecd0054a7e700c30eee7e34d8`.
The manifest retains the complete source-file and 626-file fixture inventories.
These hashes belong to 6c2's harness build, not an unexecuted 566 or release build.

## Completed Android compatibility followup

This supplements the initial document commit `ffbd8362`, which correctly left
the fresh Android work pending at its handoff. All three completed stage records
now bind exact source `56650ebe64d496080252f7b5b4db956989ef2e11`, initial clean
source and `terminalSourceUnchanged:true`; no result is relabelled as another
source. The runner refuses an existing `d07-reader-android-build` directory;
this output root was absent before invocation. Existing SDK/Java/Gradle caches
were reused, with SDK downloads disabled, one Gradle worker and no device.

Root's Android **host Rust** stage at exact `56650ebe` completed during this
documentation task: `cargo test -p locallore-android --locked --offline --jobs 1
--target-dir <task-root>/d07-comparison-reader-native-target -- --test-threads=1`
passed 90 tests across 18 result summaries, including three zero-test groups
(including documentation tests). Build 34.51s; no failures, ignores or filters.
The clean/unchanged stage ran 06:48:54.4581618Z–06:49:49.1978849Z. Exact log
`d07-reader-android-fresh-jni-host.log` SHA256
`4f051a3afa87125c42b9fc5706e868706e642156773f7258d2d580e977cc6f4b`;
runner `d07-reader-android-check.ps1` SHA256
`f0084c73e69c6b19422df423763cc07fefe76eb3fe5c0361a623e9d624f3d947`.
Individual result durations in log order are 1.65/.09/.53/.60/1.26/.97/.68/.69/
.30/.94/0/.09/2.91/0/1.12/.15/3.39/0 seconds. This is host Rust compatibility,
not Android device/JNI execution.

The Gradle stage ran 06:49:49.3097783Z–06:57:52.3953936Z, exit 0. Its own log
reports **BUILD SUCCESSFUL in 8m 2s; 81 actionable tasks, all 81 executed**.
The two actual Rust Android release builds finished in 2m48s and 2m35s. App and
instrumented test APK assembly, JVM tests and lint all completed. A read-only
parse of the fresh 24 JUnit XML files found **206 tests, 0 failures, 0 errors,
0 skipped**. These counts belong to host JVM tests, not instrumented execution.
The nine `ArchiveV3WireTest` platform JSONObject/Compose methods compiled into
the instrumented APK only; neither those methods nor other androidTest cases
were run on a device or emulator.

The existing Kotlin warning remains in the log at
`FrameworkInterruptionTest.kt:128:50`: `AtomicReference` identity equality with
`Boolean?` may be inconsistent. It is retained as a warning, not concealed or
reclassified as a new test failure. No warning-related source change was made.

Exact Gradle reproduction from `<source>/apps/android`, with the already
installed Android Studio JBR and SDK, existing `<task-root>/gradle-home`, and
the retained output init script:

```text
<android-studio-jbr>/bin/java.exe -classpath <source>/apps/android/gradle/wrapper/gradle-wrapper.jar org.gradle.wrapper.GradleWrapperMain --offline --no-daemon --max-workers=1 --console=plain -Pandroid.builder.sdkDownload=false --init-script <artifact-root>/d07-reader-android-output.gradle :app:assembleDebug :app:assembleDebugAndroidTest :app:testDebugUnitTest :app:lintDebug
```

The init script maps each project to a task-owned build directory beneath
`<task-root>/d07-reader-android-build`; it does not change tracked sources or
global Gradle configuration. The APK audit ran from repository root:

```text
python scripts/audit_apk.py <task-root>/d07-reader-android-build/_app/outputs/apk/debug/app-debug.apk
```

Audit exit 0 at 06:57:52.4999346Z–06:57:53.1891756Z. Its JSON reports status
`passed`, the sole permission
`org.locallore.app.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION`, and four native
libraries: `libandroidx.graphics.path.so` and `liblocallore_android.so` for each
of arm64-v8a and x86_64. Each reported ELF LOAD alignment is 16384 bytes (16KiB).
This is the audit's bounded manifest/library result, not Android runtime evidence.

| Fresh completed artifact | Bytes | SHA256 |
| --- | ---: | --- |
| App debug APK | 24308076 | `210d6a42ad2c4150e841b9e4760878d903e5eea563a2b6ce3f85cf3f867de942` |
| Instrumented test APK | 1847971 | `6782e0466bc6137a3df3e401fdfe6b14c6fc1f0dfaf95147d93346cadf516d6e` |

Both APK hashes match the separately recorded accepted Archive3 source65 and
its fresh build in
[Archive3 qualification](../storage/M08_ARCHIVE3_COORDINATOR_QUALIFICATION_2026-10-23.md).
This is an observed local byte equality for these particular artifacts. It is
not generalized reproducibility, release approval, Android runtime or parity
qualification.

| Completed local evidence | SHA256 |
| --- | --- |
| `d07-reader-android-fresh-jni-host.log` | `4f051a3afa87125c42b9fc5706e868706e642156773f7258d2d580e977cc6f4b` |
| `d07-reader-android-fresh-gradle.log` | `fa28ef1fcdb7d50b0bad14e210f302371d37ebe4ec745f95c1e25b37bc0715ba` |
| `d07-reader-android-fresh-apk-audit.log` | `a2220741ab7d3170dc6f144e8b0c0d97b3b85457ef46d7bf0d6e0c76a8cef49f` |
| `d07-reader-android-fresh-results.json` | `f815e9c32de4d09d9fa85c41c7b9c42360ad88abd0a94ece86794cbc45e0ff9a` |
| `d07-reader-android-output.gradle` | `9fad5748edfbbff709379551841c7a1446727c4b4eb1426d6a92a0c0673139a4` |
| `d07-reader-android-check.ps1` | `f0084c73e69c6b19422df423763cc07fefe76eb3fe5c0361a623e9d624f3d947` |

The results file is now terminal for all three stages and hashed as such; the
earlier mutable progress file is not used as immutable qualification evidence.

## Remaining gates and next runnable work

No phone/emulator, Android device/JNI runtime or desktop/Android semantic parity
result is inferred from the completed compatibility work. Final
normal frontend/executable restoration and any later strict/broad checks need
their own exact source and logs; the earlier normal verifier is not a claim
about the current dev-harness executable.

Root's semanticVersion2/30-PNG native cohort at source566 was running during
this Android followup. No terminal result has been supplied or inferred here.
Next: finish that immutable cohort, inspect all final actual PNGs,
record bounded errors and exact hashes, and update PR #157's reviewable evidence.
Selected-case rerun and comparison execution remain explicitly unavailable;
reader recovery is in memory and process restart requires explicit source
selection. Access-time expiry is not a wall-clock lock-release guarantee.
Source matching permits inspection, not execution or model-quality approval.
No real model, hosted judge, downloads, user-private story or protected chat was
used in these checks. D07 and its human-review/quality/selected-execution gates
remain open.
