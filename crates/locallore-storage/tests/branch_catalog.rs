// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
use locallore::{contracts::*, engine::Engine};
use locallore_storage::{
    derived_memory::{PrepareRequest, Target},
    BranchCatalog, ForkRequest, StorageError, Store, TurnError,
};
use rusqlite::{types::Value, Connection, OpenFlags};
use std::{
    cell::{Cell, RefCell},
    collections::BTreeMap,
    path::PathBuf,
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT: AtomicU64 = AtomicU64::new(0);
const TABLES: [&str; 9] = [
    "stories",
    "branches",
    "entities",
    "branch_entities",
    "turns",
    "accepted_events",
    "event_witnesses",
    "branch_projections",
    "derived_memory",
];
struct Fixture {
    path: PathBuf,
    store: Store,
    root: Scope,
    child: Scope,
    sibling: Scope,
    nested: Scope,
    other: Scope,
}
impl Fixture {
    fn new() -> Self {
        let directory = std::env::temp_dir().join(format!(
            "locallore-branch-catalog-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&directory).unwrap();
        let path = directory.join("synthetic.sqlite");
        let mut store = Store::open(&path, None).unwrap();
        let mut seed: Seed =
            serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
        seed.scope.story = "timeline-target".into();
        let root = seed.scope.clone();
        store
            .create_story("Synthetic timelines", seed.clone())
            .unwrap();
        apply(&mut store, &root, "prefix", Command::Wait { ticks: 1 });
        let child = fork(&mut store, &root, "z-child", 1);
        apply(
            &mut store,
            &root,
            "shared-key",
            Command::Give {
                item: "potion".into(),
                to: "mira".into(),
                quantity: 1,
            },
        );
        apply(
            &mut store,
            &child,
            "shared-key",
            Command::Consume {
                item: "potion".into(),
            },
        );
        let sibling = fork(&mut store, &root, "a-sibling", 1);
        apply(
            &mut store,
            &sibling,
            "private-claim",
            Command::Say {
                text: "Synthetic sibling-only canary".into(),
                audience: ["mira".into()].into(),
            },
        );
        let nested = fork(&mut store, &child, "m-nested", 0);
        apply(
            &mut store,
            &nested,
            "rewound-wait",
            Command::Wait { ticks: 1 },
        );
        draft(&mut store, &root, "main-draft");
        draft(&mut store, &child, "child-draft-1");
        draft(&mut store, &child, "child-draft-2");
        let e = store.resume(&sibling).unwrap().engine;
        let req = e.request(
            "cancelled",
            Intent::Actions(vec![Command::Wait { ticks: 1 }]),
        );
        store.begin_turn(&req).unwrap();
        store.cancel_turn(&req).unwrap();
        for observer in ["player", "mira"] {
            let prepared = store
                .prepare_memory(
                    &PrepareRequest {
                        scope: root.clone(),
                        expected_revision: 2,
                        observer: observer.into(),
                        from_exclusive: 0,
                        through_revision: 2,
                        target: Target::SceneWindow,
                    },
                    &|| false,
                )
                .unwrap();
            store.publish_memory(prepared, &|| false).unwrap();
        }
        seed.scope.story = "unrelated-story".into();
        let other = seed.scope.clone();
        store.create_story("Unrelated catalog title", seed).unwrap();
        apply(
            &mut store,
            &other,
            "unrelated-private-claim",
            Command::Say {
                text: "Synthetic other-story canary".into(),
                audience: ["mira".into()].into(),
            },
        );
        draft(&mut store, &other, "other-draft");
        Self {
            path,
            store,
            root,
            child,
            sibling,
            nested,
            other,
        }
    }
    fn catalog(&mut self) -> BranchCatalog {
        self.store
            .branch_catalog(&self.root.story, &|| false)
            .unwrap()
    }
    fn rows(&self) -> BTreeMap<String, Vec<Vec<Value>>> {
        let db = Connection::open_with_flags(&self.path, OpenFlags::SQLITE_OPEN_READ_ONLY).unwrap();
        TABLES
            .into_iter()
            .map(|table| {
                let mut q = db
                    .prepare(&format!("SELECT * FROM {table} ORDER BY 1,2,3"))
                    .unwrap();
                let width = q.column_count();
                let rows = q
                    .query_map([], |r| (0..width).map(|n| r.get(n)).collect())
                    .unwrap()
                    .map(Result::unwrap)
                    .collect();
                (table.into(), rows)
            })
            .collect()
    }
    fn canonical(&mut self) -> Vec<Vec<u8>> {
        let mut result = Vec::new();
        for scope in [
            &self.root,
            &self.child,
            &self.sibling,
            &self.nested,
            &self.other,
        ] {
            let engine = self.store.resume(scope).unwrap().engine;
            result.push(engine.canonical_bytes());
            result.push(serde_json::to_vec(engine.receipts()).unwrap());
            for observer in ["player", "mira", "sable"] {
                result.push(
                    serde_json::to_vec(
                        &engine
                            .character_context(observer, scope, engine.revision())
                            .unwrap(),
                    )
                    .unwrap(),
                );
            }
        }
        result
    }
}
// Fresh synthetic roots and native logs stay under the caller's task-owned TEMP;
// retain them for failures. This fixture never recursively deletes directories.
fn apply(store: &mut Store, scope: &Scope, id: &str, command: Command) {
    let engine = store.resume(scope).unwrap().engine;
    let request = engine.request(id, Intent::Actions(vec![command]));
    let receipt = engine
        .preview(&request, &Engine::proposal(&request).unwrap())
        .unwrap();
    store.begin_turn(&request).unwrap();
    store.commit_prepared(&receipt).unwrap();
}
fn draft(store: &mut Store, scope: &Scope, id: &str) {
    let engine = store.resume(scope).unwrap().engine;
    store
        .begin_turn(&engine.request(id, Intent::Actions(vec![Command::Wait { ticks: 1 }])))
        .unwrap();
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
fn same<T: PartialEq>(left: &T, right: &T) {
    assert!(left == right, "synthetic catalog state differed");
}

#[test]
fn sorted_catalog_validates_nested_rewind_and_exact_scoped_drafts_without_mutating_history() {
    let mut f = Fixture::new();
    let before = f.rows();
    let canonical = f.canonical();
    let catalog = f.catalog();
    assert_eq!(catalog.version, 2);
    assert_eq!(catalog.story_id, f.root.story);
    assert_eq!(catalog.title, "Synthetic timelines");
    assert_eq!(catalog.root_branch, f.root.branch);
    let ids: Vec<_> = catalog
        .branches
        .iter()
        .map(|b| b.scope.branch.as_str())
        .collect();
    assert_eq!(ids, ["a-sibling", "m-nested", "main", "z-child"]);
    let get = |id: &str| {
        catalog
            .branches
            .iter()
            .find(|b| b.scope.branch == id)
            .unwrap()
    };
    let root = get("main");
    assert_eq!(
        (
            root.parent_branch.as_deref(),
            root.fork_revision,
            root.revision,
            root.drafts
        ),
        (None, None, 2, 1)
    );
    let child = get("z-child");
    assert_eq!(
        (
            child.parent_branch.as_deref(),
            child.fork_revision,
            child.revision,
            child.drafts
        ),
        (Some("main"), Some(1), 2, 2)
    );
    let nested = get("m-nested");
    assert_eq!(
        (
            nested.parent_branch.as_deref(),
            nested.fork_revision,
            nested.revision,
            nested.drafts
        ),
        (Some("z-child"), Some(0), 1, 0)
    );
    assert_eq!(get("a-sibling").drafts, 0);
    assert!(catalog
        .branches
        .iter()
        .all(|b| b.scope.story == f.root.story));
    let json = serde_json::to_string(&catalog).unwrap();
    assert!(!json.contains("canary"));
    assert!(!json.contains("SECRET-TIDE"));
    assert!(json.len() <= 60 * 1024);
    same(&before, &f.rows());
    same(&canonical, &f.canonical());
    let unrelated = f.store.branch_catalog(&f.other.story, &|| false).unwrap();
    assert_eq!(unrelated.branches.len(), 1);
    assert_eq!(unrelated.branches[0].drafts, 1);
    assert_eq!(unrelated.title, "Unrelated catalog title");
    f.store = Store::open(&f.path, None).unwrap();
    same(&catalog, &f.catalog());
    same(&before, &f.rows());
}

#[test]
fn missing_and_malformed_identifiers_return_fixed_categories_and_no_data() {
    let mut f = Fixture::new();
    let before = f.rows();
    for id in ["", "foreign/story", "private\ncanary", &"x".repeat(65)] {
        assert_eq!(
            f.store.branch_catalog(id, &|| false).err(),
            Some(TurnError::Engine(Error::Scope))
        );
    }
    assert_eq!(
        f.store.branch_catalog("missing", &|| false).err(),
        Some(TurnError::Storage(StorageError::NotFound))
    );
    same(&before, &f.rows());
}

#[test]
fn cycles_and_mismatched_normalized_history_fail_closed_without_repair() {
    for corrupt in [0, 1, 2, 3] {
        let mut f = Fixture::new();
        let db = Connection::open(&f.path).unwrap();
        match corrupt {
            0 => {
                db.execute("UPDATE branches SET parent_branch='m-nested',fork_revision=0 WHERE story_id=?1 AND branch_id='z-child'",[&f.root.story]).unwrap();
            }
            1 => {
                db.execute("UPDATE accepted_events SET envelope_json='{}' WHERE story_id=?1 AND branch_id='a-sibling'",[&f.root.story]).unwrap();
            }
            2 => {
                db.execute("DELETE FROM event_witnesses WHERE story_id=?1 AND branch_id='a-sibling' AND observer_id='mira'",[&f.root.story]).unwrap();
            }
            _ => {
                db.execute("UPDATE turns SET response_json='{}' WHERE story_id=?1 AND branch_id='a-sibling' AND status='committed'",[&f.root.story]).unwrap();
            }
        }
        drop(db);
        let tampered = f.rows();
        assert_eq!(
            f.store.branch_catalog(&f.root.story, &|| false).err(),
            Some(TurnError::Integrity)
        );
        same(&tampered, &f.rows());
        let other = f.store.branch_catalog(&f.other.story, &|| false).unwrap();
        assert_eq!(other.branches.len(), 1);
    }
}

#[test]
fn every_catalog_cancel_checkpoint_and_panicking_callback_is_nonmutating() {
    let mut f = Fixture::new();
    let baseline = f.rows();
    let polls = Cell::new(0usize);
    f.store
        .branch_catalog(&f.root.story, &|| {
            polls.set(polls.get() + 1);
            false
        })
        .unwrap();
    let total = polls.get();
    assert!((12..=32).contains(&total));
    for stop in 1..=total {
        let current = Cell::new(0);
        assert_eq!(
            f.store
                .branch_catalog(&f.root.story, &|| {
                    current.set(current.get() + 1);
                    current.get() == stop
                })
                .err(),
            Some(TurnError::Engine(Error::Cancelled))
        );
        same(&baseline, &f.rows());
        same(&f.catalog().branches.len(), &4);
    }
    assert_eq!(
        f.store
            .branch_catalog(&f.root.story, &|| panic!("synthetic catalog cancellation"))
            .err(),
        Some(TurnError::Engine(Error::Cancelled))
    );
    same(&baseline, &f.rows());
}

#[test]
fn committed_writer_during_read_returns_one_coherent_catalog_then_new_state() {
    let mut f = Fixture::new();
    // WAL on this fresh synthetic DB permits a real writer to commit after the
    // reader's first SELECT. The catalog must not mix those later rows/heads.
    let db = Connection::open(&f.path).unwrap();
    let mode: String = db
        .query_row("PRAGMA journal_mode=WAL", [], |r| r.get(0))
        .unwrap();
    assert_eq!(mode, "wal");
    drop(db);
    let expected = f.catalog();
    let writer = RefCell::new(Store::open(&f.path, None).unwrap());
    let polled = Cell::new(0);
    let observed = f
        .store
        .branch_catalog(&f.root.story, &|| {
            polled.set(polled.get() + 1);
            if polled.get() == 2 {
                let mut w = writer.borrow_mut();
                let child = fork(&mut w, &f.root, "late-visible", 2);
                apply(
                    &mut w,
                    &f.root,
                    "later-root-wait",
                    Command::Wait { ticks: 1 },
                );
                draft(&mut w, &child, "later-child-draft");
            }
            false
        })
        .unwrap();
    same(&expected, &observed);
    let later = f.catalog();
    assert_eq!(later.branches.len(), 5);
    assert_eq!(
        later
            .branches
            .iter()
            .find(|b| b.scope == f.root)
            .unwrap()
            .revision,
        3
    );
    assert_eq!(
        later
            .branches
            .iter()
            .find(|b| b.scope.branch == "late-visible")
            .unwrap()
            .drafts,
        1
    );
}

#[test]
fn stale_projection_is_ignored_but_never_rebuilt_by_metadata_read() {
    let mut f = Fixture::new();
    let expected = f.catalog();
    Connection::open(&f.path).unwrap().execute("UPDATE branch_projections SET projection_json='{}' WHERE story_id=?1 AND branch_id='z-child'",[&f.root.story]).unwrap();
    let stale = f.rows();
    same(&expected, &f.catalog());
    same(&stale, &f.rows());
    assert!(f.store.resume(&f.child).unwrap().projection_needs_rebuild);
}

#[test]
fn actual_branch_and_serialized_reply_budgets_are_enforced() {
    let mut f = Fixture::new();
    for index in 4..256 {
        fork(&mut f.store, &f.root, &format!("budget-{index:03}"), 0);
    }
    let catalog = f.catalog();
    assert_eq!(catalog.branches.len(), 256);
    assert!(serde_json::to_vec(&catalog).unwrap().len() < 60 * 1024);
    let before = f.rows();
    // An externally inserted257th metadata row exceeds the catalog's own bound,
    // even though public fork admission already refuses this construction.
    let db = Connection::open(&f.path).unwrap();
    db.execute("INSERT INTO branches(story_id,branch_id,parent_branch,fork_revision,head_revision) VALUES(?1,'overflow',?2,0,0)",(&f.root.story,&f.root.branch)).unwrap();
    drop(db);
    let oversized = f.rows();
    assert_eq!(
        f.store.branch_catalog(&f.root.story, &|| false).err(),
        Some(TurnError::TooLarge)
    );
    same(&oversized, &f.rows());
    assert_ne!(before["branches"].len(), oversized["branches"].len());

    let path = f.path.with_file_name("large-catalog.sqlite");
    let mut store = Store::open(&path, None).unwrap();
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    seed.scope.story = "s".repeat(64);
    seed.scope.branch = "r".repeat(64);
    let root = seed.scope.clone();
    store
        .create_story("Bounded large identifiers", seed)
        .unwrap();
    for index in 1..256 {
        fork(
            &mut store,
            &root,
            &format!("{index:04}{}", "b".repeat(60)),
            0,
        );
    }
    // Each identifier is valid and the graph fits256, but its complete repeated
    // scoped metadata exceeds the response byte budget. Never truncate the list.
    assert_eq!(
        store.branch_catalog(&root.story, &|| false).err(),
        Some(TurnError::TooLarge)
    );
    assert_eq!(store.resume(&root).unwrap().engine.revision(), 0);
}
