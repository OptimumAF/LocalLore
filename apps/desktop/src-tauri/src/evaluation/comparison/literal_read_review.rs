// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen SOURCE ONLY / UNCOMPILED / UNRUN. Actual scripted V3 source through
//! existing native reader APIs; no OS picker, provider, model or UI execution.
use super::*;
use locallore::{
    inference::Cancellation,
    inspection_query::{self, Observer, Query, View, MAX_ROWS},
};
use locallore_eval::{
    local_lane::{
        comparison::{self as producer, literal_v3},
        LaneFactory,
    },
    memory_comparison::frozen_suite,
};
use locallore_storage::Store;
use std::{
    collections::BTreeMap,
    sync::{mpsc, OnceLock},
};

type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;
fn inventory(root: &Path) -> Inventory {
    fn walk(root: &Path, p: &Path, depth: usize, total: &mut usize, out: &mut Inventory) {
        assert!(depth <= 8 && out.len() < 4096);
        let m = fs::symlink_metadata(p).unwrap();
        assert!(!m.file_type().is_symlink());
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt;
            assert_eq!(m.file_attributes() & 0x400, 0);
        }
        let rel = p.strip_prefix(root).unwrap().to_owned();
        if m.is_dir() {
            out.insert(rel, None);
            for e in fs::read_dir(p).unwrap() {
                walk(root, &e.unwrap().path(), depth + 1, total, out);
            }
        } else {
            assert!(m.is_file() && m.len() <= 8 * 1024 * 1024);
            let b = fs::read(p).unwrap();
            *total += b.len();
            assert!(*total <= 64 * 1024 * 1024);
            out.insert(rel, Some(b));
        }
    }
    let mut out = Inventory::new();
    walk(root, root, 0, &mut 0, &mut out);
    out
}
fn root(label: &str) -> PathBuf {
    let p = std::env::temp_dir().join(format!("literal-native-read-{label}-{}", uuid().unwrap()));
    fs::create_dir(&p).unwrap();
    p
}
fn sources() -> &'static Path {
    static SOURCE: OnceLock<PathBuf> = OnceLock::new();
    SOURCE
        .get_or_init(|| {
            let root = root("producer");
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
            assert_eq!((v3.completed_scenes, v3.turns.len()), (1, 12));
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
            assert_eq!((v2.completed_scenes, v2.turns.len()), (1, 12));
            root
        })
        .as_path()
}
fn copy_run(name: &str) -> PathBuf {
    let original = inventory(&sources().join(name));
    let target = root("copy");
    for (rel, b) in &original {
        match b {
            None => fs::create_dir_all(target.join(rel)).unwrap(),
            Some(b) => fs::write(target.join(rel), b).unwrap(),
        }
    }
    assert!(inventory(&target) == original);
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
        let end = Instant::now() + Duration::from_secs(30);
        loop {
            let v = self
                .manager
                .comparison_status(&self.lease, self.epoch, true, client)
                .unwrap();
            if v["running"] == false {
                return v;
            }
            assert!(Instant::now() < end, "bounded native worker fixture");
            std::thread::sleep(Duration::from_millis(5));
        }
    }
    fn pick(&self, client: &str, path: &Path) -> Value {
        let path = path.to_owned();
        self.manager
            .comparison_pick(&self.lease, self.epoch, true, client, move || {
                Ok(Some(path))
            })
            .unwrap();
        let v = self.done(client);
        assert_eq!(v["phase"], "ready", "{v}");
        v
    }
    fn close(&self, client: &str, token: Option<&str>) {
        let v = self
            .manager
            .comparison_close(&self.lease, self.epoch, client, token)
            .unwrap();
        assert_eq!(v["phase"], "closed");
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
fn err<T>(v: Result<T>) -> String {
    match v {
        Ok(_) => panic!("expected native refusal"),
        Err(e) => e,
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
fn reacquire(path: &Path, version: u16) {
    if version == 3 {
        let c = literal_v3::desktop_api::open_read_only(path).unwrap();
        literal_v3::desktop_api::summary(&c, true).unwrap();
        drop(c);
    } else {
        let c = shared::open_read_only(path).unwrap();
        shared::summary(&c, true).unwrap();
        drop(c);
    }
}

#[test]
fn affirmative_native_picker_exposes_typed_v3_and_actual_observer_store_evidence() {
    let f = Fixture::new();
    let path = copy_run("v3");
    let before = inventory(&path);
    let client = uuid().unwrap();
    let ready = f.pick(&client, &path);
    let token = ready["run_token"].as_str().unwrap();
    let binding = ready["binding"].as_str().unwrap();
    assert_eq!(ready["execution_available"], false);
    assert_eq!(ready["read_only"], true);
    let source = f
        .manager
        .comparison_source(&f.lease, f.epoch, true, token)
        .unwrap();
    assert_eq!(source["source"]["protocol_version"], 3);
    assert_eq!(source["source"]["binding"], binding);
    assert_eq!(source["source"]["execution_available"], false);
    let summary = f
        .manager
        .comparison_summary(&f.lease, f.epoch, true, token)
        .unwrap();
    assert_eq!(summary["snapshot"]["protocol_version"], 3);
    assert_eq!(summary["snapshot"]["report"]["version"], 3);
    assert_eq!(
        summary["snapshot"]["report"]["turns"]
            .as_array()
            .unwrap()
            .len(),
        12
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
    for observer in [Observer::Player, Observer::Character { id: "mira".into() }] {
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
        let actual = f
            .manager
            .comparison_evidence(
                &f.lease,
                f.epoch,
                true,
                query(token, binding, observer.clone()),
            )
            .unwrap();
        assert_eq!(
            actual["evidence"]["body"]["page"],
            serde_json::to_value(expected).unwrap()
        );
        assert_eq!(actual["evidence"]["generation_grant"], false);
        assert_eq!(
            err(f.manager.comparison_evidence(
                &f.lease,
                f.epoch,
                true,
                input(
                    token,
                    binding,
                    shared::EvidenceRequest::Capture { observer }
                )
            )),
            "Forbidden"
        );
    }
    let accepted = f
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
        accepted["evidence"]["body"]["receipt"],
        serde_json::to_value(receipt).unwrap()
    );
    let captured = f
        .manager
        .comparison_evidence(
            &f.lease,
            f.epoch,
            true,
            input(
                token,
                binding,
                shared::EvidenceRequest::Capture {
                    observer: Observer::Omniscient,
                },
            ),
        )
        .unwrap();
    assert_eq!(captured["evidence"]["body"]["kind"], "capture");
    drop(store);
    f.close(&client, Some(token));
    reacquire(&path, 3);
    assert!(inventory(&path) == before);
}

#[test]
fn v3_source_transfer_revokes_read_capability_without_minting_execution() {
    let f = Fixture::new();
    let path = copy_run("v3");
    let before = inventory(&path);
    let client = uuid().unwrap();
    let ready = f.pick(&client, &path);
    let token = ready["run_token"].as_str().unwrap();
    let binding = ready["binding"].as_str().unwrap();
    let manager_before = inventory(&f.root);
    let transferred = f.lease.dispatch(f.epoch, || {
        f.manager
            .comparison_take_source_in_gate(&f.lease, f.epoch, &client, token, binding)
    });
    let source = transferred.unwrap();
    assert_eq!(source.protocol_version(), 3);
    assert_eq!(
        f.manager
            .comparison_status(&f.lease, f.epoch, true, &client)
            .unwrap()["phase"],
        "closed"
    );
    assert_eq!(
        err(f.manager.comparison_source(&f.lease, f.epoch, true, token)),
        "UnknownEvaluationRun"
    );
    assert_eq!(
        err(f.manager.comparison_evidence(
            &f.lease,
            f.epoch,
            true,
            query(token, binding, Observer::Player)
        )),
        "UnknownEvaluationRun"
    );
    assert!(inventory(&f.root) == manager_before);
    // Release the opaque source outside the lease/metadata gates. Preparing a
    // fresh validated Core plan and explicit consent still belong to the worker.
    let (origin, transferred_binding) = source.into_origin();
    assert_eq!(origin, path);
    assert_eq!(transferred_binding, binding);
    reacquire(&path, 3);
    assert!(inventory(&path) == before);
    // No ModelManager exists here; source transfer alone creates no output.
}

#[test]
fn held_v3_picker_close_or_epoch_retirement_never_publishes_a_late_capability() {
    for retired in [false, true] {
        let mut f = Fixture::new();
        let path = copy_run("v3");
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
        let old = f.epoch;
        if retired {
            let closed = f.lease.invalidate(&format!("main-{old}")).unwrap();
            f.manager.retire(old);
            release.send(()).unwrap();
            f.manager.drain(old);
            f.lease.finish_close(closed, || {});
            f.epoch = f.lease.begin().unwrap();
            assert_eq!(
                err(f
                    .manager
                    .comparison_status(&f.lease, f.epoch, true, &client)),
                "UnknownEvaluationRun"
            );
        } else {
            let closing = f.manager.comparison_close(&f.lease, f.epoch, &client, None);
            release.send(()).unwrap();
            let closed = f.done(&client);
            assert_eq!(closing.unwrap()["phase"], "closing");
            assert_eq!(closed["phase"], "closed");
            assert!(closed["run_token"].is_null());
        }
        reacquire(&path, 3);
        assert!(inventory(&path) == before);
        let fresh_client = uuid().unwrap();
        let fresh = f.pick(&fresh_client, &path);
        let token = fresh["run_token"].as_str().unwrap();
        if retired {
            assert_eq!(
                err(f.manager.comparison_status(&f.lease, old, true, &client)),
                "Closed"
            );
        }
        assert_eq!(
            f.manager
                .comparison_status(&f.lease, f.epoch, true, &fresh_client)
                .unwrap(),
            fresh
        );
        f.close(&fresh_client, Some(token));
        reacquire(&path, 3);
        assert!(inventory(&path) == before);
    }
}

#[test]
fn v3_close_then_v2_open_keeps_protocols_typed_and_denies_the_old_token() {
    let f = Fixture::new();
    let v3 = copy_run("v3");
    let v2 = copy_run("v2");
    let before3 = inventory(&v3);
    let before2 = inventory(&v2);
    let client = uuid().unwrap();
    let first = f.pick(&client, &v3);
    let old_token = first["run_token"].as_str().unwrap();
    assert_eq!(
        f.manager
            .comparison_source(&f.lease, f.epoch, true, old_token)
            .unwrap()["source"]["protocol_version"],
        3
    );
    f.close(&client, Some(old_token));
    reacquire(&v3, 3);
    // Native client IDs identify one chooser lifecycle, including closed status.
    // A deliberate new chooser uses a new client on the SAME manager/window.
    let next_client = uuid().unwrap();
    let second = f.pick(&next_client, &v2);
    let token = second["run_token"].as_str().unwrap();
    assert_ne!(token, old_token);
    assert_eq!(
        f.manager
            .comparison_source(&f.lease, f.epoch, true, token)
            .unwrap()["source"]["protocol_version"],
        2
    );
    assert_eq!(
        f.manager
            .comparison_summary(&f.lease, f.epoch, true, token)
            .unwrap()["snapshot"]["report"]["version"],
        2
    );
    assert_eq!(
        err(f
            .manager
            .comparison_summary(&f.lease, f.epoch, true, old_token)),
        "UnknownEvaluationRun"
    );
    f.close(&next_client, Some(token));
    reacquire(&v2, 2);
    assert!(inventory(&v3) == before3);
    assert!(inventory(&v2) == before2);
}
