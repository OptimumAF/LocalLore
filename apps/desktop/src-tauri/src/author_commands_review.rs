// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen before broker production. SOURCE ONLY, UNCOMPILED/UNRUN.
//! Actual Repository/Store/Host/worker; no model, forged receipt or canonical SQL.
use super::*;
use locallore::{
    contracts::{Command, Intent, Seed},
    engine::Engine,
};
use locallore_storage::{ForkRequest, Store};
use std::{
    path::PathBuf,
    sync::{
        atomic::{AtomicU64, Ordering},
        mpsc,
    },
    time::{Duration, Instant},
};

static NEXT: AtomicU64 = AtomicU64::new(0);
const OLD: &str = "PRIVATE_DESKTOP_OLD_A";
const NEW: &str = "PRIVATE_DESKTOP_NEW_B";
const REASON: &str = "PRIVATE_DESKTOP_AUTHOR_REASON";
struct Fixture {
    root: PathBuf,
    parent: Scope,
    host: Arc<Host>,
    session: String,
    lease: Arc<WindowLease>,
    broker: Arc<ArchiveBroker>,
    manager: Arc<AuthorManager>,
    epoch: u64,
}
impl Fixture {
    fn new(grant: bool) -> Self {
        let root = std::env::temp_dir().join(format!(
            "locallore-author-broker-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&root).unwrap();
        let mut seed: Seed =
            serde_json::from_str(include_str!("../../../../fixtures/lantern_quay.json")).unwrap();
        let fact = seed.facts.get_mut("relic-location").unwrap();
        fact.proposition = OLD.into();
        fact.discoverable_at = Some("quay".into());
        fact.known_by.insert("mira".into());
        let parent = seed.scope.clone();
        Store::open_application(&root.join("synthetic.sqlite"))
            .unwrap()
            .create_story("Synthetic author broker", seed)
            .unwrap();
        let host =
            Arc::new(locallore_workspace::open(&root.join("synthetic.sqlite"), grant).unwrap());
        let session = resume(&host, &parent);
        let lease = Arc::new(WindowLease::default());
        let epoch = lease.begin().unwrap();
        let broker = Arc::new(ArchiveBroker::default());
        let manager = AuthorManager::new(&host, &lease, &broker, epoch).unwrap();
        Self {
            root,
            parent,
            host,
            session,
            lease,
            broker,
            manager,
            epoch,
        }
    }
    fn store(&self) -> Store {
        Store::open_application(&self.root.join("synthetic.sqlite")).unwrap()
    }
    fn engine(&self, scope: &Scope) -> Engine {
        self.store().resume(scope).unwrap().engine
    }
    fn input(&self, child: &str) -> Value {
        json!({"version":1,"parent":self.parent,"expected_parent_revision":0,"fork_revision":0,"child_branch":child,
            "operation":{"op":"replace_fact_proposition","fact":"relic-location","expected_proposition":OLD,"replacement":NEW},"reason":REASON})
    }
    fn prepare_raw(&self, input: Value) -> String {
        json!({"version":1,"session":self.session,"input":input,"author_consent":true}).to_string()
    }
    fn commit_raw(&self, input: Value, preview: &Value) -> String {
        json!({"version":1,"session":self.session,"input":input,"preview_token":preview["preview_token"],"preview_sha256":preview["preview_sha256"],"confirmed":true}).to_string()
    }
    fn prepare_start(&self, raw: &str) -> Result<Value, String> {
        self.manager.prepare_start(
            self.host.clone(),
            self.lease.clone(),
            self.broker.clone(),
            self.epoch,
            raw,
        )
    }
    fn commit_start(&self, raw: &str) -> Result<Value, String> {
        self.manager.commit_start(
            self.host.clone(),
            self.lease.clone(),
            self.broker.clone(),
            self.epoch,
            raw,
        )
    }
    fn lookup_start(&self, input: Value) -> Value {
        self.manager
            .lookup_start(
                self.host.clone(),
                self.lease.clone(),
                self.broker.clone(),
                self.epoch,
                &json!({"version":1,"input":input,"author_consent":true}).to_string(),
            )
            .unwrap()
    }
    fn wait(&self, start: Value) -> Value {
        let id = start["operation_id"].as_u64().unwrap();
        let deadline = Instant::now() + Duration::from_secs(5);
        loop {
            let status = self.broker.status(&self.lease, self.epoch, id).unwrap();
            if status["running"] == false {
                self.broker.drain(self.epoch);
                return status;
            }
            assert!(
                Instant::now() < deadline,
                "bounded shared worker must finish"
            );
            std::thread::sleep(Duration::from_millis(2));
        }
    }
    fn result(&self, start: Value) -> Value {
        let status = self.wait(start);
        assert_eq!(status["error"], Value::Null, "{status}");
        status["result"].clone()
    }
    fn preview(&self, input: Value) -> Value {
        self.result(self.prepare_start(&self.prepare_raw(input)).unwrap())
    }
    fn missing(&self, input: &Value) {
        let scope = Scope {
            story: self.parent.story.clone(),
            branch: input["child_branch"].as_str().unwrap().into(),
        };
        assert!(self.store().resume(&scope).is_err());
    }
    fn append_wait(&self, scope: &Scope, key: &str) {
        let mut store = self.store();
        let engine = store.resume(scope).unwrap().engine;
        let request = engine.request(key, Intent::Actions(vec![Command::Wait { ticks: 1 }]));
        let receipt = engine
            .preview(&request, &Engine::proposal(&request).unwrap())
            .unwrap();
        store.begin_turn(&request).unwrap();
        store.commit_prepared(&receipt).unwrap();
    }
}
impl Drop for Fixture {
    fn drop(&mut self) {
        self.manager.retire(self.epoch);
        self.broker.retire(self.epoch);
        self.broker.drain(self.epoch);
        self.host.close_all();
        let host = std::mem::replace(&mut self.host, Arc::new(Host::new(false)));
        drop(host);
        if let Err(error) = std::fs::remove_dir_all(&self.root) {
            if !std::thread::panicking() {
                panic!("owned fixture cleanup: {error}");
            }
        }
    }
}
fn call(host: &Host, command: Value) -> Value {
    host.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
}
fn resume(host: &Host, scope: &Scope) -> String {
    let value = call(host, json!({"op":"resume","scope":scope}));
    assert_eq!(value["status"], "ok", "{value}");
    value["data"]["session"].as_str().unwrap().into()
}
fn err<T>(value: Result<T, String>, expected: &str) {
    match value {
        Err(actual) => assert_eq!(actual, expected),
        Ok(_) => panic!("expected {expected}"),
    }
}
fn keys(value: &Value, expected: &[&str]) {
    let object = value.as_object().unwrap();
    assert_eq!(object.len(), expected.len());
    assert!(expected.iter().all(|key| object.contains_key(*key)));
}

#[test]
fn strict_raw_duplicate_unknown_numeric_consent_and_bounded_input_are_closed() {
    let f = Fixture::new(true);
    let good = f.prepare_raw(f.input("strict"));
    assert!(parse_prepare(&good).is_ok());
    for replacement in ["-1", "1.0", "1e0", "9007199254740992", "\"0\"", "null"] {
        let raw = good.replace(
            "\"expected_parent_revision\":0",
            &format!("\"expected_parent_revision\":{replacement}"),
        );
        assert!(parse_prepare(&raw).is_err(), "{replacement}");
    }
    for raw in [
        good.replacen("{", "{\"version\":1,", 1),
        good.replace("\"reason\":", "\"reason\":\"duplicate\",\"reason\":"),
        good.replace(
            "\"reason\":",
            "\"re\\u0061son\":\"escapedduplicate\",\"reason\":",
        ),
    ] {
        assert!(parse_prepare(&raw).is_err());
    }
    for path in ["top", "parent", "operation"] {
        let mut value: Value = serde_json::from_str(&good).unwrap();
        match path {
            "top" => value["grant"] = json!(true),
            "parent" => value["input"]["parent"]["root"] = json!("path"),
            _ => value["input"]["operation"]["command"] = json!("shell"),
        };
        assert!(parse_prepare(&value.to_string()).is_err());
    }
    let mut value: Value = serde_json::from_str(&good).unwrap();
    value["author_consent"] = json!(false);
    err(parse_prepare(&value.to_string()), "AuthorConsentRequired");
    err(parse_prepare(&" ".repeat(65537)), "TooLarge");
    let mut input = f.input("strict");
    input["operation"]["replacement"] = json!(OLD);
    assert!(parse_prepare(&f.prepare_raw(input)).is_err());
    f.missing(&f.input("strict"));
}

#[test]
fn exact_core_preview_is_private_readonly_and_preserves_escaped_input_above_generic_cap() {
    let f = Fixture::new(true);
    let mut input = f.input("exact");
    input["reason"] = json!("\u{1}".repeat(2048));
    input["operation"]["replacement"] = json!("\u{2}".repeat(2048));
    let raw = f.prepare_raw(input.clone());
    assert!(raw.len() > locallore::host::MAX_INPUT);
    assert!(raw.len() <= 65536);
    let parent = f.engine(&f.parent);
    let before = parent.accepted_history_basis().unwrap();
    let native = parse_prepare(&raw).unwrap();
    let core = parent
        .prepare_author_correction(&native.input, &|| false)
        .unwrap();
    let preview = f.result(f.prepare_start(&raw).unwrap());
    keys(
        &preview,
        &[
            "version",
            "kind",
            "session",
            "preview_token",
            "preview_sha256",
            "preview_json",
            "expires_seconds",
        ],
    );
    assert_eq!(preview["version"], 1);
    assert_eq!(preview["kind"], "author_preview");
    assert_eq!(preview["session"], f.session);
    assert_eq!(preview["expires_seconds"], 600);
    let bytes = preview["preview_json"].as_str().unwrap().as_bytes();
    assert_eq!(bytes, serde_json::to_vec(core.preview()).unwrap());
    assert_eq!(
        preview["preview_sha256"],
        locallore::inspection::sha256(bytes)
    );
    assert!(crate::archive::valid_id(
        preview["preview_token"].as_str().unwrap()
    ));
    assert!(serde_json::to_vec(&preview).unwrap().len() <= locallore::host::MAX_OUTPUT);
    assert_eq!(
        f.engine(&f.parent).accepted_history_basis().unwrap(),
        before
    );
    f.missing(&input);
}

#[test]
fn actual_commit_known_operation_status_and_exact_lookup_preserve_original_and_old_knower() {
    let f = Fixture::new(true);
    let input = f.input("commit");
    let original = f.engine(&f.parent).accepted_history_basis().unwrap();
    let preview = f.preview(input.clone());
    let started = f
        .commit_start(&f.commit_raw(input.clone(), &preview))
        .unwrap();
    let id = started["operation_id"].as_u64().unwrap();
    let status = f.wait(started);
    assert_eq!(status["error"], Value::Null, "{status}");
    let committed = &status["result"];
    keys(committed, &["version", "kind", "session", "outcome"]);
    assert_eq!(committed["kind"], "author_commit");
    assert_eq!(committed["outcome"]["created"], true);
    // A known operation ID can recover the same retained terminal result slot.
    assert_eq!(f.broker.status(&f.lease, f.epoch, id).unwrap(), status);
    let scope: Scope = serde_json::from_value(committed["outcome"]["scope"].clone()).unwrap();
    let child = f.engine(&scope);
    assert_eq!(child.canonical_records().len(), 1);
    assert_eq!(
        child.effective_fact("relic-location").unwrap().proposition,
        NEW
    );
    assert_eq!(
        child.observed_facts("mira", &scope, 1).unwrap()["relic-location"].proposition,
        OLD
    );
    assert_eq!(
        f.engine(&f.parent).accepted_history_basis().unwrap(),
        original
    );
    err(
        f.commit_start(&f.commit_raw(input.clone(), &preview)),
        "UnknownAuthorPreview",
    );
    let lookup = f.result(f.lookup_start(input));
    keys(&lookup, &["version", "kind", "found", "outcome"]);
    assert_eq!(lookup["found"], true);
    assert_eq!(lookup["outcome"]["created"], false);
    assert_eq!(lookup["outcome"]["scope"], json!(scope));
    assert_eq!(
        f.engine(&scope).canonical_records(),
        child.canonical_records()
    );
}

#[test]
fn commit_and_lookup_strict_raw_parsers_do_not_consume_on_malformed_input() {
    let f = Fixture::new(true);
    let input = f.input("all-parsers");
    let preview = f.preview(input.clone());
    let commit = f.commit_raw(input.clone(), &preview);
    let lookup = json!({"version":1,"input":input,"author_consent":true}).to_string();
    assert!(parse_commit(&commit).is_ok());
    assert!(parse_lookup(&lookup).is_ok());
    for base in [&commit, &lookup] {
        for malformed in [
            base.replacen("{", "{\"version\":1,", 1),
            base.replace("\"reason\":", "\"reason\":\"duplicate\",\"reason\":"),
            base.replace("\"fork_revision\":0", "\"fork_revision\":1.0"),
            base.replace("\"fork_revision\":0", "\"fork_revision\":9007199254740992"),
        ] {
            if base == &commit {
                assert!(f.commit_start(&malformed).is_err());
            } else {
                assert!(parse_lookup(&malformed).is_err());
            }
        }
        let mut unknown: Value = serde_json::from_str(base).unwrap();
        unknown["permission"] = json!(true);
        if base == &commit {
            assert!(f.commit_start(&unknown.to_string()).is_err());
        } else {
            assert!(parse_lookup(&unknown.to_string()).is_err());
        }
    }
    err(parse_commit(&" ".repeat(65537)), "TooLarge");
    err(parse_lookup(&" ".repeat(65537)), "TooLarge");
    let mut denied: Value = serde_json::from_str(&lookup).unwrap();
    denied["author_consent"] = json!(false);
    err(parse_lookup(&denied.to_string()), "AuthorConsentRequired");
    f.missing(&input);
    assert_eq!(
        f.result(f.commit_start(&commit).unwrap())["outcome"]["created"],
        true
    );
}

#[test]
fn lost_start_ack_without_operation_id_recovers_by_readonly_exact_lookup_only() {
    let f = Fixture::new(true);
    let input = f.input("lost-start-ack");
    let preview = f.preview(input.clone());
    let (entered, seen) = mpsc::channel();
    let (release, wait) = mpsc::channel();
    *f.manager.test_gate.lock().unwrap() = Some(TestGate {
        after_apply: true,
        entered,
        release: wait,
    });
    // Simulate a transport dropping the complete start response, including its ID.
    drop(
        f.commit_start(&f.commit_raw(input.clone(), &preview))
            .unwrap(),
    );
    seen.recv_timeout(Duration::from_secs(5)).unwrap();
    release.send(()).unwrap();
    // Fixture owns native cleanup, not an application-side invented latest-ID API.
    f.broker.drain(f.epoch);
    let lookup = f.result(f.lookup_start(input.clone()));
    assert_eq!(lookup["found"], true);
    assert_eq!(lookup["outcome"]["created"], false);
    let scope: Scope = serde_json::from_value(lookup["outcome"]["scope"].clone()).unwrap();
    assert_eq!(f.engine(&scope).canonical_records().len(), 1);
    err(
        f.commit_start(&f.commit_raw(input, &preview)),
        "UnknownAuthorPreview",
    );
}

#[test]
fn second_consent_and_exact_session_input_digest_are_required_before_consumption() {
    let f = Fixture::new(true);
    for variant in ["session", "input", "digest"] {
        let input = f.input(variant);
        let preview = f.preview(input.clone());
        let raw = f.commit_raw(input.clone(), &preview);
        let mut value: Value = serde_json::from_str(&raw).unwrap();
        value["confirmed"] = json!(false);
        err(f.commit_start(&value.to_string()), "AuthorConsentRequired");
        f.missing(&input);
        value["confirmed"] = json!(true);
        match variant {
            "session" => value["session"] = json!("session-other"),
            "input" => value["input"]["reason"] = json!("edited"),
            _ => value["preview_sha256"] = json!("a".repeat(64)),
        };
        err(f.commit_start(&value.to_string()), "AuthorPreviewMismatch");
        f.missing(&input);
        assert_eq!(
            f.result(f.commit_start(&raw).unwrap())["outcome"]["created"],
            true
        );
    }
}

#[test]
fn bounded_native_discard_checks_owner_session_token_and_frees_unused_preview() {
    let f = Fixture::new(true);
    let input = f.input("discard");
    let preview = f.preview(input.clone());
    let token = preview["preview_token"].as_str().unwrap();
    err(
        f.manager
            .discard_preview(&f.host, &f.lease, f.epoch, "different-session", token),
        "AuthorPreviewMismatch",
    );
    let foreign =
        Arc::new(locallore_workspace::open(&f.root.join("synthetic.sqlite"), true).unwrap());
    err(
        f.manager
            .discard_preview(&foreign, &f.lease, f.epoch, &f.session, token),
        "Integrity",
    );
    assert!(f
        .manager
        .discard_preview(&f.host, &f.lease, f.epoch, &f.session, token)
        .unwrap());
    assert!(!f
        .manager
        .discard_preview(&f.host, &f.lease, f.epoch, &f.session, token)
        .unwrap());
    err(
        f.commit_start(&f.commit_raw(input.clone(), &preview)),
        "UnknownAuthorPreview",
    );
    f.missing(&input);
    for n in 0..4 {
        f.preview(f.input(&format!("after-discard-{n}")));
    }
}

#[test]
fn native_grant_foreign_host_window_and_epoch_cannot_mint_or_consume_authority() {
    let ordinary = Fixture::new(false);
    let input = ordinary.input("grant");
    let failed = ordinary.wait(
        ordinary
            .prepare_start(&ordinary.prepare_raw(input.clone()))
            .unwrap(),
    );
    assert_eq!(failed["error"], "Forbidden");
    ordinary.missing(&input);
    let f = Fixture::new(true);
    let input = f.input("owner");
    let preview = f.preview(input.clone());
    let raw = f.commit_raw(input.clone(), &preview);
    let foreign =
        Arc::new(locallore_workspace::open(&f.root.join("synthetic.sqlite"), true).unwrap());
    resume(&foreign, &f.parent);
    err(
        f.manager
            .commit_start(foreign, f.lease.clone(), f.broker.clone(), f.epoch, &raw),
        "Integrity",
    );
    let lease = Arc::new(WindowLease::default());
    let epoch = lease.begin().unwrap();
    assert_eq!(epoch, f.epoch);
    err(
        f.manager
            .commit_start(f.host.clone(), lease, f.broker.clone(), epoch, &raw),
        "Integrity",
    );
    err(
        f.manager.commit_start(
            f.host.clone(),
            f.lease.clone(),
            f.broker.clone(),
            f.epoch + 2,
            &raw,
        ),
        "Closed",
    );
    assert_eq!(
        f.result(f.commit_start(&raw).unwrap())["outcome"]["created"],
        true
    );
}

#[test]
fn four_cap_bound_expiration_retirement_and_invalidated_window_are_closed() {
    let f = Fixture::new(true);
    let mut previews = Vec::new();
    for n in 0..4 {
        previews.push(f.preview(f.input(&format!("cap-{n}"))));
    }
    let excess = f.wait(f.prepare_start(&f.prepare_raw(f.input("cap-5"))).unwrap());
    assert_eq!(excess["error"], "AuthorPreviewLimit");
    // Direct private clock fixture setup; production uses actual Instant/600-second TTL.
    {
        let mut state = f.manager.caps.lock().unwrap();
        state
            .get_mut(previews[0]["preview_token"].as_str().unwrap())
            .unwrap()
            .created = Instant::now() - Duration::from_secs(601);
    }
    err(
        f.commit_start(&f.commit_raw(f.input("cap-0"), &previews[0])),
        "UnknownAuthorPreview",
    );
    let fresh = f.preview(f.input("fresh"));
    f.manager.retire(f.epoch);
    err(
        f.commit_start(&f.commit_raw(f.input("fresh"), &fresh)),
        "UnknownAuthorPreview",
    );
    let fresh = f.preview(f.input("invalidation"));
    let closed = f.lease.invalidate(&format!("main-{}", f.epoch)).unwrap();
    err(
        f.commit_start(&f.commit_raw(f.input("invalidation"), &fresh)),
        "Closed",
    );
    f.manager.retire(f.epoch);
    assert!(f.manager.caps.lock().unwrap().is_empty());
    f.lease.finish_close(closed, || {});
    f.missing(&f.input("invalidation"));
}

#[test]
fn actual_parent_advance_stales_plan_without_child_and_pending_gameplay_key_is_preserved() {
    let f = Fixture::new(true);
    let input = f.input("stale");
    let preview = f.preview(input.clone());
    f.append_wait(&f.parent, "actual-parent-append");
    let failed = f.wait(
        f.commit_start(&f.commit_raw(input.clone(), &preview))
            .unwrap(),
    );
    assert_eq!(failed["error"], "Stale");
    f.missing(&input);
    let mut fresh = f.input("busy");
    fresh["expected_parent_revision"] = json!(1);
    let preview = f.preview(fresh.clone());
    let engine = f.engine(&f.parent);
    let request = engine.request(
        "existing-pending-key",
        Intent::Actions(vec![Command::Wait { ticks: 1 }]),
    );
    let queued = call(
        &f.host,
        json!({"op":"submit","session":f.session,"request":request,"mode":"accepted"}),
    );
    assert_eq!(queued["data"]["phase"], "queued");
    let failed = f.wait(
        f.commit_start(&f.commit_raw(fresh.clone(), &preview))
            .unwrap(),
    );
    assert_eq!(failed["error"], "Busy");
    f.missing(&fresh);
    let status = call(
        &f.host,
        json!({"op":"turn_status","session":f.session,"scope":f.parent,"turn":request.turn}),
    );
    assert_eq!(status["data"]["phase"], "queued");
    let cancelled = call(
        &f.host,
        json!({"op":"cancel","session":f.session,"scope":f.parent,"turn":request.turn}),
    );
    assert_eq!(cancelled["data"]["phase"], "cancelled");
}

#[test]
fn same_worker_busy_valid_attempt_is_consumed_and_no_second_worker_or_write_occurs() {
    let f = Fixture::new(true);
    let input = f.input("worker-busy");
    let preview = f.preview(input.clone());
    let (entered, seen) = mpsc::channel();
    let (release, wait) = mpsc::channel();
    let busy = f
        .broker
        .start(f.lease.clone(), f.epoch, move |work| {
            entered.send(()).unwrap();
            wait.recv_timeout(Duration::from_secs(5))
                .map_err(|_| "TestTimeout".to_owned())?;
            work.check()?;
            Ok(json!({"synthetic":true}))
        })
        .unwrap();
    seen.recv_timeout(Duration::from_secs(5)).unwrap();
    let result = f.commit_start(&f.commit_raw(input.clone(), &preview));
    release.send(()).unwrap();
    f.wait(busy);
    err(result, "ArchiveBusy");
    err(
        f.commit_start(&f.commit_raw(input.clone(), &preview)),
        "UnknownAuthorPreview",
    );
    f.missing(&input);
    let fresh = f.preview(input.clone());
    assert_eq!(
        f.result(f.commit_start(&f.commit_raw(input, &fresh)).unwrap())["outcome"]["created"],
        true
    );
}

#[test]
fn cancel_before_apply_retires_cap_and_late_commit_cannot_be_demoted() {
    for after in [false, true] {
        let f = Fixture::new(true);
        let input = f.input(if after { "late" } else { "cancel" });
        let preview = f.preview(input.clone());
        let (entered, seen) = mpsc::channel();
        let (release, wait) = mpsc::channel();
        *f.manager.test_gate.lock().unwrap() = Some(TestGate {
            after_apply: after,
            entered,
            release: wait,
        });
        let started = f
            .commit_start(&f.commit_raw(input.clone(), &preview))
            .unwrap();
        let id = started["operation_id"].as_u64().unwrap();
        seen.recv_timeout(Duration::from_secs(5)).unwrap();
        f.broker.cancel(&f.lease, f.epoch, id).unwrap();
        release.send(()).unwrap();
        let status = f.wait(started);
        if after {
            assert_eq!(status["error"], Value::Null, "{status}");
            assert_eq!(status["result"]["outcome"]["created"], true);
            assert_eq!(f.result(f.lookup_start(input.clone()))["found"], true);
        } else {
            assert_eq!(status["error"], "Cancelled");
            f.missing(&input);
        }
        err(
            f.commit_start(&f.commit_raw(input, &preview)),
            "UnknownAuthorPreview",
        );
    }
}

#[test]
fn readonly_lookup_after_parent_retirement_and_tombstone_preserves_real_store_semantics() {
    let f = Fixture::new(true);
    let parent = f
        .store()
        .fork_branch(
            &ForkRequest {
                parent: f.parent.clone(),
                child_branch: "retained-parent".into(),
                expected_parent_revision: 0,
                at_revision: 0,
            },
            &|| false,
        )
        .unwrap()
        .scope;
    f.append_wait(&parent, "excluded-future");
    let session = resume(&f.host, &parent);
    let mut input = f.input("retained-child");
    input["parent"] = json!(parent);
    input["expected_parent_revision"] = json!(1);
    let raw =
        json!({"version":1,"session":session,"input":input,"author_consent":true}).to_string();
    let preview = f.result(f.prepare_start(&raw).unwrap());
    let raw=json!({"version":1,"session":session,"input":input,"preview_token":preview["preview_token"],"preview_sha256":preview["preview_sha256"],"confirmed":true}).to_string();
    let committed = f.result(f.commit_start(&raw).unwrap());
    let child: Scope = serde_json::from_value(committed["outcome"]["scope"].clone()).unwrap();
    f.append_wait(&parent, "later-parent");
    let mut store = f.store();
    let plan = store
        .prepare_branch_deletion(&parent, 2, &|| false)
        .unwrap();
    store.delete_branch(plan, &|| false).unwrap();
    drop(store);
    let lookup = f.result(f.lookup_start(input.clone()));
    assert_eq!(lookup["found"], true);
    assert_eq!(lookup["outcome"]["created"], false);
    let mut changed = input.clone();
    changed["reason"] = json!("different");
    let failed = f.wait(f.lookup_start(changed));
    assert_eq!(failed["error"], "RetryMismatch");
    let mut absent = input.clone();
    absent["child_branch"] = json!("actually-missing");
    let missing = f.result(f.lookup_start(absent));
    assert_eq!(missing["found"], false);
    assert_eq!(missing["outcome"], Value::Null);
    let mut store = f.store();
    let plan = store.prepare_branch_deletion(&child, 1, &|| false).unwrap();
    store.delete_branch(plan, &|| false).unwrap();
    drop(store);
    let failed = f.wait(f.lookup_start(input));
    assert_eq!(failed["error"], "NotFound");
}

#[test]
fn explicit_retirement_or_window_destruction_before_apply_cannot_write_or_publish() {
    for destroyed in [false, true] {
        let f = Fixture::new(true);
        let input = f.input(if destroyed {
            "destroyed"
        } else {
            "retired-active"
        });
        let preview = f.preview(input.clone());
        let (entered, seen) = mpsc::channel();
        let (release, wait) = mpsc::channel();
        *f.manager.test_gate.lock().unwrap() = Some(TestGate {
            after_apply: false,
            entered,
            release: wait,
        });
        let started = f
            .commit_start(&f.commit_raw(input.clone(), &preview))
            .unwrap();
        let id = started["operation_id"].as_u64().unwrap();
        seen.recv_timeout(Duration::from_secs(5)).unwrap();
        let closed = destroyed.then(|| f.lease.invalidate(&format!("main-{}", f.epoch)).unwrap());
        f.manager.retire(f.epoch);
        release.send(()).unwrap();
        if let Some(closed) = closed {
            f.broker.retire(f.epoch);
            f.broker.drain(f.epoch);
            err(f.broker.status(&f.lease, f.epoch, id), "Closed");
            f.lease.finish_close(closed, || {});
        } else {
            assert_eq!(f.wait(started)["error"], "Cancelled");
        }
        f.missing(&input);
        assert!(f.manager.caps.lock().unwrap().is_empty());
    }
}

#[test]
fn foreign_archive_broker_cannot_bypass_shared_busy_or_consume_a_valid_capability() {
    let f = Fixture::new(true);
    let input = f.input("foreign-broker-commit");
    let preview = f.preview(input.clone());
    let before = f.engine(&f.parent).canonical_bytes();
    let (entered, seen) = mpsc::channel();
    let (release, wait) = mpsc::channel();
    let busy = f
        .broker
        .start(f.lease.clone(), f.epoch, move |work| {
            entered.send(()).unwrap();
            wait.recv_timeout(Duration::from_secs(5))
                .map_err(|_| "TestTimeout".to_owned())?;
            work.check()?;
            Ok(json!({"synthetic":true}))
        })
        .unwrap();
    seen.recv_timeout(Duration::from_secs(5)).unwrap();
    let mut results = Vec::new();
    // Even an otherwise correct Host/window/epoch/input cannot substitute another
    // worker owner. Drain each owned foreign broker before any assertion, so the
    // predicted pre-fix admission failure cannot leave a test worker using Store.
    for kind in ["prepare", "commit", "lookup"] {
        let foreign = Arc::new(ArchiveBroker::default());
        let result = match kind {
            "prepare" => f.manager.prepare_start(
                f.host.clone(),
                f.lease.clone(),
                foreign.clone(),
                f.epoch,
                &f.prepare_raw(f.input("foreign-broker-prepare")),
            ),
            "commit" => f.manager.commit_start(
                f.host.clone(),
                f.lease.clone(),
                foreign.clone(),
                f.epoch,
                &f.commit_raw(input.clone(), &preview),
            ),
            _ => f.manager.lookup_start(
                f.host.clone(),
                f.lease.clone(),
                foreign.clone(),
                f.epoch,
                &json!({"version":1,"input":input,"author_consent":true}).to_string(),
            ),
        };
        foreign.retire(f.epoch);
        foreign.drain(f.epoch);
        results.push((kind, result));
    }
    let original_status = f
        .broker
        .status(&f.lease, f.epoch, busy["operation_id"].as_u64().unwrap())
        .unwrap();
    release.send(()).unwrap();
    f.wait(busy);
    assert_eq!(original_status["running"], true);
    for (kind, result) in results {
        assert!(
            matches!(&result, Err(error) if error == "Integrity"),
            "foreign broker {kind} must fail before admission/consumption: {result:?}"
        );
    }
    assert_eq!(f.engine(&f.parent).canonical_bytes(), before);
    f.missing(&input);
    f.missing(&f.input("foreign-broker-prepare"));
    // A foreign attempt must not consume a valid preview, unlike a genuine
    // second-consent attempt refused by the designated broker's Busy state.
    assert_eq!(
        f.result(f.commit_start(&f.commit_raw(input, &preview)).unwrap())["outcome"]["created"],
        true
    );
}
