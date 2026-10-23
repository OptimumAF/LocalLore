// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent adversarial synthetic fixtures; direct SQL never belongs to application code.
use locallore::{contracts::*, engine::Engine};
use locallore_storage::{Store, TurnError, TurnPhase};
use rusqlite::Connection;
use std::{
    path::PathBuf,
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT: AtomicU64 = AtomicU64::new(0);
struct Fixture(PathBuf);
impl Fixture {
    fn new() -> Self {
        let path = std::env::temp_dir().join(format!(
            "locallore-review-{}-{}-{}",
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
        let connection = Connection::open(self.path()).unwrap();
        // Corruption fixtures intentionally bypass FK validation to exercise replay's own checks.
        connection
            .pragma_update(None, "foreign_keys", false)
            .unwrap();
        connection
    }
    fn seed(&self) -> (Store, Engine) {
        let seed: Seed =
            serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
        let mut store = self.open();
        store
            .create_story("Synthetic review fixture", seed.clone())
            .unwrap();
        (store, Engine::new(seed).unwrap())
    }
}
impl Drop for Fixture {
    fn drop(&mut self) {
        std::fs::remove_dir_all(&self.0).unwrap();
    }
}
fn plan(engine: &Engine, id: &str) -> (Request, Proposal, String) {
    let request = engine.request(
        id,
        Intent::Actions(vec![Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 1,
        }]),
    );
    let proposal = Engine::proposal(&request).unwrap();
    let text = engine
        .preview(&request, &proposal)
        .unwrap()
        .narration()
        .to_owned();
    (request, proposal, text)
}
fn committed(fixture: &Fixture) -> (Store, Engine, Request, Receipt) {
    let (mut store, engine) = fixture.seed();
    let (request, proposal, text) = plan(&engine, "gift");
    store.begin_turn(&request).unwrap();
    let receipt = store.commit_turn(&request, &proposal, &text).unwrap();
    (store, engine, request, receipt)
}

#[test]
fn canonical_table_tampering_is_refused_without_repairing_evidence() {
    let cases = [
        "UPDATE turns SET response_json=json_set(response_json,'$.events[0].outcome.quantity',99)",
        "UPDATE turns SET response_json=json_set(response_json,'$.events[0].witnesses',json('[\"player\",\"mira\",\"sable\"]'))",
        "UPDATE turns SET response_json=json_set(response_json,'$.narration','private synthetic forgery')",
        "UPDATE turns SET response_json=json_set(response_json,'$.unknown','private synthetic forgery')",
        "UPDATE accepted_events SET envelope_json=json_set(envelope_json,'$.sequence',2)",
        "UPDATE accepted_events SET envelope_json=json_set(envelope_json,'$.outcome.quantity',99)",
        "UPDATE accepted_events SET envelope_json=json_set(envelope_json,'$.unknown','forgery')",
        "INSERT INTO event_witnesses(story_id,branch_id,sequence,observer_id) SELECT story_id,branch_id,sequence,'sable' FROM accepted_events",
        "INSERT INTO event_witnesses(story_id,branch_id,sequence,observer_id) SELECT story_id,branch_id,999,'sable' FROM accepted_events",
        "UPDATE branches SET head_revision=0",
        "UPDATE turns SET request_json=json_set(request_json,'$.intent.actions[0].give.quantity',2)",
        "DELETE FROM accepted_events",
    ];
    for sql in cases {
        let fixture = Fixture::new();
        let (mut store, _, request, _) = committed(&fixture);
        let db = fixture.sql();
        db.execute(sql, []).unwrap();
        let old: String = db
            .query_row("SELECT projection_json FROM branch_projections", [], |r| {
                r.get(0)
            })
            .unwrap();
        let error = match store.resume(&request.scope) {
            Err(error) => error,
            Ok(_) => panic!("accepted corrupted canonical rows: {sql}"),
        };
        assert_eq!(error, TurnError::Integrity, "{sql}");
        assert_eq!(format!("{error:?}"), "Integrity");
        assert!(
            matches!(
                store.rebuild_projection(&request.scope),
                Err(TurnError::Integrity)
            ),
            "{sql}"
        );
        let after: String = db
            .query_row("SELECT projection_json FROM branch_projections", [], |r| {
                r.get(0)
            })
            .unwrap();
        assert_eq!(after, old);
    }
}

#[test]
fn duplicate_normalized_event_fields_fail_closed() {
    let fixture = Fixture::new();
    let (mut store, _, request, receipt) = committed(&fixture);
    let valid = serde_json::to_string(&receipt.events()[0]).unwrap();
    // A first-wins consumer sees a forged sequence; a last-wins consumer sees the valid one.
    let ambiguous = format!("{{\"sequence\":999,{}", &valid[1..]);
    fixture
        .sql()
        .execute("UPDATE accepted_events SET envelope_json=?1", [ambiguous])
        .unwrap();
    assert!(matches!(
        store.resume(&request.scope),
        Err(TurnError::Integrity)
    ));
}

#[test]
fn every_exact_committed_retry_returns_the_recorded_result() {
    let fixture = Fixture::new();
    let (mut store, _, request, receipt) = committed(&fixture);
    let proposal = Engine::proposal(&request).unwrap();
    assert_eq!(
        store
            .commit_turn(&request, &proposal, "different discarded generation")
            .unwrap(),
        receipt
    );
    // Response retries are resolved by exact request, even if another generation was oversized.
    assert_eq!(
        store
            .commit_turn(&request, &proposal, &"x".repeat(MAX_RECEIPT_BYTES + 1))
            .unwrap(),
        receipt
    );
}

#[test]
fn terminal_statuses_and_retry_payloads_survive_reopen() {
    for cancelled in [true, false] {
        let fixture = Fixture::new();
        let (mut store, engine) = fixture.seed();
        let (request, proposal, text) = plan(&engine, "terminal");
        store.begin_turn(&request).unwrap();
        let expected = if cancelled {
            store.cancel_turn(&request).unwrap().phase
        } else {
            store.fail_turn(&request).unwrap().phase
        };
        drop(store);
        let mut store = fixture.open();
        assert_eq!(store.begin_turn(&request).unwrap().phase, expected);
        assert_eq!(store.cancel_turn(&request).unwrap().phase, expected);
        assert_eq!(store.fail_turn(&request).unwrap().phase, expected);
        assert_eq!(
            store.commit_turn(&request, &proposal, &text),
            Err(TurnError::Terminal)
        );
        let mut changed = request.clone();
        changed.intent = Intent::Actions(vec![Command::Wait { ticks: 1 }]);
        assert!(matches!(
            store.begin_turn(&changed),
            Err(TurnError::RetryMismatch)
        ));
        assert!(matches!(
            store.turn_status(&changed),
            Err(TurnError::RetryMismatch)
        ));
        assert!(matches!(
            store.cancel_turn(&changed),
            Err(TurnError::RetryMismatch)
        ));
        assert!(matches!(
            store.fail_turn(&changed),
            Err(TurnError::RetryMismatch)
        ));
        assert!(matches!(
            store.commit_turn(&changed, &proposal, &text),
            Err(TurnError::RetryMismatch)
        ));
        assert!(store.drafts(&request.scope).unwrap().is_empty());
        assert_eq!(
            store
                .resume(&request.scope)
                .unwrap()
                .engine
                .canonical_bytes(),
            engine.canonical_bytes()
        );
    }
}

#[test]
fn projection_repair_does_not_change_receipts_or_epistemic_state() {
    for mutation in [
        "DELETE FROM branch_projections",
        "UPDATE branch_projections SET projection_json='{}'",
        "UPDATE branch_projections SET revision=0",
    ] {
        let fixture = Fixture::new();
        let (mut store, _, request, receipt) = committed(&fixture);
        let before = store.resume(&request.scope).unwrap().engine;
        fixture.sql().execute(mutation, []).unwrap();
        drop(store);
        let mut store = fixture.open();
        let restored = store.resume(&request.scope).unwrap();
        assert!(restored.projection_needs_rebuild);
        assert_eq!(restored.engine.canonical_bytes(), before.canonical_bytes());
        let repaired = store.rebuild_projection(&request.scope).unwrap();
        assert!(!repaired.projection_needs_rebuild);
        assert_eq!(repaired.engine.receipts(), &[receipt]);
        for observer in ["player", "mira", "sable"] {
            assert_eq!(
                repaired
                    .engine
                    .character_context(observer, &request.scope, before.revision())
                    .unwrap(),
                before
                    .character_context(observer, &request.scope, before.revision())
                    .unwrap()
            );
        }
        assert!(
            !store
                .resume(&request.scope)
                .unwrap()
                .projection_needs_rebuild
        );
    }
}

#[test]
fn request_and_response_budgets_leave_no_partial_intent_or_canon() {
    let fixture = Fixture::new();
    let (mut store, engine) = fixture.seed();
    let mut large = engine.request(
        "too-large",
        Intent::Dialogue {
            text: "x".repeat(MAX_PROPOSAL_BYTES + 1),
            audience: ["mira".into()].into_iter().collect(),
        },
    );
    assert!(matches!(
        store.begin_turn(&large),
        Err(TurnError::Engine(Error::TooLarge))
    ));
    assert!(matches!(
        store.turn_status(&large),
        Err(TurnError::UnknownTurn)
    ));
    large.intent = Intent::Actions(vec![Command::Wait { ticks: 1 }]);
    assert_eq!(store.begin_turn(&large).unwrap().phase, TurnPhase::Draft);
    let proposal = Engine::proposal(&large).unwrap();
    assert_eq!(
        store.commit_turn(&large, &proposal, &"x".repeat(MAX_RECEIPT_BYTES + 1)),
        Err(TurnError::TooLarge)
    );
    assert_eq!(store.turn_status(&large).unwrap().phase, TurnPhase::Draft);
    assert_eq!(store.resume(&large.scope).unwrap().engine.revision(), 0);
}

#[test]
fn stored_intent_count_is_bounded_including_terminal_rows() {
    let fixture = Fixture::new();
    let (mut store, engine) = fixture.seed();
    let db = fixture.sql();
    let request = engine.request(
        "count-limit",
        Intent::Actions(vec![Command::Wait { ticks: 1 }]),
    );
    let input = serde_json::to_string(&request).unwrap();
    db.execute("WITH RECURSIVE ids(n) AS (SELECT 1 UNION ALL SELECT n+1 FROM ids WHERE n<?1) INSERT INTO turns SELECT ?2,?3,'terminal-'||n,0,'cancelled',json_set(?4,'$.turn','terminal-'||n),NULL FROM ids", (MAX_HISTORY_RECEIPTS as i64, &request.scope.story, &request.scope.branch, input)).unwrap();
    assert_eq!(store.resume(&request.scope).unwrap().engine.revision(), 0);
    assert!(matches!(
        store.begin_turn(&request),
        Err(TurnError::TooLarge)
    ));
    assert_eq!(
        db.query_row::<i64, _, _>("SELECT count(*) FROM turns", [], |r| r.get(0))
            .unwrap(),
        MAX_HISTORY_RECEIPTS as i64
    );
}

#[test]
fn draft_enumeration_cannot_substitute_another_rows_embedded_request() {
    let fixture = Fixture::new();
    let (mut store, engine) = fixture.seed();
    let (first, _, _) = plan(&engine, "first");
    let (second, _, _) = plan(&engine, "second");
    store.begin_turn(&first).unwrap();
    store.begin_turn(&second).unwrap();
    fixture
        .sql()
        .execute(
            "UPDATE turns SET request_json=?1 WHERE turn_id='first'",
            [serde_json::to_string(&second).unwrap()],
        )
        .unwrap();
    assert!(matches!(
        store.drafts(&first.scope),
        Err(TurnError::Integrity)
    ));
}

#[test]
fn replay_byte_budget_is_checked_before_loading_individual_requests() {
    let fixture = Fixture::new();
    let (mut store, engine) = fixture.seed();
    let request = engine.request(
        "history-bytes",
        Intent::Dialogue {
            text: "x".repeat(24000),
            audience: ["mira".into()].into_iter().collect(),
        },
    );
    let input = serde_json::to_string(&request).unwrap();
    assert!(input.len() < 24576);
    let rows = MAX_HISTORY_BYTES / input.len() + 1;
    assert!(rows < MAX_HISTORY_RECEIPTS);
    fixture.sql().execute("WITH RECURSIVE ids(n) AS (SELECT 1 UNION ALL SELECT n+1 FROM ids WHERE n<?1) INSERT INTO turns SELECT ?2,?3,'terminal-'||n,0,'failed',json_set(?4,'$.turn','terminal-'||n),NULL FROM ids", (rows as i64, &request.scope.story, &request.scope.branch, input)).unwrap();
    assert!(matches!(
        store.resume(&request.scope),
        Err(TurnError::TooLarge)
    ));
    assert!(matches!(
        store.drafts(&request.scope),
        Err(TurnError::TooLarge)
    ));
}
