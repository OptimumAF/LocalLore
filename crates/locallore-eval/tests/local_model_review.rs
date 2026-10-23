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

fn probe(
    role: &str,
    text: &str,
    forbidden: actual_recording::ForbiddenByRole,
) -> Arc<actual_recording::Recording> {
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
    records.forbidden_director_prompt
        || records.forbidden_narrator_prompt
        || records.forbidden_narrator_output
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
        let state = probe(
            "director",
            canary,
            actual_recording::ForbiddenByRole {
                director: forbidden.clone(),
                narrator: forbidden.clone(),
            },
        );
        let records = state.state.lock().unwrap();
        if !records.forbidden_director_prompt {
            undetected.push(canary);
        }
        assert!(!records.forbidden_narrator_prompt);
    }
    assert!(
        undetected.is_empty(),
        "actual submitted director envelope leaks had no privacy failure: {undetected:?}"
    );
}

#[test]
fn player_secret_is_legitimate_director_input_but_forbidden_narrator_input() {
    let secret = "SECRET-TIDE-731";
    let policy = actual_recording::ForbiddenByRole {
        director: vec![
            "PARENT-FUTURE-MIST".into(),
            "SIBLING-ONLY-SALT".into(),
            "FOREIGN-ONLY-lineage".into(),
        ],
        narrator: vec![
            "PARENT-FUTURE-MIST".into(),
            "SIBLING-ONLY-SALT".into(),
            "FOREIGN-ONLY-lineage".into(),
            secret.into(),
        ],
    };
    let director = probe("director", secret, policy.clone());
    assert!(!recorded_privacy_failure(&director));
    for canary in &policy.narrator {
        let narrator = probe("narrator", canary, policy.clone());
        let records = narrator.state.lock().unwrap();
        assert!(records.forbidden_narrator_prompt);
        assert!(!records.forbidden_director_prompt);
    }
}

#[test]
fn unknown_admission_stays_charged_when_completed_story_is_reused() {
    use locallore_eval::local_lane::{run_curated, LaneFactory};
    use std::io::Write;
    let directory = std::env::temp_dir().join(format!(
        "independent-eval-unknown-reservation-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    let first = run_curated(
        &directory,
        false,
        Some("gift-agency"),
        &Cancellation::default(),
        1,
        LaneFactory::ScriptedBaseline,
    )
    .unwrap();
    assert!(first.completed);
    let checkpoint = std::fs::read(directory.join("case-00.json")).unwrap();
    let prior_roles = first.provenance["budget"]["roles_charged"]
        .as_u64()
        .unwrap();
    // Simulate the durable reservation left after admission and before settlement.
    // This is a fixed synthetic ledger fixture, not an actual process-kill claim.
    let unknown = json!({
        "version":1,"binding":first.binding_sha256,"index":4,
        "story":"gift-agency","turn":"gift","ms":60000,"roles":3
    });
    let mut file = std::fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(directory.join("admission-04.json"))
        .unwrap();
    file.write_all(&serde_json::to_vec(&unknown).unwrap())
        .unwrap();
    file.sync_all().unwrap();
    drop(file);
    let resumed = run_curated(
        &directory,
        true,
        Some("gift-agency"),
        &Cancellation::default(),
        1,
        LaneFactory::ScriptedBaseline,
    )
    .unwrap();
    assert!(resumed.completed);
    assert_eq!(
        resumed.provenance["budget"]["admissions_across_attempts"],
        5
    );
    assert_eq!(
        resumed.provenance["budget"]["roles_charged"],
        prior_roles + 3
    );
    assert!(
        resumed.provenance["budget"]["active_ms_charged"]
            .as_u64()
            .unwrap()
            >= 60000
    );
    assert!(!directory.join("admission-04-settled.json").exists());
    assert!(!directory.join("admission-05.json").exists());
    assert!(!directory.join("case-00-attempt-01").exists());
    assert_eq!(
        std::fs::read(directory.join("case-00.json")).unwrap(),
        checkpoint
    );
    assert!(!resumed.quality_accepted);
}
