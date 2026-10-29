// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
#![cfg(test)]
//! Independent FIRST oracle freeze after contract 5a4bdaa5. SOURCE ONLY / UNRUN.
//! Root registers this child only after its retained-native render gate. Missing
//! diagnostic types/methods are SETUP, not a behavioral RED. Original synthetic
//! data only: real Domain1 Engine/Play, recording provider and real TraceRing.
use crate::{
    contracts::*,
    engine::Engine,
    inference::{Cancellation, GenerationRequest, InferenceProvider, Input},
    memory_coverage::{CoverageRead, FallbackReason},
    play::{self, PlayContextPolicy, PlayProfile},
    story_presentation::{StoryPresentationV1, StoryTone},
    turn_trace::{
        AttemptHandle, AttemptIdentity, Config, ErrorCategory, HookStatus,
        NarrationRejectionReasonV1 as Reason, NarrationValidationDiagnosticV1 as Diagnostic,
        Outcome, Provenance, Reader, RingSink, Selection, Stage, StageMeasurement,
        TraceOwner, TraceRing, TraceSink,
    },
};
use serde_json::{json, Value};
use std::{cell::Cell, collections::VecDeque, sync::{Arc, Mutex}, task::Poll};

const FIRST_PERSON: &str = "You pause while we count the ripples.";
const UNAPPROVED_MOVE: &str = "You walk toward the archway.";
const ORDINARY: &str = "You pause briefly.";
const HIDDEN: &str = "SYNTHETIC_DIAGNOSTIC_PRIVATE_PAYLOAD_824";

#[derive(Clone, Copy, Debug)]
enum Policy { SceneMemory, SceneLiteral, LegacyMemory, LegacyLiteral }
fn scene_policies() -> [Policy; 2] { [Policy::SceneMemory, Policy::SceneLiteral] }
fn recipe(policy: Policy) -> super::SceneRecipeV1 {
    match policy {
        Policy::SceneMemory => super::SceneRecipeV1::Memory(PlayContextPolicy::StateRelevantMemoryV1),
        Policy::SceneLiteral => super::SceneRecipeV1::LiteralV1,
        _ => panic!("a scene recipe is required"),
    }
}
fn fixture(excluded: Option<&str>) -> Engine {
    let mut seed: Seed = serde_json::from_str(include_str!(
        "../../../../../fixtures/lantern_quay.json"
    )).unwrap();
    seed.facts.get_mut("ancestry").unwrap().proposition = HIDDEN.into();
    seed.presentation = excluded.map(|phrase| StoryPresentationV1 {
        version: 1, tone: StoryTone::Warm, excluded_phrases: vec![phrase.into()],
    });
    Engine::new(seed).unwrap()
}
fn profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-diagnostic-freeze".into(), model_sha256: "a".repeat(64),
        runtime_revision: "b".repeat(40), template_sha256: "c".repeat(64),
        worker_sha256: "d".repeat(64), profile_manifest_sha256: "e".repeat(64),
        context_tokens: 4096, director_tokens: 350, narrator_tokens: 350,
        deadline_ms: 5000, repair_limit: 1,
    }
}
fn request(engine: &Engine, text: &str) -> Request {
    engine.request("diagnostic-freeze", Intent::FreeText {
        kind: PlayInputKind::Action, text: text.into(),
    })
}
fn narration(text: &str) -> Vec<u8> {
    serde_json::to_vec(&json!({"text":text,"event_ids":[1],"speaker":"narrator"})).unwrap()
}
struct Script { replies: VecDeque<Vec<u8>>, seen: Vec<GenerationRequest> }
impl Script {
    fn new(command: Command, narrator: Vec<u8>) -> Self {
        Self { replies: [serde_json::to_vec(&json!({"commands":[command]})).unwrap(), narrator]
            .into_iter().collect(), seen: vec![] }
    }
    fn wait(text: &str) -> Self { Self::new(Command::Wait { ticks: 1 }, narration(text)) }
}
impl InferenceProvider for Script {
    fn poll(&mut self, generation: &GenerationRequest, cancel: &Cancellation)
        -> Poll<Result<Vec<u8>, Error>> {
        self.seen.push(generation.clone());
        Poll::Ready(if cancel.is_cancelled() { Err(Error::Cancelled) }
            else { self.replies.pop_front().ok_or(Error::Provider) })
    }
}
fn execute(policy: Policy, engine: &mut Engine, request: &Request, script: &mut Script,
    cancel: &Cancellation, sink: Option<&mut dyn TraceSink>) -> Result<Receipt, Error> {
    match policy {
        Policy::LegacyMemory => play::execute_traced(engine, request, script, cancel, &profile(), sink),
        Policy::LegacyLiteral => play::execute_traced_with_literal_director_v1(
            engine, request, script, cancel, &profile(), sink),
        _ => {
            let coverage = CoverageRead::RawFallback(FallbackReason::Missing);
            play::execute_traced_with_scene_recipe_v1(engine, request, script, cancel,
                &profile(), sink, super::ScenePlayConstructionInput {
                    recipe: recipe(policy), coverage: if matches!(policy, Policy::SceneMemory) {
                        Some(&coverage)
                    } else { None },
                })
        }
    }
}
fn identity(request: &Request) -> AttemptIdentity {
    AttemptIdentity { scope: request.scope.clone(), base_revision: request.expected_revision,
        observer: "player".into(), turn: request.turn.clone(), attempt: 0 }
}
fn selection(identity: &AttemptIdentity) -> Selection {
    Selection { scope: identity.scope.clone(), base_revision: identity.base_revision,
        observer: identity.observer.clone(), turn: Some(identity.turn.clone()), attempt: Some(0) }
}
fn unchanged(engine: &Engine, before: &Engine) {
    assert_eq!(engine.seed(), before.seed());
    assert_eq!(engine.canonical_records(), before.canonical_records());
    assert_eq!(engine.canonical_bytes(), before.canonical_bytes());
    assert_eq!(engine.accepted_history_basis().unwrap(), before.accepted_history_basis().unwrap());
}
// Independent executions have real measured timing metadata. Normalize ONLY
// these documented elapsed_ms values, leaving stage names/count/order intact.
// Same-Engine retry/cancel/replay assertions below do NOT use this helper.
fn stable_receipt(receipt: &Receipt) -> Value {
    let mut value = serde_json::to_value(receipt).unwrap();
    for stage in value["play"]["stages"].as_array_mut().unwrap() {
        assert!(stage["elapsed_ms"].as_u64().unwrap() <= 120_000);
        stage["elapsed_ms"] = json!(0);
    }
    value
}
fn stable_requests(script: &Script) -> Vec<Value> {
    for pair in script.seen.windows(2) {
        assert!(pair[1].budget.deadline_ms <= pair[0].budget.deadline_ms,
            "the existing turn deadline must not reset between roles");
    }
    script.seen.iter().map(|request| {
        assert!(request.budget.deadline_ms > 0 && request.budget.deadline_ms <= profile().deadline_ms);
        let Input::Structured { role, prompt, schema } = &request.input else {
            panic!("actual structured Play request required")
        };
        json!({"version":request.version,"scope":request.scope,"turn":request.turn,
            "revision":request.revision,"model_profile":request.model_profile,"schema_id":request.schema,
            "role":role,"prompt":prompt,"schema":schema,
            "max_output_bytes":request.budget.max_output_bytes,
            "max_output_tokens":request.budget.max_output_tokens,
            "max_pending_polls":request.budget.max_pending_polls})
    }).collect()
}
fn parity(engine: &Engine, receipt: &Receipt, script: &Script,
    expected_engine: &Engine, expected_receipt: &Receipt, expected_script: &Script) {
    assert_eq!(engine.seed(), expected_engine.seed());
    assert_eq!(engine.scope(), expected_engine.scope());
    assert_eq!(engine.revision(), expected_engine.revision());
    assert_eq!(serde_json::to_value(engine.state()).unwrap(), serde_json::to_value(expected_engine.state()).unwrap());
    assert_eq!(receipt.events(), expected_receipt.events());
    assert_eq!(stable_receipt(receipt), stable_receipt(expected_receipt));
    assert_eq!(stable_requests(script), stable_requests(expected_script));
    assert_eq!(script.seen.len(), 2, "no diagnostic repair/provider call");
}

#[derive(Clone, Copy, PartialEq, Eq)]
enum Mode { Passive, CancelStage, CancelDiagnostic, PanicStage, PanicDiagnostic }
struct Probe {
    ring: TraceRing, handle: AttemptHandle, identity: AttemptIdentity,
    cancel: Cancellation, mode: Mode, diagnostics: Vec<Diagnostic>,
    stages: Vec<(Stage, Outcome, Option<ErrorCategory>)>, preceding: Vec<Stage>,
    faults: Vec<&'static str>, panic_fired: bool, calls_after_panic: usize,
}
impl Probe {
    fn new(request: &Request, cancel: Cancellation, mode: Mode) -> Self {
        let identity = identity(request);
        let mut ring = TraceRing::new(Config::default());
        ring.set_enabled(true);
        let handle = ring.begin(identity.clone(), Provenance::default()).handle.unwrap();
        Self { ring, handle, identity, cancel, mode, diagnostics: vec![], stages: vec![],
            preceding: vec![], faults: vec![], panic_fired: false, calls_after_panic: 0 }
    }
    fn assert_healthy(&self) {
        assert!(self.faults.is_empty(), "trace setup faults: {:?}", self.faults);
        assert_eq!(self.calls_after_panic, 0, "panicking sink must stay disabled");
    }
    fn decision(&self, outcome: Outcome, error: Option<ErrorCategory>, reason: Option<Reason>) {
        self.assert_healthy();
        assert_eq!(self.diagnostics.len(), 1, "exactly one actual validation decision");
        assert_eq!(self.preceding, vec![Stage::NarrationValidation]);
        let value = self.diagnostics[0];
        assert_eq!(value.version(), 1);
        assert_eq!(value.outcome(), outcome);
        assert_eq!(value.error(), error);
        assert_eq!(value.reason(), reason);
    }
}
impl TraceSink for Probe {
    fn matches(&mut self, scope: &Scope, revision: u64, observer: &str, turn: &str) -> bool {
        self.identity.scope == *scope && self.identity.base_revision == revision
            && self.identity.observer == observer && self.identity.turn == turn
    }
    fn record(&mut self, measurement: StageMeasurement) {
        if self.panic_fired { self.calls_after_panic += 1; }
        if self.ring.record_measured(&self.handle, measurement) != HookStatus::Recorded {
            self.faults.push("stage not recorded"); return;
        }
        let snapshot = self.ring.read(&selection(&self.identity),
            &Reader::scoped(self.identity.scope.clone(), self.identity.observer.clone())).unwrap();
        let stage = snapshot.attempts[0].stages.last().unwrap();
        self.stages.push((stage.stage, stage.outcome, stage.error));
        if stage.stage == Stage::NarrationValidation {
            if self.mode == Mode::CancelStage { self.cancel.cancel(); }
            if self.mode == Mode::PanicStage {
                self.panic_fired = true;
                panic!("fixed synthetic stage observer panic");
            }
        }
    }
    fn capture(&mut self, _artifact: crate::turn_capture::Artifact<'_>) {
        if self.panic_fired { self.calls_after_panic += 1; }
    }
    fn narration_validation(&mut self, diagnostic: Diagnostic) {
        if self.panic_fired { self.calls_after_panic += 1; }
        if self.diagnostics.len() >= 1 { self.faults.push("duplicate validation event"); }
        if let Some((stage, _, _)) = self.stages.last() { self.preceding.push(*stage); }
        self.diagnostics.push(diagnostic);
        if self.mode == Mode::CancelDiagnostic { self.cancel.cancel(); }
        if self.mode == Mode::PanicDiagnostic {
            self.panic_fired = true;
            panic!("fixed synthetic diagnostic observer panic");
        }
    }
}

// Intentionally does NOT implement the new provided method.
struct DefaultSink { inner: RingSink, records: usize }
impl DefaultSink {
    fn new(request: &Request, disabled: bool, retired: bool) -> Self {
        let owner = TraceOwner::default();
        let mut ring = TraceRing::new(Config::default());
        ring.set_enabled(true);
        let handle = ring.begin_for_owner(&owner, identity(request), Provenance::default()).handle.unwrap();
        if disabled { ring.set_enabled(false); }
        if retired { ring.clear_owner(&owner); }
        Self { inner: RingSink::new(Arc::new(Mutex::new(ring)), handle), records: 0 }
    }
}
impl TraceSink for DefaultSink {
    fn matches(&mut self, scope: &Scope, revision: u64, observer: &str, turn: &str) -> bool {
        self.inner.matches(scope, revision, observer, turn)
    }
    fn record(&mut self, measurement: StageMeasurement) {
        self.records += 1; self.inner.record(measurement);
    }
}
struct ExplicitNoop { default: DefaultSink, calls: usize }
impl TraceSink for ExplicitNoop {
    fn matches(&mut self, scope: &Scope, revision: u64, observer: &str, turn: &str) -> bool {
        self.default.matches(scope, revision, observer, turn)
    }
    fn record(&mut self, measurement: StageMeasurement) { self.default.record(measurement); }
    fn narration_validation(&mut self, _diagnostic: Diagnostic) { self.calls += 1; }
}

#[test]
fn provided_default_explicit_noop_disabled_and_retired_sink_parity() {
    for policy in scene_policies() { for text in [ORDINARY, FIRST_PERSON] {
        let original = fixture(None);
        let request = request(&original, "I wait for one tide tick.");
        let mut baseline = original.clone(); let mut baseline_script = Script::wait(text);
        let baseline_receipt = execute(policy, &mut baseline, &request, &mut baseline_script,
            &Cancellation::default(), None).unwrap();
        for (disabled, retired) in [(false, false), (true, false), (false, true)] {
            let mut engine = original.clone(); let mut script = Script::wait(text);
            let mut sink = DefaultSink::new(&request, disabled, retired);
            let receipt = execute(policy, &mut engine, &request, &mut script,
                &Cancellation::default(), Some(&mut sink)).unwrap();
            parity(&engine, &receipt, &script, &baseline, &baseline_receipt, &baseline_script);
            assert_eq!(sink.records == 0, disabled || retired);
        }
        let mut engine = original.clone(); let mut script = Script::wait(text);
        let mut sink = ExplicitNoop { default: DefaultSink::new(&request, false, false), calls: 0 };
        let receipt = execute(policy, &mut engine, &request, &mut script,
            &Cancellation::default(), Some(&mut sink)).unwrap();
        assert_eq!(sink.calls, 1);
        parity(&engine, &receipt, &script, &baseline, &baseline_receipt, &baseline_script);
        let mut engine = original.clone(); let mut script = Script::wait(text);
        let mut sink = Probe::new(&request, Cancellation::default(), Mode::Passive);
        sink.identity.turn = "different-native-attempt".into();
        let receipt = execute(policy, &mut engine, &request, &mut script,
            &Cancellation::default(), Some(&mut sink)).unwrap();
        assert!(sink.stages.is_empty() && sink.diagnostics.is_empty());
        parity(&engine, &receipt, &script, &baseline, &baseline_receipt, &baseline_script);
    }}
}

#[test]
fn actual_reached_scene_rules_and_original_first_failure_order() {
    for policy in scene_policies() {
        for (text, reason) in [(FIRST_PERSON, Reason::SceneFirstPerson),
            (UNAPPROVED_MOVE, Reason::SceneUnapprovedMovement),
            ("You walk while we count.", Reason::SceneFirstPerson)] {
            let mut engine = fixture(None); let request = request(&engine, "I wait for one tide tick.");
            let mut script = Script::wait(text);
            let mut sink = Probe::new(&request, Cancellation::default(), Mode::Passive);
            let receipt = execute(policy, &mut engine, &request, &mut script,
                &Cancellation::default(), Some(&mut sink)).unwrap();
            sink.decision(Outcome::Rejected, Some(ErrorCategory::Narration), Some(reason));
            assert!(receipt.play().unwrap().fallback);
            assert_eq!(receipt.narration(), crate::engine::render(receipt.events()));
            assert_eq!(script.seen.len(), 2);
        }
        let mut engine = fixture(None); let request = request(&engine, "I move to pier.");
        let mut script = Script::new(Command::Move { to: "pier".into() }, narration("You walk toward the pier."));
        let mut sink = Probe::new(&request, Cancellation::default(), Mode::Passive);
        let receipt = execute(policy, &mut engine, &request, &mut script,
            &Cancellation::default(), Some(&mut sink)).unwrap();
        sink.decision(Outcome::Accepted, None, None);
        assert!(!receipt.play().unwrap().fallback);
        assert_eq!(script.seen.len(), 2);
    }
}

#[test]
fn earlier_generic_rejection_and_actual_parse_failure_are_not_posthoc_scene_codes() {
    let cases = [
        narration("You say my line."),
        serde_json::to_vec(&json!({"text":FIRST_PERSON,"event_ids":[1],"speaker":"someone"})).unwrap(),
        serde_json::to_vec(&json!({"text":FIRST_PERSON,"event_ids":[99],"speaker":"narrator"})).unwrap(),
        narration(""), b"synthetic non-json output".to_vec(),
    ];
    for policy in scene_policies() { for (index, bytes) in cases.iter().enumerate() {
        let mut engine = fixture(None); let request = request(&engine, "I wait for one tide tick.");
        let mut script = Script::new(Command::Wait { ticks: 1 }, bytes.clone());
        let mut sink = Probe::new(&request, Cancellation::default(), Mode::Passive);
        let receipt = execute(policy, &mut engine, &request, &mut script,
            &Cancellation::default(), Some(&mut sink)).unwrap();
        sink.decision(Outcome::Rejected, Some(ErrorCategory::Narration), Some(Reason::Unclassified));
        assert!(receipt.play().unwrap().fallback);
        assert_eq!(receipt.narration(), crate::engine::render(receipt.events()));
        assert_eq!(script.seen.len(), 2);
        if index == 4 {
            assert!(sink.stages.contains(&(Stage::Parsing, Outcome::Rejected, Some(ErrorCategory::Malformed))));
        }
    }
        // A real non-Narration validation failure must keep its category, not
        // acquire an inferred scene reason or the mentioned private actor ID.
        let mut engine = fixture(None); let request = request(&engine, "I wait for one tide tick.");
        let mut script = Script::wait("You notice oren nearby.");
        let mut sink = Probe::new(&request, Cancellation::default(), Mode::Passive);
        let receipt = execute(policy, &mut engine, &request, &mut script,
            &Cancellation::default(), Some(&mut sink)).unwrap();
        sink.decision(Outcome::Rejected, Some(ErrorCategory::Knowledge), None);
        assert!(!format!("{:?}", sink.diagnostics[0]).contains("oren"));
        assert!(receipt.play().unwrap().fallback);
        assert_eq!(script.seen.len(), 2);
    }
}

#[test]
fn accepted_none_reason_includes_an_explicit_known_finite_semantic_gap() {
    // An original synthetic ungrounded environmental event, NOT copied model
    // prose. Acceptance here characterizes the existing finite guard's gap;
    // it is neither desirable prose nor semantic/quality approval.
    let unsupported = "An unnamed cart rolls through an unlisted plaza.";
    for policy in scene_policies() { for text in [ORDINARY, unsupported] {
        let mut engine = fixture(None); let request = request(&engine, "I wait for one tide tick.");
        let mut script = Script::wait(text);
        let mut sink = Probe::new(&request, Cancellation::default(), Mode::Passive);
        let receipt = execute(policy, &mut engine, &request, &mut script,
            &Cancellation::default(), Some(&mut sink)).unwrap();
        sink.decision(Outcome::Accepted, None, None);
        assert!(!receipt.play().unwrap().fallback);
        assert_eq!(receipt.narration(), text);
        assert_eq!(receipt.events().len(), 1);
        assert_eq!(engine.revision(), 1);
        assert_eq!(script.seen.len(), 2);
    }}
}

fn excluded_summary() -> String {
    let engine = fixture(None); let request = request(&engine, "I wait for one tide tick.");
    let proposal = Proposal { version: VERSION, scope: request.scope.clone(), turn: request.turn.clone(),
        expected_revision: 0, commands: vec![Command::Wait { ticks: 1 }] };
    engine.stage_play_v25(&request, &proposal, &|| false).unwrap().approved().narration().into()
}

#[test]
fn stage_and_new_hook_cancellation_precede_excluded_mechanical_fallback() {
    for policy in scene_policies() { for mode in [Mode::CancelStage, Mode::CancelDiagnostic] {
        let mut engine = fixture(Some(&excluded_summary())); let before = engine.clone();
        let request = request(&engine, "I wait for one tide tick.");
        let cancel = Cancellation::default(); let mut script = Script::wait(FIRST_PERSON);
        let mut sink = Probe::new(&request, cancel.clone(), mode);
        let result = execute(policy, &mut engine, &request, &mut script, &cancel, Some(&mut sink));
        assert_eq!(result, Err(Error::Cancelled));
        assert!(cancel.is_cancelled());
        sink.decision(Outcome::Rejected, Some(ErrorCategory::Narration), Some(Reason::SceneFirstPerson));
        assert_eq!(script.seen.len(), 2);
        unchanged(&engine, &before);
    }}
}

#[test]
fn accepted_validation_callback_can_cancel_before_commit_without_relabeling_decision() {
    for policy in scene_policies() {
        let mut engine = fixture(None); let before = engine.clone();
        let request = request(&engine, "I wait for one tide tick.");
        let cancel = Cancellation::default(); let mut script = Script::wait(ORDINARY);
        let mut sink = Probe::new(&request, cancel.clone(), Mode::CancelDiagnostic);
        let result = execute(policy, &mut engine, &request, &mut script, &cancel, Some(&mut sink));
        assert_eq!(result, Err(Error::Cancelled));
        sink.decision(Outcome::Accepted, None, None);
        assert_eq!(script.seen.len(), 2);
        unchanged(&engine, &before);
    }
}

#[test]
fn stage_and_diagnostic_panics_disable_sink_without_changing_fallback_or_call_caps() {
    for policy in scene_policies() {
        let original = fixture(None); let request = request(&original, "I wait for one tide tick.");
        let mut baseline = original.clone(); let mut baseline_script = Script::wait(FIRST_PERSON);
        let baseline_receipt = execute(policy, &mut baseline, &request, &mut baseline_script,
            &Cancellation::default(), None).unwrap();
        for mode in [Mode::PanicStage, Mode::PanicDiagnostic] {
            let mut engine = original.clone(); let mut script = Script::wait(FIRST_PERSON);
            let mut sink = Probe::new(&request, Cancellation::default(), mode);
            let receipt = execute(policy, &mut engine, &request, &mut script,
                &Cancellation::default(), Some(&mut sink)).unwrap();
            sink.assert_healthy(); assert!(sink.panic_fired);
            assert!(receipt.play().unwrap().fallback);
            assert_eq!(sink.diagnostics.len(), usize::from(mode == Mode::PanicDiagnostic));
            assert_eq!(sink.stages.last().unwrap().0, Stage::NarrationValidation);
            parity(&engine, &receipt, &script, &baseline, &baseline_receipt, &baseline_script);
        }
    }
}

#[test]
fn detailed_and_compatibility_helpers_keep_the_existing_cancel_predicate_count() {
    // Public token APIs do not expose predicate-call counts. This one private
    // child case borrows an actual native bound record produced by real Play;
    // it requires the proposed internal helper, never a fake Engine/report.
    let source = fixture(None); let source_before = source.clone(); let mut engine = source.clone();
    let request = request(&source, "I wait for one tide tick.");
    let mut script = Script::wait(ORDINARY);
    let receipt = execute(Policy::SceneMemory, &mut engine, &request, &mut script,
        &Cancellation::default(), None).unwrap();
    let stage = source.stage_scene_play_v1(&request, receipt.proposal(), &|| false).unwrap();
    let bound = source.bind_scene_play_v1(stage, recipe(Policy::SceneMemory), &|| false).unwrap();
    let valid = receipt.play().unwrap().clone();
    for detailed in [false, true] {
        for (text, expected_calls, expected) in [(ORDINARY, 2, Ok(())),
            (FIRST_PERSON, 1, Err(Error::Narration)),
            (UNAPPROVED_MOVE, 1, Err(Error::Narration))] {
            let mut record = valid.clone(); record.narration.text = text.into();
            let calls = Cell::new(0);
            let cancel = || { calls.set(calls.get() + 1); false };
            let result = if detailed {
                super::validate_record_detailed(&source, &bound, &record, &cancel)
                    .map_err(|failure| failure.into_engine_error())
            } else { super::validate_record(&source, &bound, &record, &cancel) };
            assert_eq!(result, expected);
            assert_eq!(calls.get(), expected_calls, "one pass, original check order");
            unchanged(&source, &source_before);
        }
        let calls = Cell::new(0);
        let cancel = || { calls.set(calls.get() + 1); calls.get() == 2 };
        let result = if detailed {
            super::validate_record_detailed(&source, &bound, &valid, &cancel)
                .map_err(|failure| failure.into_engine_error())
        } else { super::validate_record(&source, &bound, &valid, &cancel) };
        assert_eq!(result, Err(Error::Cancelled));
        assert_eq!(calls.get(), 2, "no diagnostic predicate re-probe");
    }
    assert_eq!(script.seen.len(), 2);
}

#[test]
fn guard_stale_retry_replay_and_legacy_do_not_fabricate_scene_diagnostics() {
    for policy in scene_policies() {
        for stale in [false, true] {
            let mut engine = fixture(None); let before = engine.clone();
            let mut request = request(&engine, if stale { "I wait for one tide tick." } else { "I use blink." });
            if stale { request.expected_revision = 99; }
            let mut script = Script::wait(ORDINARY);
            let mut sink = Probe::new(&request, Cancellation::default(), Mode::Passive);
            assert_eq!(execute(policy, &mut engine, &request, &mut script,
                &Cancellation::default(), Some(&mut sink)),
                Err(if stale { Error::Stale } else { Error::Ability }));
            assert!(script.seen.is_empty() && sink.diagnostics.is_empty());
            unchanged(&engine, &before);
        }
        let mut engine = fixture(None); let request = request(&engine, "I wait for one tide tick.");
        let cancel = Cancellation::default(); let mut script = Script::wait(ORDINARY);
        let mut sink = Probe::new(&request, cancel.clone(), Mode::Passive);
        let receipt = execute(policy, &mut engine, &request, &mut script, &cancel, Some(&mut sink)).unwrap();
        sink.decision(Outcome::Accepted, None, None);
        let before = engine.clone(); let receipt_bytes = serde_json::to_vec(&receipt).unwrap();
        let stage_count = sink.stages.len(); cancel.cancel();
        let retry = execute(policy, &mut engine, &request, &mut script, &cancel, Some(&mut sink)).unwrap();
        assert_eq!(serde_json::to_vec(&retry).unwrap(), receipt_bytes);
        assert_eq!(script.seen.len(), 2); assert_eq!(sink.stages.len(), stage_count);
        assert_eq!(sink.diagnostics.len(), 1);
        unchanged(&engine, &before);
        let replayed = Engine::replay_records(engine.seed().clone(), engine.canonical_records()).unwrap();
        unchanged(&replayed, &engine);
    }
    for policy in [Policy::LegacyMemory, Policy::LegacyLiteral] {
        let mut engine = fixture(None); let request = request(&engine, "I wait for one tide tick.");
        let mut script = Script::wait(FIRST_PERSON);
        let mut sink = Probe::new(&request, Cancellation::default(), Mode::Passive);
        let receipt = execute(policy, &mut engine, &request, &mut script,
            &Cancellation::default(), Some(&mut sink)).unwrap();
        sink.decision(Outcome::Accepted, None, None);
        assert!(!receipt.play().unwrap().fallback);
        assert!(receipt.play().unwrap().scene.is_none());
        assert_eq!(script.seen.len(), 2);
    }
}

#[test]
fn native_metadata_is_copy_small_content_free_and_old_wire_keys_stay_exact() {
    fn copy_eq<T: Copy + Eq>() {}
    copy_eq::<Diagnostic>(); copy_eq::<Reason>();
    assert!(std::mem::size_of::<Diagnostic>() <= 64);
    for policy in scene_policies() {
        let mut engine = fixture(None); let request = request(&engine, "I wait for one tide tick.");
        let mut script = Script::wait(FIRST_PERSON);
        let mut sink = Probe::new(&request, Cancellation::default(), Mode::Passive);
        let receipt = execute(policy, &mut engine, &request, &mut script,
            &Cancellation::default(), Some(&mut sink)).unwrap();
        sink.decision(Outcome::Rejected, Some(ErrorCategory::Narration), Some(Reason::SceneFirstPerson));
        let diagnostic = sink.diagnostics[0];
        let description = format!("{diagnostic:?}");
        assert!(description.len() <= 256 && !description.contains(HIDDEN));
        assert!(!description.contains(FIRST_PERSON) && !description.contains(&request.turn));
        // A consumer can recognize its known code and keep a wildcard for the
        // append-only enum, without an unreachable-pattern warning in Core.
        let consumer_label = match diagnostic.reason() {
            Some(Reason::SceneFirstPerson) => "first_person",
            _ => "other_or_future",
        };
        assert_eq!(consumer_label, "first_person");
        let record = serde_json::to_value(receipt.play().unwrap()).unwrap();
        assert_eq!(record["policy"], super::SCENE_NARRATION_POLICY_V1);
        assert_eq!(record["prompt_version"], if matches!(policy, Policy::SceneMemory) {
            super::SCENE_PROMPT_VERSION_V1
        } else { super::LITERAL_SCENE_PROMPT_VERSION_V1 });
        assert_eq!(record["scene"]["version"], 1);
        let mut expected = vec!["fallback", "narration", "policy", "profile", "prompt_version",
            "repairs", "scene", "stages", "version"];
        if matches!(policy, Policy::SceneMemory) { expected.extend(["context", "context_policy"]); }
        expected.sort_unstable();
        let mut keys: Vec<_> = record.as_object().unwrap().keys().map(String::as_str).collect();
        keys.sort_unstable(); assert_eq!(keys, expected);
        let snapshot = sink.ring.read(&selection(&sink.identity),
            &Reader::scoped(sink.identity.scope.clone(), sink.identity.observer.clone())).unwrap();
        assert_eq!(snapshot.version, 1); assert!(!snapshot.exact_reconstruction);
        for stage in &snapshot.attempts[0].stages {
            let stage = serde_json::to_value(stage).unwrap();
            let mut keys: Vec<_> = stage.as_object().unwrap().keys().map(String::as_str).collect();
            keys.sort_unstable();
            assert_eq!(keys, vec!["counts", "duration_us", "error", "outcome", "stage", "started_us"]);
        }
    }
}
