// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! FIRST independent source freeze: UNCOMPILED/UNRUN. Existing native manager
//! APIs and actual scripted/Core/Host/Store producer output only. Picker callbacks
//! stand in for affirmative native selection; no OS picker, IPC, app or model.
//! Root: cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --bin locallore-desktop-spike --locked --offline --jobs 1 evaluation::comparison::scene_read_review:: -- --nocapture --test-threads=1
use super::*;
use crate::{
    evaluation::selected::{SelectedInputLane, SelectedPrepareInput},
    models::ModelManager,
};
use locallore::inspection_query::{self, Observer, Query, View, MAX_ROWS};
use locallore_eval::{
    local_lane::{
        comparison::{self as producer, literal_v3, scene_v4},
        LaneFactory,
    },
    memory_comparison::frozen_suite,
};
use locallore_storage::Store;
use std::{
    io::Write,
    sync::{
        atomic::{AtomicUsize, Ordering},
        Barrier, OnceLock,
    },
};

type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;
fn inventory(root: &Path) -> Inventory {
    fn walk(root: &Path, path: &Path, depth: usize, total: &mut usize, out: &mut Inventory) {
        assert!(depth <= 8 && out.len() < 4096);
        let metadata = fs::symlink_metadata(path).unwrap();
        assert!(!metadata.file_type().is_symlink());
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt;
            assert_eq!(metadata.file_attributes() & 0x400, 0);
        }
        let relative = path.strip_prefix(root).unwrap().to_owned();
        if metadata.is_dir() {
            out.insert(relative, None);
            for child in fs::read_dir(path).unwrap() {
                walk(root, &child.unwrap().path(), depth + 1, total, out);
            }
        } else {
            assert!(metadata.is_file() && metadata.len() <= 8 * 1024 * 1024);
            let bytes = fs::read(path).unwrap();
            *total = total.checked_add(bytes.len()).unwrap();
            assert!(*total <= 64 * 1024 * 1024);
            out.insert(relative, Some(bytes));
        }
    }
    let mut result = Inventory::new();
    walk(root, root, 0, &mut 0, &mut result);
    result
}
fn root(label: &str) -> PathBuf {
    let path =
        std::env::temp_dir().join(format!("scene-native-reader-{label}-{}", uuid().unwrap()));
    fs::create_dir(&path).unwrap();
    path
}
fn templates() -> &'static Path {
    static TEMPLATE: OnceLock<PathBuf> = OnceLock::new();
    TEMPLATE
        .get_or_init(|| {
            let root = root("closed-producers");
            let v4 = scene_v4::run_comparison(
                &root.join("v4"),
                false,
                producer::ComparisonKind::ContinuousRollout,
                &Cancellation::default(),
                1,
                LaneFactory::ScriptedBaseline,
                None,
            )
            .unwrap();
            let v3 = literal_v3::run_comparison(
                &root.join("v3"),
                false,
                producer::ComparisonKind::ContinuousRollout,
                &Cancellation::default(),
                1,
                LaneFactory::ScriptedBaseline,
                None,
            )
            .unwrap();
            let v2 = producer::run_comparison(
                &root.join("v2"),
                false,
                producer::ComparisonKind::ContinuousRollout,
                &Cancellation::default(),
                1,
                LaneFactory::ScriptedBaseline,
                None,
            )
            .unwrap();
            assert_eq!((v4.completed_scenes, v4.turns.len()), (1, 12));
            assert_eq!((v3.completed_scenes, v3.turns.len()), (1, 12));
            assert_eq!((v2.completed_scenes, v2.turns.len()), (1, 12));
            root
        })
        .as_path()
}
fn copied(version: u16) -> PathBuf {
    // Never open a template with a native/Core Reader. Every live lock and
    // mutation uses its own ordinary byte copy, including the existing run.lock.
    let original = inventory(&templates().join(format!("v{version}")));
    let target = root("copy");
    for (relative, bytes) in &original {
        let path = target.join(relative);
        match bytes {
            None => fs::create_dir_all(path).unwrap(),
            Some(bytes) => {
                let mut file = OpenOptions::new()
                    .write(true)
                    .create_new(true)
                    .open(path)
                    .unwrap();
                file.write_all(bytes).unwrap();
            }
        }
    }
    assert_eq!(inventory(&target), original);
    target
}
struct Fixture {
    root: PathBuf,
    manager: Arc<EvaluationManager>,
    lease: Arc<WindowLease>,
    epoch: u64,
}
impl Fixture {
    fn new() -> Self {
        let root = root("manager");
        let manager = Arc::new(EvaluationManager::new(root.join("evaluations")));
        let lease = Arc::new(WindowLease::default());
        let epoch = lease.begin().unwrap();
        manager.catalog(&lease, epoch).unwrap();
        Self {
            root,
            manager,
            lease,
            epoch,
        }
    }
    fn done(&self, client: &str) -> Value {
        let deadline = Instant::now() + Duration::from_secs(30);
        loop {
            let status = self
                .manager
                .comparison_status(&self.lease, self.epoch, true, client)
                .unwrap();
            if status["running"] == false {
                return status;
            }
            assert!(
                Instant::now() < deadline,
                "existing bounded native reader fixture: {status}"
            );
            std::thread::sleep(Duration::from_millis(5));
        }
    }
    fn pick(&self, client: &str, path: &Path) -> Value {
        let selected = path.to_owned();
        self.manager
            .comparison_pick(&self.lease, self.epoch, true, client, move || {
                Ok(Some(selected))
            })
            .unwrap();
        let status = self.done(client);
        assert_eq!(
            status["phase"], "ready",
            "actual protocol source must open: {status}"
        );
        status
    }
    fn close(&self, client: &str, token: Option<&str>) -> Value {
        self.manager
            .comparison_close(&self.lease, self.epoch, client, token)
            .unwrap()
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
fn err<T>(result: Result<T>) -> String {
    match result {
        Ok(_) => panic!("expected native refusal"),
        Err(error) => error,
    }
}
fn input(
    token: &str,
    binding: &str,
    request: shared::EvidenceRequest,
) -> ComparisonEvidenceRequest {
    ComparisonEvidenceRequest {
        token: token.into(),
        binding: binding.into(),
        row: shared::RowId {
            turn: "courier-01".into(),
            arm: shared::Arm::Left,
        },
        request,
    }
}
fn query(token: &str, binding: &str, observer: Observer) -> ComparisonEvidenceRequest {
    input(
        token,
        binding,
        shared::EvidenceRequest::Query {
            edge: shared::Edge::After,
            observer,
            view: View::History,
        },
    )
}
fn reacquire4(path: &Path) {
    let cap = scene_v4::desktop_api::open_read_only(path).unwrap();
    assert_eq!(
        scene_v4::desktop_api::summary(&cap, true).unwrap()["protocol_version"],
        4
    );
}

#[test]
fn actual_v4_source_and_lossless_summary_render_actual_store_observer_edges_and_receipt() {
    let f = Fixture::new();
    let path = copied(4);
    let before = inventory(&path);
    let report = serde_json::to_value(scene_v4::inspect_comparison(&path).unwrap()).unwrap();
    let client = uuid().unwrap();
    let ready = f.pick(&client, &path);
    assert_eq!(ready["read_only"], true);
    assert_eq!(ready["execution_available"], false);
    let token = ready["run_token"].as_str().unwrap();
    let binding = ready["binding"].as_str().unwrap();
    let source = f
        .manager
        .comparison_source(&f.lease, f.epoch, true, token)
        .unwrap();
    let summary = f
        .manager
        .comparison_summary(&f.lease, f.epoch, true, token)
        .unwrap();
    assert_eq!(source["source"]["protocol_version"], 4);
    assert_eq!(source["source"]["binding"], binding);
    assert_eq!(source["source"]["rows"], summary["snapshot"]["rows"]);
    assert_eq!(source["source"]["read_only"], true);
    assert_eq!(source["source"]["execution_available"], false);
    assert_eq!(summary["snapshot"]["report"], report);
    assert_eq!(summary["snapshot"]["protocol_version"], 4);
    assert_eq!(
        summary["snapshot"]["unavailable"],
        json!(["selected_protocol4_rerun_not_implemented"])
    );
    let suite = frozen_suite().unwrap();
    let mut store = Store::open_read_only(&path.join("left/synthetic.sqlite")).unwrap();
    let full = store.resume(&suite.seed().scope).unwrap().engine;
    let receipt = store
        .lookup_turn(&suite.seed().scope, "courier-01")
        .unwrap()
        .receipt
        .unwrap();
    let cut = full
        .at_revision(receipt.events().last().unwrap().sequence())
        .unwrap();
    let mut actor_pages = vec![];
    for observer in [
        Observer::Player,
        Observer::Character { id: "mira".into() },
        Observer::Character { id: "sable".into() },
    ] {
        let expected = inspection_query::query(
            &cut,
            &Query {
                version: 2,
                scope: cut.scope().clone(),
                expected_head: cut.revision(),
                at_revision: None,
                observer: observer.clone(),
                view: View::History,
                cursor: None,
                limit: MAX_ROWS,
                search: String::new(),
            },
            true,
        )
        .unwrap();
        let evidence = f
            .manager
            .comparison_evidence(
                &f.lease,
                f.epoch,
                true,
                query(token, binding, observer.clone()),
            )
            .unwrap();
        assert_eq!(
            evidence["evidence"]["body"]["page"],
            serde_json::to_value(expected).unwrap()
        );
        assert_eq!(
            evidence["evidence"]["row"],
            source["source"]["rows"][0]["row"]
        );
        assert_eq!(evidence["evidence"]["binding"], binding);
        assert_eq!(evidence["evidence"]["read_only"], true);
        assert_eq!(evidence["evidence"]["generation_grant"], false);
        assert!(!evidence.to_string().contains("SECRET-TIDE-731"));
        actor_pages.push(evidence["evidence"]["body"]["page"].clone());
        for request in [
            shared::EvidenceRequest::Receipt {
                observer: observer.clone(),
            },
            shared::EvidenceRequest::Capture {
                observer: observer.clone(),
            },
            shared::EvidenceRequest::Outputs { observer },
        ] {
            assert_eq!(
                err(f.manager.comparison_evidence(
                    &f.lease,
                    f.epoch,
                    true,
                    input(token, binding, request)
                )),
                "Forbidden"
            );
        }
    }
    assert_ne!(
        actor_pages[1]["rows"], actor_pages[2]["rows"],
        "Mira heard the first private dialogue; remote Sable did not"
    );
    let evidence = f
        .manager
        .comparison_evidence(
            &f.lease,
            f.epoch,
            true,
            input(
                token,
                binding,
                shared::EvidenceRequest::Receipt {
                    observer: Observer::Omniscient,
                },
            ),
        )
        .unwrap();
    assert_eq!(
        evidence["evidence"]["body"]["receipt"],
        serde_json::to_value(&receipt).unwrap()
    );
    assert_eq!(
        evidence["evidence"]["body"]["receipt"]["play"]["scene"]["version"],
        1
    );
    assert_eq!(
        locallore_eval::digest(&serde_json::to_vec(&receipt).unwrap()),
        report["turns"][0]["actual_receipt_sha256"]
            .as_str()
            .unwrap()
    );
    for request in [
        shared::EvidenceRequest::Capture {
            observer: Observer::Omniscient,
        },
        shared::EvidenceRequest::Outputs {
            observer: Observer::Omniscient,
        },
    ] {
        assert_eq!(
            f.manager
                .comparison_evidence(&f.lease, f.epoch, true, input(token, binding, request))
                .unwrap()["evidence"]["generation_grant"],
            false
        );
    }
    drop(store);
    assert_eq!(f.close(&client, Some(token))["phase"], "closed");
    reacquire4(&path);
    assert_eq!(inventory(&path), before);
}

#[test]
fn v4_close_then_actual_v3_and_v2_keep_typed_sources_and_deny_old_tokens() {
    let f = Fixture::new();
    let mut old_tokens: Vec<String> = vec![];
    for version in [4, 3, 2] {
        let path = copied(version);
        let before = inventory(&path);
        let client = uuid().unwrap();
        let ready = f.pick(&client, &path);
        let token = ready["run_token"].as_str().unwrap().to_owned();
        assert_eq!(
            f.manager
                .comparison_source(&f.lease, f.epoch, true, &token)
                .unwrap()["source"]["protocol_version"],
            version
        );
        assert_eq!(
            f.manager
                .comparison_summary(&f.lease, f.epoch, true, &token)
                .unwrap()["snapshot"]["report"]["version"],
            version
        );
        for old in &old_tokens {
            assert_eq!(
                err(f.manager.comparison_summary(&f.lease, f.epoch, true, old)),
                "UnknownEvaluationRun"
            );
        }
        assert_eq!(f.close(&client, Some(&token))["phase"], "closed");
        assert_eq!(inventory(&path), before);
        old_tokens.push(token);
    }
}

#[test]
fn denied_or_cancelled_picker_never_calls_selection_or_mints_a_read_grant() {
    let f = Fixture::new();
    let calls = Arc::new(AtomicUsize::new(0));
    let observed = calls.clone();
    let client = uuid().unwrap();
    let before = inventory(&f.root);
    assert_eq!(
        err(f
            .manager
            .comparison_pick(&f.lease, f.epoch, false, &client, move || {
                observed.fetch_add(1, Ordering::SeqCst);
                panic!("denied picker called")
            })),
        "Forbidden"
    );
    assert_eq!(calls.load(Ordering::SeqCst), 0);
    assert_eq!(inventory(&f.root), before);
    f.manager
        .comparison_pick(&f.lease, f.epoch, true, &client, || Ok(None))
        .unwrap();
    let cancelled = f.done(&client);
    assert_eq!(cancelled["phase"], "cancelled");
    assert!(cancelled["run_token"].is_null() && cancelled["binding"].is_null());
    assert_eq!(cancelled["read_only"], true);
    assert_eq!(cancelled["execution_available"], false);
    assert_eq!(f.close(&client, None)["phase"], "closed");
    assert_eq!(inventory(&f.root), before);
}

#[test]
fn held_v4_picker_close_or_retirement_suppresses_late_source_and_releases_lock() {
    for retired in [false, true] {
        let mut f = Fixture::new();
        let path = copied(4);
        let before = inventory(&path);
        let client = uuid().unwrap();
        let selected = path.clone();
        let (entered, seen) = mpsc::channel();
        let (release, wait) = mpsc::channel();
        f.manager
            .comparison_pick(&f.lease, f.epoch, true, &client, move || {
                entered.send(()).unwrap();
                wait.recv_timeout(Duration::from_secs(30)).unwrap();
                Ok(Some(selected))
            })
            .unwrap();
        seen.recv_timeout(Duration::from_secs(5)).unwrap();
        let old_epoch = f.epoch;
        if retired {
            let closing = f.lease.invalidate(&format!("main-{old_epoch}")).unwrap();
            f.manager.retire(old_epoch);
            release.send(()).unwrap();
            f.manager.drain(old_epoch);
            f.lease.finish_close(closing, || {});
            f.epoch = f.lease.begin().unwrap();
            assert_eq!(
                err(f
                    .manager
                    .comparison_status(&f.lease, f.epoch, true, &client)),
                "UnknownEvaluationRun"
            );
        } else {
            assert_eq!(f.close(&client, None)["phase"], "closing");
            release.send(()).unwrap();
            let closed = f.done(&client);
            assert_eq!(closed["phase"], "closed");
            assert!(closed["run_token"].is_null());
        }
        reacquire4(&path);
        assert_eq!(inventory(&path), before);
        let fresh_client = uuid().unwrap();
        let fresh = f.pick(&fresh_client, &path);
        if retired {
            assert_eq!(
                err(f
                    .manager
                    .comparison_status(&f.lease, old_epoch, true, &client)),
                "Closed"
            );
        }
        f.close(&fresh_client, fresh["run_token"].as_str());
        assert_eq!(inventory(&path), before);
    }
}

#[test]
fn v4_window_token_binding_and_mutated_source_fences_cannot_publish_private_data() {
    let f = Fixture::new();
    let path = copied(4);
    let before = inventory(&path);
    let client = uuid().unwrap();
    let ready = f.pick(&client, &path);
    let token = ready["run_token"].as_str().unwrap();
    let binding = ready["binding"].as_str().unwrap();
    let summary = f
        .manager
        .comparison_summary(&f.lease, f.epoch, true, token)
        .unwrap();
    let foreign = Arc::new(WindowLease::default());
    assert_eq!(foreign.begin().unwrap(), f.epoch);
    assert_eq!(
        err(f.manager.comparison_source(&foreign, f.epoch, true, token)),
        "UnknownEvaluationRun"
    );
    assert_eq!(
        err(f
            .manager
            .comparison_close(&foreign, f.epoch, &client, Some(token))),
        "UnknownEvaluationRun"
    );
    assert_eq!(
        err(f.manager.comparison_evidence(
            &foreign,
            f.epoch,
            true,
            query(token, binding, Observer::Player)
        )),
        "UnknownEvaluationRun"
    );
    assert_eq!(
        err(f
            .manager
            .comparison_summary(&f.lease, f.epoch, false, token)),
        "Forbidden"
    );
    assert_eq!(
        err(f.manager.comparison_evidence(
            &f.lease,
            f.epoch,
            true,
            query(token, &"0".repeat(64), Observer::Player)
        )),
        "EvaluationIntegrity"
    );
    let mut oversized = query(token, binding, Observer::Player);
    oversized.row.turn = "a".repeat(65);
    assert_eq!(
        err(f
            .manager
            .comparison_evidence(&f.lease, f.epoch, true, oversized)),
        "InvalidEvaluationInput"
    );
    let manifest_path = path.join("run.json");
    let original = fs::read(&manifest_path).unwrap();
    let mut changed: Value = serde_json::from_slice(&original).unwrap();
    changed["order"] = json!("unsupported-order");
    fs::write(&manifest_path, serde_json::to_vec(&changed).unwrap()).unwrap();
    let mut raw = input(
        "not-a-token",
        "not-a-binding",
        shared::EvidenceRequest::Capture {
            observer: Observer::Player,
        },
    );
    raw.row.turn = "not-an-actual-row".into();
    assert_eq!(
        err(f.manager.comparison_evidence(&f.lease, f.epoch, true, raw)),
        "Forbidden"
    );
    assert_eq!(
        err(f.manager.comparison_evidence(
            &f.lease,
            f.epoch,
            true,
            query(token, binding, Observer::Player)
        )),
        "EvaluationIntegrity"
    );
    assert_eq!(
        f.manager
            .comparison_summary(&f.lease, f.epoch, true, token)
            .unwrap(),
        summary
    ); // Explicit cached snapshot only.
    fs::write(&manifest_path, original).unwrap();
    assert_eq!(f.done(&client)["phase"], "ready");
    f.close(&client, Some(token));
    reacquire4(&path);
    assert_eq!(inventory(&path), before);
}

#[test]
fn close_or_retirement_after_actual_v4_evidence_suppresses_the_held_completion() {
    for retired in [false, true] {
        let mut f = Fixture::new();
        let path = copied(4);
        let before = inventory(&path);
        let client = uuid().unwrap();
        let ready = f.pick(&client, &path);
        let token = ready["run_token"].as_str().unwrap().to_owned();
        let binding = ready["binding"].as_str().unwrap().to_owned();
        let entered = Arc::new(Barrier::new(2));
        let release = Arc::new(Barrier::new(2));
        *f.manager.before_publish.lock().unwrap() = Some((entered.clone(), release.clone()));
        let manager = f.manager.clone();
        let lease = f.lease.clone();
        let epoch = f.epoch;
        let request_token = token.clone();
        let worker = std::thread::spawn(move || {
            manager.comparison_evidence(
                &lease,
                epoch,
                true,
                query(&request_token, &binding, Observer::Player),
            )
        });
        entered.wait(); // Existing test-only native worker publication hook, not fabricated evidence.
        assert_eq!(
            f.manager
                .comparison_status(&f.lease, f.epoch, true, &client)
                .unwrap()["phase"],
            "reading"
        );
        if retired {
            let closing = f.lease.invalidate(&format!("main-{}", f.epoch)).unwrap();
            f.manager.retire(f.epoch);
            release.wait();
            assert_eq!(err(worker.join().unwrap()), "Closed");
            f.manager.drain(f.epoch);
            f.lease.finish_close(closing, || {});
            f.epoch = f.lease.begin().unwrap();
            assert_eq!(
                err(f
                    .manager
                    .comparison_summary(&f.lease, f.epoch, true, &token)),
                "UnknownEvaluationRun"
            );
        } else {
            assert_eq!(f.close(&client, Some(&token))["phase"], "closing");
            release.wait();
            assert_eq!(err(worker.join().unwrap()), "Closed");
            assert_eq!(f.done(&client)["phase"], "closed");
        }
        reacquire4(&path);
        assert_eq!(inventory(&path), before);
    }
}

#[test]
fn oversized_v4_source_is_bounded_failure_without_grant_or_file_repair() {
    let f = Fixture::new();
    let path = copied(4);
    fs::write(path.join("run.json"), vec![b' '; 128 * 1024 + 1]).unwrap();
    let before = inventory(&path);
    let client = uuid().unwrap();
    let selected = path.clone();
    f.manager
        .comparison_pick(&f.lease, f.epoch, true, &client, move || Ok(Some(selected)))
        .unwrap();
    let failed = f.done(&client);
    assert_eq!(failed["phase"], "failed");
    assert_eq!(failed["error"], "EvaluationBudget");
    assert!(failed["run_token"].is_null() && failed["binding"].is_null());
    assert_eq!(failed["execution_available"], false);
    assert_eq!(f.close(&client, None)["phase"], "closed");
    assert_eq!(inventory(&path), before);
}

#[test]
fn v4_selected_prepare_refuses_both_lanes_before_consent_target_or_model_reservation() {
    for lane in [
        SelectedInputLane::ScriptedBaseline,
        SelectedInputLane::ApprovedNative,
    ] {
        let f = Fixture::new();
        let source = copied(4);
        let source_before = inventory(&source);
        let reader_client = uuid().unwrap();
        let ready = f.pick(&reader_client, &source);
        let models = Arc::new(ModelManager::new(
            f.root.join("models"),
            f.root.join("resources"),
        ));
        let held = models.reserve_evaluation().unwrap(); // In-memory ownership only, never assets/process.
        let model_before = models.status().unwrap();
        let manager_before = inventory(&f.root);
        assert!(!f.manager.selected_root().exists());
        let calls = Arc::new(AtomicUsize::new(0));
        let observed = calls.clone();
        let client = uuid().unwrap();
        f.manager
            .selected_prepare(
                &f.lease,
                &models,
                f.epoch,
                true,
                SelectedPrepareInput {
                    client_id: client.clone(),
                    reader_client_id: reader_client.clone(),
                    run_token: ready["run_token"].as_str().unwrap().into(),
                    binding: ready["binding"].as_str().unwrap().into(),
                    turn_id: "courier-01".into(),
                    arm: shared::Arm::Left,
                    lane,
                },
                move |_| {
                    observed.fetch_add(1, Ordering::SeqCst);
                    Ok(true)
                },
            )
            .unwrap();
        let deadline = Instant::now() + Duration::from_secs(30);
        let terminal = loop {
            let status = f
                .manager
                .selected_status(&f.lease, f.epoch, true, &client)
                .unwrap();
            if status["running"] == false {
                break status;
            }
            assert!(
                Instant::now() < deadline,
                "bounded selected-refusal fixture"
            );
            std::thread::sleep(Duration::from_millis(5));
        };
        assert_eq!(terminal["phase"], "failed");
        assert_eq!(terminal["error"], "NativeUnavailable");
        assert!(
            terminal["plan_token"].is_null()
                && terminal["run_token"].is_null()
                && terminal["run_id"].is_null()
        );
        assert_eq!(terminal["cleanup_required"], false);
        assert_eq!(calls.load(Ordering::SeqCst), 0);
        assert!(!f.manager.selected_root().exists());
        assert_eq!(inventory(&f.root), manager_before);
        assert_eq!(models.status().unwrap(), model_before);
        assert!(matches!(models.reserve_evaluation(), Err(ref error) if error == "Busy"));
        drop(held);
        assert!(models.cleanup_complete());
        assert_eq!(
            f.manager
                .comparison_status(&f.lease, f.epoch, true, &reader_client)
                .unwrap()["phase"],
            "closed"
        );
        assert_eq!(
            err(f.manager.comparison_summary(
                &f.lease,
                f.epoch,
                true,
                ready["run_token"].as_str().unwrap()
            )),
            "UnknownEvaluationRun"
        );
        f.manager
            .selected_close(&f.lease, f.epoch, &client)
            .unwrap();
        reacquire4(&source);
        assert_eq!(inventory(&source), source_before);
    }
}
