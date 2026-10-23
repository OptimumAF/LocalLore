// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent actual-Store owner-capability regressions. No canonical SQL edits.
use locallore::{contracts::*, engine::Engine};
use locallore_storage::{
    derived_memory::MemoryError,
    memory_jobs::{MemoryJobInfo, MemoryJobRequest},
    ForkRequest, Store,
};
use std::{
    path::PathBuf,
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT: AtomicU64 = AtomicU64::new(0);
struct Temp(PathBuf);
impl Temp {
    fn new() -> Self {
        let path = std::env::temp_dir().join(format!(
            "locallore-memory-owner-review-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&path).unwrap();
        Self(path)
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
fn populated(path: &std::path::Path) -> (Store, MemoryJobRequest, MemoryJobInfo) {
    let mut store = Store::create_new_pinned(path).unwrap();
    let seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    let scope = seed.scope.clone();
    store.create_story("Synthetic owner binding", seed).unwrap();
    let engine = store.resume(&scope).unwrap().engine;
    let request = engine.request(
        "same-accepted-source",
        Intent::Actions(vec![Command::Wait { ticks: 1 }]),
    );
    let proposal = Engine::proposal(&request).unwrap();
    let receipt = engine.preview(&request, &proposal).unwrap();
    store.begin_turn(&request).unwrap();
    store
        .commit_turn(&request, &proposal, receipt.narration())
        .unwrap();
    let request = MemoryJobRequest {
        scope,
        observer: "mira".into(),
        expected_head: 1,
    };
    let job = store.ensure_memory_job(&request, &|| false).unwrap();
    (store, request, job)
}
fn pair(temp: &Temp) -> (Store, Store, MemoryJobRequest, MemoryJobInfo, MemoryJobInfo) {
    let (mut a, request, left) = populated(&temp.path("a.sqlite"));
    let (mut b, _, right) = populated(&temp.path("b.sqlite"));
    assert_eq!(
        left.handle.id(),
        right.handle.id(),
        "independent databases reuse local row IDs"
    );
    assert_eq!(
        a.resume(&request.scope).unwrap().engine.canonical_bytes(),
        b.resume(&request.scope).unwrap().engine.canonical_bytes(),
        "identical valid source must not substitute for Store-instance authority"
    );
    (a, b, request, left, right)
}

#[test]
fn foreign_store_handle_cannot_read_identical_partition() {
    let temp = Temp::new();
    let (_a, mut b, _, left, right) = pair(&temp);
    let result = b.memory_job_status(&left.handle, &|| false);
    assert_eq!(
        b.memory_job_status(&right.handle, &|| false).unwrap(),
        right
    );
    assert_eq!(result, Err(MemoryError::NotFound));
}

#[test]
fn foreign_store_handle_cannot_cancel_identical_partition() {
    let temp = Temp::new();
    let (_a, mut b, _, left, right) = pair(&temp);
    let result = b.cancel_memory_job(&left.handle, &|| false);
    let after = b.memory_job_status(&right.handle, &|| false).unwrap();
    assert_eq!(result, Err(MemoryError::NotFound));
    assert_eq!(after, right, "foreign owner must not cancel local progress");
}

#[test]
fn foreign_store_handle_cannot_prune_local_terminal_job() {
    let temp = Temp::new();
    let (_a, mut b, _, left, right) = pair(&temp);
    let cancelled = b.cancel_memory_job(&right.handle, &|| false).unwrap();
    let result = b.prune_memory_job(&left.handle, &|| false);
    assert_eq!(result, Err(MemoryError::NotFound));
    assert_eq!(
        b.memory_job_status(&right.handle, &|| false).unwrap(),
        cancelled
    );
}

#[test]
fn foreign_store_prepared_step_cannot_publish_against_identical_source() {
    let temp = Temp::new();
    let (mut a, mut b, _, left, right) = pair(&temp);
    let prepared = a.prepare_memory_job_step(&left.handle, &|| false).unwrap();
    let result = b.publish_memory_job_step(prepared, &|| false);
    let after = b.memory_job_status(&right.handle, &|| false).unwrap();
    assert_eq!(result, Err(MemoryError::NotFound));
    assert_eq!(
        after, right,
        "foreign preparation must not publish local progress"
    );
}

#[test]
fn reopen_reissues_handle_for_same_progress_and_expires_old_native_owner() {
    let temp = Temp::new();
    let path = temp.path("reopen.sqlite");
    let (mut store, request, admitted) = populated(&path);
    let prepared = store
        .prepare_memory_job_step(&admitted.handle, &|| false)
        .unwrap();
    let published = store.publish_memory_job_step(prepared, &|| false).unwrap();
    let canonical = store
        .resume(&request.scope)
        .unwrap()
        .engine
        .canonical_bytes();
    drop(store);
    let mut reopened = Store::open(&path, None).unwrap();
    let reissued = reopened.ensure_memory_job(&request, &|| false).unwrap();
    assert_eq!(reissued.handle.id(), published.handle.id());
    assert_eq!(reissued.next_from, published.next_from);
    assert_eq!(reissued.generation, published.generation);
    assert_eq!(reissued.status, published.status);
    assert_eq!(
        reopened.memory_job_status(&published.handle, &|| false),
        Err(MemoryError::NotFound),
        "an old native capability expires even when reopened row identity is unchanged"
    );
    assert_eq!(
        reopened
            .memory_job_status(&reissued.handle, &|| false)
            .unwrap(),
        reissued
    );
    assert_eq!(
        reopened
            .resume(&request.scope)
            .unwrap()
            .engine
            .canonical_bytes(),
        canonical
    );
}

#[test]
fn historical_schema3_retired_catalog_stays_readable_without_job_tables_or_writes() {
    let temp = Temp::new();
    let path = temp.path("historical-retired.sqlite");
    let (mut store, request, _) = populated(&path);
    let parent = store
        .fork_branch(
            &ForkRequest {
                parent: request.scope.clone(),
                child_branch: "retired-parent".into(),
                expected_parent_revision: 1,
                at_revision: 1,
            },
            &|| false,
        )
        .unwrap();
    let child = store
        .fork_branch(
            &ForkRequest {
                parent: parent.scope.clone(),
                child_branch: "retained-child".into(),
                expected_parent_revision: 1,
                at_revision: 1,
            },
            &|| false,
        )
        .unwrap();
    let deletion = store
        .prepare_branch_deletion(&parent.scope, 1, &|| false)
        .unwrap();
    store.delete_branch(deletion, &|| false).unwrap();
    let canonical = store.resume(&child.scope).unwrap().engine.canonical_bytes();
    drop(store);

    // Recreate only the exact historical migration ledger and remove new derived
    // tables. Accepted history, projections and actual retirement rows are intact.
    let reference = rusqlite::Connection::open_in_memory().unwrap();
    reference
        .execute_batch(include_str!("../migrations/001_initial.sql"))
        .unwrap();
    reference
        .execute_batch(include_str!("../migrations/002_derived_memory.sql"))
        .unwrap();
    reference
        .execute_batch(include_str!("../migrations/003_branch_retention.sql"))
        .unwrap();
    let ledger: String = reference
        .query_row(
            "SELECT sql FROM sqlite_schema WHERE type='table' AND name='schema_migrations'",
            [],
            |row| row.get(0),
        )
        .unwrap();
    let db = rusqlite::Connection::open(&path).unwrap();
    db.execute_batch(&format!(
        "BEGIN IMMEDIATE; DROP TABLE memory_job_packets; DROP TABLE memory_jobs; \
         DROP TABLE schema_migrations; {ledger}; \
         INSERT INTO schema_migrations VALUES \
         (1,'locallore-storage-v1'),(2,'locallore-storage-v2-derived-memory'),\
         (3,'locallore-storage-v3-branch-retention'); PRAGMA user_version=3; COMMIT;"
    ))
    .unwrap();
    drop(db);
    let before = std::fs::read(&path).unwrap();
    let mut historical = Store::open_read_only(&path).unwrap();
    assert_eq!(historical.info().unwrap().schema_version, 3);
    assert_eq!(
        historical
            .resume(&child.scope)
            .unwrap()
            .engine
            .canonical_bytes(),
        canonical
    );
    let catalog = historical.branch_catalog(&request.scope.story, &|| false);
    drop(historical);
    assert_eq!(
        std::fs::read(&path).unwrap(),
        before,
        "no read-only migration or repair"
    );
    let catalog = catalog.expect("valid schema3 catalog must not query schema4-only job tables");
    assert!(catalog
        .branches
        .iter()
        .any(|row| row.scope == parent.scope && row.retired));
    assert!(catalog
        .branches
        .iter()
        .any(|row| row.scope == child.scope && !row.retired));
}

#[test]
fn inconsistent_complete_cursor_is_rejected_instead_of_advertised_as_finished() {
    let temp = Temp::new();
    let path = temp.path("derived-status.sqlite");
    let (mut store, request, admitted) = populated(&path);
    assert_eq!(admitted.next_from, 0);
    assert_eq!(admitted.basis_revision, 1);
    let before = store
        .resume(&request.scope)
        .unwrap()
        .engine
        .canonical_bytes();
    // Only a derived status label changes; canonical tables and fingerprints are
    // untouched. A DDL constraint or a read-time invariant may reject it.
    let db = rusqlite::Connection::open(&path).unwrap();
    let tamper = db.execute(
        "UPDATE memory_jobs SET status='complete' WHERE job_id=?1",
        [i64::try_from(admitted.handle.id()).unwrap()],
    );
    drop(db);
    let advertised = store.memory_job_status(&admitted.handle, &|| false);
    assert_eq!(
        store
            .resume(&request.scope)
            .unwrap()
            .engine
            .canonical_bytes(),
        before
    );
    match tamper {
        Ok(1) => assert_eq!(
            advertised,
            Err(MemoryError::Integrity),
            "zero covered revisions must not be advertised as completed head1"
        ),
        Err(error)
            if error.sqlite_error_code() == Some(rusqlite::ErrorCode::ConstraintViolation) =>
        {
            assert_eq!(advertised, Ok(admitted));
        }
        other => panic!("unexpected derived-row mutation result: {other:?}"),
    }
}
