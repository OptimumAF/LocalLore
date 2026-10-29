// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent retention oracle FIRST freeze. SOURCE ONLY / UNREGISTERED / UNRUN.
//! Root owns registration and implementation. Missing APIs are SETUP, not RED.
//! Real synthetic Engine/Play emits every diagnostic used here. Explicit private
//! collector controls copy those values; they are not authenticated origin proof.
use super::*;
use crate::{
    contracts::{Command, Error, Intent, PlayInputKind, Receipt, Request, Seed},
    engine::Engine,
    inference::{Cancellation, GenerationRequest, InferenceProvider, Input},
    memory_coverage::{CoverageRead, FallbackReason},
    play::{self, scene_narration, PlayContextPolicy, PlayProfile},
};
use serde_json::{json, Value};
use std::{collections::VecDeque, task::Poll};

type Diagnostic = NarrationValidationDiagnosticV1;
type Read = NarrationValidationReadV1;
type Reason = NarrationRejectionReasonV1;
const ORDINARY: &str = "You rest briefly.";
const FIRST_PERSON: &str = "You rest while we watch the water.";
const MOVEMENT: &str = "You walk toward a low stone arch.";
const PRIVATE: &str = "SYNTHETIC_RETENTION_SECRET_918";

fn fixture() -> Engine {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../../fixtures/lantern_quay.json")).unwrap();
    seed.facts.get_mut("ancestry").unwrap().proposition = PRIVATE.into();
    Engine::new(seed).unwrap()
}
fn profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-retention-freeze".into(),
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
fn request(engine: &Engine, text: &str) -> Request {
    engine.request(
        "retention-freeze",
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: text.into(),
        },
    )
}
fn narration(text: &str) -> Vec<u8> {
    serde_json::to_vec(&json!({"text":text,"event_ids":[1],"speaker":"narrator"})).unwrap()
}
struct Script {
    replies: VecDeque<Vec<u8>>,
    seen: Vec<GenerationRequest>,
}
impl Script {
    fn new(narrator: Vec<u8>) -> Self {
        Self {
            replies: [
                serde_json::to_vec(&json!({"commands":[Command::Wait { ticks: 1 }]})).unwrap(),
                narrator,
            ]
            .into_iter()
            .collect(),
            seen: vec![],
        }
    }
}
impl InferenceProvider for Script {
    fn poll(
        &mut self,
        generation: &GenerationRequest,
        cancel: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        self.seen.push(generation.clone());
        Poll::Ready(if cancel.is_cancelled() {
            Err(Error::Cancelled)
        } else {
            self.replies.pop_front().ok_or(Error::Provider)
        })
    }
}
fn execute(
    literal: bool,
    engine: &mut Engine,
    request: &Request,
    script: &mut Script,
    cancel: &Cancellation,
    sink: Option<&mut dyn TraceSink>,
) -> Result<Receipt, Error> {
    let coverage = CoverageRead::RawFallback(FallbackReason::Missing);
    play::execute_traced_with_scene_recipe_v1(
        engine,
        request,
        script,
        cancel,
        &profile(),
        sink,
        scene_narration::ScenePlayConstructionInput {
            recipe: if literal {
                scene_narration::SceneRecipeV1::LiteralV1
            } else {
                scene_narration::SceneRecipeV1::Memory(PlayContextPolicy::StateRelevantMemoryV1)
            },
            coverage: if literal { None } else { Some(&coverage) },
        },
    )
}
fn identity(request: &Request, attempt: u32) -> AttemptIdentity {
    AttemptIdentity {
        scope: request.scope.clone(),
        base_revision: request.expected_revision,
        observer: "player".into(),
        turn: request.turn.clone(),
        attempt,
    }
}
fn selection(key: &AttemptIdentity) -> Selection {
    Selection {
        scope: key.scope.clone(),
        base_revision: key.base_revision,
        observer: key.observer.clone(),
        turn: Some(key.turn.clone()),
        attempt: Some(key.attempt),
    }
}
fn reader(key: &AttemptIdentity) -> Reader {
    Reader::scoped(key.scope.clone(), key.observer.clone())
}
fn read_key(ring: &TraceRing, owner: &TraceOwner, key: &AttemptIdentity) -> Read {
    ring.read_narration_validation_for_owner(owner, &selection(key), &reader(key))
        .unwrap()
}
fn control(config: Config, key: &AttemptIdentity) -> (TraceRing, TraceOwner, AttemptHandle) {
    let owner = TraceOwner::default();
    let mut ring = TraceRing::new(config);
    ring.set_enabled(true);
    let begun = ring.begin_for_owner(&owner, key.clone(), Provenance::default());
    assert_eq!(begun.status, HookStatus::Recorded);
    (ring, owner, begun.handle.unwrap())
}
// Explicit collector control: supply coarse metadata for an ACTUAL copied
// callback. These controls test storage rules, not Engine or evidence origin.
fn matching_stage(ring: &mut TraceRing, handle: &AttemptHandle, value: Diagnostic) {
    assert_eq!(
        ring.record(
            handle,
            Stage::NarrationValidation,
            value.outcome(),
            Counts::default(),
            value.error()
        ),
        HookStatus::Recorded
    );
}
fn stored_control(
    config: Config,
    key: &AttemptIdentity,
    value: Diagnostic,
) -> (TraceRing, TraceOwner, AttemptHandle) {
    let (mut ring, owner, handle) = control(config, key);
    matching_stage(&mut ring, &handle, value);
    assert_eq!(
        ring.record_narration_validation(&handle, value),
        HookStatus::Recorded
    );
    (ring, owner, handle)
}
fn old_bytes(ring: &TraceRing, owner: &TraceOwner, key: &AttemptIdentity) -> Vec<u8> {
    serde_json::to_vec(
        &ring
            .read_for_owner(owner, &selection(key), &reader(key))
            .unwrap(),
    )
    .unwrap()
}
fn keys(value: &Value) -> Vec<&str> {
    let mut keys: Vec<_> = value
        .as_object()
        .unwrap()
        .keys()
        .map(String::as_str)
        .collect();
    keys.sort_unstable();
    keys
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum Mode {
    Passive,
    Discard,
    CancelStage,
    CancelDiagnostic,
    PanicStage,
    PanicBefore,
    PanicAfter,
    Busy,
    Poison,
}
struct Tap {
    inner: RingSink,
    ring: Arc<Mutex<TraceRing>>,
    mode: Mode,
    cancel: Cancellation,
    values: Vec<Diagnostic>,
    panic_fired: bool,
    calls_after_panic: usize,
}
impl Tap {
    fn new(
        ring: Arc<Mutex<TraceRing>>,
        handle: AttemptHandle,
        cancel: Cancellation,
        mode: Mode,
    ) -> Self {
        Self {
            inner: RingSink::new(ring.clone(), handle),
            ring,
            mode,
            cancel,
            values: vec![],
            panic_fired: false,
            calls_after_panic: 0,
        }
    }
    fn called(&mut self) {
        if self.panic_fired {
            self.calls_after_panic += 1;
        }
    }
    fn fail(&mut self) {
        self.panic_fired = true;
        panic!("fixed synthetic retention observer panic");
    }
}
impl TraceSink for Tap {
    fn matches(&mut self, scope: &Scope, revision: u64, observer: &str, turn: &str) -> bool {
        self.inner.matches(scope, revision, observer, turn)
    }
    fn record(&mut self, measurement: StageMeasurement) {
        self.called();
        let validation = measurement.stage == Stage::NarrationValidation;
        self.inner.record(measurement);
        if validation {
            if self.mode == Mode::CancelStage {
                self.cancel.cancel();
            }
            if self.mode == Mode::PanicStage {
                self.fail();
            }
        }
    }
    fn capture(&mut self, artifact: crate::turn_capture::Artifact<'_>) {
        self.called();
        self.inner.capture(artifact);
    }
    fn narration_validation(&mut self, value: Diagnostic) {
        self.called();
        self.values.push(value);
        if self.mode == Mode::Discard {
            return;
        }
        if self.mode == Mode::PanicBefore {
            self.fail();
        }
        if self.mode == Mode::Busy {
            let ring = self.ring.clone();
            let _held = ring.lock().unwrap();
            self.inner.narration_validation(value);
        } else {
            if self.mode == Mode::Poison {
                let ring = self.ring.clone();
                assert!(std::thread::spawn(move || {
                    let _held = ring.lock().unwrap();
                    panic!("fixed synthetic retention mutex poison");
                })
                .join()
                .is_err());
            }
            self.inner.narration_validation(value);
        }
        if self.mode == Mode::CancelDiagnostic {
            self.cancel.cancel();
        }
        if self.mode == Mode::PanicAfter {
            self.fail();
        }
    }
}
struct PlayRun {
    before: Engine,
    engine: Engine,
    request: Request,
    result: Result<Receipt, Error>,
    script: Script,
    ring: Arc<Mutex<TraceRing>>,
    owner: TraceOwner,
    key: AttemptIdentity,
    tap: Tap,
}
fn run(literal: bool, bytes: Vec<u8>, mode: Mode) -> PlayRun {
    let mut engine = fixture();
    let before = engine.clone();
    let request = request(&engine, "I wait for one tide tick.");
    let key = identity(&request, 0);
    let (ring, owner, handle) = control(Config::default(), &key);
    let ring = Arc::new(Mutex::new(ring));
    let cancel = Cancellation::default();
    let mut tap = Tap::new(ring.clone(), handle, cancel.clone(), mode);
    let mut script = Script::new(bytes);
    let result = execute(
        literal,
        &mut engine,
        &request,
        &mut script,
        &cancel,
        Some(&mut tap),
    );
    PlayRun {
        before,
        engine,
        request,
        result,
        script,
        ring,
        owner,
        key,
        tap,
    }
}
fn actual(text: &str) -> Diagnostic {
    let run = run(false, narration(text), Mode::Passive);
    assert!(run.result.is_ok());
    assert_eq!(run.tap.values.len(), 1);
    let value = run.tap.values[0];
    assert_eq!(
        read_key(&run.ring.lock().unwrap(), &run.owner, &run.key),
        Read::Recorded(value)
    );
    value
}
// Test caller's existing best-effort lock policy, not a magical poison detector
// inside &TraceRing. All callers here already hold an authorized exact selector.
fn caller_read(run: &PlayRun) -> Read {
    match run.ring.try_lock() {
        Ok(ring) => read_key(&ring, &run.owner, &run.key),
        Err(_) => Read::Unavailable,
    }
}
fn unchanged(engine: &Engine, before: &Engine) {
    assert_eq!(engine.seed(), before.seed());
    assert_eq!(engine.canonical_bytes(), before.canonical_bytes());
    assert_eq!(engine.canonical_records(), before.canonical_records());
    assert_eq!(
        engine.accepted_history_basis().unwrap(),
        before.accepted_history_basis().unwrap()
    );
}
// Separate executions have genuine timing. Normalize ONLY agreed receipt stage
// elapsed_ms; same-Engine retry/replay below keeps exact original bytes.
fn stable_receipt(receipt: &Receipt) -> Value {
    let mut value = serde_json::to_value(receipt).unwrap();
    for stage in value["play"]["stages"].as_array_mut().unwrap() {
        assert!(stage["elapsed_ms"].as_u64().unwrap() <= profile().deadline_ms);
        stage["elapsed_ms"] = json!(0);
    }
    value
}
fn stable_requests(script: &Script) -> Vec<Value> {
    for pair in script.seen.windows(2) {
        assert!(pair[1].budget.deadline_ms <= pair[0].budget.deadline_ms);
    }
    script
        .seen
        .iter()
        .map(|request| {
            assert!(
                request.budget.deadline_ms > 0
                    && request.budget.deadline_ms <= profile().deadline_ms
            );
            let Input::Structured {
                role,
                prompt,
                schema,
            } = &request.input
            else {
                panic!("structured Play request")
            };
            json!({"version":request.version,"scope":request.scope,"turn":request.turn,
            "revision":request.revision,"profile":request.model_profile,"schema_id":request.schema,
            "role":role,"prompt":prompt,"schema":schema,"bytes":request.budget.max_output_bytes,
            "tokens":request.budget.max_output_tokens,"polls":request.budget.max_pending_polls})
        })
        .collect()
}
fn parity(run: &PlayRun, baseline: &PlayRun) {
    assert_eq!(
        stable_receipt(run.result.as_ref().unwrap()),
        stable_receipt(baseline.result.as_ref().unwrap())
    );
    assert_eq!(
        serde_json::to_value(run.engine.state()).unwrap(),
        serde_json::to_value(baseline.engine.state()).unwrap()
    );
    assert_eq!(
        run.result.as_ref().unwrap().events(),
        baseline.result.as_ref().unwrap().events()
    );
    assert_eq!(
        stable_requests(&run.script),
        stable_requests(&baseline.script)
    );
    assert_eq!(run.script.seen.len(), 2);
    assert_eq!(run.tap.calls_after_panic, 0);
}

#[test]
fn real_play_retains_actual_decisions_for_both_scene_recipes() {
    for literal in [false, true] {
        for (bytes, outcome, error, reason) in [
            (narration(ORDINARY), Outcome::Accepted, None, None),
            (
                narration(FIRST_PERSON),
                Outcome::Rejected,
                Some(ErrorCategory::Narration),
                Some(Reason::SceneFirstPerson),
            ),
            (
                narration(MOVEMENT),
                Outcome::Rejected,
                Some(ErrorCategory::Narration),
                Some(Reason::SceneUnapprovedMovement),
            ),
            (
                narration("You walk while we watch."),
                Outcome::Rejected,
                Some(ErrorCategory::Narration),
                Some(Reason::SceneFirstPerson),
            ),
            (
                serde_json::to_vec(
                    &json!({"text":FIRST_PERSON,"event_ids":[1],"speaker":"someone"}),
                )
                .unwrap(),
                Outcome::Rejected,
                Some(ErrorCategory::Narration),
                Some(Reason::Unclassified),
            ),
            (
                narration("You notice oren nearby."),
                Outcome::Rejected,
                Some(ErrorCategory::Knowledge),
                None,
            ),
        ] {
            let baseline = run(literal, bytes.clone(), Mode::Discard);
            let run = run(literal, bytes, Mode::Passive);
            let receipt = run.result.as_ref().unwrap();
            assert_eq!(run.tap.values.len(), 1);
            let value = run.tap.values[0];
            assert_eq!(
                (
                    value.version(),
                    value.outcome(),
                    value.error(),
                    value.reason()
                ),
                (1, outcome, error, reason)
            );
            assert_eq!(caller_read(&run), Read::Recorded(value));
            assert_eq!(caller_read(&baseline), Read::Unavailable);
            parity(&run, &baseline);
            assert_eq!(
                receipt.play().unwrap().fallback,
                outcome == Outcome::Rejected
            );
            if outcome == Outcome::Rejected {
                assert_eq!(receipt.narration(), crate::engine::render(receipt.events()));
            }
            assert_eq!(run.script.seen.len(), 2);
            let description = format!("{value:?}");
            for secret in [PRIVATE, FIRST_PERSON, MOVEMENT, "oren", &run.request.turn] {
                assert!(!description.contains(secret));
            }
            let record = serde_json::to_value(receipt.play().unwrap()).unwrap();
            let mut expected = vec![
                "fallback",
                "narration",
                "policy",
                "profile",
                "prompt_version",
                "repairs",
                "scene",
                "stages",
                "version",
            ];
            if !literal {
                expected.extend(["context", "context_policy"]);
            }
            expected.sort_unstable();
            assert_eq!(keys(&record), expected);
        }
    }
}

#[test]
fn staged_collector_first_write_requires_last_matching_stage_and_finish_fences_writes() {
    let value = actual(FIRST_PERSON);
    let other = actual(ORDINARY);
    let key = identity(&request(&fixture(), "I wait for one tide tick."), 0);
    let (mut ring, owner, handle) = control(Config::default(), &key);
    assert_eq!(
        ring.record_narration_validation(&handle, value),
        HookStatus::InvalidMetadata
    );
    assert_eq!(
        ring.record(
            &handle,
            Stage::Narration,
            value.outcome(),
            Counts::default(),
            value.error()
        ),
        HookStatus::Recorded
    );
    assert_eq!(
        ring.record_narration_validation(&handle, value),
        HookStatus::InvalidMetadata
    );
    matching_stage(&mut ring, &handle, other);
    assert_eq!(
        ring.record_narration_validation(&handle, value),
        HookStatus::InvalidMetadata
    );
    matching_stage(&mut ring, &handle, value);
    let before = old_bytes(&ring, &owner, &key);
    assert_eq!(
        ring.record_narration_validation(&handle, value),
        HookStatus::Recorded
    );
    assert_eq!(
        old_bytes(&ring, &owner, &key),
        before,
        "retention changes no old serialized byte or timing"
    );
    assert_eq!(
        ring.record_narration_validation(&handle, other),
        HookStatus::Dropped
    );
    assert_eq!(read_key(&ring, &owner, &key), Read::Recorded(value));
    assert_eq!(
        ring.finish(&handle, Outcome::Committed),
        HookStatus::Recorded
    );
    assert_eq!(
        ring.record_narration_validation(&handle, other),
        HookStatus::Dropped
    );
    assert_eq!(read_key(&ring, &owner, &key), Read::Recorded(value));
    // Error mismatch alone (same Rejected outcome) also refuses; failed write
    // must leave a later matching first write possible.
    let (mut ring, owner, handle) = control(Config::default(), &key);
    assert_eq!(
        ring.record(
            &handle,
            Stage::NarrationValidation,
            value.outcome(),
            Counts::default(),
            Some(ErrorCategory::Knowledge)
        ),
        HookStatus::Recorded
    );
    assert_eq!(
        ring.record_narration_validation(&handle, value),
        HookStatus::InvalidMetadata
    );
    assert_eq!(read_key(&ring, &owner, &key), Read::Unavailable);
    matching_stage(&mut ring, &handle, value);
    assert_eq!(
        ring.record_narration_validation(&handle, value),
        HookStatus::Recorded
    );
}

#[test]
fn authorization_precedes_availability_in_scope_forbidden_invalid_order() {
    let value = actual(ORDINARY);
    let key = identity(&request(&fixture(), "I wait for one tide tick."), 0);
    for disabled in [false, true] {
        let (mut ring, owner, _) = stored_control(Config::default(), &key, value);
        if disabled {
            ring.set_enabled(false);
        }
        let mut selected = selection(&key);
        selected.scope.story = "wrong-scope".into();
        selected.observer = "bad/observer".into();
        selected.turn = None;
        assert_eq!(
            ring.read_narration_validation_for_owner(&owner, &selected, &reader(&key)),
            Err(ReadError::Scope)
        );
        selected.scope = key.scope.clone();
        assert_eq!(
            ring.read_narration_validation_for_owner(&owner, &selected, &reader(&key)),
            Err(ReadError::Forbidden)
        );
        assert_eq!(
            ring.read_narration_validation_for_owner(
                &owner,
                &selected,
                &Reader::story_lab(key.scope.clone())
            ),
            Err(ReadError::InvalidSelection)
        );
        for missing_turn in [false, true] {
            let mut selected = selection(&key);
            if missing_turn {
                selected.turn = None;
            } else {
                selected.attempt = None;
            }
            assert_eq!(
                ring.read_narration_validation_for_owner(&owner, &selected, &reader(&key)),
                Err(ReadError::InvalidSelection)
            );
        }
        let mut selected = selection(&key);
        selected.turn = Some("bad/turn".into());
        assert_eq!(
            ring.read_narration_validation_for_owner(&owner, &selected, &reader(&key)),
            Err(ReadError::InvalidSelection)
        );
        let character = Reader::scoped(key.scope.clone(), "mira".into());
        assert_eq!(
            ring.read_narration_validation_for_owner(&owner, &selection(&key), &character),
            Err(ReadError::Forbidden)
        );
        let mut character_key = key.clone();
        character_key.observer = "mira".into();
        assert_eq!(read_key(&ring, &owner, &character_key), Read::Unavailable);
        assert_eq!(
            read_key(&ring, &TraceOwner::default(), &key),
            Read::Unavailable
        );
        let mut absent = key.clone();
        absent.turn = "absent".into();
        assert_eq!(read_key(&ring, &owner, &absent), Read::Unavailable);
        let mut absent = key.clone();
        absent.base_revision += 1;
        assert_eq!(read_key(&ring, &owner, &absent), Read::Unavailable);
    }
}

#[test]
fn lifecycle_retirement_clear_disable_and_eviction_never_revive_a_slot() {
    let value = actual(FIRST_PERSON);
    let key = identity(&request(&fixture(), "I wait for one tide tick."), 0);
    for action in 0..6 {
        let (mut ring, owner, handle) =
            stored_control(Config::new(1, MAX_STAGES, MAX_BYTES).unwrap(), &key, value);
        match action {
            0 => ring.clear(),
            1 => ring.set_enabled(false),
            2 => ring.clear_owner(&owner),
            3 => owner.retire(),
            4 => {
                let mut next = key.clone();
                next.attempt = 1;
                assert_eq!(
                    ring.begin_for_owner(&owner, next, Provenance::default())
                        .status,
                    HookStatus::Recorded
                );
            }
            _ => {
                ring.set_enabled(false);
                ring.set_enabled(true);
            }
        }
        assert_eq!(read_key(&ring, &owner, &key), Read::Unavailable);
        assert_eq!(
            ring.record_narration_validation(&handle, value),
            if action == 1 {
                HookStatus::Disabled
            } else {
                HookStatus::Dropped
            }
        );
        if action != 3 {
            if action == 1 {
                ring.set_enabled(true);
            }
            let fresh = ring
                .begin_for_owner(&owner, key.clone(), Provenance::default())
                .handle
                .unwrap();
            matching_stage(&mut ring, &fresh, value);
            assert_eq!(read_key(&ring, &owner, &key), Read::Unavailable);
            assert_eq!(
                ring.record_narration_validation(&handle, value),
                HookStatus::Dropped,
                "same identity does not revive the old opaque handle"
            );
            assert_eq!(
                ring.record_narration_validation(&fresh, value),
                HookStatus::Recorded
            );
            assert_eq!(read_key(&ring, &owner, &key), Read::Recorded(value));
        }
    }
    for finished in [
        Outcome::Committed,
        Outcome::Failed,
        Outcome::Cancelled,
        Outcome::Stale,
    ] {
        let (mut ring, owner, handle) = stored_control(Config::default(), &key, value);
        assert_eq!(ring.finish(&handle, finished), HookStatus::Recorded);
        assert_eq!(read_key(&ring, &owner, &key), Read::Recorded(value));
        assert_eq!(
            ring.record_narration_validation(&handle, value),
            HookStatus::Dropped
        );
    }
}

#[test]
fn truncated_flag_or_outcome_and_write_status_priority_are_explicit() {
    let value = actual(ORDINARY);
    let key = identity(&request(&fixture(), "I wait for one tide tick."), 0);
    let (mut ring, owner, handle) = stored_control(
        Config::new(MAX_ATTEMPTS, 1, MAX_BYTES).unwrap(),
        &key,
        value,
    );
    assert_eq!(
        ring.record(
            &handle,
            Stage::Publication,
            Outcome::Accepted,
            Counts::default(),
            None
        ),
        HookStatus::Truncated
    );
    assert_eq!(read_key(&ring, &owner, &key), Read::Unavailable);
    assert_eq!(
        ring.record_narration_validation(&handle, value),
        HookStatus::Truncated
    );
    let (_, _, foreign) = control(Config::default(), &key);
    assert_eq!(
        ring.record_narration_validation(&foreign, value),
        HookStatus::Dropped
    );
    owner.retire();
    assert_eq!(
        ring.record_narration_validation(&handle, value),
        HookStatus::Dropped,
        "retired owner outranks truncation"
    );
    ring.set_enabled(false);
    assert_eq!(
        ring.record_narration_validation(&foreign, value),
        HookStatus::Disabled
    );
    // Explicit staged-metadata controls isolate the contract's OR; do not claim
    // these manually separated flags are normal production transitions.
    for flag_only in [false, true] {
        let (mut ring, owner, handle) = stored_control(Config::default(), &key, value);
        let data = &mut ring.attempts.front_mut().unwrap().data;
        data.truncated = flag_only;
        data.outcome = if flag_only {
            Outcome::Running
        } else {
            Outcome::Truncated
        };
        assert_eq!(read_key(&ring, &owner, &key), Read::Unavailable);
        assert_eq!(
            ring.record_narration_validation(&handle, value),
            HookStatus::Truncated
        );
    }
    let (mut ring, owner, handle) = control(Config::default(), &key);
    assert_eq!(ring.finish(&handle, Outcome::Failed), HookStatus::Recorded);
    assert_eq!(
        ring.record_narration_validation(&handle, value),
        HookStatus::Dropped,
        "finish outranks missing stage metadata"
    );
    assert_eq!(read_key(&ring, &owner, &key), Read::Unavailable);
}

#[test]
fn fixed_payload_and_old_wire_bytes_remain_bounded_under_count_and_byte_pressure() {
    fn copy_eq<T: Copy + Eq>() {}
    copy_eq::<Read>();
    copy_eq::<Diagnostic>();
    assert!(std::mem::size_of::<Option<Diagnostic>>() <= 32);
    assert!(std::mem::size_of::<Option<Diagnostic>>() * MAX_ATTEMPTS <= 1024);
    assert_eq!(
        (TRACE_VERSION, MAX_ATTEMPTS, MAX_STAGES, MAX_BYTES),
        (1, 32, 24, 65_536)
    );
    let value = actual(ORDINARY);
    let key = identity(&request(&fixture(), "I wait for one tide tick."), 0);
    for bytes in [MAX_BYTES, 2048] {
        let (mut ring, owner, first) =
            control(Config::new(MAX_ATTEMPTS, MAX_STAGES, bytes).unwrap(), &key);
        matching_stage(&mut ring, &first, value);
        let before = old_bytes(&ring, &owner, &key);
        assert_eq!(
            ring.record_narration_validation(&first, value),
            HookStatus::Recorded
        );
        assert_eq!(old_bytes(&ring, &owner, &key), before);
        for attempt in 1..=(MAX_ATTEMPTS as u32 + 2) {
            let mut next = key.clone();
            next.attempt = attempt;
            let begun = ring.begin_for_owner(&owner, next.clone(), Provenance::default());
            assert_eq!(begun.status, HookStatus::Recorded);
            let handle = begun.handle.unwrap();
            matching_stage(&mut ring, &handle, value);
            assert_eq!(
                ring.record_narration_validation(&handle, value),
                HookStatus::Recorded
            );
            assert_eq!(read_key(&ring, &owner, &next), Read::Recorded(value));
        }
        let mut all = selection(&key);
        all.attempt = None;
        let snapshot = ring.read_for_owner(&owner, &all, &reader(&key)).unwrap();
        assert!(serde_json::to_vec(&snapshot).unwrap().len() <= bytes);
        assert!(snapshot.attempts.len() <= MAX_ATTEMPTS);
        if bytes == 2048 {
            assert!(snapshot.attempts.len() < MAX_ATTEMPTS);
        }
        assert_eq!(read_key(&ring, &owner, &key), Read::Unavailable);
        assert_eq!(
            ring.record_narration_validation(&first, value),
            HookStatus::Dropped
        );
        let json = serde_json::to_value(&snapshot).unwrap();
        assert_eq!(
            keys(&json),
            ["attempts", "exact_reconstruction", "status", "version"]
        );
        for attempt in json["attempts"].as_array().unwrap() {
            assert_eq!(
                keys(attempt),
                [
                    "elapsed_us",
                    "identity",
                    "outcome",
                    "provenance",
                    "stages",
                    "truncated"
                ]
            );
            for stage in attempt["stages"].as_array().unwrap() {
                assert_eq!(
                    keys(stage),
                    [
                        "counts",
                        "duration_us",
                        "error",
                        "outcome",
                        "stage",
                        "started_us"
                    ]
                );
            }
        }
    }
}

#[test]
fn foreign_unowned_retired_and_current_handle_controls_do_not_transfer_a_slot() {
    let value = actual(FIRST_PERSON);
    let key = identity(&request(&fixture(), "I wait for one tide tick."), 0);
    let (mut ring, owner, handle) = control(Config::default(), &key);
    let (mut other, foreign_owner, foreign) = control(Config::default(), &key);
    matching_stage(&mut ring, &handle, value);
    matching_stage(&mut other, &foreign, value);
    assert_eq!(
        ring.record_narration_validation(&foreign, value),
        HookStatus::Dropped
    );
    assert_eq!(
        other.record_narration_validation(&handle, value),
        HookStatus::Dropped
    );
    assert_eq!(read_key(&ring, &owner, &key), Read::Unavailable);
    assert_eq!(
        ring.record_narration_validation(&handle, value),
        HookStatus::Recorded
    );
    assert_eq!(read_key(&ring, &foreign_owner, &key), Read::Unavailable);
    owner.retire();
    assert_eq!(
        ring.record_narration_validation(&handle, value),
        HookStatus::Dropped
    );
    assert_eq!(read_key(&ring, &owner, &key), Read::Unavailable);
    let mut unowned = TraceRing::default();
    unowned.set_enabled(true);
    let handle = unowned
        .begin(key.clone(), Provenance::default())
        .handle
        .unwrap();
    matching_stage(&mut unowned, &handle, value);
    assert_eq!(
        unowned.record_narration_validation(&handle, value),
        HookStatus::Dropped
    );
    unowned.attempts.front_mut().unwrap().data.truncated = true;
    assert_eq!(
        unowned.record_narration_validation(&handle, value),
        HookStatus::Dropped,
        "unowned attempt outranks truncation"
    );
    assert_eq!(read_key(&unowned, &foreign_owner, &key), Read::Unavailable);
    assert_eq!(
        other.record_narration_validation(&foreign, value),
        HookStatus::Recorded
    );
    assert_eq!(
        read_key(&other, &foreign_owner, &key),
        Read::Recorded(value)
    );
}

#[test]
fn busy_and_poisoned_ringsink_drops_keep_play_and_native_caller_behavior() {
    for literal in [false, true] {
        let baseline = run(literal, narration(FIRST_PERSON), Mode::Passive);
        for mode in [Mode::Busy, Mode::Poison] {
            let run = run(literal, narration(FIRST_PERSON), mode);
            assert_eq!(run.tap.values.len(), 1, "actual Play callback reached");
            assert_eq!(caller_read(&run), Read::Unavailable);
            parity(&run, &baseline);
            if mode == Mode::Poison {
                assert!(run.ring.is_poisoned());
                // Inspect the guard ONLY as a test assertion, never as an app's
                // permission to recover poisoned state or bypass lock policy.
                let poisoned = match run.ring.lock() {
                    Err(e) => e.into_inner(),
                    Ok(_) => panic!("expected poison"),
                };
                assert_eq!(read_key(&poisoned, &run.owner, &run.key), Read::Unavailable);
            } else {
                let _held = run.ring.lock().unwrap();
                assert_eq!(caller_read(&run), Read::Unavailable);
            }
        }
    }
}

#[test]
fn cancellation_and_observer_panics_preserve_retained_decision_not_commit_status() {
    for literal in [false, true] {
        for mode in [Mode::CancelStage, Mode::CancelDiagnostic] {
            for text in [ORDINARY, FIRST_PERSON] {
                let run = run(literal, narration(text), mode);
                assert_eq!(run.result, Err(Error::Cancelled));
                unchanged(&run.engine, &run.before);
                assert_eq!(run.script.seen.len(), 2);
                assert_eq!(run.tap.values.len(), 1);
                let value = run.tap.values[0];
                assert_eq!(caller_read(&run), Read::Recorded(value));
                assert_eq!(
                    value.outcome(),
                    if text == ORDINARY {
                        Outcome::Accepted
                    } else {
                        Outcome::Rejected
                    }
                );
            }
        }
        let baseline = run(literal, narration(FIRST_PERSON), Mode::Passive);
        for mode in [Mode::PanicStage, Mode::PanicBefore, Mode::PanicAfter] {
            let run = run(literal, narration(FIRST_PERSON), mode);
            assert!(run.tap.panic_fired);
            parity(&run, &baseline);
            assert_eq!(run.tap.values.len(), usize::from(mode != Mode::PanicStage));
            assert_eq!(
                caller_read(&run),
                if mode == Mode::PanicAfter {
                    Read::Recorded(run.tap.values[0])
                } else {
                    Read::Unavailable
                }
            );
        }
    }
}

#[test]
fn recorded_retry_replay_and_prevalidation_guards_never_fabricate_new_causes() {
    for literal in [false, true] {
        let mut run = run(literal, narration(FIRST_PERSON), Mode::Passive);
        let before = run.engine.clone();
        let receipt_bytes = serde_json::to_vec(run.result.as_ref().unwrap()).unwrap();
        let mut key = run.key.clone();
        key.attempt += 1;
        let handle = run
            .ring
            .lock()
            .unwrap()
            .begin_for_owner(&run.owner, key.clone(), Provenance::default())
            .handle
            .unwrap();
        let cancel = Cancellation::default();
        cancel.cancel();
        let mut tap = Tap::new(run.ring.clone(), handle, cancel.clone(), Mode::Passive);
        let mut unused = Script::new(narration(ORDINARY));
        let retry = execute(
            literal,
            &mut run.engine,
            &run.request,
            &mut unused,
            &cancel,
            Some(&mut tap),
        )
        .unwrap();
        assert_eq!(serde_json::to_vec(&retry).unwrap(), receipt_bytes);
        assert!(tap.values.is_empty() && unused.seen.is_empty());
        assert_eq!(
            read_key(&run.ring.lock().unwrap(), &run.owner, &key),
            Read::Unavailable
        );
        assert_eq!(caller_read(&run), Read::Recorded(run.tap.values[0]));
        unchanged(&run.engine, &before);
        let replayed =
            Engine::replay_records(run.engine.seed().clone(), run.engine.canonical_records())
                .unwrap();
        unchanged(&replayed, &run.engine);
        for stale in [false, true] {
            let mut engine = fixture();
            let before = engine.clone();
            let mut request = request(
                &engine,
                if stale {
                    "I wait for one tide tick."
                } else {
                    "I use blink."
                },
            );
            if stale {
                request.expected_revision = 99;
            }
            let key = identity(&request, 0);
            let (ring, owner, handle) = control(Config::default(), &key);
            let ring = Arc::new(Mutex::new(ring));
            let cancel = Cancellation::default();
            let mut tap = Tap::new(ring.clone(), handle, cancel.clone(), Mode::Passive);
            let mut unused = Script::new(narration(ORDINARY));
            assert_eq!(
                execute(
                    literal,
                    &mut engine,
                    &request,
                    &mut unused,
                    &cancel,
                    Some(&mut tap)
                ),
                Err(if stale { Error::Stale } else { Error::Ability })
            );
            assert!(tap.values.is_empty() && unused.seen.is_empty());
            assert_eq!(
                read_key(&ring.lock().unwrap(), &owner, &key),
                Read::Unavailable
            );
            unchanged(&engine, &before);
        }
    }
}
