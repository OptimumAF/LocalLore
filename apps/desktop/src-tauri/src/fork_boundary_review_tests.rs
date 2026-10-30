// FIRST c8f7eb88/6fa36c0b: unregistered, uncompiled, unrun; missing API=SETUP.
// One retained SQLite fixture. No provider/SQL/custom Persistence or Tauri IPC.
use crate::fork_commands::{encode_boundary_catalog, read_boundary_catalog};
use crate::lease::WindowLease;
use locallore::{
    author_correction::{AuthorCorrectionInputV1, AuthorCorrectionOperationV1, CompletedBoundaryCatalogV2},
    contracts::{Command, Intent, Scope, Seed},
    engine::Engine,
    host::{Host, WorkspaceForkRequest},
};
use locallore_storage::{ForkRequest, Store};
use serde_json::{json, Value};
use std::{cell::Cell, fs, path::PathBuf, time::{SystemTime, UNIX_EPOCH}};

fn seed() -> Seed {
    let mut seed: Seed = serde_json::from_str(include_str!("../../../../fixtures/lantern_quay.json")).unwrap();
    seed.scope = Scope { story: "fork-boundary-review".into(), branch: "main".into() };
    seed
}
fn author(parent: &Scope, head: u64) -> AuthorCorrectionInputV1 {
    AuthorCorrectionInputV1 {
        version: 1, parent: parent.clone(), expected_parent_revision: head,
        fork_revision: head, child_branch: "authored".into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "beacon-mark".into(),
            expected_proposition: "An old repair mark is scratched inside the dry well.".into(),
            replacement: "PRIVATE-BOUNDARY-TRUTH".into(),
        },
        reason: "PRIVATE-BOUNDARY-REASON".into(),
    }
}
fn two_actions() -> Intent {
    Intent::Actions(vec![Command::Wait { ticks: 1 }, Command::Wait { ticks: 1 }])
}
fn core_turn(engine: &mut Engine, turn: &str) {
    let request = engine.request(turn, two_actions());
    let proposal = Engine::proposal(&request).unwrap();
    let preview = engine.preview(&request, &proposal).unwrap();
    assert_eq!(preview.events().len(), 2);
    assert_eq!(engine.commit_prepared(&preview).unwrap(), preview);
}
fn stored_turn(store: &mut Store, scope: &Scope, turn: &str, paired: bool) {
    let engine = store.resume(scope).unwrap().engine;
    let intent = if paired { two_actions() } else { Intent::Actions(vec![Command::Wait { ticks: 1 }]) };
    let request = engine.request(turn, intent);
    let proposal = Engine::proposal(&request).unwrap();
    let preview = engine.preview(&request, &proposal).unwrap();
    store.begin_turn(&request).unwrap();
    assert_eq!(store.commit_prepared(&preview).unwrap(), preview);
}
fn call(host: &Host, command: Value) -> Value {
    host.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
}
fn ok(host: &Host, command: Value) -> Value {
    let reply = call(host, command);
    assert_eq!(reply["status"], "ok", "{reply}");
    reply["data"].clone()
}
fn input(session: &str, scope: &Scope, head: u64) -> Value {
    json!({"session":session,"scope":scope,"expected_head":head})
}
fn ephemeral() -> (Host, String, Scope) {
    let host = Host::new(false);
    let opened = ok(&host, json!({"op":"create","seed":"lantern-quay-v1"}));
    let session = opened["session"].as_str().unwrap().to_owned();
    let scope = serde_json::from_value(opened["scope"].clone()).unwrap();
    (host, session, scope)
}
fn neutral(value: &Value, scope: &Scope, head: u64, boundaries: &[u64]) {
    assert_eq!(value, &json!({"version":2,"scope":scope,"head":head,"boundaries":boundaries}));
    assert!(serde_json::to_vec(value).unwrap().len() <= 65536);
    assert!(serde_json::to_vec_pretty(value).unwrap().len() <= 65536);
    let text = serde_json::to_string(value).unwrap();
    for hidden in ["SECRET-TIDE-731", "PRIVATE-BOUNDARY-TRUTH", "PRIVATE-BOUNDARY-REASON", "coverage", "proof", "self_state"] {
        assert!(!text.contains(hidden), "neutral metadata leaked {hidden}");
    }
}
fn fingerprint(engine: &Engine) -> Value {
    json!({"canonical":engine.canonical_bytes(),"state":engine.state(),
        "player":engine.character_context_v2("player",engine.scope(),engine.revision()).unwrap(),
        "mira":engine.character_context_v2("mira",engine.scope(),engine.revision()).unwrap()})
}

#[test]
fn actual_core_catalog_keeps_multievent_and_author_only_boundaries() {
    let mut root = Engine::new(seed()).unwrap();
    core_turn(&mut root, "two-events");
    let request = author(root.scope(), 2);
    let prepared = root.prepare_author_correction(&request, &|| false).unwrap();
    let child = root.apply_author_correction(&prepared, &|| false).unwrap().engine;
    assert_eq!(root.completed_boundaries(), [0, 2]);
    assert_eq!(child.completed_boundaries(), [0, 2, 3]);
    assert_eq!(child.receipts().len(), 1, "author boundary is not a receipt");
    neutral(&encode_boundary_catalog(&child.completed_boundary_catalog()).unwrap(), child.scope(), 3, &[0,2,3]);
    let empty = Engine::new(seed()).unwrap();
    let correction = empty.prepare_author_correction(&author(empty.scope(), 0), &|| false).unwrap();
    let authored = empty.apply_author_correction(&correction, &|| false).unwrap().engine;
    assert!(authored.receipts().is_empty());
    neutral(&encode_boundary_catalog(&authored.completed_boundary_catalog()).unwrap(), authored.scope(), 1, &[0,1]);
    // Core predicate only; not a live durable-source replacement test.
    let mut different = Engine::new(seed()).unwrap();
    core_turn(&mut different, "different-accepted-identity");
    assert_eq!(root.completed_boundary_catalog(), different.completed_boundary_catalog());
    assert!(!different.extends_accepted_history(&root).unwrap());
}

#[test]
fn durable_read_forks_each_boundary_and_preserves_others() {
    // Admitted TEMP on D locally, ordinary temp on CI; no automatic cleanup.
    let directory = std::env::temp_dir().join(format!("d08-fork-boundaries-{}-{}",
        std::process::id(), SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos()));
    fs::create_dir(&directory).unwrap();
    let database: PathBuf = directory.join("synthetic.sqlite");
    let mut store = Store::create_new_pinned(&database).unwrap();
    let parent = seed().scope.clone();
    store.create_story("Synthetic boundary history", seed()).unwrap();
    stored_turn(&mut store, &parent, "durable-two-events", true);
    let prepared = store.prepare_author_correction(&author(&parent, 2), &|| false).unwrap();
    let authored = store.apply_author_correction(&prepared, &|| false).unwrap().scope;
    let sibling = store.fork_branch(&ForkRequest { parent:parent.clone(), child_branch:"untouched".into(), expected_parent_revision:2, at_revision:2 }, &|| false).unwrap().scope;
    let original = [parent.clone(), authored.clone(), sibling.clone()].map(|scope| {
        let engine = store.resume(&scope).unwrap().engine;
        (scope, fingerprint(&engine))
    });
    assert_eq!(store.resume(&authored).unwrap().engine.completed_boundaries(), [0,2,3]);
    drop(store);
    let host = locallore_workspace::open(&database, false).unwrap();
    let resumed = ok(&host, json!({"op":"resume","scope":authored}));
    let session = resumed["session"].as_str().unwrap();
    let selected = input(session, &authored, 3);
    let before = host.generation_snapshot(session, &authored, 3, &|| false).unwrap();
    assert!(matches!(before.coverage, locallore::memory_coverage::CoverageRead::RawFallback(
        locallore::memory_coverage::FallbackReason::Unsupported)));
    neutral(&read_boundary_catalog(&host, &selected, &|| false).unwrap(), &authored, 3, &[0,2,3]);
    let after = host.generation_snapshot(session, &authored, 3, &|| false).unwrap();
    assert_eq!(fingerprint(&after.engine), fingerprint(&before.engine));
    assert_eq!(read_boundary_catalog(&host, &input("missing-session", &authored, 3), &|| false), Err("Closed".into()));
    assert_eq!(read_boundary_catalog(&host, &input(session, &parent, 2), &|| false), Err("Scope".into()));
    assert_eq!(read_boundary_catalog(&host, &input(session, &authored, 2), &|| false), Err("Stale".into()));
    let denied = call(&host, json!({"op":"inspect","session":session,"scope":authored,"observer":"omniscient","expected_revision":3}));
    assert_eq!(denied["error"], "Forbidden", "no Story Lab grant");
    let invalid = WorkspaceForkRequest { parent:authored.clone(), child_branch:"not-a-boundary".into(), expected_parent_revision:3, at_revision:1 };
    assert!(host.fork_branch(session, &invalid, &|| false).is_err());
    for at in [0,2,3] {
        let request = WorkspaceForkRequest { parent:authored.clone(), child_branch:format!("boundary-{at}"), expected_parent_revision:3, at_revision:at };
        let forked = host.fork_branch(session, &request, &|| false).unwrap();
        assert_eq!(forked.fork_revision, at); assert!(forked.created);
        let child = ok(&host, json!({"op":"resume","scope":forked.scope}));
        let child_session = child["session"].as_str().unwrap();
        let actual = host.generation_snapshot(child_session, &forked.scope, at, &|| false).unwrap().engine;
        assert_eq!(actual.domain_version(), if at < 3 { 1 } else { 2 });
        assert_eq!(actual.revision(), at);
        let expected: Vec<u64> = [0,2,3].into_iter().filter(|head| *head <= at).collect();
        neutral(&read_boundary_catalog(&host, &input(child_session, &forked.scope, at), &|| false).unwrap(), &forked.scope, at, &expected);
        ok(&host, json!({"op":"close","session":child_session,"scope":forked.scope}));
    }
    let mut inspect = Store::open_read_only(&database).unwrap();
    for (scope, bytes) in &original { assert_eq!(&fingerprint(&inspect.resume(scope).unwrap().engine), bytes); }
    assert_eq!(inspect.branch_catalog(&parent.story, &|| false).unwrap().branches.len(), 6);
    drop(inspect);
    // Actual other-owner append; same-head replacement is not exercised here.
    let mut writer = Store::open_application(&database).unwrap();
    stored_turn(&mut writer, &authored, "external-append", false);
    drop(writer);
    assert_eq!(read_boundary_catalog(&host, &selected, &|| false), Err("Stale".into()));
    neutral(&read_boundary_catalog(&host, &input(session, &authored, 4), &|| false).unwrap(), &authored, 4, &[0,2,3,4]);
    let mut inspect = Store::open_read_only(&database).unwrap();
    for (scope, bytes) in &original {
        if scope != &authored { assert_eq!(&fingerprint(&inspect.resume(scope).unwrap().engine), bytes); }
    }
    drop(inspect); drop(host);
    let bytes: u64 = fs::read_dir(&directory).unwrap().map(|entry| {
        let metadata = entry.unwrap().metadata().unwrap(); assert!(metadata.is_file()); metadata.len()
    }).sum();
    assert!(bytes <= 8 * 1024 * 1024, "retained fixture budget");
}

#[test]
fn exact_input_rejects_extra_fields_bad_types_and_unbounded_scalars() {
    let (host, session, scope) = ephemeral();
    let good = input(&session, &scope, 0);
    let mut cases = vec![Value::Null, json!([]), json!({})];
    for (key, value) in [("observer",json!("omniscient")),("grant",json!(true)),("path",json!("virtual-only")),("profile",json!("x"))] {
        let mut bad = good.clone(); bad[key] = value; cases.push(bad);
    }
    for value in [json!(""),json!("s".repeat(129)),json!("雪".repeat(43)),json!(1),Value::Null] {
        let mut bad = good.clone(); bad["session"] = value; cases.push(bad);
    }
    for value in [json!(-1),json!(1.5),json!(9_007_199_254_740_992u64),json!("0"),Value::Null] {
        let mut bad = good.clone(); bad["expected_head"] = value; cases.push(bad);
    }
    for key in ["story","branch"] {
        let long = "s".repeat(65);
        for value in ["", "../bad", "é", long.as_str()] {
            let mut bad = good.clone(); bad["scope"][key] = json!(value); cases.push(bad);
        }
    }
    let mut extra = good.clone(); extra["scope"]["observer"] = json!("player"); cases.push(extra);
    let mut missing = good.clone(); missing.as_object_mut().unwrap().remove("expected_head"); cases.push(missing);
    let mut array = good.clone(); array["scope"] = json!([]); cases.push(array);
    for bad in cases { assert_eq!(read_boundary_catalog(&host, &bad, &|| false), Err("InvalidForkInput".into())); }
    assert_eq!(read_boundary_catalog(&host, &input(&"s".repeat(128), &scope, 0), &|| false), Err("Closed".into()));
    neutral(&read_boundary_catalog(&host, &good, &|| false).unwrap(), &scope, 0, &[0]);
}

#[test]
fn cancel_and_callback_panic_leave_host_usable() {
    let (host, session, scope) = ephemeral();
    let selected = input(&session, &scope, 0);
    assert_eq!(read_boundary_catalog(&host, &selected, &|| true), Err("Cancelled".into()));
    let panic = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        read_boundary_catalog(&host, &selected, &|| panic!("synthetic boundary cancellation"))
    }));
    assert!(panic.is_ok()); assert_eq!(panic.unwrap(), Err("Cancelled".into()));
    let calls = Cell::new(0);
    assert_eq!(read_boundary_catalog(&host, &selected, &|| { calls.set(calls.get()+1); calls.get() >= 2 }), Err("Cancelled".into()));
    assert!(calls.get() >= 2);
    neutral(&read_boundary_catalog(&host, &selected, &|| false).unwrap(), &scope, 0, &[0]);
}

#[test]
fn ephemeral_metadata_grants_no_fork_or_spoilers() {
    let (host, session, scope) = ephemeral();
    neutral(&read_boundary_catalog(&host, &input(&session, &scope, 0), &|| false).unwrap(), &scope, 0, &[0]);
    let request = WorkspaceForkRequest { parent:scope.clone(), child_branch:"unsupported-child".into(), expected_parent_revision:0, at_revision:0 };
    assert_eq!(host.fork_branch(&session, &request, &|| false), Err("Unsupported".into()));
    let denied = call(&host, json!({"op":"inspect","session":session,"scope":scope,"observer":"omniscient","expected_revision":0}));
    assert_eq!(denied["error"], "Forbidden");
    assert_eq!(ok(&host, json!({"op":"workspace"}))["persistent"], false);
}

#[test]
fn lease_fences_pre_read_and_retired_publication() {
    // Pure lease + actual read, not Tauri/worker integration.
    let (host, session, scope) = ephemeral();
    let lease = WindowLease::default(); let epoch = lease.begin().unwrap();
    let selected = input(&session, &scope, 0);
    let value = lease.dispatch(epoch, || read_boundary_catalog(&host, &selected, &|| !lease.valid(epoch))).unwrap();
    neutral(&value, &scope, 0, &[0]);
    let closed = lease.invalidate(&format!("main-{epoch}")).unwrap();
    assert_eq!(read_boundary_catalog(&host, &selected, &|| !lease.valid(epoch)), Err("Cancelled".into()));
    let entered = Cell::new(false);
    assert_eq!(lease.dispatch(epoch, || { entered.set(true); Ok(value.clone()) }), Err("Closed".into()));
    assert!(!entered.get(), "no retired publication");
    lease.finish_close(closed, || host.close_all());
    let next = lease.begin().unwrap(); assert_ne!(epoch, next);
    assert!(!lease.valid(epoch));
    assert_eq!(read_boundary_catalog(&host, &selected, &|| false), Err("Closed".into()));
}

#[test]
fn maximum_typed_catalog_keeps_both_wire_bounds() {
    // Synthetic DTO capacity, not 4096 executed turns.
    let catalog = CompletedBoundaryCatalogV2 { version:2,
        scope:Scope { story:"s".repeat(64), branch:"b".repeat(64) }, head:32768,
        boundaries:(0..=4096).map(|index| index * 8).collect() };
    let encoded = encode_boundary_catalog(&catalog).unwrap();
    neutral(&encoded, &catalog.scope, 32768, &catalog.boundaries);
    assert_eq!(encoded["boundaries"].as_array().unwrap().len(), 4097);
    assert_eq!(encoded["boundaries"][0], 0); assert_eq!(encoded["boundaries"][4096], 32768);
}

#[test]
fn typed_count_bytes_and_unsafe_numbers_refuse_without_truncation() {
    let base = CompletedBoundaryCatalogV2 { version:2, scope:seed().scope, head:0, boundaries:vec![0] };
    let mut count = base.clone(); count.boundaries = vec![0;4098];
    let mut number = base.clone(); number.head = 9_007_199_254_740_992;
    let mut entry = base.clone(); entry.boundaries.push(9_007_199_254_740_992);
    let mut head = base.clone(); head.head = 32769; head.boundaries.push(32769);
    // Oversized DTO overlaps invalid ID length, not an isolated live boundary.
    let mut bytes = base.clone(); bytes.scope.story = "s".repeat(65536);
    for catalog in [count, number, entry, head, bytes] {
        let before = serde_json::to_vec(&catalog).unwrap();
        assert_eq!(encode_boundary_catalog(&catalog), Err("TooLarge".into()));
        assert_eq!(serde_json::to_vec(&catalog).unwrap(), before);
    }
}
