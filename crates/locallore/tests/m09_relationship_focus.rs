// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Actual Engine read oracles; no model, persistence, JNI or Android execution.
use locallore::{author_correction::*, contracts::*, engine::Engine, inspection_query::*};
use std::collections::{BTreeMap, BTreeSet};

fn seed() -> Seed {
    serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap()
}

fn many_targets() -> Engine {
    let mut seed = seed();
    let mut upper = seed.actors["mira"].clone();
    upper.name = "PRIVATE_CASE_ACTOR_NAME_69".into();
    seed.actors.insert("Mira".into(), upper.clone());
    upper.name = "PRIVATE_PREFIX_ACTOR_NAME_69".into();
    seed.actors.insert("mira-more".into(), upper);
    for (target, value) in [("Mira", 31), ("mira-more", 41), ("oren", 51), ("sable", 61)] {
        seed.relationships.push(Relationship {
            from: "player".into(),
            to: target.into(),
            respect: value,
            trust: value + 1,
            obligation: value + 2,
        });
    }
    seed.relationships.push(Relationship {
        from: "Mira".into(),
        to: "sable".into(),
        respect: 99,
        trust: 98,
        obligation: 97,
    });
    Engine::new(seed).unwrap()
}

fn request(engine: &Engine) -> Query {
    Query {
        version: 2,
        scope: engine.scope().clone(),
        expected_head: engine.revision(),
        at_revision: None,
        observer: Observer::Player,
        view: View::Relationships,
        cursor: None,
        limit: 8,
        search: String::new(),
    }
}

fn canonical(engine: &Engine) -> (Vec<u8>, Vec<u8>) {
    (
        engine.canonical_bytes(),
        serde_json::to_vec(engine.canonical_records()).unwrap(),
    )
}

fn commit(engine: &mut Engine, turn: &str, commands: Vec<Command>) {
    let request = engine.request(turn, Intent::Actions(commands));
    let prepared = engine
        .preview(&request, &Engine::proposal(&request).unwrap())
        .unwrap();
    engine.commit_prepared(&prepared).unwrap();
}

fn focused_rows(engine: &Engine, mut query: Query, target: &str, grant: bool) -> Vec<Row> {
    let mut rows = Vec::new();
    let mut keys = BTreeSet::new();
    loop {
        let page = relationship_focus(engine, &query, target, grant).unwrap();
        assert_eq!(page.total, 3);
        assert!(page.rows.len() <= usize::from(query.limit));
        for row in &page.rows {
            assert!(keys.insert(row.key().to_owned()));
        }
        rows.extend(page.rows);
        match page.next_cursor {
            Some(cursor) => query.cursor = Some(cursor),
            None => break,
        }
        assert!(rows.len() < 3);
    }
    assert_eq!(rows.len(), 3);
    rows
}

fn dimensions(rows: &[Row], from: &str, target: &str) -> BTreeMap<String, i16> {
    rows.iter()
        .map(|row| match row {
            Row::Relationship {
                from: actual_from,
                to,
                dimension,
                value,
                origin,
                ..
            } => {
                assert_eq!(actual_from, from);
                assert_eq!(to, target);
                assert_eq!(*origin, ValueOrigin::CanonicalField);
                (dimension.clone(), *value)
            }
            _ => panic!("relationship focus returned another row kind"),
        })
        .collect()
}

#[test]
fn exact_case_and_prefix_targets_have_native_totals_and_complete_paging() {
    let engine = many_targets();
    let before = canonical(&engine);
    let all = query(&engine, &request(&engine), false).unwrap();
    assert_eq!((all.total, all.rows.len()), (15, 8));
    assert!(all.next_cursor.is_some());
    let mut text = request(&engine);
    text.search = "\"to\":\"mira\"".into();
    // Ordinary search intentionally folds case. It is not an identity filter.
    assert_eq!(query(&engine, &text, false).unwrap().total, 6);
    for (target, respect, trust, obligation) in [
        ("mira", 1, 2, 0),
        ("Mira", 31, 32, 33),
        ("mira-more", 41, 42, 43),
    ] {
        let mut q = request(&engine);
        q.limit = 1;
        let rows = focused_rows(&engine, q, target, false);
        assert_eq!(
            dimensions(&rows, "player", target),
            BTreeMap::from([
                ("respect".into(), respect),
                ("trust".into(), trust),
                ("obligation".into(), obligation),
            ])
        );
        let encoded = serde_json::to_string(&rows).unwrap();
        assert!(!encoded.contains("PRIVATE_CASE_ACTOR_NAME_69"));
        assert!(!encoded.contains("PRIVATE_PREFIX_ACTOR_NAME_69"));
    }
    assert_eq!(canonical(&engine), before);
}

#[test]
fn focus_cursor_is_domain_separated_even_when_all_visible_rows_have_one_target() {
    let engine = Engine::new(seed()).unwrap();
    let before = canonical(&engine);
    let mut q = request(&engine);
    q.limit = 1;
    let all = query(&engine, &q, false).unwrap();
    let focus = relationship_focus(&engine, &q, "mira", false).unwrap();
    assert_eq!(all.total, 3);
    assert_eq!(focus.total, 3);
    assert_eq!(
        serde_json::to_vec(&all.rows).unwrap(),
        serde_json::to_vec(&focus.rows).unwrap()
    );
    assert_ne!(all.next_cursor, focus.next_cursor);
    let mut retagged = q.clone();
    retagged.cursor = all.next_cursor;
    assert_eq!(
        relationship_focus(&engine, &retagged, "mira", false).unwrap_err(),
        QueryError::InvalidCursor
    );
    retagged.cursor = focus.next_cursor;
    assert_eq!(
        query(&engine, &retagged, false).unwrap_err(),
        QueryError::InvalidCursor
    );
    assert_eq!(
        relationship_focus(&engine, &retagged, "oren", false).unwrap_err(),
        QueryError::InvalidCursor
    );
    assert_eq!(canonical(&engine), before);
}

#[test]
fn a_target_never_grants_another_actor_lens_profile_or_hidden_incoming_edge() {
    let engine = many_targets();
    let before = canonical(&engine);
    let q = request(&engine);
    for target in ["player", "not-visible"] {
        let page = relationship_focus(&engine, &q, target, false).unwrap();
        assert_eq!(page.total, 0);
        assert!(page.rows.is_empty() && page.next_cursor.is_none());
    }
    let mut private = q.clone();
    private.observer = Observer::Character { id: "mira".into() };
    assert_eq!(
        relationship_focus(&engine, &private, "player", false).unwrap_err(),
        QueryError::Forbidden
    );
    let allowed = focused_rows(&engine, private, "player", true);
    assert_eq!(dimensions(&allowed, "mira", "player")["trust"], -3);
    let mut omniscient = q.clone();
    omniscient.observer = Observer::Omniscient;
    assert_eq!(
        relationship_focus(&engine, &omniscient, "sable", false).unwrap_err(),
        QueryError::Forbidden
    );
    let mut profile = q;
    profile.view = View::Profiles;
    assert_eq!(
        relationship_focus(&engine, &profile, "Mira", false).unwrap_err(),
        QueryError::InvalidRequest
    );
    assert_eq!(canonical(&engine), before);
}

#[test]
fn invalid_focus_boundaries_fail_without_mutating_canonical_state() {
    let engine = many_targets();
    let before = canonical(&engine);
    let q = request(&engine);
    for target in [
        "".to_owned(),
        "x".repeat(65),
        "mira\"".into(),
        "海".into(),
        "mira\n".into(),
    ] {
        assert_eq!(
            relationship_focus(&engine, &q, &target, false).unwrap_err(),
            QueryError::InvalidRequest
        );
    }
    let mut invalid = q.clone();
    invalid.version = 1;
    assert_eq!(
        relationship_focus(&engine, &invalid, "mira", false).unwrap_err(),
        QueryError::Version
    );
    invalid = q.clone();
    invalid.scope.story = "another-story".into();
    assert_eq!(
        relationship_focus(&engine, &invalid, "mira", false).unwrap_err(),
        QueryError::Scope
    );
    invalid = q.clone();
    invalid.expected_head += 1;
    assert_eq!(
        relationship_focus(&engine, &invalid, "mira", false).unwrap_err(),
        QueryError::Stale
    );
    invalid = q.clone();
    invalid.search = "mira".into();
    assert_eq!(
        relationship_focus(&engine, &invalid, "mira", false).unwrap_err(),
        QueryError::InvalidRequest
    );
    invalid = q.clone();
    invalid.limit = 0;
    assert_eq!(
        relationship_focus(&engine, &invalid, "mira", false).unwrap_err(),
        QueryError::TooLarge
    );
    invalid = q.clone();
    invalid.at_revision = Some(1);
    assert_eq!(
        relationship_focus(&engine, &invalid, "mira", false).unwrap_err(),
        QueryError::InvalidBoundary
    );
    invalid = q;
    invalid.cursor = Some("x".repeat(129));
    assert_eq!(
        relationship_focus(&engine, &invalid, "mira", false).unwrap_err(),
        QueryError::InvalidCursor
    );
    assert_eq!(canonical(&engine), before);
}

#[test]
fn corrected_child_keeps_inherited_relationship_source_not_parent_future_or_private_truth() {
    let mut seed = seed();
    seed.items
        .insert("other-potion".into(), seed.items["potion"].clone());
    let mut parent = Engine::new(seed).unwrap();
    commit(
        &mut parent,
        "help",
        vec![Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 1,
        }],
    );
    let original = parent.scope().clone();
    let input = AuthorCorrectionInputV1 {
        version: 1,
        parent: original.clone(),
        expected_parent_revision: parent.revision(),
        fork_revision: parent.revision(),
        child_branch: "corrected".into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(),
            expected_proposition: parent.seed().facts["relic-location"].proposition.clone(),
            replacement: "PRIVATE_RELATIONSHIP_WORLD_69".into(),
        },
        reason: "PRIVATE_RELATIONSHIP_REASON_69".into(),
    };
    let prepared = parent.prepare_author_correction(&input, &|| false).unwrap();
    let child = parent
        .apply_author_correction(&prepared, &|| false)
        .unwrap()
        .engine;
    assert_eq!(child.domain_version(), 2);
    let mut sibling = child.fork("sibling", child.revision()).unwrap();
    for (engine, turn) in [
        (&mut parent, "parent-future"),
        (&mut sibling, "sibling-future"),
    ] {
        commit(
            engine,
            turn,
            vec![Command::Give {
                item: "other-potion".into(),
                to: "mira".into(),
                quantity: 1,
            }],
        );
    }
    let before = canonical(&child);
    let mut q = request(&child);
    q.observer = Observer::Character { id: "mira".into() };
    let rows = focused_rows(&child, q.clone(), "player", true);
    assert_eq!(dimensions(&rows, "mira", "player")["obligation"], 1);
    assert!(rows.iter().any(|row| matches!(row, Row::Relationship { dimension, source: Source::ScopedEvent { original_scope, sequence: 1 }, .. }
        if dimension == "obligation" && original_scope == &original)));
    let encoded = serde_json::to_string(&rows).unwrap();
    for forbidden in [
        "PRIVATE_RELATIONSHIP_WORLD_69",
        "PRIVATE_RELATIONSHIP_REASON_69",
        "parent-future",
        "sibling-future",
    ] {
        assert!(!encoded.contains(forbidden));
    }
    assert_eq!(
        relationship_focus(&child, &q, "player", false).unwrap_err(),
        QueryError::Forbidden
    );
    assert_eq!(canonical(&child), before);
}

#[test]
fn historical_focus_uses_completed_observer_state_and_fences_its_cursor() {
    let mut engine = Engine::new(seed()).unwrap();
    commit(
        &mut engine,
        "help",
        vec![Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 1,
        }],
    );
    let before = canonical(&engine);
    let mut q = request(&engine);
    q.observer = Observer::Character { id: "mira".into() };
    q.limit = 1;
    let current = relationship_focus(&engine, &q, "player", true).unwrap();
    let current_rows = focused_rows(&engine, q.clone(), "player", true);
    assert_eq!(dimensions(&current_rows, "mira", "player")["obligation"], 1);
    q.at_revision = Some(0);
    let old_rows = focused_rows(&engine, q.clone(), "player", true);
    assert_eq!(dimensions(&old_rows, "mira", "player")["obligation"], 0);
    assert!(old_rows.iter().all(|row| matches!(
        row,
        Row::Relationship {
            source: Source::Seed(_),
            ..
        }
    )));
    q.cursor = current.next_cursor;
    assert_eq!(
        relationship_focus(&engine, &q, "player", true).unwrap_err(),
        QueryError::InvalidCursor
    );
    assert_eq!(canonical(&engine), before);
}
