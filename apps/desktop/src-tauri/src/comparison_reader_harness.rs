//! Fixed synthetic development fixture and native picker doubles. No caller paths.
use crate::WorkspaceState;
use locallore::inference::Cancellation;
use locallore_eval::local_lane::{
    comparison::{self, ComparisonKind},
    LaneFactory,
};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    path::{Component, Path, PathBuf},
    sync::{
        atomic::{AtomicBool, AtomicU8, Ordering},
        Arc,
    },
    time::{Duration, Instant},
};

#[derive(Default)]
pub struct ComparisonReaderHarness {
    choice: AtomicU8,
    hold: AtomicBool,
    cancelled: AtomicBool,
    lose_ack: AtomicBool,
}
pub fn active() -> bool {
    crate::harness::active()
        && std::env::var("LOCALLORE_D07_COMPARISON_READER_HARNESS").as_deref() == Ok("1")
}
fn root(workspace: &Path) -> Result<PathBuf, String> {
    if !active()
        || std::env::var_os("LOCALLORE_TEST_WORKSPACE")
            .map(PathBuf::from)
            .as_deref()
            != Some(workspace)
    {
        return Err("Forbidden".into());
    }
    let parent = workspace.parent().ok_or("SyntheticWorkspaceRequired")?;
    let name = parent
        .file_name()
        .and_then(|v| v.to_str())
        .ok_or("SyntheticWorkspaceRequired")?;
    if !workspace.is_absolute()
        || workspace
            .components()
            .any(|p| matches!(p, Component::ParentDir | Component::CurDir))
        || workspace.file_name().and_then(|v| v.to_str()) != Some("stories-v1.sqlite")
        || !name
            .strip_prefix("comparison-reader-native-")
            .is_some_and(crate::archive::valid_id)
    {
        return Err("SyntheticWorkspaceRequired".into());
    }
    let _pins = crate::archive::pin(parent)?;
    Ok(parent.join("comparison-fixtures"))
}
pub fn choose(
    workspace: &Path,
    state: &ComparisonReaderHarness,
) -> Result<Option<PathBuf>, String> {
    let root = root(workspace)?;
    let started = Instant::now();
    while state.hold.load(Ordering::SeqCst) {
        if started.elapsed() > Duration::from_secs(15) {
            return Err("PickerUnavailable".into());
        }
        std::thread::sleep(Duration::from_millis(10));
    }
    if state.cancelled.swap(false, Ordering::SeqCst) {
        return Ok(None);
    }
    Ok(Some(root.join(
        if state.choice.load(Ordering::SeqCst) == 1 {
            "rollout"
        } else {
            "paired"
        },
    )))
}
pub fn take_lost_ack(state: &ComparisonReaderHarness) -> bool {
    state.lose_ack.swap(false, Ordering::SeqCst)
}
fn inventory(root: &Path) -> Result<std::collections::BTreeMap<String, String>, String> {
    fn visit(
        root: &Path,
        path: &Path,
        depth: usize,
        out: &mut std::collections::BTreeMap<String, String>,
        total: &mut usize,
    ) -> Result<(), String> {
        if depth > 8 || out.len() >= 2048 {
            return Err("SyntheticFixtureBudget".into());
        }
        let metadata = std::fs::symlink_metadata(path).map_err(|_| "SyntheticFixtureIo")?;
        if metadata.file_type().is_symlink() {
            return Err("SyntheticFixturePath".into());
        }
        if metadata.is_dir() {
            let _pins = crate::archive::pin(path)?;
            for item in std::fs::read_dir(path).map_err(|_| "SyntheticFixtureIo")? {
                visit(
                    root,
                    &item.map_err(|_| "SyntheticFixtureIo")?.path(),
                    depth + 1,
                    out,
                    total,
                )?;
            }
        } else {
            if !metadata.is_file() || metadata.len() > 8 * 1024 * 1024 {
                return Err("SyntheticFixtureBudget".into());
            }
            let bytes = std::fs::read(path).map_err(|_| "SyntheticFixtureIo")?;
            *total = total
                .checked_add(bytes.len())
                .ok_or("SyntheticFixtureBudget")?;
            if *total > 64 * 1024 * 1024 {
                return Err("SyntheticFixtureBudget".into());
            }
            let key = path
                .strip_prefix(root)
                .map_err(|_| "SyntheticFixturePath")?
                .to_str()
                .ok_or("SyntheticFixturePath")?
                .replace('\\', "/");
            out.insert(key, format!("{:x}", Sha256::digest(bytes)));
        }
        Ok(())
    }
    let mut result = std::collections::BTreeMap::new();
    visit(root, root, 0, &mut result, &mut 0)?;
    Ok(result)
}

#[tauri::command]
pub async fn harness_comparison_reader_case(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    state: tauri::State<'_, Arc<ComparisonReaderHarness>>,
    scenario: String,
) -> Result<Value, String> {
    if !active() {
        return Err("Forbidden".into());
    }
    let epoch = workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)?;
    let lease = workspace.lease.clone();
    let workspace_path = workspace.path.clone();
    let state = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        lease.dispatch(epoch,||Ok(()))?;
        let fixtures=root(&workspace_path)?;
        match scenario.as_str() {
            "prepare" => {
                if !fixtures.exists() { std::fs::create_dir(&fixtures).map_err(|_|"SyntheticFixtureIo")?; }
                let _pins=crate::archive::pin(&fixtures)?;
                let reference=fixtures.join("reference");
                if !reference.exists() { comparison::prepare_reference(&reference,&Cancellation::default())?; }
                let reference=comparison::open_reference(&reference)?;
                let paired=fixtures.join("paired");
                if !paired.exists() { comparison::run_comparison(&paired,false,ComparisonKind::PairedSnapshots,&Cancellation::default(),2,LaneFactory::ScriptedBaseline,Some(&reference))?; }
                let rollout=fixtures.join("rollout");
                if !rollout.exists() { comparison::run_comparison(&rollout,false,ComparisonKind::ContinuousRollout,&Cancellation::default(),1,LaneFactory::ScriptedBaseline,None)?; }
                drop(reference);
                let paired=comparison::inspect_comparison(&paired)?;
                let rollout=comparison::inspect_comparison(&rollout)?;
                let fixture_inventory=inventory(&fixtures)?;
                lease.dispatch(epoch,||Ok(json!({"synthetic":true,"paired_rows":paired.turns.len(),"rollout_rows":rollout.turns.len(),"models_executed":false,"fixture_inventory":fixture_inventory})))
            }
            "choose-paired" => { state.choice.store(0,Ordering::SeqCst); Ok(json!(true)) }
            "choose-rollout" => { state.choice.store(1,Ordering::SeqCst); Ok(json!(true)) }
            "cancel-picker" => { state.cancelled.store(true,Ordering::SeqCst); Ok(json!(true)) }
            "hold-picker" => { state.hold.store(true,Ordering::SeqCst); Ok(json!(true)) }
            "release-picker" => { state.hold.store(false,Ordering::SeqCst); Ok(json!(true)) }
            "lose-pick-ack" => { state.lose_ack.store(true,Ordering::SeqCst); Ok(json!(true)) }
            _ => Err("SyntheticCaseRequired".into()),
        }
    }).await.map_err(|_|"SyntheticFixtureInternal".to_owned())?
}
