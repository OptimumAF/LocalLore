// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent FIRST Host-read freeze after 27c2607a. UNREGISTERED/UNCOMPILED/
//! UNRUN. Missing op/schema or accepted selector visibility is SETUP, not RED.
//! Real synthetic Host/Play cases are separate from explicitly trusted private
//! admission/metadata/cap controls; none authenticates evidence origin.
use super::*;
use crate::turn_trace::{
    Config, HookStatus, NarrationRejectionReasonV1 as Reason,
    NarrationValidationDiagnosticV1 as Diagnostic, NarrationValidationReadV1 as NativeRead,
    ReadError, TraceSink,
};
use std::{sync::atomic::{AtomicUsize, Ordering}, task::Poll, time::Duration};

const OP: &str = "trace_narration_validation_read_v1";
const ORDINARY: &str = "You rest briefly.";
const FIRST_PERSON: &str = "You rest while we watch the water.";
const MOVEMENT: &str = "You walk toward a low stone arch.";
const PRIVATE: &str = "SYNTHETIC_HOST_DIAGNOSTIC_SECRET_557";

fn engine(player: &str) -> Engine {
    // Original synthetic ID substitution rewrites exact JSON tokens only;
    // no public Host seed-import or player-identity override is introduced.
    let source = include_str!("../../../../fixtures/lantern_quay.json")
        .replace("\"player\"", &format!("\"{player}\""));
    let mut seed: Seed = serde_json::from_str(&source).unwrap();
    seed.facts.get_mut("ancestry").unwrap().proposition = PRIVATE.into();
    Engine::new(seed).unwrap()
}
fn attach(host: &Host, actual: Engine) -> (String, Scope) {
    let scope = actual.scope().clone();
    let reply = attach_engine(&mut host.state.lock().unwrap(), actual);
    (reply["data"]["session"].as_str().unwrap().into(), scope)
}
fn call(host: &Host, command: Value) -> Value {
    host.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
}
fn data(reply: Value) -> Value {
    assert_eq!(reply["status"], "ok", "{reply}"); reply["data"].clone()
}
fn rejected(reply: Value, error: &str) {
    assert_eq!(reply, json!({"version":1,"status":"rejected","error":error}));
}
fn request(scope: &Scope, turn: &str, text: &str) -> Request {
    Request { version: VERSION, scope: scope.clone(), turn: turn.into(), expected_revision: 0,
        intent: Intent::FreeText { kind: PlayInputKind::Action, text: text.into() } }
}
fn query(session: &str, r: &Request, head: u64, attempt: u64) -> Value {
    json!({"op":OP,"session":session,"scope":r.scope,"expected_head":head,
        "base_revision":r.expected_revision,"turn":r.turn,"attempt":attempt})
}
fn old_trace(host: &Host, session: &str, r: &Request, head: u64) -> Value {
    call(host, json!({"op":"trace_read","session":session,"scope":r.scope,
        "expected_head":head,"base_revision":r.expected_revision,
        "observer":{"kind":"player"},"turn":r.turn,"attempt":null}))
}
fn capture(host: &Host, session: &str, r: &Request, head: u64, attempt: u64) -> Value {
    call(host, json!({"op":"trace_capture_read","session":session,"scope":r.scope,
        "expected_head":head,"base_revision":r.expected_revision,"turn":r.turn,"attempt":attempt}))
}
fn action(host: &Host, session: &str, r: &Request, op: &str) -> Value {
    call(host, json!({"op":op,"session":session,"scope":r.scope,"turn":r.turn}))
}
fn keys(value: &Value) -> Vec<&str> {
    let mut keys: Vec<_> = value.as_object().unwrap().keys().map(String::as_str).collect();
    keys.sort_unstable(); keys
}
fn decision(outcome: &str, error: Option<&str>, reason: Option<&str>) -> Value {
    json!({"version":1,"outcome":outcome,"error":error,"reason":reason})
}
fn bound(reply: Value, session: &str, r: &Request, head: u64, attempt: u64, expected: Option<Value>) {
    assert!(serde_json::to_vec(&reply).unwrap().len() <= 4096);
    assert_eq!(keys(&reply), ["data", "status", "version"]);
    assert_eq!(reply["version"], 1); assert_eq!(reply["status"], "ok");
    let mut wanted = json!({"version":1,"session":session,"scope":r.scope,"head":head,
        "base_revision":r.expected_revision,"turn":r.turn,"attempt":attempt,
        "observer":"player","generation_grant":false,"status":"unavailable"});
    if let Some(expected) = expected {
        assert_eq!(keys(&expected), ["error", "outcome", "reason", "version"]);
        wanted["status"] = json!("recorded"); wanted["decision"] = expected;
    }
    assert_eq!(reply["data"], wanted, "closed exact bound reply, no hidden authority");
    assert!(!serde_json::to_string(&reply).unwrap().contains(PRIVATE));
}
fn profile() -> crate::play::PlayProfile {
    crate::play::PlayProfile { id: "synthetic-host-diagnostic".into(), model_sha256: "a".repeat(64),
        runtime_revision: "b".repeat(40), template_sha256: "c".repeat(64), worker_sha256: "d".repeat(64),
        profile_manifest_sha256: "e".repeat(64), context_tokens: 4096, director_tokens: 350,
        narrator_tokens: 350, deadline_ms: 5000, repair_limit: 1 }
}
#[derive(Default)]
struct Seen { factories: AtomicUsize, requests: Mutex<Vec<GenerationRequest>> }
impl Seen {
    fn factory(self: &Arc<Self>, narrator: Value) -> ProviderFactory {
        let seen = self.clone();
        Arc::new(move || { seen.factories.fetch_add(1, Ordering::SeqCst);
            Box::new(Script { seen: seen.clone(), narrator: narrator.clone() }) })
    }
    fn count(&self) -> usize { self.requests.lock().unwrap().len() }
}
struct Script { seen: Arc<Seen>, narrator: Value }
impl InferenceProvider for Script {
    fn poll(&mut self, request: &GenerationRequest, cancel: &Cancellation)
        -> std::task::Poll<Result<Vec<u8>, Error>>
    {
        self.seen.requests.lock().unwrap().push(request.clone());
        if cancel.is_cancelled() { return Poll::Ready(Err(Error::Cancelled)); }
        let Input::Structured { role, .. } = &request.input else { panic!("structured actual Host request") };
        Poll::Ready(Ok(serde_json::to_vec(&match role.as_str() {
            "director" => json!({"commands":[{"op":"wait","ticks":1}]}),
            "narrator" => self.narrator.clone(),
            _ => panic!("unexpected role"),
        }).unwrap()))
    }
}
fn narration(text: &str) -> Value { json!({"text":text,"event_ids":[1],"speaker":"narrator"}) }
struct Played { host: Host, session: String, r: Request, seen: Arc<Seen>, attempt: u64 }
fn prepared(literal: bool, narrator: Value, player: &str, enabled: bool) -> Played {
    let host = Host::new(true);
    let seen = Arc::new(Seen::default());
    let construction = if literal { HostPlayConstructionV1::PlayerLiteralSceneV1 }
        else { HostPlayConstructionV1::MemorySceneV1(crate::play::PlayContextPolicy::StateRelevantMemoryV1) };
    host.configure_fixture_provider_with_construction(profile(), seen.factory(narrator), construction).unwrap();
    let (session, scope) = attach(&host, engine(player));
    data(call(&host, json!({"op":"trace_configure","session":session,"scope":scope,"expected_head":0,"enabled":enabled})));
    if enabled {
        data(call(&host, json!({"op":"trace_capture_configure","session":session,"scope":scope,
            "expected_head":0,"enabled":true,"consent":true})));
    }
    let r = request(&scope, "host-diagnostic-turn", "I wait for one tide tick.");
    assert_eq!(data(call(&host, json!({"op":"submit","session":session,"request":r,"mode":"accepted"})))["phase"], "queued");
    assert_eq!(data(action(&host, &session, &r, "prepare"))["phase"], "ready");
    let attempt = host.state.lock().unwrap().sessions[&session].turns[&r.turn].trace_attempt.into();
    assert_eq!(seen.count(), 2); assert_eq!(seen.factories.load(Ordering::SeqCst), 1);
    Played { host, session, r, seen, attempt }
}
fn selected_engine(host: &Host, session: &str) -> Engine {
    host.state.lock().unwrap().sessions[session].engine.clone()
}
fn candidate(p: &Played) -> Receipt {
    p.host.state.lock().unwrap().sessions[&p.session].turns[&p.r.turn].receipt.clone().unwrap()
}
fn same_engine(actual: &Engine, before: &Engine) {
    assert_eq!(actual.canonical_bytes(), before.canonical_bytes());
    assert_eq!(actual.canonical_records(), before.canonical_records());
    assert_eq!(actual.accepted_history_basis().unwrap(), before.accepted_history_basis().unwrap());
}
fn selection_for(host: &Host, session: &str, r: &Request, attempt: u32) -> (TraceOwner, Selection) {
    let state = host.state.lock().unwrap(); let selected = &state.sessions[session];
    (selected.trace_owner.clone(), Selection { scope: r.scope.clone(), base_revision: r.expected_revision,
        observer: selected.engine.seed().player.clone(), turn: Some(r.turn.clone()), attempt: Some(attempt) })
}
fn poison<T: Send + 'static>(mutex: &Arc<Mutex<T>>) {
    let owned = mutex.clone();
    assert!(std::thread::spawn(move || { let _guard = owned.lock().unwrap();
        panic!("fixed synthetic Host-read mutex poison"); }).join().is_err());
    assert!(mutex.is_poisoned());
}
fn while_trace_busy(host: &Arc<Host>, commands: Vec<Value>) -> Vec<Value> {
    let held = host.trace.lock().unwrap(); let worker_host = host.clone();
    let (sender, receiver) = std::sync::mpsc::sync_channel(1);
    let worker = std::thread::spawn(move || {
        sender.send(commands.into_iter().map(|command| call(&worker_host, command)).collect::<Vec<_>>()).unwrap();
    });
    let result = receiver.recv_timeout(Duration::from_secs(5));
    drop(held); worker.join().unwrap();
    result.expect("read/selector checks must not wait for the held trace lock")
}
// Trusted PRIVATE metadata control, not an actual Engine validation or an
// authenticated-origin claim. No new product constructor/helper is assumed.
fn install(host: &Host, session: &str, r: &Request, attempt: u32, value: Diagnostic) -> AttemptHandle {
    let (owner, selection) = selection_for(host, session, r, attempt);
    let handle = {
        let mut ring = host.trace.lock().unwrap(); ring.set_enabled(true);
        let handle = ring.begin_for_owner(&owner, AttemptIdentity { scope: selection.scope,
            base_revision: selection.base_revision, observer: selection.observer,
            turn: r.turn.clone(), attempt }, Provenance::default()).handle.unwrap();
        assert_eq!(ring.record(&handle, Stage::NarrationValidation, value.outcome(), Counts::default(), value.error()), HookStatus::Recorded);
        handle
    };
    RingSink::new(host.trace.clone(), handle.clone()).narration_validation(value);
    handle
}

// Admission-only spy: it returns a real supplied Engine and never implements a
// competing canonical store. Relevant admission/lifecycle seams are counted.
struct Spy { actual: Engine, calls: Arc<Mutex<Vec<&'static str>>>, validate_error: Option<&'static str>, resume_error: Option<&'static str> }
impl Spy {
    fn called(&self, name: &'static str) { self.calls.lock().unwrap().push(name); }
    fn unexpected<T>(&self, name: &'static str) -> Result<T, String> {
        self.called(name); Err("UnexpectedSyntheticPortCall".into())
    }
}
impl Persistence for Spy {
    fn validate_scope(&mut self, _: &Scope) -> Result<(), String> {
        self.called("validate_scope"); self.validate_error.map_or(Ok(()), |e| Err(e.into()))
    }
    fn resume(&mut self, _: &Scope) -> Result<Engine, String> {
        self.called("resume"); self.resume_error.map_or_else(|| Ok(self.actual.clone()), |e| Err(e.into()))
    }
    fn location(&self) -> &str { self.called("location"); "synthetic-admission-only" }
    fn database_schema_version(&self) -> u32 { self.called("database_schema_version"); 1 }
    fn list(&mut self) -> Result<Vec<WorkspaceSummary>, String> { self.unexpected("list") }
    fn create(&mut self) -> Result<Engine, String> { self.unexpected("create") }
    fn begin(&mut self, _: &Request) -> Result<SavedTurn, String> { self.unexpected("begin") }
    fn commit(&mut self, _: &Request, _: &Proposal, _: &str) -> Result<Receipt, String> { self.unexpected("commit") }
    fn commit_prepared(&mut self, _: &Receipt) -> Result<Receipt, String> { self.unexpected("commit_prepared") }
    fn cancel(&mut self, _: &Request) -> Result<SavedTurn, String> { self.unexpected("cancel") }
    fn fail(&mut self, _: &Request) -> Result<SavedTurn, String> { self.unexpected("fail") }
    fn stale(&mut self, _: &Request) -> Result<SavedTurn, String> { self.unexpected("stale") }
    fn status(&mut self, _: &Scope, _: &str) -> Result<SavedTurn, String> { self.unexpected("status") }
    fn begin_bound(&mut self, _: &Request, _: &AcceptedHistoryBasis) -> Result<SavedTurn, String> { self.unexpected("begin_bound") }
    fn status_bound(&mut self, _: &Request, _: &AcceptedHistoryBasis) -> Result<SavedTurn, String> { self.unexpected("status_bound") }
    fn commit_prepared_bound(&mut self, _: &Receipt, _: &AcceptedHistoryBasis) -> Result<Receipt, String> { self.unexpected("commit_prepared_bound") }
    fn finish_bound(&mut self, _: &Request, _: &AcceptedHistoryBasis, _: DraftDisposition) -> Result<SavedTurn, String> { self.unexpected("finish_bound") }
}
struct Admission { host: Arc<Host>, session: String, r: Request, owner: TraceOwner, cancel: Cancellation, calls: Arc<Mutex<Vec<&'static str>>> }
fn admission(lab: bool, validate_error: Option<&'static str>, resume_error: Option<&'static str>) -> Admission {
    let actual = engine("player"); let calls = Arc::new(Mutex::new(vec![]));
    let host = Arc::new(Host::with_persistence(lab, Box::new(Spy { actual: actual.clone(), calls: calls.clone(), validate_error, resume_error })));
    let (session, scope) = attach(&host, actual);
    let r = request(&scope, "synthetic-queued-control", "I wait for one tide tick.");
    let cancel = Cancellation::default();
    let owner = {
        let mut state = host.state.lock().unwrap(); let selected = state.sessions.get_mut(&session).unwrap();
        // Explicit queued attachment control tests existing NotFound retirement;
        // it is not a fabricated generated result or durable turn.
        selected.turns.insert(r.turn.clone(), Turn { request: r.clone(), mode: Mode::Accepted,
            cancel: cancel.clone(), phase: Phase::Queued, receipt: None, error: None,
            trace: None, trace_attempt: 0, basis: None });
        selected.trace_owner.clone()
    };
    assert!(calls.lock().unwrap().is_empty());
    Admission { host, session, r, owner, cancel, calls }
}

#[test]
fn actual_host_play_reads_both_recipes_and_exact_reached_decisions() {
    for literal in [false, true] {
        for (narrator, expected) in [
            (narration(ORDINARY), decision("accepted", None, None)),
            (narration(FIRST_PERSON), decision("rejected", Some("narration"), Some("scene_first_person"))),
            (narration(MOVEMENT), decision("rejected", Some("narration"), Some("scene_unapproved_movement"))),
            (narration("You walk while we watch."), decision("rejected", Some("narration"), Some("scene_first_person"))),
            (json!({"text":FIRST_PERSON,"event_ids":[1],"speaker":"someone"}), decision("rejected", Some("narration"), Some("unclassified"))),
            (narration("You notice oren nearby."), decision("rejected", Some("knowledge"), None)),
        ] {
            let p = prepared(literal, narrator, "player", true);
            let before = selected_engine(&p.host, &p.session);
            let meta = old_trace(&p.host, &p.session, &p.r, 0);
            let details = capture(&p.host, &p.session, &p.r, 0, p.attempt);
            let receipt = candidate(&p);
            assert_eq!(receipt.play().unwrap().fallback, expected["outcome"] == "rejected");
            if receipt.play().unwrap().fallback { assert_eq!(receipt.narration(), crate::engine::render(receipt.events())); }
            bound(call(&p.host, query(&p.session, &p.r, 0, p.attempt)), &p.session, &p.r, 0, p.attempt, Some(expected.clone()));
            assert_eq!(old_trace(&p.host, &p.session, &p.r, 0), meta);
            assert_eq!(capture(&p.host, &p.session, &p.r, 0, p.attempt), details);
            same_engine(&selected_engine(&p.host, &p.session), &before);
            let done = data(action(&p.host, &p.session, &p.r, "commit"));
            assert_eq!(done["phase"], "committed");
            bound(call(&p.host, query(&p.session, &p.r, 1, p.attempt)), &p.session, &p.r, 1, p.attempt, Some(expected));
            assert_eq!(p.seen.count(), 2); assert_eq!(p.seen.factories.load(Ordering::SeqCst), 1);
        }
        // Wire observer remains the literal player label; native lookup must
        // derive the actor ID rather than hard-code that label as an actor.
        let p = prepared(literal, narration(ORDINARY), "hero", true);
        bound(call(&p.host, query(&p.session, &p.r, 0, p.attempt)), &p.session, &p.r, 0, p.attempt,
            Some(decision("accepted", None, None)));
    }
}

#[test]
fn non_lab_valid_requests_refuse_before_state_storage_and_lifecycle_but_keep_parse_order() {
    for poisoned_state in [false, true] {
        let a = admission(false, Some("NotFound"), Some("Storage"));
        let before = selected_engine(&a.host, &a.session);
        poison(&a.host.trace);
        if poisoned_state { poison(&a.host.state); }
        let mut valid = query(&a.session, &a.r, 99, u64::MAX);
        valid["turn"] = json!("");
        for command in [valid, query("unknown-session", &a.r, 99, 1)] {
            rejected(call(&a.host, command), "Forbidden");
        }
        rejected(a.host.call(&vec![b' '; MAX_INPUT + 1]), "TooLarge");
        for bytes in [b"{".as_slice(), &[255_u8]] { rejected(a.host.call(bytes), "Malformed"); }
        let command = query(&a.session, &a.r, 0, 1);
        rejected(a.host.call(&serde_json::to_vec(&json!({"version":2,"command":command})).unwrap()), "Version");
        for field in ["observer", "owner", "handle", "story_lab", "path"] {
            let mut bad = command.clone(); bad[field] = json!("synthetic-injected-authority");
            rejected(call(&a.host, bad), "Malformed");
        }
        let mut missing = command.clone(); missing.as_object_mut().unwrap().remove("turn");
        rejected(call(&a.host, missing), "Malformed");
        for attempt in [json!(-1), json!(1.5), Value::Null] {
            let mut bad = command.clone(); bad["attempt"] = attempt;
            rejected(call(&a.host, bad), "Malformed");
        }
        let beyond_u64 = serde_json::to_string(&json!({"version":1,"command":command})).unwrap()
            .replace("\"attempt\":1", "\"attempt\":18446744073709551616");
        rejected(a.host.call(beyond_u64.as_bytes()), "Malformed");
        rejected(call(&a.host, json!({"op":"synthetic_unknown_op"})), "Malformed");
        assert!(a.calls.lock().unwrap().is_empty(), "no admission/source/lifecycle calls");
        assert!(a.owner.live()); assert!(!a.cancel.is_cancelled());
        assert!(a.host.trace.is_poisoned(), "denial must not recover diagnostic poison");
        if poisoned_state {
            assert!(a.host.state.is_poisoned());
            let state = match a.host.state.lock() { Err(e) => e.into_inner(), Ok(_) => panic!("poison retained") };
            same_engine(&state.sessions[&a.session].engine, &before);
            assert_eq!(state.sessions.len(), 1);
        } else { same_engine(&selected_engine(&a.host, &a.session), &before); }
    }
    // Existing player-host metadata operations retain their original authority.
    let host = Host::new(false); let (session, scope) = attach(&host, engine("player"));
    let r = request(&scope, "absent", "I wait for one tide tick.");
    data(call(&host, json!({"op":"trace_configure","session":session,"scope":scope,"expected_head":0,"enabled":true})));
    assert_eq!(old_trace(&host, &session, &r, 0)["status"], "ok");
    rejected(call(&host, query(&session, &r, 0, 0)), "Forbidden");
}

#[test]
fn authorized_admission_overflow_and_shared_selector_errors_precede_trace_availability() {
    for (validate_error, resume_error, expected_calls, expected) in [
        (Some("Io"), None, vec!["validate_scope"], "Io"),
        (None, Some("Storage"), vec!["validate_scope", "resume"], "Storage"),
        (Some("NotFound"), None, vec!["validate_scope"], "NotFound"),
    ] {
        let a = admission(true, validate_error, resume_error);
        let mut bad = query(&a.session, &a.r, 99, u64::MAX); bad["turn"] = json!("");
        rejected(call(&a.host, bad), expected);
        assert_eq!(*a.calls.lock().unwrap(), expected_calls);
        assert_eq!(a.cancel.is_cancelled(), expected == "NotFound");
        assert_eq!(a.owner.live(), expected != "NotFound");
        if expected == "NotFound" { assert!(a.host.state.lock().unwrap().sessions.is_empty()); }
    }
    let a = admission(true, None, None);
    rejected(call(&a.host, query("unknown-session", &a.r, 0, 0)), "Closed");
    let mut wrong_scope = query(&a.session, &a.r, 0, 0); wrong_scope["scope"]["branch"] = json!("another");
    rejected(call(&a.host, wrong_scope), "Scope");
    assert!(a.calls.lock().unwrap().is_empty());
    let mut stale = query(&a.session, &a.r, 1, u64::MAX); stale["turn"] = json!("");
    rejected(call(&a.host, stale), "Stale");
    assert_eq!(*a.calls.lock().unwrap(), ["validate_scope", "resume"]);
    for mode in 0..4 {
        let a = admission(true, None, None);
        if mode == 1 { a.host.trace.lock().unwrap().set_enabled(true); }
        if mode == 3 { poison(&a.host.trace); }
        let mut invalid = query(&a.session, &a.r, 0, u64::MAX); invalid["turn"] = json!("");
        let (owner, mut selected) = selection_for(&a.host, &a.session, &a.r, 0);
        selected.turn = Some(String::new());
        assert_eq!(TraceRing::validate_selection(&selected, &Reader::story_lab(a.r.scope.clone())), Err(ReadError::InvalidSelection));
        // Overflow precedes invalid selector, even when trace cannot be read.
        let overflow = invalid.clone(); invalid["attempt"] = json!(0);
        let replies = if mode == 2 { while_trace_busy(&a.host, vec![overflow, invalid]) }
            else { vec![call(&a.host, overflow), call(&a.host, invalid)] };
        rejected(replies[0].clone(), "InvalidRequest");
        rejected(replies[1].clone(), "InvalidSelection");
        assert_eq!(*a.calls.lock().unwrap(), ["validate_scope", "resume", "validate_scope", "resume"]);
        assert!(owner.live());
        if mode == 3 { assert!(a.host.trace.is_poisoned()); }
    }
}

#[test]
fn exact_binding_lifecycle_and_best_effort_reads_never_recover_or_invent_a_slot() {
    let actual = Diagnostic::new(Outcome::Rejected, Some(ErrorCategory::Narration), Some(Reason::SceneFirstPerson));
    // Explicit trusted collection controls isolate native lifecycle, not model
    // quality or authenticated origin. Actual Host/Play is exercised separately.
    for mutation in 0..6 {
        let host = Host::new(true); let (session, scope) = attach(&host, engine("player"));
        let r = request(&scope, "control", "I wait for one tide tick.");
        let handle = install(&host, &session, &r, 1, actual);
        let (owner, _) = selection_for(&host, &session, &r, 1);
        match mutation {
            0 => host.trace.lock().unwrap().clear(),
            1 => host.trace.lock().unwrap().set_enabled(false),
            2 => host.trace.lock().unwrap().clear_owner(&owner),
            3 => owner.retire(),
            4 => { host.trace.lock().unwrap().finish(&handle, Outcome::Truncated); }
            _ => { host.trace.lock().unwrap().set_enabled(false); host.trace.lock().unwrap().set_enabled(true); }
        }
        let before = old_trace(&host, &session, &r, 0);
        bound(call(&host, query(&session, &r, 0, 1)), &session, &r, 0, 1, None);
        assert_eq!(old_trace(&host, &session, &r, 0), before);
    }
    for finish in [Outcome::Committed, Outcome::Failed, Outcome::Cancelled, Outcome::Stale] {
        let host = Host::new(true); let (session, scope) = attach(&host, engine("player"));
        let r = request(&scope, "finished-control", "I wait for one tide tick.");
        let handle = install(&host, &session, &r, 1, actual);
        host.trace.lock().unwrap().finish(&handle, finish);
        bound(call(&host, query(&session, &r, 0, 1)), &session, &r, 0, 1,
            Some(decision("rejected", Some("narration"), Some("scene_first_person"))));
    }
    let host = Arc::new(Host::new(true)); let (session, scope) = attach(&host, engine("player"));
    let r = request(&scope, "bound-control", "I wait for one tide tick.");
    install(&host, &session, &r, 1, actual);
    let (other_session, _) = attach(&host, engine("player"));
    bound(call(&host, query(&other_session, &r, 0, 1)), &other_session, &r, 0, 1, None);
    for field in ["turn", "base_revision", "attempt"] {
        let mut other = r.clone(); let mut attempt = 1;
        match field { "turn" => other.turn = "another".into(),
            "base_revision" => other.expected_revision = 2, _ => attempt = 2 }
        bound(call(&host, query(&session, &other, 0, attempt)), &session, &other, 0, attempt, None);
    }
    let command = query(&session, &r, 0, 1);
    bound(while_trace_busy(&host, vec![command.clone()]).remove(0), &session, &r, 0, 1, None);
    let (owner, selected) = selection_for(&host, &session, &r, 1);
    poison(&host.trace);
    bound(call(&host, command), &session, &r, 0, 1, None);
    assert!(host.trace.is_poisoned());
    let retained = match host.trace.lock() { Err(e) => e.into_inner(), Ok(_) => panic!("poison untouched") };
    assert_eq!(retained.read_narration_validation_for_owner(&owner, &selected, &Reader::story_lab(scope.clone())).unwrap(), NativeRead::Recorded(actual));
    drop(retained);
    // Count-pressure eviction uses the existing collector cap, no new cache.
    let host = Host::new(true); let (session, scope) = attach(&host, engine("player"));
    *host.trace.lock().unwrap() = TraceRing::new(Config::new(1, 24, 65_536).unwrap());
    let first = request(&scope, "first", "I wait for one tide tick.");
    let second = request(&scope, "second", "I wait for one tide tick.");
    install(&host, &session, &first, 1, actual); install(&host, &session, &second, 1, actual);
    bound(call(&host, query(&session, &first, 0, 1)), &session, &first, 0, 1, None);
    let p = prepared(false, narration(ORDINARY), "player", false);
    let before = old_trace(&p.host, &p.session, &p.r, 0);
    assert_eq!(before["data"]["snapshot"]["status"], "disabled");
    bound(call(&p.host, query(&p.session, &p.r, 0, p.attempt)), &p.session, &p.r, 0, p.attempt, None);
    assert_eq!(old_trace(&p.host, &p.session, &p.r, 0), before);
    assert_eq!(p.seen.count(), 2); assert_eq!(p.seen.factories.load(Ordering::SeqCst), 1);
}

#[test]
fn closed_fixed_tuple_projection_and_entire_reply_cap_are_metadata_only() {
    let mut allowed = vec![
        (Diagnostic::new(Outcome::Accepted, None, None), decision("accepted", None, None)),
        (Diagnostic::new(Outcome::Cancelled, Some(ErrorCategory::Cancelled), None), decision("cancelled", Some("cancelled"), None)),
        (Diagnostic::new(Outcome::Stale, Some(ErrorCategory::Stale), None), decision("stale", Some("stale"), None)),
    ];
    for (reason, code) in [(Reason::Unclassified, "unclassified"), (Reason::SceneFirstPerson, "scene_first_person"), (Reason::SceneUnapprovedMovement, "scene_unapproved_movement")] {
        allowed.push((Diagnostic::new(Outcome::Rejected, Some(ErrorCategory::Narration), Some(reason)), decision("rejected", Some("narration"), Some(code))));
    }
    for (error, code) in [
        (ErrorCategory::Malformed,"malformed"), (ErrorCategory::Version,"version"), (ErrorCategory::Scope,"scope"),
        (ErrorCategory::Rule,"rule"), (ErrorCategory::Agency,"agency"), (ErrorCategory::Deadline,"deadline"),
        (ErrorCategory::RetryMismatch,"retry_mismatch"), (ErrorCategory::TooLarge,"too_large"),
        (ErrorCategory::AuthorUiRequired,"author_ui_required"), (ErrorCategory::ClarificationRequired,"clarification_required"),
        (ErrorCategory::UnknownReference,"unknown_reference"), (ErrorCategory::DeadActor,"dead_actor"),
        (ErrorCategory::Location,"location"), (ErrorCategory::Inventory,"inventory"), (ErrorCategory::Resource,"resource"),
        (ErrorCategory::Ability,"ability"), (ErrorCategory::Knowledge,"knowledge"), (ErrorCategory::Provider,"provider"),
        (ErrorCategory::CorruptHistory,"corrupt_history"),
    ] { allowed.push((Diagnostic::new(Outcome::Rejected, Some(error), None), decision("rejected", Some(code), None))); }
    // These are trusted PRIVATE tuple controls, deliberately not actual emitted
    // Engine failures. Version!=1 is NOT constructible: getter is constant1.
    let mut unsupported = vec![
        Diagnostic::new(Outcome::Accepted, Some(ErrorCategory::Narration), None),
        Diagnostic::new(Outcome::Accepted, None, Some(Reason::Unclassified)),
        Diagnostic::new(Outcome::Rejected, None, None),
        Diagnostic::new(Outcome::Rejected, Some(ErrorCategory::Narration), None),
        Diagnostic::new(Outcome::Rejected, Some(ErrorCategory::Knowledge), Some(Reason::Unclassified)),
        Diagnostic::new(Outcome::Cancelled, None, None),
        Diagnostic::new(Outcome::Stale, Some(ErrorCategory::Cancelled), None),
    ];
    for outcome in [Outcome::NotRun, Outcome::Running, Outcome::Committed, Outcome::Failed, Outcome::Truncated, Outcome::Unknown] {
        unsupported.push(Diagnostic::new(outcome, None, None));
    }
    for error in [ErrorCategory::Storage, ErrorCategory::Unavailable, ErrorCategory::Busy, ErrorCategory::Internal,
        ErrorCategory::Unknown, ErrorCategory::Unsupported, ErrorCategory::Cancelled, ErrorCategory::Stale] {
        unsupported.push(Diagnostic::new(Outcome::Rejected, Some(error), None));
    }
    for (value, expected) in allowed.into_iter().map(|(d,v)| (d,Some(v))).chain(unsupported.into_iter().map(|d| (d,None))) {
        let host = Host::new(true); let (session, scope) = attach(&host, engine("player"));
        let r = request(&scope, "tuple-control", "I wait for one tide tick.");
        install(&host, &session, &r, 1, value);
        bound(call(&host, query(&session, &r, 0, 1)), &session, &r, 0, 1, expected);
    }
    // A long PRIVATE map alias tests the total echoed reply cap, not a normal
    // public session capability. Canonical Engine and existing owner are intact.
    let host = Host::new(true); let (session, scope) = attach(&host, engine("player"));
    let alias = "s".repeat(5000);
    { let mut state = host.state.lock().unwrap(); let selected = state.sessions.remove(&session).unwrap(); state.sessions.insert(alias.clone(), selected); }
    let r = request(&scope, "cap-control", "I wait for one tide tick.");
    rejected(call(&host, query(&alias, &r, 0, 1)), "TooLarge");
    let mut injected = query(&alias, &r, 0, 1); injected["observer"] = json!({"kind":"omniscient"});
    rejected(call(&host, injected), "Malformed");
}

fn stable_receipt(receipt: &Value) -> Value {
    let mut value = receipt.clone();
    for stage in value["play"]["stages"].as_array_mut().unwrap() {
        assert!(stage["elapsed_ms"].as_u64().unwrap() <= profile().deadline_ms); stage["elapsed_ms"] = json!(0);
    } value
}
fn stable_requests(seen: &Seen) -> Vec<Value> {
    let requests = seen.requests.lock().unwrap();
    for pair in requests.windows(2) { assert!(pair[1].budget.deadline_ms <= pair[0].budget.deadline_ms); }
    requests.iter().map(|r| {
        assert!(r.budget.deadline_ms > 0 && r.budget.deadline_ms <= profile().deadline_ms);
        let Input::Structured { role, prompt, schema } = &r.input else { panic!("structured actual request") };
        json!({"version":r.version,"scope":r.scope,"turn":r.turn,"revision":r.revision,
            "profile":r.model_profile,"schema_id":r.schema,"role":role,"prompt":prompt,"schema":schema,
            "bytes":r.budget.max_output_bytes,"tokens":r.budget.max_output_tokens,"polls":r.budget.max_pending_polls})
    }).collect()
}
#[test]
fn reads_preserve_actual_provider_receipts_replay_old_wire_and_character_knowledge() {
    for literal in [false, true] {
        let baseline = prepared(literal, narration(FIRST_PERSON), "player", true);
        let p = prepared(literal, narration(FIRST_PERSON), "player", true);
        let before = selected_engine(&p.host, &p.session);
        let observer_before = serde_json::to_value(before.character_context_v2("mira", &p.r.scope, 0).unwrap()).unwrap();
        let receipt_before = serde_json::to_vec(&candidate(&p)).unwrap();
        let old = old_trace(&p.host, &p.session, &p.r, 0);
        let private = capture(&p.host, &p.session, &p.r, 0, p.attempt);
        let value = decision("rejected", Some("narration"), Some("scene_first_person"));
        for _ in 0..3 { bound(call(&p.host, query(&p.session, &p.r, 0, p.attempt)), &p.session, &p.r, 0, p.attempt, Some(value.clone())); }
        same_engine(&selected_engine(&p.host, &p.session), &before);
        assert_eq!(serde_json::to_vec(&candidate(&p)).unwrap(), receipt_before);
        assert_eq!(old_trace(&p.host, &p.session, &p.r, 0), old);
        assert_eq!(capture(&p.host, &p.session, &p.r, 0, p.attempt), private);
        assert_eq!(serde_json::to_value(selected_engine(&p.host, &p.session).character_context_v2("mira", &p.r.scope, 0).unwrap()).unwrap(), observer_before);
        let done = data(action(&p.host, &p.session, &p.r, "commit"));
        let baseline_done = data(action(&baseline.host, &baseline.session, &baseline.r, "commit"));
        assert_eq!(stable_receipt(&done["receipt"]), stable_receipt(&baseline_done["receipt"]));
        assert_eq!(stable_requests(&p.seen), stable_requests(&baseline.seen));
        let after = selected_engine(&p.host, &p.session);
        let receipt_bytes = serde_json::to_vec(&done["receipt"]).unwrap();
        let retry = data(call(&p.host, json!({"op":"submit","session":p.session,"request":p.r,"mode":"accepted"})));
        assert_eq!(retry["phase"], "committed"); assert_eq!(serde_json::to_vec(&retry["receipt"]).unwrap(), receipt_bytes);
        same_engine(&selected_engine(&p.host, &p.session), &after);
        same_engine(&Engine::replay_records(after.seed().clone(), after.canonical_records()).unwrap(), &after);
        bound(call(&p.host, query(&p.session, &p.r, 1, p.attempt)), &p.session, &p.r, 1, p.attempt, Some(value));
        bound(call(&p.host, query(&p.session, &p.r, 1, p.attempt + 1)), &p.session, &p.r, 1, p.attempt + 1, None);
        assert_eq!(p.seen.count(), 2); assert_eq!(p.seen.factories.load(Ordering::SeqCst), 1);
        let p = prepared(literal, narration(ORDINARY), "player", true);
        let before = selected_engine(&p.host, &p.session);
        assert_eq!(data(action(&p.host, &p.session, &p.r, "cancel"))["phase"], "cancelled");
        bound(call(&p.host, query(&p.session, &p.r, 0, p.attempt)), &p.session, &p.r, 0, p.attempt, Some(decision("accepted", None, None)));
        same_engine(&selected_engine(&p.host, &p.session), &before); assert_eq!(p.seen.count(), 2);
        let host = Host::new(true); let seen = Arc::new(Seen::default());
        host.configure_fixture_provider_with_construction(profile(), seen.factory(narration(ORDINARY)),
            if literal { HostPlayConstructionV1::PlayerLiteralSceneV1 } else { HostPlayConstructionV1::MemorySceneV1(crate::play::PlayContextPolicy::StateRelevantMemoryV1) }).unwrap();
        let (session, scope) = attach(&host, engine("player"));
        data(call(&host, json!({"op":"trace_configure","session":session,"scope":scope,"expected_head":0,"enabled":true})));
        let r = request(&scope, "ability-guard", "I use blink."); let before = selected_engine(&host, &session);
        data(call(&host, json!({"op":"submit","session":session,"request":r,"mode":"accepted"})));
        assert_eq!(data(action(&host, &session, &r, "prepare"))["error"], "Ability");
        let attempt = u64::from(host.state.lock().unwrap().sessions[&session].turns[&r.turn].trace_attempt);
        let factories = seen.factories.load(Ordering::SeqCst);
        bound(call(&host, query(&session, &r, 0, attempt)), &session, &r, 0, attempt, None);
        same_engine(&selected_engine(&host, &session), &before); assert_eq!(seen.count(), 0);
        assert_eq!(seen.factories.load(Ordering::SeqCst), factories);
    }
    let host = Host::new(true); let (session, scope) = attach(&host, engine("player"));
    let r = request(&scope, "schema-control", "I wait for one tide tick.");
    let envelope = json!({"version":1,"command":query(&session, &r, 0, 0)});
    assert!(serde_json::from_value::<Envelope>(envelope).is_ok());
    assert!(serde_json::to_string(&schema()).unwrap().contains(OP));
    // Checked-in schema/type regeneration and default-Core/Android-host checks
    // remain Root-owned; this source freeze claims no compiler/device evidence.
}
