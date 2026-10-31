# Android player record Query2 verification

2026-10-31. Refs #13 (M09.04; supporting M09.03), #14 (M10.02).
This is a host-verified implementation slice; full tasks and owner acceptance
remain open. Base is unmerged PR298, exact
`facaa2b7c74ac6e825c6b06935edeb3f02477758` (`impl/m09-promise-records`).
It does not qualify newer main or the independent authoring/presentation stack.

## Behavior and authority

All five Android story-record sections now request existing native Query2.
The original four retain explicit Query1 compatibility; Promises is Query2-only.
Corrected Domain2 histories no longer fail because the consumer used Query1.
An authored seed alone is Domain1; the corpus applies real correction for Domain2.

The gateway captures actual player identity from its existing successful native
play-snapshot binding. It checks attachment epoch, session, scope, head and
binding before and after inspection. Missing binding refuses before inspection
IO; observer/attachment/head/close drift discards a captured read. Production
passes that bound actor explicitly to the decoder, without assuming literal
`player` or inferring identity from rows.

Known-as-observed facts remain observations, distinct from canonical truth,
beliefs, statements and discoveries. Unseen correction leaves prior knowledge
intact; actual native rediscovery changes it. The exact two-field correction
marker displays a history notice without private key/reason, invented witness,
event, source or navigation. Typed sources retain original story/branch/sequence.
Evidence opens only an eligible current reference through the same frozen
player lens; no ancestor session, flat fallback or privileged observer.
Query2 message IDs additionally require native ascending order.

Kotlin computes no truth, promise status, source eligibility or gameplay outcome.
No native backend/schema, dependency, runtime/model pin or lockfile changes.
See the [frozen contract](RECORD_QUERY2_CONTRACT_2026-10-31.md).

## Independent inputs and retained failures

Separate D: worktrees produced the Rust corpus example and FIRST JVM tests.
Root owns production integration/contracts. A third agent reviewed source and
fixture migration without running builds, tests or device commands.

The example calls the real engine and Query2 on root, corrected, rediscovered,
authored and authored-corrected synthetic histories (domains1/2/2/1/2).
Literal and materialized opaque player IDs, all five views and actual pagination
produce 40 pages. Canonical bytes, records and projection basis remain unchanged
by inspection. Private NPC/reason canaries are excluded. No model/provider runs.
Output including newline is **95,156 bytes**, SHA256
`afecedc44f77079115482e07c37bb6e359239b499bc9f820d6f94c20ee06b9b3`.
The committed JVM resource is exactly that output. A Clippy-only bound-expression
fix produces byte-identical output; the 128 KiB bound is unchanged.

All 15 independent FIRST tests compiled and failed assertions on the original
consumer. Production first passed14; the remaining test exposed descending
scoped-message IDs being accepted. The Query2-only fix passes all15 with the
FIRST file unchanged, SHA256
`b396f92bdf17f8068a5c0b0724fb278e7a5711c0b02b1253419506f81c694c9a`.
They cover real gateway ownership/opaque identity, malformed framing, cursors,
scoped sources, correction privacy, exact same-lens drill-down, cancellation,
stale/late results, dismissal and disposal.

The first full gate ran380 tests with10 old-fixture failures: five controller,
four view-model, one explicit-legacy promise. Its43 XMLs are retained; APK/lint/
audits were not reached. Six existing test files were migrated independently to
scoped references/explicit Query1 controls, including three instrumentation files.
All43 original method names/order and privacy/late/invalid assertions remain.
Review matched retained original hashes to the failed run. Instrumentation was
compiled, not executed. The initial Clippy `int_plus_one` failure is retained.

## Commands and actual results

Final executable **`5380c812facbc0dffb2d5443dda09cca267523c7`** adds only the
six fixture migrations after production `2fae38ce8a2c967edcdca23555a8d59b25e9a934`
and example style fix `bc6427aee27f5c41d23ad5da5ddd51d40a6e61ac`.
Later reporting edits are documentation only. Commands ran from physical D:,
offline, with Rust1.93.1, installed Java21/existing SDK, downloads disabled.
No dependency/compatibility selection is introduced.

```text
cargo +1.93.1 run --locked --offline -p locallore --features host --example android_record_query2_fixture
cargo +1.93.1 test --locked --offline -p locallore --features host --test inspection_query --test m08_query_v2 --test m08_query_v2_message_identity_review
cargo +1.93.1 clippy --locked --offline -p locallore --features host --example android_record_query2_fixture -- -D warnings
cargo +1.93.1 fmt --all -- --check
python -I -S -B scripts/check.py android --archive-verification --offline
```

Focused JVM command from `apps/android`, installed Java and verified wrapper:

```text
java -classpath gradle/wrapper/gradle-wrapper.jar org.gradle.wrapper.GradleWrapperMain :app:testDebugUnitTest --tests org.locallore.app.Query2StoryRecordTest --no-daemon --console=plain --max-workers=2 -Pandroid.builder.sdkDownload=false -PlocalLoreArchiveVerification=true --offline
```

| Cohort | Source prefix | Result | Owner elapsed ms |
| --- | --- | --- | ---: |
| native-corpus-v1 | 815f9515 | exit0; 40 real pages | 12,799 |
| jvm-first-v1 | 397dc90f | 15 assertion failures/15, zero errors/skips | 180,891 |
| jvm-first-v2 | 11e019c8 | 14 pass, one ordering failure | 37,496 |
| jvm-first-v3 | 2fae38ce | 15 pass | 24,059 |
| android-v1 | 2fae38ce | 370 pass, 10 fixture failures | 17,147 |
| native-queries-v1 | 2fae38ce | 32 named pass: 16/10/6, none ignored/filtered | 2,187 |
| clippy-v1 | 2fae38ce | exit101; example bound style | 5,115 |
| clippy-v2 | bc6427ae | exit0, warnings denied | 771 |
| fmt-v1 | bc6427ae | exit0 | 2,287 |
| native-corpus-v2 | bc6427ae | exit0; identical output | 1,883 |
| android-v2 | 5380c812 | 380 pass/43 fresh XML; builds/lint/audits pass | 57,200 |

Durations include host supervision/cleanup, not just tests. The380 includes
FIRST15; totals are not additive. Final gate executes `testDebugUnitTest` and
`lintReportDebug`: zero failures/errors/skips, lint zero errors/one existing
warning/one hint. Both APKs assemble; public product/pair audits pass. Both ABI
build invocations pass, reusing unchanged release objects (Cargo0.18/0.17s),
not fresh recompilation. Four packaged libraries pass16,384-byte ELF LOAD checks.

| Isolated artifact | Bytes | SHA256 |
| --- | ---: | --- |
| `org.locallore.app.archiveverify` | 27,756,156 | `a0d8fe2a0c172354229d6e9061c41aa25821decbf15e3ad140917ec3c6d92df3` |
| `org.locallore.app.archiveverify.test` | 2,226,591 | `fb5b93d969796f380b2e71ee7bdbff519af597ded046c5ea40e194101b6fd1a7` |

Pair audit permits only `android.permission.REORDER_TASKS` on the test APK.
The46 sealed success files contain both APKs,43 JVM XMLs and lint XML.
No ordinary-profile build, whole-workspace regression or hosted CI claim.

## Private evidence, storage and limits

Private root: `D:/Dev/Experiments/LocalLore/2026-10-31-record-query2-v1`.
Every closed cohort joins actual child, source map, helper, command, per-job/
global admission and owner captures. Recorded source/helper/admission checks
pass, cleanup/capture are known, no unexpected meter errors or unknown worker
outcome. First corpus has2,335 inputs; later cohorts2,337. Raw controls stay local.

Host budget:8 GiB, stop7 GiB, across three owned worktrees, experiment/recovery
and owned temporary root. Forecast1.5–4 GiB was conservative: final gate measured
946,960,062 bytes before artifact sealing, with246,784 bytes owned temporary output.
Create-only selected recovery, raw cap256 MiB, is retained privately at
`D:/Dev/Recovery/LocalLore/2026-10-31-record-query2-v1`; ticket handoff records
actual seal/readback. Originals, failed captures and targets remain. Shared
caches/Git metadata are not fully attributed; not peak usage or an OS quota.

No emulator, phone, ADB, app install, model transfer or inference action ran.
No AVD ledger, other emulator, shared service or system setting changed.
Current Android/JNI UI execution, touch/accessibility, process recreation and
causal OS-death are unverified. M01.01/M01.02/M10.05 device/model/performance
gates stay blocked/unverified; no ARM64 execution, privacy, story-quality or
release-readiness qualification. No merge/release.

Next runnable verification: current-source guarded inspector/UI preflight;
execution needs fresh applicable boot authority and storage admission.
Historical different-APK UI results cannot qualify these artifacts.
