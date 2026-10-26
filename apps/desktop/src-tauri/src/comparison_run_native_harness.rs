//! Fixed native full-comparison consent/picker doubles; never real user consent.
//! Compiled and registered only with dev-harness. No renderer paths or owners.
use crate::WorkspaceState;
use serde_json::{json, Value};
use std::{
    path::{Component, Path, PathBuf},
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc,
    },
    time::{Duration, Instant},
};

#[derive(Default)]
pub struct NativeComparisonHarness {
    hold: AtomicBool,
    deny_execution: AtomicBool,
    deny_read: AtomicBool,
    lost_ack: AtomicBool,
    consent_active: AtomicBool,
}

pub fn active() -> bool {
    crate::harness::active()
        && std::env::var("LOCALLORE_TEST_MEMORY").as_deref() == Ok("1")
        && std::env::var("LOCALLORE_D07_FULL_COMPARISON_HARNESS").as_deref() == Ok("1")
        && std::env::var("LOCALLORE_D07_NATIVE_FULL_HARNESS").as_deref() == Ok("1")
}

fn checked_parent(workspace: &Path) -> Result<&Path, String> {
    if !active()
        || std::env::var_os("LOCALLORE_TEST_WORKSPACE")
            .map(PathBuf::from)
            .as_deref()
            != Some(workspace)
    {
        return Err("Forbidden".into());
    }
    let parent = workspace.parent().ok_or("Forbidden")?;
    let name = parent.file_name().and_then(|v| v.to_str()).ok_or("Forbidden")?;
    let id = name.strip_prefix("full-comparison-native-").ok_or("Forbidden")?;
    if !workspace.is_absolute()
        || workspace.components().any(|p| matches!(p, Component::ParentDir | Component::CurDir))
        || workspace.file_name().and_then(|v| v.to_str()) != Some("stories-v1.sqlite")
        || !crate::archive::valid_id(id)
        || id.bytes().any(|v| v.is_ascii_uppercase())
    {
        return Err("Forbidden".into());
    }
    Ok(parent)
}

fn pins(parent: &Path) -> Result<Vec<std::fs::File>, String> {
    crate::exports::pin_directory(parent).map_err(|_| "Forbidden".into())
}

pub fn model_root(workspace: &Path) -> Result<PathBuf, String> {
    let parent = checked_parent(workspace)?;
    let _pins = pins(parent)?;
    Ok(parent.join("model-native-v1"))
}

pub fn approved_model_source(workspace: &Path) -> Result<Option<PathBuf>, String> {
    let parent = checked_parent(workspace)?;
    let _pins = pins(parent)?;
    let source = std::env::var_os("LOCALLORE_D07_NATIVE_MODEL_SOURCE")
        .map(PathBuf::from)
        .ok_or("ModelInvalid")?;
    if !source.is_absolute()
        || source.components().any(|p| matches!(p, Component::ParentDir | Component::CurDir))
    {
        return Err("ModelInvalid".into());
    }
    // The ordinary importer owns file pinning, approved profile/hash validation,
    // cancellation and atomic publication. This double supplies only its picker.
    Ok(Some(source))
}

struct ActiveConsent<'a>(&'a AtomicBool);
impl Drop for ActiveConsent<'_> {
    fn drop(&mut self) {
        self.0.store(false, Ordering::SeqCst);
    }
}

pub fn consent(
    workspace: &Path,
    state: &NativeComparisonHarness,
    metadata: &Value,
) -> Result<bool, String> {
    let parent = checked_parent(workspace)?;
    let _pins = pins(parent)?;
    // A fixed discriminator of already service-validated metadata, not another
    // report validator or an execution grant supplied by JavaScript.
    if !metadata.is_object()
        || metadata["version"] != 1
        || metadata["kind"] != "full_comparison_execution"
        || metadata["protocol_version"] != 3
        || metadata["input_lane"] != "approved_native"
        || serde_json::to_vec(metadata).map_err(|_| "InvalidEvaluationInput")?.len() > 16 * 1024
    {
        return Err("InvalidEvaluationInput".into());
    }
    state.consent_active.store(true, Ordering::SeqCst);
    let _active = ActiveConsent(&state.consent_active);
    let began = Instant::now();
    while state.hold.load(Ordering::SeqCst) {
        if !active() {
            return Err("Forbidden".into());
        }
        if began.elapsed() >= Duration::from_secs(120) {
            return Err("PickerUnavailable".into());
        }
        std::thread::sleep(Duration::from_millis(10));
    }
    if !active() {
        return Err("Forbidden".into());
    }
    Ok(!state.deny_execution.swap(false, Ordering::SeqCst))
}

pub fn read_consent(workspace: &Path, state: &NativeComparisonHarness) -> Result<bool, String> {
    let parent = checked_parent(workspace)?;
    let _pins = pins(parent)?;
    Ok(!state.deny_read.swap(false, Ordering::SeqCst))
}

impl NativeComparisonHarness {
    pub fn take_lost_ack(&self) -> bool {
        active() && self.lost_ack.swap(false, Ordering::SeqCst)
    }
}

enum Scenario {
    Hold,
    Release,
    DenyExecution,
    DenyRead,
    LoseAck,
    Status,
}
fn scenario(value: &str) -> Result<Scenario, String> {
    match value {
        "hold-execution-consent" => Ok(Scenario::Hold),
        "release-execution-consent" => Ok(Scenario::Release),
        "deny-execution-consent" => Ok(Scenario::DenyExecution),
        "deny-read-consent" => Ok(Scenario::DenyRead),
        "lose-start-ack" => Ok(Scenario::LoseAck),
        "consent-status" => Ok(Scenario::Status),
        _ => Err("InvalidEvaluationInput".into()),
    }
}

#[tauri::command]
pub async fn harness_native_comparison_case(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    state: tauri::State<'_, Arc<NativeComparisonHarness>>,
    scenario: String,
) -> Result<Value, String> {
    if !active() {
        return Err("Forbidden".into());
    }
    let scenario = self::scenario(&scenario)?;
    let epoch = workspace.lease.capture(window.label()).map_err(str::to_owned)?;
    let lease = workspace.lease.clone();
    let path = workspace.path.clone();
    let state = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        let parent = checked_parent(&path)?;
        let _pins = pins(parent)?;
        lease.dispatch(epoch, || {
            match scenario {
                Scenario::Hold => state.hold.store(true, Ordering::SeqCst),
                Scenario::Release => state.hold.store(false, Ordering::SeqCst),
                Scenario::DenyExecution => state.deny_execution.store(true, Ordering::SeqCst),
                Scenario::DenyRead => state.deny_read.store(true, Ordering::SeqCst),
                Scenario::LoseAck => state.lost_ack.store(true, Ordering::SeqCst),
                Scenario::Status => {}
            }
            // Only fixture flags: not evidence that execution or cleanup ran.
            Ok(json!({"version":1,"kind":"native_full_comparison_fixture","synthetic":true,
                "active":state.consent_active.load(Ordering::SeqCst),
                "held":state.hold.load(Ordering::SeqCst)}))
        })
    })
    .await
    .map_err(|_| "EvaluationInternal".to_owned())?
}
