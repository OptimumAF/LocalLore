// Scripted roles prove plumbing/current policy, not model quality or device behavior.
// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
use locallore::{
    author_correction::{AuthorCorrectionInputV1, AuthorCorrectionOperationV1},
    context_compiler::ContextPolicy,
    contracts::*,
    engine::Engine,
    host::Host,
    inference::{Cancellation, GenerationRequest, InferenceProvider, Input},
    play::PlayProfile,
};
use locallore_storage::{validate_archive, ForkRequest, Store, TurnPhase};
use serde_json::{json, Value};
use std::{
    path::{Path, PathBuf},
    sync::{
        atomic::{AtomicBool, AtomicU64, AtomicUsize, Ordering},
        Arc, Mutex,
    },
    task::Poll,
    time::{Duration, Instant},
};

const A: &str = "a plain marker stands beside the quay";
const B: &str = "a bronze marker stands beside the quay";
const C: &str = "a silver marker stands beside the quay";
const REASON: &str = "PRIVATE_IMPORTED_GENERATION_AUTHOR_REASON";
const PARENT_CANARY: &str = "IMPORTED_PARENT_FUTURE_CANARY";
const SIBLING_CANARY: &str = "IMPORTED_SIBLING_CANARY";
static NEXT: AtomicU64 = AtomicU64::new(0);

fn seed(story: &str) -> Seed {
    let actor = |name: &str, location: &str| {
        json!({"name":name,"location":location,"alive":true,
        "energy":2,"abilities":{},"attributes":{},"injuries":[],"affiliations":[],"goals":[]})
    };
    serde_json::from_value(json!({"version":1,"id":"imported-fresh-generation-v1",
        "scope":{"story":story,"branch":"main"},"profile":"fantasy_v1","player":"player",
        "locations":["quay","tower"],"routes":[],
        "actors":{"player":actor("Rowan","quay"),"mira":actor("Mira","quay"),"sable":actor("Sable","tower")},
        "items":{"potion":{"owner":"player","quantity":1,"return_to":null,"healing":true}},
        "abilities":{},"facts":{"relic-location":{"proposition":A,"discoverable_at":"quay","known_by":["player","mira"]}},
        "relationships":[{"from":"mira","to":"player","respect":0,"trust":0,"obligation":0}],
        "story_time":100,"beliefs":[],"commitments":{}})).unwrap()
}
fn apply(store: &mut Store, scope: &Scope, key: &str, commands: Vec<Command>) -> Receipt {
    let engine = store.resume(scope).unwrap().engine;
    let request = engine.request(key, Intent::Actions(commands));
    let preview = engine
        .preview(&request, &Engine::proposal(&request).unwrap())
        .unwrap();
    store.begin_turn(&request).unwrap();
    store.commit_prepared(&preview).unwrap()
}
fn authored(store: &mut Store, parent: &Scope, child: &str, old: &str, new: &str) -> Scope {
    let head = store.resume(parent).unwrap().engine.revision();
    let input = AuthorCorrectionInputV1 {
        version: 1,
        parent: parent.clone(),
        expected_parent_revision: head,
        fork_revision: head,
        child_branch: child.into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(),
            expected_proposition: old.into(),
            replacement: new.into(),
        },
        reason: REASON.into(),
    };
    let plan = store.prepare_author_correction(&input, &|| false).unwrap();
    store
        .apply_author_correction(&plan, &|| false)
        .unwrap()
        .scope
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
    assert_eq!(actual.revision(), expected.revision());
    assert_eq!(actual.domain_version(), expected.domain_version());
    assert_eq!(actual.canonical_bytes(), expected.canonical_bytes());
    assert_eq!(actual.canonical_records(), expected.canonical_records());
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
    }
}
fn observed(engine: &Engine, actor: &str) -> String {
    engine
        .observed_facts(actor, engine.scope(), engine.revision())
        .unwrap()["relic-location"]
        .proposition
        .clone()
}
struct Fixture {
    directory: PathBuf,
    source_path: PathBuf,
    target_path: PathBuf,
    root: Scope,
    c: Scope,
    control: Scope,
    before: Engine,
    source_before: Vec<(Scope, Engine)>,
    control_before: Engine,
    archive: Vec<u8>,
}
impl Fixture {
    fn imported() -> Self {
        let directory = std::env::temp_dir().join(format!(
            "locallore-imported-generation-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&directory).unwrap();
        let source_path = directory.join("source.sqlite");
        let target_path = directory.join("target.sqlite");
        let mut source = Store::open_application(&source_path).unwrap();
        let initial = seed("imported-generation");
        let root = initial.scope.clone();
        source
            .create_story("Source imported generation", initial)
            .unwrap();
        apply(
            &mut source,
            &root,
            "prefix",
            vec![Command::Wait { ticks: 1 }],
        );
        let sibling = source
            .fork_branch(
                &ForkRequest {
                    parent: root.clone(),
                    child_branch: "sibling".into(),
                    expected_parent_revision: 1,
                    at_revision: 1,
                },
                &|| false,
            )
            .unwrap()
            .scope;
        let b = authored(&mut source, &root, "private-b", A, B);
        apply(
            &mut source,
            &b,
            "observed-b-and-spent-potion",
            vec![
                Command::Discover {
                    fact: "relic-location".into(),
                },
                Command::Give {
                    item: "potion".into(),
                    to: "mira".into(),
                    quantity: 1,
                },
            ],
        );
        let c = authored(&mut source, &b, "private-c", B, C);
        for (scope, text) in [(&root, PARENT_CANARY), (&sibling, SIBLING_CANARY)] {
            let mut commands = vec![Command::Say {
                text: text.into(),
                audience: ["mira".into()].into(),
            }];
            commands.extend((0..3).map(|_| Command::Wait { ticks: 1 }));
            apply(&mut source, scope, "equal-head-canary", commands);
        }
        let source_before = vec![root.clone(), sibling, b.clone(), c.clone()]
            .into_iter()
            .map(|scope| {
                let engine = source.resume(&scope).unwrap().engine;
                (scope, engine)
            })
            .collect::<Vec<_>>();
        let before = source.resume(&c).unwrap().engine;
        assert_eq!(before.revision(), 5);
        assert_eq!(before.domain_version(), 2);
        assert_eq!(observed(&before, "player"), B);
        assert_eq!(observed(&before, "mira"), A);
        assert_eq!(
            before.effective_fact("relic-location").unwrap().proposition,
            C
        );
        assert_eq!(before.state().items["potion"].owner, "mira");
        let exported = source.export_archive(&root.story, &|| false).unwrap();
        assert_eq!(exported.preview().version, 3);
        let archive = exported.bytes().to_vec();
        let mut target = Store::open_application(&target_path).unwrap();
        let control_seed = seed("target-control");
        let control = control_seed.scope.clone();
        target
            .create_story("Foreign target control", control_seed)
            .unwrap();
        apply(
            &mut target,
            &control,
            "control-wait",
            vec![Command::Wait { ticks: 1 }],
        );
        let control_before = target.resume(&control).unwrap().engine;
        target
            .import_archive(validate_archive(&archive, &|| false).unwrap(), &|| false)
            .unwrap();
        drop(target);
        drop(source);
        equivalent(&read(&target_path, &c), &before);
        Self {
            directory,
            source_path,
            target_path,
            root,
            c,
            control,
            before,
            source_before,
            control_before,
            archive,
        }
    }
    fn host(&self) -> Host {
        locallore_workspace::open(&self.target_path, false).unwrap()
    }
    fn assert_preserved(&self) {
        for (scope, before) in &self.source_before {
            equivalent(&read(&self.source_path, scope), before);
            if scope != &self.c {
                equivalent(&read(&self.target_path, scope), before);
            }
        }
        equivalent(
            &read(&self.target_path, &self.control),
            &self.control_before,
        );
        let mut source = Store::open_read_only(&self.source_path).unwrap();
        assert_eq!(
            source
                .export_archive(&self.root.story, &|| false)
                .unwrap()
                .bytes(),
            self.archive
        );
        let bytes: u64 = std::fs::read_dir(&self.directory)
            .unwrap()
            .map(|entry| entry.unwrap().metadata().unwrap().len())
            .sum();
        assert!(
            bytes < 2 * 1024 * 1024,
            "Retained imported-generation fixture exceeded2MiB"
        );
    }
}
fn fresh_request(fixture: &Fixture, key: &str) -> Request {
    fixture.before.request(
        key,
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: "I discover relic-location.".into(),
        },
    )
}
fn profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-imported-fresh-play25".into(),
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
#[derive(Clone, Default)]
struct Probe {
    factories: Arc<AtomicUsize>,
    polls: Arc<AtomicUsize>,
    drops: Arc<AtomicUsize>,
    cancelled_polls: Arc<AtomicUsize>,
    seen: Arc<Mutex<Vec<GenerationRequest>>>,
    last_cancel: Arc<Mutex<Option<Cancellation>>>,
}
impl Probe {
    fn token_cancelled(&self) -> bool {
        self.last_cancel
            .lock()
            .unwrap()
            .as_ref()
            .is_some_and(Cancellation::is_cancelled)
    }
}
#[derive(Clone)]
enum Mode {
    DiscoverC,
    Deny,
    HeldNarrator {
        entered: std::sync::mpsc::SyncSender<()>,
        release: Arc<AtomicBool>,
    },
}
struct Script {
    probe: Probe,
    mode: Mode,
    announced: bool,
}
impl Drop for Script {
    fn drop(&mut self) {
        self.probe.drops.fetch_add(1, Ordering::SeqCst);
    }
}
impl InferenceProvider for Script {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        cancel: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        self.probe.polls.fetch_add(1, Ordering::SeqCst);
        self.probe.seen.lock().unwrap().push(request.clone());
        *self.probe.last_cancel.lock().unwrap() = Some(cancel.clone());
        let Input::Structured { role, .. } = &request.input else {
            return Poll::Ready(Err(Error::Provider));
        };
        if matches!(self.mode, Mode::Deny) {
            return Poll::Ready(Err(Error::Provider));
        }
        if let Mode::HeldNarrator { entered, release } = &self.mode {
            if role == "narrator" {
                if !self.announced {
                    let _ = entered.try_send(());
                    self.announced = true;
                }
                let start = Instant::now();
                while !release.load(Ordering::SeqCst) {
                    assert!(
                        start.elapsed() < Duration::from_secs(10),
                        "Synthetic narrator gate release deadline"
                    );
                    std::thread::sleep(Duration::from_millis(1));
                }
                if cancel.is_cancelled() {
                    self.probe.cancelled_polls.fetch_add(1, Ordering::SeqCst);
                }
                // Deliberately noncooperative fake: valid late C output is returned
                // even after cancellation. The real driver must discard it.
            }
        }
        let value = match role.as_str() {
            "director" => json!({"commands":[{"op":"discover","fact":"relic-location"}]}),
            "narrator" => json!({"text":C,"event_ids":[request.revision+1],"speaker":"narrator"}),
            _ => return Poll::Ready(Err(Error::Provider)),
        };
        Poll::Ready(Ok(serde_json::to_vec(&value).unwrap()))
    }
}
fn configure(host: &Host, probe: &Probe, mode: Mode) {
    let shared = probe.clone();
    host.configure_fixture_provider(
        profile(),
        Arc::new(move || {
            shared.factories.fetch_add(1, Ordering::SeqCst);
            Box::new(Script {
                probe: shared.clone(),
                mode: mode.clone(),
                announced: false,
            })
        }),
    )
    .unwrap();
}
fn call(host: &Host, command: Value) -> Value {
    host.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
}
fn data(reply: &Value) -> &Value {
    assert_eq!(reply["status"], "ok", "{reply}");
    &reply["data"]
}
fn resume(host: &Host, scope: &Scope) -> String {
    data(&call(host, json!({"op":"resume","scope":scope})))["session"]
        .as_str()
        .unwrap()
        .into()
}
fn control(host: &Host, session: &str, request: &Request, op: &str) -> Value {
    call(
        host,
        json!({"op":op,"session":session,"scope":request.scope,"turn":request.turn}),
    )
}

#[test]
fn imported_cold_host_generates_new_observation_from_b_to_c_only_after_explicit_commit() {
    let fixture = Fixture::imported();
    let before = fixture.before.clone();
    let host = fixture.host();
    let probe = Probe::default();
    configure(&host, &probe, Mode::DiscoverC);
    let session = resume(&host, &fixture.c);
    let request = fresh_request(&fixture, "fresh-after-import");
    assert_eq!(
        data(&call(
            &host,
            json!({"op":"free_text","session":session,"request":request})
        ))["phase"],
        "queued"
    );
    assert_eq!(
        data(&control(&host, &session, &request, "prepare"))["phase"],
        "ready"
    );
    equivalent(&read(&fixture.target_path, &fixture.c), &before);
    assert_eq!(probe.factories.load(Ordering::SeqCst), 1);
    assert_eq!(probe.polls.load(Ordering::SeqCst), 2);
    {
        let seen = probe.seen.lock().unwrap();
        assert_eq!(seen.len(), 2);
        for generated in seen.iter() {
            assert_eq!(generated.scope, fixture.c);
            assert_eq!(generated.turn, request.turn);
            assert_eq!(generated.revision, 5);
        }
        let Input::Structured {
            role,
            prompt: director,
            ..
        } = &seen[0].input
        else {
            panic!("Structured director")
        };
        assert_eq!(role, "director");
        assert!(director.contains(B));
        for excluded in [C, REASON, PARENT_CANARY, SIBLING_CANARY] {
            assert!(!director.contains(excluded), "Director leak {excluded}");
        }
        let Input::Structured {
            role,
            prompt: narrator,
            ..
        } = &seen[1].input
        else {
            panic!("Structured narrator")
        };
        assert_eq!(role, "narrator");
        assert!(narrator.contains(C));
        for excluded in [A, B, REASON, PARENT_CANARY, SIBLING_CANARY] {
            assert!(!narrator.contains(excluded), "Narrator leak {excluded}");
        }
    }
    let committed = control(&host, &session, &request, "commit");
    assert_eq!(data(&committed)["phase"], "committed");
    let after = read(&fixture.target_path, &fixture.c);
    assert_eq!(after.revision(), 6);
    assert_eq!(observed(&after, "player"), C);
    assert_eq!(observed(&after, "mira"), A);
    assert!(!after
        .observed_facts("sable", &fixture.c, after.revision())
        .unwrap()
        .contains_key("relic-location"));
    assert_eq!(after.state().items["potion"].owner, "mira");
    assert_eq!(after.state().item_transfers["potion"].sequence, 4);
    assert_eq!(after.state().relationships[0].obligation, 1);
    let mut target = Store::open_read_only(&fixture.target_path).unwrap();
    let stored = target.lookup_turn(&fixture.c, &request.turn).unwrap();
    assert_eq!(stored.phase, TurnPhase::Committed);
    let receipt = stored.receipt.unwrap();
    let play = receipt.play().unwrap();
    assert_eq!(play.prompt_version, "locallore-play-v2.5");
    assert_eq!(play.policy, "grounded-prose-v2.5-whole-evidence-words-v1");
    assert_eq!(
        play.context_policy,
        Some(ContextPolicy::StateRelevantMemoryV1)
    );
    assert_eq!(play.context.as_ref().unwrap().head, 5);
    assert_eq!(play.context.as_ref().unwrap().scope, fixture.c);
    assert!(!play.fallback);
    assert_eq!(play.repairs, 0);
    assert_eq!(play.narration.event_ids, vec![6]);
    assert_eq!(
        data(&committed)["receipt"],
        serde_json::to_value(&receipt).unwrap()
    );
    drop(target);
    drop(host);
    assert_eq!(probe.drops.load(Ordering::SeqCst), 1);
    fixture.assert_preserved();

    // This is the retry of the NEW imported-side generation, not a retry of a
    // generation that happened on source before export (already covered elsewhere).
    let reopened = fixture.host();
    let denying = Probe::default();
    configure(&reopened, &denying, Mode::Deny);
    let session = resume(&reopened, &fixture.c);
    assert_eq!(
        call(
            &reopened,
            json!({"op":"free_text","session":session,"request":request})
        ),
        committed
    );
    for op in ["prepare", "commit", "turn_status", "cancel"] {
        assert_eq!(control(&reopened, &session, &request, op), committed);
    }
    assert_eq!(denying.factories.load(Ordering::SeqCst), 0);
    assert_eq!(denying.polls.load(Ordering::SeqCst), 0);
    assert_eq!(denying.drops.load(Ordering::SeqCst), 0);
    assert!(denying.seen.lock().unwrap().is_empty());
    reopened.disable_local_provider();
    assert_eq!(
        call(
            &reopened,
            json!({"op":"free_text","session":session,"request":request})
        ),
        committed
    );
    equivalent(&read(&fixture.target_path, &fixture.c), &after);
    fixture.assert_preserved();
    drop(reopened);
}

// Cancel an imported-side turn while its validated candidate reaches narration.
struct HeldImportedNarrator {
    release: Arc<AtomicBool>,
    entered: std::sync::mpsc::Receiver<()>,
    finished: std::sync::mpsc::Receiver<Value>,
    worker: Option<std::thread::JoinHandle<()>>,
}
impl HeldImportedNarrator {
    fn start(host: Arc<Host>, probe: &Probe, session: &str, request: &Request) -> Self {
        let release = Arc::new(AtomicBool::new(false));
        let (entered_sender, entered) = std::sync::mpsc::sync_channel(1);
        let (finished_sender, finished) = std::sync::mpsc::sync_channel(1);
        configure(
            &host,
            probe,
            Mode::HeldNarrator {
                entered: entered_sender,
                release: release.clone(),
            },
        );
        let submitted = call(
            &host,
            json!({"op":"free_text","session":session,"request":request}),
        );
        assert_eq!(data(&submitted)["phase"], "queued");
        let session = session.to_owned();
        let request = request.clone();
        let worker = std::thread::spawn(move || {
            let reply = control(&host, &session, &request, "prepare");
            let _ = finished_sender.send(reply);
        });
        Self {
            release,
            entered,
            finished,
            worker: Some(worker),
        }
    }
    fn finish(mut self) -> Value {
        self.release.store(true, Ordering::SeqCst);
        let reply = self
            .finished
            .recv_timeout(std::time::Duration::from_secs(5))
            .expect("owned scripted prepare must finish after release");
        self.worker
            .take()
            .unwrap()
            .join()
            .expect("owned scripted prepare thread must join");
        reply
    }
}
impl Drop for HeldImportedNarrator {
    fn drop(&mut self) {
        self.release.store(true, Ordering::SeqCst);
        if let Some(worker) = self.worker.take() {
            let _ = worker.join();
        }
    }
}

#[test]
fn imported_cold_host_cancel_discards_late_valid_narration_and_never_regenerates_terminal_turn() {
    let fixture = Fixture::imported();
    let before = fixture.before.clone();
    equivalent(&read(&fixture.target_path, &fixture.c), &before);
    assert_eq!(observed(&before, "player"), B);
    assert_eq!(observed(&before, "mira"), A);
    assert_eq!(
        before.effective_fact("relic-location").unwrap().proposition,
        C
    );
    let host = Arc::new(fixture.host()); // Target Store was imported and closed first.
    let session = resume(&host, &fixture.c);
    let request = fresh_request(&fixture, "fresh-import-cancel-at-narrator");
    assert_eq!(request.expected_revision, before.revision());
    let probe = Probe::default();
    let held = HeldImportedNarrator::start(host.clone(), &probe, &session, &request);
    let entered = held.entered.recv_timeout(std::time::Duration::from_secs(5));
    // Do not assert before settling the owned thread: even a failed handshake
    // must release/join and preserve its draft evidence rather than strand it.
    let pending_counts = entered.as_ref().ok().map(|_| host.live_counts());
    let cancelled = if entered.is_ok() {
        control(&host, &session, &request, "cancel")
    } else {
        Value::Null
    };
    let cancelled_token = probe.token_cancelled();
    let late_prepare = held.finish();
    assert!(
        entered.is_ok(),
        "actual validated candidate must reach held narrator"
    );
    assert_eq!(pending_counts, Some((1, 1)));
    assert_eq!(data(&cancelled)["phase"], "cancelled");
    assert!(data(&cancelled)["receipt"].is_null());
    assert_eq!(late_prepare, cancelled);
    assert!(cancelled_token);
    assert!(probe.token_cancelled());
    assert_eq!(probe.factories.load(Ordering::SeqCst), 1);
    assert_eq!(probe.polls.load(Ordering::SeqCst), 2);
    assert_eq!(probe.cancelled_polls.load(Ordering::SeqCst), 1);
    assert_eq!(probe.drops.load(Ordering::SeqCst), 1);
    assert_eq!(host.live_counts(), (1, 0));
    {
        let seen = probe.seen.lock().unwrap();
        assert_eq!(seen.len(), 2);
        for generated in seen.iter() {
            assert_eq!(generated.scope, fixture.c);
            assert_eq!(generated.turn, request.turn);
            assert_eq!(generated.revision, before.revision());
        }
        let Input::Structured {
            role,
            prompt: director,
            ..
        } = &seen[0].input
        else {
            panic!("structured director required")
        };
        assert_eq!(role, "director");
        assert!(director.contains(B));
        for excluded in [C, REASON, PARENT_CANARY, SIBLING_CANARY] {
            assert!(
                !director.contains(excluded),
                "director must not receive {excluded}"
            );
        }
        let Input::Structured {
            role,
            prompt: narrator,
            ..
        } = &seen[1].input
        else {
            panic!("structured narrator required")
        };
        assert_eq!(role, "narrator");
        assert!(narrator.contains(C));
        for excluded in [A, B, REASON, PARENT_CANARY, SIBLING_CANARY] {
            assert!(
                !narrator.contains(excluded),
                "staged narrator must not receive {excluded}"
            );
        }
    }
    equivalent(&read(&fixture.target_path, &fixture.c), &before);
    assert_eq!(
        observed(&read(&fixture.target_path, &fixture.c), "player"),
        B
    );
    assert_eq!(observed(&read(&fixture.target_path, &fixture.c), "mira"), A);
    {
        let mut target = Store::open_read_only(&fixture.target_path).unwrap();
        let stored = target.lookup_turn(&fixture.c, &request.turn).unwrap();
        assert_eq!(stored.request, request);
        assert_eq!(stored.phase, TurnPhase::Cancelled);
        assert!(stored.receipt.is_none());
    }
    // Even though the fake returned valid C after seeing cancellation, the
    // actual driver/Host must keep the imported B canon and terminal key.
    for op in ["turn_status", "prepare", "commit", "cancel"] {
        assert_eq!(control(&host, &session, &request, op), cancelled);
    }
    assert_eq!(
        call(
            &host,
            json!({"op":"free_text","session":session,"request":request})
        ),
        cancelled
    );
    assert_eq!(probe.factories.load(Ordering::SeqCst), 1);
    assert_eq!(probe.polls.load(Ordering::SeqCst), 2);
    assert_eq!(probe.drops.load(Ordering::SeqCst), 1);
    equivalent(&read(&fixture.target_path, &fixture.c), &before);
    fixture.assert_preserved();
    host.close_all();
    assert_eq!(host.live_counts(), (0, 0));
    drop(host);

    // Cold Host/Repository/SQLite reopen, with a trap factory configured but
    // never instantiated. This retries THIS imported-side cancelled request.
    let reopened = fixture.host();
    let denying = Probe::default();
    configure(&reopened, &denying, Mode::Deny);
    let session = resume(&reopened, &fixture.c);
    assert_eq!(
        call(
            &reopened,
            json!({"op":"free_text","session":session,"request":request})
        ),
        cancelled
    );
    for op in ["prepare", "commit", "turn_status", "cancel"] {
        assert_eq!(control(&reopened, &session, &request, op), cancelled);
    }
    reopened.disable_local_provider();
    assert_eq!(
        call(
            &reopened,
            json!({"op":"free_text","session":session,"request":request})
        ),
        cancelled
    );
    assert_eq!(denying.factories.load(Ordering::SeqCst), 0);
    assert_eq!(denying.polls.load(Ordering::SeqCst), 0);
    assert_eq!(denying.drops.load(Ordering::SeqCst), 0);
    assert!(denying.seen.lock().unwrap().is_empty());
    equivalent(&read(&fixture.target_path, &fixture.c), &before);
    assert_eq!(
        observed(&read(&fixture.target_path, &fixture.c), "player"),
        B
    );
    fixture.assert_preserved();
    reopened.close_all();
    assert_eq!(reopened.live_counts(), (0, 0));
    drop(reopened);
    // Bounded scripted poll/release and owned Rust-thread completion only.
    // No real inference adapter, native backend drainage or hardware claim.
}
