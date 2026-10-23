//! Same shared play::execute production path with a synthetic provider; no model or native UI.
use locallore::{
    contracts::*,
    engine::Engine,
    inference::*,
    play::{self, PlayProfile},
    turn_trace::*,
};
use serde_json::{json, Value};
use std::{
    collections::VecDeque,
    sync::{Arc, Mutex},
    task::Poll,
    time::{Duration, Instant},
};

fn engine() -> Engine {
    Engine::new(serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap())
        .unwrap()
}
fn profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-v2".into(),
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
fn request(e: &Engine, text: &str) -> Request {
    e.request(
        "synthetic-turn",
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: text.into(),
        },
    )
}
fn gift() -> Value {
    json!({"commands":[{"op":"give","item":"potion","to":"mira","quantity":1}]})
}
fn prose() -> Value {
    json!({"text":"You place the potion in Mira's waiting hand, a small gesture of care.","event_ids":[1],"speaker":"narrator"})
}
struct Script {
    replies: VecDeque<Vec<u8>>,
    roles: Vec<String>,
    cancel_narrator: bool,
}
impl Script {
    fn new(replies: Vec<Value>) -> Self {
        Self {
            replies: replies
                .into_iter()
                .map(|r| serde_json::to_vec(&r).unwrap())
                .collect(),
            roles: vec![],
            cancel_narrator: false,
        }
    }
}
impl InferenceProvider for Script {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        cancel: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        let Input::Structured { role, .. } = &request.input else {
            panic!("structured production input");
        };
        self.roles.push(role.clone());
        if self.cancel_narrator && role == "narrator" {
            cancel.cancel();
        }
        Poll::Ready(self.replies.pop_front().ok_or(Error::Provider))
    }
}
fn key(request: &Request) -> AttemptIdentity {
    AttemptIdentity {
        scope: request.scope.clone(),
        base_revision: request.expected_revision,
        observer: "player".into(),
        turn: request.turn.clone(),
        attempt: 0,
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
fn ring(key: AttemptIdentity, config: Config) -> (Arc<Mutex<TraceRing>>, AttemptHandle, RingSink) {
    let mut trace = TraceRing::new(config);
    trace.set_enabled(true);
    let handle = trace.begin(key, Provenance::default()).handle.unwrap();
    let ring = Arc::new(Mutex::new(trace));
    let sink = RingSink::new(Arc::clone(&ring), handle.clone());
    (ring, handle, sink)
}
fn snapshot(ring: &Arc<Mutex<TraceRing>>, key: &AttemptIdentity) -> Snapshot {
    ring.lock()
        .unwrap()
        .read(
            &selection(key),
            &Reader::scoped(key.scope.clone(), key.observer.clone()),
        )
        .unwrap()
}
// Normalize ONLY existing nondeterministic StageTiming.elapsed_ms, nowhere else.
fn semantic(receipt: &Receipt) -> Value {
    let mut value = serde_json::to_value(receipt).unwrap();
    if let Some(stages) = value["play"]["stages"].as_array_mut() {
        for stage in stages {
            stage["elapsed_ms"] = json!(0);
        }
    }
    value
}
fn assert_golden(a: &Result<Receipt, Error>, b: &Result<Receipt, Error>, ea: &Engine, eb: &Engine) {
    match (a, b) {
        (Ok(a), Ok(b)) => {
            assert_eq!(semantic(a), semantic(b));
            assert_eq!(a.events(), b.events());
        }
        (Err(a), Err(b)) => assert_eq!(a, b),
        _ => panic!("tracing changed the production Result"),
    }
    assert_eq!(ea.canonical_bytes(), eb.canonical_bytes());
}

#[test]
fn successful_actual_pipeline_has_equal_receipt_events_state_and_explicit_missing_stages() {
    let mut off = engine();
    let mut on = off.clone();
    let r = request(&off, "I give my last potion to Mira.");
    let key = key(&r);
    let (ring, _, mut sink) = ring(key.clone(), Config::default());
    let mut a = Script::new(vec![gift(), prose()]);
    let mut b = Script::new(vec![gift(), prose()]);
    let ra = play::execute(&mut off, &r, &mut a, &Cancellation::default(), &profile());
    let rb = play::execute_traced(
        &mut on,
        &r,
        &mut b,
        &Cancellation::default(),
        &profile(),
        Some(&mut sink),
    );
    assert_golden(&ra, &rb, &off, &on);
    assert_eq!(a.roles, b.roles);
    let snapshot = snapshot(&ring, &key);
    let stages = &snapshot.attempts[0].stages;
    for stage in [
        Stage::Intent,
        Stage::Context,
        Stage::Director,
        Stage::Parsing,
        Stage::Validation,
        Stage::AcceptedCandidate,
        Stage::Narration,
        Stage::NarrationValidation,
    ] {
        assert!(stages
            .iter()
            .any(|s| s.stage == stage && s.outcome == Outcome::Accepted));
    }
    assert!(stages.iter().any(|s| s.stage == Stage::MemoryMaintenance
        && s.outcome == Outcome::NotRun
        && s.error == Some(ErrorCategory::Unsupported)));
    assert!(stages.iter().any(|s| s.stage == Stage::Retrieval
        && s.outcome == Outcome::Accepted
        && s.counts
            .input_tokens
            .is_some_and(|count| count.basis == TokenBasis::Estimated)));
    assert!(!stages
        .iter()
        .any(|s| s.stage == Stage::AtomicCommit || s.outcome == Outcome::Committed));
    assert_eq!(
        snapshot.attempts[0].outcome,
        Outcome::Running,
        "Host still owns durable finish"
    );
    assert!(stages
        .iter()
        .any(|s| s.stage == Stage::Context && s.counts.eligible_records > 0));
    let mut end = 0;
    for stage in stages {
        assert!(stage.started_us >= end);
        end = stage.started_us + stage.duration_us;
    }
    assert!(!snapshot.exact_reconstruction);
}

#[test]
fn invalid_ability_is_validation_rejection_without_any_provider_or_canonical_change() {
    let mut off = engine();
    let mut on = off.clone();
    let r = request(&off, "I use ability invented-teleport.");
    let key = key(&r);
    let (ring, _, mut sink) = ring(key.clone(), Config::default());
    let mut a = Script::new(vec![]);
    let mut b = Script::new(vec![]);
    let ra = play::execute(&mut off, &r, &mut a, &Cancellation::default(), &profile());
    let rb = play::execute_traced(
        &mut on,
        &r,
        &mut b,
        &Cancellation::default(),
        &profile(),
        Some(&mut sink),
    );
    assert_golden(&ra, &rb, &off, &on);
    assert_eq!(rb, Err(Error::Ability));
    assert!(b.roles.is_empty());
    assert!(snapshot(&ring, &key).attempts[0]
        .stages
        .iter()
        .any(|s| s.stage == Stage::Validation
            && s.outcome == Outcome::Rejected
            && s.error == Some(ErrorCategory::Ability)));
}

#[test]
fn malformed_repair_and_unfaithful_narration_have_separate_real_stage_failures() {
    for (replies, expected_error, repair) in [
        (vec![json!({"bad":true}), gift(), prose()], None, true),
        (
            vec![json!({"bad":true}), json!({"bad":true})],
            Some(Error::Malformed),
            true,
        ),
        (
            vec![
                gift(),
                json!({"text":"Mira is healed and her injury disappears.","event_ids":[1],"speaker":"narrator"}),
            ],
            None,
            false,
        ),
    ] {
        let mut off = engine();
        let mut on = off.clone();
        let r = request(&off, "I give my last potion to Mira.");
        let key = key(&r);
        let (ring, _, mut sink) = ring(key.clone(), Config::default());
        let mut a = Script::new(replies.clone());
        let mut b = Script::new(replies);
        let ra = play::execute(&mut off, &r, &mut a, &Cancellation::default(), &profile());
        let rb = play::execute_traced(
            &mut on,
            &r,
            &mut b,
            &Cancellation::default(),
            &profile(),
            Some(&mut sink),
        );
        assert_golden(&ra, &rb, &off, &on);
        assert_eq!(a.roles, b.roles);
        if let Some(error) = expected_error {
            assert_eq!(rb, Err(error));
        }
        let data = snapshot(&ring, &key);
        let stages = &data.attempts[0].stages;
        if repair {
            assert!(stages.iter().any(|s| s.stage == Stage::Parsing
                && s.outcome == Outcome::Rejected
                && s.error == Some(ErrorCategory::Malformed)));
            assert!(stages.iter().any(|s| s.stage == Stage::Repair));
        } else {
            assert!(rb.unwrap().play().unwrap().fallback);
            assert!(stages.iter().any(|s| s.stage == Stage::NarrationValidation
                && s.outcome == Outcome::Rejected
                && s.error == Some(ErrorCategory::Narration)));
        }
    }
}

#[test]
fn cancelled_generation_and_stale_start_preserve_actual_results_and_state() {
    for stale in [false, true] {
        let mut off = engine();
        let mut on = off.clone();
        let mut r = request(&off, "I give my last potion to Mira.");
        if stale {
            r.expected_revision = 99;
        }
        let key = key(&r);
        let (ring, _, mut sink) = ring(key.clone(), Config::default());
        let mut a = Script::new(vec![gift(), prose()]);
        let mut b = Script::new(vec![gift(), prose()]);
        a.cancel_narrator = !stale;
        b.cancel_narrator = !stale;
        let ra = play::execute(&mut off, &r, &mut a, &Cancellation::default(), &profile());
        let rb = play::execute_traced(
            &mut on,
            &r,
            &mut b,
            &Cancellation::default(),
            &profile(),
            Some(&mut sink),
        );
        assert_golden(&ra, &rb, &off, &on);
        assert_eq!(a.roles, b.roles);
        let (stage, outcome, error) = if stale {
            (Stage::Intent, Outcome::Stale, ErrorCategory::Stale)
        } else {
            (
                Stage::Narration,
                Outcome::Cancelled,
                ErrorCategory::Cancelled,
            )
        };
        assert!(snapshot(&ring, &key).attempts[0]
            .stages
            .iter()
            .any(|s| s.stage == stage && s.outcome == outcome && s.error == Some(error)));
    }
}

struct PanickingSink;
impl TraceSink for PanickingSink {
    fn matches(&mut self, _: &Scope, _: u64, _: &str, _: &str) -> bool {
        true
    }
    fn record(&mut self, _: StageMeasurement) {
        panic!("synthetic diagnostic failure");
    }
}
struct SlowSink;
impl TraceSink for SlowSink {
    fn matches(&mut self, _: &Scope, _: u64, _: &str, _: &str) -> bool {
        true
    }
    fn record(&mut self, _: StageMeasurement) {
        std::thread::sleep(Duration::from_millis(80));
    }
}
#[test]
fn panicking_and_slow_callbacks_cannot_change_a_valid_turn_or_consume_its_deadline() {
    for (sink, slow) in [
        (&mut PanickingSink as &mut dyn TraceSink, false),
        (&mut SlowSink as &mut dyn TraceSink, true),
    ] {
        let mut off = engine();
        let mut on = off.clone();
        let r = request(&off, "I give my last potion to Mira.");
        let mut p = profile();
        p.deadline_ms = 500;
        let ra = play::execute(
            &mut off,
            &r,
            &mut Script::new(vec![gift(), prose()]),
            &Cancellation::default(),
            &p,
        );
        let wall = Instant::now();
        let rb = play::execute_traced(
            &mut on,
            &r,
            &mut Script::new(vec![gift(), prose()]),
            &Cancellation::default(),
            &p,
            Some(sink),
        );
        assert_golden(&ra, &rb, &off, &on);
        assert!(rb.is_ok());
        // The slow case exceeds 500ms wall time while actual stage work remains within budget.
        if slow {
            assert!(wall.elapsed() > Duration::from_millis(500));
            assert!(rb
                .unwrap()
                .play()
                .unwrap()
                .stages
                .iter()
                .all(|stage| stage.elapsed_ms < 500));
        }
    }
}

#[test]
fn disabled_truncated_busy_poisoned_and_evicted_ring_hooks_are_passive() {
    for mode in 0..5 {
        let mut off = engine();
        let mut on = off.clone();
        let r = request(&off, "I give my last potion to Mira.");
        let key = key(&r);
        let config = if mode == 1 {
            Config::new(1, 1, MAX_BYTES).unwrap()
        } else {
            Config::new(1, MAX_STAGES, MAX_BYTES).unwrap()
        };
        let (ring, _, mut sink) = ring(key.clone(), config);
        if mode == 0 {
            ring.lock().unwrap().set_enabled(false);
        }
        if mode == 3 {
            let cloned = Arc::clone(&ring);
            assert!(std::thread::spawn(move || {
                let _held = cloned.lock().unwrap();
                panic!("synthetic poisoned diagnostics");
            })
            .join()
            .is_err());
        }
        if mode == 4 {
            let mut other = key.clone();
            other.attempt = 1;
            ring.lock().unwrap().begin(other, Provenance::default());
        }
        let busy = if mode == 2 {
            Some(ring.lock().unwrap())
        } else {
            None
        };
        let ra = play::execute(
            &mut off,
            &r,
            &mut Script::new(vec![gift(), prose()]),
            &Cancellation::default(),
            &profile(),
        );
        let rb = play::execute_traced(
            &mut on,
            &r,
            &mut Script::new(vec![gift(), prose()]),
            &Cancellation::default(),
            &profile(),
            Some(&mut sink),
        );
        assert_golden(&ra, &rb, &off, &on);
        assert!(rb.is_ok());
        drop(busy);
        if mode == 1 {
            let data = snapshot(&ring, &key);
            assert!(data.attempts[0].truncated);
            assert_eq!(data.attempts[0].outcome, Outcome::Truncated);
            assert!(serde_json::to_vec(&data).unwrap().len() <= MAX_BYTES);
        }
    }
}

#[test]
fn mismatched_handles_and_changed_reader_cannot_receive_or_relabel_production_metadata() {
    for change in 0..4 {
        let mut e = engine();
        let r = request(&e, "I give my last potion to Mira.");
        let mut key = key(&r);
        match change {
            0 => key.scope.story = "other-story".into(),
            1 => key.base_revision = 99,
            2 => key.observer = "mira".into(),
            _ => key.turn = "other-turn".into(),
        }
        let (ring, _, mut sink) = ring(key.clone(), Config::default());
        assert!(play::execute_traced(
            &mut e,
            &r,
            &mut Script::new(vec![gift(), prose()]),
            &Cancellation::default(),
            &profile(),
            Some(&mut sink)
        )
        .is_ok());
        assert!(snapshot(&ring, &key).attempts[0].stages.is_empty());
    }
    let mut e = engine();
    let r = request(&e, "I give my last potion to Mira.");
    let key = key(&r);
    let (ring, _, mut sink) = ring(key.clone(), Config::default());
    play::execute_traced(
        &mut e,
        &r,
        &mut Script::new(vec![gift(), prose()]),
        &Cancellation::default(),
        &profile(),
        Some(&mut sink),
    )
    .unwrap();
    let mut q = selection(&key);
    q.observer = "mira".into();
    let trace = ring.lock().unwrap();
    assert_eq!(
        trace.read(&q, &Reader::scoped(key.scope.clone(), "player".into())),
        Err(ReadError::Forbidden)
    );
    assert!(trace
        .read(&q, &Reader::story_lab(key.scope.clone()))
        .unwrap()
        .attempts
        .is_empty());
    q = selection(&key);
    q.base_revision += 1;
    assert!(trace
        .read(&q, &Reader::scoped(key.scope, "player".into()))
        .unwrap()
        .attempts
        .is_empty());
}

#[test]
fn private_content_and_hidden_records_never_enter_metadata_or_eligible_counts() {
    let mut contexts = vec![];
    for hidden in [false, true] {
        let mut seed = engine().seed().clone();
        if hidden {
            seed.facts.insert(
                "HIDDEN-FACT-731".into(),
                Fact {
                    proposition: "PRIVATE-CANARY-731".into(),
                    discoverable_at: None,
                    known_by: ["sable".into()].into(),
                },
            );
            seed.beliefs.push(Belief {
                believer: "sable".into(),
                proposition: "PRIVATE-CANARY-731".into(),
                source_claim: None,
                source: Evidence::Seed(seed.id.clone()),
                confidence: Confidence::Believed,
            });
        }
        let mut e = Engine::new(seed).unwrap();
        let r = request(&e, "I give my last potion to Mira.");
        let key = key(&r);
        let (ring, _, mut sink) = ring(key.clone(), Config::default());
        play::execute_traced(
            &mut e,
            &r,
            &mut Script::new(vec![gift(), prose()]),
            &Cancellation::default(),
            &profile(),
            Some(&mut sink),
        )
        .unwrap();
        let data = snapshot(&ring, &key);
        let bytes = serde_json::to_string(&data).unwrap();
        for forbidden in [
            "PRIVATE-CANARY-731",
            "HIDDEN-FACT-731",
            "SECRET-TIDE-731",
            "potion",
            "sprained-ankle",
            "waiting hand",
            "I give my last",
        ] {
            assert!(!bytes.contains(forbidden), "metadata leaked {forbidden}");
        }
        contexts.push(
            data.attempts[0]
                .stages
                .iter()
                .find(|s| s.stage == Stage::Context)
                .unwrap()
                .counts,
        );
    }
    assert_eq!(
        contexts[0], contexts[1],
        "excluded records cannot change eligible context counts"
    );
}

#[test]
fn explicit_intervals_exclude_idle_gaps_and_reject_stale_measurements() {
    let r = request(&engine(), "I give my last potion to Mira.");
    let key = key(&r);
    let (ring, handle, _) = ring(key.clone(), Config::default());
    let stale = StageTimer::start();
    std::thread::sleep(Duration::from_millis(10));
    let measured =
        StageTimer::start().finish(Stage::Director, Outcome::Accepted, Counts::default(), None);
    let duration_us = measured.duration_us();
    assert_eq!(
        ring.lock().unwrap().record_measured(&handle, measured),
        HookStatus::Recorded
    );
    assert_eq!(
        ring.lock().unwrap().record_measured(
            &handle,
            stale.finish(Stage::Director, Outcome::Accepted, Counts::default(), None)
        ),
        HookStatus::InvalidMetadata
    );
    let data = ring
        .lock()
        .unwrap()
        .read(&selection(&key), &Reader::scoped(r.scope, "player".into()))
        .unwrap();
    let stage = &data.attempts[0].stages[0];
    assert!(stage.started_us >= 10_000);
    assert_eq!(stage.duration_us, duration_us);
}

#[test]
fn recorded_retry_keeps_receipt_and_calls_neither_provider_nor_fake_stages() {
    let mut e = engine();
    let r = request(&e, "I give my last potion to Mira.");
    let first = play::execute(
        &mut e,
        &r,
        &mut Script::new(vec![gift(), prose()]),
        &Cancellation::default(),
        &profile(),
    )
    .unwrap();
    let before = e.canonical_bytes();
    let mut key = key(&r);
    key.attempt = 1;
    let (ring, _, mut sink) = ring(key.clone(), Config::default());
    let mut provider = Script::new(vec![]);
    let again = play::execute_traced(
        &mut e,
        &r,
        &mut provider,
        &Cancellation::default(),
        &profile(),
        Some(&mut sink),
    )
    .unwrap();
    assert_eq!(again, first);
    assert!(provider.roles.is_empty());
    assert_eq!(before, e.canonical_bytes());
    let data = snapshot(&ring, &key);
    assert_eq!(data.attempts[0].stages.len(), 1);
    assert_eq!(data.attempts[0].stages[0].stage, Stage::Intent);
    assert_eq!(data.attempts[0].stages[0].outcome, Outcome::Accepted);
}
