# Scoped SQLite foundation

M04.01, [ticket #8](https://github.com/OptimumAF/LocalLore/issues/8). This Rust
storage owner persists validated original seeds and initializes the first scoped
SQLite schema. Accepted-turn save/resume and outcome replay remain M04.02/.03.
The Compose app still uses its in-memory engine. This implementation PR is
stacked on the unmerged ownership fix #35; that prerequisite must land first.

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

`Store::open(path, migration_backup)` initializes a new file or verifies an owned
schema-1 database. For an existing empty version-0 file, pass a new backup path;
otherwise it returns `BackupRequired`. Nonempty unversioned databases and future
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

See [ADR-0007](../adr/0007-sqlite-storage-owner.md), [dependency sources](SOURCES_2026-10-22.md),
and [review](REVIEW_2026-10-22.md). Branch inheritance, event semantics, eligibility
and canonical replay still require engine validation; foreign keys alone do not
prove them. No physical phone, ARM64 execution, durable accepted gameplay or
release qualification follows from a host test or Android cross-build.
