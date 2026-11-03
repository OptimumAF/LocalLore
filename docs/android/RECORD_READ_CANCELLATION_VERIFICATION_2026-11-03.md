# Story-record cancellation verification

B109; Refs #14 (M10.02), supporting #13 (M09.04/M09.06).
Implemented and locally verified; in review, full criteria unchecked. No merge
or owner acceptance. Standalone base is main `752e0b068742836c489ba86165733c0aff437d59`.
Executable commit `07c2e9da1a993eca81cf6b12df33f414a3148073`, source tree
`45a66ac1798c1945d8ff0ef171d48f31aedfe94a`; later reporting is documentation only.

## Reproduced behavior and fix

A current fake reader throwing `CancellationException` left a page or event
detail loading, without the Retry action. Close/reopen, section change or Back
were still escape routes. A reader could also cancel its request job and return
otherwise valid data without another suspension; that data was published.
These are executed coroutine/reader-boundary faults, not an observed native
reader or device cancellation failure.

The controller now registers a lazy read before starting it, checks coroutine
activity before the reader and after return, and handles cancellation completion
even before coroutine entry. Completion only queues a finite state settlement
on the inherited owner dispatcher. The settlement survives parent cancellation,
rechecks request generation/disposal/loading and clears only its own pending
identity. It performs no read, retry, IO or gameplay action. Request cancellation
still propagates. Current cancellation exposes the existing safe UNAVAILABLE
problem; page retry keeps the frozen query/cursor, and detail retry keeps the
exact current-player-lens scoped reference and accepted underlying page.

Native visibility, provenance validation, canonical history, knowledge/truth
distinctions and stale-response fences are unchanged. No engine/schema/JNI,
inference, model, permission, dependency or runtime-version change. See the
[read cancellation contract](RECORD_READ_CANCELLATION_V1.md).

## Actual checks

Commands ran from the physical D: candidate, TEMP/TMP `D:/Dev/_Temp`, using
installed Java21.0.4, Gradle8.11.1, AGP8.10.1, Kotlin2.2.21/coroutines1.10.2,
existing SDK36/NDK29.0.14206865 and Rust1.93.1. Existing D: Gradle/Cargo caches,
offline mode, disabled SDK/toolchain downloads, in-process Kotlin compilation
and two Gradle workers were used. No new dependency selection/download.

Private `python -I -S -B <OUT>/run_owned_v2.py <phase>` used the separately
reviewed checked host owner from PR #361, exact runtime blob
`64cde2f5c014b01798cd7e945e3bd592434a5993`, SHA256
`51e94325ed5e59a31c64fcc274e7a41c40b9dd969b09d39df7be56b0ee941598`.
This is a host-test controller dependency, not an app change or PR prerequisite.
Each operation had an unchanged 180-second owned-job limit and checked cleanup.

| Phase and actual Gradle work | Result | Capture / owned elapsed |
| --- | --- | --- |
| red-v2: `:app:testDebugUnitTest --tests org.locallore.app.StoryRecordCancellationTest` against unchanged consumer | 9 tests, 7 assertion failures, 2 stale-response controls passed; 0 errors/skips | 100.364 / 100.655 s |
| green-v1: same nine methods, unchanged test bytes | 9 passed, 0 failures/errors/skips | 37.003 / 37.300 s |
| regression-v1: `:app:testDebugUnitTest` | 422 tests / 49 suites, 0 failures/errors/skips; includes 411 baseline + 11 new | 25.984 / 26.283 s |
| package-v1: `:app:assembleDebug :app:assembleDebugAndroidTest :app:lintDebug`, then two actual APK audits | both APKs built; lint 0 errors, 1 warning/1 hint; product structural and instrumentation-pair audits passed | 71.308 / 71.609 s |

Both successful JVM test tasks actually executed; incremental native/build tasks
were reused where Gradle reported up-to-date. Red built both Rust JNI ABIs; APK
audits inspect x86_64/arm64-v8a packaging and ELF alignment, not device execution.
The lint warning is GradleDependency (coroutines1.10.2); the hint is
AutoboxingStateCreation, in unchanged source. Neither was suppressed.

Nine original independent methods cover current page/detail cancellation with
exact explicit retries, queued-child and cancelled-parent cancellation, unrelated
parent/sibling survival, obsolete page/detail completion, and cancelled readers
returning valid data. FIRST test SHA256 remains
`1f6d4dfb7f1a4134e06051aeda4f7a8054eb463ac84a093b30f7850bfcfd4518`
(17,510 bytes). Two additional coordinator methods explicitly assert that page
and detail request jobs remain cancelled after settlement/retry and exercise
immediate owner dispatch completing cancellation before the helper returns.
The 9-method green and 422-method regression are overlapping cohorts, not 431
unique tests. Independent source/oracle and saved-result reviews found no blocker.

Source maps agree before/after each phase: RED/GREEN2,583 files; regression and
packaging2,585 files. Common executable/test files match across successful phases.
One later contract sentence was corrected for precision before packaging; no
FIRST test assertion or production code changed after green. The two supplemental
ownership methods were added after that nine-method green and ran in full regression.
Final report is added
after testing. Normal checkout8924278c and its index remain preserved.

## Artifacts, preserved failures and limits

Product APK: 28,012,664 bytes, SHA256
`47b74e97b94cace7ac6f32d82c49b6d1665c66d508803f65d505e2b95d6e5c18`.
Instrumentation APK: 2,263,236 bytes, SHA256
`3980edd3ca42f364717a4ade1d1fd8e2e300078542fd89121f6098f7b2b6c3b8`.
Raw logs, XML, source maps, original private proposal artifacts, APKs and failed controls
remain private under the D: experiment/recovery namespace
`2026-11-03-record-read-cancellation-v1`; these artifacts are not uploaded with this
report. The integrated synthetic JVM test source is published in the PR.

The first red-v1 build failed before tests because default Cargo home lacked an
existing locked dependency. Setting process-local CARGO_HOME to the existing D:
cache fixed it without fetching/changing dependencies. That setup attempt used
the older unchecked host owner; only later actual test/build operations use the
checked owner. The failed setup remains failed and receives no JUnit credit.
Intermediate worker versions were reconstructed from retained initial bytes and
exact edits, then matched byte-for-byte to original launch SHA256 pins; their
reconstructed attribution is retained. An initial publication preflight inspected
the empty alternate index instead of the normal index and refused before writing
a tree/ref. Its corrected normal-index check passes; originals are preserved.

Generated Android output measured 648,588,530 bytes after packaging, below the
2 GiB planning bound. That is post-run accounting, not a continuously enforced
quota; selected ordinary source/evidence/recovery is separately bounded at256MiB.
Tool paths/versions are recorded; this packet does not claim a fresh complete
installed-tool fingerprint or CI pass. No emulator/ADB/SDK-management/phone/model
operation, storage-ledger change, image retirement, other-emulator stop, system
setting, merge or release occurred.

Compose device execution, native cancellation/resource qualification, physical
phone/ARM64/model/privacy/performance and full M10.02/M09.06 acceptance remain
open. The pending retirement proposal grants nothing until answered, and another
boot requires separate exact approval/admission. Next runnable supporting task:
add/compile a Compose cancellation-recovery case against this reader interface;
actual UI execution waits for admitted capacity and fresh run authority.
