// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent FIRST after 8aa6db84 + e5a95395: UNREGISTERED/UNCOMPILED/UNRUN.
//! All selected3 behavior uses public APIs. Only the labelled divergent SOURCE
//! fixture drives existing private Scene4 execution, as contracted before freeze.
//! CANCEL_AFTER_ARM is a fixed post-checkpoint test boundary, not an OS crash.
//! Actual Host/Store/ledger; no model/native/UI/OS experiment or invented history.
//! Failed fixtures and explicit loss/tamper originals are retained, never cleaned.
use super::{
    desktop_read, inspect_selected, prepare_selected, prepared_metadata, resume_selected,
    run_selected, PreparedSelectedPlan, CANCEL_AFTER_ARM,
};
use crate::local_lane::{
    comparison::{
        self as comparison,
        desktop_api::{Arm, Edge, EvidenceRequest, RowId},
        scene_v4 as source4,
        selected::{SelectedIntent, SelectedLane},
    },
    LaneFactory, Ledger, TestFault,
};
use crate::memory_comparison_v4::{self as v4, TurnReportV4};
use crate::{digest, encode, engine, Result};
use locallore::{
    contracts::{Command, Intent, Request},
    engine::Engine,
    inference::Cancellation,
    inspection_query::{self, Observer, Query, View, MAX_ROWS},
};
use locallore_storage::Store;
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::{Path, PathBuf},
    sync::{
        atomic::{AtomicU64, Ordering},
        OnceLock,
    },
    time::Instant,
};

const INDEX: usize = 4;
const ARMS: [&str; 2] = ["left", "right"];
const SECRET: &str = "SECRET-TIDE-731";
type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;
static NEXT: AtomicU64 = AtomicU64::new(0);

fn root(label: &str) -> PathBuf {
    let override_parent = std::env::var_os("LOCALLORE_SELECTED4_TEST_ROOT");
    let parent = override_parent
        .clone()
        .map(PathBuf::from)
        .unwrap_or_else(std::env::temp_dir);
    assert!(parent.is_absolute() && parent.is_dir());
    let parent = fs::canonicalize(parent).unwrap();
    for ancestor in parent.ancestors() {
        let info = fs::symlink_metadata(ancestor).unwrap();
        assert!(info.is_dir() && !info.file_type().is_symlink());
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt;
            assert_eq!(
                info.file_attributes() & 0x400,
                0,
                "ordinary existing parent only"
            );
        }
    }
    // Only the explicitly dedicated test packet is scanned for cumulative
    // retention admission. Never inventory an unrelated global temp directory.
    if override_parent.is_some() {
        fn retained(dir: &Path, depth: usize, entries: &mut usize, bytes: &mut u64) {
            assert!(depth <= 12);
            for item in fs::read_dir(dir).unwrap() {
                *entries += 1;
                assert!(*entries <= 100_000);
                let path = item.unwrap().path();
                let info = fs::symlink_metadata(&path).unwrap();
                assert!(!info.file_type().is_symlink());
                if info.is_dir() {
                    retained(&path, depth + 1, entries, bytes);
                } else {
                    assert!(info.is_file());
                    *bytes = bytes.checked_add(info.len()).unwrap();
                    assert!(
                        *bytes <= 256 * 1024 * 1024,
                        "retained selected4 packet budget exceeded; preserve and stop"
                    );
                }
            }
        }
        retained(&parent, 0, &mut 0, &mut 0);
    }
    let child = parent.join(format!(
        "selected4-first-{label}-{}-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos(),
        NEXT.fetch_add(1, Ordering::Relaxed)
    ));
    fs::create_dir(&child).unwrap();
    child
}
// Only whole-inventory reads AFTER every opaque owner for this root has dropped.
fn inventory(root: &Path) -> Inventory {
    fn walk(root: &Path, dir: &Path, depth: usize, total: &mut usize, out: &mut Inventory) {
        assert!(depth <= 10);
        for entry in fs::read_dir(dir).unwrap() {
            assert!(out.len() < 8192);
            let path = entry.unwrap().path();
            let info = fs::symlink_metadata(&path).unwrap();
            assert!(!info.file_type().is_symlink());
            let relative = path.strip_prefix(root).unwrap().to_owned();
            if info.is_dir() {
                assert!(out.insert(relative, None).is_none());
                walk(root, &path, depth + 1, total, out);
            } else {
                assert!(info.is_file() && info.len() <= 8 * 1024 * 1024);
                let bytes = fs::read(path).unwrap();
                *total = total.checked_add(bytes.len()).unwrap();
                assert!(*total <= 64 * 1024 * 1024);
                assert!(out.insert(relative, Some(bytes)).is_none());
            }
        }
    }
    let mut result = Inventory::new();
    walk(root, root, 0, &mut 0, &mut result);
    result
}
fn unchanged(dir: &Path, before: &Inventory) {
    let after = inventory(dir);
    let changed: BTreeSet<_> = before
        .keys()
        .chain(after.keys())
        .filter(|path| before.get(*path) != after.get(*path))
        .collect();
    assert!(
        changed.is_empty(),
        "retained fixture {}: {} changed paths, first16 {:?}",
        dir.display(),
        changed.len(),
        changed.iter().take(16).collect::<Vec<_>>()
    );
}
fn copied(before: &Inventory, destination: &Path) {
    fs::create_dir(destination).unwrap();
    for (relative, bytes) in before {
        match bytes {
            None => fs::create_dir_all(destination.join(relative)).unwrap(),
            Some(bytes) => {
                fs::create_dir_all(destination.join(relative).parent().unwrap()).unwrap();
                fs::write(destination.join(relative), bytes).unwrap();
            }
        }
    }
    unchanged(destination, before);
}
fn value(path: &Path) -> Value {
    serde_json::from_slice(&fs::read(path).unwrap()).unwrap()
}
fn keys(object: &Value, expected: &[&str]) {
    assert_eq!(
        object
            .as_object()
            .unwrap()
            .keys()
            .map(String::as_str)
            .collect::<BTreeSet<_>>(),
        expected.iter().copied().collect::<BTreeSet<_>>()
    );
}
fn refused<T>(result: Result<T>) -> String {
    let error = result
        .err()
        .expect("expected finite refusal, never success");
    assert!(
        !error.is_empty()
            && error.len() <= 96
            && error
                .bytes()
                .all(|b| b.is_ascii_alphanumeric() || b == b'_')
    );
    error
}
fn cp(dir: &Path, arm: &str, index: usize) -> PathBuf {
    comparison::checkpoint_path(&dir.join(arm), index)
}
fn db(dir: &Path, arm: &str, index: usize, kind: comparison::ComparisonKind) -> PathBuf {
    comparison::database(&dir.join(arm), index, kind)
}
fn source_binding(dir: &Path) -> String {
    let opened = source4::desktop_api::open_read_only(dir).unwrap();
    let summary = source4::desktop_api::summary(&opened, true).unwrap();
    assert_eq!(summary["protocol_version"], 4);
    assert!(
        summary["unavailable"]
            .as_array()
            .unwrap()
            .iter()
            .any(|item| item == "selected_protocol4_rerun_not_implemented"),
        "shared producer does not silently enable the desktop rerun control"
    );
    summary["binding"].as_str().unwrap().into()
}
fn selected_binding(dir: &Path) -> String {
    value(&dir.join("selected.json"))["binding"]
        .as_str()
        .unwrap()
        .into()
}
fn row(index: usize, arm: Arm) -> RowId {
    RowId {
        turn: comparison::suite().unwrap().steps()[index].id().into(),
        arm,
    }
}
fn plan(source: &Path, index: usize, arm: Arm, client: &str) -> PreparedSelectedPlan {
    prepare_selected(
        source,
        &source_binding(source),
        &row(index, arm),
        SelectedIntent {
            client_id: client.into(),
            lane: SelectedLane::ScriptedBaseline,
        },
        &Cancellation::default(),
    )
    .unwrap()
}
fn public_source(kind: comparison::ComparisonKind, fault: bool) -> &'static Path {
    static PAIRED: OnceLock<std::result::Result<PathBuf, ()>> = OnceLock::new();
    static ROLLOUT: OnceLock<std::result::Result<PathBuf, ()>> = OnceLock::new();
    static FAILED: OnceLock<std::result::Result<PathBuf, ()>> = OnceLock::new();
    let slot = if fault {
        &FAILED
    } else if kind == comparison::ComparisonKind::PairedSnapshots {
        &PAIRED
    } else {
        &ROLLOUT
    };
    // Cache failed SOURCE construction too: preserve its first packet and fail
    // later dependent tests without generating replacement fixture attempts.
    slot.get_or_init(|| {
        std::panic::catch_unwind(|| {
            let dir = root(if fault {
                "public-failed-source"
            } else {
                "public-source"
            });
            let reference = if kind == comparison::ComparisonKind::PairedSnapshots {
                let r = dir.join("reference-owner");
                comparison::prepare_reference(&r, &Cancellation::default()).unwrap();
                Some(comparison::open_reference(&r).unwrap())
            } else {
                None
            };
            let source = dir.join("source");
            let report = source4::run_comparison(
                &source,
                false,
                kind,
                &Cancellation::default(),
                2,
                if fault {
                    LaneFactory::TestFault(TestFault::WrongCommand)
                } else {
                    LaneFactory::ScriptedBaseline
                },
                reference.as_ref(),
            )
            .unwrap();
            assert_eq!(
                (report.version, report.completed_scenes, report.turns.len()),
                (4, 2, 24)
            );
            assert_eq!(source4::inspect_comparison(&source).unwrap(), report);
            assert_eq!(report.arms, v4::arm_descriptors());
            assert!(!report.quality_accepted);
            source
        })
        .map_err(|_| ())
    })
    .as_ref()
    .expect("original public source setup failed; evidence retained; no replacement source run")
    .as_path()
}
// Approved e5a95395 private-driver SOURCE only: all outcomes/checkpoints are real.
fn divergent_source() -> &'static Path {
    static ORIGINAL: OnceLock<std::result::Result<PathBuf, ()>> = OnceLock::new();
    ORIGINAL.get_or_init(|| std::panic::catch_unwind(|| {
        let dir = root("private-driver-divergent-source").join("source");
        let manifest = source4::Manifest::new(comparison::ComparisonKind::ContinuousRollout, LaneFactory::ScriptedBaseline.profile().unwrap(), None).unwrap();
        let mut session = source4::Session4::open(&dir, false, manifest, None, Instant::now()).unwrap();
        session.begin_invocations().unwrap();
        comparison::turn_execution::record_setup(&mut session.ledgers, comparison::turn_execution::Setup {
            version: 4, dir: &session.dir, key: &session.key, native: false, physical_ms: 0, status: "scripted", load: None }).unwrap();
        let corpus = comparison::suite().unwrap();
        for index in 0..6 { for arm in 0..2 {
            let began = Instant::now(); let d = dir.join(ARMS[arm]); let path = comparison::database(&d, index, comparison::ComparisonKind::ContinuousRollout);
            comparison::ensure_database(&path, corpus.seed(), &[]).unwrap();
            let factory = if index == 0 && arm == 0 { LaneFactory::TestFault(TestFault::WrongCommand) } else { LaneFactory::ScriptedBaseline };
            let turn = source4::execute_turn4(source4::Job4 { dir: &d, path: &path, index, arm: ARMS[arm], construction: source4::CONSTRUCTIONS[arm],
                binding: &session.key, step: &corpus.steps()[index], factory: &factory, cancel: &Cancellation::default(), diagnostics: false }, &mut session.ledgers[arm]).unwrap();
            if index == 0 && arm == 0 { assert_eq!(turn.row.phase, "failed"); assert_eq!(turn.before_head, turn.after_head);
                assert!(engine(&path, &corpus.seed().scope).unwrap().receipts().is_empty()); }
            if index == 0 && arm == 1 { assert_eq!(turn.row.phase, "committed"); assert_eq!(engine(&path, &corpus.seed().scope).unwrap().receipts().len(), 1); }
            session.turns[arm].push(turn);
            session.ledgers[1 - arm].exclude_measured_interval(began.elapsed().as_millis().min(u64::MAX as u128) as u64).unwrap();
        } }
        comparison::saved(&dir.join("scene-00.json"), &source4::scene_data4(&dir, &session.key, 0).unwrap(), 4096).unwrap();
        let report = session.finish().unwrap(); assert_eq!((report.completed_scenes, report.turns.len()), (1, 12));
        assert_eq!(source4::inspect_comparison(&dir).unwrap(), report); dir
    }).map_err(|_| ())).as_ref().expect("original private-driver source setup failed; evidence retained; no replacement source run").as_path()
}
struct Fixture {
    root: PathBuf,
    source: PathBuf,
    kind: comparison::ComparisonKind,
}
impl Fixture {
    fn new(label: &str, kind: comparison::ComparisonKind) -> Self {
        let original = inventory(public_source(kind, false));
        let root = root(label);
        let source = root.join("source");
        copied(&original, &source);
        Self { root, source, kind }
    }
    fn from_source(label: &str, actual: &Path, kind: comparison::ComparisonKind) -> Self {
        let original = inventory(actual);
        let root = root(label);
        let source = root.join("source");
        copied(&original, &source);
        Self { root, source, kind }
    }
    fn run(&self, index: usize, clicked: Arm, client: &str) -> (PathBuf, Value) {
        let target = self.root.join("selected");
        let report = serde_json::to_value(
            run_selected(
                plan(&self.source, index, clicked, client),
                &target,
                &Cancellation::default(),
            )
            .unwrap(),
        )
        .unwrap();
        (target, report)
    }
}
struct ResetBoundary;
impl ResetBoundary {
    fn enable() -> Self {
        CANCEL_AFTER_ARM.with(|flag| {
            assert!(!flag.get());
            flag.set(true);
        });
        Self
    }
}
impl Drop for ResetBoundary {
    fn drop(&mut self) {
        CANCEL_AFTER_ARM.with(|flag| flag.set(false));
    }
}
fn half(f: &Fixture, index: usize) -> (PathBuf, Value) {
    let target = f.root.join("selected");
    let cancel = Cancellation::default();
    let p = plan(&f.source, index, Arm::Right, "selected4-half");
    let reset = ResetBoundary::enable();
    let report = serde_json::to_value(run_selected(p, &target, &cancel).unwrap()).unwrap();
    drop(reset);
    assert!(cancel.is_cancelled());
    assert_eq!(report["completed"], false);
    assert_eq!(report["rows"].as_array().unwrap().len(), 1);
    (target, report)
}
fn retain_loss(f: &Fixture, file: &Path, name: &str) {
    assert!(file.starts_with(&f.root));
    let saved = f.root.join(format!("retained-loss-{name}"));
    assert!(!saved.exists());
    fs::rename(file, saved).unwrap();
}
fn query(edge: Edge, observer: Observer, view: View) -> EvidenceRequest {
    EvidenceRequest::Query {
        edge,
        observer,
        view,
    }
}
fn current_scope() -> locallore::contracts::Scope {
    comparison::suite().unwrap().seed().scope.clone()
}
fn actual_before(
    source: &Path,
    arm: &str,
    index: usize,
    kind: comparison::ComparisonKind,
) -> Engine {
    let checkpoint = value(&cp(source, arm, index));
    let full = engine(&db(source, arm, index, kind), &current_scope()).unwrap();
    full.at_revision(checkpoint["before_head"].as_u64().unwrap())
        .unwrap()
}
fn contexts(engine: &Engine) -> Value {
    json!([
        engine
            .character_context(&engine.seed().player, engine.scope(), engine.revision())
            .unwrap(),
        engine
            .character_context("mira", engine.scope(), engine.revision())
            .unwrap(),
        engine
            .character_context("sable", engine.scope(), engine.revision())
            .unwrap()
    ])
}

#[test]
fn public_admission_precedence_exact_source_binding_and_lock_never_create_or_repair() {
    let f = Fixture::new("admission", comparison::ComparisonKind::ContinuousRollout);
    let before = inventory(&f.root);
    let missing = f.root.join("missing");
    let cancel = Cancellation::default();
    cancel.cancel();
    assert_eq!(
        refused(prepare_selected(
            &missing,
            "bad",
            &row(INDEX, Arm::Left),
            SelectedIntent {
                client_id: "".into(),
                lane: SelectedLane::ApprovedNative
            },
            &cancel
        )),
        "Interrupted"
    );
    assert_eq!(
        refused(prepare_selected(
            &missing,
            "bad",
            &row(INDEX, Arm::Left),
            SelectedIntent {
                client_id: "".into(),
                lane: SelectedLane::ApprovedNative
            },
            &Cancellation::default()
        )),
        "SelectedIdentity"
    );
    for (client, binding) in [
        ("".to_owned(), "a".repeat(64)),
        ("valid-client".into(), "bad".into()),
        ("invalid_client".into(), "a".repeat(64)),
        ("a".repeat(129), "a".repeat(64)),
    ] {
        assert_eq!(
            refused(prepare_selected(
                &missing,
                &binding,
                &row(INDEX, Arm::Left),
                SelectedIntent {
                    client_id: client,
                    lane: SelectedLane::ApprovedNative
                },
                &Cancellation::default()
            )),
            "SelectedIdentity"
        );
    }
    assert_eq!(
        refused(prepare_selected(
            &missing,
            &"a".repeat(64),
            &row(INDEX, Arm::Left),
            SelectedIntent {
                client_id: "native-unavailable".into(),
                lane: SelectedLane::ApprovedNative
            },
            &Cancellation::default()
        )),
        "SelectedNativeUnavailable"
    );
    unchanged(&f.root, &before);
    let binding = source_binding(&f.source);
    let run_key = value(&cp(&f.source, "left", INDEX))["binding"]
        .as_str()
        .unwrap()
        .to_owned();
    assert_ne!(binding, run_key);
    assert_eq!(
        refused(prepare_selected(
            &f.source,
            &binding,
            &RowId {
                turn: "unknown-selected4-row".into(),
                arm: Arm::Left
            },
            SelectedIntent {
                client_id: "unknown-row".into(),
                lane: SelectedLane::ScriptedBaseline
            },
            &Cancellation::default()
        )),
        "UnknownRow"
    );
    assert_eq!(
        refused(prepare_selected(
            &f.source,
            &run_key,
            &row(INDEX, Arm::Left),
            SelectedIntent {
                client_id: "wrong-authority".into(),
                lane: SelectedLane::ScriptedBaseline
            },
            &Cancellation::default()
        )),
        "SnapshotMismatch"
    );
    let p = plan(&f.source, INDEX, Arm::Right, "holds-source");
    assert_eq!(
        refused(source4::desktop_api::open_read_only(&f.source)),
        "RunBusy"
    );
    drop(p);
    unchanged(&f.root, &before);
    let p = plan(&f.source, INDEX, Arm::Left, "cancel-before-run");
    let cancelled = Cancellation::default();
    cancelled.cancel();
    assert_eq!(
        refused(run_selected(
            p,
            &f.root.join("cancelled-target"),
            &cancelled
        )),
        "Interrupted"
    );
    unchanged(&f.root, &before);
    retain_loss(
        &f,
        &cp(&f.source, "right", INDEX),
        "unclicked-arm-checkpoint",
    );
    let lost = inventory(&f.root);
    refused(prepare_selected(
        &f.source,
        &binding,
        &row(INDEX, Arm::Left),
        SelectedIntent {
            client_id: "missing-right".into(),
            lane: SelectedLane::ScriptedBaseline,
        },
        &Cancellation::default(),
    ));
    unchanged(&f.root, &lost);
}

#[test]
fn public_noninitial_paired_and_rollout_keep_exact_requests_prefixes_and_closed_v4_identity() {
    for kind in [
        comparison::ComparisonKind::PairedSnapshots,
        comparison::ComparisonKind::ContinuousRollout,
    ] {
        let f = Fixture::new("actual-prefix", kind);
        let source_before = inventory(&f.source);
        let source_id = source_binding(&f.source);
        let p = plan(&f.source, INDEX, Arm::Right, "selected4-prefix");
        let metadata = prepared_metadata(&p).unwrap();
        keys(
            &metadata,
            &[
                "version",
                "kind",
                "source_protocol_version",
                "binding",
                "source_binding",
                "lane",
                "selection",
                "arms",
                "constructions",
            ],
        );
        assert_eq!(metadata["version"], 3);
        assert_eq!(metadata["source_protocol_version"], 4);
        assert_eq!(metadata["source_binding"], source_id);
        assert_eq!(
            metadata["constructions"],
            serde_json::to_value(v4::arm_descriptors()).unwrap()
        );
        assert!(encode(&metadata).unwrap().len() <= 16 * 1024);
        let target = f.root.join("selected");
        let result = run_selected(p, &target, &Cancellation::default()).unwrap();
        let report = serde_json::to_value(&result).unwrap();
        keys(
            &report,
            &[
                "version",
                "run_type",
                "source_protocol_version",
                "arms",
                "client_id",
                "binding",
                "source_binding",
                "source_kind",
                "source_profile",
                "source_native",
                "selection",
                "lane",
                "profile",
                "suite_sha256",
                "source_sha256",
                "source_reference_sha256",
                "source_inputs",
                "rows",
                "completed",
                "per_arm_progress",
                "physical_setups",
                "physical_setup_ms",
                "native_load",
                "left_charged_ms",
                "right_charged_ms",
                "left_reserved_roles",
                "right_reserved_roles",
                "human_reviewed",
                "human_rubric",
                "quality_accepted",
                "unavailable",
                "limitations",
            ],
        );
        let manifest = value(&target.join("selected.json"));
        keys(
            &manifest,
            &[
                "version",
                "run_type",
                "source_protocol_version",
                "arms",
                "client_id",
                "binding",
                "source_binding",
                "source_kind",
                "source_profile",
                "source_native",
                "selection",
                "lane",
                "profile",
                "suite_sha256",
                "source_sha256",
                "source_reference_sha256",
                "source_inputs",
            ],
        );
        assert_eq!(manifest["version"], 3);
        assert_eq!(manifest["source_protocol_version"], 4);
        assert_eq!(manifest["source_binding"], source_id);
        assert_eq!(manifest["binding"], metadata["binding"]);
        assert_ne!(manifest["binding"], manifest["source_binding"]);
        let mut unsigned = manifest.clone();
        unsigned.as_object_mut().unwrap().remove("binding");
        assert_eq!(manifest["binding"], digest(&encode(&unsigned).unwrap()));
        assert_eq!(report["completed"], true);
        assert_eq!(
            report["arms"],
            serde_json::to_value(v4::arm_descriptors()).unwrap()
        );
        assert_eq!(
            report["selection"],
            json!({"turn": comparison::suite().unwrap().steps()[INDEX].id(), "clicked_arm":"right", "index":INDEX})
        );
        assert_eq!(report["lane"], "scripted_selected_case");
        assert_eq!(report["source_native"], false);
        assert_eq!(report["source_kind"], serde_json::to_value(kind).unwrap());
        assert_eq!(
            report["profile"],
            serde_json::to_value(LaneFactory::ScriptedBaseline.profile().unwrap()).unwrap()
        );
        assert_eq!(
            report["source_profile"],
            value(&f.source.join("run.json"))["profile"]
        );
        assert_eq!(
            report["source_reference_sha256"],
            value(&f.source.join("run.json"))["reference_sha256"]
        );
        assert_eq!(report["physical_setups"], 0);
        assert!(report["physical_setup_ms"].is_null() && report["native_load"].is_null());
        assert_eq!(report["human_reviewed"], 0);
        assert_eq!(report["human_rubric"], "not_reviewed");
        assert_eq!(report["quality_accepted"], false);
        for (arm_index, arm) in ARMS.into_iter().enumerate() {
            let before = actual_before(&f.source, arm, INDEX, kind);
            let source_cp = value(&cp(&f.source, arm, INDEX));
            let expected: Request = serde_json::from_value(source_cp["request"].clone()).unwrap();
            let actual = value(&cp(&target, arm, INDEX));
            assert_eq!(actual["version"], 4);
            assert_eq!(actual["index"], INDEX);
            assert_eq!(actual["request"], source_cp["request"]);
            assert_eq!(actual["before_head"], before.revision());
            assert_eq!(
                report["source_inputs"][arm_index]["request"],
                source_cp["request"]
            );
            assert_eq!(
                report["source_inputs"][arm_index]["prefix_sha256"],
                digest(&encode(before.receipts()).unwrap())
            );
            assert_eq!(
                report["source_inputs"][arm_index]["input_semantic_sha256"],
                source_cp["row"]["input_semantic_sha256"]
            );
            let full = engine(&db(&target, arm, INDEX, kind), &current_scope()).unwrap();
            assert_eq!(
                full.at_revision(before.revision())
                    .unwrap()
                    .canonical_bytes(),
                before.canonical_bytes()
            );
            assert_eq!(full.receipts().last().unwrap().request(), &expected);
            assert_eq!(full.receipts().len(), before.receipts().len() + 1);
            let actual_row: TurnReportV4 =
                serde_json::from_value(report["rows"][arm_index].clone()).unwrap();
            assert_eq!(actual_row.construction, v4::arm_descriptors()[arm_index]);
            assert_eq!(actual_row.phase, "committed");
            assert_eq!(
                actual_row.construction_evidence_status,
                v4::ConstructionEvidenceStatusV4::ValidatedCommittedSceneNarratorV1
            );
            let actual_typed_receipt_hash =
                digest(&encode(full.receipts().last().unwrap()).unwrap());
            assert_eq!(
                actual_row.actual_receipt_sha256.as_deref(),
                Some(actual_typed_receipt_hash.as_str())
            );
            assert_eq!(actual["row"], report["rows"][arm_index]);
            for earlier in 0..INDEX {
                assert!(!cp(&target, arm, earlier).exists());
            }
        }
        assert_eq!(
            serde_json::to_value(inspect_selected(&target).unwrap()).unwrap(),
            report
        );
        assert!(fs::metadata(target.join("report.json")).unwrap().len() <= 2 * 1024 * 1024);
        assert!(fs::metadata(target.join("report.html")).unwrap().len() <= 2 * 1024 * 1024);
        let done = inventory(&target);
        assert_eq!(
            serde_json::to_value(
                resume_selected(
                    &target,
                    &f.source,
                    metadata["binding"].as_str().unwrap(),
                    &Cancellation::default()
                )
                .unwrap()
            )
            .unwrap(),
            report
        );
        unchanged(&target, &done);
        unchanged(&f.source, &source_before);
    }
}

#[test]
fn actual_private_driver_divergence_and_failed_source_row_are_not_reconstructed_from_reports() {
    let f = Fixture::from_source(
        "divergent-selection",
        divergent_source(),
        comparison::ComparisonKind::ContinuousRollout,
    );
    let left = actual_before(&f.source, "left", INDEX, f.kind);
    let right = actual_before(&f.source, "right", INDEX, f.kind);
    assert_ne!(left.canonical_bytes(), right.canonical_bytes());
    assert_ne!(left.revision(), right.revision());
    assert!(left
        .receipts()
        .iter()
        .all(|r| r.request().turn != comparison::suite().unwrap().steps()[0].id()));
    assert!(right
        .receipts()
        .iter()
        .any(|r| r.request().turn == comparison::suite().unwrap().steps()[0].id()));
    let before = inventory(&f.source);
    let (target, report) = f.run(INDEX, Arm::Left, "selected4-divergent");
    assert_ne!(
        report["source_inputs"][0]["prefix_sha256"],
        report["source_inputs"][1]["prefix_sha256"]
    );
    for (arm, expected) in [("left", left), ("right", right)] {
        let actual = engine(&db(&target, arm, INDEX, f.kind), &current_scope()).unwrap();
        assert_eq!(
            actual
                .at_revision(expected.revision())
                .unwrap()
                .canonical_bytes(),
            expected.canonical_bytes()
        );
    }
    unchanged(&f.source, &before);
    let f = Fixture::from_source(
        "failed-row-selection",
        divergent_source(),
        comparison::ComparisonKind::ContinuousRollout,
    );
    let failed = value(&cp(&f.source, "left", 0));
    assert_eq!(failed["row"]["phase"], "failed");
    assert!(failed["row"]["actual_receipt_sha256"].is_null());
    let (_, report) = f.run(0, Arm::Left, "selected4-real-failed-input");
    assert_eq!(report["completed"], true);
    assert_eq!(report["rows"].as_array().unwrap().len(), 2);
    assert_eq!(report["source_inputs"][0]["request"], failed["request"]);
}

#[test]
fn disjoint_existing_targets_and_changed_source_refuse_without_destination_or_source_repair() {
    let f = Fixture::new(
        "target-boundaries",
        comparison::ComparisonKind::PairedSnapshots,
    );
    let before = inventory(&f.root);
    for destination in [&f.source, &f.source.join("nested"), &f.root] {
        refused(run_selected(
            plan(&f.source, INDEX, Arm::Left, "selected4-disjoint"),
            destination,
            &Cancellation::default(),
        ));
        unchanged(&f.root, &before);
    }
    let existing = f.root.join("existing");
    fs::create_dir(&existing).unwrap();
    fs::write(existing.join("sentinel"), b"unchanged").unwrap();
    let existing_before = inventory(&f.root);
    refused(run_selected(
        plan(&f.source, INDEX, Arm::Left, "selected4-existing"),
        &existing,
        &Cancellation::default(),
    ));
    unchanged(&f.root, &existing_before);
    let p = plan(&f.source, INDEX, Arm::Right, "selected4-refresh-source");
    let path = cp(&f.source, "left", INDEX);
    let mut changed = value(&path);
    changed["request"]["intent"]["value"]["text"] = json!("different synthetic original intent");
    fs::write(&path, encode(&changed).unwrap()).unwrap();
    let target = f.root.join("not-created");
    refused(run_selected(p, &target, &Cancellation::default()));
    assert!(!target.exists());
    let changed_before = inventory(&f.root);
    refused(prepare_selected(
        &f.source,
        &"a".repeat(64),
        &row(INDEX, Arm::Right),
        SelectedIntent {
            client_id: "no-repair".into(),
            lane: SelectedLane::ScriptedBaseline,
        },
        &Cancellation::default(),
    ));
    unchanged(&f.root, &changed_before);
    let f = Fixture::new(
        "paired-reference-drift",
        comparison::ComparisonKind::PairedSnapshots,
    );
    let mut before = inventory(&f.root);
    let p = plan(&f.source, INDEX, Arm::Left, "selected4-reference-drift");
    let reference_path = f.source.join("reference/reference.json");
    fs::write(&reference_path, b"{broken original reference").unwrap();
    before.insert(
        reference_path.strip_prefix(&f.root).unwrap().into(),
        Some(b"{broken original reference".to_vec()),
    );
    let target = f.root.join("not-created");
    refused(run_selected(p, &target, &Cancellation::default()));
    assert!(!target.exists());
    unchanged(&f.root, &before);
}

#[test]
fn fixed_after_arm_cancellation_retains_real_parity_winner_and_completed_resume_is_byte_identical()
{
    for index in [4usize, 5] {
        let f = Fixture::new("after-arm", comparison::ComparisonKind::PairedSnapshots);
        let source_before = inventory(&f.source);
        let (target, paused) = half(&f, index);
        let first = index % 2;
        let last = 1 - first;
        assert_eq!(paused["rows"][0]["arm"], ARMS[first]);
        assert_eq!(paused["rows"][0]["phase"], "committed");
        assert_eq!(paused["per_arm_progress"][first]["state"], "finished");
        assert_eq!(paused["per_arm_progress"][last]["state"], "not_started");
        assert!(!db(&target, ARMS[last], index, f.kind).exists());
        assert!(!cp(&target, ARMS[last], index).exists());
        let completed_turn = inventory(&target.join(ARMS[first]));
        let binding = selected_binding(&target);
        let resumed = serde_json::to_value(
            resume_selected(&target, &f.source, &binding, &Cancellation::default()).unwrap(),
        )
        .unwrap();
        assert_eq!(resumed["completed"], true);
        assert_eq!(resumed["rows"][first], paused["rows"][0]);
        let after = inventory(&target.join(ARMS[first]));
        for (path, bytes) in completed_turn {
            if !path
                .file_name()
                .unwrap()
                .to_string_lossy()
                .starts_with("invocation-")
            {
                assert_eq!(after.get(&path), Some(&bytes));
            }
        }
        let done = inventory(&target);
        let again = serde_json::to_value(
            resume_selected(&target, &f.source, &binding, &Cancellation::default()).unwrap(),
        )
        .unwrap();
        assert_eq!(again, resumed);
        unchanged(&target, &done);
        unchanged(&f.source, &source_before);
    }
}

#[test]
fn real_unknown_reservations_preflight_both_arms_without_refunds_or_extra_invocations() {
    let f = Fixture::new("budget", comparison::ComparisonKind::PairedSnapshots);
    let (target, _) = half(&f, INDEX);
    let binding = selected_binding(&target);
    let right = target.join("right");
    let mut ledger = Ledger::load(&right, &binding).unwrap();
    ledger.begin_invocation().unwrap();
    for expected in 0..27 {
        assert_eq!(
            ledger.admit("scene-0", "selected4-unknown-work").unwrap(),
            expected
        );
    }
    ledger.finish().unwrap();
    drop(ledger);
    let unknown = Ledger::load(&right, &binding).unwrap();
    assert_eq!(unknown.admissions, 27);
    assert_eq!(unknown.charged_roles, 81);
    assert!(
        unknown.remaining() >= 120_000 && unknown.remaining_after_reservation(120_000) < 63_000
    );
    drop(unknown);
    let before = inventory(&f.root);
    assert_eq!(
        refused(resume_selected(
            &target,
            &f.source,
            &binding,
            &Cancellation::default()
        )),
        "RunBudget"
    );
    unchanged(&f.root, &before);
    assert!(!db(&target, "right", INDEX, f.kind).exists());
    assert!(!cp(&target, "right", INDEX).exists());
}

#[test]
fn committed_checkpoint_loss_uses_actual_store_receipt_without_generation_or_invented_scene_evidence(
) {
    let f = Fixture::new(
        "committed-recovery",
        comparison::ComparisonKind::ContinuousRollout,
    );
    let (target, original) = f.run(INDEX, Arm::Left, "selected4-recovery");
    let before_engines: Vec<_> = ARMS
        .iter()
        .map(|arm| engine(&db(&target, arm, INDEX, f.kind), &current_scope()).unwrap())
        .collect();
    let binding = selected_binding(&target);
    let admissions: Vec<_> = ARMS
        .iter()
        .map(|arm| {
            Ledger::load(&target.join(arm), &binding)
                .unwrap()
                .admissions
        })
        .collect();
    retain_loss(
        &f,
        &cp(&target, "left", INDEX),
        "actual-committed-checkpoint",
    );
    let recovered = serde_json::to_value(
        resume_selected(&target, &f.source, &binding, &Cancellation::default()).unwrap(),
    )
    .unwrap();
    let row = &recovered["rows"][0];
    assert_eq!(row["phase"], "committed");
    assert_eq!(row["recovered_without_checkpoint"], true);
    assert_eq!(row["roles_known"], false);
    assert_eq!(row["construction_evidence_status"], "unavailable");
    assert_eq!(row["passed"], false);
    // Receipt.play retains actual recipe/fallback metadata. Its availability
    // must not be confused with independently validated original scene capture.
    for field in ["construction_matches", "fallback", "repairs"] {
        assert_eq!(row[field], original["rows"][0][field]);
    }
    for field in [
        "admission",
        "first_final_response_ms",
        "commit_elapsed_ms",
        "narrator_prompt_sha256",
        "narrator_schema_sha256",
        "scene_frame_sha256",
        "capture_sha256",
        "recording_sha256",
        "trace",
    ] {
        assert!(row[field].is_null(), "{field}");
    }
    assert_eq!(
        row["actual_receipt_sha256"],
        digest(&encode(before_engines[0].receipts().last().unwrap()).unwrap())
    );
    assert!(row["raw_sha256"].as_array().unwrap().is_empty());
    for (i, arm) in ARMS.iter().enumerate() {
        let actual = engine(&db(&target, arm, INDEX, f.kind), &current_scope()).unwrap();
        assert_eq!(
            actual.canonical_bytes(),
            before_engines[i].canonical_bytes()
        );
        assert_eq!(actual.receipts(), before_engines[i].receipts());
        assert_eq!(
            Ledger::load(&target.join(arm), &binding)
                .unwrap()
                .admissions,
            admissions[i]
        );
    }
}

#[test]
fn actual_empty_bootstrap_can_resume_but_cancelled_store_key_without_checkpoint_never_regenerates()
{
    let f = Fixture::new("bootstrap", comparison::ComparisonKind::PairedSnapshots);
    let (target, _) = half(&f, INDEX);
    let binding = selected_binding(&target);
    let path = db(&target, "right", INDEX, f.kind);
    drop(Store::open_application(&path).unwrap());
    assert_eq!(refused(inspect_selected(&target)), "BootstrapIncomplete");
    let complete = serde_json::to_value(
        resume_selected(&target, &f.source, &binding, &Cancellation::default()).unwrap(),
    )
    .unwrap();
    assert_eq!(complete["completed"], true);
    let f = Fixture::new("terminal-key", comparison::ComparisonKind::PairedSnapshots);
    let (target, _) = half(&f, INDEX);
    let binding = selected_binding(&target);
    let before = actual_before(&f.source, "right", INDEX, f.kind);
    let path = db(&target, "right", INDEX, f.kind);
    comparison::ensure_database(&path, before.seed(), before.receipts()).unwrap();
    let request = comparison::suite().unwrap().steps()[INDEX].request(&before);
    let mut store = Store::open_application(&path).unwrap();
    store.begin_turn(&request).unwrap();
    store.cancel_turn(&request).unwrap();
    drop(store);
    let cancelled = inventory(&f.root);
    assert_eq!(
        refused(resume_selected(
            &target,
            &f.source,
            &binding,
            &Cancellation::default()
        )),
        "TerminalCheckpointMissing"
    );
    unchanged(&f.root, &cancelled);
}

#[test]
fn public_reader_query2_and_finite_diagnostics_do_not_change_character_knowledge_or_generation_contexts(
) {
    let f = Fixture::new("read-only", comparison::ComparisonKind::PairedSnapshots);
    let (target, report) = f.run(INDEX, Arm::Right, "selected4-reader");
    let before = inventory(&f.root);
    let opened = desktop_read::open_read_only(&target).unwrap();
    let summary = desktop_read::summary(&opened, true).unwrap();
    keys(
        &summary,
        &[
            "version",
            "kind",
            "source_protocol_version",
            "constructions",
            "binding",
            "selection",
            "lane",
            "arms",
            "read_only",
            "execution_available",
        ],
    );
    assert_eq!(summary["version"], 3);
    assert_eq!(summary["source_protocol_version"], 4);
    assert_eq!(summary["read_only"], true);
    assert_eq!(summary["execution_available"], false);
    assert_eq!(
        summary["constructions"],
        serde_json::to_value(v4::arm_descriptors()).unwrap()
    );
    assert_eq!(summary["selection"], report["selection"]);
    assert_eq!(summary["arms"].as_array().unwrap().len(), 2);
    assert!(encode(&summary).unwrap().len() <= 16 * 1024);
    let binding = summary["binding"].as_str().unwrap();
    assert_ne!(summary["binding"], report["binding"]);
    assert_ne!(summary["binding"], report["source_binding"]);
    for forbidden in [
        "request",
        "source_inputs",
        "profile",
        "report",
        "rows",
        "narration",
        "error",
    ] {
        assert!(summary.get(forbidden).is_none());
    }
    for (arm_index, (arm, name)) in [(Arm::Left, "left"), (Arm::Right, "right")]
        .into_iter()
        .enumerate()
    {
        let checkpoint = value(&cp(&target, name, INDEX));
        let full = engine(&db(&target, name, INDEX, f.kind), &current_scope()).unwrap();
        let context = contexts(&full);
        let arm_metadata = &summary["arms"][arm_index];
        keys(
            arm_metadata,
            &["arm", "scope", "before_head", "after_head", "available"],
        );
        assert_eq!(arm_metadata["arm"], name);
        assert_eq!(arm_metadata["scope"], checkpoint["request"]["scope"]);
        assert_eq!(arm_metadata["before_head"], checkpoint["before_head"]);
        assert_eq!(arm_metadata["after_head"], checkpoint["after_head"]);
        assert_eq!(arm_metadata["available"], true);
        for (edge, field) in [(Edge::Before, "before_head"), (Edge::After, "after_head")] {
            let head = checkpoint[field].as_u64().unwrap();
            let cut = full.at_revision(head).unwrap();
            for observer in [
                Observer::Player,
                Observer::Character { id: "mira".into() },
                Observer::Character { id: "sable".into() },
            ] {
                for view in [View::History, View::Knowledge] {
                    let evidence = desktop_read::evidence(
                        &opened,
                        binding,
                        arm,
                        query(edge, observer.clone(), view),
                        true,
                    )
                    .unwrap();
                    keys(
                        &evidence,
                        &[
                            "version",
                            "binding",
                            "row",
                            "scope",
                            "before_head",
                            "after_head",
                            "observer",
                            "edge",
                            "read_only",
                            "generation_grant",
                            "body",
                        ],
                    );
                    assert_eq!(evidence["generation_grant"], false);
                    assert_eq!(evidence["read_only"], true);
                    assert!(encode(&evidence).unwrap().len() <= 256 * 1024);
                    let expected = inspection_query::query(
                        &cut,
                        &Query {
                            version: 2,
                            scope: cut.scope().clone(),
                            expected_head: head,
                            at_revision: None,
                            observer: observer.clone(),
                            view,
                            cursor: None,
                            limit: MAX_ROWS,
                            search: String::new(),
                        },
                        true,
                    )
                    .unwrap();
                    assert_eq!(
                        evidence["body"]["page"],
                        serde_json::to_value(expected).unwrap()
                    );
                    if view == View::Knowledge && matches!(&observer, Observer::Player) {
                        // This seed deliberately grants the fact to the player;
                        // authorization is observer-specific, not sentinel-wide.
                        let fact = &cut.seed().facts["relic-location"];
                        assert!(fact.known_by.contains(&cut.seed().player));
                        assert!(fact.proposition.contains(SECRET));
                        assert!(evidence["body"]["page"]["rows"]
                            .as_array()
                            .unwrap()
                            .iter()
                            .any(|row| row["kind"] == "knowledge"
                                && row["id"] == "relic-location"
                                && row["subject"].as_str() == Some(cut.seed().player.as_str())
                                && row["text"].as_str() == Some(fact.proposition.as_str())));
                    } else {
                        assert!(!evidence.to_string().contains(SECRET));
                    }
                    if view == View::History
                        && matches!(&observer, Observer::Character { id } if id == "sable")
                    {
                        assert!(evidence["body"]["page"]["rows"]
                            .as_array()
                            .unwrap()
                            .is_empty());
                    }
                    if view == View::History
                        && matches!(&observer, Observer::Character { id } if id == "mira")
                    {
                        assert!(evidence["body"]["page"]
                            .to_string()
                            .contains("amber stitch"));
                    }
                }
            }
        }
        for (kind, request) in [
            (
                "receipt",
                EvidenceRequest::Receipt {
                    observer: Observer::Omniscient,
                },
            ),
            (
                "capture",
                EvidenceRequest::Capture {
                    observer: Observer::Omniscient,
                },
            ),
            (
                "outputs",
                EvidenceRequest::Outputs {
                    observer: Observer::Omniscient,
                },
            ),
        ] {
            let evidence = desktop_read::evidence(&opened, binding, arm, request, true).unwrap();
            assert_eq!(evidence["body"]["kind"], kind);
            assert_eq!(evidence["generation_grant"], false);
            assert!(encode(&evidence).unwrap().len() <= 256 * 1024);
        }
        assert_eq!(
            contexts(&engine(&db(&target, name, INDEX, f.kind), &current_scope()).unwrap()),
            context
        );
    }
    let diagnostics =
        desktop_read::diagnostics(&opened, binding, Observer::Omniscient, true).unwrap();
    keys(
        &diagnostics,
        &[
            "version",
            "kind",
            "source_protocol_version",
            "constructions",
            "binding",
            "lane",
            "completed",
            "rows",
            "physical_setups",
            "physical_setup_ms",
            "left_charged_ms",
            "right_charged_ms",
            "left_reserved_roles",
            "right_reserved_roles",
            "human_reviewed",
            "human_rubric",
            "quality_accepted",
            "unavailable",
        ],
    );
    assert_eq!(diagnostics["version"], 3);
    assert_eq!(diagnostics["source_protocol_version"], 4);
    assert_eq!(diagnostics["human_rubric"], "not_reviewed");
    let row_keys = [
        "turn",
        "arm",
        "phase",
        "error",
        "expected",
        "passed",
        "failures",
        "quality_flags",
        "roles",
        "roles_known",
        "elapsed_ms",
        "actual_receipt_sha256",
        "construction",
        "construction_evidence_status",
        "construction_evidence_reason",
        "construction_matches",
        "privacy_evidence_status",
        "fallback",
        "repairs",
        "recovered_without_checkpoint",
        "first_final_response_ms",
        "commit_elapsed_ms",
        "narrator_prompt_sha256",
        "narrator_schema_sha256",
        "scene_frame_sha256",
    ];
    assert_eq!(
        diagnostics["rows"].as_array().unwrap().len(),
        report["rows"].as_array().unwrap().len()
    );
    for (row, actual) in diagnostics["rows"]
        .as_array()
        .unwrap()
        .iter()
        .zip(report["rows"].as_array().unwrap())
    {
        keys(row, &row_keys);
        for key in row_keys {
            assert_eq!(
                row[key], actual[key],
                "actual V4 diagnostic projection {key}"
            );
        }
        assert!(
            row.get("narration").is_none()
                && row.get("privacy_passed").is_none()
                && row.get("literal_source_units").is_none()
        );
    }
    assert!(encode(&diagnostics).unwrap().len() <= 256 * 1024);
    drop(opened);
    unchanged(&f.root, &before);
}

#[test]
fn permission_precedes_binding_and_corrupt_files_and_reader_lock_is_not_an_execution_capability() {
    let f = Fixture::new(
        "access-precedence",
        comparison::ComparisonKind::ContinuousRollout,
    );
    let (target, report) = f.run(INDEX, Arm::Left, "selected4-access");
    let mut before = inventory(&f.root);
    let opened = desktop_read::open_read_only(&target).unwrap();
    let binding = desktop_read::summary(&opened, true).unwrap()["binding"]
        .as_str()
        .unwrap()
        .to_owned();
    assert_eq!(refused(desktop_read::open_read_only(&target)), "RunBusy");
    assert_eq!(
        refused(resume_selected(
            &target,
            &f.source,
            report["binding"].as_str().unwrap(),
            &Cancellation::default()
        )),
        "RunBusy"
    );
    let path = cp(&target, "right", INDEX);
    fs::write(&path, b"{malformed").unwrap();
    before.insert(
        path.strip_prefix(&f.root).unwrap().into(),
        Some(b"{malformed".to_vec()),
    );
    assert_eq!(refused(desktop_read::summary(&opened, false)), "Forbidden");
    for request in [
        EvidenceRequest::Receipt {
            observer: Observer::Player,
        },
        EvidenceRequest::Capture {
            observer: Observer::Character { id: "mira".into() },
        },
        EvidenceRequest::Outputs {
            observer: Observer::Player,
        },
    ] {
        assert_eq!(
            refused(desktop_read::evidence(
                &opened,
                "bad",
                Arm::Left,
                request,
                true
            )),
            "Forbidden"
        );
    }
    for request in [
        EvidenceRequest::Receipt {
            observer: Observer::Omniscient,
        },
        EvidenceRequest::Capture {
            observer: Observer::Omniscient,
        },
        EvidenceRequest::Outputs {
            observer: Observer::Omniscient,
        },
    ] {
        assert_eq!(
            refused(desktop_read::evidence(
                &opened,
                "bad",
                Arm::Left,
                request,
                false
            )),
            "Forbidden"
        );
    }
    assert_eq!(
        refused(desktop_read::evidence(
            &opened,
            "bad",
            Arm::Left,
            query(Edge::Before, Observer::Player, View::History),
            false
        )),
        "Forbidden"
    );
    assert_eq!(
        refused(desktop_read::diagnostics(
            &opened,
            "bad",
            Observer::Player,
            true
        )),
        "Forbidden"
    );
    assert_eq!(
        refused(desktop_read::diagnostics(
            &opened,
            "bad",
            Observer::Omniscient,
            false
        )),
        "Forbidden"
    );
    assert_eq!(
        refused(desktop_read::evidence(
            &opened,
            report["binding"].as_str().unwrap(),
            Arm::Left,
            EvidenceRequest::Receipt {
                observer: Observer::Omniscient
            },
            true
        )),
        "SnapshotMismatch"
    );
    refused(desktop_read::evidence(
        &opened,
        &binding,
        Arm::Left,
        EvidenceRequest::Receipt {
            observer: Observer::Omniscient,
        },
        true,
    ));
    drop(opened);
    unchanged(&f.root, &before);
}

#[test]
fn strict_manifest_checkpoint_and_accounting_tamper_refuse_without_repair_and_caches_do_not_override_inspection(
) {
    let f = Fixture::new(
        "tamper-template",
        comparison::ComparisonKind::ContinuousRollout,
    );
    let (target, report) = f.run(INDEX, Arm::Left, "selected4-tamper");
    let template = inventory(&target);
    for fault in [
        "manifest-extra",
        "manifest-duplicate",
        "manifest-version",
        "manifest-source-version",
        "missing-null",
        "manifest-cap",
        "checkpoint-cap",
        "checkpoint-request",
        "ledger",
        "capture",
        "recording",
        "raw",
        "store-suffix",
    ] {
        let altered = f.root.join(fault);
        copied(&template, &altered);
        let manifest_path = altered.join("selected.json");
        let mut manifest = value(&manifest_path);
        match fault {
            "manifest-extra" => {
                manifest["opaque"] = json!({"generation_grant":true});
                fs::write(&manifest_path, encode(&manifest).unwrap()).unwrap();
            }
            "manifest-duplicate" => {
                let bytes = fs::read(&manifest_path).unwrap();
                let text = std::str::from_utf8(&bytes).unwrap();
                fs::write(
                    &manifest_path,
                    format!(
                        "{{\"version\":3,{}",
                        text.trim_start().strip_prefix('{').unwrap()
                    ),
                )
                .unwrap();
            }
            "manifest-version" => {
                manifest["version"] = json!(2);
                fs::write(&manifest_path, encode(&manifest).unwrap()).unwrap();
            }
            "manifest-source-version" => {
                manifest["source_protocol_version"] = json!(3);
                fs::write(&manifest_path, encode(&manifest).unwrap()).unwrap();
            }
            "missing-null" => {
                manifest
                    .as_object_mut()
                    .unwrap()
                    .remove("source_reference_sha256");
                fs::write(&manifest_path, encode(&manifest).unwrap()).unwrap();
            }
            "manifest-cap" => {
                let mut bytes = fs::read(&manifest_path).unwrap();
                bytes.resize(128 * 1024 + 1, b' ');
                fs::write(&manifest_path, bytes).unwrap();
            }
            "checkpoint-cap" => {
                let path = cp(&altered, "left", INDEX);
                let mut bytes = fs::read(&path).unwrap();
                bytes.resize(256 * 1024 + 1, b' ');
                fs::write(path, bytes).unwrap();
            }
            "checkpoint-request" => {
                let path = cp(&altered, "right", INDEX);
                let mut checkpoint = value(&path);
                checkpoint["request"]["turn"] = json!("different-turn");
                fs::write(path, encode(&checkpoint).unwrap()).unwrap();
            }
            "ledger" => {
                let path = altered.join("right/admission-00-settled.json");
                let mut settlement = value(&path);
                settlement["binding"] = json!("a".repeat(64));
                fs::write(path, encode(&settlement).unwrap()).unwrap();
            }
            "capture" | "recording" | "raw" => {
                let checkpoint = value(&cp(&altered, "right", INDEX));
                let path = if fault == "capture" {
                    altered
                        .join("right")
                        .join(checkpoint["capture_file"].as_str().unwrap())
                } else {
                    let recording_path = altered
                        .join("right")
                        .join(checkpoint["recording_file"].as_str().unwrap());
                    if fault == "recording" {
                        recording_path
                    } else {
                        let recording = value(&recording_path);
                        altered
                            .join("right")
                            .join(recording["raw"][0]["file"].as_str().unwrap())
                    }
                };
                fs::write(path, b"synthetic corrupt retained evidence").unwrap();
            }
            "store-suffix" => {
                let path = db(&altered, "right", INDEX, f.kind);
                let mut store = Store::open_application(&path).unwrap();
                let full = store.resume(&current_scope()).unwrap().engine;
                let request = full.request(
                    "selected4-unrelated-suffix",
                    Intent::Actions(vec![Command::Wait { ticks: 1 }]),
                );
                let proposal = Engine::proposal(&request).unwrap();
                let approved = full.preview(&request, &proposal).unwrap();
                store.begin_turn(&request).unwrap();
                store
                    .commit_turn(&request, &proposal, approved.narration())
                    .unwrap();
            }
            _ => unreachable!(),
        }
        let before = inventory(&altered);
        refused(inspect_selected(&altered));
        refused(desktop_read::open_read_only(&altered));
        unchanged(&altered, &before);
    }
    let cached = f.root.join("cache-controls");
    copied(&template, &cached);
    fs::write(cached.join("report.json"), b"not authority").unwrap();
    fs::write(
        cached.join("report.html"),
        b"<script>synthetic cached text</script>",
    )
    .unwrap();
    let before = inventory(&cached);
    assert_eq!(
        serde_json::to_value(inspect_selected(&cached).unwrap()).unwrap(),
        report
    );
    unchanged(&cached, &before);
    let oversized_directory = f.root.join("file-count");
    copied(&template, &oversized_directory);
    for n in 0..513 {
        fs::write(
            oversized_directory
                .join("right")
                .join(format!("bounded-extra-{n:03}.bin")),
            b"x",
        )
        .unwrap();
    }
    assert_eq!(
        refused(desktop_read::open_read_only(&oversized_directory)),
        "ReportBudget"
    );
}

#[test]
fn historical_source_is_inspectable_but_not_rerunnable_and_completed_work_ignores_exhausted_admission_capacity(
) {
    let f = Fixture::new(
        "historical-source",
        comparison::ComparisonKind::ContinuousRollout,
    );
    let path = f.source.join("run.json");
    let mut manifest = value(&path);
    manifest["source_sha256"] = json!("0".repeat(64));
    manifest["binding"]["source_sha256"] = json!("0".repeat(64));
    fs::write(&path, encode(&manifest).unwrap()).unwrap();
    let before = inventory(&f.root);
    assert!(
        !source4::inspect_comparison(&f.source)
            .unwrap()
            .source_matches
    );
    let fresh_binding = source_binding(&f.source);
    assert_eq!(
        refused(prepare_selected(
            &f.source,
            &fresh_binding,
            &row(INDEX, Arm::Left),
            SelectedIntent {
                client_id: "historical-refusal".into(),
                lane: SelectedLane::ScriptedBaseline
            },
            &Cancellation::default()
        )),
        "SourceMismatch"
    );
    unchanged(&f.root, &before);
    let f = Fixture::new(
        "completed-capacity",
        comparison::ComparisonKind::ContinuousRollout,
    );
    let (target, _) = f.run(INDEX, Arm::Left, "completed-no-admission");
    let binding = selected_binding(&target);
    // Trusted actual Ledger controls, not provider activity or invented cost:
    // create/finish measured preparation records up to the existing limit.
    for arm in ARMS {
        let mut ledger = Ledger::load(&target.join(arm), &binding).unwrap();
        while ledger.invocations < 32 {
            ledger.begin_invocation().unwrap();
            ledger.finish().unwrap();
        }
        assert_eq!(ledger.invocations, 32);
        assert_eq!(ledger.admissions, 1);
    }
    let expected = serde_json::to_value(inspect_selected(&target).unwrap()).unwrap();
    let before = inventory(&f.root);
    assert_eq!(
        serde_json::to_value(
            resume_selected(&target, &f.source, &binding, &Cancellation::default()).unwrap()
        )
        .unwrap(),
        expected
    );
    unchanged(&f.root, &before);
}

#[test]
fn old_selected_one_and_two_artifacts_are_actual_public_products_and_never_relabelled_as_selected_three(
) {
    for version in [1, 2] {
        let dir = root("old-version-regression");
        let source = dir.join("source");
        let target = dir.join("selected");
        let cancel = Cancellation::default();
        let kind = comparison::ComparisonKind::ContinuousRollout;
        let (binding, report) = if version == 1 {
            comparison::run_comparison(
                &source,
                false,
                kind,
                &cancel,
                1,
                LaneFactory::ScriptedBaseline,
                None,
            )
            .unwrap();
            let opened = comparison::desktop_api::open_read_only(&source).unwrap();
            let summary = comparison::desktop_api::summary(&opened, true).unwrap();
            drop(opened);
            let binding = summary["binding"].as_str().unwrap().to_owned();
            let plan = comparison::selected::prepare_selected(
                &source,
                &binding,
                &row(INDEX, Arm::Left),
                SelectedIntent {
                    client_id: "old-selected-one".into(),
                    lane: SelectedLane::ScriptedBaseline,
                },
                &cancel,
            )
            .unwrap();
            (
                binding,
                serde_json::to_value(
                    comparison::selected::run_selected(plan, &target, &cancel).unwrap(),
                )
                .unwrap(),
            )
        } else {
            comparison::literal_v3::run_comparison(
                &source,
                false,
                kind,
                &cancel,
                1,
                LaneFactory::ScriptedBaseline,
                None,
            )
            .unwrap();
            let opened = comparison::literal_v3::desktop_api::open_read_only(&source).unwrap();
            let summary = comparison::literal_v3::desktop_api::summary(&opened, true).unwrap();
            drop(opened);
            let binding = summary["binding"].as_str().unwrap().to_owned();
            let plan = comparison::literal_v3::selected_v2::prepare_selected(
                &source,
                &binding,
                &row(INDEX, Arm::Left),
                SelectedIntent {
                    client_id: "old-selected-two".into(),
                    lane: SelectedLane::ScriptedBaseline,
                },
                &cancel,
            )
            .unwrap();
            (
                binding,
                serde_json::to_value(
                    comparison::literal_v3::selected_v2::run_selected(plan, &target, &cancel)
                        .unwrap(),
                )
                .unwrap(),
            )
        };
        assert_eq!(report["version"], version);
        let before = inventory(&dir);
        refused(inspect_selected(&target));
        refused(desktop_read::open_read_only(&target));
        refused(prepare_selected(
            &source,
            &binding,
            &row(INDEX, Arm::Left),
            SelectedIntent {
                client_id: "no-version-relabel".into(),
                lane: SelectedLane::ScriptedBaseline,
            },
            &cancel,
        ));
        let old = if version == 1 {
            serde_json::to_value(comparison::selected::inspect_selected(&target).unwrap()).unwrap()
        } else {
            serde_json::to_value(
                comparison::literal_v3::selected_v2::inspect_selected(&target).unwrap(),
            )
            .unwrap()
        };
        assert_eq!(old, report);
        unchanged(&dir, &before);
    }
}

#[test]
fn actual_guard_dependency_and_optional_source_companion_do_not_invent_receipts_or_selected_diagnostics(
) {
    let f = Fixture::new("actual-guard", comparison::ComparisonKind::PairedSnapshots);
    let report = source4::inspect_comparison(&f.source).unwrap();
    let guard = comparison::suite()
        .unwrap()
        .steps()
        .iter()
        .position(|step| {
            matches!(
                step.expected(),
                crate::memory_comparison::Expected::GuardRejected(_)
            )
        })
        .unwrap();
    assert!(guard < 12);
    let (_, selected) = f.run(guard, Arm::Right, "selected4-guard");
    for row in selected["rows"].as_array().unwrap() {
        assert_ne!(row["phase"], "committed");
        assert_eq!(row["roles"], 0);
        assert!(row["actual_receipt_sha256"].is_null());
        assert_eq!(row["construction_evidence_status"], "not_applicable_guard");
    }
    assert!(!report.quality_accepted);
    let failed = public_source(comparison::ComparisonKind::ContinuousRollout, true);
    let actual = source4::inspect_comparison(failed).unwrap();
    let dependency = actual
        .turns
        .iter()
        .find(|row| row.phase == "not_run_dependency")
        .expect("actual public WrongCommand source has a dependency-only row");
    let index = comparison::suite()
        .unwrap()
        .steps()
        .iter()
        .position(|step| step.id() == dependency.turn)
        .unwrap();
    let f = Fixture::from_source(
        "actual-dependency",
        failed,
        comparison::ComparisonKind::ContinuousRollout,
    );
    let (_, selected) = f.run(index, Arm::Left, "selected4-dependency");
    assert_eq!(selected["completed"], true);
    for row in selected["rows"].as_array().unwrap() {
        assert_eq!(row["phase"], "not_run_dependency");
        assert_eq!(row["roles"], 0);
        assert!(row["actual_receipt_sha256"].is_null());
    }
    let f = Fixture::new(
        "optional-companion",
        comparison::ComparisonKind::ContinuousRollout,
    );
    fs::write(
        f.source.join("narration-diagnostics-v1.json"),
        b"{not a validated companion",
    )
    .unwrap();
    let before = inventory(&f.source);
    let (target, _) = f.run(INDEX, Arm::Left, "selected4-no-companion-authority");
    assert!(!target.join("narration-diagnostics-v1.json").exists());
    unchanged(&f.source, &before);
}
