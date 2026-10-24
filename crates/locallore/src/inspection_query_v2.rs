//! Query2 presentation over actual Core actor-safe values, not another history.
use super::*;
use crate::author_correction::{ActorEventV2, ObservationSource};

struct ReadLens {
    base: Lens,
    events: Vec<ActorEventV2>,
    scopes: BTreeMap<u64, Scope>,
    player_history_markers: bool,
}
fn source(event: &AcceptedEvent) -> Source {
    Source::ScopedEvent {
        original_scope: event.scope().clone(),
        sequence: event.sequence(),
    }
}
fn core_error(error: Error) -> QueryError {
    match error {
        Error::Scope => QueryError::Scope,
        Error::Stale => QueryError::Stale,
        Error::UnknownReference => QueryError::UnknownObserver,
        Error::Version => QueryError::Version,
        _ => QueryError::Integrity,
    }
}
impl ReadLens {
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
        let events = if let Some(id) = &actor {
            engine
                .actor_receipts_v2(id, engine.scope(), engine.revision())
                .map_err(core_error)?
                .into_iter()
                .flat_map(|r| r.events)
                .collect::<Vec<_>>()
        } else {
            // Only a granted private lens enumerates ordinary events. Even this
            // does not serialize an author record or a private truth binding.
            let ordinary = engine
                .canonical_records()
                .iter()
                .filter_map(|r| r.receipt())
                .flat_map(Receipt::events)
                .collect::<Vec<_>>();
            let discoverers = ordinary
                .iter()
                .filter_map(|event| match event.outcome() {
                    Effect::Discovered { actor, .. } => Some(actor.clone()),
                    _ => None,
                })
                .collect::<BTreeSet<_>>();
            let mut discoveries = BTreeMap::new();
            for id in discoverers {
                engine
                    .visit_actor_observations_v2(
                        &id,
                        engine.scope(),
                        engine.revision(),
                        0,
                        engine.revision(),
                        &|| false,
                        &mut |event| {
                            if let Some(value) = &event.discovery {
                                discoveries.insert(event.event.sequence(), value.clone());
                            }
                            true
                        },
                    )
                    .map_err(core_error)?;
            }
            ordinary
                .into_iter()
                .map(|event| ActorEventV2 {
                    version: 2,
                    event: event.clone(),
                    discovery: discoveries.remove(&event.sequence()),
                })
                .collect()
        };
        if events.len() > MAX_HISTORY_RECEIPTS * MAX_COMMANDS {
            return Err(QueryError::TooLarge);
        }
        let scopes = events
            .iter()
            .map(|e| (e.event.sequence(), e.event.scope().clone()))
            .collect::<BTreeMap<_, _>>();
        if scopes.len() != events.len() {
            return Err(QueryError::Integrity);
        }
        Ok(Self {
            base: Lens {
                actor,
                visible: scopes.keys().copied().collect(),
                privacy,
            },
            events,
            scopes,
            player_history_markers: matches!(observer, Observer::Player),
        })
    }
    fn scoped(&self, value: &Source) -> Source {
        match value {
            Source::Event(sequence) => {
                self.scopes
                    .get(sequence)
                    .map_or(Source::Withheld, |scope| Source::ScopedEvent {
                        original_scope: scope.clone(),
                        sequence: *sequence,
                    })
            }
            Source::ScopedEvent {
                original_scope,
                sequence,
            } if self.scopes.get(sequence) != Some(original_scope) => Source::Withheld,
            _ => value.clone(),
        }
    }
    fn normalize(&self, row: &mut Row) {
        match row {
            Row::Clock { source, .. }
            | Row::Field { source, .. }
            | Row::Relationship { source, .. } => *source = self.scoped(source),
            Row::Knowledge { sources, .. }
            | Row::Promise { sources, .. }
            | Row::Provenance { sources, .. } => {
                sources.iter_mut().for_each(|s| *s = self.scoped(s))
            }
            Row::Change { before, after, .. } => {
                if let Some(r) = before {
                    self.normalize(r)
                }
                if let Some(r) = after {
                    self.normalize(r)
                }
            }
            _ => {}
        }
    }
}
fn event_row(event: &AcceptedEvent) -> Result<Row, QueryError> {
    #[derive(Deserialize)]
    struct Metadata {
        turn: String,
        story_time: u64,
        participants: BTreeSet<String>,
    }
    let metadata: Metadata =
        serde_json::from_value(serde_json::to_value(event).map_err(|_| QueryError::Integrity)?)
            .map_err(|_| QueryError::Integrity)?;
    Ok(Row::Event {
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
    })
}
fn profiles(engine: &Engine, lens: &ReadLens) -> Result<Vec<Row>, QueryError> {
    let ids: Vec<_> = lens.base.actor.as_ref().map_or_else(
        || engine.state().actors.keys().cloned().collect(),
        |id| vec![id.clone()],
    );
    let mut rows = vec![];
    for id in ids {
        let actor = engine
            .character_context_v2(&id, engine.scope(), engine.revision())
            .map_err(core_error)?
            .self_state;
        let mut add = |field: String, value: FieldValue, source_key: String| {
            rows.push(Row::Field {
                key: key(&["field", &id, &field]),
                actor: id.clone(),
                field,
                value,
                source: lens.scoped(&lens.base.field_source(engine, &source_key)),
                origin: ValueOrigin::CanonicalField,
            })
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
    Ok(rows)
}
fn knowledge(engine: &Engine, lens: &ReadLens) -> Result<Vec<Row>, QueryError> {
    let mut rows = vec![];
    if let Some(actor) = &lens.base.actor {
        for (id, value) in engine
            .observed_facts(actor, engine.scope(), engine.revision())
            .map_err(core_error)?
        {
            let observed = match value.observation {
                ObservationSource::SeedKnowledge { seed_id, .. } => Source::Seed(seed_id),
                ObservationSource::Event { source } => Source::ScopedEvent {
                    original_scope: source.original_scope,
                    sequence: source.sequence,
                },
            };
            rows.push(Row::Knowledge {
                key: key(&["observed", &id]),
                id,
                subject: Some(actor.clone()),
                text: value.proposition,
                confidence: None,
                sources: vec![observed],
                origin: ValueOrigin::KnownAsObserved,
            });
        }
    } else {
        for id in engine.seed().facts.keys() {
            // Query2 uses uniform withheld provenance in both domains so the
            // first author interval does not invent per-fact source-only diffs.
            let text = engine.effective_fact(id).map_err(core_error)?.proposition;
            rows.push(Row::Knowledge {
                key: key(&["truth", id]),
                id: id.clone(),
                subject: None,
                text,
                confidence: None,
                sources: vec![Source::Withheld],
                origin: ValueOrigin::CanonicalTruth,
            });
        }
    }
    for claim in engine
        .state()
        .claims
        .iter()
        .filter(|c| lens.base.sees(c.source))
    {
        rows.push(Row::Knowledge {
            key: key(&["statement", &claim.source.to_string()]),
            id: claim.source.to_string(),
            subject: Some(claim.speaker.clone()),
            text: claim.text.clone(),
            confidence: None,
            sources: vec![lens.scoped(&Source::Event(claim.source))],
            origin: ValueOrigin::RecordedStatement,
        });
    }
    for (index, belief) in engine
        .state()
        .beliefs
        .iter()
        .filter(|b| lens.base.actor.as_ref().is_none_or(|id| &b.believer == id))
        .enumerate()
    {
        let mut sources = vec![lens.scoped(&lens.base.source(&belief.source))];
        if let Some(id) = belief.source_claim {
            sources.push(lens.scoped(&lens.base.source(&Evidence::Event(id))));
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
    for value in &lens.events {
        if let Effect::Discovered { actor, fact } = value.event.outcome() {
            rows.push(Row::Knowledge {
                key: key(&["discovery", &value.event.sequence().to_string()]),
                id: fact.clone(),
                subject: Some(actor.clone()),
                text: value.discovery.as_ref().map_or_else(
                    || "Recorded discovery; proposition unavailable to this observer".into(),
                    |v| v.proposition.clone(),
                ),
                confidence: None,
                sources: vec![source(&value.event)],
                origin: ValueOrigin::RecordedDiscovery,
            });
        }
    }
    Ok(rows)
}
fn history(engine: &Engine, lens: &ReadLens) -> Result<Vec<Row>, QueryError> {
    let mut rows = lens
        .events
        .iter()
        .map(|e| event_row(&e.event))
        .collect::<Result<Vec<_>, _>>()?;
    if lens
        .base
        .actor
        .as_ref()
        .is_none_or(|id| id == &engine.seed().player)
    {
        for receipt in engine
            .canonical_records()
            .iter()
            .filter_map(|r| r.receipt())
        {
            if !receipt
                .events()
                .iter()
                .all(|e| lens.base.sees(e.sequence()))
            {
                continue;
            }
            let ids = receipt
                .events()
                .iter()
                .map(AcceptedEvent::sequence)
                .collect::<Vec<_>>();
            let input = match &receipt.request().intent {
                Intent::FreeText { text, .. } | Intent::Dialogue { text, .. } => {
                    Some(text.as_str())
                }
                _ => None,
            };
            for (kind, text) in input
                .map(|s| ("original_input", s))
                .into_iter()
                .chain(std::iter::once(("narration", receipt.narration())))
            {
                let sequence = if kind == "original_input" {
                    ids.first()
                } else {
                    ids.last()
                }
                .ok_or(QueryError::Integrity)?;
                rows.push(Row::ScopedMessage {
                    key: key(&[
                        "history",
                        &format!("{sequence:020}"),
                        if kind == "original_input" {
                            "0_input"
                        } else {
                            "narration"
                        },
                        &receipt.request().scope.story,
                        &receipt.request().scope.branch,
                        &receipt.request().turn,
                        kind,
                    ]),
                    turn: receipt.request().turn.clone(),
                    message_kind: kind.into(),
                    text: text.into(),
                    event_ids: ids.clone(),
                    origin: ValueOrigin::RecordedMessage,
                    original_scope: receipt.request().scope.clone(),
                });
            }
        }
    }
    if lens.player_history_markers {
        // The reconstructed snapshot already contains only the selected prefix.
        // Inspect just the closed kind/revision, never the private author payload.
        for record in engine.canonical_records() {
            if record.kind() == crate::author_correction::CanonicalRecordKind::AuthorCorrection {
                let revision = record.last_revision();
                rows.push(Row::AuthorCorrection {
                    key: key(&["history", &format!("{revision:020}"), "author_correction"]),
                    revision,
                });
            }
        }
    }
    Ok(rows)
}
fn rows(engine: &Engine, lens: &ReadLens, view: View) -> Result<Vec<Row>, QueryError> {
    let mut rows = match view {
        View::Profiles => profiles(engine, lens)?,
        View::Knowledge => knowledge(engine, lens)?,
        View::History => history(engine, lens)?,
        View::Relationships | View::Promises => collect(engine, &lens.base, view)?,
        View::Provenance => state_rows(engine, lens)?
            .into_iter()
            .map(|r| {
                let (origin, sources) = r.provenance();
                Row::Provenance {
                    key: r.key().into(),
                    sources,
                    origin,
                }
            })
            .collect(),
        _ => return Err(QueryError::InvalidRequest),
    };
    if rows.len() > MAX_CANDIDATES {
        return Err(QueryError::TooLarge);
    }
    for row in &mut rows {
        lens.normalize(row);
    }
    Ok(rows)
}
fn state_rows(engine: &Engine, lens: &ReadLens) -> Result<Vec<Row>, QueryError> {
    let latest = engine
        .canonical_records()
        .iter()
        .rev()
        .filter_map(|r| r.receipt())
        .flat_map(|r| r.events().iter().rev())
        .find(|e| matches!(e.outcome(), Effect::TimeAdvanced { .. }));
    let mut result = vec![Row::Clock {
        key: key(&["clock"]),
        story_time: engine.state().story_time,
        source: latest.map_or_else(
            || Source::Seed(engine.seed().id.clone()),
            |e| lens.scoped(&lens.base.source(&Evidence::Event(e.sequence()))),
        ),
        origin: ValueOrigin::CanonicalField,
    }];
    for view in [
        View::Profiles,
        View::Relationships,
        View::Knowledge,
        View::Promises,
    ] {
        result.extend(rows(engine, lens, view)?);
        if result.len() > MAX_CANDIDATES {
            return Err(QueryError::TooLarge);
        }
    }
    Ok(result)
}
pub(super) fn actor_rows(engine: &Engine, actor: &str, view: View) -> Result<Vec<Row>, QueryError> {
    if !matches!(
        view,
        View::Profiles | View::Knowledge | View::Relationships | View::Promises
    ) {
        return Err(QueryError::InvalidRequest);
    }
    let lens = ReadLens::new(engine, &Observer::Character { id: actor.into() }, true)?;
    rows(engine, &lens, view)
}
pub(super) fn query(engine: &Engine, request: &Query, grant: bool) -> Result<Page, QueryError> {
    if request.version != 2 {
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
    let lens = ReadLens::new(&snapshot, &request.observer, grant)?;
    let unsupported = matches!(request.view, View::Summaries | View::RetrievalIndexes);
    let mut output = if unsupported {
        vec![]
    } else if request.view == View::TurnDiff {
        let catalog = snapshot.completed_boundary_catalog();
        let index = catalog
            .boundaries
            .iter()
            .position(|r| *r == revision)
            .filter(|n| *n > 0)
            .ok_or(QueryError::InvalidBoundary)?;
        let before = at(&snapshot, catalog.boundaries[index - 1])?;
        let left_lens = ReadLens::new(&before, &request.observer, grant)?;
        let left = state_rows(&before, &left_lens)?
            .into_iter()
            .map(|r| (r.key().to_owned(), r))
            .collect::<BTreeMap<_, _>>();
        let right = state_rows(&snapshot, &lens)?
            .into_iter()
            .map(|r| (r.key().to_owned(), r))
            .collect::<BTreeMap<_, _>>();
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
        rows(&snapshot, &lens, request.view)?
    };
    if output.len() > MAX_CANDIDATES {
        return Err(QueryError::TooLarge);
    }
    output.sort_by(|a, b| a.key().cmp(b.key()));
    let search = request.search.to_lowercase();
    let mut matching = vec![];
    for row in output {
        let encoded = serde_json::to_vec(&row).map_err(|_| QueryError::Integrity)?;
        if encoded.len() > MAX_PAGE_BYTES - 4096 {
            return Err(QueryError::TooLarge);
        }
        if search.is_empty()
            || String::from_utf8_lossy(&encoded)
                .to_lowercase()
                .contains(&search)
        {
            matching.push((row, encoded));
        }
    }
    let mut identity = request.clone();
    identity.cursor = None;
    let mut binding = Sha256::new();
    binding.update(serde_json::to_vec(&identity).map_err(|_| QueryError::Integrity)?);
    for (_, encoded) in &matching {
        binding.update((encoded.len() as u64).to_le_bytes());
        binding.update(encoded);
    }
    let binding = binding.finalize();
    let cursor = |offset: usize| {
        let mut digest = Sha256::new();
        digest.update(binding);
        digest.update((offset as u64).to_le_bytes());
        format!("2:{offset}:{:x}", digest.finalize())
    };
    let offset = match &request.cursor {
        None => 0,
        Some(value) => {
            let mut parts = value.split(':');
            if parts.next() != Some("2") {
                return Err(QueryError::InvalidCursor);
            }
            let offset = parts
                .next()
                .and_then(|v| v.parse::<usize>().ok())
                .ok_or(QueryError::InvalidCursor)?;
            if offset == 0 || offset >= matching.len() || value != &cursor(offset) {
                return Err(QueryError::InvalidCursor);
            }
            offset
        }
    };
    let total = matching.len();
    let mut selected = vec![];
    let mut bytes = 0;
    for (row, encoded) in matching
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
        version: 2,
        scope: request.scope.clone(),
        head: engine.revision(),
        revision,
        story_time: snapshot.state().story_time,
        observer: request.observer.clone(),
        view: request.view,
        privacy: lens.base.privacy,
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
