//! Actor-only exact/lexical context. Reuses authoritative context and shared eligibility.
//! No native Host, database, tokenizer, summary or provider authority.
use crate::{
    contracts::{AcceptedEvent, Effect, Profile, Scope, VERSION},
    engine::Engine,
    inspection_query::{self, FieldValue, Row, Source, ValueOrigin, View},
};

mod policy;
mod verified;
pub(crate) use policy::compile_for_director_cancelled;
pub use policy::{
    compile_policy_cancelled, ConstructionDiagnostics, ContextPolicy, PolicyCompilation,
    TranscriptUnit, POLICY_COMPILER_VERSION,
};
use serde::{Deserialize, Serialize};
use std::{
    borrow::Cow,
    collections::{BTreeMap, BTreeSet},
};
pub use verified::{
    compile_verified_cancelled, CoverageDiagnostics, CoverageMode, MemoryCompilation,
    MemoryFallbackReason,
};

pub const COMPILER_VERSION: u16 = 1;
pub const MAX_CONTEXT_BYTES: usize = 24_576;
const MAX_CANDIDATES: usize = 8192;
const MAX_CANDIDATE_BYTES: usize = 2 * 1024 * 1024;
const MAX_SELECTED: usize = 128;
const MAX_DIAGNOSTICS: usize = 32;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum Role {
    Director,
    Character,
}
#[derive(Clone, Copy, Debug)]
pub struct Budget {
    pub max_bytes: usize,
    pub estimated_tokens: u32,
    pub reserved_tokens: u32,
    pub recent_events: u8,
    pub optional_records: u16,
}
impl Default for Budget {
    fn default() -> Self {
        Self {
            max_bytes: MAX_CONTEXT_BYTES,
            estimated_tokens: 4096,
            reserved_tokens: 512,
            recent_events: 4,
            optional_records: 16,
        }
    }
}
#[derive(Clone, Debug)]
pub struct CompileRequest {
    pub version: u16,
    pub scope: Scope,
    pub expected_head: u64,
    pub at_revision: Option<u64>,
    pub observer: String,
    pub role: Role,
    pub query: String,
    pub referenced_ids: Vec<String>,
    pub budget: Budget,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum CompileError {
    Cancelled,
    Version,
    Scope,
    Stale,
    Observer,
    Boundary,
    UnsupportedBranch,
    InvalidRequest,
    TooLarge,
    Source,
    UnknownReference,
    AmbiguousAlias,
    MandatoryBudget,
    UnsupportedPolicy,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum Kind {
    Rules,
    Alias,
    CurrentState,
    Truth,
    Statement,
    Belief,
    Discovery,
    Observation,
    Relationship,
    Commitment,
    KnownAsObserved,
    Transcript,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum Reason {
    Rules,
    CurrentState,
    KnownTruth,
    CurrentBelief,
    OpenCommitment,
    Relationship,
    SupportingEvidence,
    Recent,
    Referenced,
    ExactId,
    Lexical,
    Budget,
    OptionalLimit,
    NotRelevant,
    KnownAsObserved,
    AlreadySelected,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
#[serde(tag = "type", content = "value", rename_all = "snake_case")]
pub enum Payload {
    Rules {
        version: u16,
        profile: Profile,
        policies: Vec<&'static str>,
    },
    Alias {
        actor: String,
        name: String,
    },
    Record(Box<Row>),
    TranscriptUnit(Box<TranscriptUnit>),
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct Selected {
    pub id: String,
    pub kind: Kind,
    pub source_revision: u64,
    pub sources: Vec<Source>,
    pub reason: Reason,
    pub score: u32,
    pub mandatory: bool,
    pub payload: Payload,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct Omission {
    pub id: String,
    pub reason: Reason,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct Diagnostics {
    pub eligible_candidates: usize,
    pub omitted_eligible: usize,
    pub omissions: Vec<Omission>,
    pub omissions_truncated: bool,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct ContextPackage {
    pub version: u16,
    pub scope: Scope,
    pub head: u64,
    pub revision: u64,
    pub historical: bool,
    pub observer: String,
    pub role: Role,
    pub records: Vec<Selected>,
    pub diagnostics: Diagnostics,
    pub serialized_bytes: usize,
    pub estimated_tokens: u32,
    pub token_accounting: &'static str,
    pub reserved_tokens: u32,
    pub unsupported: Vec<&'static str>,
}
struct Candidate {
    key: String,
    payload: CandidatePayload,
    encoded: String,
    ids: BTreeSet<String>,
    kind: Kind,
    sources: Vec<Source>,
    revision: u64,
}
enum CandidatePayload {
    Row(Row),
    TranscriptUnit(TranscriptUnit),
}
impl Candidate {
    fn row(&self) -> Option<&Row> {
        match &self.payload {
            CandidatePayload::Row(row) => Some(row),
            CandidatePayload::TranscriptUnit(_) => None,
        }
    }
    fn key(&self) -> &str {
        &self.key
    }
    fn from_row(row: Row, encoded: String, revision: u64, version: u16) -> Self {
        let (ids, _) = identifiers(&row);
        let (kind, sources, revision) = row_info(&row, revision, version);
        Self {
            key: row.key().into(),
            payload: CandidatePayload::Row(row),
            encoded,
            ids,
            kind,
            sources,
            revision,
        }
    }
}
struct CompilationResult {
    compilation: MemoryCompilation,
    construction: ConstructionDiagnostics,
}
fn valid_id(id: &str) -> bool {
    !id.is_empty()
        && id.len() <= 64
        && id
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b"-_".contains(&b))
}
fn check(cancel: &dyn Fn() -> bool) -> Result<(), CompileError> {
    if std::panic::catch_unwind(std::panic::AssertUnwindSafe(cancel)).unwrap_or(true) {
        Err(CompileError::Cancelled)
    } else {
        Ok(())
    }
}
fn snapshot<'a>(
    engine: &'a Engine,
    request: &CompileRequest,
    construction: policy::Construction,
) -> Result<Cow<'a, Engine>, CompileError> {
    if request.version != construction.version() {
        return Err(CompileError::Version);
    }
    if request.scope != *engine.scope() {
        return Err(CompileError::Scope);
    }
    if request.expected_head != engine.revision() {
        return Err(CompileError::Stale);
    }
    let revision = request.at_revision.unwrap_or(engine.revision());
    let snapshot = if revision == engine.revision() {
        Cow::Borrowed(engine)
    } else {
        Cow::Owned(engine.at_revision(revision).map_err(|error| match error {
            crate::contracts::Error::Rule => CompileError::Boundary,
            _ => CompileError::Source,
        })?)
    };
    if !valid_id(&request.observer)
        || !snapshot.state().actors.contains_key(&request.observer)
        || (request.role == Role::Director && request.observer != snapshot.seed().player)
    {
        return Err(CompileError::Observer);
    }
    Ok(snapshot)
}
fn actor_rows(
    engine: &Engine,
    observer: &str,
    view: View,
    construction: policy::Construction,
) -> Result<Vec<Row>, CompileError> {
    let rows = if construction.is_current() {
        inspection_query::actor_context_rows_v2(engine, observer, view)
    } else {
        inspection_query::actor_context_rows(engine, observer, view)
    }
    .map_err(|_| CompileError::Source)?;
    if rows.len() > MAX_CANDIDATES {
        return Err(CompileError::TooLarge);
    }
    Ok(rows)
}
fn row_info(row: &Row, revision: u64, version: u16) -> (Kind, Vec<Source>, u64) {
    let (kind, sources) = match row {
        Row::Field { source, .. } => (Kind::CurrentState, vec![source.clone()]),
        Row::Knowledge {
            origin, sources, ..
        } => (
            match origin {
                ValueOrigin::CanonicalTruth => Kind::Truth,
                ValueOrigin::RecordedStatement => Kind::Statement,
                ValueOrigin::SubjectiveBelief => Kind::Belief,
                ValueOrigin::RecordedDiscovery => Kind::Discovery,
                ValueOrigin::KnownAsObserved => Kind::KnownAsObserved,
                _ => Kind::Observation,
            },
            sources.clone(),
        ),
        Row::Event { event, .. } => (
            Kind::Observation,
            vec![if version == 2 {
                Source::ScopedEvent {
                    original_scope: event.scope.clone(),
                    sequence: event.sequence,
                }
            } else {
                Source::Event(event.sequence)
            }],
        ),
        Row::Relationship { source, .. } => (Kind::Relationship, vec![source.clone()]),
        Row::Promise { sources, .. } => (Kind::Commitment, sources.clone()),
        _ => (Kind::Observation, vec![]),
    };
    let source_revision = sources
        .iter()
        .filter_map(|s| match s {
            Source::Event(id) | Source::ScopedEvent { sequence: id, .. } => Some(*id),
            _ => None,
        })
        .max()
        .unwrap_or(0)
        .min(revision);
    (kind, sources, source_revision)
}
fn identifiers(row: &Row) -> (BTreeSet<String>, BTreeSet<String>) {
    let mut ids = BTreeSet::new();
    let mut actors = BTreeSet::new();
    match row {
        Row::Field {
            actor,
            field,
            value,
            ..
        } => {
            actors.insert(actor.clone());
            if let Some((_, id)) = field.split_once('/') {
                ids.insert(id.into());
            }
            if let FieldValue::Item(item) = value {
                actors.insert(item.owner.clone());
                actors.extend(item.return_to.iter().cloned());
            }
            if field == "location" {
                if let FieldValue::Text(location) = value {
                    ids.insert(location.clone());
                }
            }
        }
        Row::Knowledge { id, subject, .. } => {
            ids.insert(id.clone());
            actors.extend(subject.iter().cloned());
        }
        Row::Relationship { from, to, .. } | Row::Promise { from, to, .. } => {
            actors.extend([from.clone(), to.clone()]);
            if let Row::Promise {
                id, return_item, ..
            } = row
            {
                ids.insert(id.clone());
                ids.extend(return_item.iter().cloned());
            }
        }
        Row::Event { event, .. } => {
            actors.extend(event.participants.iter().chain(&event.witnesses).cloned());
            match &event.consequence {
                Effect::Given { item, .. } | Effect::Consumed { item, .. } => {
                    ids.insert(item.clone());
                }
                Effect::AbilityUsed { ability, .. } | Effect::Learned { ability, .. } => {
                    ids.insert(ability.clone());
                }
                Effect::Moved { from, to, .. } => {
                    ids.extend([from.clone(), to.clone()]);
                }
                Effect::Discovered { fact, .. } => {
                    ids.insert(fact.clone());
                }
                Effect::Promised { id, .. } | Effect::PromiseCompleted { id, .. } => {
                    ids.insert(id.clone());
                }
                _ => {}
            }
        }
        _ => {}
    }
    ids.extend(actors.iter().cloned());
    (ids, actors)
}
fn tokens(text: &str) -> BTreeSet<String> {
    text.split(|c: char| !c.is_alphanumeric() && c != '-' && c != '_')
        .filter(|s| !s.is_empty())
        .map(str::to_lowercase)
        .collect()
}
fn tags(row: &Row) -> &'static str {
    match row {
        Row::Event { event, .. } => match event.consequence {
            Effect::Given { .. } => "gift give given transfer",
            Effect::Promised { .. } => "promise promised commitment obligation",
            Effect::Said(_) => "say said statement speech",
            Effect::Discovered { .. } => "discovery discover fact",
            Effect::Learned { .. } => "learn learned ability",
            _ => "event",
        },
        Row::Promise { .. } => "promise commitment obligation",
        _ => "",
    }
}
fn selected(candidate: &Candidate, reason: Reason, score: u32, mandatory: bool) -> Selected {
    Selected {
        id: candidate.key().into(),
        kind: candidate.kind,
        source_revision: candidate.revision,
        sources: candidate.sources.clone(),
        reason,
        score,
        mandatory,
        payload: match &candidate.payload {
            CandidatePayload::Row(row) => Payload::Record(Box::new(row.clone())),
            CandidatePayload::TranscriptUnit(unit) => {
                Payload::TranscriptUnit(Box::new(unit.clone()))
            }
        },
    }
}
fn measure(package: &mut ContextPackage) -> Result<(), CompileError> {
    // Account for the complete response, including diagnostics and the accounting fields.
    for _ in 0..16 {
        let bytes = serde_json::to_vec(package)
            .map_err(|_| CompileError::Source)?
            .len();
        let estimated = bytes.div_ceil(4).min(u32::MAX as usize) as u32;
        if package.serialized_bytes == bytes && package.estimated_tokens == estimated {
            return Ok(());
        }
        package.serialized_bytes = bytes;
        package.estimated_tokens = estimated;
    }
    Err(CompileError::Source)
}
#[derive(Clone, Copy)]
enum FitBasis<'a> {
    DiagnosticWire,
    Director(&'a crate::play::director_budget::DirectorEnvelopeV25),
}
fn fits(
    package: &mut ContextPackage,
    budget: Budget,
    basis: FitBasis<'_>,
) -> Result<bool, CompileError> {
    measure(package)?;
    if package.serialized_bytes > budget.max_bytes || package.records.len() > MAX_SELECTED {
        return Ok(false);
    }
    match basis {
        FitBasis::DiagnosticWire => Ok(package
            .estimated_tokens
            .saturating_add(budget.reserved_tokens)
            <= budget.estimated_tokens),
        FitBasis::Director(frame) => match frame.estimate_max_pass(package) {
            Ok(_) => Ok(true),
            Err(crate::contracts::Error::TooLarge) => Ok(false),
            Err(crate::contracts::Error::Stale) => Err(CompileError::Stale),
            Err(_) => Err(CompileError::Source),
        },
    }
}

pub fn compile(engine: &Engine, request: &CompileRequest) -> Result<ContextPackage, CompileError> {
    compile_cancelled(engine, request, &|| false)
}

fn push_row(
    rows: &mut Vec<(Row, String)>,
    bytes: &mut usize,
    row: Row,
    cancel: &dyn Fn() -> bool,
) -> Result<(), CompileError> {
    check(cancel)?;
    if rows.len() >= MAX_CANDIDATES {
        return Err(CompileError::TooLarge);
    }
    let encoded = serde_json::to_string(&row).map_err(|_| CompileError::Source)?;
    *bytes = bytes
        .checked_add(encoded.len())
        .ok_or(CompileError::TooLarge)?;
    if *bytes > MAX_CANDIDATE_BYTES {
        return Err(CompileError::TooLarge);
    }
    rows.push((row, encoded));
    check(cancel)
}

/// Cooperative checks around compiler stages and each retained row. Historical
/// replay and the existing shared actor-row collector remain synchronous work;
/// this does not promise a hard whole-operation cancellation deadline.
pub fn compile_cancelled(
    engine: &Engine,
    request: &CompileRequest,
    cancel: &dyn Fn() -> bool,
) -> Result<ContextPackage, CompileError> {
    compile_inner(
        engine,
        request,
        verified::Input::Legacy,
        policy::Construction::Legacy,
        cancel,
    )
    .map(|result| result.compilation.package)
}

fn event_row(event: &AcceptedEvent) -> Result<Row, CompileError> {
    #[derive(Deserialize)]
    struct Metadata {
        turn: String,
        story_time: u64,
        participants: BTreeSet<String>,
    }
    let metadata: Metadata =
        serde_json::from_value(serde_json::to_value(event).map_err(|_| CompileError::Source)?)
            .map_err(|_| CompileError::Source)?;
    Ok(Row::Event {
        key: format!("event:{:020}", event.sequence()),
        event: inspection_query::EventRow {
            sequence: event.sequence(),
            scope: event.scope().clone(),
            turn: metadata.turn,
            story_time: metadata.story_time,
            participants: metadata.participants,
            witnesses: event.witnesses().clone(),
            consequence: event.outcome().clone(),
        },
        origin: ValueOrigin::RecordedObservation,
    })
}

#[allow(clippy::too_many_arguments)] // Keep scoped range and version dispatch explicit.
fn visit_events(
    engine: &Engine,
    observer: &str,
    after: u64,
    through: u64,
    version: u16,
    cancel: &dyn Fn() -> bool,
    visitor: &mut dyn FnMut(&AcceptedEvent) -> Result<(), CompileError>,
) -> Result<(), CompileError> {
    let mut failure = None;
    let mut callback = |event: &AcceptedEvent| match visitor(event) {
        Ok(()) => true,
        Err(error) => {
            failure = Some(error);
            false
        }
    };
    let result = if version == 2 {
        engine.visit_actor_observations_v2(
            observer,
            engine.scope(),
            engine.revision(),
            after,
            through,
            &|| check(cancel).is_err(),
            &mut |event| callback(&event.event),
        )
    } else {
        engine.visit_actor_observations(
            observer,
            engine.scope(),
            engine.revision(),
            after,
            through,
            &|| check(cancel).is_err(),
            &mut callback,
        )
    };
    result.map_err(|error| match error {
        crate::contracts::Error::Cancelled => CompileError::Cancelled,
        _ => CompileError::Source,
    })?;
    failure.map_or(Ok(()), Err)
}

fn compile_inner(
    engine: &Engine,
    request: &CompileRequest,
    input: verified::Input<'_>,
    construction: policy::Construction,
    cancel: &dyn Fn() -> bool,
) -> Result<CompilationResult, CompileError> {
    compile_inner_with_fit(
        engine,
        request,
        input,
        construction,
        FitBasis::DiagnosticWire,
        cancel,
    )
}
fn compile_inner_with_fit(
    engine: &Engine,
    request: &CompileRequest,
    input: verified::Input<'_>,
    construction: policy::Construction,
    fit_basis: FitBasis<'_>,
    cancel: &dyn Fn() -> bool,
) -> Result<CompilationResult, CompileError> {
    check(cancel)?;
    // Explicit legacy refusal before snapshot/replay, proof inspection or hashing.
    if !construction.is_current() && engine.domain_version() != 1 {
        return Err(CompileError::Version);
    }
    if let FitBasis::Director(frame) = fit_basis {
        frame.validate_basis(request)?;
    }
    let b = request.budget;
    if !(1024..=MAX_CONTEXT_BYTES).contains(&b.max_bytes)
        || b.estimated_tokens == 0
        || b.estimated_tokens > 4096
        || b.reserved_tokens >= b.estimated_tokens
        || b.recent_events > 8
        || b.optional_records > 64
        || request.query.len() > 512
        || request.query.chars().any(char::is_control)
        || request.referenced_ids.len() > 16
        || request.referenced_ids.iter().any(|id| !valid_id(id))
        || tokens(&request.query).len() > 64
    {
        return Err(CompileError::InvalidRequest);
    }
    let snapshot = snapshot(engine, request, construction)?;
    check(cancel)?;
    let mut rows = vec![];
    let mut row_bytes = 0;
    for view in [
        View::Profiles,
        View::Knowledge,
        View::Promises,
        View::Relationships,
    ] {
        check(cancel)?;
        for row in actor_rows(&snapshot, &request.observer, view, construction)? {
            push_row(&mut rows, &mut row_bytes, row, cancel)?;
        }
    }
    let mut memory = verified::collect(
        &snapshot,
        request,
        input,
        construction,
        &mut rows,
        &mut row_bytes,
        cancel,
    )?;
    check(cancel)?;
    rows.sort_by(|(a, _), (b, _)| a.key().cmp(b.key()));
    check(cancel)?;
    let mut candidates = vec![];
    let mut known = BTreeSet::new();
    let mut known_actors = BTreeSet::new();
    for (row, encoded) in rows {
        check(cancel)?;
        let (ids, actors) = identifiers(&row);
        known.extend(ids.iter().cloned());
        known_actors.extend(actors);
        candidates.push(Candidate::from_row(
            row,
            encoded,
            snapshot.revision(),
            request.version,
        ));
    }
    // Current canonical display names of ALREADY eligible actor IDs only, not a global alias scan.
    if known_actors.len() > 256 {
        return Err(CompileError::TooLarge);
    }
    let mut aliases: BTreeMap<String, BTreeSet<String>> = BTreeMap::new();
    for actor in &known_actors {
        check(cancel)?;
        if let Some(state) = snapshot.state().actors.get(actor) {
            if state.name.len() > 256 {
                return Err(CompileError::TooLarge);
            }
            aliases
                .entry(state.name.to_lowercase())
                .or_default()
                .insert(actor.clone());
        }
    }
    let query_tokens = tokens(&request.query);
    let exact_query_tokens: BTreeSet<_> = request
        .query
        .split(|c: char| !c.is_alphanumeric() && c != '-' && c != '_')
        .filter(|s| !s.is_empty())
        .collect();
    let query_words = request.query.to_lowercase();
    let mut references: BTreeSet<String> = request.referenced_ids.iter().cloned().collect();
    if references.iter().any(|id| !known.contains(id)) {
        return Err(CompileError::UnknownReference);
    }
    references.extend(
        known
            .iter()
            .filter(|id| exact_query_tokens.contains(id.as_str()))
            .cloned(),
    );
    for (name, actors) in aliases {
        check(cancel)?;
        let name_tokens = tokens(&name);
        if !name_tokens.is_empty()
            && name_tokens.is_subset(&query_tokens)
            && query_words.contains(&name)
        {
            if actors.len() > 1 && !actors.iter().any(|id| references.contains(id)) {
                return Err(CompileError::AmbiguousAlias);
            }
            if actors.len() == 1 {
                references.extend(actors);
            }
        }
    }
    let mut mandatory: BTreeMap<String, Reason> = BTreeMap::new();
    for c in &candidates {
        check(cancel)?;
        let reason = match c.row() {
            Some(Row::Field { .. }) => Some(Reason::CurrentState),
            Some(Row::Knowledge {
                origin: ValueOrigin::CanonicalTruth,
                ..
            }) => Some(Reason::KnownTruth),
            Some(Row::Knowledge {
                origin: ValueOrigin::KnownAsObserved,
                ..
            }) => Some(Reason::KnownAsObserved),
            Some(Row::Knowledge {
                origin: ValueOrigin::SubjectiveBelief,
                ..
            }) => Some(Reason::CurrentBelief),
            Some(Row::Promise { status, .. }) if status != "fulfilled" => {
                Some(Reason::OpenCommitment)
            }
            Some(Row::Relationship { .. }) => Some(Reason::Relationship),
            _ => None,
        };
        if let Some(reason) = reason {
            mandatory.insert(c.key().into(), reason);
        }
    }
    let mut events: Vec<_> = candidates
        .iter()
        .filter(|c| matches!(c.row(), Some(Row::Event { .. })))
        .collect();
    events.sort_by_key(|c| c.revision);
    for c in events.iter().rev().take(usize::from(b.recent_events)) {
        check(cancel)?;
        mandatory.entry(c.key().into()).or_insert(Reason::Recent);
    }
    for id in &references {
        check(cancel)?;
        if let Some(c) = events.iter().rev().find(|c| c.ids.contains(id)) {
            mandatory
                .entry(c.key().into())
                .or_insert(Reason::Referenced);
        }
    }
    let required_sources: BTreeSet<_> = candidates
        .iter()
        .filter(|c| mandatory.contains_key(c.key()))
        .flat_map(|c| c.sources.iter())
        .filter_map(|s| match s {
            Source::Event(id) | Source::ScopedEvent { sequence: id, .. } => Some(*id),
            _ => None,
        })
        .collect();
    for c in &events {
        check(cancel)?;
        if required_sources.contains(&c.revision) {
            mandatory
                .entry(c.key().into())
                .or_insert(Reason::SupportingEvidence);
        }
    }
    // Mandatory payloads always come from Engine. A verified packet touching
    // any mandatory/recent/supporting source is replaced as one complete unit.
    memory.replace_mandatory(&snapshot, request, &mut candidates, &mandatory, cancel)?;
    let mut package = ContextPackage {
        version: construction.version(),
        scope: request.scope.clone(),
        head: engine.revision(),
        revision: snapshot.revision(),
        historical: snapshot.revision() != engine.revision(),
        observer: request.observer.clone(),
        role: request.role,
        records: vec![Selected {
            id: if construction.is_current() {
                "rules:v2"
            } else {
                "rules:v1"
            }
            .into(),
            kind: Kind::Rules,
            source_revision: 0,
            sources: vec![Source::Seed(snapshot.seed().id.clone())],
            reason: Reason::Rules,
            score: 0,
            mandatory: true,
            payload: Payload::Rules {
                version: VERSION,
                profile: snapshot.seed().profile.clone(),
                policies: if construction.is_current() {
                    vec![
                    "Engine validates all typed consequences; input is intent, not truth.",
                    "KnownAsObserved is the observer's actual learned value, not hidden world truth.",
                    "Statements and subjective beliefs are not established facts.",
                    "Never infer an unobserved event or grant knowledge from inspection.",
                    "Use only supplied IDs; no invented powers, inventory or author authority.",
                ]
                } else {
                    vec![
                        "Engine validates all typed consequences; input is intent, not truth.",
                        "Statements and subjective beliefs are not established facts.",
                        "Never infer an unobserved event or grant knowledge from inspection.",
                        "Use only supplied IDs; no invented powers, inventory or author authority.",
                    ]
                },
            },
        }],
        diagnostics: Diagnostics {
            eligible_candidates: candidates.len(),
            omitted_eligible: 0,
            omissions: vec![],
            omissions_truncated: false,
        },
        serialized_bytes: 0,
        estimated_tokens: 0,
        token_accounting: "estimate_utf8_bytes_div_4_not_measured",
        reserved_tokens: b.reserved_tokens,
        unsupported: if construction.is_current() {
            vec![
                "Measured tokenizer/template/output fit",
                "Full alias registry",
                "SQLite FTS",
                "Embeddings",
                "Domain 2 method-v2 derived coverage",
            ]
        } else {
            vec![
                "Measured tokenizer/template/output fit",
                "Full alias registry",
                "SQLite FTS",
                "Summaries and invalidation",
                "Embeddings",
                "Branch-scoped derived caches",
            ]
        },
    };
    for c in &candidates {
        check(cancel)?;
        if let Some(reason) = mandatory.get(c.key()) {
            package.records.push(selected(c, *reason, 0, true));
        }
    }
    for actor in references.intersection(&known_actors) {
        check(cancel)?;
        if let Some(state) = snapshot.state().actors.get(actor) {
            package.records.push(Selected {
                id: format!("alias:{actor}"),
                kind: Kind::Alias,
                source_revision: 0,
                sources: vec![Source::Seed(snapshot.seed().id.clone())],
                reason: Reason::Referenced,
                score: 0,
                mandatory: true,
                payload: Payload::Alias {
                    actor: actor.clone(),
                    name: state.name.clone(),
                },
            });
        }
    }
    if !fits(&mut package, b, fit_basis)? {
        return Err(CompileError::MandatoryBudget);
    }
    let (unit_candidates, mut construction_diagnostics) = if construction.is_recent() {
        policy::transcript_candidates(&snapshot, request, candidates.len(), &mut row_bytes, cancel)?
    } else {
        (vec![], ConstructionDiagnostics::default())
    };
    if construction.is_recent() {
        package.diagnostics.eligible_candidates = package
            .diagnostics
            .eligible_candidates
            .checked_add(unit_candidates.len())
            .ok_or(CompileError::TooLarge)?;
    }
    let mandatory_sources = candidates
        .iter()
        .filter(|c| mandatory.contains_key(c.key()))
        .flat_map(|c| c.sources.iter())
        .filter_map(|s| match s {
            Source::ScopedEvent {
                original_scope,
                sequence,
            } => Some((original_scope.clone(), *sequence)),
            _ => None,
        })
        .collect::<BTreeSet<_>>();
    let mut optional: Vec<_> = candidates
        .iter()
        .chain(unit_candidates.iter())
        .filter(|c| !mandatory.contains_key(c.key()))
        .map(|c| {
            check(cancel)?;
            if construction.is_recent() {
                return match &c.payload {
                    CandidatePayload::Row(_)=>Ok((c,0,Reason::NotRelevant)),
                    CandidatePayload::TranscriptUnit(_)=>{
                        let overlap=c.sources.iter().any(|s|matches!(s,Source::ScopedEvent {original_scope,sequence} if mandatory_sources.contains(&(original_scope.clone(),*sequence))));
                        if overlap {construction_diagnostics.overlap_transcript_units+=1;Ok((c,0,Reason::AlreadySelected))}else{Ok((c,1,Reason::Recent))}
                    }
                };
            }
            let exact = c.ids.intersection(&references).count() as u32;
            let words = tokens(&format!("{} {}", c.encoded, c.row().map_or("transcript",tags)));
            let lexical = query_tokens.intersection(&words).count() as u32;
            let score = exact
                .saturating_mul(10000)
                .saturating_add(lexical.saturating_mul(10));
            let reason = if exact > 0 {
                Reason::ExactId
            } else if lexical > 0 {
                Reason::Lexical
            } else {
                Reason::NotRelevant
            };
            Ok((c, score, reason))
        })
        .collect::<Result<_, CompileError>>()?;
    check(cancel)?;
    optional.sort_by(|(a, sa, _), (b, sb, _)| {
        sb.cmp(sa)
            .then_with(|| b.revision.cmp(&a.revision))
            .then_with(|| a.key().cmp(b.key()))
    });
    let mut accepted = 0;
    for (c, score, reason) in optional {
        check(cancel)?;
        let omission = if score == 0 {
            Some(reason)
        } else if accepted >= b.optional_records {
            Some(Reason::OptionalLimit)
        } else {
            package.records.push(selected(c, reason, score, false));
            if fits(&mut package, b, fit_basis)? {
                accepted += 1;
                None
            } else {
                package.records.pop();
                Some(Reason::Budget)
            }
        };
        if let Some(reason) = omission {
            package.diagnostics.omitted_eligible += 1;
            if package.diagnostics.omissions.len() < MAX_DIAGNOSTICS {
                package.diagnostics.omissions.push(Omission {
                    id: c.key().into(),
                    reason,
                });
            } else {
                package.diagnostics.omissions_truncated = true;
            }
        }
    }
    // Diagnostics themselves consume budget. Drop their optional detail first, never mandatory facts.
    while !fits(&mut package, b, fit_basis)? {
        check(cancel)?;
        if package.diagnostics.omissions.pop().is_some() {
            package.diagnostics.omissions_truncated = true;
        } else if let Some(index) = package.records.iter().rposition(|r| !r.mandatory) {
            package.records.remove(index);
            package.diagnostics.omitted_eligible += 1;
            package.diagnostics.omissions_truncated = true;
        } else {
            return Err(CompileError::MandatoryBudget);
        }
    }
    if construction.is_recent() {
        // Admission retains newest fitting whole units. Presentation is chronological.
        let first = package
            .records
            .iter()
            .position(|r| !r.mandatory)
            .unwrap_or(package.records.len());
        package.records[first..].sort_by(|a, b| {
            a.source_revision
                .cmp(&b.source_revision)
                .then_with(|| a.id.cmp(&b.id))
        });
        if !fits(&mut package, b, fit_basis)? {
            return Err(CompileError::MandatoryBudget);
        }
        construction_diagnostics.selected_transcript_units = package
            .records
            .iter()
            .filter(|r| matches!(r.payload, Payload::TranscriptUnit(_)))
            .count();
    }
    check(cancel)?;
    Ok(CompilationResult {
        compilation: MemoryCompilation {
            package,
            coverage: memory.diagnostics,
        },
        construction: construction_diagnostics,
    })
}
