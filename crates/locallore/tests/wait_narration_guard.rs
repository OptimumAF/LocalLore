// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Fresh ordinary narration checks for time-only events.
use locallore::{
    contracts::{Command, Effect, Error, PlayInputKind, Receipt, Seed},
    engine::{self, Engine},
    inference::{Cancellation, GenerationRequest, InferenceProvider, Input},
    play::{self, PlayProfile},
};
use serde_json::json;
use std::{collections::VecDeque, task::Poll};

const LISTENER_CLAIM: &str = "You hear me as the listener.";
const WAIT: &str = "I wait for one tide tick.";

fn seed() -> Seed {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    seed.scope.story = "real-synthetic-scene-wait".into();
    seed
}

fn profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-wait-narration-review".into(),
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
    roles: Vec<String>,
}

impl InferenceProvider for Script {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        _: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        let Input::Structured { role, .. } = &request.input else {
            panic!("expected the actual structured Play pipeline");
        };
        self.roles.push(role.clone());
        Poll::Ready(self.replies.pop_front().ok_or(Error::Provider))
    }
}

fn execute(kind: PlayInputKind, text: &str, command: Command, prose: &str) -> Receipt {
    let mut engine = Engine::new(seed()).unwrap();
    let request = engine.request(
        "wait",
        locallore::contracts::Intent::FreeText {
            kind,
            text: text.into(),
        },
    );
    let mut script = Script {
        replies: [
            json!({"commands": [command]}),
            json!({"text": prose, "event_ids": [1], "speaker": "narrator"}),
        ]
        .into_iter()
        .map(|value| serde_json::to_vec(&value).unwrap())
        .collect(),
        roles: vec![],
    };
    let receipt = play::execute(
        &mut engine,
        &request,
        &mut script,
        &Cancellation::default(),
        &profile(),
    )
    .unwrap();
    assert_eq!(script.roles, ["director", "narrator"]);
    assert!(script.replies.is_empty());
    assert_eq!(receipt.request(), &request);
    assert_eq!(engine.revision(), 1);
    assert_eq!(receipt.events().len(), 1);
    receipt
}

#[test]
fn fresh_time_only_turn_falls_back_from_unsupported_listener_claim() {
    let receipt = execute(
        PlayInputKind::Action,
        WAIT,
        Command::Wait { ticks: 1 },
        LISTENER_CLAIM,
    );
    assert_eq!(
        receipt.events()[0].outcome(),
        &Effect::TimeAdvanced { from: 100, to: 101 }
    );
    assert!(
        receipt.play().unwrap().fallback,
        "time-only narration unexpectedly retained a listener claim"
    );
    assert_eq!(receipt.narration(), engine::render(receipt.events()));
}

#[test]
fn grounded_wait_prose_is_accepted() {
    for prose in [
        "You wait as the moment passes.",
        "You hear the tide while you wait.",
    ] {
        let receipt = execute(
            PlayInputKind::Action,
            WAIT,
            Command::Wait { ticks: 1 },
            prose,
        );
        assert!(!receipt.play().unwrap().fallback);
        assert_eq!(receipt.narration(), prose);
    }
}

#[test]
fn approved_dialogue_can_acknowledge_a_listener() {
    let text = "The signal is ready.";
    let prose = "You delivered your message to the listeners.";
    let receipt = execute(
        PlayInputKind::Dialogue,
        text,
        Command::Say {
            text: text.into(),
            audience: ["mira".into()].into_iter().collect(),
        },
        prose,
    );
    assert!(
        matches!(receipt.events()[0].outcome(), Effect::Said(claim) if claim.audience.contains("mira"))
    );
    assert!(!receipt.play().unwrap().fallback);
    assert_eq!(receipt.narration(), prose);
}
