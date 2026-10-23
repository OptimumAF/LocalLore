# Scoped SQLite foundation

The Rust SQLite owner under [ticket #8](https://github.com/OptimumAF/LocalLore/issues/8)
persists validated original seeds and initializes the scoped schema. The
[durability follow-on](DURABILITY.md) adds atomic root turns and validated
save/resume. Both production app adapters now use the
[shared native workspace](APP_INTEGRATION.md), with separate app-local files,
library selection and receipt-derived history. The foundation and turn layer
landed through #38/#39; current task status and acceptance remain on #8.

The native-only [inspection snapshot v1](INSPECTION_SNAPSHOT_V1.md) captures one
validated head through that same store. It creates derived read-only views,
with explicit privacy modes, rather than a second playable story format.

Run the deterministic checks without models, Android tools or ADB:

```powershell
python scripts/check.py host --offline
cargo test -p locallore-storage --locked --offline
```

The new exact dependencies must already be cached for offline mode. Ordinary
Cargo provisioning may fetch the locked crates, never model weights. The default
workspace checks include storage tests. The explicit `storage_smoke` example and
`scripts/storage_android_smoke.py` exercise the same API using synthetic data;
their commands and actual host/emulator evidence appear in the [dated verification](VERIFICATION_2026-10-22.md).
The cross-build helper neither operates devices nor downloads SDKs or weights.

`Store::open(path, migration_backup)` initializes schema2 or verifies an owned
current database. Schema2 adds a bounded derived-memory cache without changing
canonical v1 tables or receipts. An exact owned schema1 or empty version0 needs
a new backup path before upgrade; otherwise it returns `BackupRequired`.
`Store::open_application` supplies a unique nonoverwrite sibling backup for the
trusted app-private path. `open_read_only` also verifies historical schema1
without migrating it. Nonempty unversioned databases and future
versions are refused. `create_story` accepts a typed seed only after `Engine::new`
validation, then stores the seed, root namespace, typed entity memberships and
initial replaceable projection in one transaction. `load_seed` requires exact
story/root-branch scope and revalidates the seed. Duplicate story IDs fail without
replacement; identical names and item IDs in different stories stay independent.

`backup_to` creates a consistent SQLite backup at a new destination. Existing
files, including a database's own path, are refused. Keep migration backups until
the upgrade is accepted; no downgrade or automatic overwrite is provided. The
backup can be opened separately for verification. These files are plaintext,
private local data; the crate has no upload/export service. No raw SQL or connection
escapes the owner. Errors expose fixed categories rather than SQL, paths or content.

The Store's derived-memory methods prepare deterministic typed event extractives,
publish against exact accepted-source/head fences, revalidate caches on read and
search only a verified actor/scope/revision partition through temporary SQLite
FTS5. They do not establish canon or call an archivist model. See
[Store integration](M07_STORE_INTEGRATION.md) for versioning, measured checks,
limits and remaining production-memory work.

See [ADR-0007](../adr/0007-sqlite-storage-owner.md), [dependency sources](SOURCES_2026-10-22.md),
and [review](REVIEW_2026-10-22.md). Branch inheritance, event semantics, eligibility
and canonical replay still require engine validation; foreign keys alone do not
prove them. No physical phone, ARM64 execution, durable accepted gameplay or
release qualification follows from a host test or Android cross-build.
