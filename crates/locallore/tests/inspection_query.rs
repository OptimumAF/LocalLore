#![cfg(feature = "host")]
use contracts::*;
use engine::Engine;
use inspection_query::*;
use locallore::{contracts, engine, inspection_query};
use std::collections::BTreeSet;

const PRIVATE: &str = "NPC-PRIVATE-CANARY-8841";
fn seed() -> Seed {
    serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap()
}
fn private_engine() -> Engine {
    let mut s = seed();
    s.actors.get_mut("sable").unwrap().name = PRIVATE.into();
    s.facts.insert(
        "hidden-fact".into(),
        Fact {
            proposition: PRIVATE.into(),
            discoverable_at: None,
            known_by: ["sable".into()].into(),
        },
    );
    s.beliefs.insert(
        0,
        Belief {
            believer: "sable".into(),
            proposition: PRIVATE.into(),
            source_claim: None,
            source: Evidence::Seed(s.id.clone()),
            confidence: Confidence::Believed,
        },
    );
    s.commitments.insert(
        "hidden-incoming".into(),
        Commitment {
            from: "sable".into(),
            to: "player".into(),
            terms: PRIVATE.into(),
            deadline: 300,
            source: Evidence::Seed(s.id.clone()),
            return_item: None,
            completed_by: None,
        },
    );
    s.items.insert(
        "private-item".into(),
        Item {
            owner: "sable".into(),
            quantity: 1,
            return_to: None,
            healing: false,
        },
    );
    Engine::new(s).unwrap()
}
fn request(engine: &Engine, view: View) -> Query {
    Query {
        version: QUERY_VERSION,
        scope: engine.scope().clone(),
        expected_head: engine.revision(),
        at_revision: None,
        observer: Observer::Player,
        view,
        cursor: None,
        limit: MAX_ROWS,
        search: String::new(),
    }
}
fn commit(engine: &mut Engine, turn: &str, commands: Vec<Command>) -> Receipt {
    let request = engine.request(turn, Intent::Actions(commands));
    let proposal = Engine::proposal(&request).unwrap();
    let preview = engine.preview(&request, &proposal).unwrap();
    engine
        .commit(&request, &proposal, preview.narration())
        .unwrap()
}
fn all_rows(engine: &Engine, mut q: Query, grant: bool) -> Vec<Row> {
    let mut out = vec![];
    let mut cursors = BTreeSet::new();
    loop {
        let page = query(engine, &q, grant).unwrap();
        assert!(page.rows.len() <= q.limit as usize);
        assert!(serde_json::to_vec(&page).unwrap().len() <= MAX_PAGE_BYTES);
        out.extend(page.rows);
        match page.next_cursor {
            None => {
                assert_eq!(page.total, out.len());
                return out;
            }
            Some(cursor) => {
                assert!(cursor.len() <= MAX_CURSOR_BYTES);
                assert!(cursors.insert(cursor.clone()));
                q.cursor = Some(cursor);
            }
        }
        assert!(out.len() < 65_536);
    }
}

#[test]
fn hidden_canaries_never_enter_player_search_count_page_or_provenance() {
    let engine = private_engine();
    let baseline = engine.canonical_bytes();
    let context = serde_json::to_vec(
        &engine
            .character_context("player", engine.scope(), 0)
            .unwrap(),
    )
    .unwrap();
    for view in [
        View::Profiles,
        View::History,
        View::Relationships,
        View::Knowledge,
        View::Promises,
        View::Provenance,
    ] {
        let mut q = request(&engine, view);
        q.limit = 1;
        let rows = all_rows(&engine, q.clone(), false);
        let bytes = serde_json::to_string(&rows).unwrap();
        for hidden in [PRIVATE, "hidden-fact", "hidden-incoming", "private-item"] {
            assert!(!bytes.contains(hidden), "{view:?} leaked {hidden}");
        }
        q.search = PRIVATE.into();
        let page = query(&engine, &q, false).unwrap();
        assert_eq!(page.total, 0);
        assert!(page.rows.is_empty() && page.next_cursor.is_none());
    }
    assert_eq!(baseline, engine.canonical_bytes());
    assert_eq!(
        context,
        serde_json::to_vec(
            &engine
                .character_context("player", engine.scope(), 0)
                .unwrap()
        )
        .unwrap()
    );
}

#[test]
fn hidden_beliefs_do_not_shift_visible_row_identity_or_cursor() {
    let mut a = seed();
    a.beliefs.push(Belief {
        believer: "player".into(),
        proposition: "Player's uncertain memory".into(),
        source_claim: None,
        source: Evidence::Seed(a.id.clone()),
        confidence: Confidence::Uncertain,
    });
    let mut b = a.clone();
    b.beliefs.insert(
        0,
        Belief {
            believer: "sable".into(),
            proposition: PRIVATE.into(),
            source_claim: None,
            source: Evidence::Seed(b.id.clone()),
            confidence: Confidence::Believed,
        },
    );
    let a = Engine::new(a).unwrap();
    let b = Engine::new(b).unwrap();
    let mut q = request(&a, View::Knowledge);
    q.limit = 1;
    assert_eq!(query(&a, &q, false).unwrap(), query(&b, &q, false).unwrap());
}

#[test]
fn trusted_lab_lenses_require_grant_and_keep_each_npc_context_separate() {
    let engine = private_engine();
    let original =
        serde_json::to_value(engine.character_context("mira", engine.scope(), 0).unwrap()).unwrap();
    let mut q = request(&engine, View::Knowledge);
    q.observer = Observer::Character { id: "sable".into() };
    assert_eq!(query(&engine, &q, false), Err(QueryError::Forbidden));
    let page = query(&engine, &q, true).unwrap();
    assert_eq!(page.privacy, Privacy::PrivateCharacter);
    assert!(serde_json::to_string(&page).unwrap().contains(PRIVATE));
    q.observer = Observer::Character { id: "mira".into() };
    let page = query(&engine, &q, true).unwrap();
    assert!(!serde_json::to_string(&page).unwrap().contains(PRIVATE));
    assert!(serde_json::to_string(&page).unwrap().contains("old-ruins"));
    q.observer = Observer::Omniscient;
    assert_eq!(query(&engine, &q, false), Err(QueryError::Forbidden));
    assert!(serde_json::to_string(&query(&engine, &q, true).unwrap())
        .unwrap()
        .contains(PRIVATE));
    q.view = View::Profiles;
    let profiles = query(&engine, &q, true).unwrap();
    assert!(profiles.rows.iter().any(|r| matches!(r, Row::Field{actor,field,value:FieldValue::Text(name),..} if actor=="oren" && field=="name" && name=="Oren")));
    assert!(profiles.rows.iter().any(|r| matches!(r, Row::Field{actor,field,value:FieldValue::Text(name),..} if actor=="sable" && field=="name" && name==PRIVATE)));
    assert_eq!(
        original,
        serde_json::to_value(engine.character_context("mira", engine.scope(), 0).unwrap()).unwrap()
    );
}

#[test]
fn cursor_binds_scope_observer_view_head_search_limit_and_detects_edits() {
    let engine = private_engine();
    let mut q = request(&engine, View::Profiles);
    q.limit = 1;
    let first = query(&engine, &q, false).unwrap();
    q.cursor = first.next_cursor;
    assert!(query(&engine, &q, false).is_ok());
    let original = q.clone();
    for change in 0..7 {
        let mut q = original.clone();
        match change {
            0 => q.view = View::Knowledge,
            1 => q.observer = Observer::Character { id: "mira".into() },
            2 => q.limit = 2,
            3 => q.search = "name".into(),
            4 => q.at_revision = Some(0),
            5 => {
                let c = q.cursor.as_mut().unwrap();
                c.replace_range(2..3, "9");
            }
            _ => q.cursor.as_mut().unwrap().push('0'),
        }
        assert_eq!(
            query(&engine, &q, true),
            Err(QueryError::InvalidCursor),
            "change {change}"
        );
    }
    let mut q = original;
    q.scope.story = "foreign".into();
    assert_eq!(query(&engine, &q, false), Err(QueryError::Scope));
    let mut moved = engine.clone();
    commit(&mut moved, "wait", vec![Command::Wait { ticks: 1 }]);
    q = request(&engine, View::Profiles);
    assert_eq!(query(&moved, &q, false), Err(QueryError::Stale));
    q.expected_head = moved.revision();
    let mut old = request(&engine, View::Profiles);
    old.limit = 1;
    q.limit = 1;
    q.cursor = query(&engine, &old, false).unwrap().next_cursor;
    assert_eq!(query(&moved, &q, false), Err(QueryError::InvalidCursor));
}

#[test]
fn completed_turn_history_and_diff_replay_the_old_state_and_sources() {
    let mut engine = Engine::new(seed()).unwrap();
    let first = commit(
        &mut engine,
        "help",
        vec![
            Command::Give {
                item: "potion".into(),
                to: "mira".into(),
                quantity: 1,
            },
            Command::Wait { ticks: 1 },
        ],
    );
    let at_first = engine.revision();
    commit(
        &mut engine,
        "learn",
        vec![Command::Learn {
            ability: "beacon".into(),
        }],
    );
    let mut q = request(&engine, View::Profiles);
    q.at_revision = Some(0);
    let seed_page = query(&engine, &q, false).unwrap();
    assert!(seed_page.rows.iter().any(|r|matches!(r, Row::Field{field, value:FieldValue::Item(_), source:Source::Seed(_),..} if field=="item/potion")));
    q.at_revision = Some(at_first);
    let past = query(&engine, &q, false).unwrap();
    assert!(!past.rows.iter().any(
        |r| matches!(r,Row::Field{field,..} if field=="ability/beacon" || field=="item/potion")
    ));
    q.view = View::TurnDiff;
    let diff = query(&engine, &q, false).unwrap();
    assert!(diff.rows.iter().any(|r| matches!(r, Row::Change {before:Some(before),after:None,before_revision:0,after_revision,..}
        if *after_revision==at_first && matches!(before.as_ref(), Row::Field{field,..} if field=="item/potion"))));
    q.view = View::History;
    let history = query(&engine, &q, false).unwrap();
    assert!(history.rows.iter().any(|r|matches!(r,Row::Event {event,..} if event.turn=="help" && event.sequence==first.events()[0].sequence() && event.story_time==100)));
    assert!(!serde_json::to_string(&history).unwrap().contains("learn"));
    q.at_revision = Some(1);
    assert_eq!(query(&engine, &q, false), Err(QueryError::InvalidBoundary));
    q.at_revision = Some(99);
    assert_eq!(query(&engine, &q, false), Err(QueryError::InvalidBoundary));
    q.at_revision = None;
    q.view = View::Provenance;
    assert!(query(&engine,&q,false).unwrap().rows.iter().any(|r|matches!(r,Row::Provenance{key,sources,..} if key.contains("ability/beacon") && sources==&vec![Source::Event(3)])));
}

#[test]
fn facts_statements_beliefs_discoveries_remain_distinct_and_evidence_linked() {
    let mut engine = Engine::new(seed()).unwrap();
    commit(
        &mut engine,
        "false-claim",
        vec![Command::Say {
            text: "The relic is in old-ruins".into(),
            audience: ["mira".into()].into(),
        }],
    );
    commit(
        &mut engine,
        "belief",
        vec![Command::Believe { claim_event: 1 }],
    );
    commit(
        &mut engine,
        "move",
        vec![Command::Move {
            to: "dry-well".into(),
        }],
    );
    commit(
        &mut engine,
        "discover",
        vec![Command::Discover {
            fact: "beacon-mark".into(),
        }],
    );
    let page = query(&engine, &request(&engine, View::Knowledge), false).unwrap();
    assert!(page.rows.iter().any(|r|matches!(r,Row::Knowledge{origin:ValueOrigin::CanonicalTruth,text,..} if text.contains("SECRET-TIDE"))));
    assert!(page.rows.iter().any(|r|matches!(r,Row::Knowledge{origin:ValueOrigin::RecordedStatement,sources,text,..} if text.contains("old-ruins") && sources==&vec![Source::Event(1)])));
    assert!(page.rows.iter().any(|r|matches!(r,Row::Knowledge{origin:ValueOrigin::SubjectiveBelief,confidence:Some(Confidence::Uncertain),sources,..} if sources==&vec![Source::Event(2),Source::Event(1)])));
    assert!(page.rows.iter().any(|r|matches!(r,Row::Knowledge{origin:ValueOrigin::RecordedDiscovery,sources,..} if sources==&vec![Source::Event(4)])));
    assert!(page.rows.iter().any(|r|matches!(r,Row::Knowledge{origin:ValueOrigin::CanonicalTruth,id,sources,..} if id=="beacon-mark" && sources==&vec![Source::Seed("lantern-quay-v1".into()),Source::Event(4)])));
    let mut historical = request(&engine, View::Knowledge);
    historical.at_revision = Some(3);
    historical.search = "An old repair mark".into();
    assert_eq!(query(&engine, &historical, false).unwrap().total, 0);
    historical.at_revision = None;
    assert_eq!(query(&engine, &historical, false).unwrap().total, 1);
    let mut q = request(&engine, View::Knowledge);
    q.observer = Observer::Character { id: "sable".into() };
    assert!(!serde_json::to_string(&query(&engine, &q, true).unwrap())
        .unwrap()
        .contains("old-ruins"));
}

#[test]
fn directed_edges_and_promise_status_use_scoped_history_and_story_time() {
    let mut engine = Engine::new(seed()).unwrap();
    let edges = query(&engine, &request(&engine, View::Relationships), false).unwrap();
    assert!(edges
        .rows
        .iter()
        .all(|r| matches!(r,Row::Relationship{from,..} if from=="player")));
    let mut q = request(&engine, View::Relationships);
    q.observer = Observer::Character { id: "mira".into() };
    assert!(query(&engine,&q,true).unwrap().rows.iter().any(|r|matches!(r,Row::Relationship{from,dimension,value,..} if from=="mira" && dimension=="trust" && *value== -3)));
    commit(
        &mut engine,
        "pier",
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
    q = request(&engine, View::Promises);
    assert!(query(&engine,&q,false).unwrap().rows.iter().any(|r|matches!(r,Row::Promise{id,status,sources,..} if id=="return-key" && status=="fulfilled" && sources.contains(&Source::Event(3)))));
    q.at_revision = Some(0);
    assert!(query(&engine, &q, false)
        .unwrap()
        .rows
        .iter()
        .any(|r| matches!(r,Row::Promise{status,..} if status=="open")));
    let mut overdue = Engine::new(seed()).unwrap();
    commit(&mut overdue, "late", vec![Command::Wait { ticks: 21 }]);
    assert!(query(&overdue, &request(&overdue, View::Promises), false)
        .unwrap()
        .rows
        .iter()
        .any(|r| matches!(r,Row::Promise{status,..} if status=="overdue")));
}

#[test]
fn query_bounds_unsupported_views_versions_and_branch_limits_fail_honestly() {
    let engine = Engine::new(seed()).unwrap();
    let mut q = request(&engine, View::Profiles);
    for limit in [0, 65, u16::MAX] {
        q.limit = limit;
        assert_eq!(query(&engine, &q, false), Err(QueryError::TooLarge));
    }
    q.limit = 64;
    q.search = "x".repeat(257);
    assert_eq!(query(&engine, &q, false), Err(QueryError::TooLarge));
    q.search = "é".repeat(129);
    assert_eq!(query(&engine, &q, false), Err(QueryError::TooLarge));
    q.search = "\0".into();
    assert_eq!(query(&engine, &q, false), Err(QueryError::InvalidRequest));
    q.search.clear();
    q.cursor = Some("x".repeat(129));
    assert_eq!(query(&engine, &q, false), Err(QueryError::InvalidCursor));
    q.cursor = None;
    q.version = 3; // Query2 is allocated; the next unsupported version remains rejected.
    assert_eq!(query(&engine, &q, false), Err(QueryError::Version));
    q.version = 1;
    q.view = View::TurnDiff;
    assert_eq!(query(&engine, &q, false), Err(QueryError::InvalidBoundary));
    for view in [View::Summaries, View::RetrievalIndexes] {
        q.view = view;
        let page = query(&engine, &q, false).unwrap();
        assert_eq!(page.status, ViewStatus::Unsupported);
        assert!(page.rows.is_empty() && page.total == 0 && page.next_cursor.is_none());
    }
    let child = engine.fork("child", 0).unwrap();
    assert_eq!(
        query(&child, &request(&child, View::Profiles), false)
            .unwrap()
            .scope,
        *child.scope()
    );
    q = request(&engine, View::Profiles);
    q.scope.branch = "sibling".into();
    assert_eq!(query(&engine, &q, false), Err(QueryError::Scope));
    let mut other = seed();
    other.scope.story = "other".into();
    let other = Engine::new(other).unwrap();
    assert_eq!(
        query(&other, &request(&engine, View::Profiles), false),
        Err(QueryError::Scope)
    );
    assert!(serde_json::from_str::<Query>("{\"version\":1,\"unexpected\":true}").is_err());
}

#[test]
fn immutable_clone_queries_do_not_change_during_independent_commit() {
    let mut live = Engine::new(seed()).unwrap();
    let snapshot = live.clone();
    let q = request(&snapshot, View::Profiles);
    let expected = query(&snapshot, &q, false).unwrap();
    let read = std::thread::spawn(move || {
        for _ in 0..30 {
            assert_eq!(query(&snapshot, &q, false).unwrap(), expected);
        }
    });
    commit(
        &mut live,
        "spend",
        vec![Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 1,
        }],
    );
    read.join().unwrap();
    assert!(matches!(
        query(
            &live,
            &request(&Engine::new(seed()).unwrap(), View::Profiles),
            false
        ),
        Err(QueryError::Stale)
    ));
}

#[test]
fn history_exposes_only_completed_visible_messages_and_never_a_draft() {
    let mut engine = Engine::new(seed()).unwrap();
    let request = engine.request(
        "speech",
        Intent::Dialogue {
            text: "<img src=https://invalid.example/> literal statement".into(),
            audience: ["mira".into()].into(),
        },
    );
    let proposal = Engine::proposal(&request).unwrap();
    let preview = engine.preview(&request, &proposal).unwrap();
    assert_eq!(
        query(&engine, &self::request(&engine, View::History), false)
            .unwrap()
            .total,
        0
    );
    engine
        .commit(&request, &proposal, preview.narration())
        .unwrap();
    let page = query(&engine, &self::request(&engine, View::History), false).unwrap();
    assert!(page.rows.iter().any(|r| matches!(r, Row::Message {message_kind,text,..} if message_kind=="original_input" && text=="<img src=https://invalid.example/> literal statement")));
    commit(
        &mut engine,
        "mixed",
        vec![
            Command::Say {
                text: "Visible statement".into(),
                audience: ["mira".into()].into(),
            },
            Command::Wait { ticks: 1 },
        ],
    );
    let mut q = self::request(&engine, View::History);
    q.observer = Observer::Character { id: "mira".into() };
    let page = query(&engine, &q, true).unwrap();
    assert!(page
        .rows
        .iter()
        .any(|r| matches!(r,Row::Event{event,..} if event.turn=="mixed")));
    assert!(!page
        .rows
        .iter()
        .any(|r| matches!(r,Row::Message{turn,..} if turn=="mixed")));
    q.observer = Observer::Character { id: "sable".into() };
    assert_eq!(query(&engine, &q, true).unwrap().total, 0);
}

#[test]
fn row_and_byte_caps_paginate_or_fail_closed_without_mutation() {
    let mut s = seed();
    for i in 0..180 {
        s.actors
            .get_mut("player")
            .unwrap()
            .attributes
            .insert(format!("attribute-{i:03}"), 1);
    }
    let engine = Engine::new(s).unwrap();
    let q = request(&engine, View::Profiles);
    let first = query(&engine, &q, false).unwrap();
    assert_eq!(first.rows.len(), 64);
    assert!(first.next_cursor.is_some());
    let rows = all_rows(&engine, q, false);
    assert_eq!(rows.len(), first.total);
    assert_eq!(
        rows.iter().map(Row::key).collect::<BTreeSet<_>>().len(),
        rows.len()
    );
    let mut huge = seed();
    huge.actors.get_mut("player").unwrap().injuries = (0..80)
        .map(|i| format!("{i}:{}", "x".repeat(1024)))
        .collect();
    let huge = Engine::new(huge).unwrap();
    let before = huge.canonical_bytes();
    assert_eq!(
        query(&huge, &request(&huge, View::Profiles), false),
        Err(QueryError::TooLarge)
    );
    assert_eq!(before, huge.canonical_bytes());
}

#[test]
fn byte_budget_splits_long_visible_history_before_row_limit() {
    let mut engine = Engine::new(seed()).unwrap();
    for i in 0..40 {
        commit(
            &mut engine,
            &format!("long-{i}"),
            vec![Command::Say {
                text: format!("{i}:{}", "x".repeat(1900)),
                audience: ["mira".into()].into(),
            }],
        );
    }
    let q = request(&engine, View::History);
    let first = query(&engine, &q, false).unwrap();
    assert!(first.rows.len() < MAX_ROWS as usize && !first.rows.is_empty());
    assert!(first.next_cursor.is_some());
    let rows = all_rows(&engine, q, false);
    assert_eq!(rows.len(), 80); // One accepted event and one recorded narration per typed turn.
}

#[test]
fn incoming_seed_terms_are_private_but_witnessed_new_promises_are_inspectable() {
    let mut s = seed();
    s.commitments.insert(
        "unwitnessed".into(),
        Commitment {
            from: "sable".into(),
            to: "mira".into(),
            terms: PRIVATE.into(),
            deadline: 300,
            source: Evidence::Seed(s.id.clone()),
            return_item: None,
            completed_by: None,
        },
    );
    let mut engine = Engine::new(s).unwrap();
    commit(
        &mut engine,
        "promise",
        vec![Command::Promise {
            id: "visible-promise".into(),
            to: "mira".into(),
            terms: "Meet by the quay".into(),
            deadline: 150,
            return_item: None,
        }],
    );
    let mut q = request(&engine, View::Promises);
    q.observer = Observer::Character { id: "mira".into() };
    let page = query(&engine, &q, true).unwrap();
    assert_eq!(page.total, 1);
    assert!(!serde_json::to_string(&page).unwrap().contains(PRIVATE));
    assert!(page.rows.iter().any(|r|matches!(r,Row::Promise{id,sources,..} if id=="visible-promise" && sources==&vec![Source::Event(1)])));
}

#[test]
fn historical_v2_replay_preserves_original_input_without_an_inference_provider() {
    use locallore::play::{
        NarrationDocument, PlayProfile, PlayRecord, NARRATION_POLICY, PLAY_VERSION, PROMPT_VERSION,
    };
    let mut engine = Engine::new(seed()).unwrap();
    let input = "I give my sole potion to Mira";
    let request = engine.request(
        "free-text",
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: input.into(),
        },
    );
    let proposal = Proposal {
        version: VERSION,
        scope: request.scope.clone(),
        turn: request.turn.clone(),
        expected_revision: 0,
        commands: vec![Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 1,
        }],
    };
    let approved = engine.preview(&request, &proposal).unwrap();
    let record = PlayRecord {
        version: PLAY_VERSION,
        policy: NARRATION_POLICY.into(),
        prompt_version: PROMPT_VERSION.into(),
        profile: PlayProfile {
            id: "synthetic-profile".into(),
            worker_sha256: "4".repeat(64),
            profile_manifest_sha256: "5".repeat(64),
            model_sha256: "1".repeat(64),
            runtime_revision: "2".repeat(40),
            template_sha256: "3".repeat(64),
            context_tokens: 512,
            director_tokens: 100,
            narrator_tokens: 100,
            deadline_ms: 1000,
            repair_limit: 0,
        },
        repairs: 0,
        fallback: true,
        narration: NarrationDocument {
            text: approved.narration().into(),
            event_ids: vec![1],
            speaker: "narrator".into(),
        },
        stages: vec![],
        context: Some(serde_json::from_value(serde_json::json!({
            "version":2,"compiler_version":2,"scope":engine.scope(),"head":0,"observer":engine.seed().player,"source_fallback_reason":null,
            "coverage":{"mode":"raw","set_fallback_reason":"missing","packets_used":0,"packets_fell_back":0,
                "timespan_fallback_packets":0,"mandatory_fallback_packets":0,"covered_through":0,"raw_delta_after":0,
                "cached_event_candidates":0,"raw_event_candidates":0}
        })).unwrap()),
        context_policy: Some(locallore::play::PlayContextPolicy::StateRelevantMemoryV1),
        story_presentation: None,
    };
    engine.commit_play(&request, &proposal, &record).unwrap();
    commit(&mut engine, "later", vec![Command::Wait { ticks: 1 }]);
    let mut q = self::request(&engine, View::History);
    q.at_revision = Some(1);
    let page = query(&engine, &q, false).unwrap();
    assert!(page.rows.iter().any(|r|matches!(r,Row::Message{message_kind,text,turn,..} if message_kind=="original_input" && text==input && turn=="free-text")));
    assert!(!serde_json::to_string(&page)
        .unwrap()
        .contains("synthetic-profile"));
    q.observer = Observer::Character { id: "mira".into() };
    let npc = query(&engine, &q, true).unwrap();
    assert!(npc.rows.iter().any(|row| matches!(row, Row::Event { .. })));
    assert!(
        !npc.rows
            .iter()
            .any(|row| matches!(row, Row::Message { .. })),
        "seeing a gift never grants the private player prompt or narrator transcript"
    );
    assert_eq!(engine.state().items["potion"].owner, "mira");
}

#[test]
fn private_promise_completion_does_not_change_creditor_status_sources_or_derived_rows() {
    let mut engine = Engine::new(seed()).unwrap();
    commit(
        &mut engine,
        "promise",
        vec![Command::Promise {
            id: "potion-return".into(),
            to: "mira".into(),
            terms: "Return the potion".into(),
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
    let mut q = request(&engine, View::Promises);
    q.observer = Observer::Character { id: "mira".into() };
    let before = query(&engine, &q, true).unwrap().rows;
    q.view = View::Provenance;
    let sources_before = query(&engine, &q, true).unwrap().rows;
    commit(
        &mut engine,
        "private-completion",
        vec![Command::CompletePromise {
            id: "potion-return".into(),
        }],
    );
    q.expected_head = engine.revision();
    let sources_after = query(&engine, &q, true).unwrap().rows;
    assert_eq!(
        serde_json::to_value(sources_before).unwrap(),
        serde_json::to_value(sources_after).unwrap()
    );
    q.view = View::Promises;
    let after = query(&engine, &q, true).unwrap().rows;
    assert_eq!(
        serde_json::to_value(before).unwrap(),
        serde_json::to_value(after).unwrap()
    );
    q.search = "fulfilled".into();
    assert_eq!(query(&engine, &q, true).unwrap().total, 0);
    q.search.clear();
    q.view = View::TurnDiff;
    let diff = query(&engine, &q, true).unwrap();
    assert!(!serde_json::to_string(&diff.rows)
        .unwrap()
        .contains("potion-return"));
    q.view = View::Promises;
    q.observer = Observer::Player;
    assert!(query(&engine, &q, false).unwrap().rows.iter().any(
        |row| matches!(row,Row::Promise{id,status,..} if id=="potion-return" && status=="fulfilled")
    ));
}

#[test]
fn narrative_profile_does_not_invent_numeric_rpg_fields() {
    let mut s = seed();
    s.profile = Profile::NarrativeV1;
    s.abilities.clear();
    for actor in s.actors.values_mut() {
        actor.energy = 0;
        actor.abilities.clear();
        actor.attributes.clear();
    }
    let engine = Engine::new(s).unwrap();
    let page = query(&engine, &request(&engine, View::Profiles), false).unwrap();
    assert!(!page.rows.iter().any(|r|matches!(r,Row::Field{field,..} if field=="energy" || field.starts_with("ability/") || field.starts_with("attribute/"))));
    assert!(page
        .rows
        .iter()
        .any(|r| matches!(r,Row::Field{field,..} if field=="goals")));
}
