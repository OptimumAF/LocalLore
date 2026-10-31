// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent FIRST Android owner oracles; source-authored before adoption.
//! Actual Registry/SQLite/Bridge with synthetic external replies, not a model.
use locallore::{
    author_correction::{AuthorCorrectionInputV1, AuthorCorrectionOperationV1},
    contracts::{Command, Receipt, Request, Scope, Seed},
    engine::Engine,
    inspection::sha256,
    play::{
        authored_scene_narration::{self, AuthoredSceneRecipeV2},
        scene_narration::{self, SceneRecipeV1},
        PlayContextPolicy, PlayProfile,
    },
    story_authoring::*,
};
use locallore_android::workspace::WorkspaceRegistry;
use locallore_storage::Store;
use serde_json::{json, Value};
use std::{
    collections::BTreeSet,
    path::PathBuf,
    sync::{atomic::{AtomicU64, Ordering}, Arc},
    thread::{self, JoinHandle},
    time::{Duration, Instant, SystemTime, UNIX_EPOCH},
};

const LOCAL_DESCRIPTION: &str = "PRIVATE_LOCAL_DESCRIPTION_B36";
const REMOTE_NAME: &str = "Private Remote B36";
const REMOTE_DESCRIPTION: &str = "PRIVATE_REMOTE_DESCRIPTION_B36";
const NPC: &str = "PRIVATE_NPC_SHEET_B36";
const BELIEF: &str = "PRIVATE_BELIEF_B36";
const UNRELATED: &str = "PRIVATE_UNRELATED_KNOWN_FACT_B36";
const REASON: &str = "PRIVATE_CORRECTION_REASON_B36";
const CORRECTED: &str = "A corrected untyped account of the current place.";
static NEXT: AtomicU64 = AtomicU64::new(0);

fn profile() -> PlayProfile {
    PlayProfile {
        id: "android-story-scene-synthetic-v1".into(), model_sha256: "a".repeat(64),
        runtime_revision: "b".repeat(40), template_sha256: "c".repeat(64),
        worker_sha256: "d".repeat(64), profile_manifest_sha256: "e".repeat(64),
        context_tokens: 4096, director_tokens: 350, narrator_tokens: 220,
        deadline_ms: 5000, repair_limit: 1,
    }
}

fn authored_seed() -> Seed {
    let input: InitialStoryInputV1 = serde_json::from_str(include_str!(
        "../../../fixtures/initial_world/ashglass-input.json")).unwrap();
    let mut accepted: InitialWorldProposalV1 = serde_json::from_str(include_str!(
        "../../../fixtures/initial_world/ashglass-proposal.json")).unwrap();
    accepted.locations[0].name = "Copper Orchard".into();
    accepted.locations[0].description = LOCAL_DESCRIPTION.into();
    accepted.locations[1].name = REMOTE_NAME.into();
    accepted.locations[1].description = REMOTE_DESCRIPTION.into();
    accepted.characters[0].description = NPC.into();
    accepted.beliefs[0].text = BELIEF.into();
    accepted.facts.push(InitialFactV1 {
        text: UNRELATED.into(), known_by: vec![0], discoverable_at: None,
    });
    validate_proposal(&input, &accepted).unwrap();
    let response = serde_json::to_string(&accepted).unwrap();
    let origin = InitialWorldOriginV1 {
        version: 1,
        generation: InitialGenerationV1 {
            input: input.clone(), proposal: accepted.clone(), model_profile: profile().id.clone(),
            model_configuration: InitialModelConfigurationV1::from(&profile()),
            provider: InitialProviderKindV1::Scripted,
            prompt_version: locallore::story_authoring::PROMPT_VERSION.into(),
            schema_version: SCHEMA_VERSION.into(), response_sha256: sha256(response.as_bytes()), response,
        },
        reviewed: input, accepted, title: "Synthetic Android scene selection".into(),
    };
    let seed = materialize(&origin, Scope { story: "authored-android-scene".into(), branch: "main".into() }).unwrap();
    validate_origin(&seed).unwrap();
    seed
}

struct Fixture {
    database: PathBuf,
    registry: Arc<WorkspaceRegistry>,
    handle: u64,
    starter: Scope,
    authored: Scope,
    corrected: Scope,
    local_fact: String,
    remote_fact: String,
    remote: String,
}
impl Fixture {
    fn new() -> Self {
        let root = std::env::temp_dir().canonicalize().unwrap().join(format!(
            "locallore-android-story-scene-{}-{}-{}", std::process::id(),
            SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)));
        std::fs::create_dir(&root).unwrap();
        let database = root.join("stories.sqlite3");
        let mut starter: Seed = serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
        starter.scope.story = "starter-android-scene".into();
        let authored = authored_seed();
        let prefix = authored.id.strip_prefix("world-").unwrap();
        let local_fact = format!("f-{prefix}-location-0");
        let remote_fact = format!("f-{prefix}-location-1");
        let remote = format!("l-{prefix}-1");
        let mut store = Store::open_application(&database).unwrap();
        store.create_story("Starter scene control", starter.clone()).unwrap();
        store.create_story("Authored scene control", authored.clone()).unwrap();
        let input = AuthorCorrectionInputV1 {
            version: 1, parent: authored.scope.clone(), expected_parent_revision: 0, fork_revision: 0,
            child_branch: "corrected-place".into(),
            operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
                fact: local_fact.clone(), expected_proposition: authored.facts[&local_fact].proposition.clone(),
                replacement: CORRECTED.into(),
            }, reason: REASON.into(),
        };
        let prepared = store.prepare_author_correction(&input, &|| false).unwrap();
        let corrected = store.apply_author_correction(&prepared, &|| false).unwrap().scope;
        assert_eq!(store.resume(&corrected).unwrap().engine.domain_version(), 2);
        drop(store);
        let registry = Arc::new(WorkspaceRegistry::default());
        let handle = registry.open_local(&database, &serde_json::to_vec(&profile()).unwrap()).unwrap();
        Self { database, registry, handle, starter: starter.scope, authored: authored.scope,
            corrected, local_fact, remote_fact, remote }
    }
    fn call(&self, command: Value) -> Value { call(&self.registry, self.handle, command) }
    fn resume(&self, scope: &Scope) -> Value { ok(self.call(json!({"op":"resume","scope":scope}))) }
    fn engine(&self, scope: &Scope) -> Engine {
        Store::open_read_only(&self.database).unwrap().resume(scope).unwrap().engine
    }
    fn reopen(&mut self) {
        self.registry.close(self.handle);
        self.handle = self.registry.open_local(&self.database, &serde_json::to_vec(&profile()).unwrap()).unwrap();
    }
}
impl Drop for Fixture {
    fn drop(&mut self) {
        self.registry.close(self.handle);
        // Retain all synthetic database/evidence files, including on failure.
    }
}

fn decode(bytes: Vec<u8>) -> Value {
    assert!(bytes.len() <= 262_144);
    serde_json::from_slice(&bytes).unwrap()
}
fn ok(reply: Value) -> Value {
    assert_eq!(reply["status"], "ok", "fixed native call failed: {reply}");
    reply["data"].clone()
}
fn call(registry: &WorkspaceRegistry, handle: u64, command: Value) -> Value {
    decode(registry.call(handle, &serde_json::to_vec(&json!({"version":1,"command":command})).unwrap()))
}
fn op(session: &Value, scope: &Scope, operation: &str, turn: &str) -> Value {
    json!({"op":operation,"session":session["session"],"scope":scope,"turn":turn})
}
fn request(source: &Engine, turn: &str, command: &Command) -> Request {
    let text = match command {
        Command::Wait { ticks: 1 } => "I wait for one tide tick.".into(),
        Command::Move { to } => format!("I move to {to}."),
        Command::Discover { fact } => format!("I discover {fact}."),
        _ => panic!("fixture supports one exact existing action"),
    };
    source.request(turn, locallore::contracts::Intent::FreeText {
        kind: locallore::contracts::PlayInputKind::Action, text,
    })
}
fn unchanged(actual: &Engine, before: &Engine) {
    assert_eq!(actual.canonical_bytes(), before.canonical_bytes());
    assert_eq!(actual.canonical_records(), before.canonical_records());
    assert_eq!(actual.accepted_history_basis().unwrap(), before.accepted_history_basis().unwrap());
}

// An assertion during pending I/O closes the actual owned bridge BEFORE join,
// so unwinding cannot strand a scoped thread waiting for an external response.
struct Preparing {
    registry: Arc<WorkspaceRegistry>, handle: u64, worker: Option<JoinHandle<Value>>,
}
impl Preparing {
    fn new(fixture: &Fixture, session: &Value, scope: &Scope, turn: &str) -> Self {
        let registry = fixture.registry.clone();
        let handle = fixture.handle;
        let command = op(session, scope, "prepare", turn);
        let worker_registry = registry.clone();
        let worker = thread::spawn(move || call(&worker_registry, handle, command));
        Self { registry, handle, worker: Some(worker) }
    }
    fn finished(&self) -> bool { self.worker.as_ref().unwrap().is_finished() }
    fn finish(mut self) -> Value { self.worker.take().unwrap().join().unwrap() }
    fn pending(&self) -> Value {
        let deadline = Instant::now() + Duration::from_secs(6);
        loop {
            let pending = ok(decode(self.registry.poll_inference(self.handle)))["pending"].clone();
            if !pending.is_null() { return pending; }
            assert!(!self.finished(), "prepare completed without the required external request");
            assert!(Instant::now() < deadline, "bounded provider observation expired");
            thread::sleep(Duration::from_millis(1));
        }
    }
}
impl Drop for Preparing {
    fn drop(&mut self) {
        if let Some(worker) = self.worker.take() {
            self.registry.close(self.handle);
            let _ = worker.join();
        }
    }
}
fn prepare(fixture: &Fixture, session: &Value, scope: &Scope, turn: &str,
           command: &Command, text: &str) -> Vec<Value> {
    let worker = Preparing::new(fixture, session, scope, turn);
    let deadline = Instant::now() + Duration::from_secs(7);
    let mut seen = Vec::new();
    while !worker.finished() {
        let pending = ok(decode(fixture.registry.poll_inference(fixture.handle)))["pending"].clone();
        if !pending.is_null() {
            assert!(seen.len() < 4, "unexpected provider repair/role loop");
            let response = match pending["request"]["role"].as_str().unwrap() {
                "director" => json!({"commands":[command]}),
                "narrator" => json!({"text":text,"speaker":"narrator", "event_ids":pending["request"]["schema"]["properties"]["event_ids"]["const"]}),
                _ => panic!("unexpected external provider role"),
            };
            ok(decode(fixture.registry.respond_inference(fixture.handle, pending["ticket"].as_u64().unwrap(),
                &serde_json::to_vec(&response).unwrap())));
            seen.push(pending);
        }
        assert!(Instant::now() < deadline, "bounded actual prepare expired");
        thread::sleep(Duration::from_millis(1));
    }
    let terminal = ok(worker.finish());
    assert_eq!(terminal["phase"], "ready", "actual external preparation: {terminal}");
    assert_eq!(seen.len(), 2);
    assert_eq!(seen[0]["request"]["role"], "director");
    assert_eq!(seen[1]["request"]["role"], "narrator");
    assert!(seen[1]["ticket"].as_u64().unwrap() > seen[0]["ticket"].as_u64().unwrap());
    for pending in &seen {
        let request = &pending["request"];
        let keys: BTreeSet<_> = request.as_object().unwrap().keys().map(String::as_str).collect();
        assert_eq!(keys, ["version","role","prompt","schema","threads","context_tokens","max_tokens"].into());
        assert_eq!(request["version"], 1);
        assert_eq!(request["threads"], 4);
        assert_eq!(request["context_tokens"], 4096);
        assert_eq!(request["max_tokens"], if request["role"] == "director" {350} else {220});
        assert!(serde_json::to_vec(request).unwrap().len() <= 32768);
    }
    seen
}

fn commit(fixture: &Fixture, session: &Value, before: &Engine, turn: &str) -> Receipt {
    let committed = ok(fixture.call(op(session, before.scope(), "commit", turn)));
    assert_eq!(committed["phase"], "committed");
    let receipt: Receipt = serde_json::from_value(committed["receipt"].clone()).unwrap();
    let after = fixture.engine(before.scope());
    assert_eq!(after.canonical_records().len(), before.canonical_records().len() + 1);
    assert_eq!(after.recorded(receipt.request()).unwrap(), Some(receipt.clone()));
    receipt
}

fn assert_recipe(before: &Engine, receipt: &Receipt, seen: &[Value]) -> Value {
    let record = receipt.play().unwrap();
    let authored = before.seed().initial_world.is_some();
    let version = if authored {2} else {1};
    // These are contract literals, not a policy copied out of an untrusted reply.
    assert_eq!(record.scene.as_ref().map(|scene| scene.version), Some(version), "actual Android owner must choose a concrete scene recipe");
    assert_eq!(record.policy, if authored {"grounded-prose-v2.8-authored-scene-frame-v2"} else {"grounded-prose-v2.7-scene-frame-whole-evidence-words-v1"});
    assert_eq!(record.prompt_version, if authored {"locallore-play-v2.11-authored-scene-frame-v2"} else {"locallore-play-v2.9-scene-frame-v1"});
    assert_eq!(record.profile, profile());
    assert_eq!(record.context_policy, Some(PlayContextPolicy::StateRelevantMemoryV1));
    let (frame, frame_bytes, prompt, schema) = if authored {
        let stage = before.stage_authored_scene_play_v2(receipt.request(), receipt.proposal(), &|| false).unwrap();
        let bound = before.bind_authored_scene_play_v2(stage, AuthoredSceneRecipeV2::Memory(PlayContextPolicy::StateRelevantMemoryV1), &|| false).unwrap();
        let rendered = authored_scene_narration::render_authored_scene_narrator_v2(&bound, &profile(), &|| false).unwrap();
        (serde_json::to_value(bound.scene_frame()).unwrap(), serde_json::to_vec(bound.scene_frame()).unwrap(), rendered.prompt().to_owned(), rendered.schema().clone())
    } else {
        let stage = before.stage_scene_play_v1(receipt.request(), receipt.proposal(), &|| false).unwrap();
        let bound = before.bind_scene_play_v1(stage, SceneRecipeV1::Memory(PlayContextPolicy::StateRelevantMemoryV1), &|| false).unwrap();
        let rendered = scene_narration::render_scene_narrator_v1(&bound, &profile(), &|| false).unwrap();
        (serde_json::to_value(bound.scene_frame()).unwrap(), serde_json::to_vec(bound.scene_frame()).unwrap(), rendered.prompt().to_owned(), rendered.schema().clone())
    };
    assert_eq!(record.scene.as_ref().unwrap().frame_sha256, sha256(&frame_bytes));
    assert_eq!(seen[1]["request"]["prompt"], prompt);
    assert_eq!(seen[1]["request"]["schema"], schema);
    assert!(prompt.contains(std::str::from_utf8(&frame_bytes).unwrap()));
    assert_eq!(frame["scope"], json!(before.scope()));
    assert_eq!(frame["before_revision"], before.revision());
    assert_eq!(frame["after_revision"], receipt.events().last().unwrap().sequence());
    for secret in [LOCAL_DESCRIPTION, REMOTE_DESCRIPTION, NPC, BELIEF, REASON, UNRELATED] {
        assert!(!frame.to_string().contains(secret));
    }
    frame
}

fn generate(fixture: &Fixture, scope: &Scope, turn: &str, command: Command, text: &str) -> (Receipt, Vec<Value>, Value) {
    let before = fixture.engine(scope);
    let session = fixture.resume(scope);
    let request = request(&before, turn, &command);
    assert_eq!(ok(fixture.call(json!({"op":"free_text","session":session["session"],"request":request})))["phase"], "queued");
    let seen = prepare(fixture, &session, scope, turn, &command, text);
    unchanged(&fixture.engine(scope), &before);
    let receipt = commit(fixture, &session, &before, turn);
    let frame = assert_recipe(&before, &receipt, &seen);
    assert!(!receipt.play().unwrap().fallback);
    assert_eq!(receipt.narration(), text);
    (receipt, seen, frame)
}

#[test]
fn one_actual_android_owner_alternates_starter_authored_starter_and_reopens_without_inference() {
    let mut fixture = Fixture::new();
    let handle = fixture.handle;
    let mut saved = Vec::new();
    let mut last_ticket = 0;
    for (scope, turn, text) in [(fixture.starter.clone(), "starter-first", "You pause."),
        (fixture.authored.clone(), "authored-middle", "You pause at Copper Orchard."),
        (fixture.starter.clone(), "starter-again", "You pause.")] {
        let (receipt, seen, frame) = generate(&fixture, &scope, turn, Command::Wait { ticks: 1 }, text);
        assert_eq!(fixture.handle, handle);
        assert!(seen[0]["ticket"].as_u64().unwrap() > last_ticket);
        last_ticket = seen[1]["ticket"].as_u64().unwrap();
        if scope == fixture.authored {
            assert_eq!(frame["location_label"]["name"], "Copper Orchard");
            let prompt = seen[1]["request"]["prompt"].as_str().unwrap();
            for secret in [LOCAL_DESCRIPTION, REMOTE_NAME, REMOTE_DESCRIPTION, NPC, BELIEF, REASON, UNRELATED] { assert!(!prompt.contains(secret)); }
        }
        saved.push((scope, receipt));
    }
    fixture.reopen();
    assert!(fixture.handle > handle);
    for (scope, receipt) in saved {
        let before = fixture.engine(&scope);
        let session = fixture.resume(&scope);
        let retry = ok(fixture.call(json!({"op":"free_text","session":session["session"],"request":receipt.request()})));
        assert_eq!(retry["phase"], "committed");
        assert_eq!(retry["receipt"], json!(receipt));
        assert_eq!(ok(fixture.call(op(&session, &scope, "prepare", &receipt.request().turn))), retry);
        assert_eq!(ok(decode(fixture.registry.poll_inference(fixture.handle)))["pending"], Value::Null);
        assert_eq!(ok(fixture.call(op(&session, &scope, "commit", &receipt.request().turn))), retry);
        unchanged(&fixture.engine(&scope), &before);
    }
}

#[test]
fn actual_corrected_domain2_uses_authored_memory_and_rediscovery_omits_untyped_label() {
    let fixture = Fixture::new();
    let before_parent = fixture.engine(&fixture.authored);
    assert_eq!(fixture.engine(&fixture.corrected).domain_version(), 2);
    let (_, seen, remembered) = generate(&fixture, &fixture.corrected, "remember-original",
        Command::Wait { ticks: 1 }, "You pause at Copper Orchard.");
    assert_eq!(remembered["location_label"]["name"], "Copper Orchard");
    let prompt = seen[1]["request"]["prompt"].as_str().unwrap();
    for secret in [CORRECTED, REASON, LOCAL_DESCRIPTION, NPC, BELIEF, UNRELATED] { assert!(!prompt.contains(secret)); }
    let (_, seen, rediscovered) = generate(&fixture, &fixture.corrected, "rediscover-correction",
        Command::Discover { fact: fixture.local_fact.clone() }, "You pause.");
    assert!(rediscovered["location_label"].is_null());
    assert!(seen[1]["request"]["prompt"].as_str().unwrap().contains(CORRECTED));
    assert!(!seen[1]["request"]["prompt"].as_str().unwrap().contains(REASON));
    let (_, seen, later) = generate(&fixture, &fixture.corrected, "remember-new-value",
        Command::Wait { ticks: 1 }, "You pause.");
    assert!(later["location_label"].is_null());
    assert!(!seen[1]["request"]["prompt"].as_str().unwrap().contains(CORRECTED));
    unchanged(&fixture.engine(&fixture.authored), &before_parent);
}

#[test]
fn movement_does_not_grant_destination_label_but_real_discovery_preserves_its_source() {
    let fixture = Fixture::new();
    let (_, seen, moved) = generate(&fixture, &fixture.authored, "move-without-label",
        Command::Move { to: fixture.remote.clone() }, "You pause.");
    assert_eq!(moved["location"], fixture.remote);
    assert!(moved["location_label"].is_null());
    assert!(!seen[1]["request"]["prompt"].as_str().unwrap().contains(REMOTE_NAME));
    let (receipt, seen, discovered) = generate(&fixture, &fixture.authored, "discover-label",
        Command::Discover { fact: fixture.remote_fact.clone() }, "You pause.");
    assert_eq!(discovered["location_label"]["name"], REMOTE_NAME);
    assert_eq!(discovered["location_label"]["fact_id"], fixture.remote_fact);
    assert_eq!(discovered["location_label"]["observation"]["kind"], "event");
    assert_eq!(discovered["location_label"]["observation"]["source"]["sequence"], receipt.events()[0].sequence());
    assert!(seen[1]["request"]["prompt"].as_str().unwrap().contains(REMOTE_DESCRIPTION), "accepted discovery remains legitimate evidence");
    for secret in [NPC, BELIEF, REASON, UNRELATED] { assert!(!seen[1]["request"]["prompt"].as_str().unwrap().contains(secret)); }
}

#[test]
fn foreign_cancelled_and_closed_tickets_cannot_deliver_or_append_and_workers_are_joined() {
    let mut fixture = Fixture::new();
    let scope = fixture.authored.clone();
    let before = fixture.engine(&scope);
    let session = fixture.resume(&scope);
    let cancel_request = request(&before, "cancel-scene", &Command::Wait { ticks: 1 });
    ok(fixture.call(json!({"op":"free_text","session":session["session"],"request":cancel_request})));
    let worker = Preparing::new(&fixture, &session, &scope, "cancel-scene");
    let pending = worker.pending();
    let ticket = pending["ticket"].as_u64().unwrap();
    let foreign = fixture.registry.open_local(&fixture.database, &serde_json::to_vec(&profile()).unwrap()).unwrap();
    let foreign_response = decode(fixture.registry.respond_inference(foreign, ticket, b"{}"));
    fixture.registry.close(foreign);
    let cancellation = fixture.call(op(&session, &scope, "cancel", "cancel-scene"));
    let terminal = worker.finish();
    assert_eq!(foreign_response["error"], "InvalidTicket");
    assert_eq!(ok(cancellation)["phase"], "cancelled");
    assert_eq!(ok(terminal)["phase"], "cancelled");
    assert_eq!(decode(fixture.registry.respond_inference(fixture.handle, ticket, b"late"))["error"], "InvalidTicket");
    unchanged(&fixture.engine(&scope), &before);
    let close_request = request(&before, "close-scene", &Command::Wait { ticks: 1 });
    ok(fixture.call(json!({"op":"free_text","session":session["session"],"request":close_request})));
    let worker = Preparing::new(&fixture, &session, &scope, "close-scene");
    let next = worker.pending()["ticket"].as_u64().unwrap();
    let old_handle = fixture.handle;
    fixture.registry.close(old_handle);
    let terminal = worker.finish();
    assert!(next > ticket);
    assert_eq!(terminal["error"], "Closed");
    assert_eq!(decode(fixture.registry.poll_inference(old_handle))["error"], "InvalidHandle");
    assert_eq!(decode(fixture.registry.respond_inference(old_handle, next, b"late"))["error"], "InvalidHandle");
    fixture.reopen();
    assert!(fixture.handle > old_handle);
    unchanged(&fixture.engine(&scope), &before);
}

#[test]
fn ready_scene_candidates_are_transient_and_a_stale_competitor_cannot_append() {
    let fixture = Fixture::new();
    let scope = fixture.authored.clone();
    let before = fixture.engine(&scope);
    let session = fixture.resume(&scope);
    let command = Command::Wait { ticks: 1 };
    for turn in ["winner", "stale-loser"] {
        let request = request(&before, turn, &command);
        ok(fixture.call(json!({"op":"free_text","session":session["session"],"request":request})));
    }
    let first = prepare(&fixture, &session, &scope, "winner", &command, "You pause at Copper Orchard.");
    unchanged(&fixture.engine(&scope), &before);
    let second = prepare(&fixture, &session, &scope, "stale-loser", &command, "You pause at Copper Orchard.");
    unchanged(&fixture.engine(&scope), &before);
    assert_eq!(decode(fixture.registry.respond_inference(fixture.handle, first[1]["ticket"].as_u64().unwrap(), b"late"))["error"], "InvalidTicket");
    assert!(second[0]["ticket"].as_u64().unwrap() > first[1]["ticket"].as_u64().unwrap());
    let receipt = commit(&fixture, &session, &before, "winner");
    let committed = fixture.engine(&scope);
    let stale = ok(fixture.call(op(&session, &scope, "commit", "stale-loser")));
    assert_eq!(stale["phase"], "stale");
    unchanged(&fixture.engine(&scope), &committed);
    assert_recipe(&before, &receipt, &first);
}
