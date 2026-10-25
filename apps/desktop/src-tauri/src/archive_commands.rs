//! Fixed native archive IPC. Picker paths never enter renderer authority.
use crate::{
    archive::{self, ArchiveBroker},
    WorkspaceState,
};
use locallore::{
    contracts::Scope,
    host::Host,
    inspection_query::{Observer, Query, View},
};
use serde_json::Value;
use std::sync::Arc;
#[cfg(test)]
#[path = "archive_authorization_tests.rs"]
mod archive_authorization_tests;

// Reuse Host's native grant and exact durable session/scope/head checks without
// constructing the legacy readable-inspection bundle to authorize a transfer.
fn authorize_export(
    host: &Host,
    session: &str,
    scope: &Scope,
    expected_revision: u64,
) -> Result<(), String> {
    host.inspection_query(
        session,
        &Query {
            version: 2,
            scope: scope.clone(),
            expected_head: expected_revision,
            at_revision: None,
            observer: Observer::Omniscient,
            view: View::Profiles,
            cursor: None,
            limit: 1,
            search: String::new(),
        },
    )
    .map(|_| ())
}
fn epoch(window: &tauri::WebviewWindow, workspace: &WorkspaceState) -> Result<u64, String> {
    workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)
}
fn owner(window: &tauri::WebviewWindow) -> Result<isize, String> {
    #[cfg(windows)]
    {
        Ok(window.hwnd().map_err(|_| "Closed")?.0 as isize)
    }
    #[cfg(not(windows))]
    {
        let _ = window;
        Ok(0)
    }
}
#[tauri::command]
pub fn archive_catalog(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    broker: tauri::State<'_, Arc<ArchiveBroker>>,
) -> Result<Value, String> {
    let e = epoch(&window, &workspace)?;
    workspace.lease.dispatch(e, || Ok(broker.catalog()))
}
#[tauri::command]
pub async fn archive_export_preview(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    broker: tauri::State<'_, Arc<ArchiveBroker>>,
    session: String,
    scope: Value,
    expected_revision: u64,
) -> Result<Value, String> {
    if session.len() > 128 || expected_revision > 9_007_199_254_740_991 {
        return Err("InvalidArchiveInput".into());
    }
    let scope: Scope = serde_json::from_value(scope).map_err(|_| "InvalidArchiveInput")?;
    if scope.story.len() > 64 || scope.branch.len() > 64 {
        return Err("InvalidArchiveInput".into());
    }
    let e = epoch(&window, &workspace)?;
    let host = workspace.get(e).await?;
    let lease = workspace.lease.clone();
    let broker = broker.inner().clone();
    let path = workspace.path.clone();
    tauri::async_runtime::spawn_blocking(move || {
        broker.start(lease, e, move |work| {
            // Existing trusted Host private authorization and exact live session scope.
            // The archive subsequently checks its own coherent captured branch head.
            authorize_export(&host, &session, &scope, expected_revision)?;
            archive::capture(work, &path, &scope.story, &scope.branch, expected_revision)
        })
    })
    .await
    .map_err(|_| "ArchiveInternal".to_owned())?
}
#[tauri::command]
pub async fn archive_import_preview(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    broker: tauri::State<'_, Arc<ArchiveBroker>>,
) -> Result<Value, String> {
    let e = epoch(&window, &workspace)?;
    let lease = workspace.lease.clone();
    let broker = broker.inner().clone();
    let owner = owner(&window)?;
    #[cfg(feature = "dev-harness")]
    let test = test_selection(&window)?;
    tauri::async_runtime::spawn_blocking(move || {
        broker.start(lease, e, move |w| {
            w.phase("choosing_input")?;
            #[cfg(feature = "dev-harness")]
            let path = if let Some(test) = test {
                test.input()?
            } else {
                archive::choose_input(owner)?
            };
            #[cfg(not(feature = "dev-harness"))]
            let path = archive::choose_input(owner)?;
            archive::preview_input(w, path)
        })
    })
    .await
    .map_err(|_| "ArchiveInternal".to_owned())?
}
#[tauri::command]
pub async fn archive_export(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    broker: tauri::State<'_, Arc<ArchiveBroker>>,
    token: String,
    consent: bool,
) -> Result<Value, String> {
    if !consent {
        return Err("ArchiveConsentRequired".into());
    }
    if !archive::valid_id(&token) {
        return Err("InvalidArchiveInput".into());
    }
    let e = epoch(&window, &workspace)?;
    let lease = workspace.lease.clone();
    let broker = broker.inner().clone();
    let owner = owner(&window)?;
    #[cfg(feature = "dev-harness")]
    let test = test_selection(&window)?;
    tauri::async_runtime::spawn_blocking(move || {
        broker.start(lease, e, move |w| {
            w.phase("choosing_destination")?;
            #[cfg(feature = "dev-harness")]
            let (path, fail) = if let Some(test) = test {
                (test.output()?, test.fail_after())
            } else {
                (crate::exports::choose_directory(owner)?, None)
            };
            #[cfg(not(feature = "dev-harness"))]
            let (path, fail) = (crate::exports::choose_directory(owner)?, None);
            archive::publish(w, &token, path, fail)
        })
    })
    .await
    .map_err(|_| "ArchiveInternal".to_owned())?
}
#[tauri::command]
pub async fn archive_import(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    broker: tauri::State<'_, Arc<ArchiveBroker>>,
    token: String,
    consent: bool,
) -> Result<Value, String> {
    if !consent {
        return Err("ArchiveConsentRequired".into());
    }
    if !archive::valid_id(&token) {
        return Err("InvalidArchiveInput".into());
    }
    let e = epoch(&window, &workspace)?;
    let lease = workspace.lease.clone();
    let broker = broker.inner().clone();
    let path = workspace.path.clone();
    tauri::async_runtime::spawn_blocking(move || {
        broker.start(lease, e, move |w| archive::import(w, &token, &path))
    })
    .await
    .map_err(|_| "ArchiveInternal".to_owned())?
}
#[tauri::command]
pub fn archive_status(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    broker: tauri::State<'_, Arc<ArchiveBroker>>,
    operation_id: u64,
) -> Result<Value, String> {
    let e = epoch(&window, &workspace)?;
    broker.status(&workspace.lease, e, operation_id)
}
#[tauri::command]
pub fn archive_cancel(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    broker: tauri::State<'_, Arc<ArchiveBroker>>,
    operation_id: u64,
) -> Result<Value, String> {
    let e = epoch(&window, &workspace)?;
    broker.cancel(&workspace.lease, e, operation_id)
}
#[tauri::command]
pub fn archive_discard(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    broker: tauri::State<'_, Arc<ArchiveBroker>>,
    token: String,
) -> Result<Value, String> {
    let e = epoch(&window, &workspace)?;
    broker.discard(&workspace.lease, e, &token)
}

#[cfg(feature = "dev-harness")]
#[derive(Default)]
pub struct TestArchiveState(std::sync::Mutex<String>);
#[cfg(feature = "dev-harness")]
struct TestSelection {
    root: std::path::PathBuf,
    case: String,
}
#[cfg(feature = "dev-harness")]
impl TestSelection {
    fn input(&self) -> Result<Option<std::path::PathBuf>, String> {
        Ok(if self.case == "cancel" {
            None
        } else {
            Some(self.root.join(match self.case.as_str() {
                "corrupt" => "corrupt.json",
                "future" => "future.json",
                "oversize" => "oversize.json",
                "hostile" => "hostile.json",
                _ => "transfer.json",
            }))
        })
    }
    fn output(&self) -> Result<Option<std::path::PathBuf>, String> {
        Ok(if self.case == "cancel" {
            None
        } else {
            Some(self.root.join(if self.case == "unwritable" {
                "blocked"
            } else {
                "exports"
            }))
        })
    }
    fn fail_after(&self) -> Option<usize> {
        (self.case == "disk-full").then_some(0)
    }
}
#[cfg(feature = "dev-harness")]
fn test_selection(window: &tauri::WebviewWindow) -> Result<Option<TestSelection>, String> {
    use tauri::Manager;
    if !crate::harness::active() || std::env::var("LOCALLORE_D08_HARNESS").as_deref() != Ok("1") {
        return Ok(None);
    }
    let state = window.state::<TestArchiveState>();
    let case = std::mem::take(&mut *state.0.lock().map_err(|_| "ArchiveInternal")?);
    let root = std::env::var_os("LOCALLORE_D08_PICKER_ROOT")
        .map(std::path::PathBuf::from)
        .ok_or("InvalidArchiveInput")?;
    Ok(Some(TestSelection { root, case }))
}
#[cfg(feature = "dev-harness")]
#[tauri::command]
pub fn harness_archive_case(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    broker: tauri::State<'_, Arc<ArchiveBroker>>,
    state: tauri::State<'_, TestArchiveState>,
    scenario: String,
) -> Result<(), String> {
    if !crate::harness::active() || std::env::var("LOCALLORE_D08_HARNESS").as_deref() != Ok("1") {
        return Err("Forbidden".into());
    }
    if ![
        "normal",
        "cancel",
        "corrupt",
        "future",
        "oversize",
        "hostile",
        "unwritable",
        "disk-full",
        "hold-import",
        "release-import",
        "collision",
        "drop-import-ack",
    ]
    .contains(&scenario.as_str())
    {
        return Err("InvalidArchiveInput".into());
    }
    let e = epoch(&window, &workspace)?;
    workspace.lease.dispatch(e, || {
        if scenario == "drop-import-ack" {
            broker
                .drop_import_ack
                .store(true, std::sync::atomic::Ordering::SeqCst);
        } else if scenario == "collision" {
            broker
                .collision
                .store(true, std::sync::atomic::Ordering::SeqCst);
        } else if scenario == "hold-import" || scenario == "release-import" {
            broker.hold.store(
                scenario == "hold-import",
                std::sync::atomic::Ordering::SeqCst,
            )
        } else {
            *state.0.lock().map_err(|_| "ArchiveInternal")? = scenario;
        }
        Ok(())
    })
}
