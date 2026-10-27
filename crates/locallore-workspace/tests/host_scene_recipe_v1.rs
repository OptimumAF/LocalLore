// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! FIRST SOURCE freeze, UNCOMPILED/UNRUN. Future native selector absence is a
//! compile prerequisite, not behavioral RED. Actual Workspace -> Host -> Store.
//! Synthetic provider only, no application/native GUI/device/model quality proof.
//! No arbitrary Host seed import is invented for initial_world refusal.
use locallore::{contracts::*, engine::Engine, host::{Host,HostPlayConstructionV1,ProviderFactory},
    inference::*, inspection::sha256, play::{PlayContextPolicy,PlayProfile}};
use locallore_storage::{Store,TurnPhase};
use serde_json::{json,Value};
use std::{path::PathBuf,sync::{atomic::{AtomicU64,AtomicUsize,Ordering},Arc,Mutex},task::Poll};
const MEMORY:&str="locallore-play-v2.9-scene-frame-v1";
const LITERAL:&str="locallore-play-v2.10-literal-director-v1-scene-frame-v1";
const POLICY:&str="grounded-prose-v2.4-scene-frame-v1";
static NEXT:AtomicU64=AtomicU64::new(0);
struct Temp{path:PathBuf,parent:PathBuf}
impl Temp{
    fn new()->Self{let parent=std::env::temp_dir().canonicalize().unwrap();let path=parent.join(format!("locallore-host-scene-v1-{}-{}-{}",
        std::process::id(),std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos(),NEXT.fetch_add(1,Ordering::Relaxed)));
        std::fs::create_dir(&path).unwrap();Self{path,parent}}
    fn db(&self)->PathBuf{self.path.join("synthetic.sqlite")}
    fn host(&self)->Host{locallore_workspace::open(&self.db(),true).unwrap()}
    fn engine(&self,scope:&Scope)->Engine{Store::open_read_only(&self.db()).unwrap().resume(scope).unwrap().engine}
}
impl Drop for Temp{fn drop(&mut self){let resolved=self.path.canonicalize().unwrap();assert_eq!(resolved.parent(),Some(self.parent.as_path()));
    assert!(resolved.file_name().unwrap().to_str().unwrap().starts_with("locallore-host-scene-v1-"));
    if let Err(error)=std::fs::remove_dir_all(&resolved){if !std::thread::panicking(){panic!("owned synthetic Host scene cleanup: {error}");}}}}
#[derive(Clone,Copy,Debug)]
enum Arm{Memory,Literal}
impl Arm{
    fn native(self)->HostPlayConstructionV1{match self{Self::Memory=>HostPlayConstructionV1::MemorySceneV1(PlayContextPolicy::StateRelevantMemoryV1),Self::Literal=>HostPlayConstructionV1::PlayerLiteralSceneV1}}
    fn prompt(self)->&'static str{match self{Self::Memory=>MEMORY,Self::Literal=>LITERAL}}
    fn schema(self)->&'static str{match self{Self::Memory=>"locallore-play-v2",Self::Literal=>"locallore-director-literal-v1"}}
    fn opposite(self)->Self{match self{Self::Memory=>Self::Literal,Self::Literal=>Self::Memory}}
}
fn profile()->PlayProfile{PlayProfile{id:"synthetic-workspace-scene-v1".into(),model_sha256:"a".repeat(64),runtime_revision:"b".repeat(40),
    template_sha256:"c".repeat(64),worker_sha256:"d".repeat(64),profile_manifest_sha256:"e".repeat(64),context_tokens:4096,
    director_tokens:350,narrator_tokens:350,deadline_ms:5000,repair_limit:1}}
#[derive(Default)]
struct Seen{factories:AtomicUsize,requests:Mutex<Vec<GenerationRequest>>}
impl Seen{fn factory(self:&Arc<Self>)->ProviderFactory{let seen=self.clone();Arc::new(move||{seen.factories.fetch_add(1,Ordering::SeqCst);Box::new(Script(seen.clone()))})}
    fn requests(&self)->Vec<GenerationRequest>{self.requests.lock().unwrap().clone()}}
struct Script(Arc<Seen>);
impl InferenceProvider for Script{fn poll(&mut self,r:&GenerationRequest,_:&Cancellation)->Poll<Result<Vec<u8>,Error>>{
    self.0.requests.lock().unwrap().push(r.clone());let Input::Structured{role,..}=&r.input else{panic!("actual Host structured request required")};
    Poll::Ready(Ok(serde_json::to_vec(&match role.as_str(){"director"=>json!({"commands":[{"op":"wait","ticks":1}]}),
        "narrator"=>json!({"text":"You pause as a tide tick passes.","event_ids":[r.revision+1],"speaker":"narrator"}),other=>panic!("unexpected role {other}")}).unwrap()))}}
fn call(h:&Host,command:Value)->Value{h.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())}
fn ok(reply:Value)->Value{assert_eq!(reply["status"],"ok","{reply}");reply["data"].clone()}
fn create(h:&Host,presented:bool)->(String,Scope){let data=if presented{
    let review=ok(call(h,json!({"op":"story_presentation","template":"lantern-quay-v1","player_name":"Arden",
        "presentation":{"version":1,"tone":"warm","excluded_phrases":["SCENE_EXCLUDED_STATIC"]}})));
    ok(call(h,json!({"op":"create_presented","template":review["template"],"template_sha256":review["template_sha256"],
        "setup_sha256":review["setup_sha256"],"player_name":review["player_name"],"presentation":review["presentation"],
        "title":"Synthetic presented Host scene","creation_id":"scene-presented-creation"})))
    }else{ok(call(h,json!({"op":"create","seed":"lantern-quay-v1"})))};
    assert_eq!(data["revision"],0);(data["session"].as_str().unwrap().into(),serde_json::from_value(data["scope"].clone()).unwrap())}
fn resume(h:&Host,scope:&Scope)->String{let data=ok(call(h,json!({"op":"resume","scope":scope})));assert_eq!(data["revision"],1);data["session"].as_str().unwrap().into()}
fn request(scope:&Scope,key:&str)->Request{Request{version:VERSION,scope:scope.clone(),turn:key.into(),expected_revision:0,
    intent:Intent::FreeText{kind:PlayInputKind::Action,text:"I wait for one tide tick.".into()}}}
fn submit(h:&Host,s:&str,r:&Request)->Value{call(h,json!({"op":"submit","session":s,"request":r,"mode":"accepted"}))}
fn op(h:&Host,s:&str,r:&Request,command:&str)->Value{call(h,json!({"op":command,"session":s,"scope":r.scope,"turn":r.turn}))}
fn configure_capture(h:&Host,s:&str,scope:&Scope,head:u64)->Value{call(h,json!({"op":"trace_capture_configure","session":s,
    "scope":scope,"expected_head":head,"enabled":true,"consent":true}))}
fn details(h:&Host,s:&str,r:&Request,head:u64,attempt:u64)->Value{ok(call(h,json!({"op":"trace_capture_read","session":s,"scope":r.scope,
    "expected_head":head,"base_revision":r.expected_revision,"turn":r.turn,"attempt":attempt})))}
fn equal_engine(actual:&Engine,expected:&Engine){assert_eq!(actual.seed(),expected.seed());assert_eq!(actual.scope(),expected.scope());
    assert_eq!(actual.revision(),expected.revision());assert_eq!(actual.canonical_records(),expected.canonical_records());
    assert_eq!(actual.canonical_bytes(),expected.canonical_bytes());assert_eq!(actual.accepted_history_basis().unwrap(),expected.accepted_history_basis().unwrap());
    for actor in ["player","mira","sable"]{assert_eq!(actual.character_context_v2(actor,actual.scope(),actual.revision()).unwrap(),expected.character_context_v2(actor,expected.scope(),expected.revision()).unwrap());}}
fn assert_request(copy:&Value,actual:&GenerationRequest){let Input::Structured{role,prompt,schema}=&actual.input else{panic!("actual structured request")};
    assert_eq!(copy,json!({"version":actual.version,"scope":actual.scope,"turn":actual.turn,"revision":actual.revision,
        "model_profile":actual.model_profile,"schema_id":actual.schema,"budget":{"max_output_bytes":actual.budget.max_output_bytes,
        "max_output_tokens":actual.budget.max_output_tokens,"max_pending_polls":actual.budget.max_pending_polls,"deadline_ms":actual.budget.deadline_ms},
        "input":{"kind":"structured","role":role,"prompt":prompt,"schema":schema}}));}

#[test]
fn actual_workspace_host_scene_both_arms_and_typed_presentations_commit_reopen_and_retry_exact_records(){
    for presented in [false,true]{for arm in [Arm::Memory,Arm::Literal]{
        let temp=Temp::new();let h=temp.host();let seen=Arc::new(Seen::default());
        h.configure_fixture_provider_with_construction(profile(),seen.factory(),arm.native()).unwrap();
        let(s,scope)=create(&h,presented);let r=request(&scope,"durable-host-scene");
        let before=h.generation_snapshot(&s,&scope,0,&||false).unwrap().engine;
        equal_engine(&temp.engine(&scope),&before);assert_eq!(before.seed().presentation.is_some(),presented);
        ok(configure_capture(&h,&s,&scope,0));
        assert_eq!(ok(submit(&h,&s,&r))["phase"],"queued");equal_engine(&temp.engine(&scope),&before);
        let ready=ok(op(&h,&s,&r,"prepare"));assert_eq!(ready["phase"],"ready");assert!(ready["receipt"].is_null());
        equal_engine(&temp.engine(&scope),&before); // real Store, not the generation clone
        let meta=ok(call(&h,json!({"op":"trace_read","session":s,"scope":scope,"expected_head":0,"base_revision":0,
            "observer":{"kind":"player"},"turn":r.turn,"attempt":null})));
        let attempt=meta["snapshot"]["attempts"][0]["identity"]["attempt"].as_u64().unwrap();
        assert_eq!(meta["snapshot"]["attempts"][0]["provenance"]["prompt_label"],arm.prompt());
        assert_eq!(meta["snapshot"]["attempts"][0]["provenance"]["schema_label"],arm.schema());
        assert!(meta["snapshot"]["attempts"][0]["provenance"]["model_sha256"].is_null());
        let captured=details(&h,&s,&r,0,attempt);assert_eq!(captured["details"]["status"],"recorded");
        assert_eq!(captured["details"]["identity"]["observer"],before.seed().player);
        assert_eq!(captured["details"]["identity"]["scope"],json!(scope));
        assert_eq!(captured["details"]["identity"]["turn"],r.turn);
        let artifacts=captured["details"]["artifacts"].as_array().unwrap();let actual=seen.requests();assert_eq!(actual.len(),2);
        for forwarded in &actual{let Input::Structured{role,..}=&forwarded.input else{unreachable!()};
            let rows:Vec<_>=artifacts.iter().filter(|a|a["kind"]=="generation_request"&&a["value"]["input"]["role"]==*role).collect();
            assert_eq!(rows.len(),1);assert_request(&rows[0]["value"],forwarded);}
        let candidate=artifacts.iter().find(|a|a["kind"]=="accepted_candidate_not_durable_commit").unwrap()["value"].clone();
        assert_eq!(artifacts.iter().any(|a|a["kind"]=="selected_context"),matches!(arm,Arm::Memory));
        assert_eq!(actual[0].schema,if matches!(arm,Arm::Literal){"locallore-director-literal-v1"}else{"locallore-director-v2"});
        let done=ok(op(&h,&s,&r,"commit"));assert_eq!(done["phase"],"committed");assert_eq!(done["receipt"],candidate);
        let play=&done["receipt"]["play"];assert_eq!(play["prompt_version"],arm.prompt());assert_eq!(play["policy"],POLICY);
        assert_eq!(play["context"].is_null(),matches!(arm,Arm::Literal));assert_eq!(play["context_policy"].is_null(),matches!(arm,Arm::Literal));
        let after=temp.engine(&scope);assert_eq!(after.revision(),1);assert_eq!(serde_json::to_value(after.receipts().last().unwrap()).unwrap(),done["receipt"]);
        equal_engine(&h.generation_snapshot(&s,&scope,1,&||false).unwrap().engine,&after);
        let Input::Structured{role,prompt,..}=&actual[1].input else{panic!("actual narrator")};assert_eq!(role,"narrator");
        let source=prompt.split_once("Post-turn scene frame: ").unwrap().1;let mut stream=serde_json::Deserializer::from_str(source).into_iter::<Value>();
        let frame=stream.next().unwrap().unwrap();let end=stream.byte_offset();
        assert_eq!(frame,json!({"version":1,"scope":scope,"before_revision":0,"after_revision":1,"player":before.seed().player,
            "location":after.character_context_v2(&before.seed().player,&scope,1).unwrap().self_state.location}));
        assert_eq!(play["scene"],json!({"version":1,"frame_sha256":sha256(&source.as_bytes()[..end])}));
        if presented{assert_eq!(play["story_presentation"],json!({"version":1,"presentation_sha256":sha256(&serde_json::to_vec(before.seed().presentation.as_ref().unwrap()).unwrap())}));
            assert!(prompt.contains("SCENE_EXCLUDED_STATIC"));}else{assert!(play["story_presentation"].is_null());}
        assert!(!prompt.contains("SECRET-TIDE-731"));
        let saved=Store::open_read_only(&temp.db()).unwrap().lookup_turn(&scope,&r.turn).unwrap();assert_eq!(saved.phase,TurnPhase::Committed);
        assert_eq!(serde_json::to_value(saved.receipt.unwrap()).unwrap(),done["receipt"]);
        let calls=seen.requests().len();assert_eq!(seen.factories.load(Ordering::SeqCst),1);
        h.close_all();assert_eq!(h.live_counts(),(0,0));drop(h);
        let h=temp.host();h.configure_fixture_provider_with_construction(profile(),seen.factory(),arm.opposite().native()).unwrap();
        let reopened=resume(&h,&scope);equal_engine(&temp.engine(&scope),&after);
        let restored=ok(op(&h,&reopened,&r,"turn_status"));assert_eq!(restored["phase"],"committed");assert_eq!(restored["receipt"],done["receipt"]);
        let private=details(&h,&reopened,&r,1,attempt);assert_eq!(private["details"]["status"],"disabled");
        assert!(private["details"]["artifacts"].as_array().unwrap().is_empty());
        ok(configure_capture(&h,&reopened,&scope,1));
        for response in [submit(&h,&reopened,&r),op(&h,&reopened,&r,"prepare"),op(&h,&reopened,&r,"commit")]{
            let retry=ok(response);assert_eq!(retry["phase"],"committed");assert_eq!(retry["receipt"],done["receipt"]);}
        let not_retroactive=details(&h,&reopened,&r,1,attempt);assert_eq!(not_retroactive["details"]["status"],"not_retained");
        assert!(not_retroactive["details"]["artifacts"].as_array().unwrap().is_empty());
        assert_eq!(seen.factories.load(Ordering::SeqCst),1);assert_eq!(seen.requests().len(),calls);
        equal_engine(&temp.engine(&scope),&after);equal_engine(&h.generation_snapshot(&reopened,&scope,1,&||false).unwrap().engine,&after);
        h.close_all();assert_eq!(h.live_counts(),(0,0));
    }}
}

#[test]
fn actual_workspace_cancelled_and_stale_scene_candidates_never_become_durable_receipts(){
    for arm in [Arm::Memory,Arm::Literal]{for prepared in [false,true]{
        let temp=Temp::new();let h=temp.host();let seen=Arc::new(Seen::default());h.configure_fixture_provider_with_construction(profile(),seen.factory(),arm.native()).unwrap();
        let(s,scope)=create(&h,false);let r=request(&scope,"durable-cancel");let before=temp.engine(&scope);
        ok(submit(&h,&s,&r));if prepared{assert_eq!(ok(op(&h,&s,&r,"prepare"))["phase"],"ready");}
        assert_eq!(ok(op(&h,&s,&r,"cancel"))["phase"],"cancelled");
        assert_eq!(ok(op(&h,&s,&r,"prepare"))["phase"],"cancelled");
        let terminal=ok(op(&h,&s,&r,"commit"));assert_eq!(terminal["phase"],"cancelled");assert!(terminal["receipt"].is_null());
        equal_engine(&temp.engine(&scope),&before);h.close_all();drop(h);
        let h=temp.host();let data=ok(call(&h,json!({"op":"resume","scope":scope})));let s=data["session"].as_str().unwrap();
        assert_eq!(data["revision"],0);assert_eq!(ok(op(&h,s,&r,"turn_status"))["phase"],"cancelled");equal_engine(&temp.engine(&scope),&before);
        assert_eq!(seen.factories.load(Ordering::SeqCst),usize::from(prepared));assert_eq!(seen.requests().len(),if prepared{2}else{0});h.close_all();assert_eq!(h.live_counts(),(0,0));
    }
        let temp=Temp::new();let h=temp.host();let seen=Arc::new(Seen::default());h.configure_fixture_provider_with_construction(profile(),seen.factory(),arm.native()).unwrap();
        let(s,scope)=create(&h,false);let r=request(&scope,"durable-stale");ok(submit(&h,&s,&r));assert_eq!(ok(op(&h,&s,&r,"prepare"))["phase"],"ready");
        let winning=Request{intent:Intent::Actions(vec![Command::Wait{ticks:1}]),turn:"actual-other-host-turn".into(),..r.clone()};
        ok(submit(&h,&s,&winning));ok(op(&h,&s,&winning,"prepare"));assert_eq!(ok(op(&h,&s,&winning,"commit"))["phase"],"committed");
        let expected=temp.engine(&scope);let stale=ok(op(&h,&s,&r,"commit"));assert_eq!(stale["phase"],"stale");assert!(stale["receipt"].is_null());
        equal_engine(&temp.engine(&scope),&expected);h.close_all();drop(h);
        let h=temp.host();let s=resume(&h,&scope);let persisted=ok(op(&h,&s,&r,"turn_status"));assert_eq!(persisted["phase"],"stale");assert!(persisted["receipt"].is_null());
        equal_engine(&temp.engine(&scope),&expected);assert_eq!(seen.factories.load(Ordering::SeqCst),1);assert_eq!(seen.requests().len(),2);
        h.close_all();assert_eq!(h.live_counts(),(0,0));
    }
}

#[test]
fn actual_workspace_old_ordinary_and_presented_host_recipes_are_not_repointed(){
    for presented in [false,true]{for literal in [false,true]{let temp=Temp::new();let h=temp.host();let seen=Arc::new(Seen::default());
        if literal{h.configure_fixture_provider_with_construction(profile(),seen.factory(),if presented{HostPlayConstructionV1::PlayerLiteralPresentationV1}else{HostPlayConstructionV1::PlayerLiteralV1}).unwrap();}
        else{h.configure_fixture_provider(profile(),seen.factory()).unwrap();}
        let(s,scope)=create(&h,presented);let r=request(&scope,"old-durable-host-control");ok(submit(&h,&s,&r));ok(op(&h,&s,&r,"prepare"));let done=ok(op(&h,&s,&r,"commit"));
        let play=&done["receipt"]["play"];assert_eq!(play["prompt_version"],match(presented,literal){(false,false)=>"locallore-play-v2.5",(false,true)=>"locallore-play-v2.6-literal-director-v1",
            (true,false)=>"locallore-play-v2.7-story-presentation-v1",(true,true)=>"locallore-play-v2.8-literal-director-v1-story-presentation-v1"});
        assert!(play.get("scene").is_none());let expected=temp.engine(&scope);h.close_all();drop(h);let h=temp.host();let s=resume(&h,&scope);
        assert_eq!(play["policy"],if presented{"grounded-prose-v2.3-story-presentation-v1"}else{"grounded-prose-v2.2"});
        assert_eq!(ok(op(&h,&s,&r,"turn_status"))["receipt"],done["receipt"]);equal_engine(&temp.engine(&scope),&expected);h.close_all();assert_eq!(h.live_counts(),(0,0));
    }}
}
