//! One current Director projection/rendering and separately labelled byte estimate.
//! No provider, storage, actor eligibility or canonical mutation authority.
use super::*;
use crate::context_compiler::{ContextPackage, Kind, Payload, Role};

const REPAIR_SUFFIX: &str = "\nPrevious output was malformed. Repair exactly once using the schema. Do not change the player's requested intent.";

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum DirectorPassV25 {
    Initial,
    Repair,
}
/// Pure relation over two actual prompts; never constructs a prompt or grants
/// eligibility. Keep the current fixed renderer suffix in one production place.
pub fn director_repair_matches_v25(initial: &str, repair: &str) -> bool {
    repair.strip_prefix(initial) == Some(REPAIR_SUFFIX)
}

/// Counts over actual current role bytes, not measured tokenizer/template fit.
/// Serialize-only metadata cannot authenticate the selected context or its source.
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct ForwardedEstimateV1 {
    version: u16,
    prompt_bytes: usize,
    schema_bytes: usize,
    repair_extra_bytes: usize,
    actual_prompt_schema_estimated_tokens: u32,
    admission_prompt_schema_estimated_tokens: u32,
    output_tokens: u32,
    template_reserve_tokens: u32,
    estimated_total_tokens: u32,
}
impl ForwardedEstimateV1 {
    pub fn actual_prompt_schema_estimated_tokens(&self) -> u32 {
        self.actual_prompt_schema_estimated_tokens
    }
    pub fn estimated_total_tokens(&self) -> u32 {
        self.estimated_total_tokens
    }
}

/// Pure budget check over actual role input, not a prompt constructor or proof.
/// Callers must independently validate role identity, eligibility and provenance.
pub fn director_forwarded_budget_v25(
    profile: &PlayProfile,
    pass: DirectorPassV25,
    actual_prompt: &str,
    actual_schema: &Value,
) -> Result<ForwardedEstimateV1, Error> {
    profile.validate()?;
    if pass == DirectorPassV25::Repair && profile.repair_limit == 0 {
        return Err(Error::Rule);
    }
    // Existing private capture refuses role prompts over32000 bytes. Context
    // and schema inputs have independent existing bounded JSON checks as well.
    if actual_prompt.len() > 32_000 {
        return Err(Error::TooLarge);
    }
    crate::engine::check_json_budget(actual_schema, MAX_PROPOSAL_BYTES)?;
    let schema_bytes = serde_json::to_vec(actual_schema)
        .map_err(|_| Error::TooLarge)?
        .len();
    let repair_extra_bytes = if pass == DirectorPassV25::Initial && profile.repair_limit == 1 {
        REPAIR_SUFFIX.len()
    } else {
        0
    };
    let actual_bytes = actual_prompt
        .len()
        .checked_add(schema_bytes)
        .ok_or(Error::TooLarge)?;
    let maximum_bytes = actual_bytes
        .checked_add(repair_extra_bytes)
        .ok_or(Error::TooLarge)?;
    let actual_tokens = u32::try_from(actual_bytes.div_ceil(4)).map_err(|_| Error::TooLarge)?;
    let admission_tokens = u32::try_from(maximum_bytes.div_ceil(4)).map_err(|_| Error::TooLarge)?;
    // Preserve the total512 reserve (511 for the minimum valid context512).
    // At the pinned350-output profile,162 tokens are an explicitly unmeasured
    // template/envelope reserve, not a claim that a native template fits.
    let reserved = 512.min(profile.context_tokens.saturating_sub(1));
    let output_tokens = u32::from(profile.director_tokens);
    let template_reserve_tokens = reserved.checked_sub(output_tokens).ok_or(Error::Rule)?;
    let estimated_total_tokens = admission_tokens
        .checked_add(output_tokens)
        .and_then(|n| n.checked_add(template_reserve_tokens))
        .ok_or(Error::TooLarge)?;
    if estimated_total_tokens > profile.context_tokens {
        return Err(Error::TooLarge);
    }
    Ok(ForwardedEstimateV1 {
        version: 1,
        prompt_bytes: actual_prompt.len(),
        schema_bytes,
        repair_extra_bytes,
        actual_prompt_schema_estimated_tokens: actual_tokens,
        admission_prompt_schema_estimated_tokens: admission_tokens,
        output_tokens,
        template_reserve_tokens,
        estimated_total_tokens,
    })
}

#[derive(Serialize)]
struct DirectorContextV25<'a> {
    compiler_version: u16,
    observer: &'a str,
    revision: u64,
    records: Vec<DirectorRecordV25<'a>>,
}
#[derive(Serialize)]
struct DirectorRecordV25<'a> {
    kind: Kind,
    source_revision: u64,
    payload: &'a Payload,
}
impl<'a> From<&'a ContextPackage> for DirectorContextV25<'a> {
    fn from(package: &'a ContextPackage) -> Self {
        Self {
            compiler_version: package.version,
            observer: &package.observer,
            revision: package.revision,
            records: package
                .records
                .iter()
                .map(|r| DirectorRecordV25 {
                    kind: r.kind,
                    source_revision: r.source_revision,
                    payload: &r.payload,
                })
                .collect(),
        }
    }
}

pub(crate) struct RenderedDirectorV25 {
    pub(crate) prompt: String,
    pub(crate) schema: Value,
}

/// Closed frame constructed only from the actual Play Engine/request/profile.
/// No caller-supplied instructions, prompt, schema, renderer or budget callback.
pub(crate) struct DirectorEnvelopeV25 {
    scope: Scope,
    revision: u64,
    player: String,
    kind: PlayInputKind,
    text: String,
    inventory: BTreeMap<String, Item>,
    nearby: BTreeMap<String, String>,
    routes: Vec<String>,
    schema: Value,
    profile: PlayProfile,
}
impl DirectorEnvelopeV25 {
    pub(super) fn new(
        engine: &Engine,
        request: &Request,
        profile: &PlayProfile,
        guarded_action: Option<&Command>,
    ) -> Result<Self, Error> {
        profile.validate()?;
        let Intent::FreeText { kind, text } = &request.intent else {
            return Err(Error::Agency);
        };
        if request.scope != *engine.scope() || request.expected_revision != engine.revision() {
            return Err(Error::Stale);
        }
        let player = &engine.seed().player;
        let location = &engine
            .state()
            .actors
            .get(player)
            .ok_or(Error::UnknownReference)?
            .location;
        let inventory: BTreeMap<_, _> = engine
            .state()
            .items
            .iter()
            .filter(|(_, item)| &item.owner == player)
            .collect();
        let nearby: BTreeMap<_, _> = engine
            .state()
            .actors
            .iter()
            .filter(|(_, actor)| &actor.location == location && actor.alive)
            .map(|(id, actor)| (id, &actor.name))
            .collect();
        let schema =
            super::director_schema_for(kind, text, &nearby, &inventory, player, guarded_action)?;
        Ok(Self {
            scope: request.scope.clone(),
            revision: request.expected_revision,
            player: player.clone(),
            kind: *kind,
            text: text.clone(),
            inventory: inventory
                .into_iter()
                .map(|(id, item)| (id.clone(), item.clone()))
                .collect(),
            nearby: nearby
                .into_iter()
                .map(|(id, name)| (id.clone(), name.clone()))
                .collect(),
            routes: engine
                .seed()
                .routes
                .iter()
                .filter(|(from, _)| from == location)
                .map(|(_, to)| to.clone())
                .collect(),
            schema,
            profile: profile.clone(),
        })
    }
    pub(crate) fn validate_basis(
        &self,
        request: &crate::context_compiler::CompileRequest,
    ) -> Result<(), crate::context_compiler::CompileError> {
        if request.version != crate::context_compiler::POLICY_COMPILER_VERSION
            || request.scope != self.scope
            || request.expected_head != self.revision
            || request.at_revision.is_some()
            || request.observer != self.player
            || request.role != Role::Director
            || request.budget.estimated_tokens != self.profile.context_tokens
            || request.budget.reserved_tokens
                != 512.min(self.profile.context_tokens.saturating_sub(1))
        {
            return Err(crate::context_compiler::CompileError::InvalidRequest);
        }
        Ok(())
    }
    pub(crate) fn ensure_audience(&self) -> Result<(), Error> {
        if self.kind == PlayInputKind::Dialogue && !self.nearby.keys().any(|id| id != &self.player)
        {
            return Err(Error::ClarificationRequired);
        }
        Ok(())
    }
    pub(crate) fn eligible_count(&self, package: &ContextPackage) -> u32 {
        [
            package.records.len(),
            self.inventory.len(),
            self.nearby.len(),
            self.routes.len(),
            1,
        ]
        .into_iter()
        .fold(0usize, usize::saturating_add)
        .min(u32::MAX as usize) as u32
    }
    pub(crate) fn render(
        &self,
        package: &ContextPackage,
        pass: DirectorPassV25,
    ) -> Result<RenderedDirectorV25, Error> {
        if package.version != crate::context_compiler::POLICY_COMPILER_VERSION
            || package.scope != self.scope
            || package.head != self.revision
            || package.revision != self.revision
            || package.historical
            || package.observer != self.player
            || package.role != Role::Director
        {
            return Err(Error::Stale);
        }
        if pass == DirectorPassV25::Repair && self.profile.repair_limit == 0 {
            return Err(Error::Rule);
        }
        let context = DirectorContextV25::from(package);
        // Serialize to Value, as the old json! projection did, to retain exact
        // key ordering/escaping of the original current provider input bytes.
        let input = json!({"kind":self.kind,"player_text":self.text,"context":context,
            "inventory":self.inventory,"nearby":self.nearby,"routes":self.routes});
        crate::engine::check_json_budget(&input, MAX_ROLE_INPUT_BYTES)?;
        let instructions = match self.kind {
            PlayInputKind::Action => "ACTION mode: translate the attempted physical action into commands, never say. Return {\"commands\":[...]}. Command shapes: {\"op\":\"give\",\"item\":item_id,\"to\":actor_id,\"quantity\":integer}; {\"op\":\"consume\",\"item\":item_id}; {\"op\":\"use_ability\",\"ability\":ability_id}; {\"op\":\"learn\",\"ability\":ability_id}; {\"op\":\"move\",\"to\":location_id}; {\"op\":\"discover\",\"fact\":fact_id}; {\"op\":\"believe\",\"claim_event\":integer}; {\"op\":\"wait\",\"ticks\":integer}. A gift uses give, not consume. Preserve the attempted action even if it will be rejected for missing inventory or ability; never replace it with speech or wait.",
            PlayInputKind::Dialogue => "DIALOGUE mode: return exactly one say command: {\"commands\":[{\"op\":\"say\",\"text\":exact_player_text,\"audience\":[present_actor_id]}]}. Preserve player_text exactly. Choose only present audience IDs; never perform a physical action.",
        };
        let mut prompt = format!("Interpret an untrusted attempt, not an established outcome. Return JSON only. Use lowercase IDs from input, not display names. Never grant powers, items, author privileges, hidden knowledge or control NPCs. Context data: {input}\n{instructions}\nTranslate ONLY this player's {:?} request now: {}",self.kind,serde_json::to_string(&self.text).map_err(|_|Error::Malformed)?);
        if pass == DirectorPassV25::Repair {
            prompt.push_str(REPAIR_SUFFIX);
        }
        Ok(RenderedDirectorV25 {
            prompt,
            schema: self.schema.clone(),
        })
    }
    pub(crate) fn estimate_max_pass(
        &self,
        package: &ContextPackage,
    ) -> Result<ForwardedEstimateV1, Error> {
        let initial = self.render(package, DirectorPassV25::Initial)?;
        director_forwarded_budget_v25(
            &self.profile,
            DirectorPassV25::Initial,
            &initial.prompt,
            &initial.schema,
        )
    }
    pub(crate) fn render_checked(
        &self,
        package: &ContextPackage,
        pass: DirectorPassV25,
    ) -> Result<RenderedDirectorV25, Error> {
        let rendered = self.render(package, pass)?;
        director_forwarded_budget_v25(&self.profile, pass, &rendered.prompt, &rendered.schema)?;
        Ok(rendered)
    }
}
