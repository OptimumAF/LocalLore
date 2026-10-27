// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Trusted Store seam only. Successful seeds and accepted history are produced
//! by typed Store/Core APIs; no Host, provider, arbitrary seed wire or SQL canon.
use locallore::{contracts::*, engine::Engine};
use locallore_storage::{StorageError, Store, TurnPhase};
use rusqlite::{Connection, TransactionBehavior};
use std::{
    path::PathBuf,
    sync::{
        atomic::{AtomicU64, Ordering},
        Arc, Barrier,
    },
    thread,
};

static NEXT: AtomicU64 = AtomicU64::new(0);
struct Temp(PathBuf);
impl Temp {
    fn new() -> Self {
        let path = std::env::temp_dir().join(format!(
            "locallore-named-creation-{}-{}-{}",
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
    fn database(&self) -> PathBuf {
        self.0.join("stories.sqlite3")
    }
    fn open(&self) -> Store {
        Store::open(&self.database(), None).unwrap()
    }
}
impl Drop for Temp {
    fn drop(&mut self) {
        std::fs::remove_dir_all(&self.0).unwrap();
    }
}
fn seed(story: &str) -> Seed {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    seed.scope.story = story.into();
    seed
}
fn advance(store: &mut Store, scope: &Scope, turn: &str) {
    let engine = store.resume(scope).unwrap().engine;
    let request = engine.request(turn, Intent::Actions(vec![Command::Wait { ticks: 1 }]));
    let proposal = Engine::proposal(&request).unwrap();
    let receipt = engine.preview(&request, &proposal).unwrap();
    store.begin_turn(&request).unwrap();
    store
        .commit_turn(&request, &proposal, receipt.narration())
        .unwrap();
}
fn archive(store: &mut Store, story: &str) -> Vec<u8> {
    store
        .export_archive(story, &|| false)
        .unwrap()
        .bytes()
        .to_vec()
}
type Creation = Result<(Scope, bool), StorageError>;
fn race(first: Store, second: Store, inputs: [(String, Seed); 2]) -> Vec<(String, Seed, Creation)> {
    let barrier = Arc::new(Barrier::new(3));
    let handles: Vec<_> = [first, second]
        .into_iter()
        .zip(inputs)
        .map(|(mut store, (title, input))| {
            let barrier = Arc::clone(&barrier);
            thread::spawn(move || {
                barrier.wait();
                let result = store.create_workspace_exact(&title, input.clone());
                (title, input, result)
            })
        })
        .collect();
    barrier.wait();
    handles
        .into_iter()
        .map(|handle| handle.join().unwrap())
        .collect()
}

#[test]
fn exact_retry_reopens_at_current_head_without_replaying_or_losing_pending_intent() {
    let temp = Temp::new();
    let input = seed("quay-0123456789abcdef0123456789abcdef");
    let scope = input.scope.clone();
    let mut store = temp.open();
    assert_eq!(
        store
            .create_workspace_exact("My original title", input.clone())
            .unwrap(),
        (scope.clone(), true)
    );
    advance(&mut store, &scope, "accepted-before-retry");
    let before = store.resume(&scope).unwrap().engine;
    let pending = before.request(
        "unsent-to-provider",
        Intent::Actions(vec![Command::Wait { ticks: 1 }]),
    );
    assert_eq!(store.begin_turn(&pending).unwrap().phase, TurnPhase::Draft);
    let before_archive = archive(&mut store, &scope.story);
    drop(store);

    let mut store = temp.open();
    assert_eq!(
        store
            .create_workspace_exact("My original title", input.clone())
            .unwrap(),
        (scope.clone(), false)
    );
    let after = store.resume(&scope).unwrap().engine;
    assert_eq!(after.revision(), 1);
    assert_eq!(after.canonical_bytes(), before.canonical_bytes());
    assert_eq!(after.receipts(), before.receipts());
    assert_eq!(
        after.accepted_history_basis().unwrap(),
        before.accepted_history_basis().unwrap()
    );
    assert_eq!(store.load_seed(&scope).unwrap(), input);
    assert_eq!(store.turn_status(&pending).unwrap().phase, TurnPhase::Draft);
    assert_eq!(store.turn_status(&pending).unwrap().request, pending);
    assert_eq!(archive(&mut store, &scope.story), before_archive);
    let catalog = store.stories().unwrap();
    assert_eq!(catalog.len(), 1);
    assert_eq!(catalog[0].title, "My original title");
    assert_eq!(catalog[0].revision, 1);
    assert_eq!(catalog[0].drafts, 1);
}

#[test]
fn valid_title_root_and_full_seed_mismatches_cannot_overwrite_accepted_history() {
    let temp = Temp::new();
    let mut store = temp.open();
    let input = seed("exact-source");
    let scope = input.scope.clone();
    store
        .create_workspace_exact("Keep exact title", input.clone())
        .unwrap();
    advance(&mut store, &scope, "kept-canon");
    let before = archive(&mut store, &scope.story);
    let mut other_root = input.clone();
    other_root.scope.branch = "different-root".into();
    let mut other_seed = input.clone();
    other_seed.actors.get_mut("player").unwrap().name = "Different original name".into();
    // Same starter ID and scope are insufficient; the complete Seed must match.
    assert_eq!(other_seed.id, input.id);
    assert_eq!(other_seed.scope, input.scope);
    for (title, different) in [
        ("Different title", input.clone()),
        ("Keep exact title", other_root),
        ("Keep exact title", other_seed),
    ] {
        Engine::new(different.clone()).unwrap();
        assert_eq!(
            store.create_workspace_exact(title, different).unwrap_err(),
            StorageError::DuplicateStory
        );
        assert_eq!(archive(&mut store, &scope.story), before);
        assert_eq!(store.load_seed(&scope).unwrap(), input);
    }
    assert_eq!(store.stories().unwrap().len(), 1);
}

#[test]
fn invalid_inputs_leave_no_partial_story_and_keep_generic_title_bounds() {
    let temp = Temp::new();
    let mut store = temp.open();
    let input = seed("invalid-input-target");
    let mut invalid = input.clone();
    invalid.actors.remove("player");
    assert_eq!(
        store
            .create_workspace_exact("Valid title", invalid)
            .unwrap_err(),
        StorageError::InvalidSeed
    );
    for title in [String::new(), "bad\0title".into(), "x".repeat(257)] {
        assert_eq!(
            store
                .create_workspace_exact(&title, input.clone())
                .unwrap_err(),
            StorageError::InvalidInput
        );
        assert!(store.stories().unwrap().is_empty());
        assert_eq!(
            store.load_seed(&input.scope).unwrap_err(),
            StorageError::NotFound
        );
    }
    // This trusted generic seam retains the old256-scalar bound, rather than
    // borrowing the separately stricter named-creation UI title policy.
    let maximum = "雪".repeat(256);
    assert_eq!(
        store
            .create_workspace_exact(&maximum, input.clone())
            .unwrap(),
        (input.scope.clone(), true)
    );
    assert!(!store.create_workspace_exact(&maximum, input).unwrap().1);
}

#[test]
fn competing_final_catalog_slot_is_atomic_and_exact_retry_still_works_at_capacity() {
    let temp = Temp::new();
    let mut store = temp.open();
    for index in 0..255 {
        store
            .create_story(
                &format!("Existing {index}"),
                seed(&format!("existing-{index}")),
            )
            .unwrap();
    }
    let kept = seed("existing-0");
    advance(&mut store, &kept.scope, "keep-advanced-at-cap");
    let before = archive(&mut store, &kept.scope.story);
    let inputs = [
        ("Last candidate A".into(), seed("last-candidate-a")),
        ("Last candidate B".into(), seed("last-candidate-b")),
    ];
    let results = race(temp.open(), temp.open(), inputs);
    let mut created = 0;
    for (title, input, result) in results {
        match result {
            Ok((scope, true)) => {
                created += 1;
                assert_eq!(scope, input.scope);
            }
            Err(StorageError::InvalidInput | StorageError::Busy) => {
                // Busy is permitted by the finite SQLite timeout. The winner
                // has joined before this deterministic retry of the loser.
                assert_eq!(
                    store
                        .create_workspace_exact(&title, input.clone())
                        .unwrap_err(),
                    StorageError::InvalidInput
                );
                assert_eq!(
                    store.load_seed(&input.scope).unwrap_err(),
                    StorageError::NotFound
                );
            }
            other => panic!("Unexpected final-slot result: {other:?}"),
        }
    }
    assert_eq!(created, 1);
    assert_eq!(store.stories().unwrap().len(), 256);
    assert_eq!(
        store
            .create_workspace_exact("Existing 0", kept.clone())
            .unwrap(),
        (kept.scope.clone(), false)
    );
    assert_eq!(
        store
            .create_workspace_exact("Changed title", kept.clone())
            .unwrap_err(),
        StorageError::DuplicateStory
    );
    assert_eq!(archive(&mut store, &kept.scope.story), before);
    let extra = seed("after-cap");
    assert_eq!(
        store
            .create_workspace_exact("Extra", extra.clone())
            .unwrap_err(),
        StorageError::InvalidInput
    );
    assert_eq!(
        store.load_seed(&extra.scope).unwrap_err(),
        StorageError::NotFound
    );
}

#[test]
fn concurrent_identical_calls_have_one_created_result_and_one_durable_story() {
    let temp = Temp::new();
    let mut store = temp.open();
    let input = seed("same-creation-id");
    let results = race(
        temp.open(),
        temp.open(),
        [
            ("Same original title".into(), input.clone()),
            ("Same original title".into(), input.clone()),
        ],
    );
    let mut created = 0;
    for (title, input, result) in results {
        let outcome = match result {
            Ok(outcome) => outcome,
            Err(StorageError::Busy) => store.create_workspace_exact(&title, input.clone()).unwrap(),
            other => panic!("Unexpected identical creation result: {other:?}"),
        };
        if outcome.1 {
            created += 1;
        }
        assert_eq!(outcome.0, input.scope);
    }
    assert_eq!(created, 1);
    assert_eq!(store.stories().unwrap().len(), 1);
    assert_eq!(store.load_seed(&input.scope).unwrap(), input);
}

#[test]
fn concurrent_conflicting_calls_keep_only_the_winning_original_seed_and_title() {
    let temp = Temp::new();
    let mut store = temp.open();
    let first = seed("conflicting-creation-id");
    let mut second = first.clone();
    second.actors.get_mut("player").unwrap().name = "Other starting name".into();
    let results = race(
        temp.open(),
        temp.open(),
        [
            ("First title".into(), first),
            ("Second title".into(), second),
        ],
    );
    let mut winner = None;
    let mut loser = None;
    for (title, input, result) in results {
        match result {
            Ok((scope, true)) => {
                assert_eq!(scope, input.scope);
                assert!(winner.replace((title, input)).is_none());
            }
            Err(StorageError::DuplicateStory | StorageError::Busy) => {
                assert!(loser.replace((title, input)).is_none());
            }
            other => panic!("Unexpected conflicting creation result: {other:?}"),
        }
    }
    let (title, input) = winner.unwrap();
    let (wrong_title, wrong_seed) = loser.unwrap();
    advance(&mut store, &input.scope, "winner-accepted");
    let before = archive(&mut store, &input.scope.story);
    assert_eq!(
        store
            .create_workspace_exact(&wrong_title, wrong_seed)
            .unwrap_err(),
        StorageError::DuplicateStory
    );
    assert_eq!(
        store.create_workspace_exact(&title, input.clone()).unwrap(),
        (input.scope.clone(), false)
    );
    assert_eq!(store.load_seed(&input.scope).unwrap(), input);
    assert_eq!(archive(&mut store, &input.scope.story), before);
    let catalog = store.stories().unwrap();
    assert_eq!(catalog.len(), 1);
    assert_eq!(catalog[0].title, title);
}

#[test]
fn busy_owner_refuses_without_partial_insert_and_release_allows_exact_retry() {
    let temp = Temp::new();
    let mut store = temp.open();
    let kept = seed("kept-before-busy");
    store.create_workspace_exact("Keep", kept.clone()).unwrap();
    advance(&mut store, &kept.scope, "kept-before-lock");
    let before = archive(&mut store, &kept.scope.story);
    let mut blocker = Connection::open(temp.database()).unwrap();
    let lock = blocker
        .transaction_with_behavior(TransactionBehavior::Immediate)
        .unwrap();
    let input = seed("new-after-lock");
    assert_eq!(
        store
            .create_workspace_exact("New", input.clone())
            .unwrap_err(),
        StorageError::Busy
    );
    drop(lock);
    assert_eq!(
        store.load_seed(&input.scope).unwrap_err(),
        StorageError::NotFound
    );
    assert_eq!(archive(&mut store, &kept.scope.story), before);
    assert_eq!(
        store.create_workspace_exact("New", input.clone()).unwrap(),
        (input.scope.clone(), true)
    );
    assert!(!store.create_workspace_exact("New", input).unwrap().1);
}

#[test]
fn deliberately_corrupt_persisted_seed_refuses_integrity_without_repair_or_replacement() {
    // Negative invalid-DB adversary only: SQL never creates an accepted seed or
    // receipt. Every positive story/accepted turn is first made by typed APIs.
    for variant in 0..4 {
        let temp = Temp::new();
        let mut store = temp.open();
        let input = seed("corrupt-original-seed");
        store
            .create_workspace_exact("Original", input.clone())
            .unwrap();
        advance(&mut store, &input.scope, "original-accepted");
        let raw = Connection::open(temp.database()).unwrap();
        let mut invalid = serde_json::to_value(&input).unwrap();
        match variant {
            0 => invalid = serde_json::json!({}),
            1 => invalid["version"] = serde_json::json!(2),
            2 => invalid["scope"]["story"] = serde_json::json!("different-story"),
            3 => invalid["scope"]["branch"] = serde_json::json!("different-root"),
            _ => unreachable!(),
        }
        let invalid_json = serde_json::to_string(&invalid).unwrap();
        raw.execute(
            "UPDATE stories SET seed_json=?1 WHERE story_id=?2",
            (&invalid_json, &input.scope.story),
        )
        .unwrap();
        let invalid_baseline: (String, String) = raw.query_row(
            "SELECT seed_json,(SELECT response_json FROM turns WHERE story_id=?1 AND turn_id='original-accepted') FROM stories WHERE story_id=?1",
            [&input.scope.story], |row| Ok((row.get(0)?, row.get(1)?)),
        ).unwrap();
        assert_eq!(
            store
                .create_workspace_exact("Original", input.clone())
                .unwrap_err(),
            StorageError::Integrity
        );
        let after: (String, String) = raw.query_row(
            "SELECT seed_json,(SELECT response_json FROM turns WHERE story_id=?1 AND turn_id='original-accepted') FROM stories WHERE story_id=?1",
            [&input.scope.story], |row| Ok((row.get(0)?, row.get(1)?)),
        ).unwrap();
        assert_eq!(after, invalid_baseline);
        assert_eq!(after.0, invalid_json);
    }
}
