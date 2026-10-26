//! Native, source-bound generated-Play staging. Only the sanitized evidence is
//! provider output material; the capability and ordinary receipt stay native.
use super::{check_json_budget, AcceptedHistoryBasis, Engine};
use crate::contracts::*;
use serde::Serialize;

/// Consumed by commit; never serialized, cloned or constructed from wire data.
pub struct StagedPlayV25 {
    pub(super) basis: AcceptedHistoryBasis,
    pub(super) approved: Receipt,
    pub(super) evidence: NarratorEvidenceV22,
}
impl StagedPlayV25 {
    pub fn approved(&self) -> &Receipt {
        &self.approved
    }
    pub fn narrator_evidence(&self) -> &NarratorEvidenceV22 {
        &self.evidence
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct NarratorEvidenceV22 {
    version: u16,
    events: Vec<NarratorEventV22>,
    observations: Vec<NarratorObservationV22>,
    mechanical_summary: String,
}
impl NarratorEvidenceV22 {
    pub fn events(&self) -> &[NarratorEventV22] {
        &self.events
    }
    pub fn observations(&self) -> &[NarratorObservationV22] {
        &self.observations
    }
    pub fn mechanical_summary(&self) -> &str {
        &self.mechanical_summary
    }
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct NarratorEventV22 {
    event_id: u64,
    outcome: NarratorOutcomeV22,
}
impl NarratorEventV22 {
    pub fn event_id(&self) -> u64 {
        self.event_id
    }
    pub fn outcome(&self) -> &NarratorOutcomeV22 {
        &self.outcome
    }
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum NarratorOutcomeV22 {
    Resolved { effect: Effect },
    StatementDelivered,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct NarratorObservationV22 {
    event_id: u64,
    actor: String,
    fact: String,
    proposition: String,
}
impl NarratorObservationV22 {
    pub fn event_id(&self) -> u64 {
        self.event_id
    }
    pub fn actor(&self) -> &str {
        &self.actor
    }
    pub fn fact(&self) -> &str {
        &self.fact
    }
    pub fn proposition(&self) -> &str {
        &self.proposition
    }
}

pub(super) fn check(cancel: &dyn Fn() -> bool) -> Result<(), Error> {
    if std::panic::catch_unwind(std::panic::AssertUnwindSafe(cancel)).unwrap_or(true) {
        Err(Error::Cancelled)
    } else {
        Ok(())
    }
}

impl Engine {
    /// Literal-v1 target over the same opaque actual candidate/evidence. The
    /// existing V25 commit entry keeps its original strict admission contract.
    pub fn commit_staged_literal_play_v1(
        &mut self,
        staged: StagedPlayV25,
        record: &crate::play::PlayRecord,
        cancel: &dyn Fn() -> bool,
    ) -> Result<Receipt, Error> {
        self.commit_staged_literal_play_history_v1(staged, record, cancel, false)
    }
    pub(super) fn commit_staged_literal_play_history_v1(
        &mut self,
        staged: StagedPlayV25,
        record: &crate::play::PlayRecord,
        cancel: &dyn Fn() -> bool,
        recorded_history: bool,
    ) -> Result<Receipt, Error> {
        self.commit_staged_play_history_inner(staged, record, cancel, recorded_history, true)
    }
    /// Revalidate a consumed native stage against the complete current source.
    /// A recorded exact retry wins before cancellation or source-head checks.
    pub fn commit_staged_play_v25(
        &mut self,
        staged: StagedPlayV25,
        record: &crate::play::PlayRecord,
        cancel: &dyn Fn() -> bool,
    ) -> Result<Receipt, Error> {
        self.commit_staged_play_history_v25(staged, record, cancel, false)
    }

    pub(super) fn commit_staged_play_history_v25(
        &mut self,
        staged: StagedPlayV25,
        record: &crate::play::PlayRecord,
        cancel: &dyn Fn() -> bool,
        recorded_history: bool,
    ) -> Result<Receipt, Error> {
        self.commit_staged_play_history_inner(staged, record, cancel, recorded_history, false)
    }
    fn commit_staged_play_history_inner(
        &mut self,
        staged: StagedPlayV25,
        record: &crate::play::PlayRecord,
        cancel: &dyn Fn() -> bool,
        recorded_history: bool,
        literal: bool,
    ) -> Result<Receipt, Error> {
        if let Some(receipt) = self.recorded(staged.approved.request())? {
            return Ok(receipt);
        }
        check(cancel)?;
        if self.accepted_history_basis()? != staged.basis {
            return Err(Error::Stale);
        }
        let regenerated = self.stage_play_v25(
            staged.approved.request(),
            staged.approved.proposal(),
            cancel,
        )?;
        if regenerated.basis != staged.basis
            || regenerated.approved != staged.approved
            || regenerated.evidence != staged.evidence
        {
            return Err(Error::Stale);
        }
        if literal {
            crate::play::validate_record_literal_v1(
                self,
                &regenerated.approved,
                &regenerated.evidence,
                record,
                recorded_history,
                cancel,
            )?;
        } else {
            crate::play::validate_record_v25(
                self,
                &regenerated.approved,
                &regenerated.evidence,
                record,
                recorded_history,
            )?;
        }
        let mut receipt = regenerated.approved;
        receipt.narration = record.narration.text.clone();
        receipt.play = Some(record.clone());
        let mut candidate = self.clone();
        candidate.append_play(receipt.clone())?;
        // This is the final cancellation checkpoint. Once installed, the
        // successful result cannot be misreported as a rolled-back operation.
        check(cancel)?;
        *self = candidate;
        Ok(receipt)
    }

    pub fn stage_play_v25(
        &self,
        request: &Request,
        proposal: &Proposal,
        cancel: &dyn Fn() -> bool,
    ) -> Result<StagedPlayV25, Error> {
        check(cancel)?;
        if !matches!(request.intent, Intent::FreeText { .. }) {
            return Err(Error::Agency);
        }
        let approved = self.preview_resolved(request, proposal)?;
        check(cancel)?;
        let basis = self.accepted_history_basis()?;
        check(cancel)?;
        // The real append generates and validates private per-event bindings.
        // No selected-source mutation or provider work occurs on this clone.
        let mut candidate = self.clone();
        candidate.append_play(approved.clone())?;
        check(cancel)?;
        let mut observations = vec![];
        let mut invalid = false;
        candidate.visit_actor_observations_v2(
            &self.seed.player,
            &self.scope,
            candidate.revision(),
            self.revision(),
            candidate.revision(),
            cancel,
            &mut |view| {
                if let Some(discovery) = &view.discovery {
                    let event = &view.event;
                    let matches = approved.events().iter().any(|actual| {
                        actual == event
                            && matches!(actual.outcome(),
                            Effect::Discovered { actor, fact }
                            if actor == &self.seed.player && fact == &discovery.fact)
                    });
                    if !matches {
                        invalid = true;
                        return false;
                    }
                    observations.push(NarratorObservationV22 {
                        event_id: event.sequence(),
                        actor: self.seed.player.clone(),
                        fact: discovery.fact.clone(),
                        proposition: discovery.proposition.clone(),
                    });
                }
                true
            },
        )?;
        if invalid
            || observations.len()
                != approved
                    .events()
                    .iter()
                    .filter(|event| {
                        matches!(event.outcome(), Effect::Discovered { actor, .. }
                        if actor == &self.seed.player)
                    })
                    .count()
        {
            return Err(Error::CorruptHistory);
        }
        let mut events = Vec::with_capacity(approved.events().len());
        for event in approved.events() {
            check(cancel)?;
            events.push(NarratorEventV22 {
                event_id: event.sequence(),
                outcome: if matches!(event.outcome(), Effect::Said(_)) {
                    NarratorOutcomeV22::StatementDelivered
                } else {
                    NarratorOutcomeV22::Resolved {
                        effect: event.outcome().clone(),
                    }
                },
            });
        }
        let evidence = NarratorEvidenceV22 {
            version: 2,
            events,
            observations,
            mechanical_summary: approved.narration().into(),
        };
        check_json_budget(&evidence, MAX_RECEIPT_BYTES)?;
        check(cancel)?;
        Ok(StagedPlayV25 {
            basis,
            approved,
            evidence,
        })
    }
}
