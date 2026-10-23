//! Independent adversarial checks of the public private-capture integration.
use locallore::{
    contracts::*,
    engine::Engine,
    inference::*,
    play::{self, PlayProfile},
    turn_capture::{Artifact, DetailStatus, MAX_ARTIFACT_BYTES},
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
fn key(scope: &Scope, turn: &str) -> AttemptIdentity {
    AttemptIdentity {
        scope: scope.clone(),
        base_revision: 0,
        observer: "player".into(),
        turn: turn.into(),
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
fn details(
    ring: &Arc<Mutex<TraceRing>>,
    owner: &TraceOwner,
    k: &AttemptIdentity,
) -> locallore::turn_capture::DetailSnapshot {
    ring.lock()
        .unwrap()
        .read_details_for_owner(owner, &selection(k), &Reader::story_lab(k.scope.clone()))
        .unwrap()
}
fn begin(ring: &Arc<Mutex<TraceRing>>, owner: &TraceOwner, k: &AttemptIdentity) -> RingSink {
    let handle = ring
        .lock()
        .unwrap()
        .begin_for_owner(owner, k.clone(), Provenance::default())
        .handle
        .unwrap();
    RingSink::new(ring.clone(), handle)
}
fn enabled(config: Config) -> (Arc<Mutex<TraceRing>>, TraceOwner, AttemptIdentity) {
    let scope = engine().scope().clone();
    let owner = TraceOwner::default();
    let mut ring = TraceRing::new(config);
    ring.set_enabled(true);
    ring.configure_details(&owner, &scope, true);
    (Arc::new(Mutex::new(ring)), owner, key(&scope, "review"))
}

#[test]
fn serialization_expansion_drops_whole_artifact_but_keeps_exact_binary_encoding() {
    let (ring, owner, k) = enabled(Config::default());
    let mut sink = begin(&ring, &owner, &k);
    // Raw length is permitted, but JSON escaping exceeds the artifact budget.
    sink.capture(Artifact::DirectorOutput(&[0; 8192]));
    let first = details(&ring, &owner, &k);
    assert_eq!(first.status, DetailStatus::Truncated);
    assert!(first.artifacts.is_empty());
    sink.capture(Artifact::NarratorOutput(&[0xff; 16384]));
    let second = details(&ring, &owner, &k);
    assert_eq!(second.status, DetailStatus::Truncated);
    assert!(!second.exact_reconstruction);
    assert_eq!(second.artifacts.len(), 1);
    let a = &second.artifacts[0];
    assert_eq!(a.ordinal, 0);
    assert_eq!(a.value["encoding"], "hex");
    assert_eq!(a.value["bytes"], 16384);
    assert_eq!(a.value["hex"].as_str().unwrap(), "ff".repeat(16384));
    assert!(a.value.get("text").is_none());
    assert!(serde_json::to_vec(a).unwrap().len() <= MAX_ARTIFACT_BYTES);
}

#[test]
fn consent_rotation_and_metadata_eviction_never_rebind_old_handles_to_new_capture() {
    let (ring, owner, k) = enabled(Config::new(1, MAX_STAGES, MAX_BYTES).unwrap());
    let mut old = begin(&ring, &owner, &k);
    old.capture(Artifact::DirectorOutput(b"OLD-PRIVATE"));
    ring.lock()
        .unwrap()
        .configure_details(&owner, &k.scope, false);
    ring.lock()
        .unwrap()
        .configure_details(&owner, &k.scope, true);
    old.capture(Artifact::NarratorOutput(b"LATE-AFTER-RECONSENT"));
    assert!(details(&ring, &owner, &k).artifacts.is_empty());
    let other = key(&k.scope, "eviction");
    let mut replacement = begin(&ring, &owner, &other);
    replacement.capture(Artifact::DirectorOutput(b"OTHER-PRIVATE"));
    // Same identity can be reused only after its metadata attempt was evicted;
    // old sequence/epoch must not authorize this new attempt's private payload.
    let mut reused = begin(&ring, &owner, &k);
    old.capture(Artifact::DirectorOutput(b"OLD-SEQUENCE-LATE"));
    reused.capture(Artifact::DirectorOutput(b"NEW-PRIVATE"));
    let current = details(&ring, &owner, &k);
    assert_eq!(current.artifacts.len(), 1);
    assert_eq!(current.artifacts[0].value["text"], "NEW-PRIVATE");
    assert_eq!(
        details(&ring, &owner, &other).status,
        DetailStatus::NotRetained
    );
    let (ring_b, owner_b, key_b) = enabled(Config::default());
    let mut own_b = begin(&ring_b, &owner_b, &key_b);
    own_b.capture(Artifact::DirectorOutput(b"B-PRIVATE"));
    // The public sink accepts an opaque handle, but a different ring cannot
    // use it even when its local sequence starts at the same number.
    let foreign_handle = ring
        .lock()
        .unwrap()
        .begin_for_owner(&owner, key(&k.scope, "foreign"), Provenance::default())
        .handle
        .unwrap();
    let mut foreign = RingSink::new(ring_b.clone(), foreign_handle);
    foreign.capture(Artifact::DirectorOutput(b"CROSS-RING-PRIVATE"));
    let view = details(&ring_b, &owner_b, &key_b);
    assert_eq!(view.artifacts.len(), 1);
    assert_eq!(view.artifacts[0].value["text"], "B-PRIVATE");
}

fn profile() -> PlayProfile {
    PlayProfile {
        id: "independent-capture".into(),
        model_sha256: "a".repeat(64),
        runtime_revision: "b".repeat(40),
        template_sha256: "c".repeat(64),
        worker_sha256: "d".repeat(64),
        profile_manifest_sha256: "e".repeat(64),
        context_tokens: 4096,
        director_tokens: 350,
        narrator_tokens: 220,
        deadline_ms: 5000,
        repair_limit: 0,
    }
}
#[derive(Default)]
struct Script {
    requests: Vec<Value>,
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
        Poll::Ready(Ok(serde_json::to_vec(&if role == "director" {
            json!({"commands":[{"op":"wait","ticks":1}]})
        } else {
            json!({"text":"You wait as the tide turns.","event_ids":[1],"speaker":"narrator"})
        })
        .unwrap()))
    }
}
struct BusyFirstRequest {
    inner: RingSink,
    ring: Arc<Mutex<TraceRing>>,
    dropped: bool,
}
impl TraceSink for BusyFirstRequest {
    fn matches(&mut self, s: &Scope, r: u64, o: &str, t: &str) -> bool {
        self.inner.matches(s, r, o, t)
    }
    fn record(&mut self, m: StageMeasurement) {
        self.inner.record(m)
    }
    fn capture(&mut self, a: Artifact<'_>) {
        if !self.dropped && matches!(&a, Artifact::Request(_)) {
            self.dropped = true;
            let _held = self.ring.lock().unwrap();
            self.inner.capture(a);
        } else {
            self.inner.capture(a)
        }
    }
}
fn semantic(r: &Receipt) -> Value {
    let mut v = serde_json::to_value(r).unwrap();
    for stage in v["play"]["stages"].as_array_mut().unwrap() {
        stage["elapsed_ms"] = json!(0);
    }
    v
}
#[test]
fn busy_capture_hook_drops_without_deadlock_prompt_change_or_exact_reconstruction_claim() {
    let mut off = engine();
    let mut on = off.clone();
    let request = off.request(
        "review",
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: "I wait for one tide tick.".into(),
        },
    );
    let (ring, owner, k) = enabled(Config::default());
    let mut sink = BusyFirstRequest {
        inner: begin(&ring, &owner, &k),
        ring: ring.clone(),
        dropped: false,
    };
    let mut a = Script::default();
    let mut b = Script::default();
    let first = play::execute(
        &mut off,
        &request,
        &mut a,
        &Cancellation::default(),
        &profile(),
    )
    .unwrap();
    let second = play::execute_traced(
        &mut on,
        &request,
        &mut b,
        &Cancellation::default(),
        &profile(),
        Some(&mut sink),
    )
    .unwrap();
    assert!(sink.dropped);
    assert_eq!(a.requests, b.requests);
    assert_eq!(semantic(&first), semantic(&second));
    assert_eq!(off.canonical_bytes(), on.canonical_bytes());
    let detail = details(&ring, &owner, &k);
    assert!(!detail.exact_reconstruction);
    assert_eq!(detail.status, DetailStatus::Recorded);
    let requests: Vec<_> = detail
        .artifacts
        .iter()
        .filter(|a| a.kind == "generation_request")
        .collect();
    assert_eq!(requests.len(), 1);
    assert_eq!(requests[0].value["input"]["role"], "narrator");
    assert!(detail
        .artifacts
        .iter()
        .any(|a| a.kind == "raw_director_output"));
    assert!(detail
        .artifacts
        .iter()
        .any(|a| a.kind == "accepted_candidate_not_durable_commit"));
    let metadata = serde_json::to_string(
        &ring
            .lock()
            .unwrap()
            .read_for_owner(&owner, &selection(&k), &Reader::story_lab(k.scope.clone()))
            .unwrap(),
    )
    .unwrap();
    assert!(!metadata.contains("You wait as the tide turns"));
}

#[cfg(feature = "host")]
#[test]
fn actual_host_model_unload_preserves_session_capture_then_close_revokes_it() {
    use locallore::host::Host;
    fn call(h: &Host, command: Value) -> Value {
        h.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
    }
    fn prepared(h: &Host, session: &Value, scope: &Value, turn: &str) -> u64 {
        let r = json!({"version":1,"scope":scope,"turn":turn,"expected_revision":0,"intent":{"kind":"free_text","value":{"kind":"action","text":"I wait for one tide tick."}}});
        assert_eq!(
            call(
                h,
                json!({"op":"submit","session":session,"request":r,"mode":"accepted"})
            )["status"],
            "ok"
        );
        let p = call(
            h,
            json!({"op":"prepare","session":session,"scope":scope,"turn":turn}),
        );
        assert_eq!(p["data"]["phase"], "ready", "{p}");
        let m = call(
            h,
            json!({"op":"trace_read","session":session,"scope":scope,"expected_head":0,"base_revision":0,"observer":{"kind":"player"},"turn":turn,"attempt":null}),
        );
        m["data"]["snapshot"]["attempts"][0]["identity"]["attempt"]
            .as_u64()
            .unwrap()
    }
    fn read(h: &Host, s: &Value, scope: &Value, turn: &str, attempt: u64) -> Value {
        call(
            h,
            json!({"op":"trace_capture_read","session":s,"scope":scope,"expected_head":0,"base_revision":0,"turn":turn,"attempt":attempt}),
        )
    }
    let h = Host::new(true);
    let created = call(&h, json!({"op":"create","seed":"lantern-quay-v1"}));
    let s = &created["data"]["session"];
    let scope = &created["data"]["scope"];
    h.configure_local_provider(profile(), Arc::new(|| Box::new(Script::default())))
        .unwrap();
    assert_eq!(
        call(
            &h,
            json!({"op":"trace_capture_configure","session":s,"scope":scope,"expected_head":0,"enabled":true,"consent":true})
        )["status"],
        "ok"
    );
    let first = prepared(&h, s, scope, "before-unload");
    assert_eq!(
        read(&h, s, scope, "before-unload", first)["data"]["details"]["status"],
        "recorded"
    );
    h.disable_local_provider();
    assert_eq!(
        read(&h, s, scope, "before-unload", first)["data"]["details"]["status"],
        "recorded"
    );
    h.configure_local_provider(profile(), Arc::new(|| Box::new(Script::default())))
        .unwrap();
    let second = prepared(&h, s, scope, "after-unload");
    let view = read(&h, s, scope, "after-unload", second);
    assert_eq!(view["data"]["details"]["status"], "recorded");
    assert!(!view["data"]["details"]["artifacts"]
        .as_array()
        .unwrap()
        .is_empty());
    assert_eq!(
        call(
            &h,
            json!({"op":"trace_capture_read","session":s,"scope":scope,"expected_head":0,"base_revision":0,"turn":"after-unload","attempt":u64::MAX})
        )["error"],
        "InvalidRequest"
    );
    assert_eq!(
        call(&h, json!({"op":"close","session":s,"scope":scope}))["status"],
        "ok"
    );
    assert_eq!(
        read(&h, s, scope, "after-unload", second)["error"],
        "Closed"
    );
}
