//! Actual Core oracles frozen before Query2 production changes. No Host/Store/model.
use locallore::{author_correction::*, contracts::*, engine::Engine, inspection_query::*};
use serde_json::Value;
fn fixture() -> Engine {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    let fact = seed.facts.get_mut("relic-location").unwrap();
    fact.proposition = "OBSERVED_A".into();
    fact.discoverable_at = Some("quay".into());
    fact.known_by.insert("mira".into());
    seed.facts.get_mut("ancestry").unwrap().proposition = "PLAYER_SECRET".into();
    Engine::new(seed).unwrap()
}
fn correction(e: &Engine, child: &str) -> Engine {
    let input = AuthorCorrectionInputV1 {
        version: 1,
        parent: e.scope().clone(),
        expected_parent_revision: e.revision(),
        fork_revision: e.revision(),
        child_branch: child.into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(),
            expected_proposition: "OBSERVED_A".into(),
            replacement: "PRIVATE_WORLD_B".into(),
        },
        reason: "PRIVATE_AUTHOR_REASON".into(),
    };
    e.apply_author_correction(
        &e.prepare_author_correction(&input, &|| false).unwrap(),
        &|| false,
    )
    .unwrap()
    .engine
}
fn commit(e: &mut Engine, turn: &str, commands: Vec<Command>) -> Receipt {
    let request = e.request(turn, Intent::Actions(commands));
    let receipt = e
        .preview(&request, &Engine::proposal(&request).unwrap())
        .unwrap();
    e.commit_prepared(&receipt).unwrap()
}
fn request(e: &Engine, observer: Observer, view: View) -> Query {
    Query {
        version: 2,
        scope: e.scope().clone(),
        expected_head: e.revision(),
        at_revision: None,
        observer,
        view,
        cursor: None,
        limit: 64,
        search: String::new(),
    }
}
fn page(e: &Engine, observer: Observer, view: View) -> Page {
    query(e, &request(e, observer, view), true).unwrap()
}
fn encode(v: impl serde::Serialize) -> String {
    serde_json::to_string(&v).unwrap()
}
fn fact_row(p: &Page) -> &Row {
    p.rows.iter().find(|r|matches!(r,Row::Knowledge{id,origin:ValueOrigin::KnownAsObserved,..} if id=="relic-location")).unwrap()
}

#[test]
fn query1_domain2_is_version_before_every_lens_view_and_privilege() {
    let e = correction(&fixture(), "child");
    for observer in [
        Observer::Player,
        Observer::Character { id: "mira".into() },
        Observer::Character {
            id: "missing".into(),
        },
        Observer::Omniscient,
    ] {
        for view in [
            View::Profiles,
            View::History,
            View::Relationships,
            View::Knowledge,
            View::Promises,
            View::Provenance,
            View::TurnDiff,
            View::Summaries,
            View::RetrievalIndexes,
        ] {
            let mut q = request(&e, observer.clone(), view);
            q.version = 1;
            for grant in [false, true] {
                assert_eq!(query(&e, &q, grant).unwrap_err(), QueryError::Version);
            }
        }
    }
}
#[test]
fn remembered_values_and_private_world_truth_have_distinct_safe_query2_views() {
    let e = correction(&fixture(), "child");
    for observer in [Observer::Player, Observer::Character { id: "mira".into() }] {
        let p = page(&e, observer, View::Knowledge);
        assert_eq!(p.version, 2);
        assert!(
            matches!(fact_row(&p),Row::Knowledge{text,origin:ValueOrigin::KnownAsObserved,..} if text=="OBSERVED_A")
        );
        for canary in [
            "PRIVATE_WORLD_B",
            "PRIVATE_AUTHOR_REASON",
            "truth_source",
            "before",
        ] {
            assert!(!encode(&p).contains(canary));
        }
    }
    let omni = page(&e, Observer::Omniscient, View::Knowledge);
    assert!(omni.rows.iter().any(|r|matches!(r,Row::Knowledge{id,text,sources,origin:ValueOrigin::CanonicalTruth,..} if id=="relic-location" && text=="PRIVATE_WORLD_B" && sources==&vec![Source::Withheld])));
    assert!(!encode(&omni).contains("PRIVATE_AUTHOR_REASON"));
    assert_eq!(
        query(
            &e,
            &request(&e, Observer::Omniscient, View::Knowledge),
            false
        )
        .unwrap_err(),
        QueryError::Forbidden
    );
    assert_eq!(
        query(
            &e,
            &request(
                &e,
                Observer::Character { id: "mira".into() },
                View::Knowledge
            ),
            false
        )
        .unwrap_err(),
        QueryError::Forbidden
    );
}
#[test]
fn rediscovery_current_value_and_per_event_values_use_actual_scoped_observations() {
    let mut e = correction(&fixture(), "child");
    commit(
        &mut e,
        "rediscover",
        vec![
            Command::Discover {
                fact: "relic-location".into(),
            },
            Command::Discover {
                fact: "relic-location".into(),
            },
        ],
    );
    let p = page(&e, Observer::Player, View::Knowledge);
    assert!(
        matches!(fact_row(&p),Row::Knowledge{text,sources,..} if text=="PRIVATE_WORLD_B" && sources==&vec![Source::ScopedEvent{original_scope:e.scope().clone(),sequence:3}])
    );
    let discoveries: Vec<_> = p
        .rows
        .iter()
        .filter(|r| {
            matches!(
                r,
                Row::Knowledge {
                    origin: ValueOrigin::RecordedDiscovery,
                    ..
                }
            )
        })
        .collect();
    assert_eq!(discoveries.len(), 2);
    for row in discoveries {
        assert!(matches!(row,Row::Knowledge{text,..} if text=="PRIVATE_WORLD_B"));
    }
    let npc = page(
        &e,
        Observer::Character { id: "mira".into() },
        View::Knowledge,
    );
    assert!(matches!(fact_row(&npc),Row::Knowledge{text,..} if text=="OBSERVED_A"));
    assert!(!encode(npc).contains("PRIVATE_WORLD_B"));
}
#[test]
fn npc_history_filters_empty_receipts_before_search_count_and_never_attaches_player_messages() {
    let mut e = correction(&fixture(), "child");
    commit(
        &mut e,
        "private",
        vec![Command::Say {
            text: "PRIVATE_PLAYER_INPUT".into(),
            audience: ["player".into()].into(),
        }],
    );
    let empty = page(&e, Observer::Character { id: "mira".into() }, View::History);
    assert_eq!(empty.total, 0);
    assert!(empty.rows.is_empty());
    assert!(empty.next_cursor.is_none());
    let mut search = request(&e, Observer::Character { id: "mira".into() }, View::History);
    search.search = "PRIVATE_PLAYER_INPUT".into();
    assert_eq!(query(&e, &search, true).unwrap().total, 0);
    commit(
        &mut e,
        "public",
        vec![Command::Say {
            text: "WITNESSED_WORDS".into(),
            audience: ["mira".into()].into(),
        }],
    );
    let visible = page(&e, Observer::Character { id: "mira".into() }, View::History);
    assert_eq!(visible.total, 1);
    assert!(visible.rows.iter().all(|r| matches!(r, Row::Event { .. })));
    assert!(encode(&visible).contains("WITNESSED_WORDS"));
    for secret in [
        "PRIVATE_PLAYER_INPUT",
        "PRIVATE_AUTHOR_REASON",
        "PLAYER_SECRET",
        "PRIVATE_WORLD_B",
        "request",
        "proposal",
        "narration",
    ] {
        assert!(!encode(&visible).contains(secret));
    }
}
#[test]
fn owning_player_messages_require_actual_whole_receipt_eligibility() {
    let mut e = correction(&fixture(), "child");
    let r = e.request(
        "dialogue",
        Intent::Dialogue {
            text: "PLAYER_ORIGINAL".into(),
            audience: ["mira".into()].into(),
        },
    );
    let v = e.preview(&r, &Engine::proposal(&r).unwrap()).unwrap();
    e.commit_prepared(&v).unwrap();
    let p = page(&e, Observer::Player, View::History);
    assert_eq!(p.total, 4); // actual event, two scoped messages, neutral author marker
    assert!(p.rows.iter().any(|r|matches!(r,Row::ScopedMessage{message_kind,text,original_scope,..} if message_kind=="original_input" && text=="PLAYER_ORIGINAL" && original_scope==e.scope())));
    assert!(p
        .rows
        .iter()
        .any(|r| matches!(r,Row::ScopedMessage{message_kind,original_scope,..} if message_kind=="narration" && original_scope==e.scope())));
    assert!(p
        .rows
        .iter()
        .any(|r| matches!(r, Row::AuthorCorrection { revision: 1, .. })));
    assert!(!p.rows.iter().any(|r| matches!(r, Row::Message { .. })));
    let npc = page(&e, Observer::Character { id: "mira".into() }, View::History);
    assert_eq!(npc.total, 1);
    assert!(npc.rows.iter().all(|r| matches!(r, Row::Event { .. })));
}
#[test]
fn author_only_completed_interval_has_empty_actor_diff_and_one_private_truth_diff() {
    let e = correction(&fixture(), "child");
    assert_eq!(e.completed_boundary_catalog().boundaries, vec![0, 1]);
    let actor = page(&e, Observer::Player, View::TurnDiff);
    assert_eq!(actor.revision, 1);
    assert_eq!(actor.total, 0);
    let npc = page(
        &e,
        Observer::Character { id: "mira".into() },
        View::TurnDiff,
    );
    assert_eq!(npc.total, 0);
    let omni = page(&e, Observer::Omniscient, View::TurnDiff);
    assert_eq!(omni.total, 1);
    assert!(
        matches!(&omni.rows[0],Row::Change{before_revision:0,after_revision:1,before:Some(before),after:Some(after),..} if matches!(before.as_ref(),Row::Knowledge{text,..} if text=="OBSERVED_A") && matches!(after.as_ref(),Row::Knowledge{text,..} if text=="PRIVATE_WORLD_B"))
    );
    assert!(!encode(omni).contains("PRIVATE_AUTHOR_REASON"));
}
#[test]
fn cursor_namespaces_cannot_cross_versions_or_accept_tampering() {
    let mut e = fixture();
    for n in 0..4 {
        commit(
            &mut e,
            &format!("say-{n}"),
            vec![Command::Say {
                text: format!("words{n}"),
                audience: ["mira".into()].into(),
            }],
        );
    }
    let mut q = request(&e, Observer::Player, View::History);
    q.limit = 2;
    let v2 = query(&e, &q, false).unwrap().next_cursor.unwrap();
    assert!(v2.starts_with("2:"));
    q.version = 1;
    let v1 = query(&e, &q, false).unwrap().next_cursor.unwrap();
    assert!(v1.starts_with("1:"));
    q.cursor = Some(v2.clone());
    assert_eq!(query(&e, &q, false).unwrap_err(), QueryError::InvalidCursor);
    q.version = 2;
    q.cursor = Some(v1);
    assert_eq!(query(&e, &q, false).unwrap_err(), QueryError::InvalidCursor);
    q.cursor = Some(v2);
    q.search = "different".into();
    assert_eq!(query(&e, &q, false).unwrap_err(), QueryError::InvalidCursor);
}
#[test]
fn fork_original_scopes_parent_future_sibling_and_prebirth_remain_separate() {
    let mut parent = correction(&fixture(), "authored");
    commit(
        &mut parent,
        "discover",
        vec![Command::Discover {
            fact: "relic-location".into(),
        }],
    );
    let mut child = parent.fork("child", 2).unwrap();
    let mut sibling = parent.fork("sibling", 2).unwrap();
    commit(
        &mut parent,
        "future",
        vec![Command::Say {
            text: "PARENT_FUTURE".into(),
            audience: ["mira".into()].into(),
        }],
    );
    commit(
        &mut sibling,
        "sibling-turn",
        vec![Command::Say {
            text: "SIBLING_ONLY".into(),
            audience: ["mira".into()].into(),
        }],
    );
    commit(&mut child, "local", vec![Command::Wait { ticks: 1 }]);
    let p = page(&child, Observer::Player, View::Knowledge);
    assert!(
        matches!(fact_row(&p),Row::Knowledge{sources,..} if sources==&vec![Source::ScopedEvent{original_scope:Scope{story:child.scope().story.clone(),branch:"authored".into()},sequence:2}])
    );
    let h = page(&child, Observer::Player, View::History);
    for canary in ["PARENT_FUTURE", "SIBLING_ONLY", "PRIVATE_AUTHOR_REASON"] {
        assert!(!encode(&h).contains(canary));
    }
    let prebirth = child.fork("prebirth", 0).unwrap();
    assert!(
        matches!(fact_row(&page(&prebirth,Observer::Player,View::Knowledge)),Row::Knowledge{text,..} if text=="OBSERVED_A")
    );
}
#[test]
fn source_version_bounds_scope_head_partial_boundary_and_unsupported_views_are_closed() {
    let mut e = correction(&fixture(), "child");
    commit(
        &mut e,
        "multi",
        vec![Command::Wait { ticks: 1 }, Command::Wait { ticks: 1 }],
    );
    let q = request(&e, Observer::Player, View::Knowledge);
    let mut bad = q.clone();
    bad.version = 3;
    assert_eq!(query(&e, &bad, false).unwrap_err(), QueryError::Version);
    for limit in [0, 65] {
        let mut bad = q.clone();
        bad.limit = limit;
        assert_eq!(query(&e, &bad, false).unwrap_err(), QueryError::TooLarge);
    }
    let mut bad = q.clone();
    bad.search = "x".repeat(257);
    assert_eq!(query(&e, &bad, false).unwrap_err(), QueryError::TooLarge);
    let mut bad = q.clone();
    bad.search = "\u{0000}".into();
    assert_eq!(
        query(&e, &bad, false).unwrap_err(),
        QueryError::InvalidRequest
    );
    let mut bad = q.clone();
    bad.cursor = Some("x".repeat(129));
    assert_eq!(
        query(&e, &bad, false).unwrap_err(),
        QueryError::InvalidCursor
    );
    let mut bad = q.clone();
    bad.scope.branch = "foreign".into();
    assert_eq!(query(&e, &bad, false).unwrap_err(), QueryError::Scope);
    let mut bad = q.clone();
    bad.expected_head = 0;
    assert_eq!(query(&e, &bad, false).unwrap_err(), QueryError::Stale);
    let mut bad = q.clone();
    bad.at_revision = Some(2);
    assert_eq!(
        query(&e, &bad, false).unwrap_err(),
        QueryError::InvalidBoundary
    );
    for view in [View::Summaries, View::RetrievalIndexes] {
        let p = page(&e, Observer::Player, view);
        assert_eq!(p.status, ViewStatus::Unsupported);
        assert_eq!(p.total, 0);
        assert!(!p.unsupported.is_empty());
    }
}
#[test]
fn query2_is_read_only_paginated_and_source_scoped_for_mechanics_and_provenance() {
    let mut e = correction(&fixture(), "child");
    commit(
        &mut e,
        "gift",
        vec![Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 1,
        }],
    );
    let before = e.accepted_history_basis().unwrap();
    let records = e.canonical_records().to_vec();
    let state = e.canonical_bytes();
    for view in [
        View::Profiles,
        View::Relationships,
        View::Promises,
        View::Knowledge,
        View::Provenance,
        View::History,
        View::TurnDiff,
    ] {
        let mut q = request(&e, Observer::Player, view);
        q.limit = 2;
        let mut got = Vec::<Row>::new();
        let mut turns = 0;
        loop {
            let p = query(&e, &q, false).unwrap();
            assert!(p.rows.len() <= 2);
            assert!(serde_json::to_vec(&p).unwrap().len() <= MAX_PAGE_BYTES);
            got.extend(p.rows);
            turns += 1;
            assert!(turns < 100);
            if let Some(c) = p.next_cursor {
                q.cursor = Some(c)
            } else {
                break;
            }
        }
        let all = page(&e, Observer::Player, view);
        assert_eq!(got, all.rows);
        assert_eq!(got.len(), all.total);
        let value: Value = serde_json::to_value(&got).unwrap();
        assert!(!encode(value).contains("PRIVATE_AUTHOR_REASON"));
    }
    // Existing Give changes the recipient's directed obligation to the giver.
    let p = page(
        &e,
        Observer::Character { id: "mira".into() },
        View::Relationships,
    );
    assert!(p.rows.iter().any(|r|matches!(r,Row::Relationship{source:Source::ScopedEvent{original_scope,sequence:2},..} if original_scope==e.scope())));
    assert_eq!(before, e.accepted_history_basis().unwrap());
    assert_eq!(records, e.canonical_records());
    assert_eq!(state, e.canonical_bytes());
}
