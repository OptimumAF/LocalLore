// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Actual Android registry/Host/Store parity without JNI/device/model execution.
use locallore::contracts::Scope;
use locallore_android::workspace::WorkspaceRegistry;
use locallore_storage::Store;
use serde_json::{json, Value};
use std::{
    path::PathBuf,
    sync::atomic::{AtomicU64, Ordering},
};
static NEXT: AtomicU64 = AtomicU64::new(0);
struct Fixture {
    directory: PathBuf,
    parent: PathBuf,
    registry: WorkspaceRegistry,
    handle: u64,
    session: String,
    scope: Scope,
}
fn decode(bytes: Vec<u8>) -> Value {
    assert!(bytes.len() <= 4096);
    serde_json::from_slice(&bytes).unwrap()
}
fn call(registry: &WorkspaceRegistry, handle: u64, command: Value) -> Value {
    serde_json::from_slice(&registry.call(
        handle,
        &serde_json::to_vec(&json!({"version":1,"command":command})).unwrap(),
    ))
    .unwrap()
}
impl Fixture {
    fn new() -> Self {
        let parent = std::env::temp_dir().canonicalize().unwrap();
        let directory = parent.join(format!(
            "locallore-android-fork-{}-{}-{}",
            std::process::id(),
            NEXT.fetch_add(1, Ordering::SeqCst),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        std::fs::create_dir(&directory).unwrap();
        let registry = WorkspaceRegistry::default();
        let handle = registry.open(&directory.join("stories.sqlite3")).unwrap();
        let created = call(
            &registry,
            handle,
            json!({"op":"create","seed":"lantern-quay-v1"}),
        );
        assert_eq!(created["status"], "ok", "{created}");
        Self {
            directory,
            parent,
            registry,
            handle,
            session: created["data"]["session"].as_str().unwrap().into(),
            scope: serde_json::from_value(created["data"]["scope"].clone()).unwrap(),
        }
    }
    fn input(&self, child: &str, expected: u64, at: u64) -> Value {
        json!({"parent":self.scope,"child_branch":child,"expected_parent_revision":expected,"at_revision":at})
    }
    fn register(&self, input: &Value) -> Value {
        decode(
            self.registry.fork_register(
                self.handle,
                &serde_json::to_vec(&json!({"version":1,"session":self.session,"input":input}))
                    .unwrap(),
                true,
            ),
        )
    }
    fn registered(&self, input: &Value) -> u64 {
        let result = self.register(input);
        assert_eq!(result["status"], "ok", "{result}");
        result["data"]["operation"].as_u64().unwrap()
    }
    fn lookup(&self, input: &Value) -> Value {
        decode(
            self.registry
                .fork_lookup(self.handle, &serde_json::to_vec(input).unwrap()),
        )
    }
    fn store(&self) -> Store {
        Store::open_application(&self.directory.join("stories.sqlite3")).unwrap()
    }
    fn commit(&self, session: &str, scope: &Scope, turn: &str, head: u64, commands: Value) {
        let result = call(
            &self.registry,
            self.handle,
            json!({"op":"submit","session":session,"mode":"accepted","request":
            {"version":1,"scope":scope,"turn":turn,"expected_revision":head,"intent":{"kind":"actions","value":commands}}}),
        );
        assert_eq!(result["data"]["phase"], "queued", "{result}");
        for (op, phase) in [("prepare", "ready"), ("commit", "committed")] {
            let result = call(
                &self.registry,
                self.handle,
                json!({"op":op,"session":session,"scope":scope,"turn":turn}),
            );
            assert_eq!(result["data"]["phase"], phase, "{result}");
        }
    }
}
impl Drop for Fixture {
    fn drop(&mut self) {
        self.registry.close(self.handle);
        let actual = self.directory.canonicalize().unwrap();
        assert_eq!(actual, self.directory);
        assert_eq!(actual.parent(), Some(self.parent.as_path()));
        assert!(actual
            .file_name()
            .unwrap()
            .to_str()
            .unwrap()
            .starts_with("locallore-android-fork-"));
        std::fs::remove_dir_all(actual).unwrap();
    }
}
#[test]
fn closed_wire_consent_ids_integer_bounds_and_duplicate_keys_cannot_dispatch() {
    let f = Fixture::new();
    let input = f.input("child", 0, 0);
    let valid =
        serde_json::to_vec(&json!({"version":1,"session":f.session,"input":input})).unwrap();
    assert_eq!(
        decode(f.registry.fork_register(f.handle, &valid, false))["error"],
        "ForkConsentRequired"
    );
    for mutation in [
        json!({"author":true}),
        json!({"parent":{"story":f.scope.story,"branch":f.scope.branch},"child_branch":"../child","expected_parent_revision":0,"at_revision":0}),
        json!({"parent":f.scope,"child_branch":"child","expected_parent_revision":9007199254740992u64,"at_revision":0}),
        json!({"parent":f.scope,"child_branch":"child","expected_parent_revision":0,"at_revision":1}),
        json!({"parent":f.scope,"child_branch":"child","expected_parent_revision":0.0,"at_revision":0}),
    ] {
        let bytes =
            serde_json::to_vec(&json!({"version":1,"session":f.session,"input":mutation})).unwrap();
        assert_eq!(
            decode(f.registry.fork_register(f.handle, &bytes, true))["error"],
            "InvalidForkInput"
        );
    }
    let duplicate = String::from_utf8(valid.clone()).unwrap().replacen(
        r#""version":1"#,
        r#""version":1,"version":1"#,
        1,
    );
    assert_eq!(
        decode(
            f.registry
                .fork_register(f.handle, duplicate.as_bytes(), true)
        )["error"],
        "InvalidForkInput"
    );
    assert_eq!(
        decode(f.registry.fork_register(f.handle, &vec![b' '; 4097], true))["error"],
        "TooLarge"
    );
    assert_eq!(f.lookup(&input)["data"]["found"], false);
    let injected = call(
        &f.registry,
        f.handle,
        json!({"op":"fork_branch","input":input}),
    );
    assert_ne!(injected["status"], "ok");
    assert_eq!(
        f.store()
            .branch_catalog(&f.scope.story, &|| false)
            .unwrap()
            .branches
            .len(),
        1
    );
}
#[test]
fn pending_registration_is_immutable_idempotent_and_operation_cannot_cross_owners() {
    let f = Fixture::new();
    let input = f.input("child", 0, 0);
    let operation = f.registered(&input);
    for _ in 0..16 {
        assert_eq!(f.registered(&input), operation);
    }
    assert_eq!(f.register(&f.input("different", 0, 0))["error"], "Busy");
    let other = Fixture::new();
    let foreign = other.registered(&other.input("other-child", 0, 0));
    assert_ne!(foreign, operation);
    assert_eq!(
        decode(other.registry.fork_run(other.handle, operation))["error"],
        "InvalidToken"
    );
    assert_eq!(
        decode(f.registry.fork_run(f.handle, foreign))["error"],
        "InvalidToken"
    );
    assert_eq!(f.lookup(&input)["data"]["found"], false);
}
#[test]
fn committed_result_wins_late_cancel_and_terminal_run_never_reexecutes() {
    let f = Fixture::new();
    let input = f.input("child", 0, 0);
    let operation = f.registered(&input);
    let result = decode(f.registry.fork_run(f.handle, operation));
    assert_eq!(result["data"]["phase"], "completed", "{result}");
    assert_eq!(result["data"]["result"]["outcome"]["created"], true);
    let cancel = decode(f.registry.fork_cancel(f.handle, operation));
    assert_eq!(cancel["data"]["phase"], "completed");
    assert_eq!(cancel["data"]["result"], result["data"]["result"]);
    let again = decode(f.registry.fork_run(f.handle, operation));
    assert_eq!(again["data"]["result"], result["data"]["result"]);
    // Even a later cancelled exact retry cannot promise that the original child is absent.
    let retry = f.registered(&input);
    assert_ne!(retry, operation);
    f.registry.fork_cancel(f.handle, retry);
    let rejected = decode(f.registry.fork_run(f.handle, retry));
    assert_eq!(rejected["data"]["error"], "Cancelled");
    assert_eq!(f.lookup(&input)["data"]["found"], true);
    assert_eq!(
        f.store()
            .branch_catalog(&f.scope.story, &|| false)
            .unwrap()
            .branches
            .len(),
        2
    );
}
#[test]
fn precancel_and_close_revoke_before_worker_and_reopened_lookup_never_creates() {
    let f = Fixture::new();
    let input = f.input("child", 0, 0);
    let operation = f.registered(&input);
    f.registry.fork_cancel(f.handle, operation);
    assert_eq!(
        decode(f.registry.fork_run(f.handle, operation))["data"]["error"],
        "Cancelled"
    );
    assert_eq!(f.lookup(&input)["data"]["found"], false);
    f.registry.close(f.handle);
    assert_eq!(
        decode(f.registry.fork_run(f.handle, operation))["error"],
        "InvalidToken"
    );
    let reopened = WorkspaceRegistry::default();
    let handle = reopened.open(&f.directory.join("stories.sqlite3")).unwrap();
    let before = f.store().branch_catalog(&f.scope.story, &|| false).unwrap();
    let lookup = decode(reopened.fork_lookup(handle, &serde_json::to_vec(&input).unwrap()));
    assert_eq!(lookup["data"]["found"], false);
    assert_eq!(
        f.store().branch_catalog(&f.scope.story, &|| false).unwrap(),
        before
    );
    reopened.close(handle);
}
#[test]
fn discarded_ack_restart_and_parent_child_advancement_retry_the_original_identity() {
    let f = Fixture::new();
    f.commit(
        &f.session,
        &f.scope,
        "before-fork",
        0,
        json!([{"op":"wait","ticks":1}]),
    );
    let original = f.input("stable-child", 1, 0);
    let operation = f.registered(&original);
    let lost = decode(f.registry.fork_run(f.handle, operation));
    assert_eq!(lost["data"]["phase"], "completed");
    f.registry.close(f.handle);
    let handle = f
        .registry
        .open(&f.directory.join("stories.sqlite3"))
        .unwrap();
    let resumed = call(&f.registry, handle, json!({"op":"resume","scope":f.scope}));
    let session = resumed["data"]["session"].as_str().unwrap();
    let child = Scope {
        branch: "stable-child".into(),
        ..f.scope.clone()
    };
    // Use the public Store for actual external accepted continuations, not a copied engine.
    let mut store = f.store();
    for (scope, turn, text) in [
        (&f.scope, "parent-future", "PARENT-FUTURE-CANARY"),
        (&child, "child-local", "CHILD-LOCAL-CANARY"),
    ] {
        let engine = store.resume(scope).unwrap().engine;
        let request = engine.request(
            turn,
            locallore::contracts::Intent::Actions(vec![locallore::contracts::Command::Say {
                text: text.into(),
                audience: ["player".into()].into(),
            }]),
        );
        let proposal = locallore::engine::Engine::proposal(&request).unwrap();
        let receipt = engine.preview(&request, &proposal).unwrap();
        store.begin_turn(&request).unwrap();
        store
            .commit_turn(&request, &proposal, receipt.narration())
            .unwrap();
    }
    let lookup = decode(
        f.registry
            .fork_lookup(handle, &serde_json::to_vec(&original).unwrap()),
    );
    assert_eq!(lookup["data"]["outcome"]["head_revision"], 1);
    let request =
        serde_json::to_vec(&json!({"version":1,"session":session,"input":original})).unwrap();
    let retry = decode(f.registry.fork_register(handle, &request, true))["data"]["operation"]
        .as_u64()
        .unwrap();
    let outcome = decode(f.registry.fork_run(handle, retry));
    assert_eq!(
        outcome["data"]["result"]["outcome"]["created"], false,
        "{outcome}"
    );
    assert_eq!(outcome["data"]["result"]["outcome"]["head_revision"], 1);
    let child_engine = store.resume(&child).unwrap().engine;
    let context =
        serde_json::to_string(&child_engine.character_context("player", &child, 1).unwrap())
            .unwrap();
    assert!(!context.contains("PARENT-FUTURE-CANARY"));
    assert!(context.contains("CHILD-LOCAL-CANARY"));
    assert_eq!(
        store
            .branch_catalog(&f.scope.story, &|| false)
            .unwrap()
            .branches
            .len(),
        2
    );
    let mismatch = f.input("stable-child", 1, 1);
    assert_eq!(
        decode(
            f.registry
                .fork_lookup(handle, &serde_json::to_vec(&mismatch).unwrap())
        )["error"],
        "Mismatch"
    );
    f.registry.close(handle);
}
#[test]
fn store_boundary_stale_and_parent_pending_refusals_leave_no_child() {
    let f = Fixture::new();
    f.commit(
        &f.session,
        &f.scope,
        "two-events",
        0,
        json!([{"op":"wait","ticks":1},{"op":"wait","ticks":1}]),
    );
    for (input, error) in [
        (f.input("mid-turn", 2, 1), "Rule"),
        (f.input("stale-child", 1, 0), "Stale"),
    ] {
        let operation = f.registered(&input);
        assert_eq!(
            decode(f.registry.fork_run(f.handle, operation))["data"]["error"],
            error
        );
        assert_eq!(f.lookup(&input)["data"]["found"], false);
    }
    let queued = call(
        &f.registry,
        f.handle,
        json!({"op":"submit","session":f.session,"mode":"accepted","request":
        {"version":1,"scope":f.scope,"turn":"pending","expected_revision":2,"intent":{"kind":"actions","value":[{"op":"wait","ticks":1}]}}}),
    );
    assert_eq!(queued["data"]["phase"], "queued");
    let input = f.input("busy-child", 2, 0);
    let operation = f.registered(&input);
    assert_eq!(
        decode(f.registry.fork_run(f.handle, operation))["data"]["error"],
        "Busy"
    );
    assert_eq!(f.lookup(&input)["data"]["found"], false);
}
#[test]
fn repeated_owner_retirement_cannot_fill_the_four_owner_operation_budget() {
    let f = Fixture::new();
    f.registry.close(f.handle);
    for _ in 0..12 {
        let handle = f
            .registry
            .open(&f.directory.join("stories.sqlite3"))
            .unwrap();
        let session = call(&f.registry, handle, json!({"op":"resume","scope":f.scope}))["data"]
            ["session"]
            .as_str()
            .unwrap()
            .to_owned();
        let input = f.input("never-run", 0, 0);
        let registered = decode(f.registry.fork_register(
            handle,
            &serde_json::to_vec(&json!({"version":1,"session":session,"input":input})).unwrap(),
            true,
        ));
        assert_eq!(registered["status"], "ok", "{registered}");
        f.registry.close(handle);
    }
    assert_eq!(
        f.store()
            .branch_catalog(&f.scope.story, &|| false)
            .unwrap()
            .branches
            .len(),
        1
    );
}

#[test]
fn accepted_parent_retirement_invalidates_registered_fork_but_preserves_retained_child() {
    let f = Fixture::new();
    let mut store = f.store();
    let parent = store
        .fork_branch(
            &locallore_storage::ForkRequest {
                parent: f.scope.clone(),
                child_branch: "retired-parent".into(),
                expected_parent_revision: 0,
                at_revision: 0,
            },
            &|| false,
        )
        .unwrap()
        .scope;
    let child = store
        .fork_branch(
            &locallore_storage::ForkRequest {
                parent: parent.clone(),
                child_branch: "retained-child".into(),
                expected_parent_revision: 0,
                at_revision: 0,
            },
            &|| false,
        )
        .unwrap()
        .scope;
    let parent_session = call(&f.registry, f.handle, json!({"op":"resume","scope":parent}))["data"]
        ["session"]
        .as_str()
        .unwrap()
        .to_owned();
    let request = json!({"parent":parent,"child_branch":"never-created","expected_parent_revision":0,"at_revision":0});
    let registered = decode(
        f.registry.fork_register(
            f.handle,
            &serde_json::to_vec(&json!({"version":1,"session":parent_session,"input":request}))
                .unwrap(),
            true,
        ),
    );
    let operation = registered["data"]["operation"].as_u64().unwrap();
    let before = store.resume(&child).unwrap().engine.canonical_bytes();
    f.registry
        .with_branch_deletion(&f.directory.join("stories.sqlite3"), &f.scope.story, || {
            let prepared = store
                .prepare_branch_deletion(&parent, 0, &|| false)
                .map_err(|_| "TestPrepare")?;
            let result = store
                .delete_branch(prepared, &|| false)
                .map_err(|_| "TestDelete")?;
            Ok(((), result.invalidated_branches))
        })
        .unwrap();
    let result = decode(f.registry.fork_run(f.handle, operation));
    assert_eq!(result["data"]["error"], "Closed", "{result}");
    assert_eq!(
        store.resume(&child).unwrap().engine.canonical_bytes(),
        before
    );
    assert_eq!(
        decode(
            f.registry
                .fork_lookup(f.handle, &serde_json::to_vec(&request).unwrap())
        )["data"]["found"],
        false
    );
}

#[test]
fn two_existing_workspace_owners_share_one_canonical_child_identity() {
    let f = Fixture::new();
    let input = f.input("shared-child", 0, 0);
    let first = f.registered(&input);
    let other = f
        .registry
        .open(&f.directory.join("stories.sqlite3"))
        .unwrap();
    let session = call(&f.registry, other, json!({"op":"resume","scope":f.scope}))["data"]
        ["session"]
        .as_str()
        .unwrap()
        .to_owned();
    let second = decode(f.registry.fork_register(
        other,
        &serde_json::to_vec(&json!({"version":1,"session":session,"input":input})).unwrap(),
        true,
    ))["data"]["operation"]
        .as_u64()
        .unwrap();
    assert_ne!(first, second);
    let (a, b) = std::thread::scope(|threads| {
        let a = threads.spawn(|| decode(f.registry.fork_run(f.handle, first)));
        let b = threads.spawn(|| decode(f.registry.fork_run(other, second)));
        (a.join().unwrap(), b.join().unwrap())
    });
    assert_eq!(a["data"]["phase"], "completed", "{a}");
    assert_eq!(b["data"]["phase"], "completed", "{b}");
    let created = [&a, &b]
        .iter()
        .filter(|reply| reply["data"]["result"]["outcome"]["created"] == true)
        .count();
    assert_eq!(created, 1);
    assert_eq!(
        f.store()
            .branch_catalog(&f.scope.story, &|| false)
            .unwrap()
            .branches
            .len(),
        2
    );
    assert_eq!(f.store().resume(&f.scope).unwrap().engine.revision(), 0);
    f.registry.close(other);
}
