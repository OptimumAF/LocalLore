// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen before native command production at de959afe. UNCOMPILED / UNRUN.
//! Closed Value/object parser tests only; no native grant, service, runtime,
//! model, dialog or IPC evidence. Value cannot detect overwritten raw keys.
use super::*;
use locallore_eval::local_lane::comparison::ComparisonKind;
use serde_json::{json, Value};

const ID: &str = "00000000-0000-0000-0000-000000000001";
const OTHER: &str = "abcdef01-2345-6789-abcd-0123456789ef";

fn refused(action: &str, query: Value) {
    assert!(matches!(parse(action, &query), Err(error) if error == "InvalidEvaluationInput"));
}
fn queries() -> Vec<(&'static str, Value)> {
    vec![
        ("catalog", json!({})),
        ("start", json!({"clientId":ID,"comparisonKind":"paired","batch":1})),
        ("lookup", json!({"clientId":ID})),
        ("open", json!({"runId":ID})),
        ("status", json!({"runToken":ID})),
        ("resume", json!({"runToken":ID,"batch":1})),
        ("cancel", json!({"runToken":ID,"operationId":1})),
        ("close", json!({"runToken":ID})),
        ("managed", json!({"clientId":ID,"runId":OTHER})),
        ("cleanup_status", json!({})),
        ("retry_cleanup", json!({})),
    ]
}

#[test]
fn eleven_actions_preserve_their_exact_typed_inputs() {
    assert_eq!(queries().len(), 11);
    assert!(matches!(parse("catalog", &json!({})), Ok(Action::Catalog)));
    assert!(matches!(parse("cleanup_status", &json!({})), Ok(Action::CleanupStatus)));
    assert!(matches!(parse("retry_cleanup", &json!({})), Ok(Action::RetryCleanup)));
    for (kind, expected) in [("paired", ComparisonKind::PairedSnapshots), ("rollout", ComparisonKind::ContinuousRollout)] {
        match parse("start", &json!({"clientId":OTHER,"comparisonKind":kind,"batch":4})) {
            Ok(Action::Start(input)) => {
                assert_eq!(input.client_id, OTHER);
                assert_eq!(input.kind, expected);
                assert_eq!(input.max_new_scenes, 4);
            }
            _ => panic!("closed native start refused"),
        }
    }
    assert!(matches!(parse("lookup", &json!({"clientId":ID})), Ok(Action::Lookup(id)) if id == ID));
    assert!(matches!(parse("open", &json!({"runId":OTHER})), Ok(Action::Open(id)) if id == OTHER));
    assert!(matches!(parse("status", &json!({"runToken":ID})), Ok(Action::Status(id)) if id == ID));
    match parse("resume", &json!({"runToken":OTHER,"batch":3})) {
        Ok(Action::Resume(input)) => {
            assert_eq!(input.run_token, OTHER);
            assert_eq!(input.max_new_scenes, 3);
        }
        _ => panic!("closed native resume refused"),
    }
    assert!(matches!(parse("cancel", &json!({"runToken":ID,"operationId":7})), Ok(Action::Cancel(id, 7)) if id == ID));
    assert!(matches!(parse("close", &json!({"runToken":ID})), Ok(Action::Close(id)) if id == ID));
    assert!(matches!(parse("managed", &json!({"clientId":ID,"runId":OTHER})), Ok(Action::Managed(client, run)) if client == ID && run == OTHER));
}

#[test]
fn each_action_rejects_missing_extra_or_misspelled_keys() {
    for (action, query) in queries() {
        assert!(parse(action, &query).is_ok(), "valid {action}");
        let mut extra = query.clone();
        extra["granted"] = json!(true);
        refused(action, extra);
        for key in query.as_object().unwrap().keys() {
            let mut missing = query.clone();
            missing.as_object_mut().unwrap().remove(key);
            refused(action, missing);
            let mut renamed = query.clone();
            let value = renamed.as_object_mut().unwrap().remove(key).unwrap();
            renamed[format!("{key}_")] = value;
            refused(action, renamed);
        }
    }
}

#[test]
fn every_identity_position_requires_a_lowercase_uuid_without_coercion() {
    for bad in [json!(null), json!(true), json!(42), json!([]), json!({}), json!(""), json!("../run"),
        json!("ABCDEF01-2345-6789-abcd-0123456789ef"), json!("abcdef0123456789abcd0123456789ef"),
        json!("abcdef01_2345-6789-abcd-0123456789ef"), json!("gbcdef01-2345-6789-abcd-0123456789ef"), json!(format!("{ID}\n"))] {
        for (action, query) in queries() {
            for key in ["clientId", "runId", "runToken"] {
                if query.get(key).is_some() {
                    let mut changed = query.clone();
                    changed[key] = bad.clone();
                    refused(action, changed);
                }
            }
        }
    }
}

#[test]
fn native_start_and_resume_allow_only_integer_batches_one_through_four() {
    for batch in 1..=4 {
        for kind in ["paired", "rollout"] {
            assert!(parse("start", &json!({"clientId":ID,"comparisonKind":kind,"batch":batch})).is_ok());
        }
        assert!(parse("resume", &json!({"runToken":ID,"batch":batch})).is_ok());
    }
    for batch in [json!(0), json!(5), json!(-1), json!(1.5), json!("1"), json!(true), json!(null), json!([]), json!(u64::MAX)] {
        refused("start", json!({"clientId":ID,"comparisonKind":"paired","batch":batch}));
        refused("resume", json!({"runToken":ID,"batch":batch}));
    }
    for kind in [json!("native"), json!("approved_native"), json!("scripted_baseline"), json!("PAIRED"), json!("PairedSnapshots"), json!(null), json!(false)] {
        refused("start", json!({"clientId":ID,"comparisonKind":kind,"batch":1}));
    }
}

#[test]
fn cancellation_requires_positive_safe_js_integer_operation() {
    for operation in [1, 9_007_199_254_740_991u64] {
        assert!(matches!(parse("cancel", &json!({"runToken":ID,"operationId":operation})), Ok(Action::Cancel(id, actual)) if id == ID && actual == operation));
    }
    for operation in [json!(0), json!(-1), json!(1.5), json!(9_007_199_254_740_992u64), json!(u64::MAX), json!("1"), json!(null), json!(true), json!({})] {
        refused("cancel", json!({"runToken":ID,"operationId":operation}));
    }
}

#[test]
fn renderer_cannot_supply_assets_execution_consent_or_cleanup_authority() {
    for (action, query) in queries() {
        for field in ["provider", "profile", "path", "model", "modelPath", "policy", "lane", "input_lane", "consent", "granted", "cleanupId", "cleanup_id", "confirmed", "epoch", "runtime", "source", "reference"] {
            let mut changed = query.clone();
            changed[field] = json!(true);
            refused(action, changed);
        }
    }
    for action in ["cleanup_status", "retry_cleanup"] {
        for query in [json!({"runToken":ID}), json!({"clientId":ID}), json!({"operationId":1}), json!({"cleanup":true})] {
            refused(action, query);
        }
    }
}

#[test]
fn managed_read_and_close_accept_no_alias_identity_or_extra_read_grant() {
    for query in [json!({"clientId":ID}), json!({"runId":ID}), json!({"clientId":ID,"runToken":OTHER}),
        json!({"clientId":ID,"runId":OTHER,"consent":true}), json!({"clientId":ID,"runId":OTHER,"binding":"a".repeat(64)})] {
        refused("managed", query);
    }
    for query in [json!({"runToken":null}), json!({"clientId":ID}), json!({"runId":ID}), json!({"runToken":ID,"clientId":OTHER})] {
        refused("close", query);
    }
}

#[test]
fn query_is_an_object_not_json_text_and_oversized_utf8_or_unknown_actions_refuse() {
    for (action, query) in queries() {
        for nonobject in [json!(null), json!([]), json!(true), json!(0), json!(serde_json::to_string(&query).unwrap())] {
            refused(action, nonobject);
        }
    }
    for action in ["", "Catalog", "START", "pick", "prepare", "evidence", "diagnostics", "native", "run", "shell", "cleanup", "start "] {
        refused(action, json!({}));
    }
    // All valid fields have tighter bounds than4096; this is a composite
    // oversized UTF-8/identity refusal, not proof of an isolated size branch.
    let oversized = json!({"runToken":"é".repeat(2100)});
    assert!(serde_json::to_vec(&oversized).unwrap().len() > 4096);
    refused("status", oversized);
}
