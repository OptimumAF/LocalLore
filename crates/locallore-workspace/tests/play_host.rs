use locallore::{contracts::*, host::Host, inference::*, play::PlayProfile};
use serde_json::{json, Value};
use std::{
    path::PathBuf,
    sync::{
        atomic::{AtomicUsize, Ordering},
        Arc,
    },
    task::Poll,
};

struct Temp(PathBuf);
static TEMP_SEQUENCE: AtomicUsize = AtomicUsize::new(0);
impl Temp {
    fn new() -> Self {
        let p = std::env::temp_dir().join(format!(
            "locallore-play-host-{}-{}-{}",
            std::process::id(),
            TEMP_SEQUENCE.fetch_add(1, Ordering::Relaxed),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        std::fs::create_dir(&p).unwrap();
        Self(p)
    }
    fn host(&self) -> Host {
        locallore_workspace::open(&self.0.join("stories.sqlite"), true).unwrap()
    }
}
impl Drop for Temp {
    fn drop(&mut self) {
        std::fs::remove_dir_all(&self.0).unwrap();
    }
}
fn call(h: &Host, c: Value) -> Value {
    h.call(&serde_json::to_vec(&json!({"version":1,"command":c})).unwrap())
}
fn profile() -> PlayProfile {
    PlayProfile {
        id: "scripted-v2".into(),
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
}
impl InferenceProvider for Script {
    fn poll(&mut self, r: &GenerationRequest, _: &Cancellation) -> Poll<Result<Vec<u8>, Error>> {
        self.calls.fetch_add(1, Ordering::SeqCst);
        assert!(!self.panic, "synthetic provider panic");
        let Input::Structured { role, .. } = &r.input else {
            return Poll::Ready(Err(Error::Provider));
        };
        let out = if role == "director" {
            json!({"commands":[{"op":"give","item":"potion","to":"mira","quantity":1}]})
        } else {
            json!({"text":"You place the potion in Mira's hand with a gentle nod.","speaker":"narrator","event_ids":[r.revision+1]})
        };
        Poll::Ready(Ok(serde_json::to_vec(&out).unwrap()))
    }
}
fn configure(h: &Host, calls: Arc<AtomicUsize>, panic: bool) {
    h.configure_local_provider(
        profile(),
        Arc::new(move || {
            Box::new(Script {
                calls: calls.clone(),
                panic,
            })
        }),
    )
    .unwrap();
}
fn create(h: &Host) -> (String, Value) {
    let v = call(h, json!({"op":"create","seed":"lantern-quay-v1"}));
    assert_eq!(v["status"], "ok");
    (
        v["data"]["session"].as_str().unwrap().into(),
        v["data"]["scope"].clone(),
    )
}
fn request(scope: &Value) -> Value {
    json!({"version":1,"scope":scope,"turn":"original-free-gift","expected_revision":0,"intent":{"kind":"free_text","value":{"kind":"action","text":"I give my last potion to Mira."}}})
}
fn op(h: &Host, id: &str, scope: &Value, op: &str) -> Value {
    call(
        h,
        json!({"op":op,"session":id,"scope":scope,"turn":"original-free-gift"}),
    )
}
fn commit(h: &Host, id: &str, scope: &Value, r: &Value) -> Value {
    assert_eq!(
        call(h, json!({"op":"free_text","session":id,"request":r}))["data"]["phase"],
        "queued"
    );
    assert_eq!(op(h, id, scope, "prepare")["data"]["phase"], "ready");
    let receipt = op(h, id, scope, "commit");
    assert_eq!(receipt["data"]["phase"], "committed");
    receipt
}

#[test]
fn durable_original_free_text_receipt_survives_restart_and_exact_retry_with_no_loaded_model() {
    let temp = Temp::new();
    let h = temp.host();
    let calls = Arc::new(AtomicUsize::new(0));
    configure(&h, calls.clone(), false);
    let (id, scope) = create(&h);
    let r = request(&scope);
    let accepted = commit(&h, &id, &scope, &r);
    assert_eq!(calls.load(Ordering::SeqCst), 2);
    assert_eq!(accepted["data"]["receipt"]["request"], r);
    assert_eq!(accepted["data"]["receipt"]["play"]["version"], 2);
    h.disable_local_provider();
    assert_eq!(
        call(&h, json!({"op":"free_text","session":id,"request":r})),
        accepted
    );
    drop(h);
    let h = temp.host();
    let resumed = call(&h, json!({"op":"resume","scope":scope}));
    let id = resumed["data"]["session"].as_str().unwrap();
    assert_eq!(resumed["data"]["revision"], 1);
    assert_eq!(
        call(&h, json!({"op":"free_text","session":id,"request":r})),
        accepted
    );
    assert_eq!(
        call(
            &h,
            json!({"op":"submit","session":id,"request":r,"mode":"accepted"})
        ),
        accepted
    );
    assert_eq!(op(&h, id, &scope, "turn_status"), accepted);
    let mut changed = r.clone();
    changed["intent"]["value"]["text"] = json!("I keep the potion");
    assert_eq!(
        call(&h, json!({"op":"free_text","session":id,"request":changed}))["error"],
        "RetryMismatch"
    );
    let view = call(
        &h,
        json!({"op":"play_snapshot","session":id,"scope":scope,"expected_revision":1}),
    );
    assert!(view["data"]["inventory"].get("potion").is_none());
    assert_eq!(view["data"]["receipts"].as_array().unwrap().len(), 1);
    assert_eq!(calls.load(Ordering::SeqCst), 2);
}

#[test]
fn unloaded_new_free_text_does_not_persist_a_draft_and_provider_panic_releases_worker() {
    let temp = Temp::new();
    let h = temp.host();
    let (id, scope) = create(&h);
    let r = request(&scope);
    assert_eq!(
        call(&h, json!({"op":"free_text","session":id,"request":r}))["error"],
        "Unsupported"
    );
    assert_eq!(op(&h, &id, &scope, "turn_status")["error"], "UnknownTurn");
    let calls = Arc::new(AtomicUsize::new(0));
    configure(&h, calls, true);
    assert_eq!(
        call(&h, json!({"op":"free_text","session":id,"request":r}))["data"]["phase"],
        "queued"
    );
    let failed = op(&h, &id, &scope, "prepare");
    assert_eq!(failed["data"]["phase"], "failed");
    assert_eq!(failed["data"]["error"], "Provider");
    assert_eq!(h.live_counts(), (1, 0));
    let view = call(
        &h,
        json!({"op":"play_snapshot","session":id,"scope":scope,"expected_revision":0}),
    );
    assert!(view["data"]["inventory"].get("potion").is_some());
    drop(h);
    let h = temp.host();
    let resumed = call(&h, json!({"op":"resume","scope":scope}));
    let id = resumed["data"]["session"].as_str().unwrap();
    let historical_failure = op(&h, id, &scope, "turn_status");
    assert_eq!(historical_failure["data"]["phase"], "failed");
    assert_eq!(
        historical_failure["data"]["error"],
        Value::Null,
        "a terminal phase does not establish an unrecorded historical cause"
    );
}

#[test]
fn ephemeral_committed_retry_is_available_after_provider_unload() {
    let h = Host::new(true);
    let calls = Arc::new(AtomicUsize::new(0));
    configure(&h, calls.clone(), false);
    let (id, scope) = create(&h);
    let r = request(&scope);
    let accepted = commit(&h, &id, &scope, &r);
    h.disable_local_provider();
    assert_eq!(
        call(&h, json!({"op":"free_text","session":id,"request":r})),
        accepted
    );
    assert_eq!(calls.load(Ordering::SeqCst), 2);
}
