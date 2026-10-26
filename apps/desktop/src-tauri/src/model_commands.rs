use crate::{models::ModelManager, WorkspaceState};
use serde_json::Value;
use std::sync::Arc;
#[tauri::command]
pub async fn model_status(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    models: tauri::State<'_, Arc<ModelManager>>,
) -> Result<Value, String> {
    workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)?;
    let manager = models.inner().clone();
    tauri::async_runtime::spawn_blocking(move || manager.status())
        .await
        .map_err(|_| "Internal".to_owned())?
}
#[tauri::command]
pub async fn model_cancel(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    models: tauri::State<'_, Arc<ModelManager>>,
    operation_id: u64,
) -> Result<Value, String> {
    if operation_id == 0 || operation_id > 9_007_199_254_740_991 {
        return Err("InvalidInput".into());
    }
    let epoch = workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)?;
    let lease = workspace.lease.clone();
    let manager = models.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        lease.dispatch(epoch, || manager.cancel(operation_id))
    })
    .await
    .map_err(|_| "Internal".to_owned())?
}
#[tauri::command]
pub async fn model_import(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    models: tauri::State<'_, Arc<ModelManager>>,
) -> Result<Value, String> {
    let epoch = workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)?;
    let lease = workspace.lease.clone();
    let manager = models.inner().clone();
    #[cfg(windows)]
    let owner = window.hwnd().map_err(|_| "Closed")?.0 as isize;
    #[cfg(not(windows))]
    let owner = 0;
    #[cfg(feature = "dev-harness")]
    let scenario = window.state::<TestModelState>().take();
    #[cfg(feature = "dev-harness")]
    let native_workspace = workspace.path.clone();
    tauri::async_runtime::spawn_blocking(move || {
        manager.import(&lease, epoch, || {
            #[cfg(feature = "dev-harness")]
            if crate::comparison_run_native_harness::active() {
                return crate::comparison_run_native_harness::approved_model_source(&native_workspace);
            }
            #[cfg(feature = "dev-harness")]
            if crate::harness::active()
                && std::env::var("LOCALLORE_D04_HARNESS").as_deref() == Ok("1")
            {
                if scenario == "cancel" {
                    return Ok(None);
                }
                if ["missing", "corrupt"].contains(&scenario.as_str()) {
                    return std::env::var_os("LOCALLORE_D04_CASE_ROOT")
                        .map(std::path::PathBuf::from)
                        .map(|p| {
                            Some(p.join(if scenario == "missing" {
                                "missing.gguf"
                            } else {
                                "corrupt.gguf"
                            }))
                        })
                        .ok_or_else(|| "ModelInvalid".into());
                }
                return std::env::var_os("LOCALLORE_D04_MODEL_SOURCE")
                    .map(std::path::PathBuf::from)
                    .map(Some)
                    .ok_or_else(|| "ModelInvalid".into());
            }
            crate::models::choose_model(owner)
        })
    })
    .await
    .map_err(|_| "Internal".to_owned())?
}
#[tauri::command]
pub async fn model_load(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    models: tauri::State<'_, Arc<ModelManager>>,
) -> Result<Value, String> {
    let epoch = workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)?;
    let host = workspace.get(epoch).await?;
    let lease = workspace.lease.clone();
    let manager = models.inner().clone();
    tauri::async_runtime::spawn_blocking(move || manager.load(&host, &lease, epoch))
        .await
        .map_err(|_| "Internal".to_owned())?
}
#[tauri::command]
pub async fn model_unload(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    models: tauri::State<'_, Arc<ModelManager>>,
) -> Result<Value, String> {
    let epoch = workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)?;
    let host = workspace.get(epoch).await?;
    let lease = workspace.lease.clone();
    let manager = models.inner().clone();
    tauri::async_runtime::spawn_blocking(move || manager.unload(&host, &lease, epoch))
        .await
        .map_err(|_| "Internal".to_owned())?
}

#[cfg(feature = "dev-harness")]
use tauri::Manager;
#[cfg(feature = "dev-harness")]
#[derive(Default)]
pub struct TestModelState(std::sync::Mutex<String>);
#[cfg(feature = "dev-harness")]
impl TestModelState {
    fn take(&self) -> String {
        self.0
            .lock()
            .map(|mut s| std::mem::take(&mut *s))
            .unwrap_or_default()
    }
}
#[cfg(feature = "dev-harness")]
#[tauri::command]
pub fn harness_model_case(
    window: tauri::WebviewWindow,
    state: tauri::State<'_, TestModelState>,
    case: String,
) -> Result<(), String> {
    if !crate::harness::active()
        || std::env::var("LOCALLORE_D04_HARNESS").as_deref() != Ok("1")
        || !window.label().starts_with("main-")
    {
        return Err("Forbidden".into());
    }
    if !["cancel", "missing", "corrupt", "approved"].contains(&case.as_str()) {
        return Err("InvalidInput".into());
    }
    *state.0.lock().map_err(|_| "Internal")? = case;
    Ok(())
}
