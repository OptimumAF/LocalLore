// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen native-service oracles, SOURCE ONLY / UNCOMPILED / UNRUN.
//! Coordinator wire6402232299/6402311190; tests frozen before service source.
//! Scripted producer/controller-native service only, not native model/IPC/GUI.
use super::*;
use locallore::inspection_query::{Observer, View};
use locallore_eval::local_lane::{comparison as producer, LaneFactory};
use std::sync::{atomic::Ordering, OnceLock};

#[path = "execution_receipt_review_tests.rs"]
mod execution_receipt_review_tests;
#[path = "open_replacement_review_tests.rs"]
mod open_replacement_review_tests;
#[path = "shutdown_handoff_review_tests.rs"]
mod shutdown_handoff_review_tests;
#[path = "transfer_close_review_tests.rs"]
mod transfer_close_review_tests;

type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;
fn inventory(root: &Path) -> Inventory {
    fn walk(root: &Path, dir: &Path, depth: usize, bytes: &mut usize, out: &mut Inventory) {
        assert!(depth <= 8);
        for entry in fs::read_dir(dir).unwrap() {
            assert!(out.len() < 4096);
            let path = entry.unwrap().path();
            let metadata = fs::symlink_metadata(&path).unwrap();
            assert!(!metadata.file_type().is_symlink());
            let key = path.strip_prefix(root).unwrap().to_owned();
            if metadata.is_dir() {
                assert!(out.insert(key, None).is_none());
                walk(root, &path, depth + 1, bytes, out);
            } else {
                assert!(metadata.is_file() && metadata.len() <= 8 * 1024 * 1024);
                let value = fs::read(path).unwrap();
                *bytes = bytes.checked_add(value.len()).unwrap();
                assert!(*bytes <= 64 * 1024 * 1024);
                assert!(out.insert(key, Some(value)).is_none());
            }
        }
    }
    let mut result = BTreeMap::new();
    walk(root, root, 0, &mut 0, &mut result);
    result
}
fn source() -> &'static Path {
    static SOURCE: OnceLock<PathBuf> = OnceLock::new();
    SOURCE
        .get_or_init(|| {
            let root =
                std::env::temp_dir().join(format!("selected-service-source-{}", uuid().unwrap()));
            fs::create_dir(&root).unwrap();
            let path = root.join("rollout");
            let report = producer::run_comparison(
                &path,
                false,
                producer::ComparisonKind::ContinuousRollout,
                &Cancellation::default(),
                1,
                LaneFactory::ScriptedBaseline,
                None,
            )
            .unwrap();
            assert_eq!(report.turns.len(), 12);
            assert!(report.turns.iter().all(|row| row.passed));
            path
        })
        .as_path()
}
struct Fixture {
    manager: Arc<EvaluationManager>,
    models: Arc<ModelManager>,
    lease: Arc<WindowLease>,
    epoch: u64,
}
impl Fixture {
    fn new() -> Self {
        let root = std::env::temp_dir().join(format!("selected-service-{}", uuid().unwrap()));
        fs::create_dir(&root).unwrap();
        let lease = Arc::new(WindowLease::default());
        let epoch = lease.begin().unwrap();
        let manager = Arc::new(EvaluationManager::new(root.join("evaluations")));
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
    fn status(&self, client: &str) -> Value {
        self.manager
            .selected_status(&self.lease, self.epoch, true, client)
            .unwrap()
    }
    fn done(&self, client: &str) -> Value {
        let until = Instant::now() + Duration::from_secs(60);
        loop {
            let status = self.status(client);
            if status["running"] == false {
                return status;
            }
            assert!(
                Instant::now() < until,
                "bounded native service fixture: {status}"
            );
            std::thread::sleep(Duration::from_millis(5));
        }
    }
    fn input(&self, client: &str) -> SelectedPrepareInput {
        let reader = uuid().unwrap();
        let path = source().to_path_buf();
        self.manager
            .comparison_pick(&self.lease, self.epoch, true, &reader, move || {
                Ok(Some(path))
            })
            .unwrap();
        let until = Instant::now() + Duration::from_secs(60);
        let ready = loop {
            let value = self
                .manager
                .comparison_status(&self.lease, self.epoch, true, &reader)
                .unwrap();
            if value["running"] == false {
                break value;
            }
            assert!(Instant::now() < until);
            std::thread::sleep(Duration::from_millis(5));
        };
        assert_eq!(ready["phase"], "ready");
        // Source-only pre-execution correction: the evaluator's suite helper
        // is private. Obtain the actual row through the public native reader.
        let metadata = self
            .manager
            .comparison_source(
                &self.lease,
                self.epoch,
                true,
                ready["run_token"].as_str().unwrap(),
            )
            .unwrap();
        let turn = metadata["source"]["rows"][0]["row"]["turn"]
            .as_str()
            .unwrap()
            .to_owned();
        SelectedPrepareInput {
            client_id: client.into(),
            reader_client_id: reader,
            run_token: ready["run_token"].as_str().unwrap().into(),
            binding: ready["binding"].as_str().unwrap().into(),
            turn_id: turn,
            arm: Arm::Left,
            lane: SelectedInputLane::ScriptedBaseline,
        }
    }
    fn prepare(&self, client: &str) -> Value {
        self.manager
            .selected_prepare(
                &self.lease,
                &self.models,
                self.epoch,
                true,
                self.input(client),
                |metadata| {
                    assert_eq!(metadata["kind"], "selected_prepared");
                    Ok(true)
                },
            )
            .unwrap();
        let prepared = self.done(client);
        assert_eq!(prepared["phase"], "prepared", "{prepared}");
        prepared
    }
}
impl Drop for Fixture {
    fn drop(&mut self) {
        let closed = self.lease.invalidate(&format!("main-{}", self.epoch));
        self.manager.retire(self.epoch);
        self.manager.drain(self.epoch);
        if let Some(closed) = closed {
            self.lease.finish_close(closed, || {});
        }
    }
}

#[test]
fn denied_native_execution_consent_has_no_plan_target_model_reservation_or_source_write() {
    let fixture = Fixture::new();
    let before = inventory(source());
    let client = uuid().unwrap();
    fixture
        .manager
        .selected_prepare(
            &fixture.lease,
            &fixture.models,
            fixture.epoch,
            true,
            fixture.input(&client),
            |metadata| {
                assert_eq!(metadata["kind"], "selected_prepared");
                assert!(metadata.get("source_inputs").is_none());
                assert!(metadata.get("request").is_none());
                Ok(false)
            },
        )
        .unwrap();
    let result = fixture.done(&client);
    assert_eq!(result["error"], "Cancelled");
    assert_eq!(result["plan_token"], Value::Null);
    assert_eq!(result["run_id"], Value::Null);
    assert_eq!(result["cleanup_required"], false);
    assert_eq!(
        fixture
            .manager
            .selected_catalog(&fixture.lease, fixture.epoch, true)
            .unwrap()["runs"]
            .as_array()
            .unwrap()
            .len(),
        0
    );
    drop(
        fixture
            .models
            .reserve_evaluation()
            .expect("consent refusal invokes no assets/reservation"),
    );
    assert_eq!(inventory(source()), before);
}

#[test]
fn scripted_start_duplicate_and_lost_ack_keep_one_identity_then_explicit_read_grant_uses_real_edges(
) {
    let fixture = Fixture::new();
    let before = inventory(source());
    let client = uuid().unwrap();
    let prepared = fixture.prepare(&client);
    let plan = prepared["plan_token"].as_str().unwrap();
    let started = fixture
        .manager
        .selected_start(
            &fixture.lease,
            &fixture.models,
            fixture.epoch,
            true,
            &client,
            plan,
        )
        .unwrap();
    let duplicate = fixture
        .manager
        .selected_start(
            &fixture.lease,
            &fixture.models,
            fixture.epoch,
            true,
            &client,
            plan,
        )
        .unwrap();
    assert_eq!(duplicate["operation_id"], started["operation_id"]);
    assert_eq!(duplicate["run_id"], started["run_id"]);
    // Discarding the first reply is the unknown-ack fixture: lookup is same client.
    let finished = fixture.done(&client);
    assert_eq!(finished["phase"], "completed", "{finished}");
    let repeated = fixture
        .manager
        .selected_start(
            &fixture.lease,
            &fixture.models,
            fixture.epoch,
            true,
            &client,
            plan,
        )
        .unwrap();
    assert_eq!(repeated["operation_id"], started["operation_id"]);
    let run = finished["run_id"].as_str().unwrap();
    fixture
        .manager
        .selected_open(
            &fixture.lease,
            &fixture.models,
            fixture.epoch,
            true,
            (&client, run),
            |_| Ok(true),
        )
        .unwrap();
    let opened = fixture.done(&client);
    let identity = SelectedReadInput {
        client_id: client.clone(),
        run_token: opened["run_token"].as_str().unwrap().into(),
        binding: opened["binding"].as_str().unwrap().into(),
    };
    let summary = fixture
        .manager
        .selected_summary(
            &fixture.lease,
            &fixture.models,
            fixture.epoch,
            true,
            identity.clone(),
        )
        .unwrap();
    assert_eq!(summary["kind"], "selected_summary");
    assert!(summary["summary"].get("source_inputs").is_none());
    assert!(summary["summary"].get("report").is_none());
    let result = fixture
        .manager
        .selected_evidence(
            &fixture.lease,
            &fixture.models,
            fixture.epoch,
            true,
            SelectedEvidenceInput {
                identity: identity.clone(),
                arm: Arm::Left,
                request: EvidenceRequest::Query {
                    edge: Edge::After,
                    observer: Observer::Player,
                    view: View::History,
                },
            },
        )
        .unwrap();
    assert_eq!(result["evidence"]["body"]["kind"], "query");
    assert_eq!(result["evidence"]["generation_grant"], false);
    let mut invalid = identity.clone();
    invalid.run_token = "not-a-token".into();
    assert_eq!(
        fixture
            .manager
            .selected_evidence(
                &fixture.lease,
                &fixture.models,
                fixture.epoch,
                true,
                SelectedEvidenceInput {
                    identity: invalid,
                    arm: Arm::Left,
                    request: EvidenceRequest::Capture {
                        observer: Observer::Character { id: "mira".into() }
                    }
                }
            )
            .unwrap_err(),
        "Forbidden"
    );
    assert_eq!(
        fixture
            .manager
            .selected_catalog(&fixture.lease, fixture.epoch, true)
            .unwrap()["runs"]
            .as_array()
            .unwrap()
            .len(),
        1
    );
    fixture
        .manager
        .selected_close(&fixture.lease, fixture.epoch, &client)
        .unwrap();
    assert_eq!(inventory(source()), before);
}

#[test]
fn grant_and_foreign_lease_cannot_start_and_retirement_revokes_unused_plan_without_execution() {
    let fixture = Fixture::new();
    let before = inventory(source());
    let client = uuid().unwrap();
    let prepared = fixture.prepare(&client);
    let plan = prepared["plan_token"].as_str().unwrap();
    assert_eq!(
        fixture
            .manager
            .selected_start(
                &fixture.lease,
                &fixture.models,
                fixture.epoch,
                false,
                &client,
                plan
            )
            .unwrap_err(),
        "Forbidden"
    );
    let other = Arc::new(WindowLease::default());
    let other_epoch = other.begin().unwrap();
    assert_eq!(
        fixture
            .manager
            .selected_start(&other, &fixture.models, other_epoch, true, &client, plan)
            .unwrap_err(),
        "UnknownEvaluationRun"
    );
    let closed = fixture
        .lease
        .invalidate(&format!("main-{}", fixture.epoch))
        .unwrap();
    fixture.manager.retire(fixture.epoch);
    fixture.manager.drain(fixture.epoch);
    fixture.lease.finish_close(closed, || {});
    assert_eq!(
        fixture
            .manager
            .selected_status(&fixture.lease, fixture.epoch, true, &client)
            .unwrap_err(),
        "Closed"
    );
    assert_eq!(inventory(source()), before);
    drop(fixture.models.reserve_evaluation().unwrap());
}

#[test]
fn pending_native_consent_cancel_cannot_publish_grant_or_create_an_experiment() {
    let fixture = Fixture::new();
    let before = inventory(source());
    let client = uuid().unwrap();
    let (entered, waiting) = std::sync::mpsc::sync_channel(1);
    let (release, released) = std::sync::mpsc::sync_channel(1);
    let status = fixture
        .manager
        .selected_prepare(
            &fixture.lease,
            &fixture.models,
            fixture.epoch,
            true,
            fixture.input(&client),
            move |_| {
                entered.send(()).unwrap();
                released.recv_timeout(Duration::from_secs(30)).unwrap();
                Ok(true)
            },
        )
        .unwrap();
    waiting.recv_timeout(Duration::from_secs(60)).unwrap();
    fixture
        .manager
        .selected_cancel(
            &fixture.lease,
            fixture.epoch,
            true,
            &client,
            status["operation_id"].as_u64().unwrap(),
        )
        .unwrap();
    release.send(()).unwrap();
    let result = fixture.done(&client);
    assert_eq!(result["error"], "Cancelled");
    assert_eq!(result["plan_token"], Value::Null);
    assert_eq!(result["run_id"], Value::Null);
    assert_eq!(inventory(source()), before);
}

#[test]
fn spawn_failure_releases_source_cap_outside_gates_without_creating_work_or_false_grant() {
    let fixture = Fixture::new();
    let before = inventory(source());
    let client = uuid().unwrap();
    let input = fixture.input(&client);
    fixture.manager.fail_spawn.store(true, Ordering::SeqCst);
    assert_eq!(
        fixture
            .manager
            .selected_prepare(
                &fixture.lease,
                &fixture.models,
                fixture.epoch,
                true,
                input,
                |_| Ok(true)
            )
            .unwrap_err(),
        "EvaluationInternal"
    );
    let result = fixture.done(&client);
    assert_eq!(result["plan_token"], Value::Null);
    assert_eq!(result["run_id"], Value::Null);
    let cap = source_reader::open_read_only(source())
        .expect("spawn failure leaves no orphaned source lock");
    drop(cap);
    assert_eq!(inventory(source()), before);
}

#[test]
fn retired_private_job_keeps_genuine_rejected_owner_pair_until_actual_generic_cleanup() {
    // Unit-level ownership payload fixture, NOT shared native generation. The
    // cfg(test)-only Models helper performs the approved exact-ticket fault and
    // actual selected trait rejection; no fields/SQL/receipt are fabricated.
    let fixture = Fixture::new();
    let (mut runtime, directory) =
        match locallore_local_runtime::LocalRuntime::development_protocol_fixture() {
            Ok(value) => value,
            Err(locallore_local_runtime::OwnedStartFailure::BeforeChild(error)) => {
                panic!("fixed worker: {error:?}")
            }
            Err(locallore_local_runtime::OwnedStartFailure::AfterChild { cause, mut owner }) => {
                let cleanup = owner.terminate_and_reap();
                panic!("fixed worker: {cause:?}; cleanup {cleanup:?}");
            }
        };
    runtime.load(|| false).unwrap();
    struct Fixed {
        owner: Option<Arc<Mutex<locallore_local_runtime::LocalRuntime>>>,
        directory: PathBuf,
    }
    impl Drop for Fixed {
        fn drop(&mut self) {
            let owner = self.owner.take().unwrap();
            let confirmed = match owner.lock() {
                Ok(mut owner) => owner.terminate_and_reap().is_ok(),
                Err(poisoned) => poisoned.into_inner().terminate_and_reap().is_ok(),
            };
            drop(owner);
            if confirmed {
                let _ = fs::remove_dir_all(&self.directory);
            }
        }
    }
    let fixed = Fixed {
        owner: Some(Arc::new(Mutex::new(runtime))),
        directory,
    };
    let owner = fixed.owner.as_ref().unwrap().clone();
    let (reservation, returned) = fixture.models.selected_rejected_for_test(owner.clone());
    assert!(Arc::ptr_eq(&returned, &owner));
    let witness = reservation.cleanup_witness();
    let client = uuid().unwrap();
    {
        let mut parent = fixture.manager.state().unwrap();
        parent.next += 1;
        parent.job = Some(Job {
            kind: JobKind::Selected,
            worker_active: false,
            epoch: fixture.epoch,
            id: parent.next,
            run: client,
            cancel: Cancellation::default(),
            selected: Some(SelectedOwnership {
                models: fixture.models.clone(),
                witness: Some(witness.clone()),
                retained: Some((reservation, returned)),
                cleanup_running: false,
            }),
        });
    }
    fixture.manager.selected_retire(fixture.epoch);
    fixture.manager.selected_drain(fixture.epoch);
    assert!(fixture
        .manager
        .state()
        .unwrap()
        .job
        .as_ref()
        .unwrap()
        .selected
        .as_ref()
        .unwrap()
        .retained
        .is_some());
    assert!(!witness.confirmed());
    assert!(matches!(fixture.models.reserve_evaluation(), Err(error) if error == "Busy"));
    let status = fixture
        .manager
        .selected_cleanup_status(&fixture.lease, fixture.epoch)
        .unwrap();
    assert_eq!(status["cleanup_required"], true);
    assert!(status.get("run_id").is_none() && status.get("client_id").is_none());
    fixture
        .manager
        .selected_retry_cleanup(&fixture.lease, &fixture.models, fixture.epoch)
        .unwrap();
    let until = Instant::now() + Duration::from_secs(15);
    loop {
        let status = fixture
            .manager
            .selected_cleanup_status(&fixture.lease, fixture.epoch)
            .unwrap();
        if status["running"] == false {
            assert_eq!(status["cleanup_required"], false);
            break;
        }
        assert!(Instant::now() < until);
        std::thread::sleep(Duration::from_millis(5));
    }
    assert!(witness.confirmed());
    assert!(fixture.manager.state().unwrap().job.is_none());
    assert_eq!(
        owner.lock().unwrap().status(),
        locallore_local_runtime::Status::Failed
    );
    drop(
        fixture
            .models
            .reserve_evaluation()
            .expect("only actual proof releases Models fence"),
    );
}

#[test]
fn owned_curated_job_with_borrowed_handle_remains_active_then_unknown_without_private_selected_rows(
) {
    // Frozen source-only metadata fixture for Root's common Job.worker_active
    // seam. No runtime/provider exists here and no cleanup proof is invented.
    let fixture = Fixture::new();
    let client = uuid().unwrap();
    {
        let mut parent = fixture.manager.state().unwrap();
        parent.next += 1;
        parent.job = Some(Job {
            kind: JobKind::Curated,
            worker_active: true,
            epoch: fixture.epoch,
            id: parent.next,
            run: client,
            cancel: Cancellation::default(),
            selected: Some(SelectedOwnership {
                models: fixture.models.clone(),
                witness: None,
                retained: None,
                cleanup_running: false,
            }),
        });
    }
    assert!(
        fixture.manager.worker.lock().unwrap().is_none(),
        "parent drain borrowed handle fixture"
    );
    let active = fixture
        .manager
        .selected_cleanup_status(&fixture.lease, fixture.epoch)
        .unwrap();
    assert_eq!(active["running"], true);
    assert_eq!(active["cleanup_required"], false);
    let unchanged = fixture
        .manager
        .selected_retry_cleanup(&fixture.lease, &fixture.models, fixture.epoch)
        .unwrap();
    assert_eq!(unchanged["running"], true);
    assert!(
        fixture
            .manager
            .state()
            .unwrap()
            .job
            .as_ref()
            .unwrap()
            .worker_active
    );
    assert!(
        !fixture
            .manager
            .state()
            .unwrap()
            .job
            .as_ref()
            .unwrap()
            .selected
            .as_ref()
            .unwrap()
            .cleanup_running
    );
    // Test-only acknowledgement of this metadata fixture, not actual worker
    // completion or actual Runtime cleanup. Without a proof the job stays held.
    fixture
        .manager
        .state()
        .unwrap()
        .job
        .as_mut()
        .unwrap()
        .worker_active = false;
    let ended = fixture
        .manager
        .selected_cleanup_status(&fixture.lease, fixture.epoch)
        .unwrap();
    assert_eq!(ended["running"], false);
    assert_eq!(ended["cleanup_required"], true);
    assert!(fixture.manager.state().unwrap().job.is_some());
    assert!(fixture.manager.selected_lock().unwrap().records.is_empty());
    // No owner was created in this synthetic metadata-only fixture.
    let job = fixture.manager.state().unwrap().job.take();
    drop(job);
}
