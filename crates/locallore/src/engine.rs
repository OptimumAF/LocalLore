use crate::{contracts::*, scope::Lineage};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};
use std::sync::OnceLock;
#[path = "author_correction.rs"]
pub mod author_correction;
#[path = "engine/staged_play.rs"]
pub mod staged_play;
use author_correction::{CanonicalRecord, KnowledgeProjectionV2};

#[derive(Clone, Debug)]
pub struct Engine {
    seed: Seed,
    scope: Scope,
    lineage: Lineage,
    state: Projection,
    records: Vec<CanonicalRecord>,
    // Derived only from the actual serialized records at the two append sites.
    // Never persisted, deserialized, hashed as source identity or used as canon.
    canonical_record_bytes: usize,
    knowledge: KnowledgeProjectionV2,
    receipt_cache: OnceLock<Vec<Receipt>>,
}

/// Opaque native identity of an accepted source prefix. No serialized value can
/// construct this token or grant observer, mutation or persistence authority.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct AcceptedHistoryBasis {
    scope: Scope,
    revision: u64,
    digest: [u8; 32],
}
impl AcceptedHistoryBasis {
    /// The fingerprint protects precisely this request's source boundary.
    pub fn matches_request(&self, request: &Request) -> bool {
        self.scope == request.scope && self.revision == request.expected_revision
    }
    /// Read/cleanup may guard a historical request with a stronger selected head.
    pub fn covers_request(&self, request: &Request) -> bool {
        self.scope == request.scope && self.revision >= request.expected_revision
    }
}

struct BasisWriter {
    hash: sha2::Sha256,
    bytes: usize,
}
impl std::io::Write for BasisWriter {
    fn write(&mut self, bytes: &[u8]) -> std::io::Result<usize> {
        use sha2::Digest;
        let total = self
            .bytes
            .checked_add(bytes.len())
            .filter(|n| *n <= 64 * 1024 * 1024)
            .ok_or_else(|| std::io::Error::other("accepted history basis budget"))?;
        self.hash.update(bytes);
        self.bytes = total;
        Ok(bytes.len())
    }
    fn flush(&mut self) -> std::io::Result<()> {
        Ok(())
    }
}

/// Deliberately omits hidden world truth, other actors' sheets and omniscient summaries.
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct CharacterContext {
    pub version: u16,
    pub scope: Scope,
    pub revision: u64,
    pub observer: String,
    pub seed_source: String,
    pub self_state: Actor,
    pub facts: BTreeMap<String, String>,
    pub observations: Vec<AcceptedEvent>,
    pub beliefs: Vec<Belief>,
}

// This private input is never an accepted canonical value. Only rebuilding and comparing its
// entire encoding can produce a Receipt; AcceptedEvent and Receipt remain Serialize-only.
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct PersistedReceipt {
    request: Request,
    proposal: Proposal,
    events: Vec<serde_json::Value>,
    narration: String,
    play: Option<crate::play::PlayRecord>,
}

struct UniqueJson(serde_json::Value);

/// Structural JSON validation only. Caller supplies its byte budget; this grants
/// no accepted-history, engine, filesystem or permission authority.
pub fn parse_unique_json(bytes: &[u8], max_bytes: usize) -> Result<serde_json::Value, Error> {
    if bytes.len() > max_bytes {
        return Err(Error::TooLarge);
    }
    let raw: UniqueJson = serde_json::from_slice(bytes).map_err(|_| Error::Malformed)?;
    Ok(raw.0)
}

pub(crate) fn parse_unique<T: serde::de::DeserializeOwned>(bytes: &[u8]) -> Result<T, Error> {
    serde_json::from_value(parse_unique_json(bytes, bytes.len())?).map_err(|_| Error::Malformed)
}

impl<'de> Deserialize<'de> for UniqueJson {
    fn deserialize<D: serde::Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        struct Visitor;
        impl<'de> serde::de::Visitor<'de> for Visitor {
            type Value = UniqueJson;

            fn expecting(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
                formatter.write_str("JSON without duplicate object keys")
            }
            fn visit_bool<E: serde::de::Error>(self, value: bool) -> Result<Self::Value, E> {
                Ok(UniqueJson(value.into()))
            }
            fn visit_i64<E: serde::de::Error>(self, value: i64) -> Result<Self::Value, E> {
                Ok(UniqueJson(value.into()))
            }
            fn visit_u64<E: serde::de::Error>(self, value: u64) -> Result<Self::Value, E> {
                Ok(UniqueJson(value.into()))
            }
            fn visit_f64<E: serde::de::Error>(self, value: f64) -> Result<Self::Value, E> {
                serde_json::Number::from_f64(value)
                    .map(|number| UniqueJson(serde_json::Value::Number(number)))
                    .ok_or_else(|| E::custom("invalid JSON number"))
            }
            fn visit_str<E: serde::de::Error>(self, value: &str) -> Result<Self::Value, E> {
                Ok(UniqueJson(value.into()))
            }
            fn visit_string<E: serde::de::Error>(self, value: String) -> Result<Self::Value, E> {
                Ok(UniqueJson(value.into()))
            }
            fn visit_unit<E: serde::de::Error>(self) -> Result<Self::Value, E> {
                Ok(UniqueJson(serde_json::Value::Null))
            }
            fn visit_seq<A: serde::de::SeqAccess<'de>>(
                self,
                mut sequence: A,
            ) -> Result<Self::Value, A::Error> {
                let mut values = Vec::new();
                while let Some(UniqueJson(value)) = sequence.next_element()? {
                    values.push(value);
                }
                Ok(UniqueJson(serde_json::Value::Array(values)))
            }
            fn visit_map<A: serde::de::MapAccess<'de>>(
                self,
                mut object: A,
            ) -> Result<Self::Value, A::Error> {
                let mut values = serde_json::Map::new();
                while let Some(key) = object.next_key::<String>()? {
                    if values.contains_key(&key) {
                        return Err(serde::de::Error::custom("duplicate JSON key"));
                    }
                    let UniqueJson(value) = object.next_value()?;
                    values.insert(key, value);
                }
                Ok(UniqueJson(serde_json::Value::Object(values)))
            }
        }
        deserializer.deserialize_any(Visitor)
    }
}

impl Engine {
    pub fn new(seed: Seed) -> Result<Self, Error> {
        validate_seed(&seed)?;
        let state = Projection {
            actors: seed.actors.clone(),
            items: seed.items.clone(),
            claims: vec![],
            beliefs: seed.beliefs.clone(),
            discoveries: BTreeMap::new(),
            relationships: seed.relationships.clone(),
            commitments: seed.commitments.clone(),
            progression_sources: BTreeMap::new(),
            story_time: seed.story_time,
            item_transfers: BTreeMap::new(),
        };
        Ok(Self {
            scope: seed.scope.clone(),
            lineage: Lineage::new(&seed.scope),
            seed,
            state,
            records: vec![],
            canonical_record_bytes: 0,
            knowledge: KnowledgeProjectionV2::default(),
            receipt_cache: OnceLock::new(),
        })
    }

    pub fn scope(&self) -> &Scope {
        &self.scope
    }
    /// Bounded streaming fingerprint of validated native seed, immutable lineage
    /// and exact original receipts. This never materializes a second history.
    pub fn accepted_history_basis(&self) -> Result<AcceptedHistoryBasis, Error> {
        self.history_basis_at(self.revision())
    }
    pub fn accepted_history_basis_at(&self, at: u64) -> Result<AcceptedHistoryBasis, Error> {
        self.history_basis_at(at)
    }
    /// Appends retain a basis only when its entire original prefix survives.
    pub fn matches_accepted_history(&self, basis: &AcceptedHistoryBasis) -> Result<bool, Error> {
        if self.scope != basis.scope || self.revision() < basis.revision {
            return Ok(false);
        }
        match self.history_basis_at(basis.revision) {
            Ok(actual) => Ok(actual == *basis),
            Err(Error::Rule) => Ok(false),
            Err(error) => Err(error),
        }
    }
    fn history_basis_at(&self, at: u64) -> Result<AcceptedHistoryBasis, Error> {
        use sha2::Digest;
        let end = if at == 0 {
            0
        } else {
            self.records
                .iter()
                .position(|r| r.last_revision() == at)
                .ok_or(Error::Rule)?
                + 1
        };
        let mut writer = BasisWriter {
            hash: sha2::Sha256::new(),
            bytes: 0,
        };
        serde_json::to_writer(
            &mut writer,
            &(
                if self.records[..end]
                    .iter()
                    .all(|r| matches!(r, CanonicalRecord::LegacyPlay(_)))
                {
                    "locallore-native-accepted-history-v1"
                } else {
                    "locallore-native-accepted-history-v2"
                },
                &self.scope,
                at,
                &self.seed,
                self.memory_lineage_binding()?,
                &self.records[..end],
            ),
        )
        .map_err(|_| Error::TooLarge)?;
        Ok(AcceptedHistoryBasis {
            scope: self.scope.clone(),
            revision: at,
            digest: writer.hash.finalize().into(),
        })
    }
    /// Compare two validated native snapshots without granting mutation or
    /// observer authority. Matching IDs/revisions alone do not identify history.
    /// Another owner's append is allowed only to the exact immutable prefix.
    pub fn extends_accepted_history(&self, previous: &Engine) -> Result<bool, Error> {
        Ok(self.scope == previous.scope
            && self.seed == previous.seed
            && self.revision() >= previous.revision()
            && self.records.starts_with(&previous.records)
            && self.memory_lineage_binding()? == previous.memory_lineage_binding()?)
    }
    pub(crate) fn memory_lineage_binding(
        &self,
    ) -> Result<Vec<crate::scope::LineageBindingEntry>, Error> {
        self.lineage.binding(&self.scope)
    }
    pub fn seed(&self) -> &Seed {
        &self.seed
    }
    pub fn state(&self) -> &Projection {
        &self.state
    }
    pub fn receipts(&self) -> &[Receipt] {
        self.receipt_cache.get_or_init(|| {
            self.records
                .iter()
                .filter_map(CanonicalRecord::receipt)
                .cloned()
                .collect()
        })
    }
    pub fn revision(&self) -> u64 {
        self.records
            .last()
            .map_or(0, CanonicalRecord::last_revision)
    }

    /// Stable canonical projection encoding: struct field order and ordered maps/sets, no floats.
    /// Not an archive format or cryptographic integrity guarantee.
    pub fn canonical_bytes(&self) -> Vec<u8> {
        if self.domain_version() == 1 {
            serde_json::to_vec(&self.state).expect("projection is serializable")
        } else {
            serde_json::to_vec(&serde_json::json!({"version":2,"mechanical":self.state,"knowledge":self.knowledge})).expect("projection is serializable")
        }
    }

    pub fn request(&self, turn: &str, intent: Intent) -> Request {
        Request {
            version: VERSION,
            scope: self.scope.clone(),
            turn: turn.into(),
            expected_revision: self.revision(),
            intent,
        }
    }

    pub fn proposal(request: &Request) -> Result<Proposal, Error> {
        let commands = match &request.intent {
            Intent::Actions(commands) => commands.clone(),
            Intent::Dialogue { text, audience } => vec![Command::Say {
                text: text.clone(),
                audience: audience.clone(),
            }],
            Intent::AuthorCorrection(_) => return Err(Error::AuthorUiRequired),
            Intent::Thought(_) | Intent::Ambiguous(_) | Intent::FreeText { .. } => {
                return Err(Error::ClarificationRequired)
            }
        };
        Ok(Proposal {
            version: VERSION,
            scope: request.scope.clone(),
            turn: request.turn.clone(),
            expected_revision: request.expected_revision,
            commands,
        })
    }

    /// Duplicate lookup precedes inference and stale checks. The full typed request is compared,
    /// rather than relying on a noncryptographic digest collision for idempotency.
    pub fn recorded(&self, request: &Request) -> Result<Option<Receipt>, Error> {
        if request.scope != self.scope {
            return Err(Error::Scope);
        }
        if self.records.iter().any(|r| {
            r.original_scope() == &request.scope
                && r.turn_key() == request.turn
                && r.receipt().is_none()
        }) {
            return Err(Error::RetryMismatch);
        }
        if let Some(receipt) = self
            .records
            .iter()
            .filter_map(CanonicalRecord::receipt)
            .find(|r| r.request.scope == request.scope && r.request.turn == request.turn)
        {
            if &receipt.request != request {
                return Err(Error::RetryMismatch);
            }
            return Ok(Some(receipt.clone()));
        }
        Ok(None)
    }

    pub fn preflight(&self, request: &Request) -> Result<(), Error> {
        if request.version != VERSION {
            return Err(Error::Version);
        }
        if request.scope != self.scope {
            return Err(Error::Scope);
        }
        if request.expected_revision != self.revision() {
            return Err(Error::Stale);
        }
        if !valid_id(&request.turn) {
            return Err(Error::Rule);
        }
        let _ = self.recorded(request)?;
        check_json_budget(request, MAX_PROPOSAL_BYTES)?;
        if let Intent::FreeText { text, .. } = &request.intent {
            if text.trim().is_empty()
                || text.len() > MAX_TEXT_BYTES
                || text
                    .chars()
                    .any(|c| c.is_control() && c != '\n' && c != '\t')
            {
                return Err(Error::TooLarge);
            }
        }
        if let Intent::Actions(commands) = &request.intent {
            if commands.is_empty() || commands.len() > MAX_COMMANDS {
                return Err(Error::TooLarge);
            }
        }
        Ok(())
    }

    pub fn preview(&self, request: &Request, proposal: &Proposal) -> Result<Receipt, Error> {
        // The legacy public preview has no Domain 2 generated-Play contract.
        if self.domain_version() == 2 && matches!(request.intent, Intent::FreeText { .. }) {
            return Err(Error::Version);
        }
        self.preview_resolved(request, proposal)
    }

    // One resolver for legacy preview and the native, source-bound Play2.5 stage.
    // This private entry does not change public preview's version admission.
    fn preview_resolved(&self, request: &Request, proposal: &Proposal) -> Result<Receipt, Error> {
        self.preflight(request)?;
        if request.version != VERSION || proposal.version != VERSION {
            return Err(Error::Version);
        }
        if request.scope != self.scope || proposal.scope != request.scope {
            return Err(Error::Scope);
        }
        if request.expected_revision != self.revision()
            || proposal.expected_revision != request.expected_revision
        {
            return Err(Error::Stale);
        }
        if proposal.turn != request.turn || !valid_id(&request.turn) {
            return Err(Error::Rule);
        }
        if matches!(request.intent, Intent::FreeText { .. }) {
            crate::play::validate_interpretation(self, request, proposal)?;
        } else if Self::proposal(request)?.commands != proposal.commands {
            return Err(Error::Agency);
        }
        if proposal.commands.is_empty() || proposal.commands.len() > MAX_COMMANDS {
            return Err(Error::TooLarge);
        }
        let mut staged = self.state.clone();
        let mut events = vec![];
        for command in &proposal.commands {
            let sequence = self
                .revision()
                .checked_add(events.len() as u64 + 1)
                .ok_or(Error::Rule)?;
            let (outcome, participants, witnesses) = resolve(
                &self.seed,
                &mut staged,
                command,
                sequence,
                self.domain_version() == 2,
            )?;
            events.push(AcceptedEvent {
                version: VERSION,
                scope: self.scope.clone(),
                sequence,
                turn: request.turn.clone(),
                rules: self.seed.profile.clone(),
                seed: self.seed.id.clone(),
                story_time: staged.story_time,
                participants,
                witnesses,
                outcome,
            });
        }
        let narration = render(&events);
        Ok(Receipt {
            request: request.clone(),
            proposal: proposal.clone(),
            events,
            narration,
            play: None,
        })
    }

    /// In-memory atomic replacement only. SQLite durability and concurrent writers belong to M04.
    pub fn commit(
        &mut self,
        request: &Request,
        proposal: &Proposal,
        narration: &str,
    ) -> Result<Receipt, Error> {
        if let Some(receipt) = self.recorded(request)? {
            return Ok(receipt);
        }
        if matches!(request.intent, Intent::FreeText { .. }) {
            return Err(Error::Agency);
        }
        let receipt = self.preview(request, proposal)?;
        // The fake-provider proof accepts only exact engine-rendered prose. No semantic oracle claim.
        if narration != receipt.narration {
            return Err(Error::Narration);
        }
        self.append_play(receipt.clone())?;
        Ok(receipt)
    }

    /// Only a versioned generated-play record can relax v1's exact-rendered narration rule.
    pub fn commit_play(
        &mut self,
        request: &Request,
        proposal: &Proposal,
        record: &crate::play::PlayRecord,
    ) -> Result<Receipt, Error> {
        self.commit_play_history(request, proposal, record, false)
    }
    fn commit_play_history(
        &mut self,
        request: &Request,
        proposal: &Proposal,
        record: &crate::play::PlayRecord,
        recorded_history: bool,
    ) -> Result<Receipt, Error> {
        if record.prompt_version == crate::play::LITERAL_PLAY_PROMPT_VERSION_V1 {
            if let Some(receipt) = self.recorded(request)? {
                return Ok(receipt);
            }
            let staged = self.stage_play_v25(request, proposal, &|| false)?;
            return self.commit_staged_literal_play_history_v1(
                staged,
                record,
                &|| false,
                recorded_history,
            );
        }
        if record.prompt_version == "locallore-play-v2.5" {
            if let Some(receipt) = self.recorded(request)? {
                return Ok(receipt);
            }
            let staged = self.stage_play_v25(request, proposal, &|| false)?;
            return self.commit_staged_play_history_v25(
                staged,
                record,
                &|| false,
                recorded_history,
            );
        }
        if self.domain_version() == 2 {
            return Err(Error::Version);
        }
        if let Some(receipt) = self.recorded(request)? {
            return Ok(receipt);
        }
        if !matches!(request.intent, Intent::FreeText { .. }) {
            return Err(Error::Agency);
        }
        let mut receipt = self.preview(request, proposal)?;
        crate::play::validate_record(self, &receipt, record, recorded_history)?;
        receipt.narration = record.narration.text.clone();
        receipt.play = Some(record.clone());
        self.append_play(receipt.clone())?;
        Ok(receipt)
    }

    /// Revalidate a prepared engine value; callers cannot supply accepted events as authority.
    pub fn commit_prepared(&mut self, receipt: &Receipt) -> Result<Receipt, Error> {
        if let Some(play) = receipt.play() {
            self.commit_play(receipt.request(), receipt.proposal(), play)
        } else {
            self.commit(receipt.request(), receipt.proposal(), receipt.narration())
        }
    }

    // History paths alone retain the explicitly supported recorded prompt. A
    // prepared value supplied for a new turn must still use the current prompt.
    fn commit_recorded(&mut self, receipt: &Receipt) -> Result<Receipt, Error> {
        if let Some(play) = receipt.play() {
            self.commit_play_history(receipt.request(), receipt.proposal(), play, true)
        } else {
            self.commit(receipt.request(), receipt.proposal(), receipt.narration())
        }
    }

    /// Restore bounded complete persisted root-history receipts, never a supplied projection.
    /// V1 rules are deterministic: rebuilding verifies every recorded resolved outcome. Future
    /// random rules require an explicit recorded-outcome contract; they must not reroll here.
    /// No inference provider or random source is used. No partially restored engine is returned.
    pub fn restore(seed: Seed, history: &[String]) -> Result<Self, Error> {
        let mut engine = Self::new(seed)?;
        engine.restore_saved(history)?;
        Ok(engine)
    }

    /// Restore branch-local recorded receipts onto this validated engine, retaining
    /// original ancestor scopes and lineage. No provider runs and no partial value escapes.
    /// This history-only path retains the same supported recorded Play policy as restore;
    /// fresh prepared commits still require the current policy.
    pub fn restore_continuation(&self, history: &[String]) -> Result<Self, Error> {
        let mut engine = self.clone();
        engine.restore_saved(history)?;
        Ok(engine)
    }

    fn restore_saved(&mut self, history: &[String]) -> Result<(), Error> {
        if self.records.len().saturating_add(history.len()) > MAX_HISTORY_RECEIPTS {
            return Err(Error::TooLarge);
        }
        let mut total = 0usize;
        for receipt in &self.records {
            let bytes = serde_json::to_vec(receipt)
                .map_err(|_| Error::CorruptHistory)?
                .len();
            if bytes > MAX_RECEIPT_BYTES {
                return Err(Error::TooLarge);
            }
            total = total.checked_add(bytes).ok_or(Error::TooLarge)?;
        }
        for receipt in history {
            total = total.checked_add(receipt.len()).ok_or(Error::TooLarge)?;
            if receipt.len() > MAX_RECEIPT_BYTES || total > MAX_HISTORY_BYTES {
                return Err(Error::TooLarge);
            }
        }
        if total > MAX_HISTORY_BYTES {
            return Err(Error::TooLarge);
        }
        for receipt in history {
            // Value normally accepts repeated object keys. Reject them recursively before typed
            // parsing so hidden first/last-wins fields cannot survive archive validation.
            let raw: UniqueJson =
                serde_json::from_str(receipt).map_err(|_| Error::CorruptHistory)?;
            self.restore_record_value(&raw.0)?;
        }
        Ok(())
    }

    /// Replay engine-created typed outcomes under the same deterministic v1 rules as restore.
    pub fn replay(seed: Seed, receipts: &[Receipt]) -> Result<Self, Error> {
        let mut engine = Self::new(seed)?;
        for receipt in receipts {
            if engine.recorded(&receipt.request)?.is_some() {
                return Err(Error::CorruptHistory);
            }
            let rebuilt = engine.commit_recorded(receipt)?;
            if &rebuilt != receipt {
                return Err(Error::CorruptHistory);
            }
        }
        Ok(engine)
    }

    /// Read a completed historical boundary in this same branch and lineage.
    /// Original receipt scopes/provenance are retained. This cannot add history,
    /// grant observer access, create a branch or call inference.
    pub fn at_revision(&self, at: u64) -> Result<Self, Error> {
        if at > self.revision()
            || (at != 0 && !self.records.iter().any(|r| r.last_revision() == at))
        {
            return Err(Error::Rule);
        }
        if at == self.revision() {
            return Ok(self.clone());
        }
        let mut result = Self::new(self.seed.clone())?;
        result.lineage = self.lineage.clone();
        for record in &self.records {
            if record.last_revision() > at {
                break;
            }
            result.scope = record.original_scope().clone();
            result.restore_record_value(
                &serde_json::to_value(record).map_err(|_| Error::CorruptHistory)?,
            )?;
        }
        result.scope = self.scope.clone();
        Ok(result)
    }

    /// Fork only at completed turn boundaries using this already validated snapshot.
    pub fn fork(&self, child: &str, at: u64) -> Result<Self, Error> {
        if !valid_id(child) {
            return Err(Error::Rule);
        }
        let mut lineage = self.lineage.clone();
        lineage.fork(&self.scope, child, at, self.revision())?;
        let mut result = self.at_revision(at)?;
        result.lineage = lineage;
        result.scope = Scope {
            story: self.scope.story.clone(),
            branch: child.into(),
        };
        Ok(result)
    }

    fn actor_event_eligible(
        &self,
        observer: &str,
        scope: &Scope,
        revision: u64,
        event: &AcceptedEvent,
    ) -> bool {
        self.lineage
            .eligible(scope, revision, &event.scope, event.sequence)
            && event.witnesses.contains(observer)
    }

    /// Visit borrowed accepted observations after eligibility, without cloning history.
    /// `revision` must be the current head; the range is (after, through]. A false
    /// visitor stops normally. Cancellation is checked at least every 32 scanned
    /// events, including hidden events, and before each eligible callback.
    /// Actor selection is a trusted caller responsibility; this grants no wire privilege.
    #[allow(clippy::too_many_arguments)] // Keep scope/basis/range explicit at this narrow read port.
    pub fn visit_actor_observations(
        &self,
        observer: &str,
        scope: &Scope,
        revision: u64,
        after: u64,
        through: u64,
        cancel: &dyn Fn() -> bool,
        visitor: &mut dyn FnMut(&AcceptedEvent) -> bool,
    ) -> Result<(), Error> {
        if self.domain_version() != 1 {
            return Err(Error::Version);
        }
        if scope != &self.scope {
            return Err(Error::Scope);
        }
        if revision != self.revision() {
            return Err(Error::Stale);
        }
        if !self.state.actors.contains_key(observer) {
            return Err(Error::UnknownReference);
        }
        if after > through || through > revision {
            return Err(Error::Rule);
        }
        if cancel() {
            return Err(Error::Cancelled);
        }
        for (index, event) in self
            .records
            .iter()
            .filter_map(CanonicalRecord::receipt)
            .flat_map(|r| &r.events)
            .enumerate()
        {
            if index % 32 == 0 && cancel() {
                return Err(Error::Cancelled);
            }
            if event.sequence > after
                && event.sequence <= through
                && self.actor_event_eligible(observer, scope, revision, event)
            {
                if cancel() {
                    return Err(Error::Cancelled);
                }
                if !visitor(event) {
                    return Ok(());
                }
            }
        }
        if cancel() {
            return Err(Error::Cancelled);
        }
        Ok(())
    }

    pub fn character_context(
        &self,
        observer: &str,
        scope: &Scope,
        revision: u64,
    ) -> Result<CharacterContext, Error> {
        if self.domain_version() != 1 {
            return Err(Error::Version);
        }
        if scope != &self.scope {
            return Err(Error::Scope);
        }
        // Historical context requires a separately rebuilt projection, never today's sheet at an old head.
        if revision != self.revision() {
            return Err(Error::Stale);
        }
        let actor = self
            .state
            .actors
            .get(observer)
            .ok_or(Error::UnknownReference)?
            .clone();
        let facts = self
            .seed
            .facts
            .iter()
            .filter(|(id, fact)| {
                fact.known_by.contains(observer)
                    || self
                        .state
                        .discoveries
                        .get(*id)
                        .is_some_and(|s| s.contains(observer))
            })
            .map(|(id, fact)| (id.clone(), fact.proposition.clone()))
            .collect();
        let observations = self
            .records
            .iter()
            .filter_map(CanonicalRecord::receipt)
            .flat_map(|r| &r.events)
            .filter(|event| self.actor_event_eligible(observer, scope, revision, event))
            .cloned()
            .collect();
        Ok(CharacterContext {
            version: VERSION,
            scope: scope.clone(),
            revision,
            observer: observer.into(),
            seed_source: self.seed.id.clone(),
            self_state: actor,
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

pub(crate) fn valid_id(id: &str) -> bool {
    !id.is_empty()
        && id.len() <= 64
        && id
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b"-_".contains(&b))
}

fn validate_seed(seed: &Seed) -> Result<(), Error> {
    if seed.version != VERSION {
        return Err(Error::Version);
    }
    if !valid_id(&seed.id)
        || !valid_id(&seed.scope.story)
        || !valid_id(&seed.scope.branch)
        || !seed.actors.contains_key(&seed.player)
    {
        return Err(Error::Rule);
    }
    for (id, actor) in &seed.actors {
        if !valid_id(id)
            || !seed.locations.contains(&actor.location)
            || actor.energy > 100
            || actor.attributes.values().any(|v| !(-100..=100).contains(v))
        {
            return Err(Error::Rule);
        }
        if seed.profile == Profile::NarrativeV1
            && (!actor.abilities.is_empty() || actor.energy != 0 || !actor.attributes.is_empty())
        {
            return Err(Error::Rule);
        }
        for (ability, rank) in &actor.abilities {
            let definition = seed.abilities.get(ability).ok_or(Error::Ability)?;
            if *rank == 0
                || *rank > definition.max_rank
                || definition
                    .prerequisite
                    .as_ref()
                    .is_some_and(|p| !actor.abilities.contains_key(p))
            {
                return Err(Error::Ability);
            }
        }
    }
    for (id, item) in &seed.items {
        if !valid_id(id)
            || item.quantity == 0
            || !seed.actors.contains_key(&item.owner)
            || item
                .return_to
                .as_ref()
                .is_some_and(|id| !seed.actors.contains_key(id))
        {
            return Err(Error::Inventory);
        }
    }
    for (id, ability) in &seed.abilities {
        if !valid_id(id)
            || ability.max_rank == 0
            || ability.cost > 100
            || !seed.actors.contains_key(&ability.teacher)
            || ability
                .prerequisite
                .as_ref()
                .is_some_and(|p| p == id || !seed.abilities.contains_key(p))
        {
            return Err(Error::Ability);
        }
    }
    if seed.profile == Profile::NarrativeV1 && !seed.abilities.is_empty() {
        return Err(Error::Rule);
    }
    for (from, to) in &seed.routes {
        if !seed.locations.contains(from) || !seed.locations.contains(to) {
            return Err(Error::Location);
        }
    }
    for (id, fact) in &seed.facts {
        if !valid_id(id)
            || fact.proposition.len() > MAX_TEXT_BYTES
            || fact.known_by.iter().any(|id| !seed.actors.contains_key(id))
            || fact
                .discoverable_at
                .as_ref()
                .is_some_and(|l| !seed.locations.contains(l))
        {
            return Err(Error::Knowledge);
        }
    }
    let mut edges = BTreeSet::new();
    for edge in &seed.relationships {
        if !seed.actors.contains_key(&edge.from)
            || !seed.actors.contains_key(&edge.to)
            || !edges.insert((&edge.from, &edge.to))
            || [edge.respect, edge.trust, edge.obligation]
                .iter()
                .any(|v| !(-100..=100).contains(v))
        {
            return Err(Error::Rule);
        }
    }
    for belief in &seed.beliefs {
        if !seed.actors.contains_key(&belief.believer)
            || belief.proposition.len() > MAX_TEXT_BYTES
            || belief.source != Evidence::Seed(seed.id.clone())
            || belief.source_claim.is_some()
        {
            return Err(Error::Knowledge);
        }
    }
    for (id, promise) in &seed.commitments {
        if !valid_id(id)
            || !seed.actors.contains_key(&promise.from)
            || !seed.actors.contains_key(&promise.to)
            || promise.source != Evidence::Seed(seed.id.clone())
            || promise.completed_by.is_some()
            || promise.terms.len() > MAX_TEXT_BYTES
            || promise
                .return_item
                .as_ref()
                .is_some_and(|item| !seed.items.contains_key(item))
        {
            return Err(Error::Rule);
        }
    }
    Ok(())
}

fn colocated(state: &Projection, actor: &str, other: &str) -> Result<(), Error> {
    let a = state.actors.get(actor).ok_or(Error::UnknownReference)?;
    let b = state.actors.get(other).ok_or(Error::UnknownReference)?;
    if !b.alive {
        return Err(Error::DeadActor);
    }
    if a.location != b.location {
        return Err(Error::Location);
    }
    Ok(())
}

type Resolved = (Effect, BTreeSet<String>, BTreeSet<String>);
fn resolve(
    seed: &Seed,
    state: &mut Projection,
    command: &Command,
    sequence: u64,
    domain_two: bool,
) -> Result<Resolved, Error> {
    let player = &seed.player;
    let actor = state
        .actors
        .get(player)
        .ok_or(Error::UnknownReference)?
        .clone();
    if !actor.alive {
        return Err(Error::DeadActor);
    }
    let mut participants: BTreeSet<String> = [player.clone()].into();
    let mut witnesses = participants.clone();
    let effect = match command {
        Command::Give { item, to, quantity } => {
            colocated(state, player, to)?;
            if to == player {
                return Err(Error::Inventory);
            }
            let held = state.items.get_mut(item).ok_or(Error::Inventory)?;
            // A stack is one instance in v1: full-stack transfers only; no implicit split IDs.
            if held.owner != *player || *quantity == 0 || *quantity != held.quantity {
                return Err(Error::Inventory);
            }
            if held.return_to.as_ref().is_some_and(|lender| lender != to) {
                return Err(Error::Inventory);
            }
            let qualifying_help = held.healing && held.return_to.is_none();
            held.owner = to.clone();
            if held.return_to.as_ref() == Some(to) {
                held.return_to = None;
            }
            participants.insert(to.clone());
            witnesses.insert(to.clone());
            // Helping creates obligation only; trust, respect and affection are not inferred.
            if let Some(edge) = state
                .relationships
                .iter_mut()
                .find(|r| qualifying_help && r.from == *to && r.to == *player)
            {
                edge.obligation = edge.obligation.saturating_add(1).min(100);
                state
                    .progression_sources
                    .insert(format!("relationship:{to}:{player}:obligation"), sequence);
            }
            state
                .progression_sources
                .insert(format!("item:{item}"), sequence);
            state.item_transfers.insert(
                item.clone(),
                TransferEvidence {
                    from: player.clone(),
                    to: to.clone(),
                    sequence,
                    story_time: state.story_time,
                },
            );
            Effect::Given {
                item: item.clone(),
                from: player.clone(),
                to: to.clone(),
                quantity: *quantity,
            }
        }
        Command::Consume { item } => {
            let held = state.items.get(item).ok_or(Error::Inventory)?;
            if held.owner != *player || held.quantity == 0 || held.return_to.is_some() {
                return Err(Error::Inventory);
            }
            if !held.healing || seed.profile != Profile::FantasyV1 {
                return Err(Error::Rule);
            }
            let healed = actor.injuries.first().cloned();
            if healed.is_none() {
                return Err(Error::Rule);
            }
            let held = state.items.get_mut(item).ok_or(Error::Inventory)?;
            held.quantity -= 1;
            if held.quantity == 0 {
                state.items.remove(item);
            }
            if let Some(injury) = &healed {
                state
                    .actors
                    .get_mut(player)
                    .ok_or(Error::UnknownReference)?
                    .injuries
                    .remove(injury);
            }
            state
                .progression_sources
                .insert(format!("item:{item}"), sequence);
            state
                .progression_sources
                .insert(format!("injuries:{player}"), sequence);
            Effect::Consumed {
                item: item.clone(),
                actor: player.clone(),
                healed,
            }
        }
        Command::UseAbility { ability } => {
            if seed.profile != Profile::FantasyV1 || !actor.abilities.contains_key(ability) {
                return Err(Error::Ability);
            }
            let definition = seed.abilities.get(ability).ok_or(Error::Ability)?;
            if definition
                .prerequisite
                .as_ref()
                .is_some_and(|p| !actor.abilities.contains_key(p))
            {
                return Err(Error::Ability);
            }
            let remaining = actor
                .energy
                .checked_sub(definition.cost)
                .ok_or(Error::Resource)?;
            state
                .actors
                .get_mut(player)
                .ok_or(Error::UnknownReference)?
                .energy = remaining;
            state
                .progression_sources
                .insert(format!("energy:{player}"), sequence);
            Effect::AbilityUsed {
                actor: player.clone(),
                ability: ability.clone(),
                cost: definition.cost,
            }
        }
        Command::Learn { ability } => {
            if seed.profile != Profile::FantasyV1 {
                return Err(Error::Ability);
            }
            let definition = seed.abilities.get(ability).ok_or(Error::Ability)?;
            colocated(state, player, &definition.teacher)?;
            if !state.actors[&definition.teacher]
                .abilities
                .contains_key(ability)
                || definition
                    .prerequisite
                    .as_ref()
                    .is_some_and(|p| !actor.abilities.contains_key(p))
            {
                return Err(Error::Ability);
            }
            let rank = actor
                .abilities
                .get(ability)
                .copied()
                .unwrap_or(0)
                .checked_add(1)
                .ok_or(Error::Ability)?;
            if rank > definition.max_rank {
                return Err(Error::Ability);
            }
            state
                .actors
                .get_mut(player)
                .ok_or(Error::UnknownReference)?
                .abilities
                .insert(ability.clone(), rank);
            state
                .progression_sources
                .insert(format!("ability:{player}:{ability}"), sequence);
            participants.insert(definition.teacher.clone());
            witnesses.insert(definition.teacher.clone());
            Effect::Learned {
                actor: player.clone(),
                ability: ability.clone(),
                rank,
            }
        }
        Command::Move { to } => {
            if !seed.routes.contains(&(actor.location.clone(), to.clone())) {
                return Err(Error::Location);
            }
            state
                .actors
                .get_mut(player)
                .ok_or(Error::UnknownReference)?
                .location = to.clone();
            state
                .progression_sources
                .insert(format!("location:{player}"), sequence);
            Effect::Moved {
                actor: player.clone(),
                from: actor.location,
                to: to.clone(),
            }
        }
        Command::Say { text, audience } => {
            if text.is_empty() || text.len() > MAX_TEXT_BYTES || audience.is_empty() {
                return Err(Error::TooLarge);
            }
            for listener in audience {
                colocated(state, player, listener)?;
            }
            participants.extend(audience.iter().cloned());
            witnesses.extend(audience.iter().cloned());
            let claim = Claim {
                speaker: player.clone(),
                text: text.clone(),
                audience: audience.clone(),
                source: sequence,
            };
            state.claims.push(claim.clone());
            Effect::Said(claim)
        }
        Command::Believe { claim_event } => {
            let claim = state
                .claims
                .iter()
                .find(|c| {
                    c.source == *claim_event
                        && (c.audience.contains(player) || c.speaker == *player)
                })
                .ok_or(Error::Knowledge)?;
            let belief = Belief {
                believer: player.clone(),
                proposition: claim.text.clone(),
                source_claim: Some(*claim_event),
                source: Evidence::Event(sequence),
                confidence: Confidence::Uncertain,
            };
            state.beliefs.push(belief.clone());
            Effect::Believed(belief)
        }
        Command::Discover { fact } => {
            let truth = seed.facts.get(fact).ok_or(Error::Knowledge)?;
            if truth.discoverable_at.as_ref() != Some(&actor.location)
                || (!domain_two
                    && (truth.known_by.contains(player)
                        || state
                            .discoveries
                            .get(fact)
                            .is_some_and(|s| s.contains(player))))
            {
                return Err(Error::Knowledge);
            }
            state
                .discoveries
                .entry(fact.clone())
                .or_default()
                .insert(player.clone());
            Effect::Discovered {
                actor: player.clone(),
                fact: fact.clone(),
            }
        }
        Command::Promise {
            id,
            to,
            terms,
            deadline,
            return_item,
        } => {
            colocated(state, player, to)?;
            if !valid_id(id)
                || terms.is_empty()
                || terms.len() > MAX_TEXT_BYTES
                || *deadline <= state.story_time
                || state.commitments.contains_key(id)
            {
                return Err(Error::Rule);
            }
            if return_item
                .as_ref()
                .is_some_and(|item| !state.items.contains_key(item))
            {
                return Err(Error::Inventory);
            }
            participants.insert(to.clone());
            witnesses.insert(to.clone());
            let commitment = Commitment {
                from: player.clone(),
                to: to.clone(),
                terms: terms.clone(),
                deadline: *deadline,
                source: Evidence::Event(sequence),
                return_item: return_item.clone(),
                completed_by: None,
            };
            state.commitments.insert(id.clone(), commitment.clone());
            Effect::Promised {
                id: id.clone(),
                commitment,
            }
        }
        Command::CompletePromise { id } => {
            let promise = state.commitments.get(id).ok_or(Error::Rule)?;
            if promise.from != *player || promise.completed_by.is_some() {
                return Err(Error::Rule);
            }
            let item = promise.return_item.as_ref().ok_or(Error::Rule)?;
            let held = state.items.get(item).ok_or(Error::Inventory)?;
            if held.owner != promise.to || held.return_to.is_some() {
                return Err(Error::Inventory);
            }
            let transfer = state.item_transfers.get(item).ok_or(Error::Rule)?;
            if transfer.from != *player
                || transfer.to != promise.to
                || transfer.story_time > promise.deadline
            {
                return Err(Error::Rule);
            }
            let return_event = transfer.sequence;
            if let Evidence::Event(source) = promise.source {
                if return_event <= source {
                    return Err(Error::Rule);
                }
            }
            participants.insert(promise.to.clone());
            // Fulfillment is a local ledger inference; it does not telepathically notify the creditor.
            state
                .commitments
                .get_mut(id)
                .ok_or(Error::Rule)?
                .completed_by = Some(sequence);
            Effect::PromiseCompleted {
                id: id.clone(),
                return_event,
            }
        }
        Command::Wait { ticks } => {
            if *ticks == 0 || *ticks > 100 {
                return Err(Error::Rule);
            }
            let from = state.story_time;
            state.story_time = from.checked_add(u64::from(*ticks)).ok_or(Error::Resource)?;
            Effect::TimeAdvanced {
                from,
                to: state.story_time,
            }
        }
    };
    Ok((effect, participants, witnesses))
}

/// Bounded serialization count without allocating a copy of an unbounded input.
pub(crate) fn check_json_budget(value: &impl Serialize, cap: usize) -> Result<(), Error> {
    struct Counter {
        remaining: usize,
    }
    impl std::io::Write for Counter {
        fn write(&mut self, bytes: &[u8]) -> std::io::Result<usize> {
            self.remaining = self
                .remaining
                .checked_sub(bytes.len())
                .ok_or_else(|| std::io::Error::other("bounded input exceeded"))?;
            Ok(bytes.len())
        }
        fn flush(&mut self) -> std::io::Result<()> {
            Ok(())
        }
    }
    serde_json::to_writer(&mut Counter { remaining: cap }, value).map_err(|_| Error::TooLarge)
}

/// Restricted safe narration for the contract harness, not an attempted free-form prose validator.
pub fn render(events: &[AcceptedEvent]) -> String {
    events
        .iter()
        .map(|e| match &e.outcome {
            Effect::Given {
                item, to, quantity, ..
            } => format!("You give {quantity} {item} to {to}."),
            Effect::Consumed { item, .. } => format!("You use {item}; your injury improves."),
            Effect::AbilityUsed { ability, cost, .. } => {
                format!("You use {ability}, spending {cost} energy.")
            }
            Effect::Learned { ability, rank, .. } => format!("You learn {ability} at rank {rank}."),
            Effect::Moved { to, .. } => format!("You move to {to}."),
            Effect::Said(_) => "Your words are heard by the chosen listeners.".into(),
            Effect::Believed(_) => "You consider the statement uncertain.".into(),
            Effect::Discovered { .. } => "You discover evidence here.".into(),
            Effect::Promised { .. } => "Your promise is recorded.".into(),
            Effect::PromiseCompleted { .. } => "The recorded return fulfills your promise.".into(),
            Effect::TimeAdvanced { from, to } => {
                format!("Story time advances from {from} to {to}.")
            }
        })
        .collect::<Vec<_>>()
        .join(" ")
}
