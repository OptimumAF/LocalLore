// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! SOURCE ONLY / UNCOMPILED / UNRUN. Six public scripted selected2 groups.
//! Actual V3 producers/Core/Store; no native/model calls, fabricated accepted
//! records, SQL writer, source relabel, cost ledger or public fault factory.
use locallore::{engine::Engine, inference::Cancellation};
use locallore_eval::{
    local_lane::{
        comparison::{
            self, desktop_api,
            literal_v3::{self, selected_v2},
            selected, ComparisonKind,
        },
        LaneFactory,
    },
    memory_comparison::frozen_suite,
    memory_comparison_v2::semantic_input,
    memory_comparison_v3::arm_descriptors,
};
use locallore_storage::{Store, TurnPhase};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    collections::BTreeMap,
    fs,
    path::{Path, PathBuf},
    sync::{
        atomic::{AtomicUsize, Ordering},
        OnceLock,
    },
};

const INDEX: usize = 4;
const GUARD: usize = 8;
type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;
fn root(label: &str) -> PathBuf {
    static NEXT: AtomicUsize = AtomicUsize::new(0);
    let p = std::env::temp_dir().join(format!(
        "literal-selected-v2-{label}-{}-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos(),
        NEXT.fetch_add(1, Ordering::Relaxed)
    ));
    fs::create_dir(&p).unwrap();
    p
}
fn inventory(root: &Path) -> Inventory {
    fn walk(root: &Path, p: &Path, depth: usize, total: &mut usize, out: &mut Inventory) {
        assert!(depth <= 8 && out.len() < 4096);
        for e in fs::read_dir(p).unwrap() {
            let p = e.unwrap().path();
            let m = fs::symlink_metadata(&p).unwrap();
            assert!(!m.file_type().is_symlink());
            #[cfg(windows)]
            {
                use std::os::windows::fs::MetadataExt;
                assert_eq!(m.file_attributes() & 0x400, 0);
            }
            let rel = p.strip_prefix(root).unwrap().to_owned();
            if m.is_dir() {
                out.insert(rel, None);
                walk(root, &p, depth + 1, total, out);
            } else {
                assert!(m.is_file() && m.len() <= 8 * 1024 * 1024);
                let b = fs::read(p).unwrap();
                *total = total.checked_add(b.len()).unwrap();
                assert!(*total <= 64 * 1024 * 1024);
                out.insert(rel, Some(b));
            }
        }
    }
    let mut out = Inventory::new();
    walk(root, root, 0, &mut 0, &mut out);
    out
}
fn copied(source: &Path, label: &str) -> PathBuf {
    let original = inventory(source);
    let dir = root(label).join("run");
    fs::create_dir(&dir).unwrap();
    for (p, b) in &original {
        match b {
            None => fs::create_dir_all(dir.join(p)).unwrap(),
            Some(b) => fs::write(dir.join(p), b).unwrap(),
        }
    }
    assert_eq!(inventory(&dir), original);
    dir
}
fn value(p: &Path) -> Value {
    serde_json::from_slice(&fs::read(p).unwrap()).unwrap()
}
fn write(p: &Path, v: &Value) {
    fs::write(p, serde_json::to_vec(v).unwrap()).unwrap();
}
fn refusal<T>(result: Result<T, String>) -> String {
    match result {
        Ok(_) => panic!("expected bounded refusal"),
        Err(e) => {
            assert!(
                !e.is_empty()
                    && e.len() <= 96
                    && e.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'_')
            );
            e
        }
    }
}
fn intent(client: &str) -> selected::SelectedIntent {
    selected::SelectedIntent {
        client_id: client.into(),
        lane: selected::SelectedLane::ScriptedBaseline,
    }
}
fn row(index: usize) -> desktop_api::RowId {
    desktop_api::RowId {
        turn: frozen_suite().unwrap().steps()[index].id().into(),
        arm: desktop_api::Arm::Left,
    }
}
fn binding(dir: &Path) -> String {
    let opened = literal_v3::desktop_api::open_read_only(dir).unwrap();
    let summary = literal_v3::desktop_api::summary(&opened, true).unwrap();
    let binding = summary["binding"].as_str().unwrap().to_owned();
    drop(opened);
    binding
}
fn checkpoint(dir: &Path, arm: &str, index: usize) -> PathBuf {
    dir.join(arm).join(format!("attempt-{index:02}.json"))
}
fn engine(path: &Path) -> Engine {
    Store::open_read_only(path)
        .unwrap()
        .resume(&frozen_suite().unwrap().seed().scope)
        .unwrap()
        .engine
}
fn database(source: &Path, arm: &str, index: usize) -> PathBuf {
    if value(&source.join("run.json"))["kind"] == "paired_snapshots" {
        source.join(arm).join(format!("pair-{index:02}.sqlite"))
    } else {
        source.join(arm).join("synthetic.sqlite")
    }
}
fn only_database(target: &Path, arm: &str) -> PathBuf {
    let files: Vec<_> = fs::read_dir(target.join(arm))
        .unwrap()
        .map(|e| e.unwrap().path())
        .filter(|p| p.extension().is_some_and(|s| s == "sqlite"))
        .collect();
    assert_eq!(files.len(), 1);
    files[0].clone()
}
struct Sources {
    paired: PathBuf,
    rollout: PathBuf,
}
fn sources() -> &'static Sources {
    static SOURCES: OnceLock<Sources> = OnceLock::new();
    SOURCES.get_or_init(|| {
        let root = root("producers");
        let reference = root.join("reference");
        comparison::prepare_reference(&reference, &Cancellation::default()).unwrap();
        let reference = comparison::open_reference(&reference).unwrap();
        let paired = root.join("paired");
        let a = literal_v3::run_comparison(
            &paired,
            false,
            ComparisonKind::PairedSnapshots,
            &Cancellation::default(),
            1,
            LaneFactory::ScriptedBaseline,
            Some(&reference),
        )
        .unwrap();
        assert_eq!((a.completed_scenes, a.turns.len()), (1, 12));
        let rollout = root.join("rollout");
        let b = literal_v3::run_comparison(
            &rollout,
            false,
            ComparisonKind::ContinuousRollout,
            &Cancellation::default(),
            2,
            LaneFactory::ScriptedBaseline,
            None,
        )
        .unwrap();
        assert_eq!((b.completed_scenes, b.turns.len()), (2, 24));
        Sources { paired, rollout }
    })
}
fn run(source: &Path, target: &Path, index: usize, client: &str) -> Value {
    let plan = selected_v2::prepare_selected(
        source,
        &binding(source),
        &row(index),
        intent(client),
        &Cancellation::default(),
    )
    .unwrap();
    serde_json::to_value(selected_v2::run_selected(plan, target, &Cancellation::default()).unwrap())
        .unwrap()
}
fn actual_row<'a>(report: &'a Value, arm: &str) -> &'a Value {
    report["rows"]
        .as_array()
        .unwrap()
        .iter()
        .find(|r| r["arm"] == arm)
        .unwrap()
}
fn check_inputs(source: &Path, target: &Path, report: &Value, index: usize) {
    assert_eq!(report["version"], 2);
    assert_eq!(report["source_protocol_version"], 3);
    assert_eq!(
        report["arms"],
        serde_json::to_value(arm_descriptors()).unwrap()
    );
    assert_eq!(report["completed"], true);
    assert_eq!(report["rows"].as_array().unwrap().len(), 2);
    let manifest = value(&target.join("selected.json"));
    for key in [
        "version",
        "source_protocol_version",
        "arms",
        "source_inputs",
        "source_binding",
        "binding",
    ] {
        assert_eq!(manifest[key], report[key]);
    }
    let suite = frozen_suite().unwrap();
    for (n, arm) in ["left", "right"].iter().enumerate() {
        let cp = value(&checkpoint(source, arm, index));
        let original = engine(&database(source, arm, index));
        let before = original
            .at_revision(cp["before_head"].as_u64().unwrap())
            .unwrap();
        let request = suite.steps()[index].request(&before);
        let input = &report["source_inputs"][n];
        assert_eq!(input["arm"], *arm);
        assert_eq!(
            input["scope"],
            serde_json::to_value(before.scope()).unwrap()
        );
        assert_eq!(input["before_head"], before.revision());
        assert_eq!(input["request"], serde_json::to_value(&request).unwrap());
        assert_eq!(input["request"], cp["request"]);
        assert_eq!(
            input["prefix_sha256"],
            format!(
                "{:x}",
                Sha256::digest(serde_json::to_vec(before.receipts()).unwrap())
            )
        );
        assert_eq!(
            input["input_semantic_sha256"],
            semantic_input(&before, &request).unwrap()
        );
        let row = actual_row(report, arm);
        assert_eq!(
            row["construction"],
            serde_json::to_value(&arm_descriptors()[n]).unwrap()
        );
        assert_eq!(row["input_semantic_sha256"], input["input_semantic_sha256"]);
        assert!(row.get("policy").is_none());
        let isolated = engine(&only_database(target, arm));
        assert_eq!(
            &isolated.receipts()[..before.receipts().len()],
            before.receipts()
        );
        assert_eq!(
            isolated
                .at_revision(before.revision())
                .unwrap()
                .canonical_bytes(),
            before.canonical_bytes()
        );
        assert_eq!(isolated.receipts().last().unwrap().request(), &request);
        assert_eq!(isolated.receipts().len(), before.receipts().len() + 1);
        assert!(checkpoint(target, arm, index).is_file());
        assert!(!checkpoint(target, arm, 0).exists());
        assert_eq!(row["phase"], "committed");
        assert_eq!(row["roles_known"], true);
        assert_eq!(
            row["construction_evidence_status"],
            if n == 0 {
                "validated_literal"
            } else {
                "validated_relevant"
            }
        );
    }
    assert_eq!(
        serde_json::to_value(selected_v2::inspect_selected(target).unwrap()).unwrap(),
        *report
    );
}

#[test]
fn paired_actual_prefixes_requests_descriptors_and_safe_prepared_metadata_are_bound() {
    let source = copied(&sources().paired, "paired");
    let files = inventory(&source);
    let target = root("paired-output").join("selected");
    let source_binding = binding(&source);
    let plan = selected_v2::prepare_selected(
        &source,
        &source_binding,
        &row(INDEX),
        intent("literal-selected-paired"),
        &Cancellation::default(),
    )
    .unwrap();
    let metadata = selected_v2::prepared_metadata(&plan).unwrap();
    assert_eq!(metadata["version"], 2);
    assert_eq!(metadata["source_protocol_version"], 3);
    assert_eq!(
        metadata["constructions"],
        serde_json::to_value(arm_descriptors()).unwrap()
    );
    assert_eq!(metadata["arms"].as_array().unwrap().len(), 2);
    assert_eq!(selected_v2::prepared_metadata(&plan).unwrap(), metadata);
    assert!(serde_json::to_vec(&metadata).unwrap().len() <= 16 * 1024);
    for arm in metadata["arms"].as_array().unwrap() {
        assert!(arm.get("request").is_none());
        assert!(arm.get("narration").is_none());
    }
    assert!(!metadata.to_string().contains(source.to_str().unwrap()));
    let report = serde_json::to_value(
        selected_v2::run_selected(plan, &target, &Cancellation::default()).unwrap(),
    )
    .unwrap();
    check_inputs(&source, &target, &report, INDEX);
    assert_eq!(inventory(&source), files);
}

#[test]
fn rollout_uses_each_real_arm_cut_and_completed_resume_is_byte_identical() {
    let source = copied(&sources().rollout, "rollout");
    let files = inventory(&source);
    let target = root("rollout-output").join("selected");
    let report = run(&source, &target, INDEX, "literal-selected-rollout");
    check_inputs(&source, &target, &report, INDEX);
    let target_files = inventory(&target);
    for _ in 0..2 {
        let resumed = serde_json::to_value(
            selected_v2::resume_selected(
                &target,
                &source,
                report["binding"].as_str().unwrap(),
                &Cancellation::default(),
            )
            .unwrap(),
        )
        .unwrap();
        assert_eq!(resumed, report);
        assert_eq!(inventory(&target), target_files);
        assert_eq!(inventory(&source), files);
    }
    // Stable full ledger/raw/canonical inventory is measured, not a custom
    // provider-count callback. Scripted semantics agree; divergent rollout is
    // NOT qualified by this public fixture (actual Play provenance still differs).
}

#[test]
fn unclicked_source_arm_mutation_after_prepare_refuses_before_new_destination() {
    let source = copied(&sources().paired, "source-drift");
    let mut expected = inventory(&source);
    let old_binding = binding(&source);
    let plan = selected_v2::prepare_selected(
        &source,
        &old_binding,
        &row(INDEX),
        intent("literal-source-drift"),
        &Cancellation::default(),
    )
    .unwrap();
    // Explicit hostile diagnostic mutation, not altered accepted Core history.
    // LEFT was clicked; RIGHT must nevertheless be refreshed before any writes.
    let cp = checkpoint(&source, "right", INDEX);
    let mut changed = value(&cp);
    changed["row"]["input_semantic_sha256"] = json!("0".repeat(64));
    write(&cp, &changed);
    expected.insert(
        cp.strip_prefix(&source).unwrap().to_owned(),
        Some(fs::read(&cp).unwrap()),
    );
    let target = root("source-drift-output").join("must-not-exist");
    refusal(selected_v2::run_selected(
        plan,
        &target,
        &Cancellation::default(),
    ));
    assert!(!target.exists());
    assert_eq!(inventory(&source), expected);
    refusal(selected_v2::prepare_selected(
        &source,
        &old_binding,
        &row(INDEX),
        intent("literal-corrupt-source"),
        &Cancellation::default(),
    ));
    assert_eq!(inventory(&source), expected);
}

#[test]
fn lost_actual_committed_checkpoint_recovers_without_new_role_evidence_or_commit() {
    let source = copied(&sources().paired, "recovery");
    let files = inventory(&source);
    let target = root("recovery-output").join("selected");
    let report = run(&source, &target, INDEX, "literal-selected-recovery");
    let left = engine(&only_database(&target, "left"));
    let right = engine(&only_database(&target, "right"));
    let work = |files: Inventory| -> Inventory {
        files
            .into_iter()
            .filter(|(p, _)| {
                p.file_name().is_some_and(|n| {
                    let n = n.to_string_lossy();
                    n.starts_with("admission-")
                        || n.starts_with("raw-")
                        || n.contains("-capture")
                        || n.contains("-recording")
                })
            })
            .collect()
    };
    let before_work = work(inventory(&target));
    fs::remove_file(checkpoint(&target, "left", INDEX)).unwrap();
    let recovered = serde_json::to_value(
        selected_v2::resume_selected(
            &target,
            &source,
            report["binding"].as_str().unwrap(),
            &Cancellation::default(),
        )
        .unwrap(),
    )
    .unwrap();
    let row = actual_row(&recovered, "left");
    assert_eq!(row["recovered_without_checkpoint"], true);
    assert_eq!(row["roles_known"], false);
    assert_eq!(row["passed"], false);
    assert_eq!(row["construction_evidence_status"], "unavailable");
    for key in [
        "literal_source_units",
        "literal_selected_start",
        "literal_selected_units",
        "role_metrics",
    ] {
        assert!(row[key].is_null());
    }
    assert_eq!(
        row["actual_receipt_sha256"],
        actual_row(&report, "left")["actual_receipt_sha256"]
    );
    assert_eq!(
        actual_row(&recovered, "right"),
        actual_row(&report, "right")
    );
    assert_eq!(work(inventory(&target)), before_work);
    assert_eq!(
        engine(&only_database(&target, "left")).receipts(),
        left.receipts()
    );
    assert_eq!(
        engine(&only_database(&target, "right")).receipts(),
        right.receipts()
    );
    assert_eq!(inventory(&source), files);
}

#[test]
fn missing_real_guard_terminal_and_store_checkpoint_disagreement_refuse_without_retry() {
    let source = copied(&sources().rollout, "terminal");
    let source_files = inventory(&source);
    let target = root("guard-output").join("selected");
    let report = run(&source, &target, GUARD, "literal-selected-guard");
    for arm in ["left", "right"] {
        let row = actual_row(&report, arm);
        assert_eq!(row["error"], "Inventory");
        assert_eq!(row["roles"], 0);
        let mut store = Store::open_read_only(&only_database(&target, arm)).unwrap();
        let actual = store
            .lookup_turn(
                &frozen_suite().unwrap().seed().scope,
                frozen_suite().unwrap().steps()[GUARD].id(),
            )
            .unwrap();
        assert_eq!(actual.phase, TurnPhase::Failed);
        assert!(actual.receipt.is_none());
    }
    fs::remove_file(checkpoint(&target, "left", GUARD)).unwrap();
    let expected = inventory(&target);
    assert_eq!(
        refusal(selected_v2::resume_selected(
            &target,
            &source,
            report["binding"].as_str().unwrap(),
            &Cancellation::default()
        )),
        "TerminalCheckpointMissing"
    );
    assert_eq!(inventory(&target), expected);
    let accepted = root("disagreement-output").join("selected");
    let report = run(&source, &accepted, INDEX, "literal-outcome-conflict");
    let cp = checkpoint(&accepted, "right", INDEX);
    let mut false_diagnostic = value(&cp);
    false_diagnostic["row"]["phase"] = json!("failed");
    write(&cp, &false_diagnostic);
    let expected = inventory(&accepted);
    refusal(selected_v2::inspect_selected(&accepted));
    refusal(selected_v2::resume_selected(
        &accepted,
        &source,
        report["binding"].as_str().unwrap(),
        &Cancellation::default(),
    ));
    assert_eq!(inventory(&accepted), expected);
    assert_eq!(inventory(&source), source_files);
}

#[test]
fn closed_versions_descriptors_cancel_and_unavailable_native_lane_never_authorize_work() {
    let source = copied(&sources().paired, "refusal");
    let files = inventory(&source);
    let source_binding = binding(&source);
    let cancelled = Cancellation::default();
    cancelled.cancel();
    refusal(selected_v2::prepare_selected(
        &source,
        &source_binding,
        &row(INDEX),
        intent("cancelled-prepare"),
        &cancelled,
    ));
    let plan = selected_v2::prepare_selected(
        &source,
        &source_binding,
        &row(INDEX),
        intent("cancelled-run"),
        &Cancellation::default(),
    )
    .unwrap();
    let cancelled_target = root("cancelled-output").join("must-not-exist");
    refusal(selected_v2::run_selected(
        plan,
        &cancelled_target,
        &cancelled,
    ));
    assert!(!cancelled_target.exists());
    let native_plan = selected_v2::prepare_selected(
        &source,
        &source_binding,
        &row(INDEX),
        selected::SelectedIntent {
            client_id: "literal-native-denied".into(),
            lane: selected::SelectedLane::ApprovedNative,
        },
        &Cancellation::default(),
    );
    #[cfg(not(feature = "local-model"))]
    assert_eq!(refusal(native_plan), "SelectedNativeUnavailable");
    #[cfg(feature = "local-model")]
    drop(native_plan.unwrap()); // Preparation only; no assets or execution.
    refusal(selected::prepare_selected(
        &source,
        &source_binding,
        &row(INDEX),
        intent("old-selected1-denied"),
        &Cancellation::default(),
    ));
    assert_eq!(inventory(&source), files);
    let completed = root("manifest-output").join("selected");
    let report = run(&source, &completed, INDEX, "literal-manifest");
    for fault in 0..3 {
        let target = copied(&completed, "manifest-fault");
        let p = target.join("selected.json");
        let mut v = value(&p);
        match fault {
            0 => v["version"] = json!(1),
            1 => v["source_protocol_version"] = json!(2),
            _ => v["arms"][0]["prompt_version"] = json!("unsupported-copy"),
        };
        write(&p, &v);
        let expected = inventory(&target);
        refusal(selected_v2::inspect_selected(&target));
        refusal(selected_v2::resume_selected(
            &target,
            &source,
            report["binding"].as_str().unwrap(),
            &Cancellation::default(),
        ));
        assert_eq!(inventory(&target), expected);
    }
    assert_eq!(inventory(&source), files);
    // Both-arm exhaustion is Root's actual private-Ledger unit oracle. This
    // public API has no admission constructor; no resource files are fabricated.
}
