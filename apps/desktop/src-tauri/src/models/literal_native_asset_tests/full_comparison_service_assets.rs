// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen against de959afe service API, before production. UNCOMPILED / UNRUN.
//! Four separate ignored Root opt-ins, never a blanket ignored-suite launch.
//! Initial allocation: paired1 and rollout1 only. Resume3/completed recovery
//! require separate Root admission and genuine fresh current-source service data.
//! No copying, relabelling, private raw output printing or artifact deletion.
use super::*;
use crate::{
    evaluation::{EvaluationManager, FullComparisonNativeResume, FullComparisonStart},
    lease::WindowLease,
};
use std::{cell::Cell, time::{Duration, Instant}};

struct RetainedService {
    _evaluation: Arc<EvaluationManager>,
    _models: Arc<ModelManager>,
    _lease: Arc<WindowLease>,
}
static RETAINED_SERVICES: Mutex<Vec<RetainedService>> = Mutex::new(Vec::new());

struct Service {
    root: PathBuf,
    evaluation: Arc<EvaluationManager>,
    models: Arc<ModelManager>,
    lease: Arc<WindowLease>,
    epoch: u64,
    retained: Cell<bool>,
}
impl Service {
    fn attach(root: PathBuf, models: Arc<ModelManager>) -> Self {
        assert!(!BLOCKED.load(Ordering::SeqCst), "prior actual owner unresolved");
        let evaluation = Arc::new(EvaluationManager::new(root.join("evaluations")));
        let lease = Arc::new(WindowLease::default());
        let epoch = lease.begin().unwrap();
        let service = Self { root, evaluation, models, lease, epoch, retained: Cell::new(false) };
        service.evaluation.catalog(&service.lease, epoch).unwrap();
        service
    }
    fn preserve(&self) {
        BLOCKED.store(true, Ordering::SeqCst);
        if !self.retained.replace(true) {
            RETAINED_SERVICES.lock().unwrap_or_else(|p| p.into_inner()).push(RetainedService {
                _evaluation: self.evaluation.clone(), _models: self.models.clone(), _lease: self.lease.clone(),
            });
        }
    }
    fn unresolved(&self) -> ! {
        self.preserve();
        panic!("actual full-comparison evaluation/model owners retained; later asset admission blocked");
    }
    fn done(&self, token: &str) -> Value {
        // Outer fixture scheduling only. Actual shared30min/arm, role/turn,
        // preparation and cleanup bounds are never changed by this wait.
        let until = Instant::now() + Duration::from_secs(3900);
        loop {
            let status = self.evaluation.full_comparison_status_native(&self.lease, self.epoch, true, token).unwrap();
            if status["cleanup_required"] == true || status["phase"] == "cleanup_required" {
                self.unresolved();
            }
            // Async terminal publication may precede the actual worker's last
            // instructions. Observe both owners without performing any cleanup.
            if status["running"] == false && self.evaluation.cleanup_complete() && self.models.cleanup_complete() {
                return status;
            }
            if Instant::now() >= until { self.unresolved(); }
            std::thread::sleep(Duration::from_millis(10));
        }
    }
    fn open(&self, run: &str) -> Value {
        let opened = self.evaluation.full_comparison_open_native(&self.lease, self.epoch, true, run).unwrap();
        self.done(opened["run_token"].as_str().unwrap())
    }
    fn work(&self, run: &str) -> PathBuf {
        self.root.join("comparison-evaluations").join(run).join("work")
    }
    fn inspect(&self, run: &str) -> ComparisonReportV3 {
        literal_v3::inspect_comparison(&self.work(run)).unwrap()
    }
    fn finish(&self, token: &str) {
        // These observations precede close_manager: no cleanup helper can turn
        // an unresolved actual return into a passing ownership assertion.
        if !self.evaluation.cleanup_complete() || !self.models.cleanup_complete() { self.unresolved(); }
        assert!(self.evaluation.cleanup_complete());
        assert!(self.models.cleanup_complete());
        self.evaluation.full_comparison_close_native(&self.lease, self.epoch, false, token).unwrap();
        close_manager(&self.models); // already confirmed, therefore a no-op
    }
}
impl Drop for Service {
    fn drop(&mut self) {
        if self.retained.get() { return; }
        if !self.evaluation.cleanup_complete() || !self.models.cleanup_complete() {
            self.preserve();
            if !std::thread::panicking() { panic!("unresolved actual service owners retained"); }
            return;
        }
        if let Some(closed) = self.lease.invalidate(&format!("main-{}", self.epoch)) {
            self.evaluation.retire(self.epoch);
            self.evaluation.drain(self.epoch);
            self.lease.finish_close(closed, || {});
        }
    }
}
fn native_status(value: &Value, scenes: usize, completed: bool) {
    assert_eq!(value["version"], 2);
    assert_eq!(value["protocol_version"], 3);
    assert_eq!(value["input_lane"], "approved_native");
    assert_eq!(value["running"], false);
    assert_eq!(value["cleanup_required"], false);
    assert_eq!(value["cleanup_running"], false);
    assert_eq!(value["error"], Value::Null);
    assert_eq!(value["report_ready"], true);
    assert_eq!(value["source_matches"], true);
    assert_eq!(value["completed_scenes"], scenes);
    assert_eq!(value["completed"], completed);
}
fn actual_native(report: &ComparisonReportV3, scenes: usize, completed: bool) {
    assert_eq!(report.version, 3);
    assert_eq!(report.lane, "native_literal_relevant_comparison");
    assert_eq!((report.completed_scenes, report.turns.len(), report.completed), (scenes, scenes * 12, completed));
    assert!(report.source_matches);
    assert!(report.physical_setups > 0);
    assert!(report.native_load.as_ref().is_some_and(|v| v.as_array().is_some_and(|a| !a.is_empty())));
    assert!(report.turns.iter().any(|row| row.roles > 0 && !row.raw_sha256.is_empty()));
    assert_eq!(report.human_reviewed, 0);
    assert!(!report.quality_accepted);
    assert_eq!(report.profile.id, locallore_local_runtime::PROFILE);
    assert_eq!(report.profile.model_sha256, locallore_local_runtime::MODEL_SHA256);
    assert_eq!(report.profile.runtime_revision, locallore_local_runtime::RUNTIME_COMMIT);
    assert_eq!((report.profile.context_tokens, report.profile.director_tokens, report.profile.narrator_tokens), (4096, 350, 350));
    assert_eq!((report.profile.deadline_ms, report.profile.repair_limit), (120_000, 1));
    // Actual failed/guard/dependency/quality outcomes remain in the report.
    // This never asserts every row passed or that prose quality was accepted.
}
fn fresh(kind: ComparisonKind, label: &str) {
    let models = manager();
    let service = Service::attach(root(), models);
    println!("LOCALLORE_FULL_NATIVE_TEST_ROOT={}", service.root.display());
    let sequence = service.models.inner.lock().unwrap().evaluation_sequence;
    let calls = Arc::new(AtomicUsize::new(0));
    let consent = calls.clone();
    let started = service.evaluation.full_comparison_start_native(
        &service.lease, &service.models, service.epoch, true,
        FullComparisonStart { client_id: exports::identifier().unwrap(), kind, max_new_scenes: 1 },
        move |_| { consent.fetch_add(1, Ordering::SeqCst); Ok(true) },
    ).unwrap();
    println!("LOCALLORE_FULL_NATIVE_TEST_RUN_ID={}", started["run_id"].as_str().unwrap());
    let token = started["run_token"].as_str().unwrap();
    let done = service.done(token);
    native_status(&done, 1, false);
    assert_eq!(calls.load(Ordering::SeqCst), 1);
    assert_eq!(service.models.inner.lock().unwrap().evaluation_sequence, sequence.checked_add(1).unwrap());
    let run = done["run_id"].as_str().unwrap();
    let actual = service.inspect(run);
    assert_eq!(actual.kind, kind);
    actual_native(&actual, 1, false);
    assert_eq!(actual.physical_setups, 1);
    summary(label, &actual);
    service.finish(token);
}
fn existing() -> (PathBuf, String) {
    assert!(!BLOCKED.load(Ordering::SeqCst), "prior actual owner unresolved");
    let root = PathBuf::from(std::env::var_os("LOCALLORE_FULL_NATIVE_TEST_ROOT").expect("explicit genuine service root required"));
    let run = std::env::var("LOCALLORE_FULL_NATIVE_TEST_RUN_ID").expect("explicit genuine service run required");
    assert!(root.is_absolute() && root.is_dir());
    assert!(run.len() == 36 && run.bytes().enumerate().all(|(i, b)| {
        if [8, 13, 18, 23].contains(&i) { b == b'-' } else { b.is_ascii_digit() || (b'a'..=b'f').contains(&b) }
    }));
    assert!(root.join("comparison-evaluations").join(&run).join("desktop.json").is_file());
    // Public service validation still owns index/source/lane integrity. The
    // ENV never invents a default historical fixture or copies a source tree.
    (root, run)
}

#[test]
#[ignore = "Root explicit approved asset invocation1: fresh native service paired batch1 only"]
fn approved_service_paired_first_scene_returns_with_actual_owners_drained() {
    let _serial = SERIAL.lock().unwrap_or_else(|p| p.into_inner());
    fresh(ComparisonKind::PairedSnapshots, "service-paired-first");
}

#[test]
#[ignore = "Root explicit approved asset invocation2: fresh native service rollout batch1 only"]
fn approved_service_rollout_first_scene_returns_with_actual_owners_drained() {
    let _serial = SERIAL.lock().unwrap_or_else(|p| p.into_inner());
    fresh(ComparisonKind::ContinuousRollout, "service-rollout-first");
}

#[test]
#[ignore = "NOT initially allocated: separate Root launch and genuine current-source paired partial service root/run required"]
fn approved_existing_service_paired_partial_explicit_resume_three_completes() {
    let _serial = SERIAL.lock().unwrap_or_else(|p| p.into_inner());
    let (root, run) = existing();
    let service = Service::attach(root, manager());
    let opened = service.open(&run);
    native_status(&opened, 1, false);
    let before = service.inspect(&run);
    assert_eq!(before.kind, ComparisonKind::PairedSnapshots);
    actual_native(&before, 1, false);
    let token = opened["run_token"].as_str().unwrap().to_owned();
    let reference_before = inventory(&service.root.join("comparison-evaluations").join(&run).join("reference-source"));
    let calls = Arc::new(AtomicUsize::new(0));
    let consent = calls.clone();
    service.evaluation.full_comparison_resume_native(
        &service.lease, &service.models, service.epoch, true,
        FullComparisonNativeResume { run_token: token.clone(), max_new_scenes: 3 },
        move |_| { consent.fetch_add(1, Ordering::SeqCst); Ok(true) },
    ).unwrap();
    let done = service.done(&token);
    native_status(&done, 4, true);
    assert_eq!(calls.load(Ordering::SeqCst), 1);
    let actual = service.inspect(&run);
    actual_native(&actual, 4, true);
    assert_eq!(actual.kind, before.kind);
    assert!(inventory(&service.root.join("comparison-evaluations").join(&run).join("reference-source")) == reference_before);
    summary("service-paired-resume-three", &actual);
    service.finish(&token);
}

#[test]
#[ignore = "NOT initially allocated: separate Root launch and genuine fresh completed native service root/run required; empty Models assets"]
fn genuine_completed_service_resume_has_zero_consent_reservation_and_byte_changes() {
    let _serial = SERIAL.lock().unwrap_or_else(|p| p.into_inner());
    let (root, run) = existing();
    let before = inventory(&root);
    let empty = super::root();
    let empty_models = empty.join("empty-models");
    let empty_resources = empty.join("empty-resources");
    fs::create_dir(&empty_models).unwrap();
    fs::create_dir(&empty_resources).unwrap();
    assert_eq!(fs::read_dir(&empty_models).unwrap().count(), 0);
    assert_eq!(fs::read_dir(&empty_resources).unwrap().count(), 0);
    let models = Arc::new(ModelManager::new(empty_models, empty_resources));
    let sequence = models.inner.lock().unwrap().evaluation_sequence;
    let service = Service::attach(root, models.clone());
    let opened = service.open(&run);
    native_status(&opened, 4, true);
    let original = service.inspect(&run);
    actual_native(&original, 4, true);
    let token = opened["run_token"].as_str().unwrap().to_owned();
    let calls = Arc::new(AtomicUsize::new(0));
    let consent = calls.clone();
    service.evaluation.full_comparison_resume_native(
        &service.lease, &models, service.epoch, true,
        FullComparisonNativeResume { run_token: token.clone(), max_new_scenes: 1 },
        move |_| { consent.fetch_add(1, Ordering::SeqCst); Ok(false) },
    ).unwrap();
    native_status(&service.done(&token), 4, true);
    assert_eq!(calls.load(Ordering::SeqCst), 0);
    assert_eq!(models.inner.lock().unwrap().evaluation_sequence, sequence);
    assert_eq!(service.inspect(&run), original);
    summary("service-completed-zero-reservation", &original);
    service.finish(&token);
    assert!(inventory(&service.root) == before);
}
