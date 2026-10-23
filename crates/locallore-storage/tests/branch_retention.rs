// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
use locallore::{contracts::*, engine::Engine};
use locallore_storage::{
    derived_memory::{PrepareRequest, Target},
    BranchDeletionPreview, DeletionError, ForkRequest, StorageError, Store, TurnError,
};
use rusqlite::{types::Value, Connection, OpenFlags};
use std::{
    cell::Cell,
    collections::BTreeMap,
    path::PathBuf,
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT: AtomicU64 = AtomicU64::new(0);
const TABLES: [&str; 10] = [
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
];
struct Fixture {
    path: PathBuf,
    store: Store,
    root: Scope,
    parent: Scope,
    early: Scope,
    late: Scope,
    nested: Scope,
    sibling: Scope,
    other: Scope,
    ready: Receipt,
}
impl Fixture {
    fn new() -> Self {
        let dir = std::env::temp_dir().join(format!(
            "locallore-parent-retention-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&dir).unwrap();
        std::fs::write(
            dir.join("owner-v1"),
            b"locallore-synthetic-parent-retention-v1",
        )
        .unwrap();
        let path = dir.join("synthetic.sqlite");
        let mut store = Store::open(&path, None).unwrap();
        let mut seed: Seed =
            serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
        seed.scope.story = "retention-target".into();
        let root = seed.scope.clone();
        store
            .create_story("Synthetic retained timelines", seed.clone())
            .unwrap();
        for n in 0..8 {
            apply(
                &mut store,
                &root,
                &format!("root-{n}"),
                vec![if n == 7 {
                    Command::Say {
                        text: "Synthetic shared root scene evidence".into(),
                        audience: ["mira".into()].into(),
                    }
                } else {
                    Command::Wait { ticks: 1 }
                }],
            );
        }
        let parent = fork(&mut store, &root, "retired-parent", 8);
        apply(
            &mut store,
            &parent,
            "inherited-claim",
            vec![Command::Say {
                text: "Synthetic inherited parent evidence".into(),
                audience: ["mira".into()].into(),
            }],
        );
        apply(
            &mut store,
            &parent,
            "multi-event-tail",
            vec![
                Command::Give {
                    item: "potion".into(),
                    to: "mira".into(),
                    quantity: 1,
                },
                Command::Wait { ticks: 1 },
            ],
        );
        apply(
            &mut store,
            &parent,
            "unreachable-tail",
            vec![Command::Say {
                text: "Synthetic unreachable parent tail canary".into(),
                audience: ["mira".into()].into(),
            }],
        );
        let early = fork(&mut store, &parent, "early-child", 3);
        apply(
            &mut store,
            &early,
            "early-wait",
            vec![Command::Wait { ticks: 1 }],
        );
        let late = fork(&mut store, &parent, "late-child", 9);
        apply(
            &mut store,
            &late,
            "independent-consume",
            vec![Command::Consume {
                item: "potion".into(),
            }],
        );
        let nested = fork(&mut store, &early, "nested-child", 0);
        apply(
            &mut store,
            &nested,
            "nested-wait",
            vec![Command::Wait { ticks: 1 }],
        );
        let sibling = fork(&mut store, &root, "unaffected-sibling", 1);
        apply(
            &mut store,
            &sibling,
            "sibling-claim",
            vec![Command::Say {
                text: "Synthetic sibling knowledge canary".into(),
                audience: ["mira".into()].into(),
            }],
        );
        let ready = workflow(&mut store, &parent);
        caches(&mut store, &root, 8);
        seed.scope.story = "retained-other-story".into();
        let other = seed.scope.clone();
        store.create_story("Other retained story", seed).unwrap();
        apply(
            &mut store,
            &other,
            "other-gift",
            vec![Command::Give {
                item: "potion".into(),
                to: "mira".into(),
                quantity: 1,
            }],
        );
        caches(&mut store, &other, 1);
        Self {
            path,
            store,
            root,
            parent,
            early,
            late,
            nested,
            sibling,
            other,
            ready,
        }
    }
    fn prepare(&mut self, scope: &Scope) -> locallore_storage::PreparedBranchDeletion {
        let head = self.store.resume(scope).unwrap().engine.revision();
        self.store
            .prepare_branch_deletion(scope, head, &|| false)
            .unwrap()
    }
    fn rows(&self, story: &str) -> BTreeMap<String, Vec<Vec<Value>>> {
        let db = Connection::open_with_flags(&self.path, OpenFlags::SQLITE_OPEN_READ_ONLY).unwrap();
        TABLES
            .into_iter()
            .map(|table| {
                let mut q = db
                    .prepare(&format!("SELECT * FROM {table} WHERE story_id=?1"))
                    .unwrap();
                let width = q.column_count();
                let order = (1..=width)
                    .map(|n| n.to_string())
                    .collect::<Vec<_>>()
                    .join(",");
                q = db
                    .prepare(&format!(
                        "SELECT * FROM {table} WHERE story_id=?1 ORDER BY {order}"
                    ))
                    .unwrap();
                let rows = q
                    .query_map([story], |r| (0..width).map(|i| r.get(i)).collect())
                    .unwrap()
                    .map(Result::unwrap)
                    .collect();
                (table.into(), rows)
            })
            .collect()
    }
    fn branch_rows(&self, scope: &Scope) -> BTreeMap<String, Vec<Vec<Value>>> {
        let db = Connection::open_with_flags(&self.path, OpenFlags::SQLITE_OPEN_READ_ONLY).unwrap();
        [
            "branches",
            "branch_entities",
            "turns",
            "accepted_events",
            "event_witnesses",
            "branch_projections",
            "derived_memory",
        ]
        .into_iter()
        .map(|table| {
            let mut q = db
                .prepare(&format!(
                    "SELECT * FROM {table} WHERE story_id=?1 AND branch_id=?2"
                ))
                .unwrap();
            let width = q.column_count();
            let order = (1..=width)
                .map(|n| n.to_string())
                .collect::<Vec<_>>()
                .join(",");
            q = db
                .prepare(&format!(
                    "SELECT * FROM {table} WHERE story_id=?1 AND branch_id=?2 ORDER BY {order}"
                ))
                .unwrap();
            let rows = q
                .query_map((&scope.story, &scope.branch), |r| {
                    (0..width).map(|i| r.get(i)).collect()
                })
                .unwrap()
                .map(Result::unwrap)
                .collect();
            (table.into(), rows)
        })
        .collect()
    }
    fn state(&mut self, scope: &Scope) -> Vec<Vec<u8>> {
        let e = self.store.resume(scope).unwrap().engine;
        let mut result = vec![
            e.canonical_bytes(),
            serde_json::to_vec(e.receipts()).unwrap(),
        ];
        for observer in ["player", "mira", "sable"] {
            result.push(
                serde_json::to_vec(&e.character_context(observer, scope, e.revision()).unwrap())
                    .unwrap(),
            );
        }
        result
    }
}
// Exclusive synthetic roots are retained under caller-owned TEMP; no recursive
// deletion or caller-supplied path is accepted by this fixture.
fn apply(store: &mut Store, scope: &Scope, id: &str, commands: Vec<Command>) -> Receipt {
    let e = store.resume(scope).unwrap().engine;
    let req = e.request(id, Intent::Actions(commands));
    let receipt = e.preview(&req, &Engine::proposal(&req).unwrap()).unwrap();
    store.begin_turn(&req).unwrap();
    store.commit_prepared(&receipt).unwrap()
}
fn fork(store: &mut Store, parent: &Scope, id: &str, at: u64) -> Scope {
    let revision = store.resume(parent).unwrap().engine.revision();
    store
        .fork_branch(
            &ForkRequest {
                parent: parent.clone(),
                child_branch: id.into(),
                expected_parent_revision: revision,
                at_revision: at,
            },
            &|| false,
        )
        .unwrap()
        .scope
}
fn caches(store: &mut Store, scope: &Scope, head: u64) {
    for observer in ["player", "mira"] {
        let p = store
            .prepare_memory(
                &PrepareRequest {
                    scope: scope.clone(),
                    expected_revision: head,
                    observer: observer.into(),
                    from_exclusive: 0,
                    through_revision: head,
                    target: Target::SceneWindow,
                },
                &|| false,
            )
            .unwrap();
        store.publish_memory(p, &|| false).unwrap();
    }
}
fn workflow(store: &mut Store, scope: &Scope) -> Receipt {
    let e = store.resume(scope).unwrap().engine;
    let req = e.request(
        "old-ready",
        Intent::Actions(vec![Command::Wait { ticks: 1 }]),
    );
    let ready = e.preview(&req, &Engine::proposal(&req).unwrap()).unwrap();
    store.begin_turn(&req).unwrap();
    for (id, phase) in [("cancelled", 0), ("failed", 1), ("stale", 2)] {
        let req = e.request(id, Intent::Actions(vec![Command::Wait { ticks: 1 }]));
        store.begin_turn(&req).unwrap();
        match phase {
            0 => store.cancel_turn(&req),
            1 => store.fail_turn(&req),
            _ => store.stale_turn(&req),
        }
        .unwrap();
    }
    ready
}
fn same<T: PartialEq>(a: &T, b: &T) {
    assert!(a == b, "synthetic retained state differed");
}
fn head(path: &std::path::Path, scope: &Scope) -> Option<i64> {
    use rusqlite::OptionalExtension;
    Connection::open_with_flags(path, OpenFlags::SQLITE_OPEN_READ_ONLY)
        .unwrap()
        .query_row(
            "SELECT head_revision FROM branches WHERE story_id=?1 AND branch_id=?2",
            (&scope.story, &scope.branch),
            |r| r.get(0),
        )
        .optional()
        .unwrap()
}
fn retire(f: &mut Fixture, scope: &Scope) -> locallore_storage::BranchDeletionOutcome {
    let p = f.prepare(scope);
    f.store.delete_branch(p, &|| false).unwrap()
}
fn preview(f: &mut Fixture) -> BranchDeletionPreview {
    let s = f.parent.clone();
    f.prepare(&s).preview().clone()
}

#[test]
fn parent_retirement_preserves_all_children_original_history_context_and_unrelated_rows() {
    let mut f = Fixture::new();
    let parent = f.parent.clone();
    let other = f.rows(&f.other.story);
    let root = f.branch_rows(&f.root);
    let scopes = [
        f.early.clone(),
        f.late.clone(),
        f.nested.clone(),
        f.sibling.clone(),
    ];
    let states: Vec<_> = scopes.iter().map(|s| f.state(s)).collect();
    let branch_rows: Vec<_> = scopes.iter().map(|s| f.branch_rows(s)).collect();
    let all = f.rows(&parent.story);
    let plan = f.prepare(&parent);
    let p = plan.preview();
    assert_eq!(p.version, 2);
    assert_eq!(p.retained_heads[&parent.branch], 9);
    assert_eq!(p.retained_descendants.len(), 3);
    assert_eq!(p.removed_committed_turns, 2);
    assert_eq!(p.removed_noncommitted_turns, 4);
    assert_eq!(p.removed_rows["accepted_events"], 3);
    assert_eq!(p.removed_rows["turns"], 6);
    assert_eq!(p.removed_rows["branch_entities"], 0);
    assert_eq!(p.removed_rows.len(), 9);
    assert_eq!(p.removed_rows["memory_jobs"], 0);
    assert_eq!(p.removed_rows["memory_job_packets"], 0);
    assert!(serde_json::to_vec(p).unwrap().len() <= 60 * 1024);
    same(&all, &f.rows(&parent.story));
    let outcome = f.store.delete_branch(plan, &|| false).unwrap();
    assert_eq!(outcome.retained_through_revision, Some(9));
    assert_eq!(outcome.invalidated_branches, vec![parent.branch.clone()]);
    assert_eq!(outcome.collected_branches, 0);
    assert_eq!(outcome.deleted_turns, 6);
    assert_eq!(head(&f.path, &parent), Some(9));
    let kept = f.branch_rows(&parent);
    assert_eq!(kept["turns"].len(), 1);
    assert_eq!(kept["accepted_events"].len(), 1);
    assert!(kept["branch_projections"].is_empty());
    assert!(kept["derived_memory"].is_empty());
    assert!(!kept["branch_entities"].is_empty());
    let raw = Connection::open_with_flags(&f.path, OpenFlags::SQLITE_OPEN_READ_ONLY).unwrap();
    let text: String = raw
        .query_row(
            "SELECT response_json FROM turns WHERE story_id=?1 AND branch_id=?2",
            (&parent.story, &parent.branch),
            |r| r.get(0),
        )
        .unwrap();
    assert!(text.contains("inherited parent evidence"));
    assert!(!text.contains("unreachable parent tail"));
    drop(raw);
    f.store = Store::open(&f.path, None).unwrap();
    for ((s, state), rows) in scopes.iter().zip(states).zip(branch_rows) {
        same(&state, &f.state(s));
        same(&rows, &f.branch_rows(s));
    }
    same(&other, &f.rows(&f.other.story));
    same(&root, &f.branch_rows(&f.root));
    let late = f.store.resume(&f.late).unwrap().engine;
    assert!(!late.state().items.contains_key("potion"));
    let early = f.store.resume(&f.early).unwrap().engine;
    assert_eq!(early.state().items["potion"].owner, "player");
    assert!(
        !serde_json::to_string(&early.character_context("mira", &f.early, 4).unwrap())
            .unwrap()
            .contains("inherited parent evidence")
    );
}

#[test]
fn birth_floor_and_recursive_gc_keep_reserved_ids_and_only_required_source_prefixes() {
    let mut f = Fixture::new();
    let parent = f.parent.clone();
    let early = f.early.clone();
    let late = f.late.clone();
    let nested = f.nested.clone();
    let nested_state = f.state(&nested);
    let sibling = f.branch_rows(&f.sibling);
    let other = f.rows(&f.other.story);
    retire(&mut f, &parent);
    let early_out = retire(&mut f, &early);
    assert_eq!(early_out.retained_through_revision, Some(3));
    let out = retire(&mut f, &late);
    assert_eq!(out.retained_through_revision, None);
    assert_eq!(out.invalidated_branches, vec![late.branch.clone()]);
    assert_eq!(head(&f.path, &parent), Some(8));
    assert_eq!(head(&f.path, &early), Some(3));
    // The only live descendant rewinds to0, but both intermediate births are
    // still validated (parent born8, early born3). No local parent prose remains.
    assert!(f.branch_rows(&parent)["turns"].is_empty());
    same(&nested_state, &f.state(&nested));
    let final_out = retire(&mut f, &nested);
    assert_eq!(final_out.collected_branches, 3);
    let mut ids = vec![
        parent.branch.clone(),
        early.branch.clone(),
        nested.branch.clone(),
    ];
    ids.sort();
    assert_eq!(final_out.invalidated_branches, ids);
    for scope in [&parent, &early, &late, &nested] {
        assert_eq!(head(&f.path, scope), None);
        assert!(f.branch_rows(scope).values().all(Vec::is_empty));
    }
    let db = Connection::open_with_flags(&f.path, OpenFlags::SQLITE_OPEN_READ_ONLY).unwrap();
    let mut q = db
        .prepare("SELECT branch_id FROM branch_retention WHERE story_id=?1 ORDER BY branch_id")
        .unwrap();
    let reserved: Vec<String> = q
        .query_map([&f.root.story], |r| r.get(0))
        .unwrap()
        .map(Result::unwrap)
        .collect();
    assert_eq!(reserved.len(), 4);
    drop(q);
    drop(db);
    f.store = Store::open(&f.path, None).unwrap();
    same(&sibling, &f.branch_rows(&f.sibling));
    same(&other, &f.rows(&f.other.story));
    let root = f.root.clone();
    for scope in [&parent, &early, &late, &nested] {
        assert_eq!(
            f.store
                .fork_branch(
                    &ForkRequest {
                        parent: root.clone(),
                        child_branch: scope.branch.clone(),
                        expected_parent_revision: 8,
                        at_revision: 0
                    },
                    &|| false
                )
                .err(),
            Some(TurnError::Storage(StorageError::NotFound))
        );
    }
}

#[test]
fn retired_admission_old_prepared_receipts_and_parent_existing_fork_retry_are_refused() {
    let mut f = Fixture::new();
    let parent = f.parent.clone();
    assert_eq!(
        f.store.prepare_branch_deletion(&f.root, 8, &|| false).err(),
        Some(DeletionError::Malformed)
    );
    assert_eq!(
        f.store
            .prepare_branch_deletion(&parent, 11, &|| false)
            .err(),
        Some(DeletionError::Stale)
    );
    let mut bad = parent.clone();
    bad.branch = "bad/private".into();
    assert_eq!(
        f.store.prepare_branch_deletion(&bad, 12, &|| false).err(),
        Some(DeletionError::Malformed)
    );
    retire(&mut f, &parent);
    let expected = Some(TurnError::Storage(StorageError::NotFound));
    assert_eq!(f.store.resume(&parent).err(), expected);
    assert_eq!(f.store.commit_prepared(&f.ready).err(), expected);
    assert_eq!(f.store.begin_turn(f.ready.request()).err(), expected);
    assert_eq!(
        f.store.lookup_turn(&parent, "inherited-claim").err(),
        expected
    );
    assert_eq!(f.store.drafts(&parent).err(), expected);
    assert_eq!(f.store.rebuild_projection(&parent).err(), expected);
    assert_eq!(
        f.store.prepare_branch_deletion(&parent, 9, &|| false).err(),
        Some(DeletionError::NotFound)
    );
    assert_eq!(
        f.store
            .fork_branch(
                &ForkRequest {
                    parent: parent.clone(),
                    child_branch: f.late.branch.clone(),
                    expected_parent_revision: 9,
                    at_revision: 9
                },
                &|| false
            )
            .err(),
        expected
    );
    let child = f.early.clone();
    apply(
        &mut f.store,
        &child,
        "live-child-continues",
        vec![Command::Wait { ticks: 1 }],
    );
    assert_eq!(f.store.resume(&child).unwrap().engine.revision(), 5);
}

#[test]
fn real_busy_foreign_plan_and_same_store_identical_cache_aba_do_not_delete() {
    let mut f = Fixture::new();
    let p = f.parent.clone();
    let baseline = f.rows(&p.story);
    let plan = f.prepare(&p);
    let writer = Connection::open(&f.path).unwrap();
    writer.execute_batch("BEGIN IMMEDIATE").unwrap();
    assert_eq!(
        f.store.delete_branch(plan, &|| false).err(),
        Some(DeletionError::Busy)
    );
    writer.execute_batch("ROLLBACK").unwrap();
    drop(writer);
    same(&baseline, &f.rows(&p.story));
    let plan = f.prepare(&p);
    let mut foreign = Fixture::new();
    let theirs = foreign.rows(&foreign.root.story);
    assert_eq!(
        foreign.store.delete_branch(plan, &|| false).err(),
        Some(DeletionError::Stale)
    );
    same(&theirs, &foreign.rows(&foreign.root.story));
    let before = preview(&mut f);
    let plan = f.prepare(&p);
    f.store
        .invalidate_memory(&f.root, "mira", 8, &|| false)
        .unwrap();
    caches(&mut f.store, &f.root, 8);
    same(&before, &preview(&mut f));
    same(&baseline, &f.rows(&p.story));
    assert_eq!(
        f.store.delete_branch(plan, &|| false).err(),
        Some(DeletionError::Stale)
    );
    let plan = f.prepare(&p);
    let other = f.other.clone();
    apply(
        &mut f.store,
        &other,
        "other-story-writer",
        vec![Command::Wait { ticks: 1 }],
    );
    assert_eq!(
        f.store.delete_branch(plan, &|| false).err(),
        Some(DeletionError::Stale)
    );
    same(&baseline, &f.rows(&p.story));
}

#[test]
fn cancellation_at_every_retirement_and_recursive_gc_checkpoint_restores_all_rows() {
    for gc in [false, true] {
        let configure = |f: &mut Fixture| -> Scope {
            let p = f.parent.clone();
            let e = f.early.clone();
            let l = f.late.clone();
            let n = f.nested.clone();
            if gc {
                retire(f, &p);
                retire(f, &e);
                retire(f, &l);
                n
            } else {
                p
            }
        };
        let mut counter = Fixture::new();
        let target = configure(&mut counter);
        let plan = counter.prepare(&target);
        let calls = Cell::new(0usize);
        counter
            .store
            .delete_branch(plan, &|| {
                calls.set(calls.get() + 1);
                false
            })
            .unwrap();
        let total = calls.get();
        assert!((30..=256).contains(&total));
        let mut f = Fixture::new();
        let target = configure(&mut f);
        let baseline = f.rows(&f.root.story);
        let other = f.rows(&f.other.story);
        let nested = f.nested.clone();
        let state = f.state(&nested);
        for stop in 1..=total {
            let plan = f.prepare(&target);
            let calls = Cell::new(0);
            assert_eq!(
                f.store
                    .delete_branch(plan, &|| {
                        calls.set(calls.get() + 1);
                        calls.get() == stop
                    })
                    .err(),
                Some(DeletionError::Cancelled)
            );
            same(&baseline, &f.rows(&f.root.story));
            same(&other, &f.rows(&f.other.story));
            f.store = Store::open(&f.path, None).unwrap();
            same(&state, &f.state(&nested));
        }
    }
}

#[test]
fn preparation_cancel_panic_and_malformed_retention_are_nonmutating() {
    let mut f = Fixture::new();
    let p = f.parent.clone();
    let before = f.rows(&p.story);
    for stop in [1, 4, 12] {
        let polls = Cell::new(0);
        assert_eq!(
            f.store
                .prepare_branch_deletion(&p, 12, &|| {
                    polls.set(polls.get() + 1);
                    polls.get() == stop
                })
                .err(),
            Some(DeletionError::Cancelled)
        );
        same(&before, &f.rows(&p.story));
    }
    let plan = f.prepare(&p);
    assert_eq!(
        f.store
            .delete_branch(plan, &|| panic!("synthetic retirement cancellation"))
            .err(),
        Some(DeletionError::Cancelled)
    );
    same(&before, &f.rows(&p.story));
    Connection::open(&f.path)
        .unwrap()
        .execute(
            "INSERT INTO branch_retention(story_id,branch_id) VALUES(?1,?2)",
            (&f.root.story, &f.root.branch),
        )
        .unwrap();
    let bad = f.rows(&p.story);
    assert_eq!(
        f.store.prepare_branch_deletion(&p, 12, &|| false).err(),
        Some(DeletionError::Integrity)
    );
    same(&bad, &f.rows(&p.story));
}

#[test]
fn lost_confirmation_and_delete_reimport_aba_are_stale_even_with_restored_preview() {
    let mut f = Fixture::new();
    let p = f.parent.clone();
    let original = preview(&mut f);
    let archive = f.store.export_archive(&p.story, &|| false).unwrap();
    let old = f.prepare(&p);
    let accepted = f.prepare(&p);
    f.store.delete_branch(accepted, &|| false).unwrap();
    assert_eq!(
        f.store.delete_branch(old, &|| false).err(),
        Some(DeletionError::Stale)
    );
    let whole = f
        .store
        .prepare_story_deletion(&f.root, 8, &|| false)
        .unwrap();
    f.store.delete_story(whole, &|| false).unwrap();
    f.store
        .import_archive(
            locallore_storage::validate_archive(archive.bytes(), &|| false).unwrap(),
            &|| false,
        )
        .unwrap();
    workflow(&mut f.store, &p);
    caches(&mut f.store, &f.root, 8);
    same(&original, &preview(&mut f));
    let old = f.prepare(&p);
    let another = f
        .store
        .prepare_story_deletion(&f.root, 8, &|| false)
        .unwrap();
    f.store.delete_story(another, &|| false).unwrap();
    f.store
        .import_archive(
            locallore_storage::validate_archive(archive.bytes(), &|| false).unwrap(),
            &|| false,
        )
        .unwrap();
    workflow(&mut f.store, &p);
    caches(&mut f.store, &f.root, 8);
    same(&original, &preview(&mut f));
    assert_eq!(
        f.store.delete_branch(old, &|| false).err(),
        Some(DeletionError::Stale)
    );
}
