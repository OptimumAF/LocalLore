// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent source-frozen provenance oracles. Initially UNCOMPILED/UNRUN.
//! Scripted providers exercise actual Play; no Receipt is forged/deserialized.
use locallore::{
    author_correction::*,
    contracts::*,
    engine::Engine,
    inference::*,
    memory_coverage::{CoverageRead, FallbackReason},
    play::{self, PlayConstructionInput, PlayCoverageMode, PlayMemoryFallback, PlayProfile},
};
use serde_json::json;
use std::{collections::VecDeque, task::Poll};

fn fixture() -> Engine {
    Engine::new(serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap())
        .unwrap()
}
fn authored(parent: &Engine) -> Engine {
    let input = AuthorCorrectionInputV1 {
        version: 1,
        parent: parent.scope().clone(),
        expected_parent_revision: parent.revision(),
        fork_revision: parent.revision(),
        child_branch: "provenance-child".into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(),
            expected_proposition: parent.effective_fact("relic-location").unwrap().proposition,
            replacement: "PRIVATE_PROVENANCE_B".into(),
        },
        reason: "PRIVATE_PROVENANCE_REASON".into(),
    };
    let plan = parent.prepare_author_correction(&input, &|| false).unwrap();
    parent
        .apply_author_correction(&plan, &|| false)
        .unwrap()
        .engine
}
fn ordinary_wait(engine: &mut Engine) {
    let request = engine.request("prior", Intent::Actions(vec![Command::Wait { ticks: 1 }]));
    let proposal = Engine::proposal(&request).unwrap();
    let receipt = engine.preview(&request, &proposal).unwrap();
    engine.commit_prepared(&receipt).unwrap();
}
fn profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-provenance-review".into(),
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
fn generated(source: &Engine, policy: play::PlayContextPolicy) -> (Receipt, Engine) {
    let request = source.request(
        "provenance-turn",
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: "I wait for one tide tick.".into(),
        },
    );
    let mut actual = source.clone();
    let mut provider = ScriptFakeProvider {
        // Real Director parsing/mechanics; malformed narrator uses real fallback.
        replies: [json!({"commands":[{"op":"wait","ticks":1}]}), json!({})]
            .into_iter()
            .map(|v| serde_json::to_vec(&v).unwrap())
            .collect(),
        seen: vec![],
    };
    let receipt = play::execute_traced_with_policy(
        &mut actual,
        &request,
        &mut provider,
        &Cancellation::default(),
        &profile(),
        None,
        PlayConstructionInput {
            coverage: &CoverageRead::RawFallback(FallbackReason::Missing),
            policy,
        },
    )
    .unwrap();
    let roles: Vec<_> = provider
        .seen
        .iter()
        .map(|request| match &request.input {
            Input::Structured { role, .. } => role.as_str(),
            _ => panic!("actual structured pipeline required"),
        })
        .collect();
    assert_eq!(roles, vec!["director", "narrator"]);
    let record = receipt.play().unwrap();
    assert_eq!(record.prompt_version, "locallore-play-v2.5");
    assert_eq!(record.context_policy, Some(policy));
    let context = record.context.as_ref().unwrap();
    assert_eq!((context.version, context.compiler_version), (2, 2));
    // Native source reason is independent of compiler refusal. Never overwrite it.
    assert_eq!(
        context.source_fallback_reason,
        Some(PlayMemoryFallback::Missing)
    );
    let coverage = &context.coverage;
    assert_eq!(coverage.mode, PlayCoverageMode::Raw);
    assert_eq!(
        coverage.set_fallback_reason,
        Some(PlayMemoryFallback::Unsupported)
    );
    assert_eq!(coverage.packets_used, 0);
    assert_eq!(coverage.packets_fell_back, 0);
    assert_eq!(coverage.timespan_fallback_packets, 0);
    assert_eq!(coverage.mandatory_fallback_packets, 0);
    assert_eq!(coverage.covered_through, 0);
    assert_eq!(coverage.raw_delta_after, 0);
    assert_eq!(coverage.cached_event_candidates, 0);
    // raw_event_candidates is an actual actor-filtered count, not required zero.
    let strings: Vec<_> = actual
        .canonical_records()
        .iter()
        .map(|r| serde_json::to_string(r).unwrap())
        .collect();
    let restored = Engine::restore(actual.seed().clone(), &strings).unwrap();
    assert_eq!(
        restored.accepted_history_basis().unwrap(),
        actual.accepted_history_basis().unwrap()
    );
    (receipt, actual)
}
fn rejects_impossible_tuples(source: &Engine, policy: play::PlayContextPolicy) {
    let (receipt, actual) = generated(source, policy);
    let genuine = receipt.play().unwrap();
    let mut wrong_reason = genuine.clone();
    wrong_reason
        .context
        .as_mut()
        .unwrap()
        .coverage
        .set_fallback_reason = Some(PlayMemoryFallback::Missing);
    let mut invented_rejection = genuine.clone();
    invented_rejection
        .context
        .as_mut()
        .unwrap()
        .coverage
        .packets_fell_back = 1;
    let mut invented_cache = genuine.clone();
    let context = invented_cache.context.as_mut().unwrap();
    // A plausible closed finite tuple passes the generic Verified checks. No
    // source-fallback claim remains, so that independent constraint cannot mask it.
    context.source_fallback_reason = None;
    context.coverage.mode = PlayCoverageMode::Verified;
    context.coverage.set_fallback_reason = None;
    context.coverage.packets_used = 1;
    context.coverage.cached_event_candidates = 1;
    for (label, altered) in [
        ("compiler reason", wrong_reason),
        ("rejected packets", invented_rejection),
        ("verified cache", invented_cache),
    ] {
        // Exercise strict persisted restore separately before fresh acceptance:
        // edit untrusted JSON only, never deserialize a forged accepted Receipt.
        let mut strings: Vec<_> = actual
            .canonical_records()
            .iter()
            .map(|r| serde_json::to_string(r).unwrap())
            .collect();
        let mut last: serde_json::Value = serde_json::from_str(strings.last().unwrap()).unwrap();
        let persisted_receipt = if last.get("record_version").is_some() {
            &mut last["receipt"]
        } else {
            &mut last
        };
        persisted_receipt["play"] = serde_json::to_value(&altered).unwrap();
        *strings.last_mut().unwrap() = serde_json::to_string(&last).unwrap();
        assert!(
            matches!(
                Engine::restore(actual.seed().clone(), &strings),
                Err(Error::CorruptHistory)
            ),
            "strict restore accepted impossible {label} provenance"
        );

        let mut target = source.clone();
        let basis = target.accepted_history_basis().unwrap();
        let count = target.canonical_record_count();
        let staged = target
            .stage_play_v25(receipt.request(), receipt.proposal(), &|| false)
            .unwrap();
        assert!(
            target
                .commit_staged_play_v25(staged, &altered, &|| false)
                .is_err(),
            "fresh consume accepted impossible {label} provenance"
        );
        assert_eq!(target.accepted_history_basis().unwrap(), basis);
        assert_eq!(target.canonical_record_count(), count);
        let staged = target
            .stage_play_v25(receipt.request(), receipt.proposal(), &|| false)
            .unwrap();
        assert_eq!(
            target
                .commit_staged_play_v25(staged, genuine, &|| false)
                .unwrap(),
            receipt
        );
        // Recorded exact retry never calls a provider, even if cancellation is set.
        let mut no_provider = ScriptFakeProvider::default();
        let cancel = Cancellation::default();
        cancel.cancel();
        assert_eq!(
            play::execute(
                &mut target,
                receipt.request(),
                &mut no_provider,
                &cancel,
                &profile()
            )
            .unwrap(),
            receipt
        );
        assert!(no_provider.seen.is_empty());
    }
}

#[test]
fn domain2_relevant_provenance_requires_actual_unsupported_tuple_on_consume_and_restore() {
    let mut parent = fixture();
    ordinary_wait(&mut parent);
    let source = authored(&parent);
    assert_eq!(source.domain_version(), 2);
    rejects_impossible_tuples(&source, play::PlayContextPolicy::StateRelevantMemoryV1);
}

#[test]
fn domain1_recent_provenance_requires_actual_unsupported_tuple_on_consume_and_restore() {
    let mut source = fixture();
    ordinary_wait(&mut source);
    assert_eq!(source.domain_version(), 1);
    rejects_impossible_tuples(&source, play::PlayContextPolicy::StateRecentTranscriptV1);
}
