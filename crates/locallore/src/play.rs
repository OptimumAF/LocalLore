//! Versioned shared local play. Generated text is display evidence, never canonical truth.
use crate::{
    contracts::*,
    engine::Engine,
    inference::{generate, Budget, Cancellation, GenerationRequest, InferenceProvider, Input},
};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    time::Instant,
};

pub const PLAY_VERSION: u16 = 2;
pub const NARRATION_POLICY: &str = "grounded-prose-v2.0";
pub const PROMPT_VERSION: &str = "locallore-play-v2.0";

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
}

pub(crate) fn validate_interpretation(request: &Request, proposal: &Proposal) -> Result<(), Error> {
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
                Ok(())
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
) -> Result<(), Error> {
    record.profile.validate()?;
    if record.version != PLAY_VERSION
        || record.policy != NARRATION_POLICY
        || record.prompt_version != PROMPT_VERSION
        || record.repairs > record.profile.repair_limit
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
        validate_prose(engine, approved, &record.narration.text)?;
    }
    Ok(())
}

fn validate_prose(engine: &Engine, approved: &Receipt, text: &str) -> Result<(), Error> {
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
        || lower.contains(" tells ")
    {
        return Err(Error::Narration);
    }
    let source = crate::engine::render(approved.events()).to_lowercase();
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
        if (if phrase.contains(' ') {
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
        {
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
        ("consumed", &["healed", "cured", "injury disappears"][..]),
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
    let visible: BTreeSet<_> = approved
        .events()
        .iter()
        .flat_map(|e| e.witnesses().iter().map(String::as_str))
        .collect();
    for (id, actor) in &engine.state().actors {
        if !visible.contains(id.as_str())
            && (lower.contains(&id.to_lowercase()) || lower.contains(&actor.name.to_lowercase()))
        {
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
            json!({"ticks":{"type":"integer","minimum":1,"maximum":65535}}),
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
    if let Some(receipt) = engine.recorded(request)? {
        return Ok(receipt);
    }
    profile.validate()?;
    engine.preflight(request)?;
    let Intent::FreeText { kind, text } = &request.intent else {
        return Err(Error::Agency);
    };
    let started = Instant::now();
    let mut stages = Vec::new();
    let context =
        engine.character_context(&engine.seed().player, engine.scope(), engine.revision())?;
    let inventory: BTreeMap<_, _> = engine
        .state()
        .items
        .iter()
        .filter(|(_, i)| i.owner == engine.seed().player)
        .collect();
    let nearby: BTreeMap<_, _> = engine
        .state()
        .actors
        .iter()
        .filter(|(_, a)| a.location == context.self_state.location && a.alive)
        .map(|(id, a)| (id, &a.name))
        .collect();
    let routes: Vec<_> = engine
        .seed()
        .routes
        .iter()
        .filter(|(from, _)| from == &context.self_state.location)
        .map(|(_, to)| to)
        .collect();
    let input = json!({"kind":kind,"player_text":text,"context":context,"inventory":inventory,"nearby":nearby,"routes":routes});
    crate::engine::check_json_budget(&input, 24_576)?;
    let base=format!("Interpret the player's untrusted attempt, not an outcome. Return JSON commands only. Use known IDs. Never grant powers, items, author privileges, hidden knowledge or control NPCs. Action mode cannot invent player speech. Dialogue must preserve exact input text, choosing only present audience IDs. A gift is give, not consume; do not heal the recipient unless a supported action does so. Input: {input}");
    let remaining = || {
        profile
            .deadline_ms
            .checked_sub(started.elapsed().as_millis() as u64)
            .filter(|v| *v > 0)
            .ok_or(Error::Timeout)
    };
    let mut repairs = 0;
    let proposal = loop {
        if cancel.is_cancelled() {
            return Err(Error::Cancelled);
        }
        let before = Instant::now();
        let prompt = if repairs == 0 {
            base.clone()
        } else {
            format!("{base}\nPrevious output was malformed. Repair exactly once using the schema. Do not change the player's requested intent.")
        };
        let generation = role_request(
            request,
            profile,
            "director",
            prompt,
            director_schema(),
            remaining()?,
        );
        let bytes = generate(provider, &generation, cancel)?;
        stages.push(StageTiming {
            stage: if repairs == 0 { "director" } else { "repair" }.into(),
            elapsed_ms: before.elapsed().as_millis() as u64,
        });
        let parsed: Result<DirectorOutput, _> = crate::engine::parse_unique(&bytes);
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
    let before = Instant::now();
    let approved = engine.preview(request, &proposal)?;
    stages.push(StageTiming {
        stage: "validation".into(),
        elapsed_ms: before.elapsed().as_millis() as u64,
    });
    let outcomes: Vec<_> = approved
        .events()
        .iter()
        .map(|e| json!({"event_id":e.sequence(),"outcome":e.outcome()}))
        .collect();
    let prompt=format!("Write brief natural story prose in second person from ONLY these approved outcomes. The action has already resolved. No new items, abilities, healing, movement, discoveries, hidden facts or NPC knowledge. Give is possession transfer, not consumption or healing. No NPC quotation or impersonation. Small sensory/emotional description is allowed. Return JSON text, event_ids and speaker narrator. Approved outcomes: {}. Mechanical summary: {}",json!(outcomes),approved.narration());
    let generation = role_request(
        request,
        profile,
        "narrator",
        prompt,
        narration_schema(approved.events()),
        remaining()?,
    );
    let before = Instant::now();
    let bytes = generate(provider, &generation, cancel)?;
    stages.push(StageTiming {
        stage: "narrator".into(),
        elapsed_ms: before.elapsed().as_millis() as u64,
    });
    let mut record = PlayRecord {
        version: PLAY_VERSION,
        policy: NARRATION_POLICY.into(),
        prompt_version: PROMPT_VERSION.into(),
        profile: profile.clone(),
        repairs,
        fallback: false,
        narration: crate::engine::parse_unique(&bytes).unwrap_or_else(|_| NarrationDocument {
            text: String::new(),
            event_ids: Vec::new(),
            speaker: String::new(),
        }),
        stages,
    };
    let before = Instant::now();
    if validate_record(engine, &approved, &record).is_err() {
        record.fallback = true;
        record.narration = NarrationDocument {
            text: approved.narration().into(),
            event_ids: approved.events().iter().map(|e| e.sequence()).collect(),
            speaker: "narrator".into(),
        };
    }
    record.stages.push(StageTiming {
        stage: "narration_validation".into(),
        elapsed_ms: before.elapsed().as_millis() as u64,
    });
    record.stages.push(StageTiming {
        stage: "total".into(),
        elapsed_ms: started.elapsed().as_millis() as u64,
    });
    remaining()?;
    if cancel.is_cancelled() {
        return Err(Error::Cancelled);
    }
    engine.commit_play(request, &proposal, &record)
}
