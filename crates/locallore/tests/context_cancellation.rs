use locallore::{
    context_compiler::{
        compile, compile_cancelled, Budget, CompileError, CompileRequest, Role, COMPILER_VERSION,
    },
    contracts::{Command, Intent, Seed},
    engine::Engine,
};
use std::cell::Cell;

fn fixture() -> Engine {
    let seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    let mut engine = Engine::new(seed).unwrap();
    for i in 0..128 {
        let request = engine.request(
            &format!("cancel-fixture-{i}"),
            Intent::Actions(vec![Command::Wait { ticks: 1 }]),
        );
        let proposal = Engine::proposal(&request).unwrap();
        let approved = engine.preview(&request, &proposal).unwrap();
        engine
            .commit(&request, &proposal, approved.narration())
            .unwrap();
    }
    engine
}
fn request(engine: &Engine) -> CompileRequest {
    CompileRequest {
        version: COMPILER_VERSION,
        scope: engine.scope().clone(),
        expected_head: engine.revision(),
        at_revision: None,
        observer: "player".into(),
        role: Role::Director,
        query: "return key".into(),
        referenced_ids: vec!["brass-key".into()],
        budget: Budget::default(),
    }
}

#[test]
fn cancellation_at_early_observation_candidate_and_final_checkpoints_returns_no_package() {
    let engine = fixture();
    let before = engine.canonical_bytes();
    let request = request(&engine);
    let calls = Cell::new(0usize);
    let complete = compile_cancelled(&engine, &request, &|| {
        calls.set(calls.get() + 1);
        false
    })
    .unwrap();
    let checkpoints = calls.get();
    assert!(
        checkpoints > 512,
        "checks must cover retained history and selection"
    );
    for boundary in [
        1,
        16,
        64,
        128,
        256,
        checkpoints / 2,
        checkpoints - 1,
        checkpoints,
    ] {
        calls.set(0);
        let stopped = compile_cancelled(&engine, &request, &|| {
            calls.set(calls.get() + 1);
            calls.get() >= boundary
        });
        assert_eq!(stopped, Err(CompileError::Cancelled), "boundary {boundary}");
        // The borrowed visitor also checks on return; at most one extra check
        // may confirm cancellation after a callback stops. No package escapes.
        assert!(calls.get() <= boundary + 1);
        assert_eq!(before, engine.canonical_bytes());
    }
    assert_eq!(complete, compile(&engine, &request).unwrap());
}

#[test]
fn cancellation_callback_panic_is_cancelled_and_the_next_compile_can_retry() {
    let engine = fixture();
    let request = request(&engine);
    let calls = Cell::new(0);
    let result = compile_cancelled(&engine, &request, &|| {
        calls.set(calls.get() + 1);
        if calls.get() == 128 {
            panic!("synthetic private cancel callback")
        }
        false
    });
    assert_eq!(result, Err(CompileError::Cancelled));
    assert!(compile(&engine, &request).is_ok());
}

#[test]
fn historical_and_private_actor_packages_keep_their_existing_boundaries_after_retry() {
    let engine = fixture();
    let before = engine.canonical_bytes();
    for (observer, revision) in [
        ("player", None),
        ("mira", None),
        ("sable", None),
        ("player", Some(32)),
    ] {
        let mut request = request(&engine);
        request.observer = observer.into();
        request.role = Role::Character;
        request.at_revision = revision;
        request.referenced_ids.clear();
        let expected = compile(&engine, &request).unwrap();
        assert_eq!(
            compile_cancelled(&engine, &request, &|| true),
            Err(CompileError::Cancelled)
        );
        let actual = compile_cancelled(&engine, &request, &|| false).unwrap();
        assert_eq!(expected, actual);
        assert_eq!(actual.revision, revision.unwrap_or(engine.revision()));
        assert_eq!(actual.observer, observer);
        assert_eq!(before, engine.canonical_bytes());
    }
}
