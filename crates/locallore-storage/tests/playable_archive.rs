use locallore::{
    contracts::*,
    engine::Engine,
    inference::*,
    play::{self, PlayProfile},
};
use locallore_storage::{playable_archive::*, ForkRequest, Store, TurnError, TurnPhase};
use rusqlite::Connection;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    cell::Cell,
    path::PathBuf,
    sync::{
        atomic::{AtomicU64, Ordering},
        Arc, Barrier,
    },
    task::Poll,
};
static NEXT: AtomicU64 = AtomicU64::new(0);
struct Temp(PathBuf);
impl Temp {
    fn new() -> Self {
        let path = std::env::temp_dir().join(format!(
            "locallore-archive-{}-{}-{}",
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
    fn path(&self, name: &str) -> PathBuf {
        self.0.join(name)
    }
}
impl Drop for Temp {
    fn drop(&mut self) {
        std::fs::remove_dir_all(&self.0).unwrap();
    }
}
fn seed() -> Seed {
    serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap()
}
fn source(temp: &Temp) -> (Store, Scope, Scope) {
    let mut store = Store::open(&temp.path("source.sqlite"), None).unwrap();
    let seed = seed();
    let root = seed.scope.clone();
    store.create_story("Original private story", seed).unwrap();
    apply(
        &mut store,
        &root,
        "before",
        vec![Command::Wait { ticks: 1 }],
    );
    let child = fork(&mut store, &root, "child", 1);
    apply(
        &mut store,
        &root,
        "same-key",
        vec![Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 1,
        }],
    );
    apply(
        &mut store,
        &child,
        "same-key",
        vec![Command::Consume {
            item: "potion".into(),
        }],
    );
    let sibling = fork(&mut store, &root, "sibling", 1);
    apply(
        &mut store,
        &sibling,
        "private-sibling",
        vec![Command::Say {
            text: "SIBLING_PRIVATE_CANARY".into(),
            audience: ["mira".into()].into(),
        }],
    );
    (store, root, child)
}
fn target(temp: &Temp, name: &str) -> (Store, Scope) {
    let mut store = Store::open(&temp.path(name), None).unwrap();
    let mut seed = seed();
    seed.scope.story = "retained-story".into();
    let root = seed.scope.clone();
    store.create_story("Keep me", seed).unwrap();
    apply(
        &mut store,
        &root,
        "retained",
        vec![Command::Wait { ticks: 1 }],
    );
    (store, root)
}
fn apply(store: &mut Store, scope: &Scope, id: &str, commands: Vec<Command>) -> Receipt {
    let engine = store.resume(scope).unwrap().engine;
    let request = engine.request(id, Intent::Actions(commands));
    let proposal = Engine::proposal(&request).unwrap();
    let preview = engine.preview(&request, &proposal).unwrap();
    store.begin_turn(&request).unwrap();
    store
        .commit_turn(&request, &proposal, preview.narration())
        .unwrap()
}
fn fork(store: &mut Store, parent: &Scope, id: &str, at: u64) -> Scope {
    let head = store.resume(parent).unwrap().engine.revision();
    store
        .fork_branch(
            &ForkRequest {
                parent: parent.clone(),
                child_branch: id.into(),
                expected_parent_revision: head,
                at_revision: at,
            },
            &|| false,
        )
        .unwrap()
        .scope
}
fn bytes(value: &Value) -> Vec<u8> {
    serde_json::to_vec(value).unwrap()
}
// Independent manifest-editing helper: sorted insertion works with either
// serde_json map implementation. Does not implement any Engine/visibility rule.
fn canonical(value: &Value) -> Value {
    match value {
        Value::Object(map) => {
            let mut keys: Vec<_> = map.keys().collect();
            keys.sort_unstable();
            let mut out = serde_json::Map::new();
            for key in keys {
                out.insert(key.clone(), canonical(&map[key]));
            }
            Value::Object(out)
        }
        Value::Array(values) => Value::Array(values.iter().map(canonical).collect()),
        value => value.clone(),
    }
}
fn hash(value: &Value) -> String {
    format!("{:x}", Sha256::digest(bytes(&canonical(value))))
}
fn rehash(value: &mut Value) {
    value["integrity"]["payload_sha256"] = json!(hash(&value["payload"]));
    value["integrity"]["seed_sha256"] = json!(hash(&value["payload"]["story"]["seed"]));
    value["integrity"]["branches"]=Value::Array(value["payload"]["branches"].as_array().unwrap().iter().map(|branch|{
        let old=value["integrity"]["branches"].as_array().unwrap().iter().find(|row|row["id"]==branch["id"]);
        json!({"id":branch["id"],"receipts_sha256":hash(&branch["local_receipts"]),"canonical_state_sha256":old.map(|r|r["canonical_state_sha256"].clone()).unwrap_or(json!("0".repeat(64)))})
    }).collect());
}
fn branch_mut<'a>(value: &'a mut Value, id: &str) -> &'a mut Value {
    value["payload"]["branches"]
        .as_array_mut()
        .unwrap()
        .iter_mut()
        .find(|b| b["id"] == id)
        .unwrap()
}
fn table_counts(path: &std::path::Path) -> Vec<i64> {
    let db = Connection::open(path).unwrap();
    [
        "stories",
        "branches",
        "turns",
        "accepted_events",
        "event_witnesses",
        "entities",
        "branch_entities",
        "branch_projections",
        "derived_memory",
    ]
    .into_iter()
    .map(|table| {
        db.query_row(&format!("SELECT count(*) FROM {table}"), [], |r| r.get(0))
            .unwrap()
    })
    .collect()
}

#[test]
fn complete_original_branches_roundtrip_replay_retries_and_continue_without_any_model() {
    let temp = Temp::new();
    let (mut source, root, child) = source(&temp);
    let archive = source.export_archive(&root.story, &|| false).unwrap();
    assert_eq!(archive.preview().branch_heads.len(), 3);
    assert_eq!(archive.preview().committed_turns, 4);
    assert!(!archive.preview().noncommitted_workflow_transferred);
    let full_text = std::str::from_utf8(archive.bytes()).unwrap();
    assert!(full_text.contains("SECRET-TIDE-731"));
    assert!(full_text.contains("SIBLING_PRIVATE_CANARY"));
    assert!(archive
        .preview()
        .privacy_warning
        .contains("hidden seed facts"));
    let original: Vec<_> = archive
        .preview()
        .branch_heads
        .keys()
        .map(|id| {
            let scope = Scope {
                story: root.story.clone(),
                branch: id.clone(),
            };
            let e = source.resume(&scope).unwrap().engine;
            (scope, e)
        })
        .collect();
    let (mut target, retained) = target(&temp, "target.sqlite");
    let retained_before = target.resume(&retained).unwrap().engine.canonical_bytes();
    let validated = validate_archive(archive.bytes(), &|| false).unwrap();
    let result = target.import_archive(validated, &|| false).unwrap();
    assert_eq!(result.root, root);
    assert_eq!(result.branches, 3);
    drop(target);
    let mut target = Store::open(&temp.path("target.sqlite"), None).unwrap();
    for (scope, expected) in &original {
        let actual = target.resume(scope).unwrap().engine;
        assert_eq!(actual.canonical_bytes(), expected.canonical_bytes());
        assert_eq!(actual.receipts(), expected.receipts());
        for actor in ["player", "mira", "sable"] {
            assert_eq!(
                actual
                    .character_context(actor, scope, actual.revision())
                    .unwrap(),
                expected
                    .character_context(actor, scope, expected.revision())
                    .unwrap()
            );
        }
        for receipt in expected
            .receipts()
            .iter()
            .filter(|r| r.request().scope == *scope)
        {
            assert_eq!(target.commit_prepared(receipt).unwrap(), *receipt);
        }
    }
    let raw = Connection::open(temp.path("target.sqlite")).unwrap();
    assert_eq!(
        raw.query_row(
            "SELECT count(*) FROM accepted_events WHERE story_id=?1 AND branch_id='child'",
            [&root.story],
            |r| r.get::<_, i64>(0)
        )
        .unwrap(),
        1
    );
    assert_eq!(
        target.resume(&root).unwrap().engine.state().items["potion"].owner,
        "mira"
    );
    assert!(!target
        .resume(&child)
        .unwrap()
        .engine
        .state()
        .items
        .contains_key("potion"));
    let child_engine = target.resume(&child).unwrap().engine;
    let npc =
        serde_json::to_string(&child_engine.character_context("mira", &child, 2).unwrap()).unwrap();
    assert!(!npc.contains("SECRET-TIDE-731"));
    assert!(!npc.contains("SIBLING_PRIVATE_CANARY"));
    apply(
        &mut target,
        &child,
        "continued",
        vec![Command::Wait { ticks: 1 }],
    );
    assert_eq!(target.resume(&child).unwrap().engine.revision(), 3);
    assert_eq!(target.resume(&root).unwrap().engine.revision(), 2);
    assert_eq!(
        target.resume(&retained).unwrap().engine.canonical_bytes(),
        retained_before
    );
}

#[test]
fn noncommitted_workflow_and_caches_are_excluded_without_changing_source_terminal_guarantees() {
    let temp = Temp::new();
    let (mut source, root, _) = source(&temp);
    let engine = source.resume(&root).unwrap().engine;
    let mut requests = Vec::new();
    for id in [
        "EXCLUDED_DRAFT",
        "EXCLUDED_CANCELLED",
        "EXCLUDED_FAILED",
        "EXCLUDED_STALE",
    ] {
        let request = engine.request(id, Intent::Actions(vec![Command::Wait { ticks: 1 }]));
        source.begin_turn(&request).unwrap();
        requests.push(request);
    }
    source.cancel_turn(&requests[1]).unwrap();
    source.fail_turn(&requests[2]).unwrap();
    source.stale_turn(&requests[3]).unwrap();
    let request = locallore_storage::derived_memory::PrepareRequest {
        scope: root.clone(),
        expected_revision: 2,
        observer: "player".into(),
        from_exclusive: 0,
        through_revision: 2,
        target: locallore_storage::derived_memory::Target::SceneWindow,
    };
    let prepared = source.prepare_memory(&request, &|| false).unwrap();
    source.publish_memory(prepared, &|| false).unwrap();
    let archive = source.export_archive(&root.story, &|| false).unwrap();
    let text = std::str::from_utf8(archive.bytes()).unwrap();
    for request in &requests {
        assert!(!text.contains(&request.turn));
    }
    let (mut target, _) = target(&temp, "target.sqlite");
    target
        .import_archive(
            validate_archive(archive.bytes(), &|| false).unwrap(),
            &|| false,
        )
        .unwrap();
    assert!(target.drafts(&root).unwrap().is_empty());
    for request in &requests {
        assert_eq!(
            target.lookup_turn(&root, &request.turn).err(),
            Some(TurnError::UnknownTurn)
        );
    }
    assert_eq!(
        source.turn_status(&requests[1]).unwrap().phase,
        TurnPhase::Cancelled
    );
    assert_eq!(
        source.import_archive(
            validate_archive(archive.bytes(), &|| false).unwrap(),
            &|| false
        ),
        Err(ArchiveError::Conflict)
    );
    assert_eq!(
        source.turn_status(&requests[1]).unwrap().phase,
        TurnPhase::Cancelled
    );
    let db = Connection::open(temp.path("target.sqlite")).unwrap();
    assert_eq!(
        db.query_row("SELECT count(*) FROM derived_memory", [], |r| r
            .get::<_, i64>(0))
            .unwrap(),
        0
    );
}

#[test]
fn recomputed_checksums_never_make_forged_outcomes_witnesses_or_copied_ancestor_receipts_canonical()
{
    let temp = Temp::new();
    let (mut source, root, _) = source(&temp);
    let archive = source.export_archive(&root.story, &|| false).unwrap();
    let original: Value = serde_json::from_slice(archive.bytes()).unwrap();
    let mut variants = Vec::new();
    let mut v = original.clone();
    branch_mut(&mut v, "child")["local_receipts"][0]["events"][0]["sequence"] = json!(99);
    variants.push(v);
    let mut v = original.clone();
    branch_mut(&mut v, "child")["local_receipts"][0]["events"][0]["witnesses"] =
        json!(["player", "sable"]);
    variants.push(v);
    let mut v = original.clone();
    branch_mut(&mut v, "child")["local_receipts"][0]["proposal"]["commands"] =
        json!([{"op":"wait","ticks":1}]);
    variants.push(v);
    let mut v = original.clone();
    branch_mut(&mut v, "child")["local_receipts"][0]["raw_prompt"] = json!("PRIVATE_TRACE_CANARY");
    variants.push(v);
    let mut v = original.clone();
    let ancestor = branch_mut(&mut v, "main")["local_receipts"][0].clone();
    branch_mut(&mut v, "child")["local_receipts"]
        .as_array_mut()
        .unwrap()
        .insert(0, ancestor);
    variants.push(v);
    for mut value in variants {
        rehash(&mut value);
        assert_eq!(
            validate_archive(&bytes(&value), &|| false).err(),
            Some(ArchiveError::Integrity)
        );
    }
}

#[test]
fn malformed_duplicate_unknown_and_future_versions_reject_before_target_writes() {
    let temp = Temp::new();
    let (mut source, root, _) = source(&temp);
    let archive = source.export_archive(&root.story, &|| false).unwrap();
    let original: Value = serde_json::from_slice(archive.bytes()).unwrap();
    let (mut target, retained) = target(&temp, "target.sqlite");
    let before = table_counts(&temp.path("target.sqlite"));
    let state = target.resume(&retained).unwrap().engine.canonical_bytes();
    let text = std::str::from_utf8(archive.bytes()).unwrap();
    for needle in ["\"format\":", "\"energy\":", "\"narration\":"] {
        let replacement = format!("{needle}null,{needle}");
        let duplicate = text.replacen(needle, &replacement, 1);
        assert_ne!(duplicate, text);
        assert_eq!(
            validate_archive(duplicate.as_bytes(), &|| false).err(),
            Some(ArchiveError::Malformed)
        );
    }
    for malformed in [
        b"{".to_vec(),
        vec![0xff],
        archive.bytes()[..archive.bytes().len() / 2].to_vec(),
    ] {
        assert_eq!(
            validate_archive(&malformed, &|| false).err(),
            Some(ArchiveError::Malformed)
        );
    }
    for pointer in [
        "/unknown",
        "/payload/unknown",
        "/payload/story/seed/actors/player/unknown",
    ] {
        let mut value = original.clone();
        let parent = pointer.rsplit_once('/').unwrap().0;
        value
            .pointer_mut(if parent.is_empty() { "" } else { parent })
            .unwrap()["unknown"] = json!(true);
        rehash(&mut value);
        assert_eq!(
            validate_archive(&bytes(&value), &|| false).err(),
            Some(ArchiveError::Malformed)
        );
    }
    for pointer in [
        "/version",
        "/payload/domain_version",
        "/payload/source_database_schema_version",
        "/payload/story/seed/version",
    ] {
        let mut value = original.clone();
        *value.pointer_mut(pointer).unwrap() = json!(999);
        rehash(&mut value);
        assert_eq!(
            validate_archive(&bytes(&value), &|| false).err(),
            Some(ArchiveError::Unsupported)
        );
    }
    let mut value = original.clone();
    value["payload"]["files"] = json!([{"path":"../../escape.exe","code":"execute me"}]);
    rehash(&mut value);
    assert_eq!(
        validate_archive(&bytes(&value), &|| false).err(),
        Some(ArchiveError::Malformed)
    );
    assert_eq!(table_counts(&temp.path("target.sqlite")), before);
    assert_eq!(
        target.resume(&retained).unwrap().engine.canonical_bytes(),
        state
    );
}

#[test]
fn hostile_graph_heads_scopes_and_partial_turn_forks_are_rejected() {
    let temp = Temp::new();
    let (mut source, root, _) = source(&temp);
    let archive = source.export_archive(&root.story, &|| false).unwrap();
    let original: Value = serde_json::from_slice(archive.bytes()).unwrap();
    for (field, value) in [
        ("parent", json!("missing")),
        ("parent", json!("child")),
        ("fork_revision", json!(99)),
        ("head_revision", json!(99)),
    ] {
        let mut v = original.clone();
        branch_mut(&mut v, "child")[field] = value;
        rehash(&mut v);
        assert_eq!(
            validate_archive(&bytes(&v), &|| false).err(),
            Some(ArchiveError::Integrity)
        );
    }
    let mut v = original.clone();
    branch_mut(&mut v, "child")["local_receipts"][0]["request"]["scope"]["story"] =
        json!("foreign");
    rehash(&mut v);
    assert_eq!(
        validate_archive(&bytes(&v), &|| false).err(),
        Some(ArchiveError::Integrity)
    );
    let mut v = original.clone();
    let duplicate = v["payload"]["branches"][0].clone();
    v["payload"]["branches"]
        .as_array_mut()
        .unwrap()
        .push(duplicate);
    rehash(&mut v);
    assert_eq!(
        validate_archive(&bytes(&v), &|| false).err(),
        Some(ArchiveError::Integrity)
    );
    let temp = Temp::new();
    let mut source = Store::open(&temp.path("multi.sqlite"), None).unwrap();
    let seed = seed();
    let root = seed.scope.clone();
    source.create_story("Multi", seed).unwrap();
    apply(
        &mut source,
        &root,
        "multi",
        vec![Command::Wait { ticks: 1 }, Command::Wait { ticks: 1 }],
    );
    fork(&mut source, &root, "child", 2);
    let archive = source.export_archive(&root.story, &|| false).unwrap();
    let mut value: Value = serde_json::from_slice(archive.bytes()).unwrap();
    branch_mut(&mut value, "child")["fork_revision"] = json!(1);
    rehash(&mut value);
    assert_eq!(
        validate_archive(&bytes(&value), &|| false).err(),
        Some(ArchiveError::Integrity)
    );
}

#[test]
fn every_import_cancellation_checkpoint_and_sql_abort_rolls_back_new_identity_only() {
    let temp = Temp::new();
    let (mut source, root, _) = source(&temp);
    let archive = source.export_archive(&root.story, &|| false).unwrap();
    let (mut baseline, _) = target(&temp, "baseline.sqlite");
    let calls = Cell::new(0);
    baseline
        .import_archive(
            validate_archive(archive.bytes(), &|| false).unwrap(),
            &|| {
                calls.set(calls.get() + 1);
                false
            },
        )
        .unwrap();
    let calls = calls.get();
    assert!(calls > 10 && calls < 256);
    for threshold in 1..=calls {
        let name = format!("cancel-{threshold}.sqlite");
        let (mut target, retained) = target(&temp, &name);
        let before = table_counts(&temp.path(&name));
        let state = target.resume(&retained).unwrap().engine.canonical_bytes();
        let count = Cell::new(0);
        let result = target.import_archive(
            validate_archive(archive.bytes(), &|| false).unwrap(),
            &|| {
                count.set(count.get() + 1);
                count.get() >= threshold
            },
        );
        assert_eq!(result, Err(ArchiveError::Cancelled));
        assert_eq!(table_counts(&temp.path(&name)), before);
        assert_eq!(
            target.resume(&retained).unwrap().engine.canonical_bytes(),
            state
        );
    }
    let (mut target, retained) = target(&temp, "abort.sqlite");
    let db = Connection::open(temp.path("abort.sqlite")).unwrap();
    let before = table_counts(&temp.path("abort.sqlite"));
    let state = target.resume(&retained).unwrap().engine.canonical_bytes();
    db.execute_batch("CREATE TRIGGER archive_test_abort AFTER INSERT ON accepted_events WHEN new.story_id <> 'retained-story' BEGIN SELECT RAISE(ABORT,'synthetic import abort'); END;").unwrap();
    assert_eq!(
        target.import_archive(
            validate_archive(archive.bytes(), &|| false).unwrap(),
            &|| false
        ),
        Err(ArchiveError::Database)
    );
    assert_eq!(table_counts(&temp.path("abort.sqlite")), before);
    assert_eq!(
        target.resume(&retained).unwrap().engine.canonical_bytes(),
        state
    );
    db.execute_batch("DROP TRIGGER archive_test_abort").unwrap();
    target
        .import_archive(
            validate_archive(archive.bytes(), &|| false).unwrap(),
            &|| false,
        )
        .unwrap();
    let before = table_counts(&temp.path("abort.sqlite"));
    assert_eq!(
        target.import_archive(
            validate_archive(archive.bytes(), &|| false).unwrap(),
            &|| false
        ),
        Err(ArchiveError::Conflict)
    );
    assert_eq!(table_counts(&temp.path("abort.sqlite")), before);
}

#[test]
fn concurrent_imports_never_overwrite_or_claim_success_for_existing_identical_identity() {
    let temp = Temp::new();
    let (mut source, root, _) = source(&temp);
    let archive = source.export_archive(&root.story, &|| false).unwrap();
    let (target, _) = target(&temp, "target.sqlite");
    drop(target);
    let barrier = Arc::new(Barrier::new(2));
    let threads: Vec<_> = (0..2)
        .map(|_| {
            let path = temp.path("target.sqlite");
            let bytes = archive.bytes().to_vec();
            let barrier = barrier.clone();
            std::thread::spawn(move || {
                let mut owner = Store::open(&path, None).unwrap();
                let validated = validate_archive(&bytes, &|| false).unwrap();
                barrier.wait();
                owner.import_archive(validated, &|| false)
            })
        })
        .collect();
    let outcomes: Vec<_> = threads.into_iter().map(|t| t.join().unwrap()).collect();
    assert_eq!(outcomes.iter().filter(|r| r.is_ok()).count(), 1);
    assert!(outcomes
        .iter()
        .filter_map(|r| r.as_ref().err())
        .all(|e| matches!(e, ArchiveError::Conflict | ArchiveError::Busy)));
    let mut target = Store::open(&temp.path("target.sqlite"), None).unwrap();
    assert_eq!(
        target.import_archive(
            validate_archive(archive.bytes(), &|| false).unwrap(),
            &|| false
        ),
        Err(ArchiveError::Conflict)
    );
    assert_eq!(
        target.resume(&root).unwrap().engine.state().items["potion"].owner,
        "mira"
    );
}

#[test]
fn artifact_branch_receipt_count_and_reference_caps_fail_closed() {
    let temp = Temp::new();
    let (mut source, root, _) = source(&temp);
    let archive = source.export_archive(&root.story, &|| false).unwrap();
    let original: Value = serde_json::from_slice(archive.bytes()).unwrap();
    assert_eq!(
        validate_archive(&vec![b' '; MAX_ARCHIVE_BYTES + 1], &|| false).err(),
        Some(ArchiveError::TooLarge)
    );
    let mut v = original.clone();
    let first = v["payload"]["branches"][0].clone();
    v["payload"]["branches"] = json!(vec![first; MAX_ARCHIVE_BRANCHES + 1]);
    rehash(&mut v);
    assert_eq!(
        validate_archive(&bytes(&v), &|| false).err(),
        Some(ArchiveError::TooLarge)
    );
    let mut v = original.clone();
    branch_mut(&mut v, "main")["local_receipts"][0]["extra"] = json!("x".repeat(MAX_RECEIPT_BYTES));
    rehash(&mut v);
    assert_eq!(
        validate_archive(&bytes(&v), &|| false).err(),
        Some(ArchiveError::TooLarge)
    );
    let mut v = original.clone();
    let first = branch_mut(&mut v, "main")["local_receipts"][0].clone();
    branch_mut(&mut v, "main")["local_receipts"] = json!(vec![first; MAX_HISTORY_RECEIPTS + 1]);
    rehash(&mut v);
    assert_eq!(
        validate_archive(&bytes(&v), &|| false).err(),
        Some(ArchiveError::TooLarge)
    );
    let mut v = original.clone();
    v["payload"]["required_policies"] = json!(vec![
        json!({"policy":"x","prompt_version":"x"});
        MAX_MODEL_REFERENCES + 1
    ]);
    rehash(&mut v);
    assert_eq!(
        validate_archive(&bytes(&v), &|| false).err(),
        Some(ArchiveError::TooLarge)
    );
}

struct Script;
impl InferenceProvider for Script {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        _: &Cancellation,
    ) -> Poll<std::result::Result<Vec<u8>, Error>> {
        let Input::Structured { role, schema, .. } = &request.input else {
            return Poll::Ready(Err(Error::Provider));
        };
        let value = if role == "director" {
            json!({"commands":[{"op":"wait","ticks":1}]})
        } else {
            json!({"text":"Rain falls on the quay.","speaker":"narrator","event_ids":schema["properties"]["event_ids"]["const"]})
        };
        Poll::Ready(Ok(bytes(&value)))
    }
}
#[test]
fn original_play_metadata_and_timing_transfer_without_model_installation_or_policy_rewriting() {
    let temp = Temp::new();
    let mut source = Store::open(&temp.path("play.sqlite"), None).unwrap();
    let seed = seed();
    let root = seed.scope.clone();
    source.create_story("Synthetic fake Play", seed).unwrap();
    let mut engine = source.resume(&root).unwrap().engine;
    let request = engine.request(
        "fake-play",
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: "I wait for one tide tick.".into(),
        },
    );
    let profile = PlayProfile {
        id: "archive-fake-v1".into(),
        model_sha256: "0".repeat(64),
        runtime_revision: "0".repeat(40),
        template_sha256: "0".repeat(64),
        worker_sha256: "0".repeat(64),
        profile_manifest_sha256: "0".repeat(64),
        context_tokens: 4096,
        director_tokens: 350,
        narrator_tokens: 220,
        deadline_ms: 5000,
        repair_limit: 1,
    };
    let receipt = play::execute(
        &mut engine,
        &request,
        &mut Script,
        &Cancellation::default(),
        &profile,
    )
    .unwrap();
    source.begin_turn(&request).unwrap();
    source.commit_prepared(&receipt).unwrap();
    let archive = source.export_archive(&root.story, &|| false).unwrap();
    let raw: Value = serde_json::from_slice(archive.bytes()).unwrap();
    assert_eq!(
        raw["payload"]["model_references"].as_array().unwrap().len(),
        1
    );
    let (mut target, _) = target(&temp, "target.sqlite");
    target
        .import_archive(
            validate_archive(archive.bytes(), &|| false).unwrap(),
            &|| false,
        )
        .unwrap();
    assert_eq!(
        target.lookup_turn(&root, "fake-play").unwrap().receipt,
        Some(receipt.clone())
    );
    assert_eq!(target.commit_prepared(&receipt).unwrap(), receipt);
    let mut tampered = raw.clone();
    tampered["payload"]["model_references"][0]["profile"]["model_sha256"] = json!("1".repeat(64));
    rehash(&mut tampered);
    assert_eq!(
        validate_archive(&bytes(&tampered), &|| false).err(),
        Some(ArchiveError::Integrity)
    );
}

#[test]
fn export_and_validation_cancellation_are_bounded_categories_and_do_not_change_source() {
    let temp = Temp::new();
    let (mut source, root, _) = source(&temp);
    let before = table_counts(&temp.path("source.sqlite"));
    let state = source.resume(&root).unwrap().engine.canonical_bytes();
    assert_eq!(
        source.export_archive(&root.story, &|| true).err(),
        Some(ArchiveError::Cancelled)
    );
    let archive = source.export_archive(&root.story, &|| false).unwrap();
    let calls = Cell::new(0);
    validate_archive(archive.bytes(), &|| {
        calls.set(calls.get() + 1);
        false
    })
    .unwrap();
    let maximum = calls.get();
    assert!(maximum > 10 && maximum < 256);
    for threshold in 1..=maximum {
        let count = Cell::new(0);
        assert_eq!(
            validate_archive(archive.bytes(), &|| {
                count.set(count.get() + 1);
                count.get() >= threshold
            })
            .err(),
            Some(ArchiveError::Cancelled)
        );
    }
    assert_eq!(
        validate_archive(archive.bytes(), &|| panic!(
            "synthetic private cancel callback"
        ))
        .err(),
        Some(ArchiveError::Cancelled)
    );
    assert_eq!(table_counts(&temp.path("source.sqlite")), before);
    assert_eq!(
        source.resume(&root).unwrap().engine.canonical_bytes(),
        state
    );
}

#[test]
fn export_snapshot_is_coherent_while_another_owner_commits_after_capture_begins() {
    use std::sync::mpsc;
    let temp = Temp::new();
    let (mut source, root, _) = source(&temp);
    let (ready_send, ready_receive) = mpsc::channel();
    let (go_send, go_receive) = mpsc::channel();
    let path = temp.path("source.sqlite");
    let scope = root.clone();
    let writer = std::thread::spawn(move || {
        let mut owner = Store::open(&path, None).unwrap();
        let engine = owner.resume(&scope).unwrap().engine;
        let request = engine.request(
            "after-capture",
            Intent::Actions(vec![Command::Wait { ticks: 1 }]),
        );
        let proposal = Engine::proposal(&request).unwrap();
        let narration = engine
            .preview(&request, &proposal)
            .unwrap()
            .narration()
            .to_owned();
        owner.begin_turn(&request).unwrap();
        ready_send.send(()).unwrap();
        go_receive.recv().unwrap();
        for _ in 0..10 {
            match owner.commit_turn(&request, &proposal, &narration) {
                Ok(receipt) => return receipt,
                Err(TurnError::Storage(locallore_storage::StorageError::Busy)) => {
                    std::thread::yield_now()
                }
                other => panic!("unexpected synthetic writer result: {other:?}"),
            }
        }
        panic!("synthetic writer did not recover after bounded source snapshot")
    });
    ready_receive.recv().unwrap();
    let calls = Cell::new(0);
    let archive = source
        .export_archive(&root.story, &|| {
            calls.set(calls.get() + 1);
            if calls.get() == 2 {
                go_send.send(()).unwrap();
            }
            false
        })
        .unwrap();
    let receipt = writer.join().unwrap();
    assert_eq!(receipt.events()[0].sequence(), 3);
    assert_eq!(archive.preview().branch_heads[&root.branch], 2);
    assert!(!std::str::from_utf8(archive.bytes())
        .unwrap()
        .contains("after-capture"));
    assert_eq!(source.resume(&root).unwrap().engine.revision(), 3);
    validate_archive(archive.bytes(), &|| false).unwrap();
}

#[test]
fn archive_restores_original_supported_historical_play_without_fresh_commit_bypass() {
    let fixture: Value = serde_json::from_str(include_str!(
        "../../locallore/tests/fixtures/accepted_play_v2_1.json"
    ))
    .unwrap();
    let seed: Seed = serde_json::from_value(fixture["seed"].clone()).unwrap();
    let root = seed.scope.clone();
    let original = Engine::restore(seed.clone(), &[fixture["receipt"].to_string()]).unwrap();
    let temp = Temp::new();
    let mut source = Store::open(&temp.path("legacy-source.sqlite"), None).unwrap();
    source
        .create_story("Historical accepted Play", seed.clone())
        .unwrap();
    let empty = source.export_archive(&root.story, &|| false).unwrap();
    let mut value: Value = serde_json::from_slice(empty.bytes()).unwrap();
    branch_mut(&mut value, &root.branch)["local_receipts"] = json!([fixture["receipt"]]);
    branch_mut(&mut value, &root.branch)["head_revision"] = json!(original.revision());
    let play = &fixture["receipt"]["play"];
    value["payload"]["required_policies"] =
        json!([{"policy":play["policy"],"prompt_version":play["prompt_version"]}]);
    value["payload"]["model_references"] =
        json!([{"sha256":hash(&play["profile"]),"profile":play["profile"]}]);
    rehash(&mut value);
    value["integrity"]["branches"][0]["canonical_state_sha256"] =
        json!(format!("{:x}", Sha256::digest(original.canonical_bytes())));
    let (mut target, _) = target(&temp, "target.sqlite");
    target
        .import_archive(
            validate_archive(&bytes(&value), &|| false).unwrap(),
            &|| false,
        )
        .unwrap();
    let restored = target.resume(&root).unwrap().engine;
    assert_eq!(restored.receipts(), original.receipts());
    assert_eq!(restored.canonical_bytes(), original.canonical_bytes());
    assert_eq!(
        target.commit_prepared(&original.receipts()[0]).unwrap(),
        original.receipts()[0]
    );
    let mut fresh = Engine::new(seed).unwrap();
    assert_eq!(
        fresh.commit_prepared(&original.receipts()[0]),
        Err(Error::Narration)
    );
    branch_mut(&mut value, &root.branch)["local_receipts"][0]["play"]["prompt_version"] =
        json!("locallore-play-v2.0");
    value["payload"]["required_policies"][0]["prompt_version"] = json!("locallore-play-v2.0");
    rehash(&mut value);
    assert_eq!(
        validate_archive(&bytes(&value), &|| false).err(),
        Some(ArchiveError::Integrity)
    );
}

#[test]
fn nested_rewind_before_parent_birth_and_literal_code_like_story_text_roundtrip() {
    let temp = Temp::new();
    let mut source = Store::open(&temp.path("nested.sqlite"), None).unwrap();
    let seed = seed();
    let root = seed.scope.clone();
    source.create_story("Nested", seed).unwrap();
    for n in 0..5 {
        apply(
            &mut source,
            &root,
            &format!("root-{n}"),
            vec![Command::Wait { ticks: 1 }],
        );
    }
    let a = fork(&mut source, &root, "a", 5);
    apply(&mut source, &a, "later-a", vec![Command::Wait { ticks: 1 }]);
    let b = fork(&mut source, &a, "b", 1);
    apply(
        &mut source,
        &b,
        "literal",
        vec![Command::Say {
            text: "The note reads {\"a\":1,\"a\":2} and <script>nothing executes</script>.".into(),
            audience: ["mira".into()].into(),
        }],
    );
    let archive = source.export_archive(&root.story, &|| false).unwrap();
    let (mut target, _) = target(&temp, "target.sqlite");
    target
        .import_archive(
            validate_archive(archive.bytes(), &|| false).unwrap(),
            &|| false,
        )
        .unwrap();
    let actual = target.resume(&b).unwrap().engine;
    assert_eq!(actual.revision(), 2);
    assert_eq!(actual.state().story_time, 101);
    assert_eq!(actual.receipts()[0].request().scope, root);
    assert_eq!(actual.receipts()[1].request().scope, b);
    assert!(actual.receipts().iter().all(|r| r.request().scope != a));
    assert_eq!(
        actual.receipts(),
        source.resume(&b).unwrap().engine.receipts()
    );
}
