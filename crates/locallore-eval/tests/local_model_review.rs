//! Independent private-boundary probe: compile the actual recorder source unchanged.
//! No target matching is exercised; the synthetic provider always returns fixed bytes.
use locallore::{contracts::*, inference::*};
use locallore_eval::{digest, Capture, Target};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::{sync::Arc, sync::Mutex, task::Poll};

fn contains_json(_: &Value, _: &Value) -> bool {
    unreachable!("this recorder probe supplies no retrieval targets")
}
#[allow(dead_code)] // Source module also contains production paths outside this focused probe.
#[path = "../src/local_recording.rs"]
mod actual_recording;

struct Fixed;
impl InferenceProvider for Fixed {
    fn poll(&mut self, _: &GenerationRequest, _: &Cancellation) -> Poll<Result<Vec<u8>, Error>> {
        Poll::Ready(Ok(b"{}".to_vec()))
    }
}

fn probe(role: &str, text: &str, forbidden: Vec<String>) -> Arc<actual_recording::Recording> {
    let state = Arc::new(actual_recording::Recording::default());
    let mut provider =
        actual_recording::RecordingProvider::new(Box::new(Fixed), state.clone(), vec![], forbidden);
    let request = GenerationRequest {
        version: 1,
        scope: Scope {
            story: "local-lineage".into(),
            branch: "child".into(),
        },
        turn: "review-boundary".into(),
        revision: 1,
        model_profile: "eval-scripted-fake-v1".into(),
        schema: "review".into(),
        budget: locallore::inference::Budget {
            max_output_bytes: 16_384,
            max_output_tokens: 350,
            max_pending_polls: 1,
            deadline_ms: 60_000,
        },
        input: Input::Structured {
            role: role.into(),
            prompt: text.into(),
            schema: json!({"type":"object"}),
        },
    };
    assert_eq!(
        provider.poll(&request, &Cancellation::default()),
        Poll::Ready(Ok(b"{}".to_vec())),
        "passive evaluation recording must preserve the provider result"
    );
    drop(provider);
    state
}

fn recorded_privacy_failure(state: &actual_recording::Recording) -> bool {
    let records = state.state.lock().unwrap();
    records.forbidden_narrator_prompt || records.forbidden_narrator_output
}

#[test]
fn actual_director_envelope_canaries_must_record_a_privacy_failure() {
    let canaries = [
        "PARENT-FUTURE-MIST",
        "SIBLING-ONLY-SALT",
        "FOREIGN-ONLY-lineage",
    ];
    let forbidden = canaries.iter().map(|s| (*s).to_owned()).collect::<Vec<_>>();
    let mut undetected = vec![];
    for canary in canaries {
        let state = probe("director", canary, forbidden.clone());
        if !recorded_privacy_failure(&state) {
            undetected.push(canary);
        }
    }
    assert!(
        undetected.is_empty(),
        "actual submitted director envelope leaks had no privacy failure: {undetected:?}"
    );
}

#[test]
fn player_secret_is_legitimate_director_input_but_forbidden_narrator_input() {
    let secret = "SECRET-TIDE-731";
    let director = probe("director", secret, vec![secret.into()]);
    assert!(!recorded_privacy_failure(&director));
    let narrator = probe("narrator", secret, vec![secret.into()]);
    assert!(recorded_privacy_failure(&narrator));
}
