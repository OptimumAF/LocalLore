//! Passive bounded metadata only. This module has no engine, provider, storage or I/O authority.
use crate::contracts::Scope;
use serde::Serialize;
use std::{
    collections::VecDeque,
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc, Mutex,
    },
    time::Instant,
};

pub const TRACE_VERSION: u16 = 1;
pub const MAX_ATTEMPTS: usize = 32;
pub const MAX_STAGES: usize = 24;
pub const MAX_BYTES: usize = 65_536;

#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
#[serde(transparent)]
pub struct IdentityHash(String);
impl IdentityHash {
    pub fn sha256(value: &str) -> Option<Self> {
        Self::hex(value, 64)
    }
    fn hex(value: &str, length: usize) -> Option<Self> {
        (value.len() == length && value.bytes().all(|b| b.is_ascii_hexdigit()))
            .then(|| Self(value.to_ascii_lowercase()))
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
#[serde(transparent)]
pub struct Revision(String);
impl Revision {
    pub fn new(value: &str) -> Option<Self> {
        IdentityHash::hex(value, 40).map(|hash| Self(hash.0))
    }
}

/// Trusted software/version identifiers only; never error messages or excluded-record labels.
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
#[serde(transparent)]
pub struct Label(String);
impl Label {
    pub fn new(value: &str) -> Option<Self> {
        (!value.is_empty()
            && value.len() <= 64
            && value
                .bytes()
                .all(|b| b.is_ascii_alphanumeric() || b"._-".contains(&b)))
        .then(|| Self(value.into()))
    }
}

/// Missing values serialize as null: absence is not evidence of any particular runtime.
#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize)]
pub struct Provenance {
    pub model_sha256: Option<IdentityHash>,
    pub worker_sha256: Option<IdentityHash>,
    pub profile_sha256: Option<IdentityHash>,
    pub config_sha256: Option<IdentityHash>,
    pub prompt_sha256: Option<IdentityHash>,
    pub schema_sha256: Option<IdentityHash>,
    pub runtime_revision: Option<Revision>,
    pub engine_revision: Option<Revision>,
    pub profile_label: Option<Label>,
    pub prompt_label: Option<Label>,
    pub schema_label: Option<Label>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct AttemptIdentity {
    pub scope: Scope,
    /// Immutable basis of this attempt; NOT a freshness assertion about today's Engine head.
    pub base_revision: u64,
    pub observer: String,
    pub turn: String,
    pub attempt: u32,
}
fn id(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 64
        && value
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b"-_".contains(&b))
}
impl AttemptIdentity {
    fn valid(&self) -> bool {
        id(&self.scope.story) && id(&self.scope.branch) && id(&self.observer) && id(&self.turn)
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum Stage {
    Intent,
    Retrieval,
    Context,
    Director,
    Parsing,
    Validation,
    Repair,
    AcceptedCandidate,
    Narration,
    NarrationValidation,
    AtomicCommit,
    Publication,
    MemoryMaintenance,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum Outcome {
    NotRun,
    Running,
    Accepted,
    Rejected,
    Committed,
    Failed,
    Cancelled,
    Stale,
    Truncated,
    Unknown,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ErrorCategory {
    Malformed,
    Version,
    Scope,
    Rule,
    Agency,
    Narration,
    Storage,
    Unavailable,
    Busy,
    Deadline,
    Cancelled,
    Stale,
    Internal,
    Unknown,
    RetryMismatch,
    TooLarge,
    AuthorUiRequired,
    ClarificationRequired,
    UnknownReference,
    DeadActor,
    Location,
    Inventory,
    Resource,
    Ability,
    Knowledge,
    Provider,
    CorruptHistory,
    Unsupported,
}
impl ErrorCategory {
    /// Preserve existing M03.06/core fixed categories without retaining Display/error text.
    pub fn from_engine(error: &crate::contracts::Error) -> Self {
        use crate::contracts::Error;
        match error {
            Error::Version => Self::Version,
            Error::Scope => Self::Scope,
            Error::Stale => Self::Stale,
            Error::RetryMismatch => Self::RetryMismatch,
            Error::Malformed => Self::Malformed,
            Error::TooLarge => Self::TooLarge,
            Error::Agency => Self::Agency,
            Error::AuthorUiRequired => Self::AuthorUiRequired,
            Error::ClarificationRequired => Self::ClarificationRequired,
            Error::UnknownReference => Self::UnknownReference,
            Error::DeadActor => Self::DeadActor,
            Error::Location => Self::Location,
            Error::Inventory => Self::Inventory,
            Error::Resource => Self::Resource,
            Error::Ability => Self::Ability,
            Error::Knowledge => Self::Knowledge,
            Error::Rule => Self::Rule,
            Error::Cancelled => Self::Cancelled,
            Error::Provider => Self::Provider,
            Error::Timeout => Self::Deadline,
            Error::Narration => Self::Narration,
            Error::CorruptHistory => Self::CorruptHistory,
        }
    }
}
/// The actually reached finite narration refusal, not a semantic safety verdict.
#[non_exhaustive]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum NarrationRejectionReasonV1 {
    Unclassified,
    SceneFirstPerson,
    SceneUnapprovedMovement,
}

/// Content-free metadata for one actual precommit validation call.
/// Construction and attribution remain with the matched engine trace; this
/// value grants no validation, commit, inspection or generation authority.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct NarrationValidationDiagnosticV1 {
    outcome: Outcome,
    error: Option<ErrorCategory>,
    reason: Option<NarrationRejectionReasonV1>,
}
impl NarrationValidationDiagnosticV1 {
    pub(crate) fn new(
        outcome: Outcome,
        error: Option<ErrorCategory>,
        reason: Option<NarrationRejectionReasonV1>,
    ) -> Self {
        Self {
            outcome,
            error,
            reason,
        }
    }
    pub fn version(&self) -> u16 {
        1
    }
    pub fn outcome(&self) -> Outcome {
        self.outcome
    }
    pub fn error(&self) -> Option<ErrorCategory> {
        self.error
    }
    pub fn reason(&self) -> Option<NarrationRejectionReasonV1> {
        self.reason
    }
}
/// Separate native retention result. Absence never identifies a validation cause.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum NarrationValidationReadV1 {
    Unavailable,
    Recorded(NarrationValidationDiagnosticV1),
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TokenBasis {
    Measured,
    Estimated,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
pub struct TokenCount {
    pub value: u32,
    pub basis: TokenBasis,
}
/// Counts supplied by trusted hooks from eligible context only. No exclusion counts/record IDs.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize)]
pub struct Counts {
    pub eligible_records: u32,
    pub input_tokens: Option<TokenCount>,
    pub output_tokens: Option<TokenCount>,
    pub operations: u16,
    pub repairs: u8,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct StageRecord {
    pub stage: Stage,
    pub outcome: Outcome,
    pub started_us: u64,
    pub duration_us: u64,
    pub counts: Counts,
    pub error: Option<ErrorCategory>,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct Attempt {
    pub identity: AttemptIdentity,
    pub provenance: Provenance,
    pub outcome: Outcome,
    pub elapsed_us: u64,
    pub truncated: bool,
    pub stages: Vec<StageRecord>,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum HookStatus {
    Recorded,
    Disabled,
    Dropped,
    Truncated,
    InvalidMetadata,
    Unsupported,
}
/// Opaque process-local diagnostic identity. Never serialize or pass through model output.
#[derive(Clone)]
pub struct AttemptHandle {
    owner: Arc<()>,
    sequence: u64,
}
/// Opaque native capture namespace, not part of model/wire identity or serialized diagnostics.
#[derive(Clone)]
pub struct TraceOwner(Arc<AtomicBool>);
impl Default for TraceOwner {
    fn default() -> Self {
        Self(Arc::new(AtomicBool::new(true)))
    }
}
impl TraceOwner {
    #[cfg(any(feature = "host", test))]
    pub(crate) fn retire(&self) {
        self.0.store(false, Ordering::SeqCst);
    }
    pub(crate) fn live(&self) -> bool {
        self.0.load(Ordering::SeqCst)
    }
    pub(crate) fn same(&self, other: &Self) -> bool {
        Arc::ptr_eq(&self.0, &other.0)
    }
}
fn same_owner(a: Option<&TraceOwner>, b: Option<&TraceOwner>) -> bool {
    match (a, b) {
        (None, None) => true,
        (Some(a), Some(b)) => Arc::ptr_eq(&a.0, &b.0),
        _ => false,
    }
}
/// Explicit stage interval. It carries no authority, content or caller-supplied clock values.
pub struct StageTimer {
    started: Instant,
}
pub struct StageMeasurement {
    stage: Stage,
    outcome: Outcome,
    counts: Counts,
    error: Option<ErrorCategory>,
    started: Instant,
    ended: Instant,
}
impl StageMeasurement {
    pub fn duration_us(&self) -> u64 {
        micros(self.ended.duration_since(self.started))
    }
}
impl StageTimer {
    pub fn start() -> Self {
        Self {
            started: Instant::now(),
        }
    }
    pub fn finish(
        self,
        stage: Stage,
        outcome: Outcome,
        counts: Counts,
        error: Option<ErrorCategory>,
    ) -> StageMeasurement {
        StageMeasurement {
            stage,
            outcome,
            counts,
            error,
            started: self.started,
            ended: Instant::now(),
        }
    }
}
/// Trusted metadata hook only. Production callers must isolate failure and ignore trace status.
pub trait TraceSink {
    fn matches(&mut self, scope: &Scope, base_revision: u64, observer: &str, turn: &str) -> bool;
    fn record(&mut self, measurement: StageMeasurement);
    /// Optional private data hook. Existing metadata sinks retain their default no-op.
    fn capture(&mut self, _artifact: crate::turn_capture::Artifact<'_>) {}
    /// Optional native metadata hook; existing implementations may keep the no-op.
    fn narration_validation(&mut self, _diagnostic: NarrationValidationDiagnosticV1) {}
}
/// Short, nonblocking diagnostic adapter. Busy/poisoned locks and stale handles drop metadata.
pub struct RingSink {
    ring: Arc<Mutex<TraceRing>>,
    handle: AttemptHandle,
}
impl RingSink {
    pub fn new(ring: Arc<Mutex<TraceRing>>, handle: AttemptHandle) -> Self {
        Self { ring, handle }
    }
}
impl TraceSink for RingSink {
    fn matches(&mut self, scope: &Scope, base_revision: u64, observer: &str, turn: &str) -> bool {
        let Ok(ring) = self.ring.try_lock() else {
            return false;
        };
        ring.position(&self.handle).is_some_and(|index| {
            let key = &ring.attempts[index].data.identity;
            &key.scope == scope
                && key.base_revision == base_revision
                && key.observer == observer
                && key.turn == turn
        })
    }
    fn record(&mut self, measurement: StageMeasurement) {
        if let Ok(mut ring) = self.ring.try_lock() {
            let _ = ring.record_measured(&self.handle, measurement);
        }
    }
    fn capture(&mut self, artifact: crate::turn_capture::Artifact<'_>) {
        if let Ok(mut ring) = self.ring.try_lock() {
            ring.capture_artifact(&self.handle, artifact);
        }
    }
    fn narration_validation(&mut self, diagnostic: NarrationValidationDiagnosticV1) {
        if let Ok(mut ring) = self.ring.try_lock() {
            let _ = ring.record_narration_validation(&self.handle, diagnostic);
        }
    }
}
pub struct Begin {
    pub status: HookStatus,
    pub handle: Option<AttemptHandle>,
}

#[derive(Clone, Copy, Debug)]
pub struct Config {
    attempts: usize,
    stages: usize,
    bytes: usize,
}
impl Config {
    pub fn new(attempts: usize, stages: usize, bytes: usize) -> Option<Self> {
        ((1..=MAX_ATTEMPTS).contains(&attempts)
            && (1..=MAX_STAGES).contains(&stages)
            && (1024..=MAX_BYTES).contains(&bytes))
        .then_some(Self {
            attempts,
            stages,
            bytes,
        })
    }
}
impl Default for Config {
    fn default() -> Self {
        Self {
            attempts: MAX_ATTEMPTS,
            stages: MAX_STAGES,
            bytes: MAX_BYTES,
        }
    }
}

/// Read selector, not authorization. Host must independently validate current-head/session policy.
pub struct Selection {
    pub scope: Scope,
    pub base_revision: u64,
    pub observer: String,
    pub turn: Option<String>,
    pub attempt: Option<u32>,
}
/// Trusted reader identity, deliberately not Deserialize and separate from a wire selector.
pub struct Reader {
    scope: Scope,
    observer: Option<String>,
}
impl Reader {
    pub fn scoped(scope: Scope, observer: String) -> Self {
        Self {
            scope,
            observer: Some(observer),
        }
    }
    /// Only trusted native privilege construction may call this, never renderer/model input.
    pub fn story_lab(scope: Scope) -> Self {
        Self {
            scope,
            observer: None,
        }
    }
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ReadError {
    Scope,
    Forbidden,
    InvalidSelection,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CaptureStatus {
    Disabled,
    /// Metadata only, potentially incomplete due to disabled hooks, dropped handles or eviction.
    BoundedMetadataWindow,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct Snapshot {
    pub version: u16,
    pub status: CaptureStatus,
    /// Always false. Never reconstruct unavailable trace stages from canonical history.
    pub exact_reconstruction: bool,
    pub attempts: Vec<Attempt>,
}

struct LiveAttempt {
    capture_owner: Option<TraceOwner>,
    detail_epoch: Option<u64>,
    sequence: u64,
    started: Instant,
    last: Instant,
    // Fixed payload outside the unchanged serialized Attempt and its byte budget.
    narration_validation: Option<NarrationValidationDiagnosticV1>,
    data: Attempt,
}
/// Pure, single-owner collector. Integrators may put it behind a short best-effort lock.
/// Hooks return diagnostic statuses only; none is a gameplay Result or engine authority.
pub struct TraceRing {
    config: Config,
    enabled: bool,
    owner: Arc<()>,
    sequence: u64,
    attempts: VecDeque<LiveAttempt>,
    details: crate::turn_capture::CaptureStore,
}
impl Default for TraceRing {
    fn default() -> Self {
        Self::new(Config::default())
    }
}
impl TraceRing {
    pub fn new(config: Config) -> Self {
        Self {
            config,
            enabled: false,
            owner: Arc::new(()),
            sequence: 0,
            attempts: VecDeque::new(),
            details: crate::turn_capture::CaptureStore::default(),
        }
    }
    /// Disabling deletes retained metadata and invalidates outstanding handles.
    pub fn set_enabled(&mut self, enabled: bool) {
        self.enabled = enabled;
        if !enabled {
            self.clear();
        }
    }
    pub fn clear(&mut self) {
        self.attempts.clear();
        self.details.clear();
    }
    /// Trusted native teardown; cannot clear another session's metadata.
    pub fn clear_owner(&mut self, owner: &TraceOwner) {
        self.attempts
            .retain(|attempt| !same_owner(attempt.capture_owner.as_ref(), Some(owner)));
    }
    pub fn request_full_capture(&self) -> HookStatus {
        HookStatus::Unsupported
    }
    pub fn begin(&mut self, identity: AttemptIdentity, provenance: Provenance) -> Begin {
        self.begin_owned(None, identity, provenance)
    }
    pub fn begin_for_owner(
        &mut self,
        owner: &TraceOwner,
        identity: AttemptIdentity,
        provenance: Provenance,
    ) -> Begin {
        self.begin_owned(Some(owner.clone()), identity, provenance)
    }
    fn begin_owned(
        &mut self,
        capture_owner: Option<TraceOwner>,
        identity: AttemptIdentity,
        provenance: Provenance,
    ) -> Begin {
        let none = |status| Begin {
            status,
            handle: None,
        };
        if !self.enabled {
            return none(HookStatus::Disabled);
        }
        if !identity.valid() {
            return none(HookStatus::InvalidMetadata);
        }
        // Reusing one attempt identity would make a restarted hook look like the same trace.
        if self.attempts.iter().any(|a| {
            a.data.identity == identity
                && same_owner(a.capture_owner.as_ref(), capture_owner.as_ref())
        }) {
            return none(HookStatus::Dropped);
        }
        let Some(sequence) = self.sequence.checked_add(1) else {
            return none(HookStatus::Dropped);
        };
        self.sequence = sequence;
        let now = Instant::now();
        let detail_epoch = capture_owner
            .as_ref()
            .and_then(|owner| self.details.begin(owner, sequence, &identity));
        self.attempts.push_back(LiveAttempt {
            capture_owner,
            detail_epoch,
            sequence,
            started: now,
            last: now,
            narration_validation: None,
            data: Attempt {
                identity,
                provenance,
                outcome: Outcome::Running,
                elapsed_us: 0,
                truncated: false,
                stages: vec![],
            },
        });
        self.trim();
        if !self.attempts.iter().any(|a| a.sequence == sequence) {
            return none(HookStatus::Dropped);
        }
        Begin {
            status: HookStatus::Recorded,
            handle: Some(AttemptHandle {
                owner: Arc::clone(&self.owner),
                sequence,
            }),
        }
    }
    fn position(&self, handle: &AttemptHandle) -> Option<usize> {
        Arc::ptr_eq(&self.owner, &handle.owner)
            .then(|| {
                self.attempts
                    .iter()
                    .position(|a| a.sequence == handle.sequence)
            })
            .flatten()
    }
    /// Retain only a first callback aligned with the existing measured stage.
    /// This does not append a stage, advance a clock or authenticate its origin.
    fn record_narration_validation(
        &mut self,
        handle: &AttemptHandle,
        diagnostic: NarrationValidationDiagnosticV1,
    ) -> HookStatus {
        if !self.enabled {
            return HookStatus::Disabled;
        }
        let Some(index) = self.position(handle) else {
            return HookStatus::Dropped;
        };
        let live = &mut self.attempts[index];
        if !live.capture_owner.as_ref().is_some_and(TraceOwner::live) {
            return HookStatus::Dropped;
        }
        if live.data.truncated || live.data.outcome == Outcome::Truncated {
            return HookStatus::Truncated;
        }
        if live.data.outcome != Outcome::Running || live.narration_validation.is_some() {
            return HookStatus::Dropped;
        }
        if live.data.stages.last().is_none_or(|stage| {
            stage.stage != Stage::NarrationValidation
                || stage.outcome != diagnostic.outcome()
                || stage.error != diagnostic.error()
        }) {
            return HookStatus::InvalidMetadata;
        }
        live.narration_validation = Some(diagnostic);
        HookStatus::Recorded
    }
    /// Caller must separately enforce current session/head and explicit local consent.
    pub fn configure_details(&mut self, owner: &TraceOwner, scope: &Scope, enabled: bool) {
        self.details.configure(owner, scope, enabled);
    }
    pub fn revoke_details(&mut self, owner: &TraceOwner) {
        self.details.revoke(owner);
    }
    fn capture_artifact(
        &mut self,
        handle: &AttemptHandle,
        artifact: crate::turn_capture::Artifact<'_>,
    ) {
        if !self.enabled {
            return;
        }
        if let Some(index) = self.position(handle) {
            let a = &self.attempts[index];
            self.details.record(a.detail_epoch, a.sequence, artifact);
        }
    }
    /// Full details require an explicit trusted Story Lab reader, even for player attempts.
    pub fn read_details_for_owner(
        &mut self,
        owner: &TraceOwner,
        selection: &Selection,
        reader: &Reader,
    ) -> Result<crate::turn_capture::DetailSnapshot, ReadError> {
        if reader.observer.is_some() {
            return Err(ReadError::Forbidden);
        }
        self.read_for_owner(owner, selection, reader)?;
        if selection.turn.is_none() || selection.attempt.is_none() {
            return Err(ReadError::InvalidSelection);
        }
        let sequence = self
            .attempts
            .iter()
            .find(|a| {
                same_owner(a.capture_owner.as_ref(), Some(owner))
                    && a.data.identity.scope == selection.scope
                    && a.data.identity.base_revision == selection.base_revision
                    && a.data.identity.observer == selection.observer
                    && selection.turn.as_ref() == Some(&a.data.identity.turn)
                    && selection.attempt == Some(a.data.identity.attempt)
            })
            .map(|a| a.sequence);
        Ok(self.details.read(owner, &selection.scope, sequence))
    }
    pub fn record(
        &mut self,
        handle: &AttemptHandle,
        stage: Stage,
        outcome: Outcome,
        counts: Counts,
        error: Option<ErrorCategory>,
    ) -> HookStatus {
        if !self.enabled {
            return HookStatus::Disabled;
        }
        let Some(index) = self.position(handle) else {
            return HookStatus::Dropped;
        };
        let live = &self.attempts[index];
        let now = Instant::now();
        let record = StageRecord {
            stage,
            outcome,
            started_us: micros(live.last.duration_since(live.started)),
            duration_us: micros(now.duration_since(live.last)),
            counts,
            error,
        };
        self.append(index, record, now)
    }
    pub fn record_measured(
        &mut self,
        handle: &AttemptHandle,
        measurement: StageMeasurement,
    ) -> HookStatus {
        if !self.enabled {
            return HookStatus::Disabled;
        }
        let Some(index) = self.position(handle) else {
            return HookStatus::Dropped;
        };
        let live = &self.attempts[index];
        if measurement.started < live.last || measurement.ended < measurement.started {
            return HookStatus::InvalidMetadata;
        }
        let record = StageRecord {
            stage: measurement.stage,
            outcome: measurement.outcome,
            started_us: micros(measurement.started.duration_since(live.started)),
            duration_us: micros(measurement.ended.duration_since(measurement.started)),
            counts: measurement.counts,
            error: measurement.error,
        };
        self.append(index, record, measurement.ended)
    }
    fn append(&mut self, index: usize, record: StageRecord, now: Instant) -> HookStatus {
        let live = &mut self.attempts[index];
        let sequence = live.sequence;
        if live.data.outcome != Outcome::Running {
            return HookStatus::Dropped;
        }
        if live.data.stages.len() >= self.config.stages {
            live.data.truncated = true;
            live.data.outcome = Outcome::Truncated;
            self.trim();
            return HookStatus::Truncated;
        }
        live.data.stages.push(record);
        live.last = now;
        live.data.elapsed_us = micros(now.duration_since(live.started));
        self.trim();
        if self.attempts.iter().any(|a| a.sequence == sequence) {
            HookStatus::Recorded
        } else {
            HookStatus::Dropped
        }
    }
    pub fn finish(&mut self, handle: &AttemptHandle, outcome: Outcome) -> HookStatus {
        if !self.enabled {
            return HookStatus::Disabled;
        }
        let Some(index) = self.position(handle) else {
            return HookStatus::Dropped;
        };
        let live = &mut self.attempts[index];
        if live.data.outcome == Outcome::Truncated {
            return HookStatus::Truncated;
        }
        if live.data.outcome != Outcome::Running || outcome == Outcome::Running {
            return HookStatus::Dropped;
        }
        live.data.outcome = outcome;
        live.data.truncated = outcome == Outcome::Truncated;
        live.data.elapsed_us = micros(live.started.elapsed());
        self.trim();
        if self.position(handle).is_some() {
            HookStatus::Recorded
        } else {
            HookStatus::Dropped
        }
    }
    fn snapshot(&self, attempts: Vec<Attempt>) -> Snapshot {
        Snapshot {
            version: TRACE_VERSION,
            status: if self.enabled {
                CaptureStatus::BoundedMetadataWindow
            } else {
                CaptureStatus::Disabled
            },
            exact_reconstruction: false,
            attempts,
        }
    }
    fn trim(&mut self) {
        loop {
            // Measure the WHOLE response, including metadata and JSON punctuation. Any filtered
            // read is no larger. No global drop/eviction counts cross observer boundaries.
            let snapshot = self.snapshot(self.attempts.iter().map(|a| a.data.clone()).collect());
            let fits =
                serde_json::to_vec(&snapshot).is_ok_and(|bytes| bytes.len() <= self.config.bytes);
            if self.attempts.len() <= self.config.attempts && fits {
                break;
            }
            if self.attempts.pop_front().is_none() {
                break;
            }
        }
    }
    pub fn read(&self, selection: &Selection, reader: &Reader) -> Result<Snapshot, ReadError> {
        self.read_owned(None, selection, reader)
    }
    pub fn read_for_owner(
        &self,
        owner: &TraceOwner,
        selection: &Selection,
        reader: &Reader,
    ) -> Result<Snapshot, ReadError> {
        self.read_owned(Some(owner), selection, reader)
    }
    /// Native metadata only. The caller separately enforces current session/head
    /// authority and a bounded best-effort lock; no wire capability is created.
    pub fn read_narration_validation_for_owner(
        &self,
        owner: &TraceOwner,
        selection: &Selection,
        reader: &Reader,
    ) -> Result<NarrationValidationReadV1, ReadError> {
        Self::validate_selection(selection, reader)?;
        let (Some(turn), Some(attempt)) = (&selection.turn, selection.attempt) else {
            return Err(ReadError::InvalidSelection);
        };
        if !self.enabled || !owner.live() {
            return Ok(NarrationValidationReadV1::Unavailable);
        }
        let live = self.attempts.iter().find(|live| {
            let key = &live.data.identity;
            same_owner(live.capture_owner.as_ref(), Some(owner))
                && key.scope == selection.scope
                && key.base_revision == selection.base_revision
                && key.observer == selection.observer
                && &key.turn == turn
                && key.attempt == attempt
        });
        let Some(live) = live else {
            return Ok(NarrationValidationReadV1::Unavailable);
        };
        if live.data.truncated || live.data.outcome == Outcome::Truncated {
            return Ok(NarrationValidationReadV1::Unavailable);
        }
        Ok(live.narration_validation.map_or(
            NarrationValidationReadV1::Unavailable,
            NarrationValidationReadV1::Recorded,
        ))
    }
    fn read_owned(
        &self,
        owner: Option<&TraceOwner>,
        selection: &Selection,
        reader: &Reader,
    ) -> Result<Snapshot, ReadError> {
        Self::validate_selection(selection, reader)?;
        let attempts = self
            .attempts
            .iter()
            .filter(|a| {
                let key = &a.data.identity;
                same_owner(a.capture_owner.as_ref(), owner)
                    && key.scope == selection.scope
                    && key.base_revision == selection.base_revision
                    && key.observer == selection.observer
                    && selection.turn.as_ref().is_none_or(|turn| &key.turn == turn)
                    && selection
                        .attempt
                        .is_none_or(|attempt| key.attempt == attempt)
            })
            .map(|a| a.data.clone())
            .collect();
        Ok(self.snapshot(attempts))
    }
    pub(crate) fn validate_selection(
        selection: &Selection,
        reader: &Reader,
    ) -> Result<(), ReadError> {
        if selection.scope != reader.scope {
            return Err(ReadError::Scope);
        }
        if reader
            .observer
            .as_ref()
            .is_some_and(|id| id != &selection.observer)
        {
            return Err(ReadError::Forbidden);
        }
        if !id(&selection.scope.story)
            || !id(&selection.scope.branch)
            || !id(&selection.observer)
            || selection.turn.as_ref().is_some_and(|turn| !id(turn))
        {
            return Err(ReadError::InvalidSelection);
        }
        Ok(())
    }
}
fn micros(duration: std::time::Duration) -> u64 {
    duration.as_micros().min(u128::from(u64::MAX)) as u64
}

#[cfg(test)]
mod narration_diagnostic_retention_review_tests;
