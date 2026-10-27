// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! FIRST SOURCE freeze: UNCOMPILED/UNRUN; absent new native selectors are compile
//! prerequisites, not behavioral RED. Actual in-memory Host and scripted provider.
//! Durable/presented cases belong to the companion Workspace test, not a Spy.
//! No Host seed-import API exists; initial_world refusal remains Core-owned.
#![cfg(feature = "host")]
use locallore::{
    contracts::*, engine::Engine,
    host::{Host, HostPlayConstructionV1, ProviderFactory},
    inference::*, inspection::sha256, play::{PlayContextPolicy, PlayProfile},
};
use serde_json::{json, Value};
use std::{sync::{atomic::{AtomicUsize, Ordering}, Arc, Mutex}, task::Poll};

const MEMORY: &str = "locallore-play-v2.9-scene-frame-v1";
const LITERAL: &str = "locallore-play-v2.10-literal-director-v1-scene-frame-v1";
const POLICY: &str = "grounded-prose-v2.4-scene-frame-v1";
#[derive(Clone, Copy, Debug)]
enum Arm { Memory, Literal }
impl Arm {
    fn native(self) -> HostPlayConstructionV1 { match self {
        Self::Memory => HostPlayConstructionV1::MemorySceneV1(PlayContextPolicy::StateRelevantMemoryV1),
        Self::Literal => HostPlayConstructionV1::PlayerLiteralSceneV1,
    } }
    fn prompt(self) -> &'static str { match self { Self::Memory => MEMORY, Self::Literal => LITERAL } }
    fn trace_schema(self) -> &'static str { match self { Self::Memory => "locallore-play-v2", Self::Literal => "locallore-director-literal-v1" } }
    fn director_schema(self) -> &'static str { match self { Self::Memory => "locallore-director-v2", Self::Literal => "locallore-director-literal-v1" } }
}
fn profile() -> PlayProfile { PlayProfile {
    id:"synthetic-host-scene-v1".into(),model_sha256:"a".repeat(64),runtime_revision:"b".repeat(40),
    template_sha256:"c".repeat(64),worker_sha256:"d".repeat(64),profile_manifest_sha256:"e".repeat(64),
    context_tokens:4096,director_tokens:350,narrator_tokens:350,deadline_ms:5000,repair_limit:1,
} }
#[derive(Default)]
struct Seen { factories:AtomicUsize, requests:Mutex<Vec<GenerationRequest>> }
impl Seen {
    fn factory(self:&Arc<Self>) -> ProviderFactory { let seen=self.clone(); Arc::new(move || {
        seen.factories.fetch_add(1,Ordering::SeqCst); Box::new(Script(seen.clone()))
    }) }
    fn requests(&self)->Vec<GenerationRequest> { self.requests.lock().unwrap().clone() }
}
struct Script(Arc<Seen>);
impl InferenceProvider for Script {
    fn poll(&mut self,r:&GenerationRequest,_:&Cancellation)->Poll<Result<Vec<u8>,Error>> {
        self.0.requests.lock().unwrap().push(r.clone());
        let Input::Structured{role,..}=&r.input else { panic!("actual structured Host request required") };
        Poll::Ready(Ok(serde_json::to_vec(&match role.as_str() {
            "director"=>json!({"commands":[{"op":"wait","ticks":1}]}),
            "narrator"=>json!({"text":"You pause as a tide tick passes.","event_ids":[r.revision+1],"speaker":"narrator"}),
            other=>panic!("unexpected actual role {other}"),
        }).unwrap()))
    }
}
fn call(h:&Host,command:Value)->Value { h.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap()) }
fn ok(reply:Value)->Value { assert_eq!(reply["status"],"ok","{reply}"); reply["data"].clone() }
fn create(h:&Host)->(String,Scope) { let data=ok(call(h,json!({"op":"create","seed":"lantern-quay-v1"})));
    (data["session"].as_str().unwrap().into(),serde_json::from_value(data["scope"].clone()).unwrap()) }
fn request(scope:&Scope,head:u64,turn:&str)->Request { Request {version:VERSION,scope:scope.clone(),turn:turn.into(),expected_revision:head,
    intent:Intent::FreeText{kind:PlayInputKind::Action,text:"I wait for one tide tick.".into()} } }
fn submit(h:&Host,s:&str,r:&Request)->Value { call(h,json!({"op":"submit","session":s,"request":r,"mode":"accepted"})) }
fn op(h:&Host,s:&str,r:&Request,op:&str)->Value { call(h,json!({"op":op,"session":s,"scope":r.scope,"turn":r.turn})) }
fn snapshot(h:&Host,s:&str,scope:&Scope,head:u64)->Engine { h.generation_snapshot(s,scope,head,&||false).unwrap().engine }
fn same_engine(actual:&Engine,expected:&Engine) { assert_eq!(actual.canonical_records(),expected.canonical_records());
    assert_eq!(actual.canonical_bytes(),expected.canonical_bytes()); assert_eq!(actual.accepted_history_basis().unwrap(),expected.accepted_history_basis().unwrap()); }
fn trace(h:&Host,s:&str,r:&Request,head:u64,observer:Value)->Value { call(h,json!({"op":"trace_read","session":s,"scope":r.scope,
    "expected_head":head,"base_revision":r.expected_revision,"observer":observer,"turn":r.turn,"attempt":null})) }
fn details(h:&Host,s:&str,r:&Request,head:u64,attempt:u64)->Value { call(h,json!({"op":"trace_capture_read","session":s,"scope":r.scope,
    "expected_head":head,"base_revision":r.expected_revision,"turn":r.turn,"attempt":attempt})) }
fn capture_on(h:&Host,s:&str,scope:&Scope,head:u64,consent:bool)->Value { call(h,json!({"op":"trace_capture_configure","session":s,
    "scope":scope,"expected_head":head,"enabled":true,"consent":consent})) }
fn assert_forwarded(copy:&Value,actual:&GenerationRequest) {
    let Input::Structured{role,prompt,schema}=&actual.input else { panic!("actual structured role") };
    assert_eq!(copy["version"],json!(actual.version)); assert_eq!(copy["scope"],json!(actual.scope));
    assert_eq!(copy["turn"],json!(actual.turn)); assert_eq!(copy["revision"],json!(actual.revision));
    assert_eq!(copy["model_profile"],json!(actual.model_profile)); assert_eq!(copy["schema_id"],json!(actual.schema));
    assert_eq!(copy["input"],json!({"kind":"structured","role":role,"prompt":prompt,"schema":schema}));
    assert_eq!(copy["budget"],json!({"max_output_bytes":actual.budget.max_output_bytes,"max_output_tokens":actual.budget.max_output_tokens,
        "max_pending_polls":actual.budget.max_pending_polls,"deadline_ms":actual.budget.deadline_ms}));
}
fn scene_frame_from_forwarded(actual:&GenerationRequest,before:&Engine,after:&Engine,play:&Value) {
    let Input::Structured{role,prompt,..}=&actual.input else { panic!("actual narrator required") };
    assert_eq!(role,"narrator"); assert!(!prompt.contains("SECRET-TIDE-731"));
    let source=prompt.split_once("Post-turn scene frame: ").unwrap().1;
    let mut stream=serde_json::Deserializer::from_str(source).into_iter::<Value>();
    let frame=stream.next().unwrap().unwrap(); let end=stream.byte_offset();
    assert_eq!(frame,json!({"version":1,"scope":before.scope(),"before_revision":before.revision(),"after_revision":after.revision(),
        "player":before.seed().player,"location":after.character_context_v2(&before.seed().player,after.scope(),after.revision()).unwrap().self_state.location}));
    // Hash the exact actual forwarded frame substring, preserving struct field
    // ordering. Serializing parsed Value would be a different byte recipe.
    assert_eq!(play["scene"],json!({"version":1,"frame_sha256":sha256(&source.as_bytes()[..end])}));
}

#[test]
fn both_scene_arms_use_actual_host_candidates_private_capture_commit_and_zero_inference_retry() {
    for arm in [Arm::Memory,Arm::Literal] {
        let h=Host::new(true); let seen=Arc::new(Seen::default());
        h.configure_fixture_provider_with_construction(profile(),seen.factory(),arm.native()).unwrap();
        let (s,scope)=create(&h); let r=request(&scope,0,"actual-host-scene");
        let before=snapshot(&h,&s,&scope,0);
        assert_eq!(capture_on(&h,&s,&scope,0,false)["error"],"CaptureConsentRequired");
        ok(capture_on(&h,&s,&scope,0,true));
        assert_eq!(ok(submit(&h,&s,&r))["phase"],"queued");
        same_engine(&snapshot(&h,&s,&scope,0),&before);
        let ready=ok(op(&h,&s,&r,"prepare")); assert_eq!(ready["phase"],"ready"); assert!(ready["receipt"].is_null());
        same_engine(&snapshot(&h,&s,&scope,0),&before);
        let meta=ok(trace(&h,&s,&r,0,json!({"kind":"player"})));
        let attempt=meta["snapshot"]["attempts"][0]["identity"]["attempt"].as_u64().unwrap();
        let provenance=&meta["snapshot"]["attempts"][0]["provenance"];
        assert_eq!(provenance["prompt_label"],arm.prompt()); assert_eq!(provenance["schema_label"],arm.trace_schema());
        assert!(provenance["model_sha256"].is_null());
        let private=ok(details(&h,&s,&r,0,attempt)); assert_eq!(private["details"]["status"],"recorded");
        assert_eq!(private["details"]["identity"]["observer"],before.seed().player);
        assert_eq!(private["details"]["identity"]["scope"],json!(scope));
        assert_eq!(private["details"]["identity"]["turn"],r.turn);
        assert_eq!(private["details"]["identity"]["base_revision"],0);
        assert_eq!(private["details"]["exact_reconstruction"],false);
        let requests=seen.requests(); assert_eq!(requests.len(),2); assert_eq!(requests[0].schema,arm.director_schema());
        assert_eq!(requests[1].schema,"locallore-narrator-v2");
        let artifacts=private["details"]["artifacts"].as_array().unwrap();
        for actual in &requests { let Input::Structured{role,..}=&actual.input else { unreachable!() };
            let copies:Vec<_>=artifacts.iter().filter(|a|a["kind"]=="generation_request"&&a["value"]["input"]["role"]==*role).collect();
            assert_eq!(copies.len(),1); assert_forwarded(&copies[0]["value"],actual);
        }
        assert!(artifacts.iter().any(|a|a["kind"]=="validated_plan_not_durable_commit"));
        assert!(artifacts.iter().any(|a|a["kind"]=="accepted_candidate_not_durable_commit"));
        assert_eq!(artifacts.iter().any(|a|a["kind"]=="selected_context"),matches!(arm,Arm::Memory));
        let done=ok(op(&h,&s,&r,"commit")); assert_eq!(done["phase"],"committed");
        let play=&done["receipt"]["play"]; assert_eq!(play["prompt_version"],arm.prompt()); assert_eq!(play["policy"],POLICY);
        assert_eq!(play["context"].is_null(),matches!(arm,Arm::Literal)); assert_eq!(play["context_policy"].is_null(),matches!(arm,Arm::Literal));
        let after=snapshot(&h,&s,&scope,1); assert_eq!(after.receipts().len(),before.receipts().len()+1);
        scene_frame_from_forwarded(&requests[1],&before,&after,play);
        assert_eq!(serde_json::to_value(after.receipts().last().unwrap()).unwrap(),done["receipt"]);
        h.configure_fixture_provider(profile(),seen.factory()).unwrap(); // future config cannot change the recorded recipe
        for command in [submit(&h,&s,&r),op(&h,&s,&r,"prepare"),op(&h,&s,&r,"commit")] {
            let retry=ok(command); assert_eq!(retry["phase"],"committed"); assert_eq!(retry["receipt"],done["receipt"]);
        }
        assert_eq!(seen.factories.load(Ordering::SeqCst),1); assert_eq!(seen.requests().len(),2);
        same_engine(&snapshot(&h,&s,&scope,1),&after);
        assert_eq!(details(&h,&s,&r,0,attempt)["error"],"Stale");
        ok(call(&h,json!({"op":"trace_capture_revoke","session":s,"scope":scope})));
        assert!(ok(details(&h,&s,&r,1,attempt))["details"]["artifacts"].as_array().unwrap().is_empty());
        same_engine(&snapshot(&h,&s,&scope,1),&after);
        h.close_all(); assert_eq!(h.live_counts(),(0,0));
    }
}

#[test]
fn scene_selector_has_no_wire_grant_and_private_capture_remains_opt_in_player_bound() {
    for arm in [Arm::Memory,Arm::Literal] {
        let h=Host::new(false); let seen=Arc::new(Seen::default());
        h.configure_fixture_provider_with_construction(profile(),seen.factory(),arm.native()).unwrap();
        let (s,scope)=create(&h); let r=request(&scope,0,"unprivileged-scene");
        assert_eq!(capture_on(&h,&s,&scope,0,true)["error"],"Forbidden");
        assert_eq!(details(&h,&s,&r,0,1)["error"],"Forbidden");
        assert_eq!(trace(&h,&s,&r,0,json!({"kind":"character","id":"mira"}))["error"],"Forbidden");
        for command in [json!({"op":"configure_fixture_provider_with_construction","construction":"memory_scene_v1"}),
            json!({"op":"submit","session":s,"request":r,"mode":"accepted","construction":"player_literal_scene_v1"}),
            json!({"op":"prepare","session":s,"scope":scope,"turn":r.turn,"observer":"mira"})] {
            assert_eq!(call(&h,command)["error"],"Malformed");
        }
        assert!(seen.requests().is_empty());
        assert_eq!(ok(submit(&h,&s,&r))["phase"],"queued"); assert_eq!(ok(op(&h,&s,&r,"prepare"))["phase"],"ready");
        let done=ok(op(&h,&s,&r,"commit")); assert_eq!(done["receipt"]["play"]["prompt_version"],arm.prompt());
        h.close_all(); assert_eq!(h.live_counts(),(0,0));
        let h=Host::new(true); let seen=Arc::new(Seen::default());
        h.configure_fixture_provider_with_construction(profile(),seen.factory(),arm.native()).unwrap();
        let (s,scope)=create(&h); let r=request(&scope,0,"details-off");
        ok(call(&h,json!({"op":"trace_configure","session":s,"scope":scope,"expected_head":0,"enabled":true})));
        let before=snapshot(&h,&s,&scope,0);
        for observer in [json!({"kind":"character","id":"mira"}),json!({"kind":"omniscient"})] {
            ok(call(&h,json!({"op":"inspection_query","session":s,"query":{"version":1,"scope":scope,"expected_head":0,"at_revision":null,
                "observer":observer,"view":"knowledge","cursor":null,"limit":64,"search":""}})));
        }
        same_engine(&snapshot(&h,&s,&scope,0),&before);
        ok(submit(&h,&s,&r)); ok(op(&h,&s,&r,"prepare"));
        let meta=ok(trace(&h,&s,&r,0,json!({"kind":"player"})));
        let attempt=meta["snapshot"]["attempts"][0]["identity"]["attempt"].as_u64().unwrap();
        let disabled=ok(details(&h,&s,&r,0,attempt)); assert_eq!(disabled["details"]["status"],"disabled");
        assert!(disabled["details"]["artifacts"].as_array().unwrap().is_empty());
        let done=ok(op(&h,&s,&r,"commit")); let after=snapshot(&h,&s,&scope,1);
        scene_frame_from_forwarded(&seen.requests()[1],&before,&after,&done["receipt"]["play"]);
        h.close_all(); assert_eq!(h.live_counts(),(0,0));
    }
}

#[test]
fn queued_and_prepared_cancellation_and_competing_real_host_commit_preserve_canonical_outcome() {
    for arm in [Arm::Memory,Arm::Literal] {
        for prepared in [false,true] {
            let h=Host::new(false); let seen=Arc::new(Seen::default());
            h.configure_fixture_provider_with_construction(profile(),seen.factory(),arm.native()).unwrap();
            let (s,scope)=create(&h); let r=request(&scope,0,"cancel-scene"); let before=snapshot(&h,&s,&scope,0);
            ok(submit(&h,&s,&r)); if prepared { assert_eq!(ok(op(&h,&s,&r,"prepare"))["phase"],"ready"); }
            assert_eq!(ok(op(&h,&s,&r,"cancel"))["phase"],"cancelled");
            assert_eq!(ok(op(&h,&s,&r,"prepare"))["phase"],"cancelled");
            assert_eq!(op(&h,&s,&r,"commit")["error"],"NotReady");
            same_engine(&snapshot(&h,&s,&scope,0),&before);
            assert_eq!(seen.factories.load(Ordering::SeqCst),usize::from(prepared)); assert_eq!(seen.requests().len(),if prepared {2}else{0});
            h.close_all(); assert_eq!(h.live_counts(),(0,0));
        }
        let h=Host::new(false); let seen=Arc::new(Seen::default());
        h.configure_fixture_provider_with_construction(profile(),seen.factory(),arm.native()).unwrap();
        let (s,scope)=create(&h); let r=request(&scope,0,"stale-scene"); ok(submit(&h,&s,&r)); ok(op(&h,&s,&r,"prepare"));
        let winning=Request{intent:Intent::Actions(vec![Command::Wait{ticks:1}]),turn:"actual-competing-wait".into(),..r.clone()};
        ok(submit(&h,&s,&winning)); ok(op(&h,&s,&winning,"prepare")); assert_eq!(ok(op(&h,&s,&winning,"commit"))["phase"],"committed");
        let expected=snapshot(&h,&s,&scope,1); let stale=ok(op(&h,&s,&r,"commit"));
        assert_eq!(stale["phase"],"stale"); assert_eq!(stale["error"],"Stale"); assert!(stale["receipt"].is_null());
        same_engine(&snapshot(&h,&s,&scope,1),&expected); assert_eq!(seen.factories.load(Ordering::SeqCst),1);
        assert_eq!(seen.requests().len(),2); h.close_all(); assert_eq!(h.live_counts(),(0,0));
    }
}

#[test]
fn ordinary_host_default_and_literal_constructions_keep_their_old_versions() {
    for literal in [false,true] { let h=Host::new(false); let seen=Arc::new(Seen::default());
        if literal { h.configure_fixture_provider_with_construction(profile(),seen.factory(),HostPlayConstructionV1::PlayerLiteralV1).unwrap(); }
        else { h.configure_fixture_provider(profile(),seen.factory()).unwrap(); }
        let(s,scope)=create(&h); let r=request(&scope,0,"legacy-native-control"); ok(submit(&h,&s,&r)); ok(op(&h,&s,&r,"prepare"));
        let done=ok(op(&h,&s,&r,"commit")); let play=&done["receipt"]["play"];
        assert_eq!(play["prompt_version"],if literal {"locallore-play-v2.6-literal-director-v1"}else{"locallore-play-v2.5"});
        assert_eq!(play["policy"],"grounded-prose-v2.2"); assert!(play.get("scene").is_none());
        h.close_all(); assert_eq!(h.live_counts(),(0,0));
    }
}
