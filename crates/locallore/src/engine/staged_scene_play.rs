//! Source-bound scene preparation. This does not select a narration policy or
//! admit a generated record. Only the closed frame and sanitized evidence are
//! intended for a later provider request; the ordinary receipt stays native.
use super::{check_json_budget, staged_play, Engine};
use crate::contracts::{Error, Proposal, Receipt, Request, Scope, MAX_RECEIPT_BYTES};
use serde::Serialize;

/// Native preparation capability: no wire constructor, serialization or Clone.
/// Future scene-policy commit must consume and revalidate its complete stage.
pub struct StagedScenePlayV1 {
    staged: staged_play::StagedPlayV25,
    frame: NarratorSceneFrameV1,
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
