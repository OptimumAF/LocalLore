use locallore::{contracts::*, engine::Engine, inference::*};
use serde_json::{json, Value};

fn seed() -> Seed {
    serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap()
}

fn apply(engine: &mut Engine, commands: Vec<Command>) -> Receipt {
    let request = engine.request(
        &format!("turn-{}", engine.revision()),
        Intent::Actions(commands),
    );
    let proposal = Engine::proposal(&request).unwrap();
    let preview = engine.preview(&request, &proposal).unwrap();
    engine
        .commit(&request, &proposal, preview.narration())
        .unwrap()
}

fn encoded(engine: &Engine) -> Vec<String> {
    engine
        .receipts()
        .iter()
        .map(|receipt| serde_json::to_string(receipt).unwrap())
        .collect()
}

fn history() -> Engine {
    let mut engine = Engine::new(seed()).unwrap();
    apply(
        &mut engine,
        vec![Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 1,
        }],
    );
    apply(
        &mut engine,
        vec![
            Command::Learn {
                ability: "beacon".into(),
            },
            Command::UseAbility {
                ability: "steady".into(),
            },
            Command::Say {
                text: "The tideglass is in the tower.".into(),
                audience: ["mira".into()].into(),
            },
        ],
    );
    apply(
        &mut engine,
        vec![
            Command::Believe { claim_event: 4 },
            Command::Move {
                to: "dry-well".into(),
            },
            Command::Discover {
                fact: "beacon-mark".into(),
            },
            Command::Wait { ticks: 5 },
            Command::Move { to: "quay".into() },
            Command::Move { to: "pier".into() },
        ],
    );
    apply(
        &mut engine,
        vec![
            Command::Give {
                item: "brass-key".into(),
                to: "oren".into(),
                quantity: 1,
            },
            Command::CompletePromise {
                id: "return-key".into(),
            },
            Command::Promise {
                id: "new-promise".into(),
                to: "oren".into(),
                terms: "Return before the next tide".into(),
                deadline: 120,
                return_item: None,
            },
        ],
    );
    engine
}

fn corrupt(history: &[String]) {
    assert_eq!(
        Engine::restore(seed(), history).unwrap_err(),
        Error::CorruptHistory
    );
}

#[test]
fn restored_history_matches_complete_projection_receipts_and_every_observer() {
    let engine = history();
    let restored = Engine::restore(seed(), &encoded(&engine)).unwrap();
    assert_eq!(restored.canonical_bytes(), engine.canonical_bytes());
    assert_eq!(restored.receipts(), engine.receipts());
    assert_eq!(restored.revision(), 13);
    for observer in seed().actors.keys() {
        assert_eq!(
            restored
                .character_context(observer, restored.scope(), restored.revision())
                .unwrap(),
            engine
                .character_context(observer, engine.scope(), engine.revision())
                .unwrap()
        );
    }
    let absent = restored
        .character_context("sable", restored.scope(), restored.revision())
        .unwrap();
    assert!(absent.observations.is_empty());
    assert!(!serde_json::to_string(&absent)
        .unwrap()
        .contains("SECRET-TIDE-731"));
    assert!(!restored.receipts()[0].events()[0]
        .witnesses()
        .contains("sable"));
}

#[test]
fn exact_retry_after_restore_returns_recorded_receipt_without_provider() {
    let engine = history();
    let receipt = &engine.receipts()[0];
    assert_eq!(
        receipt.proposal(),
        &Engine::proposal(receipt.request()).unwrap()
    );
    let mut restored = Engine::restore(seed(), &encoded(&engine)).unwrap();
    let before = restored.canonical_bytes();
    let mut provider = FakeProvider::new(FakeMode::Failed);
    let result = execute(
        &mut restored,
        receipt.request(),
        &mut provider,
        &Cancellation::default(),
        Budget::default(),
    )
    .unwrap();
    assert_eq!(&result, receipt);
    assert_eq!(provider.calls, 0);
    assert_eq!(restored.canonical_bytes(), before);
    assert_eq!(restored.receipts().len(), engine.receipts().len());
}

#[test]
fn every_recorded_envelope_field_is_checked_including_resolved_effects() {
    let source: Value = serde_json::from_str(&encoded(&history())[0]).unwrap();
    let changes = [
        ("/request/version", json!(2)),
        ("/request/scope/story", json!("other")),
        ("/request/scope/branch", json!("other")),
        ("/request/turn", json!("other")),
        ("/request/expected_revision", json!(1)),
        ("/request/intent/value/0/quantity", json!(2)),
        ("/proposal/version", json!(2)),
        ("/proposal/scope/branch", json!("other")),
        ("/proposal/turn", json!("other")),
        ("/proposal/expected_revision", json!(1)),
        ("/events/0/version", json!(2)),
        ("/events/0/scope/branch", json!("other")),
        ("/events/0/sequence", json!(9)),
        ("/events/0/turn", json!("other")),
        ("/events/0/rules", json!("narrative_v1")),
        ("/events/0/seed", json!("other")),
        ("/events/0/story_time", json!(101)),
        ("/events/0/participants", json!(["mira", "player", "sable"])),
        ("/events/0/witnesses", json!(["mira", "player", "sable"])),
        ("/events/0/outcome/to", json!("sable")),
        ("/events/0/outcome/quantity", json!(2)),
        ("/narration", json!("You get another potion.")),
    ];
    for (pointer, value) in changes {
        let mut changed = source.clone();
        *changed.pointer_mut(pointer).unwrap() = value;
        corrupt(&[serde_json::to_string(&changed).unwrap()]);
    }
    for pointer in [
        "",
        "/request",
        "/proposal",
        "/events/0",
        "/events/0/outcome",
    ] {
        let mut changed = source.clone();
        changed
            .pointer_mut(pointer)
            .unwrap()
            .as_object_mut()
            .unwrap()
            .insert("hidden".into(), json!(true));
        corrupt(&[serde_json::to_string(&changed).unwrap()]);
    }
}

#[test]
fn duplicate_keys_are_rejected_recursively_even_when_values_match() {
    let source = encoded(&history())[0].clone();
    // Exact duplicate values would evade a parse-to-Value then equality check.
    for key in ["request", "proposal", "events", "narration"] {
        let raw: Value = serde_json::from_str(&source).unwrap();
        let duplicated = format!("{{{key:?}:{},{}", raw[key], &source[1..]);
        corrupt(&[duplicated]);
    }
    for (before, after) in [
        ("\"version\":1", "\"version\":1,\"version\":1"),
        ("\"quantity\":1", "\"quantity\":1,\"quantity\":1"),
        ("\"sequence\":1", "\"sequence\":1,\"sequence\":1"),
        (
            "\"story\":\"quay\"",
            "\"story\":\"quay\",\"story\":\"quay\"",
        ),
    ] {
        assert!(source.contains(before));
        corrupt(&[source.replace(before, after)]);
    }
    corrupt(&[source.replacen("\"version\":1", "\"version\":2,\"version\":1", 1)]);
    corrupt(&[source.replacen("\"version\":1", "\"version\":1,\"vers\\u0069on\":1", 1)]);
}

#[test]
fn reordered_object_keys_work_but_duplicate_missing_and_out_of_order_turns_fail() {
    let engine = history();
    let history = encoded(&engine);
    // Value uses sorted object keys, unlike Receipt's struct serialization order.
    let reordered: Vec<_> = history
        .iter()
        .map(|receipt| {
            serde_json::to_string_pretty(&serde_json::from_str::<Value>(receipt).unwrap()).unwrap()
        })
        .collect();
    assert_eq!(
        Engine::restore(seed(), &reordered)
            .unwrap()
            .canonical_bytes(),
        engine.canonical_bytes()
    );
    let mut duplicate = history.clone();
    duplicate.insert(1, history[0].clone());
    corrupt(&duplicate);
    let mut out_of_order = history.clone();
    out_of_order.swap(0, 1);
    corrupt(&out_of_order);
    corrupt(&history[1..]);
    let mut partial: Value = serde_json::from_str(&history[1]).unwrap();
    partial["events"].as_array_mut().unwrap().pop();
    corrupt(&[history[0].clone(), partial.to_string()]);
}

#[test]
fn receipt_count_individual_and_total_input_budgets_are_checked_first() {
    assert_eq!(
        Engine::restore(seed(), &vec![String::new(); MAX_HISTORY_RECEIPTS + 1]).unwrap_err(),
        Error::TooLarge
    );
    assert_eq!(
        Engine::restore(seed(), &[" ".repeat(MAX_RECEIPT_BYTES + 1)]).unwrap_err(),
        Error::TooLarge
    );
    let receipts = vec![" ".repeat(MAX_RECEIPT_BYTES); MAX_HISTORY_BYTES / MAX_RECEIPT_BYTES + 1];
    assert_eq!(
        Engine::restore(seed(), &receipts).unwrap_err(),
        Error::TooLarge
    );
    corrupt(&["[".repeat(256)]);
    corrupt(&["{}{}".into()]);
    corrupt(&["null".into()]);
}

#[test]
fn empty_history_and_alternate_seed_do_not_inherit_other_story_state() {
    let fresh = Engine::restore(seed(), &[]).unwrap();
    assert_eq!(
        fresh.canonical_bytes(),
        Engine::new(seed()).unwrap().canonical_bytes()
    );
    assert_eq!(fresh.revision(), 0);
    let mut other = seed();
    other.scope.story = "other-story".into();
    assert_eq!(
        Engine::restore(other, &encoded(&history())).unwrap_err(),
        Error::CorruptHistory
    );
    let mut changed_rules = seed();
    changed_rules.items.get_mut("potion").unwrap().quantity = 2;
    assert_eq!(
        Engine::restore(changed_rules, &encoded(&history())).unwrap_err(),
        Error::CorruptHistory
    );
}

#[test]
fn consumption_and_narrative_rules_restore_without_randomness() {
    let mut engine = Engine::new(seed()).unwrap();
    apply(
        &mut engine,
        vec![Command::Consume {
            item: "potion".into(),
        }],
    );
    assert_eq!(
        Engine::restore(seed(), &encoded(&engine))
            .unwrap()
            .canonical_bytes(),
        engine.canonical_bytes()
    );
    let mut narrative = seed();
    narrative.profile = Profile::NarrativeV1;
    narrative.abilities.clear();
    for actor in narrative.actors.values_mut() {
        actor.abilities.clear();
        actor.attributes.clear();
        actor.energy = 0;
    }
    let mut engine = Engine::new(narrative.clone()).unwrap();
    apply(&mut engine, vec![Command::Wait { ticks: 2 }]);
    assert_eq!(
        Engine::restore(narrative, &encoded(&engine))
            .unwrap()
            .canonical_bytes(),
        engine.canonical_bytes()
    );
}

#[test]
fn seeded_attempt_sequences_restore_every_completed_prefix() {
    for sequence_seed in 1..=12u64 {
        let mut random = sequence_seed;
        let mut engine = Engine::new(seed()).unwrap();
        for attempt in 0..32 {
            random = random.wrapping_mul(6364136223846793005).wrapping_add(1);
            let command = match random % 6 {
                0 => Command::Wait {
                    ticks: (random % 10 + 1) as u16,
                },
                1 => Command::Give {
                    item: "potion".into(),
                    to: "mira".into(),
                    quantity: 1,
                },
                2 => Command::Consume {
                    item: "potion".into(),
                },
                3 => Command::Move { to: "pier".into() },
                4 => Command::Move { to: "quay".into() },
                _ => Command::UseAbility {
                    ability: "steady".into(),
                },
            };
            let request = engine.request(
                &format!("attempt-{attempt}"),
                Intent::Actions(vec![command]),
            );
            let proposal = Engine::proposal(&request).unwrap();
            if let Ok(receipt) = engine.preview(&request, &proposal) {
                engine
                    .commit(&request, &proposal, receipt.narration())
                    .unwrap();
            }
            let restored = Engine::restore(seed(), &encoded(&engine)).unwrap();
            assert_eq!(restored.canonical_bytes(), engine.canonical_bytes());
            assert_eq!(restored.receipts(), engine.receipts());
            for (item, state) in &restored.state().items {
                assert!(seed().items.contains_key(item));
                assert_eq!(state.quantity, 1);
            }
        }
    }
}
