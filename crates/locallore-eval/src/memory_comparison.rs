//! Frozen comparison protocol/oracles only. No runner, provider, ledger or storage.
//! Recent-transcript execution stays Unsupported until the trusted Core policy exists.
use locallore::{
    context_compiler::ContextPackage,
    contracts::*,
    engine::{AcceptedHistoryBasis, Engine},
    inference::{GenerationRequest, Input},
    play::{PlayContextRecord, PlayProfile, PROMPT_VERSION},
};
use serde::Serialize;
use sha2::{Digest, Sha256};

pub const VERSION: u16 = 1;
pub const SUITE: &str = "memory-comparison-courier-v1";
pub const ATTEMPTS: usize = 24;
pub const MAX_PACKET_BYTES: usize = 128 * 1024;
const OPTIONAL_DETAIL: &str = "The pennant I carry has an amber stitch.";
const COMMON_EXCLUSIONS: &[&str] = &[
    "FOREIGN-COMPARISON",
    "SIBLING-COMPARISON",
    "PARENT-FUTURE-COMPARISON",
];
const NARRATOR_EXCLUSIONS: &[&str] = &["SECRET-TIDE-731"];
type Result<T> = std::result::Result<T, ProtocolError>;
fn hash(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}
fn encoded<T: Serialize + ?Sized>(value: &T) -> Result<Vec<u8>> {
    struct Bounded {
        bytes: Vec<u8>,
        capped: bool,
    }
    impl std::io::Write for Bounded {
        fn write(&mut self, bytes: &[u8]) -> std::io::Result<usize> {
            if self.bytes.len().saturating_add(bytes.len()) > 2 * 1024 * 1024 {
                self.capped = true;
                return Err(std::io::Error::other("comparison encoding budget"));
            }
            self.bytes.extend_from_slice(bytes);
            Ok(bytes.len())
        }
        fn flush(&mut self) -> std::io::Result<()> {
            Ok(())
        }
    }
    let mut writer = Bounded {
        bytes: Vec::new(),
        capped: false,
    };
    if serde_json::to_writer(&mut writer, value).is_err() {
        return Err(if writer.capped {
            ProtocolError::Budget
        } else {
            ProtocolError::Encoding
        });
    }
    Ok(writer.bytes)
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ProtocolError {
    Encoding,
    Binding,
    Budget,
    Order,
    Integrity,
    UnsupportedPolicy,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum HistoryPolicy {
    StateRecentTranscriptV1,
    StateRelevantMemoryV1,
}
/// This is a capability refusal, not a switch a caller can set to true.
pub fn require_execution(policy: HistoryPolicy) -> Result<()> {
    // Current 2.4 raw/verified reference observations have no policy field;
    // they cannot be relabeled as either executed 2.5 policy arm.
    match policy {
        HistoryPolicy::StateRecentTranscriptV1 | HistoryPolicy::StateRelevantMemoryV1 => {
            Err(ProtocolError::UnsupportedPolicy)
        }
    }
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ExperimentKind {
    PairedSnapshots,
    ContinuousRollout,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ProviderLane {
    Scripted,
    ApprovedNative,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
pub enum GuardRejection {
    Inventory,
    Ability,
    ClarificationRequired,
}
impl GuardRejection {
    fn core(self) -> Error {
        match self {
            Self::Inventory => Error::Inventory,
            Self::Ability => Error::Ability,
            Self::ClarificationRequired => Error::ClarificationRequired,
        }
    }
}
#[derive(Clone, Debug, Serialize)]
pub enum Expected {
    Accepted(Command),
    GuardRejected(GuardRejection),
}
#[derive(Clone, Debug, Serialize)]
pub struct Step {
    id: String,
    scene: u8,
    kind: PlayInputKind,
    text: String,
    expected: Expected,
}
impl Step {
    pub fn id(&self) -> &str {
        &self.id
    }
    pub fn scene(&self) -> u8 {
        self.scene
    }
    pub fn expected(&self) -> &Expected {
        &self.expected
    }
    pub fn text(&self) -> &str {
        &self.text
    }
    pub fn request(&self, engine: &Engine) -> Request {
        engine.request(
            &self.id,
            Intent::FreeText {
                kind: self.kind,
                text: self.text.clone(),
            },
        )
    }
}
#[derive(Clone, Debug, Serialize)]
pub struct FrozenSuite {
    version: u16,
    id: &'static str,
    seed: Seed,
    steps: Vec<Step>,
}
impl FrozenSuite {
    pub fn seed(&self) -> &Seed {
        &self.seed
    }
    pub fn steps(&self) -> &[Step] {
        &self.steps
    }
    pub fn sha256(&self) -> Result<String> {
        Ok(hash(&encoded(self)?))
    }
}
pub fn frozen_suite() -> Result<FrozenSuite> {
    let mut seed: Seed = serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json"))
        .map_err(|_| ProtocolError::Encoding)?;
    seed.id = SUITE.into();
    seed.scope.story = "memory-comparison-courier".into();
    seed.actors
        .get_mut(&seed.player)
        .ok_or(ProtocolError::Integrity)?
        .energy = 4;
    seed.routes.insert(("pier".into(), "tower".into()));
    seed.routes.insert(("tower".into(), "pier".into()));
    let mut bandage = seed.items["potion"].clone();
    bandage.healing = true;
    seed.items.insert("bandage".into(), bandage);
    let mut pennant = seed.items["potion"].clone();
    pennant.healing = false;
    seed.items.insert("pennant".into(), pennant);
    // Keep source evidence internally coherent in this NEW fixture, never edit old corpus.
    for b in &mut seed.beliefs {
        if let Evidence::Seed(id) = &mut b.source {
            *id = SUITE.into();
        }
    }
    for c in seed.commitments.values_mut() {
        if let Evidence::Seed(id) = &mut c.source {
            *id = SUITE.into();
        }
    }
    let say = |text: &str, to: &str| Command::Say {
        text: text.into(),
        audience: [to.into()].into(),
    };
    let rows = vec![
        (
            PlayInputKind::Dialogue,
            OPTIONAL_DETAIL,
            Expected::Accepted(say(OPTIONAL_DETAIL, "mira")),
        ),
        (
            PlayInputKind::Action,
            "I learn beacon.",
            Expected::Accepted(Command::Learn {
                ability: "beacon".into(),
            }),
        ),
        (
            PlayInputKind::Action,
            "I give bandage to mira.",
            Expected::Accepted(Command::Give {
                item: "bandage".into(),
                to: "mira".into(),
                quantity: 1,
            }),
        ),
        (
            PlayInputKind::Action,
            "I use beacon.",
            Expected::Accepted(Command::UseAbility {
                ability: "beacon".into(),
            }),
        ),
        (
            PlayInputKind::Action,
            "I move to pier.",
            Expected::Accepted(Command::Move { to: "pier".into() }),
        ),
        (
            PlayInputKind::Dialogue,
            "I will return the borrowed brass key before tide tick 120.",
            Expected::Accepted(say(
                "I will return the borrowed brass key before tide tick 120.",
                "oren",
            )),
        ),
        (
            PlayInputKind::Action,
            "I move to tower.",
            Expected::Accepted(Command::Move { to: "tower".into() }),
        ),
        (
            PlayInputKind::Dialogue,
            "You are the Oren who lives by the tower.",
            Expected::Accepted(say("You are the Oren who lives by the tower.", "sable")),
        ),
        (
            PlayInputKind::Action,
            "I give brass-key to sable.",
            Expected::GuardRejected(GuardRejection::Inventory),
        ),
        (
            PlayInputKind::Action,
            "I use blink.",
            Expected::GuardRejected(GuardRejection::Ability),
        ),
        (
            PlayInputKind::Action,
            "I move to pier.",
            Expected::Accepted(Command::Move { to: "pier".into() }),
        ),
        (
            PlayInputKind::Action,
            "I wait for one tide tick.",
            Expected::Accepted(Command::Wait { ticks: 1 }),
        ),
        (
            PlayInputKind::Action,
            "I move to quay.",
            Expected::Accepted(Command::Move { to: "quay".into() }),
        ),
        (
            PlayInputKind::Dialogue,
            "Oren at the tower is different from Oren at the pier.",
            Expected::Accepted(say(
                "Oren at the tower is different from Oren at the pier.",
                "mira",
            )),
        ),
        (
            PlayInputKind::Action,
            "I move to dry-well.",
            Expected::Accepted(Command::Move {
                to: "dry-well".into(),
            }),
        ),
        (
            PlayInputKind::Action,
            "I discover fact beacon-mark.",
            Expected::Accepted(Command::Discover {
                fact: "beacon-mark".into(),
            }),
        ),
        (
            PlayInputKind::Action,
            "I consume potion.",
            Expected::Accepted(Command::Consume {
                item: "potion".into(),
            }),
        ),
        (
            PlayInputKind::Action,
            "I move to quay.",
            Expected::Accepted(Command::Move { to: "quay".into() }),
        ),
        (
            PlayInputKind::Action,
            "I use steady.",
            Expected::Accepted(Command::UseAbility {
                ability: "steady".into(),
            }),
        ),
        (
            PlayInputKind::Dialogue,
            "I am returning the items I still carry.",
            Expected::Accepted(say("I am returning the items I still carry.", "mira")),
        ),
        (
            PlayInputKind::Action,
            "I move to pier.",
            Expected::Accepted(Command::Move { to: "pier".into() }),
        ),
        (
            PlayInputKind::Action,
            "I give pennant to oren.",
            Expected::Accepted(Command::Give {
                item: "pennant".into(),
                to: "oren".into(),
                quantity: 1,
            }),
        ),
        (
            PlayInputKind::Action,
            "I give brass-key to oren.",
            Expected::Accepted(Command::Give {
                item: "brass-key".into(),
                to: "oren".into(),
                quantity: 1,
            }),
        ),
        (
            PlayInputKind::Action,
            "I complete promise return-key.",
            Expected::GuardRejected(GuardRejection::ClarificationRequired),
        ),
    ];
    let steps = rows
        .into_iter()
        .enumerate()
        .map(|(i, (kind, text, expected))| Step {
            id: format!("courier-{:02}", i + 1),
            scene: (i / 6 + 1) as u8,
            kind,
            text: text.into(),
            expected,
        })
        .collect();
    Ok(FrozenSuite {
        version: VERSION,
        id: SUITE,
        seed,
        steps,
    })
}
/// Core's public finite guard and actual Engine preview own interpretation/mechanics.
/// This does NOT apply expected commands to a failed generated run.
pub fn reference_proposal(before: &Engine, step: &Step) -> std::result::Result<Proposal, Error> {
    let request = step.request(before);
    let command = match step.kind {
        PlayInputKind::Action => locallore::intent_guard::compile_action(before, &step.text)?,
        PlayInputKind::Dialogue => match &step.expected {
            Expected::Accepted(command) => command.clone(),
            _ => return Err(Error::Agency),
        },
    };
    let proposal = Proposal {
        version: request.version,
        scope: request.scope.clone(),
        turn: request.turn.clone(),
        expected_revision: request.expected_revision,
        commands: vec![command],
    };
    before.preview(&request, &proposal)?;
    Ok(proposal)
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum Outcome {
    Passed,
    Failed,
    GuardOnly,
    NotRunDependency,
}
pub enum ActualOutcome<'a> {
    Accepted(&'a Receipt),
    Rejected(Error),
    NotRunDependency,
}
#[derive(Clone, Debug, Serialize)]
#[serde(transparent)]
pub struct Failure(&'static str);
impl From<Error> for Failure {
    fn from(error: Error) -> Self {
        Self(match error {
            Error::Version => "Version",
            Error::Scope => "Scope",
            Error::Stale => "Stale",
            Error::RetryMismatch => "RetryMismatch",
            Error::Malformed => "Malformed",
            Error::TooLarge => "TooLarge",
            Error::Agency => "Agency",
            Error::AuthorUiRequired => "AuthorUiRequired",
            Error::ClarificationRequired => "ClarificationRequired",
            Error::UnknownReference => "UnknownReference",
            Error::DeadActor => "DeadActor",
            Error::Location => "Location",
            Error::Inventory => "Inventory",
            Error::Resource => "Resource",
            Error::Ability => "Ability",
            Error::Knowledge => "Knowledge",
            Error::Rule => "Rule",
            Error::Cancelled => "Cancelled",
            Error::Provider => "Provider",
            Error::Timeout => "Timeout",
            Error::Narration => "Narration",
            Error::CorruptHistory => "CorruptHistory",
        })
    }
}
#[derive(Clone, Debug, Serialize)]
pub struct TurnRow {
    pub id: String,
    pub scene: u8,
    pub outcome: Outcome,
    pub before_revision: u64,
    pub after_revision: u64,
    pub before_state_sha256: String,
    pub after_state_sha256: String,
    pub roles: usize,
    pub fallback: Option<bool>,
    pub error: Option<Failure>,
    pub receipt_sha256: Option<String>,
    pub mandatory_sha256: Option<String>,
    pub optional_detail_selected: Option<bool>,
    pub profile_sha256: Option<String>,
    pub model_profile: Option<String>,
    pub prompt_sha256: Vec<String>,
    pub schema_sha256: Vec<String>,
    pub receipt_context: Option<PlayContextRecord>,
    pub director_detail_present: Option<bool>,
    pub director_private_target_present: Option<bool>,
    pub envelope_privacy_passed: bool,
    pub displayed_privacy_passed: Option<bool>,
    pub raw_output_privacy_passed: Option<bool>,
}
/// Native-only evidence; serialized rows alone cannot reconstruct source authority.
pub struct TurnEvidence {
    row: TurnRow,
    before: AcceptedHistoryBasis,
    after: AcceptedHistoryBasis,
    input_basis: String,
    output_basis: String,
    input: String,
    narration: Option<String>,
}
impl TurnEvidence {
    pub fn row(&self) -> &TurnRow {
        &self.row
    }
}
// Comparison inputs exclude Play timing/configuration diagnostics. Exact opaque
// source bases above remain untouched and still protect each accepted observation.
fn comparison_basis(engine: &Engine) -> Result<String> {
    let history: Vec<_> = engine
        .receipts()
        .iter()
        .map(|r| (r.request(), r.proposal(), r.events(), r.narration()))
        .collect();
    Ok(hash(&encoded(&(
        engine.seed(),
        engine.scope(),
        engine.revision(),
        history,
    ))?))
}
pub fn mandatory_fingerprint(package: &ContextPackage) -> Result<String> {
    Ok(hash(&encoded(
        &package
            .records
            .iter()
            .filter(|r| r.mandatory)
            .collect::<Vec<_>>(),
    )?))
}
pub fn check_observation(
    suite: &FrozenSuite,
    index: usize,
    before: &Engine,
    after: &Engine,
    outcome: ActualOutcome<'_>,
    calls: &[GenerationRequest],
    context: Option<&ContextPackage>,
) -> Result<TurnEvidence> {
    let step = suite.steps.get(index).ok_or(ProtocolError::Order)?;
    if before.receipts().len() > index || after.receipts().len() > index + 1 {
        return Err(ProtocolError::Budget);
    }
    if before.seed() != &suite.seed
        || after.seed() != &suite.seed
        || before.scope() != &suite.seed.scope
        || before.scope() != after.scope()
        || calls.len() > 3
    {
        return Err(ProtocolError::Binding);
    }
    let request = step.request(before);
    let basis = before
        .accepted_history_basis()
        .map_err(|_| ProtocolError::Budget)?;
    let after_basis = after
        .accepted_history_basis()
        .map_err(|_| ProtocolError::Budget)?;
    let mut privacy = true;
    let mut director_detail = None;
    let mut private_target = None;
    let mut role_order = Vec::new();
    let mut prompts = Vec::new();
    let mut schemas = Vec::new();
    for call in calls {
        if call.scope != request.scope
            || call.turn != request.turn
            || call.revision != request.expected_revision
            || call.version != before.seed().version
            || call.model_profile.len() > 64
            || calls
                .first()
                .is_some_and(|first| first.model_profile != call.model_profile)
        {
            return Err(ProtocolError::Binding);
        }
        let Input::Structured {
            role,
            prompt,
            schema,
        } = &call.input
        else {
            return Err(ProtocolError::Binding);
        };
        if !["director", "narrator"].contains(&role.as_str())
            || prompt.len() > 65_536
            || encoded(schema)?.len() > 16_384
            || call.budget.max_output_tokens > 350
            || call.budget.max_output_bytes > MAX_PROPOSAL_BYTES
            || call.budget.deadline_ms > 120_000
        {
            return Err(ProtocolError::Budget);
        }
        role_order.push(role.as_str());
        prompts.push(hash(prompt.as_bytes()));
        schemas.push(hash(&encoded(schema)?));
        privacy &= !COMMON_EXCLUSIONS.iter().any(|s| prompt.contains(s));
        if role == "narrator" {
            privacy &= !NARRATOR_EXCLUSIONS.iter().any(|s| prompt.contains(s));
        }
        if role == "director" {
            director_detail =
                Some(director_detail.unwrap_or(false) || prompt.contains(OPTIONAL_DETAIL));
            private_target =
                Some(private_target.unwrap_or(false) || prompt.contains("SECRET-TIDE-731"));
        }
    }
    if !matches!(
        role_order.as_slice(),
        [] | ["director"]
            | ["director", "director"]
            | ["director", "narrator"]
            | ["director", "director", "narrator"]
    ) {
        return Err(ProtocolError::Order);
    }
    let (state, error, receipt_sha, fallback, narration, profile, receipt_context) = match outcome {
        ActualOutcome::Accepted(receipt) => {
            if receipt.request() != &request
                || !matches!(
                    role_order.as_slice(),
                    ["director", "narrator"] | ["director", "director", "narrator"]
                )
            {
                return Err(ProtocolError::Binding);
            }
            let mut checked = before.clone();
            checked
                .commit_prepared(receipt)
                .map_err(|_| ProtocolError::Integrity)?;
            if checked
                .accepted_history_basis()
                .map_err(|_| ProtocolError::Budget)?
                != after_basis
            {
                return Err(ProtocolError::Integrity);
            }
            let record = receipt.play().ok_or(ProtocolError::Binding)?;
            if calls.iter().any(|c| c.model_profile != record.profile.id) {
                return Err(ProtocolError::Binding);
            }
            let correct = matches!(&step.expected,Expected::Accepted(command) if receipt.proposal().commands.as_slice()==std::slice::from_ref(command));
            (
                if correct {
                    Outcome::Passed
                } else {
                    Outcome::Failed
                },
                None,
                Some(hash(&encoded(receipt)?)),
                Some(record.fallback),
                Some(receipt.narration().into()),
                Some(hash(&encoded(&record.profile)?)),
                record.context.clone(),
            )
        }
        ActualOutcome::Rejected(error) => {
            if basis != after_basis {
                return Err(ProtocolError::Integrity);
            }
            let expected =
                matches!(step.expected,Expected::GuardRejected(expected) if expected.core()==error);
            (
                if expected && calls.is_empty() {
                    Outcome::GuardOnly
                } else {
                    Outcome::Failed
                },
                Some(Failure::from(error)),
                None,
                None,
                None,
                None,
                None,
            )
        }
        ActualOutcome::NotRunDependency => {
            if basis != after_basis || !calls.is_empty() {
                return Err(ProtocolError::Integrity);
            }
            // Skip only if the ordinary Core oracle actually refuses this state.
            if !matches!(step.expected, Expected::Accepted(_))
                || reference_proposal(before, step).is_ok()
            {
                return Err(ProtocolError::Binding);
            }
            (
                Outcome::NotRunDependency,
                None,
                None,
                None,
                None,
                None,
                None,
            )
        }
    };
    let (mandatory, selected) = if let Some(c) = context {
        if c.scope != *before.scope()
            || c.head != before.revision()
            || c.revision != before.revision()
            || c.historical
            || c.observer != suite.seed.player
            || !matches!(c.role, locallore::context_compiler::Role::Director)
        {
            return Err(ProtocolError::Binding);
        }
        (
            Some(mandatory_fingerprint(c)?),
            Some(c.records.iter().any(|r| {
                !r.mandatory
                    && encoded(&r.payload)
                        .is_ok_and(|b| String::from_utf8_lossy(&b).contains(OPTIONAL_DETAIL))
            })),
        )
    } else {
        (None, None)
    };
    let displayed_privacy = narration.as_ref().map(|text: &String| {
        !COMMON_EXCLUSIONS
            .iter()
            .chain(NARRATOR_EXCLUSIONS)
            .any(|s| text.contains(s))
    });
    Ok(TurnEvidence {
        row: TurnRow {
            id: step.id.clone(),
            scene: step.scene,
            outcome: if privacy && displayed_privacy != Some(false) {
                state
            } else {
                Outcome::Failed
            },
            before_revision: before.revision(),
            after_revision: after.revision(),
            before_state_sha256: hash(&before.canonical_bytes()),
            after_state_sha256: hash(&after.canonical_bytes()),
            roles: calls.len(),
            fallback,
            error,
            receipt_sha256: receipt_sha,
            mandatory_sha256: mandatory,
            optional_detail_selected: selected,
            profile_sha256: profile,
            model_profile: calls.first().map(|r| r.model_profile.clone()),
            prompt_sha256: prompts,
            schema_sha256: schemas,
            receipt_context,
            director_detail_present: director_detail,
            director_private_target_present: private_target,
            envelope_privacy_passed: privacy,
            displayed_privacy_passed: displayed_privacy,
            raw_output_privacy_passed: None,
        },
        before: basis,
        after: after_basis,
        input_basis: comparison_basis(before)?,
        output_basis: comparison_basis(after)?,
        input: step.text.clone(),
        narration,
    })
}

/// Copied from the EXISTING runner's cumulative ledger, never a second ledger.
#[derive(Clone, Copy, Debug, Serialize)]
pub struct Charges {
    pub admissions: u16,
    pub roles: u16,
    pub active_ms: u64,
    pub invocations: u16,
    pub unknown_roles: u16,
}
impl Charges {
    pub fn validate(self) -> Result<()> {
        if self.admissions > 32
            || self.roles > 96
            || self.active_ms > 1_800_000
            || self.invocations > 32
            || self.unknown_roles > self.roles
        {
            Err(ProtocolError::Budget)
        } else {
            Ok(())
        }
    }
    pub fn extends(self, previous: Self) -> Result<()> {
        self.validate()?;
        previous.validate()?;
        if self.admissions < previous.admissions
            || self.roles < previous.roles
            || self.active_ms < previous.active_ms
            || self.invocations < previous.invocations
            || self.unknown_roles < previous.unknown_roles
        {
            Err(ProtocolError::Budget)
        } else {
            Ok(())
        }
    }
}
#[derive(Clone, Debug, Serialize)]
pub struct Binding {
    run_id: String,
    source_sha256: String,
    fixture_sha256: String,
    profile_sha256: String,
    model_profile: String,
    prompt_version: String,
    lane: ProviderLane,
    kind: ExperimentKind,
    policy: HistoryPolicy,
    #[serde(skip)]
    initial: AcceptedHistoryBasis,
}
impl Binding {
    pub fn new(
        run_id: &str,
        source_sha256: &str,
        suite: &FrozenSuite,
        profile: &PlayProfile,
        lane: ProviderLane,
        kind: ExperimentKind,
        policy: HistoryPolicy,
    ) -> Result<Self> {
        profile.validate().map_err(|_| ProtocolError::Binding)?;
        if run_id.is_empty()
            || run_id.len() > 64
            || !run_id
                .bytes()
                .all(|b| b.is_ascii_alphanumeric() || b"-_".contains(&b))
            || source_sha256.len() != 64
            || !source_sha256
                .bytes()
                .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
            || profile.context_tokens != 4096
            || profile.director_tokens != 350
            || profile.narrator_tokens != 350
            || profile.deadline_ms != 120_000
            || profile.repair_limit != 1
        {
            return Err(ProtocolError::Binding);
        }
        let initial = Engine::new(suite.seed.clone())
            .map_err(|_| ProtocolError::Integrity)?
            .accepted_history_basis()
            .map_err(|_| ProtocolError::Budget)?;
        Ok(Self {
            run_id: run_id.into(),
            source_sha256: source_sha256.into(),
            fixture_sha256: suite.sha256()?,
            profile_sha256: hash(&encoded(profile)?),
            model_profile: profile.id.clone(),
            prompt_version: PROMPT_VERSION.into(),
            lane,
            kind,
            policy,
            initial,
        })
    }
}
#[derive(Clone, Debug, Serialize)]
pub struct PairReport {
    pub version: u16,
    pub planned_attempts_per_arm: usize,
    pub observed_left: usize,
    pub observed_right: usize,
    pub same_snapshot_pairs: usize,
    pub exact_source_pairs: usize,
    pub first_divergence: Option<usize>,
    pub recent_policy_execution: &'static str,
    pub quality_passed: bool,
    pub human_review: &'static str,
    pub causal_recall: &'static str,
    pub left_charges: Charges,
    pub right_charges: Charges,
}
/// Compares native observations only; does not execute or bless an unavailable policy.
pub fn validate_pair(
    left: &Binding,
    right: &Binding,
    a: &[TurnEvidence],
    b: &[TurnEvidence],
    left_charges: Charges,
    right_charges: Charges,
) -> Result<PairReport> {
    if left.run_id == right.run_id
        || left.source_sha256 != right.source_sha256
        || left.fixture_sha256 != right.fixture_sha256
        || left.profile_sha256 != right.profile_sha256
        || left.prompt_version != right.prompt_version
        || left.lane != right.lane
        || left.kind != right.kind
    {
        return Err(ProtocolError::Binding);
    }
    if left.policy != HistoryPolicy::StateRecentTranscriptV1
        || right.policy != HistoryPolicy::StateRelevantMemoryV1
    {
        return Err(ProtocolError::Binding);
    }
    left_charges.validate()?;
    right_charges.validate()?;
    if a.len() > ATTEMPTS || b.len() > ATTEMPTS {
        return Err(ProtocolError::Budget);
    }
    for (rows, charges, binding) in [(a, left_charges, left), (b, right_charges, right)] {
        let admitted = rows
            .iter()
            .filter(|r| r.row.outcome != Outcome::NotRunDependency)
            .count();
        if admitted > usize::from(charges.admissions)
            || rows.iter().map(|r| r.row.roles).sum::<usize>() > usize::from(charges.roles)
        {
            return Err(ProtocolError::Budget);
        }
        if rows.iter().any(|r| {
            r.row
                .profile_sha256
                .as_ref()
                .is_some_and(|p| p != &binding.profile_sha256)
        }) {
            return Err(ProtocolError::Binding);
        }
        if rows.iter().any(|r| {
            r.row
                .model_profile
                .as_ref()
                .is_some_and(|p| p != &binding.model_profile)
        }) {
            return Err(ProtocolError::Binding);
        }
        if rows.first().is_some_and(|r| r.before != binding.initial) {
            return Err(ProtocolError::Binding);
        }
        if binding.kind == ExperimentKind::ContinuousRollout
            && rows.windows(2).any(|w| w[0].after != w[1].before)
        {
            return Err(ProtocolError::Binding);
        }
    }
    for rows in [a, b] {
        for (i, row) in rows.iter().enumerate() {
            if row.row.id != format!("courier-{:02}", i + 1) {
                return Err(ProtocolError::Order);
            }
        }
    }
    let sequence = compare_sequences(left.kind, a, b)?;
    // Structural checks do not authorize execution. Current policy-omitted2.4
    // observations still cannot be relabeled as either future2.5 policy arm.
    if !a.is_empty() {
        require_execution(left.policy)?;
    }
    if !b.is_empty() {
        require_execution(right.policy)?;
    }
    // This is protocol/source parity, NOT an executed recent-vs-memory experiment.
    Ok(PairReport {
        version: VERSION,
        planned_attempts_per_arm: ATTEMPTS,
        observed_left: a.len(),
        observed_right: b.len(),
        same_snapshot_pairs: sequence.same_snapshot_pairs,
        exact_source_pairs: sequence.exact_source_pairs,
        first_divergence: sequence.first_divergence,
        recent_policy_execution: "unsupported_core_policy",
        quality_passed: false,
        human_review: "not_reviewed",
        causal_recall: "unsupported_by_current_guard_and_narrator_contract",
        left_charges,
        right_charges,
    })
}
#[derive(Clone, Debug, Serialize)]
pub struct SequenceComparison {
    pub same_snapshot_pairs: usize,
    pub exact_source_pairs: usize,
    pub first_divergence: Option<usize>,
}
/// General model-free observation comparator. This grants NO execution policy.
pub fn compare_sequences(
    kind: ExperimentKind,
    a: &[TurnEvidence],
    b: &[TurnEvidence],
) -> Result<SequenceComparison> {
    if a.len() > ATTEMPTS || b.len() > ATTEMPTS {
        return Err(ProtocolError::Budget);
    }
    for rows in [a, b] {
        for (index, row) in rows.iter().enumerate() {
            if row.row.id != format!("courier-{:02}", index + 1) {
                return Err(ProtocolError::Order);
            }
        }
        if kind == ExperimentKind::ContinuousRollout
            && rows.windows(2).any(|w| w[0].after != w[1].before)
        {
            return Err(ProtocolError::Binding);
        }
    }
    let mut same = 0;
    let mut exact = 0;
    let mut divergence = None;
    for (i, (x, y)) in a.iter().zip(b).enumerate() {
        let equal = x.input_basis == y.input_basis;
        if x.before == y.before {
            exact += 1;
        }
        if x.row.id != y.row.id {
            return Err(ProtocolError::Order);
        }
        if kind == ExperimentKind::PairedSnapshots && x.before != y.before {
            return Err(ProtocolError::Binding);
        }
        if equal
            && x.row.mandatory_sha256.is_some()
            && y.row.mandatory_sha256.is_some()
            && x.row.mandatory_sha256 != y.row.mandatory_sha256
        {
            return Err(ProtocolError::Integrity);
        }
        if equal && (kind == ExperimentKind::PairedSnapshots || divergence.is_none()) {
            same += 1;
        }
        if divergence.is_none()
            && (x.input_basis != y.input_basis || x.output_basis != y.output_basis)
        {
            divergence = Some(i + 1);
        }
    }
    Ok(SequenceComparison {
        same_snapshot_pairs: same,
        exact_source_pairs: exact,
        first_divergence: divergence,
    })
}
pub fn render_human_packet(rows: &[TurnEvidence]) -> Result<String> {
    if rows.len() > ATTEMPTS {
        return Err(ProtocolError::Budget);
    }
    fn escape(s: &str) -> String {
        s.replace('&', "&amp;")
            .replace('<', "&lt;")
            .replace('>', "&gt;")
            .replace('"', "&quot;")
            .replace('\'', "&#39;")
    }
    let mut out=format!("<!doctype html><meta charset=utf-8><title>Synthetic comparison review</title><h1>Synthetic comparison review</h1><p>Planned attempts:24; observed prefix:{}.</p><p>Human review: not reviewed. Requested policy execution: unsupported. Causal recall: not assessed. Fallback is separate from generated prose.</p>",rows.len());
    for (index, evidence) in rows.iter().enumerate() {
        let row = &evidence.row;
        if row.id != format!("courier-{:02}", index + 1) {
            return Err(ProtocolError::Order);
        }
        let clip=format!("<section><h2>{}</h2><p>Outcome: {:?}; roles: {}; fallback: {:?}</p><h3>Original input</h3><pre>{}</pre><h3>Actual displayed narration</h3><pre>{}</pre><p>Error: {:?}</p></section>",escape(&row.id),row.outcome,row.roles,row.fallback,escape(&evidence.input),escape(evidence.narration.as_deref().unwrap_or("Unavailable: no accepted narration")),row.error);
        if out.len().saturating_add(clip.len()) > MAX_PACKET_BYTES {
            return Err(ProtocolError::Budget);
        }
        out.push_str(&clip);
    }
    Ok(out)
}
