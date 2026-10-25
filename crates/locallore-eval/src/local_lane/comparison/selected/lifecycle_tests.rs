// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! One frozen group / two indexed deterministic post-commit cancel journeys.
//! SOURCE-ONLY, UNCOMPILED/UNRUN; base0100d76f, Root freeze#29 6395530714.
//! Root registers this module and cfg(test)-only thread-local CANCEL_AFTER_ARM.
//! No pending-provider race, process kill, native/model/UI or public fault API.
//! Root: cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --lib local_lane::comparison::selected::lifecycle_tests -- --nocapture --test-threads=1
use super::*;
use std::{collections::BTreeMap, sync::{atomic::{AtomicU64, Ordering}, OnceLock}};

type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;
static NEXT: AtomicU64 = AtomicU64::new(0);

fn owned_root(label: &str) -> PathBuf {
    let root = std::env::temp_dir().join(format!(
        "locallore-selected-lifecycle-{label}-{}-{}-{}",
        std::process::id(),
        std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos(),
        NEXT.fetch_add(1, Ordering::Relaxed),
    ));
    fs::create_dir(&root).unwrap();
    root
}

// Call only after opaque source/destination locks and Store handles have dropped.
// Keep failed owned fixtures; never repair source or delete observed evidence.
fn inventory(root: &Path) -> Inventory {
    fn walk(root: &Path, path: &Path, depth: usize, bytes: &mut usize, out: &mut Inventory) {
        assert!(depth <= 8);
        for entry in fs::read_dir(path).unwrap() {
            assert!(out.len() < 4096);
            let path = entry.unwrap().path();
            let metadata = fs::symlink_metadata(&path).unwrap();
            assert!(!metadata.file_type().is_symlink());
            let relative = path.strip_prefix(root).unwrap().to_owned();
            if metadata.is_dir() {
                assert!(out.insert(relative, None).is_none());
                walk(root, &path, depth + 1, bytes, out);
            } else {
                assert!(metadata.is_file() && metadata.len() <= 8 * 1024 * 1024);
                let value = fs::read(&path).unwrap();
                *bytes = bytes.checked_add(value.len()).unwrap();
                assert!(*bytes <= 64 * 1024 * 1024);
                assert!(out.insert(relative, Some(value)).is_none());
            }
        }
    }
    let mut result = BTreeMap::new();
    walk(root, root, 0, &mut 0, &mut result);
    result
}

fn paired_template() -> &'static PathBuf {
    static SOURCE: OnceLock<PathBuf> = OnceLock::new();
    SOURCE.get_or_init(|| {
        let root = owned_root("producers");
        let reference_dir = root.join("reference");
        let produced = prepare_reference(&reference_dir, &Cancellation::default()).unwrap();
        assert_eq!((produced.accepted, produced.guard_only, produced.roles), (21, 3, 42));
        let reference = open_reference(&reference_dir).unwrap();
        let paired = root.join("paired");
        let report = run_comparison(&paired, false, ComparisonKind::PairedSnapshots,
            &Cancellation::default(), 1, LaneFactory::ScriptedBaseline, Some(&reference)).unwrap();
        assert_eq!(report.completed_scenes, 1);
        assert_eq!(report.turns.len(), 12);
        assert!(report.turns.iter().all(|row| row.passed));
        drop(reference);
        paired
    })
}

fn copied_source(root: &Path) -> PathBuf {
    let original = inventory(paired_template());
    let source = root.join("source");
    fs::create_dir(&source).unwrap();
    for (path, bytes) in &original {
        match bytes {
            None => fs::create_dir_all(source.join(path)).unwrap(),
            Some(bytes) => fs::write(source.join(path), bytes).unwrap(),
        }
    }
    assert!(inventory(&source) == original, "independent ordinary-file copy of actual producer");
    source
}

struct ResetBoundary;
impl ResetBoundary {
    fn enable() -> Self {
        CANCEL_AFTER_ARM.with(|flag| {
            assert!(!flag.get(), "fixed boundary flag defaults/reset to false");
            flag.set(true);
        });
        Self
    }
}
impl Drop for ResetBoundary {
    fn drop(&mut self) { CANCEL_AFTER_ARM.with(|flag| flag.set(false)); }
}

fn admitted_count(dir: &Path) -> usize {
    fs::read_dir(dir).unwrap().map(|entry| entry.unwrap().file_name().to_string_lossy().into_owned())
        .filter(|name| name.starts_with("admission-") && !name.ends_with("-settled.json")).count()
}

fn actual_turn_work(dir: &Path) -> Inventory {
    // The existing driver charges one new invocation to both arms on resume.
    // Permit ONLY those invocation-overhead files to differ in the completed arm;
    // every DB, checkpoint, admission, raw, capture and recording byte is retained.
    inventory(dir).into_iter().filter(|(path, _)| {
        !path.file_name().unwrap().to_string_lossy().starts_with("invocation-")
    }).collect()
}

#[test]
fn postcommit_cancel_keeps_parity_winner_then_resumes_only_the_missing_arm() {
    for index in [4usize, 5usize] {
        let root = owned_root(&format!("index-{index}"));
        let source = copied_source(&root);
        let source_inventory = inventory(&source);
        let source_binding = {
            let opened = desktop_api::open_read_only(&source).unwrap();
            let summary = desktop_api::summary(&opened, true).unwrap();
            let binding = summary["binding"].as_str().unwrap().to_owned();
            drop(opened);
            binding
        };
        let corpus = suite().unwrap();
        let step = &corpus.steps()[index];
        assert!(matches!(step.expected(), protocol::Expected::Accepted(_)));
        let plan = prepare_selected(&source, &source_binding, &desktop_api::RowId {
            turn: step.id().into(), arm: desktop_api::Arm::Right,
        }, SelectedIntent { client_id: format!("lifecycle-{index}"), lane: SelectedLane::ScriptedBaseline },
            &Cancellation::default()).unwrap();
        let before = plan.before.clone();
        let expected_inputs = plan.manifest.source_inputs.clone();
        let destination = root.join("selected");
        let cancel = Cancellation::default();
        let partial = {
            let _reset = ResetBoundary::enable();
            run_selected(plan, &destination, &cancel).unwrap()
        };
        assert!(!CANCEL_AFTER_ARM.with(|flag| flag.get()));
        assert!(cancel.is_cancelled(), "cancel fires only after actual committed checkpoint");
        assert!(!partial.completed);
        assert_eq!(partial.rows.len(), 1);
        let first = index % 2;
        let missing = 1 - first;
        let first_dir = destination.join(ARM_NAMES[first]);
        let missing_dir = destination.join(ARM_NAMES[missing]);
        let first_path = database(&first_dir, index, ComparisonKind::PairedSnapshots);
        let missing_path = database(&missing_dir, index, ComparisonKind::PairedSnapshots);
        let original: StoredTurn = decode(&checkpoint_path(&first_dir, index), 256 * 1024).unwrap();
        assert_eq!(original.arm, ARM_NAMES[first]);
        assert!(original.request == step.request(&before[first]));
        assert_eq!(original.row.phase, "committed");
        assert!(original.row.passed && original.row.roles_known && !original.row.recovered_without_checkpoint);
        assert_eq!(original.row.roles, 2);
        assert_eq!(original.row.policy, POLICIES[first]);
        assert!(partial.rows[0] == original.row);
        assert_eq!(partial.per_arm_progress[first].state, "finished");
        assert_eq!(partial.per_arm_progress[missing].state, "not_started");
        assert!(!missing_path.exists());
        assert!(!checkpoint_path(&missing_dir, index).exists());
        assert_eq!(admitted_count(&first_dir), 1);
        assert_eq!(admitted_count(&missing_dir), 0);
        let first_actual = engine(&first_path, before[first].scope()).unwrap();
        let saved = Store::open_read_only(&first_path).unwrap().lookup_turn(before[first].scope(), step.id()).unwrap();
        let receipt = saved.receipt.expect("actual committed Store receipt survives late cancel");
        assert!(receipt.request() == &original.request);
        assert!(first_actual.receipts().last() == Some(&receipt));
        assert_eq!(original.row.actual_receipt_sha256, Some(digest(&encode(&receipt).unwrap())));
        assert!(first_actual.at_revision(before[first].revision()).unwrap().canonical_bytes() == before[first].canonical_bytes());
        let initial_ledgers = ledgers(&destination, &partial.binding).unwrap();
        assert_eq!(initial_ledgers[first].admissions, 1);
        assert_eq!(initial_ledgers[first].charged_roles, 2);
        assert_eq!(initial_ledgers[missing].admissions, 0);
        assert_eq!(initial_ledgers[missing].charged_roles, 0);
        let first_work = actual_turn_work(&first_dir);
        assert!(inventory(&source) == source_inventory);

        let resumed = resume_selected(&destination, &source, &partial.binding, &Cancellation::default()).unwrap();
        assert!(resumed.completed);
        assert_eq!(resumed.rows.len(), 2);
        assert!(resumed.source_inputs == expected_inputs);
        assert!(actual_turn_work(&first_dir) == first_work, "completed first arm has no second admission, raw, receipt or checkpoint rewrite");
        let preserved = engine(&first_path, before[first].scope()).unwrap();
        assert!(preserved.canonical_bytes() == first_actual.canonical_bytes());
        assert!(preserved.receipts() == first_actual.receipts());
        assert!(resumed.rows.iter().find(|row| row.arm == ARM_NAMES[first]) == Some(&original.row));
        for arm in 0..2 {
            let dir = destination.join(ARM_NAMES[arm]);
            let turn: StoredTurn = decode(&checkpoint_path(&dir, index), 256 * 1024).unwrap();
            assert_eq!(turn.index, index);
            assert_eq!(turn.arm, ARM_NAMES[arm]);
            assert!(turn.request == step.request(&before[arm]));
            assert_eq!(turn.before_head, before[arm].revision());
            assert_eq!(turn.row.input_semantic_sha256, expected_inputs[arm].input_semantic_sha256);
            assert!(turn.row.passed && turn.row.roles_known && !turn.row.recovered_without_checkpoint);
            assert_eq!(turn.row.phase, "committed");
            assert_eq!(turn.row.policy, POLICIES[arm]);
            assert_eq!(turn.row.roles, 2);
            assert_eq!(admitted_count(&dir), 1);
            let actual = engine(&database(&dir, index, ComparisonKind::PairedSnapshots), before[arm].scope()).unwrap();
            assert!(actual.receipts().last().unwrap().request() == &turn.request);
            assert!(actual.at_revision(before[arm].revision()).unwrap().canonical_bytes() == before[arm].canonical_bytes());
        }
        assert!(inventory(&source) == source_inventory);
        let completed_destination = inventory(&destination);
        let retry = resume_selected(&destination, &source, &resumed.binding, &Cancellation::default()).unwrap();
        assert!(encode(&retry).unwrap() == encode(&resumed).unwrap());
        assert!(inventory(&destination) == completed_destination, "completed retry has no invocation/report/Store write");
        assert!(inventory(&source) == source_inventory);
    }
}
