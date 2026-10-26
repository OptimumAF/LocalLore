// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen SOURCE ONLY / UNCOMPILED / UNRUN. Four native-selected2 preflight
//! groups, actual scripted V3 source. No assets, owner cleanup or model evidence.
#![cfg(feature = "local-model")]

use locallore::inference::Cancellation;
use locallore_eval::{
    local_lane::{comparison::{desktop_api::{Arm, RowId}, literal_v3::{self, selected_v2}, selected::{SelectedIntent, SelectedLane, SelectedNativeFailure, SelectedNativeReservation}, ComparisonKind}, LaneFactory, NativeAssets},
    memory_comparison::frozen_suite,
};
use locallore_local_runtime::LocalRuntime;
use serde_json::{json, Value};
use std::{collections::BTreeMap, fs, path::{Path, PathBuf}, sync::{Arc, Mutex, OnceLock, atomic::{AtomicUsize, Ordering}}};

#[derive(Default)]
struct Counts { reserve: AtomicUsize, assets: AtomicUsize, drops: AtomicUsize }
struct FakeReservation(Arc<Counts>);
impl SelectedNativeReservation for FakeReservation {
    fn assets(&self) -> NativeAssets<'_> { self.0.assets.fetch_add(1, Ordering::SeqCst); panic!("preflight must not access assets"); }
    fn retain_uncertain(&mut self, owner: Arc<Mutex<LocalRuntime>>) -> Result<(), Arc<Mutex<LocalRuntime>>> { Err(owner) }
}
impl Drop for FakeReservation { fn drop(&mut self) { self.0.drops.fetch_add(1, Ordering::SeqCst); } }
type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;
fn root(label: &str) -> PathBuf {
    static NEXT: AtomicUsize = AtomicUsize::new(0);
    let p = std::env::temp_dir().join(format!("literal-selected-native-preflight-{label}-{}-{}-{}", std::process::id(), std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos(), NEXT.fetch_add(1, Ordering::Relaxed))); fs::create_dir(&p).unwrap(); p
}
fn inventory(root: &Path) -> Inventory {
    fn walk(root: &Path, dir: &Path, depth: usize, total: &mut usize, out: &mut Inventory) {
        assert!(depth <= 8 && out.len() < 4096);
        for e in fs::read_dir(dir).unwrap() {
            let p = e.unwrap().path(); let m = fs::symlink_metadata(&p).unwrap(); assert!(!m.file_type().is_symlink());
            #[cfg(windows)] { use std::os::windows::fs::MetadataExt; assert_eq!(m.file_attributes() & 0x400, 0); }
            let rel = p.strip_prefix(root).unwrap().to_owned();
            if m.is_dir() { out.insert(rel, None); walk(root, &p, depth + 1, total, out); }
            else { assert!(m.is_file() && m.len() <= 8 * 1024 * 1024); let bytes = fs::read(p).unwrap(); *total = total.checked_add(bytes.len()).unwrap(); assert!(*total <= 64 * 1024 * 1024); out.insert(rel, Some(bytes)); }
        }
    }
    let mut out = Inventory::new(); walk(root, root, 0, &mut 0, &mut out); out
}
fn original() -> &'static Path {
    static SOURCE: OnceLock<PathBuf> = OnceLock::new(); SOURCE.get_or_init(|| {
        let dir = root("producer").join("source"); let report = literal_v3::run_comparison(&dir, false, ComparisonKind::ContinuousRollout, &Cancellation::default(), 1, LaneFactory::ScriptedBaseline, None).unwrap(); assert_eq!((report.completed_scenes, report.turns.len()), (1, 12)); dir
    }).as_path()
}
fn fixture(label: &str) -> (PathBuf, PathBuf) {
    let root = root(label); let source = root.join("source"); fs::create_dir(&source).unwrap(); let original = inventory(original());
    for (p, bytes) in &original { match bytes { None => fs::create_dir_all(source.join(p)).unwrap(), Some(bytes) => fs::write(source.join(p), bytes).unwrap() } }
    assert_eq!(inventory(&source), original); (source, root.join("must-not-exist"))
}
fn plan(source: &Path, lane: SelectedLane, client: &str) -> selected_v2::PreparedSelectedPlan {
    let opened = literal_v3::desktop_api::open_read_only(source).unwrap(); let value = literal_v3::desktop_api::summary(&opened, true).unwrap(); let binding = value["binding"].as_str().unwrap().to_owned(); drop(opened);
    selected_v2::prepare_selected(source, &binding, &RowId { turn: frozen_suite().unwrap().steps()[4].id().into(), arm: Arm::Left }, SelectedIntent { client_id: client.into(), lane }, &Cancellation::default()).unwrap()
}
fn native_failure<T>(result: Result<T, SelectedNativeFailure<FakeReservation>>) -> SelectedNativeFailure<FakeReservation> { match result { Ok(_) => panic!("expected native preflight refusal"), Err(error) => error } }
fn string_failure<T>(result: Result<T, String>) -> String { match result { Ok(_) => panic!("expected scripted lane refusal"), Err(error) => error } }
fn reserve(counts: &Arc<Counts>) -> Result<FakeReservation, String> { counts.reserve.fetch_add(1, Ordering::SeqCst); Ok(FakeReservation(counts.clone())) }
fn counts(counts: &Counts, expected_reserve: usize, expected_drop: usize) { assert_eq!(counts.reserve.load(Ordering::SeqCst), expected_reserve); assert_eq!(counts.assets.load(Ordering::SeqCst), 0); assert_eq!(counts.drops.load(Ordering::SeqCst), expected_drop); }

#[test]
fn right_source_drift_or_preentry_cancellation_precedes_native_callback_and_output() {
    for drift in [false, true] {
        let (source, target) = fixture(if drift { "right-drift" } else { "cancel" }); let mut expected = inventory(&source); let plan = plan(&source, SelectedLane::ApprovedNative, "native-selected-preflight"); let cancel = Cancellation::default();
        if drift { // Explicit hostile diagnostic copy; no forged canonical input.
            let path = source.join("right/attempt-04.json"); let mut v: Value = serde_json::from_slice(&fs::read(&path).unwrap()).unwrap(); v["row"]["input_semantic_sha256"] = json!("0".repeat(64)); let bytes = serde_json::to_vec(&v).unwrap(); fs::write(&path, &bytes).unwrap(); expected.insert(path.strip_prefix(&source).unwrap().to_owned(), Some(bytes));
        } else { cancel.cancel(); }
        let observed = Arc::new(Counts::default()); let error = native_failure(selected_v2::run_native_selected(plan, &target, &cancel, || reserve(&observed)));
        if !drift { assert_eq!(error.code(), "Interrupted"); } assert!(!error.cleanup_uncertain()); counts(&observed, 0, 0); assert!(!target.exists()); assert_eq!(inventory(&source), expected);
    }
}

#[test]
fn reservation_provider_refusal_is_once_before_target_creation() {
    let (source, target) = fixture("callback-error"); let expected = inventory(&source); let plan = plan(&source, SelectedLane::ApprovedNative, "native-selected-provider-refused"); let observed = Arc::new(Counts::default());
    let error = native_failure(selected_v2::run_native_selected::<FakeReservation>(plan, &target, &Cancellation::default(), || { observed.reserve.fetch_add(1, Ordering::SeqCst); Err("Provider".into()) }));
    assert_eq!(error.code(), "Provider"); assert!(!error.cleanup_uncertain()); counts(&observed, 1, 0); assert!(!target.exists()); assert_eq!(inventory(&source), expected);
}

#[test]
fn callback_cancellation_drops_returned_reservation_without_assets_or_target() {
    let (source, target) = fixture("callback-cancel"); let expected = inventory(&source); let plan = plan(&source, SelectedLane::ApprovedNative, "native-selected-cancelled-callback"); let cancel = Cancellation::default(); let observed = Arc::new(Counts::default());
    let error = native_failure(selected_v2::run_native_selected(plan, &target, &cancel, || { let reservation = reserve(&observed)?; cancel.cancel(); Ok(reservation) }));
    assert_eq!(error.code(), "Interrupted"); assert!(!error.cleanup_uncertain()); counts(&observed, 1, 1); assert!(!target.exists()); assert_eq!(inventory(&source), expected);
}

#[test]
fn scripted_and_native_entrypoints_reject_the_other_prepared_lane_before_work() {
    let (source, native_target) = fixture("lane-mismatch"); let expected = inventory(&source); let observed = Arc::new(Counts::default()); let scripted = plan(&source, SelectedLane::ScriptedBaseline, "wrong-native-entry");
    let error = native_failure(selected_v2::run_native_selected(scripted, &native_target, &Cancellation::default(), || reserve(&observed))); assert_eq!(error.code(), "SelectedLaneMismatch"); assert!(!error.cleanup_uncertain()); counts(&observed, 0, 0); assert!(!native_target.exists()); assert_eq!(inventory(&source), expected);
    let native = plan(&source, SelectedLane::ApprovedNative, "wrong-scripted-entry"); let scripted_target = native_target.with_file_name("scripted-must-not-exist"); assert_eq!(string_failure(selected_v2::run_selected(native, &scripted_target, &Cancellation::default())), "SelectedLaneMismatch"); assert!(!scripted_target.exists()); assert_eq!(inventory(&source), expected);
}

// Feature-off discovery is intentionally zero tests, not a native qualification.
// This packet does not exercise recovery, cleanup owners, native checkpoints,
// real assets, successful inference or a completed-native resume fixture.
