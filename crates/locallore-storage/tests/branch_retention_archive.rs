// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Public Store/API regressions. Retirement fixtures are produced by real deletion,
//! never by inserting synthetic retirement rows or relabelling accepted receipts.
use locallore::{contracts::*, engine::Engine};
use locallore_storage::{
    playable_archive::{validate_archive, ArchiveError, ARCHIVE_VERSION},
    BranchDeletionOutcome, ForkRequest, StorageError, Store, TurnError,
};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    cell::Cell,
    path::PathBuf,
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT: AtomicU64 = AtomicU64::new(0);
struct Temp(PathBuf);
impl Temp {
    fn new() -> Self {
        let path = std::env::temp_dir().join(format!(
            "locallore-retention-archive-{}-{}-{}",
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
fn seed() -> Seed {
    serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap()
}
fn apply(store: &mut Store, scope: &Scope, key: &str, command: Command) -> Receipt {
    let engine = store.resume(scope).unwrap().engine;
    let request = engine.request(key, Intent::Actions(vec![command]));
    let proposal = Engine::proposal(&request).unwrap();
    let text = engine.preview(&request, &proposal).unwrap();
    store.begin_turn(&request).unwrap();
    store
        .commit_turn(&request, &proposal, text.narration())
        .unwrap()
}
fn fork(store: &mut Store, parent: &Scope, branch: &str, at: u64) -> (Scope, ForkRequest) {
    let request = ForkRequest {
        parent: parent.clone(),
        child_branch: branch.into(),
        expected_parent_revision: store.resume(parent).unwrap().engine.revision(),
        at_revision: at,
    };
    (
        store.fork_branch(&request, &|| false).unwrap().scope,
        request,
    )
}
fn retire(store: &mut Store, scope: &Scope) -> BranchDeletionOutcome {
    let head = store.resume(scope).unwrap().engine.revision();
    let prepared = store
        .prepare_branch_deletion(scope, head, &|| false)
        .unwrap();
    store.delete_branch(prepared, &|| false).unwrap()
}
fn absent(store: &mut Store, scope: &Scope) {
    assert!(matches!(
        store.resume(scope),
        Err(TurnError::Storage(StorageError::NotFound))
    ));
}
fn canonical(value: &Value) -> Value {
    match value {
        Value::Object(map) => {
            let mut keys: Vec<_> = map.keys().collect();
            keys.sort_unstable();
            let mut output = serde_json::Map::new();
            for key in keys {
                output.insert(key.clone(), canonical(&map[key]));
            }
            Value::Object(output)
        }
        Value::Array(rows) => Value::Array(rows.iter().map(canonical).collect()),
        scalar => scalar.clone(),
    }
}
fn bytes(value: &Value) -> Vec<u8> {
    serde_json::to_vec(value).unwrap()
}
fn rehash(value: &mut Value) {
    value["integrity"]["payload_sha256"] = json!(format!(
        "{:x}",
        Sha256::digest(bytes(&canonical(&value["payload"])))
    ));
}
fn parsed(store: &mut Store, root: &Scope) -> Value {
    serde_json::from_slice(
        store
            .export_archive(&root.story, &|| false)
            .unwrap()
            .bytes(),
    )
    .unwrap()
}
struct Source {
    store: Store,
    root: Scope,
    parent: Scope,
    child: Scope,
    rewind: Scope,
    discarded: Scope,
    discarded_fork: ForkRequest,
    before: Value,
}
fn source(temp: &Temp) -> Source {
    let mut store = Store::open(&temp.path("source.sqlite3"), None).unwrap();
    let seed = seed();
    let root = seed.scope.clone();
    store
        .create_story("Original retained timelines", seed)
        .unwrap();
    apply(
        &mut store,
        &root,
        "shared-original",
        Command::Wait { ticks: 1 },
    );
    let (parent, _) = fork(&mut store, &root, "parent", 1);
    apply(
        &mut store,
        &parent,
        "parent-original",
        Command::Wait { ticks: 1 },
    );
    let (child, _) = fork(&mut store, &parent, "child", 2);
    let (rewind, _) = fork(&mut store, &parent, "rewind", 0);
    apply(
        &mut store,
        &child,
        "child-original",
        Command::Wait { ticks: 1 },
    );
    apply(
        &mut store,
        &rewind,
        "rewind-original",
        Command::Wait { ticks: 1 },
    );
    apply(
        &mut store,
        &parent,
        "deleted-future",
        Command::Say {
            text: "REMOVED_PARENT_FUTURE_CANARY".into(),
            audience: ["mira".into()].into(),
        },
    );
    let (discarded, discarded_fork) = fork(&mut store, &root, "discarded", 1);
    let before = parsed(&mut store, &root);
    Source {
        store,
        root,
        parent,
        child,
        rewind,
        discarded,
        discarded_fork,
        before,
    }
}
fn retired_source(temp: &Temp) -> Source {
    let mut source = source(temp);
    assert_eq!(
        retire(&mut source.store, &source.parent).retained_through_revision,
        Some(2)
    );
    assert_eq!(
        retire(&mut source.store, &source.discarded).retained_through_revision,
        None
    );
    source
}

#[test]
fn v2_round_trip_preserves_children_original_scopes_and_retired_admission() {
    let temp = Temp::new();
    let mut source = source(&temp);
    let before_child = source.store.resume(&source.child).unwrap().engine;
    let before_rewind = source.store.resume(&source.rewind).unwrap().engine;
    retire(&mut source.store, &source.parent);
    retire(&mut source.store, &source.discarded);
    let archive = source
        .store
        .export_archive(&source.root.story, &|| false)
        .unwrap();
    assert_eq!(ARCHIVE_VERSION, 2);
    assert_eq!(archive.preview().version, 2);
    assert_eq!(
        archive.preview().retired_branch_ids,
        ["discarded", "parent"]
    );
    assert_eq!(archive.preview().branch_heads.get("parent"), Some(&2));
    assert!(!archive.preview().branch_heads.contains_key("discarded"));
    assert!(!std::str::from_utf8(archive.bytes())
        .unwrap()
        .contains("REMOVED_PARENT_FUTURE_CANARY"));
    let mut imported = Store::open(&temp.path("imported.sqlite3"), None).unwrap();
    let outcome = imported
        .import_archive(
            validate_archive(archive.bytes(), &|| false).unwrap(),
            &|| false,
        )
        .unwrap();
    assert_eq!(outcome.root, source.root);
    assert_eq!(outcome.branches, 4);
    absent(&mut imported, &source.parent);
    absent(&mut imported, &source.discarded);
    for (scope, original) in [
        (&source.child, before_child),
        (&source.rewind, before_rewind),
    ] {
        let restored = imported.resume(scope).unwrap().engine;
        assert_eq!(restored.canonical_bytes(), original.canonical_bytes());
        assert_eq!(restored.receipts(), original.receipts());
    }
    let inherited = imported.resume(&source.child).unwrap().engine;
    assert_eq!(inherited.receipts()[0].request().scope, source.root);
    assert_eq!(inherited.receipts()[1].request().scope, source.parent);
    assert_eq!(inherited.receipts()[2].request().scope, source.child);
    assert_eq!(
        imported
            .export_archive(&source.root.story, &|| false)
            .unwrap()
            .bytes(),
        archive.bytes()
    );
    let gift = apply(
        &mut imported,
        &source.child,
        "continued-gift",
        Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 1,
        },
    );
    assert_eq!(
        imported
            .begin_turn(gift.request())
            .unwrap()
            .receipt
            .as_ref(),
        Some(&gift)
    );
    let reopened_scope = source.child.clone();
    drop(imported);
    let mut reopened = Store::open(&temp.path("imported.sqlite3"), None).unwrap();
    assert_eq!(
        reopened.resume(&reopened_scope).unwrap().engine.revision(),
        4
    );
    absent(&mut reopened, &source.parent);
}

#[test]
fn rewind_before_retired_parents_birth_preserves_birth_floor_without_leaking_future() {
    let temp = Temp::new();
    let mut store = Store::open(&temp.path("birth.sqlite3"), None).unwrap();
    let seed = seed();
    let root = seed.scope.clone();
    store.create_story("Original birth floor", seed).unwrap();
    for index in 0..4 {
        apply(
            &mut store,
            &root,
            &format!("root-{index}"),
            Command::Wait { ticks: 1 },
        );
    }
    let (parent, _) = fork(&mut store, &root, "born-at-four", 4);
    apply(
        &mut store,
        &parent,
        "removed-local",
        Command::Wait { ticks: 1 },
    );
    let (child, _) = fork(&mut store, &parent, "rewound-to-one", 1);
    apply(
        &mut store,
        &child,
        "child-local",
        Command::Wait { ticks: 1 },
    );
    let original = store.resume(&child).unwrap().engine;
    assert_eq!(
        retire(&mut store, &parent).retained_through_revision,
        Some(4)
    );
    let archive = store.export_archive(&root.story, &|| false).unwrap();
    assert_eq!(archive.preview().branch_heads.get(&parent.branch), Some(&4));
    let mut imported = Store::open(&temp.path("birth-import.sqlite3"), None).unwrap();
    imported
        .import_archive(
            validate_archive(archive.bytes(), &|| false).unwrap(),
            &|| false,
        )
        .unwrap();
    let restored = imported.resume(&child).unwrap().engine;
    assert_eq!(restored.canonical_bytes(), original.canonical_bytes());
    assert_eq!(restored.receipts(), original.receipts());
    assert!(restored
        .receipts()
        .iter()
        .all(|receipt| receipt.request().scope != parent));
    absent(&mut imported, &parent);
}

#[test]
fn gc_tombstones_survive_export_reopen_and_original_fork_retry() {
    let temp = Temp::new();
    let mut source = retired_source(&temp);
    retire(&mut source.store, &source.child);
    retire(&mut source.store, &source.rewind);
    let archive = source
        .store
        .export_archive(&source.root.story, &|| false)
        .unwrap();
    assert_eq!(archive.preview().branch_heads.len(), 1);
    assert_eq!(
        archive.preview().retired_branch_ids,
        ["child", "discarded", "parent", "rewind"]
    );
    let mut target = Store::open(&temp.path("gc.sqlite3"), None).unwrap();
    target
        .import_archive(
            validate_archive(archive.bytes(), &|| false).unwrap(),
            &|| false,
        )
        .unwrap();
    drop(target);
    let mut target = Store::open(&temp.path("gc.sqlite3"), None).unwrap();
    for scope in [
        &source.parent,
        &source.child,
        &source.rewind,
        &source.discarded,
    ] {
        absent(&mut target, scope);
    }
    assert!(matches!(
        target.fork_branch(&source.discarded_fork, &|| false),
        Err(TurnError::Storage(StorageError::NotFound))
    ));
    assert_eq!(
        target
            .export_archive(&source.root.story, &|| false)
            .unwrap()
            .bytes(),
        archive.bytes()
    );
    assert_eq!(target.resume(&source.root).unwrap().engine.revision(), 1);
}

#[test]
fn imported_retired_prefix_stays_cache_free_and_children_can_trigger_recursive_gc() {
    let temp = Temp::new();
    let mut source = retired_source(&temp);
    let archive = source
        .store
        .export_archive(&source.root.story, &|| false)
        .unwrap();
    let mut imported = Store::open(&temp.path("imported-gc.sqlite3"), None).unwrap();
    imported
        .import_archive(
            validate_archive(archive.bytes(), &|| false).unwrap(),
            &|| false,
        )
        .unwrap();
    let root_canon = imported
        .resume(&source.root)
        .unwrap()
        .engine
        .canonical_bytes();
    // Real deletion validates the cache-free retained-ancestor normal form before
    // each new plan. It must work after import, not merely before an export.
    retire(&mut imported, &source.child);
    let between = imported
        .export_archive(&source.root.story, &|| false)
        .unwrap();
    assert_eq!(between.preview().branch_heads.get("parent"), Some(&1));
    let final_delete = retire(&mut imported, &source.rewind);
    assert!(final_delete
        .invalidated_branches
        .contains(&source.parent.branch));
    let after = imported
        .export_archive(&source.root.story, &|| false)
        .unwrap();
    assert_eq!(after.preview().branch_heads.len(), 1);
    assert_eq!(
        after.preview().retired_branch_ids,
        ["child", "discarded", "parent", "rewind"]
    );
    assert_eq!(
        imported
            .resume(&source.root)
            .unwrap()
            .engine
            .canonical_bytes(),
        root_canon
    );
    absent(&mut imported, &source.parent);
    drop(imported);
    let mut reopened = Store::open(&temp.path("imported-gc.sqlite3"), None).unwrap();
    assert_eq!(
        reopened
            .export_archive(&source.root.story, &|| false)
            .unwrap()
            .bytes(),
        after.bytes()
    );
    assert!(matches!(
        reopened.fork_branch(&source.discarded_fork, &|| false),
        Err(TurnError::Storage(StorageError::NotFound))
    ));
}

#[test]
fn strict_v2_retirement_metadata_rejects_downgrades_and_rehashed_malformed_inputs() {
    let temp = Temp::new();
    let mut source = retired_source(&temp);
    let original = parsed(&mut source.store, &source.root);
    type Change = fn(&mut Value);
    let cases: Vec<(Change, ArchiveError)> = vec![
        (
            |v| {
                v["payload"]
                    .as_object_mut()
                    .unwrap()
                    .remove("retired_branch_ids");
            },
            ArchiveError::Malformed,
        ),
        (
            |v| v["payload"]["retired_branch_ids"] = Value::Null,
            ArchiveError::Malformed,
        ),
        (
            |v| v["payload"]["retired_branch_ids"] = json!([]),
            ArchiveError::Malformed,
        ),
        (
            |v| v["payload"]["retired_branch_ids"] = json!("parent"),
            ArchiveError::Malformed,
        ),
        (
            |v| v["payload"]["retired_branch_ids"] = json!(["parent", "discarded"]),
            ArchiveError::Integrity,
        ),
        (
            |v| v["payload"]["retired_branch_ids"] = json!(["parent", "parent"]),
            ArchiveError::Integrity,
        ),
        (
            |v| v["payload"]["retired_branch_ids"] = json!(["../parent"]),
            ArchiveError::Integrity,
        ),
        (
            |v| v["payload"]["retired_branch_ids"] = json!(["main"]),
            ArchiveError::Integrity,
        ),
        (
            |v| v["payload"]["retired_branch_ids"] = json!(["child", "discarded", "parent"]),
            ArchiveError::Integrity,
        ),
        (
            |v| v["payload"]["source_database_schema_version"] = json!(2),
            ArchiveError::Unsupported,
        ),
        (|v| v["version"] = json!(1), ArchiveError::Malformed),
        (
            |v| {
                v["version"] = json!(1);
                v["payload"]["retired_branch_ids"] = Value::Null;
            },
            ArchiveError::Malformed,
        ),
        (|v| v["version"] = json!(3), ArchiveError::Unsupported),
        (
            |v| v["payload"]["retired_branch_paths"] = json!(["private.sqlite3"]),
            ArchiveError::Malformed,
        ),
    ];
    for (change, expected) in cases {
        let mut value = original.clone();
        change(&mut value);
        rehash(&mut value);
        assert_eq!(
            validate_archive(&bytes(&value), &|| false).err(),
            Some(expected)
        );
    }
    let duplicate = String::from_utf8(bytes(&original)).unwrap().replace(
        "\"retired_branch_ids\":",
        "\"retired_branch_ids\":[],\"retired_branch_ids\":",
    );
    assert_eq!(
        validate_archive(duplicate.as_bytes(), &|| false).err(),
        Some(ArchiveError::Malformed)
    );
}

#[test]
fn rehashed_retired_leaf_and_untrimmed_parent_tail_are_not_accepted_as_ancestry() {
    let temp = Temp::new();
    let source = source(&temp);
    // Original all-active history and every state/receipt checksum are valid.
    // A changed payload checksum cannot justify retaining a deleted future.
    for retired in [json!(["parent"]), json!(["discarded"])] {
        let mut value = source.before.clone();
        value["version"] = json!(2);
        value["payload"]["retired_branch_ids"] = retired;
        rehash(&mut value);
        assert_eq!(
            validate_archive(&bytes(&value), &|| false).err(),
            Some(ArchiveError::Integrity)
        );
    }
}

#[test]
fn retirement_cap_counts_distinct_union_including_gc_and_physical_branches() {
    let temp = Temp::new();
    let mut source = retired_source(&temp);
    let mut value = parsed(&mut source.store, &source.root);
    // Four physical branches plus252 absent tombstones exactly meet the256-ID cap.
    let ids = |count: usize| {
        let mut ids = vec!["parent".to_owned()];
        ids.extend((0..count).map(|index| format!("gc-{index:03}")));
        ids.sort();
        json!(ids)
    };
    value["payload"]["retired_branch_ids"] = ids(252);
    rehash(&mut value);
    assert!(validate_archive(&bytes(&value), &|| false).is_ok());
    value["payload"]["retired_branch_ids"] = ids(253);
    rehash(&mut value);
    assert_eq!(
        validate_archive(&bytes(&value), &|| false).err(),
        Some(ArchiveError::TooLarge)
    );
    value["payload"]["retired_branch_ids"] = ids(256);
    rehash(&mut value);
    assert_eq!(
        validate_archive(&bytes(&value), &|| false).err(),
        Some(ArchiveError::TooLarge)
    );
}

#[test]
fn static_schema2_v1_stays_active_and_schema3_without_retirement_exports_v1() {
    let bytes = include_bytes!("../../../apps/android/app/src/androidTest/assets/platform-roundtrip-v1/windows-origin.json");
    let original: Value = serde_json::from_slice(bytes).unwrap();
    assert_eq!(original["version"], 1);
    assert_eq!(original["payload"]["source_database_schema_version"], 2);
    let validated = validate_archive(bytes, &|| false).unwrap();
    assert_eq!(validated.preview().version, 1);
    assert!(validated.preview().retired_branch_ids.is_empty());
    let temp = Temp::new();
    let mut target = Store::open(&temp.path("legacy-import.sqlite3"), None).unwrap();
    let outcome = target.import_archive(validated, &|| false).unwrap();
    for row in original["payload"]["branches"].as_array().unwrap() {
        let scope = Scope {
            story: outcome.root.story.clone(),
            branch: row["id"].as_str().unwrap().into(),
        };
        let engine = target.resume(&scope).unwrap().engine;
        assert_eq!(engine.revision(), row["head_revision"].as_u64().unwrap());
        let expected = row["local_receipts"].as_array().unwrap();
        assert_eq!(
            engine
                .receipts()
                .iter()
                .filter(|r| r.request().scope == scope)
                .map(|receipt| serde_json::to_value(receipt).unwrap())
                .collect::<Vec<_>>(),
            *expected
        );
    }
    let exported = target
        .export_archive(&outcome.root.story, &|| false)
        .unwrap();
    let current: Value = serde_json::from_slice(exported.bytes()).unwrap();
    assert_eq!(current["version"], 1);
    assert_eq!(
        current["payload"]["source_database_schema_version"],
        locallore_storage::SCHEMA_VERSION
    );
    assert!(current["payload"].get("retired_branch_ids").is_none());
    assert!(serde_json::to_value(exported.preview())
        .unwrap()
        .get("retired_branch_ids")
        .is_none());
    assert_eq!(
        current["payload"]["branches"],
        original["payload"]["branches"]
    );
}

#[test]
fn cancelled_import_rolls_back_retirement_rows_and_conflict_preserves_existing_story() {
    let temp = Temp::new();
    let mut source = retired_source(&temp);
    let archive = source
        .store
        .export_archive(&source.root.story, &|| false)
        .unwrap();
    let mut target = Store::open(&temp.path("rollback.sqlite3"), None).unwrap();
    // Cancellation after progressively later write units must leave no story or
    // orphan tombstone; a fresh successful import of exactly the same ID follows.
    for threshold in [2, 5, 20, 40] {
        let calls = Cell::new(0);
        let result = target.import_archive(
            validate_archive(archive.bytes(), &|| false).unwrap(),
            &|| {
                calls.set(calls.get() + 1);
                calls.get() >= threshold
            },
        );
        assert_eq!(result.err(), Some(ArchiveError::Cancelled));
        assert!(target.stories().unwrap().is_empty());
    }
    target
        .import_archive(
            validate_archive(archive.bytes(), &|| false).unwrap(),
            &|| false,
        )
        .unwrap();
    assert_eq!(
        target
            .import_archive(
                validate_archive(archive.bytes(), &|| false).unwrap(),
                &|| false
            )
            .err(),
        Some(ArchiveError::Conflict)
    );
    assert_eq!(
        target
            .export_archive(&source.root.story, &|| false)
            .unwrap()
            .bytes(),
        archive.bytes()
    );
    absent(&mut target, &source.parent);
}
