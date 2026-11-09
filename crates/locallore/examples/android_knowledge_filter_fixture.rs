// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Actual player Knowledge Query2 pages; no model, Host, Store or file writes.
//! Default stdout generates JSON; --check compares the committed corpus byte-for-byte.
use locallore::{
    author_correction::{AuthorCorrectionInputV1, AuthorCorrectionOperationV1},
    contracts::*,
    engine::Engine,
    inspection_query::{
        self, Observer, Page, Privacy, Query, Row, Source, ValueOrigin, View, ViewStatus,
    },
};
use serde::Serialize;
use std::{
    collections::BTreeSet,
    io::{self, Write},
};

const FACT: &str = "relic-location";
const OLD: &str = "Tideglass lies in dry-well: SECRET-TIDE-731.";
const NEW: &str = "B86_UNSEEN_CORRECTED_RELIC_TRUTH";
const NPC_BELIEF: &str = "B86_PRIVATE_NPC_BELIEF_CANARY";
const AUTHOR_REASON: &str = "B86_PRIVATE_AUTHOR_REASON";
const PARENT_ONLY: &str = "B86_PARENT_ONLY_STATEMENT_AFTER_FORK";
const QUOTED_ORIGINS: &str = r#"The placard literally quotes {"origin":"known_as_observed"}, {"origin":"recorded_statement"}, {"origin":"subjective_belief"}, and {"origin":"recorded_discovery"}; these are words, not a truth grant."#;
const ORIGINS: [ValueOrigin; 4] = [
    ValueOrigin::KnownAsObserved,
    ValueOrigin::RecordedStatement,
    ValueOrigin::SubjectiveBelief,
    ValueOrigin::RecordedDiscovery,
];

// Page is serialized directly through its original Query2 serializer. In
// particular, no Value round-trip, row reconstruction or source rewriting occurs.
#[derive(Serialize)]
struct QueryPage {
    query: Query,
    page: Page,
}
#[derive(Serialize)]
struct FilterPages {
    origin: Option<&'static str>,
    pages: Vec<QueryPage>,
}
#[derive(Serialize)]
struct CorpusCase {
    id: &'static str,
    domain_version: u16,
    player: String,
    scope: Scope,
    head: u64,
    story_time: u64,
    forbidden: Vec<&'static str>,
    filters: Vec<FilterPages>,
}
#[derive(Serialize)]
struct Corpus {
    version: u16,
    cases: Vec<CorpusCase>,
}

fn wire_origin(origin: ValueOrigin) -> &'static str {
    match origin {
        ValueOrigin::KnownAsObserved => "known_as_observed",
        ValueOrigin::RecordedStatement => "recorded_statement",
        ValueOrigin::SubjectiveBelief => "subjective_belief",
        ValueOrigin::RecordedDiscovery => "recorded_discovery",
        _ => panic!("unexpected origin in the closed player Knowledge corpus"),
    }
}

fn origin(row: &Row) -> ValueOrigin {
    match row {
        Row::Knowledge { origin, .. } => *origin,
        _ => panic!("non-Knowledge row in the player Knowledge view"),
    }
}

fn commit(engine: &mut Engine, turn: &str, intent: Intent) -> Receipt {
    let request = engine.request(turn, intent);
    let proposal = Engine::proposal(&request).expect("mechanical fixture proposal");
    let receipt = engine
        .preview(&request, &proposal)
        .expect("valid fixture action");
    engine
        .commit_prepared(&receipt)
        .expect("accepted fixture action")
}

fn action(engine: &mut Engine, turn: &str, command: Command) -> Receipt {
    commit(engine, turn, Intent::Actions(vec![command]))
}

fn dialogue(engine: &mut Engine, turn: &str, text: String) -> Receipt {
    let receipt = commit(
        engine,
        turn,
        Intent::Dialogue {
            text,
            audience: BTreeSet::from(["mira".to_owned()]),
        },
    );
    assert_eq!(receipt.events().len(), 1);
    assert!(matches!(receipt.events()[0].outcome(), Effect::Said(_)));
    assert!(receipt.events()[0].witnesses().contains("player"));
    assert!(receipt.events()[0].witnesses().contains("mira"));
    receipt
}

fn initial() -> Engine {
    let mut seed: Seed = serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json"))
        .expect("original Lantern Quay seed");
    let fact = seed.facts.get_mut(FACT).expect("fixture relic fact");
    assert_eq!(fact.proposition, OLD);
    // Domain1 correctly refuses discovering an already-known fact. Establish a
    // real later observation rather than treating seed knowledge as discovery.
    assert!(fact.known_by.remove("player"));
    fact.known_by.insert("mira".into());
    let npc = seed.beliefs.first_mut().expect("original NPC belief");
    assert_ne!(npc.believer, seed.player);
    npc.proposition = NPC_BELIEF.into();
    Engine::new(seed).expect("valid derived synthetic seed")
}

fn observed_old(engine: &Engine) {
    let observations = engine
        .observed_facts(&engine.seed().player, engine.scope(), engine.revision())
        .expect("actual player observation lens");
    assert_eq!(
        observations
            .get(FACT)
            .expect("discovered relic")
            .proposition,
        OLD
    );
}

fn pages(
    engine: &Engine,
    selected: Option<ValueOrigin>,
    forbidden: &[&str],
) -> (Vec<QueryPage>, Vec<Row>) {
    let search = selected
        .map(|value| format!("\"origin\":\"{}\"", wire_origin(value)))
        .unwrap_or_default();
    let mut query = Query {
        version: 2,
        scope: engine.scope().clone(),
        expected_head: engine.revision(),
        at_revision: None,
        observer: Observer::Player,
        view: View::Knowledge,
        cursor: None,
        limit: 8,
        search,
    };
    let mut output = Vec::new();
    let mut rows = Vec::new();
    let mut cursors = BTreeSet::new();
    let mut keys = BTreeSet::new();
    let mut previous_key: Option<String> = None;
    let mut total = None;
    let mut completed = false;
    for _ in 0..16 {
        let page = inspection_query::query(engine, &query, false)
            .expect("actual unprivileged player Knowledge Query2");
        assert_eq!(page.version, 2);
        assert_eq!(page.scope, *engine.scope());
        assert_eq!(page.head, engine.revision());
        assert_eq!(page.revision, engine.revision());
        assert_eq!(page.story_time, engine.state().story_time);
        assert_eq!(page.observer, Observer::Player);
        assert_eq!(page.view, View::Knowledge);
        assert_eq!(page.privacy, Privacy::PlayerVisible);
        assert_eq!(page.status, ViewStatus::Supported);
        assert!(page.rows.len() <= 8);
        assert!(total
            .replace(page.total)
            .is_none_or(|prior| prior == page.total));
        for row in &page.rows {
            assert!(
                ORIGINS.contains(&origin(row)),
                "player must not receive canonical truth"
            );
            if let Some(selected) = selected {
                assert_eq!(origin(row), selected);
            }
            assert!(
                keys.insert(row.key().to_owned()),
                "native paging repeated a row"
            );
            if let Some(prior) = previous_key.as_deref() {
                assert!(prior < row.key());
            }
            previous_key = Some(row.key().to_owned());
        }
        let raw = serde_json::to_vec(&page).expect("original native Page serializer");
        assert!(raw.len() < inspection_query::MAX_PAGE_BYTES);
        let text = std::str::from_utf8(&raw).expect("native JSON UTF8");
        for canary in forbidden {
            assert!(
                !text.contains(canary),
                "hidden or future canary reached player rows"
            );
        }
        let next = page.next_cursor.clone();
        rows.extend(page.rows.iter().cloned());
        output.push(QueryPage {
            query: query.clone(),
            page,
        });
        if let Some(next) = next {
            assert!(
                cursors.insert(next.clone()),
                "native cursor did not advance"
            );
            assert_ne!(query.cursor.as_deref(), Some(next.as_str()));
            query.cursor = Some(next);
        } else {
            assert_eq!(Some(rows.len()), total);
            completed = true;
            break;
        }
    }
    assert!(completed, "finite page budget exhausted");
    (output, rows)
}

fn case(
    id: &'static str,
    engine: &Engine,
    parent: &Scope,
    fork_revision: u64,
    discovery_sequence: u64,
    corrected: bool,
) -> CorpusCase {
    assert_eq!(engine.domain_version(), if corrected { 2 } else { 1 });
    assert_eq!(
        engine
            .effective_fact(FACT)
            .expect("actual truth")
            .proposition,
        if corrected { NEW } else { OLD }
    );
    observed_old(engine);
    let canonical_before = engine.canonical_bytes();
    let projection_before = engine.state().clone();
    let records_before = engine.canonical_records().to_vec();
    let basis_before = engine
        .accepted_history_basis()
        .expect("actual accepted basis");
    let mut forbidden = vec![NPC_BELIEF, NEW, AUTHOR_REASON];
    if corrected {
        forbidden.push(PARENT_ONLY);
    }
    let (all_pages, eligible) = pages(engine, None, &forbidden);
    let counts = ORIGINS.map(|value| eligible.iter().filter(|row| origin(row) == value).count());
    // Independently established by the canonical fixture actions: two observed
    // facts, nine witnessed pre-fork statements/beliefs and one discovery.
    assert_eq!(counts, [2, if corrected { 9 } else { 10 }, 9, 1]);
    let mut found_observation = false;
    let mut found_discovery = false;
    let mut found_quoted_statement = false;
    let mut parent_only_statements = 0;
    for row in &eligible {
        if let Row::Knowledge {
            id,
            subject,
            text,
            confidence,
            sources,
            origin,
            ..
        } = row
        {
            assert_eq!(subject.as_deref(), Some(engine.seed().player.as_str()));
            match origin {
                ValueOrigin::KnownAsObserved if id == FACT => {
                    assert_eq!(text, OLD);
                    assert!(confidence.is_none());
                    assert_eq!(sources.len(), 1);
                    assert!(
                        matches!(&sources[0], Source::ScopedEvent { original_scope, sequence }
                        if original_scope == parent && *sequence == discovery_sequence)
                    );
                    found_observation = true;
                }
                ValueOrigin::RecordedDiscovery => {
                    assert_eq!(id, FACT);
                    assert_eq!(text, OLD);
                    assert!(confidence.is_none());
                    assert_eq!(sources.len(), 1);
                    assert!(
                        matches!(&sources[0], Source::ScopedEvent { original_scope, sequence }
                        if original_scope == parent && *sequence == discovery_sequence)
                    );
                    found_discovery = true;
                }
                ValueOrigin::RecordedStatement => {
                    assert!(confidence.is_none());
                    assert_eq!(sources.len(), 1);
                    found_quoted_statement |= text.contains(QUOTED_ORIGINS);
                    parent_only_statements += usize::from(text == PARENT_ONLY);
                }
                ValueOrigin::SubjectiveBelief => {
                    assert_eq!(confidence.as_ref(), Some(&Confidence::Uncertain));
                    assert_eq!(sources.len(), 2);
                }
                _ => {}
            }
            for source in sources {
                if let Source::ScopedEvent {
                    original_scope,
                    sequence,
                } = source
                {
                    assert_eq!(original_scope, parent);
                    assert!(*sequence > 0 && *sequence <= engine.revision());
                    if corrected {
                        assert!(*sequence <= fork_revision);
                    }
                }
            }
        }
    }
    assert!(found_observation && found_discovery && found_quoted_statement);
    assert_eq!(parent_only_statements, usize::from(!corrected));
    let mut filters = vec![FilterPages {
        origin: None,
        pages: all_pages,
    }];
    for selected in ORIGINS {
        let expected: Vec<Row> = eligible
            .iter()
            .filter(|row| origin(row) == selected)
            .cloned()
            .collect();
        let (actual_pages, actual_rows) = pages(engine, Some(selected), &forbidden);
        assert!(
            actual_rows == expected,
            "facet must preserve exact eligible typed rows and provenance"
        );
        if selected == ValueOrigin::SubjectiveBelief {
            assert!(actual_pages.len() >= 2);
        }
        filters.push(FilterPages {
            origin: Some(wire_origin(selected)),
            pages: actual_pages,
        });
    }
    // No assertion dumps raw canonical/private author records on failure.
    assert!(
        engine.canonical_bytes() == canonical_before,
        "reads changed canonical bytes"
    );
    assert!(
        engine.state() == &projection_before,
        "reads changed mechanical projection"
    );
    assert!(
        engine.canonical_records() == records_before.as_slice(),
        "reads changed history"
    );
    assert!(engine.accepted_history_basis().expect("basis after reads") == basis_before);
    observed_old(engine);
    CorpusCase {
        id,
        domain_version: engine.domain_version(),
        player: engine.seed().player.clone(),
        scope: engine.scope().clone(),
        head: engine.revision(),
        story_time: engine.state().story_time,
        forbidden,
        filters,
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = std::env::args_os().skip(1).collect();
    let check = match args.as_slice() {
        [] => false,
        [arg] if arg == "--check" => true,
        _ => return Err("Usage: android_knowledge_filter_fixture [--check]".into()),
    };
    let mut parent = initial();
    let parent_scope = parent.scope().clone();
    for index in 0..9 {
        let receipt = dialogue(
            &mut parent,
            &format!("knowledge-say-{index}"),
            format!("Witness note {index}: {QUOTED_ORIGINS}"),
        );
        action(
            &mut parent,
            &format!("knowledge-believe-{index}"),
            Command::Believe {
                claim_event: receipt.events()[0].sequence(),
            },
        );
    }
    action(
        &mut parent,
        "knowledge-well",
        Command::Move {
            to: "dry-well".into(),
        },
    );
    let discovery = action(
        &mut parent,
        "knowledge-discover",
        Command::Discover { fact: FACT.into() },
    );
    assert_eq!(discovery.events().len(), 1);
    assert!(
        matches!(discovery.events()[0].outcome(), Effect::Discovered { actor, fact }
        if actor == "player" && fact == FACT)
    );
    let discovery_sequence = discovery.events()[0].sequence();
    action(
        &mut parent,
        "knowledge-return",
        Command::Move { to: "quay".into() },
    );
    let fork_revision = parent.revision();
    let correction = AuthorCorrectionInputV1 {
        version: 1,
        parent: parent_scope.clone(),
        expected_parent_revision: fork_revision,
        fork_revision,
        child_branch: "knowledge-corrected".into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: FACT.into(),
            expected_proposition: OLD.into(),
            replacement: NEW.into(),
        },
        reason: AUTHOR_REASON.into(),
    };
    let prepared = parent.prepare_author_correction(&correction, &|| false)?;
    let corrected = parent.apply_author_correction(&prepared, &|| false)?.engine;
    dialogue(&mut parent, "knowledge-parent-later", PARENT_ONLY.into());
    // Equal numeric heads do not make a later parent event eligible in a child.
    assert_eq!(parent.revision(), corrected.revision());
    let corpus = Corpus {
        version: 1,
        cases: vec![
            case(
                "parent",
                &parent,
                &parent_scope,
                fork_revision,
                discovery_sequence,
                false,
            ),
            case(
                "corrected",
                &corrected,
                &parent_scope,
                fork_revision,
                discovery_sequence,
                true,
            ),
        ],
    };
    let mut encoded = serde_json::to_vec(&corpus)?;
    encoded.push(b'\n');
    assert!(encoded.len() <= 128 * 1024, "corpus stdout budget exceeded");
    if check {
        let expected = include_bytes!(concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/../../apps/android/app/src/test/resources/story-record-knowledge-filters-v1.json"
        ));
        if encoded.as_slice() != expected {
            return Err(
                "Knowledge corpus differs from Rust outcomes; review regenerated stdout".into(),
            );
        }
        println!("Knowledge corpus matches Rust engine bytes.");
        return Ok(());
    }
    let mut stdout = io::stdout().lock();
    stdout.write_all(&encoded)?;
    Ok(())
}
