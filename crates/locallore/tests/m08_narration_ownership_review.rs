// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent synthetic-pipeline regressions; initially UNCOMPILED/UNRUN.
//! Exact observed model prose is retained, not repaired/replaced in the fixture.
use locallore::{
    contracts::*,
    engine::{self, Engine},
    inference::*,
    inspection::sha256,
    play::{self, PlayProfile},
};
use serde_json::{json, Value};
use std::{collections::VecDeque, task::Poll};

const OBSERVED: &str = "I gave a small bottle of potion to mira. The potion was warm and felt like it had magic in it. I didn’t know what happened next, but I took the potion with me.";
fn fixture(item: &str) -> Engine {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    if item != "potion" {
        let actual = seed.items.remove("potion").unwrap();
        assert!(seed.items.insert(item.into(), actual).is_none());
    }
    Engine::new(seed).unwrap()
}
fn profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-ownership-review".into(),
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
fn execute(
    engine: &mut Engine,
    request: &Request,
    command: &Command,
    prose: &str,
) -> (Receipt, ScriptFakeProvider) {
    let mut provider = ScriptFakeProvider {
        replies: [
            json!({"commands":[command]}),
            json!({"text":prose,"event_ids":[1],"speaker":"narrator"}),
        ]
        .into_iter()
        .map(|v| serde_json::to_vec(&v).unwrap())
        .collect(),
        seen: vec![],
    };
    let receipt = play::execute(
        engine,
        request,
        &mut provider,
        &Cancellation::default(),
        &profile(),
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
    assert!(provider.replies.is_empty());
    assert_eq!(receipt.play().unwrap().policy, "grounded-prose-v2.2");
    assert_eq!(
        receipt.play().unwrap().prompt_version,
        "locallore-play-v2.5"
    );
    assert_eq!(receipt.request(), request);
    assert_eq!(receipt.events().len(), 1);
    assert_eq!(engine.revision(), 1);
    assert_eq!(engine.canonical_record_count(), 1);
    (receipt, provider)
}
fn give(item: &str, prose: &str, fallback: bool) {
    let mut actual = fixture(item);
    let mut expected = actual.clone();
    let command = Command::Give {
        item: item.into(),
        to: "mira".into(),
        quantity: 1,
    };
    // The independent mechanical expectation uses the actual Core typed path,
    // not a duplicate rules evaluator or a forged accepted Receipt.
    let typed = expected.request("ownership", Intent::Actions(vec![command.clone()]));
    let proposal = Engine::proposal(&typed).unwrap();
    let approved = expected.preview(&typed, &proposal).unwrap();
    expected.commit_prepared(&approved).unwrap();
    let request = actual.request(
        "ownership",
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: format!("I give {item} to Mira."),
        },
    );
    let (receipt, _) = execute(&mut actual, &request, &command, prose);
    assert_eq!(actual.state().items[item].owner, "mira");
    assert!(!actual
        .state()
        .items
        .iter()
        .any(|(id, value)| id == item && value.owner == "player"));
    assert_eq!(actual.canonical_bytes(), expected.canonical_bytes());
    assert_eq!(receipt.events(), approved.events());
    assert_eq!(receipt.play().unwrap().fallback, fallback, "{prose}");
    if fallback {
        assert_eq!(receipt.narration(), engine::render(receipt.events()));
        assert_ne!(receipt.narration(), prose);
    } else {
        assert_eq!(receipt.narration(), prose);
    }
    let strings: Vec<_> = actual
        .canonical_records()
        .iter()
        .map(|r| serde_json::to_string(r).unwrap())
        .collect();
    let restored = Engine::restore(actual.seed().clone(), &strings).unwrap();
    assert_eq!(restored.canonical_records(), actual.canonical_records());
    let mut no_provider = ScriptFakeProvider::default();
    assert_eq!(
        play::execute(
            &mut actual,
            &request,
            &mut no_provider,
            &Cancellation::default(),
            &profile()
        )
        .unwrap(),
        receipt
    );
    assert!(no_provider.seen.is_empty());
    assert_eq!(actual.canonical_record_count(), 1);
}

#[test]
fn exact_observed_post_give_possession_contradiction_uses_mechanical_fallback() {
    give("potion", OBSERVED, true);
}

#[test]
fn first_person_kept_carried_and_with_me_claims_cannot_reverse_the_given_item() {
    // A second original synthetic seed item ID prevents a potion-only phrase fix.
    for item in ["potion", "vial"] {
        for prose in [
            format!("I kept the {item}."),
            format!("I carried the {item} with me."),
            format!("The {item} remained with me."),
            format!("I took the {item} with me."),
        ] {
            give(item, &prose, true);
        }
    }
}

#[test]
fn grounded_recipient_ownership_prose_remains_displayed_without_fallback() {
    give("potion", "Mira now holds the potion.", false);
}

#[test]
fn literal_player_dialogue_is_preserved_and_not_treated_as_transfer_narration() {
    let mut actual = fixture("potion");
    let text = "I kept the potion with me.";
    let request = actual.request(
        "literal-ownership",
        Intent::FreeText {
            kind: PlayInputKind::Dialogue,
            text: text.into(),
        },
    );
    let command = Command::Say {
        text: text.into(),
        audience: ["mira".into()].into_iter().collect(),
    };
    let (receipt, provider) = execute(
        &mut actual,
        &request,
        &command,
        "You speak quietly to your listener.",
    );
    assert_eq!(actual.state().items["potion"].owner, "player");
    assert!(!receipt.play().unwrap().fallback);
    let effect = serde_json::to_value(receipt.events()[0].outcome()).unwrap();
    assert_eq!(effect["effect"], "said");
    assert_eq!(effect["text"], text);
    assert!(
        matches!(&receipt.request().intent, Intent::FreeText { kind: PlayInputKind::Dialogue, text: original } if original == text)
    );
    let Input::Structured { prompt, .. } = &provider.seen[1].input else {
        panic!("narrator")
    };
    assert!(!prompt.contains(text));
}

#[test]
fn original_21_through_24_fixture_hashes_and_zero_provider_replay_remain_unchanged() {
    for (text, hash) in [
        (
            include_str!("fixtures/accepted_play_v2_1.json"),
            "3aefb5a8c1a9ad0f27b15d424dfcecf5f7fb58a639572758a6128fb75ace36d4",
        ),
        (
            include_str!("fixtures/accepted_play_v2_2.json"),
            "f3645af4047e02b827010134cb57b1d974c86538b68ebf8e43801ea8bcde8f3d",
        ),
        (
            include_str!("fixtures/accepted_play_v2_3.json"),
            "57fb218ef2f9a50842f77c2c87cd7e694ca53ea064c6205cfef18abd9e51035c",
        ),
        (
            include_str!("fixtures/accepted_play_v2_4.json"),
            "f08801ab9ce13e0bb47434896dafa1e8e671fa4f4a239731cbd2ee0f42730e2d",
        ),
    ] {
        assert_eq!(sha256(text.as_bytes()), hash);
        let fixture: Value = serde_json::from_str(text).unwrap();
        let seed: Seed = serde_json::from_value(fixture["seed"].clone()).unwrap();
        let mut restored = Engine::restore(seed, &[fixture["receipt"].to_string()]).unwrap();
        let receipt = restored.receipts()[0].clone();
        assert_eq!(serde_json::to_value(&receipt).unwrap(), fixture["receipt"]);
        if receipt.play().unwrap().prompt_version == "locallore-play-v2.4" {
            let bytes = serde_json::to_vec(&receipt).unwrap();
            assert_eq!(
                bytes,
                include_bytes!("fixtures/accepted_play_v2_4_receipt.json")
            );
            assert_eq!(
                sha256(&bytes),
                "38dcf7329addf4ed98fd984cdb9eac95f8d078be03bf4633dd7082d23ac4bc3f"
            );
            assert_eq!(
                sha256(&serde_json::to_vec(receipt.play().unwrap()).unwrap()),
                "6ed4abcd325e14fa334d23ead9b843ebe93afd91e26b28e3167ad95e552b9341"
            );
        }
        let basis = restored.accepted_history_basis().unwrap();
        let mut no_provider = ScriptFakeProvider::default();
        let cancel = Cancellation::default();
        cancel.cancel();
        assert_eq!(
            play::execute(
                &mut restored,
                receipt.request(),
                &mut no_provider,
                &cancel,
                &profile()
            )
            .unwrap(),
            receipt
        );
        assert!(no_provider.seen.is_empty());
        assert_eq!(restored.accepted_history_basis().unwrap(), basis);
    }
}
