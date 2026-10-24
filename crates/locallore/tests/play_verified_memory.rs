//! Production Play paths with synthetic providers; no model/assets/Host/Store.
use locallore::{context_compiler as compiler, memory_coverage as memory};
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

fn commit(e: &mut Engine, turn: &str, commands: Vec<Command>) {
    let request = e.request(turn, Intent::Actions(commands));
    let proposal = Engine::proposal(&request).unwrap();
    let narration = e
        .preview(&request, &proposal)
        .unwrap()
        .narration()
        .to_owned();
    e.commit(&request, &proposal, &narration).unwrap();
}
fn say(text: &str, audience: &str) -> Command {
    Command::Say {
        text: text.into(),
        audience: [audience.into()].into(),
    }
}
fn history() -> Engine {
    let mut seed = engine().seed().clone();
    seed.beliefs.push(Belief {
        believer: "player".into(),
        proposition: "PLAYER-BELIEF-LEDGER-RELIABLE".into(),
        source_claim: None,
        source: Evidence::Seed(seed.id.clone()),
        confidence: Confidence::Believed,
    });
    seed.facts.insert(
        "npc-private".into(),
        Fact {
            proposition: "NPC-ONLY-MEMORY-771".into(),
            discoverable_at: None,
            known_by: ["sable".into()].into(),
        },
    );
    let mut e = Engine::new(seed).unwrap();
    commit(
        &mut e,
        "old-duty",
        vec![Command::Promise {
            id: "beacon-duty".into(),
            to: "mira".into(),
            terms: "Repair the old beacon after the tide".into(),
            deadline: 10000,
            return_item: None,
        }],
    );
    for batch in 0..33 {
        commit(
            &mut e,
            &format!("ledger-{batch}"),
            (0..8)
                .map(|slot| say(&format!("Ledger shell {}", batch * 8 + slot), "mira"))
                .collect(),
        );
    }
    assert_eq!(e.revision(), 265);
    e
}
fn proof(e: &Engine, observer: &str) -> memory::VerifiedCoverage {
    let mut packets = Vec::new();
    let mut after = 0;
    while let Some(packet) = memory::build_chunk(
        e,
        &memory::ChunkRequest {
            scope: e.scope().clone(),
            expected_head: e.revision(),
            observer: observer.into(),
            from_exclusive: after,
        },
        &|| false,
    )
    .unwrap()
    {
        assert!(packet.through_revision > after);
        after = packet.through_revision;
        packets.push(packet.bytes().unwrap());
        assert!(packets.len() <= memory::MAX_PACKETS);
    }
    match memory::verify_coverage(
        e,
        &memory::CoverageRequest {
            scope: e.scope().clone(),
            expected_head: e.revision(),
            observer: observer.into(),
        },
        &packets.iter().map(Vec::as_slice).collect::<Vec<_>>(),
        &|| false,
    )
    .unwrap()
    {
        memory::CoverageRead::Verified(value) => value,
        memory::CoverageRead::RawFallback(reason) => {
            panic!("actual generated proof refused: {reason:?}")
        }
    }
}
fn wait_request(e: &Engine, turn: &str) -> Request {
    e.request(
        turn,
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: "I wait for one tide tick.".into(),
        },
    )
}
fn wait_script(head: u64) -> Script {
    Script::values(vec![
        json!({"commands":[{"op":"wait","ticks":1}]}),
        json!({"text":"Time passes.","event_ids":[head+1],"speaker":"narrator"}),
    ])
}
fn prompt(provider: &Script, role: &str) -> String {
    provider
        .seen
        .iter()
        .filter_map(|request| match &request.input {
            Input::Structured {
                role: actual,
                prompt,
                ..
            } if actual == role => Some(prompt.clone()),
            _ => None,
        })
        .next()
        .unwrap()
}
#[derive(Default)]
struct ContextCapture(Vec<Vec<u8>>);
impl locallore::turn_trace::TraceSink for ContextCapture {
    fn matches(&mut self, _: &Scope, _: u64, observer: &str, _: &str) -> bool {
        observer == "player"
    }
    fn record(&mut self, _: locallore::turn_trace::StageMeasurement) {}
    fn capture(&mut self, artifact: locallore::turn_capture::Artifact<'_>) {
        if let locallore::turn_capture::Artifact::Context(value) = artifact {
            self.0.push(serde_json::to_vec(value).unwrap());
        }
    }
}

#[test]
fn actual_verified_prefix_and_raw_delta_preserve_same_prompt_state_and_mandatory_authority() {
    let mut base = history();
    let retained = proof(&base, "player");
    commit(
        &mut base,
        "raw-tail",
        vec![say("RAW-DELTA-PRESENT", "mira")],
    );
    assert_eq!(base.revision(), 266);
    let request = wait_request(&base, "same-memory-turn");
    let expected = compiler::compile_policy_cancelled(
        &base,
        &compiler::CompileRequest {
            version: compiler::POLICY_COMPILER_VERSION,
            scope: base.scope().clone(),
            expected_head: 266,
            at_revision: None,
            observer: "player".into(),
            role: compiler::Role::Director,
            query: "I wait for one tide tick.".into(),
            referenced_ids: vec![],
            budget: compiler::Budget::default(),
        },
        compiler::ContextPolicy::StateRelevantMemoryV1,
        Some(&retained),
        &|| false,
    )
    .unwrap().compilation;
    let mut raw = base.clone();
    let mut cached = base.clone();
    let mut p1 = wait_script(266);
    let mut p2 = wait_script(266);
    let mut c1 = ContextCapture::default();
    let mut c2 = ContextCapture::default();
    let r1 = play::execute_traced(
        &mut raw,
        &request,
        &mut p1,
        &Cancellation::default(),
        &profile(),
        Some(&mut c1),
    )
    .unwrap();
    let r2 = play::execute_traced_with_memory(
        &mut cached,
        &request,
        &mut p2,
        &Cancellation::default(),
        &profile(),
        Some(&mut c2),
        Some(&retained),
    )
    .unwrap();
    assert_eq!(p1.seen.len(), 2);
    assert_eq!(p2.seen.len(), 2);
    assert_eq!(c1.0, c2.0, "existing ContextPackage bytes must not change");
    assert_eq!(prompt(&p1, "director"), prompt(&p2, "director"));
    assert_eq!(prompt(&p1, "narrator"), prompt(&p2, "narrator"));
    let director = prompt(&p2, "director");
    for mandatory in [
        "beacon-duty",
        "return-key",
        "ancestry",
        "relationship",
        "PLAYER-BELIEF-LEDGER-RELIABLE",
    ] {
        assert!(
            director.contains(mandatory),
            "missing mandatory {mandatory}"
        );
    }
    assert!(
        director.contains("SECRET-TIDE-731"),
        "player legitimately knows this fact"
    );
    assert!(!director.contains("NPC-ONLY-MEMORY-771"));
    assert!(!director.contains("cached_event_candidates"));
    assert!(!prompt(&p2, "narrator").contains("SECRET-TIDE-731"));
    assert_eq!(raw.canonical_bytes(), cached.canonical_bytes());
    assert_eq!(r1.events(), r2.events());
    assert_eq!(r1.proposal(), r2.proposal());
    let c1 = r1.play().unwrap().context.as_ref().unwrap();
    let c2 = r2.play().unwrap().context.as_ref().unwrap();
    assert_eq!(
        serde_json::to_value(&c2.coverage).unwrap(),
        serde_json::to_value(&expected.coverage).unwrap(),
        "record actual compiler counters without reinterpretation"
    );
    assert_eq!(c2.scope, expected.package.scope);
    assert_eq!(c2.compiler_version, expected.package.version);
    assert_eq!(c1.coverage.mode, play::PlayCoverageMode::Raw);
    assert_eq!(
        c1.coverage.set_fallback_reason,
        Some(play::PlayMemoryFallback::Missing)
    );
    assert_eq!(c2.coverage.mode, play::PlayCoverageMode::Verified);
    assert_eq!(c2.coverage.covered_through, 265);
    assert_eq!(c2.coverage.raw_delta_after, 265);
    assert!(c2.coverage.cached_event_candidates > 0);
    assert!(c2.coverage.raw_event_candidates > 0);
    assert!(
        c2.coverage.mandatory_fallback_packets > 0,
        "supporting promise evidence must refetch its whole packet"
    );
    assert_eq!(c2.observer, "player");
    assert_eq!(c2.head, 266);
    assert_eq!(r2.play().unwrap().prompt_version, "locallore-play-v2.5");
}

#[test]
fn verified_time_span_reports_whole_packet_raw_fallback_without_relabelling() {
    let mut e = engine();
    commit(&mut e, "time", vec![Command::Wait { ticks: 1 }; 8]);
    let retained = proof(&e, "player");
    let request = wait_request(&e, "time-followup");
    let mut provider = wait_script(8);
    let receipt = play::execute_traced_with_memory(
        &mut e,
        &request,
        &mut provider,
        &Cancellation::default(),
        &profile(),
        None,
        Some(&retained),
    )
    .unwrap();
    let c = &receipt.play().unwrap().context.as_ref().unwrap().coverage;
    assert_eq!(c.mode, play::PlayCoverageMode::Verified);
    assert_eq!(c.cached_event_candidates, 0);
    assert_eq!(c.packets_used, 0);
    assert_eq!(c.timespan_fallback_packets, 1);
    assert_eq!(c.raw_event_candidates, 8);
}

#[test]
fn foreign_observer_story_branch_and_divergent_sources_fall_back_to_actual_raw_context() {
    let mut source = engine();
    commit(&mut source, "prefix", vec![say("SOURCE-PREFIX", "mira")]);
    let player = proof(&source, "player");
    let mira = proof(&source, "mira");
    let mut foreign_seed = source.seed().clone();
    foreign_seed.scope.story = "another-story".into();
    let mut divergent = Engine::new(source.seed().clone()).unwrap();
    commit(
        &mut divergent,
        "prefix",
        vec![say("ACTUAL-DIVERGENT", "mira")],
    );
    for (name, mut actual, retained) in [
        ("observer", source.clone(), &mira),
        ("story", Engine::new(foreign_seed).unwrap(), &player),
        ("branch", source.fork("child", 1).unwrap(), &player),
        ("divergent", divergent, &player),
    ] {
        let mut raw = actual.clone();
        let request = wait_request(&actual, name);
        let mut p1 = wait_script(actual.revision());
        let mut p2 = wait_script(actual.revision());
        play::execute(
            &mut raw,
            &request,
            &mut p1,
            &Cancellation::default(),
            &profile(),
        )
        .unwrap();
        let receipt = play::execute_traced_with_memory(
            &mut actual,
            &request,
            &mut p2,
            &Cancellation::default(),
            &profile(),
            None,
            Some(retained),
        )
        .unwrap();
        assert_eq!(prompt(&p1, "director"), prompt(&p2, "director"), "{name}");
        assert_eq!(raw.canonical_bytes(), actual.canonical_bytes(), "{name}");
        let c = &receipt.play().unwrap().context.as_ref().unwrap().coverage;
        assert_eq!(c.mode, play::PlayCoverageMode::Raw, "{name}");
        assert!(c.set_fallback_reason.is_some(), "{name}");
        assert_eq!(c.cached_event_candidates, 0);
        assert_eq!(c.covered_through, 0);
        if name == "divergent" {
            assert!(!prompt(&p2, "director").contains("SOURCE-PREFIX"));
        }
    }
}

#[test]
fn mandatory_budget_and_cancel_refuse_before_provider_for_raw_and_verified() {
    let mut base = engine();
    commit(&mut base, "proof", vec![say("accepted", "mira")]);
    let retained = proof(&base, "player");
    for coverage in [None, Some(&retained)] {
        for cancelled in [false, true] {
            let mut e = base.clone();
            let before = (e.canonical_bytes(), e.receipts().to_vec());
            let mut limits = profile();
            let cancel = Cancellation::default();
            if cancelled {
                cancel.cancel();
            } else {
                limits.context_tokens = 512;
            }
            let mut provider = Script::default();
            let request = wait_request(&e, "rejected");
            assert_eq!(
                play::execute_traced_with_memory(
                    &mut e,
                    &request,
                    &mut provider,
                    &cancel,
                    &limits,
                    None,
                    coverage
                ),
                Err(if cancelled {
                    Error::Cancelled
                } else {
                    Error::TooLarge
                })
            );
            assert!(provider.seen.is_empty());
            assert_eq!((e.canonical_bytes(), e.receipts().to_vec()), before);
        }
    }
}

#[test]
fn guarded_provider_proposal_stays_authoritative_and_repair_uses_same_schema() {
    let mut base = engine();
    commit(&mut base, "proof", vec![say("accepted", "mira")]);
    let retained = proof(&base, "player");
    let request = wait_request(&base, "actual-output");
    let mut e = base.clone();
    let before = e.canonical_bytes();
    let mut wrong = Script::values(vec![
        json!({"commands":[{"op":"give","item":"potion","to":"mira","quantity":1}]}),
    ]);
    assert_eq!(
        play::execute_traced_with_memory(
            &mut e,
            &request,
            &mut wrong,
            &Cancellation::default(),
            &profile(),
            None,
            Some(&retained)
        ),
        Err(Error::Agency)
    );
    assert_eq!(wrong.seen.len(), 1);
    assert_eq!(e.canonical_bytes(), before);
    let mut repair = wait_script(1);
    repair.replies.push_front(b"{".to_vec());
    let receipt = play::execute_traced_with_memory(
        &mut e,
        &request,
        &mut repair,
        &Cancellation::default(),
        &profile(),
        None,
        Some(&retained),
    )
    .unwrap();
    assert_eq!(receipt.play().unwrap().repairs, 1);
    assert_eq!(repair.seen.len(), 3);
    let schema = |request: &GenerationRequest| match &request.input {
        Input::Structured { schema, .. } => schema.clone(),
        _ => panic!("structured role"),
    };
    assert_eq!(schema(&repair.seen[0]), schema(&repair.seen[1]));
    assert_eq!(
        receipt.proposal().commands,
        vec![Command::Wait { ticks: 1 }]
    );
}

#[test]
fn exact_21_22_23_history_bytes_replay_and_retry_without_model_or_current_profile() {
    use sha2::{Digest, Sha256};
    assert_eq!(
        format!(
            "{:x}",
            Sha256::digest(include_bytes!("fixtures/accepted_play_v2_3.json"))
        ),
        "57fb218ef2f9a50842f77c2c87cd7e694ca53ea064c6205cfef18abd9e51035c"
    );
    let mut foreign = engine();
    commit(&mut foreign, "foreign", vec![say("foreign", "mira")]);
    let retained = proof(&foreign, "mira");
    for bytes in [
        include_str!("fixtures/accepted_play_v2_1.json"),
        include_str!("fixtures/accepted_play_v2_2.json"),
        include_str!("fixtures/accepted_play_v2_3.json"),
    ] {
        let fixture: Value = serde_json::from_str(bytes).unwrap();
        let seed: Seed = serde_json::from_value(fixture["seed"].clone()).unwrap();
        let mut e = Engine::restore(seed.clone(), &[fixture["receipt"].to_string()]).unwrap();
        let receipt = e.receipts()[0].clone();
        assert_eq!(serde_json::to_value(&receipt).unwrap(), fixture["receipt"]);
        // Independently measured on original 5e44 production, frozen probe b769b99.
        let (length, expected) = match receipt.play().unwrap().prompt_version.as_str() {
            "locallore-play-v2.1" => (
                1905,
                "4e95baa09c8d0646f5465945bf6a3f659d600ba6ee86b45a45a26d70fc49e234",
            ),
            "locallore-play-v2.2" => (
                1788,
                "348f33142a818744bfc1a6a542244fd0a59bae0bbdd7f141d250766cb09bf119",
            ),
            "locallore-play-v2.3" => (
                1760,
                "e9a1c58aa02236e97041658fae7910b8571ad8d487266a45201c7aa1fa8614e0",
            ),
            other => panic!("unexpected historical version {other}"),
        };
        let compact = serde_json::to_vec(&receipt).unwrap();
        assert_eq!(compact.len(), length);
        assert_eq!(
            format!("{:x}", Sha256::digest(&compact)),
            expected,
            "exact original compact Receipt bytes"
        );
        assert!(receipt.play().unwrap().context.is_none());
        assert_eq!(
            Engine::replay(seed.clone(), e.receipts())
                .unwrap()
                .canonical_bytes(),
            e.canonical_bytes()
        );
        let mut invalid = profile();
        invalid.id.clear();
        let cancel = Cancellation::default();
        cancel.cancel();
        let mut provider = Script::default();
        assert_eq!(
            play::execute_traced_with_memory(
                &mut e,
                receipt.request(),
                &mut provider,
                &cancel,
                &invalid,
                None,
                Some(&retained)
            )
            .unwrap(),
            receipt
        );
        assert!(provider.seen.is_empty());
        assert_eq!(
            Engine::new(seed).unwrap().commit_prepared(&receipt),
            Err(Error::Narration)
        );
    }
}

#[test]
fn new_context_record_replays_exactly_and_rejects_closed_binding_version_and_bound_tampering() {
    let base = engine();
    let mut e = base.clone();
    let request = wait_request(&e, "current");
    let mut provider = wait_script(0);
    let receipt = play::execute(
        &mut e,
        &request,
        &mut provider,
        &Cancellation::default(),
        &profile(),
    )
    .unwrap();
    let json = serde_json::to_value(&receipt).unwrap();
    let restored = Engine::restore(base.seed().clone(), &[json.to_string()]).unwrap();
    assert_eq!(restored.receipts(), e.receipts());
    assert_eq!(
        Engine::replay(base.seed().clone(), e.receipts())
            .unwrap()
            .canonical_bytes(),
        e.canonical_bytes()
    );
    assert_eq!(base.clone().commit_prepared(&receipt).unwrap(), receipt);
    let mut invalid_profile = profile();
    invalid_profile.id.clear();
    let mut no_model = Script::default();
    assert_eq!(
        play::execute(
            &mut e,
            &request,
            &mut no_model,
            &Cancellation::default(),
            &invalid_profile
        )
        .unwrap(),
        receipt
    );
    assert!(no_model.seen.is_empty());
    let mutations = [
        ("/play/context/version", json!(3)),
        ("/play/context/compiler_version", json!(3)),
        ("/play/context/head", json!(1)),
        ("/play/context/observer", json!("mira")),
        ("/play/context/source_fallback_reason", json!("unknown")),
        ("/play/context/scope/story", json!("other")),
        ("/play/context/coverage/mode", json!("untrusted")),
        (
            "/play/context/coverage/set_fallback_reason",
            json!("unknown"),
        ),
        ("/play/context/coverage/packets_fell_back", json!(33)),
        ("/play/context/coverage/cached_event_candidates", json!(1)),
        ("/play/context/coverage/raw_delta_after", json!(1)),
        (
            "/play/context/coverage/raw_event_candidates",
            json!(u64::MAX),
        ),
        ("/play/context", Value::Null),
        ("/play/prompt_version", json!("locallore-play-v2.6")),
    ];
    for (pointer, value) in mutations {
        let mut bad = json.clone();
        *bad.pointer_mut(pointer).unwrap() = value;
        assert_eq!(
            Engine::restore(base.seed().clone(), &[bad.to_string()]).err(),
            Some(Error::CorruptHistory),
            "{pointer}"
        );
    }
    let mut missing = json.clone();
    missing["play"].as_object_mut().unwrap().remove("context");
    assert_eq!(
        Engine::restore(base.seed().clone(), &[missing.to_string()]).err(),
        Some(Error::CorruptHistory)
    );
    let fixture: Value =
        serde_json::from_str(include_str!("fixtures/accepted_play_v2_3.json")).unwrap();
    let mut old = fixture["receipt"].clone();
    old["play"]["context"] = json["play"]["context"].clone();
    assert_eq!(
        Engine::restore(
            serde_json::from_value(fixture["seed"].clone()).unwrap(),
            &[old.to_string()]
        )
        .err(),
        Some(Error::CorruptHistory)
    );
}

#[test]
fn all_snapshot_raw_reasons_remain_distinct_from_actual_compiler_missing() {
    use memory::FallbackReason as F;
    use play::PlayMemoryFallback as P;
    let base = engine();
    let request = wait_request(&base, "source-reason");
    let mut reference = base.clone();
    let mut raw = wait_script(0);
    play::execute(
        &mut reference,
        &request,
        &mut raw,
        &Cancellation::default(),
        &profile(),
    )
    .unwrap();
    for (reason, expected) in [
        (F::Missing, P::Missing),
        (F::Budget, P::Budget),
        (F::Malformed, P::Malformed),
        (F::Unsupported, P::Unsupported),
        (F::Binding, P::Binding),
        (F::Gap, P::Gap),
        (F::Overlap, P::Overlap),
        (F::OpenTailBeforeEnd, P::OpenTailBeforeEnd),
        (F::UnprovableClosure, P::UnprovableClosure),
        (F::SourceMismatch, P::SourceMismatch),
    ] {
        let mut e = base.clone();
        let mut provider = wait_script(0);
        let receipt = play::execute_traced_with_coverage(
            &mut e,
            &request,
            &mut provider,
            &Cancellation::default(),
            &profile(),
            None,
            &memory::CoverageRead::RawFallback(reason),
        )
        .unwrap();
        let context = receipt.play().unwrap().context.as_ref().unwrap();
        assert_eq!(context.source_fallback_reason, Some(expected));
        assert_eq!(context.coverage.mode, play::PlayCoverageMode::Raw);
        assert_eq!(
            context.coverage.set_fallback_reason,
            Some(P::Missing),
            "compiler actually received None"
        );
        assert_eq!(context.coverage.cached_event_candidates, 0);
        assert_eq!(prompt(&provider, "director"), prompt(&raw, "director"));
        assert_eq!(e.canonical_bytes(), reference.canonical_bytes());
        let restored = Engine::restore(
            base.seed().clone(),
            &[serde_json::to_string(&receipt).unwrap()],
        )
        .unwrap();
        assert_eq!(restored.receipts(), e.receipts());
    }
}

#[test]
fn snapshot_verified_entry_uses_identical_proof_path_and_retry_ignores_new_source_reason() {
    let mut base = engine();
    commit(&mut base, "prefix", vec![say("accepted", "mira")]);
    let retained = proof(&base, "player");
    let read = memory::CoverageRead::Verified(proof(&base, "player"));
    let request = wait_request(&base, "verified-entry");
    let mut first = base.clone();
    let mut second = base.clone();
    let mut p1 = wait_script(1);
    let mut p2 = wait_script(1);
    let r1 = play::execute_traced_with_memory(
        &mut first,
        &request,
        &mut p1,
        &Cancellation::default(),
        &profile(),
        None,
        Some(&retained),
    )
    .unwrap();
    let r2 = play::execute_traced_with_coverage(
        &mut second,
        &request,
        &mut p2,
        &Cancellation::default(),
        &profile(),
        None,
        &read,
    )
    .unwrap();
    assert_eq!(r1.play().unwrap().context, r2.play().unwrap().context);
    assert_eq!(prompt(&p1, "director"), prompt(&p2, "director"));
    assert_eq!(first.canonical_bytes(), second.canonical_bytes());
    assert!(r2
        .play()
        .unwrap()
        .context
        .as_ref()
        .unwrap()
        .source_fallback_reason
        .is_none());
    let mut invalid = profile();
    invalid.id.clear();
    let cancel = Cancellation::default();
    cancel.cancel();
    let mut no_model = Script::default();
    assert_eq!(
        play::execute_traced_with_coverage(
            &mut second,
            &request,
            &mut no_model,
            &cancel,
            &invalid,
            None,
            &memory::CoverageRead::RawFallback(memory::FallbackReason::Malformed)
        )
        .unwrap(),
        r2
    );
    assert!(no_model.seen.is_empty());
}

/// Run only on original 2.3 production; prints public synthetic hashes, no writer.
#[test]
#[ignore = "original-source compact serialization measurement, requires 2.3 checkout"]
fn original_source_compact_receipt_hash_probe() {
    use sha2::{Digest, Sha256};
    assert_eq!(play::PROMPT_VERSION, "locallore-play-v2.3");
    for text in [
        include_str!("fixtures/accepted_play_v2_1.json"),
        include_str!("fixtures/accepted_play_v2_2.json"),
        include_str!("fixtures/accepted_play_v2_3.json"),
    ] {
        let fixture: Value = serde_json::from_str(text).unwrap();
        let restored = Engine::restore(
            serde_json::from_value(fixture["seed"].clone()).unwrap(),
            &[fixture["receipt"].to_string()],
        )
        .unwrap();
        let receipt = &restored.receipts()[0];
        assert_eq!(serde_json::to_value(receipt).unwrap(), fixture["receipt"]);
        let bytes = serde_json::to_vec(receipt).unwrap();
        println!(
            "original {} bytes={} sha256={:x}",
            receipt.play().unwrap().prompt_version,
            bytes.len(),
            Sha256::digest(&bytes)
        );
    }
}
