// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! First SOURCE-FROZEN Core recipe oracles, UNCOMPILED/UNRUN at author handoff.
//! Actual Engine/Play + deterministic recording provider only. Missing new APIs
//! are compilation prerequisites, not behavioral RED or model/quality evidence.
use locallore::{
    author_correction::*,
    contracts::*,
    engine::{staged_scene_play::BoundScenePlayV1, Engine},
    inference::*,
    memory_coverage::{CoverageRead, FallbackReason},
    play::{
        self,
        scene_narration::{
            render_scene_narrator_v1, ScenePlayConstructionInput, SceneRecipeV1,
            LITERAL_SCENE_PROMPT_VERSION_V1, SCENE_NARRATION_POLICY_V1, SCENE_PROMPT_VERSION_V1,
        },
        PlayContextPolicy, PlayProfile,
    },
    story_authoring::*,
    story_presentation::{StoryPresentationV1, StoryTone},
};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{collections::VecDeque, task::Poll};

const A: &str = "SYNTHETIC_OBSERVED_SCENE_A";
const B: &str = "SYNTHETIC_PRIVATE_TRUTH_B";
const REASON: &str = "SYNTHETIC_PRIVATE_AUTHOR_REASON";
const PROSE: &str = "You pause beside the quay.";

fn memory() -> SceneRecipeV1 {
    SceneRecipeV1::Memory(PlayContextPolicy::StateRelevantMemoryV1)
}
fn fixture(tone: Option<StoryTone>, phrases: &[&str]) -> Engine {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    let fact = seed.facts.get_mut("relic-location").unwrap();
    fact.proposition = A.into();
    fact.discoverable_at = Some("quay".into());
    fact.known_by.insert("mira".into());
    seed.facts.insert("mira-private".into(), Fact {
        proposition: "SYNTHETIC_MIRA_ONLY_PAYLOAD".into(),
        discoverable_at: None,
        known_by: ["mira".into()].into(),
    });
    seed.presentation = tone.map(|tone| StoryPresentationV1 {
        version: 1, tone, excluded_phrases: phrases.iter().map(|p| (*p).into()).collect(),
    });
    Engine::new(seed).unwrap()
}
fn profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-scene-recipe".into(), model_sha256: "a".repeat(64),
        runtime_revision: "b".repeat(40), template_sha256: "c".repeat(64),
        worker_sha256: "d".repeat(64), profile_manifest_sha256: "e".repeat(64),
        context_tokens: 4096, director_tokens: 350, narrator_tokens: 350,
        deadline_ms: 5000, repair_limit: 1,
    }
}
fn make_request(engine: &Engine, key: &str, text: &str) -> Request {
    engine.request(key, Intent::FreeText { kind: PlayInputKind::Action, text: text.into() })
}
#[derive(Default)]
struct Script {
    replies: VecDeque<Vec<u8>>,
    seen: Vec<GenerationRequest>,
    cancel_narrator: bool,
}
impl Script {
    fn new(command: Command, text: &str, end: u64) -> Self {
        Self {
            replies: [
                json!({"commands":[command]}),
                json!({"text":text,"event_ids":[end],"speaker":"narrator"}),
            ].into_iter().map(|v| serde_json::to_vec(&v).unwrap()).collect(),
            ..Self::default()
        }
    }
}
impl InferenceProvider for Script {
    fn poll(&mut self, request: &GenerationRequest, cancel: &Cancellation)
        -> Poll<Result<Vec<u8>, Error>> {
        self.seen.push(request.clone());
        if self.cancel_narrator && matches!(&request.input, Input::Structured { role, .. } if role == "narrator") {
            cancel.cancel();
        }
        Poll::Ready(self.replies.pop_front().ok_or(Error::Provider))
    }
}
fn role(script: &Script, index: usize) -> (&str, &str, &Value) {
    match &script.seen[index].input {
        Input::Structured { role, prompt, schema } => (role, prompt, schema),
        _ => panic!("actual structured request required"),
    }
}
fn execute(engine: &mut Engine, request: &Request, script: &mut Script, recipe: SceneRecipeV1)
    -> Result<Receipt, Error> {
    let coverage = CoverageRead::RawFallback(FallbackReason::Missing);
    play::execute_traced_with_scene_recipe_v1(
        engine, request, script, &Cancellation::default(), &profile(), None,
        ScenePlayConstructionInput {
            recipe,
            coverage: if matches!(recipe, SceneRecipeV1::Memory(_)) { Some(&coverage) } else { None },
        },
    )
}
fn generated(source: &Engine, recipe: SceneRecipeV1) -> (Engine, Receipt, Script) {
    let mut engine = source.clone();
    let request = make_request(source, "scene-wait", "I wait for one tide tick.");
    let mut script = Script::new(Command::Wait { ticks: 1 }, PROSE, source.revision() + 1);
    let receipt = execute(&mut engine, &request, &mut script, recipe).unwrap();
    assert_eq!(script.seen.len(), 2);
    assert!(!receipt.play().unwrap().fallback);
    (engine, receipt, script)
}
fn bound(source: &Engine, receipt: &Receipt, recipe: SceneRecipeV1) -> BoundScenePlayV1 {
    let stage = source.stage_scene_play_v1(receipt.request(), receipt.proposal(), &|| false).unwrap();
    source.bind_scene_play_v1(stage, recipe, &|| false).unwrap()
}
fn unchanged(engine: &Engine, original: &Engine) {
    assert_eq!(engine.seed(), original.seed());
    assert_eq!(engine.canonical_records(), original.canonical_records());
    assert_eq!(engine.canonical_bytes(), original.canonical_bytes());
    assert_eq!(engine.accepted_history_basis().unwrap(), original.accepted_history_basis().unwrap());
}
fn corrected(source: &Engine, replacement: &str) -> Engine {
    let input = AuthorCorrectionInputV1 {
        version: 1, parent: source.scope().clone(), expected_parent_revision: source.revision(),
        fork_revision: source.revision(), child_branch: "same-scene-child".into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(), expected_proposition: A.into(), replacement: replacement.into(),
        },
        reason: REASON.into(),
    };
    let plan = source.prepare_author_correction(&input, &|| false).unwrap();
    source.apply_author_correction(&plan, &|| false).unwrap().engine
}
fn authored_world() -> Engine {
    // Actual dependency materializer and origin validation, not a forged Seed marker.
    let input = InitialStoryInputV1 {
        version: 1, premise: "A surveyor reaches a quiet orchard.".into(),
        player_name: "Rae".into(), player_description: "A careful surveyor.".into(),
        cast: vec![InitialCastHintV1 { name: "Finch".into(), description: "An orchard keeper.".into() }],
        profile: InitialRuleProfileV1::NarrativeV1,
        presentation: StoryPresentationV1::default(),
    };
    let proposal = InitialWorldProposalV1 {
        version: 1,
        locations: vec![InitialLocationV1 { name: "Orchard".into(), description: "Copper markers hang beneath the trees.".into() }],
        player_location: 0,
        characters: vec![InitialCharacterV1 {
            name: "Finch".into(), description: "A keeper waits by the gate.".into(), location: 0, known_by: vec![1],
        }],
        routes: vec![], facts: vec![], beliefs: vec![], possessions: vec![],
    };
    let response = serde_json::to_string(&proposal).unwrap();
    let origin = InitialWorldOriginV1 {
        version: 1,
        generation: InitialGenerationV1 {
            input: input.clone(), proposal: proposal.clone(), model_profile: profile().id.clone(),
            model_configuration: InitialModelConfigurationV1::from(&profile()),
            provider: InitialProviderKindV1::Scripted,
            prompt_version: locallore::story_authoring::PROMPT_VERSION.into(),
            schema_version: locallore::story_authoring::SCHEMA_VERSION.into(),
            response_sha256: format!("{:x}", Sha256::digest(response.as_bytes())), response,
        },
        reviewed: input, accepted: proposal, title: "The Orchard Survey".into(),
    };
    let seed = materialize(&origin, Scope { story: "authored-scene-fixture".into(), branch: "main".into() }).unwrap();
    assert_eq!(validate_origin(&seed), Ok(()));
    assert!(seed.initial_world.is_some());
    Engine::new(seed).unwrap()
}

#[test]
fn existing_preparation_and_typed_authored_fixture_calibrate_without_scene_recipe() {
    let source = fixture(None, &[]);
    let request = make_request(&source, "calibration", "I wait for one tide tick.");
    let proposal = Proposal {
        version: VERSION, scope: request.scope.clone(), turn: request.turn.clone(),
        expected_revision: request.expected_revision, commands: vec![Command::Wait { ticks: 1 }],
    };
    let stage = source.stage_scene_play_v1(&request, &proposal, &|| false).unwrap();
    assert_eq!(stage.scene_frame().location(), "quay");
    assert_eq!(stage.scene_frame().after_revision(), 1);
    assert_eq!(source.revision(), 0);
    assert_eq!(authored_world().revision(), 0);
}

#[test]
fn actual_provider_receives_exact_shared_renderer_frame_evidence_schema_and_presentation() {
    assert_eq!(SCENE_PROMPT_VERSION_V1, "locallore-play-v2.9-scene-frame-v1");
    assert_eq!(LITERAL_SCENE_PROMPT_VERSION_V1, "locallore-play-v2.10-literal-director-v1-scene-frame-v1");
    assert_eq!(SCENE_NARRATION_POLICY_V1, "grounded-prose-v2.4-scene-frame-v1");
    for recipe in [memory(), SceneRecipeV1::LiteralV1] {
        for tone in [None, Some(StoryTone::Warm), Some(StoryTone::Brisk)] {
            let source = fixture(tone, if tone.is_some() { &["EXCLUDED_SYNTHETIC_PHRASE"] } else { &[] });
            let before = source.clone();
            let (after, receipt, script) = generated(&source, recipe);
            let capability = bound(&source, &receipt, recipe);
            assert_eq!(capability.recipe(), recipe);
            let rendered = render_scene_narrator_v1(&capability, &profile(), &|| false).unwrap();
            let (actual_role, actual_prompt, actual_schema) = role(&script, 1);
            assert_eq!(actual_role, "narrator");
            assert_eq!(actual_prompt, rendered.prompt());
            assert_eq!(actual_schema, rendered.schema());
            assert_eq!(script.seen[1].schema, "locallore-narrator-v2");
            assert_eq!(actual_schema, &play::narration_schema(receipt.events()));
            assert!(actual_prompt.contains(&serde_json::to_string(capability.scene_frame()).unwrap()));
            assert!(actual_prompt.contains(&serde_json::to_string(capability.narrator_evidence()).unwrap()));
            for hidden in [A, "SYNTHETIC_MIRA_ONLY_PAYLOAD", "SECRET-TIDE-731", "Context data: "] {
                assert!(!actual_prompt.contains(hidden), "narrator received unrelated source material {hidden}");
            }
            let record = receipt.play().unwrap();
            assert_eq!(record.policy, SCENE_NARRATION_POLICY_V1);
            assert_eq!(record.prompt_version, if matches!(recipe, SceneRecipeV1::LiteralV1) {
                LITERAL_SCENE_PROMPT_VERSION_V1
            } else { SCENE_PROMPT_VERSION_V1 });
            if let SceneRecipeV1::Memory(policy) = recipe {
                assert_eq!(record.context_policy, Some(policy));
                assert!(record.context.is_some());
            } else { assert!(record.context.is_none() && record.context_policy.is_none()); }
            let scene = record.scene.as_ref().unwrap();
            assert_eq!(scene.version, 1);
            assert_eq!(scene.frame_sha256, format!("{:x}", Sha256::digest(serde_json::to_vec(capability.scene_frame()).unwrap())));
            assert_eq!(record.story_presentation.is_some(), tone.is_some());
            if let Some(tone) = tone {
                assert!(actual_prompt.contains(if tone == StoryTone::Warm { "Use a warm, considerate tone" } else { "Use a brisk, concise tone" }));
                assert!(actual_prompt.contains("EXCLUDED_SYNTHETIC_PHRASE"));
                assert!(!role(&script, 0).1.contains("EXCLUDED_SYNTHETIC_PHRASE"));
                assert_eq!(record.story_presentation.as_ref().unwrap().presentation_sha256,
                    format!("{:x}", Sha256::digest(serde_json::to_vec(source.seed().presentation.as_ref().unwrap()).unwrap())));
            }
            assert_eq!(after.revision(), 1);
            unchanged(&source, &before);
        }
    }
}

#[test]
fn move_frame_uses_postcandidate_destination_and_nonmovement_keeps_actual_self_location() {
    for (text, command, prose, location) in [
        ("I move to pier.", Command::Move { to: "pier".into() }, "You walk onto pier.", "pier"),
        ("I give potion to mira.", Command::Give { item: "potion".into(), to: "mira".into(), quantity: 1 }, "You hand the potion to Mira.", "quay"),
        ("I use steady.", Command::UseAbility { ability: "steady".into() }, "You use steady.", "quay"),
    ] {
        let source = fixture(None, &[]);
        let mut after = source.clone();
        let request = make_request(&source, "effect", text);
        let mut script = Script::new(command, prose, 1);
        let receipt = execute(&mut after, &request, &mut script, memory()).unwrap();
        assert!(!receipt.play().unwrap().fallback);
        let capability = bound(&source, &receipt, memory());
        assert_eq!(capability.scene_frame().location(), location);
        assert_eq!(capability.scene_frame().location(), after.character_context_v2("player", after.scope(), after.revision()).unwrap().self_state.location);
        let rendered = render_scene_narrator_v1(&capability, &profile(), &|| false).unwrap();
        assert_eq!(role(&script, 1).1, rendered.prompt());
        assert_eq!(source.revision(), 0);
    }
}

#[test]
fn corrected_memory_preserves_observed_a_and_raw_fallback_while_literal_refuses_before_calls() {
    let source = corrected(&fixture(None, &[]), B);
    let before = source.clone();
    assert_eq!(source.character_context_v2("player", source.scope(), source.revision()).unwrap().facts["relic-location"].proposition, A);
    let (after, receipt, script) = generated(&source, memory());
    assert_eq!(after.character_context_v2("player", after.scope(), after.revision()).unwrap().facts["relic-location"].proposition, A);
    assert_eq!(after.effective_fact("relic-location").unwrap().proposition, B);
    for hidden in [A, B, REASON] { assert!(!role(&script, 1).1.contains(hidden)); }
    let context = receipt.play().unwrap().context.as_ref().unwrap();
    assert_eq!(context.coverage.mode, play::PlayCoverageMode::Raw);
    assert_eq!(context.coverage.set_fallback_reason, Some(play::PlayMemoryFallback::Unsupported));
    let request = make_request(&source, "literal-refused", "I wait for one tide tick.");
    let mut target = source.clone();
    let mut no_calls = Script::default();
    assert_eq!(execute(&mut target, &request, &mut no_calls, SceneRecipeV1::LiteralV1), Err(Error::Version));
    assert!(no_calls.seen.is_empty());
    let prep = source.stage_scene_play_v1(receipt.request(), receipt.proposal(), &|| false).unwrap();
    assert!(matches!(source.bind_scene_play_v1(prep, SceneRecipeV1::LiteralV1, &|| false), Err(Error::Version)));
    unchanged(&target, &before);
    unchanged(&source, &before);
}

#[test]
fn scene_provenance_event_ids_and_actual_cross_recipe_records_are_not_commit_authority() {
    for recipe in [memory(), SceneRecipeV1::LiteralV1] {
        let source = fixture(None, &[]);
        let (_, receipt, _) = generated(&source, recipe);
        for fault in 0..6 {
            let mut target = source.clone();
            let capability = bound(&source, &receipt, recipe);
            let mut record = receipt.play().unwrap().clone();
            match fault {
                0 => record.scene = None,
                1 => record.scene.as_mut().unwrap().version = 2,
                2 => record.scene.as_mut().unwrap().frame_sha256 = "0".repeat(64),
                3 => record.narration.event_ids = vec![999],
                4 => record.policy = play::NARRATION_POLICY.into(),
                _ => record.prompt_version = play::PROMPT_VERSION.into(),
            }
            assert!(target.commit_scene_play_v1(capability, &record, &|| false).is_err());
            unchanged(&target, &source);
        }
        let other = if matches!(recipe, SceneRecipeV1::LiteralV1) { memory() } else { SceneRecipeV1::LiteralV1 };
        let mut target = source.clone();
        let wrong_capability = bound(&source, &receipt, other);
        assert!(target.commit_scene_play_v1(wrong_capability, receipt.play().unwrap(), &|| false).is_err());
        unchanged(&target, &source);
        let mut json = serde_json::to_value(receipt.play().unwrap()).unwrap();
        json["scene"]["extra_authority"] = json!(true);
        assert!(serde_json::from_value::<play::PlayRecord>(json).is_err());
        let mut relabeled = receipt.play().unwrap().clone();
        relabeled.prompt_version = play::PROMPT_VERSION.into();
        relabeled.policy = play::NARRATION_POLICY.into();
        let mut target = source.clone();
        assert!(target.commit_play(receipt.request(), receipt.proposal(), &relabeled).is_err());
        unchanged(&target, &source);
    }
}

#[test]
fn complete_basis_binds_same_head_private_history_and_exact_typed_presentation() {
    let parent = fixture(None, &[]);
    let source = corrected(&parent, B);
    let mut other = corrected(&parent, "SYNTHETIC_PRIVATE_TRUTH_C");
    assert_eq!(source.scope(), other.scope());
    assert_eq!(source.revision(), other.revision());
    assert_eq!(source.canonical_bytes(), other.canonical_bytes());
    assert_ne!(source.accepted_history_basis().unwrap(), other.accepted_history_basis().unwrap());
    let (_, receipt, _) = generated(&source, memory());
    let before = other.clone();
    assert!(matches!(other.commit_scene_play_v1(bound(&source, &receipt, memory()), receipt.play().unwrap(), &|| false), Err(Error::Stale)));
    unchanged(&other, &before);
    let staged = source.stage_scene_play_v1(receipt.request(), receipt.proposal(), &|| false).unwrap();
    assert!(matches!(other.bind_scene_play_v1(staged, memory(), &|| false), Err(Error::Stale)));
    for target in [fixture(Some(StoryTone::Brisk), &["unspoken"]), fixture(Some(StoryTone::Warm), &["UNSPOKEN"])] {
        let source = fixture(Some(StoryTone::Warm), &["unspoken"]);
        let (_, receipt, _) = generated(&source, memory());
        assert_eq!(source.scope(), target.scope());
        assert_eq!(source.revision(), target.revision());
        let mut target = target;
        let before = target.clone();
        assert!(matches!(target.commit_scene_play_v1(bound(&source, &receipt, memory()), receipt.play().unwrap(), &|| false), Err(Error::Stale)));
        unchanged(&target, &before);
    }
}

#[test]
fn finite_new_generated_prose_guard_falls_back_without_claiming_universal_semantics() {
    for text in ["I walked through a forest.", "I’m pleased with myself.", "We wait here.", "You travel to a forest.", "You walk along the quay."] {
        for recipe in [memory(), SceneRecipeV1::LiteralV1] {
            let mut engine = fixture(None, &[]);
            let request = make_request(&engine, "guard", "I wait for one tide tick.");
            let mut script = Script::new(Command::Wait { ticks: 1 }, text, 1);
            let receipt = execute(&mut engine, &request, &mut script, recipe).unwrap();
            assert!(receipt.play().unwrap().fallback, "finite fixture should fall back: {text}");
            assert_eq!(receipt.narration(), locallore::engine::render(receipt.events()));
            assert_eq!(script.seen.len(), 2, "no extra repair/model call after narration refusal");
        }
    }
    // Positive second-person and actual Move controls appear in separate tests.
    // Unlisted paraphrases, all emotions/languages and quality are NOT proven.
}

#[test]
fn seed_exclusions_apply_to_generated_text_and_exact_mechanical_fallback() {
    for recipe in [memory(), SceneRecipeV1::LiteralV1] {
        let source = fixture(Some(StoryTone::Warm), &["pause"]);
        let mut engine = source.clone();
        let request = make_request(&source, "excluded", "I wait for one tide tick.");
        let receipt = execute(&mut engine, &request, &mut Script::new(Command::Wait { ticks: 1 }, PROSE, 1), recipe).unwrap();
        assert!(receipt.play().unwrap().fallback);
        let summary = receipt.narration().to_owned();
        assert_eq!(summary, locallore::engine::render(receipt.events()));
        let mut blocked = fixture(Some(StoryTone::Warm), &["pause", &summary]);
        let before = blocked.clone();
        let request = make_request(&blocked, "blocked-fallback", "I wait for one tide tick.");
        let result = execute(&mut blocked, &request, &mut Script::new(Command::Wait { ticks: 1 }, PROSE, 1), recipe);
        assert_eq!(result, Err(Error::Narration));
        unchanged(&blocked, &before);
    }
}

#[test]
fn valid_typed_authored_world_refuses_new_scene_before_first_director_call_and_bind() {
    let source = authored_world();
    let request = make_request(&source, "unsupported-world", "I wait for one tide tick.");
    for recipe in [memory(), SceneRecipeV1::LiteralV1] {
        let mut engine = source.clone();
        let mut no_calls = Script::default();
        assert_eq!(execute(&mut engine, &request, &mut no_calls, recipe), Err(Error::Version));
        assert!(no_calls.seen.is_empty());
        unchanged(&engine, &source);
        let proposal = Proposal {
            version: VERSION, scope: request.scope.clone(), turn: request.turn.clone(),
            expected_revision: request.expected_revision, commands: vec![Command::Wait { ticks: 1 }],
        };
        let stage = source.stage_scene_play_v1(&request, &proposal, &|| false).unwrap();
        assert!(matches!(source.bind_scene_play_v1(stage, recipe, &|| false), Err(Error::Version)));
    }
}

#[test]
fn cancelled_bind_render_commit_and_actual_pipeline_preserve_source() {
    let source = fixture(None, &[]);
    let (_, receipt, _) = generated(&source, memory());
    let stage = source.stage_scene_play_v1(receipt.request(), receipt.proposal(), &|| false).unwrap();
    assert!(matches!(source.bind_scene_play_v1(stage, memory(), &|| true), Err(Error::Cancelled)));
    assert!(matches!(render_scene_narrator_v1(&bound(&source, &receipt, memory()), &profile(), &|| true), Err(Error::Cancelled)));
    let mut target = source.clone();
    assert_eq!(target.commit_scene_play_v1(bound(&source, &receipt, memory()), receipt.play().unwrap(), &|| true), Err(Error::Cancelled));
    unchanged(&target, &source);
    for recipe in [memory(), SceneRecipeV1::LiteralV1] {
        let mut target = source.clone();
        let mut script = Script::new(Command::Wait { ticks: 1 }, PROSE, 1);
        script.cancel_narrator = true;
        assert_eq!(execute(&mut target, receipt.request(), &mut script, recipe), Err(Error::Cancelled));
        assert_eq!(script.seen.len(), 2);
        unchanged(&target, &source);
    }
}

struct CancelAfterNarration {
    cancel: Cancellation,
    observed: bool,
}
impl locallore::turn_trace::TraceSink for CancelAfterNarration {
    fn matches(&mut self, _: &Scope, _: u64, _: &str, _: &str) -> bool { true }
    fn record(&mut self, _: locallore::turn_trace::StageMeasurement) {}
    fn capture(&mut self, artifact: locallore::turn_capture::Artifact<'_>) {
        if matches!(artifact, locallore::turn_capture::Artifact::NarratorOutput(_)) {
            self.observed = true;
            self.cancel.cancel();
        }
    }
}
#[test]
fn cancellation_after_actual_narrator_capture_is_not_converted_into_excluded_fallback_error() {
    let ordinary = fixture(None, &[]);
    let request = make_request(&ordinary, "derive-summary", "I wait for one tide tick.");
    let proposal = Proposal {
        version: VERSION, scope: request.scope.clone(), turn: request.turn.clone(),
        expected_revision: request.expected_revision, commands: vec![Command::Wait { ticks: 1 }],
    };
    let summary = ordinary.stage_play_v25(&request, &proposal, &|| false).unwrap().approved().narration().to_owned();
    for recipe in [memory(), SceneRecipeV1::LiteralV1] {
        let mut engine = fixture(Some(StoryTone::Warm), &["pause", &summary]);
        let before = engine.clone();
        let request = make_request(&engine, "cancel-after-output", "I wait for one tide tick.");
        let cancel = Cancellation::default();
        let mut sink = CancelAfterNarration { cancel: cancel.clone(), observed: false };
        let mut script = Script::new(Command::Wait { ticks: 1 }, PROSE, 1);
        let coverage = CoverageRead::RawFallback(FallbackReason::Missing);
        let result = play::execute_traced_with_scene_recipe_v1(
            &mut engine, &request, &mut script, &cancel, &profile(), Some(&mut sink),
            ScenePlayConstructionInput {
                recipe,
                coverage: if matches!(recipe, SceneRecipeV1::Memory(_)) { Some(&coverage) } else { None },
            },
        );
        assert!(sink.observed, "actual narrator output must arrive before test cancellation");
        assert_eq!(script.seen.len(), 2);
        assert_eq!(result, Err(Error::Cancelled), "cancellation must not become fallback or exclusion failure");
        unchanged(&engine, &before);
    }
}

#[test]
fn committed_retry_wins_cancel_invalid_profile_new_construction_and_later_head_and_reopens() {
    for recipe in [memory(), SceneRecipeV1::LiteralV1] {
        let source = fixture(Some(StoryTone::Warm), &[]);
        let (mut engine, receipt, _) = generated(&source, recipe);
        let capability = bound(&source, &receipt, recipe);
        let wait = engine.request("later-head", Intent::Actions(vec![Command::Wait { ticks: 1 }]));
        let proposal = Engine::proposal(&wait).unwrap();
        let preview = engine.preview(&wait, &proposal).unwrap();
        engine.commit_prepared(&preview).unwrap();
        let before = engine.clone();
        let mut no_calls = Script::default();
        let cancel = Cancellation::default(); cancel.cancel();
        let mut invalid = profile(); invalid.context_tokens = 0;
        let other = if matches!(recipe, SceneRecipeV1::LiteralV1) { memory() } else { SceneRecipeV1::LiteralV1 };
        assert_eq!(play::execute_traced_with_scene_recipe_v1(
            &mut engine, receipt.request(), &mut no_calls, &cancel, &invalid, None,
            ScenePlayConstructionInput { recipe: other, coverage: None },
        ).unwrap(), receipt);
        assert_eq!(engine.commit_scene_play_v1(capability, receipt.play().unwrap(), &|| true).unwrap(), receipt);
        assert!(no_calls.seen.is_empty());
        unchanged(&engine, &before);
        let reopened = Engine::replay_records(engine.seed().clone(), engine.canonical_records()).unwrap();
        assert_eq!(reopened.canonical_records(), engine.canonical_records());
        assert_eq!(reopened.accepted_history_basis().unwrap(), engine.accepted_history_basis().unwrap());
        let strings: Vec<_> = engine.receipts().iter().map(|r| serde_json::to_string(r).unwrap()).collect();
        let restored = Engine::restore(engine.seed().clone(), &strings).unwrap();
        assert_eq!(restored.canonical_records(), engine.canonical_records());
        assert_eq!(serde_json::to_value(restored.receipts()[0].play().unwrap()).unwrap(), serde_json::to_value(receipt.play().unwrap()).unwrap());
    }
}

#[test]
fn literal_irrelevant_coverage_refuses_before_provider_but_exact_old_authored_retry_still_wins() {
    let mut source = fixture(None, &[]);
    let before = source.clone();
    let request = make_request(&source, "irrelevant", "I wait for one tide tick.");
    let coverage = CoverageRead::RawFallback(FallbackReason::Missing);
    let mut no_calls = Script::default();
    assert_eq!(play::execute_traced_with_scene_recipe_v1(
        &mut source, &request, &mut no_calls, &Cancellation::default(), &profile(), None,
        ScenePlayConstructionInput { recipe: SceneRecipeV1::LiteralV1, coverage: Some(&coverage) },
    ), Err(Error::Rule));
    assert!(no_calls.seen.is_empty());
    unchanged(&source, &before);
    let mut authored = authored_world();
    let request = make_request(&authored, "old-authored", "I wait for one tide tick.");
    let mut old = Script::new(Command::Wait { ticks: 1 }, "You pause.", 1);
    let receipt = play::execute(&mut authored, &request, &mut old, &Cancellation::default(), &profile()).unwrap();
    assert!(receipt.play().unwrap().scene.is_none());
    let before = authored.clone();
    let cancel = Cancellation::default(); cancel.cancel();
    let mut invalid = profile(); invalid.context_tokens = 0;
    assert_eq!(play::execute_traced_with_scene_recipe_v1(
        &mut authored, &request, &mut no_calls, &cancel, &invalid, None,
        ScenePlayConstructionInput { recipe: SceneRecipeV1::LiteralV1, coverage: Some(&coverage) },
    ).unwrap(), receipt);
    assert!(no_calls.seen.is_empty());
    unchanged(&authored, &before);
}

#[test]
fn original_default_25_literal26_presentation27_28_and_historical21_24_keep_old_records() {
    for (tone, literal, expected) in [
        (None, false, "locallore-play-v2.5"),
        (None, true, "locallore-play-v2.6-literal-director-v1"),
        (Some(StoryTone::Warm), false, "locallore-play-v2.7-story-presentation-v1"),
        (Some(StoryTone::Warm), true, "locallore-play-v2.8-literal-director-v1-story-presentation-v1"),
    ] {
        let source = fixture(tone, &[]);
        let mut engine = source.clone();
        let request = make_request(&source, "unchanged-old", "I wait for one tide tick.");
        let mut script = Script::new(Command::Wait { ticks: 1 }, "I felt a quiet breeze.", 1);
        let receipt = if literal && tone.is_some() {
            play::execute_traced_with_literal_director_presentation_v1(&mut engine, &request, &mut script, &Cancellation::default(), &profile(), None)
        } else if literal {
            play::execute_traced_with_literal_director_v1(&mut engine, &request, &mut script, &Cancellation::default(), &profile(), None)
        } else { play::execute(&mut engine, &request, &mut script, &Cancellation::default(), &profile()) }.unwrap();
        let record = receipt.play().unwrap();
        assert_eq!(record.prompt_version, expected);
        assert_eq!(record.policy, if tone.is_some() { play::PRESENTATION_NARRATION_POLICY } else { play::NARRATION_POLICY });
        assert!(!record.fallback, "new first-person guard must not reinterpret old policies");
        assert!(record.scene.is_none());
        assert!(serde_json::to_value(record).unwrap().get("scene").is_none());
        assert!(role(&script, 1).1.contains("Small sensory/emotional description is allowed."));
        let old_stage = source.stage_play_v25(&request, receipt.proposal(), &|| false).unwrap();
        let safe = serde_json::to_string(old_stage.narrator_evidence()).unwrap();
        let legacy = format!("Write brief natural story prose in second person from ONLY this approved evidence. The action has already resolved. Observation values describe ONLY discoveries actually made in this turn. No additional items, abilities, healing, movement, discoveries, hidden facts or NPC knowledge. Give is possession transfer, not consumption or healing. A delivered statement supplies no quotation or established fact. No NPC quotation or impersonation. Small sensory/emotional description is allowed. Return JSON text, event_ids and speaker narrator. Approved evidence: {safe}");
        if tone.is_none() { assert_eq!(role(&script, 1).1, legacy); }
        else { assert!(role(&script, 1).1.starts_with(&legacy)); }
        let restored = Engine::replay_records(engine.seed().clone(), engine.canonical_records()).unwrap();
        assert_eq!(serde_json::to_value(restored.receipts()[0].play().unwrap()).unwrap(), serde_json::to_value(record).unwrap());
    }
    for text in [
        include_str!("fixtures/accepted_play_v2_1.json"), include_str!("fixtures/accepted_play_v2_2.json"),
        include_str!("fixtures/accepted_play_v2_3.json"), include_str!("fixtures/accepted_play_v2_4.json"),
    ] {
        let fixture: Value = serde_json::from_str(text).unwrap();
        let seed: Seed = serde_json::from_value(fixture["seed"].clone()).unwrap();
        let restored = Engine::restore(seed, &[fixture["receipt"].to_string()]).unwrap();
        let receipt = &restored.receipts()[0];
        assert_eq!(serde_json::to_value(receipt).unwrap(), fixture["receipt"]);
        assert!(receipt.play().unwrap().scene.is_none());
        if receipt.play().unwrap().prompt_version == "locallore-play-v2.4" {
            assert_eq!(serde_json::to_vec(receipt).unwrap().as_slice(), include_bytes!("fixtures/accepted_play_v2_4_receipt.json").as_slice());
        }
    }
}

#[test]
fn every_old_validator_family_refuses_scene_some_on_otherwise_valid_original_records() {
    let provenance = json!({"version":1,"frame_sha256":"a".repeat(64)});
    for (tone, literal) in [
        (None, false), (None, true),
        (Some(StoryTone::Warm), false), (Some(StoryTone::Warm), true),
    ] {
        let source = fixture(tone, &[]);
        let mut actual = source.clone();
        let request = make_request(&source, "old-scene-injection", "I wait for one tide tick.");
        let mut script = Script::new(Command::Wait { ticks: 1 }, PROSE, 1);
        let receipt = if literal && tone.is_some() {
            play::execute_traced_with_literal_director_presentation_v1(&mut actual, &request, &mut script, &Cancellation::default(), &profile(), None)
        } else if literal {
            play::execute_traced_with_literal_director_v1(&mut actual, &request, &mut script, &Cancellation::default(), &profile(), None)
        } else {
            play::execute(&mut actual, &request, &mut script, &Cancellation::default(), &profile())
        }.unwrap();
        let mut wire = serde_json::to_value(receipt.play().unwrap()).unwrap();
        assert!(wire.get("scene").is_none(), "old record must calibrate before injection");
        wire["scene"] = provenance.clone();
        let forged: play::PlayRecord = serde_json::from_value(wire).unwrap();
        let mut target = source.clone();
        assert!(target.commit_play(receipt.request(), receipt.proposal(), &forged).is_err(),
            "new optional provenance cannot be ignored by old memory/literal/presentation admission");
        unchanged(&target, &source);
    }
    for text in [
        include_str!("fixtures/accepted_play_v2_1.json"), include_str!("fixtures/accepted_play_v2_2.json"),
        include_str!("fixtures/accepted_play_v2_3.json"), include_str!("fixtures/accepted_play_v2_4.json"),
    ] {
        let fixture: Value = serde_json::from_str(text).unwrap();
        let seed: Seed = serde_json::from_value(fixture["seed"].clone()).unwrap();
        let valid = Engine::restore(seed.clone(), &[fixture["receipt"].to_string()]).unwrap();
        assert_eq!(serde_json::to_value(&valid.receipts()[0]).unwrap(), fixture["receipt"]);
        let mut forged = fixture["receipt"].clone();
        forged["play"]["scene"] = provenance.clone();
        assert!(Engine::restore(seed, &[forged.to_string()]).is_err(),
            "history-only legacy admission must also reject new scene provenance");
    }
}
