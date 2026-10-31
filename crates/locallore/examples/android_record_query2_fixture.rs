// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Synthetic mechanical histories and actual Player Query2 pages for Android.
//! No provider, model, file writes or manually constructed inspector rows.
use locallore::{
    author_correction::{AuthorCorrectionInputV1, AuthorCorrectionOperationV1},
    contracts::*,
    engine::Engine,
    inspection_query::{
        self, FieldValue, Observer, Privacy, Query, Row, Source, ValueOrigin, View, ViewStatus,
    },
    story_authoring::{
        self, InitialGenerationV1, InitialModelConfigurationV1, InitialPossessionV1,
        InitialProviderKindV1, InitialRouteV1, InitialStoryInputV1, InitialWorldOriginV1,
        InitialWorldProposalV1,
    },
};
use serde_json::{json, Value};
use std::{
    collections::BTreeSet,
    io::{self, Write},
};

const FACT_ID: &str = "relic-location";
const OLD: &str = "The survey beacon flashes amber at the north pier.";
const NEW: &str = "The survey beacon flashes violet at the north pier.";
const NPC_NAME: &str = "PRIVATE_NPC_NAME_B37";
const NPC_SHEET: &str = "PRIVATE_NPC_SHEET_B37";
const NPC_BELIEF: &str = "PRIVATE_NPC_BELIEF_B37";
const HIDDEN_FACT: &str = "PRIVATE_UNOBSERVED_REGISTER_B37";
const AUTHOR_REASON: &str = "PRIVATE_AUTHOR_CORRECTION_REASON_B37";
const AUTHORED_REMOTE: &str = "PRIVATE_AUTHORED_REMOTE_DESCRIPTION_B37";

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
            "standing-offer":{"from":"player","to":"mentor","terms":"Share the completed channel survey.","deadline":100,
                "source":{"kind":"seed","value":"north-pier-survey-v1"},"return_item":null,"completed_by":null}
        }
    })).expect("valid original synthetic seed encoding");
    Engine::new(seed).expect("valid original synthetic seed")
}

fn commit(engine: &mut Engine, turn: &str, intent: Intent) -> Receipt {
    let request = engine.request(turn, intent);
    let proposal = Engine::proposal(&request).expect("mechanical fixture proposal");
    let preview = engine
        .preview(&request, &proposal)
        .expect("mechanically valid fixture action");
    engine
        .commit_prepared(&preview)
        .expect("accepted exact mechanical fixture action")
}

fn actions(engine: &mut Engine, turn: &str, commands: Vec<Command>) -> Receipt {
    commit(engine, turn, Intent::Actions(commands))
}

fn observed(engine: &Engine, fact: &str) -> String {
    engine
        .observed_facts(&engine.seed().player, engine.scope(), engine.revision())
        .expect("actual actor lens")
        .get(fact)
        .expect("actual discovered fact")
        .proposition
        .clone()
}

fn source_is(source: &Source, scope: &Scope) -> bool {
    matches!(source, Source::ScopedEvent { original_scope, .. } if original_scope == scope)
}

fn corpus_case(
    id: &str,
    engine: &Engine,
    original_scope: &Scope,
    fact_id: &str,
    expected: &str,
) -> Value {
    let before = engine.canonical_bytes();
    let records = engine.canonical_records().to_vec();
    let basis = engine
        .accepted_history_basis()
        .expect("complete accepted history basis");
    let player = engine.seed().player.as_str();
    let authored = engine.seed().initial_world.is_some();
    if !authored {
        // The helpful gift changed an incoming edge in actual canonical state.
        // Player Relationships intentionally exposes only outgoing edges.
        assert!(engine
            .state()
            .relationships
            .iter()
            .any(|edge| edge.from == "mentor" && edge.to == player && edge.obligation == 1));
    }
    let mut forbidden = vec![
        NPC_NAME,
        NPC_SHEET,
        NPC_BELIEF,
        HIDDEN_FACT,
        AUTHOR_REASON,
        AUTHORED_REMOTE,
    ];
    if id != "rediscovered" {
        forbidden.push(NEW);
    }
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
    for view in [
        View::Profiles,
        View::History,
        View::Relationships,
        View::Knowledge,
        View::Promises,
    ] {
        let mut query = Query {
            version: 2,
            scope: engine.scope().clone(),
            expected_head: engine.revision(),
            at_revision: None,
            observer: Observer::Player,
            view,
            cursor: None,
            limit: 8,
            search: String::new(),
        };
        let mut cursors = BTreeSet::new();
        let mut complete = false;
        let mut count = 0;
        let mut total = None;
        for _ in 0..16 {
            let page = inspection_query::query(engine, &query, false)
                .expect("actual bounded Player Query2");
            assert_eq!(page.version, 2);
            assert_eq!(page.scope, *engine.scope());
            assert_eq!(page.head, engine.revision());
            assert_eq!(page.revision, engine.revision());
            assert_eq!(page.observer, Observer::Player);
            assert_eq!(page.privacy, Privacy::PlayerVisible);
            assert_eq!(page.status, ViewStatus::Supported);
            assert!(page.rows.len() <= 8);
            assert!(total
                .replace(page.total)
                .is_none_or(|prior| prior == page.total));
            count += page.rows.len();
            for row in &page.rows {
                match row {
                    Row::Field {
                        actor,
                        field,
                        value,
                        source,
                        ..
                    } => {
                        assert_eq!(actor, player);
                        progression |= source_is(source, original_scope)
                            && if authored {
                                field == "location"
                            } else {
                                field == "ability/measure" && *value == FieldValue::Number(1)
                            };
                    }
                    Row::Relationship {
                        from,
                        to,
                        dimension,
                        value,
                        source,
                        ..
                    } => {
                        assert_eq!(from, player, "native Player view is outgoing only");
                        relationship |= matches!(source, Source::Seed(_))
                            && if authored {
                                dimension == "trust" && *value == 0
                            } else {
                                to == "mentor" && dimension == "trust" && *value == 1
                            };
                    }
                    Row::Knowledge {
                        id,
                        subject,
                        text,
                        confidence,
                        sources,
                        origin: ValueOrigin::KnownAsObserved,
                        ..
                    } if id == fact_id => {
                        assert_eq!(subject.as_deref(), Some(player));
                        assert!(confidence.is_none());
                        assert_eq!(text, expected);
                        let observed_scope = if expected == NEW {
                            engine.scope()
                        } else {
                            original_scope
                        };
                        assert_eq!(sources.len(), 1);
                        assert!(source_is(&sources[0], observed_scope));
                        known = true;
                    }
                    Row::Knowledge {
                        origin: ValueOrigin::RecordedStatement,
                        ..
                    } => statement = true,
                    Row::Knowledge {
                        origin: ValueOrigin::SubjectiveBelief,
                        ..
                    } => belief = true,
                    Row::Knowledge {
                        origin: ValueOrigin::RecordedDiscovery,
                        ..
                    } => discovery = true,
                    Row::ScopedMessage {
                        original_scope: scope,
                        message_kind,
                        event_ids,
                        ..
                    } => {
                        assert!(
                            !event_ids.is_empty()
                                && event_ids.windows(2).all(|pair| pair[0] < pair[1])
                        );
                        if scope == original_scope {
                            input |= message_kind == "original_input";
                            narration |= message_kind == "narration";
                        }
                    }
                    Row::AuthorCorrection { revision, .. } => {
                        assert!(engine.domain_version() == 2 && *revision <= engine.revision());
                        marker = true;
                    }
                    Row::Promise { status, .. } => {
                        statuses.insert(status.clone());
                    }
                    _ => {}
                }
            }
            let raw = serde_json::to_vec(&page).expect("unmodified native page encoding");
            assert!(raw.len() <= inspection_query::MAX_PAGE_BYTES);
            let text = std::str::from_utf8(&raw).expect("native JSON UTF8");
            for canary in &forbidden {
                assert!(
                    !text.contains(canary),
                    "private synthetic value reached a Player page"
                );
            }
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
    assert_eq!(marker, engine.domain_version() == 2);
    if authored {
        assert_eq!(statuses, BTreeSet::from(["open".to_owned()]));
    } else {
        assert_eq!(
            statuses,
            BTreeSet::from([
                "open".to_owned(),
                "overdue".to_owned(),
                "fulfilled".to_owned()
            ])
        );
    }
    assert!(paginated_views.contains("\"profiles\"") && paginated_views.contains("\"history\""));
    // Do not dump raw canonical/private author payloads even if conservation fails.
    assert!(engine.canonical_bytes() == before);
    assert!(engine.canonical_records() == records.as_slice());
    assert!(
        engine
            .accepted_history_basis()
            .expect("history remains valid")
            == basis
    );
    json!({"id":id,"domain_version":engine.domain_version(),"player":engine.seed().player,"scope":engine.scope(),
        "head":engine.revision(),"story_time":engine.state().story_time,
        "forbidden":forbidden,"pages":pages})
}

fn authored_histories() -> Result<(Engine, Engine, String), Box<dyn std::error::Error>> {
    let mut input: InitialStoryInputV1 = serde_json::from_str(include_str!(
        "../../../fixtures/initial_world/ashglass-input.json"
    ))?;
    let mut accepted: InitialWorldProposalV1 = serde_json::from_str(include_str!(
        "../../../fixtures/initial_world/ashglass-proposal.json"
    ))?;
    input.cast[1].name = NPC_NAME.into();
    accepted.characters[1].name = NPC_NAME.into();
    accepted.characters[0].location = 0;
    accepted.characters[0].description = NPC_SHEET.into();
    accepted.characters[0].known_by = vec![1];
    accepted.characters[1].description = NPC_SHEET.into();
    accepted.characters[1].known_by = vec![2];
    accepted.locations[1].description = AUTHORED_REMOTE.into();
    accepted.facts[0].text = OLD.into();
    accepted.facts[0].known_by.clear();
    accepted.facts[0].discoverable_at = Some(0);
    accepted.facts[1].text = HIDDEN_FACT.into();
    accepted.beliefs[0].text = NPC_BELIEF.into();
    accepted.routes.push(InitialRouteV1 { from: 1, to: 0 });
    accepted.possessions.push(InitialPossessionV1 {
        name: "Survey cord".into(),
        description: "A short marked survey cord.".into(),
        owner: 0,
        return_to: None,
    });
    story_authoring::validate_proposal(&input, &accepted)
        .expect("valid authored synthetic proposal");
    let profile = locallore::play::PlayProfile {
        id: "query2-authored-synthetic-v1".into(),
        model_sha256: "a".repeat(64),
        runtime_revision: "b".repeat(40),
        template_sha256: "c".repeat(64),
        worker_sha256: "d".repeat(64),
        profile_manifest_sha256: "e".repeat(64),
        context_tokens: 4096,
        director_tokens: 350,
        narrator_tokens: 350,
        deadline_ms: 5000,
        repair_limit: 1,
    };
    let response = serde_json::to_string(&accepted)?;
    let origin = InitialWorldOriginV1 {
        version: 1,
        generation: InitialGenerationV1 {
            input: input.clone(),
            proposal: accepted.clone(),
            model_profile: profile.id.clone(),
            model_configuration: InitialModelConfigurationV1::from(&profile),
            provider: InitialProviderKindV1::Scripted,
            prompt_version: story_authoring::PROMPT_VERSION.into(),
            schema_version: story_authoring::SCHEMA_VERSION.into(),
            response_sha256: locallore::inspection::sha256(response.as_bytes()),
            response,
        },
        reviewed: input,
        accepted,
        title: "Synthetic materialized Query2 survey".into(),
    };
    let seed = story_authoring::materialize(
        &origin,
        Scope {
            story: "authored-query2-b37".into(),
            branch: "main".into(),
        },
    )
    .expect("actual typed authored materialization");
    story_authoring::validate_origin(&seed).expect("exact authored origin");
    assert!(seed.player.starts_with("a-") && seed.player != "player");
    let prefix = seed
        .id
        .strip_prefix("world-")
        .expect("materialized world namespace");
    let fact_id = format!("f-{prefix}-world-0");
    let mentor = format!("a-{prefix}-1");
    let other = format!("l-{prefix}-1");
    let local = seed.actors[&seed.player].location.clone();
    let mut root = Engine::new(seed)?;
    assert_eq!(root.domain_version(), 1);
    actions(
        &mut root,
        "authored-outward",
        vec![Command::Move { to: other }],
    );
    actions(
        &mut root,
        "authored-return",
        vec![Command::Move { to: local }],
    );
    let statement = commit(
        &mut root,
        "authored-spoken",
        Intent::Dialogue {
            text: "I will return the survey notes before the bell.".into(),
            audience: [mentor.clone()].into(),
        },
    );
    actions(
        &mut root,
        "authored-belief",
        vec![Command::Believe {
            claim_event: statement.events()[0].sequence(),
        }],
    );
    actions(
        &mut root,
        "authored-observe",
        vec![Command::Discover {
            fact: fact_id.clone(),
        }],
    );
    actions(
        &mut root,
        "authored-promise",
        vec![Command::Promise {
            id: "survey-report".into(),
            to: mentor,
            terms: "Bring the report before the next bell.".into(),
            deadline: 20,
            return_item: None,
        }],
    );
    actions(
        &mut root,
        "authored-clock",
        vec![Command::Wait { ticks: 1 }],
    );
    assert_eq!(root.domain_version(), 1);
    assert_eq!(observed(&root, &fact_id), OLD);
    let correction = AuthorCorrectionInputV1 {
        version: 1,
        parent: root.scope().clone(),
        expected_parent_revision: root.revision(),
        fork_revision: root.revision(),
        child_branch: "authored-corrected".into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: fact_id.clone(),
            expected_proposition: OLD.into(),
            replacement: NEW.into(),
        },
        reason: AUTHOR_REASON.into(),
    };
    let prepared = root.prepare_author_correction(&correction, &|| false)?;
    let child = root.apply_author_correction(&prepared, &|| false)?.engine;
    assert_eq!(child.domain_version(), 2);
    assert_eq!(observed(&child, &fact_id), OLD);
    assert_eq!(child.effective_fact(&fact_id)?.proposition, NEW);
    Ok((root, child, fact_id))
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut root = initial();
    actions(
        &mut root,
        "learn-survey",
        vec![Command::Learn {
            ability: "measure".into(),
        }],
    );
    actions(
        &mut root,
        "use-survey",
        vec![Command::UseAbility {
            ability: "measure".into(),
        }],
    );
    actions(
        &mut root,
        "help-surveyor",
        vec![Command::Give {
            item: "tonic".into(),
            to: "mentor".into(),
            quantity: 1,
        }],
    );
    let statement = commit(
        &mut root,
        "spoken-survey",
        Intent::Dialogue {
            text: "The painted wheel might be jammed.".into(),
            audience: ["mentor".into()].into(),
        },
    );
    let statement_id = statement.events()[0].sequence();
    actions(
        &mut root,
        "uncertain-belief",
        vec![Command::Believe {
            claim_event: statement_id,
        }],
    );
    actions(
        &mut root,
        "observe-beacon",
        vec![Command::Discover {
            fact: FACT_ID.into(),
        }],
    );
    actions(
        &mut root,
        "return-caliper",
        vec![
            Command::Promise {
                id: "return-caliper".into(),
                to: "mentor".into(),
                terms: "Return the borrowed caliper before afternoon.".into(),
                deadline: 20,
                return_item: Some("caliper".into()),
            },
            Command::Give {
                item: "caliper".into(),
                to: "mentor".into(),
                quantity: 1,
            },
            Command::CompletePromise {
                id: "return-caliper".into(),
            },
        ],
    );
    actions(&mut root, "tide-clock", vec![Command::Wait { ticks: 3 }]);
    assert_eq!(root.domain_version(), 1);
    assert_eq!(observed(&root, FACT_ID), OLD);
    let input = AuthorCorrectionInputV1 {
        version: 1,
        parent: root.scope().clone(),
        expected_parent_revision: root.revision(),
        fork_revision: root.revision(),
        child_branch: "corrected-beacon".into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: FACT_ID.into(),
            expected_proposition: OLD.into(),
            replacement: NEW.into(),
        },
        reason: AUTHOR_REASON.into(),
    };
    let prepared = root.prepare_author_correction(&input, &|| false)?;
    let corrected = root.apply_author_correction(&prepared, &|| false)?.engine;
    assert_eq!(corrected.domain_version(), 2);
    assert_eq!(observed(&corrected, FACT_ID), OLD);
    assert_eq!(corrected.effective_fact(FACT_ID)?.proposition, NEW);
    let mut rediscovered = corrected.clone();
    actions(
        &mut rediscovered,
        "observe-corrected-beacon",
        vec![Command::Discover {
            fact: FACT_ID.into(),
        }],
    );
    assert_eq!(rediscovered.domain_version(), 2);
    assert_eq!(observed(&rediscovered, FACT_ID), NEW);
    let (authored, authored_corrected, authored_fact) = authored_histories()?;
    let payload = json!({"version":1,"cases":[
        corpus_case("root", &root, root.scope(), FACT_ID, OLD),
        corpus_case("corrected", &corrected, root.scope(), FACT_ID, OLD),
        corpus_case("rediscovered", &rediscovered, root.scope(), FACT_ID, NEW),
        corpus_case("authored", &authored, authored.scope(), &authored_fact, OLD),
        corpus_case("authored_corrected", &authored_corrected, authored.scope(), &authored_fact, OLD),
    ]});
    let bytes = serde_json::to_vec(&payload)?;
    assert!(
        bytes.len() < 128 * 1024,
        "compact corpus stdout budget exceeded"
    );
    let mut stdout = io::stdout().lock();
    stdout.write_all(&bytes)?;
    stdout.write_all(b"\n")?;
    Ok(())
}
