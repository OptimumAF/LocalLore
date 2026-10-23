//! Read-only eligibility over an immutable validated scoped Engine and its lineage.
//! Shared views and an internal actor-context port never establish canonical knowledge.
use crate::{contracts::*, engine::Engine};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};

pub const QUERY_VERSION: u16 = 1;
pub const MAX_ROWS: u16 = 64;
pub const MAX_SEARCH_BYTES: usize = 256;
pub const MAX_CURSOR_BYTES: usize = 128;
pub const MAX_PAGE_BYTES: usize = 65_536;
const MAX_CANDIDATES: usize = 65_536;

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
#[cfg_attr(feature = "host", derive(schemars::JsonSchema))]
pub enum Observer {
    Player,
    Character { id: String },
    Omniscient,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[cfg_attr(feature = "host", derive(schemars::JsonSchema))]
pub enum View {
    Profiles,
    History,
    Relationships,
    Knowledge,
    Promises,
    Provenance,
    TurnDiff,
    Summaries,
    RetrievalIndexes,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
#[cfg_attr(feature = "host", derive(schemars::JsonSchema))]
pub struct Query {
    pub version: u16,
    pub scope: Scope,
    /// Current authoritative head, even when inspecting a historical completed turn.
    pub expected_head: u64,
    pub at_revision: Option<u64>,
    pub observer: Observer,
    pub view: View,
    pub cursor: Option<String>,
    pub limit: u16,
    /// Literal case-insensitive substring of eligible serialized rows; not SQL/FTS syntax.
    pub search: String,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum QueryError {
    Version,
    Scope,
    Stale,
    Forbidden,
    UnknownObserver,
    InvalidBoundary,
    InvalidCursor,
    InvalidRequest,
    TooLarge,
    UnsupportedBranch,
    Integrity,
}
impl std::fmt::Display for QueryError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{self:?}")
    }
}
impl std::error::Error for QueryError {}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum Privacy {
    PlayerVisible,
    PrivateCharacter,
    PrivateOmniscient,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ViewStatus {
    Supported,
    Unsupported,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
#[serde(tag = "kind", content = "value", rename_all = "snake_case")]
pub enum Source {
    Seed(String),
    Event(u64),
    /// Existing context permits the value, but its latest supporting event is not visible.
    Withheld,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ValueOrigin {
    CanonicalField,
    CanonicalTruth,
    RecordedStatement,
    SubjectiveBelief,
    RecordedDiscovery,
    RecordedObservation,
    RecordedMessage,
    DerivedComparison,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
#[serde(tag = "type", content = "value", rename_all = "snake_case")]
pub enum FieldValue {
    Text(String),
    Bool(bool),
    Number(i64),
    Texts(BTreeSet<String>),
    Item(Item),
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct EventRow {
    pub sequence: u64,
    pub scope: Scope,
    pub turn: String,
    pub story_time: u64,
    pub participants: BTreeSet<String>,
    pub witnesses: BTreeSet<String>,
    pub consequence: Effect,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum Row {
    Clock {
        key: String,
        story_time: u64,
        source: Source,
        origin: ValueOrigin,
    },
    Field {
        key: String,
        actor: String,
        field: String,
        value: FieldValue,
        source: Source,
        origin: ValueOrigin,
    },
    Event {
        key: String,
        event: EventRow,
        origin: ValueOrigin,
    },
    Message {
        key: String,
        turn: String,
        message_kind: String,
        text: String,
        event_ids: Vec<u64>,
        origin: ValueOrigin,
    },
    Relationship {
        key: String,
        from: String,
        to: String,
        dimension: String,
        value: i16,
        source: Source,
        origin: ValueOrigin,
    },
    Knowledge {
        key: String,
        id: String,
        subject: Option<String>,
        text: String,
        confidence: Option<Confidence>,
        sources: Vec<Source>,
        origin: ValueOrigin,
    },
    Promise {
        key: String,
        id: String,
        from: String,
        to: String,
        terms: String,
        deadline: u64,
        status: String,
        return_item: Option<String>,
        sources: Vec<Source>,
        origin: ValueOrigin,
    },
    Provenance {
        key: String,
        sources: Vec<Source>,
        origin: ValueOrigin,
    },
    Change {
        key: String,
        before_revision: u64,
        after_revision: u64,
        before: Option<Box<Row>>,
        after: Option<Box<Row>>,
        origin: ValueOrigin,
    },
}
impl Row {
    pub fn key(&self) -> &str {
        match self {
            Self::Clock { key, .. }
            | Self::Field { key, .. }
            | Self::Event { key, .. }
            | Self::Message { key, .. }
            | Self::Relationship { key, .. }
            | Self::Knowledge { key, .. }
            | Self::Promise { key, .. }
            | Self::Provenance { key, .. }
            | Self::Change { key, .. } => key,
        }
    }
    fn provenance(&self) -> (ValueOrigin, Vec<Source>) {
        match self {
            Self::Clock { origin, source, .. }
            | Self::Field { origin, source, .. }
            | Self::Relationship { origin, source, .. } => (*origin, vec![source.clone()]),
            Self::Knowledge {
                origin, sources, ..
            }
            | Self::Promise {
                origin, sources, ..
            }
            | Self::Provenance {
                origin, sources, ..
            } => (*origin, sources.clone()),
            _ => (ValueOrigin::DerivedComparison, vec![]),
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct Page {
    pub version: u16,
    pub scope: Scope,
    pub head: u64,
    pub revision: u64,
    pub story_time: u64,
    pub observer: Observer,
    pub view: View,
    pub privacy: Privacy,
    pub status: ViewStatus,
    /// Matching eligible rows only. Hidden rows never enter search, count or pagination.
    pub total: usize,
    pub rows: Vec<Row>,
    pub next_cursor: Option<String>,
    pub unsupported: Vec<String>,
}

struct Lens {
    actor: Option<String>,
    visible: BTreeSet<u64>,
    privacy: Privacy,
}
impl Lens {
    fn new(engine: &Engine, observer: &Observer, grant: bool) -> Result<Self, QueryError> {
        let (actor, privacy) = match observer {
            Observer::Player => (Some(engine.seed().player.clone()), Privacy::PlayerVisible),
            Observer::Character { id } => {
                if id != &engine.seed().player && !grant {
                    return Err(QueryError::Forbidden);
                }
                if !engine.state().actors.contains_key(id) {
                    return Err(QueryError::UnknownObserver);
                }
                (Some(id.clone()), Privacy::PrivateCharacter)
            }
            Observer::Omniscient if grant => (None, Privacy::PrivateOmniscient),
            Observer::Omniscient => return Err(QueryError::Forbidden),
        };
        let visible = if let Some(id) = &actor {
            engine
                .character_context(id, engine.scope(), engine.revision())
                .map_err(|_| QueryError::UnknownObserver)?
                .observations
                .iter()
                .map(AcceptedEvent::sequence)
                .collect()
        } else {
            engine
                .receipts()
                .iter()
                .flat_map(Receipt::events)
                .map(AcceptedEvent::sequence)
                .collect()
        };
        Ok(Self {
            actor,
            visible,
            privacy,
        })
    }
    fn sees(&self, sequence: u64) -> bool {
        self.visible.contains(&sequence)
    }
    fn source(&self, evidence: &Evidence) -> Source {
        match evidence {
            Evidence::Seed(id) => Source::Seed(id.clone()),
            Evidence::Event(id) if self.sees(*id) => Source::Event(*id),
            Evidence::Event(_) => Source::Withheld,
        }
    }
    fn field_source(&self, engine: &Engine, field: &str) -> Source {
        engine.state().progression_sources.get(field).map_or_else(
            || Source::Seed(engine.seed().id.clone()),
            |id| self.source(&Evidence::Event(*id)),
        )
    }
}

fn key(parts: &[&str]) -> String {
    // JSON tuple encoding avoids ambiguous field/key concatenation.
    serde_json::to_string(parts).expect("string slice is serializable")
}
fn at(engine: &Engine, revision: u64) -> Result<Engine, QueryError> {
    engine.at_revision(revision).map_err(|error| match error {
        crate::contracts::Error::Rule => QueryError::InvalidBoundary,
        _ => QueryError::Integrity,
    })
}

/// `story_lab_granted` must come from trusted native construction, never request JSON.
/// Cursors detect accidental/stale/cross-query edits; they are not authentication tokens.
pub fn query(
    engine: &Engine,
    request: &Query,
    story_lab_granted: bool,
) -> Result<Page, QueryError> {
    if request.version != QUERY_VERSION {
        return Err(QueryError::Version);
    }
    if &request.scope != engine.scope() {
        return Err(QueryError::Scope);
    }
    if request.expected_head != engine.revision() {
        return Err(QueryError::Stale);
    }
    if request.limit == 0 || request.limit > MAX_ROWS || request.search.len() > MAX_SEARCH_BYTES {
        return Err(QueryError::TooLarge);
    }
    if request.search.chars().any(char::is_control) {
        return Err(QueryError::InvalidRequest);
    }
    if request
        .cursor
        .as_ref()
        .is_some_and(|s| s.len() > MAX_CURSOR_BYTES)
    {
        return Err(QueryError::InvalidCursor);
    }
    let revision = request.at_revision.unwrap_or(engine.revision());
    let snapshot = at(engine, revision)?;
    let lens = Lens::new(&snapshot, &request.observer, story_lab_granted)?;
    let unsupported = matches!(request.view, View::Summaries | View::RetrievalIndexes);
    let mut rows = if unsupported {
        vec![]
    } else if request.view == View::TurnDiff {
        let turn = snapshot
            .receipts()
            .last()
            .ok_or(QueryError::InvalidBoundary)?;
        let before = at(&snapshot, turn.request().expected_revision)?;
        let before_lens = Lens::new(&before, &request.observer, story_lab_granted)?;
        let left: BTreeMap<_, _> = state_rows(&before, &before_lens)?
            .into_iter()
            .map(|r| (r.key().to_owned(), r))
            .collect();
        let right: BTreeMap<_, _> = state_rows(&snapshot, &lens)?
            .into_iter()
            .map(|r| (r.key().to_owned(), r))
            .collect();
        left.keys()
            .chain(right.keys())
            .collect::<BTreeSet<_>>()
            .into_iter()
            .filter(|k| left.get(*k) != right.get(*k))
            .map(|k| Row::Change {
                key: k.clone(),
                before_revision: before.revision(),
                after_revision: revision,
                before: left.get(k).cloned().map(Box::new),
                after: right.get(k).cloned().map(Box::new),
                origin: ValueOrigin::DerivedComparison,
            })
            .collect()
    } else {
        collect(&snapshot, &lens, request.view)?
    };
    if rows.len() > MAX_CANDIDATES {
        return Err(QueryError::TooLarge);
    }
    rows.sort_by(|a, b| a.key().cmp(b.key()));
    let search = request.search.to_lowercase();
    // Eligibility has already been applied. Never search or count canonical raw state first.
    let mut matches = Vec::new();
    for row in rows {
        let encoded = serde_json::to_vec(&row).map_err(|_| QueryError::Integrity)?;
        if encoded.len() > MAX_PAGE_BYTES - 4096 {
            return Err(QueryError::TooLarge);
        }
        if search.is_empty()
            || String::from_utf8_lossy(&encoded)
                .to_lowercase()
                .contains(&search)
        {
            matches.push((row, encoded));
        }
    }
    let mut identity = request.clone();
    identity.cursor = None;
    let mut binding = Sha256::new();
    binding.update(serde_json::to_vec(&identity).map_err(|_| QueryError::Integrity)?);
    for (_, encoded) in &matches {
        binding.update((encoded.len() as u64).to_le_bytes());
        binding.update(encoded);
    }
    let binding = binding.finalize();
    let cursor = |offset: usize| {
        let mut digest = Sha256::new();
        digest.update(binding);
        digest.update((offset as u64).to_le_bytes());
        format!("1:{offset}:{:x}", digest.finalize())
    };
    let offset = match &request.cursor {
        None => 0,
        Some(value) => {
            let mut parts = value.split(':');
            if parts.next() != Some("1") {
                return Err(QueryError::InvalidCursor);
            }
            let offset = parts
                .next()
                .and_then(|s| s.parse::<usize>().ok())
                .ok_or(QueryError::InvalidCursor)?;
            if offset == 0 || offset >= matches.len() || value != &cursor(offset) {
                return Err(QueryError::InvalidCursor);
            }
            offset
        }
    };
    let total = matches.len();
    let mut selected = vec![];
    let mut bytes = 0;
    for (row, encoded) in matches
        .into_iter()
        .skip(offset)
        .take(request.limit as usize)
    {
        if bytes + encoded.len() > MAX_PAGE_BYTES - 4096 {
            break;
        }
        bytes += encoded.len();
        selected.push(row);
    }
    let next = offset + selected.len();
    let page = Page {
        version: QUERY_VERSION,
        scope: request.scope.clone(),
        head: engine.revision(),
        revision,
        story_time: snapshot.state().story_time,
        observer: request.observer.clone(),
        view: request.view,
        privacy: lens.privacy,
        status: if unsupported {
            ViewStatus::Unsupported
        } else {
            ViewStatus::Supported
        },
        total,
        rows: selected,
        next_cursor: (next < total).then(|| cursor(next)),
        unsupported: if unsupported {
            vec!["Shared summaries/retrieval indexes are not implemented".into()]
        } else {
            vec!["Aliases, motivations, background and additional relationship dimensions have no shared fields".into()]
        },
    };
    if serde_json::to_vec(&page)
        .map_err(|_| QueryError::Integrity)?
        .len()
        > MAX_PAGE_BYTES
    {
        return Err(QueryError::TooLarge);
    }
    Ok(page)
}

/// Internal generation port: the exact actor lens shared with inspection, without
/// any inspection privilege argument or raw Player/narrator transcript rows.
/// The caller supplies an already validated coherent snapshot/current actor.
pub(crate) fn actor_context_rows(
    engine: &Engine,
    actor: &str,
    view: View,
) -> Result<Vec<Row>, QueryError> {
    if !matches!(
        view,
        View::Profiles | View::Knowledge | View::Relationships | View::Promises
    ) {
        return Err(QueryError::InvalidRequest);
    }
    let lens = Lens::new(engine, &Observer::Character { id: actor.into() }, true)?;
    let rows = collect(engine, &lens, view)?;
    if rows.len() > MAX_CANDIDATES {
        return Err(QueryError::TooLarge);
    }
    Ok(rows)
}

fn state_rows(engine: &Engine, lens: &Lens) -> Result<Vec<Row>, QueryError> {
    let latest_clock = engine
        .receipts()
        .iter()
        .rev()
        .flat_map(|r| r.events().iter().rev())
        .find(|e| matches!(e.outcome(), Effect::TimeAdvanced { .. }));
    let mut rows = vec![Row::Clock {
        key: key(&["clock"]),
        story_time: engine.state().story_time,
        source: latest_clock.map_or_else(
            || Source::Seed(engine.seed().id.clone()),
            |e| lens.source(&Evidence::Event(e.sequence())),
        ),
        origin: ValueOrigin::CanonicalField,
    }];
    for view in [
        View::Profiles,
        View::Relationships,
        View::Knowledge,
        View::Promises,
    ] {
        rows.extend(collect(engine, lens, view)?);
        if rows.len() > MAX_CANDIDATES {
            return Err(QueryError::TooLarge);
        }
    }
    Ok(rows)
}
fn collect(engine: &Engine, lens: &Lens, view: View) -> Result<Vec<Row>, QueryError> {
    let mut rows = vec![];
    match view {
        View::Profiles => {
            let actors: Vec<_> = lens.actor.as_ref().map_or_else(
                || engine.state().actors.keys().cloned().collect(),
                |id| vec![id.clone()],
            );
            for id in actors {
                // Even the Lab's all-actor profile table reads each actor's own context.
                let actor = engine
                    .character_context(&id, engine.scope(), engine.revision())
                    .map_err(|_| QueryError::UnknownObserver)?
                    .self_state;
                let mut add = |field: String, value: FieldValue, source_key: String| {
                    rows.push(Row::Field {
                        key: key(&["field", &id, &field]),
                        actor: id.clone(),
                        field,
                        value,
                        source: lens.field_source(engine, &source_key),
                        origin: ValueOrigin::CanonicalField,
                    });
                };
                add("name".into(), FieldValue::Text(actor.name), String::new());
                add(
                    "location".into(),
                    FieldValue::Text(actor.location),
                    format!("location:{id}"),
                );
                add("alive".into(), FieldValue::Bool(actor.alive), String::new());
                if engine.seed().profile == Profile::FantasyV1 {
                    add(
                        "energy".into(),
                        FieldValue::Number(actor.energy.into()),
                        format!("energy:{id}"),
                    );
                }
                add(
                    "injuries".into(),
                    FieldValue::Texts(actor.injuries),
                    format!("injuries:{id}"),
                );
                add(
                    "affiliations".into(),
                    FieldValue::Texts(actor.affiliations),
                    String::new(),
                );
                add(
                    "goals".into(),
                    FieldValue::Texts(actor.goals),
                    String::new(),
                );
                for (ability, rank) in actor.abilities {
                    add(
                        format!("ability/{ability}"),
                        FieldValue::Number(rank.into()),
                        format!("ability:{id}:{ability}"),
                    );
                }
                for (attribute, value) in actor.attributes {
                    add(
                        format!("attribute/{attribute}"),
                        FieldValue::Number(value.into()),
                        String::new(),
                    );
                }
                for (item, value) in engine
                    .state()
                    .items
                    .iter()
                    .filter(|(_, item)| item.owner == id)
                {
                    add(
                        format!("item/{item}"),
                        FieldValue::Item(value.clone()),
                        format!("item:{item}"),
                    );
                }
            }
        }
        View::Relationships => {
            for edge in engine
                .state()
                .relationships
                .iter()
                .filter(|edge| lens.actor.as_ref().is_none_or(|id| &edge.from == id))
            {
                for (dimension, value) in [
                    ("respect", edge.respect),
                    ("trust", edge.trust),
                    ("obligation", edge.obligation),
                ] {
                    rows.push(Row::Relationship {
                        key: key(&["relationship", &edge.from, &edge.to, dimension]),
                        from: edge.from.clone(),
                        to: edge.to.clone(),
                        dimension: dimension.into(),
                        value,
                        source: lens.field_source(
                            engine,
                            &format!("relationship:{}:{}:{dimension}", edge.from, edge.to),
                        ),
                        origin: ValueOrigin::CanonicalField,
                    });
                }
            }
        }
        View::Knowledge => knowledge_rows(engine, lens, &mut rows)?,
        View::Promises => {
            for (id, promise) in &engine.state().commitments {
                if let Some(observer) = &lens.actor {
                    let incoming_visible = &promise.to == observer
                        && matches!(promise.source, Evidence::Event(id) if lens.sees(id));
                    if &promise.from != observer && !incoming_visible {
                        continue;
                    }
                }
                let mut visible_promise = promise.clone();
                visible_promise.completed_by = promise.completed_by.filter(|id| lens.sees(*id));
                let mut sources = vec![lens.source(&promise.source)];
                if let Some(id) = visible_promise.completed_by {
                    sources.push(lens.source(&Evidence::Event(id)));
                }
                rows.push(Row::Promise {
                    key: key(&["promise", id]),
                    id: id.clone(),
                    from: promise.from.clone(),
                    to: promise.to.clone(),
                    terms: promise.terms.clone(),
                    deadline: promise.deadline,
                    status: visible_promise.status(engine.state().story_time).into(),
                    return_item: promise.return_item.clone(),
                    sources,
                    origin: ValueOrigin::DerivedComparison,
                });
            }
        }
        View::History => {
            #[derive(Deserialize)]
            struct Metadata {
                turn: String,
                story_time: u64,
                participants: BTreeSet<String>,
            }
            for receipt in engine.receipts() {
                for event in receipt.events().iter().filter(|e| lens.sees(e.sequence())) {
                    let metadata: Metadata = serde_json::from_value(
                        serde_json::to_value(event).map_err(|_| QueryError::Integrity)?,
                    )
                    .map_err(|_| QueryError::Integrity)?;
                    rows.push(Row::Event {
                        key: key(&["history", &format!("{:020}", event.sequence()), "event"]),
                        event: EventRow {
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
                // A witnessed effect does not disclose the player's private input or
                // narrator display prose. Spoken words remain in witnessed Say events.
                let player_display = lens
                    .actor
                    .as_ref()
                    .is_none_or(|id| id == &engine.seed().player);
                if player_display && receipt.events().iter().all(|e| lens.sees(e.sequence())) {
                    let turn = &receipt.request().turn;
                    let events = receipt
                        .events()
                        .iter()
                        .map(AcceptedEvent::sequence)
                        .collect::<Vec<_>>();
                    let input = match &receipt.request().intent {
                        Intent::FreeText { text, .. } | Intent::Dialogue { text, .. } => Some(text),
                        _ => None,
                    };
                    for (kind, text) in input
                        .map(|s| ("original_input", s.as_str()))
                        .into_iter()
                        .chain(std::iter::once(("narration", receipt.narration())))
                    {
                        let sequence = if kind == "original_input" {
                            events.first()
                        } else {
                            events.last()
                        }
                        .ok_or(QueryError::Integrity)?;
                        rows.push(Row::Message {
                            key: key(&[
                                "history",
                                &format!("{sequence:020}"),
                                if kind == "original_input" {
                                    "0_input"
                                } else {
                                    "narration"
                                },
                            ]),
                            turn: turn.clone(),
                            message_kind: kind.into(),
                            text: text.into(),
                            event_ids: events.clone(),
                            origin: ValueOrigin::RecordedMessage,
                        });
                    }
                }
            }
        }
        View::Provenance => {
            rows = state_rows(engine, lens)?
                .into_iter()
                .map(|row| {
                    let (origin, sources) = row.provenance();
                    Row::Provenance {
                        key: row.key().to_owned(),
                        sources,
                        origin,
                    }
                })
                .collect();
        }
        _ => return Err(QueryError::InvalidRequest),
    }
    if rows.len() > MAX_CANDIDATES {
        return Err(QueryError::TooLarge);
    }
    Ok(rows)
}

fn knowledge_rows(engine: &Engine, lens: &Lens, rows: &mut Vec<Row>) -> Result<(), QueryError> {
    let context = lens
        .actor
        .as_ref()
        .map(|id| engine.character_context(id, engine.scope(), engine.revision()))
        .transpose()
        .map_err(|_| QueryError::UnknownObserver)?;
    for (id, fact) in &engine.seed().facts {
        if context.as_ref().is_some_and(|c| !c.facts.contains_key(id)) {
            continue;
        }
        let discovery = engine
            .receipts()
            .iter()
            .flat_map(Receipt::events)
            .find(|e| {
                lens.sees(e.sequence())
                    && matches!(e.outcome(), Effect::Discovered { actor, fact }
                if fact == id && lens.actor.as_ref().is_none_or(|observer| observer == actor))
            });
        let mut sources = vec![Source::Seed(engine.seed().id.clone())];
        if let Some(event) = discovery {
            sources.push(Source::Event(event.sequence()));
        }
        rows.push(Row::Knowledge {
            key: key(&["truth", id]),
            id: id.clone(),
            subject: None,
            text: fact.proposition.clone(),
            confidence: None,
            sources,
            origin: ValueOrigin::CanonicalTruth,
        });
    }
    for claim in engine.state().claims.iter().filter(|c| lens.sees(c.source)) {
        rows.push(Row::Knowledge {
            key: key(&["statement", &claim.source.to_string()]),
            id: claim.source.to_string(),
            subject: Some(claim.speaker.clone()),
            text: claim.text.clone(),
            confidence: None,
            sources: vec![Source::Event(claim.source)],
            origin: ValueOrigin::RecordedStatement,
        });
    }
    for (index, belief) in engine
        .state()
        .beliefs
        .iter()
        .filter(|b| lens.actor.as_ref().is_none_or(|id| &b.believer == id))
        .enumerate()
    {
        let mut sources = vec![lens.source(&belief.source)];
        if let Some(id) = belief.source_claim {
            sources.push(lens.source(&Evidence::Event(id)));
        }
        rows.push(Row::Knowledge {
            key: key(&["belief", &belief.believer, &index.to_string()]),
            id: index.to_string(),
            subject: Some(belief.believer.clone()),
            text: belief.proposition.clone(),
            confidence: Some(belief.confidence.clone()),
            sources,
            origin: ValueOrigin::SubjectiveBelief,
        });
    }
    for event in engine
        .receipts()
        .iter()
        .flat_map(Receipt::events)
        .filter(|e| lens.sees(e.sequence()))
    {
        if let Effect::Discovered { actor, fact } = event.outcome() {
            rows.push(Row::Knowledge {
                key: key(&["discovery", &event.sequence().to_string()]),
                id: fact.clone(),
                subject: Some(actor.clone()),
                text: "Recorded discovery event; consult the scoped truth row for its proposition"
                    .into(),
                confidence: None,
                sources: vec![Source::Event(event.sequence())],
                origin: ValueOrigin::RecordedDiscovery,
            });
        }
    }
    Ok(())
}
