// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Source-only at handoff. Actual Core/Store/Host service, no Tauri window/model.
use super::*;
use locallore::{
    contracts::{Command, Intent, Proposal, Receipt, Request, Seed},
    engine::Engine,
    host::{memory_maintenance::MaintenanceAction, HostGenerationSnapshot, Persistence, SavedTurn},
    memory_coverage::CoverageRead,
};
use locallore_storage::{memory_jobs::MemoryJobRequest, Store};
use serde_json::json;
use std::{
    path::PathBuf,
    sync::{atomic::AtomicU64, Mutex},
};

static SERIAL: Mutex<()> = Mutex::new(());
static NEXT: AtomicU64 = AtomicU64::new(0);

#[test]
fn initialization_failures_are_closed_categories_and_release_the_actual_read_slot() {
    let _serial = SERIAL.lock().unwrap_or_else(|p| p.into_inner());
    for (input, expected) in [
        ("Io", "Database"),
        ("StorageUnavailable", "Database"),
        ("ForeignDatabase", "Integrity"),
        ("FutureVersion", "Unsupported"),
        ("SchemaMismatch", "Unsupported"),
        ("BackupRequired", "Unavailable"),
        ("BackupExists", "Unavailable"),
        ("Closed", "Closed"),
        ("untrusted initialization diagnostic", "Internal"),
    ] {
        assert_eq!(initialization_category(input.into()), expected);
    }
    let root = std::env::temp_dir().join(format!(
        "locallore-memory-init-review-{}-{}",
        std::process::id(),
        NEXT.fetch_add(1, Ordering::SeqCst)
    ));
    std::fs::create_dir(&root).unwrap();
    let parent = root.join("ordinary-file-not-a-directory");
    std::fs::write(&parent, b"synthetic initialization sentinel").unwrap();
    let lease = Arc::new(WindowLease::default());
    let epoch = lease.begin().unwrap();
    let workspace = WorkspaceState {
        close_gate: Default::default(),
        incarnation: "synthetic-init-review".into(),
        path: parent.join("stories-v1.sqlite"),
        lease: lease.clone(),
        host: Default::default(),
        preview_cleanup: Arc::new(Mutex::new(Value::Null)),
        author: Mutex::new(None),
    };
    let result = tauri::async_runtime::block_on(read_current(
        &workspace,
        epoch,
        "packets",
        &serde_json::to_string(&common()).unwrap(),
    ));
    assert_eq!(result, Err("Database".into()));
    assert!(workspace.ready().is_none());
    assert_eq!(
        std::fs::read(&parent).unwrap(),
        b"synthetic initialization sentinel"
    );
    drop(ReadPermit::acquire().unwrap());
    lease.invalidate(&format!("main-{epoch}")).unwrap();
    let closed = tauri::async_runtime::block_on(read_current(
        &workspace,
        epoch,
        "packets",
        &serde_json::to_string(&common()).unwrap(),
    ));
    assert_eq!(closed, Err("Closed".into()));
    lease.finish_close(epoch + 1, || {});
    drop(workspace);
    std::fs::remove_file(parent).unwrap();
    std::fs::remove_dir(root).unwrap();
}
fn common() -> Value {
    json!({"version":1,"session":"session-1","scope":{"story":"synthetic","branch":"main"},"expected_head":6,"observer":{"kind":"player"},"binding":null,"cursor":null,"limit":64})
}
fn parse(action: &str, value: &Value) -> Result<ReadRequest, String> {
    ReadRequest::parse(action, &serde_json::to_string(value).unwrap())
}
fn rejects(action: &str, value: &Value, expected: &str) {
    assert!(matches!(parse(action, value), Err(error) if error == expected));
}

#[test]
fn closed_parser_accepts_actual_actions_and_integer_identifier_edges() {
    let mut packets = common();
    packets["scope"]["story"] = json!("a".repeat(64));
    packets["session"] = json!("s".repeat(64));
    packets["expected_head"] = json!(MAX_INTEGER);
    assert!(parse("packets", &packets).is_ok());
    packets["expected_head"] = json!(0);
    assert!(parse("packets", &packets).is_ok());
    let mut entries = common();
    entries["binding"] = json!("a".repeat(64));
    entries["packet_index"] = json!(31);
    assert!(parse("entries", &entries).is_ok());
    let mut source = entries;
    source.as_object_mut().unwrap().remove("cursor");
    source.as_object_mut().unwrap().remove("limit");
    source["source"] = json!({"scope":{"story":"synthetic","branch":"ancestor"},"sequence":6});
    assert!(
        parse("source", &source).is_ok(),
        "original ancestor scope is not rewritten to child"
    );
}

#[test]
fn recursive_unique_parser_rejects_escaped_duplicate_keys_and_privilege_fields() {
    let raw = serde_json::to_string(&common()).unwrap();
    for bad in [
        raw.replacen("{", "{\"version\":1,", 1),
        raw.replacen("{", "{\"\\u0076ersion\":1,", 1),
        raw.replace(
            "\"story\":\"synthetic\"",
            "\"story\":\"synthetic\",\"\\u0073tory\":\"other\"",
        ),
        raw.replace(
            "\"kind\":\"player\"",
            "\"kind\":\"player\",\"kind\":\"omniscient\"",
        ),
        format!("{raw}{{}}"),
        "[{}]".into(),
    ] {
        assert!(ReadRequest::parse("packets", &bad).is_err());
    }
    for key in [
        "grant", "path", "sql", "provider", "policy", "prompt", "job", "action", "search",
        "consent",
    ] {
        let mut bad = common();
        bad[key] = json!(true);
        rejects("packets", &bad, "InvalidInput");
    }
    let mut bad = common();
    bad["scope"]["path"] = json!("private");
    rejects("packets", &bad, "InvalidInput");
    assert!(
        matches!(ReadRequest::parse("packets", &" ".repeat(MAX_REQUEST + 1)), Err(error) if error == "TooLarge")
    );
    assert!(matches!(ReadRequest::parse("rebuild", &raw), Err(error) if error == "InvalidInput"));
}

#[test]
fn parser_refuses_coercion_unsafe_bounds_binding_and_cursor_drift() {
    for value in [
        json!(-1),
        json!(1.5),
        json!(MAX_INTEGER + 1),
        json!("1"),
        json!(true),
    ] {
        let mut bad = common();
        bad["expected_head"] = value;
        rejects("packets", &bad, "InvalidInput");
    }
    for value in [json!(0), json!(65), json!(1.0), json!("1")] {
        let mut bad = common();
        bad["limit"] = value;
        rejects("packets", &bad, "InvalidInput");
    }
    for value in [
        "".to_owned(),
        "../story".into(),
        "模型".into(),
        "a".repeat(65),
    ] {
        let mut bad = common();
        bad["session"] = json!(value);
        rejects("packets", &bad, "InvalidInput");
    }
    for value in ["A".repeat(64), "a".repeat(63), "g".repeat(64)] {
        let mut bad = common();
        bad["binding"] = json!(value);
        rejects("packets", &bad, "InvalidInput");
    }
    let mut version = common();
    version["version"] = json!(2);
    rejects("packets", &version, "Version");
    for value in [
        "".to_owned(),
        format!("mp1:0:{}", "a".repeat(64)),
        format!("mp1:01:{}", "a".repeat(64)),
        format!("mp1:1:{}", "A".repeat(64)),
        "x".repeat(129),
    ] {
        let mut bad = common();
        bad["binding"] = json!("a".repeat(64));
        bad["cursor"] = json!(value);
        rejects("packets", &bad, "InvalidCursor");
    }
    let mut paged = common();
    paged["cursor"] = json!(format!("mp1:1:{}", "a".repeat(64)));
    rejects("packets", &paged, "InvalidCursor");
    paged["binding"] = json!("a".repeat(64));
    assert!(
        parse("packets", &paged).is_ok(),
        "digest membership remains Core authority"
    );
    let mut entries = common();
    entries["packet_index"] = json!(0);
    rejects("entries", &entries, "InvalidInput");
    entries["binding"] = json!("a".repeat(64));
    entries["packet_index"] = json!(32);
    rejects("entries", &entries, "InvalidInput");
    let mut source = common();
    source.as_object_mut().unwrap().remove("cursor");
    source.as_object_mut().unwrap().remove("limit");
    source["binding"] = json!("a".repeat(64));
    source["packet_index"] = json!(0);
    source["source"] = json!({"scope":{"story":"synthetic","branch":"main"},"sequence":1});
    for sequence in [json!(0), json!(7), json!(1.0), json!("1"), json!(true)] {
        source["source"]["sequence"] = sequence;
        rejects("source", &source, "InvalidInput");
    }
}

#[test]
fn recognized_actor_and_omniscient_requests_are_forbidden_without_host_access() {
    for value in [
        json!({"kind":"omniscient"}),
        json!({"kind":"character","id":"player"}),
        json!({"kind":"character","id":"mira"}),
    ] {
        let mut bad = common();
        bad["observer"] = value;
        rejects("packets", &bad, "Forbidden");
    }
    let mut bad = common();
    bad["observer"]["grant"] = json!(true);
    rejects("packets", &bad, "InvalidInput");
}

struct Fixture {
    root: PathBuf,
    path: PathBuf,
    store: Option<Store>,
    engine: Engine,
    host: Arc<Host>,
    session: String,
    lease: Arc<WindowLease>,
    epoch: u64,
}
impl Fixture {
    fn new(granted: bool) -> Self {
        let root = std::env::temp_dir().join(format!(
            "locallore-native-memory-read-{}-{}-{}",
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
            serde_json::from_str(include_str!("../../../../../fixtures/lantern_quay.json"))
                .unwrap();
        let scope = seed.scope.clone();
        store
            .create_story("Synthetic verified-memory inspection", seed)
            .unwrap();
        for index in 0..6 {
            let engine = store.resume(&scope).unwrap().engine;
            let request = engine.request(
                &format!("actual-wait-{index}"),
                Intent::Actions(vec![Command::Wait { ticks: 1 }]),
            );
            let plan = engine
                .preview(&request, &Engine::proposal(&request).unwrap())
                .unwrap();
            store.begin_turn(&request).unwrap();
            store.commit_prepared(&plan).unwrap();
        }
        let engine = store.resume(&scope).unwrap().engine;
        let host = Arc::new(locallore_workspace::open(&path, granted).unwrap());
        let session = Self::resume(&host, &scope);
        let lease = Arc::new(WindowLease::default());
        let epoch = lease.begin().unwrap();
        Self {
            root,
            path,
            store: Some(store),
            engine,
            host,
            session,
            lease,
            epoch,
        }
    }
    fn resume(host: &Host, scope: &Scope) -> String {
        let selected = host.call(
            &serde_json::to_vec(&json!({"version":1,"command":{"op":"resume","scope":scope}}))
                .unwrap(),
        );
        assert_eq!(selected["status"], "ok");
        selected["data"]["session"].as_str().unwrap().to_owned()
    }
    fn request(&self) -> Value {
        json!({"version":1,"session":self.session,"scope":self.engine.scope(),"expected_head":self.engine.revision(),"observer":{"kind":"player"},"binding":null,"cursor":null,"limit":64})
    }
    fn read(&self, action: &str, value: &Value) -> Result<Value, String> {
        read_owned(
            self.host.clone(),
            self.lease.clone(),
            self.epoch,
            parse(action, value)?,
            ReadPermit::acquire()?,
        )
    }
    fn job_request(&self) -> MemoryJobRequest {
        MemoryJobRequest {
            scope: self.engine.scope().clone(),
            observer: self.engine.seed().player.clone(),
            expected_head: self.engine.revision(),
        }
    }
    fn proof(&mut self) -> (Vec<u8>, Value, Vec<Vec<u8>>) {
        let request = self.job_request();
        let snapshot = self
            .store
            .as_mut()
            .unwrap()
            .context_snapshot(&request, &|| false)
            .unwrap();
        let job = self
            .store
            .as_mut()
            .unwrap()
            .lookup_memory_job(&request, &self.engine, &|| false)
            .unwrap();
        let job = job.map(|j| json!({"id":j.handle.id(),"status":format!("{:?}",j.status),"basis":j.basis_revision,"next":j.next_from,"generation":j.generation,"error":format!("{:?}",j.last_error)})).unwrap_or(Value::Null);
        let bytes = match snapshot.coverage {
            CoverageRead::Verified(proof) => {
                proof.packets().iter().map(|p| p.bytes().unwrap()).collect()
            }
            CoverageRead::RawFallback(_) => vec![],
        };
        assert!(
            snapshot.engine.accepted_history_basis().unwrap()
                == self.engine.accepted_history_basis().unwrap()
        );
        (
            serde_json::to_vec(snapshot.engine.canonical_records()).unwrap(),
            job,
            bytes,
        )
    }
    fn rebuild(&self) {
        self.host
            .memory_maintenance(
                &self.session,
                self.engine.scope(),
                self.engine.revision(),
                MaintenanceAction::Admit,
                &|| false,
            )
            .unwrap();
        let reply = self
            .host
            .memory_maintenance(
                &self.session,
                self.engine.scope(),
                self.engine.revision(),
                MaintenanceAction::Step,
                &|| false,
            )
            .unwrap();
        assert_eq!(
            serde_json::to_value(reply).unwrap()["job"]["status"],
            "complete"
        );
    }
}
impl Drop for Fixture {
    fn drop(&mut self) {
        let old = std::mem::replace(&mut self.host, Arc::new(Host::new(false)));
        old.close_all();
        drop(old);
        drop(self.store.take());
        assert_eq!(self.root.parent(), Some(std::env::temp_dir().as_path()));
        assert!(self
            .root
            .file_name()
            .unwrap()
            .to_string_lossy()
            .starts_with("locallore-native-memory-read-"));
        assert!(!std::fs::symlink_metadata(&self.root)
            .unwrap()
            .file_type()
            .is_symlink());
        std::fs::remove_dir_all(&self.root).unwrap();
    }
}

#[test]
fn actual_absent_cache_is_passive_missing_with_no_job_or_canonical_change() {
    let _serial = SERIAL.lock().unwrap_or_else(|p| p.into_inner());
    let mut f = Fixture::new(true);
    let before = f.proof();
    assert!(before.1.is_null());
    let reply = f.read("packets", &f.request()).unwrap();
    assert_eq!(reply["kind"], "memory_inspection");
    assert_eq!(reply["coverage"]["status"], "raw_fallback");
    assert_eq!(reply["coverage"]["fallback"], "missing");
    assert_eq!(reply["rows"], json!([]));
    assert_eq!(f.proof(), before);
}

#[test]
fn actual_packets_entries_and_exact_source_use_verified_store_snapshot_read_only() {
    let _serial = SERIAL.lock().unwrap_or_else(|p| p.into_inner());
    let mut f = Fixture::new(true);
    f.rebuild();
    let before = f.proof();
    assert!(!before.2.is_empty());
    let packets = f.read("packets", &f.request()).unwrap();
    assert_eq!(packets["coverage"]["status"], "verified");
    assert_eq!(packets["privacy"], "player_visible");
    assert_eq!(packets["observer"], f.engine.seed().player);
    assert_eq!(packets["head"], f.engine.revision());
    let mut entries_request = f.request();
    entries_request["binding"] = packets["binding"].clone();
    entries_request["packet_index"] = packets["rows"][0]["index"].clone();
    let entries = f.read("entries", &entries_request).unwrap();
    let original = entries["rows"]
        .as_array()
        .unwrap()
        .iter()
        .find_map(|row| {
            row["value"]
                .get("source")
                .filter(|v| v.is_object())
                .cloned()
                .or_else(|| {
                    row["value"]["source_events"]
                        .as_array()
                        .and_then(|rows| rows.first())
                        .cloned()
                })
        })
        .expect("actual verified entries carry actual source references");
    let mut source_request = entries_request;
    source_request.as_object_mut().unwrap().remove("cursor");
    source_request.as_object_mut().unwrap().remove("limit");
    source_request["source"] = original.clone();
    let source = f.read("source", &source_request).unwrap();
    assert_eq!(source["kind"], "memory_source");
    assert_eq!(source["matched"], true);
    assert_eq!(source["source"], original);
    assert_eq!(source["page"]["version"], 2);
    assert_eq!(source["page"]["privacy"], "player_visible");
    assert!(source["page"]["rows"]
        .as_array()
        .unwrap()
        .iter()
        .any(|row| row["kind"] == "event"
            && row["event"]["scope"] == original["scope"]
            && row["event"]["sequence"] == original["sequence"]));
    for reply in [packets, entries, source] {
        let bytes = serde_json::to_vec(&reply).unwrap();
        assert!(bytes.len() <= MAX_REPLY);
        let text = String::from_utf8(bytes).unwrap();
        for forbidden in [
            "seed_sha256",
            "lineage_sha256",
            "source_sha256",
            "model_path",
        ] {
            assert!(!text.contains(forbidden));
        }
    }
    assert_eq!(
        f.proof(),
        before,
        "all canonical records, passive job fields and serialized verified packet bytes unchanged"
    );
}

#[test]
fn actual_host_grant_scope_head_and_binding_refusals_preserve_source() {
    let _serial = SERIAL.lock().unwrap_or_else(|p| p.into_inner());
    let mut f = Fixture::new(false);
    let before = f.proof();
    assert!(matches!(f.read("packets", &f.request()), Err(error) if error == "Forbidden"));
    assert_eq!(f.proof(), before);
    let mut f = Fixture::new(true);
    f.rebuild();
    let before = f.proof();
    for (field, value, error) in [
        ("expected_head", json!(f.engine.revision() + 1), "Stale"),
        ("scope", json!({"story":"foreign","branch":"main"}), "Scope"),
        ("binding", json!("0".repeat(64)), "Binding"),
    ] {
        let mut request = f.request();
        request[field] = value;
        assert!(matches!(f.read("packets", &request), Err(actual) if actual == error));
    }
    assert_eq!(f.proof(), before);
}

#[test]
fn actual_author_corrected_domain_is_unsupported_without_mutating_parent_or_child() {
    use locallore::author_correction::{AuthorCorrectionInputV1, AuthorCorrectionOperationV1};
    let _serial = SERIAL.lock().unwrap_or_else(|p| p.into_inner());
    let mut f = Fixture::new(true);
    let parent = f.engine.clone();
    let input = AuthorCorrectionInputV1 {
        version: 1,
        parent: parent.scope().clone(),
        expected_parent_revision: parent.revision(),
        fork_revision: 1,
        child_branch: "corrected".into(),
        reason: "Synthetic out-of-story edit".into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(),
            expected_proposition: parent.seed().facts["relic-location"].proposition.clone(),
            replacement: "Synthetic revised proposition".into(),
        },
    };
    let store = f.store.as_mut().unwrap();
    let prepared = store.prepare_author_correction(&input, &|| false).unwrap();
    let outcome = store.apply_author_correction(&prepared, &|| false).unwrap();
    f.engine = store.resume(&outcome.scope).unwrap().engine;
    assert_eq!(f.engine.domain_version(), 2);
    let before = serde_json::to_vec(f.engine.canonical_records()).unwrap();
    let old = std::mem::replace(
        &mut f.host,
        Arc::new(locallore_workspace::open(&f.path, true).unwrap()),
    );
    old.close_all();
    drop(old);
    f.session = Fixture::resume(&f.host, f.engine.scope());
    assert!(matches!(f.read("packets", &f.request()), Err(error) if error == "Unsupported"));
    let store = f.store.as_mut().unwrap();
    let child_after = store.resume(f.engine.scope()).unwrap().engine;
    assert_eq!(
        serde_json::to_vec(child_after.canonical_records()).unwrap(),
        before
    );
    assert!(
        store
            .resume(parent.scope())
            .unwrap()
            .engine
            .accepted_history_basis()
            .unwrap()
            == parent.accepted_history_basis().unwrap()
    );
}

#[test]
fn read_slot_is_nonwaiting_and_released_after_return_or_unwind() {
    let _serial = SERIAL.lock().unwrap_or_else(|p| p.into_inner());
    let permit = ReadPermit::acquire().unwrap();
    assert!(matches!(ReadPermit::acquire(), Err(error) if error == "Busy"));
    drop(permit);
    let unwind = std::panic::catch_unwind(|| {
        let _permit = ReadPermit::acquire().unwrap();
        panic!("fixed private read-slot fixture");
    });
    assert!(unwind.is_err());
    drop(ReadPermit::acquire().unwrap());
    let f = Fixture::new(false);
    assert!(f.read("packets", &f.request()).is_err());
    drop(ReadPermit::acquire().unwrap());
}

// An actual Store snapshot is returned by a deliberately late native port while
// the current window is invalidated. It is not fabricated accepted history.
struct ClosingPort {
    store: Store,
    lease: Arc<WindowLease>,
    epoch: u64,
}
impl Persistence for ClosingPort {
    fn create(&mut self) -> Result<Engine, String> {
        Err("Unsupported".into())
    }
    fn resume(&mut self, scope: &Scope) -> Result<Engine, String> {
        self.store
            .resume(scope)
            .map(|s| s.engine)
            .map_err(|_| "Database".into())
    }
    fn generation_snapshot(
        &mut self,
        scope: &Scope,
        expected_head: u64,
        observer: &str,
        cancel: &dyn Fn() -> bool,
    ) -> Result<HostGenerationSnapshot, String> {
        let actual = self
            .store
            .context_snapshot(
                &MemoryJobRequest {
                    scope: scope.clone(),
                    observer: observer.into(),
                    expected_head,
                },
                cancel,
            )
            .map_err(|_| "Database")?;
        self.lease
            .invalidate(&format!("main-{}", self.epoch))
            .unwrap();
        Ok(HostGenerationSnapshot {
            engine: actual.engine,
            coverage: actual.coverage,
        })
    }
    fn begin(&mut self, _: &Request) -> Result<SavedTurn, String> {
        Err("Unsupported".into())
    }
    fn commit(&mut self, _: &Request, _: &Proposal, _: &str) -> Result<Receipt, String> {
        Err("Unsupported".into())
    }
    fn cancel(&mut self, _: &Request) -> Result<SavedTurn, String> {
        Err("Unsupported".into())
    }
    fn fail(&mut self, _: &Request) -> Result<SavedTurn, String> {
        Err("Unsupported".into())
    }
    fn stale(&mut self, _: &Request) -> Result<SavedTurn, String> {
        Err("Unsupported".into())
    }
    fn status(&mut self, _: &Scope, _: &str) -> Result<SavedTurn, String> {
        Err("Unsupported".into())
    }
}

#[test]
fn retired_lease_blocks_before_io_and_after_real_snapshot_returns() {
    let _serial = SERIAL.lock().unwrap_or_else(|p| p.into_inner());
    let mut f = Fixture::new(true);
    let before = f.proof();
    let host = Arc::new(Host::with_persistence(
        true,
        Box::new(ClosingPort {
            store: Store::open_application(&f.path).unwrap(),
            lease: f.lease.clone(),
            epoch: f.epoch,
        }),
    ));
    let session = Fixture::resume(&host, f.engine.scope());
    let mut input = f.request();
    input["session"] = json!(session);
    let result = read_owned(
        host.clone(),
        f.lease.clone(),
        f.epoch,
        parse("packets", &input).unwrap(),
        ReadPermit::acquire().unwrap(),
    );
    assert!(matches!(result, Err(error) if error == "Closed"));
    host.close_all();
    drop(host);
    assert!(matches!(f.read("packets", &f.request()), Err(error) if error == "Closed"));
    drop(ReadPermit::acquire().unwrap());
    assert_eq!(f.proof(), before);
    f.lease.finish_close(f.epoch + 1, || {});
}
