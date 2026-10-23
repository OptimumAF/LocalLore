// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Actual Store/Engine archives through the Android owner. No model, device or picker claim.
use locallore::{contracts::*, engine::Engine};
use locallore_android::archive::ArchiveRegistry;
use locallore_storage::{
    playable_archive::MAX_ARCHIVE_BYTES, validate_archive, ForkRequest, Store, TurnError, TurnPhase,
};
use serde_json::{json, Value};
use std::{
    path::PathBuf,
    sync::atomic::{AtomicU64, Ordering},
    time::{SystemTime, UNIX_EPOCH},
};
static NEXT: AtomicU64 = AtomicU64::new(0);
struct Temp(PathBuf);
impl Temp {
    fn new() -> Self {
        let root = std::env::temp_dir().join(format!(
            "locallore-android-archive-{}-{}-{}",
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&root).unwrap();
        Self(root)
    }
    fn path(&self, name: &str) -> PathBuf {
        self.0.join(name)
    }
    fn stage(&self, name: &str) -> PathBuf {
        let path = self.path(name);
        std::fs::create_dir(&path).unwrap();
        path
    }
}
impl Drop for Temp {
    fn drop(&mut self) {
        std::fs::remove_dir_all(&self.0).unwrap();
    }
}
fn seed(story: &str) -> Seed {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    seed.scope.story = story.into();
    seed
}
fn create(path: &std::path::Path, story: &str) -> Scope {
    let mut store = Store::open(path, None).unwrap();
    let seed = seed(story);
    let scope = seed.scope.clone();
    store
        .create_story("SYNTHETIC <script>archive title</script>", seed)
        .unwrap();
    scope
}
fn apply(store: &mut Store, scope: &Scope, turn: &str, commands: Vec<Command>) -> Receipt {
    let engine = store.resume(scope).unwrap().engine;
    let request = engine.request(turn, Intent::Actions(commands));
    let proposal = Engine::proposal(&request).unwrap();
    let preview = engine.preview(&request, &proposal).unwrap();
    store.begin_turn(&request).unwrap();
    store
        .commit_turn(&request, &proposal, preview.narration())
        .unwrap()
}
fn decode(bytes: Vec<u8>) -> Value {
    assert!(bytes.len() <= 16 * 1024);
    serde_json::from_slice(&bytes).unwrap()
}
fn data(bytes: Vec<u8>) -> Value {
    let reply = decode(bytes);
    assert_eq!(reply["status"], "ok", "unexpected fixed archive status");
    reply["data"].clone()
}
fn export_request(scope: &Scope, head: u64) -> Vec<u8> {
    serde_json::to_vec(&json!({"story":scope.story,"branch":scope.branch,"expected_revision":head}))
        .unwrap()
}

#[test]
fn adapter_roundtrip_preserves_original_branches_witnesses_receipts_and_continuation() {
    let temp = Temp::new();
    let source_path = temp.path("source.sqlite3");
    let target_path = temp.path("target.sqlite3");
    let root = create(&source_path, "archive-source");
    let retained = create(&target_path, "retained-story");
    let mut source = Store::open(&source_path, None).unwrap();
    apply(
        &mut source,
        &root,
        "shared-prefix",
        vec![Command::Wait { ticks: 1 }],
    );
    let child = source
        .fork_branch(
            &ForkRequest {
                parent: root.clone(),
                child_branch: "child".into(),
                expected_parent_revision: 1,
                at_revision: 1,
            },
            &|| false,
        )
        .unwrap()
        .scope;
    let gift = apply(
        &mut source,
        &root,
        "same-turn-key",
        vec![Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 1,
        }],
    );
    apply(
        &mut source,
        &child,
        "same-turn-key",
        vec![Command::Consume {
            item: "potion".into(),
        }],
    );
    let sibling = source
        .fork_branch(
            &ForkRequest {
                parent: root.clone(),
                child_branch: "sibling".into(),
                expected_parent_revision: 2,
                at_revision: 1,
            },
            &|| false,
        )
        .unwrap()
        .scope;
    apply(
        &mut source,
        &sibling,
        "sibling-private",
        vec![Command::Say {
            text: "SYNTHETIC SIBLING CANARY".into(),
            audience: ["mira".into()].into(),
        }],
    );
    let draft = source.resume(&root).unwrap().engine.request(
        "uncommitted-input",
        Intent::Actions(vec![Command::Wait { ticks: 1 }]),
    );
    source.begin_turn(&draft).unwrap();
    let originals: Vec<_> = [root.clone(), child.clone(), sibling.clone()]
        .into_iter()
        .map(|scope| {
            let engine = source.resume(&scope).unwrap().engine;
            (scope, engine)
        })
        .collect();
    drop(source);
    let mut target = Store::open(&target_path, None).unwrap();
    apply(
        &mut target,
        &retained,
        "retained",
        vec![Command::Wait { ticks: 2 }],
    );
    let retained_before = target.resume(&retained).unwrap().engine.canonical_bytes();
    drop(target);
    let registry = ArchiveRegistry::default();
    let source_stage = temp.stage("source-stage");
    let target_stage = temp.stage("target-stage");
    let source_owner = registry.open(&source_path, &source_stage).unwrap();
    let target_owner = registry.open(&target_path, &target_stage).unwrap();
    let prepared = data(registry.prepare_export(source_owner, &export_request(&child, 2)));
    assert_eq!(
        prepared["preview"]["branch_heads"]
            .as_object()
            .unwrap()
            .len(),
        3
    );
    assert_eq!(prepared["preview"]["committed_turns"], 4);
    assert_eq!(
        prepared["preview"]["noncommitted_workflow_transferred"],
        false
    );
    assert!(prepared["preview"]["privacy_warning"]
        .as_str()
        .unwrap()
        .contains("hidden seed facts"));
    let token = prepared["token"].as_u64().unwrap();
    let bytes = registry.export_bytes(source_owner, token).unwrap();
    assert_eq!(
        registry.export_bytes(source_owner, token).unwrap_err(),
        "InvalidToken"
    );
    assert!(std::str::from_utf8(&bytes)
        .unwrap()
        .contains("SECRET-TIDE-731")); // Full private archive, not a player share.
    assert!(std::str::from_utf8(&bytes)
        .unwrap()
        .contains("SYNTHETIC SIBLING CANARY"));
    let validated = validate_archive(&bytes, &|| false).unwrap();
    assert_eq!(
        validated.preview().payload_sha256,
        prepared["preview"]["payload_sha256"].as_str().unwrap()
    );
    let imported = data(registry.prepare_import(target_owner, &bytes));
    assert_eq!(std::fs::read_dir(&target_stage).unwrap().count(), 0);
    let mut target = Store::open(&target_path, None).unwrap();
    assert_eq!(target.stories().unwrap().len(), 1);
    drop(target);
    let outcome = data(registry.commit_import(target_owner, imported["token"].as_u64().unwrap()));
    assert_eq!(
        outcome,
        json!({"root":root,"branches":3,"committed_turns":4})
    );
    assert_eq!(std::fs::read_dir(&target_stage).unwrap().count(), 0);
    registry.close(source_owner);
    registry.close(target_owner);
    let mut target = Store::open(&target_path, None).unwrap();
    assert_eq!(target.stories().unwrap().len(), 2);
    assert_eq!(
        target.resume(&retained).unwrap().engine.canonical_bytes(),
        retained_before
    );
    for (scope, original) in &originals {
        let restored = target.resume(scope).unwrap().engine;
        assert_eq!(restored.canonical_bytes(), original.canonical_bytes());
        let player = restored
            .character_context("player", scope, restored.revision())
            .unwrap();
        if scope == &child {
            assert!(!serde_json::to_string(&player)
                .unwrap()
                .contains("SYNTHETIC SIBLING CANARY"));
        }
        let oren = restored
            .character_context("oren", scope, restored.revision())
            .unwrap();
        assert!(!oren
            .observations
            .iter()
            .any(|event| serde_json::to_value(event).unwrap()["turn"] == "same-turn-key"));
    }
    assert!(matches!(
        target.turn_status(&draft),
        Err(TurnError::UnknownTurn)
    ));
    assert_eq!(
        target.begin_turn(gift.request()).unwrap().phase,
        TurnPhase::Committed
    );
    assert_eq!(
        target
            .commit_turn(gift.request(), gift.proposal(), gift.narration())
            .unwrap(),
        gift
    );
    apply(
        &mut target,
        &child,
        "continued-child",
        vec![Command::Wait { ticks: 2 }],
    );
    drop(target);
    let mut target = Store::open(&target_path, None).unwrap();
    assert_eq!(target.resume(&child).unwrap().engine.revision(), 3);
    assert_eq!(
        target.resume(&root).unwrap().engine.canonical_bytes(),
        originals[0].1.canonical_bytes()
    );
    assert_eq!(
        target.resume(&retained).unwrap().engine.canonical_bytes(),
        retained_before
    );
}

#[test]
fn selected_branch_head_guard_and_captured_bytes_are_not_recomputed_from_later_canon() {
    let temp = Temp::new();
    let path = temp.path("source.sqlite3");
    let scope = create(&path, "snapshot-story");
    let mut store = Store::open(&path, None).unwrap();
    apply(
        &mut store,
        &scope,
        "first",
        vec![Command::Wait { ticks: 1 }],
    );
    drop(store);
    let registry = ArchiveRegistry::default();
    let stage = temp.stage("stage");
    let owner = registry.open(&path, &stage).unwrap();
    let stale = decode(registry.prepare_export(owner, &export_request(&scope, 0)));
    assert_eq!(stale["error"], "Stale");
    let foreign = Scope {
        branch: "not-a-branch".into(),
        ..scope.clone()
    };
    assert_eq!(
        decode(registry.prepare_export(owner, &export_request(&foreign, 1)))["error"],
        "Stale"
    );
    let captured = data(registry.prepare_export(owner, &export_request(&scope, 1)));
    let mut store = Store::open(&path, None).unwrap();
    apply(
        &mut store,
        &scope,
        "later",
        vec![Command::Wait { ticks: 1 }],
    );
    drop(store);
    let bytes = registry
        .export_bytes(owner, captured["token"].as_u64().unwrap())
        .unwrap();
    assert_eq!(
        validate_archive(&bytes, &|| false)
            .unwrap()
            .preview()
            .branch_heads[&scope.branch],
        1
    );
    assert_eq!(
        decode(registry.prepare_export(owner, &export_request(&scope, 1)))["error"],
        "Stale"
    );
    assert_eq!(
        data(registry.prepare_export(owner, &export_request(&scope, 2)))["preview"]["branch_heads"]
            [&scope.branch],
        2
    );
    registry.cancel(owner);
    registry.close(owner);
    assert_eq!(std::fs::read_dir(stage).unwrap().count(), 0);
}

#[test]
fn corrupt_future_and_oversized_archives_never_change_existing_canonical_history() {
    let temp = Temp::new();
    let source_path = temp.path("source.sqlite3");
    let target_path = temp.path("target.sqlite3");
    let source = create(&source_path, "import-source");
    let retained = create(&target_path, "retained");
    let mut store = Store::open(&source_path, None).unwrap();
    let bytes = store
        .export_archive(&source.story, &|| false)
        .unwrap()
        .bytes()
        .to_vec();
    drop(store);
    let registry = ArchiveRegistry::default();
    let stage = temp.stage("stage");
    let owner = registry.open(&target_path, &stage).unwrap();
    let before = Store::open(&target_path, None)
        .unwrap()
        .resume(&retained)
        .unwrap()
        .engine
        .canonical_bytes();
    let mut corrupt: Value = serde_json::from_slice(&bytes).unwrap();
    corrupt["integrity"]["payload_sha256"] = json!("0".repeat(64));
    let mut future: Value = serde_json::from_slice(&bytes).unwrap();
    future["version"] = json!(999);
    for (payload, expected) in [
        (serde_json::to_vec(&corrupt).unwrap(), "Integrity"),
        (serde_json::to_vec(&future).unwrap(), "Unsupported"),
        (b"{PRIVATE_CANARY".to_vec(), "Malformed"),
        (vec![0xff], "Malformed"),
        (vec![b' '; MAX_ARCHIVE_BYTES + 1], "TooLarge"),
    ] {
        let error = decode(registry.prepare_import(owner, &payload));
        assert_eq!(error["error"], expected);
        assert!(!serde_json::to_string(&error)
            .unwrap()
            .contains("PRIVATE_CANARY"));
        let mut target = Store::open(&target_path, None).unwrap();
        assert_eq!(target.stories().unwrap().len(), 1);
        assert_eq!(
            target.resume(&retained).unwrap().engine.canonical_bytes(),
            before
        );
        assert_eq!(std::fs::read_dir(&stage).unwrap().count(), 0);
    }
    registry.close(owner);
}
