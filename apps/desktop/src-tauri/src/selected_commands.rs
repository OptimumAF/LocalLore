// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Closed selected IPC. Native code owns paths, consent, leases and model identity.
use crate::{
    evaluation::{EvaluationManager, SelectedEvidenceInput, SelectedInputLane, SelectedPrepareInput,
        SelectedReadInput, SelectedResumeInput},
    models::ModelManager,
    WorkspaceState,
};
use locallore::{engine::parse_unique_json, inspection_query::{Observer, View}};
use locallore_eval::local_lane::comparison::desktop_api::{Arm, Edge, EvidenceRequest};
use serde_json::Value;
use std::sync::Arc;

type Result<T> = std::result::Result<T, String>;
const MAX_REQUEST: usize = 4096;
const MAX_SAFE: u64 = 9_007_199_254_740_991;
enum Action {
    Catalog,
    Prepare(SelectedPrepareInput),
    Start(String, String),
    Status(String),
    Cancel(String, u64),
    Open(String, String),
    Resume(SelectedResumeInput),
    Summary(SelectedReadInput),
    Evidence(SelectedEvidenceInput),
    Diagnostics(SelectedReadInput, Observer),
    Close(String),
    CleanupStatus,
    RetryCleanup,
}
impl Action {
    fn requires_lab(&self) -> bool {
        !matches!(self, Self::Close(_) | Self::CleanupStatus | Self::RetryCleanup)
    }
}
fn invalid<T>() -> Result<T> { Err("InvalidEvaluationInput".into()) }
fn keys(value: &Value, expected: &[&str]) -> Result<()> {
    let object=value.as_object().ok_or("InvalidEvaluationInput")?;
    if object.len()!=expected.len() || object.keys().any(|key|!expected.contains(&key.as_str())) { return invalid(); }
    Ok(())
}
fn text(value: &Value) -> Result<&str> { value.as_str().ok_or_else(||"InvalidEvaluationInput".into()) }
fn guid(value: &Value) -> Result<String> {
    let value=text(value)?;
    if value.len()!=36 || !value.bytes().enumerate().all(|(n,b)|if [8,13,18,23].contains(&n){b==b'-'}else{b.is_ascii_digit()||(b'a'..=b'f').contains(&b)}) { return invalid(); }
    Ok(value.into())
}
fn hex(value: &Value) -> Result<String> {
    let value=text(value)?;
    if value.len()!=64 || !value.bytes().all(|b|b.is_ascii_digit()||(b'a'..=b'f').contains(&b)) { return invalid(); }
    Ok(value.into())
}
fn identifier(value: &Value) -> Result<String> {
    let value=text(value)?;
    if value.is_empty()||value.len()>64||!value.bytes().all(|b|b.is_ascii_alphanumeric()||b"-_".contains(&b)){return invalid();}
    Ok(value.into())
}
fn observer(value: &Value) -> Result<Observer> {
    match value.get("kind").and_then(Value::as_str) {
        Some("player")=>{keys(value,&["kind"])?;Ok(Observer::Player)},
        Some("omniscient")=>{keys(value,&["kind"])?;Ok(Observer::Omniscient)},
        Some("character")=>{keys(value,&["kind","id"])?;Ok(Observer::Character{id:identifier(&value["id"])?})},
        _=>invalid(),
    }
}
fn arm(value: &Value) -> Result<Arm> { match value.as_str(){Some("left")=>Ok(Arm::Left),Some("right")=>Ok(Arm::Right),_=>invalid()} }
fn view(value: &Value) -> Result<View> {
    match value.as_str() {
        Some("profiles")=>Ok(View::Profiles), Some("history")=>Ok(View::History),
        Some("relationships")=>Ok(View::Relationships), Some("knowledge")=>Ok(View::Knowledge),
        Some("promises")=>Ok(View::Promises), Some("provenance")=>Ok(View::Provenance),
        Some("turn_diff")=>Ok(View::TurnDiff), Some("summaries")=>Ok(View::Summaries),
        Some("retrieval_indexes")=>Ok(View::RetrievalIndexes), _=>invalid(),
    }
}
fn evidence(value: &Value) -> Result<EvidenceRequest> {
    match value.get("kind").and_then(Value::as_str) {
        Some("query")=>{
            keys(value,&["kind","edge","observer","view"])?;
            let edge=match value["edge"].as_str(){Some("before")=>Edge::Before,Some("after")=>Edge::After,_=>return invalid()};
            Ok(EvidenceRequest::Query{edge,observer:observer(&value["observer"])?,view:view(&value["view"])?})
        }
        Some(kind @ ("receipt"|"capture"|"outputs"))=>{
            keys(value,&["kind","observer"])?;let observer=observer(&value["observer"])?;
            // These denials are based on public request shape only. They must
            // precede private identity validation, lease and Host/token probes.
            if !matches!(observer,Observer::Omniscient){return Err("Forbidden".into())}
            Ok(match kind{"receipt"=>EvidenceRequest::Receipt{observer},"capture"=>EvidenceRequest::Capture{observer},_=>EvidenceRequest::Outputs{observer}})
        }
        _=>invalid(),
    }
}
fn identity(value: &Value) -> Result<SelectedReadInput> {
    Ok(SelectedReadInput{client_id:guid(&value["clientId"])?,run_token:guid(&value["runToken"])?,binding:hex(&value["binding"])?})
}
fn parse(action: &str, raw: &str) -> Result<Action> {
    if action.len()>32{return invalid()}
    // Structural checking is not an Engine/Store authority. Decode the raw
    // bytes once so duplicate keys cannot disappear inside serde_json::Value.
    let value=parse_unique_json(raw.as_bytes(),MAX_REQUEST).map_err(|_|"InvalidEvaluationInput")?;
    match action {
        "catalog"|"cleanup_status"|"retry_cleanup"=>{
            keys(&value,&[])?;
            Ok(match action{"catalog"=>Action::Catalog,"cleanup_status"=>Action::CleanupStatus,_=>Action::RetryCleanup})
        }
        "prepare"=>{
            keys(&value,&["clientId","readerClientId","runToken","binding","turnId","arm","lane"])?;
            let lane=match value["lane"].as_str(){Some("scripted_baseline")=>SelectedInputLane::ScriptedBaseline,Some("approved_native")=>SelectedInputLane::ApprovedNative,_=>return invalid()};
            Ok(Action::Prepare(SelectedPrepareInput{client_id:guid(&value["clientId"])?,reader_client_id:guid(&value["readerClientId"])?,run_token:guid(&value["runToken"])?,binding:hex(&value["binding"])?,turn_id:identifier(&value["turnId"])?,arm:arm(&value["arm"])?,lane}))
        }
        "start"=>{keys(&value,&["clientId","planToken"])?;Ok(Action::Start(guid(&value["clientId"])?,guid(&value["planToken"])?))}
        "status"|"close"=>{keys(&value,&["clientId"])?;let client=guid(&value["clientId"])?;Ok(if action=="status"{Action::Status(client)}else{Action::Close(client)})}
        "cancel"=>{
            keys(&value,&["clientId","operationId"])?;
            let operation=value["operationId"].as_u64().filter(|n|*n>0&&*n<=MAX_SAFE).ok_or("InvalidEvaluationInput")?;
            Ok(Action::Cancel(guid(&value["clientId"])?,operation))
        }
        "open"=>{keys(&value,&["clientId","runId"])?;Ok(Action::Open(guid(&value["clientId"])?,guid(&value["runId"])?))}
        "resume"=>{
            keys(&value,&["clientId","runToken","readerClientId","sourceToken","sourceBinding"])?;
            Ok(Action::Resume(SelectedResumeInput{client_id:guid(&value["clientId"])?,run_token:guid(&value["runToken"])?,reader_client_id:guid(&value["readerClientId"])?,source_token:guid(&value["sourceToken"])?,source_binding:hex(&value["sourceBinding"])?}))
        }
        "summary"=>{keys(&value,&["clientId","runToken","binding"])?;Ok(Action::Summary(identity(&value)?))}
        "evidence"=>{
            keys(&value,&["clientId","runToken","binding","arm","request"])?;
            let request=evidence(&value["request"])?;
            Ok(Action::Evidence(SelectedEvidenceInput{identity:identity(&value)?,arm:arm(&value["arm"])?,request}))
        }
        "diagnostics"=>{
            keys(&value,&["clientId","runToken","binding","observer"])?;
            let observer=observer(&value["observer"])?;
            if !matches!(observer,Observer::Omniscient){return Err("Forbidden".into())}
            Ok(Action::Diagnostics(identity(&value)?,observer))
        }
        _=>invalid(),
    }
}
fn closed_error(error: String) -> String {
    match error.as_str() {
        "InvalidEvaluationInput"|"EvaluationBusy"|"EvaluationModelBusy"|"EvaluationIo"|
        "EvaluationInternal"|"EvaluationBudget"|"EvaluationRunLimit"|"EvaluationSourceMismatch"|
        "EvaluationIntegrity"|"EvaluationTokenLimit"|"UnknownEvaluationRun"|"Closed"|"Forbidden"|
        "PickerUnavailable"|"Cancelled"|"Cleanup"|"NativeUnavailable"=>error,
        "Unsupported"|"UnsupportedPlatform"=>"NativeUnavailable".into(),
        "Io"|"StorageUnavailable"=>"EvaluationIo".into(),
        _=>"EvaluationInternal".into(),
    }
}

#[tauri::command]
pub async fn evaluation_selected(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_,WorkspaceState>,
    manager: tauri::State<'_,Arc<EvaluationManager>>,
    models: tauri::State<'_,Arc<ModelManager>>,
    action: String,
    request: String,
) -> Result<Value> {
    let action=parse(&action,&request)?;
    let epoch=workspace.lease.capture(window.label()).map_err(str::to_owned)?;
    let lease=workspace.lease.clone();let manager=manager.inner().clone();let models=models.inner().clone();
    // Closing/reaping must remain available without initializing a story Host
    // or restoring Lab permission. These actions cannot inspect private data.
    if !action.requires_lab() {
        return tauri::async_runtime::spawn_blocking(move||match action{
            Action::Close(client)=>manager.selected_close(&lease,epoch,&client),
            Action::CleanupStatus=>manager.selected_cleanup_status(&lease,epoch),
            Action::RetryCleanup=>manager.selected_retry_cleanup(&lease,&models,epoch),
            _=>Err("EvaluationInternal".into()),
        }).await.map_err(|_|"EvaluationInternal".to_owned())?.map_err(closed_error);
    }
    let host=workspace.get(epoch).await.map_err(closed_error)?;
    let granted=host.story_lab_granted();if !granted{return Err("Forbidden".into())}
    #[cfg(windows)]
    let owner=window.hwnd().map_err(|_|"Closed")?.0 as isize;
    #[cfg(not(windows))]
    let owner=0;
    tauri::async_runtime::spawn_blocking(move||match action{
        Action::Catalog=>manager.selected_catalog(&lease,epoch,granted),
        Action::Prepare(input)=>manager.selected_prepare(&lease,&models,epoch,granted,input,move|metadata|crate::exports::confirm_selected(owner,metadata)),
        Action::Start(client,token)=>manager.selected_start(&lease,&models,epoch,granted,&client,&token),
        Action::Status(client)=>manager.selected_status(&lease,epoch,granted,&client),
        Action::Cancel(client,operation)=>manager.selected_cancel(&lease,epoch,granted,&client,operation),
        Action::Open(client,run)=>manager.selected_open(&lease,&models,epoch,granted,&client,&run,move|metadata|crate::exports::confirm_selected(owner,metadata)),
        Action::Resume(input)=>manager.selected_resume(&lease,&models,epoch,granted,input,move|metadata|crate::exports::confirm_selected(owner,metadata)),
        Action::Summary(input)=>manager.selected_summary(&lease,&models,epoch,granted,input),
        Action::Evidence(input)=>manager.selected_evidence(&lease,&models,epoch,granted,input),
        Action::Diagnostics(input,observer)=>manager.selected_diagnostics(&lease,&models,epoch,granted,input,observer),
        Action::Close(_)|Action::CleanupStatus|Action::RetryCleanup=>Err("EvaluationInternal".into()),
    }).await.map_err(|_|"EvaluationInternal".to_owned())?.map_err(closed_error)
}

#[cfg(test)]
mod tests;
