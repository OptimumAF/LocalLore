// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! SOURCE ONLY / UNCOMPILED / UNRUN at handoff. Public ownership/preflight
//! contracts with deliberately missing assets; no worker, model or GUI proof.
#![cfg(feature = "local-model")]

use locallore::inference::Cancellation;
use locallore_eval::local_lane::{
    comparison::{literal_v3, selected::{SelectedNativeFailure, SelectedNativeReservation}, ComparisonKind},
    NativeAssets,
};
use locallore_local_runtime::LocalRuntime;
use serde_json::{json, Value};
use std::{collections::BTreeMap, fs, path::{Path, PathBuf}, sync::{Arc, Mutex, OnceLock, atomic::{AtomicUsize, Ordering}}};

#[derive(Default)]
struct Counts { reserve: AtomicUsize, assets: AtomicUsize, drops: AtomicUsize }
struct Reservation { counts: Arc<Counts>, dir: PathBuf, resources: PathBuf, model: PathBuf }
impl Reservation {
    fn new(counts: Arc<Counts>, dir: &Path) -> Self {
        let resources = dir.parent().unwrap().join("MISSING-approved-resources");
        let model = dir.parent().unwrap().join("MISSING-approved-model.gguf");
        assert!(!resources.exists() && !model.exists());
        Self { counts, dir: dir.to_owned(), resources, model }
    }
}
impl SelectedNativeReservation for Reservation {
    fn assets(&self) -> NativeAssets<'_> {
        // This is the FIRST observable asset access, not a fabricated load.
        for arm in ["left", "right"] { assert!(self.dir.join(arm).join("invocation-00.json").is_file(), "both durable reservations precede assets"); }
        self.counts.assets.fetch_add(1, Ordering::SeqCst);
        NativeAssets { resource_dir: &self.resources, model: &self.model }
    }
    fn retain_uncertain(&mut self, owner: Arc<Mutex<LocalRuntime>>) -> Result<(), Arc<Mutex<LocalRuntime>>> {
        // Missing assets must fail BeforeChild, never silently drop an owner.
        Err(owner)
    }
}
impl Drop for Reservation { fn drop(&mut self) { self.counts.drops.fetch_add(1, Ordering::SeqCst); } }
fn root(label: &str) -> PathBuf {
    static NEXT: AtomicUsize = AtomicUsize::new(0);
    let p = std::env::temp_dir().join(format!("literal-native-preflight-{label}-{}-{}-{}", std::process::id(), std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos(), NEXT.fetch_add(1, Ordering::SeqCst)));
    fs::create_dir(&p).unwrap(); p
}
type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;
fn inventory(root: &Path) -> Inventory {
    fn visit(root: &Path, p: &Path, depth: usize, total: &mut usize, out: &mut Inventory) {
        assert!(depth <= 8 && out.len() < 1024);
        let m = fs::symlink_metadata(p).unwrap(); assert!(!m.file_type().is_symlink());
        #[cfg(windows)] { use std::os::windows::fs::MetadataExt; assert_eq!(m.file_attributes() & 0x400, 0); }
        let relative = p.strip_prefix(root).unwrap().to_owned();
        if m.is_dir() { out.insert(relative, None); for e in fs::read_dir(p).unwrap() { visit(root, &e.unwrap().path(), depth + 1, total, out); } }
        else { assert!(m.is_file() && m.len() <= 8 * 1024 * 1024); let bytes = fs::read(p).unwrap(); *total += bytes.len(); assert!(*total <= 32 * 1024 * 1024); out.insert(relative, Some(bytes)); }
    }
    let mut out = Inventory::new(); if root.exists() { visit(root, root, 0, &mut 0, &mut out); } out
}
fn no_invocations(dir: &Path) { assert!(inventory(dir).keys().all(|p| !p.file_name().unwrap_or_default().to_string_lossy().starts_with("invocation-"))); }
fn failure<T>(value: Result<T, SelectedNativeFailure<Reservation>>) -> SelectedNativeFailure<Reservation> { match value { Ok(_) => panic!("expected fixed preflight/startup refusal"), Err(e) => e } }
fn invoke(dir: &Path, resume: bool, cancel: &Cancellation, scenes: usize, counts: Arc<Counts>) -> Result<locallore_eval::memory_comparison_v3::ComparisonReportV3, SelectedNativeFailure<Reservation>> {
    literal_v3::run_native_comparison(dir, resume, ComparisonKind::ContinuousRollout, cancel, scenes, || { counts.reserve.fetch_add(1, Ordering::SeqCst); Ok(Reservation::new(counts, dir)) }, None)
}

#[test]
fn cancelled_and_invalid_scene_admission_never_reserve_or_create_output() {
    let parent = root("preflight");
    for (scenes, cancelled) in [(0, false), (5, false), (1, true)] {
        let dir = parent.join(format!("run-{scenes}-{cancelled}")); let counts = Arc::new(Counts::default()); let cancel = Cancellation::default(); if cancelled { cancel.cancel(); }
        let error = failure(invoke(&dir, false, &cancel, scenes, counts.clone()));
        assert_eq!(error.code(), if cancelled { "Interrupted" } else { "SceneBudget" }); assert!(!error.cleanup_uncertain());
        assert_eq!(counts.reserve.load(Ordering::SeqCst), 0); assert_eq!(counts.assets.load(Ordering::SeqCst), 0); assert_eq!(counts.drops.load(Ordering::SeqCst), 0); assert!(!dir.exists());
    }
}

#[test]
fn cancellation_inside_reservation_drops_safe_ticket_without_assets_or_invocations() {
    let dir = root("callback-cancel").join("run"); let counts = Arc::new(Counts::default()); let cancel = Cancellation::default();
    let error = failure(literal_v3::run_native_comparison(&dir, false, ComparisonKind::ContinuousRollout, &cancel, 1, || {
        counts.reserve.fetch_add(1, Ordering::SeqCst); let owner = Reservation::new(counts.clone(), &dir); cancel.cancel(); Ok(owner)
    }, None));
    assert_eq!(error.code(), "Interrupted"); assert!(!error.cleanup_uncertain()); assert_eq!(counts.reserve.load(Ordering::SeqCst), 1); assert_eq!(counts.assets.load(Ordering::SeqCst), 0); assert_eq!(counts.drops.load(Ordering::SeqCst), 1); no_invocations(&dir);
}

fn failed_native_fixture() -> &'static PathBuf {
    static FIXTURE: OnceLock<PathBuf> = OnceLock::new(); FIXTURE.get_or_init(|| {
        let dir = root("actual-before-child").join("run"); let counts = Arc::new(Counts::default());
        let error = failure(invoke(&dir, false, &Cancellation::default(), 1, counts.clone()));
        assert!(!error.cleanup_uncertain()); assert_eq!(counts.reserve.load(Ordering::SeqCst), 1); assert!(counts.assets.load(Ordering::SeqCst) >= 1); assert_eq!(counts.drops.load(Ordering::SeqCst), 1);
        dir
    })
}
#[test]
fn genuine_before_child_asset_failure_is_owned_and_strictly_inspectable_without_generation() {
    let dir = failed_native_fixture(); let before = inventory(dir);
    let report = serde_json::to_value(literal_v3::inspect_comparison(dir).unwrap()).unwrap();
    assert_eq!(report["version"], 3); assert_eq!(report["completed"], false); assert!(report["turns"].as_array().unwrap().is_empty()); assert_eq!(report["human_reviewed"], 0); assert_eq!(report["quality_accepted"], false);
    let setup: Value = serde_json::from_slice(&fs::read(dir.join("setup-00.json")).unwrap()).unwrap(); assert_eq!(setup["status"], "failed"); assert_eq!(setup["native"], true);
    assert!(before.keys().all(|p| !p.file_name().unwrap_or_default().to_string_lossy().starts_with("raw-") && !p.file_name().unwrap_or_default().to_string_lossy().starts_with("attempt-")));
    assert_eq!(inventory(dir), before);
    // No completed-native fixture, accepted canonical turn, role inference,
    // model startup/cleanup timing or successful model load is claimed here.
}

#[test]
fn mutations_of_actual_failed_native_manifest_refuse_before_another_reservation() {
    for fault in 0..3 {
        let original = inventory(failed_native_fixture()); let dir = root("fault-copy").join("run");
        for (relative, bytes) in &original { let target = dir.join(relative); match bytes { None => fs::create_dir_all(target).unwrap(), Some(bytes) => fs::write(target, bytes).unwrap() } }
        let path = dir.join("run.json"); let mut manifest: Value = serde_json::from_slice(&fs::read(&path).unwrap()).unwrap();
        match fault { 0 => manifest["version"] = json!(2), 1 => manifest["source_sha256"] = json!("0".repeat(64)), _ => manifest["reference_sha256"] = json!("1".repeat(64)) }
        fs::write(path, serde_json::to_vec(&manifest).unwrap()).unwrap(); let expected = inventory(&dir); let counts = Arc::new(Counts::default());
        let error = failure(invoke(&dir, true, &Cancellation::default(), 1, counts.clone())); assert!(!error.cleanup_uncertain()); assert_eq!(counts.reserve.load(Ordering::SeqCst), 0); assert_eq!(counts.assets.load(Ordering::SeqCst), 0); assert_eq!(counts.drops.load(Ordering::SeqCst), 0); assert_eq!(inventory(&dir), expected);
    }
    // These are hostile copies of genuinely emitted failed native metadata,
    // never relabelled scripted/completed or historical model evidence.
}
