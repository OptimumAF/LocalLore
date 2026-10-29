//! Original synthetic checks for the portable initial-world grammar. No inference is run.
use locallore::{
    contracts::{Profile, Scope},
    engine::Engine,
    inference::Input,
    story_authoring::{
        self, InitialGenerationV1, InitialModelConfigurationV1, InitialProviderKindV1,
        InitialStoryInputV1, InitialWorldOriginV1, InitialWorldProposalV1,
    },
};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;

const INPUT: &str = include_str!("../../../fixtures/initial_world/ashglass-input.json");
const PROPOSAL: &str = include_str!("../../../fixtures/initial_world/ashglass-proposal.json");

fn fixture() -> (InitialStoryInputV1, InitialWorldProposalV1) {
    (
        serde_json::from_str(INPUT).unwrap(),
        serde_json::from_str(PROPOSAL).unwrap(),
    )
}
fn visibility(character: bool) -> Value {
    let schema = story_authoring::proposal_schema();
    if character {
        schema["properties"]["characters"]["items"]["properties"]["known_by"].clone()
    } else {
        schema["properties"]["facts"]["items"]["properties"]["known_by"].clone()
    }
}
fn choices(character: bool) -> Vec<Value> {
    visibility(character)["enum"].as_array().unwrap().clone()
}
fn origin() -> InitialWorldOriginV1 {
    let (input, proposal) = fixture();
    InitialWorldOriginV1 {
        version: 1,
        generation: InitialGenerationV1 {
            input: input.clone(),
            proposal: proposal.clone(),
            model_profile: "schema-portability-scripted-v1".into(),
            model_configuration: InitialModelConfigurationV1 {
                id: "schema-portability-scripted-v1".into(),
                model_sha256: "1".repeat(64),
                runtime_revision: "2".repeat(40),
                template_sha256: "3".repeat(64),
                worker_sha256: "4".repeat(64),
                profile_manifest_sha256: "5".repeat(64),
                context_tokens: 4096,
                director_tokens: 320,
                narrator_tokens: 256,
                deadline_ms: 5000,
                repair_limit: 1,
            },
            provider: InitialProviderKindV1::Scripted,
            prompt_version: "initial-world-v1".into(),
            schema_version: "initial-world-v1".into(),
            response: PROPOSAL.into(),
            response_sha256: format!("{:x}", Sha256::digest(PROPOSAL.as_bytes())),
        },
        reviewed: input,
        accepted: proposal,
        title: "Ashglass portable author schema".into(),
    }
}
fn scope() -> Scope {
    Scope {
        story: "schema-portability".into(),
        branch: "main".into(),
    }
}

#[test]
fn enums_cover_every_ordered_unique_array_and_exclude_exhaustive_small_adversaries() {
    for (character, count) in [(true, 64), (false, 65)] {
        let allowed = choices(character);
        assert_eq!(allowed.len(), count);
        let distinct: BTreeSet<_> = allowed.iter().map(Value::to_string).collect();
        assert_eq!(distinct.len(), count);
        // Independent base-five exhaustion includes every ordering, duplicates,
        // the out-of-range reference4 and every overlong five-element sequence.
        let mut expected = BTreeSet::new();
        for len in 0..=5_u32 {
            for mut code in 0..5_u32.pow(len) {
                let mut candidate = Vec::new();
                for _ in 0..len {
                    candidate.push(code % 5);
                    code /= 5;
                }
                let valid = len <= 4
                    && (!character || len > 0)
                    && candidate.iter().all(|n| *n < 4)
                    && candidate.iter().collect::<BTreeSet<_>>().len() == candidate.len();
                let value = json!(candidate);
                assert_eq!(
                    allowed.contains(&value),
                    valid,
                    "character={character}, array={value}"
                );
                if valid {
                    expected.insert(value.to_string());
                }
            }
        }
        assert_eq!(distinct, expected);
    }
    assert!(choices(true).contains(&json!([1, 0])));
    assert!(choices(true).contains(&json!([0, 1])));
    assert!(choices(false).contains(&json!([3, 2, 1, 0])));
}

#[test]
fn visibility_nodes_keep_original_bounds_and_reject_noninteger_or_foreign_shapes() {
    for character in [true, false] {
        let mut node = visibility(character);
        let allowed = node.as_object_mut().unwrap().remove("enum").unwrap();
        assert!(allowed.is_array());
        let mut expected =
            json!({"type":"array","items":{"type":"integer","minimum":0,"maximum":3},"maxItems":4});
        if character {
            expected["minItems"] = json!(1);
        }
        assert_eq!(node, expected);
        for invalid in [
            json!(null),
            json!(0),
            json!(true),
            json!({}),
            json!(["1"]),
            json!([1.0]),
            json!([1.5]),
            json!([-1]),
            json!([65536]),
        ] {
            assert!(!choices(character).contains(&invalid), "{invalid}");
        }
    }
    fn no_unsupported(value: &Value) {
        match value {
            Value::Object(map) => {
                assert!(!map.contains_key("uniqueItems"));
                for child in map.values() {
                    no_unsupported(child);
                }
            }
            Value::Array(values) => {
                for child in values {
                    no_unsupported(child);
                }
            }
            _ => {}
        }
    }
    no_unsupported(&story_authoring::proposal_schema());
}

#[test]
fn actual_author_request_uses_exact_production_schema_and_unchanged_budgets() {
    let (input, _) = fixture();
    let request =
        story_authoring::generation_request(&input, "portable-author-v1", "schema-proof").unwrap();
    assert_eq!(request.schema, "initial-world-v1");
    assert_eq!(request.scope.story, "author-draft-schema-proof");
    assert_eq!(request.scope.branch, "draft");
    assert_eq!(request.budget.max_output_tokens, 1024);
    assert_eq!(request.budget.max_output_bytes, 8192);
    assert_eq!(request.budget.deadline_ms, 120000);
    assert_eq!(request.budget.max_pending_polls, 24000);
    match request.input {
        Input::Structured {
            role,
            prompt,
            schema,
        } => {
            assert_eq!(role, "author");
            assert_eq!(schema, story_authoring::proposal_schema());
            let bytes = serde_json::to_vec(&schema).unwrap();
            assert!(bytes.len() <= 16384); // Existing oracle schema-string limit.
            assert!(bytes.len() + 16384 <= 32768); // Even the admitted maximum prompt fits the bridge.
            assert!(prompt.len() + bytes.len() <= 32768);
        }
        _ => panic!("author must use the structured schema route"),
    }
}

#[test]
fn grammar_visibility_choices_do_not_replace_native_cross_field_validation() {
    let (input, base) = fixture();
    story_authoring::validate_proposal(&input, &base).unwrap();
    let mut invalid = base.clone();
    invalid.facts[0].known_by = vec![3];
    assert!(choices(false).contains(&json!([3]))); // Actor3 does not exist in this particular world.
    assert!(story_authoring::validate_proposal(&input, &invalid).is_err());
    invalid = base.clone();
    invalid.characters[0].known_by = vec![0];
    assert!(choices(true).contains(&json!([0]))); // Character1 must know its own description.
    assert!(story_authoring::validate_proposal(&input, &invalid).is_err());
    for references in [vec![1, 1], vec![4], vec![0, 1, 2, 3]] {
        invalid = base.clone();
        invalid.facts[0].known_by = references;
        assert!(story_authoring::validate_proposal(&input, &invalid).is_err());
    }
    invalid = base;
    invalid.routes.clear(); // All locations still have to be reachable; the grammar cannot grant a route.
    assert!(story_authoring::validate_proposal(&input, &invalid).is_err());
}

#[test]
fn ordered_review_values_survive_origin_hash_and_engine_materialization() {
    let mut first = origin();
    first.accepted.characters[0].known_by = vec![1, 0];
    first.accepted.facts[0].known_by = vec![2, 1, 0];
    let mut second = first.clone();
    second.accepted.characters[0].known_by = vec![0, 1];
    second.accepted.facts[0].known_by = vec![0, 1, 2];
    assert_eq!(first.generation, second.generation);
    assert_ne!(
        story_authoring::origin_hash(&first).unwrap(),
        story_authoring::origin_hash(&second).unwrap()
    );
    let a = story_authoring::materialize(&first, scope()).unwrap();
    let b = story_authoring::materialize(&second, scope()).unwrap();
    assert_ne!(a.id, b.id);
    assert_eq!(a.initial_world.as_ref().unwrap().accepted, first.accepted);
    assert_eq!(b.initial_world.as_ref().unwrap().accepted, second.accepted);
    // Projection knowledge is a set, but it does not normalize the accepted provenance vectors.
    let logical_knowledge = |seed: &locallore::contracts::Seed, proposition: &str| -> BTreeSet<_> {
        let fact = seed
            .facts
            .values()
            .find(|fact| fact.proposition == proposition)
            .unwrap();
        fact.known_by
            .iter()
            .map(|id| seed.actors[id].name.clone())
            .collect()
    };
    // Derived item/location display prose legitimately embeds the new opaque IDs.
    // Compare the character/world visibility vectors whose ordering changed instead.
    for fact in &first.accepted.facts {
        assert_eq!(
            logical_knowledge(&a, &fact.text),
            logical_knowledge(&b, &fact.text)
        );
    }
    for character in &first.accepted.characters {
        let proposition = format!("Character {}: {}", character.name, character.description);
        assert_eq!(
            logical_knowledge(&a, &proposition),
            logical_knowledge(&b, &proposition)
        );
    }
    Engine::new(a).unwrap();
    Engine::new(b).unwrap();
}

#[test]
fn schema_portability_grants_no_mechanics_or_origin_bypass() {
    let origin = origin();
    let seed = story_authoring::materialize(&origin, scope()).unwrap();
    assert_eq!(seed.profile, Profile::NarrativeV1);
    assert!(seed.abilities.is_empty());
    assert!(seed
        .actors
        .values()
        .all(|actor| actor.energy == 0 && actor.abilities.is_empty()));
    Engine::new(seed.clone()).unwrap();
    let mut changed = seed.clone();
    changed.actors.get_mut(&changed.player).unwrap().energy = 100;
    assert!(Engine::new(changed).is_err());
    let mut stripped = seed;
    stripped.initial_world = None;
    assert!(Engine::new(stripped).is_err());
    let mut foreign: Value = serde_json::from_str(PROPOSAL).unwrap();
    foreign["abilities"] = json!(["grant-admin"]);
    assert!(serde_json::from_value::<InitialWorldProposalV1>(foreign).is_err());
}
