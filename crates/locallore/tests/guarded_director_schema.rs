use locallore::{
    contracts::*,
    engine::Engine,
    inference::*,
    intent_guard,
    play::{self, PlayProfile},
};
use serde_json::{json, Value};
use std::{collections::VecDeque, task::Poll};

fn engine() -> Engine {
    Engine::new(serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap())
        .unwrap()
}
fn profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-schema".into(),
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
struct Script {
    replies: VecDeque<Vec<u8>>,
    seen: Vec<GenerationRequest>,
    cancel_on_poll: bool,
}
impl Script {
    fn values(values: Vec<Value>) -> Self {
        Self {
            replies: values
                .into_iter()
                .map(|v| serde_json::to_vec(&v).unwrap())
                .collect(),
            ..Self::default()
        }
    }
}
impl InferenceProvider for Script {
    fn poll(&mut self, r: &GenerationRequest, c: &Cancellation) -> Poll<Result<Vec<u8>, Error>> {
        self.seen.push(r.clone());
        if self.cancel_on_poll {
            c.cancel();
        }
        Poll::Ready(self.replies.pop_front().ok_or(Error::Provider))
    }
}
fn request(e: &Engine, text: &str) -> Request {
    e.request(
        "guarded-schema",
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: text.into(),
        },
    )
}
fn schema(r: &GenerationRequest) -> &Value {
    let Input::Structured { schema, .. } = &r.input else {
        panic!("actual structured generation request")
    };
    schema
}
fn gift() -> Value {
    json!({"commands":[{"op":"give","item":"potion","to":"mira","quantity":1}]})
}
fn prose() -> Value {
    json!({"text":"You pass the potion to Mira with care.","event_ids":[1],"speaker":"narrator"})
}
fn commit(e: &mut Engine, command: Command) {
    let r = e.request("synthetic-setup", Intent::Actions(vec![command]));
    let p = Engine::proposal(&r).unwrap();
    let n = e.preview(&r, &p).unwrap().narration().to_owned();
    e.commit(&r, &p, &n).unwrap();
}

#[test]
fn actual_guarded_requests_bind_every_action_argument_and_emit_native_converter_cases() {
    let mut cases = vec![];
    for text in [
        "give my sole potion to Mira",
        "give 2 potion to mira",
        "drink potion",
        "use ability steady",
        "learn beacon",
        "go to pier",
        "wait 100 ticks",
        "discover fact beacon-mark",
        "believe claim event 1",
    ] {
        let mut e = engine();
        if text.contains("2 potion") {
            let mut seed = e.seed().clone();
            seed.items.get_mut("potion").unwrap().quantity = 2;
            e = Engine::new(seed).unwrap();
        }
        if text.starts_with("discover") {
            commit(
                &mut e,
                Command::Move {
                    to: "dry-well".into(),
                },
            );
        }
        if text.starts_with("believe") {
            commit(
                &mut e,
                Command::Say {
                    text: "A synthetic spoken claim".into(),
                    audience: ["mira".into()].into(),
                },
            );
        }
        let expected = intent_guard::compile_action(&e, text).unwrap();
        let r = request(&e, text);
        let before = e.canonical_bytes();
        let mut p = Script::default();
        assert_eq!(
            play::execute(&mut e, &r, &mut p, &Cancellation::default(), &profile()),
            Err(Error::Provider),
            "{text}"
        );
        assert_eq!(before, e.canonical_bytes());
        assert_eq!(p.seen.len(), 1);
        let s = schema(&p.seen[0]);
        assert_eq!(s["properties"]["commands"]["minItems"], 1);
        assert_eq!(s["properties"]["commands"]["maxItems"], 1);
        let variants = s["properties"]["commands"]["items"]["oneOf"]
            .as_array()
            .unwrap();
        assert_eq!(variants.len(), 1);
        let expected = serde_json::to_value(expected).unwrap();
        let fields = expected.as_object().unwrap();
        assert_eq!(variants[0]["additionalProperties"], false);
        assert_eq!(
            variants[0]["properties"].as_object().unwrap().len(),
            fields.len()
        );
        assert_eq!(
            variants[0]["required"].as_array().unwrap().len(),
            fields.len()
        );
        for (key, value) in fields {
            assert_eq!(
                &variants[0]["properties"][key]["const"], value,
                "{text}:{key}"
            );
        }
        assert_eq!(p.seen[0].budget.max_output_tokens, 350);
        assert_eq!(p.seen[0].budget.max_output_bytes, MAX_PROPOSAL_BYTES);
        assert_eq!(profile().context_tokens, 4096);
        let valid = json!({"commands":[expected.clone()]});
        let mut invalid = vec![
            json!({"commands":[]}),
            json!({"commands":[expected.clone(),expected.clone()]}),
            json!({"commands":[expected.clone()],"extra":true}),
        ];
        for (key, value) in fields {
            let mut changed = expected.clone();
            changed[key] = if value.is_string() {
                json!("different-valid-id")
            } else {
                json!(value.as_u64().unwrap() + 1)
            };
            invalid.push(json!({"commands":[changed]}));
        }
        let mut extra = expected.clone();
        extra["extra"] = json!(true);
        invalid.push(json!({"commands":[extra]}));
        cases.push(json!({"label":text,"schema":s,"valid":valid,"invalid":invalid}));
    }
    // Existing Dialogue remains literal speech, with a present-audience choice, not an action.
    let mut e = engine();
    let text = "Hello \"Mira\" \\ quietly";
    let r = e.request(
        "dialogue-schema",
        Intent::FreeText {
            kind: PlayInputKind::Dialogue,
            text: text.into(),
        },
    );
    let mut p = Script::default();
    assert_eq!(
        play::execute(&mut e, &r, &mut p, &Cancellation::default(), &profile()),
        Err(Error::Provider)
    );
    cases.push(json!({"label":"unchanged-dialogue","schema":schema(&p.seen[0]),
        "valid":{"commands":[{"op":"say","text":text,"audience":["mira"]}]},
        "invalid":[{"commands":[{"op":"say","text":"changed","audience":["mira"]}]},{"commands":[{"op":"say","text":text,"audience":["oren"]}]}]}));
    if let Some(path) = std::env::var_os("LOCALLORE_GUARDED_SCHEMA_OUTPUT") {
        std::fs::write(
            path,
            serde_json::to_vec_pretty(
                &json!({"synthetic":true,"prompt_version":play::PROMPT_VERSION,"cases":cases}),
            )
            .unwrap(),
        )
        .unwrap();
    }
}

#[test]
fn provider_bytes_are_never_replaced_even_when_schema_has_only_one_command() {
    for wrong in [
        json!({"commands":[{"op":"wait","ticks":1}]}),
        json!({"commands":[{"op":"consume","item":"potion"}]}),
        json!({"commands":[{"op":"give","item":"brass-key","to":"mira","quantity":1}]}),
        json!({"commands":[{"op":"give","item":"potion","to":"player","quantity":1}]}),
        json!({"commands":[{"op":"give","item":"potion","to":"mira","quantity":2}]}),
    ] {
        let mut e = engine();
        let r = request(&e, "give potion to Mira");
        let before = e.canonical_bytes();
        let mut p = Script::values(vec![wrong]);
        assert_eq!(
            play::execute(&mut e, &r, &mut p, &Cancellation::default(), &profile()),
            Err(Error::Agency)
        );
        assert_eq!(p.seen.len(), 1);
        assert_eq!(e.canonical_bytes(), before);
    }
    let mut e = engine();
    let r = request(&e, "give potion to Mira");
    let before = e.canonical_bytes();
    let mut p = Script::default();
    assert_eq!(
        play::execute(&mut e, &r, &mut p, &Cancellation::default(), &profile()),
        Err(Error::Provider)
    );
    assert_eq!(e.canonical_bytes(), before);
}

#[test]
fn unsupported_ambiguous_and_mechanically_invalid_attempts_still_spend_zero_roles() {
    for (text, error) in [
        (
            "give potion to Mira and wait 1 tick",
            Error::ClarificationRequired,
        ),
        ("I do not give potion to Mira", Error::ClarificationRequired),
        ("I teleport to tower", Error::ClarificationRequired),
        ("use ability teleport", Error::Ability),
        ("give 2 potion to Mira", Error::Inventory),
        ("move to tower", Error::Location),
        ("give Potion to Mira", Error::Inventory),
    ] {
        let mut e = engine();
        let r = request(&e, text);
        let before = e.canonical_bytes();
        let mut p = Script::default();
        assert_eq!(
            play::execute(&mut e, &r, &mut p, &Cancellation::default(), &profile()),
            Err(error),
            "{text}"
        );
        assert!(p.seen.is_empty());
        assert_eq!(e.canonical_bytes(), before);
    }
    let mut seed = engine().seed().clone();
    for id in ["oren", "sable"] {
        seed.actors.get_mut(id).unwrap().location = "quay".into();
    }
    let mut e = Engine::new(seed).unwrap();
    let r = request(&e, "give potion to Oren");
    let mut p = Script::default();
    assert_eq!(
        play::execute(&mut e, &r, &mut p, &Cancellation::default(), &profile()),
        Err(Error::ClarificationRequired)
    );
    assert!(p.seen.is_empty());
}

#[test]
fn bounded_repair_keeps_same_request_schema_and_cancellation_never_commits() {
    let mut e = engine();
    let r = request(&e, "give potion to Mira");
    let mut p = Script::values(vec![gift(), prose()]);
    p.replies.push_front(b"{".to_vec());
    let receipt = play::execute(&mut e, &r, &mut p, &Cancellation::default(), &profile()).unwrap();
    assert_eq!(receipt.play().unwrap().repairs, 1);
    assert_eq!(
        receipt.play().unwrap().prompt_version,
        "locallore-play-v2.4"
    );
    assert_eq!(schema(&p.seen[0]), schema(&p.seen[1]));
    assert_eq!(p.seen.len(), 3);
    assert_eq!(p.seen[2].budget.max_output_tokens, 220);
    for cancel_on_poll in [false, true] {
        let mut e = engine();
        let r = request(&e, "give potion to Mira");
        let before = e.canonical_bytes();
        let mut p = Script::values(vec![gift()]);
        p.cancel_on_poll = cancel_on_poll;
        let cancel = Cancellation::default();
        if !cancel_on_poll {
            cancel.cancel();
        }
        assert_eq!(
            play::execute(&mut e, &r, &mut p, &cancel, &profile()),
            Err(Error::Cancelled)
        );
        assert_eq!(p.seen.len(), usize::from(cancel_on_poll));
        assert_eq!(e.canonical_bytes(), before);
    }
    let mut e = engine();
    let r = request(&e, "give potion to Mira");
    let before = e.canonical_bytes();
    let mut p = Script {
        replies: VecDeque::from([b"{".to_vec(), b"{".to_vec()]),
        ..Script::default()
    };
    assert_eq!(
        play::execute(&mut e, &r, &mut p, &Cancellation::default(), &profile()),
        Err(Error::Malformed)
    );
    assert_eq!(p.seen.len(), 2);
    assert_eq!(e.canonical_bytes(), before);
}

#[test]
fn frozen_actual_v22_history_restores_forks_and_retries_without_becoming_a_fresh_commit() {
    let fixture: Value =
        serde_json::from_str(include_str!("fixtures/accepted_play_v2_2.json")).unwrap();
    assert_eq!(
        fixture["source_commit"],
        "8120b422c6dbd41a7ec6b0ddecc71863a756f3c9"
    );
    assert_eq!(fixture["synthetic"], true);
    assert_eq!(fixture["provider_calls"], 2);
    let seed: Seed = serde_json::from_value(fixture["seed"].clone()).unwrap();
    let mut restored = Engine::restore(seed.clone(), &[fixture["receipt"].to_string()]).unwrap();
    let receipt = restored.receipts()[0].clone();
    assert_eq!(serde_json::to_value(&receipt).unwrap(), fixture["receipt"]);
    assert_eq!(
        receipt.play().unwrap().prompt_version,
        "locallore-play-v2.2"
    );
    let before = restored.canonical_bytes();
    assert_eq!(
        Engine::replay(seed.clone(), restored.receipts())
            .unwrap()
            .canonical_bytes(),
        before
    );
    let child = restored.fork("v22-child", restored.revision()).unwrap();
    assert_eq!(child.receipts(), restored.receipts());
    assert_eq!(child.state(), restored.state());
    let mut p = Script::default();
    assert_eq!(
        play::execute(
            &mut restored,
            receipt.request(),
            &mut p,
            &Cancellation::default(),
            &profile()
        )
        .unwrap(),
        receipt
    );
    assert!(p.seen.is_empty());
    assert_eq!(restored.canonical_bytes(), before);
    let current = restored.request(
        "after-v22",
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: "wait 1 tick".into(),
        },
    );
    let mut p = Script::values(vec![
        json!({"commands":[{"op":"wait","ticks":1}]}),
        json!({"text":"Time passes.","event_ids":[2],"speaker":"narrator"}),
    ]);
    let new = play::execute(
        &mut restored,
        &current,
        &mut p,
        &Cancellation::default(),
        &profile(),
    )
    .unwrap();
    assert_eq!(new.play().unwrap().prompt_version, play::PROMPT_VERSION);
    assert_eq!(
        serde_json::to_value(&restored.receipts()[0]).unwrap(),
        fixture["receipt"],
        "new turns never rewrite old provenance"
    );
    let mixed: Vec<_> = restored
        .receipts()
        .iter()
        .map(|r| serde_json::to_string(r).unwrap())
        .collect();
    assert_eq!(
        Engine::restore(seed.clone(), &mixed)
            .unwrap()
            .canonical_bytes(),
        restored.canonical_bytes()
    );
    assert_eq!(
        Engine::replay(seed.clone(), restored.receipts())
            .unwrap()
            .canonical_bytes(),
        restored.canonical_bytes()
    );
    let mut child_after = child.clone();
    let r = request(&child_after, "wait 1 tick");
    let mut p = Script::values(vec![
        json!({"commands":[{"op":"wait","ticks":1}]}),
        json!({"text":"Time passes.","event_ids":[2],"speaker":"narrator"}),
    ]);
    let local = play::execute(
        &mut child_after,
        &r,
        &mut p,
        &Cancellation::default(),
        &profile(),
    )
    .unwrap();
    let continued = child
        .restore_continuation(&[serde_json::to_string(&local).unwrap()])
        .unwrap();
    assert_eq!(continued.canonical_bytes(), child_after.canonical_bytes());
    assert_eq!(continued.receipts()[0], receipt);
    let mut fresh = Engine::new(seed.clone()).unwrap();
    let before = fresh.canonical_bytes();
    assert_eq!(fresh.commit_prepared(&receipt), Err(Error::Narration));
    assert_eq!(fresh.canonical_bytes(), before);
    for version in [
        "locallore-play-v2.0",
        "locallore-play-v2.5",
        "locallore-play-v9",
    ] {
        let mut bad = fixture["receipt"].clone();
        bad["play"]["prompt_version"] = json!(version);
        assert_eq!(
            Engine::restore(seed.clone(), &[bad.to_string()]).err(),
            Some(Error::CorruptHistory)
        );
    }
    let mut bad = fixture["receipt"].clone();
    bad["events"][0]["outcome"]["quantity"] = json!(2);
    assert!(Engine::restore(seed, &[bad.to_string()]).is_err());
}
