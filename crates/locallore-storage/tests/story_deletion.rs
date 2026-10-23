// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
use locallore::{contracts::*, engine::Engine};
use locallore_storage::{
    derived_memory::{PrepareRequest, Target},
    validate_archive, DeletionError, ForkRequest, Store, StoryDeletionPreview, TurnError,
};
use rusqlite::{types::Value, Connection, OpenFlags};
use std::{
    cell::Cell,
    collections::BTreeMap,
    path::PathBuf,
    sync::atomic::{AtomicU64, Ordering},
};

const TABLES: [&str; 9] = [
    "derived_memory",
    "event_witnesses",
    "accepted_events",
    "turns",
    "branch_projections",
    "branch_entities",
    "entities",
    "branches",
    "stories",
];
static NEXT: AtomicU64 = AtomicU64::new(0);
struct Fixture {
    path: PathBuf,
    store: Store,
    target: Scope,
    other: Scope,
    ready: Receipt,
}
// Synthetic roots are retained for failure inspection; no recursive removal or
// caller-chosen paths. Every fixture exclusively creates its own bounded root.
impl Fixture {
    fn new() -> Self {
        let root = std::env::temp_dir().join(format!(
            "locallore-story-deletion-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&root).unwrap();
        let path = root.join("synthetic.sqlite");
        let mut store = Store::open(&path, None).unwrap();
        let (target, ready) = populate(&mut store, "delete-target");
        let (other, _) = populate(&mut store, "retained-control");
        Self {
            path,
            store,
            target,
            other,
            ready,
        }
    }
    fn prepare(&mut self) -> locallore_storage::PreparedStoryDeletion {
        self.store
            .prepare_story_deletion(&self.target, 2, &|| false)
            .unwrap()
    }
    fn rows(&self, story: &str) -> BTreeMap<String, Vec<Vec<Value>>> {
        let db = Connection::open_with_flags(&self.path, OpenFlags::SQLITE_OPEN_READ_ONLY).unwrap();
        TABLES
            .into_iter()
            .map(|table| {
                let mut query = db
                    .prepare(&format!(
                        "SELECT * FROM {table} WHERE story_id=?1 ORDER BY 1,2,3"
                    ))
                    .unwrap();
                let width = query.column_count();
                let rows = query
                    .query_map([story], |r| (0..width).map(|i| r.get(i)).collect())
                    .unwrap()
                    .map(Result::unwrap)
                    .collect();
                (table.into(), rows)
            })
            .collect()
    }
}
fn seed(id: &str) -> Seed {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    seed.scope.story = id.into();
    seed
}
fn apply(store: &mut Store, scope: &Scope, id: &str, command: Command) -> Receipt {
    let engine = store.resume(scope).unwrap().engine;
    let request = engine.request(id, Intent::Actions(vec![command]));
    let proposal = Engine::proposal(&request).unwrap();
    let prepared = engine.preview(&request, &proposal).unwrap();
    store.begin_turn(&request).unwrap();
    store.commit_prepared(&prepared).unwrap()
}
fn fork(store: &mut Store, scope: &Scope, child: &str) -> Scope {
    let head = store.resume(scope).unwrap().engine.revision();
    store
        .fork_branch(
            &ForkRequest {
                parent: scope.clone(),
                child_branch: child.into(),
                expected_parent_revision: head,
                at_revision: 1,
            },
            &|| false,
        )
        .unwrap()
        .scope
}
fn memory(scope: &Scope, observer: &str) -> PrepareRequest {
    PrepareRequest {
        scope: scope.clone(),
        observer: observer.into(),
        expected_revision: 2,
        from_exclusive: 0,
        through_revision: 2,
        target: Target::SceneWindow,
    }
}
fn caches(store: &mut Store, scope: &Scope) {
    for observer in ["player", "mira"] {
        let prepared = store
            .prepare_memory(&memory(scope, observer), &|| false)
            .unwrap();
        store.publish_memory(prepared, &|| false).unwrap();
    }
}
fn workflow(store: &mut Store, scope: &Scope) -> Receipt {
    let engine = store.resume(scope).unwrap().engine;
    let request = engine.request(
        "old-ready",
        Intent::Actions(vec![Command::Wait { ticks: 1 }]),
    );
    let ready = engine
        .preview(&request, &Engine::proposal(&request).unwrap())
        .unwrap();
    store.begin_turn(&request).unwrap();
    for (id, status) in [("cancelled-key", 0), ("failed-key", 1), ("stale-key", 2)] {
        let req = engine.request(id, Intent::Actions(vec![Command::Wait { ticks: 1 }]));
        store.begin_turn(&req).unwrap();
        match status {
            0 => store.cancel_turn(&req),
            1 => store.fail_turn(&req),
            _ => store.stale_turn(&req),
        }
        .unwrap();
    }
    ready
}
fn populate(store: &mut Store, id: &str) -> (Scope, Receipt) {
    let seed = seed(id);
    let scope = seed.scope.clone();
    store
        .create_story("Synthetic deletion isolation", seed)
        .unwrap();
    apply(store, &scope, "prefix", Command::Wait { ticks: 1 });
    let child = fork(store, &scope, "child");
    apply(
        store,
        &scope,
        "same-key",
        Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 1,
        },
    );
    apply(
        store,
        &child,
        "same-key",
        Command::Consume {
            item: "potion".into(),
        },
    );
    let sibling = fork(store, &scope, "sibling");
    apply(
        store,
        &sibling,
        "sibling-claim",
        Command::Say {
            text: format!("Synthetic {id} observer canary"),
            audience: ["mira".into()].into(),
        },
    );
    let nested = fork(store, &child, "nested");
    apply(store, &nested, "nested-wait", Command::Wait { ticks: 1 });
    let ready = workflow(store, &scope);
    caches(store, &scope);
    (scope, ready)
}
fn accepted(store: &mut Store, root: &Scope) -> Vec<Vec<u8>> {
    let mut result = Vec::new();
    for branch in [
        &root.branch,
        &"child".into(),
        &"sibling".into(),
        &"nested".into(),
    ] {
        let scope = Scope {
            story: root.story.clone(),
            branch: branch.clone(),
        };
        let engine = store.resume(&scope).unwrap().engine;
        result.push(engine.canonical_bytes());
        result.push(serde_json::to_vec(engine.receipts()).unwrap());
        for observer in ["player", "mira", "sable"] {
            result.push(
                serde_json::to_vec(
                    &engine
                        .character_context(observer, &scope, engine.revision())
                        .unwrap(),
                )
                .unwrap(),
            );
        }
    }
    for observer in ["player", "mira"] {
        result.push(
            serde_json::to_vec(
                store
                    .read_memory(&memory(root, observer), &|| false)
                    .unwrap()
                    .json(),
            )
            .unwrap(),
        );
    }
    result
}
fn same<T: PartialEq>(left: &T, right: &T) {
    assert!(left == right, "synthetic retained state differed");
}
fn preview(store: &mut Store, scope: &Scope) -> StoryDeletionPreview {
    store
        .prepare_story_deletion(scope, 2, &|| false)
        .unwrap()
        .preview()
        .clone()
}

#[test]
fn preview_is_bounded_read_only_and_covers_every_timeline_and_workflow_kind() {
    let mut f = Fixture::new();
    let rows = f.rows(&f.target.story);
    let canon = accepted(&mut f.store, &f.target);
    let p = f.prepare();
    let p = p.preview();
    assert_eq!(
        (
            p.version,
            p.branch_heads.len(),
            p.committed_turns,
            p.draft_turns,
            p.noncommitted_turns,
            p.derived_packets
        ),
        (2, 4, 5, 1, 4, 2)
    );
    assert_eq!(p.rows.len(), 10);
    assert_eq!(p.rows["turns"], 9);
    for (table, actual) in &rows {
        assert_eq!(p.rows[table], actual.len() as u64);
    }
    assert!(p.branch_heads.values().all(|head| *head == 2));
    assert!(p.privacy_warning.contains("Exported files"));
    assert!(serde_json::to_vec(p).unwrap().len() <= 65_536);
    same(&rows, &f.rows(&f.target.story));
    same(&canon, &accepted(&mut f.store, &f.target));
    let child = Scope {
        story: f.target.story.clone(),
        branch: "child".into(),
    };
    assert_eq!(
        f.store.prepare_story_deletion(&child, 2, &|| false).err(),
        Some(DeletionError::Malformed)
    );
    assert_eq!(
        f.store
            .prepare_story_deletion(&f.target, 1, &|| false)
            .err(),
        Some(DeletionError::Stale)
    );
    let missing = Scope {
        story: "missing".into(),
        branch: f.target.branch.clone(),
    };
    assert_eq!(
        f.store.prepare_story_deletion(&missing, 0, &|| false).err(),
        Some(DeletionError::NotFound)
    );
    let bad = Scope {
        story: "bad/private".into(),
        branch: f.target.branch.clone(),
    };
    assert_eq!(
        f.store.prepare_story_deletion(&bad, 0, &|| false).err(),
        Some(DeletionError::Malformed)
    );
}

#[test]
fn whole_story_delete_reopens_zero_rows_retains_other_canon_and_allows_explicit_reimport() {
    let mut f = Fixture::new();
    let retained = f.rows(&f.other.story);
    let canon = accepted(&mut f.store, &f.other);
    let archive = f.store.export_archive(&f.target.story, &|| false).unwrap();
    let plan = f.prepare();
    let outcome = f.store.delete_story(plan, &|| false).unwrap();
    assert_eq!((outcome.deleted_branches, outcome.deleted_turns), (4, 9));
    assert!(f.rows(&f.target.story).values().all(Vec::is_empty));
    same(&retained, &f.rows(&f.other.story));
    same(&canon, &accepted(&mut f.store, &f.other));
    assert!(f.store.commit_prepared(&f.ready).is_err());
    f.store = Store::open(&f.path, None).unwrap();
    assert!(f.rows(&f.target.story).values().all(Vec::is_empty));
    same(&retained, &f.rows(&f.other.story));
    same(&canon, &accepted(&mut f.store, &f.other));
    f.store
        .import_archive(
            validate_archive(archive.bytes(), &|| false).unwrap(),
            &|| false,
        )
        .unwrap();
    assert_eq!(
        f.store.lookup_turn(&f.target, "old-ready").err(),
        Some(TurnError::UnknownTurn)
    );
    assert_eq!(
        f.store.commit_prepared(&f.ready).err(),
        Some(TurnError::UnknownTurn)
    );
    apply(
        &mut f.store,
        &f.target,
        "fresh-after-import",
        Command::Wait { ticks: 1 },
    );
    assert_eq!(f.store.resume(&f.target).unwrap().engine.revision(), 3);
    // An old owner with a newly recreated identical draft needs the native
    // session fence; deleting stored drafts alone does not solve that ABA.
}

#[test]
fn consumed_and_foreign_database_plans_cannot_delete_again_or_cross_databases() {
    let mut f = Fixture::new();
    let mut other = Fixture::new();
    let rows = other.rows(&other.target.story);
    let plan = f.prepare();
    assert_eq!(
        other.store.delete_story(plan, &|| false).err(),
        Some(DeletionError::Stale)
    );
    same(&rows, &other.rows(&other.target.story));
    let first = f.prepare();
    let repeated = f.prepare();
    f.store.delete_story(first, &|| false).unwrap();
    assert_eq!(
        f.store.delete_story(repeated, &|| false).err(),
        Some(DeletionError::Stale)
    );
    assert_eq!(
        f.store
            .prepare_story_deletion(&f.target, 2, &|| false)
            .err(),
        Some(DeletionError::NotFound)
    );
}

#[test]
fn real_writer_busy_preserves_both_stories_and_waiting_preview_does_not_block_writer() {
    let mut f = Fixture::new();
    let rows = f.rows(&f.target.story);
    let retained = f.rows(&f.other.story);
    let plan = f.prepare();
    let writer = Connection::open(&f.path).unwrap();
    writer.execute_batch("BEGIN IMMEDIATE").unwrap();
    assert_eq!(
        f.store.delete_story(plan, &|| false).err(),
        Some(DeletionError::Busy)
    );
    writer.execute_batch("ROLLBACK").unwrap();
    drop(writer);
    same(&rows, &f.rows(&f.target.story));
    same(&retained, &f.rows(&f.other.story));
    let plan = f.prepare();
    let mut writer = Store::open(&f.path, None).unwrap();
    apply(
        &mut writer,
        &f.other,
        "unrelated-writer",
        Command::Wait { ticks: 1 },
    );
    assert_eq!(
        f.store.delete_story(plan, &|| false).err(),
        Some(DeletionError::Stale)
    );
    same(&rows, &f.rows(&f.target.story));
}

#[test]
fn same_store_cache_aba_and_delete_reimport_aba_stale_even_when_preview_is_identical() {
    let mut f = Fixture::new();
    let before = preview(&mut f.store, &f.target);
    let plan = f.prepare();
    let rows = f.rows(&f.target.story);
    f.store
        .invalidate_memory(&f.target, "mira", 2, &|| false)
        .unwrap();
    caches(&mut f.store, &f.target);
    same(&rows, &f.rows(&f.target.story));
    same(&before, &preview(&mut f.store, &f.target));
    assert_eq!(
        f.store.delete_story(plan, &|| false).err(),
        Some(DeletionError::Stale)
    );
    let old = f.prepare();
    let archive = f.store.export_archive(&f.target.story, &|| false).unwrap();
    let deleting = f.prepare();
    f.store.delete_story(deleting, &|| false).unwrap();
    f.store
        .import_archive(
            validate_archive(archive.bytes(), &|| false).unwrap(),
            &|| false,
        )
        .unwrap();
    workflow(&mut f.store, &f.target);
    caches(&mut f.store, &f.target);
    same(&before, &preview(&mut f.store, &f.target));
    same(&rows, &f.rows(&f.target.story));
    assert_eq!(
        f.store.delete_story(old, &|| false).err(),
        Some(DeletionError::Stale)
    );
}

#[test]
fn unrelated_draft_and_cache_commits_conservatively_invalidate_confirmation() {
    let mut f = Fixture::new();
    let rows = f.rows(&f.target.story);
    let plan = f.prepare();
    let e = f.store.resume(&f.other).unwrap().engine;
    f.store
        .begin_turn(&e.request(
            "other-new-draft",
            Intent::Actions(vec![Command::Wait { ticks: 1 }]),
        ))
        .unwrap();
    assert_eq!(
        f.store.delete_story(plan, &|| false).err(),
        Some(DeletionError::Stale)
    );
    let plan = f.prepare();
    f.store
        .invalidate_memory(&f.other, "mira", 2, &|| false)
        .unwrap();
    assert_eq!(
        f.store.delete_story(plan, &|| false).err(),
        Some(DeletionError::Stale)
    );
    same(&rows, &f.rows(&f.target.story));
}

#[test]
fn cancellation_at_every_observed_delete_checkpoint_rolls_back_all_tables() {
    let mut first = Fixture::new();
    let plan = first.prepare();
    let polls = Cell::new(0usize);
    first
        .store
        .delete_story(plan, &|| {
            polls.set(polls.get() + 1);
            false
        })
        .unwrap();
    let total = polls.get();
    assert!((20..=64).contains(&total));
    for stop in 1..=total {
        let mut f = Fixture::new();
        let target = f.rows(&f.target.story);
        let other = f.rows(&f.other.story);
        let canon = accepted(&mut f.store, &f.target);
        let plan = f.prepare();
        let polled = Cell::new(0);
        assert_eq!(
            f.store
                .delete_story(plan, &|| {
                    polled.set(polled.get() + 1);
                    polled.get() == stop
                })
                .err(),
            Some(DeletionError::Cancelled)
        );
        same(&target, &f.rows(&f.target.story));
        same(&other, &f.rows(&f.other.story));
        f.store = Store::open(&f.path, None).unwrap();
        same(&canon, &accepted(&mut f.store, &f.target));
    }
}

#[test]
fn preparation_cancellation_and_panicking_delete_cancel_are_nonmutating() {
    let mut f = Fixture::new();
    let target = f.rows(&f.target.story);
    let other = f.rows(&f.other.story);
    for stop in [1, 3, 8, 15] {
        let polls = Cell::new(0);
        assert_eq!(
            f.store
                .prepare_story_deletion(&f.target, 2, &|| {
                    polls.set(polls.get() + 1);
                    polls.get() == stop
                })
                .err(),
            Some(DeletionError::Cancelled)
        );
        same(&target, &f.rows(&f.target.story));
    }
    let plan = f.prepare();
    assert_eq!(
        f.store
            .delete_story(plan, &|| panic!("synthetic cancellation panic"))
            .err(),
        Some(DeletionError::Cancelled)
    );
    same(&target, &f.rows(&f.target.story));
    same(&other, &f.rows(&f.other.story));
}
