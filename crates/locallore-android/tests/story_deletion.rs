// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Real Store/Host owners and public deletion capabilities; no JNI/device/model claim.
use locallore::{contracts::*, engine::Engine};
use locallore_android::{archive::ArchiveRegistry, workspace::WorkspaceRegistry};
use locallore_storage::{ForkRequest, Store, TurnPhase};
use serde_json::{json, Value};
use std::{
    fs,
    path::{Path, PathBuf},
    sync::{
        atomic::{AtomicU64, Ordering},
        mpsc, Arc,
    },
    thread,
    time::{Duration, Instant, SystemTime, UNIX_EPOCH},
};

static NEXT: AtomicU64 = AtomicU64::new(0);
struct Temp(PathBuf);
impl Temp {
    fn new() -> Self {
        let parent = std::env::temp_dir().canonicalize().unwrap();
        let path = parent.join(format!(
            "locallore-native-delete-{}-{}-{}",
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        fs::create_dir(&path).unwrap();
        fs::write(path.join("owner-v1"), b"locallore-native-deletion-test-v1").unwrap();
        Self(path)
    }
    fn path(&self, name: &str) -> PathBuf {
        self.0.join(name)
    }
    fn stage(&self, name: &str) -> PathBuf {
        let path = self.path(name);
        fs::create_dir(&path).unwrap();
        path
    }
}
impl Drop for Temp {
    fn drop(&mut self) {
        // Delete only this create-new marked test directory, never a caller-selected tree.
        let parent = std::env::temp_dir().canonicalize().unwrap();
        assert_eq!(self.0.parent(), Some(parent.as_path()));
        assert_eq!(self.0.canonicalize().unwrap(), self.0);
        assert!(!fs::symlink_metadata(&self.0)
            .unwrap()
            .file_type()
            .is_symlink());
        assert_eq!(
            fs::read(self.path("owner-v1")).unwrap(),
            b"locallore-native-deletion-test-v1"
        );
        fs::remove_dir_all(&self.0).unwrap();
    }
}
fn create(database: &Path, story: &str) -> Scope {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    seed.scope.story = story.into();
    let scope = seed.scope.clone();
    Store::open(database, None)
        .unwrap()
        .create_story("Synthetic native deletion", seed)
        .unwrap();
    scope
}
fn apply(database: &Path, scope: &Scope, turn: &str) -> Receipt {
    let mut store = Store::open(database, None).unwrap();
    let engine = store.resume(scope).unwrap().engine;
    let request = engine.request(turn, Intent::Actions(vec![Command::Wait { ticks: 1 }]));
    let proposal = Engine::proposal(&request).unwrap();
    let preview = engine.preview(&request, &proposal).unwrap();
    store.begin_turn(&request).unwrap();
    store
        .commit_turn(&request, &proposal, preview.narration())
        .unwrap()
}
fn decode(bytes: Vec<u8>) -> Value {
    assert!(bytes.len() <= 262_144);
    serde_json::from_slice(&bytes).unwrap()
}
fn data(reply: Value) -> Value {
    assert_eq!(reply["version"], 1);
    assert_eq!(
        reply["status"], "ok",
        "fixed response category: {}",
        reply["error"]
    );
    reply["data"].clone()
}
fn rejected(reply: Value, category: &str) {
    assert_eq!(
        reply,
        json!({"version":1,"status":"rejected","error":category})
    );
}
fn call(registry: &WorkspaceRegistry, handle: u64, command: Value) -> Value {
    decode(registry.call(
        handle,
        &serde_json::to_vec(&json!({"version":1,"command":command})).unwrap(),
    ))
}
fn resume(registry: &WorkspaceRegistry, handle: u64, scope: &Scope) -> Value {
    data(call(registry, handle, json!({"op":"resume","scope":scope})))
}
fn scoped(session: &Value, op: &str, turn: &str) -> Value {
    json!({"op":op,"session":session["session"],"scope":session["scope"],"turn":turn})
}
fn request(scope: &Scope, key: &str, head: u64, command: Value) -> Value {
    json!({"version":1,"scope":scope,"turn":key,"expected_revision":head,"intent":{"kind":"actions","value":[command]}})
}
fn submit(registry: &WorkspaceRegistry, handle: u64, session: &Value, request: &Value) -> Value {
    call(
        registry,
        handle,
        json!({"op":"submit","session":session["session"],"request":request,"mode":"accepted"}),
    )
}
fn ready(registry: &WorkspaceRegistry, handle: u64, session: &Value, request: &Value) {
    assert_eq!(
        data(submit(registry, handle, session, request))["phase"],
        "queued"
    );
    assert_eq!(
        data(call(
            registry,
            handle,
            scoped(session, "prepare", request["turn"].as_str().unwrap())
        ))["phase"],
        "ready"
    );
}
fn snapshot(registry: &WorkspaceRegistry, handle: u64, session: &Value, head: u64) -> Value {
    data(call(
        registry,
        handle,
        json!({"op":"play_snapshot","session":session["session"],"scope":session["scope"],"expected_revision":head}),
    ))
}
fn control(scope: &Scope, head: u64) -> Vec<u8> {
    serde_json::to_vec(&json!({"story":scope.story,"branch":scope.branch,"expected_revision":head}))
        .unwrap()
}
fn deletion(registry: &ArchiveRegistry, handle: u64, scope: &Scope, head: u64) -> Value {
    data(decode(
        registry.prepare_delete(handle, &control(scope, head)),
    ))
}
fn export(registry: &ArchiveRegistry, handle: u64, scope: &Scope, head: u64) -> Vec<u8> {
    let prepared = data(decode(
        registry.prepare_export(handle, &control(scope, head)),
    ));
    registry
        .export_bytes(handle, prepared["token"].as_u64().unwrap())
        .unwrap()
}
fn import(registry: &ArchiveRegistry, handle: u64, bytes: &[u8]) {
    let prepared = data(decode(registry.prepare_import(handle, bytes)));
    data(decode(
        registry.commit_import(handle, prepared["token"].as_u64().unwrap()),
    ));
}

#[test]
fn deletion_invalidates_cross_owner_root_child_and_cached_receipts_even_after_identical_reimport() {
    let temp = Temp::new();
    let database = temp.path("stories.sqlite3");
    let root = create(&database, "delete-original");
    let retained = create(&database, "retained-original");
    let prefix = apply(&database, &root, "committed-prefix");
    let child = Store::open(&database, None)
        .unwrap()
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
    let other_database = temp.path("other.sqlite3");
    let same_id_elsewhere = create(&other_database, &root.story);
    let workspaces = WorkspaceRegistry::default();
    let archives = ArchiveRegistry::default();
    let first = workspaces.open(&database).unwrap();
    let second = workspaces.open(&database).unwrap();
    let elsewhere = workspaces.open(&other_database).unwrap();
    let root_session = resume(&workspaces, first, &root);
    let child_session = resume(&workspaces, second, &child);
    let retained_session = resume(&workspaces, first, &retained);
    let elsewhere_session = resume(&workspaces, elsewhere, &same_id_elsewhere);
    let retained_before = snapshot(&workspaces, first, &retained_session, 0);
    let elsewhere_before = snapshot(&workspaces, elsewhere, &elsewhere_session, 0);
    assert_eq!(
        data(call(
            &workspaces,
            first,
            scoped(&root_session, "turn_status", "committed-prefix")
        ))["phase"],
        "committed"
    );
    let root_request = request(
        &root,
        "reused-ready-key",
        1,
        json!({"op":"give","item":"potion","to":"mira","quantity":1}),
    );
    let child_request = request(
        &child,
        "reused-ready-key",
        1,
        json!({"op":"consume","item":"potion"}),
    );
    ready(&workspaces, first, &root_session, &root_request);
    ready(&workspaces, second, &child_session, &child_request);
    let stage = temp.stage("stage");
    let owner = archives.open(&database, &stage).unwrap();
    let original = export(&archives, owner, &root, 1);
    rejected(
        decode(archives.prepare_delete(owner, &control(&child, 1))),
        "Malformed",
    ); // Whole-story confirmation is rooted at the catalog's original root timeline.
    let prepared = deletion(&archives, owner, &root, 1);
    assert_eq!(
        prepared["preview"]["branch_heads"],
        json!({"main":1,"child":1})
    );
    assert_eq!(prepared["preview"]["committed_turns"], 1);
    assert_eq!(prepared["preview"]["draft_turns"], 2);
    assert_eq!(
        data(decode(archives.commit_delete(
            owner,
            prepared["token"].as_u64().unwrap(),
            &workspaces
        ))),
        json!({"story_id":root.story,"deleted_branches":2,"deleted_turns":3})
    );
    assert!(Store::open(&database, None)
        .unwrap()
        .stories()
        .unwrap()
        .iter()
        .all(|story| story.scope.story != root.story));
    rejected(
        call(
            &workspaces,
            first,
            scoped(&root_session, "commit", "reused-ready-key"),
        ),
        "Closed",
    );
    for (handle, session) in [(first, &root_session), (second, &child_session)] {
        for operation in ["prepare", "commit"] {
            rejected(
                call(
                    &workspaces,
                    handle,
                    scoped(session, operation, "reused-ready-key"),
                ),
                "Closed",
            );
        }
    }
    rejected(
        call(
            &workspaces,
            second,
            scoped(&child_session, "prepare", "reused-ready-key"),
        ),
        "Closed",
    );
    import(&archives, owner, &original);
    assert_eq!(export(&archives, owner, &root, 1), original);
    let fresh = workspaces.open(&database).unwrap();
    let fresh_root = resume(&workspaces, fresh, &root);
    let fresh_child = resume(&workspaces, fresh, &child);
    assert_eq!(
        data(submit(&workspaces, fresh, &fresh_root, &root_request))["phase"],
        "queued"
    );
    assert_eq!(
        data(submit(&workspaces, fresh, &fresh_child, &child_request))["phase"],
        "queued"
    );
    rejected(
        call(
            &workspaces,
            first,
            scoped(&root_session, "commit", "reused-ready-key"),
        ),
        "Closed",
    );
    rejected(
        call(
            &workspaces,
            second,
            scoped(&child_session, "prepare", "reused-ready-key"),
        ),
        "Closed",
    );
    rejected(
        submit(
            &workspaces,
            first,
            &root_session,
            &serde_json::to_value(prefix.request()).unwrap(),
        ),
        "Closed",
    );
    rejected(
        call(
            &workspaces,
            first,
            scoped(&root_session, "commit", "committed-prefix"),
        ),
        "Closed",
    );
    let mut store = Store::open(&database, None).unwrap();
    for request in [&root_request, &child_request] {
        let request: Request = serde_json::from_value(request.clone()).unwrap();
        assert_eq!(store.turn_status(&request).unwrap().phase, TurnPhase::Draft);
    }
    drop(store);
    assert_eq!(snapshot(&workspaces, fresh, &fresh_root, 1)["revision"], 1);
    assert_eq!(snapshot(&workspaces, fresh, &fresh_child, 1)["revision"], 1);
    assert_eq!(
        snapshot(&workspaces, first, &retained_session, 0),
        retained_before
    );
    assert_eq!(
        snapshot(&workspaces, elsewhere, &elsewhere_session, 0),
        elsewhere_before
    );
    let retained_wait = request(
        &retained,
        "retained-still-works",
        0,
        json!({"op":"wait","ticks":1}),
    );
    ready(&workspaces, first, &retained_session, &retained_wait);
    assert_eq!(
        data(call(
            &workspaces,
            first,
            scoped(&retained_session, "commit", "retained-still-works")
        ))["phase"],
        "committed"
    );
    for (session, request) in [(&fresh_root, &root_request), (&fresh_child, &child_request)] {
        assert_eq!(
            data(call(
                &workspaces,
                fresh,
                scoped(session, "prepare", request["turn"].as_str().unwrap())
            ))["phase"],
            "ready"
        );
        assert_eq!(
            data(call(
                &workspaces,
                fresh,
                scoped(session, "commit", request["turn"].as_str().unwrap())
            ))["phase"],
            "committed"
        );
    }
    assert_eq!(
        snapshot(&workspaces, fresh, &fresh_root, 2)["receipts"]
            .as_array()
            .unwrap()
            .len(),
        2
    );
    assert_eq!(
        snapshot(&workspaces, fresh, &fresh_child, 2)["receipts"]
            .as_array()
            .unwrap()
            .len(),
        2
    );
    for handle in [first, second, elsewhere, fresh] {
        workspaces.close(handle);
    }
    archives.close(owner);
    assert_eq!(fs::read_dir(stage).unwrap().count(), 0);
}

#[test]
fn deletion_capabilities_are_owner_kind_single_use_and_cancellation_bound() {
    let temp = Temp::new();
    let database = temp.path("stories.sqlite3");
    let root = create(&database, "token-story");
    let archives = ArchiveRegistry::default();
    let workspaces = WorkspaceRegistry::default();
    let stage = temp.stage("stage");
    let first = archives.open(&database, &stage).unwrap();
    let second = archives.open(&database, &stage).unwrap();
    let original = export(&archives, first, &root, 0);
    let token = deletion(&archives, first, &root, 0)["token"]
        .as_u64()
        .unwrap();
    rejected(
        decode(archives.commit_delete(second, token, &workspaces)),
        "InvalidToken",
    );
    rejected(decode(archives.commit_import(first, token)), "InvalidToken");
    assert_eq!(
        archives.export_bytes(first, token).unwrap_err(),
        "InvalidToken"
    );
    // A rejected foreign/wrong-kind use must preserve the legitimate deletion grant.
    assert_eq!(
        data(decode(archives.commit_delete(first, token, &workspaces))),
        json!({"story_id":root.story,"deleted_branches":1,"deleted_turns":0})
    );
    rejected(
        decode(archives.commit_delete(first, token, &workspaces)),
        "InvalidToken",
    );
    import(&archives, first, &original);
    let token = deletion(&archives, first, &root, 0)["token"]
        .as_u64()
        .unwrap();
    archives.cancel(first);
    rejected(
        decode(archives.commit_delete(first, token, &workspaces)),
        "InvalidToken",
    );
    let replaced = deletion(&archives, first, &root, 0)["token"]
        .as_u64()
        .unwrap();
    let exported = data(decode(archives.prepare_export(first, &control(&root, 0))))["token"]
        .as_u64()
        .unwrap();
    rejected(
        decode(archives.commit_delete(first, replaced, &workspaces)),
        "InvalidToken",
    );
    rejected(
        decode(archives.commit_delete(first, exported, &workspaces)),
        "InvalidToken",
    );
    assert!(!archives.export_bytes(first, exported).unwrap().is_empty());
    let stale = deletion(&archives, first, &root, 0)["token"]
        .as_u64()
        .unwrap();
    apply(&database, &root, "intervening-commit");
    rejected(
        decode(archives.commit_delete(first, stale, &workspaces)),
        "Stale",
    );
    rejected(
        decode(archives.commit_delete(first, stale, &workspaces)),
        "InvalidToken",
    );
    rejected(
        decode(archives.prepare_delete(first, &control(&root, 0))),
        "Stale",
    );
    let fresh = deletion(&archives, first, &root, 1)["token"]
        .as_u64()
        .unwrap();
    assert_eq!(
        data(decode(archives.commit_delete(first, fresh, &workspaces))),
        json!({"story_id":root.story,"deleted_branches":1,"deleted_turns":1})
    );
    rejected(
        decode(archives.commit_delete(first, fresh, &workspaces)),
        "InvalidToken",
    );
    rejected(
        decode(archives.prepare_delete(first, &control(&root, 1))),
        "NotFound",
    );
    archives.close(first);
    archives.close(second);
    rejected(
        decode(archives.prepare_delete(first, &control(&root, 1))),
        "InvalidHandle",
    );
    assert_eq!(fs::read_dir(stage).unwrap().count(), 0);
}

#[test]
fn failed_deletion_or_unrelated_intervening_commit_does_not_invalidate_live_sessions() {
    let temp = Temp::new();
    let database = temp.path("stories.sqlite3");
    let root = create(&database, "target-story");
    let other = create(&database, "other-story");
    let workspaces = WorkspaceRegistry::default();
    let handle = workspaces.open(&database).unwrap();
    let session = resume(&workspaces, handle, &root);
    let before = snapshot(&workspaces, handle, &session, 0);
    assert_eq!(
        workspaces.with_story_deletion(&database, &root.story, || Err::<(), _>("Busy")),
        Err("Busy")
    );
    assert_eq!(snapshot(&workspaces, handle, &session, 0), before);
    let archives = ArchiveRegistry::default();
    let stage = temp.stage("stage");
    let owner = archives.open(&database, &stage).unwrap();
    let token = deletion(&archives, owner, &root, 0)["token"]
        .as_u64()
        .unwrap();
    apply(&database, &other, "different-story-commit");
    rejected(
        decode(archives.commit_delete(owner, token, &workspaces)),
        "Stale",
    );
    assert_eq!(snapshot(&workspaces, handle, &session, 0), before);
    assert_eq!(
        Store::open(&database, None)
            .unwrap()
            .stories()
            .unwrap()
            .len(),
        2
    );
    archives.close(owner);
    workspaces.close(handle);
}

#[test]
fn identical_delete_reimport_is_stale_even_when_story_heads_and_archive_bytes_match() {
    let temp = Temp::new();
    let database = temp.path("stories.sqlite3");
    let root = create(&database, "aba-story");
    let archives = ArchiveRegistry::default();
    let workspaces = WorkspaceRegistry::default();
    let stage = temp.stage("stage");
    let first = archives.open(&database, &stage).unwrap();
    let second = archives.open(&database, &stage).unwrap();
    let original = export(&archives, first, &root, 0);
    let old = deletion(&archives, second, &root, 0)["token"]
        .as_u64()
        .unwrap();
    let current = deletion(&archives, first, &root, 0)["token"]
        .as_u64()
        .unwrap();
    data(decode(archives.commit_delete(first, current, &workspaces)));
    import(&archives, first, &original);
    assert_eq!(export(&archives, first, &root, 0), original);
    rejected(
        decode(archives.commit_delete(second, old, &workspaces)),
        "Stale",
    );
    rejected(
        decode(archives.commit_delete(second, old, &workspaces)),
        "InvalidToken",
    );
    assert_eq!(
        Store::open(&database, None)
            .unwrap()
            .stories()
            .unwrap()
            .len(),
        1
    );
    archives.close(first);
    archives.close(second);
}

#[test]
fn cancellation_and_close_while_waiting_for_public_workspace_gate_cannot_delete_or_free_live_owner_budget(
) {
    for close in [false, true] {
        let temp = Temp::new();
        let database = temp.path("stories.sqlite3");
        let root = create(&database, "gated-story");
        let workspaces = Arc::new(WorkspaceRegistry::default());
        let archives = Arc::new(ArchiveRegistry::default());
        let workspace = workspaces.open(&database).unwrap();
        let session = resume(&workspaces, workspace, &root);
        let before = snapshot(&workspaces, workspace, &session, 0);
        let stage = temp.stage("stage");
        let owner = archives.open(&database, &stage).unwrap();
        let token = deletion(&archives, owner, &root, 0)["token"]
            .as_u64()
            .unwrap();
        let (entered_tx, entered_rx) = mpsc::channel();
        let (release_tx, release_rx) = mpsc::channel();
        let gate_registry = workspaces.clone();
        let gate_database = database.clone();
        let gate = thread::spawn(move || {
            gate_registry.with_story_deletion(&gate_database, "unrelated-gate-only", || {
                entered_tx.send(()).map_err(|_| "Internal")?;
                release_rx
                    .recv_timeout(Duration::from_secs(5))
                    .map_err(|_| "Cancelled")?;
                Ok(())
            })
        });
        let entered = entered_rx.recv_timeout(Duration::from_secs(2)).is_ok();
        if !entered {
            let _ = release_tx.send(());
            let _ = gate.join();
            panic!("public workspace gate did not start");
        }
        let delete_registry = archives.clone();
        let delete_workspaces = workspaces.clone();
        let deleting =
            thread::spawn(move || delete_registry.commit_delete(owner, token, &delete_workspaces));
        let deadline = Instant::now() + Duration::from_secs(2);
        let mut busy = false;
        let mut valid_probe = true;
        while Instant::now() < deadline {
            match archives.export_bytes(owner, token) {
                Err(error) if error == "Busy" => {
                    busy = true;
                    break;
                }
                Err(error) if error == "InvalidToken" => {}
                _ => {
                    valid_probe = false;
                    break;
                }
            }
            thread::yield_now();
        }
        let control_registry = archives.clone();
        let (cancel_tx, cancel_rx) = mpsc::channel();
        let cancelling = thread::spawn(move || {
            if close {
                control_registry.close(owner);
            } else {
                control_registry.cancel(owner);
            }
            let _ = cancel_tx.send(());
        });
        let cancelled_while_held = cancel_rx.recv_timeout(Duration::from_secs(2)).is_ok();
        let mut replacements = Vec::new();
        let budget_held = if close && busy && cancelled_while_held {
            for _ in 0..3 {
                match archives.open(&database, &stage) {
                    Ok(handle) => replacements.push(handle),
                    Err(_) => break,
                }
            }
            match archives.open(&database, &stage) {
                Err(error) => replacements.len() == 3 && error == "WorkspaceLimit",
                Ok(handle) => {
                    replacements.push(handle);
                    false
                }
            }
        } else {
            true
        };
        let _ = release_tx.send(());
        let gate_result = gate.join();
        let cancel_result = cancelling.join();
        let delete_result = deleting.join();
        assert!(gate_result.unwrap().is_ok());
        cancel_result.unwrap();
        let reply = decode(delete_result.unwrap());
        assert!(
            valid_probe,
            "wrong-kind public probe changed deletion ownership"
        );
        assert!(busy, "actual deletion did not reach the held public gate");
        assert!(
            cancelled_while_held,
            "cancel/close waited for the deletion transaction gate"
        );
        assert!(
            budget_held,
            "closed but live deletion owner escaped the native ownership limit"
        );
        rejected(reply, "Cancelled");
        assert_eq!(snapshot(&workspaces, workspace, &session, 0), before);
        if close {
            replacements.push(archives.open(&database, &stage).unwrap());
            assert_eq!(replacements.len(), 4);
        } else {
            rejected(
                decode(archives.commit_delete(owner, token, &workspaces)),
                "InvalidToken",
            );
            archives.close(owner);
        }
        for handle in replacements {
            archives.close(handle);
        }
        workspaces.close(workspace);
        assert_eq!(fs::read_dir(stage).unwrap().count(), 0);
    }
}
