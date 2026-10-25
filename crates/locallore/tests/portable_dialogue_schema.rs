// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Synthetic providers only: portability preserves semantic audience sets, not array permutations.
use locallore::{
    contracts::*,
    engine::Engine,
    inference::{Cancellation, GenerationRequest, InferenceProvider, Input},
    play::{self, PlayProfile},
};
use serde_json::{json, Value};
use std::{
    collections::{BTreeSet, VecDeque},
    task::Poll,
};

fn seed() -> Seed {
    serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap()
}
fn profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-portable-dialogue".into(),
        model_sha256: "a".repeat(64),
        runtime_revision: "b".repeat(40),
        template_sha256: "c".repeat(64),
        worker_sha256: "d".repeat(64),
        profile_manifest_sha256: "e".repeat(64),
        context_tokens: 4096,
        director_tokens: 350,
        narrator_tokens: 220,
        deadline_ms: 1000,
        repair_limit: 1,
    }
}
#[derive(Default)]
struct Provider {
    output: VecDeque<Value>,
    requests: Vec<GenerationRequest>,
}
impl Provider {
    fn values(values: Vec<Value>) -> Self {
        Self {
            output: values.into(),
            ..Self::default()
        }
    }
}
impl InferenceProvider for Provider {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        _: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        self.requests.push(request.clone());
        Poll::Ready(
            self.output
                .pop_front()
                .map(|value| serde_json::to_vec(&value).unwrap())
                .ok_or(Error::Provider),
        )
    }
}
fn schema(request: &GenerationRequest) -> &Value {
    let Input::Structured { schema, .. } = &request.input else {
        panic!("Actual structured input required")
    };
    schema
}
fn crowd(count: usize) -> (Seed, Vec<String>) {
    let mut value = seed();
    let template = value.actors["mira"].clone();
    for (id, actor) in &mut value.actors {
        if id != &value.player {
            actor.location = "tower".into();
        }
    }
    let ids = (0..count)
        .map(|index| format!("listener-{index:03}"))
        .collect::<Vec<_>>();
    for id in &ids {
        let mut actor = template.clone();
        actor.location = "quay".into();
        actor.name = id.clone();
        value.actors.insert(id.clone(), actor);
    }
    (value, ids)
}
fn capture(value: Seed, text: &str) -> Value {
    let mut engine = Engine::new(value).unwrap();
    let before = engine.canonical_bytes();
    let request = engine.request(
        "schema-only",
        Intent::FreeText {
            kind: PlayInputKind::Dialogue,
            text: text.into(),
        },
    );
    let mut provider = Provider::default();
    assert_eq!(
        play::execute(
            &mut engine,
            &request,
            &mut provider,
            &Cancellation::default(),
            &profile()
        ),
        Err(Error::Provider)
    );
    assert_eq!(engine.canonical_bytes(), before);
    assert!(engine.receipts().is_empty());
    assert_eq!(provider.requests.len(), 1);
    schema(&provider.requests[0]).clone()
}
fn audience(schema: &Value) -> &Value {
    &schema["properties"]["commands"]["items"]["oneOf"][0]["properties"]["audience"]
}
fn choices(schema: &Value) -> Vec<Vec<String>> {
    serde_json::from_value(audience(schema)["enum"].clone()).unwrap()
}
fn reference(ids: &[String]) -> BTreeSet<Vec<String>> {
    // Independent bitmask enumeration, not the production depth-first combination algorithm.
    (1u64..(1u64 << ids.len()))
        .filter(|mask| mask.count_ones() <= 4)
        .map(|mask| {
            ids.iter()
                .enumerate()
                .filter(|(index, _)| mask & (1u64 << index) != 0)
                .map(|(_, id)| id.clone())
                .collect()
        })
        .collect()
}
fn has_keyword(value: &Value, keyword: &str) -> bool {
    match value {
        Value::Object(map) => {
            map.contains_key(keyword) || map.values().any(|value| has_keyword(value, keyword))
        }
        Value::Array(values) => values.iter().any(|value| has_keyword(value, keyword)),
        _ => false,
    }
}
fn say(text: &str, audience: Value) -> Value {
    json!({"commands":[{"op":"say","text":text,"audience":audience}]})
}
fn unsafe_prose() -> Value {
    json!({"text":"Sable knows SECRET-TIDE-731.","event_ids":[1],"speaker":"narrator"})
}

#[test]
fn exhaustive_one_to_six_listeners_preserve_every_set_up_to_four_in_sorted_order() {
    for count in 1..=6 {
        let (value, ids) = crowd(count);
        let first = capture(value.clone(), "Hello.");
        let second = capture(value, "Hello.");
        assert_eq!(first, second);
        let actual = choices(&first);
        let expected = reference(&ids);
        assert_eq!(actual, expected.iter().cloned().collect::<Vec<_>>());
        assert_eq!(actual.len(), actual.iter().collect::<BTreeSet<_>>().len());
        assert!(actual.iter().all(|set| !set.is_empty()
            && set.len() <= 4
            && set.windows(2).all(|pair| pair[0] < pair[1])));
        assert_eq!(audience(&first)["items"]["enum"], json!(ids));
        assert_eq!(audience(&first)["minItems"], 1);
        assert_eq!(audience(&first)["maxItems"], 4);
        assert!(!has_keyword(&first, "uniqueItems"));
        if count == 5 {
            assert_eq!(actual.len(), 30);
            assert!(actual.iter().any(|set| set.contains(&ids[4])));
        }
        if count == 6 {
            assert_eq!(actual.len(), 56);
        }
    }
}

#[test]
fn grammar_rejects_empty_duplicate_permuted_self_remote_dead_and_oversized_representations() {
    let (mut value, ids) = crowd(6);
    value.actors.get_mut("mira").unwrap().alive = false;
    value.actors.get_mut("mira").unwrap().location = "quay".into();
    let generated = capture(value, "Hello.");
    let allowed = audience(&generated)["enum"].as_array().unwrap();
    for invalid in [
        json!([]),
        json!([ids[0], ids[0]]),
        json!([ids[1], ids[0]]),
        json!(["player"]),
        json!(["sable"]),
        json!(["mira"]),
        json!(["unknown"]),
        json!(&ids[..5]),
    ] {
        assert!(!allowed.contains(&invalid));
    }
    assert!(allowed.contains(&json!([ids[0], ids[1], ids[2], ids[5]])));
}

#[test]
fn literal_escaped_speech_and_existing_closed_command_shape_remain_exact() {
    let text = "Hello \"Mira\" \\ 雪: uniqueItems is literal text, not a keyword.";
    let generated = capture(seed(), text);
    let commands = &generated["properties"]["commands"];
    assert_eq!(commands["minItems"], 1);
    assert_eq!(commands["maxItems"], 1);
    let variants = commands["items"]["oneOf"].as_array().unwrap();
    assert_eq!(variants.len(), 1);
    assert_eq!(variants[0]["properties"]["op"]["const"], "say");
    assert_eq!(variants[0]["properties"]["text"]["const"], text);
    assert_eq!(variants[0]["additionalProperties"], false);
    assert_eq!(generated["additionalProperties"], false);
    assert!(!has_keyword(&generated, "uniqueItems"));
    assert_eq!(audience(&generated)["enum"], json!([["mira"]]));
    assert!(serde_json::to_vec(&generated).unwrap().len() <= MAX_PROPOSAL_BYTES);
}

#[test]
fn canonical_schema_representation_does_not_change_existing_typed_set_normalization() {
    let command = |audience| {
        serde_json::from_value::<Command>(json!({"op":"say","text":"Hello.","audience":audience}))
            .unwrap()
    };
    assert_eq!(
        command(json!(["listener-001", "listener-000"])),
        command(json!(["listener-000", "listener-001"]))
    );
    assert_eq!(
        command(json!(["listener-000", "listener-000"])),
        command(json!(["listener-000"]))
    );
    // Duplicates/self are excluded by the generation schema; no new engine-array rule is claimed.
}

#[test]
fn all_four_supported_audience_sizes_still_commit_to_every_listener_and_replay() {
    let (value, ids) = crowd(5);
    for count in 1..=4 {
        let mut engine = Engine::new(value.clone()).unwrap();
        let request = engine.request(
            "speech",
            Intent::FreeText {
                kind: PlayInputKind::Dialogue,
                text: "Hello.".into(),
            },
        );
        let mut provider =
            Provider::values(vec![say("Hello.", json!(&ids[..count])), unsafe_prose()]);
        let receipt = play::execute(
            &mut engine,
            &request,
            &mut provider,
            &Cancellation::default(),
            &profile(),
        )
        .unwrap();
        assert_eq!(provider.requests.len(), 2);
        assert_eq!(engine.revision(), 1);
        assert_eq!(
            receipt.proposal().commands,
            vec![Command::Say {
                text: "Hello.".into(),
                audience: ids[..count].iter().cloned().collect()
            }]
        );
        for id in &ids[..count] {
            let context = engine.character_context(id, engine.scope(), 1).unwrap();
            assert!(serde_json::to_string(&context).unwrap().contains("Hello."));
        }
        assert!(!serde_json::to_string(
            &engine
                .character_context("sable", engine.scope(), 1)
                .unwrap()
        )
        .unwrap()
        .contains("Hello."));
        assert!(receipt.play().unwrap().fallback);
        assert!(!receipt.narration().contains("SECRET-TIDE-731"));
        let replayed = Engine::replay(value.clone(), engine.receipts()).unwrap();
        assert_eq!(replayed.canonical_bytes(), engine.canonical_bytes());
    }
}

#[test]
fn genuine_engine_literal_empty_remote_dead_and_command_guards_still_refuse_without_canon() {
    let (mut value, ids) = crowd(5);
    value.actors.get_mut("mira").unwrap().location = "quay".into();
    value.actors.get_mut("mira").unwrap().alive = false;
    let cases = [
        (say("Changed speech", json!([ids[0]])), Error::Agency),
        (say("Hello.", json!([])), Error::Agency),
        (say("Hello.", json!(["sable"])), Error::Location),
        (say("Hello.", json!(["mira"])), Error::DeadActor),
        (say("Hello.", json!(ids)), Error::Agency),
        (json!({"commands":[{"op":"wait","ticks":1}]}), Error::Agency),
    ];
    for (output, error) in cases {
        let mut engine = Engine::new(value.clone()).unwrap();
        let before = engine.canonical_bytes();
        let request = engine.request(
            "invalid",
            Intent::FreeText {
                kind: PlayInputKind::Dialogue,
                text: "Hello.".into(),
            },
        );
        let mut provider = Provider::values(vec![output]);
        assert_eq!(
            play::execute(
                &mut engine,
                &request,
                &mut provider,
                &Cancellation::default(),
                &profile()
            ),
            Err(error)
        );
        assert_eq!(provider.requests.len(), 1);
        assert_eq!(engine.canonical_bytes(), before);
        assert!(engine.receipts().is_empty());
    }
}

#[test]
fn crowded_complete_enumeration_refuses_before_provider_and_never_publishes_partial_schema() {
    let (value, _) = crowd(128);
    let mut engine = Engine::new(value).unwrap();
    let before = engine.canonical_bytes();
    let request = engine.request(
        "crowded",
        Intent::FreeText {
            kind: PlayInputKind::Dialogue,
            text: "Hello.".into(),
        },
    );
    let mut provider = Provider::default();
    assert_eq!(
        play::execute(
            &mut engine,
            &request,
            &mut provider,
            &Cancellation::default(),
            &profile()
        ),
        Err(Error::TooLarge)
    );
    assert!(provider.requests.is_empty());
    assert!(engine.receipts().is_empty());
    assert_eq!(engine.canonical_bytes(), before);
}

#[test]
fn existing_context_budget_can_refuse_even_a_small_complete_enum_without_provider() {
    let (value, _) = crowd(1);
    let mut engine = Engine::new(value).unwrap();
    let before = engine.canonical_bytes();
    let request = engine.request(
        "small-budget",
        Intent::FreeText {
            kind: PlayInputKind::Dialogue,
            text: "Hello.".into(),
        },
    );
    let mut small = profile();
    small.context_tokens = 512;
    let mut provider = Provider::default();
    assert_eq!(
        play::execute(
            &mut engine,
            &request,
            &mut provider,
            &Cancellation::default(),
            &small
        ),
        Err(Error::TooLarge)
    );
    assert!(provider.requests.is_empty());
    assert_eq!(engine.canonical_bytes(), before);
}

#[test]
fn no_eligible_listener_keeps_clarification_refusal_without_provider() {
    let (value, _) = crowd(0);
    let mut engine = Engine::new(value).unwrap();
    let before = engine.canonical_bytes();
    let request = engine.request(
        "alone",
        Intent::FreeText {
            kind: PlayInputKind::Dialogue,
            text: "Hello.".into(),
        },
    );
    let mut provider = Provider::default();
    assert_eq!(
        play::execute(
            &mut engine,
            &request,
            &mut provider,
            &Cancellation::default(),
            &profile()
        ),
        Err(Error::ClarificationRequired)
    );
    assert!(provider.requests.is_empty());
    assert_eq!(engine.canonical_bytes(), before);
}
