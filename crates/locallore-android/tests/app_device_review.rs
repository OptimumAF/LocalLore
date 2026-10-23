// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent app-owner isolation proof through the real SQLite-backed Android registry.
//! This host test does not claim execution of JNI or an Android lifecycle callback.
use locallore_android::workspace::WorkspaceRegistry;
use serde_json::{json, Value};
use std::path::PathBuf;

struct Synthetic(PathBuf);
impl Synthetic {
    fn new() -> Self {
        let path = std::env::temp_dir().join(format!(
            "locallore-app-device-review-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        std::fs::create_dir(&path).unwrap();
        Self(path)
    }
    fn database(&self) -> PathBuf {
        self.0.join("synthetic.sqlite3")
    }
}
impl Drop for Synthetic {
    fn drop(&mut self) {
        std::fs::remove_dir_all(&self.0).unwrap();
    }
}
fn call(registry: &WorkspaceRegistry, handle: u64, command: Value) -> Value {
    serde_json::from_slice(&registry.call(
        handle,
        &serde_json::to_vec(&json!({"version":1,"command":command})).unwrap(),
    ))
    .unwrap()
}
fn data(reply: Value) -> Value {
    assert_eq!(reply["status"], "ok", "{reply}");
    reply["data"].clone()
}
fn turn(registry: &WorkspaceRegistry, handle: u64, session: &Value, key: &str, op: &str) -> Value {
    call(
        registry,
        handle,
        json!({"op":op,"session":session["session"],"scope":session["scope"],"turn":key}),
    )
}
fn submit_and_prepare(registry: &WorkspaceRegistry, handle: u64, session: &Value, key: &str) {
    let request = json!({"version":1,"scope":session["scope"],"turn":key,"expected_revision":0,
        "intent":{"kind":"actions","value":[{"op":"give","item":"potion","to":"mira","quantity":1}]}});
    assert_eq!(
        data(call(
            registry,
            handle,
            json!({"op":"submit","session":session["session"],
            "request":request,"mode":"accepted"})
        ))["phase"],
        "queued"
    );
    assert_eq!(
        data(turn(registry, handle, session, key, "prepare"))["phase"],
        "ready"
    );
}
fn snapshot(registry: &WorkspaceRegistry, handle: u64, session: &Value) -> Value {
    data(call(
        registry,
        handle,
        json!({"op":"play_snapshot","session":session["session"],
        "scope":session["scope"],"expected_revision":1}),
    ))
}

#[test]
fn disposing_one_native_owner_cannot_revoke_another_owner_or_its_saved_receipt() {
    let files = Synthetic::new();
    let registry = WorkspaceRegistry::default();
    let disposed = registry.open(&files.database()).unwrap();
    let survivor = registry.open(&files.database()).unwrap();
    let first = data(call(
        &registry,
        disposed,
        json!({"op":"create","seed":"lantern-quay-v1"}),
    ));
    let second = data(call(
        &registry,
        survivor,
        json!({"op":"resume","scope":first["scope"]}),
    ));
    submit_and_prepare(&registry, disposed, &first, "discarded-owner");
    submit_and_prepare(&registry, survivor, &second, "surviving-owner");

    // Teardown is owner-local. It must not close the shared database or another Host's session.
    registry.close(disposed);
    registry.close(disposed);
    assert_eq!(
        turn(&registry, disposed, &first, "discarded-owner", "commit")["error"],
        "InvalidHandle"
    );
    let committed = data(turn(
        &registry,
        survivor,
        &second,
        "surviving-owner",
        "commit",
    ));
    assert_eq!(committed["phase"], "committed");
    let accepted = snapshot(&registry, survivor, &second);
    assert_eq!(accepted["revision"], 1);
    assert!(accepted["inventory"].get("potion").is_none());
    assert_eq!(accepted["receipts"], json!([committed["receipt"]]));

    let replacement = registry.open(&files.database()).unwrap();
    assert_ne!(replacement, disposed);
    assert_ne!(replacement, survivor);
    let restored = data(call(
        &registry,
        replacement,
        json!({"op":"resume","scope":first["scope"]}),
    ));
    // A delayed duplicate close must not revoke a newly allocated app owner.
    registry.close(disposed);
    assert_eq!(snapshot(&registry, replacement, &restored), accepted);
    assert_eq!(
        data(turn(
            &registry,
            replacement,
            &restored,
            "surviving-owner",
            "commit"
        )),
        committed
    );
    let library = data(call(&registry, replacement, json!({"op":"workspace"})));
    assert_eq!(library["stories"].as_array().unwrap().len(), 1);
    assert_eq!(library["stories"][0]["drafts"], 1);
    // Disposal retains the other owner's uncommitted draft; resume never turns it into canon.
    assert_eq!(accepted["receipts"].as_array().unwrap().len(), 1);
    registry.close(survivor);
    registry.close(replacement);

    let fresh_process_owner = WorkspaceRegistry::default();
    let reopened = fresh_process_owner.open(&files.database()).unwrap();
    let resumed = data(call(
        &fresh_process_owner,
        reopened,
        json!({"op":"resume","scope":first["scope"]}),
    ));
    assert_eq!(snapshot(&fresh_process_owner, reopened, &resumed), accepted);
    fresh_process_owner.close(reopened);
}
