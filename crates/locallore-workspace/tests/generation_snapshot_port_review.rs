// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent actual Store/Host archive-replacement regressions; no model or SQL fixture writes.
use locallore::{
    contracts::{Command, Intent, Scope},
    engine::Engine,
    host::Host,
};
use locallore_storage::{playable_archive::validate_archive, ForkRequest, Store};
use serde_json::{json, Value};
use std::{
    path::PathBuf,
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT: AtomicU64 = AtomicU64::new(0);
struct Fixture {
    parent: PathBuf,
    directory: PathBuf,
}
impl Fixture {
    fn new() -> Self {
        let parent = std::env::temp_dir().canonicalize().unwrap();
        let directory = parent.join(format!(
            "locallore-generation-port-review-{}-{}-{}",
            std::process::id(),
            NEXT.fetch_add(1, Ordering::SeqCst),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        std::fs::create_dir(&directory).unwrap();
        Self { parent, directory }
    }
    fn path(&self) -> PathBuf {
        self.directory.join("review.sqlite")
    }
    fn host(&self) -> Host {
        locallore_workspace::open(&self.path(), false).unwrap()
    }
    fn store(&self) -> Store {
        Store::open_application(&self.path()).unwrap()
    }
}
impl Drop for Fixture {
    fn drop(&mut self) {
        let actual = self.directory.canonicalize().unwrap();
        assert_eq!(actual, self.directory);
        assert_eq!(actual.parent(), Some(self.parent.as_path()));
        assert!(actual
            .file_name()
            .unwrap()
            .to_str()
            .unwrap()
            .starts_with("locallore-generation-port-review-"));
        std::fs::remove_dir_all(actual).unwrap();
    }
}
fn call(host: &Host, command: Value) -> Value {
    host.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
}
fn create(host: &Host) -> (String, Scope) {
    let result = call(host, json!({"op":"create","seed":"lantern-quay-v1"}));
    assert_eq!(result["status"], "ok", "{result}");
    (
        result["data"]["session"].as_str().unwrap().into(),
        serde_json::from_value(result["data"]["scope"].clone()).unwrap(),
    )
}
fn resume(host: &Host, scope: &Scope) -> String {
    let result = call(host, json!({"op":"resume","scope":scope}));
    assert_eq!(result["status"], "ok", "{result}");
    result["data"]["session"].as_str().unwrap().into()
}
fn commit_host(host: &Host, session: &str, engine: &Engine, turn: &str) {
    let request = engine.request(turn, Intent::Actions(vec![Command::Wait { ticks: 1 }]));
    let submitted = call(
        host,
        json!({"op":"submit","session":session,"request":request,"mode":"accepted"}),
    );
    assert_eq!(submitted["data"]["phase"], "queued", "{submitted}");
    for (op, expected) in [("prepare", "ready"), ("commit", "committed")] {
        let result = call(
            host,
            json!({"op":op,"session":session,"scope":request.scope,"turn":turn}),
        );
        assert_eq!(result["data"]["phase"], expected, "{result}");
    }
}
fn commit_store(store: &mut Store, scope: &Scope, turn: &str, ticks: u16) {
    let engine = store.resume(scope).unwrap().engine;
    let request = engine.request(turn, Intent::Actions(vec![Command::Wait { ticks }]));
    let proposal = Engine::proposal(&request).unwrap();
    let receipt = engine.preview(&request, &proposal).unwrap();
    store.begin_turn(&request).unwrap();
    store
        .commit_turn(&request, &proposal, receipt.narration())
        .unwrap();
}
fn replace_story(target: &mut Store, root: &Scope, old_head: u64, source: &mut Store) {
    let archive = source.export_archive(&root.story, &|| false).unwrap();
    let validated = validate_archive(archive.bytes(), &|| false).unwrap();
    let deletion = target
        .prepare_story_deletion(root, old_head, &|| false)
        .unwrap();
    target.delete_story(deletion, &|| false).unwrap();
    target.import_archive(validated, &|| false).unwrap();
}
fn assert_stale_preserving_replacement(
    host: &Host,
    session: &str,
    scope: &Scope,
    expected_head: u64,
    store: &mut Store,
) {
    let before = store.resume(scope).unwrap().engine;
    let result = host.generation_snapshot(session, scope, expected_head, &|| false);
    let after = store.resume(scope).unwrap().engine;
    assert_eq!(after.canonical_bytes(), before.canonical_bytes());
    assert_eq!(after.receipts(), before.receipts());
    let error = result.err();
    assert_eq!(
        error.as_deref(),
        Some("Stale"),
        "an old selected session must not silently consume replacement accepted history/ancestry"
    );
}
fn history_replacement(ticks: Option<u16>) {
    let target = Fixture::new();
    let host = target.host();
    let (session, scope) = create(&host);
    let mut target_store = target.store();
    let initial = target_store.resume(&scope).unwrap().engine;
    commit_host(&host, &session, &initial, "original-prefix");
    let original = target_store.resume(&scope).unwrap().engine;
    let alternate = Fixture::new();
    let mut source = alternate.store();
    source
        .create_story("Independent replacement", original.seed().clone())
        .unwrap();
    if let Some(ticks) = ticks {
        commit_store(&mut source, &scope, "replacement-prefix", ticks);
    }
    let replacement = source.resume(&scope).unwrap().engine;
    assert_eq!(replacement.seed(), original.seed());
    assert_eq!(replacement.scope(), original.scope());
    assert_ne!(replacement.receipts(), original.receipts());
    if ticks == Some(1) {
        assert_eq!(replacement.canonical_bytes(), original.canonical_bytes());
        assert_eq!(replacement.revision(), original.revision());
    }
    if ticks == Some(2) {
        assert_ne!(replacement.canonical_bytes(), original.canonical_bytes());
        assert_eq!(replacement.revision(), original.revision());
    }
    if ticks.is_none() {
        assert_eq!(replacement.revision(), 0);
        assert_eq!(original.revision(), 1);
    }
    replace_story(&mut target_store, &scope, 1, &mut source);
    assert_stale_preserving_replacement(
        &host,
        &session,
        &scope,
        replacement.revision(),
        &mut target_store,
    );
}
#[test]
fn same_seed_head_replacement_with_changed_canon_is_stale() {
    history_replacement(Some(2));
}
#[test]
fn same_projection_head_replacement_with_changed_receipt_identity_is_stale() {
    history_replacement(Some(1));
}
#[test]
fn same_seed_replacement_cannot_rewind_a_selected_completed_prefix() {
    history_replacement(None);
}
#[test]
fn ordinary_other_owner_append_of_the_exact_selected_prefix_remains_allowed() {
    let fixture = Fixture::new();
    let host = fixture.host();
    let (session, scope) = create(&host);
    let mut store = fixture.store();
    let initial = store.resume(&scope).unwrap().engine;
    commit_host(&host, &session, &initial, "retained-prefix");
    let prefix = store.resume(&scope).unwrap().engine;
    commit_store(&mut store, &scope, "external-extension", 2);
    let actual = store.resume(&scope).unwrap().engine;
    let snapshot = host
        .generation_snapshot(&session, &scope, 2, &|| false)
        .unwrap();
    assert_eq!(snapshot.engine.revision(), 2);
    assert!(snapshot.engine.receipts().starts_with(prefix.receipts()));
    assert_eq!(snapshot.engine.receipts(), actual.receipts());
    assert_eq!(snapshot.engine.canonical_bytes(), actual.canonical_bytes());
}
fn fork(store: &mut Store, parent: &Scope, child: &str) -> Scope {
    store
        .fork_branch(
            &ForkRequest {
                parent: parent.clone(),
                child_branch: child.into(),
                expected_parent_revision: 0,
                at_revision: 0,
            },
            &|| false,
        )
        .unwrap()
        .scope
}
#[test]
fn same_seed_empty_history_selected_child_cannot_change_original_parent_chain() {
    let target = Fixture::new();
    let host = target.host();
    let (_, root) = create(&host);
    let mut store = target.store();
    let seed = store.resume(&root).unwrap().engine.seed().clone();
    let old_parent = fork(&mut store, &root, "old-parent");
    let selected = fork(&mut store, &old_parent, "selected-child");
    let session = resume(&host, &selected);
    let old = store.resume(&selected).unwrap().engine;
    let alternate = Fixture::new();
    let mut source = alternate.store();
    source.create_story("New ancestry", seed).unwrap();
    let new_parent = fork(&mut source, &root, "new-parent");
    assert_eq!(fork(&mut source, &new_parent, "selected-child"), selected);
    let replacement = source.resume(&selected).unwrap().engine;
    assert_eq!(old.seed(), replacement.seed());
    assert_eq!(old.revision(), replacement.revision());
    assert_eq!(old.receipts(), replacement.receipts());
    assert_eq!(old.canonical_bytes(), replacement.canonical_bytes());
    let parent_before = store
        .branch_catalog(&root.story, &|| false)
        .unwrap()
        .branches
        .into_iter()
        .find(|branch| branch.scope == selected)
        .unwrap()
        .parent_branch;
    replace_story(&mut store, &root, 0, &mut source);
    let parent_after = store
        .branch_catalog(&root.story, &|| false)
        .unwrap()
        .branches
        .into_iter()
        .find(|branch| branch.scope == selected)
        .unwrap()
        .parent_branch;
    assert_ne!(parent_before, parent_after);
    assert_stale_preserving_replacement(&host, &session, &selected, 0, &mut store);
}
