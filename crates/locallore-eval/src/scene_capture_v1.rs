//! Committed Domain1 scene narrator-input consistency. This is neither output
//! authentication nor proof of provider or memory-compiler execution. In
//! particular Director prompts and schemas receive envelope checks, not source
//! regeneration.
use crate::{capture_envelope, digest, Capture};
use locallore::{
    contracts::{Intent, Request},
    engine::Engine,
    play::{
        scene_narration::{self, SceneRecipeV1},
        PlayProfile,
    },
};
use serde::Serialize;
use serde_json::{json, Value};
use std::io::Write;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum SceneCaptureErrorV1 {
    Unsupported,
    Unavailable,
    Malformed,
    Budget,
    SourceBinding,
    ReceiptBinding,
    RecipeBinding,
    CaptureBinding,
    RecordingMismatch,
    NarratorForwardingMismatch,
}
use SceneCaptureErrorV1 as E;
type Result<T> = std::result::Result<T, E>;

pub struct SceneCaptureInputV1<'a> {
    pub before: &'a Engine,
    pub after: &'a Engine,
    pub request: &'a Request,
    pub expected_recipe: SceneRecipeV1,
    pub expected_profile: &'a PlayProfile,
    pub attempt: u32,
    pub details_reply: &'a Value,
    pub recordings: &'a [Capture],
}

/// Bounded diagnostic result; no constructor, deserialization or execution grant.
pub struct CheckedSceneCaptureV1 {
    narrator_prompt: String,
    narrator_schema: String,
    receipt: String,
    director_calls: u8,
    fallback: bool,
}
impl CheckedSceneCaptureV1 {
    pub fn version(&self) -> u16 {
        1
    }
    pub fn narrator_prompt_sha256(&self) -> &str {
        &self.narrator_prompt
    }
    pub fn narrator_schema_sha256(&self) -> &str {
        &self.narrator_schema
    }
    pub fn receipt_sha256(&self) -> &str {
        &self.receipt
    }
    pub fn director_calls(&self) -> u8 {
        self.director_calls
    }
    pub fn fallback(&self) -> bool {
        self.fallback
    }
}

// Refuse oversized diagnostics before source reconstruction, without allocating
// a second unbounded copy of an already parsed Value.
struct Counter {
    bytes: usize,
    limit: usize,
}
impl Write for Counter {
    fn write(&mut self, bytes: &[u8]) -> std::io::Result<usize> {
        let total = self
            .bytes
            .checked_add(bytes.len())
            .ok_or_else(|| std::io::Error::other("Budget"))?;
        if total > self.limit {
            return Err(std::io::Error::other("Budget"));
        }
        self.bytes = total;
        Ok(bytes.len())
    }
    fn flush(&mut self) -> std::io::Result<()> {
        Ok(())
    }
}
fn budget(value: &Value, limit: usize) -> Result<()> {
    serde_json::to_writer(Counter { bytes: 0, limit }, value).map_err(|_| E::Budget)
}
fn value<T: Serialize + ?Sized>(source: &T) -> Result<Value> {
    serde_json::to_value(source).map_err(|_| E::Malformed)
}
fn hash<T: Serialize + ?Sized>(source: &T) -> Result<String> {
    serde_json::to_vec(source)
        .map(|bytes| digest(&bytes))
        .map_err(|_| E::Malformed)
}

/// The caller supplies actual native snapshots and collector/recorder replies.
/// V1 deliberately requires one fresh immediate commit, not replay or a later head.
pub fn check_committed_scene_capture_v1(
    input: SceneCaptureInputV1<'_>,
) -> Result<CheckedSceneCaptureV1> {
    let SceneCaptureInputV1 {
        before,
        after,
        request,
        expected_recipe,
        expected_profile,
        attempt,
        details_reply,
        recordings,
    } = input;
    budget(details_reply, capture_envelope::MAX_PRIVATE_CAPTURE + 4096)?;
    if before.domain_version() != 1 || after.domain_version() != 1 {
        return Err(E::Unsupported);
    }
    expected_profile.validate().map_err(|_| E::RecipeBinding)?;
    if request.scope != *before.scope()
        || request.expected_revision != before.revision()
        || !matches!(request.intent, Intent::FreeText { .. })
        || before
            .recorded(request)
            .map_err(|_| E::SourceBinding)?
            .is_some()
        || !after
            .extends_accepted_history(before)
            .map_err(|_| E::SourceBinding)?
    {
        return Err(E::SourceBinding);
    }
    let before_count = before.canonical_record_count();
    let after_count = after.canonical_record_count();
    if after_count == before_count {
        return Err(E::Unavailable);
    }
    if after_count != before_count.checked_add(1).ok_or(E::SourceBinding)? {
        return Err(E::SourceBinding);
    }
    let receipt = after
        .recorded(request)
        .map_err(|_| E::ReceiptBinding)?
        .ok_or(E::Unavailable)?;
    if after.canonical_records().last().and_then(|r| r.receipt()) != Some(&receipt)
        || receipt.events().last().map(|e| e.sequence()) != Some(after.revision())
    {
        return Err(E::ReceiptBinding);
    }
    let record = receipt.play().ok_or(E::RecipeBinding)?;
    let prompt_version = match expected_recipe {
        SceneRecipeV1::Memory(policy) => {
            if record.context_policy != Some(policy) {
                return Err(E::RecipeBinding);
            }
            scene_narration::SCENE_PROMPT_VERSION_V1
        }
        SceneRecipeV1::LiteralV1 => {
            if record.context.is_some() || record.context_policy.is_some() {
                return Err(E::RecipeBinding);
            }
            scene_narration::LITERAL_SCENE_PROMPT_VERSION_V1
        }
    };
    if record.prompt_version != prompt_version
        || record.policy != scene_narration::SCENE_NARRATION_POLICY_V1
        || record.profile != *expected_profile
        || record.scene.is_none()
    {
        return Err(E::RecipeBinding);
    }
    let prep = before
        .stage_scene_play_v1(request, receipt.proposal(), &|| false)
        .map_err(|_| E::RecipeBinding)?;
    let bound = before
        .bind_scene_play_v1(prep, expected_recipe, &|| false)
        .map_err(|_| E::RecipeBinding)?;
    let approved = value(bound.approved())?;
    let proposal = value(receipt.proposal())?;
    let candidate = value(&receipt)?;
    let rendered = scene_narration::render_scene_narrator_v1(&bound, expected_profile, &|| false)
        .map_err(|_| E::RecipeBinding)?;
    let mut reconstructed = before.clone();
    let installed = reconstructed
        .commit_scene_play_v1(bound, record, &|| false)
        .map_err(|_| E::RecipeBinding)?;
    if installed != receipt
        || reconstructed
            .accepted_history_basis()
            .map_err(|_| E::SourceBinding)?
            != after
                .accepted_history_basis()
                .map_err(|_| E::SourceBinding)?
    {
        return Err(E::SourceBinding);
    }

    let artifacts = capture_envelope::artifacts(before, request, attempt, details_reply).map_err(
        |e| match e.as_str() {
            "CaptureUnavailable" => E::Unavailable,
            "CaptureBudget" => E::Budget,
            "CaptureMalformed" => E::Malformed,
            _ => E::CaptureBinding,
        },
    )?;
    let mut generations = Vec::new();
    let (mut captured_proposal, mut captured_approved, mut captured_candidate, mut context) =
        (None, None, None, None);
    let mut kinds = Vec::new();
    for (ordinal, artifact) in artifacts.iter().enumerate() {
        capture_envelope::artifact(ordinal, artifact).map_err(|_| E::Malformed)?;
        let kind = artifact["kind"].as_str().ok_or(E::Malformed)?;
        let data = artifact.get("value").ok_or(E::Malformed)?;
        match kind {
            "generation_request" => generations.push(data),
            "parsed_proposal" => singleton(&mut captured_proposal, data)?,
            "validated_plan_not_durable_commit" => singleton(&mut captured_approved, data)?,
            "accepted_candidate_not_durable_commit" => singleton(&mut captured_candidate, data)?,
            "selected_context" => singleton(&mut context, data)?,
            "raw_director_output" | "raw_narrator_output" => {}
            _ => return Err(E::Malformed),
        }
        kinds.push(kind);
    }
    if generations.is_empty()
        || captured_proposal.is_none()
        || captured_approved.is_none()
        || captured_candidate.is_none()
        || (matches!(expected_recipe, SceneRecipeV1::Memory(_)) && context.is_none())
    {
        return Err(E::Unavailable);
    }
    if captured_proposal != Some(&proposal)
        || captured_approved != Some(&approved)
        || captured_candidate != Some(&candidate)
    {
        return Err(E::ReceiptBinding);
    }
    let director_calls = record.repairs.checked_add(1).ok_or(E::RecipeBinding)?;
    let expected_calls = usize::from(director_calls) + 1;
    if generations.len() != expected_calls || recordings.len() != expected_calls {
        return Err(E::RecordingMismatch);
    }
    // Role order is checked before envelope fields, so a renamed Narrator is not
    // silently accepted as another Director with an unrelated schema identifier.
    for (index, generation) in generations.iter().enumerate() {
        let role = if index < usize::from(director_calls) {
            "director"
        } else {
            "narrator"
        };
        if generation["input"]["role"] != role {
            return Err(E::RecordingMismatch);
        }
    }
    let mut expected_kinds = Vec::new();
    if matches!(expected_recipe, SceneRecipeV1::Memory(_)) {
        expected_kinds.push("selected_context");
    }
    for _ in 0..director_calls {
        expected_kinds.extend(["generation_request", "raw_director_output"]);
    }
    expected_kinds.extend([
        "parsed_proposal",
        "validated_plan_not_durable_commit",
        "generation_request",
        "raw_narrator_output",
        "accepted_candidate_not_durable_commit",
    ]);
    if kinds != expected_kinds {
        return Err(E::Malformed);
    }

    let mut narrator_prompt = String::new();
    let mut narrator_schema = String::new();
    for (index, generation) in generations.iter().enumerate() {
        let role = if index < usize::from(director_calls) {
            "director"
        } else {
            "narrator"
        };
        let prompt = generation["input"]["prompt"].as_str().ok_or(E::Malformed)?;
        check_generation(generation, role, request, expected_profile, expected_recipe)?;
        let schema = &generation["input"]["schema"];
        let prompt_hash = digest(prompt.as_bytes());
        let schema_hash = hash(schema)?;
        let recording = &recordings[index];
        if recording.turn != request.turn
            || recording.role != role
            || recording.prompt_sha256 != prompt_hash
            || recording.schema_sha256 != schema_hash
        {
            return Err(E::RecordingMismatch);
        }
        if role == "narrator" {
            if prompt != rendered.prompt() || schema != rendered.schema() {
                return Err(E::NarratorForwardingMismatch);
            }
            narrator_prompt = prompt_hash;
            narrator_schema = schema_hash;
        }
    }
    // Do not rewrite DetailSnapshot.exact_reconstruction=false. This narrow
    // result establishes neither raw-output authenticity nor provider execution.
    Ok(CheckedSceneCaptureV1 {
        narrator_prompt,
        narrator_schema,
        receipt: hash(&receipt)?,
        director_calls,
        fallback: record.fallback,
    })
}

fn singleton<'a>(slot: &mut Option<&'a Value>, value: &'a Value) -> Result<()> {
    if slot.replace(value).is_some() {
        Err(E::Malformed)
    } else {
        Ok(())
    }
}
fn check_generation(
    value: &Value,
    role: &str,
    request: &Request,
    profile: &PlayProfile,
    recipe: SceneRecipeV1,
) -> Result<()> {
    let schema_id = if role == "narrator" {
        "locallore-narrator-v2"
    } else if matches!(recipe, SceneRecipeV1::LiteralV1) {
        "locallore-director-literal-v1"
    } else {
        "locallore-director-v2"
    };
    let tokens = if role == "director" {
        profile.director_tokens
    } else {
        profile.narrator_tokens
    };
    if value["version"] != 1
        || value["scope"] != json!(request.scope)
        || value["turn"] != request.turn
        || value["revision"] != request.expected_revision
        || value["model_profile"] != profile.id
        || value["schema_id"] != schema_id
        || value["input"]["kind"] != "structured"
        || value["input"]["prompt"]
            .as_str()
            .is_none_or(|p| p.len() > 32000)
        || value["budget"]["max_output_bytes"] != 16384
        || value["budget"]["max_output_tokens"] != u64::from(tokens)
        || value["budget"]["max_pending_polls"] != 30_000
        || value["budget"]["deadline_ms"]
            .as_u64()
            .is_none_or(|n| n == 0 || n > profile.deadline_ms)
    {
        return Err(E::CaptureBinding);
    }
    Ok(())
}
