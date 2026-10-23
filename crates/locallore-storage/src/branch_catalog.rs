// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Coherent, bounded timeline metadata. Replay validates authority; this port
//! never repairs projections or exposes seed, accepted prose, or SQL.
use crate::{turns, StorageError, Store, TurnError, MAX_BRANCHES_PER_STORY};
use locallore::contracts::{Error, Scope};
use rusqlite::OptionalExtension;
use serde::Serialize;

// Reserve 4KiB of the native 64KiB reply bound for its fixed envelope.
const MAX_CATALOG_BYTES: usize = 60 * 1024;

#[derive(Clone, Debug, Serialize, PartialEq, Eq)]
pub struct BranchCatalog {
    pub version: u16,
    pub story_id: String,
    pub title: String,
    pub root_branch: String,
    pub branches: Vec<BranchSummary>,
}

#[derive(Clone, Debug, Serialize, PartialEq, Eq)]
pub struct BranchSummary {
    pub scope: Scope,
    pub parent_branch: Option<String>,
    pub fork_revision: Option<u64>,
    pub revision: u64,
    pub drafts: usize,
    /// Original ancestry remains visible as metadata but is never selectable.
    pub retired: bool,
}

type Result<T> = std::result::Result<T, TurnError>;
fn check(cancel: &dyn Fn() -> bool) -> Result<()> {
    if std::panic::catch_unwind(std::panic::AssertUnwindSafe(cancel)).unwrap_or(true) {
        Err(TurnError::Engine(Error::Cancelled))
    } else {
        Ok(())
    }
}
fn valid_id(id: &str) -> bool {
    !id.is_empty()
        && id.len() <= 64
        && id
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b"-_".contains(&b))
}

impl Store {
    /// All timelines and scoped draft counts come from one SQLite snapshot.
    /// Each branch passes the existing bounded lineage/history/ledger replay.
    pub fn branch_catalog(
        &mut self,
        story: &str,
        cancel: &dyn Fn() -> bool,
    ) -> Result<BranchCatalog> {
        check(cancel)?;
        if !valid_id(story) {
            return Err(TurnError::Engine(Error::Scope));
        }
        let tx = self.connection.transaction()?;
        let metadata: Option<(String, String)> = tx
            .query_row(
                "SELECT title,root_branch FROM stories WHERE story_id=?1",
                [story],
                |r| Ok((r.get(0)?, r.get(1)?)),
            )
            .optional()?;
        let (title, root_branch) = metadata.ok_or(StorageError::NotFound)?;
        if title.is_empty()
            || title.chars().count() > 256
            || title.contains('\0')
            || !valid_id(&root_branch)
        {
            return Err(TurnError::Integrity);
        }
        check(cancel)?;
        let mut branches = Vec::new();
        {
            let mut query = tx.prepare("SELECT b.branch_id,b.parent_branch,b.fork_revision,b.head_revision,(SELECT count(*) FROM turns t WHERE t.story_id=b.story_id AND t.branch_id=b.branch_id AND t.status='draft') FROM branches b WHERE b.story_id=?1 ORDER BY b.branch_id LIMIT 257")?;
            let mut rows = query.query([story])?;
            while let Some(row) = rows.next()? {
                check(cancel)?;
                if branches.len() >= MAX_BRANCHES_PER_STORY {
                    return Err(TurnError::TooLarge);
                }
                let id: String = row.get(0)?;
                let parent_branch: Option<String> = row.get(1)?;
                let fork: Option<i64> = row.get(2)?;
                let head: i64 = row.get(3)?;
                let drafts: i64 = row.get(4)?;
                if !valid_id(&id) || parent_branch.as_ref().is_some_and(|p| !valid_id(p)) {
                    return Err(TurnError::Integrity);
                }
                branches.push(BranchSummary {
                    scope: Scope {
                        story: story.into(),
                        branch: id,
                    },
                    parent_branch,
                    fork_revision: fork
                        .map(u64::try_from)
                        .transpose()
                        .map_err(|_| TurnError::Integrity)?,
                    revision: head.try_into().map_err(|_| TurnError::Integrity)?,
                    drafts: drafts.try_into().map_err(|_| TurnError::Integrity)?,
                    retired: crate::retention_state::retired(
                        &tx,
                        &Scope {
                            story: story.into(),
                            branch: row.get(0)?,
                        },
                    )?,
                });
            }
        }
        let root = branches
            .iter()
            .find(|b| b.scope.branch == root_branch)
            .ok_or(TurnError::Integrity)?;
        if root.parent_branch.is_some() || root.fork_revision.is_some() || root.retired {
            return Err(TurnError::Integrity);
        }
        for branch in &branches {
            check(cancel)?;
            let replayed =
                turns::read_engine_retained(&tx, &branch.scope).map_err(|error| match error {
                    TurnError::Engine(_) | TurnError::Storage(StorageError::NotFound) => {
                        TurnError::Integrity
                    }
                    other => other,
                })?;
            if replayed.engine.revision() != branch.revision {
                return Err(TurnError::Integrity);
            }
            check(cancel)?;
        }
        let result = BranchCatalog {
            version: 2,
            story_id: story.into(),
            title,
            root_branch,
            branches,
        };
        if serde_json::to_vec(&result)
            .map_err(|_| TurnError::Integrity)?
            .len()
            > MAX_CATALOG_BYTES
        {
            return Err(TurnError::TooLarge);
        }
        check(cancel)?;
        tx.commit()?;
        Ok(result)
    }
}
