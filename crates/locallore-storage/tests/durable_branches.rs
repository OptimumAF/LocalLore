use locallore::{contracts::*, engine::Engine};
use locallore_storage::{
    derived_memory, ForkRequest, StorageError, Store, TurnError, MAX_BRANCHES_PER_STORY,
    MAX_BRANCH_DEPTH,
};
use rusqlite::{params, Connection};
use std::{
    cell::Cell,
    path::PathBuf,
    sync::{
        atomic::{AtomicU64, Ordering},
        Arc, Barrier,
    },
};
static NEXT: AtomicU64 = AtomicU64::new(0);
struct Temp(PathBuf);
impl Temp {
    fn new() -> Self {
        let directory = std::env::temp_dir().join(format!(
            "locallore-branches-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&directory).unwrap();
        Self(directory)
    }
    fn path(&self) -> PathBuf {
        self.0.join("synthetic.sqlite")
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
fn setup(temp: &Temp) -> (Store, Scope) {
    let mut store = Store::open(&temp.path(), None).unwrap();
    let seed = seed();
    let scope = seed.scope.clone();
    store.create_story("Synthetic branches", seed).unwrap();
    (store, scope)
}
fn apply(store: &mut Store, scope: &Scope, id: &str, commands: Vec<Command>) -> Receipt {
    let engine = store.resume(scope).unwrap().engine;
    let request = engine.request(id, Intent::Actions(commands));
    let proposal = Engine::proposal(&request).unwrap();
    let narration = engine
        .preview(&request, &proposal)
        .unwrap()
        .narration()
        .to_owned();
    store.begin_turn(&request).unwrap();
    store.commit_turn(&request, &proposal, &narration).unwrap()
}
fn wait(store: &mut Store, scope: &Scope, id: &str) -> Receipt {
    apply(store, scope, id, vec![Command::Wait { ticks: 1 }])
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
fn count(db: &Connection, table: &str, scope: &Scope) -> i64 {
    assert!([
        "turns",
        "accepted_events",
        "event_witnesses",
        "derived_memory"
    ]
    .contains(&table));
    db.query_row(
        &format!("SELECT count(*) FROM {table} WHERE story_id=?1 AND branch_id=?2"),
        params![scope.story, scope.branch],
        |r| r.get(0),
    )
    .unwrap()
}

#[test]
fn durable_fork_keeps_source_scopes_independent_effects_and_exact_local_retries() {
    let temp = Temp::new();
    let (mut store, root) = setup(&temp);
    let inherited = wait(&mut store, &root, "before");
    let child = fork(&mut store, &root, "child", 1);
    let parent_receipt = apply(
        &mut store,
        &root,
        "same-key",
        vec![Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 1,
        }],
    );
    let parent_bytes = store.resume(&root).unwrap().engine.canonical_bytes();
    let child_receipt = apply(
        &mut store,
        &child,
        "same-key",
        vec![Command::Consume {
            item: "potion".into(),
        }],
    );
    let sibling = fork(&mut store, &root, "sibling", 1);
    assert_eq!(
        store.resume(&sibling).unwrap().engine.state().items["potion"].owner,
        "player"
    );
    let saved = store.resume(&child).unwrap().engine;
    assert!(!saved.state().items.contains_key("potion"));
    assert_eq!(saved.receipts(), [inherited, child_receipt.clone()]);
    assert_eq!(saved.receipts()[0].request().scope, root);
    assert_eq!(saved.receipts()[1].request().scope, child);
    assert!(saved
        .character_context("mira", &child, saved.revision())
        .unwrap()
        .observations
        .is_empty());
    let observed = saved
        .character_context("player", &child, saved.revision())
        .unwrap();
    assert!(!observed
        .observations
        .iter()
        .any(|e| e.scope() == &root && e.sequence() == 2));
    let db = Connection::open(temp.path()).unwrap();
    assert_eq!(count(&db, "accepted_events", &child), 1);
    assert_eq!(count(&db, "turns", &child), 1);
    assert_eq!(count(&db, "derived_memory", &child), 0);
    assert_eq!(
        store.lookup_turn(&child, "before").unwrap_err(),
        TurnError::UnknownTurn
    );
    drop(store);
    let mut store = Store::open(&temp.path(), None).unwrap();
    assert_eq!(
        store.resume(&child).unwrap().engine.canonical_bytes(),
        saved.canonical_bytes()
    );
    assert_eq!(
        store.begin_turn(child_receipt.request()).unwrap().receipt,
        Some(child_receipt.clone())
    );
    assert_eq!(
        store.commit_prepared(&child_receipt).unwrap(),
        child_receipt
    );
    assert_eq!(
        store.commit_prepared(&parent_receipt).unwrap(),
        parent_receipt
    );
    assert_eq!(count(&db, "accepted_events", &child), 1);
    assert_eq!(
        store.resume(&root).unwrap().engine.canonical_bytes(),
        parent_bytes
    );
}

#[test]
fn fork_identity_is_immutable_and_expected_head_is_only_new_creation_admission() {
    let temp = Temp::new();
    let (mut store, root) = setup(&temp);
    wait(&mut store, &root, "before");
    let mut request = ForkRequest {
        parent: root.clone(),
        child_branch: "child".into(),
        expected_parent_revision: 1,
        at_revision: 1,
    };
    assert!(store.fork_branch(&request, &|| false).unwrap().created);
    let child = Scope {
        story: root.story.clone(),
        branch: "child".into(),
    };
    wait(&mut store, &root, "parent-later");
    wait(&mut store, &child, "child-later");
    request.expected_parent_revision = u64::MAX;
    let existing = store.fork_branch(&request, &|| false).unwrap();
    assert!(!existing.created);
    assert_eq!(existing.head_revision, 2);
    request.at_revision = 0;
    assert_eq!(
        store.fork_branch(&request, &|| false),
        Err(TurnError::RetryMismatch)
    );
    request.child_branch = "new".into();
    assert_eq!(
        store.fork_branch(&request, &|| false),
        Err(TurnError::Stale)
    );
    request.expected_parent_revision = 2;
    let new = store.fork_branch(&request, &|| false).unwrap();
    assert_eq!(new.head_revision, 0);
    let first = wait(&mut store, &new.scope, "first");
    assert_eq!(first.events()[0].sequence(), 1);
}

#[test]
fn cancelled_and_sql_failed_forks_leave_no_child_or_partial_registry_or_projection() {
    let temp = Temp::new();
    let (mut store, root) = setup(&temp);
    let before = store.resume(&root).unwrap().engine.canonical_bytes();
    let db = Connection::open(temp.path()).unwrap();
    for threshold in 1..=5 {
        let checks = Cell::new(0);
        let request = ForkRequest {
            parent: root.clone(),
            child_branch: format!("cancel-{threshold}"),
            expected_parent_revision: 0,
            at_revision: 0,
        };
        let result = store.fork_branch(&request, &|| {
            checks.set(checks.get() + 1);
            checks.get() >= threshold
        });
        assert_eq!(result, Err(TurnError::Engine(Error::Cancelled)));
        assert_eq!(
            db.query_row(
                "SELECT count(*) FROM branches WHERE branch_id=?1",
                [&request.child_branch],
                |r| r.get::<_, i64>(0)
            )
            .unwrap(),
            0
        );
    }
    let request = ForkRequest {
        parent: root.clone(),
        child_branch: "panic".into(),
        expected_parent_revision: 0,
        at_revision: 0,
    };
    assert_eq!(
        store.fork_branch(&request, &|| panic!("synthetic cancel panic")),
        Err(TurnError::Engine(Error::Cancelled))
    );
    db.execute_batch("CREATE TRIGGER synthetic_fork_abort AFTER INSERT ON branch_projections WHEN new.branch_id='sql-failure' BEGIN SELECT RAISE(ABORT,'synthetic'); END;").unwrap();
    let mut request = request;
    request.child_branch = "sql-failure".into();
    assert_eq!(
        store.fork_branch(&request, &|| false),
        Err(TurnError::Storage(StorageError::Database))
    );
    assert_eq!(
        db.query_row("SELECT count(*) FROM branches", [], |r| r.get::<_, i64>(0))
            .unwrap(),
        1
    );
    assert_eq!(
        db.query_row("SELECT count(*) FROM branch_projections", [], |r| r
            .get::<_, i64>(0))
            .unwrap(),
        1
    );
    db.execute_batch("DROP TRIGGER synthetic_fork_abort")
        .unwrap();
    assert_eq!(
        store.resume(&root).unwrap().engine.canonical_bytes(),
        before
    );
    assert!(store.fork_branch(&request, &|| false).unwrap().created);
}

#[test]
fn nested_rewind_before_parent_birth_replays_only_correct_ancestor_prefixes() {
    let temp = Temp::new();
    let (mut store, root) = setup(&temp);
    for n in 0..5 {
        wait(&mut store, &root, &format!("root-{n}"));
    }
    let a = fork(&mut store, &root, "a", 5);
    wait(&mut store, &a, "excluded-a");
    let b = fork(&mut store, &a, "b", 1);
    wait(&mut store, &b, "included-b");
    let c = fork(&mut store, &b, "c", 2);
    drop(store);
    let mut store = Store::open(&temp.path(), None).unwrap();
    let engine = store.resume(&c).unwrap().engine;
    assert_eq!(engine.revision(), 2);
    assert_eq!(engine.state().story_time, 102);
    assert_eq!(engine.receipts().len(), 2);
    assert_eq!(engine.receipts()[0].request().scope, root);
    assert_eq!(engine.receipts()[1].request().scope, b);
    let context = engine.character_context("player", &c, 2).unwrap();
    assert_eq!(context.observations.len(), 2);
    assert!(!context.observations.iter().any(|e| e.scope() == &a));
}

#[test]
fn partial_future_foreign_and_duplicate_branch_inputs_fail_without_mutation() {
    let temp = Temp::new();
    let (mut store, root) = setup(&temp);
    apply(
        &mut store,
        &root,
        "multi",
        vec![Command::Wait { ticks: 1 }, Command::Wait { ticks: 1 }],
    );
    for (id, at) in [("partial", 1), ("future", 3), ("bad id", 0), ("main", 0)] {
        let r = ForkRequest {
            parent: root.clone(),
            child_branch: id.into(),
            expected_parent_revision: 2,
            at_revision: at,
        };
        assert!(store.fork_branch(&r, &|| false).is_err());
    }
    let child = fork(&mut store, &root, "child", 2);
    let mut other = seed();
    other.scope.story = "other".into();
    let other_scope = other.scope.clone();
    store.create_story("Other", other).unwrap();
    assert_eq!(
        store
            .resume(&Scope {
                story: other_scope.story.clone(),
                branch: child.branch
            })
            .err(),
        Some(TurnError::Storage(StorageError::NotFound))
    );
    let db = Connection::open(temp.path()).unwrap();
    assert_eq!(
        db.query_row(
            "SELECT count(*) FROM branches WHERE story_id=?1",
            [&root.story],
            |r| r.get::<_, i64>(0)
        )
        .unwrap(),
        2
    );
}

#[test]
fn cycle_missing_parent_future_link_and_inherited_source_tamper_fail_closed() {
    let temp = Temp::new();
    let (mut store, root) = setup(&temp);
    wait(&mut store, &root, "before");
    let a = fork(&mut store, &root, "a", 1);
    let b = fork(&mut store, &a, "b", 1);
    let db = Connection::open(temp.path()).unwrap();
    db.execute(
        "UPDATE branches SET parent_branch='b' WHERE branch_id='a'",
        [],
    )
    .unwrap();
    assert_eq!(store.resume(&b).err(), Some(TurnError::Integrity));
    db.execute(
        "UPDATE branches SET parent_branch=?1 WHERE branch_id='a'",
        [&root.branch],
    )
    .unwrap();
    db.execute(
        "UPDATE branches SET fork_revision=2,head_revision=2 WHERE branch_id='b'",
        [],
    )
    .unwrap();
    assert_eq!(store.resume(&b).err(), Some(TurnError::Integrity));
    // Simulate external file damage, outside the configured Store's FK boundary.
    db.execute_batch("PRAGMA foreign_keys=OFF").unwrap();
    db.execute("UPDATE branches SET fork_revision=1,head_revision=1,parent_branch='missing' WHERE branch_id='b'",[]).unwrap();
    assert_eq!(store.resume(&b).err(), Some(TurnError::Integrity));
    db.execute(
        "UPDATE branches SET parent_branch='a' WHERE branch_id='b'",
        [],
    )
    .unwrap();
    db.execute("UPDATE accepted_events SET envelope_json=json_set(envelope_json,'$.sequence',99) WHERE branch_id=?1",[&root.branch]).unwrap();
    assert_eq!(store.resume(&a).err(), Some(TurnError::Integrity));
}

#[test]
fn later_parent_tamper_does_not_enter_child_replay_and_projection_never_establishes_canon() {
    let temp = Temp::new();
    let (mut store, root) = setup(&temp);
    wait(&mut store, &root, "before");
    let child = fork(&mut store, &root, "child", 1);
    wait(&mut store, &root, "future");
    let before = store.resume(&child).unwrap().engine.canonical_bytes();
    let db = Connection::open(temp.path()).unwrap();
    db.execute("UPDATE accepted_events SET envelope_json=json_set(envelope_json,'$.sequence',99) WHERE branch_id=?1 AND sequence=2",[&root.branch]).unwrap();
    assert_eq!(store.resume(&root).err(), Some(TurnError::Integrity));
    db.execute(
        "UPDATE branch_projections SET projection_json='{}' WHERE branch_id='child'",
        [],
    )
    .unwrap();
    let resumed = store.resume(&child).unwrap();
    assert!(resumed.projection_needs_rebuild);
    assert_eq!(resumed.engine.canonical_bytes(), before);
    assert_eq!(
        store
            .rebuild_projection(&child)
            .unwrap()
            .engine
            .canonical_bytes(),
        before
    );
}

#[test]
fn competing_fork_owners_create_once_and_depth_and_story_capacity_are_bounded() {
    let temp = Temp::new();
    let (mut store, root) = setup(&temp);
    let request = ForkRequest {
        parent: root.clone(),
        child_branch: "race".into(),
        expected_parent_revision: 0,
        at_revision: 0,
    };
    let barrier = Arc::new(Barrier::new(2));
    let threads: Vec<_> = (0..2)
        .map(|_| {
            let path = temp.path();
            let barrier = barrier.clone();
            let request = request.clone();
            std::thread::spawn(move || {
                let mut owner = Store::open(&path, None).unwrap();
                barrier.wait();
                owner.fork_branch(&request, &|| false)
            })
        })
        .collect();
    let outcomes: Vec<_> = threads
        .into_iter()
        .map(|t| t.join().unwrap().unwrap())
        .collect();
    assert_eq!(outcomes.iter().filter(|o| o.created).count(), 1);
    let mut parent = root.clone();
    for n in 1..MAX_BRANCH_DEPTH {
        parent = fork(&mut store, &parent, &format!("depth-{n}"), 0);
    }
    assert_eq!(
        store.fork_branch(
            &ForkRequest {
                parent,
                child_branch: "too-deep".into(),
                expected_parent_revision: 0,
                at_revision: 0
            },
            &|| false
        ),
        Err(TurnError::TooLarge)
    );
    let db = Connection::open(temp.path()).unwrap();
    let current: i64 = db
        .query_row("SELECT count(*) FROM branches", [], |r| r.get(0))
        .unwrap();
    for n in current as usize..MAX_BRANCHES_PER_STORY - 1 {
        fork(&mut store, &root, &format!("cap-{n}"), 0);
    }
    let barrier = Arc::new(Barrier::new(2));
    let threads: Vec<_> = (0..2)
        .map(|n| {
            let path = temp.path();
            let barrier = barrier.clone();
            let root = root.clone();
            std::thread::spawn(move || {
                let mut owner = Store::open(&path, None).unwrap();
                barrier.wait();
                owner.fork_branch(
                    &ForkRequest {
                        parent: root,
                        child_branch: format!("last-cap-{n}"),
                        expected_parent_revision: 0,
                        at_revision: 0,
                    },
                    &|| false,
                )
            })
        })
        .collect();
    let outcomes: Vec<_> = threads.into_iter().map(|t| t.join().unwrap()).collect();
    assert_eq!(outcomes.iter().filter(|r| r.is_ok()).count(), 1);
    assert!(outcomes
        .iter()
        .filter_map(|r| r.as_ref().err())
        .all(|e| matches!(
            e,
            TurnError::TooLarge | TurnError::Storage(StorageError::Busy)
        )));
    assert_eq!(
        db.query_row("SELECT count(*) FROM branches", [], |r| r.get::<_, i64>(0))
            .unwrap(),
        MAX_BRANCHES_PER_STORY as i64
    );
    assert_eq!(
        store.fork_branch(
            &ForkRequest {
                parent: root,
                child_branch: "over-cap".into(),
                expected_parent_revision: 0,
                at_revision: 0
            },
            &|| false
        ),
        Err(TurnError::TooLarge)
    );
}

#[test]
fn parent_drafts_do_not_inherit_and_child_cancel_and_competing_turns_preserve_exact_receipts() {
    let temp = Temp::new();
    let (mut store, root) = setup(&temp);
    wait(&mut store, &root, "before");
    let root_engine = store.resume(&root).unwrap().engine;
    let parent_draft = root_engine.request(
        "parent-draft",
        Intent::Actions(vec![Command::Wait { ticks: 1 }]),
    );
    store.begin_turn(&parent_draft).unwrap();
    let child = fork(&mut store, &root, "child", 1);
    assert!(store.drafts(&child).unwrap().is_empty());
    assert_eq!(store.drafts(&root).unwrap().len(), 1);
    let child_engine = store.resume(&child).unwrap().engine;
    let cancelled =
        child_engine.request("cancel", Intent::Actions(vec![Command::Wait { ticks: 1 }]));
    store.begin_turn(&cancelled).unwrap();
    store.cancel_turn(&cancelled).unwrap();
    let proposal = Engine::proposal(&cancelled).unwrap();
    let narration = child_engine
        .preview(&cancelled, &proposal)
        .unwrap()
        .narration()
        .to_owned();
    assert_eq!(
        store.commit_turn(&cancelled, &proposal, &narration),
        Err(TurnError::Terminal)
    );
    let winner = child_engine.request("winner", Intent::Actions(vec![Command::Wait { ticks: 1 }]));
    let loser = child_engine.request("loser", Intent::Actions(vec![Command::Wait { ticks: 1 }]));
    store.begin_turn(&winner).unwrap();
    let mut other = Store::open(&temp.path(), None).unwrap();
    other.begin_turn(&loser).unwrap();
    let receipt = store
        .commit_turn(&winner, &Engine::proposal(&winner).unwrap(), &narration)
        .unwrap();
    assert_eq!(
        other.commit_turn(&loser, &Engine::proposal(&loser).unwrap(), &narration),
        Err(TurnError::Stale)
    );
    assert_eq!(
        other.turn_status(&loser).unwrap().phase,
        locallore_storage::TurnPhase::Stale
    );
    assert_eq!(other.commit_prepared(&receipt).unwrap(), receipt);
    assert_eq!(store.resume(&root).unwrap().engine.revision(), 1);
    assert_eq!(store.resume(&child).unwrap().engine.revision(), 2);
    let mut changed = winner.clone();
    changed.intent = Intent::Actions(vec![Command::Wait { ticks: 2 }]);
    assert_eq!(
        store.begin_turn(&changed).err(),
        Some(TurnError::RetryMismatch)
    );
}

#[test]
fn inherited_history_budget_prevents_committing_an_unrestorable_child() {
    let temp = Temp::new();
    let (mut store, root) = setup(&temp);
    wait(&mut store, &root, "inherited");
    let child = fork(&mut store, &root, "child", 1);
    let engine = store.resume(&child).unwrap().engine;
    let request = engine.request("new", Intent::Actions(vec![Command::Wait { ticks: 1 }]));
    let input = serde_json::to_string(&request).unwrap();
    let db = Connection::open(temp.path()).unwrap();
    db.execute("WITH RECURSIVE ids(n) AS (SELECT 1 UNION ALL SELECT n+1 FROM ids WHERE n<?1) INSERT INTO turns SELECT ?2,?3,'cancelled-'||n,1,'cancelled',json_set(?4,'$.turn','cancelled-'||n),NULL FROM ids",params![(MAX_HISTORY_RECEIPTS-1) as i64,child.story,child.branch,input]).unwrap();
    assert_eq!(store.begin_turn(&request).err(), Some(TurnError::TooLarge));
    assert_eq!(
        count(&db, "turns", &child),
        (MAX_HISTORY_RECEIPTS - 1) as i64
    );
    assert_eq!(store.resume(&child).unwrap().engine.revision(), 1);
}

#[test]
fn future_parent_sibling_and_unwitnessed_child_text_never_enter_npc_context() {
    let temp = Temp::new();
    let (mut store, root) = setup(&temp);
    wait(&mut store, &root, "before");
    let child = fork(&mut store, &root, "child", 1);
    apply(
        &mut store,
        &root,
        "future-secret",
        vec![Command::Say {
            text: "PARENT_FUTURE_CANARY".into(),
            audience: ["mira".into()].into(),
        }],
    );
    let sibling = fork(&mut store, &root, "sibling", 1);
    apply(
        &mut store,
        &sibling,
        "sibling-secret",
        vec![Command::Say {
            text: "SIBLING_ONLY_CANARY".into(),
            audience: ["mira".into()].into(),
        }],
    );
    apply(
        &mut store,
        &child,
        "child-secret",
        vec![Command::Say {
            text: "CHILD_PRIVATE_CANARY".into(),
            audience: ["player".into()].into(),
        }],
    );
    drop(store);
    let mut store = Store::open(&temp.path(), None).unwrap();
    let engine = store.resume(&child).unwrap().engine;
    let mira =
        serde_json::to_string(&engine.character_context("mira", &child, 2).unwrap()).unwrap();
    for canary in [
        "PARENT_FUTURE_CANARY",
        "SIBLING_ONLY_CANARY",
        "CHILD_PRIVATE_CANARY",
        "SECRET-TIDE-731",
    ] {
        assert!(!mira.contains(canary));
    }
    let player =
        serde_json::to_string(&engine.character_context("player", &child, 2).unwrap()).unwrap();
    assert!(player.contains("CHILD_PRIVATE_CANARY"));
    assert!(!player.contains("PARENT_FUTURE_CANARY"));
    assert!(!player.contains("SIBLING_ONLY_CANARY"));
}

#[test]
fn child_compiler_and_query_work_while_empty_child_cache_returns_not_found() {
    let temp = Temp::new();
    let (mut store, root) = setup(&temp);
    let child = fork(&mut store, &root, "child", 0);
    let engine = store.resume(&child).unwrap().engine;
    use locallore::context_compiler::{self, Budget, CompileRequest, Role};
    assert_eq!(
        context_compiler::compile(
            &engine,
            &CompileRequest {
                version: context_compiler::COMPILER_VERSION,
                scope: child.clone(),
                expected_head: 0,
                at_revision: None,
                observer: "player".into(),
                role: Role::Character,
                query: String::new(),
                referenced_ids: vec![],
                budget: Budget::default()
            }
        )
        .unwrap()
        .scope,
        child
    );
    use locallore::inspection_query::{self, Observer, Query, View};
    assert_eq!(
        inspection_query::query(
            &engine,
            &Query {
                version: inspection_query::QUERY_VERSION,
                scope: child.clone(),
                expected_head: 0,
                at_revision: None,
                observer: Observer::Player,
                view: View::History,
                cursor: None,
                limit: 16,
                search: String::new()
            },
            false
        )
        .unwrap()
        .scope,
        child
    );
    let request = derived_memory::PrepareRequest {
        scope: child,
        expected_revision: 0,
        observer: "player".into(),
        from_exclusive: 0,
        through_revision: 0,
        target: derived_memory::Target::SceneWindow,
    };
    assert!(matches!(
        store.prepare_memory(&request, &|| false),
        Err(derived_memory::MemoryError::NotFound)
    ));
}
