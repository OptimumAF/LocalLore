// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Retire a playable timeline while retaining only original ancestry needed by
//! surviving timelines. No receipt, scope, witness, seed or fork is rewritten.
use crate::{
    story_deletion::{check, data_version, database, FileStamp},
    DeletionError, Store, TurnError, MAX_BRANCHES_PER_STORY, MAX_BRANCH_DEPTH,
};
use locallore::contracts::Scope;
use rusqlite::{Connection, OptionalExtension, TransactionBehavior};
use serde::Serialize;
use sha2::{Digest, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    path::PathBuf,
};

const TABLES: [&str; 9] = [
    "memory_job_packets",
    "memory_jobs",
    "derived_memory",
    "event_witnesses",
    "accepted_events",
    "turns",
    "branch_projections",
    "branch_entities",
    "branches",
];
const MAX_PREVIEW_BYTES: usize = 60 * 1024;
const WARNING: &str = "Removes this playable timeline and unreachable history. Original ancestry needed by remaining timelines is retained. Deleted timeline IDs stay reserved. Exported files, OS backups and forensic traces are not removed.";
type Result<T> = std::result::Result<T, DeletionError>;

#[derive(Clone, Debug, Serialize, PartialEq, Eq)]
pub struct BranchDeletionPreview {
    pub version: u16,
    pub scope: Scope,
    pub title: String,
    pub root_branch: String,
    pub expected_revision: u64,
    pub retained_descendants: BTreeMap<String, u64>,
    pub retained_heads: BTreeMap<String, u64>,
    pub removed_branches: Vec<String>,
    pub removed_rows: BTreeMap<String, u64>,
    pub removed_committed_turns: u64,
    pub removed_noncommitted_turns: u64,
    pub privacy_warning: String,
}

/// A one-use native plan; no long-lived read transaction, Clone or Deserialize.
pub struct PreparedBranchDeletion {
    preview: BranchDeletionPreview,
    database: PathBuf,
    stamp: FileStamp,
    observer: Connection,
    data_version: i64,
}
impl PreparedBranchDeletion {
    pub fn preview(&self) -> &BranchDeletionPreview {
        &self.preview
    }
}

#[derive(Clone, Debug, Serialize, PartialEq, Eq)]
pub struct BranchDeletionOutcome {
    pub scope: Scope,
    pub retained_through_revision: Option<u64>,
    pub collected_branches: u64,
    pub deleted_turns: u64,
    /// Sorted retired target plus physically collected retired ancestors.
    pub invalidated_branches: Vec<String>,
}

#[derive(Clone)]
struct Node {
    parent: Option<String>,
    fork: Option<u64>,
    head: u64,
}
struct Graph {
    title: String,
    root: String,
    nodes: BTreeMap<String, Node>,
    retired: BTreeSet<String>,
    fingerprints: BTreeMap<String, ([u8; 32], [u8; 32])>,
}
struct Change {
    id: String,
    cap: Option<u64>,
}
struct Plan {
    preview: BranchDeletionPreview,
    changes: Vec<Change>,
    graph: Graph,
}

fn valid_id(id: &str) -> bool {
    !id.is_empty()
        && id.len() <= 64
        && id
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b"-_".contains(&b))
}
fn integer(value: u64) -> Result<i64> {
    value.try_into().map_err(|_| DeletionError::TooLarge)
}
fn replay_error(error: TurnError) -> DeletionError {
    match error {
        TurnError::TooLarge => DeletionError::TooLarge,
        TurnError::Full => DeletionError::Full,
        TurnError::Storage(e) => match e {
            crate::StorageError::NotFound => DeletionError::Integrity,
            other => other.into(),
        },
        _ => DeletionError::Integrity,
    }
}
fn count(connection: &Connection, sql: &str, story: &str, branch: &str, cap: i64) -> Result<u64> {
    let n: i64 = connection.query_row(sql, rusqlite::params![story, branch, cap], |r| r.get(0))?;
    n.try_into().map_err(|_| DeletionError::Integrity)
}
fn required_cap(nodes: &BTreeMap<String, Node>, id: &str) -> Result<Option<u64>> {
    let node = nodes.get(id).ok_or(DeletionError::Integrity)?;
    let children: Vec<_> = nodes
        .values()
        .filter(|n| n.parent.as_deref() == Some(id))
        .collect();
    if children.is_empty() {
        return Ok(None);
    }
    let mut cap = node.fork.ok_or(DeletionError::Integrity)?;
    for child in children {
        cap = cap.max(child.fork.ok_or(DeletionError::Integrity)?);
    }
    Ok(Some(cap))
}
fn graph(connection: &Connection, story: &str, cancel: &dyn Fn() -> bool) -> Result<Graph> {
    check(cancel)?;
    let schema_version = crate::identity(connection)
        .map_err(|_| DeletionError::Integrity)?
        .1;
    let metadata: Option<(String, String)> = connection
        .query_row(
            "SELECT title,root_branch FROM stories WHERE story_id=?1",
            [story],
            |r| Ok((r.get(0)?, r.get(1)?)),
        )
        .optional()?;
    let (title, root) = metadata.ok_or(DeletionError::NotFound)?;
    if title.is_empty() || title.chars().count() > 256 || title.contains('\0') || !valid_id(&root) {
        return Err(DeletionError::Integrity);
    }
    let mut nodes = BTreeMap::new();
    {
        let mut q=connection.prepare("SELECT branch_id,parent_branch,fork_revision,head_revision FROM branches WHERE story_id=?1 ORDER BY branch_id LIMIT 257")?;
        let mut rows = q.query([story])?;
        while let Some(row) = rows.next()? {
            check(cancel)?;
            let id: String = row.get(0)?;
            let parent: Option<String> = row.get(1)?;
            let fork: Option<i64> = row.get(2)?;
            let head: i64 = row.get(3)?;
            if !valid_id(&id) || parent.as_ref().is_some_and(|p| !valid_id(p)) {
                return Err(DeletionError::Integrity);
            }
            nodes.insert(
                id,
                Node {
                    parent,
                    fork: fork
                        .map(u64::try_from)
                        .transpose()
                        .map_err(|_| DeletionError::Integrity)?,
                    head: head.try_into().map_err(|_| DeletionError::Integrity)?,
                },
            );
            if nodes.len() > MAX_BRANCHES_PER_STORY {
                return Err(DeletionError::TooLarge);
            }
        }
    }
    let root_node = nodes.get(&root).ok_or(DeletionError::Integrity)?;
    if root_node.parent.is_some() || root_node.fork.is_some() {
        return Err(DeletionError::Integrity);
    }
    let mut retired = BTreeSet::new();
    {
        let mut q = connection.prepare(
            "SELECT branch_id FROM branch_retention WHERE story_id=?1 ORDER BY branch_id LIMIT 257",
        )?;
        let mut rows = q.query([story])?;
        while let Some(row) = rows.next()? {
            check(cancel)?;
            let id: String = row.get(0)?;
            if !valid_id(&id) || id == root {
                return Err(DeletionError::Integrity);
            }
            retired.insert(id);
            if retired.len() > MAX_BRANCHES_PER_STORY {
                return Err(DeletionError::TooLarge);
            }
        }
    }
    if nodes
        .keys()
        .chain(retired.iter())
        .collect::<BTreeSet<_>>()
        .len()
        > MAX_BRANCHES_PER_STORY
    {
        return Err(DeletionError::TooLarge);
    }
    let mut fingerprints = BTreeMap::new();
    for (id, node) in &nodes {
        check(cancel)?;
        let engine = crate::turns::read_engine_retained(
            connection,
            &Scope {
                story: story.into(),
                branch: id.clone(),
            },
        )
        .map_err(replay_error)?
        .engine;
        if engine.revision() != node.head {
            return Err(DeletionError::Integrity);
        }
        if retired.contains(id) {
            if required_cap(&nodes, id)? != Some(node.head) {
                return Err(DeletionError::Integrity);
            }
            for table in [
                "memory_job_packets",
                "memory_jobs",
                "derived_memory",
                "branch_projections",
            ] {
                // Historical schema3 inspection is read-only and has no v2
                // job tables. Check their emptiness only when they exist.
                if schema_version < 4 && matches!(table, "memory_job_packets" | "memory_jobs") {
                    continue;
                }
                if count(
                    connection,
                    &format!(
                        "SELECT count(*) FROM {table} WHERE story_id=?1 AND branch_id=?2 AND ?3=0"
                    ),
                    story,
                    id,
                    0,
                )? != 0
                {
                    return Err(DeletionError::Integrity);
                }
            }
            if count(connection,"SELECT count(*) FROM turns WHERE story_id=?1 AND branch_id=?2 AND status<>'committed' AND ?3=0",story,id,0)?!=0 { return Err(DeletionError::Integrity); }
        }
        // Digests are a bounded equality check, never an alternative to replay.
        let canon: [u8; 32] = Sha256::digest(engine.canonical_bytes()).into();
        let receipts: [u8; 32] = Sha256::digest(
            serde_json::to_vec(engine.receipts()).map_err(|_| DeletionError::Integrity)?,
        )
        .into();
        fingerprints.insert(id.clone(), (canon, receipts));
    }
    Ok(Graph {
        title,
        root,
        nodes,
        retired,
        fingerprints,
    })
}

/// Validate reserved IDs and the retained-prefix normal form for metadata consumers.
pub(crate) fn validate_retention(
    connection: &Connection,
    story: &str,
    cancel: &dyn Fn() -> bool,
) -> Result<()> {
    graph(connection, story, cancel).map(|_| ())
}

// Private SQL identifiers and predicates, never caller/model supplied.
fn predicate(table: &str, cap: Option<u64>) -> &'static str {
    match (table, cap) {
        ("event_witnesses" | "accepted_events", Some(_)) => "sequence>?3",
        ("turns", Some(_)) => "(status<>'committed' OR expected_revision>=?3)",
        ("branch_entities" | "branches", Some(_)) => "0 AND ?3>=0",
        _ => "?3>=0",
    }
}
fn make_plan(
    connection: &Connection,
    scope: &Scope,
    expected: u64,
    cancel: &dyn Fn() -> bool,
) -> Result<Plan> {
    let graph = graph(connection, &scope.story, cancel)?;
    if scope.branch == graph.root {
        return Err(DeletionError::Malformed);
    }
    if graph.retired.contains(&scope.branch) {
        return Err(DeletionError::NotFound);
    }
    let selected = graph
        .nodes
        .get(&scope.branch)
        .ok_or(DeletionError::NotFound)?;
    if selected.head != expected {
        return Err(DeletionError::Stale);
    }
    let mut retained_descendants = BTreeMap::new();
    for (id, node) in &graph.nodes {
        if id == &scope.branch || graph.retired.contains(id) {
            continue;
        }
        let mut parent = node.parent.as_deref();
        for _ in 0..MAX_BRANCH_DEPTH {
            let Some(p) = parent else {
                break;
            };
            if p == scope.branch {
                retained_descendants.insert(id.clone(), node.head);
                break;
            }
            parent = graph
                .nodes
                .get(p)
                .ok_or(DeletionError::Integrity)?
                .parent
                .as_deref();
        }
    }
    let mut projected = graph.nodes.clone();
    let mut id = scope.branch.clone();
    let mut changes = Vec::new();
    loop {
        check(cancel)?;
        let node = projected.get(&id).ok_or(DeletionError::Integrity)?.clone();
        let cap = required_cap(&projected, &id)?;
        if let Some(cap) = cap {
            if cap > node.head {
                return Err(DeletionError::Integrity);
            }
            crate::turns::read_engine_retained(
                connection,
                &Scope {
                    story: scope.story.clone(),
                    branch: id.clone(),
                },
            )
            .map_err(replay_error)?
            .engine
            .at_revision(cap)
            .map_err(|_| DeletionError::Integrity)?;
            changes.push(Change { id, cap: Some(cap) });
            break;
        }
        projected.remove(&id);
        changes.push(Change {
            id: id.clone(),
            cap: None,
        });
        let Some(parent) = node.parent else {
            return Err(DeletionError::Integrity);
        };
        if !graph.retired.contains(&parent) {
            break;
        }
        id = parent;
    }
    let mut removed_rows: BTreeMap<String, u64> =
        TABLES.into_iter().map(|t| (t.into(), 0)).collect();
    let mut committed = 0u64;
    let mut noncommitted = 0u64;
    let mut retained_heads = BTreeMap::new();
    let mut removed_branches = Vec::new();
    for change in &changes {
        check(cancel)?;
        let cap = integer(change.cap.unwrap_or(0))?;
        for table in TABLES {
            let n = count(
                connection,
                &format!(
                    "SELECT count(*) FROM {table} WHERE story_id=?1 AND branch_id=?2 AND {}",
                    predicate(table, change.cap)
                ),
                &scope.story,
                &change.id,
                cap,
            )?;
            let total = removed_rows
                .get_mut(table)
                .ok_or(DeletionError::Integrity)?;
            *total = total.checked_add(n).ok_or(DeletionError::TooLarge)?;
        }
        let cutoff = if change.cap.is_some() {
            "expected_revision>=?3"
        } else {
            "?3>=0"
        };
        committed = committed.checked_add(count(connection,&format!("SELECT count(*) FROM turns WHERE story_id=?1 AND branch_id=?2 AND status='committed' AND {cutoff}"),&scope.story,&change.id,cap)?).ok_or(DeletionError::TooLarge)?;
        noncommitted = noncommitted.checked_add(count(connection,"SELECT count(*) FROM turns WHERE story_id=?1 AND branch_id=?2 AND status<>'committed' AND ?3>=0",&scope.story,&change.id,cap)?).ok_or(DeletionError::TooLarge)?;
        if let Some(cap) = change.cap {
            retained_heads.insert(change.id.clone(), cap);
        } else {
            removed_branches.push(change.id.clone());
        }
    }
    removed_branches.sort();
    let preview = BranchDeletionPreview {
        version: 2,
        scope: scope.clone(),
        title: graph.title.clone(),
        root_branch: graph.root.clone(),
        expected_revision: expected,
        retained_descendants,
        retained_heads,
        removed_branches,
        removed_rows,
        removed_committed_turns: committed,
        removed_noncommitted_turns: noncommitted,
        privacy_warning: WARNING.into(),
    };
    if serde_json::to_vec(&preview)
        .map_err(|_| DeletionError::Integrity)?
        .len()
        > MAX_PREVIEW_BYTES
    {
        return Err(DeletionError::TooLarge);
    }
    Ok(Plan {
        preview,
        changes,
        graph,
    })
}

impl Store {
    pub fn prepare_branch_deletion(
        &mut self,
        scope: &Scope,
        expected_revision: u64,
        cancel: &dyn Fn() -> bool,
    ) -> Result<PreparedBranchDeletion> {
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
        let before = data_version(&observer)?;
        let tx = observer.transaction()?;
        let plan = make_plan(&tx, scope, expected_revision, cancel)?;
        tx.commit()?;
        if data_version(&observer)? != before
            || database(&self.connection)? != (path.clone(), stamp.clone())
        {
            return Err(DeletionError::Stale);
        }
        check(cancel)?;
        Ok(PreparedBranchDeletion {
            preview: plan.preview,
            database: path,
            stamp,
            observer,
            data_version: before,
        })
    }

    /// Confirmation always consumes the plan, including cancellation or failure.
    /// Native owners must fence old sessions across the accepted transaction.
    pub fn delete_branch(
        &mut self,
        prepared: PreparedBranchDeletion,
        cancel: &dyn Fn() -> bool,
    ) -> Result<BranchDeletionOutcome> {
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
        let plan = make_plan(
            &tx,
            &prepared.preview.scope,
            prepared.preview.expected_revision,
            cancel,
        )?;
        if plan.preview != prepared.preview {
            return Err(DeletionError::Stale);
        }
        check(cancel)?;
        tx.execute(
            "INSERT INTO branch_retention(story_id,branch_id) VALUES(?1,?2)",
            (&plan.preview.scope.story, &plan.preview.scope.branch),
        )?;
        check(cancel)?;
        let mut removed: BTreeMap<String, u64> =
            TABLES.into_iter().map(|t| (t.into(), 0)).collect();
        for change in &plan.changes {
            check(cancel)?;
            let cap = integer(change.cap.unwrap_or(0))?;
            for table in TABLES {
                let n = tx.execute(
                    &format!(
                        "DELETE FROM {table} WHERE story_id=?1 AND branch_id=?2 AND {}",
                        predicate(table, change.cap)
                    ),
                    rusqlite::params![plan.preview.scope.story, change.id, cap],
                )?;
                let total = removed.get_mut(table).ok_or(DeletionError::Integrity)?;
                *total = total.checked_add(n as u64).ok_or(DeletionError::TooLarge)?;
                check(cancel)?;
            }
            if let Some(cap) = change.cap {
                if tx.execute(
                    "UPDATE branches SET head_revision=?3 WHERE story_id=?1 AND branch_id=?2",
                    rusqlite::params![plan.preview.scope.story, change.id, integer(cap)?],
                )? != 1
                {
                    return Err(DeletionError::Integrity);
                }
                check(cancel)?;
            }
        }
        if removed != plan.preview.removed_rows {
            return Err(DeletionError::Integrity);
        }
        let after = graph(&tx, &plan.preview.scope.story, cancel)?;
        for (id, before) in &plan.graph.fingerprints {
            if id != &plan.preview.scope.branch
                && !plan.graph.retired.contains(id)
                && after.fingerprints.get(id) != Some(before)
            {
                return Err(DeletionError::Integrity);
            }
        }
        if tx.prepare("PRAGMA foreign_key_check")?.exists([])? {
            return Err(DeletionError::Integrity);
        }
        check(cancel)?;
        let mut invalidated: BTreeSet<String> =
            plan.preview.removed_branches.iter().cloned().collect();
        invalidated.insert(plan.preview.scope.branch.clone());
        let outcome = BranchDeletionOutcome {
            scope: plan.preview.scope.clone(),
            retained_through_revision: plan
                .preview
                .retained_heads
                .get(&plan.preview.scope.branch)
                .copied(),
            collected_branches: plan.preview.removed_branches.len() as u64,
            deleted_turns: plan.preview.removed_rows["turns"],
            invalidated_branches: invalidated.into_iter().collect(),
        };
        tx.commit()?;
        Ok(outcome)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{ForkRequest, TurnPhase};
    use locallore::{
        contracts::{Command, Intent, Seed},
        engine::Engine,
    };

    #[test]
    fn actual_sqlite_abort_after_tail_deletes_rolls_back_every_main_database_byte() {
        let directory = std::env::temp_dir().join(format!(
            "locallore-retention-sql-abort-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        std::fs::create_dir(&directory).unwrap();
        std::fs::write(
            directory.join("owner-v1"),
            b"locallore-retention-private-sql-test-v1",
        )
        .unwrap();
        let path = directory.join("synthetic.sqlite");
        let mut store = Store::open(&path, None).unwrap();
        let seed: Seed =
            serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
        let root = seed.scope.clone();
        store.create_story("Synthetic SQLite abort", seed).unwrap();
        let parent = store
            .fork_branch(
                &ForkRequest {
                    parent: root,
                    child_branch: "sql-parent".into(),
                    expected_parent_revision: 0,
                    at_revision: 0,
                },
                &|| false,
            )
            .unwrap()
            .scope;
        for (id, command) in [
            ("kept", Command::Wait { ticks: 1 }),
            ("tail", Command::Wait { ticks: 1 }),
        ] {
            let engine = store.resume(&parent).unwrap().engine;
            let request = engine.request(id, Intent::Actions(vec![command]));
            let receipt = engine
                .preview(&request, &Engine::proposal(&request).unwrap())
                .unwrap();
            store.begin_turn(&request).unwrap();
            store.commit_prepared(&receipt).unwrap();
        }
        let child = store
            .fork_branch(
                &ForkRequest {
                    parent: parent.clone(),
                    child_branch: "sql-child".into(),
                    expected_parent_revision: 2,
                    at_revision: 1,
                },
                &|| false,
            )
            .unwrap()
            .scope;
        let engine = store.resume(&parent).unwrap().engine;
        let request = engine.request("pending", Intent::Actions(vec![Command::Wait { ticks: 1 }]));
        store.begin_turn(&request).unwrap();
        // TEMP belongs to this private unit-test connection, never the main
        // schema. The real SQL abort occurs after tombstone, event and turn
        // deletes. No production hook, environment knob or extra API exists.
        store.connection.execute_batch("CREATE TEMP TRIGGER abort_retirement BEFORE DELETE ON main.branch_projections WHEN old.branch_id='sql-parent' BEGIN SELECT RAISE(ABORT,'synthetic rollback'); END;").unwrap();
        let prepared = store
            .prepare_branch_deletion(&parent, 2, &|| false)
            .unwrap();
        let before = std::fs::read(&path).unwrap();
        assert_eq!(
            store.delete_branch(prepared, &|| false).err(),
            Some(DeletionError::Integrity)
        );
        assert!(
            before == std::fs::read(&path).unwrap(),
            "synthetic database bytes changed after SQL rollback"
        );
        assert_eq!(store.resume(&parent).unwrap().engine.revision(), 2);
        assert_eq!(store.resume(&child).unwrap().engine.revision(), 1);
        assert_eq!(
            store.lookup_turn(&parent, "pending").unwrap().phase,
            TurnPhase::Draft
        );
        store
            .connection
            .execute_batch("DROP TRIGGER temp.abort_retirement")
            .unwrap();
        let fresh = store
            .prepare_branch_deletion(&parent, 2, &|| false)
            .unwrap();
        assert_eq!(
            store
                .delete_branch(fresh, &|| false)
                .unwrap()
                .retained_through_revision,
            Some(1)
        );
    }
}
