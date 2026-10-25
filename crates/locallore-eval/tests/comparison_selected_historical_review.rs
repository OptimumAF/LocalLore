// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! One explicit opt-in against the genuine retained 33356 rollout.
//! SOURCE-ONLY, UNCOMPILED/UNRUN at handoff. Never generates, copies, relabels
//! or repairs historical evidence. Tests preparation refusal, not run_selected.
use locallore::inference::Cancellation;
use locallore_eval::{
    local_lane::comparison::{desktop_api, selected},
    memory_comparison::frozen_suite,
};
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::{Path, PathBuf},
};

const COHORT_ENV: &str = "LOCALLORE_D07_HISTORICAL_COHORT";
// Original retained bytes, shared with comparison_historical_readonly.rs.
const MANIFEST: &str = "3e6ff45d65582ff9b65e550210dc0b14ff8a9fbf7d538a878d7f35014b0d668b";
const REPORT: &str = "4167a78bb84ea5cad983d7eb8ff83fb0be1c4e93d4deb019bfac1be05f785a2d";
const LEFT_DB: &str = "0a810374ef2c2f94ef890899a2377a70a90b9d63a83bdf6adc5f87c57e230fa1";
const RIGHT_DB: &str = "8b749d981bd8b1806c6e6a11e2b4b943926344b98f01f9033cfa44fca71e6576";

fn sha256(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

#[derive(PartialEq, Eq)]
struct Inventory {
    directories: BTreeSet<PathBuf>,
    files: BTreeMap<PathBuf, Vec<u8>>,
}

fn inventory(root: &Path) -> Inventory {
    fn visit(root: &Path, relative: &Path, depth: usize, total: &mut usize, out: &mut Inventory) {
        assert!(depth <= 8, "bounded retained evidence depth");
        let path = root.join(relative);
        let metadata = fs::symlink_metadata(&path).unwrap();
        assert!(!metadata.file_type().is_symlink());
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt;
            assert_eq!(
                metadata.file_attributes() & 0x400,
                0,
                "no evidence reparse entries"
            );
        }
        if metadata.is_dir() {
            assert!(out.directories.insert(relative.into()));
            for entry in fs::read_dir(path).unwrap() {
                visit(
                    root,
                    &relative.join(entry.unwrap().file_name()),
                    depth + 1,
                    total,
                    out,
                );
            }
        } else {
            assert!(metadata.is_file() && metadata.len() <= 1024 * 1024);
            let bytes = fs::read(path).unwrap();
            *total = total.checked_add(bytes.len()).unwrap();
            assert!(*total <= 64 * 1024 * 1024);
            assert!(out.files.insert(relative.into(), bytes).is_none());
        }
        assert!(out.directories.len() + out.files.len() <= 1024);
    }
    let mut out = Inventory {
        directories: BTreeSet::new(),
        files: BTreeMap::new(),
    };
    visit(root, Path::new(""), 0, &mut 0, &mut out);
    out
}

fn sentinel(directory: &Path, name: &str, expected: &str) {
    let path = directory.join(name);
    let metadata = fs::symlink_metadata(&path).unwrap();
    assert!(metadata.is_file() && !metadata.file_type().is_symlink());
    assert!(metadata.len() <= 1024 * 1024);
    assert_eq!(sha256(&fs::read(path).unwrap()), expected);
}

#[test]
#[ignore = "requires explicit LOCALLORE_D07_HISTORICAL_COHORT pointing to the genuine retained 33356 rollout"]
fn genuine_historical_reader_binding_cannot_prepare_a_selected_execution() {
    let directory = PathBuf::from(std::env::var_os(COHORT_ENV).expect(COHORT_ENV));
    assert!(
        directory.is_absolute(),
        "explicit retained original cohort only"
    );
    // Refuse a mistaken path before enumerating a complete local inventory.
    sentinel(&directory, "run.json", MANIFEST);
    sentinel(&directory, "report.json", REPORT);
    let before = inventory(&directory);
    assert_eq!(
        sha256(&before.files[Path::new("left/synthetic.sqlite")]),
        LEFT_DB
    );
    assert_eq!(
        sha256(&before.files[Path::new("right/synthetic.sqlite")]),
        RIGHT_DB
    );
    let original_manifest: Value =
        serde_json::from_slice(&before.files[Path::new("run.json")]).unwrap();
    assert!(!original_manifest["binding"]
        .as_object()
        .unwrap()
        .contains_key("forwarded_budget_version"));
    let mut original_report: Value =
        serde_json::from_slice(&before.files[Path::new("report.json")]).unwrap();
    assert_eq!(original_report["source_matches"], true);
    assert_eq!(original_report["completed"], true);
    assert_eq!(original_report["completed_scenes"], 4);
    assert_eq!(original_report["turns"].as_array().unwrap().len(), 48);
    assert!(!original_report["turns"][0]
        .as_object()
        .unwrap()
        .contains_key("forwarded_director_estimates"));
    let opened = desktop_api::open_read_only(&directory).unwrap();
    let summary = desktop_api::summary(&opened, true).unwrap();
    assert_eq!(summary["read_only"], true);
    assert_eq!(summary["report"]["source_matches"], false);
    // Only the current compatibility flag changes; old failures, timings,
    // provenance and absent measurements remain the original report values.
    original_report["source_matches"] = Value::Bool(false);
    assert!(
        summary["report"] == original_report,
        "preserve all historical report fields"
    );
    let corpus = frozen_suite().unwrap();
    let turn = corpus.steps()[0].id();
    for arm in ["left", "right"] {
        assert!(summary["rows"]
            .as_array()
            .unwrap()
            .iter()
            .any(|row| row["row"]["turn"] == turn && row["row"]["arm"] == arm));
    }
    let binding = summary["binding"].as_str().unwrap().to_owned();
    assert_eq!(binding.len(), 64);
    drop(opened); // No locked run.lock reads or reader-token promotion.
    assert!(
        inventory(&directory) == before,
        "reader preserves all original bytes and directories"
    );
    let result = selected::prepare_selected(
        &directory,
        &binding,
        &desktop_api::RowId {
            turn: turn.into(),
            arm: desktop_api::Arm::Left,
        },
        selected::SelectedIntent {
            client_id: "historical-selected-refusal".into(),
            lane: selected::SelectedLane::ScriptedBaseline,
        },
        &Cancellation::default(),
    );
    match result {
        Err(error) => assert_eq!(error, "SourceMismatch"),
        Ok(plan) => {
            drop(plan);
            panic!("historical source unexpectedly admitted selected preparation");
        }
    }
    assert!(
        inventory(&directory) == before,
        "refusal preserves the complete source inventory"
    );
    sentinel(&directory, "run.json", MANIFEST);
    sentinel(&directory, "report.json", REPORT);
    // No execution/destination/provider-count assertion: this public entry only
    // prepares and must refuse before returning an executable capability.
}
