// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Host Open is also passive app snapshot refresh. Actual Host/Store, synthetic
//! bounded provider only; no app, native worker, model or canonical SQL writes.
use locallore::{contracts::*, engine::Engine, host::Host, inference::*, play::PlayProfile};
use locallore_storage::{Store, TurnPhase};
use serde_json::{json, Value};
use std::{
    path::PathBuf,
    sync::{atomic::{AtomicBool, AtomicU64, AtomicUsize, Ordering}, mpsc, Arc, Mutex},
    task::Poll,
    time::Duration,
};
static NEXT: AtomicU64 = AtomicU64::new(0);
struct Fixture(PathBuf);
impl Fixture {
    fn new() -> Self {
        let root = std::env::temp_dir().join(format!("locallore-open-refresh-review-{}-{}-{}",
            std::process::id(), std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)));
        std::fs::create_dir(&root).unwrap();
        Self(root)
    }
    fn path(&self) -> PathBuf { self.0.join("synthetic.sqlite") }
    fn store(&self) -> Store { Store::open_application(&self.path()).unwrap() }
}
impl Drop for Fixture { fn drop(&mut self) { std::fs::remove_dir_all(&self.0).unwrap(); } }
fn create(f: &Fixture) -> Engine {
    let seed: Seed = serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    let scope = seed.scope.clone(); let mut s = f.store();
    s.create_story("Synthetic Open refresh", seed).unwrap(); s.resume(&scope).unwrap().engine
}
fn commit(s: &mut Store, e: &Engine, key: &str) -> Engine {
    let r = e.request(key, Intent::Actions(vec![Command::Wait { ticks: 1 }]));
    let p = Engine::proposal(&r).unwrap(); let receipt = e.preview(&r, &p).unwrap();
    s.begin_turn(&r).unwrap(); s.commit_prepared(&receipt).unwrap(); s.resume(e.scope()).unwrap().engine
}
fn call(h: &Host, c: Value) -> Value { h.call(&serde_json::to_vec(&json!({"version":1,"command":c})).unwrap()) }
fn select(h: &Host, scope: &Scope) -> String {
    let v = call(h, json!({"op":"resume","scope":scope})); assert_eq!(v["status"], "ok", "{v}");
    v["data"]["session"].as_str().unwrap().into()
}
fn consent(h: &Host, session: &str, e: &Engine) {
    for command in [
        json!({"op":"trace_configure","session":session,"scope":e.scope(),"expected_head":e.revision(),"enabled":true}),
        json!({"op":"trace_capture_configure","session":session,"scope":e.scope(),"expected_head":e.revision(),"enabled":true,"consent":true}),
    ] { let v = call(h, command); assert_eq!(v["status"], "ok", "{v}"); }
}
fn details(h: &Host, session: &str, r: &Request, head: u64) -> Value {
    let v = call(h, json!({"op":"trace_capture_read","session":session,"scope":r.scope,"expected_head":head,
        "base_revision":r.expected_revision,"turn":r.turn,"attempt":1}));
    assert_eq!(v["status"], "ok", "{v}"); v["data"]["details"].clone()
}
struct Held {
    entered: mpsc::SyncSender<()>, release: Arc<Mutex<mpsc::Receiver<()>>>,
    calls: Arc<AtomicUsize>, saw_cancel: Arc<AtomicBool>,
}
impl InferenceProvider for Held {
    fn poll(&mut self, r: &GenerationRequest, cancel: &Cancellation) -> Poll<Result<Vec<u8>, Error>> {
        self.calls.fetch_add(1, Ordering::SeqCst);
        let Input::Structured { role, .. } = &r.input else { panic!("actual structured input") };
        let v = if role == "director" {
            self.entered.send(()).unwrap(); self.release.lock().unwrap().recv_timeout(Duration::from_secs(5)).unwrap();
            self.saw_cancel.store(cancel.is_cancelled(), Ordering::SeqCst);
            json!({"commands":[{"op":"wait","ticks":1}]})
        } else { assert_eq!(role, "narrator"); json!({"text":"Time passes.","event_ids":[r.revision+1],"speaker":"narrator"}) };
        Poll::Ready(Ok(serde_json::to_vec(&v).unwrap()))
    }
}
struct ReleaseOnDrop(Option<mpsc::SyncSender<()>>);
impl Drop for ReleaseOnDrop { fn drop(&mut self) { if let Some(s) = self.0.take() { let _ = s.try_send(()); } } }

#[test]
fn passive_same_source_open_preserves_running_work_capture_consent_and_ready_completion() {
    let f = Fixture::new(); let empty = create(&f); let mut store = f.store();
    let e = commit(&mut store, &empty, "prefix");
    let h = Arc::new(locallore_workspace::open(&f.path(), true).unwrap()); let session = select(&h, e.scope());
    consent(&h, &session, &e);
    let r = e.request("held-passive-refresh", Intent::FreeText { kind: PlayInputKind::Action, text: "I wait for one tide tick.".into() });
    let (entered_tx, entered_rx) = mpsc::sync_channel(1); let (release_tx, release_rx) = mpsc::sync_channel(1);
    let release_rx = Arc::new(Mutex::new(release_rx)); let calls = Arc::new(AtomicUsize::new(0));
    let saw_cancel = Arc::new(AtomicBool::new(false)); let factory_calls = calls.clone(); let factory_cancel = saw_cancel.clone();
    h.configure_fixture_provider(PlayProfile {
        id: "synthetic-passive-open".into(), model_sha256: "a".repeat(64), runtime_revision: "b".repeat(40),
        template_sha256: "c".repeat(64), worker_sha256: "d".repeat(64), profile_manifest_sha256: "e".repeat(64),
        context_tokens: 4096, director_tokens: 350, narrator_tokens: 220, deadline_ms: 5000, repair_limit: 1,
    }, Arc::new(move || Box::new(Held { entered: entered_tx.clone(), release: release_rx.clone(), calls: factory_calls.clone(), saw_cancel: factory_cancel.clone() }))).unwrap();
    let submitted = call(&h, json!({"op":"free_text","session":session,"request":r})); assert_eq!(submitted["data"]["phase"], "queued");
    std::thread::scope(|threads| {
        let worker = threads.spawn(|| call(&h, json!({"op":"prepare","session":session,"scope":r.scope,"turn":r.turn})));
        let mut release = ReleaseOnDrop(Some(release_tx)); entered_rx.recv_timeout(Duration::from_secs(5)).unwrap();
        let before = details(&h, &session, &r, e.revision()); assert_eq!(before["status"], "recorded", "{before}");
        let opened = call(&h, json!({"op":"open","session":session,"scope":e.scope()})); assert_eq!(opened["status"], "ok", "{opened}");
        assert_eq!(opened["data"]["revision"], e.revision());
        let after = details(&h, &session, &r, e.revision()); assert_eq!(after, before, "passive refresh revoked/changed existing capture");
        let running = call(&h, json!({"op":"turn_status","session":session,"scope":r.scope,"turn":r.turn}));
        assert_eq!(running["data"]["phase"], "running", "{running}");
        release.0.take().unwrap().send(()).unwrap(); let ready = worker.join().unwrap();
        assert_eq!(ready["data"]["phase"], "ready", "{ready}");
        assert!(!saw_cancel.load(Ordering::SeqCst), "passive Open cancelled the real held work");
        assert_eq!(calls.load(Ordering::SeqCst), 2, "one original director and narrator only");
        assert_eq!(store.turn_status(&r).unwrap().phase, TurnPhase::Draft);
        let actual = store.resume(e.scope()).unwrap().engine; assert_eq!(actual.receipts(), e.receipts()); assert_eq!(actual.canonical_bytes(), e.canonical_bytes());
        assert_eq!(h.live_counts(), (1, 0));
    });
}

#[test]
fn accepted_prefix_extension_open_preserves_committed_outcome_and_capture_consent() {
    let f = Fixture::new(); let empty = create(&f); let mut store = f.store();
    let e = commit(&mut store, &empty, "cached-winner"); let receipt = e.receipts()[0].clone();
    let h = locallore_workspace::open(&f.path(), true).unwrap(); let session = select(&h, e.scope());
    consent(&h, &session, &e);
    let cached = call(&h, json!({"op":"submit","session":session,"request":receipt.request(),"mode":"accepted"}));
    assert_eq!(cached["data"]["phase"], "committed", "{cached}");
    assert_eq!(details(&h, &session, receipt.request(), e.revision())["status"], "not_retained");
    let advanced = commit(&mut store, &e, "independent-extension");
    let opened = call(&h, json!({"op":"open","session":session,"scope":e.scope()}));
    assert_eq!(opened["status"], "ok", "{opened}"); assert_eq!(opened["data"]["revision"], advanced.revision());
    assert_eq!(details(&h, &session, receipt.request(), advanced.revision())["status"], "not_retained", "prefix extension must preserve consent");
    let status = call(&h, json!({"op":"turn_status","session":session,"scope":e.scope(),"turn":receipt.request().turn}));
    assert_eq!(status["data"]["phase"], "committed", "{status}"); assert_eq!(status["data"]["receipt"], serde_json::to_value(&receipt).unwrap());
    let snapshot = call(&h, json!({"op":"play_snapshot","session":session,"scope":e.scope(),"expected_revision":advanced.revision()}));
    assert_eq!(snapshot["status"], "ok", "{snapshot}"); assert_eq!(snapshot["data"]["revision"], advanced.revision());
    let actual = store.resume(e.scope()).unwrap().engine; assert_eq!(actual.receipts(), advanced.receipts()); assert_eq!(actual.canonical_bytes(), advanced.canonical_bytes());
}
