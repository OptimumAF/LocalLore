// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen missing-checkpoint output-bound oracle, SOURCE ONLY / UNRUN.
//! Base 8ca63d0a; Root registers this private module and executes RED before fix.
//! Actual scripted source, native prepared plan and untouched not-started target;
//! no fabricated checkpoint, Engine, receipt, SQL history or native model work.
use super::*;
use crate::local_lane::comparison::desktop_api::{self as source_reader, Edge, RowId};
use locallore::inspection_query::{Observer, View};
use std::collections::BTreeMap;

const EVIDENCE_CAP: usize = 256 * 1024;
type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;

// Call only when all source/target capabilities have dropped: Windows run.lock
// is intentionally not read while the actual exclusive reader owns it.
fn inventory(root: &Path) -> Inventory {
    fn walk(root: &Path, dir: &Path, depth: usize, total: &mut usize, out: &mut Inventory) {
        assert!(depth <= 8);
        for entry in fs::read_dir(dir).unwrap() {
            assert!(out.len() < 4096);
            let path = entry.unwrap().path();
            let metadata = fs::symlink_metadata(&path).unwrap();
            assert!(!metadata.file_type().is_symlink());
            let relative = path.strip_prefix(root).unwrap().to_owned();
            if metadata.is_dir() {
                assert!(out.insert(relative, None).is_none());
                walk(root, &path, depth + 1, total, out);
            } else {
                assert!(metadata.is_file() && metadata.len() <= 8 * 1024 * 1024);
                let bytes = fs::read(&path).unwrap();
                *total = total.checked_add(bytes.len()).unwrap();
                assert!(*total <= 64 * 1024 * 1024);
                assert!(out.insert(relative, Some(bytes)).is_none());
            }
        }
    }
    let mut out = BTreeMap::new();
    walk(root, root, 0, &mut 0, &mut out);
    out
}

#[test]
fn absent_database_missing_envelope_obeys_same_evidence_cap_without_writes() {
    let root = std::env::temp_dir().join(format!(
        "locallore-selected-missing-budget-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    fs::create_dir(&root).unwrap();
    let source = root.join("source");
    let produced = run_comparison(
        &source,
        false,
        ComparisonKind::ContinuousRollout,
        &Cancellation::default(),
        1,
        LaneFactory::ScriptedBaseline,
        None,
    )
    .unwrap();
    assert_eq!(produced.completed_scenes, 1);
    assert_eq!(produced.turns.len(), 12);
    assert!(produced.turns.iter().all(|turn| turn.passed));
    let opened_source = source_reader::open_read_only(&source).unwrap();
    let source_summary = source_reader::summary(&opened_source, true).unwrap();
    let source_binding = source_summary["binding"].as_str().unwrap().to_owned();
    drop(opened_source);
    let corpus = suite().unwrap();
    let plan = prepare_selected(
        &source,
        &source_binding,
        &RowId {
            turn: corpus.steps()[0].id().into(),
            arm: Arm::Left,
        },
        SelectedIntent {
            client_id: "missing-output-budget-review".into(),
            lane: SelectedLane::ScriptedBaseline,
        },
        &Cancellation::default(),
    )
    .unwrap();
    let target = root.join("target");
    drop(new_destination(&plan, &target).unwrap());
    drop(plan);
    for arm in ARM_NAMES {
        assert!(!database(&target.join(arm), 0, ComparisonKind::ContinuousRollout).exists());
        assert!(!checkpoint_path(&target.join(arm), 0).exists());
    }
    let before = inventory(&root);
    let opened = open_read_only(&target).unwrap();
    let header = summary(&opened, true).unwrap();
    assert_eq!(header["arms"][0]["available"], false);
    assert_eq!(header["arms"][0]["after_head"], Value::Null);
    let binding = header["binding"].as_str().unwrap();
    let normal = evidence(
        &opened,
        binding,
        Arm::Left,
        EvidenceRequest::Query {
            edge: Edge::Before,
            observer: Observer::Player,
            view: View::History,
        },
        true,
    )
    .unwrap();
    assert_eq!(normal["body"]["kind"], "missing");
    assert_eq!(normal["body"]["reason"], "checkpoint_unavailable");
    assert_eq!(normal["after_head"], Value::Null);
    assert!(encode(&normal).unwrap().len() <= EVIDENCE_CAP);

    let oversized_observer = Observer::Character {
        id: "x".repeat(EVIDENCE_CAP + 1),
    };
    assert!(encode(&oversized_observer).unwrap().len() > EVIDENCE_CAP);
    let result = evidence(
        &opened,
        binding,
        Arm::Left,
        EvidenceRequest::Query {
            edge: Edge::Before,
            observer: oversized_observer,
            view: View::History,
        },
        true,
    );
    // Drop pins/lock and inventory even on the predicted pre-fix successful
    // oversized response; preserve the generated fixture for Root diagnosis.
    drop(opened);
    assert_eq!(inventory(&root), before, "both reads must be strictly read-only");
    match result {
        Err(error) => assert_eq!(error, "EvidenceBudget"),
        Ok(value) => panic!(
            "missing evidence escaped the existing cap: {} bytes > {EVIDENCE_CAP}",
            encode(&value).unwrap().len()
        ),
    }
}
