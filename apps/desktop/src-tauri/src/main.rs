#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
use locallore::host::Host;
use serde_json::{json, Value};
use std::sync::Arc;
use tauri::Manager;
mod archive;
mod archive_commands;
#[cfg(feature = "dev-harness")]
mod archive_v3_harness;
mod author_commands;
#[cfg(feature = "dev-harness")]
mod author_harness;
mod author_ipc;
#[cfg(all(test, windows))]
mod author_ipc_review;
mod capture_exports;
mod close_gate;
mod comparison_commands;
#[cfg(feature = "dev-harness")]
mod comparison_reader_harness;
mod evaluation;
mod evaluation_commands;
mod export_commands;
mod exports;
mod fork_commands;
mod lease;
mod memory_maintenance_commands;
mod model_commands;
mod models;
mod selected_commands;
#[cfg(feature = "dev-harness")]
mod selected_harness;
mod shutdown;
use lease::WindowLease;
#[cfg(feature = "dev-harness")]
mod fork_harness;
#[cfg(feature = "dev-harness")]
mod harness;
#[cfg(feature = "dev-harness")]
mod memory_harness;
#[cfg(feature = "dev-harness")]
mod test_bridge;
#[cfg(feature = "dev-harness")]
mod timeline_harness;
#[cfg(feature = "dev-harness")]
use std::sync::atomic::{AtomicBool, Ordering};
#[cfg(feature = "dev-harness")]
struct Reopen(AtomicBool);

struct WorkspaceState {
    close_gate: std::sync::Mutex<close_gate::CloseGate>,
    incarnation: String,
    path: std::path::PathBuf,
    lease: Arc<WindowLease>,
    host: tokio::sync::OnceCell<Arc<Host>>,
    preview_cleanup: Arc<std::sync::Mutex<Value>>,
    author: std::sync::Mutex<Option<author_ipc::AuthorOwner>>,
}
impl WorkspaceState {
    async fn get(&self, epoch: u64) -> Result<Arc<Host>, String> {
        self.host
            .get_or_try_init(|| async {
                let path = self.path.clone();
                let lease = self.lease.clone();
                let cleanup = self.preview_cleanup.clone();
                tauri::async_runtime::spawn_blocking(move || {
                    lease.dispatch(epoch, || {
                        #[cfg(feature = "dev-harness")]
                        if harness::active()
                            && std::env::var("LOCALLORE_TEST_MEMORY").as_deref() == Ok("1")
                        {
                            return Ok(Arc::new(Host::new(true)));
                        }
                        let parent = path.parent().ok_or_else(|| "InvalidInput".to_owned())?;
                        std::fs::create_dir_all(parent).map_err(|_| "Io".to_owned())?;
                        let report = exports::reap_private_previews(
                            &parent.join("inspection-preview-cache"),
                        )
                        .unwrap_or_else(|error| json!({"unavailable":error}));
                        if let Ok(mut value) = cleanup.lock() {
                            *value = report;
                        }
                        locallore_workspace::open(&path, true).map(Arc::new)
                    })
                })
                .await
                .map_err(|_| "StorageUnavailable".to_owned())?
            })
            .await
            .cloned()
    }
    fn ready(&self) -> Option<Arc<Host>> {
        self.host.get().cloned()
    }
}
#[tauri::command]
async fn host_call(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    permits: tauri::State<'_, Arc<tokio::sync::Semaphore>>,
    input: String,
) -> Result<Value, String> {
    let epoch = workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)?;
    if input.len() > locallore::host::MAX_INPUT {
        return Err("TooLarge".into());
    }
    let preparing = matches!(
        serde_json::from_str::<locallore::host::Envelope>(&input),
        Ok(locallore::host::Envelope {
            command: locallore::host::HostCommand::Prepare { .. },
            ..
        })
    );
    // Disk/replay/commit and generation all stay outside the UI event thread.
    // Only generation consumes the bounded permit; cancel/status can still run.
    let permit = if preparing {
        Some(
            permits
                .inner()
                .clone()
                .try_acquire_owned()
                .map_err(|_| "Busy".to_owned())?,
        )
    } else {
        None
    };
    let host = workspace.get(epoch).await?;
    let lease = workspace.lease.clone();
    tauri::async_runtime::spawn_blocking(move || {
        let _permit = permit;
        if preparing {
            if !lease.valid(epoch) {
                return Err("Closed".into());
            }
            Ok(host.call(input.as_bytes()))
        } else {
            lease.dispatch(epoch, || Ok(host.call(input.as_bytes())))
        }
    })
    .await
    .map_err(|_| "Transport".to_owned())?
}
fn build_window(app: &tauri::AppHandle, reopened: bool) -> Result<(), Box<dyn std::error::Error>> {
    let epoch = app
        .state::<WorkspaceState>()
        .lease
        .begin()
        .map_err(std::io::Error::other)?;
    let label = format!("main-{epoch}");
    app.state::<WorkspaceState>()
        .close_gate
        .lock()
        .map_err(|_| std::io::Error::other("Cleanup"))?
        .opened(epoch)
        .map_err(std::io::Error::other)?;
    let testing = cfg!(feature = "dev-harness")
        && std::env::var("LOCALLORE_D02_HARNESS").as_deref() == Ok("1");
    let script = if testing {
        format!(
            "window.__LOCALLORE_TEST__={{enabled:true,backend:'native',durable:{},failure:{},exporting:{},localplay:{},inspecting:{},debugging:{},capturing:{},legacy:{},evaluating:{},curated:{},comparisonReading:{},selectedEvaluating:{},archiving:{},timelining:{},forking:{},maintaining:{},authoring:{},archiveStage:'{}',stage:'{}'}};",
            std::env::var("LOCALLORE_TEST_MEMORY").as_deref() != Ok("1"),
            std::env::var("LOCALLORE_TEST_STORAGE_FAILURE").as_deref() == Ok("1"),
            std::env::var("LOCALLORE_D03_HARNESS").as_deref() == Ok("1"),
              std::env::var("LOCALLORE_D04_HARNESS").as_deref() == Ok("1"),
            std::env::var("LOCALLORE_D05_HARNESS").as_deref() == Ok("1"),
            std::env::var("LOCALLORE_D06_HARNESS").as_deref() == Ok("1"),
            std::env::var("LOCALLORE_D06_CAPTURE_HARNESS").as_deref() == Ok("1"),
            std::env::var("LOCALLORE_M07_LEGACY_HARNESS").as_deref() == Ok("1"),
            std::env::var("LOCALLORE_D07_HARNESS").as_deref() == Ok("1"),
            std::env::var("LOCALLORE_D07_CURATED_HARNESS").as_deref() == Ok("1"),
            std::env::var("LOCALLORE_D07_COMPARISON_READER_HARNESS").as_deref() == Ok("1"),
            std::env::var("LOCALLORE_D07_SELECTED_HARNESS").as_deref() == Ok("1"),
            std::env::var("LOCALLORE_D08_HARNESS").as_deref() == Ok("1"),
            std::env::var("LOCALLORE_D08_TIMELINE_HARNESS").as_deref() == Ok("1"),
            std::env::var("LOCALLORE_D08_FORK_HARNESS").as_deref() == Ok("1"),
            std::env::var("LOCALLORE_M07_MEMORY_HARNESS").as_deref() == Ok("1"),
            std::env::var("LOCALLORE_M08_AUTHOR_HARNESS").as_deref() == Ok("1"),
            match std::env::var("LOCALLORE_D08_STAGE").as_deref(){
                Ok("import")=>"import",Ok("uncertain")=>"uncertain",Ok("retire")=>"retire",Ok("restarted")=>"restarted",
                Ok("v3-source")=>"v3-source",Ok("v3-import")=>"v3-import",Ok("v3-restarted")=>"v3-restarted",Ok("v3-uncertain")=>"v3-uncertain",Ok("v3-continued")=>"v3-continued",Ok("v3-continued-restarted")=>"v3-continued-restarted",_=>"source"
            },
            if reopened {
                "reopened"
            } else if std::env::var("LOCALLORE_TEST_RESTART").as_deref() == Ok("1") {
                "restart"
            } else {
                "initial"
            }
        )
    } else {
        "window.__LOCALLORE_TEST__=undefined;".into()
    };
    let builder =
        tauri::WebviewWindowBuilder::new(app, label, tauri::WebviewUrl::App("index.html".into()));
    #[cfg(feature = "dev-harness")]
    let builder = if testing {
        let path = std::path::PathBuf::from(
            std::env::var_os("LOCALLORE_TEST_WORKSPACE").unwrap_or_default(),
        );
        builder.data_directory(
            path.parent()
                .unwrap_or_else(|| std::path::Path::new("."))
                .join("webview-profile"),
        )
    } else {
        builder
    };
    builder
        .title("LocalLore · Play & Story Lab")
        .inner_size(1280.0, 900.0)
        .min_inner_size(560.0, 500.0)
        // Harness builds never show, activate or capture the user's desktop.
        .visible(!testing)
        .focused(false)
        .on_navigation(|url| {
            (url.scheme() == "http" && url.host_str() == Some("tauri.localhost"))
                || (url.scheme() == "tauri" && url.host_str() == Some("localhost"))
        })
        .on_new_window(|_, _| tauri::webview::NewWindowResponse::Deny)
        .initialization_script(script)
        .build()?;
    Ok(())
}
#[cfg(feature = "dev-harness")]
#[tauri::command]
async fn harness_stats(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
) -> Result<Value, &'static str> {
    if !harness::active() || !window.label().starts_with("main-") {
        return Err("Forbidden");
    }
    let epoch = workspace.lease.capture(window.label())?;
    let (sessions, workers) = workspace
        .get(epoch)
        .await
        .map_err(|_| "StorageUnavailable")?
        .live_counts();
    Ok(serde_json::json!({"sessions":sessions,"workers":workers}))
}
#[cfg(feature = "dev-harness")]
#[tauri::command]
fn harness_oracle(window: tauri::WebviewWindow, receipts: Value) -> Result<Value, &'static str> {
    if !harness::active() || !window.label().starts_with("main-") {
        return Err("Forbidden");
    }
    Ok(test_bridge::oracle(&receipts))
}
#[cfg(feature = "dev-harness")]
#[tauri::command]
fn harness_reopen(
    window: tauri::WebviewWindow,
    app: tauri::AppHandle,
    state: tauri::State<'_, Reopen>,
) -> Result<(), &'static str> {
    if !harness::active()
        || !window.label().starts_with("main-")
        || state.0.swap(true, Ordering::SeqCst)
    {
        return Err("Forbidden");
    }
    let old_label = window.label().to_owned();
    window.destroy().map_err(|_| "CloseFailed")?;
    tauri::async_runtime::spawn(async move {
        for _ in 0..40 {
            tokio::time::sleep(std::time::Duration::from_millis(25)).await;
            if app.get_webview_window(&old_label).is_none()
                && app.state::<WorkspaceState>().lease.can_open()
                && app
                    .state::<WorkspaceState>()
                    .ready()
                    .is_none_or(|h| h.live_counts() == (0, 0))
            {
                let handle = app.clone();
                let _ = app.run_on_main_thread(move || {
                    if build_window(&handle, true).is_err() {
                        handle.exit(1);
                    }
                });
                return;
            }
        }
        app.exit(1);
    });
    Ok(())
}
fn main() {
    #[cfg(feature = "dev-harness")]
    if std::env::args().any(|a| a == "--host-stdio") {
        test_bridge::run();
        return;
    }
    let builder = tauri::Builder::default()
        .manage(Arc::new(capture_exports::CaptureBroker::default()))
        .manage(Arc::new(archive::ArchiveBroker::default()))
        .manage(Arc::new(tokio::sync::Semaphore::new(4)))
        .manage(Arc::new(exports::ExportBroker::default()));
    #[cfg(feature = "dev-harness")]
    let builder = builder
        .manage(capture_exports::TestCaptureState::default())
        .manage(Reopen(AtomicBool::new(false)))
        .manage(export_commands::TestExportState::default())
        .manage(archive_commands::TestArchiveState::default())
        .manage(Arc::new(fork_harness::ForkHarnessState::default()))
        .manage(model_commands::TestModelState::default())
        .invoke_handler(tauri::generate_handler![
            capture_exports::harness_capture_case,
            capture_exports::capture_preview,
            capture_exports::capture_save,
            capture_exports::capture_revoke,
            host_call,
            shutdown::application_close,
            archive_commands::archive_catalog,
            author_ipc::author_prepare_start,
            author_ipc::author_context,
            author_ipc::author_commit_start,
            author_ipc::author_lookup_start,
            author_ipc::author_preview_discard,
            fork_commands::fork_start,
            fork_commands::fork_lookup,
            fork_harness::harness_fork_case,
            memory_harness::harness_memory_case,
            author_harness::harness_author_case,
            memory_maintenance_commands::memory_maintenance_start,
            archive_commands::archive_export_preview,
            archive_commands::archive_import_preview,
            archive_commands::archive_export,
            archive_commands::archive_import,
            archive_commands::archive_status,
            archive_commands::archive_cancel,
            archive_commands::archive_discard,
            archive_commands::harness_archive_case,
            archive_v3_harness::harness_archive_v3_fixture,
            evaluation_commands::evaluation_catalog,
            evaluation_commands::evaluation_curated,
            comparison_commands::evaluation_comparison,
            selected_commands::evaluation_selected,
            selected_harness::harness_selected_case,
            comparison_reader_harness::harness_comparison_reader_case,
            evaluation_commands::evaluation_start,
            evaluation_commands::evaluation_open,
            evaluation_commands::evaluation_status,
            evaluation_commands::evaluation_read,
            evaluation_commands::evaluation_cancel,
            evaluation_commands::evaluation_resume,
            evaluation_commands::evaluation_rerun,
            model_commands::harness_model_case,
            model_commands::model_status,
            model_commands::model_import,
            model_commands::model_load,
            model_commands::model_unload,
            model_commands::model_cancel,
            export_commands::inspection_preview,
            export_commands::inspection_database_preview,
            export_commands::inspection_save,
            export_commands::inspection_cancel,
            export_commands::inspection_open,
            export_commands::inspection_storage,
            export_commands::inspection_load,
            export_commands::harness_export_case,
            evaluation_commands::harness_evaluation_case,
            harness::harness_checkpoint,
            harness::harness_viewport,
            harness::harness_finish,
            harness_stats,
            harness_oracle,
            harness_reopen
        ]);
    #[cfg(not(feature = "dev-harness"))]
    let builder = builder.invoke_handler(tauri::generate_handler![
        capture_exports::capture_preview,
        capture_exports::capture_save,
        capture_exports::capture_revoke,
        host_call,
        shutdown::application_close,
        archive_commands::archive_catalog,
        author_ipc::author_prepare_start,
        author_ipc::author_context,
        author_ipc::author_commit_start,
        author_ipc::author_lookup_start,
        author_ipc::author_preview_discard,
        fork_commands::fork_start,
        fork_commands::fork_lookup,
        memory_maintenance_commands::memory_maintenance_start,
        archive_commands::archive_export_preview,
        archive_commands::archive_import_preview,
        archive_commands::archive_export,
        archive_commands::archive_import,
        archive_commands::archive_status,
        archive_commands::archive_cancel,
        archive_commands::archive_discard,
        evaluation_commands::evaluation_catalog,
        evaluation_commands::evaluation_curated,
        comparison_commands::evaluation_comparison,
        selected_commands::evaluation_selected,
        evaluation_commands::evaluation_start,
        evaluation_commands::evaluation_open,
        evaluation_commands::evaluation_status,
        evaluation_commands::evaluation_read,
        evaluation_commands::evaluation_cancel,
        evaluation_commands::evaluation_resume,
        evaluation_commands::evaluation_rerun,
        model_commands::model_status,
        model_commands::model_import,
        model_commands::model_load,
        model_commands::model_unload,
        model_commands::model_cancel,
        export_commands::inspection_preview,
        export_commands::inspection_database_preview,
        export_commands::inspection_save,
        export_commands::inspection_cancel,
        export_commands::inspection_open,
        export_commands::inspection_storage,
        export_commands::inspection_load
    ]);
    builder
        .setup(|app| {
            #[cfg(feature = "dev-harness")]
            app.manage(Arc::new(
                comparison_reader_harness::ComparisonReaderHarness::default(),
            ));
            #[cfg(feature = "dev-harness")]
            app.manage(Arc::new(selected_harness::SelectedHarness::default()));
            let path = app.path().app_local_data_dir()?.join("stories-v1.sqlite");
            #[cfg(feature = "dev-harness")]
            let path = if harness::active() {
                std::path::PathBuf::from(
                    std::env::var_os("LOCALLORE_TEST_WORKSPACE")
                        .ok_or_else(|| std::io::Error::other("TestWorkspaceMissing"))?,
                )
            } else {
                path
            };
            #[cfg(feature = "dev-harness")]
            if harness::active()
                && std::env::var("LOCALLORE_D08_TIMELINE_HARNESS").as_deref() == Ok("1")
                && std::env::var("LOCALLORE_TEST_RESTART").as_deref() != Ok("1")
            {
                timeline_harness::seed(&path).map_err(std::io::Error::other)?;
            }
            #[cfg(feature = "dev-harness")]
            if harness::active()
                && std::env::var("LOCALLORE_D08_FORK_HARNESS").as_deref() == Ok("1")
                && std::env::var("LOCALLORE_TEST_RESTART").as_deref() != Ok("1")
            {
                fork_harness::seed(&path).map_err(std::io::Error::other)?;
            }
            #[cfg(feature = "dev-harness")]
            if memory_harness::active()
                && std::env::var("LOCALLORE_TEST_RESTART").as_deref() != Ok("1")
            {
                memory_harness::seed(&path).map_err(std::io::Error::other)?;
            }
            #[cfg(feature = "dev-harness")]
            if author_harness::active()
                && std::env::var("LOCALLORE_TEST_RESTART").as_deref() != Ok("1")
            {
                author_harness::seed(&path).map_err(std::io::Error::other)?;
            }
            let model_root = path
                .parent()
                .ok_or_else(|| std::io::Error::other("InvalidInput"))?
                .join("models");
            #[cfg(feature = "dev-harness")]
            let model_root = if harness::active()
                && std::env::var("LOCALLORE_D04_HARNESS").as_deref() == Ok("1")
            {
                std::env::var_os("LOCALLORE_D04_MODEL_ROOT")
                    .map(std::path::PathBuf::from)
                    .unwrap_or(model_root)
            } else {
                model_root
            };
            app.manage(Arc::new(models::ModelManager::new(
                model_root,
                app.path().resource_dir()?.join("runtime"),
            )));
            app.manage(Arc::new(evaluation::EvaluationManager::new(
                path.parent()
                    .ok_or_else(|| std::io::Error::other("InvalidInput"))?
                    .join("evaluation-runs-v1"),
            )));
            app.manage(WorkspaceState {
                close_gate: std::sync::Mutex::new(close_gate::CloseGate::default()),
                incarnation: exports::identifier().map_err(std::io::Error::other)?,
                path,
                lease: Arc::new(WindowLease::default()),
                host: tokio::sync::OnceCell::new(),
                preview_cleanup: Arc::new(std::sync::Mutex::new(json!({"pending":true}))),
                author: std::sync::Mutex::new(None),
            });
            #[cfg(feature = "dev-harness")]
            if harness::active() {
                app.manage(harness::HarnessState::from_env().map_err(std::io::Error::other)?);
                let handle = app.handle().clone();
                std::thread::spawn(move || {
                    std::thread::sleep(std::time::Duration::from_secs(
                        if std::env::var("LOCALLORE_D04_HARNESS").as_deref() == Ok("1") {
                            900
                        } else if std::env::var("LOCALLORE_D07_SELECTED_HARNESS").as_deref()
                            == Ok("1")
                        {
                            // Serial real SQLite fixtures, read revalidation and
                            // 27+ app-owned render checkpoints and an explicit
                            // fresh-source resume; not a turn latency SLA.
                            900
                        } else {
                            180
                        },
                    ));
                    eprintln!("D02_NATIVE_HARNESS TIMEOUT");
                    handle.exit(2);
                });
            }
            build_window(app.handle(), false)?;
            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                api.prevent_close();
                let _ = shutdown::request(
                    window.app_handle(),
                    window.label(),
                    close_gate::Intent::Window,
                );
            } else if matches!(event, tauri::WindowEvent::Destroyed) {
                // Also fence direct destruction in the app-owned dev harness.
                let _ = shutdown::request(
                    window.app_handle(),
                    window.label(),
                    close_gate::Intent::Window,
                );
            }
        })
        .build(tauri::generate_context!())
        .expect("desktop startup failed")
        .run(|app, event| {
            if let tauri::RunEvent::ExitRequested { api, code, .. } = event {
                #[cfg(feature = "dev-harness")]
                if harness::active() && code.is_none() {
                    api.prevent_exit();
                    return;
                }
                if !shutdown::exit_requested(app, code) {
                    api.prevent_exit();
                }
            }
        });
}
