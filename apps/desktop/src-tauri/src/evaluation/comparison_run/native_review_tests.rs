// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen BEFORE native service implementation at de959afe. UNCOMPILED / UNRUN.
//! Metadata fixtures are not canonical native outcomes. Protocol owners below
//! are genuine fixed test processes, NOT approved model/profile/generation proof.
//! Root: cargo test --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --bin locallore-desktop-spike evaluation::comparison_run::native_review_tests:: -- --nocapture --test-threads=1
use super::*;
use crate::{
    evaluation::{selected::SelectedOwnership, FullComparisonNativeResume},
    models::ModelManager,
};
use locallore_eval::local_lane::comparison::selected::SelectedNativeReservation;
use std::sync::{
    atomic::{AtomicUsize, Ordering},
    mpsc, OnceLock,
};

type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;
fn inventory(root: &Path) -> Inventory {
    fn walk(root: &Path, path: &Path, depth: usize, total: &mut usize, out: &mut Inventory) {
        assert!(depth <= 12 && out.len() < 8192);
        let m = fs::symlink_metadata(path).unwrap();
        assert!(!m.file_type().is_symlink());
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt;
            assert_eq!(m.file_attributes() & 0x400, 0);
        }
        let key = path.strip_prefix(root).unwrap().to_owned();
        if m.is_dir() {
            out.insert(key, None);
            for entry in fs::read_dir(path).unwrap() {
                walk(root, &entry.unwrap().path(), depth + 1, total, out);
            }
        } else {
            assert!(m.is_file() && m.len() <= 16 * 1024 * 1024);
            let bytes = fs::read(path).unwrap();
            *total += bytes.len();
            assert!(*total <= 128 * 1024 * 1024);
            out.insert(key, Some(bytes));
        }
    }
    let mut out = Inventory::new();
    walk(root, root, 0, &mut 0, &mut out);
    out
}
fn rejected<T>(result: Result<T>, code: &str) {
    match result {
        Err(error) => assert_eq!(error, code),
        Ok(_) => panic!("expected {code}"),
    }
}
fn cap(value: &Value) -> &str {
    value["run_token"].as_str().unwrap()
}
struct Fixture {
    manager: Arc<EvaluationManager>,
    models: Arc<ModelManager>,
    lease: Arc<WindowLease>,
    epoch: u64,
}
impl Fixture {
    fn new() -> Self {
        let root = std::env::temp_dir().join(format!("full-native-service-{}", uuid().unwrap()));
        fs::create_dir(&root).unwrap();
        let manager = Arc::new(EvaluationManager::new(root.join("evaluations")));
        let lease = Arc::new(WindowLease::default());
        let epoch = lease.begin().unwrap();
        manager.catalog(&lease, epoch).unwrap();
        Self {
            manager,
            models: Arc::new(ModelManager::new(
                root.join("models"),
                root.join("resources"),
            )),
            lease,
            epoch,
        }
    }
    fn root(&self) -> PathBuf {
        self.manager.root.with_file_name("comparison-evaluations")
    }
    fn input(client: &str) -> FullComparisonStart {
        FullComparisonStart {
            client_id: client.into(),
            kind: core::ComparisonKind::ContinuousRollout,
            max_new_scenes: 1,
        }
    }
    fn metadata(&self, native: bool, client: &str) -> String {
        // This is native-owned WRAPPER METADATA ONLY. There is no work/report,
        // copied NativeProfile, canonical Store, receipt or checkpoint to relabel.
        let run = uuid().unwrap();
        let path = self.root().join(&run);
        fs::create_dir_all(&path).unwrap();
        let value = json!({"version":if native{2}else{1},"protocol_version":3,"input_lane":if native{"approved_native"}else{"scripted_baseline"},"run_id":run,"client_id":client,"kind":"continuous_rollout","initial_batch":1,"created_ms":1,"binding":wire::current_binding(native).unwrap()});
        fs::write(
            path.join("desktop.json"),
            serde_json::to_vec(&value).unwrap(),
        )
        .unwrap();
        run
    }
    fn lookup(&self, client: &str) -> Value {
        self.manager
            .full_comparison_lookup_native(&self.lease, self.epoch, true, client)
            .unwrap()
    }
    fn done(&self, token: &str) -> Value {
        let end = Instant::now() + Duration::from_secs(180);
        loop {
            let value = self
                .manager
                .full_comparison_status_native(&self.lease, self.epoch, true, token)
                .unwrap();
            if value["running"] == false {
                return value;
            }
            assert!(
                Instant::now() < end,
                "native service fixture scheduling wait: {value}"
            );
            std::thread::sleep(Duration::from_millis(5));
        }
    }
    fn cleanup(&self) {
        self.manager
            .selected_retry_cleanup(&self.lease, &self.models, self.epoch)
            .unwrap();
        let end = Instant::now() + Duration::from_secs(30);
        loop {
            let value = self
                .manager
                .selected_cleanup_status(&self.lease, self.epoch)
                .unwrap();
            if value["running"] == false {
                assert_eq!(value["cleanup_required"], false);
                break;
            }
            assert!(Instant::now() < end);
            std::thread::sleep(Duration::from_millis(5));
        }
    }
}
impl Drop for Fixture {
    fn drop(&mut self) {
        let _ = self.manager.test_case("release-boundary");
        self.manager.retire(self.epoch);
        self.manager.drain(self.epoch);
        let _ = self.manager.selected_cleanup_retired(self.epoch);
        self.models.close(None, self.models.retire());
        let _ = self.manager.selected_cleanup_retired(self.epoch);
        if self.manager.cleanup_complete() && self.models.cleanup_complete() {
            if let Some(closed) = self.lease.invalidate(&format!("main-{}", self.epoch)) {
                self.lease.finish_close(closed, || {});
            }
        } else {
            // Test-only last-resort retention of the SAME actual managers/pair;
            // never drop an unconfirmed owner to make a failed assertion tidy.
            static HELD: OnceLock<
                Mutex<Vec<(Arc<EvaluationManager>, Arc<ModelManager>, Arc<WindowLease>)>>,
            > = OnceLock::new();
            HELD.get_or_init(|| Mutex::new(vec![]))
                .lock()
                .unwrap()
                .push((
                    self.manager.clone(),
                    self.models.clone(),
                    self.lease.clone(),
                ));
        }
    }
}
fn native_denied_source() -> &'static (PathBuf, String, String) {
    static SAVED: OnceLock<(PathBuf, String, String)> = OnceLock::new();
    SAVED.get_or_init(|| {
        let f = Fixture::new();
        let client = uuid().unwrap();
        let started = f
            .manager
            .full_comparison_start_native(
                &f.lease,
                &f.models,
                f.epoch,
                true,
                Fixture::input(&client),
                |_| Ok(false),
            )
            .unwrap();
        let done = f.done(cap(&started));
        assert_eq!(done["error"], "Cancelled");
        assert_eq!(done["report_ready"], false);
        let run = done["run_id"].as_str().unwrap().to_owned();
        let leaf = f.root().join(&run);
        // Actual shared provisional manifest emitted BEFORE its reserve callback;
        // no claim of native execution, roles, successful report or completion.
        assert!(leaf.join("work/run.json").is_file());
        f.manager
            .full_comparison_close_native(&f.lease, f.epoch, false, cap(&done))
            .unwrap();
        (leaf, run, client)
    })
}
fn copied_denial() -> (Fixture, String, String) {
    let f = Fixture::new();
    let (source, run, client) = native_denied_source();
    let original = inventory(source);
    let target = f.root().join(run);
    fs::create_dir_all(&target).unwrap();
    for (path, bytes) in &original {
        match bytes {
            None => fs::create_dir_all(target.join(path)).unwrap(),
            Some(bytes) => fs::write(target.join(path), bytes).unwrap(),
        }
    }
    assert!(inventory(&target) == original);
    (f, run.clone(), client.clone())
}

#[test]
fn validated_mixed_metadata_filters_lanes_without_rebinding_clients_or_rewriting_v1() {
    let f = Fixture::new();
    let s = uuid().unwrap();
    let n = uuid().unwrap();
    let sr = f.metadata(false, &s);
    let nr = f.metadata(true, &n);
    let before = inventory(&f.root());
    let old = f
        .manager
        .full_comparison_catalog(&f.lease, f.epoch, true)
        .unwrap();
    let native = f
        .manager
        .full_comparison_catalog_native(&f.lease, f.epoch, true)
        .unwrap();
    assert_eq!(old["version"], 1);
    assert_eq!(old["runs"].as_array().unwrap().len(), 1);
    assert_eq!(old["runs"][0]["run_id"], sr);
    assert_eq!(native["version"], 2);
    assert_eq!(native["input_lane"], "approved_native");
    assert_eq!(native["runs"].as_array().unwrap().len(), 1);
    assert_eq!(native["runs"][0]["run_id"], nr);
    let consent = Arc::new(AtomicUsize::new(0));
    let count = consent.clone();
    rejected(
        f.manager.full_comparison_start_native(
            &f.lease,
            &f.models,
            f.epoch,
            true,
            Fixture::input(&s),
            move |_| {
                count.fetch_add(1, Ordering::SeqCst);
                Ok(false)
            },
        ),
        "InvalidEvaluationInput",
    );
    rejected(
        f.manager
            .full_comparison_start(&f.lease, f.epoch, true, Fixture::input(&n)),
        "InvalidEvaluationInput",
    );
    assert_eq!(consent.load(Ordering::SeqCst), 0);
    assert!(inventory(&f.root()) == before);
}

#[test]
fn combined_thirty_two_run_cap_applies_to_both_lanes_before_consent_or_new_files() {
    let f = Fixture::new();
    for i in 0..32 {
        f.metadata(i != 0, &uuid().unwrap());
    }
    let before = inventory(&f.root());
    rejected(
        f.manager
            .full_comparison_start(&f.lease, f.epoch, true, Fixture::input(&uuid().unwrap())),
        "EvaluationRunLimit",
    );
    let calls = Arc::new(AtomicUsize::new(0));
    let count = calls.clone();
    rejected(
        f.manager.full_comparison_start_native(
            &f.lease,
            &f.models,
            f.epoch,
            true,
            Fixture::input(&uuid().unwrap()),
            move |_| {
                count.fetch_add(1, Ordering::SeqCst);
                Ok(false)
            },
        ),
        "EvaluationRunLimit",
    );
    assert_eq!(calls.load(Ordering::SeqCst), 0);
    assert!(inventory(&f.root()) == before);
    assert!(f.manager.cleanup_complete());
}

#[test]
fn malformed_opposite_lane_metadata_is_validated_before_catalog_filtering() {
    for native in [false, true] {
        for fault in ["version", "lane", "binding", "extra"] {
            let f = Fixture::new();
            let run = f.metadata(native, &uuid().unwrap());
            let path = f.root().join(run).join("desktop.json");
            let mut value: Value = serde_json::from_slice(&fs::read(&path).unwrap()).unwrap();
            match fault {
                "version" => value["version"] = json!(7),
                "lane" => {
                    value["input_lane"] = json!(if native {
                        "scripted_baseline"
                    } else {
                        "approved_native"
                    })
                }
                "binding" => value["binding"]["native"] = json!(!native),
                _ => value["unknown"] = json!(true),
            }
            fs::write(&path, serde_json::to_vec(&value).unwrap()).unwrap();
            let before = inventory(&f.root());
            rejected(
                f.manager.full_comparison_catalog(&f.lease, f.epoch, true),
                "EvaluationIntegrity",
            );
            rejected(
                f.manager
                    .full_comparison_catalog_native(&f.lease, f.epoch, true),
                "EvaluationIntegrity",
            );
            assert!(inventory(&f.root()) == before);
        }
    }
}

#[test]
fn opposite_lane_tokens_open_resume_cancel_and_close_never_reinterpret_or_revoke() {
    let f = Fixture::new();
    let s = uuid().unwrap();
    let n = uuid().unwrap();
    let sr = f.metadata(false, &s);
    let nr = f.metadata(true, &n);
    let st = f
        .manager
        .full_comparison_lookup(&f.lease, f.epoch, true, &s)
        .unwrap();
    let nt = f.lookup(&n);
    let before = inventory(&f.root());
    rejected(
        f.manager
            .full_comparison_status(&f.lease, f.epoch, true, cap(&nt)),
        "UnknownEvaluationRun",
    );
    rejected(
        f.manager
            .full_comparison_status_native(&f.lease, f.epoch, true, cap(&st)),
        "UnknownEvaluationRun",
    );
    rejected(
        f.manager.full_comparison_open(&f.lease, f.epoch, true, &nr),
        "UnknownEvaluationRun",
    );
    rejected(
        f.manager
            .full_comparison_open_native(&f.lease, f.epoch, true, &sr),
        "UnknownEvaluationRun",
    );
    rejected(
        f.manager
            .full_comparison_resume(&f.lease, f.epoch, true, cap(&nt), 1),
        "UnknownEvaluationRun",
    );
    let count = Arc::new(AtomicUsize::new(0));
    let calls = count.clone();
    rejected(
        f.manager.full_comparison_resume_native(
            &f.lease,
            &f.models,
            f.epoch,
            true,
            FullComparisonNativeResume {
                run_token: cap(&st).into(),
                max_new_scenes: 1,
            },
            move |_| {
                calls.fetch_add(1, Ordering::SeqCst);
                Ok(false)
            },
        ),
        "UnknownEvaluationRun",
    );
    rejected(
        f.manager
            .full_comparison_cancel(&f.lease, f.epoch, true, cap(&nt), 1),
        "UnknownEvaluationRun",
    );
    rejected(
        f.manager
            .full_comparison_cancel_native(&f.lease, f.epoch, true, cap(&st), 1),
        "UnknownEvaluationRun",
    );
    rejected(
        f.manager
            .full_comparison_close(&f.lease, f.epoch, false, cap(&nt)),
        "UnknownEvaluationRun",
    );
    rejected(
        f.manager
            .full_comparison_close_native(&f.lease, f.epoch, false, cap(&st)),
        "UnknownEvaluationRun",
    );
    assert_eq!(
        f.manager
            .full_comparison_status(&f.lease, f.epoch, true, cap(&st))
            .unwrap()["run_id"],
        sr
    );
    assert_eq!(
        f.manager
            .full_comparison_status_native(&f.lease, f.epoch, true, cap(&nt))
            .unwrap()["run_id"],
        nr
    );
    assert_eq!(count.load(Ordering::SeqCst), 0);
    assert!(inventory(&f.root()) == before);
}

#[test]
fn grant_epoch_denied_consent_and_cancel_inside_held_consent_precede_model_reservation() {
    let f = Fixture::new();
    let calls = Arc::new(AtomicUsize::new(0));
    for (epoch, granted, error) in [(f.epoch, false, "Forbidden"), (f.epoch + 2, true, "Closed")] {
        let count = calls.clone();
        rejected(
            f.manager.full_comparison_start_native(
                &f.lease,
                &f.models,
                epoch,
                granted,
                Fixture::input(&uuid().unwrap()),
                move |_| {
                    count.fetch_add(1, Ordering::SeqCst);
                    Ok(true)
                },
            ),
            error,
        );
    }
    assert_eq!(calls.load(Ordering::SeqCst), 0);
    assert!(!f.root().exists());
    let denied = f
        .manager
        .full_comparison_start_native(
            &f.lease,
            &f.models,
            f.epoch,
            true,
            Fixture::input(&uuid().unwrap()),
            |_| Ok(false),
        )
        .unwrap();
    let denied = f.done(cap(&denied));
    assert_eq!(denied["version"], 2);
    assert_eq!(denied["error"], "Cancelled");
    assert_eq!(denied["report_ready"], false);
    assert_eq!(denied["cleanup_required"], false);
    let (entered, observe) = mpsc::sync_channel(1);
    let (release, wait) = mpsc::sync_channel(1);
    let client = uuid().unwrap();
    let pending = f
        .manager
        .full_comparison_start_native(
            &f.lease,
            &f.models,
            f.epoch,
            true,
            Fixture::input(&client),
            move |_| {
                entered.send(()).map_err(|_| "Interrupted".to_owned())?;
                wait.recv_timeout(Duration::from_secs(60))
                    .map_err(|_| "Interrupted".to_owned())?;
                Ok(true)
            },
        )
        .unwrap();
    let entry = observe.recv_timeout(Duration::from_secs(30));
    // Always release before assertions so a fixture failure cannot strand consent.
    let held = f
        .manager
        .full_comparison_status_native(&f.lease, f.epoch, true, cap(&pending));
    let reserved = f.models.reserve_evaluation();
    let retry_calls = Arc::new(AtomicUsize::new(0));
    let count = retry_calls.clone();
    let retry = f.manager.full_comparison_start_native(
        &f.lease,
        &f.models,
        f.epoch,
        true,
        Fixture::input(&client),
        move |_| {
            count.fetch_add(1, Ordering::SeqCst);
            Ok(true)
        },
    );
    let cancelled = f.manager.full_comparison_cancel_native(
        &f.lease,
        f.epoch,
        true,
        cap(&pending),
        pending["operation_id"].as_u64().unwrap(),
    );
    let _ = release.send(());
    let reserve_was_free = reserved.is_ok();
    drop(reserved);
    assert!(entry.is_ok());
    assert_eq!(held.unwrap()["phase"], "awaiting_confirmation");
    assert!(reserve_was_free);
    cancelled.unwrap();
    let retry = retry.unwrap();
    assert_eq!(retry["run_id"], pending["run_id"]);
    assert_eq!(retry["operation_id"], pending["operation_id"]);
    assert_eq!(retry_calls.load(Ordering::SeqCst), 0);
    let stopped = f.done(cap(&pending));
    assert_eq!(stopped["error"], "Cancelled");
    assert_eq!(stopped["report_ready"], false);
    assert!(f.models.cleanup_complete());
    let files = inventory(&f.root());
    assert!(!files.keys().any(|p| p
        .file_name()
        .and_then(|s| s.to_str())
        .is_some_and(|s| s.starts_with("attempt-") || s.starts_with("raw-"))));
    let catalog = f
        .manager
        .full_comparison_catalog(&f.lease, f.epoch, true)
        .unwrap();
    assert!(
        catalog["runs"].as_array().unwrap().is_empty(),
        "no native-to-scripted fallback"
    );
}

#[test]
fn actual_denied_native_prefix_source_and_run_budget_refuse_before_new_consent_or_writes() {
    for source_fault in [false, true] {
        let (f, run, client) = copied_denial();
        let value = f.lookup(&client);
        let leaf = f.root().join(run);
        if source_fault {
            let path = leaf.join("desktop.json");
            let mut actual: Value = serde_json::from_slice(&fs::read(&path).unwrap()).unwrap();
            actual["binding"]["source_sha256"] = json!("0".repeat(64));
            fs::write(path, serde_json::to_vec(&actual).unwrap()).unwrap();
        } else {
            for n in 0..3 {
                let file = fs::File::create(leaf.join(format!("owned-budget-{n}.bin"))).unwrap();
                file.set_len(12 * 1024 * 1024).unwrap();
                file.sync_all().unwrap();
            }
        }
        let before = inventory(&leaf);
        let calls = Arc::new(AtomicUsize::new(0));
        let count = calls.clone();
        let expected = if source_fault {
            "EvaluationIntegrity"
        } else {
            "EvaluationBudget"
        };
        match f.manager.full_comparison_resume_native(
            &f.lease,
            &f.models,
            f.epoch,
            true,
            FullComparisonNativeResume {
                run_token: cap(&value).into(),
                max_new_scenes: 1,
            },
            move |_| {
                count.fetch_add(1, Ordering::SeqCst);
                Ok(false)
            },
        ) {
            Err(error) => assert_eq!(error, expected),
            Ok(started) => {
                let done = f.done(cap(&started));
                assert_eq!(done["error"], expected);
                assert_eq!(done["report_ready"], false);
            }
        }
        assert_eq!(calls.load(Ordering::SeqCst), 0);
        assert!(inventory(&leaf) == before);
        assert!(f.models.cleanup_complete());
    }
}

struct FixedOwner {
    owner: Arc<Mutex<locallore_local_runtime::LocalRuntime>>,
    _directory: PathBuf,
}
impl FixedOwner {
    fn new() -> Self {
        let (runtime, directory) =
            match locallore_local_runtime::LocalRuntime::development_protocol_fixture() {
                Ok(value) => value,
                Err(locallore_local_runtime::OwnedStartFailure::BeforeChild(error)) => {
                    panic!("fixed protocol fixture: {error:?}")
                }
                Err(locallore_local_runtime::OwnedStartFailure::AfterChild {
                    cause,
                    mut owner,
                }) => {
                    let cleanup = owner.terminate_and_reap();
                    if cleanup.is_err() {
                        static HELD: OnceLock<
                            Mutex<Vec<Box<locallore_local_runtime::LocalRuntime>>>,
                        > = OnceLock::new();
                        HELD.get_or_init(|| Mutex::new(vec![]))
                            .lock()
                            .unwrap()
                            .push(owner);
                    }
                    panic!("fixed protocol fixture: {cause:?}; {cleanup:?}");
                }
            };
        Self {
            owner: Arc::new(Mutex::new(runtime)),
            _directory: directory,
        }
    }
}
impl Drop for FixedOwner {
    fn drop(&mut self) {
        match self.owner.lock() {
            Ok(mut owner) => {
                let _ = owner.terminate_and_reap();
            }
            Err(owner) => {
                let _ = owner.into_inner().terminate_and_reap();
            }
        }
    }
}
fn payload(
    f: &Fixture,
    run: &str,
    witness: crate::models::CleanupWitness,
    pair: Option<(
        crate::models::EvaluationReservation,
        Arc<Mutex<locallore_local_runtime::LocalRuntime>>,
    )>,
) {
    // Explicit unit payload installation, NOT a claimed shared-producer result,
    // execution worker, failure provenance, accepted receipt or cleanup proof.
    let mut parent = f.manager.state().unwrap();
    parent.next += 1;
    let operation = parent.next;
    parent.job = Some(Job {
        kind: JobKind::ComparisonRun,
        worker_active: false,
        epoch: f.epoch,
        id: operation,
        run: run.into(),
        cancel: Cancellation::default(),
        selected: Some(SelectedOwnership {
            models: f.models.clone(),
            witness: Some(witness),
            retained: pair,
            cleanup_running: false,
        }),
    });
}

#[test]
fn actual_accepted_owner_and_witness_exclude_work_until_generic_cleanup_without_reopening_closed_record(
) {
    let f = Fixture::new();
    let client = uuid().unwrap();
    let run = f.metadata(true, &client);
    let value = f.lookup(&client);
    let fixed = FixedOwner::new();
    let mut reservation = f.models.reserve_evaluation().unwrap();
    let witness = reservation.cleanup_witness();
    assert!(
        SelectedNativeReservation::retain_uncertain(&mut reservation, fixed.owner.clone()).is_ok()
    );
    drop(reservation);
    payload(&f, &run, witness.clone(), None);
    let closed = f
        .manager
        .full_comparison_close_native(&f.lease, f.epoch, false, cap(&value))
        .unwrap();
    assert_eq!(closed["phase"], "closed");
    assert_eq!(closed["report_ready"], false);
    assert!(!witness.confirmed());
    assert!(!f.models.cleanup_complete());
    assert!(f.models.reserve_evaluation().is_err());
    rejected(
        f.manager.start(&f.lease, f.epoch, None, "one"),
        "EvaluationBusy",
    );
    assert_eq!(
        f.manager
            .selected_cleanup_status(&f.lease, f.epoch)
            .unwrap()["cleanup_required"],
        true
    );
    f.cleanup();
    assert!(witness.confirmed());
    assert!(f.models.cleanup_complete());
    assert!(f.manager.cleanup_complete());
    let after = f.lookup(&client);
    assert_eq!(after["phase"], "closed");
    assert_eq!(after["report_ready"], false);
    assert_eq!(after["cleanup_required"], false);
    assert_eq!(
        fixed.owner.lock().unwrap().status(),
        locallore_local_runtime::Status::Failed
    );
}

#[test]
fn actual_rejected_same_pair_survives_retirement_and_foreign_models_cannot_acknowledge_it() {
    let f = Fixture::new();
    let client = uuid().unwrap();
    let run = f.metadata(true, &client);
    f.lookup(&client);
    let fixed = FixedOwner::new();
    let (reservation, returned) = f.models.selected_rejected_for_test(fixed.owner.clone());
    assert!(Arc::ptr_eq(&returned, &fixed.owner));
    let witness = reservation.cleanup_witness();
    payload(&f, &run, witness.clone(), Some((reservation, returned)));
    f.manager.retire(f.epoch);
    f.manager.drain(f.epoch);
    {
        let parent = f.manager.state().unwrap();
        let pair = parent
            .job
            .as_ref()
            .unwrap()
            .selected
            .as_ref()
            .unwrap()
            .retained
            .as_ref()
            .unwrap();
        assert!(Arc::ptr_eq(&pair.1, &fixed.owner));
    }
    assert!(!witness.confirmed());
    assert!(f.models.reserve_evaluation().is_err());
    let foreign = Arc::new(ModelManager::new(
        f.manager.root.with_file_name("foreign-models"),
        f.manager.root.with_file_name("foreign-resources"),
    ));
    rejected(
        f.manager
            .selected_retry_cleanup(&f.lease, &foreign, f.epoch),
        "EvaluationModelBusy",
    );
    assert!(!witness.confirmed());
    rejected(
        f.manager.start(&f.lease, f.epoch, None, "one"),
        "EvaluationBusy",
    );
    f.cleanup();
    assert!(witness.confirmed());
    assert!(f.manager.cleanup_complete());
    assert!(f.models.cleanup_complete());
    let retained = f.lookup(&client);
    assert_eq!(retained["report_ready"], false);
    assert_eq!(retained["completed_scenes"], 0);
    assert_eq!(
        fixed.owner.lock().unwrap().status(),
        locallore_local_runtime::Status::Failed
    );
}
