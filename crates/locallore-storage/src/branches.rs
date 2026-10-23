// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Store-owned forks. Original accepted history remains on its source branch.
use crate::{turns, StorageError, Store, TurnError};
use locallore::contracts::{Error, Scope};
use rusqlite::{params, Connection, OptionalExtension, TransactionBehavior};
use std::collections::BTreeSet;

pub const MAX_BRANCH_DEPTH: usize = 32;
pub const MAX_BRANCHES_PER_STORY: usize = 256;
type Result<T> = std::result::Result<T, TurnError>;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ForkRequest {
    pub parent: Scope,
    /// Fixed native operation identity, not a display title or a filesystem path.
    pub child_branch: String,
    /// Admission guard for NEW creation only. Existing matching child identity
    /// resolves even if this guard or either branch head has since changed.
    pub expected_parent_revision: u64,
    pub at_revision: u64,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ForkOutcome {
    pub scope: Scope,
    pub parent: Scope,
    pub fork_revision: u64,
    pub head_revision: u64,
    pub created: bool,
}
#[derive(Clone, Debug)]
pub(crate) struct Branch {
    pub scope: Scope,
    pub parent: Option<String>,
    pub fork: Option<u64>,
    pub head: u64,
}
fn valid_id(id: &str) -> bool {
    !id.is_empty()
        && id.len() <= 64
        && id
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b"-_".contains(&b))
}
fn check(cancel: &dyn Fn() -> bool) -> Result<()> {
    if std::panic::catch_unwind(std::panic::AssertUnwindSafe(cancel)).unwrap_or(true) {
        Err(TurnError::Engine(Error::Cancelled))
    } else {
        Ok(())
    }
}
/// One explicit root-to-leaf path, never a recursive SQL query or a sibling scan.
/// Validate even rows introduced outside this owner: FKs alone cannot detect cycles.
pub(crate) fn lineage(connection: &Connection, scope: &Scope) -> Result<Vec<Branch>> {
    if !valid_id(&scope.story) || !valid_id(&scope.branch) {
        return Err(TurnError::Engine(Error::Scope));
    }
    let root: String = connection
        .query_row(
            "SELECT root_branch FROM stories WHERE story_id=?1",
            [&scope.story],
            |r| r.get(0),
        )
        .optional()?
        .ok_or(StorageError::NotFound)?;
    let mut branch = scope.branch.clone();
    let mut seen = BTreeSet::new();
    let mut path = Vec::new();
    loop {
        if path.len() >= MAX_BRANCH_DEPTH || !seen.insert(branch.clone()) || !valid_id(&branch) {
            return Err(TurnError::Integrity);
        }
        let row: Option<(Option<String>,Option<i64>,i64)> = connection.query_row(
            "SELECT parent_branch,fork_revision,head_revision FROM branches WHERE story_id=?1 AND branch_id=?2",
            params![scope.story,branch], |r|Ok((r.get(0)?,r.get(1)?,r.get(2)?))
        ).optional()?;
        let (parent, fork, head) = row.ok_or({
            if path.is_empty() {
                TurnError::Storage(StorageError::NotFound)
            } else {
                TurnError::Integrity
            }
        })?;
        let head = u64::try_from(head).map_err(|_| TurnError::Integrity)?;
        let fork = fork
            .map(u64::try_from)
            .transpose()
            .map_err(|_| TurnError::Integrity)?;
        if parent.is_some() != fork.is_some()
            || fork.is_some_and(|f| f > head)
            || parent.as_ref().is_some_and(|p| !valid_id(p))
        {
            return Err(TurnError::Integrity);
        }
        path.push(Branch {
            scope: Scope {
                story: scope.story.clone(),
                branch: branch.clone(),
            },
            parent: parent.clone(),
            fork,
            head,
        });
        if let Some(parent) = parent {
            branch = parent;
        } else {
            if branch != root {
                return Err(TurnError::Integrity);
            }
            break;
        }
    }
    path.reverse();
    for pair in path.windows(2) {
        if pair[1].parent.as_deref() != Some(pair[0].scope.branch.as_str())
            || pair[1].fork.is_none_or(|fork| fork > pair[0].head)
        {
            return Err(TurnError::Integrity);
        }
    }
    Ok(path)
}

impl Store {
    /// Transactional immutable fork identity. An existing matching child returns
    /// its CURRENT head, not a replay of the first call's reply. A changed parent
    /// or fork point for the same child is RetryMismatch. No full-request byte
    /// equality is promised for the creation-only expected-parent-head guard.
    pub fn fork_branch(
        &mut self,
        request: &ForkRequest,
        cancel: &dyn Fn() -> bool,
    ) -> Result<ForkOutcome> {
        check(cancel)?;
        if !valid_id(&request.child_branch) || request.child_branch == request.parent.branch {
            return Err(TurnError::Engine(Error::Rule));
        }
        let tx = self
            .connection
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        let child = Scope {
            story: request.parent.story.clone(),
            branch: request.child_branch.clone(),
        };
        // Admission precedes both immutable-identity retry and new creation.
        crate::retention_state::admit(&tx, &request.parent)?;
        crate::retention_state::admit(&tx, &child)?;
        let existing:Option<(Option<String>,Option<i64>)>=tx.query_row(
            "SELECT parent_branch,fork_revision FROM branches WHERE story_id=?1 AND branch_id=?2",
            params![child.story,child.branch],|r|Ok((r.get(0)?,r.get(1)?))
        ).optional()?;
        if let Some((parent, fork)) = existing {
            if parent.as_deref() != Some(&request.parent.branch)
                || fork.and_then(|f| u64::try_from(f).ok()) != Some(request.at_revision)
            {
                return Err(TurnError::RetryMismatch);
            }
            let resumed = turns::read_engine(&tx, &child)?;
            check(cancel)?;
            let head_revision = resumed.engine.revision();
            tx.commit()?;
            return Ok(ForkOutcome {
                scope: child,
                parent: request.parent.clone(),
                fork_revision: request.at_revision,
                head_revision,
                created: false,
            });
        }
        let path = lineage(&tx, &request.parent)?;
        if path.len() >= MAX_BRANCH_DEPTH {
            return Err(TurnError::TooLarge);
        }
        let count: i64 = tx.query_row(
            "SELECT count(*) FROM (SELECT branch_id FROM branches WHERE story_id=?1 UNION SELECT branch_id FROM branch_retention WHERE story_id=?1)",
            [&request.parent.story],
            |r| r.get(0),
        )?;
        if count >= MAX_BRANCHES_PER_STORY as i64 {
            return Err(TurnError::TooLarge);
        }
        let parent = turns::read_engine(&tx, &request.parent)?.engine;
        check(cancel)?;
        if parent.revision() != request.expected_parent_revision {
            return Err(TurnError::Stale);
        }
        let fork = parent
            .fork(&request.child_branch, request.at_revision)
            .map_err(TurnError::Engine)?;
        let at = i64::try_from(request.at_revision).map_err(|_| TurnError::TooLarge)?;
        tx.execute("INSERT INTO branches(story_id,branch_id,parent_branch,fork_revision,head_revision) VALUES(?1,?2,?3,?4,?4)",params![child.story,child.branch,request.parent.branch,at])?;
        check(cancel)?;
        // Derive the fixed seed entity registry from validated authority, not a
        // parent cache/registry that an external connection could have altered.
        // It is not observed knowledge. Current rules cannot create actors.
        let seed = fork.seed();
        for (kind, ids) in [
            ("actor", seed.actors.keys().collect::<Vec<_>>()),
            ("item", seed.items.keys().collect()),
            ("location", seed.locations.iter().collect()),
            ("ability", seed.abilities.keys().collect()),
            ("fact", seed.facts.keys().collect()),
            ("commitment", seed.commitments.keys().collect()),
        ] {
            for id in ids {
                tx.execute("INSERT INTO branch_entities(story_id,branch_id,kind,entity_id) VALUES(?1,?2,?3,?4)",params![child.story,child.branch,kind,id])?;
            }
        }
        check(cancel)?;
        turns::write_projection(&tx, &fork)?;
        check(cancel)?;
        tx.commit()?;
        Ok(ForkOutcome {
            scope: child,
            parent: request.parent.clone(),
            fork_revision: request.at_revision,
            head_revision: request.at_revision,
            created: true,
        })
    }
}
