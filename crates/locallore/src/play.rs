//! Versioned shared local play. Generated text is display evidence, never canonical truth.
use crate::{
    contracts::*,
    engine::{staged_play::NarratorEvidenceV22, Engine},
    inference::{generate, Budget, Cancellation, GenerationRequest, InferenceProvider, Input},
    turn_trace::{
        Counts, ErrorCategory, NarrationRejectionReasonV1, NarrationValidationDiagnosticV1,
        Outcome, Stage, StageMeasurement, StageTimer, TokenBasis, TokenCount, TraceSink,
    },
};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    time::{Duration, Instant},
};
pub(crate) mod director_budget;
mod director_construction;
mod literal_director;
pub mod scene_narration;
mod story_presentation;
pub use director_budget::{
    director_forwarded_budget_v25, director_repair_matches_v25, DirectorPassV25,
    ForwardedEstimateV1,
};
use director_construction::{DirectorInput, PreparedDirector};
pub use literal_director::{
    render_player_literal_director_v1_cancelled, LiteralDirectorUnitProvenanceV1,
    RenderedLiteralDirectorV1,
};
pub use story_presentation::{
    PlayStoryPresentationRecordV1, LITERAL_PRESENTATION_PROMPT_VERSION_V1,
    PRESENTATION_NARRATION_POLICY, PRESENTATION_PROMPT_VERSION,
};

struct Trace<'a> {
    sink: Option<&'a mut dyn TraceSink>,
    overhead: Duration,
}
/// Crate-private propagation of the original error and its reached rule, if any.
/// No text is re-examined and no validation or cancellation check is repeated.
pub(crate) struct NarrationValidationFailureV1 {
    error: Error,
    reason: Option<NarrationRejectionReasonV1>,
}
impl From<Error> for NarrationValidationFailureV1 {
    fn from(error: Error) -> Self {
        Self {
            reason: (error == Error::Narration).then_some(NarrationRejectionReasonV1::Unclassified),
            error,
        }
    }
}
impl NarrationValidationFailureV1 {
    fn scene(reason: NarrationRejectionReasonV1) -> Self {
        Self {
            error: Error::Narration,
            reason: Some(reason),
        }
    }
    pub(crate) fn into_engine_error(self) -> Error {
        self.error
    }
}
#[derive(Clone, Copy)]
struct GameplayClock {
    started: Instant,
    overhead: Duration,
}
impl Trace<'_> {
    fn narration_validation(&mut self, diagnostic: NarrationValidationDiagnosticV1) {
        if let Some(sink) = self.sink.as_deref_mut() {
            let before = Instant::now();
            let failed = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
                sink.narration_validation(diagnostic)
            }))
            .is_err();
            self.overhead = self.overhead.saturating_add(before.elapsed());
            if failed {
                self.sink = None;
            }
        }
    }
    fn capture(&mut self, artifact: crate::turn_capture::Artifact<'_>) {
        if let Some(sink) = self.sink.as_deref_mut() {
            let before = Instant::now();
            let failed =
                std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| sink.capture(artifact)))
                    .is_err();
            self.overhead = self.overhead.saturating_add(before.elapsed());
            if failed {
                self.sink = None;
            }
        }
    }
    fn generate(
        &mut self,
        stage: Stage,
        provider: &mut (impl InferenceProvider + ?Sized),
        cancel: &Cancellation,
        build: impl FnOnce() -> Result<GenerationRequest, Error>,
    ) -> Result<(Vec<u8>, u64), Error> {
        let timer = StageTimer::start();
        let result = (|| {
            if cancel.is_cancelled() {
                return Err(Error::Cancelled);
            }
            let request = build()?;
            self.capture(crate::turn_capture::Artifact::Request(&request));
            let started = Instant::now();
            let bytes = generate(provider, &request, cancel)?;
            Ok((bytes, started.elapsed().as_millis() as u64))
        })();
        let (outcome, error) = match &result {
            Ok(_) => (Outcome::Accepted, None),
            Err(error) => (
                match error {
                    Error::Cancelled => Outcome::Cancelled,
                    Error::Stale => Outcome::Stale,
                    _ => Outcome::Failed,
                },
                Some(ErrorCategory::from_engine(error)),
            ),
        };
        self.emit(timer.finish(stage, outcome, Counts::default(), error));
        result
    }
    fn clock(&self) -> GameplayClock {
        GameplayClock {
            started: Instant::now(),
            overhead: self.overhead,
        }
    }
    fn elapsed(&self, clock: GameplayClock) -> Duration {
        clock
            .started
            .elapsed()
            .saturating_sub(self.overhead.saturating_sub(clock.overhead))
    }
    fn emit(&mut self, measurement: StageMeasurement) {
        if let Some(sink) = self.sink.as_deref_mut() {
            let before = Instant::now();
            let failed =
                std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| sink.record(measurement)))
                    .is_err();
            self.overhead = self.overhead.saturating_add(before.elapsed());
            if failed {
                self.sink = None;
            }
        }
    }
    fn run<T>(
        &mut self,
        stage: Stage,
        failed: Outcome,
        operation: impl FnOnce() -> Result<T, Error>,
    ) -> Result<T, Error> {
        self.counted(stage, failed, operation, |_| Counts::default())
    }
    fn counted<T>(
        &mut self,
        stage: Stage,
        failed: Outcome,
        operation: impl FnOnce() -> Result<T, Error>,
        counts: impl FnOnce(&T) -> Counts,
    ) -> Result<T, Error> {
        let timer = StageTimer::start();
        let result = operation();
        let (outcome, category, counts) = match &result {
            Ok(value) => (Outcome::Accepted, None, counts(value)),
            Err(error) => (
                match error {
                    Error::Cancelled => Outcome::Cancelled,
                    Error::Stale => Outcome::Stale,
                    _ => failed,
                },
                Some(ErrorCategory::from_engine(error)),
                Counts::default(),
            ),
        };
        self.emit(timer.finish(stage, outcome, counts, category));
        result
    }
    fn not_run(&mut self, stage: Stage) {
        self.emit(StageTimer::start().finish(
            stage,
            Outcome::NotRun,
            Counts::default(),
            Some(ErrorCategory::Unsupported),
        ));
    }
}
fn remaining(clock: GameplayClock, overhead: Duration, deadline_ms: u64) -> Result<u64, Error> {
    let elapsed = clock
        .started
        .elapsed()
        .saturating_sub(overhead.saturating_sub(clock.overhead));
    deadline_ms
        .checked_sub(elapsed.as_millis() as u64)
        .filter(|v| *v > 0)
        .ok_or(Error::Timeout)
}

pub const PLAY_VERSION: u16 = 2;
pub const NARRATION_POLICY: &str = "grounded-prose-v2.5-whole-evidence-words-v1";
const RECORDED_STAGED_NARRATION_POLICY: &str = "grounded-prose-v2.2";
pub const PROMPT_VERSION: &str = "locallore-play-v2.5";
/// Immutable construction mapping: Domain1/player, source/render/schema/packing
/// v1, no compiler/coverage context, current versioned narration policy. A future
/// construction change requires a new version, never repoint this identifier.
pub const LITERAL_PLAY_PROMPT_VERSION_V1: &str = "locallore-play-v2.6-literal-director-v1";
const LITERAL_NARRATION_POLICY_V1: &str = NARRATION_POLICY;
const LITERAL_DIRECTOR_SCHEMA_ID_V1: &str = "locallore-director-literal-v1";
pub const RECORDED_PROMPT_VERSION: &str = "locallore-play-v2.1";
const RECORDED_PROMPT_V2_2: &str = "locallore-play-v2.2";
const RECORDED_PROMPT_V2_3: &str = "locallore-play-v2.3";
const RECORDED_PROMPT_V2_4: &str = "locallore-play-v2.4";
const RECORDED_NARRATION_POLICY: &str = "grounded-prose-v2.1";
const MAX_ROLE_INPUT_BYTES: usize = 24_576;
pub use crate::context_compiler::ContextPolicy as PlayContextPolicy;

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PlayProfile {
    pub id: String,
    pub model_sha256: String,
    pub runtime_revision: String,
    pub template_sha256: String,
    pub worker_sha256: String,
    pub profile_manifest_sha256: String,
    pub context_tokens: u32,
    pub director_tokens: u16,
    pub narrator_tokens: u16,
    pub deadline_ms: u64,
    pub repair_limit: u8,
}
impl PlayProfile {
    pub fn validate(&self) -> Result<(), Error> {
        fn hex(s: &str, n: usize) -> bool {
            s.len() == n && s.bytes().all(|b| b.is_ascii_hexdigit())
        }
        // Runtime profile names include model versions such as `qwen3-0.6b`.
        // This is a provenance label, not a story/entity ID or filesystem path.
        let valid_profile_id = !self.id.is_empty()
            && self.id.len() <= 64
            && self
                .id
                .bytes()
                .all(|b| b.is_ascii_alphanumeric() || matches!(b, b'-' | b'_' | b'.'));
        if !valid_profile_id
            || !hex(&self.model_sha256, 64)
            || !hex(&self.runtime_revision, 40)
            || !hex(&self.template_sha256, 64)
            || !hex(&self.worker_sha256, 64)
            || !hex(&self.profile_manifest_sha256, 64)
            || !(512..=4096).contains(&self.context_tokens)
            || self.director_tokens == 0
            || self.director_tokens > 350
            || self.narrator_tokens == 0
            || self.narrator_tokens > 350
            || self.deadline_ms == 0
            || self.deadline_ms > 120_000
            || self.repair_limit > 1
        {
            return Err(Error::Rule);
        }
        Ok(())
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct NarrationDocument {
    pub text: String,
    pub event_ids: Vec<u64>,
    pub speaker: String,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct StageTiming {
    pub stage: String,
    pub elapsed_ms: u64,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PlayRecord {
    pub version: u16,
    pub policy: String,
    pub prompt_version: String,
    pub profile: PlayProfile,
    pub repairs: u8,
    pub fallback: bool,
    pub narration: NarrationDocument,
    pub stages: Vec<StageTiming>,
    /// Count-only construction provenance, never a cache proof or knowledge grant.
    /// Absent from exact historical2.1–2.3 bytes; version1 for recorded2.4,
    /// version2 for current2.5. It never supplies proof or actor knowledge.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub context: Option<PlayContextRecord>,
    /// Requested construction, independent of actual coverage/fallback provenance.
    /// Omitted for exact historical2.1–2.4 encodings; mandatory for current2.5.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub context_policy: Option<PlayContextPolicy>,
    /// Exact seed presentation binding for the explicit presentation versions only.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub story_presentation: Option<PlayStoryPresentationRecordV1>,
    /// Recomputed frame provenance for the explicit scene recipes only.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub scene: Option<scene_narration::SceneNarrationRecordV1>,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PlayCoverageMode {
    Raw,
    Verified,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PlayMemoryFallback {
    Missing,
    Budget,
    Malformed,
    Unsupported,
    Binding,
    Gap,
    Overlap,
    OpenTailBeforeEnd,
    UnprovableClosure,
    SourceMismatch,
}
impl From<crate::memory_coverage::FallbackReason> for PlayMemoryFallback {
    fn from(reason: crate::memory_coverage::FallbackReason) -> Self {
        use crate::memory_coverage::FallbackReason as F;
        match reason {
            F::Missing => Self::Missing,
            F::Budget => Self::Budget,
            F::Malformed => Self::Malformed,
            F::Unsupported => Self::Unsupported,
            F::Binding => Self::Binding,
            F::Gap => Self::Gap,
            F::Overlap => Self::Overlap,
            F::OpenTailBeforeEnd => Self::OpenTailBeforeEnd,
            F::UnprovableClosure => Self::UnprovableClosure,
            F::SourceMismatch => Self::SourceMismatch,
        }
    }
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PlayCoverageRecord {
    /// Verified means the compiler accepted a proof, not that every packet was used.
    pub mode: PlayCoverageMode,
    pub set_fallback_reason: Option<PlayMemoryFallback>,
    pub packets_used: usize,
    pub packets_fell_back: usize,
    pub timespan_fallback_packets: usize,
    pub mandatory_fallback_packets: usize,
    pub covered_through: u64,
    pub raw_delta_after: u64,
    pub cached_event_candidates: usize,
    pub raw_event_candidates: usize,
}
/// Bounded receipt metadata describing the actual compiler call. Persisted counts
/// cannot authenticate its source cache or demonstrate saved work/model quality.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PlayContextRecord {
    pub version: u16,
    pub compiler_version: u16,
    pub scope: Scope,
    pub head: u64,
    pub observer: String,
    /// Native source rejection, distinct from the compiler's own raw Missing.
    /// Absent means the input made no source-fallback claim, not a cache hit.
    pub source_fallback_reason: Option<PlayMemoryFallback>,
    pub coverage: PlayCoverageRecord,
}
impl PlayContextRecord {
    fn from_compilation(
        value: &crate::context_compiler::MemoryCompilation,
        source_fallback_reason: Option<PlayMemoryFallback>,
    ) -> Self {
        use crate::context_compiler::{CoverageMode as M, MemoryFallbackReason as F};
        let c = &value.coverage;
        Self {
            version: 1,
            compiler_version: value.package.version,
            scope: value.package.scope.clone(),
            head: value.package.head,
            observer: value.package.observer.clone(),
            source_fallback_reason,
            coverage: PlayCoverageRecord {
                mode: match c.mode {
                    M::Raw => PlayCoverageMode::Raw,
                    M::Verified => PlayCoverageMode::Verified,
                },
                set_fallback_reason: c.set_fallback_reason.map(|reason| match reason {
                    F::Missing => PlayMemoryFallback::Missing,
                    F::Budget => PlayMemoryFallback::Budget,
                    F::Malformed => PlayMemoryFallback::Malformed,
                    F::Unsupported => PlayMemoryFallback::Unsupported,
                    F::Binding => PlayMemoryFallback::Binding,
                    F::Gap => PlayMemoryFallback::Gap,
                    F::Overlap => PlayMemoryFallback::Overlap,
                    F::OpenTailBeforeEnd => PlayMemoryFallback::OpenTailBeforeEnd,
                    F::UnprovableClosure => PlayMemoryFallback::UnprovableClosure,
                    F::SourceMismatch => PlayMemoryFallback::SourceMismatch,
                }),
                packets_used: c.packets_used,
                packets_fell_back: c.packets_fell_back,
                timespan_fallback_packets: c.timespan_fallback_packets,
                mandatory_fallback_packets: c.mandatory_fallback_packets,
                covered_through: c.covered_through,
                raw_delta_after: c.raw_delta_after,
                cached_event_candidates: c.cached_event_candidates,
                raw_event_candidates: c.raw_event_candidates,
            },
        }
    }
    fn valid(&self, engine: &Engine, approved: &Receipt) -> bool {
        self.valid_version(
            engine,
            approved,
            1,
            crate::context_compiler::COMPILER_VERSION,
        )
    }
    fn from_policy_compilation(
        value: &crate::context_compiler::PolicyCompilation,
        source_fallback_reason: Option<PlayMemoryFallback>,
    ) -> Self {
        let mut record = Self::from_compilation(&value.compilation, source_fallback_reason);
        record.version = 2;
        record
    }
    fn valid_v2(&self, engine: &Engine, approved: &Receipt) -> bool {
        self.valid_version(
            engine,
            approved,
            2,
            crate::context_compiler::POLICY_COMPILER_VERSION,
        )
    }
    fn valid_version(
        &self,
        engine: &Engine,
        approved: &Receipt,
        version: u16,
        compiler_version: u16,
    ) -> bool {
        let c = &self.coverage;
        // Finite encoding limits and binding checks, not authentication of counts.
        let max_events = MAX_HISTORY_RECEIPTS * MAX_COMMANDS;
        let packets = c.packets_used.checked_add(c.packets_fell_back);
        let fallbacks = c
            .timespan_fallback_packets
            .checked_add(c.mandatory_fallback_packets);
        let events = c
            .cached_event_candidates
            .checked_add(c.raw_event_candidates);
        self.version == version
            && self.compiler_version == compiler_version
            && self.scope == approved.request().scope
            && self.scope == *engine.scope()
            && self.head == approved.request().expected_revision
            && self.head == engine.revision()
            && self.observer == engine.seed().player
            && (self.source_fallback_reason.is_none()
                || (c.mode == PlayCoverageMode::Raw
                    && (version == 2
                        || c.set_fallback_reason == Some(PlayMemoryFallback::Missing))))
            && packets.is_some_and(|n| n <= crate::memory_coverage::MAX_PACKETS)
            && fallbacks.is_some_and(|n| n <= c.packets_fell_back)
            && events.is_some_and(|n| n <= max_events)
            && c.covered_through <= self.head
            && c.raw_delta_after == c.covered_through
            && match c.mode {
                PlayCoverageMode::Raw => {
                    c.set_fallback_reason.is_some()
                        && c.packets_used == 0
                        && c.cached_event_candidates == 0
                        && c.covered_through == 0
                        && c.raw_delta_after == 0
                        && c.timespan_fallback_packets == 0
                        && c.mandatory_fallback_packets == 0
                }
                PlayCoverageMode::Verified => c.set_fallback_reason.is_none(),
            }
    }
}

pub(crate) fn validate_interpretation(
    engine: &Engine,
    request: &Request,
    proposal: &Proposal,
) -> Result<(), Error> {
    let Intent::FreeText { kind, text } = &request.intent else {
        return Err(Error::Agency);
    };
    if proposal.commands.is_empty() || proposal.commands.len() > MAX_COMMANDS {
        return Err(Error::TooLarge);
    }
    match kind {
        PlayInputKind::Dialogue => match proposal.commands.as_slice() {
            [Command::Say {
                text: spoken,
                audience,
            }] if spoken == text && !audience.is_empty() && audience.len() <= 4 => Ok(()),
            _ => Err(Error::Agency),
        },
        PlayInputKind::Action => {
            // Speech is an explicit mode, not permission to invent words for the player.
            if proposal.commands.iter().any(|c| {
                matches!(
                    c,
                    Command::Say { .. } | Command::Promise { .. } | Command::CompletePromise { .. }
                )
            }) {
                Err(Error::Agency)
            } else {
                crate::intent_guard::validate_action(engine, request, proposal)
            }
        }
    }
}

/// Mechanical references and conservative prose checks are distinct. This is not a semantic
/// oracle: unsupported prose falls back safely; measured semantic errors remain a quality gate.
pub(crate) fn validate_record(
    engine: &Engine,
    approved: &Receipt,
    record: &PlayRecord,
    recorded_history: bool,
) -> Result<(), Error> {
    if record.scene.is_some() {
        return Err(Error::Narration);
    }
    story_presentation::validate_legacy(engine, record)?;
    record.profile.validate()?;
    if record.version != PLAY_VERSION
        || record.policy != RECORDED_NARRATION_POLICY
        || !recorded_history
        || !matches!(
            record.prompt_version.as_str(),
            RECORDED_PROMPT_VERSION
                | RECORDED_PROMPT_V2_2
                | RECORDED_PROMPT_V2_3
                | RECORDED_PROMPT_V2_4
        )
        || record.context_policy.is_some()
        || if record.prompt_version == RECORDED_PROMPT_V2_4 {
            !record
                .context
                .as_ref()
                .is_some_and(|context| context.valid(engine, approved))
        } else {
            record.context.is_some()
        }
    {
        return Err(Error::Narration);
    }
    validate_record_contents(engine, approved, record, None, ProseMode::Legacy)
}

#[derive(Clone, Copy, PartialEq, Eq)]
pub(super) enum ProseMode {
    Legacy,
    WholeEvidenceWordsV1,
}

pub(super) fn narration_policy_mode(
    record: &PlayRecord,
    recorded_history: bool,
    current: &str,
    legacy: &str,
) -> Result<ProseMode, Error> {
    if record.policy == current {
        Ok(ProseMode::WholeEvidenceWordsV1)
    } else if recorded_history && record.policy == legacy {
        Ok(ProseMode::Legacy)
    } else {
        Err(Error::Narration)
    }
}

/// Core calls this only after regenerating the actual staged candidate/evidence.
/// Persisted metadata is a closed provenance claim, never a supplied proof.
pub(crate) fn validate_record_v25(
    engine: &Engine,
    approved: &Receipt,
    evidence: &NarratorEvidenceV22,
    record: &PlayRecord,
    recorded_history: bool,
) -> Result<(), Error> {
    validate_record_v25_inner(engine, approved, evidence, record, false, recorded_history)
}

pub(crate) fn validate_record_presentation_v1(
    engine: &Engine,
    approved: &Receipt,
    evidence: &NarratorEvidenceV22,
    record: &PlayRecord,
    recorded_history: bool,
) -> Result<(), Error> {
    validate_record_v25_inner(engine, approved, evidence, record, true, recorded_history)
}

fn validate_record_v25_inner(
    engine: &Engine,
    approved: &Receipt,
    evidence: &NarratorEvidenceV22,
    record: &PlayRecord,
    presentation: bool,
    recorded_history: bool,
) -> Result<(), Error> {
    if record.scene.is_some() {
        return Err(Error::Narration);
    }
    story_presentation::validate_binding(engine, record, presentation)?;
    record.profile.validate()?;
    if record.version != PLAY_VERSION
        || record.prompt_version
            != if presentation {
                PRESENTATION_PROMPT_VERSION
            } else {
                PROMPT_VERSION
            }
    {
        return Err(Error::Narration);
    }
    let mode = narration_policy_mode(
        record,
        recorded_history,
        if presentation {
            PRESENTATION_NARRATION_POLICY
        } else {
            NARRATION_POLICY
        },
        if presentation {
            story_presentation::RECORDED_PRESENTATION_NARRATION_POLICY
        } else {
            RECORDED_STAGED_NARRATION_POLICY
        },
    )?;
    validate_memory_context_record(engine, approved, record)?;
    validate_staged_record_contents(engine, approved, evidence, record, mode)
}

fn validate_memory_context_record(
    engine: &Engine,
    approved: &Receipt,
    record: &PlayRecord,
) -> Result<(), Error> {
    if record.context_policy.is_none()
        || !record
            .context
            .as_ref()
            .is_some_and(|context| context.valid_v2(engine, approved))
    {
        return Err(Error::Narration);
    }
    // These current compiler branches refuse before inspecting any proof. A
    // finite generic coverage tuple must not claim work they cannot perform.
    if engine.domain_version() != 1
        || record.context_policy == Some(PlayContextPolicy::StateRecentTranscriptV1)
    {
        let c = &record.context.as_ref().ok_or(Error::Narration)?.coverage;
        if c.mode != PlayCoverageMode::Raw
            || c.set_fallback_reason != Some(PlayMemoryFallback::Unsupported)
            || c.packets_used != 0
            || c.packets_fell_back != 0
            || c.timespan_fallback_packets != 0
            || c.mandatory_fallback_packets != 0
            || c.covered_through != 0
            || c.raw_delta_after != 0
            || c.cached_event_candidates != 0
        {
            return Err(Error::Narration);
        }
    }
    Ok(())
}

pub(crate) fn validate_record_literal_v1(
    engine: &Engine,
    approved: &Receipt,
    evidence: &NarratorEvidenceV22,
    record: &PlayRecord,
    recorded_history: bool,
    cancel: &dyn Fn() -> bool,
) -> Result<(), Error> {
    validate_record_literal_inner(
        engine,
        approved,
        evidence,
        record,
        cancel,
        false,
        recorded_history,
    )
}

pub(crate) fn validate_record_literal_presentation_v1(
    engine: &Engine,
    approved: &Receipt,
    evidence: &NarratorEvidenceV22,
    record: &PlayRecord,
    recorded_history: bool,
    cancel: &dyn Fn() -> bool,
) -> Result<(), Error> {
    validate_record_literal_inner(
        engine,
        approved,
        evidence,
        record,
        cancel,
        true,
        recorded_history,
    )
}

fn validate_record_literal_inner(
    engine: &Engine,
    approved: &Receipt,
    evidence: &NarratorEvidenceV22,
    record: &PlayRecord,
    cancel: &dyn Fn() -> bool,
    presentation: bool,
    recorded_history: bool,
) -> Result<(), Error> {
    if record.scene.is_some() {
        return Err(Error::Narration);
    }
    if engine.domain_version() != 1 {
        return Err(Error::Version);
    }
    story_presentation::validate_binding(engine, record, presentation)?;
    record.profile.validate()?;
    if record.version != PLAY_VERSION
        || record.prompt_version
            != if presentation {
                LITERAL_PRESENTATION_PROMPT_VERSION_V1
            } else {
                LITERAL_PLAY_PROMPT_VERSION_V1
            }
    {
        return Err(Error::Narration);
    }
    let mode = narration_policy_mode(
        record,
        recorded_history,
        if presentation {
            PRESENTATION_NARRATION_POLICY
        } else {
            LITERAL_NARRATION_POLICY_V1
        },
        if presentation {
            story_presentation::RECORDED_PRESENTATION_NARRATION_POLICY
        } else {
            RECORDED_STAGED_NARRATION_POLICY
        },
    )?;
    validate_literal_context_record(engine, approved, record, cancel)?;
    validate_staged_record_contents(engine, approved, evidence, record, mode)
}

fn validate_literal_context_record(
    engine: &Engine,
    approved: &Receipt,
    record: &PlayRecord,
    cancel: &dyn Fn() -> bool,
) -> Result<(), Error> {
    if engine.domain_version() != 1 {
        return Err(Error::Version);
    }
    if record.context.is_some() || record.context_policy.is_some() {
        return Err(Error::Narration);
    }
    // Persisted metadata is not proof that a provider ran. Recompute the actual
    // source/render/fit from the immutable before-history rather than admitting
    // caller-supplied context, coverage or packing counts.
    let source = crate::context_compiler::player_literal_transcript_v1_cancelled(
        engine,
        engine.scope(),
        engine.revision(),
        &engine.seed().player,
        cancel,
    )
    .map_err(director_construction::compile_error)?;
    render_player_literal_director_v1_cancelled(
        engine,
        approved.request(),
        &source,
        &record.profile,
        DirectorPassV25::Initial,
        cancel,
    )?;
    if record.repairs > 0 {
        render_player_literal_director_v1_cancelled(
            engine,
            approved.request(),
            &source,
            &record.profile,
            DirectorPassV25::Repair,
            cancel,
        )?;
    }
    Ok(())
}

fn validate_staged_record_contents(
    engine: &Engine,
    approved: &Receipt,
    evidence: &NarratorEvidenceV22,
    record: &PlayRecord,
    mode: ProseMode,
) -> Result<(), Error> {
    // Evidence is opaque Core output. Even trusted internal callers must keep
    // its event catalogue/observation attribution bound to this approved turn.
    if evidence
        .events()
        .iter()
        .map(|e| e.event_id())
        .collect::<Vec<_>>()
        != approved
            .events()
            .iter()
            .map(|e| e.sequence())
            .collect::<Vec<_>>()
        || evidence.mechanical_summary() != approved.narration()
        || evidence.observations().iter().any(|observation| {
            observation.actor() != engine.seed().player.as_str()
                || !approved.events().iter().any(|event| {
                    event.sequence() == observation.event_id()
                        && matches!(event.outcome(), Effect::Discovered{actor,fact}
                        if actor.as_str() == observation.actor() && fact.as_str() == observation.fact())
                })
        })
    {
        return Err(Error::Narration);
    }
    crate::engine::check_json_budget(evidence, MAX_RECEIPT_BYTES)?;
    validate_record_contents(engine, approved, record, Some(evidence), mode)
}

fn validate_record_contents(
    engine: &Engine,
    approved: &Receipt,
    record: &PlayRecord,
    evidence: Option<&NarratorEvidenceV22>,
    mode: ProseMode,
) -> Result<(), Error> {
    if record.repairs > record.profile.repair_limit
        || record.stages.len() > 8
        || record.stages.iter().any(|s| {
            !matches!(
                s.stage.as_str(),
                "director"
                    | "repair"
                    | "validation"
                    | "narrator"
                    | "narration_validation"
                    | "total"
            ) || s.elapsed_ms > 120_000
        })
        || record.narration.event_ids
            != approved
                .events()
                .iter()
                .map(|e| e.sequence())
                .collect::<Vec<_>>()
        || record.narration.speaker != "narrator"
    {
        return Err(Error::Narration);
    }
    if record.fallback {
        if record.narration.text != approved.narration() {
            return Err(Error::Narration);
        }
    } else {
        validate_prose(engine, approved, &record.narration.text, evidence, mode)?;
    }
    engine.validate_story_narration(&record.narration.text)
}

// A conservative current-policy check for the observed post-gift ownership
// contradiction. It is bounded phrase matching, not a semantic language oracle.
// Historical policies do not call it; literal player dialogue is not narration.
fn narration_reclaims_transferred_item(approved: &Receipt, player: &str, lower: &str) -> bool {
    let possession = |word: &str| {
        matches!(
            word,
            "keep"
                | "kept"
                | "carry"
                | "carried"
                | "retain"
                | "retained"
                | "hold"
                | "held"
                | "pocket"
                | "pocketed"
                | "stash"
                | "stashed"
        )
    };
    approved.events().iter().any(|event| {
        let Effect::Given { from, item, .. } = event.outcome() else {
            return false;
        };
        if from != player {
            return false;
        }
        let item_lower = item.to_lowercase();
        let item_words: Vec<_> = item_lower
            .split(|c: char| !c.is_alphanumeric())
            .filter(|w| !w.is_empty())
            .collect();
        lower.split(['.', '!', '?', ';', '\n']).any(|clause| {
            let words: Vec<_> = clause
                .split(|c: char| !c.is_alphanumeric())
                .filter(|w| !w.is_empty())
                .collect();
            if item_words.is_empty() || !words.windows(item_words.len()).any(|w| w == item_words) {
                return false;
            }
            let directly_kept = words
                .windows(2)
                .any(|w| matches!(w[0], "i" | "you") && possession(w[1]))
                || words.windows(3).any(|w| {
                    matches!(w[0], "i" | "you")
                        && matches!(w[1], "still" | "now" | "then")
                        && (possession(w[2]) || w[2] == "have")
                });
            let with_player = words
                .windows(2)
                .any(|w| w[0] == "with" && matches!(w[1], "me" | "you"));
            directly_kept
                || (with_player
                    && words.iter().any(|w| {
                        matches!(
                            *w,
                            "take"
                                | "took"
                                | "bring"
                                | "brought"
                                | "remain"
                                | "remains"
                                | "remained"
                                | "stay"
                                | "stays"
                                | "stayed"
                        )
                    }))
        })
    })
}

/// Complete visible labels only. Ranges are in the lowercased text's byte
/// coordinates; they are never used to slice the original Unicode prose.
fn narrator_visible_label_spans(
    lower: &str,
    labels: &BTreeSet<String>,
    mode: ProseMode,
) -> Vec<(usize, usize)> {
    let boundary = move |c: char| {
        if mode == ProseMode::WholeEvidenceWordsV1 {
            // Match the original-word rule used by evidence checks. A combining
            // mark or non-ASCII continuation must not create a partial label
            // span that masks a hidden display name, even in lowercase prose.
            prose_word_boundary(c) || matches!(c, '‘' | '“' | '”')
        } else {
            !c.is_alphanumeric() && !matches!(c, '_' | '-' | '\'' | '’')
        }
    };
    labels
        .iter()
        .filter(|label| !label.is_empty())
        .flat_map(|label| {
            lower.match_indices(label).filter_map(move |(start, _)| {
                let end = start + label.len();
                let mut preceding = lower[..start].chars().rev();
                let left = match preceding.next() {
                    Some('\'' | '’') => preceding.next().is_none_or(boundary),
                    character => character.is_none_or(boundary),
                };
                let suffix = &lower[end..];
                let right = if let Some(tail) = suffix
                    .strip_prefix('\'')
                    .or_else(|| suffix.strip_prefix('’'))
                {
                    // Accept a closing quote or complete possessive, never a
                    // fragment of an apostrophe-extended unknown name.
                    tail.strip_prefix('s')
                        .unwrap_or(tail)
                        .chars()
                        .next()
                        .is_none_or(boundary)
                } else {
                    suffix.chars().next().is_none_or(boundary)
                };
                (left && right).then_some((start, end))
            })
        })
        .collect()
}

// English-first lexical boundaries, deliberately conservative for non-ASCII
// punctuation. All non-whitespace Unicode scalars remain in the original word,
// including combining marks; folding must never create a new partial word.
fn prose_word_boundary(character: char) -> bool {
    character.is_whitespace()
        || (character.is_ascii_punctuation() && !matches!(character, '_' | '-' | '\''))
}

fn prose_word(word: &str) -> &str {
    let word = word.trim_matches(|character| {
        prose_word_boundary(character) || matches!(character, '\'' | '‘' | '’' | '“' | '”')
    });
    word.strip_suffix("'s")
        .or_else(|| word.strip_suffix("’s"))
        .unwrap_or(word)
}

fn prose_words(text: &str) -> Vec<String> {
    text.split(prose_word_boundary)
        .map(prose_word)
        .filter(|word| !word.is_empty())
        .map(str::to_lowercase)
        .collect()
}

fn validate_prose(
    engine: &Engine,
    approved: &Receipt,
    text: &str,
    evidence: Option<&NarratorEvidenceV22>,
    mode: ProseMode,
) -> Result<(), Error> {
    if text.trim().is_empty()
        || text.len() > 4096
        || text
            .chars()
            .any(|c| c.is_control() && c != '\n' && c != '\t')
    {
        return Err(Error::Narration);
    }
    let lower = text.to_lowercase();
    // NPC dialogue requires a separately scoped speaker call; this first narrator contract
    // cannot impersonate a character or turn arbitrary quoted words into their knowledge.
    if text.contains('"')
        || text.contains('“')
        || text.contains('”')
        || lower.contains(" says")
        || lower.contains(" said")
        || lower.contains("you say ")
        || lower.contains("you tell ")
        || lower.contains(" told ")
        || lower.contains(" tells ")
    {
        return Err(Error::Narration);
    }
    let mut original_source = crate::engine::render(approved.events());
    if let Some(evidence) = evidence {
        for observation in evidence.observations() {
            original_source.push('\n');
            original_source.push_str(observation.proposition());
        }
    }
    let source = original_source.to_lowercase();
    // Segment before case folding: Unicode lowercasing can expand one scalar
    // into a letter plus a combining mark, which must not create a new word.
    let source_words = if mode == ProseMode::WholeEvidenceWordsV1 {
        prose_words(&original_source)
    } else {
        Vec::new()
    };
    let output_words = if mode == ProseMode::WholeEvidenceWordsV1 {
        prose_words(text)
    } else {
        Vec::new()
    };
    for phrase in [
        "appears",
        "materializes",
        "acquires",
        "gains",
        "golden",
        "teleport",
        "immortal",
        "omnipotent",
        "king",
        "queen",
        "sword",
        "coins",
        "is proven",
        "everyone knows",
        "secret-",
    ] {
        let unsupported = if mode == ProseMode::WholeEvidenceWordsV1 {
            if phrase.contains(' ') {
                let words = prose_words(phrase);
                output_words.windows(words.len()).any(|part| part == words)
                    && !source_words.windows(words.len()).any(|part| part == words)
            } else {
                output_words.iter().any(|word| {
                    (if phrase.ends_with('-') {
                        word.starts_with(phrase)
                    } else {
                        word == phrase
                    }) && !source_words.contains(word)
                })
            }
        } else {
            (if phrase.contains(' ') {
                lower.contains(phrase)
            } else {
                lower
                    .split(|c: char| !c.is_alphanumeric() && c != '-')
                    .any(|word| {
                        if phrase.ends_with('-') {
                            word.starts_with(phrase)
                        } else {
                            word == phrase
                        }
                    })
            }) && !source.contains(phrase)
        };
        if unsupported {
            return Err(Error::Narration);
        }
    }
    let has = |kind: &str| {
        approved.events().iter().any(|e| {
            serde_json::to_value(e.outcome())
                .ok()
                .and_then(|v| v["effect"].as_str().map(str::to_owned))
                .as_deref()
                == Some(kind)
        })
    };
    for (kind, words) in [
        (
            "consumed",
            &[
                "healed",
                "cured",
                "injury disappears",
                "ankle mends",
                "wound closes",
                "injury vanishes",
                "energy restored",
            ][..],
        ),
        ("learned", &["mastered", "learned a", "new power"][..]),
        ("moved", &["arrives at", "travels to", "teleports"][..]),
    ] {
        if !has(kind) && words.iter().any(|word| lower.contains(word)) {
            return Err(Error::Narration);
        }
    }
    if has("given")
        && [
            "still holds",
            "still have",
            "keeps the potion",
            "retains the potion",
            "refuses",
            "refused",
            "never gave",
            "did not give",
        ]
        .iter()
        .any(|w| lower.contains(w))
    {
        return Err(Error::Narration);
    }
    if evidence.is_some()
        && narration_reclaims_transferred_item(approved, &engine.seed().player, &lower)
    {
        return Err(Error::Narration);
    }
    let visible: BTreeSet<_> = approved
        .events()
        .iter()
        .flat_map(|e| e.witnesses().iter().map(String::as_str))
        .collect();
    let visible_labels: BTreeSet<_> = engine
        .state()
        .actors
        .iter()
        .filter(|(id, _)| visible.contains(id.as_str()))
        .flat_map(|(id, actor)| [id.to_lowercase(), actor.name.to_lowercase()])
        .collect();
    let label_spans = narrator_visible_label_spans(&lower, &visible_labels, mode);
    let covered_label = |start, end| {
        label_spans
            .iter()
            .any(|&(label_start, label_end)| label_start <= start && end <= label_end)
    };
    // This profile has no authority to introduce a new named character. Keep the
    // conservative check to capitalized in-sentence tokens; it is no NLP proof.
    let mut sentence_start = 0;
    for sentence in text.split(['.', '!', '?', '\n']) {
        let mut word_end = 0;
        let words: Vec<_> = if mode == ProseMode::WholeEvidenceWordsV1 {
            sentence
                .split(prose_word_boundary)
                .filter(|word| !word.is_empty())
                .collect()
        } else {
            sentence.split_whitespace().collect()
        };
        for (index, word) in words.into_iter().enumerate() {
            let word_start = word_end + sentence[word_end..].find(word).ok_or(Error::Narration)?;
            word_end = word_start + word.len();
            let token = if mode == ProseMode::WholeEvidenceWordsV1 {
                prose_word(word)
            } else {
                let token = word.trim_matches(|c: char| !c.is_alphabetic());
                token
                    .strip_suffix("'s")
                    .or_else(|| token.strip_suffix("’s"))
                    .unwrap_or(token)
            };
            let token_start = sentence_start
                + word_start
                + if mode == ProseMode::WholeEvidenceWordsV1 {
                    word.find(token).ok_or(Error::Narration)?
                } else {
                    word.len() - word.trim_start_matches(|c: char| !c.is_alphabetic()).len()
                };
            // Lowercasing may expand a Unicode scalar. Convert the original
            // prefix/token lengths, rather than applying folded offsets to text.
            let folded_start = text[..token_start].to_lowercase().len();
            let folded_end = folded_start + token.to_lowercase().len();
            let opening_word = index == 0
                && [
                    "you",
                    "your",
                    "the",
                    "a",
                    "an",
                    "it",
                    "in",
                    "at",
                    "with",
                    "as",
                    "after",
                    "before",
                    "carefully",
                    "gently",
                    "quietly",
                ]
                .contains(&token.to_lowercase().as_str());
            let capitalized = if mode == ProseMode::WholeEvidenceWordsV1 {
                // A prefix such as o' must not hide an unsupported capitalized
                // continuation. Ground the complete original atomic word.
                token.chars().any(char::is_uppercase)
            } else {
                token.chars().next().is_some_and(char::is_uppercase)
            };
            // The English pronoun is inherently capitalized, not a named
            // entity. Scene-specific first-person restrictions still run.
            let grammatical_opening = opening_word
                || (mode == ProseMode::WholeEvidenceWordsV1 && index == 0 && token == "I");
            let evidence_word = if mode == ProseMode::WholeEvidenceWordsV1 {
                source_words.contains(&token.to_lowercase())
            } else {
                source.contains(&token.to_lowercase())
            };
            let grounded = visible_labels.contains(&token.to_lowercase())
                || evidence_word
                || covered_label(folded_start, folded_end);
            if capitalized && !grammatical_opening && !grounded {
                return Err(Error::Narration);
            }
        }
        // Each separator above is a single ASCII byte. Preserve the original
        // word positions so a matched name cannot create an opening-word grant.
        sentence_start += sentence.len() + 1;
    }
    for (id, actor) in &engine.state().actors {
        let hidden_mentioned = [
            (id.to_lowercase(), false),
            (actor.name.to_lowercase(), true),
        ]
        .iter()
        .any(|(label, is_name)| {
            !visible_labels.contains(label)
                && lower.match_indices(label).any(|(start, _)| {
                    let end = start + label.len();
                    let boundary = |c: char| !c.is_alphanumeric() && !matches!(c, '_' | '-');
                    lower[..start].chars().next_back().is_none_or(boundary)
                            && lower[end..].chars().next().is_none_or(boundary)
                            // A full known name may contain another actor's
                            // display name. Exempt that occurrence only; hidden
                            // IDs and the same name elsewhere remain guarded.
                            && !(*is_name && covered_label(start, end))
                })
        });
        if !visible.contains(id.as_str()) && hidden_mentioned {
            return Err(Error::Knowledge);
        }
    }
    // No off-screen actor or unknown consequence is introduced into state by passing this
    // check. Canon remains exclusively the mechanically resolved typed events.
    Ok(())
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct DirectorOutput {
    commands: Vec<Command>,
}

pub fn director_schema() -> Value {
    let mut variants = Vec::new();
    let specs = [
        (
            "give",
            json!({"item":{"type":"string"},"to":{"type":"string"},"quantity":{"type":"integer","minimum":1,"maximum":65535}}),
        ),
        ("consume", json!({"item":{"type":"string"}})),
        ("use_ability", json!({"ability":{"type":"string"}})),
        ("learn", json!({"ability":{"type":"string"}})),
        ("move", json!({"to":{"type":"string"}})),
        (
            "say",
            json!({"text":{"type":"string"},"audience":{"type":"array","items":{"type":"string"},"minItems":1,"maxItems":4}}),
        ),
        (
            "believe",
            json!({"claim_event":{"type":"integer","minimum":1}}),
        ),
        ("discover", json!({"fact":{"type":"string"}})),
        (
            "wait",
            json!({"ticks":{"type":"integer","minimum":1,"maximum":100}}),
        ),
    ];
    for (op, mut properties) in specs {
        properties["op"] = json!({"const":op});
        let required: Vec<_> = properties.as_object().unwrap().keys().cloned().collect();
        variants.push(json!({"type":"object","properties":properties,"required":required,"additionalProperties":false}));
    }
    json!({"type":"object","properties":{"commands":{"type":"array","minItems":1,"maxItems":MAX_COMMANDS,"items":{"oneOf":variants}}},"required":["commands"],"additionalProperties":false})
}

pub fn narration_schema(events: &[AcceptedEvent]) -> Value {
    json!({"type":"object","properties":{"text":{"type":"string","maxLength":4096},"event_ids":{"const":events.iter().map(|e|e.sequence()).collect::<Vec<_>>()},"speaker":{"const":"narrator"}},"required":["text","event_ids","speaker"],"additionalProperties":false})
}

/// Every semantic audience set has one sorted representation. Grow only within the
/// existing full-schema byte budget; never materialize an unbounded powerset.
fn dialogue_audience_sets(
    eligible: &[&String],
    from: usize,
    selected: &mut Vec<String>,
    choices: &mut Vec<Value>,
    schema_bytes: &mut usize,
) -> Result<(), Error> {
    for index in from..eligible.len() {
        selected.push(eligible[index].clone());
        crate::engine::check_json_budget(selected, MAX_PROPOSAL_BYTES)?;
        let bytes = serde_json::to_vec(selected).map_err(|_| Error::TooLarge)?;
        *schema_bytes = schema_bytes
            .checked_add(bytes.len())
            .and_then(|size| size.checked_add(usize::from(!choices.is_empty())))
            .filter(|size| *size <= MAX_PROPOSAL_BYTES)
            .ok_or(Error::TooLarge)?;
        choices.push(serde_json::to_value(&*selected).map_err(|_| Error::TooLarge)?);
        if selected.len() < 4 {
            dialogue_audience_sets(eligible, index + 1, selected, choices, schema_bytes)?;
        }
        selected.pop();
    }
    Ok(())
}

fn director_schema_for(
    kind: &PlayInputKind,
    text: &str,
    nearby: &BTreeMap<&String, &String>,
    inventory: &BTreeMap<&String, &Item>,
    player: &str,
    guarded_action: Option<&Command>,
) -> Result<Value, Error> {
    let mut schema = director_schema();
    if let Some(command) = guarded_action {
        // The same finite guard result already passed Engine preflight. Constrain generation
        // to that request, but never substitute this value for the provider's actual output.
        let fields = serde_json::to_value(command).expect("typed command serializes");
        let fields = fields.as_object().expect("tagged command is an object");
        let properties: serde_json::Map<String, Value> = fields
            .iter()
            .map(|(name, value)| (name.clone(), json!({"const": value})))
            .collect();
        let required: Vec<_> = fields.keys().collect();
        schema["properties"]["commands"]["items"]["oneOf"] = json!([{
            "type":"object", "properties":properties, "required":required,
            "additionalProperties":false
        }]);
        schema["properties"]["commands"]["maxItems"] = json!(1);
        return Ok(schema);
    }
    let variants = schema["properties"]["commands"]["items"]["oneOf"]
        .as_array_mut()
        .expect("fixed director schema");
    variants.retain(|variant| {
        let speech = variant["properties"]["op"]["const"] == "say";
        let has_item = !matches!(
            variant["properties"]["op"]["const"].as_str(),
            Some("give" | "consume")
        ) || !inventory.is_empty();
        speech == matches!(kind, PlayInputKind::Dialogue) && has_item
    });
    for variant in variants.iter_mut() {
        let op = variant["properties"]["op"]["const"]
            .as_str()
            .unwrap_or_default()
            .to_owned();
        if matches!(op.as_str(), "give" | "consume") {
            variant["properties"]["item"] = json!({"enum":inventory.keys().collect::<Vec<_>>()});
        }
        if op == "give" {
            variant["properties"]["to"] = json!({"enum":nearby.keys().collect::<Vec<_>>()});
        }
    }
    if matches!(kind, PlayInputKind::Dialogue) {
        schema["properties"]["commands"]["maxItems"] = json!(1);
        let properties = &mut schema["properties"]["commands"]["items"]["oneOf"][0]["properties"];
        properties["text"] = json!({"const":text});
        let audience: Vec<&String> = nearby
            .keys()
            .filter(|id| id.as_str() != player)
            .copied()
            .collect();
        properties["audience"]["items"] = json!({"enum":audience});
        // Array-valued enum is supported by the pinned constrained decoder;
        // uniqueItems is not. Keep all sets, not only the first nearby listener.
        properties["audience"]["enum"] = json!([]);
        crate::engine::check_json_budget(&schema, MAX_PROPOSAL_BYTES)?;
        let mut schema_bytes = serde_json::to_vec(&schema)
            .map_err(|_| Error::TooLarge)?
            .len();
        let mut choices = Vec::new();
        dialogue_audience_sets(
            &audience,
            0,
            &mut Vec::new(),
            &mut choices,
            &mut schema_bytes,
        )?;
        schema["properties"]["commands"]["items"]["oneOf"][0]["properties"]["audience"]["enum"] =
            Value::Array(choices);
        crate::engine::check_json_budget(&schema, MAX_PROPOSAL_BYTES)?;
    }
    // This guarded profile supports one explicit action or utterance per turn.
    schema["properties"]["commands"]["maxItems"] = json!(1);
    Ok(schema)
}

fn role_request(
    request: &Request,
    profile: &PlayProfile,
    role: &str,
    prompt: String,
    schema: Value,
    remaining_ms: u64,
) -> GenerationRequest {
    GenerationRequest {
        version: VERSION,
        scope: request.scope.clone(),
        turn: request.turn.clone(),
        revision: request.expected_revision,
        model_profile: profile.id.clone(),
        schema: format!("locallore-{role}-v2"),
        budget: Budget {
            max_output_bytes: MAX_PROPOSAL_BYTES,
            max_output_tokens: u32::from(if role == "director" {
                profile.director_tokens
            } else {
                profile.narrator_tokens
            }),
            max_pending_polls: 30_000,
            deadline_ms: remaining_ms,
        },
        input: Input::Structured {
            role: role.into(),
            prompt,
            schema,
        },
    }
}

/// Runs on an immutable coherent engine clone on a bounded native worker. It returns an
/// engine-created candidate; canonical Host/Store commit must still revalidate original head.
pub fn execute(
    engine: &mut Engine,
    request: &Request,
    provider: &mut (impl InferenceProvider + ?Sized),
    cancel: &Cancellation,
    profile: &PlayProfile,
) -> Result<Receipt, Error> {
    execute_traced(engine, request, provider, cancel, profile, None)
}

/// Optional passive metadata over the same production path. Hooks have no gameplay authority;
/// panics are isolated and callback duration is excluded from gameplay budgets/stage timings.
/// Success creates a candidate in this clone, NOT a durable Host/Store commit.
pub fn execute_traced(
    engine: &mut Engine,
    request: &Request,
    provider: &mut (impl InferenceProvider + ?Sized),
    cancel: &Cancellation,
    profile: &PlayProfile,
    sink: Option<&mut dyn TraceSink>,
) -> Result<Receipt, Error> {
    execute_traced_with_memory(engine, request, provider, cancel, profile, sink, None)
}

/// Trusted native-only input to the same production path. The accepted compiler
/// rechecks retained coverage against this actual Engine before selecting data.
/// Coverage rejection/fallback stays authoritative in that compiler. This cannot
/// grant observer access, bypass mandatory context or authorize canonical changes.
/// The candidate still requires a separate authoritative Host/Store commit.
pub fn execute_traced_with_memory(
    engine: &mut Engine,
    request: &Request,
    provider: &mut (impl InferenceProvider + ?Sized),
    cancel: &Cancellation,
    profile: &PlayProfile,
    sink: Option<&mut dyn TraceSink>,
    coverage: Option<&crate::memory_coverage::VerifiedCoverage>,
) -> Result<Receipt, Error> {
    execute_with_context_input(
        engine,
        request,
        provider,
        cancel,
        profile,
        sink,
        DirectorInput::Memory(MemoryInput {
            proof: coverage,
            source_fallback_reason: None,
            policy: PlayContextPolicy::StateRelevantMemoryV1,
        }),
    )
}

/// Snapshot-source variant preserving its closed raw-fallback reason separately
/// from compiler diagnostics. Raw input remains the same compiler raw path;
/// the source label never constructs a proof or becomes prompt/knowledge data.
pub fn execute_traced_with_coverage(
    engine: &mut Engine,
    request: &Request,
    provider: &mut (impl InferenceProvider + ?Sized),
    cancel: &Cancellation,
    profile: &PlayProfile,
    sink: Option<&mut dyn TraceSink>,
    coverage: &crate::memory_coverage::CoverageRead,
) -> Result<Receipt, Error> {
    execute_traced_with_policy(
        engine,
        request,
        provider,
        cancel,
        profile,
        sink,
        PlayConstructionInput {
            coverage,
            policy: PlayContextPolicy::StateRelevantMemoryV1,
        },
    )
}

/// Trusted native construction selection over the same coherent Engine/input.
/// Neither the requested policy nor source fallback grants knowledge or proof.
pub struct PlayConstructionInput<'a> {
    pub coverage: &'a crate::memory_coverage::CoverageRead,
    pub policy: PlayContextPolicy,
}
pub fn execute_traced_with_policy(
    engine: &mut Engine,
    request: &Request,
    provider: &mut (impl InferenceProvider + ?Sized),
    cancel: &Cancellation,
    profile: &PlayProfile,
    sink: Option<&mut dyn TraceSink>,
    input: PlayConstructionInput<'_>,
) -> Result<Receipt, Error> {
    let context = match input.coverage {
        crate::memory_coverage::CoverageRead::Verified(proof) => MemoryInput {
            proof: Some(proof),
            source_fallback_reason: None,
            policy: input.policy,
        },
        crate::memory_coverage::CoverageRead::RawFallback(reason) => MemoryInput {
            proof: None,
            source_fallback_reason: Some((*reason).into()),
            policy: input.policy,
        },
    };
    execute_with_context_input(
        engine,
        request,
        provider,
        cancel,
        profile,
        sink,
        DirectorInput::Memory(context),
    )
}

/// Explicit native literal Director construction through the same guard,
/// parser, staging, grounded narrator and atomic candidate commit. No Host or
/// JSON selection route is added. Exact recorded retries retain original bytes
/// and construction even when this entry or configuration differs.
pub fn execute_traced_with_literal_director_v1(
    engine: &mut Engine,
    request: &Request,
    provider: &mut (impl InferenceProvider + ?Sized),
    cancel: &Cancellation,
    profile: &PlayProfile,
    sink: Option<&mut dyn TraceSink>,
) -> Result<Receipt, Error> {
    execute_with_context_input(
        engine,
        request,
        provider,
        cancel,
        profile,
        sink,
        DirectorInput::LiteralV1,
    )
}
/// Versioned literal Director construction with seed-bound narrator presentation.
/// The literal source and Director renderer remain the immutable literal-v1 pair.
pub fn execute_traced_with_literal_director_presentation_v1(
    engine: &mut Engine,
    request: &Request,
    provider: &mut (impl InferenceProvider + ?Sized),
    cancel: &Cancellation,
    profile: &PlayProfile,
    sink: Option<&mut dyn TraceSink>,
) -> Result<Receipt, Error> {
    execute_with_presentation_input(
        engine,
        request,
        provider,
        cancel,
        profile,
        sink,
        PresentationExecutionInput {
            director: DirectorInput::LiteralV1,
            literal_presentation: true,
            scene_recipe: None,
        },
    )
}
struct MemoryInput<'a> {
    proof: Option<&'a crate::memory_coverage::VerifiedCoverage>,
    source_fallback_reason: Option<PlayMemoryFallback>,
    policy: PlayContextPolicy,
}

/// Explicit trusted-native scene selection. Existing entry points retain their
/// old construction; exact recorded identity wins before interpreting new input.
pub fn execute_traced_with_scene_recipe_v1(
    engine: &mut Engine,
    request: &Request,
    provider: &mut (impl InferenceProvider + ?Sized),
    cancel: &Cancellation,
    profile: &PlayProfile,
    sink: Option<&mut dyn TraceSink>,
    input: scene_narration::ScenePlayConstructionInput<'_>,
) -> Result<Receipt, Error> {
    if let Some(receipt) = engine.recorded(request)? {
        return Ok(receipt);
    }
    let director = match input.recipe {
        scene_narration::SceneRecipeV1::LiteralV1 => {
            if input.coverage.is_some() {
                return Err(Error::Rule);
            }
            DirectorInput::LiteralV1
        }
        scene_narration::SceneRecipeV1::Memory(policy) => {
            let (proof, source_fallback_reason) = match input.coverage {
                Some(crate::memory_coverage::CoverageRead::Verified(proof)) => (Some(proof), None),
                Some(crate::memory_coverage::CoverageRead::RawFallback(reason)) => {
                    (None, Some((*reason).into()))
                }
                None => (None, None),
            };
            DirectorInput::Memory(MemoryInput {
                proof,
                source_fallback_reason,
                policy,
            })
        }
    };
    execute_with_presentation_input(
        engine,
        request,
        provider,
        cancel,
        profile,
        sink,
        PresentationExecutionInput {
            director,
            literal_presentation: false,
            scene_recipe: Some(input.recipe),
        },
    )
}

enum NarrationPreparation {
    Legacy(crate::engine::staged_play::StagedPlayV25),
    Scene(crate::engine::staged_scene_play::BoundScenePlayV1),
}
impl NarrationPreparation {
    fn approved(&self) -> &Receipt {
        match self {
            Self::Legacy(s) => s.approved(),
            Self::Scene(s) => s.approved(),
        }
    }
    fn narrator_evidence(&self) -> &NarratorEvidenceV22 {
        match self {
            Self::Legacy(s) => s.narrator_evidence(),
            Self::Scene(s) => s.narrator_evidence(),
        }
    }
    fn scene(&self) -> Option<scene_narration::SceneNarrationRecordV1> {
        match self {
            Self::Legacy(_) => None,
            Self::Scene(s) => Some(s.provenance().clone()),
        }
    }
    fn validate_detailed(
        &self,
        engine: &Engine,
        record: &PlayRecord,
        presentation: bool,
        literal: bool,
        cancel: &dyn Fn() -> bool,
    ) -> Result<(), NarrationValidationFailureV1> {
        let staged = match self {
            Self::Legacy(staged) => staged,
            Self::Scene(bound) => {
                return scene_narration::validate_record_detailed(engine, bound, record, cancel)
            }
        };
        if presentation && literal {
            validate_record_literal_presentation_v1(
                engine,
                staged.approved(),
                staged.narrator_evidence(),
                record,
                false,
                cancel,
            )
        } else if presentation {
            validate_record_presentation_v1(
                engine,
                staged.approved(),
                staged.narrator_evidence(),
                record,
                false,
            )
        } else if literal {
            validate_record_literal_v1(
                engine,
                staged.approved(),
                staged.narrator_evidence(),
                record,
                false,
                cancel,
            )
        } else {
            validate_record_v25(
                engine,
                staged.approved(),
                staged.narrator_evidence(),
                record,
                false,
            )
        }
        .map_err(NarrationValidationFailureV1::from)
    }
    fn commit(
        self,
        engine: &mut Engine,
        record: &PlayRecord,
        presentation: bool,
        literal: bool,
        cancel: &dyn Fn() -> bool,
    ) -> Result<Receipt, Error> {
        match self {
            Self::Scene(bound) => engine.commit_scene_play_v1(bound, record, cancel),
            Self::Legacy(staged) => {
                if presentation && literal {
                    engine.commit_staged_literal_presentation_play_v1(staged, record, cancel)
                } else if presentation {
                    engine.commit_staged_presentation_play_v1(staged, record, cancel)
                } else if literal {
                    engine.commit_staged_literal_play_v1(staged, record, cancel)
                } else {
                    engine.commit_staged_play_v25(staged, record, cancel)
                }
            }
        }
    }
}
fn execute_with_context_input(
    engine: &mut Engine,
    request: &Request,
    provider: &mut (impl InferenceProvider + ?Sized),
    cancel: &Cancellation,
    profile: &PlayProfile,
    sink: Option<&mut dyn TraceSink>,
    input: DirectorInput<'_>,
) -> Result<Receipt, Error> {
    execute_with_presentation_input(
        engine,
        request,
        provider,
        cancel,
        profile,
        sink,
        PresentationExecutionInput {
            director: input,
            literal_presentation: false,
            scene_recipe: None,
        },
    )
}

struct PresentationExecutionInput<'a> {
    director: DirectorInput<'a>,
    literal_presentation: bool,
    scene_recipe: Option<scene_narration::SceneRecipeV1>,
}

fn execute_with_presentation_input(
    engine: &mut Engine,
    request: &Request,
    provider: &mut (impl InferenceProvider + ?Sized),
    cancel: &Cancellation,
    profile: &PlayProfile,
    sink: Option<&mut dyn TraceSink>,
    construction: PresentationExecutionInput<'_>,
) -> Result<Receipt, Error> {
    let PresentationExecutionInput {
        director: input,
        literal_presentation,
        scene_recipe,
    } = construction;
    let literal = matches!(&input, DirectorInput::LiteralV1);
    let presentation = engine.seed().presentation.is_some();
    let mut trace = Trace {
        sink,
        overhead: Duration::ZERO,
    };
    if let Some(sink) = trace.sink.as_deref_mut() {
        let started = Instant::now();
        let matched = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            sink.matches(
                &request.scope,
                request.expected_revision,
                &engine.seed().player,
                &request.turn,
            )
        }))
        .unwrap_or(false);
        trace.overhead = started.elapsed();
        if !matched {
            trace.sink = None;
        }
    }
    let recorded = trace.run(Stage::Intent, Outcome::Rejected, || {
        if let Some(receipt) = engine.recorded(request)? {
            return Ok(Some(receipt));
        }
        if literal && engine.domain_version() != 1 {
            return Err(Error::Version);
        }
        // Exact retries above retain their construction. New literal work must
        // opt into the new version; the old mapping is never repointed.
        if literal && scene_recipe.is_none() && presentation != literal_presentation {
            return Err(Error::Narration);
        }
        if let Some(recipe) = scene_recipe {
            scene_narration::check(&|| cancel.is_cancelled())?;
            scene_narration::check_seed(engine, recipe)?;
        }
        story_presentation::binding(engine)?;
        profile.validate()?;
        engine.preflight(request)?;
        if !matches!(request.intent, Intent::FreeText { .. }) {
            return Err(Error::Agency);
        }
        Ok(None)
    })?;
    if let Some(receipt) = recorded {
        return Ok(receipt);
    }
    let Intent::FreeText { kind, text } = &request.intent else {
        return Err(Error::Agency);
    };
    let guarded_action = if matches!(kind, PlayInputKind::Action) {
        // Refuse unsupported/ambiguous syntax before spending model work. The
        // generated proposal must match again during preview, commit and replay.
        Some(trace.run(Stage::Validation, Outcome::Rejected, || {
            let expected = crate::intent_guard::compile_action(engine, text)?;
            engine.stage_play_v25(
                request,
                &Proposal {
                    version: VERSION,
                    scope: request.scope.clone(),
                    turn: request.turn.clone(),
                    expected_revision: request.expected_revision,
                    commands: vec![expected.clone()],
                },
                &|| cancel.is_cancelled(),
            )?;
            Ok(expected)
        })?)
    } else {
        None
    };
    let started = trace.clock();
    let mut stages = Vec::new();
    let director_frame = if literal {
        None
    } else {
        Some(director_budget::DirectorEnvelopeV25::new(
            engine,
            request,
            profile,
            guarded_action.as_ref(),
        )?)
    };
    let director = trace.counted(
        Stage::Retrieval,
        Outcome::Rejected,
        || PreparedDirector::new(engine, request, profile, director_frame, input, cancel),
        |director| Counts {
            eligible_records: director.retrieval_count(),
            input_tokens: Some(TokenCount {
                value: director.input_tokens(),
                basis: TokenBasis::Estimated,
            }),
            ..Counts::default()
        },
    )?;
    if let Some(compiled) = director.package() {
        trace.capture(crate::turn_capture::Artifact::Context(compiled));
    }
    trace.counted(
        Stage::Context,
        Outcome::Rejected,
        || {
            director.ensure_audience()?;
            director.render(engine, request, profile, DirectorPassV25::Initial, cancel)
        },
        |_| Counts {
            eligible_records: director.frame_count(),
            ..Counts::default()
        },
    )?;
    let mut repairs = 0;
    let proposal = loop {
        let before = trace.clock();
        let overhead = trace.overhead;
        let (bytes, _) = trace.generate(
            if repairs == 0 {
                Stage::Director
            } else {
                Stage::Repair
            },
            provider,
            cancel,
            || {
                let rendered = director.render(
                    engine,
                    request,
                    profile,
                    if repairs == 0 {
                        DirectorPassV25::Initial
                    } else {
                        DirectorPassV25::Repair
                    },
                    cancel,
                )?;
                let mut generation = role_request(
                    request,
                    profile,
                    "director",
                    rendered.prompt,
                    rendered.schema,
                    remaining(started, overhead, profile.deadline_ms)?,
                );
                if literal {
                    generation.schema = LITERAL_DIRECTOR_SCHEMA_ID_V1.into();
                }
                Ok(generation)
            },
        )?;
        trace.capture(crate::turn_capture::Artifact::DirectorOutput(&bytes));
        stages.push(StageTiming {
            stage: if repairs == 0 { "director" } else { "repair" }.into(),
            elapsed_ms: trace.elapsed(before).as_millis() as u64,
        });
        let parsed: Result<DirectorOutput, Error> = trace.counted(
            Stage::Parsing,
            Outcome::Rejected,
            || crate::engine::parse_unique(&bytes),
            |output: &DirectorOutput| Counts {
                operations: output.commands.len().min(u16::MAX as usize) as u16,
                repairs,
                ..Counts::default()
            },
        );
        match parsed {
            Ok(output) => {
                break Proposal {
                    version: VERSION,
                    scope: request.scope.clone(),
                    turn: request.turn.clone(),
                    expected_revision: request.expected_revision,
                    commands: output.commands,
                }
            }
            Err(_) if repairs < profile.repair_limit => repairs += 1,
            Err(_) => return Err(Error::Malformed),
        }
    };
    trace.capture(crate::turn_capture::Artifact::Proposal(&proposal));
    let before = trace.clock();
    let staged = trace.counted(
        Stage::Validation,
        Outcome::Rejected,
        || {
            let poll = &|| cancel.is_cancelled();
            match scene_recipe {
                Some(recipe) => {
                    let preparation = engine.stage_scene_play_v1(request, &proposal, poll)?;
                    engine
                        .bind_scene_play_v1(preparation, recipe, poll)
                        .map(NarrationPreparation::Scene)
                }
                None => engine
                    .stage_play_v25(request, &proposal, poll)
                    .map(NarrationPreparation::Legacy),
            }
        },
        |staged| Counts {
            operations: staged.approved().events().len().min(u16::MAX as usize) as u16,
            repairs,
            ..Counts::default()
        },
    )?;
    let approved = staged.approved();
    trace.capture(crate::turn_capture::Artifact::ApprovedPlan(approved));
    stages.push(StageTiming {
        stage: "validation".into(),
        elapsed_ms: trace.elapsed(before).as_millis() as u64,
    });
    let overhead = trace.overhead;
    let (bytes, narrator_elapsed_ms) = trace.generate(Stage::Narration, provider, cancel, || {
    if let NarrationPreparation::Scene(bound) = &staged {
        let rendered = scene_narration::render_scene_narrator_v1(bound, profile, &|| cancel.is_cancelled())?;
        return Ok(role_request(request, profile, "narrator", rendered.prompt().into(), rendered.schema().clone(),
            remaining(started, overhead, profile.deadline_ms)?));
    }
    // The opaque candidate made these event-specific observations in Core.
    // Never attach the compiled Director context, seed truth or raw Receipt.
    let evidence = staged.narrator_evidence();
    crate::engine::check_json_budget(evidence, MAX_RECEIPT_BYTES)?;
    let safe = serde_json::to_string(evidence).map_err(|_| Error::TooLarge)?;
    let prompt=format!("Write brief natural story prose in second person from ONLY this approved evidence. The action has already resolved. Observation values describe ONLY discoveries actually made in this turn. No additional items, abilities, healing, movement, discoveries, hidden facts or NPC knowledge. Give is possession transfer, not consumption or healing. A delivered statement supplies no quotation or established fact. No NPC quotation or impersonation. Small sensory/emotional description is allowed. Return JSON text, event_ids and speaker narrator. Approved evidence: {safe}");
    let prompt = story_presentation::narrator_prompt(engine, prompt)?;
    crate::engine::check_json_budget(&prompt, MAX_ROLE_INPUT_BYTES)?;
    let generation = role_request(
        request,
        profile,
        "narrator",
        prompt,
        narration_schema(approved.events()),
                remaining(started, overhead, profile.deadline_ms)?,
    );
    Ok(generation)
    })?;
    trace.capture(crate::turn_capture::Artifact::NarratorOutput(&bytes));
    stages.push(StageTiming {
        stage: "narrator".into(),
        elapsed_ms: narrator_elapsed_ms,
    });
    let mut record = PlayRecord {
        version: PLAY_VERSION,
        policy: if scene_recipe.is_some() {
            scene_narration::SCENE_NARRATION_POLICY_V2
        } else if presentation {
            PRESENTATION_NARRATION_POLICY
        } else if literal {
            LITERAL_NARRATION_POLICY_V1
        } else {
            NARRATION_POLICY
        }
        .into(),
        prompt_version: if let Some(recipe) = scene_recipe {
            recipe.prompt_version()
        } else if presentation && literal {
            LITERAL_PRESENTATION_PROMPT_VERSION_V1
        } else if presentation {
            PRESENTATION_PROMPT_VERSION
        } else if literal {
            LITERAL_PLAY_PROMPT_VERSION_V1
        } else {
            PROMPT_VERSION
        }
        .into(),
        profile: profile.clone(),
        repairs,
        fallback: false,
        narration: trace
            .run(Stage::Parsing, Outcome::Rejected, || {
                crate::engine::parse_unique(&bytes)
            })
            .unwrap_or_else(|_| NarrationDocument {
                text: String::new(),
                event_ids: Vec::new(),
                speaker: String::new(),
            }),
        stages,
        context: director.context_record(),
        context_policy: director.policy(),
        story_presentation: story_presentation::binding(engine)?,
        scene: staged.scene(),
    };
    let before = trace.clock();
    let mut reason = None;
    let validation = trace.run(Stage::NarrationValidation, Outcome::Rejected, || {
        staged
            .validate_detailed(engine, &record, presentation, literal, &|| {
                cancel.is_cancelled()
            })
            .map_err(|failure| {
                reason = failure.reason;
                failure.into_engine_error()
            })
    });
    let (outcome, error) = match &validation {
        Ok(()) => (Outcome::Accepted, None),
        Err(error) => (
            match error {
                Error::Cancelled => Outcome::Cancelled,
                Error::Stale => Outcome::Stale,
                _ => Outcome::Rejected,
            },
            Some(ErrorCategory::from_engine(error)),
        ),
    };
    // The original stage callback is first; a panic there disables this hook.
    trace.narration_validation(NarrationValidationDiagnosticV1::new(outcome, error, reason));
    // The passive post-validation callback can cancel after validation returned.
    // Poll before an excluded fallback could mask that cancellation as Narration.
    if scene_recipe.is_some() {
        scene_narration::check(&|| cancel.is_cancelled())?;
        if validation == Err(Error::Cancelled) {
            return Err(Error::Cancelled);
        }
    }
    if validation.is_err() {
        record.fallback = true;
        record.narration = NarrationDocument {
            text: approved.narration().into(),
            event_ids: approved.events().iter().map(|e| e.sequence()).collect(),
            speaker: "narrator".into(),
        };
    }
    // Exact mechanical fallback cannot bypass presentation restrictions or
    // manufacture a replacement event description.
    engine.validate_story_narration(&record.narration.text)?;
    record.stages.push(StageTiming {
        stage: "narration_validation".into(),
        elapsed_ms: trace.elapsed(before).as_millis() as u64,
    });
    record.stages.push(StageTiming {
        stage: "total".into(),
        elapsed_ms: trace.elapsed(started).as_millis() as u64,
    });
    let overhead = trace.overhead;
    let receipt = trace.run(Stage::AcceptedCandidate, Outcome::Rejected, || {
        remaining(started, overhead, profile.deadline_ms)?;
        if cancel.is_cancelled() {
            return Err(Error::Cancelled);
        }
        staged.commit(engine, &record, presentation, literal, &|| {
            cancel.is_cancelled()
        })
    })?;
    trace.capture(crate::turn_capture::Artifact::Candidate(&receipt));
    trace.not_run(Stage::MemoryMaintenance);
    Ok(receipt)
}
