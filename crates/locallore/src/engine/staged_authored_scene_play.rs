//! Source-bound authored scene preparation. Only the closed frame and existing
//! sanitized evidence are provider material; the capability stays native.
use super::{check_json_budget, staged_play, Engine};
use crate::{
    author_correction::ObservationSource,
    contracts::{Error, Proposal, Receipt, Request, Scope, MAX_RECEIPT_BYTES},
    play::{
        authored_scene_narration::{self, AuthoredSceneRecipeV2},
        scene_narration::SceneNarrationRecordV1,
        PlayRecord,
    },
    story_presentation::StoryPresentationV1,
};
use serde::Serialize;

/// Consumed native preparation: no wire constructor, cloning or serialization.
pub struct StagedAuthoredScenePlayV2 {
    staged: staged_play::StagedPlayV25,
    frame: NarratorAuthoredSceneFrameV2,
}

/// A source/recipe capability, never reconstructed from a recorded frame hash.
pub struct BoundAuthoredScenePlayV2 {
    preparation: StagedAuthoredScenePlayV2,
    recipe: AuthoredSceneRecipeV2,
    presentation: Option<StoryPresentationV1>,
    provenance: SceneNarrationRecordV1,
}

impl StagedAuthoredScenePlayV2 {
    pub fn approved(&self) -> &Receipt {
        self.staged.approved()
    }
    pub fn narrator_evidence(&self) -> &staged_play::NarratorEvidenceV22 {
        self.staged.narrator_evidence()
    }
    pub fn scene_frame(&self) -> &NarratorAuthoredSceneFrameV2 {
        &self.frame
    }
}

impl BoundAuthoredScenePlayV2 {
    pub fn approved(&self) -> &Receipt {
        self.preparation.approved()
    }
    pub fn narrator_evidence(&self) -> &staged_play::NarratorEvidenceV22 {
        self.preparation.narrator_evidence()
    }
    pub fn scene_frame(&self) -> &NarratorAuthoredSceneFrameV2 {
        self.preparation.scene_frame()
    }
    pub fn recipe(&self) -> AuthoredSceneRecipeV2 {
        self.recipe
    }
    pub(crate) fn presentation(&self) -> Option<&StoryPresentationV1> {
        self.presentation.as_ref()
    }
    pub(crate) fn provenance(&self) -> &SceneNarrationRecordV1 {
        &self.provenance
    }
}

/// A typed observed label, not the source fact's description or a new discovery.
#[derive(Debug, PartialEq, Eq, Serialize)]
pub struct NarratorLocationLabelV1 {
    location_id: String,
    name: String,
    fact_id: String,
    observation: ObservationSource,
}

impl NarratorLocationLabelV1 {
    pub fn location_id(&self) -> &str {
        &self.location_id
    }
    pub fn name(&self) -> &str {
        &self.name
    }
    pub fn fact_id(&self) -> &str {
        &self.fact_id
    }
    pub fn observation(&self) -> &ObservationSource {
        &self.observation
    }
}

/// The actual candidate Player anchor with at most its eligible typed label.
#[derive(Debug, PartialEq, Eq, Serialize)]
pub struct NarratorAuthoredSceneFrameV2 {
    version: u16,
    scope: Scope,
    before_revision: u64,
    after_revision: u64,
    player: String,
    location: String,
    location_label: Option<NarratorLocationLabelV1>,
}

impl NarratorAuthoredSceneFrameV2 {
    pub fn version(&self) -> u16 {
        self.version
    }
    pub fn scope(&self) -> &Scope {
        &self.scope
    }
    pub fn before_revision(&self) -> u64 {
        self.before_revision
    }
    pub fn after_revision(&self) -> u64 {
        self.after_revision
    }
    pub fn player(&self) -> &str {
        &self.player
    }
    pub fn location(&self) -> &str {
        &self.location
    }
    pub fn location_label(&self) -> Option<&NarratorLocationLabelV1> {
        self.location_label.as_ref()
    }
}

fn location_label(
    source: &Engine,
    candidate: &Engine,
    location: &str,
    cancel: &dyn Fn() -> bool,
) -> Result<Option<NarratorLocationLabelV1>, Error> {
    staged_play::check(cancel)?;
    let origin = source.seed().initial_world.as_ref().ok_or(Error::Version)?;
    // check_authored_seed validated the original materialization, including
    // seed.scope. These IDs follow that fixed initial-world-v1 typed recipe;
    // no proposition or corrected truth is parsed to recover a name.
    let prefix = source.seed().id.strip_prefix("world-").ok_or(Error::Rule)?;
    let mut selected = None;
    for (index, typed) in origin.accepted.locations.iter().enumerate() {
        staged_play::check(cancel)?;
        if location == format!("l-{prefix}-{index}") {
            selected = Some((index, typed));
            break;
        }
    }
    let (index, typed) = selected.ok_or(Error::CorruptHistory)?;
    let fact_id = format!("f-{prefix}-location-{index}");
    let original = source
        .seed()
        .facts
        .get(&fact_id)
        .ok_or(Error::CorruptHistory)?;
    let observed = candidate.observed_facts(
        &source.seed().player,
        candidate.scope(),
        candidate.revision(),
    )?;
    staged_play::check(cancel)?;
    let Some(known) = observed.get(&fact_id) else {
        return Ok(None);
    };
    if known.fact != fact_id {
        return Err(Error::CorruptHistory);
    }
    // Remembered seed knowledge is not replaced by unseen current truth. A
    // newly observed corrected free-text value has no typed label mapping.
    if known.proposition != original.proposition {
        return Ok(None);
    }
    Ok(Some(NarratorLocationLabelV1 {
        location_id: location.into(),
        name: typed.name.clone(),
        fact_id,
        // Eligible inherited observations retain their original ancestor scope.
        observation: known.observation.clone(),
    }))
}

impl Engine {
    pub fn stage_authored_scene_play_v2(
        &self,
        request: &Request,
        proposal: &Proposal,
        cancel: &dyn Fn() -> bool,
    ) -> Result<StagedAuthoredScenePlayV2, Error> {
        staged_play::check(cancel)?;
        authored_scene_narration::check_authored_seed(self)?;
        let staged = self.stage_play_v25(request, proposal, cancel)?;
        staged_play::check(cancel)?;
        let mut candidate = self.clone();
        candidate.append_play(staged.approved().clone())?;
        staged_play::check(cancel)?;
        let player = self.seed().player.clone();
        let location = candidate
            .character_context_v2(&player, candidate.scope(), candidate.revision())?
            .self_state
            .location;
        let label = location_label(self, &candidate, &location, cancel)?;
        let frame = NarratorAuthoredSceneFrameV2 {
            version: 2,
            scope: self.scope().clone(),
            before_revision: self.revision(),
            after_revision: candidate.revision(),
            player,
            location,
            location_label: label,
        };
        check_json_budget(&frame, MAX_RECEIPT_BYTES)?;
        staged_play::check(cancel)?;
        Ok(StagedAuthoredScenePlayV2 { staged, frame })
    }

    pub fn bind_authored_scene_play_v2(
        &self,
        preparation: StagedAuthoredScenePlayV2,
        recipe: AuthoredSceneRecipeV2,
        cancel: &dyn Fn() -> bool,
    ) -> Result<BoundAuthoredScenePlayV2, Error> {
        staged_play::check(cancel)?;
        authored_scene_narration::check_seed(self, recipe)?;
        if self.accepted_history_basis()? != preparation.staged.basis {
            return Err(Error::Stale);
        }
        let regenerated = self.stage_authored_scene_play_v2(
            preparation.approved().request(),
            preparation.approved().proposal(),
            cancel,
        )?;
        if regenerated.staged.basis != preparation.staged.basis
            || regenerated.approved() != preparation.approved()
            || regenerated.narrator_evidence() != preparation.narrator_evidence()
            || regenerated.scene_frame() != preparation.scene_frame()
        {
            return Err(Error::Stale);
        }
        let presentation = self.seed().presentation.clone();
        let provenance = authored_scene_narration::provenance(regenerated.scene_frame())?;
        staged_play::check(cancel)?;
        Ok(BoundAuthoredScenePlayV2 {
            preparation: regenerated,
            recipe,
            presentation,
            provenance,
        })
    }

    /// Consume and regenerate the whole source capability. A recorded exact
    /// request wins first, including after a later head or cancellation.
    pub fn commit_authored_scene_play_v2(
        &mut self,
        bound: BoundAuthoredScenePlayV2,
        record: &PlayRecord,
        cancel: &dyn Fn() -> bool,
    ) -> Result<Receipt, Error> {
        if let Some(receipt) = self.recorded(bound.approved().request())? {
            return Ok(receipt);
        }
        staged_play::check(cancel)?;
        let BoundAuthoredScenePlayV2 {
            preparation,
            recipe,
            presentation,
            provenance,
        } = bound;
        let regenerated = self.bind_authored_scene_play_v2(preparation, recipe, cancel)?;
        if regenerated.presentation != presentation || regenerated.provenance != provenance {
            return Err(Error::Stale);
        }
        authored_scene_narration::validate_record(self, &regenerated, record, cancel)?;
        self.validate_story_narration(&record.narration.text)?;
        let mut receipt = regenerated.preparation.staged.approved;
        receipt.narration = record.narration.text.clone();
        receipt.play = Some(record.clone());
        let mut candidate = self.clone();
        candidate.append_play(receipt.clone())?;
        staged_play::check(cancel)?;
        *self = candidate;
        Ok(receipt)
    }
}
