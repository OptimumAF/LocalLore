// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Direct actual Store source-basis transactions; no Host precheck or canonical SQL.
use locallore::{contracts::*, engine::Engine};
use locallore_storage::{
    playable_archive::validate_archive, ForkRequest, Store, TurnError, TurnPhase,
};
use std::{
    path::PathBuf,
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT: AtomicU64 = AtomicU64::new(0);
struct Fixture(PathBuf);
impl Fixture {
    fn new() -> Self {
        let root = std::env::temp_dir().join(format!(
            "locallore-store-basis-review-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&root).unwrap();
        Self(root)
    }
    fn path(&self) -> PathBuf {
        self.0.join("synthetic.sqlite")
    }
    fn store(&self) -> Store {
        Store::open_application(&self.path()).unwrap()
    }
}
impl Drop for Fixture {
    fn drop(&mut self) {
        std::fs::remove_dir_all(&self.0).unwrap();
    }
}
fn seed() -> Seed {
    serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap()
}
fn create(fixture: &Fixture) -> Engine {
    let seed = seed();
    let scope = seed.scope.clone();
    let mut store = fixture.store();
    store
        .create_story("Synthetic transaction basis", seed)
        .unwrap();
    store.resume(&scope).unwrap().engine
}
fn preview(engine: &Engine, key: &str, ticks: u16) -> Receipt {
    let request = engine.request(key, Intent::Actions(vec![Command::Wait { ticks }]));
    let proposal = Engine::proposal(&request).unwrap();
    engine.preview(&request, &proposal).unwrap()
}
fn commit(store: &mut Store, engine: &Engine, key: &str) -> Engine {
    let receipt = preview(engine, key, 1);
    store.begin_turn(receipt.request()).unwrap();
    store.commit_prepared(&receipt).unwrap();
    store.resume(engine.scope()).unwrap().engine
}
fn initial() -> (Fixture, Store, Engine) {
    let fixture = Fixture::new();
    let engine = create(&fixture);
    let mut store = fixture.store();
    let engine = commit(&mut store, &engine, "original-prefix");
    (fixture, store, engine)
}
fn replacement(
    fixture: &Fixture,
    store: &mut Store,
    original: &Engine,
    request: &Request,
) -> Engine {
    let other = Fixture::new();
    let empty = create(&other);
    let changed = commit(&mut other.store(), &empty, "replacement-prefix");
    assert_eq!(original.scope(), changed.scope());
    assert_eq!(original.seed(), changed.seed());
    assert_eq!(original.revision(), changed.revision());
    assert_eq!(original.canonical_bytes(), changed.canonical_bytes());
    assert_ne!(original.receipts(), changed.receipts());
    let archive = other
        .store()
        .export_archive(&original.scope().story, &|| false)
        .unwrap();
    let prepared = store
        .prepare_story_deletion(original.scope(), original.revision(), &|| false)
        .unwrap();
    store.delete_story(prepared, &|| false).unwrap();
    store
        .import_archive(
            validate_archive(archive.bytes(), &|| false).unwrap(),
            &|| false,
        )
        .unwrap();
    let recreated = store.begin_turn(request).unwrap();
    assert_eq!(recreated.phase, TurnPhase::Draft);
    assert_eq!(recreated.request, *request);
    assert_eq!(
        fixture
            .store()
            .resume(original.scope())
            .unwrap()
            .engine
            .receipts(),
        changed.receipts()
    );
    changed
}
fn unchanged(fixture: &Fixture, expected: &Engine, request: &Request, bytes: &[u8]) {
    assert_eq!(std::fs::read(fixture.path()).unwrap(), bytes);
    let mut actual = fixture.store();
    let engine = actual.resume(expected.scope()).unwrap().engine;
    assert_eq!(engine.canonical_bytes(), expected.canonical_bytes());
    assert_eq!(engine.receipts(), expected.receipts());
    let draft = actual.turn_status(request).unwrap();
    assert_eq!(draft.phase, TurnPhase::Draft);
    assert_eq!(draft.request, *request);
    assert!(draft.receipt.is_none());
}

#[test]
fn direct_bound_commit_rejects_replaced_prefix_inside_actual_write_transaction() {
    let (fixture, mut store, original) = initial();
    let basis = original.accepted_history_basis().unwrap();
    let candidate = preview(&original, "prepared-original-key", 1);
    store.begin_turn(candidate.request()).unwrap();
    let changed = replacement(&fixture, &mut store, &original, candidate.request());
    let bytes = std::fs::read(fixture.path()).unwrap();
    // No Host call or preceding bound status check can supply this protection.
    assert!(matches!(
        store.commit_prepared_bound(&candidate, &basis),
        Err(TurnError::Stale)
    ));
    unchanged(&fixture, &changed, candidate.request(), &bytes);
}
#[test]
fn direct_bound_status_and_each_terminal_cleanup_preserve_replacement_draft() {
    let (fixture, mut store, original) = initial();
    let basis = original.accepted_history_basis().unwrap();
    let candidate = preview(&original, "cleanup-original-key", 1);
    store.begin_turn(candidate.request()).unwrap();
    let changed = replacement(&fixture, &mut store, &original, candidate.request());
    let bytes = std::fs::read(fixture.path()).unwrap();
    assert!(matches!(
        store.turn_status_bound(candidate.request(), &basis),
        Err(TurnError::Stale)
    ));
    for phase in [TurnPhase::Cancelled, TurnPhase::Failed, TurnPhase::Stale] {
        assert!(matches!(
            store.finish_bound(candidate.request(), &basis, phase),
            Err(TurnError::Stale)
        ));
        unchanged(&fixture, &changed, candidate.request(), &bytes);
    }
}
#[test]
fn direct_bound_apis_refuse_shorter_basis_than_request_expected_revision() {
    let fixture = Fixture::new();
    let empty = create(&fixture);
    let shorter = empty.accepted_history_basis().unwrap();
    let mut store = fixture.store();
    let current = commit(&mut store, &empty, "unprotected-first-turn");
    assert!(
        current.matches_accepted_history(&shorter).unwrap(),
        "an intact shorter prefix is not a bound request basis"
    );
    let candidate = preview(&current, "later-request", 1);
    store.begin_turn(candidate.request()).unwrap();
    let bytes = std::fs::read(fixture.path()).unwrap();
    assert!(matches!(
        store.turn_status_bound(candidate.request(), &shorter),
        Err(TurnError::Stale)
    ));
    assert!(matches!(
        store.commit_prepared_bound(&candidate, &shorter),
        Err(TurnError::Stale)
    ));
    for phase in [TurnPhase::Cancelled, TurnPhase::Failed, TurnPhase::Stale] {
        assert!(matches!(
            store.finish_bound(candidate.request(), &shorter, phase),
            Err(TurnError::Stale)
        ));
    }
    unchanged(&fixture, &current, candidate.request(), &bytes);
}
#[test]
fn intact_prefix_allows_ordinary_append_and_exact_winner_retry() {
    let (fixture, mut store, original) = initial();
    let basis = original.accepted_history_basis().unwrap();
    let candidate = preview(&original, "old-draft", 1);
    store.begin_turn(candidate.request()).unwrap();
    let appended = commit(&mut fixture.store(), &original, "other-owner-append");
    assert!(appended.matches_accepted_history(&basis).unwrap());
    assert_eq!(
        store
            .turn_status_bound(candidate.request(), &basis)
            .unwrap()
            .phase,
        TurnPhase::Draft
    );
    assert!(matches!(
        store.commit_prepared_bound(&candidate, &basis),
        Err(TurnError::Stale)
    ));
    assert_eq!(
        store.turn_status(candidate.request()).unwrap().phase,
        TurnPhase::Stale
    );
    let basis = appended.accepted_history_basis().unwrap();
    let winner = preview(&appended, "winner-key", 1);
    store.begin_turn(winner.request()).unwrap();
    let committed = store.commit_prepared_bound(&winner, &basis).unwrap();
    assert_eq!(committed, winner);
    assert_eq!(
        store.commit_prepared_bound(&winner, &basis).unwrap(),
        committed
    );
    assert_eq!(
        store
            .turn_status_bound(winner.request(), &basis)
            .unwrap()
            .receipt,
        Some(committed.clone())
    );
    for phase in [TurnPhase::Cancelled, TurnPhase::Failed, TurnPhase::Stale] {
        let finished = store.finish_bound(winner.request(), &basis, phase).unwrap();
        assert_eq!(finished.phase, TurnPhase::Committed);
        assert_eq!(finished.receipt, Some(committed.clone()));
    }
    assert_eq!(
        store
            .resume(original.scope())
            .unwrap()
            .engine
            .receipts()
            .last(),
        Some(&committed)
    );
}
fn empty_child(fixture: &Fixture, parent: &str) -> Engine {
    let root = create(fixture);
    let mut store = fixture.store();
    store
        .fork_branch(
            &ForkRequest {
                parent: root.scope().clone(),
                child_branch: parent.into(),
                expected_parent_revision: 0,
                at_revision: 0,
            },
            &|| false,
        )
        .unwrap();
    let parent = Scope {
        story: root.scope().story.clone(),
        branch: parent.into(),
    };
    let child = store
        .fork_branch(
            &ForkRequest {
                parent,
                child_branch: "same-child".into(),
                expected_parent_revision: 0,
                at_revision: 0,
            },
            &|| false,
        )
        .unwrap();
    store.resume(&child.scope).unwrap().engine
}
#[test]
fn direct_empty_history_child_basis_binds_private_immutable_parent_chain() {
    let left = Fixture::new();
    let right = Fixture::new();
    let a = empty_child(&left, "parent-a");
    let b = empty_child(&right, "parent-b");
    assert_eq!(a.seed(), b.seed());
    assert_eq!(a.scope(), b.scope());
    assert_eq!(a.revision(), 0);
    assert_eq!(b.revision(), 0);
    assert_eq!(a.canonical_bytes(), b.canonical_bytes());
    assert!(a.receipts().is_empty() && b.receipts().is_empty());
    let basis = a.accepted_history_basis().unwrap();
    assert!(!b.matches_accepted_history(&basis).unwrap());
    let mut store = right.store();
    let candidate = preview(&a, "empty-lineage-draft", 1);
    store.begin_turn(candidate.request()).unwrap();
    let bytes = std::fs::read(right.path()).unwrap();
    assert!(matches!(
        store.commit_prepared_bound(&candidate, &basis),
        Err(TurnError::Stale)
    ));
    assert!(matches!(
        store.turn_status_bound(candidate.request(), &basis),
        Err(TurnError::Stale)
    ));
    assert!(matches!(
        store.finish_bound(candidate.request(), &basis, TurnPhase::Cancelled),
        Err(TurnError::Stale)
    ));
    unchanged(&right, &b, candidate.request(), &bytes);
}
#[test]
fn direct_bound_paths_retain_exact_original_request_mismatch_guard() {
    let (fixture, mut store, original) = initial();
    let basis = original.accepted_history_basis().unwrap();
    let a = preview(&original, "same-key", 1);
    let b = preview(&original, "same-key", 2);
    assert_ne!(a.request(), b.request());
    store.begin_turn(a.request()).unwrap();
    let bytes = std::fs::read(fixture.path()).unwrap();
    assert!(matches!(
        store.turn_status_bound(b.request(), &basis),
        Err(TurnError::RetryMismatch)
    ));
    assert!(matches!(
        store.commit_prepared_bound(&b, &basis),
        Err(TurnError::RetryMismatch)
    ));
    for phase in [TurnPhase::Cancelled, TurnPhase::Failed, TurnPhase::Stale] {
        assert!(matches!(
            store.finish_bound(b.request(), &basis, phase),
            Err(TurnError::RetryMismatch)
        ));
    }
    unchanged(&fixture, &original, a.request(), &bytes);
}

// Added for the new 55c8641 admission API; these are not pre-fix RED executions.
#[test]
fn direct_bound_begin_refuses_replacement_before_adopting_existing_draft() {
    let (fixture, mut store, original) = initial();
    let basis = original.accepted_history_basis().unwrap();
    let candidate = preview(&original, "admission-replacement", 1);
    let changed = replacement(&fixture, &mut store, &original, candidate.request());
    let bytes = std::fs::read(fixture.path()).unwrap();
    assert!(matches!(
        store.begin_bound(candidate.request(), &basis),
        Err(TurnError::Stale)
    ));
    unchanged(&fixture, &changed, candidate.request(), &bytes);
    let new = preview(&original, "not-admitted-on-replacement", 1);
    assert!(matches!(
        store.begin_bound(new.request(), &basis),
        Err(TurnError::Stale)
    ));
    assert!(matches!(
        store.turn_status(new.request()),
        Err(TurnError::UnknownTurn)
    ));
    unchanged(&fixture, &changed, candidate.request(), &bytes);
}

#[test]
fn direct_bound_begin_rejects_shorter_request_basis_without_inserting() {
    let fixture = Fixture::new();
    let empty = create(&fixture);
    let shorter = empty.accepted_history_basis().unwrap();
    let mut store = fixture.store();
    let current = commit(&mut store, &empty, "admission-prefix");
    let candidate = preview(&current, "admission-later-request", 1);
    let bytes = std::fs::read(fixture.path()).unwrap();
    assert!(current.matches_accepted_history(&shorter).unwrap());
    assert!(matches!(
        store.begin_bound(candidate.request(), &shorter),
        Err(TurnError::Stale)
    ));
    assert!(matches!(
        store.turn_status(candidate.request()),
        Err(TurnError::UnknownTurn)
    ));
    assert_eq!(std::fs::read(fixture.path()).unwrap(), bytes);
    assert_eq!(
        store.resume(current.scope()).unwrap().engine.receipts(),
        current.receipts()
    );
}

#[test]
fn direct_bound_begin_admits_and_retries_exact_request_and_committed_winner() {
    let (fixture, mut store, original) = initial();
    let basis = original.accepted_history_basis().unwrap();
    let candidate = preview(&original, "admission-winner", 1);
    let draft = store.begin_bound(candidate.request(), &basis).unwrap();
    assert_eq!(draft.phase, TurnPhase::Draft);
    assert_eq!(draft.request, *candidate.request());
    assert!(draft.receipt.is_none());
    let bytes = std::fs::read(fixture.path()).unwrap();
    let retry = store.begin_bound(candidate.request(), &basis).unwrap();
    assert_eq!(retry.phase, TurnPhase::Draft);
    assert_eq!(retry.request, *candidate.request());
    let mismatch = preview(&original, "admission-winner", 2);
    assert!(matches!(
        store.begin_bound(mismatch.request(), &basis),
        Err(TurnError::RetryMismatch)
    ));
    unchanged(&fixture, &original, candidate.request(), &bytes);
    let winner = store.commit_prepared_bound(&candidate, &basis).unwrap();
    let bytes = std::fs::read(fixture.path()).unwrap();
    let retry = store.begin_bound(candidate.request(), &basis).unwrap();
    assert_eq!(retry.phase, TurnPhase::Committed);
    assert_eq!(retry.request, *candidate.request());
    assert_eq!(retry.receipt, Some(winner));
    assert_eq!(std::fs::read(fixture.path()).unwrap(), bytes);
}
