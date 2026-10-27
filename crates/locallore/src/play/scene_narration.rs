//! Additive source-bound narration construction. Native selection is not a
//! knowledge grant, and persisted hashes are claims to regenerate, not proof.
use super::{PlayContextPolicy, PlayRecord, PLAY_VERSION};
use crate::{
    contracts::Error,
    engine::{staged_scene_play::BoundScenePlayV1, Engine},
    memory_coverage::CoverageRead,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

mod renderer;
pub use renderer::{render_scene_narrator_v1, RenderedSceneNarratorV1};

pub const SCENE_PROMPT_VERSION_V1: &str = "locallore-play-v2.9-scene-frame-v1";
pub const LITERAL_SCENE_PROMPT_VERSION_V1: &str =
    "locallore-play-v2.10-literal-director-v1-scene-frame-v1";
pub const SCENE_NARRATION_POLICY_V1: &str = "grounded-prose-v2.4-scene-frame-v1";

/// Deliberate trusted-native construction; no wire constructor or policy guess.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum SceneRecipeV1 {
    Memory(PlayContextPolicy),
    LiteralV1,
}
impl SceneRecipeV1 {
    pub(crate) fn prompt_version(self) -> &'static str {
        match self {
            Self::Memory(_) => SCENE_PROMPT_VERSION_V1,
            Self::LiteralV1 => LITERAL_SCENE_PROMPT_VERSION_V1,
        }
    }
}
pub struct ScenePlayConstructionInput<'a> {
    pub recipe: SceneRecipeV1,
    pub coverage: Option<&'a CoverageRead>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SceneNarrationRecordV1 {
    pub version: u16,
    pub frame_sha256: String,
}

pub(crate) fn check(cancel: &dyn Fn() -> bool) -> Result<(), Error> {
    if std::panic::catch_unwind(std::panic::AssertUnwindSafe(cancel)).unwrap_or(true) {
        Err(Error::Cancelled)
    } else {
        Ok(())
    }
}
pub(crate) fn provenance(
    frame: &crate::engine::staged_scene_play::NarratorSceneFrameV1,
) -> Result<SceneNarrationRecordV1, Error> {
    let bytes = serde_json::to_vec(frame).map_err(|_| Error::TooLarge)?;
    Ok(SceneNarrationRecordV1 {
        version: 1,
        frame_sha256: format!("{:x}", Sha256::digest(bytes)),
    })
}
pub(crate) fn check_seed(engine: &Engine, recipe: SceneRecipeV1) -> Result<(), Error> {
    if engine.seed().initial_world.is_some()
        || (matches!(recipe, SceneRecipeV1::LiteralV1) && engine.domain_version() != 1)
    {
        return Err(Error::Version);
    }
    super::story_presentation::binding(engine)?;
    Ok(())
}
pub(crate) fn validate_record(
    engine: &Engine,
    bound: &BoundScenePlayV1,
    record: &PlayRecord,
    cancel: &dyn Fn() -> bool,
) -> Result<(), Error> {
    check(cancel)?;
    check_seed(engine, bound.recipe())?;
    record.profile.validate()?;
    if record.version != PLAY_VERSION
        || record.policy != SCENE_NARRATION_POLICY_V1
        || record.prompt_version != bound.recipe().prompt_version()
        || record.scene.as_ref() != Some(&provenance(bound.scene_frame())?)
        || record.story_presentation
            != super::story_presentation::binding_for_presentation(bound.presentation())?
    {
        return Err(Error::Narration);
    }
    match bound.recipe() {
        SceneRecipeV1::Memory(policy) => {
            if record.context_policy != Some(policy) {
                return Err(Error::Narration);
            }
            super::validate_memory_context_record(engine, bound.approved(), record)?;
        }
        SceneRecipeV1::LiteralV1 => {
            super::validate_literal_context_record(engine, bound.approved(), record, cancel)?;
        }
    }
    super::validate_staged_record_contents(
        engine,
        bound.approved(),
        bound.narrator_evidence(),
        record,
    )?;
    if !record.fallback {
        renderer::validate_generated(bound, &record.narration.text)?;
    }
    check(cancel)
}
