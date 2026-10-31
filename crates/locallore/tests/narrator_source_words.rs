// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Recording synthetic providers exercise Core only; no model or language-understanding claim.
use locallore::{
    contracts::*,
    engine::{self, Engine},
    inference::*,
    memory_coverage::{CoverageRead, FallbackReason},
    play::{
        self,
        scene_narration::{ScenePlayConstructionInput, SceneRecipeV1},
        PlayContextPolicy, PlayProfile,
    },
    story_authoring::*,
    story_presentation::{StoryPresentationV1, StoryTone},
};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{collections::VecDeque, fs::OpenOptions, io::Write, path::Path, task::Poll};

const STRICT: &str = "grounded-prose-v2.5-whole-evidence-words-v1";
const PRESENTATION: &str = "grounded-prose-v2.6-story-presentation-whole-evidence-words-v1";
const SCENE: &str = "grounded-prose-v2.7-scene-frame-whole-evidence-words-v1";

#[derive(Clone, Copy, Debug)]
enum Family {
    Ordinary,
    Memory,
    Literal,
    Presentation,
    LiteralPresentation,
    SceneMemory,
    SceneLiteral,
    PresentedSceneMemory,
    PresentedSceneLiteral,
}

const FAMILIES: [Family; 9] = [
    Family::Ordinary,
    Family::Memory,
    Family::Literal,
    Family::Presentation,
    Family::LiteralPresentation,
    Family::SceneMemory,
    Family::SceneLiteral,
    Family::PresentedSceneMemory,
    Family::PresentedSceneLiteral,
];

impl Family {
    fn presented(self) -> bool {
        matches!(
            self,
            Self::Presentation
                | Self::LiteralPresentation
                | Self::PresentedSceneMemory
                | Self::PresentedSceneLiteral
        )
    }

    fn scene(self) -> bool {
        matches!(
            self,
            Self::SceneMemory
                | Self::SceneLiteral
                | Self::PresentedSceneMemory
                | Self::PresentedSceneLiteral
        )
    }

    fn strict_policy(self) -> &'static str {
        if self.scene() {
            SCENE
        } else if self.presented() {
            PRESENTATION
        } else {
            STRICT
        }
    }

    fn old_policy(self) -> &'static str {
        if self.scene() {
            "grounded-prose-v2.4-scene-frame-v1"
        } else if self.presented() {
            "grounded-prose-v2.3-story-presentation-v1"
        } else {
            "grounded-prose-v2.2"
        }
    }

    fn prompt(self) -> &'static str {
        match self {
            Self::Ordinary | Self::Memory => "locallore-play-v2.5",
            Self::Literal => "locallore-play-v2.6-literal-director-v1",
            Self::Presentation => "locallore-play-v2.7-story-presentation-v1",
            Self::LiteralPresentation => {
                "locallore-play-v2.8-literal-director-v1-story-presentation-v1"
            }
            Self::SceneMemory | Self::PresentedSceneMemory => "locallore-play-v2.9-scene-frame-v1",
            Self::SceneLiteral | Self::PresentedSceneLiteral => {
                "locallore-play-v2.10-literal-director-v1-scene-frame-v1"
            }
        }
    }
}

fn profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-source-words".into(),
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

fn fixture(family: Family, name: &str, observation: Option<&str>) -> Engine {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    seed.actors.get_mut("mira").unwrap().name = name.into();
    if family.presented() {
        seed.presentation = Some(StoryPresentationV1 {
            version: 1,
            tone: StoryTone::Warm,
            excluded_phrases: Vec::new(),
        });
    }
    if let Some(text) = observation {
        let fact = seed.facts.get_mut("relic-location").unwrap();
        fact.proposition = text.into();
        fact.discoverable_at = Some("quay".into());
        fact.known_by.clear();
    }
    Engine::new(seed).unwrap()
}

#[derive(Default)]
struct RecordingProvider {
    replies: VecDeque<Vec<u8>>,
    requests: Vec<GenerationRequest>,
    cancel_narrator: bool,
}

impl RecordingProvider {
    fn new(command: Command, text: &str) -> Self {
        Self {
            replies: [
                json!({"commands":[command]}),
                json!({"text":text,"event_ids":[1],"speaker":"narrator"}),
            ]
            .into_iter()
            .map(|value| serde_json::to_vec(&value).unwrap())
            .collect(),
            ..Self::default()
        }
    }
}

impl InferenceProvider for RecordingProvider {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        cancel: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        self.requests.push(request.clone());
        if self.cancel_narrator
            && matches!(&request.input, Input::Structured { role, .. } if role == "narrator")
        {
            cancel.cancel();
        }
        Poll::Ready(self.replies.pop_front().ok_or(Error::Provider))
    }
}

fn execute(
    family: Family,
    source: &mut Engine,
    request: &Request,
    provider: &mut RecordingProvider,
    cancel: &Cancellation,
) -> Result<Receipt, Error> {
    match family {
        Family::Ordinary | Family::Presentation => {
            play::execute(source, request, provider, cancel, &profile())
        }
        Family::Memory => {
            let coverage = CoverageRead::RawFallback(FallbackReason::Missing);
            play::execute_traced_with_coverage(
                source,
                request,
                provider,
                cancel,
                &profile(),
                None,
                &coverage,
            )
        }
        Family::Literal => play::execute_traced_with_literal_director_v1(
            source,
            request,
            provider,
            cancel,
            &profile(),
            None,
        ),
        Family::LiteralPresentation => play::execute_traced_with_literal_director_presentation_v1(
            source,
            request,
            provider,
            cancel,
            &profile(),
            None,
        ),
        _ => {
            let literal = matches!(family, Family::SceneLiteral | Family::PresentedSceneLiteral);
            let recipe = if literal {
                SceneRecipeV1::LiteralV1
            } else {
                SceneRecipeV1::Memory(PlayContextPolicy::StateRelevantMemoryV1)
            };
            let coverage = CoverageRead::RawFallback(FallbackReason::Missing);
            play::execute_traced_with_scene_recipe_v1(
                source,
                request,
                provider,
                cancel,
                &profile(),
                None,
                ScenePlayConstructionInput {
                    recipe,
                    coverage: if literal { None } else { Some(&coverage) },
                },
            )
        }
    }
}

fn gift() -> Command {
    Command::Give {
        item: "potion".into(),
        to: "mira".into(),
        quantity: 1,
    }
}

fn request(source: &Engine, discovery: bool) -> Request {
    source.request(
        "source-word-turn",
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: if discovery {
                "I discover relic-location."
            } else {
                "I give potion to mira."
            }
            .into(),
        },
    )
}

fn resolved(
    family: Family,
    name: &str,
    observation: Option<&str>,
    text: &str,
) -> (Engine, Receipt) {
    let mut source = fixture(family, name, observation);
    let before = source.clone();
    let request = request(&source, observation.is_some());
    let command = if observation.is_some() {
        Command::Discover {
            fact: "relic-location".into(),
        }
    } else {
        gift()
    };
    let mut provider = RecordingProvider::new(command.clone(), text);
    let receipt = execute(
        family,
        &mut source,
        &request,
        &mut provider,
        &Cancellation::default(),
    )
    .unwrap();
    assert_eq!(provider.requests.len(), 2, "{family:?}");
    assert!(provider.replies.is_empty());
    assert_eq!(receipt.proposal().commands, vec![command]);
    assert_eq!(source.state().actors, before.state().actors);
    if observation.is_none() {
        assert_eq!(source.state().items["potion"].owner, "mira");
        assert_eq!(source.state().items["potion"].quantity, 1);
    } else {
        assert_eq!(source.state().items, before.state().items);
        assert!(source.state().discoveries["relic-location"].contains("player"));
    }
    let history = vec![serde_json::to_string(&receipt).unwrap()];
    let restored = Engine::restore(source.seed().clone(), &history).unwrap();
    assert_eq!(restored.canonical_bytes(), source.canonical_bytes());
    let replayed = Engine::replay(source.seed().clone(), std::slice::from_ref(&receipt)).unwrap();
    assert_eq!(replayed.canonical_bytes(), source.canonical_bytes());
    assert_eq!(
        execute(
            family,
            &mut source,
            &request,
            &mut provider,
            &Cancellation::default()
        )
        .unwrap(),
        receipt
    );
    assert_eq!(provider.requests.len(), 2);
    let mut changed = request.clone();
    if let Intent::FreeText { text, .. } = &mut changed.intent {
        *text = "I wait one tick.".into();
    }
    assert_eq!(
        execute(
            family,
            &mut source,
            &changed,
            &mut provider,
            &Cancellation::default()
        ),
        Err(Error::RetryMismatch)
    );
    assert_eq!(provider.requests.len(), 2);
    (source, receipt)
}

fn generated(family: Family, name: &str, observation: Option<&str>, text: &str) {
    let (_, receipt) = resolved(family, name, observation, text);
    assert!(
        !receipt.play().unwrap().fallback,
        "faithful evidence word: {text:?}"
    );
    assert_eq!(receipt.narration(), text);
}

fn fallback(family: Family, observation: Option<&str>, text: &str) {
    let (_, receipt) = resolved(family, "Mira", observation, text);
    assert!(
        receipt.play().unwrap().fallback,
        "unapproved source-word fragment: {text:?}"
    );
    assert_eq!(receipt.narration(), engine::render(receipt.events()));
}

#[test]
fn source_actor_id_prefix_does_not_ground_an_unknown_recipient() {
    fallback(
        Family::Ordinary,
        None,
        "You pass the potion to Mir with care.",
    );
}

#[test]
fn source_item_prefix_does_not_ground_an_unknown_recipient() {
    fallback(
        Family::Ordinary,
        None,
        "You pass the potion to Pot with care.",
    );
}

#[test]
fn candidate_digits_underscores_hyphens_and_apostrophes_are_not_trimmed_into_known_words() {
    for name in [
        "Potion2",
        "Potion_",
        "Potion-",
        "XPotion",
        "Potionx",
        "Potion'son",
        "o'Potion",
        "o’Potion",
    ] {
        fallback(
            Family::Ordinary,
            None,
            &format!("You pass the potion to {name} with care."),
        );
    }
}

#[test]
fn hyphenated_and_underscored_evidence_does_not_grant_its_individual_fragments() {
    for name in ["Copper", "Marker", "Willow", "Grove"] {
        fallback(
            Family::Ordinary,
            Some("Copper-marker waits beside Willow_grove."),
            &format!("You notice {name} nearby."),
        );
    }
}

#[test]
fn internal_apostrophe_source_words_do_not_grant_suffix_name_fragments() {
    for name in ["Harbor", "Meadow"] {
        fallback(
            Family::Ordinary,
            Some("o'harbor waits beside o’meadow."),
            &format!("You notice {name} nearby."),
        );
    }
}

#[test]
fn unicode_prefix_case_expansion_and_combining_marks_do_not_create_short_aliases() {
    for name in ["Ré", "I", "R"] {
        fallback(
            Family::Ordinary,
            Some("réserve waits beside İris and r\u{301}ive."),
            &format!("You notice {name} nearby."),
        );
    }
}

#[test]
fn complete_evidence_words_keep_punctuation_outer_quotes_and_legitimate_possessives() {
    for text in [
        "You pass the Potion to Mira with care.",
        "You pass [Potion] to (Mira).",
        "You pass 'Potion' to Mira.",
        "You place the Potion in Mira's waiting hand.",
        "You place the Potion in Mira’s waiting hand.",
    ] {
        generated(Family::Ordinary, "Mira", None, text);
    }
}

#[test]
fn whole_visible_names_keep_multiword_unicode_and_possessive_spelling() {
    for (name, text) in [
        (
            "Sera Vale",
            "You place the potion in Sera Vale’s waiting hand.",
        ),
        ("Éira Núñez", "You pass the potion to Éira Núñez with care."),
        (
            "İpek Arden",
            "You pass the potion to İpek Arden; İpek Arden's waiting hand is steady.",
        ),
    ] {
        generated(Family::Ordinary, name, None, text);
    }
}

#[test]
fn exact_observed_compounds_apostrophes_and_unicode_words_remain_grounded() {
    for text in [
        "You notice Copper-marker beside Willow_grove.",
        "You notice O'harbor nearby.",
        "You notice Réserve beside İris.",
        "You notice R\u{301}ive nearby.",
    ] {
        generated(
            Family::Ordinary,
            "Mira",
            Some(
                "Copper-marker waits beside Willow_grove, o'harbor, réserve, İris and r\u{301}ive.",
            ),
            text,
        );
    }
}

#[test]
fn all_fresh_construction_families_select_the_new_policy_without_retagging_prompts() {
    for family in FAMILIES {
        let (_, receipt) = resolved(
            family,
            "Mira",
            None,
            "You pass the potion to Mira with care.",
        );
        assert!(!receipt.play().unwrap().fallback);
        assert_eq!(
            receipt.play().unwrap().policy,
            family.strict_policy(),
            "{family:?}"
        );
        assert_eq!(
            receipt.play().unwrap().prompt_version,
            family.prompt(),
            "{family:?}"
        );
    }
}

#[test]
fn ordinary_memory_literal_presentation_and_scene_paths_all_refuse_source_prefixes() {
    for family in FAMILIES {
        for text in [
            "You pass the potion to Mir with care.",
            "You pass the potion to Pot with care.",
        ] {
            fallback(family, None, text);
        }
    }
}

#[test]
fn cancellation_during_narration_leaves_all_fresh_families_without_a_transfer_or_receipt() {
    for family in FAMILIES {
        let mut source = fixture(family, "Mira", None);
        let before = source.canonical_bytes();
        let request = request(&source, false);
        let mut provider = RecordingProvider::new(gift(), "You pass the potion to Mira with care.");
        provider.cancel_narrator = true;
        assert_eq!(
            execute(
                family,
                &mut source,
                &request,
                &mut provider,
                &Cancellation::default()
            ),
            Err(Error::Cancelled)
        );
        assert_eq!(provider.requests.len(), 2);
        assert_eq!(source.canonical_bytes(), before);
        assert!(source.receipts().is_empty());
        assert_eq!(source.state().items["potion"].owner, "player");
    }
}

fn item_narration(item: &str, text: &str) -> Receipt {
    let mut seed = fixture(Family::Ordinary, "Mira", None).seed().clone();
    let value = seed.items.remove("potion").unwrap();
    assert!(seed.items.insert(item.into(), value).is_none());
    let mut source = Engine::new(seed).unwrap();
    let request = source.request(
        "sensitive-source-word",
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: format!("I give {item} to mira."),
        },
    );
    let command = Command::Give {
        item: item.into(),
        to: "mira".into(),
        quantity: 1,
    };
    let mut provider = RecordingProvider::new(command.clone(), text);
    let receipt = execute(
        Family::Ordinary,
        &mut source,
        &request,
        &mut provider,
        &Cancellation::default(),
    )
    .unwrap();
    assert_eq!(receipt.proposal().commands, vec![command]);
    assert_eq!(source.state().items[item].owner, "mira");
    assert_eq!(provider.requests.len(), 2);
    let history = vec![serde_json::to_string(&receipt).unwrap()];
    assert_eq!(
        Engine::restore(source.seed().clone(), &history)
            .unwrap()
            .canonical_bytes(),
        source.canonical_bytes()
    );
    assert_eq!(
        execute(
            Family::Ordinary,
            &mut source,
            &request,
            &mut provider,
            &Cancellation::default()
        )
        .unwrap(),
        receipt
    );
    assert_eq!(provider.requests.len(), 2);
    receipt
}

#[test]
fn lowercase_sensitive_words_are_not_grounded_by_longer_approved_item_ids() {
    for (item, text) in [
        (
            "kingfisher",
            "You pass kingfisher to mira while the king waits.",
        ),
        (
            "coinsmith",
            "You pass coinsmith to mira as coins fall nearby.",
        ),
    ] {
        let receipt = item_narration(item, text);
        assert!(
            receipt.play().unwrap().fallback,
            "source substring is not evidence: {text}"
        );
        assert_eq!(receipt.narration(), engine::render(receipt.events()));
    }
}

#[test]
fn an_approved_secret_prefix_does_not_grant_a_different_secret_lexeme() {
    let receipt = item_narration(
        "secret-herb",
        "You pass secret-herb to mira near secret-vault.",
    );
    assert!(receipt.play().unwrap().fallback);
    assert_eq!(receipt.narration(), engine::render(receipt.events()));
    let exact = "You pass secret-herb to mira with care.";
    let receipt = item_narration("secret-herb", exact);
    assert!(!receipt.play().unwrap().fallback);
    assert_eq!(receipt.narration(), exact);
}

fn legacy_cases() -> Vec<Value> {
    let raw = include_bytes!("../../../fixtures/narrator_source_words_legacy_v1.json");
    assert_eq!(
        format!("{:x}", Sha256::digest(raw)),
        "58b56d456220ef07b16721f31d0b2fddc125bc67e54fcfd366a9ff685e354b07"
    );
    let value: Value = serde_json::from_slice(raw).unwrap();
    assert_eq!(value["version"], 1);
    let cases = value["cases"].as_array().unwrap();
    assert_eq!(cases.len(), 18);
    for family in FAMILIES {
        assert_eq!(
            cases
                .iter()
                .filter(|case| case["family"] == format!("{family:?}"))
                .count(),
            2
        );
    }
    cases.clone()
}

fn legacy_family(case: &Value) -> Family {
    FAMILIES
        .into_iter()
        .find(|family| case["family"] == format!("{family:?}"))
        .unwrap()
}

fn restore_legacy(case: &Value) -> Engine {
    assert_eq!(case["outcome"], "accepted");
    assert_eq!(case["fallback"], false);
    let seed: Seed = serde_json::from_str(case["seed_json"].as_str().unwrap()).unwrap();
    let history = vec![case["receipt_json"].as_str().unwrap().to_owned()];
    let restored = Engine::restore(seed, &history).unwrap();
    let expected: Vec<u8> = serde_json::from_value(case["canonical_after"].clone()).unwrap();
    assert_eq!(restored.canonical_bytes(), expected);
    assert_eq!(restored.receipts().len(), 1);
    let receipt = &restored.receipts()[0];
    assert_eq!(serde_json::to_string(receipt).unwrap(), history[0]);
    assert_eq!(receipt.narration(), case["narration"].as_str().unwrap());
    assert!(!receipt.play().unwrap().fallback);
    assert_eq!(
        receipt.play().unwrap().policy,
        legacy_family(case).old_policy()
    );
    assert_eq!(
        receipt.play().unwrap().prompt_version,
        legacy_family(case).prompt()
    );
    restored
}

#[test]
fn genuine_old_receipts_keep_their_original_bytes_policies_prose_and_canonical_projection() {
    for case in legacy_cases() {
        let restored = restore_legacy(&case);
        let replayed = Engine::replay(restored.seed().clone(), restored.receipts()).unwrap();
        assert_eq!(replayed.canonical_bytes(), restored.canonical_bytes());
        assert_eq!(replayed.receipts(), restored.receipts());
        assert_eq!(
            serde_json::to_string(&replayed.receipts()[0]).unwrap(),
            case["receipt_json"].as_str().unwrap()
        );
    }
}

struct NoInference;
impl InferenceProvider for NoInference {
    fn poll(&mut self, _: &GenerationRequest, _: &Cancellation) -> Poll<Result<Vec<u8>, Error>> {
        panic!("An exact recorded retry must never request inference")
    }
}

#[test]
fn exact_legacy_retries_keep_old_acceptance_without_inference_or_policy_upgrade() {
    for case in legacy_cases() {
        let mut restored = restore_legacy(&case);
        let receipt = restored.receipts()[0].clone();
        let before = restored.canonical_bytes();
        assert_eq!(
            play::execute(
                &mut restored,
                receipt.request(),
                &mut NoInference,
                &Cancellation::default(),
                &profile()
            )
            .unwrap(),
            receipt
        );
        let mut matching_mode_trap = RecordingProvider::default();
        assert_eq!(
            execute(
                legacy_family(&case),
                &mut restored,
                receipt.request(),
                &mut matching_mode_trap,
                &Cancellation::default()
            )
            .unwrap(),
            receipt
        );
        assert!(matching_mode_trap.requests.is_empty());
        assert_eq!(restored.canonical_bytes(), before);
        assert_eq!(
            serde_json::to_string(&restored.receipts()[0]).unwrap(),
            case["receipt_json"].as_str().unwrap()
        );
    }
}

#[test]
fn genuine_legacy_acceptance_is_not_fresh_commit_authority_even_through_prepared_or_scene_paths() {
    for case in legacy_cases() {
        let restored = restore_legacy(&case);
        let receipt = &restored.receipts()[0];
        let record = receipt.play().unwrap();
        let family = legacy_family(&case);
        let mut fresh = Engine::new(restored.seed().clone()).unwrap();
        let before = fresh.canonical_bytes();
        assert!(
            fresh
                .commit_play(receipt.request(), receipt.proposal(), record)
                .is_err(),
            "{family:?}"
        );
        assert_eq!(fresh.canonical_bytes(), before);
        assert!(fresh.receipts().is_empty());
        assert!(fresh.commit_prepared(receipt).is_err(), "{family:?}");
        assert_eq!(fresh.canonical_bytes(), before);
        assert!(fresh.receipts().is_empty());
        let result = if family.scene() {
            let preparation = fresh
                .stage_scene_play_v1(receipt.request(), receipt.proposal(), &|| false)
                .unwrap();
            let recipe = if matches!(family, Family::SceneLiteral | Family::PresentedSceneLiteral) {
                SceneRecipeV1::LiteralV1
            } else {
                SceneRecipeV1::Memory(PlayContextPolicy::StateRelevantMemoryV1)
            };
            let bound = fresh
                .bind_scene_play_v1(preparation, recipe, &|| false)
                .unwrap();
            fresh.commit_scene_play_v1(bound, record, &|| false)
        } else {
            let stage = fresh
                .stage_play_v25(receipt.request(), receipt.proposal(), &|| false)
                .unwrap();
            match family {
                Family::Ordinary | Family::Memory => {
                    fresh.commit_staged_play_v25(stage, record, &|| false)
                }
                Family::Literal => fresh.commit_staged_literal_play_v1(stage, record, &|| false),
                Family::Presentation => {
                    fresh.commit_staged_presentation_play_v1(stage, record, &|| false)
                }
                Family::LiteralPresentation => {
                    fresh.commit_staged_literal_presentation_play_v1(stage, record, &|| false)
                }
                _ => unreachable!(),
            }
        };
        assert!(
            result.is_err(),
            "Old record accepted by a fresh staged commit: {family:?}"
        );
        assert_eq!(fresh.canonical_bytes(), before);
        assert!(fresh.receipts().is_empty());
    }
}

#[test]
fn new_policy_history_cannot_retain_a_tampered_prefix_as_if_it_were_genuine_legacy() {
    for family in FAMILIES {
        let (source, receipt) = resolved(
            family,
            "Mira",
            None,
            "You pass the potion to Mira with care.",
        );
        assert_eq!(receipt.play().unwrap().policy, family.strict_policy());
        let mut value = serde_json::to_value(&receipt).unwrap();
        let forged = "You pass the potion to Mir with care.";
        value["narration"] = json!(forged);
        value["play"]["narration"]["text"] = json!(forged);
        assert!(
            Engine::restore(
                source.seed().clone(),
                &[serde_json::to_string(&value).unwrap()]
            )
            .is_err(),
            "{family:?}"
        );
        let typed: play::PlayRecord = serde_json::from_value(value["play"].clone()).unwrap();
        let mut fresh = Engine::new(source.seed().clone()).unwrap();
        let before = fresh.canonical_bytes();
        assert!(
            fresh
                .commit_play(receipt.request(), receipt.proposal(), &typed)
                .is_err(),
            "{family:?}"
        );
        assert_eq!(fresh.canonical_bytes(), before);
        assert!(fresh.receipts().is_empty());
    }
}

fn original_world(family: Family) -> Engine {
    assert!(matches!(
        family,
        Family::Ordinary | Family::Memory | Family::Presentation
    ));
    let presentation = if family.presented() {
        StoryPresentationV1 {
            version: 1,
            tone: StoryTone::Warm,
            excluded_phrases: Vec::new(),
        }
    } else {
        StoryPresentationV1::default()
    };
    let input = InitialStoryInputV1 {
        version: 1,
        premise: "A surveyor reaches a quiet orchard.".into(),
        player_name: "Rae".into(),
        player_description: "A careful surveyor.".into(),
        cast: vec![InitialCastHintV1 {
            name: "Mira".into(),
            description: "An orchard keeper.".into(),
        }],
        profile: InitialRuleProfileV1::NarrativeV1,
        presentation,
    };
    let proposal = InitialWorldProposalV1 {
        version: 1,
        locations: vec![InitialLocationV1 {
            name: "Orchard".into(),
            description: "Copper markers hang beneath the trees.".into(),
        }],
        player_location: 0,
        characters: vec![InitialCharacterV1 {
            name: "Mira".into(),
            description: "A keeper waits by the gate.".into(),
            location: 0,
            known_by: vec![0, 1],
        }],
        routes: Vec::new(),
        facts: Vec::new(),
        beliefs: Vec::new(),
        possessions: vec![InitialPossessionV1 {
            name: "Potion".into(),
            description: "A small sealed bottle.".into(),
            owner: 0,
            return_to: None,
        }],
    };
    let response = serde_json::to_string(&proposal).unwrap();
    let origin = InitialWorldOriginV1 {
        version: 1,
        generation: InitialGenerationV1 {
            input: input.clone(),
            proposal: proposal.clone(),
            model_profile: profile().id.clone(),
            model_configuration: InitialModelConfigurationV1::from(&profile()),
            provider: InitialProviderKindV1::Scripted,
            prompt_version: locallore::story_authoring::PROMPT_VERSION.into(),
            schema_version: locallore::story_authoring::SCHEMA_VERSION.into(),
            response_sha256: format!("{:x}", Sha256::digest(response.as_bytes())),
            response,
        },
        reviewed: input,
        accepted: proposal,
        title: "The Orchard Survey".into(),
    };
    let seed = materialize(
        &origin,
        Scope {
            story: "source-words-original".into(),
            branch: "main".into(),
        },
    )
    .unwrap();
    assert_eq!(validate_origin(&seed), Ok(()));
    assert!(seed.initial_world.is_some());
    let engine = Engine::new(seed).unwrap();
    assert_eq!(engine.domain_version(), 2);
    engine
}

fn original_gift_request(source: &Engine) -> (Request, Command, String, String) {
    let item = source
        .state()
        .items
        .iter()
        .find(|(_, value)| value.owner == source.seed().player)
        .unwrap()
        .0
        .clone();
    let recipient = source
        .state()
        .actors
        .iter()
        .find(|(id, actor)| *id != &source.seed().player && actor.name == "Mira")
        .unwrap()
        .0
        .clone();
    let request = source.request(
        "original-world-source-word",
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: format!("I give {item} to {recipient}."),
        },
    );
    let command = Command::Give {
        item: item.clone(),
        to: recipient.clone(),
        quantity: 1,
    };
    (request, command, item, recipient)
}

#[test]
fn materialized_domain2_ordinary_memory_and_presentation_preserve_strict_generation_and_replay() {
    for family in [Family::Ordinary, Family::Memory, Family::Presentation] {
        for (text, expected_fallback) in [
            ("You pass the item to Mir with care.", true),
            ("You pass the item to Pot with care.", true),
            ("You pass the item to Mira with care.", false),
        ] {
            let mut source = original_world(family);
            let actors = source.state().actors.clone();
            let (request, command, item, recipient) = original_gift_request(&source);
            let mut provider = RecordingProvider::new(command.clone(), text);
            let receipt = execute(
                family,
                &mut source,
                &request,
                &mut provider,
                &Cancellation::default(),
            )
            .unwrap();
            assert_eq!(receipt.play().unwrap().policy, family.strict_policy());
            assert_eq!(receipt.play().unwrap().fallback, expected_fallback);
            if expected_fallback {
                assert_eq!(receipt.narration(), engine::render(receipt.events()));
            } else {
                assert_eq!(receipt.narration(), text);
            }
            assert_eq!(receipt.proposal().commands, vec![command]);
            assert_eq!(source.state().items[&item].owner, recipient);
            assert_eq!(source.state().actors, actors);
            assert_eq!(provider.requests.len(), 2);
            // Domain2 persists actual canonical envelopes, not fabricated v1 receipts.
            let records = source.canonical_records();
            assert_eq!(records.len(), 1);
            let history: Vec<_> = records
                .iter()
                .map(|record| serde_json::to_string(record).unwrap())
                .collect();
            assert_eq!(
                Engine::restore(source.seed().clone(), &history)
                    .unwrap()
                    .canonical_bytes(),
                source.canonical_bytes()
            );
            assert_eq!(
                Engine::replay_records(source.seed().clone(), records)
                    .unwrap()
                    .canonical_bytes(),
                source.canonical_bytes()
            );
            assert_eq!(
                execute(
                    family,
                    &mut source,
                    &request,
                    &mut provider,
                    &Cancellation::default()
                )
                .unwrap(),
                receipt
            );
            assert_eq!(provider.requests.len(), 2);
        }
    }
}

#[test]
fn materialized_domain2_cancellation_preserves_origin_ownership_and_empty_history() {
    for family in [Family::Ordinary, Family::Memory, Family::Presentation] {
        let mut source = original_world(family);
        let before = source.canonical_bytes();
        let seed = source.seed().clone();
        let (request, command, item, _) = original_gift_request(&source);
        let mut provider = RecordingProvider::new(command, "You pass the item to Mira with care.");
        provider.cancel_narrator = true;
        assert_eq!(
            execute(
                family,
                &mut source,
                &request,
                &mut provider,
                &Cancellation::default()
            ),
            Err(Error::Cancelled)
        );
        assert_eq!(provider.requests.len(), 2);
        assert_eq!(source.canonical_bytes(), before);
        assert_eq!(source.seed(), &seed);
        assert_eq!(source.state().items[&item].owner, source.seed().player);
        assert!(source.canonical_records().is_empty());
        assert!(source.receipts().is_empty());
    }
}

#[test]
fn double_ascii_curly_and_mixed_possessives_do_not_become_an_evidence_word() {
    for name in ["Potion's's", "Potion’s’s", "Potion's’s", "Potion’s's"] {
        fallback(
            Family::Ordinary,
            None,
            &format!("You pass the potion to {name} with care."),
        );
    }
}

#[test]
#[ignore = "Root-only one-shot genuine old-code fixture capture; never a normal test output"]
fn capture_genuine_legacy_source_word_receipts_once() {
    const OUTPUT: &str = "D:/Dev/Experiments/LocalLore/2026-10-30-narrator-grounding-v1/legacy-capture-v1/receipts-v1.json";
    let selected = std::env::var("B34_LEGACY_CAPTURE_PATH").expect("explicit Root capture path");
    assert_eq!(selected, OUTPUT, "no arbitrary output selection");
    assert!(Path::new(&selected).is_absolute());
    let mut cases = Vec::new();
    for family in FAMILIES {
        for text in [
            "You pass the potion to Mir with care.",
            "You pass the potion to Pot with care.",
        ] {
            let mut source = fixture(family, "Mira", None);
            let seed_json = serde_json::to_string(source.seed()).unwrap();
            let request = request(&source, false);
            let mut provider = RecordingProvider::new(gift(), text);
            let outcome = execute(
                family,
                &mut source,
                &request,
                &mut provider,
                &Cancellation::default(),
            );
            let value = match outcome {
                Ok(receipt) => {
                    assert_eq!(receipt.play().unwrap().policy, family.old_policy());
                    assert_eq!(receipt.play().unwrap().prompt_version, family.prompt());
                    json!({"family":format!("{family:?}"),"seed_json":seed_json,"narration":text,
                        "outcome":"accepted","fallback":receipt.play().unwrap().fallback,
                        "receipt_json":serde_json::to_string(&receipt).unwrap(),"canonical_after":source.canonical_bytes()})
                }
                Err(error) => {
                    json!({"family":format!("{family:?}"),"seed_json":seed_json,"narration":text,
                    "outcome":"refused","error":format!("{error:?}"),"receipt_json":null,
                    "canonical_after":source.canonical_bytes()})
                }
            };
            cases.push(value);
        }
    }
    let mut bytes = serde_json::to_vec_pretty(&json!({"version":1,"cases":cases})).unwrap();
    bytes.push(b'\n');
    assert!(bytes.len() < 1024 * 1024);
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&selected)
        .unwrap();
    file.write_all(&bytes).unwrap();
    file.sync_all().unwrap();
}
