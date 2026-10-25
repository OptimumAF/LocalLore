// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Dev-only corpus exporter. No LLGuidance dependency, prompt export, model or file IO.
//! Schemas are captured from actual production play requests; samples are original synthetics.
use locallore::{
    contracts::*,
    engine::Engine,
    inference::{Cancellation, GenerationRequest, InferenceProvider, Input},
    play::{self, PlayProfile},
};
use serde::Serialize;
use serde_json::{json, Value};
use std::{io::Write, task::Poll};

const SCOPE: &str = "locallore_llguidance_oracle_v1";
const MAX_OUTPUT_BYTES: usize = 1024 * 1024;
const QUESTION: &str = "Where is the tideglass relic?";
const ESCAPED: &str = "Hello \"Mira\" \\ 雪.\nIs the tideglass here?";

type ExportResult<T> = Result<T, &'static str>;

#[derive(Serialize)]
struct Corpus {
    version: u8,
    scope: &'static str,
    cases: Vec<Case>,
    refusals: Vec<Refusal>,
}
#[derive(Serialize)]
struct Case {
    id: String,
    schema_json: String,
    positives: Vec<Sample>,
    negatives: Vec<Sample>,
}
#[derive(Serialize)]
struct Sample {
    id: String,
    json: String,
}
#[derive(Serialize)]
struct Refusal {
    id: &'static str,
    error: &'static str,
    provider_calls: usize,
    canon_unchanged: bool,
}

fn require(condition: bool) -> ExportResult<()> {
    condition.then_some(()).ok_or("fixture_invariant")
}
fn seed() -> ExportResult<Seed> {
    serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json"))
        .map_err(|_| "fixture_seed")
}
fn profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-llguidance-oracle-v1".into(),
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
struct Capture {
    calls: usize,
    schema_json: Option<String>,
    unexpected_input: bool,
}
impl InferenceProvider for Capture {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        _: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        self.calls += 1;
        // Never retain or serialize the prompt, even for this public fixture.
        if let Input::Structured { role, schema, .. } = &request.input {
            if role == "director" && self.calls == 1 {
                self.schema_json = serde_json::to_string(schema).ok();
            } else {
                self.unexpected_input = true;
            }
        } else {
            self.unexpected_input = true;
        }
        Poll::Ready(Err(Error::Provider))
    }
}
struct Observation {
    error: Error,
    capture: Capture,
    canon_unchanged: bool,
}
fn observe(engine: &mut Engine, text: &str, profile: &PlayProfile) -> ExportResult<Observation> {
    let before = engine.canonical_bytes();
    let receipts = engine.receipts().len();
    let revision = engine.revision();
    let request = engine.request(
        "llguidance-schema-capture",
        Intent::FreeText {
            kind: PlayInputKind::Dialogue,
            text: text.into(),
        },
    );
    let mut capture = Capture::default();
    let error = play::execute(
        engine,
        &request,
        &mut capture,
        &Cancellation::default(),
        profile,
    )
    .err()
    .ok_or("unexpected_play_success")?;
    let canon_unchanged = engine.canonical_bytes() == before
        && engine.receipts().len() == receipts
        && engine.revision() == revision;
    require(canon_unchanged && !capture.unexpected_input)?;
    Ok(Observation {
        error,
        capture,
        canon_unchanged,
    })
}

fn engine(value: Seed) -> ExportResult<Engine> {
    Engine::new(value).map_err(|_| "fixture_engine")
}
fn crowd(count: usize) -> ExportResult<(Seed, Vec<String>)> {
    require(count <= 128)?;
    let mut value = seed()?;
    let template = value.actors.get("mira").ok_or("fixture_actor")?.clone();
    for (id, actor) in &mut value.actors {
        if id != &value.player {
            actor.location = "tower".into();
        }
    }
    let ids: Vec<_> = (0..count)
        .map(|index| format!("listener-{index:03}"))
        .collect();
    for id in &ids {
        let mut actor = template.clone();
        actor.location = "quay".into();
        actor.name = id.clone();
        value.actors.insert(id.clone(), actor);
    }
    let mut dead = template;
    dead.alive = false;
    dead.location = "quay".into();
    value.actors.insert("dead-listener".into(), dead);
    Ok((value, ids))
}
fn post_gift() -> ExportResult<Engine> {
    struct Gift {
        calls: usize,
        roles_match: bool,
    }
    impl InferenceProvider for Gift {
        fn poll(
            &mut self,
            request: &GenerationRequest,
            _: &Cancellation,
        ) -> Poll<Result<Vec<u8>, Error>> {
            let expected = match self.calls {
                0 => "director",
                1 => "narrator",
                _ => return Poll::Ready(Err(Error::Provider)),
            };
            self.roles_match &=
                matches!(&request.input, Input::Structured { role, .. } if role == expected);
            let output = if self.calls == 0 {
                json!({"commands":[{"op":"give","item":"potion","to":"mira","quantity":1}]})
            } else {
                // Existing original accepted prose from tests/play_v2.rs.
                json!({"text":"You place the potion in Mira's waiting hand, a small gesture of care.","event_ids":[1],"speaker":"narrator"})
            };
            self.calls += 1;
            Poll::Ready(serde_json::to_vec(&output).map_err(|_| Error::Provider))
        }
    }
    let mut engine = engine(seed()?)?;
    let request = engine.request(
        "llguidance-original-gift",
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: "I give my last potion to Mira.".into(),
        },
    );
    let mut provider = Gift {
        calls: 0,
        roles_match: true,
    };
    let receipt = play::execute(
        &mut engine,
        &request,
        &mut provider,
        &Cancellation::default(),
        &profile(),
    )
    .map_err(|_| "gift_play")?;
    require(engine.revision() == 1 && engine.receipts().len() == 1)?;
    require(provider.calls == 2 && provider.roles_match)?;
    require(engine.state().items["potion"].owner == "mira")?;
    let play = receipt.play().ok_or("gift_play_record")?;
    require(!play.fallback && play.repairs == 0)?;
    require(
        receipt.proposal().commands
            == vec![Command::Give {
                item: "potion".into(),
                to: "mira".into(),
                quantity: 1,
            }],
    )?;
    Ok(engine)
}

fn say(text: &str, audience: &[String]) -> Value {
    // The same production serde_json graph/order serializes schema and samples.
    json!({"commands":[{"op":"say","text":text,"audience":audience}]})
}
fn sample(id: &str, value: Value) -> ExportResult<Sample> {
    Ok(Sample {
        id: id.into(),
        json: serde_json::to_string(&value).map_err(|_| "sample_json")?,
    })
}
fn positives(text: &str, ids: &[String]) -> ExportResult<Vec<Sample>> {
    require(!ids.is_empty() && ids.len() <= 6)?;
    // Independent bitmask enumeration, not the production increasing-index DFS.
    (1u64..(1u64 << ids.len()))
        .filter(|mask| mask.count_ones() <= 4)
        .map(|mask| {
            let audience = ids
                .iter()
                .enumerate()
                .filter(|(index, _)| mask & (1u64 << index) != 0)
                .map(|(_, id)| id.clone())
                .collect::<Vec<_>>();
            sample(&format!("set-{mask}"), say(text, &audience))
        })
        .collect()
}
fn negatives(text: &str, ids: &[String], has_dead: bool) -> ExportResult<Vec<Sample>> {
    // Grammar representations only: do not invent engine duplicate/permutation/self rules.
    let mut samples = Vec::new();
    for (id, audience) in [
        ("empty-audience", vec![]),
        ("duplicate-audience", vec![ids[0].clone(), ids[0].clone()]),
        ("self-audience", vec!["player".into()]),
        ("remote-audience", vec!["sable".into()]),
        ("foreign-audience", vec!["unknown-listener".into()]),
    ] {
        samples.push(sample(id, say(text, &audience))?);
    }
    if ids.len() >= 2 {
        samples.push(sample(
            "permuted-audience",
            say(text, &[ids[1].clone(), ids[0].clone()]),
        )?);
    }
    if has_dead {
        samples.push(sample(
            "dead-audience",
            say(text, &["dead-listener".into()]),
        )?);
    }
    if ids.len() >= 5 {
        samples.push(sample("over-four-audience", say(text, &ids[..5]))?);
    }
    samples.push(sample(
        "wrong-op",
        json!({"commands":[{"op":"wait","ticks":1}]}),
    )?);
    samples.push(sample("wrong-text", say("Different literal.", &ids[..1]))?);
    samples.push(Sample {
        id: "malformed".into(),
        json: "{!".into(),
    });
    let complete = serde_json::to_string(&say(text, &ids[..1])).map_err(|_| "sample_json")?;
    samples.push(Sample {
        id: "incomplete".into(),
        json: complete.strip_suffix('}').ok_or("sample_suffix")?.into(),
    });
    Ok(samples)
}
fn case(
    id: &str,
    mut engine: Engine,
    text: &str,
    ids: &[String],
    has_dead: bool,
) -> ExportResult<Case> {
    let observation = observe(&mut engine, text, &profile())?;
    require(observation.error == Error::Provider && observation.capture.calls == 1)?;
    Ok(Case {
        id: id.into(),
        schema_json: observation.capture.schema_json.ok_or("missing_schema")?,
        positives: positives(text, ids)?,
        negatives: negatives(text, ids, has_dead)?,
    })
}
fn refusal(id: &'static str, count: usize, context: u32, expected: Error) -> ExportResult<Refusal> {
    let (value, _) = crowd(count)?;
    let mut engine = engine(value)?;
    let mut profile = profile();
    profile.context_tokens = context;
    let observation = observe(&mut engine, "Hello.", &profile)?;
    require(observation.error == expected && observation.capture.calls == 0)?;
    require(observation.capture.schema_json.is_none())?;
    let error = match observation.error {
        Error::ClarificationRequired => "ClarificationRequired",
        Error::TooLarge => "TooLarge",
        _ => return Err("unexpected_refusal"),
    };
    Ok(Refusal {
        id,
        error,
        provider_calls: 0,
        canon_unchanged: observation.canon_unchanged,
    })
}
fn corpus() -> ExportResult<Corpus> {
    let mut cases = vec![case(
        "ordinary-post-gift",
        post_gift()?,
        QUESTION,
        &["mira".into()],
        false,
    )?];
    for count in 1..=6 {
        let (value, ids) = crowd(count)?;
        cases.push(case(
            &format!("nearby-{count}"),
            engine(value)?,
            "Hello.",
            &ids,
            true,
        )?);
    }
    cases.push(case(
        "escaped-dialogue",
        engine(seed()?)?,
        ESCAPED,
        &["mira".into()],
        false,
    )?);
    Ok(Corpus {
        version: 1,
        scope: SCOPE,
        cases,
        refusals: vec![
            refusal("no-listener", 0, 4096, Error::ClarificationRequired)?,
            refusal("crowd-128", 128, 4096, Error::TooLarge)?,
            refusal("low-context-512", 1, 512, Error::TooLarge)?,
        ],
    })
}
fn encode(args: &[String]) -> ExportResult<Vec<u8>> {
    require(args.is_empty())?;
    let bytes = serde_json::to_vec(&corpus()?).map_err(|_| "corpus_json")?;
    require(bytes.len() < MAX_OUTPUT_BYTES)?; // Include the final CLI newline in the cap.
    Ok(bytes)
}
fn main() {
    // Reject even non-Unicode OS arguments without rendering or retaining their payload.
    if std::env::args_os().nth(1).is_some() {
        eprintln!("llguidance_cases: arguments_not_supported");
        std::process::exit(2);
    }
    match encode(&[]) {
        Ok(bytes) => {
            let mut stdout = std::io::stdout().lock();
            if stdout
                .write_all(&bytes)
                .and_then(|_| stdout.write_all(b"\n"))
                .is_err()
            {
                std::process::exit(1);
            }
        }
        Err(_) => {
            eprintln!("llguidance_cases: export_failed");
            std::process::exit(1);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::BTreeSet;

    fn audience(schema: &Value) -> &Value {
        &schema["properties"]["commands"]["items"]["oneOf"][0]["properties"]["audience"]
    }
    fn keys(value: &Value) -> BTreeSet<&str> {
        value
            .as_object()
            .unwrap()
            .keys()
            .map(String::as_str)
            .collect()
    }
    fn candidate_audience(sample: &Sample) -> Vec<String> {
        let value: Value = serde_json::from_str(&sample.json).unwrap();
        serde_json::from_value(value["commands"][0]["audience"].clone()).unwrap()
    }

    #[test]
    fn deterministic_bounded_corpus_has_only_frozen_wire_keys() {
        let first = encode(&[]).unwrap();
        assert_eq!(first, encode(&[]).unwrap());
        assert!(first.len() < MAX_OUTPUT_BYTES);
        let value: Value = serde_json::from_slice(&first).unwrap();
        assert_eq!(
            keys(&value),
            BTreeSet::from(["version", "scope", "cases", "refusals"])
        );
        assert_eq!(value["version"], 1);
        assert_eq!(value["scope"], SCOPE);
        assert_eq!(value["cases"].as_array().unwrap().len(), 8);
        for case in value["cases"].as_array().unwrap() {
            assert_eq!(
                keys(case),
                BTreeSet::from(["id", "schema_json", "positives", "negatives"])
            );
            for sample in case["positives"]
                .as_array()
                .unwrap()
                .iter()
                .chain(case["negatives"].as_array().unwrap())
            {
                assert_eq!(keys(sample), BTreeSet::from(["id", "json"]));
            }
        }
        for refusal in value["refusals"].as_array().unwrap() {
            assert_eq!(
                keys(refusal),
                BTreeSet::from(["id", "error", "provider_calls", "canon_unchanged"])
            );
        }
    }

    #[test]
    fn original_gift_is_committed_before_capture_and_schema_is_exact_425_bytes() {
        let mut engine = post_gift().unwrap();
        assert_eq!(engine.revision(), 1);
        assert_eq!(engine.receipts().len(), 1);
        let before = engine.canonical_bytes();
        let result = observe(&mut engine, QUESTION, &profile()).unwrap();
        assert_eq!(result.error, Error::Provider);
        assert_eq!(result.capture.calls, 1);
        assert_eq!(engine.canonical_bytes(), before);
        assert_eq!(engine.receipts().len(), 1);
        assert!(result.canon_unchanged);
        assert_eq!(result.capture.schema_json.unwrap().len(), 425);
    }

    #[test]
    fn independently_enumerated_samples_cover_every_semantic_set_for_one_to_six() {
        let corpus = corpus().unwrap();
        for (count, expected) in (1..=6).zip([1, 3, 7, 15, 30, 56]) {
            let case = &corpus.cases[count];
            assert_eq!(case.id, format!("nearby-{count}"));
            assert_eq!(case.positives.len(), expected);
            let sets = case
                .positives
                .iter()
                .map(candidate_audience)
                .collect::<BTreeSet<_>>();
            assert_eq!(sets.len(), expected);
            let schema: Value = serde_json::from_str(&case.schema_json).unwrap();
            let generated: BTreeSet<Vec<String>> =
                serde_json::from_value(audience(&schema)["enum"].clone()).unwrap();
            assert_eq!(sets, generated);
            assert!(sets.iter().all(|set| !set.is_empty()
                && set.len() <= 4
                && set.windows(2).all(|pair| pair[0] < pair[1])));
            assert!(sets
                .iter()
                .any(|set| set.contains(&format!("listener-{:03}", count - 1))));
        }
    }

    #[test]
    fn captured_schemas_keep_items_enum_lengths_single_say_and_literal_text() {
        for case in corpus().unwrap().cases {
            let schema: Value = serde_json::from_str(&case.schema_json).unwrap();
            let commands = &schema["properties"]["commands"];
            assert_eq!(commands["minItems"], 1);
            assert_eq!(commands["maxItems"], 1);
            assert_eq!(commands["items"]["oneOf"].as_array().unwrap().len(), 1);
            let variant = &commands["items"]["oneOf"][0];
            assert_eq!(variant["properties"]["op"]["const"], "say");
            assert_eq!(variant["additionalProperties"], false);
            assert_eq!(schema["additionalProperties"], false);
            assert_eq!(audience(&schema)["minItems"], 1);
            assert_eq!(audience(&schema)["maxItems"], 4);
            assert!(audience(&schema)["items"]["enum"].is_array());
            assert!(audience(&schema).get("uniqueItems").is_none());
            for positive in &case.positives {
                let value: Value = serde_json::from_str(&positive.json).unwrap();
                assert_eq!(
                    value["commands"][0]
                        .as_object()
                        .unwrap()
                        .keys()
                        .collect::<Vec<_>>(),
                    variant["properties"]
                        .as_object()
                        .unwrap()
                        .keys()
                        .collect::<Vec<_>>()
                );
                assert_eq!(
                    value["commands"][0]["text"],
                    variant["properties"]["text"]["const"]
                );
                assert_eq!(positive.json, serde_json::to_string(&value).unwrap());
            }
        }
    }

    #[test]
    fn representation_negatives_are_distinct_and_excluded_without_claiming_engine_refusal() {
        for case in corpus().unwrap().cases {
            let schema: Value = serde_json::from_str(&case.schema_json).unwrap();
            let allowed = audience(&schema)["enum"].as_array().unwrap();
            let ids = case
                .negatives
                .iter()
                .map(|sample| &sample.id)
                .collect::<BTreeSet<_>>();
            assert_eq!(ids.len(), case.negatives.len());
            for negative in &case.negatives {
                if negative.id.ends_with("-audience") {
                    let value: Value = serde_json::from_str(&negative.json).unwrap();
                    assert!(!allowed.contains(&value["commands"][0]["audience"]));
                }
                assert!(!case
                    .positives
                    .iter()
                    .any(|sample| sample.json == negative.json));
            }
            let malformed = case
                .negatives
                .iter()
                .find(|sample| sample.id == "malformed")
                .unwrap();
            let incomplete = case
                .negatives
                .iter()
                .find(|sample| sample.id == "incomplete")
                .unwrap();
            assert!(serde_json::from_str::<Value>(&malformed.json).is_err());
            assert!(serde_json::from_str::<Value>(&incomplete.json).is_err());
        }
    }

    #[test]
    fn refusal_controls_never_open_provider_or_change_canon() {
        let corpus = corpus().unwrap();
        let actual = corpus
            .refusals
            .iter()
            .map(|row| (row.id, row.error, row.provider_calls, row.canon_unchanged))
            .collect::<Vec<_>>();
        assert_eq!(
            actual,
            vec![
                ("no-listener", "ClarificationRequired", 0, true),
                ("crowd-128", "TooLarge", 0, true),
                ("low-context-512", "TooLarge", 0, true)
            ]
        );
    }

    #[test]
    fn escaped_literal_preserves_utf8_quotes_backslash_and_newline() {
        let corpus = corpus().unwrap();
        let case = corpus.cases.last().unwrap();
        assert_eq!(case.id, "escaped-dialogue");
        let schema: Value = serde_json::from_str(&case.schema_json).unwrap();
        assert_eq!(
            schema["properties"]["commands"]["items"]["oneOf"][0]["properties"]["text"]["const"],
            ESCAPED
        );
        let positive: Value = serde_json::from_str(&case.positives[0].json).unwrap();
        assert_eq!(positive["commands"][0]["text"], ESCAPED);
        assert!(case.schema_json.contains('雪'));
        assert!(case.schema_json.contains("\\n"));
    }

    #[test]
    fn unknown_arguments_refuse_without_corpus_and_cli_does_not_accept_paths() {
        for args in [
            vec!["--help".into()],
            vec!["private-path".into()],
            vec!["--schema".into(), "x".into()],
        ] {
            assert!(encode(&args).is_err());
        }
    }
}
