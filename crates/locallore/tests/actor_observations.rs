use locallore::{contracts::*, engine::Engine};
use std::cell::Cell;

fn engine() -> Engine {
    Engine::new(serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap())
        .unwrap()
}
fn commit(engine: &mut Engine, turn: &str, command: Command) {
    let request = engine.request(turn, Intent::Actions(vec![command]));
    let proposal = Engine::proposal(&request).unwrap();
    let receipt = engine.preview(&request, &proposal).unwrap();
    engine
        .commit(&request, &proposal, receipt.narration())
        .unwrap();
}
fn observations(engine: &Engine, actor: &str, after: u64, through: u64) -> Vec<AcceptedEvent> {
    let mut output = Vec::new();
    engine
        .visit_actor_observations(
            actor,
            engine.scope(),
            engine.revision(),
            after,
            through,
            &|| false,
            &mut |event| {
                output.push(event.clone());
                true
            },
        )
        .unwrap();
    output
}

#[test]
fn borrowed_port_matches_existing_context_and_fork_lineage_without_mutation() {
    let mut parent = engine();
    commit(
        &mut parent,
        "gift",
        Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 1,
        },
    );
    commit(&mut parent, "later", Command::Wait { ticks: 1 });
    let mut child = parent.fork("child", 1).unwrap();
    commit(&mut child, "child-wait", Command::Wait { ticks: 2 });
    for current in [&parent, &child] {
        let before = current.canonical_bytes();
        let receipts = current.receipts().to_vec();
        for actor in ["player", "mira", "sable"] {
            assert_eq!(
                observations(current, actor, 0, current.revision()),
                current
                    .character_context(actor, current.scope(), current.revision())
                    .unwrap()
                    .observations
            );
        }
        assert_eq!(before, current.canonical_bytes());
        assert_eq!(receipts, current.receipts());
    }
    assert_eq!(observations(&child, "mira", 0, child.revision()).len(), 1);
    assert!(observations(&child, "sable", 0, child.revision()).is_empty());
}

#[test]
fn invalid_binding_never_reaches_callback_and_ranges_are_exact() {
    let mut current = engine();
    for index in 0..3 {
        commit(
            &mut current,
            &format!("wait-{index}"),
            Command::Wait { ticks: 1 },
        );
    }
    let mut other = current.scope().clone();
    other.story = "other".into();
    for (actor, scope, revision, after, through, error) in [
        ("player", &other, 3, 0, 3, Error::Scope),
        ("player", current.scope(), 2, 0, 2, Error::Stale),
        ("missing", current.scope(), 3, 0, 3, Error::UnknownReference),
        ("player", current.scope(), 3, 2, 1, Error::Rule),
        ("player", current.scope(), 3, 0, 4, Error::Rule),
    ] {
        let calls = Cell::new(0);
        assert_eq!(
            current.visit_actor_observations(
                actor,
                scope,
                revision,
                after,
                through,
                &|| false,
                &mut |_| {
                    calls.set(calls.get() + 1);
                    true
                }
            ),
            Err(error)
        );
        assert_eq!(calls.get(), 0);
    }
    assert_eq!(
        observations(&current, "player", 1, 2)
            .iter()
            .map(AcceptedEvent::sequence)
            .collect::<Vec<_>>(),
        [2]
    );
    assert!(observations(&current, "player", 2, 2).is_empty());
}

#[test]
fn early_stop_is_normal_and_cancellation_is_bounded_even_for_hidden_history() {
    let mut current = engine();
    for index in 0..100 {
        commit(
            &mut current,
            &format!("wait-{index}"),
            Command::Wait { ticks: 1 },
        );
    }
    let mut calls = 0;
    current
        .visit_actor_observations(
            "player",
            current.scope(),
            current.revision(),
            0,
            current.revision(),
            &|| false,
            &mut |_| {
                calls += 1;
                false
            },
        )
        .unwrap();
    assert_eq!(calls, 1);
    let checks = Cell::new(0);
    let mut visible = 0;
    assert_eq!(
        current.visit_actor_observations(
            "sable",
            current.scope(),
            current.revision(),
            0,
            current.revision(),
            &|| {
                checks.set(checks.get() + 1);
                checks.get() == 3
            },
            &mut |_| {
                visible += 1;
                true
            }
        ),
        Err(Error::Cancelled)
    );
    assert_eq!(checks.get(), 3);
    assert_eq!(visible, 0);
    assert_eq!(
        current.visit_actor_observations(
            "player",
            current.scope(),
            current.revision(),
            0,
            current.revision(),
            &|| true,
            &mut |_| panic!("cancelled before callback")
        ),
        Err(Error::Cancelled)
    );
}
