// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Ignored approved-installed-asset gates. SOURCE ONLY / UNCOMPILED / UNRUN.
//! Actual desktop reservation/cleanup owner; never a substitute inference owner.
//! No quality-pass assertion, source relabel, asset copy or artifact deletion.
use super::*;
use locallore::inference::Cancellation;
use locallore_eval::{
    local_lane::comparison::{self, literal_v3, selected::SelectedNativeFailure, ComparisonKind},
    memory_comparison_v3::ComparisonReportV3,
};
use std::{collections::BTreeMap, sync::atomic::AtomicUsize};

static SERIAL: Mutex<()> = Mutex::new(());
static BLOCKED: AtomicBool = AtomicBool::new(false);
// Sole exact failed test owner only. It blocks later admission; no production
// manager/owner registry or alternative cleanup mechanism is introduced.
enum Retained {
    Pair { _manager: Arc<ModelManager>, _reservation: EvaluationReservation, _runtime: SharedRuntime },
    Manager { _manager: Arc<ModelManager> },
}
static RETAINED: Mutex<Option<Retained>> = Mutex::new(None);
type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;

fn root() -> PathBuf {
    let p = std::env::temp_dir().join(format!("locallore-literal-native-manager-{}", exports::identifier().unwrap()));
    fs::create_dir(&p).unwrap();
    println!("LOCALLORE_LITERAL_NATIVE_TEST_ARTIFACT={}", p.display());
    p
}
fn manager() -> Arc<ModelManager> {
    assert!(!BLOCKED.load(Ordering::SeqCst), "prior exact native owner remains unresolved; admission blocked");
    let resources = PathBuf::from(std::env::var_os("LOCALLORE_SELECTED_NATIVE_TEST_RESOURCES").expect("explicit approved resources ENV required"));
    let model = PathBuf::from(std::env::var_os("LOCALLORE_SELECTED_NATIVE_TEST_MODEL").expect("explicit approved model ENV required"));
    assert_eq!(model.file_name().and_then(|v| v.to_str()), Some("Qwen3-0.6B-Q8_0.gguf"));
    assert!(model.is_file() && resources.is_dir());
    Arc::new(ModelManager::new(model.parent().unwrap().to_owned(), resources))
}
fn inventory(root: &Path) -> Inventory {
    fn visit(root: &Path, p: &Path, depth: usize, total: &mut usize, out: &mut Inventory) {
        assert!(depth <= 10 && out.len() < 8192);
        let m = fs::symlink_metadata(p).unwrap(); assert!(!m.file_type().is_symlink());
        #[cfg(windows)] { use std::os::windows::fs::MetadataExt; assert_eq!(m.file_attributes() & 0x400, 0); }
        let relative = p.strip_prefix(root).unwrap().to_owned();
        if m.is_dir() { out.insert(relative, None); for e in fs::read_dir(p).unwrap() { visit(root, &e.unwrap().path(), depth + 1, total, out); } }
        else { assert!(m.is_file() && m.len() <= 8 * 1024 * 1024); let bytes = fs::read(p).unwrap(); *total = total.checked_add(bytes.len()).unwrap(); assert!(*total <= 128 * 1024 * 1024); out.insert(relative, Some(bytes)); }
    }
    let mut files = Inventory::new(); visit(root, root, 0, &mut 0, &mut files); files
}
fn retain(owner: Retained) -> ! {
    BLOCKED.store(true, Ordering::SeqCst);
    let mut slot = RETAINED.lock().unwrap_or_else(|p| p.into_inner());
    if slot.is_none() { *slot = Some(owner); } else { std::mem::forget(owner); }
    panic!("actual native owner remains retained; later asset admission blocked; Root inspection required");
}
fn close_manager(manager: &Arc<ModelManager>) {
    if manager.cleanup_complete() { return; }
    let retired = manager.retire(); manager.close(None, retired);
    if !manager.cleanup_complete() { retain(Retained::Manager { _manager: manager.clone() }); }
}
fn dispose_failure(manager: &Arc<ModelManager>, witness: Option<CleanupWitness>, failure: SelectedNativeFailure<EvaluationReservation>) -> String {
    let code = failure.code().to_owned();
    match failure.into_retained() {
        Ok((mut reservation, runtime)) => {
            let mut confirmed = false;
            for _ in 0..2 { if reservation.cleanup_retained(&runtime).confirmed { confirmed = true; break; } }
            if !confirmed { retain(Retained::Pair { _manager: manager.clone(), _reservation: reservation, _runtime: runtime }); }
            drop(runtime); drop(reservation);
        }
        Err(error) => {
            // Accepted transfer is owned by this same manager. The opaque
            // witness selects only that exact slot; never a replacement owner.
            if error.cleanup_uncertain() {
                if let Some(witness) = witness { for _ in 0..2 { if manager.cleanup_selected(&witness).confirmed { break; } } }
            }
        }
    }
    close_manager(manager); code
}
fn run(manager: &Arc<ModelManager>, dir: &Path, resume: bool, kind: ComparisonKind, scenes: usize, reference: Option<&comparison::ValidatedReference>) -> ComparisonReportV3 {
    let witness = Mutex::new(None);
    let result = literal_v3::run_native_comparison(dir, resume, kind, &Cancellation::default(), scenes, || {
        let reservation = manager.reserve_evaluation()?;
        *witness.lock().unwrap() = Some(reservation.cleanup_witness());
        Ok(reservation)
    }, reference);
    match result {
        Ok(report) => { close_manager(manager); assert!(manager.cleanup_complete()); report }
        Err(error) => { let code = dispose_failure(manager, witness.into_inner().unwrap(), error); panic!("native literal opt-in returned fixed error {code}"); }
    }
}
fn summary(label: &str, report: &ComparisonReportV3) {
    let mut phases: BTreeMap<String, usize> = BTreeMap::new();
    let mut failures: BTreeMap<String, usize> = BTreeMap::new();
    let mut flags: BTreeMap<String, usize> = BTreeMap::new();
    for row in &report.turns {
        *phases.entry(row.phase.clone()).or_default() += 1;
        for failure in &row.failures { *failures.entry(failure.clone()).or_default() += 1; }
        for flag in &row.quality_flags { *flags.entry(flag.clone()).or_default() += 1; }
    }
    assert!(phases.len() <= 16 && failures.len() <= 64 && flags.len() <= 32);
    println!("LOCALLORE_LITERAL_NATIVE_SUMMARY={}", json!({"stage":label,"completed":report.completed,"scenes":report.completed_scenes,"rows":report.turns.len(),"phases":phases,"failures":failures,"quality_flags":flags,"passed":report.turns.iter().filter(|r|r.passed).count(),"human_reviewed":report.human_reviewed,"quality_accepted":report.quality_accepted,"physical_setups":report.physical_setups}));
}
fn all_outcomes(report: &ComparisonReportV3) {
    assert!(report.completed && report.completed_scenes == 4 && report.turns.len() == 48);
    assert!(report.source_matches);
    assert!(report.physical_setups > 0 && report.native_load.as_ref().is_some_and(|v| v.as_array().is_some_and(|a| !a.is_empty())));
    let mut identities = std::collections::BTreeSet::new();
    for row in &report.turns { assert!(identities.insert((row.turn.clone(), row.arm.clone()))); }
    // Retain failures/guards/dependencies/quality flags. No assertion that all
    // passed, inference understood prose, or human quality was accepted.
}

#[test]
#[ignore = "requires explicitly approved installed model/resources; serial Root opt-in only"]
fn approved_literal_paired_resumes_and_completed_read_is_zero_asset() {
    let _serial = SERIAL.lock().unwrap_or_else(|p| p.into_inner());
    let manager = manager(); let root = root(); let reference_dir = root.join("reference");
    comparison::prepare_reference(&reference_dir, &Cancellation::default()).unwrap();
    let reference = comparison::open_reference(&reference_dir).unwrap(); let dir = root.join("paired");
    let first = run(&manager, &dir, false, ComparisonKind::PairedSnapshots, 1, Some(&reference));
    summary("paired-first", &first); assert_eq!((first.completed_scenes, first.turns.len()), (1, 12));
    let completed = run(&manager, &dir, true, ComparisonKind::PairedSnapshots, 3, None);
    summary("paired-completed", &completed); all_outcomes(&completed); assert!(manager.cleanup_complete());
    let before = inventory(&root);
    let inspected = literal_v3::inspect_comparison(&dir).unwrap(); assert_eq!(inspected, completed); assert_eq!(inventory(&root), before);
    let callbacks = AtomicUsize::new(0);
    let result = literal_v3::run_native_comparison::<EvaluationReservation>(&dir, true, ComparisonKind::PairedSnapshots, &Cancellation::default(), 3, || {
        callbacks.fetch_add(1, Ordering::SeqCst); Err("CompletedPathMustNotReserve".into())
    }, None);
    let resumed = match result { Ok(report) => report, Err(error) => { let code = dispose_failure(&manager, None, error); panic!("completed native resume refused with {code}"); } };
    close_manager(&manager);
    assert_eq!(callbacks.load(Ordering::SeqCst), 0); assert_eq!(resumed, completed); assert_eq!(inventory(&root), before); assert!(manager.cleanup_complete());
}

#[test]
#[ignore = "requires explicitly approved installed model/resources; serial Root opt-in only"]
fn approved_literal_rollout_records_all_outcomes() {
    let _serial = SERIAL.lock().unwrap_or_else(|p| p.into_inner());
    let manager = manager(); let root = root(); let dir = root.join("rollout");
    let report = run(&manager, &dir, false, ComparisonKind::ContinuousRollout, 4, None);
    summary("rollout-completed", &report); all_outcomes(&report); assert!(manager.cleanup_complete());
    let before = inventory(&root); assert_eq!(literal_v3::inspect_comparison(&dir).unwrap(), report); assert_eq!(inventory(&root), before);
}
