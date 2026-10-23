// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Derived, immutable inspection files, never a playable archive or writable authority.
use crate::engine::Engine;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};

pub const FORMAT: &str = "locallore-inspection";
pub const EXPORT_VERSION: u16 = 1;
pub const MAX_BUNDLE_BYTES: usize = 32 * 1024 * 1024;
pub const MAX_FILES: usize = 8;

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ExportMode {
    /// Shareable structure only: no story prose, seed, model configuration or filesystem path.
    #[default]
    Diagnostics,
    /// Explicit private export restricted to the player's existing visibility.
    Player,
    /// Explicit spoiler-bearing export; trusted native construction must grant this capability.
    Full,
}

#[derive(Clone, Debug)]
pub struct InspectionBundle {
    pub manifest: Value,
    /// Fixed top-level filenames. Native code writes manifest.json after validating the bundle.
    pub files: BTreeMap<String, Vec<u8>>,
}

pub fn sha256(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

impl InspectionBundle {
    pub fn byte_len(&self) -> usize {
        self.files.values().map(Vec::len).sum::<usize>()
            + serde_json::to_vec(&self.manifest).map_or(MAX_BUNDLE_BYTES + 1, |b| b.len())
    }
    /// Revalidate at the native write boundary. Fields are public for native inspection, not trust.
    pub fn validate(&self) -> Result<(), String> {
        if self.files.is_empty()
            || self.files.len() > MAX_FILES
            || self.byte_len() > MAX_BUNDLE_BYTES
        {
            return Err("TooLarge".into());
        }
        let mode = self.manifest["mode"].as_str().ok_or("Integrity")?;
        let privacy = match mode {
            "diagnostics" => "structural_metadata_only",
            "player" => "private_player_visible_story",
            "full" => "private_full_story_with_spoilers",
            _ => return Err("Integrity".into()),
        };
        if self.manifest["format"] != FORMAT
            || self.manifest["version"] != EXPORT_VERSION
            || self.manifest["privacy"] != privacy
            || self.manifest["raw_prompts"] != "excluded"
            || self.manifest["model_weights"] != "excluded"
            || self.manifest["diagnostic_traces"] != "excluded"
            || self.manifest["portable_playable"] != false
            || self.manifest["schema_version"] != 1
            || self.manifest["revision"].as_u64().is_none()
            || self.manifest["created_at_unix_ms"].as_u64().is_none()
            || !matches!(
                self.manifest["rules"].as_str(),
                Some("fantasy_v1" | "narrative_v1")
            )
        {
            return Err("Integrity".into());
        }
        for key in ["story", "branch"] {
            let id = self.manifest["scope"][key].as_str().ok_or("Integrity")?;
            if id.is_empty()
                || id.len() > 64
                || !id
                    .bytes()
                    .all(|b| b.is_ascii_alphanumeric() || b"-_".contains(&b))
            {
                return Err("Integrity".into());
            }
        }
        let inventory = self.manifest["files"].as_array().ok_or("Integrity")?;
        if inventory.len() != self.files.len()
            || self.files.len() != if mode == "diagnostics" { 1 } else { 7 }
        {
            return Err("Integrity".into());
        }
        let mut seen = BTreeSet::new();
        for row in inventory {
            let name = row["path"].as_str().ok_or("Integrity")?;
            if (mode == "diagnostics") != (name == "diagnostics.json") {
                return Err("Integrity".into());
            }
            if !matches!(
                name,
                "diagnostics.json"
                    | "events.jsonl"
                    | "transcript.jsonl"
                    | "state.json"
                    | "characters.json"
                    | "relationships.json"
                    | "knowledge.json"
                    | "threads.json"
            ) || !seen.insert(name)
            {
                return Err("Integrity".into());
            }
            let bytes = self.files.get(name).ok_or("Integrity")?;
            if std::str::from_utf8(bytes).is_err() {
                return Err("Integrity".into());
            }
            if row["bytes"].as_u64() != Some(bytes.len() as u64)
                || row["sha256"].as_str() != Some(sha256(bytes).as_str())
                || row["scope"] != self.manifest["scope"]
                || row["source_revision"] != self.manifest["revision"]
            {
                return Err("Integrity".into());
            }
        }
        let views = self.manifest["views"].as_array().ok_or("Integrity")?;
        if views.len() != 9 {
            return Err("Integrity".into());
        }
        let mut view_names = BTreeSet::new();
        for row in views {
            let name = row["name"].as_str().ok_or("Integrity")?;
            if !view_names.insert(name) {
                return Err("Integrity".into());
            }
            if matches!(name, "summaries" | "retrieval_indexes") {
                if row["status"] != "unsupported" || !row["source_revision"].is_null() {
                    return Err("Integrity".into());
                }
            } else {
                if !matches!(
                    name,
                    "events"
                        | "transcript"
                        | "state"
                        | "characters"
                        | "relationships"
                        | "knowledge"
                        | "threads"
                ) {
                    return Err("Integrity".into());
                }
                let status = match mode {
                    "diagnostics" => "omitted_privacy",
                    "player" => "observer_filtered",
                    _ => "recorded_or_derived",
                };
                if row["status"] != status || row["source_revision"] != self.manifest["revision"] {
                    return Err("Integrity".into());
                }
            }
        }
        Ok(())
    }
}

fn encode(value: impl Serialize) -> Result<Vec<u8>, String> {
    serde_json::to_vec_pretty(&value).map_err(|_| "Integrity".into())
}
fn json_lines<'a>(rows: impl Iterator<Item = &'a Value>) -> Result<Vec<u8>, String> {
    let mut out = Vec::new();
    for row in rows {
        serde_json::to_writer(&mut out, row).map_err(|_| "Integrity")?;
        out.push(b'\n');
        if out.len() > MAX_BUNDLE_BYTES {
            return Err("TooLarge".into());
        }
    }
    Ok(out)
}

/// The caller captures a validated engine at exactly one revision before calling this pure builder.
pub(crate) fn capture(
    engine: &Engine,
    mode: ExportMode,
    created_at_unix_ms: u64,
) -> Result<InspectionBundle, String> {
    let revision = engine.revision();
    let player = engine.seed().player.as_str();
    let context = engine
        .character_context(player, engine.scope(), revision)
        .map_err(|e| e.to_string())?;
    let mut files: BTreeMap<String, Vec<u8>> = BTreeMap::new();
    let mut views = Vec::new();
    if mode == ExportMode::Diagnostics {
        files.insert(
            "diagnostics.json".into(),
            encode(json!({
                "scope":engine.scope(), "revision":revision,
                "visible_event_count":context.observations.len(),
                "visible_fact_count":context.facts.len(),
                "message_content":"excluded", "raw_prompts":"excluded",
                "model_artifacts":"excluded", "filesystem_paths":"excluded",
                "credentials":"no_story_text_included"
            }))?,
        );
        for name in [
            "events",
            "transcript",
            "state",
            "characters",
            "relationships",
            "knowledge",
            "threads",
        ] {
            views.push(json!({"name":name,"status":"omitted_privacy","source_revision":revision}));
        }
    } else {
        let events: Vec<Value> = if mode == ExportMode::Full {
            engine
                .receipts()
                .iter()
                .flat_map(|r| r.events())
                .map(serde_json::to_value)
                .collect::<Result<_, _>>()
        } else {
            context
                .observations
                .iter()
                .map(serde_json::to_value)
                .collect::<Result<_, _>>()
        }
        .map_err(|_| "Integrity")?;
        let visible: BTreeSet<u64> = events
            .iter()
            .filter_map(|e| e["sequence"].as_u64())
            .collect();
        // Never attach a full request/proposal to a filtered event list. Narration is recorded
        // only when every supporting event is visible under the implemented player-turn contract.
        let transcript: Vec<Value> = engine.receipts().iter()
            .filter(|r| mode == ExportMode::Full || r.events().iter().all(|e|visible.contains(&e.sequence())))
            .map(|r| json!({"scope":engine.scope(),"revision":revision,"turn":r.request().turn,"event_ids":r.events().iter().map(|e|e.sequence()).collect::<Vec<_>>(),"narration":r.narration(),"recorded":true}))
            .collect();
        files.insert("events.jsonl".into(), json_lines(events.iter())?);
        files.insert("transcript.jsonl".into(), json_lines(transcript.iter())?);
        if mode == ExportMode::Full {
            files.insert("state.json".into(), encode(engine.state())?);
            files.insert("characters.json".into(),encode(json!({"actors":engine.state().actors,"seed_source":engine.seed().id,"field_event_sources":engine.state().progression_sources}))?);
            files.insert("relationships.json".into(),encode(json!({"directed":engine.state().relationships,"seed_source":engine.seed().id,"field_event_sources":engine.state().progression_sources}))?);
            files.insert("knowledge.json".into(),encode(json!({"reality":engine.seed().facts,"statements":engine.state().claims,"beliefs":engine.state().beliefs,"discoveries":engine.state().discoveries,"source_revision":revision}))?);
            files.insert("threads.json".into(),encode(json!({"commitments":engine.state().commitments,"story_time":engine.state().story_time,"source_revision":revision}))?);
        } else {
            let inventory: BTreeMap<_, _> = engine
                .state()
                .items
                .iter()
                .filter(|(_, item)| item.owner == player)
                .collect();
            files.insert("state.json".into(),encode(json!({"scope":engine.scope(),"revision":revision,"observer":player,"player":context.self_state,"inventory":inventory,"story_time":engine.state().story_time}))?);
            files.insert("characters.json".into(),encode(json!({"observer":player,"self_state":context.self_state,"seed_source":context.seed_source,"visible_event_sources":visible}))?);
            let relationships: Vec<_> = engine
                .state()
                .relationships
                .iter()
                .filter(|r| r.from == player)
                .collect();
            files.insert("relationships.json".into(),encode(json!({"observer":player,"directed":relationships,"seed_source":context.seed_source,"visibility":"self_outgoing_only"}))?);
            let statements: Vec<_> = engine
                .state()
                .claims
                .iter()
                .filter(|c| c.speaker == player || c.audience.contains(player))
                .collect();
            files.insert("knowledge.json".into(),encode(json!({"observer":player,"facts":context.facts,"statements":statements,"beliefs":context.beliefs,"observations":context.observations,"source_revision":revision}))?);
            let commitments: BTreeMap<_, _> = engine
                .state()
                .commitments
                .iter()
                .filter(|(_, c)| c.from == player || (c.to == player && matches!(c.source, crate::contracts::Evidence::Event(id) if visible.contains(&id))))
                .collect();
            files.insert("threads.json".into(),encode(json!({"observer":player,"commitments":commitments,"story_time":engine.state().story_time,"source_revision":revision}))?);
        }
        for name in [
            "events",
            "transcript",
            "state",
            "characters",
            "relationships",
            "knowledge",
            "threads",
        ] {
            views.push(json!({"name":name,"status":if mode==ExportMode::Full {"recorded_or_derived"} else {"observer_filtered"},"source_revision":revision}));
        }
    }
    views.push(json!({"name":"summaries","status":"unsupported","source_revision":null}));
    views.push(json!({"name":"retrieval_indexes","status":"unsupported","source_revision":null}));
    let inventory:Vec<_> = files.iter().map(|(name,bytes)|json!({"path":name,"scope":engine.scope(),"source_revision":revision,"bytes":bytes.len(),"sha256":sha256(bytes),"media_type":if name.ends_with(".jsonl") {"application/x-ndjson"} else {"application/json"}})).collect();
    let bundle = InspectionBundle {
        manifest: json!({
            "format":FORMAT,"version":EXPORT_VERSION,"mode":mode,"portable_playable":false,
            "scope":engine.scope(),"revision":revision,"created_at_unix_ms":created_at_unix_ms,
            "schema_version":1,"rules":engine.seed().profile,"engine_version":env!("CARGO_PKG_VERSION"),"app_version":env!("CARGO_PKG_VERSION"),
            "privacy":match mode {ExportMode::Diagnostics=>"structural_metadata_only",ExportMode::Player=>"private_player_visible_story",ExportMode::Full=>"private_full_story_with_spoilers"},
            "raw_prompts":"excluded","model_weights":"excluded","diagnostic_traces":"excluded",
            "content_warning":if mode==ExportMode::Diagnostics {"No story text included"} else {"Private story content may include personal information; review before sharing"},
            "views":views,"files":inventory,"limits":{"max_bytes":MAX_BUNDLE_BYTES,"max_files":MAX_FILES}
        }),
        files,
    };
    bundle.validate()?;
    Ok(bundle)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn sha256_is_standard_not_an_unstable_process_hasher() {
        assert_eq!(
            sha256(b"abc"),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        );
    }
}
