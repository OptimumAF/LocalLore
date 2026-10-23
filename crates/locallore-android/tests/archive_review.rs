// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent native-capability attacks. No model, JNI emulator, SQL or production hooks.
use locallore::{
    contracts::{Command, Intent, Scope, Seed},
    engine::Engine,
};
use locallore_android::archive::ArchiveRegistry;
use locallore_storage::Store;
use serde_json::{json, Value};
use std::{
    fs,
    path::{Path, PathBuf},
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT: AtomicU64 = AtomicU64::new(0);
struct Synthetic(PathBuf);
impl Synthetic {
    fn new() -> Self {
        let root = std::env::temp_dir().join(format!(
            "locallore-archive-review-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::SeqCst)
        ));
        fs::create_dir(&root).unwrap();
        Self(root)
    }
    fn path(&self, name: &str) -> PathBuf {
        self.0.join(name)
    }
    fn directory(&self, name: &str) -> PathBuf {
        let path = self.path(name);
        fs::create_dir(&path).unwrap();
        path
    }
}
impl Drop for Synthetic {
    fn drop(&mut self) {
        // Every operation in this suite is synchronous, and handles drop before this fixture.
        // All descendants were created by this test; no external/user paths are adopted.
        let _ = fs::remove_dir_all(&self.0);
    }
}
struct Owner<'a> {
    registry: &'a ArchiveRegistry,
    handle: u64,
}
impl<'a> Owner<'a> {
    fn new(registry: &'a ArchiveRegistry, db: &Path, stage: &Path) -> Self {
        Self {
            registry,
            handle: registry.open(db, stage).unwrap(),
        }
    }
}
impl Drop for Owner<'_> {
    fn drop(&mut self) {
        self.registry.close(self.handle);
    }
}
fn story(path: &Path, id: &str, give: bool) -> Scope {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    seed.scope.story = id.into();
    let scope = seed.scope.clone();
    let mut store = Store::open(path, None).unwrap();
    store
        .create_story("Literal <script> ../private story", seed)
        .unwrap();
    let engine = store.resume(&scope).unwrap().engine;
    let action = if give {
        Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 1,
        }
    } else {
        Command::Wait { ticks: 1 }
    };
    let request = engine.request("accepted-review-turn", Intent::Actions(vec![action]));
    let proposal = Engine::proposal(&request).unwrap();
    let preview = engine.preview(&request, &proposal).unwrap();
    store.begin_turn(&request).unwrap();
    store
        .commit_turn(&request, &proposal, preview.narration())
        .unwrap();
    scope
}
fn canonical(path: &Path, scope: &Scope) -> Vec<u8> {
    Store::open_read_only(path)
        .unwrap()
        .resume(scope)
        .unwrap()
        .engine
        .canonical_bytes()
}
fn witness(path: &Path) -> Vec<(String, String, u64, Vec<u8>)> {
    let mut store = Store::open_read_only(path).unwrap();
    store
        .stories()
        .unwrap()
        .into_iter()
        .map(|row| {
            let bytes = store.resume(&row.scope).unwrap().engine.canonical_bytes();
            (row.scope.story, row.title, row.revision, bytes)
        })
        .collect()
}
fn bytes(path: &Path, scope: &Scope) -> Vec<u8> {
    Store::open_read_only(path)
        .unwrap()
        .export_archive(&scope.story, &|| false)
        .unwrap()
        .bytes()
        .to_vec()
}
fn ok(reply: Vec<u8>) -> Value {
    assert!(reply.len() <= 16 * 1024);
    let value: Value = serde_json::from_slice(&reply).unwrap();
    assert_eq!(value["version"], 1);
    assert_eq!(value["status"], "ok", "{value}");
    value["data"].clone()
}
fn rejected(reply: Vec<u8>, error: &str) {
    assert!(reply.len() <= 16 * 1024);
    assert_eq!(
        serde_json::from_slice::<Value>(&reply).unwrap(),
        json!({"version":1,"status":"rejected","error":error})
    );
}
fn token(value: &Value) -> u64 {
    let token = value["token"].as_u64().unwrap();
    assert!(token > 0 && token <= i64::MAX as u64);
    token
}
fn export_request(scope: &Scope) -> Vec<u8> {
    serde_json::to_vec(&json!({"story":scope.story,"branch":scope.branch,"expected_revision":1}))
        .unwrap()
}

#[test]
fn missing_foreign_and_non_directory_construction_never_adopts_or_creates_paths() {
    let files = Synthetic::new();
    let db = files.path("existing.sqlite3");
    story(&db, "retained-review", false);
    let before = witness(&db);
    let stage = files.directory("staging");
    let registry = ArchiveRegistry::default();
    let absent_db = files.path("missing.sqlite3");
    assert_eq!(registry.open(&absent_db, &stage).unwrap_err(), "Io");
    assert!(!absent_db.exists());
    let absent_stage = files.path("missing-staging");
    assert_eq!(registry.open(&db, &absent_stage).unwrap_err(), "Io");
    assert!(!absent_stage.exists());
    let foreign = files.path("foreign.sqlite3");
    let canary = b"NOT_SQLITE_PRIVATE_SENTINEL";
    fs::write(&foreign, canary).unwrap();
    let category = registry.open(&foreign, &stage).unwrap_err();
    assert!(["Io", "Integrity", "Database", "Unsupported", "Internal"].contains(&category.as_str()));
    assert_eq!(fs::read(&foreign).unwrap(), canary);
    assert_eq!(registry.open(&db, &foreign).unwrap_err(), "Io");
    assert_eq!(fs::read(&foreign).unwrap(), canary);
    assert_eq!(witness(&db), before);
    assert_eq!(fs::read_dir(stage).unwrap().count(), 0);
}

#[test]
fn cross_owner_and_wrong_kind_tokens_cannot_consume_another_exact_capability() {
    let files = Synthetic::new();
    let source = files.path("source.sqlite3");
    let target = files.path("target.sqlite3");
    let source_scope = story(&source, "source-review", true);
    let retained_scope = story(&target, "retained-review", false);
    let retained = canonical(&target, &retained_scope);
    let expected = canonical(&source, &source_scope);
    let input = bytes(&source, &source_scope);
    let stage = files.directory("staging");
    let registry = ArchiveRegistry::default();
    let importing = Owner::new(&registry, &target, &stage);
    let exporting = Owner::new(&registry, &source, &stage);
    let imported = token(&ok(registry.prepare_import(importing.handle, &input)));
    let exported = token(&ok(
        registry.prepare_export(exporting.handle, &export_request(&source_scope))
    ));
    assert_ne!(imported, exported);
    assert_eq!(
        registry
            .export_bytes(importing.handle, imported)
            .unwrap_err(),
        "InvalidToken"
    );
    rejected(
        registry.commit_import(exporting.handle, exported),
        "InvalidToken",
    );
    rejected(
        registry.commit_import(importing.handle, exported),
        "InvalidToken",
    );
    assert_eq!(
        registry
            .export_bytes(exporting.handle, imported)
            .unwrap_err(),
        "InvalidToken"
    );
    assert_eq!(
        registry.export_bytes(exporting.handle, exported).unwrap(),
        input
    );
    let committed = ok(registry.commit_import(importing.handle, imported));
    assert_eq!(
        committed["root"],
        json!({"story":source_scope.story,"branch":source_scope.branch})
    );
    assert_eq!(canonical(&target, &source_scope), expected);
    assert_eq!(canonical(&target, &retained_scope), retained);
    rejected(
        registry.commit_import(importing.handle, imported),
        "InvalidToken",
    );
    assert_eq!(
        registry
            .export_bytes(exporting.handle, exported)
            .unwrap_err(),
        "InvalidToken"
    );
    assert_eq!(fs::read_dir(stage).unwrap().count(), 0);
}

#[test]
fn failed_replacement_cancel_and_closed_owner_do_not_resurrect_an_older_grant() {
    let files = Synthetic::new();
    let source = files.path("source.sqlite3");
    let target = files.path("target.sqlite3");
    let source_scope = story(&source, "source-review", true);
    story(&target, "retained-review", false);
    let before = witness(&target);
    let input = bytes(&source, &source_scope);
    let stage = files.directory("staging");
    let registry = ArchiveRegistry::default();
    let owner = Owner::new(&registry, &target, &stage);
    let replaced = token(&ok(registry.prepare_import(owner.handle, &input)));
    rejected(
        registry.prepare_import(owner.handle, b"{\"private-sentinel\":"),
        "Malformed",
    );
    rejected(
        registry.commit_import(owner.handle, replaced),
        "InvalidToken",
    );
    let cancelled = token(&ok(registry.prepare_import(owner.handle, &input)));
    assert!(cancelled > replaced);
    registry.cancel(owner.handle);
    rejected(
        registry.commit_import(owner.handle, cancelled),
        "InvalidToken",
    );
    let closed = token(&ok(registry.prepare_import(owner.handle, &input)));
    registry.close(owner.handle);
    let fresh = Owner::new(&registry, &target, &stage);
    rejected(
        registry.commit_import(owner.handle, closed),
        "InvalidHandle",
    );
    let fresh_token = token(&ok(registry.prepare_import(fresh.handle, &input)));
    assert!(fresh_token > closed);
    rejected(registry.commit_import(fresh.handle, closed), "InvalidToken");
    registry.cancel(fresh.handle);
    assert_eq!(witness(&target), before);
    assert_eq!(fs::read_dir(stage).unwrap().count(), 0);
}

#[test]
fn preexisting_stage_with_valid_database_is_never_adopted_cleaned_or_imported() {
    let files = Synthetic::new();
    let source = files.path("source.sqlite3");
    let target = files.path("target.sqlite3");
    let source_scope = story(&source, "source-review", true);
    let retained_scope = story(&target, "retained-review", false);
    let retained = canonical(&target, &retained_scope);
    let before = witness(&target);
    let expected = canonical(&source, &source_scope);
    let input = bytes(&source, &source_scope);
    let stage = files.directory("staging");
    let registry = ArchiveRegistry::default();
    let owner = Owner::new(&registry, &target, &stage);
    let pending = token(&ok(registry.prepare_import(owner.handle, &input)));
    let collision = stage.join(format!("archive-{}-{pending}", owner.handle));
    fs::create_dir(&collision).unwrap();
    let foreign_db = collision.join("staged.sqlite3");
    fs::copy(&target, &foreign_db).unwrap();
    let foreign_before = fs::read(&foreign_db).unwrap();
    let sentinel = collision.join("do-not-adopt.txt");
    fs::write(&sentinel, b"FOREIGN_STAGE_REVIEW_CANARY").unwrap();
    rejected(registry.commit_import(owner.handle, pending), "Io");
    assert_eq!(fs::read(&foreign_db).unwrap(), foreign_before);
    assert_eq!(fs::read(&sentinel).unwrap(), b"FOREIGN_STAGE_REVIEW_CANARY");
    assert_eq!(witness(&target), before);
    rejected(
        registry.commit_import(owner.handle, pending),
        "InvalidToken",
    );
    let replacement = token(&ok(registry.prepare_import(owner.handle, &input)));
    ok(registry.commit_import(owner.handle, replacement));
    assert_eq!(canonical(&target, &source_scope), expected);
    assert_eq!(canonical(&target, &retained_scope), retained);
    assert_eq!(fs::read(&foreign_db).unwrap(), foreign_before);
    assert_eq!(fs::read(&sentinel).unwrap(), b"FOREIGN_STAGE_REVIEW_CANARY");
    assert_eq!(fs::read_dir(stage).unwrap().count(), 1);
}
