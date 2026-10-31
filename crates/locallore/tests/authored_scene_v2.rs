// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Original contract oracles, source-frozen before implementation. UNRUN.
//! Actual authored origins/Engine histories and recording providers; no model.
use locallore::{
    author_correction::*, contracts::*,
    engine::{staged_authored_scene_play::BoundAuthoredScenePlayV2, Engine},
    inference::*, memory_coverage::{CoverageRead, FallbackReason},
    play::{self, authored_scene_narration::{
        render_authored_scene_narrator_v2, AuthoredScenePlayConstructionInput,
        AuthoredSceneRecipeV2, AUTHORED_SCENE_NARRATION_POLICY_V2,
        AUTHORED_SCENE_PROMPT_VERSION_V2, LITERAL_AUTHORED_SCENE_PROMPT_VERSION_V2,
    }, PlayContextPolicy, PlayProfile},
    story_authoring::*, story_presentation::{StoryPresentationV1, StoryTone},
};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{collections::{BTreeSet, VecDeque}, task::Poll};

const LOCAL_DESCRIPTION: &str = "PRIVATE_LOCATION_DESCRIPTION_V2";
const REMOTE_NAME: &str = "Silver Grotto";
const REMOTE_DESCRIPTION: &str = "PRIVATE_REMOTE_DESCRIPTION_V2";
const NPC_DESCRIPTION: &str = "PRIVATE_NPC_SHEET_V2";
const BELIEF: &str = "PRIVATE_NPC_BELIEF_V2";
const REASON: &str = "PRIVATE_CORRECTION_REASON_V2";
const CORRECTED: &str = "The remembered place now has an untyped corrected account.";

fn profile() -> PlayProfile {
    PlayProfile { id: "authored-scene-v2-test".into(), model_sha256: "a".repeat(64),
        runtime_revision: "b".repeat(40), template_sha256: "c".repeat(64),
        worker_sha256: "d".repeat(64), profile_manifest_sha256: "e".repeat(64),
        context_tokens: 4096, director_tokens: 350, narrator_tokens: 350,
        deadline_ms: 5000, repair_limit: 1 }
}
fn memory() -> AuthoredSceneRecipeV2 {
    AuthoredSceneRecipeV2::Memory(PlayContextPolicy::StateRelevantMemoryV1)
}
struct World { engine: Engine, local: String, remote: String, fact: String, remote_fact: String }
fn world(name: &str) -> World {
    presented_world(name, StoryPresentationV1::default())
}
fn presented_world(name: &str, presentation: StoryPresentationV1) -> World {
    let input = InitialStoryInputV1 { version: 1, premise: "A surveyor pauses by an orchard.".into(),
        player_name: "Rae".into(), player_description: "A patient surveyor.".into(),
        cast: vec![InitialCastHintV1 { name: "Finch".into(), description: "A keeper.".into() },
            InitialCastHintV1 { name: "Orchard".into(), description: "A distant keeper.".into() }],
        profile: InitialRuleProfileV1::NarrativeV1, presentation };
    let proposal = InitialWorldProposalV1 { version: 1,
        locations: vec![InitialLocationV1 { name: name.into(), description: LOCAL_DESCRIPTION.into() },
            InitialLocationV1 { name: REMOTE_NAME.into(), description: REMOTE_DESCRIPTION.into() }],
        player_location: 0,
        characters: vec![InitialCharacterV1 { name: "Finch".into(), description: NPC_DESCRIPTION.into(), location: 0, known_by: vec![1] },
            InitialCharacterV1 { name: "Orchard".into(), description: "PRIVATE_REMOTE_NPC_V2".into(), location: 1, known_by: vec![2] }],
        routes: vec![InitialRouteV1 { from: 0, to: 1 }, InitialRouteV1 { from: 1, to: 0 }],
        facts: vec![InitialFactV1 { text: "PRIVATE_UNRELATED_KNOWN_FACT_V2".into(), known_by: vec![0], discoverable_at: None }],
        beliefs: vec![InitialBeliefV1 { believer: 1, text: BELIEF.into(), confidence: InitialConfidenceV1::Believed }],
        possessions: vec![] };
    validate_proposal(&input, &proposal).unwrap();
    let response = serde_json::to_string(&proposal).unwrap();
    let origin = InitialWorldOriginV1 { version: 1,
        generation: InitialGenerationV1 { input: input.clone(), proposal: proposal.clone(),
            model_profile: profile().id.clone(), model_configuration: InitialModelConfigurationV1::from(&profile()),
            provider: InitialProviderKindV1::Scripted, prompt_version: locallore::story_authoring::PROMPT_VERSION.into(),
            schema_version: locallore::story_authoring::SCHEMA_VERSION.into(),
            response_sha256: format!("{:x}", Sha256::digest(response.as_bytes())), response },
        reviewed: input, accepted: proposal, title: "Survey of two places".into() };
    let hash = origin_hash(&origin).unwrap();
    let prefix = &hash[..20];
    let seed = materialize(&origin, Scope { story: "authored-scene-test".into(), branch: "main".into() }).unwrap();
    validate_origin(&seed).unwrap();
    let engine = Engine::new(seed).unwrap();
    assert_eq!(engine.domain_version(), 1, "authored origin alone is not Domain2");
    World { engine, local: format!("l-{prefix}-0"), remote: format!("l-{prefix}-1"),
        fact: format!("f-{prefix}-location-0"), remote_fact: format!("f-{prefix}-location-1") }
}
fn request(source: &Engine, key: &str) -> Request {
    source.request(key, Intent::FreeText { kind: PlayInputKind::Action, text: "I take the chosen action.".into() })
}
fn proposal(request: &Request, commands: Vec<Command>) -> Proposal {
    Proposal { version: VERSION, scope: request.scope.clone(), turn: request.turn.clone(),
        expected_revision: request.expected_revision, commands }
}
fn append(source: &mut Engine, key: &str, commands: Vec<Command>) {
    let request = source.request(key, Intent::Actions(commands));
    let proposal = Engine::proposal(&request).unwrap();
    let receipt = source.preview(&request, &proposal).unwrap();
    source.commit_prepared(&receipt).unwrap();
}
fn corrected(source: &Engine, fact: &str, branch: &str, replacement: &str) -> Engine {
    let input = AuthorCorrectionInputV1 { version: 1, parent: source.scope().clone(),
        expected_parent_revision: source.revision(), fork_revision: source.revision(), child_branch: branch.into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition { fact: fact.into(),
            expected_proposition: source.seed().facts[fact].proposition.clone(), replacement: replacement.into() },
        reason: REASON.into() };
    let plan = source.prepare_author_correction(&input, &|| false).unwrap();
    let child = source.apply_author_correction(&plan, &|| false).unwrap().engine;
    assert_eq!(child.domain_version(), 2);
    child
}
fn unchanged(actual: &Engine, before: &Engine) {
    assert_eq!(actual.seed(), before.seed());
    assert_eq!(actual.canonical_bytes(), before.canonical_bytes());
    assert_eq!(actual.canonical_records(), before.canonical_records());
    assert_eq!(actual.accepted_history_basis().unwrap(), before.accepted_history_basis().unwrap());
}
#[derive(Default)]
struct Script { replies: VecDeque<Vec<u8>>, seen: Vec<GenerationRequest>, forbidden: Vec<&'static str>, cancel_narrator: bool }
impl Script {
    fn new(source: &Engine, request: &Request, commands: Vec<Command>, text: &str) -> Self {
        let ids: Vec<_> = source.preview(request, &proposal(request, commands.clone())).unwrap()
            .events().iter().map(|event| event.sequence()).collect();
        Self { replies: [json!({"commands":commands}), json!({"text":text,"event_ids":ids,"speaker":"narrator"})]
            .into_iter().map(|value| serde_json::to_vec(&value).unwrap()).collect(), ..Self::default() }
    }
}
impl InferenceProvider for Script {
    fn poll(&mut self, request: &GenerationRequest, cancel: &Cancellation) -> Poll<Result<Vec<u8>, Error>> {
        if let Input::Structured { role, prompt, .. } = &request.input {
            if role == "narrator" {
                for secret in &self.forbidden { assert!(!prompt.contains(secret), "private source reached narrator: {secret}"); }
                if self.cancel_narrator { cancel.cancel(); }
            }
        }
        self.seen.push(request.clone());
        Poll::Ready(self.replies.pop_front().ok_or(Error::Provider))
    }
}
fn execute(source: &mut Engine, request: &Request, script: &mut Script, recipe: AuthoredSceneRecipeV2) -> Result<Receipt, Error> {
    let coverage = CoverageRead::RawFallback(FallbackReason::Missing);
    play::execute_traced_with_authored_scene_recipe_v2(source, request, script, &Cancellation::default(), &profile(), None,
        AuthoredScenePlayConstructionInput { recipe, coverage: if matches!(recipe, AuthoredSceneRecipeV2::Memory(_)) { Some(&coverage) } else { None } })
}
fn generated(source: &Engine, key: &str, text: &str, recipe: AuthoredSceneRecipeV2) -> (Engine, Receipt, Script) {
    let request = request(source, key);
    let mut script = Script::new(source, &request, vec![Command::Wait { ticks: 1 }], text);
    let mut after = source.clone();
    let receipt = execute(&mut after, &request, &mut script, recipe).unwrap();
    (after, receipt, script)
}
fn bound(source: &Engine, receipt: &Receipt, recipe: AuthoredSceneRecipeV2) -> BoundAuthoredScenePlayV2 {
    let stage = source.stage_authored_scene_play_v2(receipt.request(), receipt.proposal(), &|| false).unwrap();
    source.bind_authored_scene_play_v2(stage, recipe, &|| false).unwrap()
}
fn frame(source: &Engine, key: &str, commands: Vec<Command>) -> (Value, Value) {
    let before = source.clone();
    let request = request(source, key);
    let staged = source.stage_authored_scene_play_v2(&request, &proposal(&request, commands), &|| false).unwrap();
    let frame = serde_json::to_value(staged.scene_frame()).unwrap();
    let evidence = serde_json::to_value(staged.narrator_evidence()).unwrap();
    let actual_keys: BTreeSet<_> = frame.as_object().unwrap().keys().map(String::as_str).collect();
    assert_eq!(actual_keys, ["version","scope","before_revision","after_revision","player","location","location_label"].into());
    assert_eq!(frame["version"], 2);
    assert_eq!(frame["scope"], json!(source.scope()));
    assert_eq!(frame["before_revision"], source.revision());
    assert_eq!(frame["player"], source.seed().player);
    for secret in [LOCAL_DESCRIPTION, REMOTE_DESCRIPTION, NPC_DESCRIPTION, BELIEF, REASON, "PRIVATE_UNRELATED_KNOWN_FACT_V2"] {
        assert!(!frame.to_string().contains(secret), "frame copied private payload {secret}");
    }
    drop(staged);
    unchanged(source, &before);
    (frame, evidence)
}

#[test]
fn actual_authored_memory_and_literal_narration_use_typed_label_renderer_and_exact_provenance() {
    assert_eq!(AUTHORED_SCENE_PROMPT_VERSION_V2, "locallore-play-v2.11-authored-scene-frame-v2");
    assert_eq!(LITERAL_AUTHORED_SCENE_PROMPT_VERSION_V2, "locallore-play-v2.12-literal-director-v1-authored-scene-frame-v2");
    assert_eq!(AUTHORED_SCENE_NARRATION_POLICY_V2, "grounded-prose-v2.8-authored-scene-frame-v2");
    for recipe in [memory(), AuthoredSceneRecipeV2::LiteralV1] {
        let world = world("Copper Orchard");
        let mut after = world.engine.clone();
        let request = request(&after, "faithful-label");
        let text = "You pause at Copper Orchard.";
        let mut script = Script::new(&after, &request, vec![Command::Wait { ticks: 1 }], text);
        script.forbidden = vec![LOCAL_DESCRIPTION, REMOTE_NAME, REMOTE_DESCRIPTION, NPC_DESCRIPTION, BELIEF, REASON, "PRIVATE_UNRELATED_KNOWN_FACT_V2"];
        let receipt = execute(&mut after, &request, &mut script, recipe).unwrap();
        assert!(!receipt.play().unwrap().fallback);
        assert_eq!(receipt.narration(), text);
        assert_eq!(after.revision(), world.engine.revision() + 1);
        let approved = world.engine.preview(&request, &proposal(&request, vec![Command::Wait { ticks: 1 }])).unwrap();
        let mut mechanical = world.engine.clone();
        mechanical.commit_prepared(&approved).unwrap();
        assert_eq!(after.state(), mechanical.state(), "prose cannot change approved effects");
        let capability = bound(&world.engine, &receipt, recipe);
        let serialized = serde_json::to_value(capability.scene_frame()).unwrap();
        let observed = world.engine.observed_facts(&world.engine.seed().player, world.engine.scope(), world.engine.revision()).unwrap();
        assert_eq!(serialized["location_label"], json!({"location_id":world.local,"name":"Copper Orchard","fact_id":world.fact,"observation":observed[&world.fact].observation}));
        let rendered = render_authored_scene_narrator_v2(&capability, &profile(), &|| false).unwrap();
        assert_eq!(script.seen.len(), 2);
        let Input::Structured { role, prompt, schema } = &script.seen[1].input else { panic!("structured narrator input required") };
        assert_eq!(role, "narrator");
        assert_eq!(prompt, rendered.prompt());
        assert_eq!(schema, rendered.schema());
        assert!(prompt.contains(&serde_json::to_string(capability.scene_frame()).unwrap()));
        let record = receipt.play().unwrap();
        assert_eq!(record.policy, AUTHORED_SCENE_NARRATION_POLICY_V2);
        assert_eq!(record.prompt_version, if matches!(recipe, AuthoredSceneRecipeV2::LiteralV1) { LITERAL_AUTHORED_SCENE_PROMPT_VERSION_V2 } else { AUTHORED_SCENE_PROMPT_VERSION_V2 });
        assert_eq!(record.context_policy.is_some(), matches!(recipe, AuthoredSceneRecipeV2::Memory(_)));
        assert_eq!(record.scene.as_ref().unwrap().version, 2);
        assert_eq!(record.scene.as_ref().unwrap().frame_sha256, format!("{:x}", Sha256::digest(serde_json::to_vec(capability.scene_frame()).unwrap())));
    }
}

#[test]
fn move_does_not_discover_a_label_but_actual_destination_discovery_binds_its_typed_source() {
    let mut world = world("Copper Orchard");
    let (moved, _) = frame(&world.engine, "move-preview", vec![Command::Move { to: world.remote.clone() }]);
    assert_eq!(moved["location"], world.remote);
    assert!(moved["location_label"].is_null());
    append(&mut world.engine, "actual-move", vec![Command::Move { to: world.remote.clone() }]);
    let (waiting, _) = frame(&world.engine, "moved-wait", vec![Command::Wait { ticks: 1 }]);
    assert!(waiting["location_label"].is_null());
    let (discovered, evidence) = frame(&world.engine, "discover-place", vec![Command::Discover { fact: world.remote_fact.clone() }]);
    assert_eq!(discovered["location_label"]["name"], REMOTE_NAME);
    assert_eq!(discovered["location_label"]["fact_id"], world.remote_fact);
    assert_eq!(discovered["location_label"]["observation"]["kind"], "event");
    assert!(evidence.to_string().contains(REMOTE_DESCRIPTION), "authorized current discovery remains actual observation evidence");
    append(&mut world.engine, "record-discovery", vec![Command::Discover { fact: world.remote_fact.clone() }]);
    let observed = world.engine.observed_facts(&world.engine.seed().player, world.engine.scope(), world.engine.revision()).unwrap();
    let (remembered, _) = frame(&world.engine, "remember-place", vec![Command::Wait { ticks: 1 }]);
    assert_eq!(remembered["location_label"]["observation"], json!(observed[&world.remote_fact].observation));
}

#[test]
fn actual_domain2_correction_keeps_remembered_label_until_corrected_rediscovery_omits_it() {
    let world = world("Copper Orchard");
    let source = corrected(&world.engine, &world.fact, "corrected-place", CORRECTED);
    let (remembered, _) = frame(&source, "before-rediscovery", vec![Command::Wait { ticks: 1 }]);
    assert_eq!(remembered["location_label"]["name"], "Copper Orchard");
    let (after, receipt, script) = generated(&source, "domain2-memory", "You pause at Copper Orchard.", memory());
    assert!(!receipt.play().unwrap().fallback);
    assert_eq!(after.domain_version(), 2);
    let Input::Structured { prompt, .. } = &script.seen[1].input else { unreachable!() };
    for secret in [CORRECTED, REASON, LOCAL_DESCRIPTION, BELIEF] { assert!(!prompt.contains(secret)); }
    let (rediscovered, evidence) = frame(&source, "rediscovery", vec![Command::Discover { fact: world.fact.clone() }]);
    assert!(rediscovered["location_label"].is_null());
    assert!(evidence.to_string().contains(CORRECTED));
    assert!(!evidence.to_string().contains(REASON));
    let mut later = source.clone();
    append(&mut later, "remember-correction", vec![Command::Discover { fact: world.fact.clone() }]);
    let (waiting, _) = frame(&later, "corrected-wait", vec![Command::Wait { ticks: 1 }]);
    assert!(waiting["location_label"].is_null());
    let mut target = source.clone();
    let mut no_calls = Script::default();
    assert_eq!(execute(&mut target, &request(&source, "domain2-literal"), &mut no_calls, AuthoredSceneRecipeV2::LiteralV1), Err(Error::Version));
    assert!(no_calls.seen.is_empty());
    unchanged(&target, &source);
}

#[test]
fn complete_label_occurrences_do_not_authorize_fragments_hidden_overlaps_or_unicode_continuations() {
    let source = world("Copper Orchard").engine;
    for text in ["You pause at Copper Orchard.", "You pause at copper orchard.", "You pause at Copper Orchard's edge.", "You pause at Copper Orchard’s edge."] {
        let (_, receipt, _) = generated(&source, "whole-label", text, memory());
        assert!(!receipt.play().unwrap().fallback, "faithful whole label: {text}");
        assert_eq!(receipt.narration(), text);
    }
    for text in ["You pause at Copper.", "You pause at Orchard.", "You pause at copper orchard\u{301}.", "You pause at copper orchard—shadow.", "You pause at x'copper orchard.", "You pause at Copper Orchardson.", "You pause at Copper Orchard's's edge."] {
        let (_, receipt, script) = generated(&source, "not-whole-label", text, memory());
        assert!(receipt.play().unwrap().fallback, "label is not general word authority: {text}");
        assert_eq!(receipt.narration(), locallore::engine::render(receipt.events()));
        assert_eq!(script.seen.len(), 2);
    }
    let source = world("İpek Terrace").engine;
    let (_, receipt, _) = generated(&source, "unicode-label", "You pause; İpek Terrace remains quiet.", memory());
    assert!(!receipt.play().unwrap().fallback);
}

#[test]
fn source_scope_head_and_complete_history_basis_are_required_for_binding_and_commit() {
    let world = world("Copper Orchard");
    let source = &world.engine;
    let (_, receipt, _) = generated(source, "bound", "You pause at Copper Orchard.", memory());
    let sibling = source.fork("sibling", source.revision()).unwrap();
    let stage = source.stage_authored_scene_play_v2(receipt.request(), receipt.proposal(), &|| false).unwrap();
    assert!(matches!(sibling.bind_authored_scene_play_v2(stage, memory(), &|| false), Err(Error::Stale)));
    let mut stale = source.clone();
    append(&mut stale, "intervening", vec![Command::Wait { ticks: 1 }]);
    let before = stale.clone();
    assert!(matches!(stale.commit_authored_scene_play_v2(bound(source, &receipt, memory()), receipt.play().unwrap(), &|| false), Err(Error::Stale)));
    unchanged(&stale, &before);
    let left = corrected(source, &world.fact, "same-child", "PRIVATE_FIRST_CORRECTION");
    let right = corrected(source, &world.fact, "same-child", "PRIVATE_SECOND_CORRECTION");
    assert_eq!(left.scope(), right.scope());
    assert_eq!(left.revision(), right.revision());
    assert_ne!(left.accepted_history_basis().unwrap(), right.accepted_history_basis().unwrap());
    let request = request(&left, "history-basis");
    let stage = left.stage_authored_scene_play_v2(&request, &proposal(&request, vec![Command::Wait { ticks: 1 }]), &|| false).unwrap();
    assert!(matches!(right.bind_authored_scene_play_v2(stage, memory(), &|| false), Err(Error::Stale)));
}

#[test]
fn record_metadata_event_ids_and_cross_recipe_hashes_cannot_mint_commit_or_restore_authority() {
    for recipe in [memory(), AuthoredSceneRecipeV2::LiteralV1] {
        let source = world("Copper Orchard").engine;
        let (_, receipt, _) = generated(&source, "tamper", "You pause at Copper Orchard.", recipe);
        for fault in 0..6 {
            let mut record = receipt.play().unwrap().clone();
            match fault {
                0 => record.scene = None,
                1 => record.scene.as_mut().unwrap().version = 1,
                2 => record.scene.as_mut().unwrap().frame_sha256 = "0".repeat(64),
                3 => record.narration.event_ids = vec![999],
                4 => record.policy = play::NARRATION_POLICY.into(),
                _ => record.prompt_version = play::scene_narration::SCENE_PROMPT_VERSION_V1.into(),
            }
            let mut target = source.clone();
            assert!(target.commit_authored_scene_play_v2(bound(&source, &receipt, recipe), &record, &|| false).is_err());
            unchanged(&target, &source);
        }
        let other = if matches!(recipe, AuthoredSceneRecipeV2::LiteralV1) { memory() } else { AuthoredSceneRecipeV2::LiteralV1 };
        let mut target = source.clone();
        assert!(target.commit_authored_scene_play_v2(bound(&source, &receipt, other), receipt.play().unwrap(), &|| false).is_err());
        unchanged(&target, &source);
        let mut forged = serde_json::to_value(&receipt).unwrap();
        forged["play"]["scene"]["frame_sha256"] = json!("0".repeat(64));
        assert!(Engine::restore(source.seed().clone(), &[forged.to_string()]).is_err());
    }
}

#[test]
fn cancellation_before_stage_bind_commit_and_after_narrator_poll_never_changes_canon() {
    let source = world("Copper Orchard").engine;
    let request = request(&source, "cancelled");
    let proposal = proposal(&request, vec![Command::Wait { ticks: 1 }]);
    assert!(matches!(source.stage_authored_scene_play_v2(&request, &proposal, &|| true), Err(Error::Cancelled)));
    let stage = source.stage_authored_scene_play_v2(&request, &proposal, &|| false).unwrap();
    assert!(matches!(source.bind_authored_scene_play_v2(stage, memory(), &|| true), Err(Error::Cancelled)));
    let (_, receipt, _) = generated(&source, "cancelled", "You pause at Copper Orchard.", memory());
    let mut target = source.clone();
    assert_eq!(target.commit_authored_scene_play_v2(bound(&source, &receipt, memory()), receipt.play().unwrap(), &|| true), Err(Error::Cancelled));
    unchanged(&target, &source);
    let mut script = Script::new(&source, &request, proposal.commands.clone(), "You pause at Copper Orchard.");
    script.cancel_narrator = true;
    assert_eq!(execute(&mut target, &request, &mut script, memory()), Err(Error::Cancelled));
    assert_eq!(script.seen.len(), 2);
    unchanged(&target, &source);
}

struct NoInference;
impl InferenceProvider for NoInference {
    fn poll(&mut self, _: &GenerationRequest, _: &Cancellation) -> Poll<Result<Vec<u8>, Error>> { panic!("recorded retry must not invoke inference") }
}
#[test]
fn exact_retry_wins_later_head_cancel_and_other_recipe_and_all_canonical_records_replay() {
    let world = world("Copper Orchard");
    for source in [world.engine.clone(), corrected(&world.engine, &world.fact, "durable-child", CORRECTED)] {
        let (mut after, receipt, _) = generated(&source, "exact", "You pause at Copper Orchard.", memory());
        let capability = bound(&source, &receipt, memory());
        append(&mut after, "later", vec![Command::Wait { ticks: 1 }]);
        let before = after.clone();
        let cancel = Cancellation::default(); cancel.cancel();
        let mut invalid = profile(); invalid.context_tokens = 0;
        assert_eq!(play::execute_traced_with_authored_scene_recipe_v2(&mut after, receipt.request(), &mut NoInference, &cancel, &invalid, None,
            AuthoredScenePlayConstructionInput { recipe: AuthoredSceneRecipeV2::LiteralV1, coverage: None }).unwrap(), receipt);
        assert_eq!(after.commit_authored_scene_play_v2(capability, receipt.play().unwrap(), &|| true).unwrap(), receipt);
        unchanged(&after, &before);
        let reopened = Engine::replay_records(after.seed().clone(), after.canonical_records()).unwrap();
        unchanged(&reopened, &after);
    }
}

#[test]
fn version1_still_refuses_authored_world_and_version2_does_not_retag_starter_seeds() {
    let source = world("Copper Orchard").engine;
    let v1_request = request(&source, "v1-refusal");
    for recipe in [play::scene_narration::SceneRecipeV1::Memory(PlayContextPolicy::StateRelevantMemoryV1), play::scene_narration::SceneRecipeV1::LiteralV1] {
        let coverage = CoverageRead::RawFallback(FallbackReason::Missing);
        let mut target = source.clone(); let mut script = Script::default();
        assert_eq!(play::execute_traced_with_scene_recipe_v1(&mut target, &v1_request, &mut script, &Cancellation::default(), &profile(), None,
            play::scene_narration::ScenePlayConstructionInput { recipe, coverage: if matches!(recipe, play::scene_narration::SceneRecipeV1::Memory(_)) { Some(&coverage) } else { None } }), Err(Error::Version));
        assert!(script.seen.is_empty()); unchanged(&target, &source);
    }
    let seed: Seed = serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    let starter = Engine::new(seed).unwrap();
    let request = request(&starter, "not-authored");
    assert!(matches!(starter.stage_authored_scene_play_v2(&request, &proposal(&request, vec![Command::Wait { ticks: 1 }]), &|| false), Err(Error::Version)));
}

#[test]
fn authored_presentation_is_bound_and_exclusions_apply_without_becoming_world_authority() {
    let presentation = StoryPresentationV1 { version: 1, tone: StoryTone::Warm,
        excluded_phrases: vec!["excluded-authored-v2".into()] };
    for recipe in [memory(), AuthoredSceneRecipeV2::LiteralV1] {
        let source = presented_world("Copper Orchard", presentation.clone()).engine;
        let (_, receipt, script) = generated(&source, "presented", "You pause at Copper Orchard.", recipe);
        assert!(!receipt.play().unwrap().fallback);
        assert!(receipt.play().unwrap().story_presentation.is_some());
        let Input::Structured { prompt, .. } = &script.seen[1].input else { unreachable!() };
        assert!(prompt.contains("Use a warm, considerate tone"));
        assert!(prompt.contains("excluded-authored-v2"));
        let (_, excluded, _) = generated(&source, "excluded", "You pause at Copper Orchard. excluded-authored-v2", recipe);
        assert!(excluded.play().unwrap().fallback);
        assert_eq!(excluded.narration(), locallore::engine::render(excluded.events()));
    }
}
