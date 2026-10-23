// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Explicit bounded selected-player maintenance on the existing archive worker.
//! Integration registers only `memory_maintenance_start`; status/cancel reuse archive IPC.
use crate::{archive::ArchiveBroker, lease::WindowLease, WorkspaceState};
use locallore::{
    contracts::Scope,
    host::{memory_maintenance::MaintenanceAction, memory_maintenance::MaintenanceError, Host},
};
use serde_json::{json, Value};
use std::sync::Arc;

const MAX_INTEGER: u64 = 9_007_199_254_740_991;
const MAX_REPLY: usize = 4096;

struct StartRequest {
    session: String,
    scope: Scope,
    expected_head: u64,
    action: MaintenanceAction,
}
fn identifier(value: &str, max: usize) -> bool {
    !value.is_empty()
        && value.len() <= max
        && value
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b"-_".contains(&b))
}
impl StartRequest {
    fn parse(value: Value) -> Result<Self, String> {
        let object = value.as_object().ok_or("InvalidInput")?;
        if object.len() != 4
            || !["session", "scope", "expected_head", "action"]
                .iter()
                .all(|key| object.contains_key(*key))
        {
            return Err("InvalidInput".into());
        }
        let session = object["session"].as_str().ok_or("InvalidInput")?;
        let expected_head = object["expected_head"].as_u64().ok_or("InvalidInput")?;
        if !identifier(session, 128) || expected_head > MAX_INTEGER {
            return Err("InvalidInput".into());
        }
        let scope = object["scope"].as_object().ok_or("InvalidInput")?;
        if scope.len() != 2 || !scope.contains_key("story") || !scope.contains_key("branch") {
            return Err("InvalidInput".into());
        }
        let story = scope["story"].as_str().ok_or("InvalidInput")?;
        let branch = scope["branch"].as_str().ok_or("InvalidInput")?;
        if !identifier(story, 64) || !identifier(branch, 64) {
            return Err("InvalidInput".into());
        }
        let action = match object["action"].as_str() {
            Some("status") => MaintenanceAction::Status,
            Some("admit") => MaintenanceAction::Admit,
            Some("step") => MaintenanceAction::Step,
            Some("cancel") => MaintenanceAction::Cancel,
            Some("prune") => MaintenanceAction::Prune,
            _ => return Err("InvalidInput".into()),
        };
        Ok(Self {
            session: session.into(),
            scope: Scope {
                story: story.into(),
                branch: branch.into(),
            },
            expected_head,
            action,
        })
    }
}
fn category(error: MaintenanceError) -> String {
    match error {
        MaintenanceError::Closed => "Closed",
        MaintenanceError::Scope => "Scope",
        MaintenanceError::Stale => "Stale",
        MaintenanceError::Busy => "Busy",
        MaintenanceError::Unsupported => "Unsupported",
        MaintenanceError::Cancelled => "Cancelled",
        MaintenanceError::NotFound => "NotFound",
        MaintenanceError::TooLarge => "TooLarge",
        MaintenanceError::Integrity => "Integrity",
        MaintenanceError::Database => "Database",
        MaintenanceError::Full => "Full",
        MaintenanceError::Internal => "Internal",
    }
    .into()
}

// Same function used by native command and actual model-free adapter tests.
// Worker cancellation reads the existing owner AtomicBool without the Host lock.
fn start_owned(
    host: Arc<Host>,
    lease: Arc<WindowLease>,
    broker: Arc<ArchiveBroker>,
    epoch: u64,
    request: StartRequest,
) -> Result<Value, String> {
    broker.start(lease, epoch, move |work| {
        work.phase("memory_maintenance")?;
        #[cfg(feature = "dev-harness")]
        if crate::memory_harness::active() {
            let deadline = std::time::Instant::now() + std::time::Duration::from_secs(10);
            while crate::memory_harness::HOLD.load(std::sync::atomic::Ordering::SeqCst) {
                work.check()?;
                if std::time::Instant::now() >= deadline {return Err("Transport".into());}
                std::thread::sleep(std::time::Duration::from_millis(5));
            }
        }
        let maintenance = host
            .memory_maintenance(
                &request.session,
                &request.scope,
                request.expected_head,
                request.action,
                &|| work.cancelled(),
            )
            .map_err(category)?;
        // Host returned a committed mutation or passive snapshot. A late cancel
        // does not relabel that success as rolled back; window retirement still
        // suppresses publication in the existing broker.
        let result = json!({
            "version":1,"kind":"memory_maintenance","session":request.session,
            "scope":request.scope,"expected_head":request.expected_head,
            "action":request.action,"maintenance":maintenance
        });
        if serde_json::to_vec(&result).map_err(|_| "Internal")?.len() > MAX_REPLY {
            return Err("TooLarge".into());
        }
        Ok(result)
    })
}

#[tauri::command]
pub async fn memory_maintenance_start(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    broker: tauri::State<'_, Arc<ArchiveBroker>>,
    request: Value,
) -> Result<Value, String> {
    let request = StartRequest::parse(request)?;
    let epoch = workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)?;
    let host = workspace.get(epoch).await?;
    let lease = workspace.lease.clone();
    let broker = broker.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        #[cfg(feature="dev-harness")]
        let lose_ack=crate::memory_harness::active() && crate::memory_harness::LOSE_ACK.swap(false,std::sync::atomic::Ordering::SeqCst);
        #[cfg(feature="dev-harness")]
        let status_lease=lease.clone();
        let result=start_owned(host,lease,broker.clone(),epoch,request);
        #[cfg(feature="dev-harness")]
        if lose_ack {
            let id=result.as_ref().ok().and_then(|value|value["operation_id"].as_u64()).ok_or("SyntheticStart")?;
            for _ in 0..1000 {
                let status=broker.status(&status_lease,epoch,id)?;
                if status["running"]==false {
                    if status["error"]!=Value::Null{return Err("SyntheticMemoryFailed".into());}
                    return Err("Transport".into());
                }
                std::thread::sleep(std::time::Duration::from_millis(5));
            }
            return Err("SyntheticTimeout".into());
        }
        result
    })
        .await
        .map_err(|_| "Internal".to_owned())?
}

#[cfg(test)]
#[path = "memory_maintenance_command_tests.rs"]
mod tests;
