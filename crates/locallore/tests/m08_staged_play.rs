//! Source-frozen before the new stage implementation; uncompiled/unrun at freeze.
//! Actual Core histories only. No provider, Store, proposed receipt or wire authority.
use locallore::{author_correction::*, contracts::*, engine::Engine};
use serde_json::Value;

const A: &str = "OBSERVED_A_BEFORE_CORRECTION";
const B: &str = "ACTUAL_NEW_OBSERVED_B";
const C: &str = "ACTUAL_OTHER_SOURCE_C";
const REASON: &str = "PRIVATE_STAGING_AUTHOR_REASON";
const SECRET: &str = "PRIVATE_PLAYER_KNOWN_NOT_NEW";

fn fixture() -> Engine {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    let fact = seed.facts.get_mut("relic-location").unwrap();
    fact.proposition = A.into();
    fact.discoverable_at = Some("quay".into());
    fact.known_by.insert("mira".into());
    seed.facts.get_mut("ancestry").unwrap().proposition = SECRET.into();
    Engine::new(seed).unwrap()
}
fn correct(parent: &Engine, branch: &str, old: &str, new: &str) -> Engine {
    let request = AuthorCorrectionInputV1 {
        version: 1,
        parent: parent.scope().clone(),
        expected_parent_revision: parent.revision(),
        fork_revision: parent.revision(),
        child_branch: branch.into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(),
            expected_proposition: old.into(),
            replacement: new.into(),
        },
        reason: REASON.into(),
    };
    let plan = parent
        .prepare_author_correction(&request, &|| false)
        .unwrap();
    parent
        .apply_author_correction(&plan, &|| false)
        .unwrap()
        .engine
}
fn commit(engine: &mut Engine, key: &str, commands: Vec<Command>) -> Receipt {
    let request = engine.request(key, Intent::Actions(commands));
    let proposal = Engine::proposal(&request).unwrap();
    let preview = engine.preview(&request, &proposal).unwrap();
    engine.commit_prepared(&preview).unwrap()
}
fn free(engine: &Engine, key: &str, kind: PlayInputKind, text: &str) -> Request {
    engine.request(
        key,
        Intent::FreeText {
            kind,
            text: text.into(),
        },
    )
}
fn make_proposal(request: &Request, commands: Vec<Command>) -> Proposal {
    Proposal {
        version: VERSION,
        scope: request.scope.clone(),
        turn: request.turn.clone(),
        expected_revision: request.expected_revision,
        commands,
    }
}
fn discover() -> Command {
    Command::Discover {
        fact: "relic-location".into(),
    }
}
fn stage(engine: &Engine, request: &Request, proposal: &Proposal) -> (Receipt, Value) {
    let before = engine.canonical_bytes();
    let basis = engine.accepted_history_basis().unwrap();
    let count = engine.canonical_record_count();
    let staged = engine.stage_play_v25(request, proposal, &|| false).unwrap();
    let approved = staged.approved().clone();
    let evidence = serde_json::to_value(staged.narrator_evidence()).unwrap();
    assert_eq!(approved.request(), request);
    assert_eq!(approved.proposal(), proposal);
    assert_eq!(evidence["version"], 2);
    assert_eq!(evidence["mechanical_summary"], approved.narration());
    assert_eq!(
        evidence["events"].as_array().unwrap().len(),
        approved.events().len()
    );
    for (safe, actual) in evidence["events"]
        .as_array()
        .unwrap()
        .iter()
        .zip(approved.events())
    {
        assert_eq!(safe["event_id"], actual.sequence());
        assert!(safe.get("outcome").is_some());
    }
    assert!(serde_json::to_vec(&evidence).unwrap().len() <= MAX_RECEIPT_BYTES);
    drop(staged);
    assert_eq!(engine.canonical_bytes(), before);
    assert_eq!(engine.accepted_history_basis().unwrap(), basis);
    assert_eq!(engine.canonical_record_count(), count);
    (approved, evidence)
}
fn assert_no_private(evidence: &Value, extra: &[&str]) {
    fn keys(value: &Value) {
        match value {
            Value::Object(map) => {
                for (key, value) in map {
                    assert!(
                        ![
                            "request",
                            "proposal",
                            "input",
                            "audience",
                            "listeners",
                            "truth",
                            "truth_source",
                            "before",
                            "reason",
                            "original_input",
                            "observations_history"
                        ]
                        .contains(&key.as_str()),
                        "private key {key}"
                    );
                    keys(value);
                }
            }
            Value::Array(values) => values.iter().for_each(keys),
            _ => {}
        }
    }
    keys(evidence);
    let encoded = serde_json::to_string(evidence).unwrap();
    for hidden in [REASON, SECRET].into_iter().chain(extra.iter().copied()) {
        assert!(
            !encoded.contains(hidden),
            "unexpected private fixture value {hidden}"
        );
    }
}
fn assert_observation(evidence: &Value, sequence: u64, proposition: &str) {
    let rows = evidence["observations"].as_array().unwrap();
    assert_eq!(rows.len(), 1);
    assert_eq!(rows[0]["event_id"], sequence);
    assert_eq!(rows[0]["actor"], "player");
    assert_eq!(rows[0]["fact"], "relic-location");
    assert_eq!(rows[0]["proposition"], proposition);
    assert_eq!(rows[0].as_object().unwrap().len(), 4);
}

#[test]
fn staged_domain2_discovery_matches_actual_core_candidate_and_not_old_observed_value() {
    let engine = correct(&fixture(), "corrected", A, B);
    assert_eq!(engine.domain_version(), 2);
    assert_eq!(
        engine
            .observed_facts("player", engine.scope(), engine.revision())
            .unwrap()["relic-location"]
            .proposition,
        A
    );
    let request = free(
        &engine,
        "discover",
        PlayInputKind::Action,
        "I discover relic-location.",
    );
    let proposal = make_proposal(&request, vec![discover()]);
    assert!(matches!(
        engine.preview(&request, &proposal),
        Err(Error::Version)
    ));
    let (approved, evidence) = stage(&engine, &request, &proposal);
    assert_observation(&evidence, 2, B);
    assert_no_private(&evidence, &[A]);

    // Independent actual typed append, not supplied events/expected JSON.
    let mut actual = engine.clone();
    let committed = commit(&mut actual, "discover", vec![discover()]);
    assert_eq!(approved.events(), committed.events());
    let actor = actual
        .actor_receipts_v2("player", actual.scope(), actual.revision())
        .unwrap()
        .pop()
        .unwrap();
    let discovery = actor.events[0].discovery.as_ref().unwrap();
    assert_eq!(
        discovery.proposition,
        evidence["observations"][0]["proposition"]
    );
    assert_eq!(
        actual
            .observed_facts("mira", actual.scope(), actual.revision())
            .unwrap()["relic-location"]
            .proposition,
        A
    );
}

#[test]
fn no_discovery_has_no_known_fact_or_old_history_even_for_the_player() {
    let mut engine = correct(&fixture(), "corrected", A, B);
    commit(
        &mut engine,
        "private-history",
        vec![Command::Say {
            text: "PRIVATE_PRIOR_STAGING_HISTORY".into(),
            audience: ["player".into()].into(),
        }],
    );
    let request = free(
        &engine,
        "wait",
        PlayInputKind::Action,
        "I wait for one tide tick.",
    );
    let proposal = make_proposal(&request, vec![Command::Wait { ticks: 1 }]);
    let (approved, evidence) = stage(&engine, &request, &proposal);
    assert!(evidence["observations"].as_array().unwrap().is_empty());
    assert_eq!(approved.events().len(), 1);
    assert_no_private(
        &evidence,
        &[
            A,
            B,
            "PRIVATE_PRIOR_STAGING_HISTORY",
            "relic-location",
            "ancestry",
        ],
    );
}

#[test]
fn spoken_words_and_audience_are_only_in_approved_receipt_never_narrator_evidence() {
    let engine = correct(&fixture(), "corrected", A, B);
    let words = "RAW_STAGING_UTTERANCE is merely a claim, never world truth.";
    let request = free(&engine, "dialogue", PlayInputKind::Dialogue, words);
    let proposal = make_proposal(
        &request,
        vec![Command::Say {
            text: words.into(),
            audience: ["mira".into()].into(),
        }],
    );
    let (approved, evidence) = stage(&engine, &request, &proposal);
    assert!(serde_json::to_string(&approved)
        .unwrap()
        .contains("RAW_STAGING_UTTERANCE"));
    assert!(matches!(approved.events()[0].outcome(), Effect::Said(_)));
    assert!(evidence["observations"].as_array().unwrap().is_empty());
    assert_no_private(&evidence, &[A, B, words, "RAW_STAGING_UTTERANCE", "mira"]);
}

#[test]
fn double_prior_discovery_reobserve_and_a_b_a_keep_this_event_value_only() {
    let mut b = correct(&fixture(), "b", A, B);
    let double = commit(&mut b, "double", vec![discover(), discover()]);
    assert_eq!(double.events().len(), 2);
    let prior = b
        .actor_receipts_v2("player", b.scope(), b.revision())
        .unwrap();
    assert_eq!(prior.last().unwrap().events.len(), 2);
    for event in &prior.last().unwrap().events {
        assert_eq!(event.discovery.as_ref().unwrap().proposition, B);
    }
    let reobserve = free(
        &b,
        "reobserve",
        PlayInputKind::Action,
        "I discover relic-location.",
    );
    let (_, b_evidence) = stage(&b, &reobserve, &make_proposal(&reobserve, vec![discover()]));
    assert_observation(&b_evidence, 4, B);
    assert_eq!(b_evidence["observations"].as_array().unwrap().len(), 1);

    let a = correct(&b, "back-to-a", B, A);
    assert_eq!(
        a.observed_facts("player", a.scope(), a.revision()).unwrap()["relic-location"].proposition,
        B
    );
    let request = free(
        &a,
        "observe-a",
        PlayInputKind::Action,
        "I discover relic-location.",
    );
    let (approved, a_evidence) = stage(&a, &request, &make_proposal(&request, vec![discover()]));
    assert_observation(&a_evidence, 5, A);
    assert_no_private(&a_evidence, &[B]);
    let mut actual = a.clone();
    let appended = commit(&mut actual, "observe-a", vec![discover()]);
    assert_eq!(approved.events(), appended.events());
    let inherited = actual
        .actor_receipts_v2("player", actual.scope(), actual.revision())
        .unwrap();
    assert_eq!(
        inherited[0].events[0]
            .discovery
            .as_ref()
            .unwrap()
            .proposition,
        B
    );
    assert_eq!(
        inherited.last().unwrap().events[0]
            .discovery
            .as_ref()
            .unwrap()
            .proposition,
        A
    );
    assert_observation(&b_evidence, 4, B); // detached evidence was not relabeled
}

#[test]
fn equal_scope_head_and_mechanics_do_not_replace_actual_source_observation() {
    let root = fixture();
    let b = correct(&root, "same-child", A, B);
    let c = correct(&root, "same-child", A, C);
    assert_eq!(b.scope(), c.scope());
    assert_eq!(b.revision(), c.revision());
    assert_eq!(b.state(), c.state());
    assert_ne!(
        b.accepted_history_basis().unwrap(),
        c.accepted_history_basis().unwrap()
    );
    let request = free(
        &b,
        "same-request",
        PlayInputKind::Action,
        "I discover relic-location.",
    );
    let proposal = make_proposal(&request, vec![discover()]);
    let (b_approved, b_evidence) = stage(&b, &request, &proposal);
    let (c_approved, c_evidence) = stage(&c, &request, &proposal);
    assert_eq!(b_approved.events(), c_approved.events());
    assert_observation(&b_evidence, 2, B);
    assert_observation(&c_evidence, 2, C);
    assert_no_private(&b_evidence, &[A, C]);
    assert_no_private(&c_evidence, &[A, B]);
}

#[test]
fn new_stage_keeps_scope_head_version_identity_and_finite_agency_checks() {
    let engine = correct(&fixture(), "corrected", A, B);
    let before = engine.canonical_bytes();
    let request = free(
        &engine,
        "guarded",
        PlayInputKind::Action,
        "I wait for one tide tick.",
    );
    let proposal = make_proposal(&request, vec![Command::Wait { ticks: 1 }]);
    let mut wrong = request.clone();
    wrong.version = 2;
    assert!(matches!(
        engine.stage_play_v25(&wrong, &proposal, &|| false),
        Err(Error::Version)
    ));
    wrong = request.clone();
    wrong.scope.branch = "foreign-child".into();
    let mut wrong_proposal = proposal.clone();
    wrong_proposal.scope = wrong.scope.clone();
    assert!(matches!(
        engine.stage_play_v25(&wrong, &wrong_proposal, &|| false),
        Err(Error::Scope)
    ));
    wrong = request.clone();
    wrong.expected_revision = 0;
    wrong_proposal = proposal.clone();
    wrong_proposal.expected_revision = 0;
    assert!(matches!(
        engine.stage_play_v25(&wrong, &wrong_proposal, &|| false),
        Err(Error::Stale)
    ));
    wrong_proposal = proposal.clone();
    wrong_proposal.turn = "other-turn".into();
    assert!(matches!(
        engine.stage_play_v25(&request, &wrong_proposal, &|| false),
        Err(Error::Rule)
    ));
    wrong_proposal = proposal.clone();
    wrong_proposal.commands = vec![Command::Wait { ticks: 2 }];
    assert!(matches!(
        engine.stage_play_v25(&request, &wrong_proposal, &|| false),
        Err(Error::Agency)
    ));
    let unsupported = free(
        &engine,
        "unsupported",
        PlayInputKind::Action,
        "I juggle clouds.",
    );
    assert!(matches!(
        engine.stage_play_v25(
            &unsupported,
            &make_proposal(&unsupported, vec![Command::Wait { ticks: 1 }]),
            &|| false
        ),
        Err(Error::ClarificationRequired)
    ));
    let typed = engine.request("not-free-text", Intent::Actions(vec![discover()]));
    assert!(matches!(
        engine.stage_play_v25(&typed, &Engine::proposal(&typed).unwrap(), &|| false),
        Err(Error::Agency)
    ));
    assert!(matches!(
        engine.preview(&request, &proposal),
        Err(Error::Version)
    ));
    assert_eq!(engine.canonical_bytes(), before);
}

#[test]
fn cancellation_panic_drop_and_maximal_escaped_values_never_mutate_source_or_truncate() {
    let escaped = "\u{0001}".repeat(MAX_TEXT_BYTES);
    let engine = correct(&fixture(), "escaped", A, &escaped);
    let before = engine.canonical_bytes();
    let request = free(
        &engine,
        "escaped-discovery",
        PlayInputKind::Action,
        "I discover relic-location.",
    );
    let proposal = make_proposal(&request, vec![discover()]);
    assert!(matches!(
        engine.stage_play_v25(&request, &proposal, &|| true),
        Err(Error::Cancelled)
    ));
    assert!(matches!(
        engine.stage_play_v25(&request, &proposal, &|| panic!(
            "synthetic stage cancellation panic"
        )),
        Err(Error::Cancelled)
    ));
    assert_eq!(engine.canonical_bytes(), before);
    let (_, evidence) = stage(&engine, &request, &proposal);
    assert_observation(&evidence, 2, &escaped);
    let encoded = serde_json::to_vec(&evidence).unwrap();
    assert!(encoded.len() > MAX_TEXT_BYTES);
    assert!(encoded.len() <= MAX_RECEIPT_BYTES);
    let roundtrip: Value = serde_json::from_slice(&encoded).unwrap();
    assert_eq!(
        roundtrip["observations"][0]["proposition"]
            .as_str()
            .unwrap()
            .as_bytes(),
        escaped.as_bytes()
    );
    let oversized = free(
        &engine,
        "too-long",
        PlayInputKind::Action,
        &"x".repeat(MAX_TEXT_BYTES + 1),
    );
    assert!(matches!(
        engine.stage_play_v25(
            &oversized,
            &make_proposal(&oversized, vec![discover()]),
            &|| { false }
        ),
        Err(Error::TooLarge)
    ));
    assert_eq!(engine.canonical_bytes(), before);
    assert_eq!(engine.revision(), 1);
}
