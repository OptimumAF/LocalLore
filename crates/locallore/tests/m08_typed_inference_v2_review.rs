//! Actual typed inference path, synthetic FakeProvider; frozen before production.
use locallore::{
    author_correction::*, contracts::*, engine::Engine, inference::*,
};
use std::task::Poll;

const A: &str = "SYNTHETIC_TYPED_OBSERVED_A";
const B: &str = "SYNTHETIC_TYPED_PRIVATE_WORLD_B";
const REASON: &str = "SYNTHETIC_TYPED_PRIVATE_AUTHOR_REASON";
const NPC: &str = "SYNTHETIC_NPC_NAMED_PLAYER_ONLY";

fn root(custom: bool) -> Engine {
    let mut seed: Seed = serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    if custom {
        seed.actors.insert("hero".into(), seed.actors["player"].clone());
        seed.player = "hero".into();
        for item in seed.items.values_mut() {
            if item.owner == "player" { item.owner = "hero".into(); }
        }
        seed.facts.insert("npc-only".into(), Fact { proposition: NPC.into(),
            discoverable_at: None, known_by: ["player".into()].into() });
    }
    let fact = seed.facts.get_mut("relic-location").unwrap();
    fact.proposition = A.into();
    fact.known_by = ["mira".into()].into();
    fact.discoverable_at = Some("quay".into());
    let mut engine = Engine::new(seed).unwrap();
    let request = engine.request("actual-discovery", Intent::Actions(vec![Command::Discover { fact: "relic-location".into() }]));
    let proposal = Engine::proposal(&request).unwrap();
    let approved = engine.preview(&request, &proposal).unwrap();
    engine.commit_prepared(&approved).unwrap();
    engine
}
fn child(parent: &Engine) -> Engine {
    let input = AuthorCorrectionInputV1 { version: 1, parent: parent.scope().clone(),
        expected_parent_revision: parent.revision(), fork_revision: parent.revision(), child_branch: "typed-child".into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition { fact: "relic-location".into(),
            expected_proposition: A.into(), replacement: B.into() }, reason: REASON.into() };
    let prepared = parent.prepare_author_correction(&input, &|| false).unwrap();
    parent.apply_author_correction(&prepared, &|| false).unwrap().engine
}
struct Recording {
    fake: FakeProvider,
    seen: Vec<GenerationRequest>,
    cancel_narrator: bool,
}
impl Recording {
    fn new(mode: FakeMode) -> Self { Self { fake: FakeProvider::new(mode), seen: vec![], cancel_narrator: false } }
}
impl InferenceProvider for Recording {
    fn poll(&mut self, request: &GenerationRequest, cancel: &Cancellation) -> Poll<Result<Vec<u8>, Error>> {
        self.seen.push(request.clone());
        if self.cancel_narrator && matches!(&request.input, Input::Narrator { .. }) { cancel.cancel(); }
        self.fake.poll(request, cancel)
    }
}
fn private_oracle(engine: &Engine) {
    assert_eq!(engine.effective_fact("relic-location").unwrap().proposition, B);
    for actor in [&engine.seed().player[..], "mira"] {
        let context = engine.character_context_v2(actor, engine.scope(), engine.revision()).unwrap();
        assert_eq!(context.facts["relic-location"].proposition, A);
        let json = serde_json::to_string(&context).unwrap();
        for hidden in [B, REASON, "truth_source", "stale"] { assert!(!json.contains(hidden)); }
    }
    assert!(!engine.character_context_v2("sable", engine.scope(), engine.revision()).unwrap().facts.contains_key("relic-location"));
}

#[test]
fn typed_give_wait_use_actual_actor_v2_context_and_exact_retry_without_provider() {
    for custom in [false, true] {
        let parent = root(custom);
        let parent_bytes = parent.canonical_bytes();
        let mut engine = child(&parent);
        let base = engine.clone();
        private_oracle(&engine);
        for (key, commands) in [("typed-give", vec![Command::Give { item: "potion".into(), to: "mira".into(), quantity: 1 }]),
            ("typed-wait", vec![Command::Wait { ticks: 1 }])] {
            let request = engine.request(key, Intent::Actions(commands));
            let expected_context = engine.character_context_v2(&engine.seed().player, engine.scope(), engine.revision()).unwrap();
            assert!(serde_json::to_vec(&expected_context).unwrap().len() <= 32_768);
            let old = engine.revision();
            let mut provider = Recording::new(FakeMode::Accepted);
            let receipt = execute(&mut engine, &request, &mut provider, &Cancellation::default(), Budget::default()).unwrap();
            assert_eq!(provider.seen.len(), 2);
            let director = &provider.seen[0];
            assert_eq!(director.scope, request.scope);
            assert_eq!(director.turn, request.turn);
            assert_eq!(director.revision, old);
            // Baseline compiles without the additive variant: current failure is
            // actual execute Version, not a missing-API compilation failure.
            assert_eq!(format!("{:?}", director.input), format!("DirectorV2 {{ request: {request:?}, context: {expected_context:?} }}"));
            let all = format!("{:?}", provider.seen);
            for hidden in [B, REASON, NPC] { assert!(!all.contains(hidden)); }
            assert!(matches!(&provider.seen[1].input, Input::Narrator { .. }));
            assert_eq!(receipt.request(), &request);
            assert_eq!(engine.revision(), old + receipt.events().len() as u64);
            assert!(matches!(engine.canonical_records().last().unwrap(), CanonicalRecord::PlayV2(_)));
            private_oracle(&engine);
            let records = engine.canonical_records().to_vec();
            let bytes = engine.canonical_bytes();
            let basis = engine.accepted_history_basis().unwrap();
            let cancelled = Cancellation::default(); cancelled.cancel();
            let mut retry = Recording::new(FakeMode::Failed);
            assert_eq!(execute(&mut engine, &request, &mut retry, &cancelled, Budget::default()).unwrap(), receipt);
            assert_eq!(retry.fake.calls, 0);
            assert!(retry.seen.is_empty());
            assert_eq!(engine.canonical_records(), records);
            assert_eq!(engine.canonical_bytes(), bytes);
            assert_eq!(engine.accepted_history_basis().unwrap(), basis);
        }
        assert_eq!(engine.state().items["potion"].owner, "mira");
        assert_eq!(parent.canonical_bytes(), parent_bytes);
        let encoded: Vec<_> = engine.canonical_records().iter().skip(base.canonical_record_count())
            .map(|record| serde_json::to_string(record).unwrap()).collect();
        let restored = base.restore_continuation(&encoded).unwrap();
        assert_eq!(restored.canonical_records(), engine.canonical_records());
        assert_eq!(restored.canonical_bytes(), engine.canonical_bytes());
        assert_eq!(restored.accepted_history_basis().unwrap(), engine.accepted_history_basis().unwrap());
    }
}

#[test]
fn rejected_failed_cancelled_and_late_narrator_cancel_leave_full_v2_canon_unchanged() {
    // FakeRejected changes the requested Wait into an invented ability. The
    // existing typed-intent agency guard rejects that before ability resolution.
    for (mode, expected) in [(FakeMode::Malformed, Error::Malformed), (FakeMode::Rejected, Error::Agency),
        (FakeMode::Failed, Error::Provider), (FakeMode::Cancelled, Error::Cancelled),
        (FakeMode::InventedNarration, Error::Narration)] {
        let mut engine = child(&root(false));
        let request = engine.request("not-accepted", Intent::Actions(vec![Command::Wait { ticks: 1 }]));
        let before = engine.clone();
        let mut provider = Recording::new(mode);
        assert_eq!(execute(&mut engine, &request, &mut provider, &Cancellation::default(), Budget::default()), Err(expected));
        assert_eq!(engine.canonical_records(), before.canonical_records());
        assert_eq!(engine.canonical_bytes(), before.canonical_bytes());
        assert_eq!(engine.accepted_history_basis().unwrap(), before.accepted_history_basis().unwrap());
    }
    let mut engine = child(&root(false));
    let before = engine.clone();
    let request = engine.request("cancel-narrator", Intent::Actions(vec![Command::Wait { ticks: 1 }]));
    let mut provider = Recording::new(FakeMode::Accepted); provider.cancel_narrator = true;
    assert_eq!(execute(&mut engine, &request, &mut provider, &Cancellation::default(), Budget::default()), Err(Error::Cancelled));
    assert_eq!(provider.seen.len(), 2);
    assert_eq!(engine.canonical_records(), before.canonical_records());
    assert_eq!(engine.canonical_bytes(), before.canonical_bytes());
    assert_eq!(engine.accepted_history_basis().unwrap(), before.accepted_history_basis().unwrap());
}

#[test]
fn legacy_director_context_and_canonical_receipt_stay_legacy() {
    let mut engine = root(false);
    assert_eq!(engine.domain_version(), 1);
    let request = engine.request("legacy-wait", Intent::Actions(vec![Command::Wait { ticks: 1 }]));
    let expected = engine.character_context(&engine.seed().player, engine.scope(), engine.revision()).unwrap();
    let mut provider = Recording::new(FakeMode::Accepted);
    execute(&mut engine, &request, &mut provider, &Cancellation::default(), Budget::default()).unwrap();
    assert_eq!(provider.seen.len(), 2);
    let Input::Director { request: actual, context } = &provider.seen[0].input else { panic!("legacy Director must be preserved") };
    assert_eq!(actual, &request);
    assert_eq!(serde_json::to_vec(context).unwrap(), serde_json::to_vec(&expected).unwrap());
    assert!(matches!(engine.canonical_records().last().unwrap(), CanonicalRecord::LegacyPlay(_)));
}
