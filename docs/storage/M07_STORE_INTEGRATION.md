# Derived memory through the shared Store

Refs #11 M07.02/.03/.04, partial. Prototype `b03826b` is incorporated as
`6512077`; its original focused evidence remains in M07_DERIVED_2026-10-22.md.
Coordinator integration is `8ea750a`, version-label/race follow-up `169beb4`,
accepted main01fb9f8 integration `d97770c`. This is a shared storage capability,
not full M07 acceptance or proof the production director consumes these caches.

## Migration and interface

Migration001 is unchanged. Migration002 replaces only the version-record table
and adds one STRICT derived-memory cache table with branch/actor foreign keys.
Canonical seeds, turns, events and projections retain their existing schemas and
receipt formats. Exact known identity/schema/migration-record/quick-check/FK
verification applies independently to historical1 and current2.

Writable opening of a historical1 database requires a new consistent SQLite
backup before DDL. Identity is rechecked under the write reservation; the backup
is created nonoverwrite, includes committed WAL and is fsynced. Upgrade DDL,
migration records, version markers and final verification share the transaction.
A failure rolls back to1. The application-private factory supplies a unique
sibling backup; old files, existing backups, foreign schemas and unrelated paths
are not removed or overwritten. Backups remain private plaintext until explicitly
managed by the owner. Read-only verification of original1 does not migrate it.

Store APIs are `prepare_memory`, `publish_memory`, `read_memory`, `search_memory`
and `invalidate_memory`. Callers supply typed scope/head/actor/range/target/query,
never a connection, SQL statement or external Engine. Preparation obtains the
owner's actual validated replay. Its opaque non-Deserialize token contains exact
accepted source envelopes; publish rechecks those and the head transactionally.
Read reconstructs exact bytes from the owner's history. Search materializes only
the verified actor/scope/current-revision partition into a temporary FTS5 corpus.
Stored packets never widen knowledge or become canon; no global rank/count or
hidden exclusion metadata is returned.

The extractive format preserves statements and beliefs as distinct typed records.
Only observed consecutive time advances coalesce, retaining original source IDs.
Its provenance explicitly identifies deterministic extraction with model/prompt
null. Source envelopes cap at256 eligible events/1MiB, complete packets64KiB,
partitions32 packets and searches16 literal terms/hits. Full retained history is
not cloned merely to enforce the eligible-event cap. The owner still rebuilds
its Engine through full `Store::resume` before the borrowed scan; cancellation is
checked before/after replay and during subsequent bounded scan/SQL steps. This
does **not** establish prompt cancellation or maximum-scale latency for the whole
maintenance operation. Partial results on cancellation are discarded.

Host workspace contract1 remains compatible with existing app clients; actual
SQLite implementation2 is additive `database_schema_version`. The native storage
endpoint and database-copy manifest use the actual version. Inspection export
schema1 is a distinct canonical view format and remains unchanged. A private
database copy now also contains the derived cache; normal story inspection files
exclude it. No Android app source or system/device configuration changed.

## Checks executed on coordinator integration

Windows x64/Rust/Cargo1.93.1, debug0/incremental0, locked offline dependencies,
task-owned D: targets/fixtures/temp. Pinned Node24.22.1 and existing locked npm
dependencies. Actual commands:

```powershell
cargo test --workspace --locked --offline --target-dir <task>/m07-derived
cargo clippy --workspace --all-targets --locked --offline --target-dir <task>/m07-derived -- -D warnings
cargo fmt --all -- --check
node apps/desktop/verify-frontend.mjs
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --locked --offline --target-dir <task>/desktop-publication-target
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --all-targets --locked --offline --target-dir <task>/desktop-publication-target -- -D warnings
```

Complete integrated Rust workspace **249 passed**, zero failed/ignored; strict
workspace Clippy/format passed. This includes11 original derived-module tests,
4 public Store/migration cases and actual v1-upgrade DDL rollback. New Store
cases preserve accepted gift receipts/state across migration/read-only backup,
exercise backup collision and competing openers, prove one retained migration
backup, scoped real FTS/reopen/idempotency/invalidation/cancel/stale behavior and
refuse altered historical schema without mutation. Future-version tests advance
to current+1, preserving their rejection criterion. Host tests assert both
workspace contract1 and actual database2. Normal frontend/schema/controller/hook
checks passed. Native default **18 passed/1 ignored**; development **20 passed/1
ignored plus2 wrapper tests**, strict development/all-target Clippy passed. The
new native metadata unit verifies the actual2 display and rejects missing actual
version; ignored Windows symlink evidence remains separately qualified.

Initial new Store tests omitted the existing begin-turn requirement and failed
UnknownTurn before exercising migration; corrected fixtures now submit the real
request before commit. Strict Clippy then found an unnecessary test clone, fixed
without changing its equality assertion. Original failing logs remain local.
Independent source review caught the native metadata version mismatch before
publication; the reviewed fix keeps host compatibility while displaying actual2.

Android compatibility used existing JDK17.0.6, Gradle8.11.1/AGP8.10.1/Kotlin2.2.21,
SDK36/NDK29.0.14206865, task-private Gradle home/output, no daemon or SDK downloads:

```powershell
java -classpath gradle/wrapper/gradle-wrapper.jar org.gradle.wrapper.GradleWrapperMain -I <task>/android-output.gradle :app:assembleDebug :app:assembleDebugAndroidTest :app:testDebugUnitTest :app:lintDebug --offline --no-daemon --console=plain -Pandroid.builder.sdkDownload=false
python scripts/audit_apk.py <task>/android-build/_app/outputs/apk/debug/app-debug.apk
```

**78 tasks executed**, both JNI ABIs rebuilt, both APKs built, **38 JVM tests
passed**, zero failures/errors/skips. Lint0errors/one existing newer-coroutines
advisory; APK permissions and16KiB ELF/ZIP alignment audit passed. No ADB,
emulator or physical device was operated. Logs remain gitignored under
`target/store-*`; Android build success does not close physical-device gates.

## Remaining gates

No LLM archivist, durable job cursor/queue, automatic chapter detection,
correction/branch inheritance, semantic compression quality, production cached
memory consumption or model usefulness is implemented by this slice. Cache work
is separate from atomic gameplay and cannot roll back a committed turn. Native
app compatibility evidence is collected separately; Store migration assertions
are not relabeled as native WebView legacy-save journeys. Full M07/D06 and desktop
epic acceptance remain open. Next: maintain/rebuild bounded ranges and expose
freshness/provenance through the shared host, then integrate eligible packets
into the production context compiler and debugger.
