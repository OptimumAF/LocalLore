// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Exact historical schemas and real public migration/backup paths. Only fresh
//! synthetic roots are used; accepted history is created through Store/Engine.
use locallore::{contracts::*, engine::Engine};
use locallore_storage::{
    derived_memory::{PrepareRequest, Target},
    ForkRequest, StorageError, Store, SCHEMA_VERSION,
};
use rusqlite::{types::Value, Connection, OpenFlags};
use std::{
    collections::BTreeMap,
    fs,
    path::{Path, PathBuf},
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT: AtomicU64 = AtomicU64::new(0);
const CANONICAL_TABLES: [&str; 8] = [
    "stories",
    "branches",
    "entities",
    "branch_entities",
    "turns",
    "accepted_events",
    "event_witnesses",
    "branch_projections",
];
struct Fixture {
    root: PathBuf,
    path: PathBuf,
    scopes: Vec<Scope>,
}
impl Fixture {
    fn current() -> Self {
        let root = std::env::temp_dir().join(format!(
            "locallore-schema3-migration-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        fs::create_dir(&root).unwrap();
        fs::write(
            root.join("owner-v1"),
            b"locallore-synthetic-schema3-migration-v1",
        )
        .unwrap();
        let path = root.join("historical.sqlite");
        let mut store = Store::open(&path, None).unwrap();
        let mut seed: Seed =
            serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
        seed.scope.story = "migration-target".into();
        let main = seed.scope.clone();
        store
            .create_story("Synthetic migration history", seed.clone())
            .unwrap();
        let child = fork(&mut store, &main, "child", 0);
        apply(
            &mut store,
            &main,
            "literal-multi-effect",
            vec![
                Command::Give {
                    item: "potion".into(),
                    to: "mira".into(),
                    quantity: 1,
                },
                Command::Wait { ticks: 1 },
                Command::Say {
                    text: "Synthetic literal: \"quoted\" \\ path\nUnicode café · lantern 🕯".into(),
                    audience: ["mira".into()].into(),
                },
            ],
        );
        apply(
            &mut store,
            &child,
            "child-claim",
            vec![Command::Say {
                text: "Synthetic child-only knowledge".into(),
                audience: ["mira".into()].into(),
            }],
        );
        let sibling = fork(&mut store, &main, "sibling", 0);
        apply(
            &mut store,
            &sibling,
            "sibling-consume",
            vec![Command::Consume {
                item: "potion".into(),
            }],
        );
        let nested = fork(&mut store, &child, "nested", 0);
        apply(
            &mut store,
            &nested,
            "nested-wait",
            vec![Command::Wait { ticks: 1 }],
        );
        let engine = store.resume(&main).unwrap().engine;
        let draft = engine.request(
            "retained-draft",
            Intent::Actions(vec![Command::Wait { ticks: 1 }]),
        );
        store.begin_turn(&draft).unwrap();
        let cancelled = engine.request(
            "retained-cancelled",
            Intent::Actions(vec![Command::Wait { ticks: 1 }]),
        );
        store.begin_turn(&cancelled).unwrap();
        store.cancel_turn(&cancelled).unwrap();
        for observer in ["player", "mira"] {
            let prepared = store
                .prepare_memory(&memory(&main, observer, 3), &|| false)
                .unwrap();
            store.publish_memory(prepared, &|| false).unwrap();
        }
        seed.scope.story = "migration-other".into();
        let other = seed.scope.clone();
        store
            .create_story("Independent migration story", seed)
            .unwrap();
        apply(
            &mut store,
            &other,
            "other-claim",
            vec![Command::Say {
                text: "Synthetic independent migration canary".into(),
                audience: ["mira".into()].into(),
            }],
        );
        drop(store);
        Self {
            root,
            path,
            scopes: vec![main, child, sibling, nested, other],
        }
    }
    fn historical(version: u32) -> Self {
        let fixture = Self::current();
        historical_schema(&Connection::open(&fixture.path).unwrap(), version);
        assert_eq!(
            Store::open_read_only(&fixture.path)
                .unwrap()
                .info()
                .unwrap()
                .schema_version,
            version
        );
        fixture
    }
    fn path(&self, name: &str) -> PathBuf {
        self.root.join(name)
    }
}
// Roots remain under the caller-owned task TEMP for genuine failed-attempt
// evidence. This helper never recursively deletes or adopts an existing root.
fn historical_schema(db: &Connection, version: u32) {
    assert!([1, 2, 3].contains(&version));
    let initial = include_str!("../migrations/001_initial.sql")
        .split("CREATE TABLE stories")
        .next()
        .unwrap();
    let derived_header = include_str!("../migrations/002_derived_memory.sql")
        .split("CREATE TABLE derived_memory")
        .next()
        .unwrap();
    let optional = if version == 1 {
        "DROP TABLE derived_memory;"
    } else {
        ""
    };
    let records = if version >= 2 { derived_header } else { "" };
    let retention = if version == 3 {
        include_str!("../migrations/003_branch_retention.sql")
    } else {
        ""
    };
    // Reconstruct the actual historical schema_migrations definition, not an
    // approximation with current CHECK constraints or a renamed current table.
    db.execute_batch(&format!("BEGIN IMMEDIATE; DROP TABLE memory_job_packets; DROP TABLE memory_jobs; DROP TABLE branch_retention; {optional} DROP TABLE schema_migrations; {initial} {records} {retention} PRAGMA user_version={version}; COMMIT;")).unwrap();
}
fn apply(store: &mut Store, scope: &Scope, id: &str, commands: Vec<Command>) {
    let e = store.resume(scope).unwrap().engine;
    let req = e.request(id, Intent::Actions(commands));
    let receipt = e.preview(&req, &Engine::proposal(&req).unwrap()).unwrap();
    store.begin_turn(&req).unwrap();
    store.commit_prepared(&receipt).unwrap();
}
fn fork(store: &mut Store, parent: &Scope, id: &str, at: u64) -> Scope {
    let revision = store.resume(parent).unwrap().engine.revision();
    store
        .fork_branch(
            &ForkRequest {
                parent: parent.clone(),
                child_branch: id.into(),
                expected_parent_revision: revision,
                at_revision: at,
            },
            &|| false,
        )
        .unwrap()
        .scope
}
fn memory(scope: &Scope, observer: &str, head: u64) -> PrepareRequest {
    PrepareRequest {
        scope: scope.clone(),
        expected_revision: head,
        observer: observer.into(),
        from_exclusive: 0,
        through_revision: head,
        target: Target::SceneWindow,
    }
}
fn read(path: &Path) -> Connection {
    Connection::open_with_flags(path, OpenFlags::SQLITE_OPEN_READ_ONLY).unwrap()
}
fn state(path: &Path, scopes: &[Scope]) -> Vec<Vec<u8>> {
    let mut store = Store::open_read_only(path).unwrap();
    let mut states = Vec::new();
    for scope in scopes {
        let engine = store.resume(scope).unwrap().engine;
        states.push(engine.canonical_bytes());
        states.push(serde_json::to_vec(engine.receipts()).unwrap());
        for observer in ["player", "mira", "sable"] {
            states.push(
                serde_json::to_vec(
                    &engine
                        .character_context(observer, scope, engine.revision())
                        .unwrap(),
                )
                .unwrap(),
            );
        }
    }
    states
}
fn rows(path: &Path, derived: bool) -> BTreeMap<String, Vec<Vec<Value>>> {
    let db = read(path);
    let mut tables = CANONICAL_TABLES.to_vec();
    if derived {
        tables.push("derived_memory");
    }
    tables
        .into_iter()
        .map(|table| {
            let mut q = db.prepare(&format!("SELECT * FROM {table}")).unwrap();
            let width = q.column_count();
            let order = (1..=width)
                .map(|n| n.to_string())
                .collect::<Vec<_>>()
                .join(",");
            q = db
                .prepare(&format!("SELECT * FROM {table} ORDER BY {order}"))
                .unwrap();
            let values = q
                .query_map([], |r| (0..width).map(|i| r.get(i)).collect())
                .unwrap()
                .map(Result::unwrap)
                .collect();
            (table.into(), values)
        })
        .collect()
}
fn literal_receipts(path: &Path) -> Vec<String> {
    read(path).prepare("SELECT response_json FROM turns WHERE status='committed' ORDER BY story_id,branch_id,expected_revision,turn_id").unwrap().query_map([],|r|r.get(0)).unwrap().map(Result::unwrap).collect()
}
fn same<T: PartialEq>(a: &T, b: &T) {
    assert!(a == b, "synthetic migration parity differed");
}
fn verify_retention_empty(store: &Store, path: &Path, scopes: &[Scope]) {
    assert_eq!(store.info().unwrap().schema_version, SCHEMA_VERSION);
    assert_eq!(SCHEMA_VERSION, 4);
    for table in ["memory_jobs", "memory_job_packets"] {
        let count: i64 = read(path)
            .query_row(&format!("SELECT count(*) FROM {table}"), [], |r| r.get(0))
            .unwrap();
        assert_eq!(count, 0);
    }
    let count: i64 = read(path)
        .query_row("SELECT count(*) FROM branch_retention", [], |r| r.get(0))
        .unwrap();
    assert_eq!(count, 0);
    for scope in scopes {
        assert!(store.is_branch_active(scope).unwrap());
    }
}
fn standalone_copy(source: &Path, destination: &Path) {
    let mut input = fs::File::open(source).unwrap();
    let mut output = fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(destination)
        .unwrap();
    std::io::copy(&mut input, &mut output).unwrap();
    output.sync_all().unwrap();
}

#[test]
fn exact_v2_safety_copy_and_upgrade_preserve_literal_receipts_all_timelines_and_real_caches() {
    let f = Fixture::historical(2);
    let before = fs::read(&f.path).unwrap();
    let canonical = state(&f.path, &f.scopes);
    let original_rows = rows(&f.path, true);
    let receipts = literal_receipts(&f.path);
    assert!(receipts
        .iter()
        .any(|r| r.contains("café") && r.contains("\\nUnicode")));
    assert_eq!(
        Store::open(&f.path, None).err(),
        Some(StorageError::BackupRequired)
    );
    same(&before, &fs::read(&f.path).unwrap());
    let backup = f.path("before-v2.sqlite");
    let mut upgraded = Store::open(&f.path, Some(&backup)).unwrap();
    verify_retention_empty(&upgraded, &f.path, &f.scopes);
    same(&canonical, &state(&f.path, &f.scopes));
    same(&original_rows, &rows(&f.path, true));
    same(&receipts, &literal_receipts(&f.path));
    assert_eq!(
        upgraded
            .read_memory(&memory(&f.scopes[0], "mira", 3), &|| false)
            .unwrap()
            .json()["source_revision"],
        3
    );
    let saved = Store::open_read_only(&backup).unwrap();
    assert_eq!(saved.info().unwrap().schema_version, 2);
    drop(saved);
    same(&original_rows, &rows(&backup, true));
    same(&canonical, &state(&backup, &f.scopes));
    same(&receipts, &literal_receipts(&backup));
    let standalone = f.path("standalone-old-v2.sqlite");
    standalone_copy(&backup, &standalone);
    assert_eq!(
        Store::open_read_only(&standalone)
            .unwrap()
            .info()
            .unwrap()
            .schema_version,
        2
    );
    same(&canonical, &state(&standalone, &f.scopes));
    drop(upgraded);
    verify_retention_empty(&Store::open(&f.path, None).unwrap(), &f.path, &f.scopes);
}

#[test]
fn exact_v1_read_only_and_direct_upgrade_keep_history_and_old_backup_version() {
    let f = Fixture::historical(1);
    let original = fs::read(&f.path).unwrap();
    let states = state(&f.path, &f.scopes);
    let data = rows(&f.path, false);
    let receipts = literal_receipts(&f.path);
    let mut old = Store::open_read_only(&f.path).unwrap();
    assert_eq!(old.info().unwrap().schema_version, 1);
    assert_eq!(
        old.branch_catalog(&f.scopes[0].story, &|| false)
            .unwrap()
            .branches
            .len(),
        4
    );
    drop(old);
    same(&original, &fs::read(&f.path).unwrap());
    assert_eq!(
        Store::open(&f.path, None).err(),
        Some(StorageError::BackupRequired)
    );
    same(&original, &fs::read(&f.path).unwrap());
    let backup = f.path("before-v1.sqlite");
    let upgraded = Store::open(&f.path, Some(&backup)).unwrap();
    verify_retention_empty(&upgraded, &f.path, &f.scopes);
    same(&states, &state(&f.path, &f.scopes));
    same(&data, &rows(&f.path, false));
    same(&receipts, &literal_receipts(&f.path));
    let derived: i64 = read(&f.path)
        .query_row("SELECT count(*) FROM derived_memory", [], |r| r.get(0))
        .unwrap();
    assert_eq!(derived, 0);
    assert_eq!(
        Store::open_read_only(&backup)
            .unwrap()
            .info()
            .unwrap()
            .schema_version,
        1
    );
    same(&data, &rows(&backup, false));
    same(&states, &state(&backup, &f.scopes));
    same(&receipts, &literal_receipts(&backup));
}

#[test]
fn existing_backup_collision_preserves_both_old_databases_and_existing_destination() {
    for version in [1, 2, 3] {
        let f = Fixture::historical(version);
        let before = fs::read(&f.path).unwrap();
        let backup = f.path("already-owned.sqlite");
        let sentinel = b"Synthetic existing backup sentinel";
        fs::write(&backup, sentinel).unwrap();
        assert_eq!(
            Store::open(&f.path, Some(&backup)).err(),
            Some(StorageError::BackupExists)
        );
        same(&before, &fs::read(&f.path).unwrap());
        same(&sentinel.to_vec(), &fs::read(&backup).unwrap());
        assert_eq!(
            Store::open_read_only(&f.path)
                .unwrap()
                .info()
                .unwrap()
                .schema_version,
            version
        );
        let unique = f.path("new-backup.sqlite");
        verify_retention_empty(
            &Store::open(&f.path, Some(&unique)).unwrap(),
            &f.path,
            &f.scopes,
        );
        assert_eq!(
            Store::open_read_only(&unique)
                .unwrap()
                .info()
                .unwrap()
                .schema_version,
            version
        );
    }
}

#[test]
fn altered_current_schema_missing_migration_record_and_future_version_never_adopt_or_backup() {
    for corruption in [0, 1, 2] {
        let f = Fixture::current();
        let db = Connection::open(&f.path).unwrap();
        let expected = match corruption {
            0 => {
                db.execute_batch("ALTER TABLE branch_retention ADD COLUMN foreign_state TEXT;")
                    .unwrap();
                StorageError::SchemaMismatch
            }
            1 => {
                db.execute("DELETE FROM schema_migrations WHERE version=3", [])
                    .unwrap();
                StorageError::SchemaMismatch
            }
            _ => {
                db.pragma_update(None, "user_version", SCHEMA_VERSION + 1)
                    .unwrap();
                StorageError::FutureVersion
            }
        };
        drop(db);
        let original = fs::read(&f.path).unwrap();
        let backup = f.path("must-not-exist.sqlite");
        assert_eq!(Store::open_read_only(&f.path).err(), Some(expected));
        assert_eq!(Store::open(&f.path, Some(&backup)).err(), Some(expected));
        assert_eq!(Store::open_application(&f.path).err(), Some(expected));
        assert!(!backup.exists());
        same(&original, &fs::read(&f.path).unwrap());
    }
}

#[test]
fn application_upgrade_creates_one_new_standalone_historical_safety_copy() {
    for version in [1, 2, 3] {
        let f = Fixture::historical(version);
        let baseline = state(&f.path, &f.scopes);
        let upgraded = Store::open_application(&f.path).unwrap();
        verify_retention_empty(&upgraded, &f.path, &f.scopes);
        drop(upgraded);
        let backups = || {
            fs::read_dir(&f.root)
                .unwrap()
                .map(Result::unwrap)
                .filter(|e| {
                    e.file_name()
                        .to_string_lossy()
                        .starts_with("historical.sqlite.before-v3-")
                })
                .map(|e| e.path())
                .collect::<Vec<_>>()
        };
        let files = backups();
        assert_eq!(files.len(), 1);
        assert_eq!(
            Store::open_read_only(&files[0])
                .unwrap()
                .info()
                .unwrap()
                .schema_version,
            version
        );
        same(&baseline, &state(&files[0], &f.scopes));
        drop(Store::open_application(&f.path).unwrap());
        same(&files, &backups());
        same(&baseline, &state(&f.path, &f.scopes));
    }
}

#[test]
fn v2_upgrade_backup_contains_actual_committed_wal_history_not_just_the_main_file() {
    let f = Fixture::current();
    let keeper = Connection::open(&f.path).unwrap();
    let mode: String = keeper
        .query_row("PRAGMA journal_mode=WAL", [], |r| r.get(0))
        .unwrap();
    assert_eq!(mode, "wal");
    keeper.pragma_update(None, "wal_autocheckpoint", 0).unwrap();
    // A real old read snapshot keeps later accepted commits in WAL even when
    // the public Store writer closes. Merely keeping an idle connection open
    // does not establish the retained reader used by this fixture.
    let pinned_reader = Connection::open(&f.path).unwrap();
    pinned_reader.execute_batch("BEGIN").unwrap();
    let old_story_count: i64 = pinned_reader
        .query_row("SELECT count(*) FROM stories", [], |r| r.get(0))
        .unwrap();
    assert_eq!(old_story_count, 2);
    let main_before = fs::read(&f.path).unwrap();
    let mut live = Store::open(&f.path, None).unwrap();
    apply(
        &mut live,
        &f.scopes[0],
        "wal-only-accepted",
        vec![Command::Say {
            text: "Synthetic committed WAL-only evidence".into(),
            audience: ["mira".into()].into(),
        }],
    );
    drop(live);
    historical_schema(&keeper, 2);
    same(&main_before, &fs::read(&f.path).unwrap());
    let wal = PathBuf::from(format!("{}-wal", f.path.display()));
    assert!(fs::metadata(&wal).unwrap().len() > 32);
    let states = state(&f.path, &f.scopes);
    let receipts = literal_receipts(&f.path);
    assert!(receipts.iter().any(|r| r.contains("WAL-only evidence")));
    assert_eq!(
        Store::open_read_only(&f.path)
            .unwrap()
            .info()
            .unwrap()
            .schema_version,
        2
    );
    let wal_before = fs::read(&wal).unwrap();
    assert_eq!(
        Store::open(&f.path, None).err(),
        Some(StorageError::BackupRequired)
    );
    same(&main_before, &fs::read(&f.path).unwrap());
    same(&wal_before, &fs::read(&wal).unwrap());
    let backup = f.path("wal-safety-copy.sqlite");
    let upgraded = Store::open(&f.path, Some(&backup)).unwrap();
    verify_retention_empty(&upgraded, &f.path, &f.scopes);
    same(&states, &state(&f.path, &f.scopes));
    same(&receipts, &literal_receipts(&f.path));
    let standalone = f.path("wal-safety-standalone.sqlite");
    standalone_copy(&backup, &standalone);
    assert_eq!(
        Store::open_read_only(&standalone)
            .unwrap()
            .info()
            .unwrap()
            .schema_version,
        2
    );
    same(&states, &state(&standalone, &f.scopes));
    same(&receipts, &literal_receipts(&standalone));
    assert_eq!(
        Store::open_read_only(&standalone)
            .unwrap()
            .resume(&f.scopes[0])
            .unwrap()
            .engine
            .revision(),
        4
    );
    drop(upgraded);
    pinned_reader.execute_batch("ROLLBACK").unwrap();
    drop(pinned_reader);
    drop(keeper);
}
