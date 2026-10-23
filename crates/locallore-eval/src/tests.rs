use super::*;
use std::{
    path::PathBuf,
    sync::atomic::{AtomicU64, Ordering},
};
static NEXT: AtomicU64 = AtomicU64::new(0);
pub(crate) struct Temp(pub(crate) PathBuf);
impl Temp {
    pub(crate) fn new() -> Self {
        let p = std::env::temp_dir().join(format!(
            "locallore-eval-{}-{}",
            std::process::id(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        fs::create_dir(&p).unwrap();
        Self(p)
    }
}
impl Drop for Temp {
    fn drop(&mut self) {
        fs::remove_dir_all(&self.0).unwrap();
    }
}
fn no_failed(report: &Report) {
    for case in &report.cases {
        assert_ne!(
            case.status,
            Status::Failed,
            "{}: {:?}",
            case.id,
            case.checks
                .iter()
                .filter(|c| c.status == Status::Failed)
                .collect::<Vec<_>>()
        );
    }
}

#[test]
fn builtin_shared_host_cases_and_scripted_production_context_pass() {
    let temp = Temp::new();
    let report = run_builtin(
        &temp.0.join("run"),
        false,
        None,
        &Cancellation::default(),
        32,
    )
    .unwrap();
    no_failed(&report);
    assert!(report.completed);
    assert_eq!(report.cases.len(), 12);
    assert_eq!(
        report
            .cases
            .iter()
            .filter(|c| c.status == Status::Passed)
            .count(),
        9
    );
    assert_eq!(
        report
            .cases
            .iter()
            .filter(|c| c.status == Status::Unsupported)
            .count(),
        3
    );
    let scripted = report
        .cases
        .iter()
        .find(|c| c.id == "scripted-production-gift")
        .unwrap();
    assert!(scripted
        .provider_requests
        .iter()
        .any(|r| r.role == "director"));
    assert!(scripted
        .provider_requests
        .iter()
        .any(|r| r.role == "narrator"));
    assert!(scripted
        .provider_requests
        .iter()
        .all(|r| r.prompt_sha256.len() == 64 && r.schema_sha256.len() == 64));
    assert!(!report.quality_accepted);
    assert!(report.model.is_none());
    assert_eq!(report.android_parity, "not_run");
}

#[test]
fn actual_compiler_omission_regression_fails_with_assertion_and_source_then_restores() {
    let temp = Temp::new();
    let suite = builtin().unwrap();
    let spec = suite
        .scenarios
        .iter()
        .find(|c| c.id == "old-promise-after-distractors")
        .unwrap();
    let bad = temp.0.join("omitted");
    fs::create_dir(&bad).unwrap();
    let failed = evaluate(spec, &bad, Fault::DropCompiler).unwrap();
    assert_eq!(failed.status, Status::Failed);
    let failure = failed
        .checks
        .iter()
        .find(|c| c.id == "old-obligation-target-0")
        .unwrap();
    assert_eq!(failure.stage, "retrieval");
    assert_eq!(failure.turn.as_deref(), Some("seed:lantern-quay-v1"));
    assert_eq!(failure.status, Status::Failed);
    assert_eq!(failure.expected["present"], true);
    assert_eq!(failure.actual["present"], false);
    println!(
        "INJECTED RETRIEVAL FAILURE {}",
        String::from_utf8(encode(failure).unwrap()).unwrap()
    );
    let restored = temp.0.join("restored");
    fs::create_dir(&restored).unwrap();
    let fixed = evaluate(spec, &restored, Fault::None).unwrap();
    assert_eq!(fixed.status, Status::Passed);
    println!("RESTORED RETRIEVAL scenario={} status=passed", fixed.id);
}

#[test]
fn dropped_director_forwarding_fails_even_when_actual_compiler_target_passes() {
    let temp = Temp::new();
    let suite = builtin().unwrap();
    let spec = suite
        .scenarios
        .iter()
        .find(|s| s.id == "scripted-production-gift")
        .unwrap();
    let bad = temp.0.join("dropped-forwarding");
    fs::create_dir(&bad).unwrap();
    let failed = evaluate(spec, &bad, Fault::DropForwarded).unwrap();
    assert_eq!(failed.status, Status::Failed);
    assert_eq!(
        failed
            .checks
            .iter()
            .find(|c| c.id == "gift-context-target-0")
            .unwrap()
            .status,
        Status::Passed
    );
    let failure = failed
        .checks
        .iter()
        .find(|c| c.id == "original-gift-0-prompt-targets")
        .unwrap();
    assert_eq!(failure.status, Status::Failed);
    assert_eq!(failure.stage, "retrieval");
    assert_eq!(failure.turn.as_deref(), Some("original-gift-0"));
    assert_eq!(failure.expected, json!([true]));
    assert_eq!(failure.actual, json!([false]));
    println!(
        "INJECTED FORWARDING FAILURE {}",
        String::from_utf8(encode(failure).unwrap()).unwrap()
    );
    let restored = temp.0.join("restored-forwarding");
    fs::create_dir(&restored).unwrap();
    let fixed = evaluate(spec, &restored, Fault::None).unwrap();
    assert_eq!(fixed.status, Status::Passed);
    println!("RESTORED FORWARDING scenario={} status=passed", fixed.id);
}

#[test]
fn boundary_resume_does_not_reexecute_or_double_count_a_completed_case() {
    let temp = Temp::new();
    let dir = temp.0.join("run");
    let first = run_builtin(&dir, false, None, &Cancellation::default(), 1).unwrap();
    assert!(!first.completed);
    assert_eq!(first.cases.len(), 1);
    let checkpoint = read(&dir.join("case-00.json"), MAX_CASE).unwrap();
    let resumed = run_builtin(&dir, true, None, &Cancellation::default(), 32).unwrap();
    no_failed(&resumed);
    assert!(resumed.completed);
    assert_eq!(resumed.cases.len(), 12);
    assert_eq!(
        checkpoint,
        read(&dir.join("case-00.json"), MAX_CASE).unwrap()
    );
    assert!(!dir.join("case-00-attempt-01").exists());
    let again = run_builtin(&dir, true, None, &Cancellation::default(), 32).unwrap();
    assert_eq!(
        encode(&resumed.cases).unwrap(),
        encode(&again.cases).unwrap()
    );
}

#[test]
fn cancellation_boundary_and_abandoned_case_start_a_fresh_isolated_attempt() {
    let temp = Temp::new();
    let dir = temp.0.join("run");
    let cancel = Cancellation::default();
    cancel.cancel();
    let paused = run_builtin(&dir, false, None, &cancel, 32).unwrap();
    assert!(paused.cancelled);
    assert!(paused.cases.is_empty());
    let abandoned = dir.join("case-00-attempt-00");
    fs::create_dir(&abandoned).unwrap();
    let sentinel = abandoned.join("synthetic.sqlite");
    fs::write(&sentinel, b"synthetic abandoned bytes - never reopen").unwrap();
    let resumed = run_builtin(&dir, true, None, &Cancellation::default(), 1).unwrap();
    no_failed(&resumed);
    assert_eq!(resumed.cases.len(), 1);
    assert!(dir.join("case-00-attempt-01").is_dir());
    assert_eq!(
        fs::read(sentinel).unwrap(),
        b"synthetic abandoned bytes - never reopen"
    );
}

#[test]
fn mismatched_future_or_tampered_checkpoint_fails_closed() {
    let temp = Temp::new();
    let dir = temp.0.join("run");
    run_builtin(&dir, false, None, &Cancellation::default(), 1).unwrap();
    let metadata = read(&dir.join("run.json"), 128 * 1024).unwrap();
    for key in ["version", "prompt_version", "suite_sha256"] {
        let mut value: Value = serde_json::from_slice(&metadata).unwrap();
        value[key] = json!("future-or-other");
        fs::write(dir.join("run.json"), encode(&value).unwrap()).unwrap();
        assert_eq!(
            run_builtin(&dir, true, None, &Cancellation::default(), 32)
                .err()
                .as_deref(),
            Some("CheckpointMismatch")
        );
    }
    fs::write(dir.join("run.json"), metadata).unwrap();
    let path = dir.join("case-00.json");
    let mut value: Value = serde_json::from_slice(&read(&path, MAX_CASE).unwrap()).unwrap();
    value["result"]["id"] = json!("tampered");
    fs::write(path, encode(&value).unwrap()).unwrap();
    assert_eq!(
        run_builtin(&dir, true, None, &Cancellation::default(), 32)
            .err()
            .as_deref(),
        Some("CheckpointIntegrity")
    );
}

#[test]
fn existing_destination_unknown_case_and_competing_owner_do_not_execute() {
    let temp = Temp::new();
    let dir = temp.0.join("run");
    assert_eq!(
        run_builtin(&dir, false, Some("unknown"), &Cancellation::default(), 32)
            .err()
            .as_deref(),
        Some("UnknownCase")
    );
    assert!(!dir.exists());
    let cancel = Cancellation::default();
    cancel.cancel();
    run_builtin(&dir, false, None, &cancel, 32).unwrap();
    assert_eq!(
        run_builtin(&dir, false, None, &cancel, 32).err().as_deref(),
        Some("OutputExists")
    );
    let lock = OpenOptions::new()
        .read(true)
        .write(true)
        .open(dir.join("run.lock"))
        .unwrap();
    lock.try_lock().unwrap();
    assert_eq!(
        run_builtin(&dir, true, None, &Cancellation::default(), 32)
            .err()
            .as_deref(),
        Some("RunBusy")
    );
    assert!(!dir.join("case-00.json").exists());
}

#[test]
fn invalid_or_future_suite_is_rejected_before_any_pipeline_execution() {
    let source = builtin().unwrap();
    for change in 0..4 {
        let mut suite = source.clone();
        match change {
            0 => suite.version = 99,
            1 => suite.synthetic = false,
            2 => suite.seed_sha256 = "bad".into(),
            _ => suite.scenarios[0].steps[0].repeat = 49,
        }
        assert!(validate(&suite).is_err());
    }
    let mut json: Value = serde_json::from_slice(SUITE).unwrap();
    json["unrecognized"] = json!(true);
    assert!(serde_json::from_value::<Suite>(json).is_err());
}

#[test]
fn readable_report_is_inert_and_output_budget_is_enforced() {
    let temp = Temp::new();
    let cancel = Cancellation::default();
    cancel.cancel();
    let mut report = run_builtin(&temp.0.join("run"), false, None, &cancel, 32).unwrap();
    report.cases.push(CaseResult {
        id: "synthetic-markup".into(),
        status: Status::Failed,
        checks: vec![Check {
            id: "quoted-text".into(),
            turn: None,
            stage: "runner".into(),
            status: Status::Failed,
            expected: Value::Null,
            actual: json!("<script>alert('x')</script><img src='https://invalid.example'>"),
        }],
        turns: vec![],
        provider_requests: vec![],
        unsupported: None,
    });
    publish_reports(&temp.0.join("run"), &report).unwrap();
    let html = fs::read_to_string(temp.0.join("run/report.html")).unwrap();
    assert!(!html.contains("<script>"));
    assert!(!html.contains("<img"));
    assert!(html.contains("&lt;script&gt;"));
    assert!(html.contains("default-src 'none'"));
    report.cases[0].checks[0].actual = json!("<".repeat(MAX_REPORT));
    assert_eq!(
        publish_reports(&temp.0.join("run"), &report)
            .err()
            .as_deref(),
        Some("ReportBudget")
    );
}
