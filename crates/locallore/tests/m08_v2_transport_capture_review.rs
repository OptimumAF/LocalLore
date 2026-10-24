//! Actual Core/Host-library producer fixtures, not native IPC/render/model evidence.
#![cfg(feature = "host")]
use locallore::{
    author_correction::{AuthorCorrectionInputV1, AuthorCorrectionOperationV1},
    contracts::*,
    engine::Engine,
    host::{Host, Persistence, SavedTurn, WorkspaceSummary},
    inspection_query::{Observer, Query, View},
};
use serde_json::{json, Value};
use std::{
    collections::BTreeSet,
    fs::OpenOptions,
    io::Write,
    path::PathBuf,
    sync::{
        atomic::{AtomicUsize, Ordering},
        Arc, Mutex,
    },
};

const A: &str = "SYNTHETIC_OBSERVED_A";
const B: &str = "SYNTHETIC_PRIVATE_WORLD_B";
const REASON: &str = "SYNTHETIC_PRIVATE_AUTHOR_REASON";
const MAX_FIXTURE_BYTES: usize = 1024 * 1024;
const VIEWS: [View; 9] = [
    View::Profiles,
    View::History,
    View::Relationships,
    View::Knowledge,
    View::Promises,
    View::Provenance,
    View::TurnDiff,
    View::Summaries,
    View::RetrievalIndexes,
];

fn capture_fixture(encoded: &[u8]) {
    assert!(encoded.len() <= MAX_FIXTURE_BYTES);
    let Some(directory) = std::env::var_os("LOCALLORE_V2_FIXTURE_DIRECTORY") else {
        return;
    };
    let directory = PathBuf::from(directory);
    assert!(
        directory.is_absolute(),
        "fixture directory must be absolute"
    );
    assert!(
        std::fs::metadata(&directory).unwrap().is_dir(),
        "fixture directory must already exist"
    );
    // One fixed synthetic file, no overwrite, directory creation, arbitrary
    // app hook, runtime command or general-purpose file transport.
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(directory.join("v2-native-fixtures.json"))
        .expect("fixed synthetic fixture capture must not overwrite an existing file");
    file.write_all(encoded).unwrap();
}

struct ReadOnlySource {
    engine: Arc<Mutex<Engine>>,
    writes: Arc<AtomicUsize>,
}
impl ReadOnlySource {
    fn refuse<T>(&self) -> Result<T, String> {
        self.writes.fetch_add(1, Ordering::SeqCst);
        Err("Unsupported".into())
    }
}
impl Persistence for ReadOnlySource {
    fn location(&self) -> &str {
        "synthetic-core-host-transport-only"
    }
    fn list(&mut self) -> Result<Vec<WorkspaceSummary>, String> {
        Err("Unsupported".into())
    }
    fn create(&mut self) -> Result<Engine, String> {
        self.refuse()
    }
    fn validate_scope(&mut self, scope: &Scope) -> Result<(), String> {
        if self.engine.lock().unwrap().scope() == scope {
            Ok(())
        } else {
            Err("NotFound".into())
        }
    }
    fn resume(&mut self, scope: &Scope) -> Result<Engine, String> {
        let engine = self.engine.lock().unwrap();
        if engine.scope() == scope {
            Ok(engine.clone())
        } else {
            Err("NotFound".into())
        }
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

fn call(host: &Host, command: Value) -> Value {
    host.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
}
fn data(reply: &Value) -> &Value {
    assert_eq!(reply["version"], 1, "{reply}");
    assert_eq!(reply["status"], "ok", "{reply}");
    assert_eq!(reply.as_object().unwrap().len(), 3);
    reply.get("data").unwrap()
}
fn append(engine: &mut Engine, key: &str, intent: Intent) {
    let request = engine.request(key, intent);
    let proposal = Engine::proposal(&request).unwrap();
    let receipt = engine.preview(&request, &proposal).unwrap();
    engine.commit_prepared(&receipt).unwrap();
}
fn dialogue(engine: &mut Engine, text: &str) {
    let mut audience: BTreeSet<String> = ["mira".into()].into();
    if engine.seed().player != "player" {
        audience.insert("player".into());
    }
    append(
        engine,
        "same-turn",
        Intent::Dialogue {
            text: text.into(),
            audience,
        },
    );
}
fn scenarios(custom: bool) -> Vec<(String, Engine)> {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    if custom {
        // Keep the old actor named `player` as an NPC. All original seed refs
        // remain valid; a new actual player is selected by normal Seed validation.
        let actor = seed.actors["player"].clone();
        seed.actors.insert("hero".into(), actor);
        seed.player = "hero".into();
        seed.scope.story = "custom-quay".into();
    }
    let player = seed.player.clone();
    let fact = seed.facts.get_mut("relic-location").unwrap();
    fact.proposition = A.into();
    fact.known_by.extend([player, "mira".into()]);
    seed.facts.get_mut("beacon-mark").unwrap().discoverable_at = Some("quay".into());
    let mut parent = Engine::new(seed).unwrap();
    dialogue(&mut parent, "ANCESTOR_INPUT \\\"雪🙂");
    let input = AuthorCorrectionInputV1 {
        version: 1,
        parent: parent.scope().clone(),
        expected_parent_revision: parent.revision(),
        fork_revision: parent.revision(),
        child_branch: "authored-child".into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(),
            expected_proposition: A.into(),
            replacement: B.into(),
        },
        reason: REASON.into(),
    };
    let prepared = parent.prepare_author_correction(&input, &|| false).unwrap();
    let mut child = parent
        .apply_author_correction(&prepared, &|| false)
        .unwrap()
        .engine;
    dialogue(&mut child, "CHILD_INPUT <literal> \\\"雪🙂");
    append(
        &mut child,
        "child-discovery",
        Intent::Actions(vec![Command::Discover {
            fact: "beacon-mark".into(),
        }]),
    );
    append(
        &mut parent,
        "later-parent",
        Intent::Actions(vec![Command::Wait { ticks: 1 }]),
    );
    let prefix = if custom { "custom" } else { "default" };
    vec![
        (format!("{prefix}-domain1"), parent),
        (format!("{prefix}-domain2"), child),
    ]
}
fn observers(engine: &Engine) -> Vec<Observer> {
    let mut result = vec![
        Observer::Player,
        Observer::Character { id: "mira".into() },
        Observer::Character {
            id: engine.seed().player.clone(),
        },
        Observer::Omniscient,
    ];
    if engine.seed().player != "player" {
        result.push(Observer::Character {
            id: "player".into(),
        });
    }
    result
}
fn request(engine: &Engine, observer: Observer, view: View) -> Query {
    Query {
        version: 2,
        scope: engine.scope().clone(),
        expected_head: engine.revision(),
        at_revision: None,
        observer,
        view,
        cursor: None,
        limit: 64,
        search: String::new(),
    }
}
fn capture_page(host: &Host, session: &str, query: &Query, label: &str) -> Value {
    let reply = call(
        host,
        json!({"op":"inspection_query","session":session,"query":query}),
    );
    let page = data(&reply);
    assert_eq!(page["version"], 2);
    assert_eq!(page["scope"], json!(query.scope));
    assert_eq!(page["head"], query.expected_head);
    assert_eq!(
        page["revision"],
        query.at_revision.unwrap_or(query.expected_head)
    );
    assert_eq!(page["observer"], json!(query.observer));
    assert_eq!(page["view"], json!(query.view));
    assert!(page["rows"].as_array().unwrap().len() <= usize::from(query.limit));
    assert!(serde_json::to_vec(page).unwrap().len() <= 65_536);
    json!({"label":label,"query":query,"reply":reply})
}
fn page_rows(capture: &Value) -> &[Value] {
    capture["reply"]["data"]["rows"].as_array().unwrap()
}
fn full_page<'a>(pages: &'a [Value], observer: &Observer, view: View) -> &'a Value {
    pages
        .iter()
        .find(|p| {
            p["label"] == "current"
                && p["query"]["observer"] == json!(observer)
                && p["query"]["view"] == json!(view)
        })
        .unwrap()
}
fn inspect_oracles(engine: &Engine, pages: &[Value]) {
    for lens in observers(engine) {
        let history = full_page(pages, &lens, View::History);
        let markers: Vec<_> = page_rows(history)
            .iter()
            .filter(|r| r["kind"] == "author_correction")
            .collect();
        let expected = usize::from(engine.domain_version() == 2 && lens == Observer::Player);
        assert_eq!(markers.len(), expected);
        for marker in markers {
            assert_eq!(*marker, json!({"kind":"author_correction","revision":2}));
        }
        let encoded = serde_json::to_string(history).unwrap();
        assert!(!encoded.contains(REASON));
        if lens != Observer::Omniscient {
            assert!(!encoded.contains(B));
        }
        if matches!(&lens, Observer::Character { id } if id != &engine.seed().player) {
            assert!(!encoded.contains("scoped_message"));
        }
        let knowledge = full_page(pages, &lens, View::Knowledge);
        let fact = page_rows(knowledge)
            .iter()
            .find(|r| r["kind"] == "knowledge" && r["id"] == "relic-location")
            .unwrap();
        assert_eq!(
            fact["text"],
            if engine.domain_version() == 2 && lens == Observer::Omniscient {
                B
            } else {
                A
            }
        );
        if engine.domain_version() == 2 && lens != Observer::Omniscient {
            assert_eq!(fact["origin"], "known_as_observed");
        }
    }
    if engine.domain_version() == 2 {
        let own = full_page(pages, &Observer::Player, View::History);
        let messages: Vec<_> = page_rows(own)
            .iter()
            .filter(|r| r["kind"] == "scoped_message" && r["turn"] == "same-turn")
            .collect();
        assert_eq!(messages.len(), 4);
        let identities: BTreeSet<_> = messages
            .iter()
            .map(|r| {
                (
                    r["original_scope"].to_string(),
                    r["message_kind"].to_string(),
                )
            })
            .collect();
        assert_eq!(identities.len(), 4);
        assert!(messages
            .iter()
            .any(|r| r["original_scope"]["branch"] == "main"));
        assert!(messages
            .iter()
            .any(|r| r["original_scope"] == json!(engine.scope())));
        assert!(!serde_json::to_string(own).unwrap().contains("later-parent"));
        let historical = pages
            .iter()
            .find(|p| {
                p["label"] == "historical"
                    && p["query"]["observer"] == json!(Observer::Player)
                    && p["query"]["view"] == "history"
            })
            .unwrap();
        assert!(page_rows(historical)
            .iter()
            .all(|r| r["kind"] != "author_correction" && r["turn"] != "child-discovery"));
    }
    // Sources must really include actual scoped event references, not only seed
    // rows that could accidentally leave the scoped-source decoder unexercised.
    assert!(pages
        .iter()
        .any(|p| serde_json::to_string(&p["reply"]["data"])
            .unwrap()
            .contains("\"kind\":\"scoped_event\"")));
}

fn capture_case(id: &str, engine: &Engine) -> Value {
    let shared = Arc::new(Mutex::new(engine.clone()));
    let writes = Arc::new(AtomicUsize::new(0));
    let host = Host::with_persistence(
        true,
        Box::new(ReadOnlySource {
            engine: shared.clone(),
            writes: writes.clone(),
        }),
    );
    let before = engine.accepted_history_basis().unwrap();
    let canonical = serde_json::to_vec(engine.canonical_records()).unwrap();
    let resumed = call(&host, json!({"op":"resume","scope":engine.scope()}));
    let session = data(&resumed)["session"].as_str().unwrap();
    let snapshot = call(
        &host,
        json!({"op":"play_snapshot_v2","session":session,"scope":engine.scope(),"expected_revision":engine.revision()}),
    );
    let thin = data(&snapshot);
    assert_eq!(thin["version"], 2);
    assert_eq!(thin["domain_version"], engine.domain_version());
    assert_eq!(thin["player"]["observer"], engine.seed().player);
    assert_eq!(
        thin["player"]["self_state"],
        json!(engine.state().actors[&engine.seed().player])
    );
    let text = serde_json::to_string(thin).unwrap();
    for private in [
        A,
        B,
        REASON,
        "truth_overrides",
        "observed_overrides",
        "receipts",
    ] {
        assert!(!text.contains(private));
    }
    let mut pages = vec![];
    for lens in observers(engine) {
        for view in VIEWS {
            pages.push(capture_page(
                &host,
                session,
                &request(engine, lens.clone(), view),
                "current",
            ));
        }
        for view in [View::History, View::Knowledge, View::TurnDiff] {
            let mut query = request(engine, lens.clone(), view);
            query.at_revision = Some(1);
            pages.push(capture_page(&host, session, &query, "historical"));
        }
        let full = full_page(&pages, &lens, View::History).clone();
        let mut query = request(engine, lens.clone(), View::History);
        query.limit = 1;
        let mut combined = vec![];
        for _ in 0..64 {
            let captured = capture_page(&host, session, &query, "paged");
            assert_eq!(
                captured["reply"]["data"]["total"],
                full["reply"]["data"]["total"]
            );
            combined.extend_from_slice(page_rows(&captured));
            let cursor = captured["reply"]["data"]["next_cursor"]
                .as_str()
                .map(str::to_owned);
            pages.push(captured);
            query.cursor = cursor;
            if query.cursor.is_none() {
                break;
            }
        }
        assert!(query.cursor.is_none(), "bounded paging did not terminate");
        assert_eq!(combined, page_rows(&full));
        let mut search = request(engine, lens, View::Knowledge);
        search.search = REASON.into();
        let searched = capture_page(&host, session, &search, "private-reason-search");
        assert_eq!(searched["reply"]["data"]["total"], 0);
        pages.push(searched);
    }
    inspect_oracles(engine, &pages);
    let private_host = Host::with_persistence(
        false,
        Box::new(ReadOnlySource {
            engine: shared.clone(),
            writes: writes.clone(),
        }),
    );
    let resumed_private = call(&private_host, json!({"op":"resume","scope":engine.scope()}));
    let private_session = data(&resumed_private)["session"].as_str().unwrap();
    for observer in [
        Observer::Omniscient,
        Observer::Character { id: "mira".into() },
    ] {
        let reply = call(
            &private_host,
            json!({"op":"inspection_query","session":private_session,
            "query":request(engine, observer, View::Knowledge)}),
        );
        assert_eq!(reply["status"], "rejected");
        assert_eq!(reply["error"], "Forbidden");
    }
    assert_eq!(writes.load(Ordering::SeqCst), 0);
    assert_eq!(
        shared.lock().unwrap().accepted_history_basis().unwrap(),
        before
    );
    assert_eq!(
        serde_json::to_vec(shared.lock().unwrap().canonical_records()).unwrap(),
        canonical
    );
    json!({"id":id,"scope":engine.scope(),"head":engine.revision(),"domain_version":engine.domain_version(),
        "selected_player":engine.seed().player,"snapshot":snapshot,"pages":pages})
}

#[test]
fn actual_host_v2_transport_has_scoped_identity_private_lenses_and_stable_paging() {
    let engines = scenarios(false).into_iter().chain(scenarios(true));
    let cases: Vec<_> = engines
        .map(|(id, engine)| capture_case(&id, &engine))
        .collect();
    assert_eq!(cases.len(), 4);
    let fixture = json!({"version":1,"producer":"rust-core-host-library","cases":cases});
    let encoded = serde_json::to_vec(&fixture).unwrap();
    assert!(
        encoded.len() <= MAX_FIXTURE_BYTES,
        "synthetic fixture exceeds 1MiB"
    );
    capture_fixture(&encoded);
}
