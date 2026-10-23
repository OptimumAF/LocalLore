use crate::{
    evaluation::{CuratedEvidenceRequest, CuratedStart, EvaluationManager},
    lease::WindowLease,
    WorkspaceState,
};
use serde_json::Value;
use std::sync::Arc;
/// Closed application-owned curated adapter. No paths, executables, fixture bytes or providers.
#[tauri::command]
pub async fn evaluation_curated(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    manager: tauri::State<'_, Arc<EvaluationManager>>,
    models: tauri::State<'_, Arc<crate::models::ModelManager>>,
    action: String,
    query: Value,
) -> Result<Value, String> {
    let keys: &[&str] = match action.as_str() {
        "catalog" => &[],
        "start" => &["clientId", "lane", "caseId", "batch", "consent"],
        "lookup" => &["clientId"],
        "open" => &["runId"],
        "status" => &["runToken"],
        "resume" => &["runToken", "batch", "consent"],
        "evidence" => &[
            "runToken", "binding", "caseId", "turnId", "observer", "view",
        ],
        _ => return Err("InvalidEvaluationInput".into()),
    };
    let object = query.as_object().ok_or("InvalidEvaluationInput")?;
    if object.len() != keys.len()
        || object.keys().any(|k| !keys.contains(&k.as_str()))
        || serde_json::to_vec(&query)
            .map_err(|_| "InvalidEvaluationInput")?
            .len()
            > 4096
    {
        return Err("InvalidEvaluationInput".into());
    }
    let models = models.inner().clone();
    #[cfg(feature = "dev-harness")]
    let fault_manager = manager.inner().clone();
    #[cfg(feature = "dev-harness")]
    let is_start = action == "start";
    let result = execute(window, workspace, manager, move |m, l, e| {
        let text = |key: &str| {
            query[key]
                .as_str()
                .map(str::to_owned)
                .ok_or_else(|| "InvalidEvaluationInput".to_owned())
        };
        let consent = || {
            query["consent"]
                .as_bool()
                .ok_or_else(|| "InvalidEvaluationInput".to_owned())
        };
        match action.as_str() {
            "catalog" => {
                let mut value = m.curated_catalog(&l, e)?;
                value["model"] = models.status().map_err(|_| "EvaluationInternal")?;
                Ok(value)
            }
            "start" => {
                let selected = match &query["caseId"] {
                    Value::Null => None,
                    Value::String(s) => Some(s.clone()),
                    _ => return Err("InvalidEvaluationInput".into()),
                };
                m.curated_start(
                    &l,
                    e,
                    models,
                    CuratedStart {
                        client: &text("clientId")?,
                        chosen_lane: &text("lane")?,
                        selection: selected,
                        batch: &text("batch")?,
                        consent: consent()?,
                    },
                )
            }
            "lookup" => m.curated_lookup(&l, e, &text("clientId")?),
            "open" => m.curated_open(&l, e, &text("runId")?),
            "status" => m.curated_status(&l, e, &text("runToken")?),
            "resume" => m.curated_resume(
                &l,
                e,
                models,
                &text("runToken")?,
                &text("batch")?,
                consent()?,
            ),
            "evidence" => {
                let observer = serde_json::from_value(query["observer"].clone())
                    .map_err(|_| "InvalidEvaluationInput")?;
                let view = serde_json::from_value(query["view"].clone())
                    .map_err(|_| "InvalidEvaluationInput")?;
                m.curated_evidence(
                    &l,
                    e,
                    CuratedEvidenceRequest {
                        token: &text("runToken")?,
                        case: &text("caseId")?,
                        turn: &text("turnId")?,
                        binding: &text("binding")?,
                        observer,
                        view,
                    },
                )
            }
            _ => Err("InvalidEvaluationInput".into()),
        }
    })
    .await;
    #[cfg(feature = "dev-harness")]
    if is_start
        && crate::harness::active()
        && std::env::var("LOCALLORE_D07_CURATED_HARNESS").as_deref() == Ok("1")
        && result.is_ok()
        && fault_manager.take_curated_lost_ack()
    {
        return Err("EvaluationIo".into());
    }
    result
}
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
