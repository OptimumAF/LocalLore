//! Shared diagnostic envelope checks. These do not authenticate model outputs
//! or grant canonical, execution, observer or filesystem authority.
use crate::{digest, encode, Capture, Result};
use locallore::{contracts::Request, engine::Engine, play::PlayProfile};
use serde_json::{json, Value};

pub const MAX_PRIVATE_CAPTURE: usize = 196_608;

pub(crate) fn artifacts<'a>(
    before: &Engine,
    request: &Request,
    attempt: u32,
    reply: &'a Value,
) -> Result<&'a [Value]> {
    if before.domain_version() != 1
        || request.scope != *before.scope()
        || request.expected_revision != before.revision()
        || encode(reply)?.len() > MAX_PRIVATE_CAPTURE + 4096
        || reply["status"] != "ok"
    {
        return Err("CaptureBinding".into());
    }
    let d = &reply["data"]["details"];
    if d["version"] != 1 || d["status"] != "recorded" {
        return Err("CaptureUnavailable".into());
    }
    if d["identity"]
        != json!({"scope":request.scope,"base_revision":request.expected_revision,"observer":before.seed().player,"turn":request.turn,"attempt":attempt})
    {
        return Err("CaptureBinding".into());
    }
    let artifacts = d["artifacts"].as_array().ok_or("CaptureMalformed")?;
    if artifacts.len() > 16 || encode(artifacts)?.len() > MAX_PRIVATE_CAPTURE {
        return Err("CaptureBudget".into());
    }
    Ok(artifacts)
}

pub(crate) fn artifact(ordinal: usize, artifact: &Value) -> Result<()> {
    if artifact["ordinal"] != ordinal || encode(artifact)?.len() > 49_152 + 128 {
        return Err("CaptureMalformed".into());
    }
    Ok(())
}

pub(crate) struct Generation<'a> {
    pub role: &'a str,
    pub prompt: &'a str,
    pub recording: &'a Capture,
}

pub(crate) fn generation<'a>(
    before: &Engine,
    request: &Request,
    value: &'a Value,
    captures: &'a [Capture],
    profile: &PlayProfile,
    director_schema_id: &str,
) -> Result<Generation<'a>> {
    let role = value["input"]["role"].as_str().ok_or("CaptureMalformed")?;
    let prompt = value["input"]["prompt"]
        .as_str()
        .ok_or("CaptureMalformed")?;
    let schema_id = if role == "director" {
        director_schema_id
    } else {
        "locallore-narrator-v2"
    };
    if prompt.len() > 32000
        || value["version"] != 1
        || value["scope"] != json!(request.scope)
        || value["turn"] != request.turn
        || value["revision"] != before.revision()
        || value["model_profile"] != profile.id
        || value["schema_id"] != schema_id
        || value["input"]["kind"] != "structured"
        || value["budget"]["max_output_bytes"] != 16384
        || value["budget"]["max_output_tokens"] != 350
        || value["budget"]["max_pending_polls"] != 30_000
        || value["budget"]["deadline_ms"]
            .as_u64()
            .is_none_or(|n| n == 0 || n > profile.deadline_ms)
        || !matches!(role, "director" | "narrator")
    {
        return Err("CaptureBinding".into());
    }
    let prompt_hash = digest(prompt.as_bytes());
    let schema_hash = digest(&encode(&value["input"]["schema"])?);
    let recording = captures
        .iter()
        .find(|c| {
            c.turn == request.turn
                && c.role == role
                && c.prompt_sha256 == prompt_hash
                && c.schema_sha256 == schema_hash
        })
        .ok_or("CaptureRecordingMismatch")?;
    Ok(Generation {
        role,
        prompt,
        recording,
    })
}
