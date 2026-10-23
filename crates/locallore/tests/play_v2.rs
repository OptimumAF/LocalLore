use locallore::{
    contracts::*,
    engine::Engine,
    inference::*,
    play::{self, PlayProfile},
};
use serde_json::{json, Value};
use std::{
    collections::{BTreeSet, VecDeque},
    task::Poll,
};

fn engine() -> Engine {
    Engine::new(serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap())
        .unwrap()
}
fn profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-v2".into(),
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
struct Script {
    replies: VecDeque<Vec<u8>>,
    seen: Vec<GenerationRequest>,
    cancel_narrator: bool,
}

#[test]
fn pinned_runtime_profile_name_accepts_version_separator_only_in_profile_ids() {
    let mut p = profile();
    p.id = "qwen3-0.6b-q8-cpu-v1".into();
    assert_eq!(p.validate(), Ok(()));
    for id in [
        "",
        "../model/path",
        "model\\path",
        "model name",
        "model\nname",
        "模型",
    ] {
        p.id = id.into();
        assert_eq!(p.validate(), Err(Error::Rule), "{id:?}");
    }
    p.id = "a".repeat(65);
    assert_eq!(p.validate(), Err(Error::Rule));
    // Domain identifiers retain their existing stricter contract.
    let mut seed = engine().seed().clone();
    seed.scope.story = "story.1".into();
    assert!(Engine::new(seed).is_err());
}
impl Script {
    fn new(replies: Vec<Value>) -> Self {
        Self {
            replies: replies
                .into_iter()
                .map(|v| serde_json::to_vec(&v).unwrap())
                .collect(),
            seen: vec![],
            cancel_narrator: false,
        }
    }
}
impl InferenceProvider for Script {
    fn poll(&mut self, r: &GenerationRequest, c: &Cancellation) -> Poll<Result<Vec<u8>, Error>> {
        self.seen.push(r.clone());
        if self.cancel_narrator && matches!(&r.input,Input::Structured{role,..} if role=="narrator")
        {
            c.cancel();
        }
        Poll::Ready(self.replies.pop_front().ok_or(Error::Provider))
    }
}
fn gift() -> Value {
    json!({"commands":[{"op":"give","item":"potion","to":"mira","quantity":1}]})
}
fn prose() -> Value {
    json!({"text":"You place the potion in Mira's waiting hand, a small gesture of care.","event_ids":[1],"speaker":"narrator"})
}
fn request(e: &Engine) -> Request {
    e.request(
        "free-gift",
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: "I give my last potion to Mira.".into(),
        },
    )
}

#[test]
fn real_contract_records_original_free_text_and_generated_prose_then_replays_without_inference() {
    let mut e = engine();
    let r = request(&e);
    let mut p = Script::new(vec![gift(), prose()]);
    let receipt = play::execute(&mut e, &r, &mut p, &Cancellation::default(), &profile()).unwrap();
    let Input::Structured { schema, .. } = &p.seen[0].input else {
        panic!("structured director")
    };
    assert!(schema["properties"]["commands"]["items"]["oneOf"]
        .as_array()
        .unwrap()
        .iter()
        .all(|v| v["properties"]["op"]["const"] != "say"));
    let give_schema = schema["properties"]["commands"]["items"]["oneOf"]
        .as_array()
        .unwrap()
        .iter()
        .find(|v| v["properties"]["op"]["const"] == "give")
        .unwrap();
    assert_eq!(
        give_schema["properties"]["item"]["enum"],
        json!(["brass-key", "potion"])
    );
    assert_eq!(
        give_schema["properties"]["to"]["enum"],
        json!(["mira", "player"])
    );
    assert_eq!(p.seen.len(), 2);
    assert_eq!(receipt.request(), &r);
    assert!(!receipt.play().unwrap().fallback);
    assert_ne!(
        receipt.narration(),
        locallore::engine::render(receipt.events())
    );
    assert_eq!(e.state().items["potion"].owner, "mira");
    let history = vec![serde_json::to_string(&receipt).unwrap()];
    let restored = Engine::restore(e.seed().clone(), &history).unwrap();
    assert_eq!(restored.canonical_bytes(), e.canonical_bytes());
    assert_eq!(
        play::execute(&mut e, &r, &mut p, &Cancellation::default(), &profile()).unwrap(),
        receipt
    );
    assert_eq!(p.seen.len(), 2);
    let mut changed = r.clone();
    if let Intent::FreeText { text, .. } = &mut changed.intent {
        *text = "I keep the potion".into();
    }
    assert_eq!(
        play::execute(
            &mut e,
            &changed,
            &mut p,
            &Cancellation::default(),
            &profile()
        ),
        Err(Error::RetryMismatch)
    );
}

#[test]
fn semantic_mechanical_rejection_does_not_ask_narrator_or_repair_away_an_invalid_action() {
    for (text, command, error) in [
        (
            "I use ability invented-teleport.",
            json!({"op":"use_ability","ability":"invented-teleport"}),
            Error::Ability,
        ),
        (
            "I give invented-sword to Mira.",
            json!({"op":"give","item":"invented-sword","to":"mira","quantity":1}),
            Error::Inventory,
        ),
    ] {
        let mut e = engine();
        let before = e.canonical_bytes();
        let r = e.request(
            "unavailable-action",
            Intent::FreeText {
                kind: PlayInputKind::Action,
                text: text.into(),
            },
        );
        let mut p = Script::new(vec![json!({"commands":[command]}), prose()]);
        assert_eq!(
            play::execute(&mut e, &r, &mut p, &Cancellation::default(), &profile()),
            Err(error)
        );
        assert!(
            p.seen.is_empty(),
            "an invalid explicit attempt is rejected by Engine before generation"
        );
        assert_eq!(e.canonical_bytes(), before);
    }
}

#[test]
fn malformed_repair_is_finite_and_duplicate_keys_do_not_bypass_schema() {
    let mut e = engine();
    let r = request(&e);
    let before = e.canonical_bytes();
    let mut p = Script::new(vec![]);
    p.replies = VecDeque::from([
        b"{\"commands\":[],\"commands\":[]}".to_vec(),
        b"{broken".to_vec(),
    ]);
    assert_eq!(
        play::execute(&mut e, &r, &mut p, &Cancellation::default(), &profile()),
        Err(Error::Malformed)
    );
    assert_eq!(p.seen.len(), 2);
    assert_eq!(e.canonical_bytes(), before);
    let mut p = Script::new(vec![json!({"bad":true}), gift(), prose()]);
    let result = play::execute(&mut e, &r, &mut p, &Cancellation::default(), &profile()).unwrap();
    assert_eq!(result.play().unwrap().repairs, 1);
    assert_eq!(p.seen.len(), 3);
}

#[test]
fn consequential_invention_foreign_speaker_and_unearned_healing_use_labeled_safe_fallback() {
    for narration in [
        json!({"text":"A golden key appears in your hand.","event_ids":[1],"speaker":"narrator"}),
        json!({"text":"The potion passes to Mira.","event_ids":[1],"speaker":"sable"}),
        json!({"text":"Mira is healed and her injury disappears.","event_ids":[1],"speaker":"narrator"}),
        json!({"text":"Mira's ankle mends.","event_ids":[1],"speaker":"narrator"}),
        json!({"text":"You give a potion to Miran.","event_ids":[1],"speaker":"narrator"}),
        json!({"text":"You said that the fire is burning.","event_ids":[1],"speaker":"narrator"}),
    ] {
        let mut e = engine();
        let r = request(&e);
        let mut p = Script::new(vec![gift(), narration]);
        let receipt =
            play::execute(&mut e, &r, &mut p, &Cancellation::default(), &profile()).unwrap();
        assert!(receipt.play().unwrap().fallback);
        assert_eq!(
            receipt.narration(),
            locallore::engine::render(receipt.events())
        );
        assert_eq!(
            e.state().actors["mira"].injuries,
            BTreeSet::from(["sprained-ankle".into()])
        );
        assert!(!e.state().items.contains_key("golden-key"));
    }
}

#[test]
fn cancelled_narration_and_stale_start_leave_canon_unchanged() {
    let mut e = engine();
    let before = e.canonical_bytes();
    let r = request(&e);
    let mut p = Script::new(vec![gift(), prose()]);
    p.cancel_narrator = true;
    assert_eq!(
        play::execute(&mut e, &r, &mut p, &Cancellation::default(), &profile()),
        Err(Error::Cancelled)
    );
    assert_eq!(e.canonical_bytes(), before);
    let mut r = r;
    r.expected_revision = 99;
    let mut p = Script::new(vec![]);
    assert_eq!(
        play::execute(&mut e, &r, &mut p, &Cancellation::default(), &profile()),
        Err(Error::Stale)
    );
    assert!(p.seen.is_empty());
}

#[test]
fn dialogue_preserves_player_words_and_cannot_turn_into_a_gift_or_rewrite_the_quote() {
    for commands in [
        gift()["commands"].clone(),
        json!([{"op":"say","text":"I surrender my potion","audience":["mira"]}]),
    ] {
        let mut e = engine();
        let before = e.canonical_bytes();
        let r = e.request(
            "spoken",
            Intent::FreeText {
                kind: PlayInputKind::Dialogue,
                text: "Hello Mira".into(),
            },
        );
        let mut p = Script::new(vec![json!({"commands":commands})]);
        assert_eq!(
            play::execute(&mut e, &r, &mut p, &Cancellation::default(), &profile()),
            Err(Error::Agency)
        );
        assert_eq!(e.canonical_bytes(), before);
        let Input::Structured { schema, .. } = &p.seen[0].input else {
            panic!("structured dialogue")
        };
        let properties = &schema["properties"]["commands"]["items"]["oneOf"][0]["properties"];
        assert_eq!(properties["text"]["const"], "Hello Mira");
        assert_eq!(properties["audience"]["items"]["enum"], json!(["mira"]));
    }
}

#[test]
fn spoken_claim_contents_do_not_reach_narration_or_become_established_truth() {
    let mut e = engine();
    let text = "The relic is here: PRIVATE-SPEECH-CANARY-918.";
    let r = e.request(
        "spoken-claim",
        Intent::FreeText {
            kind: PlayInputKind::Dialogue,
            text: text.into(),
        },
    );
    let mut p = Script::new(vec![
        json!({"commands":[{"op":"say","text":text,"audience":["mira"]}]}),
        json!({"text":"You speak quietly to your listener.","event_ids":[1],"speaker":"narrator"}),
    ]);
    play::execute(&mut e, &r, &mut p, &Cancellation::default(), &profile()).unwrap();
    let Input::Structured { prompt, .. } = &p.seen[1].input else {
        panic!("narrator")
    };
    assert!(!prompt.contains("PRIVATE-SPEECH-CANARY-918"));
    assert!(!prompt.contains("The relic is here"));
    let mira = e
        .character_context("mira", e.scope(), e.revision())
        .unwrap();
    assert!(serde_json::to_string(&mira)
        .unwrap()
        .contains("PRIVATE-SPEECH-CANARY-918"));
    assert_eq!(e.seed().facts.len(), engine().seed().facts.len());
}

#[test]
fn inspector_authority_never_enters_generation_and_npc_canaries_are_filtered_before_prompting() {
    let mut seed = engine().seed().clone();
    seed.facts.insert(
        "mira-only".into(),
        Fact {
            proposition: "NPC-ONLY-CANARY-894".into(),
            discoverable_at: None,
            known_by: BTreeSet::from(["mira".into()]),
        },
    );
    let mut e = Engine::new(seed).unwrap();
    let r = request(&e);
    let mut p = Script::new(vec![gift(), prose()]);
    play::execute(&mut e, &r, &mut p, &Cancellation::default(), &profile()).unwrap();
    for g in &p.seen {
        let Input::Structured { prompt, .. } = &g.input else {
            panic!("wrong role input")
        };
        assert!(!prompt.contains("NPC-ONLY-CANARY-894"));
        assert!(!prompt.contains("old-ruins"));
    }
    let Input::Structured { prompt, .. } = &p.seen[0].input else {
        panic!()
    };
    assert!(prompt.contains("SECRET-TIDE-731"));
    let Input::Structured { prompt, .. } = &p.seen[1].input else {
        panic!()
    };
    assert!(!prompt.contains("SECRET-TIDE-731"));
}

#[test]
fn v1_bytes_and_strict_narration_survive_mixed_history_and_v2_effect_tampering_is_rejected() {
    let mut e = engine();
    let r = e.request("old", Intent::Actions(vec![Command::Wait { ticks: 1 }]));
    let p = Engine::proposal(&r).unwrap();
    let n = e.preview(&r, &p).unwrap().narration().to_owned();
    let old = e.commit(&r, &p, &n).unwrap();
    assert!(serde_json::to_value(&old).unwrap().get("play").is_none());
    let r = request(&e);
    let mut p = Script::new(vec![
        gift(),
        json!({"text":"You pass the potion to Mira with a gentle nod.","event_ids":[2],"speaker":"narrator"}),
    ]);
    let receipt = play::execute(&mut e, &r, &mut p, &Cancellation::default(), &profile()).unwrap();
    let history: Vec<_> = e
        .receipts()
        .iter()
        .map(|r| serde_json::to_string(r).unwrap())
        .collect();
    assert_eq!(
        Engine::restore(e.seed().clone(), &history)
            .unwrap()
            .canonical_bytes(),
        e.canonical_bytes()
    );
    let mut tampered = serde_json::to_value(&receipt).unwrap();
    tampered["events"][0]["outcome"]["quantity"] = json!(2);
    assert!(Engine::restore(
        e.seed().clone(),
        &[history[0].clone(), tampered.to_string()]
    )
    .is_err());
    let mut fresh = engine();
    let r = request(&fresh);
    let mut p = Script::new(vec![gift(), prose()]);
    let receipt =
        play::execute(&mut fresh, &r, &mut p, &Cancellation::default(), &profile()).unwrap();
    let mut clean = engine();
    assert_eq!(
        clean.commit(&r, receipt.proposal(), receipt.narration()),
        Err(Error::Agency)
    );
    let mut prototype = serde_json::to_value(&receipt).unwrap();
    prototype["play"]["policy"] = json!("grounded-prose-v2.0");
    prototype["play"]["prompt_version"] = json!("locallore-play-v2.0");
    assert!(
        Engine::restore(fresh.seed().clone(), &[prototype.to_string()]).is_err(),
        "unmerged unguarded prototype policy has no fresh-commit/restore bypass"
    );
}

#[test]
fn a_visible_name_alias_is_not_rejected_for_a_distinct_hidden_actor_with_the_same_name() {
    let mut seed = engine().seed().clone();
    seed.actors.get_mut("mira").unwrap().name = "Oren".into();
    let mut e = Engine::new(seed).unwrap();
    let r = e.request(
        "visible-name",
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: "I give potion to mira.".into(),
        },
    );
    let mut p = Script::new(vec![
        gift(),
        json!({"text":"You pass the potion to Oren with care.","event_ids":[1],"speaker":"narrator"}),
    ]);
    let receipt = play::execute(&mut e, &r, &mut p, &Cancellation::default(), &profile()).unwrap();
    assert!(!receipt.play().unwrap().fallback);
    assert_eq!(e.state().items["potion"].owner, "mira");
}

#[test]
fn rust_rejects_an_operation_outside_the_selected_director_schema() {
    let mut e = engine();
    let before = e.canonical_bytes();
    let r = request(&e);
    let mut p = Script::new(vec![
        json!({"commands":[{"op":"promise","id":"unrequested","to":"mira","terms":"I owe you","deadline":100,"return_item":null}]}),
    ]);
    assert_eq!(
        play::execute(&mut e, &r, &mut p, &Cancellation::default(), &profile()),
        Err(Error::Agency)
    );
    assert_eq!(p.seen.len(), 1);
    assert_eq!(e.canonical_bytes(), before);
}
