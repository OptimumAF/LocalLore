// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen command-parser oracles; SOURCE ONLY / UNCOMPILED / UNRUN.
//! These are parser/routing tests, not native IPC, consent or model execution.
use super::*;
use serde_json::json;

const ID: &str = "00000000-0000-0000-0000-000000000001";
const OTHER: &str = "00000000-0000-0000-0000-000000000002";
fn hash() -> String { "a".repeat(64) }
fn body(value: Value) -> String { serde_json::to_string(&value).unwrap() }
fn prepare() -> Value {
    json!({"clientId":ID,"readerClientId":OTHER,"runToken":ID,"binding":hash(),
        "turnId":"courier-01","arm":"left","lane":"scripted_baseline"})
}
fn read() -> Value { json!({"clientId":ID,"runToken":OTHER,"binding":hash()}) }
fn evidence(request: Value) -> Value {
    let mut value=read();value["arm"]=json!("left");value["request"]=request;value
}

#[test]
fn all_frozen_actions_decode_exact_native_input_without_new_authority_fields() {
    let input=match parse("prepare",&body(prepare())).unwrap(){Action::Prepare(input)=>input,_=>panic!("wrong native action")};
    assert_eq!(input.client_id,ID);assert_eq!(input.reader_client_id,OTHER);
    assert_eq!(input.turn_id,"courier-01");assert!(matches!(input.arm,Arm::Left));
    assert!(input.lane==SelectedInputLane::ScriptedBaseline);
    let mut native=prepare();native["lane"]=json!("approved_native");assert!(parse("prepare",&body(native)).is_ok());
    for (action,value) in [
        ("catalog",json!({})),("start",json!({"clientId":ID,"planToken":OTHER})),
        ("status",json!({"clientId":ID})),("cancel",json!({"clientId":ID,"operationId":1})),
        ("open",json!({"clientId":ID,"runId":OTHER})),
        ("resume",json!({"clientId":ID,"runToken":OTHER,"readerClientId":OTHER,"sourceToken":ID,"sourceBinding":hash()})),
        ("summary",read()),("close",json!({"clientId":ID})),
        ("cleanup_status",json!({})),("retry_cleanup",json!({})),
        ("diagnostics",{let mut v=read();v["observer"]=json!({"kind":"omniscient"});v}),
    ] { assert!(parse(action,&body(value)).is_ok(),"{action}"); }
    for kind in ["receipt","capture","outputs"] {
        assert!(parse("evidence",&body(evidence(json!({"kind":kind,"observer":{"kind":"omniscient"}})))).is_ok());
    }
}

#[test]
fn duplicate_members_are_refused_recursively_before_value_collapse() {
    let top=format!(r#"{{"clientId":"{ID}","clientId":"{OTHER}"}}"#);
    assert!(matches!(parse("status",&top),Err(error) if error=="InvalidEvaluationInput"));
    let escaped=format!(r#"{{"clientId":"{ID}","\u0063lientId":"{OTHER}"}}"#);
    assert!(parse("status",&escaped).is_err());
    // Collapsing the duplicate id would otherwise leave a valid Character query.
    let nested=format!(r#"{{"clientId":"{ID}","runToken":"{OTHER}","binding":"{}","arm":"left","request":{{"kind":"query","edge":"before","observer":{{"kind":"character","id":"mira","id":"sable"}},"view":"history"}}}}"#,hash());
    assert!(matches!(parse("evidence",&nested),Err(error) if error=="InvalidEvaluationInput"));
    assert!(parse("catalog",r#"{"nested":[{"x":1,"x":2}]}"#).is_err());
}

#[test]
fn actor_raw_and_diagnostics_are_forbidden_before_private_identity_validation() {
    for observer in [json!({"kind":"player"}),json!({"kind":"character","id":"mira"})] {
        for kind in ["receipt","capture","outputs"] {
            let value=json!({"clientId":null,"runToken":false,"binding":0,"arm":"left",
                "request":{"kind":kind,"observer":observer}});
            assert!(matches!(parse("evidence",&body(value)),Err(error) if error=="Forbidden"));
        }
        let value=json!({"clientId":null,"runToken":false,"binding":0,"observer":observer});
        assert!(matches!(parse("diagnostics",&body(value)),Err(error) if error=="Forbidden"));
    }
    let value=json!({"clientId":null,"runToken":false,"binding":0,"observer":{"kind":"omniscient"}});
    assert!(matches!(parse("diagnostics",&body(value)),Err(error) if error=="InvalidEvaluationInput"));
}

#[test]
fn raw_budget_is_4096_bytes_and_requires_an_exact_json_object() {
    let exact=format!("{}{{}}"," ".repeat(4094));assert_eq!(exact.len(),4096);
    assert!(parse("catalog",&exact).is_ok());
    assert!(parse("catalog",&format!(" {exact}")).is_err());
    for raw in ["null","[]","true","1",r#""catalog""#,r#"{}{}"#,r#"{"clientId":"unterminated}"#] {
        assert!(parse("catalog",raw).is_err());
    }
    for action in ["pick","source","load","shell","execute","set_profile","",&"x".repeat(128)] {
        assert!(parse(action,"{}").is_err());
    }
}

#[test]
fn private_ids_hashes_and_operation_numbers_do_not_coerce_or_cross_bounds() {
    for value in [json!(null),json!(true),json!(7),json!(ID.to_uppercase()+"a"),json!("../owned"),json!("0".repeat(36))] {
        assert!(parse("status",&body(json!({"clientId":value}))).is_err());
    }
    let uppercase="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa".to_uppercase();
    assert!(parse("status",&body(json!({"clientId":uppercase}))).is_err());
    for operation in [json!(0),json!(-1),json!(1.0),json!(9_007_199_254_740_992_u64),json!("1"),json!(true)] {
        assert!(parse("cancel",&body(json!({"clientId":ID,"operationId":operation}))).is_err());
    }
    assert!(parse("cancel",&body(json!({"clientId":ID,"operationId":9_007_199_254_740_991_u64}))).is_ok());
    for binding in [json!("A".repeat(64)),json!("a".repeat(63)),json!("g".repeat(64)),json!(false)] {
        let mut value=read();value["binding"]=binding;assert!(parse("summary",&body(value)).is_err());
    }
}

#[test]
fn enums_and_nested_shapes_are_closed_without_inventing_actor_knowledge() {
    for view in ["profiles","history","relationships","knowledge","promises","provenance","turn_diff","summaries","retrieval_indexes"] {
        for edge in ["before","after"] {
            let value=evidence(json!({"kind":"query","edge":edge,"observer":{"kind":"character","id":"mira"},"view":view}));
            assert!(parse("evidence",&body(value)).is_ok());
        }
    }
    for request in [
        json!({"kind":"query","edge":"head","observer":{"kind":"player"},"view":"history"}),
        json!({"kind":"query","edge":"before","observer":{"kind":"player","id":"mira"},"view":"history"}),
        json!({"kind":"query","edge":"before","observer":{"kind":"character","id":"mira","grant":true},"view":"history"}),
        json!({"kind":"query","edge":"before","observer":{"kind":"character","id":"x".repeat(65)},"view":"history"}),
        json!({"kind":"query","edge":"before","observer":{"kind":"player"},"view":"raw_context"}),
        json!({"kind":"sql","observer":{"kind":"omniscient"}}),
    ] { assert!(parse("evidence",&body(evidence(request))).is_err()); }
    for (key,value) in [("arm",json!("reference")),("lane",json!("native_selected_case")),("turnId",json!("x".repeat(65)))] {
        let mut input=prepare();input[key]=value;assert!(parse("prepare",&body(input)).is_err());
    }
}

#[test]
fn unknown_fields_never_supply_native_consent_paths_profiles_or_cleanup_ack() {
    for (key,value) in [
        ("consent",json!(true)),("path",json!("synthetic")),("profile",json!({})),
        ("assets",json!([])),("prompt",json!("synthetic")),("request",json!({})),
        ("confirmed",json!(true)),("__proto__",json!({})),("constructor",json!({})),
    ] {
        let mut value_with_extra=prepare();value_with_extra[key]=value.clone();
        assert!(parse("prepare",&body(value_with_extra)).is_err());
        assert!(parse("retry_cleanup",&body(json!({key:value}))).is_err());
    }
    assert!(parse("close",&body(json!({"clientId":ID,"runToken":null}))).is_err());
    assert!(parse("cleanup_status",&body(json!({"operationId":1}))).is_err());
}

#[test]
fn only_close_and_generic_cleanup_bypass_story_lab_initialization() {
    for action in ["cleanup_status","retry_cleanup"] { assert!(!parse(action,"{}").unwrap().requires_lab()); }
    assert!(!parse("close",&body(json!({"clientId":ID}))).unwrap().requires_lab());
    for (action,value) in [("catalog",json!({})),("status",json!({"clientId":ID})),("summary",read()),("prepare",prepare())] {
        assert!(parse(action,&body(value)).unwrap().requires_lab());
    }
}
