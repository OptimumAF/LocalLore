// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Source-only frozen D08.01/.02/.05 / M08.04/.06 authorization regressions.
//! Root registers this as a child of archive_commands.rs and implements its
//! private authorize_export(&Host, &str, &Scope, u64) -> Result<(), String>.
//! That helper DOES NOT EXIST at this freeze; all tests UNCOMPILED/UNRUN.
//! Intended production seam: actual Host inspection_query(Query2, exact live
//! session/scope/head, Omniscient, Profiles, limit1), not legacy Full construction.
//! Command after Root registration/helper implementation:
//! cargo test --locked --offline -p locallore-desktop-spike --bin locallore-desktop-spike archive_commands::archive_authorization_tests:: -- --nocapture --test-threads=1
//! Real Store/Host and synthetic denied provider only. No native IPC/WebView,
//! model-quality, device or Android corrected-timeline-opening claim. Local
//! synthetic TEMP evidence is retained; no default save is read or modified.

use locallore::{
    author_correction::{AuthorCorrectionInputV1, AuthorCorrectionOperationV1},
    contracts::{Command, Error, Intent, Scope, Seed},
    engine::Engine,
    host::Host,
    inference::{Cancellation, GenerationRequest, InferenceProvider},
    inspection::ExportMode,
    inspection_query::{Observer, Privacy, Query, View},
    play::PlayProfile,
};
use locallore_storage::Store;
use serde_json::{json, Value};
use std::{
    path::PathBuf,
    sync::{atomic::{AtomicU64, AtomicUsize, Ordering}, Arc},
    task::Poll,
};

const A: &str = "SYNTHETIC_AUTH_OBSERVED_A";
const B: &str = "SYNTHETIC_AUTH_CORRECTED_WORLD_B";
const REASON: &str = "SYNTHETIC_AUTH_PRIVATE_REASON";
static NEXT: AtomicU64 = AtomicU64::new(0);

#[derive(Clone, Default)]
struct Probe {
    factories: Arc<AtomicUsize>,
    polls: Arc<AtomicUsize>,
}
struct DeniedProvider(Probe);
impl InferenceProvider for DeniedProvider {
    fn poll(&mut self, _: &GenerationRequest, _: &Cancellation) -> Poll<Result<Vec<u8>, Error>> {
        self.0.polls.fetch_add(1, Ordering::SeqCst);
        Poll::Ready(Err(Error::Provider))
    }
}
impl Probe {
    fn attach(&self, host: &Host) {
        let probe = self.clone();
        host.configure_fixture_provider(PlayProfile {
            id: "synthetic-archive-authorization".into(), model_sha256: "a".repeat(64),
            runtime_revision: "b".repeat(40), template_sha256: "c".repeat(64),
            worker_sha256: "d".repeat(64), profile_manifest_sha256: "e".repeat(64),
            context_tokens: 4096, director_tokens: 350, narrator_tokens: 220,
            deadline_ms: 5000, repair_limit: 1,
        }, Arc::new(move || {
            probe.factories.fetch_add(1, Ordering::SeqCst);
            Box::new(DeniedProvider(probe.clone()))
        })).unwrap();
    }
    fn untouched(&self) {
        assert_eq!(self.factories.load(Ordering::SeqCst), 0);
        assert_eq!(self.polls.load(Ordering::SeqCst), 0);
    }
}

fn seed(story: &str) -> Seed {
    let actor = |name: &str, location: &str| json!({"name":name,"location":location,"alive":true,
        "energy":2,"abilities":{},"attributes":{},"injuries":[],"affiliations":[],"goals":[]});
    serde_json::from_value(json!({"version":1,"id":"archive-auth-v1",
        "scope":{"story":story,"branch":"main"},"profile":"fantasy_v1","player":"player",
        "locations":["quay","tower"],"routes":[],
        "actors":{"player":actor("Rowan","quay"),"mira":actor("Mira","quay"),"sable":actor("Sable","tower")},
        "items":{},"abilities":{},"facts":{"relic-location":{"proposition":A,"discoverable_at":"quay","known_by":["mira"]}},
        "relationships":[],"story_time":100,"beliefs":[],"commitments":{}})).unwrap()
}
fn commit(store: &mut Store, scope: &Scope, key: &str, command: Command) {
    let engine = store.resume(scope).unwrap().engine;
    let request = engine.request(key, Intent::Actions(vec![command]));
    let receipt = engine.preview(&request, &Engine::proposal(&request).unwrap()).unwrap();
    store.begin_turn(&request).unwrap();
    store.commit_prepared(&receipt).unwrap();
}
fn call(host: &Host, command: Value) -> Value {
    host.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
}
fn resume(host: &Host, scope: &Scope) -> String {
    let reply = call(host, json!({"op":"resume","scope":scope}));
    assert_eq!(reply["status"], "ok", "{reply}");
    reply["data"]["session"].as_str().unwrap().to_owned()
}
fn profiles(scope: &Scope, head: u64, observer: Observer) -> Query {
    Query { version: 2, scope: scope.clone(), expected_head: head, at_revision: None,
        observer, view: View::Profiles, cursor: None, limit: 1, search: String::new() }
}
fn equivalent(actual: &Engine, expected: &Engine) {
    // Privacy-bearing native types intentionally need no Debug/Deserialize.
    assert!(actual.seed() == expected.seed());
    assert!(actual.scope() == expected.scope());
    assert!(actual.revision() == expected.revision());
    assert!(actual.domain_version() == expected.domain_version());
    assert!(actual.canonical_records() == expected.canonical_records());
    assert!(actual.canonical_bytes() == expected.canonical_bytes());
    assert!(actual.accepted_history_basis().unwrap() == expected.accepted_history_basis().unwrap());
    for actor in ["player", "mira", "sable"] {
        assert!(actual.character_context_v2(actor, actual.scope(), actual.revision()).unwrap() ==
            expected.character_context_v2(actor, expected.scope(), expected.revision()).unwrap());
        assert!(actual.actor_receipts_v2(actor, actual.scope(), actual.revision()).unwrap() ==
            expected.actor_receipts_v2(actor, expected.scope(), expected.revision()).unwrap());
    }
}
fn privacy(engine: &Engine) {
    let scope = engine.scope();
    let head = engine.revision();
    assert_eq!(engine.effective_fact("relic-location").unwrap().proposition, B);
    for actor in ["player", "mira"] {
        assert_eq!(engine.observed_facts(actor, scope, head).unwrap()["relic-location"].proposition, A);
        let context = serde_json::to_string(&engine.character_context_v2(actor, scope, head).unwrap()).unwrap();
        assert!(context.contains(A));
        assert!(!context.contains(B));
        assert!(!context.contains(REASON));
    }
    assert!(!engine.observed_facts("sable", scope, head).unwrap().contains_key("relic-location"));
}
struct Fixture {
    path: PathBuf,
    root: Scope,
    child: Scope,
    foreign: Scope,
}
impl Fixture {
    fn new() -> Self {
        let directory = std::env::temp_dir().join(format!("locallore-archive-auth-{}-{}-{}",
            std::process::id(), std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)));
        std::fs::create_dir(&directory).unwrap();
        let path = directory.join("source.sqlite");
        let mut store = Store::open_application(&path).unwrap();
        let initial = seed("archive-auth");
        let root = initial.scope.clone();
        store.create_story("Synthetic selected archive authorization", initial).unwrap();
        commit(&mut store, &root, "observe-a", Command::Discover { fact: "relic-location".into() });
        let input = AuthorCorrectionInputV1 {
            version: 1, parent: root.clone(), expected_parent_revision: 1, fork_revision: 1,
            child_branch: "corrected".into(), reason: REASON.into(),
            operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
                fact: "relic-location".into(), expected_proposition: A.into(), replacement: B.into(),
            },
        };
        let prepared = store.prepare_author_correction(&input, &|| false).unwrap();
        let child = store.apply_author_correction(&prepared, &|| false).unwrap().scope;
        let control = seed("foreign-auth-control");
        let foreign = control.scope.clone();
        store.create_story("Unrelated synthetic authorization control", control).unwrap();
        commit(&mut store, &foreign, "keep-foreign", Command::Wait { ticks: 1 });
        assert_eq!(store.resume(&root).unwrap().engine.domain_version(), 1);
        let corrected = store.resume(&child).unwrap().engine;
        assert_eq!(corrected.domain_version(), 2);
        assert_eq!(corrected.revision(), 2);
        privacy(&corrected);
        drop(store);
        Self { path, root, child, foreign }
    }
    fn engine(&self, scope: &Scope) -> Engine {
        Store::open_read_only(&self.path).unwrap().resume(scope).unwrap().engine
    }
    fn saved(&self) -> Vec<Engine> {
        [&self.root, &self.child, &self.foreign].into_iter().map(|scope| self.engine(scope)).collect()
    }
    fn unchanged(&self, before: &[Engine]) {
        for expected in before { equivalent(&self.engine(expected.scope()), expected); }
        privacy(&self.engine(&self.child));
    }
    fn host(&self, grant: bool) -> (Host, Probe) {
        let host = locallore_workspace::open(&self.path, grant).unwrap();
        let probe = Probe::default();
        probe.attach(&host);
        (host, probe)
    }
}

#[test]
fn granted_actual_d1_and_corrected_d2_sessions_authorize_without_legacy_full_capture() {
    let fixture = Fixture::new();
    let before = fixture.saved();
    let (host, probe) = fixture.host(true);
    for (scope, head) in [(&fixture.root, 1), (&fixture.child, 2)] {
        let session = resume(&host, scope);
        // Actual public Query2 establishes feasibility; it is not a competing
        // authorization implementation. The private helper must call Host.
        let page = host.inspection_query(&session, &profiles(scope, head, Observer::Omniscient)).unwrap();
        assert!(page.privacy == Privacy::PrivateOmniscient);
        assert!(page.rows.len() <= 1);
        super::authorize_export(&host, &session, scope, head).unwrap();
        let generation = host.generation_snapshot(&session, scope, head, &|| false).unwrap();
        equivalent(&generation.engine, &fixture.engine(scope));
    }
    let child_session = resume(&host, &fixture.child);
    let mut truth_query = profiles(&fixture.child, 2, Observer::Omniscient);
    truth_query.view = View::Knowledge;
    truth_query.limit = 64;
    let truth = serde_json::to_string(&host.inspection_query(&child_session, &truth_query).unwrap()).unwrap();
    assert!(truth.contains(B), "Granted inspection can read corrected world truth");
    // The narrow authorization fix must not claim the old inspection bundle
    // became a Domain2 exporter or require that unsupported builder to succeed.
    assert!(host.inspection_snapshot(&child_session, &fixture.child, 2, ExportMode::Full).err() == Some("Version".into()));
    fixture.unchanged(&before);
    probe.untouched();
}

#[test]
fn native_false_grant_denies_both_domains_without_granting_private_generation_knowledge() {
    let fixture = Fixture::new();
    let before = fixture.saved();
    let (host, probe) = fixture.host(false);
    for (scope, head) in [(&fixture.root, 1), (&fixture.child, 2)] {
        let session = resume(&host, scope);
        assert!(super::authorize_export(&host, &session, scope, head).err() == Some("Forbidden".into()));
        assert!(host.inspection_query(&session, &profiles(scope, head, Observer::Omniscient)).err() == Some("Forbidden".into()));
        let player_page = host.inspection_query(&session, &profiles(scope, head, Observer::Player)).unwrap();
        assert!(player_page.privacy == Privacy::PlayerVisible);
        let generation = host.generation_snapshot(&session, scope, head, &|| false).unwrap();
        equivalent(&generation.engine, &fixture.engine(scope));
    }
    fixture.unchanged(&before);
    probe.untouched();
}

#[test]
fn unknown_closed_and_cross_scope_sessions_never_authorize_a_selected_corrected_branch() {
    let fixture = Fixture::new();
    let before = fixture.saved();
    let (host, probe) = fixture.host(true);
    let root = resume(&host, &fixture.root);
    let child = resume(&host, &fixture.child);
    let foreign = resume(&host, &fixture.foreign);
    assert!(super::authorize_export(&host, "forged-session", &fixture.child, 2).err() == Some("Closed".into()));
    assert!(super::authorize_export(&host, &root, &fixture.child, 2).err() == Some("Scope".into()));
    assert!(super::authorize_export(&host, &child, &fixture.root, 1).err() == Some("Scope".into()));
    assert!(super::authorize_export(&host, &foreign, &fixture.child, 2).err() == Some("Scope".into()));
    let spoofed = Scope { story: fixture.foreign.story.clone(), branch: fixture.child.branch.clone() };
    assert!(super::authorize_export(&host, &child, &spoofed, 2).err() == Some("Scope".into()));
    let closed = call(&host, json!({"op":"close","session":child,"scope":fixture.child}));
    assert_eq!(closed["status"], "ok");
    assert!(super::authorize_export(&host, &child, &fixture.child, 2).err() == Some("Closed".into()));
    super::authorize_export(&host, &root, &fixture.root, 1).unwrap();
    fixture.unchanged(&before);
    probe.untouched();
}

#[test]
fn stale_selected_head_is_rejected_against_actual_durable_history_not_the_session_cache() {
    let fixture = Fixture::new();
    let (host, probe) = fixture.host(true);
    let root = resume(&host, &fixture.root);
    let child = resume(&host, &fixture.child);
    let before = fixture.saved();
    for (session, scope, head) in [(&root, &fixture.root, 1), (&child, &fixture.child, 2)] {
        assert!(super::authorize_export(&host, session, scope, head - 1).err() == Some("Stale".into()));
        assert!(super::authorize_export(&host, session, scope, head + 1).err() == Some("Stale".into()));
    }
    fixture.unchanged(&before);
    let mut writer = Store::open_application(&fixture.path).unwrap();
    commit(&mut writer, &fixture.child, "actual-later-head", Command::Wait { ticks: 1 });
    drop(writer);
    let advanced = fixture.saved();
    assert!(super::authorize_export(&host, &child, &fixture.child, 2).err() == Some("Stale".into()));
    super::authorize_export(&host, &child, &fixture.child, 3).unwrap();
    super::authorize_export(&host, &root, &fixture.root, 1).unwrap();
    fixture.unchanged(&advanced);
    probe.untouched();
}
