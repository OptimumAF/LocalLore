// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
use super::*;
use crate::story_setup::{self, NARRATIVE_TEMPLATE, TEMPLATE};
use sha2::{Digest, Sha256};

fn call(host: &Host, command: Value) -> Value {
    host.call(&serde_json::to_vec(&json!({"version": 1, "command": command})).unwrap())
}

#[test]
fn catalog_lists_two_native_profiles_without_session_or_world_mutation() {
    let host = Host::new(false);
    let before = host.state.lock().unwrap().next;
    let catalog = call(&host, json!({"op": "story_templates"}));
    assert_eq!(catalog["status"], "ok");
    assert_eq!(catalog["data"]["version"], 1);
    assert_eq!(catalog["data"]["templates"].as_array().unwrap().len(), 2);
    for (index, (template, profile)) in [
        (TEMPLATE, "fantasy_v1"),
        (NARRATIVE_TEMPLATE, "narrative_v1"),
    ]
    .into_iter()
    .enumerate()
    {
        let descriptor = &catalog["data"]["templates"][index];
        assert_eq!(descriptor["template"], template);
        assert_eq!(descriptor["profile"], profile);
        assert_eq!(descriptor.as_object().unwrap().len(), 4);
        let preview = call(&host, json!({"op":"story_template","template":template}));
        assert_eq!(preview["status"], "ok");
        for field in ["template", "default_title", "description", "profile"] {
            assert_eq!(descriptor[field], preview["data"][field]);
        }
    }
    assert_eq!(catalog, call(&host, json!({"op": "story_templates"})));
    let state = host.state.lock().unwrap();
    assert!(state.sessions.is_empty());
    assert_eq!(state.next, before);
}

#[test]
fn catalog_command_rejects_foreign_fields_duplicates_and_seed_input() {
    let host = Host::new(false);
    for command in [
        json!({"op":"story_templates","template":TEMPLATE}),
        json!({"op":"story_templates","seed":{}}),
        json!({"op":"story_templates","version":1}),
    ] {
        assert_eq!(call(&host, command)["error"], "Malformed");
    }
    assert_eq!(
        host.call(br#"{"version":1,"command":{"op":"story_templates","op":"story_templates"}}"#)
            ["error"],
        "Malformed"
    );
    assert!(host.state.lock().unwrap().sessions.is_empty());
}

#[test]
fn narrative_preview_excludes_npc_only_truth_and_belief() {
    let preview = story_setup::template_preview(NARRATIVE_TEMPLATE).unwrap();
    let text = serde_json::to_string(&preview).unwrap();
    assert_eq!(preview.profile, "narrative_v1");
    assert!(text.contains("Player: Aster"));
    assert!(text.contains("ferry-schedule"));
    assert!(text.contains("return-lantern"));
    assert!(!text.contains("BRACKEN-CHEST-482"));
    assert!(!text.contains("BRACKEN-RUMOR-619"));
    assert!(!text.contains("ledger-location"));
    assert_eq!(
        preview.seed_sha256,
        format!(
            "{:x}",
            Sha256::digest(include_bytes!("../../../../fixtures/bracken_harbor.json"))
        )
    );
}

#[test]
fn selected_template_binds_exact_bytes_and_does_not_accept_another_hash() {
    let old = story_setup::template_preview(TEMPLATE).unwrap();
    let narrative = story_setup::template_preview(NARRATIVE_TEMPLATE).unwrap();
    assert_ne!(old.seed_sha256, narrative.seed_sha256);
    for (template, wrong_hash) in [
        (TEMPLATE, narrative.seed_sha256.as_str()),
        (NARRATIVE_TEMPLATE, old.seed_sha256.as_str()),
    ] {
        assert!(matches!(
            story_setup::prepare_named(template, wrong_hash, "Original review", &"a".repeat(32)),
            Err("Stale")
        ));
    }
    for unknown in [
        "bracken-harbor",
        "BRACKEN-HARBOR-V1",
        "../bracken_harbor.json",
    ] {
        assert!(matches!(
            story_setup::template_preview(unknown),
            Err("UnsupportedSeed")
        ));
    }
}

#[test]
fn narrative_starter_uses_real_engine_rules_and_preserves_loan_ownership() {
    let preview = story_setup::template_preview(NARRATIVE_TEMPLATE).unwrap();
    let starter = story_setup::prepare_named(
        NARRATIVE_TEMPLATE,
        &preview.seed_sha256,
        "An evening in Bracken Harbor",
        &"b".repeat(32),
    )
    .unwrap();
    assert_eq!(starter.seed().id, NARRATIVE_TEMPLATE);
    assert_eq!(starter.seed().profile, Profile::NarrativeV1);
    assert!(starter.seed().abilities.is_empty());
    assert!(starter.seed().actors.values().all(|actor| actor.energy == 0
        && actor.attributes.is_empty()
        && actor.abilities.is_empty()));
    let engine = Engine::new(starter.seed().clone()).unwrap();
    let gift = engine.request(
        "original-thread-gift",
        Intent::Actions(vec![Command::Give {
            item: "sail-thread".into(),
            to: "nessa".into(),
            quantity: 1,
        }]),
    );
    assert!(engine
        .preview(&gift, &Engine::proposal(&gift).unwrap())
        .is_ok());
    let invented = engine.request(
        "original-invented-ability",
        Intent::Actions(vec![Command::UseAbility {
            ability: "steady".into(),
        }]),
    );
    assert_eq!(
        engine.preview(&invented, &Engine::proposal(&invented).unwrap()),
        Err(Error::Ability)
    );
    let loan = engine.request(
        "original-loan-away",
        Intent::Actions(vec![
            Command::Move { to: "jetty".into() },
            Command::Give {
                item: "borrowed-lantern".into(),
                to: "cal".into(),
                quantity: 1,
            },
        ]),
    );
    assert!(engine
        .preview(&loan, &Engine::proposal(&loan).unwrap())
        .is_err());
    assert_eq!(engine.revision(), 0);
    assert_eq!(engine.state().actors["player"].location, "boathouse");
    assert_eq!(
        engine.state().items["borrowed-lantern"]
            .return_to
            .as_deref(),
        Some("nessa")
    );
}
