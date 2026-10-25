// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Synthetic wire bytes cross the real parser/intent/Engine boundary; no tokenizer or SDK.
use locallore::{
    contracts::*,
    engine::Engine,
    inference::{Cancellation, GenerationRequest, InferenceProvider, Input},
    play::{self, PlayProfile},
};
use std::{collections::VecDeque, task::Poll};

const SPEECH: &str = "Mira, snow 雪 and stars 😀.";

fn seed() -> Seed {
    serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap()
}

fn profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-json-spelling".into(),
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
    replies: VecDeque<Vec<u8>>,
    seen: Vec<GenerationRequest>,
}

impl InferenceProvider for Script {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        _: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        self.seen.push(request.clone());
        Poll::Ready(self.replies.pop_front().ok_or(Error::Provider))
    }
}

fn director(spelling: &str, audience: &str) -> Vec<u8> {
    // Keep authored JSON string spellings intact instead of reserializing them through Value.
    format!(r#"{{"commands":[{{"op":"say","text":{spelling},"audience":[{audience}]}}]}}"#)
        .into_bytes()
}

fn dialogue(engine: &Engine, text: &str) -> Request {
    engine.request(
        "json-spelling",
        Intent::FreeText {
            kind: PlayInputKind::Dialogue,
            text: text.into(),
        },
    )
}

fn commits_exact_speech(text: &str, spelling: &str) -> Vec<u8> {
    let mut engine = Engine::new(seed()).unwrap();
    let before = engine.canonical_bytes();
    let request = dialogue(&engine, text);
    let proposal_wire = format!(
        r#"{{"version":1,"scope":{{"story":"quay","branch":"main"}},"turn":"json-spelling","expected_revision":0,"commands":[{{"op":"say","text":{spelling},"audience":["mira"]}}]}}"#
    );
    let parsed = Proposal::parse(proposal_wire.as_bytes()).unwrap();
    let preview = engine.preview(&request, &parsed).unwrap();
    assert_eq!(engine.canonical_bytes(), before);
    assert!(engine.receipts().is_empty());
    assert_eq!(
        parsed.commands,
        vec![Command::Say {
            text: text.into(),
            audience: ["mira".into()].into(),
        }]
    );

    let mut script = Script {
        replies: VecDeque::from([
            director(spelling, r#""mira""#),
            // Existing grounded fallback prevents this unobserved secret from entering narration.
            br#"{"text":"Sable knows SECRET-TIDE-731.","event_ids":[1],"speaker":"narrator"}"#
                .to_vec(),
        ]),
        seen: vec![],
    };
    let receipt = play::execute(
        &mut engine,
        &request,
        &mut script,
        &Cancellation::default(),
        &profile(),
    )
    .unwrap();
    assert_eq!(receipt.request(), &request);
    assert_eq!(receipt.proposal(), &parsed);
    assert_eq!(receipt.events(), preview.events());
    assert_eq!(engine.revision(), 1);
    assert_eq!(engine.receipts().len(), 1);
    assert_eq!(engine.state().claims.len(), 1);
    assert_eq!(engine.state().claims[0].text, text);
    assert_eq!(receipt.play().unwrap().repairs, 0);
    assert!(receipt.play().unwrap().fallback);
    assert!(!receipt.narration().contains("SECRET-TIDE-731"));
    assert_eq!(receipt.events().len(), 1);
    let Effect::Said(claim) = receipt.events()[0].outcome() else {
        panic!("Only the original speech may become canonical")
    };
    assert_eq!(claim.text, text);
    assert_eq!(claim.audience, ["mira".into()].into());
    assert!(receipt.events()[0].witnesses().contains("mira"));
    assert!(!receipt.events()[0].witnesses().contains("sable"));
    for observer in ["player", "mira", "sable"] {
        let context = engine
            .character_context(observer, engine.scope(), 1)
            .unwrap();
        let heard = context
            .observations
            .iter()
            .any(|event| matches!(event.outcome(), Effect::Said(claim) if claim.text == text));
        assert_eq!(heard, observer != "sable");
    }
    let replayed = Engine::replay(seed(), engine.receipts()).unwrap();
    assert_eq!(replayed.canonical_bytes(), engine.canonical_bytes());
    let history = vec![serde_json::to_string(&receipt).unwrap()];
    assert_eq!(
        Engine::restore(seed(), &history).unwrap().canonical_bytes(),
        engine.canonical_bytes()
    );
    assert_eq!(
        play::execute(
            &mut engine,
            &request,
            &mut script,
            &Cancellation::default(),
            &profile()
        )
        .unwrap(),
        receipt
    );
    assert_eq!(
        script.seen.len(),
        2,
        "Retry must not ask the provider again"
    );
    engine.canonical_bytes()
}

fn refuses_without_canon(bytes: Vec<u8>, expected: Error, calls: usize) {
    let mut engine = Engine::new(seed()).unwrap();
    let before = engine.canonical_bytes();
    let request = dialogue(&engine, SPEECH);
    let mut script = Script {
        replies: VecDeque::from([bytes.clone(), bytes]),
        seen: vec![],
    };
    assert_eq!(
        play::execute(
            &mut engine,
            &request,
            &mut script,
            &Cancellation::default(),
            &profile()
        ),
        Err(expected)
    );
    assert_eq!(script.seen.len(), calls);
    assert!(script.seen.iter().all(
        |request| matches!(&request.input, Input::Structured { role, .. } if role == "director")
    ));
    assert_eq!(engine.canonical_bytes(), before);
    assert_eq!(engine.revision(), 0);
    assert!(engine.receipts().is_empty());
    assert!(engine.state().claims.is_empty());
    assert_eq!(engine.state().items["potion"].owner, "player");
}

#[test]
fn equivalent_space_bmp_and_surrogate_pair_spellings_commit_exact_original_speech() {
    let original = commits_exact_speech(SPEECH, r#""Mira, snow 雪 and stars 😀.""#);
    for spelling in [
        r#""Mira,\u0020snow\u0020雪\u0020and\u0020stars\u0020😀.""#,
        r#""Mira,\u0020snow\u0020\u96ea\u0020and\u0020stars\u0020\ud83d\ude00.""#,
        r#""Mira, snow \u96EA and stars \uD83D\uDE00.""#,
    ] {
        assert_eq!(commits_exact_speech(SPEECH, spelling), original);
    }
}

#[test]
fn literal_backslash_u_is_not_a_space_and_is_never_decoded_twice() {
    let spelling = r#""Mira,\\u0020snow \u96ea and stars \ud83d\ude00.""#;
    refuses_without_canon(director(spelling, r#""mira""#), Error::Agency, 1);
    commits_exact_speech(r"Mira,\u0020snow 雪 and stars 😀.", spelling);
}

#[test]
fn changed_speech_malformed_surrogates_and_authority_attempts_still_refuse() {
    refuses_without_canon(
        director(
            r#""Mira, snow \u96ea and stars \ud83d\ude01.""#,
            r#""mira""#,
        ),
        Error::Agency,
        1,
    );
    for spelling in [
        r#""Mira, snow 雪 and stars \ud83d.""#,
        r#""Mira, snow 雪 and stars \ude00.""#,
    ] {
        refuses_without_canon(director(spelling, r#""mira""#), Error::Malformed, 2);
    }
    refuses_without_canon(
        br#"{"commands":[{"op":"set_fact","id":"ancestry","text":"I am royal"}]}"#.to_vec(),
        Error::Malformed,
        2,
    );
    refuses_without_canon(
        br#"{"commands":[{"op":"give","item":"potion","to":"mira","quantity":1}]}"#.to_vec(),
        Error::Agency,
        1,
    );
}

#[test]
fn escaped_observer_identifier_cannot_grant_remote_speech_access() {
    refuses_without_canon(
        director(
            r#""Mira,\u0020snow\u0020\u96ea and stars \ud83d\ude00.""#,
            r#""\u0073able""#,
        ),
        Error::Location,
        1,
    );
}
