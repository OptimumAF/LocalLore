//! Actual SQLite Store + workspace Host typed route; no fake persistence or model.
use locallore::{
    author_correction::*,
    contracts::*,
    engine::Engine,
    host::Host,
    inspection_query::{Observer, Query, View},
};
use locallore_storage::Store;
use serde_json::{json, Value};
use std::{
    path::PathBuf,
    sync::atomic::{AtomicU64, Ordering},
};

const A: &str = "SYNTHETIC_HOST_TYPED_A";
const B: &str = "SYNTHETIC_HOST_TYPED_PRIVATE_B";
const REASON: &str = "SYNTHETIC_HOST_TYPED_PRIVATE_REASON";
static NEXT: AtomicU64 = AtomicU64::new(0);
struct Fixture {
    directory: PathBuf,
    parent: Scope,
    child: Scope,
}
impl Fixture {
    fn new(custom: bool) -> Self {
        let directory = std::env::temp_dir().join(format!(
            "locallore-typed-v2-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&directory).unwrap();
        let mut seed: Seed =
            serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
        if custom {
            seed.actors
                .insert("hero".into(), seed.actors["player"].clone());
            seed.player = "hero".into();
            for item in seed.items.values_mut() {
                if item.owner == "player" {
                    item.owner = "hero".into();
                }
            }
        }
        let fact = seed.facts.get_mut("relic-location").unwrap();
        fact.proposition = A.into();
        fact.known_by = ["mira".into()].into();
        fact.discoverable_at = Some("quay".into());
        let parent = seed.scope.clone();
        let child = Scope {
            story: parent.story.clone(),
            branch: "host-typed-child".into(),
        };
        let fixture = Self {
            directory,
            parent,
            child,
        };
        let mut store = fixture.store();
        store
            .create_story("Synthetic typed continuation", seed)
            .unwrap();
        let engine = store.resume(&fixture.parent).unwrap().engine;
        let request = engine.request(
            "actual-discovery",
            Intent::Actions(vec![Command::Discover {
                fact: "relic-location".into(),
            }]),
        );
        let approved = engine
            .preview(&request, &Engine::proposal(&request).unwrap())
            .unwrap();
        store.begin_turn(&request).unwrap();
        store.commit_prepared(&approved).unwrap();
        let input = AuthorCorrectionInputV1 {
            version: 1,
            parent: fixture.parent.clone(),
            expected_parent_revision: 1,
            fork_revision: 1,
            child_branch: fixture.child.branch.clone(),
            operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
                fact: "relic-location".into(),
                expected_proposition: A.into(),
                replacement: B.into(),
            },
            reason: REASON.into(),
        };
        let plan = store.prepare_author_correction(&input, &|| false).unwrap();
        assert_eq!(
            store
                .apply_author_correction(&plan, &|| false)
                .unwrap()
                .scope,
            fixture.child
        );
        drop(store);
        fixture
    }
    fn path(&self) -> PathBuf {
        self.directory.join("synthetic.sqlite")
    }
    fn store(&self) -> Store {
        Store::open_application(&self.path()).unwrap()
    }
    fn engine(&self, scope: &Scope) -> Engine {
        Store::open_read_only(&self.path())
            .unwrap()
            .resume(scope)
            .unwrap()
            .engine
    }
}
impl Drop for Fixture {
    fn drop(&mut self) {
        assert!(self
            .directory
            .file_name()
            .unwrap()
            .to_str()
            .unwrap()
            .starts_with("locallore-typed-v2-"));
        if let Err(error) = std::fs::remove_dir_all(&self.directory) {
            if !std::thread::panicking() {
                panic!("owned synthetic cleanup: {error}");
            }
        }
    }
}
fn call(host: &Host, command: Value) -> Value {
    host.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
}
fn data(value: &Value) -> &Value {
    assert_eq!(value["status"], "ok", "{value}");
    &value["data"]
}
fn resume(host: &Host, scope: &Scope) -> String {
    data(&call(host, json!({"op":"resume","scope":scope})))["session"]
        .as_str()
        .unwrap()
        .into()
}
fn control(host: &Host, session: &str, request: &Request, op: &str) -> Value {
    call(
        host,
        json!({"op":op,"session":session,"scope":request.scope,"turn":request.turn}),
    )
}
fn submit(host: &Host, session: &str, request: &Request, mode: &str) -> Value {
    call(
        host,
        json!({"op":"submit","session":session,"request":request,"mode":mode}),
    )
}
fn private_oracle(engine: &Engine) {
    assert_eq!(
        engine.effective_fact("relic-location").unwrap().proposition,
        B
    );
    for actor in [&engine.seed().player[..], "mira"] {
        let context = engine
            .character_context_v2(actor, engine.scope(), engine.revision())
            .unwrap();
        assert_eq!(context.facts["relic-location"].proposition, A);
        let encoded = serde_json::to_string(&context).unwrap();
        assert!(!encoded.contains(B));
        assert!(!encoded.contains(REASON));
    }
    assert!(!engine
        .character_context_v2("sable", engine.scope(), engine.revision())
        .unwrap()
        .facts
        .contains_key("relic-location"));
}

#[test]
fn actual_workspace_typed_give_wait_commit_and_reopen_preserve_v2_and_inspection_isolation() {
    for custom in [false, true] {
        for grant in [false, true] {
            let fixture = Fixture::new(custom);
            let parent = fixture.engine(&fixture.parent);
            let host = locallore_workspace::open(&fixture.path(), grant).unwrap();
            let session = resume(&host, &fixture.child);
            let before = fixture.engine(&fixture.child);
            private_oracle(&before);
            let query = Query {
                version: 2,
                scope: fixture.child.clone(),
                expected_head: 2,
                at_revision: None,
                observer: Observer::Omniscient,
                view: View::Knowledge,
                cursor: None,
                limit: 64,
                search: String::new(),
            };
            if grant {
                let text = serde_json::to_string(&host.inspection_query(&session, &query).unwrap())
                    .unwrap();
                assert!(text.contains(B));
            } else {
                assert_eq!(
                    host.inspection_query(&session, &query).unwrap_err(),
                    "Forbidden"
                );
            }
            assert_eq!(
                fixture
                    .engine(&fixture.child)
                    .accepted_history_basis()
                    .unwrap(),
                before.accepted_history_basis().unwrap()
            );
            let mut committed = vec![];
            for (key, commands) in [
                (
                    "host-give",
                    vec![Command::Give {
                        item: "potion".into(),
                        to: "mira".into(),
                        quantity: 1,
                    }],
                ),
                ("host-wait", vec![Command::Wait { ticks: 1 }]),
            ] {
                let engine = fixture.engine(&fixture.child);
                let request = engine.request(key, Intent::Actions(commands));
                assert_eq!(
                    data(&submit(&host, &session, &request, "accepted"))["phase"],
                    "queued"
                );
                let prepared = control(&host, &session, &request, "prepare");
                assert_eq!(data(&prepared)["phase"], "ready", "{prepared}");
                assert_eq!(
                    fixture
                        .engine(&fixture.child)
                        .accepted_history_basis()
                        .unwrap(),
                    engine.accepted_history_basis().unwrap(),
                    "prepare must not commit"
                );
                let reply = control(&host, &session, &request, "commit");
                assert_eq!(data(&reply)["phase"], "committed", "{reply}");
                let receipt = data(&reply)["receipt"].clone();
                assert_eq!(receipt["request"], json!(request));
                let current = fixture.engine(&fixture.child);
                assert_eq!(
                    current.revision(),
                    request.expected_revision + receipt["events"].as_array().unwrap().len() as u64
                );
                assert!(matches!(
                    current.canonical_records().last().unwrap(),
                    CanonicalRecord::PlayV2(_)
                ));
                private_oracle(&current);
                assert_eq!(
                    data(&submit(&host, &session, &request, "accepted"))["receipt"],
                    receipt
                );
                assert_eq!(
                    data(&control(&host, &session, &request, "commit"))["receipt"],
                    receipt
                );
                committed.push((request, receipt));
            }
            let accepted = fixture.engine(&fixture.child);
            assert_eq!(accepted.state().items["potion"].owner, "mira");
            assert_eq!(
                fixture.engine(&fixture.parent).canonical_records(),
                parent.canonical_records()
            );
            assert_eq!(
                fixture.engine(&fixture.parent).canonical_bytes(),
                parent.canonical_bytes()
            );
            drop(host);
            let reopened = locallore_workspace::open(&fixture.path(), grant).unwrap();
            let new_session = resume(&reopened, &fixture.child);
            let restored = fixture.engine(&fixture.child);
            assert_eq!(restored.canonical_records(), accepted.canonical_records());
            assert_eq!(restored.canonical_bytes(), accepted.canonical_bytes());
            assert_eq!(
                restored.accepted_history_basis().unwrap(),
                accepted.accepted_history_basis().unwrap()
            );
            for (request, receipt) in committed {
                assert_eq!(
                    data(&submit(&reopened, &new_session, &request, "accepted"))["receipt"],
                    receipt
                );
                assert_eq!(
                    data(&control(&reopened, &new_session, &request, "prepare"))["receipt"],
                    receipt
                );
            }
        }
    }
}

#[test]
fn actual_host_queued_cancel_and_fake_failure_never_append_partial_v2_canon() {
    let fixture = Fixture::new(false);
    let host = locallore_workspace::open(&fixture.path(), false).unwrap();
    let session = resume(&host, &fixture.child);
    let before = fixture.engine(&fixture.child);
    for (key, mode, phase, error) in [
        ("cancelled", "cancelled", "cancelled", "Cancelled"),
        ("failed", "failed", "failed", "Provider"),
        ("malformed", "malformed", "failed", "Malformed"),
    ] {
        let request = before.request(key, Intent::Actions(vec![Command::Wait { ticks: 1 }]));
        assert_eq!(
            data(&submit(&host, &session, &request, mode))["phase"],
            "queued"
        );
        let reply = control(&host, &session, &request, "prepare");
        assert_eq!(data(&reply)["phase"], phase, "{reply}");
        assert_eq!(data(&reply)["error"], error);
        assert!(data(&reply)["receipt"].is_null());
    }
    let queued = before.request(
        "explicit-queued-cancel",
        Intent::Actions(vec![Command::Wait { ticks: 1 }]),
    );
    assert_eq!(
        data(&submit(&host, &session, &queued, "accepted"))["phase"],
        "queued"
    );
    assert_eq!(
        data(&control(&host, &session, &queued, "cancel"))["phase"],
        "cancelled"
    );
    assert_eq!(
        data(&control(&host, &session, &queued, "prepare"))["phase"],
        "cancelled"
    );
    let guard = before.request(
        "inventory-guard",
        Intent::Actions(vec![Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 2,
        }]),
    );
    let rejected = submit(&host, &session, &guard, "accepted");
    assert_eq!(rejected["status"], "rejected");
    assert_eq!(rejected["error"], "Inventory");
    let after = fixture.engine(&fixture.child);
    assert_eq!(after.canonical_records(), before.canonical_records());
    assert_eq!(after.canonical_bytes(), before.canonical_bytes());
    assert_eq!(
        after.accepted_history_basis().unwrap(),
        before.accepted_history_basis().unwrap()
    );
    private_oracle(&after);
}
