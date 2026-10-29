//! Exact production initial-world schema for the isolated LLGuidance oracle.
//! Synthetic fixtures only; no inference, files, model, SDK or database is opened.
use locallore::{
    inference::Input,
    story_authoring::{self, InitialStoryInputV1, InitialWorldProposalV1},
};
use serde::Serialize;
use serde_json::{json, Value};
use std::{collections::BTreeSet, io::Write};

type ExportResult<T> = Result<T, &'static str>;
const MAX_OUTPUT: usize = 131072;
const MAX_TEXT: usize = 16384;
const SCOPE: &str = "locallore_llguidance_oracle_v1";
const ASH_INPUT: &str = include_str!("../../../fixtures/initial_world/ashglass-input.json");
const ASH_WORLD: &str = include_str!("../../../fixtures/initial_world/ashglass-proposal.json");
const COPPER_INPUT: &str = include_str!("../../../fixtures/initial_world/copper-input.json");
const COPPER_WORLD: &str = include_str!("../../../fixtures/initial_world/copper-proposal.json");

#[derive(Serialize)]
struct Sample {
    id: String,
    json: String,
}
#[derive(Serialize)]
struct Case {
    id: String,
    schema_json: String,
    positives: Vec<Sample>,
    negatives: Vec<Sample>,
}
#[derive(Serialize)]
struct Corpus {
    version: u16,
    scope: &'static str,
    cases: Vec<Case>,
    refusals: Vec<Value>,
}
fn require(ok: bool) -> ExportResult<()> {
    if ok {
        Ok(())
    } else {
        Err("export_refused")
    }
}
fn sample(id: &str, value: &Value) -> ExportResult<Sample> {
    Ok(Sample {
        id: id.into(),
        json: serde_json::to_string(value).map_err(|_| "json")?,
    })
}
fn original(
    input: &str,
    world: &str,
) -> ExportResult<(InitialStoryInputV1, InitialWorldProposalV1)> {
    let input = serde_json::from_str(input).map_err(|_| "input")?;
    let world = serde_json::from_str(world).map_err(|_| "world")?;
    story_authoring::validate_proposal(&input, &world).map_err(|_| "invalid_original")?;
    Ok((input, world))
}
fn request_schema(input: &InitialStoryInputV1) -> ExportResult<Value> {
    let request = story_authoring::generation_request(input, "portable-author-v1", "oracle-proof")
        .map_err(|_| "request")?;
    require(
        request.budget.max_output_tokens == 1024
            && request.budget.max_output_bytes == 8192
            && request.budget.deadline_ms == 120000
            && request.budget.max_pending_polls == 24000,
    )?;
    match request.input {
        Input::Structured { role, schema, .. } if role == "author" => Ok(schema),
        _ => Err("structured_request"),
    }
}
fn full_case(
    schema: &Value,
    ash_input: &InitialStoryInputV1,
    ash: &InitialWorldProposalV1,
    copper: &InitialWorldProposalV1,
) -> ExportResult<Case> {
    let base = serde_json::to_value(ash).map_err(|_| "world_json")?;
    let mut reversed = ash.clone();
    reversed.characters[0].known_by = vec![1, 0];
    reversed.facts[0].known_by = vec![2, 1, 0];
    story_authoring::validate_proposal(ash_input, &reversed).map_err(|_| "ordered_world")?;
    let positives = vec![
        sample("ashglass", &base)?,
        sample(
            "copper-orchard",
            &serde_json::to_value(copper).map_err(|_| "world_json")?,
        )?,
        sample(
            "ordered-visibility",
            &serde_json::to_value(reversed).map_err(|_| "world_json")?,
        )?,
    ];
    let mut negatives = Vec::new();
    for (id, character, value) in [
        ("duplicate-character", true, json!([1, 1])),
        ("duplicate-fact", false, json!([0, 0])),
        ("out-of-range", false, json!([4])),
        ("string-reference", false, json!(["1"])),
        ("float-reference", false, json!([1.0])),
        ("fraction-reference", false, json!([1.5])),
    ] {
        let mut candidate = base.clone();
        candidate[if character { "characters" } else { "facts" }][0]["known_by"] = value;
        let typed = serde_json::from_value::<InitialWorldProposalV1>(candidate.clone());
        require(typed.map_or(true, |proposal| {
            story_authoring::validate_proposal(ash_input, &proposal).is_err()
        }))?;
        negatives.push(sample(id, &candidate)?);
    }
    let mut missing = base.clone();
    missing.as_object_mut().ok_or("object")?.remove("routes");
    negatives.push(sample("missing-routes", &missing)?);
    let mut foreign = base.clone();
    foreign["abilities"] = json!(["grant-admin"]);
    negatives.push(sample("foreign-mechanics", &foreign)?);
    let mut version = base.clone();
    version["version"] = json!(2);
    negatives.push(sample("foreign-version", &version)?);
    negatives.push(Sample {
        id: "malformed".into(),
        json: "{".into(),
    });
    let mut incomplete = positives[0].json.clone();
    incomplete.pop();
    negatives.push(Sample {
        id: "incomplete".into(),
        json: incomplete,
    });
    Ok(Case {
        id: "full-authoring-request".into(),
        schema_json: serde_json::to_string(schema).map_err(|_| "schema_json")?,
        positives,
        negatives,
    })
}

fn grammar_case(schema: &Value, character: bool) -> ExportResult<Case> {
    let node = &schema["properties"][if character { "characters" } else { "facts" }]["items"]
        ["properties"]["known_by"];
    require(node.is_object())?;
    let mut positives = Vec::new();
    // Independent base-four enumeration, not the schema's enum list. The grammar
    // domain includes all ordered distinct references0..3. Actual actor count and
    // a character knowing its own description remain native cross-field rules.
    for len in u32::from(character)..=4 {
        for mut code in 0..4_u32.pow(len) {
            let mut values = Vec::new();
            for _ in 0..len {
                values.push(code % 4);
                code /= 4;
            }
            if values.iter().collect::<BTreeSet<_>>().len() == values.len() {
                positives.push(sample(
                    &format!("ordered-{:03}", positives.len()),
                    &json!(values),
                )?);
            }
        }
    }
    let mut negatives = Vec::new();
    for (id, value) in [
        ("duplicate", json!([1, 1])),
        ("out-of-range", json!([4])),
        ("negative", json!([-1])),
        ("overlong", json!([0, 1, 2, 3, 0])),
        ("float", json!([1.0])),
        ("fraction", json!([1.5])),
        ("string", json!(["1"])),
        ("null", Value::Null),
        ("scalar", json!(0)),
    ] {
        negatives.push(sample(id, &value)?);
    }
    if character {
        negatives.push(sample("empty", &json!([]))?);
    }
    Ok(Case {
        id: if character {
            "character-known-by-grammar"
        } else {
            "fact-known-by-grammar"
        }
        .into(),
        schema_json: serde_json::to_string(node).map_err(|_| "node_json")?,
        positives,
        negatives,
    })
}
fn corpus() -> ExportResult<Corpus> {
    let (ash_input, ash) = original(ASH_INPUT, ASH_WORLD)?;
    let (copper_input, copper) = original(COPPER_INPUT, COPPER_WORLD)?;
    let schema = request_schema(&ash_input)?;
    require(
        schema == request_schema(&copper_input)? && schema == story_authoring::proposal_schema(),
    )?;
    Ok(Corpus {
        version: 1,
        scope: SCOPE,
        cases: vec![
            full_case(&schema, &ash_input, &ash, &copper)?,
            grammar_case(&schema, true)?,
            grammar_case(&schema, false)?,
        ],
        refusals: vec![],
    })
}
fn encode() -> ExportResult<Vec<u8>> {
    let corpus = corpus()?;
    require(!corpus.cases.is_empty() && corpus.cases.len() <= 16)?;
    let mut sample_count = 0;
    for case in &corpus.cases {
        require(
            !case.schema_json.is_empty()
                && case.schema_json.len() <= MAX_TEXT
                && !case.positives.is_empty()
                && !case.negatives.is_empty(),
        )?;
        let mut ids = BTreeSet::new();
        for sample in case.positives.iter().chain(&case.negatives) {
            require(
                ids.insert(&sample.id) && !sample.json.is_empty() && sample.json.len() <= MAX_TEXT,
            )?;
            sample_count += 1;
        }
    }
    require(sample_count <= 256)?;
    let encoded = serde_json::to_vec(&corpus).map_err(|_| "corpus_json")?;
    require(encoded.len() < MAX_OUTPUT)?;
    Ok(encoded)
}
fn main() {
    if std::env::args_os().nth(1).is_some() {
        eprintln!("initial_world_schema_cases: arguments_not_supported");
        std::process::exit(2);
    }
    match encode() {
        Ok(bytes) => {
            let mut out = std::io::stdout().lock();
            if out
                .write_all(&bytes)
                .and_then(|_| out.write_all(b"\n"))
                .is_err()
            {
                std::process::exit(1);
            }
        }
        Err(_) => {
            eprintln!("initial_world_schema_cases: export_failed");
            std::process::exit(1);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn export_is_deterministic_bounded_and_keeps_exact_production_schema() {
        let bytes = encode().unwrap();
        assert_eq!(bytes, encode().unwrap());
        assert!(bytes.len() < MAX_OUTPUT);
        let output: Value = serde_json::from_slice(&bytes).unwrap();
        assert_eq!(output["scope"], SCOPE);
        assert_eq!(output["cases"].as_array().unwrap().len(), 3);
        assert_eq!(output["refusals"], json!([]));
        let schema: Value =
            serde_json::from_str(output["cases"][0]["schema_json"].as_str().unwrap()).unwrap();
        assert_eq!(schema, story_authoring::proposal_schema());
    }
    #[test]
    fn grammar_only_permutation_cases_do_not_claim_cross_field_engine_eligibility() {
        let corpus = corpus().unwrap();
        for (case, count) in corpus.cases[1..].iter().zip([64, 65]) {
            assert!(case.id.ends_with("-grammar"));
            assert_eq!(case.positives.len(), count);
            let schema: Value = serde_json::from_str(&case.schema_json).unwrap();
            let actual: BTreeSet<_> = case
                .positives
                .iter()
                .map(|sample| sample.json.clone())
                .collect();
            let expected: BTreeSet<_> = schema["enum"]
                .as_array()
                .unwrap()
                .iter()
                .map(Value::to_string)
                .collect();
            assert_eq!(actual, expected);
            assert!(case.positives.iter().any(|sample| sample.json == "[1,0]"));
        }
        assert_eq!(corpus.cases[0].positives.len(), 3);
        assert_eq!(
            corpus
                .cases
                .iter()
                .map(|case| case.positives.len() + case.negatives.len())
                .sum::<usize>(),
            162
        );
    }
    #[test]
    fn full_schema_negatives_preserve_unknown_field_and_typed_boundaries() {
        let corpus = corpus().unwrap();
        let input: InitialStoryInputV1 = serde_json::from_str(ASH_INPUT).unwrap();
        for sample in &corpus.cases[0].negatives {
            let typed = serde_json::from_str::<InitialWorldProposalV1>(&sample.json);
            assert!(
                typed.map_or(true, |proposal| story_authoring::validate_proposal(
                    &input, &proposal
                )
                .is_err()),
                "{}",
                sample.id
            );
        }
    }
}
