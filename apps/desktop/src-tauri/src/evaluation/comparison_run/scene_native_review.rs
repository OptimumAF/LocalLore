// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent native SceneV4 service freeze on 97106af7: UNCOMPILED / UNRUN.
//! Typed service calls, real denied native prefixes and separate actual scripted
//! Core/Host/Store output only. No model, native completed run, IPC or GUI proof.
//! The parent owns cfg(test) module registration and serialized execution.
use super::*;
use crate::{
    evaluation::{
        selected::{SelectedInputLane, SelectedPrepareInput},
        FullComparisonProtocol,
    },
    models::ModelManager,
};
use locallore_eval::{
    local_lane::comparison::{desktop_api::Arm, scene_v4},
    memory_comparison_v4 as wire4,
};
use std::sync::{
    atomic::{AtomicUsize, Ordering},
    mpsc, OnceLock,
};

type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;
fn inventory(root: &Path) -> Inventory {
    fn walk(root: &Path, path: &Path, depth: usize, total: &mut usize, out: &mut Inventory) {
        assert!(depth <= 12 && out.len() < 8192);
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
            assert!(metadata.is_file() && metadata.len() <= 16 * 1024 * 1024);
            let bytes = fs::read(path).unwrap();
            *total = total.checked_add(bytes.len()).unwrap();
            assert!(*total <= 128 * 1024 * 1024);
            out.insert(relative, Some(bytes));
        }
    }
    let mut result = Inventory::new();
    walk(root, root, 0, &mut 0, &mut result);
    result
}
fn rejected<T>(result: Result<T>, expected: &str) {
    match result {
        Err(error) => assert_eq!(error, expected),
        Ok(_) => panic!("expected {expected}"),
    }
}
fn token(value: &Value) -> &str {
    value["run_token"].as_str().unwrap()
}
struct HeldManagers {
    _manager: Arc<EvaluationManager>,
    _models: Arc<ModelManager>,
    _lease: Arc<WindowLease>,
}
struct Fixture {
    manager: Arc<EvaluationManager>,
    models: Arc<ModelManager>,
    lease: Arc<WindowLease>,
    epoch: u64,
    root: PathBuf,
}
impl Fixture {
    fn new() -> Self {
        let root = std::env::temp_dir().join(format!("scene-native-service-{}", uuid().unwrap()));
        fs::create_dir(&root).unwrap();
        // Synthetic sentinels, not a model/package or an asset-availability probe.
        for name in ["models", "resources"] {
            fs::create_dir(root.join(name)).unwrap();
            fs::write(root.join(name).join("synthetic-sentinel.txt"), b"unchanged fixture").unwrap();
        }
        let manager = Arc::new(EvaluationManager::new(root.join("evaluations")));
        let lease = Arc::new(WindowLease::default());
        let epoch = lease.begin().unwrap();
        manager.catalog(&lease, epoch).unwrap();
        let models = Arc::new(ModelManager::new(root.join("models"), root.join("resources")));
        Self { manager, models, lease, epoch, root }
    }
    fn runs(&self) -> PathBuf {
        self.root.join("comparison-evaluations")
    }
    fn input(client: &str) -> FullComparisonStart {
        FullComparisonStart {
            client_id: client.into(),
            kind: core::ComparisonKind::ContinuousRollout,
            max_new_scenes: 1,
        }
    }
    fn catalog(&self, protocol: FullComparisonProtocol) -> Result<Value> {
        self.manager.full_comparison_catalog_native_for(&self.lease, self.epoch, true, protocol)
    }
    fn lookup(&self, protocol: FullComparisonProtocol, client: &str) -> Value {
        self.manager.full_comparison_lookup_native_for(&self.lease, self.epoch, true, protocol, client).unwrap()
    }
    fn done(&self, protocol: FullComparisonProtocol, cap: &str) -> Value {
        self.wait(|| self.manager.full_comparison_status_native_for(&self.lease, self.epoch, true, protocol, cap))
    }
    fn read_done(&self, client: &str) -> Value {
        self.wait(|| self.manager.comparison_status(&self.lease, self.epoch, true, client))
    }
    fn wait(&self, mut status: impl FnMut() -> Result<Value>) -> Value {
        let end = Instant::now() + Duration::from_secs(180);
        loop {
            let value = status().unwrap();
            if value["running"] == false { return value; }
            assert!(Instant::now() < end, "bounded fixture scheduling wait: {value}");
            std::thread::sleep(Duration::from_millis(5));
        }
    }
    fn sequence(&self) -> u64 {
        // Reads the EXISTING ownership counter; no new counter or reserve probe.
        self.models.evaluation_sequence_for_tests().unwrap()
    }
    fn assets(&self) -> (Inventory, Inventory) {
        (inventory(&self.root.join("models")), inventory(&self.root.join("resources")))
    }
    fn metadata(&self, version: u16, client: &str) -> String {
        // Closed wrapper metadata ONLY; no report/receipt/native profile relabel.
        let run = uuid().unwrap();
        let path = self.runs().join(&run);
        fs::create_dir_all(&path).unwrap();
        let binding = if version == 3 {
            serde_json::to_value(wire4::current_binding(true).unwrap()).unwrap()
        } else {
            serde_json::to_value(wire::current_binding(version == 2).unwrap()).unwrap()
        };
        let value = json!({"version":version,"protocol_version":if version==3 {4}else{3},
            "input_lane":if version==1 {"scripted_baseline"}else{"approved_native"},
            "run_id":run,"client_id":client,"kind":"continuous_rollout","initial_batch":1,"created_ms":1,"binding":binding});
        fs::write(path.join("desktop.json"), serde_json::to_vec(&value).unwrap()).unwrap();
        run
    }
    fn deny(&self, protocol: FullComparisonProtocol, client: &str) -> Value {
        let initial = self.manager.full_comparison_start_native_for(
            &self.lease, &self.models, self.epoch, true, protocol, Self::input(client), |_| Ok(false),
        ).unwrap();
        let done = self.done(protocol, token(&initial));
        assert_eq!(done["error"], "Cancelled");
        assert_eq!(done["report_ready"], false);
        assert_eq!(done["cleanup_required"], false);
        done
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
            // Keep the SAME actual owners alive if cleanup is unknown. Evidence
            // and task TEMP are retained; no recursive cleanup or owner forgery.
            static HELD: OnceLock<Mutex<Vec<HeldManagers>>> = OnceLock::new();
            HELD.get_or_init(|| Mutex::new(vec![])).lock().unwrap().push(HeldManagers {
                _manager: self.manager.clone(), _models: self.models.clone(), _lease: self.lease.clone(),
            });
        }
    }
}

#[test]
fn scene_grant_epoch_and_closed_input_precede_files_consent_and_reservation() {
    let f = Fixture::new();
    let before = inventory(&f.root);
    let calls = Arc::new(AtomicUsize::new(0));
    for (epoch, granted, batch, client, code) in [
        (f.epoch, false, 1, uuid().unwrap(), "Forbidden"),
        (f.epoch + 1, true, 1, uuid().unwrap(), "Closed"),
        (f.epoch, true, 0, uuid().unwrap(), "InvalidEvaluationInput"),
        (f.epoch, true, 5, uuid().unwrap(), "InvalidEvaluationInput"),
        (f.epoch, true, 1, "not-a-client".into(), "InvalidEvaluationInput"),
    ] {
        let observed = calls.clone();
        let mut input = Fixture::input(&client);
        input.max_new_scenes = batch;
        rejected(f.manager.full_comparison_start_native_for(
            &f.lease, &f.models, epoch, granted, FullComparisonProtocol::SceneV4, input,
            move |_| { observed.fetch_add(1, Ordering::SeqCst); Ok(true) },
        ), code);
    }
    assert_eq!(calls.load(Ordering::SeqCst), 0);
    assert_eq!(f.sequence(), 0);
    assert_eq!(inventory(&f.root), before);
}

#[test]
fn actual_scene_denial_records_only_provisional_native4_before_any_model_reservation() {
    let f = Fixture::new();
    let assets = f.assets();
    let client = uuid().unwrap();
    let (send, receive) = mpsc::sync_channel(1);
    let started = f.manager.full_comparison_start_native_for(
        &f.lease, &f.models, f.epoch, true, FullComparisonProtocol::SceneV4, Fixture::input(&client),
        move |metadata| { send.send(metadata.clone()).map_err(|_| "Interrupted".to_owned())?; Ok(false) },
    ).unwrap();
    let done = f.done(FullComparisonProtocol::SceneV4, token(&started));
    let consent = receive.recv_timeout(Duration::from_secs(1)).unwrap();
    assert_eq!(consent, json!({"version":1,"kind":"full_comparison_execution","protocol_version":4,
        "input_lane":"approved_native","run_id":done["run_id"],"client_id":client,
        "comparison_kind":"rollout","batch":1,"max_admissions":32,"max_roles":96,"max_active_ms":1800000}));
    assert_eq!(done["version"], 3);
    assert_eq!(done["protocol_version"], 4);
    assert_eq!(done["input_lane"], "approved_native");
    assert_eq!(done["error"], "Cancelled");
    assert_eq!(done["completed_scenes"], 0);
    assert_eq!(done["completed"], false);
    assert_eq!(done["report_ready"], false);
    assert_eq!(done["cleanup_required"], false);
    let leaf = f.runs().join(done["run_id"].as_str().unwrap());
    let index: Value = serde_json::from_slice(&fs::read(leaf.join("desktop.json")).unwrap()).unwrap();
    assert_eq!(index["version"], 3);
    assert_eq!(index["protocol_version"], 4);
    assert_eq!(index["binding"], serde_json::to_value(wire4::current_binding(true).unwrap()).unwrap());
    let manifest: Value = serde_json::from_slice(&fs::read(leaf.join("work/run.json")).unwrap()).unwrap();
    assert_eq!(manifest["version"], 4);
    assert_eq!(manifest["binding"], index["binding"]);
    let actual = scene_v4::inspect_comparison(&leaf.join("work")).unwrap();
    assert_eq!(actual.completed_scenes, 0);
    assert!(actual.turns.is_empty() && !actual.completed);
    assert_eq!((actual.left_reserved_roles, actual.right_reserved_roles, actual.physical_setups), (0, 0, 0));
    assert!(actual.native_load.is_none());
    assert_eq!(f.sequence(), 0);
    assert_eq!(f.assets(), assets);
    assert!(f.models.cleanup_complete());
    assert!(!inventory(&leaf).keys().any(|p| p.file_name().and_then(|n| n.to_str())
        .is_some_and(|n| n.starts_with("attempt-") || n.starts_with("raw-") || n.starts_with("turn-"))));
}

#[test]
fn actual_default_native_wrapper_still_emits_literal3_provisional_bytes() {
    let f = Fixture::new();
    let client = uuid().unwrap();
    let initial = f.manager.full_comparison_start_native(&f.lease, &f.models, f.epoch, true,
        Fixture::input(&client), |metadata| {
            assert_eq!(metadata["protocol_version"], 3);
            Ok(false)
        }).unwrap();
    let terminal = f.done(FullComparisonProtocol::LiteralV3, token(&initial));
    assert_eq!(terminal["version"], 2);
    assert_eq!(terminal["protocol_version"], 3);
    assert_eq!(terminal["error"], "Cancelled");
    let leaf = f.runs().join(terminal["run_id"].as_str().unwrap());
    let index_bytes = fs::read(leaf.join("desktop.json")).unwrap();
    let manifest_bytes = fs::read(leaf.join("work/run.json")).unwrap();
    let index: Value = serde_json::from_slice(&index_bytes).unwrap();
    let manifest: Value = serde_json::from_slice(&manifest_bytes).unwrap();
    assert_eq!(index["version"], 2);
    assert_eq!(index["protocol_version"], 3);
    assert_eq!(manifest["version"], 3);
    assert_eq!(index["binding"], serde_json::to_value(wire::current_binding(true).unwrap()).unwrap());
    assert_eq!(manifest["binding"], index["binding"]);
    assert_eq!(terminal, f.manager.full_comparison_status_native(&f.lease, f.epoch, true, token(&initial)).unwrap());
    assert_eq!(f.catalog(FullComparisonProtocol::SceneV4).unwrap()["runs"], json!([]));
    assert_eq!(fs::read(leaf.join("desktop.json")).unwrap(), index_bytes);
    assert_eq!(fs::read(leaf.join("work/run.json")).unwrap(), manifest_bytes);
    assert_eq!(f.sequence(), 0);
}

#[test]
fn mixed_protocol_catalogs_preserve_default3_metadata_bytes_and_filter_only_after_validation() {
    let f = Fixture::new();
    let scripted = f.metadata(1, &uuid().unwrap());
    let old_client = uuid().unwrap();
    let old = f.metadata(2, &old_client);
    let scene_client = uuid().unwrap();
    let scene = f.metadata(3, &scene_client);
    let before = inventory(&f.runs());
    let old_catalog = f.manager.full_comparison_catalog_native(&f.lease, f.epoch, true).unwrap();
    let typed_old = f.catalog(FullComparisonProtocol::LiteralV3).unwrap();
    assert_eq!(typed_old, old_catalog);
    assert_eq!(old_catalog["version"], 2);
    assert_eq!(old_catalog["protocol_version"], 3);
    assert_eq!(old_catalog["runs"].as_array().unwrap().len(), 1);
    assert_eq!(old_catalog["runs"][0]["run_id"], old);
    let scene_catalog = f.catalog(FullComparisonProtocol::SceneV4).unwrap();
    assert_eq!(scene_catalog["version"], 3);
    assert_eq!(scene_catalog["protocol_version"], 4);
    assert_eq!(scene_catalog["runs"].as_array().unwrap().len(), 1);
    assert_eq!(scene_catalog["runs"][0]["run_id"], scene);
    let baseline = f.manager.full_comparison_catalog(&f.lease, f.epoch, true).unwrap();
    assert_eq!(baseline["runs"].as_array().unwrap().len(), 1);
    assert_eq!(baseline["runs"][0]["run_id"], scripted);
    let old_status = f.lookup(FullComparisonProtocol::LiteralV3, &old_client);
    assert_eq!(old_status, f.manager.full_comparison_lookup_native(&f.lease, f.epoch, true, &old_client).unwrap());
    assert_eq!(f.lookup(FullComparisonProtocol::SceneV4, &scene_client)["protocol_version"], 4);
    assert_eq!(inventory(&f.runs()), before);
    assert_eq!(f.sequence(), 0);
}

#[test]
fn malformed_other_protocol_shapes_and_duplicate_clients_refuse_globally_before_filtering() {
    for version in [1, 2, 3] {
        for fault in ["version", "protocol", "lane", "native", "descriptor", "budget", "extra", "duplicate"] {
            let f = Fixture::new();
            let client = uuid().unwrap();
            let run = f.metadata(version, &client);
            let path = f.runs().join(run).join("desktop.json");
            let mut value: Value = serde_json::from_slice(&fs::read(&path).unwrap()).unwrap();
            match fault {
                "version" => value["version"] = json!(9),
                "protocol" => value["protocol_version"] = json!(if version == 3 {3}else{4}),
                "lane" => value["input_lane"] = json!("unapproved"),
                "native" => value["binding"]["native"] = json!(version == 1),
                "descriptor" => value["binding"]["arms"][0]["prompt_version"] = json!("foreign"),
                "budget" => value["binding"]["max_roles"] = json!(97),
                "extra" => value["unknown"] = json!(true),
                "duplicate" => { f.metadata(if version == 3 {2}else{3}, &client); },
                _ => unreachable!(),
            }
            fs::write(&path, serde_json::to_vec(&value).unwrap()).unwrap();
            let before = inventory(&f.runs());
            rejected(f.catalog(FullComparisonProtocol::SceneV4), "EvaluationIntegrity");
            rejected(f.catalog(FullComparisonProtocol::LiteralV3), "EvaluationIntegrity");
            rejected(f.manager.full_comparison_catalog(&f.lease, f.epoch, true), "EvaluationIntegrity");
            assert_eq!(inventory(&f.runs()), before);
            assert_eq!(f.sequence(), 0);
        }
    }
}

#[test]
fn combined_global_cap_and_cross_protocol_client_identity_precede_consent_or_files() {
    let f = Fixture::new();
    for n in 0..32 { f.metadata(1 + n % 3, &uuid().unwrap()); }
    f.catalog(FullComparisonProtocol::SceneV4).unwrap();
    let before = inventory(&f.root);
    let calls = Arc::new(AtomicUsize::new(0));
    let observed = calls.clone();
    rejected(f.manager.full_comparison_start_native_for(
        &f.lease, &f.models, f.epoch, true, FullComparisonProtocol::SceneV4, Fixture::input(&uuid().unwrap()),
        move |_| { observed.fetch_add(1, Ordering::SeqCst); Ok(true) },
    ), "EvaluationRunLimit");
    assert_eq!(calls.load(Ordering::SeqCst), 0);
    assert_eq!(inventory(&f.root), before);
    assert_eq!(f.sequence(), 0);

    for version in [1, 2] {
        let g = Fixture::new();
        let client = uuid().unwrap();
        g.metadata(version, &client);
        let before = inventory(&g.root);
        rejected(g.manager.full_comparison_start_native_for(
            &g.lease, &g.models, g.epoch, true, FullComparisonProtocol::SceneV4, Fixture::input(&client),
            |_| panic!("cross-protocol client must never reach consent"),
        ), "InvalidEvaluationInput");
        assert_eq!(inventory(&g.root), before);
        assert_eq!(g.sequence(), 0);
    }
}

#[test]
fn protocol_tokens_never_open_resume_cancel_close_or_grant_a_reader_in_the_other_protocol() {
    let f = Fixture::new();
    let a = uuid().unwrap();
    let b = uuid().unwrap();
    let ar = f.metadata(2, &a);
    let br = f.metadata(3, &b);
    let old = f.lookup(FullComparisonProtocol::LiteralV3, &a);
    let scene = f.lookup(FullComparisonProtocol::SceneV4, &b);
    let before = inventory(&f.root);
    for (wrong, rightful, status, run) in [
        (FullComparisonProtocol::LiteralV3, FullComparisonProtocol::SceneV4, &scene, &br),
        (FullComparisonProtocol::SceneV4, FullComparisonProtocol::LiteralV3, &old, &ar),
    ] {
        rejected(f.manager.full_comparison_status_native_for(&f.lease, f.epoch, true, wrong, token(status)), "UnknownEvaluationRun");
        rejected(f.manager.full_comparison_open_native_for(&f.lease, f.epoch, true, wrong, run), "UnknownEvaluationRun");
        rejected(f.manager.full_comparison_resume_native_for(
            &f.lease, &f.models, f.epoch, true, wrong,
            FullComparisonNativeResume { run_token: token(status).into(), max_new_scenes: 1 },
            |_| panic!("wrong protocol must not reach consent"),
        ), "UnknownEvaluationRun");
        rejected(f.manager.full_comparison_cancel_native_for(&f.lease, f.epoch, true, wrong, token(status), 1), "UnknownEvaluationRun");
        rejected(f.manager.full_comparison_close_native_for(&f.lease, f.epoch, false, wrong, token(status)), "UnknownEvaluationRun");
        rejected(f.manager.full_comparison_pick_native_for(&f.lease, f.epoch, true, wrong, &uuid().unwrap(), run,
            || panic!("wrong protocol must not reach picker consent")), "UnknownEvaluationRun");
        assert_eq!(f.manager.full_comparison_status_native_for(&f.lease, f.epoch, true, rightful, token(status)).unwrap()["run_id"], run.as_str());
    }
    assert_eq!(inventory(&f.root), before);
    let baseline_client = uuid().unwrap();
    f.metadata(1, &baseline_client);
    let baseline = f.manager.full_comparison_lookup(&f.lease, f.epoch, true, &baseline_client).unwrap();
    let with_baseline = inventory(&f.root);
    rejected(f.manager.full_comparison_status_native_for(&f.lease, f.epoch, true,
        FullComparisonProtocol::SceneV4, token(&baseline)), "UnknownEvaluationRun");
    rejected(f.manager.full_comparison_status(&f.lease, f.epoch, true, token(&scene)), "UnknownEvaluationRun");
    let foreign = WindowLease::default();
    let foreign_epoch = foreign.begin().unwrap();
    assert_eq!(foreign_epoch, f.epoch);
    rejected(f.manager.full_comparison_status_native_for(&foreign, f.epoch, true,
        FullComparisonProtocol::SceneV4, token(&scene)), "UnknownEvaluationRun");
    rejected(f.manager.full_comparison_status_native_for(&f.lease, f.epoch, false,
        FullComparisonProtocol::SceneV4, token(&scene)), "Forbidden");
    assert_eq!(inventory(&f.root), with_baseline);
    assert_eq!(f.sequence(), 0);
}

#[test]
fn held_scene_consent_retry_and_operation_cancel_keep_the_original_request_without_reservation() {
    let f = Fixture::new();
    let assets = f.assets();
    let client = uuid().unwrap();
    let (entered, observe) = mpsc::sync_channel(1);
    let (release, wait) = mpsc::sync_channel(1);
    let pending = f.manager.full_comparison_start_native_for(
        &f.lease, &f.models, f.epoch, true, FullComparisonProtocol::SceneV4, Fixture::input(&client),
        move |_| {
            entered.send(()).map_err(|_| "Interrupted".to_owned())?;
            wait.recv_timeout(Duration::from_secs(60)).map_err(|_| "Interrupted".to_owned())?;
            Ok(true)
        },
    ).unwrap();
    let entry = observe.recv_timeout(Duration::from_secs(30));
    let held = f.manager.full_comparison_status_native_for(&f.lease, f.epoch, true, FullComparisonProtocol::SceneV4, token(&pending));
    let sequence = f.sequence();
    let retry = f.manager.full_comparison_start_native_for(
        &f.lease, &f.models, f.epoch, true, FullComparisonProtocol::SceneV4, Fixture::input(&client),
        |_| panic!("idempotent held retry must reuse original consent"),
    );
    let stale_cancel = f.manager.full_comparison_cancel_native_for(&f.lease, f.epoch, true, FullComparisonProtocol::SceneV4,
        token(&pending), pending["operation_id"].as_u64().unwrap() + 1);
    let cancelled = f.manager.full_comparison_cancel_native_for(&f.lease, f.epoch, true, FullComparisonProtocol::SceneV4,
        token(&pending), pending["operation_id"].as_u64().unwrap());
    // Release even if an assertion below fails; no stranded consent on failure.
    let _ = release.send(());
    assert!(entry.is_ok());
    assert_eq!(held.unwrap()["phase"], "awaiting_confirmation");
    assert_eq!(sequence, 0);
    rejected(stale_cancel, "StaleEvaluationOperation");
    let retry = retry.unwrap();
    assert_eq!(retry["run_id"], pending["run_id"]);
    assert_eq!(retry["run_token"], pending["run_token"]);
    assert_eq!(retry["operation_id"], pending["operation_id"]);
    cancelled.unwrap();
    let stopped = f.done(FullComparisonProtocol::SceneV4, token(&pending));
    assert_eq!(stopped["error"], "Cancelled");
    assert_eq!(stopped["report_ready"], false);
    assert_eq!(f.sequence(), 0);
    assert_eq!(f.assets(), assets);
}

#[test]
fn actual_denied_scene_prefix_mismatch_and_retained_budget_fail_before_resume_consent() {
    for source_fault in [true, false] {
        let f = Fixture::new();
        let denied = f.deny(FullComparisonProtocol::SceneV4, &uuid().unwrap());
        let leaf = f.runs().join(denied["run_id"].as_str().unwrap());
        if source_fault {
            let path = leaf.join("work/run.json");
            let mut value: Value = serde_json::from_slice(&fs::read(&path).unwrap()).unwrap();
            value["binding"]["source_sha256"] = json!("0".repeat(64));
            fs::write(path, serde_json::to_vec(&value).unwrap()).unwrap();
        } else {
            // Existing retained-run budget oracle, owned synthetic bytes only.
            for n in 0..3 {
                let file = fs::File::create(leaf.join(format!("owned-budget-{n}.bin"))).unwrap();
                file.set_len(12 * 1024 * 1024).unwrap();
                file.sync_all().unwrap();
            }
        }
        let before = inventory(&f.root);
        let expected = if source_fault { "EvaluationIntegrity" } else { "EvaluationBudget" };
        match f.manager.full_comparison_resume_native_for(
            &f.lease, &f.models, f.epoch, true, FullComparisonProtocol::SceneV4,
            FullComparisonNativeResume { run_token: token(&denied).into(), max_new_scenes: 1 },
            |_| panic!("retained source/budget refusal must precede new consent"),
        ) {
            Err(error) => assert_eq!(error, expected),
            Ok(initial) => {
                let terminal = f.done(FullComparisonProtocol::SceneV4, token(&initial));
                assert_eq!(terminal["error"], expected);
                assert_eq!(terminal["report_ready"], false);
            }
        }
        assert_eq!(inventory(&f.root), before);
        assert_eq!(f.sequence(), 0);
        assert!(f.models.cleanup_complete());
    }
}

#[test]
fn actual_denied_native4_managed_reader_is_empty_read_only_and_cannot_reconstruct_a_completed_run() {
    let f = Fixture::new();
    let denied = f.deny(FullComparisonProtocol::SceneV4, &uuid().unwrap());
    let run = denied["run_id"].as_str().unwrap();
    let before = inventory(&f.root);
    let reader = uuid().unwrap();
    f.manager.full_comparison_pick_native_for(&f.lease, f.epoch, true, FullComparisonProtocol::SceneV4,
        &reader, run, || Ok(true)).unwrap();
    let ready = f.read_done(&reader);
    assert_eq!(ready["phase"], "ready", "{ready}");
    assert_eq!(ready["read_only"], true);
    assert_eq!(ready["execution_available"], false);
    let source = f.manager.comparison_source(&f.lease, f.epoch, true, token(&ready)).unwrap();
    let summary = f.manager.comparison_summary(&f.lease, f.epoch, true, token(&ready)).unwrap();
    assert_eq!(source["source"]["protocol_version"], 4);
    assert_eq!(source["source"]["rows"], json!([]));
    assert_eq!(summary["snapshot"]["protocol_version"], 4);
    assert_eq!(summary["snapshot"]["report"]["completed"], false);
    assert_eq!(summary["snapshot"]["report"]["completed_scenes"], 0);
    assert_eq!(summary["snapshot"]["report"]["turns"], json!([]));
    assert_eq!(summary["snapshot"]["report"]["human_reviewed"], 0);
    assert_eq!(summary["snapshot"]["report"]["quality_accepted"], false);
    f.manager.comparison_close(&f.lease, f.epoch, &reader, Some(token(&ready))).unwrap();
    assert_eq!(inventory(&f.root), before);
    assert_eq!(f.sequence(), 0);
}

#[test]
fn separate_actual_scripted_scene_source_is_raw_readable_but_both_selected_lanes_refuse_before_consent() {
    let f = Fixture::new();
    let path = f.root.join("actual-scripted-scene");
    let report = scene_v4::run_comparison(&path, false, core::ComparisonKind::ContinuousRollout,
        &Cancellation::default(), 1, LaneFactory::ScriptedBaseline, None).unwrap();
    assert_eq!((report.completed_scenes, report.turns.len()), (1, 12));
    let source_before = inventory(&path);
    let reader = uuid().unwrap();
    let selected = path.clone();
    f.manager.comparison_pick(&f.lease, f.epoch, true, &reader, move || Ok(Some(selected))).unwrap();
    let ready = f.read_done(&reader);
    assert_eq!(ready["phase"], "ready", "{ready}");
    let summary = f.manager.comparison_summary(&f.lease, f.epoch, true, token(&ready)).unwrap();
    assert_eq!(summary["snapshot"]["protocol_version"], 4);
    assert_eq!(summary["snapshot"]["report"], serde_json::to_value(&report).unwrap());
    assert_eq!(summary["snapshot"]["unavailable"], json!(["selected_protocol4_rerun_not_implemented"]));
    for lane in [SelectedInputLane::ScriptedBaseline, SelectedInputLane::ApprovedNative] {
        let client = uuid().unwrap();
        let before = inventory(&f.root);
        f.manager.selected_prepare(&f.lease, &f.models, f.epoch, true, SelectedPrepareInput {
            client_id: client.clone(), reader_client_id: reader.clone(), run_token: token(&ready).into(),
            binding: ready["binding"].as_str().unwrap().into(), turn_id: "courier-01".into(), arm: Arm::Left, lane,
        }, |_| panic!("Protocol4 selected refusal must precede consent")).unwrap();
        let terminal = f.wait(|| f.manager.selected_status(&f.lease, f.epoch, true, &client));
        assert_eq!(terminal["phase"], "failed");
        assert_eq!(terminal["error"], "NativeUnavailable");
        assert!(terminal["plan_token"].is_null() && terminal["run_token"].is_null() && terminal["run_id"].is_null());
        assert_eq!(terminal["cleanup_required"], false);
        assert!(!f.manager.selected_root().exists());
        assert_eq!(inventory(&f.root), before);
        assert_eq!(f.sequence(), 0);
    }
    f.manager.comparison_close(&f.lease, f.epoch, &reader, Some(token(&ready))).unwrap();
    assert_eq!(inventory(&path), source_before);
}
