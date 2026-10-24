//! Frozen future Query2 seam oracles. Source-only until coordinator qualification.
use locallore::{author_correction::*, contracts::*, engine::Engine, inspection_query::*};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;

fn engine() -> Engine {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    seed.facts.get_mut("relic-location").unwrap().proposition = "OBSERVED_A".into();
    Engine::new(seed).unwrap()
}
fn correction(parent: &Engine, child: &str, before: &str, after: &str) -> Engine {
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
        reason: "PRIVATE_REASON_NEVER_A_HISTORY_ROW".into(),
    };
    parent
        .apply_author_correction(
            &parent.prepare_author_correction(&input, &|| false).unwrap(),
            &|| false,
        )
        .unwrap()
        .engine
}
fn commit(engine: &mut Engine, turn: &str, intent: Intent) -> Receipt {
    let request = engine.request(turn, intent);
    let approved = engine
        .preview(&request, &Engine::proposal(&request).unwrap())
        .unwrap();
    engine.commit_prepared(&approved).unwrap()
}
fn dialogue(engine: &mut Engine, text: &str) -> Receipt {
    commit(
        engine,
        "same-turn",
        Intent::Dialogue {
            text: text.into(),
            audience: ["mira".into()].into(),
        },
    )
}
fn request(engine: &Engine, observer: Observer) -> Query {
    Query {
        version: 2,
        scope: engine.scope().clone(),
        expected_head: engine.revision(),
        at_revision: None,
        observer,
        view: View::History,
        cursor: None,
        limit: 64,
        search: String::new(),
    }
}
fn page(engine: &Engine, observer: Observer) -> Page {
    query(engine, &request(engine, observer), true).unwrap()
}
fn value(value: impl serde::Serialize) -> Value {
    serde_json::to_value(value).unwrap()
}
fn markers(page: &Page) -> Vec<Value> {
    page.rows
        .iter()
        .map(value)
        .filter(|v| v["kind"] == "author_correction")
        .collect()
}

#[test]
fn inherited_and_child_duplicate_turn_messages_keep_actual_scope_and_unique_scoped_keys() {
    let mut parent = engine();
    let ancestor = dialogue(&mut parent, "ANCESTOR_INPUT");
    let mut child = correction(&parent, "child", "OBSERVED_A", "PRIVATE_WORLD_B");
    let local = dialogue(&mut child, "CHILD_INPUT");
    let before = child.canonical_bytes();
    let output = page(&child, Observer::Player);
    let messages: Vec<_> = output
        .rows
        .iter()
        .map(value)
        .filter(|r| r["kind"] == "scoped_message")
        .collect();
    assert_eq!(messages.len(), 4);
    assert!(!output.rows.iter().any(|r| matches!(r, Row::Message { .. })));
    for receipt in [&ancestor, &local] {
        let expected_scope = value(&receipt.request().scope);
        let expected_ids = value(
            receipt
                .events()
                .iter()
                .map(AcceptedEvent::sequence)
                .collect::<Vec<_>>(),
        );
        let own: Vec<_> = messages
            .iter()
            .filter(|m| m["original_scope"] == expected_scope)
            .collect();
        assert_eq!(own.len(), 2);
        for row in own {
            assert_eq!(row["turn"], "same-turn");
            assert_eq!(row["event_ids"], expected_ids);
            assert_eq!(row["origin"], "recorded_message");
            let key_parts: Vec<String> =
                serde_json::from_str(row["key"].as_str().unwrap()).unwrap();
            assert_eq!(key_parts[0], "history");
            assert!(key_parts
                .iter()
                .any(|p| p == &receipt.request().scope.story));
            assert!(key_parts
                .iter()
                .any(|p| p == &receipt.request().scope.branch));
            assert!(key_parts.iter().any(|p| p == "same-turn"));
            assert!(key_parts
                .iter()
                .any(|p| p == row["message_kind"].as_str().unwrap()));
        }
    }
    assert_ne!(ancestor.request().scope, local.request().scope);
    assert_eq!(ancestor.request().turn, local.request().turn);
    assert_eq!(
        markers(&output),
        vec![json!({"kind":"author_correction","revision":2})]
    );
    let keys = output.rows.iter().map(Row::key).collect::<BTreeSet<_>>();
    assert_eq!(keys.len(), output.rows.len());
    let mut q = request(&child, Observer::Player);
    q.limit = 1;
    let mut paged = vec![];
    loop {
        let next = query(&child, &q, false).unwrap();
        assert_eq!(next.total, output.total);
        paged.extend(next.rows);
        q.cursor = next.next_cursor;
        if q.cursor.is_none() {
            break;
        }
        assert!(paged.len() <= output.total);
    }
    assert_eq!(paged, output.rows);
    assert_eq!(child.canonical_bytes(), before);
}

#[test]
fn query1_message_wire_and_original24_receipt_hashes_survive_replay() {
    // Immutable actual 2.4 turn, not a rewritten current-version fixture.
    let fixture: Value =
        serde_json::from_str(include_str!("fixtures/accepted_play_v2_4.json")).unwrap();
    let seed: Seed = serde_json::from_value(fixture["seed"].clone()).unwrap();
    let receipt_json = fixture["receipt"].to_string();
    let engine = Engine::restore(seed.clone(), &[receipt_json.clone()]).unwrap();
    let receipt = &engine.receipts()[0];
    let compact = serde_json::to_vec(receipt).unwrap();
    assert_eq!(
        compact.as_slice(),
        include_bytes!("fixtures/accepted_play_v2_4_receipt.json")
    );
    assert_eq!(
        format!("{:x}", Sha256::digest(&compact)),
        "38dcf7329addf4ed98fd984cdb9eac95f8d078be03bf4633dd7082d23ac4bc3f"
    );
    let mut q = request(&engine, Observer::Player);
    q.version = 1;
    let output = query(&engine, &q, false).unwrap();
    assert_eq!(output.version, QUERY_VERSION);
    assert_eq!(QUERY_VERSION, 1);
    let input = output
        .rows
        .iter()
        .find(
            |r| matches!(r, Row::Message { message_kind, .. } if message_kind == "original_input"),
        )
        .unwrap();
    // Literal legacy Row wire bytes frozen from its existing field order and the
    // immutable receipt input. This is a new oracle, not an executed old query capture.
    let expected = r#"{"kind":"message","key":"[\"history\",\"00000000000000000001\",\"0_input\"]","turn":"original-v24-play25-boundary","message_kind":"original_input","text":"I give potion to Mira.","event_ids":[1],"origin":"recorded_message"}"#;
    assert_eq!(serde_json::to_string(input).unwrap(), expected);
    assert_eq!(
        format!("{:x}", Sha256::digest(serde_json::to_vec(input).unwrap())),
        "d14be3029e57a13e45293d3264f17ce23f7b6c9370c630d081882928b538a62e"
    );
    assert!(output
        .rows
        .iter()
        .map(value)
        .all(|r| r["kind"] != "scoped_message" && r.get("original_scope").is_none()));
    q.limit = 1;
    let first = query(&engine, &q, false).unwrap();
    assert!(first.next_cursor.as_ref().unwrap().starts_with("1:"));
    let restored = Engine::restore(seed, &[receipt_json]).unwrap();
    assert_eq!(value(query(&restored, &q, false).unwrap()), value(&first));
    assert_eq!(restored.canonical_bytes(), engine.canonical_bytes());
}

#[test]
fn marker_has_exact_two_field_wire_and_only_literal_player_history_receives_it() {
    let child = correction(&engine(), "child", "OBSERVED_A", "PRIVATE_WORLD_B");
    let before = child.canonical_bytes();
    let actor = value(
        child
            .character_context_v2("player", child.scope(), child.revision())
            .unwrap(),
    );
    let output = page(&child, Observer::Player);
    assert_eq!(output.total, 1);
    assert_eq!(output.rows.len(), 1);
    assert_eq!(
        value(&output.rows[0]),
        json!({"kind":"author_correction","revision":1})
    );
    assert_eq!(
        output.rows[0].key(),
        "[\"history\",\"00000000000000000001\",\"author_correction\"]"
    );
    assert!(output.next_cursor.is_none());
    for observer in [
        Observer::Character {
            id: "player".into(),
        },
        Observer::Character { id: "mira".into() },
        Observer::Omniscient,
    ] {
        let other = page(&child, observer.clone());
        assert_eq!(other.total, 0);
        assert!(other.rows.is_empty());
        let mut search = request(&child, observer);
        search.search = "author_correction".into();
        assert_eq!(query(&child, &search, true).unwrap().total, 0);
    }
    for view in [
        View::Profiles,
        View::Relationships,
        View::Knowledge,
        View::Promises,
        View::Provenance,
        View::TurnDiff,
        View::Summaries,
        View::RetrievalIndexes,
    ] {
        let mut q = request(&child, Observer::Player);
        q.view = view;
        let other = query(&child, &q, false).unwrap();
        assert!(markers(&other).is_empty());
        assert!(!serde_json::to_string(&other)
            .unwrap()
            .contains("PRIVATE_REASON_NEVER_A_HISTORY_ROW"));
    }
    assert_eq!(
        value(
            child
                .character_context_v2("player", child.scope(), child.revision())
                .unwrap()
        ),
        actor
    );
    assert!(!serde_json::to_string(&actor)
        .unwrap()
        .contains("author_correction"));
    assert_eq!(child.canonical_bytes(), before);
}

#[test]
fn historical_completed_boundaries_and_fork_prefix_bound_markers_before_pagination() {
    let mut parent = engine();
    commit(
        &mut parent,
        "wait",
        Intent::Actions(vec![Command::Wait { ticks: 1 }]),
    );
    let first = correction(&parent, "first", "OBSERVED_A", "PRIVATE_WORLD_B");
    let second = correction(&first, "second", "PRIVATE_WORLD_B", "PRIVATE_WORLD_C");
    assert_eq!(second.revision(), 3);
    let mut q = request(&second, Observer::Player);
    q.search = "author_correction".into();
    q.limit = 1;
    let one = query(&second, &q, false).unwrap();
    assert_eq!(one.total, 2);
    assert_eq!(
        markers(&one),
        vec![json!({"kind":"author_correction","revision":2})]
    );
    q.cursor = one.next_cursor;
    assert!(q.cursor.as_ref().unwrap().starts_with("2:"));
    let two = query(&second, &q, false).unwrap();
    assert_eq!(
        markers(&two),
        vec![json!({"kind":"author_correction","revision":3})]
    );
    assert!(two.next_cursor.is_none());
    q.cursor = None;
    q.at_revision = Some(1);
    assert_eq!(query(&second, &q, false).unwrap().total, 0);
    q.at_revision = Some(2);
    let included = query(&second, &q, false).unwrap();
    assert_eq!(included.total, 1);
    assert_eq!(
        markers(&included),
        vec![json!({"kind":"author_correction","revision":2})]
    );
    let before_author = second.fork("before-author", 1).unwrap();
    assert!(markers(&page(&before_author, Observer::Player)).is_empty());
    let after_first = second.fork("after-first", 2).unwrap();
    assert_eq!(
        markers(&page(&after_first, Observer::Player)),
        vec![json!({"kind":"author_correction","revision":2})]
    );
    let sibling = correction(&parent, "sibling", "OBSERVED_A", "SIBLING_PRIVATE_WORLD");
    let encoded = serde_json::to_string(&page(&second, Observer::Player)).unwrap();
    for excluded in [
        "PRIVATE_WORLD_B",
        "PRIVATE_WORLD_C",
        "SIBLING_PRIVATE_WORLD",
        "PRIVATE_REASON_NEVER_A_HISTORY_ROW",
        "truth_source",
        "author-correction-v1",
    ] {
        assert!(!encoded.contains(excluded));
    }
    assert_eq!(sibling.revision(), 2);
    assert_eq!(
        markers(&page(&sibling, Observer::Player)),
        vec![json!({"kind":"author_correction","revision":2})]
    );
}

#[test]
fn whole_player_receipt_prose_does_not_enter_partially_witnessing_npc_rows_or_counts() {
    let mut child = correction(&engine(), "child", "OBSERVED_A", "PRIVATE_WORLD_B");
    let receipt = commit(
        &mut child,
        "mixed",
        Intent::Actions(vec![
            Command::Say {
                text: "NPC_HEARD_PUBLIC".into(),
                audience: ["mira".into()].into(),
            },
            Command::Say {
                text: "PLAYER_PRIVATE_UTTERANCE".into(),
                audience: ["player".into()].into(),
            },
        ]),
    );
    let own = page(&child, Observer::Player);
    let messages: Vec<_> = own
        .rows
        .iter()
        .map(value)
        .filter(|r| r["kind"] == "scoped_message")
        .collect();
    assert_eq!(messages.len(), 1); // typed input: narration only
    assert_eq!(
        messages[0]["event_ids"],
        value(
            receipt
                .events()
                .iter()
                .map(AcceptedEvent::sequence)
                .collect::<Vec<_>>()
        )
    );
    assert_eq!(messages[0]["original_scope"], value(child.scope()));
    let npc = page(&child, Observer::Character { id: "mira".into() });
    assert_eq!(npc.total, 1);
    assert!(npc.rows.iter().all(|r| matches!(r, Row::Event { .. })));
    let encoded = serde_json::to_string(&npc).unwrap();
    assert!(encoded.contains("NPC_HEARD_PUBLIC"));
    for excluded in [
        "PLAYER_PRIVATE_UTTERANCE",
        "scoped_message",
        "author_correction",
        "PRIVATE_WORLD_B",
        "PRIVATE_REASON_NEVER_A_HISTORY_ROW",
        "original_input",
        "narration",
        "request",
        "proposal",
    ] {
        assert!(!encoded.contains(excluded));
    }
    let mut q = request(&child, Observer::Character { id: "mira".into() });
    q.limit = 1;
    q.search = "PLAYER_PRIVATE_UTTERANCE".into();
    assert_eq!(query(&child, &q, true).unwrap().total, 0);
    let private_omni = page(&child, Observer::Omniscient);
    assert_eq!(private_omni.total, 3); // two actual events + whole narration, NO marker
    assert!(markers(&private_omni).is_empty());
}

#[test]
fn marker_and_scoped_message_cursors_bind_observer_search_head_and_version() {
    let mut parent = engine();
    dialogue(&mut parent, "ancestor");
    let mut child = correction(&parent, "child", "OBSERVED_A", "PRIVATE_WORLD_B");
    dialogue(&mut child, "local");
    let mut q = request(&child, Observer::Player);
    q.limit = 1;
    let first = query(&child, &q, false).unwrap();
    q.cursor = first.next_cursor;
    for observer in [
        Observer::Character {
            id: "player".into(),
        },
        Observer::Omniscient,
    ] {
        let mut other = q.clone();
        other.observer = observer;
        assert_eq!(
            query(&child, &other, true).unwrap_err(),
            QueryError::InvalidCursor
        );
    }
    let mut other = q.clone();
    other.search = "author_correction".into();
    assert_eq!(
        query(&child, &other, false).unwrap_err(),
        QueryError::InvalidCursor
    );
    other = q.clone();
    other.expected_head -= 1;
    assert_eq!(query(&child, &other, false).unwrap_err(), QueryError::Stale);
    let mut domain1 = request(&parent, Observer::Player);
    domain1.limit = 1;
    domain1.version = 1;
    let legacy = query(&parent, &domain1, false)
        .unwrap()
        .next_cursor
        .unwrap();
    domain1.version = 2;
    domain1.cursor = Some(legacy);
    assert_eq!(
        query(&parent, &domain1, false).unwrap_err(),
        QueryError::InvalidCursor
    );
}
