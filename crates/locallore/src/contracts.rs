pub use crate::story_presentation::{StoryPresentationV1, StoryTone};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};

pub const VERSION: u16 = 1;
pub const MAX_COMMANDS: usize = 8;
pub const MAX_TEXT_BYTES: usize = 2048;
pub const MAX_PROPOSAL_BYTES: usize = 16_384;
/// Complete persisted v1 root-history budgets; shared with the storage owner.
pub const MAX_HISTORY_RECEIPTS: usize = 4096;
pub const MAX_RECEIPT_BYTES: usize = 65_536;
pub const MAX_HISTORY_BYTES: usize = 16 * 1024 * 1024;

#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
#[cfg_attr(feature = "host", derive(schemars::JsonSchema))]
pub struct Scope {
    pub story: String,
    pub branch: String,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Profile {
    FantasyV1,
    NarrativeV1,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Actor {
    pub name: String,
    pub location: String,
    pub alive: bool,
    pub energy: u16,
    pub abilities: BTreeMap<String, u16>,
    pub attributes: BTreeMap<String, i16>,
    pub injuries: BTreeSet<String>,
    pub affiliations: BTreeSet<String>,
    pub goals: BTreeSet<String>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Item {
    pub owner: String,
    pub quantity: u16,
    /// A loan is possession plus an immutable return obligation, not a title transfer.
    pub return_to: Option<String>,
    pub healing: bool,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Ability {
    pub cost: u16,
    pub prerequisite: Option<String>,
    pub teacher: String,
    pub max_rank: u16,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Fact {
    pub proposition: String,
    pub discoverable_at: Option<String>,
    pub known_by: BTreeSet<String>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Relationship {
    pub from: String,
    pub to: String,
    pub respect: i16,
    pub trust: i16,
    pub obligation: i16,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Seed {
    pub version: u16,
    pub id: String,
    pub scope: Scope,
    pub profile: Profile,
    pub player: String,
    pub locations: BTreeSet<String>,
    pub routes: BTreeSet<(String, String)>,
    pub actors: BTreeMap<String, Actor>,
    pub items: BTreeMap<String, Item>,
    pub abilities: BTreeMap<String, Ability>,
    pub facts: BTreeMap<String, Fact>,
    pub relationships: Vec<Relationship>,
    pub story_time: u64,
    pub beliefs: Vec<Belief>,
    pub commitments: BTreeMap<String, Commitment>,
    /// Absent from exact legacy Seed bytes. Initial configuration, not world truth.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub presentation: Option<StoryPresentationV1>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "op", rename_all = "snake_case", deny_unknown_fields)]
#[cfg_attr(feature = "host", derive(schemars::JsonSchema))]
pub enum Command {
    Give {
        item: String,
        to: String,
        quantity: u16,
    },
    Consume {
        item: String,
    },
    UseAbility {
        ability: String,
    },
    Learn {
        ability: String,
    },
    Move {
        to: String,
    },
    Say {
        text: String,
        audience: BTreeSet<String>,
    },
    Believe {
        claim_event: u64,
    },
    Discover {
        fact: String,
    },
    Promise {
        id: String,
        to: String,
        terms: String,
        deadline: u64,
        return_item: Option<String>,
    },
    CompletePromise {
        id: String,
    },
    Wait {
        ticks: u16,
    },
}

/// This comes from explicit UI selection/clarification, never the model's interpretation alone.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(
    tag = "kind",
    content = "value",
    rename_all = "snake_case",
    deny_unknown_fields
)]
#[cfg_attr(feature = "host", derive(schemars::JsonSchema))]
pub enum Intent {
    Actions(Vec<Command>),
    Dialogue {
        text: String,
        audience: BTreeSet<String>,
    },
    Thought(String),
    Ambiguous(String),
    AuthorCorrection(String),
    /// Explicit untrusted player input; the versioned play pipeline interprets it once.
    FreeText {
        kind: PlayInputKind,
        text: String,
    },
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[cfg_attr(feature = "host", derive(schemars::JsonSchema))]
pub enum PlayInputKind {
    Action,
    Dialogue,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
#[cfg_attr(feature = "host", derive(schemars::JsonSchema))]
pub struct Request {
    pub version: u16,
    pub scope: Scope,
    pub turn: String,
    pub expected_revision: u64,
    pub intent: Intent,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Proposal {
    pub version: u16,
    pub scope: Scope,
    pub turn: String,
    pub expected_revision: u64,
    pub commands: Vec<Command>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct Claim {
    pub speaker: String,
    pub text: String,
    pub audience: BTreeSet<String>,
    pub source: u64,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(
    tag = "kind",
    content = "value",
    rename_all = "snake_case",
    deny_unknown_fields
)]
pub enum Evidence {
    Seed(String),
    Event(u64),
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Confidence {
    Uncertain,
    Suspected,
    Believed,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Belief {
    pub believer: String,
    pub proposition: String,
    pub source_claim: Option<u64>,
    pub source: Evidence,
    pub confidence: Confidence,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Commitment {
    pub from: String,
    pub to: String,
    pub terms: String,
    pub deadline: u64,
    pub source: Evidence,
    pub return_item: Option<String>,
    pub completed_by: Option<u64>,
}

impl Commitment {
    pub fn status(&self, story_time: u64) -> &'static str {
        if self.completed_by.is_some() {
            "fulfilled"
        } else if story_time > self.deadline {
            "overdue"
        } else {
            "open"
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct Projection {
    pub actors: BTreeMap<String, Actor>,
    pub items: BTreeMap<String, Item>,
    pub claims: Vec<Claim>,
    pub beliefs: Vec<Belief>,
    pub discoveries: BTreeMap<String, BTreeSet<String>>,
    pub relationships: Vec<Relationship>,
    pub commitments: BTreeMap<String, Commitment>,
    /// Projection field -> latest change event; seed fields cite seed:<id> separately.
    pub progression_sources: BTreeMap<String, u64>,
    pub story_time: u64,
    pub item_transfers: BTreeMap<String, TransferEvidence>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct TransferEvidence {
    pub from: String,
    pub to: String,
    pub sequence: u64,
    pub story_time: u64,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
#[serde(tag = "effect", rename_all = "snake_case")]
pub enum Effect {
    Given {
        item: String,
        from: String,
        to: String,
        quantity: u16,
    },
    Consumed {
        item: String,
        actor: String,
        healed: Option<String>,
    },
    AbilityUsed {
        actor: String,
        ability: String,
        cost: u16,
    },
    Learned {
        actor: String,
        ability: String,
        rank: u16,
    },
    Moved {
        actor: String,
        from: String,
        to: String,
    },
    Said(Claim),
    Believed(Belief),
    Discovered {
        actor: String,
        fact: String,
    },
    Promised {
        id: String,
        commitment: Commitment,
    },
    PromiseCompleted {
        id: String,
        return_event: u64,
    },
    TimeAdvanced {
        from: u64,
        to: u64,
    },
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct AcceptedEvent {
    pub(crate) version: u16,
    pub(crate) scope: Scope,
    pub(crate) sequence: u64,
    pub(crate) turn: String,
    pub(crate) rules: Profile,
    pub(crate) seed: String,
    pub(crate) story_time: u64,
    pub(crate) participants: BTreeSet<String>,
    pub(crate) witnesses: BTreeSet<String>,
    pub(crate) outcome: Effect,
}

impl AcceptedEvent {
    pub fn sequence(&self) -> u64 {
        self.sequence
    }
    pub fn outcome(&self) -> &Effect {
        &self.outcome
    }
    pub fn scope(&self) -> &Scope {
        &self.scope
    }
    pub fn witnesses(&self) -> &BTreeSet<String> {
        &self.witnesses
    }
}

/// Constructed only by the engine. No Deserialize or public field construction for accepted history.
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct Receipt {
    pub(crate) request: Request,
    pub(crate) proposal: Proposal,
    pub(crate) events: Vec<AcceptedEvent>,
    pub(crate) narration: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub(crate) play: Option<crate::play::PlayRecord>,
}

impl Receipt {
    pub fn request(&self) -> &Request {
        &self.request
    }
    pub fn proposal(&self) -> &Proposal {
        &self.proposal
    }
    pub fn events(&self) -> &[AcceptedEvent] {
        &self.events
    }
    pub fn narration(&self) -> &str {
        &self.narration
    }
    pub fn play(&self) -> Option<&crate::play::PlayRecord> {
        self.play.as_ref()
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Version,
    Scope,
    Stale,
    RetryMismatch,
    Malformed,
    TooLarge,
    Agency,
    AuthorUiRequired,
    ClarificationRequired,
    UnknownReference,
    DeadActor,
    Location,
    Inventory,
    Resource,
    Ability,
    Knowledge,
    Rule,
    Cancelled,
    Provider,
    Timeout,
    Narration,
    CorruptHistory,
}

impl std::fmt::Display for Error {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{self:?}")
    }
}
impl std::error::Error for Error {}

impl Proposal {
    pub fn parse(bytes: &[u8]) -> Result<Self, Error> {
        if bytes.len() > MAX_PROPOSAL_BYTES {
            return Err(Error::TooLarge);
        }
        let proposal: Self = serde_json::from_slice(bytes).map_err(|_| Error::Malformed)?;
        if proposal.version != VERSION {
            return Err(Error::Version);
        }
        if proposal.commands.is_empty() || proposal.commands.len() > MAX_COMMANDS {
            return Err(Error::TooLarge);
        }
        Ok(proposal)
    }
}
