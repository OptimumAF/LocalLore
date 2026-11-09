//! Exact status presets query native, eligible rows; they never filter one UI page.
#![cfg(feature = "host")]

use locallore::{author_correction::*, contracts::*, engine::Engine, inspection_query::*};
use std::collections::BTreeSet;

const OPEN: &str = "\"status\":\"open\"";
const OVERDUE: &str = "\"status\":\"overdue\"";
const FULFILLED: &str = "\"status\":\"fulfilled\"";
const PRIVATE: &str = "UNOBSERVED_INCOMING_TERMS_66";

fn seed() -> Seed {
    serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap()
}

fn commit(engine: &mut Engine, turn: &str, commands: Vec<Command>) {
    let request = engine.request(turn, Intent::Actions(commands));
    let prepared = engine
        .preview(&request, &Engine::proposal(&request).unwrap())
        .unwrap();
    engine.commit_prepared(&prepared).unwrap();
}

fn request(engine: &Engine, search: &str) -> Query {
    Query {
        version: 2,
        scope: engine.scope().clone(),
        expected_head: engine.revision(),
        at_revision: None,
        observer: Observer::Player,
        view: View::Promises,
        cursor: None,
        limit: 8,
        search: search.into(),
    }
}

fn canon(engine: &Engine) -> (Vec<u8>, Vec<u8>) {
    (
        engine.canonical_bytes(),
        serde_json::to_vec(engine.canonical_records()).unwrap(),
    )
}

fn many_promises() -> Engine {
    let mut seed = seed();
    seed.commitments.get_mut("return-key").unwrap().terms =
        "Keep the door open. Copy these words: \"status\":\"open\" and \"status\":\"overdue\"."
            .into();
    for (prefix, deadline) in [("waiting", 300), ("late", 99)] {
        for index in 0..9 {
            seed.commitments.insert(
                format!("{prefix}-{index}"),
                Commitment {
                    from: "player".into(),
                    to: "mira".into(),
                    terms: format!("Carry note {prefix}-{index}."),
                    deadline,
                    source: Evidence::Seed(seed.id.clone()),
                    return_item: None,
                    completed_by: None,
                },
            );
        }
    }
    seed.commitments.insert(
        "hidden-incoming".into(),
        Commitment {
            from: "sable".into(),
            to: "player".into(),
            terms: PRIVATE.into(),
            deadline: 300,
            source: Evidence::Seed(seed.id.clone()),
            return_item: None,
            completed_by: None,
        },
    );
    let mut engine = Engine::new(seed).unwrap();
    commit(
        &mut engine,
        "walk",
        vec![Command::Move { to: "pier".into() }],
    );
    commit(
        &mut engine,
        "return",
        vec![
            Command::Give {
                item: "brass-key".into(),
                to: "oren".into(),
                quantity: 1,
            },
            Command::CompletePromise {
                id: "return-key".into(),
            },
        ],
    );
    engine
}

#[test]
fn exact_native_status_has_complete_counts_pages_and_query_bound_cursors() {
    let engine = many_promises();
    let before = canon(&engine);
    for (token, status, prefix) in [(OPEN, "open", "waiting-"), (OVERDUE, "overdue", "late-")] {
        let mut q = request(&engine, token);
        let first = query(&engine, &q, false).unwrap();
        assert_eq!(first.total, 9);
        assert_eq!(first.rows.len(), 8);
        let cursor = first
            .next_cursor
            .clone()
            .expect("ninth matching row remains");
        let mut rows = first.rows;
        q.cursor = Some(cursor.clone());
        let second = query(&engine, &q, false).unwrap();
        assert_eq!(second.total, 9);
        assert_eq!(second.rows.len(), 1);
        assert!(second.next_cursor.is_none());
        rows.extend(second.rows);
        let ids: BTreeSet<_> = rows
            .iter()
            .map(|row| match row {
                Row::Promise {
                    id, status: actual, ..
                } => {
                    assert_eq!(actual, status);
                    assert!(id.starts_with(prefix));
                    id.clone()
                }
                _ => panic!("promise view returned another row type"),
            })
            .collect();
        assert_eq!(ids.len(), 9);

        for other in ["", if token == OPEN { OVERDUE } else { OPEN }] {
            let mut retagged = request(&engine, other);
            retagged.cursor = Some(cursor.clone());
            assert_eq!(
                query(&engine, &retagged, false).unwrap_err(),
                QueryError::InvalidCursor
            );
        }
    }
    assert_eq!(canon(&engine), before);
}

#[test]
fn fulfilled_terms_and_unwitnessed_incoming_rows_cannot_spoof_status_presets() {
    let engine = many_promises();
    let before = canon(&engine);
    let generic = query(&engine, &request(&engine, "open"), false).unwrap();
    assert_eq!(
        generic.total, 10,
        "ordinary text search also finds fulfilled terms"
    );
    assert!(generic
        .rows
        .iter()
        .any(|row| matches!(row, Row::Promise { id, status, .. }
        if id == "return-key" && status == "fulfilled")));
    let fulfilled = query(&engine, &request(&engine, FULFILLED), false).unwrap();
    assert_eq!(fulfilled.rows.len(), 1);
    assert!(matches!(&fulfilled.rows[0], Row::Promise { id, status, .. }
        if id == "return-key" && status == "fulfilled"));
    let encoded = serde_json::to_string(&fulfilled).unwrap();
    assert!(encoded.contains("\\\"status\\\":\\\"open\\\""));
    assert!(encoded.contains("\\\"status\\\":\\\"overdue\\\""));

    for token in ["", OPEN, OVERDUE, FULFILLED, PRIVATE] {
        let mut q = request(&engine, token);
        loop {
            let page = query(&engine, &q, false).unwrap();
            let encoded = serde_json::to_string(&page).unwrap();
            assert!(!encoded.contains(PRIVATE));
            assert!(!encoded.contains("hidden-incoming"));
            if token.is_empty() {
                assert_eq!(page.total, 19);
            }
            if token == PRIVATE {
                assert_eq!(page.total, 0);
            }
            match page.next_cursor {
                Some(cursor) => q.cursor = Some(cursor),
                None => break,
            }
        }
    }
    assert_eq!(canon(&engine), before);
}

#[test]
fn creditor_preset_retains_observed_open_status_after_unwitnessed_completion() {
    let mut engine = Engine::new(seed()).unwrap();
    commit(
        &mut engine,
        "promise",
        vec![Command::Promise {
            id: "potion-return".into(),
            to: "mira".into(),
            terms: "Bring the bottle back.".into(),
            deadline: 150,
            return_item: Some("potion".into()),
        }],
    );
    commit(
        &mut engine,
        "transfer",
        vec![Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 1,
        }],
    );
    let mut creditor = request(&engine, OPEN);
    creditor.observer = Observer::Character { id: "mira".into() };
    let observed = query(&engine, &creditor, true).unwrap().rows;
    assert_eq!(observed.len(), 1);
    commit(
        &mut engine,
        "local-completion",
        vec![Command::CompletePromise {
            id: "potion-return".into(),
        }],
    );
    let before = canon(&engine);
    creditor.expected_head = engine.revision();
    assert_eq!(query(&engine, &creditor, true).unwrap().rows, observed);
    creditor.search = FULFILLED.into();
    assert_eq!(query(&engine, &creditor, true).unwrap().total, 0);
    let player = query(&engine, &request(&engine, FULFILLED), false).unwrap();
    assert_eq!(player.total, 1);
    assert!(
        matches!(&player.rows[0], Row::Promise { id, status, sources, .. }
        if id == "potion-return" && status == "fulfilled"
            && sources.contains(&Source::ScopedEvent { original_scope: engine.scope().clone(), sequence: 3 }))
    );
    assert_eq!(canon(&engine), before);
}

#[test]
fn corrected_child_status_search_keeps_original_sources_and_excludes_other_histories() {
    let mut parent = Engine::new(seed()).unwrap();
    commit(
        &mut parent,
        "original-promise",
        vec![Command::Promise {
            id: "inherited-note".into(),
            to: "mira".into(),
            terms: "Bring the written note.".into(),
            deadline: 200,
            return_item: None,
        }],
    );
    let original_scope = parent.scope().clone();
    let correction = AuthorCorrectionInputV1 {
        version: 1,
        parent: parent.scope().clone(),
        expected_parent_revision: parent.revision(),
        fork_revision: parent.revision(),
        child_branch: "corrected".into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(),
            expected_proposition: parent.seed().facts["relic-location"].proposition.clone(),
            replacement: "PRIVATE_CORRECTED_TRUTH_66".into(),
        },
        reason: "PRIVATE_AUTHOR_REASON_66".into(),
    };
    let corrected = parent
        .apply_author_correction(
            &parent
                .prepare_author_correction(&correction, &|| false)
                .unwrap(),
            &|| false,
        )
        .unwrap()
        .engine;
    let mut child = corrected.fork("reading", corrected.revision()).unwrap();
    let mut sibling = corrected.fork("sibling", corrected.revision()).unwrap();
    for (engine, id) in [
        (&mut parent, "parent-future"),
        (&mut sibling, "sibling-only"),
    ] {
        commit(
            engine,
            id,
            vec![Command::Promise {
                id: id.into(),
                to: "mira".into(),
                terms: id.into(),
                deadline: 200,
                return_item: None,
            }],
        );
    }
    commit(&mut child, "local-clock", vec![Command::Wait { ticks: 1 }]);
    let before = canon(&child);
    let q = request(&child, OPEN);
    let page = query(&child, &q, false).unwrap();
    assert_eq!(page.total, 2); // Seed return-key plus inherited witnessed promise.
    assert!(page.rows.iter().any(|row| matches!(row,
        Row::Promise { id, status, sources, .. }
            if id == "inherited-note" && status == "open"
                && sources == &vec![Source::ScopedEvent { original_scope: original_scope.clone(), sequence: 1 }]
    )));
    let encoded = serde_json::to_string(&page).unwrap();
    for forbidden in [
        "parent-future",
        "sibling-only",
        "PRIVATE_CORRECTED_TRUTH_66",
        "PRIVATE_AUTHOR_REASON_66",
    ] {
        assert!(!encoded.contains(forbidden));
        let mut search = q.clone();
        search.search = forbidden.into();
        assert_eq!(query(&child, &search, false).unwrap().total, 0);
    }
    assert_eq!(canon(&child), before);
}
