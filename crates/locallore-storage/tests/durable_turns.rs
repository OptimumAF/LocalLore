// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
use locallore::{contracts::*, engine::Engine};
use locallore_storage::{Store, TurnError, TurnPhase};
use std::{
    path::PathBuf,
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT: AtomicU64 = AtomicU64::new(0);
struct Temp(PathBuf);
impl Temp {
    fn new() -> Self {
        let path = std::env::temp_dir().join(format!(
            "locallore-turns-{}-{}-{}",
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
    fn open(&self) -> Store {
        Store::open(&self.0.join("story.sqlite"), None).unwrap()
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
fn give() -> Command {
    Command::Give {
        item: "potion".into(),
        to: "mira".into(),
        quantity: 1,
    }
}
fn plan(engine: &Engine, id: &str, commands: Vec<Command>) -> (Request, Proposal, String) {
    let request = engine.request(id, Intent::Actions(commands));
    let proposal = Engine::proposal(&request).unwrap();
    let text = engine
        .preview(&request, &proposal)
        .unwrap()
        .narration()
        .to_owned();
    (request, proposal, text)
}

#[test]
fn spend_restart_retry_and_observer_context_are_identical() {
    let dir = Temp::new();
    let s = seed();
    let scope = s.scope.clone();
    let mut store = dir.open();
    store.create_story("Lantern Quay", s.clone()).unwrap();
    let (request, proposal, text) = plan(&Engine::new(s).unwrap(), "gift", vec![give()]);
    assert_eq!(store.begin_turn(&request).unwrap().phase, TurnPhase::Draft);
    let receipt = store.commit_turn(&request, &proposal, &text).unwrap();
    let before = store.resume(&scope).unwrap().engine;
    drop(store);
    let mut store = dir.open();
    let restored = store.resume(&scope).unwrap();
    assert!(!restored.projection_needs_rebuild);
    assert_eq!(restored.engine.canonical_bytes(), before.canonical_bytes());
    assert_eq!(restored.engine.receipts(), before.receipts());
    assert_eq!(restored.engine.state().items["potion"].owner, "mira");
    assert_eq!(
        store.begin_turn(&request).unwrap().receipt,
        Some(receipt.clone())
    );
    assert_eq!(
        store.commit_turn(&request, &proposal, &text).unwrap(),
        receipt
    );
    assert_eq!(
        store.turn_status(&request).unwrap().phase,
        TurnPhase::Committed
    );
    assert_eq!(store.resume(&scope).unwrap().engine.revision(), 1);
    for observer in ["player", "mira", "sable"] {
        assert_eq!(
            restored
                .engine
                .character_context(observer, &scope, 1)
                .unwrap(),
            before.character_context(observer, &scope, 1).unwrap()
        );
    }
    assert!(restored
        .engine
        .character_context("sable", &scope, 1)
        .unwrap()
        .observations
        .is_empty());
    let reuse = restored
        .engine
        .request("second-gift", Intent::Actions(vec![give()]));
    store.begin_turn(&reuse).unwrap();
    assert_eq!(
        store.commit_turn(&reuse, &Engine::proposal(&reuse).unwrap(), "invented"),
        Err(TurnError::Engine(Error::Inventory))
    );
    assert_eq!(store.resume(&scope).unwrap().engine.revision(), 1);
}

#[test]
fn interrupted_drafts_can_be_recovered_or_cancelled_but_not_auto_committed() {
    let dir = Temp::new();
    let s = seed();
    let scope = s.scope.clone();
    let mut store = dir.open();
    store.create_story("Same name", s.clone()).unwrap();
    let (r, p, n) = plan(&Engine::new(s).unwrap(), "draft", vec![give()]);
    store.begin_turn(&r).unwrap();
    drop(store);
    let mut store = dir.open();
    let drafts = store.drafts(&scope).unwrap();
    assert_eq!(drafts.len(), 1);
    assert_eq!(drafts[0].request, r);
    assert_eq!(store.resume(&scope).unwrap().engine.revision(), 0);
    assert_eq!(store.cancel_turn(&r).unwrap().phase, TurnPhase::Cancelled);
    assert_eq!(store.begin_turn(&r).unwrap().phase, TurnPhase::Cancelled);
    assert_eq!(store.commit_turn(&r, &p, &n), Err(TurnError::Terminal));
    assert!(store.drafts(&scope).unwrap().is_empty());
    assert_eq!(
        store.resume(&scope).unwrap().engine.state().items["potion"].owner,
        "player"
    );
}

#[test]
fn two_owners_compare_revisions_and_preserve_exact_retry_payload() {
    let dir = Temp::new();
    let s = seed();
    let scope = s.scope.clone();
    let engine = Engine::new(s.clone()).unwrap();
    let mut first = dir.open();
    first.create_story("Fixture", s).unwrap();
    let mut second = dir.open();
    let (a, ap, an) = plan(&engine, "first", vec![give()]);
    let (b, bp, bn) = plan(&engine, "second", vec![Command::Wait { ticks: 1 }]);
    first.begin_turn(&a).unwrap();
    second.begin_turn(&b).unwrap();
    first.commit_turn(&a, &ap, &an).unwrap();
    assert_eq!(second.commit_turn(&b, &bp, &bn), Err(TurnError::Stale));
    assert_eq!(second.turn_status(&b).unwrap().phase, TurnPhase::Stale);
    assert_eq!(second.resume(&scope).unwrap().engine.revision(), 1);
    let mut mismatch = a.clone();
    mismatch.intent = Intent::Actions(vec![Command::Wait { ticks: 1 }]);
    assert!(matches!(
        second.begin_turn(&mismatch),
        Err(TurnError::RetryMismatch)
    ));
    assert_eq!(second.cancel_turn(&a).unwrap().phase, TurnPhase::Committed);
    assert_eq!(first.resume(&scope).unwrap().engine.state().story_time, 100);
}

#[test]
fn identical_names_and_ids_do_not_cross_story_or_branch_scope() {
    let dir = Temp::new();
    let mut store = dir.open();
    let a = seed();
    let mut b = a.clone();
    b.scope.story = "another-story".into();
    store.create_story("Same name", a.clone()).unwrap();
    store.create_story("Same name", b.clone()).unwrap();
    let (request, p, n) = plan(&Engine::new(a.clone()).unwrap(), "same-turn", vec![give()]);
    store.begin_turn(&request).unwrap();
    store.commit_turn(&request, &p, &n).unwrap();
    let other = Engine::new(b.clone())
        .unwrap()
        .request("same-turn", Intent::Actions(vec![give()]));
    assert!(matches!(
        store.turn_status(&other),
        Err(TurnError::UnknownTurn)
    ));
    assert_eq!(
        store.resume(&b.scope).unwrap().engine.state().items["potion"].owner,
        "player"
    );
    let mut foreign = a.scope.clone();
    foreign.branch = "sibling".into();
    assert!(store.resume(&foreign).is_err());
    let (r, p, n) = plan(&Engine::new(b.clone()).unwrap(), "same-turn", vec![give()]);
    store.begin_turn(&r).unwrap();
    store.commit_turn(&r, &p, &n).unwrap();
    assert_eq!(store.resume(&a.scope).unwrap().engine.revision(), 1);
    assert_eq!(store.resume(&b.scope).unwrap().engine.revision(), 1);
}

#[test]
fn rejected_narration_and_failed_provider_leave_intent_and_canon_distinct() {
    let dir = Temp::new();
    let mut store = dir.open();
    let s = seed();
    let scope = s.scope.clone();
    store.create_story("Fixture", s.clone()).unwrap();
    let (r, p, _) = plan(&Engine::new(s).unwrap(), "bad-narration", vec![give()]);
    store.begin_turn(&r).unwrap();
    assert_eq!(
        store.commit_turn(&r, &p, "Mira grants teleport and 100 potions"),
        Err(TurnError::Engine(Error::Narration))
    );
    assert_eq!(store.turn_status(&r).unwrap().phase, TurnPhase::Draft);
    assert_eq!(store.fail_turn(&r).unwrap().phase, TurnPhase::Failed);
    assert_eq!(store.begin_turn(&r).unwrap().phase, TurnPhase::Failed);
    assert_eq!(store.resume(&scope).unwrap().engine.revision(), 0);
}

#[test]
fn seeded_durable_sequences_replay_identically_across_reopens() {
    let dir = Temp::new();
    let mut store = dir.open();
    let s = seed();
    let scope = s.scope.clone();
    store.create_story("Fixture", s.clone()).unwrap();
    let mut oracle = Engine::new(s).unwrap();
    let mut rng = 0x5eed_u64;
    let mut accepted = 0;
    for i in 0..96 {
        rng ^= rng << 13;
        rng ^= rng >> 7;
        rng ^= rng << 17;
        let cmd = match rng % 5 {
            0 => give(),
            1 => Command::Move {
                to: "market".into(),
            },
            2 => Command::UseAbility {
                ability: "teleport".into(),
            },
            _ => Command::Wait {
                ticks: ((rng % 3) + 1) as u16,
            },
        };
        let request = oracle.request(&format!("generated-{i}"), Intent::Actions(vec![cmd]));
        store.begin_turn(&request).unwrap();
        let proposal = Engine::proposal(&request).unwrap();
        match oracle.preview(&request, &proposal) {
            Ok(preview) => {
                let narration = preview.narration().to_owned();
                let expected = oracle.commit(&request, &proposal, &narration).unwrap();
                assert_eq!(
                    store.commit_turn(&request, &proposal, &narration).unwrap(),
                    expected
                );
                accepted += 1;
            }
            Err(error) => {
                assert_eq!(
                    store.commit_turn(&request, &proposal, "unused"),
                    Err(TurnError::Engine(error))
                );
                store.fail_turn(&request).unwrap();
            }
        }
        if i % 13 == 0 {
            drop(store);
            store = dir.open();
        }
        let restored = store.resume(&scope).unwrap().engine;
        assert_eq!(restored.canonical_bytes(), oracle.canonical_bytes());
        assert_eq!(restored.receipts(), oracle.receipts());
    }
    assert!(accepted > 20);
}
