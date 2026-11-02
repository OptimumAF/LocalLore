// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Real Store/WorkspaceRegistry/Host byte route; no JNI, device, model or raw-DB parity claim.
use locallore::{author_correction::*, contracts::*, engine::Engine};
use locallore_android::workspace::WorkspaceRegistry;
use locallore_storage::Store;
use serde_json::{json, Value};
use std::{
    collections::BTreeMap,
    path::PathBuf,
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT: AtomicU64 = AtomicU64::new(0);

struct Fixture {
    path: PathBuf,
    root: Scope,
    other: Scope,
}

impl Fixture {
    fn new() -> Self {
        let directory = std::env::temp_dir().join(format!(
            "locallore-relationship-focus-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed),
        ));
        assert!(directory.is_absolute());
        #[cfg(windows)]
        assert!(directory.to_string_lossy().starts_with("D:"));
        std::fs::create_dir(&directory).unwrap();
        std::fs::write(
            directory.join("owner-v1"),
            b"synthetic-relationship-focus-v1",
        )
        .unwrap();
        let path = directory.join("stories.sqlite3");
        let mut store = Store::open(&path, None).unwrap();
        let mut seed: Seed =
            serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
        seed.scope.story = "focus-native".into();
        let root = seed.scope.clone();
        let mut upper = seed.actors["mira"].clone();
        upper.name = "PRIVATE_NATIVE_CASE_NAME_69".into();
        seed.actors.insert("Mira".into(), upper);
        seed.relationships.push(Relationship {
            from: "player".into(),
            to: "Mira".into(),
            respect: 21,
            trust: 22,
            obligation: 23,
        });
        store
            .create_story("Synthetic focus story", seed.clone())
            .unwrap();
        seed.scope.story = "other-focus-native".into();
        let other = seed.scope.clone();
        store
            .create_story("Other synthetic focus story", seed)
            .unwrap();
        Self { path, root, other }
    }

    fn canonical(&self, scopes: &[Scope]) -> BTreeMap<String, (Vec<u8>, Vec<u8>)> {
        let mut store = Store::open(&self.path, None).unwrap();
        scopes
            .iter()
            .map(|scope| {
                let engine = store.resume(scope).unwrap().engine;
                (
                    format!("{}/{}", scope.story, scope.branch),
                    (
                        engine.canonical_bytes(),
                        serde_json::to_vec(engine.canonical_records()).unwrap(),
                    ),
                )
            })
            .collect()
    }
}
// Keep these exclusively created synthetic roots for the caller's evidence policy.
// No Drop implementation deletes SQLite, WAL, marker or failed captures.

fn call(registry: &WorkspaceRegistry, handle: u64, command: Value) -> Value {
    let bytes = registry.call(
        handle,
        &serde_json::to_vec(&json!({"version":1,"command":command})).unwrap(),
    );
    assert!(bytes.len() <= 262_144);
    serde_json::from_slice(&bytes).unwrap()
}
fn data(reply: Value) -> Value {
    assert_eq!(reply["version"], 1);
    assert_eq!(reply["status"], "ok", "{reply}");
    reply["data"].clone()
}
fn rejected(reply: Value, error: &str) {
    assert_eq!(
        reply,
        json!({"version":1,"status":"rejected","error":error})
    );
}
fn resume(registry: &WorkspaceRegistry, handle: u64, scope: &Scope) -> Value {
    data(call(registry, handle, json!({"op":"resume","scope":scope})))
}
fn query(session: &Value, head: u64) -> Value {
    json!({"version":2,"scope":session["scope"],"expected_head":head,"at_revision":null,
        "observer":{"kind":"player"},"view":"relationships","limit":8,"search":"","cursor":null})
}
fn focus(session: &Value, query: Value, target: &str) -> Value {
    json!({"op":"inspection_relationship_focus","session":session["session"],"query":query,"target":target})
}
fn dimensions(page: &Value, target: &str) -> BTreeMap<String, i64> {
    assert_eq!(page["version"], 2);
    assert_eq!(page["privacy"], "player_visible");
    assert_eq!(page["view"], "relationships");
    assert_eq!(page["total"], 3);
    assert!(page["next_cursor"].is_null());
    let rows = page["rows"].as_array().unwrap();
    assert_eq!(rows.len(), 3);
    rows.iter()
        .map(|row| {
            assert_eq!(row["kind"], "relationship");
            assert_eq!(row["from"], "player");
            assert_eq!(row["to"], target);
            assert_eq!(row["origin"], "canonical_field");
            (
                row["dimension"].as_str().unwrap().to_owned(),
                row["value"].as_i64().unwrap(),
            )
        })
        .collect()
}
fn apply_wait(store: &mut Store, scope: &Scope) {
    let engine = store.resume(scope).unwrap().engine;
    let request = engine.request(
        "external-current-head",
        Intent::Actions(vec![Command::Wait { ticks: 1 }]),
    );
    let prepared = engine
        .preview(&request, &Engine::proposal(&request).unwrap())
        .unwrap();
    store.begin_turn(&request).unwrap();
    store.commit_prepared(&prepared).unwrap();
}

#[test]
fn durable_host_route_keeps_case_exact_native_rows_and_query_bound_cursors_read_only() {
    let files = Fixture::new();
    let scopes = [files.root.clone(), files.other.clone()];
    let before = files.canonical(&scopes);
    let registry = WorkspaceRegistry::default();
    let handle = registry.open(&files.path).unwrap();
    let session = resume(&registry, handle, &files.root);
    let q = query(&session, 0);
    for (target, value) in [("mira", 1), ("Mira", 21)] {
        let page = data(call(&registry, handle, focus(&session, q.clone(), target)));
        assert_eq!(dimensions(&page, target)["respect"], value);
        assert!(!page.to_string().contains("PRIVATE_NATIVE_CASE_NAME_69"));
    }
    let mut one = q.clone();
    one["limit"] = json!(1);
    let focused = data(call(
        &registry,
        handle,
        focus(&session, one.clone(), "mira"),
    ));
    let ordinary = data(call(
        &registry,
        handle,
        json!({"op":"inspection_query","session":session["session"],"query":one}),
    ));
    assert_ne!(focused["next_cursor"], ordinary["next_cursor"]);
    let mut retag = q.clone();
    retag["limit"] = json!(1);
    retag["cursor"] = focused["next_cursor"].clone();
    rejected(
        call(&registry, handle, focus(&session, retag.clone(), "Mira")),
        "InvalidCursor",
    );
    rejected(
        call(
            &registry,
            handle,
            json!({"op":"inspection_query","session":session["session"],"query":retag}),
        ),
        "InvalidCursor",
    );
    let mut other = q;
    other["scope"] = json!(files.other);
    rejected(
        call(&registry, handle, focus(&session, other, "mira")),
        "Scope",
    );
    registry.close(handle);
    assert_eq!(files.canonical(&scopes), before);
}

#[test]
fn durable_dispatch_refuses_malformed_private_and_closed_requests_without_echoing_payloads() {
    let files = Fixture::new();
    let scopes = [files.root.clone(), files.other.clone()];
    let before = files.canonical(&scopes);
    let registry = WorkspaceRegistry::default();
    let handle = registry.open(&files.path).unwrap();
    let session = resume(&registry, handle, &files.root);
    let q = query(&session, 0);
    let mut private = q.clone();
    private["observer"] = json!({"kind":"character","id":"mira"});
    rejected(
        call(&registry, handle, focus(&session, private, "player")),
        "Forbidden",
    );
    let mut wrong = q.clone();
    wrong["version"] = json!(1);
    rejected(
        call(&registry, handle, focus(&session, wrong, "mira")),
        "Version",
    );
    wrong = q.clone();
    wrong["view"] = json!("profiles");
    rejected(
        call(&registry, handle, focus(&session, wrong, "mira")),
        "InvalidRequest",
    );
    wrong = q.clone();
    wrong["search"] = json!("mira");
    rejected(
        call(&registry, handle, focus(&session, wrong, "mira")),
        "InvalidRequest",
    );
    let normal = focus(&session, q.clone(), "mira");
    let mut extra = normal.clone();
    extra["grant"] = json!(true);
    let mut missing = normal.clone();
    missing.as_object_mut().unwrap().remove("target");
    let mut wrong_type = normal.clone();
    wrong_type["target"] = json!(17);
    let mut nested = normal.clone();
    nested["query"]["target"] = json!("mira");
    for command in [
        extra,
        missing,
        wrong_type,
        nested,
        focus(&session, q.clone(), "SECRET_INJECTION_69\n"),
    ] {
        let reply = call(&registry, handle, command);
        assert_eq!(reply["status"], "rejected");
        assert!(reply.get("data").is_none());
        assert!(!reply.to_string().contains("SECRET_INJECTION_69"));
    }
    let mut closed_session = normal.clone();
    closed_session["session"] = json!("unknown-session");
    rejected(call(&registry, handle, closed_session), "Closed");
    registry.close(handle);
    rejected(call(&registry, handle, normal), "InvalidHandle");
    assert_eq!(files.canonical(&scopes), before);
}

#[test]
fn fresh_persistence_head_corrected_child_and_reopen_do_not_reuse_stale_session_data() {
    let files = Fixture::new();
    let registry = WorkspaceRegistry::default();
    let handle = registry.open(&files.path).unwrap();
    let stale_session = resume(&registry, handle, &files.root);
    let mut store = Store::open(&files.path, None).unwrap();
    apply_wait(&mut store, &files.root);
    let parent = store.resume(&files.root).unwrap().engine;
    let correction = AuthorCorrectionInputV1 {
        version: 1,
        parent: files.root.clone(),
        expected_parent_revision: 1,
        fork_revision: 1,
        child_branch: "corrected".into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(),
            expected_proposition: parent.seed().facts["relic-location"].proposition.clone(),
            replacement: "PRIVATE_DURABLE_WORLD_69".into(),
        },
        reason: "PRIVATE_DURABLE_REASON_69".into(),
    };
    let prepared = store
        .prepare_author_correction(&correction, &|| false)
        .unwrap();
    store.apply_author_correction(&prepared, &|| false).unwrap();
    let child = Scope {
        story: files.root.story.clone(),
        branch: "corrected".into(),
    };
    assert_eq!(store.resume(&child).unwrap().engine.domain_version(), 2);
    drop(store);
    let scopes = [files.root.clone(), files.other.clone(), child.clone()];
    let before = files.canonical(&scopes);
    rejected(
        call(
            &registry,
            handle,
            focus(&stale_session, query(&stale_session, 0), "mira"),
        ),
        "Stale",
    );
    let fresh = data(call(
        &registry,
        handle,
        focus(&stale_session, query(&stale_session, 1), "mira"),
    ));
    assert_eq!(dimensions(&fresh, "mira")["trust"], 2);
    let selected = resume(&registry, handle, &child);
    let child_page = data(call(
        &registry,
        handle,
        focus(&selected, query(&selected, 2), "Mira"),
    ));
    assert_eq!(dimensions(&child_page, "Mira")["trust"], 22);
    assert!(!child_page.to_string().contains("PRIVATE_DURABLE_WORLD_69"));
    assert!(!child_page.to_string().contains("PRIVATE_DURABLE_REASON_69"));
    registry.close(handle);
    let reopened = registry.open(&files.path).unwrap();
    let selected = resume(&registry, reopened, &child);
    let again = data(call(
        &registry,
        reopened,
        focus(&selected, query(&selected, 2), "Mira"),
    ));
    assert_eq!(again, child_page);
    registry.close(reopened);
    assert_eq!(files.canonical(&scopes), before);
}
