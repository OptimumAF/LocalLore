// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Public play regressions with recording synthetic inference, not model-quality evidence.
use locallore::{
    contracts::*,
    engine::{self, Engine},
    inference::*,
    play::{self, PlayProfile},
};
use serde_json::json;
use std::{collections::VecDeque, task::Poll};

fn fixture(visible_name: &str, offscreen_name: &str) -> Engine {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    seed.actors.get_mut("mira").unwrap().name = visible_name.into();
    seed.actors.get_mut("oren").unwrap().name = offscreen_name.into();
    seed.actors.get_mut("sable").unwrap().name = "Hidden Rowan".into();
    Engine::new(seed).unwrap()
}

fn profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-visible-names".into(),
        model_sha256: "a".repeat(64),
        runtime_revision: "b".repeat(40),
        template_sha256: "c".repeat(64),
        worker_sha256: "d".repeat(64),
        profile_manifest_sha256: "e".repeat(64),
        context_tokens: 4096,
        director_tokens: 350,
        narrator_tokens: 220,
        deadline_ms: 1000,
        repair_limit: 1,
    }
}

struct RecordingProvider {
    replies: VecDeque<Vec<u8>>,
    requests: Vec<GenerationRequest>,
    cancel_narrator: bool,
}

impl RecordingProvider {
    fn gift(text: &str) -> Self {
        let values = [
            json!({"commands":[{"op":"give","item":"potion","to":"mira","quantity":1}]}),
            json!({"text":text,"event_ids":[1],"speaker":"narrator"}),
        ];
        Self {
            replies: values
                .into_iter()
                .map(|value| serde_json::to_vec(&value).unwrap())
                .collect(),
            requests: Vec::new(),
            cancel_narrator: false,
        }
    }
}

impl InferenceProvider for RecordingProvider {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        cancellation: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        self.requests.push(request.clone());
        if self.cancel_narrator
            && matches!(&request.input, Input::Structured { role, .. } if role == "narrator")
        {
            cancellation.cancel();
        }
        Poll::Ready(self.replies.pop_front().ok_or(Error::Provider))
    }
}

fn request(source: &Engine) -> Request {
    source.request(
        "visible-name-gift",
        Intent::FreeText {
            kind: PlayInputKind::Action,
            // Deliberately use the canonical ID: display words are not in the
            // player's request or the engine's mechanical outcome narration.
            text: "I give potion to mira.".into(),
        },
    )
}

fn resolved(visible_name: &str, offscreen_name: &str, text: &str) -> (Engine, Receipt) {
    let mut source = fixture(visible_name, offscreen_name);
    let before = source.clone();
    let request = request(&source);
    let mut provider = RecordingProvider::gift(text);
    let receipt = play::execute(
        &mut source,
        &request,
        &mut provider,
        &Cancellation::default(),
        &profile(),
    )
    .unwrap();
    assert_eq!(provider.requests.len(), 2);
    assert!(provider.replies.is_empty());
    assert_eq!(receipt.request(), &request);
    assert_eq!(
        serde_json::to_value(receipt.proposal()).unwrap()["commands"],
        json!([{"op":"give","item":"potion","to":"mira","quantity":1}])
    );
    assert_eq!(source.state().items["potion"].owner, "mira");
    assert_eq!(source.state().items["potion"].quantity, 1);
    assert_eq!(source.state().actors, before.state().actors);
    assert_eq!(source.state().items.len(), before.state().items.len());
    assert_eq!(receipt.events().len(), 1);
    // Both generated and fallback receipts must preserve real replay and exact
    // retry semantics, with no third inference call.
    let history = vec![serde_json::to_string(&receipt).unwrap()];
    let restored = Engine::restore(source.seed().clone(), &history).unwrap();
    assert_eq!(restored.canonical_bytes(), source.canonical_bytes());
    let replayed = Engine::replay(source.seed().clone(), std::slice::from_ref(&receipt)).unwrap();
    assert_eq!(replayed.canonical_bytes(), source.canonical_bytes());
    assert_eq!(
        play::execute(
            &mut source,
            &request,
            &mut provider,
            &Cancellation::default(),
            &profile(),
        )
        .unwrap(),
        receipt
    );
    assert_eq!(provider.requests.len(), 2);
    let mut changed = request.clone();
    if let Intent::FreeText { text, .. } = &mut changed.intent {
        *text = "I keep the potion.".into();
    }
    assert_eq!(
        play::execute(
            &mut source,
            &changed,
            &mut provider,
            &Cancellation::default(),
            &profile(),
        ),
        Err(Error::RetryMismatch)
    );
    assert_eq!(provider.requests.len(), 2);
    (source, receipt)
}

fn generated(visible_name: &str, offscreen_name: &str, text: &str) {
    let (_, receipt) = resolved(visible_name, offscreen_name, text);
    assert!(
        !receipt.play().unwrap().fallback,
        "faithful visible label: {text:?}"
    );
    assert_eq!(receipt.narration(), text);
    assert_ne!(receipt.narration(), engine::render(receipt.events()));
}

fn fallback(visible_name: &str, offscreen_name: &str, text: &str) {
    let (_, receipt) = resolved(visible_name, offscreen_name, text);
    assert!(
        receipt.play().unwrap().fallback,
        "unsupported name: {text:?}"
    );
    assert_eq!(receipt.narration(), engine::render(receipt.events()));
}

#[test]
fn faithful_multiword_display_name_keeps_exact_generated_prose_and_id_mechanics() {
    generated(
        "Sera Vale",
        "Hidden Finch",
        "You pass the potion to Sera Vale with care.",
    );
}

#[test]
fn full_visible_name_accepts_ascii_and_curly_possessives_without_component_aliases() {
    for text in [
        "You place the potion in Sera Vale's waiting hand.",
        "You place the potion in Sera Vale’s waiting hand.",
        "You pass the potion to (Sera Vale).",
    ] {
        generated("Sera Vale", "Hidden Finch", text);
    }
}

#[test]
fn unicode_visible_name_is_grounded_without_replacing_its_recorded_spelling() {
    generated(
        "Éira Núñez",
        "Hidden Finch",
        "You place the potion in Éira Núñez’s waiting hand.",
    );
}

#[test]
fn exact_visible_full_name_is_not_hidden_by_an_offscreen_actor_with_the_same_label() {
    generated(
        "Sera Vale",
        "Sera Vale",
        "You pass the potion to Sera Vale with care.",
    );
}

#[test]
fn full_visible_occurrence_is_not_a_disclosure_of_an_offscreen_component_name() {
    for hidden in ["Sera", "Vale"] {
        generated(
            "Sera Vale",
            hidden,
            "You place the potion in Sera Vale's waiting hand.",
        );
    }
}

#[test]
fn fragments_stitched_names_and_full_name_prefixes_or_suffixes_stay_unapproved() {
    for text in [
        "You pass the potion to Sera.",
        "You pass the potion to Vale.",
        "You pass the potion to Sera Rune.",
        "You pass the potion to XSera Vale.",
        "You pass the potion to Sera Valehaven.",
        "You pass the potion to Sera Vale-Junior.",
        "You pass the potion to Sera Vale_2.",
        "You pass the potion to Sera Vale2.",
        "You place the potion in Sera Vale'son waiting hand.",
        "You pass the potion to Sera Vale and Nara Reed.",
    ] {
        fallback("Sera Vale", "Hidden Finch", text);
    }
}

#[test]
fn an_approved_full_occurrence_does_not_whitelist_components_elsewhere_or_hidden_ids() {
    for text in [
        "You pass the potion to Sera Vale. Sera waits nearby.",
        "You pass the potion to Sera Vale with Vale nearby.",
        "You pass the potion to Sera Vale while oren watches.",
        "You pass the potion to Sera Vale while sable watches.",
        "You pass the potion to Sera Vale while Hidden Finch watches.",
    ] {
        fallback("Sera Vale", "Hidden Finch", text);
    }
    for hidden in ["Sera", "Vale"] {
        let text = format!("You pass the potion to Sera Vale while {hidden} watches.");
        fallback("Sera Vale", hidden, &text);
    }
}

#[test]
fn cancellation_during_faithful_name_narration_never_commits_a_transfer_or_receipt() {
    let mut source = fixture("Sera Vale", "Hidden Finch");
    let before = source.canonical_bytes();
    let request = request(&source);
    let mut provider = RecordingProvider::gift("You pass the potion to Sera Vale with care.");
    provider.cancel_narrator = true;
    assert_eq!(
        play::execute(
            &mut source,
            &request,
            &mut provider,
            &Cancellation::default(),
            &profile(),
        ),
        Err(Error::Cancelled)
    );
    assert_eq!(provider.requests.len(), 2);
    assert_eq!(source.canonical_bytes(), before);
    assert_eq!(source.state().items["potion"].owner, "player");
    assert!(source.receipts().is_empty());
}

#[test]
fn apostrophe_extended_words_cannot_hide_offscreen_name_components_inside_a_full_alias() {
    for hidden in ["Sera", "Vale"] {
        for text in [
            "You pass the potion to sera vale'son.",
            "You pass the potion to sera vale’son.",
            "You pass the potion to o'sera vale.",
            "You pass the potion to o’sera vale.",
            "You pass the potion to Sera Vale'son.",
            "You pass the potion to Sera Vale’son.",
            "You pass the potion to O'Sera Vale.",
            "You pass the potion to O’Sera Vale.",
        ] {
            fallback("Sera Vale", hidden, text);
        }
    }
}

#[test]
fn unicode_case_expansion_preserves_full_alias_coordinates_at_later_occurrences() {
    generated(
        "İpek Arden",
        "Arden",
        "You pass the potion to İpek Arden; İpek Arden’s waiting hand is steady.",
    );
}
