//! Independent, source-frozen review oracles. No model, Store, host or author grant.
use locallore::{author_correction::*, contracts::*, engine::Engine};
use serde_json::{json, Value};

fn fixture() -> Engine {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    let fact = seed.facts.get_mut("relic-location").unwrap();
    fact.proposition = "OBSERVED_A".into();
    fact.discoverable_at = Some("quay".into());
    fact.known_by.insert("mira".into());
    Engine::new(seed).unwrap()
}
fn input(e: &Engine, child: &str, at: u64, old: &str, new: &str) -> AuthorCorrectionInputV1 {
    AuthorCorrectionInputV1 {
        version: 1,
        parent: e.scope().clone(),
        expected_parent_revision: e.revision(),
        fork_revision: at,
        child_branch: child.into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(),
            expected_proposition: old.into(),
            replacement: new.into(),
        },
        reason: "PRIVATE_REVIEW_REASON".into(),
    }
}
fn correct(e: &Engine, child: &str, at: u64, old: &str, new: &str) -> Engine {
    let plan = e
        .prepare_author_correction(&input(e, child, at, old, new), &|| false)
        .unwrap();
    e.apply_author_correction(&plan, &|| false).unwrap().engine
}
fn commit(e: &mut Engine, key: &str, commands: Vec<Command>) {
    let request = e.request(key, Intent::Actions(commands));
    let proposal = Engine::proposal(&request).unwrap();
    let receipt = e.preview(&request, &proposal).unwrap();
    e.commit_prepared(&receipt).unwrap();
}
fn encoded(e: &Engine) -> Vec<String> {
    e.canonical_records()
        .iter()
        .map(|r| serde_json::to_string(r).unwrap())
        .collect()
}
fn discover(e: &mut Engine, key: &str) {
    commit(
        e,
        key,
        vec![Command::Discover {
            fact: "relic-location".into(),
        }],
    );
}

#[test]
fn event_views_keep_values_at_each_observation_across_a_b_a_truth_changes() {
    let root = fixture();
    let mut b = correct(&root, "b", 0, "OBSERVED_A", "PRIVATE_B");
    discover(&mut b, "observed-b");
    let mut a = correct(&b, "again-a", b.revision(), "PRIVATE_B", "OBSERVED_A");
    discover(&mut a, "observed-again-a");
    let player = a
        .character_context_v2("player", a.scope(), a.revision())
        .unwrap();
    let discoveries: Vec<_> = player
        .observations
        .iter()
        .filter_map(|e| e.discovery.as_ref())
        .collect();
    assert_eq!(discoveries.len(), 2);
    assert_eq!(discoveries[0].proposition, "PRIVATE_B");
    assert_eq!(discoveries[1].proposition, "OBSERVED_A");
    assert_ne!(discoveries[0].observation, discoveries[1].observation);
    assert_eq!(player.facts["relic-location"].proposition, "OBSERVED_A");
    let npc = a
        .character_context_v2("mira", a.scope(), a.revision())
        .unwrap();
    assert_eq!(npc.facts["relic-location"].proposition, "OBSERVED_A");
    let safe = serde_json::to_string(&npc).unwrap();
    for hidden in [
        "PRIVATE_B",
        "PRIVATE_REVIEW_REASON",
        "truth_overrides",
        "stale",
    ] {
        assert!(!safe.contains(hidden), "{safe}");
    }
    let replay = Engine::replay_records(root.seed().clone(), a.canonical_records()).unwrap();
    assert_eq!(replay.canonical_records(), a.canonical_records());
    assert_eq!(replay.canonical_bytes(), a.canonical_bytes());
}

#[test]
fn repeated_discovery_bindings_must_be_exact_in_count_order_and_source() {
    let root = fixture();
    let mut child = correct(&root, "child", 0, "OBSERVED_A", "PRIVATE_B");
    commit(
        &mut child,
        "twice",
        vec![
            Command::Discover {
                fact: "relic-location".into(),
            },
            Command::Discover {
                fact: "relic-location".into(),
            },
        ],
    );
    let history = encoded(&child);
    let original: Value = serde_json::from_str(&history[1]).unwrap();
    assert_eq!(original["observations"].as_array().unwrap().len(), 2);
    let mut mutations = vec![];
    let mut missing = original.clone();
    missing["observations"].as_array_mut().unwrap().pop();
    mutations.push(missing);
    let mut extra = original.clone();
    let duplicate = extra["observations"][0].clone();
    extra["observations"]
        .as_array_mut()
        .unwrap()
        .push(duplicate);
    mutations.push(extra);
    let mut reordered = original.clone();
    reordered["observations"].as_array_mut().unwrap().swap(0, 1);
    mutations.push(reordered);
    let mut foreign = original.clone();
    foreign["observations"][0]["truth"] = json!({
        "kind":"author", "source":{"original_scope":{"story":"quay","branch":"sibling"},"sequence":1}
    });
    mutations.push(foreign);
    for mutation in mutations {
        let mut bad = history.clone();
        bad[1] = mutation.to_string();
        assert!(matches!(
            Engine::restore(root.seed().clone(), &bad),
            Err(Error::CorruptHistory)
        ));
    }
    assert_eq!(
        Engine::restore(root.seed().clone(), &history)
            .unwrap()
            .canonical_records(),
        child.canonical_records()
    );
}

#[test]
fn wrapper_unknown_fields_duplicate_keys_and_unknown_kind_never_fall_back_to_legacy() {
    let root = fixture();
    let child = correct(&root, "child", 0, "OBSERVED_A", "PRIVATE_B");
    let serialized = encoded(&child)[0].clone();
    let original: Value = serde_json::from_str(&serialized).unwrap();
    let mut mutations = vec![];
    let mut unknown = original.clone();
    unknown["unexpected"] = json!(true);
    mutations.push(unknown.to_string());
    let mut kind = original.clone();
    kind["kind"] = json!("legacy");
    mutations.push(kind.to_string());
    let mut version = original.clone();
    version["record_version"] = json!(3);
    mutations.push(version.to_string());
    mutations.push(serialized.replacen(
        "\"record_version\":2",
        "\"record_version\":2,\"record_version\":2",
        1,
    ));
    for mutation in mutations {
        assert!(matches!(
            Engine::restore(root.seed().clone(), &[mutation]),
            Err(Error::CorruptHistory)
        ));
    }
}

#[test]
fn prepared_plan_rejects_equal_revision_and_projection_with_different_accepted_source() {
    let mut parent = fixture();
    let mut replacement = fixture();
    commit(&mut parent, "actual-a", vec![Command::Wait { ticks: 1 }]);
    commit(
        &mut replacement,
        "actual-b",
        vec![Command::Wait { ticks: 1 }],
    );
    assert_eq!(parent.revision(), replacement.revision());
    assert_eq!(parent.state(), replacement.state());
    assert_eq!(parent.canonical_bytes(), replacement.canonical_bytes());
    assert_ne!(
        parent.accepted_history_basis().unwrap(),
        replacement.accepted_history_basis().unwrap()
    );
    let request = input(&parent, "child", 0, "OBSERVED_A", "PRIVATE_B");
    let plan = parent
        .prepare_author_correction(&request, &|| false)
        .unwrap();
    let before = replacement.canonical_bytes();
    assert!(matches!(
        replacement.apply_author_correction(&plan, &|| false),
        Err(Error::Stale)
    ));
    assert_eq!(replacement.canonical_bytes(), before);
    assert_eq!(replacement.canonical_record_count(), 1);
}

#[test]
fn nested_authored_prebirth_snapshots_and_continuation_preserve_real_lineage() {
    let mut root = fixture();
    commit(&mut root, "retained", vec![Command::Wait { ticks: 1 }]);
    commit(
        &mut root,
        "excluded-future",
        vec![Command::Wait { ticks: 7 }],
    );
    let mut first = correct(&root, "first", 1, "OBSERVED_A", "PRIVATE_B");
    discover(&mut first, "discover-b");
    let ordinary = first.fork("ordinary", first.revision()).unwrap();
    let second = correct(
        &ordinary,
        "second",
        ordinary.revision(),
        "PRIVATE_B",
        "PRIVATE_C",
    );
    let at_one = second.at_revision(1).unwrap();
    assert_eq!(at_one.domain_version(), 1);
    assert_eq!(at_one.scope(), second.scope());
    assert_eq!(
        at_one.effective_fact("relic-location").unwrap().proposition,
        "OBSERVED_A"
    );
    let at_two = second.at_revision(2).unwrap();
    assert_eq!(at_two.domain_version(), 2);
    assert_eq!(
        at_two.effective_fact("relic-location").unwrap().proposition,
        "PRIVATE_B"
    );
    assert_eq!(at_two.canonical_records()[0].original_scope(), root.scope());
    assert_eq!(
        at_two.canonical_records()[1].original_scope(),
        first.scope()
    );
    let early = second.fork("early", 1).unwrap();
    assert_eq!(early.domain_version(), 1);
    assert_eq!(early.canonical_record_count(), 1);
    let base = ordinary.fork("second", ordinary.revision()).unwrap();
    let author = serde_json::to_string(second.canonical_records().last().unwrap()).unwrap();
    let restored = base.restore_continuation(&[author]).unwrap();
    assert_eq!(restored.canonical_records(), second.canonical_records());
    assert_eq!(
        restored.accepted_history_basis().unwrap(),
        second.accepted_history_basis().unwrap()
    );
    // Ordinary fork metadata is not encoded by a private author record from another scope.
    assert!(Engine::replay_records(root.seed().clone(), second.canonical_records()).is_err());
}

#[test]
fn npc_positive_event_receipt_still_omits_unwitnessed_raw_request_and_author_truth() {
    let root = fixture();
    let mut child = correct(&root, "child", 0, "OBSERVED_A", "PRIVATE_B");
    commit(
        &mut child,
        "private-say",
        vec![Command::Say {
            text: "PRIVATE_PLAYER_REVIEW_INPUT".into(),
            audience: ["player".into()].into(),
        }],
    );
    commit(
        &mut child,
        "visible-gift",
        vec![Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 1,
        }],
    );
    let npc = child
        .actor_receipts_v2("mira", child.scope(), child.revision())
        .unwrap();
    assert_eq!(npc.len(), 1);
    assert_eq!(npc[0].turn, "visible-gift");
    assert_eq!(npc[0].events.len(), 1);
    let serialized = serde_json::to_string(&npc).unwrap();
    for hidden in [
        "PRIVATE_PLAYER_REVIEW_INPUT",
        "PRIVATE_REVIEW_REASON",
        "PRIVATE_B",
        "request",
        "proposal",
        "narration",
    ] {
        assert!(!serialized.contains(hidden), "{serialized}");
    }
    assert!(!npc[0].events.iter().any(|e| e.discovery.is_some()));
}
