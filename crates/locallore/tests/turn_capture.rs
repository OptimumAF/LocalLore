use locallore::{
    contracts::*,
    engine::Engine,
    inference::*,
    play::{self, PlayProfile},
    turn_capture::{Artifact, DetailStatus},
    turn_trace::*,
};
use serde_json::{json, Value};
use std::{
    sync::{Arc, Mutex},
    task::Poll,
};
fn engine() -> Engine {
    Engine::new(serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap())
        .unwrap()
}
fn profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-capture".into(),
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
fn identity(r: &Request) -> AttemptIdentity {
    AttemptIdentity {
        scope: r.scope.clone(),
        base_revision: 0,
        observer: "player".into(),
        turn: r.turn.clone(),
        attempt: 1,
    }
}
fn selection(k: &AttemptIdentity) -> Selection {
    Selection {
        scope: k.scope.clone(),
        base_revision: k.base_revision,
        observer: k.observer.clone(),
        turn: Some(k.turn.clone()),
        attempt: Some(k.attempt),
    }
}
struct Script {
    requests: Vec<Value>,
    ring: Option<Arc<Mutex<TraceRing>>>,
    replies: Vec<Vec<u8>>,
}
impl Script {
    fn new() -> Self {
        Self {
            requests: vec![],
            ring: None,
            replies: vec![
                serde_json::to_vec(
                    &json!({"commands":[{"op":"give","item":"potion","to":"mira","quantity":1}]}),
                )
                .unwrap(),
                serde_json::to_vec(
                    &json!({"text":"Mira is healed.","event_ids":[1],"speaker":"narrator"}),
                )
                .unwrap(),
            ],
        }
    }
}
impl InferenceProvider for Script {
    fn poll(&mut self, r: &GenerationRequest, _: &Cancellation) -> Poll<Result<Vec<u8>, Error>> {
        let Input::Structured {
            role,
            prompt,
            schema,
        } = &r.input
        else {
            panic!("structured")
        };
        self.requests
            .push(json!({"role":role,"prompt":prompt,"schema":schema}));
        if let Some(ring) = self.ring.take() {
            ring.lock().unwrap().clear();
        }
        Poll::Ready(if self.replies.is_empty() {
            Err(Error::Provider)
        } else {
            Ok(self.replies.remove(0))
        })
    }
}
fn semantic(r: &Receipt) -> Value {
    let mut v = serde_json::to_value(r).unwrap();
    for s in v["play"]["stages"].as_array_mut().unwrap() {
        s["elapsed_ms"] = json!(0)
    }
    v
}
fn setup(
    r: &Request,
    enabled: bool,
) -> (Arc<Mutex<TraceRing>>, TraceOwner, RingSink, AttemptIdentity) {
    let owner = TraceOwner::default();
    let key = identity(r);
    let mut ring = TraceRing::default();
    ring.set_enabled(true);
    if enabled {
        ring.configure_details(&owner, &key.scope, true)
    }
    let handle = ring
        .begin_for_owner(&owner, key.clone(), Provenance::default())
        .handle
        .unwrap();
    let ring = Arc::new(Mutex::new(ring));
    let sink = RingSink::new(ring.clone(), handle);
    (ring, owner, sink, key)
}
#[test]
fn actual_production_context_requests_outputs_and_fallback_are_captured_without_authority_changes()
{
    let mut off = engine();
    let mut on = off.clone();
    let r = off.request(
        "turn",
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: "I give my last potion to Mira.".into(),
        },
    );
    let (ring, owner, mut sink, key) = setup(&r, true);
    let mut a = Script::new();
    let mut b = Script::new();
    let ra = play::execute(&mut off, &r, &mut a, &Cancellation::default(), &profile()).unwrap();
    let rb = play::execute_traced(
        &mut on,
        &r,
        &mut b,
        &Cancellation::default(),
        &profile(),
        Some(&mut sink),
    )
    .unwrap();
    // ONLY existing nondeterministic wall-clock StageTiming values are normalized.
    assert_eq!(semantic(&ra), semantic(&rb));
    assert_eq!(off.canonical_bytes(), on.canonical_bytes());
    assert_eq!(a.requests, b.requests);
    let selected = selection(&key);
    let mut ring = ring.lock().unwrap();
    let detail = ring
        .read_details_for_owner(&owner, &selected, &Reader::story_lab(key.scope.clone()))
        .unwrap();
    assert_eq!(detail.status, DetailStatus::Recorded);
    assert!(!detail.exact_reconstruction);
    let requests:Vec<_>=detail.artifacts.iter().filter(|a|a.kind=="generation_request").map(|a|json!({"role":a.value["input"]["role"],"prompt":a.value["input"]["prompt"],"schema":a.value["input"]["schema"]})).collect();
    assert_eq!(requests, b.requests);
    let context = &detail
        .artifacts
        .iter()
        .find(|a| a.kind == "selected_context")
        .unwrap()
        .value;
    assert_eq!(context["observer"], "player");
    assert!(context["records"]
        .as_array()
        .unwrap()
        .iter()
        .any(|r| r["mandatory"] == true));
    assert!(context["diagnostics"].is_object());
    assert!(detail
        .artifacts
        .iter()
        .any(|a| a.kind == "raw_narrator_output"
            && a.value["text"].as_str().unwrap().contains("Mira is healed")));
    assert!(detail
        .artifacts
        .iter()
        .any(|a| a.kind == "parsed_proposal" && a.value["commands"][0]["op"] == "give"));
    assert_eq!(
        detail.artifacts.last().unwrap().value,
        serde_json::to_value(&rb).unwrap()
    );
    assert!(rb.play().unwrap().fallback);
    assert!(!rb.narration().contains("healed"));
    assert_eq!(
        ring.read_details_for_owner(
            &owner,
            &selected,
            &Reader::scoped(key.scope.clone(), "player".into())
        )
        .err(),
        Some(ReadError::Forbidden)
    );
    assert!(ring
        .read_details_for_owner(
            &TraceOwner::default(),
            &selected,
            &Reader::story_lab(key.scope.clone())
        )
        .unwrap()
        .artifacts
        .is_empty());
    let metadata = serde_json::to_string(
        &ring
            .read_for_owner(&owner, &selected, &Reader::story_lab(key.scope.clone()))
            .unwrap(),
    )
    .unwrap();
    assert!(!metadata.contains("SECRET-TIDE-731") && !metadata.contains("Mira is healed"));
    assert_eq!(on.recorded(&r).unwrap(), Some(rb));
}
#[test]
fn disabled_late_clear_and_reenable_never_backfill_or_resurrect_private_artifacts() {
    for clear in [false, true] {
        let mut e = engine();
        let r = e.request(
            "turn",
            Intent::FreeText {
                kind: PlayInputKind::Action,
                text: "I give my last potion to Mira.".into(),
            },
        );
        let (ring, owner, mut sink, key) = setup(&r, clear);
        let mut p = Script::new();
        if clear {
            p.ring = Some(ring.clone())
        }
        play::execute_traced(
            &mut e,
            &r,
            &mut p,
            &Cancellation::default(),
            &profile(),
            Some(&mut sink),
        )
        .unwrap();
        let mut trace = ring.lock().unwrap();
        let read = trace
            .read_details_for_owner(
                &owner,
                &selection(&key),
                &Reader::story_lab(key.scope.clone()),
            )
            .unwrap();
        assert!(read.artifacts.is_empty());
        trace.configure_details(&owner, &key.scope, true);
        sink_capture_after_unlock(&mut trace, &owner, &key);
    }
}
fn sink_capture_after_unlock(trace: &mut TraceRing, owner: &TraceOwner, key: &AttemptIdentity) {
    let read = trace
        .read_details_for_owner(
            owner,
            &selection(key),
            &Reader::story_lab(key.scope.clone()),
        )
        .unwrap();
    assert_eq!(read.status, DetailStatus::NotRetained);
    assert!(read.artifacts.is_empty());
}
struct PanicSink;
impl TraceSink for PanicSink {
    fn matches(&mut self, _: &Scope, _: u64, _: &str, _: &str) -> bool {
        true
    }
    fn record(&mut self, _: StageMeasurement) {}
    fn capture(&mut self, _: Artifact<'_>) {
        panic!("synthetic capture failure")
    }
}
#[test]
fn capture_panic_and_excess_payload_do_not_fail_valid_generation_or_change_canon() {
    let mut off = engine();
    let mut on = off.clone();
    let r = off.request(
        "turn",
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: "I give my last potion to Mira.".into(),
        },
    );
    let a = play::execute(
        &mut off,
        &r,
        &mut Script::new(),
        &Cancellation::default(),
        &profile(),
    )
    .unwrap();
    let b = play::execute_traced(
        &mut on,
        &r,
        &mut Script::new(),
        &Cancellation::default(),
        &profile(),
        Some(&mut PanicSink),
    )
    .unwrap();
    assert_eq!(semantic(&a), semantic(&b));
    assert_eq!(off.canonical_bytes(), on.canonical_bytes());
    let (ring, owner, mut sink, key) = setup(&r, true);
    sink.capture(Artifact::DirectorOutput(&vec![b'x'; 16_385]));
    let snapshot = ring
        .lock()
        .unwrap()
        .read_details_for_owner(
            &owner,
            &selection(&key),
            &Reader::story_lab(key.scope.clone()),
        )
        .unwrap();
    assert_eq!(snapshot.status, DetailStatus::Truncated);
    assert!(snapshot.artifacts.is_empty());
}

#[test]
fn repair_and_rejected_proposal_capture_actual_attempts_without_committing_failed_work() {
    for rejected in [false, true] {
        let mut e = engine();
        let before = e.canonical_bytes();
        let r = e.request(
            "repair",
            Intent::FreeText {
                kind: PlayInputKind::Action,
                text: "I give my last potion to Mira.".into(),
            },
        );
        let (ring, owner, mut sink, key) = setup(&r, true);
        let mut script = Script::new();
        script
            .replies
            .insert(0, b"{malformed private reply".to_vec());
        if rejected {
            script.replies[1] = serde_json::to_vec(
                &json!({"commands":[{"op":"give","item":"potion","to":"mira","quantity":99}]}),
            )
            .unwrap();
        }
        let result = play::execute_traced(
            &mut e,
            &r,
            &mut script,
            &Cancellation::default(),
            &profile(),
            Some(&mut sink),
        );
        let snapshot = ring
            .lock()
            .unwrap()
            .read_details_for_owner(
                &owner,
                &selection(&key),
                &Reader::story_lab(key.scope.clone()),
            )
            .unwrap();
        assert_eq!(snapshot.status, DetailStatus::Recorded);
        let directors: Vec<_> = snapshot
            .artifacts
            .iter()
            .filter(|a| a.kind == "raw_director_output")
            .collect();
        assert_eq!(directors.len(), 2);
        assert_eq!(directors[0].value["text"], "{malformed private reply");
        let requests: Vec<_> = snapshot
            .artifacts
            .iter()
            .filter(|a| a.kind == "generation_request")
            .collect();
        assert!(requests[1].value["input"]["prompt"]
            .as_str()
            .unwrap()
            .contains("Repair"));
        if rejected {
            assert!(result.is_err());
            assert_eq!(e.canonical_bytes(), before);
            assert_eq!(e.revision(), 0);
            assert_eq!(requests.len(), 2);
            assert!(snapshot
                .artifacts
                .iter()
                .any(|a| a.kind == "parsed_proposal"));
            assert!(!snapshot
                .artifacts
                .iter()
                .any(|a| a.kind == "validated_plan_not_durable_commit"
                    || a.kind == "accepted_candidate_not_durable_commit"));
        } else {
            assert_eq!(result.unwrap().play().unwrap().repairs, 1);
            assert_eq!(requests.len(), 3);
        }
    }
}

struct CancelDuringPoll;
impl InferenceProvider for CancelDuringPoll {
    fn poll(
        &mut self,
        _: &GenerationRequest,
        cancel: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        cancel.cancel();
        Poll::Pending
    }
}
#[test]
fn cancelled_generation_retains_only_observed_input_and_never_invents_output_or_receipt() {
    let mut e = engine();
    let before = e.canonical_bytes();
    let r = e.request(
        "cancel",
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: "I give my last potion to Mira.".into(),
        },
    );
    let (ring, owner, mut sink, key) = setup(&r, true);
    assert_eq!(
        play::execute_traced(
            &mut e,
            &r,
            &mut CancelDuringPoll,
            &Cancellation::default(),
            &profile(),
            Some(&mut sink)
        ),
        Err(Error::Cancelled)
    );
    assert_eq!(e.canonical_bytes(), before);
    let snapshot = ring
        .lock()
        .unwrap()
        .read_details_for_owner(
            &owner,
            &selection(&key),
            &Reader::story_lab(key.scope.clone()),
        )
        .unwrap();
    assert_eq!(
        snapshot
            .artifacts
            .iter()
            .filter(|a| a.kind == "generation_request")
            .count(),
        1
    );
    assert!(!snapshot.artifacts.iter().any(|a| a.kind.contains("output")
        || a.kind.contains("proposal")
        || a.kind.contains("commit")));
    assert!(!snapshot.exact_reconstruction);
}
