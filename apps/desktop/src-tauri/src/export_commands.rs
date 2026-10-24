//! Narrow native inspection IPC. All paths come from native picker or trusted dev launcher.
use super::{
    exports::{self, ExportBroker},
    WorkspaceState,
};
use locallore::{contracts::Scope, inspection::ExportMode};
use serde_json::{json, Value};
#[cfg(feature = "dev-harness")]
use std::path::PathBuf;
use std::sync::Arc;
#[cfg(feature = "dev-harness")]
use tauri::Manager;

#[tauri::command]
pub async fn inspection_preview(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    broker: tauri::State<'_, Arc<ExportBroker>>,
    session: String,
    scope: Value,
    expected_revision: u64,
    mode: String,
) -> Result<Value, String> {
    if session.len() > 128 {
        return Err("InvalidInput".into());
    }
    let scope: Scope = serde_json::from_value(scope).map_err(|_| "Scope")?;
    let mode = match mode.as_str() {
        "diagnostics" => ExportMode::Diagnostics,
        "player" => ExportMode::Player,
        "full" => ExportMode::Full,
        _ => return Err("InvalidInput".into()),
    };
    let epoch = workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)?;
    let host = workspace.get(epoch).await?;
    let lease = workspace.lease.clone();
    let broker = broker.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        lease.dispatch(epoch, || {
            let bundle = host.inspection_snapshot(&session, &scope, expected_revision, mode)?;
            broker.insert(epoch, bundle, || lease.valid(epoch))
        })
    })
    .await
    .map_err(|_| "Transport".to_owned())?
}

#[tauri::command]
pub async fn inspection_database_preview(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    broker: tauri::State<'_, Arc<ExportBroker>>,
    session: String,
    scope: Value,
    expected_revision: u64,
) -> Result<Value, String> {
    let parsed: Scope = serde_json::from_value(scope.clone()).map_err(|_| "Scope")?;
    let epoch = workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)?;
    let host = workspace.get(epoch).await?;
    let lease = workspace.lease.clone();
    let broker = broker.inner().clone();
    let source = workspace.path.clone();
    tauri::async_runtime::spawn_blocking(move || {
        lease.dispatch(epoch, || {
            host.inspection_snapshot(&session, &parsed, expected_revision, ExportMode::Full)?;
            let cache = source
                .parent()
                .ok_or("InvalidInput")?
                .join("inspection-preview-cache");
            let (bytes, stories) = exports::capture_database(&source, &cache)?;
            broker.insert_database(epoch, bytes, stories, scope, || lease.valid(epoch))
        })
    })
    .await
    .map_err(|_| "Transport".to_owned())?
}

#[tauri::command]
pub async fn inspection_cancel(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    broker: tauri::State<'_, Arc<ExportBroker>>,
    token: String,
) -> Result<Value, String> {
    let epoch = workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)?;
    let broker = broker.inner().clone();
    tauri::async_runtime::spawn_blocking(move || broker.cancel(epoch, &token))
        .await
        .map_err(|_| "Transport".to_owned())?
}

#[tauri::command]
pub async fn inspection_save(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    broker: tauri::State<'_, Arc<ExportBroker>>,
    token: String,
) -> Result<Value, String> {
    let epoch = workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)?;
    let record = broker.get(epoch, &token)?;
    let lease = workspace.lease.clone();
    #[cfg(windows)]
    let owner = window.hwnd().map_err(|_| "Closed")?.0 as isize;
    #[cfg(not(windows))]
    let owner = 0;
    #[cfg(feature = "dev-harness")]
    let scenario = window.state::<TestExportState>().take();
    tauri::async_runtime::spawn_blocking(move || {
        if !lease.valid(epoch) {
            return Err("Closed".into());
        }
        #[cfg(feature = "dev-harness")]
        let destination = if super::harness::active()
            && std::env::var("LOCALLORE_D03_HARNESS").as_deref() == Ok("1")
        {
            if scenario == "cancel" {
                None
            } else {
                let base = std::env::var_os("LOCALLORE_D03_EXPORT_ROOT")
                    .map(PathBuf::from)
                    .ok_or("InvalidInput")?;
                Some(match scenario.as_str() {
                    "unwritable" => base.join("blocked"),
                    "hostile" => base.join(".."),
                    _ => base,
                })
            }
        } else {
            exports::choose_directory(owner)?
        };
        #[cfg(not(feature = "dev-harness"))]
        let destination = exports::choose_directory(owner)?;
        let Some(destination) = destination else {
            return Ok(json!({"status":"cancelled"}));
        };
        let finalize =
            |handle: &std::fs::File, staging: &std::path::Path, target: &std::path::Path| {
                lease.dispatch(epoch, || {
                    #[cfg(feature = "dev-harness")]
                    if scenario == "collision" {
                        std::fs::create_dir(target).map_err(|_| "Io")?;
                    }
                    exports::atomic_finalize(handle, staging, target)
                })
            };
        #[cfg(feature = "dev-harness")]
        if scenario == "disk-full" {
            return record.save_injected(&destination, finalize, 1);
        }
        record.save(&destination, finalize)
    })
    .await
    .map_err(|_| "Transport".to_owned())?
}

#[tauri::command]
pub async fn inspection_open(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    broker: tauri::State<'_, Arc<ExportBroker>>,
    token: String,
    file: String,
) -> Result<Value, String> {
    let epoch = workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)?;
    let record = broker.get(epoch, &token)?;
    let lease = workspace.lease.clone();
    tauri::async_runtime::spawn_blocking(move || record.open_current(&file, &lease, epoch))
        .await
        .map_err(|_| "Transport".to_owned())?
}

#[tauri::command]
pub async fn inspection_load(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    broker: tauri::State<'_, Arc<ExportBroker>>,
) -> Result<Value, String> {
    let epoch = workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)?;
    let host = workspace.get(epoch).await?;
    let lease = workspace.lease.clone();
    let broker = broker.inner().clone();
    #[cfg(windows)]
    let owner = window.hwnd().map_err(|_| "Closed")?.0 as isize;
    #[cfg(not(windows))]
    let owner = 0;
    tauri::async_runtime::spawn_blocking(move || {
        if !lease.valid(epoch) {
            return Err("Closed".into());
        }
        #[cfg(feature = "dev-harness")]
        let destination = if super::harness::active()
            && std::env::var("LOCALLORE_D03_HARNESS").as_deref() == Ok("1")
        {
            Some(
                std::env::var_os("LOCALLORE_D03_OPEN_ROOT")
                    .map(PathBuf::from)
                    .or_else(|| broker.last_saved(epoch))
                    .ok_or("NotSaved")?,
            )
        } else {
            exports::choose_directory(owner)?
        };
        #[cfg(not(feature = "dev-harness"))]
        let destination = exports::choose_directory(owner)?;
        let Some(destination) = destination else {
            return Ok(json!({"status":"cancelled"}));
        };
        let (bundle, manifest_bytes) = exports::load_exact_directory(&destination)?;
        lease.dispatch(epoch, || {
            if bundle.manifest["mode"] == "full" {
                let capability = host.call(br#"{"version":1,"command":{"op":"capabilities"}}"#);
                if capability["data"]["story_lab"] != true {
                    return Err("Forbidden".into());
                }
            }
            let preview =
                broker.insert_saved(epoch, bundle, manifest_bytes, destination, || {
                    lease.valid(epoch)
                })?;
            Ok(json!({"status":"opened","preview":preview}))
        })
    })
    .await
    .map_err(|_| "Transport".to_owned())?
}

#[tauri::command]
pub async fn inspection_storage(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
) -> Result<Value, String> {
    let epoch = workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)?;
    let host = workspace.get(epoch).await?;
    let lease = workspace.lease.clone();
    let cleanup = workspace.preview_cleanup.clone();
    tauri::async_runtime::spawn_blocking(move || {
        lease.dispatch(epoch, || {
            let reply = host.call(br#"{"version":1,"command":{"op":"workspace"}}"#);
            storage_metadata(&reply, cleanup.lock().map_err(|_| "Closed")?.clone())
        })
    })
    .await
    .map_err(|_| "Transport".to_owned())?
}

fn storage_metadata(reply: &Value, cleanup: Value) -> Result<Value, String> {
    if reply["status"] != "ok" {
        return Err(reply["error"].as_str().unwrap_or("Wire").to_owned());
    }
    // Host workspace schema_version is the compatible protocol contract. This
    // distinct endpoint is displayed as the actual database implementation version.
    if reply["data"]["schema_version"] != 1
        || !matches!(
            reply["data"]["database_schema_version"].as_u64(),
            Some(1..=5)
        )
    {
        return Err("Wire".into());
    }
    Ok(
        json!({"location":reply["data"]["location"],"schema_version":reply["data"]["database_schema_version"],"read_only":true,"private_preview_cleanup":cleanup,"notice":"Storage metadata only. Live database editing is not available."}),
    )
}

#[cfg(test)]
#[path = "m08_storage_metadata_review.rs"]
mod m08_storage_metadata_review;

#[cfg(test)]
mod storage_metadata_tests {
    use super::*;
    #[test]
    fn actual_database_version_is_distinct_from_workspace_contract() {
        let mut reply = json!({"status":"ok","data":{"location":"synthetic","schema_version":1,"database_schema_version":2}});
        let metadata = storage_metadata(&reply, json!(null)).unwrap();
        assert_eq!(metadata["schema_version"], 2);
        assert_eq!(metadata["read_only"], true);
        for version in [1, 3, 4, 5] {
            reply["data"]["database_schema_version"] = json!(version);
            assert_eq!(
                storage_metadata(&reply, json!(null)).unwrap()["schema_version"],
                version
            );
        }
        reply["data"]["database_schema_version"] = json!(6);
        assert_eq!(storage_metadata(&reply, json!(null)), Err("Wire".into()));
        reply["data"]
            .as_object_mut()
            .unwrap()
            .remove("database_schema_version");
        assert_eq!(storage_metadata(&reply, json!(null)), Err("Wire".into()));
    }
}

#[cfg(feature = "dev-harness")]
#[derive(Default)]
pub struct TestExportState(std::sync::Mutex<String>);
#[cfg(feature = "dev-harness")]
impl TestExportState {
    fn take(&self) -> String {
        self.0
            .lock()
            .map(|mut s| std::mem::take(&mut *s))
            .unwrap_or_default()
    }
}
#[cfg(feature = "dev-harness")]
#[tauri::command]
pub fn harness_export_case(
    window: tauri::WebviewWindow,
    state: tauri::State<'_, TestExportState>,
    case: String,
) -> Result<(), String> {
    if !super::harness::active()
        || std::env::var("LOCALLORE_D03_HARNESS").as_deref() != Ok("1")
        || !window.label().starts_with("main-")
    {
        return Err("Forbidden".into());
    }
    if ![
        "cancel",
        "unwritable",
        "collision",
        "hostile",
        "disk-full",
        "success",
    ]
    .contains(&case.as_str())
    {
        return Err("InvalidInput".into());
    }
    *state.0.lock().map_err(|_| "Closed")? = case;
    Ok(())
}
