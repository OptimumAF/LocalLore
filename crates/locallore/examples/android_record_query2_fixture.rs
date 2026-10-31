// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Synthetic mechanical histories and actual Player Query2 pages for Android.
//! No provider, model, file writes or manually constructed inspector rows.
use locallore::{
    author_correction::{AuthorCorrectionInputV1, AuthorCorrectionOperationV1},
    contracts::*,
    engine::Engine,
    inspection_query::{self, FieldValue, Observer, Privacy, Query, Row, Source, ValueOrigin, View, ViewStatus},
};
use serde_json::{json, Value};
use std::{collections::BTreeSet, io::{self, Write}};

const FACT_ID: &str = "relic-location";
const OLD: &str = "The survey beacon flashes amber at the north pier.";
const NEW: &str = "The survey beacon flashes violet at the north pier.";
const NPC_NAME: &str = "PRIVATE_NPC_NAME_B37";
const NPC_SHEET: &str = "PRIVATE_NPC_SHEET_B37";
const NPC_BELIEF: &str = "PRIVATE_NPC_BELIEF_B37";
const HIDDEN_FACT: &str = "PRIVATE_UNOBSERVED_REGISTER_B37";
const AUTHOR_REASON: &str = "PRIVATE_AUTHOR_CORRECTION_REASON_B37";

fn initial() -> Engine {
    let seed: Seed = serde_json::from_value(json!({
        "version":1,"id":"north-pier-survey-v1",
        "scope":{"story":"survey-fixture-b37","branch":"main"},
        "profile":"fantasy_v1","player":"player",
        "locations":["north-pier","chart-room","sealed-loft"],
        "routes":[["north-pier","chart-room"],["chart-room","north-pier"]],
        "actors":{
            "player":{"name":"Mae","location":"north-pier","alive":true,"energy":6,
                "abilities":{},"attributes":{"focus":2},"injuries":["scratched-thumb"],
                "affiliations":["survey-guild"],"goals":["map-the-waterway"]},
            "mentor":{"name":"Nia","location":"north-pier","alive":true,"energy":5,
                "abilities":{"measure":2},"attributes":{},"injuries":[],"affiliations":[],"goals":[]},
            "private-npc":{"name":NPC_NAME,"location":"sealed-loft","alive":true,"energy":0,
                "abilities":{},"attributes":{},"injuries":[],"affiliations":[NPC_SHEET],"goals":[]}
        },
        "items":{
            "tonic":{"owner":"player","quantity":1,"return_to":null,"healing":true},
            "caliper":{"owner":"player","quantity":1,"return_to":"mentor","healing":false}
        },
        "abilities":{"measure":{"cost":1,"prerequisite":null,"teacher":"mentor","max_rank":2}},
        "facts":{
            "relic-location":{"proposition":OLD,"discoverable_at":"north-pier","known_by":["mentor"]},
            "private-register":{"proposition":HIDDEN_FACT,"discoverable_at":"sealed-loft","known_by":["private-npc"]}
        },
        "relationships":[
            {"from":"mentor","to":"player","respect":1,"trust":2,"obligation":0},
            {"from":"player","to":"mentor","respect":0,"trust":1,"obligation":0}
        ],
        "story_time":10,
        "beliefs":[{"believer":"private-npc","proposition":NPC_BELIEF,"source_claim":null,
            "source":{"kind":"seed","value":"north-pier-survey-v1"},"confidence":"believed"}],
        "commitments":{
            "missed-sketch":{"from":"player","to":"mentor","terms":"Bring the early sketch.","deadline":9,
                "source":{"kind":"seed","value":"north-pier-survey-v1"},"return_item":null,"completed_by":null},
            "standing-offer":{"from":"mentor","to":"player","terms":"Share the completed channel survey.","deadline":100,
                "source":{"kind":"seed","value":"north-pier-survey-v1"},"return_item":null,"completed_by":null}
        }
    })).expect("valid original synthetic seed encoding");
    Engine::new(seed).expect("valid original synthetic seed")
}

fn commit(engine: &mut Engine, turn: &str, intent: Intent) -> Receipt {
    let request = engine.request(turn, intent);
    let proposal = Engine::proposal(&request).expect("mechanical fixture proposal");
    let preview = engine.preview(&request, &proposal).expect("mechanically valid fixture action");
    engine.commit_prepared(&preview).expect("accepted exact mechanical fixture action")
}

fn actions(engine: &mut Engine, turn: &str, commands: Vec<Command>) -> Receipt {
    commit(engine, turn, Intent::Actions(commands))
}

fn observed(engine: &Engine) -> String {
    engine.observed_facts(&engine.seed().player, engine.scope(), engine.revision())
        .expect("actual actor lens").get(FACT_ID).expect("actual discovered fact").proposition.clone()
}

fn source_is(source: &Source, scope: &Scope) -> bool {
    matches!(source, Source::ScopedEvent { original_scope, .. } if original_scope == scope)
}

fn corpus_case(id: &str, engine: &Engine, original_scope: &Scope, expected: &str) -> Value {
    let before = engine.canonical_bytes();
    let records = engine.canonical_records().to_vec();
    let basis = engine.accepted_history_basis().expect("complete accepted history basis");
    let mut forbidden = vec![NPC_NAME, NPC_SHEET, NPC_BELIEF, HIDDEN_FACT, AUTHOR_REASON];
    if id != "rediscovered" { forbidden.push(NEW); }
    let mut pages = Vec::new();
    let mut progression = false;
    let mut relationship = false;
    let mut known = false;
    let mut statement = false;
    let mut belief = false;
    let mut discovery = false;
    let mut input = false;
    let mut narration = false;
    let mut marker = false;
    let mut statuses = BTreeSet::new();
    let mut paginated_views = BTreeSet::new();
    for view in [View::Profiles, View::History, View::Relationships, View::Knowledge, View::Promises] {
        let mut query = Query {
            version: 2, scope: engine.scope().clone(), expected_head: engine.revision(),
            at_revision: None, observer: Observer::Player, view, cursor: None,
            limit: 8, search: String::new(),
        };
        let mut cursors = BTreeSet::new();
        let mut complete = false;
        let mut count = 0;
        let mut total = None;
        for _ in 0..16 {
            let page = inspection_query::query(engine, &query, false).expect("actual bounded Player Query2");
            assert_eq!(page.version, 2);
            assert_eq!(page.scope, *engine.scope());
            assert_eq!(page.head, engine.revision());
            assert_eq!(page.revision, engine.revision());
            assert_eq!(page.observer, Observer::Player);
            assert_eq!(page.privacy, Privacy::PlayerVisible);
            assert_eq!(page.status, ViewStatus::Supported);
            assert!(page.rows.len() <= 8);
            assert!(total.replace(page.total).is_none_or(|prior| prior == page.total));
            count += page.rows.len();
            for row in &page.rows {
                match row {
                    Row::Field { actor, field, value: FieldValue::Number(1), source, .. }
                        if actor == "player" && field == "ability/measure" && source_is(source, original_scope) => progression = true,
                    Row::Relationship { from, to, dimension, value: 1, source, .. }
                        if from == "mentor" && to == "player" && dimension == "obligation" && source_is(source, original_scope) => relationship = true,
                    Row::Knowledge { id, subject, text, confidence, origin: ValueOrigin::KnownAsObserved, .. }
                        if id == FACT_ID => {
                            assert_eq!(subject.as_deref(), Some("player"));
                            assert!(confidence.is_none());
                            assert_eq!(text, expected);
                            known = true;
                        }
                    Row::Knowledge { origin: ValueOrigin::RecordedStatement, .. } => statement = true,
                    Row::Knowledge { origin: ValueOrigin::SubjectiveBelief, .. } => belief = true,
                    Row::Knowledge { origin: ValueOrigin::RecordedDiscovery, .. } => discovery = true,
                    Row::ScopedMessage { original_scope: scope, message_kind, event_ids, .. } => {
                        assert!(!event_ids.is_empty() && event_ids.windows(2).all(|pair| pair[0] < pair[1]));
                        if scope == original_scope {
                            input |= message_kind == "original_input";
                            narration |= message_kind == "narration";
                        }
                    }
                    Row::AuthorCorrection { revision, .. } => {
                        assert!(id != "root" && *revision <= engine.revision());
                        marker = true;
                    }
                    Row::Promise { status, .. } => { statuses.insert(status.clone()); }
                    _ => {}
                }
            }
            let raw = serde_json::to_vec(&page).expect("unmodified native page encoding");
            assert!(raw.len() <= inspection_query::MAX_PAGE_BYTES);
            let text = std::str::from_utf8(&raw).expect("native JSON UTF8");
            for canary in &forbidden { assert!(!text.contains(canary), "private synthetic value reached a Player page"); }
            let next = page.next_cursor.clone();
            pages.push(json!({"query":&query,"page":&page}));
            if let Some(next) = next {
                assert!(cursors.insert(next.clone()), "native cursor must advance");
                paginated_views.insert(serde_json::to_string(&view).unwrap());
                query.cursor = Some(next);
            } else {
                assert_eq!(Some(count), total);
                complete = true;
                break;
            }
        }
        assert!(complete, "finite fixture page budget exhausted");
    }
    assert!(progression && relationship && known && statement && belief && discovery);
    assert!(input && narration);
    assert_eq!(marker, id != "root");
    assert_eq!(statuses, BTreeSet::from(["open".to_owned(), "overdue".to_owned(), "fulfilled".to_owned()]));
    assert!(paginated_views.contains("\"profiles\"") && paginated_views.contains("\"history\""));
    // Do not dump raw canonical/private author payloads even if conservation fails.
    assert!(engine.canonical_bytes() == before);
    assert!(engine.canonical_records() == records.as_slice());
    assert!(engine.accepted_history_basis().expect("history remains valid") == basis);
    json!({"id":id,"domain_version":engine.domain_version(),"scope":engine.scope(),
        "head":engine.revision(),"story_time":engine.state().story_time,
        "forbidden":forbidden,"pages":pages})
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut root = initial();
    actions(&mut root, "learn-survey", vec![Command::Learn { ability: "measure".into() }]);
    actions(&mut root, "use-survey", vec![Command::UseAbility { ability: "measure".into() }]);
    actions(&mut root, "help-surveyor", vec![Command::Give { item: "tonic".into(), to: "mentor".into(), quantity: 1 }]);
    let statement = commit(&mut root, "spoken-survey", Intent::Dialogue {
        text: "The painted wheel might be jammed.".into(), audience: ["mentor".into()].into(),
    });
    let statement_id = statement.events()[0].sequence();
    actions(&mut root, "uncertain-belief", vec![Command::Believe { claim_event: statement_id }]);
    actions(&mut root, "observe-beacon", vec![Command::Discover { fact: FACT_ID.into() }]);
    actions(&mut root, "return-caliper", vec![
        Command::Promise { id: "return-caliper".into(), to: "mentor".into(),
            terms: "Return the borrowed caliper before afternoon.".into(), deadline: 20, return_item: Some("caliper".into()) },
        Command::Give { item: "caliper".into(), to: "mentor".into(), quantity: 1 },
        Command::CompletePromise { id: "return-caliper".into() },
    ]);
    actions(&mut root, "tide-clock", vec![Command::Wait { ticks: 3 }]);
    assert_eq!(root.domain_version(), 1);
    assert_eq!(observed(&root), OLD);
    let input = AuthorCorrectionInputV1 {
        version: 1, parent: root.scope().clone(), expected_parent_revision: root.revision(),
        fork_revision: root.revision(), child_branch: "corrected-beacon".into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: FACT_ID.into(), expected_proposition: OLD.into(), replacement: NEW.into(),
        }, reason: AUTHOR_REASON.into(),
    };
    let prepared = root.prepare_author_correction(&input, &|| false)?;
    let corrected = root.apply_author_correction(&prepared, &|| false)?.engine;
    assert_eq!(corrected.domain_version(), 2);
    assert_eq!(observed(&corrected), OLD);
    assert_eq!(corrected.effective_fact(FACT_ID)?.proposition, NEW);
    let mut rediscovered = corrected.clone();
    actions(&mut rediscovered, "observe-corrected-beacon", vec![Command::Discover { fact: FACT_ID.into() }]);
    assert_eq!(rediscovered.domain_version(), 2);
    assert_eq!(observed(&rediscovered), NEW);
    let payload = json!({"version":1,"cases":[
        corpus_case("root", &root, root.scope(), OLD),
        corpus_case("corrected", &corrected, root.scope(), OLD),
        corpus_case("rediscovered", &rediscovered, root.scope(), NEW),
    ]});
    let bytes = serde_json::to_vec(&payload)?;
    assert!(bytes.len() + 1 <= 128 * 1024, "compact corpus stdout budget exceeded");
    let mut stdout = io::stdout().lock();
    stdout.write_all(&bytes)?;
    stdout.write_all(b"\n")?;
    Ok(())
}
