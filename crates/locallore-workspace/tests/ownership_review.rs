// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent adversarial checks through the actual shared Host and SQLite owner.
use locallore::host::Host;
use serde_json::{json, Value};
use std::{
    path::PathBuf,
    sync::atomic::{AtomicU64, Ordering},
    time::{Duration, Instant},
};

static NEXT: AtomicU64 = AtomicU64::new(0);
// Keep expensive SQLite fixture construction from starving the 200 ms delayed-provider
// overlap assertions. Each case still runs its real independent Host/worker races.
static FIXTURE_GATE: std::sync::Mutex<()> = std::sync::Mutex::new(());
struct Temp(PathBuf, std::sync::MutexGuard<'static, ()>);
impl Temp {
    fn new() -> Self {
        let guard = FIXTURE_GATE.lock().unwrap_or_else(|p| p.into_inner());
        let p = std::env::temp_dir().join(format!(
            "locallore-ownership-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&p).unwrap();
        Self(p, guard)
    }
    fn host(&self, lab: bool) -> Host {
        locallore_workspace::open(&self.0.join("synthetic.sqlite"), lab).unwrap()
    }
}
impl Drop for Temp {
    fn drop(&mut self) {
        let _keep_fixture_gate = &self.1;
        std::fs::remove_dir_all(&self.0).unwrap();
    }
}
fn call(h: &Host, command: Value) -> Value {
    h.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
}
fn create(h: &Host) -> (String, Value) {
    let v = call(h, json!({"op":"create","seed":"lantern-quay-v1"}));
    assert_eq!(v["status"], "ok", "{v}");
    (
        v["data"]["session"].as_str().unwrap().into(),
        v["data"]["scope"].clone(),
    )
}
fn resume(h: &Host, scope: &Value) -> String {
    let v = call(h, json!({"op":"resume","scope":scope}));
    assert_eq!(v["status"], "ok", "{v}");
    v["data"]["session"].as_str().unwrap().into()
}
fn request(scope: &Value, turn: &str, revision: u64, gift: bool) -> Value {
    json!({"version":1,"scope":scope,"turn":turn,"expected_revision":revision,"intent":{"kind":"actions","value":if gift {json!([{"op":"give","item":"potion","to":"mira","quantity":1}])} else {json!([{"op":"wait","ticks":1}])}}})
}
fn submit(h: &Host, session: &str, req: &Value, mode: &str) -> Value {
    call(
        h,
        json!({"op":"submit","session":session,"request":req,"mode":mode}),
    )
}
fn op(h: &Host, session: &str, scope: &Value, turn: &str, op: &str) -> Value {
    call(
        h,
        json!({"op":op,"session":session,"scope":scope,"turn":turn}),
    )
}
fn commit(h: &Host, session: &str, scope: &Value, turn: &str) -> Value {
    assert_eq!(
        op(h, session, scope, turn, "prepare")["data"]["phase"],
        "ready"
    );
    let v = op(h, session, scope, turn, "commit");
    assert_eq!(v["data"]["phase"], "committed", "{v}");
    v
}
fn snapshot(h: &Host, session: &str, scope: &Value, revision: u64) -> Value {
    call(
        h,
        json!({"op":"play_snapshot","session":session,"scope":scope,"expected_revision":revision}),
    )
}
fn await_worker(h: &Host) {
    let until = Instant::now() + Duration::from_secs(2);
    while h.live_counts().1 == 0 {
        assert!(Instant::now() < until, "worker did not begin");
        std::thread::yield_now();
    }
}

#[test]
fn interrupted_draft_is_explicit_and_exact_retry_survives_restart() {
    let tmp = Temp::new();
    let h = tmp.host(false);
    let (id, scope) = create(&h);
    let req = request(&scope, "interrupted", 0, true);
    assert_eq!(submit(&h, &id, &req, "accepted")["data"]["phase"], "queued");
    drop(h);
    let h = tmp.host(false);
    let id = resume(&h, &scope);
    assert_eq!(snapshot(&h, &id, &scope, 0)["data"]["receipts"], json!([]));
    assert_eq!(
        op(&h, &id, &scope, "interrupted", "turn_status")["data"]["phase"],
        "queued"
    );
    assert_eq!(submit(&h, &id, &req, "accepted")["data"]["phase"], "queued");
    let accepted = commit(&h, &id, &scope, "interrupted");
    drop(h);
    let h = tmp.host(false);
    let id = resume(&h, &scope);
    assert_eq!(submit(&h, &id, &req, "accepted"), accepted);
    assert_eq!(op(&h, &id, &scope, "interrupted", "cancel"), accepted);
    let view = snapshot(&h, &id, &scope, 1);
    assert_eq!(view["data"]["receipts"].as_array().unwrap().len(), 1);
    assert!(view["data"]["inventory"].get("potion").is_none());
}

#[test]
fn foreign_sessions_scopes_and_play_observers_are_rejected_after_resume() {
    let tmp = Temp::new();
    let h = tmp.host(false);
    let (a, sa) = create(&h);
    let (b, sb) = create(&h);
    submit(&h, &a, &request(&sa, "gift", 0, true), "accepted");
    commit(&h, &a, &sa, "gift");
    drop(h);
    let h = tmp.host(false);
    let a = resume(&h, &sa);
    let b2 = resume(&h, &sb);
    assert_eq!(snapshot(&h, &a, &sb, 0)["error"], "Scope");
    assert_eq!(
        op(&h, &b2, &sb, "gift", "turn_status")["error"],
        "UnknownTurn"
    );
    for observer in ["sable", "omniscient"] {
        assert_eq!(
            call(
                &h,
                json!({"op":"inspect","session":a,"scope":sa,"observer":observer,"expected_revision":1})
            )["error"],
            "Forbidden"
        );
    }
    assert_eq!(
        snapshot(&h, &b2, &sb, 0)["data"]["inventory"]["potion"]["owner"],
        "player"
    );
    // Old process-local handles do not grant a foreign scope even when a handle number is reused.
    assert_eq!(op(&h, &b, &sa, "gift", "turn_status")["error"], "Scope");
}

#[test]
fn external_cancel_wins_over_running_preparation() {
    let tmp = Temp::new();
    let first = tmp.host(false);
    let (a, scope) = create(&first);
    let second = tmp.host(false);
    let b = resume(&second, &scope);
    let req = request(&scope, "same", 0, true);
    submit(&first, &a, &req, "delayed");
    std::thread::scope(|threads| {
        let running = threads.spawn(|| op(&first, &a, &scope, "same", "prepare"));
        await_worker(&first);
        assert_eq!(
            op(&second, &b, &scope, "same", "cancel")["data"]["phase"],
            "cancelled"
        );
        assert_eq!(
            running.join().unwrap()["data"]["phase"],
            "cancelled",
            "late prepare must publish the stored terminal outcome"
        );
    });
    assert_eq!(
        snapshot(&first, &a, &scope, 0)["data"]["receipts"],
        json!([])
    );
    assert_eq!(first.live_counts().1, 0);
}

#[test]
fn observed_external_commit_refreshes_the_local_player_cache() {
    let tmp = Temp::new();
    let first = tmp.host(false);
    let (a, scope) = create(&first);
    let second = tmp.host(false);
    let b = resume(&second, &scope);
    let req = request(&scope, "same", 0, true);
    submit(&first, &a, &req, "accepted");
    op(&first, &a, &scope, "same", "prepare");
    submit(&second, &b, &req, "accepted");
    let accepted = commit(&second, &b, &scope, "same");
    assert_eq!(op(&first, &a, &scope, "same", "commit"), accepted);
    let view = snapshot(&first, &a, &scope, 1);
    assert_eq!(
        view["status"], "ok",
        "authoritative receipt must agree with the Host snapshot: {view}"
    );
    assert_eq!(view["data"]["receipts"].as_array().unwrap().len(), 1);
}

#[test]
fn resume_existing_session_refreshes_after_an_external_commit() {
    let tmp = Temp::new();
    let first = tmp.host(false);
    let (a, scope) = create(&first);
    let second = tmp.host(false);
    let b = resume(&second, &scope);
    submit(
        &second,
        &b,
        &request(&scope, "external", 0, true),
        "accepted",
    );
    commit(&second, &b, &scope, "external");
    let resumed = call(&first, json!({"op":"resume","scope":scope}));
    assert_eq!(resumed["data"]["session"], a);
    assert_eq!(
        resumed["data"]["revision"], 1,
        "resume must return durable revision instead of stale cached revision"
    );
}

#[test]
fn newly_valid_request_is_not_failed_against_a_stale_local_cache() {
    let tmp = Temp::new();
    let first = tmp.host(false);
    let (a, scope) = create(&first);
    let second = tmp.host(false);
    let b = resume(&second, &scope);
    submit(
        &second,
        &b,
        &request(&scope, "external", 0, true),
        "accepted",
    );
    commit(&second, &b, &scope, "external");
    let req = request(&scope, "next", 1, false);
    let result = submit(&first, &a, &req, "accepted");
    assert_eq!(
        result["data"]["phase"], "queued",
        "store accepted this revision; cache must not fail its draft: {result}"
    );
    assert_eq!(
        op(&second, &b, &scope, "next", "turn_status")["data"]["phase"],
        "queued"
    );
}

#[test]
fn generation_holds_neither_host_nor_database_writer_lock() {
    use locallore::{contracts::Error, inference::*, play::PlayProfile};
    use std::sync::{mpsc, Arc, Mutex};
    use std::task::Poll;
    struct HeldProvider {
        entered: Option<mpsc::Sender<()>>,
        release: Arc<Mutex<mpsc::Receiver<()>>>,
    }
    impl InferenceProvider for HeldProvider {
        fn poll(
            &mut self,
            r: &GenerationRequest,
            _: &Cancellation,
        ) -> Poll<Result<Vec<u8>, Error>> {
            let Input::Structured { role, .. } = &r.input else {
                return Poll::Ready(Err(Error::Provider));
            };
            if let Some(entered) = self.entered.take() {
                entered.send(()).unwrap();
                // A bounded watchdog prevents a lock regression from hanging the suite.
                if self
                    .release
                    .lock()
                    .unwrap()
                    .recv_timeout(Duration::from_secs(5))
                    .is_err()
                {
                    return Poll::Ready(Err(Error::Timeout));
                }
            }
            let out = if role == "director" {
                json!({"commands":[{"op":"give","item":"potion","to":"mira","quantity":1}]})
            } else {
                json!({"text":"You place the potion in Mira's hand.","speaker":"narrator","event_ids":[1]})
            };
            Poll::Ready(Ok(serde_json::to_vec(&out).unwrap()))
        }
    }
    let tmp = Temp::new();
    let first = tmp.host(false);
    let (a, scope) = create(&first);
    let second = tmp.host(false);
    let b = resume(&second, &scope);
    let (entered_tx, entered_rx) = mpsc::channel();
    let (release_tx, release_rx) = mpsc::channel();
    let release = Arc::new(Mutex::new(release_rx));
    first
        .configure_local_provider(
            PlayProfile {
                id: "held-provider-test".into(),
                model_sha256: "a".repeat(64),
                runtime_revision: "b".repeat(40),
                template_sha256: "c".repeat(64),
                worker_sha256: "d".repeat(64),
                profile_manifest_sha256: "e".repeat(64),
                context_tokens: 4096,
                director_tokens: 350,
                narrator_tokens: 220,
                deadline_ms: 10_000,
                repair_limit: 0,
            },
            Arc::new(move || {
                Box::new(HeldProvider {
                    entered: Some(entered_tx.clone()),
                    release: release.clone(),
                })
            }),
        )
        .unwrap();
    let req = json!({"version":1,"scope":scope,"turn":"held","expected_revision":0,"intent":{"kind":"free_text","value":{"kind":"action","text":"I give my potion to Mira."}}});
    assert_eq!(
        submit(&first, &a, &req, "accepted")["data"]["phase"],
        "queued"
    );
    std::thread::scope(|threads| {
        let running = threads.spawn(|| op(&first, &a, &scope, "held", "prepare"));
        entered_rx
            .recv_timeout(Duration::from_secs(2))
            .expect("provider entry signal");
        assert_eq!(call(&first, json!({"op":"workspace"}))["status"], "ok");
        assert_eq!(
            submit(&second, &b, &request(&scope, "other", 0, false), "accepted")["data"]["phase"],
            "queued"
        );
        assert_eq!(
            first.live_counts().1,
            1,
            "provider is held until explicit release"
        );
        release_tx.send(()).unwrap();
        assert_eq!(running.join().unwrap()["data"]["phase"], "ready");
    });
}

#[test]
fn close_during_prepare_preserves_a_cancelled_save_without_late_effects() {
    let tmp = Temp::new();
    let h = tmp.host(false);
    let (id, scope) = create(&h);
    submit(&h, &id, &request(&scope, "closing", 0, true), "delayed");
    std::thread::scope(|threads| {
        let running = threads.spawn(|| op(&h, &id, &scope, "closing", "prepare"));
        await_worker(&h);
        assert_eq!(
            call(&h, json!({"op":"close","session":id,"scope":scope}))["data"]["saved"],
            true
        );
        assert_eq!(running.join().unwrap()["error"], "Closed");
    });
    assert_eq!(h.live_counts(), (0, 0));
    drop(h);
    let h = tmp.host(false);
    let id = resume(&h, &scope);
    assert_eq!(
        op(&h, &id, &scope, "closing", "turn_status")["data"]["phase"],
        "cancelled"
    );
    assert_eq!(snapshot(&h, &id, &scope, 0)["data"]["receipts"], json!([]));
}

#[test]
fn committed_receipt_learned_through_cancel_survives_late_worker_completion() {
    let tmp = Temp::new();
    let first = tmp.host(false);
    let (a, scope) = create(&first);
    let second = tmp.host(false);
    let b = resume(&second, &scope);
    let req = request(&scope, "same", 0, true);
    submit(&first, &a, &req, "delayed");
    submit(&second, &b, &req, "accepted");
    assert_eq!(
        op(&second, &b, &scope, "same", "prepare")["data"]["phase"],
        "ready"
    );
    std::thread::scope(|threads| {
        let running = threads.spawn(|| op(&first, &a, &scope, "same", "prepare"));
        await_worker(&first);
        let accepted = op(&second, &b, &scope, "same", "commit");
        assert_eq!(op(&first, &a, &scope, "same", "cancel"), accepted);
        assert_eq!(
            running.join().unwrap(),
            accepted,
            "late worker must preserve the receipt already learned through cancellation"
        );
    });
    call(&first, json!({"op":"open","session":a,"scope":scope}));
    assert_eq!(
        snapshot(&first, &a, &scope, 1)["data"]["receipts"]
            .as_array()
            .unwrap()
            .len(),
        1
    );
}

#[test]
fn competing_real_hosts_commit_or_cancel_one_atomic_outcome() {
    for _ in 0..12 {
        let tmp = Temp::new();
        let first = tmp.host(false);
        let (a, scope) = create(&first);
        let second = tmp.host(false);
        let b = resume(&second, &scope);
        let req = request(&scope, "race", 0, true);
        submit(&first, &a, &req, "accepted");
        op(&first, &a, &scope, "race", "prepare");
        let barrier = std::sync::Barrier::new(2);
        std::thread::scope(|threads| {
            threads.spawn(|| {
                barrier.wait();
                op(&first, &a, &scope, "race", "commit")
            });
            threads.spawn(|| {
                barrier.wait();
                op(&second, &b, &scope, "race", "cancel")
            });
        });
        drop(first);
        drop(second);
        let h = tmp.host(false);
        let id = resume(&h, &scope);
        let status = op(&h, &id, &scope, "race", "turn_status");
        let committed = status["data"]["phase"] == "committed";
        assert!(
            committed || status["data"]["phase"] == "cancelled",
            "{status}"
        );
        let view = snapshot(&h, &id, &scope, u64::from(committed));
        assert_eq!(
            view["data"]["receipts"].as_array().unwrap().len(),
            usize::from(committed)
        );
        assert_eq!(view["data"]["inventory"].get("potion").is_none(), committed);
        assert_eq!(submit(&h, &id, &req, "accepted"), status);
    }
}

#[test]
fn foreign_or_unopenable_database_never_falls_back_or_replaces_bytes() {
    let tmp = Temp::new();
    let path = tmp.0.join("synthetic.sqlite");
    let original = b"synthetic non-SQLite foreign file";
    std::fs::write(&path, original).unwrap();
    let error = match locallore_workspace::open(&path, false) {
        Ok(_) => panic!("foreign file must fail closed"),
        Err(e) => e,
    };
    assert_eq!(error, "Database");
    assert!(!error.contains(tmp.0.to_str().unwrap()));
    assert_eq!(std::fs::read(&path).unwrap(), original);
    let missing = tmp.0.join("absent-parent").join("save.sqlite");
    let error = match locallore_workspace::open(&missing, false) {
        Ok(_) => panic!("missing parent must fail closed"),
        Err(e) => e,
    };
    assert_eq!(error, "Io");
}

// Deliberately bounded test-only fault adapter. All successful operations go through the
// actual Store; only acknowledgement loss/cancellation failure is injected at the port.
struct FaultStore {
    store: locallore_storage::Store,
    fail_cancel: bool,
    lose_ack: bool,
    fail_status_once: bool,
}
fn saved(r: locallore_storage::TurnRecord) -> locallore::host::SavedTurn {
    locallore::host::SavedTurn {
        request: r.request,
        receipt: r.receipt,
        phase: match r.phase {
            locallore_storage::TurnPhase::Draft => "draft",
            locallore_storage::TurnPhase::Cancelled => "cancelled",
            locallore_storage::TurnPhase::Failed => "failed",
            locallore_storage::TurnPhase::Stale => "stale",
            locallore_storage::TurnPhase::Committed => "committed",
        }
        .into(),
    }
}
impl locallore::host::Persistence for FaultStore {
    fn location(&self) -> &str {
        "synthetic-local-test"
    }
    fn list(&mut self) -> Result<Vec<locallore::host::WorkspaceSummary>, String> {
        self.store
            .stories()
            .map(|rows| {
                rows.into_iter()
                    .map(|s| locallore::host::WorkspaceSummary {
                        scope: s.scope,
                        title: s.title,
                        revision: s.revision,
                        drafts: s.drafts,
                    })
                    .collect()
            })
            .map_err(|e| e.to_string())
    }
    fn create(&mut self) -> Result<locallore::engine::Engine, String> {
        let seed =
            serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
        let scope = self
            .store
            .create_workspace("Synthetic", seed)
            .map_err(|e| e.to_string())?;
        self.resume(&scope)
    }
    fn resume(
        &mut self,
        s: &locallore::contracts::Scope,
    ) -> Result<locallore::engine::Engine, String> {
        self.store
            .resume(s)
            .map(|r| r.engine)
            .map_err(|e| e.to_string())
    }
    fn begin(
        &mut self,
        r: &locallore::contracts::Request,
    ) -> Result<locallore::host::SavedTurn, String> {
        self.store
            .begin_turn(r)
            .map(saved)
            .map_err(|e| e.to_string())
    }
    fn commit(
        &mut self,
        r: &locallore::contracts::Request,
        p: &locallore::contracts::Proposal,
        n: &str,
    ) -> Result<locallore::contracts::Receipt, String> {
        let receipt = self.store.commit_turn(r, p, n).map_err(|e| e.to_string())?;
        if self.lose_ack {
            self.lose_ack = false;
            Err("Database".into())
        } else {
            Ok(receipt)
        }
    }
    fn cancel(
        &mut self,
        r: &locallore::contracts::Request,
    ) -> Result<locallore::host::SavedTurn, String> {
        if self.fail_cancel {
            Err("Busy".into())
        } else {
            self.store
                .cancel_turn(r)
                .map(saved)
                .map_err(|e| e.to_string())
        }
    }
    fn fail(
        &mut self,
        r: &locallore::contracts::Request,
    ) -> Result<locallore::host::SavedTurn, String> {
        self.store
            .fail_turn(r)
            .map(saved)
            .map_err(|e| e.to_string())
    }
    fn stale(
        &mut self,
        r: &locallore::contracts::Request,
    ) -> Result<locallore::host::SavedTurn, String> {
        self.store
            .stale_turn(r)
            .map(saved)
            .map_err(|e| e.to_string())
    }
    fn status(
        &mut self,
        s: &locallore::contracts::Scope,
        id: &str,
    ) -> Result<locallore::host::SavedTurn, String> {
        if self.fail_status_once {
            self.fail_status_once = false;
            return Err("Busy".into());
        }
        self.store
            .lookup_turn(s, id)
            .map(saved)
            .map_err(|e| e.to_string())
    }
}
fn fault_host(tmp: &Temp, fail_cancel: bool, lose_ack: bool) -> Host {
    Host::with_persistence(
        false,
        Box::new(FaultStore {
            store: locallore_storage::Store::open(&tmp.0.join("synthetic.sqlite"), None).unwrap(),
            fail_cancel,
            lose_ack,
            fail_status_once: false,
        }),
    )
}

#[test]
fn transient_post_generation_status_failure_releases_the_running_lease_for_retry() {
    let tmp = Temp::new();
    let h = Host::with_persistence(
        false,
        Box::new(FaultStore {
            store: locallore_storage::Store::open(&tmp.0.join("synthetic.sqlite"), None).unwrap(),
            fail_cancel: false,
            lose_ack: false,
            fail_status_once: true,
        }),
    );
    let (id, scope) = create(&h);
    let req = request(&scope, "transient-status", 0, true);
    assert_eq!(submit(&h, &id, &req, "accepted")["data"]["phase"], "queued");
    assert_eq!(
        op(&h, &id, &scope, "transient-status", "prepare")["error"],
        "Busy"
    );
    assert_eq!(h.live_counts().1, 0);
    let recovered = op(&h, &id, &scope, "transient-status", "turn_status");
    assert_eq!(
        recovered["data"]["phase"], "queued",
        "a completed worker must not strand a durable draft in running: {recovered}"
    );
    let accepted = commit(&h, &id, &scope, "transient-status");
    assert_eq!(submit(&h, &id, &req, "accepted"), accepted);
    assert_eq!(
        snapshot(&h, &id, &scope, 1)["data"]["receipts"]
            .as_array()
            .unwrap()
            .len(),
        1
    );
}

#[test]
fn failed_cancel_acknowledgement_cannot_publish_an_unpersisted_terminal_outcome() {
    let tmp = Temp::new();
    let h = fault_host(&tmp, true, false);
    let (id, scope) = create(&h);
    submit(
        &h,
        &id,
        &request(&scope, "cancel-failed", 0, true),
        "delayed",
    );
    std::thread::scope(|threads| {
        let running = threads.spawn(|| op(&h, &id, &scope, "cancel-failed", "prepare"));
        await_worker(&h);
        assert_eq!(
            op(&h, &id, &scope, "cancel-failed", "cancel")["error"],
            "Busy"
        );
        let result = running.join().unwrap();
        assert_ne!(
            result["data"]["phase"], "cancelled",
            "failed storage cancellation must remain uncertain, not falsely terminal: {result}"
        );
    });
    let status = op(&h, &id, &scope, "cancel-failed", "turn_status");
    assert_ne!(
        status["data"]["phase"], "cancelled",
        "lookup must not publish a failed in-memory transition: {status}"
    );
    drop(h);
    let h = tmp.host(false);
    let id = resume(&h, &scope);
    assert_eq!(
        op(&h, &id, &scope, "cancel-failed", "turn_status")["data"]["phase"],
        "queued"
    );
}

#[test]
fn lost_commit_acknowledgement_retries_the_recorded_outcome_without_a_second_effect() {
    let tmp = Temp::new();
    let h = fault_host(&tmp, false, true);
    let (id, scope) = create(&h);
    let req = request(&scope, "lost-ack", 0, true);
    submit(&h, &id, &req, "accepted");
    let accepted = commit(&h, &id, &scope, "lost-ack");
    assert_eq!(op(&h, &id, &scope, "lost-ack", "commit"), accepted);
    drop(h);
    let h = tmp.host(false);
    let id = resume(&h, &scope);
    assert_eq!(submit(&h, &id, &req, "accepted"), accepted);
    assert_eq!(
        snapshot(&h, &id, &scope, 1)["data"]["receipts"]
            .as_array()
            .unwrap()
            .len(),
        1
    );
}

#[test]
fn simultaneous_admission_at_library_cap_cannot_make_the_catalog_unreadable() {
    let tmp = Temp::new();
    {
        let mut store =
            locallore_storage::Store::open(&tmp.0.join("synthetic.sqlite"), None).unwrap();
        let seed: locallore::contracts::Seed =
            serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
        for n in 0..255 {
            let mut seed = seed.clone();
            seed.scope.story = format!("synthetic-{n}");
            store
                .create_story("Synthetic capacity fixture", seed)
                .unwrap();
        }
    }
    let first = tmp.host(false);
    let second = tmp.host(false);
    let barrier = std::sync::Barrier::new(2);
    let (a, b) = std::thread::scope(|threads| {
        let a = threads.spawn(|| {
            barrier.wait();
            call(&first, json!({"op":"create","seed":"lantern-quay-v1"}))
        });
        let b = threads.spawn(|| {
            barrier.wait();
            call(&second, json!({"op":"create","seed":"lantern-quay-v1"}))
        });
        (a.join().unwrap(), b.join().unwrap())
    });
    assert!(
        !(a["status"] == "ok" && b["status"] == "ok"),
        "only one of the two writers can admit the last story: {a} {b}"
    );
    let library = call(&first, json!({"op":"workspace"}));
    assert_eq!(
        library["status"], "ok",
        "hitting the library bound must preserve readable existing saves: {library}"
    );
    assert!(library["data"]["stories"].as_array().unwrap().len() <= 256);
}
