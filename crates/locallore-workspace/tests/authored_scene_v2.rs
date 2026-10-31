// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! First independent durable V2 oracles. SOURCE ONLY / UNCOMPILED / UNRUN.
//! Real materializer -> Store -> Workspace/Host and recording fake inference.
//! Native enum selection is not a renderer capability or a model/device proof.
use locallore::{
    author_correction::*,
    contracts::*,
    engine::Engine,
    host::{Host, HostPlayConstructionV1, ProviderFactory},
    inference::*,
    inspection::sha256,
    play::{PlayContextPolicy, PlayProfile},
    story_authoring::*,
};
use locallore_storage::{Store, TurnPhase};
use serde_json::{json, Value};
use std::{
    path::PathBuf,
    sync::{
        atomic::{AtomicU64, AtomicUsize, Ordering},
        Arc, Mutex,
    },
    task::Poll,
};

const POLICY: &str = "grounded-prose-v2.8-authored-scene-frame-v2";
const MEMORY: &str = "locallore-play-v2.11-authored-scene-frame-v2";
const LITERAL: &str = "locallore-play-v2.12-literal-director-v1-authored-scene-frame-v2";
fn profile() -> PlayProfile {
    PlayProfile {
        id: "workspace-authored-scene-v2".into(),
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
#[derive(Clone, Copy)]
enum Arm {
    Memory,
    Literal,
}
impl Arm {
    fn native(self) -> HostPlayConstructionV1 {
        match self {
            Self::Memory => HostPlayConstructionV1::MemoryAuthoredSceneV2(
                PlayContextPolicy::StateRelevantMemoryV1,
            ),
            Self::Literal => HostPlayConstructionV1::PlayerLiteralAuthoredSceneV2,
        }
    }
    fn prompt(self) -> &'static str {
        match self {
            Self::Memory => MEMORY,
            Self::Literal => LITERAL,
        }
    }
    fn opposite(self) -> Self {
        match self {
            Self::Memory => Self::Literal,
            Self::Literal => Self::Memory,
        }
    }
}
fn seed() -> Seed {
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
        title: "Synthetic authored scene persistence".into(),
    };
    let seed = materialize(
        &origin,
        Scope {
            story: "authored-host-scene-v2".into(),
            branch: "main".into(),
        },
    )
    .unwrap();
    validate_origin(&seed).unwrap();
    seed
}
struct Fixture {
    root: PathBuf,
    scope: Scope,
    label: String,
}
impl Fixture {
    fn new() -> Self {
        static NEXT: AtomicU64 = AtomicU64::new(0);
        let time = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let root = std::env::temp_dir().join(format!(
            "authored-scene-host-v2-{time}-{}",
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&root).unwrap();
        let seed = seed();
        let origin = seed.initial_world.as_ref().unwrap();
        let label = origin.accepted.locations[usize::from(origin.accepted.player_location)]
            .name
            .clone();
        let fixture = Self {
            root,
            scope: seed.scope.clone(),
            label,
        };
        Store::open_application(&fixture.db())
            .unwrap()
            .create_story("Synthetic authored scene", seed)
            .unwrap();
        fixture
    }
    fn db(&self) -> PathBuf {
        self.root.join("synthetic.sqlite")
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
    fn seen(&self) -> Arc<Seen> {
        Arc::new(Seen {
            text: format!("You pause at {}.", self.label),
            factories: AtomicUsize::new(0),
            requests: Mutex::new(vec![]),
        })
    }
    // Intentionally retain these small owner-created databases, including failures.
}
struct Seen {
    text: String,
    factories: AtomicUsize,
    requests: Mutex<Vec<GenerationRequest>>,
}
impl Seen {
    fn factory(self: &Arc<Self>) -> ProviderFactory {
        let seen = self.clone();
        Arc::new(move || {
            seen.factories.fetch_add(1, Ordering::SeqCst);
            Box::new(Script(seen.clone()))
        })
    }
    fn requests(&self) -> Vec<GenerationRequest> {
        self.requests.lock().unwrap().clone()
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
            panic!("actual structured generation input required")
        };
        let response = match role.as_str() {
            "director" => json!({"commands":[{"op":"wait","ticks":1}]}),
            "narrator" => {
                for secret in [
                    "ASHGLASS-NPC-319",
                    "ASHGLASS-VALVE-701",
                    "ASHGLASS-RUMOR-622",
                    "PRIVATE_HOST_CORRECTION_V2",
                ] {
                    assert!(
                        !prompt.contains(secret),
                        "unrelated private input reached narrator: {secret}"
                    );
                }
                json!({"text":self.0.text,"event_ids":[request.revision+1],"speaker":"narrator"})
            }
            _ => panic!("unexpected role {role}"),
        };
        Poll::Ready(Ok(serde_json::to_vec(&response).unwrap()))
    }
}
fn call(host: &Host, command: Value) -> Value {
    host.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
}
fn ok(reply: Value) -> Value {
    assert_eq!(reply["status"], "ok", "{reply}");
    reply["data"].clone()
}
fn resume(host: &Host, scope: &Scope, head: u64) -> String {
    let data = ok(call(host, json!({"op":"resume","scope":scope})));
    assert_eq!(data["revision"], head);
    data["session"].as_str().unwrap().into()
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
    assert_eq!(actual.canonical_bytes(), before.canonical_bytes());
    assert_eq!(actual.canonical_records(), before.canonical_records());
    assert_eq!(
        actual.accepted_history_basis().unwrap(),
        before.accepted_history_basis().unwrap()
    );
}

#[test]
fn durable_both_native_selectors_prepare_without_append_commit_once_and_reopen_without_inference() {
    for arm in [Arm::Memory, Arm::Literal] {
        let fixture = Fixture::new();
        let host = fixture.host();
        let seen = fixture.seen();
        host.configure_fixture_provider_with_construction(profile(), seen.factory(), arm.native())
            .unwrap();
        let session = resume(&host, &fixture.scope, 0);
        let before = fixture.engine(&fixture.scope);
        assert_eq!(before.domain_version(), 1);
        let request = request(&before, "durable-v2");
        assert_eq!(ok(submit(&host, &session, &request))["phase"], "queued");
        assert_eq!(
            ok(operation(&host, &session, &request, "prepare"))["phase"],
            "ready"
        );
        unchanged(&fixture.engine(&fixture.scope), &before);
        let done = ok(operation(&host, &session, &request, "commit"));
        assert_eq!(done["phase"], "committed");
        let after = fixture.engine(&fixture.scope);
        assert_eq!(after.revision(), 1);
        assert_eq!(
            after.canonical_record_count(),
            before.canonical_record_count() + 1
        );
        let saved = Store::open_read_only(&fixture.db())
            .unwrap()
            .lookup_turn(&fixture.scope, &request.turn)
            .unwrap();
        assert_eq!(saved.phase, TurnPhase::Committed);
        let receipt = saved.receipt.unwrap();
        assert_eq!(done["receipt"], json!(receipt));
        assert!(!receipt.play().unwrap().fallback);
        assert_eq!(receipt.narration(), seen.text);
        assert_eq!(receipt.play().unwrap().prompt_version, arm.prompt());
        assert_eq!(receipt.play().unwrap().policy, POLICY);
        assert_eq!(receipt.play().unwrap().scene.as_ref().unwrap().version, 2);
        let commands = &receipt.proposal().commands;
        assert_eq!(commands, &[Command::Wait { ticks: 1 }]);
        let mut mechanical = before.clone();
        let mechanical_request = mechanical.request(
            &request.turn,
            Intent::Actions(vec![Command::Wait { ticks: 1 }]),
        );
        let approved = mechanical
            .preview(
                &mechanical_request,
                &Engine::proposal(&mechanical_request).unwrap(),
            )
            .unwrap();
        mechanical.commit_prepared(&approved).unwrap();
        assert_eq!(after.state(), mechanical.state());
        let actual = seen.requests();
        assert_eq!(actual.len(), 2);
        assert_eq!(
            actual[0].schema,
            if matches!(arm, Arm::Literal) {
                "locallore-director-literal-v1"
            } else {
                "locallore-director-v2"
            }
        );
        assert_eq!(seen.factories.load(Ordering::SeqCst), 1);
        unchanged(
            &Engine::replay_records(after.seed().clone(), after.canonical_records()).unwrap(),
            &after,
        );
        host.close_all();
        assert_eq!(host.live_counts(), (0, 0));
        drop(host);
        let reopened = fixture.host();
        let trap: ProviderFactory =
            Arc::new(|| panic!("durable exact retry must never construct inference"));
        reopened
            .configure_fixture_provider_with_construction(profile(), trap, arm.opposite().native())
            .unwrap();
        let session = resume(&reopened, &fixture.scope, 1);
        for reply in [
            operation(&reopened, &session, &request, "turn_status"),
            submit(&reopened, &session, &request),
            operation(&reopened, &session, &request, "prepare"),
            operation(&reopened, &session, &request, "commit"),
        ] {
            let value = ok(reply);
            assert_eq!(value["phase"], "committed");
            assert_eq!(value["receipt"], done["receipt"]);
        }
        unchanged(&fixture.engine(&fixture.scope), &after);
        assert_eq!(seen.requests().len(), 2);
        reopened.close_all();
        assert_eq!(reopened.live_counts(), (0, 0));
    }
}

#[test]
fn cancelled_authored_candidates_remain_noncanonical_and_terminal_after_host_reopen() {
    for arm in [Arm::Memory, Arm::Literal] {
        for prepare in [false, true] {
            let fixture = Fixture::new();
            let host = fixture.host();
            let seen = fixture.seen();
            host.configure_fixture_provider_with_construction(
                profile(),
                seen.factory(),
                arm.native(),
            )
            .unwrap();
            let session = resume(&host, &fixture.scope, 0);
            let before = fixture.engine(&fixture.scope);
            let request = request(&before, "cancel-v2");
            ok(submit(&host, &session, &request));
            if prepare {
                assert_eq!(
                    ok(operation(&host, &session, &request, "prepare"))["phase"],
                    "ready"
                );
            }
            assert_eq!(
                ok(operation(&host, &session, &request, "cancel"))["phase"],
                "cancelled"
            );
            for op in ["prepare", "commit"] {
                let terminal = ok(operation(&host, &session, &request, op));
                assert_eq!(terminal["phase"], "cancelled");
                assert!(terminal["receipt"].is_null());
            }
            unchanged(&fixture.engine(&fixture.scope), &before);
            assert_eq!(seen.requests().len(), if prepare { 2 } else { 0 });
            host.close_all();
            assert_eq!(host.live_counts(), (0, 0));
            drop(host);
            let reopened = fixture.host();
            let session = resume(&reopened, &fixture.scope, 0);
            assert_eq!(
                ok(operation(&reopened, &session, &request, "turn_status"))["phase"],
                "cancelled"
            );
            unchanged(&fixture.engine(&fixture.scope), &before);
            reopened.close_all();
            assert_eq!(reopened.live_counts(), (0, 0));
        }
    }
}

#[test]
fn competing_actual_host_commit_makes_prepared_scene_stale_without_a_second_canonical_append() {
    for arm in [Arm::Memory, Arm::Literal] {
        let fixture = Fixture::new();
        let host = fixture.host();
        let seen = fixture.seen();
        host.configure_fixture_provider_with_construction(profile(), seen.factory(), arm.native())
            .unwrap();
        let session = resume(&host, &fixture.scope, 0);
        let before = fixture.engine(&fixture.scope);
        let request = request(&before, "prepared-loser");
        ok(submit(&host, &session, &request));
        assert_eq!(
            ok(operation(&host, &session, &request, "prepare"))["phase"],
            "ready"
        );
        let winner = before.request(
            "actual-winner",
            Intent::Actions(vec![Command::Wait { ticks: 1 }]),
        );
        ok(submit(&host, &session, &winner));
        ok(operation(&host, &session, &winner, "prepare"));
        assert_eq!(
            ok(operation(&host, &session, &winner, "commit"))["phase"],
            "committed"
        );
        let expected = fixture.engine(&fixture.scope);
        let stale = ok(operation(&host, &session, &request, "commit"));
        assert_eq!(stale["phase"], "stale");
        assert!(stale["receipt"].is_null());
        unchanged(&fixture.engine(&fixture.scope), &expected);
        assert_eq!(
            expected.canonical_record_count(),
            before.canonical_record_count() + 1
        );
        assert_eq!(seen.requests().len(), 2);
        host.close_all();
        drop(host);
        let reopened = fixture.host();
        let session = resume(&reopened, &fixture.scope, 1);
        assert_eq!(
            ok(operation(&reopened, &session, &request, "turn_status"))["phase"],
            "stale"
        );
        unchanged(&fixture.engine(&fixture.scope), &expected);
        reopened.close_all();
        assert_eq!(reopened.live_counts(), (0, 0));
    }
}

#[test]
fn real_persisted_author_correction_enters_domain2_memory_scene_and_replays_without_losing_author_record(
) {
    let fixture = Fixture::new();
    let host = fixture.host();
    let session = resume(&host, &fixture.scope, 0);
    let parent = fixture.engine(&fixture.scope);
    let fact = parent
        .seed()
        .facts
        .keys()
        .find(|key| key.ends_with("-location-0"))
        .unwrap()
        .clone();
    let input = AuthorCorrectionInputV1 {
        version: 1,
        parent: fixture.scope.clone(),
        expected_parent_revision: 0,
        fork_revision: 0,
        child_branch: "corrected".into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: fact.clone(),
            expected_proposition: parent.seed().facts[&fact].proposition.clone(),
            replacement: "An untyped changed account of this place.".into(),
        },
        reason: "PRIVATE_HOST_CORRECTION_V2".into(),
    };
    let preparation = host
        .prepare_author_correction(&session, &input, &|| false)
        .unwrap();
    let outcome = host
        .apply_author_correction(&preparation, &|| false)
        .unwrap();
    let child = outcome.scope;
    let before = fixture.engine(&child);
    assert_eq!(before.domain_version(), 2);
    assert_eq!(before.canonical_record_count(), 1);
    unchanged(&fixture.engine(&fixture.scope), &parent);
    host.close_all();
    drop(host);
    let host = fixture.host();
    let seen = fixture.seen();
    host.configure_fixture_provider_with_construction(
        profile(),
        seen.factory(),
        Arm::Memory.native(),
    )
    .unwrap();
    let session = resume(&host, &child, before.revision());
    let request = request(&before, "domain2-host-memory");
    ok(submit(&host, &session, &request));
    assert_eq!(
        ok(operation(&host, &session, &request, "prepare"))["phase"],
        "ready"
    );
    unchanged(&fixture.engine(&child), &before);
    let done = ok(operation(&host, &session, &request, "commit"));
    assert_eq!(done["phase"], "committed");
    assert_eq!(done["receipt"]["play"]["policy"], POLICY);
    assert_eq!(done["receipt"]["play"]["fallback"], false);
    let after = fixture.engine(&child);
    assert_eq!(after.domain_version(), 2);
    assert_eq!(
        after.canonical_record_count(),
        before.canonical_record_count() + 1
    );
    unchanged(
        &Engine::replay_records(after.seed().clone(), after.canonical_records()).unwrap(),
        &after,
    );
    unchanged(&fixture.engine(&fixture.scope), &parent);
    host.close_all();
    drop(host);
    let reopened = fixture.host();
    let session = resume(&reopened, &child, after.revision());
    assert_eq!(
        ok(operation(&reopened, &session, &request, "turn_status"))["receipt"],
        done["receipt"]
    );
    unchanged(&fixture.engine(&child), &after);
    assert_eq!(seen.requests().len(), 2);
    reopened.close_all();
    assert_eq!(reopened.live_counts(), (0, 0));
}
