// Original M10.01 staged rejection and retry oracle.
// Intended integration: crates/locallore/tests/staged_rejection_turn_key.rs
// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
use locallore::{contracts::*, engine::Engine};

#[test]
fn rejected_epistemic_and_mechanical_prefix_does_not_reserve_turn_or_event_sources() {
    let seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    let mut engine = Engine::new(seed.clone()).unwrap();
    let before = engine.canonical_bytes();
    let before_records = serde_json::to_vec(engine.canonical_records()).unwrap();
    let before_receipts = engine.receipts().to_vec(); // Warm the real receipt cache, too.
    let prefix = vec![
        Command::Say {
            text: "A staged claim is not an accepted event.".into(),
            audience: ["mira".into()].into(),
        },
        Command::Believe { claim_event: 1 },
        Command::Move {
            to: "dry-well".into(),
        },
        Command::Discover {
            fact: "beacon-mark".into(),
        },
        Command::Wait { ticks: 1 },
        Command::Move { to: "quay".into() },
        Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 1,
        },
    ];
    let mut rejected_commands = prefix.clone();
    rejected_commands.push(Command::UseAbility {
        ability: "blink".into(),
    });
    assert_eq!(rejected_commands.len(), MAX_COMMANDS);
    let rejected = engine.request("correctable-batch", Intent::Actions(rejected_commands));
    let rejected_proposal = Engine::proposal(&rejected).unwrap();
    assert_eq!(
        engine.commit(&rejected, &rejected_proposal, "unreachable narration"),
        Err(Error::Ability)
    );
    assert_eq!(engine.canonical_bytes(), before);
    assert_eq!(
        serde_json::to_vec(engine.canonical_records()).unwrap(),
        before_records
    );
    assert_eq!(engine.receipts(), before_receipts);
    assert_eq!(engine.revision(), 0);
    assert_eq!(
        engine.recorded(&rejected),
        Ok(None),
        "A rejected turn is not an idempotency record"
    );
    assert!(engine.state().claims.is_empty());
    assert!(!engine
        .state()
        .beliefs
        .iter()
        .any(|belief| belief.source_claim == Some(1)));
    assert!(!engine.state().discoveries.contains_key("beacon-mark"));
    assert_eq!(engine.state().items["potion"].owner, "player");

    // Reusing the failed key is allowed: no accepted request with that key exists.
    // Removing only the invalid last command exercises the very same staged prefix.
    let corrected = engine.request("correctable-batch", Intent::Actions(prefix));
    let corrected_proposal = Engine::proposal(&corrected).unwrap();
    let preview = engine.preview(&corrected, &corrected_proposal).unwrap();
    let accepted = engine
        .commit(&corrected, &corrected_proposal, preview.narration())
        .unwrap();
    assert_eq!(
        accepted
            .events()
            .iter()
            .map(|event| event.sequence())
            .collect::<Vec<_>>(),
        vec![1, 2, 3, 4, 5, 6, 7]
    );
    assert_eq!(engine.revision(), 7);
    assert_eq!(engine.canonical_record_count(), 1);
    assert_eq!(engine.receipts(), std::slice::from_ref(&accepted));
    assert_eq!(engine.state().claims.len(), 1);
    assert_eq!(engine.state().claims[0].source, 1);
    let newly_believed = engine
        .state()
        .beliefs
        .iter()
        .filter(|belief| belief.source_claim == Some(1))
        .collect::<Vec<_>>();
    assert_eq!(newly_believed.len(), 1);
    assert_eq!(newly_believed[0].source, Evidence::Event(2));
    assert_eq!(engine.state().story_time, 101);
    assert_eq!(engine.state().items["potion"].owner, "mira");
    assert_eq!(engine.state().item_transfers["potion"].sequence, 7);
    assert_eq!(engine.state().progression_sources["item:potion"], 7);
    assert_eq!(engine.state().relationships[0].obligation, 1);

    let committed = engine.canonical_bytes();
    let committed_records = serde_json::to_vec(engine.canonical_records()).unwrap();
    assert_eq!(
        engine.commit(&corrected, &corrected_proposal, accepted.narration()),
        Ok(accepted.clone()),
        "Exact stale retry must return its accepted receipt"
    );
    assert_eq!(
        engine.commit(&rejected, &rejected_proposal, "unreachable narration"),
        Err(Error::RetryMismatch),
        "After acceptance the old failed payload is a mismatched retry"
    );
    assert_eq!(engine.canonical_bytes(), committed);
    assert_eq!(
        serde_json::to_vec(engine.canonical_records()).unwrap(),
        committed_records
    );
    assert_eq!(engine.receipts(), &[accepted]);

    let replayed = Engine::replay(seed.clone(), engine.receipts()).unwrap();
    let history = engine
        .receipts()
        .iter()
        .map(|receipt| serde_json::to_string(receipt).unwrap())
        .collect::<Vec<_>>();
    let restored = Engine::restore(seed, &history).unwrap();
    for rebuilt in [replayed, restored] {
        assert_eq!(rebuilt.canonical_bytes(), committed);
        assert_eq!(rebuilt.receipts(), engine.receipts());
        assert_eq!(rebuilt.recorded(&corrected), engine.recorded(&corrected));
        assert_eq!(rebuilt.recorded(&rejected), Err(Error::RetryMismatch));
    }
}
