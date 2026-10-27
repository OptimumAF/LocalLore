// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen SOURCE ONLY / UNCOMPILED / UNRUN by author. The coordinator supplies
//! the genuine retained fixture explicitly; no fixture copy/relabel/generation.
//! Keep this test available WITHOUT local-model as well as WITH local-model.
use locallore_eval::{
    local_lane::comparison::literal_v3::selected_v2, memory_comparison_v3::arm_descriptors,
};
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::{
    collections::BTreeMap,
    fs,
    path::{Path, PathBuf},
};

type Inventory = BTreeMap<PathBuf, Option<(u64, String)>>;
const MANIFEST_SHA: &str = "96e0c6e860650e247fa667f5b838bd96c84f9a899bbf16f4ace29351ee971eca";
const REPORT_SHA: &str = "c356d4f85a6b3170148c85fea36f113a4670258b64912e678a5239567ff804d8";
const BINDING: &str = "e2a24574d735141a2e1e178f3b5f2a9d77de02146cf8175a198b083dd29e9dec";
const SOURCE_BINDING: &str = "e1d64c4ae499592f4cf62ced6564bd69d9dd8b71b612d46f6c4f41a7048e8f8d";
const SOURCE_SHA: &str = "f294964ed00d5455b85b5e3c9c4dbd116f523a8657d1201fc94178300f834795";

fn inventory(root: &Path) -> Inventory {
    fn visit(root: &Path, path: &Path, depth: usize, total: &mut usize, out: &mut Inventory) {
        assert!(depth <= 10 && out.len() < 8192);
        let metadata = fs::symlink_metadata(path).unwrap();
        assert!(!metadata.file_type().is_symlink());
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt;
            assert_eq!(
                metadata.file_attributes() & 0x400,
                0,
                "no reparse fixture entries"
            );
        }
        let relative = path.strip_prefix(root).unwrap().to_owned();
        if metadata.is_dir() {
            out.insert(relative, None);
            for entry in fs::read_dir(path).unwrap() {
                visit(root, &entry.unwrap().path(), depth + 1, total, out);
            }
        } else {
            assert!(metadata.is_file() && metadata.len() <= 8 * 1024 * 1024);
            let bytes = fs::read(path).unwrap();
            *total = total.checked_add(bytes.len()).unwrap();
            assert!(*total <= 128 * 1024 * 1024);
            out.insert(
                relative,
                Some((metadata.len(), format!("{:x}", Sha256::digest(&bytes)))),
            );
        }
    }
    let mut result = Inventory::new();
    visit(root, root, 0, &mut 0, &mut result);
    result
}
fn file_sha<'a>(inventory: &'a Inventory, name: &str) -> &'a str {
    &inventory.get(Path::new(name)).unwrap().as_ref().unwrap().1
}
fn assert_identity(report: &Value) {
    assert_eq!(report["version"], 2);
    assert_eq!(report["source_protocol_version"], 3);
    assert_eq!(report["lane"], "native_selected_case");
    assert_eq!(
        report["source_native"], false,
        "genuine source was scripted V3, not native"
    );
    assert_eq!(report["binding"], BINDING);
    assert_eq!(report["source_binding"], SOURCE_BINDING);
    assert_eq!(report["source_sha256"], SOURCE_SHA);
    assert_eq!(
        report["arms"],
        serde_json::to_value(arm_descriptors()).unwrap()
    );
    assert_eq!(report["completed"], true);
    assert_eq!(report["human_reviewed"], 0);
    assert_eq!(report["quality_accepted"], false);
    assert_eq!(report["physical_setups"], 1);
    let loads = report["native_load"].as_array().unwrap();
    assert_eq!(loads.len(), 1);
    assert!(loads[0].is_object());
    assert!(report["physical_setup_ms"].is_u64());
    let rows = report["rows"].as_array().unwrap();
    assert_eq!(rows.len(), 2);
    let left = rows.iter().find(|row| row["arm"] == "left").unwrap();
    let right = rows.iter().find(|row| row["arm"] == "right").unwrap();
    for row in [left, right] {
        assert_eq!(row["turn"], "courier-05");
        assert_eq!(row["phase"], "committed");
    }
    assert_eq!(left["recovered_without_checkpoint"], true);
    assert_eq!(left["roles"], 0);
    assert_eq!(left["roles_known"], false);
    assert_eq!(left["passed"], false);
    assert_eq!(left["construction_evidence_status"], "unavailable");
    assert_eq!(left["context_evidence_available"], false);
    assert_eq!(
        left["actual_receipt_sha256"],
        "51d5adae2dc67d653d2d9509094b5528caa8484955594a028c184fe48061a324"
    );
    assert_eq!(right["recovered_without_checkpoint"], false);
    assert_eq!(right["roles"], 2);
    assert_eq!(right["roles_known"], true);
    assert_eq!(right["passed"], true);
    assert_eq!(right["construction_evidence_status"], "validated_relevant");
    assert_eq!(
        right["actual_receipt_sha256"],
        "1822994b79651b1648eb8b1257c6f6daf004e39323031174b7ce52516ae252ce"
    );
    // These are retained row diagnostics, not two new calls or zero historical
    // work on the recovered side. Original four-role measurement is elsewhere.
    assert_eq!(
        rows.iter()
            .map(|row| row["roles"].as_u64().unwrap())
            .sum::<u64>(),
        2
    );
}

#[test]
#[ignore = "requires explicit genuine retained LOCALLORE_LITERAL_SELECTED_NATIVE_HISTORY; read-only Root opt-in"]
fn genuine_native_selected2_cold_inspection_is_feature_independent_and_byte_preserving() {
    let root = PathBuf::from(
        std::env::var_os("LOCALLORE_LITERAL_SELECTED_NATIVE_HISTORY")
            .expect("explicit genuine native selected2 history path required"),
    );
    assert!(root.is_absolute() && root.is_dir());
    let before = inventory(&root);
    // Wrong-fixture pins detect accidental substitution, not authenticated origin.
    assert_eq!(file_sha(&before, "selected.json"), MANIFEST_SHA);
    assert_eq!(file_sha(&before, "report.json"), REPORT_SHA);
    let stored: Value =
        serde_json::from_slice(&fs::read(root.join("report.json")).unwrap()).unwrap();
    assert_identity(&stored);
    for _ in 0..2 {
        // Public inspection fully returns/drops locks before inventory reads.
        // No source directory, asset callback, runtime or execution API is used.
        let inspected =
            serde_json::to_value(selected_v2::inspect_selected(&root).unwrap()).unwrap();
        assert_eq!(inspected, stored);
        assert_identity(&inspected);
        assert!(
            inventory(&root) == before,
            "read changed the genuine retained target inventory"
        );
    }
}
