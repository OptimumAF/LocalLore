//! Fixed reconstructed synthetic-v1 qualification fixture, never a production writer.
use locallore::{contracts::*, engine::Engine, inspection::sha256};
use locallore_storage::Store;
use serde_json::{json, Value};
use std::{fs, path::Path};

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
    // Match the existing derived_store::historical_v1 methodology: canonical rows are
    // written exclusively by Store. Only new derived-schema metadata is removed.
    let initial = include_str!("../migrations/001_initial.sql");
    let header = initial
        .split("CREATE TABLE stories")
        .next()
        .ok_or("FixtureSchema")?;
    safe_path(&path)?;
    let db = rusqlite::Connection::open(&path).map_err(|_| "FixtureDatabase")?;
    db.execute_batch(&format!("BEGIN; DROP TABLE derived_memory; DROP TABLE schema_migrations; {header} PRAGMA user_version=1; COMMIT;")).map_err(|_| "FixtureSchema")?;
    drop(db);
    inspect(&path, 1)
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
    if engine.canonical_bytes() != expected_engine.canonical_bytes()
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
    let live = inspect(&root.join(DATABASE), 2)?;
    let mut backups = Vec::new();
    for entry in fs::read_dir(root).map_err(|_| "FixtureDirectory")? {
        let entry = entry.map_err(|_| "FixtureEntry")?;
        let name = entry.file_name();
        let name = name.to_str().ok_or("FixtureName")?;
        safe_path(&entry.path())?;
        if name.starts_with("stories-v1.sqlite.before-v2-") && name.ends_with(".sqlite") {
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
