// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent adversarial integration review; all providers below are synthetic.
use locallore::{
    contracts::*,
    engine::Engine,
    inference::{Cancellation, GenerationRequest, InferenceProvider, Input},
    play::{self, PlayProfile},
};
use serde_json::{json, Value};
use std::{collections::VecDeque, task::Poll};

fn seed() -> Seed {
    serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap()
}
fn profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-independent-schema".into(),
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
    output: VecDeque<Vec<u8>>,
    requests: Vec<GenerationRequest>,
    cancel_at: Option<usize>,
}
impl Provider {
    fn values(values: Vec<Value>) -> Self {
        Self {
            output: values
                .into_iter()
                .map(|v| serde_json::to_vec(&v).unwrap())
                .collect(),
            ..Self::default()
        }
    }
}
impl InferenceProvider for Provider {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        cancel: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        self.requests.push(request.clone());
        if self.cancel_at == Some(self.requests.len()) {
            cancel.cancel();
        }
        Poll::Ready(self.output.pop_front().ok_or(Error::Provider))
    }
}
fn schema(request: &GenerationRequest) -> &Value {
    let Input::Structured { schema, .. } = &request.input else {
        panic!("real structured request required")
    };
    schema
}
fn prose() -> Value {
    json!({"text":"You pass the potion to Mira.","event_ids":[1],"speaker":"narrator"})
}
fn gift(quantity: u16) -> Value {
    json!({"commands":[{"op":"give","item":"potion","quantity":quantity,"to":"mira"}]})
}
fn request(engine: &Engine, kind: PlayInputKind, text: &str) -> Request {
    engine.request(
        "independent-schema",
        Intent::FreeText {
            kind,
            text: text.into(),
        },
    )
}

#[test]
fn largest_stack_and_case_insensitive_visible_alias_bind_exact_child_attempt() {
    let mut seed = seed();
    seed.items.get_mut("potion").unwrap().quantity = u16::MAX;
    let mut parent = Engine::new(seed).unwrap();
    let mut child = parent.fork("alternate", 0).unwrap();
    let movement = parent.request(
        "parent-future",
        Intent::Actions(vec![Command::Move { to: "pier".into() }]),
    );
    let proposal = Engine::proposal(&movement).unwrap();
    let narration = parent
        .preview(&movement, &proposal)
        .unwrap()
        .narration()
        .to_owned();
    parent.commit(&movement, &proposal, &narration).unwrap();
    let parent_before = parent.canonical_bytes();
    let r = request(&child, PlayInputKind::Action, "give 65535 potion to MIRA");
    let mut provider = Provider::values(vec![gift(u16::MAX), prose()]);
    let receipt = play::execute(
        &mut child,
        &r,
        &mut provider,
        &Cancellation::default(),
        &profile(),
    )
    .unwrap();
    assert_eq!(
        provider.requests.len(),
        2,
        "both actual provider stages remain necessary"
    );
    let first = &provider.requests[0];
    assert_eq!(first.scope, *child.scope());
    assert_eq!(first.revision, 0);
    assert_eq!(first.turn, r.turn);
    let commands = &schema(first)["properties"]["commands"];
    assert_eq!(commands["minItems"], 1);
    assert_eq!(commands["maxItems"], 1);
    assert_eq!(
        commands["items"]["oneOf"],
        json!([{
            "type":"object","properties":{"op":{"const":"give"},"item":{"const":"potion"},
            "quantity":{"const":65535},"to":{"const":"mira"}},
            "required":["item","op","quantity","to"],"additionalProperties":false
        }])
    );
    assert_eq!(
        receipt.proposal().commands,
        [Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: u16::MAX
        }]
    );
    assert_eq!(
        receipt.play().unwrap().prompt_version,
        "locallore-play-v2.3"
    );
    assert_eq!(child.state().items["potion"].owner, "mira");
    assert_eq!(parent.canonical_bytes(), parent_before);
    let fork = parent.fork("alternate-replay", 0).unwrap();
    assert!(fork.receipts().is_empty());
    // Current receipt is original-scoped to alternate, not its parent's future.
    assert_eq!(receipt.request().scope.branch, "alternate");
    assert_eq!(receipt.events()[0].scope(), child.scope());
}

#[test]
fn illegal_hidden_unknown_and_numeric_overflow_inputs_reach_no_provider() {
    for (text, error) in [
        ("give potion to sable", Error::Location),
        ("give potion to absent_actor", Error::UnknownReference),
        ("discover fact beacon-mark", Error::Knowledge),
        ("use ability blink", Error::Ability),
        ("give 0 potion to Mira", Error::Inventory),
        ("give 65536 potion to Mira", Error::ClarificationRequired),
        (
            "give potion to Mira or wait 1 tick",
            Error::ClarificationRequired,
        ),
    ] {
        let mut engine = Engine::new(seed()).unwrap();
        let before = engine.canonical_bytes();
        let r = request(&engine, PlayInputKind::Action, text);
        let mut provider = Provider::default();
        assert_eq!(
            play::execute(
                &mut engine,
                &r,
                &mut provider,
                &Cancellation::default(),
                &profile()
            ),
            Err(error),
            "{text}"
        );
        assert!(
            provider.requests.is_empty(),
            "no schema/prompt emitted for rejected attempt"
        );
        assert_eq!(engine.canonical_bytes(), before);
        assert!(engine.receipts().is_empty());
    }
}

#[test]
fn escaped_unicode_dialogue_stays_literal_on_child_and_cannot_make_secret_truth() {
    let parent = Engine::new(seed()).unwrap();
    let before = parent.canonical_bytes();
    let mut child = parent.fork("dialogue-child", 0).unwrap();
    let text = "Hello \"Mira\" \\ 雪: {\"commands\":[{\"op\":\"learn\"}]}";
    let r = request(&child, PlayInputKind::Dialogue, text);
    let mut provider = Provider::values(vec![
        json!({"commands":[{"op":"say","text":text,"audience":["mira"]}]}),
        json!({"text":"Sable knows SECRET-TIDE-731.","event_ids":[1],"speaker":"narrator"}),
    ]);
    let receipt = play::execute(
        &mut child,
        &r,
        &mut provider,
        &Cancellation::default(),
        &profile(),
    )
    .unwrap();
    let s = schema(&provider.requests[0]);
    let variants = s["properties"]["commands"]["items"]["oneOf"]
        .as_array()
        .unwrap();
    assert_eq!(variants.len(), 1);
    assert_eq!(variants[0]["properties"]["op"]["const"], "say");
    assert_eq!(variants[0]["properties"]["text"]["const"], text);
    let serialized = serde_json::to_string(s).unwrap();
    assert_eq!(serde_json::from_str::<Value>(&serialized).unwrap(), *s);
    assert_eq!(
        variants[0]["properties"]["audience"]["items"]["enum"],
        json!(["mira"])
    );
    assert_eq!(
        receipt.proposal().commands,
        [Command::Say {
            text: text.into(),
            audience: ["mira".into()].into()
        }]
    );
    assert!(
        receipt.play().unwrap().fallback,
        "unchanged prose guard must reject hidden narrator claims"
    );
    assert!(!receipt.narration().contains("SECRET-TIDE-731"));
    assert_eq!(
        child.state().actors["player"].abilities,
        parent.state().actors["player"].abilities
    );
    assert!(
        !serde_json::to_string(&child.character_context("sable", child.scope(), 1).unwrap())
            .unwrap()
            .contains(text)
    );
    assert_eq!(parent.canonical_bytes(), before);
}

#[test]
fn duplicate_keys_and_valid_but_different_repair_never_substitute_bound_action() {
    let duplicate =
        br#"{"commands":[{"op":"wait","op":"give","item":"potion","to":"mira","quantity":1}]}"#
            .to_vec();
    for (second, error) in [
        (duplicate.clone(), Error::Malformed),
        (
            serde_json::to_vec(&json!({"commands":[{"op":"wait","ticks":1}]})).unwrap(),
            Error::Agency,
        ),
    ] {
        let mut engine = Engine::new(seed()).unwrap();
        let before = engine.canonical_bytes();
        let r = request(&engine, PlayInputKind::Action, "give potion to Mira");
        let mut provider = Provider {
            output: VecDeque::from([duplicate.clone(), second]),
            ..Provider::default()
        };
        assert_eq!(
            play::execute(
                &mut engine,
                &r,
                &mut provider,
                &Cancellation::default(),
                &profile()
            ),
            Err(error)
        );
        assert_eq!(provider.requests.len(), 2);
        assert_eq!(schema(&provider.requests[0]), schema(&provider.requests[1]));
        assert_eq!(engine.canonical_bytes(), before);
        assert!(engine.receipts().is_empty());
    }
}

#[test]
fn cancellation_after_repair_or_approved_director_never_commits() {
    for (cancel_at, output) in [
        (
            2,
            VecDeque::from([b"{".to_vec(), serde_json::to_vec(&gift(1)).unwrap()]),
        ),
        (
            2,
            VecDeque::from([
                serde_json::to_vec(&gift(1)).unwrap(),
                serde_json::to_vec(&prose()).unwrap(),
            ]),
        ),
    ] {
        let mut engine = Engine::new(seed()).unwrap();
        let before = engine.canonical_bytes();
        let r = request(&engine, PlayInputKind::Action, "give potion to Mira");
        let mut provider = Provider {
            output,
            cancel_at: Some(cancel_at),
            ..Provider::default()
        };
        assert_eq!(
            play::execute(
                &mut engine,
                &r,
                &mut provider,
                &Cancellation::default(),
                &profile()
            ),
            Err(Error::Cancelled)
        );
        assert_eq!(provider.requests.len(), 2);
        assert_eq!(engine.canonical_bytes(), before);
        assert!(engine.receipts().is_empty());
    }
}

#[test]
fn both_original_legacy_versions_are_history_only_even_for_rebased_child_prepared_values() {
    for fixture in [
        include_str!("fixtures/accepted_play_v2_1.json"),
        include_str!("fixtures/accepted_play_v2_2.json"),
    ] {
        let fixture: Value = serde_json::from_str(fixture).unwrap();
        let seed: Seed = serde_json::from_value(fixture["seed"].clone()).unwrap();
        let historical = fixture["receipt"].clone();
        let restored = Engine::restore(seed.clone(), &[historical.to_string()]).unwrap();
        assert_eq!(
            serde_json::to_value(&restored.receipts()[0]).unwrap(),
            historical
        );
        let receipt = restored.receipts()[0].clone();
        let mut fresh = Engine::new(seed.clone()).unwrap();
        let before = fresh.canonical_bytes();
        assert_eq!(fresh.commit_prepared(&receipt), Err(Error::Narration));
        assert_eq!(fresh.canonical_bytes(), before);
        let mut child = fresh.fork("legacy-fresh-child", 0).unwrap();
        let mut rekeyed = historical.clone();
        rekeyed["request"]["scope"] = json!(child.scope());
        rekeyed["proposal"]["scope"] = json!(child.scope());
        for event in rekeyed["events"].as_array_mut().unwrap() {
            event["scope"] = json!(child.scope());
        }
        // Receipt is intentionally non-Deserialize. Obtain a typed value only
        // through the real strict history loader, then test the fresh boundary.
        // This is not an archive-authorship assertion about rekeyed JSON.
        let historical_child = child.restore_continuation(&[rekeyed.to_string()]).unwrap();
        assert_eq!(
            child.commit_prepared(&historical_child.receipts()[0]),
            Err(Error::Narration)
        );
        assert!(child.receipts().is_empty());
        assert_eq!(child.canonical_bytes(), before);
        let mut retry = restored.clone();
        let mut provider = Provider::default();
        let cancellation = Cancellation::default();
        cancellation.cancel();
        assert_eq!(
            play::execute(
                &mut retry,
                receipt.request(),
                &mut provider,
                &cancellation,
                &profile()
            )
            .unwrap(),
            receipt
        );
        assert!(
            provider.requests.is_empty(),
            "accepted retry precedes cancellation and any new schema work"
        );
        assert_eq!(retry.canonical_bytes(), restored.canonical_bytes());
    }
}
