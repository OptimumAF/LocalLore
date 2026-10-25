// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Genuine preserved UI5 data, never a reconstructed historical fixture.
//! Developer opt-in only; no provider, writer, native app or model execution.
use locallore::inspection_query::Observer;
use locallore_eval::local_lane::comparison::{
    desktop_api as full, selected::desktop_read as selected,
};
use sha2::{Digest, Sha256};
use std::{
    collections::BTreeMap,
    fs,
    path::{Path, PathBuf},
};

fn inventory(root: &Path) -> BTreeMap<PathBuf, Option<String>> {
    fn walk(
        root: &Path,
        path: &Path,
        depth: usize,
        bytes: &mut u64,
        out: &mut BTreeMap<PathBuf, Option<String>>,
    ) {
        assert!(depth <= 8);
        for entry in fs::read_dir(path).unwrap() {
            assert!(out.len() < 4096);
            let path = entry.unwrap().path();
            let metadata = fs::symlink_metadata(&path).unwrap();
            assert!(!metadata.file_type().is_symlink());
            let key = path.strip_prefix(root).unwrap().to_owned();
            if metadata.is_dir() {
                assert!(out.insert(key, None).is_none());
                walk(root, &path, depth + 1, bytes, out);
            } else {
                assert!(metadata.is_file() && metadata.len() <= 8 * 1024 * 1024);
                *bytes = bytes.checked_add(metadata.len()).unwrap();
                assert!(*bytes <= 64 * 1024 * 1024);
                let hash = format!("{:x}", Sha256::digest(fs::read(path).unwrap()));
                assert!(out.insert(key, Some(hash)).is_none());
            }
        }
    }
    assert!(root.is_absolute());
    let mut result = BTreeMap::new();
    walk(root, root, 0, &mut 0, &mut result);
    result
}

#[test]
#[ignore = "explicit genuine preserved UI5 paths; read-only history, no native UI/model execution"]
fn genuine_old_comparison_and_selected_history_remain_readable_without_rewrites() {
    let source = PathBuf::from(
        std::env::var_os("LOCALLORE_LITERAL_HISTORICAL_COMPARISON")
            .expect("explicit preserved comparison path"),
    );
    let target = PathBuf::from(
        std::env::var_os("LOCALLORE_LITERAL_HISTORICAL_SELECTED")
            .expect("explicit preserved selected work path"),
    );
    let before_source = inventory(&source);
    let before_target = inventory(&target);

    {
        let run = full::open_read_only(&source).unwrap();
        assert_eq!(full::summary(&run, false).unwrap_err(), "Forbidden");
        let summary = full::summary(&run, true).unwrap();
        assert_eq!(
            summary["report"]["source_matches"], false,
            "new test source advances provenance; old history is not current execution"
        );
        let binding = summary["binding"].as_str().unwrap();
        let row = full::RowId {
            turn: "courier-05".into(),
            arm: full::Arm::Right,
        };
        let receipt = full::evidence(
            &run,
            binding,
            &row,
            full::EvidenceRequest::Receipt {
                observer: Observer::Omniscient,
            },
            true,
        )
        .unwrap();
        assert_eq!(receipt["body"]["kind"], "receipt");
        assert_eq!(
            receipt["body"]["receipt"]["events"][0]["outcome"]["effect"],
            "moved"
        );
    }
    {
        let run = selected::open_read_only(&target).unwrap();
        assert_eq!(selected::summary(&run, false).unwrap_err(), "Forbidden");
        let summary = selected::summary(&run, true).unwrap();
        assert_eq!(summary["selection"]["turn"], "courier-05");
        assert_eq!(summary["selection"]["index"], 4);
        assert_eq!(summary["read_only"], true);
        assert_eq!(summary["execution_available"], false);
        let binding = summary["binding"].as_str().unwrap();
        for arm in [full::Arm::Left, full::Arm::Right] {
            let receipt = selected::evidence(
                &run,
                binding,
                arm,
                full::EvidenceRequest::Receipt {
                    observer: Observer::Omniscient,
                },
                true,
            )
            .unwrap();
            assert_eq!(receipt["body"]["kind"], "receipt");
            assert_eq!(receipt["before_head"], 4);
            assert_eq!(receipt["after_head"], 5);
            assert_eq!(
                receipt["body"]["receipt"]["events"][0]["outcome"]["effect"],
                "moved"
            );
        }
    }
    assert_eq!(
        inventory(&source),
        before_source,
        "complete original comparison bytes"
    );
    assert_eq!(
        inventory(&target),
        before_target,
        "complete original selected bytes"
    );
}
