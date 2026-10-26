// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Reference hashes captured on unchanged Core6898a35b before renderer factoring.
//! Explicit stable projection, NOT whole GenerationRequest/Receipt bytes:
//! deadlines/stage timings are measured separately and never normalized.
use locallore::{
    context_compiler::ContextPolicy,
    contracts::{Command, Error, Intent, PlayInputKind},
    engine::Engine,
    inference::{Cancellation, GenerationRequest, InferenceProvider, Input},
    memory_coverage::{CoverageRead, FallbackReason},
    play::{self, PlayConstructionInput, PlayProfile},
};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{collections::VecDeque, task::Poll};

const BASE: &str = "6898a35bad4f9dbf8c6373191e7a72620c5bcb93";
const EXPECTED: [(&str, &str); 4] = [
    (
        "recent-action-repair",
        "b3354bc3de071ba018b6d3912659c3fa525fd61fe4538ad347fd753ecbeac3f1",
    ),
    (
        "recent-dialogue-repair",
        "93c269faeb3c3844b88fbe39fe7b4219ff9ef63fb4824058d2b8cc1e3db013d4",
    ),
    (
        "relevant-action-repair",
        "bb24293d653b2c6f795cf54b2526f6c4de750565be2470aaac2b3294a26db6df",
    ),
    (
        "relevant-dialogue-repair",
        "ff8fc717b8e25456db7ed9d43dd5cccb0086a9b5261c55ee4a54b323c84e4200",
    ),
];

fn profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-legacy-render".into(),
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
fn engine() -> Engine {
    let mut e = Engine::new(
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap(),
    )
    .unwrap();
    for (key, intent) in [
        (
            "prior-typed",
            Intent::Actions(vec![Command::Wait { ticks: 1 }]),
        ),
        (
            "prior-dialogue",
            Intent::Dialogue {
                text: "Mira, remember the harbor promise: café 灯 🧭.\nA second line.".into(),
                audience: ["mira".into()].into(),
            },
        ),
    ] {
        let request = e.request(key, intent);
        let proposal = Engine::proposal(&request).unwrap();
        let preview = e.preview(&request, &proposal).unwrap();
        assert_eq!(
            e.commit(&request, &proposal, preview.narration()).unwrap(),
            preview
        );
    }
    assert_eq!(e.revision(), 2);
    e
}
struct Recorder {
    replies: VecDeque<Vec<u8>>,
    actual: Vec<GenerationRequest>,
}
impl InferenceProvider for Recorder {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        _: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        self.actual.push(request.clone());
        Poll::Ready(self.replies.pop_front().ok_or(Error::Provider))
    }
}

// Named, test-local stable projection of ACTUAL forwarded structured inputs,
// fixed profile and static request budget limits. Do not call this a full
// request hash: deadline_ms is validated below but deliberately not projected.
fn stable_role_input(request: &GenerationRequest, profile: &PlayProfile) -> Value {
    assert!(request.budget.deadline_ms > 0 && request.budget.deadline_ms <= profile.deadline_ms);
    let Input::Structured {
        role,
        prompt,
        schema,
    } = &request.input
    else {
        panic!("current Play must record the actual structured provider path");
    };
    assert_eq!(request.budget.max_output_bytes, 16_384);
    assert_eq!(request.budget.max_pending_polls, 30_000);
    assert_eq!(request.budget.max_output_tokens, 350);
    json!({
        "version":request.version,"scope":request.scope,"turn":request.turn,
        "revision":request.revision,"model_profile":request.model_profile,"schema_id":request.schema,
        "static_budget":{"max_output_bytes":request.budget.max_output_bytes,
            "max_output_tokens":request.budget.max_output_tokens,"max_pending_polls":request.budget.max_pending_polls},
        "input":{"kind":"structured","role":role,"prompt":prompt,"schema":schema},
    })
}

#[test]
fn actual_current_play_static_role_inputs_and_repair_bytes_preserve_legacy_rendering() {
    let policies = [
        ContextPolicy::StateRecentTranscriptV1,
        ContextPolicy::StateRelevantMemoryV1,
    ];
    let kinds = [PlayInputKind::Action, PlayInputKind::Dialogue];
    let mut observed = Vec::new();
    for (index, (policy, kind)) in policies
        .into_iter()
        .flat_map(|p| kinds.map(|k| (p, k)))
        .enumerate()
    {
        let (name, _) = EXPECTED[index];
        let mut e = engine();
        let p = profile();
        p.validate().unwrap();
        let text = if kind == PlayInputKind::Action {
            "I wait for one tide tick."
        } else {
            "Keep the harbor promise: café 灯 🧭; \"quoted\" \\ tide."
        };
        let request = e.request(
            "current-render",
            Intent::FreeText {
                kind,
                text: text.into(),
            },
        );
        let proposal = if kind == PlayInputKind::Action {
            json!({"commands":[{"op":"wait","ticks":1}]})
        } else {
            json!({"commands":[{"op":"say","text":text,"audience":["mira"]}]})
        };
        let narration = if kind == PlayInputKind::Action {
            "You pause as a tide tick passes."
        } else {
            "Your words are heard by the chosen listeners."
        };
        let mut provider = Recorder {
            replies: [
                b"{".to_vec(),
                serde_json::to_vec(&proposal).unwrap(),
                serde_json::to_vec(&json!({"text":narration,"event_ids":[3],"speaker":"narrator"}))
                    .unwrap(),
            ]
            .into(),
            actual: vec![],
        };
        let receipt = play::execute_traced_with_policy(
            &mut e,
            &request,
            &mut provider,
            &Cancellation::default(),
            &p,
            None,
            PlayConstructionInput {
                coverage: &CoverageRead::RawFallback(FallbackReason::Missing),
                policy,
            },
        )
        .unwrap();
        assert!(provider.replies.is_empty());
        assert_eq!(provider.actual.len(), 3);
        let record = receipt.play().unwrap();
        assert_eq!(record.prompt_version, "locallore-play-v2.5");
        assert_eq!(record.context_policy, Some(policy));
        assert_eq!(record.repairs, 1);
        assert!(!record.fallback);
        assert!(!record.stages.is_empty());
        assert!(record.stages.iter().all(|s| s.elapsed_ms <= p.deadline_ms));
        let roles: Vec<_> = provider
            .actual
            .iter()
            .map(|r| stable_role_input(r, &p))
            .collect();
        assert_eq!(
            roles
                .iter()
                .map(|r| r["input"]["role"].as_str().unwrap())
                .collect::<Vec<_>>(),
            vec!["director", "director", "narrator"]
        );
        assert!(play::director_repair_matches_v25(
            roles[0]["input"]["prompt"].as_str().unwrap(),
            roles[1]["input"]["prompt"].as_str().unwrap()
        ));
        assert_eq!(roles[0]["input"]["schema"], roles[1]["input"]["schema"]);
        let projection = json!({"projection_version":1,"projection_kind":"actual_play25_static_role_inputs",
            "policy":policy,"profile":p,"roles":roles});
        let bytes = serde_json::to_vec(&projection).unwrap();
        let hash = format!("{:x}", Sha256::digest(&bytes));
        eprintln!(
            "LEGACY_PLAY_STATIC_BYTES base={BASE} case={name} bytes={} sha256={hash}",
            bytes.len()
        );
        observed.push((name, hash));

        // Preserve REAL timings/deadlines as measured; do not normalize receipt.
        // Replay receives no provider, and full stored receipt bytes stay exact.
        let compact = serde_json::to_vec(&receipt).unwrap();
        let history: Vec<_> = e
            .receipts()
            .iter()
            .map(|r| serde_json::to_string(r).unwrap())
            .collect();
        let calls = provider.actual.len();
        let restored = Engine::restore(e.seed().clone(), &history).unwrap();
        assert_eq!(
            serde_json::to_vec(restored.receipts().last().unwrap()).unwrap(),
            compact
        );
        assert_eq!(restored.canonical_bytes(), e.canonical_bytes());
        assert_eq!(provider.actual.len(), calls);
    }
    assert_eq!(observed.len(), 4);
    let expected: Vec<_> = EXPECTED
        .into_iter()
        .map(|(n, h)| (n, h.to_owned()))
        .collect();
    assert_eq!(
        observed, expected,
        "existing Play static role bytes changed"
    );
}
