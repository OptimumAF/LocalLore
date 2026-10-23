// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent actual-Store owner-capability regressions. No canonical SQL edits.
use locallore::{contracts::*, engine::Engine};
use locallore_storage::{
    derived_memory::MemoryError,
    memory_jobs::{MemoryJobInfo, MemoryJobRequest},
    Store,
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
