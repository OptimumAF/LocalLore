// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Vendor grammar bugs do not grant permission to replace the player's speech.
use locallore::{
    contracts::*,
    engine::Engine,
    inference::{Cancellation, GenerationRequest, InferenceProvider},
    play::{self, PlayProfile},
};
use serde_json::{json, Value};
use std::{collections::VecDeque, task::Poll};

fn seed() -> Seed {
    serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap()
}
fn cases() -> Vec<(String, String)> {
    let corpus: Value = serde_json::from_str(include_str!(
        "../../../fixtures/llguidance_literal_regressions.json"
    ))
    .unwrap();
    corpus["cases"]
        .as_array()
        .unwrap()
        .iter()
        .map(|case| {
            let full: String =
                serde_json::from_str(case["positives"][0]["json"].as_str().unwrap()).unwrap();
            let short: String =
                serde_json::from_str(case["negatives"][0]["json"].as_str().unwrap()).unwrap();
            assert_ne!(full, short);
            (full, short)
        })
        .collect()
}
fn profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-literal-regression".into(),
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
struct Script {
    outputs: VecDeque<Value>,
    calls: usize,
}
impl InferenceProvider for Script {
    fn poll(&mut self, _: &GenerationRequest, _: &Cancellation) -> Poll<Result<Vec<u8>, Error>> {
        self.calls += 1;
        Poll::Ready(
            self.outputs
                .pop_front()
                .ok_or(Error::Provider)
                .and_then(|v| serde_json::to_vec(&v).map_err(|_| Error::Provider)),
        )
    }
}
fn say(text: &str) -> Value {
    json!({"commands":[{"op":"say","text":text,"audience":["mira"]}]})
}

#[test]
fn vendor_truncated_speech_is_rejected_before_narration_or_canonical_mutation() {
    for (full, short) in cases() {
        let mut engine = Engine::new(seed()).unwrap();
        let before = engine.canonical_bytes();
        let request = engine.request(
            "literal-truncation",
            Intent::FreeText {
                kind: PlayInputKind::Dialogue,
                text: full,
            },
        );
        let mut provider = Script {
            outputs: VecDeque::from([say(&short)]),
            calls: 0,
        };
        assert_eq!(
            play::execute(
                &mut engine,
                &request,
                &mut provider,
                &Cancellation::default(),
                &profile()
            ),
            Err(Error::Agency)
        );
        assert_eq!(provider.calls, 1);
        assert_eq!(engine.canonical_bytes(), before);
        assert_eq!(engine.revision(), 0);
        assert!(engine.receipts().is_empty());
    }
}

#[test]
fn full_original_literals_commit_and_replay_without_vendor_or_model_authority() {
    for (full, _) in cases() {
        let mut engine = Engine::new(seed()).unwrap();
        let request = engine.request(
            "literal-original",
            Intent::FreeText {
                kind: PlayInputKind::Dialogue,
                text: full.clone(),
            },
        );
        let mut provider = Script {
            outputs: VecDeque::from([
                say(&full),
                // Deliberately ungrounded original fixture exercises the existing safe fallback.
                json!({"text":"Sable knows SECRET-TIDE-731.","event_ids":[1],"speaker":"narrator"}),
            ]),
            calls: 0,
        };
        let receipt = play::execute(
            &mut engine,
            &request,
            &mut provider,
            &Cancellation::default(),
            &profile(),
        )
        .unwrap();
        assert_eq!(provider.calls, 2);
        assert_eq!(engine.revision(), 1);
        assert_eq!(engine.receipts().len(), 1);
        assert_eq!(
            receipt.proposal().commands,
            vec![Command::Say {
                text: full,
                audience: ["mira".into()].into(),
            }]
        );
        assert!(receipt.play().unwrap().fallback);
        assert!(!receipt.narration().contains("SECRET-TIDE-731"));
        assert_eq!(
            Engine::replay(seed(), engine.receipts())
                .unwrap()
                .canonical_bytes(),
            engine.canonical_bytes()
        );
    }
}
