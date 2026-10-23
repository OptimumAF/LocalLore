// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Host-v1: bounded in-memory sessions; no JNI, file, SQL, network or model handles.
use crate::turn_trace::{
    self, AttemptHandle, AttemptIdentity, Counts, ErrorCategory, IdentityHash, Label, Outcome,
    Provenance, Reader, Revision, RingSink, Selection, Stage, StageTimer, TraceOwner, TraceRing,
};
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
    Delayed,
    Malformed,
    Rejected,
    Failed,
    Cancelled,
}
impl Mode {
    fn provider(self) -> TimedFake {
        TimedFake {
            delayed: self == Self::Delayed,
            inner: FakeProvider::new(match self {
                Self::Accepted => FakeMode::Accepted,
                Self::Delayed => FakeMode::Delayed { polls: 4 },
                Self::Malformed => FakeMode::Malformed,
                Self::Rejected => FakeMode::Rejected,
                Self::Failed => FakeMode::Failed,
                Self::Cancelled => FakeMode::Cancelled,
            }),
        }
    }
}
// A visibly pending synthetic provider for lifecycle tests and the demo UI.
// No sleep/lock on the UI or canonical owner; generation is on a bounded worker.
struct TimedFake {
    delayed: bool,
    inner: FakeProvider,
}
impl InferenceProvider for TimedFake {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        cancel: &Cancellation,
    ) -> std::task::Poll<Result<Vec<u8>, Error>> {
        if self.delayed && self.inner.calls < 4 && !cancel.is_cancelled() {
            std::thread::sleep(std::time::Duration::from_millis(50));
        }
        self.inner.poll(request, cancel)
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
    Workspace {},
    Resume {
        scope: Scope,
    },
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
    InspectionQuery {
        session: String,
        query: crate::inspection_query::Query,
    },
    TraceConfigure {
        session: String,
        scope: Scope,
        expected_head: u64,
        enabled: bool,
    },
    TraceRead {
        session: String,
        scope: Scope,
        expected_head: u64,
        base_revision: u64,
        observer: crate::inspection_query::Observer,
        turn: Option<String>,
        attempt: Option<u64>,
    },
    TraceClear {
        session: String,
        scope: Scope,
        expected_head: u64,
    },
    TraceCaptureConfigure {
        session: String,
        scope: Scope,
        expected_head: u64,
        enabled: bool,
        consent: bool,
    },
    TraceCaptureRead {
        session: String,
        scope: Scope,
        expected_head: u64,
        base_revision: u64,
        turn: String,
        attempt: u64,
    },
    ModelStatus {},
    PlaySnapshot {
        session: String,
        scope: Scope,
        expected_revision: u64,
    },
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
    trace: Option<AttemptHandle>,
    trace_attempt: u32,
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
    trace_owner: TraceOwner,
}
#[derive(Default)]
struct State {
    next: u64,
    workers: usize,
    sessions: BTreeMap<String, Session>,
    persistence: Option<Box<dyn Persistence>>,
    local_play: Option<LocalPlay>,
}

pub type ProviderFactory = Arc<dyn Fn() -> Box<dyn InferenceProvider + Send> + Send + Sync>;
#[derive(Clone)]
struct LocalPlay {
    profile: crate::play::PlayProfile,
    provider: ProviderFactory,
}

/// Trusted native persistence boundary. Implemented by the one SQLite owner adapter,
/// never deserialized from a model, UI path or accepted-event wire payload.
#[derive(Clone, Debug, Serialize)]
pub struct WorkspaceSummary {
    pub scope: Scope,
    pub title: String,
    pub revision: u64,
    pub drafts: usize,
}
pub struct SavedTurn {
    pub request: Request,
    pub phase: String,
    pub receipt: Option<Receipt>,
}
pub trait Persistence: Send {
    /// Actual SQLite implementation version; workspace host-v1 contract stays separate.
    fn database_schema_version(&self) -> u32 {
        1
    }
    fn location(&self) -> &str;
    fn list(&mut self) -> Result<Vec<WorkspaceSummary>, String>;
    fn create(&mut self) -> Result<Engine, String>;
    fn resume(&mut self, scope: &Scope) -> Result<Engine, String>;
    fn begin(&mut self, request: &Request) -> Result<SavedTurn, String>;
    fn commit(
        &mut self,
        request: &Request,
        proposal: &Proposal,
        narration: &str,
    ) -> Result<Receipt, String>;
    fn commit_prepared(&mut self, receipt: &Receipt) -> Result<Receipt, String> {
        if receipt.play().is_some() {
            return Err("Unsupported".into());
        }
        self.commit(receipt.request(), receipt.proposal(), receipt.narration())
    }
    fn cancel(&mut self, request: &Request) -> Result<SavedTurn, String>;
    fn fail(&mut self, request: &Request) -> Result<SavedTurn, String>;
    fn stale(&mut self, request: &Request) -> Result<SavedTurn, String>;
    fn status(&mut self, scope: &Scope, turn: &str) -> Result<SavedTurn, String>;
}

/// Only trusted native construction grants spoiler inspection. JSON cannot grant capabilities.
pub struct Host {
    state: Arc<Mutex<State>>,
    story_lab: bool,
    trace: Arc<Mutex<TraceRing>>,
}
impl Default for Host {
    fn default() -> Self {
        Self::new(false)
    }
}
impl Host {
    /// Trusted native model owner configures only future work; no wire grants this capability.
    pub fn configure_local_provider(
        &self,
        profile: crate::play::PlayProfile,
        provider: ProviderFactory,
    ) -> Result<(), String> {
        profile.validate().map_err(|e| e.to_string())?;
        self.state
            .lock()
            .map_err(|_| "Internal".to_owned())?
            .local_play = Some(LocalPlay { profile, provider });
        Ok(())
    }
    pub fn disable_local_provider(&self) {
        if let Ok(mut state) = self.state.lock() {
            state.local_play = None;
            for session in state.sessions.values() {
                for turn in session.turns.values() {
                    if matches!(turn.request.intent, Intent::FreeText { .. }) {
                        turn.cancel.cancel();
                    }
                }
            }
        }
    }
    /// Native-only immutable export capture. No path or file-writing capability is on the wire.
    /// Storage is reloaded transactionally before the explicit head check; generation and writes
    /// may continue after this clone is captured, without changing the returned export.
    pub fn inspection_snapshot(
        &self,
        session: &str,
        scope: &Scope,
        expected_revision: u64,
        mode: crate::inspection::ExportMode,
    ) -> Result<crate::inspection::InspectionBundle, String> {
        if mode == crate::inspection::ExportMode::Full && !self.story_lab {
            return Err("Forbidden".into());
        }
        let engine = {
            let mut state = self.state.lock().map_err(|_| "Internal")?;
            let s = state.sessions.get(session).ok_or("Closed")?;
            if s.engine.scope() != scope {
                return Err("Scope".into());
            }
            let cached = s.engine.clone();
            if let Some(port) = state.persistence.as_mut() {
                port.resume(scope)?
            } else {
                cached
            }
        };
        if engine.revision() != expected_revision {
            return Err("Stale".into());
        }
        let timestamp = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map_err(|_| "Clock")?
            .as_millis()
            .try_into()
            .map_err(|_| "Clock")?;
        crate::inspection::capture(&engine, mode, timestamp)
    }
    pub fn with_persistence(story_lab: bool, persistence: Box<dyn Persistence>) -> Self {
        let host = Self::new(story_lab);
        host.state.lock().unwrap().persistence = Some(persistence);
        host
    }
    /// Read-only derived views use one immutable durable snapshot. The inspection grant
    /// comes only from trusted Host construction, never from a query or generation context.
    pub fn inspection_query(
        &self,
        session: &str,
        query: &crate::inspection_query::Query,
    ) -> Result<crate::inspection_query::Page, String> {
        let engine = {
            let mut state = self.state.lock().map_err(|_| "Internal")?;
            let session = state.sessions.get(session).ok_or("Closed")?;
            if session.engine.scope() != &query.scope {
                return Err("Scope".into());
            }
            let cached = session.engine.clone();
            if let Some(port) = state.persistence.as_mut() {
                port.resume(&query.scope)?
            } else {
                cached
            }
        };
        crate::inspection_query::query(&engine, query, self.story_lab).map_err(|e| e.to_string())
    }
    pub fn new(story_lab: bool) -> Self {
        Self {
            state: Arc::default(),
            story_lab,
            trace: Arc::new(Mutex::new(TraceRing::new(
                turn_trace::Config::new(
                    turn_trace::MAX_ATTEMPTS,
                    turn_trace::MAX_STAGES,
                    turn_trace::MAX_BYTES - 2048,
                )
                .unwrap(),
            ))),
        }
    }
    pub fn call(&self, input: &[u8]) -> Value {
        let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            if input.len() > MAX_INPUT {
                return reject("TooLarge");
            }
            let Ok(mut envelope) = serde_json::from_slice::<Envelope>(input) else {
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
            if let HostCommand::InspectionQuery { session, query } = &envelope.command {
                return match self.inspection_query(session, query) {
                    Ok(page) => ok(json!(page)),
                    Err(error) => reject(error),
                };
            }
            let mut state = self.state.lock().unwrap();
            if let HostCommand::FreeText { session, request } = envelope.command {
                if !matches!(request.intent, Intent::FreeText { .. }) {
                    return reject("Unsupported");
                }
                envelope.command = HostCommand::Submit {
                    session,
                    request,
                    mode: Mode::Accepted,
                };
            }
            if let HostCommand::Submit { request, mode, .. } = &envelope.command {
                if matches!(request.intent, Intent::FreeText { .. }) && *mode != Mode::Accepted {
                    return reject("Unsupported");
                }
            }
            self.dispatch_traced(&mut state, envelope.command)
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
                session.trace_owner.retire();
                for turn in session.turns.values() {
                    turn.cancel.cancel();
                }
            }
            state.sessions.clear();
        }
        if let Ok(mut trace) = self.trace.try_lock() {
            trace.set_enabled(false);
        }
    }
    /// Trusted adapter lifecycle evidence, without story content or wire authority.
    pub fn live_counts(&self) -> (usize, usize) {
        let state = self.state.lock().unwrap();
        (state.sessions.len(), state.workers)
    }
    fn trace_command(&self, state: &mut State, command: &HostCommand) -> Option<Value> {
        let (session, scope, head) = match command {
            HostCommand::TraceConfigure {
                session,
                scope,
                expected_head,
                ..
            }
            | HostCommand::TraceRead {
                session,
                scope,
                expected_head,
                ..
            }
            | HostCommand::TraceCaptureConfigure {
                session,
                scope,
                expected_head,
                ..
            }
            | HostCommand::TraceCaptureRead {
                session,
                scope,
                expected_head,
                ..
            }
            | HostCommand::TraceClear {
                session,
                scope,
                expected_head,
            } => (session, scope, *expected_head),
            _ => return None,
        };
        let result = (|| -> Result<Value, Value> {
            let session = get_session(state, session, scope)?;
            let owner = session.trace_owner.clone();
            let cached = session.engine.clone();
            let engine = if let Some(port) = state.persistence.as_mut() {
                port.resume(scope).map_err(reject)?
            } else {
                cached
            };
            if engine.revision() != head {
                return Err(reject("Stale"));
            }
            match command {
                HostCommand::TraceCaptureConfigure {
                    enabled, consent, ..
                } => {
                    if !self.story_lab {
                        return Err(reject("Forbidden"));
                    }
                    if *enabled && !consent {
                        return Err(reject("CaptureConsentRequired"));
                    }
                    let mut trace = self.trace_control()?;
                    if *enabled {
                        trace.set_enabled(true);
                    }
                    trace.configure_details(&owner, scope, *enabled);
                    Ok(ok(
                        json!({"version":1,"scope":scope,"head":head,"enabled":enabled,
                        "capture":"explicit_private_details","retention_seconds":600,
                        "retention":"Access-time expiry/clear; memory only. No forensic erasure or OS paging guarantee.",
                        "caps":{"attempts":3,"bytes":524288,"attempt_bytes":196608,"artifact_bytes":49152},
                        "warning":"Private original input, selected actor context, prompts, raw model outputs and staged proposals. Never uploaded, never included in normal story archives. Future attempts in this exact session only."}),
                    ))
                }
                HostCommand::TraceCaptureRead {
                    base_revision,
                    turn,
                    attempt,
                    ..
                } => {
                    if !self.story_lab {
                        return Err(reject("Forbidden"));
                    }
                    let attempt = u32::try_from(*attempt).map_err(|_| reject("InvalidRequest"))?;
                    let selection = Selection {
                        scope: scope.clone(),
                        base_revision: *base_revision,
                        observer: engine.seed().player.clone(),
                        turn: Some(turn.clone()),
                        attempt: Some(attempt),
                    };
                    let details = self
                        .trace
                        .try_lock()
                        .map_err(|_| reject("TraceUnavailable"))?
                        .read_details_for_owner(
                            &owner,
                            &selection,
                            &Reader::story_lab(scope.clone()),
                        )
                        .map_err(|e| reject(format!("{e:?}")))?;
                    let reply = ok(
                        json!({"scope":scope,"head":head,"base_revision":base_revision,
                        "observer":"private_player_generation_capture","details":details}),
                    );
                    if serde_json::to_vec(&reply).map_or(true, |b| b.len() > MAX_OUTPUT) {
                        return Err(reject("TooLarge"));
                    }
                    Ok(reply)
                }
                HostCommand::TraceRead {
                    base_revision,
                    observer,
                    turn,
                    attempt,
                    ..
                } => {
                    let player = &engine.seed().player;
                    let actor = match observer {
                        crate::inspection_query::Observer::Player => player.clone(),
                        crate::inspection_query::Observer::Character { id } => {
                            if id != player && !self.story_lab {
                                return Err(reject("Forbidden"));
                            }
                            if !engine.state().actors.contains_key(id) {
                                return Err(reject("UnknownObserver"));
                            }
                            id.clone()
                        }
                        crate::inspection_query::Observer::Omniscient => {
                            if !self.story_lab {
                                return Err(reject("Forbidden"));
                            }
                            // Production currently creates player attempts only. The trusted Lab
                            // may inspect those; it cannot relabel them as an NPC's own attempt.
                            player.clone()
                        }
                    };
                    let attempt = attempt
                        .map(u32::try_from)
                        .transpose()
                        .map_err(|_| reject("InvalidRequest"))?;
                    let query = Selection {
                        scope: scope.clone(),
                        base_revision: *base_revision,
                        observer: actor.clone(),
                        turn: turn.clone(),
                        attempt,
                    };
                    let reader = if self.story_lab {
                        Reader::story_lab(scope.clone())
                    } else {
                        Reader::scoped(scope.clone(), actor)
                    };
                    let trace = self
                        .trace
                        .try_lock()
                        .map_err(|_| reject("TraceUnavailable"))?;
                    let snapshot = trace
                        .read_for_owner(&owner, &query, &reader)
                        .map_err(|e| reject(format!("{e:?}")))?;
                    let reply = ok(
                        json!({"scope":scope,"head":head,"base_revision":base_revision,
                        "observer":observer,"configuration_scope":"window_host",
                        "capture":"metadata_only","full_capture":"unsupported","snapshot":snapshot}),
                    );
                    if serde_json::to_vec(&reply).map_or(true, |b| b.len() > turn_trace::MAX_BYTES)
                    {
                        return Err(reject("TooLarge"));
                    }
                    Ok(reply)
                }
                HostCommand::TraceConfigure { enabled, .. } => {
                    let mut trace = self.trace_control()?;
                    trace.set_enabled(*enabled);
                    Ok(ok(
                        json!({"configuration_scope":"window_host","capture":"metadata_only",
                        "enabled":enabled,"full_capture":"unsupported"}),
                    ))
                }
                HostCommand::TraceClear { .. } => {
                    let mut trace = self.trace_control()?;
                    trace.clear();
                    Ok(ok(
                        json!({"configuration_scope":"window_host","cleared":true,
                        "capture":"metadata_only","full_capture":"unsupported"}),
                    ))
                }
                _ => unreachable!(),
            }
        })();
        Some(result.unwrap_or_else(|reply| reply))
    }
    fn trace_control(&self) -> Result<std::sync::MutexGuard<'_, TraceRing>, Value> {
        match self.trace.try_lock() {
            Ok(trace) => Ok(trace),
            Err(std::sync::TryLockError::Poisoned(error)) => {
                // Recovery deletes only process-local diagnostics. Canonical owners are untouched.
                let mut trace = error.into_inner();
                trace.set_enabled(false);
                self.trace.clear_poison();
                Ok(trace)
            }
            Err(_) => Err(reject("TraceUnavailable")),
        }
    }

    fn trace_record(
        &self,
        handle: Option<&AttemptHandle>,
        timer: StageTimer,
        stage: Stage,
        outcome: Outcome,
        error: Option<ErrorCategory>,
    ) {
        if let Some(handle) = handle {
            if let Ok(mut trace) = self.trace.try_lock() {
                let _ = trace.record_measured(
                    handle,
                    timer.finish(stage, outcome, Counts::default(), error),
                );
            }
        }
    }
    fn trace_finish(&self, handle: Option<&AttemptHandle>, outcome: Outcome) {
        if let Some(handle) = handle {
            if let Ok(mut trace) = self.trace.try_lock() {
                let _ = trace.finish(handle, outcome);
            }
        }
    }
    fn dispatch_traced(&self, state: &mut State, command: HostCommand) -> Value {
        if let Some(reply) = self.trace_command(state, &command) {
            return reply;
        }
        let target = match &command {
            HostCommand::Commit {
                session,
                scope,
                turn,
            }
            | HostCommand::Cancel {
                session,
                scope,
                turn,
            }
            | HostCommand::TurnStatus {
                session,
                scope,
                turn,
            } => Some((session, scope, turn)),
            HostCommand::Submit {
                session, request, ..
            } => Some((session, &request.scope, &request.turn)),
            _ => None,
        };
        let binding = target.and_then(|(session, scope, turn)| {
            let s = state.sessions.get(session)?;
            if s.engine.scope() != scope {
                return None;
            }
            let t = s.turns.get(turn)?;
            Some((
                session.clone(),
                turn.clone(),
                t.trace.clone()?,
                t.request.clone(),
                t.receipt.clone(),
                t.trace_attempt,
            ))
        });
        let reply = self.dispatch(state, command);
        if let Some((session, turn, handle, request, prepared, attempt)) = binding {
            // Saved status refreshes must not lose the original process-local attempt lease.
            if let Some(t) = state
                .sessions
                .get_mut(&session)
                .and_then(|s| s.turns.get_mut(&turn))
            {
                if t.request == request && t.trace.is_none() {
                    t.trace = Some(handle.clone());
                    t.trace_attempt = attempt;
                }
            }
            if let Some(outcome) = trace_reply_outcome(&reply, prepared.as_ref()) {
                self.trace_finish(Some(&handle), outcome);
            }
        }
        reply
    }
    fn dispatch(&self, state: &mut State, command: HostCommand) -> Value {
        if state.persistence.is_some() {
            if let Some(reply) = self.dispatch_durable(state, &command) {
                return reply;
            }
        }
        match command {
            HostCommand::Workspace {} => {
                ok(json!({"persistent":false,"location":null,"schema_version":null,"stories":[]}))
            }
            HostCommand::Resume { .. } => reject("Unsupported"),
            HostCommand::Capabilities {} => {
                ok(json!({"domain_version":VERSION,"seed":"lantern-quay-v1",
                "typed_actions":true,"free_text":state.local_play.is_some(),"persistence":false,"snapshot_export":false,
                "author":false,"story_lab":self.story_lab,"max_sessions":MAX_SESSIONS,"max_turns":MAX_TURNS}))
            }
            HostCommand::ModelStatus {} => {
                if let Some(local) = &state.local_play {
                    ok(
                        json!({"provider":local.profile.id,"real_model":true,"loaded":null,"status":"configured_native_owner","profile":local.profile}),
                    )
                } else {
                    ok(
                        json!({"provider":"deterministic-fake-v1","real_model":false,"loaded":false}),
                    )
                }
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
                        trace_owner: TraceOwner::default(),
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
                    if turn.phase.active() {
                        self.trace_finish(turn.trace.as_ref(), Outcome::Cancelled);
                    }
                }
                if let Some(closed) = state.sessions.remove(&session) {
                    closed.trace_owner.retire();
                    if let Ok(mut trace) = self.trace.try_lock() {
                        trace.revoke_details(&closed.trace_owner);
                    }
                }
                ok(json!({"closed":true}))
            }
            HostCommand::Submit {
                session,
                request,
                mode,
            } => {
                let available = state.local_play.is_some();
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
                if matches!(request.intent, Intent::FreeText { .. }) && !available {
                    return reject("Unsupported");
                }
                if s.turns.len() >= MAX_TURNS {
                    return reject("TurnLimit");
                }
                if let Err(e) = s.engine.preflight(&request) {
                    return reject(e);
                }
                if !matches!(request.intent, Intent::FreeText { .. }) {
                    if let Err(e) =
                        Engine::proposal(&request).and_then(|p| s.engine.preview(&request, &p))
                    {
                        return reject(e);
                    }
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
                        trace: None,
                        trace_attempt: 0,
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
                    self.trace_finish(t.trace.as_ref(), Outcome::Cancelled);
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
                let timer = StageTimer::start();
                let outcome = s.engine.commit_prepared(receipt);
                self.trace_record(
                    t.trace.as_ref(),
                    timer,
                    Stage::AtomicCommit,
                    if outcome.is_ok() {
                        Outcome::Committed
                    } else if matches!(outcome, Err(Error::Stale)) {
                        Outcome::Stale
                    } else {
                        Outcome::Failed
                    },
                    outcome.as_ref().err().map(ErrorCategory::from_engine),
                );
                match outcome {
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
            HostCommand::PlaySnapshot {
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
                let player = &s.engine.seed().player;
                let context = s
                    .engine
                    .character_context(player, &scope, expected_revision)
                    .unwrap();
                let inventory: BTreeMap<_, _> = s
                    .engine
                    .state()
                    .items
                    .iter()
                    .filter(|(_, item)| &item.owner == player)
                    .collect();
                // All currently supported receipts resolve the player's explicit typed
                // requests. This is not an omniscient event feed for future NPC jobs.
                ok(
                    json!({"scope":scope,"revision":expected_revision,"rules":s.engine.seed().profile,"player":context,
                    "inventory":inventory,"receipts":s.engine.receipts()}),
                )
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
            HostCommand::Prepare { .. }
            | HostCommand::InspectionQuery { .. }
            | HostCommand::TraceConfigure { .. }
            | HostCommand::TraceRead { .. }
            | HostCommand::TraceClear { .. } => unreachable!(),
            HostCommand::TraceCaptureConfigure { .. } | HostCommand::TraceCaptureRead { .. } => {
                unreachable!()
            }
        }
    }

    fn dispatch_durable(&self, state: &mut State, command: &HostCommand) -> Option<Value> {
        let result = (|| -> Result<Value, Value> {
            match command {
                HostCommand::Capabilities {} => Ok(ok(
                    json!({"domain_version":VERSION,"seed":"lantern-quay-v1",
                    "typed_actions":true,"free_text":state.local_play.is_some(),"persistence":true,"snapshot_export":false,
                    "author":false,"story_lab":self.story_lab,"max_sessions":MAX_SESSIONS,"max_turns":MAX_TURNS}),
                )),
                HostCommand::Workspace {} => {
                    let port = state.persistence.as_mut().unwrap();
                    let stories = port.list().map_err(reject)?;
                    Ok(ok(
                        json!({"persistent":true,"location":port.location(),"schema_version":1,"database_schema_version":port.database_schema_version(),"stories":stories}),
                    ))
                }
                HostCommand::Create { seed } => {
                    if seed != "lantern-quay-v1" {
                        return Err(reject("UnsupportedSeed"));
                    }
                    if state.sessions.len() >= MAX_SESSIONS {
                        return Err(reject("SessionLimit"));
                    }
                    let engine = state
                        .persistence
                        .as_mut()
                        .unwrap()
                        .create()
                        .map_err(reject)?;
                    Ok(attach_engine(state, engine))
                }
                HostCommand::Resume { scope } => {
                    if let Some(id) = state
                        .sessions
                        .iter()
                        .find(|(_, s)| s.engine.scope() == scope)
                        .map(|(id, _)| id.clone())
                    {
                        refresh_session(state, &id, scope)?;
                        return Ok(ok(
                            json!({"session":id,"scope":scope,"revision":state.sessions[&id].engine.revision()}),
                        ));
                    }
                    if state.sessions.len() >= MAX_SESSIONS {
                        return Err(reject("SessionLimit"));
                    }
                    let engine = state
                        .persistence
                        .as_mut()
                        .unwrap()
                        .resume(scope)
                        .map_err(reject)?;
                    Ok(attach_engine(state, engine))
                }
                HostCommand::Open { session, scope } => {
                    get_session(state, session, scope)?;
                    let engine = state
                        .persistence
                        .as_mut()
                        .unwrap()
                        .resume(scope)
                        .map_err(reject)?;
                    let revision = engine.revision();
                    get_session(state, session, scope)?.engine = engine;
                    Ok(ok(
                        json!({"session":session,"scope":scope,"revision":revision}),
                    ))
                }
                HostCommand::Submit {
                    session,
                    request,
                    mode,
                } => {
                    let s = get_session(state, session, &request.scope)?;
                    if let Some(t) = s.turns.get(&request.turn) {
                        if t.request != *request || t.mode != *mode {
                            return Err(reject("RetryMismatch"));
                        }
                    } else if s.turns.len() >= MAX_TURNS {
                        return Err(reject("TurnLimit"));
                    }
                    if matches!(request.intent, Intent::FreeText { .. })
                        && state.local_play.is_none()
                    {
                        let saved = state
                            .persistence
                            .as_mut()
                            .unwrap()
                            .status(&request.scope, &request.turn)
                            .map_err(|e| {
                                reject(if e == "UnknownTurn" {
                                    "Unsupported".to_owned()
                                } else {
                                    e
                                })
                            })?;
                        if saved.request != *request {
                            return Err(reject("RetryMismatch"));
                        }
                        if saved.phase == "draft" {
                            return Err(reject("Unsupported"));
                        }
                        refresh_session(state, session, &request.scope)?;
                        let t = saved_turn(saved, *mode)?;
                        let reply = ok(t.view());
                        get_session(state, session, &request.scope)?
                            .turns
                            .insert(request.turn.clone(), t);
                        return Ok(reply);
                    }
                    let saved = state
                        .persistence
                        .as_mut()
                        .unwrap()
                        .begin(request)
                        .map_err(reject)?;
                    refresh_session(state, session, &request.scope)?;
                    let s = get_session(state, session, &request.scope)?;
                    if saved.phase != "draft" {
                        let t = saved_turn(saved, *mode)?;
                        let reply = ok(t.view());
                        s.turns.insert(request.turn.clone(), t);
                        return Ok(reply);
                    }
                    if let Some(t) = s.turns.get(&request.turn) {
                        return Ok(ok(t.view()));
                    }
                    if !matches!(request.intent, Intent::FreeText { .. }) {
                        if let Err(error) =
                            Engine::proposal(request).and_then(|p| s.engine.preview(request, &p))
                        {
                            let _ = state.persistence.as_mut().unwrap().fail(request);
                            return Err(reject(error));
                        }
                    }
                    let t = saved_turn(saved, *mode)?;
                    let reply = ok(t.view());
                    get_session(state, session, &request.scope)?
                        .turns
                        .insert(request.turn.clone(), t);
                    Ok(reply)
                }
                HostCommand::TurnStatus {
                    session,
                    scope,
                    turn,
                } => {
                    get_session(state, session, scope)?;
                    let saved = state
                        .persistence
                        .as_mut()
                        .unwrap()
                        .status(scope, turn)
                        .map_err(reject)?;
                    refresh_session(state, session, scope)?;
                    let s = get_session(state, session, scope)?;
                    if saved.phase == "draft" {
                        if let Some(t) = s.turns.get(turn) {
                            return Ok(ok(t.view()));
                        }
                    }
                    let mode = s.turns.get(turn).map_or(Mode::Accepted, |t| t.mode);
                    let t = saved_turn(saved, mode)?;
                    let reply = ok(t.view());
                    s.turns.insert(turn.clone(), t);
                    Ok(reply)
                }
                HostCommand::Cancel {
                    session,
                    scope,
                    turn,
                } => {
                    let s = get_session(state, session, scope)?;
                    if let Some(t) = s.turns.get_mut(turn) {
                        t.cancel.cancel();
                    }
                    let original = state
                        .persistence
                        .as_mut()
                        .unwrap()
                        .status(scope, turn)
                        .map_err(reject)?;
                    let saved = state
                        .persistence
                        .as_mut()
                        .unwrap()
                        .cancel(&original.request)
                        .map_err(reject)?;
                    refresh_session(state, session, scope)?;
                    let s = get_session(state, session, scope)?;
                    let mode = s.turns.get(turn).map_or(Mode::Accepted, |t| t.mode);
                    let t = saved_turn(saved, mode)?;
                    let reply = ok(t.view());
                    s.turns.insert(turn.clone(), t);
                    Ok(reply)
                }
                HostCommand::Commit {
                    session,
                    scope,
                    turn,
                } => {
                    get_session(state, session, scope)?;
                    let stored = state
                        .persistence
                        .as_mut()
                        .unwrap()
                        .status(scope, turn)
                        .map_err(reject)?;
                    if stored.phase != "draft" {
                        refresh_session(state, session, scope)?;
                        let s = get_session(state, session, scope)?;
                        let mode = s.turns.get(turn).map_or(Mode::Accepted, |t| t.mode);
                        let t = saved_turn(stored, mode)?;
                        let reply = ok(t.view());
                        s.turns.insert(turn.clone(), t);
                        return Ok(reply);
                    }
                    let s = get_session(state, session, scope)?;
                    let t = s.turns.get_mut(turn).ok_or_else(|| reject("NotReady"))?;
                    if t.cancel.is_cancelled() {
                        return Err(reject("Cancelled"));
                    }
                    if t.phase != Phase::Ready {
                        return Err(reject("NotReady"));
                    }
                    let prepared = t.receipt.clone().unwrap();
                    let trace = t.trace.clone();
                    let request = t.request.clone();
                    let mode = t.mode;
                    let reply = ok(
                        json!({"turn":turn,"scope":scope,"expected_revision":request.expected_revision,
                        "phase":"committed","error":null,"receipt":prepared}),
                    );
                    if serde_json::to_vec(&reply).unwrap().len() > MAX_OUTPUT {
                        return Err(reject("TooLarge"));
                    }
                    let timer = StageTimer::start();
                    match state
                        .persistence
                        .as_mut()
                        .unwrap()
                        .commit_prepared(&prepared)
                    {
                        Ok(receipt) => {
                            self.trace_record(
                                trace.as_ref(),
                                timer,
                                Stage::AtomicCommit,
                                Outcome::Committed,
                                None,
                            );
                            self.trace_finish(trace.as_ref(), Outcome::Committed);
                            refresh_session(state, session, scope)?;
                            let s = get_session(state, session, scope)?;
                            let t = saved_turn(
                                SavedTurn {
                                    request,
                                    phase: "committed".into(),
                                    receipt: Some(receipt),
                                },
                                mode,
                            )?;
                            let reply = ok(t.view());
                            s.turns.insert(turn.clone(), t);
                            Ok(reply)
                        }
                        Err(error) => {
                            // A failed acknowledgement may still have committed. Lookup before
                            // reporting failure; if lookup also fails, preserve recoverable ownership.
                            let lookup = state.persistence.as_mut().unwrap().status(scope, turn);
                            match lookup {
                                Ok(saved) if saved.phase != "draft" => {
                                    let outcome = trace_saved_outcome(&saved, Some(&prepared));
                                    self.trace_record(
                                        trace.as_ref(),
                                        timer,
                                        Stage::AtomicCommit,
                                        outcome,
                                        None,
                                    );
                                    self.trace_finish(trace.as_ref(), outcome);
                                    refresh_session(state, session, scope)?;
                                    let t = saved_turn(saved, mode)?;
                                    let reply = ok(t.view());
                                    get_session(state, session, scope)?
                                        .turns
                                        .insert(turn.clone(), t);
                                    Ok(reply)
                                }
                                Ok(_) => {
                                    self.trace_record(
                                        trace.as_ref(),
                                        timer,
                                        Stage::AtomicCommit,
                                        Outcome::Failed,
                                        Some(trace_category(&error)),
                                    );
                                    Err(reject(error))
                                }
                                Err(_) => {
                                    self.trace_record(
                                        trace.as_ref(),
                                        timer,
                                        Stage::AtomicCommit,
                                        Outcome::Unknown,
                                        Some(ErrorCategory::Unknown),
                                    );
                                    Err(reject("TransportUnknown"))
                                }
                            }
                        }
                    }
                }
                HostCommand::Close { session, scope } => {
                    let s = get_session(state, session, scope)?;
                    let active: Vec<_> = s
                        .turns
                        .values()
                        .filter(|t| t.phase.active())
                        .map(|t| {
                            t.cancel.cancel();
                            (t.request.clone(), t.trace.clone(), t.receipt.clone())
                        })
                        .collect();
                    for (request, trace, prepared) in active {
                        let saved = state.persistence.as_mut().unwrap().cancel(&request);
                        let outcome = saved.as_ref().map_or(Outcome::Unknown, |saved| {
                            trace_saved_outcome(saved, prepared.as_ref())
                        });
                        self.trace_finish(trace.as_ref(), outcome);
                    }
                    if let Some(closed) = state.sessions.remove(session) {
                        closed.trace_owner.retire();
                        if let Ok(mut trace) = self.trace.try_lock() {
                            trace.revoke_details(&closed.trace_owner);
                        }
                    }
                    Ok(ok(json!({"closed":true,"saved":true})))
                }
                _ => Ok(Value::Null),
            }
        })();
        match result {
            Ok(Value::Null) => None,
            Ok(value) | Err(value) => Some(value),
        }
    }
    fn prepare(&self, session: &str, scope: &Scope, turn: &str) -> Value {
        let work = match self.begin_work(session, scope, turn) {
            Ok(work) => work,
            Err(value) => return value,
        };
        // A clone of a coherent revision; no canonical lock or transaction during generation.
        let mut engine = work.engine.clone();
        let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            if matches!(work.request.intent, Intent::FreeText { .. }) {
                if let Some(local) = &work.local_play {
                    let mut sink = work
                        .trace
                        .clone()
                        .map(|handle| RingSink::new(Arc::clone(&self.trace), handle));
                    crate::play::execute_traced(
                        &mut engine,
                        &work.request,
                        &mut *(local.provider)(),
                        &work.cancel,
                        &local.profile,
                        sink.as_mut()
                            .map(|sink| sink as &mut dyn turn_trace::TraceSink),
                    )
                } else {
                    Err(Error::Provider)
                }
            } else {
                let timer = StageTimer::start();
                let result = execute(
                    &mut engine,
                    &work.request,
                    &mut work.mode.provider(),
                    &work.cancel,
                    Budget::default(),
                );
                let outcome = match &result {
                    Ok(_) => Outcome::Accepted,
                    Err(Error::Cancelled) => Outcome::Cancelled,
                    Err(Error::Stale) => Outcome::Stale,
                    Err(_) => Outcome::Failed,
                };
                self.trace_record(
                    work.trace.as_ref(),
                    timer,
                    Stage::AcceptedCandidate,
                    outcome,
                    result.as_ref().err().map(ErrorCategory::from_engine),
                );
                result
            }
        }))
        .unwrap_or(Err(Error::Provider));
        self.finish_work(work, result)
    }
    fn begin_work(&self, session: &str, scope: &Scope, turn: &str) -> Result<Work, Value> {
        let mut state = self.state.lock().unwrap();
        if state.workers >= MAX_WORKERS {
            return Err(reject("WorkerLimit"));
        }
        let local_play = state.local_play.clone();
        let s = get_session(&mut state, session, scope)?;
        let trace_owner = s.trace_owner.clone();
        let Some(t) = s.turns.get_mut(turn) else {
            return Err(reject("UnknownTurn"));
        };
        if t.phase != Phase::Queued {
            return Err(ok(t.view()));
        }
        t.phase = Phase::Running;
        t.trace = t.trace_attempt.checked_add(1).and_then(|attempt| {
            t.trace_attempt = attempt;
            let identity = AttemptIdentity {
                scope: t.request.scope.clone(),
                base_revision: t.request.expected_revision,
                observer: s.engine.seed().player.clone(),
                turn: t.request.turn.clone(),
                attempt,
            };
            self.trace.try_lock().ok().and_then(|mut trace| {
                trace
                    .begin_for_owner(
                        &trace_owner,
                        identity,
                        trace_provenance(
                            local_play.as_ref(),
                            matches!(t.request.intent, Intent::FreeText { .. }),
                        ),
                    )
                    .handle
            })
        });
        let work = Work {
            state: self.state.clone(),
            session: session.into(),
            turn: turn.into(),
            engine: s.engine.clone(),
            request: t.request.clone(),
            mode: t.mode,
            cancel: t.cancel.clone(),
            local_play,
            trace: t.trace.clone(),
        };
        state.workers += 1;
        Ok(work)
    }
    fn finish_work(&self, work: Work, result: Result<Receipt, Error>) -> Value {
        let prepared = if work.trace.is_some() {
            result.as_ref().ok().cloned()
        } else {
            None
        };
        let timer = StageTimer::start();
        let reply = self.finish_work_inner(&work, result);
        let terminal = trace_reply_outcome(&reply, prepared.as_ref());
        let outcome = terminal.unwrap_or_else(|| {
            if reply["status"] == "rejected" {
                Outcome::Unknown
            } else {
                Outcome::Accepted
            }
        });
        let error = reply["data"]["error"]
            .as_str()
            .or_else(|| reply["error"].as_str())
            .map(trace_category);
        self.trace_record(
            work.trace.as_ref(),
            timer,
            Stage::Publication,
            if outcome == Outcome::Committed {
                Outcome::Accepted
            } else {
                outcome
            },
            error,
        );
        if let Some(outcome) = terminal {
            self.trace_finish(work.trace.as_ref(), outcome);
        } else if reply["status"] == "rejected" {
            self.trace_finish(
                work.trace.as_ref(),
                if reply["error"] == "Closed" {
                    Outcome::Cancelled
                } else {
                    Outcome::Unknown
                },
            );
        }
        reply
    }
    fn finish_work_inner(&self, work: &Work, result: Result<Receipt, Error>) -> Value {
        let mut state = self.state.lock().unwrap();
        // Generation runs without the owner lock. Another process may have finalized
        // this key meanwhile; its persisted outcome must win over this worker.
        if state.persistence.is_some() && state.sessions.contains_key(&work.session) {
            let observed = (|| -> Result<Option<Value>, Value> {
                let saved = state
                    .persistence
                    .as_mut()
                    .unwrap()
                    .status(&work.request.scope, &work.turn)
                    .map_err(reject)?;
                refresh_session(&mut state, &work.session, &work.request.scope)?;
                if saved.phase == "draft" {
                    return Ok(None);
                }
                let t = saved_turn(saved, work.mode)?;
                let reply = ok(t.view());
                state
                    .sessions
                    .get_mut(&work.session)
                    .unwrap()
                    .turns
                    .insert(work.turn.clone(), t);
                Ok(Some(reply))
            })();
            match observed {
                Ok(Some(reply)) => return reply,
                Err(reply) => {
                    // The worker is ending without a durable observation. Leave
                    // its original key retryable after a transient read failure.
                    if let Some(t) = state
                        .sessions
                        .get_mut(&work.session)
                        .and_then(|s| s.turns.get_mut(&work.turn))
                    {
                        if t.phase == Phase::Running {
                            t.phase = Phase::Queued;
                        }
                    }
                    return reply;
                }
                Ok(None) => {}
            }
        }
        let Some(s) = state.sessions.get_mut(&work.session) else {
            return reject("Closed");
        };
        let t = s.turns.get_mut(&work.turn).unwrap();
        if !t.phase.active() {
            return ok(t.view());
        }
        if t.phase == Phase::Cancelled || work.cancel.is_cancelled() {
            t.phase = Phase::Cancelled;
            t.error = Some("Cancelled".into());
        } else if s.engine.revision() != work.request.expected_revision {
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
        let phase = t.phase;
        let reply = ok(t.view());
        if let Some(port) = state.persistence.as_mut() {
            let saved = match phase {
                Phase::Cancelled => Some(port.cancel(&work.request)),
                Phase::Failed => Some(port.fail(&work.request)),
                Phase::Stale => Some(port.stale(&work.request)),
                _ => None,
            };
            if let Some(saved) = saved {
                let saved = match saved {
                    Ok(saved) => saved,
                    Err(error) => {
                        // This outcome is still provisional. Status/retry must never
                        // advertise a terminal cache entry that storage did not accept.
                        let t = state
                            .sessions
                            .get_mut(&work.session)
                            .unwrap()
                            .turns
                            .get_mut(&work.turn)
                            .unwrap();
                        t.phase = Phase::Queued;
                        t.error = None;
                        t.receipt = None;
                        return reject(error);
                    }
                };
                if saved.phase
                    != match phase {
                        Phase::Cancelled => "cancelled",
                        Phase::Failed => "failed",
                        Phase::Stale => "stale",
                        _ => "draft",
                    }
                {
                    if let Err(reply) =
                        refresh_session(&mut state, &work.session, &work.request.scope)
                    {
                        return reply;
                    }
                    if let Ok(t) = saved_turn(saved, work.mode) {
                        let reply = ok(t.view());
                        state
                            .sessions
                            .get_mut(&work.session)
                            .unwrap()
                            .turns
                            .insert(work.turn.clone(), t);
                        return reply;
                    }
                }
            }
        }
        reply
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
    local_play: Option<LocalPlay>,
    trace: Option<AttemptHandle>,
}
fn trace_category(error: &str) -> ErrorCategory {
    match error {
        "Version" => ErrorCategory::Version,
        "Scope" => ErrorCategory::Scope,
        "Stale" => ErrorCategory::Stale,
        "RetryMismatch" => ErrorCategory::RetryMismatch,
        "Malformed" => ErrorCategory::Malformed,
        "TooLarge" => ErrorCategory::TooLarge,
        "Agency" => ErrorCategory::Agency,
        "AuthorUiRequired" => ErrorCategory::AuthorUiRequired,
        "ClarificationRequired" => ErrorCategory::ClarificationRequired,
        "UnknownReference" => ErrorCategory::UnknownReference,
        "DeadActor" => ErrorCategory::DeadActor,
        "Location" => ErrorCategory::Location,
        "Inventory" => ErrorCategory::Inventory,
        "Resource" => ErrorCategory::Resource,
        "Ability" => ErrorCategory::Ability,
        "Knowledge" => ErrorCategory::Knowledge,
        "Rule" => ErrorCategory::Rule,
        "Cancelled" | "Closed" => ErrorCategory::Cancelled,
        "Provider" => ErrorCategory::Provider,
        "Timeout" => ErrorCategory::Deadline,
        "Narration" => ErrorCategory::Narration,
        "CorruptHistory" => ErrorCategory::CorruptHistory,
        "Busy" => ErrorCategory::Busy,
        "Unsupported" => ErrorCategory::Unsupported,
        _ => ErrorCategory::Unknown,
    }
}
fn trace_reply_outcome(reply: &Value, prepared: Option<&Receipt>) -> Option<Outcome> {
    if reply["status"] != "ok" {
        return None;
    }
    match reply["data"]["phase"].as_str() {
        Some("committed") => Some(
            if prepared.and_then(|r| serde_json::to_value(r).ok()).as_ref()
                == Some(&reply["data"]["receipt"])
            {
                Outcome::Committed
            } else {
                Outcome::Stale
            },
        ),
        Some("failed") => Some(Outcome::Failed),
        Some("cancelled") => Some(Outcome::Cancelled),
        Some("stale") => Some(Outcome::Stale),
        _ => None,
    }
}
fn trace_saved_outcome(saved: &SavedTurn, prepared: Option<&Receipt>) -> Outcome {
    match saved.phase.as_str() {
        "committed" => {
            if saved.receipt.as_ref() == prepared {
                Outcome::Committed
            } else {
                Outcome::Stale
            }
        }
        "cancelled" => Outcome::Cancelled,
        "failed" => Outcome::Failed,
        "stale" => Outcome::Stale,
        _ => Outcome::Unknown,
    }
}
fn trace_provenance(local: Option<&LocalPlay>, free_text: bool) -> Provenance {
    if free_text {
        if let Some(local) = local {
            use sha2::{Digest, Sha256};
            let profile = &local.profile;
            return Provenance {
                model_sha256: IdentityHash::sha256(&profile.model_sha256),
                worker_sha256: IdentityHash::sha256(&profile.worker_sha256),
                profile_sha256: IdentityHash::sha256(&profile.profile_manifest_sha256),
                runtime_revision: Revision::new(&profile.runtime_revision),
                config_sha256: serde_json::to_vec(profile).ok().and_then(|bytes| {
                    IdentityHash::sha256(&format!("{:x}", Sha256::digest(bytes)))
                }),
                profile_label: Label::new(&profile.id),
                prompt_label: Label::new(crate::play::PROMPT_VERSION),
                schema_label: Label::new("locallore-play-v2"),
                ..Provenance::default()
            };
        }
    }
    Provenance {
        profile_label: Label::new("deterministic-fake-v1"),
        ..Provenance::default()
    }
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
fn refresh_session(state: &mut State, id: &str, scope: &Scope) -> Result<(), Value> {
    get_session(state, id, scope)?;
    let engine = state
        .persistence
        .as_mut()
        .unwrap()
        .resume(scope)
        .map_err(reject)?;
    get_session(state, id, scope)?.engine = engine;
    Ok(())
}
fn attach_engine(state: &mut State, engine: Engine) -> Value {
    let Some(next) = state.next.checked_add(1) else {
        return reject("IdExhausted");
    };
    state.next = next;
    let id = format!("session-{next}");
    let data = json!({"session":id,"scope":engine.scope(),"revision":engine.revision()});
    state.sessions.insert(
        id,
        Session {
            engine,
            turns: BTreeMap::new(),
            trace_owner: TraceOwner::default(),
        },
    );
    ok(data)
}
fn saved_turn(saved: SavedTurn, mode: Mode) -> Result<Turn, Value> {
    let phase = match saved.phase.as_str() {
        "draft" => Phase::Queued,
        "committed" => Phase::Committed,
        "cancelled" => Phase::Cancelled,
        "failed" => Phase::Failed,
        "stale" => Phase::Stale,
        _ => return Err(reject("Integrity")),
    };
    Ok(Turn {
        request: saved.request,
        mode,
        cancel: Cancellation::default(),
        phase,
        receipt: saved.receipt,
        error: match phase {
            Phase::Cancelled => Some("Cancelled".into()),
            Phase::Stale => Some("Stale".into()),
            // The existing durable port records the terminal phase, not its cause.
            // Do not fabricate a provider failure when an old validation failed.
            Phase::Failed => None,
            _ => None,
        },
        trace: None,
        trace_attempt: 0,
    })
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
    fn trace_busy_and_poison_never_decide_gameplay_and_reconfigure_recovers() {
        for poison in [false, true] {
            let h = Host::default();
            let (id, scope) = session(&h);
            assert_eq!(
                call(
                    &h,
                    json!({"op":"trace_configure","session":id,"scope":scope,"expected_head":0,"enabled":true})
                )["status"],
                "ok"
            );
            let r = request(&scope, "gift");
            if poison {
                let trace = Arc::clone(&h.trace);
                let _ = std::thread::spawn(move || {
                    let _guard = trace.lock().unwrap();
                    panic!("synthetic trace poison");
                })
                .join();
                assert_eq!(submit(&h, &id, &r)["data"]["phase"], "queued");
                assert_eq!(
                    op(&h, &id, &scope, "gift", "prepare")["data"]["phase"],
                    "ready"
                );
                assert_eq!(
                    op(&h, &id, &scope, "gift", "commit")["data"]["phase"],
                    "committed"
                );
            } else {
                let _guard = h.trace.lock().unwrap();
                assert_eq!(submit(&h, &id, &r)["data"]["phase"], "queued");
                assert_eq!(
                    op(&h, &id, &scope, "gift", "prepare")["data"]["phase"],
                    "ready"
                );
                assert_eq!(
                    op(&h, &id, &scope, "gift", "commit")["data"]["phase"],
                    "committed"
                );
            }
            assert_eq!(
                call(
                    &h,
                    json!({"op":"trace_configure","session":id,"scope":scope,"expected_head":1,"enabled":true})
                )["status"],
                "ok"
            );
            let read = call(
                &h,
                json!({"op":"trace_read","session":id,"scope":scope,"expected_head":1,"base_revision":0,"observer":{"kind":"player"}}),
            );
            assert_eq!(read["status"], "ok");
            assert!(read["data"]["snapshot"]["attempts"]
                .as_array()
                .unwrap()
                .is_empty());
        }
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
    #[test]
    fn play_snapshot_is_coherent_and_excludes_other_actors_and_beliefs() {
        let h = Host::default();
        let (id, scope) = session(&h);
        let view = call(
            &h,
            json!({"op":"play_snapshot","session":id,"scope":scope,"expected_revision":0}),
        );
        assert_eq!(view["data"]["revision"], 0);
        assert_eq!(view["data"]["player"]["observer"], "player");
        assert!(view["data"].get("state").is_none());
        assert!(view["data"]["player"]["beliefs"]
            .as_array()
            .unwrap()
            .iter()
            .all(|b| b["believer"] == "player"));
        assert_eq!(view["data"]["inventory"]["potion"]["owner"], "player");
        submit(&h, &id, &request(&scope, "gift"));
        op(&h, &id, &scope, "gift", "prepare");
        op(&h, &id, &scope, "gift", "commit");
        assert_eq!(
            call(
                &h,
                json!({"op":"play_snapshot","session":id,"scope":scope,"expected_revision":0})
            )["error"],
            "Stale"
        );
        let view = call(
            &h,
            json!({"op":"play_snapshot","session":id,"scope":scope,"expected_revision":1}),
        );
        assert!(view["data"]["inventory"].get("potion").is_none());
        assert_eq!(view["data"]["receipts"].as_array().unwrap().len(), 1);
    }
    #[test]
    fn private_capture_owner_retires_even_when_trace_lock_is_busy_but_not_on_model_unload() {
        let h = Host::new(true);
        let (id, _) = session(&h);
        let owner = h.state.lock().unwrap().sessions[&id].trace_owner.clone();
        h.disable_local_provider();
        assert!(owner.live(), "model unload does not close a session");
        let held_trace = h.trace.lock().unwrap();
        h.close_all();
        assert!(
            !owner.live(),
            "close revokes access independently of the busy diagnostic lock"
        );
        assert!(h.state.lock().unwrap().sessions.is_empty());
        drop(held_trace);
    }
}
