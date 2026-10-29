//! Fixed native full-comparison consent/picker doubles; never real user consent.
//! Compiled and registered only with dev-harness. No renderer paths or owners.
#[cfg(test)]
mod review_profile_tests;
use crate::WorkspaceState;
use serde_json::{json, Value};
use std::{
    path::{Component, Path, PathBuf},
    sync::{
        atomic::{AtomicBool, AtomicU64, Ordering},
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
    consent_calls: AtomicU64,
}

pub fn active() -> bool {
    crate::harness::active()
        && std::env::var("LOCALLORE_TEST_MEMORY").as_deref() == Ok("1")
        && std::env::var("LOCALLORE_D07_FULL_COMPARISON_HARNESS").as_deref() == Ok("1")
        && std::env::var("LOCALLORE_D07_NATIVE_FULL_HARNESS").as_deref() == Ok("1")
}

/// Fail closed even for an inconsistent scene request; never enable ordinary
/// import/load merely because another required development flag is missing.
pub fn scene_requested() -> bool {
    std::env::var_os("LOCALLORE_D07_SCENE_NATIVE_FULL_HARNESS").is_some_and(|value| value != "0")
}
pub fn scene_active() -> bool {
    active()
        && std::env::var("LOCALLORE_D07_SCENE_NATIVE_FULL_HARNESS").as_deref() == Ok("1")
        && std::env::var("LOCALLORE_D04_HARNESS").as_deref() != Ok("1")
}
/// Closed render-only stage; this does not grant execution or choose a protocol.
pub fn review_active() -> bool {
    scene_active()
        && std::env::var_os("LOCALLORE_TEST_RESTART").is_some_and(|stage| stage == "review")
        && !std::env::vars_os().any(|(key, value)| {
            let key = key.to_string_lossy();
            let other_harness = key.starts_with("LOCALLORE_")
                && key.ends_with("_HARNESS")
                && !matches!(
                    key.as_ref(),
                    "LOCALLORE_D02_HARNESS"
                        | "LOCALLORE_D07_FULL_COMPARISON_HARNESS"
                        | "LOCALLORE_D07_NATIVE_FULL_HARNESS"
                        | "LOCALLORE_D07_SCENE_NATIVE_FULL_HARNESS"
                );
            let other_test = key.starts_with("LOCALLORE_TEST_")
                && !matches!(
                    key.as_ref(),
                    "LOCALLORE_TEST_MEMORY" | "LOCALLORE_TEST_RESTART" | "LOCALLORE_TEST_WORKSPACE"
                );
            (other_harness || other_test) && !value.is_empty() && value != "0"
        })
}

/// Detect unsupported Scene4 stages even when their Windows value is not UTF-8.
pub fn review_requested() -> bool {
    std::env::var_os("LOCALLORE_TEST_RESTART").is_some_and(|stage| {
        stage == "review" || (scene_requested() && stage != "0" && stage != "1")
    })
}

fn review_absence_from_metadata(result: std::io::Result<()>) -> Result<(), String> {
    match result {
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(()),
        Ok(()) | Err(_) => Err("Forbidden".into()),
    }
}

/// Return a fresh profile address without creating any source/output files.
pub fn review_webview_profile(workspace: &Path) -> Result<PathBuf, String> {
    fn physical_d(path: &Path) -> bool {
        path.is_absolute()
            && !path
                .components()
                .any(|part| matches!(part, Component::ParentDir | Component::CurDir))
            && matches!(path.components().next(), Some(Component::Prefix(prefix))
                if matches!(prefix.kind(), std::path::Prefix::Disk(drive) | std::path::Prefix::VerbatimDisk(drive)
                    if drive.eq_ignore_ascii_case(&b'D')))
    }
    if !review_active() || !physical_d(workspace) {
        return Err("Forbidden".into());
    }
    let source = checked_parent(workspace)?;
    let _source_pins = pins(source)?;
    review_absence_from_metadata(std::fs::symlink_metadata(workspace).map(|_| ()))?;
    let artifacts = std::env::var_os("LOCALLORE_D02_ARTIFACT_DIR")
        .map(PathBuf::from)
        .ok_or("Forbidden")?;
    if !physical_d(&artifacts)
        || artifacts.file_name().and_then(|name| name.to_str()) != Some("review")
    {
        return Err("Forbidden".into());
    }
    let output = artifacts.parent().ok_or("Forbidden")?;
    let id = output
        .file_name()
        .and_then(|name| name.to_str())
        .and_then(|name| name.strip_prefix("full-comparison-native-"))
        .ok_or("Forbidden")?;
    if !crate::archive::valid_id(id) || id.bytes().any(|byte| byte.is_ascii_uppercase()) {
        return Err("Forbidden".into());
    }
    let _output_pins = pins(output)?;
    // Resolve existing ordinary ancestors before comparing aliases/ancestry.
    let source = std::fs::canonicalize(source).map_err(|_| "Forbidden")?;
    let resolved_output = std::fs::canonicalize(output).map_err(|_| "Forbidden")?;
    if source.starts_with(&resolved_output) || resolved_output.starts_with(&source) {
        return Err("Forbidden".into());
    }
    match std::fs::symlink_metadata(&artifacts) {
        Ok(_) => {
            let _artifact_pins = pins(&artifacts)?;
        }
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {}
        Err(_) => return Err("Forbidden".into()),
    }
    let profile = output.join("webview-profile");
    review_absence_from_metadata(std::fs::symlink_metadata(&profile).map(|_| ()))?;
    Ok(profile)
}
pub fn protocol() -> Result<crate::evaluation::FullComparisonProtocol, String> {
    if scene_requested() {
        if !scene_active() {
            return Err("Forbidden".into());
        }
        Ok(crate::evaluation::FullComparisonProtocol::SceneV4)
    } else {
        Ok(crate::evaluation::FullComparisonProtocol::LiteralV3)
    }
}

fn checked_parent(workspace: &Path) -> Result<&Path, String> {
    if !active()
        || (scene_requested() && !scene_active())
        || std::env::var_os("LOCALLORE_TEST_WORKSPACE")
            .map(PathBuf::from)
            .as_deref()
            != Some(workspace)
    {
        return Err("Forbidden".into());
    }
    let parent = workspace.parent().ok_or("Forbidden")?;
    let name = parent
        .file_name()
        .and_then(|v| v.to_str())
        .ok_or("Forbidden")?;
    let id = name
        .strip_prefix("full-comparison-native-")
        .ok_or("Forbidden")?;
    if !workspace.is_absolute()
        || workspace
            .components()
            .any(|p| matches!(p, Component::ParentDir | Component::CurDir))
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
    if scene_requested() {
        if !scene_active() {
            return Err("Forbidden".into());
        }
        // Launcher-only reuse input. No directory creation, importer, alternate
        // basename or fall back to a fresh copy is allowed in the scene cohort.
        let root = std::env::var_os("LOCALLORE_D04_MODEL_ROOT")
            .map(PathBuf::from)
            .ok_or("ModelInvalid")?;
        if !root.is_absolute()
            || root
                .components()
                .any(|part| matches!(part, Component::ParentDir | Component::CurDir))
            || !matches!(root.components().next(),Some(Component::Prefix(prefix)) if matches!(prefix.kind(),std::path::Prefix::Disk(_)|std::path::Prefix::VerbatimDisk(_)))
            || root.starts_with(parent)
        {
            return Err("ModelInvalid".into());
        }
        let _publication = pins(&root)?;
        // Ordinary Windows paths may name the same nested directory through
        // different case or an 8.3 alias. Compare resolved identities after
        // both ancestor chains are pinned, not just the supplied spellings.
        let resolved_root = std::fs::canonicalize(&root).map_err(|_| "ModelInvalid".to_owned())?;
        let resolved_parent =
            std::fs::canonicalize(parent).map_err(|_| "ModelInvalid".to_owned())?;
        if resolved_root.starts_with(&resolved_parent) {
            return Err("ModelInvalid".into());
        }
        return Ok(root);
    }
    Ok(parent.join("model-native-v1"))
}

pub fn approved_model_source(workspace: &Path) -> Result<Option<PathBuf>, String> {
    if scene_requested() {
        return Err("Forbidden".into());
    }
    let parent = checked_parent(workspace)?;
    let _pins = pins(parent)?;
    let source = std::env::var_os("LOCALLORE_D07_NATIVE_MODEL_SOURCE")
        .map(PathBuf::from)
        .ok_or("ModelInvalid")?;
    if !source.is_absolute()
        || source
            .components()
            .any(|p| matches!(p, Component::ParentDir | Component::CurDir))
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
        || metadata["protocol_version"] != (if scene_active() { 4 } else { 3 })
        || metadata["input_lane"] != "approved_native"
        || serde_json::to_vec(metadata)
            .map_err(|_| "InvalidEvaluationInput")?
            .len()
            > 16 * 1024
    {
        return Err("InvalidEvaluationInput".into());
    }
    if scene_active() {
        state
            .consent_calls
            .fetch_update(Ordering::SeqCst, Ordering::SeqCst, |count| {
                count.checked_add(1)
            })
            .map_err(|_| "EvaluationBudget".to_owned())?;
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
    Observation,
}
fn scenario(value: &str) -> Result<Scenario, String> {
    match value {
        "hold-execution-consent" => Ok(Scenario::Hold),
        "release-execution-consent" => Ok(Scenario::Release),
        "deny-execution-consent" => Ok(Scenario::DenyExecution),
        "deny-read-consent" => Ok(Scenario::DenyRead),
        "lose-start-ack" => Ok(Scenario::LoseAck),
        "consent-status" => Ok(Scenario::Status),
        "execution-observation" => Ok(Scenario::Observation),
        _ => Err("InvalidEvaluationInput".into()),
    }
}

#[tauri::command]
pub async fn harness_native_comparison_case(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    state: tauri::State<'_, Arc<NativeComparisonHarness>>,
    models: tauri::State<'_, Arc<crate::models::ModelManager>>,
    scenario: String,
) -> Result<Value, String> {
    if !active() {
        return Err("Forbidden".into());
    }
    let scenario = self::scenario(&scenario)?;
    let epoch = workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)?;
    let lease = workspace.lease.clone();
    let path = workspace.path.clone();
    let state = state.inner().clone();
    let models = models.inner().clone();
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
                Scenario::Observation => {
                    if !scene_active() { return Err("Forbidden".into()); }
                    let (sequence, owner_present, retained) = models.evaluation_observation_for_harness()?;
                    return Ok(json!({"version":1,"kind":"native_scene_execution_observation","protocol_version":4,
                        "reservation_sequence":sequence,"consent_calls":state.consent_calls.load(Ordering::SeqCst),
                        "owner_present":owner_present,"retained_evaluations":retained}));
                }
            }
            // Only fixture flags: not evidence that execution or cleanup ran.
            Ok(
                json!({"version":1,"kind":"native_full_comparison_fixture","synthetic":true,
                "active":state.consent_active.load(Ordering::SeqCst),
                "held":state.hold.load(Ordering::SeqCst)}),
            )
        })
    })
    .await
    .map_err(|_| "EvaluationInternal".to_owned())?
}
