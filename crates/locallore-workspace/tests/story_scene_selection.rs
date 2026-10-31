// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! FIRST source-frozen Host selection oracles. UNCOMPILED / UNRUN at handoff.
//! Real Store, Workspace, corrections, native configuration and trace capture.
//! Recording/held providers are synthetic; no model, GUI, JNI or device proof.
use locallore::{
    author_correction::*,
    contracts::*,
    engine::Engine,
    host::{Host, HostPlayConstructionV1, ProviderFactory},
    inference::*,
    inspection::sha256,
    play::{
        authored_scene_narration::AuthoredSceneRecipeV2, scene_narration::SceneRecipeV1,
        PlayContextPolicy, PlayProfile,
    },
    story_authoring::*,
};
use locallore_storage::{Store, TurnPhase};
use serde_json::{json, Value};
use std::{
    path::PathBuf,
    sync::{
        atomic::{AtomicBool, AtomicU64, AtomicUsize, Ordering},
        mpsc, Arc, Condvar, Mutex,
    },
    task::Poll,
    time::Duration,
};

const STARTER_PROMPT: &str = "locallore-play-v2.9-scene-frame-v1";
const AUTHORED_PROMPT: &str = "locallore-play-v2.11-authored-scene-frame-v2";
const STARTER_POLICY: &str = "grounded-prose-v2.7-scene-frame-whole-evidence-words-v1";
const AUTHORED_POLICY: &str = "grounded-prose-v2.8-authored-scene-frame-v2";
const AUTHORED_STORY: &str = "story-scene-authored";
fn policy() -> PlayContextPolicy {
    PlayContextPolicy::StateRelevantMemoryV1
}
fn selected() -> HostPlayConstructionV1 {
    HostPlayConstructionV1::MemoryStorySceneV1(policy())
}
fn profile() -> PlayProfile {
    PlayProfile {
        id: "story-scene-shared-profile".into(),
        model_sha256: "a".repeat(64),
        runtime_revision: "b".repeat(40),
        template_sha256: "c".repeat(64),
        worker_sha256: "d".repeat(64),
        profile_manifest_sha256: "e".repeat(64),
        context_tokens: 4096,
        director_tokens: 350,
        narrator_tokens: 350,
        deadline_ms: 5000,
        repair_limit: 1,
    }
}
fn authored_seed() -> Seed {
    let input: InitialStoryInputV1 = serde_json::from_str(include_str!(
        "../../../fixtures/initial_world/ashglass-input.json"
    ))
    .unwrap();
    let accepted: InitialWorldProposalV1 = serde_json::from_str(include_str!(
        "../../../fixtures/initial_world/ashglass-proposal.json"
    ))
    .unwrap();
    validate_proposal(&input, &accepted).unwrap();
    let response = serde_json::to_string(&accepted).unwrap();
    let origin = InitialWorldOriginV1 {
        version: 1,
        generation: InitialGenerationV1 {
            input: input.clone(),
            proposal: accepted.clone(),
            model_profile: profile().id.clone(),
            model_configuration: InitialModelConfigurationV1::from(&profile()),
            provider: InitialProviderKindV1::Scripted,
            prompt_version: locallore::story_authoring::PROMPT_VERSION.into(),
            schema_version: locallore::story_authoring::SCHEMA_VERSION.into(),
            response_sha256: sha256(response.as_bytes()),
            response,
        },
        reviewed: input,
        accepted,
        title: "Synthetic selection at the weather station".into(),
    };
    let seed = materialize(
        &origin,
        Scope {
            story: AUTHORED_STORY.into(),
            branch: "main".into(),
        },
    )
    .unwrap();
    validate_origin(&seed).unwrap();
    seed
}
struct Fixture {
    root: PathBuf,
    starter: Scope,
    authored: Scope,
}
impl Fixture {
    fn new() -> Self {
        static NEXT: AtomicU64 = AtomicU64::new(0);
        let time = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let root = std::env::temp_dir().join(format!(
            "story-scene-selection-{time}-{}",
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&root).unwrap();
        let mut starter: Seed =
            serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
        starter.scope.story = "story-scene-starter".into();
        let authored = authored_seed();
        let fixture = Self {
            root,
            starter: starter.scope.clone(),
            authored: authored.scope.clone(),
        };
        let mut store = Store::open_application(&fixture.db()).unwrap();
        store
            .create_story("Synthetic quay selection", starter)
            .unwrap();
        store
            .create_story("Synthetic authored selection", authored)
            .unwrap();
        drop(store);
        fixture
    }
    fn db(&self) -> PathBuf {
        self.root.join("stories.sqlite")
    }
    fn host(&self) -> Host {
        locallore_workspace::open(&self.db(), true).unwrap()
    }
    fn engine(&self, scope: &Scope) -> Engine {
        Store::open_read_only(&self.db())
            .unwrap()
            .resume(scope)
            .unwrap()
            .engine
    }
    // Keep small owner-created databases and failed captures for diagnosis.
}
#[derive(Clone, Copy)]
enum Expected {
    Starter,
    Authored,
}
impl Expected {
    fn prompt(self) -> &'static str {
        match self {
            Self::Starter => STARTER_PROMPT,
            Self::Authored => AUTHORED_PROMPT,
        }
    }
    fn policy(self) -> &'static str {
        match self {
            Self::Starter => STARTER_POLICY,
            Self::Authored => AUTHORED_POLICY,
        }
    }
    fn frame_version(self) -> u16 {
        match self {
            Self::Starter => 1,
            Self::Authored => 2,
        }
    }
}
#[derive(Default)]
struct Seen {
    factories: AtomicUsize,
    requests: Mutex<Vec<GenerationRequest>>,
    plain: bool,
    hold: Option<Arc<Hold>>,
}
impl Seen {
    fn factory(self: &Arc<Self>) -> ProviderFactory {
        let seen = self.clone();
        Arc::new(move || {
            seen.factories.fetch_add(1, Ordering::SeqCst);
            Box::new(Script(seen.clone()))
        })
    }
    fn requests(&self, request: &Request) -> Vec<GenerationRequest> {
        self.requests
            .lock()
            .unwrap()
            .iter()
            .filter(|value| value.scope == request.scope && value.turn == request.turn)
            .cloned()
            .collect()
    }
}
struct Script(Arc<Seen>);
impl InferenceProvider for Script {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        _: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        self.0.requests.lock().unwrap().push(request.clone());
        let Input::Structured { role, prompt, .. } = &request.input else {
            panic!("actual structured input required")
        };
        let value = match role.as_str() {
            "director" => json!({"commands":[{"op":"wait","ticks":1}]}),
            "narrator" => {
                for secret in [
                    "SECRET-TIDE-731",
                    "ASHGLASS-NPC-319",
                    "ASHGLASS-VALVE-701",
                    "ASHGLASS-RUMOR-622",
                    "PRIVATE_STORY_SELECTION_REASON",
                ] {
                    assert!(
                        !prompt.contains(secret),
                        "private source reached narrator: {secret}"
                    );
                }
                if let Some(hold) = &self.0.hold {
                    hold.wait_once();
                }
                // This controlled response table is keyed by known fixture story;
                // it neither chooses a recipe nor replaces any real validator.
                let text = if self.0.plain {
                    "You pause."
                } else if request.scope.story == AUTHORED_STORY {
                    assert!(!prompt.contains("A dry stone court stands above the cloudline."));
                    "You pause at Summit court."
                } else {
                    "You pause beside the quay."
                };
                json!({"text":text,"event_ids":[request.revision+1],"speaker":"narrator"})
            }
            _ => panic!("unexpected role {role}"),
        };
        Poll::Ready(Ok(serde_json::to_vec(&value).unwrap()))
    }
}
struct Hold {
    entered: mpsc::SyncSender<()>,
    released: Mutex<bool>,
    wake: Condvar,
    used: AtomicBool,
}
impl Hold {
    fn wait_once(&self) {
        if self.used.swap(true, Ordering::SeqCst) {
            return;
        }
        self.entered.send(()).unwrap();
        let (_released, timeout) = self
            .wake
            .wait_timeout_while(
                self.released.lock().unwrap(),
                Duration::from_secs(5),
                |released| !*released,
            )
            .unwrap();
        assert!(!timeout.timed_out(), "bounded held provider release");
        // Deliberately return a valid response despite cancellation: Host owns
        // publication fencing, not this noncooperative synthetic provider.
    }
    fn release(&self) {
        *self.released.lock().unwrap() = true;
        self.wake.notify_all();
    }
}
struct Release(Arc<Hold>);
impl Drop for Release {
    fn drop(&mut self) {
        self.0.release();
    }
}
fn call(host: &Host, command: Value) -> Value {
    host.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
}
fn ok(reply: Value) -> Value {
    assert_eq!(reply["status"], "ok", "{reply}");
    reply["data"].clone()
}
fn resume(host: &Host, source: &Engine) -> String {
    let value = ok(call(host, json!({"op":"resume","scope":source.scope()})));
    assert_eq!(value["revision"], source.revision());
    value["session"].as_str().unwrap().into()
}
fn request(source: &Engine, key: &str) -> Request {
    source.request(
        key,
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: "I wait for one tide tick.".into(),
        },
    )
}
fn submit(host: &Host, session: &str, request: &Request) -> Value {
    call(
        host,
        json!({"op":"submit","session":session,"request":request,"mode":"accepted"}),
    )
}
fn operation(host: &Host, session: &str, request: &Request, op: &str) -> Value {
    call(
        host,
        json!({"op":op,"session":session,"scope":request.scope,"turn":request.turn}),
    )
}
fn unchanged(actual: &Engine, before: &Engine) {
    assert_eq!(actual.seed(), before.seed());
    assert_eq!(actual.scope(), before.scope());
    assert_eq!(actual.canonical_records(), before.canonical_records());
    assert_eq!(actual.canonical_bytes(), before.canonical_bytes());
    assert_eq!(
        actual.accepted_history_basis().unwrap(),
        before.accepted_history_basis().unwrap()
    );
}
fn assert_concrete(source: &Engine, receipt: &Receipt, seen: &Seen, expected: Expected) {
    let record = receipt.play().unwrap();
    assert!(!record.fallback);
    assert_eq!(record.prompt_version, expected.prompt());
    assert_eq!(record.policy, expected.policy());
    assert_eq!(record.context_policy, Some(policy()));
    assert_eq!(
        record.scene.as_ref().unwrap().version,
        expected.frame_version()
    );
    let (frame_bytes, prompt, schema) = match expected {
        Expected::Starter => {
            let stage = source
                .stage_scene_play_v1(receipt.request(), receipt.proposal(), &|| false)
                .unwrap();
            let bound = source
                .bind_scene_play_v1(stage, SceneRecipeV1::Memory(policy()), &|| false)
                .unwrap();
            let rendered = locallore::play::scene_narration::render_scene_narrator_v1(
                &bound,
                &profile(),
                &|| false,
            )
            .unwrap();
            (
                serde_json::to_vec(bound.scene_frame()).unwrap(),
                rendered.prompt().to_owned(),
                rendered.schema().clone(),
            )
        }
        Expected::Authored => {
            let stage = source
                .stage_authored_scene_play_v2(receipt.request(), receipt.proposal(), &|| false)
                .unwrap();
            let bound = source
                .bind_authored_scene_play_v2(
                    stage,
                    AuthoredSceneRecipeV2::Memory(policy()),
                    &|| false,
                )
                .unwrap();
            let rendered =
                locallore::play::authored_scene_narration::render_authored_scene_narrator_v2(
                    &bound,
                    &profile(),
                    &|| false,
                )
                .unwrap();
            assert_eq!(
                bound.scene_frame().location_label().unwrap().name(),
                "Summit court"
            );
            (
                serde_json::to_vec(bound.scene_frame()).unwrap(),
                rendered.prompt().to_owned(),
                rendered.schema().clone(),
            )
        }
    };
    assert_eq!(
        record.scene.as_ref().unwrap().frame_sha256,
        sha256(&frame_bytes)
    );
    let actual = seen.requests(receipt.request());
    assert_eq!(actual.len(), 2);
    assert_eq!(actual[0].schema, "locallore-director-v2");
    assert_eq!(actual[1].schema, "locallore-narrator-v2");
    let Input::Structured {
        role,
        prompt: forwarded,
        schema: forwarded_schema,
    } = &actual[1].input
    else {
        panic!("actual narrator request")
    };
    assert_eq!(role, "narrator");
    assert_eq!(forwarded, &prompt);
    assert_eq!(forwarded_schema, &schema);
    assert!(forwarded.contains(std::str::from_utf8(&frame_bytes).unwrap()));
}
fn complete(
    fixture: &Fixture,
    host: &Host,
    session: &str,
    scope: &Scope,
    key: &str,
    seen: &Seen,
    expected: Expected,
) -> (Request, Receipt) {
    let source = fixture.engine(scope);
    let request = request(&source, key);
    ok(call(
        host,
        json!({"op":"trace_capture_configure","session":session,"scope":scope,"expected_head":source.revision(),"enabled":true,"consent":true}),
    ));
    assert_eq!(ok(submit(host, session, &request))["phase"], "queued");
    assert_eq!(
        ok(operation(host, session, &request, "prepare"))["phase"],
        "ready"
    );
    unchanged(&fixture.engine(scope), &source);
    let trace = ok(call(
        host,
        json!({"op":"trace_read","session":session,"scope":scope,"expected_head":source.revision(),
        "base_revision":source.revision(),"observer":{"kind":"player"},"turn":request.turn,"attempt":null}),
    ));
    let attempts = trace["snapshot"]["attempts"].as_array().unwrap();
    assert_eq!(attempts.len(), 1);
    assert_eq!(attempts[0]["provenance"]["prompt_label"], expected.prompt());
    assert_eq!(
        attempts[0]["provenance"]["schema_label"],
        "locallore-play-v2"
    );
    let capture = ok(call(
        host,
        json!({"op":"trace_capture_read","session":session,"scope":scope,"expected_head":source.revision(),
        "base_revision":source.revision(),"turn":request.turn,"attempt":attempts[0]["identity"]["attempt"]}),
    ));
    assert_eq!(capture["details"]["status"], "recorded");
    assert_eq!(
        capture["details"]["identity"]["observer"],
        source.seed().player
    );
    assert_eq!(capture["details"]["identity"]["scope"], json!(scope));
    let actual = seen.requests(&request);
    for forwarded in &actual {
        let Input::Structured {
            role,
            prompt,
            schema,
        } = &forwarded.input
        else {
            panic!("structured capture")
        };
        let rows: Vec<_> = capture["details"]["artifacts"]
            .as_array()
            .unwrap()
            .iter()
            .filter(|value| {
                value["kind"] == "generation_request" && value["value"]["input"]["role"] == *role
            })
            .collect();
        assert_eq!(rows.len(), 1);
        assert_eq!(rows[0]["value"]["scope"], json!(scope));
        assert_eq!(rows[0]["value"]["turn"], request.turn);
        assert_eq!(rows[0]["value"]["revision"], source.revision());
        assert_eq!(
            rows[0]["value"]["input"],
            json!({"kind":"structured","role":role,"prompt":prompt,"schema":schema})
        );
    }
    let committed = ok(operation(host, session, &request, "commit"));
    assert_eq!(committed["phase"], "committed");
    let saved = Store::open_read_only(&fixture.db())
        .unwrap()
        .lookup_turn(scope, &request.turn)
        .unwrap();
    assert_eq!(saved.phase, TurnPhase::Committed);
    let receipt = saved.receipt.unwrap();
    assert_eq!(committed["receipt"], json!(receipt));
    assert_concrete(&source, &receipt, seen, expected);
    let after = fixture.engine(scope);
    assert_eq!(
        after.canonical_record_count(),
        source.canonical_record_count() + 1
    );
    let mut mechanical = source.clone();
    let control = mechanical.request(
        &request.turn,
        Intent::Actions(vec![Command::Wait { ticks: 1 }]),
    );
    let approved = mechanical
        .preview(&control, &Engine::proposal(&control).unwrap())
        .unwrap();
    mechanical.commit_prepared(&approved).unwrap();
    assert_eq!(after.state(), mechanical.state());
    (request, receipt)
}

#[test]
fn one_host_alternates_starter_authored_starter_with_concrete_trace_and_no_cached_choice() {
    let fixture = Fixture::new();
    let host = fixture.host();
    let seen = Arc::new(Seen::default());
    host.configure_fixture_provider_with_construction(profile(), seen.factory(), selected())
        .unwrap();
    let starter = fixture.engine(&fixture.starter);
    let authored = fixture.engine(&fixture.authored);
    assert_eq!(starter.domain_version(), 1);
    assert_eq!(authored.domain_version(), 1);
    let first = resume(&host, &starter);
    let second = resume(&host, &authored);
    complete(
        &fixture,
        &host,
        &first,
        &fixture.starter,
        "starter-first",
        &seen,
        Expected::Starter,
    );
    unchanged(&fixture.engine(&fixture.authored), &authored);
    complete(
        &fixture,
        &host,
        &second,
        &fixture.authored,
        "authored-middle",
        &seen,
        Expected::Authored,
    );
    complete(
        &fixture,
        &host,
        &first,
        &fixture.starter,
        "starter-again",
        &seen,
        Expected::Starter,
    );
    assert_eq!(seen.factories.load(Ordering::SeqCst), 3);
    host.close_all();
    assert_eq!(host.live_counts(), (0, 0));
}

#[test]
fn corrected_branches_of_both_story_kinds_select_by_seed_and_keep_parent_canon() {
    let fixture = Fixture::new();
    let host = fixture.host();
    let starter = fixture.engine(&fixture.starter);
    let authored = fixture.engine(&fixture.authored);
    let mut children = vec![];
    for (parent, fact, expected) in [
        (&starter, "relic-location".to_owned(), Expected::Starter),
        (
            &authored,
            authored
                .seed()
                .facts
                .keys()
                .find(|key| key.ends_with("-location-0"))
                .unwrap()
                .clone(),
            Expected::Authored,
        ),
    ] {
        let session = resume(&host, parent);
        let input = AuthorCorrectionInputV1 {
            version: 1,
            parent: parent.scope().clone(),
            expected_parent_revision: parent.revision(),
            fork_revision: parent.revision(),
            child_branch: "corrected".into(),
            operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
                fact: fact.clone(),
                expected_proposition: parent.seed().facts[&fact].proposition.clone(),
                replacement: "A newly corrected untyped account.".into(),
            },
            reason: "PRIVATE_STORY_SELECTION_REASON".into(),
        };
        let prepared = host
            .prepare_author_correction(&session, &input, &|| false)
            .unwrap();
        let outcome = host.apply_author_correction(&prepared, &|| false).unwrap();
        let child = fixture.engine(&outcome.scope);
        assert_eq!(child.domain_version(), 2);
        assert_eq!(child.canonical_record_count(), 1);
        children.push((child, expected));
    }
    let seen = Arc::new(Seen::default());
    host.configure_fixture_provider_with_construction(profile(), seen.factory(), selected())
        .unwrap();
    for (child, expected) in children {
        let session = resume(&host, &child);
        complete(
            &fixture,
            &host,
            &session,
            child.scope(),
            "corrected-scene",
            &seen,
            expected,
        );
        let after = fixture.engine(child.scope());
        assert_eq!(after.domain_version(), 2);
        unchanged(
            &Engine::replay_records(after.seed().clone(), after.canonical_records()).unwrap(),
            &after,
        );
    }
    unchanged(&fixture.engine(&fixture.starter), &starter);
    unchanged(&fixture.engine(&fixture.authored), &authored);
    assert_eq!(seen.factories.load(Ordering::SeqCst), 2);
    host.close_all();
    assert_eq!(host.live_counts(), (0, 0));
}

#[test]
fn durable_exact_retries_after_reopen_keep_both_concrete_records_without_a_provider() {
    let fixture = Fixture::new();
    let host = fixture.host();
    let seen = Arc::new(Seen::default());
    host.configure_fixture_provider_with_construction(profile(), seen.factory(), selected())
        .unwrap();
    let mut saved = vec![];
    for (scope, expected) in [
        (&fixture.starter, Expected::Starter),
        (&fixture.authored, Expected::Authored),
    ] {
        let source = fixture.engine(scope);
        let session = resume(&host, &source);
        let (request, receipt) = complete(
            &fixture,
            &host,
            &session,
            scope,
            "same-key-each-story",
            &seen,
            expected,
        );
        saved.push((request, receipt, fixture.engine(scope)));
    }
    host.close_all();
    drop(host);
    let reopened = fixture.host();
    let trap: ProviderFactory = Arc::new(|| panic!("recorded retry cannot create a provider"));
    reopened
        .configure_fixture_provider_with_construction(profile(), trap, selected())
        .unwrap();
    for (request, receipt, before) in saved {
        let session = resume(&reopened, &before);
        for reply in [
            operation(&reopened, &session, &request, "turn_status"),
            submit(&reopened, &session, &request),
            operation(&reopened, &session, &request, "prepare"),
            operation(&reopened, &session, &request, "commit"),
        ] {
            let value = ok(reply);
            assert_eq!(value["phase"], "committed");
            assert_eq!(value["receipt"], json!(receipt));
        }
        unchanged(&fixture.engine(&request.scope), &before);
    }
    assert_eq!(seen.factories.load(Ordering::SeqCst), 2);
    reopened.close_all();
    assert_eq!(reopened.live_counts(), (0, 0));
}

#[test]
fn cancelled_authored_ready_turn_does_not_poison_other_story_selection_or_reopen_canon() {
    let fixture = Fixture::new();
    let host = fixture.host();
    let seen = Arc::new(Seen::default());
    host.configure_fixture_provider_with_construction(profile(), seen.factory(), selected())
        .unwrap();
    let authored = fixture.engine(&fixture.authored);
    let session = resume(&host, &authored);
    let request = request(&authored, "cancel-ready");
    ok(submit(&host, &session, &request));
    assert_eq!(
        ok(operation(&host, &session, &request, "prepare"))["phase"],
        "ready"
    );
    assert_eq!(
        ok(operation(&host, &session, &request, "cancel"))["phase"],
        "cancelled"
    );
    let terminal = ok(operation(&host, &session, &request, "commit"));
    assert_eq!(terminal["phase"], "cancelled");
    assert!(terminal["receipt"].is_null());
    unchanged(&fixture.engine(&fixture.authored), &authored);
    let starter = fixture.engine(&fixture.starter);
    let other = resume(&host, &starter);
    complete(
        &fixture,
        &host,
        &other,
        &fixture.starter,
        "after-authored-cancel",
        &seen,
        Expected::Starter,
    );
    host.close_all();
    drop(host);
    let reopened = fixture.host();
    let session = resume(&reopened, &authored);
    assert_eq!(
        ok(operation(&reopened, &session, &request, "turn_status"))["phase"],
        "cancelled"
    );
    unchanged(&fixture.engine(&fixture.authored), &authored);
    reopened.close_all();
    assert_eq!(reopened.live_counts(), (0, 0));
}

#[test]
fn stale_starter_candidate_cannot_append_and_authored_story_still_uses_its_own_recipe() {
    let fixture = Fixture::new();
    let host = fixture.host();
    let seen = Arc::new(Seen::default());
    host.configure_fixture_provider_with_construction(profile(), seen.factory(), selected())
        .unwrap();
    let starter = fixture.engine(&fixture.starter);
    let session = resume(&host, &starter);
    let request = request(&starter, "prepared-loser");
    ok(submit(&host, &session, &request));
    assert_eq!(
        ok(operation(&host, &session, &request, "prepare"))["phase"],
        "ready"
    );
    let winner = starter.request(
        "typed-winner",
        Intent::Actions(vec![Command::Wait { ticks: 1 }]),
    );
    ok(submit(&host, &session, &winner));
    ok(operation(&host, &session, &winner, "prepare"));
    assert_eq!(
        ok(operation(&host, &session, &winner, "commit"))["phase"],
        "committed"
    );
    let before = fixture.engine(&fixture.starter);
    let stale = ok(operation(&host, &session, &request, "commit"));
    assert_eq!(stale["phase"], "stale");
    assert!(stale["receipt"].is_null());
    unchanged(&fixture.engine(&fixture.starter), &before);
    assert_eq!(before.canonical_record_count(), 1);
    let authored = fixture.engine(&fixture.authored);
    let other = resume(&host, &authored);
    complete(
        &fixture,
        &host,
        &other,
        &fixture.authored,
        "after-starter-stale",
        &seen,
        Expected::Authored,
    );
    assert_eq!(seen.factories.load(Ordering::SeqCst), 2);
    host.close_all();
    assert_eq!(host.live_counts(), (0, 0));
}

#[test]
fn foreign_scope_and_late_noncooperative_output_after_close_never_reach_canon_or_next_session() {
    let fixture = Fixture::new();
    let host = fixture.host();
    let (tx, rx) = mpsc::sync_channel(1);
    let hold = Arc::new(Hold {
        entered: tx,
        released: Mutex::new(false),
        wake: Condvar::new(),
        used: AtomicBool::new(false),
    });
    let seen = Arc::new(Seen {
        hold: Some(hold.clone()),
        ..Seen::default()
    });
    host.configure_fixture_provider_with_construction(profile(), seen.factory(), selected())
        .unwrap();
    let starter = fixture.engine(&fixture.starter);
    let authored = fixture.engine(&fixture.authored);
    let first = resume(&host, &starter);
    let session = resume(&host, &authored);
    let request = request(&authored, "held-authored-output");
    assert_eq!(submit(&host, &first, &request)["error"], "Scope");
    assert_eq!(seen.factories.load(Ordering::SeqCst), 0);
    ok(submit(&host, &session, &request));
    std::thread::scope(|threads| {
        let release = Release(hold.clone());
        let worker = threads.spawn(|| operation(&host, &session, &request, "prepare"));
        rx.recv_timeout(Duration::from_secs(5))
            .expect("owned narrator reached the explicit hold");
        host.close_all();
        hold.release();
        let reply = worker.join().expect("owned prepare worker joined");
        assert_eq!(reply["status"], "rejected");
        assert_eq!(reply["error"], "Closed");
        assert!(reply["data"]["receipt"].is_null());
        assert_ne!(reply["data"]["phase"], "committed");
        drop(release);
    });
    assert_eq!(host.live_counts(), (0, 0));
    unchanged(&fixture.engine(&fixture.authored), &authored);
    unchanged(&fixture.engine(&fixture.starter), &starter);
    let calls = seen.factories.load(Ordering::SeqCst);
    assert_eq!(
        operation(&host, &session, &request, "prepare")["status"],
        "rejected"
    );
    assert_eq!(seen.factories.load(Ordering::SeqCst), calls);
    let next = resume(&host, &starter);
    complete(
        &fixture,
        &host,
        &next,
        &fixture.starter,
        "new-session-after-close",
        &seen,
        Expected::Starter,
    );
    unchanged(&fixture.engine(&fixture.authored), &authored);
    host.close_all();
    assert_eq!(host.live_counts(), (0, 0));
}

#[test]
fn existing_default_and_fixed_native_recipes_remain_explicit_and_refuse_cross_seed_retagging() {
    for authored in [false, true] {
        for fixed in [0, 1, 2] {
            let fixture = Fixture::new();
            let host = fixture.host();
            let seen = Arc::new(Seen {
                plain: true,
                ..Seen::default()
            });
            match fixed {
                0 => host
                    .configure_fixture_provider(profile(), seen.factory())
                    .unwrap(),
                1 => host
                    .configure_fixture_provider_with_construction(
                        profile(),
                        seen.factory(),
                        HostPlayConstructionV1::MemorySceneV1(policy()),
                    )
                    .unwrap(),
                _ => host
                    .configure_fixture_provider_with_construction(
                        profile(),
                        seen.factory(),
                        HostPlayConstructionV1::MemoryAuthoredSceneV2(policy()),
                    )
                    .unwrap(),
            }
            let scope = if authored {
                &fixture.authored
            } else {
                &fixture.starter
            };
            let before = fixture.engine(scope);
            let session = resume(&host, &before);
            let request = request(&before, "fixed-compatibility");
            ok(submit(&host, &session, &request));
            let prepared = operation(&host, &session, &request, "prepare");
            if (fixed == 1 && authored) || (fixed == 2 && !authored) {
                let failed = ok(prepared);
                assert_eq!(failed["phase"], "failed");
                assert_eq!(failed["error"], "Version");
                assert!(seen.requests(&request).is_empty());
                unchanged(&fixture.engine(scope), &before);
            } else {
                assert_eq!(ok(prepared)["phase"], "ready");
                let done = ok(operation(&host, &session, &request, "commit"));
                assert_eq!(done["phase"], "committed");
                let play = &done["receipt"]["play"];
                if fixed == 0 {
                    assert!(play["scene"].is_null());
                    assert_eq!(
                        play["policy"],
                        "grounded-prose-v2.5-whole-evidence-words-v1"
                    );
                } else {
                    assert_eq!(play["scene"]["version"], if authored { 2 } else { 1 });
                    assert_eq!(
                        play["policy"],
                        if authored {
                            AUTHORED_POLICY
                        } else {
                            STARTER_POLICY
                        }
                    );
                }
                assert_eq!(
                    fixture.engine(scope).canonical_record_count(),
                    before.canonical_record_count() + 1
                );
            }
            host.close_all();
            assert_eq!(host.live_counts(), (0, 0));
        }
    }
}
