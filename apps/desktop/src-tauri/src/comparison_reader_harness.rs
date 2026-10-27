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
fn literal_mode() -> bool {
    active() && std::env::var("LOCALLORE_D07_LITERAL_COMPARISON_READER").as_deref() == Ok("1")
}
fn scene_mode() -> bool {
    active() && std::env::var("LOCALLORE_D07_SCENE_COMPARISON_READER").as_deref() == Ok("1")
}
fn root(workspace: &Path) -> Result<(PathBuf, Vec<std::fs::File>), String> {
    if !active()
        || (literal_mode() && scene_mode())
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
    let pins = crate::archive::pin(parent)?;
    Ok((parent.join("comparison-fixtures"), pins))
}

fn scene_proof(path: &Path, scenes: usize) -> Result<Value, String> {
    use locallore_eval::memory_comparison_v4::{
        self as v4, ConstructionEvidenceStatusV4 as Construction,
        PrivacyEvidenceStatusV4 as Privacy,
    };
    let report = comparison::scene_v4::inspect_comparison(path)?;
    let committed = report
        .turns
        .iter()
        .filter(|row| row.phase == "committed")
        .count();
    let expected_kind = if scenes == 2 {
        ComparisonKind::PairedSnapshots
    } else {
        ComparisonKind::ContinuousRollout
    };
    if report.version != 4
        || report.arms != v4::arm_descriptors()
        || report.kind != expected_kind
        || report.lane != "scripted_scene_literal_relevant_comparison"
        || report.physical_setups != 0
        || report.physical_setup_ms.is_some()
        || report.native_load.is_some()
        || !report.source_matches
        || report.completed_scenes != scenes
        || report.turns.len() != scenes * 12
        || report.human_reviewed != 0
        || report.human_rubric != "not_reviewed"
        || report.quality_accepted
        || report.source_bound_committed_rows != committed
        || report.turns.iter().any(|row| {
            !row.passed
                || !row.roles_known
                || row.recovered_without_checkpoint
                || (row.phase == "committed"
                    && (row.construction_evidence_status
                        != Construction::ValidatedCommittedSceneNarratorV1
                        || row.privacy_evidence_status != Privacy::CheckedFiniteSentinels))
        })
    {
        return Err("SyntheticSceneProof".into());
    }
    // Exercise the same strict retained Core facade later reached by native UI
    // dispatch, then drop its lock before another reader can own this fixture.
    let reader = comparison::scene_v4::desktop_api::open_read_only(path)?;
    let summary = comparison::scene_v4::desktop_api::summary(&reader, true)?;
    if summary["report"] != serde_json::to_value(&report).map_err(|_| "SyntheticSceneProof")?
        || summary["read_only"] != true
        || summary["execution_available"] != false
    {
        return Err("SyntheticSceneProof".into());
    }
    Ok(
        json!({"rows":report.turns.len(),"kind":report.kind,"lane":report.lane,"source_bound_committed_rows":committed,
        "human_reviewed":report.human_reviewed,"human_rubric":report.human_rubric,
        "quality_accepted":report.quality_accepted,"source_matches":report.source_matches,
        "read_only":true,"execution_available":false,"models_executed":false}),
    )
}
pub fn choose(
    workspace: &Path,
    state: &ComparisonReaderHarness,
) -> Result<Option<PathBuf>, String> {
    let (root, _root_pins) = root(workspace)?;
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
        let (fixtures,_root_pins)=root(&workspace_path)?;
        match scenario.as_str() {
            "prepare" => {
                if !fixtures.exists() { std::fs::create_dir(&fixtures).map_err(|_|"SyntheticFixtureIo")?; }
                let _pins=crate::archive::pin(&fixtures)?;
                let reference=fixtures.join("reference");
                if !reference.exists() { comparison::prepare_reference(&reference,&Cancellation::default())?; }
                let reference=comparison::open_reference(&reference)?;
                let paired=fixtures.join("paired");
                let rollout=fixtures.join("rollout");
                let mut scene_checks = None;
                let (protocol_version, paired_rows, rollout_rows) = if scene_mode() {
                    if !paired.exists() { comparison::scene_v4::run_comparison(&paired,false,ComparisonKind::PairedSnapshots,&Cancellation::default(),2,LaneFactory::ScriptedBaseline,Some(&reference))?; }
                    if !rollout.exists() { comparison::scene_v4::run_comparison(&rollout,false,ComparisonKind::ContinuousRollout,&Cancellation::default(),1,LaneFactory::ScriptedBaseline,None)?; }
                    let paired_proof=scene_proof(&paired,2)?;
                    let rollout_proof=scene_proof(&rollout,1)?;
                    scene_checks=Some(json!({"paired":paired_proof,"rollout":rollout_proof,
                        "source_gate":"fresh_domain1_committed_narrator_input_only"}));
                    (4,24,12)
                } else if literal_mode() {
                    if !paired.exists() { comparison::literal_v3::run_comparison(&paired,false,ComparisonKind::PairedSnapshots,&Cancellation::default(),2,LaneFactory::ScriptedBaseline,Some(&reference))?; }
                    if !rollout.exists() { comparison::literal_v3::run_comparison(&rollout,false,ComparisonKind::ContinuousRollout,&Cancellation::default(),1,LaneFactory::ScriptedBaseline,None)?; }
                    (3, comparison::literal_v3::inspect_comparison(&paired)?.turns.len(), comparison::literal_v3::inspect_comparison(&rollout)?.turns.len())
                } else {
                    if !paired.exists() { comparison::run_comparison(&paired,false,ComparisonKind::PairedSnapshots,&Cancellation::default(),2,LaneFactory::ScriptedBaseline,Some(&reference))?; }
                    if !rollout.exists() { comparison::run_comparison(&rollout,false,ComparisonKind::ContinuousRollout,&Cancellation::default(),1,LaneFactory::ScriptedBaseline,None)?; }
                    (2, comparison::inspect_comparison(&paired)?.turns.len(), comparison::inspect_comparison(&rollout)?.turns.len())
                };
                drop(reference);
                let fixture_inventory=inventory(&fixtures)?;
                lease.dispatch(epoch,||Ok(json!({"synthetic":true,"protocol_version":protocol_version,"paired_rows":paired_rows,"rollout_rows":rollout_rows,"models_executed":false,"fixture_inventory":fixture_inventory,"scene_proof":scene_checks})))
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
