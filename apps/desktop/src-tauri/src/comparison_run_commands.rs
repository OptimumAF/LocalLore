// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Frozen source-only parser oracles precede command implementation.
#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    const ID: &str = "00000000-0000-0000-0000-000000000001";

    fn refused(action: &str, query: Value) {
        assert!(matches!(parse(action, &query), Err(error) if error == "InvalidEvaluationInput"));
    }

    #[test]
    fn all_eight_closed_actions_preserve_typed_arguments() {
        assert!(matches!(parse("catalog", &json!({})), Ok(Action::Catalog)));
        for (kind, expected) in [("paired", CoreComparisonKind::PairedSnapshots), ("rollout", CoreComparisonKind::ContinuousRollout)] {
            match parse("start", &json!({"clientId":ID,"comparisonKind":kind,"batch":4})) {
                Ok(Action::Start(input)) => {
                    assert_eq!(input.client_id, ID);
                    assert_eq!(input.kind, expected);
                    assert_eq!(input.max_new_scenes, 4);
                }
                _ => panic!("valid closed start refused"),
            }
        }
        assert!(matches!(parse("lookup", &json!({"clientId":ID})), Ok(Action::Lookup(id)) if id == ID));
        assert!(matches!(parse("open", &json!({"runId":ID})), Ok(Action::Open(id)) if id == ID));
        assert!(matches!(parse("status", &json!({"runToken":ID})), Ok(Action::Status(id)) if id == ID));
        assert!(matches!(parse("resume", &json!({"runToken":ID,"batch":1})), Ok(Action::Resume(id, 1)) if id == ID));
        assert!(matches!(parse("cancel", &json!({"runToken":ID,"operationId":7})), Ok(Action::Cancel(id, 7)) if id == ID));
        assert!(matches!(parse("close", &json!({"runToken":ID})), Ok(Action::Close(id)) if id == ID));
    }

    #[test]
    fn every_action_requires_only_its_exact_keys() {
        for (action, query) in [
            ("catalog", json!({})),
            ("start", json!({"clientId":ID,"comparisonKind":"paired","batch":1})),
            ("lookup", json!({"clientId":ID})),
            ("open", json!({"runId":ID})),
            ("status", json!({"runToken":ID})),
            ("resume", json!({"runToken":ID,"batch":1})),
            ("cancel", json!({"runToken":ID,"operationId":1})),
            ("close", json!({"runToken":ID})),
        ] {
            let mut extra = query.clone();
            extra["granted"] = json!(true);
            refused(action, extra);
            for key in query.as_object().unwrap().keys() {
                let mut missing = query.clone();
                missing.as_object_mut().unwrap().remove(key);
                refused(action, missing);
            }
        }
    }

    #[test]
    fn identity_is_lowercase_uuid_without_paths_or_coercion() {
        for value in [json!(null), json!(false), json!(3), json!(""), json!("../run"), json!("A0000000-0000-0000-0000-000000000001"), json!("00000000000000000000000000000001"), json!(format!("{ID}x")), json!("00000000_0000-0000-0000-000000000001")] {
            for (action, field) in [("lookup", "clientId"), ("open", "runId"), ("status", "runToken"), ("close", "runToken")] {
                let mut query = json!({});
                query[field] = value.clone();
                refused(action, query);
            }
            refused("start", json!({"clientId":value,"comparisonKind":"paired","batch":1}));
        }
    }

    #[test]
    fn scene_batches_are_integers_one_through_four() {
        for batch in 1..=4 {
            assert!(parse("start", &json!({"clientId":ID,"comparisonKind":"rollout","batch":batch})).is_ok());
            assert!(parse("resume", &json!({"runToken":ID,"batch":batch})).is_ok());
        }
        for batch in [json!(0), json!(5), json!(-1), json!(1.5), json!("1"), json!(true), json!(null), json!(u64::MAX)] {
            refused("start", json!({"clientId":ID,"comparisonKind":"paired","batch":batch}));
            refused("resume", json!({"runToken":ID,"batch":batch}));
        }
    }

    #[test]
    fn cancel_operations_are_positive_safe_js_integers() {
        for operation in [1, 9_007_199_254_740_991u64] {
            assert!(matches!(parse("cancel", &json!({"runToken":ID,"operationId":operation})), Ok(Action::Cancel(_, actual)) if actual == operation));
        }
        for operation in [json!(0), json!(-1), json!(1.5), json!(9_007_199_254_740_992u64), json!(u64::MAX), json!("1"), json!(true), json!(null)] {
            refused("cancel", json!({"runToken":ID,"operationId":operation}));
        }
    }

    #[test]
    fn renderer_cannot_select_native_provider_policy_path_or_consent() {
        for kind in [json!("native"), json!("scripted_baseline"), json!("PairedSnapshots"), json!("PAIRED"), json!(false), json!(null)] {
            refused("start", json!({"clientId":ID,"comparisonKind":kind,"batch":1}));
        }
        for field in ["path", "provider", "lane", "policy", "consent", "profile", "model", "epoch", "source", "reference"] {
            let mut query = json!({"clientId":ID,"comparisonKind":"paired","batch":1});
            query[field] = json!("synthetic");
            refused("start", query);
        }
    }

    #[test]
    fn nonobjects_unknown_actions_and_oversized_utf8_are_rejected() {
        for query in [json!(null), json!([]), json!(true), json!("{}"), json!(0)] {
            refused("catalog", query);
        }
        for action in ["", "Catalog", "run", "native", "prepare", "evidence", "shell", "cleanup", "start "] {
            refused(action, json!({}));
        }
        let huge = json!({"runToken":"é".repeat(4096)});
        assert!(serde_json::to_vec(&huge).unwrap().len() > 4096);
        refused("status", huge);
    }

    #[test]
    fn close_requires_exact_token_and_never_accepts_client_or_nullable_authority() {
        refused("close", json!({"runToken":null}));
        refused("close", json!({"clientId":ID}));
        refused("close", json!({"runToken":ID,"clientId":ID}));
        refused("cancel", json!({"runToken":ID,"operationId":1,"confirmed":true}));
    }
}
