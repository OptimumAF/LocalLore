#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
use locallore::host::Host;
use serde_json::{json, Value};
use std::sync::Arc;
use tauri::Manager;
mod export_commands;
mod exports;
mod lease;
mod model_commands;
mod models;
use lease::WindowLease;
#[cfg(feature = "dev-harness")]
mod harness;
#[cfg(feature = "dev-harness")]
mod test_bridge;
#[cfg(feature = "dev-harness")]
use std::sync::atomic::{AtomicBool, Ordering};
#[cfg(feature = "dev-harness")]
struct Reopen(AtomicBool);

struct WorkspaceState {
    path: std::path::PathBuf,
    lease: Arc<WindowLease>,
    host: tokio::sync::OnceCell<Arc<Host>>,
    preview_cleanup: Arc<std::sync::Mutex<Value>>,
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
    let testing = cfg!(feature = "dev-harness")
        && std::env::var("LOCALLORE_D02_HARNESS").as_deref() == Ok("1");
    let script = if testing {
        format!(
            "window.__LOCALLORE_TEST__={{enabled:true,backend:'native',durable:{},failure:{},exporting:{},localplay:{},inspecting:{},stage:'{}'}};",
            std::env::var("LOCALLORE_TEST_MEMORY").as_deref() != Ok("1"),
            std::env::var("LOCALLORE_TEST_STORAGE_FAILURE").as_deref() == Ok("1"),
            std::env::var("LOCALLORE_D03_HARNESS").as_deref() == Ok("1"),
              std::env::var("LOCALLORE_D04_HARNESS").as_deref() == Ok("1"),
            std::env::var("LOCALLORE_D05_HARNESS").as_deref() == Ok("1"),
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
        .manage(Arc::new(tokio::sync::Semaphore::new(4)))
        .manage(Arc::new(exports::ExportBroker::default()));
    #[cfg(feature = "dev-harness")]
    let builder = builder
        .manage(Reopen(AtomicBool::new(false)))
        .manage(export_commands::TestExportState::default())
        .manage(model_commands::TestModelState::default())
        .invoke_handler(tauri::generate_handler![
            host_call,
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
            harness::harness_checkpoint,
            harness::harness_viewport,
            harness::harness_finish,
            harness_stats,
            harness_oracle,
            harness_reopen
        ]);
    #[cfg(not(feature = "dev-harness"))]
    let builder = builder.invoke_handler(tauri::generate_handler![
        host_call,
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
            app.manage(WorkspaceState {
                path,
                lease: Arc::new(WindowLease::default()),
                host: tokio::sync::OnceCell::new(),
                preview_cleanup: Arc::new(std::sync::Mutex::new(json!({"pending":true}))),
            });
            #[cfg(feature = "dev-harness")]
            if harness::active() {
                app.manage(harness::HarnessState::from_env().map_err(std::io::Error::other)?);
                let handle = app.handle().clone();
                std::thread::spawn(move || {
                    std::thread::sleep(std::time::Duration::from_secs(
                        if std::env::var("LOCALLORE_D04_HARNESS").as_deref() == Ok("1") {
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
            if matches!(event, tauri::WindowEvent::Destroyed) {
                let state = window.state::<WorkspaceState>();
                if let Some(closed) = state.lease.invalidate(window.label()) {
                    window
                        .state::<Arc<exports::ExportBroker>>()
                        .invalidate(closed - 1);
                    let model_manager = window
                        .app_handle()
                        .state::<Arc<models::ModelManager>>()
                        .inner()
                        .clone();
                    let retired = model_manager.retire();
                    let lease = state.lease.clone();
                    let host = state.ready();
                    tauri::async_runtime::spawn_blocking(move || {
                        lease.finish_close(closed, || {
                            if let Some(host) = &host {
                                host.close_all();
                            }
                        });
                        model_manager.close(host.as_deref(), retired);
                    });
                }
            }
        })
        .build(tauri::generate_context!())
        .expect("desktop startup failed")
        .run(|_app, event| {
            #[cfg(feature = "dev-harness")]
            if harness::active() {
                if let tauri::RunEvent::ExitRequested {
                    api, code: None, ..
                } = event
                {
                    api.prevent_exit();
                }
            }
            #[cfg(not(feature = "dev-harness"))]
            let _ = event;
        });
}
