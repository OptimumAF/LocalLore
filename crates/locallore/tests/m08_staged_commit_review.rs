// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Source-frozen future staged consuming-commit oracles. Initially UNCOMPILED.
//! Genuine Receipt/PlayRecord values come from actual Play + scripted providers.
use locallore::{
    author_correction::*,
    contracts::*,
    engine::Engine,
    inference::*,
    play::{self, PlayProfile},
};
use serde_json::json;
use std::{cell::Cell, collections::VecDeque, task::Poll};

fn fixture() -> Engine {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    let fact = seed.facts.get_mut("relic-location").unwrap();
    fact.proposition = "OBSERVED_A".into();
    fact.discoverable_at = Some("quay".into());
    fact.known_by.insert("mira".into());
    Engine::new(seed).unwrap()
}
fn authored(parent: &Engine, child: &str, replacement: &str) -> Engine {
    let input = AuthorCorrectionInputV1 {
        version: 1,
        parent: parent.scope().clone(),
        expected_parent_revision: parent.revision(),
        fork_revision: parent.revision(),
        child_branch: child.into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(),
            expected_proposition: "OBSERVED_A".into(),
            replacement: replacement.into(),
        },
        reason: "PRIVATE_STAGED_COMMIT_REASON".into(),
    };
    let plan = parent.prepare_author_correction(&input, &|| false).unwrap();
    parent
        .apply_author_correction(&plan, &|| false)
        .unwrap()
        .engine
}
fn request(engine: &Engine, key: &str) -> Request {
    engine.request(
        key,
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: "I wait for one tide tick.".into(),
        },
    )
}
fn profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-staged-commit".into(),
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
    }
}
#[derive(Default)]
struct ScriptFakeProvider {
    replies: VecDeque<Vec<u8>>,
    seen: Vec<GenerationRequest>,
}
impl InferenceProvider for ScriptFakeProvider {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        _cancel: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        self.seen.push(request.clone());
        Poll::Ready(self.replies.pop_front().ok_or(Error::Provider))
    }
}
fn generated(source: &Engine, request: &Request) -> Receipt {
    let mut actual = source.clone();
    let mut provider = ScriptFakeProvider {
        // The actual valid Director reply passes ordinary parse/agency/mechanics.
        // A deliberately malformed narrator document exercises real mechanical
        // fallback; it is not prose quality or an alternate expected evaluator.
        replies: [json!({"commands":[{"op":"wait","ticks":1}]}), json!({})]
            .into_iter()
            .map(|v| serde_json::to_vec(&v).unwrap())
            .collect(),
        seen: vec![],
    };
    let receipt = play::execute(
        &mut actual,
        request,
        &mut provider,
        &Cancellation::default(),
        &profile(),
    )
    .unwrap();
    assert_eq!(provider.seen.len(), 2);
    let roles: Vec<_> = provider
        .seen
        .iter()
        .map(|r| match &r.input {
            Input::Structured { role, .. } => role.as_str(),
            _ => panic!("actual current structured roles required"),
        })
        .collect();
    assert_eq!(roles, vec!["director", "narrator"]);
    let record = receipt.play().unwrap();
    assert_eq!(record.prompt_version, "locallore-play-v2.5");
    assert_eq!(record.policy, "grounded-prose-v2.5-whole-evidence-words-v1");
    assert!(record.fallback);
    assert_eq!(record.context.as_ref().unwrap().version, 2);
    assert_eq!(record.context.as_ref().unwrap().compiler_version, 2);
    assert_eq!(
        serde_json::to_value(record).unwrap()["context_policy"],
        "state_relevant_memory_v1"
    );
    assert_eq!(actual.revision(), source.revision() + 1);
    assert_eq!(receipt.request(), request);
    receipt
}
fn ordinary_wait(engine: &mut Engine, key: &str) -> Receipt {
    let request = engine.request(key, Intent::Actions(vec![Command::Wait { ticks: 1 }]));
    let proposal = Engine::proposal(&request).unwrap();
    let receipt = engine.preview(&request, &proposal).unwrap();
    engine.commit_prepared(&receipt).unwrap()
}

#[test]
fn actual_play25_record_consumes_stage_then_replays_and_commit_prepared_uses_zero_providers() {
    for mut engine in [fixture(), authored(&fixture(), "authored", "PRIVATE_B")] {
        let before = engine.clone();
        let request = request(&engine, "staged");
        let actual = generated(&engine, &request);
        let staged = engine
            .stage_play_v25(&request, actual.proposal(), &|| false)
            .unwrap();
        assert_eq!(staged.approved().events(), actual.events());
        let accepted = engine
            .commit_staged_play_v25(staged, actual.play().unwrap(), &|| false)
            .unwrap();
        assert_eq!(accepted, actual);
        let count = engine.canonical_record_count();
        assert_eq!(count, before.canonical_record_count() + 1);
        let expected_basis = engine.accepted_history_basis().unwrap();
        let mut no_provider = ScriptFakeProvider::default();
        let restored =
            Engine::replay_records(engine.seed().clone(), engine.canonical_records()).unwrap();
        assert_eq!(restored.canonical_records(), engine.canonical_records());
        assert_eq!(restored.accepted_history_basis().unwrap(), expected_basis);
        let strings: Vec<String> = engine
            .canonical_records()
            .iter()
            .map(|r| serde_json::to_string(r).unwrap())
            .collect();
        let restored = Engine::restore(engine.seed().clone(), &strings).unwrap();
        assert_eq!(restored.accepted_history_basis().unwrap(), expected_basis);
        let mut prepared_target = before;
        assert_eq!(prepared_target.commit_prepared(&actual).unwrap(), accepted);
        assert_eq!(
            prepared_target.accepted_history_basis().unwrap(),
            expected_basis
        );
        assert_eq!(
            play::execute(
                &mut prepared_target,
                &request,
                &mut no_provider,
                &Cancellation::default(),
                &profile()
            )
            .unwrap(),
            accepted
        );
        assert!(no_provider.seen.is_empty());
        assert_eq!(prepared_target.canonical_record_count(), count);
    }
}

#[test]
fn equal_scope_head_projection_and_approved_wait_cannot_substitute_different_author_truth_source() {
    let root = fixture();
    let b = authored(&root, "same-child", "PRIVATE_B");
    let mut c = authored(&root, "same-child", "PRIVATE_C");
    assert_eq!(b.scope(), c.scope());
    assert_eq!(b.revision(), c.revision());
    assert_eq!(b.state(), c.state());
    assert_eq!(b.canonical_bytes(), c.canonical_bytes());
    assert_ne!(
        b.effective_fact("relic-location").unwrap().proposition,
        c.effective_fact("relic-location").unwrap().proposition
    );
    assert_ne!(
        b.accepted_history_basis().unwrap(),
        c.accepted_history_basis().unwrap()
    );
    let request = request(&b, "same-request");
    let actual = generated(&b, &request);
    let staged = b
        .stage_play_v25(&request, actual.proposal(), &|| false)
        .unwrap();
    let local = c
        .stage_play_v25(&request, actual.proposal(), &|| false)
        .unwrap();
    assert_eq!(staged.approved(), local.approved());
    assert_eq!(
        serde_json::to_value(staged.narrator_evidence()).unwrap(),
        serde_json::to_value(local.narrator_evidence()).unwrap()
    );
    drop(local);
    let before = c.accepted_history_basis().unwrap();
    assert!(matches!(
        c.commit_staged_play_v25(staged, actual.play().unwrap(), &|| false),
        Err(Error::Stale)
    ));
    assert_eq!(c.accepted_history_basis().unwrap(), before);
    assert_eq!(c.canonical_record_count(), 1);
}

#[test]
fn same_head_valid_seed_replacement_refuses_source_token_without_append() {
    let original = fixture();
    let mut seed = original.seed().clone();
    seed.facts.get_mut("beacon-mark").unwrap().proposition =
        "Different valid private seed fact".into();
    let mut replacement = Engine::new(seed).unwrap();
    assert_eq!(original.scope(), replacement.scope());
    assert_eq!(original.revision(), replacement.revision());
    assert_eq!(original.canonical_bytes(), replacement.canonical_bytes());
    assert_ne!(
        original.accepted_history_basis().unwrap(),
        replacement.accepted_history_basis().unwrap()
    );
    let request = request(&original, "seed-guard");
    let actual = generated(&original, &request);
    let staged = original
        .stage_play_v25(&request, actual.proposal(), &|| false)
        .unwrap();
    let before = replacement.accepted_history_basis().unwrap();
    assert!(matches!(
        replacement.commit_staged_play_v25(staged, actual.play().unwrap(), &|| false),
        Err(Error::Stale)
    ));
    assert_eq!(replacement.accepted_history_basis().unwrap(), before);
    assert_eq!(replacement.revision(), 0);
}

#[test]
fn different_accepted_turn_after_stage_is_stale_and_preserves_that_progress() {
    let mut engine = authored(&fixture(), "authored", "PRIVATE_B");
    let request = request(&engine, "pending");
    let actual = generated(&engine, &request);
    let staged = engine
        .stage_play_v25(&request, actual.proposal(), &|| false)
        .unwrap();
    let intervening = ordinary_wait(&mut engine, "other-progress");
    let before = engine.accepted_history_basis().unwrap();
    assert!(matches!(
        engine.commit_staged_play_v25(staged, actual.play().unwrap(), &|| false),
        Err(Error::Stale)
    ));
    assert_eq!(engine.accepted_history_basis().unwrap(), before);
    assert_eq!(engine.receipts(), [intervening]);
}

#[test]
fn mismatched_new_record_never_installs_candidate_and_genuine_record_can_retry_fresh() {
    for variant in 0..2 {
        let mut engine = authored(&fixture(), "authored", "PRIVATE_B");
        let request = request(&engine, "record-guard");
        let actual = generated(&engine, &request);
        let staged = engine
            .stage_play_v25(&request, actual.proposal(), &|| false)
            .unwrap();
        let mut invalid = actual.play().unwrap().clone();
        if variant == 0 {
            invalid.narration.event_ids = vec![u64::MAX];
        } else {
            invalid.prompt_version = "locallore-play-v99".into();
        }
        let before = engine.accepted_history_basis().unwrap();
        assert!(engine
            .commit_staged_play_v25(staged, &invalid, &|| false)
            .is_err());
        assert_eq!(engine.accepted_history_basis().unwrap(), before);
        assert_eq!(engine.canonical_record_count(), 1);
        let fresh = engine
            .stage_play_v25(&request, actual.proposal(), &|| false)
            .unwrap();
        assert_eq!(
            engine
                .commit_staged_play_v25(fresh, actual.play().unwrap(), &|| false)
                .unwrap(),
            actual
        );
    }
}

#[test]
fn cancellation_panic_and_later_latched_cancel_do_not_install_consumed_candidate() {
    let mut engine = authored(&fixture(), "authored", "PRIVATE_B");
    let request = request(&engine, "cancelled");
    let actual = generated(&engine, &request);
    let before = engine.accepted_history_basis().unwrap();
    let staged = engine
        .stage_play_v25(&request, actual.proposal(), &|| false)
        .unwrap();
    assert!(matches!(
        engine.commit_staged_play_v25(staged, actual.play().unwrap(), &|| true),
        Err(Error::Cancelled)
    ));
    let staged = engine
        .stage_play_v25(&request, actual.proposal(), &|| false)
        .unwrap();
    assert!(matches!(
        engine.commit_staged_play_v25(staged, actual.play().unwrap(), &|| panic!(
            "synthetic staged commit cancel"
        )),
        Err(Error::Cancelled)
    ));
    let staged = engine
        .stage_play_v25(&request, actual.proposal(), &|| false)
        .unwrap();
    let checks = Cell::new(0_u32);
    assert!(matches!(
        engine.commit_staged_play_v25(staged, actual.play().unwrap(), &|| {
            let next = checks.get() + 1;
            checks.set(next);
            next >= 2
        }),
        Err(Error::Cancelled)
    ));
    assert!(checks.get() >= 2);
    assert_eq!(engine.accepted_history_basis().unwrap(), before);
    let fresh = engine
        .stage_play_v25(&request, actual.proposal(), &|| false)
        .unwrap();
    assert_eq!(
        engine
            .commit_staged_play_v25(fresh, actual.play().unwrap(), &|| false)
            .unwrap(),
        actual
    );
}

#[test]
fn exact_recorded_retry_precedes_cancel_stale_token_and_changed_profile_without_provider_calls() {
    let mut engine = authored(&fixture(), "authored", "PRIVATE_B");
    let request = request(&engine, "winning");
    let actual = generated(&engine, &request);
    let first = engine
        .stage_play_v25(&request, actual.proposal(), &|| false)
        .unwrap();
    let retry = engine
        .stage_play_v25(&request, actual.proposal(), &|| false)
        .unwrap();
    let accepted = engine
        .commit_staged_play_v25(first, actual.play().unwrap(), &|| false)
        .unwrap();
    let basis = engine.accepted_history_basis().unwrap();
    let count = engine.canonical_record_count();
    assert_eq!(
        engine
            .commit_staged_play_v25(retry, actual.play().unwrap(), &|| true)
            .unwrap(),
        accepted
    );
    let mut provider = ScriptFakeProvider::default();
    let cancel = Cancellation::default();
    cancel.cancel();
    let mut changed_profile = profile();
    changed_profile.context_tokens = 0;
    assert_eq!(
        play::execute(
            &mut engine,
            &request,
            &mut provider,
            &cancel,
            &changed_profile
        )
        .unwrap(),
        accepted
    );
    assert!(provider.seen.is_empty());
    assert_eq!(engine.accepted_history_basis().unwrap(), basis);
    assert_eq!(engine.canonical_record_count(), count);
}

#[test]
fn same_key_different_recorded_request_wins_retry_mismatch_over_staged_append() {
    let mut engine = fixture();
    let request = request(&engine, "occupied");
    let actual = generated(&engine, &request);
    let staged = engine
        .stage_play_v25(&request, actual.proposal(), &|| false)
        .unwrap();
    let occupant = ordinary_wait(&mut engine, "occupied");
    assert_ne!(occupant.request(), &request);
    let before = engine.accepted_history_basis().unwrap();
    assert!(matches!(
        engine.commit_staged_play_v25(staged, actual.play().unwrap(), &|| false),
        Err(Error::RetryMismatch)
    ));
    assert_eq!(engine.accepted_history_basis().unwrap(), before);
    assert_eq!(engine.receipts(), [occupant]);
}
