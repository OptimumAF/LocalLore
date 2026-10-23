#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
use locallore::host::Host;
use serde_json::Value;
use std::sync::Arc;
use tauri::Manager;
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
    host: tokio::sync::OnceCell<Arc<Host>>,
}
impl WorkspaceState {
    async fn get(&self) -> Result<Arc<Host>, String> {
        self.host
            .get_or_try_init(|| async {
                let path = self.path.clone();
                tauri::async_runtime::spawn_blocking(move || {
                    #[cfg(feature = "dev-harness")]
                    if harness::active()
                        && std::env::var("LOCALLORE_TEST_MEMORY").as_deref() == Ok("1")
                    {
                        return Ok(Arc::new(Host::new(true)));
                    }
                    let parent = path.parent().ok_or_else(|| "InvalidInput".to_owned())?;
                    std::fs::create_dir_all(parent).map_err(|_| "Io".to_owned())?;
                    locallore_workspace::open(&path, true).map(Arc::new)
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
    if window.label() != "main" {
        return Err("Forbidden".into());
    }
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
    let host = workspace.get().await?;
    tauri::async_runtime::spawn_blocking(move || {
        let _permit = permit;
        host.call(input.as_bytes())
    })
    .await
    .map_err(|_| "Transport".to_owned())
}
fn build_window(app: &tauri::AppHandle, reopened: bool) -> tauri::Result<()> {
    let testing = cfg!(feature = "dev-harness")
        && std::env::var("LOCALLORE_D02_HARNESS").as_deref() == Ok("1");
    let script = if testing {
        format!(
            "window.__LOCALLORE_TEST__={{enabled:true,backend:'native',durable:{},failure:{},stage:'{}'}};",
            std::env::var("LOCALLORE_TEST_MEMORY").as_deref() != Ok("1"),
            std::env::var("LOCALLORE_TEST_STORAGE_FAILURE").as_deref() == Ok("1"),
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
        tauri::WebviewWindowBuilder::new(app, "main", tauri::WebviewUrl::App("index.html".into()));
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
    if !harness::active() || window.label() != "main" {
        return Err("Forbidden");
    }
    let (sessions, workers) = workspace
        .get()
        .await
        .map_err(|_| "StorageUnavailable")?
        .live_counts();
    Ok(serde_json::json!({"sessions":sessions,"workers":workers}))
}
#[cfg(feature = "dev-harness")]
#[tauri::command]
fn harness_oracle(window: tauri::WebviewWindow, receipts: Value) -> Result<Value, &'static str> {
    if !harness::active() || window.label() != "main" {
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
    if !harness::active() || window.label() != "main" || state.0.swap(true, Ordering::SeqCst) {
        return Err("Forbidden");
    }
    window.destroy().map_err(|_| "CloseFailed")?;
    tauri::async_runtime::spawn(async move {
        for _ in 0..40 {
            tokio::time::sleep(std::time::Duration::from_millis(25)).await;
            if app.get_webview_window("main").is_none()
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
    let builder = tauri::Builder::default().manage(Arc::new(tokio::sync::Semaphore::new(4)));
    #[cfg(feature = "dev-harness")]
    let builder = builder
        .manage(Reopen(AtomicBool::new(false)))
        .invoke_handler(tauri::generate_handler![
            host_call,
            harness::harness_checkpoint,
            harness::harness_viewport,
            harness::harness_finish,
            harness_stats,
            harness_oracle,
            harness_reopen
        ]);
    #[cfg(not(feature = "dev-harness"))]
    let builder = builder.invoke_handler(tauri::generate_handler![host_call]);
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
            app.manage(WorkspaceState {
                path,
                host: tokio::sync::OnceCell::new(),
            });
            #[cfg(feature = "dev-harness")]
            if harness::active() {
                app.manage(harness::HarnessState::from_env().map_err(std::io::Error::other)?);
                let handle = app.handle().clone();
                std::thread::spawn(move || {
                    std::thread::sleep(std::time::Duration::from_secs(180));
                    eprintln!("D02_NATIVE_HARNESS TIMEOUT");
                    handle.exit(2);
                });
            }
            build_window(app.handle(), false)?;
            Ok(())
        })
        .on_window_event(|window, event| {
            if matches!(event, tauri::WindowEvent::Destroyed) {
                if let Some(host) = window.state::<WorkspaceState>().ready() {
                    tauri::async_runtime::spawn_blocking(move || host.close_all());
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
