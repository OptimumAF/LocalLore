//! Fixed application-owned IPC. Renderer values never select a native owner or path.
use crate::{archive::ArchiveBroker, author_commands::AuthorManager, WorkspaceState};
use locallore::{contracts::MAX_RECEIPT_BYTES, host::Host};
use serde_json::Value;
use std::sync::Arc;

pub(super) struct AuthorOwner {
    epoch: u64,
    manager: Arc<AuthorManager>,
}
impl WorkspaceState {
    pub(super) async fn author_context_value(&self, epoch: u64) -> Result<Value, String> {
        let host = self.get(epoch).await?;
        self.lease.dispatch(epoch, || {
            Ok(serde_json::json!({
                "version":1,"root_incarnation":self.incarnation,"window_epoch":epoch,
                "story_lab_granted":host.story_lab_granted()
            }))
        })
    }
    pub(super) async fn author_manager(
        &self,
        epoch: u64,
        broker: &Arc<ArchiveBroker>,
    ) -> Result<(Arc<Host>, Arc<AuthorManager>), String> {
        let host = self.get(epoch).await?;
        let manager = self.lease.dispatch(epoch, || {
            let mut slot = self.author.lock().map_err(|_| "Internal")?;
            if let Some(owner) = slot.as_ref() {
                if owner.epoch == epoch {
                    owner
                        .manager
                        .check_binding(&host, &self.lease, broker, epoch)?;
                    return Ok(owner.manager.clone());
                }
                owner.manager.retire(owner.epoch);
            }
            let manager = AuthorManager::new(&host, &self.lease, broker, epoch)?;
            *slot = Some(AuthorOwner {
                epoch,
                manager: manager.clone(),
            });
            Ok(manager)
        })?;
        Ok((host, manager))
    }
    pub(super) fn retire_author(&self, epoch: u64) {
        let retired = {
            let mut slot = self.author.lock().unwrap_or_else(|p| p.into_inner());
            if slot.as_ref().is_some_and(|owner| owner.epoch == epoch) {
                slot.take()
            } else {
                None
            }
        };
        if let Some(owner) = retired {
            owner.manager.retire(epoch);
        }
    }
}
#[tauri::command]
pub async fn author_context(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
) -> Result<Value, String> {
    let epoch = workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)?;
    workspace.author_context_value(epoch).await
}
fn epoch(
    window: &tauri::WebviewWindow,
    workspace: &WorkspaceState,
    request: &str,
) -> Result<u64, String> {
    if request.len() > MAX_RECEIPT_BYTES {
        return Err("TooLarge".into());
    }
    workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)
}
#[tauri::command]
pub async fn author_prepare_start(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    broker: tauri::State<'_, Arc<ArchiveBroker>>,
    request: String,
) -> Result<Value, String> {
    let epoch = epoch(&window, &workspace, &request)?;
    let broker = broker.inner().clone();
    let (host, manager) = workspace.author_manager(epoch, &broker).await?;
    let lease = workspace.lease.clone();
    tauri::async_runtime::spawn_blocking(move || {
        manager.prepare_start(host, lease, broker, epoch, &request)
    })
    .await
    .map_err(|_| "Internal".to_owned())?
}
#[tauri::command]
pub async fn author_commit_start(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    broker: tauri::State<'_, Arc<ArchiveBroker>>,
    request: String,
) -> Result<Value, String> {
    let epoch = epoch(&window, &workspace, &request)?;
    let broker = broker.inner().clone();
    let (host, manager) = workspace.author_manager(epoch, &broker).await?;
    let lease = workspace.lease.clone();
    tauri::async_runtime::spawn_blocking(move || {
        manager.commit_start(host, lease, broker, epoch, &request)
    })
    .await
    .map_err(|_| "Internal".to_owned())?
}
#[tauri::command]
pub async fn author_lookup_start(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    broker: tauri::State<'_, Arc<ArchiveBroker>>,
    request: String,
) -> Result<Value, String> {
    let epoch = epoch(&window, &workspace, &request)?;
    let broker = broker.inner().clone();
    let (host, manager) = workspace.author_manager(epoch, &broker).await?;
    let lease = workspace.lease.clone();
    tauri::async_runtime::spawn_blocking(move || {
        manager.lookup_start(host, lease, broker, epoch, &request)
    })
    .await
    .map_err(|_| "Internal".to_owned())?
}
#[tauri::command]
pub async fn author_preview_discard(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    broker: tauri::State<'_, Arc<ArchiveBroker>>,
    request: String,
) -> Result<bool, String> {
    let epoch = epoch(&window, &workspace, &request)?;
    let broker = broker.inner().clone();
    let (host, manager) = workspace.author_manager(epoch, &broker).await?;
    let lease = workspace.lease.clone();
    tauri::async_runtime::spawn_blocking(move || {
        manager.discard_raw(&host, &lease, &broker, epoch, &request)
    })
    .await
    .map_err(|_| "Internal".to_owned())?
}
