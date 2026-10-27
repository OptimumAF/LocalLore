//! Closed literal/relevant comparison metadata and private capture validation.
//! Actual protocol3 execution lives in the separately scoped comparison driver.
//! Deserializing these values grants no execution or canonical authority.
use crate::{capture_envelope, encode, Capture, Result};
use locallore::{
    context_compiler::{player_literal_transcript_v1_cancelled, ContextPolicy},
    contracts::Request,
    engine::Engine,
    play::{self, DirectorPassV25, PlayProfile, PlayRecord},
};
use serde::{Deserialize, Deserializer, Serialize};
use serde_json::Value;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ComparisonArmV3 {
    LiteralPlayerV1,
    RelevantMemoryV1,
}

// An Option field with this deserializer is REQUIRED on the wire, including
// when its value is null. Ordinary Option derive would silently admit omission.
pub(crate) fn required_nullable<'de, D, T>(
    deserializer: D,
) -> std::result::Result<Option<T>, D::Error>
where
    D: Deserializer<'de>,
    T: Deserialize<'de>,
{
    Option::deserialize(deserializer)
}

/// Closed metadata, never convertible to Host configuration or canonical input.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ArmDescriptorV3 {
    pub arm: ComparisonArmV3,
    pub prompt_version: String,
    pub narration_policy: String,
    pub director_schema_id: String,
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
}

pub fn arm_descriptors() -> [ArmDescriptorV3; 2] {
    [
        ArmDescriptorV3 {
            arm: ComparisonArmV3::LiteralPlayerV1,
            prompt_version: play::LITERAL_PLAY_PROMPT_VERSION_V1.into(),
            narration_policy: play::NARRATION_POLICY.into(),
            director_schema_id: "locallore-director-literal-v1".into(),
            context_policy: None,
            compiler_version: None,
            context_version: None,
            literal_source_version: Some(1),
            literal_render_version: Some(1),
            literal_schema_version: Some(1),
            literal_packing_version: Some(1),
            forwarded_budget_version: 1,
        },
        ArmDescriptorV3 {
            arm: ComparisonArmV3::RelevantMemoryV1,
            prompt_version: play::PROMPT_VERSION.into(),
            narration_policy: play::NARRATION_POLICY.into(),
            director_schema_id: "locallore-director-v2".into(),
            context_policy: Some(ContextPolicy::StateRelevantMemoryV1),
            compiler_version: Some(2),
            context_version: Some(2),
            literal_source_version: None,
            literal_render_version: None,
            literal_schema_version: None,
            literal_packing_version: None,
            forwarded_budget_version: 1,
        },
    ]
}
impl ArmDescriptorV3 {
    pub fn validate(&self) -> Result<()> {
        let expected = match self.arm {
            ComparisonArmV3::LiteralPlayerV1 => &arm_descriptors()[0],
            ComparisonArmV3::RelevantMemoryV1 => &arm_descriptors()[1],
        };
        if self != expected {
            return Err("ArmDescriptorBinding".into());
        }
        Ok(())
    }
}

/// Private owned evidence; no serde or conversion to execution authority.
/// A future producer must additionally validate raw files, source/row hashes,
/// canonical history and ledger. Narrator checks cover envelope/hash/order only.
pub(crate) struct CapturedLiteralContext {
    pub director_prompts: Vec<String>,
    pub narrator_prompts: Vec<String>,
    pub director_estimates: Vec<Value>,
    pub source_units: usize,
    pub selected_start: usize,
    pub selected_units: usize,
}
impl CapturedLiteralContext {
    #[allow(clippy::too_many_arguments)]
    pub(crate) fn from_host_capture(
        before: &Engine,
        request: &Request,
        attempt: u32,
        reply: &Value,
        captures: &[Capture],
        profile: &PlayProfile,
        forwarded_budget_version: u16,
    ) -> Result<Self> {
        if forwarded_budget_version != 1 {
            return Err("CaptureBudgetVersion".into());
        }
        let artifacts = capture_envelope::artifacts(before, request, attempt, reply)?;
        if captures.is_empty() {
            return Err("CaptureUnavailable".into());
        }
        if captures.len() > 3 {
            return Err("CaptureBudget".into());
        }
        profile.validate().map_err(|_| "CaptureProfile")?;
        if profile.context_tokens != 4096
            || profile.director_tokens != 350
            || profile.narrator_tokens != 350
            || profile.deadline_ms != 120_000
            || profile.repair_limit != 1
        {
            return Err("CaptureProfile".into());
        }

        let mut requests = Vec::new();
        let mut candidate = None;
        for (ordinal, a) in artifacts.iter().enumerate() {
            capture_envelope::artifact(ordinal, a)?;
            let value = &a["value"];
            match a["kind"].as_str().ok_or("CaptureMalformed")? {
                "selected_context" => return Err("CaptureVersion".into()),
                "generation_request" => requests.push(value),
                "accepted_candidate_not_durable_commit" => {
                    if candidate.replace(value).is_some() {
                        return Err("CaptureMalformed".into());
                    }
                }
                "raw_director_output"
                | "raw_narrator_output"
                | "parsed_proposal"
                | "validated_plan_not_durable_commit" => {}
                _ => return Err("CaptureMalformed".into()),
            }
        }
        if !requests.iter().any(|v| v["input"]["role"] == "director") {
            return Err("CaptureUnavailable".into());
        }
        if requests.len() != captures.len() {
            return Err("CaptureRecordingMismatch".into());
        }
        let roles: Vec<_> = requests
            .iter()
            .map(|v| v["input"]["role"].as_str().unwrap_or(""))
            .collect();
        if !matches!(
            roles.as_slice(),
            ["director"]
                | ["director", "director"]
                | ["director", "narrator"]
                | ["director", "director", "narrator"]
        ) {
            return Err("CaptureRecordingMismatch".into());
        }
        let source = player_literal_transcript_v1_cancelled(
            before,
            before.scope(),
            before.revision(),
            &before.seed().player,
            &|| false,
        )
        .map_err(|_| "CaptureSource")?;
        let initial = play::render_player_literal_director_v1_cancelled(
            before,
            request,
            &source,
            profile,
            DirectorPassV25::Initial,
            &|| false,
        )
        .map_err(|_| "CaptureForwardingMismatch")?;
        let mut result = Self {
            director_prompts: Vec::new(),
            narrator_prompts: Vec::new(),
            director_estimates: Vec::new(),
            source_units: initial.source_units(),
            selected_start: initial.selected_start(),
            selected_units: initial.selected_units(),
        };
        for (index, value) in requests.into_iter().enumerate() {
            let checked = capture_envelope::generation(
                before,
                request,
                value,
                captures,
                profile,
                "locallore-director-literal-v1",
            )?;
            let recording = &captures[index];
            // Check ordered multiplicity, not merely membership in the same set.
            if !std::ptr::eq(checked.recording, recording)
                || recording.compiler_version.is_some()
                || recording.player_text_sha256.is_some()
            {
                return Err("CaptureRecordingMismatch".into());
            }
            if checked.role == "director" {
                let pass = if result.director_prompts.is_empty() {
                    DirectorPassV25::Initial
                } else {
                    DirectorPassV25::Repair
                };
                let rendered = play::render_player_literal_director_v1_cancelled(
                    before,
                    request,
                    &source,
                    profile,
                    pass,
                    &|| false,
                )
                .map_err(|_| "CaptureForwardingMismatch")?;
                if checked.prompt != rendered.prompt()
                    || value["input"]["schema"] != *rendered.schema()
                {
                    return Err("CaptureForwardingMismatch".into());
                }
                if pass == DirectorPassV25::Repair
                    && !play::director_repair_matches_v25(
                        &result.director_prompts[0],
                        checked.prompt,
                    )
                {
                    return Err("CaptureRepairMismatch".into());
                }
                let estimate = play::director_forwarded_budget_v25(
                    profile,
                    pass,
                    checked.prompt,
                    &value["input"]["schema"],
                )
                .map_err(|_| "CaptureForwardedBudget")?;
                if encode(&estimate)? != encode(rendered.forwarded())? {
                    return Err("CaptureForwardedBudget".into());
                }
                result
                    .director_estimates
                    .push(serde_json::to_value(estimate).map_err(|_| "Encoding")?);
                result.director_prompts.push(checked.prompt.to_owned());
            } else {
                result.narrator_prompts.push(checked.prompt.to_owned());
            }
        }
        if let Some(candidate) = candidate {
            let record: PlayRecord =
                serde_json::from_value(candidate["play"].clone()).map_err(|_| "CaptureVersion")?;
            if record.version != play::PLAY_VERSION
                || record.prompt_version != play::LITERAL_PLAY_PROMPT_VERSION_V1
                || record.policy != play::NARRATION_POLICY
                || record.profile != *profile
                || record.context.is_some()
                || record.context_policy.is_some()
                || usize::from(record.repairs) != result.director_prompts.len() - 1
            {
                return Err("CaptureVersion".into());
            }
        }
        Ok(result)
    }
}

pub const VERSION: u16 = 3;
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ConstructionEvidenceStatusV3 {
    ValidatedLiteral,
    ValidatedRelevant,
    NotApplicableGuard,
    NotApplicableDependency,
    Unavailable,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CurrentBindingV3 {
    pub protocol_version: u16,
    pub arms: [ArmDescriptorV3; 2],
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
pub fn current_binding(native: bool) -> Result<CurrentBindingV3> {
    let previous = crate::memory_comparison_v2::current_binding(native)?;
    Ok(CurrentBindingV3 {
        protocol_version: VERSION,
        arms: arm_descriptors(),
        source_sha256: previous.source_sha256,
        suite_sha256: previous.suite_sha256,
        forwarded_budget_version: 1,
        max_admissions: previous.max_admissions,
        max_roles: previous.max_roles,
        max_active_ms: previous.max_active_ms,
        attempts: previous.attempts,
        expected_accepted: previous.expected_accepted,
        expected_guard_only: previous.expected_guard_only,
        native,
    })
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct TurnReportV3 {
    pub turn: String,
    pub scene: u8,
    pub arm: String,
    pub construction: ArmDescriptorV3,
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
    pub construction_evidence_status: ConstructionEvidenceStatusV3,
    #[serde(deserialize_with = "required_nullable")]
    pub literal_source_units: Option<usize>,
    #[serde(deserialize_with = "required_nullable")]
    pub literal_selected_start: Option<usize>,
    #[serde(deserialize_with = "required_nullable")]
    pub literal_selected_units: Option<usize>,
    pub context_evidence_available: bool,
    pub context_requirement: String,
    pub privacy_passed: bool,
    #[serde(deserialize_with = "required_nullable")]
    pub fallback: Option<bool>,
    #[serde(deserialize_with = "required_nullable")]
    pub capture_sha256: Option<String>,
    #[serde(deserialize_with = "required_nullable")]
    pub recording_sha256: Option<String>,
    pub raw_sha256: Vec<String>,
    #[serde(deserialize_with = "required_nullable")]
    pub role_metrics: Option<Value>,
    #[serde(deserialize_with = "required_nullable")]
    pub trace: Option<Value>,
    #[serde(deserialize_with = "required_nullable")]
    pub actual_receipt_sha256: Option<String>,
    #[serde(deserialize_with = "required_nullable")]
    pub source_fallback_reason: Option<String>,
    #[serde(deserialize_with = "required_nullable")]
    pub compiler_fallback_reason: Option<String>,
    #[serde(deserialize_with = "required_nullable")]
    pub narration: Option<String>,
    #[serde(deserialize_with = "required_nullable")]
    pub repairs: Option<u8>,
    pub stages: Vec<Value>,
    #[serde(deserialize_with = "required_nullable")]
    pub mandatory_sha256: Option<String>,
    #[serde(deserialize_with = "required_nullable")]
    pub optional_detail_selected: Option<bool>,
    #[serde(deserialize_with = "required_nullable")]
    pub director_private_target_present: Option<bool>,
    #[serde(deserialize_with = "required_nullable")]
    pub selected_context_bytes: Option<usize>,
    #[serde(deserialize_with = "required_nullable")]
    pub estimated_context_tokens: Option<u64>,
    #[serde(deserialize_with = "required_nullable")]
    pub forwarded_director_estimates: Option<Vec<Value>>,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ComparisonReportV3 {
    pub version: u16,
    pub arms: [ArmDescriptorV3; 2],
    pub kind: crate::memory_comparison_v2::ComparisonKind,
    pub lane: String,
    pub source_matches: bool,
    pub completed: bool,
    pub completed_scenes: usize,
    pub turns: Vec<TurnReportV3>,
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
    pub unavailable: Vec<String>,
    pub profile: PlayProfile,
    pub suite_sha256: String,
    pub source_sha256: String,
    #[serde(deserialize_with = "required_nullable")]
    pub reference_sha256: Option<String>,
    pub limitations: Vec<String>,
}
