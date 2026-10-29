// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent D06 FIRST source at f624c007; UNCOMPILED/UNRUN.
//! Uses public Host/Engine commands and accepted fixed scene-script/admission-port
//! patterns from host_scene_recipe_v1 and m08_play_snapshot_v2_review. This file
//! adds no product provider, validator, store, private-field access or test hook.
//! Actual reached decisions are not the complete trusted 25-tuple codec matrix.
//! No native IPC/WebView/model/device/OS, poisoned-lock or fabricated metadata claim.
#![cfg(feature = "host")]

use locallore::{
    author_correction::{AuthorCorrectionInputV1, AuthorCorrectionOperationV1},
    contracts::*,
    engine::Engine,
    host::{
        Host, HostPlayConstructionV1, Persistence, ProviderFactory, SavedTurn, WorkspaceSummary,
    },
    inference::*,
    play::{PlayContextPolicy, PlayProfile},
};
use serde_json::{json, Value};
use std::{
    collections::BTreeSet,
    sync::{
        atomic::{AtomicUsize, Ordering},
        Arc, Mutex,
    },
    task::Poll,
};

const OP: &str = "trace_narration_validation_read_v1";
const SECRET: &str = "D06_SYNTHETIC_PRIVATE_ANCESTRY_729";

struct Wire {
    host: Host,
    commands: Mutex<Vec<String>>,
}
impl Wire {
    fn new(host: Host) -> Self {
        Self {
            host,
            commands: Mutex::new(Vec::new()),
        }
    }
    fn call(&self, command: Value) -> Value {
        self.commands
            .lock()
            .unwrap()
            .push(command["op"].as_str().unwrap().into());
        self.host
            .call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
    }
    fn trace_control_calls(&self) -> usize {
        // Observed public command-boundary count, not private Host instrumentation.
        self.commands
            .lock()
            .unwrap()
            .iter()
            .filter(|op| {
                matches!(
                    op.as_str(),
                    "trace_configure"
                        | "trace_clear"
                        | "trace_capture_configure"
                        | "trace_capture_revoke"
                )
            })
            .count()
    }
}
fn data(reply: Value) -> Value {
    assert_eq!(reply["status"], "ok", "{reply}");
    reply["data"].clone()
}
fn rejected(reply: Value, error: &str) {
    assert_eq!(
        reply,
        json!({"version":1,"status":"rejected","error":error})
    );
    assert!(serde_json::to_vec(&reply).unwrap().len() <= 4096);
}
fn keys(value: &Value, expected: &[&str]) {
    assert_eq!(
        value
            .as_object()
            .unwrap()
            .keys()
            .map(String::as_str)
            .collect::<BTreeSet<_>>(),
        expected.iter().copied().collect::<BTreeSet<_>>()
    );
}
fn create(w: &Wire) -> (String, Scope) {
    let value = data(w.call(json!({"op":"create","seed":"lantern-quay-v1"})));
    (
        value["session"].as_str().unwrap().into(),
        serde_json::from_value(value["scope"].clone()).unwrap(),
    )
}
fn request(scope: &Scope, head: u64, turn: &str) -> Request {
    Request {
        version: VERSION,
        scope: scope.clone(),
        turn: turn.into(),
        expected_revision: head,
        intent: Intent::FreeText {
            kind: PlayInputKind::Action,
            text: "I wait for one tide tick.".into(),
        },
    }
}
fn query(session: &str, r: &Request, head: u64, attempt: u64) -> Value {
    json!({"op":OP,"session":session,"scope":r.scope,"expected_head":head,
        "base_revision":r.expected_revision,"turn":r.turn,"attempt":attempt})
}
fn action(w: &Wire, session: &str, r: &Request, op: &str) -> Value {
    w.call(json!({"op":op,"session":session,"scope":r.scope,"turn":r.turn}))
}
fn trace(
    w: &Wire,
    session: &str,
    r: &Request,
    head: u64,
    turn: Option<&str>,
    observer: Value,
) -> Value {
    w.call(json!({"op":"trace_read","session":session,"scope":r.scope,
        "expected_head":head,"base_revision":r.expected_revision,"observer":observer,
        "turn":turn,"attempt":null}))
}
fn configure(w: &Wire, session: &str, scope: &Scope, head: u64, enabled: bool) {
    let reply = data(w.call(
        json!({"op":"trace_configure","session":session,"scope":scope,
        "expected_head":head,"enabled":enabled}),
    ));
    assert_eq!(reply["enabled"], enabled);
    assert_eq!(reply["configuration_scope"], "window_host");
    assert_eq!(reply["capture"], "metadata_only");
    assert_eq!(reply["full_capture"], "unsupported");
}
fn prepare(w: &Wire, session: &str, r: &Request) {
    assert_eq!(
        data(w.call(json!({"op":"submit","session":session,"request":r,"mode":"accepted"})))
            ["phase"],
        "queued"
    );
    assert_eq!(data(action(w, session, r, "prepare"))["phase"], "ready");
}
fn exact_attempt(metadata: &Value, r: &Request, player: &str) -> u64 {
    let attempts = metadata["data"]["snapshot"]["attempts"].as_array().unwrap();
    let matches: Vec<_> = attempts
        .iter()
        .filter(|a| a["identity"]["turn"] == r.turn)
        .collect();
    assert_eq!(
        matches.len(),
        1,
        "select exact actual turn, never latest: {metadata}"
    );
    let identity = &matches[0]["identity"];
    assert_eq!(identity["scope"], json!(r.scope));
    assert_eq!(identity["base_revision"], r.expected_revision);
    assert_eq!(identity["observer"], player);
    let attempt = identity["attempt"].as_u64().unwrap();
    assert!(attempt <= u32::MAX as u64);
    attempt
}
fn decision(outcome: &str, error: Option<&str>, reason: Option<&str>) -> Value {
    json!({"version":1,"outcome":outcome,"error":error,"reason":reason})
}
fn bound(
    reply: Value,
    session: &str,
    r: &Request,
    head: u64,
    attempt: u64,
    expected: Option<Value>,
) {
    assert!(
        serde_json::to_vec(&reply).unwrap().len() <= 4096,
        "TOTAL Host envelope bound"
    );
    keys(&reply, &["version", "status", "data"]);
    assert_eq!(reply["version"], 1);
    assert_eq!(reply["status"], "ok");
    let mut wanted = json!({"version":1,"session":session,"scope":r.scope,"head":head,
        "base_revision":r.expected_revision,"turn":r.turn,"attempt":attempt,
        "observer":"player","generation_grant":false,"status":"unavailable"});
    if let Some(expected) = expected {
        keys(&expected, &["version", "outcome", "error", "reason"]);
        wanted["status"] = json!("recorded");
        wanted["decision"] = expected;
    }
    assert_eq!(
        reply["data"], wanted,
        "exact closed query-bound data; absence has NO decision key"
    );
    let encoded = serde_json::to_string(&reply).unwrap();
    assert!(!encoded.contains(SECRET));
    assert!(!encoded.contains("I wait for one tide tick."));
    assert!(!encoded.contains("while we watch"));
}
fn engine(w: &Wire, session: &str, scope: &Scope, head: u64) -> Engine {
    w.host
        .generation_snapshot(session, scope, head, &|| false)
        .unwrap()
        .engine
}
fn same_engine(a: &Engine, b: &Engine) {
    assert_eq!(a.canonical_bytes(), b.canonical_bytes());
    assert_eq!(a.canonical_records(), b.canonical_records());
    assert_eq!(
        a.accepted_history_basis().unwrap(),
        b.accepted_history_basis().unwrap()
    );
}
fn normalized_receipt(mut value: Value) -> Value {
    // Existing nondeterministic stage latency only; do not normalize provenance,
    // narration, request, events, fallback or canonical contents.
    if let Some(stages) = value["play"]["stages"].as_array_mut() {
        for stage in stages {
            stage["elapsed_ms"] = json!(0);
        }
    }
    value
}
fn profile() -> PlayProfile {
    PlayProfile {
        id: "d06-fixed-scene-script".into(),
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
#[derive(Clone, Copy)]
enum Narrator {
    Accepted,
    FirstPerson,
    Movement,
    WrongSpeaker,
    HiddenActor,
    TwoTurns,
}
#[derive(Default)]
struct Seen {
    factories: AtomicUsize,
    roles: Mutex<Vec<String>>,
}
impl Seen {
    fn snapshot(&self) -> (usize, Vec<String>) {
        (
            self.factories.load(Ordering::SeqCst),
            self.roles.lock().unwrap().clone(),
        )
    }
    fn factory(self: &Arc<Self>, narrator: Narrator) -> ProviderFactory {
        let seen = self.clone();
        Arc::new(move || {
            seen.factories.fetch_add(1, Ordering::SeqCst);
            Box::new(FixedSceneScript {
                seen: seen.clone(),
                narrator,
            })
        })
    }
}
// TEST-ONLY deterministic accepted recipe, no model or competing product provider.
struct FixedSceneScript {
    seen: Arc<Seen>,
    narrator: Narrator,
}
impl InferenceProvider for FixedSceneScript {
    fn poll(
        &mut self,
        r: &GenerationRequest,
        cancel: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        if cancel.is_cancelled() {
            return Poll::Ready(Err(Error::Cancelled));
        }
        let Input::Structured { role, .. } = &r.input else {
            panic!("actual structured request required")
        };
        self.seen.roles.lock().unwrap().push(role.clone());
        let value = match role.as_str() {
            "director" => json!({"commands":[{"op":"wait","ticks":1}]}),
            "narrator" => {
                let text = match self.narrator {
                    Narrator::FirstPerson => "You rest while we watch the water.",
                    Narrator::Movement => "You walk toward a low stone arch.",
                    Narrator::HiddenActor => "You notice oren nearby.",
                    Narrator::TwoTurns if r.turn == "selected-rejected" => {
                        "You rest while we watch the water."
                    }
                    _ => "You rest briefly.",
                };
                json!({"text":text,"event_ids":[r.revision+1],"speaker":
                    if matches!(self.narrator, Narrator::WrongSpeaker) { "someone" } else { "narrator" }})
            }
            _ => panic!("unexpected actual role {role}"),
        };
        Poll::Ready(Ok(serde_json::to_vec(&value).unwrap()))
    }
}
fn fixture(literal: bool, narrator: Narrator, enabled: bool) -> (Wire, Arc<Seen>, String, Scope) {
    let w = Wire::new(Host::new(true));
    let seen = Arc::new(Seen::default());
    w.host
        .configure_fixture_provider_with_construction(
            profile(),
            seen.factory(narrator),
            if literal {
                HostPlayConstructionV1::PlayerLiteralSceneV1
            } else {
                HostPlayConstructionV1::MemorySceneV1(PlayContextPolicy::StateRelevantMemoryV1)
            },
        )
        .unwrap();
    let (session, scope) = create(&w);
    configure(&w, &session, &scope, 0, enabled);
    (w, seen, session, scope)
}

#[test]
fn exact_nonlatest_original_attempt_uses_current_head_not_base_or_latest_decision() {
    for literal in [false, true] {
        let (w, seen, s, scope) = fixture(literal, Narrator::TwoTurns, true);
        let selected = request(&scope, 0, "selected-rejected");
        prepare(&w, &s, &selected);
        let selected_meta = trace(
            &w,
            &s,
            &selected,
            0,
            Some(&selected.turn),
            json!({"kind":"player"}),
        );
        let selected_attempt = exact_attempt(&selected_meta, &selected, "player");
        assert_eq!(
            data(action(&w, &s, &selected, "cancel"))["phase"],
            "cancelled"
        );
        let later = request(&scope, 0, "later-accepted");
        prepare(&w, &s, &later);
        assert_eq!(data(action(&w, &s, &later, "commit"))["phase"], "committed");
        let all = trace(&w, &s, &selected, 1, None, json!({"kind":"omniscient"}));
        assert_eq!(all["data"]["head"], 1);
        assert_eq!(all["data"]["base_revision"], 0);
        let attempts = all["data"]["snapshot"]["attempts"].as_array().unwrap();
        assert_eq!(attempts.len(), 2);
        assert_eq!(
            attempts.last().unwrap()["identity"]["turn"],
            later.turn,
            "calibrate nonlatest selection"
        );
        assert_eq!(exact_attempt(&all, &selected, "player"), selected_attempt);
        let later_attempt = exact_attempt(&all, &later, "player");
        let before = engine(&w, &s, &scope, 1);
        let observed = seen.snapshot();
        let controls = w.trace_control_calls();
        bound(
            w.call(query(&s, &selected, 1, selected_attempt)),
            &s,
            &selected,
            1,
            selected_attempt,
            Some(decision(
                "rejected",
                Some("narration"),
                Some("scene_first_person"),
            )),
        );
        bound(
            w.call(query(&s, &later, 1, later_attempt)),
            &s,
            &later,
            1,
            later_attempt,
            Some(decision("accepted", None, None)),
        );
        rejected(w.call(query(&s, &selected, 0, selected_attempt)), "Stale");
        assert_eq!(
            trace(&w, &s, &selected, 1, None, json!({"kind":"omniscient"})),
            all
        );
        same_engine(&engine(&w, &s, &scope, 1), &before);
        assert_eq!(seen.snapshot(), observed);
        assert_eq!(
            observed,
            (
                2,
                vec![
                    "director".to_owned(),
                    "narrator".to_owned(),
                    "director".to_owned(),
                    "narrator".to_owned()
                ]
            )
        );
        assert_eq!(w.trace_control_calls(), controls);
        assert_eq!(
            before.receipts().len(),
            1,
            "cancelled selected attempt is not an accepted receipt"
        );
    }
}

#[test]
fn actual_reached_decisions_remain_separate_from_commit_and_mechanical_fallback() {
    for literal in [false, true] {
        for (case, expected) in [
            (Narrator::Accepted, decision("accepted", None, None)),
            (
                Narrator::FirstPerson,
                decision("rejected", Some("narration"), Some("scene_first_person")),
            ),
            (
                Narrator::Movement,
                decision(
                    "rejected",
                    Some("narration"),
                    Some("scene_unapproved_movement"),
                ),
            ),
            (
                Narrator::WrongSpeaker,
                decision("rejected", Some("narration"), Some("unclassified")),
            ),
            (
                Narrator::HiddenActor,
                decision("rejected", Some("knowledge"), None),
            ),
        ] {
            let (w, seen, s, scope) = fixture(literal, case, true);
            let r = request(&scope, 0, "actual-decision");
            prepare(&w, &s, &r);
            let old = trace(&w, &s, &r, 0, Some(&r.turn), json!({"kind":"player"}));
            let attempt = exact_attempt(&old, &r, "player");
            let before = engine(&w, &s, &scope, 0);
            let observed = seen.snapshot();
            let controls = w.trace_control_calls();
            bound(
                w.call(query(&s, &r, 0, attempt)),
                &s,
                &r,
                0,
                attempt,
                Some(expected.clone()),
            );
            same_engine(&engine(&w, &s, &scope, 0), &before);
            assert_eq!(
                trace(&w, &s, &r, 0, Some(&r.turn), json!({"kind":"player"})),
                old
            );
            let done = data(action(&w, &s, &r, "commit"));
            assert_eq!(done["phase"], "committed");
            assert_eq!(
                done["receipt"]["play"]["fallback"],
                expected["outcome"] == "rejected"
            );
            let after = engine(&w, &s, &scope, 1);
            bound(
                w.call(query(&s, &r, 1, attempt)),
                &s,
                &r,
                1,
                attempt,
                Some(expected),
            );
            same_engine(&engine(&w, &s, &scope, 1), &after);
            assert_eq!(seen.snapshot(), observed);
            assert_eq!(
                observed,
                (1, vec!["director".to_owned(), "narrator".to_owned()])
            );
            assert_eq!(w.trace_control_calls(), controls);
            assert_eq!(after.receipts().len(), 1);
            assert_eq!(
                serde_json::to_value(after.receipts().last().unwrap()).unwrap(),
                done["receipt"]
            );
        }
    }
}

#[test]
fn collection_on_off_and_optional_reads_leave_receipts_state_provider_and_trace_controls_unchanged()
{
    for literal in [false, true] {
        let mut results = Vec::new();
        for enabled in [false, true] {
            let (w, seen, s, scope) = fixture(literal, Narrator::Accepted, enabled);
            let r = request(&scope, 0, "golden-optional-read");
            prepare(&w, &s, &r);
            let old = trace(&w, &s, &r, 0, None, json!({"kind":"player"}));
            let attempt = if enabled {
                exact_attempt(&old, &r, "player")
            } else {
                assert_eq!(old["data"]["snapshot"]["status"], "disabled");
                assert!(old["data"]["snapshot"]["attempts"]
                    .as_array()
                    .unwrap()
                    .is_empty());
                1 // Valid absence selector control; not a claimed retained selection.
            };
            let before = engine(&w, &s, &scope, 0);
            let observed = seen.snapshot();
            let controls = w.trace_control_calls();
            bound(
                w.call(query(&s, &r, 0, attempt)),
                &s,
                &r,
                0,
                attempt,
                enabled.then(|| decision("accepted", None, None)),
            );
            same_engine(&engine(&w, &s, &scope, 0), &before);
            assert_eq!(trace(&w, &s, &r, 0, None, json!({"kind":"player"})), old);
            let done = data(action(&w, &s, &r, "commit"));
            assert_eq!(done["phase"], "committed");
            let after = engine(&w, &s, &scope, 1);
            let head_trace = trace(&w, &s, &r, 1, None, json!({"kind":"player"}));
            bound(
                w.call(query(&s, &r, 1, attempt)),
                &s,
                &r,
                1,
                attempt,
                enabled.then(|| decision("accepted", None, None)),
            );
            assert_eq!(
                trace(&w, &s, &r, 1, None, json!({"kind":"player"})),
                head_trace
            );
            same_engine(&engine(&w, &s, &scope, 1), &after);
            assert_eq!(seen.snapshot(), observed);
            assert_eq!(
                observed,
                (1, vec!["director".to_owned(), "narrator".to_owned()])
            );
            assert_eq!(w.trace_control_calls(), controls);
            assert_eq!(controls, 1);
            results.push((after, normalized_receipt(done["receipt"].clone()), observed));
        }
        // Distinct runs may have different recorded stage elapsed_ms. Exact
        // per-run history/basis equality is checked before/after every read;
        // across runs compare exact projection and only latency-normalized receipt.
        assert_eq!(
            results[0].0.canonical_bytes(),
            results[1].0.canonical_bytes()
        );
        assert_eq!(results[0].1, results[1].1);
        assert_eq!(results[0].2, results[1].2);
    }
}

// Read-only supplied-source admission spy, adapted from the accepted thin-view
// tests. Real Engine owns state/history; all canonical write methods refuse.
struct Source {
    engine: Engine,
    calls: Vec<&'static str>,
    validate_error: Option<&'static str>,
    resume_error: Option<&'static str>,
}
struct ReadOnlyPort(Arc<Mutex<Source>>);
impl ReadOnlyPort {
    fn refuse<T>(&self, operation: &'static str) -> Result<T, String> {
        self.0.lock().unwrap().calls.push(operation);
        Err("Unsupported".into())
    }
}
impl Persistence for ReadOnlyPort {
    fn location(&self) -> &str {
        self.0.lock().unwrap().calls.push("location");
        "d06-synthetic-source"
    }
    fn list(&mut self) -> Result<Vec<WorkspaceSummary>, String> {
        self.refuse("list")
    }
    fn create(&mut self) -> Result<Engine, String> {
        self.refuse("create")
    }
    fn validate_scope(&mut self, scope: &Scope) -> Result<(), String> {
        let mut source = self.0.lock().unwrap();
        source.calls.push("validate_scope");
        if let Some(error) = source.validate_error {
            return Err(error.into());
        }
        if source.engine.scope() == scope {
            Ok(())
        } else {
            Err("NotFound".into())
        }
    }
    fn resume(&mut self, scope: &Scope) -> Result<Engine, String> {
        let mut source = self.0.lock().unwrap();
        source.calls.push("resume");
        if let Some(error) = source.resume_error {
            return Err(error.into());
        }
        if source.engine.scope() == scope {
            Ok(source.engine.clone())
        } else {
            Err("NotFound".into())
        }
    }
    fn begin(&mut self, _: &Request) -> Result<SavedTurn, String> {
        self.refuse("begin")
    }
    fn commit(&mut self, _: &Request, _: &Proposal, _: &str) -> Result<Receipt, String> {
        self.refuse("commit")
    }
    fn cancel(&mut self, _: &Request) -> Result<SavedTurn, String> {
        self.refuse("cancel")
    }
    fn fail(&mut self, _: &Request) -> Result<SavedTurn, String> {
        self.refuse("fail")
    }
    fn stale(&mut self, _: &Request) -> Result<SavedTurn, String> {
        self.refuse("stale")
    }
    fn status(&mut self, _: &Scope, _: &str) -> Result<SavedTurn, String> {
        self.refuse("status")
    }
}
fn source_engine(player: &str) -> Engine {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    assert!(seed.actors.contains_key(player));
    seed.player = player.into(); // Select an existing native actor, never rename JSON property names.
    seed.facts.get_mut("ancestry").unwrap().proposition = SECRET.into();
    Engine::new(seed).unwrap()
}
fn source_host(actual: Engine, lab: bool) -> (Wire, Arc<Mutex<Source>>, String) {
    let scope = actual.scope().clone();
    let source = Arc::new(Mutex::new(Source {
        engine: actual,
        calls: Vec::new(),
        validate_error: None,
        resume_error: None,
    }));
    let w = Wire::new(Host::with_persistence(
        lab,
        Box::new(ReadOnlyPort(source.clone())),
    ));
    let opened = data(w.call(json!({"op":"resume","scope":scope})));
    let session = opened["session"].as_str().unwrap().to_owned();
    source.lock().unwrap().calls.clear();
    (w, source, session)
}

#[test]
fn permission_refuses_before_host_admission_probes_while_parse_and_version_precedence_stay_exact() {
    let actual = source_engine("player");
    let before = actual.clone();
    let (w, source, session) = source_host(actual, false);
    let r = request(before.scope(), 0, "absent-private-attempt");
    let mut command = query(&session, &r, 999, u64::MAX);
    command["turn"] = json!("");
    for target in [&session, "unknown-session"] {
        command["session"] = json!(target);
        rejected(w.call(command.clone()), "Forbidden");
    }
    rejected(
        w.host.call(&vec![b'x'; locallore::host::MAX_INPUT + 1]),
        "TooLarge",
    );
    rejected(w.host.call(b"{invalid-json"), "Malformed");
    rejected(
        w.host
            .call(&serde_json::to_vec(&json!({"version":2,"command":command})).unwrap()),
        "Version",
    );
    let mut malformed = command.clone();
    malformed["observer"] = json!({"kind":"omniscient"});
    rejected(w.call(malformed), "Malformed");
    assert!(
        source.lock().unwrap().calls.is_empty(),
        "denied VALID new op performs zero Host source/admission probes"
    );
    same_engine(&source.lock().unwrap().engine, &before);
    assert_eq!(
        w.host.live_counts(),
        (1, 0),
        "denial did not retire the existing attachment"
    );
    // Existing unprivileged player metadata is unchanged; it grants no new read.
    let old = trace(&w, &session, &r, 0, None, json!({"kind":"player"}));
    assert_eq!(old["status"], "ok");
    rejected(w.call(query(&session, &r, 0, 0)), "Forbidden");
    assert_eq!(w.trace_control_calls(), 0);
}

#[test]
fn authorized_admission_current_head_u32_and_selector_order_precede_optional_absence() {
    let actual = source_engine("player");
    let before = actual.clone();
    let (w, source, session) = source_host(actual, true);
    let r = request(before.scope(), 0, "unretained");
    rejected(w.call(query("unknown-session", &r, 0, 0)), "Closed");
    let mut foreign = query(&session, &r, 0, 0);
    foreign["scope"]["branch"] = json!("foreign");
    rejected(w.call(foreign), "Scope");
    assert!(source.lock().unwrap().calls.is_empty());
    let mut invalid = query(&session, &r, 1, u64::MAX);
    invalid["turn"] = json!("");
    rejected(w.call(invalid.clone()), "Stale");
    assert_eq!(source.lock().unwrap().calls, ["validate_scope", "resume"]);
    invalid["expected_head"] = json!(0);
    rejected(w.call(invalid.clone()), "InvalidRequest");
    invalid["attempt"] = json!(u32::MAX);
    rejected(w.call(invalid), "InvalidSelection");
    for attempt in [0, u32::MAX as u64] {
        bound(
            w.call(query(&session, &r, 0, attempt)),
            &session,
            &r,
            0,
            attempt,
            None,
        );
    }
    for bad_turn in ["", "has space", "non_ascii_é"] {
        let mut bad = query(&session, &r, 0, 0);
        bad["turn"] = json!(bad_turn);
        rejected(w.call(bad), "InvalidSelection");
    }
    let mut long = query(&session, &r, 0, 0);
    long["turn"] = json!("x".repeat(65));
    rejected(w.call(long), "InvalidSelection");
    for (validation, resume, expected, calls) in [
        (Some("Io"), None, "Io", vec!["validate_scope"]),
        (
            None,
            Some("Storage"),
            "Storage",
            vec!["validate_scope", "resume"],
        ),
    ] {
        {
            let mut state = source.lock().unwrap();
            state.validate_error = validation;
            state.resume_error = resume;
            state.calls.clear();
        }
        let mut bad = query(&session, &r, 999, u64::MAX);
        bad["turn"] = json!("");
        rejected(w.call(bad), expected);
        assert_eq!(source.lock().unwrap().calls, calls);
    }
    {
        let mut state = source.lock().unwrap();
        state.validate_error = Some("NotFound");
        state.resume_error = None;
        state.calls.clear();
    }
    rejected(w.call(query(&session, &r, 0, 0)), "NotFound");
    assert_eq!(source.lock().unwrap().calls, ["validate_scope"]);
    assert_eq!(
        w.host.live_counts(),
        (0, 0),
        "authorized existing NotFound reconciliation retires attachment"
    );
    source.lock().unwrap().validate_error = None;
    rejected(w.call(query(&session, &r, 0, 0)), "Closed");
    same_engine(&source.lock().unwrap().engine, &before);
    assert_eq!(w.trace_control_calls(), 0);
}

#[test]
fn closed_required_request_fields_numeric_shapes_and_privilege_injection_are_rejected() {
    let w = Wire::new(Host::new(true));
    let (session, scope) = create(&w);
    let r = request(&scope, 0, "shape-control");
    let valid = query(&session, &r, 0, 0);
    for field in [
        "session",
        "scope",
        "expected_head",
        "base_revision",
        "turn",
        "attempt",
    ] {
        let mut missing = valid.clone();
        missing.as_object_mut().unwrap().remove(field);
        rejected(w.call(missing), "Malformed");
    }
    for field in [
        "observer",
        "owner",
        "handle",
        "generation_grant",
        "story_lab",
        "path",
        "decision",
    ] {
        let mut extra = valid.clone();
        extra[field] = json!(true);
        rejected(w.call(extra), "Malformed");
    }
    for field in ["expected_head", "base_revision", "attempt"] {
        for value in [json!(-1), json!(0.5), json!("0"), Value::Null] {
            let mut bad = valid.clone();
            bad[field] = value;
            rejected(w.call(bad), "Malformed");
        }
    }
    let mut future = valid.clone();
    future["op"] = json!("trace_narration_validation_read_v2");
    rejected(w.call(future), "Malformed");
    bound(w.call(valid), &session, &r, 0, 0, None);
    assert_eq!(
        w.trace_control_calls(),
        0,
        "reading never enables collection"
    );
}

#[test]
fn exact_session_scope_attempt_actor_and_owner_boundaries_never_fall_back_to_other_metadata() {
    let (w, seen, session, scope) = fixture(false, Narrator::Accepted, true);
    let r = request(&scope, 0, "owner-local-turn");
    prepare(&w, &session, &r);
    let old = trace(&w, &session, &r, 0, None, json!({"kind":"player"}));
    let attempt = exact_attempt(&old, &r, "player");
    let (other_session, other_scope) = create(&w);
    let foreign = request(&other_scope, 0, &r.turn);
    let before = engine(&w, &session, &scope, 0);
    let observed = seen.snapshot();
    bound(
        w.call(query(&other_session, &foreign, 0, attempt)),
        &other_session,
        &foreign,
        0,
        attempt,
        None,
    );
    rejected(w.call(query(&other_session, &r, 0, attempt)), "Scope");
    let unknown_attempt = attempt.checked_add(1).unwrap();
    bound(
        w.call(query(&session, &r, 0, unknown_attempt)),
        &session,
        &r,
        0,
        unknown_attempt,
        None,
    );
    let actor = trace(
        &w,
        &session,
        &r,
        0,
        None,
        json!({"kind":"character","id":"sable"}),
    );
    assert!(actor["data"]["snapshot"]["attempts"]
        .as_array()
        .unwrap()
        .is_empty());
    let mut inject = query(&session, &r, 0, attempt);
    inject["observer"] = json!("sable");
    rejected(w.call(inject), "Malformed");
    bound(
        w.call(query(&session, &r, 0, attempt)),
        &session,
        &r,
        0,
        attempt,
        Some(decision("accepted", None, None)),
    );
    // A second Host deliberately has identical public session/scope/turn IDs;
    // it has no live owner/attempt from this Host and cannot borrow that result.
    let separate = Wire::new(Host::new(true));
    let (same_session_text, same_scope_text) = create(&separate);
    assert_eq!(same_session_text, session);
    assert_eq!(same_scope_text, scope);
    bound(
        separate.call(query(&same_session_text, &r, 0, attempt)),
        &same_session_text,
        &r,
        0,
        attempt,
        None,
    );
    same_engine(&engine(&w, &session, &scope, 0), &before);
    assert_eq!(seen.snapshot(), observed);
    assert_eq!(
        trace(&w, &session, &r, 0, None, json!({"kind":"player"})),
        old
    );
    data(w.call(json!({"op":"close","session":session,"scope":scope})));
    rejected(w.call(query(&session, &r, 0, attempt)), "Closed");
    bound(
        w.call(query(&other_session, &foreign, 0, attempt)),
        &other_session,
        &foreign,
        0,
        attempt,
        None,
    );
    assert_eq!(seen.snapshot(), observed);
}

fn authored_domain2() -> Engine {
    let mut parent = source_engine("mira");
    let request = parent.request(
        "supported-typed-wait",
        Intent::Actions(vec![Command::Wait { ticks: 1 }]),
    );
    let proposal = Engine::proposal(&request).unwrap();
    let receipt = parent.preview(&request, &proposal).unwrap();
    parent.commit_prepared(&receipt).unwrap();
    let original = parent.seed().facts["relic-location"].proposition.clone();
    let input = AuthorCorrectionInputV1 {
        version: 1,
        parent: parent.scope().clone(),
        expected_parent_revision: parent.revision(),
        fork_revision: parent.revision(),
        child_branch: "d06-authored".into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(),
            expected_proposition: original,
            replacement: "D06_SYNTHETIC_AUTHOR_TRUTH".into(),
        },
        reason: "D06 synthetic author fixture".into(),
    };
    let plan = parent.prepare_author_correction(&input, &|| false).unwrap();
    let actual = parent
        .apply_author_correction(&plan, &|| false)
        .unwrap()
        .engine;
    assert_eq!(actual.domain_version(), 2);
    assert!(actual.revision() > 0);
    actual
}

#[test]
fn actual_authored_domain2_current_head_and_nonliteral_player_use_existing_metadata_without_generation(
) {
    for lab in [false, true] {
        let actual = authored_domain2();
        let before = actual.clone();
        let (w, source, session) = source_host(actual, lab);
        let head = before.revision();
        let scope = before.scope();
        let thin = data(w.call(json!({"op":"play_snapshot_v2","session":session,"scope":scope,"expected_revision":head})));
        assert_eq!(thin["version"], 2);
        assert_eq!(thin["domain_version"], 2);
        assert_eq!(thin["scope"], json!(scope));
        assert_eq!(thin["revision"], head);
        assert_eq!(thin["player"]["observer"], "mira");
        configure(&w, &session, scope, head, true);
        let r = request(scope, 0, "supported-typed-wait");
        let old = trace(&w, &session, &r, head, None, json!({"kind":"player"}));
        assert_eq!(old["status"], "ok");
        assert_eq!(old["data"]["head"], head);
        assert_eq!(old["data"]["scope"], json!(scope));
        assert_eq!(old["data"]["base_revision"], 0);
        assert_eq!(old["data"]["snapshot"]["status"], "bounded_metadata_window");
        assert!(old["data"]["snapshot"]["attempts"]
            .as_array()
            .unwrap()
            .is_empty());
        let controls = w.trace_control_calls();
        source.lock().unwrap().calls.clear();
        if lab {
            // There is no restored process-local attempt. The completed real
            // history and thin player identity do not manufacture a decision.
            bound(
                w.call(query(&session, &r, head, 1)),
                &session,
                &r,
                head,
                1,
                None,
            );
            assert_eq!(source.lock().unwrap().calls, ["validate_scope", "resume"]);
            rejected(w.call(query(&session, &r, head - 1, 1)), "Stale");
            assert_eq!(
                trace(&w, &session, &r, head, None, json!({"kind":"omniscient"}))["status"],
                "ok"
            );
        } else {
            rejected(w.call(query(&session, &r, head, 1)), "Forbidden");
            assert!(source.lock().unwrap().calls.is_empty());
            rejected(
                trace(&w, &session, &r, head, None, json!({"kind":"omniscient"})),
                "Forbidden",
            );
        }
        assert_eq!(
            trace(&w, &session, &r, head, None, json!({"kind":"player"})),
            old
        );
        assert_eq!(w.trace_control_calls(), controls);
        // Existing legacy surfaces stay refused; metadata support is not Domain2
        // Inspect/receipt/generation support. No free_text/prepare/provider calls.
        rejected(w.call(json!({"op":"inspect","session":session,"scope":scope,"observer":"omniscient","expected_revision":head})),
            if lab { "Version" } else { "Forbidden" });
        assert!(w
            .commands
            .lock()
            .unwrap()
            .iter()
            .all(|op| !matches!(op.as_str(), "submit" | "free_text" | "prepare" | "commit")));
        assert!(source
            .lock()
            .unwrap()
            .calls
            .iter()
            .all(|op| matches!(*op, "validate_scope" | "resume")));
        same_engine(&source.lock().unwrap().engine, &before);
        assert_eq!(
            source
                .lock()
                .unwrap()
                .engine
                .observed_facts("sable", scope, head)
                .unwrap(),
            before.observed_facts("sable", scope, head).unwrap()
        );
        assert!(!serde_json::to_string(&old).unwrap().contains(SECRET));
    }
}
