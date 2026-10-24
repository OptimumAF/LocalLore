// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Future Host thin-view oracles, frozen before production; UNCOMPILED/UNRUN.
//! Actual Core engines behind a read-only fixture port, not SQLite/JNI execution.
#![cfg(feature = "host")]
use locallore::{
    author_correction::{AuthorCorrectionInputV1, AuthorCorrectionOperationV1},
    contracts::*,
    engine::Engine,
    host::{Host, Persistence, SavedTurn, WorkspaceSummary, MAX_OUTPUT},
};
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    sync::{Arc, Mutex},
};

const A: &str = "PRIVATE_THIN_OBSERVED_A";
const B: &str = "PRIVATE_THIN_WORLD_B";
const REASON: &str = "PRIVATE_THIN_AUTHOR_REASON";
fn root() -> Engine {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    let fact = seed.facts.get_mut("relic-location").unwrap();
    fact.proposition = A.into();
    fact.known_by.insert("mira".into());
    Engine::new(seed).unwrap()
}
fn authored(parent: &Engine, replacement: &str) -> Engine {
    let input = AuthorCorrectionInputV1 {
        version: 1,
        parent: parent.scope().clone(),
        expected_parent_revision: parent.revision(),
        fork_revision: parent.revision(),
        child_branch: "thin-child".into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(),
            expected_proposition: A.into(),
            replacement: replacement.into(),
        },
        reason: REASON.into(),
    };
    let plan = parent.prepare_author_correction(&input, &|| false).unwrap();
    parent
        .apply_author_correction(&plan, &|| false)
        .unwrap()
        .engine
}
#[derive(Default)]
struct Source {
    engines: Vec<Engine>,
    reads: usize,
    writes: usize,
}
struct ReadOnlyPort(Arc<Mutex<Source>>);
impl ReadOnlyPort {
    fn refuse_write<T>(&self) -> Result<T, String> {
        self.0.lock().unwrap().writes += 1;
        Err("Unsupported".into())
    }
}
impl Persistence for ReadOnlyPort {
    fn location(&self) -> &str {
        "synthetic-thin-view-port"
    }
    fn list(&mut self) -> Result<Vec<WorkspaceSummary>, String> {
        Err("Unsupported".into())
    }
    fn create(&mut self) -> Result<Engine, String> {
        self.refuse_write()
    }
    fn validate_scope(&mut self, scope: &Scope) -> Result<(), String> {
        if self
            .0
            .lock()
            .unwrap()
            .engines
            .iter()
            .any(|engine| engine.scope() == scope)
        {
            Ok(())
        } else {
            Err("NotFound".into())
        }
    }
    fn resume(&mut self, scope: &Scope) -> Result<Engine, String> {
        let mut source = self.0.lock().unwrap();
        source.reads += 1;
        source
            .engines
            .iter()
            .find(|engine| engine.scope() == scope)
            .cloned()
            .ok_or_else(|| "NotFound".into())
    }
    fn begin(&mut self, _: &Request) -> Result<SavedTurn, String> {
        self.refuse_write()
    }
    fn commit(&mut self, _: &Request, _: &Proposal, _: &str) -> Result<Receipt, String> {
        self.refuse_write()
    }
    fn cancel(&mut self, _: &Request) -> Result<SavedTurn, String> {
        self.refuse_write()
    }
    fn fail(&mut self, _: &Request) -> Result<SavedTurn, String> {
        self.refuse_write()
    }
    fn stale(&mut self, _: &Request) -> Result<SavedTurn, String> {
        self.refuse_write()
    }
    fn status(&mut self, _: &Scope, _: &str) -> Result<SavedTurn, String> {
        Err("Unsupported".into())
    }
}
fn host(engines: Vec<Engine>, grant: bool) -> (Host, Arc<Mutex<Source>>) {
    let source = Arc::new(Mutex::new(Source {
        engines,
        ..Source::default()
    }));
    (
        Host::with_persistence(grant, Box::new(ReadOnlyPort(source.clone()))),
        source,
    )
}
fn call(host: &Host, command: Value) -> Value {
    host.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
}
fn resume(host: &Host, engine: &Engine) -> String {
    let reply = call(host, json!({"op":"resume","scope":engine.scope()}));
    assert_eq!(reply["status"], "ok", "{reply}");
    reply["data"]["session"].as_str().unwrap().into()
}
fn snapshot(host: &Host, session: &str, engine: &Engine) -> Value {
    call(
        host,
        json!({"op":"play_snapshot_v2","session":session,"scope":engine.scope(),"expected_revision":engine.revision()}),
    )
}
fn keys(value: &Value, expected: &[&str]) {
    assert_eq!(
        value
            .as_object()
            .unwrap()
            .keys()
            .map(String::as_str)
            .collect::<BTreeSet<_>>(),
        expected.iter().copied().collect::<BTreeSet<_>>()
    );
}
fn thin(reply: &Value, engine: &Engine) {
    keys(reply, &["version", "status", "data"]);
    assert_eq!(reply["version"], 1);
    assert_eq!(reply["status"], "ok");
    let data = &reply["data"];
    keys(
        data,
        &[
            "version",
            "domain_version",
            "scope",
            "revision",
            "rules",
            "player",
            "inventory",
        ],
    );
    assert_eq!(data["version"], 2);
    assert_eq!(data["domain_version"], engine.domain_version());
    assert_eq!(data["scope"], json!(engine.scope()));
    assert_eq!(data["revision"], engine.revision());
    assert_eq!(data["rules"], json!(engine.seed().profile));
    keys(&data["player"], &["observer", "self_state"]);
    let player = &engine.seed().player;
    assert_eq!(data["player"]["observer"], *player);
    assert_eq!(
        data["player"]["self_state"],
        json!(engine.state().actors[player])
    );
    let inventory = engine
        .state()
        .items
        .iter()
        .filter(|(_, item)| &item.owner == player)
        .collect::<BTreeMap<_, _>>();
    assert_eq!(data["inventory"], serde_json::to_value(inventory).unwrap());
    assert!(serde_json::to_vec(reply).unwrap().len() <= MAX_OUTPUT);
    let encoded = serde_json::to_string(data).unwrap();
    for private in [
        A,
        B,
        REASON,
        "truth_overrides",
        "observed_overrides",
        "observations",
        "facts",
        "beliefs",
        "receipts",
        "author_correction",
    ] {
        assert!(
            !encoded.contains(private),
            "thin player view leaked {private}"
        );
    }
}
fn rejected(reply: &Value, error: &str) {
    assert_eq!(reply["version"], 1);
    assert_eq!(reply["status"], "rejected");
    assert_eq!(reply["error"], error, "{reply}");
    assert!(reply.get("data").is_none());
}

#[test]
fn actual_domain1_and_authored_domain2_are_exact_thin_reads_without_private_history() {
    for engine in [root(), authored(&root(), B)] {
        for grant in [false, true] {
            let before = engine.accepted_history_basis().unwrap();
            let (host, source) = host(vec![engine.clone()], grant);
            let session = resume(&host, &engine);
            thin(&snapshot(&host, &session, &engine), &engine);
            assert_eq!(source.lock().unwrap().writes, 0);
            assert_eq!(
                source.lock().unwrap().engines[0]
                    .accepted_history_basis()
                    .unwrap(),
                before
            );
            // Read does not change NPC observation, even with native Lab grant.
            assert_eq!(
                source.lock().unwrap().engines[0]
                    .observed_facts("mira", engine.scope(), engine.revision())
                    .unwrap()["relic-location"]
                    .proposition,
                A
            );
        }
    }
}

#[test]
fn actual_seed_player_identity_is_used_instead_of_a_hardcoded_player_actor() {
    let mut seed = root().seed().clone();
    seed.player = "mira".into();
    let engine = Engine::new(seed).unwrap();
    let (host, _) = host(vec![engine.clone()], false);
    let session = resume(&host, &engine);
    let reply = snapshot(&host, &session, &engine);
    thin(&reply, &engine);
    assert_eq!(reply["data"]["player"]["observer"], "mira");
    assert!(reply["data"]["inventory"].as_object().unwrap().is_empty());
}

#[test]
fn durable_refresh_reads_actual_appended_head_and_inventory_before_head_comparison() {
    let engine = root();
    let (host, source) = host(vec![engine.clone()], false);
    let session = resume(&host, &engine);
    thin(&snapshot(&host, &session, &engine), &engine);
    let mut advanced = engine.clone();
    let request = advanced.request(
        "external-gift",
        Intent::Actions(vec![Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 1,
        }]),
    );
    let proposal = Engine::proposal(&request).unwrap();
    let accepted = advanced.preview(&request, &proposal).unwrap();
    advanced.commit_prepared(&accepted).unwrap();
    source.lock().unwrap().engines[0] = advanced.clone();
    rejected(&snapshot(&host, &session, &engine), "Stale");
    let reply = snapshot(&host, &session, &advanced);
    thin(&reply, &advanced);
    assert!(reply["data"]["inventory"].get("potion").is_none());
    assert!(source.lock().unwrap().reads >= 4);
    assert_eq!(source.lock().unwrap().writes, 0);
}

#[test]
fn equal_head_replacement_author_truth_cannot_silently_replace_selected_source() {
    let b = authored(&root(), B);
    let c = authored(&root(), "PRIVATE_THIN_WORLD_C");
    assert_eq!(b.scope(), c.scope());
    assert_eq!(b.revision(), c.revision());
    assert_eq!(b.canonical_bytes(), c.canonical_bytes());
    assert_ne!(
        b.accepted_history_basis().unwrap(),
        c.accepted_history_basis().unwrap()
    );
    let (host, source) = host(vec![b.clone()], false);
    let session = resume(&host, &b);
    let before = snapshot(&host, &session, &b);
    thin(&before, &b);
    source.lock().unwrap().engines[0] = c;
    rejected(&snapshot(&host, &session, &b), "Stale");
    source.lock().unwrap().engines[0] = b.clone();
    assert_eq!(snapshot(&host, &session, &b), before);
    assert_eq!(source.lock().unwrap().writes, 0);
}

#[test]
fn closed_scope_stale_and_retired_admission_do_not_return_cached_private_data() {
    let parent = root();
    let child = authored(&parent, B);
    let (host, source) = host(vec![parent.clone(), child.clone()], false);
    let session = resume(&host, &parent);
    rejected(&snapshot(&host, "unknown-session", &parent), "Closed");
    rejected(&snapshot(&host, &session, &child), "Scope");
    let wrong_head = call(
        &host,
        json!({"op":"play_snapshot_v2","session":session,"scope":parent.scope(),"expected_revision":1}),
    );
    rejected(&wrong_head, "Stale");
    thin(&snapshot(&host, &session, &parent), &parent);
    // Fixture admission removal exercises the existing NotFound lifetime fence;
    // it is not actual Store retention/tombstone execution.
    source.lock().unwrap().engines.remove(0);
    rejected(&snapshot(&host, &session, &parent), "NotFound");
    source.lock().unwrap().engines.push(parent.clone());
    rejected(&snapshot(&host, &session, &parent), "Closed");
    let next = resume(&host, &parent);
    assert_ne!(session, next);
    thin(&snapshot(&host, &next, &parent), &parent);
    assert_eq!(source.lock().unwrap().writes, 0);
}

#[test]
fn exact_three_field_command_rejects_unknown_extra_and_invalid_integer_shapes() {
    let engine = root();
    let (host, _) = host(vec![engine.clone()], false);
    let session = resume(&host, &engine);
    let valid = json!({"op":"play_snapshot_v2","session":session,"scope":engine.scope(),"expected_revision":0});
    for (field, value) in [
        ("version", json!(2)),
        ("observer", json!("mira")),
        ("story_lab_granted", json!(true)),
        ("facts", json!({})),
    ] {
        let mut command = valid.clone();
        command[field] = value;
        rejected(&call(&host, command), "Malformed");
    }
    for revision in [json!(-1), json!(0.5), json!("0"), Value::Null] {
        let mut command = valid.clone();
        command["expected_revision"] = revision;
        rejected(&call(&host, command), "Malformed");
    }
    let mut unknown = valid.clone();
    unknown["op"] = json!("play_snapshot_v3");
    rejected(&call(&host, unknown), "Malformed");
    rejected(
        &host.call(&serde_json::to_vec(&json!({"version":2,"command":valid})).unwrap()),
        "Version",
    );
    thin(&snapshot(&host, &session, &engine), &engine);
}

#[test]
fn legacy_play_snapshot_keeps_domain1_shape_and_domain2_version_refusal() {
    let parent = root();
    let child = authored(&parent, B);
    let (host, source) = host(vec![parent.clone(), child.clone()], true);
    let parent_session = resume(&host, &parent);
    let child_session = resume(&host, &child);
    let legacy = |session: &str, engine: &Engine| {
        call(
            &host,
            json!({"op":"play_snapshot","session":session,"scope":engine.scope(),"expected_revision":engine.revision()}),
        )
    };
    let before = legacy(&parent_session, &parent);
    assert_eq!(before["status"], "ok");
    assert!(before["data"].get("receipts").is_some());
    assert!(before["data"]["player"].get("facts").is_some());
    rejected(&legacy(&child_session, &child), "Version");
    thin(&snapshot(&host, &child_session, &child), &child);
    assert_eq!(legacy(&parent_session, &parent), before);
    let close = call(
        &host,
        json!({"op":"close","session":child_session,"scope":child.scope()}),
    );
    assert_eq!(close["status"], "ok");
    rejected(&snapshot(&host, &child_session, &child), "Closed");
    assert_eq!(source.lock().unwrap().writes, 0);
}
