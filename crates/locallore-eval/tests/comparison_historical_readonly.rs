//! Opt-in reopening of a genuine, completed but failing historical synthetic run.
//! No historical artifact is generated, repaired, relabelled, or overwritten here.
use locallore::inference::Cancellation;
use locallore_eval::{
    local_lane::{comparison::*, LaneFactory},
    memory_comparison_v2::ComparisonReportV2,
};
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::{Path, PathBuf},
};

const COHORT_ENV: &str = "LOCALLORE_D07_HISTORICAL_COHORT";
// Executed source 0fd803bcba50fa700efc27072861a51dc6ea3be3, before 30be3c5.
// These are the original bytes from the retained 33356 rollout, not new fixtures.
const SOURCE: &str = "d2d4d193e4d12c289229aed7cd60886cf28c2eab39c669cc53b41863e6e876ff";
const SUITE: &str = "6e7172c6c8bedb4b82b703aac30b7b92c5a924d0203578cb2f027611d7def21a";
const MANIFEST: &str = "3e6ff45d65582ff9b65e550210dc0b14ff8a9fbf7d538a878d7f35014b0d668b";
const REPORT: &str = "4167a78bb84ea5cad983d7eb8ff83fb0be1c4e93d4deb019bfac1be05f785a2d";
const LEFT_DB: &str = "0a810374ef2c2f94ef890899a2377a70a90b9d63a83bdf6adc5f87c57e230fa1";
const RIGHT_DB: &str = "8b749d981bd8b1806c6e6a11e2b4b943926344b98f01f9033cfa44fca71e6576";
const MAX_FILE: u64 = 1024 * 1024;
const MAX_TOTAL: usize = 64 * 1024 * 1024;
const MAX_ENTRIES: usize = 1024;

fn sha256(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

#[derive(Debug, PartialEq, Eq)]
struct Inventory {
    directories: BTreeSet<PathBuf>,
    files: BTreeMap<PathBuf, Vec<u8>>,
}

fn inventory(root: &Path) -> Inventory {
    fn visit(
        root: &Path,
        relative: &Path,
        depth: usize,
        result: &mut Inventory,
        total: &mut usize,
    ) {
        assert!(depth <= 8, "historical evidence directory depth");
        let path = root.join(relative);
        let metadata = fs::symlink_metadata(&path).expect("ordinary historical entry");
        assert!(!metadata.file_type().is_symlink(), "no evidence symlinks");
        if metadata.is_dir() {
            result.directories.insert(relative.into());
            for entry in fs::read_dir(&path).expect("historical directory") {
                let entry = entry.expect("historical directory entry");
                visit(
                    root,
                    &relative.join(entry.file_name()),
                    depth + 1,
                    result,
                    total,
                );
            }
        } else {
            assert!(metadata.is_file(), "ordinary files only");
            assert!(
                metadata.len() <= MAX_FILE,
                "bounded historical evidence file"
            );
            let bytes = fs::read(&path).expect("historical evidence bytes");
            *total = total.checked_add(bytes.len()).expect("evidence size");
            assert!(*total <= MAX_TOTAL, "bounded complete historical inventory");
            assert!(result.files.insert(relative.into(), bytes).is_none());
        }
        assert!(
            result.files.len() + result.directories.len() <= MAX_ENTRIES,
            "bounded evidence entry count"
        );
    }
    let mut result = Inventory {
        directories: BTreeSet::new(),
        files: BTreeMap::new(),
    };
    let mut total = 0;
    visit(root, Path::new(""), 0, &mut result, &mut total);
    result
}

fn bytes<'a>(inventory: &'a Inventory, name: &str) -> &'a [u8] {
    inventory
        .files
        .get(Path::new(name))
        .expect("original evidence file")
}

fn json(inventory: &Inventory, name: &str) -> Value {
    serde_json::from_slice(bytes(inventory, name)).expect("original historical JSON")
}

fn check_sentinel(directory: &Path, name: &str, expected: &str) {
    let path = directory.join(name);
    let metadata = fs::symlink_metadata(&path).expect("explicit retained cohort sentinel");
    assert!(metadata.is_file() && !metadata.file_type().is_symlink());
    assert!(metadata.len() <= MAX_FILE);
    assert_eq!(sha256(&fs::read(path).unwrap()), expected);
}

#[test]
#[ignore = "requires explicit LOCALLORE_D07_HISTORICAL_COHORT pointing to the retained original rollout"]
fn genuine_pre_forwarded_cohort_opens_read_only_and_cannot_resume() {
    let directory = PathBuf::from(std::env::var_os(COHORT_ENV).expect(COHORT_ENV));
    assert!(
        directory.is_absolute(),
        "explicit absolute local evidence path"
    );
    // Refuse a mistaken path before enumerating its contents.
    check_sentinel(&directory, "run.json", MANIFEST);
    check_sentinel(&directory, "report.json", REPORT);
    let before = inventory(&directory);
    assert_eq!(sha256(bytes(&before, "run.json")), MANIFEST);
    assert_eq!(sha256(bytes(&before, "report.json")), REPORT);
    assert_eq!(sha256(bytes(&before, "left/synthetic.sqlite")), LEFT_DB);
    assert_eq!(sha256(bytes(&before, "right/synthetic.sqlite")), RIGHT_DB);

    let manifest = json(&before, "run.json");
    assert_eq!(manifest["version"], 2);
    assert_eq!(manifest["kind"], "continuous_rollout");
    assert_eq!(manifest["source_sha256"], SOURCE);
    assert_eq!(manifest["binding"]["source_sha256"], SOURCE);
    assert_eq!(manifest["binding"]["suite_sha256"], SUITE);
    assert_eq!(manifest["binding"]["native"], false);
    assert!(!manifest["binding"]
        .as_object()
        .unwrap()
        .contains_key("forwarded_budget_version"));

    let original_value = json(&before, "report.json");
    let mut original: ComparisonReportV2 =
        serde_json::from_value(original_value.clone()).expect("original report format");
    assert!(
        original.source_matches,
        "original execution matched its own source"
    );
    assert!(original.completed);
    assert_eq!(original.completed_scenes, 4);
    assert_eq!(original.turns.len(), 48);
    assert_eq!(original.turns.iter().filter(|row| row.passed).count(), 22);
    assert_eq!(original.turns.iter().filter(|row| !row.passed).count(), 26);
    assert_eq!(
        original
            .turns
            .iter()
            .filter(|row| row.phase == "committed")
            .count(),
        16
    );
    assert_eq!(
        original.turns.iter().map(|row| row.roles).sum::<usize>(),
        32
    );
    assert_eq!(original.human_reviewed, 0);
    assert!(!original.quality_accepted);
    assert_eq!(original.human_rubric, "not_reviewed");
    let mut captures = 0;
    let mut recordings = 0;
    let mut raw_files = 0;
    for index in 0..24 {
        for (arm_index, arm) in ["left", "right"].into_iter().enumerate() {
            let checkpoint = json(&before, &format!("{arm}/attempt-{index:02}.json"));
            assert_eq!(checkpoint["index"], index);
            assert_eq!(checkpoint["arm"], arm);
            let row = &checkpoint["row"];
            assert_eq!(row, &original_value["turns"][index * 2 + arm_index]);
            assert!(!row
                .as_object()
                .unwrap()
                .contains_key("forwarded_director_estimates"));
            assert!(original.turns[index * 2 + arm_index]
                .forwarded_director_estimates
                .is_none());
            if let Some(name) = checkpoint["capture_file"].as_str() {
                assert_eq!(
                    sha256(bytes(&before, &format!("{arm}/{name}"))),
                    row["capture_sha256"]
                );
                captures += 1;
            }
            if let Some(name) = checkpoint["recording_file"].as_str() {
                let name = format!("{arm}/{name}");
                assert_eq!(sha256(bytes(&before, &name)), row["recording_sha256"]);
                let recording = json(&before, &name);
                for raw in recording["raw"].as_array().unwrap() {
                    let name = format!("{arm}/{}", raw["file"].as_str().unwrap());
                    assert_eq!(sha256(bytes(&before, &name)), raw["sha256"]);
                    assert_eq!(
                        bytes(&before, &name).len() as u64,
                        raw["bytes"].as_u64().unwrap()
                    );
                    raw_files += 1;
                }
                recordings += 1;
            }
        }
    }
    assert_eq!((captures, recordings, raw_files), (32, 32, 32));
    for scene in 0..4 {
        let seal = json(&before, &format!("scene-{scene:02}.json"));
        assert_eq!(seal["scene"], scene);
        assert_eq!(seal["checkpoints"].as_array().unwrap().len(), 12);
        for offset in 0..6 {
            for (arm_index, arm) in ["left", "right"].into_iter().enumerate() {
                let index = scene * 6 + offset;
                let checkpoint = bytes(&before, &format!("{arm}/attempt-{index:02}.json"));
                assert_eq!(
                    sha256(checkpoint),
                    seal["checkpoints"][offset * 2 + arm_index]
                );
            }
        }
    }

    let inspected = inspect_comparison(&directory);
    assert!(
        inventory(&directory) == before,
        "inspection must change no bytes or entries"
    );
    let inspected = inspected.expect("genuine historical cohort remains viewable");
    assert!(!inspected.source_matches);
    // Only current source compatibility changes. Preserve all failures, times,
    // reservations and actual evidence; never fill in missing forwarded estimates.
    original.source_matches = false;
    assert!(
        inspected == original,
        "all original report fields must be exact"
    );

    let resumed = run_comparison(
        &directory,
        true,
        ComparisonKind::ContinuousRollout,
        &Cancellation::default(),
        4,
        LaneFactory::ScriptedBaseline,
        None,
    );
    assert!(
        inventory(&directory) == before,
        "refused resume must not admit or rewrite anything"
    );
    assert_eq!(resumed.unwrap_err(), "CheckpointMismatch");
}
