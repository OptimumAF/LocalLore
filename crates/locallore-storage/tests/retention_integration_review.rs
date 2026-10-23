// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent review of retirement against the accepted branch-cache owner.
//! Only synthetic files created by this test are opened; no production hook.
use locallore::{contracts::*, engine::Engine};
use locallore_storage::{
    derived_memory::{MemoryError, PrepareRequest, SearchRequest, Target},
    ArchiveError, DeletionError, ForkRequest, StorageError, Store, TurnError,
};
use rusqlite::Connection;
use std::{
    path::PathBuf,
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT: AtomicU64 = AtomicU64::new(0);
struct Fixture {
    path: PathBuf,
    store: Store,
    root: Scope,
    parent: Scope,
    child: Scope,
    sibling: Scope,
}
impl Fixture {
    fn new() -> Self {
        let directory = std::env::temp_dir().join(format!(
            "locallore-retention-review-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&directory).unwrap();
        std::fs::write(directory.join("owner-v1"), b"synthetic-retention-review-v1").unwrap();
        let path = directory.join("synthetic.sqlite");
        let mut store = Store::open(&path, None).unwrap();
        let seed: Seed =
            serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
        let root = seed.scope.clone();
        store
            .create_story("Independent synthetic retention review", seed)
            .unwrap();
        apply(&mut store, &root, "root", Command::Wait { ticks: 1 });
        let parent = fork(&mut store, &root, "parent", 1);
        say(&mut store, &parent, "kept", "INHERITED_CANARY");
        let child = fork(&mut store, &parent, "child", 2);
        say(&mut store, &parent, "future", "PARENT_FUTURE_CANARY");
        let sibling = fork(&mut store, &root, "sibling", 1);
        say(&mut store, &sibling, "sibling", "SIBLING_CANARY");
        say(&mut store, &child, "local", "CHILD_CANARY");
        Self {
            path,
            store,
            root,
            parent,
            child,
            sibling,
        }
    }
    fn retire_parent(&mut self) {
        let plan = self
            .store
            .prepare_branch_deletion(&self.parent, 3, &|| false)
            .unwrap();
        let result = self.store.delete_branch(plan, &|| false).unwrap();
        assert_eq!(result.retained_through_revision, Some(2));
        assert_eq!(result.invalidated_branches, [self.parent.branch.clone()]);
    }
}

fn apply(store: &mut Store, scope: &Scope, id: &str, command: Command) -> Receipt {
    let engine = store.resume(scope).unwrap().engine;
    let request = engine.request(id, Intent::Actions(vec![command]));
    let receipt = engine
        .preview(&request, &Engine::proposal(&request).unwrap())
        .unwrap();
    store.begin_turn(&request).unwrap();
    store.commit_prepared(&receipt).unwrap()
}
fn say(store: &mut Store, scope: &Scope, id: &str, text: &str) {
    apply(
        store,
        scope,
        id,
        Command::Say {
            text: text.into(),
            audience: ["mira".into()].into(),
        },
    );
}
fn fork(store: &mut Store, parent: &Scope, id: &str, at: u64) -> Scope {
    let head = store.resume(parent).unwrap().engine.revision();
    store
        .fork_branch(
            &ForkRequest {
                parent: parent.clone(),
                child_branch: id.into(),
                expected_parent_revision: head,
                at_revision: at,
            },
            &|| false,
        )
        .unwrap()
        .scope
}
fn memory(scope: &Scope, observer: &str, head: u64) -> PrepareRequest {
    PrepareRequest {
        scope: scope.clone(),
        expected_revision: head,
        observer: observer.into(),
        from_exclusive: 0,
        through_revision: head,
        target: Target::SceneWindow,
    }
}
fn search(store: &mut Store, scope: &Scope, observer: &str, head: u64, text: &str) -> usize {
    store
        .search_memory(
            &SearchRequest {
                scope: scope.clone(),
                expected_revision: head,
                observer: observer.into(),
                text: text.into(),
                limit: 16,
            },
            &|| false,
        )
        .unwrap()
        .len()
}

#[test]
fn retained_child_cache_tokens_keep_original_sources_but_retired_target_tokens_cannot_publish() {
    let mut f = Fixture::new();
    let before = f.store.resume(&f.child).unwrap().engine;
    let child = memory(&f.child, "mira", 3);
    let parent = memory(&f.parent, "mira", 3);
    let child_token = f.store.prepare_memory(&child, &|| false).unwrap();
    let parent_token = f.store.prepare_memory(&parent, &|| false).unwrap();
    let sibling_token = f
        .store
        .prepare_memory(&memory(&f.sibling, "mira", 2), &|| false)
        .unwrap();
    f.retire_parent();
    // The private prefix's original scope remains unchanged by retirement, so
    // a live child's exact token remains publishable across that transaction.
    f.store.publish_memory(child_token, &|| false).unwrap();
    f.store.publish_memory(sibling_token, &|| false).unwrap();
    assert_eq!(
        f.store.publish_memory(parent_token, &|| false).err(),
        Some(MemoryError::NotFound)
    );
    let packet = f
        .store
        .read_memory(&child, &|| false)
        .unwrap()
        .json()
        .to_string();
    assert!(packet.contains("INHERITED_CANARY") && packet.contains("CHILD_CANARY"));
    assert!(!packet.contains("PARENT_FUTURE_CANARY") && !packet.contains("SIBLING_CANARY"));
    for text in ["INHERITED_CANARY", "CHILD_CANARY"] {
        assert!(search(&mut f.store, &f.child, "mira", 3, text) > 0);
    }
    for text in ["PARENT_FUTURE_CANARY", "SIBLING_CANARY"] {
        assert_eq!(search(&mut f.store, &f.child, "mira", 3, text), 0);
    }
    let sable = memory(&f.child, "sable", 3);
    // V1 intentionally refuses an empty eligible source window; absence is not
    // a fabricated empty packet or permission to borrow Mira's materialization.
    assert_eq!(
        f.store.prepare_memory(&sable, &|| false).err(),
        Some(MemoryError::NotFound)
    );
    assert_eq!(
        search(&mut f.store, &f.child, "sable", 3, "INHERITED_CANARY"),
        0
    );
    let after = f.store.resume(&f.child).unwrap().engine;
    assert_eq!(before.canonical_bytes(), after.canonical_bytes());
    assert_eq!(before.receipts(), after.receipts());
    assert_eq!(after.receipts()[1].request().scope, f.parent);
    let old_token = f.store.prepare_memory(&child, &|| false).unwrap();
    let plan = f
        .store
        .prepare_branch_deletion(&f.child, 3, &|| false)
        .unwrap();
    let out = f.store.delete_branch(plan, &|| false).unwrap();
    assert_eq!(out.collected_branches, 2);
    assert_eq!(
        f.store.publish_memory(old_token, &|| false).err(),
        Some(MemoryError::NotFound)
    );
    assert_eq!(
        f.store.read_memory(&child, &|| false).err(),
        Some(MemoryError::NotFound)
    );
    assert_eq!(
        f.store
            .fork_branch(
                &ForkRequest {
                    parent: f.root,
                    child_branch: f.child.branch,
                    expected_parent_revision: 1,
                    at_revision: 0
                },
                &|| false
            )
            .err(),
        Some(TurnError::Storage(StorageError::NotFound))
    );
}

#[test]
fn corrupted_retained_source_is_replayed_before_cached_read_search_catalog_or_export() {
    let mut f = Fixture::new();
    let child = memory(&f.child, "mira", 3);
    let token = f.store.prepare_memory(&child, &|| false).unwrap();
    f.store.publish_memory(token, &|| false).unwrap();
    f.retire_parent();
    let db = Connection::open(&f.path).unwrap();
    assert_eq!(db.execute("DELETE FROM event_witnesses WHERE story_id=?1 AND branch_id=?2 AND sequence=2 AND observer_id='mira'",
        (&f.parent.story, &f.parent.branch)).unwrap(), 1);
    // A valid cached packet and projection cannot mask a corrupt original
    // inherited witness ledger, including before TEMP FTS materialization.
    assert_eq!(
        f.store.read_memory(&child, &|| false).err(),
        Some(MemoryError::Integrity)
    );
    assert_eq!(
        f.store
            .search_memory(
                &SearchRequest {
                    scope: f.child.clone(),
                    expected_revision: 3,
                    observer: "mira".into(),
                    text: "INHERITED_CANARY".into(),
                    limit: 1
                },
                &|| false
            )
            .err(),
        Some(MemoryError::Integrity)
    );
    assert_eq!(
        f.store.branch_catalog(&f.root.story, &|| false).err(),
        Some(TurnError::Integrity)
    );
    assert_eq!(
        f.store.export_archive(&f.root.story, &|| false).err(),
        Some(ArchiveError::Integrity)
    );
    assert_eq!(
        f.store
            .prepare_branch_deletion(&f.child, 3, &|| false)
            .err(),
        Some(DeletionError::Integrity)
    );
    db.execute("INSERT INTO event_witnesses(story_id,branch_id,sequence,observer_id) VALUES(?1,?2,2,'mira')",
        (&f.parent.story, &f.parent.branch)).unwrap();
    assert!(f
        .store
        .read_memory(&child, &|| false)
        .unwrap()
        .json()
        .to_string()
        .contains("INHERITED_CANARY"));
}

#[test]
fn competing_owner_child_commit_stales_consent_and_accepted_child_retry_survives_retirement() {
    let mut f = Fixture::new();
    let old_plan = f
        .store
        .prepare_branch_deletion(&f.parent, 3, &|| false)
        .unwrap();
    let mut other = Store::open(&f.path, None).unwrap();
    let receipt = apply(
        &mut other,
        &f.child,
        "other-owner",
        Command::Wait { ticks: 1 },
    );
    assert_eq!(
        f.store.delete_branch(old_plan, &|| false).err(),
        Some(DeletionError::Stale)
    );
    assert_eq!(f.store.resume(&f.parent).unwrap().engine.revision(), 3);
    assert_eq!(f.store.resume(&f.child).unwrap().engine.revision(), 4);
    let first = f
        .store
        .prepare_branch_deletion(&f.parent, 3, &|| false)
        .unwrap();
    let competing = other
        .prepare_branch_deletion(&f.parent, 3, &|| false)
        .unwrap();
    f.store.delete_branch(first, &|| false).unwrap();
    assert_eq!(
        other.delete_branch(competing, &|| false).err(),
        Some(DeletionError::Stale)
    );
    // Exact accepted child retry uses its own original request/receipt even
    // though an original ancestor's public target is now retired.
    assert_eq!(other.commit_prepared(&receipt).unwrap(), receipt);
    assert_eq!(other.resume(&f.child).unwrap().engine.revision(), 4);
    assert_eq!(
        other.resume(&f.parent).err(),
        Some(TurnError::Storage(StorageError::NotFound))
    );
    let archive = other.export_archive(&f.root.story, &|| false).unwrap();
    let mut imported = Store::open(&f.path.with_file_name("roundtrip.sqlite"), None).unwrap();
    imported
        .import_archive(
            locallore_storage::validate_archive(archive.bytes(), &|| false).unwrap(),
            &|| false,
        )
        .unwrap();
    assert_eq!(imported.commit_prepared(&receipt).unwrap(), receipt);
    assert_eq!(
        imported.resume(&f.child).unwrap().engine.canonical_bytes(),
        other.resume(&f.child).unwrap().engine.canonical_bytes()
    );
    assert_eq!(
        imported.resume(&f.parent).err(),
        Some(TurnError::Storage(StorageError::NotFound))
    );
}

#[cfg(feature = "development-fixtures")]
#[test]
fn private_revocation_does_not_depend_on_new_retired_scope_database_admission() {
    use locallore::host::{Host, Persistence, SavedTurn, WorkspaceSummary};
    use serde_json::{json, Value};
    use std::sync::{atomic::AtomicBool, Arc};
    struct Port {
        engine: Engine,
        unavailable: Arc<AtomicBool>,
        validations: Arc<AtomicU64>,
    }
    impl Persistence for Port {
        fn validate_scope(&mut self, _: &Scope) -> Result<(), String> {
            self.validations.fetch_add(1, Ordering::SeqCst);
            if self.unavailable.load(Ordering::SeqCst) {
                Err("Database".into())
            } else {
                Ok(())
            }
        }
        fn location(&self) -> &str {
            "synthetic-private-revoke-review"
        }
        fn list(&mut self) -> Result<Vec<WorkspaceSummary>, String> {
            Err("Database".into())
        }
        fn create(&mut self) -> Result<Engine, String> {
            Ok(self.engine.clone())
        }
        fn resume(&mut self, _: &Scope) -> Result<Engine, String> {
            if self.unavailable.load(Ordering::SeqCst) {
                Err("Database".into())
            } else {
                Ok(self.engine.clone())
            }
        }
        fn begin(&mut self, _: &Request) -> Result<SavedTurn, String> {
            Err("Database".into())
        }
        fn commit(&mut self, _: &Request, _: &Proposal, _: &str) -> Result<Receipt, String> {
            Err("Database".into())
        }
        fn cancel(&mut self, _: &Request) -> Result<SavedTurn, String> {
            Err("Database".into())
        }
        fn fail(&mut self, _: &Request) -> Result<SavedTurn, String> {
            Err("Database".into())
        }
        fn stale(&mut self, _: &Request) -> Result<SavedTurn, String> {
            Err("Database".into())
        }
        fn status(&mut self, _: &Scope, _: &str) -> Result<SavedTurn, String> {
            Err("Database".into())
        }
    }
    let seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    let scope = seed.scope.clone();
    let unavailable = Arc::new(AtomicBool::new(false));
    let validations = Arc::new(AtomicU64::new(0));
    let host = Host::with_persistence(
        true,
        Box::new(Port {
            engine: Engine::new(seed).unwrap(),
            unavailable: unavailable.clone(),
            validations: validations.clone(),
        }),
    );
    let call = |command: Value| {
        host.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
    };
    let created = call(json!({"op":"create","seed":"lantern-quay-v1"}));
    assert_eq!(created["status"], "ok");
    let session = created["data"]["session"].as_str().unwrap();
    let configured = call(
        json!({"op":"trace_capture_configure","session":session,"scope":scope,
        "expected_head":0,"enabled":true,"consent":true}),
    );
    assert_eq!(configured["status"], "ok");
    unavailable.store(true, Ordering::SeqCst);
    let before = validations.load(Ordering::SeqCst);
    let mut wrong = scope.clone();
    wrong.branch = "other".into();
    assert_eq!(
        call(json!({"op":"trace_capture_revoke","session":session,"scope":wrong}))["error"],
        "Scope"
    );
    let revoked = call(json!({"op":"trace_capture_revoke","session":session,"scope":scope}));
    assert_eq!(revoked["data"]["revoked"], true,
        "owner-only narrowing must succeed even when retired-scope admission cannot read SQLite: {revoked}");
    assert_eq!(
        validations.load(Ordering::SeqCst),
        before,
        "revocation must perform no canonical admission read"
    );
    assert_eq!(
        call(json!({"op":"open","session":session,"scope":scope}))["error"],
        "Database",
        "normal canonical access must still fail closed"
    );
}
