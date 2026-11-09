// Runner supplies D: TEMP/TMP/TMPDIR. Unique synthetic DBs are retained, never deleted.
// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
use locallore::{contracts::*, engine::Engine};
use locallore_storage::{StorageError, Store, TurnError, TurnPhase};
use rusqlite::{types::Value, Connection};
use std::{
    path::PathBuf,
    sync::atomic::{AtomicU64, Ordering},
    time::Duration,
};

static NEXT: AtomicU64 = AtomicU64::new(0);

fn retained_database() -> PathBuf {
    let directory = std::env::temp_dir().join(format!(
        "locallore-m10-epistemic-commit-busy-{}-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos(),
        NEXT.fetch_add(1, Ordering::Relaxed)
    ));
    std::fs::create_dir(&directory).unwrap();
    directory.join("synthetic.sqlite")
}

// Every persisted user table, including complete draft/cancelled rows, all
// normalized events/witnesses, head and projection. No row-hash shortcut.
fn normalized_rows(db: &Connection) -> Vec<(String, Vec<Vec<Value>>)> {
    let names = {
        let mut query = db.prepare("SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").unwrap();
        let result = query
            .query_map([], |row| row.get::<_, String>(0))
            .unwrap()
            .collect::<Result<Vec<_>, _>>()
            .unwrap();
        result
    };
    names
        .into_iter()
        .map(|name| {
            let escaped = name.replace('"', "\"\"");
            let mut query = db.prepare(&format!("SELECT * FROM \"{escaped}\"")).unwrap();
            let columns = query.column_count();
            let mut values: Vec<Vec<Value>> = query
                .query_map([], |row| (0..columns).map(|index| row.get(index)).collect())
                .unwrap()
                .collect::<Result<_, _>>()
                .unwrap();
            values.sort_by_key(|row| format!("{row:?}"));
            (name, values)
        })
        .collect()
}

fn contexts(engine: &Engine) -> Vec<serde_json::Value> {
    ["player", "mira", "oren", "sable"]
        .into_iter()
        .map(|observer| {
            serde_json::to_value(
                engine
                    .character_context(observer, engine.scope(), engine.revision())
                    .unwrap(),
            )
            .unwrap()
        })
        .collect()
}

fn assert_fixture_bounded(path: &std::path::Path) {
    let bytes: u64 = std::fs::read_dir(path.parent().unwrap())
        .unwrap()
        .map(|entry| entry.unwrap().metadata().unwrap().len())
        .sum();
    assert!(
        bytes < 2 * 1024 * 1024,
        "Retained synthetic fixture exceeded its 2 MiB budget"
    );
}

#[test]
fn final_commit_busy_rolls_back_composed_knowledge_and_mechanics_then_exact_retry_spends_once() {
    let path = retained_database();
    let seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    let initial = Engine::new(seed.clone()).unwrap();
    let scope = seed.scope.clone();
    let mut store = Store::open(&path, None).unwrap();
    store
        .create_story("M10 synthetic epistemic commit rollback", seed)
        .unwrap();
    let commands = vec![
        Command::Say {
            text: "This claim must survive only an accepted transaction.".into(),
            audience: ["mira".into()].into(),
        },
        Command::Believe { claim_event: 1 },
        Command::Move {
            to: "dry-well".into(),
        },
        Command::Discover {
            fact: "beacon-mark".into(),
        },
        Command::Wait { ticks: 1 },
        Command::Move { to: "quay".into() },
        Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 1,
        },
    ];
    let request = initial.request("composed-commit-busy", Intent::Actions(commands.clone()));
    let proposal = Engine::proposal(&request).unwrap();
    let preview = initial.preview(&request, &proposal).unwrap();
    assert_eq!(preview.events().len(), 7);
    let narration = preview.narration().to_owned();

    // Store intent admission is durable. Its cancellation key is terminal,
    // unlike the engine's unpersisted rejected request in the M10 engine test.
    let cancelled = initial.request("cancelled-composed", Intent::Actions(commands));
    let cancelled_proposal = Engine::proposal(&cancelled).unwrap();
    store.begin_turn(&cancelled).unwrap();
    assert_eq!(
        store.cancel_turn(&cancelled).unwrap().phase,
        TurnPhase::Cancelled
    );
    assert_eq!(store.begin_turn(&request).unwrap().phase, TurnPhase::Draft);
    let before = initial.canonical_bytes();
    let before_contexts = contexts(&initial);
    let inspection = Connection::open(&path).unwrap();
    let rows_before = normalized_rows(&inspection);
    drop(inspection);
    assert_fixture_bounded(&path);

    let reader = Connection::open(&path).unwrap();
    let mode: String = reader
        .pragma_query_value(None, "journal_mode", |row| row.get(0))
        .unwrap();
    assert_eq!(
        mode.to_ascii_lowercase(),
        "delete",
        "This oracle requires the existing rollback journal; it does not switch modes"
    );
    reader.execute_batch("BEGIN DEFERRED").unwrap();
    // Actually step a table read. Merely executing BEGIN has not acquired SHARED.
    let read_head: i64 = reader
        .query_row(
            "SELECT head_revision FROM branches WHERE story_id=?1 AND branch_id=?2",
            (&scope.story, &scope.branch),
            |row| row.get(0),
        )
        .unwrap();
    assert_eq!(read_head, 0);
    assert!(!reader.is_autocommit());
    {
        // The held SHARED reader admits RESERVED and real DML. This proves the
        // fixture is not an exclusive-writer lock that refuses Store at BEGIN.
        let probe = Connection::open(&path).unwrap();
        probe.busy_timeout(Duration::ZERO).unwrap();
        probe.execute_batch("BEGIN IMMEDIATE").unwrap();
        assert_eq!(probe.execute("UPDATE branches SET head_revision=head_revision WHERE story_id=?1 AND branch_id=?2",
            (&scope.story, &scope.branch)).unwrap(), 1);
        probe.execute_batch("ROLLBACK").unwrap();
    }
    // Source commit_output writes events, witnesses, projection, draft result
    // and head before tx.commit(). A SHARED reader prevents its EXCLUSIVE
    // upgrade at final COMMIT in this small DELETE-journal transaction.
    let failure = store.commit_turn(&request, &proposal, &narration);
    assert_eq!(failure, Err(TurnError::Storage(StorageError::Busy)));
    reader.execute_batch("ROLLBACK").unwrap();
    drop(reader);

    // The SAME Store remains usable after transaction-drop rollback; no reopen
    // is allowed to hide a poisoned connection or clean up partial work first.
    assert_eq!(store.turn_status(&request).unwrap().phase, TurnPhase::Draft);
    let unchanged = store.resume(&scope).unwrap();
    assert!(!unchanged.projection_needs_rebuild);
    assert_eq!(unchanged.engine.canonical_bytes(), before);
    assert_eq!(unchanged.engine.revision(), 0);
    assert!(unchanged.engine.receipts().is_empty());
    assert_eq!(contexts(&unchanged.engine), before_contexts);
    let inspection = Connection::open(&path).unwrap();
    assert_eq!(normalized_rows(&inspection), rows_before);
    drop(inspection);
    drop(store);

    // Reopen BEFORE retry as well: no normalized prefix, claim source, inventory
    // transfer, relationship increment or committed result can have leaked.
    let mut store = Store::open(&path, None).unwrap();
    let reopened = store.resume(&scope).unwrap();
    assert!(!reopened.projection_needs_rebuild);
    assert_eq!(reopened.engine.canonical_bytes(), before);
    assert_eq!(contexts(&reopened.engine), before_contexts);
    assert_eq!(store.begin_turn(&request).unwrap().phase, TurnPhase::Draft);
    assert_eq!(
        store.begin_turn(&cancelled).unwrap().phase,
        TurnPhase::Cancelled
    );
    assert_eq!(
        store.commit_turn(&cancelled, &cancelled_proposal, &narration),
        Err(TurnError::Terminal)
    );
    let mut changed = request.clone();
    changed.intent = Intent::Actions(vec![Command::Wait { ticks: 1 }]);
    assert!(matches!(
        store.begin_turn(&changed),
        Err(TurnError::RetryMismatch)
    ));
    assert_eq!(
        store.commit_turn(&changed, &proposal, &narration),
        Err(TurnError::RetryMismatch)
    );
    let mut changed_cancelled = cancelled.clone();
    changed_cancelled.intent = changed.intent.clone();
    assert!(matches!(
        store.begin_turn(&changed_cancelled),
        Err(TurnError::RetryMismatch)
    ));
    let inspection = Connection::open(&path).unwrap();
    assert_eq!(normalized_rows(&inspection), rows_before);
    drop(inspection);

    let receipt = store.commit_turn(&request, &proposal, &narration).unwrap();
    assert_eq!(receipt, preview);
    let accepted = store.resume(&scope).unwrap();
    assert!(!accepted.projection_needs_rebuild);
    assert_eq!(accepted.engine.revision(), 7);
    assert_eq!(accepted.engine.canonical_record_count(), 1);
    assert_eq!(accepted.engine.state().claims.len(), 1);
    assert_eq!(accepted.engine.state().claims[0].source, 1);
    let new_beliefs = accepted
        .engine
        .state()
        .beliefs
        .iter()
        .filter(|belief| belief.source_claim == Some(1))
        .collect::<Vec<_>>();
    assert_eq!(new_beliefs.len(), 1);
    assert_eq!(new_beliefs[0].source, Evidence::Event(2));
    assert_eq!(accepted.engine.state().story_time, 101);
    assert_eq!(accepted.engine.state().items["potion"].owner, "mira");
    assert_eq!(accepted.engine.state().item_transfers["potion"].sequence, 7);
    assert_eq!(accepted.engine.state().relationships[0].obligation, 1);
    let final_canon = accepted.engine.canonical_bytes();
    let final_contexts = contexts(&accepted.engine);
    let inspection = Connection::open(&path).unwrap();
    let event_count: i64 = inspection
        .query_row("SELECT count(*) FROM accepted_events", [], |row| row.get(0))
        .unwrap();
    let witness_count: i64 = inspection
        .query_row("SELECT count(*) FROM event_witnesses", [], |row| row.get(0))
        .unwrap();
    assert_eq!(event_count, 7);
    assert_eq!(witness_count, 9);
    let committed_rows = normalized_rows(&inspection);
    drop(inspection);
    drop(store);

    let mut store = Store::open(&path, None).unwrap();
    assert_eq!(
        store.begin_turn(&request).unwrap().receipt,
        Some(receipt.clone())
    );
    assert_eq!(
        store.commit_turn(&request, &proposal, &narration).unwrap(),
        receipt
    );
    assert_eq!(
        store.turn_status(&request).unwrap().phase,
        TurnPhase::Committed
    );
    assert_eq!(
        store.begin_turn(&cancelled).unwrap().phase,
        TurnPhase::Cancelled
    );
    assert_eq!(
        store.commit_turn(&cancelled, &cancelled_proposal, &narration),
        Err(TurnError::Terminal)
    );
    assert!(matches!(
        store.begin_turn(&changed),
        Err(TurnError::RetryMismatch)
    ));
    assert_eq!(
        store.commit_turn(&changed, &proposal, &narration),
        Err(TurnError::RetryMismatch)
    );
    let exact = store.resume(&scope).unwrap();
    assert!(!exact.projection_needs_rebuild);
    assert_eq!(exact.engine.canonical_bytes(), final_canon);
    assert_eq!(contexts(&exact.engine), final_contexts);
    assert_eq!(exact.engine.receipts(), &[receipt]);
    let inspection = Connection::open(&path).unwrap();
    assert_eq!(normalized_rows(&inspection), committed_rows);
    drop(inspection);
    drop(store);
    assert_fixture_bounded(&path);
    // Deliberately no cleanup: Root's retained fixture manifest owns preservation.
}
