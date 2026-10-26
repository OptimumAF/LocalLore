// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Closed scripted full-comparison IPC. Native code owns paths and authority.
use crate::{
    evaluation::{EvaluationManager, FullComparisonStart},
    WorkspaceState,
};
use locallore_eval::local_lane::comparison::ComparisonKind as CoreComparisonKind;
use serde_json::Value;
use std::sync::Arc;

type Result<T> = std::result::Result<T, String>;
const MAX_QUERY_BYTES: usize = 4096;
const MAX_SAFE_OPERATION: u64 = 9_007_199_254_740_991;

enum Action {
    Catalog,
    Start(FullComparisonStart),
    Lookup(String),
    Open(String),
    Status(String),
    Resume(String, usize),
    Cancel(String, u64),
    Close(String),
}

fn invalid<T>() -> Result<T> {
    Err("InvalidEvaluationInput".into())
}

fn keys(value: &Value, expected: &[&str]) -> Result<()> {
    let object = value.as_object().ok_or("InvalidEvaluationInput")?;
    if object.len() != expected.len()
        || object.keys().any(|key| !expected.contains(&key.as_str()))
    {
        return invalid();
    }
    Ok(())
}

fn guid(value: &Value) -> Result<String> {
    let id = value.as_str().ok_or("InvalidEvaluationInput")?;
    if id.len() != 36
        || !id.bytes().enumerate().all(|(index, byte)| {
            if [8, 13, 18, 23].contains(&index) {
                byte == b'-'
            } else {
                byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte)
            }
        })
    {
        return invalid();
    }
    Ok(id.into())
}

fn batch(value: &Value) -> Result<usize> {
    match value.as_u64() {
        Some(value @ 1..=4) => Ok(value as usize),
        _ => invalid(),
    }
}

fn parse(action: &str, query: &Value) -> Result<Action> {
    // The transport supplies a parsed Value. This bounds its actual compact
    // UTF-8 encoding; it cannot detect duplicate raw keys already overwritten.
    if serde_json::to_vec(query)
        .map_err(|_| "InvalidEvaluationInput")?
        .len()
        > MAX_QUERY_BYTES
    {
        return invalid();
    }
    match action {
        "catalog" => {
            keys(query, &[])?;
            Ok(Action::Catalog)
        }
        "start" => {
            keys(query, &["clientId", "comparisonKind", "batch"])?;
            let kind = match query["comparisonKind"].as_str() {
                Some("paired") => CoreComparisonKind::PairedSnapshots,
                Some("rollout") => CoreComparisonKind::ContinuousRollout,
                _ => return invalid(),
            };
            Ok(Action::Start(FullComparisonStart {
                client_id: guid(&query["clientId"])?,
                kind,
                max_new_scenes: batch(&query["batch"])?,
            }))
        }
        "lookup" => {
            keys(query, &["clientId"])?;
            Ok(Action::Lookup(guid(&query["clientId"])?))
        }
        "open" => {
            keys(query, &["runId"])?;
            Ok(Action::Open(guid(&query["runId"])?))
        }
        "status" | "close" => {
            keys(query, &["runToken"])?;
            let token = guid(&query["runToken"])?;
            Ok(if action == "status" {
                Action::Status(token)
            } else {
                Action::Close(token)
            })
        }
        "resume" => {
            keys(query, &["runToken", "batch"])?;
            Ok(Action::Resume(guid(&query["runToken"])?, batch(&query["batch"])?))
        }
        "cancel" => {
            keys(query, &["runToken", "operationId"])?;
            let operation = query["operationId"]
                .as_u64()
                .filter(|value| (1..=MAX_SAFE_OPERATION).contains(value))
                .ok_or("InvalidEvaluationInput")?;
            Ok(Action::Cancel(guid(&query["runToken"])?, operation))
        }
        _ => invalid(),
    }
}

#[tauri::command]
pub async fn evaluation_comparison_run(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    manager: tauri::State<'_, Arc<EvaluationManager>>,
    action: String,
    query: Value,
) -> Result<Value> {
    let action = parse(&action, &query)?;
    let epoch = workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)?;
    let lease = workspace.lease.clone();
    let manager = manager.inner().clone();
    // Capability cleanup cannot read reports and remains possible after the
    // Host is unavailable or Story Lab permission has been revoked.
    if let Action::Close(token) = action {
        return tauri::async_runtime::spawn_blocking(move || {
            manager.full_comparison_close(&lease, epoch, false, &token)
        })
        .await
        .map_err(|_| "EvaluationInternal".to_owned())?;
    }
    let host = workspace.get(epoch).await?;
    let granted = host.story_lab_granted();
    if !granted {
        return Err("Forbidden".into());
    }
    tauri::async_runtime::spawn_blocking(move || match action {
        Action::Catalog => manager.full_comparison_catalog(&lease, epoch, granted),
        Action::Start(input) => manager.full_comparison_start(&lease, epoch, granted, input),
        Action::Lookup(client) => manager.full_comparison_lookup(&lease, epoch, granted, &client),
        Action::Open(run) => manager.full_comparison_open(&lease, epoch, granted, &run),
        Action::Status(token) => manager.full_comparison_status(&lease, epoch, granted, &token),
        Action::Resume(token, batch) => {
            manager.full_comparison_resume(&lease, epoch, granted, &token, batch)
        }
        Action::Cancel(token, operation) => {
            manager.full_comparison_cancel(&lease, epoch, granted, &token, operation)
        }
        Action::Close(_) => Err("EvaluationInternal".into()),
    })
    .await
    .map_err(|_| "EvaluationInternal".to_owned())?
}

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
