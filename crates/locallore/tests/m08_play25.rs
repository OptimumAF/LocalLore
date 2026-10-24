//! Synthetic provider plumbing oracles; never an actual-model quality claim.
use locallore::{
    contracts::*,
    engine::Engine,
    inference::*,
    play::{self, PlayProfile},
};
use serde_json::{json, Value};
use std::{collections::VecDeque, task::Poll};

fn seed() -> Seed {
    serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap()
}
fn profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-play25".into(),
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
    seen: Vec<GenerationRequest>,
    cancel_role: Option<&'static str>,
}
impl Script {
    fn values(values: Vec<Value>) -> Self {
        Self {
            replies: values
                .into_iter()
                .map(|v| serde_json::to_vec(&v).unwrap())
                .collect(),
            ..Self::default()
        }
    }
}
impl InferenceProvider for Script {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        cancel: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        self.seen.push(request.clone());
        if let Input::Structured { role, .. } = &request.input {
            if self.cancel_role == Some(role.as_str()) {
                cancel.cancel();
            }
        }
        Poll::Ready(self.replies.pop_front().ok_or(Error::Provider))
    }
}

/// Run ONLY this frozen file revision on unchanged2.4 production before bump.
/// Fixed synthetic output in caller-owned TEMP, create_new; no arbitrary writer.
#[test]
#[ignore = "original-source 2.4 fixture capture; explicit opt-in on unchanged 2.4 source only"]
fn freeze_original_v24_before_current_version_bump() {
    use sha2::{Digest, Sha256};
    use std::io::Write;
    assert_eq!(
        std::env::var("LOCALLORE_CAPTURE_PLAY_V24").as_deref(),
        Ok("1")
    );
    assert_eq!(play::PROMPT_VERSION, "locallore-play-v2.4");
    let mut engine = Engine::new(seed()).unwrap();
    let request = engine.request(
        "original-v24-play25-boundary",
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: "I give potion to Mira.".into(),
        },
    );
    let mut provider = Script::values(vec![
        json!({"commands":[{"op":"give","item":"potion","to":"mira","quantity":1}]}),
        json!({"text":"You pass the potion to Mira with care.","event_ids":[1],"speaker":"narrator"}),
    ]);
    let receipt = play::execute(
        &mut engine,
        &request,
        &mut provider,
        &Cancellation::default(),
        &profile(),
    )
    .unwrap();
    assert_eq!(provider.seen.len(), 2);
    assert_eq!(
        receipt.play().unwrap().prompt_version,
        "locallore-play-v2.4"
    );
    let compact = serde_json::to_vec(&receipt).unwrap();
    let fixture = json!({
        "synthetic":true,"source_commit":"4b0734228b7c891720e5980ed3c5c0440acc23d6",
        "generator":"m08_play25::freeze_original_v24_before_current_version_bump",
        "provider_calls":provider.seen.len(),"seed":engine.seed(),"receipt":receipt,
        "compact_receipt_sha256":format!("{:x}",Sha256::digest(&compact)),
        "compact_receipt_bytes":compact.len()
    });
    let bytes = serde_json::to_vec_pretty(&fixture).unwrap();
    let path = std::env::temp_dir().join("locallore-original-play-v24.json");
    let mut file = std::fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)
        .unwrap();
    file.write_all(&bytes).unwrap();
    file.write_all(b"\n").unwrap();
    println!(
        "original2.4 compact bytes={} sha256={:x}; fixture bytes={} sha256={:x}",
        compact.len(),
        Sha256::digest(&compact),
        bytes.len() + 1,
        Sha256::digest([bytes.as_slice(), b"\n"].concat())
    );
}
