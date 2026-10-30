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
    io::{Read, Write},
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
fn diagnostic_mode() -> bool {
    active()
        && scene_mode()
        && !literal_mode()
        && std::env::var("LOCALLORE_D07_NARRATION_DIAGNOSTIC_READER").as_deref() == Ok("1")
}
pub(super) fn selected_scene_flags(
    base: bool,
    selected: bool,
    scene: bool,
    literal: bool,
    diagnostic: bool,
) -> bool {
    base && selected && scene && !literal && !diagnostic
}
pub(super) fn selected_scene_requested() -> bool {
    std::env::var("LOCALLORE_D07_SELECTED_HARNESS").as_deref() == Ok("1")
        && std::env::var("LOCALLORE_D07_SCENE_COMPARISON_READER").as_deref() == Ok("1")
}
pub(super) fn selected_scene_mode() -> bool {
    selected_scene_flags(
        active(),
        std::env::var("LOCALLORE_D07_SELECTED_HARNESS").as_deref() == Ok("1"),
        std::env::var("LOCALLORE_D07_SCENE_COMPARISON_READER").as_deref() == Ok("1"),
        std::env::var("LOCALLORE_D07_LITERAL_COMPARISON_READER").as_deref() == Ok("1"),
        std::env::var("LOCALLORE_D07_NARRATION_DIAGNOSTIC_READER").as_deref() == Ok("1"),
    )
}
fn root(workspace: &Path) -> Result<(PathBuf, Vec<std::fs::File>), String> {
    if !active()
        || (literal_mode() && scene_mode())
        || (selected_scene_requested() && !selected_scene_mode())
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
    if diagnostic_mode() {
        let folder = match state.choice.load(Ordering::SeqCst) {
            20 => "diagnostic-recorded",
            21 => "diagnostic-legacy",
            22 => "diagnostic-missing",
            23 => "diagnostic-unavailable",
            24 => "diagnostic-rejected",
            25 => "diagnostic-malformed",
            _ => return Err("SyntheticCaseRequired".into()),
        };
        return Ok(Some(root.join(folder)));
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
    inventory_stats(root).map(|(files, _, _)| files)
}
fn inventory_stats(
    root: &Path,
) -> Result<(std::collections::BTreeMap<String, String>, usize, usize), String> {
    inventory_stats_for_mode(root, diagnostic_mode(), false)
}
fn inventory_stats_for_mode(
    root: &Path,
    diagnostic: bool,
    selected: bool,
) -> Result<(std::collections::BTreeMap<String, String>, usize, usize), String> {
    fn visit(
        root: &Path,
        path: &Path,
        depth: usize,
        out: &mut std::collections::BTreeMap<String, String>,
        total: &mut usize,
        entries: &mut usize,
        mode: (bool, bool),
    ) -> Result<(), String> {
        let (diagnostic, selected) = mode;
        *entries = entries.checked_add(1).ok_or("SyntheticFixtureBudget")?;
        if depth > 8
            || (if diagnostic || selected {
                *entries > 8192
            } else {
                out.len() >= 2048
            })
        {
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
                    entries,
                    mode,
                )?;
            }
        } else {
            if !metadata.is_file()
                || metadata.len() > 8 * 1024 * 1024
                || (selected && out.len() >= 2048)
            {
                return Err("SyntheticFixtureBudget".into());
            }
            let bytes = if diagnostic || selected {
                read_fixture_bytes(path, 8 * 1024 * 1024)?
            } else {
                std::fs::read(path).map_err(|_| "SyntheticFixtureIo")?
            };
            *total = total
                .checked_add(bytes.len())
                .ok_or("SyntheticFixtureBudget")?;
            if *total > (if diagnostic { 128 } else { 64 }) * 1024 * 1024 {
                return Err("SyntheticFixtureBudget".into());
            }
            let key = path
                .strip_prefix(root)
                .map_err(|_| "SyntheticFixturePath")?
                .to_str()
                .ok_or("SyntheticFixturePath")?
                .replace('\\', "/");
            if selected && !selected_scene_relative(&key) {
                return Err("SyntheticFixturePath".into());
            }
            if out
                .insert(key, format!("{:x}", Sha256::digest(bytes)))
                .is_some()
                && selected
            {
                return Err("SyntheticFixturePath".into());
            }
        }
        Ok(())
    }
    let mut result = std::collections::BTreeMap::new();
    let mut entries = 0;
    let mut total = 0;
    visit(
        root,
        root,
        0,
        &mut result,
        &mut total,
        &mut entries,
        (diagnostic, selected),
    )?;
    Ok((result, entries, total))
}

const SELECTED_SCENE_FREEZE: &str = "selected-scene-source-freeze-v1.json";
const SELECTED_SCENE_FREEZE_CAP: usize = 1024 * 1024;

fn selected_scene_relative(value: &str) -> bool {
    !value.is_empty()
        && !value.contains('\\')
        && !value.contains(':')
        && value
            .split('/')
            .all(|part| !part.is_empty() && part != "." && part != "..")
        && !value.chars().any(char::is_control)
}
fn selected_scene_hash(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}
fn selected_scene_files<'de, D>(
    deserializer: D,
) -> Result<std::collections::BTreeMap<String, String>, D::Error>
where
    D: serde::Deserializer<'de>,
{
    struct Files;
    impl<'de> serde::de::Visitor<'de> for Files {
        type Value = std::collections::BTreeMap<String, String>;
        fn expecting(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
            formatter.write_str("a bounded unique source file map")
        }
        fn visit_map<M>(self, mut map: M) -> Result<Self::Value, M::Error>
        where
            M: serde::de::MapAccess<'de>,
        {
            let mut files = std::collections::BTreeMap::new();
            while let Some((name, hash)) = map.next_entry::<String, String>()? {
                if files.len() >= 2048
                    || !selected_scene_relative(&name)
                    || !selected_scene_hash(&hash)
                    || files.insert(name, hash).is_some()
                {
                    return Err(serde::de::Error::custom("invalid source file map"));
                }
            }
            Ok(files)
        }
    }
    deserializer.deserialize_map(Files)
}
#[derive(serde::Serialize, serde::Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
struct SelectedSceneFreeze {
    version: u16,
    kind: String,
    source_protocol_version: u16,
    #[serde(deserialize_with = "selected_scene_files")]
    files: std::collections::BTreeMap<String, String>,
    file_count: usize,
    entry_count: usize,
    total_bytes: usize,
}

/// Fixed native development fixture owner; no renderer path/stage is accepted.
pub(super) fn selected_scene_prepare(fixtures: &Path, stage: &str) -> Result<Value, String> {
    if !matches!(stage, "initial" | "restart")
        || !fixtures.is_absolute()
        || fixtures
            .components()
            .any(|p| matches!(p, Component::ParentDir | Component::CurDir))
        || fixtures.file_name().and_then(|s| s.to_str()) != Some("comparison-fixtures")
    {
        return Err("SyntheticWorkspaceRequired".into());
    }
    let parent = fixtures.parent().ok_or("SyntheticWorkspaceRequired")?;
    if !parent
        .file_name()
        .and_then(|s| s.to_str())
        .and_then(|s| s.strip_prefix("comparison-reader-native-"))
        .is_some_and(crate::archive::valid_id)
    {
        return Err("SyntheticWorkspaceRequired".into());
    }
    let _parent_pins = crate::archive::pin(parent)?;
    let freeze_path = parent.join(SELECTED_SCENE_FREEZE);
    let fixtures_present = present(fixtures)?;
    let freeze_present = present(&freeze_path)?;
    let creating = !fixtures_present && !freeze_present && stage == "initial";
    if !creating && (!fixtures_present || !freeze_present) {
        return Err("SyntheticFixtureInvalid".into());
    }
    // Decode retained bytes before opening any producer; never repair a partial set.
    let retained = if creating {
        None
    } else {
        let _freeze_pins = crate::archive::pin(&freeze_path)?;
        let info = std::fs::symlink_metadata(&freeze_path).map_err(|_| "SyntheticFixtureIo")?;
        if !info.is_file()
            || info.file_type().is_symlink()
            || info.len() > SELECTED_SCENE_FREEZE_CAP as u64
        {
            return Err("SyntheticFixtureBudget".into());
        }
        let bytes = read_fixture_bytes(&freeze_path, SELECTED_SCENE_FREEZE_CAP)?;
        let freeze: SelectedSceneFreeze =
            serde_json::from_slice(&bytes).map_err(|_| "SyntheticFixtureInvalid")?;
        Some((freeze, bytes))
    };
    if creating {
        std::fs::create_dir(fixtures).map_err(|_| "SyntheticFixtureIo")?;
    }
    let _fixture_pins = crate::archive::pin(fixtures)?;
    if !std::fs::metadata(fixtures)
        .map_err(|_| "SyntheticFixtureIo")?
        .is_dir()
    {
        return Err("SyntheticFixturePath".into());
    }
    let reference_path = fixtures.join("reference");
    if creating {
        comparison::prepare_reference(&reference_path, &Cancellation::default())?;
        let reference = comparison::open_reference(&reference_path)?;
        comparison::scene_v4::run_comparison(
            &fixtures.join("paired"),
            false,
            ComparisonKind::PairedSnapshots,
            &Cancellation::default(),
            2,
            LaneFactory::ScriptedBaseline,
            Some(&reference),
        )?;
        comparison::scene_v4::run_comparison(
            &fixtures.join("rollout"),
            false,
            ComparisonKind::ContinuousRollout,
            &Cancellation::default(),
            1,
            LaneFactory::ScriptedBaseline,
            None,
        )?;
    }
    let mut members = std::collections::BTreeSet::new();
    for entry in std::fs::read_dir(fixtures).map_err(|_| "SyntheticFixtureIo")? {
        let path = entry.map_err(|_| "SyntheticFixtureIo")?.path();
        let name = path
            .file_name()
            .and_then(|s| s.to_str())
            .ok_or("SyntheticFixturePath")?;
        if !matches!(name, "reference" | "paired" | "rollout") || !members.insert(name.to_owned()) {
            return Err("SyntheticFixtureInvalid".into());
        }
        let _pins = crate::archive::pin(&path)?;
        if !std::fs::metadata(&path)
            .map_err(|_| "SyntheticFixtureIo")?
            .is_dir()
        {
            return Err("SyntheticFixturePath".into());
        }
    }
    if members
        != ["reference", "paired", "rollout"]
            .into_iter()
            .map(str::to_owned)
            .collect()
    {
        return Err("SyntheticFixtureInvalid".into());
    }
    let (files, entries, total) = inventory_stats_for_mode(fixtures, false, true)?;
    let actual = SelectedSceneFreeze {
        version: 1,
        kind: "selected_scene_source_freeze_v1".into(),
        source_protocol_version: 4,
        file_count: files.len(),
        files,
        entry_count: entries,
        total_bytes: total,
    };
    let retained_bytes = match retained {
        Some((expected, bytes)) => {
            if actual != expected {
                return Err("SyntheticFixtureInvalid".into());
            }
            Some(bytes)
        }
        None => None,
    };
    drop(comparison::open_reference(&reference_path)?);
    let paired = scene_proof(&fixtures.join("paired"), 2)?;
    let rollout = scene_proof(&fixtures.join("rollout"), 1)?;
    // Public readers/proofs must leave all captured producer bytes unchanged.
    let (files, entries, total) = inventory_stats_for_mode(fixtures, false, true)?;
    if actual.files != files || actual.entry_count != entries || actual.total_bytes != total {
        return Err("SyntheticFixtureInvalid".into());
    }
    let bytes = match retained_bytes {
        Some(bytes) => bytes,
        None => {
            let bytes = serde_json::to_vec(&actual).map_err(|_| "SyntheticFixtureInvalid")?;
            if bytes.len() > SELECTED_SCENE_FREEZE_CAP {
                return Err("SyntheticFixtureBudget".into());
            }
            fixed_new(&freeze_path, &bytes)?;
            bytes
        }
    };
    Ok(
        json!({"synthetic":true,"protocol_version":4,"paired_rows":24,"rollout_rows":12,
        "models_executed":false,"scene_proof":{"paired":paired,"rollout":rollout,
        "source_gate":"fresh_domain1_committed_narrator_input_only"},
        "fixture_inventory":{"version":1,"kind":"selected_scene_source_freeze_ref_v1",
        "sha256":format!("{:x}",Sha256::digest(&bytes)),"source_protocol_version":4,
        "file_count":actual.file_count,"entry_count":actual.entry_count,"total_bytes":actual.total_bytes}}),
    )
}

const DIAGNOSTIC_FIXTURES: [(&str, &str, Option<&str>, Option<&str>); 6] = [
    (
        "diagnostic-recorded",
        "actual_scripted_host_harvest",
        Some("recorded"),
        None,
    ),
    (
        "diagnostic-legacy",
        "actual_scripted_default_no_declaration",
        Some("no_declaration"),
        None,
    ),
    (
        "diagnostic-missing",
        "retained_observation_moved_control",
        Some("no_observation"),
        None,
    ),
    (
        "diagnostic-unavailable",
        "trusted_stored_host_unavailable_control",
        Some("host_unavailable"),
        None,
    ),
    (
        "diagnostic-rejected",
        "trusted_stored_host_rejected_control",
        Some("host_rejected"),
        None,
    ),
    (
        "diagnostic-malformed",
        "trusted_stored_malformed_control",
        None,
        Some("EvaluationIntegrity"),
    ),
];
fn present(path: &Path) -> Result<bool, String> {
    match std::fs::symlink_metadata(path) {
        Ok(_) => Ok(true),
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(false),
        Err(_) => Err("SyntheticFixtureIo".into()),
    }
}
fn read_fixture_bytes(path: &Path, maximum: usize) -> Result<Vec<u8>, String> {
    let mut bytes = Vec::new();
    std::fs::File::open(path)
        .map_err(|_| "SyntheticFixtureIo")?
        .take(maximum as u64 + 1)
        .read_to_end(&mut bytes)
        .map_err(|_| "SyntheticFixtureIo")?;
    if bytes.len() > maximum {
        return Err("SyntheticFixtureBudget".into());
    }
    Ok(bytes)
}
fn fixed_bytes(path: &Path) -> Result<Vec<u8>, String> {
    let metadata = std::fs::symlink_metadata(path).map_err(|_| "SyntheticFixtureIo")?;
    if !metadata.is_file() || metadata.file_type().is_symlink() || metadata.len() > 256 * 1024 {
        return Err("SyntheticFixtureBudget".into());
    }
    read_fixture_bytes(path, 256 * 1024)
}
fn fixed_json(path: &Path) -> Result<Value, String> {
    serde_json::from_slice(&fixed_bytes(path)?).map_err(|_| "SyntheticFixtureInvalid".into())
}
fn fixed_new(path: &Path, bytes: &[u8]) -> Result<(), String> {
    let mut file = std::fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)
        .map_err(|_| "SyntheticFixtureIo")?;
    file.write_all(bytes)
        .and_then(|_| file.sync_all())
        .map_err(|_| "SyntheticFixtureIo".into())
}
fn copy_diagnostic(source: &Path, target: &Path) -> Result<(), String> {
    let expected = inventory(source)?;
    std::fs::create_dir(target).map_err(|_| "SyntheticFixtureIo")?;
    for relative in expected.keys() {
        let source = source.join(relative);
        let target = target.join(relative);
        std::fs::create_dir_all(target.parent().ok_or("SyntheticFixturePath")?)
            .map_err(|_| "SyntheticFixtureIo")?;
        fixed_new(&target, &read_fixture_bytes(&source, 8 * 1024 * 1024)?)?;
    }
    if inventory(target)? != expected {
        return Err("SyntheticFixtureChanged".into());
    }
    Ok(())
}
fn left_observation(path: &Path) -> Result<PathBuf, String> {
    let checkpoint = fixed_json(&path.join("left/attempt-00.json"))?;
    let admission = checkpoint["row"]["admission"]
        .as_u64()
        .filter(|n| *n < 32)
        .ok_or("SyntheticFixtureInvalid")?;
    Ok(path
        .join("left")
        .join(format!("narration-diagnostic-v1-{admission:02}.json")))
}
fn model_observation(models: &crate::models::ModelManager) -> Result<Value, String> {
    let (sequence, owner, retained) = models.evaluation_observation_for_harness()?;
    if sequence != 0 || owner || retained != 0 {
        return Err("SyntheticModelActivity".into());
    }
    Ok(
        json!({"version":1,"kind":"diagnostic_reader_model_observation_v1",
        "reservation_sequence":sequence,"owner_present":owner,"retained_evaluations":retained}),
    )
}
fn diagnostic_prepare(
    fixtures: &Path,
    models: &crate::models::ModelManager,
) -> Result<Value, String> {
    let observation = model_observation(models)?;
    let freeze = fixtures
        .parent()
        .ok_or("SyntheticFixturePath")?
        .join("diagnostic-reader-fixtures-v1.json");
    let existed = present(fixtures)?;
    let frozen = present(&freeze)?;
    if existed != frozen
        || (!existed && std::env::var("LOCALLORE_TEST_RESTART").as_deref() == Ok("1"))
    {
        return Err("SyntheticFixtureIncomplete".into());
    }
    if !existed {
        std::fs::create_dir(fixtures).map_err(|_| "SyntheticFixtureIo")?;
        let recorded = fixtures.join("diagnostic-recorded");
        comparison::scene_v4::run_comparison_with_narration_diagnostics_v1(
            &recorded,
            false,
            ComparisonKind::ContinuousRollout,
            &Cancellation::default(),
            1,
            LaneFactory::ScriptedBaseline,
            None,
        )?;
        comparison::scene_v4::run_comparison(
            &fixtures.join("diagnostic-legacy"),
            false,
            ComparisonKind::ContinuousRollout,
            &Cancellation::default(),
            1,
            LaneFactory::ScriptedBaseline,
            None,
        )?;
        for name in [
            "diagnostic-missing",
            "diagnostic-unavailable",
            "diagnostic-rejected",
            "diagnostic-malformed",
        ] {
            let target = fixtures.join(name);
            copy_diagnostic(&recorded, &target)?;
            let file = left_observation(&target)?;
            if name == "diagnostic-missing" {
                std::fs::rename(&file, fixtures.join("retained-missing-observation.bytes"))
                    .map_err(|_| "SyntheticFixtureIo")?;
            } else {
                let bytes = if name == "diagnostic-malformed" {
                    b"{".to_vec()
                } else {
                    let mut value = fixed_json(&file)?;
                    if name == "diagnostic-unavailable" {
                        value["host_reply"]["data"]["status"] = json!("unavailable");
                        value["host_reply"]["data"]
                            .as_object_mut()
                            .ok_or("SyntheticFixtureInvalid")?
                            .remove("decision");
                    } else {
                        value["host_reply"] =
                            json!({"version":1,"status":"rejected","error":"Closed"});
                    }
                    serde_json::to_vec(&value).map_err(|_| "SyntheticFixtureInvalid")?
                };
                // This fresh, ordinary fixture copy is the only mutation target.
                std::fs::write(&file, bytes).map_err(|_| "SyntheticFixtureIo")?;
            }
        }
    }
    let _pins = crate::archive::pin(fixtures)?;
    let roster = std::fs::read_dir(fixtures)
        .map_err(|_| "SyntheticFixtureIo")?
        .map(|entry| {
            entry.map_err(|_| "SyntheticFixtureIo").and_then(|entry| {
                entry
                    .file_name()
                    .into_string()
                    .map_err(|_| "SyntheticFixturePath")
            })
        })
        .collect::<Result<std::collections::BTreeSet<_>, _>>()?;
    let expected: std::collections::BTreeSet<String> = DIAGNOSTIC_FIXTURES
        .iter()
        .map(|(id, _, _, _)| id.to_string())
        .chain(std::iter::once("retained-missing-observation.bytes".into()))
        .collect();
    if roster != expected {
        return Err("SyntheticFixtureInvalid".into());
    }
    let mut entries = Vec::new();
    for (id, provenance, status, error) in DIAGNOSTIC_FIXTURES {
        let path = fixtures.join(id);
        let proof = scene_proof(&path, 1)?;
        if proof["rows"] != 12 {
            return Err("SyntheticSceneProof".into());
        }
        let opened = comparison::scene_v4::desktop_api::open_read_only(&path)?;
        let summary = comparison::scene_v4::desktop_api::summary(&opened, true)?;
        let result = comparison::scene_v4::desktop_api::narration_diagnostic_v1(
            &opened,
            summary["binding"]
                .as_str()
                .ok_or("SyntheticFixtureInvalid")?,
            &comparison::desktop_api::RowId {
                turn: "courier-01".into(),
                arm: comparison::desktop_api::Arm::Left,
            },
            locallore::inspection_query::Observer::Omniscient,
            true,
        );
        match (status, error, result) {
            (Some(expected), None, Ok(ref value)) if value["status"] == expected => {}
            (None, Some("EvaluationIntegrity"), Err(ref code))
                if matches!(code.as_str(), "DiagnosticWire" | "DiagnosticBinding") => {}
            _ => return Err("SyntheticDiagnosticProof".into()),
        }
        entries.push(json!({"id":id,"provenance":provenance,"expected_status":status,"expected_error":error}));
    }
    let (files, count, bytes) = inventory_stats(fixtures)?;
    let file_count = files.len();
    let proof = json!({"version":1,"kind":"narration_diagnostic_reader_fixture_v1","protocol_version":4,
        "synthetic":true,"fixtures":entries,"fixture_inventory":files,"model_observation":observation,
        "inventory_stats":{"entries":count,"files":file_count,"bytes":bytes},
        "inventory_limits":{"entries":8192,"bytes":128*1024*1024,"file_bytes":8*1024*1024,"depth":8}});
    let bytes = serde_json::to_vec(&proof).map_err(|_| "SyntheticFixtureInvalid")?;
    if bytes.len() > 256 * 1024 {
        return Err("SyntheticFixtureBudget".into());
    }
    if existed {
        if fixed_bytes(&freeze)? != bytes {
            return Err("SyntheticFixtureChanged".into());
        }
    } else {
        fixed_new(&freeze, &bytes)?;
    }
    Ok(proof)
}

#[tauri::command]
pub async fn harness_comparison_reader_case(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    state: tauri::State<'_, Arc<ComparisonReaderHarness>>,
    models: tauri::State<'_, Arc<crate::models::ModelManager>>,
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
    let models = models.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        lease.dispatch(epoch,||Ok(()))?;
        let (fixtures,_root_pins)=root(&workspace_path)?;
        if selected_scene_requested() && !selected_scene_mode() { return Err("Forbidden".into()); }
        if selected_scene_mode() && scenario == "prepare" {
            let stage = match std::env::var("LOCALLORE_TEST_RESTART") {
                Ok(value) if value == "1" => "restart",
                Ok(value) if value == "0" => "initial",
                Err(std::env::VarError::NotPresent) => "initial",
                _ => return Err("Forbidden".into()),
            };
            let answer = selected_scene_prepare(&fixtures, stage)?;
            return lease.dispatch(epoch, || Ok(answer));
        }
        if diagnostic_mode() {
            let answer=match scenario.as_str() {
                "prepare" => diagnostic_prepare(&fixtures,&models),
                "diagnostic-observation" => model_observation(&models),
                "choose-diagnostic-recorded" => {state.choice.store(20,Ordering::SeqCst);Ok(json!(true))},
                "choose-diagnostic-legacy" => {state.choice.store(21,Ordering::SeqCst);Ok(json!(true))},
                "choose-diagnostic-missing" => {state.choice.store(22,Ordering::SeqCst);Ok(json!(true))},
                "choose-diagnostic-unavailable" => {state.choice.store(23,Ordering::SeqCst);Ok(json!(true))},
                "choose-diagnostic-rejected" => {state.choice.store(24,Ordering::SeqCst);Ok(json!(true))},
                "choose-diagnostic-malformed" => {state.choice.store(25,Ordering::SeqCst);Ok(json!(true))},
                "hold-picker"|"release-picker"|"cancel-picker"|"lose-pick-ack" => {
                    match scenario.as_str() {
                        "hold-picker"=>state.hold.store(true,Ordering::SeqCst),
                        "release-picker"=>state.hold.store(false,Ordering::SeqCst),
                        "cancel-picker"=>state.cancelled.store(true,Ordering::SeqCst),
                        _=>state.lose_ack.store(true,Ordering::SeqCst),
                    }; Ok(json!(true))
                },
                _ => Err("SyntheticCaseRequired".into()),
            }?;
            return lease.dispatch(epoch,||Ok(answer));
        }
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
