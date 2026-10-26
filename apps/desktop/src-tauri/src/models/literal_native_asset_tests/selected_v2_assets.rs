// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! One ignored approved-assets gate. SOURCE ONLY / UNCOMPILED / UNRUN.
//! Actual desktop manager + native selected2 Rust API, never UI/IPC/WebView,
//! generation quality, performance qualification or rerun-until-success.
use super::*;
use locallore_eval::{
    local_lane::{
        comparison::{
            desktop_api::{Arm, RowId},
            literal_v3::selected_v2,
            selected::{SelectedIntent, SelectedLane},
        },
        LaneFactory,
    },
    memory_comparison::frozen_suite,
};
use locallore_storage::Store;

const INDEX: usize = 4;
fn selected_database(target: &Path, arm: &str) -> PathBuf {
    let found: Vec<_> = fs::read_dir(target.join(arm))
        .unwrap()
        .map(|e| e.unwrap().path())
        .filter(|p| p.extension().is_some_and(|s| s == "sqlite"))
        .collect();
    assert_eq!(found.len(), 1);
    found[0].clone()
}
fn canonical(target: &Path, arm: &str) -> locallore::engine::Engine {
    Store::open_read_only(&selected_database(target, arm))
        .unwrap()
        .resume(&frozen_suite().unwrap().seed().scope)
        .unwrap()
        .engine
}
fn frozen_role_and_setup_files(files: Inventory) -> Inventory {
    files
        .into_iter()
        .filter(|(p, _)| {
            p.file_name().is_some_and(|n| {
                let n = n.to_string_lossy();
                n.starts_with("setup-")
                    || n.starts_with("admission-")
                    || n.starts_with("raw-")
                    || n.contains("-capture")
                    || n.contains("-recording")
            })
        })
        .collect()
}
fn selected_summary(stage: &str, report: &Value) {
    let rows = report["rows"].as_array().unwrap();
    let mut phases: BTreeMap<String, usize> = BTreeMap::new();
    let mut failures: BTreeMap<String, usize> = BTreeMap::new();
    let mut fallbacks = 0;
    let mut roles = 0;
    for row in rows {
        *phases
            .entry(row["phase"].as_str().unwrap().to_owned())
            .or_default() += 1;
        for failure in row["failures"].as_array().unwrap() {
            *failures
                .entry(failure.as_str().unwrap().to_owned())
                .or_default() += 1;
        }
        fallbacks += usize::from(row["fallback"] == true);
        roles += row["roles"].as_u64().unwrap();
    }
    assert!(phases.len() <= 8 && failures.len() <= 32);
    println!(
        "LOCALLORE_LITERAL_SELECTED2_NATIVE_SUMMARY={}",
        json!({"stage":stage,"rows":rows.len(),"completed":report["completed"],"phases":phases,"failures":failures,"roles":roles,"fallbacks":fallbacks,"physical_setups":report["physical_setups"],"human_reviewed":report["human_reviewed"],"quality_accepted":report["quality_accepted"]})
    );
}
fn resume_without_assets(
    manager: &Arc<ModelManager>,
    target: &Path,
    source: &Path,
    binding: &str,
    callbacks: &AtomicUsize,
) -> Value {
    let result = selected_v2::resume_native_selected::<EvaluationReservation>(
        target,
        source,
        binding,
        &Cancellation::default(),
        || {
            callbacks.fetch_add(1, Ordering::SeqCst);
            Err("Provider".into())
        },
    );
    match result {
        Ok(report) => {
            let drained_on_return = manager.cleanup_complete();
            close_manager(manager);
            assert!(
                drained_on_return,
                "model-free resume must return with manager ownership drained"
            );
            serde_json::to_value(report).unwrap()
        }
        Err(error) => {
            let code = dispose_failure(manager, None, error);
            panic!("model-free selected2 resume failed with fixed code {code}");
        }
    }
}

#[test]
#[ignore = "requires explicitly approved installed model/resources; one serial Root opt-in"]
fn approved_selected2_move_records_outcomes_and_zero_asset_recovery() {
    let _serial = SERIAL.lock().unwrap_or_else(|p| p.into_inner());
    let manager = manager();
    let root = root();
    let source = root.join("scripted-v3-source");
    let produced = literal_v3::run_comparison(
        &source,
        false,
        ComparisonKind::ContinuousRollout,
        &Cancellation::default(),
        1,
        LaneFactory::ScriptedBaseline,
        None,
    )
    .unwrap();
    assert_eq!((produced.completed_scenes, produced.turns.len()), (1, 12));
    let source_before = inventory(&source);
    let opened = literal_v3::desktop_api::open_read_only(&source).unwrap();
    let source_summary = literal_v3::desktop_api::summary(&opened, true).unwrap();
    let source_binding = source_summary["binding"].as_str().unwrap().to_owned();
    drop(opened);
    let suite = frozen_suite().unwrap();
    assert_eq!(suite.steps()[INDEX].text(), "I move to pier.");
    let plan = selected_v2::prepare_selected(
        &source,
        &source_binding,
        &RowId {
            turn: suite.steps()[INDEX].id().into(),
            arm: Arm::Left,
        },
        SelectedIntent {
            client_id: "approved-selected2-native-move".into(),
            lane: SelectedLane::ApprovedNative,
        },
        &Cancellation::default(),
    )
    .unwrap();
    let target = root.join("native-selected2");
    let witness = Mutex::new(None);
    let first_callbacks = AtomicUsize::new(0);
    let result = selected_v2::run_native_selected(plan, &target, &Cancellation::default(), || {
        first_callbacks.fetch_add(1, Ordering::SeqCst);
        let reservation = manager.reserve_evaluation()?;
        *witness.lock().unwrap() = Some(reservation.cleanup_witness());
        Ok(reservation)
    });
    let report = match result {
        Ok(report) => {
            let drained_on_return = manager.cleanup_complete();
            close_manager(&manager);
            assert!(
                drained_on_return,
                "successful native selected2 must drain ownership before returning"
            );
            serde_json::to_value(report).unwrap()
        }
        Err(error) => {
            let code = dispose_failure(&manager, witness.into_inner().unwrap(), error);
            panic!("approved native selected2 returned fixed code {code}");
        }
    };
    selected_summary("native-move-all-outcomes", &report);
    assert_eq!(first_callbacks.load(Ordering::SeqCst), 1);
    assert_eq!(report["version"], 2);
    assert_eq!(report["source_protocol_version"], 3);
    assert_eq!(report["completed"], true);
    assert_eq!(report["physical_setups"], 1);
    assert_eq!(report["source_native"], false);
    assert_eq!(report["lane"], "native_selected_case");
    assert!(report["native_load"]
        .as_array()
        .is_some_and(|a| a.len() == 1 && a[0].is_object()));
    assert_eq!(report["human_reviewed"], 0);
    assert_eq!(report["quality_accepted"], false);
    let rows = report["rows"].as_array().unwrap();
    assert_eq!(rows.len(), 2);
    let mut calls = 0;
    for (n, arm) in ["left", "right"].iter().enumerate() {
        let row = &rows[n];
        assert_eq!(row["arm"], *arm);
        assert_eq!(row["turn"], suite.steps()[INDEX].id());
        assert_eq!(row["roles_known"], true);
        assert_eq!(row["recovered_without_checkpoint"], false);
        let roles = row["roles"].as_u64().unwrap();
        assert!((1..=3).contains(&roles));
        calls += roles;
        assert!(!row["raw_sha256"].as_array().unwrap().is_empty());
    }
    assert!((1..=6).contains(&calls));
    assert_eq!(inventory(&source), source_before);
    assert!(manager.cleanup_complete());
    // At least one REAL accepted result is required for this recovery gate.
    // Other refusals/scenario failures remain in the report; no all-pass or
    // human quality assertion, input rewriting or repeat-until-win is permitted.
    let committed = rows
        .iter()
        .find(|r| r["phase"] == "committed")
        .expect("native accepted-result/recovery gate requires an actual commit")
        .clone();
    let arm = committed["arm"].as_str().unwrap().to_owned();
    let other_arm = if arm == "left" { "right" } else { "left" };
    let other_original = rows.iter().find(|r| r["arm"] == other_arm).unwrap().clone();
    let binding = report["binding"].as_str().unwrap();
    let target_before = inventory(&target);
    let no_assets = AtomicUsize::new(0);
    let repeated = resume_without_assets(&manager, &target, &source, binding, &no_assets);
    assert_eq!(repeated, report);
    assert_eq!(no_assets.load(Ordering::SeqCst), 0);
    assert_eq!(inventory(&target), target_before);
    assert_eq!(inventory(&source), source_before);
    let original_canon: Vec<_> = ["left", "right"]
        .iter()
        .map(|arm| canonical(&target, arm))
        .collect();
    let original_work = frozen_role_and_setup_files(inventory(&target));
    let lost = target.join(&arm).join(format!("attempt-{INDEX:02}.json"));
    assert!(lost.is_file());
    fs::remove_file(&lost).unwrap();
    let recovered = resume_without_assets(&manager, &target, &source, binding, &no_assets);
    selected_summary("committed-workflow-checkpoint-loss", &recovered);
    assert_eq!(no_assets.load(Ordering::SeqCst), 0);
    assert_eq!(recovered["physical_setups"], report["physical_setups"]);
    assert_eq!(recovered["native_load"], report["native_load"]);
    assert_eq!(recovered["completed"], true);
    let recovery_rows = recovered["rows"].as_array().unwrap();
    let recovered_row = recovery_rows.iter().find(|r| r["arm"] == arm).unwrap();
    assert_eq!(
        recovered_row["actual_receipt_sha256"],
        committed["actual_receipt_sha256"]
    );
    assert_eq!(recovered_row["phase"], "committed");
    assert_eq!(recovered_row["roles_known"], false);
    assert_eq!(recovered_row["recovered_without_checkpoint"], true);
    assert_eq!(recovered_row["construction_evidence_status"], "unavailable");
    assert_eq!(recovered_row["passed"], false);
    assert_eq!(recovered_row["context_evidence_available"], false);
    for key in [
        "literal_source_units",
        "literal_selected_start",
        "literal_selected_units",
        "role_metrics",
        "capture_sha256",
        "recording_sha256",
    ] {
        assert!(recovered_row[key].is_null());
    }
    assert_eq!(
        recovery_rows
            .iter()
            .find(|r| r["arm"] == other_arm)
            .unwrap(),
        &other_original
    );
    assert_eq!(
        frozen_role_and_setup_files(inventory(&target)),
        original_work
    );
    for (n, arm) in ["left", "right"].iter().enumerate() {
        let current = canonical(&target, arm);
        assert_eq!(current.receipts(), original_canon[n].receipts());
        assert_eq!(
            current.canonical_bytes(),
            original_canon[n].canonical_bytes()
        );
    }
    let recovered_before = inventory(&target);
    let final_read = resume_without_assets(&manager, &target, &source, binding, &no_assets);
    assert_eq!(final_read, recovered);
    assert_eq!(no_assets.load(Ordering::SeqCst), 0);
    assert_eq!(inventory(&target), recovered_before);
    assert_eq!(inventory(&source), source_before);
    assert!(manager.cleanup_complete());
    // Removed only actual workflow metadata after real native commit. Missing
    // capture/role knowledge is not reconstructed as successful native evidence.
    // This Rust/desktop-owner test does not qualify UI/IPC, model prose or RAM.
}
