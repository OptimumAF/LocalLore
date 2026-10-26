// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Genuine private native3 artifacts, read only. No model/process/render run.
use locallore::inspection_query::Observer;
use locallore_eval::local_lane::comparison::{
    desktop_api::{Arm, EvidenceRequest, RowId},
    literal_v3::desktop_api,
};
use sha2::{Digest, Sha256};
use std::{
    collections::BTreeMap,
    fs,
    path::{Path, PathBuf},
};

fn inventory(root: &Path) -> BTreeMap<PathBuf, Option<Vec<u8>>> {
    fn visit(
        root: &Path,
        path: &Path,
        depth: usize,
        total: &mut usize,
        out: &mut BTreeMap<PathBuf, Option<Vec<u8>>>,
    ) {
        assert!(depth <= 10 && out.len() < 8192);
        let meta = fs::symlink_metadata(path).unwrap();
        assert!(!meta.file_type().is_symlink());
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt;
            assert_eq!(meta.file_attributes() & 0x400, 0);
        }
        let relative = path.strip_prefix(root).unwrap().to_owned();
        if meta.is_dir() {
            out.insert(relative, None);
            for entry in fs::read_dir(path).unwrap() {
                visit(root, &entry.unwrap().path(), depth + 1, total, out);
            }
        } else {
            assert!(meta.is_file() && meta.len() <= 8 * 1024 * 1024);
            let bytes = fs::read(path).unwrap();
            *total = total.checked_add(bytes.len()).unwrap();
            assert!(*total <= 128 * 1024 * 1024);
            out.insert(relative, Some(bytes));
        }
    }
    let mut result = BTreeMap::new();
    visit(root, root, 0, &mut 0, &mut result);
    result
}

#[test]
#[ignore = "requires the explicitly retained genuine native3 paired artifact; no model or GUI execution"]
fn genuine_native3_history_is_read_only_and_never_execution_permission() {
    let directory = PathBuf::from(
        std::env::var_os("LOCALLORE_LITERAL_NATIVE3_HISTORY")
            .expect("explicit genuine native3 artifact required"),
    );
    for (file, expected) in [
        (
            "run.json",
            "e284d6cce9ebef9f04369f6464bf8f88131ee594cc86ad7ab60a9edfc51e0132",
        ),
        (
            "report.json",
            "452ff03c8286159eafc85f0b0f14947406402ea944cc6af21b8d4c97fd544a86",
        ),
    ] {
        assert_eq!(
            format!(
                "{:x}",
                Sha256::digest(fs::read(directory.join(file)).unwrap())
            ),
            expected
        );
    }
    let before = inventory(&directory);
    let cap = desktop_api::open_read_only(&directory).unwrap();
    let summary = desktop_api::summary(&cap, true).unwrap();
    assert_eq!(summary["protocol_version"], 3);
    assert_eq!(summary["read_only"], true);
    assert_eq!(summary["execution_available"], false);
    assert_eq!(
        summary["report"]["lane"],
        "native_literal_relevant_comparison"
    );
    assert_eq!(summary["report"]["source_matches"], false);
    assert_eq!(summary["report"]["completed"], true);
    assert_eq!(summary["report"]["physical_setups"], 2);
    assert_eq!(summary["report"]["turns"].as_array().unwrap().len(), 48);
    assert_eq!(summary["report"]["quality_accepted"], false);
    let denied = desktop_api::evidence(
        &cap,
        "bad",
        &RowId {
            turn: "unknown".into(),
            arm: Arm::Left,
        },
        EvidenceRequest::Capture {
            observer: Observer::Actor("mira".into()),
        },
        true,
    );
    assert!(matches!(denied, Err(error) if error == "Forbidden"));
    let binding = summary["binding"].as_str().unwrap();
    let row = RowId {
        turn: "courier-01".into(),
        arm: Arm::Right,
    };
    let receipt = desktop_api::evidence(
        &cap,
        binding,
        &row,
        EvidenceRequest::Receipt {
            observer: Observer::Spoiler,
        },
        true,
    )
    .unwrap();
    assert_eq!(receipt["body"]["kind"], "receipt");
    assert_eq!(receipt["generation_grant"], false);
    let capture = desktop_api::evidence(
        &cap,
        binding,
        &row,
        EvidenceRequest::Capture {
            observer: Observer::Spoiler,
        },
        true,
    )
    .unwrap();
    assert_eq!(capture["body"]["kind"], "capture");
    assert_eq!(capture["generation_grant"], false);
    drop(cap);
    assert_eq!(inventory(&directory), before);
}
