// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent FIRST source after d6aceb58. UNREGISTERED/UNCOMPILED/UNRUN.
//! Missing companion APIs or accepted finite test seam are SETUP, never RED.
//! Actual scripted Host journeys are separate from trusted stored-metadata and
//! finite lifecycle controls. No historical/private model text or OS probes.
use super::*;
use crate::local_lane::comparison::desktop_api::{Arm, RowId};
use crate::local_lane::comparison::turn_execution::{
    self as live, NarrationDiagnosticMilestoneV1 as Mark,
    NarrationDiagnosticTestControlV1 as Control, NarrationDiagnosticTestFaultV1 as Fault,
};
use locallore::inspection_query::Observer;
use std::sync::{atomic::{AtomicU64, Ordering}, OnceLock};

const DECLARATION: &str = "narration-diagnostics-v1.json";
const PRIVATE: &str = "SYNTHETIC-COMPANION-PRIVATE-661";
type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;
static NEXT: AtomicU64 = AtomicU64::new(0);

fn root(label: &str) -> PathBuf {
    let dir = std::env::temp_dir().join(format!(
        "scene-diagnostic-first-{label}-{}-{}-{}", std::process::id(),
        std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos(),
        NEXT.fetch_add(1, Ordering::Relaxed),
    ));
    fs::create_dir(&dir).unwrap();
    dir
}
fn inventory(root: &Path) -> Inventory {
    fn visit(root: &Path, dir: &Path, depth: usize, total: &mut usize, out: &mut Inventory) {
        assert!(depth <= 8);
        for item in fs::read_dir(dir).unwrap() {
            let path = item.unwrap().path();
            let meta = fs::symlink_metadata(&path).unwrap();
            assert!(!meta.file_type().is_symlink() && out.len() < 8192);
            let relative = path.strip_prefix(root).unwrap().to_owned();
            if meta.is_dir() {
                out.insert(relative, None);
                visit(root, &path, depth + 1, total, out);
            } else {
                assert!(meta.is_file() && meta.len() <= 8 * 1024 * 1024);
                let bytes = fs::read(path).unwrap();
                *total = total.checked_add(bytes.len()).unwrap();
                assert!(*total <= 128 * 1024 * 1024);
                out.insert(relative, Some(bytes));
            }
        }
    }
    let mut out = Inventory::new();
    visit(root, root, 0, &mut 0, &mut out);
    out
}
fn copy(source: &Path, label: &str) -> PathBuf {
    let files = inventory(source);
    let dir = root(label).join("run");
    fs::create_dir(&dir).unwrap();
    for (relative, bytes) in &files {
        let target = dir.join(relative);
        match bytes {
            None => fs::create_dir_all(target).unwrap(),
            Some(bytes) => {
                fs::create_dir_all(target.parent().unwrap()).unwrap();
                let mut file = OpenOptions::new().write(true).create_new(true).open(target).unwrap();
                file.write_all(bytes).unwrap();
            }
        }
    }
    assert_eq!(inventory(&dir), files);
    dir
}
fn value(path: &Path) -> Value {
    serde_json::from_slice(&fs::read(path).unwrap()).unwrap()
}
fn set(path: &Path, v: &Value) {
    // Only a distinct ordinary synthetic fixture copy; never a frozen capture.
    fs::write(path, serde_json::to_vec(v).unwrap()).unwrap();
}
fn keys(v: &Value) -> Vec<&str> {
    let mut result: Vec<_> = v.as_object().unwrap().keys().map(String::as_str).collect();
    result.sort_unstable();
    result
}
fn exact_keys(v: &Value, wanted: &[&str]) {
    let mut wanted = wanted.to_vec();
    wanted.sort_unstable();
    assert_eq!(keys(v), wanted);
}
fn bounded_refusal<T>(result: Result<T>) {
    let Err(error) = result else { panic!("invalid companion must not become an absence/success") };
    assert!(!error.is_empty() && error.len() <= 64);
    assert!(!error.contains(PRIVATE));
}
fn run(dir: &Path, resume: bool, scenes: usize, factory: LaneFactory, enabled: bool) -> ComparisonReportV4 {
    if enabled {
        run_comparison_with_narration_diagnostics_v1(
            dir, resume, ComparisonKind::ContinuousRollout, &Cancellation::default(),
            scenes, factory, None,
        ).unwrap()
    } else {
        run_comparison(dir, resume, ComparisonKind::ContinuousRollout,
            &Cancellation::default(), scenes, factory, None).unwrap()
    }
}
fn template() -> &'static Path {
    static TEMPLATE: OnceLock<PathBuf> = OnceLock::new();
    TEMPLATE.get_or_init(|| {
        let path = root("actual-host-template").join("run");
        let report = run(&path, false, 1, LaneFactory::ScriptedBaseline, true);
        assert!(!report.completed);
        assert_eq!(report.turns.len(), 12);
        path
    })
}
fn completed_template() -> &'static Path {
    static COMPLETE: OnceLock<PathBuf> = OnceLock::new();
    COMPLETE.get_or_init(|| {
        let path = root("completed-host-template").join("run");
        let report = run(&path, false, 4, LaneFactory::ScriptedBaseline, true);
        assert!(report.completed);
        assert_eq!(report.turns.len(), 48);
        path
    })
}
fn cp(dir: &Path, arm: &str, index: usize) -> Value {
    value(&checkpoint_path(&dir.join(arm), index))
}
fn observation_path(dir: &Path, arm: &str, index: usize) -> PathBuf {
    let checkpoint = cp(dir, arm, index);
    let admission = checkpoint["row"]["admission"].as_u64().unwrap();
    dir.join(arm).join(format!("narration-diagnostic-v1-{admission:02}.json"))
}
fn row(dir: &Path, arm: &str, index: usize) -> RowId {
    RowId { turn: cp(dir, arm, index)["request"]["turn"].as_str().unwrap().into(),
        arm: if arm == "left" { Arm::Left } else { Arm::Right } }
}
fn read(dir: &Path, arm: &str, index: usize) -> Result<Value> {
    let opened = desktop_api::open_read_only(dir)?;
    let summary = desktop_api::summary(&opened, true)?;
    desktop_api::narration_diagnostic_v1(
        &opened, summary["binding"].as_str().unwrap(), &row(dir, arm, index),
        Observer::Omniscient, true,
    )
}
fn response(v: &Value, status: &str, observation: bool) {
    let mut common = vec!["version", "protocol_version", "kind", "binding", "row", "generation_grant", "status"];
    if observation { common.push("observation"); }
    exact_keys(v, &common);
    assert_eq!(v["version"], 1);
    assert_eq!(v["protocol_version"], 4);
    assert_eq!(v["kind"], "narration_diagnostic_v1");
    assert_eq!(v["generation_grant"], false);
    assert_eq!(v["status"], status);
    exact_keys(&v["row"], &["turn", "arm"]);
    assert_eq!(v.get("observation").is_some(), observation);
}
fn cold_refusal_unchanged(dir: &Path) {
    let before = inventory(dir);
    bounded_refusal(read(dir, "left", 0));
    assert_eq!(inventory(dir), before);
}
fn is_companion(relative: &Path) -> bool {
    relative.file_name().and_then(|n| n.to_str()).is_some_and(|n|
        n == DECLARATION || n.starts_with("narration-diagnostic-v1-"))
}
#[cfg(feature = "local-model")]
fn native_cancel_preflight() {
    use crate::local_lane::comparison::selected::SelectedNativeReservation;
    struct NeverReservation;
    impl SelectedNativeReservation for NeverReservation {
        fn assets(&self) -> crate::local_lane::NativeAssets<'_> {
            panic!("cancelled preflight must not inspect assets")
        }
        fn retain_uncertain(&mut self, owner: locallore_local_runtime::adapter::SharedRuntime)
            -> std::result::Result<(), locallore_local_runtime::adapter::SharedRuntime> {
            Err(owner)
        }
    }
    let dir = root("native-cancel-no-assets").join("absent-run");
    let cancel = Cancellation::default();
    cancel.cancel();
    let called = std::cell::Cell::new(0usize);
    let result = run_native_comparison_with_narration_diagnostics_v1::<NeverReservation>(
        &dir, false, ComparisonKind::ContinuousRollout, &cancel, 1,
        || { called.set(called.get() + 1); Err("must-not-reserve".into()) }, None,
    );
    assert!(matches!(result, Err(ref e) if e.code() == "Interrupted"));
    assert_eq!(called.get(), 0);
    assert!(!dir.exists());
}

#[test]
fn actual_both_recipes_one_precommit_binding_survives_cold_reader_without_old_wire_changes() {
    let dir = copy(template(), "actual-both-recipes");
    let before = inventory(&dir);
    let manifest: Manifest = decode(&dir.join("run.json"), 128 * 1024).unwrap();
    let declaration = value(&dir.join(DECLARATION));
    exact_keys(&declaration, &["version", "kind", "source_protocol_version", "run_binding_sha256",
        "run_manifest_sha256", "source_sha256", "harvest", "generation_grant"]);
    assert_eq!(declaration["version"], 1);
    assert_eq!(declaration["kind"], "full_scene_narration_diagnostics_v1");
    assert_eq!(declaration["source_protocol_version"], 4);
    assert_eq!(declaration["run_binding_sha256"], manifest.key().unwrap());
    assert_eq!(declaration["run_manifest_sha256"], digest(&fs::read(dir.join("run.json")).unwrap()));
    assert_eq!(declaration["source_sha256"], manifest.source_sha256);
    assert_eq!(declaration["harvest"], "first_exact_precommit_host_v1");
    assert_eq!(declaration["generation_grant"], false);
    let mut counts = [0usize; 2];
    for (arm_index, arm) in ARM_NAMES.into_iter().enumerate() {
        for index in 0..6 {
            let checkpoint_path = checkpoint_path(&dir.join(arm), index);
            let checkpoint = cp(&dir, arm, index);
            exact_keys(&checkpoint, &["version", "binding", "index", "arm", "request", "before_head",
                "after_head", "row", "capture_file", "recording_file"]);
            let got = read(&dir, arm, index).unwrap();
            let path = checkpoint["row"]["admission"].as_u64().map(|admission|
                dir.join(arm).join(format!("narration-diagnostic-v1-{admission:02}.json")));
            let Some(path) = path.filter(|p| p.exists()) else {
                response(&got, "no_observation", false);
                continue;
            };
            counts[arm_index] += 1;
            let stored = value(&path);
            let status = match stored["host_reply"]["status"].as_str().unwrap() {
                "rejected" => "host_rejected",
                "ok" => match stored["host_reply"]["data"]["status"].as_str().unwrap() {
                    "recorded" => "recorded", "unavailable" => "host_unavailable", other => panic!("{other}"),
                }, other => panic!("{other}"),
            };
            response(&got, status, true);
            if index == 0 {
                assert_eq!(status, "recorded", "both real baseline recipes must retain their actual decision");
                let decision = &stored["host_reply"]["data"]["decision"];
                exact_keys(decision, &["version", "outcome", "error", "reason"]);
                assert_eq!(decision["version"], 1);
            }
            assert_eq!(got["observation"], stored);
            exact_keys(&stored, &["version", "kind", "declaration_sha256", "run_binding_sha256", "source_sha256",
                "arm", "index", "admission", "checkpoint_sha256", "host_query", "host_reply", "generation_grant"]);
            assert_eq!(stored["version"], 1);
            assert_eq!(stored["kind"], "full_scene_narration_observation_v1");
            assert_eq!(stored["arm"], arm);
            assert_eq!(stored["index"], index);
            assert_eq!(stored["admission"], checkpoint["row"]["admission"]);
            assert_eq!(stored["checkpoint_sha256"], digest(&fs::read(checkpoint_path).unwrap()));
            assert_eq!(stored["declaration_sha256"], digest(&fs::read(dir.join(DECLARATION)).unwrap()));
            assert_eq!(stored["source_sha256"], declaration["source_sha256"]);
            assert_eq!(stored["run_binding_sha256"], declaration["run_binding_sha256"]);
            assert_eq!(stored["generation_grant"], false);
            exact_keys(&stored["host_query"], &["version", "command"]);
            let query = &stored["host_query"]["command"];
            exact_keys(query, &["op", "session", "scope", "expected_head", "base_revision", "turn", "attempt"]);
            assert_eq!(query["op"], "trace_narration_validation_read_v1");
            assert_eq!(query["expected_head"], checkpoint["before_head"]);
            assert_eq!(query["base_revision"], checkpoint["request"]["expected_revision"]);
            assert_eq!(query["turn"], checkpoint["request"]["turn"]);
            assert_eq!(query["scope"], checkpoint["request"]["scope"]);
            assert!(query["attempt"].as_u64().unwrap() <= u64::from(u32::MAX));
            let trace = checkpoint["row"]["trace"]["attempts"].as_array().unwrap();
            let exact = trace.iter().find(|a| {
                let id = &a["identity"];
                id["scope"] == query["scope"] && id["base_revision"] == query["base_revision"]
                    && id["turn"] == query["turn"] && id["attempt"] == query["attempt"]
                    && id["observer"] == suite().unwrap().seed().player
            }).expect("exact final trace identity, never a new latest attempt");
            if stored["host_reply"]["status"] == "ok" {
                exact_keys(&stored["host_reply"], &["version", "status", "data"]);
                let data = &stored["host_reply"]["data"];
                let mut wanted = vec!["version", "session", "scope", "head", "base_revision", "turn",
                    "attempt", "observer", "generation_grant", "status"];
                if status == "recorded" { wanted.push("decision"); }
                exact_keys(data, &wanted);
                for field in ["session", "scope", "base_revision", "turn", "attempt"] {
                    assert_eq!(data[field], query[field]);
                }
                assert_eq!(data["head"], query["expected_head"]);
                assert_eq!(data["observer"], "player");
                assert_eq!(data["generation_grant"], false);
                if status == "recorded" {
                    let stage = exact["stages"].as_array().unwrap().iter()
                        .find(|s| s["stage"] == "narration_validation").unwrap();
                    assert_eq!(data["decision"]["outcome"], stage["outcome"]);
                    assert_eq!(data["decision"]["error"], stage["error"]);
                }
            }
            assert!(fs::read(path).unwrap().len() <= 7168);
            assert!(serde_json::to_vec(&stored["host_reply"]).unwrap().len() <= 4096);
            let encoded = stored.to_string();
            for secret in [PRIVATE, "SECRET-TIDE-731", "FOREIGN-COMPARISON", "PARENT-FUTURE-COMPARISON"] {
                assert!(!encoded.contains(secret));
            }
            for forbidden in ["prompt", "narration", "raw", "receipt", "stages", "owner", "path"] {
                assert!(stored.get(forbidden).is_none());
            }
        }
    }
    assert!(counts.iter().all(|n| *n > 0 && *n <= 32));
    let companions: Vec<_> = before.iter().filter(|(p, _)| is_companion(p)).collect();
    assert!(companions.len() <= 65);
    assert!(companions.iter().map(|(_, b)| b.as_ref().unwrap().len()).sum::<usize>() <= 512 * 1024);
    assert_eq!(inventory(&dir), before);
}

#[test]
fn outputs_authorization_precedes_binding_unknown_row_and_corrupt_source_probes() {
    let dir = copy(template(), "authorization");
    let opened = desktop_api::open_read_only(&dir).unwrap();
    let good_binding = desktop_api::summary(&opened, true).unwrap()["binding"].as_str().unwrap().to_owned();
    // Corrupt only this fixture AFTER capability acquisition. Error precedence
    // is runtime-observable; this is not a transport-wide zero-I/O assertion.
    fs::write(dir.join("run.json"), b"{").unwrap();
    fs::write(dir.join(DECLARATION), PRIVATE.as_bytes()).unwrap();
    let before = inventory(&dir);
    for observer in [Observer::Player, Observer::Character { id: "mira".into() }] {
        for granted in [false, true] {
            let unknown = RowId { turn: "unknown-private-row".into(), arm: Arm::Right };
            let result = desktop_api::narration_diagnostic_v1(&opened, "wrong-binding", &unknown, observer.clone(), granted);
            assert!(matches!(result, Err(ref e) if e == "Forbidden"));
        }
    }
    let known = row(&dir, "left", 0);
    assert!(matches!(desktop_api::narration_diagnostic_v1(&opened, &good_binding, &known,
        Observer::Omniscient, false), Err(ref e) if e == "Forbidden"));
    bounded_refusal(desktop_api::narration_diagnostic_v1(&opened, &good_binding, &known,
        Observer::Omniscient, true));
    drop(opened);
    assert_eq!(inventory(&dir), before);
}

#[test]
fn trusted_stored_envelope_controls_preserve_recorded_unavailable_rejected_and_absence_distinctions() {
    // These mutations exercise the codec/reader, NOT actual Engine/Host failure
    // provenance. Hash/query consistency never authenticates their origin.
    for mode in ["recorded", "host_unavailable", "host_rejected", "no_observation"] {
        let dir = copy(template(), mode);
        let path = observation_path(&dir, "left", 0);
        let mut stored = value(&path);
        match mode {
            "recorded" => {
                stored["host_reply"]["data"]["decision"] = json!({"version":1,"outcome":"rejected",
                    "error":"narration","reason":"scene_first_person"});
            }
            "host_unavailable" => {
                stored["host_reply"]["data"]["status"] = json!("unavailable");
                stored["host_reply"]["data"].as_object_mut().unwrap().remove("decision");
            }
            "host_rejected" => stored["host_reply"] = json!({"version":1,"status":"rejected","error":"Closed"}),
            "no_observation" => {}
            _ => unreachable!(),
        }
        if mode == "no_observation" {
            fs::rename(&path, dir.parent().unwrap().join("retained-observation.bytes")).unwrap();
        } else { set(&path, &stored); }
        let before = inventory(&dir);
        let got = read(&dir, "left", 0).unwrap();
        response(&got, mode, mode != "no_observation");
        if mode != "no_observation" { assert_eq!(got["observation"], stored); }
        assert_eq!(inventory(&dir), before);
    }
    let legacy = root("actual-default-no-declaration").join("run");
    run(&legacy, false, 1, LaneFactory::ScriptedBaseline, false);
    assert!(!inventory(&legacy).keys().any(|p| is_companion(p)));
    response(&read(&legacy, "left", 0).unwrap(), "no_declaration", false);
}

#[test]
fn exact_binding_and_closed_metadata_tampering_refuse_without_mutating_legacy_report() {
    let bad: [(&str, Value); 18] = [
        ("/run_binding_sha256", json!("0".repeat(64))), ("/source_sha256", json!("1".repeat(64))),
        ("/declaration_sha256", json!("2".repeat(64))), ("/checkpoint_sha256", json!("3".repeat(64))),
        ("/arm", json!("right")), ("/index", json!(1)), ("/admission", json!(31)),
        ("/host_query/command/attempt", json!(u64::from(u32::MAX) + 1)),
        ("/host_query/command/session", json!("foreign-session")),
        ("/host_query/command/turn", json!("foreign-turn")),
        ("/host_query/command/scope/story", json!("foreign-story")),
        ("/host_query/command/scope/branch", json!("foreign-branch")),
        ("/host_query/command/base_revision", json!(1)),
        ("/host_query/command/expected_head", json!(999)),
        ("/host_reply/data/observer", json!("omniscient")),
        ("/host_reply/data/generation_grant", json!(true)),
        ("/generation_grant", json!(true)), ("/checkpoint_sha256", json!("A".repeat(64))),
    ];
    for (pointer, replacement) in bad {
        let dir = copy(template(), "exact-binding");
        let path = observation_path(&dir, "left", 0);
        let mut stored = value(&path);
        *stored.pointer_mut(pointer).unwrap() = replacement;
        set(&path, &stored);
        let old = serde_json::to_value(inspect_comparison(&dir).unwrap()).unwrap();
        cold_refusal_unchanged(&dir);
        assert_eq!(serde_json::to_value(inspect_comparison(&dir).unwrap()).unwrap(), old);
    }
    // Coordinated query/reply attempt/head changes still lack the exact final
    // checkpoint identity. Coordinated session rewrites are NOT origin proof.
    for name in ["attempt", "expected_head", "base_revision", "turn"] {
        let dir = copy(template(), "coordinated-but-unbound");
        let path = observation_path(&dir, "left", 0);
        let mut stored = value(&path);
        let new = if name == "turn" { json!("foreign-turn") } else { json!(999) };
        stored["host_query"]["command"][name] = new.clone();
        let reply_name = if name == "expected_head" { "head" } else { name };
        stored["host_reply"]["data"][reply_name] = new;
        set(&path, &stored);
        cold_refusal_unchanged(&dir);
    }
    // Explicit trusted snapshot/metadata controls, never a repaired capture:
    // a later unrelated identity is not a new selection; absence of the exact
    // identity cannot be waived by consistent checkpoint/scene hashes.
    for preserve_exact in [true, false] {
        let dir = copy(template(), "final-exact-trace-control");
        let path = observation_path(&dir, "left", 0);
        let mut stored = value(&path);
        let checkpoint_file = checkpoint_path(&dir.join("left"), 0);
        let mut checkpoint = value(&checkpoint_file);
        let attempts = checkpoint["row"]["trace"]["attempts"].as_array_mut().unwrap();
        let mut unrelated = attempts.last().unwrap().clone();
        unrelated["identity"]["turn"] = json!("unrelated-private-turn");
        unrelated["identity"]["attempt"] = json!(u32::MAX);
        if !preserve_exact { attempts.clear(); }
        attempts.push(unrelated);
        set(&checkpoint_file, &checkpoint);
        let manifest: Manifest = decode(&dir.join("run.json"), 128 * 1024).unwrap();
        set(&dir.join("scene-00.json"), &serde_json::to_value(scene_data4(&dir, &manifest.key().unwrap(), 0).unwrap()).unwrap());
        stored["checkpoint_sha256"] = json!(digest(&fs::read(&checkpoint_file).unwrap()));
        set(&path, &stored);
        if preserve_exact {
            response(&read(&dir, "left", 0).unwrap(), "recorded", true);
        } else { cold_refusal_unchanged(&dir); }
    }
}

#[test]
fn versions_unknown_keys_duplicate_keys_finite_codes_and_partial_files_are_never_unavailable_success() {
    // Complete existing Host-v1 finite decision projection, explicitly trusted
    // stored metadata controls; these are not 25 new observed Engine failures.
    let mut supported = vec![
        json!({"version":1,"outcome":"accepted","error":null,"reason":null}),
        json!({"version":1,"outcome":"cancelled","error":"cancelled","reason":null}),
        json!({"version":1,"outcome":"stale","error":"stale","reason":null}),
    ];
    for reason in ["unclassified", "scene_first_person", "scene_unapproved_movement"] {
        supported.push(json!({"version":1,"outcome":"rejected","error":"narration","reason":reason}));
    }
    for error in ["malformed", "version", "scope", "rule", "agency", "deadline", "retry_mismatch",
        "too_large", "author_ui_required", "clarification_required", "unknown_reference", "dead_actor",
        "location", "inventory", "resource", "ability", "knowledge", "provider", "corrupt_history"] {
        supported.push(json!({"version":1,"outcome":"rejected","error":error,"reason":null}));
    }
    assert_eq!(supported.len(), 25);
    for decision in supported {
        let dir = copy(template(), "supported-decision");
        let path = observation_path(&dir, "left", 0);
        let mut stored = value(&path);
        stored["host_reply"]["data"]["decision"] = decision.clone();
        set(&path, &stored);
        let got = read(&dir, "left", 0).unwrap();
        response(&got, "recorded", true);
        assert_eq!(got["observation"]["host_reply"]["data"]["decision"], decision);
    }
    for (pointer, replacement) in [
        ("/version", json!(2)), ("/kind", json!("future_kind")), ("/index", json!(24)),
        ("/admission", json!(32)), ("/host_query/version", json!(2)),
        ("/host_query/command/op", json!("trace_clear")),
        ("/host_reply/version", json!(2)), ("/host_reply/data/version", json!(2)),
        ("/host_reply/data/decision/version", json!(2)),
        ("/host_reply/data/decision/reason", json!("future_reason")),
        ("/host_reply/data/decision/error", json!("future_error")),
        ("/host_reply/data/decision/outcome", json!("committed")),
    ] {
        let dir = copy(template(), "closed-version");
        let path = observation_path(&dir, "left", 0);
        let mut stored = value(&path);
        *stored.pointer_mut(pointer).unwrap() = replacement;
        set(&path, &stored);
        cold_refusal_unchanged(&dir);
    }
    for target in ["", "/host_query", "/host_query/command", "/host_reply", "/host_reply/data", "/host_reply/data/decision"] {
        let dir = copy(template(), "closed-extra");
        let path = observation_path(&dir, "left", 0);
        let mut stored = value(&path);
        let object = stored.pointer_mut(target).unwrap().as_object_mut().unwrap();
        object.insert("untrusted_extra".into(), json!(PRIVATE));
        set(&path, &stored);
        cold_refusal_unchanged(&dir);
    }
    for (target, field) in [("", "host_query"), ("/host_query", "version"),
        ("/host_query/command", "attempt"), ("/host_reply/data", "session"),
        ("/host_reply/data/decision", "reason")] {
        let dir = copy(template(), "closed-required");
        let path = observation_path(&dir, "left", 0);
        let mut stored = value(&path);
        stored.pointer_mut(target).unwrap().as_object_mut().unwrap().remove(field);
        set(&path, &stored);
        cold_refusal_unchanged(&dir);
    }
    for bytes in [b"{".to_vec(), b"null".to_vec(), b"[]".to_vec(),
        b"{\"version\":1,\"version\":1}".to_vec()] {
        let dir = copy(template(), "partial");
        fs::write(observation_path(&dir, "left", 0), bytes).unwrap();
        cold_refusal_unchanged(&dir);
    }
    let dir = copy(template(), "duplicate-real-field");
    let path = observation_path(&dir, "left", 0);
    let original = fs::read_to_string(&path).unwrap();
    let duplicate = format!("{{\"version\":1,{}", original.trim_start().strip_prefix('{').unwrap());
    fs::write(&path, duplicate).unwrap();
    cold_refusal_unchanged(&dir);
    for error in ["Provider", "Storage", "FutureVersion"] {
        let dir = copy(template(), "finite-rejected-code");
        let path = observation_path(&dir, "left", 0);
        let mut stored = value(&path);
        stored["host_reply"] = json!({"version":1,"status":"rejected","error":error});
        set(&path, &stored);
        response(&read(&dir, "left", 0).unwrap(), "host_rejected", true);
    }
    let dir = copy(template(), "private-error-refused");
    let path = observation_path(&dir, "left", 0);
    let mut stored = value(&path);
    stored["host_reply"] = json!({"version":1,"status":"rejected","error":PRIVATE});
    set(&path, &stored);
    cold_refusal_unchanged(&dir);
}

#[test]
fn exact_file_caps_allow_whitespace_then_refuse_one_more_byte_and_overlapping_namespace_overflows() {
    for (is_declaration, limit) in [(true, 4096usize), (false, 7168usize)] {
        let dir = copy(template(), "exact-byte-cap");
        let path = if is_declaration { dir.join(DECLARATION) } else { observation_path(&dir, "left", 0) };
        let mut bytes = fs::read(&path).unwrap();
        assert!(bytes.len() < limit);
        bytes.resize(limit, b' ');
        fs::write(&path, &bytes).unwrap();
        if is_declaration {
            // Whitespace changes declaration bytes; bind every existing record
            // to those exact bytes. Explicit trusted fixture metadata control.
            for arm in ARM_NAMES {
                for entry in fs::read_dir(dir.join(arm)).unwrap() {
                    let path = entry.unwrap().path();
                    if is_companion(&path) {
                        let mut stored = value(&path);
                        stored["declaration_sha256"] = json!(digest(&bytes));
                        set(&path, &stored);
                    }
                }
            }
        }
        response(&read(&dir, "left", 0).unwrap(), "recorded", true);
        bytes.push(b' ');
        fs::write(&path, bytes).unwrap();
        cold_refusal_unchanged(&dir);
    }
    // These exceed a namespace/name/count bound together; they do not isolate
    // aggregate arithmetic. Valid per-file/count caps total only 452KiB.
    for name in ["narration-diagnostic-v1-31.json", "narration-diagnostic-v1-32.json", "narration-diagnostic-v1-0.json",
        "narration-diagnostic-v1-00-copy.json"] {
        let dir = copy(template(), "namespace-alias");
        let original = fs::read(observation_path(&dir, "left", 0)).unwrap();
        fs::write(dir.join("left").join(name), original).unwrap();
        cold_refusal_unchanged(&dir);
    }
    let dir = copy(template(), "count-and-byte-overflow");
    for index in 0..66 { fs::write(dir.join("left").join(format!("narration-diagnostic-v1-extra-{index:02}.json")), vec![b' '; 8192]).unwrap(); }
    cold_refusal_unchanged(&dir);
    let dir = copy(template(), "selected-root-not-adopted");
    fs::write(dir.join("selected.json"), b"{}").unwrap();
    cold_refusal_unchanged(&dir);
}

#[test]
fn declaration_tamper_and_opt_in_legacy_resume_refuse_before_new_evidence_or_backfill() {
    #[cfg(feature = "local-model")]
    native_cancel_preflight(); // Signature/re-export/preflight only; no runtime/assets.
    for (pointer, replacement) in [("/version", json!(2)), ("/source_protocol_version", json!(3)),
        ("/run_manifest_sha256", json!("0".repeat(64))), ("/source_sha256", json!("1".repeat(64))),
        ("/harvest", json!("latest_after_commit")), ("/generation_grant", json!(true))] {
        let dir = copy(template(), "declaration-tamper");
        let path = dir.join(DECLARATION);
        let mut declaration = value(&path);
        *declaration.pointer_mut(pointer).unwrap() = replacement;
        set(&path, &declaration);
        cold_refusal_unchanged(&dir);
    }
    let legacy = root("legacy-no-retrofit").join("run");
    run(&legacy, false, 1, LaneFactory::ScriptedBaseline, false);
    let before = inventory(&legacy);
    bounded_refusal(run_comparison_with_narration_diagnostics_v1(&legacy, true,
        ComparisonKind::ContinuousRollout, &Cancellation::default(), 1,
        LaneFactory::TestFault(crate::local_lane::TestFault::WrongCommand), None));
    assert_eq!(inventory(&legacy), before);
    assert!(!legacy.join(DECLARATION).exists());
    let partial = copy(template(), "partial-declaration-resume");
    fs::write(partial.join(DECLARATION), b"{").unwrap();
    let before = inventory(&partial);
    bounded_refusal(run_comparison_with_narration_diagnostics_v1(&partial, true,
        ComparisonKind::ContinuousRollout, &Cancellation::default(), 1,
        LaneFactory::ScriptedBaseline, None));
    assert_eq!(inventory(&partial), before);
    // A completed valid resume returns unchanged evidence, never reharvests.
    let dir = copy(completed_template(), "completed-no-reread");
    let before = inventory(&dir);
    let report = run(&dir, true, 1, LaneFactory::TestFault(crate::local_lane::TestFault::WrongCommand), true);
    assert!(report.completed);
    assert_eq!(inventory(&dir), before);
    let missing = copy(completed_template(), "completed-missing-no-backfill");
    let path = observation_path(&missing, "left", 0);
    fs::rename(&path, missing.parent().unwrap().join("retained-missing-observation.bytes")).unwrap();
    let before = inventory(&missing);
    assert!(run(&missing, true, 1, LaneFactory::ScriptedBaseline, true).completed);
    response(&read(&missing, "left", 0).unwrap(), "no_observation", false);
    assert_eq!(inventory(&missing), before);
}

// Build a real first-step owned job using existing private Scene4 machinery.
// Declaration bytes here are a trusted test setup, NOT a producer declaration
// timing proof. Both public actual producer recipes are exercised above.
fn lifecycle(fault: Fault) -> (PathBuf, Control, Result<()>, Value) {
    let dir = root("owned-lifecycle").join("run");
    let factory = LaneFactory::ScriptedBaseline;
    let manifest = Manifest::new(ComparisonKind::ContinuousRollout, factory.profile().unwrap(), None).unwrap();
    let key = manifest.key().unwrap();
    let mut session = Session4::open(&dir, false, manifest.clone(), None, Instant::now()).unwrap();
    let declaration = json!({"version":1,"kind":"full_scene_narration_diagnostics_v1","source_protocol_version":4,
        "run_binding_sha256":key,"run_manifest_sha256":digest(&fs::read(dir.join("run.json")).unwrap()),
        "source_sha256":manifest.source_sha256,"harvest":"first_exact_precommit_host_v1","generation_grant":false});
    set(&dir.join(DECLARATION), &declaration);
    session.begin_invocations().unwrap();
    let arm = dir.join("left");
    let path = database(&arm, 0, ComparisonKind::ContinuousRollout);
    let corpus = suite().unwrap();
    let step = &corpus.steps()[0];
    ensure_database(&path, corpus.seed(), &[]).unwrap();
    let before = engine(&path, &corpus.seed().scope).unwrap();
    let control = Control::new(fault);
    let actual = live::execute_with_narration_diagnostics_test_v1(live::LiveTurnJob {
        dir: &arm, path: &path, index: 0, step, factory: &factory,
        cancel: &Cancellation::default(), construction: host_construction(CONSTRUCTIONS[0]),
        before, profile: factory.profile().unwrap(),
    }, &mut session.ledgers[0], control.clone()).unwrap();
    let final_engine = engine(&path, &corpus.seed().scope).unwrap();
    assert_eq!(actual.after.canonical_bytes(), final_engine.canonical_bytes());
    assert_eq!(actual.after.receipts(), final_engine.receipts());
    let row = make_row4(Observation4 {
        dir: &arm, step, arm: "left", construction: CONSTRUCTIONS[0], before: &actual.before,
        after: &actual.after, phase: &actual.phase, error: actual.error.clone(),
        receipt: actual.receipt.as_ref(), recording: Some(&actual.recording),
        capture: actual.capture.as_ref(), trace: actual.trace.clone(), admission: Some(actual.admission),
        elapsed_ms: actual.elapsed_ms, first_final_response_ms: actual.first_final_response_ms,
        commit_elapsed_ms: actual.commit_elapsed_ms, profile: &actual.profile, recovered: false,
    }).unwrap();
    let checkpoint = StoredTurn4 { version:4, binding:key, index:0, arm:"left".into(),
        request:actual.request.clone(), before_head:actual.before.revision(), after_head:actual.after.revision(),
        row, capture_file:actual.capture_file.clone(), recording_file:Some(actual.recording_file.clone()) };
    let result = actual.checkpoint_and_settle(&arm, 0, &checkpoint, &mut session.ledgers[0]);
    let summary = json!({"phase":actual.phase,"receipt":actual.receipt,"roles":actual.recording.roles,
        "canonical_sha256":digest(&actual.after.canonical_bytes())});
    drop(actual); // Observe existing owned Drop cleanup before asserting terminal evidence.
    drop(session);
    assert_eq!(digest(&engine(&path, &corpus.seed().scope).unwrap().canonical_bytes()), summary["canonical_sha256"]);
    (dir, control, result, summary)
}
fn mark_name(mark: &Mark) -> &'static str {
    match mark {
        Mark::FirstTraceSelected => "selected", Mark::NoExactTrace => "no_trace",
        Mark::DiagnosticHostRead => "read", Mark::HarvestDecodeError => "decode_error",
        Mark::RecordedHarvested => "recorded_harvest", Mark::HostUnavailableHarvested => "unavailable_harvest",
        Mark::HostRejectedHarvested => "rejected_harvest",
        Mark::CanonicalOutcome => "canonical", Mark::CheckpointSaved => "checkpoint",
        Mark::LedgerSettled => "settled", Mark::CompanionCreated => "companion",
        Mark::CaptureRevoked => "revoked", Mark::HostClosed => "closed",
        Mark::CompanionErrorReturned => "error",
    }
}
fn marks(control: &Control) -> Vec<&'static str> {
    let actual = control.milestones();
    assert!(actual.len() <= 16);
    assert!(control.host_read_count() <= 1);
    actual.iter().map(mark_name).collect()
}
fn precedes(marks: &[&str], first: &str, next: &str) {
    assert!(marks.iter().position(|m| *m == first).unwrap() < marks.iter().position(|m| *m == next).unwrap());
}

#[test]
fn finite_actual_host_harvest_controls_latch_once_and_keep_unavailable_rejected_and_no_observation_separate() {
    for (fault, expected, reads) in [(Fault::None, "recorded", 1usize),
        (Fault::NoExactTrace, "no_observation", 0),
        (Fault::DisableTraceBeforeRead, "host_unavailable", 1),
        (Fault::CloseHostBeforeRead, "host_rejected", 1)] {
        let (dir, control, result, outcome) = lifecycle(fault);
        if expected == "host_unavailable" { bounded_refusal(result); } else { result.unwrap(); }
        assert_eq!(control.host_read_count(), reads);
        let marks = marks(&control);
        precedes(&marks, "canonical", "checkpoint");
        precedes(&marks, "checkpoint", "settled");
        precedes(&marks, "settled", "closed");
        let observation = dir.join("left/narration-diagnostic-v1-00.json");
        if expected == "no_observation" {
            assert!(!observation.exists());
            assert!(marks.contains(&"no_trace") && !marks.contains(&"read") && !marks.contains(&"companion"));
        } else if expected == "host_unavailable" {
            // Actual HostUnavailable is harvested, but disabling the trace
            // leaves no exact final identity. Refuse publication, never repair.
            assert!(marks.contains(&"unavailable_harvest"));
            assert!(!observation.exists() && !marks.contains(&"companion"));
            precedes(&marks, "selected", "read");
            precedes(&marks, "read", "unavailable_harvest");
            precedes(&marks, "unavailable_harvest", "canonical");
            precedes(&marks, "closed", "error");
            assert_eq!(outcome["phase"], "committed");
            assert!(outcome["receipt"].is_object());
        } else {
            precedes(&marks, "selected", "read");
            precedes(&marks, "read", "canonical");
            precedes(&marks, "settled", "companion");
            precedes(&marks, "companion", "closed");
            let stored = value(&observation);
            if expected == "host_rejected" {
                assert!(marks.contains(&"rejected_harvest"));
                assert_eq!(stored["host_reply"], json!({"version":1,"status":"rejected","error":"Closed"}));
                // Explicit CloseHost interference may cancel. Do not relabel it
                // as passive collection or require a committed receipt.
            } else {
                assert!(marks.contains(&"recorded_harvest"));
                assert_eq!(stored["host_reply"]["data"]["status"], if expected == "recorded" { "recorded" } else { "unavailable" });
                assert_eq!(outcome["phase"], "committed");
                assert!(outcome["receipt"].is_object());
            }
        }
    }
}

#[test]
fn finite_failure_controls_preserve_order_exact_checkpoint_canonical_receipt_and_teardown_without_repair() {
    for (fault, checkpoint, settled, file, decode_error) in [
        (Fault::MalformedHarvestReply, true, true, false, true),
        (Fault::CheckpointFailure, false, false, false, false),
        (Fault::SettlementFailure, true, false, false, false),
        (Fault::ObservationCreateFailure, true, true, false, false),
        (Fault::PartialObservation, true, true, true, false),
        (Fault::ConflictingObservation, true, true, true, false),
        (Fault::StopAfterCheckpoint, true, false, false, false),
        (Fault::StopAfterSettlement, true, true, false, false),
    ] {
        let (dir, control, result, outcome) = lifecycle(fault);
        bounded_refusal(result);
        assert_eq!(control.host_read_count(), 1);
        let marks = marks(&control);
        assert_eq!(marks.contains(&"checkpoint"), checkpoint);
        assert_eq!(marks.contains(&"settled"), settled);
        assert_eq!(marks.contains(&"decode_error"), decode_error);
        assert!(!marks.contains(&"companion"));
        assert!(marks.contains(&"closed"));
        assert_eq!(checkpoint_path(&dir.join("left"), 0).exists(), checkpoint);
        assert_eq!(dir.join("left/admission-00-settled.json").exists(), settled);
        let path = dir.join("left/narration-diagnostic-v1-00.json");
        assert_eq!(path.exists(), file);
        assert_eq!(outcome["phase"], "committed");
        assert!(outcome["receipt"].is_object());
        assert_eq!(outcome["roles"], 2);
        if checkpoint {
            let stored = cp(&dir, "left", 0);
            assert_eq!(stored["row"]["phase"], outcome["phase"]);
            assert_eq!(stored["row"]["actual_receipt_sha256"], digest(&serde_json::to_vec(&outcome["receipt"]).unwrap()));
            precedes(&marks, "canonical", "checkpoint");
        }
        if settled { precedes(&marks, "checkpoint", "settled"); }
        if decode_error {
            precedes(&marks, "read", "decode_error");
            precedes(&marks, "decode_error", "canonical");
            precedes(&marks, "closed", "error");
            precedes(&marks, "revoked", "closed");
        }
        // Synthetic stop/I/O boundaries are not actual process death. All
        // current fixture bytes (including partial/conflict files) survive.
        let frozen = inventory(&dir);
        if file { assert!(!fs::read(&path).unwrap().is_empty()); }
        assert_eq!(inventory(&dir), frozen);
    }
}

#[test]
fn default_old_wires_canonical_provider_recording_and_ready_recovery_never_gain_companion_metadata() {
    let dir = root("default-parity").join("run");
    let ordinary = run(&dir, false, 1, LaneFactory::ScriptedBaseline, false);
    assert_eq!(ordinary.turns.len(), 12);
    assert!(!inventory(&dir).keys().any(|p| is_companion(p)));
    for arm in ARM_NAMES {
        let old_engine = engine(&database(&dir.join(arm), 0, ComparisonKind::ContinuousRollout), &suite().unwrap().seed().scope).unwrap();
        let observed = engine(&database(&template().join(arm), 0, ComparisonKind::ContinuousRollout), &suite().unwrap().seed().scope).unwrap();
        // Compare the same six-step prefix; only separate-run Play stage time
        // is normalized, never error, phase, current bytes or canonical data.
        let old_receipts: Vec<_> = old_engine.receipts().iter().map(|r| {
            let mut value = serde_json::to_value(r).unwrap();
            if let Some(stages) = value.pointer_mut("/play/stages").and_then(Value::as_array_mut) {
                for stage in stages { stage["elapsed_ms"] = json!(0); }
            }
            value
        }).collect();
        let mut new_receipts: Vec<_> = observed.receipts().iter().take(old_engine.receipts().len()).map(|r| serde_json::to_value(r).unwrap()).collect();
        for value in &mut new_receipts {
            if let Some(stages) = value.pointer_mut("/play/stages").and_then(Value::as_array_mut) {
                for stage in stages { stage["elapsed_ms"] = json!(0); }
            }
        }
        assert_eq!(old_receipts, new_receipts);
        let after_prefix = observed.at_revision(old_engine.revision()).unwrap();
        assert_eq!(old_engine.canonical_bytes(), after_prefix.canonical_bytes());
        for index in 0..6 {
            let old = cp(&dir, arm, index);
            let new = cp(template(), arm, index);
            assert_eq!(old["row"]["phase"], new["row"]["phase"]);
            assert_eq!(old["row"]["error"], new["row"]["error"]);
            assert_eq!(old["row"]["roles"], new["row"]["roles"]);
            if let Some(file) = old["recording_file"].as_str() {
                let old_recording = value(&dir.join(arm).join(file));
                let new_recording = value(&template().join(arm).join(new["recording_file"].as_str().unwrap()));
                exact_keys(&old_recording, &["version", "captures", "raw", "role_metrics", "roles", "lost",
                    "forbidden_director_prompt", "forbidden_narrator_prompt", "forbidden_narrator_output"]);
                assert_eq!(keys(&old_recording), keys(&new_recording));
                assert_eq!(old_recording["roles"], new_recording["roles"]);
                assert_eq!(old_recording["raw"], new_recording["raw"]);
            }
        }
        let recovered = ready_turn4(ReadyJob4 { path:&database(&dir.join(arm), 0, ComparisonKind::ContinuousRollout),
            full:&old_engine, index:0, arm, construction:CONSTRUCTIONS[usize::from(arm == "right")],
            binding:&Manifest::new(ComparisonKind::ContinuousRollout, LaneFactory::ScriptedBaseline.profile().unwrap(), None).unwrap().key().unwrap(),
            step:&suite().unwrap().steps()[0], profile:&LaneFactory::ScriptedBaseline.profile().unwrap() }).unwrap().unwrap();
        assert!(recovered.row.recovered_without_checkpoint);
        assert!(recovered.row.trace.is_none() && recovered.row.admission.is_none());
        assert!(recovered.capture_file.is_none() && recovered.recording_file.is_none());
    }
    assert!(!inventory(&dir).keys().any(|p| is_companion(p)));
}
