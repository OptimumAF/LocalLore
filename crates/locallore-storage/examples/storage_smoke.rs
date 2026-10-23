//! Explicit synthetic on-disk storage smoke. No models, raw SQL or private data.
use locallore::contracts::Seed;
use locallore_storage::Store;
use serde_json::{json, Value};
use std::path::Path;

#[derive(Clone, Copy)]
enum Failure {
    Arguments,
    Directory,
    Fixture,
    Open,
    Create,
    Reopen,
    Verification,
    Backup,
    BackupOverwrite,
    Panic,
}

impl Failure {
    fn code(self) -> &'static str {
        match self {
            Self::Arguments => "arguments",
            Self::Directory => "directory",
            Self::Fixture => "fixture",
            Self::Open => "open",
            Self::Create => "create",
            Self::Reopen => "reopen",
            Self::Verification => "verification",
            Self::Backup => "backup",
            Self::BackupOverwrite => "backup_overwrite",
            Self::Panic => "panic",
        }
    }
}

fn smoke(directory: &Path) -> Result<Value, Failure> {
    // Refuse a pre-existing directory instead of reusing/deleting unknown files.
    std::fs::create_dir(directory).map_err(|_| Failure::Directory)?;
    let database = directory.join("stories.sqlite");
    let backup = directory.join("migration-backup.sqlite");
    let first: Seed = serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json"))
        .map_err(|_| Failure::Fixture)?;
    let mut second = first.clone();
    second.scope.story = "quay-storage-other".into();
    second
        .items
        .get_mut("potion")
        .ok_or(Failure::Fixture)?
        .quantity = 2;
    let mut store = Store::open(&database, None).map_err(|_| Failure::Open)?;
    store
        .create_story("Lantern Quay storage smoke", first.clone())
        .map_err(|_| Failure::Create)?;
    store
        .create_story("Lantern Quay storage smoke", second.clone())
        .map_err(|_| Failure::Create)?;
    drop(store);

    let store = Store::open(&database, None).map_err(|_| Failure::Reopen)?;
    let info = store.info().map_err(|_| Failure::Verification)?;
    let sqlite_version: Vec<u32> = info
        .sqlite_version
        .split('.')
        .map(str::parse)
        .collect::<Result<_, _>>()
        .map_err(|_| Failure::Verification)?;
    if info.schema_version != 1
        || !info.foreign_keys
        || sqlite_version != [3, 53, 2]
        || store
            .load_seed(&first.scope)
            .map_err(|_| Failure::Verification)?
            != first
        || store
            .load_seed(&second.scope)
            .map_err(|_| Failure::Verification)?
            != second
    {
        return Err(Failure::Verification);
    }
    store.backup_to(&backup).map_err(|_| Failure::Backup)?;
    if store.backup_to(&backup).is_ok() {
        return Err(Failure::BackupOverwrite);
    }
    drop(store);
    let restored = Store::open(&backup, None).map_err(|_| Failure::Backup)?;
    let restored_info = restored.info().map_err(|_| Failure::Backup)?;
    if !restored_info.foreign_keys
        || restored_info.schema_version != info.schema_version
        || restored
            .load_seed(&first.scope)
            .map_err(|_| Failure::Backup)?
            != first
        || restored
            .load_seed(&second.scope)
            .map_err(|_| Failure::Backup)?
            != second
    {
        return Err(Failure::Backup);
    }
    Ok(json!({
        "version": 1,
        "status": "completed",
        "schema_version": info.schema_version,
        "sqlite_version": sqlite_version,
        "foreign_keys": info.foreign_keys,
        "stories_reopened": 2,
        "stories_backed_up": 2,
        "same_entity_ids_isolated": true,
        "existing_backup_refused": true
    }))
}

fn main() {
    // Unexpected panics must not print a path, database value or raw error.
    std::panic::set_hook(Box::new(|_| {}));
    let result = std::panic::catch_unwind(|| {
        let args: Vec<_> = std::env::args_os().skip(1).collect();
        if args.len() != 2 || args[0] != "--directory" {
            return Err(Failure::Arguments);
        }
        smoke(Path::new(&args[1]))
    })
    .unwrap_or(Err(Failure::Panic));
    let (value, code) = match result {
        Ok(value) => (value, 0),
        Err(error) => (
            json!({"version": 1, "status": "failed", "error": error.code()}),
            1,
        ),
    };
    println!("{value}");
    std::process::exit(code);
}
