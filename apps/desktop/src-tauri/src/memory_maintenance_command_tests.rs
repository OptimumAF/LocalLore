// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Actual adapter/broker/Host/SQLite, model-free. Requires coordinator module wiring.
use super::*;
use locallore::{
    contracts::{Command, Intent, Seed},
    engine::Engine,
};
use locallore_storage::Store;
use std::{
    path::PathBuf,
    sync::{
        atomic::{AtomicU64, Ordering},
        mpsc,
    },
    time::{Duration, Instant},
};
static NEXT: AtomicU64 = AtomicU64::new(0);
struct Fixture {
    root: PathBuf,
    engine: Engine,
    host: Arc<Host>,
    session: String,
    lease: Arc<WindowLease>,
    broker: Arc<ArchiveBroker>,
    epoch: u64,
}
impl Fixture {
    fn new() -> Self {
        let root = std::env::temp_dir().join(format!(
            "locallore-native-maintenance-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&root).unwrap();
        let path = root.join("synthetic.sqlite");
        let mut store = Store::open_application(&path).unwrap();
        let seed: Seed =
            serde_json::from_str(include_str!("../../../../fixtures/lantern_quay.json")).unwrap();
        let scope = seed.scope.clone();
        store
            .create_story("Synthetic memory controls", seed)
            .unwrap();
        let empty = store.resume(&scope).unwrap().engine;
        let request = empty.request(
            "fixture-wait",
            Intent::Actions(vec![Command::Wait { ticks: 1 }]),
        );
        let proposal = Engine::proposal(&request).unwrap();
        let receipt = empty.preview(&request, &proposal).unwrap();
        store.begin_turn(&request).unwrap();
        store.commit_prepared(&receipt).unwrap();
        let engine = store.resume(&scope).unwrap().engine;
        let host = Arc::new(locallore_workspace::open(&path, false).unwrap());
        let selected = host.call(
            &serde_json::to_vec(&json!({"version":1,"command":{"op":"resume","scope":scope}}))
                .unwrap(),
        );
        assert_eq!(selected["status"], "ok");
        let session = selected["data"]["session"].as_str().unwrap().to_owned();
        let lease = Arc::new(WindowLease::default());
        let epoch = lease.begin().unwrap();
        Self {
            root,
            engine,
            host,
            session,
            lease,
            broker: Arc::new(ArchiveBroker::default()),
            epoch,
        }
    }
    fn input(&self, action: &str) -> Value {
        json!({"session":self.session,"scope":self.engine.scope(),"expected_head":self.engine.revision(),"action":action})
    }
    fn start(&self, action: &str) -> Value {
        start_owned(
            self.host.clone(),
            self.lease.clone(),
            self.broker.clone(),
            self.epoch,
            StartRequest::parse(self.input(action)).unwrap(),
        )
        .unwrap()
    }
    fn wait(&self, started: Value) -> Value {
        let id = started["operation_id"].as_u64().unwrap();
        let deadline = Instant::now() + Duration::from_secs(5);
        loop {
            let value = self.broker.status(&self.lease, self.epoch, id).unwrap();
            if value["running"] == false {
                self.broker.drain(self.epoch);
                return value;
            }
            assert!(
                Instant::now() < deadline,
                "bounded owned worker must finish"
            );
            std::thread::sleep(Duration::from_millis(2));
        }
    }
    fn run(&self, action: &str) -> Value {
        let value = self.wait(self.start(action));
        assert_eq!(value["phase"], "completed", "{value}");
        let result = &value["result"];
        assert_eq!(result["kind"], "memory_maintenance");
        assert_eq!(result["session"], self.session);
        assert_eq!(result["scope"], json!(self.engine.scope()));
        assert_eq!(result["expected_head"], self.engine.revision());
        assert_eq!(result["action"], action);
        assert!(serde_json::to_vec(result).unwrap().len() <= MAX_REPLY);
        result["maintenance"].clone()
    }
    fn canon(&self) {
        let actual = Store::open_application(&self.root.join("synthetic.sqlite"))
            .unwrap()
            .resume(self.engine.scope())
            .unwrap()
            .engine;
        assert_eq!(actual.canonical_bytes(), self.engine.canonical_bytes());
        assert_eq!(actual.receipts(), self.engine.receipts());
    }
}
impl Drop for Fixture {
    fn drop(&mut self) {
        self.broker.retire(self.epoch);
        self.broker.drain(self.epoch);
        let old = std::mem::replace(&mut self.host, Arc::new(Host::new(false)));
        old.close_all();
        drop(old);
        std::fs::remove_dir_all(&self.root).unwrap();
    }
}
#[test]
fn closed_input_rejects_actor_grants_paths_unknown_actions_and_bounds() {
    let good = json!({"session":"session-1","scope":{"story":"synthetic","branch":"main"},"expected_head":1,"action":"status"});
    assert!(StartRequest::parse(good.clone()).is_ok());
    for field in ["observer", "player", "grant", "path", "sql", "job_id"] {
        let mut bad = good.clone();
        bad[field] = json!("forbidden");
        assert!(matches!(StartRequest::parse(bad), Err(e) if e=="InvalidInput"));
    }
    for value in [json!(-1), json!(1.5), json!(MAX_INTEGER + 1), json!("1")] {
        let mut bad = good.clone();
        bad["expected_head"] = value;
        assert!(StartRequest::parse(bad).is_err());
    }
    for value in ["restart", "repair", "sql", ""] {
        let mut bad = good.clone();
        bad["action"] = json!(value);
        assert!(StartRequest::parse(bad).is_err());
    }
    let mut bad = good.clone();
    bad["scope"]["observer"] = json!("omniscient");
    assert!(StartRequest::parse(bad).is_err());
    let mut bad = good;
    bad["scope"]["story"] = json!("a".repeat(65));
    assert!(StartRequest::parse(bad).is_err());
}
#[test]
fn actual_shared_status_admit_cancel_prune_step_preserve_canon() {
    let f = Fixture::new();
    let before = std::fs::read(f.root.join("synthetic.sqlite")).unwrap();
    assert!(f.run("status")["job"].is_null());
    assert_eq!(
        std::fs::read(f.root.join("synthetic.sqlite")).unwrap(),
        before
    );
    assert_eq!(f.run("admit")["job"]["status"], "ready");
    assert_eq!(f.run("cancel")["job"]["status"], "cancelled");
    // Passive status and admission do not silently resurrect a terminal job.
    assert_eq!(f.run("status")["job"]["status"], "cancelled");
    assert_eq!(f.run("admit")["job"]["status"], "cancelled");
    assert!(f.run("prune")["job"].is_null());
    assert_eq!(f.run("admit")["job"]["status"], "ready");
    let step = f.run("step");
    assert_eq!(step["job"]["status"], "complete");
    assert_eq!(step["job"]["next_from"], f.engine.revision());
    f.canon();
}
#[test]
fn shared_worker_busy_and_stop_are_external_to_host_lock() {
    let f = Fixture::new();
    let (entered, seen) = mpsc::sync_channel(1);
    let (release, released) = mpsc::sync_channel(1);
    let busy = f
        .broker
        .start(f.lease.clone(), f.epoch, move |w| {
            entered.send(()).unwrap();
            released.recv_timeout(Duration::from_secs(5)).unwrap();
            w.check()?;
            Ok(json!({"version":1}))
        })
        .unwrap();
    seen.recv_timeout(Duration::from_secs(5)).unwrap();
    let id = busy["operation_id"].as_u64().unwrap();
    let result = start_owned(
        f.host.clone(),
        f.lease.clone(),
        f.broker.clone(),
        f.epoch,
        StartRequest::parse(f.input("status")).unwrap(),
    );
    // Always release the owned gate before asserting, including failure paths.
    f.broker.cancel(&f.lease, f.epoch, id).unwrap();
    release.send(()).unwrap();
    let stopped = f.wait(busy);
    assert!(matches!(result, Err(e) if e=="ArchiveBusy"));
    assert_eq!(stopped["error"], "Cancelled");
    assert!(f.run("status")["job"].is_null());
    f.canon();
}
#[test]
fn stale_and_retired_native_owners_cannot_admit() {
    let f = Fixture::new();
    let mut request = StartRequest::parse(f.input("admit")).unwrap();
    request.expected_head += 1;
    let started = start_owned(
        f.host.clone(),
        f.lease.clone(),
        f.broker.clone(),
        f.epoch,
        request,
    )
    .unwrap();
    assert_eq!(f.wait(started)["error"], "Stale");
    assert!(f.run("status")["job"].is_null());
    let closed = f.lease.invalidate(&format!("main-{}", f.epoch)).unwrap();
    assert!(
        matches!(start_owned(f.host.clone(), f.lease.clone(), f.broker.clone(), f.epoch, StartRequest::parse(f.input("admit")).unwrap()), Err(e) if e=="Closed")
    );
    f.lease.finish_close(closed, || {});
    f.canon();
}

#[test]
fn passive_stale_ready_row_requires_cancel_before_prune() {
    let mut f = Fixture::new();
    assert_eq!(f.run("admit")["job"]["status"], "ready");
    let mut writer = Store::open_application(&f.root.join("synthetic.sqlite")).unwrap();
    let request = f.engine.request(
        "advance-for-stale-job",
        Intent::Actions(vec![Command::Wait { ticks: 1 }]),
    );
    let proposal = Engine::proposal(&request).unwrap();
    let receipt = f.engine.preview(&request, &proposal).unwrap();
    writer.begin_turn(&request).unwrap();
    writer.commit_prepared(&receipt).unwrap();
    f.engine = writer.resume(f.engine.scope()).unwrap().engine;
    drop(writer);
    let opened = f.host.call(&serde_json::to_vec(&json!({"version":1,"command":{"op":"open","session":f.session,"scope":f.engine.scope()}})).unwrap());
    assert_eq!(opened["status"], "ok");
    assert_eq!(f.run("status")["job"]["status"], "stale");
    let refused = f.wait(f.start("prune"));
    assert_eq!(
        refused["error"], "Busy",
        "passive stale is not a persisted terminal transition"
    );
    assert_eq!(f.run("cancel")["job"]["status"], "cancelled");
    assert!(f.run("prune")["job"].is_null());
    f.canon();
}
