#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
use locallore::host::Host;
use serde_json::Value;
use std::sync::Arc;
use tauri::Manager;

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
    // Lifecycle/control commands remain reachable while all generation slots are busy.
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
    .map_err(|_| "WorkerFailed")
}
#[tauri::command]
fn smoke_finish(
    window: tauri::WebviewWindow,
    app: tauri::AppHandle,
    report: Value,
) -> Result<(), &'static str> {
    if window.label() != "main" || std::env::var("LOCALLORE_D01_SMOKE").as_deref() != Ok("1") {
        return Err("Forbidden");
    }
    let expected = headless();
    let pass = report == expected;
    println!(
        "D01_NATIVE_SMOKE {}: {} WebView replies compared with headless Host",
        if pass { "PASS" } else { "FAIL" },
        report.as_array().map_or(0, Vec::len)
    );
    app.exit(if pass { 0 } else { 1 });
    Ok(())
}
fn headless() -> Value {
    let host = Host::new(true);
    let steps: Vec<Value> =
        serde_json::from_str(include_str!("../../ui/smoke-requests.json")).unwrap();
    Value::Array(
        steps
            .iter()
            .map(|v| host.call(serde_json::to_string(v).unwrap().as_bytes()))
            .collect(),
    )
}
fn main() {
    tauri::Builder::default()
        .manage(Arc::new(Host::new(true)))
        .manage(Arc::new(tokio::sync::Semaphore::new(4)))
        .setup(|app| {
            if std::env::var("LOCALLORE_D01_SMOKE").as_deref() == Ok("1") {
                let handle = app.handle().clone();
                std::thread::spawn(move || {
                    std::thread::sleep(std::time::Duration::from_secs(30));
                    eprintln!("D01_NATIVE_SMOKE TIMEOUT");
                    handle.exit(2);
                });
            }
            tauri::WebviewWindowBuilder::new(
                app,
                "main",
                tauri::WebviewUrl::App("index.html".into()),
            )
            .title("LocalLore · Desktop engine spike")
            .inner_size(1040.0, 760.0)
            .on_navigation(|url| {
                (url.scheme() == "http" && url.host_str() == Some("tauri.localhost"))
                    || (url.scheme() == "tauri" && url.host_str() == Some("localhost"))
            })
            .on_new_window(|_, _| tauri::webview::NewWindowResponse::Deny)
            .initialization_script(
                if std::env::var("LOCALLORE_D01_SMOKE").as_deref() == Ok("1") {
                    "window.__D01_SMOKE__=true;"
                } else {
                    "window.__D01_SMOKE__=false;"
                },
            )
            .build()?;
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![host_call, smoke_finish])
        .on_window_event(|window, event| {
            if matches!(event, tauri::WindowEvent::Destroyed) {
                window.state::<Arc<Host>>().close_all();
            }
        })
        .run(tauri::generate_context!())
        .expect("desktop startup failed");
}
