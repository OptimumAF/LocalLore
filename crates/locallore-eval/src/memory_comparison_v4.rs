//! Closed scene-comparison metadata. Deserialization grants no native authority.
pub(crate) use crate::memory_comparison_v3::required_nullable;
use crate::Result;
use locallore::{
    context_compiler::ContextPolicy,
    play::{scene_narration, PlayProfile},
};
use serde::{Deserialize, Serialize};
use serde_json::Value;

pub const VERSION: u16 = 4;
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ComparisonArmV4 {
    LiteralSceneV1,
    RelevantMemorySceneV1,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ArmDescriptorV4 {
    pub arm: ComparisonArmV4,
    pub prompt_version: String,
    pub narration_policy: String,
    pub director_schema_id: String,
    pub narrator_schema_id: String,
    #[serde(deserialize_with = "required_nullable")]
    pub context_policy: Option<ContextPolicy>,
    #[serde(deserialize_with = "required_nullable")]
    pub compiler_version: Option<u16>,
    #[serde(deserialize_with = "required_nullable")]
    pub context_version: Option<u16>,
    #[serde(deserialize_with = "required_nullable")]
    pub literal_source_version: Option<u16>,
    #[serde(deserialize_with = "required_nullable")]
    pub literal_render_version: Option<u16>,
    #[serde(deserialize_with = "required_nullable")]
    pub literal_schema_version: Option<u16>,
    #[serde(deserialize_with = "required_nullable")]
    pub literal_packing_version: Option<u16>,
    pub forwarded_budget_version: u16,
    pub scene_frame_version: u16,
    pub scene_capture_gate_version: u16,
}
pub fn arm_descriptors() -> [ArmDescriptorV4; 2] {
    [
        ArmDescriptorV4 {
            arm: ComparisonArmV4::LiteralSceneV1,
            prompt_version: scene_narration::LITERAL_SCENE_PROMPT_VERSION_V1.into(),
            narration_policy: scene_narration::SCENE_NARRATION_POLICY_V1.into(),
            director_schema_id: "locallore-director-literal-v1".into(),
            narrator_schema_id: "locallore-narrator-v2".into(),
            context_policy: None,
            compiler_version: None,
            context_version: None,
            literal_source_version: Some(1),
            literal_render_version: Some(1),
            literal_schema_version: Some(1),
            literal_packing_version: Some(1),
            forwarded_budget_version: 1,
            scene_frame_version: 1,
            scene_capture_gate_version: 1,
        },
        ArmDescriptorV4 {
            arm: ComparisonArmV4::RelevantMemorySceneV1,
            prompt_version: scene_narration::SCENE_PROMPT_VERSION_V1.into(),
            narration_policy: scene_narration::SCENE_NARRATION_POLICY_V1.into(),
            director_schema_id: "locallore-director-v2".into(),
            narrator_schema_id: "locallore-narrator-v2".into(),
            context_policy: Some(ContextPolicy::StateRelevantMemoryV1),
            compiler_version: Some(2),
            context_version: Some(2),
            literal_source_version: None,
            literal_render_version: None,
            literal_schema_version: None,
            literal_packing_version: None,
            forwarded_budget_version: 1,
            scene_frame_version: 1,
            scene_capture_gate_version: 1,
        },
    ]
}
impl ArmDescriptorV4 {
    pub fn validate(&self) -> Result<()> {
        let index = usize::from(self.arm == ComparisonArmV4::RelevantMemorySceneV1);
        if *self != arm_descriptors()[index] && *self != current_arm_descriptors()[index] {
            return Err("ArmDescriptorBinding".into());
        }
        Ok(())
    }
}

/// Current writers opt into the strict policy; original descriptor bytes stay fixed.
pub fn current_arm_descriptors() -> [ArmDescriptorV4; 2] {
    let mut arms = arm_descriptors();
    for arm in &mut arms {
        arm.narration_policy = scene_narration::SCENE_NARRATION_POLICY_V2.into();
    }
    arms
}

pub fn validate_arm_family(arms: &[ArmDescriptorV4; 2]) -> Result<()> {
    if arms != &arm_descriptors() && arms != &current_arm_descriptors() {
        return Err("ArmDescriptorBinding".into());
    }
    Ok(())
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CurrentBindingV4 {
    pub protocol_version: u16,
    pub arms: [ArmDescriptorV4; 2],
    pub source_sha256: String,
    pub suite_sha256: String,
    pub forwarded_budget_version: u16,
    pub max_admissions: usize,
    pub max_roles: usize,
    pub max_active_ms: u64,
    pub attempts: usize,
    pub expected_accepted: usize,
    pub expected_guard_only: usize,
    pub native: bool,
}
pub fn current_binding(native: bool) -> Result<CurrentBindingV4> {
    let existing = crate::memory_comparison_v2::current_binding(native)?;
    Ok(CurrentBindingV4 {
        protocol_version: VERSION,
        arms: current_arm_descriptors(),
        source_sha256: existing.source_sha256,
        suite_sha256: existing.suite_sha256,
        forwarded_budget_version: 1,
        max_admissions: existing.max_admissions,
        max_roles: existing.max_roles,
        max_active_ms: existing.max_active_ms,
        attempts: existing.attempts,
        expected_accepted: existing.expected_accepted,
        expected_guard_only: existing.expected_guard_only,
        native,
    })
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ConstructionEvidenceStatusV4 {
    ValidatedCommittedSceneNarratorV1,
    NotApplicableGuard,
    NotApplicableDependency,
    Unavailable,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PrivacyEvidenceStatusV4 {
    CheckedFiniteSentinels,
    NotApplicableGuard,
    Unavailable,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct TurnReportV4 {
    pub turn: String,
    pub scene: u8,
    pub arm: String,
    pub construction: ArmDescriptorV4,
    pub phase: String,
    #[serde(deserialize_with = "required_nullable")]
    pub error: Option<String>,
    pub expected: String,
    pub passed: bool,
    pub failures: Vec<String>,
    pub quality_flags: Vec<String>,
    pub roles: usize,
    pub roles_known: bool,
    pub recovered_without_checkpoint: bool,
    #[serde(deserialize_with = "required_nullable")]
    pub admission: Option<usize>,
    pub elapsed_ms: u64,
    #[serde(deserialize_with = "required_nullable")]
    pub first_final_response_ms: Option<u64>,
    #[serde(deserialize_with = "required_nullable")]
    pub commit_elapsed_ms: Option<u64>,
    pub input_semantic_sha256: String,
    pub output_semantic_sha256: String,
    pub mechanical_sha256: String,
    pub construction_matches: bool,
    pub construction_evidence_status: ConstructionEvidenceStatusV4,
    #[serde(deserialize_with = "required_nullable")]
    pub construction_evidence_reason: Option<String>,
    #[serde(deserialize_with = "required_nullable")]
    pub narrator_prompt_sha256: Option<String>,
    #[serde(deserialize_with = "required_nullable")]
    pub narrator_schema_sha256: Option<String>,
    #[serde(deserialize_with = "required_nullable")]
    pub scene_frame_sha256: Option<String>,
    #[serde(deserialize_with = "required_nullable")]
    pub actual_receipt_sha256: Option<String>,
    pub privacy_evidence_status: PrivacyEvidenceStatusV4,
    #[serde(deserialize_with = "required_nullable")]
    pub fallback: Option<bool>,
    #[serde(deserialize_with = "required_nullable")]
    pub repairs: Option<u8>,
    #[serde(deserialize_with = "required_nullable")]
    pub narration: Option<String>,
    #[serde(deserialize_with = "required_nullable")]
    pub capture_sha256: Option<String>,
    #[serde(deserialize_with = "required_nullable")]
    pub recording_sha256: Option<String>,
    pub raw_sha256: Vec<String>,
    #[serde(deserialize_with = "required_nullable")]
    pub role_metrics: Option<Value>,
    #[serde(deserialize_with = "required_nullable")]
    pub trace: Option<Value>,
    pub stages: Vec<Value>,
    #[serde(deserialize_with = "required_nullable")]
    pub source_fallback_reason: Option<String>,
    #[serde(deserialize_with = "required_nullable")]
    pub compiler_fallback_reason: Option<String>,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ComparisonReportV4 {
    pub version: u16,
    pub arms: [ArmDescriptorV4; 2],
    pub kind: crate::memory_comparison_v2::ComparisonKind,
    pub lane: String,
    pub source_matches: bool,
    pub completed: bool,
    pub completed_scenes: usize,
    pub turns: Vec<TurnReportV4>,
    pub human_reviewed: usize,
    pub human_rubric: String,
    pub quality_accepted: bool,
    pub physical_setups: usize,
    #[serde(deserialize_with = "required_nullable")]
    pub physical_setup_ms: Option<u64>,
    #[serde(deserialize_with = "required_nullable")]
    pub native_load: Option<Value>,
    pub left_charged_ms: u64,
    pub right_charged_ms: u64,
    pub left_reserved_roles: usize,
    pub right_reserved_roles: usize,
    #[serde(deserialize_with = "required_nullable")]
    pub first_semantic_divergence: Option<String>,
    #[serde(deserialize_with = "required_nullable")]
    pub first_mechanical_divergence: Option<String>,
    pub same_input_pairs: usize,
    pub source_bound_committed_rows: usize,
    pub unavailable: Vec<String>,
    pub profile: PlayProfile,
    pub suite_sha256: String,
    pub source_sha256: String,
    #[serde(deserialize_with = "required_nullable")]
    pub reference_sha256: Option<String>,
    pub limitations: Vec<String>,
}
