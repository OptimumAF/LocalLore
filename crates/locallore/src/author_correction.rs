// Native pure authoring and actor-safe observations. No Store or wire authority.
use super::*;
use serde::ser::SerializeMap;

pub const AUTHOR_TURN_KEY: &str = "author-correction-v1";
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct AuthorCorrectionInputV1 {
    pub version: u16,
    pub parent: Scope,
    pub expected_parent_revision: u64,
    pub fork_revision: u64,
    pub child_branch: String,
    pub operation: AuthorCorrectionOperationV1,
    pub reason: String,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
#[serde(tag = "op", rename_all = "snake_case")]
pub enum AuthorCorrectionOperationV1 {
    ReplaceFactProposition {
        fact: String,
        expected_proposition: String,
        replacement: String,
    },
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct EventRef {
    pub original_scope: Scope,
    pub sequence: u64,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
enum TruthSource {
    SeedFact { seed_id: String, fact: String },
    Author { source: EventRef },
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
struct ObservationBinding {
    event: EventRef,
    actor: String,
    fact: String,
    truth: TruthSource,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CanonicalPlayV2 {
    receipt: Receipt,
    observations: Vec<ObservationBinding>,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
enum AuthorPolicyV1 {
    ReplaceExistingFactPropositionV1,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct AuthorCorrectionReceiptV1 {
    version: u16,
    policy: AuthorPolicyV1,
    scope: Scope,
    sequence: u64,
    rules: Profile,
    seed: String,
    story_time: u64,
    witnesses: BTreeSet<String>,
    input: AuthorCorrectionInputV1,
    before: TruthSource,
}
impl AuthorCorrectionReceiptV1 {
    pub fn input(&self) -> &AuthorCorrectionInputV1 {
        &self.input
    }
    pub fn scope(&self) -> &Scope {
        &self.scope
    }
    pub fn sequence(&self) -> u64 {
        self.sequence
    }
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum CanonicalRecord {
    LegacyPlay(Receipt),
    PlayV2(CanonicalPlayV2),
    AuthorV1(AuthorCorrectionReceiptV1),
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CanonicalRecordKind {
    LegacyPlay,
    PlayV2,
    AuthorCorrection,
}
impl CanonicalRecord {
    pub fn receipt(&self) -> Option<&Receipt> {
        match self {
            Self::LegacyPlay(r) => Some(r),
            Self::PlayV2(r) => Some(&r.receipt),
            Self::AuthorV1(_) => None,
        }
    }
    pub fn original_scope(&self) -> &Scope {
        match self {
            Self::AuthorV1(r) => &r.scope,
            _ => &self.receipt().expect("play").request.scope,
        }
    }
    pub fn first_revision(&self) -> u64 {
        match self {
            Self::AuthorV1(r) => r.sequence,
            _ => self
                .receipt()
                .expect("play")
                .events
                .first()
                .map_or(0, |e| e.sequence),
        }
    }
    pub fn last_revision(&self) -> u64 {
        match self {
            Self::AuthorV1(r) => r.sequence,
            _ => self
                .receipt()
                .expect("play")
                .events
                .last()
                .map_or(0, |e| e.sequence),
        }
    }
    pub fn turn_key(&self) -> &str {
        match self {
            Self::AuthorV1(_) => AUTHOR_TURN_KEY,
            _ => &self.receipt().expect("play").request.turn,
        }
    }
    pub fn kind(&self) -> CanonicalRecordKind {
        match self {
            Self::LegacyPlay(_) => CanonicalRecordKind::LegacyPlay,
            Self::PlayV2(_) => CanonicalRecordKind::PlayV2,
            Self::AuthorV1(_) => CanonicalRecordKind::AuthorCorrection,
        }
    }
}
impl Serialize for CanonicalRecord {
    fn serialize<S: serde::Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        match self {
            Self::LegacyPlay(r) => r.serialize(serializer),
            Self::PlayV2(r) => {
                let mut m = serializer.serialize_map(Some(4))?;
                m.serialize_entry("record_version", &2u16)?;
                m.serialize_entry("kind", "play")?;
                m.serialize_entry("receipt", &r.receipt)?;
                m.serialize_entry("observations", &r.observations)?;
                m.end()
            }
            Self::AuthorV1(r) => {
                let mut m = serializer.serialize_map(Some(3))?;
                m.serialize_entry("record_version", &2u16)?;
                m.serialize_entry("kind", "author_correction")?;
                m.serialize_entry("receipt", r)?;
                m.end()
            }
        }
    }
}
#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize)]
pub(super) struct KnowledgeProjectionV2 {
    truth_overrides: BTreeMap<String, EventRef>,
    observed_overrides: BTreeMap<String, BTreeMap<String, EventRef>>,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum ObservationSource {
    SeedKnowledge {
        seed_id: String,
        actor: String,
        fact: String,
    },
    Event {
        source: EventRef,
    },
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct ObservedFactView {
    pub fact: String,
    pub proposition: String,
    pub observation: ObservationSource,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct EffectiveFactView {
    pub fact: String,
    pub proposition: String,
    source: TruthSource,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct ActorEventV2 {
    pub version: u16,
    pub event: AcceptedEvent,
    pub discovery: Option<ObservedFactView>,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct ActorReceiptViewV2 {
    pub version: u16,
    pub original_scope: Scope,
    pub turn: String,
    pub events: Vec<ActorEventV2>,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct CharacterContextV2 {
    pub version: u16,
    pub scope: Scope,
    pub revision: u64,
    pub observer: String,
    pub seed_source: String,
    pub self_state: Actor,
    pub facts: BTreeMap<String, ObservedFactView>,
    pub observations: Vec<ActorEventV2>,
    pub beliefs: Vec<Belief>,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct CompletedBoundaryCatalogV2 {
    pub version: u16,
    pub scope: Scope,
    pub head: u64,
    pub boundaries: Vec<u64>,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct AuthorCorrectionPreviewV1 {
    pub version: u16,
    pub input: AuthorCorrectionInputV1,
    pub child: Scope,
    pub before: EffectiveFactView,
    pub creation_revision: u64,
    pub retained_knowers: usize,
    pub excluded_suffix_events: u64,
    pub excluded_suffix_records: usize,
    pub original_preserved: bool,
    pub downstream_replayed: bool,
    pub new_child_requires_fresh_derivatives: bool,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PreparedAuthorCorrection {
    input: AuthorCorrectionInputV1,
    parent: AcceptedHistoryBasis,
    fork: AcceptedHistoryBasis,
    receipt: AuthorCorrectionReceiptV1,
    preview: AuthorCorrectionPreviewV1,
}
impl PreparedAuthorCorrection {
    pub fn input(&self) -> &AuthorCorrectionInputV1 {
        &self.input
    }
    pub fn preview(&self) -> &AuthorCorrectionPreviewV1 {
        &self.preview
    }
}
#[derive(Clone, Debug)]
pub struct AuthorCorrectionOutcome {
    pub engine: Engine,
    pub receipt: AuthorCorrectionReceiptV1,
}
fn check(cancel: &dyn Fn() -> bool) -> Result<(), Error> {
    if std::panic::catch_unwind(std::panic::AssertUnwindSafe(cancel)).unwrap_or(true) {
        Err(Error::Cancelled)
    } else {
        Ok(())
    }
}
fn parts(input: &AuthorCorrectionInputV1) -> (&str, &str, &str) {
    match &input.operation {
        AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact,
            expected_proposition,
            replacement,
        } => (fact, expected_proposition, replacement),
    }
}
fn validate_input(input: &AuthorCorrectionInputV1) -> Result<(), Error> {
    if input.version != 1 {
        return Err(Error::Version);
    }
    let (fact, old, new) = parts(input);
    if !valid_id(&input.parent.story)
        || !valid_id(&input.parent.branch)
        || !valid_id(&input.child_branch)
        || !valid_id(fact)
        || input.child_branch == input.parent.branch
        || input.fork_revision > input.expected_parent_revision
        || new.is_empty()
        || new == old
    {
        return Err(Error::Rule);
    }
    if [old, new, input.reason.as_str()]
        .iter()
        .any(|s| s.len() > MAX_TEXT_BYTES)
    {
        return Err(Error::TooLarge);
    }
    check_json_budget(input, MAX_RECEIPT_BYTES)
}
impl Engine {
    pub fn canonical_records(&self) -> &[CanonicalRecord] {
        &self.records
    }
    pub fn canonical_record_count(&self) -> usize {
        self.records.len()
    }
    pub fn domain_version(&self) -> u16 {
        if self
            .records
            .iter()
            .all(|r| matches!(r, CanonicalRecord::LegacyPlay(_)))
        {
            1
        } else {
            2
        }
    }
    pub fn completed_boundaries(&self) -> Vec<u64> {
        std::iter::once(0)
            .chain(self.records.iter().map(CanonicalRecord::last_revision))
            .collect()
    }
    pub fn completed_boundary_catalog(&self) -> CompletedBoundaryCatalogV2 {
        CompletedBoundaryCatalogV2 {
            version: 2,
            scope: self.scope.clone(),
            head: self.revision(),
            boundaries: self.completed_boundaries(),
        }
    }
    fn truth_source(&self, fact: &str) -> Result<TruthSource, Error> {
        if !self.seed.facts.contains_key(fact) {
            return Err(Error::UnknownReference);
        }
        Ok(self.knowledge.truth_overrides.get(fact).map_or_else(
            || TruthSource::SeedFact {
                seed_id: self.seed.id.clone(),
                fact: fact.into(),
            },
            |source| TruthSource::Author {
                source: source.clone(),
            },
        ))
    }
    fn truth_value(&self, fact: &str, source: &TruthSource) -> Result<String, Error> {
        match source {
            TruthSource::SeedFact { seed_id, fact: id }
                if seed_id == &self.seed.id && id == fact =>
            {
                self.seed
                    .facts
                    .get(fact)
                    .map(|v| v.proposition.clone())
                    .ok_or(Error::CorruptHistory)
            }
            TruthSource::Author { source } => self
                .records
                .iter()
                .find_map(|r| match r {
                    CanonicalRecord::AuthorV1(r)
                        if r.scope == source.original_scope
                            && r.sequence == source.sequence
                            && parts(&r.input).0 == fact
                            && self.lineage.eligible(
                                &self.scope,
                                self.revision(),
                                &source.original_scope,
                                source.sequence,
                            ) =>
                    {
                        Some(parts(&r.input).2.to_owned())
                    }
                    _ => None,
                })
                .ok_or(Error::CorruptHistory),
            _ => Err(Error::CorruptHistory),
        }
    }
    pub fn effective_fact(&self, fact: &str) -> Result<EffectiveFactView, Error> {
        let source = self.truth_source(fact)?;
        Ok(EffectiveFactView {
            fact: fact.into(),
            proposition: self.truth_value(fact, &source)?,
            source,
        })
    }
    fn check_record_budget(
        &self,
        record: &CanonicalRecord,
        state: &Projection,
        knowledge: &KnowledgeProjectionV2,
    ) -> Result<(), Error> {
        if self.records.len() >= MAX_HISTORY_RECEIPTS {
            return Err(Error::TooLarge);
        }
        check_json_budget(record, MAX_RECEIPT_BYTES)?;
        let mut bytes = serde_json::to_vec(record)
            .map_err(|_| Error::TooLarge)?
            .len();
        for r in &self.records {
            bytes = bytes
                .checked_add(serde_json::to_vec(r).map_err(|_| Error::TooLarge)?.len())
                .ok_or(Error::TooLarge)?;
            if bytes > MAX_HISTORY_BYTES {
                return Err(Error::TooLarge);
            }
        }
        if bytes > MAX_HISTORY_BYTES {
            return Err(Error::TooLarge);
        }
        if self.domain_version() == 1 && matches!(record, CanonicalRecord::LegacyPlay(_)) {
            check_json_budget(state, 262_144)
        } else {
            check_json_budget(
                &serde_json::json!({"version":2,"mechanical":state,"knowledge":knowledge}),
                262_144,
            )
        }
    }
    pub(super) fn append_play(&mut self, receipt: Receipt) -> Result<(), Error> {
        let domain_two = self.domain_version() == 2;
        let mut state = self.state.clone();
        let mut knowledge = self.knowledge.clone();
        let mut observations = vec![];
        for (command, event) in receipt.proposal.commands.iter().zip(&receipt.events) {
            resolve(&self.seed, &mut state, command, event.sequence, domain_two)?;
            if domain_two {
                if let Effect::Discovered { actor, fact } = &event.outcome {
                    let source = EventRef {
                        original_scope: event.scope.clone(),
                        sequence: event.sequence,
                    };
                    observations.push(ObservationBinding {
                        event: source.clone(),
                        actor: actor.clone(),
                        fact: fact.clone(),
                        truth: self.truth_source(fact)?,
                    });
                    knowledge
                        .observed_overrides
                        .entry(actor.clone())
                        .or_default()
                        .insert(fact.clone(), source);
                }
            }
        }
        let record = if domain_two {
            CanonicalRecord::PlayV2(CanonicalPlayV2 {
                receipt,
                observations,
            })
        } else {
            CanonicalRecord::LegacyPlay(receipt)
        };
        self.check_record_budget(&record, &state, &knowledge)?;
        self.state = state;
        self.knowledge = knowledge;
        self.records.push(record);
        self.receipt_cache.take();
        Ok(())
    }
    fn append_author_history(
        &mut self,
        input: &AuthorCorrectionInputV1,
    ) -> Result<AuthorCorrectionReceiptV1, Error> {
        validate_input(input)?;
        if input.child_branch != self.scope.branch
            || input.parent.story != self.scope.story
            || self.revision() != input.fork_revision
        {
            return Err(Error::Scope);
        }
        let binding = self.memory_lineage_binding()?;
        if !binding.first().is_some_and(|b| {
            b.parent.as_deref() == Some(input.parent.branch.as_str())
                && b.fork_revision == Some(input.fork_revision)
        }) {
            return Err(Error::Scope);
        }
        if self
            .records
            .iter()
            .any(|r| r.original_scope() == &self.scope && r.turn_key() == AUTHOR_TURN_KEY)
        {
            return Err(Error::RetryMismatch);
        }
        let (fact, expected, _) = parts(input);
        let before = self.truth_source(fact)?;
        if self.truth_value(fact, &before)? != expected {
            return Err(Error::Stale);
        }
        let sequence = self.revision().checked_add(1).ok_or(Error::TooLarge)?;
        let receipt = AuthorCorrectionReceiptV1 {
            version: 1,
            policy: AuthorPolicyV1::ReplaceExistingFactPropositionV1,
            scope: self.scope.clone(),
            sequence,
            rules: self.seed.profile.clone(),
            seed: self.seed.id.clone(),
            story_time: self.state.story_time,
            witnesses: BTreeSet::new(),
            input: input.clone(),
            before,
        };
        let record = CanonicalRecord::AuthorV1(receipt.clone());
        let mut knowledge = self.knowledge.clone();
        knowledge.truth_overrides.insert(
            fact.into(),
            EventRef {
                original_scope: self.scope.clone(),
                sequence,
            },
        );
        self.check_record_budget(&record, &self.state, &knowledge)?;
        self.knowledge = knowledge;
        self.records.push(record);
        self.receipt_cache.take();
        Ok(receipt)
    }
    pub fn prepare_author_correction(
        &self,
        input: &AuthorCorrectionInputV1,
        cancel: &dyn Fn() -> bool,
    ) -> Result<PreparedAuthorCorrection, Error> {
        check(cancel)?;
        validate_input(input)?;
        if input.parent != self.scope {
            return Err(Error::Scope);
        }
        if input.expected_parent_revision != self.revision() {
            return Err(Error::Stale);
        }
        let parent = self.accepted_history_basis()?;
        let fork = self.accepted_history_basis_at(input.fork_revision)?;
        let mut child = self.fork(&input.child_branch, input.fork_revision)?;
        let fact = parts(input).0;
        let mut retained_knowers = 0;
        for actor in self.seed.actors.keys() {
            check(cancel)?;
            if child
                .observed_facts(actor, child.scope(), child.revision())?
                .contains_key(fact)
            {
                retained_knowers += 1;
            }
        }
        let before = child.effective_fact(fact)?;
        let receipt = child.append_author_history(input)?;
        let preview = AuthorCorrectionPreviewV1 {
            version: 1,
            input: input.clone(),
            child: child.scope.clone(),
            before,
            creation_revision: child.revision(),
            retained_knowers,
            excluded_suffix_events: self.revision() - input.fork_revision,
            excluded_suffix_records: self
                .records
                .iter()
                .filter(|r| r.last_revision() > input.fork_revision)
                .count(),
            original_preserved: true,
            downstream_replayed: false,
            new_child_requires_fresh_derivatives: true,
        };
        check_json_budget(&preview, 65_536)?;
        check(cancel)?;
        Ok(PreparedAuthorCorrection {
            input: input.clone(),
            parent,
            fork,
            receipt,
            preview,
        })
    }
    pub fn apply_author_correction(
        &self,
        prepared: &PreparedAuthorCorrection,
        cancel: &dyn Fn() -> bool,
    ) -> Result<AuthorCorrectionOutcome, Error> {
        let actual = self.prepare_author_correction(&prepared.input, cancel)?;
        if actual != *prepared {
            return Err(Error::Stale);
        }
        let mut engine = self.fork(&prepared.input.child_branch, prepared.input.fork_revision)?;
        let receipt = engine.append_author_history(&prepared.input)?;
        check(cancel)?;
        Ok(AuthorCorrectionOutcome { engine, receipt })
    }
    pub fn replay_records(seed: Seed, records: &[CanonicalRecord]) -> Result<Self, Error> {
        let strings = records
            .iter()
            .map(|r| serde_json::to_string(r).map_err(|_| Error::CorruptHistory))
            .collect::<Result<Vec<_>, _>>()?;
        Self::restore(seed, &strings)
    }
    pub(super) fn restore_record_value(&mut self, raw: &serde_json::Value) -> Result<(), Error> {
        let wrapped = raw.get("record_version").is_some();
        let kind = if wrapped {
            if raw["record_version"] != 2 {
                return Err(Error::CorruptHistory);
            }
            raw["kind"].as_str().ok_or(Error::CorruptHistory)?
        } else {
            "legacy"
        };
        if kind == "author_correction" {
            let input = parse_input(&raw["receipt"]["input"])?;
            if self.scope.branch != input.child_branch {
                if self.scope != input.parent {
                    return Err(Error::CorruptHistory);
                }
                let target = Scope {
                    story: self.scope.story.clone(),
                    branch: input.child_branch.clone(),
                };
                if self.lineage.binding(&target).is_ok() {
                    self.scope = target;
                } else {
                    *self = self.fork(&input.child_branch, input.fork_revision)?;
                }
            }
            self.append_author_history(&input)
                .map_err(|_| Error::CorruptHistory)?;
        } else {
            if (kind == "legacy" && self.domain_version() != 1)
                || (kind == "play" && self.domain_version() != 2)
                || !["legacy", "play"].contains(&kind)
            {
                return Err(Error::CorruptHistory);
            }
            let value = if wrapped { &raw["receipt"] } else { raw };
            let record: PersistedReceipt =
                serde_json::from_value(value.clone()).map_err(|_| Error::CorruptHistory)?;
            if record.events.is_empty()
                || record.events.len() > MAX_COMMANDS
                || self.recorded(&record.request)?.is_some()
            {
                return Err(Error::CorruptHistory);
            }
            if let Some(play) = &record.play {
                if play.narration.text != record.narration {
                    return Err(Error::CorruptHistory);
                }
                self.commit_play_history(&record.request, &record.proposal, play, true)
            } else {
                self.commit(&record.request, &record.proposal, &record.narration)
            }
            .map_err(|_| Error::CorruptHistory)?;
        }
        if serde_json::to_value(self.records.last().ok_or(Error::CorruptHistory)?)
            .map_err(|_| Error::CorruptHistory)?
            != *raw
        {
            return Err(Error::CorruptHistory);
        }
        Ok(())
    }
    fn validate_actor_read(
        &self,
        observer: &str,
        scope: &Scope,
        revision: u64,
    ) -> Result<(), Error> {
        if scope != &self.scope {
            return Err(Error::Scope);
        }
        if revision != self.revision() {
            return Err(Error::Stale);
        }
        if !self.state.actors.contains_key(observer) {
            return Err(Error::UnknownReference);
        }
        Ok(())
    }
    fn observation_binding(
        &self,
        source: &EventRef,
        actor: &str,
        fact: &str,
    ) -> Result<&ObservationBinding, Error> {
        self.records
            .iter()
            .find_map(|r| match r {
                CanonicalRecord::PlayV2(r) => r
                    .observations
                    .iter()
                    .find(|b| &b.event == source && b.actor == actor && b.fact == fact),
                _ => None,
            })
            .ok_or(Error::CorruptHistory)
    }
    pub fn observed_facts(
        &self,
        observer: &str,
        scope: &Scope,
        revision: u64,
    ) -> Result<BTreeMap<String, ObservedFactView>, Error> {
        self.validate_actor_read(observer, scope, revision)?;
        let mut values = BTreeMap::new();
        for (fact, seed_fact) in &self.seed.facts {
            let known = if let Some(source) = self
                .knowledge
                .observed_overrides
                .get(observer)
                .and_then(|v| v.get(fact))
            {
                let binding = self.observation_binding(source, observer, fact)?;
                Some((
                    self.truth_value(fact, &binding.truth)?,
                    ObservationSource::Event {
                        source: source.clone(),
                    },
                ))
            } else if seed_fact.known_by.contains(observer) {
                Some((
                    seed_fact.proposition.clone(),
                    ObservationSource::SeedKnowledge {
                        seed_id: self.seed.id.clone(),
                        actor: observer.into(),
                        fact: fact.clone(),
                    },
                ))
            } else {
                self.records.iter().filter_map(CanonicalRecord::receipt).flat_map(|r| &r.events).rev().find(|e| self.actor_event_eligible(observer, scope, revision, e) && matches!(&e.outcome, Effect::Discovered { actor, fact: id } if actor == observer && id == fact))
                    .map(|e| (seed_fact.proposition.clone(), ObservationSource::Event { source: EventRef { original_scope: e.scope.clone(), sequence: e.sequence } }))
            };
            if let Some((proposition, observation)) = known {
                values.insert(
                    fact.clone(),
                    ObservedFactView {
                        fact: fact.clone(),
                        proposition,
                        observation,
                    },
                );
            }
        }
        Ok(values)
    }
    fn actor_event_v2(&self, observer: &str, event: &AcceptedEvent) -> Result<ActorEventV2, Error> {
        let discovery = if let Effect::Discovered { actor, fact } = &event.outcome {
            if actor == observer {
                let source = EventRef {
                    original_scope: event.scope.clone(),
                    sequence: event.sequence,
                };
                let legacy = self.records.iter().any(|r| matches!(r, CanonicalRecord::LegacyPlay(r) if r.events.iter().any(|e| e.scope == source.original_scope && e.sequence == source.sequence)));
                let proposition = if legacy {
                    self.seed
                        .facts
                        .get(fact)
                        .ok_or(Error::CorruptHistory)?
                        .proposition
                        .clone()
                } else {
                    self.truth_value(fact, &self.observation_binding(&source, actor, fact)?.truth)?
                };
                Some(ObservedFactView {
                    fact: fact.clone(),
                    proposition,
                    observation: ObservationSource::Event { source },
                })
            } else {
                None
            }
        } else {
            None
        };
        Ok(ActorEventV2 {
            version: 2,
            event: event.clone(),
            discovery,
        })
    }
    #[allow(clippy::too_many_arguments)]
    pub fn visit_actor_observations_v2(
        &self,
        observer: &str,
        scope: &Scope,
        revision: u64,
        after: u64,
        through: u64,
        cancel: &dyn Fn() -> bool,
        visitor: &mut dyn FnMut(&ActorEventV2) -> bool,
    ) -> Result<(), Error> {
        self.validate_actor_read(observer, scope, revision)?;
        if after > through || through > revision {
            return Err(Error::Rule);
        }
        check(cancel)?;
        for record in &self.records {
            check(cancel)?;
            if let Some(r) = record.receipt() {
                for event in &r.events {
                    check(cancel)?;
                    if event.sequence > after
                        && event.sequence <= through
                        && self.actor_event_eligible(observer, scope, revision, event)
                        && !visitor(&self.actor_event_v2(observer, event)?)
                    {
                        return Ok(());
                    }
                }
            }
        }
        check(cancel)
    }
    pub fn actor_receipts_v2(
        &self,
        observer: &str,
        scope: &Scope,
        revision: u64,
    ) -> Result<Vec<ActorReceiptViewV2>, Error> {
        self.validate_actor_read(observer, scope, revision)?;
        let mut views = vec![];
        for r in self.records.iter().filter_map(CanonicalRecord::receipt) {
            let events = r
                .events
                .iter()
                .filter(|e| self.actor_event_eligible(observer, scope, revision, e))
                .map(|e| self.actor_event_v2(observer, e))
                .collect::<Result<Vec<_>, _>>()?;
            if !events.is_empty() {
                views.push(ActorReceiptViewV2 {
                    version: 2,
                    original_scope: r.request.scope.clone(),
                    turn: r.request.turn.clone(),
                    events,
                });
            }
        }
        Ok(views)
    }
    pub fn character_context_v2(
        &self,
        observer: &str,
        scope: &Scope,
        revision: u64,
    ) -> Result<CharacterContextV2, Error> {
        let facts = self.observed_facts(observer, scope, revision)?;
        let mut observations = vec![];
        self.visit_actor_observations_v2(
            observer,
            scope,
            revision,
            0,
            revision,
            &|| false,
            &mut |v| {
                observations.push(v.clone());
                true
            },
        )?;
        Ok(CharacterContextV2 {
            version: 2,
            scope: scope.clone(),
            revision,
            observer: observer.into(),
            seed_source: self.seed.id.clone(),
            self_state: self.state.actors[observer].clone(),
            facts,
            observations,
            beliefs: self
                .state
                .beliefs
                .iter()
                .filter(|b| b.believer == observer)
                .cloned()
                .collect(),
        })
    }
}

// Hostile persisted INPUT only; no accepted type or plan implements Deserialize.
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct InputDto {
    version: u16,
    parent: Scope,
    expected_parent_revision: u64,
    fork_revision: u64,
    child_branch: String,
    operation: OperationDto,
    reason: String,
}
#[derive(Deserialize)]
#[serde(tag = "op", rename_all = "snake_case", deny_unknown_fields)]
enum OperationDto {
    ReplaceFactProposition {
        fact: String,
        expected_proposition: String,
        replacement: String,
    },
}
fn parse_input(value: &serde_json::Value) -> Result<AuthorCorrectionInputV1, Error> {
    let v: InputDto = serde_json::from_value(value.clone()).map_err(|_| Error::CorruptHistory)?;
    let operation = match v.operation {
        OperationDto::ReplaceFactProposition {
            fact,
            expected_proposition,
            replacement,
        } => AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact,
            expected_proposition,
            replacement,
        },
    };
    Ok(AuthorCorrectionInputV1 {
        version: v.version,
        parent: v.parent,
        expected_parent_revision: v.expected_parent_revision,
        fork_revision: v.fork_revision,
        child_branch: v.child_branch,
        operation,
        reason: v.reason,
    })
}
