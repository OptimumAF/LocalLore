//! Native construction policy. Derived candidate views, never canonical authority.
use super::*;
use crate::{
    author_correction::ActorEventV2, contracts::Intent, memory_coverage::VerifiedCoverage,
};

pub const POLICY_COMPILER_VERSION: u16 = 2;
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ContextPolicy {
    StateRecentTranscriptV1,
    StateRelevantMemoryV1,
}
#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize)]
pub struct ConstructionDiagnostics {
    /// Whole units constructed for this policy, excluding hidden/author/partial
    /// player receipts. Relevant's zero means not constructed, not no history.
    pub eligible_transcript_units: usize,
    pub overlap_transcript_units: usize,
    pub selected_transcript_units: usize,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct PolicyCompilation {
    pub policy: ContextPolicy,
    pub compilation: MemoryCompilation,
    pub construction: ConstructionDiagnostics,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct TranscriptUnit {
    pub original_scope: Scope,
    pub turn: String,
    pub events: Vec<ActorEventV2>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub original_input: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub narration: Option<String>,
}
#[derive(Clone, Copy)]
pub(super) enum Construction {
    Legacy,
    Policy(ContextPolicy),
}
impl Construction {
    pub(super) fn version(self) -> u16 {
        match self {
            Self::Legacy => COMPILER_VERSION,
            Self::Policy(_) => POLICY_COMPILER_VERSION,
        }
    }
    pub(super) fn is_current(self) -> bool {
        matches!(self, Self::Policy(_))
    }
    pub(super) fn is_recent(self) -> bool {
        matches!(self, Self::Policy(ContextPolicy::StateRecentTranscriptV1))
    }
}
/// Both policies execute the same compiler. Selecting a policy cannot grant an
/// inspection lens, manufacture a cache proof or enable a missing model runner.
pub fn compile_policy_cancelled(
    engine: &Engine,
    request: &CompileRequest,
    policy: ContextPolicy,
    proof: Option<&VerifiedCoverage>,
    cancel: &dyn Fn() -> bool,
) -> Result<PolicyCompilation, CompileError> {
    let result = compile_inner(
        engine,
        request,
        verified::Input::Verified(proof),
        Construction::Policy(policy),
        cancel,
    )?;
    Ok(PolicyCompilation {
        policy,
        compilation: result.compilation,
        construction: result.construction,
    })
}
pub(super) fn transcript_candidates(
    engine: &Engine,
    request: &CompileRequest,
    existing: usize,
    bytes: &mut usize,
    cancel: &dyn Fn() -> bool,
) -> Result<(Vec<Candidate>, ConstructionDiagnostics), CompileError> {
    check(cancel)?;
    let actor = &request.observer;
    let player = actor == &engine.seed().player;
    // This is the actual same Core eligibility used by Query2, without a Lab
    // grant argument. NPC empty/hidden receipts are removed by the Core first.
    let views = engine
        .actor_receipts_v2(actor, engine.scope(), engine.revision())
        .map_err(|_| CompileError::Source)?;
    let ordinary = if player {
        engine
            .canonical_records()
            .iter()
            .filter_map(|r| r.receipt())
            .map(|r| ((r.request().scope.clone(), r.request().turn.clone()), r))
            .collect::<BTreeMap<_, _>>()
    } else {
        BTreeMap::new()
    };
    let mut candidates = vec![];
    for view in views {
        check(cancel)?;
        if view.events.is_empty() {
            continue;
        }
        let (original_input, narration) = if player {
            let receipt = ordinary
                .get(&(view.original_scope.clone(), view.turn.clone()))
                .ok_or(CompileError::Source)?;
            // Exact complete ordered event equality, not a witnessed subset.
            // A future partial player receipt cannot attach its private prose.
            if receipt.events().len() != view.events.len()
                || !receipt
                    .events()
                    .iter()
                    .zip(&view.events)
                    .all(|(a, b)| a == &b.event)
            {
                continue;
            }
            let input = match &receipt.request().intent {
                Intent::Dialogue { text, .. } | Intent::FreeText { text, .. } => Some(text.clone()),
                _ => None,
            };
            (input, Some(receipt.narration().to_owned()))
        } else {
            (None, None)
        };
        if existing
            .checked_add(candidates.len())
            .is_none_or(|n| n >= MAX_CANDIDATES)
        {
            return Err(CompileError::TooLarge);
        }
        let revision = view
            .events
            .last()
            .ok_or(CompileError::Source)?
            .event
            .sequence();
        let sources = view
            .events
            .iter()
            .map(|v| Source::ScopedEvent {
                original_scope: v.event.scope().clone(),
                sequence: v.event.sequence(),
            })
            .collect::<Vec<_>>();
        let unit = TranscriptUnit {
            original_scope: view.original_scope,
            turn: view.turn,
            events: view.events,
            original_input,
            narration,
        };
        let key = serde_json::to_string(&("transcript:v2", &unit.original_scope, &unit.turn))
            .map_err(|_| CompileError::Source)?;
        let encoded = serde_json::to_string(&unit).map_err(|_| CompileError::Source)?;
        *bytes = bytes
            .checked_add(encoded.len())
            .ok_or(CompileError::TooLarge)?;
        if *bytes > MAX_CANDIDATE_BYTES {
            return Err(CompileError::TooLarge);
        }
        candidates.push(Candidate {
            key,
            payload: CandidatePayload::TranscriptUnit(unit),
            encoded,
            ids: BTreeSet::new(),
            kind: Kind::Transcript,
            sources,
            revision,
        });
    }
    check(cancel)?;
    let diagnostics = ConstructionDiagnostics {
        eligible_transcript_units: candidates.len(),
        ..ConstructionDiagnostics::default()
    };
    Ok((candidates, diagnostics))
}
