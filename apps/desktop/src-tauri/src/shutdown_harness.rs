//! Fixed development-only shutdown observation. No renderer command or grant.
use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};
static FINISHING: AtomicBool = AtomicBool::new(false);

pub(crate) fn finishing() -> bool {
    mode().is_some() && FINISHING.load(Ordering::SeqCst)
}

pub(crate) fn mode() -> Option<String> {
    if !crate::harness::active() {
        return None;
    }
    std::env::var("LOCALLORE_D09_SHUTDOWN_CASE")
        .ok()
        .filter(|value| matches!(value.as_str(), "zero" | "seven" | "window"))
}

pub(crate) fn phase(phase: &'static str, epoch: u64) {
    static COUNT: AtomicUsize = AtomicUsize::new(0);
    if mode().is_some() && COUNT.fetch_add(1, Ordering::Relaxed) < 96 {
        // All callsites use literal phases and native-owned epoch coordinates.
        println!(
            "LOCALLORE_SHUTDOWN {}",
            serde_json::json!({"phase":phase,"epoch":epoch})
        );
    }
}

#[cfg(not(test))]
pub(crate) fn finish(app: &tauri::AppHandle, window: &tauri::WebviewWindow) -> bool {
    let Some(mode) = mode() else { return false };
    FINISHING.store(true, Ordering::SeqCst);
    let epoch = window
        .label()
        .strip_prefix("main-")
        .and_then(|s| s.parse().ok())
        .unwrap_or(0);
    phase("finish_requested", epoch);
    match mode.as_str() {
        "window" => {
            if crate::shutdown::request(app, window.label(), crate::close_gate::Intent::Window)
                .is_err()
            {
                app.exit(1);
            }
        }
        "seven" => app.exit(7),
        _ => app.exit(0),
    }
    true
}
