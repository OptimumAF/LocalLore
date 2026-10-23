// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Actual selected-player Store lookup/admission. No canonical SQL fixture edits.
use locallore::{contracts::*, engine::Engine};
use locallore_storage::{
    derived_memory::MemoryError,
    memory_jobs::{MemoryJobRequest, MemoryJobStatus},
    playable_archive::validate_archive,
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
            "locallore-maintenance-lookup-{}-{}-{}",
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
    fn path(&self) -> PathBuf {
        self.0.join("synthetic.sqlite")
    }
    fn store(&self) -> Store {
        Store::open_application(&self.path()).unwrap()
    }
}
impl Drop for Temp {
    fn drop(&mut self) {
        std::fs::remove_dir_all(&self.0).unwrap();
    }
}
fn fixture() -> (Temp, Store, Engine) {
    let temp = Temp::new();
    let mut store = temp.store();
    let seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    let scope = seed.scope.clone();
    store
        .create_story("Synthetic selected maintenance", seed)
        .unwrap();
    let engine = store.resume(&scope).unwrap().engine;
    (temp, store, engine)
}
fn request(engine: &Engine) -> MemoryJobRequest {
    MemoryJobRequest {
        scope: engine.scope().clone(),
        observer: engine.seed().player.clone(),
        expected_head: engine.revision(),
    }
}
fn commit(store: &mut Store, engine: &mut Engine, key: &str) {
    let req = engine.request(key, Intent::Actions(vec![Command::Wait { ticks: 1 }]));
    let proposal = Engine::proposal(&req).unwrap();
    let preview = engine.preview(&req, &proposal).unwrap();
    store.begin_turn(&req).unwrap();
    let receipt = store
        .commit_turn(&req, &proposal, preview.narration())
        .unwrap();
    assert_eq!(engine.commit_prepared(&receipt).unwrap(), receipt);
}
#[test]
fn missing_status_does_not_admit_or_change_bytes() {
    let (temp, mut store, engine) = fixture();
    let before = std::fs::read(temp.path()).unwrap();
    for _ in 0..3 {
        assert_eq!(
            store
                .lookup_memory_job(&request(&engine), &engine, &|| false)
                .unwrap(),
            None
        );
    }
    assert_eq!(std::fs::read(temp.path()).unwrap(), before);
    assert_eq!(
        store
            .resume(engine.scope())
            .unwrap()
            .engine
            .canonical_bytes(),
        engine.canonical_bytes()
    );
}
#[test]
fn reopen_lookup_reissues_only_current_store_handle_without_writing() {
    let (temp, mut store, mut engine) = fixture();
    commit(&mut store, &mut engine, "lookup-reopen");
    let info = store
        .ensure_selected_memory_job(&request(&engine), &engine, &|| false)
        .unwrap();
    drop(store);
    let mut reopened = temp.store();
    let before = std::fs::read(temp.path()).unwrap();
    let found = reopened
        .lookup_memory_job(&request(&engine), &engine, &|| false)
        .unwrap()
        .unwrap();
    assert_eq!(info.handle.id(), found.handle.id());
    assert_ne!(info.handle, found.handle);
    assert_eq!(
        (info.status, info.next_from, info.generation),
        (found.status, found.next_from, found.generation)
    );
    assert_eq!(
        reopened.memory_job_status(&info.handle, &|| false),
        Err(MemoryError::NotFound)
    );
    assert_eq!(
        reopened
            .memory_job_status(&found.handle, &|| false)
            .unwrap(),
        found
    );
    assert_eq!(std::fs::read(temp.path()).unwrap(), before);
}
#[test]
fn player_scope_head_and_panic_guards_never_admit() {
    let (temp, mut store, engine) = fixture();
    let before = std::fs::read(temp.path()).unwrap();
    let mut npc = request(&engine);
    npc.observer = "mira".into();
    assert_eq!(
        store.lookup_memory_job(&npc, &engine, &|| false),
        Err(MemoryError::Stale)
    );
    assert_eq!(
        store.ensure_selected_memory_job(&npc, &engine, &|| false),
        Err(MemoryError::Stale)
    );
    let mut future = request(&engine);
    future.expected_head = 1;
    assert_eq!(
        store.lookup_memory_job(&future, &engine, &|| false),
        Err(MemoryError::Stale)
    );
    let mut foreign = engine.seed().clone();
    foreign.scope.story = "foreign-selected".into();
    let foreign = Engine::new(foreign).unwrap();
    assert_eq!(
        store.lookup_memory_job(&request(&engine), &foreign, &|| false),
        Err(MemoryError::Stale)
    );
    assert_eq!(
        store.lookup_memory_job(&request(&engine), &engine, &|| panic!("synthetic callback")),
        Err(MemoryError::Cancelled)
    );
    assert_eq!(
        store.ensure_selected_memory_job(&request(&engine), &engine, &|| true),
        Err(MemoryError::Cancelled)
    );
    assert_eq!(std::fs::read(temp.path()).unwrap(), before);
    assert_eq!(
        store
            .lookup_memory_job(&request(&engine), &engine, &|| false)
            .unwrap(),
        None
    );
}
#[test]
fn appended_history_returns_passive_stale_job_then_explicit_retarget() {
    let (temp, mut store, mut engine) = fixture();
    commit(&mut store, &mut engine, "old-prefix");
    let selected = engine.clone();
    let old = store
        .ensure_selected_memory_job(&request(&engine), &selected, &|| false)
        .unwrap();
    commit(&mut store, &mut engine, "normal-append");
    let before = std::fs::read(temp.path()).unwrap();
    let stale = store
        .lookup_memory_job(&request(&engine), &selected, &|| false)
        .unwrap()
        .unwrap();
    assert_eq!(stale.status, MemoryJobStatus::Stale);
    assert_eq!(stale.basis_revision, 1);
    assert_eq!(stale.generation, old.generation);
    assert_eq!(std::fs::read(temp.path()).unwrap(), before);
    let current = store
        .ensure_selected_memory_job(&request(&engine), &selected, &|| false)
        .unwrap();
    assert_eq!(current.basis_revision, 2);
    assert!(current.generation > old.generation);
    assert_eq!(current.handle, old.handle);
}
#[test]
fn same_seed_head_replacement_refuses_selected_lookup_and_admission() {
    let (temp, mut store, mut engine) = fixture();
    commit(&mut store, &mut engine, "original-receipt");
    let mut replacement = temp.store();
    // Produce a different valid accepted history through a separate actual Store.
    let alternate = Temp::new();
    let mut other = alternate.store();
    other
        .create_story("Synthetic selected maintenance", engine.seed().clone())
        .unwrap();
    let mut changed = other.resume(engine.scope()).unwrap().engine;
    commit(&mut other, &mut changed, "different-receipt");
    let archive = other
        .export_archive(&engine.scope().story, &|| false)
        .unwrap();
    let deletion = replacement
        .prepare_story_deletion(engine.scope(), 1, &|| false)
        .unwrap();
    replacement.delete_story(deletion, &|| false).unwrap();
    replacement
        .import_archive(
            validate_archive(archive.bytes(), &|| false).unwrap(),
            &|| false,
        )
        .unwrap();
    let before = std::fs::read(temp.path()).unwrap();
    assert_eq!(
        store.lookup_memory_job(&request(&engine), &engine, &|| false),
        Err(MemoryError::Stale)
    );
    assert_eq!(
        store.ensure_selected_memory_job(&request(&engine), &engine, &|| false),
        Err(MemoryError::Stale)
    );
    assert_eq!(std::fs::read(temp.path()).unwrap(), before);
    assert_eq!(
        store.resume(engine.scope()).unwrap().engine.receipts(),
        changed.receipts()
    );
}
#[test]
fn delete_import_never_rebinds_old_handle_to_recreated_same_source_job() {
    let (_temp, mut store, mut engine) = fixture();
    commit(&mut store, &mut engine, "fixed-identity");
    let old = store
        .ensure_selected_memory_job(&request(&engine), &engine, &|| false)
        .unwrap();
    let prepared = store
        .prepare_memory_job_step(&old.handle, &|| false)
        .unwrap();
    let archive = store
        .export_archive(&engine.scope().story, &|| false)
        .unwrap();
    let deletion = store
        .prepare_story_deletion(engine.scope(), 1, &|| false)
        .unwrap();
    store.delete_story(deletion, &|| false).unwrap();
    store
        .import_archive(
            validate_archive(archive.bytes(), &|| false).unwrap(),
            &|| false,
        )
        .unwrap();
    assert_eq!(
        store
            .lookup_memory_job(&request(&engine), &engine, &|| false)
            .unwrap(),
        None
    );
    let current = store
        .ensure_selected_memory_job(&request(&engine), &engine, &|| false)
        .unwrap();
    assert!(current.handle.id() > old.handle.id());
    assert_eq!(
        store.memory_job_status(&old.handle, &|| false),
        Err(MemoryError::NotFound)
    );
    assert_eq!(
        store.cancel_memory_job(&old.handle, &|| false),
        Err(MemoryError::NotFound)
    );
    assert_eq!(
        store.prune_memory_job(&old.handle, &|| false),
        Err(MemoryError::NotFound)
    );
    assert!(matches!(
        store.publish_memory_job_step(prepared, &|| false),
        Err(MemoryError::NotFound)
    ));
    assert_eq!(
        store.memory_job_status(&current.handle, &|| false).unwrap(),
        current
    );
}
