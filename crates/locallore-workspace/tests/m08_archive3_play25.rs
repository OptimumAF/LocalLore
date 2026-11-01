//! Frozen source only: actual Store/Repository/Host Play2.5 -> Archive3 -> cold Host.
//! Root command: cargo test --locked --offline -p locallore-workspace --test m08_archive3_play25 -- --test-threads=1
//! UNCOMPILED/UNRUN by this author. Two Structured scripted roles are plumbing,
//! not model quality, native UI/IPC, JNI, Android parity or an actual device check.
//! Source-audit correction after first freeze: use public AcceptedEvent accessors
//! and compare ArchivePreview's actual serialized values (it has no PartialEq).
use locallore::{
    author_correction::{
        AuthorCorrectionInputV1, AuthorCorrectionOperationV1, CanonicalRecord, ObservationSource,
    },
    context_compiler::ContextPolicy,
    contracts::*,
    engine::Engine,
    host::Host,
    inference::{Cancellation, GenerationRequest, InferenceProvider, Input},
    play::PlayProfile,
};
use locallore_storage::{validate_archive, Store, TurnPhase};
use serde_json::{json, Value};
use std::{
    path::PathBuf,
    sync::{
        atomic::{AtomicU64, AtomicUsize, Ordering},
        Arc, Mutex,
    },
    task::Poll,
};

const A: &str = "the tideglass was at the old quay";
const B: &str = "a golden marker stands beside the quay";
const REASON: &str = "PRIVATE_ARCHIVE3_PLAY25_AUTHOR_REASON";
static NEXT: AtomicU64 = AtomicU64::new(0);

struct Temp {
    directory: PathBuf,
    parent: PathBuf,
}
impl Temp {
    fn new() -> Self {
        let parent = std::env::temp_dir().canonicalize().unwrap();
        let directory = parent.join(format!(
            "locallore-archive3-play25-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&directory).unwrap();
        Self { directory, parent }
    }
    fn path(&self, name: &str) -> PathBuf {
        self.directory.join(name)
    }
}
impl Drop for Temp {
    fn drop(&mut self) {
        assert_eq!(self.directory.parent(), Some(self.parent.as_path()));
        assert!(self
            .directory
            .file_name()
            .unwrap()
            .to_str()
            .unwrap()
            .starts_with("locallore-archive3-play25-"));
        if let Err(error) = std::fs::remove_dir_all(&self.directory) {
            if !std::thread::panicking() {
                panic!("owned synthetic cleanup: {error}");
            }
        }
    }
}
fn seed() -> Seed {
    let actor = |name: &str, location: &str| {
        json!({"name":name,"location":location,"alive":true,"energy":2,
        "abilities":{},"attributes":{},"injuries":[],"affiliations":[],"goals":[]})
    };
    serde_json::from_value(json!({"version":1,"id":"tiny-archive3-play25-v1",
        "scope":{"story":"archive3-play25","branch":"main"},"profile":"fantasy_v1","player":"player",
        "locations":["quay","tower"],"routes":[],
        "actors":{"player":actor("Rowan","quay"),"mira":actor("Mira","quay"),"sable":actor("Sable","tower")},
        "items":{},"abilities":{},"facts":{"relic-location":{"proposition":A,"discoverable_at":"quay","known_by":["mira"]}},
        "relationships":[],"story_time":100,"beliefs":[],"commitments":{}})).unwrap()
}
fn profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-archive3-play25".into(),
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
    seen: Arc<Mutex<Vec<GenerationRequest>>>,
}
struct Script {
    probe: Probe,
    deny: bool,
}
impl InferenceProvider for Script {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        _: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        let n = self.probe.polls.fetch_add(1, Ordering::SeqCst);
        if self.deny || n >= 2 {
            return Poll::Ready(Err(Error::Provider));
        }
        self.probe.seen.lock().unwrap().push(request.clone());
        let Input::Structured { role, .. } = &request.input else {
            return Poll::Ready(Err(Error::Provider));
        };
        let value = match role.as_str() {
            "director" => json!({"commands":[{"op":"discover","fact":"relic-location"}]}),
            "narrator" => {
                json!({"text":"You notice a golden marker beside the quay.","event_ids":[request.revision+1],"speaker":"narrator"})
            }
            _ => return Poll::Ready(Err(Error::Provider)),
        };
        Poll::Ready(Ok(serde_json::to_vec(&value).unwrap()))
    }
}
fn configure(host: &Host, probe: &Probe, deny: bool) {
    let shared = probe.clone();
    host.configure_fixture_provider(
        profile(),
        Arc::new(move || {
            shared.factories.fetch_add(1, Ordering::SeqCst);
            Box::new(Script {
                probe: shared.clone(),
                deny,
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
fn read(path: &std::path::Path, scope: &Scope) -> Engine {
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
fn observed(engine: &Engine, actor: &str) -> String {
    engine
        .observed_facts(actor, engine.scope(), engine.revision())
        .unwrap()["relic-location"]
        .proposition
        .clone()
}

#[test]
fn durable_play25_discovery_archive3_roundtrip_preserves_observation_sources_and_zero_call_retry() {
    let temp = Temp::new();
    let source_path = temp.path("source.sqlite");
    let imported_path = temp.path("imported.sqlite");
    let initial = seed();
    let parent = initial.scope.clone();
    let mut source = Store::open_application(&source_path).unwrap();
    source
        .create_story("Synthetic current generated-play transfer", initial)
        .unwrap();
    let root = source.resume(&parent).unwrap().engine;
    let old_request = root.request(
        "observed-before-author",
        Intent::Actions(vec![Command::Discover {
            fact: "relic-location".into(),
        }]),
    );
    let approved = root
        .preview(&old_request, &Engine::proposal(&old_request).unwrap())
        .unwrap();
    source.begin_turn(&old_request).unwrap();
    source.commit_prepared(&approved).unwrap();
    let original_parent = source.resume(&parent).unwrap().engine;
    assert_eq!(observed(&original_parent, "player"), A);
    let author_input = AuthorCorrectionInputV1 {
        version: 1,
        parent: parent.clone(),
        expected_parent_revision: 1,
        fork_revision: 1,
        child_branch: "corrected".into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(),
            expected_proposition: A.into(),
            replacement: B.into(),
        },
        reason: REASON.into(),
    };
    let plan = source
        .prepare_author_correction(&author_input, &|| false)
        .unwrap();
    let author = source.apply_author_correction(&plan, &|| false).unwrap();
    let child = author.scope.clone();
    let before = source.resume(&child).unwrap().engine;
    assert_eq!(before.revision(), 2);
    assert_eq!(before.domain_version(), 2);
    assert_eq!(
        before.effective_fact("relic-location").unwrap().proposition,
        B
    );
    assert_eq!(observed(&before, "player"), A);
    assert_eq!(observed(&before, "mira"), A);
    drop(source);

    let host = locallore_workspace::open(&source_path, false).unwrap();
    let probe = Probe::default();
    configure(&host, &probe, false);
    let session = resume(&host, &child);
    let request = before.request(
        "original-generated-discovery",
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: "I discover relic-location.".into(),
        },
    );
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
    equivalent(&read(&source_path, &child), &before);
    let committed = control(&host, &session, &request, "commit");
    assert_eq!(data(&committed)["phase"], "committed");
    assert_eq!(probe.factories.load(Ordering::SeqCst), 1);
    assert_eq!(probe.polls.load(Ordering::SeqCst), 2);
    {
        let seen = probe.seen.lock().unwrap();
        assert_eq!(seen.len(), 2);
        for generated in seen.iter() {
            assert_eq!(generated.scope, child);
            assert_eq!(generated.turn, request.turn);
            assert_eq!(generated.revision, 2);
            let Input::Structured { prompt, .. } = &generated.input else {
                panic!("Structured role required");
            };
            assert!(!prompt.contains(REASON));
        }
        let Input::Structured {
            role,
            prompt: director,
            ..
        } = &seen[0].input
        else {
            unreachable!()
        };
        assert_eq!(role, "director");
        assert!(director.contains(A));
        assert!(!director.contains(B));
        let Input::Structured {
            role,
            prompt: narrator,
            ..
        } = &seen[1].input
        else {
            unreachable!()
        };
        assert_eq!(role, "narrator");
        assert!(narrator.contains(B));
        assert!(!narrator.contains(A));
    }
    drop(host);

    let mut source = Store::open_application(&source_path).unwrap();
    let accepted = source.resume(&child).unwrap().engine;
    let saved = source.lookup_turn(&child, &request.turn).unwrap();
    assert_eq!(saved.phase, TurnPhase::Committed);
    assert_eq!(saved.request, request);
    let receipt = saved.receipt.unwrap();
    assert_eq!(
        data(&committed)["receipt"],
        serde_json::to_value(&receipt).unwrap()
    );
    let play = receipt.play().unwrap();
    assert_eq!(play.version, 2);
    assert_eq!(play.prompt_version, "locallore-play-v2.5");
    assert_eq!(play.policy, "grounded-prose-v2.5-whole-evidence-words-v1");
    assert_eq!(play.profile, profile());
    assert_eq!(
        play.context_policy,
        Some(ContextPolicy::StateRelevantMemoryV1)
    );
    let context = play.context.as_ref().unwrap();
    assert_eq!(context.version, 2);
    assert_eq!(context.compiler_version, 2);
    assert_eq!(context.scope, child);
    assert_eq!(context.head, 2);
    assert_eq!(context.observer, "player");
    assert!(!play.fallback);
    assert_eq!(play.repairs, 0);
    assert!(!play.stages.is_empty());
    assert_eq!(play.narration.event_ids, vec![3]);
    assert_eq!(accepted.revision(), 3);
    assert_eq!(accepted.canonical_record_count(), 3);
    assert!(matches!(
        accepted.canonical_records().last().unwrap(),
        CanonicalRecord::PlayV2(_)
    ));
    assert_eq!(receipt.events().len(), 1);
    let event = &receipt.events()[0];
    assert_eq!(event.scope(), &child);
    assert_eq!(event.sequence(), 3);
    assert!(event.witnesses().contains("player"));
    assert!(!event.witnesses().contains("mira"));
    assert!(!event.witnesses().contains("sable"));
    assert_eq!(observed(&accepted, "player"), B);
    assert_eq!(observed(&accepted, "mira"), A);
    assert!(!accepted
        .observed_facts("sable", &child, 3)
        .unwrap()
        .contains_key("relic-location"));
    let player_views = accepted.actor_receipts_v2("player", &child, 3).unwrap();
    let old = player_views
        .iter()
        .find(|view| view.turn == old_request.turn)
        .unwrap();
    assert_eq!(old.original_scope, parent);
    assert_eq!(old.events[0].event.scope(), &parent);
    assert_eq!(old.events[0].discovery.as_ref().unwrap().proposition, A);
    let current = player_views
        .iter()
        .find(|view| view.turn == request.turn)
        .unwrap();
    assert_eq!(current.original_scope, child);
    let discovery = current.events[0].discovery.as_ref().unwrap();
    assert_eq!(discovery.proposition, B);
    let ObservationSource::Event {
        source: observation,
    } = &discovery.observation
    else {
        panic!("actual event observation required");
    };
    assert_eq!(observation.original_scope, child);
    assert_eq!(observation.sequence, 3);
    let npc_context =
        serde_json::to_string(&accepted.character_context_v2("mira", &child, 3).unwrap()).unwrap();
    assert!(npc_context.contains(A));
    assert!(!npc_context.contains(B));
    assert!(!npc_context.contains(REASON));
    equivalent(&source.resume(&parent).unwrap().engine, &original_parent);

    let archive = source.export_archive(&parent.story, &|| false).unwrap();
    assert_eq!(archive.preview().version, 3);
    assert_eq!(archive.preview().committed_turns, 3);
    let wire: Value = serde_json::from_slice(archive.bytes()).unwrap();
    assert_eq!(wire["version"], 3);
    assert_eq!(wire["payload"]["domain_version"], 2);
    assert_eq!(wire["payload"]["source_database_schema_version"], 5);
    let validated = validate_archive(archive.bytes(), &|| false).unwrap();
    assert_eq!(
        serde_json::to_value(validated.preview()).unwrap(),
        serde_json::to_value(archive.preview()).unwrap()
    );
    let mut target = Store::open_application(&imported_path).unwrap();
    let imported = target.import_archive(validated, &|| false).unwrap();
    assert_eq!(imported.root, parent);
    assert_eq!(imported.branches, 2);
    assert_eq!(imported.committed_turns, 3);
    drop(target);
    drop(source);
    equivalent(&read(&imported_path, &child), &accepted);
    equivalent(&read(&imported_path, &parent), &original_parent);

    let reopened = locallore_workspace::open(&imported_path, false).unwrap();
    let retry_probe = Probe::default();
    configure(&reopened, &retry_probe, true);
    let imported_session = resume(&reopened, &child);
    assert_eq!(
        call(
            &reopened,
            json!({"op":"free_text","session":imported_session,"request":request})
        ),
        committed
    );
    for op in ["prepare", "commit", "turn_status", "cancel"] {
        assert_eq!(
            control(&reopened, &imported_session, &request, op),
            committed
        );
    }
    assert_eq!(retry_probe.factories.load(Ordering::SeqCst), 0);
    assert_eq!(retry_probe.polls.load(Ordering::SeqCst), 0);
    assert!(retry_probe.seen.lock().unwrap().is_empty());
    reopened.disable_local_provider();
    assert_eq!(
        call(
            &reopened,
            json!({"op":"free_text","session":imported_session,"request":request})
        ),
        committed
    );
    let mut different = request.clone();
    let Intent::FreeText { text, .. } = &mut different.intent else {
        unreachable!()
    };
    text.push_str(" now");
    let mismatch = call(
        &reopened,
        json!({"op":"free_text","session":imported_session,"request":different}),
    );
    assert_eq!(mismatch["status"], "rejected");
    assert_eq!(mismatch["error"], "RetryMismatch");
    drop(reopened);
    equivalent(&read(&imported_path, &child), &accepted);
    equivalent(&read(&imported_path, &parent), &original_parent);
    assert_eq!(probe.polls.load(Ordering::SeqCst), 2);
}
