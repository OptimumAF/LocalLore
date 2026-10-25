// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! SOURCE ONLY / UNCOMPILED / UNRUN. Private negative diagnostic, not a baseline
//! executor, conformance score, new report protocol or Core/Host authority.
//! Actual captures come from existing Host/Store/Scripted pipelines. Explicitly
//! mutated diagnostic copies below are never attributed to actual Host input.
use super::*;
use locallore::play::{director_forwarded_budget_v25, director_repair_matches_v25, DirectorPassV25};
use serde::Deserialize;
use std::{collections::BTreeSet, sync::OnceLock};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum Origin { ActualHost, MutatedDiagnosticCopy }
#[derive(Clone)]
struct ActualCapture {
    origin: Origin,
    before: Engine,
    request: Request,
    reply: Value,
    recording: RecordingFile,
    profile: PlayProfile,
    play: locallore::play::PlayRecord,
    policy: ContextPolicy,
    attempt: u32,
    directory: PathBuf,
}
struct Validated<'a> {
    source: &'a ActualCapture,
    checked: CapturedContext,
}
#[derive(Debug, PartialEq, Eq)]
enum Negative {
    CurrentNonLiteral(BTreeSet<&'static str>),
    Unavailable(&'static str),
}
impl Negative {
    // Test-local closed data only; never stored in a production report.
    fn diagnostic(&self) -> Value {
        match self {
            Self::CurrentNonLiteral(channels) => json!({"status":"current_non_literal","channels":channels}),
            Self::Unavailable(reason) => json!({"status":"unavailable","reason":reason}),
        }
    }
}
fn exact(value: &Value, keys: &[&str]) -> bool {
    value.as_object().is_some_and(|o| o.len() == keys.len() && keys.iter().all(|k| o.contains_key(*k)))
}
impl ActualCapture {
    fn gate(&self) -> std::result::Result<Validated<'_>, Negative> {
        if self.play.prompt_version != PROMPT_VERSION || self.play.profile != self.profile
            || self.play.context_policy != Some(self.policy) || self.profile.validate().is_err() {
            return Err(Negative::Unavailable("version_or_profile"));
        }
        let checked = CapturedContext::from_host_capture(&self.before, &self.request, self.attempt,
            &self.reply, &self.recording.captures, &self.profile, Some(1))
            .map_err(|_| Negative::Unavailable("capture_validation"))?;
        Ok(Validated { source: self, checked })
    }
    fn copied(&self) -> Self {
        let mut copy = self.clone(); copy.origin = Origin::MutatedDiagnosticCopy; copy
    }
    fn director(&self, ordinal: usize) -> &Value {
        self.reply["data"]["details"]["artifacts"].as_array().unwrap().iter()
            .filter(|a| a["kind"] == "generation_request" && a["value"]["input"]["role"] == "director")
            .nth(ordinal).map(|a| &a["value"]).unwrap()
    }
    fn director_mut(&mut self, ordinal: usize) -> &mut Value {
        self.reply["data"]["details"]["artifacts"].as_array_mut().unwrap().iter_mut()
            .filter(|a| a["kind"] == "generation_request" && a["value"]["input"]["role"] == "director")
            .nth(ordinal).map(|a| &mut a["value"]).unwrap()
    }
}

// This observer borrows the schema from the captured GenerationRequest. It
// neither builds a schema from a context package nor interprets player intent.
fn observe(validated: &Validated<'_>, value: &Value, pass: DirectorPassV25) -> Negative {
    let s = validated.source;
    if !exact(value, &["version","scope","turn","revision","model_profile","schema_id","budget","input"])
        || value["version"] != 1 || value["scope"] != json!(s.request.scope)
        || value["turn"] != s.request.turn || value["revision"] != s.before.revision()
        || value["model_profile"] != s.profile.id || value["schema_id"] != "locallore-director-v2"
        || !exact(&value["input"], &["kind","role","prompt","schema"])
        || value["input"]["kind"] != "structured" || value["input"]["role"] != "director"
        || !exact(&value["budget"], &["max_output_bytes","max_output_tokens","max_pending_polls","deadline_ms"])
        || value["budget"]["max_output_bytes"] != 16384 || value["budget"]["max_output_tokens"] != 350
        || value["budget"]["max_pending_polls"] != 30000
        || value["budget"]["deadline_ms"].as_u64().is_none_or(|n| n == 0 || n > s.profile.deadline_ms) {
        return Negative::Unavailable("request_shape_or_identity");
    }
    let Some(prompt) = value["input"]["prompt"].as_str() else { return Negative::Unavailable("prompt_shape"); };
    if pass == DirectorPassV25::Repair && !director_repair_matches_v25(&validated.checked.director_prompts[0], prompt) {
        return Negative::Unavailable("repair_relation");
    }
    if director_forwarded_budget_v25(&s.profile, pass, prompt, &value["input"]["schema"]).is_err() {
        return Negative::Unavailable("forwarded_budget");
    }
    let Some((_, suffix)) = prompt.split_once("Context data: ") else { return Negative::Unavailable("prompt_shape"); };
    let frame: Value = match Deserialize::deserialize(&mut serde_json::Deserializer::from_str(suffix)) {
        Ok(value) => value, Err(_) => return Negative::Unavailable("prompt_shape"),
    };
    let Intent::FreeText { kind, text } = &s.request.intent else { return Negative::Unavailable("request_kind"); };
    if !exact(&frame, &["kind","player_text","context","inventory","nearby","routes"])
        || frame["kind"] != json!(kind) || frame["player_text"] != *text
        || !exact(&frame["context"], &["compiler_version","observer","revision","records"])
        || frame["context"]["compiler_version"] != 2 || frame["context"]["observer"] != s.before.seed().player
        || frame["context"]["revision"] != s.before.revision()
        || !frame["context"]["records"].is_array() || !frame["inventory"].is_object()
        || !frame["nearby"].is_object() || !frame["routes"].is_array() {
        return Negative::Unavailable("frame_shape");
    }
    let mut channels = BTreeSet::new();
    use locallore::context_compiler::Kind;
    let state_kinds = [Kind::CurrentState,Kind::Truth,Kind::Statement,Kind::Belief,Kind::Discovery,
        Kind::Observation,Kind::Relationship,Kind::Commitment,Kind::KnownAsObserved,Kind::Transcript];
    for record in frame["context"]["records"].as_array().unwrap() {
        if !exact(record, &["kind","source_revision","payload"]) || !record["kind"].is_string()
            || !record["source_revision"].is_u64() || !record["payload"].is_object() {
            return Negative::Unavailable("record_shape");
        }
        // Anchor to the actual typed compiler Kind enum. Static rules and alias
        // records alone are not labelled current-state/memory evidence.
        if state_kinds.iter().any(|kind| record["kind"] == json!(kind)) {
            channels.insert("structured_context_records");
        } else if record["kind"] != json!(Kind::Rules) && record["kind"] != json!(Kind::Alias) {
            return Negative::Unavailable("record_kind");
        }
    }
    // Presence of these known current frame channels counts even when empty.
    channels.insert("inventory_frame"); channels.insert("nearby_frame");
    channels.insert("routes_frame");
    if !known_schema(&value["input"]["schema"])
        || !schema_channels(&value["input"]["schema"], None, 0, &mut 0, &mut channels) {
        return Negative::Unavailable("schema_shape");
    }
    resolved_action(&value["input"]["schema"], &mut channels);
    if channels.is_empty() { Negative::Unavailable("no_negative_observation") }
    else { Negative::CurrentNonLiteral(channels) }
}

// Recognize the bounded current schema grammar, ignoring command discriminant
// op constants. This is a negative side-channel observer, NOT schema validation
// of a model proposal and never a proof that any unsupported shape is clean.
fn schema_channels(v: &Value, field: Option<&str>, depth: usize, nodes: &mut usize, channels: &mut BTreeSet<&'static str>) -> bool {
    *nodes += 1;
    if depth > 16 || *nodes > 4096 { return false; }
    let Some(o) = v.as_object() else { return false; };
    for (key, child) in o {
        match key.as_str() {
            "const" => {}, // op or exact player text alone is not memory.
            "enum" if child.is_array() => {
                if matches!(field, Some("item" | "to" | "audience")) { channels.insert("state_dependent_schema"); }
            },
            "properties" => {
                let Some(fields) = child.as_object() else { return false; };
                for (field, schema) in fields {
                    if !schema_channels(schema, Some(field), depth + 1, nodes, channels) { return false; }
                }
            },
            "items" => { if !schema_channels(child, field, depth + 1, nodes, channels) { return false; } },
            "oneOf" => {
                let Some(items) = child.as_array().filter(|v| !v.is_empty()) else { return false; };
                for item in items { if !schema_channels(item, field, depth + 1, nodes, channels) { return false; } }
            },
            "type" if child.is_string() => {},
            "required" if child.as_array().is_some_and(|a| a.iter().all(Value::is_string)) => {},
            "additionalProperties" if child.is_boolean() => {},
            "minimum" | "maximum" | "minItems" | "maxItems" | "maxLength" if child.is_u64() => {},
            _ => return false,
        }
    }
    true
}
fn resolved_action(schema: &Value, channels: &mut BTreeSet<&'static str>) {
    let commands = &schema["properties"]["commands"];
    if commands["maxItems"] != 1 { return; }
    let Some(variants) = commands["items"]["oneOf"].as_array().filter(|v| v.len() == 1) else { return; };
    let Some(fields) = variants[0]["properties"].as_object().filter(|v| v.len() >= 2) else { return; };
    if fields.get("op").is_some_and(|v| v["const"].is_string() && v["const"] != "say")
        && fields.values().all(|v| exact(v, &["const"])) {
        channels.insert("resolved_action_schema");
    }
}
fn known_schema(schema: &Value) -> bool {
    if !exact(schema, &["type","properties","required","additionalProperties"])
        || schema["type"] != "object" || schema["additionalProperties"] != false
        || schema["required"] != json!(["commands"]) || !exact(&schema["properties"], &["commands"]) { return false; }
    let commands = &schema["properties"]["commands"];
    if !exact(commands, &["type","minItems","maxItems","items"]) || commands["type"] != "array"
        || commands["minItems"] != 1 || commands["maxItems"] != 1 || !exact(&commands["items"], &["oneOf"]) { return false; }
    let Some(variants) = commands["items"]["oneOf"].as_array().filter(|v| !v.is_empty() && v.len() <= 9) else { return false; };
    for variant in variants {
        if !exact(variant, &["type","properties","required","additionalProperties"])
            || variant["type"] != "object" || variant["additionalProperties"] != false { return false; }
        let Some(properties) = variant["properties"].as_object() else { return false; };
        let allowed: &[&str] = match variant["properties"]["op"]["const"].as_str() {
            Some("give") => &["op","item","to","quantity"], Some("consume") => &["op","item"],
            Some("learn" | "use_ability") => &["op","ability"], Some("move") => &["op","to"],
            Some("say") => &["op","text","audience"], Some("wait") => &["op","ticks"],
            Some("discover") => &["op","fact"], Some("believe") => &["op","claim_event"], _ => return false,
        };
        if properties.len() != allowed.len() || !allowed.iter().all(|k| properties.contains_key(*k)) { return false; }
        let Some(required) = variant["required"].as_array() else { return false; };
        let required: BTreeSet<_> = required.iter().filter_map(Value::as_str).collect();
        if required.len() != allowed.len() || !allowed.iter().all(|k| required.contains(k)) { return false; }
    }
    true
}
fn schema_only_after_gate(_validated: &Validated<'_>, copied_schema: &Value) -> Negative {
    // Explicit isolated diagnostic-copy observation, NOT an actual GenerationRequest.
    let mut channels = BTreeSet::new();
    if !known_schema(copied_schema) || !schema_channels(copied_schema, None, 0, &mut 0, &mut channels) { return Negative::Unavailable("schema_shape"); }
    resolved_action(copied_schema, &mut channels);
    if channels.is_empty() { Negative::Unavailable("no_negative_observation") }
    else { Negative::CurrentNonLiteral(channels) }
}

fn fixtures() -> &'static [ActualCapture] {
    static FIXTURES: OnceLock<Vec<ActualCapture>> = OnceLock::new();
    FIXTURES.get_or_init(|| {
        let mut out = Vec::new();
        for (p, policy) in POLICIES.into_iter().enumerate() {
            for repaired in [false, true] {
                let dir = std::env::temp_dir().join(format!("literal-control-{}-{}-{p}-{repaired}", std::process::id(),
                    std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos()));
                fs::create_dir(&dir).unwrap();
                let corpus = suite().unwrap();
                let factory = if repaired { LaneFactory::TestFault(TestFault::MalformedRepair) } else { LaneFactory::ScriptedBaseline };
                let profile = factory.profile().unwrap();
                let binding = RunManifest::new(ComparisonKind::ContinuousRollout, profile.clone(), false, None).unwrap().stable_key().unwrap();
                let path = dir.join("synthetic.sqlite"); ensure_database(&path, corpus.seed(), &[]).unwrap();
                let mut ledger = Ledger::load(&dir, &binding).unwrap(); ledger.begin_invocation().unwrap();
                // Normal index0 Dialogue then index1 Action have genuinely
                // different actual prefixes; no Expected-to-receipt shortcut.
                for index in 0..if repaired { 1 } else { 2 } {
                    let before = engine(&path, &corpus.seed().scope).unwrap();
                    let step = &corpus.steps()[index]; let request = step.request(&before);
                    let turn = execute_turn(TurnJob { dir:&dir, path:&path, index, arm:"left", policy,
                        binding:&binding, step, factory:&factory, cancel:&Cancellation::default() }, &mut ledger).unwrap();
                    assert_eq!(turn.row.phase, "committed"); assert!(turn.row.passed);
                    let reply: Value = decode(&dir.join(turn.capture_file.unwrap()), v2::MAX_PRIVATE_CAPTURE + 4096).unwrap();
                    let recording: RecordingFile = decode(&dir.join(turn.recording_file.unwrap()), 64 * 1024).unwrap();
                    let attempt = u32::try_from(reply["data"]["details"]["identity"]["attempt"].as_u64().unwrap()).unwrap();
                    let stored = Store::open_read_only(&path).unwrap().lookup_turn(before.scope(), step.id()).unwrap();
                    let play = stored.receipt.as_ref().unwrap().play().unwrap().clone();
                    let actual = ActualCapture { origin:Origin::ActualHost, before, request, reply, recording,
                        profile:profile.clone(), play, policy, attempt, directory:dir.clone() };
                    assert!(actual.gate().is_ok(), "actual Host capture must pass the existing evidence gate"); out.push(actual);
                }
                ledger.finish().unwrap();
            }
        }
        out
    })
}

fn negative_has(verdict: &Negative, channel: &str) -> bool {
    matches!(verdict, Negative::CurrentNonLiteral(codes) if codes.contains(channel))
}
fn inventory(dir: &Path) -> std::collections::BTreeMap<PathBuf, Option<Vec<u8>>> {
    fn walk(root:&Path, dir:&Path, depth:usize, bytes:&mut usize, out:&mut std::collections::BTreeMap<PathBuf,Option<Vec<u8>>>) {
        assert!(depth <= 4);
        for entry in fs::read_dir(dir).unwrap() {
            assert!(out.len() < 256); let path = entry.unwrap().path();
            let metadata = fs::symlink_metadata(&path).unwrap(); assert!(!metadata.file_type().is_symlink());
            let key = path.strip_prefix(root).unwrap().to_owned();
            if metadata.is_dir() { out.insert(key,None); walk(root,&path,depth+1,bytes,out); }
            else {
                assert!(metadata.is_file() && metadata.len() <= 8*1024*1024);
                let value = fs::read(path).unwrap(); *bytes += value.len(); assert!(*bytes <= 64*1024*1024);
                out.insert(key,Some(value));
            }
        }
    }
    let mut out = std::collections::BTreeMap::new(); walk(dir,dir,0,&mut 0,&mut out); out
}
fn frame(value: &Value) -> Value {
    let text = value["input"]["prompt"].as_str().unwrap().split_once("Context data: ").unwrap().1;
    Deserialize::deserialize(&mut serde_json::Deserializer::from_str(text)).unwrap()
}
fn replace_frame(copied: &mut Value, replacement: &Value) {
    let prompt = copied["input"]["prompt"].as_str().unwrap();
    let (prefix, suffix) = prompt.split_once("Context data: ").unwrap();
    let mut stream = serde_json::Deserializer::from_str(suffix).into_iter::<Value>(); stream.next().unwrap().unwrap();
    copied["input"]["prompt"] = json!(format!("{prefix}Context data: {replacement}{}", &suffix[stream.byte_offset()..]));
}

#[test]
fn actual_host_action_and_dialogue_both_policies_are_negative_not_literal_controls() {
    let mut matrix = BTreeSet::new();
    for actual in fixtures() {
        assert_eq!(actual.origin, Origin::ActualHost);
        let before = encode(&actual.reply).unwrap(); let basis = actual.before.accepted_history_basis().unwrap();
        let files = inventory(&actual.directory);
        let validated = actual.gate().unwrap();
        let mandatory: Vec<_> = validated.checked.package["records"].as_array().unwrap().iter().filter(|r| r["mandatory"] == true).collect();
        assert!(!mandatory.is_empty());
        let forwarded = frame(actual.director(0));
        for record in mandatory {
            let projected = json!({"kind":record["kind"],"source_revision":record["source_revision"],"payload":record["payload"]});
            assert!(forwarded["context"]["records"].as_array().unwrap().contains(&projected));
        }
        let verdict = observe(&validated, actual.director(0), DirectorPassV25::Initial);
        for code in ["structured_context_records","inventory_frame","nearby_frame","routes_frame"] { assert!(negative_has(&verdict, code)); }
        if matches!(actual.request.intent, Intent::FreeText { kind: PlayInputKind::Dialogue, .. }) {
            assert!(negative_has(&verdict, "state_dependent_schema"));
            assert!(!negative_has(&verdict, "resolved_action_schema"));
        } else {
            assert!(negative_has(&verdict, "resolved_action_schema"));
        }
        assert_eq!(verdict.diagnostic()["status"], "current_non_literal");
        assert!(encode(&verdict.diagnostic()).unwrap().len() <= 4096);
        assert_eq!(encode(&actual.reply).unwrap(), before); assert_eq!(actual.before.accepted_history_basis().unwrap(), basis);
        assert_eq!(inventory(&actual.directory), files);
        matrix.insert((format!("{:?}",actual.policy), format!("{:?}",actual.request.intent), actual.play.repairs));
    }
    assert_eq!(fixtures().len(), 6); assert_eq!(matrix.len(), 6);
}

#[test]
fn actual_malformed_first_director_repair_keeps_profile_schema_and_exact_suffix() {
    assert_eq!(fixtures().iter().filter(|f| f.play.repairs == 1).count(), 2);
    for actual in fixtures().iter().filter(|f| f.play.repairs == 1) {
        let validated = actual.gate().unwrap(); assert_eq!(validated.checked.director_prompts.len(), 2);
        assert_eq!(actual.recording.captures.iter().filter(|c| c.role == "director").count(), 2);
        assert_eq!(actual.director(0)["input"]["schema"], actual.director(1)["input"]["schema"]);
        assert!(director_repair_matches_v25(&validated.checked.director_prompts[0], &validated.checked.director_prompts[1]));
        for (index, pass) in [(0,DirectorPassV25::Initial),(1,DirectorPassV25::Repair)] {
            let estimate = director_forwarded_budget_v25(&actual.profile, pass,
                actual.director(index)["input"]["prompt"].as_str().unwrap(), &actual.director(index)["input"]["schema"]).unwrap();
            assert!(estimate.estimated_total_tokens() <= 4096);
            assert!(matches!(observe(&validated, actual.director(index), pass), Negative::CurrentNonLiteral(_)));
        }
    }
}

#[test]
fn mutated_capture_copies_with_wrong_identity_profile_version_or_budget_are_unavailable() {
    let actual = &fixtures()[0];
    for fault in 0..9 {
        let mut copy = actual.copied();
        match fault {
            0 => copy.director_mut(0)["input"]["role"] = json!("unknown"),
            1 => copy.play.prompt_version = "unknown".into(),
            2 => copy.profile.id = "not-the-actual-profile".into(),
            3 => copy.director_mut(0)["budget"]["max_output_tokens"] = json!(351),
            4 => copy.reply["data"]["details"]["status"] = json!("truncated"),
            5 => copy.director_mut(0)["scope"]["story"] = json!("foreign"),
            6 => { copy.recording.captures[0].schema_sha256 = "0".repeat(64); },
            7 => copy.recording.captures.clear(),
            _ => copy.director_mut(0)["input"]["schema"] = Value::Null,
        }
        assert_eq!(copy.origin, Origin::MutatedDiagnosticCopy);
        assert!(matches!(copy.gate(), Err(Negative::Unavailable(_))));
    }
    assert!(actual.gate().is_ok());
}

#[test]
fn mutated_diagnostic_copies_isolate_frame_and_non_op_schema_channels_without_host_attribution() {
    let actual = &fixtures()[0]; let validated = actual.gate().unwrap();
    // Gate ORIGINAL first. These altered request Values were NOT forwarded by
    // Host and have no matching captured hashes. Never emit them as Host proof.
    let mut copied = actual.director(0).clone();
    let schema_only = schema_only_after_gate(&validated, &copied["input"]["schema"]);
    assert!(negative_has(&schema_only, "state_dependent_schema"));
    assert!(!negative_has(&schema_only, "resolved_action_schema"));
    for code in ["structured_context_records","inventory_frame","nearby_frame","routes_frame"] { assert!(!negative_has(&schema_only, code)); }
    // Strip only const/enum for non-op fields in this explicitly mutated copy.
    fn strip(v: &mut Value, non_op: bool) {
        if let Some(o) = v.as_object_mut() {
            if non_op { o.remove("const"); o.remove("enum"); }
            if let Some(fields) = o.get_mut("properties").and_then(Value::as_object_mut) {
                for (field, schema) in fields { strip(schema, field != "op"); }
            }
            if let Some(items) = o.get_mut("items") { strip(items, non_op); }
            if let Some(variants) = o.get_mut("oneOf").and_then(Value::as_array_mut) { for v in variants { strip(v, non_op); } }
        }
    }
    strip(&mut copied["input"]["schema"], false);
    assert_eq!(schema_only_after_gate(&validated, &copied["input"]["schema"]), Negative::Unavailable("no_negative_observation"));
    // Static op and exact player-text constants alone yield unavailable, NEVER
    // conforming. The actual unaltered frame still carries current state.
    let frame_only = observe(&validated, &copied, DirectorPassV25::Initial);
    assert!(negative_has(&frame_only, "structured_context_records"));
    assert!(!negative_has(&frame_only, "resolved_action_schema")); assert!(!negative_has(&frame_only, "state_dependent_schema"));
    // Static rules/aliases alone are not classified as structured state; empty
    // frame values still retain the disallowed current-frame channel presence.
    let mut static_only = frame(&copied);
    static_only["context"]["records"].as_array_mut().unwrap().retain(|r|
        r["kind"] == json!(locallore::context_compiler::Kind::Rules)
        || r["kind"] == json!(locallore::context_compiler::Kind::Alias));
    static_only["inventory"] = json!({}); static_only["nearby"] = json!({}); static_only["routes"] = json!([]);
    replace_frame(&mut copied,&static_only);
    let static_frame = observe(&validated,&copied,DirectorPassV25::Initial);
    assert!(!negative_has(&static_frame,"structured_context_records"));
    for code in ["inventory_frame","nearby_frame","routes_frame"] { assert!(negative_has(&static_frame,code)); }
}

#[test]
fn mutated_diagnostic_unknown_shapes_and_oversize_prompts_never_score_clean() {
    let actual = &fixtures()[0]; let validated = actual.gate().unwrap();
    for fault in 0..6 {
        let mut copied = actual.director(0).clone();
        match fault {
            0 => copied["input"]["unknown"] = json!(true),
            1 => copied["input"]["schema"]["unknownKeyword"] = json!(true),
            2 => copied["input"]["prompt"] = json!("missing actual frame"),
            3 => { let mut f = frame(&copied); f["unknown"] = json!(true); replace_frame(&mut copied,&f); },
            4 => copied["input"]["prompt"] = json!(format!("{}{}", copied["input"]["prompt"].as_str().unwrap(), "x".repeat(32001))),
            _ => copied["input"]["schema"] = json!({}),
        }
        let result = observe(&validated, &copied, DirectorPassV25::Initial);
        assert!(matches!(result, Negative::Unavailable(_)));
        assert_eq!(result.diagnostic()["status"], "unavailable");
    }
    let repaired = fixtures().iter().find(|f| f.play.repairs == 1).unwrap();
    let validated = repaired.gate().unwrap(); let mut copied = repaired.director(1).clone();
    copied["input"]["prompt"] = json!(format!("{} ",copied["input"]["prompt"].as_str().unwrap()));
    assert_eq!(observe(&validated,&copied,DirectorPassV25::Repair),Negative::Unavailable("repair_relation"));
}
