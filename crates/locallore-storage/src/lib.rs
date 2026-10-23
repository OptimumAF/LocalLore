// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Rust's sole SQLite owner for validated seeds and atomic root-history turns.
#[cfg(any(test, feature = "development-fixtures"))]
pub mod archive_capacity_fixture;
#[cfg(test)]
mod archive_full_tests;
mod branch_catalog;
mod branch_retention;
pub use branch_retention::{BranchDeletionOutcome, BranchDeletionPreview, PreparedBranchDeletion};
mod branches;
mod retention_state;
pub use branch_catalog::{BranchCatalog, BranchSummary};
mod story_deletion;
pub use story_deletion::{
    DeletionError, PreparedStoryDeletion, StoryDeletionOutcome, StoryDeletionPreview,
};
pub mod playable_archive;
pub use playable_archive::{
    validate_archive, ArchiveError, ArchivePreview, ImportOutcome, PlayableArchive,
    ValidatedArchive,
};
mod catalog;
pub use branches::{ForkOutcome, ForkRequest, MAX_BRANCHES_PER_STORY, MAX_BRANCH_DEPTH};
pub mod derived_memory;
pub mod memory_jobs;
mod turns;
pub use catalog::StorySummary;
use locallore::{
    contracts::{Scope, Seed},
    engine::Engine,
};
use rusqlite::{Connection, OpenFlags, OptionalExtension, TransactionBehavior};
use std::{
    fs::OpenOptions,
    path::{Path, PathBuf},
    time::{Duration, Instant},
};
pub use turns::{ResumedStory, TurnError, TurnPhase, TurnRecord};

pub const SCHEMA_VERSION: u32 = 4;
pub const MAX_INSPECTION_DATABASE_BYTES: u64 = 64 * 1024 * 1024;
const APPLICATION_ID: u32 = 0x4c4c4f52;
const SCHEMA: &str = include_str!("../migrations/001_initial.sql");

/// Fixed categories deliberately omit paths, SQL, seed text and native error messages.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum StorageError {
    Io,
    Database,
    ForeignDatabase,
    FutureVersion,
    SchemaMismatch,
    BackupRequired,
    BackupExists,
    Busy,
    InvalidSeed,
    DuplicateStory,
    NotFound,
    InvalidInput,
    Integrity,
}
impl std::fmt::Display for StorageError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{self:?}")
    }
}
impl std::error::Error for StorageError {}
impl From<rusqlite::Error> for StorageError {
    fn from(error: rusqlite::Error) -> Self {
        match error.sqlite_error_code() {
            Some(rusqlite::ErrorCode::DatabaseBusy | rusqlite::ErrorCode::DatabaseLocked) => {
                Self::Busy
            }
            _ => Self::Database,
        }
    }
}
pub type Result<T> = std::result::Result<T, StorageError>;

#[derive(Debug, PartialEq, Eq)]
pub struct StoreInfo {
    pub schema_version: u32,
    pub foreign_keys: bool,
    pub sqlite_version: String,
}

/// No connection, SQL executor or deserializer for accepted events crosses this boundary.
pub struct Store {
    // Field order is intentional: SQLite closes BEFORE all staging reservations.
    connection: Connection,
    _staging_guards: Vec<std::fs::File>,
    // Native job capabilities belong to one Store instance, including when two
    // owners open identical or cloned databases with colliding persisted IDs.
    memory_job_owner: std::sync::Arc<()>,
}

#[cfg(windows)]
fn reserve_new_leaf(path: &Path, share_mode: u32) -> Result<std::fs::File> {
    use std::os::windows::fs::{MetadataExt, OpenOptionsExt};
    let leaf = path
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or(StorageError::InvalidInput)?;
    if !path.is_absolute()
        || path
            .components()
            .any(|c| matches!(c, std::path::Component::ParentDir))
        || leaf.contains([':', '\0'])
        || leaf.ends_with(['.', ' '])
    {
        return Err(StorageError::InvalidInput);
    }
    // CREATE_NEW refuses all existing leaves, including dangling reparses. Do
    // not request DELETE access: SQLite's second handle does not share DELETE.
    let file = OpenOptions::new()
        .read(true)
        .write(true)
        .create_new(true)
        .share_mode(share_mode) // Main permits READ/WRITE; sidecars READ only. Never DELETE.
        .custom_flags(0x0020_0000) // FILE_FLAG_OPEN_REPARSE_POINT.
        .open(path)
        .map_err(|_| StorageError::Io)?;
    let metadata = file.metadata().map_err(|_| StorageError::Io)?;
    if !metadata.is_file() || metadata.file_attributes() & 0x400 != 0 {
        return Err(StorageError::Integrity);
    }
    Ok(file)
}

#[cfg(windows)]
fn reserve_new_staging(path: &Path) -> Result<Vec<std::fs::File>> {
    let mut guards = Vec::with_capacity(4);
    for suffix in ["", "-journal", "-wal", "-shm"] {
        let mut name = path.as_os_str().to_owned();
        name.push(suffix);
        // Sidecars are zero-length sentinels. Deny WRITE as well as DELETE so
        // no compatible watcher can install hot-journal/WAL bytes before open.
        let sharing = if suffix.is_empty() { 0x1 | 0x2 } else { 0x1 };
        guards.push(reserve_new_leaf(Path::new(&name), sharing)?);
    }
    Ok(guards)
}

#[cfg(all(test, windows))]
struct PinnedNewHooks {
    after_reservation: fn(&Path) -> Result<()>,
    after_connect: fn(&Connection) -> Result<()>,
}

fn configure(connection: &Connection) -> Result<()> {
    connection.busy_timeout(Duration::from_millis(250))?;
    connection.pragma_update(None, "foreign_keys", true)?;
    connection.pragma_update(None, "trusted_schema", false)?;
    // Actor-scoped TEMP FTS contains story plaintext. Never spill that corpus to
    // the OS temporary directory; require the connection-local memory policy.
    connection.pragma_update(None, "temp_store", "MEMORY")?;
    connection.pragma_update(None, "synchronous", "FULL")?;
    let enabled: bool = connection.pragma_query_value(None, "foreign_keys", |r| r.get(0))?;
    let temp_store: u32 = connection.pragma_query_value(None, "temp_store", |r| r.get(0))?;
    if !enabled || temp_store != 2 {
        return Err(StorageError::Integrity);
    }
    Ok(())
}
fn connect(path: &Path, read_only: bool) -> Result<Connection> {
    let connection = connect_unconfigured(path, read_only)?;
    configure(&connection)?;
    Ok(connection)
}
fn connect_unconfigured(path: &Path, read_only: bool) -> Result<Connection> {
    let flags = if read_only {
        OpenFlags::SQLITE_OPEN_READ_ONLY
    } else {
        OpenFlags::SQLITE_OPEN_READ_WRITE
    };
    Ok(Connection::open_with_flags(
        path,
        flags | OpenFlags::SQLITE_OPEN_NO_MUTEX,
    )?)
}
#[cfg(windows)]
fn connect_staging(path: &Path) -> Result<Connection> {
    let connection = connect_unconfigured(path, false)?;
    // Preparing journal_mode can load schema/hot-journal state. ALL exact
    // sidecars must already be exclusively created and pinned before this call.
    connection.pragma_update(None, "journal_mode", "MEMORY")?;
    let mode: String = connection.pragma_query_value(None, "journal_mode", |r| r.get(0))?;
    if mode != "memory" {
        return Err(StorageError::Integrity);
    }
    configure(&connection)?;
    Ok(connection)
}
fn identity(connection: &Connection) -> Result<(u32, u32)> {
    Ok((
        connection.pragma_query_value(None, "application_id", |r| r.get(0))?,
        connection.pragma_query_value(None, "user_version", |r| r.get(0))?,
    ))
}
fn supported_identity(application: u32, version: u32) -> Result<()> {
    if version > SCHEMA_VERSION {
        return Err(StorageError::FutureVersion);
    }
    if application != 0 && application != APPLICATION_ID {
        return Err(StorageError::ForeignDatabase);
    }
    Ok(())
}
fn schema_rows(connection: &Connection) -> Result<Vec<(String, String, String, String)>> {
    let mut query = connection.prepare("SELECT type,name,tbl_name,sql FROM sqlite_schema WHERE name NOT GLOB 'sqlite_*' ORDER BY type,name")?;
    let rows = query.query_map([], |r| Ok((r.get(0)?, r.get(1)?, r.get(2)?, r.get(3)?)))?;
    Ok(rows.collect::<std::result::Result<Vec<_>, _>>()?)
}
fn verify_version(connection: &Connection, version: u32) -> Result<()> {
    if !(1..=SCHEMA_VERSION).contains(&version)
        || identity(connection)? != (APPLICATION_ID, version)
    {
        return Err(StorageError::SchemaMismatch);
    }
    let reference = Connection::open_in_memory()?;
    configure(&reference)?;
    reference.execute_batch(SCHEMA)?;
    if version >= 2 {
        reference.execute_batch(derived_memory::DERIVED_SCHEMA_SQL)?;
    }
    if version >= 3 {
        reference.execute_batch(retention_state::SCHEMA_SQL)?;
    }
    if version >= 4 {
        reference.execute_batch(memory_jobs::SCHEMA_SQL)?;
    }
    if schema_rows(connection)? != schema_rows(&reference)? {
        return Err(StorageError::SchemaMismatch);
    }
    let mut query =
        connection.prepare("SELECT version,contract FROM schema_migrations ORDER BY version")?;
    let contracts = query
        .query_map([], |row| {
            Ok((row.get::<_, u32>(0)?, row.get::<_, String>(1)?))
        })?
        .collect::<std::result::Result<Vec<_>, _>>()?;
    let mut expected = vec![(1, "locallore-storage-v1".to_owned())];
    if version >= 2 {
        expected.push((2, "locallore-storage-v2-derived-memory".to_owned()));
    }
    if version >= 3 {
        expected.push((3, "locallore-storage-v3-branch-retention".to_owned()));
    }
    if version >= 4 {
        expected.push((4, "locallore-storage-v4-memory-jobs".to_owned()));
    }
    if contracts != expected {
        return Err(StorageError::SchemaMismatch);
    }
    let integrity: String = connection.query_row("PRAGMA quick_check", [], |r| r.get(0))?;
    if integrity != "ok" || connection.prepare("PRAGMA foreign_key_check")?.exists([])? {
        return Err(StorageError::Integrity);
    }
    Ok(())
}
fn verify(connection: &Connection) -> Result<()> {
    verify_version(connection, SCHEMA_VERSION)
}

// Reserve with create_new so backups never overwrite a story, symlink or existing file.
struct Reserved {
    path: PathBuf,
    keep: bool,
}
impl Reserved {
    fn new(path: &Path) -> Result<Self> {
        let file = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(path)
            .map_err(|e| {
                if e.kind() == std::io::ErrorKind::AlreadyExists {
                    StorageError::BackupExists
                } else {
                    StorageError::Io
                }
            })?;
        let reserved = Self {
            path: path.into(),
            keep: false,
        };
        file.sync_all().map_err(|_| StorageError::Io)?;
        Ok(reserved)
    }
}
impl Drop for Reserved {
    fn drop(&mut self) {
        if !self.keep {
            let _ = std::fs::remove_file(&self.path);
        }
    }
}

fn consistent_backup(source: &Connection, path: &Path) -> Result<()> {
    let mut reserved = Reserved::new(path)?;
    {
        let mut destination = connect(path, false)?;
        let backup = rusqlite::backup::Backup::new(source, &mut destination)?;
        let deadline = Instant::now() + Duration::from_secs(5);
        loop {
            match backup.step(64)? {
                rusqlite::backup::StepResult::Done => break,
                rusqlite::backup::StepResult::More => {}
                rusqlite::backup::StepResult::Busy | rusqlite::backup::StepResult::Locked => {
                    if Instant::now() >= deadline {
                        return Err(StorageError::Busy);
                    }
                    std::thread::sleep(Duration::from_millis(5));
                }
                _ => return Err(StorageError::Database),
            }
            if Instant::now() >= deadline {
                return Err(StorageError::Busy);
            }
        }
    }
    // Persist the complete standalone database before allowing a migration to proceed.
    OpenOptions::new()
        .read(true)
        .write(true)
        .open(path)
        .and_then(|f| f.sync_all())
        .map_err(|_| StorageError::Io)?;
    reserved.keep = true;
    Ok(())
}

fn initialize(connection: &Connection, sql: &str) -> Result<()> {
    connection.execute_batch(sql)?;
    connection.execute_batch(derived_memory::DERIVED_SCHEMA_SQL)?;
    connection.execute_batch(retention_state::SCHEMA_SQL)?;
    connection.execute_batch(memory_jobs::SCHEMA_SQL)?;
    connection.pragma_update(None, "application_id", APPLICATION_ID)?;
    connection.pragma_update(None, "user_version", SCHEMA_VERSION)?;
    verify(connection)
}
fn migrate_known(connection: &Connection, version: u32) -> Result<()> {
    if version == 1 {
        connection.execute_batch(derived_memory::DERIVED_SCHEMA_SQL)?;
    }
    if version < 3 {
        connection.execute_batch(retention_state::SCHEMA_SQL)?;
    }
    connection.execute_batch(memory_jobs::SCHEMA_SQL)?;
    connection.pragma_update(None, "user_version", SCHEMA_VERSION)?;
    verify(connection)
}

impl Store {
    fn from_connection(connection: Connection) -> Self {
        Self {
            connection,
            _staging_guards: Vec::new(),
            memory_job_owner: std::sync::Arc::new(()),
        }
    }
    /// Create a disposable Windows staging Store, with MEMORY rollback journal.
    /// Reserve main/-journal/-wal/-shm BEFORE SQLite; retain no-DELETE guards
    /// (sidecars also deny WRITE) until AFTER SQLite closes. Refuse any existing
    /// leaf/sidecar. This API is NOT a crash-durable active-workspace opener.
    /// Caller MUST retain a trusted ancestor chain for the entire Store lifetime;
    /// this is namespace protection, not a same-user/OS security sandbox.
    /// On failure exclusively created empty/partial staging files may remain. No path
    /// cleanup is attempted; the trusted staging owner must handle it separately.
    /// Non-Windows callers fail closed with InvalidInput; no weaker fallback.
    pub fn create_new_pinned(path: &Path) -> Result<Self> {
        #[cfg(windows)]
        {
            #[cfg(test)]
            {
                Self::create_new_pinned_inner(
                    path,
                    PinnedNewHooks {
                        after_reservation: |_| Ok(()),
                        after_connect: |_| Ok(()),
                    },
                )
            }
            #[cfg(not(test))]
            {
                Self::create_new_pinned_inner(path)
            }
        }
        #[cfg(not(windows))]
        {
            let _ = path;
            Err(StorageError::InvalidInput)
        }
    }
    #[cfg(windows)]
    fn create_new_pinned_inner(path: &Path, #[cfg(test)] hooks: PinnedNewHooks) -> Result<Self> {
        let guards = reserve_new_staging(path)?;
        #[cfg(test)]
        (hooks.after_reservation)(path)?;
        let connection = connect_staging(path)?;
        #[cfg(test)]
        (hooks.after_connect)(&connection)?;
        // Never adopt a populated database even if someone wrote into this new
        // leaf through compatible write sharing. No overwrite or migration here.
        if identity(&connection)? != (0, 0) || !schema_rows(&connection)?.is_empty() {
            return Err(StorageError::Integrity);
        }
        let mut store = Self::open_connection(path, None, true, connection)?;
        store._staging_guards = guards;
        Ok(store)
    }
    /// Trusted application-private path only. Upgrade known old databases with a unique,
    /// nonoverwrite sibling backup; never adopt a foreign or altered schema.
    pub fn open_application(path: &Path) -> Result<Self> {
        match Self::open(path, None) {
            Err(StorageError::BackupRequired) => {
                use std::sync::atomic::{AtomicU64, Ordering};
                static NEXT_BACKUP: AtomicU64 = AtomicU64::new(0);
                let mut filename = path
                    .file_name()
                    .ok_or(StorageError::InvalidInput)?
                    .to_os_string();
                let time = std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .map_err(|_| StorageError::Io)?
                    .as_nanos();
                filename.push(format!(
                    ".before-v{SCHEMA_VERSION}-{}-{time}-{}.sqlite",
                    std::process::id(),
                    NEXT_BACKUP.fetch_add(1, Ordering::Relaxed)
                ));
                Self::open(path, Some(&path.with_file_name(filename)))
            }
            result => result,
        }
    }
    /// Inspection/backup source only: never create, migrate or expose a writable connection.
    pub fn open_read_only(path: &Path) -> Result<Self> {
        let connection = connect(path, true)?;
        let (application, version) = identity(&connection)?;
        supported_identity(application, version)?;
        verify_version(&connection, version)?;
        Ok(Self::from_connection(connection))
    }
    /// New paths initialize the current schema. Existing v0/v1/v2/v3 upgrades require a new safety
    /// backup. Foreign/nonempty v0, future or altered schemas are refused, never adopted.
    pub fn open(path: &Path, migration_backup: Option<&Path>) -> Result<Self> {
        let new_file = match OpenOptions::new().write(true).create_new(true).open(path) {
            Ok(file) => {
                drop(file);
                true
            }
            Err(e) if e.kind() == std::io::ErrorKind::AlreadyExists => false,
            Err(_) => return Err(StorageError::Io),
        };
        Self::open_connection(path, migration_backup, new_file, connect(path, false)?)
    }
    fn open_connection(
        path: &Path,
        migration_backup: Option<&Path>,
        new_file: bool,
        mut connection: Connection,
    ) -> Result<Self> {
        let (application, version) = identity(&connection)?;
        supported_identity(application, version)?;
        if version == 0 {
            let transaction =
                connection.transaction_with_behavior(TransactionBehavior::Immediate)?;
            // A second process may have changed identity while this opener waited for the lock.
            let locked_identity = identity(&transaction)?;
            supported_identity(locked_identity.0, locked_identity.1)?;
            if locked_identity != (application, version) {
                return Err(StorageError::Busy);
            }
            if !schema_rows(&transaction)?.is_empty() {
                return Err(StorageError::ForeignDatabase);
            }
            if !new_file {
                let backup_path = migration_backup.ok_or(StorageError::BackupRequired)?;
                // A separate reader sees committed data while our IMMEDIATE transaction blocks writers.
                let reader = connect(path, true)?;
                consistent_backup(&reader, backup_path)?;
            }
            initialize(&transaction, SCHEMA)?;
            transaction.commit()?;
        }
        if (1..SCHEMA_VERSION).contains(&version) {
            let transaction =
                connection.transaction_with_behavior(TransactionBehavior::Immediate)?;
            let locked = identity(&transaction)?;
            supported_identity(locked.0, locked.1)?;
            if locked != (application, version) {
                return Err(StorageError::Busy);
            }
            verify_version(&transaction, version)?;
            let backup_path = migration_backup.ok_or(StorageError::BackupRequired)?;
            let reader = connect(path, true)?;
            consistent_backup(&reader, backup_path)?;
            migrate_known(&transaction, version)?;
            transaction.commit()?;
        }
        verify(&connection)?;
        Ok(Self::from_connection(connection))
    }
    pub fn info(&self) -> Result<StoreInfo> {
        Ok(StoreInfo {
            schema_version: identity(&self.connection)?.1,
            foreign_keys: self
                .connection
                .pragma_query_value(None, "foreign_keys", |r| r.get(0))?,
            sqlite_version: self
                .connection
                .query_row("SELECT sqlite_version()", [], |r| r.get(0))?,
        })
    }
    /// Admission only; canonical state must still pass scoped replay before use.
    pub fn is_branch_active(&self, scope: &Scope) -> Result<bool> {
        if retention_state::retired(&self.connection, scope)? {
            return Ok(false);
        }
        Ok(self.connection.query_row(
            "SELECT EXISTS(SELECT 1 FROM branches WHERE story_id=?1 AND branch_id=?2)",
            (&scope.story, &scope.branch),
            |row| row.get(0),
        )?)
    }
    fn memory_engine(
        connection: &Connection,
        scope: &Scope,
        cancel: &dyn Fn() -> bool,
    ) -> std::result::Result<Engine, derived_memory::MemoryError> {
        use derived_memory::{check, MemoryError};
        check(cancel)?;
        if identity(connection).map_err(|_| MemoryError::Database)?.1 != SCHEMA_VERSION {
            return Err(MemoryError::Unsupported);
        }
        let engine = turns::read_engine(connection, scope)
            .map_err(|error| match error {
                TurnError::Engine(error) => MemoryError::from(error),
                TurnError::Storage(StorageError::Busy) => MemoryError::Busy,
                TurnError::Storage(StorageError::NotFound) | TurnError::UnknownTurn => {
                    MemoryError::NotFound
                }
                TurnError::Stale => MemoryError::Stale,
                TurnError::TooLarge => MemoryError::TooLarge,
                TurnError::Full => MemoryError::Full,
                TurnError::Integrity | TurnError::Storage(StorageError::Integrity) => {
                    MemoryError::Integrity
                }
                _ => MemoryError::Database,
            })?
            .engine;
        check(cancel)?;
        Ok(engine)
    }
    /// Prepare from this owner's validated accepted history, never a caller-provided Engine.
    pub fn prepare_memory(
        &mut self,
        request: &derived_memory::PrepareRequest,
        cancel: &dyn Fn() -> bool,
    ) -> std::result::Result<derived_memory::PreparedMemory, derived_memory::MemoryError> {
        let tx = self.connection.transaction()?;
        let engine = Self::memory_engine(&tx, &request.scope, cancel)?;
        let prepared = derived_memory::prepare(&engine, request, cancel)?;
        derived_memory::check(cancel)?;
        tx.commit()?;
        Ok(prepared)
    }
    pub fn publish_memory(
        &mut self,
        prepared: derived_memory::PreparedMemory,
        cancel: &dyn Fn() -> bool,
    ) -> std::result::Result<derived_memory::PublishOutcome, derived_memory::MemoryError> {
        derived_memory::check(cancel)?;
        let tx = self
            .connection
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        let engine = Self::memory_engine(&tx, prepared.scope(), cancel)?;
        let outcome = derived_memory::publish_in_snapshot(&tx, &engine, prepared, cancel)?;
        derived_memory::check(cancel)?;
        tx.commit()?;
        Ok(outcome)
    }
    pub fn read_memory(
        &mut self,
        request: &derived_memory::PrepareRequest,
        cancel: &dyn Fn() -> bool,
    ) -> std::result::Result<derived_memory::SummaryPacket, derived_memory::MemoryError> {
        let tx = self.connection.transaction()?;
        let engine = Self::memory_engine(&tx, &request.scope, cancel)?;
        let packet = derived_memory::read_in_snapshot(&tx, &engine, request, cancel)?;
        derived_memory::check(cancel)?;
        tx.commit()?;
        Ok(packet)
    }
    pub fn search_memory(
        &mut self,
        request: &derived_memory::SearchRequest,
        cancel: &dyn Fn() -> bool,
    ) -> std::result::Result<Vec<derived_memory::SearchHit>, derived_memory::MemoryError> {
        let tx = self.connection.transaction()?;
        let engine = Self::memory_engine(&tx, &request.scope, cancel)?;
        let hits = derived_memory::search_in_snapshot(&tx, &engine, request, cancel)?;
        derived_memory::check(cancel)?;
        tx.commit()?;
        Ok(hits)
    }
    pub fn invalidate_memory(
        &mut self,
        scope: &Scope,
        observer: &str,
        expected_revision: u64,
        cancel: &dyn Fn() -> bool,
    ) -> std::result::Result<(), derived_memory::MemoryError> {
        derived_memory::check(cancel)?;
        let tx = self
            .connection
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        let engine = Self::memory_engine(&tx, scope, cancel)?;
        if !engine.state().actors.contains_key(observer) {
            return Err(derived_memory::MemoryError::NotFound);
        }
        derived_memory::invalidate_in_snapshot(&tx, scope, observer, expected_revision, cancel)?;
        derived_memory::check(cancel)?;
        tx.commit()?;
        Ok(())
    }
    pub fn create_story(&mut self, title: &str, seed: Seed) -> Result<()> {
        self.create_story_bounded(title, seed, false)
    }
    fn create_story_bounded(&mut self, title: &str, seed: Seed, bounded: bool) -> Result<()> {
        if title.is_empty() || title.chars().count() > 256 || title.contains('\0') {
            return Err(StorageError::InvalidInput);
        }
        let engine = Engine::new(seed).map_err(|_| StorageError::InvalidSeed)?;
        let seed = engine.seed();
        let seed_json = serde_json::to_string(seed).map_err(|_| StorageError::InvalidSeed)?;
        if seed_json.len() > 131072 {
            return Err(StorageError::InvalidSeed);
        }
        let transaction = self
            .connection
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        if bounded
            && transaction.query_row("SELECT count(*) FROM stories", [], |r| r.get::<_, i64>(0))?
                >= 256
        {
            return Err(StorageError::InvalidInput);
        }
        if transaction
            .query_row(
                "SELECT 1 FROM stories WHERE story_id=?1",
                [&seed.scope.story],
                |_| Ok(()),
            )
            .optional()?
            .is_some()
        {
            return Err(StorageError::DuplicateStory);
        }
        transaction.execute(
            "INSERT INTO stories VALUES (?1,?2,?3,1,?4)",
            (&seed.scope.story, &seed.scope.branch, title, seed_json),
        )?;
        transaction.execute(
            "INSERT INTO branches(story_id,branch_id) VALUES (?1,?2)",
            (&seed.scope.story, &seed.scope.branch),
        )?;
        for (kind, ids) in [
            ("actor", seed.actors.keys().collect::<Vec<_>>()),
            ("item", seed.items.keys().collect()),
            ("location", seed.locations.iter().collect()),
            ("ability", seed.abilities.keys().collect()),
            ("fact", seed.facts.keys().collect()),
            ("commitment", seed.commitments.keys().collect()),
        ] {
            for id in ids {
                transaction.execute(
                    "INSERT INTO entities VALUES (?1,?2,?3)",
                    (&seed.scope.story, kind, id),
                )?;
                transaction.execute(
                    "INSERT INTO branch_entities VALUES (?1,?2,?3,?4)",
                    (&seed.scope.story, &seed.scope.branch, kind, id),
                )?;
            }
        }
        transaction.execute(
            "INSERT INTO branch_projections VALUES (?1,?2,0,1,?3)",
            (
                &seed.scope.story,
                &seed.scope.branch,
                String::from_utf8(engine.canonical_bytes())
                    .map_err(|_| StorageError::InvalidSeed)?,
            ),
        )?;
        transaction.commit()?;
        Ok(())
    }
    /// Loads only the requested root seed. It never trusts a cached projection as canon.
    pub fn load_seed(&self, scope: &Scope) -> Result<Seed> {
        let json: String = self
            .connection
            .query_row(
                "SELECT seed_json FROM stories WHERE story_id=?1 AND root_branch=?2",
                (&scope.story, &scope.branch),
                |r| r.get(0),
            )
            .optional()?
            .ok_or(StorageError::NotFound)?;
        let seed: Seed = serde_json::from_str(&json).map_err(|_| StorageError::Integrity)?;
        if &seed.scope != scope || Engine::new(seed.clone()).is_err() {
            return Err(StorageError::Integrity);
        }
        Ok(seed)
    }
    /// Explicit consistent backup, including committed WAL frames. Never copies a live main file.
    pub fn backup_to(&self, destination: &Path) -> Result<()> {
        consistent_backup(&self.connection, destination)
    }
    /// Bounded explicit private inspection copy. Pin a coherent read snapshot before sizing:
    /// another writer cannot grow the snapshot between the budget check and SQLite backup.
    pub fn backup_inspection_to(&self, destination: &Path) -> Result<()> {
        self.backup_bounded(destination, MAX_INSPECTION_DATABASE_BYTES)
    }
    fn backup_bounded(&self, destination: &Path, limit: u64) -> Result<()> {
        let snapshot = self.connection.unchecked_transaction()?;
        let _: i64 =
            snapshot.query_row("SELECT count(*) FROM schema_migrations", [], |r| r.get(0))?;
        let pages: u32 = snapshot.pragma_query_value(None, "page_count", |r| r.get(0))?;
        let page_bytes: u32 = snapshot.pragma_query_value(None, "page_size", |r| r.get(0))?;
        if u64::from(pages)
            .checked_mul(u64::from(page_bytes))
            .ok_or(StorageError::InvalidInput)?
            > limit
        {
            return Err(StorageError::InvalidInput);
        }
        consistent_backup(&snapshot, destination)?;
        snapshot.commit()?;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[cfg(windows)]
    mod pinned_new {
        use super::*;
        fn fixture() -> PathBuf {
            let dir = std::env::temp_dir().join(format!(
                "pinned-store-hook-{}-{}",
                std::process::id(),
                std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .unwrap()
                    .as_nanos()
            ));
            std::fs::create_dir(&dir).unwrap();
            let outside = dir.join("outside.sqlite");
            let mut store = Store::open(&outside, None).unwrap();
            let seed: Seed =
                serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
            store
                .create_story("Synthetic outside fixture", seed)
                .unwrap();
            drop(store);
            dir
        }
        fn cleanup(dir: &Path) {
            for entry in std::fs::read_dir(dir).unwrap() {
                std::fs::remove_file(entry.unwrap().path()).unwrap();
            }
            std::fs::remove_dir(dir).unwrap();
        }
        #[test]
        fn existing_leaf_refusal_never_reaches_connect_hooks() {
            let dir = fixture();
            let path = dir.join("outside.sqlite");
            let before = std::fs::read(&path).unwrap();
            let result = Store::create_new_pinned_inner(
                &path,
                PinnedNewHooks {
                    after_reservation: |_| panic!("reservation was refused"),
                    after_connect: |_| panic!("must not connect"),
                },
            );
            assert_eq!(result.err(), Some(StorageError::Io));
            assert_eq!(std::fs::read(&path).unwrap(), before);
            for suffix in ["-journal", "-wal", "-shm"] {
                let main = dir.join(format!("refused{suffix}.sqlite"));
                let mut name = main.as_os_str().to_owned();
                name.push(suffix);
                let sidecar = PathBuf::from(name);
                std::fs::write(&sidecar, b"foreign sidecar").unwrap();
                let result = Store::create_new_pinned_inner(
                    &main,
                    PinnedNewHooks {
                        after_reservation: |_| panic!("all reservations must succeed first"),
                        after_connect: |_| panic!("must not connect to existing sidecar"),
                    },
                );
                assert_eq!(result.err(), Some(StorageError::Io));
                assert_eq!(std::fs::read(&sidecar).unwrap(), b"foreign sidecar");
            }
            cleanup(&dir);
        }
        #[test]
        fn reserved_handle_blocks_replacement_in_the_exact_pre_sqlite_window() {
            let dir = fixture();
            let path = dir.join("new.sqlite");
            let outside = dir.join("outside.sqlite");
            let before = std::fs::read(&outside).unwrap();
            let store = Store::create_new_pinned_inner(
                &path,
                PinnedNewHooks {
                    after_reservation: |path| {
                        assert_eq!(std::fs::metadata(path).unwrap().len(), 0);
                        assert!(
                            std::fs::rename(path, path.with_file_name("stolen.sqlite")).is_err()
                        );
                        assert!(std::fs::remove_file(path).is_err());
                        assert!(
                            std::fs::rename(path.with_file_name("outside.sqlite"), path).is_err()
                        );
                        for suffix in ["-journal", "-wal", "-shm"] {
                            let mut name = path.as_os_str().to_owned();
                            name.push(suffix);
                            let sidecar = PathBuf::from(name);
                            assert_eq!(std::fs::metadata(&sidecar).unwrap().len(), 0);
                            assert!(OpenOptions::new().write(true).open(&sidecar).is_err());
                            assert!(std::fs::remove_file(&sidecar).is_err());
                            assert!(std::fs::rename(&sidecar, sidecar.with_extension("stolen"))
                                .is_err());
                            assert!(std::fs::rename(
                                path.with_file_name("outside.sqlite"),
                                &sidecar
                            )
                            .is_err());
                        }
                        Ok(())
                    },
                    after_connect: |connection| {
                        let mode: String =
                            connection.pragma_query_value(None, "journal_mode", |r| r.get(0))?;
                        assert_eq!(mode, "memory");
                        Ok(())
                    },
                },
            )
            .unwrap();
            assert_eq!(store.info().unwrap().schema_version, SCHEMA_VERSION);
            assert_eq!(std::fs::read(&outside).unwrap(), before);
            drop(store);
            let normal = Store::open(&path, None).unwrap();
            let mode: String = normal
                .connection
                .pragma_query_value(None, "journal_mode", |r| r.get(0))
                .unwrap();
            assert_eq!(
                mode, "delete",
                "disposable staging journal mode is not inherited by normal reopen"
            );
            drop(normal);
            cleanup(&dir);
        }
        #[test]
        fn failed_initializer_leaves_only_its_owned_partial_leaf_and_releases_handles() {
            let dir = fixture();
            let path = dir.join("failed.sqlite");
            let outside = dir.join("outside.sqlite");
            let before = std::fs::read(&outside).unwrap();
            let result = Store::create_new_pinned_inner(
                &path,
                PinnedNewHooks {
                    after_reservation: |_| Ok(()),
                    after_connect: |connection| {
                        connection.execute_batch("CREATE TABLE synthetic_initializer_failure(value TEXT); INSERT INTO synthetic_initializer_failure VALUES('owned partial leaf');")?;
                        Err(StorageError::Database)
                    },
                },
            );
            assert_eq!(result.err(), Some(StorageError::Database));
            assert!(path.is_file());
            let partial = std::fs::read(&path).unwrap();
            assert!(partial.starts_with(b"SQLite format 3\0"));
            assert_eq!(std::fs::read(&outside).unwrap(), before);
            assert_eq!(
                Store::create_new_pinned(&path).err(),
                Some(StorageError::Io)
            );
            assert_eq!(std::fs::read(&path).unwrap(), partial);
            let moved = dir.join("released.sqlite");
            std::fs::rename(&path, &moved).unwrap();
            std::fs::rename(&moved, &path).unwrap();
            cleanup(&dir);
        }
    }

    #[test]
    fn file_owner_and_read_only_connections_require_memory_only_temp_fts() {
        let path = std::env::temp_dir().join(format!(
            "locallore-temp-policy-{}-{}.sqlite",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        {
            let store = Store::open(&path, None).unwrap();
            assert_eq!(
                store
                    .connection
                    .pragma_query_value(None, "temp_store", |r| r.get::<_, u32>(0))
                    .unwrap(),
                2
            );
            store
                .connection
                .execute_batch("CREATE VIRTUAL TABLE temp.policy_probe USING fts5(body)")
                .unwrap();
            // Exercise the actual bundled FTS with a corpus larger than its
            // usual small page cache, not merely a source-level PRAGMA check.
            store
                .connection
                .execute(
                    "INSERT INTO temp.policy_probe(body) VALUES(?1)",
                    ["synthetic ".repeat(240_000)],
                )
                .unwrap();
            let count: u32 = store
                .connection
                .query_row(
                    "SELECT count(*) FROM temp.policy_probe WHERE policy_probe MATCH 'synthetic'",
                    [],
                    |r| r.get(0),
                )
                .unwrap();
            assert_eq!(count, 1);
            let temporary_file: String = store
                .connection
                .query_row(
                    "SELECT file FROM pragma_database_list WHERE name='temp'",
                    [],
                    |r| r.get(0),
                )
                .unwrap();
            assert!(temporary_file.is_empty());
            store
                .connection
                .execute_batch("DROP TABLE temp.policy_probe")
                .unwrap();
            assert!(!store
                .connection
                .prepare("SELECT 1 FROM sqlite_temp_schema WHERE name GLOB 'policy_probe*'")
                .unwrap()
                .exists([])
                .unwrap());
        }
        {
            let store = Store::open_read_only(&path).unwrap();
            assert_eq!(
                store
                    .connection
                    .pragma_query_value(None, "temp_store", |r| r.get::<_, u32>(0))
                    .unwrap(),
                2
            );
        }
        std::fs::remove_file(path).unwrap();
    }

    #[test]
    fn failed_v1_upgrade_rolls_back_derived_ddl_migration_records_and_version() {
        let mut connection = Connection::open_in_memory().unwrap();
        configure(&connection).unwrap();
        connection.execute_batch(SCHEMA).unwrap();
        connection
            .pragma_update(None, "application_id", APPLICATION_ID)
            .unwrap();
        connection.pragma_update(None, "user_version", 1).unwrap();
        let original = schema_rows(&connection).unwrap();
        for (sql, expected) in [
            (
                format!(
                    "{} INSERT INTO absent_migration_table VALUES(1);",
                    derived_memory::DERIVED_SCHEMA_SQL
                ),
                StorageError::Database,
            ),
            (
                format!(
                    "{} CREATE TABLE unexpected(data TEXT);",
                    derived_memory::DERIVED_SCHEMA_SQL
                ),
                StorageError::SchemaMismatch,
            ),
        ] {
            let tx = connection
                .transaction_with_behavior(TransactionBehavior::Immediate)
                .unwrap();
            let attempted = (|| -> Result<()> {
                tx.execute_batch(&sql)?;
                migrate_known(&tx, 2)
            })();
            assert_eq!(attempted, Err(expected));
            drop(tx);
            assert_eq!(identity(&connection).unwrap(), (APPLICATION_ID, 1));
            assert_eq!(schema_rows(&connection).unwrap(), original);
            verify_version(&connection, 1).unwrap();
        }
        assert_eq!(identity(&connection).unwrap(), (APPLICATION_ID, 1));
        assert_eq!(schema_rows(&connection).unwrap(), original);
        verify_version(&connection, 1).unwrap();
        let tx = connection
            .transaction_with_behavior(TransactionBehavior::Immediate)
            .unwrap();
        migrate_known(&tx, 1).unwrap();
        tx.commit().unwrap();
        verify(&connection).unwrap();
    }

    #[test]
    fn inspection_copy_checks_snapshot_budget_before_creating_any_destination() {
        let path = std::env::temp_dir().join(format!(
            "locallore-budget-{}-{}.sqlite",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        let mut connection = Connection::open_in_memory().unwrap();
        configure(&connection).unwrap();
        let tx = connection.transaction().unwrap();
        initialize(&tx, SCHEMA).unwrap();
        tx.commit().unwrap();
        let store = Store::from_connection(connection);
        assert_eq!(
            store.backup_bounded(&path, 1),
            Err(StorageError::InvalidInput)
        );
        assert!(!path.exists());
        assert!(store
            .backup_bounded(&path, MAX_INSPECTION_DATABASE_BYTES)
            .is_ok());
        std::fs::remove_file(path).unwrap();
    }

    #[test]
    fn failed_migration_rolls_back_ddl_data_and_versions() {
        let mut connection = Connection::open_in_memory().unwrap();
        configure(&connection).unwrap();
        {
            let transaction = connection
                .transaction_with_behavior(TransactionBehavior::Immediate)
                .unwrap();
            // Fail after all initial DDL/data, before the version transaction commits.
            let invalid = format!("{SCHEMA}\nINSERT INTO nonexistent_table VALUES (1);");
            assert_eq!(
                initialize(&transaction, &invalid),
                Err(StorageError::Database)
            );
        }
        assert!(schema_rows(&connection).unwrap().is_empty());
        assert_eq!(identity(&connection).unwrap(), (0, 0));
        let transaction = connection
            .transaction_with_behavior(TransactionBehavior::Immediate)
            .unwrap();
        initialize(&transaction, SCHEMA).unwrap();
        transaction.commit().unwrap();
        verify(&connection).unwrap();
    }

    #[test]
    fn every_configured_connection_enforces_foreign_keys_and_disables_extensions() {
        let connection = Connection::open_in_memory().unwrap();
        configure(&connection).unwrap();
        let enabled: bool = connection
            .pragma_query_value(None, "foreign_keys", |r| r.get(0))
            .unwrap();
        assert!(enabled);
        let extension_error = connection
            .query_row::<i64, _, _>("SELECT load_extension('never-loaded')", [], |r| r.get(0))
            .unwrap_err();
        assert!(
            matches!(extension_error, rusqlite::Error::SqliteFailure(_, Some(ref message))
            if message == "not authorized")
        );
        let trusted: bool = connection
            .pragma_query_value(None, "trusted_schema", |r| r.get(0))
            .unwrap();
        assert!(!trusted);
    }
}
