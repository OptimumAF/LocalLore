use super::*;
use crate::engine::Engine;
use crate::inference::Input;

fn input() -> InitialStoryInputV1 {
    InitialStoryInputV1 {
        version: 1,
        premise: "A surveyor reaches an orchard whose shadows reveal forgotten roads.".into(),
        player_name: "Sable".into(),
        player_description: "A patient surveyor who keeps careful notes.".into(),
        cast: vec![InitialCastHintV1 {
            name: "Finch".into(),
            description: "An orchard keeper with a private worry.".into(),
        }],
        profile: InitialRuleProfileV1::NarrativeV1,
        presentation: StoryPresentationV1::default(),
    }
}
fn proposal() -> InitialWorldProposalV1 {
    InitialWorldProposalV1 {
        version: 1,
        locations: vec![
            InitialLocationV1 {
                name: "Copper Orchard".into(),
                description: "Small copper markers hang beneath the trees.".into(),
            },
            InitialLocationV1 {
                name: "Wind Shed".into(),
                description: "Surveying tools line the quiet shed.".into(),
            },
        ],
        player_location: 0,
        characters: vec![InitialCharacterV1 {
            name: "Finch".into(),
            description: "Finch hides a damaged survey lens.".into(),
            location: 1,
            known_by: vec![1],
        }],
        routes: vec![
            InitialRouteV1 { from: 0, to: 1 },
            InitialRouteV1 { from: 1, to: 0 },
        ],
        facts: vec![
            InitialFactV1 {
                text: "A brass sundial is buried beneath the oldest tree.".into(),
                known_by: vec![1],
                discoverable_at: Some(0),
            },
            InitialFactV1 {
                text: "The wind shed door stands open.".into(),
                known_by: vec![0, 1],
                discoverable_at: Some(1),
            },
        ],
        beliefs: vec![InitialBeliefV1 {
            believer: 1,
            text: "Sable has already found the sundial.".into(),
            confidence: InitialConfidenceV1::Suspected,
        }],
        possessions: vec![InitialPossessionV1 {
            name: "Folded map".into(),
            description: "A map marked with fading orchard paths.".into(),
            owner: 0,
            return_to: Some(1),
        }],
    }
}
fn origin() -> InitialWorldOriginV1 {
    let input = input();
    let proposal = proposal();
    let response = serde_json::to_string(&proposal).unwrap();
    InitialWorldOriginV1 {
        version: 1,
        generation: InitialGenerationV1 {
            input: input.clone(),
            proposal: proposal.clone(),
            model_profile: "synthetic-author-v1".into(),
            provider: InitialProviderKindV1::Scripted,
            prompt_version: PROMPT_VERSION.into(),
            schema_version: SCHEMA_VERSION.into(),
            response_sha256: digest(response.as_bytes()),
            response,
        },
        reviewed: input,
        accepted: proposal,
        title: "The Orchard Survey".into(),
    }
}
fn scope() -> Scope {
    Scope {
        story: "original-test".into(),
        branch: "main".into(),
    }
}
fn seed() -> Seed {
    materialize(&origin(), scope()).unwrap()
}

#[test]
fn original_world_is_valid_in_both_profiles_with_only_native_mechanics() {
    for profile in [
        InitialRuleProfileV1::NarrativeV1,
        InitialRuleProfileV1::FantasyV1,
    ] {
        let mut o = origin();
        o.reviewed.profile = profile;
        let s = materialize(&o, scope()).unwrap();
        assert_eq!(validate_origin(&s), Ok(()));
        assert_eq!(s.actors.len(), 2);
        assert_eq!(s.locations.len(), 2);
        assert_eq!(s.relationships.len(), 2);
        assert!(s
            .relationships
            .iter()
            .all(|r| r.respect == 0 && r.trust == 0 && r.obligation == 0));
        assert!(s.actors.values().all(|a| a.alive
            && a.abilities.is_empty()
            && a.attributes.is_empty()
            && a.injuries.is_empty()));
        assert!(s.actors.values().all(|a| a.energy
            == if profile == InitialRuleProfileV1::FantasyV1 {
                100
            } else {
                0
            }));
        assert!(s.items.values().all(|i| i.quantity == 1 && !i.healing));
        assert!(s.abilities.is_empty() && s.commitments.is_empty());
        assert_eq!(s.story_time, 0);
        assert!(s.presentation.is_none());
        Engine::new(s).unwrap();
    }
}

#[test]
fn private_descriptions_beliefs_and_world_truth_keep_distinct_observers() {
    let s = seed();
    let e = Engine::new(s.clone()).unwrap();
    let h = origin_hash(&origin()).unwrap();
    let prefix = &h[..20];
    assert_eq!(s.id, format!("world-{prefix}"));
    assert_eq!(s.player, format!("a-{prefix}-0"));
    let npc = format!("a-{prefix}-1");
    let player = e.character_context(&s.player, e.scope(), 0).unwrap();
    let player_text = serde_json::to_string(&player).unwrap();
    assert!(player_text.contains("careful notes"));
    assert!(player_text.contains("Copper Orchard"));
    assert!(player_text.contains("Folded map"));
    assert!(!player_text.contains("damaged survey lens"));
    assert!(!player_text.contains("buried beneath"));
    assert!(!player_text.contains("already found"));
    assert!(!player_text.contains("synthetic-author"));
    assert!(!player_text.contains("response_sha256"));
    let other = e.character_context(&npc, e.scope(), 0).unwrap();
    let other_text = serde_json::to_string(&other).unwrap();
    assert!(other_text.contains("damaged survey lens"));
    assert!(other_text.contains("Wind Shed"));
    assert!(!other_text.contains("Folded map"));
    assert!(!other_text.contains("careful notes"));
    assert_eq!(s.beliefs.len(), 1);
    assert_eq!(s.beliefs[0].source_claim, None);
    assert_eq!(s.beliefs[0].source, Evidence::Seed(s.id.clone()));
    assert!(s
        .facts
        .values()
        .all(|f| f.proposition != "Sable has already found the sundial."));
    assert_eq!(
        s.facts[&format!("f-{prefix}-item-0")].known_by,
        BTreeSet::from([s.player.clone()])
    );
}

#[test]
fn reviewed_edits_change_native_identity_without_rewriting_original_generation() {
    let original = origin();
    let old_response = original.generation.response.clone();
    let mut reviewed = original.clone();
    reviewed.reviewed.player_name = "Maren".into();
    reviewed.reviewed.cast[0].name = "Tern".into();
    reviewed.accepted.characters[0].name = "Tern".into();
    reviewed.accepted.characters[0].description = "A keeper who tends the weather markers.".into();
    reviewed.accepted.facts[0].text = "The survey lens is safely stored in the shed.".into();
    let a = materialize(&original, scope()).unwrap();
    let b = materialize(&reviewed, scope()).unwrap();
    assert_ne!(a.id, b.id);
    assert_ne!(a.player, b.player);
    assert_ne!(origin_hash(&original), origin_hash(&reviewed));
    assert_eq!(b.actors[&b.player].name, "Maren");
    assert_eq!(
        b.initial_world.as_ref().unwrap().generation.response,
        old_response
    );
    assert_eq!(
        b.initial_world
            .as_ref()
            .unwrap()
            .generation
            .input
            .player_name,
        "Sable"
    );
    assert_eq!(validate_origin(&b), Ok(()));
}

#[test]
fn origin_replays_exact_raw_json_and_refuses_rebound_or_duplicate_provenance() {
    let mut o = origin();
    let compact = o.generation.response.clone();
    o.generation.response = format!("  {compact}\n");
    o.generation.response_sha256 = digest(o.generation.response.as_bytes());
    assert!(origin_hash(&o).is_ok());
    assert_ne!(origin_hash(&o), origin_hash(&origin()));
    let mut bad = o.clone();
    bad.generation.response_sha256 = "0".repeat(64);
    assert!(origin_hash(&bad).is_err());
    let mut bad = o.clone();
    bad.generation.proposal.facts[0].text = "A forged parsed proposal.".into();
    assert!(origin_hash(&bad).is_err());
    let mut bad = o.clone();
    bad.generation.response = compact.replacen("{", "{\"version\":1,", 1);
    bad.generation.response_sha256 = digest(bad.generation.response.as_bytes());
    assert!(origin_hash(&bad).is_err());
    for field in ["prompt", "schema", "profile"] {
        let mut bad = o.clone();
        match field {
            "prompt" => bad.generation.prompt_version = "initial-world-v2".into(),
            "schema" => bad.generation.schema_version = "seed-import".into(),
            _ => bad.generation.model_profile = "../model".into(),
        };
        assert!(origin_hash(&bad).is_err());
    }
    let mut bad = o;
    bad.generation.response = "x".repeat(MAX_ORIGIN_BYTES);
    assert_eq!(origin_hash(&bad), Err("TooLarge".into()));
}

#[test]
fn every_materialized_field_is_reconstructed_and_scope_rebinding_is_explicit() {
    let s = seed();
    let mut rebound = s.clone();
    rebound.scope = Scope {
        story: "imported-story".into(),
        branch: "child".into(),
    };
    assert_eq!(validate_origin(&rebound), Ok(()));
    assert_eq!(
        origin_hash(rebound.initial_world.as_ref().unwrap()),
        origin_hash(s.initial_world.as_ref().unwrap())
    );
    for n in 0..6 {
        let mut bad = s.clone();
        match n {
            0 => bad.actors.get_mut(&bad.player).unwrap().name = "Forged".into(),
            1 => bad.items.values_mut().next().unwrap().healing = true,
            2 => bad.items.values_mut().next().unwrap().quantity = 2,
            3 => bad.actors.get_mut(&bad.player).unwrap().energy = 1,
            4 => bad.facts.values_mut().next().unwrap().proposition = "A changed fact.".into(),
            _ => bad.story_time = 1,
        };
        assert!(validate_origin(&bad).is_err());
    }
    let engine = Engine::new(s).unwrap();
    let child = engine.fork("forked", 0).unwrap();
    assert_eq!(validate_origin(child.seed()), Ok(()));
}

#[test]
fn proposal_refs_visibility_names_and_directed_reachability_fail_closed() {
    let i = input();
    for n in 0..10 {
        let mut p = proposal();
        match n {
            0 => p.characters[0].known_by = vec![0],
            1 => p.characters[0].known_by = vec![1, 1],
            2 => p.facts[0].known_by = vec![2],
            3 => p.facts[0].discoverable_at = Some(2),
            4 => p.beliefs[0].believer = 2,
            5 => p.possessions[0].return_to = Some(0),
            6 => p.characters[0].name = "SABLE".into(),
            7 => p.routes = vec![InitialRouteV1 { from: 1, to: 0 }],
            8 => p.routes.push(p.routes[0].clone()),
            _ => p.characters[0].name = "Another keeper".into(),
        };
        assert!(validate_proposal(&i, &p).is_err(), "case {n}");
    }
    let mut p = proposal();
    p.routes = vec![InitialRouteV1 { from: 0, to: 1 }];
    assert_eq!(validate_proposal(&i, &p), Ok(()));
    let mut p = proposal();
    p.facts[0].known_by.clear();
    assert_eq!(validate_proposal(&i, &p), Ok(()));
}

#[test]
fn original_text_and_count_limits_are_utf8_bounded_without_normalization() {
    let mut i = input();
    i.cast.clear();
    i.player_description.clear();
    i.premise = "é".repeat(1024);
    assert_eq!(validate_input(&i), Ok(()));
    i.premise.push('x');
    assert!(validate_input(&i).is_err());
    let mut i = input();
    i.player_name = "🪶".repeat(64);
    assert_eq!(validate_input(&i), Ok(()));
    i.player_name.push('x');
    assert!(validate_input(&i).is_err());
    for bad in [" outer", "outer ", "line\nline", "bidi\u{202e}", "nul\0"] {
        let mut i = input();
        i.player_description = bad.into();
        assert!(validate_input(&i).is_err());
    }
    let mut i = input();
    i.player_description.clear();
    i.cast[0].description.clear();
    assert_eq!(validate_input(&i), Ok(()));
    let mut p = proposal();
    p.facts = (0..9)
        .map(|n| InitialFactV1 {
            text: format!("Distinct fact {n}"),
            known_by: vec![0],
            discoverable_at: None,
        })
        .collect();
    assert!(validate_proposal(&input(), &p).is_err());
    let mut p = proposal();
    p.facts[0].text = "x".repeat(513);
    assert!(validate_proposal(&input(), &p).is_err());
    let mut p = proposal();
    p.locations[0].description = "é".repeat(256);
    assert!(validate_proposal(&input(), &p).is_ok());
}

#[test]
fn closed_wire_and_author_request_do_not_offer_ids_tools_or_mechanical_fields() {
    let mut value = serde_json::to_value(proposal()).unwrap();
    value["characters"][0]["abilities"] = serde_json::json!({"teleport":100});
    assert!(serde_json::from_value::<InitialWorldProposalV1>(value).is_err());
    let schema = proposal_schema();
    assert_eq!(schema["additionalProperties"], false);
    for field in [
        "id",
        "scope",
        "commands",
        "energy",
        "abilities",
        "attributes",
        "healing",
    ] {
        assert!(schema["properties"].get(field).is_none());
    }
    let r = generation_request(&input(), "synthetic-author-v1", "job_1").unwrap();
    assert_eq!(r.scope.story, "author-draft-job_1");
    assert_eq!(r.scope.branch, "draft");
    assert_eq!(r.schema, SCHEMA_VERSION);
    assert_eq!(r.budget.max_output_tokens, 1024);
    assert_eq!(r.budget.max_output_bytes, 8192);
    assert_eq!(r.budget.deadline_ms, 120000);
    assert_eq!(r.budget.max_pending_polls, 24000);
    let Input::Structured {
        role,
        prompt,
        schema: actual,
    } = r.input
    else {
        panic!("author structured request")
    };
    assert_eq!(role, "author");
    assert!(prompt.contains("untrusted author data"));
    assert_eq!(actual, schema);
    for job in ["", "../job", "with space", "🪶"] {
        assert!(generation_request(&input(), "synthetic-author-v1", job).is_err());
    }
    assert!(generation_request(&input(), "synthetic-author-v1", &"a".repeat(33)).is_err());
}

#[test]
fn reserved_native_namespace_refuses_stripped_origin_without_authenticating_legacy_imports() {
    let mut s = seed();
    s.initial_world = None;
    assert!(validate_origin(&s).is_err());
    assert!(Engine::new(s.clone()).is_err());
    s.id = "legacy-imported-world".into();
    s.beliefs.clear();
    assert_eq!(validate_origin(&s), Ok(()));
    Engine::new(s).unwrap();
}
