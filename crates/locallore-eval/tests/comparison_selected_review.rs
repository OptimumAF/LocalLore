// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Six frozen scripted selected-case groups. SOURCE-ONLY, UNCOMPILED/UNRUN.
//! Root freeze #29 6394962471; claim6394969024, base42d76520.
//! Actual existing public producer/Core/Store fixtures; no native/model calls,
//! forged receipts, SQL writer, source relabelling or public fault hooks.
//! Root: cargo test --manifest-path crates/locallore-eval/Cargo.toml --locked --offline --test comparison_selected_review -- --test-threads=1
use locallore::{
    contracts::{Command, Intent, Proposal, VERSION},
    engine::Engine,
    inference::Cancellation,
};
use locallore_eval::{
    local_lane::{
        comparison::{self, desktop_api, selected, ComparisonKind},
        LaneFactory,
    },
    memory_comparison::frozen_suite,
    memory_comparison_v2::{semantic_input, TurnReportV2},
};
use locallore_storage::Store;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::{Path, PathBuf},
    sync::{atomic::{AtomicU64, Ordering}, OnceLock},
};

static NEXT: AtomicU64 = AtomicU64::new(0);
const SELECTED_INDEX: usize = 4;
type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;

fn owned_root(label: &str) -> PathBuf {
    let root = std::env::temp_dir().join(format!(
        "locallore-selected-public-{label}-{}-{}-{}",
        std::process::id(),
        std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH)
            .unwrap().as_nanos(),
        NEXT.fetch_add(1, Ordering::Relaxed)
    ));
    fs::create_dir(&root).unwrap();
    root
}

fn inventory(root: &Path) -> Inventory {
    fn walk(root: &Path, path: &Path, depth: usize, total: &mut usize, out: &mut Inventory) {
        assert!(depth <= 8 && out.len() < 4096);
        for entry in fs::read_dir(path).unwrap() {
            let path = entry.unwrap().path();
            let meta = fs::symlink_metadata(&path).unwrap();
            assert!(!meta.file_type().is_symlink());
            let relative = path.strip_prefix(root).unwrap().to_owned();
            if meta.is_dir() {
                assert!(out.insert(relative, None).is_none());
                walk(root, &path, depth + 1, total, out);
            } else {
                assert!(meta.is_file() && meta.len() <= 8 * 1024 * 1024);
                let bytes = fs::read(path).unwrap();
                *total += bytes.len();
                assert!(*total <= 64 * 1024 * 1024);
                assert!(out.insert(relative, Some(bytes)).is_none());
            }
        }
    }
    let mut out = BTreeMap::new();
    walk(root, root, 0, &mut 0, &mut out);
    out
}

fn copy_owned(source: &Path, label: &str) -> PathBuf {
    let snapshot = inventory(source);
    let target = owned_root(label).join("run");
    fs::create_dir(&target).unwrap();
    for (path, value) in &snapshot {
        match value {
            None => fs::create_dir_all(target.join(path)).unwrap(),
            Some(bytes) => fs::write(target.join(path), bytes).unwrap(),
        }
    }
    assert_eq!(inventory(&target), snapshot);
    target
}

fn value(path: &Path) -> Value {
    serde_json::from_slice(&fs::read(path).unwrap()).unwrap()
}
fn hash(bytes: &[u8]) -> String { format!("{:x}", Sha256::digest(bytes)) }
fn keys(value: &Value, expected: &[&str]) {
    assert_eq!(value.as_object().unwrap().keys().map(String::as_str).collect::<BTreeSet<_>>(),
        expected.iter().copied().collect::<BTreeSet<_>>());
}
fn fixed_error<T>(result: Result<T, String>) -> String {
    // Opaque capabilities and reports intentionally need no Debug/public fields.
    let error = result.err().expect("fixed refusal, never a successful capability");
    assert!(!error.is_empty() && error.len() <= 96);
    assert!(error.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'_'));
    error
}
fn hex(value: &Value) {
    let text = value.as_str().unwrap();
    assert_eq!(text.len(), 64);
    assert!(text.bytes().all(|b| b.is_ascii_hexdigit() && !b.is_ascii_uppercase()));
}
fn json_report(report: selected::SelectedComparisonReportV1) -> Value {
    serde_json::to_value(report).unwrap()
}
fn intent(client: &str) -> selected::SelectedIntent {
    selected::SelectedIntent { client_id: client.into(), lane: selected::SelectedLane::ScriptedBaseline }
}
fn row() -> desktop_api::RowId {
    desktop_api::RowId {
        turn: frozen_suite().unwrap().steps()[SELECTED_INDEX].id().into(),
        arm: desktop_api::Arm::Right,
    }
}
fn source_binding(source: &Path) -> String {
    let opened = desktop_api::open_read_only(source).unwrap();
    let summary = desktop_api::summary(&opened, true).unwrap();
    let result = summary["binding"].as_str().unwrap().to_owned();
    drop(opened); // No inventory read/prepare while Windows run.lock is held.
    result
}
fn checkpoint(dir: &Path, arm: &str) -> PathBuf {
    dir.join(arm).join(format!("attempt-{SELECTED_INDEX:02}.json"))
}
fn engine(path: &Path) -> Engine {
    Store::open_read_only(path).unwrap()
        .resume(&frozen_suite().unwrap().seed().scope).unwrap().engine
}
fn only_database(dir: &Path, arm: &str) -> PathBuf {
    let paths: Vec<_> = fs::read_dir(dir.join(arm)).unwrap()
        .map(|entry| entry.unwrap().path())
        .filter(|path| path.extension().is_some_and(|s| s == "sqlite"))
        .collect();
    assert_eq!(paths.len(), 1, "one isolated actual Store per selected arm");
    paths[0].clone()
}

struct Producers { paired: PathBuf, rollout: PathBuf, reference: PathBuf }
fn producers() -> &'static Producers {
    static PRODUCERS: OnceLock<Producers> = OnceLock::new();
    PRODUCERS.get_or_init(|| {
        let root = owned_root("producers");
        let reference = root.join("reference");
        let reference_report = comparison::prepare_reference(&reference, &Cancellation::default()).unwrap();
        assert_eq!((reference_report.accepted, reference_report.guard_only, reference_report.roles), (21, 3, 42));
        let prepared_reference = comparison::open_reference(&reference).unwrap();
        let paired = root.join("paired");
        let paired_report = comparison::run_comparison(&paired, false, ComparisonKind::PairedSnapshots,
            &Cancellation::default(), 1, LaneFactory::ScriptedBaseline, Some(&prepared_reference)).unwrap();
        let rollout = root.join("rollout");
        let rollout_report = comparison::run_comparison(&rollout, false, ComparisonKind::ContinuousRollout,
            &Cancellation::default(), 1, LaneFactory::ScriptedBaseline, None).unwrap();
        for report in [&paired_report, &rollout_report] {
            assert_eq!(report.turns.len(), 12);
            assert_eq!(report.completed_scenes, 1);
            assert!(report.turns.iter().all(|turn| turn.passed));
        }
        Producers { paired, rollout, reference }
    })
}

fn execute_selected(source: &Path, destination: &Path, client: &str) -> Value {
    let binding = source_binding(source);
    let plan = selected::prepare_selected(source, &binding, &row(), intent(client), &Cancellation::default()).unwrap();
    json_report(selected::run_selected(plan, destination, &Cancellation::default()).unwrap())
}

fn check_exact_report(source: &Path, destination: &Path, report: &Value) {
    keys(report, &[
        "version", "run_type", "source_protocol_version", "binding", "source_binding",
        "source_kind", "source_profile", "selection", "lane", "profile", "suite_sha256",
        "source_sha256", "source_reference_sha256", "source_inputs", "rows", "completed",
        "per_arm_progress", "physical_setups", "physical_setup_ms", "native_load",
        "left_charged_ms", "right_charged_ms", "left_reserved_roles", "right_reserved_roles",
        "human_reviewed", "human_rubric", "quality_accepted", "unavailable", "limitations",
    ]);
    assert_eq!(report["version"], 1);
    assert_eq!(report["run_type"], "selected_case");
    assert_eq!(report["source_protocol_version"], 2);
    assert_eq!(report["lane"], "scripted_selected_case");
    assert_eq!(report["source_binding"], source_binding(source));
    assert_eq!(report["selection"], json!({"turn":row().turn,"clicked_arm":"right","index":SELECTED_INDEX}));
    assert_eq!(report["completed"], true);
    assert_eq!(report["human_reviewed"], 0);
    assert_eq!(report["human_rubric"], "not_reviewed");
    assert_eq!(report["quality_accepted"], false);
    hex(&report["binding"]);
    let source_manifest = value(&source.join("run.json"));
    assert_eq!(report["source_kind"], source_manifest["kind"]);
    assert_eq!(report["source_profile"], source_manifest["profile"]);
    let manifest = value(&destination.join("selected.json"));
    keys(&manifest, &["version", "run_type", "client_id", "binding", "source_binding",
        "source_kind", "source_profile", "selection", "lane", "profile", "suite_sha256",
        "source_sha256", "source_reference_sha256", "source_inputs"]);
    assert!(!manifest["client_id"].as_str().unwrap().is_empty());
    for field in ["version", "run_type", "binding", "source_binding", "source_kind",
        "source_profile", "selection", "lane", "profile", "suite_sha256", "source_sha256",
        "source_reference_sha256", "source_inputs"] {
        assert_eq!(manifest[field], report[field]);
    }
    let rows = report["rows"].as_array().unwrap();
    let inputs = report["source_inputs"].as_array().unwrap();
    let progress = report["per_arm_progress"].as_array().unwrap();
    assert_eq!((rows.len(), inputs.len(), progress.len()), (2, 2, 2));
    let suite = frozen_suite().unwrap();
    for (n, arm) in ["left", "right"].iter().enumerate() {
        let cp = value(&checkpoint(source, arm));
        let source_db = if source_manifest["kind"] == "paired_snapshots" {
            source.join(arm).join(format!("pair-{SELECTED_INDEX:02}.sqlite"))
        } else { source.join(arm).join("synthetic.sqlite") };
        let full = engine(&source_db);
        let before = full.at_revision(cp["before_head"].as_u64().unwrap()).unwrap();
        let request = suite.steps()[SELECTED_INDEX].request(&before);
        keys(&inputs[n], &["arm", "scope", "before_head", "request", "prefix_sha256", "input_semantic_sha256"]);
        assert_eq!(inputs[n]["arm"], *arm);
        assert_eq!(inputs[n]["scope"], serde_json::to_value(before.scope()).unwrap());
        assert_eq!(inputs[n]["before_head"], before.revision());
        assert_eq!(inputs[n]["request"], serde_json::to_value(&request).unwrap());
        assert_eq!(inputs[n]["request"], cp["request"]);
        assert_eq!(inputs[n]["input_semantic_sha256"], semantic_input(&before, &request).unwrap());
        // Root's explicit follow-up freeze: digest(crate::encode(actual receipts)).
        assert_eq!(inputs[n]["prefix_sha256"], hash(&serde_json::to_vec(before.receipts()).unwrap()));
        let actual_row: TurnReportV2 = serde_json::from_value(rows[n].clone()).unwrap();
        assert_eq!(actual_row.turn, request.turn);
        assert_eq!(actual_row.arm, *arm);
        assert_eq!(actual_row.phase, "committed");
        assert_eq!(actual_row.input_semantic_sha256, inputs[n]["input_semantic_sha256"].as_str().unwrap());
        assert_eq!(actual_row.output_semantic_sha256, cp["row"]["output_semantic_sha256"].as_str().unwrap());
        assert_eq!(actual_row.mechanical_sha256, cp["row"]["mechanical_sha256"].as_str().unwrap());
        assert!(actual_row.roles_known && !actual_row.recovered_without_checkpoint);
        assert_eq!(actual_row.roles, 2);
        assert_eq!(progress[n], json!({"arm":arm,"state":"finished"}));
        let isolated = engine(&only_database(destination, arm));
        assert_eq!(isolated.receipts().len(), before.receipts().len() + 1);
        assert_eq!(&isolated.receipts()[..before.receipts().len()], before.receipts());
        let cut = isolated.at_revision(before.revision()).unwrap();
        assert_eq!(cut.canonical_bytes(), before.canonical_bytes());
        assert_eq!(isolated.receipts().last().unwrap().request(), &request);
        assert!(checkpoint(destination, arm).exists(), "actual emitted original-index checkpoint");
        assert!(!destination.join(arm).join("attempt-00.json").exists(), "no preceding generated step");
        let admissions = fs::read_dir(destination.join(arm)).unwrap()
            .map(|e| e.unwrap().file_name().to_string_lossy().into_owned())
            .filter(|name| name.starts_with("admission-") && !name.contains("settled")).count();
        assert_eq!(admissions, 1, "only one selected admitted attempt per arm");
    }
    assert_eq!(json_report(selected::inspect_selected(destination).unwrap()), *report);
}

#[test]
fn noninitial_paired_selection_preserves_actual_reference_prefix_and_full_requests() {
    let source = copy_owned(&producers().paired, "paired-source");
    let before_files = inventory(&source);
    let destination = owned_root("paired-output").join("selected");
    let report = execute_selected(&source, &destination, "paired-selected");
    check_exact_report(&source, &destination, &report);
    let reference = engine(&producers().reference.join("synthetic.sqlite"));
    for arm in ["left", "right"] {
        let cp = value(&checkpoint(&source, arm));
        let before = reference.at_revision(cp["before_head"].as_u64().unwrap()).unwrap();
        let isolated = engine(&only_database(&destination, arm));
        assert_eq!(&isolated.receipts()[..before.receipts().len()], before.receipts());
    }
    assert_eq!(inventory(&source), before_files);
}

#[test]
fn rollout_selection_uses_each_actual_arm_cut_without_generating_preceding_turns() {
    let source = copy_owned(&producers().rollout, "rollout-source");
    let before_files = inventory(&source);
    let destination = owned_root("rollout-output").join("selected");
    let report = execute_selected(&source, &destination, "rollout-selected");
    check_exact_report(&source, &destination, &report);
    assert_eq!(inventory(&source), before_files);
    // Both scripted source arms happen to agree. This is actual per-arm-cut
    // coverage, not a fabricated divergent-rollout or real-model claim.
}

#[test]
fn cached_reader_lock_is_not_execution_authority_then_fresh_binding_can_prepare() {
    let source = copy_owned(&producers().paired, "reader-lock");
    let before_files = inventory(&source);
    let opened = desktop_api::open_read_only(&source).unwrap();
    let summary = desktop_api::summary(&opened, true).unwrap();
    let binding = summary["binding"].as_str().unwrap().to_owned();
    assert_eq!(fixed_error(selected::prepare_selected(&source, &binding, &row(), intent("held-reader"),
        &Cancellation::default())), "RunBusy");
    drop(opened);
    let fresh = source_binding(&source);
    assert_eq!(fresh, binding);
    let prepared = selected::prepare_selected(&source, &fresh, &row(), intent("fresh-reader"),
        &Cancellation::default()).unwrap();
    drop(prepared);
    assert_eq!(inventory(&source), before_files);
}

#[test]
fn invalid_identity_cancel_and_required_source_corruption_refuse_without_output_or_repair() {
    let source = copy_owned(&producers().paired, "early-source");
    let original = inventory(&source);
    let binding = source_binding(&source);
    for bad in [String::new(), "bad/client".into(), "a".repeat(129)] {
        fixed_error(selected::prepare_selected(&source, &binding, &row(), intent(&bad), &Cancellation::default()));
        assert_eq!(inventory(&source), original);
    }
    let stale = if binding == "0".repeat(64) { "1".repeat(64) } else { "0".repeat(64) };
    fixed_error(selected::prepare_selected(&source, &stale, &row(), intent("stale-binding"), &Cancellation::default()));
    let cancelled = Cancellation::default();
    cancelled.cancel();
    fixed_error(selected::prepare_selected(&source, &binding, &row(), intent("cancelled-prepare"), &cancelled));
    let destination = owned_root("cancel-output").join("must-not-exist");
    let plan = selected::prepare_selected(&source, &binding, &row(), intent("cancelled-run"), &Cancellation::default()).unwrap();
    fixed_error(selected::run_selected(plan, &destination, &cancelled));
    assert!(!destination.exists());
    assert_eq!(inventory(&source), original);
    let cp = value(&checkpoint(&source, "right"));
    let capture = source.join("right").join(cp["capture_file"].as_str().unwrap());
    assert!(capture.is_file());
    fs::write(&capture, b"SYNTHETIC_REQUIRED_CAPTURE_CORRUPTION").unwrap();
    let faulted = inventory(&source);
    fixed_error(selected::prepare_selected(&source, &binding, &row(), intent("corrupt-source"), &Cancellation::default()));
    assert_eq!(inventory(&source), faulted);
    assert!(!destination.exists());
}

#[test]
fn completed_selected_resume_is_exact_read_only_with_original_source_inventory() {
    let source = copy_owned(&producers().paired, "completed-source");
    let source_files = inventory(&source);
    let destination = owned_root("completed-output").join("selected");
    let report = execute_selected(&source, &destination, "completed-selected");
    let before_files = inventory(&destination);
    let binding = report["binding"].as_str().unwrap();
    for _ in 0..2 {
        assert_eq!(json_report(selected::resume_selected(&destination, &source, binding, &Cancellation::default()).unwrap()), report);
        assert_eq!(json_report(selected::inspect_selected(&destination).unwrap()), report);
        assert_eq!(inventory(&destination), before_files);
        assert_eq!(inventory(&source), source_files);
    }
}

fn append_actual_off_reference_wait(path: &Path) {
    let mut store = Store::open_application(path).unwrap();
    let scope = frozen_suite().unwrap().seed().scope.clone();
    let mut candidate = store.resume(&scope).unwrap().engine;
    let command = Command::Wait { ticks: 1 };
    let request = candidate.request("selected-off-reference-wait", Intent::Actions(vec![command.clone()]));
    let proposal = Proposal { version: VERSION, scope: scope.clone(), turn: request.turn.clone(),
        expected_revision: request.expected_revision, commands: vec![command] };
    let approved = candidate.preview(&request, &proposal).unwrap();
    let receipt = candidate.commit(&request, &proposal, approved.narration()).unwrap();
    store.begin_turn(&request).unwrap();
    store.commit_prepared(&receipt).unwrap();
    assert_eq!(store.resume(&scope).unwrap().engine.receipts(), candidate.receipts());
}

#[test]
fn lost_actual_checkpoint_recovers_once_and_both_completed_half_and_off_reference_guards_preflight() {
    let source = copy_owned(&producers().paired, "recovery-source");
    let source_files = inventory(&source);
    let destination = owned_root("recovery-output").join("selected");
    let report = execute_selected(&source, &destination, "recover-selected");
    let binding = report["binding"].as_str().unwrap().to_owned();
    let original_canonical: Vec<_> = ["left", "right"].iter()
        .map(|arm| engine(&only_database(&destination, arm))).collect();
    let original_turn_work: Inventory = inventory(&destination).into_iter().filter(|(path, _)| {
        let name = path.file_name().unwrap().to_string_lossy();
        name.starts_with("admission-") || name.starts_with("raw-") || name.contains("-capture") || name.contains("-recording")
    }).collect();
    // execute_turn itself emitted this durable workflow file after the real
    // Store commit. Remove ONLY that actual file: workflow-loss model, not a
    // measured process kill or canonical receipt forgery.
    let lost = checkpoint(&destination, "left");
    assert!(lost.is_file());
    fs::remove_file(&lost).unwrap();
    let recovered = json_report(selected::resume_selected(&destination, &source, &binding, &Cancellation::default()).unwrap());
    assert_eq!(recovered["completed"], true);
    assert_eq!(recovered["rows"].as_array().unwrap().len(), 2);
    assert_eq!(recovered["rows"][0]["recovered_without_checkpoint"], true);
    assert_eq!(recovered["rows"][0]["roles_known"], false);
    assert_eq!(recovered["rows"][0]["actual_receipt_sha256"], report["rows"][0]["actual_receipt_sha256"]);
    assert_eq!(recovered["rows"][1], report["rows"][1]);
    assert!(recovered["rows"][0]["role_metrics"].is_null());
    let after_work: Inventory = inventory(&destination).into_iter().filter(|(path, _)| {
        let name = path.file_name().unwrap().to_string_lossy();
        name.starts_with("admission-") || name.starts_with("raw-") || name.contains("-capture") || name.contains("-recording")
    }).collect();
    assert_eq!(after_work, original_turn_work);
    for (n, arm) in ["left", "right"].iter().enumerate() {
        let current = engine(&only_database(&destination, arm));
        assert_eq!(current.receipts(), original_canonical[n].receipts());
        assert_eq!(current.canonical_bytes(), original_canonical[n].canonical_bytes());
    }
    // Missing left checkpoint must not let an invalid completed RIGHT half
    // evade fresh both-arm preflight or reserve another invocation/role.
    for fault in ["completed-checkpoint", "off-reference-canonical"] {
        let bad = copy_owned(&destination, fault);
        fs::remove_file(checkpoint(&bad, "left")).unwrap();
        if fault == "completed-checkpoint" {
            fs::write(checkpoint(&bad, "right"), b"SYNTHETIC_CORRUPT_COMPLETED_HALF").unwrap();
        } else {
            append_actual_off_reference_wait(&only_database(&bad, "right"));
        }
        let expected = inventory(&bad);
        let canonical: Vec<_> = ["left", "right"].iter().map(|arm| engine(&only_database(&bad, arm)).canonical_bytes()).collect();
        fixed_error(selected::resume_selected(&bad, &source, &binding, &Cancellation::default()));
        assert_eq!(inventory(&bad), expected, "no ledger/source/destination mutation on refusal");
        for (n, arm) in ["left", "right"].iter().enumerate() {
            assert_eq!(engine(&only_database(&bad, arm)).canonical_bytes(), canonical[n]);
        }
    }
    assert_eq!(inventory(&source), source_files);
}
