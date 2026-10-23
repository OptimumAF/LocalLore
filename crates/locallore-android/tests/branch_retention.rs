// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Actual Store/Host/native capability behavior on original synthetic histories.
use locallore::{contracts::*, engine::Engine};
use locallore_android::{archive::ArchiveRegistry, workspace::WorkspaceRegistry};
use locallore_storage::{ForkRequest, Store};
use serde_json::{json, Value};
use std::{
    path::PathBuf,
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT_FIXTURE: AtomicU64 = AtomicU64::new(0);

// This integration-test allocator is shared by the real fixture and its collision regression.
fn create_fixture_dir(timestamp: u128) -> std::io::Result<PathBuf> {
    let dir = std::env::temp_dir().join(format!(
        "locallore-native-retention-{}-{timestamp}-{}",
        std::process::id(),
        NEXT_FIXTURE.fetch_add(1, Ordering::Relaxed),
    ));
    std::fs::create_dir(&dir)?;
    Ok(dir)
}

#[test]
fn concurrent_fixtures_with_the_same_clock_value_have_distinct_directories() {
    let timestamp = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    let barrier = std::sync::Arc::new(std::sync::Barrier::new(8));
    let threads: Vec<_> = (0..8)
        .map(|_| {
            let barrier = barrier.clone();
            std::thread::spawn(move || {
                barrier.wait();
                create_fixture_dir(timestamp)
            })
        })
        .collect();
    let mut paths = std::collections::BTreeSet::new();
    let mut errors = Vec::new();
    for thread in threads {
        match thread.join().unwrap() {
            Ok(path) => {
                assert!(paths.insert(path));
            }
            Err(error) => errors.push(error.kind()),
        }
    }
    // Remove only directories successfully created by this test, even on the RED path.
    for path in &paths {
        std::fs::remove_dir(path).unwrap();
    }
    assert!(
        errors.is_empty(),
        "same-process allocator collisions: {errors:?}"
    );
    assert_eq!(paths.len(), 8);
}
struct Fixture {
    dir: PathBuf,
    database: PathBuf,
    root: Scope,
    parent: Scope,
    child: Scope,
    sibling: Scope,
}
impl Fixture {
    fn new() -> Self {
        let dir = create_fixture_dir(
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
        )
        .unwrap();
        let database = dir.join("workspace.sqlite3");
        let mut store = Store::open(&database, None).unwrap();
        let seed: Seed =
            serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
        let root = seed.scope.clone();
        store
            .create_story("Original retained native scene", seed)
            .unwrap();
        for i in 0..4 {
            wait(&mut store, &root, &format!("root-{i}"));
        }
        let parent = fork(&mut store, &root, "parent", 2);
        for i in 0..3 {
            wait(&mut store, &parent, &format!("parent-{i}"));
        }
        let child = fork(&mut store, &parent, "child", 4);
        let sibling = fork(&mut store, &root, "sibling", 1);
        drop(store);
        Self {
            dir,
            database,
            root,
            parent,
            child,
            sibling,
        }
    }
    fn control(&self) -> Vec<u8> {
        serde_json::to_vec(
            &json!({"story":self.parent.story,"branch":self.parent.branch,"expected_revision":5}),
        )
        .unwrap()
    }
    fn staging(&self) -> PathBuf {
        let p = self.dir.join("staging");
        std::fs::create_dir(&p).unwrap();
        p
    }
}
impl Drop for Fixture {
    fn drop(&mut self) {
        std::fs::remove_dir_all(&self.dir).unwrap();
    }
}
fn wait(s: &mut Store, scope: &Scope, key: &str) {
    let e = s.resume(scope).unwrap().engine;
    let q = e.request(key, Intent::Actions(vec![Command::Wait { ticks: 1 }]));
    let proposal = Engine::proposal(&q).unwrap();
    let expected = e.preview(&q, &proposal).unwrap();
    s.begin_turn(&q).unwrap();
    s.commit_turn(&q, &proposal, expected.narration()).unwrap();
}
fn fork(s: &mut Store, parent: &Scope, id: &str, at: u64) -> Scope {
    let head = s.resume(parent).unwrap().engine.revision();
    s.fork_branch(
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
fn reply(bytes: Vec<u8>) -> Value {
    serde_json::from_slice(&bytes).unwrap()
}
fn accepted(bytes: Vec<u8>) -> Value {
    let r = reply(bytes);
    assert_eq!(r["status"], "ok", "{r}");
    r["data"].clone()
}
fn call(r: &WorkspaceRegistry, h: u64, c: Value) -> Vec<u8> {
    r.call(
        h,
        &serde_json::to_vec(&json!({"version":1,"command":c})).unwrap(),
    )
}
fn session(r: &WorkspaceRegistry, h: u64, scope: &Scope) -> String {
    accepted(call(r, h, json!({"op":"resume","scope":scope})))["session"]
        .as_str()
        .unwrap()
        .into()
}
fn request(scope: &Scope, head: u64, key: &str) -> Value {
    json!({"version":1,"scope":scope,"turn":key,"expected_revision":head,"intent":{"kind":"actions","value":[{"op":"wait","ticks":1}]}})
}
fn ready(r: &WorkspaceRegistry, h: u64, id: &str, scope: &Scope, head: u64, key: &str) {
    accepted(call(
        r,
        h,
        json!({"op":"submit","session":id,"request":request(scope,head,key),"mode":"accepted"}),
    ));
    let p = accepted(call(
        r,
        h,
        json!({"op":"prepare","session":id,"scope":scope,"turn":key}),
    ));
    assert_eq!(p["phase"], "ready");
}
fn snapshot(r: &WorkspaceRegistry, h: u64, id: &str, scope: &Scope, head: u64) -> Value {
    accepted(call(
        r,
        h,
        json!({"op":"play_snapshot","session":id,"scope":scope,"expected_revision":head}),
    ))
}

#[test]
fn accepted_retirement_fences_only_target_across_owners_and_retained_child_ready_can_commit() {
    let f = Fixture::new();
    let work = WorkspaceRegistry::default();
    let archive = ArchiveRegistry::default();
    let a = work.open(&f.database).unwrap();
    let b = work.open(&f.database).unwrap();
    let grant = archive.open(&f.database, &f.staging()).unwrap();
    let pa = session(&work, a, &f.parent);
    let pb = session(&work, b, &f.parent);
    let child = session(&work, a, &f.child);
    let sibling = session(&work, b, &f.sibling);
    let child_before = snapshot(&work, a, &child, &f.child, 4);
    let sibling_before = snapshot(&work, b, &sibling, &f.sibling, 1);
    ready(&work, a, &pa, &f.parent, 5, "old-parent-ready");
    ready(&work, a, &child, &f.child, 4, "retained-child-ready");
    let prepared = accepted(archive.prepare_branch_delete(grant, &f.control()));
    assert_eq!(prepared["preview"]["retained_heads"]["parent"], 4);
    let result =
        accepted(archive.commit_branch_delete(grant, prepared["token"].as_u64().unwrap(), &work));
    assert_eq!(result["scope"], json!(f.parent));
    assert_eq!(result["invalidated_branches"], json!(["parent"]));
    for (h, id) in [(a, &pa), (b, &pb)] {
        for op in ["open", "prepare", "commit", "turn_status", "cancel"] {
            let mut command = json!({"op":op,"session":id,"scope":f.parent});
            if op != "open" {
                command["turn"] = json!("old-parent-ready");
            }
            let r = reply(call(&work, h, command));
            assert_eq!(r["error"], "Closed", "{op}: {r}");
        }
    }
    assert_eq!(
        reply(call(&work, a, json!({"op":"resume","scope":f.parent})))["error"],
        "NotFound"
    );
    assert_eq!(snapshot(&work, a, &child, &f.child, 4), child_before);
    assert_eq!(snapshot(&work, b, &sibling, &f.sibling, 1), sibling_before);
    let committed = accepted(call(
        &work,
        a,
        json!({"op":"commit","session":child,"scope":f.child,"turn":"retained-child-ready"}),
    ));
    assert_eq!(committed["phase"], "committed");
    assert_eq!(
        accepted(call(
            &work,
            a,
            json!({"op":"commit","session":child,"scope":f.child,"turn":"retained-child-ready"})
        )),
        committed
    );
    let cat = accepted(call(
        &work,
        a,
        json!({"op":"branches","story":f.root.story}),
    ));
    assert_eq!(cat["version"], 2);
    assert!(cat["branches"]
        .as_array()
        .unwrap()
        .iter()
        .any(|b| b["scope"]["branch"] == "parent" && b["retired"] == true));
    work.close(a);
    work.close(b);
    archive.close(grant);
    let mut slots = Vec::new();
    for _ in 0..4 {
        slots.push(work.open(&f.database).unwrap());
    }
    for h in slots {
        work.close(h);
    }
}
#[test]
fn external_store_retirement_cannot_return_cached_parent_ready_or_status() {
    let f = Fixture::new();
    let work = WorkspaceRegistry::default();
    let h = work.open(&f.database).unwrap();
    let parent = session(&work, h, &f.parent);
    let child = session(&work, h, &f.child);
    ready(&work, h, &parent, &f.parent, 5, "external-ready");
    let before = snapshot(&work, h, &child, &f.child, 4);
    let mut external = Store::open(&f.database, None).unwrap();
    let plan = external
        .prepare_branch_deletion(&f.parent, 5, &|| false)
        .unwrap();
    external.delete_branch(plan, &|| false).unwrap();
    let r = reply(call(
        &work,
        h,
        json!({"op":"prepare","session":parent,"scope":f.parent,"turn":"external-ready"}),
    ));
    assert_eq!(r["error"], "NotFound");
    assert_eq!(
        reply(call(
            &work,
            h,
            json!({"op":"turn_status","session":parent,"scope":f.parent,"turn":"external-ready"})
        ))["error"],
        "Closed"
    );
    assert_eq!(snapshot(&work, h, &child, &f.child, 4), before);
    drop(external);
    work.close(h);
}
#[test]
fn branch_consent_is_kind_owner_one_use_and_cancellation_bound() {
    let f = Fixture::new();
    let archive = ArchiveRegistry::default();
    let work = WorkspaceRegistry::default();
    let staging = f.staging();
    let a = archive.open(&f.database, &staging).unwrap();
    let b = archive.open(&f.database, &staging).unwrap();
    let p = accepted(archive.prepare_branch_delete(a, &f.control()));
    let token = p["token"].as_u64().unwrap();
    assert_eq!(
        reply(archive.commit_branch_delete(b, token, &work))["error"],
        "InvalidToken"
    );
    assert_eq!(
        reply(archive.commit_delete(a, token, &work))["error"],
        "InvalidToken"
    );
    archive.cancel(a);
    assert_eq!(
        reply(archive.commit_branch_delete(a, token, &work))["error"],
        "InvalidToken"
    );
    let p = accepted(archive.prepare_branch_delete(a, &f.control()));
    let token = p["token"].as_u64().unwrap();
    accepted(archive.commit_branch_delete(a, token, &work));
    assert_eq!(
        reply(archive.commit_branch_delete(a, token, &work))["error"],
        "InvalidToken"
    );
    archive.close(a);
    archive.close(b);
    let mut owners = Vec::new();
    for _ in 0..4 {
        owners.push(archive.open(&f.database, &staging).unwrap());
    }
    for h in owners {
        archive.close(h);
    }
}
