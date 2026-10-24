//! Fixed reconstructed synthetic-v1 qualification fixture, never a production writer.
use locallore::{contracts::*, engine::Engine, inspection::sha256};
use locallore_storage::{Store, SCHEMA_VERSION};
use rusqlite::{params_from_iter, types::Value as SqlValue, Connection};
use serde_json::{json, Value};
use std::{fs, path::Path, time::Duration};

const DATABASE: &str = "stories-v1.sqlite";
const TURN: &str = "legacy-original-gift";

fn safe_path(path: &Path) -> Result<(), String> {
    if !path.is_absolute() {
        return Err("AbsoluteFixtureRootRequired".into());
    }
    for part in path.ancestors() {
        let metadata = fs::symlink_metadata(part).map_err(|_| "FixturePathUnavailable")?;
        if metadata.file_type().is_symlink() {
            return Err("FixtureReparseRefused".into());
        }
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt;
            if metadata.file_attributes() & 0x400 != 0 {
                return Err("FixtureReparseRefused".into());
            }
        }
    }
    Ok(())
}
fn owner_fixture() -> Result<(Seed, Engine, Receipt), String> {
    let seed: Seed = serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json"))
        .map_err(|_| "FixtureSeed")?;
    let mut engine = Engine::new(seed.clone()).map_err(|_| "FixtureEngine")?;
    let request = engine.request(
        TURN,
        Intent::Actions(vec![Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 1,
        }]),
    );
    let proposal = Engine::proposal(&request).map_err(|_| "FixtureProposal")?;
    let text = engine
        .preview(&request, &proposal)
        .map_err(|_| "FixturePreview")?;
    let receipt = engine
        .commit(&request, &proposal, text.narration())
        .map_err(|_| "FixtureCommit")?;
    Ok((seed, engine, receipt))
}
fn create(root: &Path) -> Result<Value, String> {
    if root.file_name().and_then(|x| x.to_str()) != Some("legacy-fixture") {
        return Err("FixedFixtureDirectoryRequired".into());
    }
    safe_path(root.parent().ok_or("FixtureParent")?)?;
    // Existing directories, files and links are all refused; never open a caller's save.
    fs::create_dir(root).map_err(|_| "NewFixtureDirectoryRequired")?;
    safe_path(root)?;
    let path = root.join(DATABASE);
    let (seed, _, expected) = owner_fixture()?;
    let mut store = Store::open(&path, None).map_err(|_| "FixtureStore")?;
    store
        .create_story("Synthetic legacy Lantern Quay", seed)
        .map_err(|_| "FixtureStory")?;
    store
        .begin_turn(expected.request())
        .map_err(|_| "FixtureBegin")?;
    store
        .commit_turn(
            expected.request(),
            expected.proposal(),
            expected.narration(),
        )
        .map_err(|_| "FixtureSave")?;
    drop(store);
    reconstruct_v1(&path)?;
    inspect(&path, 1)
}
/// Fixed synthetic reconstruction, not an old Store writer or production downgrade.
/// Only create() calls this after exclusively creating this directory and Store.
fn reconstruct_v1(path: &Path) -> Result<(), String> {
    if path.file_name().and_then(|name| name.to_str()) != Some(DATABASE)
        || path
            .parent()
            .and_then(Path::file_name)
            .and_then(|name| name.to_str())
            != Some("legacy-fixture")
    {
        return Err("FixedFixtureDatabaseRequired".into());
    }
    safe_path(path)?;
    let metadata = fs::symlink_metadata(path).map_err(|_| "FixtureRead")?;
    if !metadata.is_file() || metadata.len() > 64 * 1024 * 1024 {
        return Err("BoundedFixtureDatabaseRequired".into());
    }
    // Validate the actual source via read-only Store/Core before copying bytes.
    // inspect closes its Store and proves read-only byte equality itself.
    inspect(path, SCHEMA_VERSION)?;
    let mut destination = Connection::open(path).map_err(|_| "FixtureDatabase")?;
    let nonlegacy: i64 = destination
        .query_row(
            "SELECT (SELECT count(*) FROM turns WHERE canonical_kind<>'legacy_play') +
                (SELECT count(*) FROM accepted_events WHERE record_kind<>'play') +
                (SELECT count(*) FROM branch_projections WHERE projection_version<>1)",
            [],
            |row| row.get(0),
        )
        .map_err(|_| "FixtureSourceKind")?;
    if nonlegacy != 0 {
        return Err("FixtureSourceKind".into());
    }
    let mut historical = Connection::open_in_memory().map_err(|_| "FixtureDatabase")?;
    historical
        .pragma_update(None, "foreign_keys", true)
        .map_err(|_| "FixtureSchema")?;
    historical
        .execute_batch(include_str!("../migrations/001_initial.sql"))
        .map_err(|_| "FixtureSchema")?;
    historical
        .pragma_update(None, "application_id", 0x4c4c4f52_u32)
        .map_err(|_| "FixtureSchema")?;
    historical
        .pragma_update(None, "user_version", 1u32)
        .map_err(|_| "FixtureSchema")?;
    // Exact original columns only; do not relabel current5 tables/CHECKs as1.
    // This inventory mirrors the fixed historical test factory without importing
    // or broadening its unrelated TEMP/PID-family admission rules.
    let tables: [(&str, &[&str]); 8] = [
        (
            "stories",
            &[
                "story_id",
                "root_branch",
                "title",
                "seed_version",
                "seed_json",
            ],
        ),
        (
            "branches",
            &[
                "story_id",
                "branch_id",
                "parent_branch",
                "fork_revision",
                "head_revision",
            ],
        ),
        ("entities", &["story_id", "kind", "entity_id"]),
        (
            "branch_entities",
            &["story_id", "branch_id", "kind", "entity_id"],
        ),
        (
            "turns",
            &[
                "story_id",
                "branch_id",
                "turn_id",
                "expected_revision",
                "status",
                "request_json",
                "response_json",
            ],
        ),
        (
            "accepted_events",
            &[
                "story_id",
                "branch_id",
                "sequence",
                "turn_id",
                "event_version",
                "envelope_json",
            ],
        ),
        (
            "event_witnesses",
            &[
                "story_id",
                "branch_id",
                "sequence",
                "observer_kind",
                "observer_id",
            ],
        ),
        (
            "branch_projections",
            &[
                "story_id",
                "branch_id",
                "revision",
                "projection_version",
                "projection_json",
            ],
        ),
    ];
    {
        let tx = historical.transaction().map_err(|_| "FixtureTransaction")?;
        tx.pragma_update(None, "defer_foreign_keys", true)
            .map_err(|_| "FixtureSchema")?;
        for (table, columns) in tables {
            let actual_columns: Vec<String> = tx
                .prepare(&format!("PRAGMA table_info({table})"))
                .map_err(|_| "FixtureSchema")?
                .query_map([], |row| row.get(1))
                .map_err(|_| "FixtureSchema")?
                .collect::<rusqlite::Result<_>>()
                .map_err(|_| "FixtureSchema")?;
            if actual_columns
                != columns
                    .iter()
                    .map(|name| name.to_string())
                    .collect::<Vec<_>>()
            {
                return Err("FixtureColumnInventory".into());
            }
            let names = columns.join(",");
            let placeholders = (1..=columns.len())
                .map(|n| format!("?{n}"))
                .collect::<Vec<_>>()
                .join(",");
            let mut read = destination
                .prepare(&format!("SELECT {names} FROM {table}"))
                .map_err(|_| "FixtureRead")?;
            let rows = read
                .query_map([], |row| {
                    (0..columns.len())
                        .map(|index| row.get::<_, SqlValue>(index))
                        .collect::<rusqlite::Result<Vec<_>>>()
                })
                .map_err(|_| "FixtureRead")?;
            let mut write = tx
                .prepare(&format!(
                    "INSERT INTO {table}({names}) VALUES({placeholders})"
                ))
                .map_err(|_| "FixtureWrite")?;
            for row in rows {
                let values = row.map_err(|_| "FixtureRead")?;
                write
                    .execute(params_from_iter(values.iter()))
                    .map_err(|_| "FixtureWrite")?;
            }
        }
        if tx
            .prepare("PRAGMA foreign_key_check")
            .map_err(|_| "FixtureForeignKeys")?
            .exists([])
            .map_err(|_| "FixtureForeignKeys")?
        {
            return Err("FixtureForeignKeys".into());
        }
        tx.commit().map_err(|_| "FixtureTransaction")?;
    }
    // Both handles are private to the fixed new fixture. SQLite copies the exact
    // historical database, including its old column inventory and constraints.
    rusqlite::backup::Backup::new(&historical, &mut destination)
        .map_err(|_| "FixtureBackup")?
        .run_to_completion(128, Duration::ZERO, None)
        .map_err(|_| "FixtureBackup")?;
    if destination
        .prepare("PRAGMA foreign_key_check")
        .map_err(|_| "FixtureForeignKeys")?
        .exists([])
        .map_err(|_| "FixtureForeignKeys")?
    {
        return Err("FixtureForeignKeys".into());
    }
    Ok(())
}
fn inspect(path: &Path, version: u32) -> Result<Value, String> {
    safe_path(path)?;
    let before = fs::read(path).map_err(|_| "FixtureRead")?;
    let (_, expected_engine, expected_receipt) = owner_fixture()?;
    let mut store = Store::open_read_only(path).map_err(|_| "FixtureReadOnly")?;
    let info = store.info().map_err(|_| "FixtureInfo")?;
    if info.schema_version != version {
        return Err("FixtureVersion".into());
    }
    let stories = store.stories().map_err(|_| "FixtureStories")?;
    if stories.len() != 1
        || stories[0].scope != *expected_engine.scope()
        || stories[0].revision != 1
        || stories[0].drafts != 0
    {
        return Err("FixtureLibrary".into());
    }
    let engine = store
        .resume(expected_engine.scope())
        .map_err(|_| "FixtureReplay")?
        .engine;
    if engine.domain_version() != 1
        || engine.canonical_bytes() != expected_engine.canonical_bytes()
        || engine.receipts() != [expected_receipt.clone()]
    {
        return Err("FixtureCanonicalMismatch".into());
    }
    drop(store);
    let after = fs::read(path).map_err(|_| "FixtureRead")?;
    if before != after {
        return Err("ReadOnlyChangedFixture".into());
    }
    Ok(
        json!({"synthetic":true,"reconstructed_v1":true,"schema_version":version,"scope":engine.scope(),"revision":engine.revision(),"receipts":engine.receipts().len(),"canonical_sha256":sha256(&engine.canonical_bytes()),"receipt_sha256":sha256(&serde_json::to_vec(&expected_receipt).map_err(|_| "FixtureReceipt")?),"database_sha256":sha256(&after),"read_only_unchanged":true}),
    )
}
fn verify(root: &Path) -> Result<Value, String> {
    if root.file_name().and_then(|x| x.to_str()) != Some("legacy-fixture") {
        return Err("FixedFixtureDirectoryRequired".into());
    }
    safe_path(root)?;
    let live = inspect(&root.join(DATABASE), SCHEMA_VERSION)?;
    let mut backups = Vec::new();
    for entry in fs::read_dir(root).map_err(|_| "FixtureDirectory")? {
        let entry = entry.map_err(|_| "FixtureEntry")?;
        let name = entry.file_name();
        let name = name.to_str().ok_or("FixtureName")?;
        safe_path(&entry.path())?;
        if name.starts_with(&format!("stories-v1.sqlite.before-v{SCHEMA_VERSION}-"))
            && name.ends_with(".sqlite")
        {
            backups.push(entry.path());
        } else if name != DATABASE
            && !["webview-profile", "inspection-preview-cache"].contains(&name)
        {
            return Err("UnexpectedFixtureFile".into());
        }
    }
    if backups.len() != 1 {
        return Err("ExactlyOneBackupRequired".into());
    }
    let backup = inspect(&backups[0], 1)?;
    if live["canonical_sha256"] != backup["canonical_sha256"]
        || live["receipt_sha256"] != backup["receipt_sha256"]
    {
        return Err("BackupCanonicalMismatch".into());
    }
    Ok(
        json!({"synthetic":true,"reconstructed_v1":true,"live":live,"backup":backup,"backup_count":1}),
    )
}
fn run() -> Result<Value, String> {
    let args: Vec<_> = std::env::args_os().skip(1).collect();
    if args.len() != 2 {
        return Err("FixedFixtureArguments".into());
    }
    match args[0].to_str() {
        Some("create") => create(Path::new(&args[1])),
        Some("verify") => verify(Path::new(&args[1])),
        _ => Err("FixedFixtureOperation".into()),
    }
}
fn main() {
    match run() {
        Ok(report) => println!("{report}"),
        Err(category) => {
            eprintln!("{category}");
            std::process::exit(1);
        }
    }
}
