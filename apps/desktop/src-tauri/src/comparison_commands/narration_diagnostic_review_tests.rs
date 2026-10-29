// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent FIRST parser source: UNREGISTERED/UNCOMPILED/UNRUN.
//! Value has already lost duplicate raw JSON keys; no duplicate-key claim.
use super::*;
use serde_json::json;
const TOKEN: &str="22222222-2222-2222-2222-222222222222";
fn query() -> Value {
    json!({"runToken":TOKEN,"binding":"a".repeat(64),"turnId":"courier-01","arm":"left","observer":{"kind":"omniscient"}})
}
#[test]
fn exact_diagnostic_action_maps_all_three_requested_lenses_without_issuing_privilege() {
    for (lens,expected) in [(json!({"kind":"omniscient"}),Observer::Omniscient),
        (json!({"kind":"player"}),Observer::Player),
        (json!({"kind":"character","id":"mira"}),Observer::Character{id:"mira".into()})] {
        let mut q=query();q["observer"]=lens;
        let Action::NarrationDiagnosticV1(input)=parse("narration_diagnostic_v1",&q).unwrap() else {panic!("wrong closed action")};
        assert_eq!(input.token,TOKEN);assert_eq!(input.binding,"a".repeat(64));
        assert_eq!(input.row.turn,"courier-01");assert!(matches!(input.row.arm,Arm::Left));
        assert_eq!(input.observer,expected);
    }
}
#[test]
fn new_action_refuses_missing_coerced_unknown_execution_and_unsafe_selector_fields() {
    for key in ["runToken","binding","turnId","arm","observer"] {
        let mut q=query();q.as_object_mut().unwrap().remove(key);
        assert!(matches!(parse("narration_diagnostic_v1",&q),Err(ref e) if e=="InvalidEvaluationInput"));
    }
    for key in ["path","source","grant","granted","generation_grant","protocol_version",
        "attempt","admission","session","owner","model","resume","runId","request"] {
        let mut q=query();q[key]=json!(true);
        assert!(parse("narration_diagnostic_v1",&q).is_err(),"unknown {key}");
    }
    for (key,bad) in [("runToken",json!("A".repeat(36))),("runToken",json!(null)),
        ("binding",json!("A".repeat(64))),("binding",json!(1)),("turnId",json!("../private")),
        ("turnId",json!("x".repeat(65))),("arm",json!("LEFT")),("arm",json!(false)),
        ("observer",json!({"kind":"character","id":"../mira"})),
        ("observer",json!({"kind":"omniscient","grant":true})),
        ("observer",json!({"kind":"player","id":"mira"})),("observer",json!("omniscient"))] {
        let mut q=query();q[key]=bad;assert!(parse("narration_diagnostic_v1",&q).is_err(),"{key}");
    }
    let mut q=query();q["future"]=json!("x".repeat(4097));
    assert!(serde_json::to_vec(&q).unwrap().len()>4096);
    assert!(matches!(parse("narration_diagnostic_v1",&q),Err(ref e) if e=="InvalidEvaluationInput"));
}
#[test]
fn existing_actions_and_their_overflow_error_remain_closed_and_unchanged() {
    assert!(matches!(parse("source",&json!({"runToken":TOKEN})),Ok(Action::Source(_))));
    assert!(matches!(parse("summary",&json!({"runToken":TOKEN})),Ok(Action::Summary(_))));
    assert!(matches!(parse("pick",&json!({"clientId":TOKEN})),Ok(Action::Pick(_))));
    assert!(matches!(parse("close",&json!({"clientId":TOKEN,"runToken":null})),Ok(Action::Close(_,None))));
    assert!(matches!(parse("evidence",&json!({"runToken":TOKEN,"binding":"a".repeat(64),"turnId":"courier-01","arm":"left","request":{"kind":"outputs","observer":{"kind":"omniscient"}}})),Ok(Action::Evidence(_))));
    for action in ["run","start","resume","import","load","shell","narration_diagnostic"] {
        assert!(parse(action,&query()).is_err());
    }
    assert!(matches!(parse("pick",&json!({"clientId":TOKEN,"padding":"x".repeat(4097)})),Err(ref e) if e=="InvalidEvaluationInput"));
}
