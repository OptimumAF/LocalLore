//! Public-API oracles frozen before private canonical-byte accounting changes.
//! Synthetic only; these tests never inspect or reproduce an Engine byte counter.
use locallore::{
    author_correction::{AuthorCorrectionInputV1, AuthorCorrectionOperationV1},
    contracts::*,
    engine::{AcceptedHistoryBasis, Engine},
};
use sha2::{Digest, Sha256};

fn fixture() -> Engine {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    seed.facts.get_mut("relic-location").unwrap().proposition = "BEFORE".into();
    Engine::new(seed).unwrap()
}

fn dialogue(text: &str) -> Intent {
    Intent::Dialogue {
        text: text.into(),
        audience: ["mira".into()].into(),
    }
}

fn append(engine: &mut Engine, key: &str, intent: Intent) -> Receipt {
    let request = engine.request(key, intent);
    let proposal = Engine::proposal(&request).unwrap();
    let preview = engine.preview(&request, &proposal).unwrap();
    let receipt = engine
        .commit(&request, &proposal, preview.narration())
        .unwrap();
    assert_eq!(receipt, preview);
    receipt
}

fn records(engine: &Engine) -> Vec<String> {
    engine
        .canonical_records()
        .iter()
        .map(|record| serde_json::to_string(record).unwrap())
        .collect()
}

fn actual_bytes(engine: &Engine) -> usize {
    records(engine).iter().map(String::len).sum()
}

fn snapshot(engine: &Engine) -> (Vec<u8>, [u8; 32], usize, AcceptedHistoryBasis) {
    (
        engine.canonical_bytes(),
        Sha256::digest(serde_json::to_vec(engine.canonical_records()).unwrap()).into(),
        actual_bytes(engine),
        engine.accepted_history_basis().unwrap(),
    )
}

#[test]
fn actual_encoded_record_history_crosses_real_byte_cap_before_record_count_cap() {
    let mut seed = fixture().seed().clone();
    seed.id = "s".repeat(64);
    // Seed evidence must name this actual synthetic seed, as normal validation
    // requires; preserve all original beliefs and commitments.
    for belief in &mut seed.beliefs {
        belief.source = Evidence::Seed(seed.id.clone());
    }
    for commitment in seed.commitments.values_mut() {
        commitment.source = Evidence::Seed(seed.id.clone());
    }
    seed.scope.story = "t".repeat(64);
    seed.scope.branch = "b".repeat(64);
    let mut engine = Engine::new(seed).unwrap();
    append(
        &mut engine,
        "escaped",
        dialogue(&"\\".repeat(MAX_TEXT_BYTES)),
    );
    append(&mut engine, "unicode", dialogue("spoken \\\"雪🙂\n"));
    let mut total = actual_bytes(&engine);
    let mut crossed = false;
    for index in 0..MAX_HISTORY_RECEIPTS {
        let key = format!("budget-{index:057}");
        assert_eq!(key.len(), 64);
        let request = engine.request(
            &key,
            Intent::Actions(vec![Command::Wait { ticks: 1 }; MAX_COMMANDS]),
        );
        let proposal = Engine::proposal(&request).unwrap();
        let preview = engine.preview(&request, &proposal).unwrap();
        // All inputs are real Domain1 typed turns; LegacyPlay serializes this
        // native receipt directly. No fabricated or padded persisted record.
        let encoded = serde_json::to_vec(&preview).unwrap();
        assert!(encoded.len() > MAX_HISTORY_BYTES / MAX_HISTORY_RECEIPTS);
        assert!(encoded.len() <= MAX_RECEIPT_BYTES);
        let would_cross = total.checked_add(encoded.len()).unwrap() > MAX_HISTORY_BYTES;
        let before = would_cross.then(|| snapshot(&engine));
        match engine.commit(&request, &proposal, preview.narration()) {
            Ok(actual) => {
                assert!(!would_cross, "accepted history exceeded its byte budget");
                assert_eq!(actual, preview);
                let accepted =
                    serde_json::to_vec(engine.canonical_records().last().unwrap()).unwrap();
                assert_eq!(accepted, encoded);
                total += accepted.len();
            }
            Err(Error::TooLarge) => {
                assert!(
                    would_cross,
                    "another limit prevented reaching the byte boundary"
                );
                assert!(engine.canonical_record_count() < MAX_HISTORY_RECEIPTS);
                assert_eq!(actual_bytes(&engine), total);
                assert!(total <= MAX_HISTORY_BYTES);
                assert!(total + encoded.len() > MAX_HISTORY_BYTES);
                assert_eq!(snapshot(&engine), before.unwrap());
                // Repeating the real rejected admission must not consume bytes.
                assert_eq!(
                    engine.commit(&request, &proposal, preview.narration()),
                    Err(Error::TooLarge)
                );
                assert_eq!(actual_bytes(&engine), total);
                crossed = true;
                break;
            }
            Err(error) => panic!("unexpected byte-boundary rejection: {error:?}"),
        }
    }
    assert!(
        crossed,
        "public fixture failed to reach the canonical byte limit"
    );
}

#[test]
fn escaped_dialogue_uses_actual_utf8_json_bytes_and_rejects_projection_overflow_atomically() {
    let mut engine = fixture();
    let unicode = "\\\"雪🙂\nspoken";
    let receipt = append(&mut engine, "unicode", dialogue(unicode));
    match receipt.events()[0].outcome() {
        Effect::Said(claim) => assert_eq!(claim.text, unicode),
        other => panic!("expected actual spoken outcome, got {other:?}"),
    }
    let text = "\\".repeat(MAX_TEXT_BYTES);
    let mut reached_projection_limit = false;
    for index in 0..MAX_HISTORY_RECEIPTS {
        let request = engine.request(&format!("escaped-{index}"), dialogue(&text));
        let proposal = Engine::proposal(&request).unwrap();
        let preview = engine.preview(&request, &proposal).unwrap();
        let encoded = serde_json::to_vec(&preview).unwrap();
        assert!(encoded.len() > text.len());
        assert!(encoded.len() <= MAX_RECEIPT_BYTES);
        let before = snapshot(&engine);
        match engine.commit(&request, &proposal, preview.narration()) {
            Ok(actual) => {
                assert_eq!(actual, preview);
                assert_eq!(records(&engine).last().unwrap().as_bytes(), encoded);
            }
            Err(Error::TooLarge) => {
                // Say retains its text in Projection.claims. This is deliberately
                // NOT mislabeled as reaching the 16MiB canonical-history limit.
                assert!(before.2 + encoded.len() < MAX_HISTORY_BYTES);
                assert!(engine.canonical_record_count() < MAX_HISTORY_RECEIPTS);
                assert_eq!(snapshot(&engine), before);
                reached_projection_limit = true;
                break;
            }
            Err(error) => panic!("unexpected dialogue rejection: {error:?}"),
        }
    }
    assert!(reached_projection_limit);
    let small = append(
        &mut engine,
        "after-rejection",
        Intent::Actions(vec![Command::Wait { ticks: 1 }]),
    );
    assert_eq!(
        engine.canonical_records().last().unwrap().receipt(),
        Some(&small)
    );
    assert!(actual_bytes(&engine) <= MAX_HISTORY_BYTES);
}

#[test]
fn clone_historical_fork_author_and_replay_keep_actual_records_without_failed_append_drift() {
    let mut parent = fixture();
    append(&mut parent, "one", dialogue("\\\\雪🙂"));
    append(&mut parent, "two", dialogue("second spoken line"));
    let fork_at = parent.revision();
    let prefix = records(&parent);
    append(
        &mut parent,
        "later-parent",
        dialogue("excluded later parent"),
    );
    let parent_before = snapshot(&parent);
    let mut child = parent.fork("ordinary-child", fork_at).unwrap();
    assert_eq!(records(&child), prefix);
    let untouched_clone = child.clone();
    append(&mut child, "child-line", dialogue("child \\\"雪🙂"));
    assert_eq!(records(&untouched_clone), prefix);
    assert_eq!(snapshot(&parent), parent_before);

    let replay_parent = Engine::restore(parent.seed().clone(), &prefix).unwrap();
    let replay_child = replay_parent
        .fork("ordinary-child", fork_at)
        .unwrap()
        .restore_continuation(&records(&child)[prefix.len()..])
        .unwrap();
    assert_eq!(snapshot(&replay_child), snapshot(&child));

    let input = AuthorCorrectionInputV1 {
        version: 1,
        parent: child.scope().clone(),
        expected_parent_revision: child.revision(),
        fork_revision: child.revision(),
        child_branch: "author-child".into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(),
            expected_proposition: "BEFORE".into(),
            replacement: "AFTER \\ 雪🙂".into(),
        },
        reason: "synthetic private reason \\ 雪🙂".into(),
    };
    let before = snapshot(&child);
    assert!(matches!(
        child.prepare_author_correction(&input, &|| true),
        Err(Error::Cancelled)
    ));
    assert_eq!(snapshot(&child), before);
    let prepared = child.prepare_author_correction(&input, &|| false).unwrap();
    assert!(matches!(
        child.apply_author_correction(&prepared, &|| true),
        Err(Error::Cancelled)
    ));
    assert_eq!(snapshot(&child), before);
    let mut authored = child
        .apply_author_correction(&prepared, &|| false)
        .unwrap()
        .engine;
    assert_eq!(authored.domain_version(), 2);
    let receipt = append(
        &mut authored,
        "authored-line",
        dialogue("authored spoken \\ 雪🙂"),
    );
    let accepted = snapshot(&authored);
    assert_eq!(authored.commit_prepared(&receipt).unwrap(), receipt);
    assert_eq!(snapshot(&authored), accepted);

    let request = authored.request("bad-narration", dialogue("never appended"));
    let proposal = Engine::proposal(&request).unwrap();
    assert_eq!(
        authored.commit(&request, &proposal, "incorrect narration"),
        Err(Error::Narration)
    );
    assert_eq!(snapshot(&authored), accepted);
    append(
        &mut authored,
        "after-failure",
        dialogue("valid after rejection"),
    );
    let replay_authored = replay_child
        .restore_continuation(&records(&authored)[child.canonical_record_count()..])
        .unwrap();
    assert_eq!(snapshot(&replay_authored), snapshot(&authored));
    assert_eq!(snapshot(&child), before);
    assert!(actual_bytes(&authored) <= MAX_HISTORY_BYTES);
}
