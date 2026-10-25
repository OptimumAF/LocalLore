// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen authorization-order regression, UNCOMPILED/UNRUN by this author.
//! Actual producer base77b56f690cc6773c9a2def5600da05d261e7a5a9.
//! Claim #29 6393349980; sole NEW test file, existing oracles/production untouched.
//! Root: cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --test comparison_reader_authorization_review -- --nocapture --test-threads=1
//! Exactly TWO normal tests. Synthetic provider fixture, not real model/native
//! UI execution; no zero-provider/role claim inferred from metadata.

use locallore::{inference::Cancellation, inspection_query::{Observer, View}};
use locallore_eval::{
    local_lane::{comparison::{self, desktop_api, ComparisonKind}, LaneFactory},
    memory_comparison::frozen_suite,
};
use serde_json::Value;
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::{Path, PathBuf},
    sync::{atomic::{AtomicU64, Ordering}, OnceLock},
};

static NEXT: AtomicU64 = AtomicU64::new(0);

fn owned_root(label: &str) -> PathBuf {
    let path = std::env::temp_dir().join(format!(
        "locallore-reader-auth-{label}-{}-{}-{}",
        std::process::id(),
        std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos(),
        NEXT.fetch_add(1, Ordering::Relaxed)
    ));
    fs::create_dir(&path).unwrap();
    path
}

#[derive(PartialEq, Eq)]
struct Inventory {
    directories: BTreeSet<PathBuf>,
    files: BTreeMap<PathBuf, Vec<u8>>,
}
fn inventory(root: &Path) -> Inventory {
    fn visit(root: &Path, relative: &Path, depth: usize, result: &mut Inventory, total: &mut usize) {
        assert!(depth <= 8);
        let path = root.join(relative);
        let metadata = fs::symlink_metadata(&path).unwrap();
        assert!(!metadata.file_type().is_symlink());
        if metadata.is_dir() {
            result.directories.insert(relative.into());
            for entry in fs::read_dir(path).unwrap() {
                visit(root, &relative.join(entry.unwrap().file_name()), depth + 1, result, total);
            }
        } else {
            assert!(metadata.is_file() && metadata.len() <= 8 * 1024 * 1024);
            let bytes = fs::read(path).unwrap();
            *total = total.checked_add(bytes.len()).unwrap();
            assert!(*total <= 32 * 1024 * 1024);
            assert!(result.files.insert(relative.into(), bytes).is_none());
        }
        assert!(result.files.len() + result.directories.len() <= 1024);
    }
    let mut result = Inventory { directories: BTreeSet::new(), files: BTreeMap::new() };
    visit(root, Path::new(""), 0, &mut result, &mut 0);
    result
}

fn actual_producer() -> &'static Path {
    static SOURCE: OnceLock<PathBuf> = OnceLock::new();
    SOURCE.get_or_init(|| {
        let run = owned_root("producer").join("run");
        let report = comparison::run_comparison(
            &run, false, ComparisonKind::ContinuousRollout, &Cancellation::default(),
            1, LaneFactory::ScriptedBaseline, None,
        ).unwrap();
        assert_eq!(report.completed_scenes, 1);
        assert_eq!(report.turns.len(), 12);
        assert!(report.turns.iter().all(|row| row.passed));
        run
    }).as_path()
}

fn copy_run(label: &str) -> PathBuf {
    let source = inventory(actual_producer());
    let target = owned_root(label).join("run");
    fs::create_dir(&target).unwrap();
    for relative in &source.directories {
        if !relative.as_os_str().is_empty() { fs::create_dir_all(target.join(relative)).unwrap(); }
    }
    for (relative, bytes) in &source.files { fs::write(target.join(relative), bytes).unwrap(); }
    assert!(inventory(&target) == source);
    target
}

fn known_row() -> desktop_api::RowId {
    desktop_api::RowId {
        turn: frozen_suite().unwrap().steps()[0].id().into(),
        arm: desktop_api::Arm::Left,
    }
}
fn query() -> desktop_api::EvidenceRequest {
    desktop_api::EvidenceRequest::Query {
        edge: desktop_api::Edge::Before,
        observer: Observer::Player,
        view: View::Knowledge,
    }
}
fn raw(kind: u8, observer: Observer) -> desktop_api::EvidenceRequest {
    match kind {
        0 => desktop_api::EvidenceRequest::Receipt { observer },
        1 => desktop_api::EvidenceRequest::Capture { observer },
        2 => desktop_api::EvidenceRequest::Outputs { observer },
        _ => unreachable!(),
    }
}
fn error<T>(result: Result<T, String>) -> String {
    // Opaque OpenedComparison and private Core authority never need Debug.
    result.err().expect("must return an error, never private data")
}

#[test]
fn actor_raw_denial_precedes_stale_binding_and_unknown_row_even_on_healthy_snapshot() {
    let directory = copy_run("identity");
    let before = inventory(&directory);
    let opened = desktop_api::open_read_only(&directory).unwrap();
    let summary = desktop_api::summary(&opened, true).unwrap();
    let binding = summary["binding"].as_str().unwrap();
    let known = known_row();
    assert_eq!(desktop_api::evidence(&opened, binding, &known, query(), true).unwrap()["body"]["kind"], "query");
    let unknown = desktop_api::RowId { turn: "not-a-frozen-turn".into(), arm: desktop_api::Arm::Right };
    let stale = "0".repeat(64);
    assert_ne!(binding, stale);
    let mut denials = vec![];
    for observer in [Observer::Player, Observer::Character { id: "mira".into() }] {
        for kind in 0..3 {
            for (binding, row) in [(stale.as_str(), &known), (binding, &unknown), (stale.as_str(), &unknown)] {
                denials.push(error(desktop_api::evidence(&opened, binding, row, raw(kind, observer.clone()), true)));
            }
        }
    }
    drop(opened);
    assert!(inventory(&directory) == before, "denials cannot write ledgers, checkpoints or source bytes");
    assert_eq!(denials.len(), 18);
    // Collect first so all three raw kinds and both identities are exercised
    // before reporting the expected pre-fix denial-precedence failure.
    assert_eq!(denials, vec!["Forbidden".to_owned(); 18]);
}

#[test]
fn actor_raw_denial_precedes_live_required_evidence_loss_or_corruption_while_query_fails_closed() {
    let mut denials = vec![];
    for (label, capture, remove) in [
        ("missing-capture", true, true),
        ("corrupt-capture", true, false),
        ("missing-checkpoint", false, true),
        ("corrupt-checkpoint", false, false),
    ] {
        let directory = copy_run(label);
        // Windows run.lock is mandatory-locked while the capability is open.
        // Capture ALL bytes before opening; alter only the expected fixture fault
        // below, then read/compare the entire inventory only after dropping it.
        let mut after_fault = inventory(&directory);
        let opened = desktop_api::open_read_only(&directory).unwrap();
        let summary = desktop_api::summary(&opened, true).unwrap();
        let binding = summary["binding"].as_str().unwrap();
        let known = known_row();
        assert_eq!(desktop_api::evidence(&opened, binding, &known, query(), true).unwrap()["body"]["kind"], "query");
        let checkpoint_path = directory.join("left/attempt-00.json");
        let checkpoint: Value = serde_json::from_slice(&fs::read(&checkpoint_path).unwrap()).unwrap();
        let capture_file = checkpoint["capture_file"].as_str().unwrap();
        assert_eq!(capture_file, "attempt-00-capture.json");
        let fault_path = if capture { directory.join("left").join(capture_file) } else { checkpoint_path };
        // Deliberate noncooperating-writer fault in this freshly owned clone,
        // AFTER valid opening/binding. It adds no accepted history or fake row.
        let relative = fault_path.strip_prefix(&directory).unwrap();
        assert!(after_fault.files.contains_key(relative));
        if remove {
            fs::remove_file(&fault_path).unwrap();
            assert!(after_fault.files.remove(relative).is_some());
        } else {
            let corrupted = b"SYNTHETIC_REQUIRED_EVIDENCE_CORRUPTION";
            fs::write(&fault_path, corrupted).unwrap();
            assert!(after_fault.files.insert(relative.into(), corrupted.to_vec()).is_some());
        }
        for observer in [Observer::Player, Observer::Character { id: "mira".into() }] {
            for kind in 0..3 {
                denials.push(error(desktop_api::evidence(&opened, binding, &known, raw(kind, observer.clone()), true)));
            }
        }
        let permitted_query_error = error(desktop_api::evidence(&opened, binding, &known, query(), true));
        assert_ne!(permitted_query_error, "Forbidden", "valid actor query must actually validate the now-corrupt source");
        assert!(!permitted_query_error.is_empty() && permitted_query_error.len() <= 96);
        assert!(permitted_query_error.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'_'));
        drop(opened);
        assert!(inventory(&directory) == after_fault, "reader must not repair, admit, settle or publish after the fault");
    }
    assert_eq!(denials.len(), 24);
    assert_eq!(denials, vec!["Forbidden".to_owned(); 24]);
}
