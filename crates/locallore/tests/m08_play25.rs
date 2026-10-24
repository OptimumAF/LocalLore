//! Synthetic provider plumbing oracles; never an actual-model quality claim.
use locallore::{
    author_correction::*,
    context_compiler::ContextPolicy,
    contracts::*,
    engine::Engine,
    inference::*,
    memory_coverage::{CoverageRead, FallbackReason},
    play::{self, PlayProfile},
};
use serde_json::{json, Value};
use std::{collections::VecDeque, task::Poll};

fn seed() -> Seed {
    serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap()
}
fn profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-play25".into(),
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
struct Script {
    replies: VecDeque<Vec<u8>>,
    seen: Vec<GenerationRequest>,
    cancel_role: Option<&'static str>,
}
impl Script {
    fn values(values: Vec<Value>) -> Self {
        Self {
            replies: values
                .into_iter()
                .map(|v| serde_json::to_vec(&v).unwrap())
                .collect(),
            ..Self::default()
        }
    }
}
impl InferenceProvider for Script {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        cancel: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        self.seen.push(request.clone());
        if let Input::Structured { role, .. } = &request.input {
            if self.cancel_role == Some(role.as_str()) {
                cancel.cancel();
            }
        }
        Poll::Ready(self.replies.pop_front().ok_or(Error::Provider))
    }
}

const A: &str = "the tideglass was at the old quay";
const B: &str = "the tideglass rests near violet reeds";
const SECRET: &str = "PRIVATE_UNRELATED_PLAYER_KNOWLEDGE";
const REASON: &str = "PRIVATE_PLAY25_AUTHOR_REASON";
fn root() -> Engine {
    let mut seed = seed();
    let fact = seed.facts.get_mut("relic-location").unwrap();
    fact.proposition = A.into();
    fact.discoverable_at = Some("quay".into());
    fact.known_by.insert("mira".into());
    seed.facts.get_mut("ancestry").unwrap().proposition = SECRET.into();
    Engine::new(seed).unwrap()
}
fn authored(parent: &Engine, replacement: &str) -> Engine {
    let input = AuthorCorrectionInputV1 {
        version: 1,
        parent: parent.scope().clone(),
        expected_parent_revision: parent.revision(),
        fork_revision: parent.revision(),
        child_branch: "authored".into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(),
            expected_proposition: A.into(),
            replacement: replacement.into(),
        },
        reason: REASON.into(),
    };
    let plan = parent.prepare_author_correction(&input, &|| false).unwrap();
    parent
        .apply_author_correction(&plan, &|| false)
        .unwrap()
        .engine
}
fn request(engine: &Engine, key: &str, kind: PlayInputKind, text: &str) -> Request {
    engine.request(
        key,
        Intent::FreeText {
            kind,
            text: text.into(),
        },
    )
}
fn wait_provider(event: u64) -> Script {
    Script::values(vec![
        json!({"commands":[{"op":"wait","ticks":1}]}),
        json!({"text":"You pause as a tide tick passes.","event_ids":[event],"speaker":"narrator"}),
    ])
}
fn envelope(provider: &Script, index: usize) -> (&str, &str, &Value) {
    match &provider.seen[index].input {
        Input::Structured {
            role,
            prompt,
            schema,
        } => (role, prompt, schema),
        _ => panic!("current Play must use its actual structured role path"),
    }
}
fn assert_narrator_private(prompt: &str, excluded: &[&str]) {
    for hidden in [
        SECRET,
        REASON,
        "truth_source",
        "observed_overrides",
        "optional_records",
        "player_text",
    ]
    .into_iter()
    .chain(excluded.iter().copied())
    {
        assert!(
            !prompt.contains(hidden),
            "unexpected narrator fixture payload {hidden}"
        );
    }
}

#[test]
fn current_default_discovery_uses_actual_staged_value_and_never_optional_context_for_narrator() {
    let mut engine = authored(&root(), B);
    let r = request(
        &engine,
        "discover",
        PlayInputKind::Action,
        "I discover relic-location.",
    );
    let mut provider = Script::values(vec![
        json!({"commands":[{"op":"discover","fact":"relic-location"}]}),
        json!({"text":format!("You discover {B}."),"event_ids":[2],"speaker":"narrator"}),
    ]);
    let receipt = play::execute(
        &mut engine,
        &r,
        &mut provider,
        &Cancellation::default(),
        &profile(),
    )
    .unwrap();
    assert_eq!(provider.seen.len(), 2);
    assert_eq!(envelope(&provider, 0).0, "director");
    assert!(envelope(&provider, 0).1.contains(A));
    assert!(!envelope(&provider, 0).1.contains(B));
    let (_, narrator, _) = envelope(&provider, 1);
    assert!(narrator.contains(B));
    assert_narrator_private(narrator, &[A]);
    let record = receipt.play().unwrap();
    assert_eq!(record.prompt_version, "locallore-play-v2.5");
    assert_eq!(record.policy, "grounded-prose-v2.2");
    assert_eq!(
        record.context_policy,
        Some(ContextPolicy::StateRelevantMemoryV1)
    );
    assert_eq!(record.context.as_ref().unwrap().version, 2);
    assert_eq!(record.context.as_ref().unwrap().compiler_version, 2);
    assert!(!record.fallback);
    assert_eq!(
        engine
            .observed_facts("player", engine.scope(), engine.revision())
            .unwrap()["relic-location"]
            .proposition,
        B
    );
    assert_eq!(
        engine
            .observed_facts("mira", engine.scope(), engine.revision())
            .unwrap()["relic-location"]
            .proposition,
        A
    );
}

#[test]
fn both_real_current_policies_use_compiler2_but_optional_history_stays_director_only() {
    let mut basis = authored(&root(), B);
    for index in 0..12 {
        let r = basis.request(
            &format!("history-{index}"),
            Intent::Actions(vec![Command::Say {
                text: format!("PUBLIC_OLD_HISTORY_{index}"),
                audience: ["mira".into()].into(),
            }]),
        );
        let p = Engine::proposal(&r).unwrap();
        let v = basis.preview(&r, &p).unwrap();
        basis.commit_prepared(&v).unwrap();
    }
    let before = basis.canonical_bytes();
    for policy in [
        ContextPolicy::StateRecentTranscriptV1,
        ContextPolicy::StateRelevantMemoryV1,
    ] {
        let mut engine = basis.clone();
        let r = request(
            &engine,
            "current-wait",
            PlayInputKind::Action,
            "I wait for one tide tick.",
        );
        let mut provider = wait_provider(14);
        let receipt = play::execute_traced_with_policy(
            &mut engine,
            &r,
            &mut provider,
            &Cancellation::default(),
            &profile(),
            None,
            play::PlayConstructionInput {
                coverage: &CoverageRead::RawFallback(FallbackReason::Missing),
                policy,
            },
        )
        .unwrap();
        let director = envelope(&provider, 0).1;
        assert!(director.contains("\"compiler_version\":2"));
        assert_eq!(
            director.contains("transcript_unit"),
            policy == ContextPolicy::StateRecentTranscriptV1
        );
        assert_narrator_private(envelope(&provider, 1).1, &[A, B, "PUBLIC_OLD_HISTORY"]);
        assert_eq!(receipt.play().unwrap().context_policy, Some(policy));
        assert_eq!(
            receipt
                .play()
                .unwrap()
                .context
                .as_ref()
                .unwrap()
                .compiler_version,
            2
        );
    }
    assert_eq!(basis.canonical_bytes(), before);
}

#[test]
fn wait_and_dialogue_never_attach_old_knowledge_raw_speech_or_audience_to_narrator() {
    for dialogue in [false, true] {
        let mut engine = authored(&root(), B);
        let (kind, text) = if dialogue {
            (
                PlayInputKind::Dialogue,
                "RAW_LITERAL_PLAYER_WORDS are only speech.",
            )
        } else {
            (PlayInputKind::Action, "I wait for one tide tick.")
        };
        let r = request(&engine, "turn", kind, text);
        let command = if dialogue {
            json!({"op":"say","text":text,"audience":["mira"]})
        } else {
            json!({"op":"wait","ticks":1})
        };
        let prose = if dialogue {
            "Your words are heard by the chosen listeners."
        } else {
            "You pause as a tide tick passes."
        };
        let mut provider = Script::values(vec![
            json!({"commands":[command]}),
            json!({"text":prose,"event_ids":[2],"speaker":"narrator"}),
        ]);
        let receipt = play::execute(
            &mut engine,
            &r,
            &mut provider,
            &Cancellation::default(),
            &profile(),
        )
        .unwrap();
        assert_narrator_private(
            envelope(&provider, 1).1,
            &[A, B, "RAW_LITERAL_PLAYER_WORDS", "mira", "audience"],
        );
        assert!(!receipt.play().unwrap().fallback);
    }
}

#[test]
fn closed_native_source_reasons_remain_separate_from_actual_domain2_compiler_unsupported() {
    for reason in [
        FallbackReason::Missing,
        FallbackReason::Budget,
        FallbackReason::Malformed,
        FallbackReason::Unsupported,
        FallbackReason::Binding,
        FallbackReason::Gap,
        FallbackReason::Overlap,
        FallbackReason::OpenTailBeforeEnd,
        FallbackReason::UnprovableClosure,
        FallbackReason::SourceMismatch,
    ] {
        let mut engine = authored(&root(), B);
        let r = request(
            &engine,
            "wait",
            PlayInputKind::Action,
            "I wait for one tide tick.",
        );
        let mut provider = wait_provider(2);
        let receipt = play::execute_traced_with_coverage(
            &mut engine,
            &r,
            &mut provider,
            &Cancellation::default(),
            &profile(),
            None,
            &CoverageRead::RawFallback(reason),
        )
        .unwrap();
        let context = receipt.play().unwrap().context.as_ref().unwrap();
        assert_eq!(context.source_fallback_reason, Some(reason.into()));
        assert_eq!(context.coverage.mode, play::PlayCoverageMode::Raw);
        assert_eq!(
            context.coverage.set_fallback_reason,
            Some(play::PlayMemoryFallback::Unsupported)
        );
        assert_eq!(context.coverage.cached_event_candidates, 0);
        assert_eq!(provider.seen.len(), 2);
    }
}

#[test]
fn exact_recorded_retry_uses_no_roles_even_after_current_policy_profile_and_cancel_change() {
    let mut engine = authored(&root(), B);
    let r = request(
        &engine,
        "wait",
        PlayInputKind::Action,
        "I wait for one tide tick.",
    );
    let mut provider = wait_provider(2);
    let receipt = play::execute(
        &mut engine,
        &r,
        &mut provider,
        &Cancellation::default(),
        &profile(),
    )
    .unwrap();
    let before = engine.canonical_bytes();
    let mut invalid = profile();
    invalid.context_tokens = 0;
    let cancel = Cancellation::default();
    cancel.cancel();
    let mut no_roles = Script::default();
    assert_eq!(
        play::execute_traced_with_policy(
            &mut engine,
            &r,
            &mut no_roles,
            &cancel,
            &invalid,
            None,
            play::PlayConstructionInput {
                coverage: &CoverageRead::RawFallback(FallbackReason::Malformed),
                policy: ContextPolicy::StateRecentTranscriptV1
            }
        )
        .unwrap(),
        receipt
    );
    assert!(no_roles.seen.is_empty());
    assert_eq!(engine.canonical_bytes(), before);
}

#[test]
fn current_record_replays_exactly_and_rejects_version_policy_and_context_tuple_tampering() {
    let parent = root();
    let mut engine = authored(&parent, B);
    let r = request(
        &engine,
        "wait",
        PlayInputKind::Action,
        "I wait for one tide tick.",
    );
    let mut provider = wait_provider(2);
    play::execute(
        &mut engine,
        &r,
        &mut provider,
        &Cancellation::default(),
        &profile(),
    )
    .unwrap();
    let base = parent.fork("authored", 0).unwrap();
    let history: Vec<String> = engine
        .canonical_records()
        .iter()
        .map(|r| serde_json::to_string(r).unwrap())
        .collect();
    let restored = base.restore_continuation(&history).unwrap();
    assert_eq!(restored.canonical_bytes(), engine.canonical_bytes());
    assert_eq!(restored.canonical_records(), engine.canonical_records());
    for (field, value) in [
        ("prompt_version", json!("locallore-play-v2.4")),
        ("policy", json!("grounded-prose-v2.1")),
        ("context_policy", Value::Null),
        ("context_policy", json!("state_invented_v1")),
    ] {
        let mut bad = history.clone();
        let mut value_record: Value = serde_json::from_str(&bad[1]).unwrap();
        value_record["receipt"]["play"][field] = value;
        bad[1] = value_record.to_string();
        assert!(base.restore_continuation(&bad).is_err());
    }
    for field in ["version", "compiler_version"] {
        let mut bad = history.clone();
        let mut value: Value = serde_json::from_str(&bad[1]).unwrap();
        value["receipt"]["play"]["context"][field] = json!(1);
        bad[1] = value.to_string();
        assert!(base.restore_continuation(&bad).is_err());
    }
}

#[test]
fn invalid_intent_wrong_actual_proposal_cancel_and_mandatory_budget_do_not_change_canon() {
    let basis = authored(&root(), B);
    let before = basis.canonical_bytes();
    let mut engine = basis.clone();
    let r = request(
        &engine,
        "unsupported",
        PlayInputKind::Action,
        "I juggle clouds.",
    );
    let mut provider = Script::default();
    assert_eq!(
        play::execute(
            &mut engine,
            &r,
            &mut provider,
            &Cancellation::default(),
            &profile()
        ),
        Err(Error::ClarificationRequired)
    );
    assert!(provider.seen.is_empty());
    assert_eq!(engine.canonical_bytes(), before);
    let r = request(
        &engine,
        "wrong",
        PlayInputKind::Action,
        "I wait for one tide tick.",
    );
    let mut wrong = Script::values(vec![json!({"commands":[{"op":"wait","ticks":2}]})]);
    assert_eq!(
        play::execute(
            &mut engine,
            &r,
            &mut wrong,
            &Cancellation::default(),
            &profile()
        ),
        Err(Error::Agency)
    );
    assert_eq!(wrong.seen.len(), 1);
    assert_eq!(engine.canonical_bytes(), before);
    let mut cancelled = wait_provider(2);
    cancelled.cancel_role = Some("narrator");
    assert_eq!(
        play::execute(
            &mut engine,
            &r,
            &mut cancelled,
            &Cancellation::default(),
            &profile()
        ),
        Err(Error::Cancelled)
    );
    assert_eq!(engine.canonical_bytes(), before);
    let mut tiny = profile();
    tiny.context_tokens = 512;
    let mut no_roles = Script::default();
    assert_eq!(
        play::execute(
            &mut engine,
            &r,
            &mut no_roles,
            &Cancellation::default(),
            &tiny
        ),
        Err(Error::TooLarge)
    );
    assert!(no_roles.seen.is_empty());
    assert_eq!(engine.canonical_bytes(), before);
}

#[test]
fn discovered_value_does_not_expand_hidden_actor_allowlist_and_fallback_is_mechanical() {
    let mut engine = authored(&root(), "Sable carries the token");
    let r = request(
        &engine,
        "discover",
        PlayInputKind::Action,
        "I discover relic-location.",
    );
    let mut provider = Script::values(vec![
        json!({"commands":[{"op":"discover","fact":"relic-location"}]}),
        json!({"text":"You discover Sable carries the token.","event_ids":[2],"speaker":"narrator"}),
    ]);
    let receipt = play::execute(
        &mut engine,
        &r,
        &mut provider,
        &Cancellation::default(),
        &profile(),
    )
    .unwrap();
    assert!(envelope(&provider, 1).1.contains("Sable carries the token"));
    assert!(receipt.play().unwrap().fallback);
    assert_eq!(
        receipt.narration(),
        locallore::engine::render(receipt.events())
    );
    assert!(!receipt.narration().contains("Sable"));
}

#[test]
fn guarded_phrase_is_supported_only_by_actual_this_turn_observation_not_private_world_truth() {
    // "golden" is an existing guarded phrase. This pair requires the new safe
    // evidence seam to matter, while keeping the same private truth in both runs.
    for discover in [false, true] {
        let mut engine = authored(&root(), "a golden mark lies beside the quay");
        let items = engine.state().items.clone();
        let r = request(
            &engine,
            "paired-grounding",
            PlayInputKind::Action,
            if discover {
                "I discover relic-location."
            } else {
                "I wait for one tide tick."
            },
        );
        let command = if discover {
            json!({"op":"discover","fact":"relic-location"})
        } else {
            json!({"op":"wait","ticks":1})
        };
        let mut provider = Script::values(vec![
            json!({"commands":[command]}),
            json!({"text":"You notice a golden mark beside the quay.","event_ids":[2],"speaker":"narrator"}),
        ]);
        let receipt = play::execute(
            &mut engine,
            &r,
            &mut provider,
            &Cancellation::default(),
            &profile(),
        )
        .unwrap();
        assert_eq!(envelope(&provider, 1).1.contains("golden"), discover);
        assert_eq!(receipt.play().unwrap().fallback, !discover);
        assert_eq!(engine.state().items, items);
        if !discover {
            assert_eq!(
                receipt.narration(),
                locallore::engine::render(receipt.events())
            );
        }
    }
}

#[test]
fn actual_original_21_through_24_history_bytes_and_zero_role_retry_survive_current_dispatch() {
    use sha2::{Digest, Sha256};
    for text in [
        include_str!("fixtures/accepted_play_v2_1.json"),
        include_str!("fixtures/accepted_play_v2_2.json"),
        include_str!("fixtures/accepted_play_v2_3.json"),
        include_str!("fixtures/accepted_play_v2_4.json"),
    ] {
        let fixture: Value = serde_json::from_str(text).unwrap();
        let seed: Seed = serde_json::from_value(fixture["seed"].clone()).unwrap();
        let mut restored =
            Engine::restore(seed.clone(), &[fixture["receipt"].to_string()]).unwrap();
        let receipt = restored.receipts()[0].clone();
        assert_eq!(serde_json::to_value(&receipt).unwrap(), fixture["receipt"]);
        assert!(receipt.play().unwrap().context_policy.is_none());
        assert!(!serde_json::to_value(&receipt).unwrap()["play"]
            .as_object()
            .unwrap()
            .contains_key("context_policy"));
        if receipt.play().unwrap().prompt_version == "locallore-play-v2.4" {
            let compact = serde_json::to_vec(&receipt).unwrap();
            assert_eq!(
                compact.as_slice(),
                include_bytes!("fixtures/accepted_play_v2_4_receipt.json")
            );
            assert_eq!(compact.len(), 2150);
            assert_eq!(
                format!("{:x}", Sha256::digest(&compact)),
                "38dcf7329addf4ed98fd984cdb9eac95f8d078be03bf4633dd7082d23ac4bc3f"
            );
            let record_bytes = serde_json::to_vec(receipt.play().unwrap()).unwrap();
            assert_eq!(record_bytes.len(), 1352);
            assert_eq!(
                format!("{:x}", Sha256::digest(&record_bytes)),
                "6ed4abcd325e14fa334d23ead9b843ebe93afd91e26b28e3167ad95e552b9341"
            );
            assert_eq!(
                receipt
                    .play()
                    .unwrap()
                    .context
                    .as_ref()
                    .unwrap()
                    .compiler_version,
                1
            );
            assert_eq!(receipt.play().unwrap().context.as_ref().unwrap().version, 1);
        }
        let before = restored.canonical_bytes();
        let mut no_roles = Script::default();
        let mut invalid_profile = profile();
        invalid_profile.context_tokens = 0;
        let cancel = Cancellation::default();
        cancel.cancel();
        assert_eq!(
            play::execute(
                &mut restored,
                receipt.request(),
                &mut no_roles,
                &cancel,
                &invalid_profile
            )
            .unwrap(),
            receipt
        );
        assert!(no_roles.seen.is_empty());
        assert_eq!(restored.canonical_bytes(), before);
        let mut bad = fixture["receipt"].clone();
        bad["play"]["context_policy"] = json!("state_relevant_memory_v1");
        assert!(Engine::restore(seed, &[bad.to_string()]).is_err());
    }
}
