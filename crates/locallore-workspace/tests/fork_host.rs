// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Actual native Host/SQLite port; no app, model, SQL fixture writes or author grant.
use locallore::{
    contracts::*,
    host::{Host, WorkspaceForkRequest},
    inference::{Cancellation, GenerationRequest, InferenceProvider},
    inspection_query::{Observer, Query, View},
    play::PlayProfile,
};
use locallore_storage::Store;
use serde_json::{json, Value};
use std::{
    cell::Cell,
    path::PathBuf,
    sync::{
        atomic::{AtomicU64, Ordering},
        mpsc, Arc, Mutex,
    },
    task::Poll,
    time::Duration,
};

static NEXT: AtomicU64 = AtomicU64::new(0);
struct Temp(PathBuf);
impl Temp {
    fn new() -> Self {
        let path = std::env::temp_dir().join(format!(
            "locallore-fork-port-{}-{}-{}",
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
    fn host(&self) -> Host {
        locallore_workspace::open(&self.path(), false).unwrap()
    }
    fn engine(&self, scope: &Scope) -> locallore::engine::Engine {
        Store::open_read_only(&self.path())
            .unwrap()
            .resume(scope)
            .unwrap()
            .engine
    }
}
impl Drop for Temp {
    fn drop(&mut self) {
        std::fs::remove_dir_all(&self.0).unwrap();
    }
}
fn call(host: &Host, command: Value) -> Value {
    host.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
}
fn create(host: &Host) -> (String, Scope) {
    let v = call(host, json!({"op":"create","seed":"lantern-quay-v1"}));
    assert_eq!(v["status"], "ok", "{v}");
    (
        v["data"]["session"].as_str().unwrap().into(),
        serde_json::from_value(v["data"]["scope"].clone()).unwrap(),
    )
}
fn resume(host: &Host, scope: &Scope) -> String {
    let v = call(host, json!({"op":"resume","scope":scope}));
    assert_eq!(v["status"], "ok", "{v}");
    v["data"]["session"].as_str().unwrap().into()
}
fn op(host: &Host, session: &str, scope: &Scope, turn: &str, op: &str) -> Value {
    call(
        host,
        json!({"op":op,"session":session,"scope":scope,"turn":turn}),
    )
}
fn request(scope: &Scope, head: u64, turn: &str, commands: Vec<Command>) -> Request {
    Request {
        version: 1,
        scope: scope.clone(),
        turn: turn.into(),
        expected_revision: head,
        intent: Intent::Actions(commands),
    }
}
fn submit(host: &Host, session: &str, request: &Request) {
    let v = call(
        host,
        json!({"op":"submit","session":session,"request":request,"mode":"accepted"}),
    );
    assert_eq!(v["data"]["phase"], "queued", "{v}");
}
fn commit(host: &Host, session: &str, request: &Request) -> Value {
    submit(host, session, request);
    let v = op(host, session, &request.scope, &request.turn, "prepare");
    assert_eq!(v["data"]["phase"], "ready", "{v}");
    let v = op(host, session, &request.scope, &request.turn, "commit");
    assert_eq!(v["data"]["phase"], "committed", "{v}");
    v["data"]["receipt"].clone()
}
fn fork(parent: &Scope, child: &str, expected: u64, at: u64) -> WorkspaceForkRequest {
    WorkspaceForkRequest {
        parent: parent.clone(),
        child_branch: child.into(),
        expected_parent_revision: expected,
        at_revision: at,
    }
}
fn say(text: &str) -> Command {
    Command::Say {
        text: text.into(),
        audience: ["mira".into()].into(),
    }
}
fn catalog(host: &Host, scope: &Scope) -> Value {
    let v = call(host, json!({"op":"branches","story":scope.story}));
    assert_eq!(v["status"], "ok", "{v}");
    v["data"].clone()
}
fn full_query(scope: &Scope, head: u64, observer: Observer) -> Query {
    Query {
        version: 1,
        scope: scope.clone(),
        expected_head: head,
        at_revision: None,
        observer,
        view: View::History,
        cursor: None,
        limit: 64,
        search: String::new(),
    }
}

#[test]
fn completed_fork_preserves_original_scopes_and_excludes_future_and_sibling() {
    let temp = Temp::new();
    let host = temp.host();
    let (session, root) = create(&host);
    let inherited_wire = commit(
        &host,
        &session,
        &request(
            &root,
            0,
            "prefix",
            vec![say("shared-prefix"), Command::Wait { ticks: 1 }],
        ),
    );
    let inherited = temp.engine(&root).receipts()[0].clone();
    assert_eq!(serde_json::to_value(&inherited).unwrap(), inherited_wire);
    assert_eq!(inherited.events().len(), 2);
    let before = temp.engine(&root).canonical_bytes();
    let counts = host.live_counts();
    let child = host
        .fork_branch(&session, &fork(&root, "child", 2, 2), &|| false)
        .unwrap();
    assert_eq!(
        (
            child.version,
            child.fork_revision,
            child.head_revision,
            child.created
        ),
        (1, 2, 2, true)
    );
    assert_eq!(child.parent, root);
    assert_eq!(
        host.live_counts(),
        counts,
        "fork does not attach/select a child session"
    );
    assert_eq!(temp.engine(&root).canonical_bytes(), before);
    let sibling = host
        .fork_branch(&session, &fork(&root, "sibling", 2, 2), &|| false)
        .unwrap();
    commit(
        &host,
        &session,
        &request(&root, 2, "parent-future", vec![say("PARENT-FUTURE")]),
    );
    let sibling_session = resume(&host, &sibling.scope);
    commit(
        &host,
        &sibling_session,
        &request(
            &sibling.scope,
            2,
            "sibling-future",
            vec![say("SIBLING-FUTURE")],
        ),
    );
    let child_session = resume(&host, &child.scope);
    let child_receipt = commit(
        &host,
        &child_session,
        &request(&child.scope, 2, "child-only", vec![say("CHILD-PRESENT")]),
    );
    let engine = temp.engine(&child.scope);
    assert_eq!(engine.receipts().len(), 2);
    assert_eq!(engine.receipts()[0], inherited);
    assert_eq!(
        serde_json::to_value(&engine.receipts()[1]).unwrap(),
        child_receipt
    );
    assert_eq!(engine.receipts()[0].request().scope, root);
    assert!(engine.receipts()[0]
        .events()
        .iter()
        .all(|event| event.scope() == &root));
    let mira = engine.character_context("mira", &child.scope, 3).unwrap();
    let visible = serde_json::to_string(&mira).unwrap();
    assert!(visible.contains("shared-prefix") && visible.contains("CHILD-PRESENT"));
    assert!(!visible.contains("PARENT-FUTURE") && !visible.contains("SIBLING-FUTURE"));
    let sable = engine.character_context("sable", &child.scope, 3).unwrap();
    assert!(!serde_json::to_string(&sable)
        .unwrap()
        .contains("shared-prefix"));
    assert_eq!(
        host.inspection_query(
            &child_session,
            &full_query(&child.scope, 3, Observer::Character { id: "mira".into() })
        )
        .unwrap_err(),
        "Forbidden"
    );
    assert_eq!(
        host.inspection_query(
            &child_session,
            &full_query(&child.scope, 3, Observer::Omniscient)
        )
        .unwrap_err(),
        "Forbidden"
    );
    assert_eq!(
        call(&host, json!({"op":"capabilities"}))["data"]["author"],
        false
    );
    assert_eq!(
        call(&host, json!({"op":"open","session":session,"scope":root}))["data"]["revision"],
        3
    );
}

#[test]
fn cancel_during_transaction_rolls_back_and_pre_cancel_creates_no_child() {
    let temp = Temp::new();
    let host = temp.host();
    let (session, root) = create(&host);
    assert_eq!(
        host.fork_branch(&session, &fork(&root, "pre-cancel", 0, 0), &|| true)
            .unwrap_err(),
        "Cancelled"
    );
    let polls = Cell::new(0);
    let cancel = || {
        polls.set(polls.get() + 1);
        polls.get() == 3
    };
    assert_eq!(
        host.fork_branch(&session, &fork(&root, "transaction-cancel", 0, 0), &cancel)
            .unwrap_err(),
        "Cancelled"
    );
    assert_eq!(
        polls.get(),
        3,
        "Store cancellation after child insertion must roll back"
    );
    assert_eq!(
        catalog(&host, &root)["branches"].as_array().unwrap().len(),
        1
    );
    assert_eq!(temp.engine(&root).revision(), 0);
    assert!(
        host.fork_branch(&session, &fork(&root, "transaction-cancel", 0, 0), &|| {
            false
        })
        .unwrap()
        .created
    );
}

#[test]
fn stale_partial_boundary_and_child_identity_mismatch_remain_store_errors() {
    let temp = Temp::new();
    let host = temp.host();
    let (session, root) = create(&host);
    commit(
        &host,
        &session,
        &request(
            &root,
            0,
            "two",
            vec![Command::Wait { ticks: 1 }, Command::Wait { ticks: 1 }],
        ),
    );
    assert_eq!(
        host.fork_branch(&session, &fork(&root, "stale", 0, 2), &|| false)
            .unwrap_err(),
        "Stale"
    );
    assert_eq!(
        host.fork_branch(&session, &fork(&root, "partial", 2, 1), &|| false)
            .unwrap_err(),
        "Rule"
    );
    let child = host
        .fork_branch(&session, &fork(&root, "fixed", 2, 2), &|| false)
        .unwrap();
    assert_eq!(
        host.fork_branch(&session, &fork(&root, "fixed", 2, 0), &|| false)
            .unwrap_err(),
        "RetryMismatch"
    );
    let child_session = resume(&host, &child.scope);
    assert_eq!(
        host.fork_branch(&child_session, &fork(&child.scope, "fixed", 2, 2), &|| {
            false
        })
        .unwrap_err(),
        "Rule"
    );
    assert_eq!(
        catalog(&host, &root)["branches"].as_array().unwrap().len(),
        2
    );
}

#[test]
fn lost_ack_restart_retry_uses_fixed_identity_and_current_child_head() {
    let temp = Temp::new();
    let host = temp.host();
    let (session, root) = create(&host);
    commit(
        &host,
        &session,
        &request(
            &root,
            0,
            "prefix",
            vec![Command::Wait { ticks: 1 }, Command::Wait { ticks: 1 }],
        ),
    );
    let fixed = fork(&root, "fixed-recovery", 2, 2);
    // Real committed outcome is deliberately discarded, simulating lost acknowledgement.
    host.fork_branch(&session, &fixed, &|| false).unwrap();
    call(&host, json!({"op":"close","session":session,"scope":root}));
    drop(host);
    let host = temp.host();
    let session = resume(&host, &root);
    let child = Scope {
        story: root.story.clone(),
        branch: fixed.child_branch.clone(),
    };
    let child_session = resume(&host, &child);
    commit(
        &host,
        &session,
        &request(&root, 2, "later-parent", vec![Command::Wait { ticks: 1 }]),
    );
    commit(
        &host,
        &child_session,
        &request(
            &child,
            2,
            "later-child",
            vec![Command::Wait { ticks: 1 }, Command::Wait { ticks: 1 }],
        ),
    );
    let parent_before = temp.engine(&root).canonical_bytes();
    let child_before = temp.engine(&child).canonical_bytes();
    let recovered = host.fork_branch(&session, &fixed, &|| false).unwrap();
    assert!(!recovered.created);
    assert_eq!(
        (
            recovered.scope.clone(),
            recovered.fork_revision,
            recovered.head_revision
        ),
        (child.clone(), 2, 4)
    );
    let changed_guard = WorkspaceForkRequest {
        expected_parent_revision: 999,
        ..fixed.clone()
    };
    assert_eq!(
        host.fork_branch(&session, &changed_guard, &|| false)
            .unwrap(),
        recovered
    );
    assert_eq!(temp.engine(&root).canonical_bytes(), parent_before);
    assert_eq!(temp.engine(&child).canonical_bytes(), child_before);
    assert_eq!(temp.engine(&child).receipts().len(), 2);
    assert_eq!(
        catalog(&host, &root)["branches"].as_array().unwrap().len(),
        2
    );
    let wrong_parent = fork(&child, "fixed-recovery", 4, 2);
    assert_eq!(
        host.fork_branch(&child_session, &wrong_parent, &|| false)
            .unwrap_err(),
        "Rule"
    );
    let other = host
        .fork_branch(&session, &fork(&root, "other-parent", 3, 2), &|| false)
        .unwrap();
    let other_session = resume(&host, &other.scope);
    assert_eq!(
        host.fork_branch(
            &other_session,
            &fork(&other.scope, "fixed-recovery", 2, 2),
            &|| false
        )
        .unwrap_err(),
        "RetryMismatch"
    );
}

#[test]
fn queued_and_ready_parent_turns_block_fork_but_another_scope_does_not() {
    let temp = Temp::new();
    let host = temp.host();
    let (session, root) = create(&host);
    let pending = request(&root, 0, "pending", vec![Command::Wait { ticks: 1 }]);
    submit(&host, &session, &pending);
    let fixed = fork(&root, "after-pending", 0, 0);
    assert_eq!(
        host.fork_branch(&session, &fixed, &|| false).unwrap_err(),
        "Busy"
    );
    assert_eq!(
        op(&host, &session, &root, "pending", "prepare")["data"]["phase"],
        "ready"
    );
    assert_eq!(
        host.fork_branch(&session, &fixed, &|| false).unwrap_err(),
        "Busy"
    );
    let (other_session, other) = create(&host);
    assert!(
        host.fork_branch(&other_session, &fork(&other, "independent", 0, 0), &|| {
            false
        })
        .unwrap()
        .created
    );
    assert_eq!(
        op(&host, &session, &root, "pending", "cancel")["data"]["phase"],
        "cancelled"
    );
    assert!(
        host.fork_branch(&session, &fixed, &|| false)
            .unwrap()
            .created
    );
}

struct HeldProvider {
    started: mpsc::SyncSender<()>,
    release: Arc<Mutex<mpsc::Receiver<()>>>,
}
impl InferenceProvider for HeldProvider {
    fn poll(&mut self, _: &GenerationRequest, _: &Cancellation) -> Poll<Result<Vec<u8>, Error>> {
        self.started.send(()).unwrap();
        self.release
            .lock()
            .unwrap()
            .recv_timeout(Duration::from_secs(10))
            .unwrap();
        Poll::Ready(Err(Error::Provider))
    }
}
#[test]
fn actual_inflight_provider_parent_is_busy_until_work_settles() {
    let temp = Temp::new();
    let host = Arc::new(temp.host());
    let (session, root) = create(&host);
    let (started_tx, started_rx) = mpsc::sync_channel(1);
    let (release_tx, release_rx) = mpsc::channel();
    let release = Arc::new(Mutex::new(release_rx));
    host.configure_fixture_provider(
        PlayProfile {
            id: "fork-held-synthetic".into(),
            model_sha256: "a".repeat(64),
            runtime_revision: "b".repeat(40),
            template_sha256: "c".repeat(64),
            worker_sha256: "d".repeat(64),
            profile_manifest_sha256: "e".repeat(64),
            context_tokens: 4096,
            director_tokens: 350,
            narrator_tokens: 350,
            deadline_ms: 120_000,
            repair_limit: 1,
        },
        Arc::new(move || {
            Box::new(HeldProvider {
                started: started_tx.clone(),
                release: release.clone(),
            })
        }),
    )
    .unwrap();
    let r = Request {
        version: 1,
        scope: root.clone(),
        turn: "held".into(),
        expected_revision: 0,
        intent: Intent::FreeText {
            kind: PlayInputKind::Action,
            text: "I give my last potion to Mira.".into(),
        },
    };
    assert_eq!(
        call(
            &host,
            json!({"op":"free_text","session":session,"request":r})
        )["data"]["phase"],
        "queued"
    );
    let worker_host = host.clone();
    let worker_session = session.clone();
    let worker_scope = root.clone();
    let worker = std::thread::spawn(move || {
        op(
            &worker_host,
            &worker_session,
            &worker_scope,
            "held",
            "prepare",
        )
    });
    started_rx.recv_timeout(Duration::from_secs(10)).unwrap();
    let result = host.fork_branch(&session, &fork(&root, "held-fork", 0, 0), &|| false);
    release_tx.send(()).unwrap();
    let settled = worker.join().unwrap();
    assert_eq!(result.unwrap_err(), "Busy");
    assert_eq!(settled["data"]["phase"], "failed", "{settled}");
    assert!(
        host.fork_branch(&session, &fork(&root, "held-fork", 0, 0), &|| false)
            .unwrap()
            .created
    );
}

#[test]
fn exact_live_session_scope_and_native_only_boundary_are_required() {
    let temp = Temp::new();
    let host = temp.host();
    let (session, root) = create(&host);
    let (other_session, _) = create(&host);
    let r = fork(&root, "native-child", 0, 0);
    assert_eq!(
        host.fork_branch("missing", &r, &|| false).unwrap_err(),
        "Closed"
    );
    assert_eq!(
        host.fork_branch(&other_session, &r, &|| false).unwrap_err(),
        "Scope"
    );
    assert_eq!(
        call(
            &host,
            json!({"op":"fork_branch","session":session,"parent":root,"child_branch":"wire-child","expected_parent_revision":0,"at_revision":0})
        )["status"],
        "rejected"
    );
    assert_eq!(
        catalog(&host, &root)["branches"].as_array().unwrap().len(),
        1
    );
    call(&host, json!({"op":"close","session":session,"scope":root}));
    assert_eq!(
        host.fork_branch(&session, &r, &|| false).unwrap_err(),
        "Closed"
    );
    let ephemeral = Host::new(false);
    let (ephemeral_session, ephemeral_scope) = create(&ephemeral);
    assert_eq!(
        ephemeral
            .fork_branch(
                &ephemeral_session,
                &fork(&ephemeral_scope, "no-durability", 0, 0),
                &|| false
            )
            .unwrap_err(),
        "Unsupported"
    );
}
