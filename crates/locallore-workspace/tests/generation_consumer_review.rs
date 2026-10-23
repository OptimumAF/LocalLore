// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent public-API source-basis regressions. No model or canonical SQL writes.
use locallore::{contracts::*, engine::Engine, host::Host, inference::*, play::PlayProfile};
use locallore_storage::{playable_archive::validate_archive, Store, TurnPhase};
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
        let path = std::env::temp_dir().join(format!(
            "locallore-generation-basis-review-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&path).unwrap();
        Self(path)
    }
    fn path(&self) -> PathBuf {
        self.0.join("synthetic.sqlite")
    }
    fn store(&self) -> Store {
        Store::open_application(&self.path()).unwrap()
    }
    fn host(&self) -> Host {
        locallore_workspace::open(&self.path(), false).unwrap()
    }
}
impl Drop for Fixture {
    fn drop(&mut self) {
        std::fs::remove_dir_all(&self.0).unwrap();
    }
}
fn seed() -> Seed {
    serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap()
}
fn create_prefix(fixture: &Fixture, key: &str) -> Engine {
    let mut store = fixture.store();
    let seed = seed();
    let scope = seed.scope.clone();
    store.create_story("Synthetic basis review", seed).unwrap();
    let engine = store.resume(&scope).unwrap().engine;
    let request = engine.request(key, Intent::Actions(vec![Command::Wait { ticks: 1 }]));
    let proposal = Engine::proposal(&request).unwrap();
    let preview = engine.preview(&request, &proposal).unwrap();
    store.begin_turn(&request).unwrap();
    store
        .commit_turn(&request, &proposal, preview.narration())
        .unwrap();
    store.resume(&scope).unwrap().engine
}
fn call(host: &Host, command: Value) -> Value {
    host.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
}
fn select(host: &Host, scope: &Scope) -> String {
    let result = call(host, json!({"op":"resume","scope":scope}));
    assert_eq!(result["status"], "ok", "{result}");
    result["data"]["session"].as_str().unwrap().into()
}
fn request(engine: &Engine) -> Request {
    engine.request(
        "same-explicit-turn",
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: "I wait for one tide tick.".into(),
        },
    )
}
fn submit(host: &Host, session: &str, request: &Request) {
    let result = call(
        host,
        json!({"op":"free_text","session":session,"request":request}),
    );
    assert_eq!(result["data"]["phase"], "queued", "{result}");
}
fn operation(host: &Host, session: &str, request: &Request, operation: &str) -> Value {
    call(
        host,
        json!({"op":operation,"session":session,"scope":request.scope,"turn":request.turn}),
    )
}
fn profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-source-basis-review".into(),
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
    }
}
struct Gate {
    armed: AtomicBool,
    entered: mpsc::SyncSender<()>,
    release: Mutex<mpsc::Receiver<()>>,
}
#[derive(Clone)]
struct Script {
    calls: Arc<AtomicUsize>,
    gate: Option<Arc<Gate>>,
}
impl InferenceProvider for Script {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        _: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        self.calls.fetch_add(1, Ordering::Relaxed);
        let Input::Structured { role, .. } = &request.input else {
            panic!("structured role required")
        };
        if role == "director" {
            if let Some(gate) = &self.gate {
                if gate.armed.swap(false, Ordering::AcqRel) {
                    gate.entered.send(()).unwrap();
                    gate.release
                        .lock()
                        .unwrap()
                        .recv_timeout(Duration::from_secs(5))
                        .expect("owned test gate release");
                }
            }
        }
        let output = match role.as_str() {
            "director" => json!({"commands":[{"op":"wait","ticks":1}]}),
            "narrator" => {
                json!({"text":"Time passes.","event_ids":[request.revision+1],"speaker":"narrator"})
            }
            _ => panic!("unexpected role"),
        };
        Poll::Ready(Ok(serde_json::to_vec(&output).unwrap()))
    }
}
fn configure(host: &Host, gate: Option<Arc<Gate>>) -> Arc<AtomicUsize> {
    let calls = Arc::new(AtomicUsize::new(0));
    let script = Script {
        calls: calls.clone(),
        gate,
    };
    host.configure_fixture_provider(profile(), Arc::new(move || Box::new(script.clone())))
        .unwrap();
    calls
}
fn replace_and_redraft(target: &Fixture, original: &Engine, request: &Request) -> Engine {
    let alternate = Fixture::new();
    let replacement = create_prefix(&alternate, "different-accepted-prefix");
    assert_eq!(replacement.seed(), original.seed());
    assert_eq!(replacement.scope(), original.scope());
    assert_eq!(replacement.revision(), original.revision());
    assert_eq!(replacement.canonical_bytes(), original.canonical_bytes());
    assert_ne!(
        replacement.receipts(),
        original.receipts(),
        "matching projection is not source identity"
    );
    let archive = alternate
        .store()
        .export_archive(&original.scope().story, &|| false)
        .unwrap();
    let mut writer = target.store();
    let deletion = writer
        .prepare_story_deletion(original.scope(), original.revision(), &|| false)
        .unwrap();
    writer.delete_story(deletion, &|| false).unwrap();
    writer
        .import_archive(
            validate_archive(archive.bytes(), &|| false).unwrap(),
            &|| false,
        )
        .unwrap();
    let draft = writer.begin_turn(request).unwrap();
    assert_eq!(draft.phase, TurnPhase::Draft);
    assert_eq!(draft.request, *request);
    assert_eq!(
        writer.resume(original.scope()).unwrap().engine.receipts(),
        replacement.receipts()
    );
    replacement
}
fn assert_stale_without_mutating_replacement(
    result: &Value,
    target: &Fixture,
    replacement: &Engine,
    request: &Request,
) {
    let mut store = target.store();
    let after = store.resume(replacement.scope()).unwrap().engine;
    let draft = store.turn_status(request).unwrap();
    assert!(result["error"]=="Stale" || result["data"]["phase"]=="stale",
        "old generation basis must be refused, result={result}, actual_head={}, replacement_head={}",after.revision(),replacement.revision());
    assert_eq!(after.canonical_bytes(), replacement.canonical_bytes());
    assert_eq!(after.receipts(), replacement.receipts());
    assert_eq!(
        draft.phase,
        TurnPhase::Draft,
        "old worker must not terminalize replacement owner's new draft"
    );
    assert_eq!(draft.request, *request);
    assert!(draft.receipt.is_none());
}

#[test]
fn ready_candidate_cannot_commit_after_same_head_receipt_replacement_and_redraft() {
    let target = Fixture::new();
    let original = create_prefix(&target, "original-accepted-prefix");
    let host = target.host();
    let session = select(&host, original.scope());
    let calls = configure(&host, None);
    let request = request(&original);
    submit(&host, &session, &request);
    let ready = operation(&host, &session, &request, "prepare");
    assert_eq!(ready["data"]["phase"], "ready", "{ready}");
    assert_eq!(calls.load(Ordering::Relaxed), 2);
    let replacement = replace_and_redraft(&target, &original, &request);
    let committed = operation(&host, &session, &request, "commit");
    assert_stale_without_mutating_replacement(&committed, &target, &replacement, &request);
    assert_eq!(
        calls.load(Ordering::Relaxed),
        2,
        "source refusal cannot silently regenerate"
    );
    assert_eq!(host.live_counts().1, 0);
}

struct ReleaseOnDrop(Option<mpsc::SyncSender<()>>);
impl Drop for ReleaseOnDrop {
    fn drop(&mut self) {
        if let Some(send) = self.0.take() {
            let _ = send.try_send(());
        }
    }
}
#[test]
fn in_flight_candidate_cannot_become_ready_after_same_head_receipt_replacement_and_redraft() {
    let target = Fixture::new();
    let original = create_prefix(&target, "original-accepted-prefix");
    let host = Arc::new(target.host());
    let session = select(&host, original.scope());
    let request = request(&original);
    let (entered_send, entered_receive) = mpsc::sync_channel(1);
    let (release_send, release_receive) = mpsc::sync_channel(1);
    let gate = Arc::new(Gate {
        armed: AtomicBool::new(true),
        entered: entered_send,
        release: Mutex::new(release_receive),
    });
    let calls = configure(&host, Some(gate));
    submit(&host, &session, &request);
    std::thread::scope(|threads| {
        let worker = threads.spawn(|| operation(&host, &session, &request, "prepare"));
        let mut release = ReleaseOnDrop(Some(release_send));
        entered_receive
            .recv_timeout(Duration::from_secs(5))
            .expect("actual production director must reach held poll");
        assert_eq!(calls.load(Ordering::Relaxed), 1);
        let replacement = replace_and_redraft(&target, &original, &request);
        release.0.take().unwrap().send(()).unwrap();
        let result = worker.join().unwrap();
        assert_stale_without_mutating_replacement(&result, &target, &replacement, &request);
    });
    assert_eq!(
        host.live_counts().1,
        0,
        "source rejection must drain the admitted worker"
    );
}

#[test]
fn selected_session_cannot_adopt_replacement_source_during_fresh_submit() {
    let target = Fixture::new();
    let original = create_prefix(&target, "original-accepted-prefix");
    let host = target.host();
    let session = select(&host, original.scope());
    let calls = configure(&host, None);
    let request = request(&original);
    let replacement = replace_and_redraft(&target, &original, &request);
    let submitted = call(
        &host,
        json!({"op":"free_text","session":session,"request":request}),
    );
    assert_stale_without_mutating_replacement(&submitted, &target, &replacement, &request);
    assert_eq!(calls.load(Ordering::Relaxed), 0);
    assert_eq!(host.live_counts().1, 0);
}

#[test]
fn turn_status_cannot_launder_queued_source_basis_before_prepare() {
    let target = Fixture::new();
    let original = create_prefix(&target, "original-accepted-prefix");
    let host = target.host();
    let session = select(&host, original.scope());
    let calls = configure(&host, None);
    let request = request(&original);
    submit(&host, &session, &request);
    let replacement = replace_and_redraft(&target, &original, &request);
    let status = operation(&host, &session, &request, "turn_status");
    assert_stale_without_mutating_replacement(&status, &target, &replacement, &request);
    let prepared = operation(&host, &session, &request, "prepare");
    assert_stale_without_mutating_replacement(&prepared, &target, &replacement, &request);
    assert_eq!(calls.load(Ordering::Relaxed), 0);
    assert_eq!(host.live_counts().1, 0);
}

#[test]
fn uncached_turn_status_cannot_adopt_replacement_source_before_fresh_submit() {
    let target = Fixture::new();
    let original = create_prefix(&target, "original-accepted-prefix");
    let host = target.host();
    let session = select(&host, original.scope());
    let calls = configure(&host, None);
    let request = request(&original);
    // The selected session has no cached Turn or per-turn basis. The replacement
    // owner's draft must not become an implicit permission to adopt its history.
    let replacement = replace_and_redraft(&target, &original, &request);
    let status = operation(&host, &session, &request, "turn_status");
    assert_stale_without_mutating_replacement(&status, &target, &replacement, &request);
    let submitted = call(
        &host,
        json!({"op":"free_text","session":session,"request":request}),
    );
    assert_stale_without_mutating_replacement(&submitted, &target, &replacement, &request);
    assert_eq!(calls.load(Ordering::Relaxed), 0);
    assert_eq!(host.live_counts().1, 0);
}
