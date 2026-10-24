//! Native Host policy plumbing. Synthetic providers, no model or durability claim.
#![cfg(feature = "host")]

use locallore::{
    context_compiler::ContextPolicy,
    contracts::*,
    engine::{AcceptedHistoryBasis, Engine},
    host::{Host, Persistence, ProviderFactory, SavedTurn, WorkspaceSummary},
    inference::*,
    play::PlayProfile,
};
use serde_json::{json, Value};
use std::{
    collections::BTreeMap,
    sync::{
        atomic::{AtomicBool, Ordering},
        mpsc, Arc, Mutex,
    },
    task::Poll,
    time::Duration,
};

fn profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-host-policy".into(),
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
fn call(host: &Host, command: Value) -> Value {
    host.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
}
fn session(host: &Host) -> (String, Scope) {
    let reply = call(host, json!({"op":"create","seed":"lantern-quay-v1"}));
    assert_eq!(reply["status"], "ok", "{reply}");
    (
        reply["data"]["session"].as_str().unwrap().into(),
        serde_json::from_value(reply["data"]["scope"].clone()).unwrap(),
    )
}
fn request(scope: &Scope, turn: &str, head: u64) -> Request {
    Request {
        version: 1,
        scope: scope.clone(),
        turn: turn.into(),
        expected_revision: head,
        intent: Intent::FreeText {
            kind: PlayInputKind::Action,
            text: "I wait for one tide tick.".into(),
        },
    }
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

#[derive(Clone, Default)]
struct Seen(Arc<Mutex<Vec<GenerationRequest>>>);
impl Seen {
    fn requests(&self) -> Vec<GenerationRequest> {
        self.0.lock().unwrap().clone()
    }
    fn factory(&self) -> ProviderFactory {
        let seen = self.clone();
        Arc::new(move || Box::new(Script { seen: seen.clone() }))
    }
}
struct Script {
    seen: Seen,
}
impl InferenceProvider for Script {
    fn poll(&mut self, r: &GenerationRequest, _: &Cancellation) -> Poll<Result<Vec<u8>, Error>> {
        self.seen.0.lock().unwrap().push(r.clone());
        let Input::Structured { role, .. } = &r.input else {
            panic!("actual current structured role required")
        };
        Poll::Ready(Ok(serde_json::to_vec(&match role.as_str() {
            "director" => json!({"commands":[{"op":"wait","ticks":1}]}),
            "narrator" => json!({"text":"You pause as a tide tick passes.","event_ids":[r.revision + 1],"speaker":"narrator"}),
            other => panic!("unexpected role {other}"),
        }).unwrap()))
    }
}
fn prompts(seen: &Seen) -> (String, String) {
    let requests = seen.requests();
    assert_eq!(
        requests.len(),
        2,
        "one actual director and one actual narrator"
    );
    let prompt = |index: usize, expected: &str| match &requests[index].input {
        Input::Structured { role, prompt, .. } => {
            assert_eq!(role, expected);
            prompt.clone()
        }
        _ => panic!("structured role required"),
    };
    (prompt(0, "director"), prompt(1, "narrator"))
}
fn assert_record(reply: &Value, policy: ContextPolicy) {
    assert_eq!(reply["status"], "ok", "{reply}");
    let receipt: Receipt = serde_json::from_value(reply["data"]["receipt"].clone()).unwrap();
    let record = receipt.play().unwrap();
    assert_eq!(record.prompt_version, "locallore-play-v2.5");
    assert_eq!(record.policy, "grounded-prose-v2.2");
    assert_eq!(record.context_policy, Some(policy));
    assert_eq!(record.context.as_ref().unwrap().version, 2);
    assert_eq!(record.context.as_ref().unwrap().compiler_version, 2);
}
fn assert_prompt_policy(seen: &Seen, policy: ContextPolicy) {
    let (director, narrator) = prompts(seen);
    assert!(director.contains("\"compiler_version\":2"));
    assert_eq!(
        director.contains("transcript_unit"),
        policy == ContextPolicy::StateRecentTranscriptV1
    );
    for excluded in [
        "PUBLIC_OLD_HISTORY",
        "SECRET-TIDE-731",
        "optional_records",
        "transcript_unit",
        "player_text",
    ] {
        assert!(!narrator.contains(excluded), "narrator contains {excluded}");
    }
}

fn history_engine() -> Engine {
    let seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    let mut engine = Engine::new(seed).unwrap();
    for index in 0..12 {
        let r = engine.request(
            &format!("history-{index}"),
            Intent::Actions(vec![Command::Say {
                text: format!("PUBLIC_OLD_HISTORY_{index}"),
                audience: ["mira".into()].into(),
            }]),
        );
        let proposal = Engine::proposal(&r).unwrap();
        let approved = engine.preview(&r, &proposal).unwrap();
        engine.commit_prepared(&approved).unwrap();
    }
    engine
}

// Test-only, read-only canonical fixture. The actual Engine creates every accepted
// history record. This adapter admits only temporary drafts; it cannot persist a
// receipt. The actual default Persistence::generation_snapshot must do the read.
struct ReadFixture {
    engine: Engine,
    drafts: BTreeMap<String, Request>,
}
impl ReadFixture {
    fn verify(&self, basis: &AcceptedHistoryBasis) -> Result<(), String> {
        if self
            .engine
            .matches_accepted_history(basis)
            .map_err(|e| e.to_string())?
        {
            Ok(())
        } else {
            Err("Stale".into())
        }
    }
}
impl Persistence for ReadFixture {
    fn location(&self) -> &str {
        "synthetic-read-only-fixture"
    }
    fn list(&mut self) -> Result<Vec<WorkspaceSummary>, String> {
        Ok(vec![])
    }
    fn create(&mut self) -> Result<Engine, String> {
        Ok(self.engine.clone())
    }
    fn resume(&mut self, scope: &Scope) -> Result<Engine, String> {
        if scope != self.engine.scope() {
            return Err("Scope".into());
        }
        Ok(self.engine.clone())
    }
    fn begin_bound(
        &mut self,
        r: &Request,
        basis: &AcceptedHistoryBasis,
    ) -> Result<SavedTurn, String> {
        self.verify(basis)?;
        self.engine.preflight(r).map_err(|e| e.to_string())?;
        if r.expected_revision != self.engine.revision() {
            return Err("Stale".into());
        }
        self.begin(r)
    }
    fn status_bound(
        &mut self,
        r: &Request,
        basis: &AcceptedHistoryBasis,
    ) -> Result<SavedTurn, String> {
        self.verify(basis)?;
        let saved = self.status(&r.scope, &r.turn)?;
        if saved.request != *r {
            return Err("RetryMismatch".into());
        }
        Ok(saved)
    }
    fn begin(&mut self, r: &Request) -> Result<SavedTurn, String> {
        if let Some(old) = self.drafts.get(&r.turn) {
            if old != r {
                return Err("RetryMismatch".into());
            }
        } else {
            self.drafts.insert(r.turn.clone(), r.clone());
        }
        self.status(&r.scope, &r.turn)
    }
    fn status(&mut self, scope: &Scope, turn: &str) -> Result<SavedTurn, String> {
        if scope != self.engine.scope() {
            return Err("Scope".into());
        }
        Ok(SavedTurn {
            request: self.drafts.get(turn).ok_or("UnknownTurn")?.clone(),
            phase: "draft".into(),
            receipt: None,
        })
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
}

#[test]
fn both_policies_use_actual_host_default_native_snapshot_and_current_record() {
    for policy in [
        ContextPolicy::StateRecentTranscriptV1,
        ContextPolicy::StateRelevantMemoryV1,
    ] {
        let basis = history_engine();
        let before = basis.canonical_bytes();
        let host = Host::with_persistence(
            false,
            Box::new(ReadFixture {
                engine: basis,
                drafts: BTreeMap::new(),
            }),
        );
        let seen = Seen::default();
        host.configure_fixture_provider_with_policy(profile(), seen.factory(), policy)
            .unwrap();
        let (session, scope) = session(&host);
        let r = request(&scope, "policy", 12);
        assert_eq!(submit(&host, &session, &r)["data"]["phase"], "queued");
        let ready = operation(&host, &session, &r, "prepare");
        assert_eq!(ready["data"]["phase"], "ready", "{ready}");
        assert_record(&ready, policy);
        assert_prompt_policy(&seen, policy);
        // Default native port returns coherent actual history; prepare never writes it.
        let snapshot = host
            .generation_snapshot(&session, &scope, 12, &|| false)
            .unwrap();
        assert_eq!(snapshot.engine.canonical_bytes(), before);
        assert!(matches!(
            snapshot.coverage,
            locallore::memory_coverage::CoverageRead::RawFallback(
                locallore::memory_coverage::FallbackReason::Missing
            )
        ));
        assert_eq!(
            call(&host, json!({"op":"model_status"}))["data"]["real_model"],
            false
        );
    }
}

#[test]
fn legacy_native_configuration_defaults_to_relevant_and_preserves_provenance() {
    // The local-owner arm checks its established metadata only; this is STILL
    // the same synthetic provider, never evidence that a real model ran.
    for native_owner in [false, true] {
        let host = Host::new(false);
        let seen = Seen::default();
        if native_owner {
            host.configure_local_provider(profile(), seen.factory())
                .unwrap();
        } else {
            host.configure_fixture_provider(profile(), seen.factory())
                .unwrap();
        }
        let (session, scope) = session(&host);
        let r = request(&scope, "default-policy", 0);
        assert_eq!(submit(&host, &session, &r)["data"]["phase"], "queued");
        let ready = operation(&host, &session, &r, "prepare");
        assert_eq!(ready["data"]["phase"], "ready", "{ready}");
        assert_record(&ready, ContextPolicy::StateRelevantMemoryV1);
        assert_prompt_policy(&seen, ContextPolicy::StateRelevantMemoryV1);
        assert_eq!(
            call(&host, json!({"op":"model_status"}))["data"]["real_model"],
            native_owner
        );
    }
}

#[test]
fn exact_committed_retry_uses_zero_roles_after_policy_change_and_json_cannot_set_policy() {
    let host = Host::new(false);
    let seen = Seen::default();
    host.configure_fixture_provider_with_policy(
        profile(),
        seen.factory(),
        ContextPolicy::StateRecentTranscriptV1,
    )
    .unwrap();
    let (session, scope) = session(&host);
    let r = request(&scope, "retry", 0);
    assert_eq!(submit(&host, &session, &r)["data"]["phase"], "queued");
    assert_eq!(
        operation(&host, &session, &r, "prepare")["data"]["phase"],
        "ready"
    );
    let committed = operation(&host, &session, &r, "commit");
    assert_eq!(committed["data"]["phase"], "committed", "{committed}");
    assert_record(&committed, ContextPolicy::StateRecentTranscriptV1);
    let future = Seen::default();
    host.configure_fixture_provider_with_policy(
        profile(),
        future.factory(),
        ContextPolicy::StateRelevantMemoryV1,
    )
    .unwrap();
    assert_eq!(submit(&host, &session, &r), committed);
    assert_eq!(operation(&host, &session, &r, "prepare"), committed);
    assert_eq!(operation(&host, &session, &r, "commit"), committed);
    assert_eq!(seen.requests().len(), 2);
    assert!(future.requests().is_empty());
    assert_eq!(
        call(
            &host,
            json!({"op":"configure_fixture_provider_with_policy","policy":"state_recent_transcript_v1"})
        )["error"],
        "Malformed"
    );
    assert_eq!(
        call(
            &host,
            json!({"op":"submit","session":session,"request":r,"mode":"accepted","context_policy":"state_recent_transcript_v1"})
        )["error"],
        "Malformed"
    );
}

struct Held {
    script: Script,
    release: Arc<AtomicBool>,
    entered: Option<mpsc::Sender<()>>,
}
impl InferenceProvider for Held {
    fn poll(
        &mut self,
        r: &GenerationRequest,
        cancel: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        if let Some(sender) = self.entered.take() {
            let _ = sender.send(());
        }
        if !self.release.load(Ordering::SeqCst) {
            return Poll::Pending;
        }
        self.script.poll(r, cancel)
    }
}
struct Release(Arc<AtomicBool>);
impl Drop for Release {
    fn drop(&mut self) {
        self.0.store(true, Ordering::SeqCst);
    }
}

#[test]
fn reconfiguration_during_actual_held_work_does_not_relabel_its_policy_or_provider() {
    let host = Arc::new(Host::new(false));
    let seen = Seen::default();
    let release = Arc::new(AtomicBool::new(false));
    let cleanup = Release(release.clone());
    let (sender, receiver) = mpsc::channel();
    let factory: ProviderFactory = {
        let seen = seen.clone();
        let release = release.clone();
        Arc::new(move || {
            Box::new(Held {
                script: Script { seen: seen.clone() },
                release: release.clone(),
                entered: Some(sender.clone()),
            })
        })
    };
    host.configure_fixture_provider_with_policy(
        profile(),
        factory,
        ContextPolicy::StateRecentTranscriptV1,
    )
    .unwrap();
    let (session, scope) = session(&host);
    let first = request(&scope, "held", 0);
    assert_eq!(submit(&host, &session, &first)["data"]["phase"], "queued");
    let worker = {
        let host = host.clone();
        let session = session.clone();
        let first = first.clone();
        std::thread::spawn(move || operation(&host, &session, &first, "prepare"))
    };
    receiver
        .recv_timeout(Duration::from_secs(2))
        .expect("actual provider must be polled");
    let future = Seen::default();
    host.configure_fixture_provider_with_policy(
        profile(),
        future.factory(),
        ContextPolicy::StateRelevantMemoryV1,
    )
    .unwrap();
    assert!(seen.requests().is_empty());
    assert!(future.requests().is_empty());
    drop(cleanup);
    let ready = worker.join().unwrap();
    assert_eq!(ready["data"]["phase"], "ready", "{ready}");
    assert_record(&ready, ContextPolicy::StateRecentTranscriptV1);
    assert_eq!(seen.requests().len(), 2);
    assert!(future.requests().is_empty());
    let committed = operation(&host, &session, &first, "commit");
    assert_eq!(committed["data"]["phase"], "committed", "{committed}");
    assert_record(&committed, ContextPolicy::StateRecentTranscriptV1);
    let next = request(&scope, "future", 1);
    assert_eq!(submit(&host, &session, &next)["data"]["phase"], "queued");
    let next_ready = operation(&host, &session, &next, "prepare");
    assert_eq!(next_ready["data"]["phase"], "ready", "{next_ready}");
    assert_record(&next_ready, ContextPolicy::StateRelevantMemoryV1);
    assert_eq!(future.requests().len(), 2);
    assert_eq!(seen.requests().len(), 2);
}
