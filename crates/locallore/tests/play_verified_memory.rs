//! Production Play paths with synthetic providers; no model/assets/Host/Store.
use locallore::{
    contracts::*,
    engine::Engine,
    inference::*,
    play::{self, PlayProfile},
};
use serde_json::{json, Value};
use std::{collections::VecDeque, task::Poll};

fn engine() -> Engine {
    Engine::new(serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap())
        .unwrap()
}
fn profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-memory-boundary".into(),
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
struct Script {
    replies: VecDeque<Vec<u8>>,
    seen: Vec<GenerationRequest>,
}
impl Script {
    fn values(values: Vec<Value>) -> Self {
        Self {
            replies: values
                .into_iter()
                .map(|value| serde_json::to_vec(&value).unwrap())
                .collect(),
            ..Self::default()
        }
    }
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

/// Sole explicit test-only writer: fixed NEW synthetic fixture, create_new only.
/// Must execute against unmodified 2.3 production before the version bump.
#[test]
#[ignore = "one-time original 2.3 fixture capture, requires explicit environment opt-in"]
fn freeze_original_v23_receipt_before_memory_consumer() {
    assert_eq!(
        std::env::var("LOCALLORE_CAPTURE_PLAY_V23").as_deref(),
        Ok("1")
    );
    assert_eq!(play::PROMPT_VERSION, "locallore-play-v2.3");
    let mut e = engine();
    let request = e.request(
        "accepted-v23-memory-boundary",
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: "give potion to Mira".into(),
        },
    );
    let mut provider = Script::values(vec![
        json!({"commands":[{"op":"give","item":"potion","to":"mira","quantity":1}]}),
        json!({"text":"You pass the potion to Mira with care.","event_ids":[1],"speaker":"narrator"}),
    ]);
    let receipt = play::execute(
        &mut e,
        &request,
        &mut provider,
        &Cancellation::default(),
        &profile(),
    )
    .unwrap();
    assert_eq!(provider.seen.len(), 2);
    assert_eq!(
        receipt.play().unwrap().prompt_version,
        "locallore-play-v2.3"
    );
    let fixture = json!({"source_commit":"5e44ea91bfa9e93ecf583e31a26937efdfa96366",
        "generator":"tests/play_verified_memory.rs::freeze_original_v23_receipt_before_memory_consumer",
        "synthetic":true,"provider_calls":provider.seen.len(),"seed":e.seed(),"receipt":receipt});
    let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("tests/fixtures/accepted_play_v2_3.json");
    use std::io::Write;
    let mut file = std::fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)
        .unwrap();
    file.write_all(&serde_json::to_vec_pretty(&fixture).unwrap())
        .unwrap();
    file.write_all(b"\n").unwrap();
}
