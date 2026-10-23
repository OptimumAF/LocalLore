use crate::{contracts::*, scope::Lineage};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};

#[derive(Clone, Debug)]
pub struct Engine {
    seed: Seed,
    scope: Scope,
    lineage: Lineage,
    state: Projection,
    receipts: Vec<Receipt>,
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

pub(crate) fn parse_unique<T: serde::de::DeserializeOwned>(bytes: &[u8]) -> Result<T, Error> {
    let raw: UniqueJson = serde_json::from_slice(bytes).map_err(|_| Error::Malformed)?;
    serde_json::from_value(raw.0).map_err(|_| Error::Malformed)
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
            receipts: vec![],
        })
    }

    pub fn scope(&self) -> &Scope {
        &self.scope
    }
    pub fn seed(&self) -> &Seed {
        &self.seed
    }
    pub fn state(&self) -> &Projection {
        &self.state
    }
    pub fn receipts(&self) -> &[Receipt] {
        &self.receipts
    }
    pub fn revision(&self) -> u64 {
        self.receipts
            .last()
            .and_then(|r| r.events.last())
            .map_or(0, |e| e.sequence)
    }

    /// Stable canonical projection encoding: struct field order and ordered maps/sets, no floats.
    /// Not an archive format or cryptographic integrity guarantee.
    pub fn canonical_bytes(&self) -> Vec<u8> {
        serde_json::to_vec(&self.state).expect("projection is serializable")
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
        if let Some(receipt) = self
            .receipts
            .iter()
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
            crate::play::validate_interpretation(request, proposal)?;
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
            let (outcome, participants, witnesses) =
                resolve(&self.seed, &mut staged, command, sequence)?;
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
        let mut staged = self.state.clone();
        for (command, event) in proposal.commands.iter().zip(&receipt.events) {
            let _ = resolve(&self.seed, &mut staged, command, event.sequence)?;
        }
        self.state = staged;
        self.receipts.push(receipt.clone());
        Ok(receipt)
    }

    /// Only a versioned generated-play record can relax v1's exact-rendered narration rule.
    pub fn commit_play(
        &mut self,
        request: &Request,
        proposal: &Proposal,
        record: &crate::play::PlayRecord,
    ) -> Result<Receipt, Error> {
        if let Some(receipt) = self.recorded(request)? {
            return Ok(receipt);
        }
        if !matches!(request.intent, Intent::FreeText { .. }) {
            return Err(Error::Agency);
        }
        let mut receipt = self.preview(request, proposal)?;
        crate::play::validate_record(self, &receipt, record)?;
        receipt.narration = record.narration.text.clone();
        receipt.play = Some(record.clone());
        let mut staged = self.state.clone();
        for (command, event) in proposal.commands.iter().zip(&receipt.events) {
            let _ = resolve(&self.seed, &mut staged, command, event.sequence)?;
        }
        self.state = staged;
        self.receipts.push(receipt.clone());
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

    /// Restore bounded complete persisted root-history receipts, never a supplied projection.
    /// V1 rules are deterministic: rebuilding verifies every recorded resolved outcome. Future
    /// random rules require an explicit recorded-outcome contract; they must not reroll here.
    /// No inference provider or random source is used. No partially restored engine is returned.
    pub fn restore(seed: Seed, history: &[String]) -> Result<Self, Error> {
        if history.len() > MAX_HISTORY_RECEIPTS {
            return Err(Error::TooLarge);
        }
        let mut total = 0usize;
        for receipt in history {
            total = total.checked_add(receipt.len()).ok_or(Error::TooLarge)?;
            if receipt.len() > MAX_RECEIPT_BYTES || total > MAX_HISTORY_BYTES {
                return Err(Error::TooLarge);
            }
        }
        let mut engine = Self::new(seed)?;
        for receipt in history {
            // Value normally accepts repeated object keys. Reject them recursively before typed
            // parsing so hidden first/last-wins fields cannot survive archive validation.
            let raw: UniqueJson =
                serde_json::from_str(receipt).map_err(|_| Error::CorruptHistory)?;
            let recorded: PersistedReceipt =
                serde_json::from_value(raw.0.clone()).map_err(|_| Error::CorruptHistory)?;
            if recorded.events.is_empty()
                || recorded.events.len() > MAX_COMMANDS
                || engine
                    .recorded(&recorded.request)
                    .map_err(|_| Error::CorruptHistory)?
                    .is_some()
            {
                return Err(Error::CorruptHistory);
            }
            let rebuilt = if let Some(play) = &recorded.play {
                if play.narration.text != recorded.narration {
                    return Err(Error::CorruptHistory);
                }
                engine.commit_play(&recorded.request, &recorded.proposal, play)
            } else {
                engine.commit(&recorded.request, &recorded.proposal, &recorded.narration)
            }
            .map_err(|_| Error::CorruptHistory)?;
            // Full JSON equality rejects unknown envelope/effect fields, forged witnesses,
            // provenance, order, scope, sequence and effects. Object key order is irrelevant.
            if serde_json::to_value(rebuilt).map_err(|_| Error::CorruptHistory)? != raw.0 {
                return Err(Error::CorruptHistory);
            }
        }
        Ok(engine)
    }

    /// Replay engine-created typed outcomes under the same deterministic v1 rules as restore.
    pub fn replay(seed: Seed, receipts: &[Receipt]) -> Result<Self, Error> {
        let mut engine = Self::new(seed)?;
        for receipt in receipts {
            if engine.recorded(&receipt.request)?.is_some() {
                return Err(Error::CorruptHistory);
            }
            let rebuilt = engine.commit_prepared(receipt)?;
            if &rebuilt != receipt {
                return Err(Error::CorruptHistory);
            }
        }
        Ok(engine)
    }

    /// Forks only at completed turn boundaries. Rebuild from seed, never clone a stale projection.
    pub fn fork(&self, child: &str, at: u64) -> Result<Self, Error> {
        if !valid_id(child) {
            return Err(Error::Rule);
        }
        if at != 0
            && !self
                .receipts
                .iter()
                .any(|r| r.events.last().is_some_and(|e| e.sequence == at))
        {
            return Err(Error::Rule);
        }
        let mut lineage = self.lineage.clone();
        lineage.fork(&self.scope, child, at, self.revision())?;
        let scope = Scope {
            story: self.scope.story.clone(),
            branch: child.into(),
        };
        let mut result = Self::new(self.seed.clone())?;
        result.lineage = lineage;
        for receipt in &self.receipts {
            if receipt.events.last().is_none_or(|e| e.sequence > at) {
                break;
            }
            result.scope = receipt.request.scope.clone();
            let rebuilt = result.commit_prepared(receipt)?;
            if rebuilt != *receipt {
                return Err(Error::CorruptHistory);
            }
        }
        result.scope = scope;
        Ok(result)
    }

    pub fn character_context(
        &self,
        observer: &str,
        scope: &Scope,
        revision: u64,
    ) -> Result<CharacterContext, Error> {
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
            .receipts
            .iter()
            .flat_map(|r| &r.events)
            .filter(|event| {
                self.lineage
                    .eligible(scope, revision, &event.scope, event.sequence)
                    && event.witnesses.contains(observer)
            })
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
                || truth.known_by.contains(player)
                || state
                    .discoveries
                    .get(fact)
                    .is_some_and(|s| s.contains(player))
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
