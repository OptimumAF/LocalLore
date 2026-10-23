//! Frozen before production edits. Pure actual Core; no Store/model/host grant.
use locallore::{author_correction::*, contracts::*, engine::Engine};
use serde_json::json;
fn fixture() -> Engine {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    let fact = seed.facts.get_mut("relic-location").unwrap();
    fact.proposition = "KNOWN_A".into();
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
        reason: "PRIVATE_AUTHOR_REASON".into(),
    }
}
fn correct(e: &Engine, child: &str, old: &str, new: &str) -> Engine {
    let p = e
        .prepare_author_correction(&input(e, child, e.revision(), old, new), &|| false)
        .unwrap();
    e.apply_author_correction(&p, &|| false).unwrap().engine
}
fn commit(e: &mut Engine, key: &str, commands: Vec<Command>) -> Receipt {
    let r = e.request(key, Intent::Actions(commands));
    let p = Engine::proposal(&r).unwrap();
    let v = e.preview(&r, &p).unwrap();
    e.commit_prepared(&v).unwrap()
}
#[test]
fn known_player_npc_values_survive_private_truth_correction_without_mechanical_change() {
    let e = fixture();
    let before = e.canonical_bytes();
    let c = correct(&e, "corrected", "KNOWN_A", "PRIVATE_B");
    assert_eq!(e.canonical_bytes(), before);
    assert_eq!(e.revision(), 0);
    assert_eq!(c.revision(), 1);
    assert_eq!(c.domain_version(), 2);
    assert_eq!(c.state(), e.state());
    assert_eq!(
        c.effective_fact("relic-location").unwrap().proposition,
        "PRIVATE_B"
    );
    for actor in ["player", "mira"] {
        let values = c.observed_facts(actor, c.scope(), c.revision()).unwrap();
        assert_eq!(values["relic-location"].proposition, "KNOWN_A");
        let view = serde_json::to_string(
            &c.character_context_v2(actor, c.scope(), c.revision())
                .unwrap(),
        )
        .unwrap();
        for hidden in [
            "PRIVATE_B",
            "PRIVATE_AUTHOR_REASON",
            "truth_source",
            "stale",
        ] {
            assert!(!view.contains(hidden), "{view}");
        }
    }
    assert!(!c
        .observed_facts("sable", c.scope(), c.revision())
        .unwrap()
        .contains_key("relic-location"));
    assert_eq!(
        c.character_context("player", c.scope(), c.revision()),
        Err(Error::Version)
    );
}
#[test]
fn uniform_discovery_reconfirms_same_value_and_updates_only_player_exactly_once_per_request() {
    let mut c = correct(&fixture(), "corrected", "KNOWN_A", "PRIVATE_B");
    let r = commit(
        &mut c,
        "discover",
        vec![Command::Discover {
            fact: "relic-location".into(),
        }],
    );
    assert_eq!(
        c.observed_facts("player", c.scope(), c.revision()).unwrap()["relic-location"].proposition,
        "PRIVATE_B"
    );
    assert_eq!(
        c.observed_facts("mira", c.scope(), c.revision()).unwrap()["relic-location"].proposition,
        "KNOWN_A"
    );
    let count = c.canonical_record_count();
    assert_eq!(c.commit_prepared(&r).unwrap(), r);
    assert_eq!(c.canonical_record_count(), count);
    commit(
        &mut c,
        "reconfirm",
        vec![
            Command::Discover {
                fact: "relic-location".into(),
            },
            Command::Discover {
                fact: "relic-location".into(),
            },
        ],
    );
    assert_eq!(c.revision(), 4);
    assert_eq!(c.canonical_record_count(), 3);
    assert!(!serde_json::to_string(c.receipts())
        .unwrap()
        .contains("truth"));
}
#[test]
fn returning_to_old_text_keeps_distinct_canonical_sources_without_actor_flags() {
    let a = fixture();
    let b = correct(&a, "b", "KNOWN_A", "PRIVATE_B");
    let aa = correct(&b, "aa", "PRIVATE_B", "KNOWN_A");
    assert_eq!(
        aa.effective_fact("relic-location").unwrap().proposition,
        "KNOWN_A"
    );
    assert_eq!(aa.revision(), 2);
    assert_ne!(aa.canonical_bytes(), a.canonical_bytes());
    let text = serde_json::to_string(
        &aa.observed_facts("mira", aa.scope(), aa.revision())
            .unwrap(),
    )
    .unwrap();
    assert!(!text.contains("PRIVATE_B") && !text.contains("author") && !text.contains("stale"));
    assert_eq!(aa.receipts().len(), 0);
    assert_eq!(aa.canonical_record_count(), 2);
}
#[test]
fn completed_boundaries_author_head_prefix_and_legacy_receipt_cache_are_independent() {
    let mut e = fixture();
    commit(
        &mut e,
        "multi",
        vec![Command::Wait { ticks: 1 }, Command::Wait { ticks: 1 }],
    );
    let bad = input(&e, "bad", 1, "KNOWN_A", "B");
    assert!(matches!(
        e.prepare_author_correction(&bad, &|| false),
        Err(Error::Rule)
    ));
    let cached = e.receipts().to_vec();
    let c = correct(&e, "corrected", "KNOWN_A", "B");
    assert_eq!(c.completed_boundaries(), vec![0, 2, 3]);
    assert_eq!(c.receipts(), cached);
    assert_eq!(c.canonical_record_count(), 2);
    let old = c.fork("preauthor", 2).unwrap();
    assert_eq!(old.domain_version(), 1);
    assert_eq!(old.receipts(), cached);
    assert_eq!(
        old.effective_fact("relic-location").unwrap().proposition,
        "KNOWN_A"
    );
    assert!(!old.extends_accepted_history(&c).unwrap());
    assert_ne!(
        c.accepted_history_basis().unwrap(),
        e.accepted_history_basis().unwrap()
    );
}
#[test]
fn mixed_restore_continuation_rechecks_bindings_and_rejects_private_record_forgery() {
    let parent = fixture();
    let mut c = correct(&parent, "corrected", "KNOWN_A", "PRIVATE_B");
    commit(
        &mut c,
        "discover",
        vec![Command::Discover {
            fact: "relic-location".into(),
        }],
    );
    let strings: Vec<String> = c
        .canonical_records()
        .iter()
        .map(|r| serde_json::to_string(r).unwrap())
        .collect();
    let base = parent.fork("corrected", 0).unwrap();
    let restored = base.restore_continuation(&strings).unwrap();
    assert_eq!(restored.canonical_bytes(), c.canonical_bytes());
    assert_eq!(restored.canonical_records(), c.canonical_records());
    for (index, field, value) in [
        (0, "sequence", json!(7)),
        (0, "witnesses", json!(["player"])),
    ] {
        let mut bad = strings.clone();
        let mut v: serde_json::Value = serde_json::from_str(&bad[index]).unwrap();
        v["receipt"][field] = value;
        bad[index] = v.to_string();
        assert!(base.restore_continuation(&bad).is_err());
    }
    let mut bad = strings.clone();
    let mut v: serde_json::Value = serde_json::from_str(&bad[1]).unwrap();
    v["observations"][0]["truth"] = json!({"author":{"source":{"original_scope":{"story":"foreign","branch":"sibling"},"sequence":1}}});
    bad[1] = v.to_string();
    assert!(base.restore_continuation(&bad).is_err());
}
#[test]
fn plan_stale_expected_value_cancel_and_bounded_input_leave_parent_unchanged() {
    let mut e = fixture();
    let before = e.canonical_bytes();
    let good = input(&e, "child", 0, "KNOWN_A", "B");
    let p = e.prepare_author_correction(&good, &|| false).unwrap();
    assert!(matches!(
        e.apply_author_correction(&p, &|| true),
        Err(Error::Cancelled)
    ));
    assert_eq!(e.canonical_bytes(), before);
    for mut bad in [
        input(&e, "child", 0, "wrong", "B"),
        input(&e, "child", 0, "KNOWN_A", "KNOWN_A"),
        input(&e, "../bad", 0, "KNOWN_A", "B"),
    ] {
        assert!(e.prepare_author_correction(&bad, &|| false).is_err());
        bad.reason = "x".repeat(2049);
        assert!(e.prepare_author_correction(&bad, &|| false).is_err());
    }
    commit(&mut e, "advance", vec![Command::Wait { ticks: 1 }]);
    assert!(matches!(
        e.apply_author_correction(&p, &|| false),
        Err(Error::Stale)
    ));
}
#[test]
fn actor_event_and_receipt_views_omit_author_records_and_raw_player_text() {
    let mut c = correct(&fixture(), "child", "KNOWN_A", "PRIVATE_B");
    commit(
        &mut c,
        "private-say",
        vec![Command::Say {
            text: "PRIVATE_PLAYER_INPUT".into(),
            audience: ["player".into()].into(),
        }],
    );
    let views = c
        .actor_receipts_v2("mira", c.scope(), c.revision())
        .unwrap();
    let serialized = serde_json::to_string(&views).unwrap();
    for private in [
        "PRIVATE_AUTHOR_REASON",
        "PRIVATE_B",
        "PRIVATE_PLAYER_INPUT",
        "request",
        "proposal",
        "narration",
    ] {
        assert!(!serialized.contains(private), "{serialized}");
    }
    assert!(views.is_empty());
}

#[test]
fn fixed_author_key_remains_valid_for_ordinary_legacy_turns() {
    let mut e = fixture();
    let r = commit(
        &mut e,
        "author-correction-v1",
        vec![Command::Wait { ticks: 1 }],
    );
    assert_eq!(e.recorded(r.request()).unwrap(), Some(r));
    assert_eq!(e.domain_version(), 1);
}
#[test]
fn actual_author_record_reserves_its_own_scoped_key_against_ordinary_requests() {
    let c = correct(&fixture(), "child", "KNOWN_A", "B");
    assert_eq!(c.canonical_records()[0].turn_key(), "author-correction-v1");
    let r = c.request(
        "author-correction-v1",
        Intent::Actions(vec![Command::Wait { ticks: 1 }]),
    );
    assert_eq!(c.recorded(&r), Err(Error::RetryMismatch));
    assert_eq!(
        c.preview(&r, &Engine::proposal(&r).unwrap()),
        Err(Error::RetryMismatch)
    );
}
#[test]
fn inherited_author_or_ordinary_key_does_not_reserve_another_branch_namespace() {
    let mut e = fixture();
    commit(
        &mut e,
        "author-correction-v1",
        vec![Command::Wait { ticks: 1 }],
    );
    let c = correct(&e, "child", "KNOWN_A", "B");
    let mut other = c.fork("grandchild", c.revision()).unwrap();
    let r = commit(
        &mut other,
        "author-correction-v1",
        vec![Command::Wait { ticks: 1 }],
    );
    assert_eq!(r.request().scope, *other.scope());
    assert_eq!(other.canonical_record_count(), 3);
    assert_eq!(c.canonical_record_count(), 2);
}

#[test]
fn retained_boundary_restore_preserves_creation_head_without_requiring_excluded_parent_future() {
    let mut parent = fixture();
    commit(&mut parent, "retained", vec![Command::Wait { ticks: 2 }]);
    let retained_revision = parent.revision();
    commit(&mut parent, "excluded", vec![Command::Wait { ticks: 3 }]);
    let request = input(&parent, "child", retained_revision, "KNOWN_A", "PRIVATE_B");
    let plan = parent
        .prepare_author_correction(&request, &|| false)
        .unwrap();
    assert_eq!(plan.preview().excluded_suffix_events, 1);
    assert_eq!(plan.preview().excluded_suffix_records, 1);
    let child = parent
        .apply_author_correction(&plan, &|| false)
        .unwrap()
        .engine;
    assert_eq!(
        child.state().story_time,
        parent
            .at_revision(retained_revision)
            .unwrap()
            .state()
            .story_time
    );
    assert_eq!(child.canonical_records()[0], parent.canonical_records()[0]);
    assert_eq!(child.canonical_record_count(), 2);
    let author = serde_json::to_string(&child.canonical_records()[1]).unwrap();
    let base = parent.fork("child", retained_revision).unwrap();
    let restored = base.restore_continuation(&[author]).unwrap();
    assert_eq!(restored.canonical_records(), child.canonical_records());
    assert_eq!(restored.canonical_bytes(), child.canonical_bytes());
    assert_eq!(
        restored.accepted_history_basis().unwrap(),
        child.accepted_history_basis().unwrap()
    );
    let replayed =
        Engine::replay_records(parent.seed().clone(), child.canonical_records()).unwrap();
    assert_eq!(replayed.canonical_records(), child.canonical_records());
    assert_eq!(replayed.canonical_bytes(), child.canonical_bytes());
    assert_eq!(
        child.canonical_records()[1].last_revision(),
        retained_revision + 1
    );
    assert_eq!(parent.revision(), request.expected_parent_revision);
    assert!(request.expected_parent_revision > request.fork_revision);
}

#[test]
fn inherited_author_prefix_retains_original_scopes_and_does_not_invent_ordinary_fork_lineage() {
    let root = fixture();
    let mut authored = correct(&root, "authored", "KNOWN_A", "PRIVATE_B");
    commit(
        &mut authored,
        "discover",
        vec![Command::Discover {
            fact: "relic-location".into(),
        }],
    );
    let mut grandchild = authored.fork("ordinary-fork", authored.revision()).unwrap();
    let inherited = grandchild.canonical_records().to_vec();
    commit(
        &mut grandchild,
        "ordinary-child-turn",
        vec![Command::Wait { ticks: 1 }],
    );
    assert_eq!(&grandchild.canonical_records()[..2], inherited);
    assert_eq!(
        grandchild.canonical_records()[0].original_scope(),
        authored.scope()
    );
    assert_eq!(
        grandchild
            .observed_facts("player", grandchild.scope(), grandchild.revision())
            .unwrap()["relic-location"]
            .proposition,
        "PRIVATE_B"
    );
    let base = authored.fork("ordinary-fork", authored.revision()).unwrap();
    let suffix = serde_json::to_string(&grandchild.canonical_records()[2]).unwrap();
    let restored = base.restore_continuation(&[suffix]).unwrap();
    assert_eq!(
        restored.accepted_history_basis().unwrap(),
        grandchild.accepted_history_basis().unwrap()
    );
    assert!(Engine::replay_records(root.seed().clone(), grandchild.canonical_records()).is_err());
    let before_author = grandchild.fork("prebirth", 0).unwrap();
    assert_eq!(before_author.domain_version(), 1);
    assert_eq!(before_author.canonical_record_count(), 0);
    assert_eq!(
        before_author
            .effective_fact("relic-location")
            .unwrap()
            .proposition,
        "KNOWN_A"
    );
}

#[test]
fn actor_v2_cancellation_and_legacy_version_refusal_emit_no_private_callbacks() {
    let c = correct(&fixture(), "child", "KNOWN_A", "PRIVATE_B");
    let mut callbacks = 0;
    c.visit_actor_observations_v2(
        "player",
        c.scope(),
        c.revision(),
        0,
        c.revision(),
        &|| false,
        &mut |_| {
            callbacks += 1;
            true
        },
    )
    .unwrap();
    assert_eq!(callbacks, 0);
    assert_eq!(
        c.visit_actor_observations_v2(
            "player",
            c.scope(),
            c.revision(),
            0,
            c.revision(),
            &|| panic!("synthetic cancellation"),
            &mut |_| {
                callbacks += 1;
                true
            }
        ),
        Err(Error::Cancelled)
    );
    assert_eq!(callbacks, 0);
    assert_eq!(
        c.visit_actor_observations(
            "player",
            c.scope(),
            c.revision(),
            0,
            c.revision(),
            &|| false,
            &mut |_| {
                callbacks += 1;
                true
            }
        ),
        Err(Error::Version)
    );
    assert_eq!(callbacks, 0);
    let request = c.request(
        "free-text",
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: "I wait for one tide tick.".into(),
        },
    );
    let proposal = Proposal {
        version: VERSION,
        scope: c.scope().clone(),
        turn: request.turn.clone(),
        expected_revision: c.revision(),
        commands: vec![Command::Wait { ticks: 1 }],
    };
    assert_eq!(c.preview(&request, &proposal), Err(Error::Version));
}

#[test]
fn bounded_escaped_author_text_round_trips_and_play_cache_cannot_set_canonical_head() {
    let root = fixture();
    let mut request = input(&root, "child", 0, "KNOWN_A", &"\u{0000}".repeat(2048));
    request.reason = "\u{0001}".repeat(2048);
    let plan = root.prepare_author_correction(&request, &|| false).unwrap();
    let mut child = root
        .apply_author_correction(&plan, &|| false)
        .unwrap()
        .engine;
    assert!(child.receipts().is_empty());
    assert_eq!(child.revision(), 1);
    let receipt = commit(&mut child, "after-cache", vec![Command::Wait { ticks: 1 }]);
    assert_eq!(child.receipts(), &[receipt]);
    assert_eq!(child.canonical_record_count(), 2);
    assert_eq!(child.revision(), 2);
    let encoded: Vec<String> = child
        .canonical_records()
        .iter()
        .map(|r| serde_json::to_string(r).unwrap())
        .collect();
    let restored = Engine::restore(root.seed().clone(), &encoded).unwrap();
    assert_eq!(restored.canonical_bytes(), child.canonical_bytes());
    assert_eq!(restored.canonical_records(), child.canonical_records());
}
