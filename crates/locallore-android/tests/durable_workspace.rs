// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
use locallore_android::workspace::WorkspaceRegistry;
use serde_json::{json, Value};
use std::{
    path::PathBuf,
    sync::atomic::{AtomicU64, Ordering},
};
static NEXT: AtomicU64 = AtomicU64::new(0);
struct Synthetic(PathBuf);
impl Synthetic {
    fn new() -> Self {
        let directory = std::env::temp_dir().join(format!(
            "locallore-android-durable-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::SeqCst)
        ));
        std::fs::create_dir(&directory).unwrap();
        Self(directory)
    }
    fn path(&self) -> PathBuf {
        self.0.join("synthetic.sqlite3")
    }
}
impl Drop for Synthetic {
    fn drop(&mut self) {
        let _ = std::fs::remove_dir_all(&self.0);
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
fn turn(session: &Value, id: &str, revision: u64) -> Value {
    json!({"version":1,"scope":session["scope"],"turn":id,"expected_revision":revision,
        "intent":{"kind":"actions","value":[{"op":"give","item":"potion","to":"mira","quantity":1}]}})
}
fn scoped(session: &Value, op: &str, id: &str) -> Value {
    json!({"op":op,"session":session["session"],"scope":session["scope"],"turn":id})
}

#[test]
fn app_adapter_reopens_real_sqlite_and_resumes_receipt_without_duplicate_reward() {
    let files = Synthetic::new();
    let registry = WorkspaceRegistry::default();
    let h = registry.open(&files.path()).unwrap();
    let initial = data(call(&registry, h, json!({"op":"workspace"})));
    assert_eq!(initial["persistent"], true);
    assert_eq!(initial["schema_version"], 1);
    let first = data(call(
        &registry,
        h,
        json!({"op":"create","seed":"lantern-quay-v1"}),
    ));
    let request = turn(&first, "android-retry-key", 0);
    data(call(
        &registry,
        h,
        json!({"op":"submit","session":first["session"],"request":request,"mode":"accepted"}),
    ));
    assert_eq!(
        data(call(
            &registry,
            h,
            scoped(&first, "prepare", "android-retry-key")
        ))["phase"],
        "ready"
    );
    let committed = data(call(
        &registry,
        h,
        scoped(&first, "commit", "android-retry-key"),
    ));
    let second = data(call(
        &registry,
        h,
        json!({"op":"create","seed":"lantern-quay-v1"}),
    ));
    assert_ne!(first["scope"], second["scope"]);
    registry.close(h);
    registry.close(h);
    assert!(files.path().is_file());
    assert_eq!(
        call(&registry, h, json!({"op":"workspace"}))["error"],
        "InvalidHandle"
    );
    let reopened = registry.open(&files.path()).unwrap();
    let library = data(call(&registry, reopened, json!({"op":"workspace"})));
    assert_eq!(library["stories"].as_array().unwrap().len(), 2);
    let restored = data(call(
        &registry,
        reopened,
        json!({"op":"resume","scope":first["scope"]}),
    ));
    assert_eq!(restored["revision"], 1);
    assert_eq!(
        data(call(
            &registry,
            reopened,
            scoped(&restored, "turn_status", "android-retry-key")
        ))["receipt"],
        committed["receipt"]
    );
    let snapshot = data(call(
        &registry,
        reopened,
        json!({"op":"play_snapshot","session":restored["session"],"scope":restored["scope"],"expected_revision":1}),
    ));
    assert_eq!(snapshot["receipts"].as_array().unwrap().len(), 1);
    assert!(snapshot["inventory"].get("potion").is_none());
    // Original key remains retry-safe even after all in-memory native owners have gone away.
    assert_eq!(
        data(call(
            &registry,
            reopened,
            scoped(&restored, "commit", "android-retry-key")
        ))["receipt"],
        committed["receipt"]
    );
    let independent = data(call(
        &registry,
        reopened,
        json!({"op":"resume","scope":second["scope"]}),
    ));
    assert_eq!(independent["revision"], 0);
    registry.close(reopened);
}

#[test]
fn prepared_and_cancelled_drafts_do_not_become_canon_on_owner_close_or_reopen() {
    let files = Synthetic::new();
    let registry = WorkspaceRegistry::default();
    let h = registry.open(&files.path()).unwrap();
    let session = data(call(
        &registry,
        h,
        json!({"op":"create","seed":"lantern-quay-v1"}),
    ));
    data(call(
        &registry,
        h,
        json!({"op":"submit","session":session["session"],"request":turn(&session,"draft",0),"mode":"accepted"}),
    ));
    data(call(&registry, h, scoped(&session, "prepare", "draft")));
    assert_eq!(
        data(call(&registry, h, scoped(&session, "cancel", "draft")))["phase"],
        "cancelled"
    );
    registry.close(h);
    let reopened = registry.open(&files.path()).unwrap();
    let restored = data(call(
        &registry,
        reopened,
        json!({"op":"resume","scope":session["scope"]}),
    ));
    assert_eq!(restored["revision"], 0);
    let snapshot = data(call(
        &registry,
        reopened,
        json!({"op":"play_snapshot","session":restored["session"],"scope":restored["scope"],"expected_revision":0}),
    ));
    assert!(snapshot["receipts"].as_array().unwrap().is_empty());
    registry.close(reopened);
}

#[test]
fn durable_jni_adapter_keeps_bounded_errors_and_rejects_foreign_scope_and_closed_handles() {
    let files = Synthetic::new();
    let registry = WorkspaceRegistry::default();
    let h = registry.open(&files.path()).unwrap();
    assert_eq!(
        serde_json::from_slice::<Value>(&registry.call(h, &[b'x'; 24_577])).unwrap()["error"],
        "TooLarge"
    );
    assert_eq!(
        serde_json::from_slice::<Value>(&registry.call(h, b"private non-json")).unwrap()["error"],
        "Malformed"
    );
    let session = data(call(
        &registry,
        h,
        json!({"op":"create","seed":"lantern-quay-v1"}),
    ));
    let mut foreign = scoped(&session, "turn_status", "foreign");
    foreign["scope"]["story"] = json!("other-story");
    assert_eq!(call(&registry, h, foreign)["error"], "Scope");
    registry.close(h);
    assert_eq!(
        call(
            &registry,
            h,
            json!({"op":"create","seed":"lantern-quay-v1"})
        )["error"],
        "InvalidHandle"
    );
}

#[test]
fn workspace_open_failures_release_capacity_and_live_owners_remain_bounded() {
    let files = Synthetic::new();
    let registry = WorkspaceRegistry::default();
    for _ in 0..8 {
        assert!(registry.open(&files.0).is_err());
    }
    let handles: Vec<_> = (0..4)
        .map(|i| {
            registry
                .open(&files.0.join(format!("owner-{i}.sqlite3")))
                .unwrap()
        })
        .collect();
    assert_eq!(registry.open(&files.path()).unwrap_err(), "WorkspaceLimit");
    registry.close(handles[0]);
    let replacement = registry.open(&files.path()).unwrap();
    registry.close(replacement);
    for handle in handles {
        registry.close(handle);
    }
}
