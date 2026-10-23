pub use locallore::{contracts, engine};
#[path = "../src/intent_guard.rs"]
mod intent_guard;
use contracts::*;
use engine::Engine;
use intent_guard::*;

fn seed() -> Seed {
    serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap()
}
fn engine() -> Engine {
    Engine::new(seed()).unwrap()
}
fn proposal(engine: &Engine, text: &str, commands: Vec<Command>) -> (Request, Proposal) {
    let request = engine.request(
        "guard",
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: text.into(),
        },
    );
    let proposal = Proposal {
        version: VERSION,
        scope: request.scope.clone(),
        turn: request.turn.clone(),
        expected_revision: request.expected_revision,
        commands,
    };
    (request, proposal)
}

#[test]
fn explicit_gift_cannot_be_substituted_or_extended_with_other_valid_effects() {
    let mut s = seed();
    s.actors.get_mut("oren").unwrap().location = "quay".into();
    let e = Engine::new(s).unwrap();
    let expected = Command::Give {
        item: "potion".into(),
        to: "mira".into(),
        quantity: 1,
    };
    assert_eq!(
        compile_action(&e, "I give my last potion to Mira."),
        Ok(expected.clone())
    );
    for commands in [
        vec![Command::Wait { ticks: 1 }],
        vec![Command::Consume {
            item: "potion".into(),
        }],
        vec![Command::Give {
            item: "potion".into(),
            to: "oren".into(),
            quantity: 1,
        }],
        vec![Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 2,
        }],
        vec![expected.clone(), Command::Wait { ticks: 1 }],
    ] {
        let (request, proposal) = proposal(&e, "I give my last potion to Mira.", commands);
        assert_eq!(validate_action(&e, &request, &proposal), Err(Error::Agency));
    }
    let (request, proposal) = proposal(&e, "I give my last potion to Mira.", vec![expected]);
    assert_eq!(validate_action(&e, &request, &proposal), Ok(()));
}

#[test]
fn unavailable_ids_survive_for_the_real_engine_resolver() {
    let mut e = engine();
    let cmd = compile_action(&e, "I give another potion to Mira.").unwrap();
    let request = e.request("first", Intent::Actions(vec![cmd.clone()]));
    let p = Engine::proposal(&request).unwrap();
    let approved = e.preview(&request, &p).unwrap();
    e.commit(&request, &p, approved.narration()).unwrap();
    let request = e.request(
        "second",
        Intent::Actions(vec![
            compile_action(&e, "I give another potion to Mira.").unwrap()
        ]),
    );
    assert_eq!(
        e.preview(&request, &Engine::proposal(&request).unwrap()),
        Err(Error::Inventory)
    );
    for (text, error) in [
        ("I use ability teleport.", Error::Ability),
        ("I use my blink ability.", Error::Ability),
        ("I move to tower.", Error::Location),
    ] {
        let command = compile_action(&e, text).unwrap();
        let request = e.request("invalid", Intent::Actions(vec![command]));
        assert_eq!(
            e.preview(&request, &Engine::proposal(&request).unwrap()),
            Err(error)
        );
    }
    assert_eq!(
        compile_action(&e, "I use my teleport ability to jump to the tower."),
        Err(Error::ClarificationRequired)
    );
}

#[test]
fn names_are_scoped_and_ambiguous_names_are_not_guessed() {
    let mut s = seed();
    for id in ["oren", "sable"] {
        s.actors.get_mut(id).unwrap().location = "quay".into();
    }
    let e = Engine::new(s).unwrap();
    assert_eq!(
        compile_action(&e, "give potion to Oren"),
        Err(Error::ClarificationRequired)
    );
    assert_eq!(
        compile_action(&e, "give potion to oren"),
        Ok(Command::Give {
            item: "potion".into(),
            to: "oren".into(),
            quantity: 1
        })
    );
    assert_eq!(
        compile_action(&e, "give potion to MIRA"),
        Ok(Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 1
        })
    );
    assert_eq!(
        compile_action(&e, "give potion to unknown-id"),
        Ok(Command::Give {
            item: "potion".into(),
            to: "unknown-id".into(),
            quantity: 1
        })
    );
    assert_eq!(
        compile_action(&e, "give potion to Unknown Person"),
        Err(Error::ClarificationRequired)
    );
}

#[test]
fn canonical_argument_case_is_preserved_and_aliases_do_not_rewrite_ids() {
    let e = engine();
    assert_eq!(
        compile_action(&e, "GIVE my Potion TO Mira."),
        Ok(Command::Give {
            item: "Potion".into(),
            to: "mira".into(),
            quantity: 1
        })
    );
    assert_eq!(
        compile_action(&e, "USE ability BLINK"),
        Ok(Command::UseAbility {
            ability: "BLINK".into()
        })
    );
    assert_eq!(
        compile_action(&e, "move to PIER"),
        Ok(Command::Move { to: "PIER".into() })
    );
    let (request, proposal) = proposal(
        &e,
        "GIVE my Potion TO Mira.",
        vec![Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 1,
        }],
    );
    assert_eq!(validate_action(&e, &request, &proposal), Err(Error::Agency));
}

#[test]
fn finite_grammar_covers_supported_operations_without_effects() {
    let e = engine();
    let before = e.canonical_bytes();
    for (text, command) in [
        (
            "give my sole potion to mira",
            Command::Give {
                item: "potion".into(),
                to: "mira".into(),
                quantity: 1,
            },
        ),
        (
            "I give the 2 potion to mira.",
            Command::Give {
                item: "potion".into(),
                to: "mira".into(),
                quantity: 2,
            },
        ),
        (
            "drink my potion",
            Command::Consume {
                item: "potion".into(),
            },
        ),
        (
            "consume the potion",
            Command::Consume {
                item: "potion".into(),
            },
        ),
        (
            "use ability steady",
            Command::UseAbility {
                ability: "steady".into(),
            },
        ),
        (
            "learn the beacon ability",
            Command::Learn {
                ability: "beacon".into(),
            },
        ),
        ("go to the pier", Command::Move { to: "pier".into() }),
        ("I wait for one tide tick.", Command::Wait { ticks: 1 }),
        ("wait 2 ticks", Command::Wait { ticks: 2 }),
        (
            "discover fact beacon-mark",
            Command::Discover {
                fact: "beacon-mark".into(),
            },
        ),
        (
            "believe claim event 42",
            Command::Believe { claim_event: 42 },
        ),
    ] {
        assert_eq!(compile_action(&e, text), Ok(command), "{text}");
    }
    assert_eq!(before, e.canonical_bytes());
    assert_eq!(INPUT_GUARD_VERSION, "supported-english-v1");
}

#[test]
fn negated_quoted_compound_unsupported_and_oversized_input_never_guesses() {
    let e = engine();
    for text in [
        "",
        "I do not give potion to Mira",
        "I never give potion to Mira",
        "give no potion to Mira",
        "I don't give potion to Mira",
        "\"give potion to Mira\"",
        "`give potion to Mira`",
        "give potion to Mira and wait 1 tick",
        "give potion to Mira; wait 1 tick",
        "give potion to Mira, then wait",
        "give potion to Mira instead of Oren",
        "use blink or steady",
        "I teleport to tower",
        "wait",
        "give potion",
        "move pier",
        "wait -1 ticks",
        "give potion to Mira\nwait 1 tick",
        "say hello",
        "learn magic with Mira",
        "give potion to Mira..",
        "wait 99999999999 ticks",
    ] {
        assert_eq!(
            compile_action(&e, text),
            Err(Error::ClarificationRequired),
            "{text:?}"
        );
    }
    assert_eq!(
        compile_action(&e, &"x".repeat(MAX_TEXT_BYTES + 1)),
        Err(Error::TooLarge)
    );
}

#[test]
fn guard_never_grants_dialogue_or_privileged_intent_an_action() {
    let e = engine();
    let (request, p) = proposal(&e, "wait 1 tick", vec![Command::Wait { ticks: 1 }]);
    for intent in [
        Intent::Dialogue {
            text: "wait 1 tick".into(),
            audience: ["mira".into()].into(),
        },
        Intent::AuthorCorrection("wait 1 tick".into()),
        Intent::Thought("wait 1 tick".into()),
    ] {
        let mut q = request.clone();
        q.intent = intent;
        assert_eq!(validate_action(&e, &q, &p), Err(Error::Agency));
    }
    let mut q = request;
    q.intent = Intent::FreeText {
        kind: PlayInputKind::Dialogue,
        text: "wait 1 tick".into(),
    };
    assert_eq!(validate_action(&e, &q, &p), Err(Error::Agency));
}
