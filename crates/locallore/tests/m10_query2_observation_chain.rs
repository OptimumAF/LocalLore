#![cfg(feature = "host")]
// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Original M10.01 observation-chain composition oracle.
//! Intended integration: crates/locallore/tests/m10_query2_observation_chain.rs.
//! No confirmed defect is claimed; this fills a concrete Query2 regression gap.
use locallore::{author_correction::*, contracts::*, engine::Engine, inspection_query::*};

const A: &str = "B95_A_SEED_KNOWN";
const B: &str = "B95_B_WITNESSED";
const C: &str = "B95_C_UNSEEN_CORRECTION";
const PARENT: &str = "B95_PARENT_AFTER_FORK";
const SIBLING: &str = "B95_SIBLING_AFTER_FORK";

fn amend(parent: &Engine, child: &str, before: &str, after: &str) -> Engine {
    let input = AuthorCorrectionInputV1 {
        version: 1,
        parent: parent.scope().clone(),
        expected_parent_revision: parent.revision(),
        fork_revision: parent.revision(),
        child_branch: child.into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(),
            expected_proposition: before.into(),
            replacement: after.into(),
        },
        reason: "B95_PRIVATE_AUTHOR_REASON".into(),
    };
    parent
        .apply_author_correction(
            &parent.prepare_author_correction(&input, &|| false).unwrap(),
            &|| false,
        )
        .unwrap()
        .engine
}

fn commit(engine: &mut Engine, turn: &str, command: Command) -> Receipt {
    let request = engine.request(turn, Intent::Actions(vec![command]));
    let prepared = engine
        .preview(&request, &Engine::proposal(&request).unwrap())
        .unwrap();
    engine.commit_prepared(&prepared).unwrap()
}

fn request(engine: &Engine, observer: Observer, view: View) -> Query {
    Query {
        version: 2,
        scope: engine.scope().clone(),
        expected_head: engine.revision(),
        at_revision: None,
        observer,
        view,
        cursor: None,
        limit: MAX_ROWS,
        search: String::new(),
    }
}

fn remembered(page: &Page) -> (&str, &[Source]) {
    page.rows
        .iter()
        .find_map(|row| match row {
            Row::Knowledge {
                id,
                text,
                sources,
                origin: ValueOrigin::KnownAsObserved,
                ..
            } if id == "relic-location" => Some((text.as_str(), sources.as_slice())),
            _ => None,
        })
        .unwrap()
}

#[test]
fn remembered_and_per_event_values_survive_two_corrections_without_same_revision_branch_bleed() {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    let player = seed.player.clone();
    let seed_id = seed.id.clone();
    let fact = seed.facts.get_mut("relic-location").unwrap();
    fact.proposition = A.into();
    fact.discoverable_at = Some("quay".into());
    fact.known_by.insert(player.clone());
    fact.known_by.insert("mira".into());
    let initial = Engine::new(seed).unwrap();
    let mut parent = amend(&initial, "first-correction", A, B);
    let discovery = commit(
        &mut parent,
        "witness-B",
        Command::Discover {
            fact: "relic-location".into(),
        },
    );
    let original_scope = parent.scope().clone();
    let discovery_sequence = discovery.events()[0].sequence();
    assert_eq!(discovery_sequence, 2);
    let mut sibling = parent.fork("sibling", parent.revision()).unwrap();
    let selected = amend(&parent, "second-correction", B, C);
    for (engine, canary) in [(&mut parent, PARENT), (&mut sibling, SIBLING)] {
        commit(
            engine,
            "same-numeric-future",
            Command::Say {
                text: canary.into(),
                audience: [player.clone()].into(),
            },
        );
    }
    assert_eq!(
        (parent.revision(), sibling.revision(), selected.revision()),
        (3, 3, 3)
    );
    let before = selected.canonical_bytes();
    let records = selected.canonical_records().to_vec();
    let observed_source = Source::ScopedEvent {
        original_scope,
        sequence: discovery_sequence,
    };

    let current = query(
        &selected,
        &request(&selected, Observer::Player, View::Knowledge),
        false,
    )
    .unwrap();
    assert_eq!(remembered(&current), (B, &[observed_source.clone()][..]));
    assert!(current.rows.iter().any(|row| matches!(row,
        Row::Knowledge { text, sources, origin: ValueOrigin::RecordedDiscovery, .. }
        if text == B && sources == &vec![observed_source.clone()])));
    let npc = query(
        &selected,
        &request(
            &selected,
            Observer::Character { id: "mira".into() },
            View::Knowledge,
        ),
        true,
    )
    .unwrap();
    assert_eq!(remembered(&npc), (A, &[Source::Seed(seed_id.clone())][..]));

    for view in [
        View::Knowledge,
        View::History,
        View::Provenance,
        View::TurnDiff,
    ] {
        for hidden in [C, PARENT, SIBLING, "B95_PRIVATE_AUTHOR_REASON"] {
            let mut q = request(&selected, Observer::Player, view);
            q.search = hidden.into();
            q.limit = 1;
            let page = query(&selected, &q, false).unwrap();
            assert_eq!(page.total, 0, "{view:?} search must not count {hidden}");
            assert!(page.rows.is_empty() && page.next_cursor.is_none());
        }
    }
    for (revision, expected) in [(1, A), (2, B)] {
        let mut q = request(&selected, Observer::Player, View::Knowledge);
        q.at_revision = Some(revision);
        let page = query(&selected, &q, false).unwrap();
        assert_eq!((page.head, page.revision), (3, revision));
        assert_eq!(remembered(&page).0, expected);
        if revision == 1 {
            assert_eq!(remembered(&page).1, &[Source::Seed(seed_id.clone())]);
            assert!(!page.rows.iter().any(|r| matches!(
                r,
                Row::Knowledge {
                    origin: ValueOrigin::RecordedDiscovery,
                    ..
                }
            )));
        } else {
            assert_eq!(remembered(&page).1, std::slice::from_ref(&observed_source));
        }
    }
    let mut q = request(&selected, Observer::Player, View::Knowledge);
    q.search = B.into();
    q.limit = 1;
    let first = query(&selected, &q, false).unwrap();
    assert_eq!((first.total, first.rows.len()), (2, 1));
    q.cursor = Some(first.next_cursor.clone().unwrap());
    let last = query(&selected, &q, false).unwrap();
    assert_eq!((last.total, last.rows.len()), (2, 1));
    assert!(last.next_cursor.is_none());
    assert_ne!(first.rows[0].key(), last.rows[0].key());
    q.at_revision = Some(2); // Same B rows, different historical request identity.
    assert_eq!(
        query(&selected, &q, false).unwrap_err(),
        QueryError::InvalidCursor
    );
    let omni = query(
        &selected,
        &request(&selected, Observer::Omniscient, View::Knowledge),
        true,
    )
    .unwrap();
    assert!(omni.rows.iter().any(|r| matches!(r,
        Row::Knowledge { id, text, origin: ValueOrigin::CanonicalTruth, .. }
        if id == "relic-location" && text == C)));
    assert_eq!(selected.canonical_bytes(), before);
    assert_eq!(selected.canonical_records(), records.as_slice());
}
