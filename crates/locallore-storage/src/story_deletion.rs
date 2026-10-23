// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Explicit whole-story deletion, separate from gameplay and model proposals.
//!
//! The app-private database and its ancestors must not be replaced while any
//! Store is open. Metadata checks detect drift; they are not an OS adversary
//! boundary. A native owner must additionally fence old in-flight gameplay work.
use crate::{StorageError, Store, TurnError, MAX_BRANCHES_PER_STORY};
use locallore::contracts::Scope;
use rusqlite::{Connection, OptionalExtension, TransactionBehavior};
use serde::Serialize;
use std::{
    collections::BTreeMap,
    fs,
    panic::{catch_unwind, AssertUnwindSafe},
    path::PathBuf,
    time::SystemTime,
};

const TABLES: [&str; 12] = [
    "memory_job_packets",
    "memory_jobs",
    "branch_retention",
    "derived_memory",
    "event_witnesses",
    "accepted_events",
    "turns",
    "branch_projections",
    "branch_entities",
    "entities",
    "branches",
    "stories",
];
const WARNING: &str = "Deletes this whole saved story, all timelines, accepted history, pending work and derived caches. Exported files, OS backups and forensic traces are not removed.";
const MAX_PREVIEW_BYTES: usize = 65_536;

#[derive(Clone, Debug, Serialize, PartialEq, Eq)]
pub struct StoryDeletionPreview {
    pub version: u16,
    pub story_id: String,
    pub title: String,
    pub root_branch: String,
    pub branch_heads: BTreeMap<String, u64>,
    pub committed_turns: u64,
    pub draft_turns: u64,
    /// All noncommitted workflow rows, including drafts.
    pub noncommitted_turns: u64,
    pub derived_packets: u64,
    pub rows: BTreeMap<String, u64>,
    pub privacy_warning: String,
}

/// A read-only observer, not a long-lived SQLite read transaction. Deliberately
/// neither Clone nor Deserialize: callers cannot manufacture confirmation plans.
pub struct PreparedStoryDeletion {
    preview: StoryDeletionPreview,
    database: PathBuf,
    stamp: FileStamp,
    observer: Connection,
    data_version: i64,
}
impl PreparedStoryDeletion {
    pub fn preview(&self) -> &StoryDeletionPreview {
        &self.preview
    }
}

#[derive(Clone, Debug, Serialize, PartialEq, Eq)]
pub struct StoryDeletionOutcome {
    pub story_id: String,
    pub deleted_branches: u64,
    /// Includes committed and noncommitted workflow rows.
    pub deleted_turns: u64,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum DeletionError {
    Malformed,
    NotFound,
    Stale,
    Cancelled,
    Busy,
    Full,
    Integrity,
    Database,
    Io,
    TooLarge,
}
impl std::fmt::Display for DeletionError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{self:?}")
    }
}
impl std::error::Error for DeletionError {}
impl From<rusqlite::Error> for DeletionError {
    fn from(e: rusqlite::Error) -> Self {
        match e.sqlite_error_code() {
            Some(rusqlite::ErrorCode::DatabaseBusy | rusqlite::ErrorCode::DatabaseLocked) => {
                Self::Busy
            }
            Some(rusqlite::ErrorCode::DiskFull) => Self::Full,
            Some(
                rusqlite::ErrorCode::DatabaseCorrupt
                | rusqlite::ErrorCode::NotADatabase
                | rusqlite::ErrorCode::ConstraintViolation,
            ) => Self::Integrity,
            _ => Self::Database,
        }
    }
}
impl From<StorageError> for DeletionError {
    fn from(e: StorageError) -> Self {
        match e {
            StorageError::Io => Self::Io,
            StorageError::Busy => Self::Busy,
            StorageError::NotFound => Self::NotFound,
            StorageError::Database => Self::Database,
            _ => Self::Integrity,
        }
    }
}
type Result<T> = std::result::Result<T, DeletionError>;

#[derive(Clone, PartialEq, Eq)]
pub(crate) struct FileStamp {
    len: u64,
    modified: Option<SystemTime>,
    created: Option<SystemTime>,
    readonly: bool,
    #[cfg(unix)]
    dev: u64,
    #[cfg(unix)]
    ino: u64,
    #[cfg(windows)]
    attributes: u32,
}
pub(crate) fn database(connection: &Connection) -> Result<(PathBuf, FileStamp)> {
    let path = connection
        .path()
        .filter(|p| !p.is_empty())
        .ok_or(DeletionError::Malformed)?;
    let original = PathBuf::from(path);
    // Refuse detectable leaf aliases, including Windows junction/reparse links.
    let meta = fs::symlink_metadata(&original).map_err(|_| DeletionError::Io)?;
    if !meta.is_file() || meta.file_type().is_symlink() {
        return Err(DeletionError::Stale);
    }
    #[cfg(windows)]
    {
        use std::os::windows::fs::MetadataExt;
        if meta.file_attributes() & 0x400 != 0 {
            return Err(DeletionError::Stale);
        }
    }
    let canonical = fs::canonicalize(original).map_err(|_| DeletionError::Io)?;
    #[cfg(unix)]
    use std::os::unix::fs::MetadataExt;
    #[cfg(windows)]
    use std::os::windows::fs::MetadataExt;
    Ok((
        canonical,
        FileStamp {
            len: meta.len(),
            modified: meta.modified().ok(),
            created: meta.created().ok(),
            readonly: meta.permissions().readonly(),
            #[cfg(unix)]
            dev: meta.dev(),
            #[cfg(unix)]
            ino: meta.ino(),
            #[cfg(windows)]
            attributes: meta.file_attributes(),
        },
    ))
}
pub(crate) fn check(cancel: &dyn Fn() -> bool) -> Result<()> {
    if catch_unwind(AssertUnwindSafe(cancel)).unwrap_or(true) {
        Err(DeletionError::Cancelled)
    } else {
        Ok(())
    }
}
fn valid_id(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 64
        && value
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b"-_".contains(&b))
}
pub(crate) fn data_version(connection: &Connection) -> Result<i64> {
    Ok(connection.pragma_query_value(None, "data_version", |r| r.get(0))?)
}
fn count(connection: &Connection, table: &str, story: &str) -> Result<u64> {
    // Every identifier comes from the fixed, private TABLES array.
    let n: i64 = connection.query_row(
        &format!("SELECT count(*) FROM {table} WHERE story_id=?1"),
        [story],
        |r| r.get(0),
    )?;
    n.try_into().map_err(|_| DeletionError::Integrity)
}
fn preview(
    connection: &Connection,
    scope: &Scope,
    expected: u64,
    cancel: &dyn Fn() -> bool,
) -> Result<StoryDeletionPreview> {
    let story: Option<(String, String)> = connection
        .query_row(
            "SELECT title,root_branch FROM stories WHERE story_id=?1",
            [&scope.story],
            |r| Ok((r.get(0)?, r.get(1)?)),
        )
        .optional()?;
    let (title, root_branch) = story.ok_or(DeletionError::NotFound)?;
    if scope.branch != root_branch {
        return Err(DeletionError::Malformed);
    }
    let mut branch_heads = BTreeMap::new();
    {
        let mut query = connection.prepare("SELECT branch_id,head_revision FROM branches WHERE story_id=?1 ORDER BY branch_id LIMIT 257")?;
        let mut rows = query.query([&scope.story])?;
        while let Some(row) = rows.next()? {
            check(cancel)?;
            let branch: String = row.get(0)?;
            let head: i64 = row.get(1)?;
            if !valid_id(&branch) {
                return Err(DeletionError::Integrity);
            }
            branch_heads.insert(
                branch,
                head.try_into().map_err(|_| DeletionError::Integrity)?,
            );
            if branch_heads.len() > MAX_BRANCHES_PER_STORY {
                return Err(DeletionError::TooLarge);
            }
        }
    }
    if branch_heads.get(&root_branch) != Some(&expected) {
        return Err(DeletionError::Stale);
    }
    // Replay all timelines. Derived projections alone do not authorize deletion.
    for branch in branch_heads.keys() {
        check(cancel)?;
        crate::turns::read_engine_retained(
            connection,
            &Scope {
                story: scope.story.clone(),
                branch: branch.clone(),
            },
        )
        .map_err(|e| match e {
            TurnError::TooLarge => DeletionError::TooLarge,
            TurnError::Storage(e) => e.into(),
            _ => DeletionError::Integrity,
        })?;
    }
    let mut counts = BTreeMap::new();
    for table in TABLES {
        check(cancel)?;
        counts.insert(table.into(), count(connection, table, &scope.story)?);
    }
    let (committed, draft, noncommitted): (i64,i64,i64) = connection.query_row(
        "SELECT coalesce(sum(status='committed'),0),coalesce(sum(status='draft'),0),coalesce(sum(status<>'committed'),0) FROM turns WHERE story_id=?1", [&scope.story], |r| Ok((r.get(0)?,r.get(1)?,r.get(2)?)))?;
    let result = StoryDeletionPreview {
        version: 3,
        story_id: scope.story.clone(),
        title,
        root_branch,
        branch_heads,
        committed_turns: committed.try_into().map_err(|_| DeletionError::Integrity)?,
        draft_turns: draft.try_into().map_err(|_| DeletionError::Integrity)?,
        noncommitted_turns: noncommitted
            .try_into()
            .map_err(|_| DeletionError::Integrity)?,
        derived_packets: counts["derived_memory"] + counts["memory_job_packets"],
        rows: counts,
        privacy_warning: WARNING.into(),
    };
    if serde_json::to_vec(&result)
        .map_err(|_| DeletionError::Integrity)?
        .len()
        > MAX_PREVIEW_BYTES
    {
        return Err(DeletionError::TooLarge);
    }
    Ok(result)
}

impl Store {
    pub fn prepare_story_deletion(
        &mut self,
        scope: &Scope,
        expected_revision: u64,
        cancel: &dyn Fn() -> bool,
    ) -> Result<PreparedStoryDeletion> {
        check(cancel)?;
        if !valid_id(&scope.story)
            || !valid_id(&scope.branch)
            || expected_revision > i64::MAX as u64
        {
            return Err(DeletionError::Malformed);
        }
        if !self.connection.is_autocommit() {
            return Err(DeletionError::Busy);
        }
        let (path, stamp) = database(&self.connection)?;
        let mut observer = Store::open_read_only(&path)?.connection;
        // Compare only values read on this particular retained connection.
        let before = data_version(&observer)?;
        let tx = observer.transaction()?;
        let result = preview(&tx, scope, expected_revision, cancel)?;
        tx.commit()?;
        if data_version(&observer)? != before
            || database(&self.connection)? != (path.clone(), stamp.clone())
        {
            return Err(DeletionError::Stale);
        }
        check(cancel)?;
        Ok(PreparedStoryDeletion {
            preview: result,
            database: path,
            stamp,
            observer,
            data_version: before,
        })
    }

    /// Consumes the plan even on failure. Confirmation is a new explicit action.
    pub fn delete_story(
        &mut self,
        prepared: PreparedStoryDeletion,
        cancel: &dyn Fn() -> bool,
    ) -> Result<StoryDeletionOutcome> {
        check(cancel)?;
        if !self.connection.is_autocommit() || !prepared.observer.is_autocommit() {
            return Err(DeletionError::Busy);
        }
        if database(&self.connection)? != (prepared.database.clone(), prepared.stamp) {
            return Err(DeletionError::Stale);
        }
        let tx = self
            .connection
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        if data_version(&prepared.observer)? != prepared.data_version {
            return Err(DeletionError::Stale);
        }
        let scope = Scope {
            story: prepared.preview.story_id.clone(),
            branch: prepared.preview.root_branch.clone(),
        };
        let expected = prepared.preview.branch_heads[&scope.branch];
        if preview(&tx, &scope, expected, cancel)? != prepared.preview {
            return Err(DeletionError::Stale);
        }
        check(cancel)?;
        for table in TABLES {
            let removed = tx.execute(
                &format!("DELETE FROM {table} WHERE story_id=?1"),
                [&scope.story],
            )?;
            if removed as u64 != prepared.preview.rows[table] {
                return Err(DeletionError::Integrity);
            }
            check(cancel)?;
        }
        {
            let mut query = tx.prepare("PRAGMA foreign_key_check")?;
            if query.query([])?.next()?.is_some() {
                return Err(DeletionError::Integrity);
            }
        }
        for table in TABLES {
            if count(&tx, table, &scope.story)? != 0 {
                return Err(DeletionError::Integrity);
            }
        }
        check(cancel)?;
        tx.commit()?;
        Ok(StoryDeletionOutcome {
            story_id: scope.story,
            deleted_branches: prepared.preview.rows["branches"],
            deleted_turns: prepared.preview.rows["turns"],
        })
    }
}
