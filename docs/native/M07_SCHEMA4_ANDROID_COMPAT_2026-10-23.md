# Schema-4 Android compatibility packet — 2026-10-23

M07.03/.04 prerequisite; supporting D08.06/.07 and D09.03. Coordinator-delegated `app_storage_review`, `impl/m07-schema4-android-compat` / `source-schema4-android`, accepted base `e534f01e107a48642370fa0a976fa25c747baba9`. Claims: #11 comment 6373348989, #30 comment 6373349285, #31 comment 6373349589. Status: **static implementation in review, execution pending**. This packet is not Android/device, archive parity, capacity or full M07/D08/D09 acceptance.

The coordinator owns the additive derived-only storage migration `004_memory_jobs.sql`, the Rust schema/version/adapter changes, job implementation and compatibility integration. At this base, the checked-out Rust owner still reports schema 3. Therefore these Kotlin expectations must be integrated with the actual frozen schema-4 owner before runnable native compatibility checks; they are not a standalone schema migration or a compatible APK paired with the old JNI binary.

## Narrow implementation

Only these six Kotlin files change:

| Path below `apps/android/app/src/` | Change |
| --- | --- |
| `main/java/org/locallore/app/DurableGateway.kt` | Both exact live database-schema admission/refresh guards change 3→4. Host workspace protocol stays 1. No `>=`, unknown-version acceptance or read-only fallback. |
| `androidTest/java/org/locallore/app/ArchiveIntegrationTest.kt` | Actual live workspace/reopen/import snapshot expectations become database schema 4; workspace protocol remains 1. |
| `androidTest/java/org/locallore/app/ArchivePlatformRoundTripTest.kt` | Current exported archive source schema must be 4; parsed copy of historical schema-2/v1 input is normalized to 4 only for existing structural comparison. |
| `androidTest/java/org/locallore/app/DurableDeletionRecoveryTest.kt` | Its fixed protocol reply and matching current snapshot expectation become 4. |
| `androidTest/java/org/locallore/app/TimelineProtocolTest.kt` | Fixed protocol metadata defaults to 4; three new actual-DurableGateway protocol cases retain strict admission/refresh fencing. |
| `test/java/org/locallore/app/BranchDeletionShellTest.kt` | Current synthetic SavedSnapshot metadata becomes 4; all lifecycle/assertion logic is unchanged. |

No new parser, alternate storage owner, capability, domain/rules version, gameplay consequence, ID, budget or dependency is introduced. Generic older SavedSnapshot-only unit fixtures with schema-2 metadata are not evidence of live native storage and are left unchanged. No existing tests are deleted, skipped or weakened.

## Historical archive input remains historical

Actual `androidTest/assets/parent-retention-v1.json` is **archive version 1, source database schema 3**, SHA-256 `5cc8eea595258669c1ebb04a15c0a8d642e43be0e534a35cd776920883d62dc7`. The initial claim called it schema3/v2; that archive-version wording was inaccurate and is corrected here from its actual header. No bytes changed. Existing `ParentRetentionNativeTest` still reads and imports that asset through `NativeArchive.prepareImport`/`commitImport`, then exercises real shared retained-child lifecycle semantics. Its successful execution against schema 4 is pending; this packet preserves that required test rather than claiming it passed.

The separate platform-roundtrip assets are historical schema-2/v1 inputs and are also untouched. `matchesHistoricalArchive` already parses two separate byte arrays into local JSON objects. It now requires current source schema 4 and historical source schema 2, then changes only the **parsed copy's** source-schema/digest fields to compare the unchanged remaining canonical content. It never rewrites the asset, importer input, accepted receipts or on-disk archive. This does not license relabeling a real schema-3 fixture as current, or bypass Rust import validation.

Old archive source schema and live workspace schema are different contracts. Rust may validate/import supported historical archives into the current Store; a schema-2/3 live workspace reply must still be refused by this strict client. Migration, hostile archive validation, archive-version policy, ledger replay and source metadata remain solely the shared Rust owner's responsibility. The Rust `locallore-android/examples/platform_roundtrip.rs` also has a current schema-3 export expectation/parsed-copy normalization that the coordinator must update with its shared source; it is outside this packet's ownership.

## New protocol cases and execution plan

Three cases use the **actual DurableGateway** and the existing fixed Android `JSONObject` transport fixture, not a copied gateway/decoder:

- Current database schema 4 initializes with workspace protocol 1 and the existing selected root, without create/submit/prepare/commit/free-text operations.
- Live database schemas 2, 3 and future 5 refuse initialization. The expected complete RPC list is exactly `workspace`, proving no resume/create or gameplay request occurs after unsupported metadata.
- After a successful schema-4 initialization, a later schema-5 refresh must fail without returning a snapshot or issuing create/submit/prepare/commit/free-text. Read-only open/snapshot calls that precede the workspace refresh are not mislabeled as canonical writes.

These tests are in `androidTest`, where real Android `JSONObject` is available. They have **not been compiled or executed**. No extra JVM JSON library, alternate decoder or source-pattern test is added to fabricate local gateway execution. Existing JVM controller tests, including `BranchDeletionShellTest`, can run later without devices; they do not prove these instrumented protocol or JNI cases. No timing, deadlines, pending-operation or cleanup assertions are relaxed.

Next after coordinator imports/freezes schema 4 and allocates a build slot: use the existing task-local Android tooling and exclusive project cache/output on D, run the relevant local JVM suite, compile ordinary main/androidTest, and audit both ABI JNI builds/APK with the exact Rust/schema source. Record actual source/tool/runtime versions and failures; do not infer device execution from compilation. Actual `TimelineProtocolTest`, `ArchiveIntegrationTest`, `ParentRetentionNativeTest`, platform-roundtrip/lifecycle and required device journeys remain separately pending. No ADB, emulator or device operation is authorized for this packet.

## Capacity qualification is intentionally blocked, not retuned

Read-only inspection finds a concrete dependency boundary across:

- `apps/android/capacity-profile.properties`: schema3 / format2 / Ready17-page ceiling.
- `capacity-relief-profile.properties`: schema3 / format2 / 32-page ceiling, initial17 and padding14.
- `app/build.gradle.kts`: exact profile equality, schema-3 metadata, v3 caches/output/mode guards and 17/32 native limits.
- `src/capacityTest` and `src/capacityReliefTest`: exact schema3 manifests/identity/current-snapshot assertions and helper contracts.
- `scripts/android_capacity_probe.py`, `android_capacity_relief_probe.py`, `capacity_padding_probe.py` and their tests: exact schema-3 marker/migration/profile metadata. Padding builds its reference from migrations 001–003, with strict schema verification before its writable phase.
- `SqlitePaddingProcess.kt`: digest `c05ced1f0439fb767f97d2ff93a34ef44eb6fbc27da6814a75fad455fb0b2c17`, initial17 / rows14 / freed15 and reviewed helper lifecycle protocol.

The proposed migration adds tables/indexes, a schema-migration row and an AUTOINCREMENT job identity (`sqlite_sequence` involvement). This changes physical layout/reference-schema identity; it does **not** justify assuming Ready17, failure-at18, padding14, freed15 or a particular new page count. The actual new counts have not been measured by this agent. A schema-4 Store and schema-3 padding reference must not be mixed by widening a digest/schema guard. Schema-3 calibrated results remain historical, not current qualification.

All these capacity paths, calibrated **17/32 limits**, helper guards, scripts/tests, caches and manifests are unchanged, verified by an empty scoped diff. Coordinator recalibration must separately freeze source/identity/profile/caps, obtain actual bounded synthetic Ready/commit/cleanup measurements, preserve old evidence, then coordinate the exact cross-language changes and requalification. Merely changing metadata to 4 or increasing a cap until a test passes would erase the original fault boundary. No such edit is made or requested here.

## Actual checks and handoff limits

Actually performed: read relevant AGENTS/specs/current claims, exact live schema/DTO/gateway paths, archive comparison/import fixtures, coordinator working migration and capacity contracts; reviewed all six-file deltas; `git diff --check` passed. Scoped diff confirms **all historical JSON assets, capacity properties/Gradle/manifests/fixtures/helper/scripts and all Rust files are unchanged**. Read header/hash of the actual parent-retention asset; no synthetic/native database was opened or modified.

The observed coordinator working-copy `004_memory_jobs.sql` had SHA-256 `23f6f3461bbd00bd6887382fb78a90f2c8bc0324e4e6f3fb898d667422ba7e9d`; this is an inspection binding, not a frozen shared implementation or evidence of executed migration. Final integration must use the coordinator's committed schema source and actual compatibility results.

**No Gradle, Kotlin compiler, JVM tests, Rust/JNI build, APK, native app, model, worker, ADB, emulator, device, desktop/CUA, settings, download or protected-resource action was run.** No test PASS is claimed. Build slot is still reserved for coordinator storage work. The existing verified-Core consumer handoff and author-correction design remain untouched. Next runnable work is coordinator source reconciliation/freeze and a separately cleared local JVM/build slot, with capacity and actual device gates kept pending.
