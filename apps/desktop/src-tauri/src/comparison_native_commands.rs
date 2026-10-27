//! Closed native full-comparison transport; native code owns scope and assets.
use crate::{
    evaluation::{EvaluationManager, FullComparisonNativeResume, FullComparisonStart, FullComparisonProtocol},
    models::ModelManager,
    WorkspaceState,
};
use locallore_eval::local_lane::comparison::ComparisonKind;
use serde_json::Value;
use std::sync::Arc;
type Result<T> = std::result::Result<T, String>;
enum Action {
    Catalog,
    Start(FullComparisonStart),
    Lookup(String),
    Open(String),
    Status(String),
    Resume(FullComparisonNativeResume),
    Cancel(String, u64),
    Close(String),
    Managed(String, String),
    CleanupStatus,
    RetryCleanup,
}
fn keys(value: &Value, expected: &[&str]) -> Result<()> {
    let object = value.as_object().ok_or("InvalidEvaluationInput")?;
    if object.len() != expected.len() || object.keys().any(|k| !expected.contains(&k.as_str())) {
        return Err("InvalidEvaluationInput".into());
    }
    Ok(())
}
fn guid(value: &Value) -> Result<String> {
    let id = value.as_str().ok_or("InvalidEvaluationInput")?;
    if id.len() != 36
        || !id.bytes().enumerate().all(|(i, b)| {
            if [8, 13, 18, 23].contains(&i) {
                b == b'-'
            } else {
                b.is_ascii_digit() || (b'a'..=b'f').contains(&b)
            }
        })
    {
        return Err("InvalidEvaluationInput".into());
    }
    Ok(id.into())
}
fn batch(value: &Value) -> Result<usize> {
    match value.as_u64() {
        Some(n @ 1..=4) => Ok(n as usize),
        _ => Err("InvalidEvaluationInput".into()),
    }
}
fn parse(action: &str, query: &Value) -> Result<Action> {
    if serde_json::to_vec(query)
        .map_err(|_| "InvalidEvaluationInput")?
        .len()
        > 4096
    {
        return Err("InvalidEvaluationInput".into());
    }
    match action {
        "catalog" => {
            keys(query, &[])?;
            Ok(Action::Catalog)
        }
        "start" => {
            keys(query, &["clientId", "comparisonKind", "batch"])?;
            let kind = match query["comparisonKind"].as_str() {
                Some("paired") => ComparisonKind::PairedSnapshots,
                Some("rollout") => ComparisonKind::ContinuousRollout,
                _ => return Err("InvalidEvaluationInput".into()),
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
            Ok(Action::Resume(FullComparisonNativeResume {
                run_token: guid(&query["runToken"])?,
                max_new_scenes: batch(&query["batch"])?,
            }))
        }
        "cancel" => {
            keys(query, &["runToken", "operationId"])?;
            let operation = query["operationId"]
                .as_u64()
                .filter(|n| *n > 0 && *n <= 9_007_199_254_740_991)
                .ok_or("InvalidEvaluationInput")?;
            Ok(Action::Cancel(guid(&query["runToken"])?, operation))
        }
        "managed" => {
            keys(query, &["clientId", "runId"])?;
            Ok(Action::Managed(
                guid(&query["clientId"])?,
                guid(&query["runId"])?,
            ))
        }
        "cleanup_status" => {
            keys(query, &[])?;
            Ok(Action::CleanupStatus)
        }
        "retry_cleanup" => {
            keys(query, &[])?;
            Ok(Action::RetryCleanup)
        }
        _ => Err("InvalidEvaluationInput".into()),
    }
}
fn closed(error: String) -> String {
    match error.as_str() {
        "Forbidden"
        | "Closed"
        | "InvalidEvaluationInput"
        | "UnknownEvaluationRun"
        | "StaleEvaluationOperation"
        | "EvaluationBusy"
        | "EvaluationModelBusy"
        | "EvaluationBudget"
        | "EvaluationRunLimit"
        | "EvaluationTokenLimit"
        | "EvaluationSourceMismatch"
        | "EvaluationIntegrity"
        | "EvaluationNotReady"
        | "UnsafeEvaluationPath"
        | "EvaluationIo"
        | "EvaluationInternal"
        | "Cancelled"
        | "PickerUnavailable"
        | "NativeUnavailable"
        | "Cleanup" => error,
        _ => "EvaluationInternal".into(),
    }
}
#[tauri::command]
pub async fn evaluation_comparison_native(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    manager: tauri::State<'_, Arc<EvaluationManager>>,
    models: tauri::State<'_, Arc<ModelManager>>,
    action: String,
    query: Value,
) -> Result<Value> {
    let action = parse(&action, &query)?;
    #[cfg(not(feature = "dev-harness"))]
    let protocol = FullComparisonProtocol::LiteralV3;
    #[cfg(feature = "dev-harness")]
    let protocol: FullComparisonProtocol = crate::comparison_run_native_harness::protocol()?;
    let epoch = workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)?;
    let lease = workspace.lease.clone();
    let manager = manager.inner().clone();
    let models = models.inner().clone();
    // Cleanup/revocation remains available without a Host or spoiler grant.
    if matches!(
        &action,
        Action::Close(_) | Action::CleanupStatus | Action::RetryCleanup
    ) {
        return tauri::async_runtime::spawn_blocking(move || match action {
            Action::Close(token) => {
                manager.full_comparison_close_native_for(&lease, epoch, false, protocol, &token)
            }
            Action::CleanupStatus => manager.selected_cleanup_status(&lease, epoch),
            Action::RetryCleanup => manager.selected_retry_cleanup(&lease, &models, epoch),
            _ => Err("EvaluationInternal".into()),
        })
        .await
        .map_err(|_| "EvaluationInternal".to_owned())?
        .map_err(closed);
    }
    let host = workspace.get(epoch).await.map_err(closed)?;
    let granted = host.story_lab_granted();
    if !granted {
        return Err("Forbidden".into());
    }
    #[cfg(windows)]
    let owner = window.hwnd().map_err(|_| "Closed")?.0 as isize;
    #[cfg(not(windows))]
    let owner = 0;
    #[cfg(feature = "dev-harness")]
    let test = {
        use tauri::Manager;
        if crate::comparison_run_native_harness::active() {
            Some((
                workspace.path.clone(),
                window
                    .try_state::<Arc<crate::comparison_run_native_harness::NativeComparisonHarness>>()
                    .ok_or("Forbidden")?
                    .inner()
                    .clone(),
            ))
        } else {
            None
        }
    };
    #[cfg(feature = "dev-harness")]
    let read_test = test.clone();
    #[cfg(feature = "dev-harness")]
    let lose_ack = test.as_ref().map(|(_, state)| state.clone());
    #[cfg(feature = "dev-harness")]
    let is_start = matches!(&action, Action::Start(_));
    let consent = move |metadata: &Value| {
        #[cfg(feature = "dev-harness")]
        if let Some((path, state)) = &test {
            return crate::comparison_run_native_harness::consent(path, state, metadata);
        }
        crate::exports::confirm_native_comparison_execution(owner, metadata)
    };
    let result = tauri::async_runtime::spawn_blocking(move || match action {
        Action::Catalog => manager.full_comparison_catalog_native_for(&lease, epoch, granted, protocol),
        Action::Start(input) => {
            manager.full_comparison_start_native_for(&lease, &models, epoch, granted, protocol, input, consent)
        }
        Action::Lookup(client) => {
            manager.full_comparison_lookup_native_for(&lease, epoch, granted, protocol, &client)
        }
        Action::Open(run) => manager.full_comparison_open_native_for(&lease, epoch, granted, protocol, &run),
        Action::Status(token) => {
            manager.full_comparison_status_native_for(&lease, epoch, granted, protocol, &token)
        }
        Action::Resume(input) => {
            manager.full_comparison_resume_native_for(&lease, &models, epoch, granted, protocol, input, consent)
        }
        Action::Cancel(token, operation) => {
            manager.full_comparison_cancel_native_for(&lease, epoch, granted, protocol, &token, operation)
        }
        Action::Managed(client, run) => {
            manager.full_comparison_pick_native_for(&lease, epoch, granted, protocol, &client, &run, move || {
                #[cfg(feature = "dev-harness")]
                if let Some((path, state)) = &read_test {
                    return crate::comparison_run_native_harness::read_consent(path, state);
                }
                crate::exports::confirm_comparison_read(owner)
            })
        }
        _ => Err("EvaluationInternal".into()),
    })
    .await
    .map_err(|_| "EvaluationInternal".to_owned())?
    .map_err(closed);
    #[cfg(feature = "dev-harness")]
    if is_start && result.is_ok() && lose_ack.as_ref().is_some_and(|state| state.take_lost_ack()) {
        return Err("EvaluationIo".into());
    }
    result
}
#[cfg(test)]
mod review_tests;
