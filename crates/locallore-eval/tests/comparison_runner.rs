//! Frozen actual shared-pipeline oracles; synthetic provider, never a real-model claim.
use locallore::inference::Cancellation;
use locallore_eval::local_lane::{comparison::*, LaneFactory};
use serde_json::Value;
use std::path::{Path, PathBuf};

fn root(name: &str) -> PathBuf {
    let p = std::env::temp_dir().join(format!(
        "locallore-comparison-{name}-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    std::fs::create_dir(&p).unwrap();
    p
}
fn snapshot(dir: &Path) -> Vec<(PathBuf, Vec<u8>)> {
    let mut result = Vec::new();
    let mut paths: Vec<_> = std::fs::read_dir(dir)
        .unwrap()
        .map(|e| e.unwrap().path())
        .collect();
    paths.sort();
    for p in paths {
        if p.is_dir() {
            result.extend(snapshot(&p));
        } else {
            result.push((p.clone(), std::fs::read(p).unwrap()));
        }
    }
    result
}
#[test]
fn scripted_reference_is_actual_21_accepted_3_guard_and_reopens_without_rewrite() {
    let p = root("reference").join("reference");
    let report = prepare_reference(&p, &Cancellation::default()).unwrap();
    assert_eq!(report.accepted, 21);
    assert_eq!(report.guard_only, 3);
    assert_eq!(report.roles, 42);
    assert_eq!(report.turns.len(), 24);
    assert!(report.turns.iter().all(|t| t.passed));
    let before = snapshot(&p);
    let checked = open_reference(&p).unwrap();
    assert_eq!(checked.report(), &report);
    assert_eq!(snapshot(&p), before);
    assert!(prepare_reference(&p, &Cancellation::default()).is_err());
    assert_eq!(snapshot(&p), before);
}
#[test]
fn actual_paired_snapshots_use_same_reference_input_but_record_both_real_policies() {
    let p = root("paired");
    prepare_reference(&p.join("reference"), &Cancellation::default()).unwrap();
    let reference = open_reference(&p.join("reference")).unwrap();
    let report = run_comparison(
        &p.join("run"),
        false,
        ComparisonKind::PairedSnapshots,
        &Cancellation::default(),
        1,
        LaneFactory::ScriptedBaseline,
        Some(&reference),
    )
    .unwrap();
    assert_eq!(report.completed_scenes, 1);
    assert_eq!(report.turns.len(), 12);
    assert!(!report.completed);
    assert!(report
        .turns
        .iter()
        .all(|t| t.passed && t.policy_matches && t.context_evidence_available));
    for pair in report.turns.chunks_exact(2) {
        assert_eq!(pair[0].input_semantic_sha256, pair[1].input_semantic_sha256);
        assert_ne!(pair[0].policy, pair[1].policy);
    }
    assert_eq!(report.human_reviewed, 0);
    assert!(!report.quality_accepted);
    assert_eq!(report.human_rubric, "not_reviewed");
    assert_eq!(report.physical_setups, 0); // scripted has no native asset load
    let bytes = std::fs::read(p.join("run/report.html")).unwrap();
    assert!(!String::from_utf8(bytes).unwrap().contains("<script"));
}
#[test]
fn rollout_resume_finishes_each_actual_chain_and_completed_resume_has_no_invocation() {
    let p = root("rollout").join("run");
    let first = run_comparison(
        &p,
        false,
        ComparisonKind::ContinuousRollout,
        &Cancellation::default(),
        1,
        LaneFactory::ScriptedBaseline,
        None,
    )
    .unwrap();
    assert_eq!(first.completed_scenes, 1);
    assert_eq!(first.turns.len(), 12);
    let done = run_comparison(
        &p,
        true,
        ComparisonKind::ContinuousRollout,
        &Cancellation::default(),
        4,
        LaneFactory::ScriptedBaseline,
        None,
    )
    .unwrap();
    assert!(done.completed);
    assert_eq!(done.turns.len(), 48);
    assert!(done.turns.iter().all(|t| t.passed));
    assert_eq!(done.turns.iter().map(|t| t.roles).sum::<usize>(), 84);
    let before = snapshot(&p);
    let reopened = run_comparison(
        &p,
        true,
        ComparisonKind::ContinuousRollout,
        &Cancellation::default(),
        4,
        LaneFactory::ScriptedBaseline,
        None,
    )
    .unwrap();
    assert_eq!(reopened, done);
    assert_eq!(snapshot(&p), before);
}
#[test]
fn inspect_is_read_only_and_source_drift_is_viewable_but_not_resumable() {
    let p = root("drift").join("run");
    run_comparison(
        &p,
        false,
        ComparisonKind::ContinuousRollout,
        &Cancellation::default(),
        1,
        LaneFactory::ScriptedBaseline,
        None,
    )
    .unwrap();
    let path = p.join("run.json");
    let mut value: Value = serde_json::from_slice(&std::fs::read(&path).unwrap()).unwrap();
    value["source_sha256"] = Value::String("0".repeat(64));
    std::fs::write(&path, serde_json::to_vec(&value).unwrap()).unwrap();
    let before = snapshot(&p);
    let inspected = inspect_comparison(&p).unwrap();
    assert!(!inspected.source_matches);
    assert_eq!(snapshot(&p), before);
    assert!(run_comparison(
        &p,
        true,
        ComparisonKind::ContinuousRollout,
        &Cancellation::default(),
        1,
        LaneFactory::ScriptedBaseline,
        None
    )
    .is_err());
    assert_eq!(snapshot(&p), before);
}
#[test]
fn pre_cancelled_run_never_opens_reference_or_admits_provider_work() {
    let p = root("cancel").join("run");
    let cancel = Cancellation::default();
    cancel.cancel();
    assert!(run_comparison(
        &p,
        false,
        ComparisonKind::ContinuousRollout,
        &cancel,
        1,
        LaneFactory::ScriptedBaseline,
        None
    )
    .is_err());
    assert!(!p.exists());
}
#[test]
fn reference_source_tamper_is_not_authenticated_by_resealing_a_digest() {
    let p = root("reference-tamper").join("reference");
    prepare_reference(&p, &Cancellation::default()).unwrap();
    let path = p.join("reference.json");
    let mut v: Value = serde_json::from_slice(&std::fs::read(&path).unwrap()).unwrap();
    v["turns"][0]["input_semantic_sha256"] = Value::String("0".repeat(64));
    std::fs::write(&path, serde_json::to_vec(&v).unwrap()).unwrap();
    let before = snapshot(&p);
    assert!(open_reference(&p).is_err());
    assert_eq!(snapshot(&p), before);
}
#[test]
fn retained_actual_context_tamper_or_loss_never_becomes_a_privacy_pass() {
    let p = root("capture-tamper").join("run");
    run_comparison(
        &p,
        false,
        ComparisonKind::ContinuousRollout,
        &Cancellation::default(),
        1,
        LaneFactory::ScriptedBaseline,
        None,
    )
    .unwrap();
    let path = p.join("left/attempt-00-capture.json");
    let original = std::fs::read(&path).unwrap();
    let mut v: Value = serde_json::from_slice(&original).unwrap();
    v["data"]["details"]["identity"]["observer"] = Value::String("sable".into());
    std::fs::write(&path, serde_json::to_vec(&v).unwrap()).unwrap();
    assert!(inspect_comparison(&p).is_err());
    std::fs::write(&path, &original).unwrap();
    assert!(inspect_comparison(&p).is_ok());
    std::fs::remove_file(&path).unwrap();
    assert!(inspect_comparison(&p).is_err());
}
#[test]
fn committed_missing_ack_uses_actual_lookup_and_never_reopens_a_completed_role() {
    let p = root("lost-ack").join("run");
    run_comparison(
        &p,
        false,
        ComparisonKind::ContinuousRollout,
        &Cancellation::default(),
        1,
        LaneFactory::ScriptedBaseline,
        None,
    )
    .unwrap();
    // Synthetic interruption boundary: committed SQLite and private outputs exist,
    // but the final left checkpoint and not-yet-sealed scene acknowledgment do not.
    let db = std::fs::read(p.join("left/synthetic.sqlite")).unwrap();
    let before_ledger: Vec<_> = snapshot(&p.join("left"))
        .into_iter()
        .filter(|(path, _)| {
            path.file_name()
                .unwrap()
                .to_string_lossy()
                .starts_with("admission-")
        })
        .collect();
    std::fs::remove_file(p.join("left/attempt-05.json")).unwrap();
    std::fs::remove_file(p.join("scene-00.json")).unwrap();
    let report = run_comparison(
        &p,
        true,
        ComparisonKind::ContinuousRollout,
        &Cancellation::default(),
        1,
        LaneFactory::ScriptedBaseline,
        None,
    )
    .unwrap();
    let recovered = report
        .turns
        .iter()
        .find(|t| t.arm == "left" && t.turn == "courier-06")
        .unwrap();
    assert_eq!(recovered.phase, "committed");
    assert!(recovered.recovered_without_checkpoint);
    assert!(!recovered.roles_known);
    assert!(!recovered.passed);
    assert_eq!(std::fs::read(p.join("left/synthetic.sqlite")).unwrap(), db);
    let after_ledger: Vec<_> = snapshot(&p.join("left"))
        .into_iter()
        .filter(|(path, _)| {
            path.file_name()
                .unwrap()
                .to_string_lossy()
                .starts_with("admission-")
        })
        .collect();
    assert_eq!(after_ledger, before_ledger);
}

#[test]
fn removing_reserved_cost_or_changing_known_settlement_is_integrity_failure() {
    let p=root("ledger-tamper").join("run");
    run_comparison(&p,false,ComparisonKind::ContinuousRollout,&Cancellation::default(),1,LaneFactory::ScriptedBaseline,None).unwrap();
    let path=p.join("left/admission-00-settled.json");
    let original=std::fs::read(&path).unwrap();
    let mut v:Value=serde_json::from_slice(&original).unwrap();v["roles"]=Value::from(0);
    std::fs::write(&path,serde_json::to_vec(&v).unwrap()).unwrap();
    assert!(inspect_comparison(&p).is_err());
    std::fs::write(&path,&original).unwrap();
    assert!(inspect_comparison(&p).is_ok());
    std::fs::remove_file(p.join("left/admission-00.json")).unwrap();
    std::fs::remove_file(&path).unwrap();
    assert!(inspect_comparison(&p).is_err());
}
