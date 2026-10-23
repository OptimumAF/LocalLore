use crate::{evaluation::EvaluationManager, lease::WindowLease, WorkspaceState};
use serde_json::Value;
use std::sync::Arc;
async fn execute(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    manager: tauri::State<'_, Arc<EvaluationManager>>,
    action: impl FnOnce(Arc<EvaluationManager>, Arc<WindowLease>, u64) -> Result<Value, String>
        + Send
        + 'static,
) -> Result<Value, String> {
    let epoch = workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)?;
    let lease = workspace.lease.clone();
    let manager = manager.inner().clone();
    tauri::async_runtime::spawn_blocking(move || action(manager, lease, epoch))
        .await
        .map_err(|_| "EvaluationInternal".to_owned())?
}
#[tauri::command]
pub async fn evaluation_catalog(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    manager: tauri::State<'_, Arc<EvaluationManager>>,
) -> Result<Value, String> {
    execute(window, workspace, manager, |m, l, e| m.catalog(&l, e)).await
}
#[tauri::command]
pub async fn evaluation_start(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    manager: tauri::State<'_, Arc<EvaluationManager>>,
    case_id: Option<String>,
    batch: String,
) -> Result<Value, String> {
    execute(window, workspace, manager, move |m, l, e| {
        m.start(&l, e, case_id, &batch)
    })
    .await
}
#[tauri::command]
pub async fn evaluation_open(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    manager: tauri::State<'_, Arc<EvaluationManager>>,
    run_id: String,
) -> Result<Value, String> {
    execute(window, workspace, manager, move |m, l, e| {
        m.open(&l, e, &run_id)
    })
    .await
}
#[tauri::command]
pub async fn evaluation_status(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    manager: tauri::State<'_, Arc<EvaluationManager>>,
    run_token: String,
) -> Result<Value, String> {
    execute(window, workspace, manager, move |m, l, e| {
        m.status(&l, e, &run_token)
    })
    .await
}
#[tauri::command]
pub async fn evaluation_read(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    manager: tauri::State<'_, Arc<EvaluationManager>>,
    run_token: String,
    case_id: Option<String>,
) -> Result<Value, String> {
    execute(window, workspace, manager, move |m, l, e| {
        m.read(&l, e, &run_token, case_id.as_deref())
    })
    .await
}
#[tauri::command]
pub async fn evaluation_cancel(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    manager: tauri::State<'_, Arc<EvaluationManager>>,
    run_token: String,
    operation_id: u64,
) -> Result<Value, String> {
    if operation_id == 0 || operation_id > 9_007_199_254_740_991 {
        return Err("InvalidEvaluationInput".into());
    }
    execute(window, workspace, manager, move |m, l, e| {
        m.cancel(&l, e, &run_token, operation_id)
    })
    .await
}
#[tauri::command]
pub async fn evaluation_resume(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    manager: tauri::State<'_, Arc<EvaluationManager>>,
    run_token: String,
    batch: String,
) -> Result<Value, String> {
    execute(window, workspace, manager, move |m, l, e| {
        m.resume(&l, e, &run_token, &batch)
    })
    .await
}
#[tauri::command]
pub async fn evaluation_rerun(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    manager: tauri::State<'_, Arc<EvaluationManager>>,
    run_token: String,
    case_id: String,
) -> Result<Value, String> {
    execute(window, workspace, manager, move |m, l, e| {
        m.rerun(&l, e, &run_token, &case_id)
    })
    .await
}
#[cfg(feature = "dev-harness")]
#[tauri::command]
pub async fn harness_evaluation_case(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    manager: tauri::State<'_, Arc<EvaluationManager>>,
    scenario: String,
) -> Result<Value, String> {
    if !crate::harness::active() || std::env::var("LOCALLORE_D07_HARNESS").as_deref() != Ok("1") {
        return Err("Forbidden".into());
    }
    execute(window, workspace, manager, move |m, l, e| {
        l.dispatch(e, || m.test_case(&scenario))
    })
    .await
}
