//! Actor-only exact/lexical context. Reuses authoritative context and shared eligibility.
//! No native Host, database, tokenizer, summary or provider authority.
use crate::{
    contracts::{Effect, Profile, Scope, VERSION},
    engine::Engine,
    inspection_query::{self, FieldValue, Row, Source, ValueOrigin, View},
};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};

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
    row: Row,
    encoded: String,
    ids: BTreeSet<String>,
    kind: Kind,
    sources: Vec<Source>,
    revision: u64,
}
fn valid_id(id: &str) -> bool {
    !id.is_empty()
        && id.len() <= 64
        && id
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b"-_".contains(&b))
}
fn snapshot(engine: &Engine, request: &CompileRequest) -> Result<Engine, CompileError> {
    if request.version != COMPILER_VERSION {
        return Err(CompileError::Version);
    }
    if request.scope != *engine.scope() {
        return Err(CompileError::Scope);
    }
    if request.expected_head != engine.revision() {
        return Err(CompileError::Stale);
    }
    if engine.scope() != &engine.seed().scope {
        return Err(CompileError::UnsupportedBranch);
    }
    let revision = request.at_revision.unwrap_or(engine.revision());
    let snapshot = if revision == engine.revision() {
        engine.clone()
    } else {
        let count = if revision == 0 {
            0
        } else {
            engine
                .receipts()
                .iter()
                .position(|r| r.events().last().is_some_and(|e| e.sequence() == revision))
                .map(|i| i + 1)
                .ok_or(CompileError::Boundary)?
        };
        Engine::replay(engine.seed().clone(), &engine.receipts()[..count])
            .map_err(|_| CompileError::Source)?
    };
    if !valid_id(&request.observer)
        || !snapshot.state().actors.contains_key(&request.observer)
        || (request.role == Role::Director && request.observer != snapshot.seed().player)
    {
        return Err(CompileError::Observer);
    }
    Ok(snapshot)
}
fn actor_rows(engine: &Engine, observer: &str, view: View) -> Result<Vec<Row>, CompileError> {
    let rows = inspection_query::actor_context_rows(engine, observer, view)
        .map_err(|_| CompileError::Source)?;
    if rows.len() > MAX_CANDIDATES {
        return Err(CompileError::TooLarge);
    }
    Ok(rows)
}
fn row_info(row: &Row, revision: u64) -> (Kind, Vec<Source>, u64) {
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
                _ => Kind::Observation,
            },
            sources.clone(),
        ),
        Row::Event { event, .. } => (Kind::Observation, vec![Source::Event(event.sequence)]),
        Row::Relationship { source, .. } => (Kind::Relationship, vec![source.clone()]),
        Row::Promise { sources, .. } => (Kind::Commitment, sources.clone()),
        _ => (Kind::Observation, vec![]),
    };
    let source_revision = sources
        .iter()
        .filter_map(|s| {
            if let Source::Event(id) = s {
                Some(*id)
            } else {
                None
            }
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
        id: candidate.row.key().into(),
        kind: candidate.kind,
        source_revision: candidate.revision,
        sources: candidate.sources.clone(),
        reason,
        score,
        mandatory,
        payload: Payload::Record(Box::new(candidate.row.clone())),
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
fn fits(package: &mut ContextPackage, budget: Budget) -> Result<bool, CompileError> {
    measure(package)?;
    Ok(package.serialized_bytes <= budget.max_bytes
        && package
            .estimated_tokens
            .saturating_add(budget.reserved_tokens)
            <= budget.estimated_tokens
        && package.records.len() <= MAX_SELECTED)
}

pub fn compile(engine: &Engine, request: &CompileRequest) -> Result<ContextPackage, CompileError> {
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
    let snapshot = snapshot(engine, request)?;
    let context = snapshot
        .character_context(&request.observer, snapshot.scope(), snapshot.revision())
        .map_err(|_| CompileError::Observer)?;
    let mut rows = vec![];
    for view in [
        View::Profiles,
        View::Knowledge,
        View::Promises,
        View::Relationships,
    ] {
        rows.extend(actor_rows(&snapshot, &request.observer, view)?);
    }
    #[derive(Deserialize)]
    struct Metadata {
        turn: String,
        story_time: u64,
        participants: BTreeSet<String>,
    }
    // These events have ALREADY passed authoritative branch/time/witness eligibility.
    for event in &context.observations {
        let metadata: Metadata =
            serde_json::from_value(serde_json::to_value(event).map_err(|_| CompileError::Source)?)
                .map_err(|_| CompileError::Source)?;
        rows.push(Row::Event {
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
        });
    }
    if rows.len() > MAX_CANDIDATES {
        return Err(CompileError::TooLarge);
    }
    rows.sort_by(|a, b| a.key().cmp(b.key()));
    let mut candidates = vec![];
    let mut known = BTreeSet::new();
    let mut known_actors = BTreeSet::new();
    let mut bytes = 0usize;
    for row in rows {
        let encoded = serde_json::to_string(&row).map_err(|_| CompileError::Source)?;
        bytes = bytes.saturating_add(encoded.len());
        if bytes > MAX_CANDIDATE_BYTES {
            return Err(CompileError::TooLarge);
        }
        let (ids, actors) = identifiers(&row);
        known.extend(ids.iter().cloned());
        known_actors.extend(actors);
        let (kind, sources, revision) = row_info(&row, snapshot.revision());
        candidates.push(Candidate {
            row,
            encoded,
            ids,
            kind,
            sources,
            revision,
        });
    }
    // Current canonical display names of ALREADY eligible actor IDs only, not a global alias scan.
    if known_actors.len() > 256 {
        return Err(CompileError::TooLarge);
    }
    let mut aliases: BTreeMap<String, BTreeSet<String>> = BTreeMap::new();
    for actor in &known_actors {
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
        let reason = match &c.row {
            Row::Field { .. } => Some(Reason::CurrentState),
            Row::Knowledge {
                origin: ValueOrigin::CanonicalTruth,
                ..
            } => Some(Reason::KnownTruth),
            Row::Knowledge {
                origin: ValueOrigin::SubjectiveBelief,
                ..
            } => Some(Reason::CurrentBelief),
            Row::Promise { status, .. } if status != "fulfilled" => Some(Reason::OpenCommitment),
            Row::Relationship { .. } => Some(Reason::Relationship),
            _ => None,
        };
        if let Some(reason) = reason {
            mandatory.insert(c.row.key().into(), reason);
        }
    }
    let mut events: Vec<_> = candidates
        .iter()
        .filter(|c| matches!(c.row, Row::Event { .. }))
        .collect();
    events.sort_by_key(|c| c.revision);
    for c in events.iter().rev().take(usize::from(b.recent_events)) {
        mandatory
            .entry(c.row.key().into())
            .or_insert(Reason::Recent);
    }
    for id in &references {
        if let Some(c) = events.iter().rev().find(|c| c.ids.contains(id)) {
            mandatory
                .entry(c.row.key().into())
                .or_insert(Reason::Referenced);
        }
    }
    let required_sources: BTreeSet<_> = candidates
        .iter()
        .filter(|c| mandatory.contains_key(c.row.key()))
        .flat_map(|c| c.sources.iter())
        .filter_map(|s| {
            if let Source::Event(id) = s {
                Some(*id)
            } else {
                None
            }
        })
        .collect();
    for c in &events {
        if required_sources.contains(&c.revision) {
            mandatory
                .entry(c.row.key().into())
                .or_insert(Reason::SupportingEvidence);
        }
    }
    let mut package = ContextPackage {
        version: COMPILER_VERSION,
        scope: request.scope.clone(),
        head: engine.revision(),
        revision: snapshot.revision(),
        historical: snapshot.revision() != engine.revision(),
        observer: request.observer.clone(),
        role: request.role,
        records: vec![Selected {
            id: "rules:v1".into(),
            kind: Kind::Rules,
            source_revision: 0,
            sources: vec![Source::Seed(snapshot.seed().id.clone())],
            reason: Reason::Rules,
            score: 0,
            mandatory: true,
            payload: Payload::Rules {
                version: VERSION,
                profile: snapshot.seed().profile.clone(),
                policies: vec![
                    "Engine validates all typed consequences; input is intent, not truth.",
                    "Statements and subjective beliefs are not established facts.",
                    "Never infer an unobserved event or grant knowledge from inspection.",
                    "Use only supplied IDs; no invented powers, inventory or author authority.",
                ],
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
        unsupported: vec![
            "Measured tokenizer/template/output fit",
            "Full alias registry",
            "SQLite FTS",
            "Summaries and invalidation",
            "Embeddings",
            "Durable branch history",
        ],
    };
    for c in &candidates {
        if let Some(reason) = mandatory.get(c.row.key()) {
            package.records.push(selected(c, *reason, 0, true));
        }
    }
    for actor in references.intersection(&known_actors) {
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
    if !fits(&mut package, b)? {
        return Err(CompileError::MandatoryBudget);
    }
    let mut optional: Vec<_> = candidates
        .iter()
        .filter(|c| !mandatory.contains_key(c.row.key()))
        .map(|c| {
            let exact = c.ids.intersection(&references).count() as u32;
            let words = tokens(&format!("{} {}", c.encoded, tags(&c.row)));
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
            (c, score, reason)
        })
        .collect();
    optional.sort_by(|(a, sa, _), (b, sb, _)| {
        sb.cmp(sa)
            .then_with(|| b.revision.cmp(&a.revision))
            .then_with(|| a.row.key().cmp(b.row.key()))
    });
    let mut accepted = 0;
    for (c, score, reason) in optional {
        let omission = if score == 0 {
            Some(Reason::NotRelevant)
        } else if accepted >= b.optional_records {
            Some(Reason::OptionalLimit)
        } else {
            package.records.push(selected(c, reason, score, false));
            if fits(&mut package, b)? {
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
                    id: c.row.key().into(),
                    reason,
                });
            } else {
                package.diagnostics.omissions_truncated = true;
            }
        }
    }
    // Diagnostics themselves consume budget. Drop their optional detail first, never mandatory facts.
    while !fits(&mut package, b)? {
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
    Ok(package)
}
