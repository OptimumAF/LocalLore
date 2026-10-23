// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent M04.01 filesystem/schema tests; only original synthetic fixtures.
use locallore::contracts::{Scope, Seed};
use locallore_storage::{StorageError, Store};
use rusqlite::{params, Connection};
use std::{
    fs,
    path::{Path, PathBuf},
    sync::atomic::{AtomicU64, Ordering},
    time::{SystemTime, UNIX_EPOCH},
};

const APPLICATION_ID: i64 = 0x4c4c4f52;
const CANARY: &str = "SYNTHETIC-PRIVATE-STORAGE-731";
static NEXT: AtomicU64 = AtomicU64::new(0);

struct Sandbox {
    root: PathBuf,
    parent: PathBuf,
}
impl Sandbox {
    fn new() -> Self {
        let workspace = Path::new(env!("CARGO_MANIFEST_DIR"))
            .parent()
            .unwrap()
            .parent()
            .unwrap();
        let parent = workspace.join("target/storage-adversarial");
        fs::create_dir_all(&parent).unwrap();
        let name = format!(
            "case-{}-{}-{}",
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        );
        let root = parent.join(name);
        fs::create_dir(&root).unwrap();
        Self { root, parent }
    }
    fn path(&self, name: &str) -> PathBuf {
        self.root.join(name)
    }
}
impl Drop for Sandbox {
    fn drop(&mut self) {
        // Verify the resolved target before recursive Windows cleanup. Never
        // remove a parent, a reused path, or a symlink outside this owned area.
        if let (Ok(root), Ok(parent)) = (self.root.canonicalize(), self.parent.canonicalize()) {
            if root.parent() == Some(parent.as_path())
                && root
                    .file_name()
                    .is_some_and(|name| name.to_string_lossy().starts_with("case-"))
            {
                let _ = fs::remove_dir_all(root);
            }
        }
    }
}

fn seed(story: &str, branch: &str) -> Seed {
    let mut value: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    value.scope = Scope {
        story: story.into(),
        branch: branch.into(),
    };
    value
}
fn scope(story: &str, branch: &str) -> Scope {
    Scope {
        story: story.into(),
        branch: branch.into(),
    }
}
fn empty_database(path: &Path, application: i64, version: i64) {
    let connection = Connection::open(path).unwrap();
    connection
        .pragma_update(None, "application_id", application)
        .unwrap();
    connection
        .pragma_update(None, "user_version", version)
        .unwrap();
}
fn assert_seed(actual: Seed, expected: &Seed) {
    assert_eq!(
        serde_json::to_value(actual).unwrap(),
        serde_json::to_value(expected).unwrap()
    );
}
fn assert_fk(result: rusqlite::Result<usize>) {
    match result {
        Err(rusqlite::Error::SqliteFailure(error, _)) => assert_eq!(
            error.extended_code,
            rusqlite::ffi::SQLITE_CONSTRAINT_FOREIGNKEY
        ),
        other => panic!("expected a composite foreign-key rejection, got {other:?}"),
    }
}

#[test]
fn new_reopened_and_second_owner_connections_preserve_two_independent_stories() {
    let files = Sandbox::new();
    let database = files.path("stories.db");
    let first = seed("first", "root");
    let second = seed("second", "root");
    {
        let mut owner = Store::open(&database, None).unwrap();
        owner
            .create_story("Same display title", first.clone())
            .unwrap();
        owner
            .create_story("Same display title", second.clone())
            .unwrap();
        let concurrent = Store::open(&database, None).unwrap();
        for store in [&owner, &concurrent] {
            let info = store.info().unwrap();
            assert_eq!(info.schema_version, locallore_storage::SCHEMA_VERSION);
            assert!(info.foreign_keys);
            assert!(!info.sqlite_version.is_empty());
            assert_seed(store.load_seed(&first.scope).unwrap(), &first);
            assert_seed(store.load_seed(&second.scope).unwrap(), &second);
            assert_eq!(
                store.load_seed(&scope("first", "other")).unwrap_err(),
                StorageError::NotFound
            );
        }
    }
    let reopened = Store::open(&database, None).unwrap();
    assert!(reopened.info().unwrap().foreign_keys);
    assert_seed(reopened.load_seed(&first.scope).unwrap(), &first);
    assert_seed(reopened.load_seed(&second.scope).unwrap(), &second);
}

#[test]
fn existing_empty_migration_requires_backup_and_keeps_a_readable_original_version() {
    let files = Sandbox::new();
    let database = files.path("old.db");
    let backup = files.path("old-before-migration.db");
    empty_database(&database, APPLICATION_ID, 0);
    let before = fs::read(&database).unwrap();
    assert_eq!(
        Store::open(&database, None).err().unwrap(),
        StorageError::BackupRequired
    );
    assert_eq!(fs::read(&database).unwrap(), before);
    let store = Store::open(&database, Some(&backup)).unwrap();
    assert_eq!(
        store.info().unwrap().schema_version,
        locallore_storage::SCHEMA_VERSION
    );
    let original = Connection::open(&backup).unwrap();
    assert_eq!(
        original
            .pragma_query_value::<i64, _>(None, "user_version", |r| r.get(0))
            .unwrap(),
        0
    );
    assert_eq!(
        original
            .pragma_query_value::<i64, _>(None, "application_id", |r| r.get(0))
            .unwrap(),
        APPLICATION_ID
    );
    assert_eq!(
        original
            .query_row::<i64, _, _>("SELECT count(*) FROM sqlite_schema", [], |r| r.get(0))
            .unwrap(),
        0
    );
    assert_eq!(
        original
            .query_row::<String, _, _>("PRAGMA integrity_check", [], |r| r.get(0))
            .unwrap(),
        "ok"
    );
}

#[test]
fn nonempty_v0_object_with_sqlite_like_name_is_never_adopted_or_changed() {
    let files = Sandbox::new();
    let database = files.path("foreign.db");
    let backup = files.path("must-not-be-created.db");
    {
        let connection = Connection::open(&database).unwrap();
        connection
            .execute_batch("CREATE TABLE sqliteXprivate(secret TEXT NOT NULL);")
            .unwrap();
        connection
            .execute("INSERT INTO sqliteXprivate VALUES (?1)", [CANARY])
            .unwrap();
    }
    let before = fs::read(&database).unwrap();
    let error = Store::open(&database, Some(&backup))
        .err()
        .expect("nonempty v0 database was adopted");
    assert_eq!(error, StorageError::ForeignDatabase);
    assert_eq!(fs::read(&database).unwrap(), before);
    assert!(!backup.exists());
}

#[test]
fn altered_v1_object_with_sqlite_like_name_is_not_hidden_from_schema_verification() {
    let files = Sandbox::new();
    let database = files.path("tampered.db");
    drop(Store::open(&database, None).unwrap());
    Connection::open(&database)
        .unwrap()
        .execute_batch("CREATE TABLE sqliteXprivate(secret TEXT);")
        .unwrap();
    let before = fs::read(&database).unwrap();
    assert_eq!(
        Store::open(&database, None)
            .err()
            .expect("altered schema accepted"),
        StorageError::SchemaMismatch
    );
    assert_eq!(fs::read(&database).unwrap(), before);
}

#[test]
fn foreign_future_and_negative_versions_refuse_without_mutation_or_backup() {
    let files = Sandbox::new();
    for (name, application, version, expected) in [
        ("foreign", 1234, 1, Some(StorageError::ForeignDatabase)),
        (
            "future",
            APPLICATION_ID,
            i64::from(locallore_storage::SCHEMA_VERSION + 1),
            Some(StorageError::FutureVersion),
        ),
        ("negative", APPLICATION_ID, -1, None),
    ] {
        let database = files.path(&format!("{name}.db"));
        let backup = files.path(&format!("{name}-backup.db"));
        empty_database(&database, application, version);
        let before = fs::read(&database).unwrap();
        let error = Store::open(&database, Some(&backup)).err().unwrap();
        if let Some(expected) = expected {
            assert_eq!(error, expected);
        }
        assert_eq!(fs::read(&database).unwrap(), before);
        assert!(!backup.exists());
        assert!(!format!("{error:?} {error}").contains(CANARY));
    }
}

#[test]
fn ordinary_schema_tampering_is_refused_without_rewriting_the_database() {
    let files = Sandbox::new();
    let database = files.path("tampered.db");
    drop(Store::open(&database, None).unwrap());
    Connection::open(&database)
        .unwrap()
        .execute_batch("ALTER TABLE stories ADD COLUMN unexpected TEXT;")
        .unwrap();
    let before = fs::read(&database).unwrap();
    assert_eq!(
        Store::open(&database, None).err().unwrap(),
        StorageError::SchemaMismatch
    );
    assert_eq!(fs::read(&database).unwrap(), before);
}

#[test]
fn backup_destination_collision_never_overwrites_source_or_existing_bytes() {
    let files = Sandbox::new();
    let database = files.path("source.db");
    let destination = files.path("existing.db");
    let mut store = Store::open(&database, None).unwrap();
    let value = seed("quay", "main");
    store.create_story("Original", value.clone()).unwrap();
    fs::write(&destination, CANARY).unwrap();
    assert_eq!(
        store.backup_to(&destination),
        Err(StorageError::BackupExists)
    );
    assert_eq!(fs::read(&destination).unwrap(), CANARY.as_bytes());
    assert_eq!(store.backup_to(&database), Err(StorageError::BackupExists));
    assert_seed(store.load_seed(&value.scope).unwrap(), &value);
    let empty = files.path("empty-existing.db");
    fs::write(&empty, []).unwrap();
    assert_eq!(store.backup_to(&empty), Err(StorageError::BackupExists));
    assert_eq!(fs::metadata(empty).unwrap().len(), 0);
    let existing_directory = files.path("existing-directory");
    fs::create_dir(&existing_directory).unwrap();
    fs::write(existing_directory.join("sentinel"), CANARY).unwrap();
    assert!(store.backup_to(&existing_directory).is_err());
    assert_eq!(
        fs::read(existing_directory.join("sentinel")).unwrap(),
        CANARY.as_bytes()
    );
}

#[test]
fn migration_backup_collision_keeps_original_schema_and_data_unchanged() {
    let files = Sandbox::new();
    let database = files.path("old.db");
    let backup = files.path("existing-backup.db");
    empty_database(&database, 0, 0);
    fs::write(&backup, CANARY).unwrap();
    let before = fs::read(&database).unwrap();
    assert_eq!(
        Store::open(&database, Some(&backup)).err().unwrap(),
        StorageError::BackupExists
    );
    assert_eq!(fs::read(&database).unwrap(), before);
    assert_eq!(fs::read(&backup).unwrap(), CANARY.as_bytes());
}

#[test]
fn migration_rechecks_version_after_waiting_for_an_existing_writer() {
    let files = Sandbox::new();
    let database = files.path("concurrent-version.db");
    let backup = files.path("must-not-back-up-future.db");
    empty_database(&database, APPLICATION_ID, 0);
    let writer = Connection::open(&database).unwrap();
    writer
        .execute_batch(&format!(
            "BEGIN IMMEDIATE; PRAGMA user_version={};",
            locallore_storage::SCHEMA_VERSION + 1
        ))
        .unwrap();
    let path = database.clone();
    let destination = backup.clone();
    let (started, entered) = std::sync::mpsc::channel();
    let open = std::thread::spawn(move || {
        started.send(()).unwrap();
        Store::open(&path, Some(&destination))
    });
    entered
        .recv_timeout(std::time::Duration::from_secs(2))
        .unwrap();
    // Readers can inspect committed v0 while the writer holds its reservation.
    // On this host the owner then waits for BEGIN IMMEDIATE behind this writer.
    std::thread::sleep(std::time::Duration::from_millis(80));
    writer.execute_batch("COMMIT").unwrap();
    let result = open.join().unwrap();
    assert_eq!(
        result
            .err()
            .expect("concurrently promoted future database was adopted"),
        StorageError::FutureVersion
    );
    assert!(!backup.exists());
    assert_eq!(
        writer
            .pragma_query_value::<i64, _>(None, "user_version", |r| r.get(0))
            .unwrap(),
        i64::from(locallore_storage::SCHEMA_VERSION + 1)
    );
}

#[test]
fn invalid_seed_title_and_duplicate_story_cannot_leave_partial_records() {
    let files = Sandbox::new();
    let database = files.path("atomic.db");
    let mut store = Store::open(&database, None).unwrap();
    let original = seed("first", "root");
    store.create_story("Original", original.clone()).unwrap();
    let mut invalid = seed("second", "root");
    invalid.items.get_mut("potion").unwrap().owner = CANARY.into();
    assert_eq!(
        store.create_story("Invalid", invalid),
        Err(StorageError::InvalidSeed)
    );
    assert_eq!(
        store.create_story("bad\0title", seed("second", "root")),
        Err(StorageError::InvalidInput)
    );
    assert_eq!(
        store.create_story("Duplicate", original.clone()),
        Err(StorageError::DuplicateStory)
    );
    assert_seed(store.load_seed(&original.scope).unwrap(), &original);
    assert_eq!(
        store.load_seed(&scope("second", "root")).unwrap_err(),
        StorageError::NotFound
    );
    store
        .create_story("Valid second", seed("second", "root"))
        .unwrap();
    let raw = Connection::open(&database).unwrap();
    assert_eq!(
        raw.query_row::<i64, _, _>("SELECT count(*) FROM stories", [], |r| r.get(0))
            .unwrap(),
        2
    );
    assert_eq!(
        raw.query_row::<i64, _, _>("SELECT count(*) FROM branches", [], |r| r.get(0))
            .unwrap(),
        2
    );
}

#[test]
fn busy_writer_preserves_existing_seed_and_allows_retry_after_release() {
    let files = Sandbox::new();
    let database = files.path("busy.db");
    let mut store = Store::open(&database, None).unwrap();
    let first = seed("first", "main");
    let second = seed("second", "main");
    store.create_story("Existing story", first.clone()).unwrap();
    let writer = Connection::open(&database).unwrap();
    writer.execute_batch("BEGIN IMMEDIATE").unwrap();
    let started = std::time::Instant::now();
    assert_eq!(
        store.create_story("Blocked story", second.clone()),
        Err(StorageError::Busy)
    );
    // This is a finite host cleanup bound, not a phone/database latency target.
    assert!(started.elapsed() < std::time::Duration::from_secs(3));
    assert_seed(store.load_seed(&first.scope).unwrap(), &first);
    assert_eq!(
        store.load_seed(&second.scope).unwrap_err(),
        StorageError::NotFound
    );
    writer.execute_batch("ROLLBACK").unwrap();
    store
        .create_story("Retry after release", second.clone())
        .unwrap();
    assert_seed(store.load_seed(&second.scope).unwrap(), &second);
}

#[test]
fn consistent_backup_includes_committed_wal_frames_and_reopens_with_fk_enforced() {
    let files = Sandbox::new();
    let database = files.path("wal.db");
    let backup = files.path("snapshot.db");
    let mut store = Store::open(&database, None).unwrap();
    let value = seed("quay", "main");
    store
        .create_story("Before WAL change", value.clone())
        .unwrap();
    let writer = Connection::open(&database).unwrap();
    assert_eq!(
        writer
            .pragma_update_and_check::<_, String, _>(None, "journal_mode", "WAL", |r| r.get(0))
            .unwrap(),
        "wal"
    );
    let main_before = fs::read(&database).unwrap();
    writer
        .execute(
            "UPDATE stories SET title=?1 WHERE story_id='quay'",
            [CANARY],
        )
        .unwrap();
    assert_eq!(
        fs::read(&database).unwrap(),
        main_before,
        "test did not retain the update in WAL"
    );
    store.backup_to(&backup).unwrap();
    let snapshot = Connection::open(&backup).unwrap();
    assert_eq!(
        snapshot
            .query_row::<String, _, _>("SELECT title FROM stories WHERE story_id='quay'", [], |r| r
                .get(0))
            .unwrap(),
        CANARY
    );
    drop(snapshot);
    let reopened = Store::open(&backup, None).unwrap();
    assert!(reopened.info().unwrap().foreign_keys);
    assert_seed(reopened.load_seed(&value.scope).unwrap(), &value);
}

#[test]
fn composite_foreign_keys_reject_cross_story_branch_turn_and_observer_references() {
    let files = Sandbox::new();
    let database = files.path("scope.db");
    let mut store = Store::open(&database, None).unwrap();
    for (story, branch, extra) in [
        ("first", "first-root", "first-only"),
        ("second", "second-root", "second-only"),
    ] {
        let mut value = seed(story, branch);
        value
            .actors
            .insert(extra.into(), value.actors["mira"].clone());
        store.create_story("Same title", value).unwrap();
    }
    let raw = Connection::open(&database).unwrap();
    raw.pragma_update(None, "foreign_keys", true).unwrap();
    assert_fk(raw.execute(
        "INSERT INTO branch_entities VALUES ('second','second-root','actor','first-only')",
        [],
    ));
    assert_fk(raw.execute(
        "INSERT INTO branch_entities VALUES ('first','second-root','actor','mira')",
        [],
    ));
    for (story, branch) in [("first", "first-root"), ("second", "second-root")] {
        raw.execute(
            "INSERT INTO turns VALUES (?1,?2,'same-turn',0,'committed','{}','{}')",
            params![story, branch],
        )
        .unwrap();
        raw.execute(
            "INSERT INTO accepted_events VALUES (?1,?2,1,'same-turn',1,'{}')",
            params![story, branch],
        )
        .unwrap();
    }
    raw.execute("INSERT INTO turns VALUES ('second','second-root','second-only-turn',0,'committed','{}','{}')", []).unwrap();
    assert_fk(raw.execute(
        "INSERT INTO accepted_events VALUES ('first','first-root',2,'second-only-turn',1,'{}')",
        [],
    ));
    raw.execute(
        "INSERT INTO event_witnesses VALUES ('first','first-root',1,'actor','mira')",
        [],
    )
    .unwrap();
    assert_fk(raw.execute(
        "INSERT INTO event_witnesses VALUES ('first','first-root',1,'actor','second-only')",
        [],
    ));
    assert_fk(raw.execute(
        "INSERT INTO branch_projections VALUES ('first','second-root',0,1,'{}')",
        [],
    ));
    assert_eq!(
        raw.query_row::<i64, _, _>("SELECT count(*) FROM accepted_events", [], |r| r.get(0))
            .unwrap(),
        2
    );
    assert!(!raw
        .prepare("PRAGMA foreign_key_check")
        .unwrap()
        .exists([])
        .unwrap());
}

#[test]
fn corrupt_seed_payload_is_not_canonical_and_fixed_errors_never_echo_content_or_paths() {
    let files = Sandbox::new();
    let database = files.path(&format!("{CANARY}.db"));
    let mut store = Store::open(&database, None).unwrap();
    let value = seed("quay", "main");
    store.create_story("Original", value).unwrap();
    let raw = Connection::open(&database).unwrap();
    raw.execute(
        "UPDATE stories SET seed_json=?1",
        [format!("{{\"private\":\"{CANARY}\"}}")],
    )
    .unwrap();
    let error = store.load_seed(&scope("quay", "main")).unwrap_err();
    assert_eq!(error, StorageError::Integrity);
    assert!(!format!("{error} {error:?}").contains(CANARY));
    let missing = files.path("missing-parent").join(CANARY);
    let error = Store::open(&missing, None).err().unwrap();
    assert!(!format!("{error} {error:?}").contains(CANARY));
}
