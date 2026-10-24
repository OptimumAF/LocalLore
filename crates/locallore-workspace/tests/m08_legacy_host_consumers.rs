// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen against b85122a before the legacy Host Domain2 admission fix.
//! Actual Store author API and workspace Host; no fake persistence or inference.
use locallore::{
    author_correction::{AuthorCorrectionInputV1, AuthorCorrectionOperationV1, CanonicalRecord},
    contracts::{Scope, Seed},
    host::Host,
};
use locallore_storage::Store;
use serde_json::{json, Value};
use std::{
    path::PathBuf,
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT: AtomicU64 = AtomicU64::new(0);

struct Temp(PathBuf);
impl Temp {
    fn new() -> Self {
        let path = std::env::temp_dir().join(format!(
            "locallore-m08-legacy-host-{}-{}-{}",
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
    fn database(&self) -> PathBuf {
        self.0.join("synthetic.sqlite")
    }
}
impl Drop for Temp {
    fn drop(&mut self) {
        // The only recursively removed path is this guard's newly created temp directory.
        // Do not obscure the original assertion if a failed Host still owns a file.
        if let Err(error) = std::fs::remove_dir_all(&self.0) {
            if !std::thread::panicking() {
                panic!("synthetic fixture cleanup failed: {error}");
            }
        }
    }
}

struct Fixture {
    parent: Scope,
    child: Scope,
    control: Scope,
    child_head: u64,
}

fn authored_fixture(temp: &Temp) -> Fixture {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    seed.facts.get_mut("relic-location").unwrap().proposition = "SYNTHETIC_BEFORE".into();
    let parent = seed.scope.clone();
    let mut control_seed = seed.clone();
    control_seed.scope.story = "unrelated-control".into();
    let control = control_seed.scope.clone();
    let mut store = Store::open_application(&temp.database()).unwrap();
    assert_eq!(store.info().unwrap().schema_version, 5);
    store.create_story("Synthetic author source", seed).unwrap();
    store
        .create_story("Synthetic unrelated Domain1 control", control_seed)
        .unwrap();
    let request = AuthorCorrectionInputV1 {
        version: 1,
        parent: parent.clone(),
        expected_parent_revision: 0,
        fork_revision: 0,
        child_branch: "authored-child".into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(),
            expected_proposition: "SYNTHETIC_BEFORE".into(),
            replacement: "SYNTHETIC_AUTHOR_AFTER".into(),
        },
        reason: "SYNTHETIC_AUTHOR_REASON".into(),
    };
    let prepared = store
        .prepare_author_correction(&request, &|| false)
        .unwrap();
    let outcome = store.apply_author_correction(&prepared, &|| false).unwrap();
    assert!(outcome.created);
    assert_eq!(outcome.author_revision, 1);
    assert_eq!(outcome.head_revision, 1);
    let child_engine = store.resume(&outcome.scope).unwrap().engine;
    assert_eq!(child_engine.domain_version(), 2);
    assert!(matches!(
        child_engine.canonical_records(),
        [CanonicalRecord::AuthorV1(_)]
    ));
    assert_eq!(store.resume(&parent).unwrap().engine.domain_version(), 1);
    assert_eq!(store.resume(&control).unwrap().engine.domain_version(), 1);
    Fixture {
        parent,
        child: outcome.scope,
        control,
        child_head: outcome.head_revision,
    }
}

fn call(host: &Host, command: Value) -> Value {
    host.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
}

fn assert_workspace(reply: &Value) {
    assert_eq!(reply["version"], 1, "{reply}");
    assert_eq!(reply["status"], "ok", "{reply}");
    assert_eq!(reply["data"]["persistent"], true, "{reply}");
    // Host/workspace protocol1 and SQLite schema5 are different version axes.
    assert_eq!(reply["data"]["schema_version"], 1, "{reply}");
    assert_eq!(reply["data"]["database_schema_version"], 5, "{reply}");
    assert_eq!(reply["data"]["stories"].as_array().unwrap().len(), 2);
}

fn canonical_contents(temp: &Temp, fixture: &Fixture) -> Value {
    // Public read-only replay includes the complete mixed record stream, not
    // merely Engine::receipts(), which omits author records by design.
    let mut store = Store::open_read_only(&temp.database()).unwrap();
    let scopes = [&fixture.parent, &fixture.child, &fixture.control];
    let histories: Vec<Value> = scopes
        .into_iter()
        .map(|scope| {
            let engine = store.resume(scope).unwrap().engine;
            json!({
                "scope":scope,
                "domain":engine.domain_version(),
                "revision":engine.revision(),
                "seed":engine.seed(),
                "canonical_projection":engine.canonical_bytes(),
                "canonical_records":engine.canonical_records(),
                "legacy_receipts":engine.receipts()
            })
        })
        .collect();
    json!({
        "database_schema":store.info().unwrap().schema_version,
        "histories":histories,
        "author_catalog":store.branch_catalog(&fixture.parent.story, &||false).unwrap(),
        "control_catalog":store.branch_catalog(&fixture.control.story, &||false).unwrap()
    })
}

fn assert_closed_legacy_refusal(reply: &Value) {
    assert!(
        reply == &json!({"version":1,"status":"rejected","error":"Version"})
            || reply == &json!({"version":1,"status":"rejected","error":"Unsupported"}),
        "Domain2 must receive a closed legacy refusal, never Internal, incomplete success, or fallback: {reply}"
    );
}

fn legacy_consumer_refusal(op: &str) {
    let temp = Temp::new();
    let fixture = authored_fixture(&temp);
    let before = canonical_contents(&temp, &fixture);
    // Each test owns a fresh real Host. In particular a PlaySnapshot panic must
    // not hide the independent omniscient Inspect incomplete-success defect.
    let host = locallore_workspace::open(&temp.database(), true).unwrap();
    assert_workspace(&call(&host, json!({"op":"workspace"})));
    let resumed = call(&host, json!({"op":"resume","scope":fixture.child}));
    let refusal = if resumed["status"] == "ok" {
        assert_eq!(resumed["data"]["scope"], json!(fixture.child));
        assert_eq!(resumed["data"]["revision"], fixture.child_head);
        let session = resumed["data"]["session"].as_str().unwrap();
        let mut command = json!({
            "op":op,"session":session,"scope":fixture.child,
            "expected_revision":fixture.child_head
        });
        if op == "inspect" {
            // Story Lab permission is actually granted above; Forbidden is not
            // an acceptable substitute for a Domain2 compatibility refusal.
            command["observer"] = json!("omniscient");
        }
        call(&host, command)
    } else {
        // A deliberate typed refusal at Resume is also a safe interim closure.
        // Neither alternative proves a functional Domain2 desktop UI.
        resumed
    };

    // Capture all follow-ups before asserting the refusal. The historical
    // caught panic returns Internal and poisons the owner; both facts remain
    // visible in diagnostics rather than stopping at the first response.
    let workspace_after = call(&host, json!({"op":"workspace"}));
    let control_resume = call(&host, json!({"op":"resume","scope":fixture.control}));
    let control_view = control_resume["data"]["session"].as_str().map(|session| {
        call(
            &host,
            json!({"op":"play_snapshot","session":session,"scope":fixture.control,"expected_revision":0}),
        )
    });
    drop(host);
    let after = canonical_contents(&temp, &fixture);
    assert_eq!(after, before, "legacy read/refusal changed durable canon");
    let diagnostic = json!({
        "consumer":op,"refusal":refusal,"workspace_after":workspace_after,
        "control_resume":control_resume,"control_view":control_view
    });
    assert_eq!(
        workspace_after["status"], "ok",
        "unrelated owner work must remain usable after {op}: {diagnostic}"
    );
    assert_workspace(&workspace_after);
    assert_eq!(control_resume["status"], "ok", "{diagnostic}");
    assert_eq!(control_resume["data"]["scope"], json!(fixture.control));
    assert_eq!(control_resume["data"]["revision"], 0);
    let control_view = control_view.expect("successful control Resume must provide a session");
    assert_eq!(control_view["status"], "ok", "{diagnostic}");
    assert_eq!(control_view["data"]["scope"], json!(fixture.control));
    assert_eq!(control_view["data"]["revision"], 0);
    assert_eq!(control_view["data"]["receipts"], json!([]));
    assert_closed_legacy_refusal(&refusal);
}

#[test]
fn actual_schema5_workspace_keeps_protocol1_with_store_authored_domain2_present() {
    let temp = Temp::new();
    let fixture = authored_fixture(&temp);
    let before = canonical_contents(&temp, &fixture);
    let host = locallore_workspace::open(&temp.database(), true).unwrap();
    assert_workspace(&call(&host, json!({"op":"workspace"})));
    drop(host);
    assert_eq!(canonical_contents(&temp, &fixture), before);
}

#[test]
fn legacy_play_snapshot_refuses_domain2_without_poisoning_unrelated_domain1_host_work() {
    legacy_consumer_refusal("play_snapshot");
}

#[test]
fn legacy_omniscient_inspect_refuses_domain2_without_incomplete_success_or_canon_change() {
    legacy_consumer_refusal("inspect");
}
