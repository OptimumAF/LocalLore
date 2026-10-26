// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen SOURCE ONLY / UNCOMPILED / UNRUN. Actual Core Host/private capture and
//! existing RecordingProvider, static fake outputs only. Mutated diagnostic
//! copies are NOT actual Host evidence, accepted Receipts or execution grants.
use crate::*;
use crate::{local_recording::{ForbiddenByRole,Recording,RecordingProvider},
    memory_comparison_v3::{arm_descriptors,ArmDescriptorV3,ComparisonArmV3,CapturedLiteralContext}};
use locallore::{author_correction::*,context_compiler::{player_literal_transcript_v1_cancelled,ContextPolicy},
    host::{HostPlayConstructionV1,ProviderFactory},play::{self,DirectorPassV25}};
use std::{sync::OnceLock, sync::atomic::Ordering};

#[derive(Clone,Copy,Debug,PartialEq,Eq)]enum Origin{ActualHost,MutatedDiagnosticCopy}
#[derive(Clone)]struct Fixture{origin:Origin,before:Engine,request:Request,reply:Value,captures:Vec<Capture>,profile:PlayProfile,attempt:u32,committed:Option<Value>}
fn profile()->PlayProfile{PlayProfile{id:"synthetic-literal-capture".into(),model_sha256:"a".repeat(64),runtime_revision:"b".repeat(40),template_sha256:"c".repeat(64),worker_sha256:"d".repeat(64),profile_manifest_sha256:"e".repeat(64),context_tokens:4096,director_tokens:350,narrator_tokens:350,deadline_ms:120000,repair_limit:1}}
fn call(h:&Host,c:Value)->Value{h.call(&encode(&json!({"version":1,"command":c})).unwrap())}
fn op(h:&Host,s:&str,r:&Request,name:&str)->Value{call(h,json!({"op":name,"session":s,"scope":r.scope,"turn":r.turn}))}
fn submit(h:&Host,s:&str,r:&Request)->Value{call(h,json!({"op":"submit","session":s,"request":r,"mode":"accepted"}))}
const HISTORY:&str="Original history 雪 café \"quoted\" \\ harbor\nsecond line";
struct Script{directors:usize,dialogue:bool}
impl InferenceProvider for Script{fn poll(&mut self,r:&GenerationRequest,_:&Cancellation)->Poll<std::result::Result<Vec<u8>,Error>>{
    let Input::Structured{role,prompt,..}=&r.input else{panic!("actual structured request")};
    if role=="director"{self.directors+=1;if self.directors==1{return Poll::Ready(Ok(b"{".to_vec()));}}
    let value=if role=="director"{let frame=serde_json::Deserializer::from_str(prompt.split_once("Literal conversation data: ").unwrap().1).into_iter::<Value>().next().unwrap().unwrap();self.dialogue=frame["kind"]=="dialogue";
        if self.dialogue{json!({"commands":[{"op":"say","text":frame["player_text"],"audience":["mira"]}]})}else{json!({"commands":[{"op":"wait","ticks":1}]})}}
        else{assert_eq!(role,"narrator");json!({"text":if self.dialogue{"Your words are heard by the chosen listeners."}else{"You pause as a tide tick passes."},"event_ids":[r.revision+1],"speaker":"narrator"})};Poll::Ready(encode(&value).map_err(|_|Error::Provider))}}
fn build(kind:PlayInputKind,guard:bool)->Fixture{
    let h=Host::new(true);let made=call(&h,json!({"op":"create","seed":"lantern-quay-v1"}));assert_eq!(made["status"],"ok");
    let session=made["data"]["session"].as_str().unwrap();let scope:Scope=serde_json::from_value(made["data"]["scope"].clone()).unwrap();
    let first=Engine::new({let mut s:Seed=serde_json::from_slice(SEED).unwrap();s.scope=scope.clone();s}).unwrap();
    let history=first.request("history",Intent::Dialogue{text:HISTORY.into(),audience:["mira".into()].into()});
    assert_eq!(submit(&h,session,&history)["data"]["phase"],"queued");assert_eq!(op(&h,session,&history,"prepare")["data"]["phase"],"ready");assert_eq!(op(&h,session,&history,"commit")["data"]["phase"],"committed");
    // Actual selected Engine from the existing coherent native read, not a
    // reconstructed compiler package or a fabricated accepted history.
    let before=h.generation_snapshot(session,&scope,1,&||false).unwrap().engine;
    let recording=Arc::new(Recording::default());let factory:ProviderFactory={let recording=recording.clone();Arc::new(move||Box::new(RecordingProvider::new(Box::new(Script{directors:0,dialogue:false}),recording.clone(),vec![],ForbiddenByRole::default())))};
    h.configure_fixture_provider_with_construction(profile(),factory,HostPlayConstructionV1::PlayerLiteralV1).unwrap();
    let text=if guard{"I juggle clouds."}else if kind==PlayInputKind::Action{"I wait for one tide tick."}else{"Current literal 雪 \"quote\" \\ path"};
    let request=before.request("literal-capture",Intent::FreeText{kind,text:text.into()});
    for command in [json!({"op":"trace_configure","session":session,"scope":scope,"expected_head":1,"enabled":true}),json!({"op":"trace_capture_configure","session":session,"scope":scope,"expected_head":1,"enabled":true,"consent":true})]{assert_eq!(call(&h,command)["status"],"ok");}
    assert_eq!(submit(&h,session,&request)["data"]["phase"],"queued");let prepared=op(&h,session,&request,"prepare");
    if guard{assert_eq!(prepared["data"]["phase"],"failed");}else{assert_eq!(prepared["data"]["phase"],"ready","{prepared}");assert!(prepared["data"]["receipt"].is_null());}
    let trace=call(&h,json!({"op":"trace_read","session":session,"scope":scope,"expected_head":1,"base_revision":1,"observer":{"kind":"player"},"turn":request.turn,"attempt":null}));
    let attempt=u32::try_from(trace["data"]["snapshot"]["attempts"].as_array().unwrap().last().unwrap()["identity"]["attempt"].as_u64().unwrap()).unwrap();
    let reply=call(&h,json!({"op":"trace_capture_read","session":session,"scope":scope,"expected_head":1,"base_revision":1,"turn":request.turn,"attempt":attempt}));
    let captures=recording.state.lock().unwrap().captures.clone();assert!(!recording.lost.load(Ordering::SeqCst));
    assert_eq!(recording.roles.load(Ordering::SeqCst),if guard{0}else{3});
    let committed=if guard{None}else{let done=op(&h,session,&request,"commit");assert_eq!(done["data"]["phase"],"committed");Some(done["data"]["receipt"].clone())};
    Fixture{origin:Origin::ActualHost,before,request,reply,captures,profile:profile(),attempt,committed}
}
fn fixtures()->&'static [Fixture]{static F:OnceLock<Vec<Fixture>>=OnceLock::new();F.get_or_init(||vec![build(PlayInputKind::Action,false),build(PlayInputKind::Dialogue,false)])}
impl Fixture{
    fn gate(&self)->Result<CapturedLiteralContext>{CapturedLiteralContext::from_host_capture(&self.before,&self.request,self.attempt,&self.reply,&self.captures,&self.profile,1)}
    fn copied(&self)->Self{let mut c=self.clone();c.origin=Origin::MutatedDiagnosticCopy;c}
    fn artifacts(&self)->&Vec<Value>{self.reply["data"]["details"]["artifacts"].as_array().unwrap()}
    fn artifacts_mut(&mut self)->&mut Vec<Value>{self.reply["data"]["details"]["artifacts"].as_array_mut().unwrap()}
    fn generation(&self,n:usize)->&Value{&self.artifacts().iter().filter(|a|a["kind"]=="generation_request").nth(n).unwrap()["value"]}
    fn generation_mut(&mut self,n:usize)->&mut Value{&mut self.artifacts_mut().iter_mut().filter(|a|a["kind"]=="generation_request").nth(n).unwrap()["value"]}
    fn candidate_mut(&mut self)->&mut Value{&mut self.artifacts_mut().iter_mut().find(|a|a["kind"]=="accepted_candidate_not_durable_commit").unwrap()["value"]}
    fn rehash(&mut self,n:usize){let prompt=self.generation(n)["input"]["prompt"].as_str().unwrap();let p=digest(prompt.as_bytes());let s=digest(&encode(&self.generation(n)["input"]["schema"]).unwrap());self.captures[n].prompt_sha256=p;self.captures[n].schema_sha256=s;}
    fn renumber(&mut self){for(i,a)in self.artifacts_mut().iter_mut().enumerate(){a["ordinal"]=json!(i);}}
    fn refused(&self){assert_eq!(self.origin,Origin::MutatedDiagnosticCopy);match self.gate(){Err(_)=>{},Ok(_)=>panic!("mutated diagnostic capture was accepted")}}
}

#[test]
fn actual_host_both_modes_one_repair_match_full_core_renderer_and_plain_recording(){
    for f in fixtures(){assert_eq!(f.origin,Origin::ActualHost);let bytes=encode(&f.reply).unwrap();let basis=f.before.accepted_history_basis().unwrap();let checked=f.gate().unwrap();
        assert_eq!(checked.director_prompts.len(),2);assert_eq!(checked.narrator_prompts.len(),1);assert_eq!(checked.director_estimates.len(),2);assert_eq!(f.captures.len(),3);
        let source=player_literal_transcript_v1_cancelled(&f.before,f.before.scope(),f.before.revision(),"player",&||false).unwrap();
        for(n,pass)in [(0,DirectorPassV25::Initial),(1,DirectorPassV25::Repair)]{let rendered=play::render_player_literal_director_v1_cancelled(&f.before,&f.request,&source,&f.profile,pass,&||false).unwrap();
            assert_eq!(checked.director_prompts[n],rendered.prompt());assert_eq!(f.generation(n)["input"]["schema"],*rendered.schema());assert_eq!(f.generation(n)["schema_id"],"locallore-director-literal-v1");
            assert_eq!(checked.director_estimates[n],serde_json::to_value(rendered.forwarded()).unwrap());assert_eq!(checked.source_units,rendered.source_units());assert_eq!(checked.selected_start,rendered.selected_start());assert_eq!(checked.selected_units,rendered.selected_units());}
        for c in &f.captures{assert!(c.compiler_version.is_none());assert!(c.player_text_sha256.is_none());}
        assert!(f.artifacts().iter().all(|a|a["kind"]!="selected_context"));let candidate=&f.artifacts().iter().find(|a|a["kind"]=="accepted_candidate_not_durable_commit").unwrap()["value"];
        assert_eq!(Some(candidate),f.committed.as_ref());assert_eq!(candidate["play"]["prompt_version"],play::LITERAL_PLAY_PROMPT_VERSION_V1);assert!(candidate["play"]["context"].is_null());assert!(candidate["play"]["context_policy"].is_null());
        assert_eq!(f.before.accepted_history_basis().unwrap(),basis);assert_eq!(encode(&f.reply).unwrap(),bytes);assert!(f.gate().is_ok());
    }
}

#[test]
fn descriptor_metadata_has_closed_required_shape_exact_tuple_and_no_native_grant(){
    let d=arm_descriptors();assert!(matches!(&d[0].arm,ComparisonArmV3::LiteralPlayerV1));assert!(matches!(&d[1].arm,ComparisonArmV3::RelevantMemoryV1));
    let keys=["arm","prompt_version","narration_policy","director_schema_id","context_policy","compiler_version","context_version","literal_source_version","literal_render_version","literal_schema_version","literal_packing_version","forwarded_budget_version"];
    for(index,descriptor)in d.iter().enumerate(){descriptor.validate().unwrap();let value=serde_json::to_value(descriptor).unwrap();assert_eq!(value.as_object().unwrap().len(),keys.len());for key in keys{assert!(value.get(key).is_some());}
        assert_eq!(value["arm"],if index==0{"literal_player_v1"}else{"relevant_memory_v1"});assert_eq!(value["narration_policy"],"grounded-prose-v2.2");assert_eq!(value["forwarded_budget_version"],1);
        if index==0{assert_eq!(value["prompt_version"],play::LITERAL_PLAY_PROMPT_VERSION_V1);assert_eq!(value["director_schema_id"],"locallore-director-literal-v1");for key in ["context_policy","compiler_version","context_version"]{assert!(value[key].is_null());}for key in ["literal_source_version","literal_render_version","literal_schema_version","literal_packing_version"]{assert_eq!(value[key],1);}}
        else{assert_eq!(value["prompt_version"],play::PROMPT_VERSION);assert_eq!(value["director_schema_id"],"locallore-director-v2");assert_eq!(value["context_policy"],json!(ContextPolicy::StateRelevantMemoryV1));assert_eq!(value["compiler_version"],2);assert_eq!(value["context_version"],2);for key in ["literal_source_version","literal_render_version","literal_schema_version","literal_packing_version"]{assert!(value[key].is_null());}}
        let decoded:ArmDescriptorV3=serde_json::from_value(value.clone()).unwrap();decoded.validate().unwrap();assert_eq!(serde_json::to_value(decoded).unwrap(),value);
        for key in keys{let mut missing=value.clone();missing.as_object_mut().unwrap().remove(key);assert!(serde_json::from_value::<ArmDescriptorV3>(missing).is_err());}
        let mut unknown=value.clone();unknown["execution_granted"]=json!(true);assert!(serde_json::from_value::<ArmDescriptorV3>(unknown).is_err());
        for key in keys{let mut changed=value.clone();changed[key]=match key{"arm"=>json!(if index==0{"relevant_memory_v1"}else{"literal_player_v1"}),"prompt_version"|"narration_policy"|"director_schema_id"=>json!("unsupported"),"context_policy"=>if index==0{json!("state_relevant_memory_v1")}else{Value::Null},_=>json!(99)};if let Ok(parsed)=serde_json::from_value::<ArmDescriptorV3>(changed){assert!(parsed.validate().is_err());}}
    }
    let h=Host::new(false);assert_eq!(call(&h,json!({"op":"configure_play_construction","descriptor":serde_json::to_value(&d[0]).unwrap()}))["error"],"Malformed");assert_eq!(call(&h,json!({"op":"model_status"}))["data"]["real_model"],false);
}

#[test]
fn fully_rehashed_director_prefix_tail_state_schema_and_repair_copies_still_refuse(){
    for f in fixtures(){for fault in 0..6{let mut c=f.copied();let n=if fault==5{1}else{0};let old=c.generation(n)["input"]["prompt"].as_str().unwrap().to_owned();
        match fault{0=>c.generation_mut(n)["input"]["prompt"]=json!(format!("COPY_PREFIX {old}")),1=>c.generation_mut(n)["input"]["prompt"]=json!(format!("{old} ")),
            2=>{let(before,rest)=old.split_once("Literal conversation data: ").unwrap();let mut stream=serde_json::Deserializer::from_str(rest).into_iter::<Value>();let mut frame=stream.next().unwrap().unwrap();let end=stream.byte_offset();frame["inventory"]=json!({"COPY_ONLY":"not forwarded"});c.generation_mut(n)["input"]["prompt"]=json!(format!("{before}Literal conversation data: {frame}{}",&rest[end..]));},
            3=>c.generation_mut(n)["input"]["schema"]["x-state-copy"]=json!("not actual Host input"),4=>c.generation_mut(n)["input"]["schema"]=json!({"type":"object"}),_=>c.generation_mut(n)["input"]["prompt"]=json!(format!("{old} ")),}
        c.rehash(n);let pass=if n==0{DirectorPassV25::Initial}else{DirectorPassV25::Repair};assert!(play::director_forwarded_budget_v25(&c.profile,pass,c.generation(n)["input"]["prompt"].as_str().unwrap(),&c.generation(n)["input"]["schema"]).is_ok());
        assert_eq!(c.captures[n].prompt_sha256,digest(c.generation(n)["input"]["prompt"].as_str().unwrap().as_bytes()));assert_eq!(c.captures[n].schema_sha256,digest(&encode(&c.generation(n)["input"]["schema"]).unwrap()));c.refused();
    }}
}

#[test]
fn copied_identity_profile_deadline_budget_schema_id_and_recording_annotations_refuse(){
    let f=&fixtures()[0];for fault in 0..13{let mut c=f.copied();match fault{
        0=>c.reply["data"]["details"]["identity"]["attempt"]=json!(c.attempt+1),1=>c.reply["data"]["details"]["identity"]["observer"]=json!("mira"),
        2=>c.generation_mut(0)["scope"]["story"]=json!("foreign"),3=>c.generation_mut(0)["model_profile"]=json!("wrong-valid-profile"),4=>c.generation_mut(0)["schema_id"]=json!("locallore-director-v2"),
        5=>c.generation_mut(0)["budget"]["deadline_ms"]=json!(0),6=>c.generation_mut(0)["budget"]["deadline_ms"]=json!(120001),7=>c.generation_mut(0)["budget"]["max_output_tokens"]=json!(351),
        8=>c.captures[0].compiler_version=Some(2),9=>c.captures[0].player_text_sha256=Some(digest(b"copied annotation")),10=>c.captures[0].prompt_sha256="0".repeat(64),
        11=>c.profile.id="different-valid-profile".into(),_=>c.generation_mut(0)["input"]["schema"]=Value::Null,}c.refused();}
    for version in [0,2]{match CapturedLiteralContext::from_host_capture(&f.before,&f.request,f.attempt,&f.reply,&f.captures,&f.profile,version){Err(_)=>{},Ok(_)=>panic!("unknown forwarded budget version accepted")}}
}

#[test]
fn ordered_role_multiplicity_and_artifact_closure_reject_renumbered_mutated_copies(){
    let f=&fixtures()[0];for fault in 0..6{let mut c=f.copied();let generation:Vec<_>=c.artifacts().iter().enumerate().filter(|(_,a)|a["kind"]=="generation_request").map(|(n,_)|n).collect();match fault{
        0=>c.captures.swap(0,2),1=>c.artifacts_mut().swap(generation[0],generation[2]),
        2=>{let duplicate=c.artifacts()[generation[0]].clone();c.artifacts_mut().insert(generation[0]+1,duplicate);},
        3=>c.artifacts_mut().push(json!({"kind":"selected_context","ordinal":0,"value":{}})),
        4=>c.artifacts_mut().push(json!({"kind":"unknown_artifact","ordinal":0,"value":{}})),_=>c.captures[2].role="director".into(),}
        c.renumber();c.refused();}
}

#[test]
fn actual_guard_absence_empty_recording_and_refused_source_identity_are_never_positive(){
    let guard=build(PlayInputKind::Action,true);match guard.gate(){Err(error)=>assert_eq!(error,"CaptureUnavailable"),Ok(_)=>panic!("guard absence is not literal evidence")}
    let f=&fixtures()[0];let mut empty=f.copied();empty.captures.clear();match empty.gate(){Err(error)=>assert_eq!(error,"CaptureUnavailable"),Ok(_)=>panic!("empty recording is unavailable")}
    let mut no_director=f.copied();no_director.artifacts_mut().retain(|a|a["kind"]!="generation_request"||a["value"]["input"]["role"]!="director");no_director.captures.retain(|c|c.role!="director");no_director.renumber();match no_director.gate(){Err(error)=>assert_eq!(error,"CaptureUnavailable"),Ok(_)=>panic!("no director is unavailable")}
    let mut appended=f.copied();let r=appended.before.request("later",Intent::Actions(vec![Command::Wait{ticks:1}]));let p=Engine::proposal(&r).unwrap();let v=appended.before.preview(&r,&p).unwrap();appended.before.commit_prepared(&v).unwrap();appended.refused();
    let mut scope=f.copied();scope.before=scope.before.fork("different-scope",scope.before.revision()).unwrap();scope.refused();
    // Actual changed-player Seed changes identity. This gate cannot authenticate
    // arbitrary unrelated Seed changes invisible to literal bytes; full source
    // fingerprint/canonical row/ledger validation remains its owner's job.
    let mut changed_player=f.copied();let mut seed=changed_player.before.seed().clone();seed.player="mira".into();let mut e=Engine::new(seed).unwrap();let r=e.request("history",Intent::Dialogue{text:HISTORY.into(),audience:["mira".into()].into()});let p=Engine::proposal(&r).unwrap();let v=e.preview(&r,&p).unwrap();e.commit_prepared(&v).unwrap();changed_player.before=e;changed_player.refused();
    let mut d2=f.copied();let input=AuthorCorrectionInputV1{version:1,parent:d2.before.scope().clone(),expected_parent_revision:d2.before.revision(),fork_revision:d2.before.revision(),child_branch:"authored".into(),operation:AuthorCorrectionOperationV1::ReplaceFactProposition{fact:"ancestry".into(),expected_proposition:d2.before.seed().facts["ancestry"].proposition.clone(),replacement:"PRIVATE_B".into()},reason:"PRIVATE_REASON".into()};d2.before=d2.before.apply_author_correction(&d2.before.prepare_author_correction(&input,&||false).unwrap(),&||false).unwrap().engine;assert_eq!(d2.before.domain_version(),2);d2.refused();
}

#[test]
fn candidate_tuple_is_strict_but_narrator_gate_is_not_renderer_or_raw_output_authentication(){
    let f=&fixtures()[0];for fault in 0..6{let mut c=f.copied();let record=&mut c.candidate_mut()["play"];match fault{0=>record["prompt_version"]=json!(play::PROMPT_VERSION),1=>record["policy"]=json!("grounded-prose-v2.1"),2=>record["profile"]["id"]=json!("different-valid-profile"),3=>record["context_policy"]=json!("state_relevant_memory_v1"),4=>record["context"]=json!({"copy_only":true}),_=>record["repairs"]=json!(2),}c.refused();}
    for fault in 0..3{let mut c=f.copied();match fault{0=>c.generation_mut(2)["schema_id"]=json!("not-narrator-schema"),1=>c.captures[2].schema_sha256="0".repeat(64),_=>c.generation_mut(2)["turn"]=json!("foreign-turn"),}c.refused();}
    // Explicitly copied/rehashed narrator prose proves ONLY the limited input
    // gate contract. It was NOT emitted by Host; it has no accepted/raw-output,
    // renderer-exactness or semantic-privacy authority. Director remains exact.
    let mut narrator_copy=f.copied();narrator_copy.generation_mut(2)["input"]["prompt"]=json!("Diagnostic-only narrator prompt copy, not an actual forwarded request.");narrator_copy.rehash(2);assert!(narrator_copy.gate().is_ok());
}
