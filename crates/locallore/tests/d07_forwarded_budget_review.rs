//! Frozen source-only regressions, not executed evidence. Synthetic providers only.
//! Reuse the exact frozen suite; do not maintain a second copy of its 24 texts.
use locallore::{
    context_compiler::{self as compiler, ContextPackage, ContextPolicy, Kind},
    contracts::*,
    engine::Engine,
    inference::{Cancellation, GenerationRequest, InferenceProvider, Input},
    memory_coverage::{CoverageRead, FallbackReason},
    play::{self, PlayConstructionInput, PlayProfile},
    turn_capture::Artifact,
    turn_trace::{StageMeasurement, TraceSink},
};
use serde_json::{json, Value};
use std::{collections::BTreeSet, task::Poll};

// Exact existing pure protocol, not its runner/Store/runtime. This also binds the
// suite hash to the unchanged original scenarios and expected commands.
#[allow(dead_code)]
#[path = "../../locallore-eval/src/memory_comparison.rs"]
mod protocol;

const POLICIES: [ContextPolicy; 2] = [
    ContextPolicy::StateRecentTranscriptV1,
    ContextPolicy::StateRelevantMemoryV1,
];
const REPAIR_SUFFIX: &str = "\nPrevious output was malformed. Repair exactly once using the schema. Do not change the player's requested intent.";
const TEMPLATE_RESERVE_ESTIMATE: usize = 162;

fn profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-forwarded-budget".into(),
        model_sha256: "a".repeat(64),
        runtime_revision: "b".repeat(40),
        template_sha256: "c".repeat(64),
        worker_sha256: "d".repeat(64),
        profile_manifest_sha256: "e".repeat(64),
        context_tokens: 4096,
        director_tokens: 350,
        narrator_tokens: 350,
        deadline_ms: 120_000,
        repair_limit: 1,
    }
}
fn suite() -> protocol::FrozenSuite {
    let suite = protocol::frozen_suite().unwrap();
    assert_eq!(suite.steps().len(), 24);
    assert_eq!(
        suite.sha256().unwrap(),
        "6e7172c6c8bedb4b82b703aac30b7b92c5a924d0203578cb2f027611d7def21a"
    );
    suite
}
#[derive(Default)]
struct Script {
    commands: Vec<Command>,
    narration: String,
    events: Vec<u64>,
    seen: Vec<GenerationRequest>,
    malformed_first: bool,
}
impl Script {
    fn step(before: &Engine, step: &protocol::Step) -> Self {
        let Ok(proposal) = protocol::reference_proposal(before, step) else {
            return Self::default();
        };
        let approved = before.preview(&step.request(before), &proposal).unwrap();
        Self {
            commands: proposal.commands,
            narration: approved.narration().into(),
            events: approved.events().iter().map(|e| e.sequence()).collect(),
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
        if self.malformed_first && self.seen.len() == 1 {
            return Poll::Ready(Ok(b"{".to_vec()));
        }
        let Input::Structured { role, .. } = &request.input else {
            return Poll::Ready(Err(Error::Provider));
        };
        let value = match role.as_str() {
            "director" => json!({"commands":self.commands}),
            "narrator" => {
                json!({"text":self.narration,"event_ids":self.events,"speaker":"narrator"})
            }
            _ => return Poll::Ready(Err(Error::Provider)),
        };
        Poll::Ready(Ok(serde_json::to_vec(&value).unwrap()))
    }
}
#[derive(Default)]
struct Capture(Vec<ContextPackage>);
impl TraceSink for Capture {
    fn matches(&mut self, _: &Scope, _: u64, _: &str, _: &str) -> bool {
        true
    }
    fn record(&mut self, _: StageMeasurement) {}
    fn capture(&mut self, artifact: Artifact<'_>) {
        if let Artifact::Context(package) = artifact {
            self.0.push(package.clone());
        }
    }
}
fn execute(
    engine: &mut Engine,
    step: &protocol::Step,
    policy: ContextPolicy,
    provider: &mut Script,
    capture: &mut Capture,
) -> Result<Receipt, Error> {
    let request = step.request(engine);
    play::execute_traced_with_policy(
        engine,
        &request,
        provider,
        &Cancellation::default(),
        &profile(),
        Some(capture),
        PlayConstructionInput {
            coverage: &CoverageRead::RawFallback(FallbackReason::Missing),
            policy,
        },
    )
}
fn first_eight() -> Engine {
    let suite = suite();
    let mut engine = Engine::new(suite.seed().clone()).unwrap();
    for step in &suite.steps()[..8] {
        let mut script = Script::step(&engine, step);
        let receipt = execute(
            &mut engine,
            step,
            ContextPolicy::StateRelevantMemoryV1,
            &mut script,
            &mut Capture::default(),
        )
        .unwrap();
        assert_eq!(script.seen.len(), 2);
        assert_eq!(receipt.events().len(), 1);
    }
    assert_eq!(engine.revision(), 8);
    assert_eq!(engine.receipts().len(), 8);
    engine
}
fn compile_request(engine: &Engine, step: &protocol::Step) -> compiler::CompileRequest {
    compiler::CompileRequest {
        version: 2,
        scope: engine.scope().clone(),
        expected_head: engine.revision(),
        at_revision: None,
        observer: engine.seed().player.clone(),
        role: compiler::Role::Director,
        query: if step.kind() == PlayInputKind::Action {
            step.text().into()
        } else {
            String::new()
        },
        referenced_ids: vec![],
        budget: compiler::Budget::default(),
    }
}
fn actual_input(request: &GenerationRequest) -> (&str, &Value, Value) {
    let Input::Structured { prompt, schema, .. } = &request.input else {
        panic!("actual structured Director request required")
    };
    let suffix = prompt.split_once("Context data: ").unwrap().1;
    let mut values = serde_json::Deserializer::from_str(suffix).into_iter::<Value>();
    (prompt, schema, values.next().unwrap().unwrap())
}
fn assert_forwarded(package: &ContextPackage, request: &GenerationRequest) {
    let (prompt, schema, input) = actual_input(request);
    let records: Vec<_> = package
        .records
        .iter()
        .map(|r| json!({"kind":r.kind,"source_revision":r.source_revision,"payload":r.payload}))
        .collect();
    assert_eq!(
        input["context"],
        json!({
            "compiler_version":package.version,"observer":package.observer,
            "revision":package.revision,"records":records
        })
    );
    assert_eq!(
        input["context"].as_object().unwrap().len(),
        4,
        "no diagnostic/package-only fields may be added to model context"
    );
    assert_eq!(
        package.serialized_bytes,
        serde_json::to_vec(package).unwrap().len()
    );
    assert_eq!(
        package.estimated_tokens as usize,
        package.serialized_bytes.div_ceil(4)
    );
    assert!(package.serialized_bytes <= 24_576);
    assert!(package.records.len() <= 128);
    assert_eq!(request.budget.max_output_tokens, 350);
    assert_eq!(REPAIR_SUFFIX.len(), 114);
    let repair_bytes = if prompt.ends_with(REPAIR_SUFFIX) {
        0
    } else {
        REPAIR_SUFFIX.len()
    };
    // This is explicitly an estimate, not actual model tokenization/template fit.
    // Preserve the old total reserve512 = output350 + template estimate162.
    let charged = (prompt.len() + serde_json::to_vec(schema).unwrap().len() + repair_bytes)
        .div_ceil(4)
        + 350
        + TEMPLATE_RESERVE_ESTIMATE;
    assert!(
        charged <= 4096,
        "actual complete forwarded envelope estimate {charged}"
    );
    assert!(input["context"].get("diagnostics").is_none());
}

#[test]
fn generic_current_compiler_still_refuses_the_full_wire_floor_at_head8() {
    let suite = suite();
    let engine = first_eight();
    let before = engine.canonical_bytes();
    for policy in POLICIES {
        for index in [10, 11] {
            assert_eq!(
                compiler::compile_policy_cancelled(
                    &engine,
                    &compile_request(&engine, &suite.steps()[index]),
                    policy,
                    None,
                    &|| false
                )
                .unwrap_err(),
                compiler::CompileError::MandatoryBudget
            );
        }
    }
    assert_eq!(engine.canonical_bytes(), before);
}

#[test]
#[ignore = "historical baseline ONLY: run unchanged on0fd before the Play-only budget fix"]
fn historical_play_head8_refuses_before_any_provider_role() {
    let suite = suite();
    for policy in POLICIES {
        for index in [10, 11] {
            let mut engine = first_eight();
            let before = engine.canonical_bytes();
            let mut script = Script::step(&engine, &suite.steps()[index]);
            assert_eq!(
                execute(
                    &mut engine,
                    &suite.steps()[index],
                    policy,
                    &mut script,
                    &mut Capture::default()
                )
                .unwrap_err(),
                Error::TooLarge
            );
            assert!(script.seen.is_empty());
            assert_eq!(engine.canonical_bytes(), before);
        }
    }
}

#[test]
fn current_play_admits_same_head8_payload_without_dropping_mandatory_evidence() {
    let suite = suite();
    for policy in POLICIES {
        for index in [10, 11] {
            let mut engine = first_eight();
            let mut script = Script::step(&engine, &suite.steps()[index]);
            let mut capture = Capture::default();
            let receipt = execute(
                &mut engine,
                &suite.steps()[index],
                policy,
                &mut script,
                &mut capture,
            )
            .unwrap();
            assert_eq!(script.seen.len(), 2);
            assert_eq!(receipt.play().unwrap().context_policy, Some(policy));
            assert_eq!(engine.revision(), 9);
            let package = &capture.0[0];
            assert!(
                package.estimated_tokens + 512 > 4096,
                "full diagnostic-wire token accounting must stay honest; only the Play admission basis changes"
            );
            let evidence: BTreeSet<_> = package
                .records
                .iter()
                .filter(|r| r.mandatory && r.kind == Kind::Observation)
                .map(|r| r.source_revision)
                .collect();
            assert_eq!(evidence, [2, 4, 5, 6, 7, 8].into());
            for (kind, count) in [
                (Kind::CurrentState, 13),
                (Kind::KnownAsObserved, 2),
                (Kind::Relationship, 3),
                (Kind::Commitment, 1),
                (Kind::Rules, 1),
            ] {
                assert_eq!(
                    package
                        .records
                        .iter()
                        .filter(|r| r.mandatory && r.kind == kind)
                        .count(),
                    count
                );
            }
            assert_forwarded(package, &script.seen[0]);
        }
    }
}

#[test]
fn actual_regular_and_repair_requests_share_exact_projection_and_complete_budget() {
    let suite = suite();
    for policy in POLICIES {
        let mut engine = Engine::new(suite.seed().clone()).unwrap();
        let mut script = Script::step(&engine, &suite.steps()[0]);
        script.malformed_first = true;
        let mut capture = Capture::default();
        let receipt = execute(
            &mut engine,
            &suite.steps()[0],
            policy,
            &mut script,
            &mut capture,
        )
        .unwrap();
        assert_eq!(script.seen.len(), 3);
        assert_eq!(receipt.play().unwrap().repairs, 1);
        assert_forwarded(&capture.0[0], &script.seen[0]);
        assert_forwarded(&capture.0[0], &script.seen[1]);
        let (base, _, _) = actual_input(&script.seen[0]);
        let (repair, _, _) = actual_input(&script.seen[1]);
        assert_eq!(repair, format!("{base}{REPAIR_SUFFIX}"));
    }
}

#[test]
fn unchanged_original24_complete_both_policy_chains_with_21_accepts_3_guards_and_42_roles() {
    let suite = suite();
    for policy in POLICIES {
        let mut engine = Engine::new(suite.seed().clone()).unwrap();
        let (mut accepted, mut guarded, mut roles) = (0, 0, 0);
        for step in suite.steps() {
            let before = engine.canonical_bytes();
            let mut script = Script::step(&engine, step);
            let mut capture = Capture::default();
            let result = execute(&mut engine, step, policy, &mut script, &mut capture);
            match step.expected() {
                protocol::Expected::Accepted(command) => {
                    let receipt = result.unwrap();
                    assert_eq!(receipt.proposal().commands, vec![command.clone()]);
                    assert_eq!(script.seen.len(), 2);
                    assert_forwarded(&capture.0[0], &script.seen[0]);
                    accepted += 1;
                }
                protocol::Expected::GuardRejected(expected) => {
                    let error = match expected {
                        protocol::GuardRejection::Inventory => Error::Inventory,
                        protocol::GuardRejection::Ability => Error::Ability,
                        protocol::GuardRejection::ClarificationRequired => {
                            Error::ClarificationRequired
                        }
                    };
                    assert_eq!(result.unwrap_err(), error);
                    assert!(script.seen.is_empty());
                    assert_eq!(engine.canonical_bytes(), before);
                    guarded += 1;
                }
            }
            roles += script.seen.len();
        }
        assert_eq!((accepted, guarded, roles), (21, 3, 42));
        assert_eq!(engine.revision(), 21);
    }
}

#[test]
fn truly_oversized_mandatory_known_values_refuse_with_zero_roles_and_no_canon_change() {
    let suite = suite();
    let mut seed = suite.seed().clone();
    for n in 0..8 {
        seed.facts.insert(
            format!("budget-known-{n}"),
            Fact {
                proposition: "q".repeat(MAX_TEXT_BYTES),
                discoverable_at: None,
                known_by: [seed.player.clone()].into(),
            },
        );
    }
    // These mandatory proposition strings alone exhaust the entire4096 estimate;
    // the actual JSON envelope and350 output make the true estimate exceed it.
    assert_eq!(8 * MAX_TEXT_BYTES, 4096 * 4);
    for policy in POLICIES {
        let mut engine = Engine::new(seed.clone()).unwrap();
        let before = engine.canonical_bytes();
        let mut script = Script::step(&engine, &suite.steps()[0]);
        assert_eq!(
            execute(
                &mut engine,
                &suite.steps()[0],
                policy,
                &mut script,
                &mut Capture::default()
            )
            .unwrap_err(),
            Error::TooLarge
        );
        assert!(script.seen.is_empty());
        assert_eq!(engine.canonical_bytes(), before);
    }
}

#[test]
fn original_historical21_through24_records_replay_and_retry_without_any_roles() {
    use sha2::{Digest, Sha256};
    for text in [
        include_str!("fixtures/accepted_play_v2_1.json"),
        include_str!("fixtures/accepted_play_v2_2.json"),
        include_str!("fixtures/accepted_play_v2_3.json"),
        include_str!("fixtures/accepted_play_v2_4.json"),
    ] {
        let fixture: Value = serde_json::from_str(text).unwrap();
        let seed: Seed = serde_json::from_value(fixture["seed"].clone()).unwrap();
        let mut engine = Engine::restore(seed, &[fixture["receipt"].to_string()]).unwrap();
        let receipt = engine.receipts()[0].clone();
        assert_eq!(serde_json::to_value(&receipt).unwrap(), fixture["receipt"]);
        assert!(receipt.play().unwrap().context_policy.is_none());
        if receipt.play().unwrap().prompt_version == "locallore-play-v2.4" {
            let bytes = serde_json::to_vec(&receipt).unwrap();
            assert_eq!(
                bytes.as_slice(),
                include_bytes!("fixtures/accepted_play_v2_4_receipt.json").as_slice()
            );
            assert_eq!(
                format!("{:x}", Sha256::digest(&bytes)),
                "38dcf7329addf4ed98fd984cdb9eac95f8d078be03bf4633dd7082d23ac4bc3f"
            );
        }
        let before = engine.canonical_bytes();
        let mut no_roles = Script::default();
        let cancel = Cancellation::default();
        cancel.cancel();
        let mut invalid = profile();
        invalid.context_tokens = 0;
        assert_eq!(
            play::execute(
                &mut engine,
                receipt.request(),
                &mut no_roles,
                &cancel,
                &invalid
            )
            .unwrap(),
            receipt
        );
        assert!(no_roles.seen.is_empty());
        assert_eq!(engine.canonical_bytes(), before);
    }
}
