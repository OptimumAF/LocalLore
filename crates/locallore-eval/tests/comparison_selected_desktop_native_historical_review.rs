// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! SOURCE ONLY / UNCOMPILED / UNRUN. Explicit genuine retained approved-native
//! Move4 target, never generated/copied/relabelled here. Read capability only;
//! no model assets, factory, reservation, execution, repair or native UI API.
use locallore::{
    contracts::Request,
    inspection_query::{self, Observer, Query, Row, View, MAX_ROWS},
};
use locallore_eval::local_lane::comparison::{
    desktop_api::{Arm, Edge, EvidenceRequest},
    selected::desktop_read,
};
use locallore_storage::Store;
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::{Path, PathBuf}};

const HISTORY_ENV: &str = "LOCALLORE_SELECTED_NATIVE_HISTORY";
type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;

fn inventory(root: &Path) -> Inventory {
    fn visit(root: &Path, path: &Path, depth: usize, total: &mut usize, out: &mut Inventory) {
        assert!(depth <= 8 && out.len() < 1024);
        let metadata = fs::symlink_metadata(path).unwrap();
        assert!(!metadata.file_type().is_symlink());
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt;
            assert_eq!(metadata.file_attributes() & 0x400, 0, "no retained reparse entries");
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
fn bounded_json(path: &Path, cap: u64) -> Value {
    let metadata = fs::symlink_metadata(path).unwrap();
    assert!(metadata.is_file() && !metadata.file_type().is_symlink() && metadata.len() <= cap);
    serde_json::from_slice(&fs::read(path).unwrap()).unwrap()
}
fn database(directory: &Path) -> PathBuf {
    let mut databases = Vec::new();
    for (count, entry) in fs::read_dir(directory).unwrap().enumerate() {
        assert!(count < 512);
        let path = entry.unwrap().path();
        if path.extension().is_some_and(|extension| extension == "sqlite") {
            databases.push(path);
        }
    }
    assert_eq!(databases.len(), 1, "actual isolated selected arm has one canonical Store");
    databases.pop().unwrap()
}
fn keys(value: &Value) -> Vec<&str> {
    value.as_object().unwrap().keys().map(String::as_str).collect()
}
fn digest(value: &Value) -> String {
    Sha256::digest(serde_json::to_vec(value).unwrap()).iter().map(|byte| format!("{byte:02x}")).collect()
}

#[test]
#[ignore = "requires explicit LOCALLORE_SELECTED_NATIVE_HISTORY naming genuine prior approved-native completed Move4 target; no assets/execution"]
fn genuine_native_selected_read_cap_matches_store_query2_and_raw_evidence_twice_without_writes() {
    let directory = PathBuf::from(std::env::var_os(HISTORY_ENV).expect(HISTORY_ENV));
    assert!(directory.is_absolute(), "explicit genuine retained target only");
    let original = inventory(&directory);
    let manifest = bounded_json(&directory.join("selected.json"), 128 * 1024);
    assert_eq!(manifest["version"], 1);
    assert_eq!(manifest["run_type"], "selected_case");
    assert_eq!(manifest["lane"], "native_selected_case");
    assert_eq!(manifest["selection"]["index"], 4);
    assert_eq!(manifest["profile"]["id"], "qwen3-0.6b-q8-cpu-v1");
    assert_eq!(manifest["source_inputs"].as_array().unwrap().len(), 2);

    let mut first_summary = None;
    let mut first_evidence = None;
    for _repeat in 0..2 {
        let mut evidence = Vec::new();
        let mut saw_actual_capture = false;
        {
            let opened = desktop_read::open_read_only(&directory).expect("genuine completed selected read capability");
            assert_eq!(desktop_read::summary(&opened, false).unwrap_err(), "Forbidden");
            let summary = desktop_read::summary(&opened, true).unwrap();
            assert_eq!(keys(&summary), ["arms", "binding", "execution_available", "kind", "lane", "read_only", "selection", "version"]);
            assert_eq!(summary["version"], 1);
            assert_eq!(summary["kind"], "selected_read");
            assert_eq!(summary["lane"], "native_selected_case");
            assert_eq!(summary["read_only"], true);
            assert_eq!(summary["execution_available"], false);
            assert!(summary["selection"] == manifest["selection"]);
            assert_eq!(keys(&summary["selection"]), ["clicked_arm", "index", "turn"]);
            let binding = summary["binding"].as_str().unwrap();
            assert!(binding.len() == 64 && binding.bytes().all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase()));
            assert_eq!(summary["arms"].as_array().unwrap().len(), 2);

            for (index, (name, arm)) in [("left", Arm::Left), ("right", Arm::Right)].into_iter().enumerate() {
                let request: Request = serde_json::from_value(manifest["source_inputs"][index]["request"].clone()).unwrap();
                let path = database(&directory.join(name));
                let mut store = Store::open_read_only(&path).unwrap();
                let full = store.resume(&request.scope).unwrap().engine;
                let receipt = store.lookup_turn(&request.scope, &request.turn).unwrap().receipt.expect("actual native committed receipt");
                assert!(receipt.request() == &request, "actual full Request, not reported row identity alone");
                assert!(receipt.play().is_some(), "genuine accepted Play metadata");
                assert_eq!(full.domain_version(), 1);
                assert!(full.state().actors.contains_key("sable"));
                let before_head = manifest["source_inputs"][index]["before_head"].as_u64().unwrap();
                let after_head = full.revision();
                assert!(after_head > before_head);
                let metadata = &summary["arms"][index];
                assert_eq!(keys(metadata), ["after_head", "arm", "available", "before_head", "scope"]);
                assert_eq!(metadata["arm"], name);
                assert_eq!(metadata["available"], true);
                assert_eq!(metadata["before_head"], before_head);
                assert_eq!(metadata["after_head"], after_head);
                assert!(metadata["scope"] == serde_json::to_value(&request.scope).unwrap());
                let before = full.at_revision(before_head).unwrap();
                let after = full.at_revision(after_head).unwrap();

                for observer in [Observer::Player, Observer::Character { id: "sable".into() }] {
                    for (edge, edge_name, cut) in [(Edge::Before, "before", &before), (Edge::After, "after", &after)] {
                        for view in [View::History, View::Knowledge] {
                            let expected = inspection_query::query(cut, &Query {
                                version: 2, scope: cut.scope().clone(), expected_head: cut.revision(),
                                at_revision: None, observer: observer.clone(), view,
                                cursor: None, limit: MAX_ROWS, search: String::new(),
                            }, true).unwrap();
                            assert_eq!(expected.head, cut.revision());
                            assert_eq!(expected.revision, cut.revision());
                            if matches!(observer, Observer::Character { .. }) {
                                assert!(expected.rows.iter().all(|row| !matches!(row, Row::Message { .. } | Row::ScopedMessage { .. })), "NPC history excludes player input and whole narration");
                            }
                            let actual = desktop_read::evidence(&opened, binding, arm, EvidenceRequest::Query { edge, observer: observer.clone(), view }, true).unwrap();
                            assert_eq!(actual["binding"], binding);
                            assert_eq!(actual["row"]["turn"], request.turn);
                            assert_eq!(actual["row"]["arm"], name);
                            assert_eq!(actual["edge"], edge_name);
                            assert_eq!(actual["read_only"], true);
                            assert_eq!(actual["generation_grant"], false);
                            assert_eq!(actual["body"]["kind"], "query");
                            assert!(actual["body"]["page"] == serde_json::to_value(expected).unwrap(), "reader page equals actual Core Query2 over the exact immutable Store edge");
                            evidence.push(actual);
                        }
                    }
                    // Actor raw denial also precedes even a deliberately stale binding.
                    for raw in [EvidenceRequest::Receipt { observer: observer.clone() }, EvidenceRequest::Capture { observer }] {
                        assert_eq!(desktop_read::evidence(&opened, "stale-binding", arm, raw, true).unwrap_err(), "Forbidden");
                    }
                }

                let raw = desktop_read::evidence(&opened, binding, arm, EvidenceRequest::Receipt { observer: Observer::Omniscient }, true).unwrap();
                assert_eq!(raw["body"]["kind"], "receipt");
                assert!(raw["body"]["receipt"] == serde_json::to_value(&receipt).unwrap(), "raw receipt is the actual validated Store result");
                assert_eq!(raw["generation_grant"], false);
                evidence.push(raw);

                let checkpoint = bounded_json(&directory.join(name).join("attempt-04.json"), 256 * 1024);
                let capture = desktop_read::evidence(&opened, binding, arm, EvidenceRequest::Capture { observer: Observer::Omniscient }, true).unwrap();
                if checkpoint["capture_file"].is_null() {
                    assert_eq!(capture["body"]["kind"], "missing");
                    assert_eq!(capture["body"]["reason"], "capture_unavailable");
                } else {
                    assert_eq!(capture["body"]["kind"], "capture");
                    assert_eq!(digest(&capture["body"]["capture"]), checkpoint["row"]["capture_sha256"].as_str().unwrap());
                    saw_actual_capture = true;
                }
                assert_eq!(capture["generation_grant"], false);
                evidence.push(capture);
            }
            assert!(saw_actual_capture, "genuine retained Move target preserves at least one original native capture; recovered missing captures stay honest");
            if let Some(previous) = &first_summary {
                assert!(*previous == summary, "identical reopened source metadata/binding");
            } else {
                first_summary = Some(summary);
            }
        } // Drop the opaque run.lock capability and every Store before inventory.
        assert!(inventory(&directory) == original, "read capability changed retained source bytes/directories");
        if let Some(previous) = &first_evidence {
            assert!(*previous == evidence, "repeat evidence is stable under the same validated source");
        } else {
            first_evidence = Some(evidence);
        }
    }
}
