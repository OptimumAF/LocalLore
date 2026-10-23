//! Passive bounded metadata only. This module has no engine, provider, storage or I/O authority.
use crate::contracts::Scope;
use serde::Serialize;
use std::{collections::VecDeque, sync::Arc, time::Instant};

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
    sequence: u64,
    started: Instant,
    last: Instant,
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
    }
    pub fn request_full_capture(&self) -> HookStatus {
        HookStatus::Unsupported
    }
    pub fn begin(&mut self, identity: AttemptIdentity, provenance: Provenance) -> Begin {
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
        if self.attempts.iter().any(|a| a.data.identity == identity) {
            return none(HookStatus::Dropped);
        }
        let Some(sequence) = self.sequence.checked_add(1) else {
            return none(HookStatus::Dropped);
        };
        self.sequence = sequence;
        let now = Instant::now();
        self.attempts.push_back(LiveAttempt {
            sequence,
            started: now,
            last: now,
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
        let live = &mut self.attempts[index];
        if live.data.outcome != Outcome::Running {
            return HookStatus::Dropped;
        }
        if live.data.stages.len() >= self.config.stages {
            live.data.truncated = true;
            live.data.outcome = Outcome::Truncated;
            self.trim();
            return HookStatus::Truncated;
        }
        let now = Instant::now();
        live.data.stages.push(StageRecord {
            stage,
            outcome,
            started_us: micros(live.last.duration_since(live.started)),
            duration_us: micros(now.duration_since(live.last)),
            counts,
            error,
        });
        live.last = now;
        live.data.elapsed_us = micros(now.duration_since(live.started));
        self.trim();
        if self.position(handle).is_some() {
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
        let attempts = self
            .attempts
            .iter()
            .filter(|a| {
                let key = &a.data.identity;
                key.scope == selection.scope
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
}
fn micros(duration: std::time::Duration) -> u64 {
    duration.as_micros().min(u128::from(u64::MAX)) as u64
}
