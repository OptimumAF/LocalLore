// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Opt-in reader against a genuine retained native selected target, never generated here.
//! SOURCE ONLY / UNCOMPILED / UNRUN at handoff. Run independently without features
//! and with local-model. No assets, factory, reservation, execution or repair API.
//! Genuine producer provenance is supplied by the coordinator, not authenticated
//! by a native lane label or report hashes. No model/GUI/device quality claim.
use locallore::{context_compiler::ContextPolicy, contracts::Request, play::PlayProfile};
use locallore_eval::{local_lane::comparison::selected, memory_comparison_v2::TurnReportV2};
use serde_json::Value;
use std::{
    collections::BTreeMap,
    fs,
    path::{Path, PathBuf},
};

const HISTORY_ENV: &str = "LOCALLORE_SELECTED_NATIVE_HISTORY";
const HISTORICAL_PROFILE: &str = "qwen3-0.6b-q8-cpu-v1";
type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;

fn inventory(root: &Path) -> Inventory {
    fn visit(root: &Path, path: &Path, depth: usize, total: &mut usize, out: &mut Inventory) {
        assert!(
            depth <= 8 && out.len() < 1024,
            "bounded retained target inventory"
        );
        let metadata = fs::symlink_metadata(path).unwrap();
        assert!(!metadata.file_type().is_symlink());
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt;
            assert_eq!(
                metadata.file_attributes() & 0x400,
                0,
                "no retained reparse entries"
            );
        }
        let relative = path.strip_prefix(root).unwrap().to_owned();
        if metadata.is_dir() {
            assert!(out.insert(relative, None).is_none());
            for entry in fs::read_dir(path).unwrap() {
                visit(root, &entry.unwrap().path(), depth + 1, total, out);
            }
        } else {
            assert!(metadata.is_file() && metadata.len() <= 8 * 1024 * 1024);
            let bytes = fs::read(path).unwrap();
            *total = total.checked_add(bytes.len()).unwrap();
            assert!(*total <= 64 * 1024 * 1024);
            assert!(out.insert(relative, Some(bytes)).is_none());
        }
    }
    let mut out = BTreeMap::new();
    visit(root, root, 0, &mut 0, &mut out);
    out
}

fn hex(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
}

#[test]
#[ignore = "requires explicit LOCALLORE_SELECTED_NATIVE_HISTORY naming a genuine retained native selected target"]
fn genuine_native_selected_history_is_readable_without_execution_or_any_byte_change() {
    let directory = PathBuf::from(std::env::var_os(HISTORY_ENV).expect(HISTORY_ENV));
    assert!(
        directory.is_absolute(),
        "explicit genuine retained target only"
    );
    let manifest_path = directory.join("selected.json");
    let metadata = fs::symlink_metadata(&manifest_path).unwrap();
    assert!(metadata.is_file() && !metadata.file_type().is_symlink());
    assert!(metadata.len() <= 128 * 1024);
    let manifest: Value = serde_json::from_slice(&fs::read(&manifest_path).unwrap()).unwrap();
    assert_eq!(manifest["version"], 1);
    assert_eq!(manifest["run_type"], "selected_case");
    assert_eq!(manifest["lane"], "native_selected_case");
    assert_eq!(manifest["profile"]["id"], HISTORICAL_PROFILE);

    // The explicit cohort must be finished by its producer. Neither call keeps
    // a read capability alive when complete inventories (including run.lock)
    // are examined; these public results are serialized data, not execution grants.
    let before = inventory(&directory);
    let first = {
        let report =
            selected::inspect_selected(&directory).expect("genuine retained native history");
        serde_json::to_vec(&report).unwrap()
    };
    assert!(first.len() <= 2 * 1024 * 1024);
    assert!(
        inventory(&directory) == before,
        "first read changed retained evidence"
    );
    let second = {
        let report = selected::inspect_selected(&directory).expect("same retained native history");
        serde_json::to_vec(&report).unwrap()
    };
    assert_eq!(first, second, "complete serialized reports must match");
    assert!(
        inventory(&directory) == before,
        "second read changed retained evidence"
    );

    let report: Value = serde_json::from_slice(&first).unwrap();
    assert_eq!(report["version"], 1);
    assert_eq!(report["source_protocol_version"], 2);
    assert_eq!(report["run_type"], "selected_case");
    assert_eq!(report["lane"], "native_selected_case");
    for key in ["binding", "source_binding", "suite_sha256", "source_sha256"] {
        assert!(hex(report[key].as_str().unwrap()));
        assert!(report[key] == manifest[key]);
    }
    assert!(report["profile"] == manifest["profile"]);
    assert!(report["source_profile"] == manifest["source_profile"]);
    assert!(report["selection"] == manifest["selection"]);
    assert!(report["source_inputs"] == manifest["source_inputs"]);
    let profile: PlayProfile = serde_json::from_value(report["profile"].clone()).unwrap();
    profile.validate().unwrap(); // Structural historical profile, not current asset approval.
    assert_eq!(profile.id, HISTORICAL_PROFILE);
    assert_eq!(report["human_reviewed"], 0);
    assert_eq!(report["human_rubric"], "not_reviewed");
    assert_eq!(report["quality_accepted"], false);

    let measured = report["physical_setups"].as_u64().unwrap();
    assert!(measured > 0 && measured <= 32);
    assert!(report["physical_setup_ms"].as_u64().is_some());
    let load = report["native_load"]
        .as_array()
        .expect("retained measured load entries");
    assert_eq!(load.len() as u64, measured);
    assert!(load.iter().any(|metrics| {
        metrics.as_object().is_some_and(|fields| {
            fields.len() == 9
                && metrics["load_ms"]
                    .as_f64()
                    .is_some_and(|ms| ms.is_finite() && ms >= 0.0)
                && metrics["model_loads"]
                    .as_u64()
                    .is_some_and(|count| count > 0)
        })
    }));

    let inputs = report["source_inputs"].as_array().unwrap();
    assert_eq!(inputs.len(), 2);
    let mut requests = BTreeMap::new();
    for (index, arm) in ["left", "right"].into_iter().enumerate() {
        let input = &inputs[index];
        assert_eq!(input["arm"], arm);
        let request: Request = serde_json::from_value(input["request"].clone()).unwrap();
        assert_eq!(request.version, 1);
        assert_eq!(request.turn, report["selection"]["turn"].as_str().unwrap());
        assert_eq!(
            request.expected_revision,
            input["before_head"].as_u64().unwrap()
        );
        assert!(serde_json::to_value(&request.scope).unwrap() == input["scope"]);
        assert!(hex(input["prefix_sha256"].as_str().unwrap()));
        assert!(hex(input["input_semantic_sha256"].as_str().unwrap()));
        requests.insert(arm, request);
    }
    let rows: Vec<TurnReportV2> = serde_json::from_value(report["rows"].clone()).unwrap();
    assert!(!rows.is_empty() && rows.len() <= 2);
    let mut seen = std::collections::BTreeSet::new();
    for row in &rows {
        assert!(seen.insert(row.arm.as_str()));
        let index = match row.arm.as_str() {
            "left" => 0,
            "right" => 1,
            _ => panic!("unknown retained arm"),
        };
        assert_eq!(row.turn, requests[row.arm.as_str()].turn);
        assert_eq!(
            row.input_semantic_sha256,
            inputs[index]["input_semantic_sha256"].as_str().unwrap()
        );
        assert_eq!(
            row.policy,
            if index == 0 {
                ContextPolicy::StateRecentTranscriptV1
            } else {
                ContextPolicy::StateRelevantMemoryV1
            }
        );
        if let Some(receipt) = &row.actual_receipt_sha256 {
            assert!(hex(receipt));
        }
    }
    assert!(
        rows.iter().any(|row| {
            row.phase == "committed" && row.actual_receipt_sha256.as_deref().is_some_and(hex)
        }),
        "at least one actual committed receipt, not just a native label"
    );
    assert_eq!(report["completed"].as_bool().unwrap(), rows.len() == 2);
    // Recovered lost-checkpoint rows can retain unknown roles/timings and failed
    // quality checks. Never require all rows to pass or invent missing metrics.
    assert!(
        inventory(&directory) == before,
        "validation changed original evidence"
    );
}
