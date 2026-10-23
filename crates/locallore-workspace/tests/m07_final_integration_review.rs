// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Actual Store/public archive lifecycle. A native port injects a second-owner
//! rewind precisely at bound admission; no canonical SQL or inference is used.
use locallore::{
    contracts::*,
    engine::{AcceptedHistoryBasis, Engine},
    host::{Host, Persistence, SavedTurn, WorkspaceSummary},
};
use locallore_storage::{playable_archive::validate_archive, Store, TurnError, TurnRecord};
use serde_json::{json, Value};
use std::{
    path::PathBuf,
    sync::{
        atomic::{AtomicBool, AtomicU64, Ordering},
        Arc,
    },
};

static NEXT: AtomicU64 = AtomicU64::new(0);
struct Fixture(PathBuf);
impl Fixture {
    fn new() -> Self {
        let root = std::env::temp_dir().join(format!(
            "locallore-final-m07-review-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&root).unwrap();
        Self(root)
    }
    fn path(&self) -> PathBuf {
        self.0.join("synthetic.sqlite")
    }
    fn store(&self) -> Store {
        Store::open_application(&self.path()).unwrap()
    }
}
impl Drop for Fixture {
    fn drop(&mut self) {
        std::fs::remove_dir_all(&self.0).unwrap();
    }
}
fn create(fixture: &Fixture) -> Engine {
    let seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    let scope = seed.scope.clone();
    let mut store = fixture.store();
    store.create_story("Synthetic final M07 review", seed).unwrap();
    store.resume(&scope).unwrap().engine
}
fn commit(store: &mut Store, engine: &Engine, key: &str) -> Engine {
    let request = engine.request(key, Intent::Actions(vec![Command::Wait { ticks: 1 }]));
    let proposal = Engine::proposal(&request).unwrap();
    let receipt = engine.preview(&request, &proposal).unwrap();
    store.begin_turn(&request).unwrap();
    store.commit_prepared(&receipt).unwrap();
    store.resume(engine.scope()).unwrap().engine
}
fn saved(record: TurnRecord) -> SavedTurn {
    SavedTurn {
        request: record.request,
        phase: match record.phase {
            locallore_storage::TurnPhase::Draft => "draft",
            locallore_storage::TurnPhase::Committed => "committed",
            locallore_storage::TurnPhase::Cancelled => "cancelled",
            locallore_storage::TurnPhase::Failed => "failed",
            locallore_storage::TurnPhase::Stale => "stale",
        }
        .into(),
        receipt: record.receipt,
    }
}
fn error(value: TurnError) -> String {
    format!("{value:?}")
}
struct RewindAtBegin {
    store: Store,
    replacement: Option<Vec<u8>>,
    replaced: Arc<AtomicBool>,
}
impl Persistence for RewindAtBegin {
    fn location(&self) -> &str {
        "synthetic-final-review"
    }
    fn list(&mut self) -> Result<Vec<WorkspaceSummary>, String> {
        Ok(Vec::new())
    }
    fn create(&mut self) -> Result<Engine, String> {
        Err("Unsupported".into())
    }
    fn resume(&mut self, scope: &Scope) -> Result<Engine, String> {
        self.store.resume(scope).map(|value| value.engine).map_err(error)
    }
    fn begin_bound(
        &mut self,
        request: &Request,
        basis: &AcceptedHistoryBasis,
    ) -> Result<SavedTurn, String> {
        if let Some(bytes) = self.replacement.take() {
            let current = self.store.resume(&request.scope).unwrap().engine;
            let plan = self
                .store
                .prepare_story_deletion(current.scope(), current.revision(), &|| false)
                .unwrap();
            self.store.delete_story(plan, &|| false).unwrap();
            self.store
                .import_archive(validate_archive(&bytes, &|| false).unwrap(), &|| false)
                .unwrap();
            self.replaced.store(true, Ordering::SeqCst);
        }
        self.store.begin_bound(request, basis).map(saved).map_err(error)
    }
    fn status_bound(
        &mut self,
        request: &Request,
        basis: &AcceptedHistoryBasis,
    ) -> Result<SavedTurn, String> {
        self.store
            .turn_status_bound(request, basis)
            .map(saved)
            .map_err(error)
    }
    fn begin(&mut self, request: &Request) -> Result<SavedTurn, String> {
        self.store.begin_turn(request).map(saved).map_err(error)
    }
    fn commit(
        &mut self,
        request: &Request,
        proposal: &Proposal,
        narration: &str,
    ) -> Result<Receipt, String> {
        self.store.commit_turn(request, proposal, narration).map_err(error)
    }
    fn cancel(&mut self, request: &Request) -> Result<SavedTurn, String> {
        self.store.cancel_turn(request).map(saved).map_err(error)
    }
    fn fail(&mut self, request: &Request) -> Result<SavedTurn, String> {
        self.store.fail_turn(request).map(saved).map_err(error)
    }
    fn stale(&mut self, request: &Request) -> Result<SavedTurn, String> {
        self.store.stale_turn(request).map(saved).map_err(error)
    }
    fn status(&mut self, scope: &Scope, turn: &str) -> Result<SavedTurn, String> {
        self.store.lookup_turn(scope, turn).map(saved).map_err(error)
    }
}
fn call(host: &Host, command: Value) -> Value {
    host.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
}
fn select(host: &Host, scope: &Scope) -> String {
    let reply = call(host, json!({"op":"resume","scope":scope}));
    assert_eq!(reply["status"], "ok", "{reply}");
    reply["data"]["session"].as_str().unwrap().into()
}

#[test]
fn stale_historical_new_key_cannot_admit_draft_after_a_source_rewind_at_begin() {
    let fixture = Fixture::new();
    let empty = create(&fixture);
    let mut store = fixture.store();
    let prefix = commit(&mut store, &empty, "original-prefix");
    let archive = store.export_archive(&prefix.scope().story, &|| false).unwrap();
    let current = commit(&mut store, &prefix, "selected-suffix");
    assert_eq!(prefix.revision(), 1);
    assert_eq!(current.revision(), 2);
    let request = prefix.request(
        "new-key-at-historical-head",
        Intent::Actions(vec![Command::Wait { ticks: 1 }]),
    );
    let replaced = Arc::new(AtomicBool::new(false));
    let host = Host::with_persistence(
        false,
        Box::new(RewindAtBegin {
            store,
            replacement: Some(archive.bytes().to_vec()),
            replaced: replaced.clone(),
        }),
    );
    let session = select(&host, current.scope());
    let result = call(
        &host,
        json!({"op":"submit","session":session,"request":request,"mode":"accepted"}),
    );
    assert_eq!(result["error"], "Stale", "{result}");
    // An early stale refusal before invoking the mutation port is also correct.
    // If admission was reached, it must protect the selected full prefix inside
    // the actual transaction, not leave a new draft in the rewound source.
    let mut actual = fixture.store();
    let expected = if replaced.load(Ordering::SeqCst) { &prefix } else { &current };
    let restored = actual.resume(current.scope()).unwrap().engine;
    assert_eq!(restored.receipts(), expected.receipts());
    assert_eq!(restored.canonical_bytes(), expected.canonical_bytes());
    assert!(
        matches!(actual.turn_status(&request), Err(TurnError::UnknownTurn)),
        "a stale selected owner must not create a replacement-source draft"
    );
    assert_eq!(host.live_counts(), (1, 0));
}

#[test]
fn exact_committed_historical_submit_remains_available_after_selected_head_advances() {
    let fixture = Fixture::new();
    let empty = create(&fixture);
    let mut store = fixture.store();
    let prefix = commit(&mut store, &empty, "exact-historical-winner");
    let winner = prefix.receipts()[0].clone();
    let current = commit(&mut store, &prefix, "selected-suffix");
    let host = locallore_workspace::open(&fixture.path(), false).unwrap();
    let session = select(&host, current.scope());
    let result = call(
        &host,
        json!({"op":"submit","session":session,"request":winner.request(),"mode":"accepted"}),
    );
    assert_eq!(result["data"]["phase"], "committed", "{result}");
    assert_eq!(result["data"]["receipt"], serde_json::to_value(&winner).unwrap());
    let restored = fixture.store().resume(current.scope()).unwrap().engine;
    assert_eq!(restored.receipts(), current.receipts());
    assert_eq!(restored.canonical_bytes(), current.canonical_bytes());
}

#[test]
fn uncached_exact_historical_draft_submit_is_read_only_after_independent_append() {
    let fixture = Fixture::new();
    let empty = create(&fixture);
    let mut store = fixture.store();
    let prefix = commit(&mut store, &empty, "original-prefix");
    let request = prefix.request(
        "historical-draft-retry",
        Intent::Actions(vec![Command::Wait { ticks: 1 }]),
    );
    store.begin_turn(&request).unwrap();
    let current = commit(&mut store, &prefix, "independent-selected-suffix");
    let host = locallore_workspace::open(&fixture.path(), false).unwrap();
    let session = select(&host, current.scope());
    let before = std::fs::read(fixture.path()).unwrap();
    let result = call(
        &host,
        json!({"op":"submit","session":session,"request":request,"mode":"accepted"}),
    );
    assert_eq!(result["data"]["phase"], "queued", "{result}");
    assert_eq!(result["data"]["receipt"], Value::Null);
    assert_eq!(std::fs::read(fixture.path()).unwrap(), before);
    let mut actual = fixture.store();
    let draft = actual.turn_status(&request).unwrap();
    assert_eq!(draft.phase, locallore_storage::TurnPhase::Draft);
    assert_eq!(draft.request, request);
    assert!(draft.receipt.is_none());
    let restored = actual.resume(current.scope()).unwrap().engine;
    assert_eq!(restored.receipts(), current.receipts());
    assert_eq!(restored.canonical_bytes(), current.canonical_bytes());
}

fn explicit_open_rewind_cannot_reuse_cached_committed_result(operation: &str) {
    let fixture = Fixture::new();
    let empty = create(&fixture);
    let mut store = fixture.store();
    let prefix = commit(&mut store, &empty, "original-prefix");
    let archive = store.export_archive(&prefix.scope().story, &|| false).unwrap();
    let original = commit(&mut store, &prefix, "cached-accepted-key");
    let winner = original.receipts()[1].clone();
    let host = locallore_workspace::open(&fixture.path(), false).unwrap();
    let session = select(&host, original.scope());
    let cached = call(
        &host,
        json!({"op":"submit","session":session,"request":winner.request(),"mode":"accepted"}),
    );
    assert_eq!(cached["data"]["phase"], "committed", "{cached}");
    let deletion = store
        .prepare_story_deletion(original.scope(), original.revision(), &|| false)
        .unwrap();
    store.delete_story(deletion, &|| false).unwrap();
    store
        .import_archive(validate_archive(archive.bytes(), &|| false).unwrap(), &|| false)
        .unwrap();
    store.begin_turn(winner.request()).unwrap();
    let opened = call(
        &host,
        json!({"op":"open","session":session,"scope":prefix.scope()}),
    );
    // An implementation may instead refuse incompatible Open and require a
    // fresh selected session. In that case old-session reads must fail closed.
    let selected = if opened["status"] == "ok" {
        assert_eq!(opened["data"]["revision"], prefix.revision());
        session
    } else {
        assert_eq!(opened["error"], "Stale", "{opened}");
        let old = call(
            &host,
            json!({"op":"turn_status","session":session,"scope":prefix.scope(),"turn":winner.request().turn}),
        );
        assert_eq!(old["error"], "Stale", "{old}");
        let closed = call(
            &host,
            json!({"op":"close","session":session,"scope":prefix.scope()}),
        );
        assert_eq!(closed["status"], "ok", "{closed}");
        select(&host, prefix.scope())
    };
    let response = if operation == "submit" {
        call(
            &host,
            json!({"op":"submit","session":selected,"request":winner.request(),"mode":"accepted"}),
        )
    } else {
        call(
            &host,
            json!({"op":"turn_status","session":selected,"scope":prefix.scope(),"turn":winner.request().turn}),
        )
    };
    assert_eq!(response["data"]["phase"], "queued", "{response}");
    assert_eq!(response["data"]["receipt"], Value::Null);
    let draft = store.turn_status(winner.request()).unwrap();
    assert_eq!(draft.phase, locallore_storage::TurnPhase::Draft);
    assert!(draft.receipt.is_none());
    let actual = store.resume(prefix.scope()).unwrap().engine;
    assert_eq!(actual.receipts(), prefix.receipts());
    assert_eq!(actual.canonical_bytes(), prefix.canonical_bytes());
}

#[test]
fn explicit_open_rewind_status_never_reports_an_old_cached_commit_as_current() {
    explicit_open_rewind_cannot_reuse_cached_committed_result("status");
}

#[test]
fn explicit_open_rewind_submit_never_reports_an_old_cached_commit_as_current() {
    explicit_open_rewind_cannot_reuse_cached_committed_result("submit");
}
