//! App-owned close/exit continuation. Renderer data cannot acknowledge cleanup.
use crate::{
    close_gate::{CloseTicket, Continuation, Decision, Intent},
    WorkspaceState,
};
use serde_json::{json, Value};
use std::sync::Arc;
use tauri::{Emitter, Manager};

type RetiredModels = Option<(
    u64,
    Option<Arc<std::sync::Mutex<locallore_local_runtime::LocalRuntime>>>,
)>;
pub(crate) fn drain_owned_work(
    evaluations: &crate::evaluation::EvaluationManager,
    archives: &crate::archive::ArchiveBroker,
    models: &crate::models::ModelManager,
    host: Option<&locallore::host::Host>,
    retired: RetiredModels,
    epoch: u64,
) -> bool {
    evaluations.drain(epoch);
    archives.drain(epoch);
    let _ = evaluations.selected_cleanup_retired(epoch);
    models.close(host, retired);
    if let Some(host) = host {
        host.close_all();
    }
    if models.cleanup_complete() {
        // Accepted handoff cleanup may have confirmed its actual witness only
        // during Models.close. Reconcile that same epoch's Job now, without
        // repeating uncertain cleanup or requiring another user close attempt.
        let _ = evaluations.selected_cleanup_retired(epoch);
    }
    evaluations.cleanup_complete() && models.cleanup_complete()
}

fn status(app: &tauri::AppHandle, phase: &str) {
    // Fixed bounded metadata only. Emission failure cannot certify cleanup.
    let _ = app.emit("locallore-close-status", json!({"version":1,"phase":phase}));
}
fn continuation_failed(app: &tauri::AppHandle, ticket: CloseTicket) {
    let restored = app
        .state::<WorkspaceState>()
        .close_gate
        .lock()
        .map(|mut gate| gate.continuation_failed(ticket))
        .unwrap_or(false);
    if restored {
        status(app, "close_failed");
    }
}
fn continue_close(app: &tauri::AppHandle, ticket: CloseTicket) {
    let state = app.state::<WorkspaceState>();
    let continuation = state.close_gate.lock().ok().and_then(|mut gate| {
        finish_lease(&state, &gate, ticket.epoch());
        gate.take_continuation(ticket)
    });
    if let Some(continuation) = continuation {
        let handle = app.clone();
        let scheduled = app.run_on_main_thread(move || match continuation {
            Continuation::DestroyWindow { epoch } => {
                #[cfg(feature = "dev-harness")]
                crate::shutdown_harness::phase("destroy_issued", epoch);
                if let Some(window) = handle.get_webview_window(&format!("main-{epoch}")) {
                    if window.destroy().is_err() {
                        continuation_failed(&handle, ticket);
                    }
                }
            }
            Continuation::Exit { code } => {
                #[cfg(feature = "dev-harness")]
                crate::shutdown_harness::phase("exit_issued", ticket.epoch());
                handle.exit(code.unwrap_or(0));
            }
        });
        if scheduled.is_err() {
            continuation_failed(app, ticket);
        }
    }
}

// Hold the coordinator lock while acknowledging this exact lease. A stale
// continuation must not overwrite the closed marker after a newer epoch opens.
// No native destroy/exit call is made while either coordination lock is held.
fn finish_lease(state: &WorkspaceState, gate: &crate::close_gate::CloseGate, epoch: u64) {
    if gate.can_finish_close(epoch) {
        if let Some(closed) = epoch.checked_add(1) {
            state.lease.finish_close(closed, || {});
            #[cfg(feature = "dev-harness")]
            crate::shutdown_harness::phase("lease_closed", epoch);
        }
    }
}

/// `label` comes from the actual native window, never a JSON epoch or token.
pub(crate) fn request(app: &tauri::AppHandle, label: &str, intent: Intent) -> Result<(), String> {
    request_inner(app, label, intent, false)
}

/// Called only by the actual native Destroyed event, never by renderer JSON.
pub(crate) fn destroyed(app: &tauri::AppHandle, label: &str) -> Result<(), String> {
    request_inner(app, label, Intent::Window, true)
}

fn request_inner(
    app: &tauri::AppHandle,
    label: &str,
    intent: Intent,
    destroyed: bool,
) -> Result<(), String> {
    let epoch: u64 = label
        .strip_prefix("main-")
        .and_then(|s| s.parse().ok())
        .ok_or("Closed")?;
    let state = app.state::<WorkspaceState>();
    let decision = {
        let mut gate = state.close_gate.lock().map_err(|_| "Cleanup")?;
        let decision = if destroyed {
            gate.destroyed(epoch)?
        } else {
            gate.request(epoch, intent)?
        };
        // A window-only destruction can complete after its worker's proof.
        // In that case no further continuation is needed, but reopen still
        // waits for this acknowledgement of BOTH facts.
        if matches!(decision, Decision::Pending) {
            finish_lease(&state, &gate, epoch);
        }
        decision
    };
    let ticket = match decision {
        Decision::Pending => return Ok(()),
        Decision::Continue(ticket) => {
            continue_close(app, ticket);
            return Ok(());
        }
        Decision::Start(ticket) => ticket,
    };
    // This is synchronous before scheduling a drain. A retry targets only this
    // gate's captured epoch after its original lease has already been revoked.
    let epoch = ticket.epoch();
    #[cfg(feature = "dev-harness")]
    crate::shutdown_harness::phase("cleanup_started", epoch);
    let _ = state.lease.invalidate(label);
    state.retire_author(epoch);
    app.state::<Arc<crate::capture_exports::CaptureBroker>>()
        .invalidate(epoch);
    app.state::<Arc<crate::exports::ExportBroker>>()
        .invalidate(epoch);
    let evaluations = app
        .state::<Arc<crate::evaluation::EvaluationManager>>()
        .inner()
        .clone();
    evaluations.retire(epoch);
    let archives = app
        .state::<Arc<crate::archive::ArchiveBroker>>()
        .inner()
        .clone();
    archives.retire(epoch);
    let models = app
        .state::<Arc<crate::models::ModelManager>>()
        .inner()
        .clone();
    let retired = models.retire();
    let host = state.ready();
    let handle = app.clone();
    status(app, "closing");
    tauri::async_runtime::spawn_blocking(move || {
        if !drain_owned_work(
            &evaluations,
            &archives,
            &models,
            host.as_deref(),
            retired,
            epoch,
        ) {
            if let Ok(mut gate) = handle.state::<WorkspaceState>().close_gate.lock() {
                gate.pause(ticket);
            }
            status(&handle, "cleanup_required");
            return;
        }
        let confirmed = handle
            .state::<WorkspaceState>()
            .close_gate
            .lock()
            .map(|mut gate| gate.confirm(ticket))
            .unwrap_or(false);
        if confirmed {
            #[cfg(feature = "dev-harness")]
            crate::shutdown_harness::phase("cleanup_confirmed", epoch);
            status(&handle, "closed");
            continue_close(&handle, ticket);
        }
    });
    Ok(())
}

#[tauri::command]
pub(crate) fn application_close(
    window: tauri::WebviewWindow,
    app: tauri::AppHandle,
) -> Result<Value, String> {
    // No request body, owner IDs or purported cleanup proof is accepted.
    request(&app, window.label(), Intent::Window)?;
    Ok(
        json!({"version":1,"pending":app.state::<WorkspaceState>().close_gate.lock().map_err(|_| "Cleanup")?.pending()}),
    )
}

pub(crate) fn exit_requested(app: &tauri::AppHandle, code: Option<i32>) -> bool {
    let state = app.state::<WorkspaceState>();
    let epoch = match state.close_gate.lock() {
        Ok(mut gate) => {
            if gate.consume_exit(code) {
                #[cfg(feature = "dev-harness")]
                crate::shutdown_harness::phase("exit_permitted", gate.current_epoch());
                return true;
            }
            gate.current_epoch()
        }
        Err(_) => return false,
    };
    let _ = request(app, &format!("main-{epoch}"), Intent::Exit(code));
    false
}
