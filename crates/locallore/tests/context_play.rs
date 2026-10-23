//! Actual production context/commit/replay paths with synthetic provider input capture.
use locallore::{
    contracts::*,
    engine::Engine,
    inference::*,
    play::{self, PlayProfile},
};
use serde_json::{json, Value};
use std::task::Poll;

fn seed() -> Seed {
    serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap()
}
fn profile() -> PlayProfile {
    PlayProfile {
        id: "context-test".into(),
        model_sha256: "a".repeat(64),
        runtime_revision: "b".repeat(40),
        template_sha256: "c".repeat(64),
        worker_sha256: "d".repeat(64),
        profile_manifest_sha256: "e".repeat(64),
        context_tokens: 4096,
        director_tokens: 350,
        narrator_tokens: 220,
        deadline_ms: 5000,
        repair_limit: 1,
    }
}
#[derive(Default)]
struct Captured {
    calls: usize,
    director: String,
}
impl InferenceProvider for Captured {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        _: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        self.calls += 1;
        let Input::Structured { role, prompt, .. } = &request.input else {
            panic!("production structured input")
        };
        let value = if role == "director" {
            self.director = prompt.clone();
            json!({"commands":[{"op":"wait","ticks":1}]})
        } else {
            json!({"text":"Rain falls on the quay.","event_ids":[request.revision+1],"speaker":"narrator"})
        };
        Poll::Ready(Ok(serde_json::to_vec(&value).unwrap()))
    }
}
fn commit(e: &mut Engine, turn: &str, command: Command) {
    let request = e.request(turn, Intent::Actions(vec![command]));
    let proposal = Engine::proposal(&request).unwrap();
    let approved = e.preview(&request, &proposal).unwrap();
    e.commit(&request, &proposal, approved.narration()).unwrap();
}

#[test]
fn production_director_receives_old_commitment_and_selected_evidence_not_full_history_or_secrets() {
    let mut s = seed();
    s.facts.insert(
        "private-memory".into(),
        Fact {
            proposition: "HIDDEN_MEMORY_CANARY_771".into(),
            discoverable_at: None,
            known_by: ["sable".into()].into(),
        },
    );
    let mut e = Engine::new(s).unwrap();
    commit(
        &mut e,
        "old-promise",
        Command::Promise {
            id: "beacon-duty".into(),
            to: "mira".into(),
            terms: "Keep the ancient beacon promise alive.".into(),
            deadline: 5000,
            return_item: None,
        },
    );
    commit(
        &mut e,
        "old-transfer",
        Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 1,
        },
    );
    for index in 0..1024 {
        commit(
            &mut e,
            &format!("distractor-{index:04}"),
            Command::Wait { ticks: 1 },
        );
    }
    let before = e.canonical_bytes();
    let request = e.request(
        "compiled-play",
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: "I wait for one tide tick.".into(),
        },
    );
    let mut candidate = e.clone();
    let mut provider = Captured::default();
    let receipt = play::execute(
        &mut candidate,
        &request,
        &mut provider,
        &Cancellation::default(),
        &profile(),
    )
    .unwrap();
    assert_eq!(provider.calls, 2);
    assert!(provider
        .director
        .contains("Keep the ancient beacon promise alive."));
    assert!(provider.director.contains("beacon-duty"));
    assert!(!provider.director.contains("HIDDEN_MEMORY_CANARY_771"));
    assert!(!provider.director.contains("private-memory"));
    assert!(!provider.director.contains("distractor-0001"));
    assert!(!provider.director.contains("omitted_eligible"));
    assert!(provider.director.len() < 24_576);
    assert_eq!(
        e.canonical_bytes(),
        before,
        "preparation changes only the candidate clone"
    );
    assert_eq!(receipt.play().unwrap().prompt_version, play::PROMPT_VERSION);
    let rebuilt = Engine::replay(candidate.seed().clone(), candidate.receipts()).unwrap();
    assert_eq!(rebuilt.canonical_bytes(), candidate.canonical_bytes());
}

#[test]
fn mandatory_context_budget_stops_before_provider_and_preserves_state() {
    let mut e = Engine::new(seed()).unwrap();
    let before = e.canonical_bytes();
    let request = e.request(
        "too-small-context",
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: "I wait for one tide tick.".into(),
        },
    );
    let mut limits = profile();
    limits.context_tokens = 512;
    let mut provider = Captured::default();
    assert_eq!(
        play::execute(
            &mut e,
            &request,
            &mut provider,
            &Cancellation::default(),
            &limits
        ),
        Err(Error::TooLarge)
    );
    assert_eq!(provider.calls, 0);
    assert_eq!(e.canonical_bytes(), before);
}

#[test]
fn exact_accepted_main_v21_receipt_restores_replays_and_retries_but_cannot_be_a_new_prepared_commit(
) {
    let fixture: Value =
        serde_json::from_str(include_str!("fixtures/accepted_play_v2_1.json")).unwrap();
    assert_eq!(
        fixture["source_commit"],
        "dd3de5739ced38af7d67cd7354bd7136798a0b63"
    );
    let seed: Seed = serde_json::from_value(fixture["seed"].clone()).unwrap();
    let encoded = serde_json::to_string(&fixture["receipt"]).unwrap();
    let restored = Engine::restore(seed.clone(), &[encoded]).unwrap();
    let receipt = &restored.receipts()[0];
    assert_eq!(serde_json::to_value(receipt).unwrap(), fixture["receipt"]);
    assert_eq!(
        receipt.play().unwrap().prompt_version,
        play::RECORDED_PROMPT_VERSION
    );
    assert_eq!(
        Engine::replay(seed.clone(), restored.receipts())
            .unwrap()
            .canonical_bytes(),
        restored.canonical_bytes()
    );
    assert_eq!(
        restored.recorded(receipt.request()).unwrap().as_ref(),
        Some(receipt)
    );
    let child = restored.fork("legacy-child", restored.revision()).unwrap();
    assert_eq!(child.scope().branch, "legacy-child");
    assert_eq!(child.revision(), restored.revision());
    assert_eq!(child.state(), restored.state());
    assert_eq!(child.receipts(), restored.receipts());
    let mut fresh = Engine::new(seed).unwrap();
    let before = fresh.canonical_bytes();
    assert_eq!(fresh.commit_prepared(receipt), Err(Error::Narration));
    assert_eq!(fresh.canonical_bytes(), before);
    let mut forged = fixture["receipt"].clone();
    forged["play"]["prompt_version"] = json!("locallore-play-v2.0");
    assert_eq!(
        Engine::restore(fresh.seed().clone(), &[forged.to_string()]).err(),
        Some(Error::CorruptHistory)
    );
}
