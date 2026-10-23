# Retained-parent deletion verification, 2026-10-23

Refs #12 (M08.05, supporting M08.01/M08.04/M08.06) and #8 (M04.04 follow-up).
Implemented and locally verified, pending owner acceptance. Source
`3c5cfba` incorporates current main `884cf3f`; no PR was merged by this packet.
See the [contract](PARENT_RETENTION_CONTRACT.md),
[ADR-0009](../adr/0009-retained-parent-deletion.md),
[structured results](PARENT_RETENTION_RESULTS_2026-10-23.json) and
[independent review](PARENT_RETENTION_REVIEW_2026-10-23.md).

## Implemented behavior

Deleting a nonroot timeline retires its playable ID while preserving the
original accepted prefix required by active children. It prunes unreachable
tail/drafts/derived data and recursively collects unneeded retired ancestors.
Public reads, writes and cached retries reject retired targets; private ancestry
replay preserves original receipt scopes. Native invalidation fences only
retired/collected sessions, including actual running generation. Retained child
and sibling owners remain usable. Root deletion remains whole-story deletion.

Schema3 uses backed-up exact-schema migration and persistent reserved IDs.
Catalogv2 validates the original graph before filtering playable choices.
Archivev2 transfers retirement state and required prefixes atomically; legacy
v1/source-schema1/2 imports remain supported. The Compose shell captures a native
preview before confirmation and reconciles saved state after completion or
uncertainty. Story Record, text and timeline callbacks share the deletion fence.
No production dependency, model/runtime or network capability was added.

## Checks actually executed

Environment: Windows, Rust/Cargo1.93.1, Java17.0.6, Gradle8.11.1,
AGP8.10.1, Kotlin2.2.21, compile/targetSDK36, BuildTools35.0.0,
NDK29.0.14206865. Device aliases A/B identify two authorized, already running
API35/x86_64 emulators with4096-byte OS pages. No physical phone was tested.

| Command or procedure | Actual result |
|---|---|
| `python scripts/check.py host --offline` | 380 Rust workspace passes, 3 linker passes, 352 Python tests; four generated fixtures match; fmt and strict Clippy pass |
| `cargo test -p locallore-android --features play-probe --locked --offline` and matching all-target Clippy | 69 passes, zero failures; strict Clippy passes |
| Dedicated Gradle build/test/lint | 146 JVM passes, zero failures/errors/skips; lint0errors/1existing dependency advisory; both ABIs and test sources compiled |
| `python scripts/check.py android --offline` | Ordinary build,146 JVM passes, lint and APK audit pass; ordinary APK not installed over existing saves |
| `npm ci --offline`, `npm run check` from `apps/desktop` | Locked cached dependencies restored; frontend/schema/TypeScript/controller/privacy/lifecycle checks pass |
| Dedicated/ordinary APK audits | Both native ABIs,16KiB ELF LOAD/ZIP alignment, eleven archive JNI exports; no fixture96/test-provider manifest/INTERNET capability in product |
| Configuration refusals | Ten invalid value/cache/mixed verification or capacity/release configurations rejected before a build |
| Latest focused A/B | 22 passes each, zero failures/skips/unfinished methods |
| Corrected regression A/B | 26 passes each, zero failures/skips/unfinished methods |
| Preservation/cleanup | Thirteen pre-existing installed package APK identities preserved; owned processes absent and all bounded clients terminal after every cohort |

Two existing Rust entries remain explicitly ignored: the96-page qualifier
requires its separate compiler profile, and an IPC worker is invoked by its
parent-owned interruption tests. Neither is counted as a pass. Existing
instrumentation compilation also reports the prior nullable-Boolean
AtomicReference advisory; it is not a new runtime result.

The Store tests exercise prefix preservation, multiple descendants, nested
rewind before a parent's birth, recursive collection, reserved-ID reuse refusal,
stale consent/ABA/database replacement, cancellation, malformed history, SQL
abort and rollback. Archive tests cover v1 compatibility, v2 normal form,
collected IDs, byte/canonical/context equality, hostile versions/graphs and
transactional interruption. Migration tests cover exact schema1/2 copies,
backup identity/WAL content, refusal, rollback and read-only historical opens.

The Rust running-worker test observes two actual Host workers and both Running
statuses immediately before deletion. The parent returns Closed; the child
finishes Ready, preserves its old canon until commit, then commits/retries once.
The JNI counterpart observes the same Running overlap on both emulators and
reacquires all four workspace and archive slots after cleanup. These are actual
synthetic-provider workers, not delayed delivery of an already finished reply.

The ComponentActivity journey imports an original Store-produced fixture:
root4, parent born2/head5, child fork4, rewind fork1 and independent sibling1.
It verifies included shared parent speech and excluded tail speech, cancels
consent, confirms retained parent cap4, rejects a stale parent selection,
reopens owners, continues the child independently, and exports/imports actual
v2 through native staging while the parent remains unplayable. An unrelated
story stays intact. Actual MainActivity separately exercises product factory,
selector and own-story create/delete/recreate while preserving prior stories.
Its final runs start nonempty; they do not establish a fresh empty MainActivity
startup. Isolated ComponentActivity/protocol checks exercise empty libraries.

## Artifact bindings and reproduction

All96 latest product passes use application APK
`9a68c915ce963a38a5a0beeafbc7465ff4d8c28b65953457b3a8beeb45aa6d17`.
Focused44 passes use testAPK `4a4ece0e4fbc76ea34b59204755897b97bbd6ad269156135e5cdd92f3d5f4c3e`;
regression52 use `6fa5ea0703aabee5b0d783a57f44c5986a240ce0c57cb3c02fa4930975848889`.
The only source difference between those test builds is one legacy imported
database-schema assertion changed2→3. Application APK and both Rust libraries
are identical. The ordinary146 JVM/build/audit run preceded that last test-only
assertion; it does not claim executing ordinary instrumentation.

From `apps/android`, build the isolated pair:

```powershell
.\gradlew.bat :app:assembleDebug :app:assembleDebugAndroidTest :app:cleanTestDebugUnitTest :app:testDebugUnitTest :app:lintDebug -PlocalLoreParentRetentionVerification=true --project-cache-dir .gradle-parent-retention -Pkotlin.incremental=false --offline --no-daemon --console=plain -Pandroid.builder.sdkDownload=false
```

This uses `org.locallore.app.parentverify`, `app/build-parent-retention` and
its exclusive project cache. Install only the isolated pair on an authorized
target. Use AndroidJUnitRunner with the following class inventories; set the
authorized target explicitly and retain raw method starts/ends and terminal
runner status. The private wrappers use the repository's bounded client and
strict instrumentation parser, not ADB exit alone as a pass.

| Cohort | Classes and exact method counts |
|---|---|
| Focused22 | ParentRetentionNativeTest1, ParentRetentionProtocolTest3, ParentRetentionActivityTest1, TimelineNativeTest1, TimelineProtocolTest5, TimelineActivityTest1, TimelineMainActivityTest1, StoryDeletionActivityTest1, StoryDeletionMainActivityTest1, DurableDeletionRecoveryTest7 |
| Regression26 | ArchiveIntegrationTest6, ArchiveDocumentTest5, ArchiveDialogTest6, DurableNativeTest5, ArchiveActivityTest2, ArchiveChooserActivityTest2 |

All classes are in `org.locallore.app`; the runner is
`org.locallore.app.parentverify.test/androidx.test.runner.AndroidJUnitRunner`.
The synthetic fixture producer is the `parent_retention_fixture` Rust example;
its unit test compares the packaged archive byte-for-byte and validates its
heads. Generate only to a new explicit output path.

Raw build/host logs, XML, bounded-client journals, APK ledgers and143-file source
bindings are retained privately under `target/checks/parent-retention`; the
public JSON contains aliases/counts/hashes. Fourteen nonordinary local APKs
were unchanged through the ordinary final build; the later deliberate fix3
test-APK rebuild is recorded separately. Existing installed data was not
cleared or uninstalled. Synthetic test roots are retained. Earlier task-generated
outputs were moved intact to another host volume with original-path junctions
and identity ledgers when system-volume storage was exhausted; unrelated work,
model files and AVDs were preserved.

## Retained failures and review corrections

The private evidence and JSON retain all attempts; earlier passes are not added
to the96 latest product passes.

1. Initial Store/catalog and derived-store tests found old catalog/schema
   expectations. The first full host run also found historical archive goldens
   reporting source schema2; these goldens remain unchanged. Comparison now
   validates both archives and permits only source-schema metadata/checksum
   evolution. A later host run found whole-story previewv1 expectations after
   the table-list change; expectations now requirev2/ten tables. A fmt gate
   caught the new fixture producer before the final host pass.
2. Initial native tests used arbitrary narration and then an unsupported Open
   field. Fixtures now use actual Engine narration and exact command fields.
   The running-worker test first failed compilation for an owned archive/API
   and Serialize assumption, then passed its behavioral assertions but failed
   Windows directory cleanup while a test-held Arc still owned SQLite. Dropping
   that test lease fixed cleanup; the final test and full host pass retain the
   same overlap/commit assertions.
3. Archive author checks caught a forbidden Receipt-deserialization assumption
   and a lint issue. Review found retired projections must not be imported;
   the fix and regression were integrated before host/device passes. A Store
   memory fixture used Wait without observable speech; it now creates the
   original Say evidence it asserts. Original failures remain in author logs.
4. After main integration, the UI regression reproduced a live Story Record
   overlay during branch consent. Dismissal plus noncooperative late-result,
   text/head and empty-library regressions pass in the146-test suite. Reviewer
   identified JNI test cleanup gaps; the coordinator corrected them to always
   close archive ownership and preserve the primary failure, even if worker drain fails.
5. The initial A wrapper requested an unsupported240s process budget and was
   rejected before instrumentation launched. It has no raw instrumentation
   file. The existing180s bounded budget was restored, without changing product
   deadlines. Both initial focused runs then executed22:11pass/11fail from
   fakes missing the newly merged capability query, stale schema assertions and
   an empty-start assumption after a preceding test created a story. Corrected
   fakes and own-created-story preservation passed22 each. Each first regression
   run executed26:25pass/1fail at the final stale schema2 import assertion.
   Its test-only fix then passed26 each. Superseded cohorts total72passes and
   24failures, never counted as current qualification.
6. Initial frontend verification lacked installed locked modules and failed.
   Cached offline `npm ci` followed by `npm run check` passed; no lock or
   dependency version changed. Private helper formatting/path-spelling
   assertions were corrected without losing attempts or rerunning successful
   device tests for observation alone.

## Remaining gates and next task

The provider is explicitly synthetic. No physical phone, ARM64 execution,
real-model performance, thermal behavior or narrative quality is qualified.
The separate authorized model-copy experiment is in PR #84; its integrity and
host-storage blockers remain independent of these product results.

Retirement is logical deletion: retained inherited content, SQLite free pages,
private migration backups, VM/OS copies and external exports are not forensic
erasure. Checksums do not authenticate historical deletion intent. Other-process
scope admission fails closed, without a promise to scrub its memory immediately.
No hard replay CPU deadline or maximum-history latency is established. No
branch creation/rewind/retcon UI or complete M08 exit-gate acceptance is claimed.

Review identified a runnable M04.04 prerequisite for future storage qualification:
legacy32-page padding helpers require schema1 and the original001 baseline,
so they must refuse current schema3. The15-page gift ceiling is calibrated to
an older15→16-page transition; its current page budget is unmeasured. Neither
profile was requalified or relaxed here. Historical capacity results remain
historical. Next runnable work is an isolated exact-schema3 fixture/recalibration
packet preserving actual Full, rollback, owner cleanup and original-key recovery
criteria, before using those profiles to qualify further storage changes.
