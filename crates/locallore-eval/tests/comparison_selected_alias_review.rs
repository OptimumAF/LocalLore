// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen actual producer hardlink regression; SOURCE-ONLY, UNCOMPILED/UNRUN.
//! Exact baseline f1377ea7d3f4dc250d88056c18c202f716b9994d. No canonical SQL,
//! fabricated receipt, native/model provider or external source path.
//! Fixture correction after Root's first run failed before linking: a generated
//! accepted row's Play diagnostics need not equal the reference receipt. Use an
//! actual guard-only database, whose copied reference prefix is unchanged.
//! Root: cargo test --manifest-path crates/locallore-eval/Cargo.toml --locked --offline --test comparison_selected_alias_review -- --nocapture --test-threads=1
use locallore::{engine::Engine, inference::Cancellation};
use locallore_eval::{
    local_lane::{
        comparison::{self, desktop_api, selected, ComparisonKind},
        LaneFactory,
    },
    memory_comparison::{frozen_suite, Expected},
};
use locallore_storage::Store;
use serde_json::Value;
use std::{collections::BTreeMap, fs, path::{Path, PathBuf}};

type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;

fn owned_root() -> PathBuf {
    let path = std::env::temp_dir().join(format!(
        "locallore-selected-alias-{}-{}",
        std::process::id(),
        std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH)
            .unwrap().as_nanos(),
    ));
    fs::create_dir(&path).unwrap();
    // Retain only this owned synthetic root if the regression fails. Never
    // repair/recreate the source or discard its observed corrupted bytes.
    path
}

fn inventory(root: &Path) -> Inventory {
    fn walk(root: &Path, path: &Path, depth: usize, total: &mut usize, out: &mut Inventory) {
        assert!(depth <= 8 && out.len() < 4096, "bounded actual inventory");
        for entry in fs::read_dir(path).unwrap() {
            let path = entry.unwrap().path();
            let meta = fs::symlink_metadata(&path).unwrap();
            assert!(!meta.file_type().is_symlink());
            let key = path.strip_prefix(root).unwrap().to_owned();
            if meta.is_dir() {
                assert!(out.insert(key, None).is_none());
                walk(root, &path, depth + 1, total, out);
            } else {
                assert!(meta.is_file() && meta.len() <= 8 * 1024 * 1024);
                let bytes = fs::read(&path).unwrap();
                *total = total.checked_add(bytes.len()).unwrap();
                assert!(*total <= 64 * 1024 * 1024);
                assert!(out.insert(key, Some(bytes)).is_none());
            }
        }
    }
    let mut out = BTreeMap::new();
    walk(root, root, 0, &mut 0, &mut out);
    out
}

fn changed(before: &Inventory, after: &Inventory) -> Vec<PathBuf> {
    before.keys().chain(after.keys()).filter(|key| before.get(*key) != after.get(*key))
        .cloned().collect::<std::collections::BTreeSet<_>>().into_iter().collect()
}

fn value(path: &Path) -> Value {
    serde_json::from_slice(&fs::read(path).unwrap()).unwrap()
}

fn engine(path: &Path) -> Engine {
    let mut store = Store::open_read_only(path).unwrap();
    let engine = store.resume(&frozen_suite().unwrap().seed().scope).unwrap().engine;
    drop(store);
    engine
}

fn sole_database(destination: &Path, arm: &str) -> PathBuf {
    let paths = fs::read_dir(destination.join(arm)).unwrap()
        .map(|entry| entry.unwrap().path())
        .filter(|path| path.extension().is_some_and(|extension| extension == "sqlite"))
        .collect::<Vec<_>>();
    assert_eq!(paths.len(), 1, "exactly one actual selected arm database");
    assert!(paths[0].is_file());
    paths[0].clone()
}

#[test]
fn resume_refuses_valid_prefix_hardlinked_to_earlier_paired_source_before_any_mutation() {
    let root = owned_root();
    let source = root.join("paired");
    let reference_path = root.join("reference");
    let suite = frozen_suite().unwrap();
    let guard_index = suite.steps().windows(2).position(|steps| {
        matches!(steps[0].expected(), Expected::GuardRejected(_))
            && matches!(steps[1].expected(), Expected::Accepted(_))
    }).expect("actual guard-only step immediately before an accepted selected step");
    let selected_index = guard_index + 1;
    let scenes = selected_index / 6 + 1;
    assert!(scenes <= 4);
    let reference_report = comparison::prepare_reference(&reference_path, &Cancellation::default()).unwrap();
    assert_eq!((reference_report.accepted, reference_report.guard_only, reference_report.roles), (21, 3, 42));
    let reference = comparison::open_reference(&reference_path).unwrap();
    let produced = comparison::run_comparison(
        &source, false, ComparisonKind::PairedSnapshots, &Cancellation::default(),
        scenes, LaneFactory::ScriptedBaseline, Some(&reference),
    ).unwrap();
    assert_eq!(produced.turns.len(), scenes * 12);
    assert_eq!(produced.completed_scenes, scenes);
    assert!(produced.turns.iter().all(|row| row.passed));
    drop(reference);

    let selected_source = source.join("left").join(format!("pair-{selected_index:02}.sqlite"));
    let earlier_source = source.join("left").join(format!("pair-{guard_index:02}.sqlite"));
    let source_checkpoint = value(&source.join("left").join(format!("attempt-{selected_index:02}.json")));
    let guard_checkpoint = value(&source.join("left").join(format!("attempt-{guard_index:02}.json")));
    let guard_rejection = match suite.steps()[guard_index].expected() {
        Expected::GuardRejected(rejection) => format!("{rejection:?}"),
        _ => unreachable!("guard derived from the frozen suite"),
    };
    assert_eq!(guard_checkpoint["row"]["phase"], "failed");
    assert_eq!(guard_checkpoint["row"]["error"], guard_rejection);
    assert_eq!(guard_checkpoint["row"]["roles"], 0);
    assert!(guard_checkpoint["row"]["actual_receipt_sha256"].is_null());
    assert_eq!(guard_checkpoint["before_head"], guard_checkpoint["after_head"]);
    assert_eq!(source_checkpoint["row"]["phase"], "committed", "selected step actually accepted, not dependency-skipped");
    assert!(!source_checkpoint["row"]["actual_receipt_sha256"].is_null());
    {
        let full = engine(&selected_source);
        let selected_before = full.at_revision(source_checkpoint["before_head"].as_u64().unwrap()).unwrap();
        let earlier_after = engine(&earlier_source);
        assert_eq!(earlier_after.revision(), guard_checkpoint["after_head"].as_u64().unwrap());
        assert!(earlier_after.receipts().iter().all(|receipt| receipt.request().turn != suite.steps()[guard_index].id()),
            "the actual guard database has no accepted receipt for its failed step");
        assert_eq!(earlier_after.revision(), selected_before.revision());
        assert!(earlier_after.receipts() == selected_before.receipts(), "full actual receipt prefix equality");
        assert!(earlier_after.canonical_bytes() == selected_before.canonical_bytes(), "full actual canonical prefix equality");
        assert!(earlier_after.accepted_history_basis().unwrap() == selected_before.accepted_history_basis().unwrap());
    }
    let source_binding = {
        let opened = desktop_api::open_read_only(&source).unwrap();
        let summary = desktop_api::summary(&opened, true).unwrap();
        let binding = summary["binding"].as_str().unwrap().to_owned();
        drop(opened);
        binding
    };
    let selection = desktop_api::RowId {
        turn: suite.steps()[selected_index].id().into(),
        arm: desktop_api::Arm::Left,
    };
    let plan = selected::prepare_selected(
        &source, &source_binding, &selection,
        selected::SelectedIntent {
            client_id: "selected-hardlink-alias".into(),
            lane: selected::SelectedLane::ScriptedBaseline,
        },
        &Cancellation::default(),
    ).unwrap();
    let destination = root.join("selected");
    let selected_report = serde_json::to_value(
        selected::run_selected(plan, &destination, &Cancellation::default()).unwrap(),
    ).unwrap();
    assert_eq!(selected_report["completed"], true);
    assert_eq!(selected_report["rows"].as_array().unwrap().len(), 2);
    assert!(selected_report["rows"].as_array().unwrap().iter()
        .all(|row| row["phase"] == "committed" && row["passed"] == true),
        "both actual selected arms commit the legitimate accepted step");
    let selected_binding = selected_report["binding"].as_str().unwrap().to_owned();
    let left_checkpoint = destination.join("left").join(format!("attempt-{selected_index:02}.json"));
    let right_checkpoint = destination.join("right").join(format!("attempt-{selected_index:02}.json"));
    assert!(left_checkpoint.is_file() && right_checkpoint.is_file());
    let left_database = sole_database(&destination, "left");
    // Both producer calls have returned and all Store/read capabilities were
    // dropped before replacing these two actual workflow-owned files.
    fs::remove_file(&left_checkpoint).unwrap();
    fs::remove_file(&left_database).unwrap();
    fs::hard_link(&earlier_source, &left_database)
        .expect("the ordinary-file hardlink must actually succeed; no skip/pass fallback");
    assert!(fs::read(&left_database).unwrap() == fs::read(&earlier_source).unwrap(), "actual hardlinked bytes equal");
    assert!(!left_checkpoint.exists());
    assert!(right_checkpoint.is_file(), "the completed right half is retained intact");

    // Inventories are captured AFTER the intentional alias setup, with no live
    // locks. They include every file byte and directory, including invocation,
    // admission/settlement, recording/capture and canonical database files.
    let before_source = inventory(&source);
    let before_destination = inventory(&destination);
    let resumed = selected::resume_selected(
        &destination, &source, &selected_binding, &Cancellation::default(),
    );
    let after_source = inventory(&source);
    let after_destination = inventory(&destination);
    let source_changes = changed(&before_source, &after_source);
    let destination_changes = changed(&before_destination, &after_destination);
    let error = resumed.err();
    assert!(source_changes.is_empty() && destination_changes.is_empty(),
        "alias refusal must precede writes: source changes {:?}; destination changes {:?}; error {:?}; retained synthetic root {:?}",
        source_changes, destination_changes, error, root);
    let error = error.expect("an ordinary hardlink to source must be refused, not admitted or repaired");
    assert!(!error.is_empty() && error.len() <= 96);
    assert!(error.bytes().all(|byte| byte.is_ascii_alphanumeric() || byte == b'_'));
    assert_eq!(inventory(&source), before_source);
    assert_eq!(inventory(&destination), before_destination);
}
