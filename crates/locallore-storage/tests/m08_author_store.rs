// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen before Store author implementation. All new cases initially UNRUN.
//! Direct SQL is confined to synthetic corruption/rollback fixtures.
use locallore::{
    author_correction::{
        AuthorCorrectionInputV1, AuthorCorrectionOperationV1, CanonicalRecord, AUTHOR_TURN_KEY,
    },
    contracts::*,
    engine::{parse_unique_json, Engine},
};
use locallore_storage::{ForkRequest, StorageError, Store, TurnError};
use rusqlite::{params, types::Value as SqlValue, Connection};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    path::PathBuf,
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT: AtomicU64 = AtomicU64::new(0);
struct Temp(PathBuf);
impl Temp {
    fn new() -> Self {
        let path = std::env::temp_dir().join(format!(
            "locallore-m08-author-store-{}-{}-{}",
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
    fn open(&self) -> Store {
        Store::open(&self.path(), None).unwrap()
    }
    fn sql(&self) -> Connection {
        Connection::open(self.path()).unwrap()
    }
}
impl Drop for Temp {
    fn drop(&mut self) {
        std::fs::remove_dir_all(&self.0).unwrap();
    }
}
fn setup(temp: &Temp) -> (Store, Scope) {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    let fact = seed.facts.get_mut("relic-location").unwrap();
    fact.proposition = "OBSERVED_A".into();
    fact.discoverable_at = Some("quay".into());
    fact.known_by.insert("mira".into());
    let root = seed.scope.clone();
    let mut store = temp.open();
    store.create_story("Synthetic author Store", seed).unwrap();
    (store, root)
}
fn apply(store: &mut Store, scope: &Scope, key: &str, commands: Vec<Command>) -> Receipt {
    let engine = store.resume(scope).unwrap().engine;
    let request = engine.request(key, Intent::Actions(commands));
    let proposal = Engine::proposal(&request).unwrap();
    let preview = engine.preview(&request, &proposal).unwrap();
    store.begin_turn(&request).unwrap();
    store.commit_prepared(&preview).unwrap()
}
fn wait(store: &mut Store, scope: &Scope, key: &str) {
    apply(store, scope, key, vec![Command::Wait { ticks: 1 }]);
}
fn fork(store: &mut Store, parent: &Scope, child: &str, at: u64) -> Scope {
    let head = store.resume(parent).unwrap().engine.revision();
    store
        .fork_branch(
            &ForkRequest {
                parent: parent.clone(),
                child_branch: child.into(),
                expected_parent_revision: head,
                at_revision: at,
            },
            &|| false,
        )
        .unwrap()
        .scope
}
fn input(
    store: &mut Store,
    parent: &Scope,
    child: &str,
    at: u64,
    old: &str,
    new: &str,
) -> AuthorCorrectionInputV1 {
    AuthorCorrectionInputV1 {
        version: 1,
        parent: parent.clone(),
        expected_parent_revision: store.resume(parent).unwrap().engine.revision(),
        fork_revision: at,
        child_branch: child.into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(),
            expected_proposition: old.into(),
            replacement: new.into(),
        },
        reason: "PRIVATE_STORE_AUTHOR_REASON".into(),
    }
}
fn create(store: &mut Store, request: &AuthorCorrectionInputV1) -> Scope {
    let plan = store.prepare_author_correction(request, &|| false).unwrap();
    let result = store.apply_author_correction(&plan, &|| false).unwrap();
    assert!(result.created);
    assert_eq!(result.parent, request.parent);
    assert_eq!(result.fork_revision, request.fork_revision);
    assert_eq!(result.author_revision, request.fork_revision + 1);
    assert_eq!(result.head_revision, result.author_revision);
    assert_eq!(result.scope.story, request.parent.story);
    assert_eq!(result.scope.branch, request.child_branch);
    result.scope
}
fn rows(db: &Connection) -> Vec<(&'static str, Vec<Vec<SqlValue>>)> {
    // Fixed application tables, no caller-supplied SQL or alternate evaluator.
    [
        "schema_migrations",
        "stories",
        "branches",
        "entities",
        "branch_entities",
        "turns",
        "accepted_events",
        "event_witnesses",
        "branch_projections",
        "derived_memory",
        "branch_retention",
        "memory_jobs",
        "memory_job_packets",
    ]
    .into_iter()
    .map(|table| {
        let mut q = db.prepare(&format!("SELECT * FROM {table}")).unwrap();
        let width = q.column_count();
        let mut values: Vec<Vec<SqlValue>> = q
            .query_map([], |r| (0..width).map(|n| r.get(n)).collect())
            .unwrap()
            .map(Result::unwrap)
            .collect();
        values.sort_by_key(|v| format!("{v:?}"));
        (table, values)
    })
    .collect()
}
fn count(db: &Connection, table: &str, scope: &Scope) -> i64 {
    assert!([
        "turns",
        "accepted_events",
        "event_witnesses",
        "derived_memory",
        "memory_jobs",
        "memory_job_packets"
    ]
    .contains(&table));
    db.query_row(
        &format!("SELECT count(*) FROM {table} WHERE story_id=?1 AND branch_id=?2"),
        params![scope.story, scope.branch],
        |r| r.get(0),
    )
    .unwrap()
}
fn retire(store: &mut Store, scope: &Scope) {
    let head = store.resume(scope).unwrap().engine.revision();
    let plan = store
        .prepare_branch_deletion(scope, head, &|| false)
        .unwrap();
    store.delete_branch(plan, &|| false).unwrap();
}

#[test]
fn atomic_author_row_normalization_index_projection_and_reopen_preserve_originals() {
    let temp = Temp::new();
    let (mut store, root) = setup(&temp);
    wait(&mut store, &root, "retained");
    let sibling = fork(&mut store, &root, "sibling", 1);
    wait(&mut store, &root, "excluded");
    let original = store.resume(&root).unwrap().engine;
    let sibling_before = store.resume(&sibling).unwrap().engine;
    let request = input(&mut store, &root, "authored", 1, "OBSERVED_A", "PRIVATE_B");
    let before = rows(&temp.sql());
    let plan = store
        .prepare_author_correction(&request, &|| false)
        .unwrap();
    assert_eq!(rows(&temp.sql()), before, "preparation must be read-only");
    let shown = plan.preview_bytes().to_vec();
    assert_eq!(
        parse_unique_json(&shown, 65536).unwrap(),
        serde_json::to_value(plan.preview()).unwrap()
    );
    let outcome = store.apply_author_correction(&plan, &|| false).unwrap();
    assert_eq!(plan.preview_bytes(), shown.as_slice());
    assert!(outcome.created);
    assert_eq!(outcome.parent, root);
    assert_eq!(
        (
            outcome.fork_revision,
            outcome.author_revision,
            outcome.head_revision
        ),
        (1, 2, 2)
    );
    let child = outcome.scope;
    let engine = store.resume(&child).unwrap().engine;
    assert_eq!(
        engine.state().story_time,
        original.at_revision(1).unwrap().state().story_time
    );
    assert_eq!(engine.domain_version(), 2);
    assert_eq!(engine.canonical_record_count(), 2);
    assert_eq!(engine.receipts().len(), 1);
    let db = temp.sql();
    let (kind, expected, index, response): (String, i64, String, String) = db.query_row(
        "SELECT canonical_kind,expected_revision,request_json,response_json FROM turns WHERE story_id=?1 AND branch_id=?2 AND turn_id=?3",
        params![child.story, child.branch, AUTHOR_TURN_KEY], |r| Ok((r.get(0)?,r.get(1)?,r.get(2)?,r.get(3)?))).unwrap();
    assert_eq!(kind, "author_v1");
    assert_eq!(expected, 1, "index guards fork f, not original parent H");
    let record = engine.canonical_records().last().unwrap();
    assert_eq!(
        serde_json::from_str::<Value>(&response).unwrap(),
        serde_json::to_value(record).unwrap()
    );
    let hash = format!("{:x}", Sha256::digest(serde_json::to_vec(record).unwrap()));
    assert_eq!(
        parse_unique_json(index.as_bytes(), 24576).unwrap(),
        json!({
            "version":1,"kind":"author_correction","scope":child,"turn":AUTHOR_TURN_KEY,
            "expected_revision":1,"record_sha256":hash
        })
    );
    let (normalized_kind, version, envelope): (String, u16, String) = db.query_row(
        "SELECT record_kind,event_version,envelope_json FROM accepted_events WHERE story_id=?1 AND branch_id=?2 AND sequence=2",
        params![child.story,child.branch], |r| Ok((r.get(0)?,r.get(1)?,r.get(2)?))).unwrap();
    assert_eq!(normalized_kind, "author_correction");
    assert_eq!(version, 1);
    let CanonicalRecord::AuthorV1(author) = record else {
        panic!("actual private author record required")
    };
    assert_eq!(envelope, serde_json::to_string(author).unwrap());
    assert_eq!(count(&db, "turns", &child), 1);
    assert_eq!(count(&db, "accepted_events", &child), 1);
    assert_eq!(count(&db, "event_witnesses", &child), 0);
    for table in ["derived_memory", "memory_jobs", "memory_job_packets"] {
        assert_eq!(count(&db, table, &child), 0);
    }
    let projection_version: u16 = db
        .query_row(
            "SELECT projection_version FROM branch_projections WHERE story_id=?1 AND branch_id=?2",
            params![child.story, child.branch],
            |r| r.get(0),
        )
        .unwrap();
    assert_eq!(projection_version, 2);
    drop(db);
    drop(store);
    let mut store = temp.open();
    let reopened = store.resume(&child).unwrap();
    assert!(!reopened.projection_needs_rebuild);
    assert_eq!(
        reopened.engine.canonical_records(),
        engine.canonical_records()
    );
    assert_eq!(
        reopened.engine.accepted_history_basis().unwrap(),
        engine.accepted_history_basis().unwrap()
    );
    assert_eq!(
        store
            .resume(&root)
            .unwrap()
            .engine
            .accepted_history_basis()
            .unwrap(),
        original.accepted_history_basis().unwrap()
    );
    assert_eq!(
        store.resume(&sibling).unwrap().engine.canonical_bytes(),
        sibling_before.canonical_bytes()
    );
}

#[test]
fn valid_escaped_author_input_uses_small_index_without_widening_ordinary_limit() {
    let temp = Temp::new();
    let (mut store, root) = setup(&temp);
    let mut request = input(
        &mut store,
        &root,
        "escaped",
        0,
        "OBSERVED_A",
        &"\u{0000}".repeat(2048),
    );
    request.reason = "\u{0001}".repeat(2048);
    assert!(serde_json::to_vec(&request).unwrap().len() > 24576);
    let child = create(&mut store, &request);
    let db = temp.sql();
    let (index, response): (String, String) = db
        .query_row(
            "SELECT request_json,response_json FROM turns WHERE story_id=?1 AND branch_id=?2",
            params![child.story, child.branch],
            |r| Ok((r.get(0)?, r.get(1)?)),
        )
        .unwrap();
    assert!(index.len() < 24576);
    assert!(!index.contains("replacement") && !index.contains("reason"));
    assert_eq!(
        serde_json::from_str::<Value>(&response).unwrap()["receipt"]["input"],
        serde_json::to_value(&request).unwrap()
    );
    let ordinary = json!({"padding":"x".repeat(24576)}).to_string();
    assert!(db.execute("INSERT INTO turns(story_id,branch_id,turn_id,expected_revision,status,request_json,response_json,canonical_kind) VALUES(?1,?2,'oversized-ordinary',0,'draft',?3,NULL,'legacy_play')", params![root.story,root.branch,ordinary]).is_err());
    drop(db);
    drop(store);
    let mut store = temp.open();
    assert!(store
        .lookup_author_correction(&request, &|| false)
        .unwrap()
        .is_some());
    assert_eq!(
        store
            .resume(&child)
            .unwrap()
            .engine
            .effective_fact("relic-location")
            .unwrap()
            .proposition,
        "\u{0000}".repeat(2048)
    );
}

#[test]
fn observed_values_repeated_discoveries_and_a_b_a_survive_actual_store_reopen() {
    let temp = Temp::new();
    let (mut store, root) = setup(&temp);
    let request = input(&mut store, &root, "b", 0, "OBSERVED_A", "PRIVATE_B");
    let b = create(&mut store, &request);
    let e = store.resume(&b).unwrap().engine;
    for actor in ["player", "mira"] {
        assert_eq!(
            e.observed_facts(actor, &b, e.revision()).unwrap()["relic-location"].proposition,
            "OBSERVED_A"
        );
    }
    apply(
        &mut store,
        &b,
        "twice",
        vec![
            Command::Discover {
                fact: "relic-location".into(),
            },
            Command::Discover {
                fact: "relic-location".into(),
            },
        ],
    );
    let e = store.resume(&b).unwrap().engine;
    assert_eq!(
        e.observed_facts("player", &b, e.revision()).unwrap()["relic-location"].proposition,
        "PRIVATE_B"
    );
    assert_eq!(
        e.observed_facts("mira", &b, e.revision()).unwrap()["relic-location"].proposition,
        "OBSERVED_A"
    );
    let again = input(
        &mut store,
        &b,
        "again-a",
        e.revision(),
        "PRIVATE_B",
        "OBSERVED_A",
    );
    let a = create(&mut store, &again);
    let e = store.resume(&a).unwrap().engine;
    assert_eq!(
        e.observed_facts("player", &a, e.revision()).unwrap()["relic-location"].proposition,
        "PRIVATE_B"
    );
    apply(
        &mut store,
        &a,
        "rediscover-a",
        vec![Command::Discover {
            fact: "relic-location".into(),
        }],
    );
    let before = store.resume(&a).unwrap().engine;
    drop(store);
    let e = temp.open().resume(&a).unwrap().engine;
    assert_eq!(e.canonical_records(), before.canonical_records());
    assert_eq!(
        e.accepted_history_basis().unwrap(),
        before.accepted_history_basis().unwrap()
    );
    let context = e.character_context_v2("player", &a, e.revision()).unwrap();
    let values: Vec<_> = context
        .observations
        .iter()
        .filter_map(|v| v.discovery.as_ref())
        .map(|v| v.proposition.as_str())
        .collect();
    assert_eq!(values, vec!["PRIVATE_B", "PRIVATE_B", "OBSERVED_A"]);
    let npc =
        serde_json::to_string(&e.character_context_v2("mira", &a, e.revision()).unwrap()).unwrap();
    assert!(!npc.contains("PRIVATE_B") && !npc.contains("PRIVATE_STORE_AUTHOR_REASON"));
}

#[test]
fn foreign_same_file_cloned_and_reopened_store_cannot_use_native_preparation() {
    let temp = Temp::new();
    let (mut owner, root) = setup(&temp);
    let request = input(&mut owner, &root, "child", 0, "OBSERVED_A", "PRIVATE_B");
    let plan = owner
        .prepare_author_correction(&request, &|| false)
        .unwrap();
    let before = rows(&temp.sql());
    let mut foreign = temp.open();
    assert!(matches!(
        foreign.apply_author_correction(&plan, &|| false),
        Err(TurnError::Integrity)
    ));
    assert_eq!(rows(&temp.sql()), before);
    let clone_path = temp.0.join("clone.sqlite");
    owner.backup_to(&clone_path).unwrap();
    let mut cloned = Store::open(&clone_path, None).unwrap();
    assert_eq!(
        owner
            .resume(&root)
            .unwrap()
            .engine
            .accepted_history_basis()
            .unwrap(),
        cloned
            .resume(&root)
            .unwrap()
            .engine
            .accepted_history_basis()
            .unwrap()
    );
    assert!(matches!(
        cloned.apply_author_correction(&plan, &|| false),
        Err(TurnError::Integrity)
    ));
    drop(foreign);
    drop(owner);
    let mut reopened = temp.open();
    assert!(matches!(
        reopened.apply_author_correction(&plan, &|| false),
        Err(TurnError::Integrity)
    ));
    assert_eq!(rows(&temp.sql()), before);
    let fresh = reopened
        .prepare_author_correction(&request, &|| false)
        .unwrap();
    assert!(
        reopened
            .apply_author_correction(&fresh, &|| false)
            .unwrap()
            .created
    );
}

#[test]
fn actual_parent_advance_stales_prepared_creation_without_child_or_draft_mutation() {
    let temp = Temp::new();
    let (mut store, root) = setup(&temp);
    let request = input(&mut store, &root, "child", 0, "OBSERVED_A", "PRIVATE_B");
    let plan = store
        .prepare_author_correction(&request, &|| false)
        .unwrap();
    wait(&mut store, &root, "later");
    let before = rows(&temp.sql());
    assert!(matches!(
        store.apply_author_correction(&plan, &|| false),
        Err(TurnError::Stale)
    ));
    assert_eq!(rows(&temp.sql()), before);
    assert!(store
        .lookup_author_correction(&request, &|| false)
        .unwrap()
        .is_none());
}

#[test]
fn valid_same_head_replacement_seed_stales_full_source_guard() {
    let temp = Temp::new();
    let (mut store, root) = setup(&temp);
    let request = input(&mut store, &root, "child", 0, "OBSERVED_A", "PRIVATE_B");
    let plan = store
        .prepare_author_correction(&request, &|| false)
        .unwrap();
    let mut changed = store.resume(&root).unwrap().engine.seed().clone();
    changed.facts.get_mut("beacon-mark").unwrap().proposition =
        "Different valid hidden source".into();
    let db = temp.sql();
    db.execute(
        "UPDATE stories SET seed_json=?2 WHERE story_id=?1",
        params![root.story, serde_json::to_string(&changed).unwrap()],
    )
    .unwrap();
    let actual = store.resume(&root).unwrap().engine;
    assert_eq!(actual.revision(), 0);
    assert_eq!(
        actual.effective_fact("relic-location").unwrap().proposition,
        "OBSERVED_A"
    );
    let before = rows(&db);
    assert!(matches!(
        store.apply_author_correction(&plan, &|| false),
        Err(TurnError::Stale)
    ));
    assert_eq!(rows(&db), before);
}

#[test]
fn exact_lookup_is_read_only_after_progress_and_full_input_mismatch_refuses() {
    let temp = Temp::new();
    let (mut store, root) = setup(&temp);
    wait(&mut store, &root, "parent-creation-head");
    let request = input(&mut store, &root, "child", 0, "OBSERVED_A", "PRIVATE_B");
    let child = create(&mut store, &request);
    wait(&mut store, &child, "child-progress");
    wait(&mut store, &root, "parent-progress");
    let before = rows(&temp.sql());
    let result = store
        .lookup_author_correction(&request, &|| false)
        .unwrap()
        .unwrap();
    assert!(!result.created);
    assert_eq!((result.author_revision, result.head_revision), (1, 2));
    assert_eq!(result.scope, child);
    for variant in 0..4 {
        let mut bad = request.clone();
        match variant {
            0 => bad.reason.push('!'),
            1 => bad.expected_parent_revision += 1,
            2 => bad.fork_revision += 1,
            _ => {
                bad.operation = AuthorCorrectionOperationV1::ReplaceFactProposition {
                    fact: "relic-location".into(),
                    expected_proposition: "OBSERVED_A".into(),
                    replacement: "DIFFERENT_B".into(),
                }
            }
        }
        assert!(matches!(
            store.lookup_author_correction(&bad, &|| false),
            Err(TurnError::RetryMismatch)
        ));
    }
    let mut missing = request.clone();
    missing.child_branch = "never-created".into();
    missing.parent.branch = "missing-parent".into();
    assert!(store
        .lookup_author_correction(&missing, &|| false)
        .unwrap()
        .is_none());
    assert_eq!(rows(&temp.sql()), before);
}

#[test]
fn symmetric_child_kind_and_ordinary_author_key_occupants_fail_without_writes() {
    let temp = Temp::new();
    let (mut store, root) = setup(&temp);
    let request = input(&mut store, &root, "authored", 0, "OBSERVED_A", "PRIVATE_B");
    let child = create(&mut store, &request);
    let ordinary = fork(&mut store, &root, "ordinary", 0);
    wait(&mut store, &ordinary, AUTHOR_TURN_KEY);
    let mut conflicting = request.clone();
    conflicting.child_branch = ordinary.branch.clone();
    let before = rows(&temp.sql());
    assert!(matches!(
        store.lookup_author_correction(&conflicting, &|| false),
        Err(TurnError::RetryMismatch)
    ));
    assert!(matches!(
        store.fork_branch(
            &ForkRequest {
                parent: root.clone(),
                child_branch: child.branch.clone(),
                expected_parent_revision: 0,
                at_revision: 0
            },
            &|| false
        ),
        Err(TurnError::RetryMismatch)
    ));
    let engine = store.resume(&child).unwrap().engine;
    let ordinary_request = engine.request(
        AUTHOR_TURN_KEY,
        Intent::Actions(vec![Command::Wait { ticks: 1 }]),
    );
    assert!(matches!(
        store.begin_turn(&ordinary_request),
        Err(TurnError::RetryMismatch)
    ));
    assert!(matches!(
        store.turn_status(&ordinary_request),
        Err(TurnError::RetryMismatch)
    ));
    assert!(matches!(
        store.lookup_turn(&child, AUTHOR_TURN_KEY),
        Err(TurnError::RetryMismatch)
    ));
    assert!(matches!(
        store.cancel_turn(&ordinary_request),
        Err(TurnError::RetryMismatch)
    ));
    assert_eq!(rows(&temp.sql()), before);
    let unrelated = fork(&mut store, &child, "unrelated-key", engine.revision());
    wait(&mut store, &unrelated, AUTHOR_TURN_KEY);
}

#[test]
fn cancelled_panicking_and_invalid_preparations_never_create_partial_children() {
    let temp = Temp::new();
    let (mut store, root) = setup(&temp);
    let request = input(&mut store, &root, "child", 0, "OBSERVED_A", "PRIVATE_B");
    let before = rows(&temp.sql());
    assert!(matches!(
        store.prepare_author_correction(&request, &|| true),
        Err(TurnError::Engine(Error::Cancelled))
    ));
    assert!(matches!(
        store.prepare_author_correction(&request, &|| panic!("synthetic cancel")),
        Err(TurnError::Engine(Error::Cancelled))
    ));
    let plan = store
        .prepare_author_correction(&request, &|| false)
        .unwrap();
    assert!(matches!(
        store.apply_author_correction(&plan, &|| true),
        Err(TurnError::Engine(Error::Cancelled))
    ));
    assert!(matches!(
        store.apply_author_correction(&plan, &|| panic!("synthetic cancel")),
        Err(TurnError::Engine(Error::Cancelled))
    ));
    let mut bad = request.clone();
    bad.reason = "x".repeat(2049);
    assert!(store.prepare_author_correction(&bad, &|| false).is_err());
    bad = request.clone();
    bad.child_branch = "../invalid".into();
    assert!(store.prepare_author_correction(&bad, &|| false).is_err());
    assert_eq!(rows(&temp.sql()), before);
    apply(
        &mut store,
        &root,
        "two-events",
        vec![Command::Wait { ticks: 1 }, Command::Wait { ticks: 1 }],
    );
    let bad = input(&mut store, &root, "mid-turn", 1, "OBSERVED_A", "PRIVATE_B");
    let before = rows(&temp.sql());
    assert!(store.prepare_author_correction(&bad, &|| false).is_err());
    assert_eq!(rows(&temp.sql()), before);
}

#[test]
fn actual_sqlite_abort_during_author_normalization_rolls_back_every_application_row() {
    let temp = Temp::new();
    let (mut store, root) = setup(&temp);
    let request = input(&mut store, &root, "child", 0, "OBSERVED_A", "PRIVATE_B");
    let plan = store
        .prepare_author_correction(&request, &|| false)
        .unwrap();
    let db = temp.sql();
    db.execute_batch("CREATE TRIGGER synthetic_author_abort BEFORE INSERT ON accepted_events WHEN NEW.record_kind='author_correction' BEGIN SELECT RAISE(ABORT,'synthetic author normalization failure'); END;").unwrap();
    let before = rows(&db);
    assert!(matches!(
        store.apply_author_correction(&plan, &|| false),
        Err(TurnError::Storage(StorageError::Database))
    ));
    assert_eq!(rows(&db), before);
    db.execute_batch("DROP TRIGGER synthetic_author_abort;")
        .unwrap();
    assert!(store
        .lookup_author_correction(&request, &|| false)
        .unwrap()
        .is_none());
    let fresh = store
        .prepare_author_correction(&request, &|| false)
        .unwrap();
    assert!(
        store
            .apply_author_correction(&fresh, &|| false)
            .unwrap()
            .created
    );
}

#[test]
fn author_normalization_index_witness_and_even_rehashed_unknown_wrapper_tamper_fail_closed() {
    for case in 0..6 {
        let temp = Temp::new();
        let (mut store, root) = setup(&temp);
        let request = input(&mut store, &root, "child", 0, "OBSERVED_A", "PRIVATE_B");
        let child = create(&mut store, &request);
        let db = temp.sql();
        match case {
            0 => {
                db.execute("UPDATE accepted_events SET envelope_json=json_set(envelope_json,'$.story_time',999) WHERE branch_id=?1",[&child.branch]).unwrap();
            }
            1 => {
                db.execute("UPDATE turns SET request_json=json_set(request_json,'$.expected_revision',9) WHERE branch_id=?1",[&child.branch]).unwrap();
            }
            2 => {
                db.execute("INSERT INTO event_witnesses(story_id,branch_id,sequence,observer_id) VALUES(?1,?2,1,'mira')",params![child.story,child.branch]).unwrap();
            }
            3 => {
                db.execute(
                    "UPDATE accepted_events SET record_kind='play' WHERE branch_id=?1",
                    [&child.branch],
                )
                .unwrap();
            }
            4 => {
                db.execute(
                    "UPDATE turns SET canonical_kind='legacy_play' WHERE branch_id=?1",
                    [&child.branch],
                )
                .unwrap();
            }
            _ => {
                let (response, index): (String, String) = db
                    .query_row(
                        "SELECT response_json,request_json FROM turns WHERE branch_id=?1",
                        [&child.branch],
                        |r| Ok((r.get(0)?, r.get(1)?)),
                    )
                    .unwrap();
                let mut response: Value = serde_json::from_str(&response).unwrap();
                response["unexpected"] = json!(true);
                let mut index: Value = serde_json::from_str(&index).unwrap();
                index["record_sha256"] = json!(format!(
                    "{:x}",
                    Sha256::digest(serde_json::to_vec(&response).unwrap())
                ));
                db.execute(
                    "UPDATE turns SET response_json=?2,request_json=?3 WHERE branch_id=?1",
                    params![child.branch, response.to_string(), index.to_string()],
                )
                .unwrap();
            }
        }
        let before = rows(&db);
        assert!(
            matches!(store.resume(&child), Err(TurnError::Integrity)),
            "case {case}"
        );
        assert!(
            matches!(
                store.lookup_author_correction(&request, &|| false),
                Err(TurnError::Integrity)
            ),
            "case {case}"
        );
        assert_eq!(
            rows(&db),
            before,
            "corruption must not repair or hide evidence"
        );
    }
}

#[test]
fn exact_recovery_survives_nonroot_parent_retirement_and_collection_of_excluded_future() {
    let temp = Temp::new();
    let (mut store, root) = setup(&temp);
    wait(&mut store, &root, "root-retained");
    let parent = fork(&mut store, &root, "parent", 1);
    wait(&mut store, &parent, "excluded-parent-future");
    let request = input(&mut store, &parent, "child", 1, "OBSERVED_A", "PRIVATE_B");
    assert_eq!(request.expected_parent_revision, 2);
    let child = create(&mut store, &request);
    wait(&mut store, &child, "child-later");
    retire(&mut store, &parent);
    assert!(matches!(
        store.resume(&parent),
        Err(TurnError::Storage(StorageError::NotFound))
    ));
    let db = temp.sql();
    let parent_head: i64 = db
        .query_row(
            "SELECT head_revision FROM branches WHERE branch_id=?1",
            [&parent.branch],
            |r| r.get(0),
        )
        .unwrap();
    assert_eq!(parent_head, 1);
    assert_eq!(count(&db, "turns", &parent), 0);
    let before = rows(&db);
    let found = store
        .lookup_author_correction(&request, &|| false)
        .unwrap()
        .unwrap();
    assert_eq!(found.head_revision, 3);
    assert!(!found.created);
    assert_eq!(rows(&db), before);
    drop(db);
    drop(store);
    let mut reopened = temp.open();
    assert_eq!(
        reopened
            .lookup_author_correction(&request, &|| false)
            .unwrap()
            .unwrap()
            .head_revision,
        3
    );
}

#[test]
fn prebirth_fork_retention_and_collected_author_tombstone_never_resurrect_identity() {
    let temp = Temp::new();
    let (mut store, root) = setup(&temp);
    wait(&mut store, &root, "retained");
    wait(&mut store, &root, "excluded");
    let request = input(&mut store, &root, "authored", 1, "OBSERVED_A", "PRIVATE_B");
    let authored = create(&mut store, &request);
    let early = fork(&mut store, &authored, "prebirth", 0);
    wait(&mut store, &early, "early-progress");
    let early_before = store.resume(&early).unwrap().engine;
    assert_eq!(early_before.domain_version(), 1);
    assert_eq!(
        early_before
            .effective_fact("relic-location")
            .unwrap()
            .proposition,
        "OBSERVED_A"
    );
    retire(&mut store, &authored);
    assert_eq!(
        store
            .resume(&early)
            .unwrap()
            .engine
            .accepted_history_basis()
            .unwrap(),
        early_before.accepted_history_basis().unwrap()
    );
    let before = rows(&temp.sql());
    assert!(matches!(
        store.lookup_author_correction(&request, &|| false),
        Err(TurnError::Storage(StorageError::NotFound))
    ));
    assert_eq!(rows(&temp.sql()), before);
    retire(&mut store, &early);
    let before = rows(&temp.sql());
    assert!(matches!(
        store.lookup_author_correction(&request, &|| false),
        Err(TurnError::Storage(StorageError::NotFound))
    ));
    assert!(store
        .prepare_author_correction(&request, &|| false)
        .is_err());
    assert_eq!(rows(&temp.sql()), before);
    let reserved: i64 = temp
        .sql()
        .query_row(
            "SELECT count(*) FROM branch_retention WHERE story_id=?1 AND branch_id=?2",
            params![authored.story, authored.branch],
            |r| r.get(0),
        )
        .unwrap();
    assert_eq!(reserved, 1);
}
