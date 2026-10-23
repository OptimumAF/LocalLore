//! Actual Host wire + SQLite lifecycle, synthetic provider only; no UI/model/native worker.
use locallore::{contracts::*, host::Host, inference::*, play::PlayProfile};
use locallore_storage::Store;
use serde_json::{json, Value};
use std::{
    path::PathBuf,
    sync::{
        atomic::{AtomicUsize, Ordering},
        mpsc, Arc, Mutex,
    },
    task::Poll,
    time::Duration,
};
static SEQUENCE: AtomicUsize = AtomicUsize::new(0);
struct Temp(PathBuf);
impl Temp {
    fn new() -> Self {
        let root = std::env::var_os("LOCALLORE_TRACE_TEST_ROOT")
            .map(PathBuf::from)
            .unwrap_or_else(std::env::temp_dir);
        std::fs::create_dir_all(&root).unwrap();
        let path = root.join(format!(
            "trace-host-{}-{}",
            std::process::id(),
            SEQUENCE.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&path).unwrap();
        Self(path)
    }
    fn seeded(&self, name: &str) -> PathBuf {
        let path = self.0.join(name);
        let mut store = Store::open(&path, None).unwrap();
        store.create_story("Synthetic trace story", seed()).unwrap();
        path
    }
}
impl Drop for Temp {
    fn drop(&mut self) {
        std::fs::remove_dir_all(&self.0).unwrap();
    }
}
fn seed() -> Seed {
    serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap()
}
fn scope() -> Value {
    serde_json::to_value(seed().scope).unwrap()
}
fn host(path: &std::path::Path, lab: bool) -> Host {
    locallore_workspace::open(path, lab).unwrap()
}
fn call(h: &Host, command: Value) -> Value {
    h.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
}
fn resume(h: &Host) -> String {
    let reply = call(h, json!({"op":"resume","scope":scope()}));
    assert_eq!(reply["status"], "ok", "{reply}");
    reply["data"]["session"].as_str().unwrap().into()
}
fn profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-trace-v2".into(),
        model_sha256: "a".repeat(64),
        runtime_revision: "b".repeat(40),
        template_sha256: "c".repeat(64),
        worker_sha256: "d".repeat(64),
        profile_manifest_sha256: "e".repeat(64),
        context_tokens: 4096,
        director_tokens: 350,
        narrator_tokens: 220,
        deadline_ms: 1000,
        repair_limit: 1,
    }
}
struct Script {
    calls: Arc<AtomicUsize>,
    panic: bool,
    gate: Option<Gate>,
}
impl InferenceProvider for Script {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        cancel: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        self.calls.fetch_add(1, Ordering::SeqCst);
        assert!(!self.panic, "synthetic provider panic");
        let Input::Structured { role, .. } = &request.input else {
            return Poll::Ready(Err(Error::Provider));
        };
        if role == "director" {
            if let Some((entered, release)) = self.gate.take() {
                entered.send(()).unwrap();
                release
                    .lock()
                    .unwrap()
                    .recv_timeout(Duration::from_secs(3))
                    .unwrap();
            }
        }
        if cancel.is_cancelled() {
            return Poll::Ready(Err(Error::Cancelled));
        }
        let output = if role == "director" {
            json!({"commands":[{"op":"give","item":"potion","to":"mira","quantity":1}]})
        } else {
            json!({"text":"You place the potion in Mira's hand with a gentle nod.","speaker":"narrator","event_ids":[request.revision+1]})
        };
        Poll::Ready(Ok(serde_json::to_vec(&output).unwrap()))
    }
}
type Gate = (mpsc::SyncSender<()>, Arc<Mutex<mpsc::Receiver<()>>>);
fn configure(h: &Host, calls: Arc<AtomicUsize>, panic: bool, gate: Option<Gate>) {
    h.configure_local_provider(
        profile(),
        Arc::new(move || {
            Box::new(Script {
                calls: Arc::clone(&calls),
                panic,
                gate: gate.clone(),
            })
        }),
    )
    .unwrap();
}
fn enable(h: &Host, session: &str, head: u64, enabled: bool) -> Value {
    call(
        h,
        json!({"op":"trace_configure","session":session,"scope":scope(),"expected_head":head,"enabled":enabled}),
    )
}
fn clear(h: &Host, session: &str, head: u64) -> Value {
    call(
        h,
        json!({"op":"trace_clear","session":session,"scope":scope(),"expected_head":head}),
    )
}
fn read(h: &Host, session: &str, head: u64, base: u64, observer: Value) -> Value {
    call(
        h,
        json!({"op":"trace_read","session":session,"scope":scope(),"expected_head":head,"base_revision":base,"observer":observer,"turn":null,"attempt":null}),
    )
}
fn player() -> Value {
    json!({"kind":"player"})
}
fn attempts(reply: &Value) -> &Vec<Value> {
    assert_eq!(reply["status"], "ok", "{reply}");
    reply["data"]["snapshot"]["attempts"].as_array().unwrap()
}
fn request(turn: &str, revision: u64) -> Value {
    json!({"version":1,"scope":scope(),"turn":turn,"expected_revision":revision,"intent":{"kind":"free_text","value":{"kind":"action","text":"I give my last potion to Mira."}}})
}
fn submit(h: &Host, id: &str, r: Value) -> Value {
    call(h, json!({"op":"free_text","session":id,"request":r}))
}
fn op(h: &Host, id: &str, turn: &str, op: &str) -> Value {
    call(h, json!({"op":op,"session":id,"scope":scope(),"turn":turn}))
}
fn commit(h: &Host, id: &str, turn: &str) -> Value {
    assert_eq!(submit(h, id, request(turn, 0))["data"]["phase"], "queued");
    assert_eq!(op(h, id, turn, "prepare")["data"]["phase"], "ready");
    let reply = op(h, id, turn, "commit");
    assert_eq!(reply["data"]["phase"], "committed", "{reply}");
    reply
}
fn normalize_receipt(mut value: Value) -> Value {
    if let Some(stages) = value["play"]["stages"].as_array_mut() {
        for stage in stages {
            stage["elapsed_ms"] = json!(0);
        }
    }
    value
}

#[test]
fn actual_sqlite_on_off_receipts_events_state_restart_and_default_disabled_are_equal() {
    let temp = Temp::new();
    let a = temp.seeded("off.sqlite");
    let b = temp.seeded("on.sqlite");
    let mut receipts = vec![];
    let mut states = vec![];
    for (path, enabled) in [(&a, false), (&b, true)] {
        let h = host(path, false);
        let id = resume(&h);
        let calls = Arc::new(AtomicUsize::new(0));
        configure(&h, calls.clone(), false, None);
        assert_eq!(
            read(&h, &id, 0, 0, player())["data"]["snapshot"]["status"],
            "disabled"
        );
        assert!(attempts(&read(&h, &id, 0, 0, player())).is_empty());
        if enabled {
            assert_eq!(enable(&h, &id, 0, true)["data"]["enabled"], true);
        }
        let before = call(
            &h,
            json!({"op":"play_snapshot","session":id,"scope":scope(),"expected_revision":0}),
        );
        let trace = read(&h, &id, 0, 0, player());
        assert!(attempts(&trace).is_empty());
        assert_eq!(
            before,
            call(
                &h,
                json!({"op":"play_snapshot","session":id,"scope":scope(),"expected_revision":0})
            )
        );
        let result = commit(&h, &id, "gift");
        assert_eq!(calls.load(Ordering::SeqCst), 2);
        let trace = read(&h, &id, 1, 0, player());
        if enabled {
            let trace = &attempts(&trace)[0];
            assert_eq!(trace["outcome"], "committed");
            assert_eq!(trace["identity"]["base_revision"], 0);
            assert_eq!(trace["identity"]["attempt"], 1);
            assert_eq!(trace["provenance"]["model_sha256"], "a".repeat(64));
            assert!(trace["provenance"]["engine_revision"].is_null());
            assert!(trace["stages"]
                .as_array()
                .unwrap()
                .iter()
                .any(|stage| stage["stage"] == "atomic_commit" && stage["outcome"] == "committed"));
            let text = trace.to_string();
            for private in [
                "SECRET-TIDE-731",
                "potion",
                "gentle nod",
                "I give my last",
                "stories.sqlite",
                "C:\\Users",
            ] {
                assert!(!text.contains(private), "{private}");
            }
        } else {
            assert!(attempts(&trace).is_empty());
        }
        let traced_before = trace.clone();
        assert_eq!(op(&h, &id, "gift", "commit"), result);
        assert_eq!(op(&h, &id, "gift", "prepare"), result);
        assert_eq!(
            read(&h, &id, 1, 0, player()),
            traced_before,
            "cached retry adds no fabricated stages"
        );
        receipts.push(normalize_receipt(result["data"]["receipt"].clone()));
        let mut store = Store::open(path, None).unwrap();
        states.push(
            store
                .resume(&seed().scope)
                .unwrap()
                .engine
                .canonical_bytes(),
        );
        drop(store);
        drop(h);
        let h = host(path, false);
        let id = resume(&h);
        assert_eq!(submit(&h, &id, request("gift", 0)), result);
        assert!(attempts(&read(&h, &id, 1, 0, player())).is_empty());
        assert_eq!(
            read(&h, &id, 1, 0, player())["data"]["snapshot"]["status"],
            "disabled"
        );
    }
    assert_eq!(receipts[0], receipts[1]);
    assert_eq!(states[0], states[1]);
}

#[test]
fn wire_denials_fresh_head_scope_privileges_and_explicit_clear_are_nonmutating() {
    let temp = Temp::new();
    let path = temp.seeded("privacy.sqlite");
    let h = host(&path, false);
    let id = resume(&h);
    enable(&h, &id, 0, true);
    configure(&h, Arc::new(AtomicUsize::new(0)), false, None);
    commit(&h, &id, "gift");
    assert_eq!(read(&h, &id, 0, 0, player())["error"], "Stale");
    assert_eq!(enable(&h, &id, 0, false)["error"], "Stale");
    for observer in [
        json!({"kind":"character","id":"mira"}),
        json!({"kind":"omniscient"}),
    ] {
        assert_eq!(read(&h, &id, 1, 0, observer)["error"], "Forbidden");
    }
    let mut foreign = scope();
    foreign["story"] = json!("foreign");
    assert_eq!(
        call(
            &h,
            json!({"op":"trace_clear","session":id,"scope":foreign,"expected_head":1})
        )["error"],
        "Scope"
    );
    let injected = call(
        &h,
        json!({"op":"trace_read","session":id,"scope":scope(),"expected_head":1,"base_revision":0,"observer":player(),"story_lab_granted":true}),
    );
    assert_eq!(injected["error"], "Malformed");
    assert_eq!(
        call(
            &h,
            json!({"op":"trace_configure","session":id,"scope":scope(),"expected_head":1,"enabled":true,"full_capture":true})
        )["error"],
        "Malformed"
    );
    assert_eq!(
        call(
            &h,
            json!({"op":"trace_read","session":id,"scope":scope(),"expected_head":1,"base_revision":0,"observer":player(),"attempt":u64::MAX})
        )["error"],
        "InvalidRequest"
    );
    let before = call(
        &h,
        json!({"op":"play_snapshot","session":id,"scope":scope(),"expected_revision":1}),
    );
    assert_eq!(clear(&h, &id, 1)["data"]["cleared"], true);
    assert!(attempts(&read(&h, &id, 1, 0, player())).is_empty());
    assert_eq!(
        before,
        call(
            &h,
            json!({"op":"play_snapshot","session":id,"scope":scope(),"expected_revision":1})
        )
    );
    let lab = host(&path, true);
    let lid = resume(&lab);
    enable(&lab, &lid, 1, true);
    assert!(attempts(&read(
        &lab,
        &lid,
        1,
        0,
        json!({"kind":"character","id":"mira"})
    ))
    .is_empty());
    assert!(attempts(&read(&lab, &lid, 1, 0, json!({"kind":"omniscient"}))).is_empty());
    assert_eq!(enable(&h, &id, 1, false)["data"]["enabled"], false);
    assert_eq!(
        read(&h, &id, 1, 0, player())["data"]["snapshot"]["status"],
        "disabled"
    );
}

fn gated(h: &Host) -> (mpsc::Receiver<()>, mpsc::SyncSender<()>, Arc<AtomicUsize>) {
    let (entered_tx, entered_rx) = mpsc::sync_channel(1);
    let (release_tx, release_rx) = mpsc::sync_channel(1);
    let calls = Arc::new(AtomicUsize::new(0));
    configure(
        h,
        calls.clone(),
        false,
        Some((entered_tx, Arc::new(Mutex::new(release_rx)))),
    );
    (entered_rx, release_tx, calls)
}
#[test]
fn blocked_provider_allows_reads_cancel_and_clear_without_deadlock_or_late_resurrection() {
    for delete in [false, true] {
        let temp = Temp::new();
        let path = temp.seeded("cancel.sqlite");
        let h = Arc::new(host(&path, false));
        let id = resume(&h);
        enable(&h, &id, 0, true);
        let (entered, release, _) = gated(&h);
        submit(&h, &id, request("pending", 0));
        let worker_h = Arc::clone(&h);
        let worker_id = id.clone();
        let worker = std::thread::spawn(move || op(&worker_h, &worker_id, "pending", "prepare"));
        entered.recv_timeout(Duration::from_secs(2)).unwrap();
        assert_eq!(
            attempts(&read(&h, &id, 0, 0, player()))[0]["outcome"],
            "running"
        );
        if delete {
            clear(&h, &id, 0);
        }
        assert_eq!(
            op(&h, &id, "pending", "cancel")["data"]["phase"],
            "cancelled"
        );
        release.send(()).unwrap();
        assert_eq!(worker.join().unwrap()["data"]["phase"], "cancelled");
        let trace = read(&h, &id, 0, 0, player());
        if delete {
            assert!(attempts(&trace).is_empty());
        } else {
            assert_eq!(attempts(&trace)[0]["outcome"], "cancelled");
        }
        assert_eq!(h.live_counts(), (1, 0));
    }
}

#[test]
fn close_and_reopen_same_story_uses_new_private_trace_owner() {
    let temp = Temp::new();
    let path = temp.seeded("close.sqlite");
    let h = Arc::new(host(&path, true));
    let id = resume(&h);
    enable(&h, &id, 0, true);
    let (entered, release, _) = gated(&h);
    submit(&h, &id, request("pending", 0));
    let wh = Arc::clone(&h);
    let wid = id.clone();
    let worker = std::thread::spawn(move || op(&wh, &wid, "pending", "prepare"));
    entered.recv_timeout(Duration::from_secs(2)).unwrap();
    assert_eq!(
        call(&h, json!({"op":"close","session":id,"scope":scope()}))["data"]["closed"],
        true
    );
    assert_eq!(read(&h, &id, 0, 0, player())["error"], "Closed");
    let next = resume(&h);
    assert_ne!(next, id);
    assert!(attempts(&read(&h, &next, 0, 0, player())).is_empty());
    release.send(()).unwrap();
    worker.join().unwrap();
    assert!(attempts(&read(&h, &next, 0, 0, json!({"kind":"omniscient"}))).is_empty());
    assert_eq!(h.live_counts(), (1, 0));
}

#[test]
fn external_commit_makes_running_candidate_stale_and_fresh_trace_read_remains_coherent() {
    let temp = Temp::new();
    let path = temp.seeded("stale.sqlite");
    let h = Arc::new(host(&path, false));
    let id = resume(&h);
    enable(&h, &id, 0, true);
    let (entered, release, _) = gated(&h);
    submit(&h, &id, request("pending", 0));
    let wh = Arc::clone(&h);
    let wid = id.clone();
    let worker = std::thread::spawn(move || op(&wh, &wid, "pending", "prepare"));
    entered.recv_timeout(Duration::from_secs(2)).unwrap();
    let writer = host(&path, false);
    let other = resume(&writer);
    let typed = json!({"version":1,"scope":scope(),"turn":"advance","expected_revision":0,"intent":{"kind":"actions","value":[{"op":"wait","ticks":1}]}});
    assert_eq!(
        call(
            &writer,
            json!({"op":"submit","session":other,"request":typed,"mode":"accepted"})
        )["data"]["phase"],
        "queued"
    );
    assert_eq!(
        op(&writer, &other, "advance", "prepare")["data"]["phase"],
        "ready"
    );
    assert_eq!(
        op(&writer, &other, "advance", "commit")["data"]["phase"],
        "committed"
    );
    assert_eq!(read(&h, &id, 0, 0, player())["error"], "Stale");
    release.send(()).unwrap();
    assert_eq!(worker.join().unwrap()["data"]["phase"], "stale");
    let trace = read(&h, &id, 1, 0, player());
    assert_eq!(trace["data"]["head"], 1);
    assert_eq!(attempts(&trace)[0]["outcome"], "stale");
    assert!(attempts(&trace)[0]["stages"]
        .as_array()
        .unwrap()
        .iter()
        .any(|stage| stage["stage"] == "publication" && stage["outcome"] == "stale"));
    assert!(call(
        &h,
        json!({"op":"play_snapshot","session":id,"scope":scope(),"expected_revision":1})
    )["data"]["inventory"]
        .get("potion")
        .is_some());
}

#[test]
fn caught_provider_panic_is_observed_but_restart_does_not_invent_failed_cause_or_trace() {
    let temp = Temp::new();
    let path = temp.seeded("panic.sqlite");
    let h = host(&path, false);
    let id = resume(&h);
    enable(&h, &id, 0, true);
    configure(&h, Arc::new(AtomicUsize::new(0)), true, None);
    submit(&h, &id, request("panic", 0));
    let failed = op(&h, &id, "panic", "prepare");
    assert_eq!(failed["data"]["phase"], "failed");
    assert_eq!(failed["data"]["error"], "Provider");
    let trace = read(&h, &id, 0, 0, player());
    assert_eq!(attempts(&trace)[0]["outcome"], "failed");
    assert!(attempts(&trace)[0]["stages"]
        .as_array()
        .unwrap()
        .iter()
        .any(|stage| stage["stage"] == "publication" && stage["error"] == "provider"));
    drop(h);
    let h = host(&path, false);
    let id = resume(&h);
    assert!(op(&h, &id, "panic", "turn_status")["data"]["error"].is_null());
    assert!(attempts(&read(&h, &id, 0, 0, player())).is_empty());
}

#[test]
fn one_window_ring_is_bounded_and_trace_controls_never_change_typed_commits() {
    let h = Host::new(true);
    let created = call(&h, json!({"op":"create","seed":"lantern-quay-v1"}));
    let id = created["data"]["session"].as_str().unwrap();
    let current_scope = created["data"]["scope"].clone();
    assert_eq!(
        call(
            &h,
            json!({"op":"trace_configure","session":id,"scope":current_scope,"expected_head":0,"enabled":true})
        )["status"],
        "ok"
    );
    for n in 0..40 {
        let r = json!({"version":1,"scope":current_scope,"turn":format!("wait-{n}"),"expected_revision":n,"intent":{"kind":"actions","value":[{"op":"wait","ticks":1}]}});
        assert_eq!(
            call(
                &h,
                json!({"op":"submit","session":id,"request":r,"mode":"accepted"})
            )["data"]["phase"],
            "queued"
        );
        for op in ["prepare", "commit"] {
            assert_eq!(
                call(
                    &h,
                    json!({"op":op,"session":id,"scope":current_scope,"turn":format!("wait-{n}")})
                )["status"],
                "ok"
            );
        }
    }
    let mut retained = 0;
    for base in 0..40 {
        let reply = call(
            &h,
            json!({"op":"trace_read","session":id,"scope":current_scope,"expected_head":40,"base_revision":base,"observer":player()}),
        );
        assert!(serde_json::to_vec(&reply).unwrap().len() <= 65536);
        retained += attempts(&reply).len();
        assert_eq!(reply["data"]["snapshot"]["exact_reconstruction"], false);
    }
    assert!(retained > 0 && retained <= 32);
    assert_eq!(h.live_counts(), (1, 0));
}

// The sole SQLite owner still decides truth when transport acknowledgement is lost.
struct LostAck {
    store: Store,
    lookup_failure: bool,
    committed: bool,
}
fn fault_saved(record: locallore_storage::TurnRecord) -> locallore::host::SavedTurn {
    locallore::host::SavedTurn {
        request: record.request,
        receipt: record.receipt,
        phase: match record.phase {
            locallore_storage::TurnPhase::Draft => "draft",
            locallore_storage::TurnPhase::Committed => "committed",
            locallore_storage::TurnPhase::Cancelled => "cancelled",
            locallore_storage::TurnPhase::Failed => "failed",
            locallore_storage::TurnPhase::Stale => "stale",
        }
        .into(),
    }
}
impl locallore::host::Persistence for LostAck {
    fn begin_bound(
        &mut self,
        request: &Request,
        basis: &locallore::engine::AcceptedHistoryBasis,
    ) -> Result<locallore::host::SavedTurn, String> {
        self.store
            .begin_bound(request, basis)
            .map(fault_saved)
            .map_err(|e| e.to_string())
    }
    fn status_bound(
        &mut self,
        request: &Request,
        basis: &locallore::engine::AcceptedHistoryBasis,
    ) -> Result<locallore::host::SavedTurn, String> {
        if self.committed && self.lookup_failure {
            self.lookup_failure = false;
            return Err("Io".into());
        }
        self.store
            .turn_status_bound(request, basis)
            .map(fault_saved)
            .map_err(|e| e.to_string())
    }
    fn commit_prepared_bound(
        &mut self,
        receipt: &Receipt,
        basis: &locallore::engine::AcceptedHistoryBasis,
    ) -> Result<Receipt, String> {
        self.store
            .commit_prepared_bound(receipt, basis)
            .map_err(|e| e.to_string())?;
        self.committed = true;
        Err("Io".into())
    }
    fn finish_bound(
        &mut self,
        request: &Request,
        basis: &locallore::engine::AcceptedHistoryBasis,
        phase: locallore::host::DraftDisposition,
    ) -> Result<locallore::host::SavedTurn, String> {
        let phase = match phase {
            locallore::host::DraftDisposition::Cancelled => locallore_storage::TurnPhase::Cancelled,
            locallore::host::DraftDisposition::Failed => locallore_storage::TurnPhase::Failed,
            locallore::host::DraftDisposition::Stale => locallore_storage::TurnPhase::Stale,
        };
        self.store
            .finish_bound(request, basis, phase)
            .map(fault_saved)
            .map_err(|e| e.to_string())
    }
    fn location(&self) -> &str {
        "private-test-store"
    }
    fn list(&mut self) -> Result<Vec<locallore::host::WorkspaceSummary>, String> {
        Ok(vec![])
    }
    fn create(&mut self) -> Result<locallore::engine::Engine, String> {
        Err("Unsupported".into())
    }
    fn resume(&mut self, scope: &Scope) -> Result<locallore::engine::Engine, String> {
        self.store
            .resume(scope)
            .map(|r| r.engine)
            .map_err(|e| e.to_string())
    }
    fn begin(&mut self, request: &Request) -> Result<locallore::host::SavedTurn, String> {
        self.store
            .begin_turn(request)
            .map(fault_saved)
            .map_err(|e| e.to_string())
    }
    fn commit(
        &mut self,
        request: &Request,
        proposal: &Proposal,
        narration: &str,
    ) -> Result<Receipt, String> {
        self.store
            .commit_turn(request, proposal, narration)
            .map_err(|e| e.to_string())
    }
    fn commit_prepared(&mut self, receipt: &Receipt) -> Result<Receipt, String> {
        self.store
            .commit_prepared(receipt)
            .map_err(|e| e.to_string())?;
        self.committed = true;
        Err("Io".into())
    }
    fn cancel(&mut self, request: &Request) -> Result<locallore::host::SavedTurn, String> {
        self.store
            .cancel_turn(request)
            .map(fault_saved)
            .map_err(|e| e.to_string())
    }
    fn fail(&mut self, request: &Request) -> Result<locallore::host::SavedTurn, String> {
        self.store
            .fail_turn(request)
            .map(fault_saved)
            .map_err(|e| e.to_string())
    }
    fn stale(&mut self, request: &Request) -> Result<locallore::host::SavedTurn, String> {
        self.store
            .stale_turn(request)
            .map(fault_saved)
            .map_err(|e| e.to_string())
    }
    fn status(&mut self, scope: &Scope, turn: &str) -> Result<locallore::host::SavedTurn, String> {
        if self.committed && self.lookup_failure {
            self.lookup_failure = false;
            return Err("Io".into());
        }
        self.store
            .lookup_turn(scope, turn)
            .map(fault_saved)
            .map_err(|e| e.to_string())
    }
}
#[test]
fn lost_ack_and_failed_lookup_never_invent_commit_and_retry_uses_actual_sqlite() {
    let temp = Temp::new();
    for lookup_failure in [false, true] {
        let path = temp.seeded(if lookup_failure {
            "unknown.sqlite"
        } else {
            "lookup.sqlite"
        });
        let h = Host::with_persistence(
            false,
            Box::new(LostAck {
                store: Store::open(&path, None).unwrap(),
                lookup_failure,
                committed: false,
            }),
        );
        let id = resume(&h);
        enable(&h, &id, 0, true);
        let calls = Arc::new(AtomicUsize::new(0));
        configure(&h, calls.clone(), false, None);
        submit(&h, &id, request("gift", 0));
        assert_eq!(op(&h, &id, "gift", "prepare")["data"]["phase"], "ready");
        let first = op(&h, &id, "gift", "commit");
        let snapshot = read(&h, &id, 1, 0, player());
        let trace = &attempts(&snapshot)[0];
        if lookup_failure {
            assert_eq!(first["error"], "TransportUnknown");
            assert_eq!(trace["outcome"], "running");
            assert!(trace["stages"]
                .as_array()
                .unwrap()
                .iter()
                .any(|s| s["stage"] == "atomic_commit" && s["outcome"] == "unknown"));
        } else {
            assert_eq!(first["data"]["phase"], "committed");
            assert_eq!(trace["outcome"], "committed");
        }
        let recovered = op(&h, &id, "gift", "commit");
        assert_eq!(recovered["data"]["phase"], "committed");
        let snapshot = read(&h, &id, 1, 0, player());
        assert_eq!(attempts(&snapshot)[0]["outcome"], "committed");
        assert_eq!(calls.load(Ordering::SeqCst), 2);
        assert_eq!(op(&h, &id, "gift", "prepare"), recovered);
        assert_eq!(read(&h, &id, 1, 0, player()), snapshot);
        let mut store = Store::open(&path, None).unwrap();
        let canonical = store.resume(&seed().scope).unwrap().engine;
        assert_eq!(canonical.revision(), 1);
        assert_eq!(
            serde_json::to_value(
                store
                    .lookup_turn(&seed().scope, "gift")
                    .unwrap()
                    .receipt
                    .unwrap()
            )
            .unwrap(),
            recovered["data"]["receipt"]
        );
    }
}

#[test]
fn another_owner_same_turn_commit_is_not_attributed_to_our_late_generation() {
    let temp = Temp::new();
    let path = temp.seeded("same-key.sqlite");
    let h = Arc::new(host(&path, false));
    let id = resume(&h);
    enable(&h, &id, 0, true);
    let (entered_tx, entered_rx) = mpsc::sync_channel(1);
    let (release_tx, release_rx) = mpsc::sync_channel(1);
    configure(
        &h,
        Arc::new(AtomicUsize::new(0)),
        false,
        Some((entered_tx, Arc::new(Mutex::new(release_rx)))),
    );
    submit(&h, &id, request("same-turn", 0));
    let worker = {
        let h = Arc::clone(&h);
        let id = id.clone();
        std::thread::spawn(move || op(&h, &id, "same-turn", "prepare"))
    };
    entered_rx.recv_timeout(Duration::from_secs(3)).unwrap();
    let external = host(&path, false);
    let external_id = resume(&external);
    configure(&external, Arc::new(AtomicUsize::new(0)), false, None);
    let committed = commit(&external, &external_id, "same-turn");
    release_tx.send(()).unwrap();
    assert_eq!(worker.join().unwrap(), committed);
    let snapshot = read(&h, &id, 1, 0, player());
    assert_eq!(attempts(&snapshot)[0]["outcome"], "stale");
    assert!(attempts(&snapshot)[0]["stages"]
        .as_array()
        .unwrap()
        .iter()
        .all(|s| s["stage"] != "atomic_commit"));
    assert_eq!(op(&h, &id, "same-turn", "commit"), committed);
    assert_eq!(read(&h, &id, 1, 0, player()), snapshot);
    let mut store = Store::open(&path, None).unwrap();
    assert_eq!(store.resume(&seed().scope).unwrap().engine.revision(), 1);
}
