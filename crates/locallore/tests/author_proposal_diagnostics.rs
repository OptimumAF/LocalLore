//! Original hostile proposals exercise the authoritative checks, never a repair path.
use locallore::{
    contracts::*,
    engine::Engine,
    story_authoring::{
        self, InitialGenerationV1, InitialModelConfigurationV1, InitialProposalFailureV1 as F,
        InitialProviderKindV1, InitialStoryInputV1, InitialWorldOriginV1, InitialWorldProposalV1,
    },
};
use serde_json::json;
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;

fn fixture() -> (InitialStoryInputV1, InitialWorldProposalV1) {
    let input = serde_json::from_value(json!({"version":1,
        "premise":"Mira visits a reed ferry landing to ask which bell marks a safe crossing.",
        "player_name":"Mira","player_description":"A courier with no special authority.",
        "cast":[{"name":"Neri","description":"A bell keeper."},{"name":"Vale","description":"A paper sorter."}],
        "profile":"narrative_v1","presentation":{"version":1,"tone":"plain","excluded_phrases":[]}})).unwrap();
    let proposal = serde_json::from_value(json!({"version":1,
        "locations":[{"name":"Reed landing","description":"A bell hangs beside a ferry rope."},
                     {"name":"Drying room","description":"Reed paper rests on shelves."}],
        "player_location":0,
        "characters":[{"name":"Neri","description":"A keeper watching the ferry rope.","location":0,"known_by":[1,0]},
                      {"name":"Vale","description":"A sorter guarding a folded note.","location":1,"known_by":[2]}],
        "routes":[{"from":0,"to":1}],
        "facts":[{"text":"The ferry rope is tied to the landing.","known_by":[0,1],"discoverable_at":0},
                 {"text":"A blue note is hidden on the upper shelf.","known_by":[2],"discoverable_at":1}],
        "beliefs":[{"believer":1,"text":"The blue note may be blank.","confidence":"suspected"}],
        "possessions":[{"name":"Reed token","description":"A plain ferry marker.","owner":0,"return_to":1}]})).unwrap();
    (input, proposal)
}
fn invalid(reason: F, change: impl FnOnce(&mut InitialStoryInputV1, &mut InitialWorldProposalV1)) {
    let (mut input, mut proposal) = fixture();
    change(&mut input, &mut proposal);
    let original = (input.clone(), proposal.clone());
    assert_eq!(
        story_authoring::validate_proposal_detailed(&input, &proposal),
        Err(reason)
    );
    assert_eq!(
        story_authoring::validate_proposal(&input, &proposal),
        Err("InvalidProposal".into())
    );
    assert_eq!(reason.legacy_error(), "InvalidProposal");
    assert_eq!(
        (input, proposal),
        original,
        "diagnostics cannot repair or normalize input"
    );
}
type Mutation = fn(&mut InitialStoryInputV1, &mut InitialWorldProposalV1);

#[test]
fn version_cardinality_and_player_location_keep_the_legacy_refusal() {
    let cases: &[(F, Mutation)] = &[
        (F::ProposalVersion, |_, p| p.version = 2),
        (F::LocationCount, |_, p| p.locations.clear()),
        (F::LocationCount, |_, p| {
            p.locations.resize(5, p.locations[0].clone())
        }),
        (F::CharacterCount, |_, p| p.characters.clear()),
        (F::CharacterCount, |_, p| {
            p.characters.resize(4, p.characters[0].clone())
        }),
        (F::PlayerLocation, |_, p| p.player_location = 2),
        (F::RouteCount, |_, p| {
            p.routes.resize(9, p.routes[0].clone())
        }),
        (F::FactCount, |_, p| p.facts.resize(9, p.facts[0].clone())),
        (F::BeliefCount, |_, p| {
            p.beliefs.resize(7, p.beliefs[0].clone())
        }),
        (F::PossessionCount, |_, p| {
            p.possessions.resize(5, p.possessions[0].clone())
        }),
    ];
    for (reason, change) in cases {
        invalid(*reason, change);
    }
}

#[test]
fn names_and_descriptions_refuse_unsafe_duplicate_or_mismatched_cast_data() {
    let cases: &[(F, Mutation)] = &[
        (F::LocationNames, |_, p| {
            p.locations[1].name = "REED LANDING".into()
        }),
        (F::LocationNames, |_, p| {
            p.locations[0].name = "unsafe\u{202e}".into()
        }),
        (F::LocationNames, |_, p| {
            p.locations[0].name = "界".repeat(65)
        }),
        (F::CharacterNames, |_, p| {
            p.characters[0].name = "MIRA".into()
        }),
        (F::CharacterNames, |_, p| {
            p.characters[0].name = "Neri\0".into()
        }),
        (F::PossessionNames, |_, p| {
            p.possessions.push(p.possessions[0].clone())
        }),
        (F::PossessionNames, |_, p| {
            p.possessions[0].name = " ".into()
        }),
        (F::LocationDescription, |_, p| {
            p.locations[0].description.clear()
        }),
        (F::LocationDescription, |_, p| {
            p.locations[0].description = "x".repeat(513)
        }),
        (F::CastNames, |i, _| i.cast.reverse()),
        (F::CastNames, |i, _| {
            i.cast.pop();
        }),
        (F::CastNames, |i, _| i.cast[0].name = "Other keeper".into()),
    ];
    for (reason, change) in cases {
        invalid(*reason, change);
    }
}

#[test]
fn character_description_location_references_and_self_knowledge_are_distinct() {
    let cases: &[(F, Mutation)] = &[
        (F::CharacterDescription, |_, p| {
            p.characters[0].description = "a\nb".into()
        }),
        (F::CharacterLocation, |_, p| p.characters[0].location = 2),
        (F::CharacterKnownBy, |_, p| {
            p.characters[0].known_by = vec![1, 1]
        }),
        (F::CharacterKnownBy, |_, p| {
            p.characters[0].known_by = vec![1, 3]
        }),
        (F::CharacterKnownBy, |_, p| {
            p.characters[0].known_by = vec![0, 1, 2, 0]
        }),
        (F::CharacterSelfKnowledge, |_, p| {
            p.characters[0].known_by = vec![0]
        }),
        (F::CharacterSelfKnowledge, |_, p| {
            p.characters[1].known_by.clear()
        }),
    ];
    for (reason, change) in cases {
        invalid(*reason, change);
    }
}

#[test]
fn directed_route_guards_never_autoconnect_or_reverse_a_route() {
    let cases: &[(F, Mutation)] = &[
        (F::RouteSelf, |_, p| p.routes[0].to = 0),
        (F::RouteReference, |_, p| p.routes[0].from = 2),
        (F::RouteReference, |_, p| p.routes[0].to = 2),
        (F::RouteDuplicate, |_, p| p.routes.push(p.routes[0].clone())),
        (F::RouteReachability, |_, p| p.routes.clear()),
        (F::RouteReachability, |_, p| p.player_location = 1),
    ];
    for (reason, change) in cases {
        invalid(*reason, change);
    }
}

#[test]
fn fact_belief_and_possession_guards_keep_truth_and_belief_boundaries() {
    let cases: &[(F, Mutation)] = &[
        (F::FactText, |_, p| {
            p.facts[0].text = "unsafe\u{2066}".into()
        }),
        (F::FactKnownBy, |_, p| p.facts[0].known_by = vec![0, 0]),
        (F::FactKnownBy, |_, p| p.facts[0].known_by = vec![3]),
        (F::FactDiscoveryLocation, |_, p| {
            p.facts[0].discoverable_at = Some(2)
        }),
        (F::FactDuplicate, |_, p| {
            p.facts[1].text = p.facts[0].text.to_uppercase()
        }),
        (F::BeliefBeliever, |_, p| p.beliefs[0].believer = 3),
        (F::BeliefText, |_, p| p.beliefs[0].text = " ".into()),
        (F::BeliefDuplicate, |_, p| {
            p.beliefs.push(p.beliefs[0].clone())
        }),
        (F::PossessionDescription, |_, p| {
            p.possessions[0].description.clear()
        }),
        (F::PossessionOwner, |_, p| p.possessions[0].owner = 3),
        (F::PossessionReturnTo, |_, p| {
            p.possessions[0].return_to = Some(3)
        }),
        (F::PossessionReturnTo, |_, p| {
            p.possessions[0].return_to = Some(0)
        }),
    ];
    for (reason, change) in cases {
        invalid(*reason, change);
    }
}

#[test]
fn input_and_total_size_errors_preserve_exact_legacy_projection_and_precedence() {
    let (mut input, mut proposal) = fixture();
    input.version = 2;
    assert_eq!(
        story_authoring::validate_proposal_detailed(&input, &proposal),
        Err(F::InvalidInput)
    );
    assert_eq!(
        story_authoring::validate_proposal(&input, &proposal),
        Err("InvalidInput".into())
    );
    input.premise = "x".repeat(4097);
    assert_eq!(
        story_authoring::validate_proposal_detailed(&input, &proposal),
        Err(F::InputTooLarge)
    );
    assert_eq!(
        story_authoring::validate_proposal(&input, &proposal),
        Err("TooLarge".into())
    );
    let (input, _) = fixture();
    proposal.locations[0].description = "x".repeat(8193);
    assert_eq!(
        story_authoring::validate_proposal_detailed(&input, &proposal),
        Err(F::ProposalTooLarge)
    );
    assert_eq!(
        story_authoring::validate_proposal(&input, &proposal),
        Err("TooLarge".into())
    );
    // Preserve the original short-circuit precedence when more than one field is invalid.
    invalid(F::ProposalVersion, |_, p| {
        p.version = 2;
        p.locations.clear();
    });
    invalid(F::CharacterKnownBy, |_, p| {
        p.characters[0].known_by = vec![3]
    });
    assert_eq!(F::ProposalEncoding.legacy_error(), "InvalidInput");
}

fn origin(input: InitialStoryInputV1, proposal: InitialWorldProposalV1) -> InitialWorldOriginV1 {
    let response = serde_json::to_string(&proposal).unwrap();
    InitialWorldOriginV1 {
        version: 1,
        generation: InitialGenerationV1 {
            input: input.clone(),
            proposal: proposal.clone(),
            model_profile: "diagnostic-fixture-v1".into(),
            model_configuration: InitialModelConfigurationV1 {
                id: "diagnostic-fixture-v1".into(),
                model_sha256: "1".repeat(64),
                runtime_revision: "2".repeat(40),
                template_sha256: "3".repeat(64),
                worker_sha256: "4".repeat(64),
                profile_manifest_sha256: "5".repeat(64),
                context_tokens: 4096,
                director_tokens: 350,
                narrator_tokens: 220,
                deadline_ms: 60000,
                repair_limit: 1,
            },
            provider: InitialProviderKindV1::Scripted,
            prompt_version: "initial-world-v1".into(),
            schema_version: "initial-world-v1".into(),
            response_sha256: format!("{:x}", Sha256::digest(response.as_bytes())),
            response,
        },
        reviewed: input,
        accepted: proposal,
        title: "Reed ferry diagnostic fixture".into(),
    }
}

#[test]
fn valid_original_world_still_materializes_with_private_knowledge_and_no_stats_grants() {
    let (input, mut proposal) = fixture();
    for profile in [
        story_authoring::InitialRuleProfileV1::NarrativeV1,
        story_authoring::InitialRuleProfileV1::FantasyV1,
    ] {
        let mut input = input.clone();
        input.profile = profile;
        proposal.characters[0].known_by.reverse();
        let unchanged = proposal.clone();
        assert_eq!(
            story_authoring::validate_proposal_detailed(&input, &proposal),
            Ok(())
        );
        assert_eq!(
            story_authoring::validate_proposal(&input, &proposal),
            Ok(())
        );
        assert_eq!(proposal, unchanged);
        let origin = origin(input, proposal.clone());
        let scope = Scope {
            story: "diagnostic-fixture".into(),
            branch: "main".into(),
        };
        let seed = story_authoring::materialize(&origin, scope.clone()).unwrap();
        let engine = Engine::new(seed.clone()).unwrap();
        assert!(seed.abilities.is_empty());
        assert!(seed
            .actors
            .values()
            .all(|a| a.attributes.is_empty() && a.abilities.is_empty() && a.injuries.is_empty()));
        let expected_energy = if profile == story_authoring::InitialRuleProfileV1::FantasyV1 {
            100
        } else {
            0
        };
        assert!(seed.actors.values().all(|a| a.energy == expected_energy));
        assert!(seed.items.values().all(|i| i.quantity == 1 && !i.healing));
        let player = engine.character_context(&seed.player, &scope, 0).unwrap();
        assert!(!player
            .facts
            .values()
            .any(|text| text.contains("upper shelf") || text.contains("sorter guarding")));
        assert!(player.beliefs.is_empty());
        assert_eq!(seed.beliefs.len(), 1);
        assert!(seed.beliefs[0].source_claim.is_none());
        assert!(!seed
            .facts
            .values()
            .any(|f| f.proposition == seed.beliefs[0].proposition));
        assert_eq!(engine.revision(), 0);
    }
}

#[test]
fn empty_author_hints_and_unknown_world_truth_remain_accepted_without_normalization() {
    let (mut input, mut proposal) = fixture();
    input.cast.clear();
    input.player_description.clear();
    proposal.facts[0].known_by.clear();
    proposal.facts[0].discoverable_at = None;
    proposal.possessions[0].return_to = None;
    assert_eq!(
        story_authoring::validate_proposal_detailed(&input, &proposal),
        Ok(())
    );
    assert_eq!(
        story_authoring::validate_proposal(&input, &proposal),
        Ok(())
    );
    assert!(proposal.facts[0].known_by.is_empty());
}

#[test]
fn reason_wire_is_closed_data_free_and_legacy_strings_are_exact() {
    let reasons = [
        F::InvalidInput,
        F::InputTooLarge,
        F::ProposalTooLarge,
        F::ProposalEncoding,
        F::ProposalVersion,
        F::LocationCount,
        F::CharacterCount,
        F::PlayerLocation,
        F::RouteCount,
        F::FactCount,
        F::BeliefCount,
        F::PossessionCount,
        F::LocationNames,
        F::CharacterNames,
        F::PossessionNames,
        F::LocationDescription,
        F::CastNames,
        F::CharacterDescription,
        F::CharacterLocation,
        F::CharacterKnownBy,
        F::CharacterSelfKnowledge,
        F::RouteSelf,
        F::RouteReference,
        F::RouteDuplicate,
        F::RouteReachability,
        F::FactText,
        F::FactKnownBy,
        F::FactDiscoveryLocation,
        F::FactDuplicate,
        F::BeliefBeliever,
        F::BeliefText,
        F::BeliefDuplicate,
        F::PossessionDescription,
        F::PossessionOwner,
        F::PossessionReturnTo,
    ];
    let mut values = BTreeSet::new();
    for reason in reasons {
        let value = serde_json::to_value(reason).unwrap();
        let name = value.as_str().unwrap();
        assert!(name.bytes().all(|b| b.is_ascii_lowercase() || b == b'_'));
        assert!(values.insert(name.to_owned()));
        assert_eq!(serde_json::from_value::<F>(value).unwrap(), reason);
        assert!(matches!(
            reason.legacy_error(),
            "InvalidInput" | "TooLarge" | "InvalidProposal"
        ));
    }
    assert_eq!(values.len(), 35);
    assert!(serde_json::from_value::<F>(json!("unknown_reason")).is_err());
    assert!(
        serde_json::from_value::<F>(json!({"character_self_knowledge":"secret text"})).is_err()
    );
}
