//! Source-bound scene preparation. This does not select a narration policy or
//! admit a generated record. Only the closed frame and sanitized evidence are
//! intended for a later provider request; the ordinary receipt stays native.
use super::{check_json_budget, staged_play, Engine};
use crate::contracts::{Error, Proposal, Receipt, Request, Scope, MAX_RECEIPT_BYTES};
use crate::{
    play::{
        scene_narration::{self, SceneNarrationRecordV1, SceneRecipeV1},
        PlayRecord,
    },
    story_presentation::StoryPresentationV1,
};
use serde::Serialize;

/// Native preparation capability: no wire constructor, serialization or Clone.
/// Future scene-policy commit must consume and revalidate its complete stage.
pub struct StagedScenePlayV1 {
    staged: staged_play::StagedPlayV25,
    frame: NarratorSceneFrameV1,
}

/// Consumed source/recipe capability, never constructed from a record hash.
pub struct BoundScenePlayV1 {
    preparation: StagedScenePlayV1,
    recipe: SceneRecipeV1,
    presentation: Option<StoryPresentationV1>,
    provenance: SceneNarrationRecordV1,
}
impl BoundScenePlayV1 {
    pub fn approved(&self) -> &Receipt {
        self.preparation.approved()
    }
    pub fn narrator_evidence(&self) -> &staged_play::NarratorEvidenceV22 {
        self.preparation.narrator_evidence()
    }
    pub fn scene_frame(&self) -> &NarratorSceneFrameV1 {
        self.preparation.scene_frame()
    }
    pub fn recipe(&self) -> SceneRecipeV1 {
        self.recipe
    }
    pub(crate) fn presentation(&self) -> Option<&StoryPresentationV1> {
        self.presentation.as_ref()
    }
    pub(crate) fn provenance(&self) -> &SceneNarrationRecordV1 {
        &self.provenance
    }
}

impl StagedScenePlayV1 {
    pub fn approved(&self) -> &Receipt {
        self.staged.approved()
    }
    pub fn narrator_evidence(&self) -> &staged_play::NarratorEvidenceV22 {
        self.staged.narrator_evidence()
    }
    pub fn scene_frame(&self) -> &NarratorSceneFrameV1 {
        &self.frame
    }
}

/// Provider-safe location identity derived from the actual candidate's Player
/// self-profile policy. No location catalog, NPC data or world facts are copied.
#[derive(Debug, PartialEq, Eq, Serialize)]
pub struct NarratorSceneFrameV1 {
    version: u16,
    scope: Scope,
    before_revision: u64,
    after_revision: u64,
    player: String,
    location: String,
}

impl NarratorSceneFrameV1 {
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
}

impl Engine {
    /// Bind to actual complete history and exact native construction. The
    /// original preparation is rederived, not admitted by matching head alone.
    pub fn bind_scene_play_v1(
        &self,
        preparation: StagedScenePlayV1,
        recipe: SceneRecipeV1,
        cancel: &dyn Fn() -> bool,
    ) -> Result<BoundScenePlayV1, Error> {
        staged_play::check(cancel)?;
        scene_narration::check_seed(self, recipe)?;
        if self.accepted_history_basis()? != preparation.staged.basis {
            return Err(Error::Stale);
        }
        let regenerated = self.stage_scene_play_v1(
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
        let provenance = scene_narration::provenance(regenerated.scene_frame())?;
        staged_play::check(cancel)?;
        Ok(BoundScenePlayV1 {
            preparation: regenerated,
            recipe,
            presentation,
            provenance,
        })
    }

    /// Exact recorded retry wins first. Fresh installation consumes and
    /// regenerates the complete capability, including typed seed presentation.
    pub fn commit_scene_play_v1(
        &mut self,
        bound: BoundScenePlayV1,
        record: &PlayRecord,
        cancel: &dyn Fn() -> bool,
    ) -> Result<Receipt, Error> {
        self.commit_scene_play_history_v1(bound, record, cancel, false)
    }

    /// Only recorded-history dispatch may retain a prior scene prose policy.
    /// The public commit remains fresh-only, with the same capability checks.
    pub(crate) fn commit_scene_play_history_v1(
        &mut self,
        bound: BoundScenePlayV1,
        record: &PlayRecord,
        cancel: &dyn Fn() -> bool,
        recorded_history: bool,
    ) -> Result<Receipt, Error> {
        if let Some(receipt) = self.recorded(bound.approved().request())? {
            return Ok(receipt);
        }
        staged_play::check(cancel)?;
        let BoundScenePlayV1 {
            preparation,
            recipe,
            presentation,
            provenance,
        } = bound;
        let regenerated = self.bind_scene_play_v1(preparation, recipe, cancel)?;
        if regenerated.presentation != presentation || regenerated.provenance != provenance {
            return Err(Error::Stale);
        }
        scene_narration::validate_record_history(
            self,
            &regenerated,
            record,
            cancel,
            recorded_history,
        )?;
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

    /// Prepare a closed scene anchor over the existing validated native stage.
    /// This neither commits the candidate nor changes current generation/replay.
    pub fn stage_scene_play_v1(
        &self,
        request: &Request,
        proposal: &Proposal,
        cancel: &dyn Fn() -> bool,
    ) -> Result<StagedScenePlayV1, Error> {
        let staged = self.stage_play_v25(request, proposal, cancel)?;
        staged_play::check(cancel)?;

        // Reuse the actual canonical append on a transient clone. The existing
        // stage retains the full accepted-history basis; no alternate state or
        // retained candidate is introduced by this preparation wrapper.
        let mut candidate = self.clone();
        candidate.append_play(staged.approved().clone())?;
        staged_play::check(cancel)?;
        let player = self.seed().player.clone();
        let location = candidate
            .character_context_v2(&player, candidate.scope(), candidate.revision())?
            .self_state
            .location;
        staged_play::check(cancel)?;
        let frame = NarratorSceneFrameV1 {
            version: 1,
            scope: self.scope().clone(),
            before_revision: self.revision(),
            after_revision: candidate.revision(),
            player,
            location,
        };
        check_json_budget(&frame, MAX_RECEIPT_BYTES)?;
        staged_play::check(cancel)?;
        Ok(StagedScenePlayV1 { staged, frame })
    }
}
