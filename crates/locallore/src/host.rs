// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Host-v1: bounded in-memory sessions; no JNI, file, SQL, network or model handles.
use crate::turn_trace::{
    self, AttemptHandle, AttemptIdentity, Counts, ErrorCategory, IdentityHash, Label, Outcome,
    Provenance, Reader, Revision, RingSink, Selection, Stage, StageTimer, TraceOwner, TraceRing,
};
use crate::{
    contracts::*,
    engine::{AcceptedHistoryBasis, Engine},
    inference::*,
};
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::{
    collections::BTreeMap,
    sync::{Arc, Mutex},
};

pub const HOST_VERSION: u16 = 1;
mod author_port;
pub use author_port::{HostAuthorPreparation, NativeAuthorPreparation, WorkspaceAuthorOutcomeV1};
pub mod memory_maintenance;
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
    Branches {
        story: String,
    },
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
    /// Narrowing private diagnostic access needs no current canonical head.
    TraceCaptureRevoke {
        session: String,
        scope: Scope,
    },
    ModelStatus {},
    PlaySnapshot {
        session: String,
        scope: Scope,
        expected_revision: u64,
    },
    PlaySnapshotV2 {
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
    basis: Option<AcceptedHistoryBasis>,
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
    work_owner: Arc<()>,
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
/// Trusted native selection only; neither JSON nor an inspection lens grants it.
/// ```compile_fail,E0277
/// use locallore::host::HostPlayConstructionV1;
/// fn serialize<T: serde::Serialize>() {}
/// serialize::<HostPlayConstructionV1>();
/// ```
/// ```compile_fail,E0277
/// use locallore::host::HostPlayConstructionV1;
/// fn deserialize<T: serde::de::DeserializeOwned>() {}
/// deserialize::<HostPlayConstructionV1>();
/// ```
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum HostPlayConstructionV1 {
    Memory(crate::play::PlayContextPolicy),
    PlayerLiteralV1,
}
impl HostPlayConstructionV1 {
    fn labels(self) -> (&'static str, &'static str) {
        match self {
            Self::Memory(_) => (crate::play::PROMPT_VERSION, "locallore-play-v2"),
            Self::PlayerLiteralV1 => (
                crate::play::LITERAL_PLAY_PROMPT_VERSION_V1,
                "locallore-director-literal-v1",
            ),
        }
    }
}
#[derive(Clone, Copy)]
enum GenerationReadKind {
    Memory,
    Canonical,
}
#[derive(Clone)]
struct LocalPlay {
    profile: crate::play::PlayProfile,
    provider: ProviderFactory,
    real_model: bool,
    construction: HostPlayConstructionV1,
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
#[derive(Clone, Debug, Serialize, PartialEq, Eq)]
pub struct WorkspaceBranch {
    pub scope: Scope,
    pub parent_branch: Option<String>,
    pub fork_revision: Option<u64>,
    pub revision: u64,
    pub drafts: usize,
    pub retired: bool,
}
#[derive(Clone, Debug, Serialize, PartialEq, Eq)]
pub struct WorkspaceBranchCatalog {
    pub version: u16,
    pub story_id: String,
    pub title: String,
    pub root_branch: String,
    pub branches: Vec<WorkspaceBranch>,
}
/// Trusted native fork identity. This is deliberately not a HostCommand or a
/// deserializable author capability. The expected head guards new creation only.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct WorkspaceForkRequest {
    pub parent: Scope,
    pub child_branch: String,
    pub expected_parent_revision: u64,
    pub at_revision: u64,
}
#[derive(Clone, Debug, Serialize, PartialEq, Eq)]
pub struct WorkspaceForkOutcome {
    pub version: u16,
    pub scope: Scope,
    pub parent: Scope,
    pub fork_revision: u64,
    pub head_revision: u64,
    pub created: bool,
}
/// Native-only coherent generation input. This is neither a wire payload nor an
/// inspection grant. Consumers must recheck an opaque proof against this Engine
/// at consumption; missing cache remains honest exact-raw fallback.
pub struct HostGenerationSnapshot {
    pub engine: Engine,
    pub coverage: crate::memory_coverage::CoverageRead,
}
fn check_generation_cancel(cancel: &dyn Fn() -> bool) -> Result<(), String> {
    if std::panic::catch_unwind(std::panic::AssertUnwindSafe(cancel)).unwrap_or(true) {
        Err("Cancelled".into())
    } else {
        Ok(())
    }
}
fn validate_generation_engine(
    engine: &Engine,
    scope: &Scope,
    expected_head: u64,
    observer: &str,
) -> Result<(), String> {
    if engine.scope() != scope {
        return Err("Scope".into());
    }
    if engine.revision() != expected_head || engine.seed().player != observer {
        return Err("Stale".into());
    }
    Ok(())
}
fn generation_read_error(error: String) -> String {
    // Only this selected-session port treats a missing/replaced source or player
    // as a stale basis. Other persistence ports retain their existing mapping.
    if error == "NotFound" {
        "Stale".into()
    } else {
        error
    }
}
pub struct SavedTurn {
    pub request: Request,
    pub phase: String,
    pub receipt: Option<Receipt>,
}
#[derive(Clone, Copy)]
pub enum DraftDisposition {
    Cancelled,
    Failed,
    Stale,
}
pub trait Persistence: Send {
    /// Native-only capability; legacy ports fail closed without a Store owner.
    fn prepare_author_correction(
        &mut self,
        _input: &crate::author_correction::AuthorCorrectionInputV1,
        _cancel: &dyn Fn() -> bool,
    ) -> Result<Box<dyn NativeAuthorPreparation>, String> {
        Err("Unsupported".into())
    }
    fn apply_author_correction(
        &mut self,
        _prepared: &dyn NativeAuthorPreparation,
        _cancel: &dyn Fn() -> bool,
    ) -> Result<WorkspaceAuthorOutcomeV1, String> {
        Err("Unsupported".into())
    }
    fn lookup_author_correction(
        &mut self,
        _input: &crate::author_correction::AuthorCorrectionInputV1,
        _cancel: &dyn Fn() -> bool,
    ) -> Result<Option<WorkspaceAuthorOutcomeV1>, String> {
        Err("Unsupported".into())
    }
    fn begin_bound(
        &mut self,
        _request: &Request,
        _basis: &AcceptedHistoryBasis,
    ) -> Result<SavedTurn, String> {
        Err("Unsupported".into())
    }
    fn status_bound(
        &mut self,
        _request: &Request,
        _basis: &AcceptedHistoryBasis,
    ) -> Result<SavedTurn, String> {
        Err("Unsupported".into())
    }
    /// Implementations must compare the basis atomically with canonical writes.
    /// Legacy ports fail closed rather than pretending a read then write is atomic.
    fn commit_prepared_bound(
        &mut self,
        _receipt: &Receipt,
        _basis: &AcceptedHistoryBasis,
    ) -> Result<Receipt, String> {
        Err("Unsupported".into())
    }
    fn finish_bound(
        &mut self,
        _request: &Request,
        _basis: &AcceptedHistoryBasis,
        _phase: DraftDisposition,
    ) -> Result<SavedTurn, String> {
        Err("Unsupported".into())
    }
    /// Trusted native maintenance uses the existing selected canonical source.
    /// Unsupported ports cannot silently create a competing maintenance owner.
    fn memory_maintenance(
        &mut self,
        _selected: &Engine,
        _expected_head: u64,
        _action: memory_maintenance::MaintenanceAction,
        _cancel: &dyn Fn() -> bool,
    ) -> Result<memory_maintenance::MaintenanceReply, memory_maintenance::MaintenanceError> {
        Err(memory_maintenance::MaintenanceError::Unsupported)
    }
    /// Recheck public target admission even before returning process-cached work.
    fn validate_scope(&mut self, _scope: &Scope) -> Result<(), String> {
        Ok(())
    }
    /// Actual SQLite implementation version; workspace host-v1 contract stays separate.
    fn database_schema_version(&self) -> u32 {
        1
    }
    fn location(&self) -> &str;
    fn list(&mut self) -> Result<Vec<WorkspaceSummary>, String>;
    fn branches(&mut self, _story: &str) -> Result<WorkspaceBranchCatalog, String> {
        Err("Unsupported".into())
    }
    fn fork_branch(
        &mut self,
        _request: &WorkspaceForkRequest,
        _cancel: &dyn Fn() -> bool,
    ) -> Result<WorkspaceForkOutcome, String> {
        Err("Unsupported".into())
    }
    fn create(&mut self) -> Result<Engine, String>;
    fn resume(&mut self, scope: &Scope) -> Result<Engine, String>;
    fn generation_snapshot(
        &mut self,
        scope: &Scope,
        expected_head: u64,
        observer: &str,
        cancel: &dyn Fn() -> bool,
    ) -> Result<HostGenerationSnapshot, String> {
        check_generation_cancel(cancel)?;
        let engine = self.resume(scope).map_err(generation_read_error)?;
        validate_generation_engine(&engine, scope, expected_head, observer)?;
        check_generation_cancel(cancel)?;
        Ok(HostGenerationSnapshot {
            engine,
            coverage: crate::memory_coverage::CoverageRead::RawFallback(
                crate::memory_coverage::FallbackReason::Missing,
            ),
        })
    }
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
        self.configure_local_provider_with_policy(
            profile,
            provider,
            crate::play::PlayContextPolicy::StateRelevantMemoryV1,
        )
    }
    /// Trusted native construction policy for future work only. No JSON capability.
    pub fn configure_local_provider_with_policy(
        &self,
        profile: crate::play::PlayProfile,
        provider: ProviderFactory,
        policy: crate::play::PlayContextPolicy,
    ) -> Result<(), String> {
        self.configure_local_provider_with_construction(
            profile,
            provider,
            HostPlayConstructionV1::Memory(policy),
        )
    }
    /// Configure only future native work. No wire operation selects this enum.
    pub fn configure_local_provider_with_construction(
        &self,
        profile: crate::play::PlayProfile,
        provider: ProviderFactory,
        construction: HostPlayConstructionV1,
    ) -> Result<(), String> {
        self.configure_provider(profile, provider, true, construction)
    }
    /// Synthetic plumbing, configured by trusted native code only. Never claims a real model.
    pub fn configure_fixture_provider(
        &self,
        profile: crate::play::PlayProfile,
        provider: ProviderFactory,
    ) -> Result<(), String> {
        self.configure_fixture_provider_with_policy(
            profile,
            provider,
            crate::play::PlayContextPolicy::StateRelevantMemoryV1,
        )
    }
    /// Synthetic native policy plumbing; never claims a real model or comparison run.
    pub fn configure_fixture_provider_with_policy(
        &self,
        profile: crate::play::PlayProfile,
        provider: ProviderFactory,
        policy: crate::play::PlayContextPolicy,
    ) -> Result<(), String> {
        self.configure_fixture_provider_with_construction(
            profile,
            provider,
            HostPlayConstructionV1::Memory(policy),
        )
    }
    /// Synthetic native plumbing, including literal construction. Always keeps
    /// the fixture label; configuring a construction does not run a model.
    pub fn configure_fixture_provider_with_construction(
        &self,
        profile: crate::play::PlayProfile,
        provider: ProviderFactory,
        construction: HostPlayConstructionV1,
    ) -> Result<(), String> {
        self.configure_provider(profile, provider, false, construction)
    }
    fn configure_provider(
        &self,
        profile: crate::play::PlayProfile,
        provider: ProviderFactory,
        real_model: bool,
        construction: HostPlayConstructionV1,
    ) -> Result<(), String> {
        profile.validate().map_err(|e| e.to_string())?;
        self.state
            .lock()
            .map_err(|_| "Internal".to_owned())?
            .local_play = Some(LocalPlay {
            profile,
            provider,
            real_model,
            construction,
        });
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
    /// Native-only durable fork. Does not select the child, refresh an existing
    /// session, or confer inspection/author privileges. The owner lock serializes
    /// local turn admission/publication with the Store transaction; generation
    /// already admitted on this parent must settle before a fork is requested.
    pub fn fork_branch(
        &self,
        session: &str,
        request: &WorkspaceForkRequest,
        cancel: &dyn Fn() -> bool,
    ) -> Result<WorkspaceForkOutcome, String> {
        let mut state = self.state.lock().map_err(|_| "Internal")?;
        let selected = state.sessions.get(session).ok_or("Closed")?;
        if selected.engine.scope() != &request.parent {
            return Err("Scope".into());
        }
        if state.sessions.values().any(|selected| {
            selected.engine.scope() == &request.parent
                && selected.turns.values().any(|turn| turn.phase.active())
        }) {
            return Err("Busy".into());
        }
        // Store owns completed boundaries, cancellation and immutable child
        // retry. In particular, do not reject an existing-child retry by checking
        // expected_parent_revision against this process's cached or current head.
        // A successful return is committed even if cancellation arrives later.
        state
            .persistence
            .as_mut()
            .ok_or("Unsupported")?
            .fork_branch(request, cancel)
    }
    /// Read-only native generation input, independent of spoiler inspection.
    /// The selected seed fixes the player; neither JSON nor the caller supplies
    /// an observer. Does not admit jobs, select/refresh sessions or run a provider.
    pub fn generation_snapshot(
        &self,
        session: &str,
        scope: &Scope,
        expected_head: u64,
        cancel: &dyn Fn() -> bool,
    ) -> Result<HostGenerationSnapshot, String> {
        let (engine, coverage) = self.generation_read(
            session,
            scope,
            expected_head,
            cancel,
            GenerationReadKind::Memory,
        )?;
        Ok(HostGenerationSnapshot {
            engine,
            coverage: coverage.ok_or("Internal")?,
        })
    }
    fn literal_generation_engine(
        &self,
        session: &str,
        scope: &Scope,
        expected_head: u64,
        cancel: &dyn Fn() -> bool,
    ) -> Result<Engine, String> {
        self.generation_read(
            session,
            scope,
            expected_head,
            cancel,
            GenerationReadKind::Canonical,
        )
        .map(|(engine, _)| engine)
    }
    // Both source paths share the same selected-session/seed/prefix/cancel
    // fence. Canonical mode uses the existing coherent resume transaction and
    // never obtains, fabricates or drops a derived-memory proof.
    fn generation_read(
        &self,
        session: &str,
        scope: &Scope,
        expected_head: u64,
        cancel: &dyn Fn() -> bool,
        kind: GenerationReadKind,
    ) -> Result<(Engine, Option<crate::memory_coverage::CoverageRead>), String> {
        let mut state = self.state.lock().map_err(|_| "Internal")?;
        let selected = state.sessions.get(session).ok_or("Closed")?;
        if selected.engine.scope() != scope {
            return Err("Scope".into());
        }
        let selected_seed = selected.engine.seed().clone();
        let ephemeral = state.persistence.is_none().then(|| selected.engine.clone());
        let observed_cancelled = std::cell::Cell::new(false);
        let safe_cancel = || {
            if !observed_cancelled.get() {
                observed_cancelled.set(check_generation_cancel(cancel).is_err());
            }
            observed_cancelled.get()
        };
        check_generation_cancel(&safe_cancel)?;
        let (engine, coverage) = if let Some(port) = state.persistence.as_mut() {
            // Overrides receive the same panic-safe cancellation boundary as
            // the default port. An observed true/panic remains cancelled even
            // if an override ignores it and returns an otherwise valid Engine.
            // Contain a native override failure inside the guard so it cannot
            // poison every later operation on this owner.
            std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| match kind {
                GenerationReadKind::Memory => port
                    .generation_snapshot(scope, expected_head, &selected_seed.player, &safe_cancel)
                    .map(|snapshot| (snapshot.engine, Some(snapshot.coverage))),
                GenerationReadKind::Canonical => port.resume(scope).map(|engine| (engine, None)),
            }))
            .map_err(|_| "Internal")?
            .map_err(generation_read_error)?
        } else {
            (
                ephemeral.expect("selected ephemeral Engine"),
                matches!(kind, GenerationReadKind::Memory).then(|| {
                    crate::memory_coverage::CoverageRead::RawFallback(
                        crate::memory_coverage::FallbackReason::Missing,
                    )
                }),
            )
        };
        validate_generation_engine(&engine, scope, expected_head, &selected_seed.player)?;
        if engine.seed() != &selected_seed {
            return Err("Stale".into());
        }
        // A matching seed/head does not identify immutable accepted history:
        // an archive can replace a deleted scope with different receipts or
        // ancestry. Permit another owner's append only to this exact prefix.
        let selected = &state.sessions.get(session).ok_or("Closed")?.engine;
        if !engine
            .extends_accepted_history(selected)
            .map_err(|_| "Stale")?
        {
            return Err("Stale".into());
        }
        check_generation_cancel(&safe_cancel)?;
        Ok((engine, coverage))
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
        {
            // Cleanup must revoke leases even if gameplay previously poisoned
            // State. Do not clear poison or resume gameplay with this guard.
            let mut state = self.state.lock().unwrap_or_else(|p| p.into_inner());
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
    /// Trusted storage lifecycle notification, never an LLM/Host wire command.
    /// The adapter fences new submit/commit/resume calls through the deletion transaction.
    pub fn invalidate_story(&self, story: &str) {
        let mut state = self.state.lock().unwrap_or_else(|p| p.into_inner());
        state.sessions.retain(|_, session| {
            if session.engine.scope().story != story {
                return true;
            }
            session.trace_owner.retire();
            for turn in session.turns.values() {
                turn.cancel.cancel();
            }
            false
        });
        drop(state);
        // Clear immediately when available. Removed sessions cannot read retained
        // metadata; retired owners fence late private writes and purge on next access
        // if a diagnostic reader currently holds the lock.
        if let Ok(mut trace) = self.trace.try_lock() {
            trace.clear();
        }
    }
    /// Remove only retired/collected targets. Retained descendant sessions stay live.
    pub fn invalidate_branches(&self, story: &str, branches: &[String]) {
        // Lifecycle cleanup must revoke capabilities even after gameplay poison;
        // recovering this guard does not clear poison or authorize more gameplay.
        let mut state = self.state.lock().unwrap_or_else(|p| p.into_inner());
        let mut owners = Vec::new();
        state.sessions.retain(|_, session| {
            let scope = session.engine.scope();
            if scope.story != story || !branches.contains(&scope.branch) {
                return true;
            }
            session.trace_owner.retire();
            owners.push(session.trace_owner.clone());
            for turn in session.turns.values() {
                turn.cancel.cancel();
            }
            false
        });
        drop(state);
        // Retired owner liveness fences late private writes independently of a
        // busy/poisoned diagnostic lock. Preserve unrelated live owner metadata.
        if let Ok(mut trace) = self.trace.try_lock() {
            for owner in owners {
                trace.clear_owner(&owner);
            }
        }
    }
    /// Trusted adapter lifecycle evidence, without story content or wire authority.
    pub fn live_counts(&self) -> (usize, usize) {
        let state = self.state.lock().unwrap();
        (state.sessions.len(), state.workers)
    }
    fn trace_command(&self, state: &mut State, command: &HostCommand) -> Option<Value> {
        if let HostCommand::TraceCaptureRevoke { session, scope } = command {
            let result = (|| -> Result<Value, Value> {
                if !self.story_lab {
                    return Err(reject("Forbidden"));
                }
                // Revocation only removes optional copies. Resolve the live
                // in-memory lease without canonical Store admission or replay:
                // unavailable storage must not prevent narrowing access.
                let selected = state
                    .sessions
                    .get(session)
                    .ok_or_else(|| reject("Closed"))?;
                if selected.engine.scope() != scope {
                    return Err(reject("Scope"));
                }
                let owner = selected.trace_owner.clone();
                // No persistence read, head assertion or canonical mutation is
                // needed to revoke this owner's optional diagnostic copies.
                self.trace_control()?.revoke_details(&owner);
                Ok(ok(json!({"version":1,"scope":scope,"revoked":true})))
            })();
            return Some(result.unwrap_or_else(|reply| reply));
        }
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
            HostCommand::Branches { .. } => reject("Unsupported"),
            HostCommand::Capabilities {} => {
                ok(json!({"domain_version":VERSION,"seed":"lantern-quay-v1",
                "typed_actions":true,"free_text":state.local_play.is_some(),"persistence":false,"snapshot_export":false,
                "author":false,"story_lab":self.story_lab,"max_sessions":MAX_SESSIONS,"max_turns":MAX_TURNS}))
            }
            HostCommand::ModelStatus {} => {
                if let Some(local) = &state.local_play {
                    ok(
                        json!({"provider":local.profile.id,"real_model":local.real_model,
                            "loaded":if local.real_model { Value::Null } else { json!(false) },
                            "status":if local.real_model { "configured_native_owner" } else { "configured_fixture_owner" },
                            "profile":local.profile}),
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
                        work_owner: Arc::new(()),
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
                        basis: None,
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
                    if s.engine.domain_version() != 1 {
                        return reject("Version");
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
            HostCommand::PlaySnapshotV2 {
                session,
                scope,
                expected_revision,
            } => {
                if state.persistence.is_some() {
                    if let Err(error) = refresh_session(state, &session, &scope) {
                        return error;
                    }
                }
                let selected = match get_session(state, &session, &scope) {
                    Ok(selected) => selected,
                    Err(error) => return error,
                };
                let engine = &selected.engine;
                if expected_revision != engine.revision() {
                    return reject("Stale");
                }
                let player = &engine.seed().player;
                let inventory: BTreeMap<_, _> = engine
                    .state()
                    .items
                    .iter()
                    .filter(|(_, item)| &item.owner == player)
                    .collect();
                // Thin native player display only. History/observed facts use
                // separately paged Query2; no context or private record is built.
                ok(json!({"version":2,"domain_version":engine.domain_version(),
                    "scope":engine.scope(),"revision":engine.revision(),"rules":engine.seed().profile,
                    "player":{"observer":player,"self_state":engine.state().actors[player]},
                    "inventory":inventory}))
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
                let context = match s
                    .engine
                    .character_context(player, &scope, expected_revision)
                {
                    Ok(context) => context,
                    Err(error) => return reject(error),
                };
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
            HostCommand::TraceCaptureConfigure { .. }
            | HostCommand::TraceCaptureRead { .. }
            | HostCommand::TraceCaptureRevoke { .. } => {
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
                HostCommand::Branches { story } => {
                    let catalog = state
                        .persistence
                        .as_mut()
                        .unwrap()
                        .branches(story)
                        .map_err(reject)?;
                    let reply = ok(json!(catalog));
                    if serde_json::to_vec(&reply).map_or(true, |bytes| bytes.len() > 64 * 1024) {
                        return Err(reject("TooLarge"));
                    }
                    Ok(reply)
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
                    let selected = get_session(state, session, scope)?;
                    // Open also serves passive frontend refresh. Preserve work
                    // and diagnostic consent for the same accepted source or an
                    // exact append; only a replacement/rewind selects a new owner.
                    if !engine
                        .extends_accepted_history(&selected.engine)
                        .map_err(reject)?
                    {
                        for turn in selected.turns.values() {
                            turn.cancel.cancel();
                            if turn.phase.active() {
                                self.trace_finish(turn.trace.as_ref(), Outcome::Cancelled);
                            }
                        }
                        selected.turns.clear();
                        selected.work_owner = Arc::new(());
                        selected.trace_owner.retire();
                        if let Ok(mut trace) = self.trace.try_lock() {
                            trace.revoke_details(&selected.trace_owner);
                        }
                        selected.trace_owner = TraceOwner::default();
                    }
                    selected.engine = engine;
                    Ok(ok(
                        json!({"session":session,"scope":scope,"revision":revision}),
                    ))
                }
                HostCommand::Submit {
                    session,
                    request,
                    mode,
                } => {
                    refresh_session(state, session, &request.scope)?;
                    let s = get_session(state, session, &request.scope)?;
                    if let Some(t) = s.turns.get(&request.turn) {
                        if t.request != *request || t.mode != *mode {
                            return Err(reject("RetryMismatch"));
                        }
                    } else if s.turns.len() >= MAX_TURNS {
                        return Err(reject("TurnLimit"));
                    }
                    let basis = match s.turns.get(&request.turn).and_then(|t| t.basis.clone()) {
                        Some(basis) => basis,
                        None => s
                            .engine
                            .accepted_history_basis_at(request.expected_revision)
                            .map_err(|error| {
                                reject(if error == Error::Rule {
                                    Error::Stale
                                } else {
                                    error
                                })
                            })?,
                    };
                    if !s.engine.matches_accepted_history(&basis).map_err(reject)? {
                        return Err(reject("Stale"));
                    }
                    let selected_basis = s.engine.accepted_history_basis().map_err(reject)?;
                    let historical = request.expected_revision != s.engine.revision();
                    if matches!(request.intent, Intent::FreeText { .. })
                        && state.local_play.is_none()
                    {
                        let saved = state
                            .persistence
                            .as_mut()
                            .unwrap()
                            .status_bound(request, &selected_basis)
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
                    let port = state.persistence.as_mut().unwrap();
                    // Historical retries are reads. A shorter request prefix must
                    // never admit a new draft if another owner rewinds the source
                    // between refresh and the persistence transaction.
                    let saved = if historical {
                        port.status_bound(request, &selected_basis)
                            .map_err(|error| {
                                reject(if error == "UnknownTurn" {
                                    "Stale".to_owned()
                                } else {
                                    error
                                })
                            })?
                    } else {
                        port.begin_bound(request, &selected_basis).map_err(reject)?
                    };
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
                    if !historical && !matches!(request.intent, Intent::FreeText { .. }) {
                        if let Err(error) =
                            Engine::proposal(request).and_then(|p| s.engine.preview(request, &p))
                        {
                            let _ = state.persistence.as_mut().unwrap().finish_bound(
                                request,
                                &basis,
                                DraftDisposition::Failed,
                            );
                            return Err(reject(error));
                        }
                    }
                    let mut t = saved_turn(saved, *mode)?;
                    t.basis = Some(basis);
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
                    let saved =
                        selected_turn_status(state, session, scope, turn).map_err(reject)?;
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
                    let original =
                        selected_turn_status(state, session, scope, turn).map_err(reject)?;
                    let selected = get_session(state, session, scope)?;
                    let basis = selected.engine.accepted_history_basis().map_err(reject)?;
                    let saved = state
                        .persistence
                        .as_mut()
                        .unwrap()
                        .finish_bound(&original.request, &basis, DraftDisposition::Cancelled)
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
                    let stored =
                        selected_turn_status(state, session, scope, turn).map_err(reject)?;
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
                    let original_basis = t.basis.as_ref().ok_or_else(|| reject("NotReady"))?;
                    if !s
                        .engine
                        .matches_accepted_history(original_basis)
                        .map_err(reject)?
                    {
                        return Err(reject("Stale"));
                    }
                    let basis = s.engine.accepted_history_basis().map_err(reject)?;
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
                    let port = state.persistence.as_mut().unwrap();
                    let committed = if basis.matches_request(&request) {
                        port.commit_prepared_bound(&prepared, &basis)
                    } else {
                        // The selected source has advanced. Terminalize only
                        // under its stronger full prefix, never the old candidate's
                        // shorter prefix after a separate status/read operation.
                        port.finish_bound(&request, &basis, DraftDisposition::Stale)
                            .and_then(|saved| {
                                saved.receipt.ok_or_else(|| {
                                    match saved.phase.as_str() {
                                        "cancelled" => "Cancelled",
                                        "failed" => "Failed",
                                        _ => "Stale",
                                    }
                                    .into()
                                })
                            })
                    };
                    match committed {
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
                            let lookup = state
                                .persistence
                                .as_mut()
                                .unwrap()
                                .status_bound(&request, &basis);
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
                                Err(source_error)
                                    if source_error == "Stale"
                                        || source_error == "RetryMismatch" =>
                                {
                                    self.trace_record(
                                        trace.as_ref(),
                                        timer,
                                        Stage::AtomicCommit,
                                        Outcome::Stale,
                                        Some(trace_category(&source_error)),
                                    );
                                    self.trace_finish(trace.as_ref(), Outcome::Stale);
                                    Err(reject(source_error))
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
                            (
                                t.request.clone(),
                                t.trace.clone(),
                                t.receipt.clone(),
                                s.engine.accepted_history_basis().ok(),
                            )
                        })
                        .collect();
                    for (request, trace, prepared, basis) in active {
                        let saved = match basis {
                            Some(basis) => state.persistence.as_mut().unwrap().finish_bound(
                                &request,
                                &basis,
                                DraftDisposition::Cancelled,
                            ),
                            None => Err("Unsupported".into()),
                        };
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
        let mut work = match self.begin_work(session, scope, turn) {
            Ok(work) => work,
            Err(value) => return value,
        };
        if let (Intent::FreeText { .. }, Some(local)) =
            (&work.request.intent, work.local_play.as_ref())
        {
            let construction = local.construction;
            let snapshot = match construction {
                HostPlayConstructionV1::Memory(_) => self
                    .generation_snapshot(session, scope, work.request.expected_revision, &|| {
                        work.cancel.is_cancelled()
                    })
                    .map(|s| (s.engine, Some(s.coverage))),
                HostPlayConstructionV1::PlayerLiteralV1 => self
                    .literal_generation_engine(
                        session,
                        scope,
                        work.request.expected_revision,
                        &|| work.cancel.is_cancelled(),
                    )
                    .map(|engine| (engine, None)),
            };
            match snapshot {
                Ok((engine, coverage)) => {
                    if construction == HostPlayConstructionV1::PlayerLiteralV1
                        && engine.domain_version() != 1
                    {
                        return self.finish_work(work, Err(Error::Version));
                    }
                    work.engine = engine;
                    work.coverage = coverage;
                }
                Err(error) => return self.generation_input_failure(work, error),
            }
        }
        // A clone of a coherent revision; no canonical lock or transaction during generation.
        let mut engine = work.engine.clone();
        let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            if matches!(work.request.intent, Intent::FreeText { .. }) {
                if let Some(local) = &work.local_play {
                    let mut sink = work
                        .trace
                        .clone()
                        .map(|handle| RingSink::new(Arc::clone(&self.trace), handle));
                    match local.construction {
                        HostPlayConstructionV1::Memory(policy) => {
                            crate::play::execute_traced_with_policy(
                                &mut engine,
                                &work.request,
                                &mut *(local.provider)(),
                                &work.cancel,
                                &local.profile,
                                sink.as_mut()
                                    .map(|sink| sink as &mut dyn turn_trace::TraceSink),
                                crate::play::PlayConstructionInput {
                                    coverage: work
                                        .coverage
                                        .as_ref()
                                        .expect("coherent free-text input"),
                                    policy,
                                },
                            )
                        }
                        HostPlayConstructionV1::PlayerLiteralV1 => {
                            crate::play::execute_traced_with_literal_director_v1(
                                &mut engine,
                                &work.request,
                                &mut *(local.provider)(),
                                &work.cancel,
                                &local.profile,
                                sink.as_mut()
                                    .map(|sink| sink as &mut dyn turn_trace::TraceSink),
                            )
                        }
                    }
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
    fn generation_input_failure(&self, work: Work, error: String) -> Value {
        let terminal = match error.as_str() {
            "Cancelled" | "Closed" => Some(Error::Cancelled),
            "Stale" | "NotFound" => Some(Error::Stale),
            "Scope" => Some(Error::Scope),
            "TooLarge" => Some(Error::TooLarge),
            "Integrity" => Some(Error::CorruptHistory),
            _ => None,
        };
        if let Some(error) = terminal {
            return self.finish_work(work, Err(error));
        }
        // A transient storage read did not run a provider or consume the key.
        // Keep it queued; status/exact retry can observe another owner's commit.
        if let Ok(mut state) = self.state.lock() {
            if let Some(turn) = state
                .sessions
                .get_mut(&work.session)
                .filter(|session| Arc::ptr_eq(&session.work_owner, &work.owner))
                .and_then(|session| session.turns.get_mut(&work.turn))
            {
                if turn.phase == Phase::Running {
                    turn.phase = Phase::Queued;
                    turn.error = None;
                    turn.receipt = None;
                }
            }
        }
        self.trace_record(
            work.trace.as_ref(),
            StageTimer::start(),
            Stage::Retrieval,
            Outcome::Failed,
            Some(trace_category(&error)),
        );
        self.trace_finish(work.trace.as_ref(), Outcome::Unknown);
        reject(error)
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
        let basis = match &t.basis {
            Some(basis) => basis.clone(),
            None => s
                .engine
                .accepted_history_basis_at(t.request.expected_revision)
                .map_err(reject)?,
        };
        if !s.engine.matches_accepted_history(&basis).map_err(reject)? {
            return Err(reject("Stale"));
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
            owner: s.work_owner.clone(),
            engine: s.engine.clone(),
            request: t.request.clone(),
            mode: t.mode,
            cancel: t.cancel.clone(),
            local_play,
            trace: t.trace.clone(),
            coverage: None,
            basis,
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
        if !state
            .sessions
            .get(&work.session)
            .is_some_and(|session| Arc::ptr_eq(&session.work_owner, &work.owner))
        {
            return reject("Closed");
        }
        // Generation runs without the owner lock. Another process may have finalized
        // this key meanwhile; its persisted outcome must win over this worker.
        if state.persistence.is_some() && state.sessions.contains_key(&work.session) {
            let observed = (|| -> Result<Option<Value>, Value> {
                let saved = state
                    .persistence
                    .as_mut()
                    .unwrap()
                    .status_bound(&work.request, &work.basis)
                    .map_err(reject)?;
                refresh_session(&mut state, &work.session, &work.request.scope)?;
                if saved.request != work.request {
                    return Err(reject("RetryMismatch"));
                }
                if !state.sessions[&work.session]
                    .engine
                    .matches_accepted_history(&work.basis)
                    .map_err(reject)?
                {
                    let t = state
                        .sessions
                        .get_mut(&work.session)
                        .unwrap()
                        .turns
                        .get_mut(&work.turn)
                        .unwrap();
                    t.phase = Phase::Stale;
                    t.error = Some("Stale".into());
                    t.receipt = None;
                    // The new source owns its own draft: no stale/cancel/fail write.
                    return Ok(Some(ok(t.view())));
                }
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
                    if reply["error"] == "Stale" {
                        if let Some(t) = state
                            .sessions
                            .get_mut(&work.session)
                            .and_then(|s| s.turns.get_mut(&work.turn))
                        {
                            t.phase = Phase::Stale;
                            t.error = Some("Stale".into());
                            t.receipt = None;
                            return ok(t.view());
                        }
                    }
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
        if !matches!(s.engine.matches_accepted_history(&work.basis), Ok(true)) {
            let t = s.turns.get_mut(&work.turn).unwrap();
            t.phase = Phase::Stale;
            t.error = Some("Stale".into());
            t.receipt = None;
            return ok(t.view());
        }
        let terminal_basis = match s.engine.accepted_history_basis() {
            Ok(basis) => basis,
            Err(error) => {
                if let Some(t) = s.turns.get_mut(&work.turn) {
                    if t.phase == Phase::Running {
                        t.phase = Phase::Queued;
                    }
                }
                return reject(error);
            }
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
                    t.basis = Some(work.basis.clone());
                }
                Err(e) => {
                    t.phase = match e {
                        Error::Cancelled => Phase::Cancelled,
                        Error::Stale => Phase::Stale,
                        _ => Phase::Failed,
                    };
                    t.error = Some(e.to_string());
                }
            }
        }
        let phase = t.phase;
        let reply = ok(t.view());
        if let Some(port) = state.persistence.as_mut() {
            let saved = match phase {
                Phase::Cancelled => Some(port.finish_bound(
                    &work.request,
                    &terminal_basis,
                    DraftDisposition::Cancelled,
                )),
                Phase::Failed => Some(port.finish_bound(
                    &work.request,
                    &terminal_basis,
                    DraftDisposition::Failed,
                )),
                Phase::Stale => {
                    Some(port.finish_bound(&work.request, &terminal_basis, DraftDisposition::Stale))
                }
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

#[cfg(test)]
mod fork_port_tests;
#[cfg(test)]
mod generation_snapshot_tests;
impl Drop for Host {
    fn drop(&mut self) {
        self.close_all();
    }
}
struct Work {
    state: Arc<Mutex<State>>,
    session: String,
    turn: String,
    owner: Arc<()>,
    engine: Engine,
    request: Request,
    mode: Mode,
    cancel: Cancellation,
    local_play: Option<LocalPlay>,
    trace: Option<AttemptHandle>,
    coverage: Option<crate::memory_coverage::CoverageRead>,
    basis: AcceptedHistoryBasis,
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
            let (prompt_label, schema_label) = local.construction.labels();
            if !local.real_model {
                return Provenance {
                    profile_label: Label::new(&local.profile.id),
                    prompt_label: Label::new(prompt_label),
                    schema_label: Label::new(schema_label),
                    ..Provenance::default()
                };
            }
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
                prompt_label: Label::new(prompt_label),
                schema_label: Label::new(schema_label),
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
    let Some(s) = state.sessions.get(id) else {
        return Err(reject("Closed"));
    };
    if s.engine.scope() != scope {
        return Err(reject("Scope"));
    }
    if let Some(port) = state.persistence.as_mut() {
        if let Err(error) = port.validate_scope(scope) {
            if error == "NotFound" {
                if let Some(session) = state.sessions.remove(id) {
                    session.trace_owner.retire();
                    for turn in session.turns.values() {
                        turn.cancel.cancel();
                    }
                }
            }
            return Err(reject(error));
        }
    }
    Ok(state.sessions.get_mut(id).unwrap())
}
fn refresh_session(state: &mut State, id: &str, scope: &Scope) -> Result<(), Value> {
    get_session(state, id, scope)?;
    let engine = state
        .persistence
        .as_mut()
        .unwrap()
        .resume(scope)
        .map_err(reject)?;
    let selected = get_session(state, id, scope)?;
    // An implicit refresh may observe appends to the selected accepted source;
    // it cannot silently select a replacement seed, prefix or lineage.
    if !engine
        .extends_accepted_history(&selected.engine)
        .map_err(reject)?
    {
        return Err(reject("Stale"));
    }
    selected.engine = engine;
    Ok(())
}
fn selected_turn_status(
    state: &mut State,
    session: &str,
    scope: &Scope,
    turn: &str,
) -> Result<SavedTurn, String> {
    refresh_session(state, session, scope)
        .map_err(|reply| reply["error"].as_str().unwrap_or("Internal").to_owned())?;
    let selected = state.sessions.get(session).ok_or("Closed")?;
    let basis = selected
        .engine
        .accepted_history_basis()
        .map_err(|error| error.to_string())?;
    let cached = selected.turns.get(turn).map(|t| t.request.clone());
    let port = state.persistence.as_mut().ok_or("Unsupported")?;
    let request = match cached {
        Some(request) => request,
        None => port.status(scope, turn)?.request,
    };
    port.status_bound(&request, &basis)
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
            work_owner: Arc::new(()),
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
        basis: None,
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
    #[test]
    fn trusted_fixture_configuration_is_honest_without_changing_real_provider_provenance() {
        let h = Host::default();
        let profile = crate::play::PlayProfile {
            id: "test-scripted".into(),
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
        };
        let provider: ProviderFactory =
            Arc::new(|| Box::new(FakeProvider::new(FakeMode::Accepted)));
        for real in [false, true] {
            if real {
                h.configure_local_provider(profile.clone(), provider.clone())
                    .unwrap();
            } else {
                h.configure_fixture_provider(profile.clone(), provider.clone())
                    .unwrap();
            }
            let status = call(&h, json!({"op":"model_status"}));
            assert_eq!(status["data"]["real_model"], real);
            assert_eq!(
                status["data"]["loaded"],
                if real { Value::Null } else { json!(false) }
            );
            assert_eq!(
                call(&h, json!({"op":"capabilities"}))["data"]["free_text"],
                true
            );
            let local = h.state.lock().unwrap().local_play.clone();
            let provenance = trace_provenance(local.as_ref(), true);
            assert_eq!(provenance.model_sha256.is_some(), real);
            assert_eq!(provenance.worker_sha256.is_some(), real);
            assert_eq!(provenance.profile_sha256.is_some(), real);
            assert_eq!(provenance.config_sha256.is_some(), real);
            assert_eq!(provenance.runtime_revision.is_some(), real);
            assert!(provenance.profile_label.is_some());
        }
        assert_eq!(
            call(&h, json!({"op":"configure_fixture_provider"}))["error"],
            "Malformed"
        );
        h.disable_local_provider();
        assert_eq!(
            call(&h, json!({"op":"capabilities"}))["data"]["free_text"],
            false
        );
        assert_eq!(
            call(&h, json!({"op":"model_status"}))["data"]["real_model"],
            false
        );
    }
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
    fn branch_invalidation_retires_target_owner_and_preserves_same_story_child() {
        let h = Host::new(true);
        let (parent, scope) = session(&h);
        let (child, target_owner, child_owner) = {
            let mut state = h.state.lock().unwrap();
            let engine = state.sessions[&parent]
                .engine
                .fork("retained-child", 0)
                .unwrap();
            let child = attach_engine(&mut state, engine)["data"]["session"]
                .as_str()
                .unwrap()
                .to_owned();
            (
                child.clone(),
                state.sessions[&parent].trace_owner.clone(),
                state.sessions[&child].trace_owner.clone(),
            )
        };
        h.invalidate_branches(&scope.story, std::slice::from_ref(&scope.branch));
        assert!(
            !target_owner.live(),
            "removed target must fence late private writes"
        );
        assert!(child_owner.live());
        let state = h.state.lock().unwrap();
        assert!(!state.sessions.contains_key(&parent));
        assert!(state.sessions.contains_key(&child));
    }
    #[test]
    fn branch_retirement_retires_only_targets_with_busy_trace_and_poisoned_state() {
        for poison in [false, true] {
            let h = Host::new(true);
            let (target, scope) = session(&h);
            let (other, _) = session(&h);
            let (selected, retained) = {
                let state = h.state.lock().unwrap();
                (
                    state.sessions[&target].trace_owner.clone(),
                    state.sessions[&other].trace_owner.clone(),
                )
            };
            if poison {
                let _ = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
                    let _state = h.state.lock().unwrap();
                    panic!("synthetic retirement cleanup poison");
                }));
            }
            let held_trace = h.trace.lock().unwrap();
            h.invalidate_branches(&scope.story, std::slice::from_ref(&scope.branch));
            assert!(!selected.live());
            assert!(retained.live());
            let state = h.state.lock().unwrap_or_else(|p| p.into_inner());
            assert_eq!(state.sessions.len(), 1);
            assert!(state.sessions.contains_key(&other));
            assert_eq!(h.state.is_poisoned(), poison);
            drop(state);
            drop(held_trace);
        }
    }
    #[test]
    fn public_scope_retirement_retires_owner_before_removing_cached_session() {
        struct AdmissionOnly(&'static str);
        impl Persistence for AdmissionOnly {
            fn validate_scope(&mut self, _: &Scope) -> Result<(), String> {
                Err(self.0.into())
            }
            fn location(&self) -> &str {
                "synthetic-admission-only"
            }
            fn list(&mut self) -> Result<Vec<WorkspaceSummary>, String> {
                unreachable!()
            }
            fn create(&mut self) -> Result<Engine, String> {
                unreachable!()
            }
            fn resume(&mut self, _: &Scope) -> Result<Engine, String> {
                unreachable!()
            }
            fn begin(&mut self, _: &Request) -> Result<SavedTurn, String> {
                unreachable!()
            }
            fn commit(&mut self, _: &Request, _: &Proposal, _: &str) -> Result<Receipt, String> {
                unreachable!()
            }
            fn cancel(&mut self, _: &Request) -> Result<SavedTurn, String> {
                unreachable!()
            }
            fn fail(&mut self, _: &Request) -> Result<SavedTurn, String> {
                unreachable!()
            }
            fn stale(&mut self, _: &Request) -> Result<SavedTurn, String> {
                unreachable!()
            }
            fn status(&mut self, _: &Scope, _: &str) -> Result<SavedTurn, String> {
                unreachable!()
            }
        }
        for error in ["NotFound", "Busy"] {
            let h = Host::new(true);
            let (id, scope) = session(&h);
            let mut state = h.state.lock().unwrap();
            let owner = state.sessions[&id].trace_owner.clone();
            state.persistence = Some(Box::new(AdmissionOnly(error)));
            assert_eq!(
                get_session(&mut state, &id, &scope).err().unwrap()["error"],
                error
            );
            assert_eq!(state.sessions.contains_key(&id), error != "NotFound");
            assert_eq!(
                owner.live(),
                error != "NotFound",
                "retired admission must fence late captures; Busy must retain the session"
            );
        }
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
    #[test]
    fn teardown_retires_private_capture_owner_with_poisoned_state_and_busy_trace() {
        let h = Host::new(true);
        let (id, _) = session(&h);
        let owner = h.state.lock().unwrap().sessions[&id].trace_owner.clone();
        let _ = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            let _state = h.state.lock().unwrap();
            panic!("synthetic state poison");
        }));
        let held_trace = h.trace.lock().unwrap();
        h.close_all();
        assert!(!owner.live());
        assert!(h
            .state
            .lock()
            .unwrap_or_else(|p| p.into_inner())
            .sessions
            .is_empty());
        // Cleanup does not clear poison or resume gameplay through untrusted state.
        assert!(h.state.is_poisoned());
        drop(held_trace);
    }
    #[test]
    fn story_invalidation_retires_only_matching_owners_even_with_busy_trace_and_poison() {
        for poison in [false, true] {
            let h = Host::new(true);
            let (a, scope) = session(&h);
            let (b, _) = session(&h);
            let (selected, retained) = {
                let state = h.state.lock().unwrap();
                (
                    state.sessions[&a].trace_owner.clone(),
                    state.sessions[&b].trace_owner.clone(),
                )
            };
            if poison {
                let _ = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
                    let _state = h.state.lock().unwrap();
                    panic!("synthetic invalidation cleanup poison");
                }));
            }
            let held_trace = h.trace.lock().unwrap();
            h.invalidate_story(&scope.story);
            assert!(!selected.live());
            assert!(retained.live());
            let state = h.state.lock().unwrap_or_else(|p| p.into_inner());
            assert_eq!(state.sessions.len(), 1);
            assert!(state.sessions.contains_key(&b));
            assert_eq!(h.state.is_poisoned(), poison);
            drop(state);
            drop(held_trace);
        }
    }
    #[test]
    fn private_capture_revoke_is_owner_scoped_busy_honest_and_fences_late_artifacts() {
        use crate::turn_capture::{Artifact, DetailStatus};
        use crate::turn_trace::TraceSink;
        struct Unreadable;
        impl Persistence for Unreadable {
            fn validate_scope(&mut self, _: &Scope) -> Result<(), String> {
                panic!("revocation must not validate an unavailable canonical Store")
            }
            fn location(&self) -> &str {
                "synthetic-unavailable"
            }
            fn list(&mut self) -> Result<Vec<WorkspaceSummary>, String> {
                Err("Database".into())
            }
            fn create(&mut self) -> Result<Engine, String> {
                Err("Database".into())
            }
            fn resume(&mut self, _: &Scope) -> Result<Engine, String> {
                panic!("revocation must not read an unavailable canonical Store")
            }
            fn begin(&mut self, _: &Request) -> Result<SavedTurn, String> {
                Err("Database".into())
            }
            fn commit(&mut self, _: &Request, _: &Proposal, _: &str) -> Result<Receipt, String> {
                Err("Database".into())
            }
            fn cancel(&mut self, _: &Request) -> Result<SavedTurn, String> {
                Err("Database".into())
            }
            fn fail(&mut self, _: &Request) -> Result<SavedTurn, String> {
                Err("Database".into())
            }
            fn stale(&mut self, _: &Request) -> Result<SavedTurn, String> {
                Err("Database".into())
            }
            fn status(&mut self, _: &Scope, _: &str) -> Result<SavedTurn, String> {
                Err("Database".into())
            }
        }
        let h = Host::new(true);
        let (a, scope_a) = session(&h);
        let (b, scope_b) = session(&h);
        let owner = h.state.lock().unwrap().sessions[&b].trace_owner.clone();
        let identity = AttemptIdentity {
            scope: scope_b.clone(),
            base_revision: 0,
            observer: "player".into(),
            turn: "private".into(),
            attempt: 1,
        };
        let handle = {
            let mut ring = h.trace.lock().unwrap();
            ring.set_enabled(true);
            ring.configure_details(&owner, &scope_b, true);
            ring.begin_for_owner(&owner, identity, Provenance::default())
                .handle
                .unwrap()
        };
        let mut sink = RingSink::new(h.trace.clone(), handle);
        sink.capture(Artifact::DirectorOutput(b"synthetic private bytes"));
        let select = Selection {
            scope: scope_b.clone(),
            base_revision: 0,
            observer: "player".into(),
            turn: Some("private".into()),
            attempt: Some(1),
        };
        let read = || {
            h.trace
                .lock()
                .unwrap()
                .read_details_for_owner(&owner, &select, &Reader::story_lab(scope_b.clone()))
                .unwrap()
        };
        assert_eq!(read().artifacts.len(), 1);
        // The native session already exists. Optional diagnostic deletion must
        // still work if its durable reader later becomes unavailable.
        h.state.lock().unwrap().persistence = Some(Box::new(Unreadable));
        assert_eq!(
            call(
                &h,
                json!({"op":"trace_capture_revoke","session":a,"scope":scope_b})
            )["error"],
            "Scope"
        );
        assert_eq!(
            call(
                &h,
                json!({"op":"trace_capture_revoke","session":a,"scope":scope_a})
            )["data"]["revoked"],
            true
        );
        assert_eq!(
            read().artifacts.len(),
            1,
            "another owner's consent survives"
        );
        let busy = h.trace.lock().unwrap();
        assert_eq!(
            call(
                &h,
                json!({"op":"trace_capture_revoke","session":b,"scope":scope_b})
            )["error"],
            "TraceUnavailable"
        );
        drop(busy);
        assert_eq!(read().artifacts.len(), 1, "busy is not reported as erased");
        assert_eq!(
            call(
                &h,
                json!({"op":"trace_capture_revoke","session":b,"scope":scope_b})
            )["data"]["revoked"],
            true
        );
        sink.capture(Artifact::DirectorOutput(b"late private callback"));
        assert_eq!(read().status, DetailStatus::Disabled);
        assert!(read().artifacts.is_empty());
        assert!(owner.live(), "revocation does not close a usable session");
        let ring = h.trace.lock().unwrap();
        assert_eq!(
            ring.read_for_owner(&owner, &select, &Reader::story_lab(scope_b))
                .unwrap()
                .attempts
                .len(),
            1
        );
    }
}
