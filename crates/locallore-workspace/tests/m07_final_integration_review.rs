// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Actual Store/public archive lifecycle. A native port injects a second-owner
//! rewind precisely at bound admission; no canonical SQL or inference is used.
use locallore::{
    contracts::*,
    engine::{AcceptedHistoryBasis, Engine},
    host::{Host, Persistence, SavedTurn, WorkspaceSummary},
    inference::{Cancellation, GenerationRequest, InferenceProvider, Input},
    play::PlayProfile,
};
use locallore_storage::{playable_archive::validate_archive, Store, TurnError, TurnRecord};
use serde_json::{json, Value};
use std::{
    path::PathBuf,
    sync::{
        atomic::{AtomicBool, AtomicU64, AtomicUsize, Ordering},
        mpsc, Arc, Mutex,
    },
    task::Poll,
    time::Duration,
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
    store
        .create_story("Synthetic final M07 review", seed)
        .unwrap();
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
        self.store
            .resume(scope)
            .map(|value| value.engine)
            .map_err(error)
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
        self.store
            .begin_bound(request, basis)
            .map(saved)
            .map_err(error)
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
        self.store
            .commit_turn(request, proposal, narration)
            .map_err(error)
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
        self.store
            .lookup_turn(scope, turn)
            .map(saved)
            .map_err(error)
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
    let archive = store
        .export_archive(&prefix.scope().story, &|| false)
        .unwrap();
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
    let expected = if replaced.load(Ordering::SeqCst) {
        &prefix
    } else {
        &current
    };
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
    assert_eq!(
        result["data"]["receipt"],
        serde_json::to_value(&winner).unwrap()
    );
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
    let archive = store
        .export_archive(&prefix.scope().story, &|| false)
        .unwrap();
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
        .import_archive(
            validate_archive(archive.bytes(), &|| false).unwrap(),
            &|| false,
        )
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

struct HeldDirector {
    entered: mpsc::SyncSender<()>,
    release: Arc<Mutex<mpsc::Receiver<()>>>,
    calls: Arc<AtomicUsize>,
}
impl InferenceProvider for HeldDirector {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        _: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        self.calls.fetch_add(1, Ordering::SeqCst);
        let Input::Structured { role, .. } = &request.input else {
            panic!("actual structured production input required")
        };
        let output = if role == "director" {
            self.entered.send(()).unwrap();
            self.release
                .lock()
                .unwrap()
                .recv_timeout(Duration::from_secs(5))
                .expect("bounded owned director release");
            json!({"commands":[{"op":"wait","ticks":1}]})
        } else {
            assert_eq!(role, "narrator");
            json!({"text":"Time passes.","event_ids":[request.revision+1],"speaker":"narrator"})
        };
        Poll::Ready(Ok(serde_json::to_vec(&output).unwrap()))
    }
}
struct ReleaseOnDrop(Option<mpsc::SyncSender<()>>);
impl Drop for ReleaseOnDrop {
    fn drop(&mut self) {
        if let Some(sender) = self.0.take() {
            let _ = sender.try_send(());
        }
    }
}

#[test]
fn explicit_open_reselection_fences_held_old_work_from_same_key_new_owner() {
    let fixture = Fixture::new();
    let empty = create(&fixture);
    let mut store = fixture.store();
    let original = commit(&mut store, &empty, "original-prefix");
    let alternate = Fixture::new();
    let other_empty = create(&alternate);
    let changed = commit(&mut alternate.store(), &other_empty, "different-prefix");
    assert_eq!(original.seed(), changed.seed());
    assert_eq!(original.revision(), changed.revision());
    assert_eq!(original.canonical_bytes(), changed.canonical_bytes());
    assert_ne!(original.receipts(), changed.receipts());
    let archive = alternate
        .store()
        .export_archive(&changed.scope().story, &|| false)
        .unwrap();
    let host = Arc::new(locallore_workspace::open(&fixture.path(), false).unwrap());
    let session = select(&host, original.scope());
    let request = original.request(
        "same-key-new-incarnation",
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: "I wait for one tide tick.".into(),
        },
    );
    let (entered_send, entered_receive) = mpsc::sync_channel(1);
    let (release_send, release_receive) = mpsc::sync_channel(1);
    let release_receive = Arc::new(Mutex::new(release_receive));
    let calls = Arc::new(AtomicUsize::new(0));
    let factory_calls = calls.clone();
    host.configure_fixture_provider(
        PlayProfile {
            id: "synthetic-final-open-review".into(),
            model_sha256: "a".repeat(64),
            runtime_revision: "b".repeat(40),
            template_sha256: "c".repeat(64),
            worker_sha256: "d".repeat(64),
            profile_manifest_sha256: "e".repeat(64),
            context_tokens: 4096,
            director_tokens: 350,
            narrator_tokens: 220,
            deadline_ms: 5000,
            repair_limit: 1,
        },
        Arc::new(move || {
            Box::new(HeldDirector {
                entered: entered_send.clone(),
                release: release_receive.clone(),
                calls: factory_calls.clone(),
            })
        }),
    )
    .unwrap();
    let submitted = call(
        &host,
        json!({"op":"free_text","session":session,"request":request}),
    );
    assert_eq!(submitted["data"]["phase"], "queued", "{submitted}");
    std::thread::scope(|threads| {
        let worker = threads.spawn(|| {
            call(
                &host,
                json!({
                    "op":"prepare","session":session,"scope":request.scope,"turn":request.turn,
                }),
            )
        });
        let mut release = ReleaseOnDrop(Some(release_send));
        entered_receive
            .recv_timeout(Duration::from_secs(5))
            .expect("actual production director reached held poll");
        let deletion = store
            .prepare_story_deletion(original.scope(), original.revision(), &|| false)
            .unwrap();
        store.delete_story(deletion, &|| false).unwrap();
        store
            .import_archive(
                validate_archive(archive.bytes(), &|| false).unwrap(),
                &|| false,
            )
            .unwrap();
        store.begin_turn(&request).unwrap();
        let opened = call(
            &host,
            json!({"op":"open","session":session,"scope":changed.scope()}),
        );
        let selected = if opened["status"] == "ok" {
            session.clone()
        } else {
            assert_eq!(opened["error"], "Stale", "{opened}");
            let closed = call(
                &host,
                json!({"op":"close","session":session,"scope":changed.scope()}),
            );
            assert_eq!(closed["status"], "ok", "{closed}");
            select(&host, changed.scope())
        };
        let fresh = call(
            &host,
            json!({"op":"free_text","session":selected,"request":request}),
        );
        assert_eq!(fresh["data"]["phase"], "queued", "{fresh}");
        release.0.take().unwrap().send(()).unwrap();
        let retired = worker
            .join()
            .expect("retired work must not panic on missing/reused turn");
        assert!(
            retired["error"] == "Closed"
                || retired["error"] == "Stale"
                || retired["error"] == "Cancelled"
                || retired["data"]["phase"] == "stale"
                || retired["data"]["phase"] == "cancelled",
            "{retired}"
        );
        let status = call(
            &host,
            json!({"op":"turn_status","session":selected,"scope":request.scope,"turn":request.turn}),
        );
        assert_eq!(
            status["data"]["phase"], "queued",
            "old work overwrote new incarnation: {status}"
        );
        assert_eq!(status["data"]["receipt"], Value::Null);
        let draft = store.turn_status(&request).unwrap();
        assert_eq!(draft.phase, locallore_storage::TurnPhase::Draft);
        assert_eq!(draft.request, request);
        assert!(draft.receipt.is_none());
        let current = store.resume(changed.scope()).unwrap().engine;
        assert_eq!(current.receipts(), changed.receipts());
        assert_eq!(current.canonical_bytes(), changed.canonical_bytes());
        assert_eq!(
            calls.load(Ordering::SeqCst),
            1,
            "no new provider or narrator work"
        );
        assert_eq!(host.live_counts().1, 0);
    });
}

#[test]
#[ignore = "superseded: same-source Open is passive refresh; see M07_OPEN_REFRESH_COMPATIBILITY_REVIEW_2026-10-23.md and m07_open_refresh_compatibility"]
fn explicit_open_same_source_fences_cancelled_old_work_from_retried_draft() {
    let fixture = Fixture::new();
    let empty = create(&fixture);
    let mut store = fixture.store();
    let original = commit(&mut store, &empty, "original-prefix");
    let host = Arc::new(locallore_workspace::open(&fixture.path(), false).unwrap());
    let session = select(&host, original.scope());
    let request = original.request(
        "same-source-new-incarnation",
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: "I wait for one tide tick.".into(),
        },
    );
    let (entered_send, entered_receive) = mpsc::sync_channel(1);
    let (release_send, release_receive) = mpsc::sync_channel(1);
    let release_receive = Arc::new(Mutex::new(release_receive));
    let calls = Arc::new(AtomicUsize::new(0));
    let factory_calls = calls.clone();
    host.configure_fixture_provider(
        PlayProfile {
            id: "synthetic-same-source-open-review".into(),
            model_sha256: "a".repeat(64),
            runtime_revision: "b".repeat(40),
            template_sha256: "c".repeat(64),
            worker_sha256: "d".repeat(64),
            profile_manifest_sha256: "e".repeat(64),
            context_tokens: 4096,
            director_tokens: 350,
            narrator_tokens: 220,
            deadline_ms: 5000,
            repair_limit: 1,
        },
        Arc::new(move || {
            Box::new(HeldDirector {
                entered: entered_send.clone(),
                release: release_receive.clone(),
                calls: factory_calls.clone(),
            })
        }),
    )
    .unwrap();
    let submitted = call(
        &host,
        json!({"op":"free_text","session":session,"request":request}),
    );
    assert_eq!(submitted["data"]["phase"], "queued", "{submitted}");
    std::thread::scope(|threads| {
        let worker = threads.spawn(|| {
            call(
                &host,
                json!({
                    "op":"prepare","session":session,"scope":request.scope,"turn":request.turn,
                }),
            )
        });
        let mut release = ReleaseOnDrop(Some(release_send));
        entered_receive
            .recv_timeout(Duration::from_secs(5))
            .expect("actual director reached held poll before same-source Open");
        // No replacement, rewind or source mismatch: the old Work basis still
        // exactly matches. Incarnation, rather than history, must fence cleanup.
        let opened = call(
            &host,
            json!({"op":"open","session":session,"scope":original.scope()}),
        );
        assert_eq!(opened["status"], "ok", "{opened}");
        let fresh = call(
            &host,
            json!({"op":"free_text","session":session,"request":request}),
        );
        assert_eq!(fresh["data"]["phase"], "queued", "{fresh}");
        release.0.take().unwrap().send(()).unwrap();
        let retired = worker
            .join()
            .expect("retired same-source work must not panic");
        assert!(
            retired["error"] == "Closed"
                || retired["error"] == "Cancelled"
                || retired["error"] == "Stale"
                || retired["data"]["phase"] == "cancelled"
                || retired["data"]["phase"] == "stale",
            "{retired}"
        );
        let status = call(
            &host,
            json!({"op":"turn_status","session":session,"scope":request.scope,"turn":request.turn}),
        );
        assert_eq!(
            status["data"]["phase"], "queued",
            "old cancelled work overwrote new owner: {status}"
        );
        assert_eq!(status["data"]["receipt"], Value::Null);
        let draft = store.turn_status(&request).unwrap();
        assert_eq!(draft.phase, locallore_storage::TurnPhase::Draft);
        assert_eq!(draft.request, request);
        assert!(draft.receipt.is_none());
        let actual = store.resume(original.scope()).unwrap().engine;
        assert_eq!(actual.receipts(), original.receipts());
        assert_eq!(actual.canonical_bytes(), original.canonical_bytes());
        assert_eq!(
            calls.load(Ordering::SeqCst),
            1,
            "cancelled retired work cannot narrate or regenerate"
        );
        assert_eq!(host.live_counts().1, 0);
    });
}
