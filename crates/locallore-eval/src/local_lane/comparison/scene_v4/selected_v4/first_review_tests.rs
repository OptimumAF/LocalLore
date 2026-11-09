// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent FIRST frozen before selected4 producer. SOURCE ONLY / UNCOMPILED / UNRUN.
//! Real SCRIPTED Core/Store histories prove input binding/recovery, never native generation.
//! No new runtime provider/cleanup owner or production hook. Trap assets must never be reached.
//! Future admitted fixtures are retained; no deletion/retry, and no fixtures exist at authorship.
use super::prepare_selected;
use crate::local_lane::comparison::{
    self as comparison,
    desktop_api::{Arm, RowId},
    selected::{SelectedIntent, SelectedLane},
};
use crate::Result;
use locallore::inference::Cancellation;
use std::{
    fs,
    path::PathBuf,
    sync::atomic::{AtomicUsize, Ordering},
};

#[cfg(feature = "local-model")]
use super::{
    desktop_read, inspect_selected, inspect_work, new_destination, open_destination,
    preflight, prepared_metadata, resume_native_selected, run_native_selected,
    PreparedSelectedPlan,
};
#[cfg(feature = "local-model")]
use crate::{
    digest, encode, engine,
    local_lane::{
        comparison::{scene_v4 as source4, selected as shared},
        LaneFactory, Ledger, TestFault,
    },
};
#[cfg(feature = "local-model")]
use locallore::{
    engine::Engine,
    inspection_query::{self, Observer, Query, View, MAX_ROWS},
};
#[cfg(feature = "local-model")]
use locallore_local_runtime::LocalRuntime;
#[cfg(feature = "local-model")]
use serde_json::{json, Value};
#[cfg(feature = "local-model")]
use std::{
    collections::{BTreeMap, BTreeSet},
    sync::{Arc, Mutex, OnceLock},
    time::Instant,
    path::Path,
};

const INDEX: usize = 4;
static NEXT: AtomicUsize = AtomicUsize::new(0);
fn fixture_root(label: &str) -> PathBuf {
    // Reuse the future admitted D: TEMP parent, not selected3's existing
    // LOCALLORE_SELECTED4_TEST_ROOT selector. This distinct prefix is test-only.
    let parent = fs::canonicalize(std::env::temp_dir()).expect("admitted test parent");
    assert!(parent.is_absolute() && parent.is_dir());
    for ancestor in parent.ancestors() {
        let info = fs::symlink_metadata(ancestor).unwrap();
        assert!(info.is_dir() && !info.file_type().is_symlink());
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt;
            assert_eq!(info.file_attributes() & 0x400, 0);
        }
    }
    let root = parent.join(format!(
        "native-selected4-first-{label}-{}-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos(),
        NEXT.fetch_add(1, Ordering::Relaxed)
    ));
    fs::create_dir(&root).unwrap();
    root
}
fn row(index: usize, arm: Arm) -> RowId {
    RowId { turn: comparison::suite().unwrap().steps()[index].id().into(), arm }
}
fn refused<T>(result: Result<T>) -> String {
    let error = result.err().expect("expected finite refusal");
    assert!(!error.is_empty() && error.len() <= 96 &&
        error.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'_'));
    error
}
#[test]
fn n01_cancel_identity_lane_and_feature_precede_source_target_and_asset_io() {
    let root = fixture_root("pure-admission");
    let missing = root.join("missing-source");
    let intent = || SelectedIntent {
        client_id: "native4-admission".into(), lane: SelectedLane::ApprovedNative,
    };
    let cancel = Cancellation::default(); cancel.cancel();
    assert_eq!(refused(prepare_selected(&missing, "bad", &row(INDEX, Arm::Left),
        SelectedIntent { client_id: String::new(), lane: SelectedLane::ScriptedBaseline },
        &cancel)), "Interrupted");
    for (client, binding) in [
        ("", "a".repeat(64)), ("bad_client", "a".repeat(64)),
        ("valid-client", "bad".into()),
    ] {
        assert_eq!(refused(prepare_selected(&missing, &binding, &row(INDEX, Arm::Left),
            SelectedIntent { client_id: client.into(), lane: SelectedLane::ApprovedNative },
            &Cancellation::default())), "SelectedIdentity");
    }
    assert_eq!(refused(prepare_selected(&missing, &"a".repeat(64), &row(INDEX, Arm::Right),
        SelectedIntent { client_id: "native4-lane".into(), lane: SelectedLane::ScriptedBaseline },
        &Cancellation::default())), "SelectedLaneMismatch");
    let unknown = RowId { turn: "not-a-corpus-row".into(), arm: Arm::Left };
    #[cfg(not(feature = "local-model"))]
    assert_eq!(refused(prepare_selected(&missing, &"a".repeat(64), &unknown,
        intent(), &Cancellation::default())), "NativeFeatureUnavailable");
    #[cfg(feature = "local-model")]
    assert_eq!(refused(prepare_selected(&missing, &"a".repeat(64), &unknown,
        intent(), &Cancellation::default())), "UnknownRow");
    assert!(!missing.exists() && fs::read_dir(&root).unwrap().next().is_none());
}

#[cfg(feature = "local-model")]
const ARMS: [&str; 2] = ["left", "right"];
#[cfg(feature = "local-model")]
type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;
#[cfg(feature = "local-model")]
fn inventory(root: &Path) -> Inventory {
    fn walk(base: &Path, dir: &Path, depth: usize, total: &mut usize, out: &mut Inventory) {
        assert!(depth <= 12);
        for item in fs::read_dir(dir).unwrap() {
            assert!(out.len() < 8192);
            let path = item.unwrap().path();
            let info = fs::symlink_metadata(&path).unwrap();
            assert!(!info.file_type().is_symlink());
            #[cfg(windows)]
            {
                use std::os::windows::fs::MetadataExt;
                assert_eq!(info.file_attributes() & 0x400, 0);
            }
            let name = path.strip_prefix(base).unwrap().to_owned();
            if info.is_dir() {
                assert!(out.insert(name, None).is_none());
                walk(base, &path, depth + 1, total, out);
            } else {
                assert!(info.is_file() && info.len() <= 8 * 1024 * 1024);
                let bytes = fs::read(&path).unwrap();
                *total = total.checked_add(bytes.len()).unwrap();
                assert!(*total <= 64 * 1024 * 1024);
                assert!(out.insert(name, Some(bytes)).is_none());
            }
        }
    }
    let mut out = Inventory::new();
    walk(root, root, 0, &mut 0, &mut out);
    out
}
#[cfg(feature = "local-model")]
fn unchanged(root: &Path, before: &Inventory) {
    // Never read an opaque source/destination run.lock while its owner is live.
    assert!(inventory(root) == *before, "retained fixture changed");
}
#[cfg(feature = "local-model")]
fn copy_tree(before: &Inventory, destination: &Path) {
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
#[cfg(feature = "local-model")]
fn value(path: &Path) -> Value {
    serde_json::from_slice(&fs::read(path).unwrap()).unwrap()
}
#[cfg(feature = "local-model")]
fn keys(value: &Value, expected: &[&str]) {
    assert!(value.as_object().unwrap().keys().map(String::as_str).collect::<BTreeSet<_>>() ==
        expected.iter().copied().collect::<BTreeSet<_>>(), "closed JSON keys");
}
#[cfg(feature = "local-model")]
fn cp(dir: &Path, arm: &str) -> PathBuf {
    comparison::checkpoint_path(&dir.join(arm), INDEX)
}
#[cfg(feature = "local-model")]
fn db(dir: &Path, arm: &str, kind: comparison::ComparisonKind) -> PathBuf {
    comparison::database(&dir.join(arm), INDEX, kind)
}
#[cfg(feature = "local-model")]
fn source_binding(source: &Path) -> String {
    let opened = source4::desktop_api::open_read_only(source).unwrap();
    let summary = source4::desktop_api::summary(&opened, true).unwrap();
    assert_eq!(summary["protocol_version"], 4);
    assert_eq!(summary["read_only"], true);
    assert_eq!(summary["execution_available"], false);
    summary["binding"].as_str().unwrap().into()
}
#[cfg(feature = "local-model")]
fn original_source(kind: comparison::ComparisonKind, divergent: bool) -> &'static Path {
    static PAIRED: OnceLock<std::result::Result<PathBuf, ()>> = OnceLock::new();
    static ROLLOUT: OnceLock<std::result::Result<PathBuf, ()>> = OnceLock::new();
    static DIVERGENT: OnceLock<std::result::Result<PathBuf, ()>> = OnceLock::new();
    assert!(!divergent || kind == comparison::ComparisonKind::ContinuousRollout);
    let slot = if divergent { &DIVERGENT } else if kind == comparison::ComparisonKind::PairedSnapshots {
        &PAIRED
    } else { &ROLLOUT };
    slot.get_or_init(|| std::panic::catch_unwind(|| {
        let parent = fixture_root(if divergent { "real-divergent-source" } else { "public-source" });
        let dir = parent.join("source");
        if divergent {
            // Explicit b4344405 allowance: reuse the existing real private
            // SOURCE driver, never edit receipts/checkpoints to manufacture it.
            let manifest = source4::Manifest::new(kind,
                LaneFactory::ScriptedBaseline.profile().unwrap(), None).unwrap();
            let mut session = source4::Session4::open(
                &dir, false, manifest, None, Instant::now()).unwrap();
            session.begin_invocations().unwrap();
            comparison::turn_execution::record_setup(&mut session.ledgers,
                comparison::turn_execution::Setup {
                    version: 4, dir: &session.dir, key: &session.key,
                    native: false, physical_ms: 0, status: "scripted", load: None,
                }).unwrap();
            let corpus = comparison::suite().unwrap();
            for index in 0..6 {
                for (arm, name) in ARMS.iter().copied().enumerate() {
                    let began = Instant::now();
                    let arm_dir = dir.join(name);
                    let path = comparison::database(&arm_dir, index, kind);
                    comparison::ensure_database(&path, corpus.seed(), &[]).unwrap();
                    let factory = if index == 0 && arm == 0 {
                        LaneFactory::TestFault(TestFault::WrongCommand)
                    } else { LaneFactory::ScriptedBaseline };
                    let turn = source4::execute_turn4(source4::Job4 {
                        dir: &arm_dir, path: &path, index, arm: name,
                        construction: source4::CONSTRUCTIONS[arm], binding: &session.key,
                        step: &corpus.steps()[index], factory: &factory,
                        cancel: &Cancellation::default(), diagnostics: false,
                    }, &mut session.ledgers[arm]).unwrap();
                    if index == 0 && arm == 0 {
                        assert_eq!(turn.row.phase, "failed");
                        assert_eq!(turn.before_head, turn.after_head);
                    }
                    if index == 0 && arm == 1 {
                        assert_eq!(turn.row.phase, "committed");
                    }
                    session.turns[arm].push(turn);
                    session.ledgers[1 - arm].exclude_measured_interval(
                        began.elapsed().as_millis().min(u64::MAX as u128) as u64).unwrap();
                }
            }
            comparison::saved(&dir.join("scene-00.json"),
                &source4::scene_data4(&dir, &session.key, 0).unwrap(), 4096).unwrap();
            let report = session.finish().unwrap();
            assert_eq!((report.completed_scenes, report.turns.len()), (1, 12));
        } else {
            let reference = if kind == comparison::ComparisonKind::PairedSnapshots {
                let path = parent.join("reference-owner");
                comparison::prepare_reference(&path, &Cancellation::default()).unwrap();
                Some(comparison::open_reference(&path).unwrap())
            } else { None };
            let report = source4::run_comparison(&dir, false, kind,
                &Cancellation::default(), 1, LaneFactory::ScriptedBaseline,
                reference.as_ref()).unwrap();
            assert_eq!((report.version, report.completed_scenes, report.turns.len()), (4, 1, 12));
        }
        source4::inspect_comparison(&dir).unwrap();
        dir
    }).map_err(|_| ())).as_ref()
        .expect("original source construction failed; retained, no replacement").as_path()
}
#[cfg(feature = "local-model")]
struct Fixture { root: PathBuf, source: PathBuf, kind: comparison::ComparisonKind }
#[cfg(feature = "local-model")]
impl Fixture {
    fn new(label: &str, kind: comparison::ComparisonKind, divergent: bool) -> Self {
        let original = inventory(original_source(kind, divergent));
        let root = fixture_root(label);
        let source = root.join("source");
        copy_tree(&original, &source);
        Self { root, source, kind }
    }
    fn plan(&self, client: &str) -> PreparedSelectedPlan {
        prepare_selected(&self.source, &source_binding(&self.source), &row(INDEX, Arm::Right),
            SelectedIntent { client_id: client.into(), lane: SelectedLane::ApprovedNative },
            &Cancellation::default()).unwrap()
    }
}
#[cfg(feature = "local-model")]
struct Trap { assets: Arc<AtomicUsize> }
#[cfg(feature = "local-model")]
impl shared::SelectedNativeReservation for Trap {
    fn assets(&self) -> crate::local_lane::NativeAssets<'_> {
        self.assets.fetch_add(1, Ordering::SeqCst);
        panic!("native-selected4 FIRST reached forbidden assets");
    }
    fn retain_uncertain(&mut self, owner: Arc<Mutex<LocalRuntime>>)
        -> std::result::Result<(), Arc<Mutex<LocalRuntime>>> { Err(owner) }
}
#[cfg(feature = "local-model")]
fn native_error<T>(result: std::result::Result<T, shared::SelectedNativeFailure<Trap>>)
    -> shared::SelectedNativeFailure<Trap> {
    match result { Ok(_) => panic!("expected finite selected4 refusal"), Err(error) => error }
}


#[cfg(feature = "local-model")]
const MANIFEST_KEYS: &[&str] = &[
    "version", "run_type", "source_protocol_version", "arms", "client_id", "binding",
    "source_binding", "source_kind", "source_profile", "source_native", "selection",
    "lane", "profile", "suite_sha256", "source_sha256", "source_reference_sha256", "source_inputs",
];
#[cfg(feature = "local-model")]
fn reseal(manifest: &mut Value) {
    manifest.as_object_mut().unwrap().remove("binding");
    manifest["binding"] = json!(digest(&encode(manifest).unwrap()));
}
#[cfg(feature = "local-model")]
fn actual_before(f: &Fixture, arm: &str) -> Engine {
    let checkpoint = value(&cp(&f.source, arm));
    let scope = comparison::suite().unwrap().seed().scope.clone();
    engine(&db(&f.source, arm, f.kind), &scope).unwrap()
        .at_revision(checkpoint["before_head"].as_u64().unwrap()).unwrap()
}
#[cfg(feature = "local-model")]
fn check_plan_inputs(f: &Fixture, plan: &PreparedSelectedPlan) {
    let m = serde_json::to_value(&plan.manifest).unwrap();
    keys(&m, MANIFEST_KEYS);
    assert_eq!(m["version"], 4);
    assert_eq!(m["source_protocol_version"], 4);
    assert_eq!(m["lane"], "native_selected_case");
    assert_eq!(m["run_type"], "selected_case");
    assert_eq!(m["source_native"], false);
    assert!(m["source_profile"] == value(&f.source.join("run.json"))["profile"]);
    assert!(m["profile"] == serde_json::to_value(SelectedLane::ApprovedNative.profile().unwrap()).unwrap());
    assert!(m["arms"] == serde_json::to_value(crate::memory_comparison_v4::current_arm_descriptors()).unwrap());
    let mut unsigned = m.clone(); unsigned.as_object_mut().unwrap().remove("binding");
    assert_eq!(m["binding"], digest(&encode(&unsigned).unwrap()));
    assert_ne!(m["binding"], m["source_binding"]);
    for (arm_index, arm) in ARMS.iter().enumerate() {
        let before = actual_before(f, arm);
        let source_cp = value(&cp(&f.source, arm));
        assert_eq!(plan.before[arm_index].revision(), before.revision());
        assert!(plan.before[arm_index].receipts() == before.receipts(), "actual arm prefix");
        assert!(plan.before[arm_index].canonical_bytes() == before.canonical_bytes());
        assert!(m["source_inputs"][arm_index]["request"] == source_cp["request"]);
        assert_eq!(m["source_inputs"][arm_index]["prefix_sha256"],
            digest(&encode(before.receipts()).unwrap()));
        assert_eq!(m["source_inputs"][arm_index]["input_semantic_sha256"],
            source_cp["row"]["input_semantic_sha256"]);
    }
    let metadata = prepared_metadata(plan).unwrap();
    keys(&metadata, &["version", "kind", "source_protocol_version", "binding",
        "source_binding", "lane", "selection", "arms", "constructions"]);
    assert_eq!(metadata["version"], 4);
    assert_eq!(metadata["kind"], "selected_prepared");
    assert_eq!(metadata["source_protocol_version"], 4);
    assert_eq!(metadata["lane"], "native_selected_case");
    assert_eq!(metadata["binding"], m["binding"]);
    assert_eq!(metadata["source_binding"], m["source_binding"]);
    assert!(metadata["constructions"] == m["arms"]);
    assert!(encode(&metadata).unwrap().len() <= 16 * 1024);
    for (index, arm) in ARMS.iter().enumerate() {
        keys(&metadata["arms"][index],
            &["arm", "scope", "before_head", "prefix_sha256", "input_semantic_sha256"]);
        assert_eq!(metadata["arms"][index]["arm"], *arm);
        for key in ["scope", "before_head", "prefix_sha256", "input_semantic_sha256"] {
            assert!(metadata["arms"][index][key] == m["source_inputs"][index][key]);
        }
    }
    for forbidden in ["generation_grant", "request", "source_inputs", "profile", "rows", "report"] {
        assert!(metadata.get(forbidden).is_none());
    }
}

#[cfg(feature = "local-model")]
#[test]
fn n02_closed_manifest4_native_codec_preserves_selected3_and_scripted_source_provenance() {
    let f = Fixture::new("closed-codec", comparison::ComparisonKind::ContinuousRollout, false);
    let source_before = inventory(&f.source);
    let p = f.plan("native4-closed-manifest");
    check_plan_inputs(&f, &p);
    let target = f.root.join("selected-native4");
    let destination = new_destination(&p, &target).unwrap();
    drop(destination); drop(p);
    let reopened = open_destination(&target).unwrap();
    assert_eq!(reopened.manifest.binding,
        value(&target.join("selected.json"))["binding"].as_str().unwrap());
    drop(reopened);
    let template = inventory(&target);
    for fault in ["extra", "duplicate", "version", "protocol", "lane", "missing-null",
        "bad-arm", "swapped-arms", "input-head"] {
        let altered = f.root.join(format!("bad-{fault}"));
        copy_tree(&template, &altered);
        let file = altered.join("selected.json");
        let mut m = value(&file);
        match fault {
            "extra" => { m["opaque"] = json!({"generation_grant":true}); }
            "version" => { m["version"] = json!(3); }
            "protocol" => { m["source_protocol_version"] = json!(3); }
            "lane" => { m["lane"] = json!("scripted_selected_case"); }
            "missing-null" => { m.as_object_mut().unwrap().remove("source_reference_sha256"); }
            "bad-arm" => { m["arms"][0]["version"] = json!(99); }
            "swapped-arms" => { m["arms"].as_array_mut().unwrap().swap(0, 1); }
            "input-head" => { m["source_inputs"][0]["before_head"] = json!(0); }
            "duplicate" => {}
            _ => unreachable!(),
        }
        reseal(&mut m);
        if fault == "duplicate" {
            let text = String::from_utf8(encode(&m).unwrap()).unwrap();
            fs::write(&file, format!("{{\"version\":4,{}", text.strip_prefix('{').unwrap())).unwrap();
        } else { fs::write(&file, encode(&m).unwrap()).unwrap(); }
        let before = inventory(&altered);
        refused(inspect_selected(&altered));
        refused(desktop_read::open_read_only(&altered));
        unchanged(&altered, &before);
    }
    // Actual selected3 still refuses native before trying the nonexistent source.
    assert_eq!(refused(source4::selected_v3::prepare_selected(
        &f.root.join("missing"), &"a".repeat(64), &row(INDEX, Arm::Left),
        SelectedIntent { client_id: "old3-native-denial".into(), lane: SelectedLane::ApprovedNative },
        &Cancellation::default())), "SelectedNativeUnavailable");
    refused(source4::selected_v3::inspect_selected(&target));
    let old = f.root.join("actual-scripted-selected3");
    let old_plan = source4::selected_v3::prepare_selected(&f.source, &source_binding(&f.source),
        &row(INDEX, Arm::Left),
        SelectedIntent { client_id: "old3-retained".into(), lane: SelectedLane::ScriptedBaseline },
        &Cancellation::default()).unwrap();
    let old_report = serde_json::to_value(source4::selected_v3::run_selected(
        old_plan, &old, &Cancellation::default()).unwrap()).unwrap();
    assert_eq!(old_report["version"], 3);
    assert_eq!(old_report["physical_setups"], 0);
    refused(inspect_selected(&old));
    unchanged(&f.source, &source_before);
}

#[cfg(feature = "local-model")]
#[test]
fn n03_noninitial_paired_before_engines_are_real_reference_prefixes_and_source_is_immutable() {
    let f = Fixture::new("paired-prefix", comparison::ComparisonKind::PairedSnapshots, false);
    let before = inventory(&f.source);
    let plan = f.plan("native4-paired-prefix");
    check_plan_inputs(&f, &plan);
    let reference = comparison::open_reference(&f.source.join("reference")).unwrap();
    let expected = reference.prefix(INDEX).unwrap();
    assert!(!expected.is_empty());
    for actual in &plan.before {
        assert!(actual.receipts() == expected, "paired accepted reference prefix");
    }
    drop(reference); drop(plan);
    unchanged(&f.source, &before);
}

#[cfg(feature = "local-model")]
#[test]
fn n04_noninitial_rollout_rederives_each_real_divergent_arm_instead_of_cloning_left() {
    let f = Fixture::new("divergent-prefix", comparison::ComparisonKind::ContinuousRollout, true);
    let before = inventory(&f.source);
    let plan = f.plan("native4-divergent-prefix");
    check_plan_inputs(&f, &plan);
    assert!(plan.before[0].receipts() != plan.before[1].receipts(),
        "real one-arm failed SOURCE turn must remain divergent");
    assert!(plan.before[0].accepted_history_basis().unwrap() !=
        plan.before[1].accepted_history_basis().unwrap());
    assert_ne!(plan.manifest.source_inputs[0].prefix_sha256,
        plan.manifest.source_inputs[1].prefix_sha256);
    drop(plan);
    unchanged(&f.source, &before);
}

#[cfg(feature = "local-model")]
#[test]
fn n05_source_locks_binding_staleness_and_historical_source_refuse_without_new_authority() {
    let f = Fixture::new("source-admission", comparison::ComparisonKind::ContinuousRollout, false);
    let before = inventory(&f.source);
    let held = source4::desktop_api::open_read_only(&f.source).unwrap();
    assert_eq!(refused(prepare_selected(&f.source, &"a".repeat(64), &row(INDEX, Arm::Left),
        SelectedIntent { client_id: "native4-source-busy".into(), lane: SelectedLane::ApprovedNative },
        &Cancellation::default())), "RunBusy");
    drop(held);
    assert_eq!(refused(prepare_selected(&f.source, &"a".repeat(64), &row(INDEX, Arm::Left),
        SelectedIntent { client_id: "native4-source-binding".into(), lane: SelectedLane::ApprovedNative },
        &Cancellation::default())), "SnapshotMismatch");
    unchanged(&f.source, &before);
    let plan = f.plan("native4-source-refresh");
    let source_cp = cp(&f.source, "left");
    fs::write(f.root.join("retained-original-checkpoint.json"), fs::read(&source_cp).unwrap()).unwrap();
    let mut changed = value(&source_cp); changed["request"]["turn"] = json!("not-the-original-turn");
    fs::write(&source_cp, encode(&changed).unwrap()).unwrap();
    let calls = AtomicUsize::new(0);
    let target = f.root.join("not-created");
    let failure = native_error(run_native_selected(plan, &target, &Cancellation::default(), || {
        calls.fetch_add(1, Ordering::SeqCst);
        Err::<Trap, _>("UnexpectedReservation".into())
    }));
    assert!(!failure.cleanup_uncertain() && !target.exists());
    assert_eq!(calls.load(Ordering::SeqCst), 0);
    let changed_before = inventory(&f.root);
    refused(prepare_selected(&f.source, &"a".repeat(64), &row(INDEX, Arm::Left),
        SelectedIntent { client_id: "native4-no-repair".into(), lane: SelectedLane::ApprovedNative },
        &Cancellation::default()));
    unchanged(&f.root, &changed_before);
    let historical = Fixture::new("historical-source", comparison::ComparisonKind::ContinuousRollout, false);
    let path = historical.source.join("run.json");
    fs::write(historical.root.join("retained-run-before-historical.json"), fs::read(&path).unwrap()).unwrap();
    let mut m = value(&path);
    m["source_sha256"] = json!("0".repeat(64)); m["binding"]["source_sha256"] = json!("0".repeat(64));
    fs::write(path, encode(&m).unwrap()).unwrap();
    assert!(!source4::inspect_comparison(&historical.source).unwrap().source_matches);
    let binding = source_binding(&historical.source);
    let historical_before = inventory(&historical.root);
    assert_eq!(refused(prepare_selected(&historical.source, &binding, &row(INDEX, Arm::Left),
        SelectedIntent { client_id: "native4-historical-no-run".into(), lane: SelectedLane::ApprovedNative },
        &Cancellation::default())), "SourceMismatch");
    unchanged(&historical.root, &historical_before);
}

#[cfg(feature = "local-model")]
#[test]
fn n06_disjoint_existing_nonordinary_target_and_source_path_drift_precede_reservation() {
    let f = Fixture::new("target-paths", comparison::ComparisonKind::PairedSnapshots, false);
    let before = inventory(&f.root);
    let calls = AtomicUsize::new(0);
    for target in [f.source.clone(), f.source.join("nested"), f.root.clone()] {
        let failure = native_error(run_native_selected(f.plan("native4-disjoint"), &target,
            &Cancellation::default(), || {
                calls.fetch_add(1, Ordering::SeqCst);
                Err::<Trap, _>("UnexpectedReservation".into())
            }));
        assert!(!failure.cleanup_uncertain());
        unchanged(&f.root, &before);
    }
    let existing = f.root.join("existing");
    fs::create_dir(&existing).unwrap(); fs::write(existing.join("sentinel"), b"unchanged").unwrap();
    let component = f.root.join("ordinary-file-not-directory");
    fs::write(&component, b"unchanged").unwrap();
    let before_paths = inventory(&f.root);
    for target in [existing, component.join("child")] {
        native_error(run_native_selected(f.plan("native4-existing-target"), &target,
            &Cancellation::default(), || {
                calls.fetch_add(1, Ordering::SeqCst);
                Err::<Trap, _>("UnexpectedReservation".into())
            }));
        unchanged(&f.root, &before_paths);
    }
    assert_eq!(calls.load(Ordering::SeqCst), 0);
    let source_before_move = inventory(&f.source);
    let p = f.plan("native4-source-path-pins");
    let retained = f.root.join("retained-source-original-path");
    match fs::rename(&f.source, &retained) {
        Ok(()) => {
            // POSIX may allow rename despite held directory pins. Keep the
            // actual old tree; the missing original source cannot authorize run.
            let target = f.root.join("not-created-after-source-move");
            native_error(run_native_selected(p, &target, &Cancellation::default(), || {
                calls.fetch_add(1, Ordering::SeqCst);
                Err::<Trap, _>("UnexpectedReservation".into())
            }));
            assert!(!target.exists());
            assert!(retained.is_dir() && !f.source.exists());
            unchanged(&retained, &source_before_move);
        }
        Err(_) => {
            // Existing Windows pins use share_mode3 (no FILE_SHARE_DELETE).
            // A refused rename is evidence of pin protection, not observed drift.
            assert!(cfg!(windows));
            drop(p);
            unchanged(&f.root, &before_paths);
        }
    }
    assert_eq!(calls.load(Ordering::SeqCst), 0);
}


#[cfg(feature = "local-model")]
#[test]
fn n07_unknown_role_and_turn_time_reservations_in_either_arm_preflight_before_other_arm_mutation() {
    for exhausted in ARMS {
        let f = Fixture::new("both-arm-unknown", comparison::ComparisonKind::ContinuousRollout, false);
        let source_before = inventory(&f.source);
        let p = f.plan("native4-both-arm-unknown");
        let target = f.root.join("selected");
        let destination = new_destination(&p, &target).unwrap();
        let binding = destination.manifest.binding.clone();
        let corpus = comparison::suite().unwrap();
        let step = &corpus.steps()[INDEX];
        let dir = target.join(exhausted);
        let mut ledger = Ledger::load(&dir, &binding).unwrap();
        ledger.begin_invocation().unwrap();
        for admission in 0..27 {
            assert_eq!(ledger.admit(&format!("scene-{}", step.scene()), step.id()).unwrap(), admission);
            assert!(!dir.join(format!("admission-{admission:02}-settled.json")).exists());
        }
        ledger.finish().unwrap(); // Actual preparation measurement, no admission refunds.
        drop(ledger);
        let recorded = Ledger::load(&dir, &binding).unwrap();
        assert_eq!((recorded.invocations, recorded.admissions, recorded.charged_roles), (1, 27, 81));
        assert!(recorded.remaining() >= crate::local_lane::PREPARATION_MS);
        assert!(recorded.remaining().saturating_sub(crate::local_lane::PREPARATION_MS) <
            crate::local_lane::TURN_MS + crate::local_lane::CLEANUP_RESERVE_MS);
        drop(recorded);
        let work = inspect_work(&p, &target, Instant::now()).unwrap();
        assert!(work.needs_admission.into_iter().all(|needed| needed));
        assert_eq!(refused(preflight(&work)), "RunBudget");
        drop(work); drop(destination); drop(p);
        let before = inventory(&target);
        let calls = AtomicUsize::new(0);
        let failure = native_error(resume_native_selected(&target, &f.source, &binding,
            &Cancellation::default(), || {
                calls.fetch_add(1, Ordering::SeqCst);
                Err::<Trap, _>("RunBudget".into())
            }));
        assert_eq!(failure.code(), "RunBudget");
        assert!(!failure.cleanup_uncertain());
        assert_eq!(calls.load(Ordering::SeqCst), 0);
        unchanged(&target, &before); unchanged(&f.source, &source_before);
        for arm in ARMS {
            assert!(!db(&target, arm, f.kind).exists() && !cp(&target, arm).exists());
        }
    }
}

#[cfg(feature = "local-model")]
#[test]
fn n08_both_arm_invocation_and_unknown_preparation_caps_refuse_before_reserve_or_assets() {
    for exhausted in ARMS {
        for budget in ["invocations", "unknown-preparation"] {
            let f = Fixture::new("invocation-preflight", comparison::ComparisonKind::ContinuousRollout, false);
            let source_before = inventory(&f.source);
            let p = f.plan("native4-preflight-cap");
            let target = f.root.join("selected");
            let destination = new_destination(&p, &target).unwrap();
            let binding = destination.manifest.binding.clone();
            let mut ledger = Ledger::load(&target.join(exhausted), &binding).unwrap();
            if budget == "invocations" {
                for _ in 0..32 { ledger.begin_invocation().unwrap(); ledger.finish().unwrap(); }
                assert_eq!(ledger.invocations, 32);
            } else {
                // Keep genuine preparation reservations unknown; never invent
                // elapsed measurements or fabricate a charged-time counter.
                for _ in 0..15 { ledger.begin_invocation().unwrap(); }
                assert_eq!(ledger.invocations, 15);
                assert_eq!(ledger.charged_ms, crate::local_lane::MAX_ACTIVE_MS);
            }
            assert_eq!((ledger.admissions, ledger.charged_roles), (0, 0));
            drop(ledger); drop(destination); drop(p);
            let before = inventory(&target);
            let calls = AtomicUsize::new(0);
            let failure = native_error(resume_native_selected(&target, &f.source, &binding,
                &Cancellation::default(), || {
                    calls.fetch_add(1, Ordering::SeqCst);
                    Err::<Trap, _>("RunBudget".into())
                }));
            assert_eq!(failure.code(), "RunBudget");
            assert!(!failure.cleanup_uncertain());
            assert_eq!(calls.load(Ordering::SeqCst), 0);
            unchanged(&target, &before); unchanged(&f.source, &source_before);
        }
    }
}

#[cfg(feature = "local-model")]
#[test]
fn n09_fresh_reservation_is_once_after_preflight_and_late_cancel_still_precedes_assets_or_target() {
    let f = Fixture::new("reserve-order", comparison::ComparisonKind::ContinuousRollout, false);
    let before = inventory(&f.root);
    let calls = AtomicUsize::new(0);
    let assets = Arc::new(AtomicUsize::new(0));
    let target = f.root.join("refused-reservation");
    let failure = native_error(run_native_selected(f.plan("native4-reserve-once"), &target,
        &Cancellation::default(), || {
            calls.fetch_add(1, Ordering::SeqCst);
            Err::<Trap, _>("RunBudget".into())
        }));
    assert_eq!(failure.code(), "RunBudget");
    assert_eq!(calls.load(Ordering::SeqCst), 1);
    assert!(!failure.cleanup_uncertain() && !target.exists());
    unchanged(&f.root, &before);
    let late = Cancellation::default();
    let target = f.root.join("cancelled-after-reserve");
    let failure = native_error(run_native_selected(f.plan("native4-late-cancel"), &target, &late, || {
        calls.fetch_add(1, Ordering::SeqCst);
        late.cancel();
        Ok(Trap { assets: assets.clone() })
    }));
    assert_eq!(failure.code(), "Interrupted");
    assert!(!failure.cleanup_uncertain());
    assert_eq!(calls.load(Ordering::SeqCst), 2);
    assert_eq!(assets.load(Ordering::SeqCst), 0);
    assert!(!target.exists());
    unchanged(&f.root, &before);
    let early = Cancellation::default(); early.cancel();
    let target = f.root.join("cancelled-at-entry");
    let p = f.plan("native4-early-cancel");
    let failure = native_error(run_native_selected(p, &target, &early, || {
        calls.fetch_add(1, Ordering::SeqCst);
        Err::<Trap, _>("RunBudget".into())
    }));
    assert_eq!(failure.code(), "Interrupted");
    assert_eq!(calls.load(Ordering::SeqCst), 2);
    unchanged(&f.root, &before);
}

#[cfg(feature = "local-model")]
fn import_recovery(f: &Fixture) -> (PathBuf, Value, Vec<Engine>, Vec<Value>) {
    let p = f.plan("native4-import-real-scripted");
    let target = f.root.join("selected");
    let destination = new_destination(&p, &target).unwrap();
    let binding = destination.manifest.binding.clone();
    let corpus = comparison::suite().unwrap();
    let step = &corpus.steps()[INDEX];
    let mut imported = Vec::new();
    let mut expected = Vec::new();
    for (arm_index, arm) in ARMS.iter().enumerate() {
        let source_cp: source4::StoredTurn4 =
            comparison::decode(&cp(&f.source, arm), 256 * 1024).unwrap();
        assert_eq!(source_cp.row.phase, "committed");
        let full = engine(&db(&f.source, arm, f.kind), &corpus.seed().scope).unwrap();
        let after = full.at_revision(source_cp.after_head).unwrap();
        assert!(after.receipts().last().unwrap().request() == &source_cp.request);
        let path = db(&target, arm, f.kind);
        comparison::ensure_database(&path, corpus.seed(), after.receipts()).unwrap();
        assert!(!cp(&target, arm).exists());
        // Existing real recovery helper supplies the actual construction_matches
        // result. It never upgrades SCRIPTED provenance to current native profile.
        let recovered = source4::ready_turn4(source4::ReadyJob4 {
            path: &path, full: &after, index: INDEX, arm,
            construction: source4::CONSTRUCTIONS[arm_index], binding: &binding,
            step, profile: &p.manifest.profile,
        }).unwrap().expect("actual imported selected receipt");
        expected.push(serde_json::to_value(recovered.row).unwrap());
        imported.push(after);
    }
    drop(destination); drop(p);
    let calls = AtomicUsize::new(0);
    let report = serde_json::to_value(resume_native_selected(&target, &f.source, &binding,
        &Cancellation::default(), || {
            calls.fetch_add(1, Ordering::SeqCst);
            Err::<Trap, _>("RunBudget".into())
        }).unwrap()).unwrap();
    assert_eq!(calls.load(Ordering::SeqCst), 0);
    (target, report, imported, expected)
}
#[cfg(feature = "local-model")]
fn assert_unknown_recovery(report: &Value, imported: &[Engine], expected: &[Value]) {
    assert_eq!(report["version"], 4);
    assert_eq!(report["source_protocol_version"], 4);
    assert_eq!(report["lane"], "native_selected_case");
    assert_eq!(report["source_native"], false);
    assert_eq!(report["completed"], true);
    assert_eq!(report["physical_setups"], 0);
    assert!(report["physical_setup_ms"].is_null() && report["native_load"].is_null());
    assert_eq!(report["human_reviewed"], 0);
    assert_eq!(report["human_rubric"], "not_reviewed");
    assert_eq!(report["quality_accepted"], false);
    let notes = report["unavailable"].as_array().unwrap();
    for note in ["human_quality_not_reviewed", "native_setup_measurement_unavailable"] {
        assert!(notes.iter().any(|value| value == note));
    }
    assert_eq!(report["rows"].as_array().unwrap().len(), 2);
    for (index, arm) in ARMS.iter().enumerate() {
        let row = &report["rows"][index];
        assert_eq!(row["arm"], *arm);
        assert_eq!(row["phase"], "committed");
        assert_eq!(row["recovered_without_checkpoint"], true);
        assert_eq!(row["roles_known"], false);
        assert_eq!(row["passed"], false);
        assert_eq!(row["construction_evidence_status"], "unavailable");
        assert_eq!(row["privacy_evidence_status"], "unavailable");
        assert!(row["construction_matches"] == expected[index]["construction_matches"]);
        assert_eq!(row["actual_receipt_sha256"],
            digest(&encode(imported[index].receipts().last().unwrap()).unwrap()));
        for field in ["admission", "first_final_response_ms", "commit_elapsed_ms",
            "narrator_prompt_sha256", "narrator_schema_sha256", "scene_frame_sha256",
            "capture_sha256", "recording_sha256", "trace"] {
            assert!(row[field].is_null(), "unavailable recovery field");
        }
        assert!(row["raw_sha256"].as_array().unwrap().is_empty());
    }
}
#[cfg(feature = "local-model")]
#[test]
fn n10_genuine_scripted_core_store_import_recovers_both_arms_without_assets_or_native_claims() {
    for kind in [comparison::ComparisonKind::PairedSnapshots, comparison::ComparisonKind::ContinuousRollout] {
        let f = Fixture::new("real-import-recovery", kind, false);
        let source_before = inventory(&f.source);
        let (target, report, imported, expected) = import_recovery(&f);
        assert_unknown_recovery(&report, &imported, &expected);
        let binding = report["binding"].as_str().unwrap();
        for (index, arm) in ARMS.iter().enumerate() {
            let actual = engine(&db(&target, arm, f.kind),
                &comparison::suite().unwrap().seed().scope).unwrap();
            assert!(actual.receipts() == imported[index].receipts());
            assert!(actual.canonical_bytes() == imported[index].canonical_bytes());
            let recorded = value(&cp(&target, arm));
            assert!(recorded["row"] == report["rows"][index]);
            let ledger = Ledger::load(&target.join(arm), binding).unwrap();
            assert_eq!((ledger.admissions, ledger.charged_roles), (0, 0));
            assert!(fs::read_dir(target.join(arm)).unwrap().all(|item| {
                let name = item.unwrap().file_name().to_string_lossy().into_owned();
                !name.starts_with("admission-") && !name.starts_with("raw-")
            }));
        }
        assert!(serde_json::to_value(inspect_selected(&target).unwrap()).unwrap() == report);
        assert!(fs::metadata(target.join("report.json")).unwrap().len() <= 2 * 1024 * 1024);
        assert!(fs::metadata(target.join("report.html")).unwrap().len() <= 2 * 1024 * 1024);
        unchanged(&f.source, &source_before);
    }
}

#[cfg(feature = "local-model")]
#[test]
fn n11_completed_current_source_resume_at_cap_is_read_only_and_does_not_upgrade_imported_evidence() {
    let f = Fixture::new("completed-at-cap", comparison::ComparisonKind::ContinuousRollout, false);
    let (target, report, imported, expected) = import_recovery(&f);
    assert_unknown_recovery(&report, &imported, &expected);
    let binding = report["binding"].as_str().unwrap();
    for arm in ARMS {
        let mut ledger = Ledger::load(&target.join(arm), binding).unwrap();
        while ledger.invocations < 32 {
            ledger.begin_invocation().unwrap(); ledger.finish().unwrap();
        }
        assert_eq!((ledger.invocations, ledger.admissions, ledger.charged_roles), (32, 0, 0));
    }
    let expected_report = serde_json::to_value(inspect_selected(&target).unwrap()).unwrap();
    let before = inventory(&f.root);
    let calls = AtomicUsize::new(0);
    let repeated = serde_json::to_value(resume_native_selected(&target, &f.source, binding,
        &Cancellation::default(), || {
            calls.fetch_add(1, Ordering::SeqCst);
            Err::<Trap, _>("RunBudget".into())
        }).unwrap()).unwrap();
    assert!(repeated == expected_report);
    assert_eq!(calls.load(Ordering::SeqCst), 0);
    assert_unknown_recovery(&repeated, &imported, &expected);
    unchanged(&f.root, &before);
    let source_file = f.source.join("run.json");
    fs::write(f.root.join("retained-completed-source-original.json"), fs::read(&source_file).unwrap()).unwrap();
    let mut source = value(&source_file);
    source["source_sha256"] = json!("0".repeat(64));
    source["binding"]["source_sha256"] = json!("0".repeat(64));
    fs::write(source_file, encode(&source).unwrap()).unwrap();
    let stale_before = inventory(&f.root);
    let failure = native_error(resume_native_selected(&target, &f.source, binding,
        &Cancellation::default(), || {
            calls.fetch_add(1, Ordering::SeqCst);
            Err::<Trap, _>("RunBudget".into())
        }));
    assert!(!failure.cleanup_uncertain());
    assert_eq!(calls.load(Ordering::SeqCst), 0);
    unchanged(&f.root, &stale_before);
}


#[cfg(feature = "local-model")]
fn query(edge: comparison::desktop_api::Edge, observer: Observer, view: View)
    -> comparison::desktop_api::EvidenceRequest {
    comparison::desktop_api::EvidenceRequest::Query { edge, observer, view }
}
#[cfg(feature = "local-model")]
fn contexts(engine: &Engine) -> Value {
    json!([
        engine.character_context(&engine.seed().player, engine.scope(), engine.revision()).unwrap(),
        engine.character_context("mira", engine.scope(), engine.revision()).unwrap(),
        engine.character_context("sable", engine.scope(), engine.revision()).unwrap(),
    ])
}
#[cfg(feature = "local-model")]
#[test]
fn n12_native_read_setup_checkpoint_bounds_grants_queries_privacy_and_drift_never_mint_authority() {
    use comparison::desktop_api::{Edge, EvidenceRequest};
    let f = Fixture::new("read-integrity", comparison::ComparisonKind::PairedSnapshots, false);
    let (target, report, imported, expected) = import_recovery(&f);
    assert_unknown_recovery(&report, &imported, &expected);
    let before = inventory(&f.root);
    let opened = desktop_read::open_read_only(&target).unwrap();
    assert_eq!(refused(desktop_read::summary(&opened, false)), "Forbidden");
    assert_eq!(refused(desktop_read::open_read_only(&target)), "RunBusy");
    let metadata = desktop_read::summary(&opened, true).unwrap();
    keys(&metadata, &["version", "kind", "source_protocol_version", "constructions",
        "binding", "selection", "lane", "arms", "read_only", "execution_available"]);
    assert_eq!(metadata["version"], 4);
    assert_eq!(metadata["kind"], "selected_read");
    assert_eq!(metadata["source_protocol_version"], 4);
    assert_eq!(metadata["lane"], "native_selected_case");
    assert_eq!(metadata["read_only"], true);
    assert_eq!(metadata["execution_available"], false);
    assert!(encode(&metadata).unwrap().len() <= 16 * 1024);
    assert!(metadata["selection"] == report["selection"] && metadata["constructions"] == report["arms"]);
    let binding = metadata["binding"].as_str().unwrap();
    assert_ne!(metadata["binding"], report["binding"]);
    assert_ne!(metadata["binding"], report["source_binding"]);
    for forbidden in ["generation_grant", "request", "source_inputs", "profile", "report",
        "rows", "narration", "error", "native_load"] {
        assert!(metadata.get(forbidden).is_none());
    }
    assert_eq!(refused(desktop_read::evidence(&opened, "bad", Arm::Left,
        EvidenceRequest::Receipt { observer: Observer::Player }, false)), "Forbidden");
    assert_eq!(refused(desktop_read::diagnostics(&opened, "bad", Observer::Omniscient, false)), "Forbidden");
    assert_eq!(refused(desktop_read::diagnostics(&opened, binding, Observer::Player, true)), "Forbidden");
    assert_eq!(refused(desktop_read::evidence(&opened, "bad", Arm::Right,
        query(Edge::Before, Observer::Player, View::History), true)), "SnapshotMismatch");
    for (index, (arm, name)) in [(Arm::Left, "left"), (Arm::Right, "right")].into_iter().enumerate() {
        let checkpoint = value(&cp(&target, name));
        let full = engine(&db(&target, name, f.kind), &comparison::suite().unwrap().seed().scope).unwrap();
        let context_before = contexts(&full);
        keys(&metadata["arms"][index], &["arm", "scope", "before_head", "after_head", "available"]);
        assert_eq!(metadata["arms"][index]["arm"], name);
        assert_eq!(metadata["arms"][index]["available"], true);
        assert!(metadata["arms"][index]["scope"] == checkpoint["request"]["scope"]);
        assert!(metadata["arms"][index]["before_head"] == checkpoint["before_head"]);
        assert!(metadata["arms"][index]["after_head"] == checkpoint["after_head"]);
        for (edge, head_field) in [(Edge::Before, "before_head"), (Edge::After, "after_head")] {
            let head = checkpoint[head_field].as_u64().unwrap();
            let cut = full.at_revision(head).unwrap();
            for observer in [Observer::Player, Observer::Character { id: "sable".into() }] {
                for view in [View::History, View::Knowledge] {
                    let evidence = desktop_read::evidence(&opened, binding, arm,
                        query(edge, observer.clone(), view), true).unwrap();
                    keys(&evidence, &["version", "binding", "row", "scope", "before_head",
                        "after_head", "observer", "edge", "read_only", "generation_grant", "body"]);
                    assert_eq!(evidence["read_only"], true);
                    assert_eq!(evidence["generation_grant"], false);
                    let actual_query = inspection_query::query(&cut, &Query {
                        version: 2, scope: cut.scope().clone(), expected_head: head,
                        at_revision: None, observer: observer.clone(), view, cursor: None,
                        limit: MAX_ROWS, search: String::new(),
                    }, true).unwrap();
                    assert!(evidence["body"]["page"] == serde_json::to_value(actual_query).unwrap());
                    assert!(encode(&evidence).unwrap().len() <= 256 * 1024);
                    if matches!(&observer, Observer::Character { id } if id == "sable") {
                        assert!(!evidence.to_string().contains("SECRET-TIDE-731"));
                    }
                }
            }
        }
        for request in [
            EvidenceRequest::Receipt { observer: Observer::Omniscient },
            EvidenceRequest::Capture { observer: Observer::Omniscient },
            EvidenceRequest::Outputs { observer: Observer::Omniscient },
        ] {
            let evidence = desktop_read::evidence(&opened, binding, arm, request, true).unwrap();
            assert_eq!(evidence["read_only"], true);
            assert_eq!(evidence["generation_grant"], false);
            assert!(encode(&evidence).unwrap().len() <= 256 * 1024);
            // Recovered rows cannot manufacture their missing capture/calls.
        }
        assert!(contexts(&engine(&db(&target, name, f.kind),
            &comparison::suite().unwrap().seed().scope).unwrap()) == context_before);
    }
    let diagnostics = desktop_read::diagnostics(&opened, binding, Observer::Omniscient, true).unwrap();
    keys(&diagnostics, &["version", "kind", "source_protocol_version", "constructions",
        "binding", "lane", "completed", "rows", "physical_setups", "physical_setup_ms",
        "left_charged_ms", "right_charged_ms", "left_reserved_roles", "right_reserved_roles",
        "human_reviewed", "human_rubric", "quality_accepted", "unavailable"]);
    assert_eq!(diagnostics["version"], 4);
    assert_eq!(diagnostics["kind"], "selected_diagnostics");
    assert_eq!(diagnostics["source_protocol_version"], 4);
    assert_eq!(diagnostics["human_reviewed"], 0);
    assert_eq!(diagnostics["quality_accepted"], false);
    assert!(encode(&diagnostics).unwrap().len() <= 256 * 1024);
    let row_keys = ["turn", "arm", "phase", "error", "expected", "passed", "failures",
        "quality_flags", "roles", "roles_known", "elapsed_ms", "actual_receipt_sha256",
        "construction", "construction_evidence_status", "construction_evidence_reason",
        "construction_matches", "privacy_evidence_status", "fallback", "repairs",
        "recovered_without_checkpoint", "first_final_response_ms", "commit_elapsed_ms",
        "narrator_prompt_sha256", "narrator_schema_sha256", "scene_frame_sha256"];
    for row in diagnostics["rows"].as_array().unwrap() {
        keys(row, &row_keys);
        for secret in ["request", "narration", "native_load", "recording_file", "capture_file", "raw"] {
            assert!(row.get(secret).is_none());
        }
    }
    drop(opened);
    unchanged(&f.root, &before);
    let template = inventory(&target);
    // Invalid fixtures preserve their genuine baseline and never repair source.
    // No manufactured valid native setup/metric is used as positive evidence.
    for fault in ["setup-v4", "setup-scripted", "setup-large", "manifest-large",
        "checkpoint-large", "checkpoint-request", "checkpoint-roles", "accounting"] {
        let altered = f.root.join(format!("read-tamper-{fault}"));
        copy_tree(&template, &altered);
        let binding = value(&altered.join("selected.json"))["binding"].as_str().unwrap().to_owned();
        match fault {
            "setup-v4" | "setup-scripted" => {
                fs::write(altered.join("setup-00.json"), encode(&json!({
                    "version": if fault == "setup-v4" { 4 } else { 2 },
                    "binding": binding, "left_invocation":0, "right_invocation":0,
                    "native":fault == "setup-v4", "physical_ms":0,
                    "status":"failed", "load":null,
                })).unwrap()).unwrap();
            }
            "setup-large" => { fs::write(altered.join("setup-00.json"), vec![b' '; 64*1024+1]).unwrap(); }
            "manifest-large" => {
                let file = altered.join("selected.json"); let mut bytes = fs::read(&file).unwrap();
                bytes.resize(128*1024+1, b' '); fs::write(file, bytes).unwrap();
            }
            "checkpoint-large" => {
                let file = cp(&altered, "right"); let mut bytes = fs::read(&file).unwrap();
                bytes.resize(256*1024+1, b' '); fs::write(file, bytes).unwrap();
            }
            "checkpoint-request" | "checkpoint-roles" => {
                let file = cp(&altered, "right"); let mut checkpoint = value(&file);
                if fault == "checkpoint-request" { checkpoint["request"]["turn"] = json!("changed"); }
                else { checkpoint["row"]["roles_known"] = json!(true); }
                fs::write(file, encode(&checkpoint).unwrap()).unwrap();
            }
            "accounting" => {
                let file = altered.join("right/invocation-00-settled.json");
                let mut settlement = value(&file); settlement["binding"] = json!("a".repeat(64));
                fs::write(file, encode(&settlement).unwrap()).unwrap();
            }
            _ => unreachable!(),
        }
        let bad_before = inventory(&altered);
        refused(inspect_selected(&altered)); refused(desktop_read::open_read_only(&altered));
        unchanged(&altered, &bad_before);
    }
    let cached = f.root.join("cached-report-not-authority"); copy_tree(&template, &cached);
    fs::write(cached.join("report.json"), b"not an authoritative manifest").unwrap();
    fs::write(cached.join("report.html"), b"not authoritative HTML").unwrap();
    let cache_before = inventory(&cached);
    assert!(serde_json::to_value(inspect_selected(&cached).unwrap()).unwrap() == report);
    unchanged(&cached, &cache_before);
    let drift = f.root.join("opened-read-drift"); copy_tree(&template, &drift);
    let opened = desktop_read::open_read_only(&drift).unwrap();
    let private = desktop_read::summary(&opened, true).unwrap()["binding"].as_str().unwrap().to_owned();
    let file = cp(&drift, "left"); let mut checkpoint = value(&file);
    checkpoint["request"]["turn"] = json!("changed after read capability");
    fs::write(file, encode(&checkpoint).unwrap()).unwrap();
    // Permission denial precedes probing corrupt retained data.
    assert_eq!(refused(desktop_read::summary(&opened, false)), "Forbidden");
    assert_eq!(refused(desktop_read::diagnostics(&opened, "bad", Observer::Player, true)), "Forbidden");
    refused(desktop_read::summary(&opened, true));
    refused(desktop_read::evidence(&opened, &private, Arm::Left,
        query(Edge::After, Observer::Player, View::History), true));
    drop(opened);
    unchanged(&f.source, &inventory(original_source(f.kind, false)));
}

#[test]
fn n13_data_only_historical_native_codec_reads_without_feature_assets_or_current_profile() {
    use crate::{digest, encode, memory_comparison_v2 as v2, memory_comparison_v4 as v4};
    use crate::local_lane::LaneFactory;
    use locallore::{engine::Engine, inspection_query::Observer};
    use serde_json::{json, Value};

    // EXPLICIT DATA-ONLY artifact, not a native run or an authenticated source.
    // No receipt, checkpoint, setup, invocation, provider, grant or runtime is
    // created. Corpus-derived request/prefix/input hashes test the real codec;
    // the historical-shaped profile is synthetic provenance, not fake results.
    let root = fixture_root("data-only-historical-read");
    let dir = root.join("selected-data-only");
    fs::create_dir(&dir).unwrap();
    for arm in ["left", "right"] { fs::create_dir(dir.join(arm)).unwrap(); }
    fs::write(dir.join("run.lock"), b"").unwrap();
    let corpus = comparison::suite().unwrap();
    let before = Engine::new(corpus.seed().clone()).unwrap();
    assert!(before.receipts().is_empty());
    let step = &corpus.steps()[0];
    let request = step.request(&before);
    let prefix = digest(&encode(before.receipts()).unwrap());
    let semantic = v2::semantic_input(&before, &request).unwrap();
    let source_profile = LaneFactory::ScriptedBaseline.profile().unwrap();
    let mut historical_profile = source_profile.clone();
    historical_profile.id = "data-only-obsolete-native-selected4-profile".into();
    historical_profile.validate().unwrap();
    // This deliberately differs from the fixed current native profile's
    // provenance label; neither feature branch calls native_profile().
    assert_ne!(historical_profile.id, source_profile.id);
    let current = v4::current_binding(false).unwrap();
    let inputs: Vec<Value> = ["left", "right"].into_iter().map(|arm| json!({
        "arm":arm,"scope":before.scope(),"before_head":before.revision(),
        "prefix_sha256":prefix,"input_semantic_sha256":semantic,"request":request,
    })).collect();
    let mut manifest = json!({
        "version":4,"run_type":"selected_case","source_protocol_version":4,
        "arms":v4::current_arm_descriptors(),"client_id":"data-only-historical-read",
        "source_binding":"a".repeat(64),
        "source_kind":comparison::ComparisonKind::ContinuousRollout,
        "source_profile":source_profile,"source_native":false,
        "selection":{"turn":step.id(),"index":0,"clicked_arm":"left"},
        "lane":"native_selected_case","profile":historical_profile,
        "suite_sha256":current.suite_sha256,"source_sha256":"0".repeat(64),
        "source_reference_sha256":null,"source_inputs":inputs,
    });
    manifest["binding"] = json!(digest(&encode(&manifest).unwrap()));
    let file = dir.join("selected.json");
    let original = encode(&manifest).unwrap();
    fs::write(&file, &original).unwrap();

    let report = serde_json::to_value(super::inspect_selected(&dir).unwrap()).unwrap();
    assert_eq!(report["version"], 4);
    assert_eq!(report["source_protocol_version"], 4);
    assert_eq!(report["lane"], "native_selected_case");
    assert_eq!(report["completed"], false);
    assert!(report["rows"].as_array().unwrap().is_empty());
    assert!(report["profile"] == manifest["profile"]);
    assert!(report["source_profile"] == manifest["source_profile"]);
    assert_eq!(report["source_native"], false);
    assert_eq!(report["physical_setups"], 0);
    assert!(report["physical_setup_ms"].is_null() && report["native_load"].is_null());
    assert_eq!(report["human_reviewed"], 0);
    assert_eq!(report["human_rubric"], "not_reviewed");
    assert_eq!(report["quality_accepted"], false);
    for note in ["human_quality_not_reviewed", "native_setup_measurement_unavailable"] {
        assert!(report["unavailable"].as_array().unwrap().iter().any(|value| value == note));
    }
    let opened = super::desktop_read::open_read_only(&dir).unwrap();
    let summary = super::desktop_read::summary(&opened, true).unwrap();
    assert_eq!(summary["version"], 4);
    assert_eq!(summary["kind"], "selected_read");
    assert_eq!(summary["read_only"], true);
    assert_eq!(summary["execution_available"], false);
    assert!(encode(&summary).unwrap().len() <= 16 * 1024);
    for field in ["generation_grant", "request", "source_inputs", "profile", "report", "rows"] {
        assert!(summary.get(field).is_none());
    }
    for arm in summary["arms"].as_array().unwrap() {
        assert_eq!(arm["before_head"], 0);
        assert!(arm["after_head"].is_null());
        assert_eq!(arm["available"], false);
    }
    let diagnostics = super::desktop_read::diagnostics(&opened,
        summary["binding"].as_str().unwrap(), Observer::Omniscient, true).unwrap();
    assert!(diagnostics["rows"].as_array().unwrap().is_empty());
    assert_eq!(diagnostics["quality_accepted"], false);
    assert_eq!(refused(super::desktop_read::summary(&opened, false)), "Forbidden");
    // The empty read artifact and obsolete profile remain data, not a source
    // read capability, prepared execution plan or generation authorization.
    #[cfg(not(feature = "local-model"))]
    assert_eq!(refused(prepare_selected(&root.join("missing-full-source"),
        manifest["source_binding"].as_str().unwrap(), &row(0, Arm::Left),
        SelectedIntent { client_id: "no-feature-historical-data".into(),
            lane: SelectedLane::ApprovedNative }, &Cancellation::default())),
        "NativeFeatureUnavailable");
    assert_eq!(refused(prepare_selected(&dir,
        manifest["source_binding"].as_str().unwrap(), &row(0, Arm::Left),
        SelectedIntent { client_id: "read-is-not-scripted-authority".into(),
            lane: SelectedLane::ScriptedBaseline }, &Cancellation::default())),
        "SelectedLaneMismatch");
    drop(opened);
    assert!(fs::read(&file).unwrap() == original);
    assert!(fs::read(dir.join("run.lock")).unwrap().is_empty());
    let mut names = fs::read_dir(&dir).unwrap().map(|entry|
        entry.unwrap().file_name().to_string_lossy().into_owned()).collect::<Vec<_>>();
    names.sort();
    assert!(names.iter().map(String::as_str).eq(["left", "right", "run.lock", "selected.json"]));
    for arm in ["left", "right"] {
        assert!(fs::read_dir(dir.join(arm)).unwrap().next().is_none());
    }
    assert!(!root.join("missing-full-source").exists());
}
