// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Fixed synthetic selected consent/ack doubles, never user acceptance evidence.
//! No caller path, command, runtime owner, inference fault or execution server.
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
pub struct SelectedHarness {
    hold: AtomicBool,
    deny: AtomicBool,
    lost_ack: AtomicBool,
    consent_active: AtomicBool,
}
struct ActiveConsent<'a>(&'a AtomicBool);
impl Drop for ActiveConsent<'_> {
    fn drop(&mut self) {
        self.0.store(false, Ordering::SeqCst);
    }
}
pub fn active() -> bool {
    crate::comparison_reader_harness::active()
        && std::env::var("LOCALLORE_D07_SELECTED_HARNESS").as_deref() == Ok("1")
}
// Same exact identity/layout guard as the existing comparison fixture. This
// pure portion performs no filesystem work; actual entry points pin the parent.
fn workspace_parent<'a>(workspace: &'a Path, expected: Option<&Path>) -> Result<&'a Path, String> {
    if expected != Some(workspace) {
        return Err("Forbidden".into());
    }
    let parent = workspace.parent().ok_or("SyntheticWorkspaceRequired")?;
    let name = parent
        .file_name()
        .and_then(|value| value.to_str())
        .ok_or("SyntheticWorkspaceRequired")?;
    if !workspace.is_absolute()
        || workspace
            .components()
            .any(|part| matches!(part, Component::ParentDir | Component::CurDir))
        || workspace.file_name().and_then(|value| value.to_str()) != Some("stories-v1.sqlite")
        || !name
            .strip_prefix("comparison-reader-native-")
            .is_some_and(crate::archive::valid_id)
    {
        return Err("SyntheticWorkspaceRequired".into());
    }
    Ok(parent)
}
fn checked_workspace(workspace: &Path) -> Result<&Path, String> {
    if !active() {
        return Err("Forbidden".into());
    }
    let expected = std::env::var_os("LOCALLORE_TEST_WORKSPACE").map(PathBuf::from);
    workspace_parent(workspace, expected.as_deref())
}
fn metadata_kind(metadata: &Value) -> Result<(), String> {
    // This is a closed fixture discriminator, NOT a second canonical/DTO
    // validator. The actual service supplies already-validated shared metadata.
    if !metadata.is_object()
        || !matches!(metadata["version"].as_u64(), Some(1 | 2))
        || (metadata["version"] == 2 && metadata["source_protocol_version"] != 3)
        || !matches!(
            metadata["kind"].as_str(),
            Some("selected_prepared" | "selected_read")
        )
        || serde_json::to_vec(metadata)
            .map_err(|_| "InvalidEvaluationInput")?
            .len()
            > 16 * 1024
    {
        return Err("InvalidEvaluationInput".into());
    }
    Ok(())
}
fn finish_consent(state: &SelectedHarness) -> bool {
    !state.deny.swap(false, Ordering::SeqCst)
}
pub fn consent(
    workspace: &Path,
    state: &SelectedHarness,
    metadata: &Value,
) -> Result<bool, String> {
    let parent = checked_workspace(workspace)?;
    let _pins = crate::archive::pin(parent)?;
    metadata_kind(metadata)?;
    state.consent_active.store(true, Ordering::SeqCst);
    let _active = ActiveConsent(&state.consent_active);
    let started = Instant::now();
    while state.hold.load(Ordering::SeqCst) {
        if !active() {
            return Err("Forbidden".into());
        }
        if started.elapsed() >= Duration::from_secs(15) {
            return Err("PickerUnavailable".into());
        }
        std::thread::sleep(Duration::from_millis(10));
    }
    if !active() {
        return Err("Forbidden".into());
    }
    // Deliberately synthetic dev affirmation. It is not a real dialog/user
    // permission, model measurement, or an override of shared Rust validation.
    Ok(finish_consent(state))
}
fn consume_lost_ack(state: &SelectedHarness) -> bool {
    state.lost_ack.swap(false, Ordering::SeqCst)
}
pub fn take_lost_ack(state: &SelectedHarness) -> bool {
    active() && consume_lost_ack(state)
}

#[derive(Clone, Copy)]
enum Scenario {
    HoldConsent,
    ReleaseConsent,
    DenyConsent,
    LoseStartAck,
    ConsentStatus,
}
fn scenario(value: &str) -> Result<Scenario, String> {
    match value {
        "hold-consent" => Ok(Scenario::HoldConsent),
        "release-consent" => Ok(Scenario::ReleaseConsent),
        "deny-consent" => Ok(Scenario::DenyConsent),
        "lose-start-ack" => Ok(Scenario::LoseStartAck),
        "consent-status" => Ok(Scenario::ConsentStatus),
        _ => Err("InvalidEvaluationInput".into()),
    }
}
fn apply(state: &SelectedHarness, scenario: Scenario) -> Value {
    let name = match scenario {
        Scenario::HoldConsent => {
            state.hold.store(true, Ordering::SeqCst);
            "hold-consent"
        }
        Scenario::ReleaseConsent => {
            state.hold.store(false, Ordering::SeqCst);
            "release-consent"
        }
        Scenario::DenyConsent => {
            state.deny.store(true, Ordering::SeqCst);
            "deny-consent"
        }
        Scenario::LoseStartAck => {
            state.lost_ack.store(true, Ordering::SeqCst);
            "lose-start-ack"
        }
        Scenario::ConsentStatus => {
            return json!({"version":1,"kind":"selected_fixture","synthetic":true,
            "scenario":"consent-status","active":state.consent_active.load(Ordering::SeqCst),"held":state.hold.load(Ordering::SeqCst)})
        }
    };
    // This acknowledges only that a fixed flag was armed/released, not that a
    // consent worker has entered, inference ran, or an acknowledgement was lost.
    json!({"version":1,"kind":"selected_fixture","synthetic":true,"scenario":name})
}
#[tauri::command]
pub async fn harness_selected_case(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    state: tauri::State<'_, Arc<SelectedHarness>>,
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
    tauri::async_runtime::spawn_blocking(move || {
        let parent = checked_workspace(&path)?;
        let _pins = crate::archive::pin(parent)?;
        lease.dispatch(epoch, || Ok(apply(&state, scenario)))
    })
    .await
    .map_err(|_| "EvaluationInternal".to_owned())?
}

#[cfg(test)]
mod tests;
