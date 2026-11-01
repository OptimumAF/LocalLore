//! FIRST native presentation oracles. Real accepted Engines behind a read-only
//! persistence fixture; neither SQLite/JNI nor model-quality evidence.
#![cfg(feature = "host")]

use locallore::{
    author_correction::{AuthorCorrectionInputV1, AuthorCorrectionOperationV1},
    contracts::*,
    engine::Engine,
    host::{Host, Persistence, SavedTurn, WorkspaceSummary, MAX_OUTPUT},
    inference::{Cancellation, GenerationRequest, InferenceProvider},
    play::{self, PlayProfile},
};
use serde_json::{json, Value};
use std::{
    collections::{BTreeSet, VecDeque},
    sync::{Arc, Mutex},
    task::Poll,
};

const OLD: &str = "The sealed survey beacon flashes amber.";
const NEW: &str = "PRIVATE_UNSEEN_PRESENTATION_CORRECTION";
const REASON: &str = "PRIVATE_PRESENTATION_AUTHOR_REASON";
const NPC: &str = "PRIVATE_PRESENTATION_NPC_BELIEF";

fn engine() -> Engine {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    seed.facts.get_mut("relic-location").unwrap().proposition = OLD.into();
    seed.beliefs[0].proposition = NPC.into();
    Engine::new(seed).unwrap()
}

fn append(engine: &mut Engine, turn: &str, intent: Intent) -> Receipt {
    let request = engine.request(turn, intent);
    let proposal = Engine::proposal(&request).unwrap();
    let receipt = engine.preview(&request, &proposal).unwrap();
    engine.commit_prepared(&receipt).unwrap();
    receipt
}

struct Script(VecDeque<Vec<u8>>);
impl InferenceProvider for Script {
    fn poll(
        &mut self,
        _: &GenerationRequest,
        _: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        Poll::Ready(self.0.pop_front().ok_or(Error::Provider))
    }
}

fn mixed() -> (Engine, Vec<Receipt>) {
    let mut engine = engine();
    let mut receipts = vec![append(
        &mut engine,
        "accepted-actions",
        Intent::Actions(vec![Command::Wait { ticks: 1 }]),
    )];
    receipts.push(append(
        &mut engine,
        "accepted-dialogue",
        Intent::Dialogue {
            text: "I will inspect the survey notes myself.".into(),
            audience: ["mira".into()].into(),
        },
    ));
    let request = engine.request(
        "accepted-free-text",
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: "I wait for one tide tick.".into(),
        },
    );
    let mut script = Script(
        [
            json!({"commands":[{"op":"wait","ticks":1}]}),
            json!({"text":"You pause as a tide tick passes.","event_ids":[3],"speaker":"narrator"}),
        ]
        .into_iter()
        .map(|reply| serde_json::to_vec(&reply).unwrap())
        .collect(),
    );
    let profile = PlayProfile {
        id: "presentation-first-script".into(),
        model_sha256: "a".repeat(64),
        runtime_revision: "b".repeat(40),
        template_sha256: "c".repeat(64),
        worker_sha256: "d".repeat(64),
        profile_manifest_sha256: "e".repeat(64),
        context_tokens: 4096,
        director_tokens: 350,
        narrator_tokens: 350,
        deadline_ms: 5000,
        repair_limit: 1,
    };
    let receipt = play::execute(
        &mut engine,
        &request,
        &mut script,
        &Cancellation::default(),
        &profile,
    )
    .unwrap();
    assert_eq!(receipt.request(), &request);
    engine.commit_prepared(&receipt).unwrap();
    receipts.push(receipt);
    (engine, receipts)
}

fn corrected(parent: &Engine, replacement: &str) -> Engine {
    let input = AuthorCorrectionInputV1 {
        version: 1,
        parent: parent.scope().clone(),
        expected_parent_revision: parent.revision(),
        fork_revision: parent.revision(),
        child_branch: "corrected".into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(),
            expected_proposition: OLD.into(),
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
    writes: usize,
}
struct ReadOnly(Arc<Mutex<Source>>);
impl ReadOnly {
    fn refuse<T>(&self) -> Result<T, String> {
        self.0.lock().unwrap().writes += 1;
        Err("Unsupported".into())
    }
}
impl Persistence for ReadOnly {
    fn location(&self) -> &str {
        "synthetic-presentation-readonly"
    }
    fn list(&mut self) -> Result<Vec<WorkspaceSummary>, String> {
        Err("Unsupported".into())
    }
    fn create(&mut self) -> Result<Engine, String> {
        self.refuse()
    }
    fn validate_scope(&mut self, scope: &Scope) -> Result<(), String> {
        if self.0.lock().unwrap().engines.iter().any(|e| e.scope() == scope) {
            Ok(())
        } else {
            Err("NotFound".into())
        }
    }
    fn resume(&mut self, scope: &Scope) -> Result<Engine, String> {
        self.0
            .lock()
            .unwrap()
            .engines
            .iter()
            .find(|e| e.scope() == scope)
            .cloned()
            .ok_or_else(|| "NotFound".into())
    }
    fn begin(&mut self, _: &Request) -> Result<SavedTurn, String> {
        self.refuse()
    }
    fn commit(&mut self, _: &Request, _: &Proposal, _: &str) -> Result<Receipt, String> {
        self.refuse()
    }
    fn cancel(&mut self, _: &Request) -> Result<SavedTurn, String> {
        self.refuse()
    }
    fn fail(&mut self, _: &Request) -> Result<SavedTurn, String> {
        self.refuse()
    }
    fn stale(&mut self, _: &Request) -> Result<SavedTurn, String> {
        self.refuse()
    }
    fn status(&mut self, _: &Scope, _: &str) -> Result<SavedTurn, String> {
        Err("Unsupported".into())
    }
}
fn host(engines: Vec<Engine>, grant: bool) -> (Host, Arc<Mutex<Source>>) {
    let source = Arc::new(Mutex::new(Source { engines, writes: 0 }));
    let host = Host::with_persistence(grant, Box::new(ReadOnly(source.clone())));
    (host, source)
}
fn call(host: &Host, command: Value) -> Value {
    host.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
}
fn session(host: &Host, engine: &Engine) -> String {
    let reply = call(host, json!({"op":"resume","scope":engine.scope()}));
    assert_eq!(reply["status"], "ok", "{reply}");
    reply["data"]["session"].as_str().unwrap().into()
}
fn presentation(host: &Host, session: &str, engine: &Engine) -> Value {
    call(host, json!({"op":"play_presentation_v2","session":session,
        "scope":engine.scope(),"expected_revision":engine.revision()}))
}
fn keys(value: &Value, expected: &[&str]) {
    assert_eq!(
        value.as_object().unwrap().keys().map(String::as_str).collect::<BTreeSet<_>>(),
        expected.iter().copied().collect::<BTreeSet<_>>()
    );
}
fn rejected(reply: &Value, error: &str) {
    assert_eq!(reply["status"], "rejected", "{reply}");
    assert_eq!(reply["error"], error, "{reply}");
    assert!(reply.get("data").is_none());
}
fn check(reply: &Value, engine: &Engine, all_receipts: &[Receipt]) {
    assert_eq!(reply["status"], "ok", "{reply}");
    keys(reply, &["version", "status", "data"]);
    let data = &reply["data"];
    keys(data, &["version", "domain_version", "scope", "revision", "rules", "player", "inventory", "turns", "window"]);
    assert_eq!(data["version"], 2);
    assert_eq!(data["domain_version"], engine.domain_version());
    assert_eq!(data["scope"], json!(engine.scope()));
    assert_eq!(data["revision"], engine.revision());
    assert_eq!(data["rules"], json!(engine.seed().profile));
    keys(&data["player"], &["observer", "self_state"]);
    assert_eq!(data["player"]["observer"], engine.seed().player);
    assert_eq!(data["player"]["self_state"], json!(engine.state().actors[&engine.seed().player]));
    let inventory = engine.state().items.iter().filter(|(_, item)| item.owner == engine.seed().player).collect::<std::collections::BTreeMap<_, _>>();
    assert_eq!(data["inventory"], json!(inventory));
    let start = all_receipts.len().saturating_sub(20);
    assert_eq!(data["window"], json!({"total":all_receipts.len(),"start":start,"end":all_receipts.len()}));
    let rows = data["turns"].as_array().unwrap();
    assert_eq!(rows.len(), all_receipts.len() - start);
    for (row, accepted) in rows.iter().zip(&all_receipts[start..]) {
        keys(row, &["original_scope", "turn", "event_ids", "intent", "narration"]);
        assert_eq!(row["original_scope"], json!(accepted.request().scope));
        assert_eq!(row["turn"], accepted.request().turn);
        assert_eq!(row["event_ids"], json!(accepted.events().iter().map(AcceptedEvent::sequence).collect::<Vec<_>>()));
        assert_eq!(row["intent"], json!(accepted.request().intent));
        assert_eq!(row["narration"], accepted.narration());
    }
    let encoded = serde_json::to_string(reply).unwrap();
    for private in [OLD, NEW, REASON, NPC, "observed_overrides", "truth_overrides", "proposal", "model_sha256"] {
        assert!(!encoded.contains(private), "private field/value leaked: {private}");
    }
}

#[test]
fn both_domains_preserve_accepted_actions_dialogue_and_free_text_without_private_records() {
    let (root, receipts) = mixed();
    let child = corrected(&root, NEW);
    for engine in [root, child] {
        let canonical = engine.canonical_bytes();
        let basis = engine.accepted_history_basis().unwrap();
        for grant in [false, true] {
            let (host, source) = host(vec![engine.clone()], grant);
            let session = session(&host, &engine);
            check(&presentation(&host, &session, &engine), &engine, &receipts);
            let source = source.lock().unwrap();
            assert_eq!(source.engines[0].canonical_bytes(), canonical);
            assert_eq!(source.engines[0].accepted_history_basis().unwrap(), basis);
            assert_eq!(source.writes, 0);
        }
    }
}

#[test]
fn twenty_turn_window_preserves_whole_pairs_and_absolute_original_identities() {
    let mut engine = engine();
    let mut receipts = Vec::new();
    for i in 0..25 {
        receipts.push(append(&mut engine, &format!("wait-{i}"), Intent::Actions(vec![Command::Wait { ticks: 1 }])));
    }
    let (host, source) = host(vec![engine.clone()], false);
    let session = session(&host, &engine);
    let first = presentation(&host, &session, &engine);
    check(&first, &engine, &receipts);
    receipts.push(append(&mut engine, "wait-25", Intent::Actions(vec![Command::Wait { ticks: 1 }])));
    source.lock().unwrap().engines[0] = engine.clone();
    let second = presentation(&host, &session, &engine);
    check(&second, &engine, &receipts);
    assert_eq!(first["data"]["turns"][1], second["data"]["turns"][0]);
}

#[test]
fn fork_keeps_original_ancestor_scope_and_excludes_unselected_parent_suffix() {
    let mut parent = engine();
    let inherited = append(&mut parent, "ancestor-wait", Intent::Actions(vec![Command::Wait { ticks: 1 }]));
    append(&mut parent, "parent-only", Intent::Dialogue { text: "PRIVATE_UNSELECTED_PARENT_SUFFIX".into(), audience: ["mira".into()].into() });
    let mut child = parent.fork("presentation-child", 1).unwrap();
    let own = append(&mut child, "child-wait", Intent::Actions(vec![Command::Wait { ticks: 1 }]));
    let (host, _) = host(vec![parent, child.clone()], false);
    let session = session(&host, &child);
    let reply = presentation(&host, &session, &child);
    check(&reply, &child, &[inherited, own]);
    assert_eq!(reply["data"]["turns"][0]["original_scope"]["branch"], "main");
    assert_eq!(reply["data"]["turns"][1]["original_scope"]["branch"], "presentation-child");
    assert!(!reply.to_string().contains("PRIVATE_UNSELECTED_PARENT_SUFFIX"));
}

#[test]
fn native_observer_and_empty_window_do_not_assume_literal_player() {
    let mut seed = engine().seed().clone();
    seed.player = "mira".into();
    let engine = Engine::new(seed).unwrap();
    let (host, _) = host(vec![engine.clone()], false);
    let session = session(&host, &engine);
    check(&presentation(&host, &session, &engine), &engine, &[]);
}

#[test]
fn stale_foreign_closed_and_exact_request_shape_never_return_a_presentation() {
    let (engine, _) = mixed();
    let child = corrected(&engine, NEW);
    let (host, source) = host(vec![engine.clone(), child.clone()], false);
    let session = session(&host, &engine);
    check(&presentation(&host, &session, &engine), &engine, engine.receipts());
    rejected(&presentation(&host, "unknown", &engine), "Closed");
    rejected(&presentation(&host, &session, &child), "Scope");
    let valid = json!({"op":"play_presentation_v2","session":session,"scope":engine.scope(),"expected_revision":engine.revision()});
    for extra in ["observer", "cursor", "limit", "story_lab", "grant", "version"] {
        let mut bad = valid.clone(); bad[extra] = json!("unexpected");
        rejected(&call(&host, bad), "Malformed");
    }
    for bad_revision in [json!(-1), json!(1.5), json!(true), json!("3")] {
        let mut bad = valid.clone(); bad["expected_revision"] = bad_revision;
        rejected(&call(&host, bad), "Malformed");
    }
    let mut bad = valid.clone();bad["expected_revision"] = json!(0);
    rejected(&call(&host, bad), "Stale");
    source.lock().unwrap().engines.remove(0);
    rejected(&presentation(&host, &session, &engine), "NotFound");
    source.lock().unwrap().engines.push(engine.clone());
    rejected(&presentation(&host, &session, &engine), "Closed");
}

#[test]
fn equal_head_author_replacement_is_stale_and_legacy_domain_refusal_is_unchanged() {
    let (root, _) = mixed();
    let child = corrected(&root, NEW);
    let replacement = corrected(&root, "PRIVATE_DIFFERENT_AUTHOR_TRUTH");
    assert_eq!(child.revision(), replacement.revision());
    let (host, source) = host(vec![root.clone(), child.clone()], false);
    let main = session(&host, &root);
    let selected = session(&host, &child);
    check(&presentation(&host, &selected, &child), &child, root.receipts());
    let legacy = |session: &str, e: &Engine| call(&host, json!({"op":"play_snapshot","session":session,"scope":e.scope(),"expected_revision":e.revision()}));
    let legacy_main = legacy(&main, &root);
    assert_eq!(legacy_main["status"], "ok");
    keys(&legacy_main["data"], &["scope", "revision", "rules", "player", "inventory", "receipts"]);
    assert_eq!(legacy_main["data"]["receipts"], json!(root.receipts()));
    assert_eq!(legacy_main["data"]["player"], json!(root.character_context(&root.seed().player, root.scope(), root.revision()).unwrap()));
    rejected(&legacy(&selected, &child), "Version");
    let thin = call(&host, json!({"op":"play_snapshot_v2","session":selected,"scope":child.scope(),"expected_revision":child.revision()}));
    assert_eq!(thin["status"], "ok");
    assert!(thin["data"].get("turns").is_none());
    source.lock().unwrap().engines[1] = replacement;
    rejected(&presentation(&host, &selected, &child), "Stale");
    assert_eq!(source.lock().unwrap().writes, 0);
}

#[test]
fn oversized_twenty_complete_turns_refuse_without_clipping_or_adaptive_window() {
    let mut engine = engine();
    let mut projected_turn_bytes = 0;
    let mut largest_receipt_bytes = 0;
    for i in 0..20 {
        let commands = (0..8).map(|_| Command::Say { text: "r".repeat(1550), audience: ["mira".into()].into() }).collect();
        let request = engine.request(&format!("large-{i}"), Intent::Actions(commands));
        let request_bytes = serde_json::to_vec(&request).unwrap().len();
        assert!(request_bytes <= MAX_PROPOSAL_BYTES, "fixture request {i}: {request_bytes}");
        let proposal = Engine::proposal(&request).unwrap();
        let proposal_bytes = serde_json::to_vec(&proposal).unwrap().len();
        assert!(proposal_bytes <= MAX_PROPOSAL_BYTES, "fixture proposal {i}: {proposal_bytes}");
        engine.preflight(&request).unwrap_or_else(|error| panic!("fixture preflight {i}, request {request_bytes}, proposal {proposal_bytes}: {error:?}"));
        let receipt = engine.preview(&request, &proposal).unwrap_or_else(|error| panic!("fixture preview {i}, request {request_bytes}, proposal {proposal_bytes}: {error:?}"));
        let receipt_bytes = serde_json::to_vec(&receipt).unwrap().len();
        assert!(receipt_bytes <= MAX_RECEIPT_BYTES, "fixture receipt {i}: {receipt_bytes}");
        largest_receipt_bytes = largest_receipt_bytes.max(receipt_bytes);
        engine.commit_prepared(&receipt).unwrap();
        assert!(serde_json::to_vec(engine.state()).unwrap().len() <= 262_144);
        projected_turn_bytes += serde_json::to_vec(&json!({"original_scope":receipt.request().scope,
            "turn":receipt.request().turn,"event_ids":receipt.events().iter().map(AcceptedEvent::sequence).collect::<Vec<_>>(),
            "intent":receipt.request().intent,"narration":receipt.narration()})).unwrap().len();
    }
    assert!(projected_turn_bytes > MAX_OUTPUT, "fixture must reach the real Host cap");
    println!("Accepted overflow fixture: 20 turns; largest receipt {largest_receipt_bytes}; mechanical projection {}; presentation turns {projected_turn_bytes}", serde_json::to_vec(engine.state()).unwrap().len());
    let (host, source) = host(vec![engine.clone()], false);
    let session = session(&host, &engine);
    let reply = presentation(&host, &session, &engine);
    rejected(&reply, "TooLarge");
    assert!(serde_json::to_vec(&reply).unwrap().len() <= MAX_OUTPUT);
    assert_eq!(source.lock().unwrap().writes, 0);
}
