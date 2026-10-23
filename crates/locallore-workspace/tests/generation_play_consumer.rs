//! Actual SQLite -> native Host prepare -> production Play, synthetic role outputs only.
//! The final two cases explicitly use a fake persistence port to inject read errors.
use locallore::{
    contracts::*,
    engine::Engine,
    host::{Host, HostGenerationSnapshot, Persistence, SavedTurn, WorkspaceSummary},
    inference::*,
    inspection_query::{Observer, Query, View},
    memory_coverage::{CoverageRead, FallbackReason},
    play::PlayProfile,
};
use locallore_storage::{
    memory_jobs::{MemoryJobRequest, MemoryJobStatus},
    Store,
};
use serde_json::{json, Value};
use std::{
    path::PathBuf,
    sync::{Arc, Mutex},
    task::Poll,
};

struct Temp(PathBuf);
impl Temp {
    fn new() -> Self {
        let path = std::env::temp_dir().join(format!(
            "locallore-generation-consumer-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
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
}
// Bounded synthetic evidence is deliberately retained under caller-owned TEMP.
fn seed() -> Seed {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    seed.facts.insert(
        "npc-private".into(),
        Fact {
            proposition: "NPC-ONLY-SOURCE-947".into(),
            discoverable_at: None,
            known_by: ["mira".into()].into(),
        },
    );
    seed
}
fn call(host: &Host, command: Value) -> Value {
    host.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
}
fn resume(host: &Host) -> String {
    let v = call(host, json!({"op":"resume","scope":seed().scope}));
    assert_eq!(v["status"], "ok", "{v}");
    v["data"]["session"].as_str().unwrap().into()
}
fn profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-host-memory".into(),
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
#[derive(Clone)]
struct Script(Arc<Mutex<Vec<GenerationRequest>>>);
impl InferenceProvider for Script {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        _: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        self.0.lock().unwrap().push(request.clone());
        let Input::Structured { role, .. } = &request.input else {
            panic!("structured role required")
        };
        let value = match role.as_str() {
            "director" => json!({"commands":[{"op":"wait","ticks":1}]}),
            "narrator" => {
                json!({"text":"Time passes.","event_ids":[request.revision+1],"speaker":"narrator"})
            }
            _ => panic!("unexpected role"),
        };
        Poll::Ready(Ok(serde_json::to_vec(&value).unwrap()))
    }
}
fn configure(host: &Host) -> Arc<Mutex<Vec<GenerationRequest>>> {
    let calls = Arc::new(Mutex::new(Vec::new()));
    let provider = Script(calls.clone());
    host.configure_fixture_provider(profile(), Arc::new(move || Box::new(provider.clone())))
        .unwrap();
    calls
}
fn request(head: u64) -> Request {
    Request {
        version: 1,
        scope: seed().scope,
        turn: format!("memory-turn-{head}"),
        expected_revision: head,
        intent: Intent::FreeText {
            kind: PlayInputKind::Action,
            text: "I wait for one tide tick.".into(),
        },
    }
}
fn op(host: &Host, session: &str, request: &Request, op: &str) -> Value {
    call(
        host,
        json!({"op":op,"session":session,"scope":request.scope,"turn":request.turn}),
    )
}
fn submit(host: &Host, session: &str, request: &Request) {
    let v = call(
        host,
        json!({"op":"free_text","session":session,"request":request}),
    );
    assert_eq!(v["data"]["phase"], "queued", "{v}");
}
fn accepted(host: &Host, session: &str, request: &Request) -> Value {
    submit(host, session, request);
    let v = op(host, session, request, "prepare");
    assert_eq!(v["data"]["phase"], "ready", "{v}");
    let v = op(host, session, request, "commit");
    assert_eq!(v["data"]["phase"], "committed", "{v}");
    v
}
fn typed(store: &mut Store, turn: &str, commands: Vec<Command>) {
    let engine = store.resume(&seed().scope).unwrap().engine;
    let request = engine.request(turn, Intent::Actions(commands));
    let proposal = Engine::proposal(&request).unwrap();
    let narration = engine
        .preview(&request, &proposal)
        .unwrap()
        .narration()
        .to_owned();
    store.begin_turn(&request).unwrap();
    store.commit_turn(&request, &proposal, &narration).unwrap();
}
fn drain(store: &mut Store, observer: &str, head: u64) {
    let mut info = store
        .ensure_memory_job(
            &MemoryJobRequest {
                scope: seed().scope,
                observer: observer.into(),
                expected_head: head,
            },
            &|| false,
        )
        .unwrap();
    for _ in 0..32 {
        if info.status == MemoryJobStatus::Complete {
            return;
        }
        assert_eq!(info.status, MemoryJobStatus::Ready);
        let prepared = store
            .prepare_memory_job_step(&info.handle, &|| false)
            .unwrap();
        info = store.publish_memory_job_step(prepared, &|| false).unwrap();
    }
    panic!("fixed input exceeded packet ceiling")
}

#[test]
fn actual_missing_cache_uses_raw_without_admission_and_exact_receipt_survives_restart() {
    let temp = Temp::new();
    temp.store()
        .create_story("Synthetic raw consumer", seed())
        .unwrap();
    let host = locallore_workspace::open(&temp.path(), false).unwrap();
    let session = resume(&host);
    let calls = configure(&host);
    let r = request(0);
    let committed = accepted(&host, &session, &r);
    let context = &committed["data"]["receipt"]["play"]["context"];
    assert_eq!(
        committed["data"]["receipt"]["play"]["prompt_version"],
        "locallore-play-v2.4"
    );
    assert_eq!(context["observer"], "player");
    assert_eq!(context["source_fallback_reason"], "missing");
    assert_eq!(context["coverage"]["mode"], "raw");
    assert_eq!(context["coverage"]["set_fallback_reason"], "missing");
    assert_eq!(calls.lock().unwrap().len(), 2);
    assert!(matches!(
        temp.store()
            .context_snapshot(
                &MemoryJobRequest {
                    scope: seed().scope,
                    observer: "player".into(),
                    expected_head: 1
                },
                &|| false
            )
            .unwrap()
            .coverage,
        CoverageRead::RawFallback(FallbackReason::Missing)
    ));
    drop(host);
    let host = locallore_workspace::open(&temp.path(), false).unwrap();
    let session = resume(&host);
    assert_eq!(
        call(
            &host,
            json!({"op":"free_text","session":session,"request":r})
        ),
        committed
    );
    assert_eq!(op(&host, &session, &r, "prepare"), committed);
    assert_eq!(calls.lock().unwrap().len(), 2);
    assert_eq!(
        temp.store()
            .resume(&seed().scope)
            .unwrap()
            .engine
            .receipts()
            .len(),
        1
    );
}

#[test]
fn actual_player_job_reaches_production_compiler_after_npc_inspection_without_extra_knowledge() {
    let temp = Temp::new();
    let mut store = temp.store();
    store
        .create_story("Synthetic verified consumer", seed())
        .unwrap();
    // One sealed256-event packet and an eight-event tail keep recent-event
    // promotion entirely in the tail. Freeze the finite oracle before running.
    for batch in 0..33 {
        typed(
            &mut store,
            &format!("ledger-{batch}"),
            (0..8)
                .map(|slot| Command::Say {
                    text: format!("Ledger {}", batch * 8 + slot),
                    audience: ["mira".into()].into(),
                })
                .collect(),
        );
    }
    drain(&mut store, "player", 264);
    drain(&mut store, "mira", 264);
    let before = store.resume(&seed().scope).unwrap().engine;
    let host = locallore_workspace::open(&temp.path(), true).unwrap();
    let session = resume(&host);
    let calls = configure(&host);
    let page = host
        .inspection_query(
            &session,
            &Query {
                version: 1,
                scope: seed().scope,
                expected_head: 264,
                at_revision: None,
                observer: Observer::Character { id: "mira".into() },
                view: View::Knowledge,
                cursor: None,
                limit: 64,
                // Literal search selects the permitted fact before pagination;
                // the unfiltered first page is filled by earlier statement rows.
                search: "NPC-ONLY-SOURCE-947".into(),
            },
        )
        .unwrap();
    assert!(serde_json::to_string(&page)
        .unwrap()
        .contains("NPC-ONLY-SOURCE-947"));
    assert_eq!(
        store
            .resume(&seed().scope)
            .unwrap()
            .engine
            .canonical_bytes(),
        before.canonical_bytes()
    );
    let committed = accepted(&host, &session, &request(264));
    let context = &committed["data"]["receipt"]["play"]["context"];
    assert_eq!(context["observer"], "player");
    assert_eq!(context["head"], 264);
    assert_eq!(context["coverage"]["mode"], "verified");
    assert!(context["coverage"]["packets_used"].as_u64().unwrap() > 0);
    assert!(
        context["coverage"]["cached_event_candidates"]
            .as_u64()
            .unwrap()
            > 0
    );
    assert!(context["source_fallback_reason"].is_null());
    let seen = calls.lock().unwrap();
    assert_eq!(seen.len(), 2);
    assert!(seen.iter().all(|request| match &request.input {
        Input::Structured {
            role,
            prompt,
            schema,
        } => !serde_json::to_string(&json!({"role":role,"prompt":prompt,"schema":schema}),)
            .unwrap()
            .contains("NPC-ONLY-SOURCE-947"),
        _ => false,
    }));
    let after = store.resume(&seed().scope).unwrap().engine;
    assert!(after.extends_accepted_history(&before).unwrap());
    assert_eq!(after.revision(), 265);
    assert_eq!(
        after
            .character_context("mira", after.scope(), 265)
            .unwrap()
            .facts,
        before
            .character_context("mira", before.scope(), 264)
            .unwrap()
            .facts
    );
}

#[test]
fn actual_external_append_after_submit_stops_before_any_provider_role() {
    let temp = Temp::new();
    temp.store()
        .create_story("Synthetic stale consumer", seed())
        .unwrap();
    let host = locallore_workspace::open(&temp.path(), false).unwrap();
    let session = resume(&host);
    let calls = configure(&host);
    let r = request(0);
    submit(&host, &session, &r);
    typed(
        &mut temp.store(),
        "external",
        vec![Command::Wait { ticks: 1 }],
    );
    let result = op(&host, &session, &r, "prepare");
    assert_eq!(result["data"]["phase"], "stale", "{result}");
    assert!(calls.lock().unwrap().is_empty());
    assert_eq!(
        temp.store()
            .resume(&seed().scope)
            .unwrap()
            .engine
            .revision(),
        1
    );
    assert_eq!(host.live_counts().1, 0);
}

// A fake persistence port injects exact read errors; this is not SQLite evidence.
struct ErrorPort {
    actual: Engine,
    error: String,
    phase: Arc<Mutex<String>>,
    request: Arc<Mutex<Option<Request>>>,
}
impl ErrorPort {
    fn saved(&self) -> SavedTurn {
        SavedTurn {
            request: self.request.lock().unwrap().clone().unwrap(),
            phase: self.phase.lock().unwrap().clone(),
            receipt: None,
        }
    }
    fn terminal(&self, phase: &str) -> Result<SavedTurn, String> {
        *self.phase.lock().unwrap() = phase.into();
        Ok(self.saved())
    }
}
impl Persistence for ErrorPort {
    fn location(&self) -> &str {
        "synthetic-error-port"
    }
    fn list(&mut self) -> Result<Vec<WorkspaceSummary>, String> {
        Ok(Vec::new())
    }
    fn create(&mut self) -> Result<Engine, String> {
        Ok(self.actual.clone())
    }
    fn resume(&mut self, _: &Scope) -> Result<Engine, String> {
        Ok(self.actual.clone())
    }
    fn begin(&mut self, r: &Request) -> Result<SavedTurn, String> {
        *self.request.lock().unwrap() = Some(r.clone());
        Ok(self.saved())
    }
    fn generation_snapshot(
        &mut self,
        _: &Scope,
        _: u64,
        _: &str,
        _: &dyn Fn() -> bool,
    ) -> Result<HostGenerationSnapshot, String> {
        assert_ne!(
            self.error, "Panic",
            "synthetic native snapshot override panic"
        );
        Err(self.error.clone())
    }
    fn commit(&mut self, _: &Request, _: &Proposal, _: &str) -> Result<Receipt, String> {
        panic!("read failure cannot commit")
    }
    fn cancel(&mut self, _: &Request) -> Result<SavedTurn, String> {
        self.terminal("cancelled")
    }
    fn fail(&mut self, _: &Request) -> Result<SavedTurn, String> {
        self.terminal("failed")
    }
    fn stale(&mut self, _: &Request) -> Result<SavedTurn, String> {
        self.terminal("stale")
    }
    fn status(&mut self, _: &Scope, _: &str) -> Result<SavedTurn, String> {
        Ok(self.saved())
    }
}
#[test]
fn native_snapshot_override_panic_returns_internal_without_poisoning_host_owner() {
    let (host, session, _) = error_host("Panic");
    let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        host.generation_snapshot(&session, &seed().scope, 0, &|| false)
    }));
    assert!(
        result.is_ok(),
        "native override panic escaped through the owner lock"
    );
    assert!(matches!(result.unwrap(), Err(error) if error == "Internal"));
    assert_eq!(host.live_counts(), (1, 0));
    assert_eq!(
        call(
            &host,
            json!({"op":"snapshot","session":session,"scope":seed().scope,"observer":"player"})
        )["status"],
        "ok"
    );
}
fn error_host(error: &str) -> (Host, String, Arc<Mutex<String>>) {
    let phase = Arc::new(Mutex::new("draft".into()));
    let host = Host::with_persistence(
        false,
        Box::new(ErrorPort {
            actual: Engine::new(seed()).unwrap(),
            error: error.into(),
            phase: phase.clone(),
            request: Arc::new(Mutex::new(None)),
        }),
    );
    let reply = call(&host, json!({"op":"create","seed":"lantern-quay-v1"}));
    assert_eq!(reply["status"], "ok", "{reply}");
    let session = reply["data"]["session"].as_str().unwrap().into();
    (host, session, phase)
}
#[test]
fn injected_transient_snapshot_errors_keep_original_key_queued_without_roles_or_terminal_writes() {
    for error in ["Busy", "Full", "Database", "Unsupported", "Internal"] {
        let (host, session, phase) = error_host(error);
        let calls = configure(&host);
        let r = request(0);
        submit(&host, &session, &r);
        for _ in 0..2 {
            assert_eq!(op(&host, &session, &r, "prepare")["error"], error);
            assert_eq!(
                op(&host, &session, &r, "turn_status")["data"]["phase"],
                "queued"
            );
            assert_eq!(*phase.lock().unwrap(), "draft");
            assert!(calls.lock().unwrap().is_empty());
            assert_eq!(host.live_counts().1, 0);
        }
    }
}
#[test]
fn injected_terminal_snapshot_errors_reconcile_stale_cancelled_and_strict_canon_failure_without_roles(
) {
    for (error, expected) in [
        ("Stale", "stale"),
        ("Cancelled", "cancelled"),
        ("Integrity", "failed"),
    ] {
        let (host, session, phase) = error_host(error);
        let calls = configure(&host);
        let r = request(0);
        submit(&host, &session, &r);
        let result = op(&host, &session, &r, "prepare");
        assert_eq!(result["data"]["phase"], expected, "{result}");
        assert_eq!(*phase.lock().unwrap(), expected);
        assert!(calls.lock().unwrap().is_empty());
        assert_eq!(host.live_counts().1, 0);
    }
}
