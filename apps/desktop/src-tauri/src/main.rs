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

#[tauri::command]
async fn host_call(
    window: tauri::WebviewWindow,
    host: tauri::State<'_, Arc<Host>>,
    permits: tauri::State<'_, Arc<tokio::sync::Semaphore>>,
    input: String,
) -> Result<Value, &'static str> {
    if window.label() != "main" {
        return Err("Forbidden");
    }
    if input.len() > locallore::host::MAX_INPUT {
        return Err("TooLarge");
    }
    if !matches!(
        serde_json::from_str::<locallore::host::Envelope>(&input),
        Ok(locallore::host::Envelope {
            command: locallore::host::HostCommand::Prepare { .. },
            ..
        })
    ) {
        return Ok(host.call(input.as_bytes()));
    }
    let permit = permits
        .inner()
        .clone()
        .try_acquire_owned()
        .map_err(|_| "Busy")?;
    let host = host.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        let _permit = permit;
        host.call(input.as_bytes())
    })
    .await
    .map_err(|_| "Transport")
}
fn build_window(app: &tauri::AppHandle, reopened: bool) -> tauri::Result<()> {
    let testing = cfg!(feature = "dev-harness")
        && std::env::var("LOCALLORE_D02_HARNESS").as_deref() == Ok("1");
    let script = if testing {
        format!(
            "window.__LOCALLORE_TEST__={{enabled:true,backend:'native',stage:'{}'}};",
            if reopened { "reopened" } else { "initial" }
        )
    } else {
        "window.__LOCALLORE_TEST__=undefined;".into()
    };
    tauri::WebviewWindowBuilder::new(app, "main", tauri::WebviewUrl::App("index.html".into()))
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
fn harness_stats(
    window: tauri::WebviewWindow,
    host: tauri::State<'_, Arc<Host>>,
) -> Result<Value, &'static str> {
    if !harness::active() || window.label() != "main" {
        return Err("Forbidden");
    }
    let (sessions, workers) = host.live_counts();
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
                && app.state::<Arc<Host>>().live_counts() == (0, 0)
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
        .manage(Arc::new(Host::new(true)))
        .manage(Arc::new(tokio::sync::Semaphore::new(4)));
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
                window.state::<Arc<Host>>().close_all();
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
