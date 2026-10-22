//! Synthetic, bounded stdin/stdout oracle for the development-only runtime spike.
//! Model text is never an event or a trusted request. No state is persisted.
use locallore::{contracts::*, engine::Engine};
use serde::Deserialize;
use serde_json::{json, Value};
use std::io::{self, Read};

fn setup(case: &str) -> Result<(Engine, Request), Error> {
    let seed: Seed = serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json"))
        .map_err(|_| Error::Malformed)?;
    let mut engine = Engine::new(seed)?;
    let gift = Command::Give {
        item: "potion".into(),
        to: "mira".into(),
        quantity: 1,
    };
    if case == "spent" {
        let request = engine.request("spike-first-gift", Intent::Actions(vec![gift.clone()]));
        let proposal = Engine::proposal(&request)?;
        let preview = engine.preview(&request, &proposal)?;
        engine.commit(&request, &proposal, preview.narration())?;
    }
    let command = match case {
        "gift" | "spent" => gift,
        "unlearned" => Command::UseAbility {
            ability: "blink".into(),
        },
        _ => return Err(Error::Rule),
    };
    let request = engine.request("spike-request", Intent::Actions(vec![command]));
    Ok((engine, request))
}

fn preflight(engine: &Engine, request: &Request) -> Result<(), Error> {
    engine.preflight(request)?;
    engine.preview(request, &Engine::proposal(request)?)?;
    Ok(())
}

fn schema(request: &Request) -> Value {
    // This experiment admits one selected Give action; it is not the complete v1 command schema.
    json!({
        "type":"object", "additionalProperties":false,
        "required":["version","scope","turn","expected_revision","commands"],
        "properties":{
            "version":{"type":"integer","const":VERSION},
            "scope":{"type":"object","additionalProperties":false,"required":["story","branch"],
                "properties":{"story":{"type":"string","const":request.scope.story},
                              "branch":{"type":"string","const":request.scope.branch}}},
            "turn":{"type":"string","const":request.turn},
            "expected_revision":{"type":"integer","const":request.expected_revision},
            "commands":{"type":"array","minItems":1,"maxItems":1,"items":{
                "type":"object","additionalProperties":false,"required":["op","item","to","quantity"],
                "properties":{"op":{"type":"string","const":"give"},"item":{"type":"string"},
                    "to":{"type":"string"},"quantity":{"type":"integer","minimum":1,"maximum":65535}}}}
        }
    })
}

fn role(role: &str, prompt: String, schema: Value) -> Value {
    json!({"version":1,"role":role,"prompt":prompt,"schema":schema,
           "max_tokens":if role == "director" {350} else {220},"context_tokens":4096,"threads":4})
}

fn fixture(case: &str) -> Result<Value, Error> {
    let (engine, request) = setup(case)?;
    if let Err(error) = preflight(&engine, &request) {
        return Ok(
            json!({"version":1,"case":case,"preflight_error":error.to_string(),
                         "revision":engine.revision(),"director":null}),
        );
    }
    let context =
        engine.character_context(&engine.seed().player, &request.scope, engine.revision())?;
    let prompt = format!(
        "Return only one LocalLore Proposal v1 JSON object, with no markdown or explanation. \
         The trusted request selects the authorized action. Copy its version, scope, turn and \
         expected_revision; propose only its authorized commands. Never execute tools or invent \
         facts, rewards, powers, identity or history. Character beliefs are not world truth.\n\
         Trusted request:\n{}\nObserver-filtered context:\n{}\nRequired JSON schema:\n{}",
        serde_json::to_string(&request).map_err(|_| Error::Malformed)?,
        serde_json::to_string(&context).map_err(|_| Error::Malformed)?,
        schema(&request)
    );
    Ok(
        json!({"version":1,"case":case,"preflight_error":null,"revision":engine.revision(),
              "director":role("director",prompt,schema(&request))}),
    )
}

fn validate(case: &str, bytes: &[u8]) -> Result<Value, Error> {
    let (engine, request) = setup(case)?;
    let before = engine.canonical_bytes();
    preflight(&engine, &request)?;
    let proposal = Proposal::parse(bytes)?;
    let preview = engine.preview(&request, &proposal)?;
    let prompt = format!(
        "This is an exact-render compatibility test, not a creative-writing task. Return ONLY \
         the accepted public description below, byte-for-byte, without quotes, markdown, \
         explanation, new facts or hidden reasoning.\nAccepted public description:\n{}",
        preview.narration()
    );
    Ok(json!({"version":1,"status":"accepted","error":null,
              "canonical_unchanged":engine.canonical_bytes()==before,
              "narrator":role("narrator",prompt,Value::Null)}))
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Completion {
    proposal: String,
    narration: String,
}

fn commit(case: &str, bytes: &[u8]) -> Result<Value, Error> {
    let input: Completion = serde_json::from_slice(bytes).map_err(|_| Error::Malformed)?;
    if input.narration.len() > MAX_TEXT_BYTES {
        return Err(Error::TooLarge);
    }
    let (mut engine, request) = setup(case)?;
    preflight(&engine, &request)?;
    let proposal = Proposal::parse(input.proposal.as_bytes())?;
    engine.commit(&request, &proposal, &input.narration)?;
    let committed = engine.canonical_bytes();
    // A retry returns the same receipt rather than spending the item a second time.
    engine.commit(&request, &proposal, &input.narration)?;
    let mira = engine.character_context("mira", engine.scope(), engine.revision())?;
    let absent = engine.character_context("sable", engine.scope(), engine.revision())?;
    Ok(
        json!({"version":1,"status":"committed","error":null,"revision":engine.revision(),
              "events":engine.receipts().iter().map(|r|r.events().len()).sum::<usize>(),
              "exact_retry_unchanged":engine.canonical_bytes()==committed,
              "recipient_observations":mira.observations.len(),"absent_observations":absent.observations.len()}),
    )
}

fn dispatch(mode: &str, case: &str, bytes: &[u8]) -> Value {
    let result = match mode {
        "fixture" => fixture(case),
        "validate" => validate(case, bytes),
        "commit" => commit(case, bytes),
        _ => Err(Error::Rule),
    };
    result.unwrap_or_else(|error| {
        json!({"version":1,"status":"rejected","error":error.to_string(),
                                       "state_retained":false})
    })
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let mut input = vec![];
    let output = if args.len() != 3 || io::stdin().take(131_073).read_to_end(&mut input).is_err() {
        json!({"version":1,"status":"rejected","error":"Malformed","state_retained":false})
    } else if input.len() > 131_072 {
        json!({"version":1,"status":"rejected","error":"TooLarge","state_retained":false})
    } else {
        dispatch(&args[1], &args[2], &input)
    };
    println!("{output}");
}

#[cfg(test)]
mod tests {
    use super::*;
    fn proposal() -> Value {
        let (_, request) = setup("gift").unwrap();
        serde_json::to_value(Engine::proposal(&request).unwrap_or_else(|_| panic!("valid intent")))
            .unwrap_or_else(|_| panic!("valid JSON"))
    }
    #[test]
    fn observer_context_and_narrator_boundary_precede_model_input() {
        let director = fixture("gift").unwrap();
        assert!(director["director"]["prompt"]
            .as_str()
            .unwrap()
            .contains("SECRET-TIDE-731")); // player knows
        let validated = validate("gift", proposal().to_string().as_bytes()).unwrap();
        let narrator = validated["narrator"]["prompt"].as_str().unwrap();
        assert!(
            !narrator.contains("SECRET-TIDE-731") && !narrator.contains("ordinary quay keepers")
        );
        assert_eq!(validated["canonical_unchanged"], true);
    }
    #[test]
    fn forged_scope_revision_agency_and_unknown_fields_fail_closed() {
        for (field, value, error) in [
            ("scope", json!({"story":"other","branch":"main"}), "Scope"),
            ("expected_revision", json!(9), "Stale"),
            ("extra", json!(1), "Malformed"),
            (
                "commands",
                json!([{"op":"grant","ability":"blink"}]),
                "Malformed",
            ),
            (
                "commands",
                json!([{"op":"give","item":"brass-key","to":"mira","quantity":1}]),
                "Agency",
            ),
        ] {
            let mut forged = proposal();
            forged[field] = value;
            let result = dispatch("validate", "gift", forged.to_string().as_bytes());
            assert_eq!(result["error"], error);
            assert_eq!(result["state_retained"], false);
        }
    }
    #[test]
    fn invalid_intents_never_receive_a_director_request() {
        for (case, error) in [("spent", "Inventory"), ("unlearned", "Ability")] {
            let result = fixture(case).unwrap();
            assert_eq!(result["preflight_error"], error);
            assert!(result["director"].is_null());
        }
    }
    #[test]
    fn narrative_cannot_override_engine_and_exact_retry_is_idempotent() {
        let proposed = proposal().to_string();
        let wrong = json!({"proposal":proposed,"narration":"A golden crown appears."});
        assert_eq!(
            dispatch("commit", "gift", wrong.to_string().as_bytes())["error"],
            "Narration"
        );
        let exact = json!({"proposal":proposed,"narration":"You give 1 potion to mira."});
        let result = commit("gift", exact.to_string().as_bytes()).unwrap();
        assert_eq!(result["revision"], 1);
        assert_eq!(result["events"], 1);
        assert_eq!(result["exact_retry_unchanged"], true);
        assert_eq!(result["recipient_observations"], 1);
        assert_eq!(result["absent_observations"], 0);
    }
    #[test]
    fn malformed_numeric_and_oversize_generation_are_rejected() {
        let mut wrong = proposal();
        wrong["commands"][0]["quantity"] = json!(1.5);
        assert_eq!(
            dispatch("validate", "gift", wrong.to_string().as_bytes())["error"],
            "Malformed"
        );
        assert_eq!(
            dispatch("validate", "gift", &vec![b'x'; MAX_PROPOSAL_BYTES + 1])["error"],
            "TooLarge"
        );
    }
}
