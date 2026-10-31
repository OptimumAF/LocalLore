//! Current construction-policy experiment data, not a second compiler or authority.
#[cfg(test)]
mod literal_capture_legacy_tests;
use crate::{digest, encode, local_lane, memory_comparison as old, Capture, Result, SOURCE_INPUTS};
use locallore::{
    context_compiler::ContextPolicy,
    contracts::*,
    engine::Engine,
    play::{
        director_forwarded_budget_v25, director_repair_matches_v25, DirectorPassV25, PlayProfile,
        NARRATION_POLICY, PROMPT_VERSION,
    },
};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};

pub const VERSION: u16 = 2;
/// Immutable narrator policy of the original protocol2/3 captures.
pub const LEGACY_NARRATION_POLICY: &str = "grounded-prose-v2.2";
pub use crate::capture_envelope::MAX_PRIVATE_CAPTURE;
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ComparisonKind {
    PairedSnapshots,
    ContinuousRollout,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SuiteIdentity {
    pub turns: Vec<(String, String)>,
    pub sha256: String,
}
pub fn suite_identity() -> Result<SuiteIdentity> {
    let s = old::frozen_suite().map_err(|_| "Suite")?;
    Ok(SuiteIdentity {
        turns: s
            .steps()
            .iter()
            .map(|s| (s.id().to_owned(), s.text().to_owned()))
            .collect(),
        sha256: s.sha256().map_err(|_| "Suite")?,
    })
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CurrentBinding {
    pub protocol_version: u16,
    pub source_sha256: String,
    pub suite_sha256: String,
    pub prompt_version: String,
    pub narration_policy: String,
    pub compiler_version: u16,
    pub context_version: u16,
    /// Absent only on immutable historical reports; it cannot authorize resume.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub forwarded_budget_version: Option<u16>,
    pub policies: Vec<ContextPolicy>,
    pub max_admissions: usize,
    pub max_roles: usize,
    pub max_active_ms: u64,
    pub attempts: usize,
    pub expected_accepted: usize,
    pub expected_guard_only: usize,
    pub native: bool,
}
pub fn current_binding(native: bool) -> Result<CurrentBinding> {
    let sources: Vec<_> = SOURCE_INPUTS
        .iter()
        .map(|(name, bytes)| (*name, digest(bytes)))
        .collect();
    Ok(CurrentBinding {
        protocol_version: 2,
        source_sha256: digest(&encode(&sources)?),
        suite_sha256: suite_identity()?.sha256,
        prompt_version: PROMPT_VERSION.into(),
        narration_policy: NARRATION_POLICY.into(),
        compiler_version: 2,
        context_version: 2,
        forwarded_budget_version: Some(1),
        policies: vec![
            ContextPolicy::StateRecentTranscriptV1,
            ContextPolicy::StateRelevantMemoryV1,
        ],
        max_admissions: local_lane::MAX_ADMISSIONS,
        max_roles: local_lane::MAX_ROLES,
        max_active_ms: local_lane::MAX_ACTIVE_MS,
        attempts: 24,
        expected_accepted: 21,
        expected_guard_only: 3,
        native,
    })
}
fn canon_semantics(engine: &Engine) -> Result<Value> {
    if engine.domain_version() != 1 {
        return Err("UnsupportedDomain".into());
    }
    let receipts:Vec<_>=engine.receipts().iter().map(|r|json!({"request":r.request(),"proposal":r.proposal(),"events":r.events(),"narration":r.narration()})).collect();
    Ok(
        json!({"seed":engine.seed(),"scope":engine.scope(),"revision":engine.revision(),"receipts":receipts}),
    )
}
pub fn semantic_input(engine: &Engine, request: &Request) -> Result<String> {
    if request.scope != *engine.scope() || request.expected_revision != engine.revision() {
        return Err("InputBinding".into());
    }
    Ok(digest(&encode(
        &json!({"canon":canon_semantics(engine)?,"request":request}),
    )?))
}
pub(crate) fn semantic_output(engine: &Engine) -> Result<String> {
    Ok(digest(&encode(&canon_semantics(engine)?)?))
}
pub(crate) fn mechanical_output(engine: &Engine) -> Result<String> {
    if engine.domain_version() != 1 {
        return Err("UnsupportedDomain".into());
    }
    let receipts: Vec<_> = engine
        .receipts()
        .iter()
        .map(|r| json!({"request":r.request(),"proposal":r.proposal(),"events":r.events()}))
        .collect();
    Ok(digest(&encode(
        &json!({"seed":engine.seed(),"scope":engine.scope(),"revision":engine.revision(),"receipts":receipts}),
    )?))
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct TurnReportV2 {
    pub turn: String,
    pub scene: u8,
    pub arm: String,
    pub policy: ContextPolicy,
    pub phase: String,
    pub error: Option<String>,
    pub expected: String,
    pub passed: bool,
    pub failures: Vec<String>,
    pub quality_flags: Vec<String>,
    pub roles: usize,
    pub roles_known: bool,
    pub recovered_without_checkpoint: bool,
    pub admission: Option<usize>,
    pub elapsed_ms: u64,
    pub first_final_response_ms: Option<u64>,
    pub commit_elapsed_ms: Option<u64>,
    pub input_semantic_sha256: String,
    pub output_semantic_sha256: String,
    pub mechanical_sha256: String,
    pub policy_matches: bool,
    pub context_evidence_available: bool,
    pub context_requirement: String,
    pub privacy_passed: bool,
    pub fallback: Option<bool>,
    pub capture_sha256: Option<String>,
    pub recording_sha256: Option<String>,
    pub raw_sha256: Vec<String>,
    pub role_metrics: Option<Value>,
    pub trace: Option<Value>,
    pub actual_receipt_sha256: Option<String>,
    pub source_fallback_reason: Option<String>,
    pub compiler_fallback_reason: Option<String>,
    pub narration: Option<String>,
    pub repairs: Option<u8>,
    pub stages: Vec<Value>,
    pub mandatory_sha256: Option<String>,
    pub optional_detail_selected: Option<bool>,
    pub director_private_target_present: Option<bool>,
    pub selected_context_bytes: Option<usize>,
    pub estimated_context_tokens: Option<u64>,
    /// Checked actual role-byte estimates, independent of full diagnostic wire.
    /// Missing historical values remain missing, never reconstructed as proof.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub forwarded_director_estimates: Option<Vec<Value>>,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ReferenceReportV2 {
    pub version: u16,
    pub source_sha256: String,
    pub suite_sha256: String,
    pub accepted: usize,
    pub guard_only: usize,
    pub roles: usize,
    pub turns: Vec<TurnReportV2>,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ComparisonReportV2 {
    pub version: u16,
    pub kind: ComparisonKind,
    pub lane: String,
    pub source_matches: bool,
    pub completed: bool,
    pub completed_scenes: usize,
    pub turns: Vec<TurnReportV2>,
    pub human_reviewed: usize,
    pub human_rubric: String,
    pub quality_accepted: bool,
    pub physical_setups: usize,
    pub physical_setup_ms: Option<u64>,
    pub native_load: Option<Value>,
    pub left_charged_ms: u64,
    pub right_charged_ms: u64,
    pub left_reserved_roles: usize,
    pub right_reserved_roles: usize,
    pub first_semantic_divergence: Option<String>,
    pub first_mechanical_divergence: Option<String>,
    pub same_input_pairs: usize,
    pub unavailable: Vec<String>,
    pub profile: PlayProfile,
    pub suite_sha256: String,
    pub source_sha256: String,
    pub reference_sha256: Option<String>,
    pub limitations: Vec<String>,
}

/// Private evidence validated against the actual Host capture and recording envelope.
/// Not Deserialize: stored JSON must pass this same validation again on inspection.
pub(crate) struct CapturedContext {
    pub package: Value,
    pub director_prompts: Vec<String>,
    pub narrator_prompts: Vec<String>,
    pub director_estimates: Option<Vec<Value>>,
}
impl CapturedContext {
    pub fn from_host_capture(
        before: &Engine,
        request: &Request,
        attempt: u32,
        reply: &Value,
        captures: &[Capture],
        profile: &PlayProfile,
        forwarded_budget_version: Option<u16>,
    ) -> Result<Self> {
        if !matches!(forwarded_budget_version, None | Some(1)) {
            return Err("CaptureBudgetVersion".into());
        }
        let artifacts = crate::capture_envelope::artifacts(before, request, attempt, reply)?;
        let mut package = None;
        let mut director_prompts: Vec<String> = Vec::new();
        let mut narrator_prompts: Vec<String> = Vec::new();
        let mut director_estimates: Option<Vec<Value>> =
            forwarded_budget_version.map(|_| Vec::new());
        let mut observed = Vec::new();
        for (ordinal, a) in artifacts.iter().enumerate() {
            crate::capture_envelope::artifact(ordinal, a)?;
            let v = &a["value"];
            match a["kind"].as_str().ok_or("CaptureMalformed")? {
                "selected_context" => {
                    if package.replace(v.clone()).is_some() {
                        return Err("CaptureMalformed".into());
                    }
                }
                "generation_request" => {
                    let checked = crate::capture_envelope::generation(
                        before,
                        request,
                        v,
                        captures,
                        profile,
                        "locallore-director-v2",
                    )?;
                    let role = checked.role;
                    let prompt = checked.prompt;
                    let matching = checked.recording;
                    if role == "director" {
                        let Intent::FreeText { text, .. } = &request.intent else {
                            return Err("CaptureBinding".into());
                        };
                        if matching.compiler_version != Some(2)
                            || matching.player_text_sha256 != Some(digest(text.as_bytes()))
                        {
                            return Err("CaptureVersion".into());
                        }
                        if let Some(estimates) = &mut director_estimates {
                            let pass = match director_prompts.len() {
                                0 => DirectorPassV25::Initial,
                                1 => DirectorPassV25::Repair,
                                _ => return Err("CaptureBudget".into()),
                            };
                            if pass == DirectorPassV25::Repair
                                && !director_repair_matches_v25(&director_prompts[0], prompt)
                            {
                                return Err("CaptureRepairMismatch".into());
                            }
                            let estimate = director_forwarded_budget_v25(
                                profile,
                                pass,
                                prompt,
                                &v["input"]["schema"],
                            )
                            .map_err(|_| "CaptureForwardedBudget")?;
                            estimates.push(serde_json::to_value(estimate).map_err(|_| "Encoding")?);
                        }
                        director_prompts.push(prompt.to_owned());
                    } else {
                        narrator_prompts.push(prompt.to_owned());
                    }
                    observed.push((
                        role.to_owned(),
                        digest(prompt.as_bytes()),
                        digest(&encode(&v["input"]["schema"])?),
                    ));
                }
                "raw_director_output"
                | "raw_narrator_output"
                | "parsed_proposal"
                | "validated_plan_not_durable_commit"
                | "accepted_candidate_not_durable_commit" => {}
                _ => return Err("CaptureMalformed".into()),
            }
        }
        if captures.is_empty()
            || captures.len() > 3
            || observed.len() != captures.len()
            || director_prompts.is_empty()
        {
            return Err("CaptureUnavailable".into());
        }
        for c in captures {
            if !observed
                .iter()
                .any(|(r, p, s)| r == &c.role && p == &c.prompt_sha256 && s == &c.schema_sha256)
            {
                return Err("CaptureRecordingMismatch".into());
            }
        }
        let package = package.ok_or("CaptureUnavailable")?;
        if package["version"] != 2
            || package["scope"] != json!(before.scope())
            || package["head"] != before.revision()
            || package["revision"] != before.revision()
            || package["observer"] != before.seed().player
            || package["role"] != "director"
            || package["historical"] != false
        {
            return Err("CaptureBinding".into());
        }
        let rows = package["records"].as_array().ok_or("CaptureMalformed")?;
        let projected:Vec<_>=rows.iter().map(|r|json!({"kind":r["kind"],"source_revision":r["source_revision"],"payload":r["payload"]})).collect();
        let Intent::FreeText { kind, text } = &request.intent else {
            return Err("CaptureBinding".into());
        };
        for prompt in &director_prompts {
            let suffix = prompt
                .split_once("Context data: ")
                .ok_or("CaptureMalformed")?
                .1;
            let actual: Value =
                Deserialize::deserialize(&mut serde_json::Deserializer::from_str(suffix))
                    .map_err(|_| "CaptureMalformed")?;
            if actual["context"]
                != json!({"compiler_version":2,"observer":before.seed().player,"revision":before.revision(),"records":projected})
                || actual["player_text"] != *text
                || actual["kind"] != json!(kind)
            {
                return Err("CaptureForwardingMismatch".into());
            }
        }
        Ok(Self {
            package,
            director_prompts,
            narrator_prompts,
            director_estimates,
        })
    }
}

#[cfg(test)]
mod forwarded_budget_tests {
    use super::*;

    fn profile() -> PlayProfile {
        PlayProfile {
            id: "synthetic-budget-counts".into(),
            model_sha256: "a".repeat(64),
            runtime_revision: "b".repeat(40),
            template_sha256: "c".repeat(64),
            worker_sha256: "d".repeat(64),
            profile_manifest_sha256: "e".repeat(64),
            context_tokens: 4096,
            director_tokens: 350,
            narrator_tokens: 350,
            deadline_ms: 120_000,
            repair_limit: 1,
        }
    }

    #[test]
    fn actual_utf8_schema_and_exact_repair_bytes_are_charged_once() {
        let profile = profile();
        let initial = format!("Actual Unicode: {} and quoted input: \\\"", "é".repeat(512));
        let schema = json!({"type":"object","properties":{"quoted":{"const":"\\\"\n雪"}}});
        let suffix="\nPrevious output was malformed. Repair exactly once using the schema. Do not change the player's requested intent.";
        assert_eq!(suffix.len(), 114);
        let repair = format!("{initial}{suffix}");
        assert!(director_repair_matches_v25(&initial, &repair));
        assert!(!director_repair_matches_v25(
            &initial,
            &format!("{repair} ")
        ));
        let first =
            director_forwarded_budget_v25(&profile, DirectorPassV25::Initial, &initial, &schema)
                .unwrap();
        let second =
            director_forwarded_budget_v25(&profile, DirectorPassV25::Repair, &repair, &schema)
                .unwrap();
        let first = serde_json::to_value(first).unwrap();
        let second = serde_json::to_value(second).unwrap();
        let schema_bytes = encode(&schema).unwrap().len();
        assert_eq!(first["prompt_bytes"], initial.len());
        assert_eq!(first["schema_bytes"], schema_bytes);
        assert_eq!(first["repair_extra_bytes"], 114);
        assert_eq!(second["repair_extra_bytes"], 0);
        assert_eq!(
            first["actual_prompt_schema_estimated_tokens"],
            (initial.len() + schema_bytes).div_ceil(4)
        );
        assert_eq!(
            first["estimated_total_tokens"],
            (repair.len() + schema_bytes).div_ceil(4) + 350 + 162
        );
        assert_eq!(
            first["estimated_total_tokens"],
            second["estimated_total_tokens"]
        );
        assert_eq!(first["template_reserve_tokens"], 162);
    }

    #[test]
    fn unsupported_profile_or_oversized_actual_input_cannot_get_an_admission_estimate() {
        let mut profile = profile();
        let schema = json!({"type":"object"});
        assert!(director_forwarded_budget_v25(
            &profile,
            DirectorPassV25::Initial,
            &"x".repeat(4096 * 4),
            &schema
        )
        .is_err());
        profile.repair_limit = 0;
        assert!(director_forwarded_budget_v25(
            &profile,
            DirectorPassV25::Repair,
            "initial",
            &schema
        )
        .is_err());
        let allowed =
            director_forwarded_budget_v25(&profile, DirectorPassV25::Initial, "initial", &schema)
                .unwrap();
        assert_eq!(
            serde_json::to_value(allowed).unwrap()["repair_extra_bytes"],
            0
        );
        profile.context_tokens = 4097;
        assert!(director_forwarded_budget_v25(
            &profile,
            DirectorPassV25::Initial,
            "initial",
            &schema
        )
        .is_err());
    }
}
