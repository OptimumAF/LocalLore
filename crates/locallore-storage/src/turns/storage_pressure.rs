// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Real SQLite page pressure, without commit fault hooks or production controls.
use super::*;
use locallore::contracts::{Command, Intent};
use rusqlite::types::Value;
use std::path::PathBuf;
use std::sync::atomic::{AtomicU64, Ordering};

static NEXT_DIRECTORY: AtomicU64 = AtomicU64::new(0);

struct Temp(PathBuf);
impl Temp {
    fn new() -> Self {
        // Android's explicit native runner supplies a fresh synthetic TMPDIR.
        let path = std::env::temp_dir().join(format!(
            "locallore-storage-pressure-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT_DIRECTORY.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&path).unwrap();
        Self(path)
    }
    fn open(&self) -> Store {
        Store::open(&self.0.join("story.sqlite"), None).unwrap()
    }
    fn assert_bounded(&self) {
        let bytes: u64 = std::fs::read_dir(&self.0)
            .unwrap()
            .map(|entry| entry.unwrap().metadata().unwrap().len())
            .sum();
        assert!(
            bytes < 2 * 1024 * 1024,
            "synthetic database exceeded test budget"
        );
    }
}
impl Drop for Temp {
    fn drop(&mut self) {
        std::fs::remove_dir_all(&self.0).unwrap();
    }
}
fn seed() -> Seed {
    serde_json::from_str(include_str!("../../../../fixtures/lantern_quay.json")).unwrap()
}
fn large_gift(engine: &Engine) -> (Request, Proposal, Receipt) {
    let mut commands = vec![Command::Give {
        item: "potion".into(),
        to: "mira".into(),
        quantity: 1,
    }];
    commands.extend((0..7).map(|index| Command::Say {
        text: format!(
            "Synthetic storage-pressure statement {index}: {}",
            "x".repeat(1800)
        ),
        audience: ["mira".into()].into(),
    }));
    let request = engine.request("storage-pressure", Intent::Actions(commands));
    let proposal = Engine::proposal(&request).unwrap();
    let preview = engine.preview(&request, &proposal).unwrap();
    assert_eq!(preview.events().len(), 8);
    (request, proposal, preview)
}

// Every persisted scoped row, including the complete draft, normalized witnesses,
// canonical events, derived cache and head, is compared without hash shortcuts.
fn rows(store: &Store, story: Option<&str>) -> Vec<Vec<Vec<Value>>> {
    [
        "stories",
        "branches",
        "entities",
        "branch_entities",
        "turns",
        "accepted_events",
        "event_witnesses",
        "branch_projections",
    ]
    .iter()
    .map(|table| {
        let filter = if story.is_some() {
            " WHERE story_id=?1"
        } else {
            ""
        };
        let mut query = store
            .connection
            .prepare(&format!("SELECT * FROM {table}{filter} ORDER BY 1,2,3"))
            .unwrap();
        let columns = query.column_count();
        let params: Vec<&str> = story.into_iter().collect();
        query
            .query_map(rusqlite::params_from_iter(params), |row| {
                (0..columns).map(|index| row.get(index)).collect()
            })
            .unwrap()
            .collect::<std::result::Result<Vec<Vec<Value>>, _>>()
            .unwrap()
    })
    .collect()
}
fn clamp_pages(store: &Store) -> i64 {
    let pages: i64 = store
        .connection
        .pragma_query_value(None, "page_count", |r| r.get(0))
        .unwrap();
    let page_size: i64 = store
        .connection
        .pragma_query_value(None, "page_size", |r| r.get(0))
        .unwrap();
    assert!(pages * page_size < 1024 * 1024);
    store
        .connection
        .pragma_update(None, "max_page_count", pages)
        .unwrap();
    assert_eq!(
        store
            .connection
            .pragma_query_value::<i64, _>(None, "max_page_count", |r| r.get(0))
            .unwrap(),
        pages
    );
    pages
}
fn raise_pages(store: &Store, pages: i64) {
    store
        .connection
        .pragma_update(None, "max_page_count", pages + 128)
        .unwrap();
}
fn contexts(engine: &Engine) -> Vec<String> {
    ["player", "mira", "oren", "sable"]
        .iter()
        .map(|observer| {
            serde_json::to_string(
                &engine
                    .character_context(observer, engine.scope(), engine.revision())
                    .unwrap(),
            )
            .unwrap()
        })
        .collect()
}
fn add_other_story(store: &mut Store) -> (Scope, Vec<u8>) {
    let mut other = seed();
    other.scope.story = "independent-pressure-control".into();
    let engine = Engine::new(other.clone()).unwrap();
    store
        .create_story("Independent synthetic control", other)
        .unwrap();
    let request = engine.request(
        "storage-pressure",
        Intent::Actions(vec![Command::Wait { ticks: 1 }]),
    );
    let proposal = Engine::proposal(&request).unwrap();
    let preview = engine.preview(&request, &proposal).unwrap();
    store.begin_turn(&request).unwrap();
    store
        .commit_turn(&request, &proposal, preview.narration())
        .unwrap();
    let scope = engine.scope().clone();
    let canon = store.resume(&scope).unwrap().engine.canonical_bytes();
    (scope, canon)
}

#[test]
fn full_after_insertable_gift_rolls_back_all_rows_then_exact_retry_spends_once() {
    gift_pressure(false);
}

#[test]
fn full_then_reopen_preserves_draft_and_exact_retry_spends_potion_once() {
    gift_pressure(true);
}

fn gift_pressure(reopen_after_full: bool) {
    let directory = Temp::new();
    let mut store = directory.open();
    let initial = seed();
    let scope = initial.scope.clone();
    let engine = Engine::new(initial.clone()).unwrap();
    store
        .create_story("Synthetic pressure fixture", initial)
        .unwrap();
    let (other_scope, other_canon) = add_other_story(&mut store);
    let other_rows = rows(&store, Some(&other_scope.story));
    let (request, proposal, preview) = large_gift(&engine);
    store.begin_turn(&request).unwrap();
    let before = rows(&store, None);
    let before_contexts = contexts(&engine);
    let pages = clamp_pages(&store);

    // Establish that this exact first envelope + witnesses fits under the same
    // page budget. Roll back this proof before the actual owner transaction.
    // The remaining large-turn writes, not an uninsertable first gift, exhaust pages.
    {
        let tx = store.connection.transaction().unwrap();
        let first = &preview.events()[0];
        tx.execute(
            "INSERT INTO accepted_events(story_id,branch_id,sequence,turn_id,event_version,envelope_json) VALUES (?1,?2,?3,?4,1,?5)",
            (
                &scope.story,
                &scope.branch,
                sql_revision(first.sequence()).unwrap(),
                &request.turn,
                serde_json::to_string(first).unwrap(),
            ),
        )
        .unwrap();
        for observer in first.witnesses() {
            tx.execute("INSERT INTO event_witnesses(story_id,branch_id,sequence,observer_id) VALUES (?1,?2,?3,?4)",
                (&scope.story, &scope.branch, sql_revision(first.sequence()).unwrap(), observer)).unwrap();
        }
        assert_eq!(
            tx.query_row::<i64, _, _>(
                "SELECT count(*) FROM accepted_events WHERE story_id=?1",
                [&scope.story],
                |r| r.get(0)
            )
            .unwrap(),
            1
        );
        tx.rollback().unwrap();
    }
    assert_eq!(rows(&store, None), before);
    // Both retries must return real SQLITE_FULL. The reopen variant closes the
    // failed owner before checking recovery or retrying the original draft.
    for attempt in 0..2 {
        assert_eq!(
            store.commit_turn(&request, &proposal, preview.narration()),
            Err(TurnError::Full)
        );
        if reopen_after_full && attempt == 0 {
            drop(store);
            store = directory.open();
            let reopened_cap: i64 = store
                .connection
                .pragma_query_value(None, "max_page_count", |row| row.get(0))
                .unwrap();
            let reopened_pages: i64 = store
                .connection
                .pragma_query_value(None, "page_count", |row| row.get(0))
                .unwrap();
            assert_eq!(reopened_pages, pages);
            assert!(reopened_cap >= reopened_pages);
            // max_page_count is a connection-local test constraint; do not
            // assume a reopened owner inherits it or models a full partition.
            // Reapply it explicitly, then raise this new connection's budget
            // only after another real FULL and all recovery checks below.
            assert_eq!(clamp_pages(&store), pages);
        }
        assert_eq!(rows(&store, None), before);
        let resumed = store.resume(&scope).unwrap();
        assert!(!resumed.projection_needs_rebuild);
        assert_eq!(resumed.engine.canonical_bytes(), engine.canonical_bytes());
        assert_eq!(contexts(&resumed.engine), before_contexts);
        assert_eq!(resumed.engine.state().items["potion"].owner, "player");
        assert_eq!(resumed.engine.state().items["potion"].quantity, 1);
        let draft = store.turn_status(&request).unwrap();
        assert_eq!(draft.request, request);
        assert_eq!(draft.phase, TurnPhase::Draft);
        assert!(draft.receipt.is_none());
        assert_eq!(store.drafts(&scope).unwrap().len(), 1);
        assert_eq!(rows(&store, Some(&other_scope.story)), other_rows);
        assert_eq!(
            store.resume(&other_scope).unwrap().engine.canonical_bytes(),
            other_canon
        );
    }
    raise_pages(&store, pages);
    let mut reference = Engine::new(engine.seed().clone()).unwrap();
    reference
        .commit(&request, &proposal, preview.narration())
        .unwrap();
    let committed = store
        .commit_turn(&request, &proposal, preview.narration())
        .unwrap();
    assert_eq!(committed, preview);
    assert_eq!(
        store.turn_status(&request).unwrap().phase,
        TurnPhase::Committed
    );
    assert!(store.drafts(&scope).unwrap().is_empty());
    let after = rows(&store, None);
    assert_eq!(
        store
            .commit_turn(&request, &proposal, preview.narration())
            .unwrap(),
        committed
    );
    assert_eq!(rows(&store, None), after);
    directory.assert_bounded();
    drop(store);

    let mut store = directory.open();
    let resumed = store.resume(&scope).unwrap();
    assert!(!resumed.projection_needs_rebuild);
    assert_eq!(resumed.engine.revision(), 8);
    assert_eq!(
        resumed.engine.canonical_bytes(),
        reference.canonical_bytes()
    );
    assert_eq!(resumed.engine.seed().facts, engine.seed().facts);
    assert_eq!(resumed.engine.receipts(), std::slice::from_ref(&committed));
    assert_eq!(resumed.engine.state().items["potion"].owner, "mira");
    assert_eq!(resumed.engine.state().items["potion"].quantity, 1);
    assert_eq!(resumed.engine.state().claims.len(), 7);
    assert_eq!(resumed.engine.state().beliefs, engine.state().beliefs);
    assert_eq!(
        resumed.engine.state().discoveries,
        engine.state().discoveries
    );
    assert_eq!(
        resumed
            .engine
            .character_context("sable", &scope, 8)
            .unwrap()
            .observations
            .len(),
        0
    );
    assert_eq!(
        store
            .commit_turn(&request, &proposal, preview.narration())
            .unwrap(),
        committed
    );
    assert_eq!(rows(&store, None), after);
    assert_eq!(rows(&store, Some(&other_scope.story)), other_rows);
    assert_eq!(
        store.resume(&other_scope).unwrap().engine.canonical_bytes(),
        other_canon
    );
    directory.assert_bounded();
}

#[test]
fn full_while_creating_draft_leaves_no_turn_and_same_connection_can_retry() {
    let directory = Temp::new();
    let mut store = directory.open();
    let initial = seed();
    let scope = initial.scope.clone();
    let engine = Engine::new(initial.clone()).unwrap();
    store
        .create_story("Synthetic draft pressure fixture", initial)
        .unwrap();
    let (other_scope, other_canon) = add_other_story(&mut store);
    let (request, proposal, preview) = large_gift(&engine);
    let before = rows(&store, None);
    let pages = clamp_pages(&store);
    assert!(matches!(store.begin_turn(&request), Err(TurnError::Full)));
    assert_eq!(rows(&store, None), before);
    assert!(matches!(
        store.turn_status(&request),
        Err(TurnError::UnknownTurn)
    ));
    assert!(store.drafts(&scope).unwrap().is_empty());
    assert_eq!(
        store.resume(&scope).unwrap().engine.canonical_bytes(),
        engine.canonical_bytes()
    );
    assert_eq!(
        store.resume(&other_scope).unwrap().engine.canonical_bytes(),
        other_canon
    );
    raise_pages(&store, pages);
    assert_eq!(store.begin_turn(&request).unwrap().phase, TurnPhase::Draft);
    assert_eq!(
        store
            .commit_turn(&request, &proposal, preview.narration())
            .unwrap(),
        preview
    );
    let after = rows(&store, None);
    drop(store);
    let mut store = directory.open();
    assert_eq!(
        store.begin_turn(&request).unwrap().phase,
        TurnPhase::Committed
    );
    assert_eq!(
        store
            .commit_turn(&request, &proposal, preview.narration())
            .unwrap(),
        preview
    );
    assert_eq!(rows(&store, None), after);
    assert_eq!(
        store.resume(&scope).unwrap().engine.state().items["potion"].owner,
        "mira"
    );
    assert_eq!(
        store.resume(&other_scope).unwrap().engine.canonical_bytes(),
        other_canon
    );
    directory.assert_bounded();
}
