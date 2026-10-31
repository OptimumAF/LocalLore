// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen at f77c36e2, before the service implementation. UNCOMPILED / UNRUN.
//! Real shared scripted comparison/native-service tests, NOT IPC, WebView,
//! native inference, quality or desktop-control evidence. Synthetic files stay local.
//! Root: cargo test --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml evaluation::comparison_run::review_tests:: -- --nocapture --test-threads=1
use super::*;
mod budget_review_tests;
mod managed_read_review_tests;
use crate::{evaluation::EvaluationManager, lease::WindowLease, models::ModelManager};
use locallore_eval::local_lane::comparison::{self as producer, literal_v3};
use serde_json::{json, Value};
use std::{
    collections::BTreeMap,
    fs,
    path::{Path, PathBuf},
    sync::{Arc, OnceLock},
    time::{Duration, Instant},
};

type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;
fn inventory(root: &Path) -> Inventory {
    fn walk(root: &Path, path: &Path, depth: usize, size: &mut usize, out: &mut Inventory) {
        assert!(depth <= 12 && out.len() < 8192);
        let metadata = fs::symlink_metadata(path).unwrap();
        assert!(!metadata.file_type().is_symlink());
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt;
            assert_eq!(metadata.file_attributes() & 0x400, 0);
        }
        let key = path.strip_prefix(root).unwrap().to_owned();
        if metadata.is_dir() {
            assert!(out.insert(key, None).is_none());
            for entry in fs::read_dir(path).unwrap() {
                walk(root, &entry.unwrap().path(), depth + 1, size, out);
            }
        } else {
            assert!(metadata.is_file() && metadata.len() <= 16 * 1024 * 1024);
            let bytes = fs::read(path).unwrap();
            *size = size.checked_add(bytes.len()).unwrap();
            assert!(*size <= 128 * 1024 * 1024);
            assert!(out.insert(key, Some(bytes)).is_none());
        }
    }
    let mut result = Inventory::new();
    walk(root, root, 0, &mut 0, &mut result);
    result
}
fn refusal<T>(value: std::result::Result<T, String>, expected: &str) {
    match value {
        Err(error) => assert_eq!(error, expected),
        Ok(_) => panic!("expected closed refusal {expected}"),
    }
}
struct Fixture {
    manager: Arc<EvaluationManager>,
    models: Arc<ModelManager>,
    lease: Arc<WindowLease>,
    epoch: u64,
}
impl Fixture {
    fn new() -> Self {
        let root =
            std::env::temp_dir().join(format!("full-comparison-service-{}", uuid().unwrap()));
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
    fn input(client: &str, kind: producer::ComparisonKind, batch: usize) -> FullComparisonStart {
        FullComparisonStart {
            client_id: client.into(),
            kind,
            max_new_scenes: batch,
        }
    }
    fn start(&self, client: &str, kind: producer::ComparisonKind, batch: usize) -> Value {
        self.manager
            .full_comparison_start(
                &self.lease,
                self.epoch,
                true,
                Self::input(client, kind, batch),
            )
            .unwrap()
    }
    fn status(&self, token: &str) -> Value {
        self.manager
            .full_comparison_status(&self.lease, self.epoch, true, token)
            .unwrap()
    }
    fn done(&self, token: &str) -> Value {
        // Fixture scheduling: resume3 has18 missing scenario turns/both arms and many SQLite prefix/cold validations; no product/runtime/consent/cancel/resource/quality deadline changes.
        let deadline = Instant::now() + Duration::from_secs(600);
        loop {
            let value = self.status(token);
            if value["running"] == false {
                return value;
            }
            assert!(
                Instant::now() < deadline,
                "bounded full-comparison service wait: {value}"
            );
            std::thread::sleep(Duration::from_millis(5));
        }
    }
    fn close(&self, token: &str) {
        self.manager
            .full_comparison_close(&self.lease, self.epoch, false, token)
            .unwrap();
    }
    fn reopen_epoch(&mut self) {
        let closed = self
            .lease
            .invalidate(&format!("main-{}", self.epoch))
            .unwrap();
        self.manager.retire(self.epoch);
        self.manager.drain(self.epoch);
        self.lease.finish_close(closed, || {});
        self.epoch = self.lease.begin().unwrap();
    }
    fn opened(&self, run: &str) -> Value {
        let value = self
            .manager
            .full_comparison_open(&self.lease, self.epoch, true, run)
            .unwrap();
        self.done(value["run_token"].as_str().unwrap())
    }
}
impl Drop for Fixture {
    fn drop(&mut self) {
        self.manager.test_case("release-boundary").unwrap();
        if let Some(closed) = self.lease.invalidate(&format!("main-{}", self.epoch)) {
            self.manager.retire(self.epoch);
            self.manager.drain(self.epoch);
            self.lease.finish_close(closed, || {});
        }
        assert!(self.models.cleanup_complete());
        // Do not delete source/checkpoint evidence, even on test failure.
    }
}
fn token(value: &Value) -> &str {
    value["run_token"].as_str().unwrap()
}
fn id(value: &Value) -> &str {
    value["run_id"].as_str().unwrap()
}
fn report(f: &Fixture, run: &str) -> Value {
    serde_json::to_value(literal_v3::inspect_comparison(&f.root().join(run).join("work")).unwrap())
        .unwrap()
}
fn published(status: &Value, scenes: u64, complete: bool) {
    assert_eq!(status["protocol_version"], 3);
    assert_eq!(status["input_lane"], "scripted_baseline");
    assert_eq!(status["running"], false);
    assert_eq!(status["error"], Value::Null);
    assert_eq!(status["report_ready"], true);
    assert_eq!(status["completed_scenes"], scenes);
    assert_eq!(status["completed"], complete);
    assert_eq!(status["source_matches"], true);
}
// Reuse one genuine SERVICE-produced rollout prefix. Copies preserve all bytes;
// only the explicitly hostile diagnostic tests mutate their own isolated copies.
fn saved() -> &'static (PathBuf, String, String) {
    static SAVED: OnceLock<(PathBuf, String, String)> = OnceLock::new();
    SAVED.get_or_init(|| {
        let f = Fixture::new();
        let client = uuid().unwrap();
        let start = f.start(&client, producer::ComparisonKind::ContinuousRollout, 1);
        let done = f.done(token(&start));
        published(&done, 1, false);
        let run = id(&done).to_owned();
        f.close(token(&done));
        (f.root().join(&run), run, client)
    })
}
fn copied() -> (Fixture, String, String) {
    let f = Fixture::new();
    let (source, run, client) = saved();
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
fn paired_one_then_three_keeps_actual_reference_and_completed_resume_read_only() {
    let f = Fixture::new();
    let client = uuid().unwrap();
    let first = f.start(&client, producer::ComparisonKind::PairedSnapshots, 1);
    let first = f.done(token(&first));
    published(&first, 1, false);
    let run = id(&first).to_owned();
    let cap = token(&first).to_owned();
    let leaf = f.root().join(&run);
    let reference = inventory(&leaf.join("reference-source"));
    assert_eq!(report(&f, &run)["turns"].as_array().unwrap().len(), 12);
    f.manager
        .full_comparison_resume(&f.lease, f.epoch, true, &cap, 3)
        .unwrap();
    let done = f.done(&cap);
    published(&done, 4, true);
    assert!(inventory(&leaf.join("reference-source")) == reference);
    let actual = report(&f, &run);
    assert_eq!(actual["version"], 3);
    assert_eq!(actual["turns"].as_array().unwrap().len(), 48);
    assert_eq!(
        actual["arms"],
        serde_json::to_value(locallore_eval::memory_comparison_v3::current_arm_descriptors()).unwrap()
    );
    let before = inventory(&leaf);
    f.manager
        .full_comparison_resume(&f.lease, f.epoch, true, &cap, 4)
        .unwrap();
    published(&f.done(&cap), 4, true);
    assert!(inventory(&leaf) == before);
    f.close(&cap);
    assert!(f.manager.cleanup_complete());
}

#[test]
fn rollout_four_exact_client_retry_conflict_and_lookup_never_execute_again() {
    let f = Fixture::new();
    let client = uuid().unwrap();
    let start = f.start(&client, producer::ComparisonKind::ContinuousRollout, 4);
    let done = f.done(token(&start));
    published(&done, 4, true);
    let leaf = f.root().join(id(&done));
    assert!(!leaf.join("reference-source").exists());
    let actual = report(&f, id(&done));
    assert_eq!(actual["turns"].as_array().unwrap().len(), 48);
    let before = inventory(&f.root());
    let retry = f.start(&client, producer::ComparisonKind::ContinuousRollout, 4);
    assert_eq!(retry["run_id"], done["run_id"]);
    assert_eq!(retry["operation_id"], done["operation_id"]);
    assert_eq!(retry["running"], false);
    let lookup = f
        .manager
        .full_comparison_lookup(&f.lease, f.epoch, true, &client)
        .unwrap();
    assert_eq!(lookup["run_id"], done["run_id"]);
    for (kind, batch) in [
        (producer::ComparisonKind::PairedSnapshots, 4),
        (producer::ComparisonKind::ContinuousRollout, 1),
    ] {
        refusal(
            f.manager.full_comparison_start(
                &f.lease,
                f.epoch,
                true,
                Fixture::input(&client, kind, batch),
            ),
            "InvalidEvaluationInput",
        );
    }
    assert!(inventory(&f.root()) == before);
    f.close(token(&done));
}

#[test]
fn cold_lookup_open_new_epoch_and_catalog_are_read_only_with_old_token_fenced() {
    let (mut f, run, client) = copied();
    let before = inventory(&f.root());
    let lookup = f
        .manager
        .full_comparison_lookup(&f.lease, f.epoch, true, &client)
        .unwrap();
    assert_eq!(lookup["run_id"], run);
    assert_eq!(lookup["running"], false);
    let ready = f.opened(&run);
    published(&ready, 1, false);
    let old = token(&ready).to_owned();
    f.reopen_epoch();
    refusal(
        f.manager
            .full_comparison_status(&f.lease, f.epoch, true, &old),
        "UnknownEvaluationRun",
    );
    let catalog = f
        .manager
        .full_comparison_catalog(&f.lease, f.epoch, true)
        .unwrap();
    assert_eq!(catalog["kind"], "comparison_run_catalog");
    assert_eq!(catalog["runs"].as_array().unwrap().len(), 1);
    assert_eq!(catalog["runs"][0]["run_id"], run);
    let current = f.opened(&run);
    published(&current, 1, false);
    assert_ne!(token(&current), old);
    f.close(token(&current));
    assert!(inventory(&f.root()) == before);
}

#[test]
fn permission_invalid_identifiers_and_scene_limits_refuse_without_files_or_jobs() {
    let f = Fixture::new();
    let before = inventory(f.manager.root.parent().unwrap());
    let client = uuid().unwrap();
    refusal(
        f.manager.full_comparison_catalog(&f.lease, f.epoch, false),
        "Forbidden",
    );
    refusal(
        f.manager.full_comparison_start(
            &f.lease,
            f.epoch,
            false,
            Fixture::input(&client, producer::ComparisonKind::ContinuousRollout, 1),
        ),
        "Forbidden",
    );
    for batch in [0, 5] {
        refusal(
            f.manager.full_comparison_start(
                &f.lease,
                f.epoch,
                true,
                Fixture::input(&client, producer::ComparisonKind::ContinuousRollout, batch),
            ),
            "InvalidEvaluationInput",
        );
    }
    for bad in ["../other", "not-a-uuid"] {
        refusal(
            f.manager
                .full_comparison_lookup(&f.lease, f.epoch, true, bad),
            "InvalidEvaluationInput",
        );
        refusal(
            f.manager.full_comparison_open(&f.lease, f.epoch, true, bad),
            "InvalidEvaluationInput",
        );
    }
    assert!(inventory(f.manager.root.parent().unwrap()) == before);
    assert!(f.manager.cleanup_complete());
}

#[test]
fn wrong_native_index_kind_and_corrupt_shared_source_cannot_be_opened_or_resumed() {
    for fault in ["index", "manifest", "checkpoint"] {
        let (f, run, _) = copied();
        let leaf = f.root().join(&run);
        let file = leaf.join(match fault {
            "index" => "desktop.json",
            "manifest" => "work/run.json",
            _ => "work/left/attempt-00.json",
        });
        if fault == "index" {
            let mut actual: Value = serde_json::from_slice(&fs::read(&file).unwrap()).unwrap();
            actual["kind"] = json!("curated");
            fs::write(&file, serde_json::to_vec(&actual).unwrap()).unwrap();
        } else {
            assert!(file.is_file());
            fs::write(&file, b"{invalid synthetic owned diagnostic").unwrap();
        }
        let before = inventory(&f.root());
        match f
            .manager
            .full_comparison_open(&f.lease, f.epoch, true, &run)
        {
            Err(error) => assert_eq!(error, "EvaluationIntegrity"),
            Ok(start) => {
                let stopped = f.done(token(&start));
                assert_eq!(stopped["error"], "EvaluationIntegrity");
                assert_eq!(stopped["report_ready"], false);
                match f
                    .manager
                    .full_comparison_resume(&f.lease, f.epoch, true, token(&stopped), 1)
                {
                    Err(error) => assert_eq!(error, "EvaluationIntegrity"),
                    Ok(resume) => {
                        let failed = f.done(token(&resume));
                        assert_eq!(failed["error"], "EvaluationIntegrity");
                        assert_eq!(failed["report_ready"], false);
                    }
                }
                f.close(token(&stopped));
            }
        }
        assert!(inventory(&f.root()) == before);
        assert!(f.manager.cleanup_complete());
    }
}

#[test]
fn held_parent_job_cancel_stale_operation_and_retirement_cannot_publish_late() {
    let mut f = Fixture::new();
    f.manager.test_case("hold-boundary").unwrap();
    let client = uuid().unwrap();
    let first = f.start(&client, producer::ComparisonKind::ContinuousRollout, 4);
    let cap = token(&first).to_owned();
    let op = first["operation_id"].as_u64().unwrap();
    assert_eq!(f.status(&cap)["running"], true);
    let retry = f.start(&client, producer::ComparisonKind::ContinuousRollout, 4);
    assert_eq!(retry["operation_id"], op);
    refusal(
        f.manager.start(&f.lease, f.epoch, None, "one"),
        "EvaluationBusy",
    );
    refusal(
        f.manager.full_comparison_start(
            &f.lease,
            f.epoch,
            true,
            Fixture::input(
                &uuid().unwrap(),
                producer::ComparisonKind::ContinuousRollout,
                1,
            ),
        ),
        "EvaluationBusy",
    );
    refusal(
        f.manager
            .full_comparison_cancel(&f.lease, f.epoch, true, &cap, op + 1),
        "StaleEvaluationOperation",
    );
    f.manager
        .full_comparison_cancel(&f.lease, f.epoch, true, &cap, op)
        .unwrap();
    let stopped = f.done(&cap);
    assert_eq!(stopped["completed"], false);
    f.manager.test_case("release-boundary").unwrap();
    f.close(&cap);
    f.manager.test_case("hold-boundary").unwrap();
    let next = f.start(
        &uuid().unwrap(),
        producer::ComparisonKind::ContinuousRollout,
        1,
    );
    let old_epoch = f.epoch;
    let retired_leaf = f.root().join(id(&next));
    let before_retire = inventory(&retired_leaf);
    let closed = f.lease.invalidate(&format!("main-{old_epoch}")).unwrap();
    f.manager.retire(old_epoch);
    f.manager.drain(old_epoch);
    refusal(
        f.manager
            .full_comparison_status(&f.lease, old_epoch, true, token(&next)),
        "Closed",
    );
    assert!(f.manager.cleanup_complete());
    assert!(inventory(&retired_leaf) == before_retire);
    f.lease.finish_close(closed, || {});
    f.epoch = f.lease.begin().unwrap();
    refusal(
        f.manager
            .full_comparison_status(&f.lease, f.epoch, true, token(&next)),
        "UnknownEvaluationRun",
    );
    assert!(f.manager.state().unwrap().job.is_none());
}

#[test]
fn refused_worker_spawn_leaves_no_global_job_and_lookup_does_not_retry_it() {
    let f = Fixture::new();
    let client = uuid().unwrap();
    f.manager
        .fail_spawn
        .store(true, std::sync::atomic::Ordering::SeqCst);
    refusal(
        f.manager.full_comparison_start(
            &f.lease,
            f.epoch,
            true,
            Fixture::input(&client, producer::ComparisonKind::ContinuousRollout, 1),
        ),
        "EvaluationInternal",
    );
    assert!(f.manager.cleanup_complete());
    let before = if f.root().exists() {
        Some(inventory(&f.root()))
    } else {
        None
    };
    let lookup = f
        .manager
        .full_comparison_lookup(&f.lease, f.epoch, true, &client);
    match lookup {
        Ok(value) => assert_eq!(value["running"], false),
        Err(error) => assert_eq!(error, "UnknownEvaluationRun"),
    }
    assert!(if let Some(before) = before {
        inventory(&f.root()) == before
    } else {
        !f.root().exists()
    });
    assert!(f.manager.state().unwrap().job.is_none());
}
