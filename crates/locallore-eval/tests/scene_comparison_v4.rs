// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! FIRST SOURCE FREEZE: UNCOMPILED/UNRUN, before the Protocol4 API exists.
//! Public real scripted producer/Host/Store/collector/gate only, no fake report,
//! copied compiler/runtime or model execution. Every mutable fixture is private.
use locallore::{
    engine::Engine,
    inference::Cancellation,
    play::{scene_narration::SceneRecipeV1, PlayProfile},
};
use locallore_eval::{
    digest,
    local_lane::{comparison::{self, scene_v4, ComparisonKind}, LaneFactory},
    memory_comparison::frozen_suite,
    memory_comparison_v4::{self as wire, ArmDescriptorV4, ComparisonReportV4},
    scene_capture_v1::{check_committed_scene_capture_v1, SceneCaptureInputV1},
    Capture,
};
use locallore_storage::Store;
use serde_json::{json, Value};
use std::{
    collections::BTreeMap,
    fs::{self, OpenOptions},
    io::Write,
    path::{Path, PathBuf},
    sync::{atomic::{AtomicU64, Ordering}, OnceLock},
};

type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;
static NEXT: AtomicU64 = AtomicU64::new(0);

fn root(label: &str) -> PathBuf {
    let path = std::env::temp_dir().join(format!(
        "scene-comparison-v4-{label}-{}-{}-{}",
        std::process::id(),
        std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos(),
        NEXT.fetch_add(1, Ordering::Relaxed),
    ));
    fs::create_dir(&path).unwrap();
    path
}
fn inventory(root: &Path) -> Inventory {
    fn visit(root: &Path, dir: &Path, depth: usize, total: &mut usize, out: &mut Inventory) {
        assert!(depth <= 8);
        for entry in fs::read_dir(dir).unwrap() {
            let path = entry.unwrap().path();
            let meta = fs::symlink_metadata(&path).unwrap();
            assert!(!meta.file_type().is_symlink());
            assert!(out.len() < 4096);
            let key = path.strip_prefix(root).unwrap().to_owned();
            if meta.is_dir() {
                out.insert(key, None);
                visit(root, &path, depth + 1, total, out);
            } else {
                assert!(meta.is_file() && meta.len() <= 8 * 1024 * 1024);
                let bytes = fs::read(&path).unwrap();
                *total += bytes.len();
                assert!(*total <= 64 * 1024 * 1024);
                out.insert(key, Some(bytes));
            }
        }
    }
    let mut out = Inventory::new();
    visit(root, root, 0, &mut 0, &mut out);
    out
}
fn copied(source: &Path, label: &str) -> PathBuf {
    let files = inventory(source);
    let target = root(label).join("run");
    fs::create_dir(&target).unwrap();
    for (relative, bytes) in &files {
        let path = target.join(relative);
        match bytes {
            None => fs::create_dir_all(path).unwrap(),
            Some(bytes) => {
                if let Some(parent) = path.parent() { fs::create_dir_all(parent).unwrap(); }
                let mut file = OpenOptions::new().write(true).create_new(true).open(path).unwrap();
                file.write_all(bytes).unwrap();
            }
        }
    }
    assert_eq!(inventory(&target), files);
    target
}
fn read(path: &Path) -> Value {
    serde_json::from_slice(&fs::read(path).unwrap()).unwrap()
}
fn save(path: &Path, value: &Value) {
    // Mutations are confined to a newly copied synthetic fixture.
    fs::write(path, serde_json::to_vec(value).unwrap()).unwrap();
}
fn run(
    dir: &Path, resume: bool, kind: ComparisonKind, scenes: usize,
    reference: Option<&comparison::ValidatedReference>,
) -> Value {
    serde_json::to_value(scene_v4::run_comparison(
        dir, resume, kind, &Cancellation::default(), scenes,
        LaneFactory::ScriptedBaseline, reference,
    ).unwrap()).unwrap()
}
fn refuse<T>(result: Result<T, String>) {
    assert!(result.is_err(), "mutated evidence must not become valid source evidence");
}
fn inspect_refusal_unchanged(dir: &Path) {
    let before = inventory(dir);
    refuse(scene_v4::inspect_comparison(dir));
    assert_eq!(inventory(dir), before);
}

// A closed producer template is read only after initialization. Each test copies
// its own directory before opening Reader/Store/producer locks or mutating bytes.
// No tests share a live mutable producer or retained exclusive reader lock.
struct Templates {
    paired: PathBuf,
    rollout: PathBuf,
    partial: PathBuf,
    first: Value,
    second: Value,
    completed: Value,
    first_bytes: Inventory,
}
fn templates() -> &'static Templates {
    static T: OnceLock<Templates> = OnceLock::new();
    T.get_or_init(|| {
        let base = root("producer-template");
        let reference_dir = base.join("reference");
        let reference_report = comparison::prepare_reference(&reference_dir, &Cancellation::default()).unwrap();
        assert_eq!((reference_report.accepted, reference_report.guard_only, reference_report.roles), (21, 3, 42));
        let reference = comparison::open_reference(&reference_dir).unwrap();
        let reference_before = inventory(&reference_dir);
        let paired = base.join("paired");
        let paired_report = run(&paired, false, ComparisonKind::PairedSnapshots, 4, Some(&reference));
        assert_eq!(paired_report["completed"], true);
        assert_eq!(inventory(&reference_dir), reference_before);
        drop(reference);
        let rollout = base.join("rollout");
        let first = run(&rollout, false, ComparisonKind::ContinuousRollout, 1, None);
        let first_bytes = inventory(&rollout);
        let partial = copied(&rollout, "partial-template");
        let second = run(&rollout, true, ComparisonKind::ContinuousRollout, 1, None);
        let completed = run(&rollout, true, ComparisonKind::ContinuousRollout, 4, None);
        Templates { paired, rollout, partial, first, second, completed, first_bytes }
    })
}
fn row<'a>(report: &'a Value, turn: &str, arm: &str) -> &'a Value {
    report["turns"].as_array().unwrap().iter()
        .find(|r| r["turn"] == turn && r["arm"] == arm).unwrap()
}
fn actual_engine(path: &Path) -> Engine {
    Store::open_read_only(path).unwrap()
        .resume(&frozen_suite().unwrap().seed().scope).unwrap().engine
}
fn database(dir: &Path, arm: &str, index: usize, paired: bool) -> PathBuf {
    dir.join(arm).join(if paired { format!("pair-{index:02}.sqlite") } else { "synthetic.sqlite".into() })
}
fn checkpoint(dir: &Path, arm: &str, index: usize) -> PathBuf {
    dir.join(arm).join(format!("attempt-{index:02}.json"))
}
fn full_checks(dir: &Path, paired: bool) {
    let before_files = inventory(dir);
    let report = serde_json::to_value(scene_v4::inspect_comparison(dir).unwrap()).unwrap();
    assert_eq!(report["version"], 4);
    assert_eq!(report["completed"], true);
    assert_eq!(report["completed_scenes"], 4);
    assert_eq!(report["turns"].as_array().unwrap().len(), 48);
    assert_eq!(report["arms"], serde_json::to_value(wire::arm_descriptors()).unwrap());
    assert_eq!(report["source_matches"], true);
    assert_eq!(report["suite_sha256"], frozen_suite().unwrap().sha256().unwrap());
    assert_eq!(report["human_reviewed"], 0);
    assert_eq!(report["human_rubric"], "not_reviewed");
    assert_eq!(report["quality_accepted"], false);
    assert_eq!(report["source_bound_committed_rows"], 42);
    assert_eq!(report["physical_setups"], 0);
    assert!(report["physical_setup_ms"].is_null());
    assert!(report["native_load"].is_null());
    // LaneFactory::profile is private. Read public metadata and independently
    // check fixed caps; native receipt/gate checks below bind its exact identity.
    let profile: PlayProfile = serde_json::from_value(report["profile"].clone()).unwrap();
    profile.validate().unwrap();
    assert_eq!((profile.context_tokens, profile.director_tokens, profile.narrator_tokens,
        profile.deadline_ms, profile.repair_limit), (4096, 350, 350, 120_000, 1));
    let corpus = frozen_suite().unwrap();
    for arm in ["left", "right"] {
        let mut accepted = 0;
        let mut guards = 0;
        let mut total_roles = 0;
        for (index, step) in corpus.steps().iter().enumerate() {
            let r = row(&report, step.id(), arm);
            assert_eq!(r["passed"], true, "{}:{arm}", step.id());
            assert_eq!(r["roles_known"], true);
            assert_eq!(r["recovered_without_checkpoint"], false);
            assert_eq!(r["construction"], report["arms"][usize::from(arm == "right")]);
            assert_eq!(r["expected"], serde_json::to_string(step.expected()).unwrap());
            let roles = r["roles"].as_u64().unwrap();
            total_roles += roles;
            let saved = read(&checkpoint(dir, arm, index));
            assert_eq!(saved["version"], 4);
            assert_eq!(&saved["row"], r);
            let full = actual_engine(&database(dir, arm, index, paired));
            if r["phase"] == "committed" {
                accepted += 1;
                assert_eq!(roles, 2);
                assert_eq!(r["construction_matches"], true);
                assert_eq!(r["construction_evidence_status"], "validated_committed_scene_narrator_v1");
                assert!(r["construction_evidence_reason"].is_null());
                assert_eq!(r["privacy_evidence_status"], "checked_finite_sentinels");
                let actual = full.receipts().iter().find(|receipt| receipt.request().turn == step.id()).unwrap();
                let before = full.at_revision(actual.request().expected_revision).unwrap();
                let after = full.at_revision(actual.events().last().unwrap().sequence()).unwrap();
                assert_eq!(actual.request(), &step.request(&before));
                assert_eq!(saved["request"], serde_json::to_value(actual.request()).unwrap());
                assert_eq!(after.canonical_record_count(), before.canonical_record_count() + 1);
                assert!(after.extends_accepted_history(&before).unwrap());
                let capture = read(&dir.join(arm).join(saved["capture_file"].as_str().unwrap()));
                let recording = read(&dir.join(arm).join(saved["recording_file"].as_str().unwrap()));
                let recordings: Vec<Capture> = serde_json::from_value(recording["captures"].clone()).unwrap();
                let checked = check_committed_scene_capture_v1(SceneCaptureInputV1 {
                    before: &before, after: &after, request: actual.request(),
                    expected_recipe: if arm == "left" { SceneRecipeV1::LiteralV1 } else {
                        SceneRecipeV1::Memory(locallore::play::PlayContextPolicy::StateRelevantMemoryV1)
                    },
                    expected_profile: &profile,
                    attempt: u32::try_from(capture["data"]["details"]["identity"]["attempt"].as_u64().unwrap()).unwrap(),
                    details_reply: &capture, recordings: &recordings,
                }).ok().expect("actual Store receipt and actual collector must pass the separate gate");
                assert_eq!(r["narrator_prompt_sha256"], checked.narrator_prompt_sha256());
                assert_eq!(r["narrator_schema_sha256"], checked.narrator_schema_sha256());
                assert_eq!(r["actual_receipt_sha256"], checked.receipt_sha256());
                assert_eq!(checked.director_calls(), 1);
                let play = actual.play().unwrap();
                assert_eq!(r["scene_frame_sha256"], play.scene.as_ref().unwrap().frame_sha256);
                assert_eq!(r["narration"], actual.narration());
                assert_eq!(r["fallback"], checked.fallback());
                assert_eq!(r["repairs"], play.repairs);
                assert_eq!(capture["data"]["details"]["exact_reconstruction"], false);
                assert_eq!(r["actual_receipt_sha256"], digest(&serde_json::to_vec(actual).unwrap()));
            } else {
                guards += 1;
                assert!(matches!(step.id(), "courier-09" | "courier-10" | "courier-24"));
                assert_eq!(roles, 0);
                assert_eq!(r["construction_evidence_status"], "not_applicable_guard");
                assert_eq!(r["privacy_evidence_status"], "not_applicable_guard");
                assert_eq!(saved["before_head"], saved["after_head"]);
                for key in ["narrator_prompt_sha256", "narrator_schema_sha256", "scene_frame_sha256", "actual_receipt_sha256", "fallback", "repairs", "narration"] {
                    assert!(r[key].is_null(), "guard has no generated/committed {key}");
                }
            }
        }
        assert_eq!((accepted, guards, total_roles), (21, 3, 42));
    }
    if paired {
        assert_eq!(report["same_input_pairs"], 24);
        for step in corpus.steps() {
            let left = row(&report, step.id(), "left");
            let right = row(&report, step.id(), "right");
            assert_eq!(left["input_semantic_sha256"], right["input_semantic_sha256"]);
            if left["phase"] == "committed" {
                // Same actual reference source/proposal/frame/presentation uses
                // the same narrator, despite distinct native recipe records.
                assert_eq!(left["narrator_prompt_sha256"], right["narrator_prompt_sha256"]);
                assert_eq!(left["narrator_schema_sha256"], right["narrator_schema_sha256"]);
            }
        }
    }
    assert_eq!(inventory(dir), before_files, "strict inspection/gate/Store reads must not rewrite files");
}

fn expected_descriptor(literal: bool) -> Value {
    json!({
        "arm":if literal { "literal_scene_v1" } else { "relevant_memory_scene_v1" },
        "prompt_version":if literal { "locallore-play-v2.10-literal-director-v1-scene-frame-v1" } else { "locallore-play-v2.9-scene-frame-v1" },
        "narration_policy":"grounded-prose-v2.4-scene-frame-v1",
        "director_schema_id":if literal { "locallore-director-literal-v1" } else { "locallore-director-v2" },
        "narrator_schema_id":"locallore-narrator-v2",
        "context_policy":if literal { Value::Null } else { json!("state_relevant_memory_v1") },
        "compiler_version":if literal { Value::Null } else { json!(2) },
        "context_version":if literal { Value::Null } else { json!(2) },
        "literal_source_version":if literal { json!(1) } else { Value::Null },
        "literal_render_version":if literal { json!(1) } else { Value::Null },
        "literal_schema_version":if literal { json!(1) } else { Value::Null },
        "literal_packing_version":if literal { json!(1) } else { Value::Null },
        "forwarded_budget_version":1,"scene_frame_version":1,"scene_capture_gate_version":1
    })
}

#[test]
fn closed_descriptor_exact_tuple_required_nullable_and_unknown_fields() {
    let descriptors = wire::arm_descriptors();
    for (index, literal) in [true, false].into_iter().enumerate() {
        let expected = expected_descriptor(literal);
        assert_eq!(serde_json::to_value(&descriptors[index]).unwrap(), expected);
        descriptors[index].validate().unwrap();
        let roundtrip: ArmDescriptorV4 = serde_json::from_value(expected.clone()).unwrap();
        roundtrip.validate().unwrap();
        for key in expected.as_object().unwrap().keys() {
            let mut omitted = expected.clone();
            omitted.as_object_mut().unwrap().remove(key);
            assert!(serde_json::from_value::<ArmDescriptorV4>(omitted).is_err(), "required key {key}");
            let mut wrong = expected.clone();
            wrong[key] = match key.as_str() {
                "arm" => json!(if literal { "relevant_memory_scene_v1" } else { "literal_scene_v1" }),
                "context_policy" => json!("state_recent_transcript_v1"),
                name if name.ends_with("version") => json!(99),
                _ => json!("wrong"),
            };
            if let Ok(parsed) = serde_json::from_value::<ArmDescriptorV4>(wrong) {
                assert!(parsed.validate().is_err(), "invalid full tuple {key}");
            }
        }
        let mut unknown = expected;
        unknown["execution_grant"] = json!(true);
        assert!(serde_json::from_value::<ArmDescriptorV4>(unknown).is_err());
    }
}

#[test]
fn current_binding_keeps_original_suite_and_resource_limits() {
    let value = serde_json::to_value(wire::current_binding(false).unwrap()).unwrap();
    assert_eq!(value["protocol_version"], 4);
    assert_eq!(value["arms"], serde_json::to_value(wire::arm_descriptors()).unwrap());
    assert_eq!(value["suite_sha256"], frozen_suite().unwrap().sha256().unwrap());
    assert_eq!(value["max_admissions"], 32);
    assert_eq!(value["max_roles"], 96);
    assert_eq!(value["max_active_ms"], 1_800_000);
    assert_eq!(value["forwarded_budget_version"], 1);
    assert_eq!(value["attempts"], 24);
    assert_eq!(value["expected_accepted"], 21);
    assert_eq!(value["expected_guard_only"], 3);
    assert_eq!(value["native"], false);
    assert_eq!(value["source_sha256"].as_str().unwrap().len(), 64);
}

#[test]
fn actual_full_paired_and_rollout_match_all_original_outcomes_and_source_bound_captures() {
    let paired = copied(&templates().paired, "full-paired");
    let rollout = copied(&templates().rollout, "full-rollout");
    full_checks(&paired, true);
    full_checks(&rollout, false);
}

#[test]
fn partial_resume_preserves_original_checkpoints_then_completed_resume_is_byte_read_only() {
    let t = templates();
    assert_eq!(t.first["turns"].as_array().unwrap().len(), 12);
    assert_eq!(t.second["turns"].as_array().unwrap().len(), 24);
    assert_eq!(t.completed["turns"].as_array().unwrap().len(), 48);
    for original in t.first["turns"].as_array().unwrap() {
        for later in [&t.second, &t.completed] {
            assert_eq!(row(later, original["turn"].as_str().unwrap(), original["arm"].as_str().unwrap()), original);
        }
    }
    let final_bytes = inventory(&t.rollout);
    for (path, bytes) in &t.first_bytes {
        if path.file_name().and_then(|v| v.to_str()).is_some_and(|v| v.starts_with("attempt-") || v.starts_with("raw-") || v.contains("-capture.json") || v.contains("-recording.json")) {
            assert_eq!(final_bytes.get(path), Some(bytes));
        }
    }
    let dir = copied(&t.rollout, "completed-resume");
    let before = inventory(&dir);
    let reopened = serde_json::to_value(scene_v4::inspect_comparison(&dir).unwrap()).unwrap();
    assert_eq!(run(&dir, true, ComparisonKind::ContinuousRollout, 4, None), reopened);
    assert_eq!(inventory(&dir), before);
    // Closed LaneFactory has no injected poll counter. This measures identical
    // full admission/recording/raw/database/report inventories, not hidden work.
}

fn reseal_scene(dir: &Path, scene: usize) {
    let path = dir.join(format!("scene-{scene:02}.json"));
    let mut seal = read(&path);
    let mut hashes = Vec::new();
    for index in scene * 6..scene * 6 + 6 {
        for arm in ["left", "right"] {
            hashes.push(digest(&fs::read(checkpoint(dir, arm, index)).unwrap()));
        }
    }
    assert_eq!(seal["version"], 4);
    seal["checkpoints"] = json!(hashes);
    save(&path, &seal);
}

#[test]
fn resealed_checkpoint_row_cannot_replace_actual_store_narration_or_tuple() {
    for field in ["narration", "actual_receipt_sha256", "scene_frame_sha256", "construction"] {
        let dir = copied(&templates().rollout, "resealed-row");
        let path = checkpoint(&dir, "left", 0);
        let mut cp = read(&path);
        cp["row"][field] = if field == "construction" { expected_descriptor(false) }
            else { json!(if field == "narration" { "SYNTHETIC_FORGED_PROSE".into() } else { "0".repeat(64) }) };
        save(&path, &cp);
        reseal_scene(&dir, 0);
        inspect_refusal_unchanged(&dir);
    }
}

#[test]
fn rehashed_narrator_forwarding_or_candidate_forgery_cannot_claim_validated_source() {
    for fault in ["prompt", "schema", "candidate"] {
        let dir = copied(&templates().rollout, "resealed-source");
        let cp_path = checkpoint(&dir, "left", 0);
        let mut cp = read(&cp_path);
        let capture_path = dir.join("left").join(cp["capture_file"].as_str().unwrap());
        let recording_path = dir.join("left").join(cp["recording_file"].as_str().unwrap());
        let mut capture = read(&capture_path);
        let mut recording = read(&recording_path);
        let artifacts = capture["data"]["details"]["artifacts"].as_array_mut().unwrap();
        if fault == "candidate" {
            let candidate = artifacts.iter_mut().find(|a| a["kind"] == "accepted_candidate_not_durable_commit").unwrap();
            candidate["value"]["play"]["scene"]["frame_sha256"] = json!("f".repeat(64));
            cp["row"]["scene_frame_sha256"] = json!("f".repeat(64));
        } else {
            let generation = artifacts.iter_mut().find(|a| a["kind"] == "generation_request" && a["value"]["input"]["role"] == "narrator").unwrap();
            if fault == "prompt" {
                let text = generation["value"]["input"]["prompt"].as_str().unwrap();
                generation["value"]["input"]["prompt"] = json!(format!("{text} SYNTHETIC_REHASHED_FORGERY"));
            } else {
                generation["value"]["input"]["schema"]["properties"]["speaker"]["const"] = json!("forged");
            }
            let prompt_hash = digest(generation["value"]["input"]["prompt"].as_str().unwrap().as_bytes());
            let schema_hash = digest(&serde_json::to_vec(&generation["value"]["input"]["schema"]).unwrap());
            let rec = recording["captures"].as_array_mut().unwrap().iter_mut().find(|c| c["role"] == "narrator").unwrap();
            rec["prompt_sha256"] = json!(prompt_hash);
            rec["schema_sha256"] = json!(schema_hash);
            cp["row"]["narrator_prompt_sha256"] = rec["prompt_sha256"].clone();
            cp["row"]["narrator_schema_sha256"] = rec["schema_sha256"].clone();
        }
        cp["row"]["capture_sha256"] = json!(digest(&serde_json::to_vec(&capture).unwrap()));
        cp["row"]["recording_sha256"] = json!(digest(&serde_json::to_vec(&recording).unwrap()));
        save(&capture_path, &capture);
        save(&recording_path, &recording);
        save(&cp_path, &cp);
        reseal_scene(&dir, 0);
        inspect_refusal_unchanged(&dir);
    }
}

#[test]
fn missing_referenced_capture_or_raw_file_cannot_be_vacuous_privacy_success() {
    for raw in [false, true] {
        let dir = copied(&templates().rollout, "missing-evidence");
        let cp = read(&checkpoint(&dir, "left", 0));
        let path = if raw {
            let recording = read(&dir.join("left").join(cp["recording_file"].as_str().unwrap()));
            dir.join("left").join(recording["raw"][0]["file"].as_str().unwrap())
        } else { dir.join("left").join(cp["capture_file"].as_str().unwrap()) };
        assert!(path.starts_with(&dir));
        fs::remove_file(path).unwrap();
        inspect_refusal_unchanged(&dir);
    }
}

#[test]
fn actual_commit_without_its_checkpoint_recovers_unknown_unavailable_not_new_inference() {
    let dir = copied(&templates().partial, "lost-checkpoint");
    fs::remove_file(checkpoint(&dir, "left", 5)).unwrap();
    fs::remove_file(dir.join("scene-00.json")).unwrap();
    let db_before = fs::read(database(&dir, "left", 0, false)).unwrap();
    let files_before = inventory(&dir);
    let recovered = run(&dir, true, ComparisonKind::ContinuousRollout, 1, None);
    let r = row(&recovered, "courier-06", "left");
    assert_eq!(r["phase"], "committed");
    assert_eq!(r["recovered_without_checkpoint"], true);
    assert_eq!(r["roles_known"], false);
    assert_eq!(r["passed"], false);
    assert_eq!(r["construction_evidence_status"], "unavailable");
    assert_eq!(r["privacy_evidence_status"], "unavailable");
    assert!(r["construction_evidence_reason"].as_str().is_some_and(|v| !v.is_empty()));
    for key in ["narrator_prompt_sha256", "narrator_schema_sha256", "scene_frame_sha256"] {
        assert!(r[key].is_null());
    }
    assert_eq!(fs::read(database(&dir, "left", 0, false)).unwrap(), db_before);
    let files_after = inventory(&dir);
    for (path, bytes) in files_before {
        if path.file_name().and_then(|v| v.to_str()).is_some_and(|v| v.starts_with("raw-") || v.contains("-capture.json") || v.contains("-recording.json")) {
            assert_eq!(files_after.get(&path), Some(&bytes));
        }
    }
}

#[test]
fn source_profile_descriptor_and_protocol_drift_refuse_resume_before_new_admission() {
    for fault in ["source", "profile", "descriptor", "version"] {
        let dir = copied(&templates().partial, "binding-drift");
        let path = dir.join("run.json");
        let mut manifest = read(&path);
        match fault {
            "source" => manifest["source_sha256"] = json!("0".repeat(64)),
            "profile" => manifest["profile"]["context_tokens"] = json!(0),
            "descriptor" => manifest["binding"]["arms"][0]["scene_frame_version"] = json!(99),
            _ => manifest["version"] = json!(3),
        }
        save(&path, &manifest);
        let before = inventory(&dir);
        refuse(scene_v4::run_comparison(&dir, true, ComparisonKind::ContinuousRollout,
            &Cancellation::default(), 1, LaneFactory::ScriptedBaseline, None));
        assert_eq!(inventory(&dir), before);
        if fault == "source" {
            if let Ok(report) = scene_v4::inspect_comparison(&dir) {
                assert!(!report.source_matches);
            }
            assert_eq!(inventory(&dir), before);
        }
    }
}

#[test]
fn pre_cancel_invalid_scene_count_and_reference_combination_create_no_run() {
    let base = root("early-refusal");
    let cancel = Cancellation::default();
    cancel.cancel();
    let path = base.join("cancelled");
    refuse(scene_v4::run_comparison(&path, false, ComparisonKind::ContinuousRollout,
        &cancel, 1, LaneFactory::ScriptedBaseline, None));
    assert!(!path.exists());
    for scenes in [0, 5] {
        let path = base.join(format!("scenes-{scenes}"));
        refuse(scene_v4::run_comparison(&path, false, ComparisonKind::ContinuousRollout,
            &Cancellation::default(), scenes, LaneFactory::ScriptedBaseline, None));
        assert!(!path.exists());
    }
    let path = base.join("paired-without-reference");
    refuse(scene_v4::run_comparison(&path, false, ComparisonKind::PairedSnapshots,
        &Cancellation::default(), 1, LaneFactory::ScriptedBaseline, None));
    assert!(!path.exists());
}

#[test]
fn existing_reservations_and_settlements_retain_original_limits_and_actual_role_counts() {
    let dir = copied(&templates().rollout, "ledger");
    let report = serde_json::to_value(scene_v4::inspect_comparison(&dir).unwrap()).unwrap();
    for arm in ["left", "right"] {
        let mut admissions = 0;
        let mut roles = 0;
        for index in 0..32 {
            let path = dir.join(arm).join(format!("admission-{index:02}.json"));
            if !path.exists() { continue; }
            admissions += 1;
            let reserved = read(&path);
            assert_eq!(reserved["version"], 1);
            assert_eq!(reserved["index"], index);
            assert_eq!(reserved["ms"], 60_000);
            assert_eq!(reserved["roles"], 3);
            let settled = read(&dir.join(arm).join(format!("admission-{index:02}-settled.json")));
            assert_eq!(settled["version"], 1);
            assert_eq!(settled["index"], index);
            assert!(settled["ms"].as_u64().unwrap() <= 60_000);
            roles += settled["roles"].as_u64().unwrap();
        }
        assert_eq!((admissions, roles), (24, 42));
        assert!(report[format!("{arm}_charged_ms")].as_u64().unwrap() <= 1_800_000);
        assert!(report[format!("{arm}_reserved_roles")].as_u64().unwrap() <= 96);
    }
    let reservation = dir.join("left/admission-00.json");
    let mut forged = read(&reservation);
    forged["ms"] = json!(60_001);
    save(&reservation, &forged);
    inspect_refusal_unchanged(&dir);
    // Scripted settlement observations do not establish native process drain.
}

#[test]
fn protocol3_reader_and_new_reader_do_not_adopt_each_others_checkpoints() {
    let old = root("protocol3").join("run");
    let old_report = comparison::literal_v3::run_comparison(&old, false,
        ComparisonKind::ContinuousRollout, &Cancellation::default(), 1,
        LaneFactory::ScriptedBaseline, None).unwrap();
    let old_bytes = inventory(&old);
    refuse(scene_v4::inspect_comparison(&old));
    assert_eq!(inventory(&old), old_bytes);
    assert_eq!(serde_json::to_value(comparison::literal_v3::inspect_comparison(&old).unwrap()).unwrap(),
        serde_json::to_value(old_report).unwrap());
    assert_eq!(inventory(&old), old_bytes);
    let new = copied(&templates().partial, "protocol4-reader");
    let new_bytes = inventory(&new);
    refuse(comparison::literal_v3::inspect_comparison(&new));
    assert_eq!(inventory(&new), new_bytes);
}

#[test]
fn report_nullable_fields_and_unknown_members_remain_closed_metadata() {
    let report = templates().completed.clone();
    let _: ComparisonReportV4 = serde_json::from_value(report.clone()).unwrap();
    let mut extra = report.clone();
    extra["execution_grant"] = json!(true);
    assert!(serde_json::from_value::<ComparisonReportV4>(extra).is_err());
    for key in ["physical_setup_ms", "native_load", "first_semantic_divergence", "first_mechanical_divergence", "reference_sha256"] {
        let mut omitted = report.clone();
        omitted.as_object_mut().unwrap().remove(key);
        assert!(serde_json::from_value::<ComparisonReportV4>(omitted).is_err(), "required nullable report {key}");
    }
}

#[cfg(feature = "local-model")]
mod native_before_owner {
    use super::*;
    use locallore_eval::local_lane::{comparison::selected::SelectedNativeReservation, NativeAssets};
    use locallore_local_runtime::LocalRuntime;
    use std::sync::{Arc, Mutex, atomic::AtomicUsize};
    struct NoAssets;
    impl SelectedNativeReservation for NoAssets {
        fn assets(&self) -> NativeAssets<'_> { panic!("before-owner oracle must not open assets") }
        fn retain_uncertain(&mut self, _: Arc<Mutex<LocalRuntime>>) -> Result<(), Arc<Mutex<LocalRuntime>>> {
            panic!("no runtime exists to retain in a before-owner oracle")
        }
    }
    #[test]
    fn native_public_pre_cancel_and_scene_refusal_do_not_reserve_or_open_assets() {
        let base = root("native-before-owner");
        let calls = AtomicUsize::new(0);
        for (index, scenes) in [1, 0, 5].into_iter().enumerate() {
            let cancel = Cancellation::default();
            if scenes == 1 { cancel.cancel(); }
            let path = base.join(format!("case-{index}"));
            let result = scene_v4::run_native_comparison(&path, false,
                ComparisonKind::ContinuousRollout, &cancel, scenes,
                || { calls.fetch_add(1, Ordering::SeqCst); Ok(NoAssets) }, None);
            assert!(result.is_err());
            assert_eq!(calls.load(Ordering::SeqCst), 0);
            assert!(!path.exists());
        }
    }
    #[test]
    fn native_reservation_refusal_never_opens_assets_or_creates_turn_admission() {
        let path = root("native-reserve-refusal").join("run");
        let calls = AtomicUsize::new(0);
        let result = scene_v4::run_native_comparison(&path, false,
            ComparisonKind::ContinuousRollout, &Cancellation::default(), 1,
            || { calls.fetch_add(1, Ordering::SeqCst); Err::<NoAssets, _>("SelectedResourceBusy".into()) }, None);
        assert!(result.is_err());
        assert_eq!(calls.load(Ordering::SeqCst), 1);
        if path.exists() {
            for key in inventory(&path).keys() {
                assert!(!key.file_name().and_then(|v| v.to_str()).is_some_and(|v| v.starts_with("admission-") || v.starts_with("invocation-")));
            }
        }
        // No runtime was created: this is reservation refusal, not measured drain.
    }
}
