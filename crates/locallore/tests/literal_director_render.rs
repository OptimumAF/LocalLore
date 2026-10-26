// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen SOURCE ONLY / UNCOMPILED / UNRUN. Actual Core receipts and native
//! data-only sources; no provider, generated receipt, runtime, Host or Store.
use locallore::{
    author_correction::{AuthorCorrectionInputV1,AuthorCorrectionOperationV1},
    context_compiler::{player_literal_transcript_v1_cancelled,LiteralTranscriptSourceV1},
    contracts::*, engine::Engine,
    play::{director_forwarded_budget_v25,director_repair_matches_v25,
        render_player_literal_director_v1_cancelled,DirectorPassV25,PlayProfile,RenderedLiteralDirectorV1},
};
use serde_json::{json,Value};
use std::cell::Cell;

const MARKER: &str = "Literal conversation data: ";
fn seed() -> Seed {
    let mut s: Seed = serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    s.scope.story = "SOURCE_STORY_CANARY".into(); s.scope.branch = "SOURCE_BRANCH_CANARY".into();
    s.facts.get_mut("ancestry").unwrap().proposition = "ELIGIBLE_SEED_NOT_CONVERSATION".into();
    s.facts.get_mut("relic-location").unwrap().proposition = "PRIVATE_SEED_NOT_CONVERSATION".into(); s
}
fn engine() -> Engine { Engine::new(seed()).unwrap() }
fn profile() -> PlayProfile {
    PlayProfile { id:"synthetic-literal-render".into(),model_sha256:"a".repeat(64),runtime_revision:"b".repeat(40),
        template_sha256:"c".repeat(64),worker_sha256:"d".repeat(64),profile_manifest_sha256:"e".repeat(64),
        context_tokens:4096,director_tokens:350,narrator_tokens:350,deadline_ms:120000,repair_limit:1 }
}
fn commit(e:&mut Engine,id:&str,intent:Intent) -> Receipt {
    let r=e.request(id,intent); let p=Engine::proposal(&r).unwrap(); let v=e.preview(&r,&p).unwrap(); e.commit_prepared(&v).unwrap()
}
fn dialogue(e:&mut Engine,id:&str,text:&str) -> Receipt {
    commit(e,id,Intent::Dialogue{text:text.into(),audience:["mira".into()].into()})
}
fn source(e:&Engine) -> LiteralTranscriptSourceV1 {
    player_literal_transcript_v1_cancelled(e,e.scope(),e.revision(),e.seed().player.as_str(),&||false).unwrap()
}
fn request(e:&Engine,kind:PlayInputKind,text:&str) -> Request { e.request("CURRENT_TURN_CANARY",Intent::FreeText{kind,text:text.into()}) }
fn render(e:&Engine,r:&Request,s:&LiteralTranscriptSourceV1,p:&PlayProfile,pass:DirectorPassV25) -> RenderedLiteralDirectorV1 {
    render_player_literal_director_v1_cancelled(e,r,s,p,pass,&||false).unwrap()
}
fn expect_error(result:Result<RenderedLiteralDirectorV1,Error>,expected:Error) {
    match result { Err(actual)=>assert_eq!(actual,expected),Ok(_)=>panic!("renderer accepted a refused input") }
}
fn exact(v:&Value,keys:&[&str]) -> bool { v.as_object().is_some_and(|o|o.len()==keys.len()&&keys.iter().all(|k|o.contains_key(*k))) }
// Parse exactly ONE JSON value using its actual byte end, retaining ALL fixed
// suffix bytes for the shared full-forwarded estimator. No English golden.
fn split(prompt:&str) -> (&str,Value,&str) {
    let (before,rest)=prompt.split_once(MARKER).expect("fixed literal frame marker");
    let mut stream=serde_json::Deserializer::from_str(rest).into_iter::<Value>();
    let frame=stream.next().unwrap().unwrap(); let end=stream.byte_offset();
    (before,frame,&rest[end..])
}
fn candidate(prompt:&str,conversation:Value) -> String {
    let (before,mut frame,after)=split(prompt); frame["conversation"]=conversation;
    format!("{before}{MARKER}{frame}{after}")
}
fn pairs(s:&LiteralTranscriptSourceV1,start:usize) -> Value {
    Value::Array(s.units()[start..].iter().map(|u| {
        let mut pair=serde_json::Map::new();
        if let Some(input)=u.original_input(){pair.insert("original_input".into(),json!(input));}
        pair.insert("narration".into(),json!(u.narration().expect("actual receipt narration"))); Value::Object(pair)
    }).collect())
}
fn assert_render(r:&RenderedLiteralDirectorV1,s:&LiteralTranscriptSourceV1,q:&Request,p:&PlayProfile,pass:DirectorPassV25) {
    assert_eq!(r.prompt_version(),"locallore-literal-director-v1"); assert_eq!(r.schema_version(),1); assert_eq!(r.packing_version(),1);
    assert_eq!(r.source_units(),s.units().len()); assert!(r.selected_units()<=128);
    assert_eq!(r.selected_units()+r.omitted_units(),r.source_units()); assert_eq!(r.selected_start(),r.omitted_units());
    assert_eq!(r.selected_start()+r.selected_units(),r.source_units());
    assert_eq!(r.selected_provenance().len(),r.selected_units());
    for (provenance,unit) in r.selected_provenance().iter().zip(&s.units()[r.selected_start()..]) {
        assert_eq!(provenance.original_scope(),unit.original_scope()); assert_eq!(provenance.turn(),unit.turn());
        assert_eq!(provenance.through_revision(),unit.through_revision());
    }
    let (_,frame,after)=split(r.prompt()); assert!(!after.trim().is_empty(),"fixed instructions follow JSON");
    assert!(exact(&frame,&["kind","player_text","conversation"]));
    let Intent::FreeText{kind,text}=&q.intent else {panic!("actual test request")};
    assert_eq!(frame["kind"],json!(kind)); assert_eq!(frame["player_text"],*text);
    assert_eq!(frame["conversation"],pairs(s,r.selected_start()));
    let computed=director_forwarded_budget_v25(p,pass,r.prompt(),r.schema()).unwrap();
    assert_eq!(r.forwarded(),&computed); assert!(computed.estimated_total_tokens()<=p.context_tokens);
}

#[test]
fn exact_unicode_recorded_pairs_typed_absence_empty_history_and_private_provenance() {
    let mut e=engine(); let text="雪 café \"quoted\" \\ harbor\nsecond line 🕯";
    let spoken=dialogue(&mut e,"RECORDED_TURN_CANARY",text);
    let typed=commit(&mut e,"TYPED_TURN_CANARY",Intent::Actions(vec![Command::Wait{ticks:1},Command::Wait{ticks:1}]));
    let s=source(&e); let q=request(&e,PlayInputKind::Dialogue,"CURRENT \"literal\" \\ 雪"); let p=profile();
    let r=render(&e,&q,&s,&p,DirectorPassV25::Initial); assert_render(&r,&s,&q,&p,DirectorPassV25::Initial);
    let frame=split(r.prompt()).1;
    assert_eq!(r.selected_units(),2);
    assert_eq!(frame["conversation"][0],json!({"original_input":text,"narration":spoken.narration()}));
    assert_eq!(frame["conversation"][1],json!({"narration":typed.narration()}));
    assert!(!frame["conversation"][1].as_object().unwrap().contains_key("original_input"));
    for forbidden in ["SOURCE_STORY_CANARY","SOURCE_BRANCH_CANARY","RECORDED_TURN_CANARY","TYPED_TURN_CANARY",
        "CURRENT_TURN_CANARY","ELIGIBLE_SEED_NOT_CONVERSATION","PRIVATE_SEED_NOT_CONVERSATION"] {
        assert!(!r.prompt().contains(forbidden)); assert!(!serde_json::to_string(r.schema()).unwrap().contains(forbidden));
    }
    let empty=engine();let empty_source=source(&empty);let empty_request=request(&empty,PlayInputKind::Action,"I wait.");
    let empty_render=render(&empty,&empty_request,&empty_source,&p,DirectorPassV25::Initial);
    assert_render(&empty_render,&empty_source,&empty_request,&p,DirectorPassV25::Initial);
    assert_eq!(split(empty_render.prompt()).1["conversation"],json!([])); assert_eq!(empty_render.selected_units(),0);
}

#[test]
fn ordinary_fork_repeated_turn_ids_keep_native_provenance_without_parent_future_or_sibling_prose() {
    let mut parent=engine();dialogue(&mut parent,"same-id","ROOT_LITERAL");let at=parent.revision();
    let mut child=parent.fork("CHILD_SCOPE_CANARY",at).unwrap();let mut sibling=parent.fork("SIBLING_SCOPE_CANARY",at).unwrap();
    dialogue(&mut parent,"parent-future","PARENT_FUTURE_CANARY");dialogue(&mut sibling,"same-id","SIBLING_TEXT_CANARY");
    dialogue(&mut child,"same-id","CHILD_LITERAL");let s=source(&child);let q=request(&child,PlayInputKind::Action,"I wait.");let p=profile();
    let r=render(&child,&q,&s,&p,DirectorPassV25::Initial);assert_render(&r,&s,&q,&p,DirectorPassV25::Initial);
    assert_eq!(r.selected_units(),2);assert_eq!(r.selected_provenance()[0].turn(),r.selected_provenance()[1].turn());
    assert_ne!(r.selected_provenance()[0].original_scope(),r.selected_provenance()[1].original_scope());
    for forbidden in ["SOURCE_STORY_CANARY","SOURCE_BRANCH_CANARY","CHILD_SCOPE_CANARY","SIBLING_SCOPE_CANARY",
        "same-id","PARENT_FUTURE_CANARY","SIBLING_TEXT_CANARY"] {assert!(!r.prompt().contains(forbidden));}
    assert_eq!(split(r.prompt()).1["conversation"][0]["original_input"],"ROOT_LITERAL");
    assert_eq!(split(r.prompt()).1["conversation"][1]["original_input"],"CHILD_LITERAL");
}

fn variants(schema:&Value)->&[Value]{schema["properties"]["commands"]["items"]["oneOf"].as_array().unwrap()}
fn id_grammar(value:&Value){
    assert_eq!(value["type"],"string");assert_eq!(value["minLength"],1);assert_eq!(value["maxLength"],64);
    assert_eq!(value["pattern"],"^[A-Za-z0-9_-]+$");assert!(value.get("const").is_none());assert!(value.get("enum").is_none());
}
#[test]
fn mode_grammar_is_static_across_worlds_with_only_current_dialogue_text_constant() {
    let a=engine();let mut other=seed();other.items.remove("potion");other.actors.get_mut("mira").unwrap().location="pier".into();
    other.facts.get_mut("ancestry").unwrap().proposition="DIFFERENT_CURRENT_WORLD".into();let b=Engine::new(other).unwrap();
    let p=profile();let sa=source(&a);let sb=source(&b);
    for kind in [PlayInputKind::Action,PlayInputKind::Dialogue] {
        let qa=request(&a,kind,"CURRENT EXACT TEXT");let qb=request(&b,kind,"CURRENT EXACT TEXT");
        let ra=render(&a,&qa,&sa,&p,DirectorPassV25::Initial);let rb=render(&b,&qb,&sb,&p,DirectorPassV25::Initial);
        assert_eq!(ra.schema(),rb.schema());
        for variant in variants(ra.schema()) {
            let fields=variant["properties"].as_object().unwrap();let op=fields["op"]["const"].as_str().unwrap();
            if kind==PlayInputKind::Action{assert_ne!(op,"say");}else{assert_eq!(op,"say");}
            for(name,value)in fields{
                if name=="op"{continue;}
                if kind==PlayInputKind::Dialogue&&name=="text"{assert_eq!(*value,json!({"const":"CURRENT EXACT TEXT"}));continue;}
                assert!(value.get("const").is_none());assert!(value.get("enum").is_none());
                if ["item","to","ability","fact"].contains(&name.as_str()){id_grammar(value);}
                if name=="audience"{assert_eq!(value["minItems"],1);assert_eq!(value["maxItems"],4);id_grammar(&value["items"]);}
            }
        }
        if kind==PlayInputKind::Dialogue{assert_eq!(variants(ra.schema()).len(),1);assert_eq!(ra.schema()["properties"]["commands"]["maxItems"],1);}
        else{
            let static_schema=locallore::play::director_schema();
            let expected:Vec<_>=variants(&static_schema).iter().filter(|v|v["properties"]["op"]["const"]!="say")
                .map(|v|v["properties"]["op"]["const"].clone()).collect();
            assert_eq!(variants(ra.schema()).iter().map(|v|v["properties"]["op"]["const"].clone()).collect::<Vec<_>>(),expected);
            let different=request(&a,kind,"I give potion to mira.");
            assert_eq!(render(&a,&different,&sa,&p,DirectorPassV25::Initial).schema(),ra.schema());
        }
    }
}

#[test]
fn initial_and_repair_share_selection_and_exact_existing_forwarded_budget_relation() {
    let mut e=engine();dialogue(&mut e,"history","Recorded \"Unicode\" 雪 \\ text");let s=source(&e);let p=profile();
    for kind in [PlayInputKind::Action,PlayInputKind::Dialogue]{
        let q=request(&e,kind,"CURRENT TEXT");let a=render(&e,&q,&s,&p,DirectorPassV25::Initial);let b=render(&e,&q,&s,&p,DirectorPassV25::Repair);
        assert_render(&a,&s,&q,&p,DirectorPassV25::Initial);assert_render(&b,&s,&q,&p,DirectorPassV25::Repair);
        assert_eq!(a.selected_start(),b.selected_start());assert_eq!(a.selected_units(),b.selected_units());assert_eq!(a.schema(),b.schema());
        assert!(director_repair_matches_v25(a.prompt(),b.prompt()));
    }
    let mut no_repair=p.clone();no_repair.repair_limit=0;let q=request(&e,PlayInputKind::Action,"I wait.");
    expect_error(render_player_literal_director_v1_cancelled(&e,&q,&s,&no_repair,DirectorPassV25::Repair,&||false),Error::Rule);
}

#[test]
fn packing_stops_at_first_nonfitting_older_whole_unit_without_backfill() {
    let mut e=engine();dialogue(&mut e,"old-small","SMALL_OLDER");dialogue(&mut e,"old-large",&"X".repeat(1900));
    dialogue(&mut e,"newest","NEWEST_SHORT");let s=source(&e);let q=request(&e,PlayInputKind::Action,"I wait.");let full=profile();
    let all=render(&e,&q,&s,&full,DirectorPassV25::Initial);assert_eq!(all.selected_units(),3);
    let all_pairs=pairs(&s,0);let entries=all_pairs.as_array().unwrap();
    let newest=candidate(all.prompt(),json!([entries[2]]));let with_large=candidate(all.prompt(),json!([entries[1],entries[2]]));
    let illegal_backfill=candidate(all.prompt(),json!([entries[0],entries[2]]));
    let mut chosen=None;
    for tokens in 512..=4096{let mut p=full.clone();p.context_tokens=tokens;
        if director_forwarded_budget_v25(&p,DirectorPassV25::Initial,&newest,all.schema()).is_ok()
            && director_forwarded_budget_v25(&p,DirectorPassV25::Initial,&illegal_backfill,all.schema()).is_ok()
            && matches!(director_forwarded_budget_v25(&p,DirectorPassV25::Initial,&with_large,all.schema()),Err(Error::TooLarge)){chosen=Some(p);break;}}
    let p=chosen.expect("actual shared budget must expose a bounded whole-unit cut");
    let a=render(&e,&q,&s,&p,DirectorPassV25::Initial);let b=render(&e,&q,&s,&p,DirectorPassV25::Repair);
    assert_render(&a,&s,&q,&p,DirectorPassV25::Initial);assert_render(&b,&s,&q,&p,DirectorPassV25::Repair);
    assert_eq!(a.selected_start(),2);assert_eq!(a.selected_units(),1);assert_eq!(a.omitted_units(),2);
    assert_eq!(split(a.prompt()).1["conversation"],json!([entries[2]]));assert_eq!(b.selected_start(),a.selected_start());
}

fn assert_selection_cap_is_128_whole_newest_units_even_when_129_fit_shared_budget() {
    let mut e=engine();for n in 0..129{commit(&mut e,&format!("wait-{n}"),Intent::Actions(vec![Command::Wait{ticks:1}]));}
    let s=source(&e);let q=request(&e,PlayInputKind::Action,"I wait.");let p=profile();
    let r=render(&e,&q,&s,&p,DirectorPassV25::Initial);assert_render(&r,&s,&q,&p,DirectorPassV25::Initial);
    let all=candidate(r.prompt(),pairs(&s,0));assert!(director_forwarded_budget_v25(&p,DirectorPassV25::Initial,&all,r.schema()).is_ok());
    assert_eq!(r.source_units(),129);assert_eq!(r.selected_units(),128);assert_eq!(r.selected_start(),1);assert_eq!(r.omitted_units(),1);
}

#[test]
fn newest_nonfitting_and_empty_base_over_budget_refuse_without_truncating_text() {
    assert_selection_cap_is_128_whole_newest_units_even_when_129_fit_shared_budget();
    let mut e=engine();dialogue(&mut e,"large-newest",&"\\\"".repeat(1000));let s=source(&e);let q=request(&e,PlayInputKind::Action,"I wait.");let full=profile();
    let high=render(&e,&q,&s,&full,DirectorPassV25::Initial);let empty=candidate(high.prompt(),json!([]));let mut chosen=None;
    for tokens in 512..=4096{let mut p=full.clone();p.context_tokens=tokens;
        if director_forwarded_budget_v25(&p,DirectorPassV25::Initial,&empty,high.schema()).is_ok()
            && matches!(director_forwarded_budget_v25(&p,DirectorPassV25::Initial,high.prompt(),high.schema()),Err(Error::TooLarge)){chosen=Some(p);break;}}
    let p=chosen.expect("actual shared budget exposes newest-unit refusal");
    expect_error(render_player_literal_director_v1_cancelled(&e,&q,&s,&p,DirectorPassV25::Initial,&||false),Error::TooLarge);
    let base=engine();let bs=source(&base);let bq=request(&base,PlayInputKind::Action,"I wait.");
    assert_eq!(render(&base,&bq,&bs,&p,DirectorPassV25::Initial).prompt(),empty);
    let mut minimum=full;minimum.context_tokens=512;
    expect_error(render_player_literal_director_v1_cancelled(&base,&bq,&bs,&minimum,DirectorPassV25::Initial,&||false),Error::TooLarge);
}

#[test]
fn exact_native_identity_and_input_errors_refuse_divergent_seed_history_append_and_domain2() {
    let mut e=engine();dialogue(&mut e,"same","ORIGINAL");let s=source(&e);let p=profile();let q=request(&e,PlayInputKind::Action,"I wait.");
    let mut other=engine();dialogue(&mut other,"same","OTHER_REAL_HISTORY");let oq=request(&other,PlayInputKind::Action,"I wait.");
    expect_error(render_player_literal_director_v1_cancelled(&other,&oq,&s,&p,DirectorPassV25::Initial,&||false),Error::Stale);
    let mut changed=seed();changed.facts.get_mut("ancestry").unwrap().proposition="OTHER_REAL_SEED".into();let mut changed=Engine::new(changed).unwrap();
    dialogue(&mut changed,"same","ORIGINAL");let cq=request(&changed,PlayInputKind::Action,"I wait.");
    expect_error(render_player_literal_director_v1_cancelled(&changed,&cq,&s,&p,DirectorPassV25::Initial,&||false),Error::Stale);
    let mut bad=q.clone();bad.scope.story="foreign".into();expect_error(render_player_literal_director_v1_cancelled(&e,&bad,&s,&p,DirectorPassV25::Initial,&||false),Error::Scope);
    let child=e.fork("other-scope",e.revision()).unwrap();let child_source=source(&child);
    expect_error(render_player_literal_director_v1_cancelled(&e,&q,&child_source,&p,DirectorPassV25::Initial,&||false),Error::Scope);
    let mut bad=q.clone();bad.expected_revision+=1;expect_error(render_player_literal_director_v1_cancelled(&e,&bad,&s,&p,DirectorPassV25::Initial,&||false),Error::Stale);
    let typed=e.request("typed-current",Intent::Actions(vec![Command::Wait{ticks:1}]));
    expect_error(render_player_literal_director_v1_cancelled(&e,&typed,&s,&p,DirectorPassV25::Initial,&||false),Error::Agency);
    let mut bad_profile=p.clone();bad_profile.context_tokens=0;
    expect_error(render_player_literal_director_v1_cancelled(&e,&q,&s,&bad_profile,DirectorPassV25::Initial,&||false),Error::Rule);
    let input=AuthorCorrectionInputV1{version:1,parent:e.scope().clone(),expected_parent_revision:e.revision(),fork_revision:e.revision(),child_branch:"d2".into(),
        operation:AuthorCorrectionOperationV1::ReplaceFactProposition{fact:"ancestry".into(),expected_proposition:"ELIGIBLE_SEED_NOT_CONVERSATION".into(),replacement:"PRIVATE_B".into()},reason:"PRIVATE_REASON".into()};
    let d2=e.apply_author_correction(&e.prepare_author_correction(&input,&||false).unwrap(),&||false).unwrap().engine;
    let dq=request(&d2,PlayInputKind::Action,"I wait.");expect_error(render_player_literal_director_v1_cancelled(&d2,&dq,&s,&p,DirectorPassV25::Initial,&||false),Error::Version);
    dialogue(&mut e,"appended","APPENDED");let fresh=request(&e,PlayInputKind::Action,"I wait.");
    expect_error(render_player_literal_director_v1_cancelled(&e,&fresh,&s,&p,DirectorPassV25::Initial,&||false),Error::Stale);
}

#[test]
fn rendering_and_cancellation_preserve_request_profile_source_projection_and_history_basis() {
    let mut e=engine();for n in 0..16{dialogue(&mut e,&format!("entry-{n}"),"Literal recorded text");}
    let s=source(&e);let copy=s.clone();let p=profile();let pc=p.clone();let q=request(&e,PlayInputKind::Dialogue,"CURRENT 雪");
    let request_bytes=serde_json::to_vec(&q).unwrap();let projection=e.canonical_bytes();let basis=e.accepted_history_basis().unwrap();
    let rendered=render(&e,&q,&s,&p,DirectorPassV25::Initial);assert_render(&rendered,&s,&q,&p,DirectorPassV25::Initial);
    expect_error(render_player_literal_director_v1_cancelled(&e,&q,&s,&p,DirectorPassV25::Initial,&||true),Error::Cancelled);
    expect_error(render_player_literal_director_v1_cancelled(&e,&q,&s,&p,DirectorPassV25::Initial,&||panic!("fixed cancellation callback")),Error::Cancelled);
    let calls=Cell::new(0);let cancel=||{let n=calls.get()+1;calls.set(n);n>=3};
    expect_error(render_player_literal_director_v1_cancelled(&e,&q,&s,&p,DirectorPassV25::Initial,&cancel),Error::Cancelled);assert!(calls.get()>=3);
    assert_eq!(s,copy);assert_eq!(p,pc);assert_eq!(serde_json::to_vec(&q).unwrap(),request_bytes);
    assert_eq!(e.canonical_bytes(),projection);assert_eq!(e.accepted_history_basis().unwrap(),basis);
}
