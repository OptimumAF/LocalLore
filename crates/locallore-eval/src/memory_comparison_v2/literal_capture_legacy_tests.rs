// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Old4511d67d semantic-result references captured before helper extraction.
//! Not full Host reply/request/receipt hashes: live timings remain unprojected.
//! Root registers/captures/anchors BEFORE production capture-helper extraction.
use super::*;
use crate::local_recording::{ForbiddenByRole, Recording, RecordingProvider};
use locallore::{host::{Host, ProviderFactory}, inference::{Cancellation, GenerationRequest, InferenceProvider, Input}};
use std::{collections::VecDeque, sync::{atomic::Ordering, Arc}, task::Poll};

const BASE: &str = "4511d67dac8376fa90cc56a71a408d88d4fae05b";
const EXPECTED: [(&str, &str); 4] = [
    ("recent-action-repair", "cf83fcef668f11f1c81fa1bcc3c839a5f67e4e077672ac274a2c8e8de84ed157"),
    ("recent-dialogue-repair", "05a66e4cdab9fe760266f74a2597e90c8b1721f84e5cdb4e08d68e4e3926c1f7"),
    ("relevant-action-repair", "fe571feb3982a193ee247994c82d942b0f72aa90f0f5f78ccac28064262c779c"),
    ("relevant-dialogue-repair", "d22505d9ec3b4890218c8dc1f85a0b02f844cc27c969f668b1fdbdf5bdb6dd81"),
];
fn call(h: &Host, command: Value) -> Value {
    h.call(&encode(&json!({"version":1,"command":command})).unwrap())
}
fn op(h: &Host, session: &str, r: &Request, name: &str) -> Value {
    call(h,json!({"op":name,"session":session,"scope":r.scope,"turn":r.turn}))
}
fn profile() -> PlayProfile {
    PlayProfile { id:"synthetic-v2-capture-legacy".into(), model_sha256:"a".repeat(64), runtime_revision:"b".repeat(40),
        template_sha256:"c".repeat(64), worker_sha256:"d".repeat(64), profile_manifest_sha256:"e".repeat(64),
        context_tokens:4096, director_tokens:350, narrator_tokens:350, deadline_ms:5000, repair_limit:1 }
}
fn fixture(h: &Host) -> (String, Scope) {
    let created=call(h,json!({"op":"create","seed":"lantern-quay-v1"}));
    assert_eq!(created["status"],"ok");
    let session=created["data"]["session"].as_str().unwrap().to_owned();
    let scope:Scope=serde_json::from_value(created["data"]["scope"].clone()).unwrap();
    for (n,intent) in [
        Intent::Actions(vec![Command::Wait{ticks:1}]),
        Intent::Dialogue{text:"Recorded harbor promise: café 灯 🧭.".into(),audience:["mira".into()].into()},
    ].into_iter().enumerate() {
        let r=Request{version:1,scope:scope.clone(),turn:format!("prior-{n}"),expected_revision:n as u64,intent};
        assert_eq!(call(h,json!({"op":"submit","session":session,"request":r,"mode":"accepted"}))["data"]["phase"],"queued");
        assert_eq!(op(h,&session,&r,"prepare")["data"]["phase"],"ready");
        assert_eq!(op(h,&session,&r,"commit")["data"]["phase"],"committed");
    }
    (session,scope)
}
struct Script { replies:VecDeque<Vec<u8>> }
impl Script {
    fn new(kind:PlayInputKind,text:&str) -> Self {
        let proposal=if kind==PlayInputKind::Action {json!({"commands":[{"op":"wait","ticks":1}]})}
            else {json!({"commands":[{"op":"say","text":text,"audience":["mira"]}]})};
        let narration=if kind==PlayInputKind::Action {"You pause as a tide tick passes."}
            else {"Your words are heard by the chosen listeners."};
        Self{replies:[b"{".to_vec(),encode(&proposal).unwrap(),
            encode(&json!({"text":narration,"event_ids":[3],"speaker":"narrator"})).unwrap()].into()}
    }
}
impl InferenceProvider for Script {
    fn poll(&mut self,r:&GenerationRequest,_:&Cancellation)->Poll<std::result::Result<Vec<u8>,Error>> {
        let Input::Structured{role,..}=&r.input else {panic!("actual structured role required")};
        assert!(matches!(role.as_str(),"director"|"narrator"));
        assert!(r.budget.deadline_ms>0 && r.budget.deadline_ms<=5000);
        Poll::Ready(self.replies.pop_front().ok_or(Error::Provider))
    }
}

#[test]
fn all_old_v2_captured_context_semantic_bytes_are_frozen_before_common_helper_extraction() {
    let policies=[ContextPolicy::StateRecentTranscriptV1,ContextPolicy::StateRelevantMemoryV1];
    let kinds=[PlayInputKind::Action,PlayInputKind::Dialogue];
    let mut actual=Vec::new();
    for (index,(policy,kind)) in policies.into_iter().flat_map(|p|kinds.map(|k|(p,k))).enumerate() {
        let (name,_)=EXPECTED[index]; let host=Host::new(true); let (session,scope)=fixture(&host);
        let before=host.generation_snapshot(&session,&scope,2,&||false).unwrap().engine;
        let p=profile(); p.validate().unwrap();
        let text=if kind==PlayInputKind::Action {"I wait for one tide tick."}
            else {"Keep the harbor promise: 雪 café \"quoted\" \\ tide.\nSecond line 🧭."};
        let request=before.request("captured-original",Intent::FreeText{kind,text:text.into()});
        let recording=Arc::new(Recording::default()); let observed=recording.clone(); let scripted_text=text.to_owned();
        let factory:ProviderFactory=Arc::new(move||Box::new(RecordingProvider::new(
            Box::new(Script::new(kind,&scripted_text)),observed.clone(),vec![],ForbiddenByRole::default())));
        host.configure_fixture_provider_with_policy(p.clone(),factory,policy).unwrap();
        for command in [
            json!({"op":"trace_configure","session":session,"scope":scope,"expected_head":2,"enabled":true}),
            json!({"op":"trace_capture_configure","session":session,"scope":scope,"expected_head":2,"enabled":true,"consent":true}),
        ] {assert_eq!(call(&host,command)["status"],"ok");}
        assert_eq!(call(&host,json!({"op":"free_text","session":session,"request":request}))["data"]["phase"],"queued");
        assert_eq!(op(&host,&session,&request,"prepare")["data"]["phase"],"ready");
        let trace=call(&host,json!({"op":"trace_read","session":session,"scope":scope,"expected_head":2,
            "base_revision":2,"observer":{"kind":"player"},"turn":request.turn,"attempt":null}));
        assert_eq!(trace["status"],"ok");
        let attempt=u32::try_from(trace["data"]["snapshot"]["attempts"].as_array().unwrap().last().unwrap()["identity"]["attempt"].as_u64().unwrap()).unwrap();
        let reply=call(&host,json!({"op":"trace_capture_read","session":session,"scope":scope,"expected_head":2,
            "base_revision":2,"turn":request.turn,"attempt":attempt}));
        let records=recording.state.lock().unwrap();
        assert_eq!(recording.roles.load(Ordering::SeqCst),3); assert!(!recording.lost.load(Ordering::SeqCst));
        assert_eq!(records.outputs.len(),3);
        assert_eq!(records.captures.iter().map(|c|c.role.as_str()).collect::<Vec<_>>(),vec!["director","director","narrator"]);
        for c in records.captures.iter().filter(|c|c.role=="director") {
            assert_eq!(c.compiler_version,Some(2)); assert_eq!(c.player_text_sha256,Some(digest(text.as_bytes())));
        }
        // Run the ORIGINAL production v2 gate on actual Host private artifacts
        // and the SAME passive recording before projecting any result fields.
        let checked=CapturedContext::from_host_capture(&before,&request,attempt,&reply,&records.captures,&p,Some(1)).unwrap();
        assert_eq!(checked.director_prompts.len(),2); assert_eq!(checked.narrator_prompts.len(),1);
        assert_eq!(checked.director_estimates.as_ref().unwrap().len(),2);
        assert_eq!(checked.package["version"],2); assert_eq!(checked.package["scope"],json!(scope));
        assert_eq!(checked.package["head"],2); assert_eq!(checked.package["observer"],before.seed().player);
        assert!(director_repair_matches_v25(&checked.director_prompts[0],&checked.director_prompts[1]));
        // ENTIRE stable semantic result (all four fields). This is explicitly
        // not the timing-bearing raw reply, GenerationRequest or full Receipt.
        let projection=json!({"projection_version":1,"projection_kind":"old_v2_captured_context_all_semantic_fields",
            "package":checked.package,"director_prompts":checked.director_prompts,
            "narrator_prompts":checked.narrator_prompts,"director_estimates":checked.director_estimates});
        let bytes=encode(&projection).unwrap(); let hash=digest(&bytes);
        eprintln!("OLD_V2_CAPTURE_BYTES base={BASE} case={name} bytes={} sha256={hash}",bytes.len());
        actual.push((name,hash)); drop(records);
        let accepted=op(&host,&session,&request,"commit"); assert_eq!(accepted["data"]["phase"],"committed");
        assert_eq!(accepted["data"]["receipt"]["play"]["prompt_version"],PROMPT_VERSION);
        assert_eq!(accepted["data"]["receipt"]["play"]["context_policy"],json!(policy));
        assert_eq!(accepted["data"]["receipt"]["play"]["repairs"],1);
        host.close_all();
    }
    assert_eq!(actual.len(),4);
    let expected:Vec<_>=EXPECTED.into_iter().map(|(n,h)|(n,h.to_owned())).collect();
    // First old-source run is reference capture, not a demonstrated behavior RED.
    assert_eq!(actual,expected,"capture OLD4511d67d results then anchor before helper extraction; no update hook");
}
