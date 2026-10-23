use locallore::host::Host;
use serde_json::{json, Value};
use std::path::PathBuf;
static NEXT: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
struct Temp(PathBuf);
impl Temp {
    fn new() -> Self {
        let p = std::env::temp_dir().join(format!(
            "locallore-app-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, std::sync::atomic::Ordering::Relaxed)
        ));
        std::fs::create_dir(&p).unwrap();
        Self(p)
    }
    fn host(&self) -> Host {
        locallore_workspace::open(&self.0.join("stories.sqlite"), false).unwrap()
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
fn create(h: &Host) -> (String, Value) {
    let v = call(h, json!({"op":"create","seed":"lantern-quay-v1"}));
    assert_eq!(v["status"], "ok", "{v}");
    (
        v["data"]["session"].as_str().unwrap().into(),
        v["data"]["scope"].clone(),
    )
}
fn request(scope: &Value, turn: &str) -> Value {
    json!({"version":1,"scope":scope,"turn":turn,"expected_revision":0,"intent":{"kind":"actions","value":[{"op":"give","item":"potion","to":"mira","quantity":1}]}})
}
fn op(h: &Host, id: &str, scope: &Value, turn: &str, op: &str) -> Value {
    call(h, json!({"op":op,"session":id,"scope":scope,"turn":turn}))
}
#[test]
fn real_shared_host_save_resume_and_original_turn_lookup() {
    let dir = Temp::new();
    let h = dir.host();
    let (id, scope) = create(&h);
    let r = request(&scope, "saved");
    let workspace = call(&h, json!({"op":"workspace"}));
    assert_eq!(workspace["data"]["persistent"], true);
    assert_eq!(workspace["data"]["schema_version"], 1);
    assert_eq!(workspace["data"]["database_schema_version"], 2);
    assert_eq!(
        call(
            &h,
            json!({"op":"submit","session":id,"request":r,"mode":"accepted"})
        )["data"]["phase"],
        "queued"
    );
    assert_eq!(
        op(&h, &id, &scope, "saved", "prepare")["data"]["phase"],
        "ready"
    );
    let accepted = op(&h, &id, &scope, "saved", "commit");
    assert_eq!(accepted["data"]["phase"], "committed", "{accepted}");
    drop(h);
    let h = dir.host();
    let resumed = call(&h, json!({"op":"resume","scope":scope}));
    let id = resumed["data"]["session"].as_str().unwrap();
    assert_eq!(resumed["data"]["revision"], 1);
    assert_eq!(op(&h, id, &scope, "saved", "turn_status"), accepted);
    assert_eq!(op(&h, id, &scope, "saved", "commit"), accepted);
    assert_eq!(
        call(
            &h,
            json!({"op":"submit","session":id,"request":r,"mode":"accepted"})
        ),
        accepted
    );
    let view = call(
        &h,
        json!({"op":"play_snapshot","session":id,"scope":scope,"expected_revision":1}),
    );
    assert_eq!(view["data"]["receipts"].as_array().unwrap().len(), 1);
    assert!(view["data"]["inventory"].get("potion").is_none());
}
#[test]
fn close_retains_save_and_new_workspaces_never_collide_across_hosts() {
    let dir = Temp::new();
    let h = dir.host();
    let (id, a) = create(&h);
    call(&h, json!({"op":"close","session":id,"scope":a}));
    drop(h);
    let first = dir.host();
    let second = dir.host();
    let (_, b) = create(&first);
    let (_, c) = create(&second);
    assert_ne!(a, b);
    assert_ne!(b, c);
    assert_eq!(
        call(&first, json!({"op":"workspace"}))["data"]["stories"]
            .as_array()
            .unwrap()
            .len(),
        3
    );
    assert_eq!(
        call(&second, json!({"op":"resume","scope":a}))["data"]["revision"],
        0
    );
}
#[test]
fn failure_cancel_and_stale_do_not_publish_partial_saved_canon() {
    let dir = Temp::new();
    let h = dir.host();
    let (id, scope) = create(&h);
    let r = request(&scope, "bad");
    call(
        &h,
        json!({"op":"submit","session":id,"request":r,"mode":"malformed"}),
    );
    assert_eq!(
        op(&h, &id, &scope, "bad", "prepare")["data"]["phase"],
        "failed"
    );
    let r = request(&scope, "cancel");
    call(
        &h,
        json!({"op":"submit","session":id,"request":r,"mode":"accepted"}),
    );
    assert_eq!(
        op(&h, &id, &scope, "cancel", "cancel")["data"]["phase"],
        "cancelled"
    );
    let r = request(&scope, "conflict");
    call(
        &h,
        json!({"op":"submit","session":id,"request":r,"mode":"accepted"}),
    );
    op(&h, &id, &scope, "conflict", "prepare");
    let other = dir.host();
    let resumed = call(&other, json!({"op":"resume","scope":scope}));
    let oid = resumed["data"]["session"].as_str().unwrap();
    let req = request(&scope, "winner");
    call(
        &other,
        json!({"op":"submit","session":oid,"request":req,"mode":"accepted"}),
    );
    op(&other, oid, &scope, "winner", "prepare");
    op(&other, oid, &scope, "winner", "commit");
    assert_eq!(
        op(&h, &id, &scope, "conflict", "commit")["data"]["phase"],
        "stale"
    );
    assert_eq!(
        call(&h, json!({"op":"open","session":id,"scope":scope}))["data"]["revision"],
        1
    );
    drop(h);
    let h = dir.host();
    let resumed = call(&h, json!({"op":"resume","scope":scope}));
    let id = resumed["data"]["session"].as_str().unwrap();
    assert_eq!(
        op(&h, id, &scope, "bad", "turn_status")["data"]["phase"],
        "failed"
    );
    assert_eq!(
        op(&h, id, &scope, "cancel", "turn_status")["data"]["phase"],
        "cancelled"
    );
}
