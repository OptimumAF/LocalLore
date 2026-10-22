// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Host-v1: bounded in-memory sessions; no JNI, file, SQL, network or model handles.
use crate::{contracts::*, engine::Engine, inference::*};
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::{
    collections::BTreeMap,
    sync::{Arc, Mutex},
};

pub const HOST_VERSION: u16 = 1;
pub const MAX_INPUT: usize = 24_576;
pub const MAX_OUTPUT: usize = 262_144;
pub const MAX_SESSIONS: usize = 4;
pub const MAX_TURNS: usize = 64;
pub const MAX_WORKERS: usize = 4;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Deserialize, Serialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub enum Mode {
    Accepted,
    Malformed,
    Rejected,
    Failed,
    Cancelled,
}
impl Mode {
    fn provider(self) -> FakeProvider {
        FakeProvider::new(match self {
            Self::Accepted => FakeMode::Accepted,
            Self::Malformed => FakeMode::Malformed,
            Self::Rejected => FakeMode::Rejected,
            Self::Failed => FakeMode::Failed,
            Self::Cancelled => FakeMode::Cancelled,
        })
    }
}

/// One source of truth for the generated frontend JSON Schema. No arbitrary seed import.
#[derive(Debug, Deserialize, Serialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct Envelope {
    pub version: u16,
    pub command: HostCommand,
}
#[derive(Debug, Deserialize, Serialize, JsonSchema)]
#[serde(tag = "op", rename_all = "snake_case", deny_unknown_fields)]
pub enum HostCommand {
    Capabilities {},
    Create {
        seed: String,
    },
    Open {
        session: String,
        scope: Scope,
    },
    Close {
        session: String,
        scope: Scope,
    },
    Submit {
        session: String,
        request: Request,
        mode: Mode,
    },
    Prepare {
        session: String,
        scope: Scope,
        turn: String,
    },
    Commit {
        session: String,
        scope: Scope,
        turn: String,
    },
    Cancel {
        session: String,
        scope: Scope,
        turn: String,
    },
    TurnStatus {
        session: String,
        scope: Scope,
        turn: String,
    },
    Inspect {
        session: String,
        scope: Scope,
        observer: String,
        expected_revision: u64,
    },
    ModelStatus {},
    FreeText {
        session: String,
        request: Request,
    },
    SnapshotExport {
        session: String,
        scope: Scope,
        expected_revision: u64,
    },
}

pub fn schema() -> Value {
    let mut value = serde_json::to_value(schemars::schema_for!(Envelope)).unwrap();
    value["properties"]["version"] = json!({"const": HOST_VERSION});
    value
}

#[derive(Clone, Copy, PartialEq, Eq)]
enum Phase {
    Queued,
    Running,
    Ready,
    Committed,
    Cancelled,
    Failed,
    Stale,
}
impl Phase {
    fn name(self) -> &'static str {
        match self {
            Self::Queued => "queued",
            Self::Running => "running",
            Self::Ready => "ready",
            Self::Committed => "committed",
            Self::Cancelled => "cancelled",
            Self::Failed => "failed",
            Self::Stale => "stale",
        }
    }
    fn active(self) -> bool {
        matches!(self, Self::Queued | Self::Running | Self::Ready)
    }
}
struct Turn {
    request: Request,
    mode: Mode,
    cancel: Cancellation,
    phase: Phase,
    receipt: Option<Receipt>,
    error: Option<String>,
}
impl Turn {
    fn view(&self) -> Value {
        json!({"turn": self.request.turn, "scope": self.request.scope,
            "expected_revision": self.request.expected_revision,
            "phase": self.phase.name(), "error": self.error,
            "receipt": if self.phase == Phase::Committed { self.receipt.as_ref() } else { None }})
    }
}
struct Session {
    engine: Engine,
    turns: BTreeMap<String, Turn>,
}
#[derive(Default)]
struct State {
    next: u64,
    workers: usize,
    sessions: BTreeMap<String, Session>,
}

/// Only trusted native construction grants spoiler inspection. JSON cannot grant capabilities.
pub struct Host {
    state: Arc<Mutex<State>>,
    story_lab: bool,
}
impl Default for Host {
    fn default() -> Self {
        Self::new(false)
    }
}
impl Host {
    pub fn new(story_lab: bool) -> Self {
        Self {
            state: Arc::default(),
            story_lab,
        }
    }
    pub fn call(&self, input: &[u8]) -> Value {
        let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            if input.len() > MAX_INPUT {
                return reject("TooLarge");
            }
            let Ok(envelope) = serde_json::from_slice::<Envelope>(input) else {
                return reject("Malformed");
            };
            if envelope.version != HOST_VERSION {
                return reject("Version");
            }
            if let HostCommand::Prepare {
                session,
                scope,
                turn,
            } = envelope.command
            {
                return self.prepare(&session, &scope, &turn);
            }
            let mut state = self.state.lock().unwrap();
            self.dispatch(&mut state, envelope.command)
        }))
        .unwrap_or_else(|_| reject("Internal"));
        if serde_json::to_vec(&result).map_or(true, |bytes| bytes.len() > MAX_OUTPUT) {
            reject("TooLarge")
        } else {
            result
        }
    }
    /// Window/process teardown invalidates all outstanding leases before dropping sessions.
    pub fn close_all(&self) {
        if let Ok(mut state) = self.state.lock() {
            for session in state.sessions.values() {
                for turn in session.turns.values() {
                    turn.cancel.cancel();
                }
            }
            state.sessions.clear();
        }
    }
    fn dispatch(&self, state: &mut State, command: HostCommand) -> Value {
        match command {
            HostCommand::Capabilities {} => {
                ok(json!({"domain_version":VERSION,"seed":"lantern-quay-v1",
                "typed_actions":true,"free_text":false,"persistence":false,"snapshot_export":false,
                "author":false,"story_lab":self.story_lab,"max_sessions":MAX_SESSIONS,"max_turns":MAX_TURNS}))
            }
            HostCommand::ModelStatus {} => {
                ok(json!({"provider":"deterministic-fake-v1","real_model":false,"loaded":false}))
            }
            HostCommand::Create { seed } => {
                if seed != "lantern-quay-v1" {
                    return reject("UnsupportedSeed");
                }
                if state.sessions.len() >= MAX_SESSIONS {
                    return reject("SessionLimit");
                }
                let Some(next) = state.next.checked_add(1) else {
                    return reject("IdExhausted");
                };
                state.next = next;
                let id = format!("session-{next}");
                let mut seed: Seed =
                    serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json"))
                        .unwrap();
                // Each creation is a new ephemeral story. Windows sharing a story
                // must open its existing session, not create a second authority.
                seed.scope.story = format!("quay-{next}");
                let engine = Engine::new(seed).unwrap();
                let data =
                    json!({"session":id,"scope":engine.scope(),"revision":engine.revision()});
                state.sessions.insert(
                    id,
                    Session {
                        engine,
                        turns: BTreeMap::new(),
                    },
                );
                ok(data)
            }
            HostCommand::Open { session, scope } => match get_session(state, &session, &scope) {
                Ok(s) => {
                    ok(json!({"session":session,"scope":scope,"revision":s.engine.revision()}))
                }
                Err(e) => e,
            },
            HostCommand::Close { session, scope } => {
                let s = match get_session(state, &session, &scope) {
                    Ok(s) => s,
                    Err(e) => return e,
                };
                for turn in s.turns.values() {
                    turn.cancel.cancel();
                }
                state.sessions.remove(&session);
                ok(json!({"closed":true}))
            }
            HostCommand::Submit {
                session,
                request,
                mode,
            } => {
                let s = match get_session(state, &session, &request.scope) {
                    Ok(s) => s,
                    Err(e) => return e,
                };
                if let Some(turn) = s.turns.get(&request.turn) {
                    return if turn.request == request && turn.mode == mode {
                        ok(turn.view())
                    } else {
                        reject("RetryMismatch")
                    };
                }
                if s.turns.len() >= MAX_TURNS {
                    return reject("TurnLimit");
                }
                if let Err(e) = s.engine.preflight(&request) {
                    return reject(e);
                }
                if let Err(e) =
                    Engine::proposal(&request).and_then(|p| s.engine.preview(&request, &p))
                {
                    return reject(e);
                }
                let id = request.turn.clone();
                s.turns.insert(
                    id.clone(),
                    Turn {
                        request,
                        mode,
                        cancel: Cancellation::default(),
                        phase: Phase::Queued,
                        receipt: None,
                        error: None,
                    },
                );
                ok(s.turns[&id].view())
            }
            HostCommand::Commit {
                session,
                scope,
                turn,
            } => {
                let s = match get_session(state, &session, &scope) {
                    Ok(s) => s,
                    Err(e) => return e,
                };
                let Some(t) = s.turns.get_mut(&turn) else {
                    return reject("UnknownTurn");
                };
                if t.phase == Phase::Committed {
                    return ok(t.view());
                }
                if t.phase != Phase::Ready {
                    return reject("NotReady");
                }
                if t.cancel.is_cancelled() {
                    t.phase = Phase::Cancelled;
                    return ok(t.view());
                }
                let receipt = t.receipt.as_ref().unwrap();
                // Refuse an oversized prospective reply before changing canon. Lost transport
                // replies can then always be recovered with the same bounded turn lookup.
                let reply = ok(
                    json!({"turn":t.request.turn,"scope":scope,"expected_revision":t.request.expected_revision,
                    "phase":"committed","error":null,"receipt":receipt}),
                );
                if serde_json::to_vec(&reply).unwrap().len() > MAX_OUTPUT {
                    return reject("TooLarge");
                }
                match s.engine.commit(
                    &t.request,
                    &Engine::proposal(&t.request).unwrap(),
                    receipt.narration(),
                ) {
                    Ok(receipt) => {
                        t.receipt = Some(receipt);
                        t.phase = Phase::Committed;
                    }
                    Err(e) => {
                        t.phase = if e == Error::Stale {
                            Phase::Stale
                        } else {
                            Phase::Failed
                        };
                        t.error = Some(e.to_string());
                        t.receipt = None;
                    }
                }
                ok(t.view())
            }
            HostCommand::Cancel {
                session,
                scope,
                turn,
            } => {
                let s = match get_session(state, &session, &scope) {
                    Ok(s) => s,
                    Err(e) => return e,
                };
                let Some(t) = s.turns.get_mut(&turn) else {
                    return reject("UnknownTurn");
                };
                if t.phase.active() {
                    t.cancel.cancel();
                    t.phase = Phase::Cancelled;
                    t.receipt = None;
                }
                ok(t.view())
            }
            HostCommand::TurnStatus {
                session,
                scope,
                turn,
            } => {
                let s = match get_session(state, &session, &scope) {
                    Ok(s) => s,
                    Err(e) => return e,
                };
                match s.turns.get(&turn) {
                    Some(t) => ok(t.view()),
                    None => reject("UnknownTurn"),
                }
            }
            HostCommand::Inspect {
                session,
                scope,
                observer,
                expected_revision,
            } => {
                let s = match get_session(state, &session, &scope) {
                    Ok(s) => s,
                    Err(e) => return e,
                };
                if expected_revision != s.engine.revision() {
                    return reject("Stale");
                }
                if observer == "omniscient" {
                    if !self.story_lab {
                        return reject("Forbidden");
                    }
                    ok(
                        json!({"scope":scope,"observer":observer,"revision":s.engine.revision(),"state":s.engine.state(),"receipts":s.engine.receipts()}),
                    )
                } else {
                    if observer != s.engine.seed().player && !self.story_lab {
                        return reject("Forbidden");
                    }
                    match s
                        .engine
                        .character_context(&observer, &scope, expected_revision)
                    {
                        Ok(context) => ok(json!({"context":context})),
                        Err(e) => reject(e),
                    }
                }
            }
            HostCommand::FreeText { session, request } => {
                if let Err(e) = get_session(state, &session, &request.scope) {
                    return e;
                }
                reject("Unsupported")
            }
            HostCommand::SnapshotExport {
                session,
                scope,
                expected_revision,
            } => {
                let s = match get_session(state, &session, &scope) {
                    Ok(s) => s,
                    Err(e) => return e,
                };
                if expected_revision != s.engine.revision() {
                    return reject("Stale");
                }
                reject("Unsupported")
            }
            HostCommand::Prepare { .. } => unreachable!(),
        }
    }
    fn prepare(&self, session: &str, scope: &Scope, turn: &str) -> Value {
        let work = match self.begin_work(session, scope, turn) {
            Ok(work) => work,
            Err(value) => return value,
        };
        // A clone of a coherent revision; no canonical lock or transaction during generation.
        let mut engine = work.engine.clone();
        let result = execute(
            &mut engine,
            &work.request,
            &mut work.mode.provider(),
            &work.cancel,
            Budget::default(),
        );
        self.finish_work(work, result)
    }
    fn begin_work(&self, session: &str, scope: &Scope, turn: &str) -> Result<Work, Value> {
        let mut state = self.state.lock().unwrap();
        if state.workers >= MAX_WORKERS {
            return Err(reject("WorkerLimit"));
        }
        let s = get_session(&mut state, session, scope)?;
        let Some(t) = s.turns.get_mut(turn) else {
            return Err(reject("UnknownTurn"));
        };
        if t.phase != Phase::Queued {
            return Err(ok(t.view()));
        }
        t.phase = Phase::Running;
        let work = Work {
            state: self.state.clone(),
            session: session.into(),
            turn: turn.into(),
            engine: s.engine.clone(),
            request: t.request.clone(),
            mode: t.mode,
            cancel: t.cancel.clone(),
        };
        state.workers += 1;
        Ok(work)
    }
    fn finish_work(&self, work: Work, result: Result<Receipt, Error>) -> Value {
        let mut state = self.state.lock().unwrap();
        let Some(s) = state.sessions.get_mut(&work.session) else {
            return reject("Closed");
        };
        let t = s.turns.get_mut(&work.turn).unwrap();
        if t.phase == Phase::Cancelled || work.cancel.is_cancelled() {
            t.phase = Phase::Cancelled;
            t.error = Some("Cancelled".into());
            return ok(t.view());
        }
        if s.engine.revision() != work.request.expected_revision {
            t.phase = Phase::Stale;
            t.error = Some("Stale".into());
        } else {
            match result {
                Ok(receipt) => {
                    t.phase = Phase::Ready;
                    t.receipt = Some(receipt);
                }
                Err(e) => {
                    t.phase = if e == Error::Cancelled {
                        Phase::Cancelled
                    } else {
                        Phase::Failed
                    };
                    t.error = Some(e.to_string());
                }
            }
        }
        ok(t.view())
    }
}
impl Drop for Host {
    fn drop(&mut self) {
        self.close_all();
    }
}
struct Work {
    state: Arc<Mutex<State>>,
    session: String,
    turn: String,
    engine: Engine,
    request: Request,
    mode: Mode,
    cancel: Cancellation,
}
impl Drop for Work {
    fn drop(&mut self) {
        if let Ok(mut state) = self.state.lock() {
            state.workers -= 1;
        }
    }
}
fn get_session<'a>(
    state: &'a mut State,
    id: &str,
    scope: &Scope,
) -> Result<&'a mut Session, Value> {
    let Some(s) = state.sessions.get_mut(id) else {
        return Err(reject("Closed"));
    };
    if s.engine.scope() != scope {
        return Err(reject("Scope"));
    }
    Ok(s)
}
fn ok(data: Value) -> Value {
    json!({"version":HOST_VERSION,"status":"ok","data":data})
}
fn reject(error: impl std::fmt::Display) -> Value {
    json!({"version":HOST_VERSION,"status":"rejected","error":error.to_string()})
}

#[cfg(test)]
mod tests {
    use super::*;
    fn call(h: &Host, c: Value) -> Value {
        h.call(&serde_json::to_vec(&json!({"version":1,"command":c})).unwrap())
    }
    fn session(h: &Host) -> (String, Scope) {
        let v = call(h, json!({"op":"create","seed":"lantern-quay-v1"}));
        (
            v["data"]["session"].as_str().unwrap().into(),
            serde_json::from_value(v["data"]["scope"].clone()).unwrap(),
        )
    }
    fn request(scope: &Scope, turn: &str) -> Request {
        Request {
            version: 1,
            scope: scope.clone(),
            turn: turn.into(),
            expected_revision: 0,
            intent: Intent::Actions(vec![Command::Give {
                item: "potion".into(),
                to: "mira".into(),
                quantity: 1,
            }]),
        }
    }
    fn submit(h: &Host, id: &str, r: &Request) -> Value {
        call(
            h,
            json!({"op":"submit","session":id,"request":r,"mode":"accepted"}),
        )
    }
    fn op(h: &Host, id: &str, scope: &Scope, turn: &str, op: &str) -> Value {
        call(h, json!({"op":op,"session":id,"scope":scope,"turn":turn}))
    }
    #[test]
    fn schema_is_generated_from_rust() {
        let checked: Value =
            serde_json::from_str(include_str!("../../../apps/desktop/host-v1.schema.json"))
                .unwrap();
        assert_eq!(schema(), checked);
    }
    #[test]
    fn transport_and_scope_reject_without_changes() {
        let h = Host::default();
        let (id, scope) = session(&h);
        assert_eq!(h.call(b"{")["error"], "Malformed");
        for bytes in [
            &[255_u8][..],
            br#"{"version":1,"extra":true,"command":{"op":"capabilities"}}"#,
            br#"{"version":1,"command":{"op":"run_sql"}}"#,
            br#"{"version":1.5,"command":{"op":"capabilities"}}"#,
        ] {
            assert_eq!(h.call(bytes)["error"], "Malformed");
        }
        assert_eq!(h.call(&vec![b' '; MAX_INPUT + 1])["error"], "TooLarge");
        assert_eq!(
            h.call(br#"{"version":2,"command":{"op":"capabilities"}}"#)["error"],
            "Version"
        );
        assert_eq!(
            call(&h, json!({"op":"capabilities","extra":true}))["error"],
            "Malformed"
        );
        let mut r = request(&scope, "gift");
        r.scope.branch = "foreign".into();
        assert_eq!(submit(&h, &id, &r)["error"], "Scope");
        let inspect = |observer| {
            call(
                &h,
                json!({"op":"inspect","session":id,"scope":scope,"observer":observer,"expected_revision":0}),
            )
        };
        assert_eq!(inspect("omniscient")["error"], "Forbidden");
        assert_eq!(inspect("mira")["error"], "Forbidden");
        assert_eq!(inspect("player")["status"], "ok");
        r = request(&scope, "gift");
        r.version = 2;
        assert_eq!(submit(&h, &id, &r)["error"], "Version");
        assert_eq!(
            op(&h, &id, &scope, "gift", "turn_status")["error"],
            "UnknownTurn"
        );
    }
    #[test]
    fn native_contract_receipt_matches_headless_and_lost_reply_lookup() {
        let h = Host::new(true);
        let (id, scope) = session(&h);
        let r = request(&scope, "gift");
        assert_eq!(submit(&h, &id, &r)["data"]["phase"], "queued");
        assert_eq!(
            op(&h, &id, &scope, "gift", "prepare")["data"]["phase"],
            "ready"
        );
        let committed = op(&h, &id, &scope, "gift", "commit");
        assert_eq!(committed["data"]["phase"], "committed");
        let mut seed: Seed =
            serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
        seed.scope = scope.clone();
        let mut engine = Engine::new(seed).unwrap();
        let receipt = execute(
            &mut engine,
            &r,
            &mut FakeProvider::new(FakeMode::Accepted),
            &Cancellation::default(),
            Budget::default(),
        )
        .unwrap();
        assert_eq!(
            committed["data"]["receipt"],
            serde_json::to_value(receipt).unwrap()
        );
        assert_eq!(op(&h, &id, &scope, "gift", "turn_status"), committed);
        assert_eq!(submit(&h, &id, &r), committed);
        assert_eq!(op(&h, &id, &scope, "gift", "commit"), committed);
        assert_eq!(op(&h, &id, &scope, "gift", "cancel"), committed);
        let mut changed = r.clone();
        changed.expected_revision = 1;
        assert_eq!(submit(&h, &id, &changed)["error"], "RetryMismatch");
        let view = call(
            &h,
            json!({"op":"inspect","session":id,"scope":scope,"observer":"omniscient","expected_revision":1}),
        );
        assert_eq!(
            view["data"]["state"],
            serde_json::to_value(engine.state()).unwrap()
        );
        for (observer, count) in [("mira", 1), ("sable", 0)] {
            let view = call(
                &h,
                json!({"op":"inspect","session":id,"scope":scope,"observer":observer,"expected_revision":1}),
            );
            assert_eq!(
                view["data"]["context"]["observations"]
                    .as_array()
                    .unwrap()
                    .len(),
                count
            );
        }
        assert_eq!(
            call(
                &h,
                json!({"op":"inspect","session":id,"scope":scope,"observer":"omniscient","expected_revision":0})
            )["error"],
            "Stale"
        );
    }
    #[test]
    fn held_worker_cancel_close_and_stale_completion_are_fenced() {
        let h = Host::default();
        let (id, scope) = session(&h);
        let r = request(&scope, "first");
        submit(&h, &id, &r);
        let work = h.begin_work(&id, &scope, "first").ok().unwrap();
        let success = work
            .engine
            .preview(&work.request, &Engine::proposal(&work.request).unwrap())
            .unwrap();
        assert_eq!(
            op(&h, &id, &scope, "first", "cancel")["data"]["phase"],
            "cancelled"
        );
        assert_eq!(
            h.finish_work(work, Ok(success))["data"]["phase"],
            "cancelled"
        );
        assert_eq!(h.state.lock().unwrap().workers, 0);
        let r = request(&scope, "stale");
        submit(&h, &id, &r);
        let work = h.begin_work(&id, &scope, "stale").ok().unwrap();
        let success = work
            .engine
            .preview(&work.request, &Engine::proposal(&work.request).unwrap())
            .unwrap();
        submit(&h, &id, &request(&scope, "winner"));
        op(&h, &id, &scope, "winner", "prepare");
        op(&h, &id, &scope, "winner", "commit");
        assert_eq!(h.finish_work(work, Ok(success))["data"]["phase"], "stale");
        let mut r = request(&scope, "closed");
        r.expected_revision = 1;
        r.intent = Intent::Actions(vec![Command::Wait { ticks: 1 }]);
        submit(&h, &id, &r);
        let work = h.begin_work(&id, &scope, "closed").ok().unwrap();
        let success = work
            .engine
            .preview(&work.request, &Engine::proposal(&work.request).unwrap())
            .unwrap();
        assert_eq!(
            call(&h, json!({"op":"close","session":id,"scope":scope}))["status"],
            "ok"
        );
        let (new_id, _) = session(&h);
        assert_ne!(new_id, id);
        assert!(work.cancel.is_cancelled());
        assert_eq!(h.finish_work(work, Ok(success))["error"], "Closed");
        assert_eq!(h.state.lock().unwrap().workers, 0);
    }
    #[test]
    fn cancel_commit_race_has_one_canonical_outcome() {
        for _ in 0..20 {
            let h = Host::new(true);
            let (id, scope) = session(&h);
            submit(&h, &id, &request(&scope, "race"));
            op(&h, &id, &scope, "race", "prepare");
            let barrier = std::sync::Barrier::new(2);
            std::thread::scope(|threads| {
                threads.spawn(|| {
                    barrier.wait();
                    op(&h, &id, &scope, "race", "cancel");
                });
                threads.spawn(|| {
                    barrier.wait();
                    op(&h, &id, &scope, "race", "commit");
                });
            });
            let status = op(&h, &id, &scope, "race", "turn_status");
            let state = h.state.lock().unwrap();
            let engine = &state.sessions[&id].engine;
            match status["data"]["phase"].as_str().unwrap() {
                "committed" => {
                    assert_eq!(engine.revision(), 1);
                    assert_eq!(engine.state().items["potion"].owner, "mira");
                }
                "cancelled" => {
                    assert_eq!(engine.revision(), 0);
                    assert_eq!(engine.state().items["potion"].owner, "player");
                }
                phase => panic!("Unexpected phase {phase}"),
            }
        }
    }
    #[test]
    fn ready_work_becomes_stale_at_commit_and_invalid_mechanics_reject() {
        let h = Host::default();
        let (id, scope) = session(&h);
        for turn in ["a", "b"] {
            submit(&h, &id, &request(&scope, turn));
            op(&h, &id, &scope, turn, "prepare");
        }
        assert_eq!(
            op(&h, &id, &scope, "a", "commit")["data"]["phase"],
            "committed"
        );
        assert_eq!(op(&h, &id, &scope, "b", "commit")["data"]["phase"], "stale");
        let mut r = request(&scope, "again");
        r.expected_revision = 1;
        assert_eq!(submit(&h, &id, &r)["error"], "Inventory");
        r.turn = "ability".into();
        r.intent = Intent::Actions(vec![Command::UseAbility {
            ability: "teleport".into(),
        }]);
        assert_eq!(submit(&h, &id, &r)["error"], "Ability");
    }
    #[test]
    fn provider_errors_unsupported_capabilities_and_bounds_are_honest() {
        let h = Host::default();
        let (id, scope) = session(&h);
        for (mode, phase, error) in [
            ("malformed", "failed", "Malformed"),
            ("rejected", "failed", "Agency"),
            ("failed", "failed", "Provider"),
            ("cancelled", "cancelled", "Cancelled"),
        ] {
            let r = request(&scope, mode);
            call(
                &h,
                json!({"op":"submit","session":id,"request":r,"mode":mode}),
            );
            let v = op(&h, &id, &scope, mode, "prepare");
            assert_eq!(v["data"]["phase"], phase);
            assert_eq!(v["data"]["error"], error);
            assert_eq!(h.state.lock().unwrap().workers, 0);
        }
        assert_eq!(
            call(
                &h,
                json!({"op":"free_text","session":id,"request":request(&scope,"text")})
            )["error"],
            "Unsupported"
        );
        assert_eq!(
            call(
                &h,
                json!({"op":"snapshot_export","session":id,"scope":scope,"expected_revision":0})
            )["error"],
            "Unsupported"
        );
        for _ in 1..MAX_SESSIONS {
            session(&h);
        }
        assert_eq!(
            call(&h, json!({"op":"create","seed":"lantern-quay-v1"}))["error"],
            "SessionLimit"
        );
        h.close_all();
        assert!(h.state.lock().unwrap().sessions.is_empty());
    }
    #[test]
    fn bounded_workers_survive_session_churn_and_turn_retention_is_finite() {
        let h = Host::default();
        let mut held = vec![];
        for _ in 0..MAX_WORKERS {
            let (id, scope) = session(&h);
            submit(&h, &id, &request(&scope, "held"));
            held.push(h.begin_work(&id, &scope, "held").ok().unwrap());
            call(&h, json!({"op":"close","session":id,"scope":scope}));
        }
        let (id, scope) = session(&h);
        submit(&h, &id, &request(&scope, "blocked"));
        assert_eq!(
            h.begin_work(&id, &scope, "blocked").err().unwrap()["error"],
            "WorkerLimit"
        );
        drop(held);
        assert_eq!(h.state.lock().unwrap().workers, 0);
        for i in 1..MAX_TURNS {
            submit(&h, &id, &request(&scope, &format!("turn-{i}")));
        }
        assert_eq!(
            submit(&h, &id, &request(&scope, "limit"))["error"],
            "TurnLimit"
        );
    }
    #[test]
    fn creations_have_distinct_story_scopes_and_open_reuses_one_authority() {
        let h = Host::default();
        let (a, scope_a) = session(&h);
        let (b, scope_b) = session(&h);
        assert_ne!(scope_a, scope_b);
        assert_eq!(
            submit(&h, &b, &request(&scope_a, "foreign"))["error"],
            "Scope"
        );
        assert_eq!(
            call(&h, json!({"op":"open","session":a,"scope":scope_a}))["data"]["revision"],
            0
        );
        submit(&h, &a, &request(&scope_a, "gift"));
        op(&h, &a, &scope_a, "gift", "prepare");
        op(&h, &a, &scope_a, "gift", "commit");
        assert_eq!(
            call(&h, json!({"op":"open","session":a,"scope":scope_a}))["data"]["revision"],
            1
        );
        assert_eq!(
            call(&h, json!({"op":"open","session":b,"scope":scope_b}))["data"]["revision"],
            0
        );
    }
}
