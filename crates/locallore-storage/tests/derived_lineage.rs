// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Actual sole-Store authority tests, distinct from the included prototype module.
use locallore::{contracts::*, engine::Engine};
use locallore_storage::{derived_memory::*, ForkRequest, Store};
use rusqlite::{params, Connection};
use serde_json::json;
use std::{
    cell::Cell,
    path::PathBuf,
    sync::{
        atomic::{AtomicUsize, Ordering},
        mpsc, Arc, Barrier,
    },
};
static NEXT: AtomicUsize = AtomicUsize::new(0);
struct Temp(PathBuf);
impl Temp {
    fn new() -> Self {
        let dir = std::env::temp_dir().join(format!(
            "derived-lineage-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&dir).unwrap();
        Self(dir)
    }
    fn path(&self) -> PathBuf {
        self.0.join("synthetic.sqlite")
    }
    fn open(&self) -> Store {
        Store::open(&self.path(), None).unwrap()
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
fn create(store: &mut Store) -> Scope {
    let seed = seed();
    let scope = seed.scope.clone();
    store
        .create_story("Synthetic derived lineage", seed)
        .unwrap();
    scope
}
fn apply(store: &mut Store, scope: &Scope, key: &str, commands: Vec<Command>) -> Receipt {
    let e = store.resume(scope).unwrap().engine;
    let r = e.request(key, Intent::Actions(commands));
    let p = Engine::proposal(&r).unwrap();
    let n = e.preview(&r, &p).unwrap().narration().to_owned();
    store.begin_turn(&r).unwrap();
    store.commit_turn(&r, &p, &n).unwrap()
}
fn say(store: &mut Store, scope: &Scope, key: &str, text: &str) {
    apply(
        store,
        scope,
        key,
        vec![Command::Say {
            text: text.into(),
            audience: ["mira".into()].into(),
        }],
    );
}
fn fork(store: &mut Store, parent: &Scope, name: &str, at: u64) -> Scope {
    let head = store.resume(parent).unwrap().engine.revision();
    store
        .fork_branch(
            &ForkRequest {
                parent: parent.clone(),
                child_branch: name.into(),
                expected_parent_revision: head,
                at_revision: at,
            },
            &|| false,
        )
        .unwrap()
        .scope
}
fn request(scope: &Scope, observer: &str, head: u64) -> PrepareRequest {
    PrepareRequest {
        scope: scope.clone(),
        expected_revision: head,
        observer: observer.into(),
        from_exclusive: 0,
        through_revision: head,
        target: Target::SceneWindow,
    }
}
fn search(scope: &Scope, observer: &str, head: u64, text: &str) -> SearchRequest {
    SearchRequest {
        scope: scope.clone(),
        expected_revision: head,
        observer: observer.into(),
        text: text.into(),
        limit: MAX_HITS,
    }
}
fn family(store: &mut Store) -> (Scope, Scope, Scope) {
    let root = create(store);
    say(store, &root, "inherited", "INHERITED-VISIBLE");
    let child = fork(store, &root, "child", 1);
    let sibling = fork(store, &root, "sibling", 1);
    say(store, &root, "parent-future", "PARENT-FUTURE-PRIVATE");
    say(store, &sibling, "sibling-private", "SIBLING-PRIVATE");
    say(store, &child, "child-local", "CHILD-VISIBLE");
    (root, child, sibling)
}
fn publish(store: &mut Store, r: &PrepareRequest) -> PublishOutcome {
    let p = store.prepare_memory(r, &|| false).unwrap();
    store.publish_memory(p, &|| false).unwrap()
}
fn cache_rows(path: &std::path::Path) -> Vec<(String, i64, String)> {
    let db = Connection::open(path).unwrap();
    let rows = db.prepare("SELECT branch_id,source_revision,packet_json FROM derived_memory ORDER BY story_id,branch_id,observer_id,cache_key").unwrap().query_map([], |r| Ok((r.get(0)?,r.get(1)?,r.get(2)?))).unwrap().collect::<Result<_,_>>().unwrap();
    rows
}

#[test]
fn root_packet_v1_bytes_and_original_child_sources_survive_reopen_without_projection_repair() {
    let dir = Temp::new();
    let mut store = dir.open();
    let root = create(&mut store);
    apply(&mut store, &root, "wait", vec![Command::Wait { ticks: 1 }]);
    let r = request(&root, "player", 1);
    publish(&mut store, &r);
    let expected = json!({"version":1,"scope":{"story":"quay","branch":"main"},"observer":"player","source_revision":1,"from_exclusive":0,"through_revision":1,"target":{"kind":"scene_window"},"visibility":"actor_observations","provenance":{"method":"deterministic-event-extractive-v1","model":null,"prompt":null},"source_events":[1],"entries":[{"class":"observed_time_span","from":100,"to":101,"source_events":[1]}]});
    assert_eq!(
        store.read_memory(&r, &|| false).unwrap().json().to_string(),
        expected.to_string()
    );
    let child = fork(&mut store, &root, "child", 1);
    say(&mut store, &child, "local", "CHILD-VISIBLE");
    let r = request(&child, "player", 2);
    publish(&mut store, &r);
    drop(store);
    let db = Connection::open(dir.path()).unwrap();
    db.execute(
        "UPDATE branch_projections SET projection_json='{}' WHERE branch_id='child'",
        [],
    )
    .unwrap();
    drop(db);
    let mut store = dir.open();
    let before = store.resume(&child).unwrap();
    assert!(before.projection_needs_rebuild);
    assert_eq!(before.engine.receipts()[0].request().scope, root);
    assert_eq!(before.engine.receipts()[1].request().scope, child);
    let packet = store.read_memory(&r, &|| false).unwrap();
    assert_eq!(packet.json()["source_events"], json!([1, 2]));
    assert!(store.resume(&child).unwrap().projection_needs_rebuild);
    assert_eq!(
        store.resume(&child).unwrap().engine.canonical_bytes(),
        before.engine.canonical_bytes()
    );
    let mut readonly = Store::open_read_only(&dir.path()).unwrap();
    assert_eq!(
        readonly
            .search_memory(&search(&child, "player", 2, "CHILD"), &|| false)
            .unwrap()
            .len(),
        1
    );
}

#[test]
fn nested_prebirth_packets_exclude_parent_future_sibling_and_unknown_or_hidden_targets() {
    let dir = Temp::new();
    let mut store = dir.open();
    let root = create(&mut store);
    say(&mut store, &root, "first", "INHERITED-VISIBLE");
    for n in 0..4 {
        say(
            &mut store,
            &root,
            &format!("future-{n}"),
            "PARENT-FUTURE-PRIVATE",
        );
    }
    let a = fork(&mut store, &root, "a", 5);
    say(&mut store, &a, "a-local", "A-LATER-PRIVATE");
    let b = fork(&mut store, &a, "b", 1);
    say(&mut store, &b, "b-local", "B-LOCAL-VISIBLE");
    let sibling = fork(&mut store, &a, "sibling", 5);
    say(&mut store, &sibling, "sib", "SIBLING-PRIVATE");
    let r = request(&b, "mira", 2);
    publish(&mut store, &r);
    let packet = store.read_memory(&r, &|| false).unwrap();
    let text = packet.json().to_string();
    for s in ["INHERITED-VISIBLE", "B-LOCAL-VISIBLE"] {
        assert!(text.contains(s));
    }
    for s in [
        "PARENT-FUTURE-PRIVATE",
        "A-LATER-PRIVATE",
        "SIBLING-PRIVATE",
        "SECRET-TIDE-731",
    ] {
        assert!(!text.contains(s));
        assert!(store
            .search_memory(&search(&b, "mira", 2, s), &|| false)
            .unwrap()
            .is_empty());
    }
    assert_eq!(
        store
            .prepare_memory(&request(&b, "sable", 2), &|| false)
            .err(),
        Some(MemoryError::NotFound)
    );
    for id in ["relic-location", "no-such-fact"] {
        let mut q = r.clone();
        q.target = Target::Entity {
            kind: EntityKind::Fact,
            id: id.into(),
        };
        assert_eq!(
            store.prepare_memory(&q, &|| false).err(),
            Some(MemoryError::NotFound)
        );
    }
    let mut q = request(&b, "sable", 2);
    q.from_exclusive = 1;
    assert_eq!(
        store.prepare_memory(&q, &|| false).err(),
        Some(MemoryError::InvalidInput)
    );
    q.from_exclusive = 99;
    assert_eq!(
        store.prepare_memory(&q, &|| false).err(),
        Some(MemoryError::InvalidInput)
    );
}

#[test]
fn parent_future_advance_does_not_stale_child_but_child_advance_does() {
    let dir = Temp::new();
    let mut store = dir.open();
    let (root, child, _) = family(&mut store);
    let r = request(&child, "mira", 2);
    let prepared = store.prepare_memory(&r, &|| false).unwrap();
    let mut other = dir.open();
    say(&mut other, &root, "later-parent", "FUTURE-AGAIN");
    assert_eq!(
        store.publish_memory(prepared, &|| false).unwrap(),
        PublishOutcome::Published
    );
    let old = store.read_memory(&r, &|| false).unwrap();
    assert!(!old.json().to_string().contains("FUTURE-AGAIN"));
    let prepared = store.prepare_memory(&r, &|| false).unwrap();
    say(&mut other, &child, "later-child", "LATER-CHILD");
    let rows = cache_rows(&dir.path());
    assert_eq!(
        store.publish_memory(prepared, &|| false),
        Err(MemoryError::Stale)
    );
    assert_eq!(
        store.read_memory(&r, &|| false).err(),
        Some(MemoryError::Stale)
    );
    assert_eq!(
        store.search_memory(&search(&child, "mira", 2, "INHERITED"), &|| false),
        Err(MemoryError::Stale)
    );
    assert_eq!(cache_rows(&dir.path()), rows);
}

#[test]
fn inherited_source_and_witness_tampering_fail_before_cache_or_search_publication() {
    for witness in [false, true] {
        let dir = Temp::new();
        let mut store = dir.open();
        let (root, child, _) = family(&mut store);
        let r = request(&child, "mira", 2);
        publish(&mut store, &r);
        let prepared = store.prepare_memory(&r, &|| false).unwrap();
        let rows = cache_rows(&dir.path());
        let db = Connection::open(dir.path()).unwrap();
        if witness {
            db.execute("DELETE FROM event_witnesses WHERE story_id=?1 AND branch_id=?2 AND sequence=1 AND observer_id='mira'",params![root.story,root.branch]).unwrap();
        } else {
            db.execute("UPDATE accepted_events SET envelope_json=json_set(envelope_json,'$.sequence',99) WHERE story_id=?1 AND branch_id=?2 AND sequence=1",params![root.story,root.branch]).unwrap();
        }
        assert_eq!(
            store.publish_memory(prepared, &|| false),
            Err(MemoryError::Integrity)
        );
        assert_eq!(
            store.read_memory(&r, &|| false).err(),
            Some(MemoryError::Integrity)
        );
        assert_eq!(
            store.search_memory(&search(&child, "mira", 2, "INHERITED"), &|| false),
            Err(MemoryError::Integrity)
        );
        assert_eq!(
            store.invalidate_memory(&child, "mira", 2, &|| false),
            Err(MemoryError::Integrity)
        );
        assert_eq!(cache_rows(&dir.path()), rows);
    }
}

#[test]
fn excluded_parent_future_tamper_does_not_enter_child_source_validation() {
    let dir = Temp::new();
    let mut store = dir.open();
    let (root, child, _) = family(&mut store);
    let r = request(&child, "mira", 2);
    let prepared = store.prepare_memory(&r, &|| false).unwrap();
    let db = Connection::open(dir.path()).unwrap();
    db.execute("UPDATE accepted_events SET envelope_json=json_set(envelope_json,'$.sequence',99) WHERE story_id=?1 AND branch_id=?2 AND sequence=2",params![root.story,root.branch]).unwrap();
    assert_eq!(
        store.publish_memory(prepared, &|| false).unwrap(),
        PublishOutcome::Published
    );
    assert_eq!(
        store
            .search_memory(&search(&child, "mira", 2, "INHERITED"), &|| false)
            .unwrap()
            .len(),
        1
    );
}

#[test]
fn foreign_partition_poison_does_not_materialize_and_local_packet_forgery_fails_closed() {
    let dir = Temp::new();
    let mut store = dir.open();
    let (_, child, sibling) = family(&mut store);
    let r = request(&child, "mira", 2);
    publish(&mut store, &r);
    let db = Connection::open(dir.path()).unwrap();
    for branch in [&child, &sibling] {
        for n in 0..40 {
            db.execute("INSERT INTO derived_memory(story_id,branch_id,observer_id,cache_key,source_revision,summary_version,method,visibility,packet_json) VALUES(?1,?2,'sable',?3,2,1,'deterministic-event-extractive-v1','actor_observations',?4)",params![branch.story,branch.branch,format!("poison-{n}"),r#"{"secret":"FOREIGN-PRIVATE-CANARY"}"#]).unwrap();
        }
    }
    assert_eq!(
        store
            .search_memory(&search(&child, "mira", 2, "INHERITED"), &|| false)
            .unwrap()
            .len(),
        1
    );
    assert!(store
        .search_memory(&search(&child, "mira", 2, "FOREIGN"), &|| false)
        .unwrap()
        .is_empty());
    db.execute("UPDATE derived_memory SET packet_json=json_set(packet_json,'$.entries[0].outcome','FORGED-PRIVATE') WHERE branch_id='child' AND observer_id='mira'",[]).unwrap();
    assert_eq!(
        store.read_memory(&r, &|| false).err(),
        Some(MemoryError::Integrity)
    );
    assert_eq!(
        store.search_memory(&search(&child, "mira", 2, "absent"), &|| false),
        Err(MemoryError::Integrity)
    );
}

#[test]
fn every_publication_cancel_checkpoint_and_sql_abort_restore_previous_partition() {
    let dir = Temp::new();
    let mut store = dir.open();
    let (_, child, _) = family(&mut store);
    publish(&mut store, &request(&child, "mira", 2));
    let old = cache_rows(&dir.path());
    say(&mut store, &child, "next", "NEXT-VISIBLE");
    let r = request(&child, "mira", 3);
    let count = Cell::new(0);
    let p = store.prepare_memory(&r, &|| false).unwrap();
    store
        .publish_memory(p, &|| {
            count.set(count.get() + 1);
            false
        })
        .unwrap();
    let total = count.get();
    assert!(total > 5 && total < 128);
    let db = Connection::open(dir.path()).unwrap();
    db.execute("UPDATE derived_memory SET source_revision=?1,packet_json=?2 WHERE branch_id='child' AND observer_id='mira'",params![old[0].1,old[0].2]).unwrap();
    for stop in 1..=total {
        let p = store.prepare_memory(&r, &|| false).unwrap();
        let n = Cell::new(0);
        assert_eq!(
            store.publish_memory(p, &|| {
                n.set(n.get() + 1);
                n.get() >= stop
            }),
            Err(MemoryError::Cancelled),
            "checkpoint {stop}"
        );
        assert_eq!(cache_rows(&dir.path()), old, "checkpoint {stop}");
    }
    db.execute_batch("CREATE TRIGGER abort_memory BEFORE INSERT ON derived_memory BEGIN SELECT RAISE(ABORT,'synthetic'); END;").unwrap();
    let p = store.prepare_memory(&r, &|| false).unwrap();
    assert_eq!(
        store.publish_memory(p, &|| false),
        Err(MemoryError::Database)
    );
    assert_eq!(cache_rows(&dir.path()), old);
    db.execute_batch("DROP TRIGGER abort_memory").unwrap();
    assert_eq!(publish(&mut store, &r), PublishOutcome::Published);
    assert_eq!(store.resume(&child).unwrap().engine.revision(), 3);
}

#[test]
fn search_uses_one_snapshot_when_another_owner_commits_after_replay() {
    let dir = Temp::new();
    let mut store = dir.open();
    let (_, child, _) = family(&mut store);
    let r = request(&child, "mira", 2);
    publish(&mut store, &r);
    // Explicit synthetic WAL fixture permits a writer to finish while this read
    // snapshot is held. The default rollback journal legitimately returns Busy.
    Connection::open(dir.path())
        .unwrap()
        .pragma_update(None, "journal_mode", "WAL")
        .unwrap();
    let mut other = dir.open();
    let engine = other.resume(&child).unwrap().engine;
    let req = engine.request(
        "concurrent",
        Intent::Actions(vec![Command::Wait { ticks: 1 }]),
    );
    let proposal = Engine::proposal(&req).unwrap();
    let narration = engine
        .preview(&req, &proposal)
        .unwrap()
        .narration()
        .to_owned();
    other.begin_turn(&req).unwrap();
    let (go_tx, go_rx) = mpsc::channel();
    let (done_tx, done_rx) = mpsc::channel();
    let worker = std::thread::spawn(move || {
        go_rx.recv().unwrap();
        let result = other.commit_turn(&req, &proposal, &narration);
        done_tx.send(result).unwrap();
    });
    let count = Cell::new(0);
    let hits = store
        .search_memory(&search(&child, "mira", 2, "INHERITED"), &|| {
            count.set(count.get() + 1);
            // memory_engine's second checkpoint follows strict replay under the read transaction.
            if count.get() == 2 {
                go_tx.send(()).unwrap();
                let committed = done_rx.recv().unwrap();
                assert!(committed.is_ok(), "{committed:?}");
            }
            false
        })
        .unwrap();
    worker.join().unwrap();
    assert_eq!(hits.len(), 1);
    assert_eq!(store.resume(&child).unwrap().engine.revision(), 3);
    assert_eq!(
        store.search_memory(&search(&child, "mira", 2, "INHERITED"), &|| false),
        Err(MemoryError::Stale)
    );
}

#[test]
fn competing_owners_publish_once_and_cancelled_search_recovers_on_same_owner() {
    let dir = Temp::new();
    let mut store = dir.open();
    let (_, child, _) = family(&mut store);
    let r = request(&child, "mira", 2);
    let mut other = dir.open();
    let a = store.prepare_memory(&r, &|| false).unwrap();
    let b = other.prepare_memory(&r, &|| false).unwrap();
    let barrier = Arc::new(Barrier::new(2));
    let gate = barrier.clone();
    let thread = std::thread::spawn(move || {
        gate.wait();
        other.publish_memory(b, &|| false)
    });
    barrier.wait();
    let first = store.publish_memory(a, &|| false);
    let second = thread.join().unwrap();
    assert!([first, second]
        .iter()
        .any(|r| *r == Ok(PublishOutcome::Published)));
    for result in [first, second] {
        assert!(matches!(
            result,
            Ok(PublishOutcome::Published | PublishOutcome::Unchanged) | Err(MemoryError::Busy)
        ));
    }
    assert_eq!(publish(&mut store, &r), PublishOutcome::Unchanged);
    assert_eq!(cache_rows(&dir.path()).len(), 1);
    let calls = Cell::new(0);
    store
        .search_memory(&search(&child, "mira", 2, "INHERITED"), &|| {
            calls.set(calls.get() + 1);
            false
        })
        .unwrap();
    let total = calls.get();
    for stop in [1, total / 2, total - 1, total] {
        let n = Cell::new(0);
        assert_eq!(
            store.search_memory(&search(&child, "mira", 2, "INHERITED"), &|| {
                n.set(n.get() + 1);
                n.get() >= stop
            }),
            Err(MemoryError::Cancelled)
        );
    }
    assert_eq!(
        store
            .search_memory(&search(&child, "mira", 2, "INHERITED"), &|| false)
            .unwrap()
            .len(),
        1
    );
    store
        .invalidate_memory(&child, "mira", 2, &|| false)
        .unwrap();
    assert_eq!(
        store.read_memory(&r, &|| false).err(),
        Some(MemoryError::NotFound)
    );
}
