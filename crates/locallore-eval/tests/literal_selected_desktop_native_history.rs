// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen SOURCE ONLY / UNCOMPILED / UNRUN by author. Explicit genuine retained
//! artifact only; no feature gate, generated substitute, model or source opening.
use locallore::{engine::Engine, inspection_query::{self, Observer, Query, View, MAX_ROWS}};
use locallore_eval::{local_lane::comparison::{desktop_api::{Arm, Edge, EvidenceRequest},
    literal_v3::selected_v2::desktop_read}, memory_comparison::frozen_suite,
    memory_comparison_v3::arm_descriptors};
use locallore_storage::Store;
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::{collections::{BTreeMap, BTreeSet}, fs, path::{Path, PathBuf}};

type Inventory = BTreeMap<PathBuf, Option<(u64, String)>>;
const RUN_BINDING: &str = "e2a24574d735141a2e1e178f3b5f2a9d77de02146cf8175a198b083dd29e9dec";
fn inventory(root: &Path) -> Inventory {
    fn visit(root: &Path, path: &Path, depth: usize, total: &mut usize, out: &mut Inventory) {
        assert!(depth <= 10 && out.len() < 8192);
        let m = fs::symlink_metadata(path).unwrap();
        assert!(!m.file_type().is_symlink());
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt;
            assert_eq!(m.file_attributes() & 0x400, 0);
        }
        let relative = path.strip_prefix(root).unwrap().to_owned();
        if m.is_dir() {
            out.insert(relative, None);
            for entry in fs::read_dir(path).unwrap() {
                visit(root, &entry.unwrap().path(), depth + 1, total, out);
            }
        } else {
            assert!(m.is_file() && m.len() <= 8 * 1024 * 1024);
            let bytes = fs::read(path).unwrap();
            *total = total.checked_add(bytes.len()).unwrap();
            assert!(*total <= 128 * 1024 * 1024);
            out.insert(relative, Some((m.len(), format!("{:x}", Sha256::digest(&bytes)))));
        }
    }
    let mut result = Inventory::new();
    visit(root, root, 0, &mut 0, &mut result);
    result
}
fn exact_keys(value: &Value, names: &[&str]) {
    let actual: BTreeSet<_> = value.as_object().unwrap().keys().map(String::as_str).collect();
    assert_eq!(actual, names.iter().copied().collect());
}
fn refused<T>(result: Result<T, String>) -> String {
    match result { Err(error) => error, Ok(_) => panic!("expected access denial") }
}
fn actual_engine(root: &Path, arm: &str) -> Engine {
    let databases: Vec<_> = fs::read_dir(root.join(arm)).unwrap().map(|e| e.unwrap().path())
        .filter(|p| p.extension().is_some_and(|e| e == "sqlite")).collect();
    assert_eq!(databases.len(), 1);
    Store::open_read_only(&databases[0]).unwrap().resume(&frozen_suite().unwrap().seed().scope).unwrap().engine
}

#[test]
#[ignore = "explicit genuine LOCALLORE_LITERAL_SELECTED_NATIVE_HISTORY required; read-only Root opt-in"]
fn genuine_native_selected2_capability_preserves_privacy_and_all_retained_bytes() {
    let root = PathBuf::from(std::env::var_os("LOCALLORE_LITERAL_SELECTED_NATIVE_HISTORY")
        .expect("explicit genuine retained native selected2 target required"));
    assert!(root.is_absolute() && root.is_dir());
    let before = inventory(&root);
    for (name, expected) in [
        ("selected.json", "96e0c6e860650e247fa667f5b838bd96c84f9a899bbf16f4ace29351ee971eca"),
        ("report.json", "c356d4f85a6b3170148c85fea36f113a4670258b64912e678a5239567ff804d8"),
    ] {
        assert_eq!(before[Path::new(name)].as_ref().unwrap().1, expected);
    }
    // Wrong-fixture pins detect substitution/drift, not authenticated origin.
    let engines = [actual_engine(&root, "left"), actual_engine(&root, "right")];
    assert!(before.keys().any(|p| p.starts_with("left") && p.file_name().is_some_and(|n| n.to_string_lossy().starts_with("raw-"))));
    let cap = desktop_read::open_read_only(&root).unwrap();
    assert_eq!(refused(desktop_read::summary(&cap, false)), "Forbidden");
    let metadata = desktop_read::summary(&cap, true).unwrap();
    exact_keys(&metadata, &["version", "kind", "source_protocol_version", "constructions", "binding",
        "selection", "lane", "arms", "read_only", "execution_available"]);
    assert_eq!(metadata["version"], 2);
    assert_eq!(metadata["kind"], "selected_read");
    assert_eq!(metadata["source_protocol_version"], 3);
    assert_eq!(metadata["constructions"], serde_json::to_value(arm_descriptors()).unwrap());
    assert_eq!(metadata["lane"], "native_selected_case");
    assert_eq!(metadata["read_only"], true);
    assert_eq!(metadata["execution_available"], false);
    let binding = metadata["binding"].as_str().unwrap();
    assert_eq!(binding.len(), 64);
    assert!(binding.bytes().all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b)));
    assert_ne!(binding, RUN_BINDING, "read snapshot seal is not the execution/run binding");
    exact_keys(&metadata["selection"], &["turn", "clicked_arm", "index"]);
    assert_eq!(metadata["selection"]["turn"], "courier-05");
    let arms = metadata["arms"].as_array().unwrap();
    assert_eq!(arms.len(), 2);
    for arm in arms {
        exact_keys(arm, &["arm", "scope", "before_head", "after_head", "available"]);
        assert_eq!(arm["available"], true);
    }
    for observer in [Observer::Player, Observer::Character { id: "mira".into() }, Observer::Character { id: "sable".into() }] {
        assert_eq!(refused(desktop_read::diagnostics(&cap, "bad-binding", observer.clone(), true)), "Forbidden");
        for arm in [Arm::Left, Arm::Right] {
            for request in [EvidenceRequest::Receipt { observer: observer.clone() },
                EvidenceRequest::Capture { observer: observer.clone() }, EvidenceRequest::Outputs { observer: observer.clone() }] {
                assert_eq!(refused(desktop_read::evidence(&cap, "bad-binding", arm, request, true)), "Forbidden");
            }
        }
    }
    let diagnostics = desktop_read::diagnostics(&cap, binding, Observer::Omniscient, true).unwrap();
    assert_eq!(diagnostics["version"], 2);
    assert_eq!(diagnostics["source_protocol_version"], 3);
    assert_eq!(diagnostics["physical_setups"], 1);
    assert_eq!(diagnostics["human_reviewed"], 0);
    assert_eq!(diagnostics["quality_accepted"], false);
    let rows = diagnostics["rows"].as_array().unwrap();
    assert_eq!(rows.len(), 2);
    for (index, (arm, name, expected_sha)) in [
        (Arm::Left, "left", "51d5adae2dc67d653d2d9509094b5528caa8484955594a028c184fe48061a324"),
        (Arm::Right, "right", "1822994b79651b1648eb8b1257c6f6daf004e39323031174b7ce52516ae252ce"),
    ].into_iter().enumerate() {
        let row = rows.iter().find(|row| row["arm"] == name).unwrap();
        assert_eq!(row["turn"], "courier-05");
        assert_eq!(row["phase"], "committed");
        assert_eq!(row["actual_receipt_sha256"], expected_sha);
        assert_eq!(row["roles"], if index == 0 { 0 } else { 2 });
        assert_eq!(row["roles_known"], index == 1);
        assert_eq!(row["passed"], index == 1);
        assert_eq!(row["construction_evidence_status"], if index == 0 { "unavailable" } else { "validated_relevant" });
        let source = arms.iter().find(|source| source["arm"] == name).unwrap();
        for (edge, key) in [(Edge::Before, "before_head"), (Edge::After, "after_head")] {
            let cut = engines[index].at_revision(source[key].as_u64().unwrap()).unwrap();
            for observer in [Observer::Player, Observer::Character { id: "mira".into() }, Observer::Character { id: "sable".into() }] {
                let expected = inspection_query::query(&cut, &Query { version: 2, scope: cut.scope().clone(),
                    expected_head: cut.revision(), at_revision: None, observer: observer.clone(), view: View::Knowledge,
                    cursor: None, limit: MAX_ROWS, search: String::new() }, true).unwrap();
                let actual = desktop_read::evidence(&cap, binding, arm,
                    EvidenceRequest::Query { edge, observer: observer.clone(), view: View::Knowledge }, true).unwrap();
                assert_eq!(actual["body"]["page"], serde_json::to_value(expected).unwrap());
                if matches!(observer, Observer::Character { .. }) {
                    assert!(!actual["body"]["page"].to_string().contains("SECRET-TIDE-731"));
                }
            }
        }
        let receipt = desktop_read::evidence(&cap, binding, arm,
            EvidenceRequest::Receipt { observer: Observer::Omniscient }, true).unwrap();
        assert_eq!(receipt["body"]["kind"], "receipt");
        let actual_receipt = engines[index].receipts().iter().find(|r| r.request().turn == "courier-05").unwrap();
        assert_eq!(receipt["body"]["receipt"], serde_json::to_value(actual_receipt).unwrap());
        for (request, kind, missing) in [
            (EvidenceRequest::Capture { observer: Observer::Omniscient }, "capture", "capture_unavailable"),
            (EvidenceRequest::Outputs { observer: Observer::Omniscient }, "outputs", "recording_unavailable"),
        ] {
            let reply = desktop_read::evidence(&cap, binding, arm, request, true).unwrap();
            if index == 0 {
                assert_eq!(reply["body"]["kind"], "missing");
                assert_eq!(reply["body"]["reason"], missing);
            } else {
                assert_eq!(reply["body"]["kind"], kind);
                if kind == "outputs" {
                    let outputs = reply["body"]["outputs"].as_array().unwrap();
                    assert_eq!(outputs.len(), 2);
                    for output in outputs {
                        assert_eq!(output["sha256"].as_str().unwrap().len(), 64);
                        assert!(output["bytes"].as_u64().unwrap() > 0);
                    }
                } else { assert!(reply["body"]["capture"].is_object()); }
            }
        }
    }
    drop(cap);
    assert!(inventory(&root) == before);
    let reopened = desktop_read::open_read_only(&root).unwrap();
    assert_eq!(desktop_read::summary(&reopened, true).unwrap(), metadata);
    assert_eq!(desktop_read::diagnostics(&reopened, binding, Observer::Omniscient, true).unwrap(), diagnostics);
    drop(reopened);
    assert!(inventory(&root) == before);
}
