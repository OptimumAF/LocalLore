// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen selective-reader contract; UNCOMPILED/UNRUN by this author.
//! Base7c1d7bdaf2ff84aa51005fdb6ab3c5ab3cac06e2, claim #29 6393593224.
//! Exactly THREE tests. The old whole-run-on-each-click reader is expected to
//! fail the unselected diagnostic case; only Root's execution can establish RED.
//! Root: cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --test comparison_reader_snapshot_review -- --nocapture --test-threads=1
//! Cooperative run.lock protects normal writers. Deliberate noncooperating
//! faults below are bounded owned-file changes, never canonical SQL/history.
//! Immutable summary means last validated snapshot, not fresh whole-report
//! validation or execution permission. Future execution must full-preflight.

use locallore::{
    engine::Engine,
    inference::Cancellation,
    inspection_query::{self, Observer, Query, View, MAX_ROWS},
};
use locallore_eval::{
    local_lane::{comparison::{self, desktop_api, ComparisonKind}, LaneFactory},
    memory_comparison::frozen_suite,
};
use locallore_storage::Store;
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::{Path, PathBuf},
    sync::{atomic::{AtomicU64, Ordering}, OnceLock},
};

static NEXT: AtomicU64 = AtomicU64::new(0);
const CORRUPT: &[u8] = b"SYNTHETIC_OWNED_DIAGNOSTIC_CORRUPTION";

fn owned_root(label: &str) -> PathBuf {
    let root = std::env::temp_dir().join(format!("locallore-reader-snapshot-{label}-{}-{}-{}",
        std::process::id(),
        std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos(),
        NEXT.fetch_add(1, Ordering::Relaxed)));
    fs::create_dir(&root).unwrap();
    root
}
#[derive(PartialEq, Eq)]
struct Inventory { directories: BTreeSet<PathBuf>, files: BTreeMap<PathBuf, Vec<u8>> }
fn inventory(root: &Path) -> Inventory {
    fn visit(root: &Path, relative: &Path, depth: usize, result: &mut Inventory, total: &mut usize) {
        assert!(depth <= 8);
        let path = root.join(relative);
        let metadata = fs::symlink_metadata(&path).unwrap();
        assert!(!metadata.file_type().is_symlink());
        if metadata.is_dir() {
            result.directories.insert(relative.into());
            for child in fs::read_dir(path).unwrap() {
                visit(root, &relative.join(child.unwrap().file_name()), depth + 1, result, total);
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
fn producer() -> &'static Path {
    static SOURCE: OnceLock<PathBuf> = OnceLock::new();
    SOURCE.get_or_init(|| {
        let run = owned_root("producer").join("run");
        let report = comparison::run_comparison(&run, false, ComparisonKind::ContinuousRollout,
            &Cancellation::default(), 1, LaneFactory::ScriptedBaseline, None).unwrap();
        assert_eq!(report.completed_scenes, 1);
        assert_eq!(report.turns.len(), 12);
        assert!(report.turns.iter().all(|row| row.passed));
        run
    }).as_path()
}
fn owned_copy(label: &str) -> PathBuf {
    let source = inventory(producer());
    let target = owned_root(label).join("run");
    fs::create_dir(&target).unwrap();
    for relative in &source.directories {
        if !relative.as_os_str().is_empty() { fs::create_dir_all(target.join(relative)).unwrap(); }
    }
    for (relative, bytes) in &source.files { fs::write(target.join(relative), bytes).unwrap(); }
    assert!(inventory(&target) == source);
    target
}
fn json_file(path: &Path) -> Value { serde_json::from_slice(&fs::read(path).unwrap()).unwrap() }
fn known_row() -> desktop_api::RowId {
    desktop_api::RowId { turn: frozen_suite().unwrap().steps()[0].id().into(), arm: desktop_api::Arm::Left }
}
fn query(edge: desktop_api::Edge, observer: Observer, view: View) -> desktop_api::EvidenceRequest {
    desktop_api::EvidenceRequest::Query { edge, observer, view }
}
fn closed_error<T>(result: Result<T, String>) -> String {
    // No Debug bound on the opaque read capability or private Core values.
    let error = result.err().expect("required evidence must fail closed");
    assert!(!error.is_empty() && error.len() <= 96);
    assert!(error.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'_'));
    error
}
fn expect_write(root: &Path, relative: &Path, bytes: &[u8], expected: &mut Inventory) {
    assert!(expected.files.contains_key(relative));
    fs::write(root.join(relative), bytes).unwrap();
    assert!(expected.files.insert(relative.into(), bytes.to_vec()).is_some());
}
fn expect_remove(root: &Path, relative: &Path, expected: &mut Inventory) {
    assert!(expected.files.remove(relative).is_some());
    fs::remove_file(root.join(relative)).unwrap();
}
fn actual_engine(directory: &Path) -> Engine {
    Store::open_read_only(&directory.join("left/synthetic.sqlite")).unwrap()
        .resume(&frozen_suite().unwrap().seed().scope).unwrap().engine
}
fn actual_query(engine: &Engine, head: u64, observer: Observer, view: View) -> Value {
    let cut = engine.at_revision(head).unwrap();
    serde_json::to_value(inspection_query::query(&cut, &Query {
        version: 2, scope: cut.scope().clone(), expected_head: head, at_revision: None,
        observer, view, cursor: None, limit: MAX_ROWS, search: String::new(),
    }, true).unwrap()).unwrap()
}
fn assert_query(reply: &Value, binding: &str, cp: &Value, head: u64, edge: &str, observer: Observer, expected_page: Value) {
    assert_eq!(reply["version"], 1);
    assert_eq!(reply["binding"], binding);
    assert_eq!(reply["row"], json!({"turn":cp["row"]["turn"],"arm":"left"}));
    assert_eq!(reply["scope"], cp["request"]["scope"]);
    assert_eq!(reply["before_head"], cp["before_head"]);
    assert_eq!(reply["after_head"], cp["after_head"]);
    assert_eq!(reply["observer"], serde_json::to_value(observer).unwrap());
    assert_eq!(reply["edge"], edge);
    assert_eq!(reply["read_only"], true);
    assert_eq!(reply["generation_grant"], false);
    assert_eq!(reply["body"], json!({"kind":"query","page":expected_page}));
    assert_eq!(reply["body"]["page"]["head"], head);
    assert_eq!(reply["body"]["page"]["revision"], head);
}

#[test]
fn manifest_order_or_profile_drift_after_open_rejects_selected_evidence_without_repair() {
    for profile in [false, true] {
        let directory = owned_copy(if profile { "profile" } else { "order" });
        let mut expected = inventory(&directory); // Before mandatory run.lock.
        let opened = desktop_api::open_read_only(&directory).unwrap();
        let summary = desktop_api::summary(&opened, true).unwrap();
        let binding = summary["binding"].as_str().unwrap();
        let row = known_row();
        desktop_api::evidence(&opened, binding, &row, query(desktop_api::Edge::Before, Observer::Player, View::Knowledge), true).unwrap();
        let mut manifest = json_file(&directory.join("run.json"));
        // Drift a real field. Never relabel source_sha256 as fake history.
        if profile { manifest["profile"]["director_tokens"] = json!(351); }
        else { manifest["order"] = json!("SYNTHETIC_INVALID_ORDER"); }
        expect_write(&directory, Path::new("run.json"), &serde_json::to_vec(&manifest).unwrap(), &mut expected);
        closed_error(desktop_api::evidence(&opened, binding, &row, query(desktop_api::Edge::Before, Observer::Player, View::Knowledge), true));
        closed_error(desktop_api::evidence(&opened, binding, &row, desktop_api::EvidenceRequest::Receipt { observer: Observer::Omniscient }, true));
        assert_eq!(closed_error(desktop_api::evidence(&opened, binding, &row, query(desktop_api::Edge::Before, Observer::Player, View::Knowledge), false)), "Forbidden");
        drop(opened);
        assert!(inventory(&directory) == expected);
    }
}

#[test]
fn selected_checkpoint_and_capture_loss_or_corruption_never_return_cached_success() {
    for (label, capture, remove) in [
        ("selected-capture-missing",true,true), ("selected-capture-corrupt",true,false),
        ("selected-checkpoint-missing",false,true), ("selected-checkpoint-corrupt",false,false),
    ] {
        let directory = owned_copy(label);
        let mut expected = inventory(&directory);
        let opened = desktop_api::open_read_only(&directory).unwrap();
        let summary = desktop_api::summary(&opened, true).unwrap();
        let binding = summary["binding"].as_str().unwrap();
        let row = known_row();
        let cp = json_file(&directory.join("left/attempt-00.json"));
        assert_eq!(cp["capture_file"], "attempt-00-capture.json");
        desktop_api::evidence(&opened,binding,&row,query(desktop_api::Edge::After,Observer::Player,View::History),true).unwrap();
        let relative = Path::new(if capture { "left/attempt-00-capture.json" } else { "left/attempt-00.json" });
        if remove { expect_remove(&directory,relative,&mut expected); }
        else { expect_write(&directory,relative,CORRUPT,&mut expected); }
        for request in [
            query(desktop_api::Edge::After,Observer::Player,View::Knowledge),
            desktop_api::EvidenceRequest::Receipt{observer:Observer::Omniscient},
            desktop_api::EvidenceRequest::Capture{observer:Observer::Omniscient},
            desktop_api::EvidenceRequest::Outputs{observer:Observer::Omniscient},
        ] { closed_error(desktop_api::evidence(&opened,binding,&row,request,true)); }
        assert_eq!(closed_error(desktop_api::evidence(&opened,binding,&row,desktop_api::EvidenceRequest::Capture{observer:Observer::Character{id:"mira".into()}},true)),"Forbidden");
        drop(opened);
        assert!(inventory(&directory) == expected);
    }
}

#[test]
fn unselected_diagnostic_fault_preserves_last_validated_summary_and_selected_core_evidence_but_reopen_rejects() {
    for capture in [true,false] {
        let directory = owned_copy(if capture { "unselected-capture" } else { "unselected-recording" });
        let mut expected = inventory(&directory);
        let cp = json_file(&directory.join("left/attempt-00.json"));
        let later = json_file(&directory.join("left/attempt-05.json"));
        let relative = PathBuf::from("left").join(later[if capture { "capture_file" } else { "recording_file" }].as_str().unwrap());
        assert_ne!(relative,PathBuf::from("left/attempt-00-capture.json"));
        assert_ne!(relative,PathBuf::from("left/attempt-00-recording.json"));
        let actual = actual_engine(&directory);
        let row = known_row();
        let actual_receipt = Store::open_read_only(&directory.join("left/synthetic.sqlite")).unwrap()
            .lookup_turn(actual.scope(),&row.turn).unwrap().receipt.unwrap();
        let opened = desktop_api::open_read_only(&directory).unwrap();
        let summary = desktop_api::summary(&opened,true).unwrap();
        let binding = summary["binding"].as_str().unwrap();
        assert_eq!(summary["read_only"],true);
        assert_eq!(summary["execution_available"],false);
        let original_receipt = desktop_api::evidence(&opened,binding,&row,desktop_api::EvidenceRequest::Receipt{observer:Observer::Omniscient},true).unwrap();
        assert_eq!(original_receipt["body"],json!({"kind":"receipt","receipt":actual_receipt}));
        expect_write(&directory,&relative,CORRUPT,&mut expected);
        assert_eq!(desktop_api::summary(&opened,true).unwrap(),summary,"last validated summary is immutable, not a fresh whole-run health assertion");
        for (edge,name,head) in [(desktop_api::Edge::Before,"before",cp["before_head"].as_u64().unwrap()),(desktop_api::Edge::After,"after",cp["after_head"].as_u64().unwrap())] {
            for observer in [Observer::Player,Observer::Character{id:"mira".into()}] {
                for view in [View::Knowledge,View::History] {
                    let reply = desktop_api::evidence(&opened,binding,&row,query(edge,observer.clone(),view),true).unwrap();
                    assert_query(&reply,binding,&cp,head,name,observer.clone(),actual_query(&actual,head,observer.clone(),view));
                    if matches!(&observer,Observer::Character{id} if id=="mira") {
                        assert!(!reply.to_string().contains("SECRET-TIDE-731"));
                    }
                }
            }
        }
        assert_eq!(desktop_api::evidence(&opened,binding,&row,desktop_api::EvidenceRequest::Receipt{observer:Observer::Omniscient},true).unwrap(),original_receipt);
        assert_eq!(closed_error(desktop_api::evidence(&opened,binding,&row,query(desktop_api::Edge::After,Observer::Player,View::History),false)),"Forbidden");
        assert_eq!(closed_error(desktop_api::evidence(&opened,binding,&row,desktop_api::EvidenceRequest::Receipt{observer:Observer::Character{id:"mira".into()}},true)),"Forbidden");
        drop(opened);
        assert!(inventory(&directory) == expected);
        closed_error(desktop_api::open_read_only(&directory));
        assert!(inventory(&directory) == expected,"whole reopen rejects unrelated corruption without repair or publication");
    }
}
