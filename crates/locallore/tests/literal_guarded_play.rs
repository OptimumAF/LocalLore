// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen SOURCE ONLY / UNCOMPILED / UNRUN. Static scripted outputs exercise
//! actual Core guard/stage/narrator/replay, not model quality, Host, Store or UI.
use locallore::{author_correction::*,context_compiler::player_literal_transcript_v1_cancelled,
    contracts::*,engine::Engine,inference::*,play::{self,DirectorPassV25,PlayProfile},
    turn_capture::Artifact,turn_trace::{StageMeasurement,TraceSink}};
use serde_json::{json,Value};
use std::{collections::VecDeque,task::Poll};

fn fixture()->Engine{
    let mut s:Seed=serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    s.facts.get_mut("ancestry").unwrap().proposition="PRIVATE_SEED_CANARY".into();Engine::new(s).unwrap()
}
fn profile()->PlayProfile{PlayProfile{id:"synthetic-literal-play".into(),model_sha256:"a".repeat(64),runtime_revision:"b".repeat(40),
    template_sha256:"c".repeat(64),worker_sha256:"d".repeat(64),profile_manifest_sha256:"e".repeat(64),
    context_tokens:4096,director_tokens:350,narrator_tokens:350,deadline_ms:5000,repair_limit:1}}
fn request(e:&Engine,key:&str,kind:PlayInputKind,text:&str)->Request{e.request(key,Intent::FreeText{kind,text:text.into()})}
fn ordinary(e:&mut Engine,key:&str,intent:Intent)->Receipt{
    let r=e.request(key,intent);let p=Engine::proposal(&r).unwrap();let v=e.preview(&r,&p).unwrap();e.commit_prepared(&v).unwrap()
}
fn wait(e:&mut Engine,key:&str){ordinary(e,key,Intent::Actions(vec![Command::Wait{ticks:1}]));}
fn authored(e:&Engine)->Engine{
    let i=AuthorCorrectionInputV1{version:1,parent:e.scope().clone(),expected_parent_revision:e.revision(),fork_revision:e.revision(),child_branch:"authored".into(),
        operation:AuthorCorrectionOperationV1::ReplaceFactProposition{fact:"ancestry".into(),expected_proposition:"PRIVATE_SEED_CANARY".into(),replacement:"PRIVATE_B".into()},reason:"PRIVATE_AUTHOR_REASON".into()};
    e.apply_author_correction(&e.prepare_author_correction(&i,&||false).unwrap(),&||false).unwrap().engine
}
#[derive(Default)]
struct Script{replies:VecDeque<Vec<u8>>,seen:Vec<GenerationRequest>,cancel_role:Option<&'static str>}
impl InferenceProvider for Script{
    fn poll(&mut self,r:&GenerationRequest,c:&Cancellation)->Poll<Result<Vec<u8>,Error>>{
        self.seen.push(r.clone());if let Input::Structured{role,..}=&r.input{if self.cancel_role==Some(role.as_str()){c.cancel();}}
        Poll::Ready(self.replies.pop_front().ok_or(Error::Provider))
    }
}
impl Script{
    fn values(values:Vec<Value>)->Self{Self{replies:values.into_iter().map(|v|serde_json::to_vec(&v).unwrap()).collect(),..Self::default()}}
}
#[derive(Default)]
struct Capture{requests:Vec<GenerationRequest>,contexts:usize,measurements:usize}
impl TraceSink for Capture{
    fn matches(&mut self,_:&Scope,_:u64,_:&str,_:&str)->bool{true}
    fn record(&mut self,_:StageMeasurement){self.measurements+=1;}
    fn capture(&mut self,a:Artifact<'_>){match a{Artifact::Request(r)=>self.requests.push(r.clone()),Artifact::Context(_)=>self.contexts+=1,_=>{}}}
}
fn role(r:&GenerationRequest)->(&str,&str,&Value){match &r.input{Input::Structured{role,prompt,schema}=>(role,prompt,schema),_=>panic!("actual structured role required")}}
fn script(e:&Engine,r:&Request,malformed:bool,bad_narrator:bool)->Script{
    let Intent::FreeText{kind,text}=&r.intent else{panic!("actual fixture request")};
    let proposal=if *kind==PlayInputKind::Action{json!({"commands":[{"op":"wait","ticks":1}]})}
        else{json!({"commands":[{"op":"say","text":text,"audience":["mira"]}]})};
    let narration=if *kind==PlayInputKind::Action{"You pause as a tide tick passes."}else{"Your words are heard by the chosen listeners."};
    let mut p=Script::values(vec![proposal,if bad_narrator{json!({})}else{json!({"text":narration,"event_ids":[e.revision()+1],"speaker":"narrator"})}]);
    if malformed{p.replies.push_front(b"{".to_vec());}p
}
fn literal(e:&mut Engine,r:&Request,p:&mut Script)->Result<Receipt,Error>{
    play::execute_traced_with_literal_director_v1(e,r,p,&Cancellation::default(),&profile(),None)
}
fn generated(before:&Engine,r:&Request)->Receipt{let mut e=before.clone();let mut p=script(&e,r,false,false);literal(&mut e,r,&mut p).unwrap()}
fn normal(before:&Engine,r:&Request)->Receipt{let mut e=before.clone();let mut p=script(&e,r,false,false);play::execute(&mut e,r,&mut p,&Cancellation::default(),&profile()).unwrap()}
fn assert_record(receipt:&Receipt){let p=receipt.play().unwrap();assert_eq!(play::LITERAL_PLAY_PROMPT_VERSION_V1,"locallore-play-v2.6-literal-director-v1");
    assert_eq!(p.prompt_version,play::LITERAL_PLAY_PROMPT_VERSION_V1);assert_eq!(p.policy,"grounded-prose-v2.2");assert_eq!(p.version,play::PLAY_VERSION);
    assert!(p.context.is_none());assert!(p.context_policy.is_none());assert_eq!(p.profile,profile());}
fn assert_unchanged(e:&Engine,before:&Engine){assert_eq!(e.canonical_records(),before.canonical_records());assert_eq!(e.accepted_history_basis().unwrap(),before.accepted_history_basis().unwrap());}

#[test]
fn both_modes_use_actual_literal_rendered_director_bytes_and_sanitized_grounded_narrator(){
    for kind in [PlayInputKind::Action,PlayInputKind::Dialogue]{
        let mut e=fixture();ordinary(&mut e,"past",Intent::Dialogue{text:"HISTORY_ONLY_CANARY 雪 \"quote\" \\".into(),audience:["mira".into()].into()});
        let before=e.clone();let text=if kind==PlayInputKind::Action{"I wait for one tide tick."}else{"RAW_DIALOGUE_CANARY 雪 \"quote\" \\"};
        let r=request(&e,"literal",kind,text);let source=player_literal_transcript_v1_cancelled(&before,before.scope(),before.revision(),"player",&||false).unwrap();
        let rendered=play::render_player_literal_director_v1_cancelled(&before,&r,&source,&profile(),DirectorPassV25::Initial,&||false).unwrap();
        let mut p=script(&e,&r,false,false);let mut capture=Capture::default();
        let actual=play::execute_traced_with_literal_director_v1(&mut e,&r,&mut p,&Cancellation::default(),&profile(),Some(&mut capture)).unwrap();
        assert_record(&actual);assert!(!actual.play().unwrap().fallback);assert_eq!(p.seen.len(),2);assert_eq!(capture.requests.len(),2);assert_eq!(capture.contexts,0);assert!(capture.measurements>0);
        assert_eq!(p.seen[0].schema,"locallore-director-literal-v1");assert_eq!(p.seen[1].schema,"locallore-narrator-v2");
        assert_eq!(role(&p.seen[0]),("director",rendered.prompt(),rendered.schema()));
        for (seen,traced) in p.seen.iter().zip(&capture.requests){assert_eq!(role(seen),role(traced));assert_eq!(seen.schema,traced.schema);assert_eq!(seen.scope,r.scope);assert_eq!(seen.turn,r.turn);assert_eq!(seen.revision,r.expected_revision);assert_eq!(seen.model_profile,profile().id);}
        assert!(role(&p.seen[0]).1.contains("HISTORY_ONLY_CANARY"));assert!(!role(&p.seen[0]).1.contains("PRIVATE_SEED_CANARY"));
        let narrator=role(&p.seen[1]).1;for excluded in ["HISTORY_ONLY_CANARY","RAW_DIALOGUE_CANARY","PRIVATE_SEED_CANARY","player_text","original_input","Literal conversation data:"]{assert!(!narrator.contains(excluded));}
        assert_eq!(actual.request(),&r);assert_eq!(actual.events().len(),1);assert_eq!(e.revision(),before.revision()+1);
        assert_eq!(source.accepted_basis(),&before.accepted_history_basis().unwrap());
    }
}

#[test]
fn malformed_director_repairs_once_with_exact_renderer_and_malformed_narrator_falls_back(){
    for kind in [PlayInputKind::Action,PlayInputKind::Dialogue]{
        let mut e=fixture();let before=e.clone();let text=if kind==PlayInputKind::Action{"I wait for one tide tick."}else{"A literal quoted utterance."};
        let r=request(&e,"repair",kind,text);let s=player_literal_transcript_v1_cancelled(&e,e.scope(),e.revision(),"player",&||false).unwrap();let mut p=script(&e,&r,true,true);
        let receipt=literal(&mut e,&r,&mut p).unwrap();assert_record(&receipt);assert_eq!(receipt.play().unwrap().repairs,1);assert!(receipt.play().unwrap().fallback);assert_eq!(p.seen.len(),3);
        for (index,pass) in [(0,DirectorPassV25::Initial),(1,DirectorPassV25::Repair)]{
            let rendered=play::render_player_literal_director_v1_cancelled(&before,&r,&s,&profile(),pass,&||false).unwrap();
            assert_eq!(role(&p.seen[index]),("director",rendered.prompt(),rendered.schema()));assert_eq!(p.seen[index].schema,"locallore-director-literal-v1");
        }
        assert!(play::director_repair_matches_v25(role(&p.seen[0]).1,role(&p.seen[1]).1));assert_eq!(role(&p.seen[2]).0,"narrator");
        let approved=before.stage_play_v25(&r,receipt.proposal(),&||false).unwrap();assert_eq!(receipt.narration(),approved.approved().narration());
    }
}

#[test]
fn finite_guard_and_actual_wrong_proposals_refuse_without_substituting_expected_commands(){
    for (text,error) in [("I juggle clouds.",Error::ClarificationRequired),("I consume missing-item.",Error::Inventory)]{
        let mut e=fixture();let before=e.clone();let r=request(&e,"guard",PlayInputKind::Action,text);let mut p=Script::default();
        assert_eq!(literal(&mut e,&r,&mut p),Err(error));assert!(p.seen.is_empty());assert_unchanged(&e,&before);
    }
    for proposal in [json!({"commands":[{"op":"wait","ticks":2}]}),json!({"commands":[{"op":"consume","item":"never-existed"}]})]{
        let mut e=fixture();let before=e.clone();let r=request(&e,"wrong",PlayInputKind::Action,"I wait for one tide tick.");let mut p=Script::values(vec![proposal]);
        assert!(literal(&mut e,&r,&mut p).is_err());assert_eq!(p.seen.len(),1);assert_eq!(role(&p.seen[0]).0,"director");assert_unchanged(&e,&before);
    }
    let mut e=fixture();let before=e.clone();let r=request(&e,"bad-both",PlayInputKind::Action,"I wait for one tide tick.");
    let mut p=Script{replies:[b"{".to_vec(),b"{".to_vec()].into(),..Script::default()};assert!(literal(&mut e,&r,&mut p).is_err());assert_eq!(p.seen.len(),2);assert_unchanged(&e,&before);
}

#[test]
fn cancellation_at_director_or_narrator_and_new_domain2_work_never_commit(){
    for cancelled_role in ["director","narrator"]{
        let mut e=fixture();let before=e.clone();let r=request(&e,"cancelled",PlayInputKind::Action,"I wait for one tide tick.");let mut p=script(&e,&r,false,false);p.cancel_role=Some(cancelled_role);
        assert_eq!(literal(&mut e,&r,&mut p),Err(Error::Cancelled));assert_unchanged(&e,&before);assert_eq!(p.seen.len(),if cancelled_role=="director"{1}else{2});
    }
    let mut e=authored(&fixture());let before=e.clone();let r=request(&e,"d2-new",PlayInputKind::Action,"I wait for one tide tick.");let mut p=Script::default();
    assert_eq!(literal(&mut e,&r,&mut p),Err(Error::Version));assert!(p.seen.is_empty());assert_unchanged(&e,&before);
    let mut e=fixture();let before=e.clone();let r=request(&e,"pre-cancel",PlayInputKind::Action,"I wait for one tide tick.");let c=Cancellation::default();c.cancel();
    assert_eq!(play::execute_traced_with_literal_director_v1(&mut e,&r,&mut p,&c,&profile(),None),Err(Error::Cancelled));assert!(p.seen.is_empty());assert_unchanged(&e,&before);
}

#[test]
fn exact_recorded_retry_wins_cross_construction_profile_cancel_and_even_existing_domain2(){
    for make_literal in [false,true]{
        let mut e=fixture();let r=request(&e,"retry",PlayInputKind::Action,"I wait for one tide tick.");let mut p=script(&e,&r,false,false);
        let receipt=if make_literal{literal(&mut e,&r,&mut p).unwrap()}else{play::execute(&mut e,&r,&mut p,&Cancellation::default(),&profile()).unwrap()};
        let before=e.clone();let mut invalid=profile();invalid.context_tokens=0;let c=Cancellation::default();c.cancel();let mut no_roles=Script::default();
        assert_eq!(play::execute_traced_with_literal_director_v1(&mut e,&r,&mut no_roles,&c,&invalid,None).unwrap(),receipt);
        assert_eq!(play::execute(&mut e,&r,&mut no_roles,&c,&invalid).unwrap(),receipt);assert!(no_roles.seen.is_empty());assert_unchanged(&e,&before);
        assert_eq!(receipt.play().unwrap().prompt_version,if make_literal{play::LITERAL_PLAY_PROMPT_VERSION_V1}else{play::PROMPT_VERSION});
    }
    let mut d2=authored(&fixture());let r=request(&d2,"d2-recorded",PlayInputKind::Action,"I wait for one tide tick.");let mut p=script(&d2,&r,false,false);
    let recorded=play::execute(&mut d2,&r,&mut p,&Cancellation::default(),&profile()).unwrap();let before=d2.clone();let c=Cancellation::default();c.cancel();let mut bad=profile();bad.context_tokens=0;let mut none=Script::default();
    assert_eq!(play::execute_traced_with_literal_director_v1(&mut d2,&r,&mut none,&c,&bad,None).unwrap(),recorded);assert!(none.seen.is_empty());assert_unchanged(&d2,&before);
}

#[test]
fn native_commit_targets_are_closed_on_uncommitted_records_and_literal_stage_installs_actual_receipt(){
    let before=fixture();let r=request(&before,"staged",PlayInputKind::Action,"I wait for one tide tick.");let actual=generated(&before,&r);let memory=normal(&before,&r);
    let mut target=before.clone();let stage=target.stage_play_v25(&r,actual.proposal(),&||false).unwrap();
    assert!(target.commit_staged_play_v25(stage,actual.play().unwrap(),&||false).is_err());assert_unchanged(&target,&before);
    for prompt in ["locallore-play-v2.1","locallore-play-v2.2","locallore-play-v2.3","locallore-play-v2.4",play::PROMPT_VERSION]{
        let stage=target.stage_play_v25(&r,memory.proposal(),&||false).unwrap();let mut record=memory.play().unwrap().clone();record.prompt_version=prompt.into();
        assert!(target.commit_staged_literal_play_v1(stage,&record,&||false).is_err());assert_unchanged(&target,&before);
    }
    let stage=target.stage_play_v25(&r,actual.proposal(),&||false).unwrap();assert_eq!(stage.approved().events(),actual.events());
    let accepted=target.commit_staged_literal_play_v1(stage,actual.play().unwrap(),&||false).unwrap();assert_eq!(accepted,actual);assert_eq!(target.canonical_record_count(),1);
}

#[test]
fn native_stage_fences_append_same_head_different_seed_or_history_and_cancel(){
    let base=fixture();let r=request(&base,"pending",PlayInputKind::Action,"I wait for one tide tick.");let actual=generated(&base,&r);
    let mut appended=base.clone();let stage=appended.stage_play_v25(&r,actual.proposal(),&||false).unwrap();wait(&mut appended,"intervening");let keep=appended.clone();
    assert_eq!(appended.commit_staged_literal_play_v1(stage,actual.play().unwrap(),&||false),Err(Error::Stale));assert_unchanged(&appended,&keep);
    let mut s=base.seed().clone();s.facts.get_mut("ancestry").unwrap().proposition="DIFFERENT_VALID_SEED".into();let mut other=Engine::new(s).unwrap();
    let stage=base.stage_play_v25(&r,actual.proposal(),&||false).unwrap();let keep=other.clone();assert_eq!(other.revision(),base.revision());
    assert_eq!(other.commit_staged_literal_play_v1(stage,actual.play().unwrap(),&||false),Err(Error::Stale));assert_unchanged(&other,&keep);
    let mut a=fixture();wait(&mut a,"history-a");let mut b=fixture();wait(&mut b,"history-b");assert_eq!(a.canonical_bytes(),b.canonical_bytes());
    let q=request(&a,"same-head",PlayInputKind::Action,"I wait for one tide tick.");let receipt=generated(&a,&q);let stage=a.stage_play_v25(&q,receipt.proposal(),&||false).unwrap();let keep=b.clone();
    assert_eq!(b.commit_staged_literal_play_v1(stage,receipt.play().unwrap(),&||false),Err(Error::Stale));assert_unchanged(&b,&keep);
    for panic_cancel in [false,true]{let mut e=base.clone();let stage=e.stage_play_v25(&r,actual.proposal(),&||false).unwrap();
        assert_eq!(e.commit_staged_literal_play_v1(stage,actual.play().unwrap(),&||{if panic_cancel{panic!("fixed native cancel")}true}),Err(Error::Cancelled));assert_unchanged(&e,&base);}
}

#[test]
fn full_receipt_restore_prepared_canonical_replay_and_fork_continuation_use_no_provider(){
    let before=fixture();let r=request(&before,"literal",PlayInputKind::Action,"I wait for one tide tick.");let actual=generated(&before,&r);let mut e=before.clone();
    assert_eq!(e.commit_prepared(&actual).unwrap(),actual);let record_bytes=serde_json::to_vec(e.canonical_records()).unwrap();
    let history:Vec<_>=e.canonical_records().iter().map(|v|serde_json::to_string(v).unwrap()).collect();let restored=Engine::restore(e.seed().clone(),&history).unwrap();
    assert_eq!(serde_json::to_vec(restored.canonical_records()).unwrap(),record_bytes);assert_eq!(restored.accepted_history_basis().unwrap(),e.accepted_history_basis().unwrap());
    let direct=Engine::restore(e.seed().clone(),&[serde_json::to_string(&actual).unwrap()]).unwrap();assert_eq!(direct.receipts(),e.receipts());
    let replayed=Engine::replay_records(e.seed().clone(),e.canonical_records()).unwrap();assert_eq!(replayed.canonical_records(),e.canonical_records());
    let child_before=e.fork("literal-child",e.revision()).unwrap();let q=request(&child_before,"child-turn",PlayInputKind::Dialogue,"Child original literal text.");let child_receipt=generated(&child_before,&q);
    let continuation=vec![serde_json::to_string(&child_receipt).unwrap()];let child=child_before.restore_continuation(&continuation).unwrap();
    assert_eq!(child.receipts().last().unwrap(),&child_receipt);assert_eq!(child.receipts()[0],actual);
    let mut no_roles=Script::default();let mut child=child;assert_eq!(literal(&mut child,&q,&mut no_roles).unwrap(),child_receipt);assert!(no_roles.seen.is_empty());
}

#[test]
fn single_field_record_tampering_is_refused_on_uncommitted_basis_not_confused_with_retry(){
    let before=fixture();let r=request(&before,"tamper",PlayInputKind::Action,"I wait for one tide tick.");let actual=generated(&before,&r);let memory=normal(&before,&r);
    for fault in 0..8{let mut e=before.clone();let mut record=actual.play().unwrap().clone();match fault{
        0=>record.prompt_version="locallore-play-v99".into(),1=>record.prompt_version=play::PROMPT_VERSION.into(),
        2=>record.policy="grounded-prose-v2.1".into(),3=>record.context=memory.play().unwrap().context.clone(),
        4=>record.context_policy=memory.play().unwrap().context_policy,5=>record.profile.context_tokens=0,
        6=>record.repairs=2,_=>record.narration.event_ids=vec![u64::MAX],}
        let stage=e.stage_play_v25(&r,actual.proposal(),&||false).unwrap();assert!(e.commit_staged_literal_play_v1(stage,&record,&||false).is_err());assert_unchanged(&e,&before);
        // Explicitly tampered diagnostic/history copy; it is not an accepted
        // Receipt and is never deserialized as authority outside real restore.
        let mut copied=serde_json::to_value(&actual).unwrap();copied["play"]=serde_json::to_value(&record).unwrap();
        assert!(Engine::restore(before.seed().clone(),&[copied.to_string()]).is_err());
    }
    // Actual Domain2 stage, with a genuine literal record made on a separate
    // Domain1 branch at the same scope/head. No recorded key may hide refusal.
    let mut d2=authored(&before);let mut d1=before.fork("authored",0).unwrap();wait(&mut d1,"same-revision");
    let q=request(&d1,"domain-record",PlayInputKind::Action,"I wait for one tide tick.");let literal_record=generated(&d1,&q);let keep=d2.clone();
    let stage=d2.stage_play_v25(&q,literal_record.proposal(),&||false).unwrap();
    assert_eq!(d2.commit_staged_literal_play_v1(stage,literal_record.play().unwrap(),&||false),Err(Error::Version));assert_unchanged(&d2,&keep);
    // This tests single-field/explicit target fences, not cryptographic
    // authenticity against rewriting every field into another legal contract.
}
