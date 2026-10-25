// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen before native Archive3 advertisement. UNCOMPILED/UNRUN at freeze.
//! Register ONLY as archive.rs child: #[cfg(test)] #[path="archive_v3_tests.rs"] mod archive_v3_tests;
//! Windows-only native filesystem/broker tests, not IPC/WebView/model/device evidence.
//! Root command: cargo test --locked --offline -p locallore-desktop-spike --bin locallore-desktop-spike archive::archive_v3_tests:: -- --nocapture --test-threads=1
//! Current catalog2 is an expected source-level failure; this is not measured RED.
//! Existing production/test hooks only. Unique synthetic TEMP directories retained
//! locally for inspection; never read default saves or alter Android open support.
#![cfg(windows)]

#[path = "archive_continuation_tests.rs"]
mod continuation_tests;

use super::*;
use locallore::{
    author_correction::{AuthorCorrectionInputV1, AuthorCorrectionOperationV1, CanonicalRecord},
    contracts::{Command, Intent, Receipt, Scope, Seed},
    engine::Engine,
};
use locallore_storage::{ForkRequest, StorageError, TurnError};
use std::cell::Cell;

const A: &str = "SYNTHETIC_OBSERVED_A";
const B: &str = "SYNTHETIC_AUTHOR_WORLD_B";
const REASON: &str = "SYNTHETIC_PRIVATE_AUTHOR_REASON";

struct Harness {
    root: PathBuf,
    broker: Arc<ArchiveBroker>,
    lease: Arc<WindowLease>,
    epoch: u64,
    last: Cell<Option<u64>>,
}
impl Harness {
    fn new() -> Self {
        let root =
            std::env::temp_dir().join(format!("locallore-native-archive3-{}", id().unwrap()));
        fs::create_dir(&root).unwrap();
        let broker = Arc::new(ArchiveBroker::default());
        let lease = Arc::new(WindowLease::default());
        let epoch = lease.begin().unwrap();
        eprintln!("native Archive3 synthetic fixture: {}", root.display());
        Self {
            root,
            broker,
            lease,
            epoch,
            last: Cell::new(None),
        }
    }
    fn start(&self, work: impl FnOnce(&Work) -> Result<Value> + Send + 'static) -> u64 {
        let operation = self
            .broker
            .start(self.lease.clone(), self.epoch, work)
            .unwrap()["operation_id"]
            .as_u64()
            .unwrap();
        self.last.set(Some(operation));
        operation
    }
    fn wait(&self, operation: u64, phase: Option<&str>) -> Value {
        let deadline = Instant::now() + Duration::from_secs(30);
        loop {
            let status = self
                .broker
                .status(&self.lease, self.epoch, operation)
                .unwrap();
            if phase.is_some_and(|expected| status["phase"] == expected)
                || (phase.is_none() && status["running"] == false)
            {
                return status;
            }
            assert_ne!(
                status["running"], false,
                "job ended before requested phase: {status}"
            );
            assert!(
                Instant::now() < deadline,
                "bounded native Archive3 wait: {status}"
            );
            std::thread::sleep(Duration::from_millis(5));
        }
    }
    fn run(&self, work: impl FnOnce(&Work) -> Result<Value> + Send + 'static) -> Value {
        self.wait(self.start(work), None)
    }
    fn preview(&self, input: &Path) -> Value {
        let input = input.to_path_buf();
        let status = self.run(move |work| preview_input(work, Some(input)));
        assert!(status["error"].is_null(), "{status}");
        assert_eq!(status["result"]["kind"], "import");
        assert!(valid_id(status["result"]["token"].as_str().unwrap()));
        status["result"].clone()
    }
    fn apply(&self, preview: &Value, target: &Path) -> Value {
        let token = preview["token"].as_str().unwrap().to_owned();
        let target = target.to_path_buf();
        self.run(move |work| import(work, &token, &target))
    }
    fn clean_staging(&self) {
        assert_eq!(
            fs::read_dir(self.root.join("archive-staging-v1"))
                .unwrap()
                .count(),
            0
        );
    }
}
impl Drop for Harness {
    fn drop(&mut self) {
        // Stop an existing held fixture worker even if a test assertion panics.
        // Cancellation uses the actual broker API, not an invented job owner.
        if let Some(operation) = self.last.get() {
            let _ = self.broker.cancel(&self.lease, self.epoch, operation);
        }
        self.broker.hold.store(false, Ordering::SeqCst);
        self.broker.drain(self.epoch);
        if let Some(closed) = self.lease.invalidate(&format!("main-{}", self.epoch)) {
            self.lease.finish_close(closed, || {});
        }
    }
}

fn seed(story: &str) -> Seed {
    let actor = |name: &str, location: &str| {
        json!({"name":name,"location":location,
        "alive":true,"energy":2,"abilities":{},"attributes":{},"injuries":[],"affiliations":[],"goals":[]})
    };
    serde_json::from_value(json!({"version":1,"id":"native-archive3-v1",
        "scope":{"story":story,"branch":"main"},"profile":"fantasy_v1","player":"player",
        "locations":["quay","tower"],"routes":[],
        "actors":{"player":actor("Rowan","quay"),"mira":actor("Mira","quay"),"sable":actor("Sable","tower")},
        "items":{},"abilities":{},"facts":{"relic-location":{"proposition":A,"discoverable_at":"quay","known_by":["mira"]}},
        "relationships":[],"story_time":100,"beliefs":[],"commitments":{}})).unwrap()
}
fn apply(store: &mut Store, scope: &Scope, turn: &str, command: Command) -> Receipt {
    let engine = store.resume(scope).unwrap().engine;
    let request = engine.request(turn, Intent::Actions(vec![command]));
    let approved = engine
        .preview(&request, &Engine::proposal(&request).unwrap())
        .unwrap();
    store.begin_turn(&request).unwrap();
    store.commit_prepared(&approved).unwrap()
}
fn read(path: &Path, scope: &Scope) -> Engine {
    Store::open_read_only(path)
        .unwrap()
        .resume(scope)
        .unwrap()
        .engine
}
fn equivalent(actual: &Engine, expected: &Engine) {
    assert_eq!(actual.seed(), expected.seed());
    assert_eq!(actual.scope(), expected.scope());
    assert_eq!(actual.domain_version(), expected.domain_version());
    assert_eq!(actual.revision(), expected.revision());
    assert_eq!(actual.canonical_records(), expected.canonical_records());
    assert_eq!(actual.canonical_bytes(), expected.canonical_bytes());
    assert_eq!(
        actual.accepted_history_basis().unwrap(),
        expected.accepted_history_basis().unwrap()
    );
    for actor in ["player", "mira", "sable"] {
        assert_eq!(
            actual
                .character_context_v2(actor, actual.scope(), actual.revision())
                .unwrap(),
            expected
                .character_context_v2(actor, expected.scope(), expected.revision())
                .unwrap()
        );
        assert_eq!(
            actual
                .actor_receipts_v2(actor, actual.scope(), actual.revision())
                .unwrap(),
            expected
                .actor_receipts_v2(actor, expected.scope(), expected.revision())
                .unwrap()
        );
    }
}
fn privacy(engine: &Engine, root: &Scope, corrected: &Scope) {
    let scope = engine.scope();
    let head = engine.revision();
    assert_eq!(engine.domain_version(), 2);
    assert_eq!(
        engine.effective_fact("relic-location").unwrap().proposition,
        B
    );
    assert_eq!(
        engine.observed_facts("player", scope, head).unwrap()["relic-location"].proposition,
        B
    );
    assert_eq!(
        engine.observed_facts("mira", scope, head).unwrap()["relic-location"].proposition,
        A
    );
    assert!(!engine
        .observed_facts("sable", scope, head)
        .unwrap()
        .contains_key("relic-location"));
    let npc =
        serde_json::to_string(&engine.character_context_v2("mira", scope, head).unwrap()).unwrap();
    assert!(npc.contains(A));
    assert!(!npc.contains(B));
    assert!(!npc.contains(REASON));
    let views = engine.actor_receipts_v2("player", scope, head).unwrap();
    let old = views
        .iter()
        .find(|view| view.turn == "observe-before-author")
        .unwrap();
    assert_eq!(&old.original_scope, root);
    assert_eq!(old.events[0].event.scope(), root);
    assert_eq!(old.events[0].discovery.as_ref().unwrap().proposition, A);
    let new = views
        .iter()
        .find(|view| view.turn == "discover-corrected")
        .unwrap();
    assert_eq!(&new.original_scope, corrected);
    assert_eq!(new.events[0].event.scope(), corrected);
    assert_eq!(new.events[0].event.sequence(), 3);
    assert_eq!(new.events[0].discovery.as_ref().unwrap().proposition, B);
    assert!(new.events[0].event.witnesses().contains("player"));
    assert!(!new.events[0].event.witnesses().contains("mira"));
    assert!(!new.events[0].event.witnesses().contains("sable"));
}
struct Fixture {
    path: PathBuf,
    input: PathBuf,
    bytes: Vec<u8>,
    root: Scope,
    corrected: Scope,
    active: Scope,
    root_engine: Engine,
    active_engine: Engine,
    retired: bool,
}
impl Fixture {
    fn new(harness: &Harness, retired: bool) -> Self {
        let path = harness.root.join("source.sqlite");
        let input = harness.root.join("shared-source.json");
        let mut store = Store::open_application(&path).unwrap();
        let seed = seed("native-archive3");
        let root = seed.scope.clone();
        store
            .create_story("Synthetic mixed native archive", seed)
            .unwrap();
        apply(
            &mut store,
            &root,
            "observe-before-author",
            Command::Discover {
                fact: "relic-location".into(),
            },
        );
        let author = AuthorCorrectionInputV1 {
            version: 1,
            parent: root.clone(),
            expected_parent_revision: 1,
            fork_revision: 1,
            child_branch: "corrected".into(),
            reason: REASON.into(),
            operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
                fact: "relic-location".into(),
                expected_proposition: A.into(),
                replacement: B.into(),
            },
        };
        let prepared = store.prepare_author_correction(&author, &|| false).unwrap();
        let outcome = store.apply_author_correction(&prepared, &|| false).unwrap();
        assert!(outcome.created);
        let corrected = outcome.scope;
        let receipt = apply(
            &mut store,
            &corrected,
            "discover-corrected",
            Command::Discover {
                fact: "relic-location".into(),
            },
        );
        assert_eq!(receipt.events().len(), 1);
        let active = if retired {
            let live = store
                .fork_branch(
                    &ForkRequest {
                        parent: corrected.clone(),
                        child_branch: "live-child".into(),
                        expected_parent_revision: 3,
                        at_revision: 3,
                    },
                    &|| false,
                )
                .unwrap()
                .scope;
            let plan = store
                .prepare_branch_deletion(&corrected, 3, &|| false)
                .unwrap();
            store.delete_branch(plan, &|| false).unwrap();
            assert!(matches!(
                store.resume(&corrected),
                Err(TurnError::Storage(StorageError::NotFound))
            ));
            live
        } else {
            corrected.clone()
        };
        let root_engine = store.resume(&root).unwrap().engine;
        let active_engine = store.resume(&active).unwrap().engine;
        assert_eq!(root_engine.domain_version(), 1);
        assert_eq!(root_engine.revision(), 1);
        assert_eq!(active_engine.canonical_record_count(), 3);
        assert!(active_engine
            .canonical_records()
            .iter()
            .any(|record| matches!(record, CanonicalRecord::AuthorV1(_))));
        privacy(&active_engine, &root, &corrected);
        let archive = store.export_archive(&root.story, &|| false).unwrap();
        assert_eq!(archive.preview().version, 3);
        assert_eq!(archive.preview().committed_turns, 3);
        let bytes = archive.bytes().to_vec();
        assert!(bytes.len() < 128 * 1024);
        drop(store);
        fs::write(&input, &bytes).unwrap();
        Self {
            path,
            input,
            bytes,
            root,
            corrected,
            active,
            root_engine,
            active_engine,
            retired,
        }
    }
    fn preview_shape(&self, preview: &Value) {
        assert_eq!(preview["version"], 3);
        assert_eq!(preview["story_id"], self.root.story);
        assert_eq!(preview["root_branch"], self.root.branch);
        assert_eq!(preview["branch_heads"][self.root.branch.as_str()], 1);
        assert_eq!(preview["branch_heads"][self.active.branch.as_str()], 3);
        assert_eq!(
            preview["committed_turns"], 3,
            "one parent play + one author + one child play"
        );
        assert_eq!(preview["noncommitted_workflow_transferred"], false);
        if self.retired {
            assert_eq!(
                preview["retired_branch_ids"],
                json!([self.corrected.branch])
            );
        } else {
            assert!(preview.get("retired_branch_ids").is_none());
        }
        let warning = preview["privacy_warning"].as_str().unwrap();
        for meaning in [
            "author corrections/reasons/prior truth",
            "private discovery source bindings",
            "Accepted records include play and author corrections",
        ] {
            assert!(warning.contains(meaning), "{warning}");
        }
    }
    fn preserved(&self, target: &Path, foreign: &Scope, foreign_engine: &Engine) {
        let mut store = Store::open_read_only(target).unwrap();
        equivalent(&store.resume(&self.root).unwrap().engine, &self.root_engine);
        let active = store.resume(&self.active).unwrap().engine;
        equivalent(&active, &self.active_engine);
        privacy(&active, &self.root, &self.corrected);
        equivalent(&store.resume(foreign).unwrap().engine, foreign_engine);
        assert_eq!(store.stories().unwrap().len(), 2);
        if self.retired {
            assert!(matches!(
                store.resume(&self.corrected),
                Err(TurnError::Storage(StorageError::NotFound))
            ));
        }
        assert_eq!(
            store
                .export_archive(&self.root.story, &|| false)
                .unwrap()
                .bytes(),
            self.bytes
        );
        assert_eq!(fs::read(&self.input).unwrap(), self.bytes);
    }
}
fn destination(harness: &Harness) -> (PathBuf, Scope, Engine) {
    let target = harness.root.join("target.sqlite");
    let mut store = Store::open_application(&target).unwrap();
    let seed = seed("foreign-native-control");
    let scope = seed.scope.clone();
    store
        .create_story("Unrelated retained synthetic story", seed)
        .unwrap();
    apply(
        &mut store,
        &scope,
        "keep-foreign",
        Command::Wait { ticks: 1 },
    );
    let engine = store.resume(&scope).unwrap().engine;
    drop(store);
    (target, scope, engine)
}

#[test]
fn archive3_catalog_advertises_all_three_supported_versions_without_dropping_v2() {
    let harness = Harness::new();
    let catalog = harness.broker.catalog();
    assert_eq!(catalog["archive_version"], 3);
    assert_eq!(catalog["supported_archive_versions"], json!([1, 2, 3]));
    assert_eq!(catalog["privacy"], "full_private");
    assert_eq!(catalog["caps"]["bytes"], MAX_BYTES);
}

#[test]
fn mixed_capture_publish_and_native_staging_cold_reopen_preserve_full_private_history() {
    for retired in [false, true] {
        let harness = Harness::new();
        let fixture = Fixture::new(&harness, retired);
        let (target, foreign, foreign_engine) = destination(&harness);
        let path = fixture.path.clone();
        let captured = harness.run(move |work| capture(work, &path, "native-archive3", "main", 1));
        assert!(captured["error"].is_null(), "{captured}");
        fixture.preview_shape(&captured["result"]["preview"]);
        assert_eq!(captured["result"]["kind"], "export");
        let token = captured["result"]["token"].as_str().unwrap().to_owned();
        let folder = harness.root.join("published");
        fs::create_dir(&folder).unwrap();
        let published = harness.run(move |work| publish(work, &token, Some(folder), None));
        assert!(published["error"].is_null(), "{published}");
        assert_eq!(published["result"]["status"], "exported");
        let input = PathBuf::from(published["result"]["location"].as_str().unwrap());
        assert_eq!(
            input.parent(),
            Some(harness.root.join("published").as_path())
        );
        assert_eq!(fs::read(&input).unwrap(), fixture.bytes);
        let preview = harness.preview(&input);
        fixture.preview_shape(&preview["preview"]);
        let imported = harness.apply(&preview, &target);
        assert!(imported["error"].is_null(), "{imported}");
        assert_eq!(imported["result"]["status"], "imported");
        assert_eq!(
            imported["result"]["root"],
            serde_json::to_value(&fixture.root).unwrap()
        );
        assert_eq!(imported["result"]["branches"], if retired { 3 } else { 2 });
        assert_eq!(imported["result"]["committed_turns"], 3);
        assert_eq!(imported["result"]["staging_cleanup_complete"], true);
        assert_eq!(imported["result"]["pending_workflow_resumed"], false);
        assert_eq!(imported["result"]["model_loaded"], false);
        harness.clean_staging();
        fixture.preserved(&target, &foreign, &foreign_engine);
        equivalent(&read(&fixture.path, &fixture.root), &fixture.root_engine);
        equivalent(
            &read(&fixture.path, &fixture.active),
            &fixture.active_engine,
        );
        assert_eq!(fs::read(input).unwrap(), fixture.bytes);
    }
}

#[test]
fn mixed_lost_import_ack_is_durable_and_fresh_preview_retry_conflicts_without_duplicate_records() {
    let harness = Harness::new();
    let fixture = Fixture::new(&harness, false);
    let (target, foreign, foreign_engine) = destination(&harness);
    let preview = harness.preview(&fixture.input);
    harness.broker.drop_import_ack.store(true, Ordering::SeqCst);
    let lost = harness.apply(&preview, &target);
    assert_eq!(lost["error"], "ArchiveAcknowledgementUnavailable");
    assert_eq!(lost["phase"], "error");
    assert!(lost["result"].is_null());
    harness.clean_staging();
    fixture.preserved(&target, &foreign, &foreign_engine);
    let fresh = harness.preview(&fixture.input);
    assert_ne!(fresh["token"], preview["token"]);
    let retry = harness.apply(&fresh, &target);
    assert_eq!(retry["error"], "Conflict", "{retry}");
    harness.clean_staging();
    fixture.preserved(&target, &foreign, &foreign_engine);
}

#[test]
fn mixed_preapply_cancel_after_real_staging_keeps_foreign_canon_and_fresh_preview_can_import() {
    let harness = Harness::new();
    let fixture = Fixture::new(&harness, false);
    let (target, foreign, foreign_engine) = destination(&harness);
    let preview = harness.preview(&fixture.input);
    let token = preview["token"].as_str().unwrap().to_owned();
    let output = target.clone();
    harness.broker.hold.store(true, Ordering::SeqCst);
    let operation = harness.start(move |work| import(work, &token, &output));
    let staging_done = harness.wait(operation, Some("importing"));
    assert_eq!(staging_done["running"], true);
    harness.clean_staging();
    assert_eq!(
        harness
            .broker
            .cancel(&harness.lease, harness.epoch, operation)
            .unwrap()["running"],
        true
    );
    let cancelled = harness.wait(operation, None);
    assert_eq!(cancelled["error"], "Cancelled", "{cancelled}");
    harness.broker.hold.store(false, Ordering::SeqCst);
    let mut cold = Store::open_read_only(&target).unwrap();
    equivalent(&cold.resume(&foreign).unwrap().engine, &foreign_engine);
    assert_eq!(cold.stories().unwrap().len(), 1);
    assert!(matches!(
        cold.resume(&fixture.root),
        Err(TurnError::Storage(StorageError::NotFound))
    ));
    drop(cold);
    assert_eq!(fs::read(&fixture.input).unwrap(), fixture.bytes);
    let fresh = harness.preview(&fixture.input);
    assert_ne!(fresh["token"], preview["token"]);
    let imported = harness.apply(&fresh, &target);
    assert_eq!(imported["result"]["status"], "imported", "{imported}");
    harness.clean_staging();
    fixture.preserved(&target, &foreign, &foreign_engine);
}

#[test]
fn mixed_capture_rejects_stale_selected_head_without_changing_saved_history() {
    let harness = Harness::new();
    let fixture = Fixture::new(&harness, false);
    let path = fixture.path.clone();
    let stale = harness.run(move |work| capture(work, &path, "native-archive3", "main", 0));
    assert_eq!(stale["error"], "Stale", "{stale}");
    assert!(stale["result"].is_null());
    equivalent(&read(&fixture.path, &fixture.root), &fixture.root_engine);
    equivalent(
        &read(&fixture.path, &fixture.active),
        &fixture.active_engine,
    );
    let path = fixture.path.clone();
    let fresh = harness.run(move |work| capture(work, &path, "native-archive3", "main", 1));
    assert!(fresh["error"].is_null(), "{fresh}");
    fixture.preview_shape(&fresh["result"]["preview"]);
    harness
        .broker
        .discard(
            &harness.lease,
            harness.epoch,
            fresh["result"]["token"].as_str().unwrap(),
        )
        .unwrap();
}
