use locallore::{contracts::*, engine::Engine};
use locallore_storage::{derived_memory::*, StorageError, Store, SCHEMA_VERSION};
use rusqlite::Connection;
use std::{
    path::PathBuf,
    sync::atomic::{AtomicUsize, Ordering},
};
static NEXT: AtomicUsize = AtomicUsize::new(0);
struct Temp(PathBuf);
impl Temp {
    fn new() -> Self {
        let root = std::env::temp_dir().join(format!(
            "locallore-derived-owner-{}-{}",
            std::process::id(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&root).unwrap();
        Self(root)
    }
    fn path(&self, name: &str) -> PathBuf {
        self.0.join(name)
    }
}
impl Drop for Temp {
    fn drop(&mut self) {
        std::fs::remove_dir_all(&self.0).unwrap();
    }
}
fn seed() -> Seed {
    serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap()
}
fn populate(store: &mut Store) -> (Scope, Receipt) {
    let seed = seed();
    let scope = seed.scope.clone();
    store.create_story("Synthetic derived owner", seed).unwrap();
    let engine = store.resume(&scope).unwrap().engine;
    let request = engine.request(
        "gift",
        Intent::Actions(vec![Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 1,
        }]),
    );
    let proposal = Engine::proposal(&request).unwrap();
    let receipt = engine.preview(&request, &proposal).unwrap();
    store.begin_turn(&request).unwrap();
    let receipt = store
        .commit_turn(&request, &proposal, receipt.narration())
        .unwrap();
    (scope, receipt)
}
fn historical_v1(path: &std::path::Path) -> (Scope, Receipt) {
    let mut store = Store::open(path, None).unwrap();
    let populated = populate(&mut store);
    drop(store);
    // Exact original schema objects and canonical payloads, without the new derived cache.
    let initial = include_str!("../migrations/001_initial.sql");
    let header = initial.split("CREATE TABLE stories").next().unwrap();
    let db = Connection::open(path).unwrap();
    db.execute_batch(&format!("BEGIN; DROP TABLE memory_job_packets; DROP TABLE memory_jobs; DROP TABLE branch_retention; DROP TABLE derived_memory; DROP TABLE schema_migrations; {header} PRAGMA user_version=1; COMMIT;")).unwrap();
    assert_eq!(
        Store::open_read_only(path)
            .unwrap()
            .info()
            .unwrap()
            .schema_version,
        1
    );
    populated
}
fn request(scope: &Scope, observer: &str, head: u64) -> PrepareRequest {
    PrepareRequest {
        scope: scope.clone(),
        expected_revision: head,
        observer: observer.into(),
        from_exclusive: 0,
        through_revision: head,
        target: Target::SceneWindow,
    }
}

#[test]
fn actual_v1_migration_preserves_history_and_backup_is_exact_read_only_v1() {
    let dir = Temp::new();
    let path = dir.path("story.sqlite");
    let backup = dir.path("before.sqlite");
    let (scope, receipt) = historical_v1(&path);
    let original = std::fs::read(&path).unwrap();
    assert_eq!(
        Store::open(&path, None).err(),
        Some(StorageError::BackupRequired)
    );
    assert_eq!(std::fs::read(&path).unwrap(), original);
    let mut store = Store::open(&path, Some(&backup)).unwrap();
    assert_eq!(store.info().unwrap().schema_version, SCHEMA_VERSION);
    let engine = store.resume(&scope).unwrap().engine;
    assert_eq!(engine.receipts(), std::slice::from_ref(&receipt));
    let mut saved = Store::open_read_only(&backup).unwrap();
    assert_eq!(saved.info().unwrap().schema_version, 1);
    let before = saved.resume(&scope).unwrap().engine;
    assert_eq!(before.receipts(), [receipt]);
    assert_eq!(before.canonical_bytes(), engine.canonical_bytes());
    assert_eq!(
        saved
            .prepare_memory(&request(&scope, "mira", 1), &|| false)
            .err(),
        Some(MemoryError::Unsupported)
    );
    drop(store);
    drop(saved);
    assert_eq!(
        Store::open(&path, None)
            .unwrap()
            .info()
            .unwrap()
            .schema_version,
        SCHEMA_VERSION
    );
}

#[test]
fn application_open_backs_up_once_and_never_adopts_tampered_v1() {
    let dir = Temp::new();
    let path = dir.path("old.sqlite");
    historical_v1(&path);
    drop(Store::open_application(&path).unwrap());
    let backups = || {
        std::fs::read_dir(&dir.0)
            .unwrap()
            .filter_map(Result::ok)
            .filter(|entry| {
                entry
                    .file_name()
                    .to_string_lossy()
                    .contains(&format!(".before-v{SCHEMA_VERSION}-"))
            })
            .count()
    };
    assert_eq!(backups(), 1);
    drop(Store::open_application(&path).unwrap());
    assert_eq!(backups(), 1);
    let tampered = dir.path("tampered.sqlite");
    historical_v1(&tampered);
    Connection::open(&tampered)
        .unwrap()
        .execute_batch("CREATE TABLE foreign_table(data TEXT);")
        .unwrap();
    let before = std::fs::read(&tampered).unwrap();
    assert_eq!(
        Store::open_application(&tampered).err(),
        Some(StorageError::SchemaMismatch)
    );
    assert_eq!(std::fs::read(&tampered).unwrap(), before);
    assert_eq!(backups(), 1);
}

#[test]
fn v1_backup_collision_preserves_original_and_concurrent_openers_make_one_backup() {
    let dir = Temp::new();
    let path = dir.path("old.sqlite");
    let (scope, receipt) = historical_v1(&path);
    let collision = dir.path("existing-backup.sqlite");
    std::fs::write(&collision, b"keep existing backup").unwrap();
    let before = std::fs::read(&path).unwrap();
    assert_eq!(
        Store::open(&path, Some(&collision)).err(),
        Some(StorageError::BackupExists)
    );
    assert_eq!(std::fs::read(&path).unwrap(), before);
    assert_eq!(std::fs::read(&collision).unwrap(), b"keep existing backup");
    let barrier = std::sync::Arc::new(std::sync::Barrier::new(2));
    let threads: Vec<_> = ["a.sqlite", "b.sqlite"]
        .into_iter()
        .map(|name| {
            let path = path.clone();
            let backup = dir.path(name);
            let barrier = barrier.clone();
            std::thread::spawn(move || {
                barrier.wait();
                Store::open(&path, Some(&backup))
            })
        })
        .collect();
    for thread in threads {
        match thread.join().unwrap() {
            Ok(store) => assert_eq!(store.info().unwrap().schema_version, SCHEMA_VERSION),
            Err(error) => assert_eq!(error, StorageError::Busy),
        }
    }
    assert_eq!(
        ["a.sqlite", "b.sqlite"]
            .into_iter()
            .filter(|name| dir.path(name).is_file())
            .count(),
        1
    );
    let mut store = Store::open(&path, None).unwrap();
    assert_eq!(store.resume(&scope).unwrap().engine.receipts(), [receipt]);
}

#[test]
fn real_owner_summary_search_reopen_cancel_stale_and_invalidation_preserve_canon() {
    let dir = Temp::new();
    let path = dir.path("story.sqlite");
    let mut store = Store::open(&path, None).unwrap();
    let (scope, receipt) = populate(&mut store);
    let before = store.resume(&scope).unwrap().engine.canonical_bytes();
    let req = request(&scope, "mira", 1);
    let prepared = store.prepare_memory(&req, &|| false).unwrap();
    assert_eq!(
        store.publish_memory(prepared, &|| true),
        Err(MemoryError::Cancelled)
    );
    assert_eq!(
        store.read_memory(&req, &|| false),
        Err(MemoryError::NotFound)
    );
    let prepared = store.prepare_memory(&req, &|| false).unwrap();
    assert_eq!(
        store.publish_memory(prepared, &|| false),
        Ok(PublishOutcome::Published)
    );
    let packet = store.read_memory(&req, &|| false).unwrap();
    let search = SearchRequest {
        scope: scope.clone(),
        expected_revision: 1,
        observer: "mira".into(),
        text: "potion".into(),
        limit: 4,
    };
    assert_eq!(
        store.search_memory(&search, &|| false).unwrap()[0].packet,
        packet
    );
    let mut hidden = search.clone();
    hidden.observer = "sable".into();
    assert!(store.search_memory(&hidden, &|| false).unwrap().is_empty());
    drop(store);
    let mut store = Store::open(&path, None).unwrap();
    assert_eq!(store.read_memory(&req, &|| false).unwrap(), packet);
    let prepared = store.prepare_memory(&req, &|| false).unwrap();
    assert_eq!(
        store.publish_memory(prepared, &|| false),
        Ok(PublishOutcome::Unchanged)
    );
    store
        .invalidate_memory(&scope, "mira", 1, &|| false)
        .unwrap();
    assert_eq!(
        store.read_memory(&req, &|| false),
        Err(MemoryError::NotFound)
    );
    assert_eq!(
        store.resume(&scope).unwrap().engine.canonical_bytes(),
        before
    );
    assert_eq!(store.resume(&scope).unwrap().engine.receipts(), [receipt]);
    let prepared = store.prepare_memory(&req, &|| false).unwrap();
    let engine = store.resume(&scope).unwrap().engine;
    let next = engine.request("later", Intent::Actions(vec![Command::Wait { ticks: 1 }]));
    let proposal = Engine::proposal(&next).unwrap();
    let next_receipt = engine.preview(&next, &proposal).unwrap();
    store.begin_turn(&next).unwrap();
    store
        .commit_turn(&next, &proposal, next_receipt.narration())
        .unwrap();
    assert_eq!(
        store.publish_memory(prepared, &|| false),
        Err(MemoryError::Stale)
    );
    assert_eq!(store.read_memory(&req, &|| false), Err(MemoryError::Stale));
}
