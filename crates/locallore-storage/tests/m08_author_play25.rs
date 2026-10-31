//! Frozen shared Store/Core integration oracles. Synthetic provider only.
//! No SQL writer, forged Receipt, platform/IPC hook or actual model.
use locallore::{
    author_correction::*,
    contracts::*,
    engine::Engine,
    inference::*,
    play::{self, PlayProfile},
};
use locallore_storage::{ForkRequest, Store, TurnError, TurnPhase};
use serde_json::{json, Value};
use std::{
    collections::VecDeque,
    path::PathBuf,
    sync::atomic::{AtomicU64, Ordering},
    task::Poll,
};

const A: &str = "the tideglass was at the old quay";
const B: &str = "a golden marker stands beside the quay";
const C: &str = "a plain marker stands beside the quay";
const REASON: &str = "PRIVATE_AUTHOR_PLAY25_STORE_REASON";
static NEXT: AtomicU64 = AtomicU64::new(0);
struct Temp {
    path: PathBuf,
    parent: PathBuf,
}
impl Temp {
    fn new() -> Self {
        let parent = std::env::temp_dir().canonicalize().unwrap();
        let path = parent.join(format!(
            "locallore-m08-author-play25-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&path).unwrap();
        Self { path, parent }
    }
    fn open(&self) -> Store {
        Store::open(&self.path.join("synthetic.sqlite"), None).unwrap()
    }
}
impl Drop for Temp {
    fn drop(&mut self) {
        assert_eq!(self.path.parent(), Some(self.parent.as_path()));
        assert!(self
            .path
            .file_name()
            .unwrap()
            .to_str()
            .unwrap()
            .starts_with("locallore-m08-author-play25-"));
        std::fs::remove_dir_all(&self.path).unwrap();
    }
}
fn setup(temp: &Temp) -> (Store, Scope) {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    let fact = seed.facts.get_mut("relic-location").unwrap();
    fact.proposition = A.into();
    fact.discoverable_at = Some("quay".into());
    fact.known_by.insert("mira".into());
    let scope = seed.scope.clone();
    let mut store = temp.open();
    store.create_story("Synthetic author Play25", seed).unwrap();
    (store, scope)
}
fn typed(store: &mut Store, scope: &Scope, key: &str, commands: Vec<Command>) -> Receipt {
    let engine = store.resume(scope).unwrap().engine;
    let request = engine.request(key, Intent::Actions(commands));
    let proposal = Engine::proposal(&request).unwrap();
    let approved = engine.preview(&request, &proposal).unwrap();
    store.begin_turn(&request).unwrap();
    store.commit_prepared(&approved).unwrap()
}
fn author(
    store: &mut Store,
    root: &Scope,
    at: u64,
    replacement: &str,
) -> (AuthorCorrectionInputV1, Scope) {
    let input = AuthorCorrectionInputV1 {
        version: 1,
        parent: root.clone(),
        expected_parent_revision: store.resume(root).unwrap().engine.revision(),
        fork_revision: at,
        child_branch: "authored".into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(),
            expected_proposition: A.into(),
            replacement: replacement.into(),
        },
        reason: REASON.into(),
    };
    let plan = store.prepare_author_correction(&input, &|| false).unwrap();
    let outcome = store.apply_author_correction(&plan, &|| false).unwrap();
    assert!(outcome.created);
    assert_eq!(outcome.author_revision, at + 1);
    (input, outcome.scope)
}
fn profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-author-store-play25".into(),
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
#[derive(Default)]
struct Script {
    replies: VecDeque<Value>,
    seen: Vec<GenerationRequest>,
}
impl InferenceProvider for Script {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        _: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        self.seen.push(request.clone());
        Poll::Ready(
            self.replies
                .pop_front()
                .map(|v| serde_json::to_vec(&v).unwrap())
                .ok_or(Error::Provider),
        )
    }
}
fn generated(engine: &mut Engine, key: &str, discover: bool) -> (Request, Receipt, Script) {
    let next = engine.revision() + 1;
    let request = engine.request(
        key,
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: if discover {
                "I discover relic-location."
            } else {
                "I wait for one tide tick."
            }
            .into(),
        },
    );
    let command = if discover {
        json!({"op":"discover","fact":"relic-location"})
    } else {
        json!({"op":"wait","ticks":1})
    };
    let prose = if discover {
        "You notice a golden marker beside the quay."
    } else {
        "You pause as a tide tick passes."
    };
    let mut provider = Script {
        replies: [
            json!({"commands":[command]}),
            json!({"text":prose,"event_ids":[next],"speaker":"narrator"}),
        ]
        .into(),
        ..Script::default()
    };
    let receipt = play::execute(
        engine,
        &request,
        &mut provider,
        &Cancellation::default(),
        &profile(),
    )
    .unwrap();
    assert_eq!(provider.seen.len(), 2);
    assert_eq!(
        receipt.play().unwrap().prompt_version,
        "locallore-play-v2.5"
    );
    assert_eq!(
        receipt.play().unwrap().policy,
        "grounded-prose-v2.5-whole-evidence-words-v1"
    );
    assert!(!receipt.play().unwrap().fallback);
    (request, receipt, provider)
}
fn known(engine: &Engine, observer: &str) -> String {
    engine
        .observed_facts(observer, engine.scope(), engine.revision())
        .unwrap()["relic-location"]
        .proposition
        .clone()
}

#[test]
fn actual_author_generated_discovery_store_commit_reopen_and_retry_preserve_full_canon_and_observers(
) {
    let temp = Temp::new();
    let (mut store, root) = setup(&temp);
    let retained = typed(
        &mut store,
        &root,
        "retained-gift",
        vec![Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 1,
        }],
    );
    let sibling = store
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
    typed(
        &mut store,
        &sibling,
        "sibling-suffix",
        vec![Command::Say {
            text: "EXCLUDED_SIBLING_PLAY25".into(),
            audience: ["mira".into()].into(),
        }],
    );
    typed(
        &mut store,
        &root,
        "parent-future",
        vec![Command::Say {
            text: "EXCLUDED_PARENT_FUTURE_PLAY25".into(),
            audience: ["mira".into()].into(),
        }],
    );
    let parent_before = store.resume(&root).unwrap().engine;
    let sibling_before = store.resume(&sibling).unwrap().engine;
    let (input, child) = author(&mut store, &root, 1, B);
    let before = store.resume(&child).unwrap().engine;
    assert_eq!(before.domain_version(), 2);
    assert_eq!(before.revision(), 2);
    assert_eq!(known(&before, "player"), A);
    assert_eq!(known(&before, "mira"), A);
    assert_eq!(before.receipts(), &[retained]);
    let request = before.request(
        "current-discovery",
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: "I discover relic-location.".into(),
        },
    );
    assert_eq!(store.begin_turn(&request).unwrap().phase, TurnPhase::Draft);
    let mut candidate_engine = store.resume(&child).unwrap().engine;
    let (actual_request, prepared, provider) =
        generated(&mut candidate_engine, "current-discovery", true);
    assert_eq!(actual_request, request);
    assert_eq!(
        store.resume(&child).unwrap().engine.canonical_bytes(),
        before.canonical_bytes(),
        "generation is not durable canonical acceptance"
    );
    let narrator = match &provider.seen[1].input {
        Input::Structured { role, prompt, .. } => {
            assert_eq!(role, "narrator");
            prompt
        }
        _ => panic!("actual structured narrator required"),
    };
    assert!(narrator.contains(B));
    assert!(!narrator.contains(A));
    assert!(!narrator.contains(REASON));
    let committed = store.commit_prepared(&prepared).unwrap();
    assert_eq!(
        serde_json::to_vec(&committed).unwrap(),
        serde_json::to_vec(&prepared).unwrap()
    );
    let actual = store.resume(&child).unwrap().engine;
    assert_eq!(
        actual.canonical_records(),
        candidate_engine.canonical_records()
    );
    assert_eq!(
        actual.accepted_history_basis().unwrap(),
        candidate_engine.accepted_history_basis().unwrap()
    );
    assert_eq!(actual.completed_boundaries(), vec![0, 1, 2, 3]);
    assert_eq!(actual.canonical_record_count(), 3);
    assert_eq!(actual.revision(), 3);
    assert_eq!(known(&actual, "player"), B);
    assert_eq!(known(&actual, "mira"), A);
    let views = actual
        .actor_receipts_v2("player", actual.scope(), actual.revision())
        .unwrap();
    assert_eq!(
        views.last().unwrap().events[0]
            .discovery
            .as_ref()
            .unwrap()
            .proposition,
        B
    );
    assert_eq!(actual.receipts()[0].request().scope, root);
    let public = serde_json::to_string(&views).unwrap();
    for excluded in [
        REASON,
        "EXCLUDED_PARENT_FUTURE_PLAY25",
        "EXCLUDED_SIBLING_PLAY25",
        "truth_source",
    ] {
        assert!(!public.contains(excluded));
    }
    assert_eq!(
        store.resume(&root).unwrap().engine.canonical_bytes(),
        parent_before.canonical_bytes()
    );
    assert_eq!(
        store.resume(&sibling).unwrap().engine.canonical_bytes(),
        sibling_before.canonical_bytes()
    );
    let canonical = actual.canonical_bytes();
    let basis = actual.accepted_history_basis().unwrap();
    drop(store);
    let mut reopened = temp.open();
    let mut resumed = reopened.resume(&child).unwrap().engine;
    assert_eq!(resumed.canonical_bytes(), canonical);
    assert_eq!(resumed.canonical_records(), actual.canonical_records());
    assert_eq!(resumed.accepted_history_basis().unwrap(), basis);
    assert_eq!(known(&resumed, "player"), B);
    assert_eq!(known(&resumed, "mira"), A);
    let saved = reopened.lookup_turn(&child, "current-discovery").unwrap();
    assert_eq!(saved.phase, TurnPhase::Committed);
    assert_eq!(saved.request, request);
    assert_eq!(saved.receipt, Some(committed.clone()));
    let lookup_author = reopened
        .lookup_author_correction(&input, &|| false)
        .unwrap()
        .unwrap();
    assert_eq!(lookup_author.scope, child);
    assert_eq!(lookup_author.author_revision, 2);
    assert_eq!(lookup_author.head_revision, 3);
    assert_eq!(
        reopened.begin_turn(&request).unwrap().receipt,
        Some(committed.clone())
    );
    let mut no_roles = Script::default();
    let cancelled = Cancellation::default();
    cancelled.cancel();
    let mut invalid_profile = profile();
    invalid_profile.context_tokens = 0;
    assert_eq!(
        play::execute(
            &mut resumed,
            &request,
            &mut no_roles,
            &cancelled,
            &invalid_profile
        )
        .unwrap(),
        committed
    );
    assert!(no_roles.seen.is_empty());
    assert_eq!(reopened.commit_prepared(&prepared).unwrap(), committed);
    let late = reopened.cancel_turn(&request).unwrap();
    assert_eq!(late.phase, TurnPhase::Committed);
    assert_eq!(late.receipt, Some(committed));
    assert_eq!(
        reopened.resume(&child).unwrap().engine.canonical_bytes(),
        canonical
    );
    let mut mismatch = request.clone();
    if let Intent::FreeText { text, .. } = &mut mismatch.intent {
        text.push_str(" now");
    }
    assert!(matches!(
        reopened.begin_turn(&mismatch),
        Err(TurnError::RetryMismatch)
    ));
}

#[test]
fn actual_cancelled_draft_never_commits_prepared_play25_and_survives_reopen() {
    let temp = Temp::new();
    let (mut store, root) = setup(&temp);
    let (_, child) = author(&mut store, &root, 0, B);
    let before = store.resume(&child).unwrap().engine;
    let request = before.request(
        "cancelled-current",
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: "I wait for one tide tick.".into(),
        },
    );
    store.begin_turn(&request).unwrap();
    let mut candidate = before.clone();
    let (_, prepared, _) = generated(&mut candidate, "cancelled-current", false);
    assert_eq!(
        store.cancel_turn(&request).unwrap().phase,
        TurnPhase::Cancelled
    );
    assert!(matches!(
        store.commit_prepared(&prepared),
        Err(TurnError::Terminal)
    ));
    assert_eq!(
        store.resume(&child).unwrap().engine.canonical_bytes(),
        before.canonical_bytes()
    );
    drop(store);
    let mut reopened = temp.open();
    let saved = reopened.lookup_turn(&child, &request.turn).unwrap();
    assert_eq!(saved.phase, TurnPhase::Cancelled);
    assert!(saved.receipt.is_none());
    let actual = reopened.resume(&child).unwrap().engine;
    assert_eq!(actual.canonical_records(), before.canonical_records());
    assert_eq!(actual.revision(), 1);
    assert_eq!(known(&actual, "player"), A);
    assert_eq!(known(&actual, "mira"), A);
}

#[test]
fn same_scope_head_mechanics_different_source_reject_bound_commit_and_revalidate_unbound_prose() {
    let left = Temp::new();
    let right = Temp::new();
    let (mut b_store, b_root) = setup(&left);
    let (mut c_store, c_root) = setup(&right);
    let (_, b_scope) = author(&mut b_store, &b_root, 0, B);
    let (_, c_scope) = author(&mut c_store, &c_root, 0, C);
    assert_eq!(b_scope, c_scope);
    let b = b_store.resume(&b_scope).unwrap().engine;
    let c = c_store.resume(&c_scope).unwrap().engine;
    assert_eq!(b.revision(), c.revision());
    assert_eq!(b.state(), c.state());
    let b_basis = b.accepted_history_basis().unwrap();
    assert_ne!(b_basis, c.accepted_history_basis().unwrap());
    let mut candidate = b.clone();
    let (request, prepared, _) = generated(&mut candidate, "cross-source", true);
    assert_eq!(
        c_store.begin_turn(&request).unwrap().phase,
        TurnPhase::Draft
    );
    assert!(matches!(
        c_store.commit_prepared_bound(&prepared, &b_basis),
        Err(TurnError::Stale)
    ));
    assert_eq!(
        c_store.resume(&c_scope).unwrap().engine.canonical_bytes(),
        c.canonical_bytes()
    );
    assert_eq!(
        c_store.lookup_turn(&c_scope, &request.turn).unwrap().phase,
        TurnPhase::Draft
    );
    // A real B-generated candidate, not forged JSON: revalidate against C's
    // actual new discovery. Its guarded "golden" prose is no longer supported.
    assert!(matches!(
        c_store.commit_prepared(&prepared),
        Err(TurnError::Engine(Error::Narration))
    ));
    assert_eq!(
        c_store.resume(&c_scope).unwrap().engine.canonical_records(),
        c.canonical_records()
    );
    assert_eq!(
        c_store.lookup_turn(&c_scope, &request.turn).unwrap().phase,
        TurnPhase::Draft
    );
    assert_eq!(
        b_store.resume(&b_scope).unwrap().engine.canonical_bytes(),
        b.canonical_bytes()
    );
}
